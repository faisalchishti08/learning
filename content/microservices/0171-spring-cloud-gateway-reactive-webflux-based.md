---
card: microservices
gi: 171
slug: spring-cloud-gateway-reactive-webflux-based
title: "Spring Cloud Gateway (reactive, WebFlux-based)"
---

## 1. What it is

Spring Cloud Gateway is Spring's official API gateway implementation, built on Spring WebFlux's reactive, non-blocking foundation — every request is handled through a chain of asynchronous, non-blocking operations rather than dedicating one blocking thread per in-flight request, letting a modest number of threads handle a large volume of concurrent, mostly-I/O-bound gateway traffic (routing, waiting on backend responses) efficiently.

## 2. Why & when

A gateway's core workload — receive a request, wait for a backend to respond, return the response — is fundamentally I/O-bound: most of the time spent per request is waiting on network I/O, not doing CPU work. A traditional blocking, thread-per-request model wastes threads sitting idle during that wait, meaning the number of concurrent in-flight requests a gateway can handle is capped by how many threads the JVM can reasonably run, which becomes a real bottleneck under high concurrent load. Spring Cloud Gateway's reactive foundation means a request's "waiting for the backend" period doesn't block a thread at all — the thread is freed to handle other work, and only resumes processing this particular request once the backend's response actually arrives.

Reach for Spring Cloud Gateway specifically when building a Spring-based gateway that needs to handle significant concurrent request volume efficiently, and the team is comfortable with (or willing to adopt) reactive programming's different mental model. For scenarios where blocking, imperative-style code is preferred and expected concurrency is modest, [Spring Cloud Gateway MVC](0172-spring-cloud-gateway-mvc-servlet-based.md)'s traditional servlet-based alternative may be a simpler fit.

## 3. Core concept

Routes and filters are expressed as reactive operators over a `Mono<ServerWebExchange>` (a publisher representing the eventual outcome of processing one exchange); the gateway never blocks a thread waiting on a backend call, instead composing asynchronous operations that resume automatically once each step's result becomes available.

```java
@Bean
public RouteLocator customRouteLocator(RouteLocatorBuilder builder) {
    return builder.routes()
        .route("order_route", r -> r.path("/orders/**")
            .filters(f -> f.addRequestHeader("X-Gateway", "spring-cloud-gateway"))
            .uri("http://order-service:8080"))
        .build();
    // internally: every step is reactive -- NO thread blocks waiting for order-service's response
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A blocking, thread-per-request model dedicates one thread per in-flight request, idle while waiting on the backend. A reactive model frees the thread during that wait, letting a small thread pool handle many more concurrent requests" >
  <text x="150" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Blocking (thread-per-request)</text>
  <rect x="30" y="40" width="60" height="100" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="60" y="95" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">thread 1</text>
  <text x="60" y="110" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">BLOCKED</text>
  <rect x="100" y="40" width="60" height="100" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="130" y="95" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">thread 2</text>
  <text x="130" y="110" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">BLOCKED</text>
  <rect x="170" y="40" width="60" height="100" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/><text x="200" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">no more</text>
  <text x="200" y="110" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">threads!</text>

  <text x="480" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Reactive (non-blocking)</text>
  <rect x="380" y="40" width="60" height="100" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/><text x="410" y="95" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">thread 1</text>
  <text x="410" y="110" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">handles MANY</text>
  <text x="480" y="140" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">freed during I/O wait, handles other requests meanwhile</text>

  <defs>
    <marker id="arr52" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

A small pool of non-blocking threads can serve far more concurrent, I/O-bound requests than one thread pinned per in-flight request.

## 5. Runnable example

Scenario: a gateway forwarding requests to a slow backend that starts with a simulated blocking model showing thread exhaustion under load, moves to a simulated non-blocking, callback-based model that frees threads during the wait, and finally demonstrates the throughput difference numerically by measuring how many concurrent requests each model can actually sustain with the same small thread pool.

### Level 1 — Basic

```java
// File: BlockingThreadPerRequest.java -- each in-flight request BLOCKS a thread
// for the ENTIRE backend wait; a small pool runs out of threads under load.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class BlockingThreadPerRequest {
    static String blockingBackendCall(int requestId) throws InterruptedException {
        Thread.sleep(200); // simulates waiting on a slow backend -- the thread does NOTHING else during this
        return "response for request " + requestId;
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(2); // ONLY 2 threads available
        AtomicInteger completed = new AtomicInteger();
        long start = System.currentTimeMillis();

        for (int i = 1; i <= 6; i++) {
            int requestId = i;
            pool.submit(() -> {
                try {
                    String result = blockingBackendCall(requestId); // BLOCKS this thread for 200ms
                    completed.incrementAndGet();
                    System.out.println(result);
                } catch (InterruptedException ignored) { }
            });
        }
        pool.shutdown();
        pool.awaitTermination(3, TimeUnit.SECONDS);

        System.out.println("6 requests, 2 threads: took ~" + (System.currentTimeMillis() - start) + "ms (requests QUEUE UP behind the 2 blocked threads)");
    }
}
```

**How to run:** `javac BlockingThreadPerRequest.java && java BlockingThreadPerRequest` (JDK 17+).

With only 2 threads, 6 requests each requiring a 200ms blocking wait take roughly 600ms total (3 sequential batches of 2), since a blocked thread can serve nothing else during its wait.

### Level 2 — Intermediate

```java
// File: NonBlockingCallbackModel.java -- the SAME work, but the thread is FREED
// during the wait via a callback, mirroring the reactive model's core mechanism.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.function.*;

