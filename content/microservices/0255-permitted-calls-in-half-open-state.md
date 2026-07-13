---
card: microservices
gi: 255
slug: permitted-calls-in-half-open-state
title: "Permitted calls in half-open state"
---

## 1. What it is

The permitted number of calls in half-open state is the configured limit on how many trial calls a circuit breaker allows through while probing a dependency's recovery, before deciding whether to fully close (if enough of them succeeded) or return to open (if they didn't) — rather than a single trial call, most real breakers allow a small batch, evaluating the resulting mini failure rate against the same threshold logic used in closed state.

## 2. Why & when

A single trial call, as a simplified mental model of half-open might suggest, is a fragile signal — it could succeed purely by luck even while the dependency is still mostly unhealthy, or fail purely by bad luck even though the dependency has genuinely recovered, either way leading to an incorrect transition decision based on a sample size of one. Allowing a small batch of trial calls (typically single digits, not the full traffic volume) and evaluating their aggregate success rate provides a much more statistically reliable signal, while still keeping the probe's load on the recovering dependency deliberately small — the same trade-off that motivates a [minimum number of calls](0253-minimum-number-of-calls.md) guard in closed state, applied specifically to the recovery-testing phase.

Configure a permitted-calls count large enough to give a reasonably trustworthy signal about recovery, but small enough that a still-struggling dependency isn't hit with a meaningful fraction of full production traffic during the probe — a handful of calls (Resilience4j's default is 10) is typically the right order of magnitude, not hundreds and not exactly one.

## 3. Core concept

While in half-open state, the breaker allows up to `permittedNumberOfCallsInHalfOpenState` calls through as trials, tracking their outcomes exactly like a closed-state window; once that many trial calls have completed, the breaker evaluates their aggregate failure rate against its normal threshold to decide whether to close (recovered) or reopen (still failing) — calls beyond that permitted count, while still in half-open, are rejected just like in open state.

```java
CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .permittedNumberOfCallsInHalfOpenState(5) // allow 5 TRIAL calls through during recovery testing
    .failureRateThreshold(50) // the SAME threshold logic applies to these 5 trial calls
    .build();

// during HALF_OPEN:
// calls 1-5: allowed through as TRIALS, outcomes tracked
// call 6+ (while still evaluating): REJECTED, same as OPEN state, until the 5 trials are evaluated
// once all 5 complete: failure rate of THOSE 5 decides CLOSED (recovered) vs OPEN (still failing) again
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="During half-open state, a fixed small number of calls are allowed through as trials while their outcomes are tracked; once that many trials complete, their aggregate failure rate decides whether the breaker closes or returns to open, and any further calls during the evaluation are rejected" >
  <rect x="20" y="65" width="150" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">HALF_OPEN</text>

  <rect x="230" y="20" width="180" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="47" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Calls 1-5: TRIALS allowed</text>

  <rect x="230" y="110" width="180" height="45" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="137" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Call 6+: REJECTED (evaluating)</text>

  <rect x="470" y="65" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">CLOSED or OPEN</text>

  <line x1="170" y1="85" x2="228" y2="42" stroke="#8b949e" marker-end="url(#arr255)"/>
  <line x1="170" y1="90" x2="228" y2="128" stroke="#8b949e" marker-end="url(#arr255)"/>
  <line x1="410" y1="42" x2="468" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr255g)"/>

  <defs>
    <marker id="arr255" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="arr255g" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Only a fixed, small batch of trials is evaluated for the decision; everything else during that window is rejected.

## 5. Runnable example

Scenario: a half-open state modeled first with a single trial call (fragile, easily misled by one lucky or unlucky outcome), refactored to require a small batch of trials evaluated together for a more reliable decision, and finally demonstrating the batch correctly rejecting extra calls beyond the permitted count while trials are still being evaluated, matching real breaker behavior under concurrent traffic during a recovery probe.

### Level 1 — Basic

```java
// File: SingleTrialFragility.java -- ONE trial call decides everything --
// a SINGLE lucky or unlucky outcome can produce the WRONG decision.
public class SingleTrialFragility {
    // simulates a dependency that's MOSTLY still unhealthy, but happens to succeed on THIS particular call
    static boolean simulateCall() { return true; } // got LUCKY -- but the dependency is actually still 80% failing

