---
card: java
gi: 313
slug: thread-class
title: Thread class
---

## 1. What it is

`Thread` is Java's built-in class representing a single thread of execution — a separate path of instructions that runs concurrently with other threads in the same program. Every Java program already has at least one thread (the "main" thread, which runs your `main` method); `Thread` lets you create additional ones.

```java
public class ThreadDemo {
    public static void main(String[] args) {
        Thread worker = new Thread(() -> {
            System.out.println("Running in: " + Thread.currentThread().getName());
        });
        worker.start();

        System.out.println("Running in: " + Thread.currentThread().getName());
    }
}
```

`new Thread(() -> {...})` creates a new thread with the given code as its task; `start()` actually begins running it concurrently with the rest of the program; `Thread.currentThread().getName()` reports which thread is executing the line that calls it — the main thread and the worker thread each report their own distinct name.

## 2. Why & when

A single thread of execution runs one instruction at a time, in order — if a program needs to do multiple things "at once" (respond to user input while downloading a file, process several independent tasks in parallel to use multiple CPU cores), a single thread can't do that; multiple threads can.

- **Parallelism** — splitting independent work (processing chunks of a large dataset, handling multiple network requests) across threads lets a multi-core CPU actually do more than one thing simultaneously.
- **Responsiveness** — a long-running operation (a network call, a large computation) run on a separate thread doesn't block the main thread from continuing other work, such as keeping a user interface responsive.
- **Modeling independent activities** — some programs naturally have multiple independent, ongoing activities (a game's rendering loop and its background asset loader) that map cleanly onto separate threads.

Use `Thread` directly for simple, one-off concurrent tasks or to understand the fundamentals; for anything beyond a handful of threads or any real production workload, prefer the higher-level `java.util.concurrent` utilities (`ExecutorService`, thread pools) covered elsewhere, which manage thread lifecycle, reuse, and scheduling far more efficiently and safely than manually creating `Thread` objects one at a time.

## 3. Core concept

```java
public class ThreadCore {
    public static void main(String[] args) throws InterruptedException {
        Thread t1 = new Thread(() -> System.out.println("Thread A: " + Thread.currentThread().getName()));
        Thread t2 = new Thread(() -> System.out.println("Thread B: " + Thread.currentThread().getName()));

        t1.start();
        t2.start();

        t1.join(); // wait for t1 to finish before continuing
        t2.join(); // wait for t2 to finish before continuing
        System.out.println("Both threads finished.");
    }
}
```

`start()` returns almost immediately — it doesn't wait for the thread's task to complete — so `t1.start()` and `t2.start()` both fire off quickly, and the two threads' `println` output can appear in either order (or even interleaved) since they run concurrently; `join()` is what actually pauses the calling thread until the target thread finishes.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The main thread continues running immediately after starting two worker threads which execute concurrently">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#8b949e" font-size="10" font-family="monospace">main thread:  ----start(t1)----start(t2)----join(t1)====join(t2)====done</text>
  <text x="20" y="70" fill="#6db33f" font-size="10" font-family="monospace">t1:                  |----running work------|</text>
  <text x="20" y="95" fill="#79c0ff" font-size="10" font-family="monospace">t2:                       |----running work-----------|</text>
  <text x="20" y="130" fill="#8b949e" font-size="9">main continues immediately after start(); join() blocks until that specific thread finishes.</text>
</svg>

Threads run concurrently once started; `join()` is the explicit synchronization point where one thread waits for another.

## 5. Runnable example

Scenario: a small parallel sum calculator, evolved from a basic single-thread demonstration into splitting work across multiple threads, then into correctly aggregating each thread's partial result using `join` and shared state.

### Level 1 — Basic

```java
public class ThreadBasic {
    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            long sum = 0;
            for (int i = 1; i <= 1_000_000; i++) sum += i;
            System.out.println("Worker computed: " + sum);
        });

        worker.start();
        worker.join(); // wait for the worker to finish before the program ends
        System.out.println("Main thread continues after worker is done.");
    }
}
```

**How to run:** `java ThreadBasic.java`

A single worker thread computes a sum independently while the main thread waits for it via `join()` — the simplest possible demonstration of offloading work to another thread.

### Level 2 — Intermediate

Same summing task, now split across four threads, each summing a different quarter of the range — demonstrating genuine parallel work, though each thread's partial result is only printed individually so far, not yet combined.

```java
public class ThreadIntermediate {
    static long sumRange(int start, int end) {
        long sum = 0;
        for (int i = start; i <= end; i++) sum += i;
        return sum;
    }

    public static void main(String[] args) throws InterruptedException {
        int total = 1_000_000;
        int quarter = total / 4;

        Thread[] threads = new Thread[4];
        for (int i = 0; i < 4; i++) {
            int start = i * quarter + 1;
            int end = (i == 3) ? total : (i + 1) * quarter;
            threads[i] = new Thread(() -> {
                long partial = sumRange(start, end);
                System.out.println("Thread " + Thread.currentThread().getName() + " summed [" + start + ", " + end + "] = " + partial);
            });
            threads[i].start();
        }

        for (Thread t : threads) t.join();
        System.out.println("All four threads finished.");
    }
}
```

**How to run:** `java ThreadIntermediate.java`

Four threads each sum a distinct quarter of the range `[1, 1000000]` independently and concurrently; the final `for (Thread t : threads) t.join()` loop waits for every one of them before the program reports completion — each thread's individual print may appear in any order across runs, since their exact timing isn't controlled.

### Level 3 — Advanced

Same parallel sum, now correctly combining each thread's partial result into a single final total, using an array to safely collect results from multiple threads without a race condition (each thread writes to its own distinct array slot, so there's no shared-write conflict).

