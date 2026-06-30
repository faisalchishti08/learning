---
card: spring-framework
gi: 80
slug: lifecycle-mechanism-combination-order
title: Lifecycle mechanism combination order
---

## 1. What it is

When multiple lifecycle mechanisms are applied to the **same bean**, Spring fires them all in a fixed, deterministic order. At initialisation: `@PostConstruct` fires first, `InitializingBean.afterPropertiesSet()` fires second, and XML/annotation `init-method` fires last. At destruction (mirror image): `@PreDestroy` fires first, `DisposableBean.destroy()` fires second, and `destroy-method` fires last.

```java
@Component
public class ReportEngine implements InitializingBean, DisposableBean {

    @PostConstruct
    void postConstruct() { System.out.println("1 — @PostConstruct");  }  // ① first

    @Override
    public void afterPropertiesSet() {
        System.out.println("2 — afterPropertiesSet()"); }               // ② second

    void customInit() { System.out.println("3 — init-method"); }        // ③ third (via @Bean(initMethod=))

    @PreDestroy
    void preDestroy()  { System.out.println("1 — @PreDestroy"); }       // ① first

    @Override
    public void destroy() {
        System.out.println("2 — DisposableBean.destroy()"); }           // ② second

    void customDestroy() { System.out.println("3 — destroy-method"); }  // ③ third
}
```

In one sentence: **When multiple lifecycle mechanisms coexist on a single bean, Spring fires them in a fixed order — `@PostConstruct` → `afterPropertiesSet()` → `init-method` at init; `@PreDestroy` → `destroy()` → `destroy-method` at destroy — and all three always run, they do not replace each other.**

## 2. Why & when

Knowing the combination order matters when:

- You are **integrating with a library** that implements `InitializingBean` and you add `@PostConstruct` on a subclass — you must know your `@PostConstruct` runs before the library's `afterPropertiesSet()`.
- You add `@Bean(initMethod="customInit")` to a `@Configuration` class for a bean that already has `@PostConstruct` — both will fire.
- You are **migrating** from XML-based `init-method` to `@PostConstruct` and need to know if both are still active during the migration period.

Most of the time, use only ONE mechanism per bean. Mix them only when you have no choice (e.g., extending a third-party class).

## 3. Core concept

```
FIXED COMBINATION ORDER — same bean, all three present:

Init order:
  ① @PostConstruct      (JSR-250, via CommonAnnotationBeanPostProcessor)
  ② afterPropertiesSet() (InitializingBean interface)
  ③ init-method=""       (XML attribute / @Bean(initMethod=""))

Destroy order:
  ① @PreDestroy         (JSR-250, via CommonAnnotationBeanPostProcessor)
  ② destroy()            (DisposableBean interface)
  ③ destroy-method=""    (XML attribute / @Bean(destroyMethod=""))

Rules:
  ✓ All present mechanisms ALWAYS fire — none skips because another exists.
  ✓ A checked exception from ANY step aborts context startup (init)
     or logs a warning and continues (destroy).
  ✓ If the same method is wired to two mechanisms (e.g. named "init" and
     also annotated @PostConstruct), it fires TWICE — be careful with
     default-init-method + @PostConstruct on same method name.

Recommendation:
  Pick ONE mechanism per bean.
  Prefer @PostConstruct / @PreDestroy for application code.
  Use InitializingBean / DisposableBean for framework/library code.
  Use init-method / destroy-method for third-party classes you can't annotate.
```

## 4. Diagram

