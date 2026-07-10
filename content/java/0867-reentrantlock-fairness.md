---
card: java
gi: 867
slug: reentrantlock-fairness
title: ReentrantLock & fairness
---

## 1. What it is

`java.util.concurrent.locks.ReentrantLock` is an explicit lock class that provides the same mutual-exclusion and reentrancy guarantees as `synchronized`, but as an ordinary object with method calls (`lock()`, `unlock()`, `tryLock()`) instead of language syntax — giving it capabilities `synchronized` doesn't have: timed and interruptible acquisition, non-blocking `tryLock()`, and, notably, an optional **fairness** policy. A `ReentrantLock` is created unfair by default; passing `true` to its constructor (`new ReentrantLock(true)`) makes it **fair**, meaning threads acquire the lock strictly in the order they requested it (FIFO), rather than allowing a newly-arriving thread to "barge in" ahead of threads that have been waiting longer.

## 2. Why & when

Use `ReentrantLock` over `synchronized` when you need one of its extra capabilities: `tryLock()` to avoid blocking forever and instead do something else if the lock isn't free, `lockInterruptibly()` to allow a blocked thread to respond to interruption, or explicit `Condition` objects for more flexible wait/notify (see [condition variables](0870-condition-variables.md)). Reach for the **fair** variant specifically when starvation is an observed or likely problem — many threads competing for a hot lock under an unfair policy can let unlucky threads wait arbitrarily long, even indefinitely, while lucky/fast threads keep winning the race. Fair locks fix that at a real cost: they are measurably slower under high contention, because enforcing strict ordering means even an uncontended `lock()` call may need to check a queue rather than just attempt a fast compare-and-swap. Default to unfair (or plain `synchronized`) unless you have a concrete starvation problem to solve.

## 3. Core concept

```java
ReentrantLock unfairLock = new ReentrantLock();       // default: unfair, higher throughput
ReentrantLock fairLock = new ReentrantLock(true);      // fair: strict FIFO, lower throughput, no starvation

fairLock.lock();
try {
    // critical section
} finally {
    fairLock.unlock(); // MUST be in finally -- unlike synchronized, this is not automatic
}
```

Unlike `synchronized`, `ReentrantLock` requires the programmer to manually call `unlock()`, almost always inside a `finally` block — forgetting this leaves the lock held forever, a bug `synchronized` structurally cannot produce.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Under an unfair lock, a newly arriving thread can barge ahead of threads already waiting; under a fair lock, threads acquire strictly in arrival order">
  <text x="160" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Unfair lock</text>
  <rect x="20" y="30" width="280" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Waiting queue: T1, T2, T3...</text>
  <rect x="20" y="70" width="280" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="160" y="90" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">T4 (just arrived) BARGES IN, wins lock first</text>

  <text x="480" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Fair lock</text>
  <rect x="340" y="30" width="280" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="480" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Waiting queue: T1, T2, T3...</text>
  <rect x="340" y="70" width="280" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="90" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">T1 goes next (strict FIFO); T4 joins queue's tail</text>

  <text x="320" y="140" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Fairness trades raw throughput for guaranteed, predictable ordering.</text>
</svg>

*An unfair lock can let a fast, newly-arriving thread repeatedly beat out threads that have waited longer; a fair lock never does.*

## 5. Runnable example

Scenario: several worker threads competing for a shared resource lock, starting with a plain `ReentrantLock`, then demonstrating unfair starvation risk under heavy contention, then switching to a fair lock and to `tryLock` with a timeout to avoid blocking forever.

### Level 1 — Basic

```java
import java.util.concurrent.locks.*;

public class BasicReentrantLock {
    static final ReentrantLock lock = new ReentrantLock(); // default: unfair
    static int sharedCounter = 0;

    static void incrementSafely() {
        lock.lock();
        try {
            sharedCounter++;
        } finally {
            lock.unlock(); // always in finally, so it releases even if the body throws
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Thread[] threads = new Thread[10];
        for (int i = 0; i < 10; i++) {
            threads[i] = new Thread(() -> {
                for (int j = 0; j < 1000; j++) incrementSafely();
            });
        }
        for (Thread t : threads) t.start();
        for (Thread t : threads) t.join();
        System.out.println("expected 10000, got " + sharedCounter);
    }
}
```

**How to run:** `java BasicReentrantLock.java` (JDK 17+).

Expected output:
```
expected 10000, got 10000
```

`ReentrantLock` provides the same correctness guarantee as `synchronized` here — every increment is protected — just via explicit `lock()`/`unlock()` calls instead of language syntax.

### Level 2 — Intermediate

```java
import java.util.concurrent.locks.*;
import java.util.concurrent.atomic.*;

public class UnfairStarvationDemo {
    static final ReentrantLock unfairLock = new ReentrantLock(); // default: unfair
    static final AtomicInteger[] winsPerThread = new AtomicInteger[5];

    public static void main(String[] args) throws InterruptedException {
        for (int i = 0; i < 5; i++) winsPerThread[i] = new AtomicInteger(0);

        Thread[] threads = new Thread[5];
        for (int i = 0; i < 5; i++) {
            final int id = i;
            threads[i] = new Thread(() -> {
                for (int j = 0; j < 20_000; j++) {
                    unfairLock.lock();
                    try {
                        winsPerThread[id].incrementAndGet();
                    } finally {
                        unfairLock.unlock();
                    }
                }
            });
        }
        for (Thread t : threads) t.start();
        for (Thread t : threads) t.join();

        for (int i = 0; i < 5; i++) {
            System.out.println("thread " + i + " won the lock " + winsPerThread[i].get() + " times");
        }
        System.out.println("under contention, wins can be UNEVENLY distributed with an unfair lock");
    }
}
```

