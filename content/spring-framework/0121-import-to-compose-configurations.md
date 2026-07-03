---
card: spring-framework
gi: 121
slug: import-to-compose-configurations
title: "@Import to compose configurations"
---

## 1. What it is

`@Import` lets one `@Configuration` class pull in another configuration class (or a regular class) into the same application context — without component scanning. It is the Java-config equivalent of `<import>` in XML Spring config. You declare exactly which configuration classes participate, rather than relying on package scanning to find them.

```java
@Configuration
@Import({DataSourceConfig.class, CacheConfig.class, SecurityConfig.class})
class AppConfig { }
```

Spring processes each imported class as if it had been registered directly — all its `@Bean` methods, nested configs, and further `@Import`s are followed recursively.

## 2. Why & when

- **Modular configuration** — split a large config into focused classes (`DataConfig`, `WebConfig`, `SecurityConfig`) and compose them in a root config.
- **Library / auto-configuration** — a library ships its own `@Configuration` and instructs users to `@Import` it rather than scanning their whole classpath.
- **Testing** — import only the subset of config needed for a test slice instead of loading the whole application.
- **`ImportSelector`** — `@Import` can also take a class that implements `ImportSelector`, which returns class names to import dynamically (covered next tutorial).
- **`ImportBeanDefinitionRegistrar`** — import a class that registers bean definitions programmatically.

## 3. Core concept

`@Import` accepts an array of `Class<?>`. Each element may be:

1. **Another `@Configuration` class** — full processing (CGLIB, nested `@Bean`, `@ComponentScan`, recursive `@Import`).
2. **A `@Component` class** — registered as a bean.
3. **An `ImportSelector`** — Spring calls `selectImports()` to get class names to import.
4. **An `ImportBeanDefinitionRegistrar`** — Spring calls `registerBeanDefinitions()` with the registry.

`@Import` is transitive. If `AppConfig` imports `DataConfig` and `DataConfig` itself imports `JdbcConfig`, then `JdbcConfig` is also processed in the `AppConfig` context — no explicit listing in `AppConfig` required.

`@Import` can appear on:
- `@Configuration` classes.
- Custom annotations (meta-annotation) so that using your annotation automatically imports the right config.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Root config -->
  <rect x="10" y="70" width="170" height="65" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="95" y="93" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">AppConfig</text>
  <text x="95" y="110" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Import({DataCfg,</text>
  <text x="95" y="124" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">CacheCfg, SecCfg})</text>

  <!-- Imported configs -->
  <rect x="260" y="20" width="135" height="46" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="327" y="43" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">DataConfig</text>
  <text x="327" y="57" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Bean dataSource()</text>

  <rect x="260" y="80" width="135" height="46" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="327" y="103" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">CacheConfig</text>
  <text x="327" y="117" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Bean cacheManager()</text>

  <rect x="260" y="140" width="135" height="46" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="327" y="163" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">SecurityConfig</text>
  <text x="327" y="177" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Bean authManager()</text>

  <!-- Arrows from AppConfig -->
  <line x1="182" y1="88" x2="257" y2="43" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a121)"/>
  <line x1="182" y1="103" x2="257" y2="103" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a121)"/>
  <line x1="182" y1="117" x2="257" y2="163" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a121)"/>
  <defs>
    <marker id="a121" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b121" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Unified context -->
  <rect x="480" y="70" width="210" height="65" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="585" y="93" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Single Context</text>
  <text x="585" y="110" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">dataSource, cacheManager,</text>
  <text x="585" y="124" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">authManager, app beans…</text>

  <line x1="397" y1="103" x2="477" y2="103" stroke="#79c0ff" stroke-width="2" marker-end="url(#b121)"/>
  <text x="350" y="190" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">@Import merges multiple configs into one context without component scanning</text>
</svg>

`@Import` pulls named config classes into the same context — all their beans are available in one registry.

## 5. Runnable example

### Level 1 — Basic

Compose two config classes via `@Import`: data config and service config.

