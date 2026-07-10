---
card: java
gi: 879
slug: completablefuture-creation-supplyasync-runasync
title: CompletableFuture creation (supplyAsync/runAsync)
---

## 1. What it is

`CompletableFuture<T>` is Java's richer, composable alternative to a plain `Future`: it can be created, completed, chained, and combined without needing an explicit `ExecutorService` reference at every call site. `CompletableFuture.supplyAsync(Supplier<T>)` starts an asynchronous computation that *produces* a value, returning immediately with a `CompletableFuture<T>` that completes once the supplier finishes. `CompletableFuture.runAsync(Runnable)` does the same for a task that produces no result (`CompletableFuture<Void>`). Both have overloads accepting an explicit `Executor`; without one, they run on the shared `ForkJoinPool.commonPool()`.

## 2. Why & when

`supplyAsync`/`runAsync` are the entry points for building an asynchronous pipeline — use `supplyAsync` when the very first step of a chain needs to fetch or compute a value asynchronously (a database query, an HTTP call, an expensive calculation), and `runAsync` when the first step just needs to happen asynchronously without producing a result (writing a log line, firing a notification). The real value of `CompletableFuture` over a plain `Future` shows up once you start chaining (`thenApply`, `thenCompose`) or combining (`thenCombine`, `allOf`) — see the related tutorials — but every such chain has to start somewhere, and `supplyAsync`/`runAsync` are that starting point. Passing your own `Executor` (rather than relying on the shared common pool) matters whenever the task might block on I/O or run long, since the common pool is shared JVM-wide and starving it can silently slow down unrelated code, including parallel streams, that also uses it by default.

## 3. Core concept

```java
// Produces a value asynchronously, on the common pool by default:
CompletableFuture<Integer> priceFuture = CompletableFuture.supplyAsync(() -> fetchPrice("AAPL"));

// Runs a side-effecting task asynchronously, with an explicit executor:
ExecutorService ioPool = Executors.newFixedThreadPool(8);
CompletableFuture<Void> logFuture = CompletableFuture.runAsync(() -> writeAuditLog("started"), ioPool);

int price = priceFuture.join(); // blocks for the result (join() is get() without checked exceptions)
```

Both factory methods return immediately; the actual work runs on a separate thread (from the specified or default executor), and the caller decides when (and whether) to block for the result.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="supplyAsync submits a Supplier to an executor and returns a CompletableFuture immediately; the supplier runs concurrently and eventually completes the future with its result">
  <rect x="20" y="20" width="220" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="130" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">supplyAsync(supplier, executor)</text>

  <rect x="280" y="20" width="160" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="360" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">returns immediately</text>

  <rect x="480" y="20" width="140" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">CompletableFuture&lt;T&gt;</text>

  <rect x="130" y="100" width="220" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="240" y="125" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">supplier runs on executor thread</text>

  <line x1="130" y1="60" x2="240" y2="98" stroke="#f0883e" stroke-width="2" marker-end="url(#a15)"/>
  <line x1="240" y1="100" x2="550" y2="62" stroke="#6db33f" stroke-width="2" stroke-dasharray="4" marker-end="url(#a15)"/>
  <text x="400" y="90" fill="#6db33f" font-size="10" font-family="sans-serif">eventually completes the future</text>
  <defs><marker id="a15" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*The call returns before the work is done; the future is completed later, asynchronously, by whichever thread the executor assigns.*

## 5. Runnable example

Scenario: fetching a user's profile data to build a welcome message, growing from a blocking, synchronous version, to `supplyAsync` for the fetch plus `runAsync` for a parallel audit log, to using a dedicated executor instead of the shared common pool for I/O-bound work.

### Level 1 — Basic

```java
public class SynchronousBaseline {
    static String fetchUserName(int userId) {
        try { Thread.sleep(100); } catch (InterruptedException ignored) {}
        return "user-" + userId;
    }

    public static void main(String[] args) {
        long start = System.currentTimeMillis();
        String name = fetchUserName(42); // BLOCKS the main thread for the full 100ms
        System.out.println("welcome, " + name + "!");
        System.out.println("elapsed ~" + (System.currentTimeMillis() - start) + "ms");
    }
}
```

**How to run:** `java SynchronousBaseline.java` (JDK 17+).

Expected output shape:
```
welcome, user-42!
elapsed ~100ms
```

