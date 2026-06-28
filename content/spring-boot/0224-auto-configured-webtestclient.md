---
card: spring-boot
gi: 224
slug: auto-configured-webtestclient
title: "Auto-configured WebTestClient"
---

## 1. What it is

`WebTestClient` is the reactive counterpart of `TestRestTemplate`. Spring Boot auto-configures it for tests in two scenarios: (1) `@SpringBootTest` with `RANDOM_PORT` or `DEFINED_PORT` — binds to a real running server; (2) `@WebFluxTest` — binds to the mock reactive web environment. Unlike `TestRestTemplate`, `WebTestClient` is non-blocking and supports reactive assertions, SSE streams, and WebSocket connections.

## 2. Why & when

Use auto-configured `WebTestClient` when:
- Your app uses Spring WebFlux (`@RestController` + reactive return types like `Mono<T>`, `Flux<T>`).
- You want to test streaming endpoints (Server-Sent Events, WebFlux streaming).
- You need the reactive assertion API (`.value()`, `.expectBodyList()`, `.returnResult()`).
- Full integration tests via `@SpringBootTest(RANDOM_PORT)` where `TestRestTemplate` is insufficient for reactive responses.

For standard Spring MVC apps, use `MockMvc` (with `@WebMvcTest`) or `TestRestTemplate` (with `@SpringBootTest`) instead.

## 3. Core concept

```java
// With @WebFluxTest (mock environment — no real server)
@WebFluxTest(OrderController.class)
class OrderWebFluxTest {

    @Autowired WebTestClient webTestClient;
    @MockitoBean OrderService orderService;

    @Test
    void getOrder_returnsMonoResponse() {
        when(orderService.findById("1")).thenReturn(Mono.just(new Order("1","alice",99.99)));

        webTestClient.get().uri("/orders/1")
                .exchange()
                .expectStatus().isOk()
                .expectBody(Order.class)
                .value(o -> assertThat(o.customer()).isEqualTo("alice"));
    }

    @Test
    void listOrders_returnsFluxAsJsonArray() {
        when(orderService.findAll()).thenReturn(Flux.just(
                new Order("1","alice",99.99), new Order("2","bob",149.0)));

        webTestClient.get().uri("/orders")
                .exchange()
                .expectStatus().isOk()
                .expectBodyList(Order.class).hasSize(2);
    }
}

// With @SpringBootTest (real server — full integration)
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
class OrderIntegrationTest {

    @Autowired WebTestClient webTestClient;

    @Test
    void fullStack_getOrder() {
        webTestClient.get().uri("/orders/1")
                .exchange()
                .expectStatus().isOk()
                .expectBody().jsonPath("$.customer").isEqualTo("alice");
    }
}
```

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="WebTestClient auto-configured in two modes: @WebFluxTest connects to mock reactive environment, @SpringBootTest connects to real embedded server; both return reactive assertions with expectStatus, expectBody, expectBodyList">
  <!-- WebTestClient -->
  <rect x="10" y="70" width="140" height="80" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/>
  <text x="75" y="93" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">WebTestClient</text>
  <text x="75" y="108" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">.get().uri("/orders/1")</text>
  <text x="75" y="121" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">.exchange()</text>
  <text x="75" y="134" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">.expectStatus().isOk()</text>
  <text x="75" y="146" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">.expectBody(Order.class)</text>

  <!-- Arrow to modes -->
  <line x1="152" y1="110" x2="200" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#wtc_a)"/>
  <line x1="152" y1="120" x2="200" y2="145" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#wtc_a)"/>

  <!-- Mode 1: @WebFluxTest -->
  <rect x="205" y="30" width="220" height="100" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="315" y="52" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@WebFluxTest (mock env)</text>
  <rect x="216" y="62" width="198" height="24" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="315" y="78" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Reactive WebFilter + Router</text>
  <rect x="216" y="93" width="198" height="24" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="315" y="109" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@Controller (WebFlux)</text>
  <text x="315" y="125" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">No real server — dispatches in-process</text>

  <!-- Mode 2: @SpringBootTest RANDOM_PORT -->
  <rect x="205" y="142" width="220" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="315" y="163" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@SpringBootTest RANDOM_PORT</text>
  <text x="315" y="180" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Real Netty / Tomcat — full HTTP stack</text>

  <!-- Assertions -->
  <rect x="465" y="55" width="205" height="110" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="567" y="76" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Reactive Assertions</text>
  <text x="567" y="94" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">.expectStatus().isOk() / isCreated()</text>
  <text x="567" y="108" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">.expectBody(T.class).value(Consumer)</text>
  <text x="567" y="121" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">.expectBodyList(T.class).hasSize(n)</text>
  <text x="567" y="134" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">.expectBody().jsonPath("$.x").isEq("y")</text>
  <text x="567" y="148" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">.returnResult() → FluxExchangeResult</text>
  <text x="567" y="162" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">Streaming: .getResponseBody()</text>

  <line x1="427" y1="80" x2="463" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#wtc_a)"/>
  <line x1="427" y1="162" x2="463" y2="130" stroke="#6db33f" stroke-width="1.5" marker-end="url(#wtc_b)"/>

  <text x="340" y="195" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Same API for mock and real server — swap @WebFluxTest ↔ @SpringBootTest</text>

  <defs>
    <marker id="wtc_a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="wtc_b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

