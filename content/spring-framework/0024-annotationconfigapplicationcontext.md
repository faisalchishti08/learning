---
card: spring-framework
gi: 24
slug: annotationconfigapplicationcontext
title: AnnotationConfigApplicationContext
---

## 1. What it is

`AnnotationConfigApplicationContext` is the `ApplicationContext` implementation that reads configuration from **Java classes** rather than XML files. You pass it either:

- A `@Configuration` class (explicit Java configuration), or
- One or more packages to scan for `@Component`-annotated classes.

```java
// From a @Configuration class
ApplicationContext ctx =
    new AnnotationConfigApplicationContext(AppConfig.class);

// From a component scan
ApplicationContext ctx2 =
    new AnnotationConfigApplicationContext("com.example.service");

// Both combined
ApplicationContext ctx3 =
    new AnnotationConfigApplicationContext(AppConfig.class, InfraConfig.class);
```

This is the standard container for standalone Spring applications and integration tests. Spring Boot's `SpringApplication.run()` uses it internally (wrapped in `SpringBootApplication`).

In one sentence: **`AnnotationConfigApplicationContext` bootstraps a full Spring IoC container from `@Configuration` classes and `@Component` scans — no XML required.**

## 2. Why & when

XML configuration requires you to keep a separate file in sync with your Java classes. Annotation/Java config eliminates that gap:

- **Type safety.** `@Bean` methods have return types; the compiler catches typos.
- **IDE navigation.** Ctrl+click on a `@Bean` method name jumps straight to the definition — impossible with `"orderService"` strings in XML.
- **Refactoring.** Rename a class → IDE renames all references including `@Bean` return types.
- **Testability.** Create a `@Configuration` class with mock beans for testing; swap with the real one for production.

Use `AnnotationConfigApplicationContext` for:
- Standalone Spring apps (no web server needed).
- Integration tests via `@SpringJUnitConfig` or manual context construction.
- Microservices that start with a `main` method.

Spring Boot handles bootstrap automatically. Manual `AnnotationConfigApplicationContext` is useful when you need fine-grained control over which configs are loaded.

## 3. Core concept

`AnnotationConfigApplicationContext` has two internal readers:

```
AnnotationConfigApplicationContext
  ├── AnnotatedBeanDefinitionReader   (processes @Configuration classes)
  └── ClassPathBeanDefinitionScanner  (discovers @Component classes)
```

**`register(Class<?>...)`** uses `AnnotatedBeanDefinitionReader` to process explicit `@Configuration` or `@Component` classes. **`scan(String...)`** uses `ClassPathBeanDefinitionScanner` to find all `@Component`-annotated classes under the given packages.

After registering/scanning, calling `refresh()` triggers the standard lifecycle:

```
register/scan → BeanDefinitions stored
refresh()     → BeanFactoryPostProcessors run (e.g., @PropertySource, @Import)
             → BeanPostProcessors registered
             → All singleton beans instantiated + wired
             → ContextRefreshedEvent fired
```

`AnnotationConfigApplicationContext` can also be built **incrementally** (without auto-refresh in the constructor):

```java
AnnotationConfigApplicationContext ctx = new AnnotationConfigApplicationContext();
ctx.register(AppConfig.class);
ctx.getEnvironment().setActiveProfiles("production");
ctx.refresh();  // manual refresh after all setup
```

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AnnotationConfigApplicationContext with register and scan paths converging to refresh and singleton beans">
  <defs>
    <marker id="a24" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- register() path -->
  <rect x="10" y="20" width="175" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="97" y="41" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">register(AppConfig.class)</text>
  <text x="97" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">AnnotatedBeanDefinitionReader</text>

  <!-- scan() path -->
  <rect x="10" y="100" width="175" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="97" y="121" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">scan("com.example")</text>
  <text x="97" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ClassPathBeanDefinitionScanner</text>

  <!-- BeanDefinitions -->
  <rect x="260" y="50" width="155" height="70" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="337" y="72" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">BeanDefinitions</text>
  <text x="337" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">class, scope, deps</text>
  <text x="337" y="106" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">init/destroy, lazy</text>

  <line x1="185" y1="45" x2="258" y2="75" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a24)"/>
  <line x1="185" y1="125" x2="258" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a24)"/>

  <!-- refresh() -->
  <rect x="490" y="50" width="180" height="70" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="580" y="72" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">refresh()</text>
  <text x="580" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">post-processors applied</text>
  <text x="580" y="106" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">all singletons ready</text>

  <line x1="415" y1="85" x2="488" y2="85" stroke="#6db33f" stroke-width="2" marker-end="url(#a24)"/>

  <text x="340" y="185" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">After refresh(): getBean(OrderService.class) returns fully wired singleton</text>

  <!-- Profile box -->
  <rect x="260" y="170" width="155" height="34" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="337" y="192" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">setActiveProfiles() before refresh()</text>
