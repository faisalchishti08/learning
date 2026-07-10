---
card: java
gi: 856
slug: interruption-model
title: Interruption model
---

## 1. What it is

Java's thread interruption is a **cooperative** cancellation signal — calling `thread.interrupt()` does not forcibly stop the target thread; it merely sets an internal boolean "interrupted" flag on that thread and, if the thread is currently blocked in an interruptible operation (`Thread.sleep`, `Object.wait`, `Thread.join`, many blocking I/O and concurrency operations), causes that operation to immediately throw `InterruptedException` (which also clears the flag as a side effect). Code must actively check for interruption — via the static `Thread.interrupted()` (checks the flag **and clears it**) or the instance method `thread.isInterrupted()` (checks the flag **without clearing it**) — and choose to respond, typically by stopping what it's doing. Nothing about interruption is automatic or forced; a thread that never checks its interrupted status, and is never blocked in an interruptible call, simply ignores an `interrupt()` call entirely.

## 2. Why & when

Forcibly killing a thread mid-execution (the deprecated, dangerous `Thread.stop()`) can leave shared data structures in an inconsistent state — stopped in the middle of updating one field of a multi-field invariant, for instance — which is exactly why that mechanism was deprecated. Cooperative interruption exists instead: the target thread itself decides *when* it's safe to respond to a cancellation request, typically by checking its own interrupted status at safe points in its logic (the top of a loop iteration, before starting a new unit of work) and cleaning up or exiting gracefully rather than being torn down mid-operation. Use interruption whenever a long-running or background task needs to support graceful cancellation — a worker thread processing a queue that should stop when the application shuts down, a long computation that should abort if its result is no longer needed.

## 3. Core concept

```java
Thread worker = new Thread(() -> {
    while (!Thread.currentThread().isInterrupted()) { // check at a safe point, each loop iteration
        // do one unit of work
    }
    System.out.println("worker noticed interruption and is exiting cleanly");
});
worker.start();
Thread.sleep(100);
worker.interrupt(); // sets the flag -- does NOT forcibly stop anything

// If the worker were instead BLOCKED in Thread.sleep() or Object.wait() at the moment
// interrupt() is called, that blocking call would immediately throw InterruptedException
// (and the flag would be cleared as part of that), rather than the loop check ever needing to run.
```

Whether interruption manifests as an `InterruptedException` (if blocked in an interruptible call) or as a flag the code must explicitly poll (if doing non-blocking computation) depends entirely on what the target thread happens to be doing at the moment `interrupt()` is called.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Calling interrupt on a thread either throws InterruptedException immediately if the thread is blocked in an interruptible call, or simply sets a flag that must be explicitly checked if the thread is doing non-blocking work">
  <rect x="240" y="15" width="160" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="40" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">thread.interrupt()</text>

  <line x1="290" y1="55" x2="150" y2="90" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a856)"/>
  <line x1="350" y1="55" x2="490" y2="90" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a856)"/>

  <rect x="40" y="95" width="220" height="55" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="150" y="118" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">blocked in sleep/wait/join</text>
  <text x="150" y="135" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">throws InterruptedException NOW</text>

  <rect x="380" y="95" width="220" height="55" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="490" y="118" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">doing non-blocking work</text>
  <text x="490" y="135" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">just sets a flag -- must be polled</text>

  <defs><marker id="a856" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*The same `interrupt()` call has two different effects, depending entirely on what the target thread happens to be doing at that moment.*

## 5. Runnable example

Scenario: a cancellable background task, growing from basic interruption of a sleeping thread, through a cooperative polling loop for non-blocking work, to the correct pattern for restoring interrupt status when a method catches `InterruptedException` but doesn't own the overall cancellation decision.

### Level 1 — Basic

```java
public class InterruptSleepingThread {
    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            try {
                Thread.sleep(5000); // long sleep -- will be interrupted well before it naturally ends
                System.out.println("this line never runs -- interrupted before the sleep finished");
            } catch (InterruptedException e) {
                System.out.println("worker: caught InterruptedException, exiting");
            }
        });

        worker.start();
        Thread.sleep(100); // let worker get into its sleep call first
        worker.interrupt(); // immediately throws InterruptedException inside worker's sleep(5000)
        worker.join();
        System.out.println("main: worker has finished");
    }
}
```

**How to run:** `java InterruptSleepingThread.java` (JDK 17+).

Expected output:
```
worker: caught InterruptedException, exiting
main: worker has finished
```

Because `worker` was blocked in `Thread.sleep(5000)` at the moment `interrupt()` was called, that sleep call throws `InterruptedException` immediately, rather than actually waiting the full 5 seconds — this is the "blocked in an interruptible call" case.

### Level 2 — Intermediate

```java
public class CooperativePollingLoop {
    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            long iterations = 0;
            while (!Thread.currentThread().isInterrupted()) { // NON-blocking work -- must poll explicitly
                iterations++; // simulate doing a unit of CPU-bound work, no blocking calls involved
            }
            System.out.println("worker: noticed interruption after " + iterations + " iterations, exiting cleanly");
        });

        worker.start();
        Thread.sleep(50); // let worker run for a bit
        worker.interrupt(); // just sets the flag -- worker must check isInterrupted() to notice
        worker.join();
        System.out.println("main: worker has finished");
    }
}
```

**How to run:** `java CooperativePollingLoop.java`. The exact iteration count varies by machine speed.

