---
card: spring-cloud
gi: 71
slug: circuit-breaker-states-closed-open-half-open
title: "Circuit breaker states (closed/open/half-open)"
---

## 1. What it is

Earlier cards used CLOSED/OPEN/HALF_OPEN informally; this card examines Resilience4j's actual state machine in full, including the two states earlier examples simplified away: `DISABLED` (circuit breaking turned off entirely — always calls through), and `FORCED_OPEN` (manually forced open, always uses the fallback, ignoring real failure rates) — both useful operational controls beyond the automatic three-state cycle.

```java
CircuitBreaker cb = circuitBreakerRegistry.circuitBreaker("billing-service");

cb.transitionToOpenState();       // manually force OPEN
cb.transitionToClosedState();     // manually force back to CLOSED
cb.transitionToDisabledState();   // turn off circuit breaking entirely for this instance
cb.transitionToForcedOpenState(); // permanently OPEN until manually transitioned elsewhere
```

## 2. Why & when

The automatic CLOSED → OPEN → HALF_OPEN → CLOSED cycle (covered across earlier cards) handles ordinary failure detection and recovery, but operations sometimes needs to intervene directly — deliberately disabling circuit breaking during a controlled load test (where you *want* to see real failures, not fallback masking), or forcibly opening a circuit ahead of a known, scheduled maintenance window on a downstream dependency, before any real failures have even occurred.

Understanding the full state set matters when:

- Running a load test or chaos experiment where circuit breaking would interfere with observing real failure behavior — `transitionToDisabledState()` removes the circuit breaker from the equation entirely, temporarily.
- A downstream service has scheduled maintenance and you want to proactively protect callers *before* it goes down (rather than waiting for real failures to accumulate and trip the breaker naturally) — `transitionToForcedOpenState()` does this deliberately, ahead of time.
- Debugging a circuit breaker that seems "stuck" — knowing all five states (not just the automatic three) helps correctly diagnose whether it's genuinely cycling through OPEN/HALF_OPEN, or has been manually forced into a state that needs manual reversal.

## 3. Core concept

```
 Automatic cycle:
   CLOSED --(failure rate exceeds threshold)--> OPEN
   OPEN --(wait-duration-in-open-state elapses)--> HALF_OPEN
   HALF_OPEN --(trial calls succeed enough)--> CLOSED
   HALF_OPEN --(trial calls still failing)--> OPEN

 Manual-only states:
   DISABLED     -- circuit breaking is off; every call goes straight through, no protection at all
   FORCED_OPEN  -- always uses the fallback; real calls are never attempted, until manually transitioned out
```

DISABLED and FORCED_OPEN sit outside the automatic cycle entirely — nothing but an explicit `transitionTo*` call moves the breaker into or out of them.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The automatic cycle moves between closed, open, and half open based on failure rate and elapsed time, while disabled and forced open sit outside that cycle and only change on an explicit manual transition">
  <rect x="30" y="30" width="130" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="55" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">CLOSED</text>

  <rect x="240" y="30" width="130" height="40" rx="8" fill="#e6494930" stroke="#e64949" stroke-width="1.5"/>
  <text x="305" y="55" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">OPEN</text>

  <rect x="450" y="30" width="130" height="40" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="515" y="55" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">HALF_OPEN</text>

  <line x1="160" y1="50" x2="238" y2="50" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a71)"/>
  <line x1="370" y1="50" x2="448" y2="50" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a71)"/>
  <line x1="450" y1="65" x2="170" y2="65" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a71)"/>
  <text x="320" y="80" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">trial succeeds -&gt; CLOSED</text>

  <rect x="120" y="140" width="150" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="4,3"/>
  <text x="195" y="165" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">DISABLED (manual only)</text>

  <rect x="370" y="140" width="180" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="4,3"/>
  <text x="460" y="165" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">FORCED_OPEN (manual only)</text>

  <defs><marker id="a71" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The top row cycles automatically; the bottom row only ever changes when an operator or a piece of code explicitly requests it.

## 5. Runnable example

The scenario: model all five states for `billing-service`'s circuit breaker. Start with just the automatic three-state cycle (already familiar from earlier cards), then add `DISABLED` for load-testing, then add `FORCED_OPEN` for proactive maintenance-window protection.

### Level 1 — Basic

The automatic three-state cycle, as a refresher baseline.

