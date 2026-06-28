---
card: spring-boot
gi: 205
slug: springboottest
title: "@SpringBootTest"
---

## 1. What it is

`@SpringBootTest` is the main annotation for Spring Boot integration tests. It loads the **full application context** — all beans, auto-configurations, and configuration properties — in the test JVM. This contrasts with test slices (`@WebMvcTest`, `@DataJpaTest`, etc.) which load only a subset. `@SpringBootTest` is the right choice when you want to test the application as a whole, end-to-end within the JVM.

## 2. Why & when

Use `@SpringBootTest` when:
- You need multiple layers working together (controller → service → repository).
- You're testing application startup itself (e.g., all beans wire up without errors).
- Your integration test needs the full auto-configuration (Flyway, security, metrics).
- You're testing with a real (or Testcontainers) database and want the full JPA stack.

Avoid it for unit tests (no Spring context needed) or fast slice tests (only a thin layer needed). Full context loads are slow — reserve them for integration test suites.

## 3. Core concept

```java
@SpringBootTest
class OrderServiceIT {

    @Autowired OrderService orderService;

    @Test void createOrder_persistsToDatabase() {
        Order o = orderService.create(new OrderRequest("alice", 99.99));
        assertThat(o.id()).isNotNull();
    }
}
```

**Key attributes:**

| Attribute | Purpose |
|---|---|
| `webEnvironment` | `MOCK` (default), `RANDOM_PORT`, `DEFINED_PORT`, `NONE` |
| `classes` | Specific configuration classes (defaults to `@SpringBootConfiguration` scan) |
| `properties` | Inline property overrides: `"server.port=0"` |
| `args` | Simulate command-line `ApplicationArguments` |

**With a real HTTP server:**
```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
class OrderControllerIT {

    @Autowired TestRestTemplate restTemplate;

    @LocalServerPort int port;

    @Test void getOrder_returns200() {
        ResponseEntity<Order> resp = restTemplate.getForEntity(
            "http://localhost:" + port + "/api/orders/1", Order.class);
        assertThat(resp.getStatusCode()).isEqualTo(HttpStatus.OK);
    }
}
```

## 4. Diagram

<svg viewBox="0 0 680 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@SpringBootTest loads the full application context with all beans; test can inject any bean; webEnvironment controls whether a real HTTP server starts">
  <!-- Test class -->
  <rect x="10" y="75" width="145" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="82" y="96" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@SpringBootTest</text>
  <text x="82" y="112" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Test class</text>
  <text x="82" y="125" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@Autowired any bean</text>

  <!-- Arrow to context -->
  <line x1="157" y1="102" x2="215" y2="102" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sba)"/>

  <!-- Full context -->
  <rect x="220" y="45" width="280" height="120" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="360" y="68" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Full Application Context</text>
  <text x="360" y="87" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">All @Component, @Service, @Repository, @Controller</text>
  <text x="360" y="102" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">All AutoConfigurations (JPA, Security, Actuator...)</text>
  <text x="360" y="117" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">application.properties + test overrides</text>
  <text x="360" y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@TestConfiguration / @MockitoBean replacements</text>
  <text x="360" y="147" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Flyway migrations, cache warming, etc.</text>

  <!-- webEnvironment options -->
  <rect x="515" y="30" width="155" height="140" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="592" y="52" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">webEnvironment=</text>
  <text x="592" y="70" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">MOCK (default)</text>
  <text x="592" y="84" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">mock servlet, no port</text>
  <text x="592" y="102" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">RANDOM_PORT</text>
  <text x="592" y="116" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">real server, random port</text>
  <text x="592" y="134" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">DEFINED_PORT</text>
  <text x="592" y="148" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">real server, server.port</text>
  <text x="592" y="166" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">NONE</text>

  <line x1="502" y1="102" x2="513" y2="102" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#sbb)"/>

  <defs>
    <marker id="sba" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="sbb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`@SpringBootTest` starts the full Spring context; `webEnvironment` controls whether a real HTTP server is started and on which port.

## 5. Runnable example

