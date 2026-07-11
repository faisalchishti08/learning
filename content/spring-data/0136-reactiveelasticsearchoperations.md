---
card: spring-data
gi: 136
slug: reactiveelasticsearchoperations
title: "ReactiveElasticsearchOperations"
---

## 1. What it is

`ReactiveElasticsearchOperations` is the non-blocking counterpart to `ElasticsearchOperations`: every operation returns a `Mono` (single result) or `Flux` (stream of results) instead of blocking the calling thread, matching the same reactive pattern already seen for R2DBC, reactive MongoDB, and reactive Redis in earlier cards.

```java
@Autowired ReactiveElasticsearchOperations reactiveOperations;

Mono<Order> order = reactiveOperations.get("1", Order.class);
Flux<SearchHit<Order>> hits = reactiveOperations.search(
    Query.of(q -> q.match(m -> m.field("status").query("SHIPPED"))), Order.class);
```

## 2. Why & when

A search request to Elasticsearch is a network call like any other — potentially slow, especially for a complex aggregation or a large result set — and blocking a thread on it defeats a reactive application's whole purpose, exactly as blocking Redis or MongoDB calls did in earlier reactive cards. `ReactiveElasticsearchOperations` lets search be composed into a reactive pipeline alongside other non-blocking data access, without ever tying up an event-loop thread waiting on Elasticsearch's response.

Reach for `ReactiveElasticsearchOperations` when:

- The surrounding call chain is already reactive (a WebFlux endpoint building a response from a search plus other reactive sources) and a blocking `ElasticsearchOperations` call would break that chain's non-blocking guarantee.
- You want to stream a large result set with backpressure rather than materializing the whole thing into a `List` up front — `Flux<SearchHit<T>>` composes naturally with downstream reactive consumers.
- You're combining a search result with other reactive operations — enriching each hit with data fetched reactively from R2DBC or reactive Redis, via `flatMap`.

## 3. Core concept

```
 ElasticsearchOperations.search(query, Order.class)          -> SearchHits<Order>   (BLOCKS until complete)
 ReactiveElasticsearchOperations.search(query, Order.class)  -> Flux<SearchHit<Order>>  (returns IMMEDIATELY)

   Flux<SearchHit<Order>> hitsFlux = reactiveOperations.search(query, Order.class);
   // nothing has queried Elasticsearch yet -- hitsFlux is just a description of the search

   hitsFlux.subscribe(hit -> System.out.println("Got: " + hit.getContent()));
   // NOW the search actually executes, and hits stream in as they're available
```

Exactly like every other reactive Spring Data API covered so far, building the pipeline and running it are two separate steps — nothing happens until something subscribes.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A reactive search call returns a Flux immediately; the actual Elasticsearch query only executes once something subscribes">
  <rect x="20" y="20" width="200" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">reactiveOperations.search(...)</text>

  <rect x="270" y="20" width="150" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="345" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Flux&lt;SearchHit&lt;T&gt;&gt;</text>

  <line x1="220" y1="42" x2="265" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <text x="242" y="32" fill="#3fb950" font-size="8" text-anchor="middle" font-family="sans-serif">returns instantly</text>

  <rect x="470" y="20" width="140" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="540" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">.subscribe(...)</text>

  <line x1="420" y1="42" x2="465" y2="42" stroke="#8b949e" stroke-width="1.3" stroke-dasharray="4,3"/>

  <text x="320" y="110" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">the Elasticsearch query round trip only happens after .subscribe() runs</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Nothing executes against Elasticsearch until the reactive pipeline is subscribed to.

## 5. Runnable example

The scenario: searching orders reactively, evolving from a `CompletableFuture`-based stand-in for a single reactive `get`, to composing a search with a follow-up reactive lookup via `flatMap`, to streaming multiple search results concurrently and collecting them — the same conventions used in this section's earlier reactive Redis card.

### Level 1 — Basic

Model the non-blocking `get`, returning a handle immediately rather than the value directly.

