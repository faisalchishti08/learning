---
card: spring-framework
gi: 52
slug: references-to-other-beans-ref
title: References to other beans (ref)
---

## 1. What it is

**Bean references** connect one Spring bean to another. Instead of constructing collaborators yourself, you declare that a bean *depends on* another bean by name or type, and Spring injects the live instance. In XML this uses the `ref` attribute or `<ref>` element; in annotation-driven code it uses `@Autowired` or `@Inject`.

```java
// Annotation style — Spring finds and injects the DataSource bean
@Component
public class UserRepository {

    private final DataSource dataSource;

    @Autowired
    public UserRepository(DataSource dataSource) {   // ref by type
        this.dataSource = dataSource;
    }
}

// XML equivalent
// <bean id="userRepository" class="UserRepository">
//   <constructor-arg ref="dataSource"/>          <!-- ref by id -->
// </bean>
```

The `ref` attribute tells Spring "inject the bean named X here" — Spring looks up that bean, ensures it exists and is fully initialised, and passes it in.

In one sentence: **A bean reference (`ref`) lets one bean declare that it needs another bean as a collaborator, and Spring satisfies that dependency by wiring in the referenced bean's live instance.**

## 2. Why & when

Bean references implement the *Dependency Inversion* and *Single Responsibility* principles — each bean does one job, and its collaborators are injected, not created inline:

- **Service → Repository** — `UserService` references `UserRepository`.
- **Controller → Service** — `OrderController` references `OrderService`.
- **Service → external client** — `EmailService` references a `JavaMailSender` bean.
- **Cross-cutting infrastructure** — multiple services all reference the same `TransactionManager` bean.

Prefer constructor injection (`ref` on `<constructor-arg>`) over setter injection: it makes dependencies explicit and ensures the bean is never in a partially-constructed state.

## 3. Core concept

```
Bean A declares a ref to Bean B:

  Container startup:
    1. Instantiate Bean B (if singleton, once only).
    2. Instantiate Bean A, passing the Bean B instance as argument.
    3. Bean A holds a reference to Bean B; they share the same object.

  XML:
    <bean id="b" class="B"/>
    <bean id="a" class="A">
      <constructor-arg ref="b"/>         ← ref by bean id
    </bean>

  Annotation:
    @Autowired  ← ref by type (Spring finds the DataSource bean)
    DataSource ds;

  Circular ref (A → B and B → A):
    → BeanCurrentlyInCreationException  (constructor injection)
    → silently works but is a design smell (setter injection, fixable with @Lazy)
```

## 4. Diagram

<svg viewBox="0 0 620 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring container resolving bean references: Container creates DataSource, then injects it into UserRepository, which is injected into UserService">
  <defs>
    <marker id="a52" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <!-- Container -->
  <rect x="5" y="5" width="610" height="185" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="310" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Spring IoC Container</text>

  <!-- DataSource bean -->
  <rect x="20" y="40" width="150" height="60" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="95" y="62" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">DataSource</text>
  <text x="95" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">id="dataSource"</text>
  <text x="95" y="94" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">HikariCP pool</text>

  <!-- UserRepository bean -->
  <rect x="230" y="40" width="160" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="62" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">UserRepository</text>
  <text x="310" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ref="dataSource" ↑</text>
  <text x="310" y="94" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">DataSource injected</text>

  <!-- UserService bean -->
  <rect x="450" y="40" width="150" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="525" y="62" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">UserService</text>
  <text x="525" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ref="userRepository" ↑</text>
  <text x="525" y="94" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Repository injected</text>

  <!-- Arrows -->
  <line x1="170" y1="70" x2="228" y2="70" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a52)"/>
  <line x1="390" y1="70" x2="448" y2="70" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a52)"/>

  <!-- Creation order -->
  <text x="95"  y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">① created first</text>
  <text x="310" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">② created second</text>
  <text x="525" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">③ created last</text>

  <text x="310" y="170" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">All three beans are singletons. The same DataSource instance is injected wherever it is referenced.</text>
</svg>

Spring resolves references depth-first: `DataSource` is created first (no deps), then `UserRepository` (depends on DataSource), then `UserService` (depends on UserRepository).

## 5. Runnable example