```java
// SpringBootTestDemo.java — simulates full application context loading and test scenarios
// How to run: java SpringBootTestDemo.java  (JDK 17+, no dependencies)
// Real use: annotate test class with @SpringBootTest; JUnit 5 runs it via SpringExtension

import java.util.*;

public class SpringBootTestDemo {

    // Simulates the application context (a simplified container)
    static class ApplicationContext {
        private final Map<Class<?>, Object> beans = new HashMap<>();
        private final Properties properties  = new Properties();

        ApplicationContext(Properties overrides) {
            // Simulate auto-configuration: wire up layers
            this.properties.setProperty("spring.datasource.url", "jdbc:h2:mem:testdb");
            this.properties.setProperty("server.port", "8080");
            this.properties.putAll(overrides);

            // Register "beans" (simplified)
            OrderRepository repo = new OrderRepository();
            OrderService     svc  = new OrderService(repo);
            OrderController  ctrl = new OrderController(svc);

            beans.put(OrderRepository.class, repo);
            beans.put(OrderService.class,    svc);
            beans.put(OrderController.class, ctrl);
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) { return (T) beans.get(type); }
        String property(String key)  { return properties.getProperty(key); }
    }

    // Application layers (would be @Repository, @Service, @RestController in real app)
    static class OrderRepository {
        private final Map<String, Double> db = new LinkedHashMap<>();
        String save(String customer, double total) {
            String id = "ORD-" + (db.size() + 1);
            db.put(id, total);
            return id;
        }
        boolean exists(String id) { return db.containsKey(id); }
        int count() { return db.size(); }
    }

    static class OrderService {
        private final OrderRepository repo;
        OrderService(OrderRepository repo) { this.repo = repo; }
        String createOrder(String customer, double total) { return repo.save(customer, total); }
        boolean orderExists(String id)                    { return repo.exists(id); }
    }

    static class OrderController {
        private final OrderService svc;
        OrderController(OrderService svc) { this.svc = svc; }
        record Response(int status, String body) {}
        Response postOrder(String customer, double total) {
            String id = svc.createOrder(customer, total);
            return new Response(201, "{\"id\":\"" + id + "\"}");
        }
        Response getOrder(String id) {
            return svc.orderExists(id) ? new Response(200, "{\"id\":\"" + id + "\"}")
                                       : new Response(404, "{\"error\":\"not found\"}");
        }
    }

    // Test assertions
    static void expect(boolean condition, String message) {
        if (!condition) throw new AssertionError("FAIL: " + message);
        System.out.println("  ✓ " + message);
    }

    public static void main(String[] args) {
        System.out.println("=== @SpringBootTest Context Simulation ===\n");

        // --- Test 1: basic context load ---
        System.out.println("Test: context loads and wires beans");
        ApplicationContext ctx = new ApplicationContext(new Properties());
        expect(ctx.getBean(OrderService.class) != null, "OrderService autowired");
        expect(ctx.getBean(OrderController.class) != null, "OrderController autowired");
        expect("jdbc:h2:mem:testdb".equals(ctx.property("spring.datasource.url")),
               "datasource auto-configured");

        // --- Test 2: full integration (controller → service → repository) ---
        System.out.println("\nTest: full integration (controller → service → repository)");
        OrderController ctrl = ctx.getBean(OrderController.class);
        OrderController.Response resp = ctrl.postOrder("alice", 99.99);
        expect(resp.status() == 201,                   "POST /orders returns 201");
        expect(resp.body().contains("ORD-1"),          "response contains order id");

        OrderController.Response getResp = ctrl.getOrder("ORD-1");
        expect(getResp.status() == 200,                "GET /orders/ORD-1 returns 200");
        OrderController.Response notFound = ctrl.getOrder("ORD-999");
        expect(notFound.status() == 404,               "GET /orders/ORD-999 returns 404");

        // --- Test 3: property overrides ---
        System.out.println("\nTest: property overrides");
        Properties overrides = new Properties();
        overrides.setProperty("server.port", "9090");
        ApplicationContext ctx2 = new ApplicationContext(overrides);
        expect("9090".equals(ctx2.property("server.port")), "server.port overridden to 9090");

        // --- Summary: real @SpringBootTest patterns ---
        System.out.println("\n--- Real @SpringBootTest patterns ---");
        System.out.println("""
@SpringBootTest
class OrderControllerIT {
    @Autowired MockMvc mockMvc;

    @Test void createOrder() throws Exception {
        mockMvc.perform(post("/api/orders")
                .contentType(APPLICATION_JSON)
                .content("{\\"customer\\":\\"alice\\",\\"total\\":99.99}"))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id").isNotEmpty());
    }
}

// With real HTTP server:
@SpringBootTest(webEnvironment = RANDOM_PORT)
class OrderControllerHttpIT {
    @Autowired TestRestTemplate rest;
    @LocalServerPort int port;

    @Test void createOrder_http() {
        var resp = rest.postForEntity("/api/orders", req, Order.class);
        assertThat(resp.getStatusCode()).isEqualTo(CREATED);
    }
}""");

        System.out.println("\nAll tests passed.");
    }
}
```

**How to run:** `java SpringBootTestDemo.java`

## 6. Walkthrough

- **Context loads and wires beans**: simulates what Spring Boot does at test startup — instantiates all auto-configurations and wires dependencies. If a bean can't be created (missing datasource, typo in `@Value`), the test fails here.
- **Full integration test**: the controller calls the service which calls the repository in a single test. All three layers are exercised together, unlike unit tests where each layer is tested in isolation with mocks.
- **Property overrides**: `@SpringBootTest(properties = "server.port=9090")` overrides `application.properties` values. In the simulation, the `overrides` map fills this role. Useful for testing different configurations without separate property files.
- The real test snippet shows `MockMvc` (webEnvironment=MOCK) and `TestRestTemplate` (webEnvironment=RANDOM_PORT) usage — both are auto-configured by `@SpringBootTest`.

## 7. Gotchas & takeaways

> `@SpringBootTest` context is **cached** between tests in the same test suite. If two test classes use the same context configuration, Spring reuses the loaded context rather than starting a new one. Anything that modifies context state (dirty beans, DB writes) can affect subsequent tests. Use `@DirtiesContext` to force a reload, but use it sparingly — it's expensive.

> Tests annotated with `@SpringBootTest` without `webEnvironment` default to `MOCK` — no real HTTP server starts. Use `TestRestTemplate` only with `RANDOM_PORT` or `DEFINED_PORT`; with `MOCK`, use `MockMvc` or `MockMvcTester` instead.

- `@SpringBootTest` finds `@SpringBootApplication` (or `@SpringBootConfiguration`) automatically by scanning up from the test class package.
- Use `@SpringBootTest(classes = {MyApp.class, TestConfig.class})` to load a specific root configuration.
- `@SpringBootTest(args = "--debug")` simulates passing command-line arguments to the application.
- Combine with `@ActiveProfiles("test")` to activate a test-specific profile and its properties.
