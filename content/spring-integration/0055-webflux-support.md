---
card: spring-integration
gi: 55
slug: webflux-support
title: "WebFlux support"
---

## 1. What it is

WebFlux support (`WebFlux.inboundGateway(...)`/`WebFlux.outboundGateway(...)`) is the reactive counterpart to the HTTP support from card 0054, built on Spring WebFlux and Project Reactor instead of the Servlet API. Where `Http.outboundGateway` performs a blocking HTTP call and holds a thread until the response arrives, `WebFlux.outboundGateway` returns a `Mono`/`Flux` immediately and completes the response asynchronously — connecting HTTP integration to `FluxMessageChannel`'s (card 0014) reactive, backpressure-aware world instead of the imperative, thread-per-request model.

## 2. Why & when

You reach for WebFlux support specifically when a flow's HTTP integration needs to be non-blocking, or already lives in a reactive application:

- **The application is already built on Spring WebFlux** (reactive controllers, R2DBC, reactive service clients) — using WebFlux's HTTP gateways keeps the entire request-handling path non-blocking end to end, avoiding the thread-per-request cost `Http.inboundGateway`'s Servlet-based model carries.
- **An outbound HTTP call shouldn't hold a thread hostage while waiting for a response** — under high concurrency, blocking threads on slow external HTTP calls (as `Http.outboundGateway`, card 0054, does) can exhaust a thread pool; `WebFlux.outboundGateway` frees the calling thread immediately, with the response handled asynchronously once it arrives.
- **The flow needs genuine backpressure on a high-volume HTTP interaction** — connecting HTTP handling to a `FluxMessageChannel` (card 0014) brings the same subscriber-driven demand control described there, letting a slow downstream consumer signal reduced demand rather than being overwhelmed by request volume.

## 3. Core concept

Think of `Http.outboundGateway` (card 0054) like calling a company's support line and staying on hold, tying up your own phone the entire time until someone answers — the thread is blocked, unavailable for anything else, for the full duration of the wait. `WebFlux.outboundGateway` is like leaving a callback request instead: you hang up immediately (the thread is freed for other work), and when the company is ready to respond, they call *you* back — your line was never tied up waiting, even though the eventual response still arrives and gets handled.

```java
@Bean
public IntegrationFlow reactiveOutboundFlow() {
    return IntegrationFlow.from("chargeRequests")
        .handle(WebFlux.outboundGateway("https://payments.example.com/charge")
            .httpMethod(HttpMethod.POST)
            .expectedResponseType(ChargeResult.class))       // returns a Mono<ChargeResult> internally
        .channel("chargeResults")
        .get();
}
```

The calling thread that triggers this outbound call is never blocked waiting for the payment service's response — the WebFlux/Reactor machinery underneath handles the async completion and routes the eventual result onward once it actually arrives.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Http.outboundGateway blocks the calling thread until a response arrives; WebFlux.outboundGateway returns immediately and completes the response asynchronously via a Mono, freeing the thread for other work in the meantime" >
  <text x="150" y="20" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Http.outboundGateway (blocking)</text>
  <rect x="20" y="35" width="110" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="75" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">thread</text>
  <rect x="150" y="35" width="200" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="3,2"/>
  <text x="250" y="59" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">BLOCKED waiting for response</text>

  <text x="490" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">WebFlux.outboundGateway (non-blocking)</text>
  <rect x="360" y="135" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="405" y="159" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">thread</text>
  <line x1="450" y1="155" x2="490" y2="155" stroke="#6db33f" stroke-width="2" marker-end="url(#wf1)"/>
  <text x="470" y="145" fill="#6db33f" font-size="6" text-anchor="middle" font-family="sans-serif">FREED</text>
  <rect x="500" y="135" width="120" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="560" y="153" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Mono completes</text>
  <text x="560" y="166" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">async, later</text>

  <defs>
    <marker id="wf1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The blocking model ties up a thread for the entire wait; the reactive model frees the thread immediately and completes the response asynchronously.

## 5. Runnable example

The scenario: an outbound HTTP call to a payment service, contrasted between blocking and reactive styles, starting with a basic blocking baseline, then the same interaction expressed reactively with `CompletableFuture` (standing in for `Mono`, since real `Mono`/WebFlux requires the full reactor dependency), and finally comparing thread usage under concurrent load.

### Level 1 — Basic

