---
card: spring-framework
gi: 29
slug: what-a-spring-bean-is
title: What a Spring bean is
---

## 1. What it is

A **Spring bean** is any object whose lifecycle — creation, dependency injection, and destruction — is managed by the Spring IoC container.

A bean is defined by a **bean definition**: a metadata record that tells the container:
- Which class to instantiate
- How to construct it (constructor args, factory method)
- What scope to use (singleton, prototype, request, ...)
- What init and destroy methods to call
- What other beans to inject

You declare beans via `@Component` annotations, `@Bean` methods in `@Configuration` classes, or XML `<bean>` elements. The container creates and manages instances from these declarations.

Key point: not every Java object is a bean. `new Product("Laptop", 999)` creates a plain object — Spring knows nothing about it. Only objects registered with the container are beans.

In one sentence: **A Spring bean is an object that the IoC container creates, configures, wires, and destroys — it is the basic unit of a Spring application.**

## 2. Why & when

Beans are how you structure a Spring application's collaborating services. Any object that:
- Has dependencies on other objects,
- Should be reused (singleton) across the app,
- Has a lifecycle (needs init / cleanup),
- Benefits from AOP (transactions, caching, security),

... should be a bean. Non-bean objects are typically simple value objects (`Money`, `Address`, `Product`) or short-lived request-specific data structures.

The distinction matters because:
- Only beans get `@Autowired` dependencies injected.
- Only beans get `@Transactional`, `@Cacheable`, `@Async` applied.
- Only beans have `@PostConstruct` / `@PreDestroy` lifecycle hooks.

## 3. Core concept

A bean has three distinct aspects:

```
Bean = class + definition + instance

1. Class          — the Java type (e.g., OrderService.class)
2. BeanDefinition — metadata (scope, deps, init method, ...)
3. Instance       — the actual object in memory (singleton: one per context)
```

Scopes control how many instances exist:

| Scope | Instances | Use case |
|---|---|---|
| `singleton` | 1 per context | Stateless services, repositories |
| `prototype` | 1 per `getBean()` call | Stateful helpers, command objects |
| `request` | 1 per HTTP request | Web layer state |
| `session` | 1 per HTTP session | User session state |

The default is `singleton`. Over 99% of Spring beans are singletons.

A minimal bean declaration (three equivalent forms):

```java
// Annotation
@Service public class OrderService { ... }

// Java config
@Bean public OrderService orderService() { return new OrderService(); }

// XML
// <bean id="orderService" class="com.example.OrderService"/>
```

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bean lifecycle: BeanDefinition in registry, container creates instance, injects deps, calls init, exposes to app, calls destroy on close">
  <defs>
    <marker id="a29" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- BeanDefinition -->
  <rect x="10" y="70" width="130" height="76" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="75" y="92" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">BeanDefinition</text>
  <text x="75" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">class, scope</text>
  <text x="75" y="121" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">init/destroy</text>
  <text x="75" y="134" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">constructor args</text>

  <!-- Container -->
  <rect x="200" y="30" width="155" height="46" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="277" y="58" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">IoC Container</text>

  <line x1="140" y1="108" x2="198" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a29)"/>

  <!-- Lifecycle steps -->
  <rect x="200" y="100" width="120" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="260" y="123" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">instantiate()</text>

  <rect x="200" y="148" width="120" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="260" y="171" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">injectDeps()</text>

  <rect x="340" y="100" width="120" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="400" y="123" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@PostConstruct</text>

  <rect x="340" y="148" width="120" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="400" y="171" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">ready → app uses</text>

  <rect x="480" y="124" width="120" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="540" y="147" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@PreDestroy</text>

  <line x1="277" y1="76" x2="260" y2="98" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a29)"/>
  <line x1="260" y1="136" x2="260" y2="146" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a29)"/>
  <line x1="320" y1="118" x2="338" y2="118" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a29)"/>
  <line x1="400" y1="136" x2="400" y2="146" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a29)"/>
  <line x1="460" y1="166" x2="478" y2="142" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="3,2" marker-end="url(#a29)"/>
  <text x="485" y="173" fill="#8b949e" font-size="7" font-family="sans-serif">on ctx.close()</text>
</svg>

The container takes a `BeanDefinition`, creates the object, injects its dependencies, calls init hooks, exposes it to the app, and finally calls destroy hooks when the context closes.

## 5. Runnable example

