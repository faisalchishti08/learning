---
card: spring-framework
gi: 75
slug: init-method-destroy-method-attributes
title: init-method / destroy-method attributes
---

## 1. What it is

The `init-method` and `destroy-method` attributes are **XML and annotation-level hooks** that tell Spring which methods to call at bean initialisation and destruction without requiring the bean class to implement any interface or carry any annotation. They are the **third and final** mechanism in each lifecycle chain — firing after `@PostConstruct`/`@PreDestroy` and after `InitializingBean`/`DisposableBean`.

```xml
<!-- XML configuration -->
<bean id="dbPool" class="com.example.HikariConnectionPool"
      init-method="open"
      destroy-method="close"/>
```

```java
// Annotation configuration (@Bean)
@Bean(initMethod = "open", destroyMethod = "close")
public HikariConnectionPool dbPool() {
    HikariConnectionPool p = new HikariConnectionPool();
    p.setJdbcUrl("jdbc:postgresql://host/db");
    return p;
}
```

```java
// The bean class — no Spring imports at all
public class HikariConnectionPool {
    public void open()  { /* open connections */ }
    public void close() { /* close connections */ }
}
```

In one sentence: **`init-method` / `destroy-method` attributes wire lifecycle callbacks to existing method names without touching the bean class — ideal for third-party classes you can't annotate, firing last in the init/destroy chain.**

## 2. Why & when

Use `init-method` / `destroy-method` when:

- **The class is third-party** — you can't add `@PostConstruct` / `@PreDestroy` to a library class.
- **You want zero Spring coupling in your bean class** — the bean has `open()`/`close()` methods for its own reasons; you just point Spring at them.
- **You use XML configuration** — XML beans always configure lifecycle via attributes, not annotations.
- **You use `@Bean` factory methods** — the `@Bean(initMethod="...", destroyMethod="...")` form is the natural fit in `@Configuration` classes.

Prefer `@PostConstruct` / `@PreDestroy` for your own classes in annotation-driven apps. Use `init-method` / `destroy-method` for library integrations or legacy XML config.

## 3. Core concept

```
Full init order (all three present on same bean):
  ① @PostConstruct                          fires first
  ② InitializingBean.afterPropertiesSet()   fires second
  ③ init-method="open"                      fires LAST ← you are here

Full destroy order:
  ① @PreDestroy                             fires first
  ② DisposableBean.destroy()                fires second
  ③ destroy-method="close"                  fires LAST ← you are here

XML syntax:
  <bean id="..." class="..." init-method="methodName" destroy-method="methodName"/>

@Bean annotation syntax:
  @Bean(initMethod = "methodName", destroyMethod = "methodName")

Global defaults in XML:
  <beans default-init-method="init" default-destroy-method="destroy">
    <!-- every bean gets these defaults unless it sets its own -->
  </beans>

Auto-detected destroyMethod (Spring-only behaviour for @Bean):
  If destroyMethod is NOT set on @Bean, Spring auto-detects close() or shutdown()
  as an implicit destroy method. Suppress with @Bean(destroyMethod = "").

destroyMethod="" :
  Disables auto-detection and explicit destroy — use for externally-managed
  resources (e.g., a DataSource from a pool library that manages its own lifecycle).
```

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="init-method / destroy-method position in lifecycle chain, XML vs annotation syntax">
  <defs>
    <marker id="a75" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b75" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="198" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">init-method / destroy-method — always fires last in the three-step chain</text>

  <!-- INIT row -->
  <text x="10" y="42" fill="#8b949e" font-size="8" font-family="sans-serif">INIT:</text>
  <rect x="45"  y="30" width="120" height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="105" y="48" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">① @PostConstruct</text>
  <line x1="165" y1="44" x2="175" y2="44" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a75)"/>
  <rect x="178" y="30" width="160" height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="258" y="48" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">② afterPropertiesSet()</text>
  <line x1="338" y1="44" x2="348" y2="44" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a75)"/>
  <rect x="351" y="30" width="155" height="28" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.8"/>
  <text x="428" y="44" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">③ init-method="open"</text>
  <text x="428" y="54" fill="#6db33f" font-size="6.5" text-anchor="middle" font-family="sans-serif">← LAST, no coupling to Spring</text>

  <!-- DESTROY row -->
  <text x="10" y="82" fill="#8b949e" font-size="8" font-family="sans-serif">DEST:</text>
  <rect x="45"  y="70" width="120" height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="105" y="88" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">① @PreDestroy</text>
  <line x1="165" y1="84" x2="175" y2="84" stroke="#8b949e" stroke-width="1.2" marker-end="url(#b75)"/>
  <rect x="178" y="70" width="160" height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="258" y="88" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">② DisposableBean.destroy()</text>
  <line x1="338" y1="84" x2="348" y2="84" stroke="#8b949e" stroke-width="1.2" marker-end="url(#b75)"/>
  <rect x="351" y="70" width="155" height="28" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.8"/>
  <text x="428" y="84" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">③ destroy-method="close"</text>
  <text x="428" y="94" fill="#6db33f" font-size="6.5" text-anchor="middle" font-family="sans-serif">← LAST, auto-detects close()/shutdown()</text>

  <!-- Config syntax comparison -->
  <rect x="10" y="112" width="655" height="83" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.8"/>
  <text x="22" y="130" fill="#8b949e" font-size="9" font-family="monospace">Two ways to configure:</text>
  <line x1="12" y1="134" x2="662" y2="134" stroke="#8b949e" stroke-width="0.5"/>
  <text x="22" y="149" fill="#79c0ff" font-size="9" font-family="monospace">XML:   &lt;bean class="Pool" init-method="open" destroy-method="close"/&gt;</text>
  <text x="22" y="164" fill="#6db33f" font-size="9" font-family="monospace">@Bean: @Bean(initMethod="open", destroyMethod="close")</text>
  <text x="22" y="179" fill="#8b949e" font-size="9" font-family="monospace">@Bean: @Bean(destroyMethod="")   ← suppress auto-detect of close()/shutdown()</text>
  <text x="22" y="187" fill="#8b949e" font-size="8" font-family="sans-serif">   </text>
