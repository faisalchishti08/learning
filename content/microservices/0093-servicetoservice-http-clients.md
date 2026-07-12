---
card: microservices
gi: 93
slug: service-to-service-http-clients
title: "Service-to-service HTTP clients"
---

## 1. What it is

An HTTP client library is the tool a service uses to actually make outbound calls to another service — in the Java/Spring ecosystem, this means choosing between `RestTemplate` (older, synchronous, now in maintenance mode), `RestClient` (modern, synchronous, Spring's current recommended default), and `WebClient` (reactive, non-blocking, part of Spring WebFlux). Each wraps the mechanics of building a request, sending it, and parsing the response, so application code doesn't have to construct raw HTTP calls by hand.

## 2. Why & when

Constructing HTTP requests manually — building headers, serializing the body, opening a connection, handling the response stream — is repetitive, error-prone boilerplate that a good client library eliminates entirely, letting application code focus on what request to make and what to do with the response. The choice between the three options matters because they carry different underlying execution models: `RestTemplate` and `RestClient` are blocking (see [blocking vs non-blocking I/O](0087-blocking-vs-non-blocking-i-o.md)) — the calling thread waits for the response — while `WebClient` is non-blocking, returning a reactive `Mono`/`Flux` that completes later without occupying a thread while waiting.

Use `RestClient` for most new synchronous Spring services — it's the current recommended default, replacing `RestTemplate` with a cleaner, more fluent API while keeping the same blocking execution model most applications are built around. Use `WebClient` specifically when a service is built reactively (Spring WebFlux) or needs to make many concurrent outbound calls without dedicating a thread to each one. Avoid starting new code with `RestTemplate` — it remains supported for existing code, but Spring's own documentation recommends `RestClient` for new development.

## 3. Core concept

Each client offers the same fundamental operation — build a request, send it, get a typed response — through progressively different styles: an older, more verbose builder API, a modern fluent API, and a reactive, non-blocking API.

```java
// RestClient (modern, blocking, recommended default)
Order order = restClient.get()
    .uri("/orders/{id}", 42)
    .retrieve()
    .body(Order.class);   // BLOCKS here until the response arrives

// WebClient (reactive, non-blocking)
Mono<Order> orderMono = webClient.get()
    .uri("/orders/{id}", 42)
    .retrieve()
    .bodyToMono(Order.class);   // returns IMMEDIATELY; subscribe() triggers the actual call
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RestClient blocks the calling thread until the HTTP response arrives, while WebClient returns a Mono immediately and delivers the result later via subscription">
  <rect x="20" y="20" width="280" height="130" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">RestClient (blocking)</text>
  <text x="160" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">.body(Order.class)</text>
  <text x="160" y="85" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">thread WAITS for the response</text>

  <rect x="340" y="20" width="280" height="130" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">WebClient (non-blocking)</text>
  <text x="480" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">.bodyToMono(Order.class)</text>
  <text x="480" y="85" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">returns IMMEDIATELY, result via callback</text>
</svg>

Both APIs express the same logical HTTP call; their execution models differ fundamentally.

## 5. Runnable example

Scenario: an order lookup call made against a downstream service, first with a raw manual HTTP-call simulation to make the boilerplate concrete, then wrapped in a `RestClient`-style fluent blocking builder, then extended to a `WebClient`-style non-blocking equivalent, comparing what each returns immediately versus later.

### Level 1 — Basic

```java
// File: ManualHttpCall.java -- construct and "send" an HTTP call by
// hand -- the boilerplate a client library exists to eliminate.
import java.util.*;

public class ManualHttpCall {
    static Map<Integer, String> orders = new HashMap<>(Map.of(42, "PLACED"));

    static String rawHttpGet(String path) throws InterruptedException {
        Thread.sleep(50); // simulated network latency
        int id = Integer.parseInt(path.substring(path.lastIndexOf('/') + 1));
        return "{\"id\":" + id + ",\"status\":\"" + orders.get(id) + "\"}";
    }

    public static void main(String[] args) throws InterruptedException {
        String rawResponse = rawHttpGet("/orders/42"); // caller builds the path, parses the raw response itself
        System.out.println("Manual response: " + rawResponse);
    }
}
```

**How to run:** `javac ManualHttpCall.java && java ManualHttpCall` (JDK 17+).

Expected output:
```
Manual response: {"id":42,"status":"PLACED"}
```

### Level 2 — Intermediate

```java
// File: RestClientStyle.java -- a fluent, TYPED builder API -- models
// Spring's RestClient: blocking, returns a fully-parsed object directly.
import java.util.*;

public class RestClientStyle {
    record Order(int id, String status) {}
    static Map<Integer, String> orders = new HashMap<>(Map.of(42, "PLACED"));

    static class SimulatedRestClient {
        RequestBuilder get() { return new RequestBuilder(); }
        class RequestBuilder {
            String uri;
            RequestBuilder uri(String template, Object... args) { uri = String.format(template.replace("{id}", "%s"), args); return this; }
            Order retrieveBodyAsOrder() throws InterruptedException { // .retrieve().body(Order.class) collapsed for brevity
                Thread.sleep(50); // BLOCKS the calling thread for the network round trip
                int id = Integer.parseInt(uri.substring(uri.lastIndexOf('/') + 1));
                return new Order(id, orders.get(id));
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        SimulatedRestClient restClient = new SimulatedRestClient();
        Order order = restClient.get().uri("/orders/{id}", 42).retrieveBodyAsOrder(); // fluent, typed, BLOCKING
        System.out.println("RestClient result: " + order);
        System.out.println("(main thread was BLOCKED until this line could execute)");
    }
}
```

**How to run:** `javac RestClientStyle.java && java RestClientStyle` (JDK 17+).

Expected output:
```
RestClient result: Order[id=42, status=PLACED]
(main thread was BLOCKED until this line could execute)
```

### Level 3 — Advanced

```java
// File: WebClientStyle.java -- a NON-BLOCKING equivalent -- models
// Spring's WebClient: the call returns an immediately-available
// "Mono"-like handle, and the actual result is delivered LATER, via a
// callback, without occupying the calling thread while waiting.
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;

public class WebClientStyle {
    record Order(int id, String status) {}
    static Map<Integer, String> orders = new HashMap<>(Map.of(42, "PLACED"));
    static ExecutorService ioPool = Executors.newFixedThreadPool(1);

    static class SimpleMono<T> { // a minimal stand-in for Spring's reactive Mono<T>
        private CompletableFuture<T> future;
        SimpleMono(CompletableFuture<T> future) { this.future = future; }
        void subscribe(Consumer<T> onResult) { future.thenAccept(onResult); } // registers a CALLBACK, doesn't block
    }

    static class SimulatedWebClient {
        RequestBuilder get() { return new RequestBuilder(); }
        class RequestBuilder {
            String uri;
            RequestBuilder uri(String template, Object... args) { uri = String.format(template.replace("{id}", "%s"), args); return this; }
            SimpleMono<Order> bodyToMonoOrder() { // returns IMMEDIATELY -- no blocking here at all
                CompletableFuture<Order> future = CompletableFuture.supplyAsync(() -> {
                    try { Thread.sleep(50); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                    int id = Integer.parseInt(uri.substring(uri.lastIndexOf('/') + 1));
                    return new Order(id, orders.get(id));
                }, ioPool);
                return new SimpleMono<>(future);
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        SimulatedWebClient webClient = new SimulatedWebClient();
        SimpleMono<Order> orderMono = webClient.get().uri("/orders/{id}", 42).bodyToMonoOrder();
        System.out.println("Mono obtained -- main thread was NEVER blocked waiting for the network call");

        orderMono.subscribe(order -> System.out.println("WebClient result (via callback): " + order));

        Thread.sleep(100); // give the async callback time to fire before the program exits
        ioPool.shutdown();
    }
}
```

**How to run:** `javac WebClientStyle.java && java WebClientStyle` (JDK 17+).

Expected output:
```
Mono obtained -- main thread was NEVER blocked waiting for the network call
WebClient result (via callback): Order[id=42, status=PLACED]
```

## 6. Walkthrough

1. **Level 1** — `rawHttpGet` simulates the full manual process: sleep for simulated latency, then manually parse the numeric id out of the path string and build a raw JSON response. `main` calls it and prints the unparsed string directly — every piece of this (path construction, response parsing) would need to be repeated by hand for every single outbound call in a real service without a client library.
2. **Level 2 — a fluent, blocking, typed client** — `SimulatedRestClient.get().uri(...).retrieveBodyAsOrder()` models `RestClient`'s real fluent builder chain. Calling `retrieveBodyAsOrder()` sleeps (simulating the network round trip) *before* returning — the calling thread genuinely waits. `main` calls this chain and only reaches the print statement once the call has fully completed and returned a typed `Order` object — no manual JSON parsing needed, but still a blocking call, exactly like Spring's real `RestClient`.
3. **Level 3 — the non-blocking equivalent** — `SimulatedWebClient.get().uri(...).bodyToMonoOrder()` returns a `SimpleMono<Order>` *immediately*, without any `Thread.sleep` happening on `main`'s own thread — the actual work is submitted to `ioPool` via `CompletableFuture.supplyAsync`, which begins executing on a separate thread while `main` continues.
4. **Tracing the non-blocking flow** — `main` calls `webClient.get().uri(...).bodyToMonoOrder()`, immediately gets back `orderMono`, and prints the "Mono obtained" line — this happens essentially instantly, well before the simulated 50ms network delay has elapsed, proving `main`'s thread was never blocked waiting. `main` then calls `orderMono.subscribe(...)`, registering a callback (not blocking) that will run once the underlying future completes. `main` then sleeps 100ms purely to keep the JVM alive long enough for that callback to actually fire — in a real Spring WebFlux application, this artificial wait wouldn't be needed, since the containing reactive pipeline itself would naturally keep the process alive until the chain completes.
5. **What each response ends up printing, and why it matters** — Level 2's output shows the "RestClient result" line appearing *after* the (simulated) blocking wait — the print statement literally cannot execute until the call returns, which is guaranteed by the blocking model. Level 3's output shows "Mono obtained" printing essentially immediately, followed later by "WebClient result (via callback)" once the async work completes and the subscription's callback fires — demonstrating that `main`'s own execution was decoupled from the network call's completion timing entirely, matching the [blocking vs non-blocking I/O](0087-blocking-vs-non-blocking-i-o.md) distinction applied concretely to a real HTTP client choice.

## 7. Gotchas & takeaways

> **Gotcha:** calling `.block()` on a `WebClient`'s `Mono` (forcing it to behave synchronously, waiting for the result right there) is a common but usually mistaken pattern — it throws away all of `WebClient`'s non-blocking benefit while keeping its added complexity. If a call site genuinely needs blocking, synchronous behavior, use `RestClient` instead of `WebClient` with `.block()` bolted on.

- `RestClient` (modern, blocking) is Spring's current recommended default for synchronous service-to-service calls — prefer it over the older `RestTemplate` for new code.
- `WebClient` (reactive, non-blocking) fits services built on Spring WebFlux, or any case needing many concurrent outbound calls without dedicating a thread to each one's wait.
- A blocking client's call returns the fully-resolved result directly; a non-blocking client's call returns immediately with a handle (`Mono`/`Flux`), and the actual result arrives later via a subscription/callback.
- Mixing execution models inconsistently within one service (blocking calls buried inside an otherwise-reactive pipeline, or vice versa) tends to erase whichever model's benefits you were trying to get — pick one execution model per service and stay consistent.
- See [connection pooling & keep-alive](0095-connection-pooling-keep-alive.md) and [client-side timeouts](0096-client-side-timeouts-connect-read.md) for the configuration concerns that apply to any of these client choices in production.
