---
card: spring-framework
gi: 184
slug: standard-context-events-refreshed-started-stopped-closed
title: "Standard context events (Refreshed, Started, Stopped, Closed)"
---

## 1. What it is

Spring's `ApplicationContext` fires a set of **lifecycle events** at fixed points in its own startup and shutdown sequence. These events are published internally — your code listens to them to hook into the container lifecycle.

| Event | Fired when |
|---|---|
| `ContextRefreshedEvent` | Context has been refreshed (beans created, dependencies injected, `SmartInitializingSingleton` run). Fires on every `refresh()` call including re-refresh. |
| `ContextStartedEvent` | `context.start()` explicitly called. Signals `Lifecycle` beans to start. |
| `ContextStoppedEvent` | `context.stop()` explicitly called. Signals `Lifecycle` beans to stop (but context is not closed). |
| `ContextClosedEvent` | `context.close()` called (or JVM shutdown hook fires). Beans are being destroyed. |
| `ApplicationStartedEvent` | Spring Boot only: application started but `ApplicationRunner` / `CommandLineRunner` not yet called. |
| `ApplicationReadyEvent` | Spring Boot only: application is fully ready to serve requests. |

## 2. Why & when

- **`ContextRefreshedEvent`** — warm up caches, validate external config, prefetch reference data. Fires reliably after all beans are wired; safer than `@PostConstruct` for work that depends on the full context being ready.
- **`ContextClosedEvent`** — flush write-behind caches, release file handles, log shutdown audit records.
- **`ContextStartedEvent` / `ContextStoppedEvent`** — control pauseable subsystems (rate limiters, scheduled jobs) without destroying them — `stop` pauses, `start` resumes.
- **`ApplicationReadyEvent`** (Spring Boot) — perform any action that should run only after the app is serving traffic: post-deployment health checks, registration with a service registry.
- **Prefer `@EventListener` annotation** (next topic) over implementing `ApplicationListener` for less boilerplate.

## 3. Core concept

**Standard lifecycle sequence:**

```
1. SpringApplication.run() or new AnnotationConfigApplicationContext()
2. Beans instantiated + injected
3. @PostConstruct methods run
4. SmartInitializingSingleton.afterSingletonsInstantiated() called
5. → ContextRefreshedEvent fired ←
6. (Spring Boot only) → ApplicationStartedEvent fired
7. CommandLineRunner / ApplicationRunner beans called
8. (Spring Boot only) → ApplicationReadyEvent fired
─────────────────────── running ───────────────────────────
9. context.stop() called (optional)  → ContextStoppedEvent
10. context.start() called (optional) → ContextStartedEvent
─────────────────────── running ───────────────────────────
11. context.close() or JVM shutdown hook
12. @PreDestroy methods run
13. → ContextClosedEvent fired ←
```

**`ContextRefreshedEvent` vs `@PostConstruct`:**

