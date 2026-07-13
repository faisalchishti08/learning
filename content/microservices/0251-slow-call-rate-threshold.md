---
card: microservices
gi: 251
slug: slow-call-rate-threshold
title: "Slow-call rate threshold"
---

## 1. What it is

The slow-call rate threshold is a second, independent condition — alongside the [failure rate threshold](0250-failure-rate-threshold.md) — that can trip a circuit breaker: a configurable percentage of recent calls that exceed a defined duration counts as "slow," and if that proportion crosses its own threshold, the breaker trips even though those calls technically returned successfully rather than throwing an exception.

## 2. Why & when

A dependency that responds successfully but very slowly is often a worse problem than one that fails outright and quickly — a call that hangs for ten seconds before finally succeeding ties up a caller's thread or connection for that entire duration, contributing directly to the resource-accumulation mechanism behind [cascading failures](0243-cascading-failures.md), even though it never registers as a *failure* in the traditional sense. A circuit breaker that only tracks failure rate would completely miss this scenario: every one of those slow calls counts as a success, so the failure rate stays at 0% no matter how badly the dependency is actually degrading the caller's own performance. The slow-call rate threshold closes this gap by tracking a second, independent signal — call duration — and tripping the breaker based on that signal too, regardless of whether the calls ultimately succeeded.

Configure a slow-call threshold for any dependency where an unacceptably slow-but-successful response is nearly as harmful to the caller as an outright failure — which is true for most synchronous, latency-sensitive call paths. A background or batch process with much looser latency requirements may reasonably tolerate slow calls without needing this protection.

## 3. Core concept

Each call's duration is measured and compared against a configured `slowCallDurationThreshold`; calls exceeding it are counted as "slow" within the same sliding window used for failure tracking, and a separate `slowCallRateThreshold` percentage, if crossed, trips the breaker independently of the failure rate — a dependency can trip a breaker for being *too slow*, even while technically succeeding on every call.

```java
CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .slowCallDurationThreshold(Duration.ofSeconds(2)) // a call taking LONGER than this counts as "slow"
    .slowCallRateThreshold(50) // trip if 50%+ of recent calls are "slow" -- INDEPENDENT of failure rate
    .failureRateThreshold(50)  // the ORIGINAL failure-based condition, still tracked separately
    .slidingWindowSize(10)
    .build();

// a dependency that SUCCEEDS on every call, but takes 3 seconds each time:
// failure rate = 0% (never fails) -- would NOT trip a failure-only breaker
// slow-call rate = 100% (every call exceeds the 2s threshold) -- TRIPS via the slow-call condition instead
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A circuit breaker evaluates two independent conditions against its sliding window of recent calls -- failure rate and slow-call rate -- and trips if either one crosses its own configured threshold, even when the other stays at zero" >
  <rect x="20" y="65" width="180" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="88" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Failure rate: 0%</text>
  <text x="110" y="104" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">every call SUCCEEDS</text>

  <rect x="230" y="65" width="180" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="88" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Slow-call rate: 100%</text>
  <text x="320" y="104" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">every call EXCEEDS duration threshold</text>

  <rect x="450" y="65" width="160" height="60" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="530" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Breaker TRIPS</text>
  <text x="530" y="104" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">via the SLOW-CALL condition</text>

  <line x1="410" y1="95" x2="448" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr251)"/>

  <defs>
    <marker id="arr251" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

A perfectly successful failure rate doesn't prevent tripping when the slow-call rate independently crosses its own threshold.

## 5. Runnable example

Scenario: a breaker built with only failure-rate tracking, which completely misses a dependency that's always successful but always slow, refactored to add independent slow-call tracking that correctly trips in that exact scenario, and finally demonstrating both conditions evaluated together against a realistic mixed sequence of fast successes, slow successes, and outright failures.

### Level 1 — Basic

```java
// File: FailureRateOnlyMissesSlowness.java -- tracks ONLY failure rate;
// a dependency that's ALWAYS SLOW but NEVER fails goes COMPLETELY undetected.
public class FailureRateOnlyMissesSlowness {
    static boolean breakerOpen = false;

    static void recordCall(boolean succeeded, long durationMillis) {
        // this breaker has NO IDEA how long the call took -- only whether it succeeded
        if (!succeeded) breakerOpen = true;
    }

