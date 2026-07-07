---
card: java
gi: 396
slug: executor-executorservice
title: Executor & ExecutorService
---

## 1. What it is

`Executor` and `ExecutorService`, introduced in Java 5 as part of `java.util.concurrent`, decouple *what* code should run concurrently from *how* the threads that run it are created and managed. `Executor` is the simplest interface: it has one method, `execute(Runnable)`, which submits a task to be run — how or when it actually runs (immediately, on a pooled thread, queued) is entirely up to the implementation. `ExecutorService` extends `Executor` with a richer API: `submit(Callable)` (for tasks that return a value or throw a checked exception), tracking results via `Future`, and lifecycle control (`shutdown()`, `awaitTermination(...)`). The `Executors` factory class provides ready-made implementations — `Executors.newFixedThreadPool(n)`, `Executors.newSingleThreadExecutor()`, and others.

## 2. Why & when

Before `java.util.concurrent`, running work concurrently meant manually creating and managing `Thread` objects yourself — `new Thread(runnable).start()` for every single task. This gets unmanageable fast: creating a brand-new OS thread per task is expensive and doesn't scale to thousands of small tasks, and there's no built-in way to limit how many run simultaneously, wait for a group of them to finish, or retrieve a return value cleanly (a raw `Thread` has no return value at all — you'd need to manually stash a result in a shared variable and handle synchronization yourself).

An `ExecutorService` solves all of this: it manages a pool of reusable worker threads internally, submitting a task just means handing it a `Runnable` or `Callable` and letting the pool decide which thread (of a small, fixed, reused set) actually executes it — dramatically cheaper than a new thread per task. `submit(Callable<T>)` returns a `Future<T>`, a handle you can later call `.get()` on to block until the result is ready (or to retrieve an exception the task threw). You reach for an `ExecutorService` any time you need to run more than a handful of concurrent tasks, need their results back, or need controlled shutdown behaviour — essentially the default, professional way to do concurrent work in Java, rather than raw `Thread` management.

## 3. Core concept

```java
import java.util.concurrent.*;

public class ExecutorDemo {
    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(2); // a pool of exactly 2 reusable worker threads

        Future<Integer> result = pool.submit(() -> { // Callable: returns a value
            Thread.sleep(100);
            return 21 * 2;
        });

        System.out.println("Doing other work while the task runs...");
        System.out.println("Result: " + result.get()); // blocks here until the task finishes

        pool.shutdown(); // no more tasks accepted; lets already-submitted tasks finish
    }
}
```

**How to run:** `java ExecutorDemo.java`

`Executors.newFixedThreadPool(2)` creates a pool backed by exactly two reusable threads. `pool.submit(() -> { ... })` hands it a `Callable<Integer>` (a lambda that computes and returns a value); the pool assigns it to one of its two worker threads and immediately returns a `Future<Integer>` without blocking `main`. `"Doing other work..."` prints right away, proving `submit` doesn't wait for the task. `result.get()` then blocks until the background task finishes and returns its value, `42`.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="submitting a task to an ExecutorService returns immediately with a Future while a worker thread from the pool runs the task in the background; get() on the Future blocks until the result is ready">
  <rect x="8" y="8" width="624" height="164" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">pool.submit(callable)  -&gt;  returns Future immediately, does NOT block</text>

  <rect x="30" y="50" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="75" fill="#79c0ff" font-size="10" text-anchor="middle">main thread continues</text>

  <rect x="250" y="50" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="340" y="75" fill="#6db33f" font-size="10" text-anchor="middle">worker thread runs task</text>

  <text x="20" y="120" fill="#e6edf3" font-size="11">future.get()  -&gt;  BLOCKS main thread until worker thread's task completes</text>
  <line x1="120" y1="130" x2="340" y2="130" stroke="#f85149" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="230" y="150" fill="#f85149" font-size="9" text-anchor="middle">waits here</text>
</svg>

## 5. Runnable example

Scenario: fetching data from several simulated remote sources, evolved from manually managing raw `Thread` objects (with no easy way to get results back), through an `ExecutorService` handling multiple `Callable` tasks with `Future`, to a version properly handling task failures and pool shutdown together.

### Level 1 — Basic

```java
public class FetchWithRawThreads {
    static String fetchSlow(String source) throws InterruptedException {
        Thread.sleep(50); // simulates network latency
        return "data from " + source;
    }

    public static void main(String[] args) throws InterruptedException {
        // No clean way to get a return value back from a raw Thread -- need a shared array as a workaround
        String[] resultHolder = new String[1];

        Thread worker = new Thread(() -> {
            try {
                resultHolder[0] = fetchSlow("server-A");
            } catch (InterruptedException ignored) { }
        });
        worker.start();
        worker.join(); // block until this ONE thread finishes -- no pooling, no reuse

        System.out.println(resultHolder[0]);
    }
}
```

**How to run:** `java FetchWithRawThreads.java`

Getting a result back from a raw `Thread` requires an awkward workaround — a shared array captured by the lambda, since `Thread` has no built-in return-value mechanism. There's also no thread reuse: each new task would need an entirely new `Thread` object, expensive if there were many of them.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.List;

public class FetchWithExecutorService {
    static String fetchSlow(String source) throws InterruptedException {
        Thread.sleep(50);
        return "data from " + source;
    }

    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(3);

        Future<String> futureA = pool.submit(() -> fetchSlow("server-A"));
        Future<String> futureB = pool.submit(() -> fetchSlow("server-B"));
        Future<String> futureC = pool.submit(() -> fetchSlow("server-C"));

        // All three tasks run concurrently on the pool's 3 threads; get() waits for each result
        System.out.println(futureA.get());
        System.out.println(futureB.get());
        System.out.println(futureC.get());

        pool.shutdown();
    }
}
```

**How to run:** `java FetchWithExecutorService.java`

Three `Callable` tasks are submitted to a 3-thread pool, all running concurrently rather than one at a time; each returns a real `String` directly through its own `Future`, with no shared-array workaround needed. Because the pool has exactly enough threads for all three tasks, all three run genuinely in parallel, and the total wait time is roughly the time for one task, not the sum of all three.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.List;
import java.util.ArrayList;

public class FetchWithFailureHandling {
    static String fetchSlow(String source) throws InterruptedException {
        Thread.sleep(50);
        if (source.equals("server-B")) {
            throw new RuntimeException("server-B is down"); // simulates a real failure
        }
        return "data from " + source;
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(3);
        List<Future<String>> futures = new ArrayList<>();

        for (String source : List.of("server-A", "server-B", "server-C")) {
            futures.add(pool.submit(() -> fetchSlow(source)));
        }

        for (Future<String> future : futures) {
            try {
                System.out.println(future.get());
            } catch (ExecutionException e) { // wraps the task's real exception
                System.out.println("Task failed: " + e.getCause().getMessage());
            }
        }

        pool.shutdown();
        boolean finished = pool.awaitTermination(1, TimeUnit.SECONDS); // wait for a clean shutdown
        System.out.println("Pool shut down cleanly: " + finished);
    }
}
```