Scenario: a reporting pipeline with a `DataLoader`, a `ReportFormatter`, and a `ReportService`. We show what it means for each one to be a bean versus a plain object.

### Level 1 — Basic

Identify which objects are beans (managed) and which are plain objects (not managed).

```java
// WhatIsABeanDemo.java — run with: java WhatIsABeanDemo.java
import java.util.*;

public class WhatIsABeanDemo {

    // Plain value object — NOT a bean (no lifecycle, no DI)
    record ReportRow(String label, double value) {}

    // Service — IS a bean (has dep, has lifecycle)
    static class DataLoader {
        private final String source;
        DataLoader(String source) {
            this.source = source;
            System.out.println("  [BEAN] DataLoader created (source=" + source + ")");
        }
        List<ReportRow> load() {
            return List.of(new ReportRow("Q1 Revenue", 125000.0),
                           new ReportRow("Q2 Revenue", 148000.0));
        }
    }

    static class ReportFormatter {
        ReportFormatter() { System.out.println("  [BEAN] ReportFormatter created"); }
        String format(List<ReportRow> rows) {
            var sb = new StringBuilder("=== Report ===\n");
            rows.forEach(r -> sb.append(String.format("  %-15s $%,.0f%n", r.label(), r.value())));
            return sb.toString();
        }
    }

    static class ReportService {
        private final DataLoader      loader;
        private final ReportFormatter formatter;

        ReportService(DataLoader loader, ReportFormatter formatter) {
            this.loader = loader; this.formatter = formatter;
            System.out.println("  [BEAN] ReportService created + deps injected");
        }

        void generateReport() {
            List<ReportRow> rows = loader.load();
            System.out.println(formatter.format(rows));
        }
    }

    // Minimal bean container
    static class BeanContainer {
        private final Map<Class<?>, Object> beans = new LinkedHashMap<>();
        <T> void registerBean(Class<T> type, T bean) {
            beans.put(type, bean);
            System.out.println("  [CTX] Registered bean: " + bean.getClass().getSimpleName());
        }
        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) { return (T) beans.get(type); }
    }

    public static void main(String[] args) {
        System.out.println("=== Container creates and wires beans ===");
        BeanContainer ctx = new BeanContainer();

        DataLoader      loader    = new DataLoader("sales_db");
        ReportFormatter formatter = new ReportFormatter();
        ReportService   service   = new ReportService(loader, formatter);

        ctx.registerBean(DataLoader.class,      loader);
        ctx.registerBean(ReportFormatter.class, formatter);
        ctx.registerBean(ReportService.class,   service);

        System.out.println("\n=== App uses the bean ===");
        ctx.getBean(ReportService.class).generateReport();

        System.out.println("=== NOT beans: value objects created freely ===");
        ReportRow r = new ReportRow("Q3 Revenue", 160000.0);
        System.out.println("  Plain object (not in container): " + r);
    }
}
```

How to run: `java WhatIsABeanDemo.java`

`DataLoader`, `ReportFormatter`, and `ReportService` are beans — the container manages them. `ReportRow` is a plain value object — created with `new`, not registered, not injected. You can create hundreds of `ReportRow` objects; there is always exactly one `ReportService` singleton.

### Level 2 — Intermediate

Add scope: one singleton service and a prototype row-builder that returns a fresh instance on every call.

