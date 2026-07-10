---
card: java
gi: 851
slug: thread-lifecycle-states-new-runnable-blocked-waiting-timed-w
title: Thread lifecycle & states (NEW, RUNNABLE, BLOCKED, WAITING, TIMED_WAITING, TERMINATED)
---

## 1. What it is

Every Java thread, at any given moment, is in exactly one of six states defined by the `Thread.State` enum, queryable via `thread.getState()`: **NEW** (created but `start()` not yet called), **RUNNABLE** (executing, or ready and waiting for CPU time — the JVM doesn't distinguish "actually running" from "eligible to run" as separate states), **BLOCKED** (waiting to acquire a `synchronized` lock currently held by another thread), **WAITING** (paused indefinitely, waiting for another thread to explicitly wake it, via `Object.wait()` with no timeout, `Thread.join()` with no timeout, or `LockSupport.park()`), **TIMED_WAITING** (like `WAITING`, but with a bound — `Thread.sleep(ms)`, `Object.wait(ms)`, `Thread.join(ms)`), and **TERMINATED** (run completed, either normally or via an uncaught exception).

## 2. Why & when

Understanding these states matters directly for debugging concurrency problems: a thread stuck in `BLOCKED` for a long time suggests lock contention or a deadlock; a thread stuck in `WAITING` suggests it's genuinely paused expecting another thread to notify or complete something, and that expected wake-up may never be arriving (a classic "lost wakeup" bug); a thread that never leaves `NEW` means `start()` was never called at all (a surprisingly common bug — accidentally calling `run()` directly instead of `start()`, which executes the code on the *calling* thread rather than starting a new one). Tools like thread dumps (`jstack`, or a debugger's thread view) report exactly these states, so recognizing what each one implies about what a thread is currently doing (or failing to do) is essential for diagnosing hangs and contention.

## 3. Core concept

```java
Thread t = new Thread(() -> {
    try { Thread.sleep(100); } catch (InterruptedException ignored) {}
});

t.getState(); // NEW -- created, but start() hasn't been called yet
t.start();
t.getState(); // RUNNABLE (very likely, right after start()) -- or briefly TIMED_WAITING if it's already sleeping
// ... after 100ms elapse and the thread's run() method returns ...
t.getState(); // TERMINATED
```

The six states are mutually exclusive and collectively exhaustive — at any instant, `getState()` returns exactly one of them, and a thread transitions between them according to specific triggers (calling `start()`, entering/leaving a `synchronized` block, calling `wait()`/`sleep()`/`join()`, or a monitored method returning/throwing).

## 4. Diagram

<svg viewBox="0 0 640 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A thread's lifecycle moves from NEW through RUNNABLE, possibly cycling through BLOCKED, WAITING, or TIMED_WAITING, and finally to TERMINATED">
  <g font-family="sans-serif">
    <rect x="30" y="20" width="100" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
    <text x="80" y="45" fill="#e6edf3" font-size="10" text-anchor="middle">NEW</text>

    <line x1="130" y1="40" x2="180" y2="40" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a851)"/>
    <text x="155" y="30" fill="#79c0ff" font-size="8">start()</text>

    <rect x="190" y="20" width="120" height="40" rx="6" fill="#1c2430" stroke="#3fb950"/>
    <text x="250" y="45" fill="#e6edf3" font-size="10" text-anchor="middle">RUNNABLE</text>

    <line x1="250" y1="60" x2="140" y2="100" stroke="#f85149" stroke-width="1.5" marker-end="url(#a851)"/>
    <rect x="60" y="100" width="120" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
    <text x="120" y="125" fill="#e6edf3" font-size="10" text-anchor="middle">BLOCKED</text>
    <text x="120" y="150" fill="#8b949e" font-size="8" text-anchor="middle">waiting for a lock</text>

    <line x1="250" y1="60" x2="250" y2="100" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a851)"/>
    <rect x="190" y="100" width="120" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
    <text x="250" y="125" fill="#e6edf3" font-size="10" text-anchor="middle">WAITING</text>
    <text x="250" y="150" fill="#8b949e" font-size="8" text-anchor="middle">indefinite wait/join</text>

    <line x1="250" y1="60" x2="360" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a851)"/>
    <rect x="320" y="100" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
    <text x="390" y="125" fill="#e6edf3" font-size="10" text-anchor="middle">TIMED_WAITING</text>
    <text x="390" y="150" fill="#8b949e" font-size="8" text-anchor="middle">sleep/timed wait/join</text>

    <line x1="120" y1="140" x2="250" y2="180" stroke="#8b949e" stroke-width="1.5"/>
    <line x1="250" y1="140" x2="250" y2="180" stroke="#8b949e" stroke-width="1.5"/>
    <line x1="390" y1="140" x2="250" y2="180" stroke="#8b949e" stroke-width="1.5"/>
    <line x1="250" y1="60" x2="250" y2="180" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a851)"/>

    <rect x="190" y="185" width="120" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
    <text x="250" y="207" fill="#e6edf3" font-size="10" text-anchor="middle">TERMINATED</text>
  </g>
  <defs><marker id="a851" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*RUNNABLE can cycle through BLOCKED, WAITING, or TIMED_WAITING (and back) any number of times before finally reaching TERMINATED.*