    public static void main(String[] args) {
        for (int i = 0; i < 10; i++) recordCall(true, 3000); // EVERY call succeeds, but takes 3 FULL SECONDS each
        System.out.println("10/10 calls succeeded, but EVERY ONE took 3000ms. Breaker: " + (breakerOpen ? "OPEN" : "CLOSED (completely missed the problem!)"));
    }
}
```

**How to run:** `javac FailureRateOnlyMissesSlowness.java && java FailureRateOnlyMissesSlowness` (JDK 17+).

Expected output:
```
10/10 calls succeeded, but EVERY ONE took 3000ms. Breaker: CLOSED (completely missed the problem!)
```

### Level 2 — Intermediate

```java
// File: SlowCallRateDetectsIt.java -- adds INDEPENDENT slow-call tracking;
// now correctly TRIPS on the SAME scenario Level 1 completely missed.
import java.util.*;

public class SlowCallRateDetectsIt {
    static Deque<Boolean> recentSlowCalls = new ArrayDeque<>();
    static final int WINDOW_SIZE = 10;
    static final long SLOW_THRESHOLD_MILLIS = 2000; // calls LONGER than this count as "slow"
    static final double SLOW_RATE_THRESHOLD = 0.5;  // trip if 50%+ are slow
    static boolean breakerOpen = false;

    static void recordCall(boolean succeeded, long durationMillis) {
        boolean isSlow = durationMillis > SLOW_THRESHOLD_MILLIS; // INDEPENDENT of success/failure
        recentSlowCalls.addLast(isSlow);
        if (recentSlowCalls.size() > WINDOW_SIZE) recentSlowCalls.removeFirst();

        if (recentSlowCalls.size() >= WINDOW_SIZE) {
            long slowCount = recentSlowCalls.stream().filter(s -> s).count();
            double slowRate = (double) slowCount / recentSlowCalls.size();
            if (slowRate >= SLOW_RATE_THRESHOLD) breakerOpen = true; // TRIPS regardless of the failure rate
        }
    }

    public static void main(String[] args) {
        for (int i = 0; i < 10; i++) recordCall(true, 3000); // the SAME scenario as Level 1: always succeeds, always slow
        System.out.println("10/10 calls succeeded, but ALL took 3000ms. Breaker: " + (breakerOpen ? "OPEN (correctly detected slowness!)" : "CLOSED"));
    }
}
```

**How to run:** `javac SlowCallRateDetectsIt.java && java SlowCallRateDetectsIt` (JDK 17+).

Expected output:
```
10/10 calls succeeded, but ALL took 3000ms. Breaker: OPEN (correctly detected slowness!)
```

### Level 3 — Advanced

```java
// File: BothConditionsEvaluatedTogether.java -- BOTH conditions tracked
// INDEPENDENTLY against a REALISTIC mixed sequence -- fast successes,
// slow successes, and outright failures -- showing EITHER condition can
// trip the breaker on its own.
import java.util.*;

public class BothConditionsEvaluatedTogether {
    record CallResult(boolean succeeded, long durationMillis) {}

    static Deque<CallResult> window = new ArrayDeque<>();
    static final int WINDOW_SIZE = 10;
    static final long SLOW_THRESHOLD_MILLIS = 2000;
    static final double FAILURE_RATE_THRESHOLD = 0.5;
    static final double SLOW_RATE_THRESHOLD = 0.5;

    static String evaluateBreakerState() {
        if (window.size() < WINDOW_SIZE) return "CLOSED (not enough data yet)";
        long failures = window.stream().filter(c -> !c.succeeded()).count();
        long slowCalls = window.stream().filter(c -> c.durationMillis() > SLOW_THRESHOLD_MILLIS).count();
        double failureRate = (double) failures / window.size();
        double slowRate = (double) slowCalls / window.size();

        if (failureRate >= FAILURE_RATE_THRESHOLD) return "OPEN (tripped via FAILURE rate: " + (int)(failureRate * 100) + "%)";
        if (slowRate >= SLOW_RATE_THRESHOLD) return "OPEN (tripped via SLOW-CALL rate: " + (int)(slowRate * 100) + "%)";
        return "CLOSED (both rates under threshold)";
    }