Expected output shape:
```
worker: noticed interruption after 84213764 iterations, exiting cleanly
main: worker has finished
```

The real-world concern added: since `worker` is doing pure CPU-bound, non-blocking work (no `sleep`/`wait`/`join` calls), `interrupt()` has no `InterruptedException` to throw — it only sets the flag, and `worker`'s own `while (!Thread.currentThread().isInterrupted())` check is what actually notices it and exits the loop. Without that explicit check, `worker` would simply ignore the interruption entirely and loop forever.

### Level 3 — Advanced

```java
public class RestoreInterruptStatusPattern {

    // A reusable helper method that does NOT own the overall cancellation decision --
    // it just performs one interruptible step and needs to correctly report interruption
    // back to whichever caller DOES own that decision.
    static boolean attemptWithRetry(int maxAttempts) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                Thread.sleep(50); // stands in for some interruptible operation, like a network call
                return true; // succeeded
            } catch (InterruptedException e) {
                // WRONG (anti-pattern): silently swallowing this loses the interruption signal entirely,
                // and the caller has no way to know cancellation was requested.
                // RIGHT: restore the interrupt status so code higher up the call stack can still see it.
                Thread.currentThread().interrupt();
                return false; // stop retrying -- honor the cancellation request
            }
        }
        return false;
    }

    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            boolean succeeded = attemptWithRetry(5);
            // Because attemptWithRetry restored the interrupt status, THIS code can still observe it:
            System.out.println("attemptWithRetry succeeded: " + succeeded);
            System.out.println("interrupt status correctly still visible here: " + Thread.currentThread().isInterrupted());
        });

        worker.start();
        Thread.sleep(20);
        worker.interrupt();
        worker.join();
    }
}
```

**How to run:** `java RestoreInterruptStatusPattern.java`.

Expected output:
```
attemptWithRetry succeeded: false
interrupt status correctly still visible here: true
```

This adds the production-flavored hard case: `attemptWithRetry` catches `InterruptedException` internally (since it needs to stop its retry loop), but it doesn't get to decide the *overall* fate of the thread — that decision belongs to whatever code called it. Calling `Thread.currentThread().interrupt()` inside the `catch` block **restores** the interrupt status that catching the exception would otherwise have silently consumed, so that code further up the call stack (here, the lambda in `worker`) can still observe that a cancellation was requested and react accordingly. Silently swallowing `InterruptedException` without this restoration is a well-known anti-pattern that permanently loses the cancellation signal.

## 6. Walkthrough

Tracing `RestoreInterruptStatusPattern.main`:

1. `worker` is started; it calls `attemptWithRetry(5)`, which enters its `for` loop and calls `Thread.sleep(50)` on its first attempt.
2. `worker.interrupt()` is called from `main` after a short delay, while `worker` is blocked inside that `Thread.sleep(50)` call — this immediately throws `InterruptedException` inside `attemptWithRetry`'s `try` block, and as a side effect of the exception being thrown this way, the thread's interrupt status is automatically **cleared** at that point (a detail of how `sleep`/`wait`/`join` handle interruption internally).
3. The `catch (InterruptedException e)` block runs. Critically, it calls `Thread.currentThread().interrupt()` **before** returning `false` — this re-sets the interrupt flag that the `sleep` call's exception-throwing had just cleared, ensuring the flag correctly reflects "yes, a cancellation was requested" for any code that checks it afterward.
4. `attemptWithRetry` returns `false` to its caller (the lambda running inside `worker`), reporting that it did not succeed — but *why* it didn't succeed (a genuine failure versus an interruption) isn't distinguishable from the boolean return value alone; that's exactly why restoring the interrupt flag matters, since it's a separate, independent channel carrying that information.
5. Back in the lambda, `Thread.currentThread().isInterrupted()` is checked and correctly reports `true` — proving that even though the actual `InterruptedException` was caught and handled two calls deep inside `attemptWithRetry`, the broader signal that a cancellation was requested successfully survived that boundary, precisely because `attemptWithRetry` took care to restore the flag before returning, rather than silently discarding it.

## 7. Gotchas & takeaways

> **Gotcha:** catching `InterruptedException` and doing nothing with it (`catch (InterruptedException e) {}`, an empty or merely logging catch block) is one of the most common and most damaging concurrency anti-patterns in Java code — it silently discards the cancellation signal entirely, meaning no other code anywhere in the call stack can ever learn that an interruption was requested. Always either propagate the exception (declare it in the method's `throws` clause, letting it continue up the stack), or if it must be caught locally, call `Thread.currentThread().interrupt()` to restore the flag before returning.

- Interruption is cooperative, not forcible — `interrupt()` sets a flag (and, if the target is blocked in an interruptible call, causes `InterruptedException` to be thrown) but never forcibly stops anything.
- `Thread.interrupted()` (static) checks and **clears** the flag; `thread.isInterrupted()` (instance) checks **without clearing** it — using the wrong one for a given need is an easy mistake.
- Non-blocking, CPU-bound work must explicitly poll `isInterrupted()` at safe points (typically the top of a loop) to notice a requested cancellation at all.
- A method that catches `InterruptedException` internally but doesn't own the overall cancellation decision must restore the interrupt status via `Thread.currentThread().interrupt()` before returning, so the signal isn't lost to code higher up the call stack.
- Never silently swallow `InterruptedException` — always either propagate it or explicitly restore the interrupt flag, preserving the cancellation signal for whoever actually needs to act on it.
