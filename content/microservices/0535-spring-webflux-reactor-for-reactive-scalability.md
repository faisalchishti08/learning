---
card: microservices
gi: 535
slug: spring-webflux-reactor-for-reactive-scalability
title: "Spring WebFlux / Reactor for reactive scalability"
---

## 1. What it is

**Spring WebFlux** is Spring's reactive web framework, built on **Project Reactor** (`Mono` and `Flux`, the reactive types representing "zero-or-one async result" and "zero-to-many async results" respectively), providing the same kind of [asynchronous, non-blocking processing](0516-asynchronous-reactive-for-throughput.md) discussed earlier, but as a first-class, complete web stack — reactive controllers, a reactive HTTP client (`WebClient`), and a small, fixed pool of event-loop threads handling potentially thousands of concurrent in-flight requests, as an alternative to Spring MVC's traditional one-thread-per-request servlet model.

## 2. Why & when

You reach for WebFlux specifically when a service's workload is dominated by waiting on I/O across many concurrent requests, and the thread-per-request model would require an impractically large thread pool to keep up:

- **Spring MVC's traditional model ties one thread to one request for its entire duration**, including all the time spent waiting on downstream calls — a service handling many slow, I/O-heavy requests concurrently needs a correspondingly large thread pool, and threads themselves aren't free (each carries real memory overhead for its stack).
- **WebFlux runs on a small, fixed number of event-loop threads** (by default, one per CPU core), and never blocks one of them waiting on I/O — a `Mono`/`Flux` chain describes what should happen when data becomes available, and the event loop moves on to other work in the meantime, picking the callback back up once the awaited data actually arrives.
- **`WebClient` is WebFlux's reactive HTTP client**, replacing the traditional blocking `RestTemplate` — calling a downstream service returns a `Mono<Response>` immediately, without blocking the calling thread, which matters enormously for high-fan-out services (an API gateway calling several downstream services per incoming request) where the difference between blocking and non-blocking downstream calls determines whether the whole benefit of WebFlux is actually realized.
- **The trade-off is real and worth weighing deliberately**: reactive code is harder to write, debug, and reason about than straightforward blocking code — stack traces fragment across asynchronous boundaries, and simple sequential logic becomes a chain of composed operators. WebFlux earns its complexity on genuinely I/O-heavy, high-concurrency services; a low-traffic or CPU-bound service gains little from it and pays the full complexity cost regardless.

## 3. Core concept

Think of a reactive pipeline as an assembly line with sensors instead of workers standing and staring at each station waiting for parts to arrive. A traditional (blocking) worker at station 3 stands there, arms crossed, doing nothing until station 2 finishes and hands off a part — one worker, one station, idle whenever there's nothing to do right this second. A reactive pipeline instead wires a sensor to station 3 that fires an action automatically the instant a part arrives, freeing whoever would have stood there to help elsewhere in the meantime — the same small number of people (event-loop threads) can service far more stations (concurrent requests) than a one-worker-per-station model, because nobody stands idle waiting.

Concretely:

1. **`Mono<T>` represents zero-or-one asynchronous result** — the reactive equivalent of a `CompletableFuture<T>`, but composable through a rich set of operators (`.map`, `.flatMap`, `.filter`) that describe *what to do when the value arrives*, without ever blocking to wait for it.
2. **`Flux<T>` represents zero-to-many asynchronous results** — a stream of values arriving over time, useful for things like server-sent events, streaming query results, or any sequence of items produced asynchronously.
3. **A reactive controller method returns a `Mono`/`Flux` rather than a plain value** — Spring WebFlux subscribes to it on the caller's behalf and writes the response once (or as, for a `Flux`) the reactive chain produces its result, never dedicating a thread to blocking on that production.
4. **`WebClient.get().uri(...).retrieve().bodyToMono(SomeType.class)`** issues a non-blocking HTTP call and returns a `Mono<SomeType>` immediately — chaining `.flatMap(...)` onto it composes what happens with the response once it arrives, all without blocking any thread in the interim, which is what lets a WebFlux-based gateway fan out to several downstream services concurrently using only a handful of threads.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring MVC ties one thread per request for its full duration including waits; Spring WebFlux uses a small fixed pool of event-loop threads that never block, composing Mono/Flux chains that resume when data arrives">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring MVC</text>
  <rect x="20" y="35" width="260" height="30" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">thread-per-request, blocked on downstream I/O</text>
  <text x="150" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">N concurrent requests need ~N threads</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring WebFlux</text>
  <rect x="380" y="35" width="260" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Mono/Flux chain, event loop resumes on data</text>
  <text x="510" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">a few event-loop threads serve thousands of requests</text>
</svg>

MVC ties a thread to every in-flight wait; WebFlux describes what to do when data arrives and frees the thread in the meantime.

## 5. Runnable example

