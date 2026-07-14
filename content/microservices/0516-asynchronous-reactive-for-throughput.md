---
card: microservices
gi: 516
slug: asynchronous-reactive-for-throughput
title: "Asynchronous & reactive for throughput"
---

## 1. What it is

**Asynchronous and reactive processing** means a service handles a request without dedicating a thread to sit idle while it waits for a slow operation (a database call, a downstream HTTP call, a disk read) to finish. Instead, the thread is freed to handle other work immediately, and a callback, future, or reactive stream picks up the result once it's ready. This is different from the traditional "one thread per request, blocked until done" model, and it exists specifically to let a service handle far more concurrent requests than it has threads, because most of a request's lifetime in a distributed system is spent *waiting* on I/O, not computing.

## 2. Why & when

You reach for asynchronous or reactive processing when a service's throughput is limited not by CPU, but by how many requests can be in flight waiting on I/O at once:

- **Traditional blocking servers tie up one thread per in-flight request.** If a downstream call takes 200ms and the thread pool has 200 threads, the server can only have 200 requests in flight at once — the 201st request queues, even though the CPU is almost entirely idle, because every thread is simply parked waiting on network I/O.
- **Async/reactive processing decouples "requests in flight" from "threads in use."** A small, fixed pool of threads (often one per CPU core) can service thousands of concurrent in-flight requests, because a thread only does work when there's actual work to do — CPU-bound computation — and hands off waiting to the underlying I/O mechanism.
- **This matters most for I/O-heavy, high-fan-out services** — an API gateway calling five downstream services per request, or a service under bursty traffic where waiting-thread exhaustion is the actual bottleneck, benefit the most. A CPU-bound batch job gets little to no benefit, since there's no waiting to reclaim.
- **The cost is real: reactive code is harder to write, read, and debug** — stack traces fragment across callbacks, and simple sequential logic becomes a graph of composed asynchronous stages. It's a deliberate trade of code complexity for throughput and resource efficiency, not a default to reach for everywhere.

## 3. Core concept

Think of a restaurant with ten waiters (threads) and a hundred tables (requests). If each waiter stands at one table the entire time the kitchen cooks that table's order — unable to serve anyone else — then only ten tables can ever be served at once, no matter how fast the kitchen actually is. A reactive waiter instead takes the order, hands it to the kitchen, and immediately goes to serve a different table; when a dish is ready, whichever waiter is free at that moment delivers it. Ten waiters can now keep far more than ten tables moving, because none of them stand around waiting on the kitchen — the kitchen's queue holds the waiting, not the waiter.

Concretely:

1. **A blocking call ties up the calling thread until the operation completes** — the thread cannot do anything else, even though it's doing nothing but waiting.
2. **A non-blocking call returns immediately** with a stand-in handle for the eventual result — a `Future`, `CompletableFuture`, or reactive `Mono`/`Flux` — and the thread is freed to pick up other work right away.
3. **When the underlying operation completes** (the database responds, the HTTP call returns), a callback or subscriber is invoked with the result, often on a different thread from a small event-loop or worker pool, not the original caller's thread.
4. **Throughput scales with how much I/O-wait can be reclaimed**, not with the number of threads — a handful of threads processing thousands of pending I/O completions can vastly outperform hundreds of threads each blocked on one I/O operation.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Blocking model ties one thread per waiting request; reactive model frees the thread while waiting, serving many more requests with the same threads">
  <text x="150" y="24" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Blocking: thread parked</text>
  <rect x="30" y="40" width="240" height="30" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">thread-1 -- WAITING on I/O (idle)</text>
  <rect x="30" y="80" width="240" height="30" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">thread-2 -- WAITING on I/O (idle)</text>
  <text x="150" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">only N threads = only N requests in flight</text>

  <text x="510" y="24" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Reactive: thread freed</text>
  <rect x="390" y="40" width="240" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">event-loop -- serving request A, B, C...</text>
  <rect x="390" y="80" width="240" height="70" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="510" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">1000s of pending I/O completions</text>
  <text x="510" y="116" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">tracked without a dedicated thread each</text>
  <text x="510" y="132" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">callback fires when data is ready</text>
  <text x="510" y="180" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">few threads = many more requests in flight</text>
</svg>

Blocking ties a thread to every in-flight wait; reactive frees the thread and tracks the wait elsewhere, so the same threads serve far more concurrent requests.

