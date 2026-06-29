---
card: spring-framework
gi: 7
slug: spring-6-spring-boot-3-generation-overview
title: Spring 6 / Spring Boot 3 generation overview
---

## 1. What it is

**Spring Framework 6** and **Spring Boot 3** (released together in November 2022) form the current major generation of the Spring platform. They share a common set of hard prerequisites:

- **JDK 17** minimum (JDK 21 for virtual threads in Spring 6.1 / Boot 3.2).
- **Jakarta EE 9+** (`jakarta.*` namespace).
- **Hibernate ORM 6** for JPA.
- **Tomcat 10** / **Jetty 11** / **Undertow 2.2** as embedded servers.

The generation introduced several landmark capabilities:

| Capability | Details |
|---|---|
| **AOT (Ahead-of-Time) processing** | Generates bean definitions and reflection metadata at build time for faster startup and GraalVM native images |
| **GraalVM Native Image** | Compile the Spring app to a platform-native binary (no JVM) — millisecond startup, low memory |
| **Observability** | Built-in Micrometer Observation API for unified metrics, tracing, and logging across all Spring modules |
| **RestClient** | New synchronous HTTP client (Spring 6.1) — fluent `RestClient` replaces the old `RestTemplate` |
| **HTTP interface clients** | `@HttpExchange` + declarative HTTP client interfaces (similar to Spring Data repositories) |
| **Virtual threads (Spring 6.1 / Boot 3.2)** | JDK 21 virtual threads for `@Async`, Tomcat threads, `@Transactional` — massive scalability improvement without reactive code |
| **Problem Details (RFC 7807)** | `ProblemDetail` response type for structured error responses |

## 2. Why & when

The Spring 6 / Boot 3 generation is the **target for all new projects** started in 2023 or later. Spring Boot 2.x / Framework 5.x reached end-of-life in November 2023; security patches are no longer published for those branches.

**Key reasons to be on Spring 6 / Boot 3:**
- Native image support means cloud functions, serverless, and CLI tools can be built with Spring and still start in < 100 ms.
- Observability is baked in — no more separate instrumentation code for metrics and traces.
- Jakarta EE 9+ alignment keeps the ecosystem moving together (Hibernate, Tomcat, Jackson all moved to jakarta too).

**Upgrade path:** Spring Boot provides a structured migration path from 2.x to 3.x. The main steps are: JDK 17, jakarta.* imports, Properties Migrator, Spring Security 6.x API changes, and Hibernate 6.x naming defaults.

## 3. Core concept

**AOT (Ahead-of-Time) processing** is the flagship architectural feature. In traditional Spring, the `ApplicationContext` performs all bean creation, dependency resolution, and proxy generation at runtime during startup. AOT shifts much of that work to build time.

How AOT works in Spring 6 / Boot 3:
1. At build time, `spring-aot-maven-plugin` (or Gradle equivalent) runs `SpringApplicationAotProcessor`.
2. The processor simulates a context refresh, generates bean definition classes (`BeanDefinitionRegistrar`), serialises reflection/proxy/resource hints to `META-INF/native-image/`.
3. GraalVM's `native-image` tool compiles the application — including all reachable code — to a native binary. It uses the hints to include reflection metadata that GraalVM would otherwise strip.
4. At runtime, the native binary starts without a JVM, reads the pre-computed bean definitions, and the app is ready in milliseconds.

For JVM deployments (the common case), AOT still helps: Spring Boot generates `*__BeanFactoryRegistrations.java` source files that replace XML/annotation-based bean discovery with direct method calls — faster startup than full classpath scanning.

**Observability** is the second major theme: Spring 6 wraps all cross-cutting operations (HTTP requests, JDBC calls, cache hits, `@Async` tasks) with `Observation` instances from the `micrometer-observation` API. One `Observation` produces metrics (Micrometer), traces (OpenTelemetry / Zipkin / Jaeger), and log correlation automatically — without manual instrumentation.

## 4. Diagram