## 5. Runnable example

Scenario: a monitoring harness observing a worker thread's state transitions live, growing from basic NEW/RUNNABLE/TERMINATED observation, through capturing BLOCKED under lock contention, to capturing WAITING and TIMED_WAITING in a single richer scenario.

### Level 1 — Basic

```java
public class LifecycleBasic {
    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            try { Thread.sleep(50); } catch (InterruptedException ignored) {}
        });

        System.out.println("before start(): " + worker.getState());
        worker.start();
        System.out.println("right after start(): " + worker.getState());
        worker.join();
        System.out.println("after join() returns: " + worker.getState());
    }
}
```

**How to run:** `java LifecycleBasic.java` (JDK 17+). The state right after `start()` is very likely `TIMED_WAITING` here (since the thread immediately calls `sleep`), but could occasionally print `RUNNABLE` if the check happens to run before the new thread has started sleeping — both are valid, timing-dependent outcomes.

Expected output shape:
```
before start(): NEW
right after start(): TIMED_WAITING
after join() returns: TERMINATED
```

`getState()` before `start()` is always exactly `NEW`; after `join()` returns (meaning the thread has fully finished), it's always exactly `TERMINATED` — these two are deterministic, unlike the state observed immediately after `start()`.

### Level 2 — Intermediate

```java
public class LifecycleBlocked {
    static final Object lock = new Object();

    public static void main(String[] args) throws InterruptedException {
        Thread holder = new Thread(() -> {
            synchronized (lock) {
                try { Thread.sleep(200); } catch (InterruptedException ignored) {}
            }
        });

        Thread contender = new Thread(() -> {
            synchronized (lock) { // this thread will BLOCK here while "holder" holds the lock
                System.out.println("contender finally acquired the lock");
            }
        });

        holder.start();
        Thread.sleep(50); // give "holder" time to acquire the lock first
        contender.start();
        Thread.sleep(50); // give "contender" time to attempt the lock and block

        System.out.println("contender's state while waiting for the lock: " + contender.getState());

        holder.join();
        contender.join();
        System.out.println("contender's state after both finish: " + contender.getState());
    }
}
```

**How to run:** `java LifecycleBlocked.java`.

Expected output:
```
contender finally acquired the lock
contender's state while waiting for the lock: BLOCKED
contender's state after both finish: TERMINATED
```

The real-world concern added: capturing `BLOCKED` directly — `contender` attempts to enter the `synchronized (lock)` block while `holder` is still inside it (sleeping for 200ms), so `contender` is genuinely stuck waiting to acquire the monitor lock, exactly the situation `BLOCKED` represents, distinct from `WAITING` (which represents a thread that voluntarily paused itself, not one contending for a lock).

### Level 3 — Advanced

```java
public class LifecycleWaitingStates {
    static final Object monitor = new Object();

    public static void main(String[] args) throws InterruptedException {
        Thread waiter = new Thread(() -> {
            synchronized (monitor) {
                try {
                    monitor.wait(); // INDEFINITE wait -- WAITING state, until notify() is called
                } catch (InterruptedException ignored) {}
            }
        });

        Thread sleeper = new Thread(() -> {
            try {
                Thread.sleep(300); // BOUNDED wait -- TIMED_WAITING state
            } catch (InterruptedException ignored) {}
        });

        waiter.start();
        sleeper.start();
        Thread.sleep(50); // let both threads settle into their respective waiting states

        System.out.println("waiter's state (indefinite wait()): " + waiter.getState());
        System.out.println("sleeper's state (bounded sleep()): " + sleeper.getState());

        synchronized (monitor) {
            monitor.notify(); // wake the waiter thread up
        }

        waiter.join();
        sleeper.join();
        System.out.println("both terminated: waiter=" + waiter.getState() + ", sleeper=" + sleeper.getState());
    }
}
```