## 5. Runnable example

Scenario: a service that calls a slow downstream dependency to fetch a price quote for an order. We start with a simple blocking call, extend it to a non-blocking `CompletableFuture` version that frees the calling thread, then handle the hard case: composing multiple concurrent downstream calls with a timeout and fallback, so one slow dependency doesn't stall the whole response.

### Level 1 — Basic

```java
// File: QuoteServiceBasic.java -- a BLOCKING call: the calling thread
// is parked for the entire duration of the "downstream" call.
public class QuoteServiceBasic {
    static double fetchQuoteBlocking(String item) throws InterruptedException {
        System.out.println("[" + Thread.currentThread().getName() + "] calling downstream for " + item + "...");
        Thread.sleep(200); // simulates network latency to a pricing service
        return 42.50;
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        double price = fetchQuoteBlocking("widget");
        System.out.println("Got price $" + price + " after " + (System.currentTimeMillis() - start) + "ms -- thread was blocked the whole time");
    }
}
```

How to run: `java QuoteServiceBasic.java`

`Thread.sleep(200)` stands in for a slow network call. The calling thread (`main`) does nothing else during those 200ms — it's entirely occupied by the wait, which is the core limitation this pattern has.

### Level 2 — Intermediate

```java
// File: QuoteServiceAsync.java -- a NON-BLOCKING version: the calling
// thread is freed immediately, and a separate executor thread completes
// the future when the "downstream" work finishes.
import java.util.concurrent.*;

public class QuoteServiceAsync {
    static ExecutorService downstreamPool = Executors.newFixedThreadPool(2);

    static CompletableFuture<Double> fetchQuoteAsync(String item) {
        return CompletableFuture.supplyAsync(() -> {
            System.out.println("[" + Thread.currentThread().getName() + "] calling downstream for " + item + "...");
            try { Thread.sleep(200); } catch (InterruptedException e) { throw new RuntimeException(e); }
            return 42.50;
        }, downstreamPool);
    }

    public static void main(String[] args) throws Exception {
        long start = System.currentTimeMillis();
        CompletableFuture<Double> future = fetchQuoteAsync("widget");
        System.out.println("[" + Thread.currentThread().getName() + "] call returned immediately -- free to do other work now");
        double price = future.get(); // only blocks HERE, at the point we actually need the result
        System.out.println("Got price $" + price + " after " + (System.currentTimeMillis() - start) + "ms");
        downstreamPool.shutdown();
    }
}
```

How to run: `java QuoteServiceAsync.java`

`supplyAsync` submits the slow work to `downstreamPool` and returns a `CompletableFuture` immediately — the `main` thread prints its "free to do other work" line before the 200ms wait even finishes. Only `future.get()` blocks, and only if we actually need the result before it's ready; in a real server, the calling thread would instead register a callback (`.thenAccept(...)`) and return to serving other requests, never blocking at all.

### Level 3 — Advanced

```java
// File: QuoteServiceComposed.java -- composes TWO concurrent downstream
// calls (price + inventory), each with its OWN timeout and fallback,
// so one slow or failing dependency doesn't stall or break the response.
import java.util.concurrent.*;

public class QuoteServiceComposed {
    static ExecutorService pool = Executors.newFixedThreadPool(4);

    static CompletableFuture<Double> fetchPrice(String item, boolean simulateSlow) {
        return CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(simulateSlow ? 2000 : 100); } catch (InterruptedException e) { throw new RuntimeException(e); }
            return 42.50;
        }, pool).orTimeout(500, TimeUnit.MILLISECONDS)
         .exceptionally(ex -> {
             System.out.println("[price] timed out or failed (" + ex.getClass().getSimpleName() + ") -- using fallback price");
             return -1.0; // fallback: "price unavailable" sentinel
         });
    }

    static CompletableFuture<Integer> fetchInventory(String item) {
        return CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(100); } catch (InterruptedException e) { throw new RuntimeException(e); }
            return 17;
        }, pool).orTimeout(500, TimeUnit.MILLISECONDS)
         .exceptionally(ex -> -1); // fallback: "inventory unavailable" sentinel
    }

    public static void main(String[] args) throws Exception {
        // simulate the pricing dependency being slow (2s) this time, well past its 500ms budget
        CompletableFuture<Double> priceFuture = fetchPrice("widget", true);
        CompletableFuture<Integer> inventoryFuture = fetchInventory("widget");

        CompletableFuture<Void> combined = CompletableFuture.allOf(priceFuture, inventoryFuture);
        combined.get(3, TimeUnit.SECONDS); // overall safety net for the composed call

        double price = priceFuture.get();
        int inventory = inventoryFuture.get();
        System.out.println("Response: price=" + (price < 0 ? "unavailable" : "$" + price)
            + ", inventory=" + (inventory < 0 ? "unavailable" : inventory));
        pool.shutdown();
    }
}
```

