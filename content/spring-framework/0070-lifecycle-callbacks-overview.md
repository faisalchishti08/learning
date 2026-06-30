---
card: spring-framework
gi: 70
slug: lifecycle-callbacks-overview
title: Lifecycle callbacks overview
---

## 1. What it is

Spring provides **lifecycle callback hooks** that let you run custom logic at two key moments: immediately after a bean is fully constructed and its dependencies injected (**initialisation**), and just before the bean is destroyed when the container shuts down (**destruction**). Spring offers three parallel mechanisms for each — annotation, interface, and XML attribute — which can even be combined on the same bean.

```java
@Component
public class CacheManager {

    // Annotation (preferred)
    @PostConstruct
    public void init() {
        System.out.println("Cache warming up...");
    }

    // Interface
    // implements InitializingBean → afterPropertiesSet()

    // XML attribute: init-method="warmUp"
    public void warmUp() { ... }

    @PreDestroy
    public void shutdown() {
        System.out.println("Cache flushing on shutdown...");
    }
}
```

The three mechanisms produce the same result — they let you tap into the create and destroy points of a bean's life — but have different trade-offs in coupling and flexibility.

In one sentence: **Lifecycle callbacks are hooks that Spring calls after a bean is fully wired (init) and just before it is destroyed (destroy), available as `@PostConstruct`/`@PreDestroy` annotations, `InitializingBean`/`DisposableBean` interfaces, or XML `init-method`/`destroy-method` attributes.**

## 2. Why & when

Lifecycle callbacks are used to:

- **Open resources** at init — connect to a database, establish a socket, load a file.
- **Validate configuration** at init — fail fast if a required property is missing.
- **Warm a cache** at init — pre-load hot data before the first request arrives.
- **Close resources** at destroy — close connections, flush buffers, stop background threads.
- **De-register from a registry** at destroy — remove from service discovery, close MBean.

Do NOT put constructor logic that depends on injected fields in the constructor body — at construction time, `@Autowired` fields are not yet set. Use `@PostConstruct` for post-injection init.

## 3. Core concept

```
Lifecycle sequence for a singleton bean:

  1. Instantiate        (constructor called)
  2. Inject dependencies (@Autowired / @Value / constructor args)
  3. BeanPostProcessor.postProcessBeforeInitialization()
  4. InitializingBean.afterPropertiesSet()     ← interface
     @PostConstruct                            ← annotation (fired FIRST, before interface)
     init-method="..."                         ← XML (fired LAST)
  5. BeanPostProcessor.postProcessAfterInitialization()
  6. Bean ready — stored in singleton cache
  7. Context closes:
     @PreDestroy                               ← annotation (fired FIRST)
     DisposableBean.destroy()                  ← interface
     destroy-method="..."                      ← XML (fired LAST)

Order when multiple mechanisms combined:
  INIT:  @PostConstruct → afterPropertiesSet() → init-method
  DESTROY: @PreDestroy  → destroy()            → destroy-method
```

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring bean lifecycle: construct, inject, postConstruct, ready, preDestroy, destroy">
  <defs>
    <marker id="a70" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="208" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Bean lifecycle — creation callbacks then destruction callbacks</text>

  <!-- Step boxes -->
  <rect x="10"  y="35" width="90" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="55"  y="57" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">① construct</text>

  <rect x="115" y="35" width="100" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="57" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">② inject deps</text>

  <rect x="230" y="35" width="140" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="50" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">③ @PostConstruct</text>
  <text x="300" y="63" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">→ afterPropertiesSet()</text>

  <rect x="385" y="35" width="100" height="35" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="435" y="57" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">④ READY</text>

  <!-- flow arrows creation -->
  <line x1="100" y1="52" x2="113" y2="52" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a70)"/>
  <line x1="215" y1="52" x2="228" y2="52" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a70)"/>
  <line x1="370" y1="52" x2="383" y2="52" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a70)"/>

  <!-- Separation line -->
  <line x1="15" y1="90" x2="660" y2="90" stroke="#8b949e" stroke-width="0.6" stroke-dasharray="4,3"/>
  <text x="338" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">CONTEXT CLOSE (shutdown signal)</text>

  <!-- Destruction boxes -->
  <rect x="385" y="115" width="100" height="35" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="435" y="137" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">⑤ CLOSING</text>

  <rect x="230" y="115" width="140" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="130" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">⑥ @PreDestroy</text>
  <text x="300" y="143" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">→ destroy() → destroy-method</text>

  <rect x="115" y="115" width="100" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="137" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">⑦ gone</text>

  <!-- Flow arrows destruction (right to left) -->
  <line x1="383" y1="132" x2="372" y2="132" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a70)"/>
  <line x1="228" y1="132" x2="217" y2="132" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a70)"/>

  <!-- Three mechanism labels -->
  <text x="300" y="170" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Init:    @PostConstruct  →  afterPropertiesSet()  →  init-method=</text>
  <text x="300" y="185" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Destroy: @PreDestroy    →  destroy()             →  destroy-method=</text>
  <text x="300" y="200" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">All three may be present; they fire in the order shown above.</text>