</svg>

`register()` processes explicit classes; `scan()` discovers annotated classes. Both populate `BeanDefinitions`. `refresh()` instantiates everything.

## 5. Runnable example

Scenario: an inventory management system. `InventoryService` depends on a `ProductRepository` and an `AuditLogger`. We evolve from basic Java config to profile-based config swapping.

### Level 1 — Basic

One `@Configuration` class, two `@Bean` methods, one `getBean()` call — the minimal pattern.

```java
// AcacDemo.java — run with: java AcacDemo.java
import java.lang.annotation.*;
import java.util.*;

public class AcacDemo {

    // Minimal simulation of @Configuration / @Bean / AnnotationConfigApplicationContext
    @Retention(RetentionPolicy.RUNTIME) @interface Configuration {}
    @Retention(RetentionPolicy.RUNTIME) @interface Bean {}

    // Domain
    record Product(int id, String name, int stock) {}

    static class ProductRepository {
        private final List<Product> store = new ArrayList<>(List.of(
            new Product(1, "Laptop",  42),
            new Product(2, "Monitor", 15),
            new Product(3, "Keyboard", 0)
        ));
        List<Product> findAll() { return Collections.unmodifiableList(store); }
        Optional<Product> findById(int id) { return store.stream().filter(p -> p.id() == id).findFirst(); }
    }

    static class AuditLogger {
        void log(String event) { System.out.println("  [AUDIT] " + event); }
    }

    static class InventoryService {
        private final ProductRepository repo;
        private final AuditLogger       audit;
        InventoryService(ProductRepository repo, AuditLogger audit) {
            this.repo = repo; this.audit = audit;
        }
        void listInStock() {
            System.out.println("  In-stock products:");
            repo.findAll().stream().filter(p -> p.stock() > 0)
                .forEach(p -> System.out.printf("    %-10s stock=%d%n", p.name(), p.stock()));
            audit.log("listed in-stock products");
        }
    }

    // --- @Configuration class ---
    @Configuration
    static class AppConfig {
        @Bean ProductRepository productRepository() { return new ProductRepository(); }
        @Bean AuditLogger       auditLogger()        { return new AuditLogger(); }
        @Bean InventoryService  inventoryService()   {
            return new InventoryService(productRepository(), auditLogger());
        }
    }

    // --- Simulated AnnotationConfigApplicationContext ---
    static class AnnotationConfigCtx {
        private final Map<Class<?>, Object> beans = new LinkedHashMap<>();

        void register(Object config) throws Exception {
            System.out.println("[CTX] Processing @Configuration: " + config.getClass().getSimpleName());
            for (var m : config.getClass().getDeclaredMethods()) {
                if (!m.isAnnotationPresent(Bean.class)) continue;
                Object bean = m.invoke(config);
                beans.put(m.getReturnType(), bean);
                System.out.println("  @Bean → " + m.getReturnType().getSimpleName());
            }
            System.out.println("[CTX] refresh() complete\n");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) {
            return (T) beans.entrySet().stream()
                .filter(e -> type.isAssignableFrom(e.getKey()))
                .map(Map.Entry::getValue).findFirst()
                .orElseThrow(() -> new RuntimeException("No bean: " + type.getSimpleName()));
        }
    }

    public static void main(String[] args) throws Exception {
        AnnotationConfigCtx ctx = new AnnotationConfigCtx();
        ctx.register(new AppConfig());

        InventoryService svc = ctx.getBean(InventoryService.class);
        svc.listInStock();
    }
}
```

How to run: `java AcacDemo.java`

`AppConfig` is a plain Java class. The container calls each `@Bean` method and caches the result. `InventoryService` calls `productRepository()` and `auditLogger()` — in real Spring these calls are intercepted by CGLIB so the same singleton is returned each time, not a new instance.

