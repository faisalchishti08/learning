---
card: microservices
gi: 253
slug: minimum-number-of-calls
title: "Minimum number of calls"
---

## 1. What it is

The minimum number of calls is a circuit breaker configuration guard that prevents the [failure rate](0250-failure-rate-threshold.md) or [slow-call rate](0251-slow-call-rate-threshold.md) from being evaluated at all until at least that many calls have been recorded in the current [sliding window](0252-sliding-window-count-based-time-based.md) — below that count, the breaker stays closed regardless of what percentage of those few calls happened to fail.

## 2. Why & when

A percentage computed from a very small sample is statistically unreliable: one failure out of one call is a 100% failure rate, and one failure out of two calls is 50%, but neither number says much trustworthy about the dependency's actual health — a single unlucky, transient failure during a quiet traffic period could trip a breaker configured with, say, a 50% threshold, purely because the sample size happened to be tiny at that moment. This risk is especially acute for [time-based sliding windows](0252-sliding-window-count-based-time-based.md), where a quiet period can leave very few calls in the tracked window even though the time span itself is fixed. The minimum number of calls guard fixes this by requiring a statistically meaningful sample size before the rate is trusted enough to act on at all.

Configure this minimum based on how large a sample is needed for the computed rate to be a trustworthy signal for a given dependency's typical traffic pattern — a reasonable default (Resilience4j's default is 100) works for most cases, but a lower-traffic dependency may need a smaller minimum to ever evaluate a rate at all, while a very high-traffic one can afford a larger minimum for extra statistical confidence.

## 3. Core concept

The rate is computed and compared against its threshold only when the sliding window contains at least `minimumNumberOfCalls` entries; below that count, the breaker unconditionally stays closed, regardless of how extreme the failure proportion of the few tracked calls happens to be.

```java
CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .failureRateThreshold(50)
    .minimumNumberOfCalls(10) // do NOT evaluate the rate until AT LEAST 10 calls have occurred
    .slidingWindowSize(10)
    .build();

// 1 failure out of 1 call = 100% failure rate -- but BELOW minimumNumberOfCalls -- breaker stays CLOSED regardless
// 6 failures out of 10 calls = 60% failure rate -- AT the minimum, threshold crossed -- breaker TRIPS
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="With too few calls recorded, even a one hundred percent failure rate does not trip the breaker because the sample size is below the configured minimum; once enough calls accumulate, the same or a lower failure rate is evaluated and can trip the breaker" >
  <rect x="20" y="20" width="270" height="60" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="155" y="42" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">1 call, 100% failed</text>
  <text x="155" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">BELOW minimumNumberOfCalls</text>
  <text x="155" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">rate NOT evaluated -- stays CLOSED</text>

  <rect x="350" y="20" width="270" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">10 calls, 60% failed</text>
  <text x="485" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">AT/ABOVE minimumNumberOfCalls</text>
  <text x="485" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">rate EVALUATED -- can TRIP</text>
</svg>

Below the minimum, the rate is never even checked; above it, the same computation becomes an actionable, trustworthy signal.

## 5. Runnable example

Scenario: a breaker with no minimum-calls guard that trips on a single unlucky failure during a quiet period, refactored to add the guard and correctly stay closed until enough calls accumulate, and finally demonstrating how the guard specifically protects a time-based window during a realistic burst-then-quiet traffic pattern, where without it a single call during the quiet period would otherwise trip the breaker unnecessarily.

### Level 1 — Basic

```java
// File: NoMinimumGuard.java -- evaluates the failure rate from EVEN
// ONE call -- a SINGLE unlucky failure trips the breaker unnecessarily.
import java.util.*;

public class NoMinimumGuard {
    static Deque<Boolean> window = new ArrayDeque<>();
    static boolean breakerOpen = false;

    static void recordCall(boolean succeeded) {
        window.addLast(succeeded);
        long failures = window.stream().filter(s -> !s).count();
        double failureRate = (double) failures / window.size(); // evaluated REGARDLESS of sample size
        if (failureRate >= 0.5) breakerOpen = true;
    }

