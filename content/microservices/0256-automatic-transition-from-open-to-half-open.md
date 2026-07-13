---
card: microservices
gi: 256
slug: automatic-transition-from-open-to-half-open
title: "Automatic transition from open to half-open"
---

## 1. What it is

The automatic transition from open to half-open is the mechanism by which a circuit breaker moves from rejecting-everything to testing-recovery entirely on its own, with no external trigger or human intervention required — either by checking the elapsed [wait duration](0254-wait-duration-in-open-state.md) lazily on the next call attempt, or, in some implementations, via a dedicated background timer/scheduler that flips the state proactively even without any incoming calls.

## 2. Why & when

A circuit breaker requiring a human to notice it's tripped and manually flip it back would defeat much of the pattern's value — the whole point is to protect a system reliably, at any time of day, without depending on someone watching a dashboard and taking action. Automating the open-to-half-open transition means recovery detection happens reliably and promptly regardless of whether anyone is actively monitoring, which matters enormously for incidents that resolve outside business hours or before an on-call engineer has even been paged. The two common implementation approaches — lazy (check on next call) versus eager (a background timer) — have a meaningful practical difference: a lazily-checked breaker on a genuinely idle dependency (no calls arriving at all) won't transition until a call actually arrives to trigger the check, while an eager, timer-based breaker transitions on schedule regardless of whether any calls are currently arriving.

Understand which style a given circuit breaker library implements when reasoning about exactly when recovery testing will actually begin — for a low-traffic dependency, the difference between lazy and eager transition can matter for how promptly recovery gets detected after the wait duration technically elapses.

## 3. Core concept

Lazy transition defers the state check to the next call attempt — the breaker doesn't do anything on its own between calls, it simply evaluates "has the wait duration elapsed?" whenever the next call happens to arrive; eager transition uses a separate scheduled task that proactively flips the state at the exact moment the wait duration elapses, independent of whether any call is currently in flight.

```java
// LAZY transition -- the state is only checked/updated WHEN a call actually arrives
String makeCall() {
    if (state == State.OPEN && (now() - openedAt) >= waitDuration) {
        state = State.HALF_OPEN; // transition happens HERE, only because a call triggered this check
    }
    // ... proceed based on (possibly just-updated) state
}

// EAGER transition -- a SEPARATE scheduled task flips the state on its OWN timeline
scheduler.schedule(() -> {
    if (state == State.OPEN) state = State.HALF_OPEN; // transitions REGARDLESS of whether any call has arrived
}, waitDuration);
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Lazy transition checks the elapsed wait duration only when the next call arrives, so on an idle dependency the transition is delayed until that call happens; eager transition uses a background scheduled task that flips the state proactively at exactly the wait duration mark, regardless of call activity" >
  <rect x="20" y="20" width="270" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="155" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Lazy: checked on next call</text>
  <text x="155" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">idle dependency = delayed transition</text>
  <text x="155" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">simple, no background thread</text>

  <rect x="350" y="20" width="270" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Eager: background timer</text>
  <text x="485" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">transitions ON SCHEDULE regardless</text>
  <text x="485" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">requires a scheduled task</text>
</svg>

Both eliminate the need for manual intervention, but differ in exactly when the transition actually happens relative to real call traffic.

## 5. Runnable example

Scenario: a breaker implemented with lazy transition, showing that an idle dependency (no calls arriving) delays the state transition beyond the wait duration, refactored to add eager, timer-based transition that flips state precisely on schedule regardless of call activity, and finally demonstrating both approaches side by side against the identical idle period, showing the concrete difference in when each one's state actually changes.

### Level 1 — Basic

```java
// File: LazyTransition.java -- the state ONLY updates when a call
// ACTUALLY arrives -- an idle dependency (no calls) means the transition
// is DELAYED, even though the wait duration has technically elapsed.
public class LazyTransition {
    enum State { OPEN, HALF_OPEN }
    static State state = State.OPEN;
    static long openedAt = 0;
    static final long WAIT_DURATION_MILLIS = 500;

    static State checkStateOnCall(long now) { // the check ONLY runs as part of handling an actual call
        if (state == State.OPEN && (now - openedAt) >= WAIT_DURATION_MILLIS) {
            state = State.HALF_OPEN;
        }
        return state;
    }

