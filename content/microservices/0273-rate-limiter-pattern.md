---
card: microservices
gi: 273
slug: rate-limiter-pattern
title: "Rate limiter pattern"
---

## 1. What it is

A rate limiter caps how many operations are permitted within a given time window — for example, 100 requests per second — rejecting or delaying anything beyond that rate, regardless of how many are currently in flight simultaneously; this distinguishes it from a [bulkhead](0267-bulkhead-pattern.md), which caps *concurrency* (how many calls are in flight at once) rather than *throughput* (how many calls happen per unit of time).

## 2. Why & when

A bulkhead limiting concurrency to, say, 10 simultaneous calls doesn't prevent an extremely high *rate* of very fast calls from overwhelming a downstream dependency or its own infrastructure — 10 concurrent slots, each completing and being reused thousands of times per second, could still generate an enormous request rate even while concurrency itself stays perfectly bounded. Rate limiting addresses a fundamentally different dimension of protection: it's the right tool when the concern is the *frequency* of requests (a downstream API's contractual rate limit, protecting a resource with a fixed processing rate rather than a fixed concurrency capacity, fairly sharing a resource's fixed throughput among many clients) rather than how many are simultaneously outstanding.

Use a rate limiter to protect a resource with a rate-based constraint — a third-party API enforcing its own rate limit that must be respected, a downstream system whose processing capacity is naturally expressed as "units per second" rather than "concurrent connections," or to enforce fair usage limits across multiple clients sharing a resource. Use a bulkhead instead (or alongside) when the concern is specifically about concurrent in-flight calls rather than request frequency — the two patterns address different, complementary dimensions and are frequently used together.

## 3. Core concept

A rate limiter tracks how many operations have occurred within the current time window and permits a new operation only if that count is still under the configured limit for the window — several concrete algorithms (covered by name in the rest of this section: [token bucket](0274-token-bucket-algorithm.md), [leaky bucket](0275-leaky-bucket-algorithm.md), [fixed/sliding window counters](0276-fixed-window-sliding-window-counters.md)) implement this same basic idea with different tradeoffs around burst tolerance and smoothness.

```java
RateLimiterConfig config = RateLimiterConfig.custom()
    .limitForPeriod(100) // 100 operations
    .limitRefreshPeriod(Duration.ofSeconds(1)) // ...per 1-second window
    .timeoutDuration(Duration.ofMillis(0)) // reject immediately if the limit is already reached
    .build();
RateLimiter rateLimiter = RateLimiter.of("external-api", config);

String result = rateLimiter.executeSupplier(() -> externalApiClient.call());
// the 101st call within the SAME 1-second window is REJECTED, regardless of how many calls are
// CURRENTLY in flight (which is what a bulkhead, a DIFFERENT concern, would instead govern)
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A bulkhead caps how many calls are simultaneously in flight at any instant, regardless of how fast they complete; a rate limiter caps how many calls occur per unit of time, regardless of how many are simultaneously in flight -- the two address orthogonal dimensions of load" >
  <rect x="20" y="20" width="270" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="155" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Bulkhead: CONCURRENCY</text>
  <text x="155" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">caps HOW MANY at once, ANY speed</text>

  <rect x="350" y="20" width="270" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Rate limiter: THROUGHPUT</text>
  <text x="485" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">caps HOW OFTEN, ANY concurrency</text>
</svg>

Concurrency and throughput are orthogonal load dimensions; a system can be bounded on one while unbounded on the other.

## 5. Runnable example

Scenario: a call pattern with low concurrency but an extremely high rate, protected only by a bulkhead that completely fails to catch the resulting overload, refactored to add a rate limiter that correctly bounds the request frequency, and finally demonstrating both mechanisms combined, each catching a different kind of overload that the other alone would miss.

### Level 1 — Basic

```java
// File: BulkheadMissesRateOverload.java -- LOW concurrency (never more
// than 1 at a time) but an EXTREMELY HIGH RATE -- a bulkhead alone
// PROVIDES NO PROTECTION against this AT ALL.
public class BulkheadMissesRateOverload {
    static int concurrentCallsRightNow = 0;
    static int peakConcurrency = 0;
    static int totalCallsThisSecond = 0;

