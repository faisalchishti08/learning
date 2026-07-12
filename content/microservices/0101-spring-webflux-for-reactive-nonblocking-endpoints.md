---
card: microservices
gi: 101
slug: spring-webflux-for-reactive-non-blocking-endpoints
title: "Spring WebFlux for reactive, non-blocking endpoints"
---

## 1. What it is

Spring WebFlux is Spring's [non-blocking](0087-blocking-vs-non-blocking-i-o.md), reactive alternative to [Spring MVC](0100-spring-web-mvc-for-rest-endpoints.md), built on Project Reactor's `Mono` (0 or 1 result) and `Flux` (0 to N results) types instead of returning plain objects directly. A WebFlux controller method returns `Mono<Order>` instead of `Order`, and the entire request-handling pipeline — from receiving the request to writing the response — runs on a small, fixed pool of event-loop threads rather than dedicating one thread per in-flight request.

## 2. Why & when

Spring MVC's thread-per-request model ties a service's maximum concurrency to its thread pool size — fine for most workloads, but a genuine ceiling when a service needs to handle very large numbers of concurrent, I/O-bound requests (many slow downstream calls in flight at once) where thread-per-request would need an impractically large thread pool just to keep up. WebFlux's event-loop model decouples concurrency from thread count entirely, the same way [non-blocking I/O](0087-blocking-vs-non-blocking-i-o.md) does more generally — a small, fixed number of threads can service a much larger number of concurrent in-flight requests, since no thread is ever dedicated to just waiting.

Choose WebFlux specifically when a service's concurrency needs genuinely exceed what thread-per-request comfortably supports — an API gateway proxying to many backend services, or a service handling very high volumes of concurrent slow I/O. For most ordinary services, Spring MVC's simpler, imperative model remains the better default; WebFlux's reactive operator chains carry a real learning curve and debugging cost (stack traces are harder to follow through asynchronous chains) that shouldn't be paid without a genuine concurrency need driving it.

## 3. Core concept

A WebFlux controller declares its return type as `Mono`/`Flux` instead of a plain object; the framework composes the entire request pipeline as a non-blocking, asynchronous chain, only actually executing when the response is subscribed to (by the underlying server machinery, transparently).

```java
@RestController
class OrderController {
    @GetMapping("/orders/{id}")
    Mono<Order> getOrder(@PathVariable int id) {
        return orderRepository.findById(id);  // returns IMMEDIATELY; doesn't block the request thread
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A small, fixed pool of event-loop threads in WebFlux services a much larger number of concurrent in-flight requests, compared to Spring MVC's one-thread-per-request model requiring a much larger pool for the same concurrency">
  <text x="160" y="18" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Spring MVC (thread-per-request)</text>
  <rect x="20" y="30" width="280" height="100" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">200 concurrent requests</text>
  <text x="160" y="75" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">needs ~200 threads</text>

  <text x="480" y="18" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">WebFlux (event loop)</text>
  <rect x="340" y="30" width="280" height="100" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">200 concurrent requests</text>
  <text x="480" y="75" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">needs only a handful of threads</text>
</svg>

WebFlux decouples concurrent request count from thread count, the same way non-blocking I/O does generally.

## 5. Runnable example

Scenario: an order-lookup endpoint, first modeled with Spring MVC-style blocking dispatch (one thread per request), then rewritten in WebFlux style returning a `Mono`-like handle immediately, then extended to compose multiple non-blocking calls together via a reactive-style chain, mirroring how a real WebFlux controller would combine several downstream calls.

### Level 1 — Basic

```java
// File: BlockingStyleController.java -- Spring MVC style: the method
// returns the Order DIRECTLY -- the calling thread blocks until it's ready.
public class BlockingStyleController {
    record Order(int id, String status) {}

    static Order getOrder(int id) throws InterruptedException {
        Thread.sleep(50); // simulated blocking database/network call
        return new Order(id, "PLACED");
    }