    static void recordCall(boolean succeeded, long durationMillis) {
        window.addLast(new CallResult(succeeded, durationMillis));
        if (window.size() > WINDOW_SIZE) window.removeFirst();
    }

    public static void main(String[] args) {
        // a REALISTIC mixed sequence: mostly fast successes, a FEW very slow ones, NO outright failures
        long[] durations = {100, 100, 3000, 100, 3000, 100, 3000, 100, 3000, 3000}; // 5 of 10 are slow (>2000ms)
        for (long d : durations) recordCall(true, d); // ALL succeed -- failure rate stays 0%

        System.out.println(evaluateBreakerState());
    }
}
```

**How to run:** `javac BothConditionsEvaluatedTogether.java && java BothConditionsEvaluatedTogether` (JDK 17+).

Expected output:
```
OPEN (tripped via SLOW-CALL rate: 50%)
```

## 6. Walkthrough

1. **Level 1, the blind spot** — `recordCall` only ever checks `succeeded`, completely ignoring `durationMillis`; a dependency that succeeds on every one of ten calls, each taking 3000ms, produces a breaker state that stays `CLOSED`, even though a real caller experiencing this would have been blocked for 3 full seconds on every single request.
2. **Level 2, tracking duration independently** — `recordCall` computes `isSlow` purely from `durationMillis > SLOW_THRESHOLD_MILLIS`, entirely separate from the `succeeded` parameter, and maintains its own sliding window (`recentSlowCalls`) tracking only this slowness signal.
3. **Level 2, the correct detection** — running the identical scenario from Level 1 (ten successful, 3000ms calls) through this logic correctly sets `breakerOpen` to `true`, since 100% of calls exceed the 2000ms `SLOW_THRESHOLD_MILLIS`, crossing the 50% `SLOW_RATE_THRESHOLD` — the exact detection Level 1's failure-only tracking was structurally incapable of making.
4. **Level 3, unifying both signals in one window** — `CallResult` bundles both `succeeded` and `durationMillis` for each call, and `window` tracks the full record rather than a boolean derived from just one dimension, letting `evaluateBreakerState` compute both `failureRate` and `slowRate` independently from the same underlying tracked data.
5. **Level 3, checking failure rate first, then slow-call rate** — `evaluateBreakerState` checks `failureRate >= FAILURE_RATE_THRESHOLD` first, and only if that's not met, checks `slowRate >= SLOW_RATE_THRESHOLD` — mirroring how a real circuit breaker evaluates both conditions and trips if *either* one independently crosses its threshold, regardless of the other's value.
6. **Level 3, the mixed sequence's outcome** — `durations` contains five calls at 100ms (fast) and five at 3000ms (slow), all of which `succeeded = true`, so `failureRate` computes to exactly `0%` (no trip via that path), but `slowRate` computes to `50%`, meeting the `SLOW_RATE_THRESHOLD` and correctly reporting `"OPEN (tripped via SLOW-CALL rate: 50%)"` — demonstrating both conditions being evaluated together against one realistic mixed workload, with the slow-call condition alone (independent of a perfect 0% failure rate) being sufficient to trip the breaker.

## 7. Gotchas & takeaways

> **Gotcha:** the `slowCallDurationThreshold` needs to be set meaningfully above a dependency's normal, healthy latency — setting it too close to typical response time will flag ordinary, acceptable variance as "slow" and trip the breaker unnecessarily during completely normal operation; this threshold should be informed by the dependency's actual observed latency distribution (e.g., a value well above its normal p99), not an arbitrary round number.

- The slow-call rate threshold trips a circuit breaker based on response *duration*, independent of and in addition to the [failure rate threshold](0250-failure-rate-threshold.md) based on outcome.
- This closes a real blind spot: a dependency that always succeeds but responds very slowly ties up caller resources just as harmfully as an outright failure, yet contributes nothing to a failure-rate-only breaker's trip condition.
- Both conditions are typically tracked over the same sliding window of recent calls, and either one crossing its own configured threshold trips the breaker.
- The slow-call duration threshold should be set based on a dependency's actual, observed healthy latency, not an arbitrary value — too low a threshold flags normal variance as slowness and trips unnecessarily.
- This is one of two independent trip conditions Resilience4j's circuit breaker supports natively, letting a single breaker configuration protect against both outright failure and unacceptable-but-technically-successful slowness.
