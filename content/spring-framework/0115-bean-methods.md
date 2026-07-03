---
card: spring-framework
gi: 115
slug: bean-methods
title: "@Bean methods"
---

## 1. What it is

A `@Bean` method is a method inside a `@Configuration` (or `@Component`) class that tells Spring to create, configure, and manage the return value as a bean. The method name becomes the bean name, the return type is the bean type, and the method body is the factory code Spring calls once to create the instance.

```java
@Bean
public DataSource dataSource() {
    return new HikariDataSource(hikariConfig());
}
```

Spring calls this method during context refresh, stores the result in its registry, and injects it wherever the type is needed.

## 2. Why & when

`@Bean` methods are the standard way to register beans that:

- Come from third-party libraries (no source to annotate with `@Component`).
- Require constructor arguments or multi-step initialization that can't be expressed with annotation-only config.
- Depend on runtime values or environment properties to determine which implementation to create.
- Need multiple beans of the same type (e.g., two different `DataSource` beans for primary and replica).

## 3. Core concept

Key facts about `@Bean` methods:

- **Return type** — Spring registers the bean under the declared return type (and any supertypes/interfaces). Use the most specific type you need for autowiring.
- **Method name** — default bean name. Override with `@Bean("customName")` or `@Bean(name = {"name1", "name2"})`.
- **Parameters** — method parameters are resolved from the container. Spring autowires them the same way it would inject a `@Autowired` dependency. No `@Autowired` annotation needed on `@Bean` method params.
- **Singleton guarantee** — in `@Configuration` classes, inter-`@Bean` method calls go through CGLIB and return the singleton. In `@Component` (lite mode), each call is a plain Java call.
- **`@Scope`** — add to the method to override singleton with prototype, request, etc.
- **`@Lazy`** — defer creation until first use.
- **`@Primary` / `@Qualifier`** — resolve ambiguity when multiple beans of the same type exist.
- **`@DependsOn`** — force another bean to initialize first.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Config -->
  <rect x="10" y="50" width="200" height="110" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="110" y="73" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">@Configuration</text>
  <text x="110" y="93" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Bean DataSource ds()</text>
  <text x="110" y="110" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">params → autowired from ctx</text>
  <text x="110" y="130" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Bean @Primary UserRepo r()</text>
  <text x="110" y="147" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Scope("prototype")</text>

  <!-- Arrow -->
  <line x1="212" y1="105" x2="295" y2="105" stroke="#6db33f" stroke-width="2" marker-end="url(#a115)"/>
  <defs>
    <marker id="a115" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b115" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Registry -->
  <rect x="297" y="50" width="170" height="110" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="382" y="73" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Bean Registry</text>
  <text x="382" y="93" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">dataSource → HikariDS</text>
  <text x="382" y="110" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">r → UserRepo (primary)</text>
  <text x="382" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">scope=prototype</text>

  <!-- Arrow to injection -->
  <line x1="469" y1="105" x2="560" y2="105" stroke="#79c0ff" stroke-width="2" marker-end="url(#b115)"/>

  <!-- Injection targets -->
  <rect x="562" y="50" width="130" height="110" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="627" y="73" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">@Autowired</text>
  <text x="627" y="93" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">DataSource → ds</text>
  <text x="627" y="110" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">UserRepo → r</text>

  <text x="350" y="185" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">@Bean method return value → registered in context → injected into dependants</text>
</svg>

`@Bean` method return value goes into the registry; Spring injects it from there.

## 5. Runnable example

### Level 1 — Basic

Declare beans for a notification pipeline: a channel bean and a service that depends on it.