    public static void main(String[] args) throws InterruptedException {
        Order order = getOrder(42); // BLOCKS here
        System.out.println("Blocking result: " + order);
    }
}
```

**How to run:** `javac BlockingStyleController.java && java BlockingStyleController` (JDK 17+).

Expected output:
```
Blocking result: Order[id=42, status=PLACED]
```

### Level 2 — Intermediate

```java
// File: ReactiveStyleController.java -- WebFlux style: the method
// returns a Mono-like handle IMMEDIATELY -- the actual value arrives
// later, delivered via subscription, without blocking the caller.
import java.util.concurrent.*;
import java.util.function.*;

public class ReactiveStyleController {
    record Order(int id, String status) {}
    static ExecutorService eventLoop = Executors.newFixedThreadPool(2); // WebFlux's small, fixed event-loop pool

    static class SimpleMono<T> {
        CompletableFuture<T> future;
        SimpleMono(CompletableFuture<T> future) { this.future = future; }
        void subscribe(Consumer<T> onValue) { future.thenAccept(onValue); }
    }

    static SimpleMono<Order> getOrder(int id) { // returns IMMEDIATELY -- no blocking
        CompletableFuture<Order> future = CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(50); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            return new Order(id, "PLACED");
        }, eventLoop);
        return new SimpleMono<>(future);
    }

    public static void main(String[] args) throws InterruptedException {
        SimpleMono<Order> orderMono = getOrder(42);
        System.out.println("Mono returned immediately -- caller was never blocked");
        orderMono.subscribe(order -> System.out.println("Reactive result (via subscription): " + order));
        Thread.sleep(100); // keep the JVM alive long enough for the async callback to fire
        eventLoop.shutdown();
    }
}
```

**How to run:** `javac ReactiveStyleController.java && java ReactiveStyleController` (JDK 17+).

Expected output:
```
Mono returned immediately -- caller was never blocked
Reactive result (via subscription): Order[id=42, status=PLACED]
```

### Level 3 — Advanced

```java
// File: ComposedReactiveChain.java -- compose TWO non-blocking calls
// (get the order, then get its shipping estimate) into ONE reactive
// chain -- neither call blocks a thread while waiting for the other.
import java.util.concurrent.*;
import java.util.function.*;

public class ComposedReactiveChain {
    record Order(int id, String status) {}
    record ShippingEstimate(int orderId, String eta) {}
    record OrderWithShipping(Order order, ShippingEstimate shipping) {}

    static ExecutorService eventLoop = Executors.newFixedThreadPool(2);

    static class SimpleMono<T> {
        CompletableFuture<T> future;
        SimpleMono(CompletableFuture<T> future) { this.future = future; }
        <R> SimpleMono<R> flatMap(Function<T, SimpleMono<R>> mapper) { // composes without blocking
            return new SimpleMono<>(future.thenCompose(value -> mapper.apply(value).future));
        }
        void subscribe(Consumer<T> onValue) { future.thenAccept(onValue); }
    }

