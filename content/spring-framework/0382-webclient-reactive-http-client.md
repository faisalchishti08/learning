---
card: spring-framework
gi: 382
slug: webclient-reactive-http-client
title: "WebClient (reactive HTTP client)"
---

## 1. What it is

`WebClient` is Spring's non-blocking, reactive HTTP client — the modern replacement for the older, blocking `RestTemplate`, returning `Mono<T>`/`Flux<T>` from every request rather than blocking the calling thread until a response arrives. It's part of the WebFlux module but is usable in *any* Spring application, including a traditional Spring MVC one, whenever making outbound HTTP calls without blocking a thread is valuable.

```java
WebClient client = WebClient.create("https://api.example.com");

Mono<Product> product = client.get()
    .uri("/products/{id}", 1)
    .retrieve()
    .bodyToMono(Product.class);
```

## 2. Why & when

`RestTemplate` has been in maintenance mode (no new features) since Spring 5, with `WebClient` as its official recommended replacement for new code, even in synchronous applications — `WebClient` calls can always be made blocking at the call site (`.block()`) when needed, but not vice versa. Use `WebClient` when:

- Calling external services (other microservices, third-party APIs) from within a WebFlux application, where you want to preserve non-blocking behavior end-to-end (calling `RestTemplate` from a WebFlux handler would block a precious event-loop thread, exactly the anti-pattern covered in the imperative-vs-reactive trade-offs card).
- Making several independent outbound HTTP calls that can run concurrently — `WebClient`'s `Mono`/`Flux`-based results compose naturally with `Mono.zip`/`Flux.merge` for concurrent execution, mirroring the Project Reactor card's patterns.
- Building new code in any Spring application, since it's the actively maintained, modern option regardless of whether the surrounding application itself is reactive.

## 3. Core concept

```
WebClient.create() or WebClient.builder()...build()  -- create ONCE, reuse (thread-safe)

Request building (fluent, method-per-HTTP-verb):

  client.get()  / .post() / .put() / .delete() / ...
      .uri("/products/{id}", id)          — path + variables
      .header("X-Custom", "value")         — request headers
      .bodyValue(requestBody)               — request body (for POST/PUT)
      .retrieve()                            — commit to processing the response
      .bodyToMono(Product.class)              — deserialize response body to ONE object
      .bodyToFlux(Product.class)               — deserialize response body to MANY objects

.retrieve() vs .exchangeToMono()/.exchangeToFlux():

  retrieve()          — simpler, throws WebClientResponseException for 4xx/5xx by default
  exchangeToMono(...)   — MORE control: inspect status/headers BEFORE deciding how
                            to handle the body, useful for custom error mapping

Response handling — everything is STILL a Mono/Flux:

  Mono<Product> result = ....bodyToMono(Product.class);
  result.subscribe(...)     — non-blocking (correct, in reactive code)
  result.block()             — BLOCKING (only for tests / non-reactive callers)
```

## 4. Diagram

<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="200" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">WebClient fluent request-building chain</text>

  <rect x="20" y="50" width="140" height="50" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="80" text-anchor="middle" fill="#79c0ff" font-size="10">.get().uri(...)</text>

  <line x1="160" y1="75" x2="210" y2="75" stroke="#8b949e" marker-end="url(#a58)"/>

  <rect x="210" y="50" width="140" height="50" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="280" y="80" text-anchor="middle" fill="#6db33f" font-size="10">.retrieve()</text>

  <line x1="350" y1="75" x2="400" y2="75" stroke="#8b949e" marker-end="url(#a58)"/>

  <rect x="400" y="50" width="180" height="50" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="490" y="80" text-anchor="middle" fill="#e6edf3" font-size="10">.bodyToMono(T.class)</text>

  <line x1="580" y1="75" x2="630" y2="75" stroke="#8b949e" marker-end="url(#a58)"/>

  <rect x="630" y="55" width="70" height="40" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="665" y="80" text-anchor="middle" fill="#e6edf3" font-size="9">Mono&lt;T&gt;</text>

  <defs>
    <marker id="a58" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Each stage of the fluent chain returns an intermediate builder; the terminal `bodyToMono`/`bodyToFlux` call produces the actual reactive result.*

