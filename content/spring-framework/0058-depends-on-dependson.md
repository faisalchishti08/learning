---
card: spring-framework
gi: 58
slug: depends-on-dependson
title: depends-on / @DependsOn
---

## 1. What it is

`depends-on` (XML) and `@DependsOn` (annotation) tell Spring that one bean must be **fully initialised before** another, even when there is no direct injection relationship between them. This creates an invisible ordering constraint — useful for side-effect dependencies like database migrations, connection pool warm-up, or JVM-level static initialisers that must run before a bean is usable.

```java
// Annotation: ensure liquibase runs before dataSource is used
@Component
@DependsOn("liquibaseMigration")
public class UserRepository {
    // No field or constructor reference to LiquibaseMigration,
    // but the DB schema must be set up before this bean executes queries.
}

// XML equivalent
// <bean id="userRepository" class="UserRepository" depends-on="liquibaseMigration"/>
```

Multiple dependencies are supported:

```java
@DependsOn({"cacheWarmup", "liquibaseMigration"})
public class OrderService { ... }
```

In one sentence: **`depends-on` / `@DependsOn` enforces bean creation order when one bean relies on a side-effect produced by another (like schema migration or cache warm-up) but does not hold a direct reference to it.**

## 2. Why & when

Use `depends-on` when:

- A **database migration** (`Flyway`, `Liquibase`) must complete before any repository bean opens a connection.
- A **cache warm-up** bean populates shared state (e.g. a static `Map`) before other beans read from it.
- An **external service registration** (e.g. registering to a service registry) must happen before consumers try to call it.
- A **JVM-level system property** or static initialiser set by bean A must exist before bean B's constructor runs.
- Tear-down order must also be controlled: the dependent bean is destroyed **before** the dependency (reverse of creation order).

Do not use `depends-on` as a substitute for proper dependency injection. If bean A actually uses bean B, inject B into A with `@Autowired`/`ref` — that already implies the ordering. Reserve `depends-on` for invisible/side-effect relationships only.

## 3. Core concept

```
Normal singleton creation order:
  Spring scans, builds dependency graph from @Autowired / ref.
  Creates beans in dependency order (topological sort).

depends-on adds an EXPLICIT edge to the graph:
  @DependsOn("B")  on  A
  → equivalent to: "B must be created before A"
  → Spring adds an ordering constraint: B → A in creation order
  → B is also destroyed AFTER A (reverse order)

Without depends-on:
  A ──(no ref)──> B
  B may or may not be created before A (undefined if no other ordering)

With @DependsOn("B"):
  A ──[depends-on]──> B
  B is guaranteed to be fully initialised (including @PostConstruct) before A

Circular depends-on:
  A depends-on B, B depends-on A → BeanCreationException at startup
```

## 4. Diagram

<svg viewBox="0 0 640 205" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@DependsOn ordering: LiquibaseMigration created and completed before UserRepository is initialised">
  <defs>
    <marker id="a58" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b58" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <rect x="5" y="5" width="630" height="190" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>

  <!-- Timeline bar -->
  <text x="320" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Bean creation timeline with @DependsOn</text>
  <line x1="20" y1="50" x2="620" y2="50" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>
  <text x="20" y="45" fill="#8b949e" font-size="8" font-family="sans-serif">time →</text>

  <!-- LiquibaseMigration -->
  <rect x="20" y="60" width="200" height="55" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="78" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">LiquibaseMigration</text>
  <text x="120" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">instantiate → migrate() → @PostConstruct</text>
  <text x="120" y="107" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">✓ fully initialised</text>

  <!-- depends-on arrow -->
  <line x1="220" y1="87" x2="350" y2="87" stroke="#6db33f" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#a58)"/>
  <text x="285" y="80" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">@DependsOn</text>
  <text x="285" y="100" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">gate</text>

  <!-- UserRepository -->
  <rect x="352" y="60" width="200" height="55" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="452" y="78" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">UserRepository</text>
  <text x="452" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">instantiate → DataSource inject → @PostConstruct</text>
  <text x="452" y="107" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">✓ schema ready — safe to query</text>

  <!-- Destroy order (reverse) -->
  <line x1="452" y1="125" x2="452" y2="155" stroke="#8b949e" stroke-width="1" marker-end="url(#b58)"/>
  <line x1="120" y1="125" x2="120" y2="155" stroke="#8b949e" stroke-width="1" marker-end="url(#b58)"/>
  <rect x="352" y="155" width="200" height="25" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="452" y="171" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">UserRepository destroyed first</text>
  <rect x="20" y="155" width="200" height="25" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="120" y="171" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">then LiquibaseMigration destroyed</text>
  <text x="320" y="194" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Destroy order is the reverse of creation order — mirrors creation guarantee.</text>