<svg viewBox="0 0 700 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring 6 Boot 3 generation: JVM path on left, AOT native path on right, both starting from source code">
  <defs>
    <marker id="ga" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="oa" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Source -->
  <rect x="260" y="10" width="180" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="350" y="35" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Spring Application Source</text>

  <!-- Build time fork -->
  <line x1="350" y1="50" x2="180" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ga)"/>
  <line x1="350" y1="50" x2="520" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#oa)"/>

  <!-- JVM path -->
  <rect x="60" y="100" width="240" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="180" y="120" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">JVM path (default)</text>
  <text x="180" y="137" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">mvn package → fat JAR → java -jar</text>

  <!-- AOT / Native path -->
  <rect x="400" y="100" width="240" height="45" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="520" y="120" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">AOT + Native path</text>
  <text x="520" y="137" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">mvn -Pnative package → GraalVM → binary</text>

  <!-- JVM result -->
  <rect x="80" y="165" width="200" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="180" y="184" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Startup: ~2–5 s</text>
  <text x="180" y="200" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Memory: ~300–500 MB</text>
  <text x="180" y="213" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Throughput: excellent (JIT)</text>

  <!-- Native result -->
  <rect x="420" y="165" width="200" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="520" y="184" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Startup: &lt; 100 ms</text>
  <text x="520" y="200" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Memory: ~50–100 MB</text>
  <text x="520" y="213" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Throughput: good (no JIT warmup)</text>

  <!-- Observability banner -->
  <rect x="100" y="228" width="500" height="24" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="350" y="244" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Both paths: Micrometer Observation → metrics + traces + log correlation, zero extra code</text>
</svg>

Spring 6 / Boot 3 supports both paths: JVM fat JARs and GraalVM native binaries from the same source code.

## 5. Runnable example

A product order service built with Spring 6 / Boot 3 patterns — observability, RestClient, and `ProblemDetail`.

### Level 1 — Basic

`RestClient` (new in Spring 6.1) replacing `RestTemplate` — the simplest form.

```java
// Spring6Demo.java — run with: java Spring6Demo.java
// Demonstrates Spring 6 / Boot 3 API patterns without a running server.

import java.util.*;

public class Spring6Demo {

    // --- Spring 6.1: RestClient (simulated) ---
    // In a real Spring Boot 3 app:
    //   RestClient client = RestClient.builder()
    //       .baseUrl("https://api.example.com")
    //       .build();
    //   Product product = client.get()
    //       .uri("/products/{id}", 42)
    //       .retrieve()
    //       .body(Product.class);

    record Product(int id, String name, double price) {}
    record Order(int id, String customer, Product product, double total) {}

    // Simulated RestClient behaviour
    static class ProductClient {
        private final Map<Integer, Product> catalog = Map.of(
            1, new Product(1, "Laptop",  1299.99),
            2, new Product(2, "Monitor",  449.99)
        );

        // RestClient.get().uri("/products/{id}").retrieve().body(Product.class)
        Optional<Product> get(int id) { return Optional.ofNullable(catalog.get(id)); }
    }

    static class OrderService {
        private final ProductClient productClient;

        OrderService(ProductClient client) { this.productClient = client; }

        Order placeOrder(String customer, int productId) {
            Product product = productClient.get(productId)
                .orElseThrow(() -> new NoSuchElementException("Product not found: " + productId));
            return new Order(1, customer, product, product.price() * 1.1);  // +10% tax
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Spring 6 / Boot 3 — Level 1: RestClient style ===\n");

        ProductClient client = new ProductClient();
        OrderService svc = new OrderService(client);

        System.out.println("GET /products/1 via RestClient:");
        System.out.println("  " + client.get(1));

        System.out.println("\nPlace order (customer=alice, product=1):");
        Order order = svc.placeOrder("alice@example.com", 1);
        System.out.println("  " + order);

        System.out.println("\nPlace order (customer=bob, product=99):");
        try {
            svc.placeOrder("bob@example.com", 99);
        } catch (NoSuchElementException e) {
            System.out.println("  Error: " + e.getMessage());
        }
    }
}
```

How to run: `java Spring6Demo.java`

`ProductClient.get` mirrors `RestClient.get().uri("/products/{id}",id).retrieve().body(Product.class)`. The fluent builder API is Spring 6.1's replacement for `RestTemplate.getForObject()`.

### Level 2 — Intermediate

