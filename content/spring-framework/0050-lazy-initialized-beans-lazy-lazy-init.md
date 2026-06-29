---
card: spring-framework
gi: 50
slug: lazy-initialized-beans-lazy-lazy-init
title: Lazy-initialized beans @Lazy / lazy-init
---

## 1. What it is

By default, Spring creates all singleton beans **eagerly** at container startup — every `@Component`, `@Service`, and `@Bean` is instantiated during `refresh()`. **Lazy initialization** defers a bean's creation until it is first requested.

```java
// Eager (default) — created at startup
@Component
public class HeavyReportService { ... }

// Lazy — created only when first injected or getBean() called
@Component
@Lazy
public class HeavyReportService { ... }

// XML equivalent
// <bean id="heavyReportService" class="..." lazy-init="true"/>

// Entire application lazy (Spring Boot 3.x)
// spring.main.lazy-initialization=true
```

When a lazy bean is injected into an eager bean, Spring injects a CGLIB proxy. The proxy defers the actual bean creation until a method on it is first called.

In one sentence: **`@Lazy` defers bean creation from container startup to first use — useful for expensive beans that are not always needed, at the cost of detecting missing-dependency errors later (at first call rather than at startup).**

## 2. Why & when

Use lazy initialization when:

- **A bean is expensive to create** (opens a connection, loads a large dataset, starts a thread pool) and is not always needed in every application run or request.
- **Optional feature beans** — if a feature is disabled via config, its bean is never requested and never created.
- **Speeding up test startup** — `@SpringBootTest` with `spring.main.lazy-initialization=true` starts the context faster by only creating beans that the test actually uses.
- **Circular dependency workaround** — `@Lazy` on one injection point breaks the cycle by injecting a proxy.

Avoid lazy initialization for beans that are almost always needed — the first-call cost hits at an unpredictable moment in production.

## 3. Core concept

```
Eager (default):
  refresh() → pre-instantiate singletons:
    new HeavyReportService()  ← happens NOW at startup
    → any missing dep → fail fast ✓
    → startup is slow if many heavy beans

Lazy:
  refresh() → sees @Lazy → skips pre-instantiation
  → "heavyReportService" registered but not created

  First getBean("heavyReportService") or first injection method call:
    → now creates HeavyReportService
    → any missing dep → fail here (runtime, not startup) ✗

Lazy + injected into eager bean:
  eager B has:   @Lazy @Autowired HeavyReportService service;
  → Spring injects a CGLIB proxy for HeavyReportService
  → B.service.generateReport() → proxy → create real HeavyReportService → delegate
```

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Eager vs lazy: eager creates bean at refresh; lazy creates bean on first use via proxy">
  <defs>
    <marker id="a50" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b50" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Eager timeline -->
  <text x="155" y="18" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Eager (default)</text>
  <rect x="10" y="28" width="130" height="38" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="75" y="52" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">refresh() → new Bean()</text>
  <line x1="140" y1="47" x2="170" y2="47" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a50)"/>
  <rect x="170" y="28" width="130" height="38" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="235" y="52" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Bean ready ✓</text>
  <text x="155" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Missing dep detected at startup</text>

  <!-- Lazy timeline -->
  <text x="155" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Lazy</text>
  <rect x="10" y="118" width="130" height="38" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="135" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">refresh() → skip</text>
  <text x="75" y="150" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(proxy registered)</text>
  <line x1="140" y1="137" x2="170" y2="137" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b50)"/>
  <rect x="170" y="118" width="130" height="38" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="235" y="135" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">first method call →</text>
  <text x="235" y="150" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">new Bean() now</text>
  <text x="155" y="172" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Missing dep detected at first call (runtime)</text>

  <!-- Global lazy label -->
  <rect x="390" y="65" width="280" height="80" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="530" y="88" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">spring.main.lazy-initialization=true</text>
  <text x="530" y="106" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">→ ALL beans lazy by default</text>
  <text x="530" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">→ faster test startup</text>
  <text x="530" y="138" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">→ add @Eager on critical beans</text>
</svg>

Eager: bean created at `refresh()`, errors visible at startup. Lazy: bean created at first method call, errors surface at runtime.

## 5. Runnable example

Scenario: a `ReportController` eagerly created, depending on a `HeavyReportEngine` (expensive — loads templates from disk). With `@Lazy`, the engine is only created when a report is actually requested.

### Level 1 — Basic

Simple lazy vs eager comparison: show when each bean is created.