`@PostConstruct` runs when the *individual bean* is fully constructed. `ContextRefreshedEvent` fires when the *entire context* is ready — all beans created, all `ApplicationRunner` beans about to run. Use `@PostConstruct` for bean-local setup; use `ContextRefreshedEvent` for work that depends on other beans being ready (e.g., calling another service to warm a cache).

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="lca" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Timeline -->
  <line x1="40" y1="100" x2="670" y2="100" stroke="#8b949e" stroke-width="2"/>
  <text x="10" y="104" fill="#8b949e" font-size="8" font-family="sans-serif">time →</text>

  <!-- Startup phase -->
  <rect x="40" y="60" width="120" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="100" y="79" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">beans created</text>
  <text x="100" y="89" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">+@PostConstruct</text>

  <!-- ContextRefreshedEvent -->
  <line x1="162" y1="70" x2="162" y2="130" stroke="#6db33f" stroke-width="2"/>
  <text x="162" y="145" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif" transform="rotate(-30,162,145)">ContextRefreshedEvent</text>
  <circle cx="162" cy="100" r="5" fill="#6db33f"/>

  <!-- Running phase -->
  <rect x="175" y="75" width="80" height="20" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="215" y="89" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">cache warm-up</text>

  <!-- ContextStartedEvent -->
  <line x1="290" y1="70" x2="290" y2="130" stroke="#79c0ff" stroke-width="2" stroke-dasharray="4,3"/>
  <circle cx="290" cy="100" r="4" fill="#79c0ff"/>
  <text x="290" y="148" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif" transform="rotate(-30,290,148)">ContextStartedEvent</text>

  <!-- Running -->
  <rect x="300" y="75" width="90" height="20" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="345" y="89" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">serving requests</text>

  <!-- ContextStoppedEvent -->
  <line x1="420" y1="70" x2="420" y2="130" stroke="#79c0ff" stroke-width="2" stroke-dasharray="4,3"/>
  <circle cx="420" cy="100" r="4" fill="#79c0ff"/>
  <text x="420" y="148" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif" transform="rotate(-30,420,148)">ContextStoppedEvent</text>

  <!-- Paused -->
  <rect x="430" y="75" width="80" height="20" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="470" y="89" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">paused…</text>

  <!-- ContextClosedEvent -->
  <line x1="560" y1="70" x2="560" y2="130" stroke="#e74c3c" stroke-width="2"/>
  <circle cx="560" cy="100" r="5" fill="#e74c3c"/>
  <text x="560" y="148" fill="#e74c3c" font-size="7" text-anchor="middle" font-family="sans-serif" transform="rotate(-30,560,148)">ContextClosedEvent</text>

  <!-- Shutdown -->
  <rect x="568" y="60" width="90" height="30" rx="4" fill="#1c2430" stroke="#e74c3c" stroke-width="1"/>
  <text x="613" y="79" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">@PreDestroy</text>
  <text x="613" y="89" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">+ shutdown</text>

  <!-- Labels -->
  <text x="350" y="185" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">
    ContextRefreshed (solid green) = most commonly used.  Started/Stopped (dashed blue) = optional pause/resume.  Closed (red) = shutdown.
  </text>
</svg>

`ContextRefreshedEvent` is the post-startup hook; `ContextClosedEvent` is the pre-shutdown hook. Started/Stopped events bracket optional pause/resume cycles without closing the context.

## 5. Runnable example

The scenario is a **cache-warming and graceful-shutdown system** — growing from a simple `ContextRefreshedEvent` listener to a complete lifecycle management pattern.

### Level 1 — Basic

Listen to `ContextRefreshedEvent` to warm a cache after the context is fully started.

```java
// ContextEventsBasic.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Service
class ProductCache {
    private java.util.List<String> data = new java.util.ArrayList<>();
    public void load()               { data = java.util.List.of("Laptop","Phone","Tablet"); }
    public java.util.List<String> get() { return data; }
}

// Warm the cache when the ENTIRE context is ready
@Component
class CacheWarmer implements ApplicationListener<ContextRefreshedEvent> {
    private final ProductCache cache;
    CacheWarmer(ProductCache cache) { this.cache = cache; }

    @Override
    public void onApplicationEvent(ContextRefreshedEvent event) {
        System.out.println("[CacheWarmer] Context refreshed — loading cache...");
        cache.load();
        System.out.println("[CacheWarmer] Cache loaded: " + cache.get());
    }
}

@Configuration
@ComponentScan
class BasicConfig { }

public class ContextEventsBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(BasicConfig.class);
        // ContextRefreshedEvent was fired during ctx construction above
        var cache = ctx.getBean(ProductCache.class);
        System.out.println("Cache ready: " + cache.get());
        ctx.close();  // fires ContextClosedEvent
        System.out.println("Context closed.");
    }
}
```

How to run: `java ContextEventsBasic.java`

`ContextRefreshedEvent` fires *during* `new AnnotationConfigApplicationContext(...)` once all beans are created and wired. The cache is fully populated by the time the `main` method reaches `ctx.getBean(ProductCache.class)`. `ctx.close()` fires `ContextClosedEvent` — if you have a listener for it, it runs before the JVM exits.

### Level 2 — Intermediate

Listen to `ContextRefreshedEvent`, `ContextClosedEvent`, and avoid double-loading on re-refresh.