Add `ProblemDetail` (RFC 7807) error responses and `@HttpExchange` declarative client pattern.

```java
// Spring6DemoV2.java — run with: java Spring6DemoV2.java
// Adds ProblemDetail RFC 7807 + @HttpExchange declarative client pattern.

import java.util.*;
import java.net.URI;

public class Spring6DemoV2 {

    record Product(int id, String name, double price) {}

    // --- Spring 6: ProblemDetail (RFC 7807) ---
    // In a real Spring MVC controller: return ResponseEntity.of(ProblemDetail.forStatus(404))
    record ProblemDetail(int status, String title, String detail, URI type) {
        static ProblemDetail notFound(String detail) {
            return new ProblemDetail(404, "Not Found", detail,
                URI.create("https://api.example.com/errors/not-found"));
        }
        static ProblemDetail badRequest(String detail) {
            return new ProblemDetail(400, "Bad Request", detail,
                URI.create("https://api.example.com/errors/bad-request"));
        }
        @Override public String toString() {
            return String.format("ProblemDetail{status=%d, title='%s', detail='%s'}",
                status, title, detail);
        }
    }

    // --- Spring 6: @HttpExchange declarative client (interface + RestClient/WebClient) ---
    // In real Spring: annotate with @HttpExchange, inject via @HttpExchangeClient
    interface ProductHttpClient {
        Optional<Product> getProduct(int id);    // GET /products/{id}
        List<Product> listProducts();            // GET /products
    }

    static class ProductHttpClientImpl implements ProductHttpClient {
        private final Map<Integer, Product> remote = Map.of(
            1, new Product(1, "Laptop",  1299.99),
            2, new Product(2, "Monitor",  449.99)
        );
        public Optional<Product> getProduct(int id) { return Optional.ofNullable(remote.get(id)); }
        public List<Product> listProducts() { return new ArrayList<>(remote.values()); }
    }

    // --- Controller returning ProblemDetail on error ---
    record HttpResponse(int status, Object body) {
        @Override public String toString() {
            return "HTTP " + status + ": " + body;
        }
    }

    static class ProductController {
        private final ProductHttpClient client;

        ProductController(ProductHttpClient client) { this.client = client; }

        HttpResponse getProduct(int id) {
            return client.getProduct(id)
                .<HttpResponse>map(p -> new HttpResponse(200, p))
                .orElseGet(() -> new HttpResponse(404, ProblemDetail.notFound("Product " + id + " not found")));
        }

        HttpResponse getProductsFiltered(double minPrice) {
            if (minPrice < 0)
                return new HttpResponse(400, ProblemDetail.badRequest("minPrice must be >= 0"));
            List<Product> matching = client.listProducts().stream()
                .filter(p -> p.price() >= minPrice)
                .toList();
            return new HttpResponse(200, matching);
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Spring 6 / Boot 3 — Level 2: ProblemDetail + @HttpExchange ===\n");

        ProductHttpClient client = new ProductHttpClientImpl();
        ProductController ctrl = new ProductController(client);

        System.out.println("GET /products/1:  " + ctrl.getProduct(1));
        System.out.println("GET /products/99: " + ctrl.getProduct(99));
        System.out.println();
        System.out.println("GET /products?minPrice=500:  " + ctrl.getProductsFiltered(500));
        System.out.println("GET /products?minPrice=-1:   " + ctrl.getProductsFiltered(-1));
    }
}
```

How to run: `java Spring6DemoV2.java`

`ProblemDetail.notFound(...)` produces a structured JSON error body with `status`, `title`, `detail`, and `type` fields — the RFC 7807 format. Spring Boot 3 serialises this to JSON automatically when the controller returns `ProblemDetail`.

### Level 3 — Advanced

Add Micrometer Observation tracing simulation, AOT metadata generation hint, and virtual thread readiness check — the full Spring 6.1 / Boot 3.2 feature set.