    static void fastCall() { // completes INSTANTLY -- so concurrency NEVER builds up, even at a huge RATE
        concurrentCallsRightNow++;
        peakConcurrency = Math.max(peakConcurrency, concurrentCallsRightNow);
        totalCallsThisSecond++;
        concurrentCallsRightNow--; // completes IMMEDIATELY
    }

    public static void main(String[] args) {
        for (int i = 0; i < 10000; i++) fastCall(); // 10,000 calls, but EACH completes before the next starts

        System.out.println("Peak CONCURRENCY observed: " + peakConcurrency + " (a bulkhead sized for even 1 would have been 'sufficient')");
        System.out.println("Total calls made in this burst: " + totalCallsThisSecond + " -- a MASSIVE rate, completely UNCAUGHT by concurrency-based protection.");
    }
}
```

**How to run:** `javac BulkheadMissesRateOverload.java && java BulkheadMissesRateOverload` (JDK 17+).

Expected output:
```
Peak CONCURRENCY observed: 1 (a bulkhead sized for even 1 would have been 'sufficient')
Total calls made in this burst: 10000 -- a MASSIVE rate, completely UNCAUGHT by concurrency-based protection.
```

### Level 2 — Intermediate

```java
// File: RateLimiterCatchesIt.java -- adds a RATE limiter -- correctly
// bounds the SAME call pattern to a MAXIMUM number PER time window.
import java.util.concurrent.atomic.*;

public class RateLimiterCatchesIt {
    static final int LIMIT_PER_WINDOW = 100; // AT MOST 100 calls per simulated "window"
    static AtomicInteger callsInCurrentWindow = new AtomicInteger(0);

    static boolean tryCall() {
        if (callsInCurrentWindow.get() >= LIMIT_PER_WINDOW) return false; // REJECTED -- rate limit reached
        callsInCurrentWindow.incrementAndGet();
        return true;
    }

