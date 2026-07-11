---
card: spring-data
gi: 90
slug: r2dbc-reactive-overview
title: "R2DBC reactive overview"
---

## 1. What it is

R2DBC (Reactive Relational Database Connectivity) is a database driver specification built from the ground up on non-blocking I/O, and Spring Data R2DBC is the Spring Data module built on top of it — every repository method returns a `Mono<T>` (zero-or-one result) or `Flux<T>` (zero-or-many results) instead of returning `T`/`List<T>` directly, and no thread ever blocks waiting for a query to finish.

```java
interface OrderRepository extends ReactiveCrudRepository<Order, Long> {
    Flux<Order> findByStatus(String status); // returns IMMEDIATELY, emits results as they arrive
}
```

## 2. Why & when

Every module covered earlier in this section — JPA, JDBC — uses the classic JDBC driver underneath, which is fundamentally blocking: the calling thread sits idle, doing nothing, while a query executes against the database. R2DBC exists because that blocking model doesn't scale well under high concurrency (each blocked thread still consumes memory and a context-switch slot) — a non-blocking driver lets one thread handle many concurrent database operations by never blocking on I/O at all.

Reach for Spring Data R2DBC specifically when:

- You're building a fully reactive application stack (e.g., using Spring WebFlux for the web layer) and want the database access layer to be non-blocking end-to-end, avoiding the thread-pool exhaustion risk of mixing blocking JDBC calls into a reactive pipeline.
- Your workload involves many concurrent, mostly-I/O-bound database operations (as opposed to CPU-heavy processing) — this is exactly the profile where non-blocking I/O provides a real throughput advantage over one-thread-per-request blocking models.
- You're prepared to accept R2DBC's tradeoffs: a younger ecosystem than JDBC, fewer available drivers, and the requirement that *everything* downstream (transaction management, testing, connection pooling) also be reactive-aware.

## 3. Core concept

```
 Blocking JDBC (JPA/JDBC modules):
   Thread calls query() -> BLOCKS, sits idle -> database responds -> thread resumes, gets result
   -- one thread PER in-flight query, however long it takes

 Non-blocking R2DBC:
   Thread calls query() -> returns a Publisher (Mono/Flux) IMMEDIATELY, thread is FREE to do other work
   -- when data arrives, a callback/subscriber is notified -- NO thread sat waiting the whole time
```

The defining difference is what the calling thread does while the query executes: block and wait, or immediately move on and get notified later.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="A blocking JDBC call parks the thread until the database responds, while a reactive R2DBC call returns immediately and notifies later">
  <text x="20" y="20" fill="#e6edf3" font-size="10" font-family="sans-serif">Blocking (JDBC)</text>
  <rect x="20" y="30" width="140" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="90" y="53" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">thread calls query()</text>
  <rect x="180" y="30" width="220" height="40" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.3" stroke-dasharray="4,3"/>
  <text x="290" y="53" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">thread BLOCKED, idle, waiting...</text>
  <rect x="420" y="30" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="495" y="53" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">result returned</text>

  <text x="20" y="110" fill="#e6edf3" font-size="10" font-family="sans-serif">Non-blocking (R2DBC)</text>
  <rect x="20" y="120" width="140" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="90" y="143" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">thread calls query()</text>
  <rect x="180" y="120" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="255" y="143" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Mono/Flux returned NOW</text>
  <rect x="350" y="120" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="425" y="143" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">thread FREE, does other work</text>
</svg>

The blocking model reserves a thread for the entire query duration; the reactive model returns a handle immediately and frees the thread to do other work.

## 5. Runnable example

The scenario: fetching orders by status, evolving from a blocking-style call demonstrating the thread-idle problem, to a reactive-style call using `CompletableFuture` to model non-blocking behavior (since real R2DBC needs a database), to composing multiple reactive calls without ever blocking a thread.

### Level 1 — Basic

Model the blocking baseline directly: the calling thread is genuinely occupied for the query's entire duration.

