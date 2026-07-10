---
card: spring-framework
gi: 386
slug: reactive-testing-webtestclient
title: "Reactive testing (WebTestClient)"
---

## 1. What it is

`WebTestClient` is Spring's dedicated test client for WebFlux applications (briefly introduced in the WebFlux vs WebMVC comparison card) — a fluent, `WebClient`-styled API purpose-built for testing, capable of running against a fully mocked, in-memory WebFlux application context (no real server, no network) or against a genuinely running server over real HTTP, with rich, chainable assertion methods for status, headers, and body content.

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class ProductControllerTest {

    @Autowired WebTestClient webTestClient;

    @Test
    void getReturnsProduct() {
        webTestClient.get().uri("/products/1")
            .exchange()
            .expectStatus().isOk()
            .expectBody()
            .jsonPath("$.name").isEqualTo("Drill");
    }
}
```

## 2. Why & when

`WebTestClient` deliberately mirrors `WebClient`'s fluent API (request building via `.get()`/`.post()`/`.uri(...)`/etc.), so if you already know `WebClient`, most of `WebTestClient`'s request-building syntax is immediately familiar — the genuinely new part is the assertion chain (`.expectStatus()`, `.expectBody()`, `.expectHeader()`) that replaces manual response inspection. Use `WebTestClient` for:

- Testing any WebFlux controller (annotated or functional) — it's the standard, recommended testing tool for this framework, analogous to `MockMvc` for Spring MVC.
- Testing streaming responses (`Flux<T>` with SSE or NDJSON) via its `.returnResult()`/`FluxExchangeResult` capabilities, which can consume and assert against a genuinely streaming response over time — something a simpler request/response-only test tool couldn't express.
- Integration testing a running server over real HTTP (`bindToServer()`) or, more commonly for fast unit-style tests, testing directly against an in-memory `ApplicationContext` (`bindToApplicationContext(...)`) without starting a real network listener at all.

## 3. Core concept

```
Two binding modes:

  bindToApplicationContext(context).build()   — IN-MEMORY, no real server,
                                                   FAST, most common for unit tests
  bindToServer().baseUrl("http://localhost:8080").build()
                                                — REAL HTTP, against an ACTUALLY
                                                   running server (integration tests)

@SpringBootTest(webEnvironment = RANDOM_PORT) autoconfigures
a WebTestClient bean bound to the REAL running test server automatically.

Request-building — MIRRORS WebClient:
  .get()/.post()/.put()/.delete() .uri(...) .header(...) .bodyValue(...)

.exchange() — commits the request, returns a ResponseSpec for assertions:

  .expectStatus().isOk() / .isNotFound() / .isEqualTo(HttpStatus...)
  .expectHeader().contentType(MediaType...)
  .expectBody(Product.class).isEqualTo(expectedProduct)
  .expectBody().jsonPath("$.name").isEqualTo("Drill")
  .expectBodyList(Product.class).hasSize(3)

Streaming responses:
  .returnResult(Product.class).getResponseBody()   — a Flux<Product>
    you can then subscribe to / assert against with StepVerifier
```

## 4. Diagram

<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="200" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">WebTestClient: WebClient-styled requests, fluent assertions</text>

  <rect x="20" y="50" width="220" height="50" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="130" y="80" text-anchor="middle" fill="#79c0ff" font-size="10">.get().uri("/products/1")</text>

  <line x1="240" y1="75" x2="290" y2="75" stroke="#8b949e" marker-end="url(#a62)"/>

  <rect x="290" y="50" width="120" height="50" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="350" y="80" text-anchor="middle" fill="#6db33f" font-size="10">.exchange()</text>

  <line x1="410" y1="75" x2="460" y2="75" stroke="#8b949e" marker-end="url(#a62)"/>

  <rect x="460" y="50" width="240" height="50" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="580" y="80" text-anchor="middle" fill="#e6edf3" font-size="10">.expectStatus().isOk()...</text>

  <defs>
    <marker id="a62" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Requests are built exactly like `WebClient`; `.exchange()` commits, and a chain of `.expect*()` assertions verify the result.*

## 5. Runnable example

### Level 1 — Basic

Testing a simple GET endpoint, both against an in-memory context and a running server:

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {

    record Product(long id, String name) {}

    @GetMapping("/products/{id}")
    public Mono<Product> get(@PathVariable long id) {
        return Mono.just(new Product(id, "Drill"));
    }
}
```

```java
// ProductControllerUnitTest.java — FAST, in-memory, no real server started
import org.junit.jupiter.api.Test;
import org.springframework.test.web.reactive.server.WebTestClient;

class ProductControllerUnitTest {

    private final WebTestClient webTestClient = WebTestClient
        .bindToController(new ProductController())
        .build();

    @Test
    void getReturnsProduct() {
        webTestClient.get().uri("/products/1")
            .exchange()
            .expectStatus().isOk()
            .expectBody()
            .jsonPath("$.name").isEqualTo("Drill");
    }
}
```

