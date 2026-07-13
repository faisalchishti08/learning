---
card: microservices
gi: 254
slug: wait-duration-in-open-state
title: "Wait duration in open state"
---

## 1. What it is

The wait duration in open state is the configured length of time a circuit breaker stays in [open state](0249-closed-open-half-open-states.md), rejecting every call immediately, before automatically transitioning to half-open to test whether the failing dependency has recovered — it's the timer that governs exactly how long the breaker waits between tripping and its first recovery attempt.

## 2. Why & when

Transitioning to half-open too quickly after tripping risks probing a dependency that's still in the middle of failing (a service restarting, a database still under heavy load) — the trial call fails again almost immediately, and the breaker just cycles back to open with no real benefit, or worse, adds one more request to a system that's actively trying to recover and doesn't need additional load right now. Waiting too long, on the other hand, means a dependency that recovered quickly continues being unnecessarily blocked from real traffic for far longer than needed, degrading the user experience more than necessary during a brief outage. The wait duration is the tunable knob balancing these two costs — long enough to give a typical outage genuine time to resolve, short enough that recovery is detected reasonably promptly once it happens.

Tune the wait duration based on how quickly a specific dependency typically recovers from the kinds of failures it experiences — a dependency that restarts in a few seconds after a crash needs a much shorter wait than one that requires manual intervention or a lengthy database failover, and setting the value too far from that dependency's actual recovery characteristics either wastes recovery time unnecessarily or probes prematurely and repeatedly.

## 3. Core concept

The breaker records the timestamp it transitioned to open, and on each subsequent call attempt, checks whether the elapsed time since that transition has reached the configured `waitDurationInOpenState` — once it has, the very next call is allowed through as a half-open trial, regardless of how many rejected calls happened during the wait.

```java
CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .waitDurationInOpenState(Duration.ofSeconds(30)) // stay OPEN for 30 seconds before the first recovery probe
    .build();

// internally, roughly:
if (state == State.OPEN && (now - openedAt) >= waitDurationInOpenState) {
    state = State.HALF_OPEN; // the WAIT has elapsed -- allow ONE trial call through
}
// EVERY call during the wait period is still rejected immediately, right up until this exact moment
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A timeline showing the breaker entering open state at time zero, rejecting all calls for the configured wait duration, and transitioning to half-open exactly when that duration elapses, allowing the first trial call through" >
  <line x1="30" y1="90" x2="610" y2="90" stroke="#8b949e"/>
  <circle cx="60" cy="90" r="5" fill="#8b949e"/>
  <text x="60" y="115" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">t=0: OPEN</text>

  <rect x="90" y="70" width="420" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="300" y="94" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">wait duration -- ALL calls rejected immediately</text>

  <circle cx="550" cy="90" r="5" fill="#6db33f"/>
  <text x="550" y="115" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">t=30s: HALF_OPEN, trial allowed</text>

  <line x1="550" y1="90" x2="550" y2="40" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr254)"/>

  <defs>
    <marker id="arr254" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Every call during the wait window is rejected identically; the transition happens at a precise, measured instant, not gradually.

## 5. Runnable example

Scenario: a breaker with a fixed wait duration that first demonstrates rejecting every call precisely until the duration elapses, then compares two different wait duration configurations against the identical failure-and-recovery scenario to show the direct trade-off between waiting too briefly (probing prematurely) and waiting appropriately, and finally simulating repeated open-state cycles to demonstrate the wait duration resetting correctly on each new trip.

### Level 1 — Basic

```java
// File: RejectsUntilWaitElapses.java -- demonstrates the WAIT DURATION
// precisely: EVERY call is rejected right up until the exact moment
// it elapses.
public class RejectsUntilWaitElapses {
    static long openedAt = 1000; // the SIMULATED time the breaker tripped
    static final long WAIT_DURATION_MILLIS = 500;

    static String attemptCall(long now) {
        if (now - openedAt < WAIT_DURATION_MILLIS) return "REJECTED (still within wait duration)";
        return "TRIAL ALLOWED (wait duration elapsed)";
    }