```java
public class CircuitBreakerStatesLevel1 {
    enum State { CLOSED, OPEN, HALF_OPEN }

    static class CircuitBreaker {
        State state = State.CLOSED;

        void recordFailure() {
            if (state == State.CLOSED) { state = State.OPEN; System.out.println("-> OPEN"); }
            else if (state == State.HALF_OPEN) { state = State.OPEN; System.out.println("-> OPEN (trial failed)"); }
        }

        void recordSuccess() {
            if (state == State.HALF_OPEN) { state = State.CLOSED; System.out.println("-> CLOSED (trial succeeded)"); }
        }

        void cooldownElapsed() {
            if (state == State.OPEN) { state = State.HALF_OPEN; System.out.println("-> HALF_OPEN"); }
        }
    }

    public static void main(String[] args) {
        CircuitBreaker cb = new CircuitBreaker();
        cb.recordFailure();     // CLOSED -> OPEN
        cb.cooldownElapsed();   // OPEN -> HALF_OPEN
        cb.recordSuccess();     // HALF_OPEN -> CLOSED
        System.out.println("final state: " + cb.state);
    }
}
```

How to run: `java CircuitBreakerStatesLevel1.java`

This is the familiar automatic cycle from earlier cards — three states, all transitions driven by observed call outcomes and elapsed time, nothing manual involved.

### Level 2 — Intermediate

Add `DISABLED`: a manual state where the circuit breaker steps aside entirely, letting every call through regardless of failure rate — useful for load testing.

```java
public class CircuitBreakerStatesLevel2 {
    enum State { CLOSED, OPEN, HALF_OPEN, DISABLED }

    static class CircuitBreaker {
        State state = State.CLOSED;

        void recordFailure() {
            if (state == State.DISABLED) { System.out.println("(disabled -- failure ignored for breaker purposes)"); return; }
            if (state == State.CLOSED) { state = State.OPEN; System.out.println("-> OPEN"); }
        }

        boolean callAllowed() {
            return state != State.OPEN; // DISABLED, CLOSED, HALF_OPEN all permit calls; only OPEN blocks them
        }

        void transitionToDisabled() { state = State.DISABLED; System.out.println("-> DISABLED (manual)"); }
        void transitionToClosed() { state = State.CLOSED; System.out.println("-> CLOSED (manual)"); }
    }

    public static void main(String[] args) {
        CircuitBreaker cb = new CircuitBreaker();

        // simulate a load test: force DISABLED so real failures don't trip the breaker and mask results
        cb.transitionToDisabled();
        for (int i = 0; i < 5; i++) {
            cb.recordFailure(); // would normally trip OPEN after enough failures -- but DISABLED ignores them
        }
        System.out.println("after 5 failures while DISABLED, state is still: " + cb.state);
        System.out.println("callAllowed: " + cb.callAllowed()); // true -- every call still goes through

        cb.transitionToClosed(); // load test finished, restore normal automatic behavior
    }
}
```

How to run: `java CircuitBreakerStatesLevel2.java`

While `DISABLED`, `recordFailure` explicitly ignores every failure for state-machine purposes — five consecutive failures, which would normally trip a real breaker `OPEN`, leave the state completely unchanged. `callAllowed()` returns `true` throughout, meaning every call — including the real backend calls a load test needs to actually exercise — genuinely goes through, with the circuit breaker's usual protective behavior entirely suspended.

### Level 3 — Advanced