    public static void main(String[] args) {
        recordCall(false); // ONE isolated, unlucky failure -- e.g. a single transient network blip
        System.out.println("After 1 call (1 failure): failure rate = 100%, breaker: " + (breakerOpen ? "OPEN (tripped on ONE data point!)" : "CLOSED"));
    }
}
```

**How to run:** `javac NoMinimumGuard.java && java NoMinimumGuard` (JDK 17+).

Expected output:
```
After 1 call (1 failure): failure rate = 100%, breaker: OPEN (tripped on ONE data point!)
```

### Level 2 — Intermediate

```java
// File: MinimumCallsGuard.java -- requires AT LEAST minimumNumberOfCalls
// before evaluating the rate at all -- the SAME single failure no longer
// trips the breaker prematurely.
import java.util.*;

public class MinimumCallsGuard {
    static Deque<Boolean> window = new ArrayDeque<>();
    static final int MINIMUM_CALLS = 10;
    static boolean breakerOpen = false;

    static void recordCall(boolean succeeded) {
        window.addLast(succeeded);
        if (window.size() < MINIMUM_CALLS) return; // NOT ENOUGH DATA YET -- skip evaluation entirely

        long failures = window.stream().filter(s -> !s).count();
        double failureRate = (double) failures / window.size();
        if (failureRate >= 0.5) breakerOpen = true;
    }

    public static void main(String[] args) {
        recordCall(false); // the SAME single failure as Level 1
        System.out.println("After 1 call: breaker = " + (breakerOpen ? "OPEN" : "CLOSED (correctly waiting for more data)"));

        for (int i = 0; i < 9; i++) recordCall(true); // 9 MORE successes, reaching the minimum of 10 total calls
        System.out.println("After 10 calls (1 failure, 9 successes = 10% rate): breaker = " + (breakerOpen ? "OPEN" : "CLOSED (10% is well under the 50% threshold)"));
    }
}
```

**How to run:** `javac MinimumCallsGuard.java && java MinimumCallsGuard` (JDK 17+).

Expected output:
```
After 1 call: breaker = CLOSED (correctly waiting for more data)
After 10 calls (1 failure, 9 successes = 10% rate): breaker = CLOSED (10% is well under the 50% threshold)
```

### Level 3 — Advanced

```java
// File: GuardsATimeBasedWindowDuringQuietPeriod.java -- combines the
// minimum-calls guard with a TIME-BASED window, showing it protecting
// EXACTLY the low-traffic scenario that motivated it: a quiet period
// leaving very few calls in an otherwise fixed time span.
import java.util.*;

public class GuardsATimeBasedWindowDuringQuietPeriod {
    record CallRecord(long timestamp, boolean succeeded) {}
    static Deque<CallRecord> window = new ArrayDeque<>();
    static final long WINDOW_DURATION_MILLIS = 5000;
    static final int MINIMUM_CALLS = 5;
    static boolean breakerOpen = false;

    static void recordCall(long now, boolean succeeded) {
        window.addLast(new CallRecord(now, succeeded));
        while (!window.isEmpty() && now - window.peekFirst().timestamp() > WINDOW_DURATION_MILLIS) window.removeFirst();

        if (window.size() < MINIMUM_CALLS) {
            System.out.println("  [t=" + now + "] window size=" + window.size() + " -- BELOW minimum (" + MINIMUM_CALLS + "), rate NOT evaluated");
            return;
        }
        long failures = window.stream().filter(c -> !c.succeeded()).count();
        double failureRate = (double) failures / window.size();
        breakerOpen = failureRate >= 0.5;
        System.out.println("  [t=" + now + "] window size=" + window.size() + ", failure rate=" + (int)(failureRate * 100) + "%, breaker=" + (breakerOpen ? "OPEN" : "CLOSED"));
    }

    public static void main(String[] args) {
        // a BURST -- 5 calls, all fast, all succeed
        for (int i = 0; i < 5; i++) recordCall(1000 + i * 100, true);

        // a QUIET period -- the burst calls AGE OUT of the 5s window, leaving very little data
        recordCall(1000 + 6000, false); // ONE failure, alone in the window after the burst ages out
        System.out.println("\nWithout the minimum-calls guard, THIS single failure (100% of a 1-call window) would have tripped the breaker.");
        System.out.println("With the guard, it correctly waits for MORE data before deciding anything.");
    }
}
```

**How to run:** `javac GuardsATimeBasedWindowDuringQuietPeriod.java && java GuardsATimeBasedWindowDuringQuietPeriod` (JDK 17+).

Expected output:
```
  [t=1000] window size=1 -- BELOW minimum (5), rate NOT evaluated
  [t=1100] window size=2 -- BELOW minimum (5), rate NOT evaluated
  [t=1200] window size=3 -- BELOW minimum (5), rate NOT evaluated
  [t=1300] window size=4 -- BELOW minimum (5), rate NOT evaluated
  [t=1400] window size=5, failure rate=0%, breaker=CLOSED
  [t=7000] window size=1 -- BELOW minimum (5), rate NOT evaluated

