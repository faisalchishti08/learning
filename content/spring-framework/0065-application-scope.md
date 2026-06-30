---
card: spring-framework
gi: 65
slug: application-scope
title: application scope
---

## 1. What it is

**Application scope** creates one bean instance per `ServletContext` — effectively one per web application, shared across all sessions and all requests. It is similar to singleton scope, but while a singleton is scoped to the Spring `ApplicationContext`, an application-scoped bean is scoped to the `javax.servlet.ServletContext`. In a standard single-context Spring Boot app the two are equivalent; they differ when multiple Spring `ApplicationContext` instances share one `ServletContext`.

```java
@Component
@Scope(value = WebApplicationContext.SCOPE_APPLICATION,
       proxyMode = ScopedProxyMode.TARGET_CLASS)
public class AppMetrics {
    private final AtomicLong totalRequests = new AtomicLong();
    // One instance for the whole application lifetime
}

// Shortcut:
@Component
@ApplicationScope
public class FeatureFlagRegistry {
    private final Map<String, Boolean> flags = new ConcurrentHashMap<>();
}
```

In one sentence: **Application-scoped beans are created once per `ServletContext` and shared across all sessions, requests, and users — making them suitable for application-wide state, global counters, and servlet-context-level registries.**

## 2. Why & when

Use application scope (vs singleton) when:

- You want the bean to be associated with the **`ServletContext`** lifecycle specifically — created when the servlet context starts, destroyed when it stops.
- You need to store data in the **`ServletContext` attributes** (accessible to other servlets or filters).
- You have multiple Spring `ApplicationContext` instances sharing one `ServletContext` (e.g., a root context + dispatcher context) and you want one shared bean across both.

In practice, for most Spring Boot applications a `@Singleton` bean serves the same purpose. Use `@ApplicationScope` when the distinction matters (classic Spring MVC with split contexts, or integration with legacy servlet filters/listeners).

## 3. Core concept

```
Scope hierarchy (widest to narrowest):
  ApplicationContext (singleton) ≈ application scope (per ServletContext)
    ↓
  Session scope (per HttpSession — one per user)
    ↓
  Request scope (per HTTP request — one per request)
    ↓
  (WebSocket scope — per WebSocket session)

ApplicationScope vs Singleton:
  Singleton: one per Spring ApplicationContext
  Application: one per ServletContext
  In a standard Spring Boot app: both produce one instance (same thing).
  In split-context apps (root + dispatcher): 
    singleton may appear twice; application scope exists once in ServletContext.

Bean stored as ServletContext attribute:
  context.setAttribute(beanName, beanInstance)
  → accessible to non-Spring components (JSP, legacy servlets)
```

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application scope hierarchy: one bean per ServletContext, wider than session or request scope">
  <defs>
    <marker id="a65" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="650" height="198" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="330" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Scope hierarchy — application scope is the widest web scope</text>

  <!-- Application scope -->
  <rect x="30" y="30" width="600" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="50" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Application Scope  (per ServletContext)</text>
  <text x="330" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">FeatureFlagRegistry, AppMetrics — shared across ALL users, ALL sessions, ALL requests</text>

  <!-- Session scope -->
  <rect x="50" y="88" width="260" height="42" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="180" y="104" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Session Scope (Alice — JSESSIONID=AAA)</text>
  <text x="180" y="120" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">ShoppingBasket#A — Alice's items</text>

  <rect x="350" y="88" width="260" height="42" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="480" y="104" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Session Scope (Bob — JSESSIONID=BBB)</text>
  <text x="480" y="120" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">ShoppingBasket#B — Bob's items</text>

  <!-- Request scope -->
  <rect x="50" y="143" width="120" height="30" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="110" y="161" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Request#1 (Alice)</text>
  <rect x="180" y="143" width="120" height="30" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="240" y="161" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Request#2 (Alice)</text>
  <rect x="350" y="143" width="120" height="30" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="410" y="161" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Request#3 (Bob)</text>
  <rect x="480" y="143" width="120" height="30" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="540" y="161" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Request#4 (Bob)</text>

  <!-- Arrows -->
  <line x1="330" y1="75" x2="180" y2="86" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a65)"/>
  <line x1="330" y1="75" x2="480" y2="86" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a65)"/>

  <text x="330" y="198" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Application-scope bean accessed by all sessions and requests. Singleton is almost equivalent in practice.</text>
</svg>

