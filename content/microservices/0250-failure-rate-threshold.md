---
card: microservices
gi: 250
slug: failure-rate-threshold
title: "Failure rate threshold"
---

## 1. What it is

The failure rate threshold is the configurable percentage of recent calls that must fail before a [circuit breaker](0248-circuit-breaker-pattern.md) trips from closed to open — for example, a 50% threshold means the breaker trips once half or more of the calls in its tracked window have failed, rather than tripping on the very first failure or requiring every single call to fail.

## 2. Why & when

Tripping on the first single failure would make a circuit breaker far too sensitive — a single transient blip (one slow response, one momentary network hiccup) would unnecessarily cut off an otherwise healthy dependency, triggering fallback behavior when the real, underlying dependency was actually fine. Requiring literally every call to fail before tripping, on the other hand, would make the breaker far too slow to react, letting a genuinely struggling dependency continue receiving full traffic well past the point where protection was actually needed. A percentage-based threshold, evaluated over a tracked window of recent calls (covered by name in [sliding window count-based/time-based](0252-sliding-window-count-based-time-based.md)), strikes a deliberate, tunable balance between these two extremes — sensitive enough to react to a genuine, sustained problem, but tolerant enough to absorb occasional, isolated failures without unnecessary tripping.

Tune the failure rate threshold based on how tolerant a specific dependency's calls actually are of individual failures, and how costly a false trip (cutting off a still-healthy dependency) versus a missed trip (continuing to hit a genuinely failing one) would be for that particular call path — there's no universally correct number, only a deliberate trade-off appropriate to the specific dependency and its criticality.

## 3. Core concept

The threshold is evaluated against a fixed-size window of the most recent calls, and the breaker trips the moment the proportion of failures within that window meets or exceeds the configured percentage — a small number of scattered failures among many successes stays under threshold, while a sustained run of failures crosses it.

```java
CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .failureRateThreshold(50) // trip once 50% (or more) of tracked calls have failed
    .slidingWindowSize(10)    // evaluated over the LAST 10 calls
    .minimumNumberOfCalls(10) // don't evaluate the rate until AT LEAST this many calls have occurred
    .build();

// 3 failures out of 10 tracked calls = 30% failure rate -- BELOW the 50% threshold, breaker stays CLOSED
// 6 failures out of 10 tracked calls = 60% failure rate -- AT/ABOVE the 50% threshold, breaker TRIPS to OPEN
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A sliding window of ten recent calls with three failures sits below a fifty percent threshold and keeps the breaker closed, while the same window with six failures crosses the threshold and trips the breaker open" >
  <text x="160" y="25" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">3/10 failed = 30% -- BELOW threshold</text>
  <rect x="20" y="35" width="28" height="28" fill="#1c2430" stroke="#8b949e"/><rect x="52" y="35" width="28" height="28" fill="#1c2430" stroke="#8b949e"/>
  <rect x="84" y="35" width="28" height="28" fill="#79c0ff" stroke="#79c0ff"/><rect x="116" y="35" width="28" height="28" fill="#1c2430" stroke="#8b949e"/>
  <rect x="148" y="35" width="28" height="28" fill="#1c2430" stroke="#8b949e"/><rect x="180" y="35" width="28" height="28" fill="#79c0ff" stroke="#79c0ff"/>
  <rect x="212" y="35" width="28" height="28" fill="#1c2430" stroke="#8b949e"/><rect x="244" y="35" width="28" height="28" fill="#1c2430" stroke="#8b949e"/>
  <rect x="276" y="35" width="28" height="28" fill="#79c0ff" stroke="#79c0ff"/><rect x="308" y="35" width="28" height="28" fill="#1c2430" stroke="#8b949e"/>

  <text x="480" y="25" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">6/10 failed = 60% -- CROSSES threshold, TRIPS</text>
  <rect x="340" y="35" width="28" height="28" fill="#79c0ff" stroke="#79c0ff"/><rect x="372" y="35" width="28" height="28" fill="#79c0ff" stroke="#79c0ff"/>
  <rect x="404" y="35" width="28" height="28" fill="#1c2430" stroke="#8b949e"/><rect x="436" y="35" width="28" height="28" fill="#79c0ff" stroke="#79c0ff"/>
  <rect x="468" y="35" width="28" height="28" fill="#79c0ff" stroke="#79c0ff"/><rect x="500" y="35" width="28" height="28" fill="#1c2430" stroke="#8b949e"/>
  <rect x="532" y="35" width="28" height="28" fill="#79c0ff" stroke="#79c0ff"/><rect x="564" y="35" width="28" height="28" fill="#1c2430" stroke="#8b949e"/>
  <rect x="596" y="35" width="28" height="28" fill="#79c0ff" stroke="#79c0ff"/>

  <text x="320" y="100" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">blue = failed call, dark = succeeded call, out of the last 10</text>
</svg>

The same window size with more failures crosses the threshold; the same threshold tolerates a smaller number of scattered failures.

## 5. Runnable example

Scenario: a circuit breaker built with a fixed trip-on-first-failure rule (far too sensitive, tripping on an isolated blip), refactored to use a percentage-based failure rate threshold evaluated over a tracked window (tolerating occasional failures while still catching a genuine sustained problem), and finally demonstrating tuning the threshold itself and observing how a stricter versus looser threshold changes exactly when the same call sequence trips the breaker.

### Level 1 — Basic

```java
// File: TripsOnFirstFailure.java -- WAY too sensitive: a SINGLE
// transient failure trips the breaker, even though the dependency is
// mostly healthy.
import java.util.*;