</svg>

`init-method` and `destroy-method` always fire last. They require no change to the bean class.

## 5. Runnable example

Scenario: a `FileStore` third-party class (imagine you can't modify it) with `open()` and `close()` methods — Spring is configured to call them as lifecycle hooks.

### Level 1 — Basic

Minimal simulation: Spring calls `open()` at init and `close()` at destroy, without the class knowing it.

```java
// InitDestroyMethodDemo.java — run with: java InitDestroyMethodDemo.java
import java.util.*;

public class InitDestroyMethodDemo {

    // ── "third-party" class — no Spring annotations, no interfaces ────
    static class FileStore {
        private final String directory;
        private boolean open = false;
        private final List<String> files = new ArrayList<>();

        FileStore(String directory) {
            this.directory = directory;
            System.out.println("  [CONSTRUCT] FileStore dir=" + directory);
        }

        // Spring calls this as init-method (or @Bean(initMethod="open"))
        public void open() {
            System.out.println("  [init-method open()] FileStore '" + directory + "' opening...");
            // validate directory exists, open file handles, etc.
            open = true;
            System.out.println("  [init-method open()] ready");
        }

        // Spring calls this as destroy-method (or @Bean(destroyMethod="close"))
        public void close() {
            System.out.println("  [destroy-method close()] FileStore '" + directory + "' closing ("
                + files.size() + " files)");
            open = false;
            files.clear();
            System.out.println("  [destroy-method close()] done");
        }

        public void store(String filename, String content) {
            if (!open) throw new IllegalStateException("FileStore is not open");
            files.add(filename);
            System.out.println("  [STORE] " + filename + " → " + directory);
        }

        public int count() { return files.size(); }
    }

    // ── simulated Spring container ────────────────────────────────────
    static FileStore createBean(String dir) {
        FileStore fs = new FileStore(dir);   // ① construct
        // ② inject (setter-based if needed — none here)
        fs.open();                           // ③ init-method fires LAST (after @PostConstruct / afterPropertiesSet)
        return fs;
    }

    static void destroyBean(FileStore fs) {
        fs.close();                          // ① destroy-method fires LAST
    }

    public static void main(String[] args) {
        System.out.println("=== Container starting ===");
        FileStore store = createBean("/var/data/uploads");

        System.out.println("\n=== Application running ===");
        store.store("report.pdf",  "PDF content");
        store.store("invoice.xml", "XML content");
        store.store("photo.jpg",   "JPEG bytes");
        System.out.println("[STORED] " + store.count() + " files");

        System.out.println("\n=== Context closing ===");
        destroyBean(store);

        System.out.println("\n=== After destroy ===");
        try { store.store("too.late", "data"); }
        catch (IllegalStateException e) { System.out.println("[EXPECTED] " + e.getMessage()); }
    }
}
```

How to run: `java InitDestroyMethodDemo.java`

`FileStore` has no Spring imports at all. Spring calls `open()` at init and `close()` at destroy purely via the attribute configuration. The class could be any third-party library with existing lifecycle methods.

### Level 2 — Intermediate

Global `default-init-method` / `default-destroy-method` applied to all beans in a context — and `@Bean(destroyMethod="")` to suppress auto-detection for an externally-managed resource.

```java
// InitDestroyMethodDemo2.java — run with: java InitDestroyMethodDemo2.java
import java.util.*;

public class InitDestroyMethodDemo2 {

    // ── Multiple "third-party" beans with init/destroy ─────────────────
    static class CacheStore {
        private final String name;
        private final Map<String, String> data = new LinkedHashMap<>();
        private boolean ready = false;

        CacheStore(String name) { this.name = name; System.out.println("  [CONSTRUCT] CacheStore " + name); }

        // default-init-method target: named "init" per convention
        public void init() {
            System.out.println("  [init-method CacheStore.init()] loading " + name);
            data.put("k:warmup", "cached-value");
            ready = true;
        }

        // default-destroy-method target: named "destroy" per convention
        public void destroy() {
            System.out.println("  [destroy-method CacheStore.destroy()] evicting " + name
                + " entries=" + data.size());
            data.clear();
            ready = false;
        }

        String get(String key) { return ready ? data.get(key) : null; }
        void put(String key, String val) { if (ready) data.put(key, val); }
        int size() { return data.size(); }
    }

    static class SessionStore {
        private final String storeName;
        private final Map<String, Object> sessions = new LinkedHashMap<>();
        private boolean ready = false;

        SessionStore(String storeName) { this.storeName = storeName; System.out.println("  [CONSTRUCT] SessionStore " + storeName); }

        // Also named init/destroy — picked up by default-init-method
        public void init() {
            System.out.println("  [init-method SessionStore.init()] initialising " + storeName);
            ready = true;
        }
        public void destroy() {
            System.out.println("  [destroy-method SessionStore.destroy()] invalidating "
                + sessions.size() + " sessions in " + storeName);
            sessions.clear();
            ready = false;
        }

        void put(String id, Object session) { if (ready) sessions.put(id, session); }
        int count() { return sessions.size(); }
    }

    // ── Externally-managed resource — NO destroy-method ───────────────
    static class ExternalDataSource {
        private final String url;

        ExternalDataSource(String url) {
            this.url = url;
            System.out.println("  [CONSTRUCT] ExternalDataSource url=" + url);
        }

        // Has a close() method, but managed by the pool library externally
        public void close() {
            System.out.println("  [ExternalDataSource.close()] called — should NOT be called by Spring");
            throw new IllegalStateException("close() must not be called by Spring — externally managed");
        }

        String url() { return url; }
    }

    // ── Simulated container ───────────────────────────────────────────
    static <T> T initBean(T bean, Runnable initFn) {
        initFn.run();
        return bean;
    }

    public static void main(String[] args) {
        System.out.println("=== Container startup ===");
        System.out.println("(global default-init-method=init, default-destroy-method=destroy)");

        // Beans that pick up the global default
        CacheStore   cache   = new CacheStore("product-cache");
        SessionStore sessions = new SessionStore("user-sessions");
        cache.init();      // called by Spring via default-init-method="init"
        sessions.init();   // called by Spring via default-init-method="init"

        // ExternalDataSource: @Bean(destroyMethod="") suppresses auto-detect of close()
        ExternalDataSource ds = new ExternalDataSource("jdbc:postgresql://prod:5432/app");
        // Spring does NOT call ds.close() because destroyMethod="" suppresses it

        System.out.println("\n=== Application running ===");
        cache.put("product:1",    "Notebook");
        cache.put("product:2",    "Pen");
        sessions.put("sess:abc",  Map.of("user", "alice"));
        sessions.put("sess:def",  Map.of("user", "bob"));
        System.out.println("[CACHE] size=" + cache.size() + " get product:1=" + cache.get("product:1"));
        System.out.println("[SESSIONS] count=" + sessions.count());
        System.out.println("[DS] url=" + ds.url());

        System.out.println("\n=== Context closing ===");
        // Beans destroyed in reverse init order
        sessions.destroy(); // default-destroy-method="destroy"
        cache.destroy();    // default-destroy-method="destroy"
        // ExternalDataSource.close() NOT called — destroyMethod="" in @Bean suppresses it
        System.out.println("[ExternalDataSource] close() suppressed — managed externally ✓");
    }
}
```

How to run: `java InitDestroyMethodDemo2.java`

`CacheStore` and `SessionStore` both have `init()` and `destroy()` methods. A global `default-init-method="init"` and `default-destroy-method="destroy"` in XML would wire them automatically. `ExternalDataSource` has a `close()` method that Spring would otherwise auto-detect — `@Bean(destroyMethod="")` suppresses that auto-detection.

### Level 3 — Advanced

All three init mechanisms on the same bean — demonstrate exact ordering: `@PostConstruct` first, `afterPropertiesSet()` second, `init-method` last; and same for destroy.

```java
// InitDestroyMethodDemo3.java — run with: java InitDestroyMethodDemo3.java
import java.util.*;

public class InitDestroyMethodDemo3 {

    @interface PostConstruct {}
    @interface PreDestroy    {}
    interface InitializingBean { void afterPropertiesSet() throws Exception; }
    interface DisposableBean   { void destroy()            throws Exception; }

    static class OrderService implements InitializingBean, DisposableBean {
        private String serviceName;
        private int    workerCount;
        private final List<String> initLog    = new ArrayList<>();
        private final List<String> destroyLog = new ArrayList<>();
        private boolean ready = false;

        void setServiceName(String v) { this.serviceName = v; }
        void setWorkerCount(int v)    { this.workerCount  = v; }

        // ── INIT chain ─────────────────────────────────────────────────
        // Fires 1st: @PostConstruct
        @PostConstruct
        void postConstruct() {
            System.out.println("[1st] @PostConstruct: validate serviceName='" + serviceName + "'");
            if (serviceName == null || serviceName.isBlank())
                throw new IllegalStateException("serviceName required");
            initLog.add("@PostConstruct");
        }

        // Fires 2nd: InitializingBean
        @Override
        public void afterPropertiesSet() throws Exception {
            System.out.println("[2nd] afterPropertiesSet(): validate workerCount=" + workerCount);
            if (workerCount < 1 || workerCount > 32)
                throw new IllegalStateException("workerCount must be 1-32: " + workerCount);
            initLog.add("afterPropertiesSet");
        }

        // Fires 3rd: init-method (named "open" in @Bean / XML attribute)
        public void open() {
            System.out.println("[3rd] init-method open(): start " + workerCount
                + " workers for service '" + serviceName + "'");
            ready = true;
            initLog.add("init-method:open");
            System.out.println("[3rd] init-method open(): service READY");
        }

        // ── application method ─────────────────────────────────────────
        String processOrder(String orderId) {
            if (!ready) throw new IllegalStateException(serviceName + " not ready");
            return "processed:" + orderId + " by " + serviceName;
        }

        // ── DESTROY chain ──────────────────────────────────────────────
        // Fires 1st: @PreDestroy
        @PreDestroy
        void preDestroy() {
            System.out.println("[1st] @PreDestroy: stop accepting orders");
            ready = false;
            destroyLog.add("@PreDestroy");
        }

        // Fires 2nd: DisposableBean
        @Override
        public void destroy() throws Exception {
            System.out.println("[2nd] DisposableBean.destroy(): drain in-flight requests");
            destroyLog.add("DisposableBean.destroy");
        }

        // Fires 3rd: destroy-method (named "close" in @Bean / XML attribute)
        public void close() {
            System.out.println("[3rd] destroy-method close(): shutdown " + workerCount + " workers");
            destroyLog.add("destroy-method:close");
        }

        void printLogs() {
            System.out.println("[INIT LOG]    " + initLog);
            System.out.println("[DESTROY LOG] " + destroyLog);
        }
    }

    // ── simulated Spring container ────────────────────────────────────
    static OrderService createBean() throws Exception {
        OrderService svc = new OrderService();
        // inject
        svc.setServiceName("order-service");
        svc.setWorkerCount(8);
        // init chain — Spring fires in this order:
        svc.postConstruct();        // ① @PostConstruct
        svc.afterPropertiesSet();   // ② InitializingBean
        svc.open();                 // ③ init-method="open"
        return svc;
    }

    static void destroyBean(OrderService svc) throws Exception {
        // destroy chain — Spring fires in this order:
        svc.preDestroy();  // ① @PreDestroy
        svc.destroy();     // ② DisposableBean.destroy()
        svc.close();       // ③ destroy-method="close"
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Container startup — all three init mechanisms ===");
        OrderService svc = createBean();

        System.out.println("\n=== Application running ===");
        System.out.println(svc.processOrder("ORD-001"));
        System.out.println(svc.processOrder("ORD-002"));

        System.out.println("\n=== Context closing — all three destroy mechanisms ===");
        destroyBean(svc);

        svc.printLogs();

        System.out.println("\n[AFTER DESTROY]");
        try { svc.processOrder("ORD-003"); }
        catch (IllegalStateException e) { System.out.println("[EXPECTED] " + e.getMessage()); }
    }
}
```

How to run: `java InitDestroyMethodDemo3.java`

Three init mechanisms fire in order: `@PostConstruct` (name validation), `afterPropertiesSet()` (worker count validation), `open()` / `init-method` (start workers, mark ready). Three destroy mechanisms fire in order: `@PreDestroy` (stop accepting), `destroy()` (drain in-flight), `close()` / `destroy-method` (shut down workers). The `initLog` and `destroyLog` prove the exact ordering.

## 6. Walkthrough

**Level 3 full lifecycle trace:**

```
Container startup:
  new OrderService()                          ← ① constructor
  svc.setServiceName("order-service")         ← ② inject
  svc.setWorkerCount(8)                       ← ② inject

  svc.postConstruct()                         ← ③ @PostConstruct (fires FIRST)
    validate serviceName → OK
    initLog = ["@PostConstruct"]

  svc.afterPropertiesSet()                    ← ④ InitializingBean (fires SECOND)
    validate workerCount 8 in [1,32] → OK
    initLog = ["@PostConstruct", "afterPropertiesSet"]

  svc.open()                                  ← ⑤ init-method (fires LAST)
    ready = true
    initLog = ["@PostConstruct","afterPropertiesSet","init-method:open"]

Application:
  svc.processOrder("ORD-001") → "processed:ORD-001 by order-service"
  svc.processOrder("ORD-002") → "processed:ORD-002 by order-service"

Context close:
  svc.preDestroy()                            ← ⑥ @PreDestroy (fires FIRST)
    ready = false   ← no new orders
    destroyLog = ["@PreDestroy"]

  svc.destroy()                               ← ⑦ DisposableBean.destroy() (fires SECOND)
    drain in-flight
    destroyLog = ["@PreDestroy","DisposableBean.destroy"]

  svc.close()                                 ← ⑧ destroy-method (fires LAST)
    shutdown 8 workers
    destroyLog = ["@PreDestroy","DisposableBean.destroy","destroy-method:close"]

svc.processOrder("ORD-003")                   ← IllegalStateException: not ready ✓
```

## 7. Gotchas & takeaways

> **`@Bean` on methods auto-detects `close()` or `shutdown()` as destroy methods** even if you don't set `destroyMethod`. For third-party beans (connection pools, HTTP clients) that manage their own lifecycle, suppress this with `@Bean(destroyMethod = "")` — otherwise Spring will call `close()` at context shutdown and you'll get a double-close or resource exception.

> **If all three mechanisms are present on the same bean, they stack — they don't replace each other.** `@PostConstruct` does NOT prevent `afterPropertiesSet()` from running. If you want only one mechanism, use only one.

- XML global defaults: `<beans default-init-method="init" default-destroy-method="destroy">` applies to every `<bean>` in that file that doesn't override it — useful for legacy XML configs where all beans follow a naming convention.
- The method pointed to by `init-method` / `destroy-method` **must be public and take no arguments** — Spring will throw `BeanDefinitionValidationException` at startup if the method is not found.
- `destroy-method` is NOT called on prototype beans — same rule as `@PreDestroy` and `DisposableBean`.
- Exception thrown from `init-method` aborts context startup (wrapped in `BeanCreationException`). Exception thrown from `destroy-method` is logged as a warning and shutdown continues.
- When using Kotlin or Groovy DSL-based Spring configs, lifecycle methods are expressed via `init` and `destroyMethod` properties on the bean definition builder — same semantics, different syntax.
- For Spring Boot: `@Bean(initMethod="...", destroyMethod="...")` is the idiomatic form. XML configuration is rarely used in Spring Boot apps but still fully supported.