Application-scoped bean sits at the top of the web scope hierarchy. All sessions, all requests — everyone shares it.

## 5. Runnable example

Scenario: a `FeatureFlagRegistry` and an `AppMetrics` counter that are application-wide. All users and requests share the same instance.

### Level 1 — Basic

One instance for the whole application — all requests see the same counters.

```java
// ApplicationScopeDemo.java — run with: java ApplicationScopeDemo.java
import java.util.*;
import java.util.concurrent.atomic.*;

public class ApplicationScopeDemo {

    // ── application-scoped bean ───────────────────────────────────────
    static class AppMetrics {
        private static int instanceCount = 0;
        final int id;
        private final AtomicLong requestCount  = new AtomicLong();
        private final AtomicLong errorCount    = new AtomicLong();
        private final long       startTimeMs   = System.currentTimeMillis();

        AppMetrics() {
            id = ++instanceCount;
            System.out.println("  [APP BEAN CREATED #" + id + "] (one per application)");
        }

        void recordRequest(boolean error) {
            requestCount.incrementAndGet();
            if (error) errorCount.incrementAndGet();
        }

        String summary() {
            long uptimeSec = (System.currentTimeMillis() - startTimeMs) / 1000;
            return String.format("AppMetrics#%d: requests=%d errors=%d uptime=%ds",
                id, requestCount.get(), errorCount.get(), uptimeSec);
        }

        void destroy() {
            System.out.println("  [APP BEAN DESTROYED #" + id + "] final: " + summary());
        }
    }

    // ── simulated request handler ─────────────────────────────────────
    static class ServletContext {
        final AppMetrics metrics = new AppMetrics();  // application-scoped singleton
    }

    static void handleRequest(ServletContext ctx, String user, String path, boolean error) {
        System.out.println("[REQUEST] user=" + user + " path=" + path + " error=" + error
            + " metricsId=" + ctx.metrics.id);
        ctx.metrics.recordRequest(error);
    }

    public static void main(String[] args) {
        ServletContext ctx = new ServletContext();

        // Multiple users, multiple sessions — all share the same AppMetrics instance
        handleRequest(ctx, "alice", "/products",   false);
        handleRequest(ctx, "alice", "/cart",       false);
        handleRequest(ctx, "bob",   "/products",   false);
        handleRequest(ctx, "carol", "/checkout",   true);   // simulated error
        handleRequest(ctx, "dave",  "/products",   false);
        handleRequest(ctx, "alice", "/orders",     false);

        System.out.println("\n[METRICS] " + ctx.metrics.summary());
        System.out.println("[INSTANCES CREATED] " + AppMetrics.instanceCount
            + " (only 1 for entire application)");
        ctx.metrics.destroy();
    }
}
```

How to run: `java ApplicationScopeDemo.java`

`AppMetrics` is created once. Six requests from four different users all increment the same `requestCount`. The counter at the end shows `requests=6 errors=1` — all tracked through the single application-scoped instance.

### Level 2 — Intermediate

Feature flag registry: application-wide flags read by all sessions, writable by admin requests.

