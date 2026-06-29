---
card: spring-framework
gi: 15
slug: choosing-module-dependencies
title: Choosing module dependencies
---

## 1. What it is

Spring Framework is composed of ~20 modules. Choosing the right set means your project has exactly what it needs and nothing extra. The choice is driven by three questions:

1. **What kind of application?** (Web/REST, batch, event-driven, CLI, library)
2. **Blocking or reactive?** (Servlet-based MVC vs. reactive WebFlux)
3. **What data store?** (JDBC, JPA, R2DBC, no database)

**Common application archetypes and their Spring module sets:**

| Archetype | Modules needed |
|---|---|
| REST API (Servlet) | `spring-webmvc` + `spring-web` |
| REST API (Reactive) | `spring-webflux` |
| Batch processor | `spring-context` + `spring-jdbc` + `spring-tx` |
| Library (no web) | `spring-context` |
| JPA + database | `spring-orm` + `spring-tx` + `spring-jdbc` |
| Message-driven | `spring-jms` or `spring-messaging` |
| AOP-only (cross-cutting) | `spring-aop` + `spring-aspects` |
| WebSocket | `spring-websocket` + `spring-messaging` |

In Spring Boot, these translate directly to starters:

| Module set | Starter |
|---|---|
| `spring-webmvc` + Tomcat + Jackson | `spring-boot-starter-web` |
| `spring-webflux` + Reactor Netty | `spring-boot-starter-webflux` |
| `spring-orm` + Hibernate + HikariCP | `spring-boot-starter-data-jpa` |
| `spring-jdbc` + HikariCP | `spring-boot-starter-jdbc` |
| Batch | `spring-boot-starter-batch` |
| `spring-websocket` | `spring-boot-starter-websocket` |
| Test infrastructure | `spring-boot-starter-test` |

## 2. Why & when

The wrong module choice causes either **excess classpath weight** (pulling in Tomcat for a batch job) or **missing functionality** (forgetting `spring-tx` and wondering why `@Transactional` does nothing).

Rules of thumb:
- **Start minimal.** Add only what a failing compilation or failing test tells you is missing.
- **Let starters choose for you.** If you use Spring Boot, pick the appropriate starter — it has been tested with the correct module set.
- **MVC vs. WebFlux is a hard choice.** You cannot use `spring-webmvc` and `spring-webflux` as the primary web layer in the same application. If you need reactive streaming, choose WebFlux entirely; if you need blocking JDBC/JPA without async complexity, choose MVC.
- **`spring-context` is always the floor.** Every other module depends on it transitively, so it will always be present.

## 3. Core concept

**Decision tree for module selection:**

```
Does the app serve HTTP?
  ├── YES: Is the workload CPU-bound or calls blocking APIs (JDBC, JPA)?
  │          → spring-webmvc  (+ spring-boot-starter-web in Boot)
  │
  ├── YES: Is the workload I/O bound, streaming, or SSE?
  │          → spring-webflux (+ spring-boot-starter-webflux in Boot)
  │
  └── NO: Is it a background processor / CLI?
            → spring-context only

Does it read/write a relational database?
  ├── Using JPA entities (@Entity, @Repository)?
  │          → spring-orm + spring-tx (+ spring-boot-starter-data-jpa)
  │
  ├── Using SQL templates directly?
  │          → spring-jdbc + spring-tx (+ spring-boot-starter-jdbc)
  │
  └── Using reactive database (R2DBC)?
               → spring-r2dbc + reactor-core (+ spring-boot-starter-data-r2dbc)

Does it need AOP (@Transactional, @Async, @Cacheable)?
  → spring-aop (transitive via spring-context — usually implicit)

Does it need WebSocket or STOMP messaging?
  → spring-websocket + spring-messaging

Does it send emails?
  → spring-context-support (JavaMailSender)

Does it need integration with JMS / messaging?
  → spring-jms + a JMS provider (ActiveMQ, RabbitMQ)
```

**The "`spring-webmvc` vs. `spring-webflux`" decision in detail:**

