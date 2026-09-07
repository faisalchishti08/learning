---
card: system-design
gi: 136
slug: circuit-breaker
title: Circuit breaker
---

## 1. What it is

A **circuit breaker** stops a service from repeatedly calling a dependency that is clearly failing, instead of letting every single request try, wait for a [timeout](0134-timeouts.md), and fail again. It works like an electrical circuit breaker: once too many failures happen (too much "current"), the circuit "trips" and further calls fail instantly, without even attempting the doomed real call, until the dependency has had a chance to recover.

## 2. Why & when

Without a circuit breaker, a failing dependency causes every single caller to still wait out its full timeout before failing — even though the outcome is essentially certain to be another failure, given the dependency's current state. This wastes time and resources on calls that are very unlikely to succeed, and keeps adding load to a dependency that is already struggling, potentially delaying its recovery. A circuit breaker recognizes the pattern of repeated failure and short-circuits future calls, failing them immediately (or routing them to a [fallback](0138-fallbacks-graceful-degradation.md)) instead. Use a circuit breaker around any call to an external dependency that could become unavailable or slow — a downstream service, an external API, a database — especially where that dependency's failure should not also degrade the calling service's own responsiveness.

## 3. Core concept

- **Closed state:** normal operation — calls go through to the real dependency, and the breaker counts recent successes and failures.
- **Open state:** triggered once failures exceed a threshold (e.g. 50% of the last 20 calls failed); calls fail immediately without even attempting the real dependency, for a configured cooldown period.
- **Half-open state:** after the cooldown, the breaker allows a small number of test calls through; if they succeed, the breaker closes again (resume normal operation); if they fail, it reopens (stay protected, wait longer).
- **Failure threshold and window:** the breaker typically tracks failures over a rolling window (the last N calls, or the last N seconds), not just a single failure, to avoid tripping on one isolated blip.
- **Fail fast, not fail hung:** the entire point of the open state is that a caller gets an immediate, definite failure instead of waiting out a timeout for a call almost certain to fail anyway — this preserves the calling service's own responsiveness even while a dependency is down.

## 4. Diagram

```
                    CLOSED (normal)
                    calls go through,
                    track success/failure
                          |
              failure rate exceeds threshold
                          v
                    OPEN
                    calls FAIL IMMEDIATELY,
                    no real call attempted
                          |
                   cooldown period elapses
                          v
                    HALF-OPEN
                    allow a few test calls through
                     /                    \
              test calls succeed    test calls fail
                    |                      |
                    v                      v
                 CLOSED                  OPEN (retry cooldown again)
```
*Caption: the breaker moves between closed (normal), open (failing fast), and half-open (cautiously testing recovery) based on observed call outcomes.*

## 5. Runnable example

**Level 1 — Basic.** Track recent call outcomes and trip the breaker open once a failure threshold is exceeded.

**Level 2 — Fail fast while open.** Calls made while open return immediately without attempting the real dependency.

**Level 3 — Half-open recovery.** After a cooldown, allow a test call through; close the breaker if it succeeds.

