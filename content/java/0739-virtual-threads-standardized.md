---
card: java
gi: 739
slug: virtual-threads-standardized
title: Virtual threads — standardized
---

## 1. What it is

**Java 21** (JEP 444) makes [virtual threads](0735-virtual-threads-2nd-preview.md) a **permanent, standard feature** of the platform — no `--enable-preview` flag needed. After two preview rounds (Java 19 and Java 20) that fixed pinning bugs and refined the API surface, `Thread.ofVirtual()`, `Thread.startVirtualThread(...)`, and `Executors.newVirtualThreadPerTaskExecutor()` are now committed, stable API that any production code can depend on without caveats about future breakage. The core idea is unchanged: a virtual thread is a lightweight, JVM-managed thread that gets mounted onto a small pool of OS ("carrier") threads only while actually running, and unmounts during blocking operations — so a program can create millions of them without exhausting OS resources.

## 2. Why & when

Before virtual threads, the standard way to get high I/O concurrency in Java was either to accept **one OS thread per request** (which stops scaling somewhere in the low thousands, because each OS thread costs megabytes of stack and kernel scheduling overhead), or to rewrite the whole call chain in a reactive style (`CompletableFuture`, `Mono`/`Flux`), trading straight-line, debuggable code for callback chains and dedicated reactive-only libraries. Virtual threads close that gap: you keep the simple "one thread per request, blocking calls read top to bottom" style, and the JVM handles making blocking I/O cheap under the hood. Standardization in Java 21 is the signal that this trade-off has been validated across two years of preview feedback — it's now safe to build production thread-per-request servers, batch pipelines, and fan-out/fan-in workloads on virtual threads without worrying the API will change under you. Use virtual threads when your bottleneck is **waiting** (network calls, database queries, file I/O) with lots of concurrent tasks; keep platform threads for CPU-bound work, since virtual threads don't add compute parallelism — the number of CPU cores is still the limit for actual crunching.

## 3. Core concept

```java
import java.util.concurrent.*;

// No --enable-preview needed anymore — this is just normal Java 21 API.
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    for (int i = 0; i < 100_000; i++) {
        int taskId = i;
        executor.submit(() -> {
            Thread.sleep(Duration.ofMillis(10)); // "blocking" I/O simulation
            return taskId;
        });
    }
} // executor.close() waits for all submitted tasks to finish
```

`ExecutorService` itself became `AutoCloseable` in Java 19, so the try-with-resources block above both submits work and waits for completion — no separate `shutdown()`/`awaitTermination()` dance required.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Many virtual threads share a small pool of carrier OS threads, mounting only while running and unmounting during blocking calls">
  <rect x="20" y="20" width="600" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">100,000 virtual threads (JVM-managed, cheap)</text>
  <text x="320" y="65" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">VT-1  VT-2  VT-3  VT-4  ...  VT-100000</text>

  <line x1="320" y1="80" x2="320" y2="110" stroke="#79c0ff" stroke-width="2"/>
  <text x="330" y="100" fill="#79c0ff" font-size="10" font-family="sans-serif">mount / unmount</text>

  <rect x="120" y="120" width="400" height="60" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="320" y="145" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Small pool of carrier (platform/OS) threads</text>
  <text x="320" y="165" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">typically ~ number of CPU cores</text>

  <text x="320" y="205" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Blocking I/O unmounts the virtual thread, freeing the carrier for another one</text>
</svg>

*One small pool of OS threads serves an enormous number of virtual threads because blocked ones step aside.*

## 5. Runnable example

The scenario: a service that fetches data for many customer IDs, where each "fetch" simulates a slow network call. We grow it from a trivial version to a production-shaped batch job.

### Level 1 — Basic

```java
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;

public class FetchBasic {
    static String fetchCustomer(int id) throws InterruptedException {
        Thread.sleep(Duration.ofMillis(50)); // pretend network call
        return "customer-" + id;
    }

    public static void main(String[] args) throws InterruptedException {
        List<Thread> threads = new ArrayList<>();
        for (int i = 0; i < 20; i++) {
            int id = i;
            Thread t = Thread.ofVirtual().start(() -> {
                try {
                    System.out.println(fetchCustomer(id));
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            });
            threads.add(t);
        }
        for (Thread t : threads) t.join();
    }
}
```

**How to run:** `java FetchBasic.java` (JDK 21+, no flags needed).

This starts 20 virtual threads directly with `Thread.ofVirtual().start(...)`, each sleeping 50ms to simulate a slow call, then joins them all. Even though the total simulated work is 20 × 50ms = 1 second of sleeping, the threads run concurrently, so the whole program finishes in roughly 50ms.

### Level 2 — Intermediate

```java
import java.time.Duration;
import java.util.concurrent.*;
import java.util.List;
import java.util.stream.IntStream;

public class FetchExecutor {
    static String fetchCustomer(int id) throws InterruptedException {
        Thread.sleep(Duration.ofMillis(50));
        if (id == 13) throw new RuntimeException("customer 13 lookup failed");
        return "customer-" + id;
    }

    public static void main(String[] args) throws InterruptedException {
        try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
            List<Future<String>> futures = IntStream.range(0, 20)
                .mapToObj(id -> executor.submit(() -> fetchCustomer(id)))
                .toList();

            for (Future<String> future : futures) {
                try {
                    System.out.println(future.get());
                } catch (ExecutionException e) {
                    System.out.println("failed: " + e.getCause().getMessage());
                }
            }
        }
    }
}
```

