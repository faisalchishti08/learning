---
card: java
gi: 852
slug: creating-threads-thread-vs-runnable-vs-callable
title: Creating threads (Thread vs Runnable vs Callable)
---

## 1. What it is

Java offers three ways to define the work a thread executes. **Extending `Thread`** and overriding `run()` couples the task directly to the `Thread` class itself — since Java has no multiple inheritance, a class that extends `Thread` can't extend anything else. **Implementing `Runnable`** (a single method, `void run()`) decouples the task from `Thread` entirely — a `Runnable` is just a unit of work, passed to a `Thread` constructor (or, more commonly today, submitted to an `ExecutorService`), and the implementing class remains free to extend something else if needed. **Implementing `Callable<V>`** (a single method, `V call() throws Exception`) goes further: unlike `Runnable`, it can **return a value** and can throw **checked exceptions** — submitted to an `ExecutorService`, it returns a `Future<V>` representing the eventual result.

## 2. Why & when

Extending `Thread` is rarely the right choice in modern code — it wastes the one available superclass slot on inheritance from `Thread` purely to get `run()` overridden, when a `Runnable` achieves the identical result without that cost, and remains usable with the modern `ExecutorService` framework that extending `Thread` doesn't naturally fit into. `Runnable` is the right default for fire-and-forget work — a task that does something (logs, updates state, sends a notification) but doesn't need to report a result back, and doesn't need to signal failure via a checked exception. `Callable<V>` is the right choice specifically when the task needs to **produce a result** the calling code needs to consume — computing a value, fetching data — or when the task's logic naturally throws a checked exception that needs to propagate back to whoever's waiting on the result, which `Runnable`'s signature simply has no way to express.

## 3. Core concept

```java
// Extending Thread -- couples the task to Thread itself, burns the one superclass slot.
class WorkerThread extends Thread {
    @Override public void run() { System.out.println("running via Thread subclass"); }
}

// Implementing Runnable -- decoupled, no return value, no checked exceptions.
Runnable task = () -> System.out.println("running via Runnable");
new Thread(task).start();

// Implementing Callable -- decoupled, DOES return a value, CAN throw checked exceptions.
Callable<Integer> computation = () -> { return 6 * 7; };
ExecutorService pool = Executors.newSingleThreadExecutor();
Future<Integer> future = pool.submit(computation);
Integer result = future.get(); // 42 -- blocks until the computation completes, then returns its result
```

Only `Callable`'s `call()` method signature (`V call() throws Exception`) permits both returning a typed value and declaring a checked exception — `Runnable.run()`'s signature (`void run()`) permits neither.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Runnable has no return value and cannot throw checked exceptions; Callable can return a typed value and can throw checked exceptions, submitted through an ExecutorService to get a Future">
  <rect x="40" y="30" width="250" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="165" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Runnable.run()</text>
  <text x="165" y="75" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">void, no checked exceptions</text>

  <rect x="340" y="30" width="260" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="470" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Callable&lt;V&gt;.call()</text>
  <text x="470" y="75" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">returns V, throws Exception</text>

  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">ExecutorService.submit(Callable) returns a Future&lt;V&gt; -- the handle to the eventual result or thrown exception</text>
</svg>

*`Runnable` is fire-and-forget; `Callable` returns a value (and can throw), retrieved later through a `Future`.*

## 5. Runnable example

Scenario: computing a report value from a data source, growing from the legacy `Thread`-extension approach, through the decoupled `Runnable` approach, to `Callable` returning a genuine result with proper exception handling via `Future`.

### Level 1 — Basic

```java
public class ThreadSubclassApproach {
    static class ReportWorker extends Thread {
        @Override
        public void run() {
            System.out.println("computing report on: " + Thread.currentThread().getName());
        }
    }

    public static void main(String[] args) throws InterruptedException {
        ReportWorker worker = new ReportWorker();
        worker.start();
        worker.join();
        System.out.println("done (main thread: " + Thread.currentThread().getName() + ")");
    }
}
```

**How to run:** `java ThreadSubclassApproach.java` (JDK 17+).

Expected output:
```
computing report on: Thread-0
done (main thread: main)
```