<svg viewBox="0 0 680 165" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="All three init and destroy mechanisms combined, showing exact firing order">
  <defs>
    <marker id="a80" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b80" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="153" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Same bean — all three mechanisms present — fixed firing order</text>

  <!-- INIT row -->
  <text x="12" y="45" fill="#6db33f" font-size="9" font-family="sans-serif">INIT:</text>
  <rect x="55"  y="33" width="150" height="28" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="51" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">① @PostConstruct</text>
  <line x1="205" y1="47" x2="215" y2="47" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a80)"/>
  <rect x="218" y="33" width="175" height="28" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="305" y="51" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">② afterPropertiesSet()</text>
  <line x1="393" y1="47" x2="403" y2="47" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a80)"/>
  <rect x="406" y="33" width="175" height="28" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="493" y="51" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">③ init-method="..."</text>

  <!-- DESTROY row -->
  <text x="12" y="95" fill="#8b949e" font-size="9" font-family="sans-serif">DEST:</text>
  <rect x="55"  y="83" width="150" height="28" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="101" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">① @PreDestroy</text>
  <line x1="205" y1="97" x2="215" y2="97" stroke="#8b949e" stroke-width="1.2" marker-end="url(#b80)"/>
  <rect x="218" y="83" width="175" height="28" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="305" y="101" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">② DisposableBean.destroy()</text>
  <line x1="393" y1="97" x2="403" y2="97" stroke="#8b949e" stroke-width="1.2" marker-end="url(#b80)"/>
  <rect x="406" y="83" width="175" height="28" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="493" y="101" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">③ destroy-method="..."</text>

  <!-- Rules -->
  <rect x="10" y="125" width="655" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.7"/>
  <text x="22" y="142" fill="#8b949e" font-size="8.5" font-family="monospace">All fire. None replaced by another. Prefer one per bean. @PostConstruct / @PreDestroy recommended.</text>
</svg>

Both rows fire in the order shown. The three mechanisms stack — they do not replace each other.

## 5. Runnable example

Scenario: an `AuditService` bean that inherits `afterPropertiesSet()` from a library base class, adds its own `@PostConstruct`, and is configured with an XML-style `init-method` — all three fire in sequence.

### Level 1 — Basic

One bean with all three init mechanisms — prove they all fire in order.

```java
// CombinationOrderDemo.java — run with: java CombinationOrderDemo.java
import java.util.*;

public class CombinationOrderDemo {

    @interface PostConstruct {}
    @interface PreDestroy    {}
    interface InitializingBean { void afterPropertiesSet() throws Exception; }
    interface DisposableBean   { void destroy()            throws Exception; }

    static class AuditService implements InitializingBean, DisposableBean {
        private String auditTarget;
        private int    retentionDays;
        private final List<String> log = new ArrayList<>();

        void setAuditTarget(String v)    { this.auditTarget    = v; }
        void setRetentionDays(int v)     { this.retentionDays  = v; }

        // ── INIT: fires 1st ──────────────────────────────────────────
        @PostConstruct
        void postConstruct() {
            log.add("1-postConstruct");
            System.out.println("  [①] @PostConstruct: auditTarget='" + auditTarget + "' (set by injection)");
            if (auditTarget == null || auditTarget.isBlank())
                throw new IllegalStateException("auditTarget required");
        }

        // ── INIT: fires 2nd ──────────────────────────────────────────
        @Override
        public void afterPropertiesSet() {
            log.add("2-afterPropertiesSet");
            System.out.println("  [②] afterPropertiesSet(): retentionDays=" + retentionDays);
            if (retentionDays < 1) throw new IllegalStateException("retentionDays must be >= 1");
        }

        // ── INIT: fires 3rd ──────────────────────────────────────────
        public void customInit() {
            log.add("3-customInit(init-method)");
            System.out.println("  [③] init-method customInit(): opening audit log stream");
        }

        // ── DESTROY: fires 1st ───────────────────────────────────────
        @PreDestroy
        void preDestroy() {
            log.add("4-preDestroy");
            System.out.println("  [①] @PreDestroy: flushing audit buffer");
        }

        // ── DESTROY: fires 2nd ───────────────────────────────────────
        @Override
        public void destroy() {
            log.add("5-destroy");
            System.out.println("  [②] DisposableBean.destroy(): closing audit connection");
        }

        // ── DESTROY: fires 3rd ───────────────────────────────────────
        public void customDestroy() {
            log.add("6-customDestroy(destroy-method)");
            System.out.println("  [③] destroy-method customDestroy(): writing shutdown entry");
        }

        void printLog() { System.out.println("[LOG] " + log); }
    }

    // ── simulated container ───────────────────────────────────────────
    static AuditService startContainer() throws Exception {
        AuditService svc = new AuditService();
        svc.setAuditTarget("ORDER_TABLE");
        svc.setRetentionDays(90);
        // Spring calls in this order:
        svc.postConstruct();        // ① @PostConstruct
        svc.afterPropertiesSet();   // ② InitializingBean
        svc.customInit();           // ③ init-method
        return svc;
    }

    static void stopContainer(AuditService svc) throws Exception {
        svc.preDestroy();           // ① @PreDestroy
        svc.destroy();              // ② DisposableBean
        svc.customDestroy();        // ③ destroy-method
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Startup ===");
        AuditService svc = startContainer();
        System.out.println("\n=== App running ===");
        System.out.println("=== Shutdown ===");
        stopContainer(svc);
        System.out.println();
        svc.printLog();
        System.out.println("[INIT ORDER CORRECT]    " + svc.log.subList(0, 3).equals(List.of("1-postConstruct","2-afterPropertiesSet","3-customInit(init-method)")));
        System.out.println("[DESTROY ORDER CORRECT] " + svc.log.subList(3, 6).equals(List.of("4-preDestroy","5-destroy","6-customDestroy(destroy-method)")));
    }
}
```

