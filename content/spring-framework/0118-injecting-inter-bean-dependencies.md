---
card: spring-framework
gi: 118
slug: injecting-inter-bean-dependencies
title: "Injecting inter-bean dependencies"
---

## 1. What it is

When one `@Bean` method needs the object produced by another `@Bean` method in the same `@Configuration` class, you have two ways to express that dependency:

1. **Inter-bean method call** — `return new ServiceA(serviceB())`. Works only in full `@Configuration` (CGLIB ensures `serviceB()` returns the singleton).
2. **Parameter injection** — `public ServiceA serviceA(ServiceB b)`. Spring resolves and injects the `ServiceB` bean as a method argument.

Both styles declare the same dependency; the wiring mechanism differs.

## 2. Why & when

- **Method-call style** is natural when all beans live in one config class — it reads like plain Java construction.
- **Parameter style** is required when the dependency comes from a *different* `@Configuration` class, when you want a compile-time-visible dependency signature, or when you're in `@Component` lite mode where CGLIB isn't active.
- Prefer parameter style in large configs to avoid hidden cross-class dependencies — the method signature becomes a contract.

## 3. Core concept

In a `@Configuration` class (full mode, CGLIB active):

```java
@Bean ServiceB serviceB() { return new ServiceB(); }

@Bean ServiceA serviceA() {
    return new ServiceA(serviceB());  // CGLIB intercepts → returns singleton
}
```

Spring's CGLIB subclass overrides `serviceB()` so repeated calls return the cached singleton rather than constructing a new one.

With parameter injection (works in both `@Configuration` and `@Component`):

```java
@Bean ServiceA serviceA(ServiceB b) {
    return new ServiceA(b);  // b is resolved from context
}
```

Spring resolves the parameter `b` by type (with `@Qualifier` support), then injects it. This works even when `ServiceB` is defined in an imported `@Configuration` class — no CGLIB needed.

You can mix both styles in the same config class. Parameters take precedence for cross-class dependencies; method calls are fine for same-class references.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Config class -->
  <rect x="10" y="40" width="195" height="125" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="107" y="63" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">@Configuration</text>
  <text x="107" y="85" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Bean ServiceB serviceB()</text>
  <text x="107" y="108" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Bean ServiceA serviceA()</text>
  <text x="107" y="123" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">  → calls serviceB() (CGLIB)</text>
  <text x="107" y="143" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Bean ServiceC serviceC(B b)</text>
  <text x="107" y="157" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">  → param injected from ctx</text>

  <!-- Singleton registry -->
  <rect x="290" y="40" width="160" height="125" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="370" y="63" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Singleton Cache</text>
  <text x="370" y="85" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">serviceB → ServiceB(1)</text>
  <text x="370" y="105" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">serviceA → ServiceA(B1)</text>
  <text x="370" y="125" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">serviceC → ServiceC(B1)</text>

  <!-- Arrows -->
  <line x1="207" y1="105" x2="287" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#a118)"/>
  <defs>
    <marker id="a118" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b118" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="240" y="82" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">CGLIB intercept</text>
  <text x="240" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">param injection</text>

  <!-- Dependants -->
  <rect x="540" y="65" width="150" height="75" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="615" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Dependants</text>
  <text x="615" y="108" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">same B1 singleton</text>
  <text x="615" y="124" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">in A and C</text>

  <line x1="452" y1="100" x2="537" y2="100" stroke="#79c0ff" stroke-width="2" marker-end="url(#b118)"/>
  <text x="350" y="190" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Both styles route through the singleton cache — same ServiceB instance in every consumer</text>
</svg>

Both method-call and parameter styles ultimately share the same singleton from the registry.

## 5. Runnable example

### Level 1 — Basic

Method-call style within a single `@Configuration`: show that the same instance is shared.

