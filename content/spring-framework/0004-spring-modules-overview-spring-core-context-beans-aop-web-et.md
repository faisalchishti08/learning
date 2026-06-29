---
card: spring-framework
gi: 4
slug: spring-modules-overview-spring-core-context-beans-aop-web-et
title: Spring modules overview (spring-core, -context, -beans, -aop, -web, etc.)
---

## 1. What it is

Spring Framework ships as a set of focused Maven/Gradle modules (JARs). Each module depends on lower-level ones, forming a directed acyclic graph. You include only the modules your application needs.

**Core group** — the mandatory foundation:

| Module | Purpose |
|---|---|
| `spring-core` | Utilities, resource loading, type conversion, `@Nullable` |
| `spring-beans` | `BeanFactory`, bean definitions, property editors |
| `spring-context` | `ApplicationContext`, event publishing, EL, scheduling, i18n |
| `spring-expression` | Spring Expression Language (SpEL) |

**AOP & Instrumentation:**

| Module | Purpose |
|---|---|
| `spring-aop` | Proxy-based AOP: `@Aspect`, pointcuts, advice |
| `spring-aspects` | Integration with AspectJ (compile-time / load-time weaving) |
| `spring-instrument` | JVM agent for load-time weaving |

**Data access:**

| Module | Purpose |
|---|---|
| `spring-jdbc` | `JdbcTemplate`, `NamedParameterJdbcTemplate`, `DataSourceUtils` |
| `spring-tx` | `@Transactional`, `TransactionManager`, programmatic TX |
| `spring-orm` | JPA, Hibernate, MyBatis integration (`LocalEntityManagerFactoryBean`) |
| `spring-oxm` | Object/XML mapping (JAXB, Castor) |
| `spring-jms` | JMS template, listener container |

**Web:**

| Module | Purpose |
|---|---|
| `spring-web` | `HttpMessageConverter`, `RestTemplate`, multipart, web utilities |
| `spring-webmvc` | `DispatcherServlet`, `@Controller`, `@RequestMapping`, view resolvers |
| `spring-webflux` | Reactive web: `RouterFunction`, `WebClient`, Reactor-based |
| `spring-websocket` | WebSocket and SockJS support |
| `spring-messaging` | STOMP messaging, `@MessageMapping` |

**Test:**

| Module | Purpose |
|---|---|
| `spring-test` | `@SpringBootTest`, `MockMvc`, `@MockBean`, context caching |

## 2. Why & when

The modular design means you don't pay the weight of unused modules. A batch job needs `spring-context` + `spring-jdbc` + `spring-tx` but not `spring-webmvc`. A reactive API needs `spring-webflux` but not `spring-webmvc`.

Spring Boot's starters take care of module selection automatically:
- `spring-boot-starter-web` → `spring-webmvc` + `spring-web` + `spring-context` + Jackson + Tomcat.
- `spring-boot-starter-webflux` → `spring-webflux` + `spring-web` + Reactor Netty.
- `spring-boot-starter-data-jpa` → `spring-orm` + `spring-tx` + `spring-jdbc` + Hibernate.

When not using Boot, you add modules manually — knowing the module graph prevents missing transitive dependencies.

## 3. Core concept

The module dependency order (simplified):

```
spring-core
   └─ spring-beans
         └─ spring-context     (pulls spring-aop + spring-expression)
               ├─ spring-webmvc   (needs spring-web)
               ├─ spring-webflux  (needs spring-web)
               ├─ spring-jdbc     (needs spring-tx)
               └─ spring-orm      (needs spring-jdbc + spring-tx)
```

`spring-core` is the only module with no Spring dependencies. It provides:
- `Resource` abstraction (classpath, file, URL resources).
- `BeanWrapper` / type conversion.
- `@Nullable`, `@NonNull` annotations.
- `ReflectionUtils`, `ClassUtils`, `StringUtils`.

`spring-beans` builds on `core` and introduces `BeanFactory` — the minimal IoC container interface.

`spring-context` builds on `beans` and introduces `ApplicationContext` — the full container with event publishing, i18n, lifecycle hooks, and AOP integration.

Everything else (`spring-webmvc`, `spring-jdbc`, `spring-orm`) builds on `context` and adds domain-specific functionality.

## 4. Diagram

