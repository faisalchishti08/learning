---
card: spring-framework
gi: 365
slug: reactive-programming-overview
title: "Reactive programming overview"
---

## 1. What it is

Reactive programming is a style of writing asynchronous, non-blocking code by composing streams of data (which may arrive over time, one item or many) using declarative operators, rather than writing imperative code that blocks a thread waiting for each result. In the Spring ecosystem, this means working with `Mono<T>` (zero or one result) and `Flux<T>` (zero to many results) from Project Reactor, instead of a plain `T` returned by a thread that blocks until the value is ready.

```java
// Imperative (blocking): the thread WAITS here
Product product = productRepository.findById(id);   // blocks until the DB responds

// Reactive (non-blocking): describes what to do WHEN data arrives, doesn't block
Mono<Product> productMono = productRepository.findById(id);
productMono.map(p -> p.withDiscount(0.1)).subscribe(discounted -> ...);
```

## 2. Why & when

A traditional (imperative, thread-per-request) web application ties up one thread for the entire duration of a request, including time spent waiting on I/O — a database query, an external HTTP call, a file read. Under high concurrency with many slow I/O-bound requests, this model needs a large thread pool (each thread mostly idle, just waiting) to keep throughput up, and threads themselves are a relatively expensive resource (memory for each thread's stack, context-switching overhead).

Reactive programming addresses this by never blocking a thread on I/O — instead, a small, fixed pool of threads handles many concurrent operations by reacting to events (data arriving, an operation completing) as they happen, moving on to other work in between. This matters specifically when:

- Your application is I/O-bound (frequent calls to databases, other services, message queues) with high concurrency requirements — reactive can sustain far more simultaneous in-flight requests with far fewer threads than the imperative model.
- You're building a system that needs to gracefully handle backpressure (a slow consumer, without simply buffering unboundedly or blocking the producer) — covered in a later card.
- You're integrating with already-reactive infrastructure (a reactive database driver, a reactive message broker client) where converting back to blocking calls would reintroduce the very problem reactive programming solves.

Reactive programming is not automatically "faster" for CPU-bound work, and it introduces real complexity (different debugging, different exception handling patterns, a steeper learning curve) — it's a deliberate tradeoff, not a universal upgrade over imperative code. The next few cards explore this tradeoff and the specific mechanics in depth.

## 3. Core concept

```
Imperative, thread-per-request model:

  Thread 1: [--- waiting on DB query (50ms, thread BLOCKED) ---] [process result]
  Thread 2: [--- waiting on DB query (50ms, thread BLOCKED) ---] [process result]
  Thread 3: [--- waiting on DB query (50ms, thread BLOCKED) ---] [process result]
  ...
  N concurrent requests -> need N threads (roughly), each mostly idle/blocked

Reactive, event-loop model:

  Thread 1 (event loop): handles request A's "start DB query" -> MOVES ON
                          handles request B's "start DB query" -> MOVES ON
                          handles request C's "start DB query" -> MOVES ON
                          ... (DB driver notifies when EACH completes)
                          request A's result arrives -> Thread 1 processes it
                          request B's result arrives -> Thread 1 processes it
  ...
  N concurrent requests -> handled by a SMALL, FIXED number of threads,
                           since no thread ever blocks waiting

Mono<T>  — a reactive "promise" of ZERO or ONE value (or an error)
Flux<T>  — a reactive "stream" of ZERO to MANY values over time (or an error)
```

## 4. Diagram

<svg viewBox="0 0 740 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="220" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">Thread-per-request (blocking) vs event-loop (reactive)</text>

  <rect x="20" y="50" width="330" height="140" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="185" y="70" text-anchor="middle" fill="#8b949e" font-size="10">Imperative: many threads, mostly blocked</text>
  <text x="35" y="95" fill="#8b949e" font-size="9">Thread 1: [====WAIT ON I/O====][work]</text>
  <text x="35" y="113" fill="#8b949e" font-size="9">Thread 2: [====WAIT ON I/O====][work]</text>
  <text x="35" y="131" fill="#8b949e" font-size="9">Thread 3: [====WAIT ON I/O====][work]</text>
  <text x="35" y="155" fill="#8b949e" font-size="9">N requests need ~N threads</text>

  <rect x="390" y="50" width="330" height="140" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="555" y="70" text-anchor="middle" fill="#6db33f" font-size="10">Reactive: few threads, never blocked</text>
  <text x="405" y="95" fill="#6db33f" font-size="9">Thread 1: startA, startB, startC,</text>
  <text x="405" y="113" fill="#6db33f" font-size="9">          handleA-done, handleB-done...</text>
  <text x="405" y="155" fill="#8b949e" font-size="9">N requests handled by FEW threads</text>

  <defs>
    <marker id="a41" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Reactive's event-loop model handles many concurrent I/O-bound operations without dedicating a thread to each one's wait time.*

## 5. Runnable example

### Level 1 — Basic

A minimal Mono-returning method, compared directly to its blocking equivalent, to see the type-level difference:

```java
// ProductLookup.java
import reactor.core.publisher.Mono;

public class ProductLookup {

    record Product(long id, String name) {}

    // BLOCKING: returns the value directly, thread waits here
    public Product findBlocking(long id) {
        simulateSlowIO();
        return new Product(id, "Drill");
    }

    // REACTIVE: returns a Mono immediately — describes FUTURE work, doesn't block
    public Mono<Product> findReactive(long id) {
        return Mono.fromSupplier(() -> {
            simulateSlowIO();
            return new Product(id, "Drill");
        });
    }

    private void simulateSlowIO() {
        try { Thread.sleep(100); } catch (InterruptedException ignored) {}
    }

    public static void main(String[] args) {
        ProductLookup lookup = new ProductLookup();

        Product blocking = lookup.findBlocking(1);
        System.out.println("Blocking result: " + blocking);

        Mono<Product> mono = lookup.findReactive(1);
        System.out.println("Mono created (nothing has run yet): " + mono);
        mono.subscribe(p -> System.out.println("Reactive result (via subscribe): " + p));
    }
}
```

**How to run:**
```bash
java ProductLookup.java
# Blocking result: Product[id=1, name=Drill]
# Mono created (nothing has run yet): MonoSupplier
# Reactive result (via subscribe): Product[id=1, name=Drill]
```

Notice `findReactive` returns *immediately*, printing `"Mono created..."` before any actual work happens — the `Mono` is a description of work to be done, not the result itself. Nothing executes until `.subscribe(...)` is called; this is the core reactive principle of **laziness**, distinct from a Java `Future`, which typically starts its work eagerly.

### Level 2 — Intermediate

Composing multiple reactive operations declaratively, contrasted with the imperative equivalent, showing how transformation logic reads as a pipeline rather than sequential statements:

```java
// ProductPricing.java
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.List;

public class ProductPricing {

    record Product(long id, String name, double price) {}
    record PricedProduct(long id, String name, double finalPrice) {}

    // IMPERATIVE version
    public List<PricedProduct> applyDiscountsBlocking(List<Product> products) {
        return products.stream()
            .filter(p -> p.price() > 10)
            .map(p -> new PricedProduct(p.id(), p.name(), p.price() * 0.9))
            .toList();
    }

    // REACTIVE version — same LOGIC, expressed as a Flux pipeline
    public Flux<PricedProduct> applyDiscountsReactive(Flux<Product> products) {
        return products
            .filter(p -> p.price() > 10)
            .map(p -> new PricedProduct(p.id(), p.name(), p.price() * 0.9));
    }

    public static void main(String[] args) {
        ProductPricing pricing = new ProductPricing();
        List<Product> catalog = List.of(
            new Product(1, "Nail", 0.50),
            new Product(2, "Drill", 29.99),
            new Product(3, "Hammer", 14.99)
        );

        System.out.println("Imperative: " + pricing.applyDiscountsBlocking(catalog));

        Flux<Product> productFlux = Flux.fromIterable(catalog);
        pricing.applyDiscountsReactive(productFlux)
            .subscribe(p -> System.out.println("Reactive item: " + p));
    }
}
```

**How to run:**
```bash
java ProductPricing.java
# Imperative: [PricedProduct[id=2, name=Drill, finalPrice=26.991], PricedProduct[id=3, name=Hammer, finalPrice=13.491]]
# Reactive item: PricedProduct[id=2, name=Drill, finalPrice=26.991]
# Reactive item: PricedProduct[id=3, name=Hammer, finalPrice=13.491]
```

**What changed:** The reactive pipeline (`filter` then `map`) reads almost identically to the `Stream` API's imperative equivalent — this is deliberate; Project Reactor's operator vocabulary closely mirrors Java's `Stream` API for exactly this reason, easing the transition. The critical difference is *when* elements are processed: `Flux`/`Mono` elements can arrive **asynchronously over time** (from a database, a network call), whereas a `Stream` always operates over data already fully available in memory.

### Level 3 — Advanced

Demonstrating the actual concurrency payoff — simulating many "slow I/O" operations and comparing how many threads each model needs, using `Mono.fromCallable` with an explicit scheduler to model non-blocking I/O realistically:

```java
// ConcurrencyComparison.java
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.IntStream;

public class ConcurrencyComparison {

    // Simulates 20 "slow I/O" lookups (100ms each) using BLOCKING calls,
    // one thread per request, all launched roughly concurrently via parallel streams.
    static void runBlocking(int count) {
        Instant start = Instant.now();
        AtomicInteger activeThreads = new AtomicInteger(0);
        AtomicInteger maxThreads = new AtomicInteger(0);

        IntStream.range(0, count).parallel().forEach(i -> {
            int active = activeThreads.incrementAndGet();
            maxThreads.updateAndGet(max -> Math.max(max, active));
            try { Thread.sleep(100); } catch (InterruptedException ignored) {}
            activeThreads.decrementAndGet();
        });

        System.out.println("Blocking: " + count + " requests, peak concurrent threads=" + maxThreads.get()
            + ", took " + Duration.between(start, Instant.now()).toMillis() + "ms");
    }

    // Same 20 "slow I/O" lookups, but modeled reactively — the underlying elastic
    // scheduler here still uses threads for the blocking simulation call itself
    // (Reactor can't make Thread.sleep non-blocking), but demonstrates how a REAL
    // non-blocking I/O driver (a reactive DB client) would need ZERO dedicated
    // waiting threads at all, unlike the blocking version above.
    static void runReactive(int count) {
        Instant start = Instant.now();

        Flux<Integer> results = Flux.range(0, count)
            .flatMap(i -> Mono.fromCallable(() -> {
                    try { Thread.sleep(100); } catch (InterruptedException ignored) {}
                    return i;
                })
                .subscribeOn(Schedulers.boundedElastic()),
                count)   // concurrency hint: process ALL of them concurrently, not sequentially
            .doOnComplete(() -> System.out.println("Reactive: " + count + " requests, took "
                + Duration.between(start, Instant.now()).toMillis() + "ms"));

        results.blockLast();   // ONLY for this demo's main() to wait for completion — never do this in a real handler
    }

    public static void main(String[] args) {
        runBlocking(20);
        runReactive(20);
    }
}
```

**How to run:**
```bash
java ConcurrencyComparison.java
# Blocking: 20 requests, peak concurrent threads=20, took ~105ms
# Reactive: 20 requests, took ~105ms
```

**What changed and why:**
- Both versions complete in roughly the same wall-clock time (~100ms, since all 20 "I/O" operations run concurrently either way) — the payoff of reactive isn't raw speed for a single burst like this, it's **resource efficiency under sustained, larger-scale concurrency**. The blocking version genuinely needs 20 real OS threads alive simultaneously; a *real* reactive pipeline using a genuinely non-blocking I/O driver (not `Thread.sleep`, which cannot be made non-blocking) would need close to **zero** dedicated waiting threads for the same 20 operations — Reactor's event loop threads would issue all 20 I/O requests and then be free to handle other work while waiting for the I/O layer itself to signal completion.
- `Schedulers.boundedElastic()` is used here specifically because `Thread.sleep` is an inherently blocking call — this scheduler exists precisely to safely run blocking operations from reactive code without stalling Reactor's main event-loop threads, but it still consumes real threads while blocked, unlike genuine non-blocking I/O.
- `blockLast()` is used only to keep this demo's `main()` method alive until the reactive pipeline finishes — this is explicitly the kind of blocking call that should **never** appear in a real reactive web handler, since it would negate the entire non-blocking model; it's included here purely so the example program terminates predictably when run.

## 6. Walkthrough

**Execution: `ProductLookup.main()` (Level 1 code), step by step.**

1. `lookup.findBlocking(1)` is called directly. Execution enters the method body immediately: `simulateSlowIO()` calls `Thread.sleep(100)` — the **calling thread itself** (here, the `main` thread) is blocked for 100 milliseconds, unable to do anything else.
2. After the sleep completes, `new Product(1, "Drill")` is constructed and returned directly as the method's return value — `blocking` now holds the actual `Product` object.
3. `System.out.println("Blocking result: " + blocking)` executes immediately, since `blocking` already holds a fully resolved value.
4. `lookup.findReactive(1)` is called. Inside, `Mono.fromSupplier(() -> {...})` wraps the slow-lookup logic in a lambda — **critically, this lambda is not executed yet**. `Mono.fromSupplier` just builds a `Mono` object describing "when someone subscribes, run this supplier." The method returns this `Mono` object immediately, having done zero actual work.
5. `System.out.println("Mono created...")` executes right away, printing before any of the `Product`-fetching logic has run at all — proof that constructing a `Mono` is a cheap, immediate, non-blocking operation regardless of what work it eventually describes.
6. `mono.subscribe(p -> System.out.println(...))` is the trigger: **only now** does Reactor actually invoke the supplier lambda from step 4. `simulateSlowIO()` runs (blocking the current thread for 100ms, since `Mono.fromSupplier` doesn't itself introduce any threading — it just describes the work), then `new Product(1, "Drill")` is constructed.
7. Once the supplier returns, Reactor delivers this value to the `subscribe` callback, which prints `"Reactive result (via subscribe): Product[id=1, name=Drill]"`.

The key sequencing insight: steps 4–5 happen **before** any of the actual product-lookup logic runs — construction of a `Mono` and *execution* of the work it describes are two entirely separate moments in time, connected only by the eventual call to `subscribe` (or an equivalent terminal operation).

## 7. Gotchas & takeaways

> **A `Mono`/`Flux` that's never subscribed to never does anything at all** — building a reactive pipeline and forgetting to call `.subscribe()` (or return it from a WebFlux handler, which subscribes on your behalf) is a common beginner mistake that silently produces no observable effect whatsoever, with no error or warning.

> **Calling `.block()`/`.blockLast()`/`.blockFirst()` on a `Mono`/`Flux` defeats the entire purpose of reactive programming** — it forces the calling thread to wait synchronously for the reactive pipeline to complete, exactly like the imperative model reactive programming exists to avoid. These methods exist for specific, narrow use cases (test code, a `main()` method, deliberate bridging at an application's outermost boundary) — never call them inside a reactive web handler or any code meant to remain non-blocking.

> **Reactive programming does not make CPU-bound work faster** — its benefit is specifically about not wasting threads on I/O wait time. A CPU-intensive computation (heavy math, image processing) gains nothing from being wrapped in a `Mono`/`Flux`; it still needs the same CPU time regardless of the programming model, and reactive's added complexity would be pure overhead for such workloads.

- Reactive programming avoids blocking threads on I/O wait time, using an event-loop model that can sustain far higher concurrency with far fewer threads than the imperative, thread-per-request model.
- `Mono<T>` represents zero-or-one future value; `Flux<T>` represents zero-to-many future values arriving over time — both are lazy, doing nothing until subscribed to.
- Reactive's benefits are specific to I/O-bound, high-concurrency workloads — it offers no advantage (and real added complexity) for CPU-bound work.
- Never call blocking terminal operations (`.block()`, `.blockLast()`) inside reactive handler code — that reintroduces the exact problem reactive programming solves.