Scenario: an `OrderService` that delegates to an `InventoryRepository` and an `EmailNotifier`. We wire them purely via references — no `new` inside `OrderService`.

### Level 1 — Basic

Three collaborating beans wired by constructor reference.

```java
// BeanRefDemo.java — run with: java BeanRefDemo.java

public class BeanRefDemo {

    // ── collaborators ──────────────────────────────────────────────────
    static class EmailNotifier {
        void send(String to, String msg) {
            System.out.println("  [EMAIL→" + to + "] " + msg);
        }
    }

    static class InventoryRepository {
        boolean isInStock(String productId, int qty) {
            System.out.println("  [INVENTORY] checking " + productId + " qty=" + qty);
            return qty <= 100;   // simplified: everything ≤100 is in stock
        }
    }

    static class OrderService {
        private final InventoryRepository inventory;
        private final EmailNotifier       notifier;

        // constructor injection — mirrors Spring @Autowired constructor
        OrderService(InventoryRepository inventory, EmailNotifier notifier) {
            this.inventory = inventory;
            this.notifier  = notifier;
            System.out.println("  [BEAN] OrderService created (refs wired)");
        }

        void placeOrder(String productId, int qty, String email) {
            System.out.println("[ORDER] place: product=" + productId + " qty=" + qty);
            if (!inventory.isInStock(productId, qty)) {
                notifier.send(email, "Out of stock: " + productId);
                return;
            }
            notifier.send(email, "Order confirmed: " + productId + " x" + qty);
        }
    }

    // ── "container" — manually wires the refs ─────────────────────────
    static OrderService buildContainer() {
        EmailNotifier       notifier  = new EmailNotifier();        // bean B
        InventoryRepository inventory = new InventoryRepository();  // bean C
        return new OrderService(inventory, notifier);               // bean A, refs B+C
    }

    public static void main(String[] args) {
        OrderService svc = buildContainer();
        svc.placeOrder("SKU-001", 5,   "alice@example.com");
        svc.placeOrder("SKU-999", 200, "bob@example.com");
    }
}
```

How to run: `java BeanRefDemo.java`

`buildContainer()` simulates Spring's `ApplicationContext`: it creates the dependency beans first, then constructs `OrderService` with references to them. `OrderService` never calls `new`; it receives live collaborator instances. This is exactly what Spring does with `ref` attributes.

### Level 2 — Intermediate

Same scenario — now the notifier and repository are interfaces, demonstrating how `ref` enables polymorphism (swap implementations without changing `OrderService`).

```java
// BeanRefDemo2.java — run with: java BeanRefDemo2.java
import java.util.HashMap;
import java.util.Map;

public class BeanRefDemo2 {

    // ── abstractions ───────────────────────────────────────────────────
    interface Notifier {
        void send(String to, String msg);
    }

    interface InventoryRepo {
        boolean isInStock(String productId, int qty);
    }

    // ── implementations ────────────────────────────────────────────────
    static class LoggingNotifier implements Notifier {
        @Override
        public void send(String to, String msg) {
            System.out.println("  [LOG ONLY] to=" + to + " msg=" + msg);
        }
    }

    static class SmtpNotifier implements Notifier {
        @Override
        public void send(String to, String msg) {
            System.out.println("  [SMTP→" + to + "] " + msg);
        }
    }

    static class InMemoryInventory implements InventoryRepo {
        private final Map<String, Integer> stock = new HashMap<>(Map.of(
            "SKU-001", 50, "SKU-002", 200, "SKU-999", 0
        ));
        @Override
        public boolean isInStock(String productId, int qty) {
            int available = stock.getOrDefault(productId, 0);
            System.out.println("  [INVENTORY] " + productId + " available=" + available + " wanted=" + qty);
            return available >= qty;
        }
    }

    // ── service: refs to interfaces, not concrete types ────────────────
    static class OrderService {
        private final InventoryRepo inventory;
        private final Notifier      notifier;

        OrderService(InventoryRepo inventory, Notifier notifier) {
            this.inventory = inventory;
            this.notifier  = notifier;
            System.out.println("  [BEAN] OrderService wired: inventory="
                + inventory.getClass().getSimpleName()
                + " notifier=" + notifier.getClass().getSimpleName());
        }

        void placeOrder(String productId, int qty, String email) {
            System.out.println("[ORDER] product=" + productId + " qty=" + qty);
            if (!inventory.isInStock(productId, qty)) {
                notifier.send(email, "Insufficient stock for " + productId);
            } else {
                notifier.send(email, "Confirmed: " + productId + " x" + qty);
            }
        }
    }

    static OrderService buildProd() {
        return new OrderService(new InMemoryInventory(), new SmtpNotifier());
    }

    static OrderService buildDev() {
        return new OrderService(new InMemoryInventory(), new LoggingNotifier());
    }

    public static void main(String[] args) {
        System.out.println("=== Prod wiring ===");
        OrderService prod = buildProd();
        prod.placeOrder("SKU-001", 10, "alice@example.com");

        System.out.println("\n=== Dev wiring (no real email) ===");
        OrderService dev = buildDev();
        dev.placeOrder("SKU-999", 1, "dev@local");
    }
}
```