```java
// LazyBeanDemo.java — run with: java LazyBeanDemo.java

public class LazyBeanDemo {

    // Simulated expensive bean
    static class HeavyReportEngine {
        HeavyReportEngine() {
            System.out.println("  [EXPENSIVE] HeavyReportEngine created — loading templates...");
            // Simulate expensive init: file I/O, DB queries, etc.
        }
        String generate(String type) { return "Report[" + type + "]"; }
    }

    // Cheap bean — always needed
    static class HealthCheckService {
        HealthCheckService() { System.out.println("  [CHEAP] HealthCheckService created"); }
        String check() { return "OK"; }
    }

    // Container with lazy support
    static class Ctx {
        private HealthCheckService health;
        private HeavyReportEngine  engine;
        private boolean            engineCreated = false;

        void refresh() {
            System.out.println("=== Container refresh() ===");
            // Eager beans: create now
            health = new HealthCheckService();
            // Lazy beans: deferred — engine NOT created here
            System.out.println("  [LAZY] HeavyReportEngine registered but NOT created yet");
            System.out.println("  [CTX] refresh() complete");
        }

        HeavyReportEngine getReportEngine() {
            if (!engineCreated) {
                System.out.println("  [LAZY] First access — creating HeavyReportEngine now");
                engine = new HeavyReportEngine();
                engineCreated = true;
            }
            return engine;
        }

        HealthCheckService getHealth() { return health; }
    }

    public static void main(String[] args) {
        Ctx ctx = new Ctx();
        ctx.refresh();

        System.out.println("\n=== Health check (uses eager bean) ===");
        System.out.println("  " + ctx.getHealth().check());
        System.out.println("  Note: HeavyReportEngine not created yet");

        System.out.println("\n=== First report request (triggers lazy creation) ===");
        String result = ctx.getReportEngine().generate("Q1 Sales");
        System.out.println("  " + result);

        System.out.println("\n=== Second report request (reuses existing instance) ===");
        result = ctx.getReportEngine().generate("Q2 Sales");
        System.out.println("  " + result);
        System.out.println("  HeavyReportEngine was created exactly ONCE");
    }
}
```

How to run: `java LazyBeanDemo.java`

`HealthCheckService` is created during `refresh()`. `HeavyReportEngine` is not created until `getReportEngine()` is first called. The second call reuses the cached instance. Container startup is faster because the expensive bean is skipped.

### Level 2 — Intermediate

Lazy bean injected into eager bean via a proxy — the proxy intercepts the first method call.

```java
// LazyBeanDemo2.java — run with: java LazyBeanDemo2.java
import java.lang.reflect.*;
import java.util.function.Supplier;

public class LazyBeanDemo2 {

    interface ReportEngine {
        String generate(String type);
        String status();
    }

    static class HeavyReportEngine implements ReportEngine {
        private final String version;
        HeavyReportEngine(String version) {
            System.out.println("  [EXPENSIVE] HeavyReportEngine v" + version + " created");
            this.version = version;
        }
        @Override public String generate(String type) { return "Report[" + type + " v" + version + "]"; }
        @Override public String status() { return "ReportEngine v" + version + " ready"; }
    }

    // CGLIB-style lazy proxy: wraps a Supplier, resolves on first method call
    @SuppressWarnings("unchecked")
    static <T> T lazyProxy(Class<T> iface, Supplier<T> factory) {
        Object[] holder = {null};
        return (T) Proxy.newProxyInstance(
            iface.getClassLoader(), new Class<?>[]{iface},
            (proxy, method, callArgs) -> {
                if (holder[0] == null) {
                    System.out.println("  [PROXY] first call to " + method.getName() + "() → creating real bean");
                    holder[0] = factory.get();
                }
                return method.invoke(holder[0], callArgs);
            }
        );
    }

    static class ReportController {
        private final ReportEngine engine;  // may be a lazy proxy

        ReportController(ReportEngine engine) {
            System.out.println("  [EAGER] ReportController created (engine=" + engine.getClass().getSimpleName() + ")");
            this.engine = engine;
        }

        String handleReport(String type) {
            System.out.println("  [CTRL] handleReport(" + type + ")");
            return engine.generate(type);
        }

        String handleStatus() {
            return engine.status();
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Container refresh() ===");
        // Lazy proxy for HeavyReportEngine — factory called only on first method invocation
        ReportEngine lazyEngine = lazyProxy(ReportEngine.class,
            () -> new HeavyReportEngine("2.5.1"));

        // ReportController is eager and gets the proxy injected
        ReportController ctrl = new ReportController(lazyEngine);
        System.out.println("  [CTX] refresh() complete — HeavyReportEngine NOT created yet");

        System.out.println("\n=== Handling /health (no report engine needed) ===");
        System.out.println("  health: OK");

        System.out.println("\n=== First /report request (triggers lazy creation) ===");
        System.out.println("  " + ctrl.handleReport("Annual Revenue"));

        System.out.println("\n=== Second /report request (reuses instance) ===");
        System.out.println("  " + ctrl.handleReport("Customer Churn"));

        System.out.println("\n=== /status request ===");
        System.out.println("  " + ctrl.handleStatus());
    }
}
```

