---
card: java
gi: 885
slug: common-pool
title: Common pool
---

## 1. What it is

`ForkJoinPool.commonPool()` is a single, static, JVM-wide `ForkJoinPool` instance, lazily created the first time it's needed and shared by every piece of code in the process that doesn't explicitly specify its own pool. By default, its parallelism level is `Runtime.getRuntime().availableProcessors() - 1` (reserving one implicit slot, roughly, for the calling thread's own participation). Three major Java facilities use it implicitly unless told otherwise: parallel streams (`.parallelStream()`), `CompletableFuture`'s `*Async` methods called *without* an explicit `Executor` argument, and any `RecursiveTask`/`RecursiveAction` submitted via the static convenience methods rather than an explicitly created `ForkJoinPool`.

## 2. Why & when

The common pool exists so unrelated pieces of code across a large application (or even across independent libraries) can share one modestly-sized, pre-warmed thread pool for CPU-bound, forkable work, instead of each needing to create and manage its own — avoiding a proliferation of separate pools all competing for the same limited CPU cores. This works well for genuinely short, CPU-bound, non-blocking tasks — exactly what parallel streams and typical fork/join computations are designed for. It becomes a real production hazard the moment *any* code submits a long-running or blocking task to the common pool without realizing it — a `CompletableFuture.supplyAsync(() -> blockingCall())` with no explicit executor, for instance — because that task occupies one of the common pool's few worker threads for its entire blocking duration, and since the pool is shared, this can silently degrade the performance of completely unrelated code elsewhere in the same JVM that also happens to rely on the common pool, including parallel streams running in other, unrelated parts of the same application.

## 3. Core concept

```java
// All of these implicitly use ForkJoinPool.commonPool():
list.parallelStream().map(this::transform).toList();
CompletableFuture.supplyAsync(() -> compute()); // no executor argument -- common pool
new MaxTask(data, 0, data.length).fork();        // static ForkJoinTask methods -- common pool

int commonPoolParallelism = ForkJoinPool.commonPool().getParallelism(); // typically cores - 1
```

Anything that *doesn't* explicitly pass its own `Executor`/`ForkJoinPool` is implicitly sharing this one JVM-wide resource with everything else that also doesn't.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple unrelated features -- parallel stream, CompletableFuture without an executor, and a fork/join task -- all implicitly sharing the same JVM-wide common pool; one blocking task starves the others">
  <rect x="20" y="20" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="43" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">parallelStream()</text>

  <rect x="20" y="65" width="150" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="95" y="88" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">supplyAsync (no executor)</text>

  <rect x="20" y="110" width="150" height="35" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="95" y="133" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">a BLOCKING async task</text>

  <rect x="280" y="60" width="180" height="70" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="370" y="90" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">ForkJoinPool.commonPool()</text>
  <text x="370" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">shared, JVM-wide, few threads</text>

  <line x1="170" y1="37" x2="278" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a20)"/>
  <line x1="170" y1="82" x2="278" y2="90" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a20)"/>
  <line x1="170" y1="127" x2="278" y2="105" stroke="#f85149" stroke-width="2" marker-end="url(#a20)"/>

  <text x="480" y="160" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">A blocking task occupies a worker for its whole duration --</text>
  <text x="480" y="175" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">starving unrelated parallel streams and futures elsewhere.</text>
  <defs><marker id="a20" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Three unrelated features share one small, JVM-wide pool by default — a single blocking task can degrade all of them.*

## 5. Runnable example

