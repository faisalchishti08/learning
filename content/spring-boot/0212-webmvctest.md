---
card: spring-boot
gi: 212
slug: webmvctest
title: "@WebMvcTest"
---

## 1. What it is

`@WebMvcTest` is a Spring Boot test slice that loads **only the web layer** of your application. It configures a mock servlet environment with `MockMvc`, loads `@Controller`, `@RestController`, `@ControllerAdvice`, `Filter`, `WebMvcConfigurer`, and `HandlerMethodArgumentResolver` beans, but does NOT load `@Service`, `@Repository`, or JPA auto-configuration. It is the standard tool for testing controllers in isolation.

## 2. Why & when

Use `@WebMvcTest` to test:
- HTTP request mappings (URL, method, content type).
- Request parameter binding and `@Valid` bean validation.
- JSON serialization/deserialization of request/response bodies.
- Response status codes and headers.
- `@ExceptionHandler` and `@ControllerAdvice` error handling.
- Spring Security rules (with `@WithMockUser`).

Avoid it when you need end-to-end integration through all layers — use `@SpringBootTest` for that. `@WebMvcTest` is **fast** (sub-second startup) and should cover the majority of controller tests.

## 3. Core concept

```java
// Test a specific controller:
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired MockMvc mockMvc;
    @MockitoBean OrderService orderService;   // service layer must be mocked

    @Test
    void getOrder_existingId_returns200() throws Exception {
        when(orderService.findById("1")).thenReturn(new Order("1", "alice", 99.99));

        mockMvc.perform(get("/api/orders/1")
                    .accept(MediaType.APPLICATION_JSON))
               .andExpect(status().isOk())
               .andExpect(jsonPath("$.id").value("1"))
               .andExpect(jsonPath("$.customer").value("alice"))
               .andExpect(jsonPath("$.total").value(99.99));

        verify(orderService).findById("1");
    }

    @Test
    void createOrder_invalidBody_returns400() throws Exception {
        mockMvc.perform(post("/api/orders")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content("{\"customer\":\"\",\"total\":-1}"))   // invalid
               .andExpect(status().isBadRequest());
    }
}
```

**With Spring Security:**
```java
@WithMockUser(roles = "ADMIN")
@Test
void deleteOrder_asAdmin_returns204() throws Exception {
    mockMvc.perform(delete("/api/orders/1"))
           .andExpect(status().isNoContent());
}
```

## 4. Diagram

<svg viewBox="0 0 680 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@WebMvcTest loads controllers, MockMvc, ControllerAdvice, and security filter; service layer beans are provided as mocks; no JPA or DataSource is started">
  <!-- MockMvc (test) -->
  <rect x="10" y="75" width="115" height="55" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="62" y="97" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">MockMvc</text>
  <text x="62" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">perform(get(...))</text>
  <text x="62" y="124" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">andExpect(...)</text>

  <!-- Arrow -->
  <line x1="127" y1="102" x2="185" y2="102" stroke="#6db33f" stroke-width="1.5" marker-end="url(#wma)"/>

  <!-- Web layer slice -->
  <rect x="190" y="20" width="280" height="155" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="42" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">@WebMvcTest Slice</text>
  <rect x="203" y="55" width="255" height="28" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="73" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Security Filter Chain (if configured)</text>
  <rect x="203" y="91" width="255" height="28" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="109" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">DispatcherServlet + OrderController</text>
  <rect x="203" y="127" width="255" height="28" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="145" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@ControllerAdvice (GlobalExceptionHandler)</text>

  <!-- Mock service -->
  <line x1="472" y1="102" x2="540" y2="102" stroke="#6db33f" stroke-width="1.5" marker-end="url(#wmb)"/>
  <rect x="545" y="75" width="125" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="607" y="97" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">@MockitoBean</text>
  <text x="607" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">OrderService (mock)</text>
  <text x="607" y="124" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">no DB, no real logic</text>

  <!-- Excluded -->
  <text x="330" y="188" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">✗ JPA, DataSource, Kafka, Redis, Actuator — excluded from slice</text>

  <defs>
    <marker id="wma" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="wmb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`MockMvc` dispatches requests directly to the slice; the service is a Mockito mock; no database or external infrastructure is started.