How to run: `java BeanRefDemo2.java`

`OrderService` is unchanged between prod and dev. Only the wiring (`ref`) changes: `SmtpNotifier` vs `LoggingNotifier`. This is why `ref` to an interface is powerful — the consumer is decoupled from the implementation. Spring's `ref` attribute achieves the same swap by pointing to a different bean id.

### Level 3 — Advanced

Same scenario, production-grade: layered wiring, a shared `TransactionManager` referenced by multiple beans, lazy initialisation, and post-init checks.

```java
// BeanRefDemo3.java — run with: java BeanRefDemo3.java
import java.util.*;

public class BeanRefDemo3 {

    // ── transaction support ────────────────────────────────────────────
    static class TransactionManager {
        private int txCount = 0;
        void begin()    { txCount++; System.out.println("    [TX#" + txCount + "] begin"); }
        void commit()   { System.out.println("    [TX#" + txCount + "] commit"); }
        void rollback() { System.out.println("    [TX#" + txCount + "] rollback"); }
    }

    // ── repositories — both reference the SAME TransactionManager bean ─
    static class OrderRepository {
        private final TransactionManager tx;
        OrderRepository(TransactionManager tx) {
            this.tx = tx;
            System.out.println("  [BEAN] OrderRepository created");
        }
        void save(String orderId) {
            tx.begin();
            System.out.println("    [REPO] INSERT order id=" + orderId);
            tx.commit();
        }
    }

    static class AuditRepository {
        private final TransactionManager tx;
        AuditRepository(TransactionManager tx) {
            this.tx = tx;
            System.out.println("  [BEAN] AuditRepository created");
        }
        void log(String event) {
            tx.begin();
            System.out.println("    [AUDIT] INSERT audit event=" + event);
            tx.commit();
        }
    }

    interface Notifier {
        void send(String to, String msg);
    }

    static class SmtpNotifier implements Notifier {
        private boolean initialised = false;
        void init() {
            System.out.println("  [SMTP] connecting to smtp.example.com:587...");
            initialised = true;
        }
        @Override
        public void send(String to, String msg) {
            if (!initialised) throw new IllegalStateException("NotInitialised");
            System.out.println("  [SMTP→" + to + "] " + msg);
        }
    }

    // ── service — references three separate beans ──────────────────────
    static class OrderService {
        private final OrderRepository orderRepo;
        private final AuditRepository auditRepo;
        private final Notifier        notifier;

        OrderService(OrderRepository orderRepo, AuditRepository auditRepo, Notifier notifier) {
            this.orderRepo = orderRepo;
            this.auditRepo = auditRepo;
            this.notifier  = notifier;
            System.out.println("  [BEAN] OrderService created (3 refs wired)");
        }

        void placeOrder(String productId, int qty, String email) {
            System.out.println("[ORDER] placing: product=" + productId + " qty=" + qty);
            String orderId = "ORD-" + System.nanoTime() % 10000;
            try {
                orderRepo.save(orderId);
                auditRepo.log("ORDER_PLACED orderId=" + orderId);
                notifier.send(email, "Order " + orderId + " confirmed: " + productId + " x" + qty);
                System.out.println("[ORDER] done: " + orderId);
            } catch (Exception e) {
                System.out.println("[ORDER] FAILED: " + e.getMessage());
            }
        }
    }

    // ── container bootstrap ────────────────────────────────────────────
    static OrderService buildContainer() {
        System.out.println("[CONTAINER] starting up...");
        TransactionManager tx = new TransactionManager();          // shared singleton
        OrderRepository orderRepo = new OrderRepository(tx);       // ref→tx
        AuditRepository auditRepo = new AuditRepository(tx);       // ref→SAME tx instance
        SmtpNotifier notifier = new SmtpNotifier();
        notifier.init();                                           // @PostConstruct equivalent
        OrderService svc = new OrderService(orderRepo, auditRepo, notifier);
        System.out.println("[CONTAINER] ready\n");
        return svc;
    }

    public static void main(String[] args) {
        OrderService svc = buildContainer();
        svc.placeOrder("SKU-001", 3, "alice@example.com");
        System.out.println();
        svc.placeOrder("SKU-002", 1, "bob@example.com");
    }
}
```

