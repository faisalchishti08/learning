---
card: java
gi: 323
slug: thread-states-lifecycle
title: Thread states & lifecycle
---

## 1. What it is

Every `Thread` moves through a well-defined set of states over its lifetime, reported by `getState()` as a value of the `Thread.State` enum: `NEW` (created but not started), `RUNNABLE` (eligible to run, whether actually running or waiting for CPU time), `BLOCKED` (waiting to acquire a lock), `WAITING`/`TIMED_WAITING` (waiting for another thread's action, with or without a timeout), and `TERMINATED` (finished executing).

```java
public class ThreadStateDemo {
    public static void main(String[] args) throws InterruptedException {
        Thread t = new Thread(() -> {
            try { Thread.sleep(200); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });

        System.out.println("Before start: " + t.getState()); // NEW
        t.start();
        System.out.println("Just after start: " + t.getState()); // RUNNABLE (or occasionally TIMED_WAITING)
        Thread.sleep(50);
        System.out.println("While sleeping: " + t.getState()); // TIMED_WAITING
        t.join();
        System.out.println("After join: " + t.getState()); // TERMINATED
    }
}
```

`getState()` reports the thread's current position in its lifecycle at the exact instant it's called — since threads can transition between states extremely quickly, the observed state can vary between runs depending on precise timing, but the overall progression (`NEW` -> `RUNNABLE` -> ... -> `TERMINATED`) is always in that general direction, never backward.

## 2. Why & when

Understanding a thread's lifecycle states is essential for reasoning about concurrent programs correctly — knowing whether a thread is actually running, blocked waiting for a lock, or waiting for a condition helps diagnose performance problems (contention, deadlock) and understand exactly what a program's threads are doing at any given moment.

- **Debugging concurrency issues** — a thread stuck in `BLOCKED` for a long time suggests lock contention; a thread stuck in `WAITING` suggests it's waiting for a `notify()`/`notifyAll()` that may never come (a potential bug); tools like thread dumps report exactly these states.
- **Understanding `join()` and `isAlive()`** — `isAlive()` returns `true` for any state except `NEW` and `TERMINATED`, clarifying exactly what "alive" means in terms of the underlying state machine.
- **Reasoning about deadlock** — two threads each `BLOCKED` waiting for a lock the other holds is the classic deadlock signature, visible directly in their states.

You rarely call `getState()` in everyday application code, but understanding the state machine underneath `Thread`'s behavior — what `start()`, `sleep()`, `wait()`, blocking on a lock, and finishing actually do to a thread's state — is foundational to correctly reasoning about any concurrent program, and essential when reading thread dumps to diagnose a stuck or slow application.

## 3. Core concept

```java
public class ThreadStateCore {
    static final Object lock = new Object();

    public static void main(String[] args) throws InterruptedException {
        Thread blocker = new Thread(() -> {
            synchronized (lock) {
                try { Thread.sleep(500); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            }
        });
        Thread waiter = new Thread(() -> {
            synchronized (lock) { /* just needs the lock briefly */ }
        });

        blocker.start();
        Thread.sleep(50); // let blocker acquire the lock first
        waiter.start();
        Thread.sleep(50); // let waiter attempt to acquire it and get stuck

        System.out.println("blocker state: " + blocker.getState()); // TIMED_WAITING (sleeping)
        System.out.println("waiter state: " + waiter.getState());   // BLOCKED (waiting for the lock)

        blocker.join();
        waiter.join();
    }
}
```

`blocker` holds `lock` while sleeping, so its own state is `TIMED_WAITING` (it's the one sleeping); `waiter`, trying to enter the same `synchronized (lock)` block that `blocker` currently holds, is stuck in `BLOCKED` — a genuinely different state, specifically meaning "waiting to acquire a lock," as opposed to "sleeping" or "waiting for a notification."

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A thread progresses from NEW through RUNNABLE possibly through BLOCKED or WAITING and finally to TERMINATED">
  <rect x="8" y="8" width="624" height="204" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="90" height="35" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="65" y="52" fill="#e6edf3" font-size="10" text-anchor="middle">NEW</text>
  <line x1="112" y1="47" x2="150" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#s1)"/>
  <text x="130" y="40" fill="#8b949e" font-size="8" text-anchor="middle">start()</text>

  <rect x="155" y="30" width="110" height="35" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="210" y="52" fill="#6db33f" font-size="10" text-anchor="middle">RUNNABLE</text>

  <line x1="210" y1="67" x2="210" y2="100" stroke="#f85149" stroke-width="2" marker-end="url(#s2)"/>
  <rect x="140" y="105" width="140" height="35" rx="5" fill="#1c2430" stroke="#f85149"/>
  <text x="210" y="127" fill="#f85149" font-size="9" text-anchor="middle">BLOCKED (lock) /</text>
  <text x="210" y="140" fill="#f85149" font-size="9" text-anchor="middle" dy="10">WAITING (wait/join)</text>

  <line x1="280" y1="122" x2="330" y2="122" stroke="#8b949e" stroke-width="2" marker-end="url(#s3)"/>
  <text x="305" y="112" fill="#8b949e" font-size="8" text-anchor="middle">resumes</text>
  <line x1="265" y1="47" x2="400" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#s4)"/>
  <text x="330" y="40" fill="#8b949e" font-size="8" text-anchor="middle">run() completes</text>

  <rect x="405" y="30" width="120" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="465" y="52" fill="#79c0ff" font-size="10" text-anchor="middle">TERMINATED</text>
  <defs>
    <marker id="s1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="s2" markerWidth="9" markerHeight="9" refX="4" refY="7" orient="auto"><path d="M0,0 L8,0 L4,7 Z" fill="#f85149"/></marker>
    <marker id="s3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="s4" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

A thread's state always moves forward through this progression; it never returns to `NEW` and never leaves `TERMINATED` once reached.

## 5. Runnable example

Scenario: monitoring a worker thread's state changes over its lifetime, evolved from a basic before/after snapshot into observing a mid-execution state, then into a small state-monitoring utility that samples and reports a thread's state transitions periodically while it runs.

### Level 1 — Basic

```java
public class ThreadStateBasic {
    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            long sum = 0;
            for (int i = 0; i < 1_000_000_000; i++) sum += i;
        });

        System.out.println("State before start(): " + worker.getState());
        worker.start();
        worker.join();
        System.out.println("State after join(): " + worker.getState());
    }
}
```

**How to run:** `java ThreadStateBasic.java`

Captures only the two endpoints of the lifecycle — `NEW` before `start()`, `TERMINATED` after `join()` returns — without observing anything in between.

### Level 2 — Intermediate

Same worker, now with the main thread sampling its state once while it's actively running, revealing the `RUNNABLE` state in the middle of its lifecycle.

```java
public class ThreadStateIntermediate {
    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            long sum = 0;
            for (int i = 0; i < 2_000_000_000; i++) sum += i; // long enough to observe mid-execution
        });

        System.out.println("Before start: " + worker.getState());
        worker.start();

        Thread.sleep(50); // give the worker a moment to actually start running
        System.out.println("Mid-execution: " + worker.getState());

        worker.join();
        System.out.println("After join: " + worker.getState());
    }
}
```

**How to run:** `java ThreadStateIntermediate.java`

The 50ms sleep in the main thread gives the worker time to transition from `NEW` to `RUNNABLE` and actually begin its long-running loop, so the mid-execution sample reliably observes `RUNNABLE` — the state indicating the thread is eligible to run (and, on a machine with a free core, actually is running) its busy-work loop.

### Level 3 — Advanced

Same worker, now with a dedicated monitoring thread that repeatedly samples and logs the worker's state at regular intervals throughout its entire lifetime, producing a timeline of its state transitions — demonstrating a practical technique for observing concurrent behavior.

```java
import java.util.ArrayList;
import java.util.List;

public class ThreadStateAdvanced {
    public static void main(String[] args) throws InterruptedException {
        final Object lock = new Object();

        Thread worker = new Thread(() -> {
            long sum = 0;
            for (int i = 0; i < 500_000_000; i++) sum += i; // phase 1: RUNNABLE

            synchronized (lock) {
                try { Thread.sleep(150); } catch (InterruptedException e) { Thread.currentThread().interrupt(); } // phase 2: TIMED_WAITING
            }
        });

        List<String> log = new ArrayList<>();
        Thread monitor = new Thread(() -> {
            Thread.State lastState = null;
            while (worker.getState() != Thread.State.TERMINATED) {
                Thread.State current = worker.getState();
                if (current != lastState) {
                    log.add("State changed to: " + current);
                    lastState = current;
                }
                try { Thread.sleep(10); } catch (InterruptedException e) { return; }
            }
            log.add("State changed to: TERMINATED");
        });

        worker.start();
        monitor.start();
        worker.join();
        monitor.join();

        log.forEach(System.out::println);
    }
}
```

**How to run:** `java ThreadStateAdvanced.java`

`monitor` polls `worker.getState()` every 10 milliseconds and records each *change* (not every poll, to avoid duplicate log entries) — since `worker`'s task deliberately has two distinct phases (a busy-work loop, then a synchronized sleep), the resulting log captures the transition from `NEW` through `RUNNABLE` (during the loop) to `TIMED_WAITING` (during the sleep) and finally to `TERMINATED`, giving a visible timeline of the thread's actual lifecycle.

## 6. Walkthrough

Trace `ThreadStateAdvanced.main` step by step.

**Startup.** `worker.start()` and `monitor.start()` are both called in quick succession. `worker` begins transitioning from `NEW` toward `RUNNABLE` as the JVM schedules it; `monitor` begins its polling loop almost immediately.

**Monitor's first checks.** `monitor` calls `worker.getState()` repeatedly, every 10ms. Very early on, it might catch `worker` still in `NEW` (if `monitor` happens to run before `worker` has actually started) or already in `RUNNABLE`. Each time the observed state differs from `lastState`, a log entry is added and `lastState` is updated — so even if `monitor` polls dozens of times while `worker` remains `RUNNABLE`, only one log entry records that transition.

**Worker's busy-work phase.** For roughly the time it takes to count from 0 to 500 million (highly variable across machines, but typically tens to low hundreds of milliseconds), `worker` remains in `RUNNABLE`. `monitor`'s repeated polls during this phase all see the same state, so no additional log entries accumulate.

**Worker enters its synchronized-sleep phase.** Once the loop finishes, `worker` enters `synchronized (lock)` (uncontended, since no other thread wants `lock`) and calls `Thread.sleep(150)`. Its state transitions to `TIMED_WAITING` (sleeping with a defined duration). The next time `monitor` polls and sees this new state, it logs `"State changed to: TIMED_WAITING"`.

**Worker finishes.** After 150ms of sleeping, `worker`'s task completes, and its state becomes `TERMINATED`. `monitor`'s `while (worker.getState() != Thread.State.TERMINATED)` loop condition becomes `false` on its next check, so the loop exits, and the final `log.add("State changed to: TERMINATED")` line runs directly (outside the loop, guaranteeing this final entry is always recorded exactly once).

**Final reporting.** Both `worker.join()` and `monitor.join()` in the main thread ensure both threads have fully finished before `log.forEach(System.out::println)` prints the recorded timeline in order.

```
worker:  NEW -> RUNNABLE (busy loop, ~X ms) -> TIMED_WAITING (sleep 150ms) -> TERMINATED
monitor: polls every 10ms, logs only on CHANGE:
           RUNNABLE detected (assuming NEW was too brief to catch)
           TIMED_WAITING detected
           TERMINATED detected (loop exits, final log line runs)
```

**Output (illustrative — exact timing/order depends on the machine):**
```
State changed to: RUNNABLE
State changed to: TIMED_WAITING
State changed to: TERMINATED
```

## 7. Gotchas & takeaways

> Polling `getState()` in a tight loop (as `monitor` does, even with a 10ms sleep between checks) can miss very brief states entirely — if a thread passes through a state faster than the polling interval, that transition simply won't be observed. `NEW` is a common casualty of this, since a thread often transitions out of it almost immediately after `start()` is called, well within a 10ms window.

> `BLOCKED` (waiting for a lock) and `WAITING`/`TIMED_WAITING` (waiting for a condition via `wait()`/`join()`/`sleep()`) are genuinely different states representing different situations — a thread stuck in `BLOCKED` for a long time points to lock contention (something else is holding the lock too long), while one stuck in `WAITING` indefinitely points to a missing or lost `notify()` call. Correctly distinguishing them is often the key diagnostic step when debugging a stuck concurrent program.

- A `Thread`'s lifecycle moves through `NEW`, `RUNNABLE`, possibly `BLOCKED`/`WAITING`/`TIMED_WAITING`, and finally `TERMINATED` — always forward, never backward, never revisiting `NEW`.
- `getState()` reports the exact instantaneous state; rapid transitions can be missed by periodic polling, especially very brief ones.
- `BLOCKED` specifically means waiting to acquire a lock; `WAITING`/`TIMED_WAITING` means waiting for a notification, join, or timed sleep — the distinction is a key diagnostic signal.
- Understanding these states is essential for reading thread dumps and diagnosing concurrency problems like contention or threads stuck waiting indefinitely.
