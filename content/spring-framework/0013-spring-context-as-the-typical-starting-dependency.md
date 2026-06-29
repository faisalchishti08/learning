---
card: spring-framework
gi: 13
slug: spring-context-as-the-typical-starting-dependency
title: spring-context as the typical starting dependency
---

## 1. What it is

`spring-context` is the module that provides the full **`ApplicationContext`** — Spring's primary IoC container. When you use Spring Framework directly (not through Spring Boot), `spring-context` is the one dependency you almost always add first: it pulls in the entire core Spring stack through its transitive dependencies.

**Maven:**
```xml
<dependency>
    <groupId>org.springframework</groupId>
    <artifactId>spring-context</artifactId>
    <version>6.1.4</version>
</dependency>
```

**Gradle:**
```kotlin
implementation("org.springframework:spring-context:6.1.4")
```

What `spring-context` pulls in transitively:

```
spring-context:6.1.4
  └── spring-aop:6.1.4         (AOP support for @Transactional, @Async, @Cacheable)
  └── spring-beans:6.1.4       (BeanFactory, BeanDefinition, property binding)
  └── spring-core:6.1.4        (Resource loading, type conversion, reflection utils)
  └── spring-expression:6.1.4  (SpEL — @Value("#{...}"), @ConditionalOnExpression)
```

If you're using Spring Boot, `spring-boot-starter` already includes `spring-context` — you don't add it separately. `spring-context` as an explicit direct dependency is for non-Boot Spring projects: libraries, batch jobs, CLI tools, or integration with other frameworks.

## 2. Why & when

`spring-context` gives you exactly the `ApplicationContext`, nothing more. No embedded servlet container, no web layer, no JPA. It's the right choice when:

- **Building a library** that wants to be Spring-compatible (provide beans, honour `@PostConstruct`) without forcing a web server on users.
- **Writing a batch/CLI application** that needs DI and transactions but not HTTP.
- **Integrating Spring into an existing non-Spring project** — add the container, wire your existing classes into it without pulling in MVC or Boot.
- **Testing outside Boot** — a `@Configuration` class loaded with `AnnotationConfigApplicationContext` needs only `spring-context`.

If you need web endpoints: add `spring-webmvc` (Servlet-based) or `spring-webflux` (reactive) — both depend on `spring-context` transitively. If you need JDBC: add `spring-jdbc` — also depends on `spring-context`. So `spring-context` is the floor, not the ceiling.

## 3. Core concept

`ApplicationContext` extends `BeanFactory` (from `spring-beans`) and adds:

| Capability | Provided by | Example |
|---|---|---|
| Bean creation & DI | `spring-beans` + `spring-core` | `@Component`, `@Autowired` |
| AOP proxy creation | `spring-aop` | `@Transactional`, `@Aspect` |
| Event publishing | `spring-context` | `ApplicationEventPublisher` |
| i18n / MessageSource | `spring-context` | `MessageSource.getMessage(...)` |
| Resource loading | `spring-core` | `@Value("classpath:config.yaml")` |
| Environment & Profiles | `spring-context` | `@Profile`, `@PropertySource` |
| Lifecycle callbacks | `spring-context` | `@PostConstruct`, `@PreDestroy` |
| SpEL | `spring-expression` | `@Value("#{bean.property}")` |

**Three ways to bootstrap `ApplicationContext`:**

```java
// 1. Annotation-based (most common in Spring 6.x):
ApplicationContext ctx = new AnnotationConfigApplicationContext(AppConfig.class);

// 2. Component-scan only (no explicit @Bean methods):
ApplicationContext ctx = new AnnotationConfigApplicationContext("com.example.app");

// 3. XML (legacy):
ApplicationContext ctx = new ClassPathXmlApplicationContext("applicationContext.xml");
```

