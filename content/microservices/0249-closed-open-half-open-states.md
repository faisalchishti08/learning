---
card: microservices
gi: 249
slug: closed-open-half-open-states
title: "Closed / open / half-open states"
---

## 1. What it is

Closed, open, and half-open are the three states a [circuit breaker](0248-circuit-breaker-pattern.md) moves through: closed means calls flow through normally while failures are tracked; open means calls are rejected immediately without attempting the dependency at all; half-open is a probing state, entered after a wait period, that allows a limited number of test calls through to check whether the dependency has recovered, deciding whether to return to closed (recovered) or back to open (still failing).

## 2. Why & when

A circuit breaker that only ever trips (moves to open) and never re-tests the dependency would provide only half the pattern's value — protecting the caller during an outage, but then leaving every future call permanently failing via fallback even long after the dependency has genuinely recovered, since nothing would ever attempt a real call again to discover that recovery. The three-state design solves this: the half-open state provides a deliberate, controlled way to test recovery without fully reopening the floodgates — a small number of trial calls, rather than every caller's traffic, get to attempt the real dependency, so recovery can be detected safely and the breaker can transition back to normal operation automatically once it's confirmed.

Understand this state machine when configuring or reasoning about any circuit breaker's behavior — the specific transition conditions (how many consecutive successes in half-open state are needed to fully close, how long open state waits before allowing a half-open probe) are exactly the tunable parameters that determine how quickly a system recovers after a dependency comes back, and how much load a still-recovering dependency receives during that recovery.

## 3. Core concept

The breaker transitions closed → open when the tracked failure rate crosses its threshold, open → half-open automatically after a configured wait duration, and half-open → either closed (if the limited probe calls succeed) or back to open (if they fail) — each transition is triggered by a specific, measurable condition, not a manual intervention.

```java
enum BreakerState { CLOSED, OPEN, HALF_OPEN }

BreakerState state = BreakerState.CLOSED;
// CLOSED -- calls flow through; failures tracked; too many failures -> transition to OPEN
// OPEN -- calls REJECTED immediately; after waitDurationInOpenState elapses -> transition to HALF_OPEN
// HALF_OPEN -- a LIMITED number of trial calls allowed through:
//   enough SUCCEED -> transition back to CLOSED (dependency has recovered)
//   ANY fail (or fail rate still too high) -> transition back to OPEN (still broken, wait again)
```

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A circuit breaker cycles through three states: closed, where calls flow normally until a failure threshold trips it to open; open, where calls are rejected immediately until a wait duration elapses, moving to half-open; half-open, where limited trial calls determine whether the breaker returns to closed on success or back to open on failure" >
  <rect x="30" y="80" width="150" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="103" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">CLOSED</text>
  <text x="105" y="119" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">calls flow normally</text>

  <rect x="245" y="20" width="150" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="43" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">HALF_OPEN</text>
  <text x="320" y="59" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">limited trial calls</text>

  <rect x="460" y="80" width="150" height="55" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="535" y="103" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">OPEN</text>
  <text x="535" y="119" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">calls rejected immediately</text>

  <line x1="180" y1="95" x2="458" y2="95" stroke="#8b949e" marker-end="url(#arr249)"/>
  <text x="320" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">failure threshold crossed</text>

  <line x1="500" y1="80" x2="360" y2="65" stroke="#8b949e" marker-end="url(#arr249)"/>
  <text x="440" y="170" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">wait duration elapses</text>

  <line x1="245" y1="55" x2="185" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr249g)"/>
  <text x="180" y="190" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">trial calls succeed</text>

  <line x1="330" y1="75" x2="470" y2="82" stroke="#8b949e" marker-end="url(#arr249)"/>
  <text x="440" y="195" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">trial calls fail</text>

  <defs>
    <marker id="arr249" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="arr249g" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Each transition is triggered by a specific, measurable condition, cycling the breaker automatically between protection and recovery testing.

## 5. Runnable example

Scenario: a circuit breaker state machine built first with only closed and open states (protecting the caller but never recovering automatically), extended with a half-open state that tests recovery after a wait period, and finally demonstrating the full cycle across a dependency that fails, gets protected against, recovers, and is automatically detected as healthy again — all three transitions exercised in one continuous run.

### Level 1 — Basic

```java
// File: TwoStateOnly.java -- only CLOSED and OPEN; ONCE tripped, it
// NEVER re-tests the dependency -- permanently stuck rejecting calls,
// even after the dependency recovers.
public class TwoStateOnly {
    enum State { CLOSED, OPEN }
    static State state = State.CLOSED;
    static int consecutiveFailures = 0;

    static String callDependency(boolean dependencyHealthy) {
        if (!dependencyHealthy) throw new RuntimeException("dependency failed");
        return "success";
    }

    static String protectedCall(boolean dependencyHealthy) {
        if (state == State.OPEN) return "REJECTED (permanently open, no recovery mechanism)";
        try {
            String result = callDependency(dependencyHealthy);
            consecutiveFailures = 0;
            return result;
        } catch (RuntimeException e) {
            if (++consecutiveFailures >= 3) state = State.OPEN;
            return "FAILED";
        }
    }

    public static void main(String[] args) {
        for (int i = 0; i < 3; i++) System.out.println(protectedCall(false)); // dependency FAILS 3 times -- trips
        System.out.println("State: " + state);

        // the dependency has now RECOVERED -- but this breaker has NO WAY to find out
        System.out.println(protectedCall(true)); // STILL rejected, even though dependencyHealthy=true now!
    }
}
```