How to run: `java LazyBeanDemo2.java`

`ReportController` receives a JDK proxy for `ReportEngine` at construction. The proxy's holder is null. On the first call to `engine.generate()`, the proxy creates the real `HeavyReportEngine`. Subsequent calls skip the creation check and call the cached instance directly. Health checks before any report hit never trigger the expensive creation.

### Level 3 — Advanced

Multiple lazy beans with creation-time tracking, demonstrating startup time savings and per-feature lazy initialization.

```java
// LazyBeanDemo3.java — run with: java LazyBeanDemo3.java
import java.util.*;
import java.util.function.Supplier;

public class LazyBeanDemo3 {

    // --- Feature interfaces ---
    interface PdfExporter    { byte[] export(String data); }
    interface ExcelExporter  { byte[] export(String data); }
    interface ChartRenderer  { String render(String data); }

    // --- Expensive implementations ---
    static class ITextPdfExporter implements PdfExporter {
        ITextPdfExporter() { simulateSlowInit("ITextPdfExporter", 80); }
        @Override public byte[] export(String d) { return ("PDF:" + d).getBytes(); }
    }

    static class ApachePoiExcelExporter implements ExcelExporter {
        ApachePoiExcelExporter() { simulateSlowInit("ApachePoiExcelExporter", 120); }
        @Override public byte[] export(String d) { return ("XLSX:" + d).getBytes(); }
    }

    static class D3ChartRenderer implements ChartRenderer {
        D3ChartRenderer() { simulateSlowInit("D3ChartRenderer", 60); }
        @Override public String render(String d) { return "CHART:" + d; }
    }

    static void simulateSlowInit(String name, int fakeMs) {
        System.out.println("  [INIT " + fakeMs + "ms] " + name + " created");
    }

    // --- Lazy bean registry ---
    static class BeanRegistry {
        private final Map<String, Supplier<?>> factories = new LinkedHashMap<>();
        private final Map<String, Object>      cache     = new LinkedHashMap<>();
        private final List<String>             created   = new ArrayList<>();
        private long startupMs;

        <T> void registerLazy(String name, Supplier<T> factory) {
            factories.put(name, factory);
            System.out.println("  [REG-LAZY] '" + name + "' registered (not created)");
        }

        <T> void registerEager(String name, Supplier<T> factory) {
            Object bean = factory.get();
            cache.put(name, bean);
            created.add(name);
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) {
            if (!cache.containsKey(name)) {
                if (!factories.containsKey(name))
                    throw new RuntimeException("No bean: " + name);
                System.out.println("  [LAZY-INIT] '" + name + "' first access → creating");
                Object bean = factories.get(name).get();
                cache.put(name, bean);
                created.add(name);
            }
            return (T) cache.get(name);
        }

        void markStartupComplete(long ms) {
            this.startupMs = ms;
            System.out.printf("  [CTX] refresh() complete in %dms. Lazy beans not created: %s%n",
                ms, factories.keySet().stream()
                    .filter(k -> !cache.containsKey(k)).toList());
        }

        void printSummary() {
            System.out.println("  Creation order: " + created);
            System.out.println("  Total beans created: " + cache.size() + " / " + factories.size() + " lazy + eager");
        }
    }

    // --- Application controller ---
    static class ExportController {
        private final BeanRegistry registry;
        ExportController(BeanRegistry r) { this.registry = r; }

        String exportPdf(String data) {
            PdfExporter e = registry.getBean("pdfExporter");
            return new String(e.export(data)) + " size=" + e.export(data).length + "b";
        }

        String exportExcel(String data) {
            ExcelExporter e = registry.getBean("excelExporter");
            return new String(e.export(data)) + " size=" + e.export(data).length + "b";
        }

        String renderChart(String data) {
            ChartRenderer r = registry.getBean("chartRenderer");
            return r.render(data);
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Container refresh() ===");
        long t0 = System.currentTimeMillis();
        BeanRegistry registry = new BeanRegistry();

        // All three exporters are lazy — expensive; not always needed
        registry.registerLazy("pdfExporter",   ITextPdfExporter::new);
        registry.registerLazy("excelExporter", ApachePoiExcelExporter::new);
        registry.registerLazy("chartRenderer", D3ChartRenderer::new);

        // Controller is eager — always needed for routing
        ExportController ctrl = new ExportController(registry);
        registry.registerEager("exportController", () -> ctrl);

        long t1 = System.currentTimeMillis();
        registry.markStartupComplete(t1 - t0);

        System.out.println("\n=== Request 1: GET /export/pdf ===");
        System.out.println("  " + ctrl.exportPdf("Q1-Sales-Data"));

        System.out.println("\n=== Request 2: GET /export/pdf (reuse same instance) ===");
        System.out.println("  " + ctrl.exportPdf("Q2-Sales-Data"));

        System.out.println("\n=== Request 3: GET /render/chart ===");
        System.out.println("  " + ctrl.renderChart("revenue-2026"));

        System.out.println("\n=== No Excel request — ApachePoiExcelExporter never created ===");

        System.out.println("\n=== Registry summary ===");
        registry.printSummary();
    }
}
```