```java
// ProductControllerIntegrationTest.java — REAL server, full Spring context
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.reactive.server.WebTestClient;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class ProductControllerIntegrationTest {

    @Autowired WebTestClient webTestClient;   // autoconfigured, bound to the RUNNING test server

    @Test
    void getReturnsProduct() {
        webTestClient.get().uri("/products/1")
            .exchange()
            .expectStatus().isOk()
            .expectBody()
            .jsonPath("$.name").isEqualTo("Drill");
    }
}
```

**How to run:**
```bash
./mvnw test
# Both tests pass — IDENTICAL assertions, different underlying execution:
# ProductControllerUnitTest: no real server, no Spring context beyond the one controller
# ProductControllerIntegrationTest: FULL Spring Boot context, real HTTP over a random port
```

`bindToController(new ProductController())` creates a `WebTestClient` wired to test just that one controller class directly, in memory — extremely fast, ideal for focused unit tests of a single controller's routing/argument-binding logic without needing the full application context. The integration test variant, using `@SpringBootTest` with `RANDOM_PORT`, exercises the entire application stack (all autoconfiguration, all beans, real network I/O) at the cost of slower test startup.

### Level 2 — Intermediate

Testing request bodies, validation errors, and JSON path assertions on nested structures:

```java
// ProductController.java (extended)
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {

    record ProductRequest(@NotBlank String name, @Positive double price) {}
    record Product(long id, String name, double price) {}

    @PostMapping("/products")
    public Mono<ResponseEntity<Product>> create(@Valid @RequestBody Mono<ProductRequest> requestMono) {
        return requestMono.map(request ->
            ResponseEntity.status(HttpStatus.CREATED).body(new Product(1, request.name(), request.price())));
    }
}
```

```java
// ProductControllerTest.java (extended)
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.reactive.server.WebTestClient;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class ProductControllerTest {

    @Autowired WebTestClient webTestClient;

    @Test
    void createReturnsCreatedProduct() {
        webTestClient.post().uri("/products")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue("""
                {"name":"Drill","price":29.99}
                """)
            .exchange()
            .expectStatus().isCreated()
            .expectBody()
            .jsonPath("$.id").isEqualTo(1)
            .jsonPath("$.name").isEqualTo("Drill")
            .jsonPath("$.price").isEqualTo(29.99);
    }

    @Test
    void createWithInvalidDataReturnsBadRequest() {
        webTestClient.post().uri("/products")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue("""
                {"name":"","price":-5}
                """)
            .exchange()
            .expectStatus().isBadRequest();
    }
}
```

**How to run:**
```bash
./mvnw test
# Both tests pass: valid input produces a 201 with the expected JSON fields;
# invalid input (blank name, negative price) correctly produces a 400
```

**What changed:** `.jsonPath("$.field").isEqualTo(...)` provides targeted assertions against specific fields in the response body, without needing to deserialize the entire JSON into a Java object first — useful when only specific fields matter for a given test, or when testing against an API contract you don't control a matching Java class for. The invalid-input test demonstrates verifying error-path behavior (validation failures producing `400`) exactly as thoroughly as the success path.

### Level 3 — Advanced

Testing a streaming SSE response using `StepVerifier` (Reactor's own testing library, working in tandem with `WebTestClient`'s streaming result extraction) — verifying not just the final outcome but the timing and sequence of individually-arriving elements:

```java
// StreamController.java
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

import java.time.Duration;

@RestController
public class StreamController {

    @GetMapping(value = "/events", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> stream() {
        return Flux.interval(Duration.ofMillis(100))
            .take(3)
            .map(tick -> ServerSentEvent.<String>builder().data("tick " + tick).build());
    }
}
```

```java
// StreamControllerTest.java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.test.web.reactive.server.FluxExchangeResult;
import org.springframework.test.web.reactive.server.WebTestClient;
import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

import java.time.Duration;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class StreamControllerTest {

    @Autowired WebTestClient webTestClient;

    @Test
    void streamEmitsThreeTicksInOrder() {
        FluxExchangeResult<ServerSentEvent> result = webTestClient.get().uri("/events")
            .exchange()
            .expectStatus().isOk()
            .returnResult(ServerSentEvent.class);

        Flux<ServerSentEvent> eventStream = result.getResponseBody();

        StepVerifier.create(eventStream)
            .expectNextMatches(event -> "tick 0".equals(event.data()))
            .expectNextMatches(event -> "tick 1".equals(event.data()))
            .expectNextMatches(event -> "tick 2".equals(event.data()))
            .expectComplete()
            .verify(Duration.ofSeconds(2));   // fail the test if this doesn't complete within 2s
    }
}
```

**How to run:**
```bash
./mvnw test
# streamEmitsThreeTicksInOrder passes, verifying:
# - exactly three events arrive
# - each one's data matches "tick 0", "tick 1", "tick 2" IN ORDER
# - the stream properly completes afterward
# - the whole thing happens within 2 seconds (fails loudly if it hangs)
```