### Level 2 — Intermediate

Add `@ComponentScan`-style discovery: beans annotated with `@Component` are auto-discovered without explicit `@Bean` methods.

```java
// AcacDemo2.java — run with: java AcacDemo2.java
import java.lang.annotation.*;
import java.util.*;

public class AcacDemo2 {

    @Retention(RetentionPolicy.RUNTIME) @interface Component { String value() default ""; }
    @Retention(RetentionPolicy.RUNTIME) @interface Autowired {}
    @Retention(RetentionPolicy.RUNTIME) @interface Configuration {}
    @Retention(RetentionPolicy.RUNTIME) @interface Bean {}

    record Product(int id, String name, int stock) {}

    @Component
    static class ProductRepository {
        private final List<Product> store = new ArrayList<>(List.of(
            new Product(1, "Laptop", 42), new Product(2, "Monitor", 15)
        ));
        List<Product> findAll() { return Collections.unmodifiableList(store); }
    }

    @Component
    static class AuditLogger {
        void log(String event) { System.out.println("  [AUDIT] " + event); }
    }

    @Component
    static class InventoryService {
        private final ProductRepository repo;
        private final AuditLogger       audit;
        @Autowired
        InventoryService(ProductRepository repo, AuditLogger audit) {
            this.repo = repo; this.audit = audit;
        }
        void listInStock() {
            System.out.println("  In-stock products:");
            repo.findAll().stream().filter(p -> p.stock() > 0)
                .forEach(p -> System.out.printf("    %-10s stock=%d%n", p.name(), p.stock()));
            audit.log("listed in-stock");
        }
    }

    // Infrastructure bean in @Configuration — not a @Component
    @Configuration
    static class InfraConfig {
        @Bean String dbUrl() { return "jdbc:h2:mem:inventory"; }
    }

    // --- Scanning container: discovers @Component + processes @Configuration ---
    static class ScanningCtx {
        private final Map<Class<?>, Object> typed = new LinkedHashMap<>();
        private final Map<String, Object>   named = new LinkedHashMap<>();

        void scan(Class<?>... componentClasses) throws Exception {
            System.out.println("[SCAN] Discovering @Component beans...");
            // Pass 1: instantiate no-arg @Component beans
            for (Class<?> cls : componentClasses) {
                if (!cls.isAnnotationPresent(Component.class)) continue;
                var ctors = cls.getDeclaredConstructors();
                if (ctors[0].getParameterCount() == 0) {
                    Object bean = ctors[0].newInstance();
                    typed.put(cls, bean);
                    for (var iface : cls.getInterfaces()) typed.put(iface, bean);
                    System.out.println("  Scanned: " + cls.getSimpleName() + " (no-arg)");
                }
            }
            // Pass 2: wire @Autowired constructor beans
            for (Class<?> cls : componentClasses) {
                if (!cls.isAnnotationPresent(Component.class) || typed.containsKey(cls)) continue;
                for (var ctor : cls.getDeclaredConstructors()) {
                    if (!ctor.isAnnotationPresent(Autowired.class)) continue;
                    Object[] deps = Arrays.stream(ctor.getParameterTypes())
                        .map(t -> typed.entrySet().stream()
                            .filter(e -> t.isAssignableFrom(e.getKey()))
                            .map(Map.Entry::getValue).findFirst()
                            .orElseThrow(() -> new RuntimeException("No dep: " + t)))
                        .toArray();
                    Object bean = ctor.newInstance(deps);
                    typed.put(cls, bean);
                    System.out.println("  Wired:   " + cls.getSimpleName());
                }
            }
        }

        void processConfig(Object config) throws Exception {
            System.out.println("[CONFIG] Processing @Configuration: " + config.getClass().getSimpleName());
            for (var m : config.getClass().getDeclaredMethods()) {
                if (!m.isAnnotationPresent(Bean.class)) continue;
                Object bean = m.invoke(config);
                typed.put(m.getReturnType(), bean);
                named.put(m.getName(), bean);
                System.out.println("  @Bean: " + m.getName() + " → " + bean);
            }
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) {
            return (T) typed.entrySet().stream()
                .filter(e -> type.isAssignableFrom(e.getKey()))
                .map(Map.Entry::getValue).findFirst()
                .orElseThrow();
        }
    }

    public static void main(String[] args) throws Exception {
        ScanningCtx ctx = new ScanningCtx();
        ctx.scan(ProductRepository.class, AuditLogger.class, InventoryService.class);
        ctx.processConfig(new InfraConfig());
        System.out.println("[CTX] Ready\n");

        InventoryService svc = ctx.getBean(InventoryService.class);
        svc.listInStock();
        System.out.println("\nDB URL: " + ctx.getBean(String.class));
    }
}
```