All three build the same container; only the metadata source differs.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="spring-context module and its transitive dependencies, plus the capabilities each module adds">
  <defs>
    <marker id="ca" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- spring-context centre -->
  <rect x="250" y="80" width="200" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="350" y="106" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">spring-context</text>
  <text x="350" y="124" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ApplicationContext</text>
  <text x="350" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Events · i18n · Profiles · @PostConstruct</text>

  <!-- spring-core -->
  <rect x="10" y="10" width="175" height="55" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="97" y="32" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">spring-core</text>
  <text x="97" y="50" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Resource · TypeConversion · Utils</text>

  <!-- spring-beans -->
  <rect x="200" y="10" width="170" height="55" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="285" y="32" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">spring-beans</text>
  <text x="285" y="50" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">BeanFactory · Property binding</text>

  <!-- spring-aop -->
  <rect x="390" y="10" width="160" height="55" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="32" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">spring-aop</text>
  <text x="470" y="50" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Proxy · @Transactional · Advisors</text>

  <!-- spring-expression -->
  <rect x="565" y="10" width="125" height="55" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="627" y="32" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">spring-expression</text>
  <text x="627" y="50" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">SpEL · @Value("#{}")</text>

  <!-- Arrows (transitive deps flow into spring-context) -->
  <line x1="97"  y1="65" x2="270" y2="82" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ca)"/>
  <line x1="285" y1="65" x2="310" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ca)"/>
  <line x1="470" y1="65" x2="400" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ca)"/>
  <line x1="627" y1="65" x2="435" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ca)"/>

  <!-- What you can do box -->
  <rect x="100" y="170" width="500" height="48" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="350" y="190" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">One dependency, full container: @Component · @Autowired · @Bean · @Profile · @EventListener</text>
  <text x="350" y="208" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">No web server, no JPA — add spring-webmvc / spring-jdbc if needed</text>

  <line x1="350" y1="150" x2="350" y2="168" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ca)"/>
</svg>

One dependency covers the entire IoC core — web and data modules are optional additions.

## 5. Runnable example

A product notification service using only `spring-context` patterns — no Boot, no MVC, no database.

### Level 1 — Basic

The simplest `ApplicationContext` bootstrap: one `@Configuration` class, two beans, DI.

```java
// SpringContextDemo.java — run with: java SpringContextDemo.java
// Demonstrates spring-context capabilities without Spring Boot or a servlet container.

import java.util.*;

public class SpringContextDemo {

    // === @Configuration class (metadata for the container) ===
    // In a real project these would be separate files with Spring annotations.
    // Here we simulate the container's behaviour.

    record Product(int id, String name, double price) {}

    // @Repository bean
    static class ProductRepository {
        private final Map<Integer, Product> store = Map.of(
            1, new Product(1, "Laptop",  1299.99),
            2, new Product(2, "Monitor",  449.99)
        );
        Optional<Product> findById(int id) { return Optional.ofNullable(store.get(id)); }
        List<Product> findAll() { return new ArrayList<>(store.values()); }
    }

    // @Service bean — depends on ProductRepository
    static class ProductService {
        private final ProductRepository repo;

        // Constructor injection — no @Autowired needed on single constructor in Spring 4.3+
        ProductService(ProductRepository repo) { this.repo = repo; }

        void printAll() {
            System.out.println("All products:");
            repo.findAll().stream()
               .sorted(Comparator.comparingInt(Product::id))
               .forEach(p -> System.out.printf("  [%d] %-12s $%.2f%n", p.id(), p.name(), p.price()));
        }

        Optional<Product> find(int id) { return repo.findById(id); }
    }

    // @Configuration + @Bean factory methods
    static class AppConfig {
        ProductRepository productRepository() { return new ProductRepository(); }
        ProductService productService() { return new ProductService(productRepository()); }
    }

    // AnnotationConfigApplicationContext bootstrap (simulated)
    static class MiniApplicationContext {
        private final Map<Class<?>, Object> beans = new HashMap<>();

        void register(AppConfig config) {
            beans.put(ProductRepository.class, config.productRepository());
            beans.put(ProductService.class, config.productService());
            System.out.println("[Context] Initialised " + beans.size() + " beans");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) { return (T) beans.get(type); }
    }

    public static void main(String[] args) {
        System.out.println("=== spring-context: minimal ApplicationContext ===\n");

        // In a real Spring project:
        //   ApplicationContext ctx = new AnnotationConfigApplicationContext(AppConfig.class);
        //   ProductService svc = ctx.getBean(ProductService.class);
        MiniApplicationContext ctx = new MiniApplicationContext();
        ctx.register(new AppConfig());

        ProductService svc = ctx.getBean(ProductService.class);
        svc.printAll();

        System.out.println("\nFind id=1: " + svc.find(1));
        System.out.println("Find id=9: " + svc.find(9));
    }
}
```

How to run: `java SpringContextDemo.java`

`MiniApplicationContext.register()` mirrors what `AnnotationConfigApplicationContext(AppConfig.class)` does: instantiate beans in dependency order, wire them via constructor arguments, and store in the container. `getBean(ProductService.class)` retrieves the already-wired singleton.

### Level 2 — Intermediate

Add application events, `@PostConstruct`/`@PreDestroy` lifecycle, and `@Profile`-based bean selection.