This works, but `ReportWorker` can never extend any other class — if it needed to inherit from some existing base class for other reasons, extending `Thread` here would make that impossible, since Java classes can only extend one superclass.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class RunnableApproach {
    // Decoupled from Thread entirely -- this class could extend something else if it needed to.
    static class ReportTask implements Runnable {
        @Override
        public void run() {
            System.out.println("computing report on: " + Thread.currentThread().getName());
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Thread thread = new Thread(new ReportTask());
        thread.start();
        thread.join();

        // The SAME Runnable can also be submitted to a thread pool -- Thread-extension can't do this naturally.
        ExecutorService pool = Executors.newFixedThreadPool(2);
        pool.submit(new ReportTask());
        pool.shutdown();
        pool.awaitTermination(1, TimeUnit.SECONDS);
    }
}
```

**How to run:** `java RunnableApproach.java`.

Expected output shape (thread names vary depending on which is used):
```
computing report on: Thread-0
computing report on: pool-1-thread-1
```

The real-world concern added: the exact same `ReportTask` object works both with a plain `Thread` and with an `ExecutorService`'s thread pool — decoupling the task's logic from any specific thread-creation mechanism, which is exactly the flexibility extending `Thread` directly would have prevented.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class CallableWithResultAndException {
    static class ReportComputation implements Callable<Integer> {
        private final int dataPoints;
        ReportComputation(int dataPoints) { this.dataPoints = dataPoints; }

        @Override
        public Integer call() throws Exception {
            if (dataPoints < 0) {
                throw new IllegalArgumentException("dataPoints cannot be negative: " + dataPoints);
            }
            return dataPoints * dataPoints; // stand-in for some real computed report value
        }
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(2);

        Future<Integer> goodResult = pool.submit(new ReportComputation(12));
        Future<Integer> badResult = pool.submit(new ReportComputation(-5));

        try {
            Integer value = goodResult.get(); // blocks until the computation completes, returns its result
            System.out.println("report value: " + value);
        } catch (ExecutionException e) {
            System.out.println("unexpected failure: " + e.getCause());
        }

        try {
            badResult.get(); // the thrown exception is wrapped and re-thrown as ExecutionException here
        } catch (ExecutionException e) {
            System.out.println("caught expected failure via Future.get(): " + e.getCause());
        }

        pool.shutdown();
    }
}
```

**How to run:** `java CallableWithResultAndException.java`.

Expected output:
```
report value: 144
caught expected failure via Future.get(): java.lang.IllegalArgumentException: dataPoints cannot be negative: -5
```

This adds the production-flavored hard case: a `Callable<Integer>` that both returns a genuine typed result (`144`, the square of `12`) **and** can throw a checked-or-unchecked exception during computation — something `Runnable` has no way to express in its signature at all. `Future.get()` is where both possibilities surface: it either returns the successfully computed value, or throws `ExecutionException` wrapping whatever exception the `Callable` actually threw, letting the calling code recover the original failure via `getCause()`.

## 6. Walkthrough

Tracing `CallableWithResultAndException.main`:

1. `pool.submit(new ReportComputation(12))` hands the `Callable<Integer>` to the thread pool, which schedules it for execution on one of its worker threads and immediately returns a `Future<Integer>` — `goodResult` — representing the eventual outcome, without blocking the calling thread at all.
2. Similarly, `pool.submit(new ReportComputation(-5))` returns `badResult` immediately, and its actual execution (successful or not) happens asynchronously on a pool thread.
3. `goodResult.get()` blocks the main thread until that specific submitted task actually finishes running. Since `ReportComputation(12).call()` returns `144` without throwing, `get()` simply returns that value directly, and it's printed.
4. `badResult.get()` similarly blocks until its corresponding task finishes — but `ReportComputation(-5).call()` throws `IllegalArgumentException` partway through, on the pool's worker thread, not on the main thread that's waiting via `get()`. The `ExecutorService` framework catches that exception internally and stores it inside the `Future`, so it can be reported back correctly to whichever thread eventually calls `get()`.
5. `get()` on `badResult` re-throws this stored failure as a checked `ExecutionException`, wrapping the original exception as its cause — the `catch (ExecutionException e)` block retrieves that original `IllegalArgumentException` via `e.getCause()` and prints it, demonstrating that even though the actual failure happened on a completely different thread, its information is correctly and safely propagated back to the thread that called `get()`.

## 7. Gotchas & takeaways

> **Gotcha:** an exception thrown inside a `Callable.call()` is **not** propagated automatically the way an uncaught exception on a plain thread would print a stack trace — it's silently captured inside the `Future` and only surfaces when (and if) something actually calls `get()` on that specific `Future`. A submitted `Callable` whose result is never retrieved via `get()` can fail completely silently, with no visible error at all.

- Extending `Thread` couples task logic to `Thread` itself, wasting the class's one available superclass slot — generally avoid this in modern code.
- `Runnable` (`void run()`) is the right default for fire-and-forget work with no return value and no need to propagate a checked exception.
- `Callable<V>` (`V call() throws Exception`) is the right choice when a task needs to return a typed result or needs to signal failure via a (possibly checked) exception.
- `ExecutorService.submit(Callable<V>)` returns a `Future<V>` immediately without blocking; calling `.get()` on it later blocks until the result is available, returning the value or re-throwing any failure wrapped in `ExecutionException`.
- A `Callable` submission whose `Future` is never checked via `get()` can fail silently — always retrieve (or at least check) the result of anything submitted this way if failure detection matters.