```java
public class ThreadAdvanced {
    static long sumRange(int start, int end) {
        long sum = 0;
        for (int i = start; i <= end; i++) sum += i;
        return sum;
    }

    public static void main(String[] args) throws InterruptedException {
        int total = 1_000_000;
        int threadCount = 4;
        int chunk = total / threadCount;

        Thread[] threads = new Thread[threadCount];
        long[] partialSums = new long[threadCount]; // each thread writes to its OWN index -- no race

        for (int i = 0; i < threadCount; i++) {
            int index = i;
            int start = i * chunk + 1;
            int end = (i == threadCount - 1) ? total : (i + 1) * chunk;
            threads[i] = new Thread(() -> {
                partialSums[index] = sumRange(start, end);
            });
            threads[i].start();
        }

        for (Thread t : threads) t.join(); // MUST wait for all threads before reading partialSums

        long finalTotal = 0;
        for (long partial : partialSums) finalTotal += partial;

        System.out.println("Parallel total: " + finalTotal);
        System.out.println("Expected total: " + ((long) total * (total + 1) / 2));
    }
}
```

**How to run:** `java ThreadAdvanced.java`

Each thread writes exclusively to `partialSums[index]`, a distinct array slot assigned before the thread starts — since no two threads ever write to the same slot, there's no need for synchronization on the writes themselves; the critical correctness requirement is that **all** `join()` calls complete before the main thread reads `partialSums` to compute `finalTotal`, ensuring every write has actually happened and is visible.

## 6. Walkthrough

Trace `ThreadAdvanced.main` step by step.

**Setup.** `total = 1_000_000`, `threadCount = 4`, `chunk = 250_000`. `partialSums` is a `long[4]`, initially all zeros.

**Thread creation loop.** For `i = 0`: `index = 0`, `start = 1`, `end = 250_000`. A `Thread` is created whose task computes `sumRange(1, 250_000)` and stores it in `partialSums[0]`. `threads[0].start()` launches it — execution of that sum begins concurrently with the rest of `main` continuing. The same pattern repeats for `i = 1, 2, 3`, with `start`/`end` covering `[250001, 500000]`, `[500001, 750000]`, and `[750001, 1000000]` respectively, and `index` values `1, 2, 3` ensuring each thread targets a distinct array slot.

**Concurrent execution.** All four threads now run `sumRange` on their respective ranges, potentially on different CPU cores, genuinely in parallel. Each thread's final act is writing its computed sum into its own reserved slot in `partialSums` — since slots are distinct, there's no possibility of two threads overwriting each other's result.

**The `join` loop.** `for (Thread t : threads) t.join()` iterates over all four threads and waits for each one, in turn, to finish completely before proceeding to the next iteration. After this loop completes, it is guaranteed that all four `partialSums` writes have happened and are visible to the main thread — this guarantee (about visibility, not just ordering) is part of `join()`'s documented contract.

**Aggregation.** The `for (long partial : partialSums)` loop sums all four slots into `finalTotal` — since the `join` loop already guaranteed all writes are complete and visible, this read is safe and will see each thread's correct, final value, not a stale or partial one.

**Verification.** `finalTotal` is compared against the closed-form sum formula `total * (total + 1) / 2` for verification — both should print the identical value, `500000500000`.

```
Thread 0: sumRange(1, 250000)        -> partialSums[0]
Thread 1: sumRange(250001, 500000)   -> partialSums[1]
Thread 2: sumRange(500001, 750000)   -> partialSums[2]
Thread 3: sumRange(750001, 1000000)  -> partialSums[3]

all join() -> guaranteed all 4 writes visible

finalTotal = partialSums[0]+[1]+[2]+[3] = 500000500000
```

**Output:**
```
Parallel total: 500000500000
Expected total: 500000500000
```

## 7. Gotchas & takeaways

> `start()` returns almost immediately, without waiting for the thread's task to run to completion — reading a value a thread is supposed to compute immediately after calling `start()` (without a corresponding `join()`) is a race condition that will very likely read a stale or default value, since the thread's work probably hasn't finished (or even begun) yet.

> Multiple threads writing to **different** elements of the same array (as in this example) requires no synchronization — but multiple threads writing to the **same** shared variable or the same array element does, and doing so without synchronization is a genuine data race with undefined, unpredictable results. The safety here comes specifically from each thread owning a distinct slot, not from arrays being inherently thread-safe.

- `Thread` represents an independent path of execution; `new Thread(task)` creates one, `start()` begins running it concurrently, and `join()` waits for it to finish.
- `start()` does not block — code after it continues immediately, running concurrently with the new thread.
- Multiple threads can safely write to distinct locations (like separate array slots) without synchronization; shared, overlapping writes require explicit coordination.
- For anything beyond simple, small-scale concurrency, prefer `java.util.concurrent`'s `ExecutorService` and thread pools over manually managing individual `Thread` objects.