**How to run:** `java LifecycleWaitingStates.java`.

Expected output:
```
waiter's state (indefinite wait()): WAITING
sleeper's state (bounded sleep()): TIMED_WAITING
both terminated: waiter=TERMINATED, sleeper=TERMINATED
```

This adds the production-flavored hard case: distinguishing `WAITING` from `TIMED_WAITING` directly, side by side. `waiter` calls `monitor.wait()` with no timeout — it will remain in `WAITING` indefinitely until some other thread calls `monitor.notify()`/`notifyAll()`, with no automatic wake-up. `sleeper` calls `Thread.sleep(300)` — a *bounded* pause that will end on its own after 300ms regardless of any other thread's action, correctly reported as `TIMED_WAITING`. The distinction matters practically: a thread stuck in `WAITING` with no corresponding `notify()` ever coming is a genuine "lost wakeup" bug, while a thread in `TIMED_WAITING` will always eventually proceed on its own.

## 6. Walkthrough

Tracing `LifecycleWaitingStates.main`:

1. `waiter` is started; inside its `run()`, it enters the `synchronized (monitor)` block (acquiring the monitor lock) and calls `monitor.wait()`. This call **releases** the monitor lock (a key detail — `wait()` gives up the lock it was holding while it waits, allowing other threads to acquire that same lock) and puts the thread into the `WAITING` state, with no time bound.
2. `sleeper` is started independently; it calls `Thread.sleep(300)`, which does **not** involve any lock at all — it simply pauses the thread for up to 300 milliseconds, placing it in `TIMED_WAITING`.
3. After the main thread's own `Thread.sleep(50)` gives both threads time to settle into their respective states, `waiter.getState()` correctly reports `WAITING` and `sleeper.getState()` correctly reports `TIMED_WAITING` — both are "paused," but for fundamentally different reasons (indefinite external wake-up dependency versus a bounded, self-resolving timer).
4. The main thread then enters `synchronized (monitor)` itself (acquiring the lock `waiter` released back in step 1) and calls `monitor.notify()`, which wakes up exactly one thread waiting on that monitor — here, `waiter`. `waiter` then re-acquires the monitor lock (since `wait()`'s contract requires reacquiring the lock before returning) and, since its `synchronized` block has no more code after the `wait()` call, exits and terminates.
5. Independently, `sleeper`'s 300ms sleep duration eventually elapses on its own, regardless of the `notify()` call (which has nothing to do with `sleeper`), and it too terminates. Both `join()` calls in `main` return once each thread reaches `TERMINATED`, confirmed by the final printed states.

## 7. Gotchas & takeaways

> **Gotcha:** calling a thread's `run()` method directly (`worker.run()`) instead of `start()` does **not** create a new thread at all — it simply executes the `Runnable`'s code synchronously on whatever thread made the call, and `getState()` would never transition through `NEW` or `RUNNABLE` in the way expected, since no actual new thread was ever created. This is a common, easy-to-miss beginner mistake that silently produces sequential (not concurrent) execution.

- A thread is always in exactly one of six states: `NEW`, `RUNNABLE`, `BLOCKED`, `WAITING`, `TIMED_WAITING`, or `TERMINATED`, queryable via `getState()`.
- `BLOCKED` means waiting to acquire a `synchronized` lock currently held by another thread; `WAITING`/`TIMED_WAITING` mean the thread voluntarily paused itself (via `wait`, `join`, or `sleep`), with or without a time bound respectively.
- `Object.wait()` releases the monitor lock it was called under while waiting, and requires reacquiring that lock before returning once woken — a detail that matters for understanding lock contention around `wait`/`notify` patterns.
- A thread stuck in `BLOCKED` suggests lock contention (possibly a deadlock); a thread stuck in `WAITING` with no corresponding `notify()` ever coming suggests a lost-wakeup bug.
- Calling `run()` directly instead of `start()` never actually creates a concurrent thread — it silently executes synchronously on the calling thread instead.