<svg viewBox="0 0 700 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring module dependency graph from spring-core up through web and data modules">
  <defs>
    <marker id="ma" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- spring-core -->
  <rect x="270" y="10" width="160" height="38" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="34" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">spring-core</text>

  <!-- spring-beans -->
  <rect x="270" y="72" width="160" height="38" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="96" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">spring-beans</text>

  <!-- spring-context -->
  <rect x="270" y="134" width="160" height="38" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="350" y="158" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">spring-context</text>

  <!-- spring-aop -->
  <rect x="80" y="134" width="145" height="38" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="152" y="158" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">spring-aop</text>

  <!-- spring-expression -->
  <rect x="475" y="134" width="165" height="38" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="557" y="158" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">spring-expression</text>

  <!-- spring-web -->
  <rect x="130" y="210" width="130" height="38" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="195" y="234" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">spring-web</text>

  <!-- spring-webmvc -->
  <rect x="10" y="265" width="145" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="82" y="284" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">spring-webmvc</text>

  <!-- spring-webflux -->
  <rect x="165" y="265" width="145" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="237" y="284" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">spring-webflux</text>

  <!-- spring-jdbc/tx/orm -->
  <rect x="335" y="210" width="130" height="38" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="400" y="228" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">spring-jdbc</text>
  <text x="400" y="243" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ spring-tx</text>

  <rect x="480" y="210" width="130" height="38" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="545" y="234" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">spring-orm</text>

  <!-- Arrows -->
  <line x1="350" y1="48"  x2="350" y2="70"  stroke="#6db33f" stroke-width="1.5" marker-end="url(#ma)"/>
  <line x1="350" y1="110" x2="350" y2="132" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ma)"/>
  <line x1="270" y1="153" x2="227" y2="153" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ma)"/>
  <line x1="430" y1="153" x2="473" y2="153" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ma)"/>
  <line x1="310" y1="172" x2="230" y2="208" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ma)"/>
  <line x1="370" y1="172" x2="380" y2="208" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ma)"/>
  <line x1="430" y1="172" x2="510" y2="208" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ma)"/>
  <line x1="160" y1="248" x2="100" y2="263" stroke="#8b949e" stroke-width="1" marker-end="url(#ma)"/>
  <line x1="220" y1="248" x2="250" y2="263" stroke="#8b949e" stroke-width="1" marker-end="url(#ma)"/>
</svg>

`spring-core` is the only leaf. Everything else builds upward through the graph.

## 5. Runnable example

We'll build a product-lookup app that deliberately shows each module's contribution layer by layer.

### Level 1 — Basic

`spring-core` and `spring-beans` concerns only: resource loading and type conversion.

```java
// ModulesDemo.java — run with: java ModulesDemo.java
// Demonstrates spring-core utilities that every other module depends on.

import java.util.*;

public class ModulesDemo {

    // spring-core: Resource abstraction (simplified)
    sealed interface Resource permits ClasspathResource, FileResource {}
    record ClasspathResource(String path) implements Resource {}
    record FileResource(String path) implements Resource {}

    static String loadContent(Resource r) {
        return switch (r) {
            case ClasspathResource(var p) -> "[CLASSPATH] " + p + " loaded";
            case FileResource(var p)      -> "[FILE]      " + p + " loaded";
        };
    }

    // spring-core: Type conversion (PropertyEditor style)
    static int toInt(String s, int defaultVal) {
        try { return Integer.parseInt(s.trim()); }
        catch (NumberFormatException e) { return defaultVal; }
    }

    // spring-beans: BeanWrapper-style property binding
    record ServerConfig(String host, int port, boolean ssl) {}

    static ServerConfig bindProperties(Map<String, String> props) {
        return new ServerConfig(
            props.getOrDefault("server.host", "localhost"),
            toInt(props.getOrDefault("server.port", "8080"), 8080),
            Boolean.parseBoolean(props.getOrDefault("server.ssl", "false"))
        );
    }

    public static void main(String[] args) {
        System.out.println("=== spring-core: Resource loading ===");
        System.out.println(loadContent(new ClasspathResource("application.properties")));
        System.out.println(loadContent(new FileResource("/etc/config/app.yaml")));

        System.out.println("\n=== spring-core: Type conversion ===");
        System.out.println("'8080' → " + toInt("8080", 0));
        System.out.println("'bad'  → " + toInt("bad", 9090) + " (default used)");

        System.out.println("\n=== spring-beans: Property binding ===");
        Map<String, String> props = Map.of(
            "server.host", "api.example.com",
            "server.port", "443",
            "server.ssl",  "true"
        );
        System.out.println(bindProperties(props));
    }
}
```