Add `FORCED_OPEN`: proactively protect callers ahead of a scheduled maintenance window, before any real failures occur, and confirm it behaves differently from the automatically-triggered `OPEN` state (it never auto-transitions to `HALF_OPEN`, since there's no cooldown involved — only a manual transition moves it out).

```java
public class CircuitBreakerStatesLevel3 {
    enum State { CLOSED, OPEN, HALF_OPEN, DISABLED, FORCED_OPEN }

    static class CircuitBreaker {
        State state = State.CLOSED;

        boolean callAllowed() {
            return state == State.CLOSED || state == State.HALF_OPEN || state == State.DISABLED;
        }

        void cooldownElapsed() {
            if (state == State.OPEN) { state = State.HALF_OPEN; System.out.println("-> HALF_OPEN (automatic)"); }
            // NOTE: FORCED_OPEN does NOT respond to cooldownElapsed() at all -- only a manual transition moves it
        }

        void transitionToForcedOpen() { state = State.FORCED_OPEN; System.out.println("-> FORCED_OPEN (manual)"); }
        void transitionToClosed() { state = State.CLOSED; System.out.println("-> CLOSED (manual)"); }
    }

    public static void main(String[] args) {
        CircuitBreaker cb = new CircuitBreaker();

        // billing-service has a scheduled maintenance window starting soon -- protect callers proactively
        cb.transitionToForcedOpen();
        System.out.println("callAllowed during maintenance: " + cb.callAllowed()); // false -- fallback used for every call

        // unlike automatic OPEN, waiting doesn't help -- FORCED_OPEN ignores cooldown entirely
        cb.cooldownElapsed();
        System.out.println("state after cooldown elapsed (still forced): " + cb.state);

        // maintenance window ends -- an operator (or a scheduled job) explicitly restores normal operation
        cb.transitionToClosed();
        System.out.println("callAllowed after maintenance ends: " + cb.callAllowed()); // true again
    }
}
```

How to run: `java CircuitBreakerStatesLevel3.java`

`transitionToForcedOpen()` puts the breaker into `FORCED_OPEN` proactively, before the maintenance window even begins and before any real failures occur — `callAllowed()` immediately returns `false`, meaning every caller gets the fallback from this point on. Critically, `cooldownElapsed()` — which would normally move a real, automatically-triggered `OPEN` breaker into `HALF_OPEN` — has no effect at all on `FORCED_OPEN`, since it's designed to require an explicit manual transition to leave; only the final `transitionToClosed()` call, presumably issued once the maintenance window is confirmed complete, restores normal call flow.

## 6. Walkthrough

Trace the sequence in Level 3.

1. `cb.transitionToForcedOpen()` runs first — this models an operator (or an automated maintenance-window scheduler) proactively calling `circuitBreaker.transitionToForcedOpenState()` ahead of a known downstream outage, rather than waiting for real failures to accumulate and trip the breaker the normal way. `state` becomes `FORCED_OPEN`.
2. `cb.callAllowed()` is checked — the method's condition (`CLOSED || HALF_OPEN || DISABLED`) doesn't include `FORCED_OPEN`, so it returns `false`. Every caller from this point on receives the fallback response immediately, with real calls never attempted, exactly the intended protective effect during the maintenance window.
3. `cb.cooldownElapsed()` runs — its logic only checks `if (state == State.OPEN)`, and `state` is `FORCED_OPEN`, not `OPEN`, so this check fails and nothing happens. This is the crucial distinguishing behavior from ordinary `OPEN`: waiting out any amount of time never automatically recovers a `FORCED_OPEN` breaker.
4. The `println` after `cooldownElapsed()` confirms `state` is still `FORCED_OPEN`, unchanged by the elapsed-time check that would have moved a genuinely automatic `OPEN` breaker into `HALF_OPEN`.
5. `cb.transitionToClosed()` runs last — this models the maintenance window ending and an operator or scheduled job explicitly restoring the breaker to normal, automatic operation. `callAllowed()` now returns `true` again, and from this point forward the breaker resumes its ordinary CLOSED-based failure tracking.

```
transitionToForcedOpen() -> FORCED_OPEN
callAllowed() -> false (every call gets the fallback)

cooldownElapsed() -> NO EFFECT (FORCED_OPEN only responds to explicit manual transitions, never to elapsed time)
state remains FORCED_OPEN

transitionToClosed() -> CLOSED (manual, e.g. once maintenance is confirmed over)
callAllowed() -> true again
```

## 7. Gotchas & takeaways

> **Gotcha:** a `FORCED_OPEN` breaker that's never explicitly transitioned back out stays that way indefinitely — since it doesn't respond to elapsed time at all, forgetting to call `transitionToClosedState()` (or an equivalent) after a maintenance window ends leaves callers permanently receiving fallback responses, potentially long after the actual downstream service has recovered. Any code path that programmatically forces a breaker open should have a clearly corresponding, reliably-triggered path to un-force it.

- The automatic three-state cycle (CLOSED/OPEN/HALF_OPEN) handles ordinary failure detection and recovery without any manual intervention; `DISABLED` and `FORCED_OPEN` exist specifically for deliberate operational control outside that automatic behavior.
- `DISABLED` is the right tool for temporarily removing circuit breaking's interference during load tests or chaos experiments where observing genuine failure behavior matters more than protection.
- `FORCED_OPEN` is the right tool for proactive protection ahead of a *known* future outage (scheduled maintenance) — protecting callers before failures even start, rather than reactively after enough of them have already occurred.
- Both manual states require an explicit transition to enter and an explicit transition to leave — neither responds to the automatic failure-rate or cooldown-timer logic that governs the CLOSED/OPEN/HALF_OPEN cycle, which is exactly what makes them suitable for deliberate, operator-controlled scenarios.