```java
import java.util.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

public class ReactiveOverviewLevel1 {
    // Simulates a blocking JDBC-style query: the calling thread sits here until this returns.
    static List<Order> findByStatusBlocking(String status) {
        try { Thread.sleep(100); } catch (InterruptedException ignored) {} // simulates network/DB latency
        return List.of(new Order(1, status), new Order(2, status));
    }

    public static void main(String[] args) {
        System.out.println("Thread " + Thread.currentThread().getName() + ": calling blocking query...");
        long start = System.currentTimeMillis();

        List<Order> orders = findByStatusBlocking("SHIPPED"); // THIS thread is stuck here for ~100ms

        long elapsed = System.currentTimeMillis() - start;
        System.out.println("Thread was blocked for ~" + elapsed + "ms, got " + orders.size() + " orders");
        System.out.println("During that time, THIS thread could do nothing else at all.");
    }
}
```

How to run: `java ReactiveOverviewLevel1.java`

The main thread is genuinely idle for the full ~100ms of `Thread.sleep`, standing in for network/database latency — this is exactly the cost of blocking JDBC: one thread reserved, doing nothing useful, for the entire duration of every in-flight query.

### Level 2 — Intermediate

Model the reactive equivalent using `CompletableFuture` (a widely-available async primitive, standing in for `Mono`/`Flux` since real R2DBC requires an actual reactive database driver): the calling thread returns immediately and is free to do other work while the query completes on a separate thread.

```java
import java.util.*;
import java.util.concurrent.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

public class ReactiveOverviewLevel2 {
    // Simulates a reactive R2DBC-style query: returns a "Mono" (here, a CompletableFuture) IMMEDIATELY.
    static CompletableFuture<List<Order>> findByStatusReactive(String status) {
        return CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(100); } catch (InterruptedException ignored) {} // latency happens on ANOTHER thread
            return List.of(new Order(1, status), new Order(2, status));
        });
    }

    public static void main(String[] args) throws Exception {
        System.out.println("Thread " + Thread.currentThread().getName() + ": calling reactive query...");
        long start = System.currentTimeMillis();

        CompletableFuture<List<Order>> future = findByStatusReactive("SHIPPED"); // returns IMMEDIATELY

        long elapsedBeforeBlocking = System.currentTimeMillis() - start;
        System.out.println("Call returned after only ~" + elapsedBeforeBlocking + "ms -- thread was NEVER blocked on the query itself");
        System.out.println("Thread is free to do other work right now...");

        List<Order> orders = future.get(); // only HERE do we (optionally) wait for the result, e.g. in a demo
        System.out.println("Eventually got " + orders.size() + " orders");
    }
}
```

How to run: `java ReactiveOverviewLevel2.java`

`findByStatusReactive` returns its `CompletableFuture` almost instantly (`elapsedBeforeBlocking` is near `0`), because the actual 100ms of simulated latency runs on a separate thread pool thread — the calling thread was free to do other work in between; `future.get()` here is only used to demonstrate the eventual result, not something a real reactive pipeline would typically call (that would defeat the purpose).

### Level 3 — Advanced

Compose multiple reactive calls together without ever blocking — fetching orders, then for each one fetching related data, all chained through non-blocking composition rather than sequential blocking calls.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }
class LineItemCount { long orderId; int count; LineItemCount(long orderId, int count) { this.orderId = orderId; this.count = count; } }