```java
// SpringContextV2.java — run with: java SpringContextV2.java
// Adds: events, lifecycle callbacks, profile-aware configuration.

import java.util.*;
import java.util.function.Consumer;

public class SpringContextV2 {

    record Product(int id, String name, double price) {}

    // === ApplicationEvent ===
    sealed interface ProductEvent permits ProductCreated, ProductDeleted {}
    record ProductCreated(Product product) implements ProductEvent {}
    record ProductDeleted(int productId)   implements ProductEvent {}

    // === ApplicationEventPublisher ===
    static class EventBus {
        private final Map<Class<?>, List<Consumer<Object>>> listeners = new HashMap<>();

        @SuppressWarnings("unchecked")
        <E> void on(Class<E> type, Consumer<E> listener) {
            listeners.computeIfAbsent(type, k -> new ArrayList<>())
                .add(e -> listener.accept((E) e));
        }
        void publish(Object event) {
            listeners.getOrDefault(event.getClass(), List.of()).forEach(l -> l.accept(event));
        }
    }

    // === @Service with lifecycle callbacks ===
    static class ProductCacheService {
        private Map<Integer, Product> cache;
        private final EventBus events;

        ProductCacheService(EventBus events) { this.events = events; }

        // @PostConstruct — called after all dependencies are injected
        void init() {
            System.out.println("[PostConstruct] Warming product cache...");
            cache = new HashMap<>(Map.of(
                1, new Product(1, "Laptop",  1299.99),
                2, new Product(2, "Monitor",  449.99)
            ));

            // Listen for events (Spring: @EventListener)
            events.on(ProductCreated.class, e -> {
                cache.put(e.product().id(), e.product());
                System.out.println("[Cache] Added: " + e.product().name());
            });
            events.on(ProductDeleted.class, e -> {
                cache.remove(e.productId());
                System.out.println("[Cache] Removed: id=" + e.productId());
            });
        }

        Optional<Product> get(int id) { return Optional.ofNullable(cache.get(id)); }
        List<Product> all() { return new ArrayList<>(cache.values()); }

        // @PreDestroy — called before context closes
        void destroy() {
            System.out.println("[PreDestroy] Evicting cache (" + cache.size() + " entries)");
            cache.clear();
        }
    }

    // === Profile-aware service ===
    // @Profile("dev"):
    static class DevProductService {
        String describe() { return "DEV: using in-memory data"; }
    }
    // @Profile("prod"):
    static class ProdProductService {
        String describe() { return "PROD: using PostgreSQL via JdbcTemplate"; }
    }

    public static void main(String[] args) {
        System.out.println("=== spring-context: Events + Lifecycle + Profiles ===\n");

        EventBus events = new EventBus();
        ProductCacheService cache = new ProductCacheService(events);
        cache.init();  // @PostConstruct

        System.out.println("\n--- Initial state ---");
        cache.all().stream()
             .sorted(Comparator.comparingInt(Product::id))
             .forEach(p -> System.out.println("  " + p));

        System.out.println("\n--- Publishing events ---");
        events.publish(new ProductCreated(new Product(3, "Keyboard", 89.99)));
        events.publish(new ProductDeleted(2));

        System.out.println("\n--- State after events ---");
        cache.all().stream()
             .sorted(Comparator.comparingInt(Product::id))
             .forEach(p -> System.out.println("  " + p));

        System.out.println("\n--- Profile-aware beans ---");
        String activeProfile = System.getProperty("spring.profiles.active", "dev");
        Object svc = "prod".equals(activeProfile) ? new ProdProductService() : new DevProductService();
        System.out.println("Active profile: " + activeProfile);
        if (svc instanceof DevProductService d) System.out.println("Service: " + d.describe());
        if (svc instanceof ProdProductService p) System.out.println("Service: " + p.describe());

        System.out.println("\n--- Context close ---");
        cache.destroy();  // @PreDestroy
    }
}
```

How to run: `java SpringContextV2.java` (or `java -Dspring.profiles.active=prod SpringContextV2.java`)

`init()` mirrors `@PostConstruct`: called once after all dependencies are injected. `destroy()` mirrors `@PreDestroy`: called when `ctx.close()` is invoked (in tests: `try (var ctx = new AnnotationConfigApplicationContext(...))` — the `try-with-resources` calls `close()`). Profile selection shows how `@Profile("dev")` / `@Profile("prod")` controls which implementation the container registers.

### Level 3 — Advanced

Full `spring-context`-only application: hierarchical context (parent/child), `Environment` property resolution, `@Conditional` bean registration, and graceful shutdown.