</svg>

Init flows left-to-right: construct → inject → `@PostConstruct` → `afterPropertiesSet()` → ready. Destroy flows right-to-left on context close: `@PreDestroy` → `destroy()` → gone.

## 5. Runnable example

Scenario: a `ConnectionPool` bean that must open connections at startup and close them at shutdown. We demonstrate all three lifecycle mechanisms on the same bean.

### Level 1 — Basic

A bean with `@PostConstruct` and `@PreDestroy` equivalents — the simplest lifecycle pattern.

```java
// LifecycleDemo.java — run with: java LifecycleDemo.java

public class LifecycleDemo {

    static class ConnectionPool {
        private final int    maxSize;
        private final String url;
        private boolean      open  = false;
        private int          openConns = 0;

        ConnectionPool(String url, int maxSize) {
            this.url     = url;
            this.maxSize = maxSize;
            System.out.println("  [①CONSTRUCT] ConnectionPool url=" + url
                + " (deps not yet injected if setter-based)");
        }

        // @PostConstruct equivalent — called after all deps injected
        void init() {
            System.out.println("  [③POSTCONSTRUCT] opening pool to " + url
                + " maxSize=" + maxSize);
            open     = true;
            openConns = maxSize;
            System.out.println("  [③POSTCONSTRUCT] pool ready: " + openConns + " connections open");
        }

        String borrow() {
            if (!open)      throw new IllegalStateException("Pool is closed");
            if (openConns <= 0) throw new IllegalStateException("No available connections");
            openConns--;
            return "conn@" + url + "#" + openConns;
        }

        void returnConn(String conn) {
            openConns++;
            System.out.println("  [RETURN] " + conn + " returned, available=" + openConns);
        }

        // @PreDestroy equivalent — called before bean is removed from context
        void destroy() {
            System.out.println("  [⑥PREDESTROY] closing " + openConns + " connections to " + url);
            open     = false;
            openConns = 0;
            System.out.println("  [⑦GONE] pool closed");
        }
    }

    // ── simulated container lifecycle ──────────────────────────────────
    static ConnectionPool startContainer() {
        System.out.println("[CONTAINER] starting up...");
        ConnectionPool pool = new ConnectionPool("jdbc:postgresql://prod:5432/app", 5);
        pool.init();   // @PostConstruct
        System.out.println("[CONTAINER] ready\n");
        return pool;
    }

    static void stopContainer(ConnectionPool pool) {
        System.out.println("[CONTAINER] shutting down...");
        pool.destroy();  // @PreDestroy
        System.out.println("[CONTAINER] stopped");
    }

    public static void main(String[] args) {
        ConnectionPool pool = startContainer();

        String c1 = pool.borrow();
        String c2 = pool.borrow();
        System.out.println("[APP] using " + c1 + " and " + c2);
        pool.returnConn(c1);
        pool.returnConn(c2);

        stopContainer(pool);

        System.out.println("\n=== After shutdown ===");
        try { pool.borrow(); }
        catch (IllegalStateException e) { System.out.println("[EXPECTED] " + e.getMessage()); }
    }
}
```