How to run: `java LazyBeanDemo3.java`

Three exporters are registered lazy. `ExportController` is eager. Container startup registers all three lazy beans without creating them. `ITextPdfExporter` is created on the first `/export/pdf` request. `D3ChartRenderer` is created on the `/render/chart` request. `ApachePoiExcelExporter` is never created because no Excel export is requested — it costs 0ms.

## 6. Walkthrough

**Level 3 — execution order:**

```
registry.registerLazy("pdfExporter", ITextPdfExporter::new)
  → factories["pdfExporter"] = ITextPdfExporter::new  (NOT called yet)

registry.registerLazy("excelExporter", ...)  → same, deferred
registry.registerLazy("chartRenderer",  ...)  → same, deferred
registry.registerEager("exportController", () -> ctrl)
  → factory called NOW → ctrl already exists → cache["exportController"] = ctrl

markStartupComplete: lazy beans not created: [pdfExporter, excelExporter, chartRenderer]

ctrl.exportPdf("Q1-Sales-Data"):
  → registry.getBean("pdfExporter")
      → cache miss → factory.get() = new ITextPdfExporter() → "[INIT 80ms] ..."
      → cache["pdfExporter"] = ITextPdfExporter
  → e.export("Q1-Sales-Data") = "PDF:Q1-Sales-Data".getBytes()
  → return "PDF:Q1-Sales-Data size=16b"

ctrl.exportPdf("Q2-Sales-Data"):
  → registry.getBean("pdfExporter")
      → cache hit → return cached ITextPdfExporter (NOT re-created)
```

**Summary table:**

| Bean | Strategy | Created at |
|---|---|---|
| `pdfExporter` | lazy | first PDF request |
| `excelExporter` | lazy | never (no Excel request) |
| `chartRenderer` | lazy | first chart request |
| `exportController` | eager | container startup |

## 7. Gotchas & takeaways

> **Lazy beans fail at first use, not at startup.** If `HeavyReportEngine` has a missing dependency, the error surfaces when the first report request arrives — not at container startup. Under load, this can cause the first request to a feature to be slow and error-prone.

> **`@Lazy` on a constructor parameter injects a CGLIB/JDK proxy, not the real bean.** `instanceof HeavyReportEngine` on the injected field returns `false` — the field holds a proxy. This breaks identity checks, `equals()` comparisons, and reflection over the concrete class.

- `spring.main.lazy-initialization=true` makes all beans lazy globally — useful in test suites to reduce startup time. Pair with `@Lazy(false)` on critical beans (security filters, datasource) that must be verified at startup.
- `@Lazy` on a `@Bean` method in a `@Configuration` class applies lazy semantics to that specific bean.
- A lazy singleton is still a singleton — once created, the same instance is returned on every subsequent request. Prototype beans (`@Scope("prototype")`) always create a new instance regardless of `@Lazy`.
- `ObjectProvider<T>` (Spring 4.3+) is an alternative: inject a provider, call `provider.getIfAvailable()` to get the bean only if it exists — lazy by nature without proxying.