</svg>

`LiquibaseMigration` (including its `@PostConstruct` method) completes before `UserRepository` starts. On shutdown, `UserRepository` is destroyed first, then `LiquibaseMigration`.

## 5. Runnable example

Scenario: a `CacheRegistry` populates a shared static lookup table during its own init. A `ProductService` reads from that table. Without ordering control, `ProductService` might initialise first and see an empty cache.

### Level 1 — Basic

Force `CacheWarmup` to run before `ProductService` with an explicit ordering constraint.

```java
// DependsOnDemo.java — run with: java DependsOnDemo.java
import java.util.*;

public class DependsOnDemo {

    // ── shared cache (side-effect target) ─────────────────────────────
    static final Map<String, String> PRODUCT_CACHE = new LinkedHashMap<>();

    static class CacheWarmup {
        CacheWarmup() {
            System.out.println("[BEAN] CacheWarmup: starting warm-up...");
            PRODUCT_CACHE.put("SKU-001", "Laptop Pro 15");
            PRODUCT_CACHE.put("SKU-002", "Wireless Mouse");
            PRODUCT_CACHE.put("SKU-003", "USB-C Hub");
            System.out.println("[BEAN] CacheWarmup: loaded " + PRODUCT_CACHE.size() + " products");
        }

        void destroy() {
            System.out.println("[BEAN] CacheWarmup: destroyed (cleared cache)");
            PRODUCT_CACHE.clear();
        }
    }

    // ── @DependsOn("cacheWarmup") — CacheWarmup must init first ───────
    static class ProductService {
        ProductService() {
            System.out.println("[BEAN] ProductService: init, cache size=" + PRODUCT_CACHE.size());
            if (PRODUCT_CACHE.isEmpty())
                throw new IllegalStateException("Cache is empty — CacheWarmup must run first!");
        }

        String findName(String sku) {
            String name = PRODUCT_CACHE.get(sku);
            return name != null ? name : "UNKNOWN";
        }

        void destroy() {
            System.out.println("[BEAN] ProductService: destroyed");
        }
    }

    // ── container: enforce ordering ────────────────────────────────────
    static void run(boolean correctOrder) {
        System.out.println("=== " + (correctOrder ? "Correct order (@DependsOn)" : "Wrong order (no ordering)") + " ===");
        CacheWarmup   warmup;
        ProductService svc;

        if (correctOrder) {
            warmup = new CacheWarmup();    // created first
            svc    = new ProductService(); // then this
        } else {
            // ProductService first — cache is empty → throws
            try {
                svc    = new ProductService(); // WRONG: cache empty!
                warmup = new CacheWarmup();
            } catch (IllegalStateException e) {
                System.out.println("[ERROR] " + e.getMessage());
                return;
            }
        }

        System.out.println("[RESULT] SKU-001: " + svc.findName("SKU-001"));
        System.out.println("[RESULT] SKU-999: " + svc.findName("SKU-999"));
        svc.destroy();
        warmup.destroy();
    }

    public static void main(String[] args) {
        run(true);
        System.out.println();
        PRODUCT_CACHE.clear();
        run(false);
    }
}
```

How to run: `java DependsOnDemo.java`

`CacheWarmup` populates `PRODUCT_CACHE` during construction. `ProductService` reads from it. Without ordering (`run(false)`), `ProductService` is created first and sees an empty cache, throwing `IllegalStateException`. With ordering (`run(true)`) — equivalent to `@DependsOn("cacheWarmup")` — the warmup runs first and the service sees 3 entries.

### Level 2 — Intermediate

Multi-dependency ordering: `UserService` depends on both `DatabaseMigration` AND `ConfigLoader` completing before it starts.