How to run: `java ModulesDemo.java`

`spring-core`'s `Resource` hierarchy lets code handle classpath resources and file-system resources uniformly. `toInt` mirrors `PropertyEditor` type conversion. `bindProperties` mirrors `BeanWrapper`'s property binding — what `@ConfigurationProperties` does internally.

### Level 2 — Intermediate

Add `spring-context` concerns: event publishing, bean lifecycle, and `@Value`-style property resolution.

```java
// ModulesDemoV2.java — run with: java ModulesDemoV2.java
// Adds spring-context: events, lifecycle callbacks, property resolution.

import java.util.*;
import java.util.function.Consumer;

public class ModulesDemoV2 {

    // --- spring-context: ApplicationEvent ---
    sealed interface AppEvent permits OrderPlaced, OrderShipped {}
    record OrderPlaced(int orderId, String customer) implements AppEvent {}
    record OrderShipped(int orderId, String trackingId) implements AppEvent {}

    // --- spring-context: ApplicationListener ---
    @FunctionalInterface interface EventListener<E extends AppEvent> {
        void onEvent(E event);
    }

    // --- spring-context: ApplicationEventPublisher ---
    static class EventPublisher {
        private final Map<Class<?>, List<Consumer<AppEvent>>> listeners = new HashMap<>();

        @SuppressWarnings("unchecked")
        <E extends AppEvent> void register(Class<E> type, EventListener<E> listener) {
            listeners.computeIfAbsent(type, k -> new ArrayList<>())
                .add(e -> listener.onEvent((E) e));
        }

        void publish(AppEvent event) {
            listeners.getOrDefault(event.getClass(), List.of())
                .forEach(l -> l.accept(event));
        }
    }

    // --- spring-context: @PostConstruct / @PreDestroy lifecycle ---
    static class CacheService {
        private final Map<Integer, String> cache = new HashMap<>();

        void init() {                           // @PostConstruct
            System.out.println("[CacheService] Warming up cache...");
            cache.put(1, "Laptop");
            cache.put(2, "Monitor");
        }

        Optional<String> get(int id) { return Optional.ofNullable(cache.get(id)); }

        void destroy() {                        // @PreDestroy
            System.out.println("[CacheService] Evicting cache...");
            cache.clear();
        }
    }

    public static void main(String[] args) {
        System.out.println("=== spring-context: Event publishing ===");
        EventPublisher publisher = new EventPublisher();

        publisher.register(OrderPlaced.class,  e -> System.out.println("  EMAIL: order " + e.orderId() + " placed for " + e.customer()));
        publisher.register(OrderPlaced.class,  e -> System.out.println("  AUDIT: new order " + e.orderId()));
        publisher.register(OrderShipped.class, e -> System.out.println("  SMS:   order " + e.orderId() + " shipped, track=" + e.trackingId()));

        publisher.publish(new OrderPlaced(42, "alice@example.com"));
        publisher.publish(new OrderShipped(42, "TRK-9900"));

        System.out.println("\n=== spring-context: Bean lifecycle (@PostConstruct/@PreDestroy) ===");
        CacheService cache = new CacheService();
        cache.init();  // Spring calls this after bean is fully wired
        System.out.println("  Cache lookup 1: " + cache.get(1));
        System.out.println("  Cache lookup 9: " + cache.get(9));
        cache.destroy();  // Spring calls this before context closes

        System.out.println("\n=== spring-expression: SpEL property resolution ===");
        Map<String, Object> env = Map.of("app.name", "order-service", "max.threads", 10);
        // @Value("${app.name}") → "order-service"
        // @Value("#{max.threads * 2}") → 20
        System.out.println("  ${app.name}          → " + env.get("app.name"));
        System.out.println("  #{max.threads * 2}   → " + (int)env.get("max.threads") * 2);
    }
}
```

How to run: `java ModulesDemoV2.java`

`EventPublisher` mirrors `ApplicationEventPublisher`. `init()` / `destroy()` mirror `@PostConstruct` / `@PreDestroy`. SpEL's `#{}` syntax is shown as property-resolution.