How to run: `java LifecycleDemo.java`

The constructor runs first (step 1). `init()` (step 3, `@PostConstruct`) runs after construction — it opens the connection pool. `destroy()` (step 6, `@PreDestroy`) runs at shutdown. After `destroy()`, `borrow()` throws `IllegalStateException` — the pool is closed.

### Level 2 — Intermediate

All three init mechanisms on one bean — show they fire in order: `@PostConstruct` first, then `afterPropertiesSet()`, then `init-method`.

```java
// LifecycleDemo2.java — run with: java LifecycleDemo2.java
import java.util.*;

public class LifecycleDemo2 {

    // ── simulated interfaces ───────────────────────────────────────────
    interface InitializingBean { void afterPropertiesSet() throws Exception; }
    interface DisposableBean   { void destroy()            throws Exception; }

    static class HealthMonitor implements InitializingBean, DisposableBean {
        private final String serviceName;
        private final String healthEndpoint;
        private final List<String> lifecycleLog = new ArrayList<>();
        private boolean monitoring = false;

        HealthMonitor(String serviceName, String healthEndpoint) {
            this.serviceName    = serviceName;
            this.healthEndpoint = healthEndpoint;
            lifecycleLog.add("①CONSTRUCT: serviceName=" + serviceName);
            System.out.println("  [①] constructor: serviceName=" + serviceName);
        }

        // Fires FIRST: @PostConstruct equivalent
        void postConstruct() {
            lifecycleLog.add("③POSTCONSTRUCT: validating healthEndpoint");
            System.out.println("  [③] @PostConstruct: validate endpoint=" + healthEndpoint);
            if (healthEndpoint == null || healthEndpoint.isBlank())
                throw new IllegalStateException("healthEndpoint is required");
            System.out.println("  [③] @PostConstruct: endpoint is valid");
        }

        // Fires SECOND: InitializingBean.afterPropertiesSet()
        @Override
        public void afterPropertiesSet() {
            lifecycleLog.add("④AFTERPROPERTIESSET: starting monitoring");
            System.out.println("  [④] afterPropertiesSet(): starting health monitor");
            monitoring = true;
            System.out.println("  [④] monitoring=" + monitoring + " endpoint=" + healthEndpoint);
        }

        // Fires THIRD: init-method equivalent
        void initMethod() {
            lifecycleLog.add("⑤INITMETHOD: registering with service registry");
            System.out.println("  [⑤] init-method: register " + serviceName + " in service registry");
        }

        String check() {
            if (!monitoring) return "NOT_MONITORING";
            return "UP: " + serviceName + " endpoint=" + healthEndpoint;
        }

        // Destroy order: @PreDestroy → DisposableBean.destroy() → destroy-method
        void preDestroy() {
            System.out.println("  [⑥] @PreDestroy: de-register from service registry");
            lifecycleLog.add("⑥PREDESTROY");
        }

        @Override
        public void destroy() {
            System.out.println("  [⑦] DisposableBean.destroy(): stop monitoring");
            monitoring = false;
            lifecycleLog.add("⑦DESTROY");
        }

        void destroyMethod() {
            System.out.println("  [⑧] destroy-method: flush final health status");
            lifecycleLog.add("⑧DESTROYMETHOD");
        }

        void printLog() { System.out.println("  [LIFECYCLE LOG] " + lifecycleLog); }
    }

    // ── simulated container calling all mechanisms in order ───────────
    static HealthMonitor startContainer() throws Exception {
        System.out.println("[CONTAINER] startup:");
        HealthMonitor hm = new HealthMonitor("payment-service", "https://payments.example.com/health");
        // Simulated Spring lifecycle:
        hm.postConstruct();          // @PostConstruct (order 1)
        hm.afterPropertiesSet();     // InitializingBean (order 2)
        hm.initMethod();             // init-method (order 3)
        System.out.println("[CONTAINER] bean ready\n");
        return hm;
    }

    static void stopContainer(HealthMonitor hm) throws Exception {
        System.out.println("[CONTAINER] shutdown:");
        hm.preDestroy();    // @PreDestroy (order 1)
        hm.destroy();       // DisposableBean.destroy() (order 2)
        hm.destroyMethod(); // destroy-method (order 3)
        System.out.println("[CONTAINER] done");
    }

    public static void main(String[] args) throws Exception {
        HealthMonitor hm = startContainer();
        System.out.println("[CHECK] " + hm.check());
        stopContainer(hm);
        hm.printLog();
    }
}
```