```java
// BeanMethodBasic.java
import org.springframework.context.annotation.*;

interface Channel { void send(String msg); }

class EmailChannel implements Channel {
    private final String host;
    EmailChannel(String h) { this.host = h; }
    public void send(String msg) { System.out.println("[EMAIL:" + host + "] " + msg); }
}

class NotifyService {
    private final Channel channel;
    NotifyService(Channel c) { this.channel = c; }
    public void alert(String msg) { channel.send("ALERT: " + msg); }
}

@Configuration
class BeanCfg {
    @Bean
    public Channel emailChannel() {
        System.out.println("Creating EmailChannel");
        return new EmailChannel("smtp.acme.com");
    }

    @Bean
    public NotifyService notifyService() {
        // Spring autowires Channel param from the registry
        return new NotifyService(emailChannel());  // CGLIB returns singleton
    }
}

public class BeanMethodBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(BeanCfg.class);
        ctx.getBean(NotifyService.class).alert("CPU spike");
        ctx.close();
    }
}
```

How to run: `java BeanMethodBasic.java`

`"Creating EmailChannel"` prints once. CGLIB intercepts the `emailChannel()` call from `notifyService()` and returns the existing singleton.

### Level 2 — Intermediate

`@Bean` method with parameters (Spring-autowired), multiple beans of the same type, and `@Primary`.

```java
// BeanMethodParams.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;

interface Store { String save(String item); }

class SqlStore implements Store {
    public String save(String item) { return "[SQL] saved " + item; }
}

class CacheStore implements Store {
    public String save(String item) { return "[CACHE] cached " + item; }
}

class ItemService {
    private final Store primary;
    private final Store cache;

    ItemService(Store primary, Store cache) {
        this.primary = primary; this.cache = cache;
    }

    public void saveItem(String item) {
        System.out.println(primary.save(item));
        System.out.println(cache.save(item));
    }
}

@Configuration
class StoreCfg {
    @Bean @Primary
    public Store sqlStore() { return new SqlStore(); }

    @Bean("cacheStore")
    public Store cacheStore() { return new CacheStore(); }

    @Bean
    public ItemService itemService(Store sqlStore,
                                   @Qualifier("cacheStore") Store cacheStore) {
        // Parameters are autowired: sqlStore resolved by @Primary, cacheStore by name
        return new ItemService(sqlStore, cacheStore);
    }
}

public class BeanMethodParams {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(StoreCfg.class);
        ctx.getBean(ItemService.class).saveItem("order-99");
        ctx.close();
    }
}
```

How to run: `java BeanMethodParams.java`

`@Bean` method parameters are automatically resolved from the container. `Store sqlStore` matches by `@Primary`; `@Qualifier("cacheStore")` selects the second bean by name.

### Level 3 — Advanced

`@Bean` with `@Scope`, `@Lazy`, `@DependsOn`, and intercepted inter-bean calls verifying singleton semantics.

```java
// BeanMethodAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.context.*;

class ConnectionPool {
    private static int instanceCount = 0;
    private final int id;

    ConnectionPool() {
        this.id = ++instanceCount;
        System.out.println("[Pool] Connection pool #" + id + " created");
    }

    public String borrow() { return "conn-from-pool-" + id; }
}

class AuditLog {
    AuditLog() { System.out.println("[Audit] AuditLog initialized"); }
    public void log(String entry) { System.out.println("[Audit] " + entry); }
}

class OrderService {
    private final ConnectionPool pool;
    private final AuditLog audit;

    OrderService(ConnectionPool p, AuditLog a) {
        this.pool = p; this.audit = a;
        System.out.println("[OrderService] created with pool#" + p.borrow());
    }

    public void placeOrder(int id) {
        audit.log("Order #" + id + " via " + pool.borrow());
        System.out.println("[Order] placed order " + id);
    }
}

class ReportService {
    // Lazily created — only when first requested
    ReportService(ConnectionPool pool) {
        System.out.println("[ReportService] created with " + pool.borrow());
    }
    public void report() { System.out.println("[Report] generating report"); }
}

@Configuration
class AppCfg {
    @Bean
    @DependsOn("auditLog")  // ensure auditLog is ready first
    public ConnectionPool connectionPool() {
        return new ConnectionPool();
    }

    @Bean
    public AuditLog auditLog() {
        return new AuditLog();
    }

    @Bean
    public OrderService orderService(ConnectionPool pool, AuditLog audit) {
        return new OrderService(pool, audit);
    }

    @Bean @Lazy
    public ReportService reportService(ConnectionPool pool) {
        // Created only when getBean(ReportService.class) is first called
        return new ReportService(pool);
    }
}

public class BeanMethodAdvanced {
    public static void main(String[] args) {
        System.out.println("=== Context starting ===");
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);

        // ReportService is @Lazy — NOT yet created at context startup
        System.out.println("\n=== Using OrderService ===");
        ctx.getBean(OrderService.class).placeOrder(1);
        ctx.getBean(OrderService.class).placeOrder(2);

        // Verify ConnectionPool is singleton
        System.out.println("\nSame pool? " + (
            ctx.getBean(ConnectionPool.class) == ctx.getBean(ConnectionPool.class)));

        // Trigger lazy ReportService creation on first access
        System.out.println("\n=== Accessing ReportService (lazy) ===");
        ctx.getBean(ReportService.class).report();

        ctx.close();
    }
}
```

