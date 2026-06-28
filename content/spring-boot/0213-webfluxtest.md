---
card: spring-boot
gi: 213
slug: webfluxtest
title: "@WebFluxTest"
---

## 1. What it is

`@WebFluxTest` is the reactive counterpart of `@WebMvcTest`. It loads only the reactive web layer — `@RestController`, `@ControllerAdvice`, `WebFilter`, and `WebFluxConfigurer` beans — and auto-configures a `WebTestClient`. It does NOT load services, repositories, or JPA. Use it to test Spring WebFlux (Netty-based reactive) controllers in isolation, using the same fast, no-real-server approach as `@WebMvcTest`.

## 2. Why & when

Use `@WebFluxTest` when your application uses Spring WebFlux (reactive stack) and you need to:
- Test reactive `@RestController` request mappings and response bodies.
- Verify `Mono<T>` and `Flux<T>` return types serialize correctly.
- Test Server-Sent Events (SSE) or streaming responses.
- Validate `@Valid` bean validation in reactive controllers.
- Test reactive security with `@WithMockUser` or `SecurityWebFilterChain` mocks.

It is functionally equivalent to `@WebMvcTest` but for the reactive stack — same isolation principle, different infrastructure (Netty + WebFlux vs Tomcat + Spring MVC).

## 3. Core concept

```java
@WebFluxTest(OrderController.class)
class OrderControllerTest {

    @Autowired WebTestClient webClient;
    @MockitoBean OrderService orderService;

    @Test
    void getOrder_existingId_returns200() {
        when(orderService.findById("1")).thenReturn(Mono.just(new Order("1", "alice")));

        webClient.get().uri("/api/orders/1")
                 .exchange()
                 .expectStatus().isOk()
                 .expectBody()
                 .jsonPath("$.id").isEqualTo("1")
                 .jsonPath("$.customer").isEqualTo("alice");
    }

    @Test
    void streamOrders_returnsFlux() {
        when(orderService.streamAll()).thenReturn(
            Flux.just(new Order("1","alice"), new Order("2","bob")));

        webClient.get().uri("/api/orders/stream")
                 .accept(MediaType.TEXT_EVENT_STREAM)
                 .exchange()
                 .expectStatus().isOk()
                 .expectBodyList(Order.class)
                 .hasSize(2);
    }
}
```

Key difference from `@WebMvcTest`: `WebTestClient` returns reactive assertions (`.expectStatus()`, `.expectBody()`) instead of MockMvc's `.andExpect()`.

## 4. Diagram

<svg viewBox="0 0 680 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@WebFluxTest loads reactive controllers and WebTestClient; service layer is a Mockito mock returning Mono/Flux; no blocking IO, no JPA or Tomcat">
  <!-- WebTestClient -->
  <rect x="10" y="72" width="130" height="52" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/>
  <text x="75" y="93" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">WebTestClient</text>
  <text x="75" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.get().uri(...)</text>
  <text x="75" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.expectStatus().isOk()</text>

  <!-- Arrow -->
  <line x1="142" y1="98" x2="200" y2="98" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#wfa)"/>

  <!-- Reactive web slice -->
  <rect x="205" y="25" width="280" height="140" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="345" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@WebFluxTest Slice</text>
  <rect x="218" y="58" width="254" height="26" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="345" y="75" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">ReactiveSecurityFilterChain (if configured)</text>
  <rect x="218" y="91" width="254" height="26" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="345" y="108" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">DispatcherHandler + @RestController (reactive)</text>
  <rect x="218" y="124" width="254" height="26" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="345" y="141" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">@ControllerAdvice  WebFilter  WebFluxConfigurer</text>

  <!-- Mock service -->
  <line x1="487" y1="98" x2="540" y2="98" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#wfb)"/>
  <rect x="545" y="65" width="125" height="65" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="607" y="87" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">@MockitoBean</text>
  <text x="607" y="102" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="607" y="116" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">returns Mono/Flux</text>
  <text x="607" y="128" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">stubs</text>

  <text x="345" y="178" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">✗ Tomcat, JPA, DataSource, Kafka, Redis excluded; no blocking IO</text>

  <defs>
    <marker id="wfa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="wfb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`WebTestClient` sends requests into the reactive slice; services return `Mono`/`Flux` stubs; no Tomcat or JPA runs.