`WebTestClient` is auto-configured for both `@WebFluxTest` (in-process dispatch) and `@SpringBootTest(RANDOM_PORT)` (real HTTP). Same assertion API for both.

## 5. Runnable example

```java
// WebTestClientDemo.java — simulates auto-configured WebTestClient assertion patterns
// How to run: java WebTestClientDemo.java  (JDK 17+, no dependencies)
// Real use: @WebFluxTest + @Autowired WebTestClient  OR  @SpringBootTest + @Autowired WebTestClient

import java.util.*;
import java.util.function.*;

public class WebTestClientDemo {

    record Order(String id, String customer, double total) {}

    // Simulates reactive response (Mono/Flux)
    sealed interface ReactiveResult<T> permits ReactiveResult.Ok, ReactiveResult.Empty, ReactiveResult.Err {
        record Ok<T>(T value) implements ReactiveResult<T> {}
        record Empty<T>() implements ReactiveResult<T> {}
        record Err<T>(int status, String message) implements ReactiveResult<T> {}
    }

    // Simulates WebFlux controller
    static class OrderController {
        private final Map<String, Order> db = new LinkedHashMap<>();

        OrderController() {
            db.put("1", new Order("1", "alice", 99.99));
            db.put("2", new Order("2", "bob",   149.50));
        }

        ReactiveResult<Order> findById(String id) {
            Order o = db.get(id);
            return o != null ? new ReactiveResult.Ok<>(o) : new ReactiveResult.Err<>(404, "Not Found");
        }

        ReactiveResult<List<Order>> findAll() {
            return new ReactiveResult.Ok<>(List.copyOf(db.values()));
        }

        ReactiveResult<Order> create(Order o) {
            db.put(o.id(), o);
            return new ReactiveResult.Ok<>(o);
        }
    }

    // Simulates WebTestClient response spec
    static class ResponseSpec {
        private final int status;
        private final Object body;
        private boolean statusChecked = false;

        ResponseSpec(int status, Object body) { this.status = status; this.body = body; }

        StatusAssertions expectStatus() { return new StatusAssertions(this); }

        @SuppressWarnings("unchecked")
        <T> BodySpec<T> expectBody(Class<T> type) {
            return new BodySpec<>(body instanceof List ? null : type.cast(body));
        }

        @SuppressWarnings("unchecked")
        <T> ListBodySpec<T> expectBodyList(Class<T> type) {
            List<T> list = body instanceof List ? (List<T>) body : List.of();
            return new ListBodySpec<>(list);
        }

        JsonBodySpec expectBody() { return new JsonBodySpec(body); }
    }

    static class StatusAssertions {
        private final ResponseSpec spec;
        StatusAssertions(ResponseSpec spec) { this.spec = spec; }

        ResponseSpec isOk()      { return assertStatus(200); }
        ResponseSpec isCreated() { return assertStatus(201); }
        ResponseSpec isNotFound() { return assertStatus(404); }

        private ResponseSpec assertStatus(int expected) {
            if (spec.status != expected)
                throw new AssertionError("Expected status " + expected + " but was " + spec.status);
            System.out.println("  ✓ expectStatus()." + (expected == 200 ? "isOk" : expected == 201 ? "isCreated" : "isNotFound") + "()");
            return spec;
        }
    }

    static class BodySpec<T> {
        private final T body;
        BodySpec(T body) { this.body = body; }

        void value(Consumer<T> consumer) {
            consumer.accept(body);
            System.out.println("  ✓ .value(consumer) — body assertion passed");
        }

        T returnResult() { return body; }
    }

    static class ListBodySpec<T> {
        private final List<T> list;
        ListBodySpec(List<T> list) { this.list = list; }

        ListBodySpec<T> hasSize(int expected) {
            if (list.size() != expected)
                throw new AssertionError("Expected list size " + expected + " but was " + list.size());
            System.out.println("  ✓ expectBodyList().hasSize(" + expected + ")");
            return this;
        }

        ListBodySpec<T> contains(Predicate<T> predicate, String label) {
            if (list.stream().noneMatch(predicate))
                throw new AssertionError("List does not contain matching element: " + label);
            System.out.println("  ✓ list contains: " + label);
            return this;
        }
    }

    static class JsonBodySpec {
        private final Object body;
        JsonBodySpec(Object body) { this.body = body; }

        JsonBodySpec jsonPathEquals(String path, Object expected) {
            // Simplified path check on Order
            if (body instanceof Order o) {
                String field = path.replace("$.", "");
                Object actual = switch (field) {
                    case "id" -> o.id(); case "customer" -> o.customer(); case "total" -> o.total();
                    default -> null;
                };
                if (!expected.equals(actual) && !expected.toString().equals(String.valueOf(actual)))
                    throw new AssertionError("jsonPath " + path + " = " + actual + " expected " + expected);
                System.out.println("  ✓ .jsonPath(\"" + path + "\").isEqualTo(" + expected + ")");
            }
            return this;
        }
    }

    // Simulates WebTestClient
    static class WebTestClient {
        private final OrderController controller;

        WebTestClient(OrderController controller) { this.controller = controller; }

        RequestSpec get() { return new RequestSpec("GET", controller); }
        RequestSpec post() { return new RequestSpec("POST", controller); }
    }

    static class RequestSpec {
        private final String method;
        private final OrderController controller;
        private String uri;
        private Object requestBody;

        RequestSpec(String method, OrderController controller) {
            this.method = method; this.controller = controller;
        }

        RequestSpec uri(String uri) { this.uri = uri; return this; }
        RequestSpec bodyValue(Object body) { this.requestBody = body; return this; }

        ResponseSpec exchange() {
            System.out.println("  [WebTestClient] " + method + " " + uri);
            if ("GET".equals(method)) {
                if (uri.matches("/orders/[^/]+")) {
                    String id = uri.substring("/orders/".length());
                    ReactiveResult<Order> result = controller.findById(id);
                    if (result instanceof ReactiveResult.Ok<Order> ok)
                        return new ResponseSpec(200, ok.value());
                    if (result instanceof ReactiveResult.Err<Order> err)
                        return new ResponseSpec(err.status(), err.message());
                }
                if ("/orders".equals(uri)) {
                    ReactiveResult<List<Order>> result = controller.findAll();
                    if (result instanceof ReactiveResult.Ok<List<Order>> ok)
                        return new ResponseSpec(200, ok.value());
                }
            }
            if ("POST".equals(method) && "/orders".equals(uri) && requestBody instanceof Order o) {
                return new ResponseSpec(201, controller.create(o) instanceof ReactiveResult.Ok<Order> ok ? ok.value() : null);
            }
            return new ResponseSpec(404, "Not Found");
        }
    }

    static void expect(boolean c, String m) {
        if (!c) throw new AssertionError("FAIL: " + m);
        System.out.println("  ✓ " + m);
    }

    public static void main(String[] args) {
        System.out.println("=== Auto-configured WebTestClient Demo ===\n");

        OrderController controller = new OrderController();
        WebTestClient client = new WebTestClient(controller);

        // Test 1: GET single order → 200 + body assertion
        System.out.println("--- Test 1: GET /orders/1 → expectBody().value() ---");
        client.get().uri("/orders/1").exchange()
                .expectStatus().isOk()
                .expectBody(Order.class)
                .value(o -> {
                    expect("alice".equals(o.customer()), "customer = alice");
                    expect(o.total() == 99.99,           "total = 99.99");
                });

        // Test 2: GET list → expectBodyList()
        System.out.println("\n--- Test 2: GET /orders → expectBodyList().hasSize(2) ---");
        client.get().uri("/orders").exchange()
                .expectStatus().isOk()
                .expectBodyList(Order.class)
                .hasSize(2)
                .contains(o -> "alice".equals(o.customer()), "alice in list")
                .contains(o -> "bob".equals(o.customer()),   "bob in list");

        // Test 3: GET not found → 404
        System.out.println("\n--- Test 3: GET /orders/999 → 404 (no throw) ---");
        client.get().uri("/orders/999").exchange()
                .expectStatus().isNotFound();

        // Test 4: POST → 201 + jsonPath assertion
        System.out.println("\n--- Test 4: POST /orders → 201 + jsonPath ---");
        client.post().uri("/orders")
                .bodyValue(new Order("3", "carol", 75.00)).exchange()
                .expectStatus().isCreated()
                .expectBody()
                .jsonPathEquals("$.customer", "carol")
                .jsonPathEquals("$.total",    75.00);

        System.out.println("\n--- Real auto-configured WebTestClient ---");
        System.out.println("""
// Mode 1: @WebFluxTest (mock server — fast slice test)
@WebFluxTest(OrderController.class)
class OrderWebFluxTest {
    @Autowired WebTestClient client;
    @MockitoBean OrderService service;

    @Test void getOrder() {
        when(service.findById("1")).thenReturn(Mono.just(new Order("1","alice",99.99)));

        client.get().uri("/orders/1")
              .exchange()
              .expectStatus().isOk()
              .expectBody(Order.class)
              .value(o -> assertThat(o.customer()).isEqualTo("alice"));
    }

    @Test void listOrders() {
        when(service.findAll()).thenReturn(Flux.just(
            new Order("1","alice",99.99), new Order("2","bob",149.0)));

        client.get().uri("/orders")
              .exchange()
              .expectStatus().isOk()
              .expectBodyList(Order.class).hasSize(2);
    }
}

// Mode 2: @SpringBootTest (real server — full integration)
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
class OrderIntegrationTest {
    @Autowired WebTestClient client;  // bound to random port automatically

    @Test void fullStack() {
        client.get().uri("/orders/1")
              .exchange()
              .expectStatus().isOk()
              .expectBody().jsonPath("$.customer").isEqualTo("alice");
    }
}

// SSE streaming assertion:
// client.get().uri("/events")
//       .accept(MediaType.TEXT_EVENT_STREAM)
//       .exchange()
//       .returnResult(String.class)
//       .getResponseBody()  // → Flux<String>
//       .take(3)
//       .as(StepVerifier::create)
//       .expectNext("event1","event2","event3")
//       .verifyComplete();""");

        System.out.println("\nAll tests passed.");
    }
}
```