```java
// CircuitBreakerDemo.java
import java.util.*;

public class CircuitBreakerDemo {

    enum State { CLOSED, OPEN, HALF_OPEN }

    static State state = State.CLOSED;
    static Deque<Boolean> recentResults = new ArrayDeque<>(); // true = success, false = failure
    static int windowSize = 5;
    static double failureThreshold = 0.5; // trip if 50%+ of the recent window failed
    static long openedAtTick = -1;
    static long cooldownTicks = 3;

    static void recordResult(boolean success) {
        recentResults.addLast(success);
        if (recentResults.size() > windowSize) recentResults.removeFirst();
    }

    static double currentFailureRate() {
        if (recentResults.isEmpty()) return 0;
        long failures = recentResults.stream().filter(r -> !r).count();
        return (double) failures / recentResults.size();
    }

    // The real (simulated) call to the dependency.
    static boolean callDependency(boolean dependencyIsHealthy) {
        return dependencyIsHealthy;
    }

    static String guardedCall(long tick, boolean dependencyIsHealthy) {
        if (state == State.OPEN) {
            if (tick - openedAtTick >= cooldownTicks) {
                state = State.HALF_OPEN;
                System.out.println("tick " + tick + ": cooldown elapsed, moving to HALF_OPEN, allowing a test call");
            } else {
                return "tick " + tick + ": OPEN - failing fast, no real call attempted";
            }
        }

        boolean success = callDependency(dependencyIsHealthy);
        if (state == State.HALF_OPEN) {
            state = success ? State.CLOSED : State.OPEN;
            if (state == State.OPEN) openedAtTick = tick;
            return "tick " + tick + ": HALF_OPEN test call " + (success ? "SUCCEEDED -> CLOSED" : "FAILED -> back to OPEN");
        }

        recordResult(success);
        if (state == State.CLOSED && currentFailureRate() >= failureThreshold && recentResults.size() >= windowSize) {
            state = State.OPEN;
            openedAtTick = tick;
            return "tick " + tick + ": call " + (success ? "succeeded" : "FAILED") + " -> failure rate tripped breaker to OPEN";
        }
        return "tick " + tick + ": call " + (success ? "succeeded" : "failed") + " (CLOSED, failure rate=" + currentFailureRate() + ")";
    }

    public static void main(String[] args) {
        // Level 1 & 2: dependency starts failing; breaker trips open and fails fast.
        boolean[] dependencyHealthPerTick = {true, false, false, false, false, false, false, true, true};
        for (int tick = 0; tick < dependencyHealthPerTick.length; tick++) {
            System.out.println(guardedCall(tick, dependencyHealthPerTick[tick]));
        }
    }
}
```

**How to run:** save as `CircuitBreakerDemo.java`, then run `java CircuitBreakerDemo.java`.

## 6. Walkthrough

1. `guardedCall` first checks the breaker's `state`; while `CLOSED`, it calls `callDependency`, records the outcome via `recordResult`, and checks whether the recent window's `currentFailureRate` has reached `failureThreshold`.
2. Early ticks with `dependencyHealthPerTick` mostly `false` accumulate failures in `recentResults`; once the window fills with mostly failures, `currentFailureRate() >= failureThreshold` becomes true, and the breaker trips to `OPEN`, recording `openedAtTick`.
3. The next several ticks hit the `state == State.OPEN` branch at the top of `guardedCall`, and since `tick - openedAtTick < cooldownTicks`, they return immediately with "failing fast, no real call attempted" — `callDependency` is never even invoked for these calls, exactly the point of the open state.
4. Once enough ticks pass (`tick - openedAtTick >= cooldownTicks`), the state moves to `HALF_OPEN` and the *next* call is allowed to actually reach `callDependency` as a test.
5. Since `dependencyHealthPerTick` has recovered to `true` by then, the test call succeeds, and the code sets `state = State.CLOSED` — the printed line confirms the breaker closing again and resuming normal operation, having protected the caller from repeatedly hitting a dependency that was still down during the cooldown window.

## 7. Gotchas & takeaways

> Gotcha: a circuit breaker configured with too small a failure window (or too low a threshold) can trip open due to a handful of unrelated, coincidental failures, unnecessarily cutting off a dependency that is actually mostly healthy — tune the window size and threshold against the dependency's real observed failure patterns, not an arbitrary guess.

- A circuit breaker stops calling a clearly-failing dependency, failing fast instead of letting every caller wait out a timeout for an almost-certain failure.
- The closed, open, and half-open states let the breaker automatically detect both failure and recovery, without needing a human to flip it back on.
- Choosing the failure threshold, window size, and cooldown period correctly is what determines whether the breaker protects the system well or trips too eagerly on normal, transient noise.
- Related concepts: [Timeouts](0134-timeouts.md) (what a circuit breaker avoids repeatedly waiting out), [Retries with exponential backoff & jitter](0135-retries-with-exponential-backoff-jitter.md) (a complementary, often combined mechanism), [Fallbacks & graceful degradation](0138-fallbacks-graceful-degradation.md) (what an open circuit typically routes to instead of failing outright).
