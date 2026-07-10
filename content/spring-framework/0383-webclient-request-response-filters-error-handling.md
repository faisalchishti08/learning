---
card: spring-framework
gi: 383
slug: webclient-request-response-filters-error-handling
title: "WebClient request/response, filters, error handling"
---

## 1. What it is

This card goes deeper into three `WebClient` capabilities beyond the basics from the previous card: fine-grained request/response inspection via `.exchangeToMono()`/`.exchangeToFlux()`, `ExchangeFilterFunction` (WebClient's own filter mechanism for cross-cutting concerns like logging, auth token injection, and retry — the client-side counterpart to `WebFilter`), and structured error handling that goes beyond the default exception-throwing behavior.

```java
WebClient client = WebClient.builder()
    .filter(logRequest())
    .filter(addAuthHeader())
    .build();

Mono<Product> result = client.get()
    .uri("/products/{id}", id)
    .exchangeToMono(response -> {
        if (response.statusCode().is2xxSuccessful()) {
            return response.bodyToMono(Product.class);
        }
        return response.createException().flatMap(Mono::error);
    });
```

## 2. Why & when

The previous card's `.retrieve()` pattern is the right default for most calls — simple, with sensible built-in error handling. Reach for the capabilities in this card when:

- You need to make a decision based on the response *status code or headers* before committing to how the body should be processed — `.retrieve()` commits to "success path deserializes to T, error path throws" before you've inspected anything; `.exchangeToMono()` lets you branch first.
- You want cross-cutting behavior applied to *every* request made through a given `WebClient` instance — request/response logging, automatically attaching an auth token, retry-on-specific-status-codes — without repeating that logic at every call site. `ExchangeFilterFunction` is exactly this mechanism, mirroring `WebFilter`'s role on the server side.
- You need custom exception types mapped from specific HTTP status codes, rather than the generic `WebClientResponseException` `.retrieve()` throws by default.

## 3. Core concept

```
.retrieve()  vs  .exchangeToMono()/.exchangeToFlux():

  retrieve()
    .bodyToMono(T.class)              — SIMPLE: 2xx -> deserialize,
                                          4xx/5xx -> WebClientResponseException
    .onStatus(predicate, handler)      — customize error handling PER STATUS
                                          (still built on top of retrieve()'s model)

  exchangeToMono(response -> { ... })
    FULL access to ClientResponse BEFORE deciding what to do:
      response.statusCode()
      response.headers()
      response.bodyToMono(T.class)     — read the body ONLY if/when you choose to

ExchangeFilterFunction — client-side filter, applied to EVERY request
through a WebClient built with .filter(...):

  ExchangeFilterFunction.ofRequestProcessor(request -> ...)   — inspect/modify REQUEST
  ExchangeFilterFunction.ofResponseProcessor(response -> ...)  — inspect/modify RESPONSE
  custom implementations of the FUNCTIONAL interface itself for full control

  Multiple filters compose in REGISTRATION order (like WebFilter/HandlerInterceptor
  chains — each filter wraps the NEXT one in the chain)
```

## 4. Diagram

<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="200" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">ExchangeFilterFunction wraps every request through one WebClient</text>

  <rect x="20" y="50" width="160" height="50" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="100" y="80" text-anchor="middle" fill="#79c0ff" font-size="10">Your .get().uri(...)</text>

  <line x1="180" y1="75" x2="230" y2="75" stroke="#8b949e" marker-end="url(#a59)"/>

  <rect x="230" y="50" width="160" height="50" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="310" y="80" text-anchor="middle" fill="#6db33f" font-size="10">Auth filter</text>

  <line x1="390" y1="75" x2="440" y2="75" stroke="#8b949e" marker-end="url(#a59)"/>

  <rect x="440" y="50" width="160" height="50" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="520" y="80" text-anchor="middle" fill="#6db33f" font-size="10">Logging filter</text>

  <line x1="600" y1="75" x2="650" y2="75" stroke="#8b949e" marker-end="url(#a59)"/>

  <rect x="650" y="55" width="60" height="40" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="680" y="80" text-anchor="middle" fill="#e6edf3" font-size="9">HTTP</text>

  <defs>
    <marker id="a59" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Filters registered on a `WebClient` apply to every request made through it, composing in registration order.*

## 5. Runnable example

### Level 1 — Basic

An `ExchangeFilterFunction` logging every request/response through a `WebClient` — applied once, active for all subsequent calls:

```java
// LoggingWebClientConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.ExchangeFilterFunction;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class LoggingWebClientConfig {

    @Bean
    public WebClient supplierWebClient() {
        return WebClient.builder()
            .baseUrl("https://api.example.com")
            .filter(logRequest())
            .filter(logResponse())
            .build();
    }

    private ExchangeFilterFunction logRequest() {
        return ExchangeFilterFunction.ofRequestProcessor(request -> {
            System.out.println("Request: " + request.method() + " " + request.url());
            return reactor.core.publisher.Mono.just(request);
        });
    }

    private ExchangeFilterFunction logResponse() {
        return ExchangeFilterFunction.ofResponseProcessor(response -> {
            System.out.println("Response status: " + response.statusCode());
            return reactor.core.publisher.Mono.just(response);
        });
    }
}
```

```java
// SupplierClient.java
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Component
public class SupplierClient {

    record Product(long id, String name) {}

    private final WebClient webClient;
    public SupplierClient(WebClient supplierWebClient) { this.webClient = supplierWebClient; }

    public Mono<Product> getProduct(long id) {
        return webClient.get().uri("/products/{id}", id).retrieve().bodyToMono(Product.class);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# server log:
# Request: GET https://api.example.com/products/1
# Response status: 200 OK
```

Every call made through `supplierWebClient` (regardless of which method or path) automatically logs its request and response — this cross-cutting behavior is written once, in the `WebClient`'s own construction, rather than repeated at every individual call site like `getProduct`.

### Level 2 — Intermediate

An authentication-token-injecting filter and custom, status-code-driven error mapping via `.onStatus(...)`:

```java
// AuthWebClientConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.web.reactive.function.client.ClientRequest;
import org.springframework.web.reactive.function.client.ExchangeFilterFunction;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Configuration
public class AuthWebClientConfig {

    @Bean
    public WebClient supplierWebClient() {
        return WebClient.builder()
            .baseUrl("https://api.example.com")
            .filter(addAuthHeader())
            .build();
    }

    private ExchangeFilterFunction addAuthHeader() {
        return ExchangeFilterFunction.ofRequestProcessor(request -> {
            ClientRequest authenticated = ClientRequest.from(request)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + fetchCurrentToken())
                .build();
            return Mono.just(authenticated);
        });
    }

    private String fetchCurrentToken() {
        return "shared-service-token";   // in production, likely cached and periodically refreshed
    }
}
```

```java
// SupplierClient.java (extended)
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Component
public class SupplierClient {

    record Product(long id, String name) {}
    static class ProductNotFoundException extends RuntimeException {
        ProductNotFoundException(long id) { super("Product " + id + " not found upstream"); }
    }
    static class SupplierUnavailableException extends RuntimeException {
        SupplierUnavailableException(String msg) { super(msg); }
    }

    private final WebClient webClient;
    public SupplierClient(WebClient supplierWebClient) { this.webClient = supplierWebClient; }

    public Mono<Product> getProduct(long id) {
        return webClient.get()
            .uri("/products/{id}", id)
            .retrieve()
            .onStatus(status -> status == HttpStatus.NOT_FOUND,
                response -> Mono.error(new ProductNotFoundException(id)))
            .onStatus(HttpStatus::is5xxServerError,
                response -> Mono.error(new SupplierUnavailableException("Supplier service error")))
            .bodyToMono(Product.class);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/1
# {"id":1,"name":"Drill"}
# (Authorization: Bearer shared-service-token was automatically added by the filter)

curl -i http://localhost:8080/products/999   # supplier returns 404 for this id
# maps to a ProductNotFoundException, which a @ControllerAdvice can then format as a 404 for OUR client
```

**What changed:** `addAuthHeader()` demonstrates request mutation via `ClientRequest.from(request).header(...).build()` — filters don't modify the request in place; they construct and return a new, modified `ClientRequest`. `.onStatus(predicate, handler)` maps specific status codes to specific, meaningful domain exceptions instead of the generic `WebClientResponseException` `.retrieve()` would otherwise throw for any 4xx/5xx — these domain exceptions then flow naturally into `@ExceptionHandler`/`@ControllerAdvice` processing (per the reactive exception handling card) in the calling application.

### Level 3 — Advanced

Production concern: a retry filter for specific transient failure conditions (combining `ExchangeFilterFunction` with Reactor's `retryWhen`), and `.exchangeToMono()` for full response inspection when the decision of how to process the body genuinely depends on response headers, not just the status code:

```java
// RetryWebClientConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.ExchangeFilterFunction;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.util.retry.Retry;

import java.time.Duration;

@Configuration
public class RetryWebClientConfig {

    @Bean
    public WebClient supplierWebClient() {
        return WebClient.builder()
            .baseUrl("https://api.example.com")
            .filter(retryOn503())
            .build();
    }

    private ExchangeFilterFunction retryOn503() {
        return (request, next) -> next.exchange(request)
            .flatMap(response -> {
                if (response.statusCode().value() == 503) {
                    // Discard this response's resources properly before retrying,
                    // then signal an error so retryWhen (applied by the CALLER, below)
                    // can trigger a genuine re-attempt.
                    return response.releaseBody()
                        .then(Mono.error(new RuntimeException("503 Service Unavailable")));
                }
                return Mono.just(response);
            });
    }
}
```

```java
// SupplierClient.java (production version)
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import reactor.util.retry.Retry;

import java.time.Duration;

@Component
public class SupplierClient {

    record Product(long id, String name) {}

    private final WebClient webClient;
    public SupplierClient(WebClient supplierWebClient) { this.webClient = supplierWebClient; }

    public Mono<Product> getProduct(long id) {
        return webClient.get()
            .uri("/products/{id}", id)
            .retrieve()
            .bodyToMono(Product.class)
            .retryWhen(Retry.backoff(3, Duration.ofMillis(200))
                .filter(ex -> ex.getMessage() != null && ex.getMessage().contains("503")));
    }

    // Full response inspection: the SHAPE of the response body genuinely
    // differs based on a response header, requiring exchangeToMono instead
    // of retrieve()'s "always deserialize the same way" model.
    public Mono<Product> getProductVersionAware(long id) {
        return webClient.get()
            .uri("/products/{id}", id)
            .exchangeToMono(response -> {
                String apiVersion = response.headers().header("X-Api-Version")
                    .stream().findFirst().orElse("v1");
                if ("v2".equals(apiVersion)) {
                    return response.bodyToMono(Product.class);   // v2 shape matches Product directly
                }
                // v1 shape is different — adapt it
                return response.bodyToMono(LegacyProductV1.class)
                    .map(legacy -> new Product(legacy.id(), legacy.title()));
            });
    }

    record LegacyProductV1(long id, String title) {}
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/1
# {"id":1,"name":"Drill"}     <- succeeds, possibly after internal retries if the
#                                 supplier transiently returned 503 during the attempt(s)

curl http://localhost:8080/products/1/version-aware
# {"id":1,"name":"Drill"}     <- correctly adapted regardless of which API version the supplier responded with
```

**What changed and why:**
- The `retryOn503()` `ExchangeFilterFunction` and the caller's `.retryWhen(...)` work together: the filter detects a `503` and converts it into an error signal (after properly releasing the original response's resources via `.releaseBody()`, avoiding a resource leak), and the caller's `retryWhen` — which wraps the *entire* `retrieve().bodyToMono(...)` call, not just the filter — actually performs the re-attempt, re-executing the whole request from scratch. This separation (filter detects/signals, caller decides retry policy) keeps the retry *policy* (how many attempts, what backoff) configurable per call site while the *detection* logic (what counts as retriable) lives centrally in the filter.
- `.exchangeToMono(response -> {...})` in `getProductVersionAware` demonstrates genuine full-response-first decision-making — the code inspects `X-Api-Version` (a response header) *before* deciding which type to deserialize the body into, something `.retrieve().bodyToMono(SomeFixedType.class)` cannot express, since that pattern commits to one deserialization target upfront.
- This pattern (adapting between API versions based on a response header) is a realistic scenario when integrating with an external service that's mid-migration between two response shapes, or when calling a service that supports content negotiation via a custom header rather than (or in addition to) standard HTTP content negotiation.

## 6. Walkthrough

**Request: `GET /products/1` (Level 3 code, supplier transiently returns 503 once, then succeeds).**

1. `SupplierClient.getProduct(1)` builds the request chain: `.get().uri(...).retrieve().bodyToMono(Product.class).retryWhen(...)`. This entire composed `Mono<Product>` is lazy — nothing executes until subscribed.
2. Subscription triggers the actual HTTP call. Before reaching the network, the request passes through the registered `ExchangeFilterFunction` chain on `supplierWebClient` — here, just `retryOn503()`. This filter's job is only to *inspect the response after it comes back*, so it calls `next.exchange(request)` to actually perform the underlying HTTP request unmodified, then attaches its own `.flatMap(response -> {...})` handling to the result.
3. Assume the first attempt genuinely receives a `503 Service Unavailable` response from `api.example.com`. Back in `retryOn503()`'s `flatMap`: `response.statusCode().value() == 503` is `true`. It calls `response.releaseBody()` (properly discarding the unread response body's resources, since this filter isn't consuming it as a successful result) `.then(Mono.error(new RuntimeException("503 Service Unavailable")))` — converting this response into an error signal instead of letting it flow through as a normal (if unsuccessful) HTTP exchange.
4. This error signal propagates up through `.retrieve()`, causing `.bodyToMono(Product.class)` to also signal an error rather than attempting to deserialize a body (there is none to deserialize meaningfully, given the 503).
5. `.retryWhen(Retry.backoff(3, Duration.ofMillis(200)).filter(ex -> ex.getMessage() != null && ex.getMessage().contains("503")))` receives this error. Its filter checks the exception's message for `"503"` — matches, so a retry is permitted. It waits ~200ms (the configured initial backoff), then **re-subscribes** to the entire upstream chain — re-executing steps 2 through 4 from scratch, including passing through the `retryOn503` filter again for this fresh attempt.
6. This second attempt succeeds: the supplier returns `200 OK` with `{"id":1,"name":"Drill"}`. Inside `retryOn503()`: `response.statusCode().value() == 503` is now `false`, so it returns `Mono.just(response)` unchanged — the successful response flows through.
7. Back in `.retrieve().bodyToMono(Product.class)`: since this is now a successful, non-503 response, the body is deserialized normally into `Product(1, "Drill")`.
8. This value satisfies the `retryWhen`-wrapped `Mono<Product>` — no further retries needed, since a value was successfully produced.
9. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   {"id":1,"name":"Drill"}
   ```

The entire retry cycle (one failed attempt, a ~200ms backoff, one successful attempt) happens transparently within the `WebClient` call chain, invisible to whatever code ultimately called `getProduct(1)`.

## 7. Gotchas & takeaways

> **`ExchangeFilterFunction`s applied via `.filter(...)` on a `WebClient.Builder` apply to every request made through the resulting `WebClient` instance** — this is powerful for cross-cutting concerns but means a filter with a subtle bug (like the retry-detection example, if it mismatched too broadly) affects every call site using that client, not just one. Test filter logic thoroughly, since its blast radius is the entire client instance.

> **Forgetting to call `response.releaseBody()`/`response.bodyToMono(Void.class)` when deliberately discarding a response inside `.exchangeToMono()`/`.exchangeToFlux()` or a custom filter can leak underlying connection resources** — unlike `.retrieve()`, which handles this automatically, the lower-level `exchangeToMono`/filter APIs put this responsibility on your code whenever you decide not to consume a response body.

> **`.retryWhen(...)` at the call site re-executes the ENTIRE request from scratch on each retry**, including re-running any request-side `ExchangeFilterFunction`s (like an auth-token-refreshing filter) — this is usually desirable (a fresh token, a fresh connection) but worth knowing explicitly, since it means retry attempts are not "free" replays of a cached attempt; each one is a genuine, full new HTTP request.

- `ExchangeFilterFunction` is `WebClient`'s cross-cutting mechanism, applied to every request through a given client instance — the direct client-side counterpart to server-side `WebFilter`.
- `.retrieve()` with `.onStatus(...)` handles most error-mapping needs; `.exchangeToMono()`/`.exchangeToFlux()` provide full response inspection when the processing decision genuinely depends on status or headers before committing to a body type.
- Combine a detection filter (identifying retriable conditions) with call-site `.retryWhen(...)` (deciding retry policy) for clean, composable resilience against transient failures.
- Always properly release an unconsumed response body (`releaseBody()`) when using the lower-level `exchangeToMono`/filter APIs, to avoid leaking connection resources.
