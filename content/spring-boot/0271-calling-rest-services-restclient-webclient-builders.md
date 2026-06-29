---
card: spring-boot
gi: 271
slug: calling-rest-services-restclient-webclient-builders
title: Calling REST services (RestClient/WebClient builders)
---

## 1. What it is

Spring Boot auto-configures **builder beans** for making outbound HTTP calls, so you get pre-configured clients without boilerplate:

- **`RestClient.Builder`** (Spring 6.1+ / Spring Boot 3.2+) — the modern synchronous HTTP client. Successor to `RestTemplate`. Fluent API, supports message converters, interceptors, and error handlers.
- **`WebClient.Builder`** (Spring WebFlux) — the reactive, non-blocking HTTP client. Auto-configured when `spring-boot-starter-webflux` is on the classpath.
- **`RestTemplate` (legacy)** — still supported but not auto-configured as a bean; Spring Boot provides a `RestTemplateBuilder` for manual construction.

The auto-configured builders are pre-wired with:
- Jackson `HttpMessageConverter` (JSON support).
- Micrometer metrics (observation for tracing HTTP calls).
- SSL/TLS configuration from Spring Boot's SSL bundle support.
- `spring.http.client.*` properties (timeouts, connection pool).

## 2. Why & when

Use `RestClient.Builder` for:
- Synchronous REST calls from a traditional Spring MVC app.
- Simple request-response patterns (CRUD against an external API).
- Migrating away from `RestTemplate`.

Use `WebClient.Builder` for:
- Non-blocking calls in a reactive stack (WebFlux).
- Streaming responses (Server-Sent Events, large payloads).
- High-throughput scenarios where thread-per-request doesn't scale.

Both builders are prototype-scoped — each injection site gets its own builder instance that you can customise without affecting other uses of the same builder. Call `builder.build()` to get the final client, typically in a `@Bean` method.

## 3. Core concept

The builder pattern separates *configuration* (done once, at startup) from *client creation* (done per use case):

```
RestClient.Builder (auto-configured)
    ↓ inject, then customise
  .baseUrl("https://api.example.com")
  .defaultHeader("X-API-Key", apiKey)
  .requestInterceptor(loggingInterceptor)
    ↓ .build()
RestClient (immutable, thread-safe)
    ↓ use in service
  .get().uri("/orders/{id}", 42)
  .retrieve().body(Order.class)
```

The builder is `@Scope("prototype")` so each `@Bean` that injects it gets an independent copy to customise. The built `RestClient` is thread-safe and should be a singleton.

Key `spring.http.client.*` properties (Spring Boot 3.2+):
```properties
spring.http.client.connect-timeout=5s
spring.http.client.read-timeout=30s
```

For `WebClient`, the underlying Reactor Netty connection pool is tuned via `spring.webflux.client.*` or directly on the builder.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RestClient.Builder and WebClient.Builder auto-configured and injected into service beans">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Auto-config -->
  <rect x="10" y="80" width="190" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Auto-configuration</text>
  <text x="105" y="122" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">RestClient.Builder @Bean</text>
  <text x="105" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ WebClient.Builder @Bean</text>

  <!-- Your @Bean -->
  <rect x="255" y="60" width="200" height="110" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="355" y="85" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Your @Bean</text>
  <text x="355" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">inject RestClient.Builder</text>
  <text x="355" y="119" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">.baseUrl(...)</text>
  <text x="355" y="133" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">.defaultHeader(...)</text>
  <text x="355" y="148" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">.build()</text>

  <!-- RestClient -->
  <rect x="515" y="80" width="170" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="600" y="105" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">RestClient</text>
  <text x="600" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">thread-safe singleton</text>
  <text x="600" y="137" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">used in service methods</text>

  <line x1="200" y1="115" x2="253" y2="115" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="455" y1="115" x2="513" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <text x="350" y="210" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Builder is @Scope("prototype") — each injection site gets its own copy to customise independently</text>
</svg>

The auto-configured builder is prototype-scoped; you inject and customise it, then build an immutable, thread-safe client.

## 5. Runnable example