Scenario: measuring the impact of a blocking task on unrelated parallel-stream work, growing from a baseline showing normal common-pool performance, to demonstrating degradation when a blocking task occupies the common pool, to fixing it with a dedicated executor for the blocking work.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class CommonPoolBaseline {
    public static void main(String[] args) {
        List<Integer> numbers = IntStream.rangeClosed(1, 20_000_000).boxed().toList();

        long start = System.currentTimeMillis();
        long sum = numbers.parallelStream().mapToLong(Integer::longValue).sum(); // uses the common pool
        long elapsed = System.currentTimeMillis() - start;

        System.out.println("sum = " + sum);
        System.out.println("common pool parallelism: " + java.util.concurrent.ForkJoinPool.commonPool().getParallelism());
        System.out.println("baseline elapsed ~" + elapsed + "ms (no contention on the common pool)");
    }
}
```

**How to run:** `java CommonPoolBaseline.java` (JDK 17+).

Expected output shape (elapsed time is machine-dependent, establishing a baseline to compare against):
```
sum = 200000010000000
common pool parallelism: 7
baseline elapsed ~60ms (no contention on the common pool)
```

This measures how fast a genuinely CPU-bound parallel stream runs when the common pool is otherwise idle — the number to compare the next two levels against.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

public class BlockingTaskStarvesCommonPool {
    public static void main(String[] args) throws InterruptedException {
        List<Integer> numbers = IntStream.rangeClosed(1, 20_000_000).boxed().toList();
        int parallelism = ForkJoinPool.commonPool().getParallelism();

        // Occupy MOST of the common pool's worker threads with long BLOCKING calls,
        // submitted with no explicit executor -- so they run ON the common pool.
        List<CompletableFuture<Void>> blockers = new ArrayList<>();
        for (int i = 0; i < parallelism - 1; i++) {
            blockers.add(CompletableFuture.runAsync(() -> {
                try { Thread.sleep(500); } catch (InterruptedException ignored) {} // BLOCKING, on a shared worker
            }));
        }
        Thread.sleep(50); // let the blockers actually start and occupy their threads

        long start = System.currentTimeMillis();
        long sum = numbers.parallelStream().mapToLong(Integer::longValue).sum(); // starved of workers now
        long elapsed = System.currentTimeMillis() - start;

        System.out.println("sum = " + sum);
        System.out.println("elapsed WHILE common pool is starved ~" + elapsed + "ms (likely much slower than baseline)");

        CompletableFuture.allOf(blockers.toArray(new CompletableFuture[0])).join();
    }
}
```

**How to run:** `java BlockingTaskStarvesCommonPool.java`.

Expected output shape (elapsed noticeably higher than the Level 1 baseline, since most common-pool workers are tied up sleeping):
```
sum = 200000010000000
elapsed WHILE common pool is starved ~350ms (likely much slower than baseline)
```

The real-world concern added: several unrelated `CompletableFuture.runAsync` calls — submitted with **no explicit executor**, so they land on the shared common pool — each block for 500ms. While they're sleeping, the parallel stream's summation has far fewer common-pool workers actually available to help, so it takes noticeably longer than the Level 1 baseline, even though the summation logic itself hasn't changed at all — purely a symptom of unrelated code silently starving a shared resource.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

