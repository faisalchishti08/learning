---
card: java
gi: 858
slug: volatile-semantics
title: volatile semantics
---

## 1. What it is

The `volatile` keyword, applied to a field, gives two specific guarantees: **visibility** (a write to a `volatile` field is immediately visible to every other thread that subsequently reads it — the [happens-before relationship](0857-happens-before-relationship.md) between volatile writes and reads) and **ordering** (the compiler and CPU are forbidden from reordering other memory operations across a `volatile` read or write, preventing certain classes of instruction-reordering bugs). Critically, `volatile` does **not** provide **atomicity** for compound operations — `volatileInt++` is not one atomic operation; it's a read, an increment, and a write, performed as three separate steps, and two threads can still interleave those steps and lose an update, even though the field is `volatile`.

## 2. Why & when

`volatile` is the right tool specifically for a single field where the only concern is "make sure every thread sees the latest value written" — a status flag signaling "stop now," a reference to an immutable configuration object being hot-swapped, a simple one-directional signal from one thread to another. It is the wrong tool the moment the operation involves reading the current value and computing a new value based on it (increment, compare-and-set, appending to a collection) — those are compound, multi-step operations that need actual atomicity, which `volatile` alone never provides. The frequent, costly mistake is assuming `volatile` makes a counter or accumulator field thread-safe for increments — it makes the *visibility* of whatever value is currently stored reliable, but does nothing to prevent two threads from both reading the same old value and both writing back the same (now-stale) incremented result, silently losing one of the two increments.

## 3. Core concept

```java
volatile boolean shouldStop = false;
// Perfectly fine use: a simple flag, only ever fully overwritten, never read-then-written based on itself.
void requestStop() { shouldStop = true; }
void workLoop() { while (!shouldStop) { /* do work */ } }

volatile int counter = 0;
// BROKEN use: volatile does NOT make ++ atomic.
void increment() { counter++; } // actually: read counter, add 1, write counter -- THREE separate steps
// Two threads calling increment() concurrently CAN still lose an update, despite "volatile".
```

`counter++` compiles to a read, an addition, and a write — `volatile` guarantees each of those three individual memory operations is immediately visible to other threads, but does nothing to make the three-step sequence atomic as a whole, so two threads can interleave between the read and the write and both compute the same "new" value from the same stale "old" value.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two threads both reading the same volatile counter value, both incrementing it locally, and both writing back the same result — losing one of the two increments despite the field being volatile">
  <text x="320" y="20" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">counter starts at 5 (volatile, visible to both threads)</text>

  <g font-family="sans-serif">
    <rect x="40" y="35" width="260" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
    <text x="170" y="60" fill="#e6edf3" font-size="10" text-anchor="middle">Thread A reads counter = 5</text>

    <rect x="340" y="35" width="260" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
    <text x="470" y="60" fill="#e6edf3" font-size="10" text-anchor="middle">Thread B reads counter = 5</text>

    <rect x="40" y="85" width="260" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
    <text x="170" y="110" fill="#e6edf3" font-size="10" text-anchor="middle">Thread A writes counter = 6</text>

    <rect x="340" y="85" width="260" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
    <text x="470" y="110" fill="#e6edf3" font-size="10" text-anchor="middle">Thread B writes counter = 6</text>
  </g>
  <text x="320" y="150" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Final value: 6, not 7 — one increment silently lost, despite "volatile"</text>
</svg>

*Both threads see each other's individual reads/writes correctly (visibility works) — but the read-modify-write sequence itself still races.*

## 5. Runnable example

Scenario: a shutdown-flag pattern combined with a request counter, growing from correct volatile-flag usage, through the classic volatile-doesn't-make-increment-atomic bug made concrete, to the correct fix using `AtomicInteger` alongside the still-correct volatile flag.

### Level 1 — Basic

```java
public class VolatileFlagCorrectUse {
    static volatile boolean shouldStop = false;

    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            long iterations = 0;
            while (!shouldStop) { iterations++; }
            System.out.println("worker stopped after " + iterations + " iterations");
        });

        worker.start();
        Thread.sleep(50);
        shouldStop = true; // guaranteed visible to worker's next read of shouldStop, thanks to volatile
        worker.join();
        System.out.println("main: worker has terminated");
    }
}
```

**How to run:** `java VolatileFlagCorrectUse.java` (JDK 17+).

Expected output shape:
```
worker stopped after 91827364 iterations
main: worker has terminated
```