## 5. Runnable example

### Level 1 — Basic

A minimal GET request, deserializing the response into an object:

```java
// SupplierClient.java
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Component
public class SupplierClient {

    record Product(long id, String name, double price) {}

    private final WebClient webClient = WebClient.create("https://api.example.com");

    public Mono<Product> getProduct(long id) {
        return webClient.get()
            .uri("/products/{id}", id)
            .retrieve()
            .bodyToMono(Product.class);
    }
}
```

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {

    private final SupplierClient supplierClient;
    public ProductController(SupplierClient supplierClient) { this.supplierClient = supplierClient; }

    @GetMapping("/products/{id}")
    public Mono<SupplierClient.Product> get(@PathVariable long id) {
        return supplierClient.getProduct(id);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# {"id":1,"name":"Drill","price":29.99}    (proxied from the external API, non-blocking throughout)
```

`getProduct` returns a `Mono<Product>` immediately, without blocking — the actual HTTP call to `api.example.com` happens asynchronously, and the calling thread is free to handle other work while waiting for the response, exactly as the reactive programming overview card described for any `Mono`-returning operation.

### Level 2 — Intermediate

Configuring a reusable, pre-configured `WebClient` bean with a base URL, default headers, and a timeout — the standard production pattern rather than ad hoc `WebClient.create()` calls scattered through the codebase:

```java
// WebClientConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class WebClientConfig {

    @Bean
    public WebClient supplierWebClient() {
        return WebClient.builder()
            .baseUrl("https://api.example.com")
            .defaultHeader(HttpHeaders.ACCEPT, "application/json")
            .defaultHeader("X-Api-Key", "shared-api-key")
            .build();
    }
}
```

```java
// SupplierClient.java (extended)
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;

@Component
public class SupplierClient {

    record Product(long id, String name, double price) {}

    private final WebClient webClient;
    public SupplierClient(WebClient supplierWebClient) { this.webClient = supplierWebClient; }

    public Mono<Product> getProduct(long id) {
        return webClient.get()
            .uri("/products/{id}", id)
            .retrieve()
            .bodyToMono(Product.class)
            .timeout(Duration.ofSeconds(3));   // fail if the external service doesn't respond in time
    }

    public Mono<Product> createProduct(String name, double price) {
        return webClient.post()
            .uri("/products")
            .bodyValue(new Product(0, name, price))
            .retrieve()
            .bodyToMono(Product.class);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/1
# {"id":1,"name":"Drill","price":29.99}

# If the external service is slow/unresponsive beyond 3 seconds, the Mono errors
# with a TimeoutException instead of hanging indefinitely.
```

**What changed:** Building `WebClient` once, as a Spring `@Bean` with `baseUrl` and default headers, means every call site (`getProduct`, `createProduct`) only needs to specify the path and method-specific details — `WebClient` instances are explicitly designed to be thread-safe and reusable, so constructing a new one per request (as Level 1's inline `WebClient.create(...)` implicitly risks if called repeatedly) wastes resources and loses the benefit of shared connection pooling. `.timeout(Duration.ofSeconds(3))` guards against an unresponsive external dependency hanging the calling request indefinitely.

### Level 3 — Advanced

Production concern: concurrent, independent calls composed via `Mono.zip` (mirroring the Project Reactor card's pattern, now applied to real outbound HTTP calls), connection pool tuning, and graceful degradation when a non-critical dependency fails:

```java
// WebClientConfig.java (production version)
import io.netty.channel.ChannelOption;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.netty.http.client.HttpClient;
import reactor.netty.resources.ConnectionProvider;

import java.time.Duration;

@Configuration
public class WebClientConfig {

    @Bean
    public WebClient supplierWebClient() {
        ConnectionProvider connectionProvider = ConnectionProvider.builder("supplier-pool")
            .maxConnections(50)
            .pendingAcquireTimeout(Duration.ofSeconds(5))
            .build();

        HttpClient httpClient = HttpClient.create(connectionProvider)
            .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 2000)
            .responseTimeout(Duration.ofSeconds(3));

        return WebClient.builder()
            .baseUrl("https://api.example.com")
            .clientConnector(new ReactorClientHttpConnector(httpClient))
            .build();
    }
}
```

```java
// ProductAggregationService.java
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;

@Service
public class ProductAggregationService {

    record Product(long id, String name, double price) {}
    record Reviews(long productId, double averageRating) {}
    record ProductDetail(String name, double price, double rating) {}

    private final WebClient webClient;
    public ProductAggregationService(WebClient supplierWebClient) { this.webClient = supplierWebClient; }

    public Mono<ProductDetail> getDetail(long id) {
        Mono<Product> productMono = webClient.get()
            .uri("/products/{id}", id)
            .retrieve()
            .bodyToMono(Product.class)
            .timeout(Duration.ofSeconds(2));

        Mono<Reviews> reviewsMono = webClient.get()
            .uri("/products/{id}/reviews", id)
            .retrieve()
            .bodyToMono(Reviews.class)
            .timeout(Duration.ofSeconds(2))
            // Reviews are NON-CRITICAL — if the reviews service is down or slow,
            // degrade gracefully with a default rather than failing the WHOLE request.
            .onErrorResume(ex -> Mono.just(new Reviews(id, 0.0)));

        // Both calls run CONCURRENTLY, not sequentially — total time bounded
        // by the SLOWER of the two, not their sum.
        return Mono.zip(productMono, reviewsMono)
            .map(tuple -> new ProductDetail(tuple.getT1().name(), tuple.getT1().price(), tuple.getT2().averageRating()));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/1/detail
# {"name":"Drill","price":29.99,"rating":4.5}

# Even if the reviews service is completely down:
# {"name":"Drill","price":29.99,"rating":0.0}    <- graceful degradation, not a total failure
```

**What changed and why:**
- `ConnectionProvider.builder("supplier-pool").maxConnections(50)` explicitly bounds the connection pool used for calls to this specific external service — without this, `WebClient`'s default connection pool settings apply, which may not be tuned appropriately for a specific dependency's actual capacity or the calling application's concurrency needs. Naming the pool (`"supplier-pool"`) also aids observability, since Reactor Netty can expose pool-specific metrics under this name.
- `productMono` (critical — the request fails without it) has a plain `.timeout(...)` with no recovery, so a timeout genuinely fails the overall `getDetail` call; `reviewsMono` (non-critical — a nice-to-have enhancement) pairs its timeout with `.onErrorResume(...)`, providing a sensible default so a slow or failing reviews service degrades the response quality slightly rather than failing the entire product detail lookup — this mirrors the resilience patterns from the Project Reactor and reactive exception handling cards, now applied specifically to real outbound `WebClient` calls.
- `Mono.zip(productMono, reviewsMono)` runs both outbound HTTP calls concurrently — a genuine, measurable latency improvement over calling them sequentially, directly analogous to the concurrent-Mono pattern demonstrated with simulated calls in the Project Reactor card, now applied to actual network requests.

## 6. Walkthrough

**Request: `GET /products/1/detail` (Level 3 code, reviews service responding normally).**

1. `DispatcherHandler` dispatches to `ProductAggregationService.getDetail(1)` (assume wrapped by a thin controller not shown here for brevity). The method constructs `productMono` and `reviewsMono` — both are `WebClient` request chains, lazily describing outbound HTTP calls that haven't executed yet.
2. `Mono.zip(productMono, reviewsMono)` is constructed, describing "run both concurrently, combine results" — still nothing has executed; this is Reactor's laziness principle applying to real network calls exactly as it does to any other `Mono`/`Flux` composition.
3. The method returns this composed `Mono<ProductDetail>`. WebFlux's response-writing machinery subscribes to it to actually produce the response, which triggers subscription to both `productMono` and `reviewsMono` simultaneously.
4. `productMono`'s subscription triggers an actual outbound HTTP `GET https://api.example.com/products/1` call via the configured `WebClient` (using the tuned `ReactorClientHttpConnector`/`ConnectionProvider` from `WebClientConfig`) — this call is genuinely non-blocking; no thread sits idle waiting for the response.
5. Simultaneously, `reviewsMono`'s subscription triggers `GET https://api.example.com/products/1/reviews`.
6. Both external HTTP calls are in flight concurrently. Assume the products call responds first (say, after 150ms) with `{"id":1,"name":"Drill","price":29.99}`, deserialized into `Product(1, "Drill", 29.99)`. `Mono.zip` holds this result, waiting for the second input.
7. Shortly after (say, 180ms total), the reviews call responds with `{"productId":1,"averageRating":4.5}`, deserialized into `Reviews(1, 4.5)`. Because this succeeded within its 2-second timeout, `.onErrorResume(...)` never fires — the genuine value passes through unchanged.
8. Both inputs to `Mono.zip` have now resolved. It combines them into a `Tuple2<Product, Reviews>` and emits it to the subsequent `.map(...)`, which constructs `ProductDetail("Drill", 29.99, 4.5)`.
9. This final value resolves the overall `Mono<ProductDetail>`, which WebFlux serializes as the response body.
10. Response:
    ```
    HTTP/1.1 200 OK
    Content-Type: application/json

    {"name":"Drill","price":29.99,"rating":4.5}
    ```

**Same request, but the reviews service is down (connection refused or times out).**

1–5. Identical concurrent kickoff.
6. `productMono` succeeds normally as before, `Product(1, "Drill", 29.99)`.
7. `reviewsMono`'s underlying HTTP call fails (connection error, or exceeds its 2-second timeout) — this produces an error signal instead of a `Reviews` value.
8. `.onErrorResume(ex -> Mono.just(new Reviews(1, 0.0)))` intercepts this error signal, substituting a fallback `Reviews(1, 0.0)` — from `Mono.zip`'s perspective, this input "succeeded" with the fallback value; it has no visibility into the fact that a real failure occurred and was recovered from.
9. `Mono.zip` proceeds exactly as in the successful case, combining `Product(1, "Drill", 29.99)` with the fallback `Reviews(1, 0.0)`, producing `ProductDetail("Drill", 29.99, 0.0)`.
10. Response, still a `200 OK` despite the reviews service outage:
    ```
    HTTP/1.1 200 OK
    Content-Type: application/json

    {"name":"Drill","price":29.99,"rating":0.0}
    ```

## 7. Gotchas & takeaways

> **Constructing a new `WebClient` instance per request (rather than building one reusable instance, as a `@Bean`, and reusing it) discards connection pooling benefits and adds unnecessary overhead** — `WebClient` instances are explicitly designed to be thread-safe and long-lived; always construct them once, typically at application startup via a `@Bean` method or a shared field.

> **Calling `.block()` on a `WebClient` call's `Mono` inside a WebFlux request handler reintroduces exactly the blocking-on-a-reactive-thread anti-pattern covered in the imperative-vs-reactive trade-offs card** — the entire point of using `WebClient` instead of `RestTemplate` is preserving non-blocking behavior; blocking on its result defeats that purpose just as thoroughly as any other blocking call inside reactive code.

> **`.retrieve()`'s default error handling throws `WebClientResponseException` for any 4xx/5xx response**, which propagates as a `Mono` error signal — if you need to inspect the response status or body *before* deciding how to handle an error response (rather than always treating 4xx/5xx as exceptions), use `.exchangeToMono(...)`/`.exchangeToFlux(...)` instead, covered in more depth in the next card.

- `WebClient` is Spring's modern, non-blocking HTTP client, the recommended replacement for the deprecated-in-spirit `RestTemplate`, usable in any Spring application regardless of whether it's reactive.
- Build `WebClient` instances once (typically as a `@Bean`) and reuse them — they're thread-safe and designed for long-lived, shared use with connection pooling.
- Independent outbound calls composed via `Mono.zip` run concurrently, providing a genuine latency benefit over sequential blocking calls.
- Pair timeouts with `onErrorResume` fallbacks for non-critical dependencies to enable graceful degradation, reserving unrecovered failures for genuinely critical calls.