**How to run:** `java FetchWithFailureHandling.java`

`server-B`'s task deliberately throws an exception; `future.get()` for that task doesn't crash the whole program — instead, it throws `ExecutionException`, wrapping the real exception (retrieved via `.getCause()`), letting the loop handle each task's success or failure independently. `pool.awaitTermination(1, TimeUnit.SECONDS)` waits, after `shutdown()`, for all already-submitted tasks to genuinely finish, confirming a clean, complete shutdown.

## 6. Walkthrough

Execution starts in `main`. The `for` loop submits three tasks to `pool`, one per source (`"server-A"`, `"server-B"`, `"server-C"`), each wrapped in a lambda `Callable<String>`. Because the pool has three threads, all three tasks begin running concurrently almost immediately — `submit` itself returns instantly for each, adding a `Future<String>` to `futures` without waiting for any task to actually complete.

The second `for` loop processes the futures in submission order (`server-A`, then `server-B`, then `server-C`), *not* necessarily the order they finish in, since `.get()` blocks until that specific future's task is done. For `server-A`'s future: `fetchSlow("server-A")` sleeps 50ms then returns `"data from server-A"` normally; `.get()` returns this string once the task completes, and it's printed directly.

For `server-B`'s future: inside the task, `fetchSlow("server-B")` sleeps 50ms, then `source.equals("server-B")` is `true`, so it throws `new RuntimeException("server-B is down")`. This exception doesn't propagate directly out of `.get()` as a `RuntimeException` — instead, the executor framework wraps it in `ExecutionException`, and `.get()` throws *that* wrapper. The `catch (ExecutionException e)` block catches it; `e.getCause()` retrieves the original `RuntimeException`, and `.getMessage()` gives `"server-B is down"`. This is printed as `Task failed: server-B is down`.

For `server-C`'s future: `fetchSlow("server-C")` completes normally, `.get()` returns `"data from server-C"`, printed directly — the loop continues correctly to this third future even after the second one's exception, since the `try/catch` is inside the loop body, scoped to each individual future.

After the loop, `pool.shutdown()` signals the pool to stop accepting new tasks. Since all three submitted tasks have already completed by this point (the loop above already called `.get()` on all of them), `pool.awaitTermination(1, TimeUnit.SECONDS)` returns `true` almost immediately, confirming the pool terminated cleanly within the given timeout.

Expected output:
```
data from server-A
Task failed: server-B is down
data from server-C
Pool shut down cleanly: true
```

## 7. Gotchas & takeaways

> Always call `shutdown()` on an `ExecutorService` once you're done submitting tasks to it — an `ExecutorService` that's never shut down keeps its worker threads alive indefinitely, which can prevent the JVM process from exiting even after `main` finishes, since non-daemon threads keep the program running.

- `Executor` is the minimal interface (`execute(Runnable)`); `ExecutorService` extends it with `submit(Callable)`/`Future`-based result retrieval and lifecycle management (`shutdown()`, `awaitTermination(...)`).
- `Executors.newFixedThreadPool(n)` creates a pool of exactly `n` reusable worker threads — submitting more tasks than there are threads simply queues the extras until a thread frees up.
- `Future<T>.get()` blocks the calling thread until the submitted task completes, returning its result — or throwing `ExecutionException` (wrapping the task's real exception, retrievable via `.getCause()`) if the task itself threw.
- Using an `ExecutorService` instead of raw `Thread` objects avoids the cost of creating a new OS thread per task and provides a clean, built-in way to retrieve results and handle failures.
- Always call `shutdown()` (and typically `awaitTermination(...)`) once all tasks have been submitted, to allow the pool's threads to terminate and let the JVM exit normally.