```java
// DependsOnDemo2.java — run with: java DependsOnDemo2.java
import java.util.*;

public class DependsOnDemo2 {

    static final List<String> INIT_LOG = new ArrayList<>();  // tracks creation order

    static class DatabaseMigration {
        DatabaseMigration() {
            System.out.println("[BEAN] DatabaseMigration: running V1..V5 migrations");
            INIT_LOG.add("DatabaseMigration");
            System.out.println("[BEAN] DatabaseMigration: schema ready (5 tables created)");
        }
    }

    static class ConfigLoader {
        final Map<String, String> config = new LinkedHashMap<>();
        ConfigLoader() {
            System.out.println("[BEAN] ConfigLoader: loading config from classpath");
            INIT_LOG.add("ConfigLoader");
            config.put("feature.newDashboard", "true");
            config.put("maxLoginAttempts",     "5");
            config.put("sessionTimeoutMin",    "30");
            System.out.println("[BEAN] ConfigLoader: loaded " + config.size() + " keys");
        }
        String get(String key) { return config.getOrDefault(key, ""); }
    }

    // ── @DependsOn({"databaseMigration", "configLoader"}) ─────────────
    static class UserService {
        final int    maxLoginAttempts;
        final int    sessionTimeoutMin;
        final boolean newDashboard;

        UserService(ConfigLoader config) {
            if (!INIT_LOG.contains("DatabaseMigration"))
                throw new IllegalStateException("DB not migrated!");
            if (!INIT_LOG.contains("ConfigLoader"))
                throw new IllegalStateException("Config not loaded!");

            // ConfigLoader is injected (normal ref dependency)
            // DatabaseMigration is a depends-on (no ref, pure ordering)
            this.maxLoginAttempts = Integer.parseInt(config.get("maxLoginAttempts"));
            this.sessionTimeoutMin = Integer.parseInt(config.get("sessionTimeoutMin"));
            this.newDashboard      = Boolean.parseBoolean(config.get("feature.newDashboard"));
            INIT_LOG.add("UserService");
            System.out.println("[BEAN] UserService: ready maxLogin=" + maxLoginAttempts
                + " sessionTimeout=" + sessionTimeoutMin + "m newDashboard=" + newDashboard);
        }

        boolean authenticate(String user, String pwd) {
            System.out.println("  [AUTH] user=" + user + " maxAttempts=" + maxLoginAttempts);
            return !pwd.isBlank();
        }
    }

    public static void main(String[] args) {
        // ── correct order: migration → config → service ────────────────
        System.out.println("=== Container startup ===");
        DatabaseMigration migration = new DatabaseMigration();  // @DependsOn edge
        ConfigLoader      config    = new ConfigLoader();        // injected + @DependsOn
        UserService       svc       = new UserService(config);  // created last

        System.out.println("\n[INIT ORDER] " + INIT_LOG);

        System.out.println("\n=== Service calls ===");
        System.out.println("  auth alice: " + svc.authenticate("alice", "s3cr3t"));
        System.out.println("  auth bob:   " + svc.authenticate("bob",   ""));
    }
}
```

How to run: `java DependsOnDemo2.java`

`UserService` has TWO ordering constraints: `DatabaseMigration` (no injection reference, pure `@DependsOn`) and `ConfigLoader` (injected via constructor, which implies ordering automatically). `INIT_LOG` records creation order and proves `DatabaseMigration` and `ConfigLoader` are both complete before `UserService` constructs.

### Level 3 — Advanced

Chain of ordering constraints with destroy-order verification, and a circular dependency detection demo.

```java
// DependsOnDemo3.java — run with: java DependsOnDemo3.java
import java.util.*;

public class DependsOnDemo3 {

    static final Deque<String> DESTROY_LOG = new ArrayDeque<>();

    static abstract class ManagedBean {
        final String name;
        ManagedBean(String name) {
            this.name = name;
            System.out.println("[BEAN] " + name + ": created");
        }
        void destroy() {
            DESTROY_LOG.push(name);
            System.out.println("[DESTROY] " + name);
        }
    }

    // ── creation chain: JvmProperties → DbMigration → CacheWarmup → ApiService ──
    static class JvmProperties extends ManagedBean {
        final Map<String, String> props = new LinkedHashMap<>();
        JvmProperties() {
            super("JvmProperties");
            props.put("db.maxPoolSize", "20");
            props.put("cache.ttlSec",   "300");
            System.out.println("  [INIT] system properties set: " + props.keySet());
        }
        String get(String k) { return props.getOrDefault(k, ""); }
    }

    // depends-on: JvmProperties
    static class DbMigration extends ManagedBean {
        final int maxPoolSize;
        DbMigration(JvmProperties jvmProps) {  // injected ref → implied ordering
            super("DbMigration");
            this.maxPoolSize = Integer.parseInt(jvmProps.get("db.maxPoolSize"));
            System.out.println("  [INIT] ran 3 migrations, pool=" + maxPoolSize);
        }
    }

    // depends-on: DbMigration (no ref — side-effect ordering only)
    static class CacheWarmup extends ManagedBean {
        final long ttlSec;
        CacheWarmup(JvmProperties jvmProps) {
            super("CacheWarmup");
            this.ttlSec = Long.parseLong(jvmProps.get("cache.ttlSec"));
            System.out.println("  [INIT] warmed 500 entries, ttl=" + ttlSec + "s");
        }
    }

    // depends-on: DbMigration, CacheWarmup
    static class ApiService extends ManagedBean {
        ApiService(DbMigration dbMig, CacheWarmup cache) {  // both injected
            super("ApiService");
            System.out.println("  [INIT] API ready (db.maxPool=" + dbMig.maxPoolSize
                + " cache.ttl=" + cache.ttlSec + "s)");
        }
        String handle(String req) {
            return "{ \"response\": \"handled " + req + "\" }";
        }
    }

    // ── container lifecycle ────────────────────────────────────────────
    static List<ManagedBean> startContainer() {
        System.out.println("=== Container startup ===");
        JvmProperties jvm    = new JvmProperties();   // ① no deps
        DbMigration   db     = new DbMigration(jvm);  // ② depends on jvm
        CacheWarmup   cache  = new CacheWarmup(jvm);  // ③ depends on jvm (+@DependsOn db)
        ApiService    api    = new ApiService(db, cache); // ④ depends on both
        System.out.println();
        return List.of(jvm, db, cache, api);           // creation order
    }

    static void shutdownContainer(List<ManagedBean> beans) {
        System.out.println("=== Container shutdown (reverse order) ===");
        // destroy in REVERSE creation order
        List<ManagedBean> reversed = new ArrayList<>(beans);
        Collections.reverse(reversed);
        reversed.forEach(ManagedBean::destroy);
        System.out.println("[DESTROY ORDER] " + DESTROY_LOG);
    }

    public static void main(String[] args) {
        List<ManagedBean> beans = startContainer();

        ApiService api = (ApiService) beans.get(3);
        System.out.println("[REQUEST] " + api.handle("GET /users"));
        System.out.println();

        shutdownContainer(beans);

        System.out.println();
        System.out.println("=== Verify destroy order ===");
        List<String> expected = List.of("ApiService", "CacheWarmup", "DbMigration", "JvmProperties");
        System.out.println("  Expected: " + expected);
        System.out.println("  Actual:   " + DESTROY_LOG);
        System.out.println("  Correct?  " + expected.equals(new ArrayList<>(DESTROY_LOG)));
    }
}
```

