---
card: microservices
gi: 103
slug: webclient-reactive-synchronous-client
title: "WebClient (reactive/synchronous client)"
---

## 1. What it is

`WebClient` is Spring's non-blocking, reactive HTTP client, returning `Mono<T>`/`Flux<T>` from every call — but despite being fundamentally reactive, it can also be used in a **synchronous, blocking style** by calling `.block()` on the returned `Mono`, which waits for and returns the resolved value directly, discarding the non-blocking benefit for that specific call. This dual nature — genuinely reactive by default, but usable synchronously when needed — is exactly what the topic name "reactive/synchronous client" is pointing at.

## 2. Why & when

`WebClient` was originally built as the natural HTTP client companion to [Spring WebFlux](0101-spring-webflux-for-reactive-non-blocking-endpoints.md)'s reactive programming model — non-blocking end to end, from receiving a request through making any outbound calls to producing the response. But `WebClient` is a perfectly capable client even inside an otherwise-blocking, Spring MVC-based service: calling `.block()` at the call site gets you a plain, synchronous result, letting a traditional service occasionally use `WebClient` (say, for its cleaner API or specific feature support) without adopting the reactive model throughout.

Use `WebClient` reactively (subscribing, never blocking) when the calling code itself lives inside a WebFlux reactive pipeline — blocking there defeats the whole non-blocking model, as covered in WebFlux's own gotchas. Use `.block()` only from genuinely blocking, non-reactive contexts (a Spring MVC controller, a scheduled batch job) where `WebClient` is being used purely for its API rather than for its non-blocking properties — and in that case, seriously consider whether [`RestClient`](0104-restclient-spring-6-1-synchronous-fluent-client.md), designed for exactly this blocking use case, might be the more natural fit instead.

## 3. Core concept

The same `WebClient` call can be consumed two ways: reactively, by composing and subscribing without ever blocking, or synchronously, by calling `.block()` to force it to behave like an ordinary blocking call.

```java
// Reactive usage -- non-blocking, composed
Mono<Order> orderMono = webClient.get().uri("/orders/{id}", 42).retrieve().bodyToMono(Order.class);
orderMono.subscribe(order -> ...);   // never blocks

// Synchronous usage -- forces blocking behavior
Order order = webClient.get().uri("/orders/{id}", 42).retrieve().bodyToMono(Order.class).block();  // BLOCKS
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same WebClient call chain can either be subscribed to for non-blocking reactive use, or have block called on it to force synchronous blocking behavior">
  <rect x="20" y="55" width="260" height="45" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="150" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">webClient.get()...bodyToMono(...)</text>

  <rect x="340" y="20" width="270" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">.subscribe(...) -- non-blocking</text>

  <rect x="340" y="85" width="270" height="45" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="475" y="112" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">.block() -- forces blocking</text>

  <line x1="280" y1="75" x2="340" y2="42" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="280" y1="75" x2="340" y2="107" stroke="#8b949e" stroke-width="1.5"/>
</svg>

The identical call chain branches into two very different execution behaviors at the final step.

## 5. Runnable example

Scenario: the same `WebClient`-style order lookup, first consumed reactively (subscribing, never blocking), then consumed synchronously via a `.block()`-style call, comparing what each returns to the caller and when, then extended to show why calling the blocking style from inside a simulated reactive pipeline is dangerous — it silently reintroduces the exact thread-occupation problem WebFlux's non-blocking model exists to avoid.

### Level 1 — Basic

```java
// File: ReactiveUsage.java -- consume WebClient reactively: subscribe,
// never block, exactly as intended inside a WebFlux pipeline.
import java.util.concurrent.*;
import java.util.function.*;

public class ReactiveUsage {
    record Order(int id, String status) {}
    static ExecutorService pool = Executors.newFixedThreadPool(1);

    static class SimpleMono<T> {
        CompletableFuture<T> future;
        SimpleMono(CompletableFuture<T> future) { this.future = future; }
        void subscribe(Consumer<T> onValue) { future.thenAccept(onValue); }
    }

