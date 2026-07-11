---
card: spring-cloud
gi: 73
slug: rate-limiter
title: "Rate limiter"
---

## 1. What it is

Resilience4j's `RateLimiter` caps how many calls *from* this application *to* a specific dependency are permitted within a refresh period, rejecting (or optionally queuing, briefly) anything beyond that limit — the client-side counterpart to the Gateway `RequestRateLimiter` filter covered earlier, which limits how many calls *arrive at* the gateway *from* external clients.

```properties
resilience4j.ratelimiter.instances.billing-service.limit-for-period=50
resilience4j.ratelimiter.instances.billing-service.limit-refresh-period=1s
resilience4j.ratelimiter.instances.billing-service.timeout-duration=0
```

## 2. Why & when

The Gateway `RequestRateLimiter` protects *your own* service from being overwhelmed by too many incoming requests; a Resilience4j `RateLimiter` protects a *downstream* dependency (or a rate-limited third-party API) from being overwhelmed by too many *outgoing* calls your own application makes to it — the direction of protection is reversed, but the underlying mechanism (cap calls per period) is conceptually similar.

Reach for a client-side rate limiter when:

- Calling a third-party API with a contractually or technically enforced rate limit (a payment provider, a mapping service, an SMS gateway) — self-imposing a limit slightly under their actual limit avoids ever triggering their own throttling or, worse, a temporary ban.
- A downstream internal service, even without a hard external limit, has known capacity constraints, and you want to deliberately smooth out call bursts from this caller rather than sending everything as fast as the caller could generate it.
- Multiple callers within the same application independently call the same rate-limited dependency, and a shared `RateLimiter` instance (keyed by dependency name) coordinates their combined call rate against one limit, rather than each caller unknowingly exceeding it independently.

## 3. Core concept

```
 limit-for-period: 50, limit-refresh-period: 1s

 within each 1-second window: up to 50 calls permitted
 the 51st call in the same window:
   timeout-duration: 0   -> rejected immediately
   timeout-duration: 5s  -> waits up to 5s for the next window to open, then either proceeds or times out
```

The rate limiter tracks calls *this application makes*, not calls it receives — protecting the target dependency from this application's own excessive call rate.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Calls made to a rate limited dependency within the current period are permitted up to the configured limit, and any call beyond that limit is rejected or made to wait for the next period" >
  <rect x="30" y="30" width="580" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="320" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">current 1-second window: 50 calls permitted, evenly or in a burst</text>

  <rect x="30" y="100" width="270" height="40" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.3"/>
  <text x="165" y="124" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">call 1-50 -&gt; proceed normally</text>

  <rect x="340" y="100" width="270" height="40" rx="6" fill="#e6494930" stroke="#e64949" stroke-width="1.3"/>
  <text x="475" y="124" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">call 51+ -&gt; rejected or waits for next window</text>

  <defs><marker id="a73" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Every call within the period's limit proceeds unimpeded; anything beyond it is either rejected outright or made to wait for the window to refresh.

## 5. Runnable example

