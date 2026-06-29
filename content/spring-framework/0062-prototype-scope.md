---
card: spring-framework
gi: 62
slug: prototype-scope
title: prototype scope
---

## 1. What it is

**Prototype scope** tells Spring to create a **new bean instance every time** one is requested — either via `ApplicationContext.getBean()`, an `@Autowired ObjectProvider<T>`, or a `@Lookup` method. Unlike singleton (one instance per container), prototype gives each caller its own independent copy.

```java
@Component
@Scope("prototype")   // or @Scope(ConfigurableBeanFactory.SCOPE_PROTOTYPE)
public class ShoppingCart {
    private final List<Item> items = new ArrayList<>();
    // Must be prototype — each user session needs their own cart
}

// XML equivalent
// <bean id="shoppingCart" class="ShoppingCart" scope="prototype"/>
```

Spring creates the bean and injects its dependencies, but does **not** manage the prototype's lifecycle after hand-off — `@PreDestroy` is never called by the container.

In one sentence: **A prototype-scoped bean is created fresh on every request, giving each caller their own independent instance with independent state — suitable for stateful or non-thread-safe objects.**

## 2. Why & when

Use prototype when:

- **Per-request state** must be isolated — a `ShoppingCart`, a `CommandBuilder`, a parser that accumulates results.
- The bean is **not thread-safe** and cannot be shared concurrently.
- Each caller needs its own **mutable scratch-pad** object.
- You're building **domain objects with Spring-managed lifecycle** (e.g., `@Lookup` method injection into a service bean).

Do NOT use prototype for:

- Stateless services (`UserService`, `OrderService`) — waste resources creating new instances for no reason.
- Infrastructure beans (`DataSource`, `TransactionManager`) — creating a new pool per call is catastrophic.

## 3. Core concept

```
Singleton:
  ctx.getBean("svc") → always return same cached instance

Prototype:
  ctx.getBean("cart") → new ShoppingCart() → inject deps → return
  ctx.getBean("cart") → new ShoppingCart() → inject deps → return
  (never the same object twice)

Lifecycle difference:
  Singleton  → container manages full lifecycle: create → use → @PreDestroy
  Prototype  → container creates only: create → inject → hand off
               caller is responsible for cleanup

Injecting prototype into singleton (the scoping problem):
  @Autowired ShoppingCart cart;  // cart injected ONCE at singleton creation
  // → the prototype is frozen; subsequent calls reuse the SAME prototype instance
  // Fix: @Lookup, ObjectProvider<T>, or ApplicationContext.getBean()
```

## 4. Diagram

<svg viewBox="0 0 660 215" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Prototype scope: each getBean call returns a new instance">
  <defs>
    <marker id="a62" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b62" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <rect x="5" y="5" width="650" height="202" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="330" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Prototype scope — new instance per request</text>

  <!-- Container factory -->
  <rect x="235" y="30" width="190" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="330" y="53" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Spring Container (prototype factory)</text>

  <!-- Three arrows down — new instances -->
  <line x1="280" y1="70" x2="130" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a62)"/>
  <line x1="330" y1="70" x2="330" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a62)"/>
  <line x1="380" y1="70" x2="530" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a62)"/>
  <text x="172" y="96" fill="#6db33f" font-size="8" font-family="sans-serif">new()</text>
  <text x="335" y="96" fill="#6db33f" font-size="8" font-family="sans-serif">new()</text>
  <text x="448" y="96" fill="#6db33f" font-size="8" font-family="sans-serif">new()</text>

  <!-- Three separate instances -->
  <rect x="20"  y="115" width="220" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="135" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">ShoppingCart #1  @0x1a2b3c</text>
  <text x="130" y="151" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">items=[] — Alice's cart</text>

  <rect x="245" y="115" width="170" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="135" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">ShoppingCart #2  @0x4d5e6f</text>
  <text x="330" y="151" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">items=[] — Bob's cart</text>

  <rect x="420" y="115" width="225" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="532" y="135" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">ShoppingCart #3  @0x7a8b9c</text>
  <text x="532" y="151" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">items=[] — Carol's cart</text>

  <!-- No lifecycle management -->
  <text x="330" y="185" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Container hands off each instance — @PreDestroy NOT called. Caller responsible for cleanup.</text>
  <text x="330" y="198" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Three different heap addresses — three independent state machines.</text>
</svg>

Each `getBean()` call produces a different object at a different heap address. State changes in Cart #1 have no effect on Carts #2 or #3.

## 5. Runnable example

Scenario: a `QueryBuilder` that accumulates SQL clauses. It must be prototype-scoped because each query is built independently and sharing state across concurrent callers would corrupt queries.

