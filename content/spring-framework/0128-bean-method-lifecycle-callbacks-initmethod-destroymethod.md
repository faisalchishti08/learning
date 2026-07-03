---
card: spring-framework
gi: 128
slug: bean-method-lifecycle-callbacks-initmethod-destroymethod
title: "Bean method lifecycle callbacks (initMethod/destroyMethod)"
---

## 1. What it is

`@Bean(initMethod = "open", destroyMethod = "close")` tells Spring which methods to call on the returned object after construction and before destruction. They are the `@Bean`-annotation equivalent of `@PostConstruct` / `@PreDestroy` — but useful for third-party classes you can't annotate, or when you want to express lifecycle in the config class rather than in the bean class.

```java
@Bean(initMethod = "connect", destroyMethod = "disconnect")
public ConnectionPool pool() {
    return new HikariConnectionPool(config());
}
```

Spring calls `pool.connect()` after constructing and injecting the bean, and `pool.disconnect()` when the context closes.

## 2. Why & when

Use `initMethod` / `destroyMethod` when:

- The bean class is from a **third-party library** you cannot modify — no way to add `@PostConstruct`.
- You want lifecycle configuration to live in the **config class**, not the bean class (separation of concerns).
- You need different lifecycle methods for different profiles/environments (one config class uses `init`, another uses `initForTesting`).
- The class already has well-known lifecycle method names (`start`/`stop`, `open`/`close`, `init`/`destroy`) you want Spring to honour.

`destroyMethod` has a special default: `""` (empty string) means auto-detect — Spring automatically calls `close()` or `shutdown()` if the bean declares either method. Set `destroyMethod = ""` explicitly to **disable** auto-detection.

## 3. Core concept

Execution order for a full lifecycle:

1. Constructor
2. Dependency injection (`@Autowired` fields / setters)
3. `BeanPostProcessor.postProcessBeforeInitialization()`
4. `@PostConstruct` method (if present)
5. `InitializingBean.afterPropertiesSet()` (if implemented)
6. **`initMethod`** (if specified in `@Bean`)
7. Bean ready for use
8. Context close triggered
9. `@PreDestroy` method (if present)
10. `DisposableBean.destroy()` (if implemented)
11. **`destroyMethod`** (if specified in `@Bean`)

The `initMethod` is called after ALL other init mechanisms — it's the last step in initialization.

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <!-- Lifecycle timeline -->
  <rect x="10"  y="60" width="95" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="57"  y="82" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">1. new()</text>
  <text x="57"  y="96" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">constructor</text>

  <rect x="120" y="60" width="95" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="167" y="82" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">2. inject</text>
  <text x="167" y="96" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">@Autowired</text>

  <rect x="230" y="60" width="95" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="277" y="82" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">3. @Post...</text>
  <text x="277" y="96" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Construct</text>

  <rect x="340" y="50" width="115" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="397" y="75" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">4. initMethod</text>
  <text x="397" y="90" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">@Bean(initMethod)</text>
  <text x="397" y="108" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">bean ready</text>

  <rect x="470" y="60" width="95" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="517" y="82" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">5. @Pre...</text>
  <text x="517" y="96" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Destroy</text>

  <rect x="580" y="50" width="115" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="637" y="75" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">6. destroyMethod</text>
  <text x="637" y="92" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">@Bean(destroy...</text>
  <text x="637" y="108" fill="#79c0ff" font-size="9"  text-anchor="middle" font-family="sans-serif">context close</text>

  <line x1="107" y1="85" x2="117" y2="85" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a128)"/>
  <line x1="217" y1="85" x2="227" y2="85" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a128)"/>
  <line x1="327" y1="85" x2="337" y2="85" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a128)"/>
  <line x1="457" y1="85" x2="467" y2="85" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b128)"/>
  <line x1="567" y1="85" x2="577" y2="85" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a128)"/>
  <defs>
    <marker id="a128" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b128" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="185" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">initMethod runs last in init sequence; destroyMethod runs last in shutdown sequence</text>
</svg>

`initMethod` fires after `@PostConstruct`; `destroyMethod` fires after `@PreDestroy` — they are the final hooks in each lifecycle phase.

## 5. Runnable example

### Level 1 — Basic

A third-party `CacheStore` class with `open()` / `close()` methods wired via `@Bean(initMethod/destroyMethod)`.