How to run: `java LifecycleDemo2.java`

All three init mechanisms fire in order: `@PostConstruct` (validates), `afterPropertiesSet()` (starts monitoring), `initMethod()` (registers). All three destroy mechanisms fire in order: `@PreDestroy` (de-registers), `destroy()` (stops monitoring), `destroyMethod()` (flushes). The `lifecycleLog` shows the exact sequence.

### Level 3 — Advanced

Multiple beans with interdependent lifecycle — destroy order is reverse of init order, and we verify that dependencies are still alive when a bean is being destroyed.

```java
// LifecycleDemo3.java — run with: java LifecycleDemo3.java
import java.util.*;

public class LifecycleDemo3 {

    static final List<String> INIT_ORDER    = new ArrayList<>();
    static final List<String> DESTROY_ORDER = new ArrayList<>();

    static class DatabasePool {
        DatabasePool() { System.out.println("  [CONSTRUCT] DatabasePool"); }
        void init()    { INIT_ORDER.add("DatabasePool"); System.out.println("  [INIT] DatabasePool: connections opened"); }
        boolean isOpen() { return !DESTROY_ORDER.contains("DatabasePool"); }
        void destroy() { DESTROY_ORDER.add("DatabasePool"); System.out.println("  [DESTROY] DatabasePool: connections closed"); }
    }

    static class CacheService {
        private final DatabasePool db;
        CacheService(DatabasePool db) { this.db = db; System.out.println("  [CONSTRUCT] CacheService"); }
        void init()    { INIT_ORDER.add("CacheService"); System.out.println("  [INIT] CacheService: warmed up (db.isOpen=" + db.isOpen() + ")"); }
        void destroy() { DESTROY_ORDER.add("CacheService"); System.out.println("  [DESTROY] CacheService: flushed (db.isOpen=" + db.isOpen() + ")"); }
    }

    static class BusinessService {
        private final CacheService cache;
        private final DatabasePool db;
        BusinessService(CacheService cache, DatabasePool db) {
            this.cache = cache; this.db = db;
            System.out.println("  [CONSTRUCT] BusinessService");
        }
        void init()    { INIT_ORDER.add("BusinessService"); System.out.println("  [INIT] BusinessService: ready (cache+db available)"); }
        void process(String item) { System.out.println("  [PROCESS] " + item + " via db=" + db.isOpen()); }
        void destroy() { DESTROY_ORDER.add("BusinessService"); System.out.println("  [DESTROY] BusinessService: deps still alive? cache=" + !DESTROY_ORDER.contains("CacheService") + " db=" + db.isOpen()); }
    }

    // ── container: creation and destruction in dependency order ────────
    public static void main(String[] args) {
        System.out.println("=== Container startup (creation order = dependency order) ===");
        DatabasePool   db  = new DatabasePool();
        CacheService   cache = new CacheService(db);
        BusinessService svc  = new BusinessService(cache, db);

        // Init in creation order
        db.init();
        cache.init();
        svc.init();

        System.out.println("[INIT ORDER] " + INIT_ORDER);
        System.out.println();

        System.out.println("=== Application running ===");
        svc.process("order-001");
        svc.process("order-002");

        System.out.println();
        System.out.println("=== Container shutdown (REVERSE creation order) ===");
        // Destroy in reverse creation order: svc first, then cache, then db
        svc.destroy();   // svc destroyed FIRST — its deps (cache, db) still alive
        cache.destroy(); // cache destroyed SECOND — db still alive
        db.destroy();    // db destroyed LAST

        System.out.println("[DESTROY ORDER] " + DESTROY_ORDER);
        System.out.println("[KEY] Destroy is reverse of init: " +
            DESTROY_ORDER.equals(List.of("BusinessService", "CacheService", "DatabasePool")));
    }
}
```

