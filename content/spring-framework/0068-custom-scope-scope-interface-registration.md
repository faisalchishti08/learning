---
card: spring-framework
gi: 68
slug: custom-scope-scope-interface-registration
title: Custom scope (Scope interface) & registration
---

## 1. What it is

Spring's built-in scopes (singleton, prototype, request, session) are implemented by the `org.springframework.beans.factory.config.Scope` interface. You can implement this interface to create **custom scopes** — any lifecycle boundary you need — and register it with `ConfigurableBeanFactory.registerScope(String name, Scope scope)`.

```java
// Implement the Scope interface
public class TenantScope implements Scope {
    private final Map<String, Map<String, Object>> tenantStores = new ConcurrentHashMap<>();

    @Override
    public Object get(String name, ObjectFactory<?> objectFactory) {
        String tenantId = TenantContext.getCurrentTenantId();
        Map<String, Object> store = tenantStores.computeIfAbsent(tenantId, id -> new ConcurrentHashMap<>());
        return store.computeIfAbsent(name, k -> objectFactory.getObject());
    }

    @Override
    public Object remove(String name) {
        String tenantId = TenantContext.getCurrentTenantId();
        Map<String, Object> store = tenantStores.get(tenantId);
        return store != null ? store.remove(name) : null;
    }
    // ... registerDestructionCallback, resolveContextualObject, getConversationId
}

// Register the scope
@Configuration
public class TenantScopeConfig {
    @Bean
    public static CustomScopeConfigurer tenantScopeConfigurer() {
        CustomScopeConfigurer configurer = new CustomScopeConfigurer();
        configurer.addScope("tenant", new TenantScope());
        return configurer;
    }
}

// Use the custom scope
@Component
@Scope("tenant")
public class TenantCache { ... }
```

In one sentence: **A custom scope lets you define any lifecycle boundary (tenant, job, batch step, conversation) by implementing `Scope` and registering it — Spring then manages bean creation and destruction within that boundary.**

## 2. Why & when

Built-in scopes cover request, session, singleton, and prototype. Custom scopes cover everything else:

- **Tenant scope** — one bean instance per tenant in a SaaS application.
- **Job scope** — one bean per batch job execution (`@JobScope` in Spring Batch).
- **Step scope** — one bean per batch step (`@StepScope` in Spring Batch).
- **Conversation scope** — one bean per multi-step user flow (not tied to one HTTP session).
- **Thread scope** — one bean per thread (`SimpleThreadScope`, not registered by default).

## 3. Core concept

```
Scope interface (4 required methods + 2 optional):

  Object get(String name, ObjectFactory<?> factory)
    → return existing instance OR call factory.getObject() to create a new one
    → store the new instance in your scope store

  Object remove(String name)
    → remove and return the bean from the scope store
    → called when the scope is explicitly cleaned up

  void registerDestructionCallback(String name, Runnable callback)
    → Spring registers a callback to be called when the bean is destroyed
    → you must call it when the scope ends

  Object resolveContextualObject(String key)
    → resolve well-known contextual objects (e.g., "request", "session") for SpEL
    → return null if not applicable

  String getConversationId()
    → returns a unique id for the current scope instance (e.g., sessionId)
    → used for logging and debugging

Registration:
  beanFactory.registerScope("tenant", new TenantScope());
  OR via CustomScopeConfigurer @Bean
```

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Custom scope: Scope interface, store, registration, and bean lifecycle">
  <defs>
    <marker id="a68" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="650" height="198" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="330" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Custom Scope — Scope interface, store, and lifecycle</text>

  <!-- Scope interface box -->
  <rect x="15" y="30" width="200" height="140" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="115" y="48" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">«interface» Scope</text>
  <text x="115" y="66" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="monospace">get(name, factory)</text>
  <text x="115" y="80" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="monospace">remove(name)</text>
  <text x="115" y="94" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="monospace">registerDestructionCallback</text>
  <text x="115" y="108" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="monospace">resolveContextualObject</text>
  <text x="115" y="122" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="monospace">getConversationId</text>
  <line x1="25" y1="130" x2="205" y2="130" stroke="#8b949e" stroke-width="0.5"/>
  <text x="115" y="145" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Implement to define lifecycle boundary</text>
  <text x="115" y="158" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">TenantScope / JobScope / etc.</text>

  <!-- Scope store -->
  <rect x="240" y="30" width="195" height="140" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="337" y="48" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Scope Store</text>
  <text x="337" y="64" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Map&lt;tenantId, Map&lt;name, Object&gt;&gt;</text>
  <rect x="250" y="72" width="175" height="22" rx="3" fill="#0d1117"/>
  <text x="337" y="86" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">tenant-A → {cache→CacheBean#1}</text>
  <rect x="250" y="97" width="175" height="22" rx="3" fill="#0d1117"/>
  <text x="337" y="111" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">tenant-B → {cache→CacheBean#2}</text>
  <rect x="250" y="122" width="175" height="22" rx="3" fill="#0d1117"/>
  <text x="337" y="136" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">tenant-C → {cache→CacheBean#3}</text>
  <text x="337" y="160" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Each tenant: own bean instances</text>

  <!-- Registration and usage -->
  <rect x="460" y="30" width="185" height="140" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="552" y="48" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Registration &amp; Usage</text>
  <text x="552" y="66" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">beanFactory</text>
  <text x="552" y="78" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">  .registerScope("tenant",</text>
  <text x="552" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">     new TenantScope())</text>
  <line x1="470" y1="100" x2="635" y2="100" stroke="#8b949e" stroke-width="0.5"/>
  <text x="552" y="115" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Scope("tenant")</text>
  <text x="552" y="127" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">public class TenantCache {}</text>
  <line x1="470" y1="137" x2="635" y2="137" stroke="#8b949e" stroke-width="0.5"/>
  <text x="552" y="153" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">@Autowired TenantCache cache</text>
  <text x="552" y="165" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">→ proxy → TenantScope.get()</text>

  <!-- Arrows -->
  <line x1="215" y1="90" x2="238" y2="90" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a68)"/>
  <line x1="435" y1="90" x2="458" y2="90" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a68)"/>

  <text x="330" y="193" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Custom scope: implement Scope interface → register → use @Scope("tenant") on beans.</text>