    public static void main(String[] args) {
        long[] attemptTimes = {1100, 1300, 1499, 1500, 1600}; // approaching, then crossing, the 500ms mark
        for (long t : attemptTimes) {
            System.out.println("t=" + t + " (elapsed=" + (t - openedAt) + "ms): " + attemptCall(t));
        }
    }
}
```

**How to run:** `javac RejectsUntilWaitElapses.java && java RejectsUntilWaitElapses` (JDK 17+).

Expected output:
```
t=1100 (elapsed=100ms): REJECTED (still within wait duration)
t=1300 (elapsed=300ms): REJECTED (still within wait duration)
t=1499 (elapsed=499ms): REJECTED (still within wait duration)
t=1500 (elapsed=500ms): TRIAL ALLOWED (wait duration elapsed)
t=1600 (elapsed=600ms): TRIAL ALLOWED (wait duration elapsed)
```

### Level 2 — Intermediate

```java
// File: ComparingWaitDurations.java -- runs the SAME recovery scenario
// (dependency recovers at t=800ms) against TWO different wait durations,
// showing the DIRECT trade-off: too short probes prematurely and fails
// again; well-tuned succeeds on the first real probe.
public class ComparingWaitDurations {
    static final long DEPENDENCY_RECOVERS_AT = 800; // the dependency GENUINELY recovers at this simulated time

    static boolean dependencyHealthyAt(long time) { return time >= DEPENDENCY_RECOVERS_AT; }

    static void simulate(long waitDurationMillis, long openedAt) {
        long firstProbeTime = openedAt + waitDurationMillis;
        boolean probeSucceeds = dependencyHealthyAt(firstProbeTime);
        System.out.println("Wait duration=" + waitDurationMillis + "ms: first probe at t=" + firstProbeTime +
            ", dependency recovers at t=" + DEPENDENCY_RECOVERS_AT + " -> probe " + (probeSucceeds ? "SUCCEEDS (recovery detected)" : "FAILS (probed too early, must wait AGAIN)"));
    }

    public static void main(String[] args) {
        long openedAt = 0;
        simulate(300, openedAt); // TOO SHORT -- probes before recovery
        simulate(1000, openedAt); // WELL-TUNED -- probes after recovery
    }
}
```

**How to run:** `javac ComparingWaitDurations.java && java ComparingWaitDurations` (JDK 17+).

Expected output:
```
Wait duration=300ms: first probe at t=300, dependency recovers at t=800 -> probe FAILS (probed too early, must wait AGAIN)
Wait duration=1000ms: first probe at t=1000, dependency recovers at t=800 -> probe SUCCEEDS (recovery detected)
```

### Level 3 — Advanced

```java
// File: WaitDurationResetsOnEachTrip.java -- simulates MULTIPLE
// open-state cycles (trip, premature failed probe, RE-trip, wait AGAIN,
// eventually successful probe) -- showing the wait timer RESETS fully
// on EACH new trip to open, not just the first.
public class WaitDurationResetsOnEachTrip {
    static final long WAIT_DURATION_MILLIS = 300;
    static final long DEPENDENCY_RECOVERS_AT = 700;

    static boolean dependencyHealthyAt(long time) { return time >= DEPENDENCY_RECOVERS_AT; }

    public static void main(String[] args) {
        long openedAt = 0; // FIRST trip, at t=0
        int cycle = 1;

        while (true) {
            long probeTime = openedAt + WAIT_DURATION_MILLIS; // the NEXT probe, timed from THIS trip's openedAt
            boolean healthy = dependencyHealthyAt(probeTime);
            System.out.println("Cycle " + cycle + ": opened at t=" + openedAt + ", probe at t=" + probeTime + " -> " + (healthy ? "SUCCESS -- CLOSED" : "FAIL -- back to OPEN"));

            if (healthy) break; // recovery confirmed -- breaker fully closes
            openedAt = probeTime; // the FAILED probe RE-OPENS the breaker -- wait timer RESETS from THIS new point
            cycle++;
        }
        System.out.println("\nEach failed probe RESET the wait timer from that probe's OWN timestamp -- not the ORIGINAL trip time.");
    }
}
```

**How to run:** `javac WaitDurationResetsOnEachTrip.java && java WaitDurationResetsOnEachTrip` (JDK 17+).

Expected output:
```
Cycle 1: opened at t=0, probe at t=300 -> FAIL -- back to OPEN
Cycle 2: opened at t=300, probe at t=600 -> FAIL -- back to OPEN
Cycle 3: opened at t=600, probe at t=900 -> SUCCESS -- CLOSED

