---
card: java
gi: 874
slug: executor-executorservice-scheduledexecutorservice
title: Executor / ExecutorService / ScheduledExecutorService
---

## 1. What it is

`Executor` is the simplest possible abstraction over "running something asynchronously": a single method, `execute(Runnable)`, that decouples *submitting* a task from deciding *how* it runs (new thread per task, a pool of reused threads, the calling thread itself). `ExecutorService` extends this with a full lifecycle (`shutdown()`, `awaitTermination()`) and the ability to submit tasks that return results (`submit(Callable<T>)` returns a `Future<T>`). `ScheduledExecutorService` extends `ExecutorService` further with the ability to run tasks after a delay or on a repeating schedule (`schedule`, `scheduleAtFixedRate`, `scheduleWithFixedDelay`). Together they form the standard, higher-level replacement for manually creating and managing `Thread` objects.

## 2. Why & when

Manually creating a new `Thread` for every unit of work is expensive (thread creation and teardown cost real time and memory) and unmanaged (nothing limits how many threads pile up under load, and nothing coordinates a clean shutdown). `ExecutorService`, backed by a thread pool, reuses a bounded set of worker threads across many submitted tasks, giving you back control over concurrency limits, and gives you `Future`s to track completion and results instead of manually joining threads. Use `Executor`/`ExecutorService` any time you have "run this asynchronously" work — HTTP request handling, background jobs, parallel computation — and reach for `ScheduledExecutorService` specifically when you need delayed or periodic execution (a health-check ping every 30 seconds, a cleanup task after a timeout) instead of hand-rolling `Thread.sleep` loops, which are harder to cancel cleanly and don't share a pool with other work.

## 3. Core concept

```java
ExecutorService pool = Executors.newFixedThreadPool(4);
pool.execute(() -> System.out.println("fire and forget"));       // Executor's basic method
Future<Integer> future = pool.submit(() -> 21 * 2);               // ExecutorService: get a result back
pool.shutdown();                                                   // stop accepting new tasks, let existing ones finish

ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
scheduler.scheduleAtFixedRate(() -> System.out.println("tick"), 0, 1, TimeUnit.SECONDS); // repeats every 1s
```

`execute` fires and forgets; `submit` gives you a handle (`Future`) to check completion, retrieve a result, or catch an exception the task threw; the scheduled variants add timing on top of the same pooled-thread model.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Tasks submitted to a thread pool queue, worker threads pulling from the queue and executing tasks, results returned via Future">
  <rect x="20" y="20" width="160" height="130" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="100" y="15" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Task queue</text>
  <text x="100" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">task 1</text>
  <text x="100" y="70" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">task 2</text>
  <text x="100" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">task 3</text>
  <text x="100" y="120" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">task 4...</text>

  <rect x="240" y="20" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Worker thread 1</text>
  <rect x="240" y="90" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="120" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Worker thread 2</text>

  <rect x="460" y="55" width="160" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="540" y="85" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Future&lt;T&gt; -- result</text>

  <line x1="180" y1="45" x2="238" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a12)"/>
  <line x1="180" y1="95" x2="238" y2="105" stroke="#8b949e" stroke-width="2" marker-end="url(#a12)"/>
  <line x1="400" y1="55" x2="456" y2="70" stroke="#79c0ff" stroke-width="2" marker-end="url(#a12)"/>
  <defs><marker id="a12" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*A fixed pool of worker threads pulls tasks off a shared queue; `submit()` hands the caller a `Future` to retrieve the eventual result.*

## 5. Runnable example

Scenario: computing a batch of "expensive" values, growing from manual `Thread` management, to a fixed `ExecutorService` with `Future`s, to a `ScheduledExecutorService` running a periodic health check alongside the worker pool, then shutting both down cleanly.

### Level 1 — Basic

```java
import java.util.*;

public class ManualThreadsBasic {
    static int expensiveSquare(int n) {
        try { Thread.sleep(50); } catch (InterruptedException ignored) {}
        return n * n;
    }

    public static void main(String[] args) throws InterruptedException {
        int[] inputs = {1, 2, 3, 4};
        int[] results = new int[inputs.length];
        Thread[] threads = new Thread[inputs.length];

        for (int i = 0; i < inputs.length; i++) {
            final int idx = i;
            threads[i] = new Thread(() -> results[idx] = expensiveSquare(inputs[idx]));
            threads[i].start(); // a BRAND NEW thread for every single task -- no reuse, no pooling
        }
        for (Thread t : threads) t.join();

        System.out.println("results = " + Arrays.toString(results));
    }
}
```

**How to run:** `java ManualThreadsBasic.java` (JDK 17+).

Expected output:
```
results = [1, 4, 9, 16]
```

Works for four tasks, but creating a new OS-backed thread per task doesn't scale — at hundreds or thousands of tasks, the overhead of thread creation/teardown and unbounded concurrency becomes a real problem.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.concurrent.*;

public class FixedPoolWithFutures {
    static int expensiveSquare(int n) {
        try { Thread.sleep(50); } catch (InterruptedException ignored) {}
        return n * n;
    }