```java
// ImportBasic.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;

// Separate data config
@Configuration
class DataConfig {
    @Bean
    public String connectionUrl() { return "jdbc:h2:mem:testdb"; }
}

// Service config — imported into root
@Configuration
class ServiceConfig {
    @Bean
    public UserService userService(String connectionUrl) {
        return new UserService(connectionUrl);
    }
}

class UserService {
    private final String url;
    UserService(String u) { this.url = u; }
    public String whoAmI() { return "UserService connected to " + url; }
}

// Root config — composes both
@Configuration
@Import({DataConfig.class, ServiceConfig.class})
class AppConfig {}

public class ImportBasic {
    public static void main(String[] args) {
        // Only register AppConfig — @Import brings in the rest
        var ctx = new AnnotationConfigApplicationContext(AppConfig.class);

        System.out.println(ctx.getBean(UserService.class).whoAmI());

        // Verify both imported config classes are in the context
        System.out.println("DataConfig registered: " + ctx.containsBean("dataConfig"));
        System.out.println("ServiceConfig registered: " + ctx.containsBean("serviceConfig"));
        ctx.close();
    }
}
```

How to run: `java ImportBasic.java`

Registering only `AppConfig` pulls in `DataConfig` and `ServiceConfig` via `@Import`. The `connectionUrl` bean from `DataConfig` is injected into `UserService` by `ServiceConfig`.

### Level 2 — Intermediate

Transitive `@Import` chains and mixing regular-class imports.

```java
// ImportTransitive.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

// --- Level 3: deepest dependency ---
@Configuration
class DbConfig {
    @Bean public String jdbcUrl() { return "jdbc:postgresql://localhost/shop"; }
    @Bean public DataPool dataPool(String jdbcUrl) { return new DataPool(jdbcUrl); }
}

class DataPool {
    final String url;
    DataPool(String u) { this.url = u; }
    public String borrow() { return "conn@" + url; }
}

// --- Level 2: middle ---
@Configuration
@Import(DbConfig.class)             // transitive: pulls DbConfig
class RepositoryConfig {
    @Bean public ProductRepo productRepo(DataPool pool) { return new ProductRepo(pool); }
    @Bean public OrderRepo   orderRepo(DataPool pool)   { return new OrderRepo(pool); }
}

class ProductRepo {
    final DataPool pool;
    ProductRepo(DataPool p) { this.pool = p; }
    public String find(int id) { return "[Product#" + id + " via " + pool.borrow() + "]"; }
}

class OrderRepo {
    final DataPool pool;
    OrderRepo(DataPool p) { this.pool = p; }
    public String find(int id) { return "[Order#" + id + " via " + pool.borrow() + "]"; }
}

// Plain @Component imported directly (not a @Configuration)
@Component
class HealthCheck {
    boolean ok() { return true; }
}

// --- Level 1: root ---
@Configuration
@Import({RepositoryConfig.class, HealthCheck.class})   // RepositoryConfig brings DbConfig transitively
class RootConfig {
    @Bean public AppService appService(ProductRepo pr, OrderRepo or) {
        return new AppService(pr, or);
    }
}

class AppService {
    final ProductRepo pr; final OrderRepo or;
    AppService(ProductRepo p, OrderRepo o) { this.pr = p; this.or = o; }
    public void run(int uid) {
        System.out.println(pr.find(uid));
        System.out.println(or.find(uid));
    }
}

public class ImportTransitive {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(RootConfig.class);
        ctx.getBean(AppService.class).run(42);

        // DbConfig beans are available even though RootConfig doesn't import it directly
        System.out.println("jdbcUrl: " + ctx.getBean("jdbcUrl", String.class));
        System.out.println("healthCheck: " + ctx.getBean(HealthCheck.class).ok());
        ctx.close();
    }
}
```

How to run: `java ImportTransitive.java`

`RootConfig` imports `RepositoryConfig`. `RepositoryConfig` imports `DbConfig`. So `DbConfig`'s beans (`jdbcUrl`, `dataPool`) are available in the root context even though `RootConfig` never mentions `DbConfig`. `HealthCheck` is imported as a plain `@Component`.

### Level 3 — Advanced

`@Import` on a custom annotation (meta-annotation) — importing config by enabling a feature with a toggle annotation.