**How to run:** `java WebTestClientDemo.java`

## 6. Walkthrough

- **Test 1 (single entity)**: `.expectBody(Order.class).value(consumer)` deserializes the response body into `Order` and passes it to the `Consumer<Order>` lambda for assertions. This is the reactive analogue of `assertThat(response.getBody().customer()).isEqualTo(...)`.
- **Test 2 (list)**: `.expectBodyList(Order.class).hasSize(2)` asserts the `Flux<Order>` result came back as a JSON array with 2 elements. The `contains(predicate)` chain verifies specific elements are present.
- **Test 3 (404, no throw)**: like `TestRestTemplate`, `WebTestClient` does not throw on non-2xx — it returns the response for assertion. `expectStatus().isNotFound()` is the preferred style over checking `status == 404`.
- **Test 4 (POST + jsonPath)**: `.bodyValue(order)` serializes the request body. `.expectBody().jsonPath("$.customer").isEqualTo("carol")` asserts on the raw JSON response without needing to deserialize.
- **SSE streaming**: `.returnResult(String.class).getResponseBody()` returns a `Flux<String>` — use `StepVerifier.create(flux).expectNext(...).verifyComplete()` for reactive streaming assertions.

## 7. Gotchas & takeaways

> `WebTestClient` auto-configuration depends on the test annotation. `@WebFluxTest` binds to a mock server in-process (no port). `@SpringBootTest(RANDOM_PORT)` binds to a real Netty/Tomcat port. With `@SpringBootTest`, inject `@Autowired WebTestClient` — Spring Boot 2.7+ configures it automatically for reactive AND servlet-based apps (servlet apps use `MockMvcWebTestClient`).

> `WebTestClient` assertions are **lazy until** `.exchange()` is called. Build the request chain first, then call `.exchange()`, then chain assertions. Do not call `.expectStatus()` before `.exchange()`.

- `expectBody().isEmpty()` — asserts the response has no body (e.g., 204 No Content).
- `expectHeader().contentType(MediaType.APPLICATION_JSON)` — asserts response headers.
- `mutateWith(csrf())` — CSRF support for POST/PUT requests in security-enabled slices.
- `mutateWith(mockUser("alice").roles("ADMIN"))` — security context injection without HTTP auth round-trip.
- For `@SpringBootTest` with servlet stack (not reactive): `WebTestClient` wraps `MockMvc` internally via `MockMvcWebTestClient` — same assertion API works.