```java
// ApplicationScopeDemo2.java — run with: java ApplicationScopeDemo2.java
import java.util.*;
import java.util.concurrent.*;

public class ApplicationScopeDemo2 {

    // ── application-scoped feature flag registry ───────────────────────
    static class FeatureFlagRegistry {
        private static int count = 0;
        final int id;
        private final ConcurrentHashMap<String, Boolean> flags = new ConcurrentHashMap<>();

        FeatureFlagRegistry() {
            id = ++count;
            // Defaults
            flags.put("newCheckout",     false);
            flags.put("darkMode",        true);
            flags.put("betaSearch",      false);
            flags.put("loyaltyProgram",  true);
            System.out.println("  [APP BEAN CREATED #" + id + "] flags=" + flags);
        }

        boolean isEnabled(String flag) {
            return flags.getOrDefault(flag, false);
        }

        void setFlag(String flag, boolean value) {
            flags.put(flag, value);
            System.out.println("  [FLAG UPDATED] " + flag + " → " + value
                + " (visible to ALL users immediately)");
        }

        void destroy() {
            System.out.println("  [APP BEAN DESTROYED #" + id + "]");
        }
    }

    // ── request handler ────────────────────────────────────────────────
    static String handle(FeatureFlagRegistry flags, String user, String feature) {
        boolean enabled = flags.isEnabled(feature);
        System.out.println("[REQUEST] user=" + user + " feature=" + feature
            + " enabled=" + enabled + " flagsId=" + flags.id);
        return enabled ? "feature active" : "feature inactive";
    }

    public static void main(String[] args) {
        FeatureFlagRegistry flags = new FeatureFlagRegistry();  // application-scoped

        System.out.println("=== Initial state — all users see same flags ===");
        System.out.println("  Alice newCheckout: "  + handle(flags, "alice", "newCheckout"));
        System.out.println("  Bob   newCheckout: "  + handle(flags, "bob",   "newCheckout"));
        System.out.println("  Carol loyaltyProgram: " + handle(flags, "carol", "loyaltyProgram"));

        System.out.println("\n=== Admin enables newCheckout (affects ALL users) ===");
        flags.setFlag("newCheckout", true);
        System.out.println("  Alice newCheckout: " + handle(flags, "alice", "newCheckout"));
        System.out.println("  Bob   newCheckout: " + handle(flags, "bob",   "newCheckout"));

        System.out.println("\n=== Beta launched, betaSearch enabled ===");
        flags.setFlag("betaSearch", true);
        System.out.println("  Dave  betaSearch: " + handle(flags, "dave", "betaSearch"));

        System.out.println("\n[INSTANCES CREATED] " + FeatureFlagRegistry.count);
        flags.destroy();
    }
}
```

How to run: `java ApplicationScopeDemo2.java`

`FeatureFlagRegistry` is created once. When an admin enables `newCheckout`, all subsequent requests — Alice, Bob, Dave — immediately see `enabled=true` through the same instance. No cache invalidation needed — it's one shared object.

### Level 3 — Advanced

Concurrent all-user access, write-through to simulated `ServletContext` attributes, and application-level statistics.

```java
// ApplicationScopeDemo3.java — run with: java ApplicationScopeDemo3.java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class ApplicationScopeDemo3 {

    // ── application-scoped "dashboard" — written by all requests ──────
    static class ApplicationDashboard {
        private static final AtomicInteger seq = new AtomicInteger();
        final int id;

        // All fields are thread-safe (concurrent access from all requests)
        private final AtomicLong            totalRequests   = new AtomicLong();
        private final AtomicLong            activeUsers     = new AtomicLong();
        private final ConcurrentHashMap<String, AtomicLong> endpointHits = new ConcurrentHashMap<>();
        private final ConcurrentHashMap<String, Long>       lastSeen     = new ConcurrentHashMap<>();
        private final long                                  startMs      = System.currentTimeMillis();

        ApplicationDashboard() {
            id = seq.incrementAndGet();
            System.out.println("  [APP BEAN #" + id + "] ApplicationDashboard created");
        }

        void onRequest(String userId, String endpoint) {
            totalRequests.incrementAndGet();
            lastSeen.put(userId, System.currentTimeMillis());
            endpointHits.computeIfAbsent(endpoint, k -> new AtomicLong()).incrementAndGet();
        }

        void onLogin(String userId) {
            activeUsers.incrementAndGet();
            System.out.printf("  [LOGIN]  userId=%s activeUsers=%d%n", userId, activeUsers.get());
        }

        void onLogout(String userId) {
            activeUsers.decrementAndGet();
            System.out.printf("  [LOGOUT] userId=%s activeUsers=%d%n", userId, activeUsers.get());
        }

        void printDashboard() {
            long uptimeMs = System.currentTimeMillis() - startMs;
            System.out.println("\n  === Application Dashboard (bean #" + id + ") ===");
            System.out.printf("  Uptime:        %dms%n", uptimeMs);
            System.out.printf("  Total requests:%d%n", totalRequests.get());
            System.out.printf("  Active users:  %d%n", activeUsers.get());
            System.out.println("  Endpoint hits:");
            endpointHits.entrySet().stream()
                .sorted(Map.Entry.<String, AtomicLong>comparingByValue(
                    Comparator.comparingLong(AtomicLong::get)).reversed())
                .forEach(e -> System.out.printf("    %-25s %d%n", e.getKey(), e.getValue().get()));
            System.out.println("  Last seen (users): " + lastSeen.keySet());
        }

        void destroy() {
            System.out.println("  [APP BEAN DESTROYED #" + id + "] requests=" + totalRequests);
        }
    }

    // ── simulate servlet context with multiple concurrent users ────────
    static void simulate(ApplicationDashboard dash) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(8);
        List<Future<?>> futures = new ArrayList<>();

        String[][] userRequests = {
            {"alice",  "/products"},    {"alice",  "/cart"},
            {"bob",    "/products"},    {"bob",    "/checkout"},
            {"carol",  "/dashboard"},  {"carol",  "/products"},
            {"dave",   "/orders"},     {"dave",   "/products"},
            {"eve",    "/search"},     {"eve",    "/search"},
            {"frank",  "/products"},   {"frank",  "/cart"},
        };

        for (String[] req : userRequests) {
            final String user = req[0], endpoint = req[1];
            futures.add(pool.submit(() -> dash.onRequest(user, endpoint)));
        }

        for (Future<?> f : futures) f.get();
        pool.shutdown();
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Application startup ===");
        ApplicationDashboard dash = new ApplicationDashboard();  // one for the whole app

        System.out.println("\n=== Users logging in ===");
        dash.onLogin("alice");
        dash.onLogin("bob");
        dash.onLogin("carol");

        System.out.println("\n=== Concurrent requests from all users ===");
        simulate(dash);

        System.out.println("\n=== More logins ===");
        dash.onLogin("dave");
        dash.onLogin("eve");
        dash.onLogin("frank");

        System.out.println("\n=== Some users log out ===");
        dash.onLogout("bob");
        dash.onLogout("carol");

        dash.printDashboard();

        System.out.println();
        System.out.println("[APP BEAN INSTANCES CREATED] " + ApplicationDashboard.seq.get()
            + " (only 1 for the entire application)");
        dash.destroy();
    }
}
```