This is exactly the right use of `volatile`: a single flag, only ever fully overwritten (never read-then-incremented), where visibility of the latest value is the only property actually needed — and `volatile` provides precisely that, reliably.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class VolatileIncrementBug {
    static volatile int counter = 0; // volatile -- but this does NOT make ++ atomic

    public static void main(String[] args) throws InterruptedException {
        int threads = 8;
        int incrementsPerThread = 10_000;

        ExecutorService pool = Executors.newFixedThreadPool(threads);
        for (int t = 0; t < threads; t++) {
            pool.submit(() -> {
                for (int i = 0; i < incrementsPerThread; i++) {
                    counter++; // read, add 1, write -- THREE steps, not one atomic operation
                }
            });
        }
        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);

        int expected = threads * incrementsPerThread;
        System.out.println("expected: " + expected);
        System.out.println("actual (volatile alone does NOT prevent lost updates): " + counter);
    }
}
```

**How to run:** `java VolatileIncrementBug.java`. The actual count will very likely be **less than** `expected`, and the exact shortfall varies by run and machine, since it depends on precisely how the eight threads' read-modify-write sequences happen to interleave.

Expected output shape:
```
expected: 80000
actual (volatile alone does NOT prevent lost updates): 63847
```

The real-world concern added: proving directly that `volatile` alone is insufficient for a counter incremented by multiple threads. Every individual read and write of `counter` is correctly, immediately visible across threads (that part of `volatile`'s contract holds perfectly), but the three-step read-modify-write sequence as a whole is not atomic — two threads can both read the same value before either writes back its incremented result, silently losing one of the two increments, exactly the same lost-update race that would occur with a plain, non-volatile `int`.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class CorrectFlagAndCounter {
    static volatile boolean shouldStop = false; // CORRECT use of volatile: a simple flag
    static AtomicInteger counter = new AtomicInteger(0); // CORRECT tool for atomic increments

    public static void main(String[] args) throws InterruptedException {
        int threads = 8;
        ExecutorService pool = Executors.newFixedThreadPool(threads);

        for (int t = 0; t < threads; t++) {
            pool.submit(() -> {
                while (!shouldStop) { // volatile flag check -- correctly visible across threads
                    counter.incrementAndGet(); // ATOMIC read-modify-write -- no lost updates possible
                }
            });
        }

        Thread.sleep(100);
        shouldStop = true; // signals all 8 threads to stop, correctly and promptly visible to all of them
        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);

        System.out.println("final counter value (every increment correctly counted): " + counter.get());
        System.out.println("-> volatile correctly handles the STOP SIGNAL; AtomicInteger correctly handles the COUNTING");
    }
}
```

**How to run:** `java CorrectFlagAndCounter.java`. The exact final counter value varies by machine speed (since it depends on how many increments happen in the 100ms window), but it is always internally consistent — no lost updates, unlike the buggy version.

Expected output shape:
```
final counter value (every increment correctly counted): 8234156
-> volatile correctly handles the STOP SIGNAL; AtomicInteger correctly handles the COUNTING
```

This adds the production-flavored hard case: correctly combining two different concurrency tools, each for the job it's actually suited to. `shouldStop` remains a simple `volatile boolean` — exactly right, since it's a single flag, only ever fully overwritten, never computed from its own current value. `counter` is upgraded to `AtomicInteger`, whose `incrementAndGet()` performs the entire read-modify-write sequence as one indivisible atomic operation (typically implemented via a hardware compare-and-swap instruction), correctly preventing the lost-update race that plagued the plain `volatile int` version.

## 6. Walkthrough

Tracing `CorrectFlagAndCounter.main`:

1. Eight worker tasks are submitted, each looping `while (!shouldStop) { counter.incrementAndGet(); }`.
2. Every iteration's check of `shouldStop` reads the current value of that `volatile` field — since it's `volatile`, each thread is guaranteed to see the most recently written value, not a stale, thread-local cached copy.
3. `counter.incrementAndGet()` performs its read-modify-write as one atomic hardware-level operation (internally, typically a compare-and-swap loop: read the current value, compute the new value, attempt to atomically swap it in, retrying if another thread's concurrent update won the race in between) — so even with eight threads calling this concurrently and continuously, every single increment is correctly, individually counted, with no possibility of two threads both reading the same value and both writing back the same result.
4. After 100ms, the main thread sets `shouldStop = true`. Because `shouldStop` is `volatile`, this write is guaranteed to become visible to every one of the eight worker threads promptly — each one's next loop-condition check will see `true` and exit its loop.
5. `counter.get()` after all eight threads have stopped and the pool has fully shut down reports the true total number of increments actually performed — a number that varies by run (since it depends on timing), but is always internally correct and consistent, in contrast to the buggy `VolatileIncrementBug` version's undercount.

## 7. Gotchas & takeaways

> **Gotcha:** `volatile` on a numeric field does **not** make `++`, `+=`, or any other compound assignment atomic — these all compile to separate read, compute, and write steps, and `volatile` only guarantees each individual step's visibility, not the atomicity of the sequence as a whole. This is one of the most common `volatile` misunderstandings, since the field genuinely does behave correctly for simple assignment (`flag = true`), which can lead to a false sense that it's equally safe for compound operations.

- `volatile` guarantees visibility (a write is immediately visible to subsequent reads on other threads) and ordering (preventing certain instruction reorderings around the access), but **not** atomicity for compound operations.
- Use `volatile` for simple flags and reference hot-swaps — fields that are only ever fully overwritten, never computed from their own prior value in a way that needs to be atomic.
- Never use `volatile` alone for counters or accumulators updated via `++`, `+=`, or similar compound operations — use [`AtomicInteger`](0830-concurrenthashmap-internals.md)/`AtomicLong`/`AtomicReference` (or explicit synchronization) instead, since those provide genuine atomicity for the full read-modify-write sequence.
- A `volatile` flag and an `Atomic*` counter often work together correctly in the same piece of code, each handling the specific concern it's actually suited for.
- The safest heuristic: if the new value being written depends on reading the field's current value first, `volatile` alone is insufficient — reach for an atomic class or proper synchronization instead.
