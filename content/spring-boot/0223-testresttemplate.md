---
card: spring-boot
gi: 223
slug: testresttemplate
title: "TestRestTemplate"
---

## 1. What it is

`TestRestTemplate` is a Spring Boot test utility that wraps `RestTemplate` with testing-friendly defaults. It is auto-configured by `@SpringBootTest` when the web environment is `RANDOM_PORT` or `DEFINED_PORT`. Unlike plain `RestTemplate`, `TestRestTemplate` does not throw exceptions on 4xx/5xx responses — it returns the `ResponseEntity` with the error status code, making assertions on error paths straightforward.

## 2. Why & when

Use `TestRestTemplate` for **full-stack integration tests** against a real running embedded server:
- You need to test the entire HTTP request path — filters, interceptors, security, serialization, controller, service, repository.
- You want to verify error handling (404, 400, 500) without try/catch.
- You're testing redirects or cookie-based auth where `MockMvc` is insufficient.
- You want HTTP Basic auth support out of the box (via `withBasicAuth()`).

Prefer `MockMvc` for unit-testing controllers in isolation (`@WebMvcTest`). Use `TestRestTemplate` when the embedded server must run.

## 3. Core concept

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
class OrderIntegrationTest {

    @Autowired TestRestTemplate restTemplate;
    @LocalServerPort int port;