```java
// Spring6DemoV3.java — run with: java Spring6DemoV3.java (JDK 21 for virtual threads)

import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class Spring6DemoV3 {

    record Product(int id, String name, double price) {}
    record Order(int id, String customer, Product product, double total) {}

    // --- Micrometer Observation (simulated) ---
    // Real: io.micrometer.observation.Observation.createNotStarted("order.place", registry)
    static class Observation {
        private final String name;
        private final long startNs;
        private final List<String> events = new ArrayList<>();
        static final AtomicLong counter = new AtomicLong();

        Observation(String name) {
            this.name = name;
            this.startNs = System.nanoTime();
            System.out.println("  [OBS] START  " + name + " (traceId=" + traceId() + ")");
        }

        void event(String eventName) {
            events.add(eventName);
            System.out.println("  [OBS] EVENT  " + name + " → " + eventName);
        }

        void stop(boolean success) {
            long elapsed = (System.nanoTime() - startNs) / 1_000;
            System.out.printf("  [OBS] STOP   %s success=%b elapsed=%dµs → metric emitted%n",
                name, success, elapsed);
        }

        private static String traceId() { return String.format("%016x", counter.incrementAndGet()); }
    }

    // --- Service with Observation instrumentation (Spring 6 @Observed equivalent) ---
    static class OrderService {
        private final Map<Integer, Product> products = Map.of(
            1, new Product(1, "Laptop",  1299.99),
            2, new Product(2, "Monitor",  449.99)
        );

        Order placeOrder(String customer, int productId) {
            Observation obs = new Observation("order.place");
            try {
                obs.event("product.lookup");
                Product p = Optional.ofNullable(products.get(productId))
                    .orElseThrow(() -> new NoSuchElementException("Product " + productId));

                obs.event("order.create");
                Order order = new Order(
                    (int)(System.nanoTime() % 10000), customer, p, p.price() * 1.1);

                obs.stop(true);
                return order;
            } catch (Exception e) {
                obs.event("error: " + e.getMessage());
                obs.stop(false);
                throw e;
            }
        }
    }

    // --- AOT hint simulation ---
    static void printAotHints() {
        System.out.println("\n  [AOT] Bean definition registrar generated:");
        System.out.println("        OrderService__BeanDefinitions.registerOrderServiceBean(ctx)");
        System.out.println("  [AOT] Reflection hints for GraalVM:");
        System.out.println("        {\"name\":\"Product\",\"allDeclaredConstructors\":true,\"allDeclaredFields\":true}");
        System.out.println("        {\"name\":\"Order\",   \"allDeclaredConstructors\":true,\"allDeclaredFields\":true}");
    }

    // --- Virtual thread readiness ---
    static void demonstrateVirtualThreads() throws Exception {
        boolean isVirtualAvailable;
        try {
            Thread.ofVirtual();  // JDK 21+
            isVirtualAvailable = true;
        } catch (NoSuchMethodError e) {
            isVirtualAvailable = false;
        }

        System.out.println("\n  Virtual thread support: " + (isVirtualAvailable ? "JDK 21 — enabled" : "JDK < 21 — not available"));
        System.out.println("  spring.threads.virtual.enabled=true  → Boot 3.2 activates on JDK 21");

        if (isVirtualAvailable) {
            try (ExecutorService vtp = Executors.newVirtualThreadPerTaskExecutor()) {
                List<Future<String>> futures = new ArrayList<>();
                for (int i = 0; i < 5; i++) {
                    final int n = i;
                    futures.add(vtp.submit(() -> "VT-" + Thread.currentThread().getName() + " processed " + n));
                }
                for (Future<String> f : futures) System.out.println("    " + f.get());
            }
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Spring 6 / Boot 3 — Level 3: Observability + AOT + Virtual Threads ===\n");

        OrderService svc = new OrderService();

        System.out.println("--- Order 1 (success) ---");
        Order o1 = svc.placeOrder("alice@example.com", 1);
        System.out.println("  Result: " + o1);

        System.out.println("\n--- Order 2 (not found) ---");
        try { svc.placeOrder("bob@example.com", 99); }
        catch (NoSuchElementException e) { System.out.println("  Error: " + e.getMessage()); }

        System.out.println("\n--- AOT Metadata (generated at build time) ---");
        printAotHints();

        System.out.println("\n--- Runtime Characteristics ---");
        demonstrateVirtualThreads();

        System.out.println("\n=== Spring 6 / Boot 3 generation summary ===");
        System.out.println("  JDK 17+         → records, sealed types, pattern matching");
        System.out.println("  Jakarta EE 9+   → jakarta.* namespace");
        System.out.println("  AOT + GraalVM   → native images, < 100ms startup");
        System.out.println("  Observability   → Micrometer Observation (metrics + traces unified)");
        System.out.println("  RestClient      → replaces RestTemplate (fluent, non-blocking capable)");
        System.out.println("  ProblemDetail   → RFC 7807 structured error responses");
        System.out.println("  Virtual threads → Boot 3.2 + JDK 21 = massive concurrency, no reactive code");
    }
}
```