How to run: `java ApplicationScopeDemo3.java`

12 concurrent requests from 6 users all feed into the single `ApplicationDashboard` instance. `AtomicLong` counters and `ConcurrentHashMap` ensure no data is lost under concurrency. `printDashboard()` shows unified stats gathered from all users through the one shared application-scoped bean.

## 6. Walkthrough

**`simulate(dash)` — concurrent access:**

```
12 tasks submitted to 8-thread pool.
Each task calls: dash.onRequest(user, endpoint)

onRequest("alice", "/products"):
  totalRequests.incrementAndGet() → atomic, thread-safe
  lastSeen.put("alice", now)      → ConcurrentHashMap, thread-safe
  endpointHits.computeIfAbsent("/products", ...).incrementAndGet()

[All 12 tasks run in parallel]

After all complete:
  totalRequests = 12 (no lost increments)
  endpointHits:
    /products  = 5  (alice, bob, carol, frank x2 → count varies by test)
    /cart      = 2
    /checkout  = 1
    /search    = 2
    /orders    = 1
    /dashboard = 1
  lastSeen keys: {alice, bob, carol, dave, eve, frank}
```

**Scope comparison with singleton:**

```
Singleton: created at Spring ApplicationContext refresh.
  → If root + dispatcher contexts both define the bean, TWO instances exist.

Application scope: stored in ServletContext.
  → Only ONE instance regardless of how many Spring contexts share that ServletContext.
  → Destroyed at ServletContext.destroy() (app shutdown).

In Spring Boot (single context): no practical difference between the two.
```

## 7. Gotchas & takeaways

> **Application-scoped beans are not the same as singleton beans in a split-context setup.** A root `WebApplicationContext` (loaded by `ContextLoaderListener`) and a dispatcher `WebApplicationContext` (loaded by `DispatcherServlet`) each have their own singleton cache, but they share one `ServletContext`. Application-scoped beans live in the `ServletContext` — one shared instance; singleton beans may be duplicated.

> **All requests from all users share the same instance — mutable state must be thread-safe.** Use `AtomicLong`, `ConcurrentHashMap`, and other concurrent types. Never use unsynchronised `HashMap` or `int` counters in an application-scoped bean.

- `@ApplicationScope` (Spring 4.3+) is shorthand for `@Scope(value="application", proxyMode=ScopedProxyMode.TARGET_CLASS)`.
- Application-scoped beans are accessible via `ServletContext.getAttribute(beanName)` — useful for integration with non-Spring components (legacy servlets, JSP, filters).
- Destroyed at `ServletContext.destroy()` — i.e., when the web application is undeployed. `@PreDestroy` is called at that time.
- In embedded server (Spring Boot) applications, `ServletContext.destroy()` is called on JVM shutdown — effectively the same as `ApplicationContext.close()`.