Without the minimum-calls guard, THIS single failure (100% of a 1-call window) would have tripped the breaker.
With the guard, it correctly waits for MORE data before deciding anything.
```

## 6. Walkthrough

1. **Level 1, evaluating from a sample of one** — `recordCall` computes `failureRate` immediately after adding any single call to `window`, with no check on how many calls have actually accumulated; a single call that happens to fail produces a computed rate of exactly 100%, which crosses the 50% threshold and trips the breaker based on essentially no real evidence.
2. **Level 2, the guard withholding judgment** — `recordCall` now checks `window.size() < MINIMUM_CALLS` and returns immediately if true, meaning no rate computation or breaker-state decision happens at all until at least 10 calls have been recorded — the identical single failure that tripped Level 1's breaker now produces no decision whatsoever, correctly deferred until more evidence accumulates.
3. **Level 2, the trustworthy evaluation once enough data exists** — after nine more (successful) calls bring the total to 10, meeting `MINIMUM_CALLS`, the rate is finally computed: 1 failure out of 10 calls is 10%, comfortably under the 50% threshold, and the breaker correctly stays closed — the same original failure, now properly contextualized within a larger, statistically meaningful sample, no longer looks alarming.
4. **Level 3, combining the guard with a time-based window** — `recordCall` first evicts any window entries older than `WINDOW_DURATION_MILLIS` (mirroring [time-based sliding window](0252-sliding-window-count-based-time-based.md) behavior), and only *then* checks the minimum-calls guard against whatever entries remain after that eviction.
5. **Level 3, the burst filling the window normally** — the first five calls, all within a tight 400ms span, accumulate in the window one at a time; the guard correctly withholds evaluation for the first four (sizes 1 through 4), and only evaluates once the fifth call brings the window to exactly `MINIMUM_CALLS` (5), computing a healthy 0% failure rate.
6. **Level 3, the quiet period's single call correctly withheld** — by the time the next call arrives 6 seconds later, every one of the five burst calls has aged out of the 5-second time-based window (since `now - timestamp > WINDOW_DURATION_MILLIS` for all of them), leaving the window holding just that one new, failing call; the guard correctly detects this window size (1) is below `MINIMUM_CALLS` and withholds evaluation entirely, exactly preventing the premature, statistically meaningless trip that Level 1's unguarded logic (and an unguarded time-based window generally) would have triggered from a single unlucky data point during a quiet traffic period.

## 7. Gotchas & takeaways

> **Gotcha:** setting `minimumNumberOfCalls` too high for a genuinely low-traffic dependency can mean the breaker effectively never evaluates its rate at all — if a dependency only receives a handful of calls per hour and the minimum is set to 100, the breaker may take an unreasonably long time to ever accumulate enough data to trip, even during a genuine, sustained outage; the minimum needs to be calibrated to the dependency's actual expected traffic volume, not copied uniformly from a high-traffic dependency's configuration.

- The minimum number of calls guard prevents a circuit breaker's failure or slow-call rate from being evaluated at all until a statistically meaningful sample size has accumulated in the sliding window.
- Without this guard, a single unlucky failure during a low-traffic period can compute a misleadingly extreme rate (up to 100% from a sample of one) and trip the breaker on essentially no real evidence.
- This guard is especially important for time-based sliding windows, where a quiet traffic period can leave very few calls tracked even though the time span itself stays fixed.
- The guard doesn't change the failure or slow-call rate computation itself — it only determines whether that computation is trusted enough to act on yet.
- The minimum should be calibrated to a specific dependency's actual traffic volume — too low a minimum risks premature trips on noisy data, while too high a minimum can prevent the breaker from ever reacting to a genuine, sustained problem for a low-traffic dependency.
