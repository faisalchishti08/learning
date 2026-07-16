---
card: spring-integration
gi: 75
slug: r2dbc-support
title: "R2DBC support"
---

## 1. What it is

R2DBC support (`R2dbc.inboundChannelAdapter(...)`/`R2dbc.outboundChannelAdapter(...)`/`R2dbc.outboundGateway(...)`) connects a flow to a relational database using R2DBC (Reactive Relational Database Connectivity) instead of blocking JDBC (card 0064). Queries and updates return a `Mono`/`Flux` of results rather than blocking the calling thread, letting a reactive flow (built on WebFlux support, card 0055, or `FluxMessageChannel`) reach a relational database without ever blocking a thread waiting on I/O.

## 2. Why & when

You reach for R2DBC support specifically inside a reactive flow that must not block:

- **The rest of the pipeline is already reactive** — a flow built around `FluxMessageChannel` or WebFlux endpoints benefits from a database access layer that returns `Mono`/`Flux` too; mixing in a blocking JDBC call anywhere in that pipeline would tie up one of the limited event-loop threads reactive systems depend on, defeating the purpose of going reactive in the first place.
- **High concurrency with a relatively small thread pool** — reactive database access lets a modest number of threads handle a large number of concurrent database operations, since a thread isn't held hostage waiting for a slow query to return; this matters most under high concurrency where blocking JDBC's thread-per-request model would need proportionally many more threads.
- **Do not reach for R2DBC just because it's newer** — for straightforward, non-reactive flows the mature, thoroughly-understood JDBC adapter (card 0064) is simpler to reason about and has no less capability; the reactive model earns its added complexity only when the flow around it is genuinely reactive end to end.

## 3. Core concept

Think of blocking JDBC as a bank teller who serves one customer at a time, standing there doing nothing productive while a slow transaction (say, a wire transfer needing external verification) is in progress — that teller (thread) is unavailable to help anyone else until it completes. R2DBC is like a teller who, the moment a slow transaction is submitted, immediately turns to help the next customer, and comes back to the first customer only when their transaction result is actually ready — one teller effectively serving many customers by never idling on a wait.

```java
@Bean
public IntegrationFlow r2dbcInboundFlow(DatabaseClient databaseClient) {
    return IntegrationFlow.from(
            R2dbc.inboundChannelAdapter(databaseClient, "SELECT * FROM orders WHERE status = 'PENDING'")
                .rowsFetchSpecMapper((rows, meta) -> rows.map(this::mapRowToOrder)),
            e -> e.poller(Pollers.fixedDelay(5_000)))
        .handle(order -> orderService.processReactive(order)) // returns Mono<Void>, non-blocking
        .get();
}
```

Even the polling adapter's query execution returns a reactive publisher, so the poller's thread is never blocked waiting on the database round trip.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Blocking JDBC ties up a thread for the full duration of a query; R2DBC releases the thread immediately and resumes only when the result is ready, letting one thread serve many concurrent queries" >
  <text x="160" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JDBC: thread blocked for full query duration</text>
  <rect x="20" y="30" width="280" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="50" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">thread-1: [------ blocked on query ------]</text>
  <text x="160" y="80" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">thread-1 can serve nothing else meanwhile</text>

  <text x="480" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">R2DBC: thread freed, resumes on completion</text>
  <rect x="340" y="30" width="280" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="50" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">thread-1: [sub][free for other work][resume]</text>
  <text x="480" y="80" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">same thread serves other requests during the wait</text>

  <text x="480" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">One thread, many in-flight queries — no thread held hostage on I/O</text>
</svg>

R2DBC frees the thread during the wait; JDBC holds it captive for the whole round trip.

## 5. Runnable example

The scenario: querying orders reactively without blocking, simulated with `CompletableFuture` standing in for `Mono`/`Flux`-style non-blocking composition (no real R2DBC driver or reactive database connection needed to demonstrate the non-blocking chaining logic), starting with a basic async query, then chaining a downstream async processing step, then handling a query failure without ever blocking the calling thread.