Simple, but the main thread is fully blocked for the entire fetch — it can do nothing else, and there's no way to run this concurrently with other independent work.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class SupplyAsyncAndRunAsync {
    static String fetchUserName(int userId) {
        try { Thread.sleep(100); } catch (InterruptedException ignored) {}
        return "user-" + userId;
    }

    static void writeAuditLog(String message) {
        try { Thread.sleep(30); } catch (InterruptedException ignored) {}
        System.out.println("[audit] " + message);
    }

    public static void main(String[] args) {
        long start = System.currentTimeMillis();

        CompletableFuture<String> nameFuture = CompletableFuture.supplyAsync(() -> fetchUserName(42));
        CompletableFuture<Void> logFuture = CompletableFuture.runAsync(() -> writeAuditLog("profile lookup started"));

        String name = nameFuture.join(); // blocks HERE, but the fetch already ran concurrently with the log write
        logFuture.join(); // ensure the audit log finished too before proceeding

        System.out.println("welcome, " + name + "!");
        System.out.println("elapsed ~" + (System.currentTimeMillis() - start) + "ms (fetch and log ran concurrently)");
    }
}
```

**How to run:** `java SupplyAsyncAndRunAsync.java`.

Expected output shape:
```
[audit] profile lookup started
welcome, user-42!
elapsed ~100ms (fetch and log ran concurrently)
```

The real-world concern added: the 100ms fetch and the 30ms audit log now run concurrently on the shared common pool, rather than sequentially — total elapsed time is close to the *slower* of the two (100ms), not their sum (130ms), since `supplyAsync` and `runAsync` both return immediately and the two tasks proceed in parallel.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class DedicatedExecutorForIo {
    static String fetchUserName(int userId) {
        try { Thread.sleep(100); } catch (InterruptedException ignored) {}
        return "user-" + userId;
    }

    static void writeAuditLog(String message) {
        try { Thread.sleep(30); } catch (InterruptedException ignored) {}
        System.out.println("[audit] " + message + " on " + Thread.currentThread().getName());
    }

    public static void main(String[] args) throws Exception {
        // A dedicated pool for I/O-bound work, sized generously and separate from the
        // shared ForkJoinPool.commonPool() -- so a slow fetch here can't starve unrelated
        // code elsewhere in the JVM that also relies on the common pool (e.g. parallel streams).
        ExecutorService ioPool = Executors.newFixedThreadPool(8);

        CompletableFuture<String> nameFuture = CompletableFuture.supplyAsync(() -> fetchUserName(42), ioPool);
        CompletableFuture<Void> logFuture = CompletableFuture.runAsync(() -> writeAuditLog("profile lookup started"), ioPool);

        String name = nameFuture.join();
        logFuture.join();

        System.out.println("welcome, " + name + "!");
        System.out.println("used thread from dedicated ioPool, not the shared commonPool");

        ioPool.shutdown();
        ioPool.awaitTermination(5, TimeUnit.SECONDS);
    }
}
```

**How to run:** `java DedicatedExecutorForIo.java`.

Expected output shape (thread name confirms the dedicated pool was used):
```
[audit] profile lookup started on pool-1-thread-2
welcome, user-42!
used thread from dedicated ioPool, not the shared commonPool
```

This adds the production-flavored hard case: explicitly passing a dedicated `ExecutorService` to both `supplyAsync` and `runAsync`, instead of relying on the default `ForkJoinPool.commonPool()`. The common pool is shared across the entire JVM (including parallel streams and any other unrelated `CompletableFuture` chains that don't specify their own executor) — a slow or blocking task run there can unexpectedly delay other, seemingly unrelated code. Using a dedicated pool for I/O-bound work isolates that risk and lets you size the pool appropriately for the workload (see [thread pool sizing strategies](0876-thread-pool-sizing-strategies.md)).

## 6. Walkthrough

Tracing `DedicatedExecutorForIo.main`:

1. `ioPool` is created as an explicit 8-thread fixed pool, separate from the JVM-wide `ForkJoinPool.commonPool()`.
2. `CompletableFuture.supplyAsync(() -> fetchUserName(42), ioPool)` submits the fetch to `ioPool` and returns immediately with a `CompletableFuture<String>` — no blocking happens here; a thread from `ioPool` begins executing `fetchUserName` concurrently with the rest of `main`.
3. `CompletableFuture.runAsync(() -> writeAuditLog(...), ioPool)` similarly submits the audit-log write to `ioPool` and returns immediately with a `CompletableFuture<Void>` — this runs on a *different* thread from the same pool, concurrently with the fetch.
4. `nameFuture.join()` blocks `main` until `fetchUserName` completes (~100ms) and returns its result, `"user-42"`.
5. `logFuture.join()` blocks (likely returning immediately by this point, since the 30ms log write finished well before the 100ms fetch did) confirming the audit log task also completed.
6. `main` prints the welcome message and confirms via the earlier printed thread name (`pool-1-thread-2`, matching `ioPool`'s naming convention, not the common pool's `ForkJoinPool.commonPool-worker-N` naming) that the work ran on the dedicated pool.
7. `ioPool.shutdown()` and `awaitTermination` cleanly release the dedicated pool's threads before the program exits — since it's an explicitly created resource, it's the caller's responsibility to shut it down, unlike the shared common pool, which is never explicitly shut down by application code.

## 7. Gotchas & takeaways

> **Gotcha:** the default executor for `supplyAsync`/`runAsync` (when no `Executor` argument is given) is `ForkJoinPool.commonPool()` — the *same* pool used internally by parallel streams and other JVM facilities. A long-running or blocking task submitted there without an explicit executor can starve unrelated code elsewhere in the same JVM process that also depends on the common pool's threads being available.

- `supplyAsync` starts an async computation that produces a value; `runAsync` starts one that doesn't — both return a `CompletableFuture` immediately, without blocking the calling thread.
- Without an explicit `Executor` argument, both run on the shared `ForkJoinPool.commonPool()` — fine for short, CPU-bound work, risky for anything that blocks on I/O or runs long.
- Pass a dedicated `Executor` for I/O-bound or long-running tasks to avoid starving the shared common pool used elsewhere in the JVM.
- `join()` is like `get()` but throws an unchecked `CompletionException` instead of a checked `ExecutionException` — convenient in lambda-heavy chains where checked exceptions are awkward to propagate.
- `supplyAsync`/`runAsync` are just the starting point — the real power of `CompletableFuture` comes from chaining these results with [`thenApply`/`thenCompose`](0880-completablefuture-chaining-thenapply-thenaccept-thencompose.md) and combining multiple futures with [`thenCombine`/`allOf`](0881-completablefuture-combining-thencombine-allof-anyof.md).
