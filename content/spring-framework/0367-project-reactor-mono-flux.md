---
card: spring-framework
gi: 367
slug: project-reactor-mono-flux
title: "Project Reactor (Mono / Flux)"
---

## 1. What it is

Project Reactor is the reactive library Spring uses internally (for WebFlux, R2DBC, and reactive Kafka/RabbitMQ clients), providing two core types — `Mono<T>` (a publisher of zero or one element) and `Flux<T>` (a publisher of zero to many elements) — along with a rich set of operators (`map`, `filter`, `flatMap`, `zip`, `merge`, and dozens more) for composing asynchronous, non-blocking pipelines declaratively.

```java
Mono<Product> product = productRepository.findById(1L);
Flux<Product> allProducts = productRepository.findAll();

Flux<String> names = allProducts
    .filter(p -> p.price() > 10)
    .map(Product::name);
```

## 2. Why & when

`Mono`/`Flux` implement the Reactive Streams specification (previous card), giving them backpressure and interoperability for free, but their real value for day-to-day development is the **operator vocabulary** — a large, well-tested set of composable transformations that let you express complex asynchronous logic (combine two independent async calls, retry on failure, timeout, fall back to a default) declaratively, rather than hand-rolling callback chains or manual thread coordination.

Use `Mono` for any operation that produces at most one result — a single database lookup by ID, a single HTTP call, a computed value. Use `Flux` for anything that produces a stream of results — a list of database rows, a stream of Server-Sent Events, paginated results. The choice mirrors `Optional<T>` (zero-or-one) versus `Stream<T>`/`List<T>` (zero-to-many) in ordinary Java, but with the crucial added dimension of *time* — elements can arrive asynchronously rather than all being available upfront.

## 3. Core concept

```
Mono<T>: 0 or 1 element, then terminate (onComplete or onError)

  Mono.just(value)            — wraps an already-known value
  Mono.empty()                — completes with ZERO elements
  Mono.error(exception)       — terminates immediately with an error
  Mono.fromCallable(() -> ...) — lazily computes a value when subscribed

Flux<T>: 0 to N elements, then terminate

  Flux.just(a, b, c)          — a fixed, known sequence
  Flux.fromIterable(list)     — wraps an existing collection
  Flux.range(1, 10)           — a sequence of integers
  Flux.interval(Duration)     — an INFINITE stream, one element per tick

Common operators (both types share most of these):

  map(fn)        — transform each element (1-to-1, synchronous)
  filter(pred)   — keep only matching elements
  flatMap(fn)    — transform each element into ANOTHER Mono/Flux, flatten results
                   (the tool for "call another async operation per element")
  zip(other)     — combine with another Mono/Flux pairwise
  onErrorResume  — recover from an error with a fallback Mono/Flux
  timeout(dur)   — fail if no signal arrives within a duration
```

`flatMap` is the operator that most distinguishes reactive pipelines from simple `Stream`-style transformations — it's how you chain a second asynchronous operation (another database call, another HTTP request) that depends on the result of the first, without blocking.

## 4. Diagram

<svg viewBox="0 0 740 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="220" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">Mono (0-1) vs Flux (0-N) marble diagram</text>

  <text x="30" y="60" fill="#6db33f" font-size="11">Mono&lt;Product&gt;</text>
  <line x1="30" y1="80" x2="700" y2="80" stroke="#8b949e"/>
  <circle cx="200" cy="80" r="8" fill="#6db33f"/>
  <text x="200" y="105" text-anchor="middle" fill="#8b949e" font-size="9">onNext(product)</text>
  <line x1="230" y1="75" x2="230" y2="85" stroke="#e6edf3" stroke-width="2"/>
  <text x="230" y="105" text-anchor="middle" fill="#8b949e" font-size="9">onComplete</text>

  <text x="30" y="150" fill="#79c0ff" font-size="11">Flux&lt;Product&gt;</text>
  <line x1="30" y1="170" x2="700" y2="170" stroke="#8b949e"/>
  <circle cx="150" cy="170" r="8" fill="#79c0ff"/>
  <circle cx="300" cy="170" r="8" fill="#79c0ff"/>
  <circle cx="450" cy="170" r="8" fill="#79c0ff"/>
  <text x="300" y="195" text-anchor="middle" fill="#8b949e" font-size="9">onNext × 3, one per item, over time</text>
  <line x1="500" y1="165" x2="500" y2="175" stroke="#e6edf3" stroke-width="2"/>
  <text x="500" y="195" text-anchor="middle" fill="#8b949e" font-size="9">onComplete</text>

  <defs>
    <marker id="a43" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`Mono` emits at most one value before completing; `Flux` can emit any number of values, each potentially arriving at a different moment in time.*