Scenario: a gateway endpoint aggregating a price quote from a downstream pricing service. We start with a plain Java model of the reactive "describe, don't block" idea, extend it to the real WebFlux controller and `WebClient` call, then handle the hard case: composing two concurrent downstream calls with a timeout and fallback, reactively.

### Level 1 — Basic

```java
// File: ReactiveConceptBasic.java -- models the CORE reactive idea using
// plain CompletableFuture (Reactor's Mono adds richer composition, but the
// underlying "describe what happens when data arrives, don't block" idea is the same).
import java.util.concurrent.*;

public class ReactiveConceptBasic {
    static CompletableFuture<Double> fetchPriceAsync(String item) {
        return CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(100); } catch (InterruptedException e) { throw new RuntimeException(e); }
            return 42.50;
        });
    }

    public static void main(String[] args) throws Exception {
        System.out.println("[" + Thread.currentThread().getName() + "] issuing call, NOT blocking yet");
        CompletableFuture<Double> priceFuture = fetchPriceAsync("widget");

        // describes WHAT TO DO once the price arrives -- doesn't block to find out
        CompletableFuture<String> responseFuture = priceFuture.thenApply(price -> "Price: $" + price);

        System.out.println("[" + Thread.currentThread().getName() + "] chain composed, main thread free to do other work");
        System.out.println("Final response: " + responseFuture.get()); // only blocks HERE, where we actually need the result
    }
}
```

How to run: `java ReactiveConceptBasic.java`

`.thenApply(...)` describes what should happen to the price *once it arrives*, without blocking the calling thread to wait for it right away — the chain is fully composed and returned before the underlying 100ms sleep even completes. This is the same core idea Reactor's `Mono.map(...)` embodies, just using `CompletableFuture` as a simpler, JDK-native stand-in for the concept.

### Level 2 — Intermediate

```java
// File: WebFluxRealShape.java -- the REAL Spring WebFlux shape: a reactive
// controller calling a downstream service via WebClient, composed with Mono.
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

public class WebFluxRealShape {

    @RestController
    static class QuoteController {
        private final WebClient webClient;

        QuoteController(WebClient.Builder webClientBuilder) {
            this.webClient = webClientBuilder.baseUrl("http://pricing-service").build();
        }

        @GetMapping("/quote/{item}")
        public Mono<String> getQuote(@PathVariable String item) {
            // non-blocking downstream call: returns a Mono IMMEDIATELY, the actual HTTP
            // call and response happen asynchronously on the event loop
            return webClient.get()
                .uri("/prices/{item}", item)
                .retrieve()
                .bodyToMono(Double.class)
                .map(price -> "Price for " + item + ": $" + price); // describes what to do WHEN the price arrives
        }
    }
}
```

How to run: requires `spring-boot-starter-webflux` on the classpath; run via `mvn spring-boot:run` and `GET /quote/widget` against a running instance — the calling thread handling this request is freed back to the event loop the moment `webClient.get()...` is issued, and only resumes processing this specific request once the downstream response actually arrives.

`getQuote` returns `Mono<String>` rather than a plain `String` — Spring WebFlux subscribes to this `Mono` on the framework's behalf and writes the HTTP response once the chain completes, but the request-handling thread is never blocked waiting for `webClient`'s downstream call in between; it's freed to handle other requests' event-loop work in the meantime, which is precisely what lets a small, fixed thread pool serve many more concurrent in-flight requests than a blocking, one-thread-per-request equivalent would allow.

### Level 3 — Advanced

```java
// File: WebFluxComposedTimeout.java -- composes TWO concurrent downstream
// calls (price + inventory) reactively, each with its OWN timeout and
// fallback, so neither dependency's slowness stalls the whole response.
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import java.time.Duration;

public class WebFluxComposedTimeout {

    @RestController
    static class QuoteController {
        private final WebClient webClient;
        QuoteController(WebClient.Builder builder) { this.webClient = builder.baseUrl("http://backend").build(); }

        Mono<Double> fetchPrice(String item) {
            return webClient.get().uri("/prices/{item}", item).retrieve().bodyToMono(Double.class)
                .timeout(Duration.ofMillis(500))
                .onErrorReturn(-1.0); // fallback: "price unavailable" sentinel, reactively
        }

        Mono<Integer> fetchInventory(String item) {
            return webClient.get().uri("/inventory/{item}", item).retrieve().bodyToMono(Integer.class)
                .timeout(Duration.ofMillis(500))
                .onErrorReturn(-1);
        }

        @GetMapping("/quote/{item}")
        public Mono<String> getQuote(@PathVariable String item) {
            Mono<Double> priceMono = fetchPrice(item);
            Mono<Integer> inventoryMono = fetchInventory(item);

            // Mono.zip runs BOTH reactive chains concurrently and combines their results
            // once BOTH have completed (or fallen back), never blocking any thread meanwhile
            return Mono.zip(priceMono, inventoryMono)
                .map(tuple -> {
                    double price = tuple.getT1();
                    int inventory = tuple.getT2();
                    return "price=" + (price < 0 ? "unavailable" : "$" + price)
                         + ", inventory=" + (inventory < 0 ? "unavailable" : inventory);
                });
        }
    }
}
```