How to run: `java LifecycleDemo3.java`

Three beans with a dependency chain: `DatabasePool` ← `CacheService` ← `BusinessService`. Spring initialises in dependency order (DB first, business service last). Destruction is the reverse: `BusinessService` first (so it can still use `CacheService` and `DatabasePool` during its teardown), then `CacheService` (can still use `DatabasePool`), then `DatabasePool` last. The `destroy()` output shows that all dependencies are still alive at each teardown step.

## 6. Walkthrough

**Full lifecycle of `BusinessService` in Level 3:**

```
Container startup:
  ① new DatabasePool()         → [CONSTRUCT] DatabasePool
  ① new CacheService(db)       → [CONSTRUCT] CacheService
  ① new BusinessService(c, db) → [CONSTRUCT] BusinessService

  ③ db.init()          → INIT_ORDER=[DatabasePool]
                          db connections opened
  ③ cache.init()        → INIT_ORDER=[DatabasePool, CacheService]
                          cache warmed (db.isOpen=true)
  ③ svc.init()          → INIT_ORDER=[DatabasePool, CacheService, BusinessService]
                          svc ready

Application:
  svc.process("order-001") → [PROCESS] order-001 via db=true
  svc.process("order-002") → [PROCESS] order-002 via db=true

Container shutdown:
  ⑥ svc.destroy()   → [DESTROY] BusinessService: cache=true db=true (both alive ✓)
                       DESTROY_ORDER=[BusinessService]
  ⑦ cache.destroy() → [DESTROY] CacheService: db=true (db still alive ✓)
                       DESTROY_ORDER=[BusinessService, CacheService]
  ⑧ db.destroy()    → [DESTROY] DatabasePool: connections closed
                       DESTROY_ORDER=[BusinessService, CacheService, DatabasePool]

Reverse confirmed: [BusinessService, CacheService, DatabasePool]
  = reverse of [DatabasePool, CacheService, BusinessService] ✓
```

## 7. Gotchas & takeaways

> **`@PostConstruct` fires BEFORE `InitializingBean.afterPropertiesSet()` which fires BEFORE `init-method`.** If you use all three on the same bean, know the order. Typically choose just one — prefer `@PostConstruct` as it is standard JSR-250 and does not tie your class to Spring interfaces.

> **Lifecycle callbacks are NOT called on prototype beans at destruction.** `@PreDestroy` / `DisposableBean.destroy()` are only invoked on **singleton** beans at context close. Prototype beans are handed off after creation — teardown is the caller's responsibility.

- In a `@Configuration` class, `@Bean` methods support `initMethod` and `destroyMethod` attributes: `@Bean(initMethod="init", destroyMethod="destroy")`.
- If `destroyMethod` is set to `""` (empty string) in a `@Bean` annotation, the auto-inferred close method is disabled — useful for externally-managed resources like `DataSource`.
- Spring auto-detects `close()` or `shutdown()` methods as implicit `destroyMethod` if no explicit method is specified on a `@Bean` — annotate with `@Bean(destroyMethod="")` to suppress this.
- The `SmartLifecycle` interface (extends `Lifecycle`) adds ordered startup/shutdown control across multiple beans — use it for infrastructure beans that need to start and stop in a specific order relative to each other.