How to run: `java Spring6DemoV3.java` (JDK 17+ for compile; JDK 21 for virtual thread output)

`Observation` wraps every service call: `START → EVENT(s) → STOP`. In a real Spring Boot 3 app, one `Observation.start()` produces a Micrometer timer metric, a Brave/OTel span for distributed tracing, and an MDC log key for correlation — three outputs, zero extra lines in business code.

## 6. Walkthrough

**Level 1 — normal flow:**
`OrderService.placeOrder("alice", 1)` calls `ProductClient.get(1)` → `Optional.of(Product(1, "Laptop", 1299.99))`. Multiplied by 1.1 for tax → `Order(1, "alice", Product(...), 1429.99)`. Returned and printed.

**Level 2 — ProblemDetail:**
`ctrl.getProduct(99)` calls `client.getProduct(99)` → `Optional.empty()`. The `orElseGet` branch fires → `ProblemDetail.notFound("Product 99 not found")` → `HttpResponse(404, ProblemDetail{...})`. In real Spring MVC this becomes:
```
HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{"status":404,"title":"Not Found","detail":"Product 99 not found","type":"https://api.example.com/errors/not-found"}
```

**Level 3 — observation lifecycle:**
1. `new Observation("order.place")` records start time, logs `[OBS] START`.
2. `obs.event("product.lookup")` logs the phase.
3. If product found, `obs.event("order.create")` fires.
4. `obs.stop(true)` logs elapsed time and "metric emitted". In real Micrometer this calls `registry.timer("order.place").record(elapsed)`.

**AOT at build time:**
```
mvn spring-boot:process-aot
```
Generates `OrderService__BeanDefinitions.java` (direct method calls replacing classpath scanning), and `reflect-config.json` entries so GraalVM knows to include reflection for `Product` and `Order` constructors.

**Virtual threads (JDK 21):**
Five tasks submit to `newVirtualThreadPerTaskExecutor`. Each runs on its own virtual thread (cheap — JDK manages tens of thousands). Spring 6.1 routes all `@Async` calls and Tomcat request threads through this pool automatically when `spring.threads.virtual.enabled=true`.

## 7. Gotchas & takeaways

> **AOT / native image has restrictions.** GraalVM's closed-world assumption means all reflection, proxies, and resources must be declared in hints at build time. Spring Boot's AOT processor generates most hints automatically, but dynamic class loading, runtime-generated bytecode (some Hibernate features), and reflection via `Class.forName(String)` with a runtime-computed name require manual `@RegisterReflectionForBinding` or `RuntimeHints` registrations.

> **`RestClient` is synchronous; `WebClient` is reactive.** Both fluent. Use `RestClient` when you have a Servlet-based app (Spring MVC). Use `WebClient` when you have a reactive app (Spring WebFlux). `RestTemplate` is not deprecated but receives no new features in Spring 6.

- Spring 6.0 released November 2022; Spring 6.1 (December 2023) added virtual thread support, `RestClient`, and HTTP interface client improvements.
- Spring Boot 3.0 = Framework 6.0; Boot 3.1 = Framework 6.0.x; Boot 3.2 = Framework 6.1; Boot 3.3 = Framework 6.1.x.
- `ProblemDetail` is automatically serialised by `ErrorMessageConverter` when you annotate a controller with `@RestControllerAdvice` and return `ResponseEntity<ProblemDetail>`.
- Micrometer Observation API is the replacement for manual `Timer.record(...)` calls; annotate methods with `@Observed` to auto-instrument without writing `Observation` objects.
- GraalVM native images build in minutes but the resulting binary is platform-specific (Linux/macOS/Windows). CI must build on the target platform.
