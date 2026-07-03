---
card: spring-framework
gi: 102
slug: postconstruct-predestroy-jsr-250
title: "@PostConstruct / @PreDestroy (JSR-250)"
---

## 1. What it is

`@PostConstruct` and `@PreDestroy` are JSR-250 lifecycle annotations that mark methods to run at specific moments in a Spring bean's life:

- **`@PostConstruct`** — called once, immediately after the bean is constructed and all dependencies are injected. Use it for initialisation logic that needs injected fields to already be set.
- **`@PreDestroy`** — called once, just before the bean is removed from the container (context close). Use it for cleanup: closing connections, flushing buffers, releasing resources.

## 2. Why & when

Every long-lived bean sometimes needs to warm up (open a connection pool, load a cache, register a listener) and later clean up (drain queues, close sockets, flush writes). `@PostConstruct` / `@PreDestroy` are the cleanest way to express this:

| Mechanism | Notes |
|---|---|
| `@PostConstruct` / `@PreDestroy` | JSR-250, readable, no Spring coupling |
| `InitializingBean` / `DisposableBean` | Spring-specific interfaces |
| `@Bean(initMethod=…, destroyMethod=…)` | XML-style, good for third-party classes |

Prefer `@PostConstruct` / `@PreDestroy` for your own beans — they're standard, non-intrusive, and supported across Spring and Jakarta EE containers.

## 3. Core concept

`@PostConstruct` and `@PreDestroy` are processed by `CommonAnnotationBeanPostProcessor`:

1. **`@PostConstruct`** — fires after constructor, after setter injection, after `@Autowired` field injection. The bean is fully wired before this runs.
2. **`@PreDestroy`** — fires when `ctx.close()` is called (or the JVM shuts down if a `shutdown hook` is registered). Only fires for singleton-scoped beans; prototype beans are not tracked by the container after hand-off.

Method signature rules:
- Must be `void` return type.
- Must take no arguments.
- May be `private`, `protected`, or `public`.
- A bean can have **at most one** `@PostConstruct` and one `@PreDestroy` method (technically multiple are allowed, but order is not guaranteed between them).

## 4. Diagram

<svg viewBox="0 0 700 160" xmlns="http://www.w3.org/2000/svg">
  <rect x="10"  y="55" width="110" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="65" y="78" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">constructor()</text>
  <text x="65" y="93" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">bean created</text>

  <rect x="155" y="55" width="120" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="215" y="78" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Autowired</text>
  <text x="215" y="93" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">deps injected</text>

  <rect x="310" y="55" width="130" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="375" y="78" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">@PostConstruct</text>
  <text x="375" y="93" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">init logic runs</text>

  <rect x="475" y="55" width="110" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="530" y="78" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">in service</text>
  <text x="530" y="93" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">handles requests</text>

  <rect x="478" y="118" width="107" height="30" rx="7" fill="#1c2430" stroke="#ff7b72" stroke-width="1.5"/>
  <text x="531" y="137" fill="#ff7b72" font-size="11" text-anchor="middle" font-family="sans-serif">@PreDestroy</text>

  <line x1="122" y1="80" x2="152" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a102)"/>
  <line x1="277" y1="80" x2="307" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a102)"/>
  <line x1="442" y1="80" x2="472" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#b102)"/>
  <line x1="530" y1="105" x2="530" y2="116" stroke="#ff7b72" stroke-width="1.5" marker-end="url(#c102)"/>
  <defs>
    <marker id="a102" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="b102" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="c102" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#ff7b72"/></marker>
  </defs>
  <text x="350" y="22" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">@PostConstruct fires after full wiring · @PreDestroy fires on context close</text>
</svg>

`@PostConstruct` sits between "fully wired" and "in service"; `@PreDestroy` fires at context shutdown.

## 5. Runnable example

### Level 1 — Basic

A connection pool that initialises on `@PostConstruct` and drains cleanly on `@PreDestroy`.

```java
// LifecycleBasic.java
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.Component;
import java.util.ArrayDeque;
import java.util.Deque;

@Component
class ConnectionPool {
    private final Deque<String> pool = new ArrayDeque<>();

    @PostConstruct
    void init() {
        for (int i = 1; i <= 3; i++) pool.push("conn-" + i);
        System.out.println("Pool ready: " + pool);
    }

    public String acquire() {
        return pool.isEmpty() ? null : pool.pop();
    }

    public void release(String c) { pool.push(c); }

    @PreDestroy
    void shutdown() {
        System.out.println("Draining pool: " + pool);
        pool.clear();
        System.out.println("Pool closed.");
    }
}

@Configuration
@ComponentScan
class LcCfg {}

public class LifecycleBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(LcCfg.class);
        var pool = ctx.getBean(ConnectionPool.class);
        var c = pool.acquire();
        System.out.println("Using: " + c);
        pool.release(c);
        ctx.close();  // triggers @PreDestroy
    }
}
```

How to run: `java LifecycleBasic.java`

`@PostConstruct init()` runs after `ConnectionPool` is wired — the pool is pre-filled. `@PreDestroy shutdown()` runs when `ctx.close()` is called, draining cleanly.

### Level 2 — Intermediate

Add a dependent `OrderService` to show that by the time `@PostConstruct` runs, all `@Autowired` fields are already set.