**How to run:** `javac TwoStateOnly.java && java TwoStateOnly` (JDK 17+).

Expected output:
```
FAILED
FAILED
FAILED
State: OPEN
REJECTED (permanently open, no recovery mechanism)
```

### Level 2 — Intermediate

```java
// File: ThreeStateWithRecovery.java -- adds HALF_OPEN: after a WAIT
// PERIOD, a LIMITED trial call is allowed through to test recovery.
public class ThreeStateWithRecovery {
    enum State { CLOSED, OPEN, HALF_OPEN }
    static State state = State.CLOSED;
    static int consecutiveFailures = 0;
    static long openedAt;
    static final long WAIT_DURATION_MILLIS = 100;

    static String callDependency(boolean dependencyHealthy) {
        if (!dependencyHealthy) throw new RuntimeException("dependency failed");
        return "success";
    }

    static String protectedCall(boolean dependencyHealthy, long now) {
        if (state == State.OPEN && now - openedAt >= WAIT_DURATION_MILLIS) {
            state = State.HALF_OPEN; // TRANSITION: wait period elapsed -- allow a TRIAL call
            System.out.println("  [breaker] OPEN -> HALF_OPEN (wait period elapsed, testing recovery)");
        }
        if (state == State.OPEN) return "REJECTED (still open, waiting)";

        try {
            String result = callDependency(dependencyHealthy);
            if (state == State.HALF_OPEN) {
                state = State.CLOSED; consecutiveFailures = 0; // TRIAL succeeded -- FULLY recovered
                System.out.println("  [breaker] HALF_OPEN -> CLOSED (trial call succeeded)");
            }
            return result;
        } catch (RuntimeException e) {
            if (state == State.HALF_OPEN) {
                state = State.OPEN; openedAt = now; // TRIAL failed -- back to OPEN, wait again
                System.out.println("  [breaker] HALF_OPEN -> OPEN (trial call still failing)");
            } else if (++consecutiveFailures >= 3) {
                state = State.OPEN; openedAt = now;
                System.out.println("  [breaker] CLOSED -> OPEN (failure threshold reached)");
            }
            return "FAILED";
        }
    }

    public static void main(String[] args) throws InterruptedException {
        for (int i = 0; i < 3; i++) protectedCall(false, System.currentTimeMillis()); // trip it
        System.out.println("State after 3 failures: " + state);

        Thread.sleep(150); // let the wait duration pass

        String result = protectedCall(true, System.currentTimeMillis()); // dependency has RECOVERED -- trial call attempted
        System.out.println("Trial call result: " + result + ", final state: " + state);
    }
}
```

**How to run:** `javac ThreeStateWithRecovery.java && java ThreeStateWithRecovery` (JDK 17+).

Expected output:
```
State after 3 failures: OPEN
  [breaker] OPEN -> HALF_OPEN (wait period elapsed, testing recovery)
  [breaker] HALF_OPEN -> CLOSED (trial call succeeded)
Trial call result: success, final state: CLOSED
```

### Level 3 — Advanced

```java
// File: FullCycleWithFlappingRecovery.java -- exercises the FULL cycle,
// including a HALF_OPEN trial that FAILS first (dependency still
// unstable) before EVENTUALLY succeeding -- realistic "flapping" recovery.
public class FullCycleWithFlappingRecovery {
    enum State { CLOSED, OPEN, HALF_OPEN }
    static State state = State.CLOSED;
    static int consecutiveFailures = 0;
    static long openedAt;
    static final long WAIT_DURATION_MILLIS = 50;

    static String callDependency(boolean healthy) {
        if (!healthy) throw new RuntimeException("dependency failed");
        return "success";
    }

    static String protectedCall(boolean healthy, long now) {
        if (state == State.OPEN && now - openedAt >= WAIT_DURATION_MILLIS) {
            state = State.HALF_OPEN;
            System.out.println("  [t+" + now + "] OPEN -> HALF_OPEN");
        }
        if (state == State.OPEN) return "REJECTED";

        try {
            String result = callDependency(healthy);
            if (state == State.HALF_OPEN) { state = State.CLOSED; consecutiveFailures = 0; System.out.println("  HALF_OPEN -> CLOSED (recovered)"); }
            return result;
        } catch (RuntimeException e) {
            if (state == State.HALF_OPEN) { state = State.OPEN; openedAt = now; System.out.println("  HALF_OPEN -> OPEN (still unstable)"); }
            else if (++consecutiveFailures >= 3) { state = State.OPEN; openedAt = now; System.out.println("  CLOSED -> OPEN (threshold reached)"); }
            return "FAILED";
        }
    }

    public static void main(String[] args) throws InterruptedException {
        long t = System.currentTimeMillis();
        for (int i = 0; i < 3; i++) protectedCall(false, t); // trip the breaker
        System.out.println("State: " + state + "\n");

        Thread.sleep(70); // pass the wait duration
        protectedCall(false, System.currentTimeMillis()); // FIRST recovery attempt -- dependency STILL flaky, trial FAILS
        System.out.println("State: " + state + "\n");

        Thread.sleep(70); // wait again, per the (re-)opened state
        String finalResult = protectedCall(true, System.currentTimeMillis()); // SECOND recovery attempt -- dependency NOW genuinely healthy
        System.out.println("Final trial result: " + finalResult + ", state: " + state);
    }
}
```

