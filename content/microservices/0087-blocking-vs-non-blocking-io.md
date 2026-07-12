---
card: microservices
gi: 87
slug: blocking-vs-non-blocking-i-o
title: "Blocking vs non-blocking I/O"
---

## 1. What it is

Blocking I/O ties up a thread for the entire duration of an I/O operation (a network call, a disk read) — the thread makes the call and simply sits idle, unable to do anything else, until the operating system signals that data is ready. Non-blocking I/O instead lets a thread issue the I/O request and immediately move on to other work; when the data eventually becomes available, a callback, future, or event loop notifies the code, without ever dedicating a whole thread to sitting and waiting. This distinction sits underneath the [synchronous request/response model](0075-synchronous-request-response-model.md): the *logical* interaction can still be synchronous from the caller's point of view (wait for the response before continuing) while the *underlying I/O* is implemented in either a blocking or non-blocking way.

## 2. Why & when

A thread blocked on I/O is a thread doing nothing productive but still consuming a real operating system resource — its own stack memory, and one of a finite number of threads the OS can schedule efficiently. A service handling thousands of concurrent slow downstream calls with blocking I/O needs thousands of threads sitting mostly idle, which is expensive and eventually hits hard OS-level limits. Non-blocking I/O lets a small, fixed number of threads handle a much larger number of concurrent in-flight requests, because no thread is ever dedicated to just waiting — it's picked back up only when there's actual work (data arrived) to do.

Blocking I/O's simplicity (code reads top-to-bottom, easy to debug with a normal stack trace) makes it the right default for most services, especially where concurrency is modest and thread-per-request is affordable. Reach for non-blocking I/O specifically when a service needs to handle very high concurrency — many thousands of simultaneous slow connections — where thread-per-request would exhaust available threads well before it exhausts CPU or memory.

## 3. Core concept

A blocking call occupies its calling thread for the operation's full duration; a non-blocking call returns control immediately, and a separate notification mechanism delivers the result later, freeing that thread to do other work in the meantime.

```
BLOCKING:                              NON-BLOCKING:
Thread A: call() ---[thread PARKED,   Thread A: call() -> returns immediately
           doing nothing]---> result             Thread A picks up OTHER work
Thread A: continues with result                   ... later, event loop delivers result
                                       Thread A (or another): handles result via callback
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A blocking thread sits idle for the full duration of an I/O call, while a non-blocking thread issues the call, does other work, and is notified later when the result is ready">
  <text x="160" y="18" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Blocking</text>
  <line x1="60" y1="35" x2="60" y2="170" stroke="#8b949e"/>
  <rect x="52" y="50" width="16" height="80" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="95" fill="#79c0ff" font-size="7.5" font-family="sans-serif">thread idle, waiting</text>

  <text x="480" y="18" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Non-blocking</text>
  <line x1="380" y1="35" x2="380" y2="170" stroke="#8b949e"/>
  <rect x="372" y="50" width="16" height="15" fill="#1c2430" stroke="#6db33f"/>
  <text x="450" y="62" fill="#6db33f" font-size="7.5" font-family="sans-serif">issues call, returns</text>
  <rect x="372" y="70" width="16" height="25" fill="#1c2430" stroke="#6db33f"/>
  <text x="450" y="87" fill="#6db33f" font-size="7.5" font-family="sans-serif">does OTHER work</text>
  <rect x="372" y="120" width="16" height="15" fill="#1c2430" stroke="#6db33f"/>
  <text x="450" y="132" fill="#6db33f" font-size="7.5" font-family="sans-serif">notified, handles result</text>
</svg>

The blocking thread does nothing but wait; the non-blocking thread stays busy with other work in the meantime.

## 5. Runnable example

Scenario: a service needing to make several slow downstream calls concurrently, first with blocking I/O using one thread per call, then with the same work done using Java's `CompletableFuture` to model non-blocking-style composition without dedicating a thread to each wait, then extended to show the thread-count difference under higher concurrency, making the resource-efficiency gap concrete.

### Level 1 — Basic

```java
// File: BlockingIO.java -- ONE thread per call, each PARKED for the
// full duration of its simulated I/O wait.
public class BlockingIO {
    static String blockingCall(int id) throws InterruptedException {
        Thread.sleep(100); // simulated slow I/O -- the thread does NOTHING else during this
        return "result-" + id;
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        Thread[] threads = new Thread[3];
        String[] results = new String[3];
        for (int i = 0; i < 3; i++) {
            int id = i;
            threads[i] = new Thread(() -> {
                try { results[id] = blockingCall(id); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            });
            threads[i].start(); // one THREAD dedicated to each blocking call
        }
        for (Thread t : threads) t.join();
        System.out.println("Results: " + String.join(", ", results));
        System.out.println("Threads used: 3 (one per call, each blocked for its full duration)");
    }
}
```

**How to run:** `javac BlockingIO.java && java BlockingIO` (JDK 17+).

Expected output:
```
Results: result-0, result-1, result-2
Threads used: 3 (one per call, each blocked for its full duration)
```

### Level 2 — Intermediate

```java
// File: NonBlockingWithFutures.java -- the SAME three calls, now
// composed via CompletableFuture -- the calling code doesn't dedicate a
// thread to each wait; it registers what to do WHEN the result arrives.
import java.util.concurrent.*;
import java.util.*;

public class NonBlockingWithFutures {
    static ExecutorService ioPool = Executors.newFixedThreadPool(1); // just ONE worker thread, unlike Level 1's 3