```java
import java.util.*;
import java.util.concurrent.*;

public class ReactiveEsLevel1 {
    public static void main(String[] args) throws Exception {
        ReactiveElasticsearchOperations reactiveOperations = new ReactiveElasticsearchOperations();
        reactiveOperations.save(new Order("1", "SHIPPED", "Wireless mouse")).get();

        CompletableFuture<Order> orderFuture = reactiveOperations.get("1"); // returns IMMEDIATELY
        System.out.println("get() call returned immediately; result not necessarily available yet.");
        Order order = orderFuture.get(); // wait here ONLY for demo purposes
        System.out.println("Eventually resolved: " + order.status);
    }
}

class Order { String id; String status; String description; Order(String id, String status, String description) { this.id = id; this.status = status; this.description = description; } }

// Stands in for Mono<T>-returning reactive Elasticsearch operations.
class ReactiveElasticsearchOperations {
    private final Map<String, Order> index = new HashMap<>();
    CompletableFuture<String> save(Order order) {
        return CompletableFuture.supplyAsync(() -> { index.put(order.id, order); return order.id; });
    }
    CompletableFuture<Order> get(String id) {
        return CompletableFuture.supplyAsync(() -> index.get(id));
    }
}
```

How to run: `java ReactiveEsLevel1.java`

`save`/`get` both return a `CompletableFuture` (standing in for `Mono<String>`/`Mono<Order>`) immediately, mirroring exactly how `ReactiveMongoTemplate` and `ReactiveRedisTemplate` behaved in their own cards — the pattern holds consistently across every reactive Spring Data module.

### Level 2 — Intermediate

Compose a search with a follow-up reactive operation using `thenCompose`, matching how real reactive code chains a search result into a further `Mono`/`Flux` via `flatMap`.

```java
import java.util.*;
import java.util.concurrent.*;

public class ReactiveEsLevel2 {
    public static void main(String[] args) throws Exception {
        ReactiveElasticsearchOperations reactiveOperations = new ReactiveElasticsearchOperations();
        reactiveOperations.save(new Order("1", "SHIPPED", "Wireless mouse")).get();

        // Mirrors: reactiveOperations.get("1", Order.class)
        //              .flatMap(order -> reactiveInventoryLookup(order.description))
        CompletableFuture<String> pipeline = reactiveOperations.get("1")
            .thenCompose(order -> reactiveInventoryLookup(order.description));

        System.out.println("Pipeline built; nothing executed synchronously here.");
        System.out.println("Result: " + pipeline.get()); // .get() used only for demo sequencing
    }

    // Simulates a SEPARATE reactive call (e.g. to a reactive inventory service) chained after the search result.
    static CompletableFuture<String> reactiveInventoryLookup(String description) {
        return CompletableFuture.supplyAsync(() -> "in-stock: " + description.contains("mouse"));
    }
}

class Order { String id; String status; String description; Order(String id, String status, String description) { this.id = id; this.status = status; this.description = description; } }

class ReactiveElasticsearchOperations {
    private final Map<String, Order> index = new HashMap<>();
    CompletableFuture<String> save(Order order) { return CompletableFuture.supplyAsync(() -> { index.put(order.id, order); return order.id; }); }
    CompletableFuture<Order> get(String id) { return CompletableFuture.supplyAsync(() -> index.get(id)); }
}
```

How to run: `java ReactiveEsLevel2.java`

`thenCompose` chains a second asynchronous call (standing in for a reactive inventory lookup) to run only after the Elasticsearch `get` resolves — exactly the shape `Mono.flatMap` produces. No thread blocks between the two calls; the whole chain is described up front and only runs when subscribed to (here, when the demo's final `.get()` forces evaluation).

### Level 3 — Advanced

Search across multiple ids concurrently and collect the results, mirroring `Flux.fromIterable(ids).flatMap(reactiveOperations::get)` — several independent reactive lookups composed into one stream.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

public class ReactiveEsLevel3 {
    public static void main(String[] args) throws Exception {
        ReactiveElasticsearchOperations reactiveOperations = new ReactiveElasticsearchOperations();
        reactiveOperations.save(new Order("1", "SHIPPED", "Wireless mouse")).get();
        reactiveOperations.save(new Order("2", "PENDING", "Wireless keyboard")).get();
        reactiveOperations.save(new Order("3", "DELIVERED", "Office chair")).get();

        List<String> ids = List.of("1", "2", "3", "404");

        // Mirrors: Flux.fromIterable(ids).flatMap(reactiveOperations::get)
        List<CompletableFuture<Order>> futures = ids.stream()
            .map(reactiveOperations::get) // all LOOKUPS launched CONCURRENTLY
            .collect(Collectors.toList());

        System.out.println("All " + futures.size() + " lookups launched concurrently.");
        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).get(); // demo sequencing only

        List<Order> results = futures.stream().map(CompletableFuture::join).collect(Collectors.toList());
        for (int i = 0; i < ids.size(); i++) {
            Order o = results.get(i);
            System.out.println(ids.get(i) + " -> " + (o == null ? "not found" : o.description));
        }
    }
}