```java
// ContextEventsIntermediate.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.util.*;
import java.util.concurrent.atomic.*;

@Service
class ReferenceDataCache {
    private volatile List<String> countries = List.of();
    private volatile boolean loaded = false;
    public void load()             { countries = List.of("US","UK","DE","JP","AU"); loaded=true; }
    public List<String> getAll()   { return countries; }
    public boolean isLoaded()      { return loaded; }
    public void evict()            { countries = List.of(); loaded = false; }
}

@Component
class LifecycleListener
    implements ApplicationListener<ApplicationContextEvent> {
    // ApplicationContextEvent is the supertype of all four context events
    private final ReferenceDataCache cache;
    private final AtomicBoolean refreshed = new AtomicBoolean(false);

    LifecycleListener(ReferenceDataCache cache) { this.cache = cache; }

    @Override
    public void onApplicationEvent(ApplicationContextEvent event) {
        if (event instanceof ContextRefreshedEvent) {
            // Guard: ContextRefreshedEvent fires on EVERY refresh (incl. child contexts)
            if (refreshed.compareAndSet(false, true)) {
                System.out.println("[Lifecycle] ContextRefreshed → warming cache");
                cache.load();
            } else {
                System.out.println("[Lifecycle] ContextRefreshed again — skipping (already loaded)");
            }
        } else if (event instanceof ContextStartedEvent) {
            System.out.println("[Lifecycle] ContextStarted → resuming scheduled tasks");
        } else if (event instanceof ContextStoppedEvent) {
            System.out.println("[Lifecycle] ContextStopped → pausing scheduled tasks");
        } else if (event instanceof ContextClosedEvent) {
            System.out.println("[Lifecycle] ContextClosed → flushing cache to disk");
            cache.evict();
        }
    }
}

@Configuration
@ComponentScan
class IntermConfig { }

public class ContextEventsIntermediate {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(IntermConfig.class);
        System.out.println("Cache after refresh: " + ctx.getBean(ReferenceDataCache.class).getAll());

        // Manually trigger start/stop cycle (normally done by lifecycle manager)
        ctx.start();  // → ContextStartedEvent
        ctx.stop();   // → ContextStoppedEvent
        ctx.start();  // → ContextStartedEvent (resume)

        // Simulate re-refresh (rare but can happen with child contexts in tests)
        ctx.refresh();
        System.out.println("Cache after re-refresh: " + ctx.getBean(ReferenceDataCache.class).getAll());

        ctx.close();  // → ContextClosedEvent
    }
}
```

How to run: `java ContextEventsIntermediate.java`