```java
// WhatIsABeanDemo2.java — run with: java WhatIsABeanDemo2.java
import java.util.*;
import java.util.function.*;

public class WhatIsABeanDemo2 {

    record ReportRow(String label, double value) {}

    // SINGLETON — one instance, shared
    static class DataLoader {
        private int callCount = 0;
        DataLoader() { System.out.println("  [SINGLETON] DataLoader created (once)"); }
        List<ReportRow> load() {
            callCount++;
            return List.of(new ReportRow("Revenue", 125000.0 * callCount));
        }
        int getCallCount() { return callCount; }
    }

    // PROTOTYPE — new instance on every getBean()
    static class ReportBuilder {
        private final List<String> steps = new ArrayList<>();
        ReportBuilder() { System.out.println("  [PROTOTYPE] ReportBuilder created (new instance)"); }
        void addStep(String s) { steps.add(s); }
        String build(List<ReportRow> rows) {
            var sb = new StringBuilder("Report via " + steps + ":\n");
            rows.forEach(r -> sb.append("  ").append(r.label()).append(": $").append(r.value()).append("\n"));
            return sb.toString();
        }
    }

    static class ScopedContainer {
        private final Map<Class<?>, Object>            singletons = new LinkedHashMap<>();
        private final Map<Class<?>, Supplier<Object>>  prototypes = new LinkedHashMap<>();

        <T> void singleton(Class<T> type, T instance) { singletons.put(type, instance); }
        <T> void prototype(Class<T> type, Supplier<T> factory) {
            prototypes.put(type, (Supplier<Object>) factory);
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) {
            if (singletons.containsKey(type)) return (T) singletons.get(type);
            if (prototypes.containsKey(type)) return (T) prototypes.get(type).get();
            throw new RuntimeException("No bean: " + type.getSimpleName());
        }
    }

    public static void main(String[] args) {
        ScopedContainer ctx = new ScopedContainer();
        ctx.singleton(DataLoader.class, new DataLoader());
        ctx.prototype(ReportBuilder.class, ReportBuilder::new);

        System.out.println("\n=== Singleton: same instance every call ===");
        DataLoader l1 = ctx.getBean(DataLoader.class);
        DataLoader l2 = ctx.getBean(DataLoader.class);
        System.out.println("  Same instance: " + (l1 == l2));  // true

        System.out.println("\n=== Prototype: fresh instance every call ===");
        ReportBuilder b1 = ctx.getBean(ReportBuilder.class);
        ReportBuilder b2 = ctx.getBean(ReportBuilder.class);
        System.out.println("  Same instance: " + (b1 == b2));  // false

        b1.addStep("load");
        b1.addStep("format");
        b2.addStep("load-only");  // independent from b1

        System.out.println("\n=== Using beans ===");
        List<ReportRow> rows = l1.load();
        System.out.println(b1.build(rows));
        System.out.println("DataLoader call count: " + l1.getCallCount());
    }
}
```

How to run: `java WhatIsABeanDemo2.java`

`DataLoader` is a singleton — `l1 == l2` is true, same object reference. `ReportBuilder` is prototype-scoped — `b1` and `b2` are different objects with independent state. `b1.steps` and `b2.steps` are separate lists. This is the critical scope distinction in Spring.

### Level 3 — Advanced

Add lifecycle callbacks: `@PostConstruct`-equivalent init and `@PreDestroy`-equivalent destroy, demonstrating that beans are more than plain objects.

```java
// WhatIsABeanDemo3.java — run with: java WhatIsABeanDemo3.java
import java.util.*;
import java.util.concurrent.*;

public class WhatIsABeanDemo3 {

    record ReportRow(String label, double value) {}

    // Bean with full lifecycle: init, use, destroy
    static class DataSource {
        private final String url;
        private boolean      connected = false;

        DataSource(String url) { this.url = url; }

        // @PostConstruct — called after construction and DI
        void init() {
            System.out.println("  [@PostConstruct] DataSource.init() — opening connection to " + url);
            connected = true;
        }

        List<ReportRow> query(String sql) {
            if (!connected) throw new IllegalStateException("DataSource not initialized");
            System.out.println("  [QUERY] " + sql);
            return List.of(new ReportRow("Q1", 125000.0), new ReportRow("Q2", 148000.0));
        }

        // @PreDestroy — called before container closes
        void destroy() {
            System.out.println("  [@PreDestroy] DataSource.destroy() — closing connection to " + url);
            connected = false;
        }
    }

    static class ReportService {
        private final DataSource ds;
        ReportService(DataSource ds) {
            this.ds = ds;
            System.out.println("  [BEAN] ReportService created");
        }

        void generate() {
            List<ReportRow> rows = ds.query("SELECT label, value FROM quarterly_revenue");
            System.out.println("  === Report ===");
            rows.forEach(r -> System.out.printf("  %-5s $%,.0f%n", r.label(), r.value()));
        }
    }

    // Full lifecycle container
    static class LifecycleContainer {
        record BeanRecord(Object bean, String initMethod, String destroyMethod) {}
        private final List<BeanRecord> records = new ArrayList<>();

        void register(Object bean, String init, String destroy) throws Exception {
            if (init != null) {
                bean.getClass().getDeclaredMethod(init).invoke(bean);
            }
            records.add(new BeanRecord(bean, init, destroy));
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) {
            return (T) records.stream()
                .map(BeanRecord::bean)
                .filter(b -> type.isAssignableFrom(b.getClass()))
                .findFirst().orElseThrow();
        }

        void close() throws Exception {
            System.out.println("\n[CTX] Shutdown — calling @PreDestroy (reverse order)...");
            List<BeanRecord> reversed = new ArrayList<>(records);
            Collections.reverse(reversed);
            for (BeanRecord r : reversed) {
                if (r.destroyMethod() != null) {
                    System.out.println("  Destroying: " + r.bean().getClass().getSimpleName());
                    r.bean().getClass().getDeclaredMethod(r.destroyMethod()).invoke(r.bean());
                }
            }
        }
    }

    public static void main(String[] args) throws Exception {
        LifecycleContainer ctx = new LifecycleContainer();

        DataSource  ds  = new DataSource("jdbc:postgresql://prod:5432/reports");
        ReportService rs = new ReportService(ds);

        System.out.println("=== Container startup ===");
        ctx.register(ds,  "init",    "destroy");
        ctx.register(rs,  null,      null);

        System.out.println("\n=== Application running ===");
        ctx.getBean(ReportService.class).generate();

        System.out.println("\n=== Attempt to use DataSource before init (shows why init matters) ===");
        DataSource raw = new DataSource("jdbc:postgresql://prod:5432/reports");
        // raw is NOT a bean — init() was never called
        try { raw.query("SELECT 1"); }
        catch (IllegalStateException e) { System.out.println("  Plain object (no init): " + e.getMessage()); }

        ctx.close();
    }
}
```