How to run: `java AcacDemo2.java`

`@Component` beans are discovered and wired automatically. `InfraConfig` provides infrastructure beans (database URL) that cannot be easily expressed as `@Component` because they require constructor arguments. Both paths coexist in the same context.

### Level 3 — Advanced

Profiles: two `@Configuration` classes provide different `PriceStrategy` implementations. The active profile selects which one is loaded.

```java
// AcacDemo3.java — run with: java AcacDemo3.java
import java.lang.annotation.*;
import java.util.*;
import java.util.function.*;

public class AcacDemo3 {

    @Retention(RetentionPolicy.RUNTIME) @interface Configuration {}
    @Retention(RetentionPolicy.RUNTIME) @interface Bean       {}
    @Retention(RetentionPolicy.RUNTIME) @interface Profile    { String value(); }

    record Product(String name, double price) {}

    interface PriceStrategy {
        double apply(Product p, int qty);
        String name();
    }

    static class RetailPriceStrategy implements PriceStrategy {
        public double apply(Product p, int qty) { return p.price() * qty; }
        public String name() { return "retail"; }
    }

    static class WholesalePriceStrategy implements PriceStrategy {
        public double apply(Product p, int qty) {
            double discount = qty >= 10 ? 0.20 : 0.05;
            return p.price() * qty * (1 - discount);
        }
        public String name() { return "wholesale(qty=" + qty(qty) + ")"; }
        private String qty(int q) { return q >= 10 ? ">=10,20%off" : "<10,5%off"; }
    }

    static class InventoryService {
        private final PriceStrategy strategy;
        InventoryService(PriceStrategy strategy) { this.strategy = strategy; }
        void quote(Product p, int qty) {
            System.out.printf("  %-10s x%-3d strategy=%-20s total=$%.2f%n",
                p.name(), qty, strategy.name(), strategy.apply(p, qty));
        }
    }

    // --- Profile-aware configuration classes ---
    @Configuration @Profile("retail")
    static class RetailConfig {
        @Bean PriceStrategy priceStrategy()  { return new RetailPriceStrategy(); }
        @Bean InventoryService inventoryService() {
            return new InventoryService(priceStrategy());
        }
    }

    @Configuration @Profile("wholesale")
    static class WholesaleConfig {
        @Bean PriceStrategy priceStrategy()  { return new WholesalePriceStrategy(); }
        @Bean InventoryService inventoryService() {
            return new InventoryService(priceStrategy());
        }
    }

    // --- Profile-aware AnnotationConfigApplicationContext simulation ---
    static class ProfileCtx {
        private final String           activeProfile;
        private final Map<Class<?>, Object> beans = new LinkedHashMap<>();

        ProfileCtx(String activeProfile, Object... configs) throws Exception {
            this.activeProfile = activeProfile;
            System.out.println("[CTX] Active profile: " + activeProfile);
            for (Object cfg : configs) {
                Profile p = cfg.getClass().getAnnotation(Profile.class);
                if (p != null && !p.value().equals(activeProfile)) {
                    System.out.println("  Skipping @Configuration (profile=" + p.value() + "): "
                        + cfg.getClass().getSimpleName());
                    continue;
                }
                System.out.println("  Loading @Configuration: " + cfg.getClass().getSimpleName());
                for (var m : cfg.getClass().getDeclaredMethods()) {
                    if (!m.isAnnotationPresent(Bean.class)) continue;
                    Object bean = m.invoke(cfg);
                    beans.put(m.getReturnType(), bean);
                    System.out.println("    @Bean: " + m.getName() + " → " + bean.getClass().getSimpleName());
                }
            }
            System.out.println("[CTX] refresh() complete\n");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) {
            return (T) beans.entrySet().stream()
                .filter(e -> type.isAssignableFrom(e.getKey()))
                .map(Map.Entry::getValue).findFirst()
                .orElseThrow(() -> new RuntimeException("No bean: " + type.getSimpleName()));
        }
    }

    public static void main(String[] args) throws Exception {
        List<Product> products = List.of(
            new Product("Laptop",  1299.00),
            new Product("Monitor",  449.99)
        );

        for (String profile : List.of("retail", "wholesale")) {
            System.out.println("=== Profile: " + profile + " ===");
            ProfileCtx ctx = new ProfileCtx(profile, new RetailConfig(), new WholesaleConfig());
            InventoryService svc = ctx.getBean(InventoryService.class);
            for (Product p : products) {
                svc.quote(p, 3);   // small order
                svc.quote(p, 15);  // bulk order
            }
            System.out.println();
        }
    }
}
```