The scenario: rate-limit calls from `orders-service` to a third-party payment gateway with a strict external limit. Start with unlimited calling (the risk of triggering the provider's own throttling), then add a client-side rate limiter capping the call rate, then add a wait-for-next-window behavior instead of immediate rejection.

### Level 1 — Basic

Unlimited calling — the risk this feature protects against.

```java
public class RateLimiterLevel1 {
    static int callCount = 0;

    static String callPaymentGateway() {
        callCount++;
        return "call #" + callCount + " sent"; // no restraint at all -- could easily exceed the provider's own limit
    }

    public static void main(String[] args) {
        for (int i = 0; i < 60; i++) {
            callPaymentGateway();
        }
        System.out.println("sent " + callCount + " calls in a tight burst -- a real rate-limited API would likely start rejecting these");
    }
}
```

How to run: `java RateLimiterLevel1.java`

Sixty calls fired in a tight burst with no restraint whatsoever — against a real third-party API enforcing, say, a 50-calls-per-second limit, this would trigger their own throttling (or worse, a temporary ban) well before this loop finishes.

### Level 2 — Intermediate

Add a client-side rate limiter capping calls per period, rejecting anything beyond the limit within the current window.

```java
public class RateLimiterLevel2 {
    static class RateLimiter {
        int limitForPeriod;
        long periodMs;
        int callsInCurrentPeriod = 0;
        long currentPeriodStartMs = 0;

        RateLimiter(int limitForPeriod, long periodMs) { this.limitForPeriod = limitForPeriod; this.periodMs = periodMs; }

        boolean tryAcquire(long nowMs) {
            if (nowMs - currentPeriodStartMs >= periodMs) {
                currentPeriodStartMs = nowMs; // new period begins, counter resets
                callsInCurrentPeriod = 0;
            }
            if (callsInCurrentPeriod < limitForPeriod) {
                callsInCurrentPeriod++;
                return true;
            }
            return false; // limit reached for this period -- rejected
        }
    }

    public static void main(String[] args) {
        RateLimiter limiter = new RateLimiter(50, 1000); // 50 calls per 1-second window

        int accepted = 0, rejected = 0;
        for (int i = 0; i < 60; i++) {
            if (limiter.tryAcquire(0)) accepted++; // all 60 attempted within the SAME instant (nowMs=0)
            else rejected++;
        }
        System.out.println("accepted: " + accepted + ", rejected: " + rejected + " (all within the same 1s window)");
    }
}
```

How to run: `java RateLimiterLevel2.java`

`tryAcquire` tracks `callsInCurrentPeriod` against `limitForPeriod`, resetting only when a new period genuinely begins — with all 60 attempts happening at the same simulated instant (`nowMs=0`, all within the first window), exactly 50 are accepted and the remaining 10 are rejected immediately, protecting the downstream dependency from ever seeing more than the configured 50 calls in that window.

### Level 3 — Advanced

Add a wait-for-next-window behavior (`timeout-duration > 0`): instead of rejecting immediately, a call beyond the limit waits (up to a configured timeout) for the next period to open, then proceeds if a slot becomes available in time.

```java
public class RateLimiterLevel3 {
    static class RateLimiter {
        int limitForPeriod;
        long periodMs;
        int callsInCurrentPeriod = 0;
        long currentPeriodStartMs = 0;

        RateLimiter(int limitForPeriod, long periodMs) { this.limitForPeriod = limitForPeriod; this.periodMs = periodMs; }

        void refreshPeriodIfNeeded(long nowMs) {
            if (nowMs - currentPeriodStartMs >= periodMs) {
                currentPeriodStartMs = nowMs;
                callsInCurrentPeriod = 0;
            }
        }

        boolean tryAcquireImmediate(long nowMs) {
            refreshPeriodIfNeeded(nowMs);
            if (callsInCurrentPeriod < limitForPeriod) { callsInCurrentPeriod++; return true; }
            return false;
        }

        // models waiting for the next period to open, up to timeoutMs, rather than rejecting immediately
        boolean tryAcquireWithTimeout(long nowMs, long timeoutMs) {
            if (tryAcquireImmediate(nowMs)) return true;
            long nextPeriodStart = currentPeriodStartMs + periodMs;
            long waitNeeded = nextPeriodStart - nowMs;
            if (waitNeeded > timeoutMs) {
                System.out.println("would need to wait " + waitNeeded + "ms, exceeds timeout of " + timeoutMs + "ms -- give up");
                return false;
            }
            System.out.println("waiting " + waitNeeded + "ms for the next window to open...");
            return tryAcquireImmediate(nextPeriodStart); // the next period has now started, fresh capacity available
        }

        int getCallsInCurrentPeriod() { return callsInCurrentPeriod; }
    }

    public static void main(String[] args) {
        RateLimiter limiter = new RateLimiter(50, 1000);
        for (int i = 0; i < 50; i++) limiter.tryAcquireImmediate(0); // fill up the current window entirely

        System.out.println("window full: " + limiter.getCallsInCurrentPeriod() + "/50");

        // the 51st call, arriving at t=800ms (200ms before the window refreshes), is willing to wait up to 500ms
        boolean succeededByWaiting = limiter.tryAcquireWithTimeout(800, 500);
        System.out.println("51st call succeeded by waiting: " + succeededByWaiting);
    }
}
```

How to run: `java RateLimiterLevel3.java`

`tryAcquireWithTimeout` first tries the immediate path; when it fails (window is full), it computes how long until the next window opens (`nextPeriodStart - nowMs`) and, if that's within the caller's configured `timeoutMs`, actually waits and retries against the fresh window. Here, the 51st call arrives at `t=800ms` with a 1000ms period starting at `t=0`, so the next window opens at `t=1000ms` — only 200ms away, comfortably within the 500ms timeout — so the call succeeds by effectively "waiting" for fresh capacity, rather than being rejected outright the way `tryAcquireImmediate` alone would have handled it.

## 6. Walkthrough

Trace the sequence in Level 3.

1. The loop calls `limiter.tryAcquireImmediate(0)` fifty times, all at `nowMs=0` — each call increments `callsInCurrentPeriod`, reaching `50` by the end of the loop, exactly filling the window's capacity.
2. The `println` confirms the window is now full: `50/50`.
3. `limiter.tryAcquireWithTimeout(800, 500)` runs — it first calls `tryAcquireImmediate(800)`. Inside that, `refreshPeriodIfNeeded(800)` checks `800 - 0 = 800`, which is `< periodMs (1000)`, so the period does *not* refresh yet, and `callsInCurrentPeriod` is still `50`, which is not `< limitForPeriod (50)`, so `tryAcquireImmediate` returns `false`.
4. Back in `tryAcquireWithTimeout`, since the immediate attempt failed, it computes `nextPeriodStart = 0 + 1000 = 1000`, and `waitNeeded = 1000 - 800 = 200`. Since `200 <= timeoutMs (500)`, the wait is acceptable, so it prints the "waiting 200ms" message.
5. It then calls `tryAcquireImmediate(1000)` — this time, `refreshPeriodIfNeeded(1000)` checks `1000 - 0 = 1000`, which is `>= periodMs (1000)`, so the period *does* refresh: `currentPeriodStartMs` becomes `1000` and `callsInCurrentPeriod` resets to `0`. The subsequent capacity check (`0 < 50`) passes, `callsInCurrentPeriod` becomes `1`, and `true` is returned.
6. The final `println` confirms the 51st call succeeded — not by being squeezed into the already-full first window, but by genuinely waiting until the next window opened and then being the very first call admitted into it.

```
window [0, 1000): calls 1-50 fill it completely
call 51 arrives at t=800 -> immediate attempt fails (window still full)
  -> next window opens at t=1000, only 200ms away, within the 500ms timeout
  -> "wait" until t=1000 -> window refreshes -> call 51 becomes the FIRST call in the new window -> succeeds
```

## 7. Gotchas & takeaways

> **Gotcha:** a non-zero `timeoutDuration` means a rate-limited call can genuinely block the calling thread for up to that duration waiting for capacity — in a Servlet-model (blocking) application, this ties up a request-handling thread for the wait, which interacts with the earlier Bulkhead card's thread-exhaustion concerns; in a reactive application, this needs to be handled non-blockingly, similar to the Gateway MVC vs. reactive Gateway tradeoff covered earlier. A `timeoutDuration` of `0` (immediate rejection, no waiting) avoids this risk entirely, at the cost of a higher rejection rate under bursty traffic.

- A Resilience4j `RateLimiter` protects a downstream dependency from *this application's* excessive outgoing call rate — the mirror image of the Gateway `RequestRateLimiter`, which protects this application from excessive *incoming* traffic.
- Setting the limit slightly below a third-party API's actual documented limit provides a safety margin against timing/measurement discrepancies between your tracking and theirs.
- `timeoutDuration=0` gives fast, predictable rejection with no thread-blocking risk; a non-zero timeout smooths out short bursts at the cost of temporarily occupying the calling thread — the right choice depends on the calling code's own threading model and how tolerant it is of brief waits.
- Rate limiting (calls per period) and bulkheading (concurrent calls at once) are complementary, addressing different dimensions of protection — a dependency can need both a cap on how many calls happen per second *and* a cap on how many are ever in flight simultaneously.
