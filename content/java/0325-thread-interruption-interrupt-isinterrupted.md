---
card: java
gi: 325
slug: thread-interruption-interrupt-isinterrupted
title: Thread interruption (interrupt/isInterrupted)
---

## 1. What it is

Thread interruption is Java's cooperative mechanism for asking a running thread to stop what it's doing. Calling `thread.interrupt()` sets an internal boolean "interrupt status" flag on that thread; it does **not** forcibly kill the thread or throw an exception into arbitrary code. The target thread must itself check for interruption — either by calling `Thread.isInterrupted()` (which reads the flag without clearing it) or `Thread.interrupted()` (a static method that reads *and clears* the flag on the *calling* thread) — or by calling a blocking method like `Thread.sleep()`, `Object.wait()`, or `Thread.join()`, which detect the flag and throw `InterruptedException` on the caller's behalf, clearing the flag as they do.

```java
public class InterruptDemo {
    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            while (!Thread.currentThread().isInterrupted()) {
                // pretend to do work
            }
            System.out.println("Worker noticed interruption and is exiting.");
        });
        worker.start();
        Thread.sleep(50);
        worker.interrupt(); // politely ask the worker to stop
        worker.join();
    }
}
```

`worker.interrupt()` only sets a flag; the loop's own check of `isInterrupted()` is what makes the thread actually respond and exit.

## 2. Why & when

There is no safe, general way to force a Java thread to stop instantly — the old `Thread.stop()` method existed for that but is deprecated and dangerous, because it can release locks mid-update and leave shared objects in a corrupted state. Interruption exists instead as a *request*, giving the target thread the chance to notice, clean up (close files, release locks, log state), and exit on its own terms.

- **Cancelling long-running or blocked tasks** — stopping a worker that's stuck in `Thread.sleep()`, waiting on a `BlockingQueue`, or blocked in network I/O that supports interruption.
- **Graceful application shutdown** — thread pools like `ExecutorService` use interruption internally when you call `shutdownNow()`, to ask worker threads to stop between (or during) tasks.
- **Responsive polling loops** — any loop that could otherwise run forever should periodically check `isInterrupted()` so it can be told to stop.

Interruption is cooperative: if the target thread never checks the flag and never calls an interruptible blocking method, `interrupt()` has no effect at all. It is a request, not a command.

## 3. Core concept

```java
public class InterruptCore {
    public static void main(String[] args) throws InterruptedException {
        Thread sleeper = new Thread(() -> {
            try {
                Thread.sleep(10_000); // long sleep
            } catch (InterruptedException e) {
                // sleep() detects the interrupt flag, throws this exception,
                // and CLEARS the flag as part of throwing it
                System.out.println("Sleep interrupted early: " + e.getMessage());
                return;
            }
            System.out.println("Slept the full 10 seconds (should not print).");
        });
        sleeper.start();
        Thread.sleep(100);
        sleeper.interrupt();
        sleeper.join();
    }
}
```

**How to run:** `java InterruptCore.java`

Because `sleeper` is blocked inside `Thread.sleep(10_000)` when `interrupt()` is called, the sleep itself detects the flag, immediately throws `InterruptedException`, and clears the flag — the thread wakes up almost instantly instead of waiting the full ten seconds.

## 4. Diagram

<svg viewBox="0 0 620 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="interrupt sets a flag; a blocking call or manual isInterrupted check is what makes the thread react">
  <rect x="8" y="8" width="604" height="174" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">Main thread</text>
  <rect x="20" y="40" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="60" fill="#79c0ff" font-size="10" text-anchor="middle">worker.interrupt()</text>
  <text x="230" y="60" fill="#8b949e" font-size="16">→</text>
  <rect x="260" y="40" width="180" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="350" y="60" fill="#6db33f" font-size="10" text-anchor="middle">sets interrupt flag = true</text>

  <text x="20" y="110" fill="#e6edf3" font-size="11">Worker thread (two possible reactions)</text>
  <rect x="20" y="120" width="270" height="45" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="155" y="140" fill="#e6edf3" font-size="10" text-anchor="middle">loop checks isInterrupted()</text>
  <text x="155" y="155" fill="#8b949e" font-size="9" text-anchor="middle">exits loop next iteration</text>

  <rect x="330" y="120" width="270" height="45" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="465" y="140" fill="#f85149" font-size="10" text-anchor="middle">blocked in sleep()/wait()/join()</text>
  <text x="465" y="155" fill="#8b949e" font-size="9" text-anchor="middle">wakes NOW, throws InterruptedException, flag cleared</text>
</svg>

`interrupt()` only flips a flag; how (and whether) the thread reacts depends on what it's doing when the flag is set.

## 5. Runnable example

Scenario: a worker thread polling a task queue, evolved from a busy-spin that ignores interruption, into one that responds to it in its loop condition, into a production-style task processor that responds to interruption both in its poll loop and while blocked, and re-asserts the flag correctly.

### Level 1 — Basic

```java
public class InterruptBasic {
    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            long spins = 0;
            while (spins < 3_000_000_000L) { // ignores interruption entirely (bug)
                spins++;
            }
            System.out.println("Worker finished all spins unconditionally.");
        });
        worker.start();
        Thread.sleep(50);
        System.out.println("Main requesting interruption...");
        worker.interrupt();
        worker.join(2000);
        System.out.println("Worker still alive after 2s? " + worker.isAlive());
    }
}
```