    static SimpleMono<Order> getOrder(int id) {
        return new SimpleMono<>(CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(30); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            return new Order(id, "PLACED");
        }, eventLoop));
    }

    static SimpleMono<ShippingEstimate> getShippingEstimate(int orderId) {
        return new SimpleMono<>(CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(30); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            return new ShippingEstimate(orderId, "2 days");
        }, eventLoop));
    }

    public static void main(String[] args) throws InterruptedException {
        SimpleMono<OrderWithShipping> combined = getOrder(42).flatMap(order ->
            getShippingEstimate(order.id()).flatMap(shipping ->
                new SimpleMono<>(CompletableFuture.completedFuture(new OrderWithShipping(order, shipping)))
            )
        );
        System.out.println("Composed chain built -- no blocking occurred while assembling it");
        combined.subscribe(result -> System.out.println("Final composed result: " + result));
        Thread.sleep(150);
        eventLoop.shutdown();
    }
}
```

**How to run:** `javac ComposedReactiveChain.java && java ComposedReactiveChain` (JDK 17+).

Expected output:
```
Composed chain built -- no blocking occurred while assembling it
Final composed result: OrderWithShipping[order=Order[id=42, status=PLACED], shipping=ShippingEstimate[orderId=42, eta=2 days]]
```

## 6. Walkthrough

1. **Level 1** — `getOrder` sleeps 50ms then returns an `Order` directly. `main` calls it and the assignment `Order order = getOrder(42)` genuinely blocks `main`'s thread for the full 50ms before the print statement can run — the Spring MVC-style shape: the calling thread is occupied for the operation's duration.
2. **Level 2 — returning a handle immediately** — `getOrder` now returns `SimpleMono<Order>` immediately, submitting the actual 50ms-sleeping work to `eventLoop` via `CompletableFuture.supplyAsync`. `main` calls `getOrder(42)`, immediately gets `orderMono` back, and prints the "Mono returned immediately" line right away — well before the 50ms delay has elapsed. Only when `orderMono.subscribe(...)` is called does a callback get registered to run once the future completes; `main`'s subsequent `Thread.sleep(100)` exists purely to keep the JVM alive long enough for that callback to fire and print its result — in a real WebFlux application, the reactive framework itself keeps the request alive until the chain completes, so this artificial sleep wouldn't be needed.
3. **Level 3 — composing two non-blocking calls** — `SimpleMono.flatMap` lets one `SimpleMono` be chained into a second, dependent async operation without ever blocking a thread to wait for the first one to finish — this mirrors Reactor's real `Mono.flatMap`. `main` builds `combined` by calling `getOrder(42).flatMap(order -> getShippingEstimate(order.id()).flatMap(shipping -> ...))` — this entire chain is constructed and returned *instantly*, without any of the actual async work having executed yet at the point `combined` is assigned.
4. **Tracing what happens when the chain actually runs** — `getOrder(42)`'s underlying future starts running on `eventLoop`, sleeping 30ms, then resolving to an `Order`. Because of `flatMap`, once that resolves, its result (`order`) is passed into the next stage, which calls `getShippingEstimate(order.id())` — starting a *second* 30ms async operation. Once that resolves too, the innermost `flatMap` combines both results into one `OrderWithShipping` record. `main` prints the "Composed chain built" line immediately (before either 30ms operation has even started), then later, once `subscribe`'s callback fires (after both sequential 30ms stages have completed, roughly 60ms total), it prints the final combined result.
5. **Why this matters for a real WebFlux controller handling many concurrent requests** — at no point across this entire two-stage chain did any thread block waiting for either the order lookup or the shipping estimate; both were expressed as composed, non-blocking operations. In a real WebFlux service handling thousands of concurrent requests each needing a similar two-step lookup, this composability is what lets a small, fixed event-loop thread pool serve all of them concurrently — each request's chain progresses independently as its underlying async operations complete, without any request needing a dedicated thread sitting idle while waiting.

## 7. Gotchas & takeaways

> **Gotcha:** calling any blocking operation (a blocking JDBC call, `Thread.sleep`, a synchronous `RestClient` call) from inside a WebFlux reactive chain defeats the entire point — it ties up one of WebFlux's small number of event-loop threads exactly the way Spring MVC's thread-per-request model would, except now there are far fewer threads to go around, making the impact worse, not better. Every I/O operation inside a WebFlux pipeline needs its own non-blocking counterpart (a reactive database driver, `WebClient` instead of `RestClient`, etc.).

- WebFlux decouples concurrent request count from thread count via an event-loop model, letting a small, fixed thread pool serve far more concurrent in-flight requests than thread-per-request would allow with the same thread count.
- Controller methods return `Mono`/`Flux` instead of plain objects; the actual work happens asynchronously, composed via non-blocking operators like `flatMap`, only executing once something subscribes to the chain.
- Choose WebFlux specifically for genuinely high-concurrency, I/O-bound workloads; for most ordinary services, [Spring MVC](0100-spring-web-mvc-for-rest-endpoints.md)'s simpler, imperative model remains the better default.
- Every dependency called from within a WebFlux pipeline (database driver, HTTP client, etc.) must itself be non-blocking — mixing in a blocking call anywhere in the chain undermines the entire model's benefit.
- See [WebClient](0103-webclient-reactive-synchronous-client.md) for the non-blocking HTTP client that pairs naturally with WebFlux controllers for making outbound calls without blocking the event loop.