</svg>

`TenantScope` implements `Scope`, stores beans per tenant, and is registered with the container. Beans annotated `@Scope("tenant")` are looked up through `TenantScope.get()` on every access.

## 5. Runnable example

Scenario: a `TenantScope` that gives each tenant its own `TenantConfig` bean in a multi-tenant SaaS app.

### Level 1 — Basic

Implement the minimum `Scope` contract and demonstrate per-tenant isolation.

```java
// CustomScopeDemo.java — run with: java CustomScopeDemo.java
import java.util.*;
import java.util.function.Supplier;

public class CustomScopeDemo {

    // ── tenant context (simulates ThreadLocal in real Spring) ──────────
    static String CURRENT_TENANT = null;

    // ── Scope implementation ───────────────────────────────────────────
    static class TenantScope {
        // tenantId → beanName → instance
        private final Map<String, Map<String, Object>> store = new LinkedHashMap<>();
        private final Map<String, Map<String, Runnable>> callbacks = new LinkedHashMap<>();

        // get() — core method: return cached or create new
        @SuppressWarnings("unchecked")
        <T> T get(String name, Supplier<T> factory) {
            if (CURRENT_TENANT == null) throw new IllegalStateException("No active tenant");
            Map<String, Object> tenantStore =
                store.computeIfAbsent(CURRENT_TENANT, id -> new LinkedHashMap<>());
            return (T) tenantStore.computeIfAbsent(name, k -> {
                T bean = factory.get();
                System.out.println("    [SCOPE] created " + name + " for tenant=" + CURRENT_TENANT);
                return bean;
            });
        }

        // remove() — evict a bean from a tenant's scope
        Object remove(String tenantId, String name) {
            Map<String, Object> tenantStore = store.get(tenantId);
            if (tenantStore == null) return null;
            Object bean = tenantStore.remove(name);
            Map<String, Runnable> cb = callbacks.getOrDefault(tenantId, Map.of());
            Runnable destroy = cb.get(name);
            if (destroy != null) { destroy.run(); cb.remove(name); }
            return bean;
        }

        // registerDestructionCallback — Spring calls registered Runnable when scope ends
        void registerDestroyCallback(String name, Runnable callback) {
            callbacks.computeIfAbsent(CURRENT_TENANT, id -> new LinkedHashMap<>())
                     .put(name, callback);
        }

        // Evict entire tenant scope
        void destroyTenant(String tenantId) {
            System.out.println("    [SCOPE] destroying tenant=" + tenantId);
            Map<String, Runnable> cb = callbacks.remove(tenantId);
            if (cb != null) cb.values().forEach(Runnable::run);
            store.remove(tenantId);
        }

        String getConversationId() { return CURRENT_TENANT; }
    }

    // ── tenant-scoped bean ─────────────────────────────────────────────
    static class TenantConfig {
        private static int count = 0;
        final int id;
        final String tenantId;
        final String plan;
        final int    maxUsers;

        TenantConfig(String tenantId, String plan, int maxUsers) {
            id = ++count;
            this.tenantId = tenantId;
            this.plan     = plan;
            this.maxUsers = maxUsers;
            System.out.println("  [BEAN #" + id + "] TenantConfig: tenant=" + tenantId
                + " plan=" + plan + " maxUsers=" + maxUsers);
        }

        String greeting() { return "Hello, tenant " + tenantId + " (plan=" + plan + ")"; }
        boolean canAddUser(int currentCount) { return currentCount < maxUsers; }

        void destroy() { System.out.println("  [BEAN #" + id + " DESTROYED] tenant=" + tenantId); }
    }

    // ── service using scope ────────────────────────────────────────────
    static TenantScope SCOPE = new TenantScope();

    static TenantConfig tenantConfig() {
        // Simulate: Spring calls get("tenantConfig", objectFactory)
        return SCOPE.get("tenantConfig", () -> {
            // objectFactory creates the bean + registers destroy callback
            String[] plans = {"free:10", "pro:100", "enterprise:9999"};
            String[] parts = plans[Math.abs(CURRENT_TENANT.hashCode()) % plans.length].split(":");
            TenantConfig cfg = new TenantConfig(CURRENT_TENANT, parts[0], Integer.parseInt(parts[1]));
            SCOPE.registerDestroyCallback("tenantConfig", cfg::destroy);
            return cfg;
        });
    }

    static void handleRequest(String tenant, String action) {
        CURRENT_TENANT = tenant;
        try {
            TenantConfig cfg = tenantConfig();
            System.out.println("[REQUEST] tenant=" + tenant + " action=" + action
                + " beanId=" + cfg.id);
            System.out.println("  " + cfg.greeting());
            System.out.println("  canAddUser(5): " + cfg.canAddUser(5));
        } finally {
            CURRENT_TENANT = null;
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Requests from three tenants ===");
        handleRequest("acme-corp",    "view-dashboard");
        handleRequest("globex",       "add-user");
        handleRequest("acme-corp",    "generate-report");  // reuses acme's TenantConfig
        handleRequest("startup-xyz",  "signup");
        handleRequest("globex",       "view-billing");     // reuses globex's TenantConfig

        System.out.println("\n=== TenantConfig instances created: " + TenantConfig.count
            + " (one per tenant, not per request)");

        System.out.println("\n=== Tenant offboarding ===");
        SCOPE.destroyTenant("acme-corp");
        SCOPE.destroyTenant("globex");
        SCOPE.destroyTenant("startup-xyz");
    }
}
```