`ApplicationContextEvent` is the common supertype of all four context events; one listener catches all four with a single `instanceof` dispatch. `AtomicBoolean refreshed` guards against double-loading: `ContextRefreshedEvent` can fire multiple times in apps with parent/child contexts (common in Spring MVC with `DispatcherServlet`'s child context). `ctx.start()` and `ctx.stop()` demonstrate the pause/resume lifecycle without destroying beans.

### Level 3 — Advanced

A Spring Boot app with `ApplicationReadyEvent` for post-startup service registration, and `ContextClosedEvent` for graceful shutdown with connection draining.

```java
// ContextEventsAdvanced.java — Spring Boot lifecycle hooks
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.context.event.*;
import org.springframework.stereotype.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

@org.springframework.stereotype.Component
class ServiceRegistry {
    private final Set<String> registered = ConcurrentHashMap.newKeySet();
    public void register(String name)   { registered.add(name);    System.out.println("[Registry] Registered: " + name); }
    public void deregister(String name) { registered.remove(name); System.out.println("[Registry] Deregistered: " + name); }
    public Set<String> getAll() { return registered; }
}

@org.springframework.stereotype.Component
class ConnectionPool {
    private final AtomicInteger active = new AtomicInteger(0);
    public void init()   { active.set(10); System.out.println("[Pool] Initialised 10 connections"); }
    public void drain()  {
        System.out.println("[Pool] Draining " + active.get() + " connections…");
        active.set(0);
        System.out.println("[Pool] Drained.");
    }
    public int getActive() { return active.get(); }
}

@org.springframework.stereotype.Component
class AppLifecycleManager {
    private final ServiceRegistry registry;
    private final ConnectionPool pool;

    AppLifecycleManager(ServiceRegistry registry, ConnectionPool pool) {
        this.registry = registry;
        this.pool     = pool;
    }

    // Fires after full startup — safe to init connection pool and register with discovery
    @EventListener(ApplicationReadyEvent.class)
    public void onReady(ApplicationReadyEvent event) {
        pool.init();
        registry.register("order-service-" + ProcessHandle.current().pid());
        System.out.println("[AppLifecycle] Ready. Active connections: " + pool.getActive());
    }

    // Fires on ctx.close() or JVM shutdown — drain connections, deregister
    @EventListener(ContextClosedEvent.class)
    public void onClose(ContextClosedEvent event) {
        System.out.println("[AppLifecycle] Shutting down…");
        registry.getAll().forEach(registry::deregister);
        pool.drain();
    }
}

@SpringBootApplication
public class ContextEventsAdvanced {
    public static void main(String[] args) {
        var ctx = SpringApplication.run(ContextEventsAdvanced.class, args);
        System.out.println("Application is running. Registered services: "
            + ctx.getBean(ServiceRegistry.class).getAll());
        // Simulate shutdown
        ctx.close();
    }
}
```

How to run: `./mvnw spring-boot:run` or `java ContextEventsAdvanced.java`

`@EventListener(ApplicationReadyEvent.class)` (Spring Boot only) is the safest hook for work that must run after ALL startup steps including `CommandLineRunner` and `ApplicationRunner`. Using `ContextClosedEvent` for deregistration + connection draining ensures graceful shutdown even when the JVM receives a SIGTERM (Spring Boot registers a JVM shutdown hook that fires `ContextClosedEvent`).

## 6. Walkthrough

Tracing startup and shutdown of the Level 3 app:

**Startup sequence:**

1. `SpringApplication.run` begins.
2. Beans created: `ServiceRegistry`, `ConnectionPool`, `AppLifecycleManager`.
3. `@PostConstruct` methods run (none in this example).
4. **`ContextRefreshedEvent` fired** — Spring's internal autoconfigurations hook here.
5. Spring Boot continues: `CommandLineRunner` beans run (none here).
6. **`ApplicationStartedEvent` fired** — emitted just before runners complete.
7. **`ApplicationReadyEvent` fired** — Spring Boot calls `AppLifecycleManager.onReady`:
   - `pool.init()` → `[Pool] Initialised 10 connections`
   - `registry.register("order-service-<pid>")` → `[Registry] Registered: order-service-1234`
   - Prints `[AppLifecycle] Ready. Active connections: 10`
8. `SpringApplication.run` returns; `main` prints registered services.

**Shutdown (`ctx.close()`):**

1. Spring Boot's shutdown hook (or explicit `ctx.close()`) calls `AbstractApplicationContext.close()`.
2. **`ContextClosedEvent` fired** — `AppLifecycleManager.onClose` runs:
   - `registry.getAll().forEach(registry::deregister)` → `[Registry] Deregistered: order-service-1234`
   - `pool.drain()` → `[Pool] Draining 10 connections… [Pool] Drained.`
3. `@PreDestroy` methods run.
4. Beans destroyed.
5. JVM exits.

**Data flow through the lifecycle:**

```
main → SpringApplication.run()
         ↓ beans created
         ↓ ContextRefreshedEvent (internal)
         ↓ ApplicationReadyEvent
               pool.init()              → pool.active = 10
               registry.register(pid)   → registry = {order-service-1234}
         ↓ main continues (app running)
main → ctx.close()
         ↓ ContextClosedEvent
               registry.deregister(all) → registry = {}
               pool.drain()             → pool.active = 0
         ↓ beans destroyed
```

## 7. Gotchas & takeaways

> **`ContextRefreshedEvent` fires on every `refresh()` call.** In Spring MVC apps there are TWO contexts: a root context and the `DispatcherServlet`'s child context — both fire `ContextRefreshedEvent`. If your listener is registered in both (common with `@ComponentScan`), it runs twice. Guard with an `AtomicBoolean` flag or check `event.getApplicationContext()` identity.

> **Don't do slow I/O inside `ContextRefreshedEvent`** if you're using Spring Boot — use `ApplicationReadyEvent` instead. `ContextRefreshedEvent` fires before the embedded server is bound to its port; long-running work delays the port-open, causing health checks to fail.

- `ContextClosedEvent` fires before `@PreDestroy` methods in Spring Boot; the reverse order applies in plain Spring MVC (manual `ctx.close()`). For resource cleanup, prefer `@PreDestroy` on the bean that owns the resource — it's more portable.
- `context.start()` and `context.stop()` are NOT the same as `run()` and `close()`. `start()` triggers `Lifecycle.start()` on beans implementing `Lifecycle`; `stop()` triggers `Lifecycle.stop()`. The context stays valid between `stop()` and `close()`.
- Register a JVM shutdown hook with `ctx.registerShutdownHook()` to fire `ContextClosedEvent` on SIGTERM/SIGINT in non-Boot apps.
- `ApplicationReadyEvent` fires only in Spring Boot apps; use `ContextRefreshedEvent` for framework-agnostic lifecycle hooks.
