---
card: java
gi: 398
slug: callable-future
title: Callable & Future
---

## 1. What it is

`Callable<V>` is a functional interface, like `Runnable`, but with two key differences: its single method, `call()`, **returns a value** of type `V`, and it's allowed to **throw a checked exception**. `Future<V>` is the handle you get back from submitting a `Callable` to an `ExecutorService` — it represents a result that isn't ready yet. `Future` lets you check if the task is done (`isDone()`), block until it finishes and get the result (`get()`, with an optional timeout), or attempt to stop it early (`cancel()`).

## 2. Why & when

`Runnable.run()` returns `void` and can't throw checked exceptions — fine for fire-and-forget work, but useless when you need a result back from a background computation (calling an API, querying a database, running a calculation). Before `Callable`/`Future`, getting a result out of a background thread meant manually writing to a shared, synchronized variable and inventing your own way to signal "it's done."

`Callable` and `Future` solve this cleanly: submit a `Callable<V>`, get back a `Future<V>` immediately (non-blocking), keep doing other work, and call `.get()` whenever you actually need the value — at which point it blocks only if the result isn't ready yet. You reach for this any time you're kicking off concurrent work that produces an answer: parallel API calls, background computations, or any task where "fire and forget" (`Runnable`) isn't enough.

## 3. Core concept

Think of a `Future` as a **restaurant pager**. You place your order (submit the `Callable`), and instead of waiting at the counter, you get a buzzing pager (the `Future`) and go sit down. You can glance at it anytime to see if it's ready (`isDone()`), or you can just wait for it to buzz (`get()`, which blocks). If you decide you don't want the order anymore, you can try to cancel it (`cancel()`) — though if the kitchen has already started cooking, cancelling might not stop it.

```java
Callable<Integer> task = () -> {
    Thread.sleep(100);
    return 42;                 // Callable: can RETURN a value
};

Future<Integer> future = executor.submit(task); // returns immediately, task runs in background
// ... do other work here while the task runs ...
Integer result = future.get(); // blocks HERE until the task finishes, then returns 42
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="submit returns a Future immediately; get blocks until the Callable's result is ready">
  <rect x="8" y="8" width="624" height="184" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="180" height="44" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="57" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">main thread</text>

  <rect x="30" y="120" width="180" height="44" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="147" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">worker thread runs call()</text>

  <line x1="210" y1="52" x2="420" y2="52" stroke="#e6edf3" stroke-width="1.5" marker-end="url(#a1)"/>
  <text x="315" y="44" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">submit(callable) -&gt; Future (immediate)</text>

  <line x1="120" y1="74" x2="120" y2="120" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="3,3"/>

  <text x="440" y="52" fill="#8b949e" font-size="10" font-family="sans-serif">main keeps working...</text>

  <line x1="120" y1="164" x2="120" y2="190" stroke="#f85149" stroke-width="1.5" marker-end="url(#a2)"/>
  <text x="120" y="184" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">future.get() blocks until result ready</text>

  <defs>
    <marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#e6edf3"/></marker>
    <marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
</svg>

Submitting a `Callable` returns a `Future` right away; only `.get()` actually waits for the result.

## 5. Runnable example

Scenario: fetching the current price for a product from three supplier APIs and picking the cheapest — the same three-supplier price check, evolved from a blocking `.get()`, through a timeout-protected version, to one that also cancels slow suppliers instead of waiting forever.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class PriceCheckBasic {
    static int fetchPrice(String supplier) throws InterruptedException {
        Thread.sleep(100); // simulates a network call
        return supplier.equals("SupplierB") ? 42 : 55;
    }

    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(3);

        Callable<Integer> priceA = () -> fetchPrice("SupplierA");
        Callable<Integer> priceB = () -> fetchPrice("SupplierB");
        Callable<Integer> priceC = () -> fetchPrice("SupplierC");

        Future<Integer> futureA = pool.submit(priceA);
        Future<Integer> futureB = pool.submit(priceB);
        Future<Integer> futureC = pool.submit(priceC);

        int cheapest = Math.min(futureA.get(), Math.min(futureB.get(), futureC.get()));
        System.out.println("Cheapest price: " + cheapest);

        pool.shutdown();
    }
}
```

**How to run:** `java PriceCheckBasic.java`