### Level 1 — Basic

Show that each `getBean("queryBuilder")` call returns a distinct instance with independent state.

```java
// PrototypeScopeDemo.java — run with: java PrototypeScopeDemo.java

public class PrototypeScopeDemo {

    // ── prototype bean: stateful, cannot be shared ─────────────────────
    static class QueryBuilder {
        private static int instanceCount = 0;
        private final  int id;
        private String table;
        private final java.util.List<String> conditions = new java.util.ArrayList<>();
        private final java.util.List<String> columns    = new java.util.ArrayList<>();

        QueryBuilder() {
            id = ++instanceCount;
            System.out.println("  [PROTOTYPE CREATED] QueryBuilder #" + id);
        }

        QueryBuilder from(String t)   { table = t;       return this; }
        QueryBuilder select(String c) { columns.add(c);  return this; }
        QueryBuilder where(String w)  { conditions.add(w); return this; }

        String build() {
            String cols = columns.isEmpty() ? "*" : String.join(", ", columns);
            String sql  = "SELECT " + cols + " FROM " + table;
            if (!conditions.isEmpty())
                sql += " WHERE " + String.join(" AND ", conditions);
            return sql;
        }
        int getId() { return id; }
    }

    // ── container: always creates a new instance ────────────────────────
    static class Container {
        QueryBuilder newQueryBuilder() { return new QueryBuilder(); }  // prototype factory
    }

    public static void main(String[] args) {
        Container ctx = new Container();

        // Each call gets a DIFFERENT instance
        QueryBuilder q1 = ctx.newQueryBuilder();
        QueryBuilder q2 = ctx.newQueryBuilder();
        QueryBuilder q3 = ctx.newQueryBuilder();

        System.out.println("[IDENTITY] q1==q2: " + (q1 == q2));
        System.out.println("[IDENTITY] q2==q3: " + (q2 == q3));
        System.out.println("[IDS]      q1=" + q1.getId() + " q2=" + q2.getId() + " q3=" + q3.getId());
        System.out.println();

        // Each builder has its own independent state
        q1.from("users").select("id").select("name").where("active = true");
        q2.from("orders").select("*").where("status = 'PENDING'").where("amount > 100");
        q3.from("products").select("id").select("sku").select("price");

        System.out.println("[Q1] " + q1.build());
        System.out.println("[Q2] " + q2.build());
        System.out.println("[Q3] " + q3.build());

        // q1's conditions have no effect on q2 — independent state
        System.out.println("\n[ISOLATION] q1 conditions: " + q1.conditions);
        System.out.println("[ISOLATION] q2 conditions: " + q2.conditions);
    }
}
```

How to run: `java PrototypeScopeDemo.java`

`[PROTOTYPE CREATED]` prints three times — one per `newQueryBuilder()` call. `q1 == q2` is `false` (different references). Each builder accumulates its own clauses independently. `q1.conditions` has no overlap with `q2.conditions`.

### Level 2 — Intermediate

Inject a prototype into a singleton via `ObjectProvider<T>` — the correct pattern to avoid the scope-mismatch problem.

```java
// PrototypeScopeDemo2.java — run with: java PrototypeScopeDemo2.java
import java.util.*;
import java.util.function.Supplier;

public class PrototypeScopeDemo2 {

    static class ReportBuilder {
        private static int count = 0;
        final int id;
        private String title;
        private final List<String> rows = new ArrayList<>();

        ReportBuilder() {
            id = ++count;
            System.out.println("  [PROTO] ReportBuilder #" + id + " created");
        }

        ReportBuilder title(String t)       { this.title = t; return this; }
        ReportBuilder addRow(String r)      { rows.add(r); return this; }

        String build() {
            StringBuilder sb = new StringBuilder("=== " + title + " ===\n");
            rows.forEach(r -> sb.append("  ").append(r).append("\n"));
            return sb.toString().trim();
        }
    }

    // ── singleton service: uses Supplier<T> as ObjectProvider equivalent ─
    static class ReportService {
        private final Supplier<ReportBuilder> builderFactory;  // prototype factory
        private static int instanceCount = 0;
        final int id;

        ReportService(Supplier<ReportBuilder> builderFactory) {
            id = ++instanceCount;
            this.builderFactory = builderFactory;
            System.out.println("  [SINGLETON] ReportService #" + id + " created");
        }

        // Each call creates a FRESH prototype via the factory
        String generateUserReport(List<String> users) {
            ReportBuilder builder = builderFactory.get();  // NEW prototype every call
            builder.title("User Report");
            users.forEach(u -> builder.addRow("User: " + u));
            return builder.build();
        }

        String generateOrderReport(List<String> orders) {
            ReportBuilder builder = builderFactory.get();  // DIFFERENT new instance
            builder.title("Order Report");
            orders.forEach(o -> builder.addRow("Order: " + o));
            return builder.build();
        }
    }

    public static void main(String[] args) {
        // Container: ReportService is singleton, ReportBuilder is prototype
        ReportService svc = new ReportService(ReportBuilder::new);  // factory = ObjectProvider

        System.out.println("[SINGLETON] ReportService id=" + svc.id);
        System.out.println();

        System.out.println("=== First user report ===");
        System.out.println(svc.generateUserReport(List.of("alice", "bob", "carol")));

        System.out.println("\n=== Order report ===");
        System.out.println(svc.generateOrderReport(List.of("ORD-001", "ORD-002")));

        System.out.println("\n=== Second user report (new prototype) ===");
        System.out.println(svc.generateUserReport(List.of("dave", "eve")));

        System.out.println("\n[NOTE] ReportService created ONCE; ReportBuilder created "
            + ReportBuilder.count + " times (one per report)");
    }
}
```

