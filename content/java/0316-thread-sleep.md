---
card: java
gi: 316
slug: thread-sleep
title: Thread.sleep()
---

## 1. What it is

`Thread.sleep(millis)` pauses the **currently executing thread** for at least the specified number of milliseconds, without consuming CPU while paused, and without giving up any locks it holds. It's a static method — it always affects whichever thread calls it, never some other thread you happen to have a reference to.

```java
public class SleepDemo {
    public static void main(String[] args) throws InterruptedException {
        System.out.println("Before sleep: " + System.currentTimeMillis());
        Thread.sleep(1000); // pause THIS thread for ~1 second
        System.out.println("After sleep: " + System.currentTimeMillis());
    }
}
```

`Thread.sleep(1000)` pauses the main thread (since that's the thread calling it) for approximately one second; the difference between the two printed timestamps will be at least `1000` milliseconds, though it may run slightly longer due to OS scheduling.

## 2. Why & when

Sometimes a thread genuinely needs to pause for a while — waiting for some external condition to likely become true, spacing out repeated actions (polling, retries), or simply simulating a slow operation. `Thread.sleep` is the simplest tool for "stop running for a while, then continue."

- **Polling with a delay** — checking some condition repeatedly without spamming it in a tight loop that wastes CPU.
- **Rate limiting / pacing** — spacing out repeated actions like retries or periodic status updates.
- **Simulating slow operations** — in examples, tests, or demonstrations, standing in for a genuinely slow network call or computation.

`Thread.sleep` declares `throws InterruptedException` — a checked exception thrown if another thread interrupts the sleeping thread before the time elapses — so every call must be wrapped in a `try`/`catch` (or the calling method must itself declare `throws InterruptedException`). Sleeping does **not** release any locks the thread holds, which matters when sleeping inside a `synchronized` block (covered separately): other threads waiting on that same lock remain blocked for the entire sleep duration. For genuine "wait until notified" coordination between threads, `wait`/`notify` (covered separately) is usually more appropriate than sleeping in a loop.

## 3. Core concept

```java
public class SleepCore {
    public static void main(String[] args) throws InterruptedException {
        for (int i = 1; i <= 3; i++) {
            System.out.println("Tick " + i);
            Thread.sleep(500); // pause half a second between ticks
        }
        System.out.println("Done.");
    }
}
```

Each loop iteration prints, then pauses for 500 milliseconds before the next iteration — the three "Tick" lines appear roughly half a second apart, demonstrating `sleep` as a simple pacing mechanism within a single thread's own execution.

## 4. Diagram

<svg viewBox="0 0 600 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A thread alternates between running and sleeping, consuming no CPU while asleep, then resumes where it left off">
  <rect x="8" y="8" width="584" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="40" width="80" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="60" y="60" fill="#e6edf3" font-size="9" text-anchor="middle">running</text>
  <rect x="110" y="40" width="140" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="180" y="60" fill="#8b949e" font-size="9" text-anchor="middle">sleeping (no CPU used)</text>
  <rect x="260" y="40" width="80" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="300" y="60" fill="#e6edf3" font-size="9" text-anchor="middle">running</text>
  <text x="20" y="100" fill="#8b949e" font-size="9">The thread resumes automatically once the sleep duration elapses -- no external action required.</text>
</svg>

Sleeping frees the CPU for other work without terminating the thread — it simply resumes on its own after the timer expires.

## 5. Runnable example

Scenario: a simple retry-with-backoff mechanism for a flaky operation, evolved from a fixed-delay retry into an increasing ("backoff") delay, then into a version that properly handles interruption during the sleep.

### Level 1 — Basic

```java
public class SleepBasic {
    static boolean flakyOperation(int attempt) {
        return attempt >= 3; // succeeds only on the 3rd attempt, for this demo
    }

    public static void main(String[] args) throws InterruptedException {
        int attempt = 1;
        while (!flakyOperation(attempt)) {
            System.out.println("Attempt " + attempt + " failed, retrying...");
            Thread.sleep(500); // fixed delay between retries
            attempt++;
        }
        System.out.println("Succeeded on attempt " + attempt);
    }
}
```

**How to run:** `java SleepBasic.java`

Retries a simulated flaky operation with a fixed 500ms pause between attempts, stopping as soon as it succeeds — the simplest possible retry loop using `sleep` for pacing.

### Level 2 — Intermediate

Same retry loop, now with **exponential backoff**: each failed attempt doubles the wait time, a common real-world pattern for retrying against overloaded services without hammering them.

```java
public class SleepIntermediate {
    static boolean flakyOperation(int attempt) {
        return attempt >= 4;
    }

    public static void main(String[] args) throws InterruptedException {
        int attempt = 1;
        long delay = 200; // starting delay in milliseconds

        while (!flakyOperation(attempt)) {
            System.out.println("Attempt " + attempt + " failed, retrying in " + delay + "ms...");
            Thread.sleep(delay);
            delay *= 2; // exponential backoff
            attempt++;
        }
        System.out.println("Succeeded on attempt " + attempt);
    }
}
```

**How to run:** `java SleepIntermediate.java`

`delay *= 2` after each failed attempt means the pauses grow `200ms -> 400ms -> 800ms`, spacing out retries more and more as failures accumulate — a real technique used to avoid overwhelming a struggling downstream service with rapid, tightly-spaced retries.

### Level 3 — Advanced

Same backoff retry loop, now properly handling the case where the sleeping thread is interrupted mid-wait: catching `InterruptedException`, re-asserting the thread's interrupted status (the correct convention, rather than silently swallowing it), and aborting the retry loop cleanly instead of continuing to retry.

```java
public class SleepAdvanced {
    static boolean flakyOperation(int attempt) {
        return attempt >= 5;
    }

    static boolean retryWithBackoff(int maxAttempts) {
        int attempt = 1;
        long delay = 200;

        while (attempt < maxAttempts && !flakyOperation(attempt)) {
            System.out.println("Attempt " + attempt + " failed, retrying in " + delay + "ms...");
            try {
                Thread.sleep(delay);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt(); // preserve the interrupt signal for callers
                System.out.println("Retry loop interrupted -- aborting.");
                return false;
            }
            delay *= 2;
            attempt++;
        }
        return flakyOperation(attempt);
    }

    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            boolean success = retryWithBackoff(10);
            System.out.println("retryWithBackoff finished, success=" + success);
        });

        worker.start();
        Thread.sleep(300); // let it fail once, then start sleeping for its second retry
        worker.interrupt(); // simulate an external request to cancel the retry loop
        worker.join();
        System.out.println("Main thread done.");
    }
}
```

**How to run:** `java SleepAdvanced.java`

`worker.interrupt()` is called from the main thread while `worker` is sleeping inside `Thread.sleep(delay)` for its second retry — this causes `Thread.sleep` to immediately throw `InterruptedException` inside `worker` rather than waiting out the full delay, and the `catch` block re-asserts the interrupt flag via `Thread.currentThread().interrupt()` (a documented best practice so that any code further up the call stack can still observe that an interrupt occurred) before returning `false` to abandon the retry loop.

## 6. Walkthrough

Trace `SleepAdvanced.main` step by step.

**Starting the worker.** `worker.start()` launches a new thread running `retryWithBackoff(10)`. Inside, `attempt = 1`, `delay = 200`. Since `flakyOperation(1)` is `false` (it only succeeds at attempt 5), the loop body runs: it prints the failure message and calls `Thread.sleep(200)`.

**Main thread's own timing.** Concurrently, the main thread calls `Thread.sleep(300)` — pausing itself (not the worker) for 300ms. During this time, the worker thread's first `Thread.sleep(200)` completes normally (200 < 300), so the worker increments `delay` to `400`, `attempt` to `2`, and — since `flakyOperation(2)` is still `false` — loops again: prints another failure message and calls `Thread.sleep(400)` for its second retry.

**The interrupt.** At the 300ms mark, the main thread's own sleep finishes, and it calls `worker.interrupt()`. At this moment, the worker thread is in the middle of its second `Thread.sleep(400)` call (which started at roughly the 200ms mark and would otherwise finish around 600ms). Calling `interrupt()` on a sleeping thread causes that thread's `Thread.sleep` call to immediately throw `InterruptedException`, rather than waiting for the remaining ~300ms.

**Handling the interruption.** Inside the worker, the `catch (InterruptedException e)` block runs: `Thread.currentThread().interrupt()` re-sets the worker thread's interrupted status (since catching the exception clears it automatically, and re-asserting it is the correct convention for code that can't immediately act on the interrupt itself). It prints the abort message and `retryWithBackoff` returns `false` immediately, skipping any further retry attempts.