How to run: `java BeanRefDemo3.java`

Both `OrderRepository` and `AuditRepository` reference the **same** `TransactionManager` singleton — this is a fundamental property of Spring `ref` with singleton-scoped beans: all referencing beans share the exact same instance. `SmtpNotifier.init()` mirrors `@PostConstruct` — the container calls it after construction but before any beans that reference it are built. The creation order is: `TransactionManager` → `OrderRepository` → `AuditRepository` → `SmtpNotifier` → `OrderService`.

## 6. Walkthrough

Entry point: `main()` calls `buildContainer()`.

**Step 1 — Container creates `TransactionManager`.**
No dependencies; instantiated immediately. This singleton will be shared.

**Step 2 — Container creates `OrderRepository(tx)`.**
Constructor receives the `TransactionManager` reference. Prints `[BEAN] OrderRepository created`.

**Step 3 — Container creates `AuditRepository(tx)`.**
Same `TransactionManager` instance passed. Both repos now hold the same object reference.

**Step 4 — Container creates and initialises `SmtpNotifier`.**
`init()` called — equivalent to `@PostConstruct`. Sets `initialised = true`.

**Step 5 — Container creates `OrderService(orderRepo, auditRepo, notifier)`.**
Three refs wired simultaneously. Prints `[BEAN] OrderService created`.

**Step 6 — `placeOrder("SKU-001", 3, "alice@example.com")`.**

```
[ORDER] placing: product=SKU-001 qty=3
  OrderRepository.save("ORD-XXXX"):
    [TX#1] begin
    [REPO] INSERT order id=ORD-XXXX
    [TX#1] commit
  AuditRepository.log("ORDER_PLACED orderId=ORD-XXXX"):
    [TX#2] begin
    [AUDIT] INSERT audit event=ORDER_PLACED orderId=ORD-XXXX
    [TX#2] commit
  SmtpNotifier.send("alice@example.com", "Order ORD-XXXX confirmed: SKU-001 x3")
    [SMTP→alice@example.com] Order ORD-XXXX confirmed: SKU-001 x3
[ORDER] done: ORD-XXXX
```

The `txCount` on the shared `TransactionManager` is now `2` — both repos incremented the same counter, proving they share the same instance.

## 7. Gotchas & takeaways

> **Injecting a prototype-scoped bean via `ref` into a singleton gives you ONE instance of the prototype forever.** The singleton is created once; the prototype ref is resolved once at that time. Use `ApplicationContext.getBean()`, a `Provider<T>`, or `@Lookup` if you need a fresh prototype per call.

> **Circular constructor references (`A` needs `B`, `B` needs `A`) cause `BeanCurrentlyInCreationException` at startup.** Spring cannot resolve constructor-injection cycles. Fix by breaking the cycle (usually a design smell), using setter injection on one side, or using `@Lazy` on one constructor parameter.

- `ref` by type (`@Autowired`) is ambiguous when multiple beans implement the same interface — qualify with `@Qualifier("beanId")` or `@Primary`.
- In XML, `ref` and `<ref bean="..."/>` are equivalent; `local` was removed in Spring 5 (use `bean`).
- Singleton refs are resolved at container startup — a missing ref bean causes a fast-fail `NoSuchBeanDefinitionException`, not a `NullPointerException` at call time.
- Constructor injection with `ref` makes the dependency graph explicit and testable: pass a mock directly in unit tests without needing the container.