### Level 3 — Advanced

Full module stack: `spring-webmvc` request handling, `spring-jdbc`-style template, `spring-tx` transaction boundary, `spring-aop` logging advice — all composing through the container.

```java
// ModulesDemoV3.java — run with: java ModulesDemoV3.java
// Adds spring-webmvc, spring-jdbc template, spring-tx, spring-aop advice.

import java.util.*;
import java.util.function.*;

public class ModulesDemoV3 {

    record Product(int id, String name, double price) {}

    // --- spring-jdbc: JdbcTemplate style ---
    static class ProductJdbcTemplate {
        private final Map<Integer, Product> db = new LinkedHashMap<>(Map.of(
            1, new Product(1, "Laptop",  1299.99),
            2, new Product(2, "Monitor",  449.99)
        ));
        Optional<Product> queryForObject(int id) { return Optional.ofNullable(db.get(id)); }
        List<Product> query() { return new ArrayList<>(db.values()); }
        void update(int id, double price) {
            db.compute(id, (k, p) -> p == null ? null : new Product(k, p.name(), price));
        }
    }

    // --- spring-tx: Transaction boundary ---
    static class TransactionManager {
        <T> T execute(Supplier<T> work) {
            System.out.println("  [TX] BEGIN");
            try {
                T result = work.get();
                System.out.println("  [TX] COMMIT");
                return result;
            } catch (Exception e) {
                System.out.println("  [TX] ROLLBACK — " + e.getMessage());
                throw e;
            }
        }
    }

    // --- spring-aop: MethodInterceptor proxy ---
    static class LoggingAdvice {
        static <T> T around(String methodName, Supplier<T> target) {
            System.out.println("  [AOP BEFORE] " + methodName);
            T result = target.get();
            System.out.println("  [AOP AFTER]  " + methodName + " returned " + result);
            return result;
        }
    }

    // --- spring-webmvc: @RestController handler ---
    record HttpRequest(String method, String path) {}
    record HttpResponse(int status, String body) {
        @Override public String toString() { return "HTTP " + status + ": " + body; }
    }

    static class ProductController {
        private final ProductJdbcTemplate jdbc;
        private final TransactionManager tx;

        ProductController(ProductJdbcTemplate jdbc, TransactionManager tx) {
            this.jdbc = jdbc; this.tx = tx;
        }

        // GET /products
        HttpResponse getAll() {
            return LoggingAdvice.around("getAll", () ->
                new HttpResponse(200, jdbc.query().toString()));
        }

        // GET /products/{id}
        HttpResponse getById(int id) {
            return LoggingAdvice.around("getById(" + id + ")", () ->
                jdbc.queryForObject(id)
                    .map(p -> new HttpResponse(200, p.toString()))
                    .orElse(new HttpResponse(404, "Product " + id + " not found")));
        }

        // PUT /products/{id}/price  — transactional
        HttpResponse updatePrice(int id, double newPrice) {
            return tx.execute(() ->
                LoggingAdvice.around("updatePrice(" + id + "," + newPrice + ")", () -> {
                    jdbc.update(id, newPrice);
                    return jdbc.queryForObject(id)
                        .map(p -> new HttpResponse(200, "Updated: " + p))
                        .orElse(new HttpResponse(404, "Not found"));
                }));
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Full Spring Module Stack Demo ===\n");

        // spring-beans + spring-context: wiring (Boot would auto-configure these)
        ProductJdbcTemplate jdbc = new ProductJdbcTemplate();
        TransactionManager tx = new TransactionManager();
        ProductController ctrl = new ProductController(jdbc, tx);

        System.out.println("--- GET /products ---");
        System.out.println(ctrl.getAll());

        System.out.println("\n--- GET /products/1 ---");
        System.out.println(ctrl.getById(1));

        System.out.println("\n--- GET /products/99 ---");
        System.out.println(ctrl.getById(99));

        System.out.println("\n--- PUT /products/1/price?value=999.99 ---");
        System.out.println(ctrl.updatePrice(1, 999.99));

        System.out.println("\n--- GET /products/1 (after price update) ---");
        System.out.println(ctrl.getById(1));

        System.out.println("\n=== Module responsibilities ===");
        System.out.println("  spring-core:    Resource, type conversion, reflection utils");
        System.out.println("  spring-beans:   BeanFactory, property binding");
        System.out.println("  spring-context: ApplicationContext, events, lifecycle");
        System.out.println("  spring-aop:     LoggingAdvice (before/after), @Transactional proxy");
        System.out.println("  spring-jdbc:    JdbcTemplate (SQL + result mapping)");
        System.out.println("  spring-tx:      TransactionManager (begin/commit/rollback)");
        System.out.println("  spring-webmvc:  ProductController (HTTP → Java method)");
    }
}
```