How to run: requires `spring-boot-starter-webflux`; run via `mvn spring-boot:run` and `GET /quote/widget` — if the pricing backend is slow (past 500ms) while inventory responds quickly, the response still returns in roughly 500ms with `price=unavailable, inventory=<value>`, never blocking any thread on the slow pricing call beyond its timeout.

`Mono.zip(priceMono, inventoryMono)` subscribes to both reactive chains concurrently and only proceeds to `.map(...)` once *both* have reached a terminal state (a real value or, via `onErrorReturn`, a fallback) — this is the reactive equivalent of `CompletableFuture.allOf(...)` from the earlier async example, composed declaratively rather than imperatively, and still without ever blocking a thread to wait for either downstream call.

## 6. Walkthrough

Trace a request to `GET /quote/widget` against `WebFluxComposedTimeout.QuoteController`, assuming the pricing backend takes 2000ms (well past its 500ms budget) while inventory responds normally in 50ms:

1. **The event loop thread handling this request calls `getQuote("widget")`.** Inside, `fetchPrice("widget")` and `fetchInventory("widget")` are both called, each immediately returning a `Mono` — neither call blocks the event loop thread even momentarily; both underlying HTTP requests are issued to the backend service asynchronously.
2. **`Mono.zip(priceMono, inventoryMono)` subscribes to both `Mono`s concurrently.** The event loop thread that made this call is now free to process other requests entirely — nothing about this in-flight request occupies any thread while waiting.
3. **The inventory response arrives after ~50ms.** Some event-loop thread (not necessarily the original one) resumes `inventoryMono`'s chain, applying its own timeout check (well within the 500ms budget) and yielding the inventory value.
4. **At the 500ms mark, `priceMono`'s `.timeout(Duration.ofMillis(500))` fires**, since the actual pricing response hasn't arrived yet (it needs 2000ms). This converts the `Mono<Double>` into an error signal, which `.onErrorReturn(-1.0)` intercepts and replaces with the fallback value `-1.0` — the chain reaches a terminal state at roughly 500ms, not 2000ms.
5. **`Mono.zip` now has terminal values from both sources** (the real inventory count from step 3, the fallback price from step 4) and proceeds to `.map(...)`, building the final string `"price=unavailable, inventory=<count>"`.
6. **Some event-loop thread writes this string as the HTTP response body**, completing the request at roughly 500ms total — bounded by the price timeout, not by the pricing backend's actual (much slower) response time, and without any thread having spent that 500ms sitting blocked waiting.

Response shape (conceptually, as an HTTP exchange):

```
GET /quote/widget HTTP/1.1
```
```
HTTP/1.1 200 OK
Content-Type: text/plain

price=unavailable, inventory=17
```

The key structural point, mirroring the earlier `CompletableFuture`-based async example but expressed reactively: no thread anywhere in this flow is ever dedicated to sitting and waiting the full 2000ms for the slow pricing call — the small, fixed event-loop pool picks up and resumes work only when there's actually something to do, whether that's a real response arriving or a timeout firing.

## 7. Gotchas & takeaways

> **Gotcha:** calling any blocking API (a traditional JDBC call, `Thread.sleep`, a blocking `RestTemplate` call) from inside a reactive chain running on an event-loop thread defeats the entire point of WebFlux — that one blocking call ties up an event-loop thread that would otherwise be serving many other concurrent requests, and because there are only a handful of event-loop threads (unlike MVC's larger thread pool), even a few such blocking calls can stall the whole server's throughput far more severely than the same mistake would in a traditional blocking stack.

- WebFlux earns its complexity on genuinely I/O-heavy, high-concurrency workloads — a small, fixed thread pool serves far more concurrent requests than a thread-per-request model, but only if every hop in the chain is actually non-blocking.
- `Mono` (zero-or-one) and `Flux` (zero-to-many) are the two core reactive types; a WebFlux controller method returns one of these instead of a plain value, and Spring subscribes to it on the caller's behalf.
- `WebClient` is the non-blocking counterpart to the traditional blocking `RestTemplate` — using `RestTemplate` inside a WebFlux application reintroduces exactly the blocking behavior WebFlux is meant to eliminate.
- Compose concurrent downstream calls with `Mono.zip` (or `Flux` equivalents) plus per-call `.timeout(...)` and `.onErrorReturn(...)`/`.onErrorResume(...)` fallbacks, mirroring the same bounded, gracefully-degrading pattern used with plain `CompletableFuture` — the reactive types don't remove the need for timeouts and fallbacks, they just let you express them declaratively.