| Criterion | spring-webmvc | spring-webflux |
|---|---|---|
| Thread model | One thread per request | Event loop (Netty) |
| Database | Blocking JDBC / JPA | R2DBC or reactive clients |
| Library ecosystem | Mature — all libraries work | Needs reactive-compatible libs |
| Complexity | Lower | Higher (reactive programming model) |
| Throughput under high concurrency | Scales with thread count | Scales with CPU cores |
| JDK 21 virtual threads | Excellent fit (Boot 3.2) | Not needed — already non-blocking |

For most new REST APIs targeting a relational database: choose `spring-webmvc` + virtual threads (JDK 21 + Boot 3.2). WebFlux is the right choice for streaming, SSE, or when your upstream services are reactive.

## 4. Diagram

<svg viewBox="0 0 700 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Module selection decision tree: HTTP or not, blocking or reactive, database type">
  <defs>
    <marker id="da" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="db" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>

  <!-- Root question -->
  <rect x="250" y="10" width="200" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="350" y="35" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Serve HTTP?</text>

  <!-- YES: blocking -->
  <rect x="30" y="85" width="195" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="127" y="100" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">spring-webmvc</text>
  <text x="127" y="117" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">blocking, Servlet, JDBC/JPA</text>

  <!-- YES: reactive -->
  <rect x="255" y="85" width="195" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="352" y="100" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">spring-webflux</text>
  <text x="352" y="117" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">reactive, Netty, R2DBC</text>

  <!-- NO: CLI/batch -->
  <rect x="480" y="85" width="195" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="577" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">spring-context</text>
  <text x="577" y="117" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">CLI, batch, library</text>

  <!-- Database question -->
  <rect x="100" y="160" width="200" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="200" y="178" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">spring-orm + spring-tx</text>
  <text x="200" y="193" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">JPA entities, @Repository</text>

  <rect x="330" y="160" width="200" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="430" y="178" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">spring-jdbc + spring-tx</text>
  <text x="430" y="193" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">SQL templates, raw queries</text>

  <!-- Always present -->
  <rect x="200" y="238" width="300" height="26" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="350" y="255" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">spring-context always present (transitive floor)</text>

  <!-- Arrows from root -->
  <line x1="280" y1="50" x2="165" y2="83" stroke="#6db33f" stroke-width="1.5" marker-end="url(#da)"/>
  <line x1="350" y1="50" x2="352" y2="83" stroke="#6db33f" stroke-width="1.5" marker-end="url(#da)"/>
  <line x1="420" y1="50" x2="535" y2="83" stroke="#6db33f" stroke-width="1.5" marker-end="url(#da)"/>

  <!-- Labels -->
  <text x="200" y="75" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">blocking</text>
  <text x="352" y="75" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">reactive</text>
  <text x="500" y="75" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no HTTP</text>

  <!-- Arrows to DB modules -->
  <line x1="127" y1="125" x2="200" y2="158" stroke="#8b949e" stroke-width="1" marker-end="url(#da)"/>
  <line x1="127" y1="125" x2="380" y2="158" stroke="#8b949e" stroke-width="1" marker-end="url(#da)"/>
</svg>

The decision tree makes the choice explicit — pick the highest appropriate module; `spring-context` is implicit.

## 5. Runnable example

An order processing system built three ways — one per module combination — to show how the choice of modules shapes the architecture.

### Level 1 — Basic

Library / CLI archetype: `spring-context` only, no HTTP, no database.