## 5. Runnable example

```java
// WebFluxTestDemo.java — simulates @WebFluxTest WebTestClient assertion patterns
// How to run: java WebFluxTestDemo.java  (JDK 17+, no dependencies)
// Real use: @WebFluxTest(OrderController.class) + @Autowired WebTestClient

import java.util.*;

public class WebFluxTestDemo {

    record Order(String id, String customer, double total) {}

    // Simulate Mono/Flux (simplified reactive types)
    static class Mono<T> {
        private final T value;
        private final boolean empty;
        Mono(T value) { this.value = value; this.empty = false; }
        static <T> Mono<T> just(T v)  { return new Mono<>(v); }
        static <T> Mono<T> empty()    { Mono<T> m = new Mono<>(null); return m; }
        T block() { return value; }
        boolean isEmpty() { return empty || value == null; }
    }

    static class Flux<T> {
        private final List<T> items;
        Flux(List<T> items) { this.items = items; }
        static <T> Flux<T> just(@SuppressWarnings("unchecked") T... items) { return new Flux<>(List.of(items)); }
        List<T> collectList() { return items; }
        int count() { return items.size(); }
    }

    // Mock reactive service
    static class MockOrderService {
        private final Map<String, Order> stubs = new LinkedHashMap<>();
        private final List<Order>        all   = new ArrayList<>();
        private final List<String>       calls = new ArrayList<>();

        void stub(Order o) { stubs.put(o.id(), o); all.add(o); }
        Mono<Order> findById(String id) { calls.add("findById:" + id); return Mono.just(stubs.get(id)); }
        Flux<Order> findAll()           { calls.add("findAll"); return new Flux<>(all); }
        void verify(String call) {
            if (!calls.contains(call)) throw new AssertionError("Expected: " + call + " got: " + calls);
            System.out.println("  ✓ verify: " + call);
        }
    }

    // Simulated WebTestClient response
    record Response(int status, String body, List<?> items) {
        String jsonPath(String path) {
            // naive extraction: $.id → look for "id":"value"
            String key = path.replace("$.", "");
            var m = java.util.regex.Pattern.compile("\"" + key + "\":\"?([^,}\"]+)\"?").matcher(body);
            return m.find() ? m.group(1) : null;
        }
    }

    // Simulate reactive controller dispatch
    static Response dispatch(String method, String path, MockOrderService svc) {
        if ("GET".equals(method) && path.startsWith("/api/orders/stream")) {
            Flux<Order> flux = svc.findAll();
            var items = flux.collectList();
            StringBuilder sb = new StringBuilder("[");
            items.forEach(o -> sb.append(String.format("{\"id\":\"%s\",\"customer\":\"%s\"},", o.id(), o.customer())));
            if (!items.isEmpty()) sb.setLength(sb.length() - 1);
            sb.append("]");
            return new Response(200, sb.toString(), items);
        }
        if ("GET".equals(method) && path.startsWith("/api/orders/")) {
            String id = path.substring("/api/orders/".length());
            Mono<Order> mono = svc.findById(id);
            if (mono.isEmpty()) return new Response(404, "{\"error\":\"not found\"}", List.of());
            Order o = mono.block();
            return new Response(200,
                String.format("{\"id\":\"%s\",\"customer\":\"%s\",\"total\":%.2f}", o.id(), o.customer(), o.total()),
                List.of(o));
        }
        return new Response(404, "{}", List.of());
    }

    static void expectStatus(Response r, int expected, String label) {
        if (r.status() != expected)
            throw new AssertionError(label + ": expected " + expected + " got " + r.status());
        System.out.println("  ✓ " + label + " [" + r.status() + "]");
    }

    static void expectJsonPath(Response r, String path, String expected, String label) {
        String val = r.jsonPath(path);
        if (!expected.equals(val))
            throw new AssertionError(label + ": " + path + " = " + val + " expected " + expected);
        System.out.println("  ✓ " + label + " [" + path + " = " + val + "]");
    }

    public static void main(String[] args) {
        System.out.println("=== @WebFluxTest / WebTestClient Demo ===\n");

        MockOrderService svc = new MockOrderService();
        svc.stub(new Order("1", "alice", 99.99));
        svc.stub(new Order("2", "bob",   149.50));

        // Test 1: GET single order (Mono)
        System.out.println("--- Test 1: GET /api/orders/1 (Mono) ---");
        Response r1 = dispatch("GET", "/api/orders/1", svc);
        expectStatus(r1, 200, "status 200");
        expectJsonPath(r1, "$.id",       "1",     "id");
        expectJsonPath(r1, "$.customer", "alice",  "customer");
        svc.verify("findById:1");

        // Test 2: GET not found
        System.out.println("\n--- Test 2: GET /api/orders/999 (empty Mono → 404) ---");
        Response r2 = dispatch("GET", "/api/orders/999", svc);
        expectStatus(r2, 404, "status 404");

        // Test 3: SSE stream (Flux)
        System.out.println("\n--- Test 3: GET /api/orders/stream (Flux) ---");
        Response r3 = dispatch("GET", "/api/orders/stream", svc);
        expectStatus(r3, 200, "status 200");
        if (r3.items().size() != 2) throw new AssertionError("Expected 2 items, got " + r3.items().size());
        System.out.println("  ✓ stream has 2 orders");
        svc.verify("findAll");

        System.out.println("\n--- Real @WebFluxTest patterns ---");
        System.out.println("""
@WebFluxTest(OrderController.class)
class OrderControllerTest {
    @Autowired WebTestClient webClient;
    @MockitoBean OrderService orderService;

    @Test void getOrder() {
        when(orderService.findById("1"))
            .thenReturn(Mono.just(new Order("1","alice",99.99)));
        webClient.get().uri("/api/orders/1")
            .exchange()
            .expectStatus().isOk()
            .expectBody()
            .jsonPath("$.id").isEqualTo("1");
    }

    @Test void streamOrders() {
        when(orderService.streamAll())
            .thenReturn(Flux.just(new Order("1","alice"), new Order("2","bob")));
        webClient.get().uri("/api/orders/stream")
            .accept(MediaType.TEXT_EVENT_STREAM)
            .exchange()
            .expectStatus().isOk()
            .expectBodyList(Order.class).hasSize(2);
    }
}""");

        System.out.println("\nAll tests passed.");
    }
}
```