## 5. Runnable example

```java
// WebMvcTestDemo.java — simulates @WebMvcTest request dispatch and assertion patterns
// How to run: java WebMvcTestDemo.java  (JDK 17+, no dependencies)
// Real use: @WebMvcTest(OrderController.class) + @Autowired MockMvc

import java.util.*;

public class WebMvcTestDemo {

    // Domain
    record Order(String id, String customer, double total) {}

    // Mock service (simulates @MockitoBean)
    static class MockOrderService {
        private final Map<String, Order> stubs = new LinkedHashMap<>();
        private final List<String>       calls = new ArrayList<>();

        void stubFindById(String id, Order order) { stubs.put(id, order); }

        Order findById(String id) {
            calls.add("findById:" + id);
            return stubs.get(id);
        }

        String save(String customer, double total) {
            String id = "ORD-" + (stubs.size() + 1);
            Order o = new Order(id, customer, total);
            stubs.put(id, o);
            calls.add("save:" + customer + ":" + total);
            return id;
        }

        void verify(String expectedCall) {
            if (!calls.contains(expectedCall))
                throw new AssertionError("Expected: " + expectedCall + " got: " + calls);
            System.out.println("  ✓ verify: " + expectedCall);
        }
    }

    // Simplified request/response (simulates MockMvc)
    record MockRequest(String method, String path, String body, String accept, String contentType) {}
    record MockResponse(int status, String body) {}

    // Controller logic (what @WebMvcTest would exercise)
    static MockResponse dispatch(MockRequest req, MockOrderService svc) {
        // Routing
        if ("GET".equals(req.method()) && req.path().startsWith("/api/orders/")) {
            String id = req.path().substring("/api/orders/".length());
            Order o = svc.findById(id);
            if (o == null) return new MockResponse(404, "{\"error\":\"Order not found\"}");
            return new MockResponse(200,
                    String.format("{\"id\":\"%s\",\"customer\":\"%s\",\"total\":%.2f}",
                            o.id(), o.customer(), o.total()));
        }
        if ("POST".equals(req.method()) && "/api/orders".equals(req.path())) {
            // Simulate @Valid: customer required, total > 0
            if (req.body() == null || req.body().contains("\"customer\":\"\"") ||
                    req.body().contains("\"total\":-")) {
                return new MockResponse(400, "{\"error\":\"Validation failed\"}");
            }
            // Simplified parse
            String customer = req.body().replaceAll(".*\"customer\":\"([^\"]+)\".*", "$1");
            double total    = Double.parseDouble(req.body().replaceAll(".*\"total\":(\\d+\\.?\\d*).*", "$1"));
            String id = svc.save(customer, total);
            return new MockResponse(201, "{\"id\":\"" + id + "\"}");
        }
        if ("DELETE".equals(req.method()) && req.path().startsWith("/api/orders/")) {
            return new MockResponse(204, "");
        }
        return new MockResponse(404, "{}");
    }

    static void assertStatus(MockResponse resp, int expected, String label) {
        if (resp.status() != expected)
            throw new AssertionError(label + ": expected " + expected + " got " + resp.status());
        System.out.println("  ✓ " + label + " [" + resp.status() + "]");
    }

    static void assertBodyContains(MockResponse resp, String substring, String label) {
        if (!resp.body().contains(substring))
            throw new AssertionError(label + ": body '" + resp.body() + "' missing '" + substring + "'");
        System.out.println("  ✓ " + label);
    }

    public static void main(String[] args) {
        System.out.println("=== @WebMvcTest Demo ===\n");

        MockOrderService svc = new MockOrderService();
        svc.stubFindById("1", new Order("1", "alice", 99.99));

        // Test 1: GET existing order
        System.out.println("--- Test 1: GET /api/orders/1 (exists) ---");
        var r1 = dispatch(new MockRequest("GET", "/api/orders/1", null, "application/json", null), svc);
        assertStatus(r1, 200, "status 200");
        assertBodyContains(r1, "\"id\":\"1\"",       "id in body");
        assertBodyContains(r1, "\"customer\":\"alice\"", "customer in body");
        assertBodyContains(r1, "99.99",              "total in body");
        svc.verify("findById:1");

        // Test 2: GET non-existent
        System.out.println("\n--- Test 2: GET /api/orders/999 (not found) ---");
        var r2 = dispatch(new MockRequest("GET", "/api/orders/999", null, "application/json", null), svc);
        assertStatus(r2, 404, "status 404");
        assertBodyContains(r2, "not found", "error message");

        // Test 3: POST valid order
        System.out.println("\n--- Test 3: POST /api/orders (valid) ---");
        var r3 = dispatch(new MockRequest("POST", "/api/orders",
                "{\"customer\":\"bob\",\"total\":149.50}", "application/json", "application/json"), svc);
        assertStatus(r3, 201, "status 201");
        assertBodyContains(r3, "\"id\":", "id returned");
        svc.verify("save:bob:149.5");

        // Test 4: POST invalid (validation failure)
        System.out.println("\n--- Test 4: POST /api/orders (invalid body) ---");
        var r4 = dispatch(new MockRequest("POST", "/api/orders",
                "{\"customer\":\"\",\"total\":-1}", "application/json", "application/json"), svc);
        assertStatus(r4, 400, "status 400 on validation error");
        assertBodyContains(r4, "Validation", "validation error message");

        // Test 5: DELETE
        System.out.println("\n--- Test 5: DELETE /api/orders/1 ---");
        var r5 = dispatch(new MockRequest("DELETE", "/api/orders/1", null, null, null), svc);
        assertStatus(r5, 204, "status 204");

        System.out.println("\n--- Real @WebMvcTest patterns ---");
        System.out.println("""
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired MockMvc mockMvc;
    @MockitoBean OrderService orderService;

    @Test void get_existing() throws Exception {
        when(orderService.findById("1"))
            .thenReturn(new Order("1","alice",99.99));
        mockMvc.perform(get("/api/orders/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.customer").value("alice"));
    }

    @Test void post_invalid() throws Exception {
        mockMvc.perform(post("/api/orders")
            .contentType(APPLICATION_JSON)
            .content("{\\"customer\\":\\"\\",\\"total\\":-1}"))
            .andExpect(status().isBadRequest());
    }
}""");

        System.out.println("\nAll tests passed.");
    }
}
```