    public static void main(String[] args) {
        System.out.println("Wait duration elapses at t=500. Dependency is IDLE (no calls) until t=2000.");
        System.out.println("State at t=2000 (first call FINALLY arrives): " + checkStateOnCall(2000));
        System.out.println("The transition was DELAYED 1500ms past when it technically should have happened,");
        System.out.println("purely because NO call arrived to trigger the check until t=2000.");
    }
}
```

**How to run:** `javac LazyTransition.java && java LazyTransition` (JDK 17+).

Expected output:
```
Wait duration elapses at t=500. Dependency is IDLE (no calls) until t=2000.
State at t=2000 (first call FINALLY arrives): HALF_OPEN
The transition was DELAYED 1500ms past when it technically should have happened,
purely because NO call arrived to trigger the check until t=2000.
```

### Level 2 — Intermediate

```java
// File: EagerTransition.java -- a SCHEDULED task flips the state
// PROACTIVELY at EXACTLY the wait duration mark -- REGARDLESS of
// whether any call has arrived.
import java.util.concurrent.*;

public class EagerTransition {
    enum State { OPEN, HALF_OPEN }
    static volatile State state = State.OPEN;
    static final long WAIT_DURATION_MILLIS = 500;

    public static void main(String[] args) throws InterruptedException {
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();

        long start = System.currentTimeMillis();
        scheduler.schedule(() -> {
            state = State.HALF_OPEN; // fires on SCHEDULE, with NO call needed to trigger it
            System.out.println("  [scheduler] transitioned to HALF_OPEN at t=" + (System.currentTimeMillis() - start) + "ms, purely on schedule");
        }, WAIT_DURATION_MILLIS, TimeUnit.MILLISECONDS);

        Thread.sleep(700); // simulate an IDLE period -- NO calls at all, just waiting
        System.out.println("State after 700ms of COMPLETE idleness (no calls ever made): " + state);

        scheduler.shutdown();
    }
}
```

**How to run:** `javac EagerTransition.java && java EagerTransition` (JDK 17+).

Expected output (timing approximate):
```
  [scheduler] transitioned to HALF_OPEN at t=50Xms, purely on schedule
State after 700ms of COMPLETE idleness (no calls ever made): HALF_OPEN
```

### Level 3 — Advanced

```java
// File: SideBySideDuringIdlePeriod.java -- runs BOTH approaches against
// the IDENTICAL idle scenario (no calls arriving until t=2000), showing
// the CONCRETE difference in when each one's state ACTUALLY updates.
import java.util.concurrent.*;

public class SideBySideDuringIdlePeriod {
    enum State { OPEN, HALF_OPEN }

    // LAZY breaker
    static State lazyState = State.OPEN;
    static long lazyOpenedAt = 0;
    static final long WAIT_DURATION_MILLIS = 500;
    static State checkLazyStateOnCall(long now) {
        if (lazyState == State.OPEN && (now - lazyOpenedAt) >= WAIT_DURATION_MILLIS) lazyState = State.HALF_OPEN;
        return lazyState;
    }

    // EAGER breaker
    static volatile State eagerState = State.OPEN;

