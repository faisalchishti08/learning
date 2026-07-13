---
card: microservices
gi: 276
slug: fixed-window-sliding-window-counters
title: "Fixed window & sliding window counters"
---

## 1. What it is

Fixed window and sliding window are two simpler counter-based rate-limiting strategies, alternatives to [token bucket](0274-token-bucket-algorithm.md) and [leaky bucket](0275-leaky-bucket-algorithm.md). A fixed window counter divides time into discrete, non-overlapping blocks (e.g., "the current minute") and counts requests within the current block, resetting to zero the instant a new block begins. A sliding window counter fixes the boundary-burst problem of fixed windows by weighting the count from the previous window based on how much of it still overlaps the current moment, producing a smoother, more accurate approximation of "requests in the last N seconds" measured continuously rather than in resettable blocks.

## 2. Why & when

Fixed window is the simplest possible rate limiter to implement and reason about — one counter, one reset timer — which makes it attractive when a rough, easy-to-audit limit is good enough. But it has a well-known flaw: a client can send its full quota right at the end of one window and its full quota again right at the start of the next, producing up to 2x the intended rate within a short burst straddling the boundary. Sliding window counters exist specifically to close that gap cheaply, without the memory cost of tracking every individual request timestamp (which a true sliding log would require).

Use fixed window when simplicity and low overhead matter more than precision and boundary bursts are tolerable (e.g., a soft usage-tier limit). Use the sliding window counter approximation when boundary bursts are a real concern but the cost of a full sliding log (storing every request's exact timestamp) is not justified — it is the common middle ground used by many production API gateways.

## 3. Core concept

Fixed window: one integer counter and a window-start timestamp, reset when the window elapses.

Sliding window counter: keep the previous window's count and the current window's count; the *estimated* count "right now" is `currentCount + previousCount * overlapFraction`, where `overlapFraction` shrinks linearly from 1 (just entered the new window) to 0 (about to enter the next one).

```java
class SlidingWindowCounter {
    long windowStart; final long windowSizeMillis; final int limit;
    int previousCount = 0, currentCount = 0;

    boolean allow(long now) {
        if (now - windowStart >= windowSizeMillis) {
            long windowsElapsed = (now - windowStart) / windowSizeMillis;
            previousCount = (windowsElapsed == 1) ? currentCount : 0; // roll forward ONE window
            currentCount = 0;
            windowStart += windowsElapsed * windowSizeMillis;
        }
        double elapsedInWindow = now - windowStart;
        double overlap = 1.0 - (elapsedInWindow / windowSizeMillis); // shrinks toward 0
        double estimated = currentCount + previousCount * overlap;
        if (estimated < limit) { currentCount++; return true; }
        return false;
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Fixed window resets its counter abruptly at each boundary, allowing a double burst straddling the boundary; sliding window blends a weighted portion of the previous window's count into the current estimate, smoothing out the boundary and preventing the double-burst problem">
  <text x="160" y="16" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Fixed window (hard reset)</text>
  <rect x="30" y="25" width="130" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="44" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">window N: count=10/10</text>
  <rect x="160" y="25" width="130" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="225" y="44" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">window N+1: RESET to 0</text>
  <line x1="160" y1="20" x2="160" y2="60" stroke="#8b949e" stroke-dasharray="2,2"/>
  <text x="160" y="70" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">burst of 10 here + 10 here = 20 in a blink</text>

  <text x="160" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Sliding window (weighted blend)</text>
  <rect x="30" y="110" width="130" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="95" y="129" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">previous: count=10</text>
  <rect x="160" y="110" width="130" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="225" y="129" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">current: count=0</text>
  <text x="320" y="129" fill="#6db33f" font-size="7.5" font-family="sans-serif">estimate = 0 + 10 &#215; overlap%</text>
</svg>

Fixed window resets abruptly at the boundary; sliding window blends a shrinking weight of the previous window in.

## 5. Runnable example

Scenario: a fixed window counter that visibly allows a double-burst across a boundary, extended to a sliding window counter that closes that gap by blending the previous window's weighted count, and finally a version exposed behind a small HTTP-style request handler that returns 429 with a Retry-After-style hint when denied.

### Level 1 — Basic

```java
// File: FixedWindowBoundaryBurst.java -- demonstrates the classic flaw:
// a full quota right before a window boundary plus a full quota right
// after it lets nearly double the intended rate through.
public class FixedWindowBoundaryBurst {
    static class FixedWindowCounter {
        long windowStart; final long windowSizeMillis; final int limit;
        int count = 0;
        FixedWindowCounter(long windowSizeMillis, int limit) {
            this.windowSizeMillis = windowSizeMillis; this.limit = limit;
            this.windowStart = System.currentTimeMillis();
        }
        boolean allow(long now) {
            if (now - windowStart >= windowSizeMillis) { windowStart = now; count = 0; }
            if (count < limit) { count++; return true; }
            return false;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        FixedWindowCounter limiter = new FixedWindowCounter(1000, 5); // 5 req / 1s window
        int allowed = 0;
        // Burst 1: fires right at the START of the window.
        for (int i = 0; i < 5; i++) if (limiter.allow(System.currentTimeMillis())) allowed++;
        Thread.sleep(999); // wait until JUST before the window resets
        // Burst 2: fires right after the window resets.
        for (int i = 0; i < 5; i++) if (limiter.allow(System.currentTimeMillis())) allowed++;
        System.out.println("Allowed across ~1 second straddling the boundary: " + allowed + " (limit was 5/window)");
    }
}
```

How to run: `java FixedWindowBoundaryBurst.java`

Five requests fire immediately, consuming the full quota for window N. Then the program sleeps 999ms — just short of the 1000ms window size — and fires five more requests, which land just after the window resets and get a fresh quota. The total allowed count prints close to 10, roughly double the configured 5/second limit, even though both bursts occurred within about one second of wall-clock time. This is the boundary-burst flaw made concrete.

### Level 2 — Intermediate

```java
// File: SlidingWindowCounterFix.java -- same scenario, but the counter
// now blends a weighted share of the previous window's count into the
// estimate, closing the boundary-burst gap.
public class SlidingWindowCounterFix {
    static class SlidingWindowCounter {
        long windowStart; final long windowSizeMillis; final int limit;
        int previousCount = 0, currentCount = 0;

        SlidingWindowCounter(long windowSizeMillis, int limit) {
            this.windowSizeMillis = windowSizeMillis; this.limit = limit;
            this.windowStart = System.currentTimeMillis();
        }

        boolean allow(long now) {
            long windowsElapsed = (now - windowStart) / windowSizeMillis;
            if (windowsElapsed >= 1) {
                previousCount = (windowsElapsed == 1) ? currentCount : 0;
                currentCount = 0;
                windowStart += windowsElapsed * windowSizeMillis;
            }
            double elapsedInWindow = now - windowStart;
            double overlap = 1.0 - (elapsedInWindow / windowSizeMillis);
            double estimated = currentCount + previousCount * overlap;
            if (estimated < limit) { currentCount++; return true; }
            return false;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        SlidingWindowCounter limiter = new SlidingWindowCounter(1000, 5);
        int allowed = 0;
        for (int i = 0; i < 5; i++) if (limiter.allow(System.currentTimeMillis())) allowed++;
        Thread.sleep(999);
        for (int i = 0; i < 5; i++) if (limiter.allow(System.currentTimeMillis())) allowed++;
        System.out.println("Allowed across ~1 second straddling the boundary: " + allowed + " (limit was 5/window, sliding-window corrected)");
    }
}
```

How to run: `java SlidingWindowCounterFix.java`

Same burst pattern as Level 1, but this time the second burst, arriving just 1ms after the boundary, still sees an `overlap` fraction close to 1.0 for the previous window's count of 5 — so the estimated count is close to `0 + 5*1.0 = 5`, which is already at the limit, and most of the second burst's requests get rejected. The printed allowed total comes out much closer to 5-6 instead of 10, showing the sliding window's weighted blend closes the loophole that plain fixed window has.

### Level 3 — Advanced

```java
// File: RateLimitedHandler.java -- wraps the sliding window counter in a
// tiny synchronous "HTTP handler" that returns a 429-style response with
// a retry hint when the limit is exceeded, as a real API gateway would.
public class RateLimitedHandler {
    static class SlidingWindowCounter {
        long windowStart; final long windowSizeMillis; final int limit;
        int previousCount = 0, currentCount = 0;
        SlidingWindowCounter(long windowSizeMillis, int limit) {
            this.windowSizeMillis = windowSizeMillis; this.limit = limit;
            this.windowStart = System.currentTimeMillis();
        }
        synchronized boolean allow(long now) {
            long windowsElapsed = (now - windowStart) / windowSizeMillis;
            if (windowsElapsed >= 1) {
                previousCount = (windowsElapsed == 1) ? currentCount : 0;
                currentCount = 0;
                windowStart += windowsElapsed * windowSizeMillis;
            }
            double elapsedInWindow = now - windowStart;
            double overlap = 1.0 - (elapsedInWindow / windowSizeMillis);
            double estimated = currentCount + previousCount * overlap;
            if (estimated < limit) { currentCount++; return true; }
            return false;
        }
        long millisUntilNextWindow(long now) { return windowSizeMillis - ((now - windowStart) % windowSizeMillis); }
    }

    record Response(int status, String body, Long retryAfterMillis) {}

    static Response handle(SlidingWindowCounter limiter, String clientId, long now) {
        if (limiter.allow(now)) {
            return new Response(200, "{\"client\":\"" + clientId + "\",\"result\":\"ok\"}", null);
        }
        long retryAfter = limiter.millisUntilNextWindow(now);
        return new Response(429,
                "{\"error\":\"rate_limited\",\"client\":\"" + clientId + "\"}", retryAfter);
    }

    public static void main(String[] args) {
        SlidingWindowCounter limiter = new SlidingWindowCounter(1000, 3);
        long now = System.currentTimeMillis();
        for (int i = 1; i <= 5; i++) {
            Response r = handle(limiter, "client-42", now);
            if (r.status() == 200) {
                System.out.println("Request " + i + " -> 200 OK  body=" + r.body());
            } else {
                System.out.println("Request " + i + " -> 429 Too Many Requests  Retry-After=" + r.retryAfterMillis() + "ms  body=" + r.body());
            }
        }
    }
}
```

How to run: `java RateLimitedHandler.java`

Five requests hit a handler wrapping a 3-request-per-second sliding window limiter, all at essentially the same instant (`now` captured once). The first three get a `200 OK` JSON body; the fourth and fifth get a `429 Too Many Requests` JSON body with a computed `Retry-After`-style hint telling the caller how many milliseconds remain until the current window rolls over. This is the shape a real API gateway or Spring `HandlerInterceptor` would return to a rate-limited client, including the retry hint so well-behaved clients can back off intelligently instead of retrying immediately.

## 6. Walkthrough

Trace `RateLimitedHandler.main` in execution order. **First**, a `SlidingWindowCounter` is constructed with a 1000ms window and a limit of 3, capturing `windowStart` at the current time.

**Next**, the loop sends five requests, each calling `handle(limiter, "client-42", now)` with the same captured `now`. Inside `handle`, `limiter.allow(now)` runs: since `now - windowStart` is near zero, `windowsElapsed` is 0, so no window roll-over happens; `overlap` is close to 1.0 but `previousCount` is 0 (no prior window yet), so `estimated = currentCount`. For the first three calls, `currentCount` is 0, 1, 2 respectively — all below the limit of 3 — so each increments `currentCount` and returns `true`.

**Request example** — think of request 1 as `GET /api/resource` with header `X-Client-Id: client-42`. Its response, encoded in the `Response` record, is:
```
HTTP/1.1 200 OK
Content-Type: application/json

{"client":"client-42","result":"ok"}
```

**By request 4**, `currentCount` is already 3, so `estimated = 3`, which is not less than the limit of 3 — `allow` returns `false`. Back in `handle`, this triggers the rejection branch: it calls `millisUntilNextWindow(now)` to compute how long until the window resets, then builds a 429 response:
```
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 843

{"error":"rate_limited","client":"client-42"}
```

**Request 5** follows the identical path as request 4 — `currentCount` is still 3 (rejections do not increment the counter), so it is also rejected with a fresh `Retry-After` value.

**State transformation summary**: the raw call arrives at `handle` (entry point) → `handle` delegates the accept/reject decision to `limiter.allow` (business logic layer) → `allow` mutates the counter's internal `currentCount`/`previousCount` state (the "storage" layer, here just in-memory fields) → the boolean result propagates back up through `handle`, which shapes it into either a 200 or 429 `Response` object (the outward-facing layer) that the caller consumes.

```
client -> handle() -> limiter.allow() -> [currentCount/previousCount state] -> allow() returns bool -> handle() builds Response -> client
```

## 7. Gotchas & takeaways

> A pure fixed window counter can silently let through up to roughly 2x its configured limit for traffic that clusters around a window boundary — this is not a bug in a specific implementation, it is inherent to the algorithm's hard resets.

- Fixed window is cheap and simple but structurally allows boundary bursts; only use it where that slack is acceptable.
- The sliding window counter is an *approximation*, not an exact sliding log — it assumes requests in the previous window were spread evenly across it, which is close enough for most rate-limiting purposes without the memory cost of a true sliding log.
- A true sliding log (storing every request's exact timestamp and counting those within the last N seconds) is the most precise option but is far more memory-intensive at scale — reserve it for cases needing exact enforcement.
- Always return a `Retry-After`-style hint on rejection so well-behaved clients can back off instead of hammering the limiter immediately after being denied.