```java
// LifecycleBasic.java
import org.springframework.context.annotation.*;

// Third-party class — cannot modify
class CacheStore {
    private boolean open = false;

    public void open() {
        open = true;
        System.out.println("[CacheStore] opened — ready to serve");
    }

    public String get(String key) {
        if (!open) throw new IllegalStateException("Cache not open");
        return "[cached] " + key;
    }

    public void close() {
        open = false;
        System.out.println("[CacheStore] closed — resources released");
    }
}

@Configuration
class CacheCfg {
    @Bean(initMethod = "open", destroyMethod = "close")
    public CacheStore cacheStore() {
        System.out.println("[Config] constructing CacheStore");
        return new CacheStore();
    }
}

public class LifecycleBasic {
    public static void main(String[] args) {
        System.out.println("=== Context starting ===");
        var ctx = new AnnotationConfigApplicationContext(CacheCfg.class);

        System.out.println("\n=== Using cache ===");
        System.out.println(ctx.getBean(CacheStore.class).get("user:1"));

        System.out.println("\n=== Context closing ===");
        ctx.close();
    }
}
```

How to run: `java LifecycleBasic.java`

`open()` is called automatically after construction. `close()` is called automatically on context shutdown. The bean is fully initialised before the first `getBean()` call.

### Level 2 — Intermediate

Mix `initMethod` with `@PostConstruct` — show execution order and use `destroyMethod = ""` to disable auto-detection.

```java
// LifecycleOrder.java
import jakarta.annotation.*;
import org.springframework.context.annotation.*;

class ConnectionPool {
    private int connections = 0;

    // Would be auto-detected as destroyMethod if destroyMethod = "" not set
    public void shutdown() {
        System.out.println("[Pool] shutdown(): releasing " + connections + " connections");
        connections = 0;
    }

    @PostConstruct
    public void postConstruct() {
        System.out.println("[Pool] @PostConstruct: validating config");
    }

    public void init() {
        connections = 10;
        System.out.println("[Pool] init(): pool of " + connections + " connections ready");
    }

    @PreDestroy
    public void preDestroy() {
        System.out.println("[Pool] @PreDestroy: draining active queries");
    }

    public String borrow() { return "conn-" + (connections--); }
}

@Configuration
class PoolCfg {
    // initMethod fires AFTER @PostConstruct
    // destroyMethod="" disables auto-detection of shutdown()
    @Bean(initMethod = "init", destroyMethod = "")
    public ConnectionPool connectionPool() {
        System.out.println("[Config] constructing ConnectionPool");
        return new ConnectionPool();
    }
}

public class LifecycleOrder {
    public static void main(String[] args) {
        System.out.println("=== Startup ===");
        var ctx = new AnnotationConfigApplicationContext(PoolCfg.class);

        System.out.println("\n=== Using pool ===");
        var pool = ctx.getBean(ConnectionPool.class);
        System.out.println("Borrowed: " + pool.borrow());
        System.out.println("Borrowed: " + pool.borrow());

        System.out.println("\n=== Shutdown ===");
        ctx.close();
        // shutdown() is NOT called because destroyMethod="" disabled auto-detection
        System.out.println("Pool.shutdown() was NOT auto-called (destroyMethod disabled)");
    }
}
```

How to run: `java LifecycleOrder.java`

Startup prints: `constructing` → `@PostConstruct: validating config` → `init(): pool...`. Shutdown prints: `@PreDestroy: draining...` (but NOT `shutdown()` because `destroyMethod = ""` prevents it).

### Level 3 — Advanced

Multiple beans with different lifecycle methods, `destroyMethod` auto-detection, and a managed resource that tracks its state.