How to run: `java QuoteServiceComposed.java`

`orTimeout(500, ms)` bounds each individual downstream call so a single slow dependency can't hold the response hostage, and `.exceptionally(...)` supplies a fallback value instead of propagating the failure — the composed response is built from whatever succeeded, degrading gracefully rather than failing entirely. `fetchInventory` returns in 100ms and succeeds normally; `fetchPrice` is forced to take 2s, blows past its 500ms budget, and the timeout kicks in, so the final response reports the price as unavailable while still returning a valid inventory count. This is the production-flavored shape of async composition: not just "don't block," but "don't let one slow dependency's wait become everyone's problem."

## 6. Walkthrough

Trace `QuoteServiceComposed.main` end to end:

1. **`main` calls `fetchPrice("widget", true)`.** This immediately submits a task to `pool` and returns a `CompletableFuture<Double>` — `main` does not block here. The returned future already has `.orTimeout(500ms)` and `.exceptionally(...)` chained onto it, so its eventual behavior (timeout -> fallback) is fully wired up before any work has even started.
2. **`main` calls `fetchInventory("widget")`.** Same shape: submitted to the pool, returns immediately with its own future.
3. **Concurrently, on separate pool threads:** the inventory task sleeps 100ms then returns `17`; the price task sleeps 2000ms (simulating a slow dependency).
4. **`main` calls `CompletableFuture.allOf(priceFuture, inventoryFuture).get(3, SECONDS)`** — this is the one deliberate blocking point, waiting for *both* futures to reach a terminal state (success or fallback), bounded overall by 3 seconds.
5. **At the 500ms mark, `priceFuture`'s `orTimeout` fires** because the price task is still sleeping (it needs 2000ms). This completes `priceFuture` exceptionally with a `TimeoutException`, which `.exceptionally(...)` catches and converts into the fallback value `-1.0`, printing `[price] timed out or failed (TimeoutException) -- using fallback price`.
6. **`inventoryFuture` completes normally at ~100ms** with `17`, well before its own 500ms budget.
7. **`allOf(...)` resolves once both are done** (the price future resolved via fallback at 500ms, not the full 2000ms) — so `combined.get(3, SECONDS)` returns at roughly 500ms, not 2000ms, because the timeout capped the wait.
8. **`main` reads both results** — `price = -1.0` (interpreted as "unavailable"), `inventory = 17` — and prints the final composed response: `Response: price=unavailable, inventory=17`.

Response shape (conceptually, as JSON this composed result might become at an HTTP layer):

```json
{ "item": "widget", "price": "unavailable", "inventory": 17 }
```

The key structural point: nothing in this flow ever dedicates a thread to sitting and waiting the full 2000ms for the slow price call. The pool thread running that task is the only one occupied by it, and even that thread's result is discarded in favor of the timeout-driven fallback — the caller-facing behavior is bounded by the 500ms budget, not by however slow the flakiest dependency happens to be that day.

## 7. Gotchas & takeaways

> **Gotcha:** switching to async/reactive code without changing anything else is a false economy — if the async pipeline still funnels everything through a single-threaded downstream client, or a downstream call itself blocks internally, you've added complexity without adding concurrency. Every hop in the chain has to be non-blocking for the throughput benefit to actually materialize.

- Async/reactive processing decouples "requests in flight" from "threads consumed," letting a small thread pool serve far more concurrent I/O-bound work than a blocking model with the same thread count.
- It earns its complexity cost on I/O-heavy, high-fan-out services — not on CPU-bound work, where there's no waiting to reclaim.
- Always pair concurrent downstream calls with per-call timeouts and fallbacks (as in Level 3) — composing calls without bounding each one just means one slow dependency stalls the whole composed response instead of one thread.
- Debugging reactive code is harder: stack traces fragment across callbacks and thread boundaries, so invest in structured logging/tracing (correlation IDs) to keep a composed async flow followable in production.