How to run: `java WhatIsABeanDemo3.java`

`DataSource` the bean has `init()` called by the container after construction — it opens the connection. `DataSource` the plain object (`raw`) never gets `init()` called — querying it throws. This shows concretely why being a bean (container-managed) differs from being a plain object — lifecycle hooks run, making the object fully usable.

## 6. Walkthrough

**Level 3 — container registration and lifecycle:**

```
ctx.register(ds, "init", "destroy")
  → ds.init() called
      → "[@PostConstruct] DataSource.init() — opening connection to jdbc:..."
      → connected = true
  → BeanRecord{bean=ds, init="init", destroy="destroy"} stored

ctx.register(rs, null, null)
  → no init method → skipped
  → BeanRecord{bean=rs, ...} stored
```

**`ctx.getBean(ReportService.class).generate()` execution:**
```
generate()
  → ds.query("SELECT label, value FROM quarterly_revenue")
      → connected == true → proceeds
      → "[QUERY] SELECT label, value FROM quarterly_revenue"
      → returns [ReportRow(Q1, 125000), ReportRow(Q2, 148000)]
  → prints report rows
```

**`raw.query("SELECT 1")` (plain object, no init):**
```
query("SELECT 1")
  → connected == false (init() never called)
  → throw IllegalStateException("DataSource not initialized")
```

**`ctx.close()` — reverse order:**
```
reversed records: [rs, ds]
  rs: destroyMethod == null → skip
  ds: destroyMethod == "destroy"
    → ds.destroy()
        → "[PreDestroy] DataSource.destroy() — closing connection..."
        → connected = false
```

**Bean vs plain object — difference summary:**

| Aspect | Bean | Plain object (`new`) |
|---|---|---|
| Creation | container calls constructor | your code calls `new` |
| Dependencies | injected by container | passed manually |
| Init | `@PostConstruct` called | never called |
| Destroy | `@PreDestroy` called on close | GC, no callback |
| AOP | `@Transactional` / proxied | no proxying |

## 7. Gotchas & takeaways

> **Calling `new` inside a Spring component creates a plain object, not a bean.** `new OrderService()` inside a `@Service` class bypasses the container — no injection, no AOP, no lifecycle. Inject `OrderService` via the constructor instead.

> **`@PostConstruct` runs after ALL dependencies are injected** — it is safe to use injected fields. Do not perform heavy initialization in the constructor (injected fields are null then); use `@PostConstruct` instead.

- Beans are not just objects — they carry metadata (scope, init method, dependencies) stored as `BeanDefinition` objects in the container's registry.
- The `singleton` scope is the default and makes beans stateless and thread-safe by convention. Never store mutable request-specific data in a singleton bean field.
- Prototype-scoped beans get no `@PreDestroy` call — Spring hands them off after creation and forgets them.
- You can check if an object is a Spring-managed bean proxy with `AopUtils.isAopProxy(obj)` — useful when debugging why `@Transactional` is not applying.
- `@Bean(initMethod="init", destroyMethod="close")` lets you add lifecycle hooks to third-party classes you cannot annotate.