public class NonBlockingCallbackModel {
    static ScheduledExecutorService timer = Executors.newScheduledThreadPool(1); // simulates the I/O layer notifying us later

    // NON-BLOCKING: registers a callback and returns IMMEDIATELY, freeing the calling thread
    static void nonBlockingBackendCall(int requestId, Consumer<String> onComplete) {
        timer.schedule(() -> onComplete.accept("response for request " + requestId), 200, TimeUnit.MILLISECONDS);
        // the calling thread does NOT wait here -- it returns immediately, free to do other work
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(2); // SAME 2-thread pool as Level 1
        CountDownLatch latch = new CountDownLatch(6);
        long start = System.currentTimeMillis();

        for (int i = 1; i <= 6; i++) {
            int requestId = i;
            pool.submit(() -> {
                // this thread SUBMITS the call and is immediately free for other work -- no blocking wait here
                nonBlockingBackendCall(requestId, result -> {
                    System.out.println(result);
                    latch.countDown();
                });
            });
        }
        latch.await(3, TimeUnit.SECONDS);
        pool.shutdown();
        timer.shutdown();

        System.out.println("6 requests, 2 threads, NON-BLOCKING: took ~" + (System.currentTimeMillis() - start) + "ms (much closer to the SINGLE 200ms wait, not 3x it)");
    }
}
```

**How to run:** `javac NonBlockingCallbackModel.java && java NonBlockingCallbackModel` (JDK 17+).

Expected output (timing approximate, roughly 200-250ms instead of Level 1's ~600ms):
```
response for request 1
response for request 2
response for request 3
response for request 4
response for request 5
response for request 6
6 requests, 2 threads, NON-BLOCKING: took ~210ms (much closer to the SINGLE 200ms wait, not 3x it)
```

All six requests' backend calls were submitted essentially immediately (since submitting a non-blocking call doesn't tie up a pool thread), so they all complete around the same time — roughly one 200ms wait, not three sequential 200ms waits.

### Level 3 — Advanced

```java
// File: ThroughputComparisonAtScale.java -- measures how many CONCURRENT
// requests a fixed 2-thread pool can sustain under EACH model, making the
// practical throughput difference numerically explicit.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.function.*;

public class ThroughputComparisonAtScale {
    static String blockingBackendCall() throws InterruptedException { Thread.sleep(100); return "ok"; }

    static ScheduledExecutorService timer = Executors.newScheduledThreadPool(1);
    static void nonBlockingBackendCall(Consumer<String> onComplete) {
        timer.schedule(() -> onComplete.accept("ok"), 100, TimeUnit.MILLISECONDS);
    }