```java
// BlockingBaselineDemo.java
// Establishes the blocking baseline (what Http.outboundGateway, card 0054, does) so Level 2 can
// contrast it directly against the non-blocking WebFlux equivalent.
import java.util.concurrent.*;

public class BlockingBaselineDemo {
    static String slowExternalCall() throws InterruptedException {
        Thread.sleep(300); // simulates network latency to a payment service
        return "{\"approved\":true}";
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("Thread " + Thread.currentThread().getName() + " calling out...");
        String result = slowExternalCall(); // BLOCKS this thread for the full 300ms
        System.out.println("Thread " + Thread.currentThread().getName() + " got result: " + result
            + " (was BLOCKED the entire time, unable to do anything else)");
    }
}
```

How to run: `java BlockingBaselineDemo.java`. Expected output: a "calling out..." line, then (after a real ~300ms pause during which the thread is fully occupied) the result line — the calling thread had nothing else to do for the entire duration, exactly `Http.outboundGateway`'s (card 0054) blocking behavior.

### Level 2 — Intermediate

The same interaction expressed non-blocking, using `CompletableFuture` (standing in for `Mono`, since it's built into the JDK and demonstrates the identical "return immediately, complete later" principle without requiring the Reactor dependency) — the calling thread is freed immediately, and completion happens asynchronously on a different thread.

```java
// NonBlockingEquivalentDemo.java
import java.util.concurrent.*;

public class NonBlockingEquivalentDemo {
    static CompletableFuture<String> asyncExternalCall(ExecutorService pool) {
        return CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(300); } catch (InterruptedException ignored) {} // simulated network latency
            return "{\"approved\":true}";
        }, pool);
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(2);

        System.out.println("Thread " + Thread.currentThread().getName() + " initiating async call...");
        CompletableFuture<String> future = asyncExternalCall(pool); // returns IMMEDIATELY — thread is FREE now
        System.out.println("Thread " + Thread.currentThread().getName() + " is FREE — doing other work while waiting");

        future.thenAccept(result -> System.out.println("Thread " + Thread.currentThread().getName()
            + " (a DIFFERENT thread) completed with: " + result));

        Thread.sleep(400); // let the async completion happen before main exits
        pool.shutdown();
    }
}
```

How to run: `java NonBlockingEquivalentDemo.java`. Expected output: `Thread main initiating async call...`, immediately followed by `Thread main is FREE — doing other work while waiting` (no delay at all), and then, roughly 300ms later, `Thread pool-1-thread-N (a DIFFERENT thread) completed with: {"approved":true}` — the main thread never blocked; it moved on immediately, and the eventual result was handled by whichever pool thread happened to complete the async work.

### Level 3 — Advanced

Comparing thread usage under concurrent load — 10 simultaneous slow calls handled blocking-style (needing 10 dedicated threads, one per in-flight call) versus non-blocking style (a small pool handles all 10, since no thread is ever held hostage waiting) — makes the practical throughput implication concrete.

```java
// ThreadUsageComparisonDemo.java
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public class ThreadUsageComparisonDemo {
    public static void main(String[] args) throws InterruptedException {
        int concurrentCalls = 10;

        // BLOCKING style: needs one thread PER in-flight call, held hostage for its entire duration
        AtomicInteger peakBlockingThreads = new AtomicInteger(0);
        ExecutorService blockingPool = Executors.newCachedThreadPool();
        CountDownLatch blockingDone = new CountDownLatch(concurrentCalls);
        for (int i = 0; i < concurrentCalls; i++) {
            blockingPool.submit(() -> {
                peakBlockingThreads.incrementAndGet();
                try { Thread.sleep(200); } finally {
                    peakBlockingThreads.decrementAndGet();
                    blockingDone.countDown();
                }
            });
        }
        blockingDone.await();
        blockingPool.shutdown();

        // NON-BLOCKING style: a SMALL fixed pool handles all 10, since no thread waits idle for a response
        int smallPoolSize = 2;
        ExecutorService reactivePool = Executors.newFixedThreadPool(smallPoolSize);
        CountDownLatch reactiveDone = new CountDownLatch(concurrentCalls);
        long start = System.currentTimeMillis();
        for (int i = 0; i < concurrentCalls; i++) {
            CompletableFuture.supplyAsync(() -> {
                try { Thread.sleep(20); } catch (InterruptedException ignored) {} // quick non-blocking dispatch
                return "done";
            }, reactivePool).thenAccept(r -> reactiveDone.countDown());
        }
        reactiveDone.await();
        long elapsed = System.currentTimeMillis() - start;
        reactivePool.shutdown();

        System.out.println("Blocking style needed up to " + concurrentCalls + " concurrently-held threads for "
            + concurrentCalls + " in-flight calls");
        System.out.println("Non-blocking style handled all " + concurrentCalls + " calls with just "
            + smallPoolSize + " pool threads, in ~" + elapsed + "ms");
    }
}
```

How to run: `java ThreadUsageComparisonDemo.java`. Expected output: `Blocking style needed up to 10 concurrently-held threads for 10 in-flight calls` then `Non-blocking style handled all 10 calls with just 2 pool threads, in ~<some small number>ms` — the blocking approach required a thread per in-flight call (a `newCachedThreadPool` grows to accommodate exactly this), while the non-blocking approach handled the same volume with a fixed, much smaller pool, since no thread was ever held idle waiting on a slow response.

## 6. Walkthrough

Tracing `NonBlockingEquivalentDemo` in execution order:

1. `main` prints its "initiating async call" message, then calls `asyncExternalCall(pool)`.
2. Inside `asyncExternalCall`, `CompletableFuture.supplyAsync(..., pool)` submits the slow work (the simulated 300ms network call) to the pool and *immediately* returns a `CompletableFuture<String>` representing that eventual result — critically, `supplyAsync` does not wait for the work to finish; it hands off the work and returns right away.
3. Control returns to `main` essentially instantly; `main` prints its "is FREE" message right after — no 300ms wait occurred on the main thread at all, unlike `BlockingBaselineDemo`'s equivalent line.
4. `future.thenAccept(...)` registers a callback to run once the future eventually completes — this registration also returns immediately; it doesn't block waiting for completion either.
5. Meanwhile, on a separate pool thread, the actual `Thread.sleep(300)` and subsequent computation run independently of the main thread's continued execution.
6. Once that pool thread's work finishes (around the 300ms mark), the `CompletableFuture` completes, and the registered `thenAccept` callback runs — on that same pool thread, not the main thread — printing the final confirmation, demonstrating that the response was handled asynchronously, by a different thread, entirely decoupled from whatever the main thread had been doing since it initiated the call.

```
main: "initiating async call..." -> supplyAsync(...) submits work, returns IMMEDIATELY
main: "is FREE" (printed with ~0ms delay, thread was NEVER blocked)
main: registers thenAccept callback, continues (sleeps here only to let the demo finish cleanly)

[pool thread, ~300ms later]: slow work completes -> thenAccept callback fires -> prints result
```

## 7. Gotchas & takeaways

> Reactive/non-blocking code (`WebFlux.outboundGateway`, `Mono`/`Flux`, `CompletableFuture`) only delivers its thread-efficiency benefit if *nothing* in the call chain blocks — a single blocking call (a JDBC call on a non-reactive `DataSource`, a synchronous library call) buried inside an otherwise-reactive pipeline silently reintroduces thread-blocking, often without any obvious error, just degraded throughput under load. Mixing blocking and non-blocking code carelessly is a common, hard-to-diagnose source of reactive applications not actually delivering their expected scalability benefit.

- WebFlux support (`WebFlux.inboundGateway`/`WebFlux.outboundGateway`) is the non-blocking, reactive counterpart to the Servlet-based HTTP support from card 0054, built on Spring WebFlux and Project Reactor.
- Use it when a flow's HTTP integration should avoid holding a thread hostage while waiting for a response, or when the surrounding application is already built reactively (WebFlux controllers, R2DBC, other reactive clients).
- The core tradeoff: blocking HTTP gateways need roughly one thread per in-flight request; non-blocking gateways can handle far more concurrent in-flight requests with a much smaller thread pool, since no thread waits idle for a response.
- WebFlux outbound calls connect naturally to `FluxMessageChannel`'s (card 0014) reactive backpressure model, letting a slow downstream consumer's demand genuinely throttle upstream request volume.
- The efficiency benefit only holds if the entire call chain stays non-blocking — a single blocking call embedded in an otherwise-reactive pipeline silently undermines the whole point, often without any obvious symptom besides reduced throughput under load.