How to run: `java CombinationOrderDemo.java`

All six callbacks fire in order: `@PostConstruct` (1st), `afterPropertiesSet()` (2nd), `init-method` (3rd), then `@PreDestroy` (1st), `destroy()` (2nd), `destroy-method` (3rd). The assertions confirm the exact sequence.

### Level 2 — Intermediate

Extending a library class that uses `InitializingBean` — your `@PostConstruct` fires before the library's `afterPropertiesSet()`.

```java
// CombinationOrderDemo2.java — run with: java CombinationOrderDemo2.java
import java.util.*;

public class CombinationOrderDemo2 {

    @interface PostConstruct {}
    @interface PreDestroy    {}
    interface InitializingBean { void afterPropertiesSet() throws Exception; }
    interface DisposableBean   { void destroy()            throws Exception; }

    // ── "Library" base class (uses InitializingBean — can't change it) ──
    static abstract class AbstractCacheBean implements InitializingBean, DisposableBean {
        protected String cacheName;
        protected int    maxEntries;
        protected final List<String> log;

        AbstractCacheBean(List<String> log) { this.log = log; }

        void setCacheName(String v)   { this.cacheName  = v; }
        void setMaxEntries(int v)     { this.maxEntries  = v; }

        // Library's init logic — fires 2nd (after @PostConstruct)
        @Override
        public void afterPropertiesSet() throws Exception {
            log.add("AbstractCacheBean.afterPropertiesSet");
            System.out.println("  [②] AbstractCacheBean.afterPropertiesSet(): cacheName='" + cacheName + "' maxEntries=" + maxEntries);
            if (maxEntries <= 0) throw new IllegalStateException("maxEntries must be positive");
        }

        // Library's destroy logic — fires 2nd (after @PreDestroy)
        @Override
        public void destroy() throws Exception {
            log.add("AbstractCacheBean.destroy");
            System.out.println("  [②] AbstractCacheBean.destroy(): evicting all entries from '" + cacheName + "'");
        }
    }

    // ── Your application subclass ─────────────────────────────────────
    static class ProductCache extends AbstractCacheBean {
        private final Map<String, String> store = new LinkedHashMap<>();

        ProductCache(List<String> log) { super(log); }

        // Your @PostConstruct — fires BEFORE library's afterPropertiesSet()
        @PostConstruct
        void postConstruct() {
            log.add("ProductCache.postConstruct");
            System.out.println("  [①] ProductCache.@PostConstruct: validate config cacheName='"
                + cacheName + "' maxEntries=" + maxEntries);
            if (cacheName == null || cacheName.isBlank())
                throw new IllegalStateException("cacheName required");
        }

        // Custom init-method — fires AFTER library's afterPropertiesSet()
        public void warmUp() {
            log.add("ProductCache.warmUp(init-method)");
            System.out.println("  [③] ProductCache.warmUp(): preloading " + cacheName + " with seed data");
            store.put("p:1", "Notebook");
            store.put("p:2", "Pen");
        }

        // Your @PreDestroy — fires BEFORE library's destroy()
        @PreDestroy
        void preDestroy() {
            log.add("ProductCache.preDestroy");
            System.out.println("  [①] ProductCache.@PreDestroy: flush dirty entries from '" + cacheName + "'");
        }

        // Custom destroy-method — fires AFTER library's destroy()
        public void shutdown() {
            log.add("ProductCache.shutdown(destroy-method)");
            System.out.println("  [③] ProductCache.shutdown(): close monitoring handles");
        }

        String get(String key) { return store.get(key); }
        int size() { return store.size(); }
    }

    public static void main(String[] args) throws Exception {
        List<String> log = new ArrayList<>();
        ProductCache cache = new ProductCache(log);
        cache.setCacheName("product-cache");
        cache.setMaxEntries(1000);

        System.out.println("=== INIT (all three mechanisms) ===");
        cache.postConstruct();      // ① @PostConstruct (your code)
        cache.afterPropertiesSet(); // ② InitializingBean (library base)
        cache.warmUp();             // ③ init-method (your code)

        System.out.println("\n=== APP ===");
        System.out.println("[GET p:1] " + cache.get("p:1") + " size=" + cache.size());

        System.out.println("\n=== DESTROY (all three mechanisms) ===");
        cache.preDestroy();  // ① @PreDestroy (your code)
        cache.destroy();     // ② DisposableBean (library base)
        cache.shutdown();    // ③ destroy-method (your code)

        System.out.println("\n[LOG] " + log);
        System.out.println("[ORDER CORRECT] " + log.equals(List.of(
            "ProductCache.postConstruct",
            "AbstractCacheBean.afterPropertiesSet",
            "ProductCache.warmUp(init-method)",
            "ProductCache.preDestroy",
            "AbstractCacheBean.destroy",
            "ProductCache.shutdown(destroy-method)"
        )));
    }
}
```