```java
// SpringContextV3.java — run with: java SpringContextV3.java
// Advanced: hierarchical context, Environment, @Conditional, graceful shutdown hook.

import java.util.*;
import java.util.function.Supplier;

public class SpringContextV3 {

    record Product(int id, String name, double price) {}
    record AppProperties(String name, int port, boolean debugMode) {}

    // === Environment / @PropertySource ===
    static class Environment {
        private final Map<String, String> properties = new LinkedHashMap<>();

        void loadDefaults() {
            properties.put("app.name",       "product-service");
            properties.put("server.port",    "8080");
            properties.put("debug.mode",     "false");
            properties.put("cache.ttl",      "300");
        }

        void loadProfile(String profile) {
            if ("local".equals(profile)) {
                properties.put("debug.mode", "true");
                properties.put("server.port", "9090");
            }
        }

        String get(String key) { return properties.getOrDefault(key, ""); }
        String get(String key, String def) { return properties.getOrDefault(key, def); }

        AppProperties bind() {
            return new AppProperties(
                get("app.name"),
                Integer.parseInt(get("server.port", "8080")),
                Boolean.parseBoolean(get("debug.mode", "false")));
        }
    }

    // === @Conditional bean registration ===
    @FunctionalInterface interface Condition { boolean matches(Environment env); }

    static class ConditionalBeanRegistry {
        private final Environment env;
        private final Map<String, Object> beans = new LinkedHashMap<>();

        ConditionalBeanRegistry(Environment env) { this.env = env; }

        <T> void registerIf(String name, Condition cond, Supplier<T> factory) {
            if (cond.matches(env)) {
                beans.put(name, factory.get());
                System.out.println("  [Conditional] Registered: " + name);
            } else {
                System.out.println("  [Conditional] Skipped:    " + name + " (condition false)");
            }
        }

        @SuppressWarnings("unchecked")
        <T> Optional<T> getBean(String name) {
            return Optional.ofNullable((T) beans.get(name));
        }
    }

    // === Hierarchical context: parent (infrastructure) + child (web) ===
    static class BeanContainer {
        private final String name;
        private final Map<Class<?>, Object> beans = new LinkedHashMap<>();
        private BeanContainer parent;

        BeanContainer(String name) { this.name = name; }
        BeanContainer withParent(BeanContainer p) { this.parent = p; return this; }
        <T> void register(Class<T> type, T bean) { beans.put(type, bean); }

        @SuppressWarnings("unchecked")
        <T> Optional<T> getBean(Class<T> type) {
            if (beans.containsKey(type)) return Optional.of((T) beans.get(type));
            if (parent != null) return parent.getBean(type);
            return Optional.empty();
        }

        void describe() {
            System.out.println("  Context [" + name + "]: " + beans.keySet().stream()
                .map(c -> c.getSimpleName()).toList());
        }
    }

    static class CacheService { String status() { return "WARM"; } }
    static class DatabaseService { String status() { return "CONNECTED"; } }
    static class ProductController {
        private final DatabaseService db;
        ProductController(DatabaseService db) { this.db = db; }
        String handle(String path) { return "200 OK [db=" + db.status() + "] → " + path; }
    }
    static class DebugController {
        String handle() { return "200 OK /debug — ONLY IN DEBUG MODE"; }
    }

    public static void main(String[] args) {
        System.out.println("=== spring-context: Advanced Features ===\n");

        // 1. Environment and properties
        Environment env = new Environment();
        env.loadDefaults();
        env.loadProfile(System.getProperty("spring.profiles.active", "local"));
        AppProperties props = env.bind();
        System.out.println("1. Bound properties: " + props);

        // 2. Conditional bean registration (@Conditional)
        System.out.println("\n2. Conditional beans:");
        ConditionalBeanRegistry cond = new ConditionalBeanRegistry(env);
        cond.registerIf("cacheService", e -> true,  CacheService::new);
        cond.registerIf("debugController",
            e -> Boolean.parseBoolean(e.get("debug.mode", "false")),
            DebugController::new);

        // 3. Hierarchical context: parent=infrastructure, child=web
        System.out.println("\n3. Hierarchical context:");
        BeanContainer infraCtx = new BeanContainer("infrastructure");
        infraCtx.register(CacheService.class, new CacheService());
        infraCtx.register(DatabaseService.class, new DatabaseService());

        BeanContainer webCtx = new BeanContainer("web").withParent(infraCtx);
        webCtx.register(ProductController.class,
            new ProductController(infraCtx.getBean(DatabaseService.class).orElseThrow()));

        infraCtx.describe();
        webCtx.describe();

        // Child can see parent beans, parent cannot see child beans
        System.out.println("  web can see DatabaseService: " + webCtx.getBean(DatabaseService.class).isPresent());
        System.out.println("  infra can see ProductController: " + infraCtx.getBean(ProductController.class).isPresent());

        // 4. Request handling
        System.out.println("\n4. Request handling:");
        ProductController ctrl = webCtx.getBean(ProductController.class).orElseThrow();
        System.out.println("  GET /products → " + ctrl.handle("/products"));

        // 5. Shutdown hook (@PreDestroy on all beans, ordered)
        System.out.println("\n5. Graceful shutdown (ctx.registerShutdownHook):");
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("  [Shutdown] Closing web context...");
            System.out.println("  [Shutdown] Closing infra context...");
            System.out.println("  [Shutdown] All beans destroyed.");
        }));
        System.out.println("  Shutdown hook registered. JVM will call it on exit.");
    }
}
```

