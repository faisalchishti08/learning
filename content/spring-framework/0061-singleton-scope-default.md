---
card: spring-framework
gi: 61
slug: singleton-scope-default
title: singleton scope (default)
---

## 1. What it is

**Singleton scope** is the default bean scope in Spring. A singleton-scoped bean is created **once** per `ApplicationContext` and the same instance is returned every time it is requested — whether by `getBean()`, `@Autowired`, or any other injection mechanism. There is one and only one object graph node for that bean definition within a container.

```java
@Component    // default scope = singleton
public class UserRepository {
    // Same instance injected everywhere in this ApplicationContext
}

// XML equivalent
// <bean id="userRepository" class="UserRepository" scope="singleton"/>
// (scope="singleton" is the default — you do not need to write it)
```

Singleton scope is independent of the GoF Singleton pattern: Spring's singleton is one instance *per container*, not one instance *per JVM*. Two `ApplicationContext` instances in the same JVM produce two separate `UserRepository` instances.

In one sentence: **A singleton bean is instantiated once per `ApplicationContext` — the same object is returned every time it is requested, making it suitable for stateless services, repositories, and shared infrastructure components.**

## 2. Why & when

Singleton is correct for:

- **Stateless services** — `UserService`, `OrderService`, `EmailService` — no mutable per-request state.
- **Repositories** — `UserRepository`, `ProductRepository` — share a `DataSource` singleton.
- **Infrastructure beans** — `DataSource`, `PlatformTransactionManager`, `RestTemplate` — expensive to create and safe to share.
- **Caches** — a single `CacheManager` instance shared across all consumers.

Singleton is **wrong** for:

- Objects with **per-request state** — use `prototype`, `request`, or `session` scope.
- Beans that hold **user-specific data** in fields — two concurrent requests will corrupt each other's data.

## 3. Core concept

```
ApplicationContext creates bean definitions, not instances.
Instance created: on first request (lazy) or at startup (eager, the default).

Singleton lifecycle:
  1. Container parses bean definition.
  2. Container creates the bean instance (once).
  3. Dependencies injected (constructor or setter).
  4. @PostConstruct called.
  5. Bean is ready — stored in the singleton cache.
  6. ALL calls to getBean("userRepo") → return the SAME object from cache.
  7. Context.close() → @PreDestroy called → instance discarded.

Contrast:
  getBean("userRepo") → [SINGLETON CACHE] → same object reference every time
  getBean("order")    → [PROTOTYPE] → new instance every call (next tutorial)
```

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Singleton scope: one instance created, same reference returned to all callers">
  <defs>
    <marker id="a61" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="650" height="198" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="330" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Singleton scope — one instance, shared by all consumers</text>

  <!-- Singleton bean -->
  <rect x="245" y="35" width="170" height="65" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">UserRepository</text>
  <text x="330" y="70" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">scope=singleton</text>
  <text x="330" y="83" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@0x3f4b6a2 (same address)</text>

  <!-- Three consumers -->
  <rect x="15"  y="140" width="140" height="45" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="85"  y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">UserService</text>
  <text x="85"  y="175" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@Autowired repo</text>

  <rect x="260" y="140" width="140" height="45" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="330" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">AdminController</text>
  <text x="330" y="175" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@Autowired repo</text>

  <rect x="505" y="140" width="140" height="45" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="575" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ReportService</text>
  <text x="575" y="175" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@Autowired repo</text>

  <!-- Arrows (same object ref to all) -->
  <line x1="245" y1="70" x2="130" y2="138" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a61)"/>
  <line x1="295" y1="100" x2="310" y2="138" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a61)"/>
  <line x1="414" y1="70" x2="530" y2="138" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a61)"/>

  <text x="155" y="113" fill="#6db33f" font-size="8" font-family="sans-serif">same ref</text>
  <text x="320" y="120" fill="#6db33f" font-size="8" font-family="sans-serif">same ref</text>
  <text x="455" y="105" fill="#6db33f" font-size="8" font-family="sans-serif">same ref</text>

  <text x="330" y="198" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">All three consumers receive the identical object reference. Mutating shared state would affect all of them.</text>
</svg>

All three consumers receive the same `UserRepository` instance. The container creates it once and stores it in the singleton cache; subsequent requests return the cached reference.

## 5. Runnable example