```java
// LifecycleAdvanced.java
import jakarta.annotation.*;
import org.springframework.context.annotation.*;
import java.util.*;

class EventBus {
    private final List<String> handlers = new ArrayList<>();
    private boolean running = false;

    public void start() {
        running = true;
        System.out.println("[EventBus] started — accepting events");
    }

    public void subscribe(String handler) {
        handlers.add(handler);
        System.out.println("[EventBus] subscribed: " + handler);
    }

    public void publish(String event) {
        if (!running) throw new IllegalStateException("EventBus not running");
        handlers.forEach(h -> System.out.println("[" + h + "] handling: " + event));
    }

    public void stop() {
        running = false;
        System.out.println("[EventBus] stopped — handlers: " + handlers.size() + " cleaned up");
        handlers.clear();
    }
}

class MetricsCollector {
    private final Map<String,Long> counts = new LinkedHashMap<>();

    public void initialize() {
        System.out.println("[Metrics] initializing counters");
        counts.put("events", 0L);
        counts.put("errors", 0L);
    }

    public void increment(String metric) {
        counts.merge(metric, 1L, Long::sum);
    }

    // Spring auto-detects close() as destroyMethod when destroyMethod not set explicitly
    public void close() {
        System.out.println("[Metrics] closing — final counts: " + counts);
    }
}

class AppOrchestrator {
    @org.springframework.beans.factory.annotation.Autowired EventBus bus;
    @org.springframework.beans.factory.annotation.Autowired MetricsCollector metrics;

    @PostConstruct
    public void setup() {
        bus.subscribe("AuditHandler");
        bus.subscribe("LogHandler");
        System.out.println("[Orchestrator] setup complete");
    }

    public void run(String event) {
        metrics.increment("events");
        bus.publish(event);
    }

    @PreDestroy
    public void teardown() {
        System.out.println("[Orchestrator] teardown — events=" + "recorded");
    }
}

@Configuration
class AppCfg {
    @Bean(initMethod = "start", destroyMethod = "stop")
    public EventBus eventBus() { return new EventBus(); }

    // destroyMethod auto-detected: close() exists → called on context close
    @Bean(initMethod = "initialize")
    public MetricsCollector metricsCollector() { return new MetricsCollector(); }

    @Bean public AppOrchestrator appOrchestrator() { return new AppOrchestrator(); }
}

public class LifecycleAdvanced {
    public static void main(String[] args) {
        System.out.println("=== Startup ===");
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);

        System.out.println("\n=== Events ===");
        var app = ctx.getBean(AppOrchestrator.class);
        app.run("user.login");
        app.run("order.placed");
        app.run("payment.received");

        System.out.println("\n=== Shutdown ===");
        ctx.close();
    }
}
```

How to run: `java LifecycleAdvanced.java`

`EventBus` uses explicit `start`/`stop`. `MetricsCollector` uses explicit `initialize` for init and auto-detected `close()` for destroy. `AppOrchestrator` uses `@PostConstruct` / `@PreDestroy`. All three lifecycle layers cooperate.

## 6. Walkthrough

Startup sequence for Level 3:

1. **`MetricsCollector` constructed** → `initialize()` called → counters set up.
2. **`EventBus` constructed** → `start()` called → `running = true`.
3. **`AppOrchestrator` constructed** → `@Autowired` injection → `@PostConstruct setup()` → subscribes two handlers.
4. **`run("user.login")`** → `metrics.increment("events")` → `bus.publish("user.login")` → both handlers invoked.

Shutdown sequence:
5. **`AppOrchestrator.@PreDestroy teardown()`** called first.
6. **`MetricsCollector.close()`** called — prints final counts.
7. **`EventBus.stop()`** called — clears handlers.

Expected output (abbreviated):
```
=== Startup ===
[Metrics] initializing counters
[EventBus] started — accepting events
[EventBus] subscribed: AuditHandler
[EventBus] subscribed: LogHandler
[Orchestrator] setup complete

=== Events ===
[AuditHandler] handling: user.login
[LogHandler] handling: user.login
...

=== Shutdown ===
[Orchestrator] teardown — events=recorded
[Metrics] closing — final counts: {events=3, errors=0}
[EventBus] stopped — handlers: 0 cleaned up
```

## 7. Gotchas & takeaways

> `destroyMethod` defaults to `""` (empty string), which enables Spring's auto-detection of a `close()` or `shutdown()` method. If the third-party class you're wrapping happens to have such a method that should NOT be called on shutdown (e.g., it shuts down a shared system resource), set `destroyMethod = ""` explicitly to disable auto-detection.

> `initMethod` and `destroyMethod` must be **no-argument** methods. Spring uses reflection and throws `IllegalStateException` at startup if it can't find a matching no-arg method with the given name.

- The `initMethod` fires after `@PostConstruct` and `InitializingBean.afterPropertiesSet()`. If you use all three, they all run — in that order.
- `destroyMethod` does NOT fire for prototype-scoped beans. Spring doesn't track prototypes after creation.
- For the same class always initialized the same way, prefer `@PostConstruct` in the class itself. Use `@Bean(initMethod=...)` when the class is from a library or when different configs need different init methods.
- In Spring Boot, many auto-configured beans (e.g., `DataSource`) use `destroyMethod` internally to handle connection pool shutdown correctly.
