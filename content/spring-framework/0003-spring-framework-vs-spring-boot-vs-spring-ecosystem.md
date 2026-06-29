---
card: spring-framework
gi: 3
slug: spring-framework-vs-spring-boot-vs-spring-ecosystem
title: Spring Framework vs Spring Boot vs Spring ecosystem
---

## 1. What it is

Three levels of "Spring" are often confused:

**Spring Framework** is the core library: the IoC container, dependency injection, AOP, transaction management, Spring MVC, WebFlux, JDBC/ORM integration, and testing utilities. It is a set of JARs you add to any Java project. You decide how to wire it up, which modules to use, and how to configure them.

**Spring Boot** sits on top of Spring Framework. It adds:
- **Auto-configuration** — detects what JARs are on the classpath and configures beans automatically (no XML, no `@Bean` factory methods for standard setups).
- **Starters** — curated Maven/Gradle dependencies that pull in a consistent set of libraries (`spring-boot-starter-web` = Spring MVC + Tomcat + Jackson).
- **Embedded server** — Tomcat, Jetty, or Undertow embedded directly in the JAR; you run `java -jar app.jar`, no external server needed.
- **Opinionated defaults** — sensible property defaults, Actuator for health/metrics, and a production-ready baseline out of the box.

**Spring ecosystem** (often called "Spring Projects") is a family of standalone projects built on Spring Framework and/or Spring Boot, each solving a specific domain:

| Project | Purpose |
|---|---|
| Spring Data | Repository abstractions for JPA, MongoDB, Redis, Cassandra, etc. |
| Spring Security | Authentication, authorisation, OAuth2, CSRF protection |
| Spring Batch | Large-scale, fault-tolerant batch processing |
| Spring Integration | Enterprise Integration Patterns (messaging, adapters) |
| Spring Cloud | Microservice patterns: service discovery, config server, gateway |
| Spring AI | LLM integration, embedding, vector stores, AI clients |

## 2. Why & when