**How to run:** `java WebFluxTestDemo.java`

## 6. Walkthrough

- **Mono stub** (test 1): `Mono.just(order)` simulates `when(service.findById("1")).thenReturn(Mono.just(...))`. The reactive controller subscribes to it and serializes the result. `WebTestClient.expectBody().jsonPath(...)` asserts on the JSON.
- **Empty Mono → 404** (test 2): no stub for `"999"` returns `Mono.empty()`. The controller maps that to `404 Not Found` — typically via `.switchIfEmpty(Mono.error(new ResponseStatusException(NOT_FOUND)))`.
- **Flux stream** (test 3): `findAll()` returns `Flux.just(...)`. For SSE endpoints (`text/event-stream`), `WebTestClient.expectBodyList(Order.class).hasSize(2)` collects the flux and asserts count.
- The real patterns snippet shows `WebTestClient`'s fluent assertion chain — each method in the chain is reactive-safe and returns the next assertion step.

## 7. Gotchas & takeaways

> `@WebFluxTest` does **not start a real server** — `WebTestClient` binds directly to the `DispatcherHandler` via `WebTestClient.bindToApplicationContext(ctx)`. If your test requires real TCP (e.g., WebSocket handshake), use `@SpringBootTest(webEnvironment = RANDOM_PORT)` with a `WebTestClient` bound to the server URL.

> Service stubs must return reactive types (`Mono<T>`, `Flux<T>`). Returning a raw object (like `when(...).thenReturn(order)` instead of `Mono.just(order)`) will cause a `ClassCastException` at runtime. Always match the reactive return type of the service method.

- `WebTestClient` assertion chains are blocking under the hood — the test thread waits for the reactive pipeline to complete before asserting.
- Security in WebFlux tests: use `@WithMockUser` (works with Spring Security reactive) or configure `SecurityWebFilterChain` mocks.
- `expectBody(String.class).consumeWith(body -> ...)` is useful for asserting raw response bodies (e.g., SSE event format).
- For controller advice (`@ExceptionHandler` methods), `@WebFluxTest` includes them automatically — test error handling the same way as success paths.