How to run: `java CombinationOrderDemo2.java`

`ProductCache` extends `AbstractCacheBean` (a library class using `InitializingBean`). Spring fires `@PostConstruct` first (your validation), then the library's `afterPropertiesSet()` (its validation + setup), then your `init-method` `warmUp()` (pre-loading data). Destroy mirrors: your `@PreDestroy` (flush), library's `destroy()` (evict), your `destroy-method` `shutdown()` (close handles).

### Level 3 — Advanced

Edge case: same method name wired to multiple mechanisms — it fires twice. Detect and prevent double-init.

```java
// CombinationOrderDemo3.java — run with: java CombinationOrderDemo3.java
import java.util.*;

public class CombinationOrderDemo3 {

    @interface PostConstruct {}
    interface InitializingBean { void afterPropertiesSet() throws Exception; }

    // ── Accidental double-fire: default-init-method="init" + @PostConstruct on same method ──
    static class ServiceWithDoubleInit implements InitializingBean {
        private String url;
        void setUrl(String v) { this.url = v; }
        private final List<String> callLog = new ArrayList<>();
        private int initCount = 0;

        // This method is BOTH the @PostConstruct AND named "init" (matching default-init-method)
        // Result: Spring calls it TWICE (once via @PostConstruct, once via default-init-method)
        @PostConstruct
        public void init() {
            initCount++;
            callLog.add("init#" + initCount + "(@PostConstruct or init-method)");
            System.out.println("  [init#" + initCount + "] url='" + url + "'");
            if (initCount > 1) System.out.println("  ⚠ DOUBLE INIT — called " + initCount + " times!");
        }

        @Override
        public void afterPropertiesSet() {
            callLog.add("afterPropertiesSet");
            System.out.println("  [afterPropertiesSet] url='" + url + "'");
        }
    }

    // ── Fixed version: idempotent guard ────────────────────────────────
    static class ServiceWithIdempotentInit implements InitializingBean {
        private String url;
        void setUrl(String v) { this.url = v; }
        private final List<String> callLog = new ArrayList<>();
        private volatile boolean initialised = false;

        @PostConstruct
        public void init() {
            if (initialised) { callLog.add("init#SKIP"); System.out.println("  [init] already initialised — skip"); return; }
            initialised = true;
            callLog.add("init#1");
            System.out.println("  [init] first call — url='" + url + "' → initialised");
        }

        @Override
        public void afterPropertiesSet() {
            callLog.add("afterPropertiesSet");
            System.out.println("  [afterPropertiesSet] url='" + url + "'");
        }
    }

    // ── Best practice: use only ONE mechanism ─────────────────────────
    static class ServiceWithSingleInit {
        private String url;
        void setUrl(String v) { this.url = v; }
        private final List<String> callLog = new ArrayList<>();

        @PostConstruct
        public void init() {
            callLog.add("postConstruct");
            System.out.println("  [@PostConstruct] url='" + url + "' — SINGLE mechanism, no double-fire risk");
        }
    }

    // ── container sim: applies both @PostConstruct AND default-init-method="init" ──
    static void initBean(Object bean, String defaultInitMethod) throws Exception {
        // 1. @PostConstruct
        try { var m = bean.getClass().getMethod("init"); m.invoke(bean); }
        catch (NoSuchMethodException ignored) {}
        // 2. InitializingBean
        if (bean instanceof InitializingBean b) b.afterPropertiesSet();
        // 3. default-init-method (if it exists AND is different from @PostConstruct method that already ran)
        if (defaultInitMethod != null) {
            try { var m = bean.getClass().getMethod(defaultInitMethod); m.invoke(bean); }
            catch (NoSuchMethodException ignored) {}
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== CASE 1: Double init (same method wired twice) ===");
        ServiceWithDoubleInit s1 = new ServiceWithDoubleInit();
        s1.setUrl("https://api.example.com");
        initBean(s1, "init");   // "init" is both @PostConstruct AND default-init-method
        System.out.println("[CALL LOG] " + s1.callLog);

        System.out.println("\n=== CASE 2: Fixed with idempotency guard ===");
        ServiceWithIdempotentInit s2 = new ServiceWithIdempotentInit();
        s2.setUrl("https://api.example.com");
        initBean(s2, "init");   // called twice but second call is skipped
        System.out.println("[CALL LOG] " + s2.callLog);

        System.out.println("\n=== CASE 3: Best practice — single mechanism ===");
        ServiceWithSingleInit s3 = new ServiceWithSingleInit();
        s3.setUrl("https://api.example.com");
        initBean(s3, null);     // no default-init-method
        System.out.println("[CALL LOG] " + s3.callLog);
    }
}
```