```java
// LifecycleWired.java
import jakarta.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.util.ArrayList;
import java.util.List;

@Repository
class OrderRepository {
    private final List<String> orders = new ArrayList<>();
    public void save(String order) { orders.add(order); System.out.println("Saved: " + order); }
    public List<String> findAll() { return List.copyOf(orders); }
}

@Service
class OrderService {
    @Autowired
    private OrderRepository repo;          // injected before @PostConstruct

    private List<String> pendingOrders;    // set in @PostConstruct

    @PostConstruct
    void loadPending() {
        // repo is guaranteed non-null here
        System.out.println("@PostConstruct: repo = " + repo);
        pendingOrders = new ArrayList<>(List.of("order-101", "order-102"));
        System.out.println("Loaded pending: " + pendingOrders);
        // flush pending orders into the repository at startup
        pendingOrders.forEach(repo::save);
    }

    public void process(String newOrder) {
        repo.save(newOrder);
    }

    @PreDestroy
    void flush() {
        System.out.println("@PreDestroy: pending count = " + repo.findAll().size());
    }
}

@Configuration
@ComponentScan
class WiredCfg {}

public class LifecycleWired {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(WiredCfg.class);
        ctx.getBean(OrderService.class).process("order-200");
        ctx.close();
    }
}
```

How to run: `java LifecycleWired.java`

`repo` is injected before `loadPending()` runs. The `@PostConstruct` uses the injected `repo` to save pending orders at startup — something you can't do in the constructor because `repo` isn't set yet at that point.

### Level 3 — Advanced

A cache-warming service with ordered lifecycle: cache fills on `@PostConstruct`, stats logged on `@PreDestroy`, and error handling inside both lifecycle methods.

```java
// LifecycleAdvanced.java
import jakarta.annotation.*;
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Repository
class ProductRepository {
    private final Map<String, String> db = Map.of(
        "P001", "Widget",
        "P002", "Gadget",
        "P003", "Gizmo"
    );
    public Map<String, String> findAll() { return Collections.unmodifiableMap(db); }
}

@Service
class ProductCacheService {
    @Autowired
    private ProductRepository repo;

    private final Map<String, String> cache = new ConcurrentHashMap<>();
    private long loadedAt;
    private int hitCount = 0;

    @PostConstruct
    void warmCache() {
        System.out.println("[@PostConstruct] warming cache…");
        try {
            cache.putAll(repo.findAll());
            loadedAt = System.currentTimeMillis();
            System.out.println("[@PostConstruct] loaded " + cache.size() + " products into cache");
        } catch (Exception e) {
            System.err.println("[@PostConstruct] cache warm failed: " + e.getMessage());
            // non-fatal — service still starts, just without cache
        }
    }

    public Optional<String> find(String id) {
        var val = cache.get(id);
        if (val != null) hitCount++;
        return Optional.ofNullable(val);
    }

    @PreDestroy
    void logStats() {
        long uptime = System.currentTimeMillis() - loadedAt;
        System.out.printf("[@PreDestroy] cache stats — size=%d hits=%d uptime=%dms%n",
            cache.size(), hitCount, uptime);
        cache.clear();
        System.out.println("[@PreDestroy] cache cleared.");
    }
}

@Configuration
@ComponentScan
class AdvCfg {}

public class LifecycleAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AdvCfg.class);
        var svc = ctx.getBean(ProductCacheService.class);

        System.out.println("P001 → " + svc.find("P001").orElse("not found"));
        System.out.println("P999 → " + svc.find("P999").orElse("not found"));
        System.out.println("P002 → " + svc.find("P002").orElse("not found"));

        ctx.close();
    }
}
```

How to run: `java LifecycleAdvanced.java`

`@PostConstruct warmCache()` uses `repo` (fully injected) to pre-fill the concurrent map. `@PreDestroy logStats()` logs hit count and uptime before clearing. Error handling in `@PostConstruct` prevents a warm-up failure from crashing the context.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **`ProductRepository` instantiated** — no deps; `db` map populated.
2. **`ProductCacheService` instantiated** — default constructor called. `cache` and `hitCount` initialised. `repo` and `loadedAt` not yet set.
3. **`@Autowired` injection** — `ProductCacheService.repo` = the `ProductRepository` singleton.
4. **`@PostConstruct warmCache()` called** — `repo.findAll()` returns `{P001→Widget, P002→Gadget, P003→Gizmo}`. `cache.putAll(...)` fills the map. `loadedAt` recorded.
5. **`find("P001")`** — cache hit → `"Widget"`, `hitCount = 1`.
6. **`find("P999")`** — cache miss → `Optional.empty()` → `"not found"`. `hitCount` unchanged.
7. **`find("P002")`** — cache hit → `"Gadget"`, `hitCount = 2`.
8. **`ctx.close()`** — Spring calls `@PreDestroy logStats()`. Prints size=3, hits=2, uptime. Clears cache.

Expected output:
```
[@PostConstruct] warming cache…
[@PostConstruct] loaded 3 products into cache
P001 → Widget
P999 → not found
P002 → Gadget
[@PreDestroy] cache stats — size=3 hits=2 uptime=2ms
[@PreDestroy] cache cleared.
```

## 7. Gotchas & takeaways

> `@PostConstruct` runs **after** all injection is complete — but **before** the bean is returned to callers. You can safely use `@Autowired` fields inside it. Never attempt resource-dependent logic in the constructor — deps are not set yet.

> `@PreDestroy` only fires for **singleton** beans. If you scope a bean as `prototype`, Spring hands it off and forgets about it — `@PreDestroy` will never be called. Clean up prototype beans manually.

- Both annotations live in `jakarta.annotation` (Spring 6+) / `javax.annotation` (Spring 5). Add `jakarta.annotation-api` to the classpath if not already pulled in.
- `@PostConstruct` and the Spring `InitializingBean.afterPropertiesSet()` both fire at the same lifecycle point — don't use both unless you have good reason.
- Ordering between multiple `@PostConstruct` methods on the same bean is not defined — keep to one per bean.
- For prototype scope, use `@Bean(destroyMethod = "")` to opt out of auto-destroy entirely.
- `ctx.registerShutdownHook()` ensures `@PreDestroy` fires even when the JVM exits without an explicit `ctx.close()`.