    static SimpleMono<Order> getOrder(int id) {
        return new SimpleMono<>(CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(50); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            return new Order(id, "PLACED");
        }, pool));
    }

    public static void main(String[] args) throws InterruptedException {
        getOrder(42).subscribe(order -> System.out.println("Reactive (subscribed): " + order));
        System.out.println("main continues immediately -- never blocked");
        Thread.sleep(100);
        pool.shutdown();
    }
}
```

**How to run:** `javac ReactiveUsage.java && java ReactiveUsage` (JDK 17+).

Expected output:
```
main continues immediately -- never blocked
Reactive (subscribed): Order[id=42, status=PLACED]
```

### Level 2 — Intermediate

```java
// File: SynchronousBlockUsage.java -- consume the SAME kind of call via
// a .block()-style method: forces the caller to wait, returning the
// resolved value directly, like a plain synchronous call.
import java.util.concurrent.*;

public class SynchronousBlockUsage {
    record Order(int id, String status) {}
    static ExecutorService pool = Executors.newFixedThreadPool(1);

    static class SimpleMono<T> {
        CompletableFuture<T> future;
        SimpleMono(CompletableFuture<T> future) { this.future = future; }
        T block() throws Exception { return future.get(); } // FORCES blocking, waits for the result
    }

    static SimpleMono<Order> getOrder(int id) {
        return new SimpleMono<>(CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(50); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            return new Order(id, "PLACED");
        }, pool));
    }

    public static void main(String[] args) throws Exception {
        Order order = getOrder(42).block(); // BLOCKS main's thread until resolved
        System.out.println("Synchronous (blocked): " + order);
        pool.shutdown();
    }
}
```

**How to run:** `javac SynchronousBlockUsage.java && java SynchronousBlockUsage` (JDK 17+).

Expected output:
```
Synchronous (blocked): Order[id=42, status=PLACED]
```

### Level 3 — Advanced

```java
// File: DangerOfBlockingInsideEventLoop.java -- demonstrate WHY calling
// .block() from inside a reactive event-loop pool is dangerous: it
// occupies one of the FEW event-loop threads, exactly reproducing
// thread-per-request's resource cost inside a model designed to avoid it.
import java.util.concurrent.*;

public class DangerOfBlockingInsideEventLoop {
    static ExecutorService eventLoop = Executors.newFixedThreadPool(2); // WebFlux-style: only 2 event-loop threads!
    static ExecutorService ioPool = Executors.newFixedThreadPool(2);    // the SEPARATE pool real I/O actually runs on

    record Order(int id, String status) {}

    static class SimpleMono<T> {
        CompletableFuture<T> future;
        SimpleMono(CompletableFuture<T> future) { this.future = future; }
        T block() throws Exception { return future.get(); }
    }