How to run: `java ModulesDemoV3.java`

Each module's seam is visible: AOP advice wraps controller methods; the transaction wraps the `updatePrice` unit of work; `JdbcTemplate` hides raw SQL machinery; `spring-webmvc`'s `DispatcherServlet` (simulated here) routes HTTP to controller methods.

## 6. Walkthrough

**Entry point — `main`:** Wires `jdbc → tx → ctrl`. In a real Boot app `@SpringBootApplication` triggers component scan; `ProductJdbcTemplate`, `TransactionManager`, and `ProductController` are all `@Component` or `@Bean`, wired automatically.

**GET /products:** `ctrl.getAll()` enters `LoggingAdvice.around` (the AOP before-advice fires, logging `[AOP BEFORE] getAll`). Then `jdbc.query()` returns all products from the in-memory map. The result is wrapped in `HttpResponse(200, ...)` and returned to `LoggingAdvice.around` (after-advice fires). The entire call is **not** transactional — read-only queries typically don't need a transaction boundary.

**PUT /products/1/price:** `ctrl.updatePrice(1, 999.99)` first enters `tx.execute` (the `[TX] BEGIN` log). Inside the transaction, AOP advice wraps `updatePrice(1,999.99)`. `jdbc.update(1, 999.99)` modifies the in-memory store. `jdbc.queryForObject(1)` reads the updated product. The supplier returns `HttpResponse(200, "Updated: ...")`. `tx.execute` commits (`[TX] COMMIT`). If `update` threw a `RuntimeException`, the transaction block would catch it and log `ROLLBACK`.

**State change:**

```
Before PUT:  Product[id=1, name=Laptop, price=1299.99]
After PUT:   Product[id=1, name=Laptop, price=999.99]
```

`GET /products/1` after the update confirms the new price.

**In real Spring:**
- `spring-aop` creates a proxy around `ProductController`; `@Around` advice runs `LoggingAdvice`.
- `@Transactional` on `updatePrice` tells `TransactionInterceptor` (another AOP advice) to call `PlatformTransactionManager.getTransaction()`, run the method, then `commit()` or `rollback()`.
- `JdbcTemplate` uses a `DataSource` (auto-configured by Boot if `spring.datasource.url` is set) and `DataSourceUtils.getConnection()` to participate in the active transaction automatically.

## 7. Gotchas & takeaways

> **`spring-webmvc` and `spring-webflux` are mutually exclusive as the primary web layer.** You can have both JARs on the classpath (some libraries depend on `spring-web`), but you must choose one `DispatcherServlet` (MVC) or one `HttpHandler` chain (WebFlux) as your request-handling entry point. Boot auto-configures the correct one based on which starter you add.

> **`spring-aop` uses JDK dynamic proxies for interfaces and CGLIB for classes.** If you call a `@Transactional` method on `this` inside the same class, the proxy is bypassed — the advice never fires. Always inject the proxy (let Spring inject `this`'s proxy via `@Autowired`) or use `@Scope("prototype")` + self-injection workarounds.

- `spring-test` is the most underused module: `@SpringBootTest` brings up the real context in tests; `MockMvc` sends HTTP requests to the `DispatcherServlet` in memory; `@MockBean` replaces a Spring bean with a Mockito mock for the test.
- `spring-tx` is not exclusive to JDBC: it abstracts over JDBC, JPA, JMS, and custom `PlatformTransactionManager` implementations uniformly via `@Transactional`.
- Module versions are locked together: never mix different Spring Framework versions (e.g., `spring-core:6.1.0` + `spring-webmvc:6.0.11`). Use the Spring BOM to ensure all modules are at the same version.
- `spring-expression` (SpEL) is used internally by Spring Security, Spring Data, and Spring Cache — you use it indirectly even when you don't write `#{}` expressions yourself.