How to run: `java SpringContextV3.java`

The hierarchical context is Spring's pattern for large applications: infrastructure beans (DB, cache) live in a parent context shared across all web deployments; each web module has a child context with its controllers. Child beans can `@Autowired` parent beans; the reverse is forbidden (the parent doesn't know about children).

## 6. Walkthrough

**Level 1 — container startup:**
1. `new AppConfig()` holds factory methods. `config.productRepository()` instantiates `ProductRepository`. `config.productService()` calls `productRepository()` again — in Spring's real container this would return the already-created singleton; here the mini-context pre-calls it.
2. Both beans stored in `beans` map. `getBean(ProductService.class)` returns the wired singleton.
3. `svc.printAll()` calls `repo.findAll()` → iterates the map → prints sorted products.

**Level 2 — event flow:**
1. `events.publish(new ProductCreated(new Product(3, "Keyboard", 89.99)))` → finds `ProductCreated` listener registered in `init()` → adds product to `cache`.
2. `events.publish(new ProductDeleted(2))` → finds `ProductDeleted` listener → removes `id=2` from cache.
3. `cache.all()` after events shows `[Laptop, Keyboard]` (Monitor removed).

**Level 3 — hierarchical context:**
`webCtx.getBean(ProductController.class)` → found in `webCtx.beans`. `webCtx.getBean(DatabaseService.class)` → not in `webCtx.beans` → delegates to `parent` (infraCtx) → found. `infraCtx.getBean(ProductController.class)` → not in `infraCtx.beans` → no parent → empty. This mirrors Spring's `parent: infraCtx` behaviour exactly.

**Conditional registration:**
`debugController` condition: `env.get("debug.mode") = "true"` (loaded from local profile) → registered. If profile is `default` (not `local`), `debug.mode=false` → skipped.

**Shutdown hook:** `ApplicationContext.registerShutdownHook()` registers a JVM shutdown hook that calls `ctx.close()`, which calls `@PreDestroy` on every bean in reverse creation order. The hook fires on SIGTERM (Kubernetes pod termination), CTRL+C, or normal JVM exit.

## 7. Gotchas & takeaways

> **`ApplicationContext.close()` must be called for `@PreDestroy` to fire in standalone (non-Boot) applications.** In Spring Boot, the embedded server handles context closure on shutdown automatically. In a bare `main` method using `AnnotationConfigApplicationContext`, you must either call `ctx.close()` explicitly or call `ctx.registerShutdownHook()` — otherwise `@PreDestroy` beans are silently skipped, and resources like database connections or file handles leak.

> **`AnnotationConfigApplicationContext` scans annotations, but not classes on the classpath.** If you pass a `@Configuration` class, only the beans declared in that class (and those it imports) are registered. If you want component scan, pass a package name: `new AnnotationConfigApplicationContext("com.example.app")` — or annotate your config with `@ComponentScan("com.example.app")`.

- `BeanFactory` (from `spring-beans`) is a lower-level container without events, i18n, lifecycle callbacks, or AOP post-processing. Use `ApplicationContext` (from `spring-context`) in application code — `BeanFactory` is only useful in very memory-constrained embedded environments.
- `spring-context` adds `spring-aop` transitively, so `@Transactional` and `@Aspect` beans work without adding `spring-aop` explicitly.
- The `try-with-resources` pattern with `ConfigurableApplicationContext` (the closeable sub-interface) automatically calls `close()` and fires `@PreDestroy`:
  ```java
  try (var ctx = new AnnotationConfigApplicationContext(AppConfig.class)) {
      ProductService svc = ctx.getBean(ProductService.class);
      svc.doWork();
  }  // ctx.close() called here → @PreDestroy fires
  ```
- For long-running non-Boot applications (`main` that blocks), call `ctx.registerShutdownHook()` once and let the JVM handle it.
- If you are in Spring Boot, you never bootstrap `ApplicationContext` yourself — `SpringApplication.run()` does it. `spring-context` is simply a transitive dependency you never see in your `pom.xml`.