How to run: `java PrototypeScopeDemo2.java`

`ReportService` is a singleton (created once). Each call to `generateUserReport()` or `generateOrderReport()` calls `builderFactory.get()` — equivalent to `ObjectProvider<ReportBuilder>.getObject()` — which produces a fresh `ReportBuilder`. Three reports → three `ReportBuilder` instances. `ReportService` itself is constructed only once.

### Level 3 — Advanced

`@Lookup` pattern equivalent: a singleton service with a factory method that delegates to the container to get a fresh prototype. Includes lifecycle management (prototype cleanup) by the caller.

```java
// PrototypeScopeDemo3.java — run with: java PrototypeScopeDemo3.java
import java.util.*;
import java.util.function.Supplier;

public class PrototypeScopeDemo3 {

    // ── Closeable prototype: caller must close it ─────────────────────
    static class DatabaseTransaction implements AutoCloseable {
        private static int count = 0;
        final int id;
        private boolean committed = false;
        private boolean closed    = false;
        private final List<String> ops = new ArrayList<>();

        DatabaseTransaction() {
            id = ++count;
            System.out.println("    [TX#" + id + "] created (BEGIN)");
        }

        void execute(String sql) {
            if (closed) throw new IllegalStateException("TX#" + id + " is closed");
            ops.add(sql);
            System.out.println("    [TX#" + id + "] " + sql);
        }

        void commit() {
            committed = true;
            System.out.println("    [TX#" + id + "] COMMIT (" + ops.size() + " ops)");
        }

        void rollback() {
            System.out.println("    [TX#" + id + "] ROLLBACK");
        }

        @Override
        public void close() {
            if (!committed) rollback();
            closed = true;
            System.out.println("    [TX#" + id + "] closed (container does NOT do this for prototypes)");
        }
    }

    // ── singleton service: uses @Lookup-style factory ──────────────────
    static class OrderService {
        private final Supplier<DatabaseTransaction> txFactory;  // @Lookup equivalent

        OrderService(Supplier<DatabaseTransaction> txFactory) {
            this.txFactory = txFactory;
            System.out.println("  [SINGLETON] OrderService created");
        }

        // @Lookup public DatabaseTransaction createTransaction() { return null; }
        // Spring overrides this at runtime — our Supplier simulates it

        void placeOrder(String orderId, double amount) {
            System.out.println("[ORDER] Placing " + orderId + " amount=" + amount);
            try (DatabaseTransaction tx = txFactory.get()) {  // fresh prototype
                tx.execute("INSERT INTO orders VALUES ('" + orderId + "', " + amount + ")");
                tx.execute("UPDATE inventory SET reserved = reserved + 1");
                tx.execute("INSERT INTO audit_log VALUES ('" + orderId + "', NOW())");
                tx.commit();
            }
        }

        void cancelOrder(String orderId) {
            System.out.println("[ORDER] Cancelling " + orderId);
            try (DatabaseTransaction tx = txFactory.get()) {  // different fresh prototype
                tx.execute("UPDATE orders SET status='CANCELLED' WHERE id='" + orderId + "'");
                tx.execute("UPDATE inventory SET reserved = reserved - 1");
                // simulate rollback by not committing
                throw new RuntimeException("Simulated constraint violation");
            } catch (RuntimeException e) {
                System.out.println("[ORDER] Failed: " + e.getMessage() + " (tx rolled back)");
            }
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Container startup ===");
        // Prototype factory: each call → new DatabaseTransaction (auto-closed by caller)
        OrderService svc = new OrderService(DatabaseTransaction::new);
        System.out.println();

        System.out.println("=== Place two orders (each gets its own TX prototype) ===");
        svc.placeOrder("ORD-001", 299.99);
        System.out.println();
        svc.placeOrder("ORD-002", 49.50);
        System.out.println();

        System.out.println("=== Cancel (TX rolled back by caller, not container) ===");
        svc.cancelOrder("ORD-001");
        System.out.println();

        System.out.println("[SUMMARY] DatabaseTransaction instances created: " + DatabaseTransaction.count);
        System.out.println("[SUMMARY] OrderService instances: 1 (singleton)");
        System.out.println("[KEY LESSON] Each TX prototype closed by 'caller' (try-with-resources).");
        System.out.println("[KEY LESSON] Spring does NOT call close/@PreDestroy on prototypes.");
    }
}
```