public class TripsOnFirstFailure {
    static boolean breakerOpen = false;

    static void recordCall(boolean succeeded) {
        if (!succeeded) breakerOpen = true; // trips on the VERY FIRST failure -- overly sensitive
    }

    public static void main(String[] args) {
        // a MOSTLY healthy dependency: 9 successes, ONE isolated blip
        boolean[] callResults = {true, true, true, false, true, true, true, true, true, true};
        for (boolean succeeded : callResults) recordCall(succeeded);

        System.out.println("9/10 calls succeeded (90% success rate), but breaker is: " + (breakerOpen ? "OPEN (tripped unnecessarily!)" : "CLOSED"));
    }
}
```

**How to run:** `javac TripsOnFirstFailure.java && java TripsOnFirstFailure` (JDK 17+).

Expected output:
```
9/10 calls succeeded (90% success rate), but breaker is: OPEN (tripped unnecessarily!)
```

### Level 2 — Intermediate

```java
// File: PercentageThresholdOverWindow.java -- uses a PERCENTAGE-based
// threshold evaluated over a SLIDING WINDOW -- tolerates the SAME
// isolated blip, but still WOULD catch a genuine sustained problem.
import java.util.*;

public class PercentageThresholdOverWindow {
    static Deque<Boolean> recentCalls = new ArrayDeque<>(); // the SLIDING WINDOW
    static final int WINDOW_SIZE = 10;
    static final double FAILURE_RATE_THRESHOLD = 0.5; // 50%
    static boolean breakerOpen = false;

    static void recordCall(boolean succeeded) {
        recentCalls.addLast(succeeded);
        if (recentCalls.size() > WINDOW_SIZE) recentCalls.removeFirst(); // keep only the LAST WINDOW_SIZE calls

        if (recentCalls.size() >= WINDOW_SIZE) { // only evaluate once ENOUGH data exists
            long failures = recentCalls.stream().filter(s -> !s).count();
            double failureRate = (double) failures / recentCalls.size();
            breakerOpen = failureRate >= FAILURE_RATE_THRESHOLD;
        }
    }

    public static void main(String[] args) {
        boolean[] mostlyHealthy = {true, true, true, false, true, true, true, true, true, true}; // ONE blip, same as Level 1
        for (boolean succeeded : mostlyHealthy) recordCall(succeeded);
        System.out.println("Mostly-healthy sequence (1 failure out of 10): breaker is " + (breakerOpen ? "OPEN" : "CLOSED"));

        recentCalls.clear(); breakerOpen = false; // reset for the second scenario
        boolean[] genuinelyFailing = {true, false, false, true, false, false, true, false, false, false}; // 6/10 failed -- 60%
        for (boolean succeeded : genuinelyFailing) recordCall(succeeded);
        System.out.println("Genuinely-failing sequence (6 failures out of 10): breaker is " + (breakerOpen ? "OPEN" : "CLOSED"));
    }
}
```

**How to run:** `javac PercentageThresholdOverWindow.java && java PercentageThresholdOverWindow` (JDK 17+).

Expected output:
```
Mostly-healthy sequence (1 failure out of 10): breaker is CLOSED
Genuinely-failing sequence (6 failures out of 10): breaker is OPEN
```

### Level 3 — Advanced

```java
// File: TuningTheThresholdChangesTiming.java -- runs the SAME call
// sequence against MULTIPLE different threshold values, showing EXACTLY
// how the chosen threshold changes WHEN (or WHETHER) the breaker trips.
import java.util.*;

public class TuningTheThresholdChangesTiming {
    static int simulateWithThreshold(double threshold, boolean[] callResults) {
        Deque<Boolean> recentCalls = new ArrayDeque<>();
        int windowSize = 10;
        for (int i = 0; i < callResults.length; i++) {
            recentCalls.addLast(callResults[i]);
            if (recentCalls.size() > windowSize) recentCalls.removeFirst();
            if (recentCalls.size() >= windowSize) {
                long failures = recentCalls.stream().filter(s -> !s).count();
                double rate = (double) failures / recentCalls.size();
                if (rate >= threshold) return i + 1; // returns the CALL NUMBER at which it tripped
            }
        }
        return -1; // never tripped
    }