How to run: `java BeanMethodAdvanced.java`

`AuditLog` is created before `ConnectionPool` due to `@DependsOn`. `ReportService` creation is deferred — the log message appears only when `getBean(ReportService.class)` is called, not at startup.

## 6. Walkthrough

Execution order for Level 3:

1. **`AnnotationConfigApplicationContext` created** — `ConfigurationClassPostProcessor` processes `AppCfg`.
2. **`@DependsOn("auditLog")` on `connectionPool`** — Spring forces `auditLog()` to run before `connectionPool()`.
3. **`auditLog()` called** — `new AuditLog()` created. Prints `[Audit] AuditLog initialized`.
4. **`connectionPool()` called** — `new ConnectionPool()` created. Prints `[Pool] Connection pool #1 created`.
5. **`orderService(pool, audit)` called** — receives singleton pool and audit log. Prints `[OrderService] created with pool#conn-from-pool-1`.
6. **`reportService` skipped** — `@Lazy` defers creation.
7. **`placeOrder(1)` and `placeOrder(2)`** — both use the same pool singleton and audit log singleton.
8. **`getBean(ReportService.class)` — first access** — `reportService(pool)` called now. `pool` injected is the same singleton. Prints `[ReportService] created...`.

Expected output:
```
=== Context starting ===
[Audit] AuditLog initialized
[Pool] Connection pool #1 created
[OrderService] created with pool#conn-from-pool-1

=== Using OrderService ===
[Audit] Order #1 via conn-from-pool-1
[Order] placed order 1
[Audit] Order #2 via conn-from-pool-1
[Order] placed order 2

Same pool? true

=== Accessing ReportService (lazy) ===
[ReportService] created with conn-from-pool-1
[Report] generating report
```

## 7. Gotchas & takeaways

> `@Bean` method parameters are autowired by the container — you never call them yourself. If you add a parameter without a matching bean in the context, Spring throws `NoSuchBeanDefinitionException` at startup.

> In a `@Component` class (lite mode), calling `beanMethodA()` from `beanMethodB()` creates a **new object** each time — it's a plain Java call. This is the most common source of "I have two connection pools" bugs when people switch from `@Configuration` to `@Component`.

- Return type: use the most specific interface, not the concrete class, so that autowiring by type is unambiguous.
- Name defaults to method name; add aliases with `@Bean({"primary", "main"})`.
- `@Scope` on a `@Bean` method overrides `singleton`; add `proxyMode = ScopedProxyMode.TARGET_CLASS` when injecting a short-lived bean into a singleton.
- `@PostConstruct` / `@PreDestroy` on the returned object run normally. Also see `initMethod` / `destroyMethod` attributes on `@Bean` for third-party classes.
- `@Bean` methods may be `static` — useful for `BeanFactoryPostProcessor` beans that must be available before the config class is instantiated.