    @Test
    void getOrder_returnsCorrectBody() {
        ResponseEntity<Order> resp = restTemplate.getForEntity("/orders/1", Order.class);

        assertThat(resp.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(resp.getBody().customer()).isEqualTo("alice");
    }

    @Test
    void getOrder_notFound_returns404() {
        // TestRestTemplate does NOT throw on 404 — returns ResponseEntity with 404 status
        ResponseEntity<String> resp = restTemplate.getForEntity("/orders/999", String.class);
        assertThat(resp.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
    }

    @Test
    void createOrder_secured_withBasicAuth() {
        ResponseEntity<Order> resp = restTemplate
            .withBasicAuth("admin", "password")
            .postForEntity("/orders", new OrderRequest("alice", 99.99), Order.class);

        assertThat(resp.getStatusCode()).isEqualTo(HttpStatus.CREATED);
    }
}
```

The base URL is automatically set to `http://localhost:{random-port}` — relative URLs like `/orders/1` work without specifying the host.

## 4. Diagram

<svg viewBox="0 0 680 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="TestRestTemplate wraps RestTemplate with no-throw 4xx/5xx behavior; @SpringBootTest starts embedded server on random port; TestRestTemplate sends real HTTP requests and returns ResponseEntity for assertion">
  <!-- Test -->
  <rect x="10" y="55" width="145" height="80" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="82" y="77" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@SpringBootTest</text>
  <text x="82" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">RANDOM_PORT</text>
  <text x="82" y="107" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">TestRestTemplate</text>
  <text x="82" y="121" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">  .getForEntity("/orders/1")</text>
  <text x="82" y="134" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">  → ResponseEntity (no throw)</text>

  <!-- Real HTTP -->
  <line x1="157" y1="95" x2="205" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#trt_a)"/>
  <text x="180" y="87" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">HTTP</text>

  <!-- Embedded Server -->
  <rect x="210" y="30" width="255" height="135" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="337" y="52" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Embedded Server (Tomcat)</text>
  <rect x="222" y="63" width="230" height="25" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="337" y="80" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Filters / Security / Interceptors</text>
  <rect x="222" y="95" width="230" height="25" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="337" y="112" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@RestController</text>
  <rect x="222" y="127" width="230" height="25" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="337" y="144" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Service → @Repository</text>

  <!-- Behavior box -->
  <rect x="480" y="40" width="190" height="115" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="575" y="62" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif" font-weight="bold">TestRestTemplate behavior</text>
  <text x="575" y="80" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">✓ No throw on 4xx / 5xx</text>
  <text x="575" y="95" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">✓ Returns ResponseEntity</text>
  <text x="575" y="110" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">✓ withBasicAuth(user, pwd)</text>
  <text x="575" y="125" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">✓ Follows redirects</text>
  <text x="575" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">✓ Cookie support</text>

  <text x="340" y="178" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Real HTTP through full stack — no mocking of web layer</text>

  <defs>
    <marker id="trt_a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

`TestRestTemplate` sends real HTTP to the embedded server; the full stack (filters, security, controller, service) handles the request; the response is returned as `ResponseEntity` with no exception on error status codes.

## 5. Runnable example

```java
// TestRestTemplateDemo.java — simulates TestRestTemplate patterns
// How to run: java TestRestTemplateDemo.java  (JDK 17+, no dependencies)
// Real use: @SpringBootTest(webEnvironment=RANDOM_PORT) + @Autowired TestRestTemplate

import java.util.*;
import java.util.function.*;

public class TestRestTemplateDemo {

    record Order(String id, String customer, double total) {}
    record OrderRequest(String customer, double total) {}

    // Simulates HTTP status codes
    enum HttpStatus {
        OK(200), CREATED(201), NOT_FOUND(404), UNAUTHORIZED(401),
        BAD_REQUEST(400), INTERNAL_SERVER_ERROR(500);

        final int code;
        HttpStatus(int c) { this.code = c; }
        boolean is2xxSuccessful() { return code >= 200 && code < 300; }
        boolean is4xxClientError() { return code >= 400 && code < 500; }
        boolean is5xxServerError() { return code >= 500; }
    }

    static class ResponseEntity<T> {
        private final T body;
        private final HttpStatus status;
        ResponseEntity(T body, HttpStatus status) { this.body = body; this.status = status; }
        T getBody()            { return body; }
        HttpStatus getStatusCode() { return status; }
        @Override public String toString() { return status.code + " " + body; }
    }

    // Simulates the embedded server (OrderController + OrderService)
    static class EmbeddedServer {
        private final Map<String, Order> db = new LinkedHashMap<>();
        private int seq = 1;
        private final Set<String> authorizedUsers = Set.of("admin:password");

        EmbeddedServer() {
            db.put("1", new Order("1", "alice", 99.99));
            db.put("2", new Order("2", "bob",   149.50));
        }

        <T> ResponseEntity<T> handle(String method, String path, Object body, String authHeader, Class<T> responseType) {
            System.out.println("  [Server] " + method + " " + path + (authHeader != null ? " (auth)" : ""));

            // Security check for POST
            if ("POST".equals(method) && !"/orders/public".equals(path)) {
                if (authHeader == null || !authorizedUsers.contains(decodeBasic(authHeader))) {
                    System.out.println("  [Server] 401 Unauthorized");
                    return cast(new ResponseEntity<>("Unauthorized", HttpStatus.UNAUTHORIZED), responseType);
                }
            }

            if ("GET".equals(method) && path.startsWith("/orders/")) {
                String id = path.substring("/orders/".length());
                Order o = db.get(id);
                if (o == null)
                    return cast(new ResponseEntity<>(null, HttpStatus.NOT_FOUND), responseType);
                return cast(new ResponseEntity<>(o, HttpStatus.OK), responseType);
            }

            if ("GET".equals(method) && "/orders".equals(path)) {
                return cast(new ResponseEntity<>(List.copyOf(db.values()), HttpStatus.OK), responseType);
            }

            if ("POST".equals(method) && "/orders".equals(path) && body instanceof OrderRequest req) {
                String id = String.valueOf(seq++);
                Order created = new Order(id, req.customer(), req.total());
                db.put(id, created);
                return cast(new ResponseEntity<>(created, HttpStatus.CREATED), responseType);
            }

            if ("POST".equals(method) && "/orders/error".equals(path)) {
                return cast(new ResponseEntity<>("Internal error", HttpStatus.INTERNAL_SERVER_ERROR), responseType);
            }

            return cast(new ResponseEntity<>(null, HttpStatus.NOT_FOUND), responseType);
        }

        @SuppressWarnings("unchecked")
        private <T> ResponseEntity<T> cast(ResponseEntity<?> re, Class<T> t) {
            return (ResponseEntity<T>) re;
        }

        private String decodeBasic(String header) {
            String encoded = header.startsWith("Basic ") ? header.substring(6) : header;
            return new String(Base64.getDecoder().decode(encoded));
        }
    }

    // Simulates TestRestTemplate (wraps embedded server; no throw on 4xx/5xx)
    static class TestRestTemplate {
        private final EmbeddedServer server;
        private String authHeader;
        private final int port;

        TestRestTemplate(EmbeddedServer server, int port) { this.server = server; this.port = port; }

        TestRestTemplate withBasicAuth(String user, String password) {
            TestRestTemplate auth = new TestRestTemplate(server, port);
            auth.authHeader = "Basic " + Base64.getEncoder().encodeToString((user + ":" + password).getBytes());
            return auth;
        }

        <T> ResponseEntity<T> getForEntity(String url, Class<T> type) {
            return server.handle("GET", url, null, authHeader, type);
        }

        <T> ResponseEntity<T> postForEntity(String url, Object body, Class<T> type) {
            return server.handle("POST", url, body, authHeader, type);
        }
    }

    static void expect(boolean c, String m) {
        if (!c) throw new AssertionError("FAIL: " + m);
        System.out.println("  ✓ " + m);
    }

    public static void main(String[] args) {
        System.out.println("=== TestRestTemplate Demo ===\n");

        EmbeddedServer embeddedServer = new EmbeddedServer();
        TestRestTemplate restTemplate = new TestRestTemplate(embeddedServer, 8765);

        // Test 1: GET existing order → 200
        System.out.println("--- Test 1: GET /orders/1 → 200 ---");
        ResponseEntity<Order> r1 = restTemplate.getForEntity("/orders/1", Order.class);
        expect(r1.getStatusCode() == HttpStatus.OK,           "status 200");
        expect("alice".equals(r1.getBody().customer()),       "customer = alice");
        expect(r1.getBody().total() == 99.99,                 "total = 99.99");

        // Test 2: GET non-existent → 404 (no exception thrown)
        System.out.println("\n--- Test 2: GET /orders/999 → 404 (no throw) ---");
        ResponseEntity<String> r2 = restTemplate.getForEntity("/orders/999", String.class);
        expect(r2.getStatusCode() == HttpStatus.NOT_FOUND,    "status 404 — no exception");
        expect(r2.getStatusCode().is4xxClientError(),         "is4xxClientError");

        // Test 3: POST without auth → 401
        System.out.println("\n--- Test 3: POST /orders without auth → 401 ---");
        ResponseEntity<String> r3 = restTemplate.postForEntity("/orders",
                new OrderRequest("carol", 200.0), String.class);
        expect(r3.getStatusCode() == HttpStatus.UNAUTHORIZED, "401 without auth");

        // Test 4: POST with basic auth → 201
        System.out.println("\n--- Test 4: POST /orders with basic auth → 201 ---");
        ResponseEntity<Order> r4 = restTemplate
                .withBasicAuth("admin", "password")
                .postForEntity("/orders", new OrderRequest("carol", 200.0), Order.class);
        expect(r4.getStatusCode() == HttpStatus.CREATED,      "201 CREATED");
        expect("carol".equals(r4.getBody().customer()),       "created customer = carol");
        expect(r4.getBody().id() != null,                     "assigned id");

        // Test 5: 500 server error → no exception
        System.out.println("\n--- Test 5: POST /orders/error → 500 (no throw) ---");
        ResponseEntity<String> r5 = restTemplate
                .withBasicAuth("admin", "password")
                .postForEntity("/orders/error", null, String.class);
        expect(r5.getStatusCode() == HttpStatus.INTERNAL_SERVER_ERROR, "500 no exception");
        expect(r5.getStatusCode().is5xxServerError(),         "is5xxServerError");

        System.out.println("\n--- Real @SpringBootTest + TestRestTemplate ---");
        System.out.println("""
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
class OrderIntegrationTest {
    @Autowired TestRestTemplate restTemplate;
    @LocalServerPort int port;   // injected random port

    @Test void getOrder_ok() {
        var resp = restTemplate.getForEntity("/orders/1", Order.class);
        assertThat(resp.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(resp.getBody().customer()).isEqualTo("alice");
    }

    @Test void getOrder_notFound_noThrow() {
        // TestRestTemplate returns 404 ResponseEntity — plain RestTemplate would throw
        var resp = restTemplate.getForEntity("/orders/999", String.class);
        assertThat(resp.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
    }

    @Test void createOrder_withAuth() {
        var resp = restTemplate.withBasicAuth("admin","password")
                               .postForEntity("/orders",
                                   new OrderRequest("carol",200.0), Order.class);
        assertThat(resp.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(resp.getBody().id()).isNotNull();
    }
}""");

        System.out.println("\nAll tests passed.");
    }
}
```

**How to run:** `java TestRestTemplateDemo.java`

## 6. Walkthrough

- **Test 1 (200 OK)**: `getForEntity("/orders/1", Order.class)` sends a real GET to the embedded server. The response is automatically deserialized into `Order`. Status and body are asserted on the `ResponseEntity`.
- **Test 2 (404, no throw)**: `TestRestTemplate` returns a `ResponseEntity` with 404 status. Plain `RestTemplate` would throw `HttpClientErrorException.NotFound`. This is the key behavioral difference — test code doesn't need try/catch for error paths.
- **Test 3 (401 without auth)**: `postForEntity` without credentials returns 401. `TestRestTemplate` does not throw — you assert on `getStatusCode()`.
- **Test 4 (201 with auth)**: `withBasicAuth("admin","password")` returns a new `TestRestTemplate` instance with `Authorization: Basic ...` header on every request. The POST creates a new order and returns 201.
- **Test 5 (500 no throw)**: server returns 500; `TestRestTemplate` returns it as `ResponseEntity` — `is5xxServerError()` confirms. Useful for testing that your error-handling middleware returns the right error structure.

## 7. Gotchas & takeaways

> `TestRestTemplate` uses `RANDOM_PORT` — the embedded server binds to a random port. Inject the port with `@LocalServerPort int port` when you need to construct absolute URLs (e.g., for `WebSocket` connections or OAuth redirect URIs). For relative URLs (`/orders/1`), the base URL is set automatically.

> `withBasicAuth()` returns a **new** `TestRestTemplate` instance. Reassign or chain immediately: `restTemplate.withBasicAuth("u","p").getForEntity(...)`. The original `restTemplate` has no auth header.

- `TestRestTemplate` follows redirects by default (unlike `MockMvc`). Test redirect behavior: `restTemplate.getForEntity("/old-path", String.class)` — status is 200 if redirected to a valid endpoint.
- `exchange()` method allows full control: custom headers, arbitrary HTTP methods, body type: `restTemplate.exchange("/orders/1", HttpMethod.DELETE, HttpEntity.EMPTY, Void.class)`.
- For reactive stacks: use `WebTestClient` instead (auto-configured for `@SpringBootTest` with reactive web).
- `TestRestTemplate` does not follow Spring's `MockMvc` filter chain interceptors — if you need `HandlerInterceptor` testing, use `MockMvc` + `@WebMvcTest`.
- `TestRestTemplate` is not suitable for `WebEnvironment.MOCK` — it requires a real port.