**Finishing up.** The worker's lambda receives `success = false` and prints its completion message. `worker.join()` in the main thread waits for the worker to fully finish (which it has, having returned from `retryWithBackoff`), and the final line prints.

```
t=0ms:    worker starts; attempt=1, sleep(200) begins
t=0ms:    main starts sleep(300)
t=200ms:  worker's sleep(200) ends normally -> attempt=2, delay=400, sleep(400) begins
t=300ms:  main's sleep(300) ends -> worker.interrupt() called
t=300ms:  worker's sleep(400) is interrupted early -> InterruptedException thrown
          -> caught, interrupt status restored, retryWithBackoff returns false
```

**Output:**
```
Attempt 1 failed, retrying in 200ms...
Attempt 2 failed, retrying in 400ms...
Retry loop interrupted -- aborting.
retryWithBackoff finished, success=false
Main thread done.
```

## 7. Gotchas & takeaways

> `Thread.sleep` guarantees the thread will sleep for **at least** the requested duration, never exactly that duration — OS scheduling, system load, and JVM garbage collection can all cause it to sleep longer. Code that depends on sleeping for a precise, exact amount of time is relying on a guarantee `sleep` doesn't make.

> Catching `InterruptedException` and doing nothing with it (an empty `catch` block) silently discards a signal that some other part of the program wanted this thread to stop what it's doing — the corrected convention, shown above, is to either handle the interruption meaningfully (as `retryWithBackoff` does, by aborting) or, if the method can't act on it itself, call `Thread.currentThread().interrupt()` to restore the interrupted status so calling code further up the stack can still detect and respond to it.

- `Thread.sleep(millis)` pauses the calling thread (never a different one) for at least the given duration, without consuming CPU or releasing any held locks.
- It declares `throws InterruptedException`, since another thread can interrupt a sleeping thread, causing `sleep` to return early via that exception.
- Never silently swallow `InterruptedException` — either act on it meaningfully or re-assert the interrupt via `Thread.currentThread().interrupt()`.
- Exponential backoff (doubling the delay after each failure) is a common, real-world pattern for spacing out retries against a struggling or overloaded service.