```java
// ModuleChoiceDemo.java — run with: java ModuleChoiceDemo.java
// Archetype: library / CLI — spring-context only.

import java.util.*;

public class ModuleChoiceDemo {

    // This is what you'd write for a library or CLI tool:
    // pom.xml:  spring-context:6.1.4  (only dependency)
    // No spring-webmvc, no spring-jdbc, no embedded server.

    record Product(int id, String name, double price) {}
    record OrderRequest(String customer, int productId, int quantity) {}
    record OrderResult(String status, double total, String message) {}

    // @Service bean — testable POJO, no HTTP, no DB
    static class OrderCalculator {
        private final Map<Integer, Product> catalog = Map.of(
            1, new Product(1, "Laptop",  1299.99),
            2, new Product(2, "Monitor",  449.99),
            3, new Product(3, "Keyboard",  89.99)
        );

        OrderResult calculate(OrderRequest req) {
            Product p = catalog.get(req.productId());
            if (p == null)
                return new OrderResult("FAILED", 0, "Product not found: " + req.productId());
            double total = p.price() * req.quantity();
            return new OrderResult("OK", total,
                "Order for " + req.quantity() + "x " + p.name() + " = $" + String.format("%.2f", total));
        }
    }

    // @Configuration — the only wiring needed
    static class AppConfig {
        OrderCalculator orderCalculator() { return new OrderCalculator(); }
    }

    public static void main(String[] args) {
        System.out.println("=== Module Choice — Level 1: spring-context only (CLI/library) ===\n");
        System.out.println("pom.xml:");
        System.out.println("  <dependency>");
        System.out.println("    <groupId>org.springframework</groupId>");
        System.out.println("    <artifactId>spring-context</artifactId>");
        System.out.println("  </dependency>");
        System.out.println("  NO spring-webmvc, NO spring-jdbc, NO Tomcat\n");

        AppConfig cfg = new AppConfig();
        OrderCalculator calc = cfg.orderCalculator();

        List<OrderRequest> requests = List.of(
            new OrderRequest("alice", 1, 2),
            new OrderRequest("bob",   3, 5),
            new OrderRequest("carol", 9, 1)
        );

        for (OrderRequest req : requests) {
            OrderResult result = calc.calculate(req);
            System.out.printf("%-10s → %s%n", req.customer(), result.message());
        }
    }
}
```

How to run: `java ModuleChoiceDemo.java`

`OrderCalculator` is a plain Java class with zero framework imports. The "container" here is a hand-built `AppConfig`. In a real Spring project the container (`AnnotationConfigApplicationContext`) wires it; in tests you create it directly — no container needed. This is the minimal module footprint.

### Level 2 — Intermediate

REST API archetype: `spring-webmvc` + `spring-jdbc` + `spring-tx`.