    public static void main(String[] args) {
        int attemptedCalls = 10000; // the SAME huge burst as Level 1
        int accepted = 0, rejected = 0;
        for (int i = 0; i < attemptedCalls; i++) {
            if (tryCall()) accepted++; else rejected++;
        }
        System.out.println("Attempted: " + attemptedCalls + ", accepted: " + accepted + " (capped at the " + LIMIT_PER_WINDOW + "-per-window limit), rejected: " + rejected);
        System.out.println("The RATE limiter correctly bounded throughput, regardless of the fact that concurrency NEVER exceeded 1.");
    }
}
```

**How to run:** `javac RateLimiterCatchesIt.java && java RateLimiterCatchesIt` (JDK 17+).

Expected output:
```
Attempted: 10000, accepted: 100 (capped at the 100-per-window limit), rejected: 9900
The RATE limiter correctly bounded throughput, regardless of the fact that concurrency NEVER exceeded 1.
```

### Level 3 — Advanced

```java
// File: BulkheadAndRateLimiterTogether.java -- COMBINES both mechanisms,
// demonstrating EACH catching a DIFFERENT kind of overload the OTHER
// alone would miss -- a HIGH-concurrency-LOW-rate scenario, and a
// LOW-concurrency-HIGH-rate scenario.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class BulkheadAndRateLimiterTogether {
    static Semaphore bulkhead = new Semaphore(10); // caps CONCURRENCY at 10
    static AtomicInteger callsInWindow = new AtomicInteger(0);
    static final int RATE_LIMIT = 50; // caps THROUGHPUT at 50 per window

    static String tryProtectedCall(String scenario) {
        if (!bulkhead.tryAcquire()) return scenario + ": REJECTED by BULKHEAD (concurrency limit)";
        try {
            if (callsInWindow.incrementAndGet() > RATE_LIMIT) return scenario + ": REJECTED by RATE LIMITER (throughput limit)";
            return scenario + ": ACCEPTED";
        } finally {
            bulkhead.release();
        }
    }

    public static void main(String[] args) {
        // SCENARIO 1: HIGH concurrency (20 SIMULTANEOUS holds), LOW total rate -- BULKHEAD catches this
        Semaphore concurrencyHog = new Semaphore(0);
        for (int i = 0; i < 15; i++) bulkhead.tryAcquire(); // simulate 15 ALREADY-held slots (exceeds the 10 limit)
        System.out.println(tryProtectedCall("high-concurrency scenario"));
        for (int i = 0; i < 15; i++) bulkhead.release(); // release the simulated holds

        // SCENARIO 2: LOW concurrency, but the window is ALREADY at its rate limit -- RATE LIMITER catches this
        callsInWindow.set(RATE_LIMIT); // simulate the window ALREADY being at its 50-call limit
        System.out.println(tryProtectedCall("high-rate scenario"));
    }
}
```

**How to run:** `javac BulkheadAndRateLimiterTogether.java && java BulkheadAndRateLimiterTogether` (JDK 17+).

Expected output:
```
high-concurrency scenario: REJECTED by BULKHEAD (concurrency limit)
high-rate scenario: REJECTED by RATE LIMITER (throughput limit)
```

## 6. Walkthrough

1. **Level 1, the blind spot made explicit** — `fastCall` increments and immediately decrements `concurrentCallsRightNow` within the same method call, meaning `peakConcurrency` never exceeds 1, even as `totalCallsThisSecond` climbs to 10000 across the loop — a bulkhead monitoring only concurrency would see nothing alarming here at all, since concurrency genuinely never builds up, despite an enormous total request volume.
2. **Level 2, tracking frequency instead of concurrency** — `tryCall` checks `callsInCurrentWindow` against `LIMIT_PER_WINDOW` (100) *before* incrementing, entirely independent of anything resembling concurrent in-flight state; this correctly caps the total number of accepted calls at exactly 100, regardless of how quickly or slowly they arrive or how many are "in flight" at any given instant.
3. **Level 2, the correct rejection behavior observed** — out of 10000 attempted calls, exactly 100 are accepted and 9900 rejected, precisely matching the configured rate limit — demonstrating protection against exactly the scenario Level 1's concurrency-only approach was structurally blind to.
4. **Level 3, combining both mechanisms deliberately** — `tryProtectedCall` checks the bulkhead (`bulkhead.tryAcquire()`) first, and only if that succeeds, checks the rate limiter (`callsInWindow.incrementAndGet() > RATE_LIMIT`) — both checks are independent gates a call must pass through, each protecting against a different dimension of overload.
5. **Level 3, the high-concurrency scenario caught by the bulkhead** — by pre-acquiring 15 permits (simulating 15 already-in-flight calls, exceeding the bulkhead's 10-permit capacity) before attempting a new call, the new call's `bulkhead.tryAcquire()` fails immediately, and the rate limiter check is never even reached — this is exactly the kind of overload (too many *simultaneous* calls) a rate limiter alone, which only tracks frequency, would never catch on its own.
6. **Level 3, the high-rate scenario caught by the rate limiter** — for the second scenario, `callsInWindow` is set directly to `RATE_LIMIT` (simulating the window already being fully consumed by prior, now-completed calls, meaning concurrency itself is currently low or zero), so the bulkhead check succeeds normally, but the subsequent rate-limiter check correctly rejects the call — this is exactly the kind of overload (too many calls *over time*, even with low concurrency) a bulkhead alone, which only tracks simultaneous in-flight count, would never catch on its own; together, the two mechanisms provide complete coverage across both dimensions of load that either one alone would leave a real gap in.

## 7. Gotchas & takeaways

> **Gotcha:** a bulkhead and a rate limiter address genuinely different, orthogonal concerns — mistaking one for adequately covering the other (assuming a bulkhead alone protects against request frequency, or a rate limiter alone protects against concurrent resource exhaustion) leaves a real gap, as both directions of Level 3's demonstration show; a thorough protection strategy for a dependency with both concurrency and throughput constraints needs both mechanisms applied deliberately, not either one alone assumed to cover both.

- A rate limiter caps the number of operations permitted per unit of time, addressing throughput, while a bulkhead caps the number of simultaneously in-flight operations, addressing concurrency — two genuinely different, orthogonal dimensions of load.
- A high-frequency but low-concurrency call pattern (many fast, sequential calls) can overwhelm a rate-constrained resource while never triggering a concurrency-based bulkhead at all.
- A high-concurrency but low-frequency call pattern (many slow, simultaneous calls) can overwhelm a concurrency-constrained resource while staying well within a rate limit.
- The two patterns are frequently used together, each guarding against the specific kind of overload the other structurally cannot detect.
- Several concrete algorithms — token bucket, leaky bucket, fixed/sliding window counters, each covered next in this section — implement the same basic rate-limiting idea with different tradeoffs around burst tolerance and smoothness of enforcement.