Scenario: a `ProductInventory` singleton that tracks stock levels. Multiple services share the same instance — stock changes made by one service are immediately visible to the other, because it is the same object.

### Level 1 — Basic

Prove that multiple calls to construct/retrieve a singleton return the same instance and share state.

```java
// SingletonScopeDemo.java — run with: java SingletonScopeDemo.java

public class SingletonScopeDemo {

    // ── singleton bean: one instance per "container" ─────────────────
    static class InventoryService {
        private static int instanceCount = 0;
        private final  int instanceId;
        private int stock = 100;

        InventoryService() {
            instanceId = ++instanceCount;
            System.out.println("  [BEAN CREATED] InventoryService #" + instanceId);
        }

        void reduce(int qty)  { stock -= qty; }
        int  getStock()       { return stock; }
        int  getInstanceId()  { return instanceId; }
    }

    // ── simulated singleton container: stores bean in a map ────────────
    static class Container {
        private InventoryService cachedInstance;

        InventoryService getInventoryService() {
            if (cachedInstance == null) {
                cachedInstance = new InventoryService();  // created ONCE
            }
            return cachedInstance;   // returns same instance every time
        }
    }

    public static void main(String[] args) {
        Container ctx = new Container();

        InventoryService a = ctx.getInventoryService();
        InventoryService b = ctx.getInventoryService();
        InventoryService c = ctx.getInventoryService();

        System.out.println("[IDENTITY] a==b: " + (a == b));
        System.out.println("[IDENTITY] b==c: " + (b == c));
        System.out.println("[IDENTITY] instanceIds: a=" + a.getInstanceId()
            + " b=" + b.getInstanceId() + " c=" + c.getInstanceId());

        System.out.println("\n[INITIAL STOCK] " + a.getStock());
        System.out.println("[REDUCE via a] -10");
        a.reduce(10);
        System.out.println("[STOCK via b]  " + b.getStock());   // b sees the change
        System.out.println("[STOCK via c]  " + c.getStock());   // c sees the change too
        System.out.println("(All show " + a.getStock() + " — same object)");
    }
}
```

How to run: `java SingletonScopeDemo.java`

The `Container` creates `InventoryService` only once — `[BEAN CREATED]` prints once no matter how many times `getInventoryService()` is called. `a == b == c` (same reference). A stock reduction via `a.reduce(10)` is immediately visible through `b` and `c` because they are the same object.

### Level 2 — Intermediate

A more realistic example: a singleton `AuditLog` shared across multiple services. Trace the call patterns to verify all services write to the same log.

```java
// SingletonScopeDemo2.java — run with: java SingletonScopeDemo2.java
import java.util.*;

public class SingletonScopeDemo2 {

    // ── singleton: shared audit log ────────────────────────────────────
    static class AuditLog {
        private static int instanceCount = 0;
        private final  int id;
        private final  List<String> entries = new ArrayList<>();

        AuditLog() {
            id = ++instanceCount;
            System.out.println("  [BEAN CREATED] AuditLog #" + id);
        }

        void log(String service, String action, String detail) {
            String entry = String.format("[%s] %s: %s", service, action, detail);
            entries.add(entry);
            System.out.println("  [AUDIT] " + entry);
        }

        void printAll() {
            System.out.println("  [LOG CONTENTS] " + entries.size() + " entries:");
            entries.forEach(e -> System.out.println("    " + e));
        }

        int getId() { return id; }
    }

    // ── two services sharing the SAME AuditLog singleton ──────────────
    static class UserService {
        private final AuditLog audit;
        UserService(AuditLog audit) {
            this.audit = audit;
            System.out.println("  [BEAN] UserService wired to AuditLog#" + audit.getId());
        }
        void createUser(String name) {
            System.out.println("[USER] Creating user: " + name);
            // ... business logic ...
            audit.log("UserService", "USER_CREATED", "name=" + name);
        }
        void deleteUser(String name) {
            System.out.println("[USER] Deleting user: " + name);
            audit.log("UserService", "USER_DELETED", "name=" + name);
        }
    }

    static class OrderService {
        private final AuditLog audit;
        OrderService(AuditLog audit) {
            this.audit = audit;
            System.out.println("  [BEAN] OrderService wired to AuditLog#" + audit.getId());
        }
        void placeOrder(String orderId, double amount) {
            System.out.println("[ORDER] Placing order " + orderId + " amount=" + amount);
            audit.log("OrderService", "ORDER_PLACED", "id=" + orderId + " amount=" + amount);
        }
        void cancelOrder(String orderId) {
            System.out.println("[ORDER] Cancelling order " + orderId);
            audit.log("OrderService", "ORDER_CANCELLED", "id=" + orderId);
        }
    }

    static void buildAndRun() {
        System.out.println("=== Container startup ===");
        AuditLog    auditLog     = new AuditLog();      // singleton: created ONCE
        UserService  userService  = new UserService(auditLog);   // SAME instance
        OrderService orderService = new OrderService(auditLog);  // SAME instance

        System.out.println("\n[SAME INSTANCE?] userService.audit == orderService.audit: "
            + (userService.audit == orderService.audit));  // true

        System.out.println("\n=== Business operations ===");
        userService.createUser("alice");
        orderService.placeOrder("ORD-001", 99.99);
        userService.createUser("bob");
        orderService.placeOrder("ORD-002", 49.50);
        userService.deleteUser("alice");
        orderService.cancelOrder("ORD-001");

        System.out.println("\n=== Unified audit trail (from ONE AuditLog instance) ===");
        auditLog.printAll();
    }

    public static void main(String[] args) {
        buildAndRun();
    }
}
```