```java
// ModuleChoiceV2.java — run with: java ModuleChoiceV2.java
// Archetype: REST API — spring-webmvc + spring-jdbc + spring-tx.

import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class ModuleChoiceV2 {

    // pom.xml starters:
    //   spring-boot-starter-web   → spring-webmvc + Tomcat + Jackson
    //   spring-boot-starter-jdbc  → spring-jdbc + HikariCP
    //   (spring-tx included transitively in both)

    record Product(int id, String name, double price) {}
    record OrderRequest(String customer, int productId, int quantity) {}

    // @Repository — wraps spring-jdbc JdbcTemplate
    static class ProductRepository {
        private final Map<Integer, Product> db = new LinkedHashMap<>(Map.of(
            1, new Product(1, "Laptop",  1299.99),
            2, new Product(2, "Monitor",  449.99)
        ));
        Optional<Product> findById(int id) { return Optional.ofNullable(db.get(id)); }
        // In real spring-jdbc: jdbcTemplate.queryForObject("SELECT...", productRowMapper, id)
    }

    // @Service with @Transactional
    static class OrderService {
        private final ProductRepository repo;
        private final AtomicInteger orderSeq = new AtomicInteger(1000);

        OrderService(ProductRepository repo) { this.repo = repo; }

        // @Transactional — spring-tx + spring-jdbc manage the connection lifecycle
        Map<String, Object> placeOrder(OrderRequest req) {
            System.out.println("  [TX BEGIN]");
            Product p = repo.findById(req.productId())
                .orElseThrow(() -> new NoSuchElementException("Product " + req.productId()));
            int orderId = orderSeq.incrementAndGet();
            double total = p.price() * req.quantity();
            System.out.printf("  [SQL] INSERT INTO orders(id,customer,product_id,total) VALUES(%d,'%s',%d,%.2f)%n",
                orderId, req.customer(), req.productId(), total);
            System.out.println("  [TX COMMIT]");
            return Map.of("orderId", orderId, "total", total, "product", p.name());
        }
    }

    // @RestController — spring-webmvc routes HTTP to this method
    static class OrderController {
        private final OrderService svc;
        OrderController(OrderService svc) { this.svc = svc; }

        // POST /orders → 201 Created with JSON body
        Map<String, Object> createOrder(OrderRequest req) { return svc.placeOrder(req); }
    }

    // Simulated HTTP layer
    record HttpReq(String method, String path, OrderRequest body) {}
    record HttpResp(int status, Object body) {
        @Override public String toString() { return "HTTP " + status + " " + body; }
    }

    public static void main(String[] args) {
        System.out.println("=== Module Choice — Level 2: spring-webmvc + spring-jdbc + spring-tx ===\n");
        System.out.println("Starters: spring-boot-starter-web + spring-boot-starter-jdbc\n");

        ProductRepository repo = new ProductRepository();
        OrderService svc = new OrderService(repo);
        OrderController ctrl = new OrderController(svc);

        List<HttpReq> requests = List.of(
            new HttpReq("POST", "/orders", new OrderRequest("alice", 1, 2)),
            new HttpReq("POST", "/orders", new OrderRequest("bob",   2, 1)),
            new HttpReq("POST", "/orders", new OrderRequest("carol", 9, 1))
        );

        for (HttpReq req : requests) {
            System.out.printf("--- %s %s (body: %s) ---%n", req.method(), req.path(), req.body());
            HttpResp resp;
            try {
                Map<String, Object> result = ctrl.createOrder(req.body());
                resp = new HttpResp(201, result);
            } catch (NoSuchElementException e) {
                resp = new HttpResp(404, Map.of("error", e.getMessage()));
            }
            System.out.println("  → " + resp + "\n");
        }

        System.out.println("Module responsibility:");
        System.out.println("  spring-webmvc: HTTP routing, JSON marshalling, DispatcherServlet");
        System.out.println("  spring-jdbc:   SQL execution (JdbcTemplate), connection from HikariCP");
        System.out.println("  spring-tx:     @Transactional wraps service method in DB transaction");
    }
}
```

How to run: `java ModuleChoiceV2.java`

Each module has a clear seam: `spring-webmvc` owns the HTTP layer, `spring-jdbc` owns SQL execution, `spring-tx` owns the transaction boundary. Swapping `spring-jdbc` for `spring-orm` (JPA) would change only the repository implementation — the controller and service are unaffected.

### Level 3 — Advanced

Side-by-side comparison: the same order service as MVC (blocking, thread-per-request) vs. WebFlux (reactive, event loop) — showing when to choose each.