```java
// InterBeanBasic.java
import org.springframework.context.annotation.*;

class Db {
    private static int instances = 0;
    private final int id;
    Db() { this.id = ++instances; System.out.println("[Db] instance #" + id + " created"); }
    public String query(String sql) { return "[DB#" + id + "] " + sql; }
}

class UserRepo {
    private final Db db;
    UserRepo(Db d) { this.db = d; }
    public String find(int id) { return db.query("SELECT * FROM users WHERE id=" + id); }
}

class OrderRepo {
    private final Db db;
    OrderRepo(Db d) { this.db = d; }
    public String find(int id) { return db.query("SELECT * FROM orders WHERE id=" + id); }
}

@Configuration
class DbCfg {
    @Bean public Db db() { return new Db(); }

    @Bean public UserRepo userRepo() {
        return new UserRepo(db());   // CGLIB returns singleton Db
    }

    @Bean public OrderRepo orderRepo() {
        return new OrderRepo(db());  // same singleton Db
    }
}

public class InterBeanBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DbCfg.class);

        System.out.println(ctx.getBean(UserRepo.class).find(1));
        System.out.println(ctx.getBean(OrderRepo.class).find(5));

        // Only one Db was created
        System.out.println("Db instance count: " + Db.instances);
        ctx.close();
    }
}
```

How to run: `java InterBeanBasic.java`

`[Db] instance #1 created` appears exactly once. Both `UserRepo` and `OrderRepo` share `Db#1` — CGLIB makes `db()` return the singleton even when called multiple times in the config class.

### Level 2 — Intermediate

Parameter injection across two `@Configuration` classes connected via `@Import`.

```java
// InterBeanParams.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;

// Data layer — separate config
@Configuration
class DataLayer {
    @Bean public String connectionString() { return "jdbc:h2:mem:test"; }

    @Bean public InMemStore inMemStore(String connectionString) {
        System.out.println("[Store] connecting to " + connectionString);
        return new InMemStore(connectionString);
    }
}

class InMemStore {
    private final String conn;
    InMemStore(String c) { this.conn = c; }
    public String save(String item) { return "[" + conn + "] saved " + item; }
}

// Service layer — imports data layer
@Configuration
@Import(DataLayer.class)
class ServiceLayer {
    @Bean
    public ItemService itemService(InMemStore store) {
        // param 'store' injected from DataLayer — no CGLIB cross-class call needed
        return new ItemService(store);
    }
}

class ItemService {
    private final InMemStore store;
    ItemService(InMemStore s) { this.store = s; }
    public void add(String item) { System.out.println(store.save(item)); }
}

public class InterBeanParams {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ServiceLayer.class);
        ctx.getBean(ItemService.class).add("widget-7");
        ctx.getBean(ItemService.class).add("widget-8");

        // Verify single InMemStore
        var s1 = ctx.getBean(InMemStore.class);
        var s2 = ctx.getBean(InMemStore.class);
        System.out.println("Same store? " + (s1 == s2));
        ctx.close();
    }
}
```

How to run: `java InterBeanParams.java`

`ServiceLayer.itemService(InMemStore store)` receives the `InMemStore` bean defined in `DataLayer` via parameter injection. No direct method call to the other config class is needed.

### Level 3 — Advanced

Mixed approach: method calls for same-class beans, parameters for cross-config beans, plus a circular dependency resolved via parameter injection order.