How to run: `java SingletonScopeDemo2.java`

`AuditLog` is created once and passed to both services. Both write to the same `entries` list. The final `printAll()` shows a unified audit trail with events from both services — proving they share the singleton. `instanceCount` stays at 1 throughout.

### Level 3 — Advanced

Singleton + thread-safety: a shared `RequestCounter` singleton that must handle concurrent access safely. Demonstrates the critical concern for stateful singletons.

```java
// SingletonScopeDemo3.java — run with: java SingletonScopeDemo3.java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class SingletonScopeDemo3 {

    // ── singleton: must be thread-safe because it is shared ───────────
    static class RequestCounter {
        private static int instanceCount = 0;
        private final  int id;

        // Atomic counters — thread-safe shared state in a singleton
        private final AtomicLong    totalRequests  = new AtomicLong();
        private final AtomicLong    failedRequests = new AtomicLong();
        private final ConcurrentMap<String, AtomicLong> perEndpoint = new ConcurrentHashMap<>();

        RequestCounter() {
            id = ++instanceCount;
            System.out.println("  [BEAN CREATED] RequestCounter #" + id);
        }

        void record(String endpoint, boolean success) {
            totalRequests.incrementAndGet();
            if (!success) failedRequests.incrementAndGet();
            perEndpoint.computeIfAbsent(endpoint, k -> new AtomicLong()).incrementAndGet();
        }

        void printStats() {
            System.out.println("  [STATS] total=" + totalRequests
                + " failed=" + failedRequests
                + " errorRate=" + String.format("%.1f%%",
                    totalRequests.get() == 0 ? 0.0
                    : 100.0 * failedRequests.get() / totalRequests.get()));
            System.out.println("  [PER ENDPOINT]");
            perEndpoint.entrySet().stream()
                .sorted(Map.Entry.<String, AtomicLong>comparingByValue(
                    Comparator.comparingLong(AtomicLong::get)).reversed())
                .forEach(e -> System.out.println("    " + e.getKey() + " = " + e.getValue()));
        }

        int getId() { return id; }
    }

    // ── two handler beans sharing the SAME counter singleton ──────────
    static class ApiGateway {
        private final RequestCounter counter;
        ApiGateway(RequestCounter counter) {
            this.counter = counter;
            System.out.println("  [BEAN] ApiGateway using counter#" + counter.getId());
        }
        void handle(String endpoint, boolean ok) {
            counter.record(endpoint, ok);
        }
    }

    static class WebhookHandler {
        private final RequestCounter counter;
        WebhookHandler(RequestCounter counter) {
            this.counter = counter;
            System.out.println("  [BEAN] WebhookHandler using counter#" + counter.getId());
        }
        void receive(String event, boolean ok) {
            counter.record("/webhooks/" + event, ok);
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Container startup ===");
        RequestCounter counter = new RequestCounter();       // singleton
        ApiGateway     gateway = new ApiGateway(counter);    // shares counter
        WebhookHandler webhook = new WebhookHandler(counter); // shares SAME counter

        System.out.println("[SAME?] gateway.counter == webhook.counter: "
            + (gateway.counter == webhook.counter));

        System.out.println("\n=== Concurrent traffic simulation (5 threads) ===");
        ExecutorService pool = Executors.newFixedThreadPool(5);
        List<Future<?>> futures = new ArrayList<>();
        Random rng = new Random(42);

        String[] endpoints = {"/users", "/orders", "/products", "/auth"};
        for (int i = 0; i < 50; i++) {
            final int req = i;
            futures.add(pool.submit(() -> {
                String ep  = endpoints[req % endpoints.length];
                boolean ok = rng.nextDouble() > 0.1;  // 10% error rate
                if (req % 7 == 0) {
                    webhook.receive("order.created", ok);
                } else {
                    gateway.handle(ep, ok);
                }
            }));
        }
        for (Future<?> f : futures) f.get();
        pool.shutdown();

        System.out.println("\n=== Stats from singleton counter ===");
        counter.printStats();

        System.out.println("\n[THREAD SAFETY] Counter is AtomicLong — safe for concurrent access.");
        System.out.println("[DANGER]       If counter fields were plain int, concurrent ++ would lose updates.");
    }
}
```