```java
// ModuleChoiceV3.java — run with: java ModuleChoiceV3.java
// Archetype comparison: spring-webmvc vs spring-webflux — same scenario, different model.

import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;

public class ModuleChoiceV3 {

    record Product(int id, String name, double price) {}
    record OrderResult(int orderId, String product, double total) {}

    // ==== MVC archetype (spring-webmvc) ====
    // spring-boot-starter-web + spring-boot-starter-data-jpa
    // One thread per request. @RestController returns OrderResult directly.
    static class MvcOrderController {
        private final Map<Integer, Product> catalog = Map.of(
            1, new Product(1, "Laptop", 1299.99),
            2, new Product(2, "Monitor", 449.99)
        );
        private final AtomicInteger seq = new AtomicInteger(100);

        // @PostMapping("/orders")
        // @Transactional     ← blocks the request thread until DB commit
        OrderResult placeOrder(int productId, int qty) throws InterruptedException {
            Thread.sleep(5);  // simulates blocking JDBC call
            Product p = Optional.ofNullable(catalog.get(productId))
                .orElseThrow(() -> new NoSuchElementException("Product " + productId));
            return new OrderResult(seq.incrementAndGet(), p.name(), p.price() * qty);
        }
    }

    // ==== WebFlux archetype (spring-webflux) ====
    // spring-boot-starter-webflux + spring-boot-starter-data-r2dbc
    // Event loop. @RestController returns Mono<OrderResult>.
    static class WebFluxOrderHandler {
        private final Map<Integer, Product> catalog = Map.of(
            1, new Product(1, "Laptop", 1299.99),
            2, new Product(2, "Monitor", 449.99)
        );
        private final AtomicInteger seq = new AtomicInteger(200);

        // RouterFunction<ServerResponse> → Mono<ServerResponse>
        // Non-blocking R2DBC call → no thread blocked
        CompletableFuture<OrderResult> placeOrderAsync(int productId, int qty) {
            return CompletableFuture.supplyAsync(() -> {
                Product p = Optional.ofNullable(catalog.get(productId))
                    .orElseThrow(() -> new NoSuchElementException("Product " + productId));
                return new OrderResult(seq.incrementAndGet(), p.name(), p.price() * qty);
            });
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Module Choice — Level 3: MVC vs. WebFlux comparison ===\n");

        int concurrentRequests = 10;

        // MVC: thread-per-request — each request ties up a thread for 5ms
        MvcOrderController mvc = new MvcOrderController();
        ExecutorService pool = Executors.newFixedThreadPool(4);  // 4 threads = 4 concurrent requests

        System.out.println("--- spring-webmvc (blocking, 4-thread pool) ---");
        long mvcStart = System.currentTimeMillis();
        List<Future<OrderResult>> mvcFutures = new ArrayList<>();
        for (int i = 0; i < concurrentRequests; i++) {
            final int pid = (i % 2) + 1;
            mvcFutures.add(pool.submit(() -> mvc.placeOrder(pid, 1)));
        }
        for (Future<OrderResult> f : mvcFutures) System.out.println("  MVC: " + f.get());
        long mvcElapsed = System.currentTimeMillis() - mvcStart;
        pool.shutdown();

        // WebFlux: event loop — all requests start immediately, no thread blocking
        WebFluxOrderHandler flux = new WebFluxOrderHandler();

        System.out.println("\n--- spring-webflux (non-blocking, event loop) ---");
        long fluxStart = System.currentTimeMillis();
        List<CompletableFuture<OrderResult>> fluxFutures = new ArrayList<>();
        for (int i = 0; i < concurrentRequests; i++) {
            final int pid = (i % 2) + 1;
            fluxFutures.add(flux.placeOrderAsync(pid, 1));
        }
        List<OrderResult> fluxResults = CompletableFuture
            .allOf(fluxFutures.toArray(new CompletableFuture[0]))
            .thenApply(_ -> fluxFutures.stream().map(CompletableFuture::join).toList())
            .get();
        fluxResults.forEach(r -> System.out.println("  WebFlux: " + r));
        long fluxElapsed = System.currentTimeMillis() - fluxStart;

        System.out.printf("%n--- Performance summary for %d concurrent requests ---%n", concurrentRequests);
        System.out.printf("  MVC (4-thread pool):  %dms  — limited by thread count%n", mvcElapsed);
        System.out.printf("  WebFlux (event loop): %dms  — not blocked by thread count%n", fluxElapsed);

        System.out.println("\n--- When to choose ---");
        System.out.println("  MVC:    blocking JDBC/JPA + JDK 21 virtual threads → best of both worlds");
        System.out.println("  WebFlux: streaming, SSE, fully reactive stack (R2DBC, reactive clients)");
        System.out.println("  Key rule: if your team doesn't need reactive, use MVC + virtual threads.");
    }
}
```

How to run: `java ModuleChoiceV3.java` (JDK 17+; `_ ` lambda parameter requires JDK 22+ — replace with `ignored` if on 17)