**How to run:** `java InterruptBasic.java`

Calling `interrupt()` sets the flag, but because the loop never checks it, the worker keeps spinning regardless — this demonstrates that interruption does nothing unless the target thread actually looks for it.

### Level 2 — Intermediate

```java
public class InterruptIntermediate {
    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            long spins = 0;
            while (!Thread.currentThread().isInterrupted()) {
                spins++;
            }
            System.out.println("Worker stopped after noticing interruption; spins=" + spins);
        });
        worker.start();
        Thread.sleep(50);
        System.out.println("Main requesting interruption...");
        worker.interrupt();
        worker.join(2000);
        System.out.println("Worker still alive after 2s? " + worker.isAlive());
    }
}
```

**How to run:** `java InterruptIntermediate.java`

Now the loop condition itself checks `isInterrupted()`, so the very first iteration after the flag is set exits the loop — the worker stops promptly instead of running forever.

### Level 3 — Advanced

```java
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

public class InterruptAdvanced {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> tasks = new LinkedBlockingQueue<>();

        Thread worker = new Thread(() -> {
            try {
                while (!Thread.currentThread().isInterrupted()) {
                    String task = tasks.take(); // blocks here until a task arrives, or interrupted
                    System.out.println("Processing: " + task);
                }
            } catch (InterruptedException e) {
                // take() detected the flag while blocked and cleared it while throwing
                System.out.println("Worker interrupted while waiting for a task; shutting down cleanly.");
                Thread.currentThread().interrupt(); // best practice: re-assert flag for any outer caller
            }
        });
        worker.start();

        tasks.put("task-1");
        Thread.sleep(50);
        System.out.println("Main requesting interruption while worker likely blocked in take()...");
        worker.interrupt();
        worker.join(2000);
        System.out.println("Worker still alive after 2s? " + worker.isAlive());
    }
}
```

**How to run:** `java InterruptAdvanced.java`

This version handles interruption whether the worker is busy in the loop or blocked inside `tasks.take()` waiting for work — `take()` throws `InterruptedException` the moment the flag is set, and the `catch` block re-asserts the interrupt flag with `Thread.currentThread().interrupt()`, a standard idiom so that any code further up the call stack can still observe that an interruption occurred.

## 6. Walkthrough

Execution starts in `main`: it creates a `LinkedBlockingQueue<String>` and starts `worker`. The worker immediately enters its `while` loop and calls `tasks.take()`, which blocks because the queue is empty — the worker thread is now parked, not spinning.

Back in `main`, `tasks.put("task-1")` unblocks the worker's `take()` call, returning `"task-1"`, which gets printed as `Processing: task-1`. The worker loops back to `take()` and blocks again, waiting for the next task.

`main` sleeps 50ms to give the worker time to re-enter the blocked state, then calls `worker.interrupt()`. This sets the worker thread's interrupt flag to `true`. Because the worker is currently blocked inside `take()`, the JVM's blocking-method machinery detects the flag immediately, clears it back to `false`, and throws `InterruptedException` out of `take()` — the worker does not have to wait for its next loop check.

The `catch (InterruptedException e)` block runs: it prints the shutdown message, then calls `Thread.currentThread().interrupt()` to set the flag back to `true` one more time. This matters because the `catch` block just consumed (cleared) the flag by catching the exception — re-setting it means that if this code were inside a larger method that returns control to other logic, that logic could still check `isInterrupted()` and know an interruption happened.

The worker's `run()` method then returns naturally, ending the thread. `main`'s `worker.join(2000)` returns almost immediately (well under the 2-second timeout) because the thread has already terminated, and `worker.isAlive()` prints `false`.

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="sequence: put task, worker processes it, main interrupts, take() throws, worker exits">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="10">main: put("task-1")</text>
  <text x="20" y="50" fill="#8b949e" font-size="9">→ worker.take() returns "task-1", prints Processing: task-1</text>
  <text x="20" y="72" fill="#e6edf3" font-size="10">worker loops back, blocks in take() again</text>
  <text x="20" y="94" fill="#e6edf3" font-size="10">main: worker.interrupt() (worker is blocked)</text>
  <text x="20" y="116" fill="#79c0ff" font-size="10">→ take() throws InterruptedException, flag cleared</text>
  <text x="20" y="138" fill="#6db33f" font-size="10">catch: print shutdown msg, re-set flag, thread exits</text>
</svg>

## 7. Gotchas & takeaways

> Catching `InterruptedException` and silently swallowing it (an empty `catch` block) is one of the most common concurrency bugs — it discards the fact that someone asked this thread to stop, and any outer code checking `isInterrupted()` will never know.

- `interrupt()` sets a flag; it never forcibly stops a thread or throws exceptions into arbitrary running code.
- `Thread.isInterrupted()` reads the flag without clearing it; the static `Thread.interrupted()` reads and clears the flag on the *current* thread — easy to mix up.
- Blocking methods (`sleep`, `wait`, `join`, `BlockingQueue.take`) detect interruption for you and throw `InterruptedException`, clearing the flag as part of throwing it.
- When you catch `InterruptedException` and can't propagate it (e.g., inside a `Runnable`), re-assert the flag with `Thread.currentThread().interrupt()` so callers further up can still detect it.
- `Thread.stop()` is deprecated and unsafe — never use it to cancel a thread; use cooperative interruption instead.