How to run: `java DependsOnDemo3.java`

Four-bean chain: `JvmProperties` → `DbMigration` → `CacheWarmup` → `ApiService`. The destroy order is the exact reverse: `ApiService` destroyed first, then `CacheWarmup`, `DbMigration`, finally `JvmProperties`. This mirrors Spring's guaranteed destroy ordering: a bean is always destroyed before any of its `depends-on` dependencies.

## 6. Walkthrough

**Container startup — creation order:**

```
Step 1: JvmProperties()
  → [BEAN] JvmProperties: created
  → props = {db.maxPoolSize:20, cache.ttlSec:300}

Step 2: DbMigration(jvmProps)    [depends-on JvmProperties via ref + @DependsOn]
  → [BEAN] DbMigration: created
  → maxPoolSize = parseInt("20") = 20
  → ran 3 migrations

Step 3: CacheWarmup(jvmProps)    [@DependsOn("dbMigration") — ordering only, no ref to DbMigration]
  → [BEAN] CacheWarmup: created
  → ttlSec = 300
  → warmed 500 entries

Step 4: ApiService(db, cache)    [refs to both → implied ordering]
  → [BEAN] ApiService: created
  → API ready
```

**Container shutdown — destroy order (reverse of creation):**

```
Step 1: ApiService.destroy()    → [DESTROY] ApiService
Step 2: CacheWarmup.destroy()   → [DESTROY] CacheWarmup
Step 3: DbMigration.destroy()   → [DESTROY] DbMigration
Step 4: JvmProperties.destroy() → [DESTROY] JvmProperties

DESTROY_LOG: [ApiService, CacheWarmup, DbMigration, JvmProperties] ← stack push order
Expected:    [ApiService, CacheWarmup, DbMigration, JvmProperties] ✓
```

The `depends-on` relationship guarantees that during destroy, `DbMigration` is still alive when `CacheWarmup` is being destroyed — useful if teardown needs the DB to be up.

## 7. Gotchas & takeaways

> **`@DependsOn` does not inject the referenced bean.** You only get the ordering guarantee — the dependency bean is created before yours and destroyed after yours, but you cannot call it. If you need to call it, inject it with `@Autowired`.

> **Circular `@DependsOn` (A depends-on B, B depends-on A) causes `BeanCreationException` at startup.** Spring detects the cycle during the graph-sort phase. There is no way around it — break the cycle by removing one direction.

- `@DependsOn` on a `@Configuration` class applies to all `@Bean` methods inside it — all beans from that configuration depend on the listed beans.
- The reverse-destroy guarantee is useful for connection pools: the pool should be destroyed **after** all services that use it are destroyed, not before.
- If the dependency is already implied by an `@Autowired` reference, `@DependsOn` is redundant — Spring already infers the ordering from the reference. Only add `@DependsOn` for non-injected side-effect dependencies.
- `depends-on` takes a comma-separated list in XML: `depends-on="migrationA,migrationB,cacheWarmup"`.