    static SimpleMono<Order> getOrder(int id) {
        return new SimpleMono<>(CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(100); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            return new Order(id, "PLACED");
        }, ioPool)); // I/O runs on ioPool, NOT on eventLoop -- avoids the handlers deadlocking themselves
    }

    public static void main(String[] args) throws Exception {
        // simulate TWO "requests" handled ON the event loop, each WRONGLY calling .block()
        Future<String> handler1 = eventLoop.submit(() -> {
            try {
                Order order = getOrder(1).block(); // occupies ONE of only 2 event-loop threads while waiting
                return "handler1 got: " + order;
            } catch (Exception e) { return "handler1 failed"; }
        });
        Future<String> handler2 = eventLoop.submit(() -> {
            try {
                Order order = getOrder(2).block(); // occupies the OTHER of only 2 event-loop threads
                return "handler2 got: " + order;
            } catch (Exception e) { return "handler2 failed"; }
        });

        long start = System.currentTimeMillis();
        System.out.println(handler1.get());
        System.out.println(handler2.get());
        long elapsed = System.currentTimeMillis() - start;
        System.out.println("Both handlers used the event loop's ENTIRE 2-thread capacity just to block-wait: ~" + elapsed + "ms");
        eventLoop.shutdown();
        ioPool.shutdown();
    }
}
```

**How to run:** `javac DangerOfBlockingInsideEventLoop.java && java DangerOfBlockingInsideEventLoop` (JDK 17+).

Expected output (timing will vary, but both handlers succeed and elapsed reflects serialized/contended execution):
```
handler1 got: Order[id=1, status=PLACED]
handler2 got: Order[id=2, status=PLACED]
Both handlers used the event loop's ENTIRE 2-thread capacity just to block-wait: ~207ms
```

## 6. Walkthrough

1. **Level 1** — `getOrder(42).subscribe(...)` registers a callback and returns immediately; `main` prints "main continues immediately" right away, and only later (once the underlying 50ms async operation completes) does the subscribed callback fire and print the reactive result — the non-blocking, intended usage pattern.
2. **Level 2 — the same shape, forced synchronous** — `SimpleMono.block()` calls `future.get()` directly, which genuinely waits for the future to resolve before returning. `main` calls `getOrder(42).block()`, and the assignment line itself blocks for the full 50ms before the print statement can execute — behaviorally identical to a plain synchronous call, achieved by forcing the reactive type to behave that way at the call site.
3. **Level 3 — why blocking inside an event loop is a real danger** — `eventLoop` is deliberately sized at just 2 threads, standing in for WebFlux's small, fixed event-loop pool that dispatches incoming "requests"; `ioPool` is a separate pool standing in for wherever the actual downstream I/O work runs. Two "request handlers" are submitted *to the event loop*, and each one incorrectly calls `.block()` on its `getOrder` call — exactly the anti-pattern the WebFlux gotcha warns against. (Note that `getOrder`'s own async work deliberately runs on the separate `ioPool` rather than on `eventLoop` itself — if it ran on the same 2-thread `eventLoop` that the blocking handlers already occupy, there would be no thread left for it to ever run on, a self-inflicted deadlock this example sidesteps to isolate the specific cost being demonstrated: thread occupation, not total deadlock.)
4. **Tracing what happens with only 2 event-loop threads and 2 blocking handlers** — `handler1` and `handler2` are both submitted to `eventLoop`. Since the pool has exactly 2 threads, both handlers *can* start immediately — but each one then calls `.block()`, which occupies its own event-loop thread for the full 100ms duration of its underlying `getOrder` call (whose actual work runs on `ioPool`, freeing it to complete independently). This means, for that 100ms window, the entire 2-thread event loop is completely consumed just by these two handlers *waiting*, even though the real work is happening elsewhere — if a *third* request arrived at that exact moment needing the event loop, it would have absolutely nowhere to run, since both event-loop threads are occupied purely by blocking waits.
5. **Contrast with correct reactive usage** — had `handler1` and `handler2` instead used `.subscribe()` (Level 1's pattern) rather than `.block()`, neither would have occupied an event-loop thread while waiting — the event loop would only be touched briefly to *initiate* the call, and the actual waiting would happen without any event-loop thread sitting idle, freeing it to handle many more concurrent requests with the same 2 threads. This is precisely why `.block()` should be reserved for genuinely blocking, non-reactive contexts — using it inside a component that's meant to be reactive throughout reintroduces the exact thread-occupation cost that WebFlux's model exists specifically to eliminate, and in a real system where the I/O work also competes for the same limited pool, it can escalate all the way to the kind of full deadlock this example's separate `ioPool` was structured to avoid.

## 7. Gotchas & takeaways

> **Gotcha:** Reactor (the library underlying `Mono`/`Flux`) actually detects and throws an exception if you call `.block()` from certain contexts it recognizes as non-blocking-only threads, specifically to catch exactly this misuse early rather than letting it silently degrade performance. Don't rely on that safety net as your only defense, though — it doesn't catch every possible case, and understanding *why* the restriction exists (as demonstrated in Level 3) is what actually prevents the mistake.

- `WebClient` is fundamentally reactive (`Mono`/`Flux`-returning), but can be forced into synchronous, blocking behavior via `.block()` when called from a genuinely blocking context.
- Use `.subscribe()` (never blocking) when calling code lives inside a reactive pipeline (a WebFlux controller, a reactive chain); use `.block()` only from ordinary blocking contexts like a Spring MVC controller or scheduled job.
- Calling `.block()` from inside a reactive event-loop context reproduces the exact thread-occupation cost non-blocking I/O is designed to eliminate — with WebFlux's typically small thread pool, this cost is proportionally much more damaging than it would be under Spring MVC's larger thread-per-request pool.
- If a service is fundamentally blocking/synchronous throughout and only occasionally needs `WebClient`'s specific features, seriously weigh whether [`RestClient`](0104-restclient-spring-6-1-synchronous-fluent-client.md) — designed natively for synchronous use — is the more appropriate tool.
- See [Spring WebFlux](0101-spring-webflux-for-reactive-non-blocking-endpoints.md) for the broader reactive model `WebClient` is designed to pair with when used non-blocking throughout.