```java
// RestClientBuilderDemo.java — run with: java RestClientBuilderDemo.java
// Shows RestClient and WebClient builder patterns, equivalent to how
// Spring Boot auto-configures and you customise them for outbound calls.

import java.net.URI;
import java.net.http.*;
import java.time.Duration;

public class RestClientBuilderDemo {

    public static void main(String[] args) throws Exception {
        System.out.println("=== RestClient / WebClient Builder Demo ===\n");

        printRestClientPattern();
        printWebClientPattern();
        printTestingPattern();
        demonstrateJdkHttpClient();
    }

    static void printRestClientPattern() {
        System.out.println("--- RestClient (Spring 6.1+ / Spring Boot 3.2+) ---");
        System.out.println("""
            // In a @Configuration class:
            @Bean
            RestClient orderServiceClient(RestClient.Builder builder) {
                return builder
                    .baseUrl("https://orders.api.example.com")
                    .defaultHeader("X-API-Version", "2")
                    .defaultStatusHandler(HttpStatusCode::is4xxClientError, (req, res) -> {
                        throw new OrderNotFoundException("Order not found: " + res.getStatusCode());
                    })
                    .build();
            }

            // In @Service:
            @Service
            public class OrderService {
                private final RestClient client;

                OrderService(RestClient orderServiceClient) {
                    this.client = orderServiceClient;
                }

                Order findById(long id) {
                    return client.get()
                        .uri("/orders/{id}", id)
                        .retrieve()
                        .body(Order.class);     // synchronous — blocks until response
                }

                Order create(CreateOrderRequest req) {
                    return client.post()
                        .uri("/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .body(req)
                        .retrieve()
                        .body(Order.class);
                }
            }
            """);
    }

    static void printWebClientPattern() {
        System.out.println("--- WebClient (reactive, non-blocking) ---");
        System.out.println("""
            // In a @Configuration class (WebFlux or Mixed stack):
            @Bean
            WebClient paymentClient(WebClient.Builder builder) {
                return builder
                    .baseUrl("https://payments.api.example.com")
                    .defaultHeader(HttpHeaders.AUTHORIZATION, "Bearer " + apiKey)
                    .filter(ExchangeFilterFunction.ofRequestProcessor(req -> {
                        log.debug("Calling: {} {}", req.method(), req.url());
                        return Mono.just(req);
                    }))
                    .build();
            }

            // In @Service:
            Mono<PaymentResult> charge(ChargeRequest req) {
                return paymentClient.post()
                    .uri("/charges")
                    .bodyValue(req)
                    .retrieve()
                    .onStatus(HttpStatusCode::is4xxClientError,
                        r -> r.bodyToMono(ErrorResponse.class).map(PaymentException::new))
                    .bodyToMono(PaymentResult.class)
                    .timeout(Duration.ofSeconds(10));
            }
            """);
    }

    static void printTestingPattern() {
        System.out.println("--- Testing outbound REST calls ---");
        System.out.println("""
            // Fake server for testing (Spring Boot Test):
            @SpringBootTest(webEnvironment = RANDOM_PORT)
            class OrderServiceTest {

                @Autowired RestClientTestRequestValues testValues;  // Spring Boot 3.2+

                // OR: MockWebServer (OkHttp):
                MockWebServer mockServer = new MockWebServer();

                @Test
                void findOrder_callsDownstreamApi() {
                    mockServer.enqueue(new MockResponse()
                        .setResponseCode(200)
                        .setBody(\"\"\"{ "id": 42, "status": "SHIPPED" }\"\"\")
                        .setHeader("Content-Type", "application/json"));

                    Order order = orderService.findById(42);
                    assertThat(order.status()).isEqualTo("SHIPPED");
                }
            }
            """);
    }

    static void demonstrateJdkHttpClient() throws Exception {
        System.out.println("--- Equivalent using JDK HttpClient (for comparison) ---");

        // JDK 11+ built-in — no Spring needed — shows what RestClient does under the hood
        HttpClient client = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/get"))
            .header("Accept", "application/json")
            .GET()
            .build();

        System.out.println("  Built JDK HttpClient (equivalent to RestClient internals)");
        System.out.println("  Request: GET " + request.uri());
        System.out.println("  (actual HTTP call skipped in demo — would need network)");
        System.out.println();

        System.out.println("--- application.properties for RestClient ---");
        System.out.println("""
            spring.http.client.connect-timeout=5s
            spring.http.client.read-timeout=30s

            # RestTemplate (legacy builder still available):
            spring.resttemplate.interceptors.class=...
            """);
    }
}
```

**How to run:** `java RestClientBuilderDemo.java`

## 6. Walkthrough

- **`RestClient.Builder` is `@Scope("prototype")`** — each bean that injects it gets an independent instance. If two services both inject `RestClient.Builder`, they customise separate builder instances. This is why you can set `.baseUrl(...)` without affecting other callers.
- **`.defaultStatusHandler()`** — registers a global error handler for this client. `HttpStatusCode::is4xxClientError` matches any 400–499 response. The handler can throw a domain exception, read the error body, or return a fallback response. This keeps error handling out of service methods.
- **`WebClient` timeout via `.timeout(Duration)`** — `Mono.timeout()` cuts off the reactive pipeline after the duration. The upstream `WebClient` call is cancelled. Without this, a slow downstream service holds a reactive thread indefinitely.
- **`MockWebServer`** — the recommended testing tool for outbound HTTP. It's an in-process HTTP server that you enqueue responses on. Spring Boot 3.2+ also offers `@RestClientTest` + `RestClientTestRequestValues` for simpler assertion of calls made.
- **JDK `HttpClient`** — Spring Boot 3.2's `RestClient` uses JDK `HttpClient` as the default underlying transport (replacing the previous Apache HttpClient default). Setting `spring.http.client.connect-timeout` configures this underlying client.

## 7. Gotchas & takeaways

> **`RestClient` is synchronous, `WebClient` is not.** If you call `webClient.get().retrieve().bodyToMono(...)` from a `@RestController` that is not reactive, you must call `.block()` to get the value — but `.block()` inside a reactive context (WebFlux request thread) throws `IllegalStateException`. Use `RestClient` in MVC apps; `WebClient` in WebFlux apps.

> **`RestTemplate` is still available but deprecated for new code.** `RestTemplateBuilder` auto-configures a builder bean (not a `RestTemplate` bean). Inject `RestTemplateBuilder`, customise, and call `.build()` — same pattern as `RestClient.Builder`. Migrate to `RestClient` for new code.

- Use `RestClient.Builder`'s `.requestInterceptor(ClientHttpRequestInterceptor)` for logging, auth tokens, or retry logic — avoids duplicating this in every service method.
- `@LoadBalanced RestClient.Builder` (Spring Cloud) enables client-side load balancing with service discovery for calls like `.baseUrl("http://order-service/")`.
- For resilience (retry, circuit breaker), wrap `RestClient` with Resilience4j: `RestClient.builder().requestInterceptor(new Resilience4jInterceptor(...))`.
- Test with `@RestClientTest(OrderService.class)` — Spring Boot creates a minimal context with just the client and a `MockRestServiceServer`.