**What changed and why:**
- `.returnResult(ServerSentEvent.class)` (instead of `.expectBody(...)`, used for ordinary, single-value responses) is specifically designed for streaming responses — it doesn't wait for the whole response to complete before returning; it gives back a `FluxExchangeResult` wrapping the response as a genuine, still-live `Flux<ServerSentEvent>` you can then assert against as it arrives.
- `StepVerifier` (Reactor's own dedicated testing utility, distinct from `WebTestClient` itself but commonly paired with it for exactly this kind of streaming assertion) lets you assert not just *that* certain values arrive, but their *exact sequence* and that the stream *completes* correctly — `.expectNextMatches(...)` chains verify each element in order, and `.expectComplete()` confirms the `Flux` terminates as expected rather than hanging or erroring.
- `.verify(Duration.ofSeconds(2))` imposes an explicit timeout on the entire verification — without this, a bug causing the stream to never complete (or never emit expected values) could hang the test indefinitely rather than failing promptly with a clear timeout error, a genuinely important safeguard for any test asserting against a live, time-based reactive stream.

## 6. Walkthrough

**Test execution: `streamEmitsThreeTicksInOrder` (Level 3 code), tracing what happens step by step.**

1. `webTestClient.get().uri("/events").exchange()` sends a real HTTP `GET` request (since this is a `@SpringBootTest(webEnvironment = RANDOM_PORT)` test, `WebTestClient` is bound to the actually-running embedded server) to `/events`, initiating the SSE connection.
2. `.expectStatus().isOk()` asserts the initial response status is `200` — this check happens essentially immediately, based on the response headers, before the (potentially long-lived) streaming body has necessarily finished arriving.
3. `.returnResult(ServerSentEvent.class)` doesn't wait for the stream to complete — it returns a `FluxExchangeResult` object immediately, wrapping continued access to the response body as it arrives. `result.getResponseBody()` extracts this as a genuine `Flux<ServerSentEvent>`.
4. `StepVerifier.create(eventStream)` subscribes to this `Flux`, beginning to actively consume events from the still-in-progress streaming HTTP response. This subscription is what actually triggers `StreamController.stream()`'s underlying `Flux.interval(100ms).take(3)` to (if it hasn't already) begin emitting ticks — though in this case, subscription already happened implicitly when the HTTP request was made and the server began processing it.
5. `.expectNextMatches(event -> "tick 0".equals(event.data()))` waits for the first SSE event to arrive over the connection (up to ~100ms after the server-side interval starts), then checks its `data()` field equals `"tick 0"` — if a different value arrived, or if too much time passed with nothing arriving, this step would fail.
6. `.expectNextMatches(...)` for `"tick 1"` similarly waits for and verifies the second event, arriving roughly 100ms after the first.
7. `.expectNextMatches(...)` for `"tick 2"` verifies the third and final expected event.
8. `.expectComplete()` asserts that, after these three events, the underlying `Flux` (and therefore the SSE connection/response) properly signals completion — matching the server's `.take(3)` operator, which causes `Flux.interval` to stop and complete after exactly three emissions.
9. `.verify(Duration.ofSeconds(2))` triggers the actual execution of this entire verification sequence (steps 4–8 were building a *specification*, not yet running it) and blocks the test thread until either all expectations are satisfied or the 2-second timeout elapses — since the real elapsed time for three 100ms-spaced ticks plus completion is roughly 300ms, well under the 2-second budget, the test completes successfully well within its allotted time.

## 7. Gotchas & takeaways

> **`bindToController(...)`-based unit tests don't load the full Spring application context** — they won't catch configuration issues, missing beans, or `@ControllerAdvice`-based global exception handling that a full `@SpringBootTest` integration test would exercise. Use focused unit tests for fast iteration on a controller's own logic, but retain integration tests for verifying the full request pipeline, including cross-cutting concerns.

> **`.expectBody(SomeType.class)` deserializes the entire response body into that one type upfront** — for a streaming response (SSE, NDJSON), this either doesn't make sense or forces the test to wait for the entire stream to complete before any assertion happens, defeating the purpose of testing streaming behavior specifically. Use `.returnResult(...)` combined with `StepVerifier` (as in Level 3) whenever the test genuinely needs to observe streaming, element-by-element behavior.

> **Forgetting `.verify(timeout)` (or using `StepVerifier` without any timeout at all) on an assertion against a stream that never actually completes as expected can hang the test suite indefinitely** rather than failing with a clear, fast error — always bound `StepVerifier` verification with an explicit, reasonable timeout.

- `WebTestClient` mirrors `WebClient`'s fluent request-building API, adding a rich chain of `.expect*()` assertion methods for verifying status, headers, and body content.
- `bindToController(...)`/`bindToApplicationContext(...)` provide fast, in-memory testing without a real server; `@SpringBootTest(webEnvironment = RANDOM_PORT)` autoconfigures a `WebTestClient` bound to a genuinely running server for full integration testing.
- `.returnResult(...)` combined with Reactor's `StepVerifier` enables genuine, sequence-and-timing-aware assertions against streaming responses (SSE, NDJSON) that simple `.expectBody(...)` assertions cannot express.
- Always bound `StepVerifier` assertions with an explicit `.verify(timeout)` to avoid an indefinitely hanging test suite when a stream doesn't behave as expected.