**How to run:** `javac FullCycleWithFlappingRecovery.java && java FullCycleWithFlappingRecovery` (JDK 17+).

Expected output (timestamps vary, sequence is stable):
```
  CLOSED -> OPEN (threshold reached)
State: OPEN

  [t+...] OPEN -> HALF_OPEN
  HALF_OPEN -> OPEN (still unstable)
State: OPEN

  [t+...] OPEN -> HALF_OPEN
  HALF_OPEN -> CLOSED (recovered)
Final trial result: success, state: CLOSED
```

## 6. Walkthrough

1. **Level 1, the missing recovery path** — `TwoStateOnly` has only `CLOSED` and `OPEN`; once three failures push `state` to `OPEN`, nothing in `protectedCall` ever checks the dependency again, so even calling it with `dependencyHealthy = true` (simulating full recovery) is rejected identically to when the dependency was actually still down — the breaker has no way to ever discover recovery on its own.
2. **Level 2, the wait-triggered probe** — `ThreeStateWithRecovery` checks, at the top of every call while `state == OPEN`, whether `WAIT_DURATION_MILLIS` has elapsed since `openedAt`; once it has, `state` transitions to `HALF_OPEN` *before* deciding whether to actually attempt the call, allowing exactly one trial call through.
3. **Level 2, the successful recovery path** — because `dependencyHealthy` is `true` on the trial call in `main`, `callDependency` succeeds, and the `if (state == State.HALF_OPEN)` check inside the success branch transitions `state` back to `CLOSED`, resetting `consecutiveFailures` — the breaker has now fully recovered, having discovered this automatically rather than requiring any manual intervention.
4. **Level 3, a trial call that itself fails** — `FullCycleWithFlappingRecovery` calls `protectedCall(false, ...)` for its *first* post-wait attempt, meaning the dependency is still unhealthy at that point; the `catch` block's `if (state == State.HALF_OPEN)` branch fires instead of the success branch, transitioning `state` back to `OPEN` and resetting `openedAt` to the current time — modeling a realistic "flapping" dependency that appears to have recovered timing-wise but is still actually broken.
5. **Level 3, the second wait cycle** — because the breaker went back to `OPEN` (not straight to `CLOSED`), it must wait out `WAIT_DURATION_MILLIS` *again* before offering another trial call; `main`'s second `Thread.sleep(70)` and subsequent call models exactly this second wait-and-retry cycle.
6. **Level 3, eventual genuine recovery detected** — the second trial call passes `healthy = true`, and this time `callDependency` succeeds, transitioning `state` to `CLOSED` for good; the full sequence — trip, failed recovery attempt, successful recovery attempt — demonstrates that the half-open state's design correctly handles not just a clean, one-shot recovery (as in Level 2) but also a more realistic, imperfect recovery where the dependency needs more than one probe before it's genuinely stable again, without ever needing a human to intervene at any point in the cycle.

## 7. Gotchas & takeaways

> **Gotcha:** in half-open state, only a small, limited number of calls should be allowed through as trials — allowing unlimited traffic through the moment the breaker enters half-open would defeat its purpose, potentially overwhelming a dependency that's only barely starting to recover; real circuit breaker implementations (like Resilience4j) configure a specific `permittedNumberOfCallsInHalfOpenState`, and this example's single-trial-call simplification stands in for that same, deliberately limited probing behavior.

- Closed, open, and half-open are the three states a circuit breaker cycles through: normal operation, tripped rejection, and controlled recovery testing.
- The open-to-half-open transition happens automatically after a configured wait duration, giving the breaker a way to periodically re-check whether a failing dependency has recovered.
- Half-open allows only a limited number of trial calls through — success transitions back to closed (fully recovered), while failure transitions back to open (still broken, wait again).
- A real dependency's recovery isn't always clean on the first try; the cycle can repeat through open and half-open multiple times before genuinely stabilizing, and the state machine handles this correctly without manual intervention.
- Without the half-open state, a tripped circuit breaker would stay permanently rejecting calls even long after the underlying dependency has fully recovered — half-open is what makes the pattern self-healing rather than a one-way trip.