Three `Callable<Integer>` tasks run concurrently on the pool; each `.get()` blocks only until *that* supplier's price is ready, and since all three run in parallel the total wait is close to 100ms rather than 300ms.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class PriceCheckTimeout {
    static int fetchPrice(String supplier) throws InterruptedException {
        if (supplier.equals("SupplierC")) Thread.sleep(2000); // SupplierC is unusually slow
        else Thread.sleep(100);
        return supplier.equals("SupplierB") ? 42 : 55;
    }

    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(3);

        Future<Integer> futureA = pool.submit(() -> fetchPrice("SupplierA"));
        Future<Integer> futureB = pool.submit(() -> fetchPrice("SupplierB"));
        Future<Integer> futureC = pool.submit(() -> fetchPrice("SupplierC"));

        int a = futureA.get(500, TimeUnit.MILLISECONDS);
        int b = futureB.get(500, TimeUnit.MILLISECONDS);
        int cheapest = Math.min(a, b);

        try {
            int c = futureC.get(500, TimeUnit.MILLISECONDS); // won't be ready in time
            cheapest = Math.min(cheapest, c);
        } catch (TimeoutException e) {
            System.out.println("SupplierC too slow, skipping it.");
        }

        System.out.println("Cheapest price (within budget): " + cheapest);
        pool.shutdown();
    }
}
```

**How to run:** `java PriceCheckTimeout.java`

`get(500, TimeUnit.MILLISECONDS)` bounds how long we're willing to wait for each supplier — SupplierC, artificially slow, throws `TimeoutException` after 500ms rather than blocking indefinitely, letting the program move on without that price. Note: the background task itself keeps running even after the timeout; `get()` with a timeout doesn't stop the task, it just stops *waiting* for it.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class PriceCheckCancel {
    static int fetchPrice(String supplier) throws InterruptedException {
        if (supplier.equals("SupplierC")) Thread.sleep(2000);
        else Thread.sleep(100);
        return supplier.equals("SupplierB") ? 42 : 55;
    }

    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(3);

        Future<Integer> futureA = pool.submit(() -> fetchPrice("SupplierA"));
        Future<Integer> futureB = pool.submit(() -> fetchPrice("SupplierB"));
        Future<Integer> futureC = pool.submit(() -> fetchPrice("SupplierC"));

        int cheapest = Math.min(futureA.get(500, TimeUnit.MILLISECONDS),
                                 futureB.get(500, TimeUnit.MILLISECONDS));

        try {
            cheapest = Math.min(cheapest, futureC.get(500, TimeUnit.MILLISECONDS));
        } catch (TimeoutException e) {
            boolean cancelled = futureC.cancel(true); // true = interrupt it if already running
            System.out.println("SupplierC cancelled: " + cancelled + ", isCancelled: " + futureC.isCancelled());
        }

        System.out.println("Cheapest price: " + cheapest);
        pool.shutdown();
        pool.awaitTermination(1, TimeUnit.SECONDS);
    }
}
```

**How to run:** `java PriceCheckCancel.java`

`futureC.cancel(true)` doesn't just give up waiting — it actively interrupts the worker thread running `fetchPrice("SupplierC")`, since `Thread.sleep` responds to interruption by throwing `InterruptedException`, which stops that background task from wasting further pool capacity. `isCancelled()` then correctly reports `true`, and any later call to `futureC.get()` would throw `CancellationException` instead of returning a stale value.

## 6. Walkthrough

Execution starts in `main`. Three `Callable<Integer>` lambdas are submitted to the 3-thread pool; each `submit()` call returns its `Future<Integer>` immediately, without waiting, so all three background tasks (SupplierA, SupplierB, SupplierC) start running concurrently on the pool's three worker threads right away.

`futureA.get(500, TimeUnit.MILLISECONDS)` blocks the main thread, but only until SupplierA's task finishes (about 100ms) — well within the 500ms budget — returning `55`. `futureB.get(...)` similarly returns quickly, `42`. `Math.min(55, 42)` gives `cheapest = 42` so far.

Then `futureC.get(500, TimeUnit.MILLISECONDS)` is attempted inside a `try` block. SupplierC's task sleeps for 2000ms total, so 500ms into waiting, the timeout fires and `get()` throws `TimeoutException` — caught by the `catch` block. Inside the catch, `futureC.cancel(true)` is called: this sends an interrupt to SupplierC's worker thread. Since that thread is currently blocked inside `Thread.sleep(2000)`, the interrupt causes `Thread.sleep` to throw `InterruptedException` immediately, ending `fetchPrice("SupplierC")` early rather than letting it run the full 2 seconds pointlessly.

`futureC.cancel(true)` returns `true` (the task hadn't already finished, so cancellation succeeded), and `futureC.isCancelled()` also reports `true`. `cheapest` remains `42` since SupplierC's price was never incorporated. Finally, `pool.shutdown()` and `pool.awaitTermination(1, TimeUnit.SECONDS)` let the pool wind down cleanly.

Expected output:
```
SupplierC cancelled: true, isCancelled: true
Cheapest price: 42
```

## 7. Gotchas & takeaways

> `Future.get()` with **no timeout** blocks forever if the task never completes (e.g. it's stuck waiting on a resource that never arrives). In production code, prefer the timed overload, `get(timeout, unit)`, so a stuck task can't silently hang your whole application.

- `Callable<V>` is like `Runnable` but returns a value (`V call()`) and may throw checked exceptions — use it whenever you need a result back.
- `submit(Callable)` returns immediately with a `Future`; the actual work happens on a pool thread in the background.
- `future.get()` blocks until the result is ready (or throws `ExecutionException` if the task failed); the timed overload throws `TimeoutException` instead of blocking forever.
- `future.cancel(true)` attempts to interrupt a running task; `cancel(false)` only prevents it from starting if it hasn't already. Neither guarantees the task stops immediately — it depends on the task responding to interruption.
- Once cancelled, calling `.get()` on that `Future` throws `CancellationException` rather than returning a value.