MVC with a 4-thread pool processes 10 requests in ~3 batches (`ceil(10/4)*5ms ≈ 15ms`). WebFlux processes all 10 concurrently (≈5ms total). The lesson: MVC is not inherently slow — it just limits concurrency to thread count. Spring Boot 3.2 + JDK 21 virtual threads give MVC WebFlux-level concurrency without reactive programming.

## 6. Walkthrough

**Level 1 — catalog lookup:**
`calc.calculate(new OrderRequest("alice", 1, 2))` → `catalog.get(1)` → `Product(1, "Laptop", 1299.99)` → `total = 1299.99 * 2 = 2599.98` → `OrderResult("OK", 2599.98, "Order for 2x Laptop = $2599.98")`.

**Level 2 — HTTP → service → SQL → response:**
```
POST /orders {"customer":"alice","productId":1,"quantity":2}
  → OrderController.createOrder(req)
  → OrderService.placeOrder(req)
      [TX BEGIN]
      repo.findById(1) → Product(1,"Laptop",1299.99)
      [SQL] INSERT INTO orders(id,customer,product_id,total) VALUES(1001,'alice',1,2599.98)
      [TX COMMIT]
  → {orderId:1001, total:2599.98, product:"Laptop"}
HTTP 201 {orderId:1001, total:2599.98, product:"Laptop"}
```

`productId=9` → `repo.findById(9)` → `Optional.empty()` → `NoSuchElementException` → controller catches → `HTTP 404 {"error":"Product 9"}`.

**Level 3 — MVC blocking behaviour:**
10 requests, 4-thread pool, each blocks for 5ms. First 4 requests start simultaneously. Requests 5–8 wait for threads 1–4 to finish (~5ms). Requests 9–10 wait another ~5ms. Total: ~15ms. With JDK 21 virtual threads (`Executors.newVirtualThreadPerTaskExecutor()`), each of the 10 requests gets its own virtual thread, all 10 start simultaneously, and total time ≈ 5ms — matching WebFlux.

**WebFlux event loop:** all 10 `CompletableFuture.supplyAsync()` calls start immediately on the ForkJoinPool (simulating Netty's event loop). No thread is blocked waiting. `allOf(...)` resolves when all 10 complete — approximately 5ms for the group.

## 7. Gotchas & takeaways

> **Do not mix `spring-webmvc` and `spring-webflux` as primary web layers.** You can have `spring-webflux` on the classpath (some libraries need it) alongside `spring-webmvc`, but Spring Boot auto-configuration will pick one. The auto-config prefers MVC if both are present. Use `spring.main.web-application-type=reactive` to force WebFlux, or remove `spring-boot-starter-web` to prevent MVC from taking over.

> **`spring-tx` is not automatic without AOP.** `@Transactional` requires a proxy around the annotated bean. If you declare a `@Transactional` service bean but the container doesn't process AOP post-processors (which `spring-context` enables by default), the annotation is silently ignored and no transaction is created. Always add `@EnableTransactionManagement` to your `@Configuration` (or use Spring Boot, which enables it automatically with `spring-boot-starter-data-jpa` or `spring-boot-starter-jdbc`).

- Module selection is the first architecture decision. Get it right before writing code — changing from MVC to WebFlux mid-project requires rewriting every controller, service, and data access layer.
- `spring-context-support` provides enterprise extras: `JavaMailSender`, `Quartz` integration, `ThreadPoolTaskExecutor`. Add it when you need email or scheduled tasks without Boot.
- Don't add `spring-aop` explicitly — it is a transitive dependency of `spring-context`. Only add `spring-aspects` if you need AspectJ compile-time or load-time weaving (rare, for non-proxy-able cross-cutting concerns).
- For test dependencies: `spring-test` (in `spring-boot-starter-test`) provides `@SpringBootTest`, `MockMvc`, `@MockBean`, and context caching across tests. These require `spring-context`; they are not useful without a container.
- Run `mvn dependency:tree | grep spring` (or `./gradlew :app:dependencies | grep spring`) to verify the exact Spring module set resolved for your project. Compare it to the expected set for your archetype.