    public static void main(String[] args) throws InterruptedException {
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        scheduler.schedule(() -> eagerState = State.HALF_OPEN, WAIT_DURATION_MILLIS, TimeUnit.MILLISECONDS);

        // check BOTH states at t=300ms (BEFORE wait duration elapses) -- via a "call" for lazy, direct read for eager
        Thread.sleep(300);
        System.out.println("At t=300ms (before wait elapses): lazy=" + checkLazyStateOnCall(300) + ", eager=" + eagerState);

        // check BOTH states at t=700ms -- but ONLY via a background read for lazy (simulating NO call has arrived yet)
        Thread.sleep(400); // now at t=700ms total
        System.out.println("At t=700ms, NO call has arrived yet: lazy=" + lazyState + " (STILL OPEN -- no call triggered the check!), eager=" + eagerState + " (transitioned ON SCHEDULE)");

        // FINALLY, a call arrives for the lazy breaker
        System.out.println("A call FINALLY arrives for lazy breaker: " + checkLazyStateOnCall(700));

        scheduler.shutdown();
    }
}
```

**How to run:** `javac SideBySideDuringIdlePeriod.java && java SideBySideDuringIdlePeriod` (JDK 17+).

Expected output (timing approximate):
```
At t=300ms (before wait elapses): lazy=OPEN, eager=OPEN
At t=700ms, NO call has arrived yet: lazy=OPEN (STILL OPEN -- no call triggered the check!), eager=HALF_OPEN (transitioned ON SCHEDULE)
A call FINALLY arrives for lazy breaker: HALF_OPEN
```

## 6. Walkthrough

1. **Level 1, the delay mechanism** — `checkStateOnCall` only performs its `state == State.OPEN && elapsed >= WAIT_DURATION_MILLIS` check when it's actually invoked, and it's only invoked as part of handling a real call attempt; simulating a call arriving at `t=2000` (long after the 500ms wait duration technically elapsed at `t=500`) shows the transition happening at that late point, not at the theoretically correct `t=500`.
2. **Level 2, a proactive scheduled transition** — `scheduler.schedule(..., WAIT_DURATION_MILLIS, ...)` registers a task that runs on its own timeline, entirely independent of any call being made; `state` is updated by this background task directly, and `main`'s subsequent check (after `Thread.sleep(700)`, with zero calls ever made) confirms `state` is already `HALF_OPEN`, purely from the scheduled task having fired.
3. **Level 2, the key demonstrated difference from Level 1** — this transition happened with *no calls made at all* throughout the entire program's execution, which is structurally impossible for `LazyTransition`'s approach, where the state field itself never changes unless something explicitly calls `checkStateOnCall`.
4. **Level 3, both mechanisms running concurrently against the same idle timeline** — `SideBySideDuringIdlePeriod` maintains two entirely separate breaker simulations (`lazyState`/`lazyOpenedAt` for the lazy approach, `eagerState` plus a scheduled task for the eager approach), both configured with the identical 500ms wait duration, observed at the same two checkpoints (`t=300ms` and `t=700ms`).
5. **Level 3, the checkpoint before the wait elapses** — at `t=300ms`, neither breaker has transitioned yet (both correctly report `OPEN`), since the wait duration (500ms) hasn't elapsed for either — at this point in time, lazy and eager behave identically.
6. **Level 3, the checkpoint after the wait elapses, with no call yet** — at `t=700ms`, `eagerState` has already become `HALF_OPEN` (the scheduled task fired around `t=500ms`, entirely on its own), while `lazyState` is still directly read as `OPEN`, because nothing has called `checkLazyStateOnCall` since the `t=300ms` check — only once a "call" is simulated arriving (the final `checkLazyStateOnCall(700)` invocation) does the lazy breaker's state actually update to `HALF_OPEN`, retroactively catching up to what the eager breaker already reflected 200ms earlier — this side-by-side comparison makes the practical difference between the two transition styles directly observable: identical configuration, identical wait duration, but a real difference in exactly *when* the state change becomes visible, driven entirely by whether the mechanism depends on incoming call traffic or runs independently of it.

## 7. Gotchas & takeaways

> **Gotcha:** a lazy-transition breaker's "recovery testing" only begins once a call actually arrives to trigger the check — for a dependency receiving very sparse traffic, this can mean recovery detection is effectively gated behind whenever the next real request happens to occur, which might be much later than the configured wait duration alone would suggest; if prompt recovery detection matters for a low-traffic dependency specifically, verify whether the circuit breaker library in use implements eager (scheduled) or lazy (call-triggered) transition, since the practical latency to detecting recovery can differ substantially between the two.

- The automatic transition from open to half-open happens without any manual intervention, either by lazily checking elapsed wait duration on the next call, or eagerly via a background scheduled task.
- Lazy transition requires no background thread but delays the actual state change until a real call happens to arrive after the wait duration has elapsed.
- Eager transition uses a scheduled task to flip the state precisely on schedule, independent of call traffic, at the cost of requiring a background scheduler.
- For a low-traffic or genuinely idle dependency, the choice between these two styles can meaningfully affect how promptly recovery testing actually begins in practice.
- Understanding which style a specific circuit breaker library implements matters when reasoning precisely about the real-world timing of recovery detection, not just the configured wait duration value alone.