    public static void main(String[] args) {
        // a call sequence with a GRADUALLY WORSENING failure rate over time
        boolean[] worseningSequence = {
            true, true, true, true, true, true, true, true, true, true,   // calls 1-10: 100% healthy
            false, true, false, true, false, true, false, true, false, true, // calls 11-20: 50% failing
            false, false, false, true, false, false, false, true, false, false // calls 21-30: 80% failing
        };

        for (double threshold : new double[]{0.30, 0.50, 0.70}) {
            int trippedAt = simulateWithThreshold(threshold, worseningSequence);
            System.out.println("Threshold " + (int)(threshold * 100) + "%: tripped at call #" +
                (trippedAt == -1 ? "never" : trippedAt));
        }
        System.out.println("\nA STRICTER (lower) threshold trips EARLIER, as the failure rate first climbs;");
        System.out.println("a LOOSER (higher) threshold waits for a MORE severe, sustained problem before tripping.");
    }
}
```

**How to run:** `javac TuningTheThresholdChangesTiming.java && java TuningTheThresholdChangesTiming` (JDK 17+).

Expected output:
```
Threshold 30%: tripped at call #17
Threshold 50%: tripped at call #20
Threshold 70%: tripped at call #24

A STRICTER (lower) threshold trips EARLIER, as the failure rate first climbs;
a LOOSER (higher) threshold waits for a MORE severe, sustained problem before tripping.
```

## 6. Walkthrough

1. **Level 1, the oversensitive baseline** — `recordCall` sets `breakerOpen = true` the instant *any* single call fails, with no consideration of how many calls succeeded around it; even though 9 out of 10 calls in the test sequence succeeded (a 90% success rate, clearly indicating a healthy dependency), the one isolated failure trips the breaker anyway — an unnecessary, overly aggressive reaction.
2. **Level 2, evaluating a rate over a window instead** — `recordCall` maintains `recentCalls` as a fixed-size sliding window (evicting the oldest entry once it exceeds `WINDOW_SIZE`), and only sets `breakerOpen` based on the *proportion* of failures within that window, not the mere presence of any single failure.
3. **Level 2, tolerating the same blip that tripped Level 1** — running the identical "1 failure out of 10" sequence through this percentage-based logic correctly keeps the breaker `CLOSED`, since a 10% failure rate is well under the configured 50% threshold — exactly the desired behavior for a dependency experiencing an isolated, non-systemic hiccup.
4. **Level 2, still catching a genuine problem** — the second test sequence, with 6 failures out of 10 calls (a 60% failure rate), correctly trips the breaker to `OPEN`, since that rate crosses the 50% threshold — demonstrating the threshold isn't simply "never trip," but specifically "don't trip on isolated blips, but do trip on a genuinely sustained problem."
5. **Level 3, the same sequence, three different thresholds** — `worseningSequence` models a dependency degrading gradually over time (fully healthy, then 50% failing, then 80% failing), and `simulateWithThreshold` is run three times against this identical sequence with thresholds of 30%, 50%, and 70% respectively, tracking exactly which call number each configuration first trips at.
6. **Level 3, the concrete tuning trade-off observed** — the 30% threshold trips earliest (at call #17, partway through the 50%-failing segment), the 50% threshold trips somewhat later (call #20, right as that segment's window fully reflects a 50% rate), and the 70% threshold trips latest (call #24, only once the more severe 80%-failing segment has been running for a while) — this concrete progression is exactly what "tuning the threshold" means in practice: a lower threshold reacts faster to a *developing* problem (at the cost of potentially reacting to milder issues that might have resolved on their own), while a higher threshold waits for stronger evidence of a *genuinely* severe problem before disrupting traffic to the dependency.

## 7. Gotchas & takeaways

> **Gotcha:** a failure rate threshold is meaningless without also considering the minimum number of calls required before it's evaluated at all — checking a "failure rate" against just one or two calls (100% failure from a sample size of one) is statistically unreliable and can trip a breaker prematurely during low-traffic periods; production circuit breakers (like Resilience4j) require a configured minimum number of calls in the window before the failure rate is evaluated at all, exactly as `minimumNumberOfCalls` does in the concept example.

- The failure rate threshold is the percentage of recent calls, evaluated over a tracked window, that must fail before a circuit breaker trips from closed to open.
- A percentage-based threshold strikes a deliberate balance between tripping too eagerly (on isolated, non-systemic blips) and too slowly (only after every call has failed).
- There's no universally correct threshold value — the right choice depends on how failure-tolerant a specific dependency's calls are and how costly a false trip versus a missed trip would be for that call path.
- A lower (stricter) threshold reacts faster to a developing problem; a higher (looser) threshold requires stronger, more sustained evidence before disrupting traffic — this trade-off is directly observable and tunable.
- The threshold should only be evaluated once a minimum number of calls have occurred in the tracked window; evaluating it against too small a sample produces statistically unreliable, premature trips.