    public static void main(String[] args) throws InterruptedException, ExecutionException {
        ExecutorService pool = Executors.newFixedThreadPool(4); // bounded, REUSED worker threads
        int[] inputs = {1, 2, 3, 4, 5, 6, 7, 8};
        List<Future<Integer>> futures = new ArrayList<>();

        for (int n : inputs) {
            futures.add(pool.submit(() -> expensiveSquare(n))); // returns a Future, doesn't block
        }

        List<Integer> results = new ArrayList<>();
        for (Future<Integer> f : futures) {
            results.add(f.get()); // blocks until THIS task's result is ready
        }

        pool.shutdown(); // stop accepting new tasks
        pool.awaitTermination(5, TimeUnit.SECONDS); // wait for in-flight tasks to finish
        System.out.println("results = " + results);
    }
}
```

**How to run:** `java FixedPoolWithFutures.java`.

Expected output:
```
results = [1, 4, 9, 16, 25, 36, 49, 64]
```

The real-world concern added: eight tasks now share only four worker threads (reused, not recreated per task), submitted via `submit()` which returns a `Future` per task — letting the pool naturally throttle concurrency and letting the caller collect results without manually managing thread objects or join order.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class ScheduledHealthCheckWithPool {
    static int expensiveSquare(int n) {
        try { Thread.sleep(50); } catch (InterruptedException ignored) {}
        return n * n;
    }

    public static void main(String[] args) throws InterruptedException, ExecutionException {
        ExecutorService workerPool = Executors.newFixedThreadPool(4);
        ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
        AtomicInteger healthChecks = new AtomicInteger(0);

        // Runs every 100ms, independent of the worker pool's task queue -- monitors system health.
        ScheduledFuture<?> healthTask = scheduler.scheduleAtFixedRate(
            () -> healthChecks.incrementAndGet(), 0, 100, TimeUnit.MILLISECONDS);

        List<Future<Integer>> futures = new ArrayList<>();
        for (int n = 1; n <= 8; n++) {
            final int val = n;
            futures.add(workerPool.submit(() -> expensiveSquare(val)));
        }

        List<Integer> results = new ArrayList<>();
        for (Future<Integer> f : futures) results.add(f.get());

        healthTask.cancel(false); // stop the recurring health check -- don't interrupt if it's mid-run
        scheduler.shutdown();
        workerPool.shutdown();
        workerPool.awaitTermination(5, TimeUnit.SECONDS);
        scheduler.awaitTermination(5, TimeUnit.SECONDS);

        System.out.println("results = " + results);
        System.out.println("health checks that ran while work was in progress: " + (healthChecks.get() > 0));
    }
}
```

**How to run:** `java ScheduledHealthCheckWithPool.java`.

Expected output shape (the exact health-check count varies by timing, but is always greater than zero):
```
results = [1, 4, 9, 16, 25, 36, 49, 64]
health checks that ran while work was in progress: true
```

This adds the production-flavored hard case: a `ScheduledExecutorService` running an independent, periodic background task (a health check every 100ms) concurrently with the main worker pool's batch of one-off tasks — the two pools operate independently, so the recurring health check keeps its own steady cadence regardless of how busy the worker pool is, and both are shut down cleanly and explicitly at the end (canceling the recurring task first, so it doesn't keep firing during shutdown).

## 6. Walkthrough

Tracing `ScheduledHealthCheckWithPool.main`:

1. Two separate pools are created: `workerPool` (4 threads, for the CPU/latency-bound squaring work) and `scheduler` (1 thread, dedicated to timing).
2. `scheduler.scheduleAtFixedRate(..., 0, 100, TimeUnit.MILLISECONDS)` schedules the health-check `Runnable` to run immediately, then every 100ms thereafter, on the scheduler's own thread — this is entirely independent of `workerPool`'s queue and thread count.
3. Eight squaring tasks are submitted to `workerPool` via `submit()`; each returns a `Future<Integer>` immediately without blocking the main thread, while the 4 worker threads pick tasks off the internal queue and execute `expensiveSquare` (each call sleeping 50ms to simulate real work).
4. `main` then iterates the list of `Future`s and calls `f.get()` on each in turn — this blocks only until that specific task's result is ready; since 8 tasks share 4 threads (each 50ms), the whole batch takes roughly 100ms of wall-clock time (two waves of 4 tasks each), during which the scheduler has fired its health check roughly once per wave.
5. Once every result has been collected into `results`, `healthTask.cancel(false)` stops the recurring schedule (the `false` means "don't interrupt it if it happens to be running right now" — appropriate since the health check body here is trivial and fast).
6. `scheduler.shutdown()` and `workerPool.shutdown()` both stop accepting new tasks; `awaitTermination` on each blocks until all already-submitted work finishes.
7. The final prints confirm both the correct squared results and that at least one health check fired during the roughly 100ms the worker pool was busy — demonstrating the two pools ran concurrently and independently.

## 7. Gotchas & takeaways

> **Gotcha:** forgetting to call `shutdown()` (or its more aggressive cousin `shutdownNow()`) on an `ExecutorService` leaves its threads alive indefinitely, which will keep a JVM process running even after `main` logically finishes — a classic cause of programs that mysteriously never exit.

- `Executor` is the minimal "run this asynchronously" interface; `ExecutorService` adds lifecycle management and result-bearing submission (`Future`); `ScheduledExecutorService` adds delayed and periodic execution on top of that.
- Always explicitly `shutdown()` an `ExecutorService` you created, and typically follow with `awaitTermination` to wait for in-flight work to finish before moving on.
- `submit()` returns a `Future` even for a `Runnable` (result is `null`) or a `Callable<T>` (result is the computed value); use `execute()` only when you truly don't need to track completion or catch exceptions.
- `scheduleAtFixedRate` and `scheduleWithFixedDelay` differ subtly: fixed-rate schedules the next run relative to the *start* time of the previous run (so it can "catch up" or overlap if a run takes too long), while fixed-delay schedules it relative to the *end* — pick based on whether drift or overlap is the bigger concern for your task.
- For actual sizing of a fixed pool's thread count, and choosing among `Executors`' preset factory methods, see [thread pool sizing strategies](0876-thread-pool-sizing-strategies.md) and [`ThreadPoolExecutor` configuration](0875-threadpoolexecutor-configuration-core-max-queue-rejection.md).