How to run: `java AcacDemo3.java`

With `profile=retail`, `RetailConfig` loads and `WholesaleConfig` is skipped. With `profile=wholesale` the reverse. The same `InventoryService` class works under both — only the injected `PriceStrategy` changes. In real Spring: `ctx.getEnvironment().setActiveProfiles("wholesale")` before `ctx.refresh()` achieves exactly this.

## 6. Walkthrough

**Level 3 — profile selection and bean creation:**

1. `ProfileCtx("wholesale", new RetailConfig(), new WholesaleConfig())` iterates configs.
2. `RetailConfig` has `@Profile("retail")` → `"retail" != "wholesale"` → skipped entirely.
3. `WholesaleConfig` has `@Profile("wholesale")` → matches → process.
4. `priceStrategy()` → `new WholesalePriceStrategy()` → stored as `PriceStrategy`.
5. `inventoryService()` → calls `priceStrategy()` (which returns the already-created singleton in real Spring via CGLIB proxy) → `new InventoryService(wholesaleStrategy)` → stored.

**`svc.quote(Laptop, 3)` with wholesale profile:**
```
quote(Product("Laptop", 1299.00), 3)
  → strategy.apply(p, 3)
      → qty=3 < 10 → discount=0.05
      → 1299.00 * 3 * 0.95 = 3702.15
  → output: Laptop x3  strategy=wholesale(<10,5%off)  total=$3702.15
```

**`svc.quote(Laptop, 15)` with wholesale profile:**
```
quote(Product("Laptop", 1299.00), 15)
  → strategy.apply(p, 15)
      → qty=15 >= 10 → discount=0.20
      → 1299.00 * 15 * 0.80 = 15588.00
  → output: Laptop x15 strategy=wholesale(>=10,20%off) total=$15588.00
```

**Data state changes across profiles:**

| Profile | `PriceStrategy` loaded | 3x Laptop total | 15x Laptop total |
|---|---|---|---|
| `retail` | `RetailPriceStrategy` | $3897.00 | $19485.00 |
| `wholesale` | `WholesalePriceStrategy` | $3702.15 | $15588.00 |

## 7. Gotchas & takeaways

> **`@Bean` methods in `@Configuration` classes are CGLIB-proxied.** Calling `productRepository()` from within another `@Bean` method returns the **singleton** already in the context — not a new object. If you annotate a class with `@Component` instead of `@Configuration` (lite mode), `@Bean` methods are NOT proxied and each call creates a new instance. This is a common source of subtle bugs.

> **`AnnotationConfigApplicationContext` does NOT call `refresh()` automatically when constructed without arguments.** `new AnnotationConfigApplicationContext()` (no args) returns an unrefreshed context — call `register()` / `scan()` then `refresh()` manually. Constructors that accept class or package arguments DO call `refresh()` automatically.

- `ctx.register(AppConfig.class)` can be called multiple times before `refresh()` to accumulate config classes.
- `ctx.scan("com.example")` triggers a classpath scan — can be slow on large classpaths; prefer explicit `@Bean` registrations in performance-sensitive tests.
- Use `@Import(OtherConfig.class)` inside a `@Configuration` class to compose multiple configs without listing them all in the constructor.
- `@Profile("dev")` on a `@Configuration` or `@Bean` method skips that config unless the profile is active — the primary mechanism for environment-specific wiring.
- Spring Boot's `@SpringBootApplication` combines `@Configuration` + `@EnableAutoConfiguration` + `@ComponentScan` — it triggers `AnnotationConfigApplicationContext` (or `AnnotationConfigServletWebServerApplicationContext` for web apps) internally.
