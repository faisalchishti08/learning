---
card: microservices
gi: 172
slug: spring-cloud-gateway-mvc-servlet-based
title: "Spring Cloud Gateway MVC (servlet-based)"
---

## 1. What it is

Spring Cloud Gateway MVC is a servlet-based, blocking-model alternative to [Spring Cloud Gateway's reactive implementation](0171-spring-cloud-gateway-reactive-webflux-based) — it exposes the same route/predicate/filter configuration style and concepts, but runs on the traditional Spring MVC servlet stack (thread-per-request, blocking I/O) rather than WebFlux, using Java's virtual threads to get much of the non-blocking model's efficiency without requiring reactive programming.

## 2. Why & when

Reactive programming has real value for I/O-bound throughput, but it also has a real cost: reactive code (`Mono`/`Flux` chains, avoiding blocking calls anywhere in the pipeline, different debugging and stack-trace ergonomics) is a genuinely different programming model that not every team wants to adopt, especially for a codebase already comfortable with traditional blocking Spring MVC. Java's virtual threads (Project Loom, stable since JDK 21) changed this trade-off: a blocking call on a virtual thread no longer ties up a scarce OS thread the way it would on a traditional platform thread, meaning much of the reactive model's core efficiency argument (don't block a thread during I/O wait) can now be achieved with ordinary, imperative, blocking-style code running on virtual threads instead.

Reach for Spring Cloud Gateway MVC when a team prefers or already has expertise in traditional, imperative Spring MVC code, wants simpler debugging and stack traces than reactive chains typically provide, and is running on a JDK new enough to benefit from virtual threads. Reach for the reactive implementation instead when the team is already comfortable with reactive programming, or when working in an ecosystem (existing WebFlux-based services) where consistency with the reactive model elsewhere in the system is valuable.

## 3. Core concept

Routes and filters are still expressed through the same route/predicate/filter configuration model as the reactive gateway, but the underlying request-handling code is ordinary, blocking, imperative Java — when running on virtual threads, a blocking call inside a route handler suspends only that lightweight virtual thread, not an expensive platform thread, letting the JVM support a very large number of concurrent in-flight requests despite the blocking-style code.

```java
@Bean
public RouterFunction<ServerResponse> orderRoute() {
    // SAME route/predicate/filter concepts as reactive Gateway, but plain, BLOCKING, imperative code
    return GatewayRouterFunctions.route("order_route")
        .route(RequestPredicates.path("/orders/**"), HandlerFunctions.http("http://order-service:8080"))
        .build();
    // running on a VIRTUAL thread: this blocking call doesn't waste a scarce platform thread
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Ordinary blocking code running on a virtual thread suspends only that lightweight virtual thread during I/O wait; the underlying platform thread is freed to run other virtual threads, achieving similar efficiency to reactive code without a different programming model" >
  <rect x="20" y="30" width="180" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">virtual thread (blocked)</text>

  <rect x="20" y="110" width="180" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="132" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">virtual thread (blocked)</text>

  <rect x="280" y="65" width="180" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="88" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">ONE platform thread</text>
  <text x="370" y="103" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">runs whichever isn't blocked</text>

  <line x1="200" y1="47" x2="278" y2="80" stroke="#8b949e" marker-end="url(#arr53)"/>
  <line x1="200" y1="127" x2="278" y2="95" stroke="#8b949e" marker-end="url(#arr53)"/>

  <defs>
    <marker id="arr53" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Many virtual threads share few platform threads; a blocked virtual thread doesn't tie up its underlying platform thread.

## 5. Runnable example

Scenario: a gateway forwarding requests to a slow backend that starts using ordinary platform threads to show the classic blocking limitation, switches to virtual threads with the identical blocking code to show the throughput improvement without any reactive rewrite, and finally compares the code complexity directly by contrasting the virtual-thread blocking style against an equivalent reactive-style chain solving the same problem.

### Level 1 — Basic

```java
// File: PlatformThreadBlocking.java -- ordinary platform threads: blocking calls
// tie up a SCARCE, expensive OS thread for the whole wait.
import java.util.concurrent.*;

public class PlatformThreadBlocking {
    static String slowBackendCall(int requestId) throws InterruptedException {
        Thread.sleep(100); // simulated backend wait
        return "response for " + requestId;
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService platformThreadPool = Executors.newFixedThreadPool(4); // a SMALL, fixed number of expensive platform threads
        CountDownLatch latch = new CountDownLatch(20);
        long start = System.currentTimeMillis();

        for (int i = 1; i <= 20; i++) {
            int requestId = i;
            platformThreadPool.submit(() -> {
                try { slowBackendCall(requestId); } catch (InterruptedException ignored) { }
                latch.countDown();
            });
        }
        latch.await(10, TimeUnit.SECONDS);
        platformThreadPool.shutdown();

        System.out.println("20 requests, 4 platform threads: ~" + (System.currentTimeMillis() - start) + "ms");
        System.out.println("Only 4 requests can be 'in flight' at once -- the rest QUEUE, waiting for a thread to free up.");
    }
}
```

**How to run:** `javac PlatformThreadBlocking.java && java PlatformThreadBlocking` (JDK 17+, works on any modern JDK).

### Level 2 — Intermediate

```java
// File: VirtualThreadBlocking.java -- IDENTICAL blocking code, run on VIRTUAL
// threads instead -- dramatically more concurrency, ZERO reactive rewrite needed.
import java.util.concurrent.*;

public class VirtualThreadBlocking {
    static String slowBackendCall(int requestId) throws InterruptedException {
        Thread.sleep(100); // IDENTICAL blocking call to Level 1 -- not rewritten AT ALL
        return "response for " + requestId;
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService virtualThreadPool = Executors.newVirtualThreadPerTaskExecutor(); // ONE virtual thread PER TASK -- cheap to create
        CountDownLatch latch = new CountDownLatch(20);
        long start = System.currentTimeMillis();

        for (int i = 1; i <= 20; i++) {
            int requestId = i;
            virtualThreadPool.submit(() -> {
                try { slowBackendCall(requestId); } catch (InterruptedException ignored) { } // the SAME blocking call
                latch.countDown();
            });
        }
        latch.await(10, TimeUnit.SECONDS);
        virtualThreadPool.shutdown();

        System.out.println("20 requests, virtual threads: ~" + (System.currentTimeMillis() - start) + "ms");
        System.out.println("ALL 20 requests ran essentially CONCURRENTLY -- the SAME blocking Thread.sleep() call, just scheduled onto cheap virtual threads.");
    }
}
```

**How to run:** `javac VirtualThreadBlocking.java && java VirtualThreadBlocking` (JDK 21+, requires virtual thread support).

Expected output (approximate; close to the single 100ms wait, not scaled by request count / thread count):
```
20 requests, virtual threads: ~110ms
ALL 20 requests ran essentially CONCURRENTLY -- the SAME blocking Thread.sleep() call, just scheduled onto cheap virtual threads.
```

Comparing directly against Level 1's roughly `20/4 * 100ms = 500ms`, virtual threads achieve close to the single-wait-period latency, using the exact same blocking `Thread.sleep` call — no reactive rewrite, no `Mono`/`Flux`, just ordinary imperative code scheduled differently by the JVM.

### Level 3 — Advanced

```java
// File: BlockingVsReactiveCodeComparison.java -- contrasts the CODE STYLE of a
// virtual-thread blocking chain against an equivalent reactive chain solving the
// SAME problem: fetch order, then fetch customer, combine, HANDLE a failure.
import java.util.concurrent.*;

public class BlockingVsReactiveCodeComparison {
    record Order(int orderId, int customerId) {}
    record Customer(int customerId, String name) {}
    record CombinedView(Order order, Customer customer) {}

    static Order fetchOrder(int orderId) throws InterruptedException {
        Thread.sleep(50);
        if (orderId == 999) throw new RuntimeException("order not found"); // simulated failure case
        return new Order(orderId, 7);
    }
    static Customer fetchCustomer(int customerId) throws InterruptedException { Thread.sleep(50); return new Customer(customerId, "Alice"); }

    // VIRTUAL-THREAD-BLOCKING style: ordinary, imperative, try/catch -- reads top to bottom
    static CombinedView getOrderViewBlocking(int orderId) {
        try {
            Order order = fetchOrder(orderId);       // blocks the VIRTUAL thread, cheaply
            Customer customer = fetchCustomer(order.customerId()); // blocks again, cheaply
            return new CombinedView(order, customer);
        } catch (Exception e) {
            System.out.println("  [blocking style] caught failure directly: " + e.getMessage());
            return null; // ordinary Java error handling -- a plain try/catch
        } catch (Throwable t) { return null; }
    }

    public static void main(String[] args) throws Exception {
        ExecutorService virtualThreads = Executors.newVirtualThreadPerTaskExecutor();

        Future<CombinedView> successCase = virtualThreads.submit(() -> getOrderViewBlocking(42));
        Future<CombinedView> failureCase = virtualThreads.submit(() -> getOrderViewBlocking(999));

        System.out.println("Success case result: " + successCase.get());
        System.out.println("Failure case result: " + failureCase.get() + " (handled with a PLAIN try/catch, no reactive error operators)");

        virtualThreads.shutdown();
        System.out.println("This entire flow used ordinary Java control flow (try/catch, sequential calls) -- the mental model a Spring MVC team already knows, running efficiently on virtual threads.");
    }
}
```

**How to run:** `javac BlockingVsReactiveCodeComparison.java && java BlockingVsReactiveCodeComparison` (JDK 21+).

Expected output:
```
  [blocking style] caught failure directly: order not found
Success case result: CombinedView[order=Order[orderId=42, customerId=7], customer=Customer[customerId=7, name=Alice]]
Failure case result: null (handled with a PLAIN try/catch, no reactive error operators)
This entire flow used ordinary Java control flow (try/catch, sequential calls) -- the mental model a Spring MVC team already knows, running efficiently on virtual threads.
```

## 6. Walkthrough

1. **Level 1** — `platformThreadPool` is fixed at 4 threads; with 20 requests each needing a 100ms blocking wait, only 4 can be "in flight" concurrently, forcing the remaining 16 to queue behind them — the measured total time (~500ms) reflects five sequential batches of four.
2. **Level 2, the identical blocking call** — `slowBackendCall` in `VirtualThreadBlocking` is byte-for-byte the same method as in `PlatformThreadBlocking`; the only change anywhere in the program is swapping `Executors.newFixedThreadPool(4)` for `Executors.newVirtualThreadPerTaskExecutor()`.
3. **Level 2, why virtual threads change the outcome** — each submitted task gets its own cheap, JVM-managed virtual thread; when that virtual thread calls `Thread.sleep(100)`, the JVM's scheduler unmounts it from its underlying platform thread (also called a "carrier thread") during the wait, freeing that platform thread to run other virtual threads' work in the meantime — the blocking *call* is unchanged, but its cost to the system is fundamentally different.
4. **Level 2, the measured result** — all 20 requests complete in roughly the time of a single 100ms wait, not five sequential batches, despite using the identical blocking `Thread.sleep` call as Level 1 — demonstrating that virtual threads deliver much of the reactive model's throughput benefit without requiring any change to the blocking, imperative code itself.
5. **Level 3, the blocking style's readability** — `getOrderViewBlocking` reads as an ordinary sequence of statements: call `fetchOrder`, then call `fetchCustomer` using its result, wrapped in a standard `try`/`catch` for error handling — no operator chaining, no `.flatMap`, no separate reactive error-handling operators.
6. **Level 3, error handling as plain Java** — when `fetchOrder(999)` throws, the `catch` block catches it directly and immediately, printing a message and returning `null` — this is the exact same `try`/`catch` mechanism used throughout ordinary, non-reactive Java code, requiring no additional reactive-specific error-handling knowledge.
7. **Level 3, both cases run concurrently on virtual threads** — `successCase` and `failureCase` are each submitted as separate tasks to `virtualThreads`, running concurrently on their own lightweight virtual threads; both `Future.get()` calls in `main` correctly retrieve their respective results, one a fully populated `CombinedView` and the other `null` (having gone through the `catch` block) — demonstrating that this entire program, written in a style immediately familiar to any traditional Spring MVC developer, still achieves genuine, efficient concurrency, which is precisely the value proposition Spring Cloud Gateway MVC offers as an alternative to the reactive implementation.

## 7. Gotchas & takeaways

> **Gotcha:** virtual threads don't help with CPU-bound blocking — a genuinely CPU-intensive computation (not I/O wait) still occupies its carrier platform thread for its actual duration, since there's no I/O operation for the JVM to unmount the virtual thread during; virtual threads specifically address the "thread sitting idle waiting on I/O" problem, not "thread doing genuine CPU work," so a gateway doing heavy CPU-bound transformation work per request won't see the same dramatic improvement virtual threads provide for I/O-bound backend calls.

- Spring Cloud Gateway MVC provides the same route/predicate/filter model as the reactive Spring Cloud Gateway, but runs on the traditional servlet stack with ordinary, blocking, imperative code.
- Java virtual threads let blocking-style code achieve much of the reactive model's I/O-bound throughput efficiency, since a blocked virtual thread doesn't tie up its underlying, scarce platform thread during the wait.
- This lets a team keep the familiar mental model of ordinary sequential code and standard `try`/`catch` error handling, rather than adopting reactive programming's different chaining and error-handling operators.
- Choosing between the reactive and MVC-based gateway implementations is largely a question of team familiarity and existing ecosystem consistency, not a hard performance requirement, given virtual threads' efficiency gains.
- Virtual threads specifically address I/O-bound blocking; genuinely CPU-bound work still occupies its carrier thread for its actual duration and doesn't see the same improvement.