How to run: `java SingletonScopeDemo3.java`

50 concurrent tasks split between `ApiGateway` and `WebhookHandler` — all recording to the same `RequestCounter` singleton. `AtomicLong.incrementAndGet()` is thread-safe; a plain `int ++` would lose increments under concurrency. The stats show all 50 requests counted by the one shared instance. This is the critical point: **a singleton that holds mutable state must use thread-safe data structures** because it is shared across all concurrent callers.

## 6. Walkthrough

**Container startup and lifecycle:**

```
Step 1: buildContainer() starts
  → new RequestCounter()
      instanceCount++ → id = 1
      [BEAN CREATED] RequestCounter #1
  → new ApiGateway(counter)
      [BEAN] ApiGateway using counter#1
  → new WebhookHandler(counter)
      [BEAN] WebhookHandler using counter#1
```

**Concurrent requests — thread-safe increment:**

```
Thread-1: gateway.handle("/users", true)
  → counter.record("/users", true)
  → totalRequests.incrementAndGet()   → 1 (atomic)
  → perEndpoint.compute("/users")      → AtomicLong(1)

Thread-2: webhook.receive("order.created", false)
  → counter.record("/webhooks/order.created", false)
  → totalRequests.incrementAndGet()   → 2 (atomic, no data race)
  → failedRequests.incrementAndGet()  → 1
  → perEndpoint.compute("/webhooks/order.created") → AtomicLong(1)

[50 tasks later]
counter.printStats():
  total=50 failed≈5 errorRate≈10.0%
  /orders             = 15
  /users              = 13
  /products           = 12
  /auth               = 3
  /webhooks/order.created = 7
```

**Key insight — same instance through the chain:**

```
gateway.counter  == RequestCounter#1  (id=1)
webhook.counter  == RequestCounter#1  (id=1)
counter          == RequestCounter#1  (id=1)
All three references point to the same heap object.
```

## 7. Gotchas & takeaways

> **Singletons with mutable instance fields are a concurrency hazard.** If a singleton stores per-request data in a field (e.g., `private String currentUser`), two concurrent requests will corrupt each other's data. Keep singletons **stateless** or use thread-safe types (`AtomicLong`, `ConcurrentHashMap`).

> **Spring's singleton is per-container, not per-JVM.** If you load two `ApplicationContext` instances (common in tests), you get two independent singleton instances. The GoF Singleton pattern prevents this; Spring's scope does not.

- A singleton bean is eagerly created at context refresh by default. Add `@Lazy` to defer creation until first use — but be careful: lazy singletons will throw at first use, not at startup, if their dependencies are missing.
- Prototype beans injected into a singleton are only resolved once (at singleton creation time). The singleton holds a frozen reference to the first prototype instance — subsequent calls do not get a new prototype. Use `ApplicationContext.getBean()`, `@Lookup`, or `ObjectProvider<T>` to get a fresh prototype each time.
- `DisposableBean.destroy()` and `@PreDestroy` are called on singletons at context close — but NOT on prototype beans (Spring hands them off after creation).
- Thread-local state (e.g., `ThreadLocal<SecurityContext>`) is fine in a singleton — each thread has its own copy of the thread-local variable.