**How to run:** `java FetchExecutor.java`.

This replaces manual thread management with `newVirtualThreadPerTaskExecutor()`, which submits one virtual thread per task and returns a `Future` per task — the real-world concern being added is **error isolation**: one failing task (customer 13) doesn't crash the whole batch, because `Future.get()` re-throws its failure wrapped in an `ExecutionException` that we catch individually, letting the other 19 results print normally.

### Level 3 — Advanced

```java
import java.time.Duration;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.List;
import java.util.stream.IntStream;

public class FetchProduction {
    static String fetchCustomer(int id) throws InterruptedException {
        Thread.sleep(Duration.ofMillis(50));
        if (id == 13) throw new RuntimeException("customer 13 lookup failed");
        return "customer-" + id;
    }

    public static void main(String[] args) throws InterruptedException {
        AtomicInteger succeeded = new AtomicInteger();
        AtomicInteger failed = new AtomicInteger();
        long start = System.nanoTime();

        try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
            List<Future<String>> futures = IntStream.range(0, 5000)
                .mapToObj(id -> executor.submit(() -> {
                    try {
                        String result = fetchCustomer(id);
                        succeeded.incrementAndGet();
                        return result;
                    } catch (RuntimeException e) {
                        failed.incrementAndGet();
                        throw e;
                    }
                }))
                .toList();

            for (Future<String> future : futures) {
                try {
                    future.get(2, TimeUnit.SECONDS);
                } catch (ExecutionException | TimeoutException ignored) {
                    // already counted in `failed`, or timed out — move on
                }
            }
        }

        double seconds = (System.nanoTime() - start) / 1e9;
        System.out.printf("succeeded=%d failed=%d elapsed=%.2fs%n",
            succeeded.get(), failed.get(), seconds);
    }
}
```

**How to run:** `java FetchProduction.java`.

This scales the batch to 5,000 concurrent fetches — a size that would need careful thread-pool tuning with platform threads but here needs none — and adds the hard cases a real batch job faces: **per-task timeouts** (`future.get(2, TimeUnit.SECONDS)`, so one hung task can't stall the whole loop forever), and **aggregate success/failure counters** using `AtomicInteger` since many virtual threads update them concurrently. The elapsed time printed stays close to 50ms plus scheduling overhead, not 5000 × 50ms, because all 5,000 virtual threads overlap their sleeps on the small carrier-thread pool.

## 6. Walkthrough

Tracing `FetchProduction` from entry point to output:

1. `main` starts a timer and creates two `AtomicInteger` counters shared across every task.
2. The try-with-resources block creates a virtual-thread-per-task executor. Because it's try-with-resources, `executor.close()` runs automatically at the end of the block and blocks until every submitted task has finished — this is the Java 19+ `AutoCloseable` behavior on `ExecutorService`.
3. `IntStream.range(0, 5000).mapToObj(...)` submits 5,000 tasks. Each `executor.submit(...)` call returns immediately with a `Future<String>` and hands the actual task to a **new virtual thread**, which the JVM schedules onto its small carrier-thread pool (usually sized to the number of CPU cores).
4. Each task calls `fetchCustomer(id)`, which sleeps 50ms. During that sleep, the **virtual thread unmounts** from its carrier — the carrier OS thread is freed to run a different virtual thread's task in the meantime. This is why 5,000 sleeping tasks don't need 5,000 OS threads.
5. On success, `succeeded.incrementAndGet()` runs; for `id == 13`, the lambda throws, `failed.incrementAndGet()` runs, and the exception propagates out of the task, which `Future` captures instead of crashing anything.
6. Back in `main`, the loop over `futures` calls `future.get(2, TimeUnit.SECONDS)` for each one. For the failed task, this throws `ExecutionException` (caught and ignored, since the failure was already counted); for a task that somehow never completes within 2 seconds, `TimeoutException` is thrown instead.
7. Once every future has been waited on, the try-with-resources block ends, `executor.close()` returns (all tasks are already done by then), and `main` prints the final line.

Expected output shape:
```
succeeded=4999 failed=1 elapsed=0.06s
```

The elapsed time near 0.06s (not 250s) is the concrete, observable proof that virtual threads delivered real I/O concurrency: 5,000 tasks each "blocking" for 50ms completed in roughly one sleep interval's worth of wall-clock time.

## 7. Gotchas & takeaways

> **Gotcha:** virtual threads don't make CPU-bound code faster. If `fetchCustomer` did heavy computation instead of sleeping, running 5,000 of them wouldn't finish any faster than 5,000 platform threads would — you'd still be bound by the number of CPU cores. Virtual threads only pay off when the bottleneck is waiting, not computing.

- Standardized in Java 21 — no `--enable-preview` flag, safe for production use.
- Use `Executors.newVirtualThreadPerTaskExecutor()` for "one virtual thread per task" workloads; it's `AutoCloseable`, so try-with-resources handles shutdown.
- Don't pool virtual threads like platform threads — creating a new one per task is the intended, cheap pattern.
- Avoid `synchronized` blocks around blocking calls on the hot path; prefer `java.util.concurrent.locks.ReentrantLock` to avoid carrier-thread pinning.
- CPU-bound work still needs a bounded platform-thread pool sized to core count — virtual threads solve the I/O-concurrency problem, not the compute-parallelism problem.