public class ReactiveOverviewLevel3 {
    static CompletableFuture<List<Order>> findByStatusReactive(String status) {
        return CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(50); } catch (InterruptedException ignored) {}
            return List.of(new Order(1, status), new Order(2, status));
        });
    }

    static CompletableFuture<LineItemCount> countLineItemsReactive(long orderId) {
        return CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(30); } catch (InterruptedException ignored) {}
            return new LineItemCount(orderId, (int) (orderId * 2)); // simulated count
        });
    }

    public static void main(String[] args) throws Exception {
        long start = System.currentTimeMillis();

        // Chain: fetch orders, THEN for each order (concurrently), fetch its line-item count -- no blocking anywhere.
        CompletableFuture<List<LineItemCount>> pipeline = findByStatusReactive("SHIPPED")
            .thenCompose(orders -> {
                List<CompletableFuture<LineItemCount>> counts = orders.stream()
                    .map(o -> countLineItemsReactive(o.id)) // fired CONCURRENTLY for every order
                    .collect(Collectors.toList());
                return CompletableFuture.allOf(counts.toArray(new CompletableFuture[0]))
                    .thenApply(v -> counts.stream().map(CompletableFuture::join).collect(Collectors.toList()));
            });

        System.out.println("Pipeline composed and started -- no thread blocked waiting, so far: "
            + (System.currentTimeMillis() - start) + "ms elapsed");

        List<LineItemCount> results = pipeline.get(); // wait ONLY here, at the very end, for demo purposes
        for (LineItemCount lc : results) System.out.println("Order " + lc.orderId + ": " + lc.count + " line items");
        System.out.println("Total elapsed: " + (System.currentTimeMillis() - start) + "ms");
    }
}
```

How to run: `java ReactiveOverviewLevel3.java`

The pipeline chains `findByStatusReactive` into `countLineItemsReactive` for every returned order, and — crucially — all the per-order `countLineItemsReactive` calls fire concurrently (not sequentially), because each one is an independent async operation kicked off in the `.map(...)` step before any of them are waited on. The "Pipeline composed" message prints almost instantly, well before any actual data has arrived, confirming that composing the reactive chain itself never blocks.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `findByStatusReactive("SHIPPED")` is called — it immediately returns a `CompletableFuture` and kicks off its own 50ms simulated latency on a background thread pool thread; the calling thread does not wait here.

`.thenCompose(orders -> ...)` registers a continuation to run once `orders` becomes available — but registering it does not block either. Inside that continuation (which will run later, once the orders are ready), `orders.stream().map(o -> countLineItemsReactive(o.id))` is evaluated: this calls `countLineItemsReactive` once *per order*, and because each call immediately returns its own `CompletableFuture` (kicking off its own 30ms background latency), all of these per-order lookups start running concurrently with each other, not one after another.

`CompletableFuture.allOf(...)` then registers a further continuation that waits for *all* of the per-order futures to complete, and once they have, `.thenApply(...)` collects each one's already-available result via `.join()` (safe here specifically because `allOf` already guarantees completion) into the final `List<LineItemCount>`.

Back in `main`, "Pipeline composed and started" prints almost immediately (a few milliseconds, not 50+30ms), confirming that none of this composition work involved blocking. Only `pipeline.get()` — called once, purely to keep this demo program from exiting before the async work finishes — actually waits, and by the time it returns, both orders' line-item counts are available, printed in the final loop, with total elapsed time reflecting the *overlapped* (not sequential) latencies of the fetch-then-count chain.

```
findByStatusReactive("SHIPPED")  -- returns immediately, 50ms latency runs in background
  .thenCompose(orders -> ...)     -- registered, not blocking
    countLineItemsReactive(1)     -- fired concurrently, 30ms background latency
    countLineItemsReactive(2)     -- fired concurrently, 30ms background latency (same time as above)
  allOf(...).thenApply(...)       -- waits for BOTH counts, combines results
pipeline.get()                     -- the ONLY blocking call in this program, purely for demo purposes
```

In a real Spring Data R2DBC application, `orderRepository.findByStatus("SHIPPED")` returns a `Flux<Order>` immediately — a subscriber (often Spring WebFlux itself, handling an HTTP response) is notified as each `Order` row arrives from the database, without any thread ever sitting idle waiting for the query to complete. Chaining further reactive calls (`.flatMap(order -> lineItemRepository.countByOrderId(order.id))`) composes additional non-blocking database operations the same way `thenCompose` did here, letting a single request-handling thread manage many concurrent in-flight database operations across many simultaneous HTTP requests, which is the core scalability argument for choosing R2DBC over blocking JDBC under high concurrency.

## 7. Gotchas & takeaways

> Gotcha: mixing a single blocking JDBC call into an otherwise-reactive R2DBC pipeline (e.g., calling a blocking repository method from inside a `Flux`/`Mono` chain) reintroduces exactly the thread-blocking problem R2DBC exists to avoid — and can be worse than a purely blocking application, since reactive runtimes typically use a small, fixed-size thread pool that a single blocking call can starve for every other concurrent request sharing it.

- R2DBC's defining feature is non-blocking I/O: a query call returns a `Mono`/`Flux` handle immediately, and the calling thread is never parked waiting for the database to respond.
- Spring Data R2DBC repository methods return `Mono<T>`/`Flux<T>` instead of `T`/`List<T>` — this is a genuine API shape change, not just an internal implementation detail.
- Reach for R2DBC when building a fully reactive stack under high I/O-bound concurrency; accept its narrower driver ecosystem and the requirement that everything downstream also be reactive-aware.
- Never mix a blocking call into a reactive pipeline — doing so can starve the reactive runtime's thread pool for all concurrent requests, not just the one making the blocking call.
