---
card: java
gi: 452
slug: fork-join-framework-forkjoinpool
title: Fork/Join framework (ForkJoinPool)
---

## 1. What it is

`ForkJoinPool`, added in Java 7, is a specialized `ExecutorService` implementation built around **work-stealing**: each worker thread maintains its own queue of tasks, and whenever a worker's queue runs empty, it "steals" a task from another (busy) worker's queue rather than sitting idle. Every JVM has a shared, ready-to-use instance available via `ForkJoinPool.commonPool()`, used implicitly by parallel streams and `CompletableFuture`; you can also construct your own with a chosen level of parallelism, `new ForkJoinPool(parallelism)`.

## 2. Why & when

A regular `ThreadPoolExecutor` distributes tasks from one shared queue — fine for independent, unrelated tasks, but a poor fit for **recursive, divide-and-conquer** workloads, where one large task splits into many smaller subtasks that themselves might split further. If every subtask were submitted to one shared queue, the coordination overhead and contention on that single queue would dominate for workloads with many small pieces. `ForkJoinPool`'s work-stealing design instead lets each worker cheaply manage its *own* queue of subtasks (usually the ones it just split off), only reaching across to steal from another worker when it has genuinely run out of its own work — dramatically reducing contention for exactly this recursive-splitting pattern.

You reach for `ForkJoinPool` any time you're doing (or the JVM is implicitly doing on your behalf) recursive, divide-and-conquer parallel work — parallel streams (`list.parallelStream()`), `CompletableFuture`'s async operations, or your own `RecursiveTask`/`RecursiveAction` computations (covered in the next tutorial) all run on a `ForkJoinPool`, typically the shared common pool, unless you specify otherwise.

## 3. Core concept

```java
import java.util.concurrent.*;

ForkJoinPool commonPool = ForkJoinPool.commonPool(); // shared, JVM-wide, ready to use
System.out.println(commonPool.getParallelism());     // typically (available processors - 1)

ForkJoinTask<Integer> task = commonPool.submit(() -> 21 * 2); // ordinary Callable works fine too
int result = task.get(); // 42

ForkJoinPool customPool = new ForkJoinPool(4); // your own pool, 4 worker threads
// ... use it ...
customPool.shutdown();
```

`ForkJoinPool` implements `ExecutorService`, so ordinary `submit`, `invoke`, and `Future`-based patterns all work exactly as with any other executor — its distinguishing feature, work-stealing, operates transparently underneath, most visibly benefiting genuinely recursive workloads.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each ForkJoinPool worker thread has its own task queue; when a worker's queue is empty, it steals a task from another worker's queue instead of sitting idle">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="150" height="60" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="105" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Worker A</text><text x="105" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">queue: [T1, T2, T3]</text>

  <rect x="240" y="30" width="150" height="60" rx="6" fill="#1c2430" stroke="#f85149"/><text x="315" y="50" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Worker B</text><text x="315" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">queue: [] (empty, idle)</text>

  <line x1="180" y1="60" x2="235" y2="60" stroke="#f85149" stroke-dasharray="4,3" marker-end="url(afj1)"/>
  <text x="207" y="50" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">steals T3</text>

  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Idle workers stay productive by stealing work, instead of waiting for a shared queue.</text>
  <defs><marker id="afj1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker></defs>
</svg>

An idle worker reaches into a busy worker's queue rather than waiting on one shared, contended queue.

## 5. Runnable example

Scenario: submitting independent units of work to a `ForkJoinPool` — the same pool, evolved from a single basic task on the shared common pool, through observing multiple tasks distributed across several worker threads, to a custom-sized pool whose limited parallelism becomes observable through timing.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class ForkJoinPoolBasic {
    public static void main(String[] args) throws Exception {
        ForkJoinPool pool = ForkJoinPool.commonPool();
        System.out.println("Common pool parallelism: " + pool.getParallelism());

        ForkJoinTask<Integer> task = pool.submit(() -> {
            System.out.println("Running on: " + Thread.currentThread().getName());
            return 21 * 2;
        });

        Integer result = task.get();
        System.out.println("Result: " + result);
    }
}
```

**How to run:** `java ForkJoinPoolBasic.java`

`ForkJoinPool.commonPool()` is a shared, JVM-wide pool that's always available with no setup — `pool.submit(...)` accepts an ordinary lambda (implementing `Callable`), runs it on one of the pool's worker threads, and `task.get()` blocks for the result exactly like a regular `ExecutorService`'s `Future`. (The exact `getParallelism()` value and worker thread name depend on the machine's available processors.)

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.*;

public class ForkJoinPoolWorkStealing {
    public static void main(String[] args) throws Exception {
        ForkJoinPool pool = new ForkJoinPool(4); // fixed 4 worker threads, for a predictable demo

        List<ForkJoinTask<String>> tasks = new ArrayList<>();
        for (int i = 1; i <= 8; i++) {
            int taskId = i;
            tasks.add(pool.submit(() -> {
                try { Thread.sleep(50); } catch (InterruptedException ignored) { }
                return "Task " + taskId + " on " + Thread.currentThread().getName();
            }));
        }

        Set<String> threadsUsed = new TreeSet<>();
        for (ForkJoinTask<String> task : tasks) {
            String result = task.get();
            System.out.println(result);
            threadsUsed.add(result.substring(result.indexOf(" on ") + 4));
        }

        System.out.println("Distinct worker threads used: " + threadsUsed.size());
        pool.shutdown();
    }
}
```

