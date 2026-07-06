---
card: java
gi: 319
slug: daemon-threads
title: Daemon threads
---

## 1. What it is

A **daemon thread** is a thread marked (via `setDaemon(true)`, before it's started) as a background helper that should **not** keep the JVM alive — when every remaining thread is a daemon thread, the JVM exits immediately, abandoning any daemon threads mid-execution, with no cleanup or final code running. Ordinary ("user") threads, by contrast, do keep the JVM running until they finish.

```java
public class DaemonDemo {
    public static void main(String[] args) throws InterruptedException {
        Thread daemon = new Thread(() -> {
            while (true) {
                System.out.println("Daemon still running...");
                try { Thread.sleep(300); } catch (InterruptedException e) { return; }
            }
        });
        daemon.setDaemon(true); // MUST be called before start()
        daemon.start();

        Thread.sleep(1000);
        System.out.println("Main thread exiting -- the JVM will terminate the daemon thread too.");
    }
}
```

`daemon.setDaemon(true)` marks the thread before it starts; when `main` finishes after its one-second sleep, the JVM has no remaining user threads (the daemon doesn't count), so it exits immediately — the daemon thread's infinite loop is simply abandoned mid-execution, with no further "Daemon still running..." lines printed after that point.

## 2. Why & when

Some background tasks exist purely to support the main work of a program — periodic cleanup, monitoring, caching maintenance — and have no meaningful "final result" that needs to be preserved or completed. If such a task were an ordinary user thread, the JVM would wait for it to finish before exiting, potentially hanging the program indefinitely (or requiring the background task to explicitly notice a shutdown request and stop itself).

- **Background housekeeping** — periodic cache eviction, connection-pool maintenance, or monitoring loops that should simply stop existing when the main application shuts down, with no need for a graceful wind-down.
- **Avoiding hung shutdowns** — a forgotten infinite-loop background thread, if it were a user thread, would prevent the JVM from ever exiting; marking it a daemon thread avoids this failure mode entirely.
- **JVM internals** — the JVM itself uses daemon threads for things like garbage collection, which should never prevent program exit.

Mark a thread as a daemon only when its work is truly disposable — abandoning it mid-task at any arbitrary point must be safe. Never use a daemon thread for anything that writes important data or needs to complete a transaction; since it can be terminated at any instant with zero warning and zero cleanup code guaranteed to run, using one for critical work risks silent data loss or corruption.

## 3. Core concept

```java
public class DaemonCore {
    public static void main(String[] args) throws InterruptedException {
        Thread userThread = new Thread(() -> System.out.println("User thread: I will be waited for."));
        Thread daemonThread = new Thread(() -> System.out.println("Daemon thread: I will NOT be waited for."));
        daemonThread.setDaemon(true);

        System.out.println("userThread.isDaemon() = " + userThread.isDaemon());
        System.out.println("daemonThread.isDaemon() = " + daemonThread.isDaemon());

        userThread.start();
        daemonThread.start();
    }
}
```

`isDaemon()` confirms each thread's status before starting either — note that `main` here doesn't call `join()` on either thread, so this specific program's exit timing is itself a small demonstration of the daemon/non-daemon distinction: the JVM will actually wait for `userThread` to finish (since it's a user thread) even without an explicit `join()`, but would not have waited for `daemonThread` alone.

## 4. Diagram

<svg viewBox="0 0 600 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The JVM waits for all user threads to finish before exiting, but abandons daemon threads immediately once no user threads remain">
  <rect x="8" y="8" width="584" height="124" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="260" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="55" fill="#6db33f" font-size="10" text-anchor="middle">user thread(s)</text>
  <text x="20" y="90" fill="#8b949e" font-size="9">JVM waits for ALL of these before exiting</text>

  <rect x="320" y="30" width="260" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="450" y="55" fill="#f85149" font-size="10" text-anchor="middle">daemon thread(s)</text>
  <text x="320" y="90" fill="#8b949e" font-size="9">abandoned instantly once no user threads remain</text>
</svg>

The JVM's exit decision depends entirely on whether any non-daemon (user) threads are still alive.

## 5. Runnable example

Scenario: a background cache-cleanup task, evolved from a basic daemon-thread demonstration into a version that shows the program exiting while the daemon is mid-cycle, then into a properly designed application where the daemon status is combined with a deliberate, cooperative shutdown signal for cleaner (though still not guaranteed) termination.

### Level 1 — Basic

```java
public class DaemonBasic {
    public static void main(String[] args) throws InterruptedException {
        Thread cleanupTask = new Thread(() -> {
            int cycle = 0;
            while (true) {
                cycle++;
                System.out.println("Cache cleanup cycle " + cycle);
                try { Thread.sleep(200); } catch (InterruptedException e) { return; }
            }
        });
        cleanupTask.setDaemon(true);
        cleanupTask.start();

        System.out.println("Main doing work for 700ms...");
        Thread.sleep(700);
        System.out.println("Main exiting.");
    }
}
```

**How to run:** `java DaemonBasic.java`

The infinite `cleanupTask` loop never runs its own termination logic — the program simply ends once `main`'s 700ms sleep completes, abandoning the daemon thread wherever it happened to be at that instant, typically after 3 cycles (since 700ms / 200ms ≈ 3.5).

### Level 2 — Intermediate

Same cleanup task, now compared directly against an equivalent **user** thread to show the difference in program exit behavior explicitly.

```java
public class DaemonIntermediate {
    static Thread makeLoopingThread(String name) {
        return new Thread(() -> {
            int cycle = 0;
            while (cycle < 3) { // bounded, so the USER-thread version doesn't hang forever
                cycle++;
                System.out.println(name + " cycle " + cycle);
                try { Thread.sleep(200); } catch (InterruptedException e) { return; }
            }
        });
    }

    public static void main(String[] args) throws InterruptedException {
        Thread daemonTask = makeLoopingThread("Daemon");
        daemonTask.setDaemon(true);
        daemonTask.start();

        // Deliberately NOT joining or waiting for the daemon -- main exits almost immediately.
        System.out.println("Main finishing right away -- the daemon likely won't complete all 3 cycles.");
    }
}
```

**How to run:** `java DaemonIntermediate.java`

Because `main` has no more work and doesn't wait for `daemonTask`, the JVM exits essentially as soon as `main` returns — the daemon thread has barely started (perhaps printing "cycle 1" or nothing at all, depending on scheduling) before the program terminates, since there are no user threads left to keep it alive.

### Level 3 — Advanced

Same cleanup task, now designed properly: still a daemon thread (so it never blocks JVM exit if forgotten), but combined with a cooperative shutdown flag the main thread sets before its own planned exit, giving the cleanup task a chance to notice and stop gracefully — though the daemon-thread safety net remains in place in case that cooperative signal is ever missed.

```java
import java.util.concurrent.atomic.AtomicBoolean;

public class DaemonAdvanced {
    public static void main(String[] args) throws InterruptedException {
        AtomicBoolean shutdownRequested = new AtomicBoolean(false);

        Thread cleanupTask = new Thread(() -> {
            int cycle = 0;
            while (!shutdownRequested.get()) {
                cycle++;
                System.out.println("Cleanup cycle " + cycle);
                try { Thread.sleep(150); } catch (InterruptedException e) { return; }
            }
            System.out.println("Cleanup task noticed shutdown request and stopped gracefully after " + cycle + " cycles.");
        });
        cleanupTask.setDaemon(true); // safety net: JVM won't hang even if this line is somehow skipped
        cleanupTask.start();

        System.out.println("Main doing work...");
        Thread.sleep(500);

        System.out.println("Main requesting graceful shutdown...");
        shutdownRequested.set(true);
        cleanupTask.join(1000); // give it a moment to notice and finish gracefully

        System.out.println("Main exiting. Cleanup task alive? " + cleanupTask.isAlive());
    }
}
```

**How to run:** `java DaemonAdvanced.java`

`shutdownRequested` is an `AtomicBoolean` that both threads share; `cleanupTask` checks it at the top of every loop iteration, and setting it to `true` from the main thread lets the cleanup task notice on its *next* check (within roughly 150ms, its sleep interval) and exit its loop cleanly, printing a graceful shutdown message — the daemon flag remains set purely as a safety net, ensuring correctness (no hung JVM) even if this cooperative signaling were ever broken or forgotten.

## 6. Walkthrough

Trace `DaemonAdvanced.main` step by step.

**Startup.** `shutdownRequested` starts as `false`. `cleanupTask` is created, marked as a daemon, and started — it enters its `while (!shutdownRequested.get())` loop, printing "Cleanup cycle 1", sleeping 150ms, then checking the flag again (still `false`), printing "Cleanup cycle 2", and so on.

**Main's own work.** Concurrently, the main thread sleeps for 500ms — during this window, `cleanupTask` completes roughly three cycles (500ms / 150ms ≈ 3.3), printing "Cleanup cycle 1", "2", and "3" at approximately 150ms intervals.

**Requesting shutdown.** After its 500ms sleep, the main thread prints its intent and calls `shutdownRequested.set(true)`. This write is visible to `cleanupTask` because `AtomicBoolean` provides the necessary memory visibility guarantees (its whole purpose is safe concurrent access without needing a separate lock).

**The cleanup task notices.** At some point soon after — specifically, the next time `cleanupTask` reaches the top of its `while` loop and calls `shutdownRequested.get()` — it sees `true` and exits the loop. This happens within one sleep interval (150ms) of the flag being set, not instantly, since the thread is likely still sleeping when the flag changes.

**Joining and confirming.** `cleanupTask.join(1000)` in the main thread waits up to a full second for the cleanup task to finish — comfortably more than the roughly 150ms it actually needs to notice the flag and print its graceful-shutdown message. By the time `join` returns, `cleanupTask` has genuinely finished (its loop exited, its final message printed), so `cleanupTask.isAlive()` reports `false`.

**Final print.** Confirms the cleanup task is no longer alive, having shut down gracefully rather than being abruptly abandoned by JVM exit.

```
t=0ms:    cleanupTask starts; cycle 1 prints, sleeps 150ms
t=150ms:  check flag (false) -> cycle 2 prints, sleeps
t=300ms:  check flag (false) -> cycle 3 prints, sleeps
t=450ms:  check flag (false) -> cycle 4 prints, sleeps
t=500ms:  main wakes, sets shutdownRequested=true
t=600ms:  cleanupTask wakes from its sleep, checks flag (true) -> exits loop, prints graceful message
t=600ms:  main's join(1000) returns (cleanupTask finished well within the 1000ms timeout)
```

**Output (approximate timing, illustrative):**
```
Main doing work...
Cleanup cycle 1
Cleanup cycle 2
Cleanup cycle 3
Cleanup cycle 4
Main requesting graceful shutdown...
Cleanup task noticed shutdown request and stopped gracefully after 4 cycles.
Main exiting. Cleanup task alive? false
```

## 7. Gotchas & takeaways

> `setDaemon(true)` **must** be called before `start()` — calling it on an already-started thread throws `IllegalThreadStateException`. A thread's daemon status is fixed at the moment it starts running and cannot be changed afterward.

> A daemon thread can be terminated by the JVM at literally any point in its execution, with zero warning, zero guaranteed cleanup code, and zero chance to finish an in-progress operation — never use a daemon thread for anything where being abandoned mid-task (mid-write to a file, mid-transaction) would cause real harm. The cooperative shutdown-flag pattern shown in Level 3 is what makes graceful (rather than abrupt) termination possible, but the daemon flag itself is purely a last-resort safety net, not a substitute for that cooperative design.

- A daemon thread does not keep the JVM alive; once no non-daemon (user) threads remain, the JVM exits immediately, abandoning any daemon threads mid-execution.
- `setDaemon(true)` must be called before `start()`; it cannot be changed once the thread is running.
- Use daemon threads only for genuinely disposable background work — never for anything that must complete or clean up properly before the program exits.
- For graceful shutdown of background work, combine the daemon flag (as a safety net) with a cooperative signal (like a shared `AtomicBoolean`) the background thread checks periodically.