### Level 1 — Basic

```java
// R2dbcQueryDemo.java
import java.util.concurrent.*;
import java.util.*;

public class R2dbcQueryDemo {
    record Order(int id, String status) {}

    // Stand-in for R2dbc.inboundChannelAdapter's non-blocking query execution.
    static CompletableFuture<List<Order>> queryPendingAsync() {
        return CompletableFuture.supplyAsync(() -> {
            System.out.println("  (querying database on a worker thread, caller thread stays free)");
            return List.of(new Order(1, "PENDING"), new Order(2, "PENDING"));
        });
    }

    public static void main(String[] args) throws Exception {
        System.out.println("Submitting query (main thread not blocked here)...");
        CompletableFuture<List<Order>> future = queryPendingAsync();
        List<Order> orders = future.get(); // only this line actually waits, to keep the demo simple
        System.out.println("Received orders: " + orders.size());
    }
}
```

How to run: `java R2dbcQueryDemo.java`. Expected output: `Submitting query (main thread not blocked here)...`, then the worker-thread message, then `Received orders: 2` — the query submission itself returns immediately with a future rather than blocking.

### Level 2 — Intermediate

```java
// R2dbcQueryDemo.java
import java.util.concurrent.*;
import java.util.*;

public class R2dbcQueryDemo {
    record Order(int id, String status) {}
    record ProcessedOrder(int id, String result) {}

    static CompletableFuture<List<Order>> queryPendingAsync() {
        return CompletableFuture.supplyAsync(() ->
            List.of(new Order(1, "PENDING"), new Order(2, "PENDING")));
    }

    // Real-world concern: the downstream processing step must also stay non-blocking, or the
    // reactive benefit of the query is lost the moment a blocking call is chained after it.
    static CompletableFuture<ProcessedOrder> processReactive(Order order) {
        return CompletableFuture.supplyAsync(() -> {
            System.out.println("  processing order " + order.id() + " asynchronously");
            return new ProcessedOrder(order.id(), "DONE");
        });
    }

    public static void main(String[] args) throws Exception {
        List<ProcessedOrder> results = queryPendingAsync()
            .thenCompose(orders -> {
                List<CompletableFuture<ProcessedOrder>> futures =
                    orders.stream().map(R2dbcQueryDemo::processReactive).toList();
                return CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
                    .thenApply(v -> futures.stream().map(CompletableFuture::join).toList());
            })
            .get();

        results.forEach(r -> System.out.println("Result: order " + r.id() + " -> " + r.result()));
    }
}
```

How to run: `java R2dbcQueryDemo.java`. Expected output: both orders process concurrently (their print order may interleave), followed by two `Result: order N -> DONE` lines — the query and the downstream handling both stay expressed as chained, non-blocking futures rather than either step blocking the caller.

### Level 3 — Advanced

```java
// R2dbcQueryDemo.java
import java.util.concurrent.*;
import java.util.*;

public class R2dbcQueryDemo {
    record Order(int id, String status) {}
    record ProcessedOrder(int id, String result) {}

    static CompletableFuture<List<Order>> queryPendingAsync(boolean simulateFailure) {
        return CompletableFuture.supplyAsync(() -> {
            if (simulateFailure) throw new RuntimeException("connection pool exhausted");
            return List.of(new Order(1, "PENDING"), new Order(2, "PENDING"));
        });
    }

    static CompletableFuture<ProcessedOrder> processReactive(Order order) {
        return CompletableFuture.supplyAsync(() -> new ProcessedOrder(order.id(), "DONE"));
    }

    // Production concern: a reactive query can fail (pool exhaustion, connection drop) just
    // like a blocking one -- handle the error in the reactive chain itself (exceptionally /
    // onErrorResume equivalent) rather than letting it propagate as an uncaught async failure.
    static CompletableFuture<List<ProcessedOrder>> runPipeline(boolean simulateFailure) {
        return queryPendingAsync(simulateFailure)
            .thenCompose(orders -> {
                List<CompletableFuture<ProcessedOrder>> futures =
                    orders.stream().map(R2dbcQueryDemo::processReactive).toList();
                return CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
                    .thenApply(v -> futures.stream().map(CompletableFuture::join).toList());
            })
            .exceptionally(ex -> {
                System.out.println("Query failed (" + ex.getCause().getMessage() + "), returning empty result set");
                return List.of();
            });
    }

    public static void main(String[] args) throws Exception {
        System.out.println("-- healthy run --");
        runPipeline(false).get().forEach(r -> System.out.println("Result: " + r));

        System.out.println("-- failing run --");
        List<ProcessedOrder> fallback = runPipeline(true).get();
        System.out.println("Fallback result count: " + fallback.size());
    }
}
```