    public static void main(String[] args) {
        boolean trialSucceeded = simulateCall();
        String decision = trialSucceeded ? "CLOSED (fully recovered!)" : "OPEN (still failing)";
        System.out.println("Single trial result: " + trialSucceeded + " -> decision: " + decision);
        System.out.println("Based on ONE lucky call, the breaker just declared a MOSTLY-STILL-BROKEN dependency fully healthy.");
    }
}
```

**How to run:** `javac SingleTrialFragility.java && java SingleTrialFragility` (JDK 17+).

Expected output:
```
Single trial result: true -> decision: CLOSED (fully recovered!)
Based on ONE lucky call, the breaker just declared a MOSTLY-STILL-BROKEN dependency fully healthy.
```

### Level 2 — Intermediate

```java
// File: BatchOfTrials.java -- requires a BATCH of trial calls, evaluating
// their AGGREGATE rate -- the SAME "mostly still broken" dependency is
// now correctly identified, since ONE lucky call can't dominate the sample.
import java.util.*;

public class BatchOfTrials {
    static final int PERMITTED_CALLS = 5;
    static Random simulatedDependency = new Random(42); // reproducible "mostly broken" behavior

    static boolean simulateCall() { return simulatedDependency.nextDouble() > 0.8; } // ~20% chance of success -- MOSTLY still failing

    public static void main(String[] args) {
        List<Boolean> trialResults = new ArrayList<>();
        for (int i = 0; i < PERMITTED_CALLS; i++) trialResults.add(simulateCall());

        long successes = trialResults.stream().filter(r -> r).count();
        double successRate = (double) successes / PERMITTED_CALLS;
        String decision = successRate >= 0.5 ? "CLOSED (recovered)" : "OPEN (still failing)";

        System.out.println("Trial results: " + trialResults);
        System.out.println("Success rate: " + (int)(successRate * 100) + "% -> decision: " + decision);
    }
}
```

**How to run:** `javac BatchOfTrials.java && java BatchOfTrials` (JDK 17+).

Expected output (deterministic due to fixed seed):
```
Trial results: [false, false, false, true, false]
Success rate: 20% -> decision: OPEN (still failing)
```

### Level 3 — Advanced

```java
// File: ExtraCallsRejectedDuringEvaluation.java -- MORE calls arrive than
// the permitted trial count WHILE trials are still being evaluated --
// the EXTRA calls are REJECTED, exactly like open state, until the
// batch decision is made.
import java.util.*;

public class ExtraCallsRejectedDuringEvaluation {
    enum State { HALF_OPEN, CLOSED, OPEN }
    static State state = State.HALF_OPEN;
    static final int PERMITTED_CALLS = 3;
    static List<Boolean> trialResults = new ArrayList<>();

    static boolean simulateCall(int callIndex) { return callIndex != 1; } // ONE of the trials fails, the rest succeed

    static String handleCall(int callIndex) {
        if (state != State.HALF_OPEN) return "final state reached, no longer accepting trials";
        if (trialResults.size() >= PERMITTED_CALLS) {
            return "REJECTED (already have " + PERMITTED_CALLS + " trials, still evaluating)"; // EXTRA calls rejected
        }

        boolean result = simulateCall(callIndex);
        trialResults.add(result);

        if (trialResults.size() == PERMITTED_CALLS) { // the BATCH is complete -- decide NOW
            long successes = trialResults.stream().filter(r -> r).count();
            state = (successes >= 2) ? State.CLOSED : State.OPEN; // majority-success rule for THIS example
            return "trial " + trialResults.size() + " (" + result + ") -- BATCH COMPLETE, decision: " + state;
        }
        return "trial " + trialResults.size() + " (" + result + ") -- awaiting more trials";
    }