**How to run:** `java WebMvcTestDemo.java`

## 6. Walkthrough

- **Test 1 (GET existing)**: stubs `findById("1")` to return an `Order`. MockMvc dispatches `GET /api/orders/1`, asserts `200` status and JSON fields. Then `verify(findById:1)` confirms the service was called.
- **Test 2 (GET 404)**: no stub for `"999"` → service returns `null` → controller returns `404`. Tests error-path handling without any special setup.
- **Test 3 (POST valid)**: submits a valid JSON body. Controller parses, calls `save`, returns `201` with the new ID.
- **Test 4 (POST invalid)**: empty customer and negative total → validation fails → `400`. This tests `@Valid` / `@Validated` behavior, which is part of the web layer and exercised by `@WebMvcTest`.
- **Test 5 (DELETE)**: `204 No Content` on deletion. No service call needed here — tests the route exists and returns the right status.

## 7. Gotchas & takeaways

> `@WebMvcTest` loads **all controllers** by default unless you specify `@WebMvcTest(OrderController.class)`. Always specify the controller class to keep the slice minimal and avoid loading unrelated controllers that might have unsatisfied dependencies.

> If your controller has a `@Secured` or Spring Security annotation, tests will get `403` unless you provide `@WithMockUser` or configure security in the test. `@WebMvcTest` includes `SecurityAutoConfiguration` by default — it doesn't skip security.

- `jsonPath()` uses the Hamcrest/AssertJ DSL: `jsonPath("$.items[0].name").value("Widget")`.
- `@WebMvcTest` auto-configures `MockMvc` — no `@AutoConfigureMockMvc` needed (unlike `@SpringBootTest`).
- Test `@ControllerAdvice` by making the controller throw an exception and asserting on the error response body.
- `content().json(expectedJson, true)` performs strict JSON equality check (uses JSONassert internally).