How to run: `java CustomScopeDemo.java`

Three tenants → three `TenantConfig` beans. `acme-corp` makes two requests but its `TenantConfig#1` is reused (the scope's `computeIfAbsent` returns the cached bean). When `destroyTenant("acme-corp")` is called, the registered destroy callback (`cfg::destroy`) is invoked. This is exactly how `registerDestructionCallback` works in Spring's `Scope` interface.

### Level 2 — Intermediate

A full `Scope` implementation with `registerDestructionCallback`, `resolveContextualObject`, and multiple tenant-scoped beans.

```java
// CustomScopeDemo2.java — run with: java CustomScopeDemo2.java
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Supplier;

public class CustomScopeDemo2 {

    static String CURRENT_TENANT = null;

    // ── full Scope interface simulation ───────────────────────────────
    static class TenantScope {
        private final ConcurrentHashMap<String, Map<String, Object>>   beanMap     = new ConcurrentHashMap<>();
        private final ConcurrentHashMap<String, Map<String, Runnable>> destroyMap  = new ConcurrentHashMap<>();

        @SuppressWarnings("unchecked")
        <T> T get(String name, Supplier<T> factory) {
            assertTenant();
            return (T) beanMap.computeIfAbsent(CURRENT_TENANT, id -> new ConcurrentHashMap<>())
                               .computeIfAbsent(name, k -> factory.get());
        }

        void registerDestructionCallback(String name, Runnable callback) {
            assertTenant();
            destroyMap.computeIfAbsent(CURRENT_TENANT, id -> new ConcurrentHashMap<>())
                       .put(name, callback);
        }

        Object resolveContextualObject(String key) {
            return switch (key) {
                case "tenant" -> CURRENT_TENANT;
                case "tenantStore" -> beanMap.get(CURRENT_TENANT);
                default -> null;
            };
        }

        String getConversationId() { return CURRENT_TENANT; }

        void destroyTenant(String tenantId) {
            System.out.println("  [SCOPE] destroying tenant=" + tenantId);
            Map<String, Runnable> callbacks = destroyMap.remove(tenantId);
            if (callbacks != null) callbacks.values().forEach(Runnable::run);
            beanMap.remove(tenantId);
        }

        void remove(String name) {
            assertTenant();
            Map<String, Object> store = beanMap.get(CURRENT_TENANT);
            if (store != null) {
                store.remove(name);
                Map<String, Runnable> cbs = destroyMap.get(CURRENT_TENANT);
                if (cbs != null) { Runnable cb = cbs.remove(name); if (cb != null) cb.run(); }
            }
        }

        private void assertTenant() {
            if (CURRENT_TENANT == null) throw new IllegalStateException("No active tenant context");
        }
    }

    static final TenantScope SCOPE = new TenantScope();

    // ── two tenant-scoped beans ────────────────────────────────────────
    static class TenantLimits {
        private static int count = 0;
        final int id; final String tenantId; final int maxUsers; final int maxStorageGb;
        TenantLimits(String tenantId, int maxUsers, int maxStorageGb) {
            id = ++count; this.tenantId = tenantId; this.maxUsers = maxUsers; this.maxStorageGb = maxStorageGb;
            System.out.println("    [LIMITS CREATED #" + id + "] tenant=" + tenantId
                + " maxUsers=" + maxUsers + " maxStorageGb=" + maxStorageGb);
        }
        void destroy() { System.out.println("    [LIMITS DESTROYED #" + id + "]"); }
    }

    static class TenantAuditLog {
        private static int count = 0;
        final int id; final String tenantId;
        private final List<String> entries = new ArrayList<>();
        TenantAuditLog(String tenantId) {
            id = ++count; this.tenantId = tenantId;
            System.out.println("    [AUDIT CREATED #" + id + "] tenant=" + tenantId);
        }
        void log(String event) { entries.add(event); }
        void destroy() {
            System.out.println("    [AUDIT DESTROYED #" + id + "] entries=" + entries.size());
        }
    }

    static TenantLimits limits()   {
        return SCOPE.get("tenantLimits", () -> {
            TenantLimits l;
            int mb = Math.abs(CURRENT_TENANT.hashCode()) % 3;
            l = switch (mb) {
                case 0 -> new TenantLimits(CURRENT_TENANT, 10,  5);
                case 1 -> new TenantLimits(CURRENT_TENANT, 100, 50);
                default -> new TenantLimits(CURRENT_TENANT, Integer.MAX_VALUE, 1000);
            };
            SCOPE.registerDestructionCallback("tenantLimits", l::destroy);
            return l;
        });
    }

    static TenantAuditLog audit() {
        return SCOPE.get("tenantAuditLog", () -> {
            TenantAuditLog a = new TenantAuditLog(CURRENT_TENANT);
            SCOPE.registerDestructionCallback("tenantAuditLog", a::destroy);
            return a;
        });
    }

    static void handle(String tenant, String event) {
        CURRENT_TENANT = tenant;
        try {
            TenantLimits l = limits();
            TenantAuditLog a = audit();
            System.out.println("[REQ] tenant=" + tenant + " event=" + event
                + " limits#=" + l.id + " audit#=" + a.id);
            a.log(event);
            System.out.println("  maxUsers=" + l.maxUsers + " log entries=" + a.entries.size());
        } finally { CURRENT_TENANT = null; }
    }

    public static void main(String[] args) {
        System.out.println("=== Requests ===");
        handle("acme", "login:alice");
        handle("beta", "login:bob");
        handle("acme", "login:carol");  // acme: reuses limits#1 and audit#1
        handle("beta", "create-report");
        handle("acme", "upload-file");

        System.out.println("\n=== Beans per tenant ===");
        System.out.println("  TenantLimits created: " + TenantLimits.count + " (one per tenant)");
        System.out.println("  TenantAuditLog created: " + TenantAuditLog.count + " (one per tenant)");

        System.out.println("\n=== Destroy acme's tenant scope ===");
        SCOPE.destroyTenant("acme");
        System.out.println("=== Destroy beta's tenant scope ===");
        SCOPE.destroyTenant("beta");
    }
}
```

How to run: `java CustomScopeDemo2.java`

Two tenant-scoped beans per tenant: `TenantLimits` and `TenantAuditLog`. Five requests from two tenants — only two `TenantLimits` and two `TenantAuditLog` instances ever created (one per tenant). `destroyTenant` fires both destroy callbacks in sequence.

### Level 3 — Advanced

Integrate the custom scope with a `BeanPostProcessor`-equivalent pattern; demonstrate scope eviction on demand and scope re-entry after eviction.

```java
// CustomScopeDemo3.java — run with: java CustomScopeDemo3.java
import java.util.*;
import java.util.concurrent.*;
import java.util.function.Supplier;

public class CustomScopeDemo3 {

    static final ThreadLocal<String> TENANT_TL = new ThreadLocal<>();

    static class FullTenantScope {
        private final ConcurrentHashMap<String, ConcurrentHashMap<String, Object>>   beans   = new ConcurrentHashMap<>();
        private final ConcurrentHashMap<String, ConcurrentHashMap<String, Runnable>> destroy = new ConcurrentHashMap<>();

        @SuppressWarnings("unchecked")
        <T> T get(String name, Supplier<T> factory) {
            String tenant = requireTenant();
            return (T) beans.computeIfAbsent(tenant, id -> new ConcurrentHashMap<>())
                             .computeIfAbsent(name, k -> factory.get());
        }

        void registerDestroy(String name, Runnable cb) {
            String tenant = requireTenant();
            destroy.computeIfAbsent(tenant, id -> new ConcurrentHashMap<>()).put(name, cb);
        }

        void evict(String name) {
            String tenant = requireTenant();
            ConcurrentHashMap<String, Object>   bs = beans.get(tenant);
            ConcurrentHashMap<String, Runnable>  ds = destroy.get(tenant);
            if (bs != null) bs.remove(name);
            if (ds != null) { Runnable cb = ds.remove(name); if (cb != null) cb.run(); }
            System.out.println("    [EVICT] " + name + " from tenant=" + tenant);
        }

        void destroyTenant(String tenant) {
            System.out.println("  [TENANT END] " + tenant);
            ConcurrentHashMap<String, Runnable> ds = destroy.remove(tenant);
            if (ds != null) ds.values().forEach(Runnable::run);
            beans.remove(tenant);
        }

        String requireTenant() {
            String t = TENANT_TL.get();
            if (t == null) throw new IllegalStateException("No tenant context");
            return t;
        }
    }

    static final FullTenantScope SCOPE = new FullTenantScope();

    // ── tenant-scoped bean with version tracking ───────────────────────
    static class TenantSettingsCache {
        private static int count = 0;
        final int    id;
        final String tenant;
        final Map<String, String> settings = new LinkedHashMap<>();
        private int version = 1;

        TenantSettingsCache(String tenant) {
            id = ++count; this.tenant = tenant;
            settings.put("locale", "en-US");
            settings.put("timezone", "UTC");
            settings.put("theme", "light");
            System.out.println("    [CACHE CREATED #" + id + "] tenant=" + tenant + " v" + version);
        }

        void update(String key, String value) { settings.put(key, value); version++; }
        String get(String key) { return settings.get(key); }
        void destroy() { System.out.println("    [CACHE DESTROYED #" + id + "] tenant=" + tenant + " v" + version); }
        @Override public String toString() { return "SettingsCache#" + id + "v" + version + settings; }
    }

    static TenantSettingsCache settingsCache() {
        return SCOPE.get("settingsCache", () -> {
            TenantSettingsCache c = new TenantSettingsCache(TENANT_TL.get());
            SCOPE.registerDestroy("settingsCache", c::destroy);
            return c;
        });
    }

    static void handle(String tenant, String action, String... args) {
        TENANT_TL.set(tenant);
        try {
            TenantSettingsCache cache = settingsCache();
            System.out.printf("[REQ] tenant=%-12s action=%-20s cache#=%d%n", tenant, action, cache.id);
            switch (action) {
                case "get-setting"    -> System.out.println("  " + args[0] + "=" + cache.get(args[0]));
                case "update-setting" -> { cache.update(args[0], args[1]); System.out.println("  updated: " + cache); }
                case "evict-cache"    -> SCOPE.evict("settingsCache");
            }
        } finally { TENANT_TL.remove(); }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Tenant A: normal requests ===");
        handle("tenant-A", "get-setting",    "locale");
        handle("tenant-A", "update-setting", "theme", "dark");
        handle("tenant-A", "get-setting",    "theme");

        System.out.println("\n=== Tenant B: concurrent requests ===");
        ExecutorService pool = Executors.newFixedThreadPool(3);
        List<Future<?>> futures = new ArrayList<>();
        futures.add(pool.submit(() -> handle("tenant-B", "get-setting", "timezone")));
        futures.add(pool.submit(() -> handle("tenant-B", "update-setting", "locale", "de-DE")));
        futures.add(pool.submit(() -> handle("tenant-A", "get-setting", "locale")));
        for (Future<?> f : futures) f.get();
        pool.shutdown();

        System.out.println("\n=== Evict tenant-A's cache (e.g., admin forced refresh) ===");
        handle("tenant-A", "evict-cache");
        System.out.println("=== Re-access: tenant-A gets fresh cache ===");
        handle("tenant-A", "get-setting", "locale");  // fresh bean created

        System.out.println("\n=== Tenant offboarding ===");
        SCOPE.destroyTenant("tenant-A");
        SCOPE.destroyTenant("tenant-B");
        System.out.println("[TOTAL CACHES CREATED] " + TenantSettingsCache.count);
    }
}
```

How to run: `java CustomScopeDemo3.java`

Demonstrates cache eviction: `SCOPE.evict("settingsCache")` destroys the current tenant's `TenantSettingsCache` and calls its destroy callback. The next request for the same tenant creates a fresh instance (version 1 again). This is equivalent to calling `remove()` on the `Scope` interface. Concurrent requests from different tenants use `ThreadLocal` for isolation.

## 6. Walkthrough

**`handle("tenant-A", "update-setting", "theme", "dark")`:**

```
TENANT_TL.set("tenant-A")
settingsCache():
  SCOPE.get("settingsCache", factory)
    beans.computeIfAbsent("tenant-A", ...) → existing map
    map.computeIfAbsent("settingsCache", ...) → cache already exists → RETURN TenantSettingsCache#1
cache.update("theme", "dark") → settings{locale:en-US, timezone:UTC, theme:dark} version=2
```

**`handle("tenant-A", "evict-cache")`:**

```
SCOPE.evict("settingsCache")
  tenant = "tenant-A"
  bs = beans.get("tenant-A") → {settingsCache: TenantSettingsCache#1}
  bs.remove("settingsCache") → cache removed from store
  ds.remove("settingsCache") → destroy callback retrieved
  callback.run() → TenantSettingsCache#1.destroy() prints [CACHE DESTROYED #1]
```

**Next `handle("tenant-A", "get-setting", ...)`:**

```
SCOPE.get("settingsCache", factory)
  map.computeIfAbsent("settingsCache", factory)
    → key absent (evicted) → factory.get()
    → new TenantSettingsCache("tenant-A")  ← [CACHE CREATED #3] v1
    → registerDestroy callback
  → return TenantSettingsCache#3 (fresh)
```

## 7. Gotchas & takeaways

> **`registerDestructionCallback` is your responsibility to call.** Spring gives you the `Runnable` — you must store it and invoke it when the scope ends. If you don't, `@PreDestroy` and `DisposableBean.destroy()` will never fire for beans in your custom scope.

> **Custom scopes must be registered before any bean of that scope is requested.** If `@Scope("tenant")` is used on a bean and `TenantScope` is not yet registered, Spring throws `IllegalStateException: No Scope registered for scope name 'tenant'`. Register via `BeanFactoryPostProcessor` (called before beans are created) — `CustomScopeConfigurer` is Spring's built-in helper for this.

- Use `CustomScopeConfigurer` (a `BeanFactoryPostProcessor`) to register scopes declaratively in a `@Configuration` class — it guarantees registration happens before any bean definition is processed.
- Spring Batch's `@JobScope` and `@StepScope` are custom scope implementations that follow exactly this pattern.
- `getConversationId()` returns a human-readable identifier for the scope (e.g., job execution ID, step ID, tenant ID) — useful for logging and for Spring to generate unique scoped target bean names.
- Your `Scope.get()` implementation must be **thread-safe** if multiple threads can access the same scope store concurrently (e.g., in a tenant scope where multiple threads serve the same tenant simultaneously).