    public static void main(String[] args) throws InterruptedException {
        int requestCount = 20;

        // BLOCKING model, 2 threads
        ExecutorService blockingPool = Executors.newFixedThreadPool(2);
        long blockingStart = System.currentTimeMillis();
        CountDownLatch blockingLatch = new CountDownLatch(requestCount);
        for (int i = 0; i < requestCount; i++) {
            blockingPool.submit(() -> {
                try { blockingBackendCall(); } catch (InterruptedException ignored) { }
                blockingLatch.countDown();
            });
        }
        blockingLatch.await(10, TimeUnit.SECONDS);
        long blockingElapsed = System.currentTimeMillis() - blockingStart;
        blockingPool.shutdown();

        // NON-BLOCKING model, SAME 2 threads
        ExecutorService nonBlockingPool = Executors.newFixedThreadPool(2);
        long nonBlockingStart = System.currentTimeMillis();
        CountDownLatch nonBlockingLatch = new CountDownLatch(requestCount);
        for (int i = 0; i < requestCount; i++) {
            nonBlockingPool.submit(() -> nonBlockingBackendCall(result -> nonBlockingLatch.countDown()));
        }
        nonBlockingLatch.await(10, TimeUnit.SECONDS);
        long nonBlockingElapsed = System.currentTimeMillis() - nonBlockingStart;
        nonBlockingPool.shutdown();
        timer.shutdown();

        System.out.println(requestCount + " requests, 2 threads, BLOCKING model: ~" + blockingElapsed + "ms");
        System.out.println(requestCount + " requests, 2 threads, NON-BLOCKING model: ~" + nonBlockingElapsed + "ms");
        System.out.println("The SAME 2 threads handled the SAME 20 requests far faster non-blocking -- this gap widens further as concurrency increases.");
    }
}
```

**How to run:** `javac ThroughputComparisonAtScale.java && java ThroughputComparisonAtScale` (JDK 17+).

Expected output (approximate; blocking scales with `ceil(requestCount / threads) * 100ms`, non-blocking stays close to `100ms` regardless of request count):
```
20 requests, 2 threads, BLOCKING model: ~1000ms
20 requests, 2 threads, NON-BLOCKING model: ~110ms
The SAME 2 threads handled the SAME 20 requests far faster non-blocking -- this gap widens further as concurrency increases.
```

## 6. Walkthrough

1. **Level 1** — `blockingBackendCall` calls `Thread.sleep(200)` directly on whatever thread invokes it, meaning that thread is completely unavailable for any other work for the full 200ms; with only 2 threads available, the six submitted tasks must queue and run in three sequential waves of two.
2. **Level 1, the measured cost** — the total elapsed time (~600ms) is roughly three times the single-request wait time (200ms), directly reflecting that only 2 requests could be "in flight" from the pool's perspective at any given moment.
3. **Level 2, the callback-based non-blocking call** — `nonBlockingBackendCall` calls `timer.schedule(...)`, which registers a callback to run *later*, on a separate timer thread, and returns to its caller *immediately*, without ever calling anything that blocks the calling thread.
4. **Level 2, the pool thread freed instantly** — because submitting a task to `pool` that calls `nonBlockingBackendCall` returns essentially instantly (the actual 200ms wait happens elsewhere, on the `timer` thread), all six of the pool's submitted tasks complete their *submission* almost immediately, freeing the 2 pool threads to accept further work rather than sitting blocked.
5. **Level 2, the measured improvement** — total elapsed time drops to roughly 200-250ms (close to a single wait period) instead of Level 1's ~600ms, because the non-blocking model doesn't force the six 200ms waits to happen in sequential batches of two — they can all be "in flight" simultaneously, since none of them occupies a pool thread for their duration.
6. **Level 3, scaling up the concurrency** — using 20 requests instead of 6 against the same 2-thread pools makes the difference more dramatic: the blocking model's total time scales roughly linearly with `requestCount / threads`, reaching about 1000ms (10 sequential batches of 2 at 100ms each), while the non-blocking model's total time barely increases past a single 100ms wait period, since none of the 20 non-blocking calls ever occupies a pool thread for the duration of its wait.
7. **Level 3, why this matters for a real gateway** — Spring Cloud Gateway's reactive foundation applies exactly this non-blocking principle to every routed request's wait on a backend response; a gateway handling hundreds or thousands of concurrent in-flight requests, each mostly waiting on I/O rather than doing CPU work, can serve dramatically more concurrent traffic with a modest, fixed-size thread pool than a blocking, thread-per-request model ever could with the same thread count — precisely the throughput gap this level's measurements make concrete.

## 7. Gotchas & takeaways

> **Gotcha:** reactive, non-blocking code is unforgiving of accidentally blocking calls slipping in anywhere in the chain — a single blocking database call, a blocking file read, or even certain blocking logging configurations, buried inside an otherwise-reactive filter or route, can stall one of the gateway's few event-loop threads and quietly degrade throughput for every other concurrently in-flight request sharing that thread, not just the one making the blocking call.

- Spring Cloud Gateway is built on Spring WebFlux's reactive, non-blocking foundation, letting a small, fixed thread pool handle a large volume of concurrent, I/O-bound gateway traffic efficiently.
- The core mechanism is freeing a thread during an I/O wait (like waiting on a backend response) rather than blocking it for that wait's full duration, letting that thread serve other requests in the meantime.
- This produces dramatically higher throughput than a blocking, thread-per-request model under high concurrency, since throughput is no longer capped by how many threads can be blocked simultaneously.
- The throughput gap between blocking and non-blocking models widens as concurrent request volume increases, making the reactive approach's benefit most pronounced under genuinely high load.
- Reactive code is fragile to accidentally introduced blocking calls, which can stall a shared event-loop thread and degrade performance for unrelated concurrent requests — this fragility is a real cost of the reactive model's benefits.