public class DedicatedExecutorFixesStarvation {
    public static void main(String[] args) throws InterruptedException {
        List<Integer> numbers = IntStream.rangeClosed(1, 20_000_000).boxed().toList();
        int parallelism = ForkJoinPool.commonPool().getParallelism();

        // FIX: run the blocking tasks on a SEPARATE, dedicated executor --
        // they no longer compete with the common pool for worker threads at all.
        ExecutorService blockingPool = Executors.newFixedThreadPool(parallelism);

        List<CompletableFuture<Void>> blockers = new ArrayList<>();
        for (int i = 0; i < parallelism - 1; i++) {
            blockers.add(CompletableFuture.runAsync(() -> {
                try { Thread.sleep(500); } catch (InterruptedException ignored) {}
            }, blockingPool)); // <-- explicit executor, NOT the common pool
        }
        Thread.sleep(50);

        long start = System.currentTimeMillis();
        long sum = numbers.parallelStream().mapToLong(Integer::longValue).sum(); // common pool is FREE
        long elapsed = System.currentTimeMillis() - start;

        System.out.println("sum = " + sum);
        System.out.println("elapsed with a DEDICATED executor for blocking work ~" + elapsed + "ms (back to baseline speed)");

        CompletableFuture.allOf(blockers.toArray(new CompletableFuture[0])).join();
        blockingPool.shutdown();
        blockingPool.awaitTermination(5, TimeUnit.SECONDS);
    }
}
```

**How to run:** `java DedicatedExecutorFixesStarvation.java`.

Expected output shape (elapsed time back near the Level 1 baseline, despite the same blocking work happening concurrently):
```
sum = 200000010000000
elapsed with a DEDICATED executor for blocking work ~62ms (back to baseline speed)
```

This adds the production-flavored hard case: the exact same blocking workload as Level 2, but submitted to an explicitly created `blockingPool` instead of relying on the default common pool — because `runAsync(..., blockingPool)` passes an explicit `Executor`, none of it competes with the common pool's workers at all. The parallel stream summation runs on a fully available common pool and returns to roughly its Level 1 baseline speed, even though the same amount of "unrelated blocking work" is happening concurrently in the background.

## 6. Walkthrough

Contrasting Level 2 and Level 3's behavior:

1. In `BlockingTaskStarvesCommonPool`, each `CompletableFuture.runAsync(() -> Thread.sleep(500))` call, with no second argument, defaults to submitting its `Runnable` onto `ForkJoinPool.commonPool()` — the exact same shared pool the subsequent `parallelStream()` call will also try to use.
2. With `parallelism - 1` such blocking tasks submitted and given 50ms to actually start sleeping, nearly all of the common pool's worker threads are now occupied for the next 500ms, doing nothing but sleeping — unavailable for any other work.
3. When `numbers.parallelStream().mapToLong(...).sum()` then runs, it internally splits the summation into fork/join subtasks and submits them to the common pool — but finds most workers already busy, so far fewer of them are actually available to process the split subtasks concurrently, and the summation takes measurably longer than it would with a fully available pool.
4. In `DedicatedExecutorFixesStarvation`, the identical blocking calls are instead submitted with `blockingPool` explicitly passed as the second argument to `runAsync` — this routes them to a completely separate `ExecutorService`, one that has nothing to do with `ForkJoinPool.commonPool()`.
5. When the parallel stream runs this time, the common pool has never been touched by the blocking tasks at all — every one of its worker threads is available to help process the summation's fork/join subtasks, so it completes in roughly the same time as the uncontended Level 1 baseline.
6. The comparison between Level 2's and Level 3's elapsed times makes the cost of accidental common-pool contention concrete: identical "real" work (the blocking tasks) produces a measurable slowdown in *completely unrelated* code (the parallel stream) purely because they happened to share a thread pool by default — and that slowdown disappears entirely once the blocking work is moved to its own dedicated pool.

## 7. Gotchas & takeaways

> **Gotcha:** `CompletableFuture.supplyAsync`/`runAsync` called with no `Executor` argument, and any `.parallelStream()` call, both default to the shared `ForkJoinPool.commonPool()` — it's easy to write code that looks perfectly correct and performant in isolation, but silently degrades unrelated parallel streams or `CompletableFuture` chains elsewhere in the same JVM the moment it does anything blocking or long-running on that shared pool.

- The common pool is a single, JVM-wide `ForkJoinPool`, sized (by default) to roughly `availableProcessors() - 1`, shared by parallel streams, `CompletableFuture`'s `*Async` methods without an explicit executor, and default fork/join task submission.
- Never submit blocking (I/O, `Thread.sleep`, lock-waiting) work to the common pool — pass an explicit, dedicated `Executor` to `CompletableFuture`'s `*Async` methods, or construct and use your own `ForkJoinPool`/`ExecutorService` for that work instead.
- Reserve the common pool for genuinely short, CPU-bound, non-blocking tasks — exactly the kind parallel streams and typical `RecursiveTask`/`RecursiveAction` computations are meant to be.
- The common pool's default parallelism can be tuned via the `java.util.concurrent.ForkJoinPool.common.parallelism` system property, but changing it JVM-wide affects every feature that relies on the pool, not just your own code — prefer a dedicated pool over globally reconfiguring the shared one.
- When diagnosing unexplained slowdowns in parallel streams or `CompletableFuture` chains, check whether *any* code in the same JVM process is submitting blocking work to the common pool — it's a common, easy-to-miss cause of exactly this symptom.