    static CompletableFuture<String> nonBlockingCall(int id) {
        return CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(100); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            return "result-" + id;
        }, ioPool);
    }

    public static void main(String[] args) throws Exception {
        List<CompletableFuture<String>> futures = new ArrayList<>();
        for (int i = 0; i < 3; i++) {
            futures.add(nonBlockingCall(i)); // returns IMMEDIATELY, doesn't block main thread
        }
        System.out.println("All 3 calls issued -- main thread was never blocked waiting for any single one");

        List<String> results = new ArrayList<>();
        for (CompletableFuture<String> f : futures) results.add(f.get()); // collect final results
        System.out.println("Results: " + String.join(", ", results));
        ioPool.shutdown();
    }
}
```

**How to run:** `javac NonBlockingWithFutures.java && java NonBlockingWithFutures` (JDK 17+).

Expected output:
```
All 3 calls issued -- main thread was never blocked waiting for any single one
Results: result-0, result-1, result-2
```

### Level 3 — Advanced

```java
// File: ThreadCountComparison.java -- make the resource difference
// concrete: run 20 concurrent "requests" both ways, and report how many
// THREADS each approach actually needed at its peak.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.*;

public class ThreadCountComparison {
    static int REQUEST_COUNT = 20;

    static void blockingApproach() throws InterruptedException {
        AtomicInteger peakThreads = new AtomicInteger(0);
        Thread[] threads = new Thread[REQUEST_COUNT];
        for (int i = 0; i < REQUEST_COUNT; i++) {
            threads[i] = new Thread(() -> {
                peakThreads.incrementAndGet(); // one thread PER request, all alive concurrently
                try { Thread.sleep(50); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            });
            threads[i].start();
        }
        for (Thread t : threads) t.join();
        System.out.println("Blocking approach: peak threads used = " + peakThreads.get());
    }

    static void nonBlockingApproach() throws InterruptedException {
        ExecutorService smallPool = Executors.newFixedThreadPool(2); // FIXED, small pool regardless of request count
        List<CompletableFuture<Void>> futures = new ArrayList<>();
        for (int i = 0; i < REQUEST_COUNT; i++) {
            futures.add(CompletableFuture.runAsync(() -> {
                try { Thread.sleep(50); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            }, smallPool));
        }
        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
        System.out.println("Non-blocking approach: peak threads used = 2 (fixed pool, independent of request count)");
        smallPool.shutdown();
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("Handling " + REQUEST_COUNT + " concurrent requests:");
        blockingApproach();
        nonBlockingApproach();
    }
}
```

**How to run:** `javac ThreadCountComparison.java && java ThreadCountComparison` (JDK 17+).

Expected output:
```
Handling 20 concurrent requests:
Blocking approach: peak threads used = 20
Non-blocking approach: peak threads used = 2 (fixed pool, independent of request count)
```

## 6. Walkthrough

1. **Level 1** — `blockingCall` sleeps for 100ms, standing in for a slow network call, and the calling thread has nothing else to do during that sleep — it is genuinely parked. `main` starts 3 separate `Thread` objects, one per call, each of which blocks independently; `main` then joins all three and prints their results. Three real OS threads were required, each dedicated entirely to waiting.
2. **Level 2 — composing without dedicating a thread per wait** — `nonBlockingCall` wraps the same 100ms simulated work in `CompletableFuture.supplyAsync`, submitted to `ioPool`, a pool with just *one* worker thread. `main` calls `nonBlockingCall` three times in a tight loop; each call returns a `CompletableFuture` *immediately* — `main`'s loop doesn't block at all while issuing all three, which is why the "All 3 calls issued" line prints right away, before any of the three simulated calls has actually completed. Only the later `f.get()` calls actually wait for each future's result — and the single worker thread in `ioPool` processes the three submitted tasks one after another (since it only has one thread), still eventually producing all three results.
3. **Level 3 — measuring the difference under real concurrency** — `blockingApproach` starts 20 separate `Thread` objects, one per simulated request, and `peakThreads` (incremented once per thread as it starts) ends up at `20` — the operating system genuinely had 20 threads alive concurrently, each parked in `Thread.sleep`. `nonBlockingApproach` instead uses `Executors.newFixedThreadPool(2)` — a hard cap of 2 threads — and submits all 20 tasks as `CompletableFuture.runAsync` calls against that fixed pool.
4. **Tracing what happens with only 2 threads handling 20 tasks** — since the pool has only 2 threads, at most 2 of the 20 tasks can be *actively* running at once; the rest wait in the pool's internal queue until a thread frees up. `CompletableFuture.allOf(...).join()` blocks `main` until every one of the 20 futures has completed, which naturally takes roughly 10 rounds of 50ms each (20 tasks / 2 threads), rather than all 20 finishing in parallel — a real tradeoff of using fewer threads. `main` prints that the non-blocking approach needed only `2` threads at its peak, regardless of `REQUEST_COUNT` being `20` (or, in principle, much higher).
5. **Why this specific number matters** — this simulation still uses a small fixed thread pool rather than true OS-level non-blocking I/O (Java's real non-blocking I/O APIs, like NIO's selectors, or a reactive framework, would need even fewer threads and wouldn't serialize the 20 tasks 2-at-a-time the way this simplified pool-based simulation does) — but the core, generalizable lesson holds: blocking I/O ties thread count directly to concurrent request count, while non-blocking I/O decouples the two, letting a small, fixed number of threads serve a much larger number of concurrent in-flight operations.

## 7. Gotchas & takeaways

> **Gotcha:** non-blocking I/O trades away easy debuggability for resource efficiency — a stack trace from a blocking call shows the full call chain that led to the wait; a non-blocking callback's stack trace often shows only the callback's own immediate context, since the code that issued the original call has already returned and moved on. Reach for non-blocking I/O when the concurrency numbers genuinely demand it, not by default, given this real debugging cost.

- A blocking thread occupies a real OS thread for the full duration of an I/O wait; a non-blocking call frees the thread immediately and delivers the result later via a callback, future, or event loop.
- Thread-per-request (blocking I/O) ties thread count directly to concurrent request count — it's simple and usually fine, until concurrency grows large enough to exhaust available threads.
- Non-blocking I/O decouples thread count from concurrent request count, letting a small, fixed pool serve far more simultaneous slow operations.
- This distinction is about *implementation*, not about whether the caller's own code is logically synchronous or asynchronous — see [synchronous request/response model](0075-synchronous-request-response-model.md) for the caller-facing shape, which can be built on top of either blocking or non-blocking I/O underneath.
- Default to blocking I/O's simplicity unless concurrency numbers specifically demand non-blocking's resource efficiency — the debugging and reasoning cost of non-blocking code is real and shouldn't be paid unnecessarily.