**How to run:** `java ForkJoinPoolWorkStealing.java`

With 8 independent tasks and only 4 workers, each worker handles roughly 2 tasks — exactly which task lands on which worker isn't guaranteed or deterministic (it depends on submission timing and work-stealing), but the pool as a whole consistently uses all 4 of its configured worker threads to get through the batch.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class ForkJoinPoolCustomSize {
    public static void main(String[] args) throws Exception {
        ForkJoinPool pool = new ForkJoinPool(2); // deliberately small, to make queuing observable

        System.out.println("Configured parallelism: " + pool.getParallelism());

        long start = System.currentTimeMillis();
        ForkJoinTask<?>[] tasks = new ForkJoinTask<?>[4];
        for (int i = 0; i < 4; i++) {
            int id = i;
            tasks[i] = pool.submit(() -> {
                try { Thread.sleep(100); } catch (InterruptedException ignored) { }
                return id;
            });
        }
        for (ForkJoinTask<?> task : tasks) task.join();
        long elapsed = System.currentTimeMillis() - start;

        // With only 2 workers processing 4 tasks of 100ms each, total time should be roughly 2 batches (~200ms),
        // not 4 batches (~400ms) and not all-at-once (~100ms) -- confirming real, bounded parallelism.
        System.out.println("All 4 tasks completed in ~" + (elapsed / 100 * 100) + "ms (2 workers, 2 batches expected)");

        pool.shutdown();
        boolean terminated = pool.awaitTermination(2, TimeUnit.SECONDS);
        System.out.println("Pool terminated cleanly: " + terminated);
    }
}
```

**How to run:** `java ForkJoinPoolCustomSize.java`

With exactly 2 worker threads processing 4 tasks that each take 100ms, the total elapsed time lands around 200ms — two batches of two, rather than all four running simultaneously (~100ms) or entirely sequentially (~400ms) — direct, observable evidence that the pool's configured parallelism genuinely bounds how much work runs concurrently.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `pool` is constructed with parallelism `2`, so it maintains exactly 2 worker threads. `pool.getParallelism()` confirms this, printing `"Configured parallelism: 2"`.

`start` records the current time. The `for` loop submits 4 tasks, each of which sleeps 100ms and returns its own `id`. Since the pool has only 2 workers, at most 2 of these tasks can actually be *running* at any given moment — the other 2 wait in a worker's queue until a worker frees up.

The `for (ForkJoinTask<?> task : tasks) task.join()` loop blocks until all 4 tasks finish. Because the pool can only run 2 tasks at a time, the 4 tasks effectively complete in two "batches": the first 2 tasks run concurrently for about 100ms, then (once a worker is free) the remaining 2 tasks run for another ~100ms — bringing the total elapsed time to roughly 200ms, not the ~100ms it would take if all 4 ran fully in parallel, and not the ~400ms it would take if they ran one at a time.

`elapsed` is computed, then rounded down to the nearest 100ms increment (`elapsed / 100 * 100`) purely to keep the printed output stable despite small timing variance — the underlying behavior (two roughly-100ms batches) is what's being demonstrated, not a precise millisecond figure.

`pool.shutdown()` signals the pool to accept no further tasks; `pool.awaitTermination(2, TimeUnit.SECONDS)` waits for its (already-finished) worker threads to fully terminate, returning `true` since this happens well within the 2-second budget.

Expected output:
```
Configured parallelism: 2
All 4 tasks completed in ~200ms (2 workers, 2 batches expected)
Pool terminated cleanly: true
```

## 7. Gotchas & takeaways

> The shared `ForkJoinPool.commonPool()` is used **implicitly** by parallel streams, `CompletableFuture`'s async methods, and any code you write against the common pool directly. If your application submits a long-running or blocking task to the common pool, it can starve unrelated parallel streams or `CompletableFuture` chains elsewhere in the *same JVM process* that also happen to rely on that same shared pool. For long-running or blocking work, use a dedicated custom `ForkJoinPool` (or a regular `ExecutorService`) instead of the common pool.

- `ForkJoinPool` is built around work-stealing: each worker thread manages its own task queue, and idle workers steal from busy ones rather than contending on one shared queue.
- `ForkJoinPool.commonPool()` is a shared, ready-to-use, JVM-wide pool, typically sized to (available processors − 1); it's what parallel streams and `CompletableFuture` use implicitly unless told otherwise.
- Constructing your own pool with `new ForkJoinPool(parallelism)` gives explicit control over how many worker threads are used, useful when you need predictable, bounded concurrency or isolation from the shared common pool.
- `ForkJoinPool` implements the ordinary `ExecutorService` interface, so `submit`, `Future`-based result retrieval, and `shutdown`/`awaitTermination` all work exactly as with any other executor.
- Work-stealing's benefits are most pronounced for genuinely recursive, divide-and-conquer workloads (covered via `RecursiveTask`/`RecursiveAction` in the next tutorial) — for simple, unrelated independent tasks like the ones shown here, an ordinary `ThreadPoolExecutor` would behave similarly.