How to run: `java PrototypeScopeDemo3.java`

Each `placeOrder` and `cancelOrder` call creates a fresh `DatabaseTransaction` prototype via `txFactory.get()` (simulating `@Lookup`). The `try-with-resources` block ensures `close()` is called — equivalent to the caller manually managing the prototype's lifecycle. `OrderService` is a singleton (created once); `DatabaseTransaction.count` grows by one per request. Spring does not call `close()` on prototypes — the caller must.

## 6. Walkthrough

**`svc.placeOrder("ORD-001", 299.99)` — step by step:**

```
placeOrder("ORD-001", 299.99):
  txFactory.get()                → new DatabaseTransaction()
                                   [TX#1] created (BEGIN)
  try (tx = TX#1):
    tx.execute("INSERT INTO orders VALUES ('ORD-001', 299.99)")
      [TX#1] INSERT INTO orders VALUES ('ORD-001', 299.99)
    tx.execute("UPDATE inventory SET reserved = reserved + 1")
      [TX#1] UPDATE inventory SET reserved = reserved + 1
    tx.execute("INSERT INTO audit_log VALUES ('ORD-001', NOW())")
      [TX#1] INSERT INTO audit_log VALUES ('ORD-001', NOW())
    tx.commit()
      [TX#1] COMMIT (3 ops)
  } // try block exits → tx.close() called by try-with-resources
    [TX#1] closed (container does NOT do this for prototypes)
```

**`svc.cancelOrder("ORD-001")` — rollback:**

```
cancelOrder("ORD-001"):
  txFactory.get()                → new DatabaseTransaction()
                                   [TX#2] created (BEGIN)
  try (tx = TX#2):
    tx.execute("UPDATE orders SET status='CANCELLED'...")
      [TX#2] UPDATE orders SET status='CANCELLED'...
    tx.execute("UPDATE inventory SET reserved = reserved - 1")
      [TX#2] UPDATE inventory SET reserved = reserved - 1
    throw RuntimeException("Simulated constraint violation")
  } // tx.close() called: committed=false → rollback()
    [TX#2] ROLLBACK
    [TX#2] closed
  catch: [ORDER] Failed: Simulated constraint violation (tx rolled back)
```

**Lifecycle comparison:**

```
Singleton OrderService:
  Created: once at startup
  Destroyed: at context.close() → @PreDestroy called

Prototype DatabaseTransaction:
  Created: once per txFactory.get() call (3 total)
  Destroyed: never by container → caller's try-with-resources handles it
```

## 7. Gotchas & takeaways

> **`@PreDestroy` is never called on prototype beans.** Spring creates the prototype and hands it off — lifecycle management ends there. If the prototype holds resources (connections, file handles), the caller must close them explicitly. Use `AutoCloseable` and try-with-resources.

> **Injecting a prototype directly into a singleton via `@Autowired` gives you a frozen singleton-scoped prototype.** The singleton is created once, the prototype is injected once at that time, and the same prototype instance is reused forever. Use `ObjectProvider<T>`, `Supplier<T>`, or `@Lookup` to get a fresh prototype per call.

- `ApplicationContext.getBean("name")` always returns a new instance for prototype-scoped beans.
- `@Scope(proxyMode = ScopedProxyMode.TARGET_CLASS)` creates a scoped proxy — every method call on the proxy fetches a fresh prototype from the container. Useful when the prototype is injected into a singleton that was already constructed.
- Prototype scope plus constructor injection: Spring fully constructs and wires the prototype (including all its singleton dependencies) before handing it to the caller.
- Test isolation: prototype-scoped beans are often the right choice for test helper objects that accumulate state during a test and should not share state across tests.