How to run: `java R2dbcQueryDemo.java`. Expected output: the healthy run prints two processed results; the failing run prints `Query failed (connection pool exhausted), returning empty result set` followed by `Fallback result count: 0` — the error handled entirely within the reactive chain, with no blocking wait and no uncaught exception propagating out of the pipeline.

## 6. Walkthrough

Trace a reactive query through to processed results, including the failure path.

1. **Poller fires**: `R2dbc.inboundChannelAdapter`'s poller triggers the configured query, which R2DBC executes by returning a `Publisher` (`Mono`/`Flux`) immediately — the calling thread is never held waiting for the database round trip to complete.
2. **Subscription and execution**: Spring Integration subscribes to that publisher; the actual database work happens asynchronously, and results arrive as they become available rather than all at once after a blocking wait.
3. **Row mapping**: as rows arrive, the configured mapper converts each into a domain object (`Order`), the same conceptual step as `RowMapper` in the JDBC adapter, just expressed reactively.
4. **Reactive downstream processing**: each mapped object flows to a `.handle(...)` step that itself returns a `Mono`/`Flux` (as in `processReactive`), so the non-blocking property holds all the way through the pipeline rather than being undone by a blocking call further downstream.
5. **Success path**: once all reactive steps complete, the final results are available to whatever consumes them — a response to an HTTP caller, a further processing step, or storage.
6. **Failure path**: if the query or a downstream reactive step fails (connection pool exhaustion, query error), the reactive chain's own error-handling operator (`exceptionally`/`onErrorResume` in Reactor terms) catches it and produces a fallback result, keeping the failure contained within the reactive pipeline rather than surfacing as an unhandled exception on some unrelated thread.

```
poller tick
  -> R2DBC query returns Publisher immediately (thread not blocked)
    -> rows arrive asynchronously -> mapped to Order objects
      -> reactive downstream processing (also non-blocking)
        success -> processed results
        failure -> reactive error handler -> fallback result
```

## 7. Gotchas & takeaways

> **Gotcha:** chaining even a single blocking call (a synchronous JDBC lookup, a blocking HTTP client call, a `Thread.sleep`) anywhere inside an otherwise-reactive R2DBC pipeline can starve the small thread pool reactive systems rely on, causing seemingly unrelated requests elsewhere in the application to stall — going reactive is an all-the-way-through commitment, not something that can be partially adopted without care.

- R2DBC is worth its added complexity specifically when the surrounding flow is genuinely reactive (WebFlux, `FluxMessageChannel`); bolting it onto an otherwise blocking, thread-per-request flow gains little while adding a less mature ecosystem and driver set to depend on.
- Reactive error handling must happen inside the reactive chain itself; a `try/catch` wrapped around only the initial call will not catch an error that surfaces later, asynchronously, deep in a chained pipeline.
- R2DBC drivers are database-specific, similarly to JDBC drivers, but the R2DBC driver ecosystem is younger and narrower — verify driver maturity and feature parity for the specific database in use before committing to it for a critical path.
- Prefer JDBC (card 0064) for straightforward, low-concurrency, non-reactive flows; reach for R2DBC when the concurrency profile and the rest of the architecture specifically call for a non-blocking database access layer.