Each failed probe RESET the wait timer from that probe's OWN timestamp -- not the ORIGINAL trip time.
```

## 6. Walkthrough

1. **Level 1, the precise boundary** — `attemptCall` compares `now - openedAt` against `WAIT_DURATION_MILLIS` (500), and the test times step right up to and across that exact boundary: at `elapsed=499ms` the call is still rejected, but at `elapsed=500ms` (the exact configured duration) it's allowed through as a trial — demonstrating the transition happens at a precise instant, not gradually or probabilistically.
2. **Level 2, a wait duration shorter than actual recovery time** — `simulate(300, 0)` computes the first probe at `t=300`, but `DEPENDENCY_RECOVERS_AT` is `800`, meaning the dependency is still genuinely unhealthy at the moment of that probe — the probe fails, and the breaker must return to open and wait again, having gained nothing from probing this early except one more failed call.
3. **Level 2, a wait duration that matches recovery reasonably well** — `simulate(1000, 0)` computes the first probe at `t=1000`, which is after the dependency's actual `t=800` recovery, so the probe succeeds on its first attempt — demonstrating the direct, measurable cost of an under-tuned wait duration (Level 2's first case, requiring a second cycle) versus a well-tuned one (succeeding immediately).
4. **Level 3, the timer resetting on each failed probe** — in the `while` loop, each time a probe fails, `openedAt` is reassigned to `probeTime` (the moment of that failed probe), meaning the *next* probe is scheduled `WAIT_DURATION_MILLIS` after *this* failure, not after the original trip — this correctly models real circuit breaker behavior, where each return to open state restarts the wait timer fresh.
5. **Level 3, three full cycles to detect actual recovery** — with a wait duration of 300ms and actual recovery at `t=700`, the first probe (at `t=300`) fails, the second probe (at `t=600`, since `openedAt` reset to `300`) also fails, but the third probe (at `t=900`, since `openedAt` reset to `600`) succeeds, because by then the actual `t=700` recovery point has passed.
6. **Level 3, why the resetting behavior matters** — if the wait timer did *not* reset on each failed probe (instead always counting from the original `t=0` trip), the timing of subsequent probes would be predictable and fixed regardless of how many times the dependency had already failed a probe, potentially probing at a fixed cadence that has no relationship to how the failure is actually evolving; resetting from each new open-state entry, as this simulation does, ensures the breaker consistently gives the dependency a full, fresh wait period after *every* failed recovery attempt, not a diminishing or misaligned one.

## 7. Gotchas & takeaways

> **Gotcha:** an excessively short wait duration combined with a dependency that fails quickly on each probe can produce a rapid, repeated open→half-open→open cycle that itself adds noticeable load and noise (repeated probe calls, repeated log entries) without ever giving the dependency meaningful recovery time — if a dependency is known to take a specific, predictable amount of time to recover from its typical failure modes, the wait duration should be set with that real recovery time in mind, not left at an arbitrary short default.

- The wait duration in open state is the configured time a circuit breaker stays fully open, rejecting every call, before allowing its first recovery-testing trial call through in half-open state.
- Too short a wait duration risks probing a dependency that hasn't actually recovered yet, wasting the probe and cycling back to open with no benefit; too long a wait unnecessarily extends the outage's impact on users beyond what's actually needed.
- The wait duration should be tuned to a specific dependency's real, typical recovery characteristics, not left at a generic default unrelated to how that dependency actually behaves.
- Each time the breaker returns to open state (after a failed half-open probe), the wait timer restarts fresh from that point, not from the original trip — ensuring every recovery attempt gets a full, consistent wait period.
- A wait duration that's poorly matched to a dependency's actual recovery time can produce a rapid, repeated trip-probe-fail cycle that adds its own overhead without meaningfully aiding recovery detection.