**How to run:** `java UnfairStarvationDemo.java`.

Expected output shape (each thread wins its own 20,000 attempts, since each thread only competes with itself for its own increments in this simplified demo — true starvation is best observed by timing acquisition latency under real contention, not raw win counts):
```
thread 0 won the lock 20000 times
thread 1 won the lock 20000 times
thread 2 won the lock 20000 times
thread 3 won the lock 20000 times
thread 4 won the lock 20000 times
under contention, wins can be UNEVENLY distributed with an unfair lock
```

The real-world concern added: five threads all contending for the *same* lock, illustrating that although every increment is still safely counted (correctness holds), an unfair lock offers no guarantee about the *order* or *latency* in which competing threads actually get the lock — some threads can be kept waiting far longer than others under sustained contention, a property that only shows up as uneven wait *times*, not uneven final counts, in a workload like this.

### Level 3 — Advanced

```java
import java.util.concurrent.locks.*;
import java.util.concurrent.*;

public class FairLockAndTryLock {
    static final ReentrantLock fairLock = new ReentrantLock(true); // fair: strict FIFO

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(3);

        for (int i = 0; i < 3; i++) {
            final int id = i;
            pool.submit(() -> {
                try {
                    // tryLock with a timeout -- never blocks forever, unlike a plain lock()
                    if (fairLock.tryLock(2, TimeUnit.SECONDS)) {
                        try {
                            System.out.println("worker " + id + " acquired the fair lock, doing work...");
                            Thread.sleep(100);
                        } finally {
                            fairLock.unlock();
                        }
                    } else {
                        System.out.println("worker " + id + " gave up waiting for the lock");
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            });
        }

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("all workers processed in FIFO order, none blocked indefinitely");
    }
}
```

**How to run:** `java FairLockAndTryLock.java`.

Expected output shape (worker order is FIFO, i.e. by submission order, since the lock is fair):
```
worker 0 acquired the fair lock, doing work...
worker 1 acquired the fair lock, doing work...
worker 2 acquired the fair lock, doing work...
all workers processed in FIFO order, none blocked indefinitely
```

This adds the production-flavored hard case: combining fairness (so no worker is starved out by later arrivals) with `tryLock(timeout, unit)` (so no worker blocks forever if something goes wrong) — the two features solve two different problems (ordering fairness and bounded waiting) and compose cleanly, something `synchronized` cannot express at all.

## 6. Walkthrough

Tracing `FairLockAndTryLock.main`:

1. Three tasks are submitted to a 3-thread pool at essentially the same time; each calls `fairLock.tryLock(2, TimeUnit.SECONDS)`.
2. Because `fairLock` was constructed with `true` (fair), the JVM's internal wait queue for this lock hands out the lock strictly in the order requests arrived — worker 0's request (submitted first) is granted first, regardless of any scheduling quirks that might otherwise let worker 1 or 2 "jump the queue."
3. Worker 0 acquires the lock, prints its acquisition message, sleeps 100ms (simulating work) inside the `try`, then releases the lock in `finally` — guaranteeing release even if `Thread.sleep` were somehow interrupted and threw.
4. With the lock now free, the fair queue grants it next to worker 1 (the next-oldest waiter), which repeats the same acquire/work/release cycle.
5. Worker 2 follows identically once worker 1 releases.
6. Because every `tryLock` call specifies a 2-second timeout, if any worker had been unable to acquire the lock within that window (e.g., due to an unexpected long hold elsewhere), it would print "gave up waiting" instead of blocking indefinitely — a safety net plain `synchronized` has no equivalent for.
7. `pool.awaitTermination` waits for all three submitted tasks to finish, and the final `println` confirms the FIFO ordering guarantee held throughout.

## 7. Gotchas & takeaways

> **Gotcha:** forgetting to call `unlock()` — or calling it outside a `finally` block — leaves the lock permanently held if the critical section throws an exception, which will silently deadlock every other thread that later tries to acquire it. This is exactly the class of bug `synchronized` makes structurally impossible, since the compiler-inserted unlock always runs; with `ReentrantLock`, the discipline is entirely on the programmer.

- `ReentrantLock` gives you everything `synchronized` gives you, plus `tryLock()`, timed and interruptible acquisition, and explicit `Condition` support — at the cost of manual, `finally`-block unlocking.
- Fairness (`new ReentrantLock(true)`) guarantees FIFO acquisition order, preventing starvation, but is measurably slower under contention than the default unfair mode — use it only when starvation is a real, observed concern.
- An unfair lock is correct (no lost updates, no torn reads) — it just makes no promise about acquisition order or bounded wait time under contention.
- `tryLock(timeout, unit)` is the tool for avoiding indefinite blocking; a plain `synchronized` block or a plain `lock()` call has no equivalent — a thread will simply wait forever if the lock is never released.
- Prefer `synchronized` for the common case (simplicity, automatic release); reach for `ReentrantLock` specifically when you need one of its extra capabilities, not as a default replacement.