How to run: `java CombinationOrderDemo3.java`

Case 1 shows the double-fire trap: `init()` is both annotated `@PostConstruct` AND matches `default-init-method="init"` — Spring calls it twice. Case 2 fixes it with an `initialised` flag (idempotency guard). Case 3 is the best practice: use only `@PostConstruct` and no `default-init-method`.

## 6. Walkthrough

**Level 3 Case 1 trace — double-fire:**

```
initBean(s1, "init"):

  Step 1: reflection finds "init" method → invoke (simulating @PostConstruct)
    init#1 called → callLog=[init#1(@PostConstruct or init-method)]
    initCount=1

  Step 2: s1 implements InitializingBean → afterPropertiesSet()
    callLog=[init#1, afterPropertiesSet]

  Step 3: defaultInitMethod="init" → reflection finds "init" again → invoke
    init#2 called → callLog=[init#1, afterPropertiesSet, init#2(@PostConstruct or init-method)]
    initCount=2
    ⚠ DOUBLE INIT — printed warning

Case 2 fix:
  Step 1: init() → initialised=false → set true → callLog=[init#1]
  Step 2: afterPropertiesSet() → callLog=[init#1, afterPropertiesSet]
  Step 3: init() again → initialised=true → callLog=[init#1, afterPropertiesSet, init#SKIP]
  No double-init ✓

Case 3 best practice:
  Step 1: @PostConstruct fired once → callLog=[postConstruct]
  Step 2: not InitializingBean → skipped
  Step 3: defaultInitMethod=null → skipped
  Clean ✓
```

## 7. Gotchas & takeaways

> **A method wired to both `@PostConstruct` AND a matching `default-init-method` (or explicit `init-method`) fires TWICE.** This is a real trap when migrating XML-configured beans to annotation-driven config. Check for the double-wiring and fix by removing one mechanism or adding an idempotency guard.

> **All three mechanisms always fire — no short-circuiting.** An exception from `@PostConstruct` aborts the chain (Spring wraps it in `BeanCreationException` before calling `afterPropertiesSet()`). But if `@PostConstruct` succeeds, `afterPropertiesSet()` always runs next, regardless of what `@PostConstruct` did.

- When migrating from `init-method` to `@PostConstruct`, remove the XML attribute simultaneously — having both fires the method twice unless you add a guard.
- Use `@Bean(initMethod="")` (empty string) in `@Configuration` to explicitly suppress the auto-inferred `close()` / `shutdown()` destroy method detection.
- If you want to guarantee a single entry point for all init logic, implement only one mechanism and have it call the others as private methods. Don't spread init concerns across three mechanisms on the same bean.
- Prefer `@PostConstruct` / `@PreDestroy` for app code (no Spring coupling), `InitializingBean` / `DisposableBean` for framework code, and `init-method` / `destroy-method` for third-party classes you can't annotate.