```java
// ImportMetaAnnotation.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.lang.annotation.*;

// Feature: metrics collection
@Configuration
class MetricsConfig {
    @Bean public MetricsCollector metricsCollector() {
        System.out.println("[Metrics] collector created");
        return new MetricsCollector();
    }
    @Bean public MetricsDashboard metricsDashboard(MetricsCollector mc) {
        return new MetricsDashboard(mc);
    }
}

class MetricsCollector {
    public void record(String name, double value) {
        System.out.println("[Metrics] " + name + "=" + value);
    }
}

class MetricsDashboard {
    final MetricsCollector mc;
    MetricsDashboard(MetricsCollector m) { this.mc = m; }
    public void show() { System.out.println("[Dashboard] metrics online"); }
}

// Feature annotation — use @EnableMetrics to activate MetricsConfig
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Import(MetricsConfig.class)
@interface EnableMetrics {}

// Another feature: audit trail
@Configuration
class AuditConfig {
    @Bean public AuditTrail auditTrail() { return new AuditTrail(); }
}

class AuditTrail {
    public void record(String action) { System.out.println("[Audit] " + action); }
}

@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Import(AuditConfig.class)
@interface EnableAudit {}

// Application config enables features via meta-annotations
@Configuration
@EnableMetrics
@EnableAudit
class AppCfg {}

@Service
class OrderProcessor {
    @org.springframework.beans.factory.annotation.Autowired
    MetricsCollector metrics;

    @org.springframework.beans.factory.annotation.Autowired
    AuditTrail audit;

    public void processOrder(int id, double amount) {
        metrics.record("order.amount", amount);
        audit.record("order#" + id + " placed");
        System.out.println("[Order] processed #" + id);
    }
}

@Configuration
@Import(AppCfg.class)
@ComponentScan(basePackageClasses = ImportMetaAnnotation.class)
class RootCfg {}

public class ImportMetaAnnotation {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(RootCfg.class);
        ctx.getBean(OrderProcessor.class).processOrder(7, 299.99);
        ctx.getBean(MetricsDashboard.class).show();
        ctx.close();
    }
}
```

How to run: `java ImportMetaAnnotation.java`

`@EnableMetrics` and `@EnableAudit` are custom annotations meta-annotated with `@Import`. Applying them to `AppCfg` pulls in `MetricsConfig` and `AuditConfig` — this is the exact pattern Spring Boot's `@Enable*` annotations use (e.g., `@EnableCaching`, `@EnableScheduling`).

## 6. Walkthrough

Execution for Level 3:

1. **`AnnotationConfigApplicationContext(RootCfg.class)` created** — processes `RootCfg`.
2. **`@Import(AppCfg.class)` on `RootCfg`** — adds `AppCfg` to the processing queue.
3. **`AppCfg` is processed** — has `@EnableMetrics` → which is meta-annotated `@Import(MetricsConfig.class)` → adds `MetricsConfig`. Has `@EnableAudit` → adds `AuditConfig`.
4. **`MetricsConfig` processed** — registers `metricsCollector` and `metricsDashboard` beans.
5. **`AuditConfig` processed** — registers `auditTrail` bean.
6. **`@ComponentScan` on `RootCfg`** — finds `OrderProcessor` via `@Service`.
7. **`OrderProcessor` post-processed** — `@Autowired MetricsCollector` and `AuditTrail` injected.
8. **`processOrder(7, 299.99)`** → prints metrics record, audit record, order done.

Expected output:
```
[Metrics] collector created
[Metrics] order.amount=299.99
[Audit] order#7 placed
[Order] processed #7
[Dashboard] metrics online
```

## 7. Gotchas & takeaways

> `@Import` is processed by `ConfigurationClassPostProcessor` before instantiation. If you add `@Import` to a class that Spring has already processed (e.g., programmatically via `ctx.register()`), the import is honoured — the processor handles it. But if you add it after `ctx.refresh()` is called, it is too late.

> Duplicate imports are deduplicated — importing the same class twice (from two different paths) registers its beans once. This is safe for transitive imports.

- `@Import` is order-independent for bean registration but defines import processing order — useful when one config's `BeanFactoryPostProcessor` must run before another.
- Imported configs participate in the same bean factory as the importing config — they share the same `BeanDefinitionRegistry`, so bean names must be unique across all imports.
- `@Import` on a custom `@Enable*` annotation is the idiomatic Spring pattern for feature-toggle annotations — study `@EnableTransactionManagement`, `@EnableCaching`, `@EnableScheduling` for examples.
- You can mix `@Import` and `@ComponentScan` in the same `@Configuration` — they complement each other.