```java
// InterBeanAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;

// Shared infrastructure
@Configuration
class Infra {
    @Bean public EventBus eventBus() {
        System.out.println("[Infra] creating EventBus");
        return new EventBus();
    }

    @Bean public AuditLogger auditLogger(EventBus bus) {
        System.out.println("[Infra] creating AuditLogger");
        return new AuditLogger(bus);  // param injection from same class — also works
    }
}

class EventBus {
    public void publish(String e) { System.out.println("[EventBus] " + e); }
}

class AuditLogger {
    private final EventBus bus;
    AuditLogger(EventBus b) { this.bus = b; }
    public void audit(String action) {
        bus.publish("AUDIT: " + action);
    }
}

// Business config
@Configuration
@Import(Infra.class)
class Business {
    @Bean
    public PaymentService paymentService(AuditLogger audit) {
        return new PaymentService(audit);
    }

    @Bean
    public NotificationService notificationService(EventBus bus) {
        return new NotificationService(bus);
    }

    @Bean
    public OrderService orderService(PaymentService pay,
                                     NotificationService notify) {
        return new OrderService(pay, notify);
    }
}

class PaymentService {
    private final AuditLogger audit;
    PaymentService(AuditLogger a) { this.audit = a; }
    public String charge(double amt) {
        audit.audit("charge $" + amt);
        return "charged $" + amt;
    }
}

class NotificationService {
    private final EventBus bus;
    NotificationService(EventBus b) { this.bus = b; }
    public void notify(String msg) { bus.publish("NOTIFY: " + msg); }
}

class OrderService {
    private final PaymentService pay;
    private final NotificationService notify;

    OrderService(PaymentService p, NotificationService n) {
        this.pay = p; this.notify = n;
    }

    public void process(int id, double amount) {
        String result = pay.charge(amount);
        notify.notify("Order " + id + " → " + result);
        System.out.println("[Order] processed #" + id);
    }
}

public class InterBeanAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(Business.class);
        ctx.getBean(OrderService.class).process(42, 149.99);

        // Verify shared EventBus singleton
        var b1 = ctx.getBean(EventBus.class);
        var b2 = ctx.getBean(EventBus.class);
        System.out.println("\nSame EventBus? " + (b1 == b2));
        ctx.close();
    }
}
```

How to run: `java InterBeanAdvanced.java`

Both `PaymentService → AuditLogger → EventBus` and `NotificationService → EventBus` chains end up with the same `EventBus` singleton. The dependency graph is fully expressed via method parameters across config classes.

## 6. Walkthrough

Execution order for Level 3:

1. **Context created with `Business.class`** — `@Import(Infra.class)` adds `Infra` config.
2. **`Infra.eventBus()` called** — `new EventBus()` created and registered. Prints `[Infra] creating EventBus`.
3. **`Infra.auditLogger(EventBus bus)` called** — Spring resolves `EventBus` param from registry → passes the singleton → `new AuditLogger(bus)`. Prints `[Infra] creating AuditLogger`.
4. **`Business.paymentService(AuditLogger audit)` called** — `audit` resolved from registry.
5. **`Business.notificationService(EventBus bus)` called** — same `EventBus` singleton injected.
6. **`Business.orderService(PaymentService, NotificationService)` called** — both resolved from registry.
7. **`process(42, 149.99)` called:**
   - `pay.charge(149.99)` → `audit.audit("charge $149.99")` → `bus.publish("AUDIT: charge $149.99")` → `[EventBus] AUDIT: charge $149.99`
   - `notify.notify("Order 42 → charged $149.99")` → `bus.publish(...)` → `[EventBus] NOTIFY: Order 42 → ...`
   - `[Order] processed #42`

Expected output:
```
[Infra] creating EventBus
[Infra] creating AuditLogger
[EventBus] AUDIT: charge $149.99
[EventBus] NOTIFY: Order 42 → charged $149.99
[Order] processed #42

Same EventBus? true
```

## 7. Gotchas & takeaways

> Calling a `@Bean` method from a **different** `@Configuration` class does **not** go through CGLIB — you'd be calling a plain Java method on the other config class instance and getting a new object. Use parameter injection for cross-class bean references.

> If you call `serviceB()` from `serviceA()` in the **same** `@Configuration`, CGLIB intercepts and returns the singleton. If you forget that and move both methods to a `@Component` (lite mode), you silently get separate instances.

- Parameter injection is the safest pattern in all contexts — it works in `@Configuration`, `@Component`, and regardless of CGLIB.
- Spring resolves `@Bean` method parameters by type, with `@Qualifier` and `@Primary` for disambiguation.
- A `@Bean` method with 0 parameters depends on whatever types it instantiates via method calls — those are not visible as declared dependencies. Parameter injection makes dependencies explicit and testable.
- For optional dependencies in `@Bean` methods, use `Optional<T>` or `ObjectProvider<T>` as parameter types.