    public static void main(String[] args) {
        // FIVE calls arrive "concurrently" while only 3 are permitted as trials
        for (int i = 0; i < 5; i++) {
            System.out.println("Call " + (i + 1) + ": " + handleCall(i));
        }
    }
}
```

**How to run:** `javac ExtraCallsRejectedDuringEvaluation.java && java ExtraCallsRejectedDuringEvaluation` (JDK 17+).

Expected output:
```
Call 1: trial 1 (true) -- awaiting more trials
Call 2: trial 2 (false) -- awaiting more trials
Call 3: trial 3 (true) -- BATCH COMPLETE, decision: CLOSED
Call 4: final state reached, no longer accepting trials
Call 5: final state reached, no longer accepting trials
```

## 6. Walkthrough

1. **Level 1, the fragile single-trial decision** — `simulateCall` returns `true` (success) exactly once, and that single outcome directly determines the printed decision (`CLOSED`); the comment makes explicit that this "success" happened despite the underlying dependency actually still being mostly broken — a single data point simply cannot distinguish "genuinely recovered" from "got lucky once."
2. **Level 2, requiring a batch before deciding** — `BatchOfTrials` collects `PERMITTED_CALLS` (5) outcomes into `trialResults` before computing any decision at all, using a `Random` seeded deterministically to simulate a dependency that succeeds only about 20% of the time (still mostly broken).
3. **Level 2, the batch correctly identifying continued failure** — across the five simulated trial calls, only one happens to succeed (consistent with the ~20% success rate), producing an aggregate success rate of 20%, well under the 50% needed to close — the batch approach correctly avoids being misled by whichever individual calls happened to succeed or fail, unlike Level 1's single-sample decision.
4. **Level 3, tracking trials up to the permitted limit** — `handleCall` only appends a new outcome to `trialResults` while `trialResults.size() < PERMITTED_CALLS` (3); the moment that count is reached, the very next call attempt hits the `trialResults.size() >= PERMITTED_CALLS` check and is rejected instead of being treated as a fourth trial.
5. **Level 3, the batch completing and deciding** — the third call (index 2) brings `trialResults` to exactly `PERMITTED_CALLS`, triggering the decision logic immediately within that same call's handling; with 2 successes out of 3 trials meeting the majority-success rule used in this example, `state` transitions to `CLOSED`.
6. **Level 3, calls arriving after the decision** — calls 4 and 5, arriving after `state` has already become `CLOSED`, hit the `if (state != State.HALF_OPEN)` check at the very top of `handleCall` and are handled as "final state reached" rather than being evaluated as trials at all — demonstrating that once the permitted-calls batch has produced its decision, the breaker has already moved on to a new, definitive state, and any calls that arrive concurrently during or immediately after the brief evaluation window are handled according to that resolved state, not treated as additional, unplanned trials.

## 7. Gotchas & takeaways

> **Gotcha:** under genuinely concurrent traffic (multiple requests arriving at nearly the same instant while the breaker is half-open), more calls than the permitted count can attempt to become trials simultaneously — real circuit breaker implementations need to handle this race condition carefully (typically via an atomic counter reserving trial "slots"), since a naive, non-atomic size check like this example's simplified version could let more than the intended number of trials through under true concurrency.

- The permitted number of calls in half-open state defines how many trial calls a circuit breaker allows through while probing recovery, evaluating their aggregate outcome rather than relying on a single call.
- A batch of trials provides a far more statistically reliable recovery signal than a single trial call, which can easily be misled by one lucky or unlucky outcome.
- Calls arriving beyond the permitted trial count while still in half-open state are rejected, just as they would be in fully open state, until the batch's outcome determines the breaker's next definitive state.
- The permitted count should be small enough to limit load on a still-recovering dependency, but large enough to give a genuinely trustworthy statistical signal — a handful of calls is the typical right order of magnitude.
- Correctly handling concurrent calls competing for a limited number of trial "slots" during half-open state is a real implementation subtlety that production circuit breaker libraries handle with atomic counters, not naive sequential checks.