**Use Spring Framework** when: you are building a library; you need fine-grained control over configuration; you are integrating into a container-managed environment (JBoss, WebLogic); or you are wrapping Spring from another framework (e.g. Quarkus's Spring compatibility layer).

**Use Spring Boot** when: you are building a standalone application, microservice, REST API, or batch job and you want to get to production fast with sensible defaults. This is the right choice for > 90% of new Spring projects.

**Use Spring ecosystem projects** when: you need a specific domain capability that is not in Spring Framework itself — persisting data (Spring Data), securing endpoints (Spring Security), or distributing across services (Spring Cloud).

The three are not alternatives — they layer. A typical production service uses Spring Boot (auto-config + embedded server) + Spring Framework (the container underneath) + Spring Security + Spring Data JPA + Spring Cloud Config.

## 3. Core concept

Think of it as a stack:

```
Your application code
      │
Spring Boot  (auto-config, starters, embedded server, Actuator)
      │
Spring Framework  (IoC container, MVC, AOP, JDBC, transactions)
      │
Spring ecosystem projects  (plug in beside Boot/Framework)
      │
Plain Java / JDK / Jakarta EE APIs
```

**Auto-configuration** is the key difference between Framework and Boot. When you add `spring-boot-starter-data-jpa` to a Boot project, the auto-configurator detects `javax.persistence.EntityManagerFactory` on the classpath and wires up a `DataSource`, `EntityManagerFactory`, and `TransactionManager` — dozens of beans you'd have to declare yourself with bare Framework.

The mechanism: `@SpringBootApplication` includes `@EnableAutoConfiguration`, which triggers `AutoConfigurationImportSelector`. That reads `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` (in Boot 3.x) and conditionally activates configuration classes based on `@ConditionalOnClass`, `@ConditionalOnMissingBean`, etc.

With bare Spring Framework you do all of that manually via `@Bean` factory methods in `@Configuration` classes.

## 4. Diagram

<svg viewBox="0 0 700 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Stack diagram: Your code on top, Spring Boot middle, Spring Framework below, ecosystem projects alongside">
  <defs>
    <marker id="da" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Your code -->
  <rect x="200" y="10" width="300" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="35" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Your Application Code</text>

  <!-- Spring Boot -->
  <rect x="130" y="65" width="440" height="55" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="350" y="85" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Boot</text>
  <text x="350" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Auto-configuration · Starters · Embedded Tomcat/Jetty · Actuator · Opinionated defaults</text>

  <!-- Spring Framework -->
  <rect x="70" y="135" width="560" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="155" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Framework</text>
  <text x="350" y="174" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">IoC Container · DI · AOP · MVC · WebFlux · JDBC · Transactions · Testing</text>

  <!-- Ecosystem -->
  <rect x="10" y="205" width="155" height="55" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="87" y="226" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Spring Data</text>
  <text x="87" y="244" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JPA/Mongo/Redis</text>

  <rect x="175" y="205" width="155" height="55" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="252" y="226" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Spring Security</text>
  <text x="252" y="244" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Auth · OAuth2 · CSRF</text>

  <rect x="340" y="205" width="155" height="55" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="417" y="226" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Spring Cloud</text>
  <text x="417" y="244" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Discovery · Gateway · Config</text>

  <rect x="505" y="205" width="155" height="55" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="582" y="226" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Spring Batch/AI/…</text>
  <text x="582" y="244" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Domain-specific</text>

  <!-- Arrows -->
  <line x1="350" y1="50" x2="350" y2="63" stroke="#6db33f" stroke-width="1.5" marker-end="url(#da)"/>
  <line x1="350" y1="120" x2="350" y2="133" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#da)"/>
  <line x1="87"  y1="192" x2="87"  y2="203" stroke="#8b949e" stroke-width="1.5" marker-end="url(#da)"/>
  <line x1="252" y1="192" x2="252" y2="203" stroke="#8b949e" stroke-width="1.5" marker-end="url(#da)"/>
  <line x1="417" y1="192" x2="417" y2="203" stroke="#8b949e" stroke-width="1.5" marker-end="url(#da)"/>
  <line x1="582" y1="192" x2="582" y2="203" stroke="#8b949e" stroke-width="1.5" marker-end="url(#da)"/>

  <text x="350" y="273" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Ecosystem projects plug in beside Boot/Framework — they don't replace either layer</text>
</svg>

The stack has hard layers; ecosystem projects plug in at the sides.

## 5. Runnable example

We'll build the same REST-style product lookup — first with plain Spring Framework (manual wiring), then with what Spring Boot's auto-configuration handles automatically, and finally showing an ecosystem project (Spring Data style).

### Level 1 — Basic

Plain Spring Framework: no Boot. You create every bean manually.

```java
// FrameworkOnlyDemo.java — run with: java FrameworkOnlyDemo.java
// Shows what Spring Framework provides WITHOUT Spring Boot's auto-config.
// No embedded server here — just the container, service, and repository pattern.

import java.util.*;

public class FrameworkOnlyDemo {

    // --- Domain ---
    record Product(int id, String name, double price) {}

    // --- Repository (Data access layer) ---
    interface ProductRepository {
        Optional<Product> findById(int id);
        List<Product> findAll();
    }

    static class InMemoryProductRepository implements ProductRepository {
        private final Map<Integer, Product> store = Map.of(
            1, new Product(1, "Laptop",  1299.99),
            2, new Product(2, "Monitor",  449.99),
            3, new Product(3, "Keyboard",  89.99)
        );
        public Optional<Product> findById(int id) { return Optional.ofNullable(store.get(id)); }
        public List<Product> findAll() { return new ArrayList<>(store.values()); }
    }

    // --- Service (Business layer) ---
    static class ProductService {
        private final ProductRepository repo;
        ProductService(ProductRepository repo) { this.repo = repo; }  // constructor injection

        Product getOrThrow(int id) {
            return repo.findById(id)
                .orElseThrow(() -> new NoSuchElementException("Product not found: " + id));
        }
        List<Product> listAll() { return repo.findAll(); }
    }

    // --- Manual "application context" (Spring Framework without Boot auto-config) ---
    static ProductService createContext() {
        // In a real Spring project:
        //   @Configuration class AppConfig {
        //       @Bean ProductRepository repo() { return new InMemoryProductRepository(); }
        //       @Bean ProductService service() { return new ProductService(repo()); }
        //   }
        //   ApplicationContext ctx = new AnnotationConfigApplicationContext(AppConfig.class);
        ProductRepository repo = new InMemoryProductRepository();
        return new ProductService(repo);  // manual wiring — Boot would auto-configure this
    }

    public static void main(String[] args) {
        System.out.println("=== Spring Framework (no Boot) ===");
        ProductService svc = createContext();

        System.out.println("\nAll products:");
        svc.listAll().stream()
           .sorted(Comparator.comparingInt(Product::id))
           .forEach(p -> System.out.printf("  [%d] %-12s $%.2f%n", p.id(), p.name(), p.price()));

        System.out.println("\nFetch id=2: " + svc.getOrThrow(2));

        try { svc.getOrThrow(99); }
        catch (NoSuchElementException e) { System.out.println("Not found: " + e.getMessage()); }
    }
}
```

How to run: `java FrameworkOnlyDemo.java`

Pure Spring Framework is just a container. You declare beans and wire them — no embedded server, no auto-detection. The service and repository are testable POJOs.

### Level 2 — Intermediate

Now add what Spring Boot brings: auto-configured starters, `application.properties` values, and Actuator-style health (simulated).

```java
// BootStyleDemo.java — run with: java BootStyleDemo.java
// Simulates what Spring Boot auto-configuration does ON TOP of Framework.

import java.util.*;

public class BootStyleDemo {

    record Product(int id, String name, double price) {}

    interface ProductRepository {
        Optional<Product> findById(int id);
        List<Product> findAll();
    }

    static class InMemoryProductRepository implements ProductRepository {
        private final Map<Integer, Product> store = Map.of(
            1, new Product(1, "Laptop",  1299.99),
            2, new Product(2, "Monitor",  449.99)
        );
        public Optional<Product> findById(int id) { return Optional.ofNullable(store.get(id)); }
        public List<Product> findAll() { return new ArrayList<>(store.values()); }
    }

    static class ProductService {
        private final ProductRepository repo;
        ProductService(ProductRepository repo) { this.repo = repo; }
        Optional<Product> findById(int id) { return repo.findById(id); }
        List<Product> findAll() { return repo.findAll(); }
    }

    // Simulated Spring Boot starter auto-detection
    static class SpringBootAutoConfig {
        static String detectServer() { return "embedded-tomcat:8080"; }  // spring-boot-starter-web
        static String detectSerialization() { return "Jackson:auto-configured"; }  // jackson-databind on classpath
        static String detectActuator() { return "health:UP, info:enabled"; }  // spring-boot-actuator
    }

    // Simulated application.properties
    static class AppProperties {
        static String appName() { return "product-service"; }        // spring.application.name
        static int port() { return 8080; }                           // server.port
        static String logLevel() { return "INFO"; }                  // logging.level.root
    }

    // Simulated @RestController (the controller Boot wires automatically)
    static class ProductController {
        private final ProductService service;
        ProductController(ProductService svc) { this.service = svc; }

        // GET /products        → 200 + JSON array
        // GET /products/{id}   → 200 + JSON or 404
        String handleGet(String path) {
            if (path.equals("/products")) {
                return service.findAll().toString();
            }
            int id = Integer.parseInt(path.replace("/products/", ""));
            return service.findById(id)
                .map(Product::toString)
                .orElse("404 Not Found");
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Spring Boot Application Startup ===");
        System.out.println("  App:         " + AppProperties.appName());
        System.out.println("  Server:      " + SpringBootAutoConfig.detectServer());
        System.out.println("  JSON:        " + SpringBootAutoConfig.detectSerialization());
        System.out.println("  Actuator:    " + SpringBootAutoConfig.detectActuator());

        // Auto-configured context (in real Boot: @SpringBootApplication + component scan)
        ProductRepository repo = new InMemoryProductRepository();
        ProductService svc = new ProductService(repo);
        ProductController ctrl = new ProductController(svc);

        System.out.println("\n=== Handling Requests ===");
        System.out.println("GET /products       → " + ctrl.handleGet("/products"));
        System.out.println("GET /products/1     → " + ctrl.handleGet("/products/1"));
        System.out.println("GET /products/99    → " + ctrl.handleGet("/products/99"));

        System.out.println("\n=== What Boot added over bare Framework ===");
        System.out.println("  Framework alone: you write @Bean DataSource, @Bean EntityManager, @Bean TxManager");
        System.out.println("  Spring Boot:     detects JPA on classpath → wires all three automatically");
        System.out.println("  Framework alone: deploy WAR to Tomcat");
        System.out.println("  Spring Boot:     embedded Tomcat, run with 'java -jar app.jar'");
    }
}
```

How to run: `java BootStyleDemo.java`

Boot's auto-configuration replaced your `@Bean DataSource` / `@Bean EntityManagerFactory` declarations. The controller, service, and repository classes are identical; what changed is that you didn't have to declare the infrastructure beans.

### Level 3 — Advanced

Add an ecosystem project flavour — Spring Data-style repository (generic CRUD abstraction) plus a Spring Security-style filter, then compose them with Boot-style auto-configuration.

```java
// EcosystemDemo.java — run with: java EcosystemDemo.java
// Shows how Spring Data + Spring Security patterns sit on top of Boot + Framework.

import java.util.*;
import java.util.function.*;

public class EcosystemDemo {

    record Product(int id, String name, double price) {}

    // --- Spring Data style: generic CrudRepository<T, ID> ---
    interface CrudRepository<T, ID> {
        Optional<T> findById(ID id);
        List<T> findAll();
        T save(T entity);
    }

    static class ProductRepository implements CrudRepository<Product, Integer> {
        private final Map<Integer, Product> store = new LinkedHashMap<>(Map.of(
            1, new Product(1, "Laptop",  1299.99),
            2, new Product(2, "Monitor",  449.99)
        ));
        public Optional<Product> findById(Integer id) { return Optional.ofNullable(store.get(id)); }
        public List<Product> findAll() { return new ArrayList<>(store.values()); }
        public Product save(Product p) { store.put(p.id(), p); return p; }
    }

    // --- Spring Security style: security filter chain ---
    @FunctionalInterface interface SecurityFilter { boolean permit(String user, String role); }

    static class RoleBasedFilter implements SecurityFilter {
        private final Map<String, String> userRoles = Map.of("alice", "ADMIN", "bob", "USER");
        public boolean permit(String user, String role) {
            return role.equals(userRoles.getOrDefault(user, "NONE"));
        }
    }

    // --- Service layer (business logic) ---
    static class ProductService {
        private final CrudRepository<Product, Integer> repo;
        ProductService(CrudRepository<Product, Integer> repo) { this.repo = repo; }
        Optional<Product> findById(int id) { return repo.findById(id); }
        List<Product> findAll() { return repo.findAll(); }
        Product create(Product p, String user, SecurityFilter security) {
            if (!security.permit(user, "ADMIN")) throw new SecurityException("Access denied for " + user);
            return repo.save(p);
        }
    }

    // --- Simulated HTTP request handling ---
    record HttpRequest(String method, String path, String user) {}
    record HttpResponse(int status, String body) {
        @Override public String toString() { return status + " " + body; }
    }

    static class ProductController {
        private final ProductService svc;
        private final SecurityFilter security;
        ProductController(ProductService svc, SecurityFilter security) {
            this.svc = svc; this.security = security;
        }

        HttpResponse handle(HttpRequest req) {
            return switch (req.method() + " " + req.path()) {
                case "GET /products" -> new HttpResponse(200, svc.findAll().toString());
                case "GET /products/1" -> svc.findById(1)
                    .map(p -> new HttpResponse(200, p.toString()))
                    .orElse(new HttpResponse(404, "Not Found"));
                case "POST /products" -> {
                    try {
                        Product created = svc.create(
                            new Product(3, "Keyboard", 89.99), req.user(), security);
                        yield new HttpResponse(201, "Created: " + created);
                    } catch (SecurityException e) {
                        yield new HttpResponse(403, "Forbidden: " + e.getMessage());
                    }
                }
                default -> new HttpResponse(404, "Unknown path");
            };
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Spring Ecosystem Demo ===");
        System.out.println("  Spring Data    → generic CrudRepository<Product, Integer>");
        System.out.println("  Spring Security → RoleBasedFilter (permit by user/role)");
        System.out.println("  Spring Boot    → auto-wired context below");

        // Auto-wired by Boot; shown explicitly here
        ProductRepository repo = new ProductRepository();
        SecurityFilter security = new RoleBasedFilter();
        ProductService svc = new ProductService(repo);
        ProductController ctrl = new ProductController(svc, security);

        System.out.println("\n--- Requests ---");
        List<HttpRequest> requests = List.of(
            new HttpRequest("GET",  "/products",   "alice"),
            new HttpRequest("GET",  "/products/1", "bob"),
            new HttpRequest("POST", "/products",   "alice"),  // ADMIN — allowed
            new HttpRequest("POST", "/products",   "bob")     // USER  — denied
        );
        for (HttpRequest req : requests) {
            System.out.printf("  %-25s (user=%-5s) → %s%n",
                req.method() + " " + req.path(), req.user(), ctrl.handle(req));
        }

        System.out.println("\n--- Data state after POST (Spring Data save) ---");
        repo.findAll().forEach(p ->
            System.out.printf("  [%d] %-12s $%.2f%n", p.id(), p.name(), p.price()));
    }
}
```

How to run: `java EcosystemDemo.java`

`CrudRepository` mirrors Spring Data's interface. `RoleBasedFilter` mirrors Spring Security's filter chain. In a real Boot app both are provided as auto-configured beans; you implement the interfaces, not the infrastructure.

## 6. Walkthrough

**Level 1:** `createContext()` manually creates `InMemoryProductRepository` and passes it to `ProductService`'s constructor. This mirrors what an `@Configuration` class does in Spring Framework. `findAll()` returns the in-memory map; `getOrThrow` throws `NoSuchElementException` for missing IDs — standard framework code.

**Level 2:** `SpringBootAutoConfig.detectServer()` and friends simulate the classpath scanning Boot does at startup. In a real Boot app this happens via `@ConditionalOnClass(Tomcat.class)` — if the Tomcat class is on the classpath, `TomcatServletWebServerFactory` is registered. Boot wires `ProductController` → `ProductService` → `InMemoryProductRepository` automatically because `@Controller` and `@Service` are discovered via component-scan.

**Level 3 — request/response flow (POST /products, user=alice):**

```
HttpRequest("POST", "/products", "alice")
  → ProductController.handle(req)
  → switch → "POST /products" branch
  → ProductService.create(new Product(3, "Keyboard", 89.99), "alice", security)
  → RoleBasedFilter.permit("alice", "ADMIN")
      userRoles.get("alice") = "ADMIN" → true
  → ProductRepository.save(Product(3, "Keyboard", 89.99))
      store.put(3, ...) → Product(3, "Keyboard", 89.99) returned
  → HttpResponse(201, "Created: Product[id=3, name=Keyboard, price=89.99]")

HttpRequest("POST", "/products", "bob")
  → RoleBasedFilter.permit("bob", "ADMIN")
      userRoles.get("bob") = "USER" → false
  → SecurityException("Access denied for bob")
  → HttpResponse(403, "Forbidden: ...")
```

The data state after the ADMIN POST shows three products — the keyboard was persisted. The USER POST left the store unchanged.

## 7. Gotchas & takeaways

> **"Spring" means different things in different contexts.** When a job posting says "Spring experience required" they usually mean Spring Boot + Spring MVC + Spring Data. When a library's README says "requires Spring Framework 6.x" they mean the core JARs. Knowing the distinction prevents wiring-level confusion.

> **Adding a Spring ecosystem starter auto-configures the whole module.** Adding `spring-boot-starter-data-jpa` doesn't just add JPA — Boot auto-configures a `DataSource` (from `application.properties`), `EntityManagerFactory`, `JpaTransactionManager`, and all Spring Data repositories in your package. If you don't have a database configured, Boot fails fast at startup with a clear error. This is intentional: fail early, not silently.

- Boot's auto-configuration is conditional: it backs off if you provide your own bean. `@ConditionalOnMissingBean` means "auto-configure only if the user hasn't declared this bean type already."
- Spring Data repositories are interfaces — you declare `interface ProductRepository extends JpaRepository<Product, Long>` and Spring Data generates the implementation at runtime.
- Spring Security is opt-in but once added secures every endpoint by default. Add it intentionally; not adding it means no security.
- Spring Cloud requires a running infrastructure (Eureka, Consul, Vault, etc.). Don't add Cloud starters unless you have the corresponding infrastructure.
- The spring.io/projects page is the authoritative list of all Spring ecosystem projects with their current status and documentation.