## 5. Runnable example

### Level 1 — Basic

Basic `Mono`/`Flux` creation and the core `map`/`filter` operators:

```java
// BasicReactorDemo.java
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.List;

public class BasicReactorDemo {

    record Product(long id, String name, double price) {}

    public static void main(String[] args) {
        Mono<Product> productMono = Mono.just(new Product(1, "Drill", 29.99));
        productMono
            .map(p -> p.name().toUpperCase())
            .subscribe(name -> System.out.println("Mono result: " + name));

        Flux<Product> productFlux = Flux.fromIterable(List.of(
            new Product(1, "Nail", 0.50),
            new Product(2, "Drill", 29.99),
            new Product(3, "Hammer", 14.99)
        ));

        productFlux
            .filter(p -> p.price() > 10)
            .map(Product::name)
            .subscribe(name -> System.out.println("Flux item: " + name));
    }
}
```

**How to run:**
```bash
java BasicReactorDemo.java
# Mono result: DRILL
# Flux item: Drill
# Flux item: Hammer
```

`Mono.just`/`Flux.fromIterable` wrap already-known values into reactive types — useful for testing and for bridging simple synchronous data into a reactive pipeline. `map` transforms each element; `filter` on the `Flux` skips the `"Nail"` item entirely (price `0.50` fails the `> 10` predicate), so only two of the three items reach `subscribe`.

### Level 2 — Intermediate

`flatMap` for chaining a second async operation per element — the operator that models "look up more data based on this item," a very common real pattern:

```java
// FlatMapDemo.java
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;

public class FlatMapDemo {

    record Product(long id, String name, long supplierId) {}
    record Supplier(long id, String companyName) {}
    record ProductWithSupplier(String productName, String supplierName) {}

    // Simulates an async lookup — a Mono returned instead of a direct value
    static Mono<Supplier> findSupplier(long supplierId) {
        Map<Long, Supplier> suppliers = Map.of(
            100L, new Supplier(100, "Acme Tools Inc"),
            200L, new Supplier(200, "BuildCo Supplies")
        );
        return Mono.justOrEmpty(suppliers.get(supplierId));
    }

    public static void main(String[] args) {
        Flux<Product> products = Flux.just(
            new Product(1, "Drill", 100),
            new Product(2, "Hammer", 200),
            new Product(3, "Nail", 100)
        );

        products
            .flatMap(product ->
                findSupplier(product.supplierId())
                    .map(supplier -> new ProductWithSupplier(product.name(), supplier.companyName()))
            )
            .subscribe(result -> System.out.println(result));
    }
}
```

**How to run:**
```bash
java FlatMapDemo.java
# ProductWithSupplier[productName=Drill, supplierName=Acme Tools Inc]
# ProductWithSupplier[productName=Hammer, supplierName=BuildCo Supplies]
# ProductWithSupplier[productName=Nail, supplierName=Acme Tools Inc]
```

**What changed:** `flatMap` takes each `Product` and, for each one, calls `findSupplier(...)` — which itself returns a `Mono<Supplier>`, a **new, independent async operation**. If `map` had been used here instead, the result type would be `Flux<Mono<ProductWithSupplier>>` — a stream of un-resolved, nested `Mono`s, not actually usable data. `flatMap` specifically "flattens" this nesting, subscribing to each inner `Mono` and emitting its eventual result directly into the outer `Flux`, which is exactly the tool needed whenever one async operation's result feeds into another.

### Level 3 — Advanced

Combining multiple independent async sources with `zip`, adding error handling (`onErrorResume`) and a timeout, and demonstrating that reactive pipelines execute all independent branches **concurrently**, not sequentially — a key performance characteristic:

```java
// ProductionReactorDemo.java
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.time.Duration;
import java.time.Instant;

public class ProductionReactorDemo {

    record Product(long id, String name, double price) {}
    record Inventory(long productId, int stockLevel) {}
    record Review(long productId, double averageRating) {}
    record ProductDetail(String name, double price, int stock, double rating) {}

    static Mono<Product> fetchProduct(long id) {
        return Mono.fromCallable(() -> {
            simulateSlowCall(300);
            return new Product(id, "Drill", 29.99);
        }).subscribeOn(Schedulers.boundedElastic());
    }

    static Mono<Inventory> fetchInventory(long id) {
        return Mono.fromCallable(() -> {
            simulateSlowCall(200);
            return new Inventory(id, 15);
        }).subscribeOn(Schedulers.boundedElastic());
    }

    static Mono<Review> fetchReviews(long id) {
        return Mono.fromCallable(() -> {
            simulateSlowCall(400);
            if (id == 99) throw new RuntimeException("Review service unavailable");
            return new Review(id, 4.5);
        })
        .subscribeOn(Schedulers.boundedElastic())
        .timeout(Duration.ofSeconds(1))
        .onErrorResume(ex -> Mono.just(new Review(id, 0.0)));   // fallback: no reviews available

    }

    static void simulateSlowCall(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException ignored) {}
    }

    public static void main(String[] args) {
        Instant start = Instant.now();

        Mono<ProductDetail> detail = Mono.zip(
                fetchProduct(1), fetchInventory(1), fetchReviews(1))
            .map(tuple -> new ProductDetail(
                tuple.getT1().name(), tuple.getT1().price(),
                tuple.getT2().stockLevel(), tuple.getT3().averageRating()));

        detail.subscribe(result -> {
            System.out.println("Result: " + result);
            System.out.println("Took: " + Duration.between(start, Instant.now()).toMillis() + "ms");
        });

        // Second call: the FAILING id=99 case, demonstrating graceful fallback
        Mono<ProductDetail> failingDetail = Mono.zip(
                fetchProduct(99), fetchInventory(99), fetchReviews(99))
            .map(tuple -> new ProductDetail(
                tuple.getT1().name(), tuple.getT1().price(),
                tuple.getT2().stockLevel(), tuple.getT3().averageRating()));

        failingDetail.subscribe(result -> System.out.println("Fallback result: " + result));

        try { Thread.sleep(1000); } catch (InterruptedException ignored) {}   // let async work finish before exit
    }
}
```

**How to run:**
```bash
java ProductionReactorDemo.java
# Result: ProductDetail[name=Drill, price=29.99, stock=15, rating=4.5]
# Took: ~400ms
# Fallback result: ProductDetail[name=Drill, price=29.99, stock=15, rating=0.0]
```

**What changed and why:**
- `Mono.zip(fetchProduct(1), fetchInventory(1), fetchReviews(1))` runs all three calls **concurrently**, not sequentially — the total time (`~400ms`) matches the *slowest* individual call (`fetchReviews` at 400ms), not the *sum* of all three (`300+200+400=900ms`). This is a genuine, measurable performance benefit of composing independent async operations reactively instead of awaiting them one after another.
- `fetchReviews` demonstrates resilience: `.timeout(Duration.ofSeconds(1))` guards against a hung call, and `.onErrorResume(ex -> Mono.just(...))` provides a graceful fallback value instead of letting the error propagate and fail the entire `zip` — for product id `99`, the simulated review-service failure is caught and replaced with a default `Review(99, 0.0)`, so the overall `ProductDetail` still completes successfully rather than failing outright.
- `Schedulers.boundedElastic()` explicitly moves the simulated blocking `Thread.sleep` calls off Reactor's core processing threads — necessary here because `Thread.sleep` is genuinely blocking and would otherwise stall Reactor's small, precious thread pool; a real non-blocking I/O call (a reactive HTTP client, R2DBC) wouldn't need this, since it never blocks a thread in the first place.

## 6. Walkthrough

**Execution: the first `detail.subscribe(...)` call in `ProductionReactorDemo.main()` (Level 3 code, successful path, id=1).**