class Order { String id; String status; String description; Order(String id, String status, String description) { this.id = id; this.status = status; this.description = description; } }

class ReactiveElasticsearchOperations {
    private final Map<String, Order> index = new HashMap<>();
    CompletableFuture<String> save(Order order) { return CompletableFuture.supplyAsync(() -> { index.put(order.id, order); return order.id; }); }
    CompletableFuture<Order> get(String id) { return CompletableFuture.supplyAsync(() -> index.get(id)); }
}
```

How to run: `java ReactiveEsLevel3.java`

All four `get` calls are launched up front without waiting for any single one to finish, mirroring `Flux.fromIterable(ids).flatMap(...)`, which subscribes to each inner `Mono` concurrently. The missing id (`"404"`) resolves to `null`, just like a real Elasticsearch id lookup for a document that doesn't exist, without breaking the batch — the other three results are unaffected.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three orders are saved and awaited (`.get()` used only for this demo's own sequencing). Then `ids.stream().map(reactiveOperations::get)` calls `get` for all four ids in a tight loop, immediately collecting four `CompletableFuture<Order>` objects — none of the underlying lookups have necessarily finished by the time this line completes.

`CompletableFuture.allOf(...).get()` blocks (again, only for this demo) until every future has resolved. `futures.stream().map(CompletableFuture::join)` extracts each resolved value in request order. The final loop pairs each id with its result: ids `"1"`, `"2"`, `"3"` resolve to their respective `Order` objects, and `"404"` resolves to `null` since `index.get("404")` finds nothing.

```
All 4 lookups launched concurrently.
1 -> Wireless mouse
2 -> Wireless keyboard
3 -> Office chair
404 -> not found
```

In real reactive code, `Flux.fromIterable(ids).flatMap(reactiveOperations::get)` produces a `Flux<Order>` that emits results as each underlying Elasticsearch lookup completes — not necessarily in request order, since `flatMap` doesn't preserve ordering by default (use `flatMapSequential` if that matters) — and the whole pipeline runs exactly once, when whatever consumes the final `Flux` (a WebFlux response, for instance) subscribes to it.

## 7. Gotchas & takeaways

> Gotcha: like every other reactive Spring Data module in this course, `ReactiveElasticsearchOperations`'s `Flux.flatMap` doesn't guarantee output order matches input order — use `flatMapSequential` or `concatMap` if search results must come back in the same order the underlying requests were issued.

> Gotcha: mixing a blocking `ElasticsearchOperations` call into an otherwise-reactive WebFlux request path blocks a shared event-loop thread for the duration of the search — exactly the same trap called out for blocking Redis calls in the reactive Redis card, and equally damaging here, since a slow aggregation query can stall unrelated concurrent requests.

- `ReactiveElasticsearchOperations` mirrors `ElasticsearchOperations`'s API shape, but every operation returns `Mono`/`Flux` and nothing executes until something subscribes.
- It composes naturally with other reactive data sources via `flatMap`/`zipWith`, letting a search result feed directly into further reactive processing without ever blocking a thread.
- Concurrent multi-id lookups via `Flux.fromIterable(...).flatMap(...)` run in parallel by default, with `flatMapSequential` available when result order must be preserved.
- The reactive-vs-blocking choice for Elasticsearch access should match the rest of the application's stack, exactly as it did for R2DBC, reactive MongoDB, and reactive Redis in earlier sections.