1. `Mono.zip(fetchProduct(1), fetchInventory(1), fetchReviews(1))` is constructed. Calling `zip` does **not** immediately execute any of the three `Mono`s — like all Reactor operators, this is lazy; it builds a description of "run these three concurrently, then combine their results," which only executes once subscribed.
2. `.map(tuple -> ...)` is chained onto the zipped result, describing the final transformation into a `ProductDetail`. Still nothing has executed.
3. `detail.subscribe(result -> {...})` is the trigger. This causes Reactor to subscribe to the zipped `Mono`, which in turn subscribes to all three inner `Mono`s (`fetchProduct`, `fetchInventory`, `fetchReviews`) **simultaneously**.
4. Because each inner `Mono` was built with `.subscribeOn(Schedulers.boundedElastic())`, each one's blocking `Thread.sleep` call runs on a *separate* thread from Reactor's `boundedElastic` pool, all three starting at roughly the same moment.
5. `fetchInventory` (200ms) completes first, its `Inventory` result held internally by the `zip` operator, waiting for the other two.
6. `fetchProduct` (300ms) completes next, its `Product` result also held.
7. `fetchReviews` (400ms) completes last — note its own `.timeout(1s)` and `.onErrorResume(...)` wrap its execution, but since this call succeeds well within the 1-second timeout, neither fires; it simply returns `Review(1, 4.5)` normally.
8. Now that all three inner `Mono`s have emitted their values, `Mono.zip` combines them into a `Tuple3<Product, Inventory, Review>` and emits it downstream to the `.map(...)` operator.
9. `.map` executes the transformation lambda, constructing `ProductDetail("Drill", 29.99, 15, 4.5)`.
10. This final value reaches the `subscribe` callback, which prints the result and the elapsed time — approximately `400ms` total, matching the slowest of the three concurrent calls, not their sum.

**Execution: the `failingDetail.subscribe(...)` call (id=99, simulated review-service failure).**

1–4. Identical concurrent-kickoff steps, but for `id=99` this time.
5. `fetchReviews(99)`'s inner callable executes `Thread.sleep(400)`, then checks `if (id == 99) throw new RuntimeException(...)` — this condition is true, so it throws instead of returning a `Review`.
6. This exception propagates as an `onError` signal through the `Mono` pipeline, first reaching `.timeout(Duration.ofSeconds(1))` — since the failure happened well within the timeout window (400ms < 1000ms), the timeout operator passes the error through unchanged rather than replacing it with its own timeout exception.
7. `.onErrorResume(ex -> Mono.just(new Review(id, 0.0)))` intercepts this error signal and, instead of letting it propagate further (which would fail the entire `zip`), **replaces** the failed `Mono` with a new one that immediately emits `Review(99, 0.0)` — the fallback value.
8. From `zip`'s perspective, `fetchReviews(99)` "succeeded" with this fallback `Review` — it has no visibility into the fact that an error occurred and was recovered from further upstream; `zip` proceeds exactly as it would have for a genuinely successful call, combining all three results.
9. The final `ProductDetail` is constructed with `rating = 0.0` (the fallback value) alongside the genuinely successful `product`/`inventory` results, and reaches `subscribe`, printing the fallback result.

## 7. Gotchas & takeaways

> **`flatMap` and `map` are not interchangeable** — `map` is for *synchronous*, one-to-one transformations (a value already in hand, transformed into another value); `flatMap` is specifically for when the transformation itself produces a *new* `Mono`/`Flux` (an additional async operation) that needs to be subscribed to and flattened into the outer stream. Using `map` where `flatMap` was needed produces a nested, unusable `Flux<Mono<T>>` type that won't even compile as intended, immediately signaling the mistake — but understanding *why* is essential.

> **`Mono.zip`/`Flux.zip` run their inputs concurrently, but only complete once ALL inputs complete (or any one of them errors)** — a single slow or hung input Mono without its own timeout can stall the entire `zip` indefinitely. Always apply a `.timeout(...)` to any Mono/Flux whose completion isn't otherwise time-bounded, especially before combining it with others via `zip`.

> **Operators like `.subscribeOn()` and `.publishOn()` control *which thread* subsequent operations run on, and their placement in the chain matters** — `subscribeOn` affects the entire chain's subscription-time behavior regardless of where it appears, while `publishOn` only affects operators *after* it in the chain. Misplacing these is a common source of "why is this still blocking my main thread" confusion in early reactive code.

- `Mono<T>` (0-1 element) and `Flux<T>` (0-N elements) are Project Reactor's core types, both lazy and both implementing the Reactive Streams specification.
- `flatMap` chains a second, dependent async operation per element — the essential operator whenever one reactive call's result feeds into another.
- `Mono.zip`/`Flux.zip` combine multiple independent async sources concurrently, completing in roughly the time of the *slowest* input, not the sum of all inputs — a genuine performance benefit over sequential blocking calls.
- Always pair long-running or externally-dependent `Mono`/`Flux` chains with `.timeout(...)` and `.onErrorResume(...)` for resilience against slow or failing dependencies.
