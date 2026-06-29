---
card: spring-framework
gi: 16
slug: inversion-of-control-ioc-principle
title: Inversion of Control (IoC) principle
---

## 1. What it is

**Inversion of Control (IoC)** is a design principle where the *framework* — not your code — controls the creation, configuration, and lifecycle of objects.

Normally your code is in charge: it calls `new`, decides construction order, wires objects together. With IoC that control is *inverted*: you declare what you need and the framework figures out how to build and connect everything.

Spring's IoC container is the machinery that implements this principle. You annotate classes (`@Component`, `@Service`) or write configuration classes, and the container reads those declarations and assembles the application.

In one sentence: **IoC means the framework drives object creation, not your code.**

## 2. Why & when

Without IoC, every class that needs a collaborator must construct it (`new EmailService()`) or look it up (`JNDI.lookup("email")`). This creates three problems:

- **Tight coupling.** `OrderService` becomes permanently bound to `EmailService`. Swapping to `SmsService` requires editing `OrderService`.
- **Hard to test.** You cannot substitute a mock without either subclassing or modifying the source.
- **Manual ordering.** You must construct dependencies before consumers, in the right order, throughout the whole app.

IoC solves all three at once: the container controls construction order, injects the correct implementation, and lets tests inject substitutes at will.

Use IoC everywhere in Spring applications. The only exception is short-lived value objects (`new Address(street, city)`) where there is no collaborator — those never need a container.

## 3. Core concept

Think of a car assembly line. In the *old* approach the car engine builds its own fuel pump: `this.fuelPump = new FuelPump("diesel")`. The engine is tightly coupled to one fuel type. With IoC the assembly line *installs* the right fuel pump into the engine. The engine just declares "I need a `FuelPump`."

The shift in responsibility:

| | Who controls construction |
|---|---|
| **Without IoC** | The object itself (`new` inside) |
| **With IoC** | The container (Spring's `ApplicationContext`) |

Spring implements IoC through **Dependency Injection (DI)**: the container injects dependencies into objects through constructors or setters rather than letting objects fetch them.

Three things must exist for IoC to work:
1. **Component declarations** — tell the container which classes are beans (`@Component`, `@Bean`).
2. **Dependency declarations** — tell the container what each bean needs (constructor parameters, `@Autowired`).
3. **A container** — reads the declarations, creates beans in dependency order, injects them.

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Traditional control flow vs IoC: object creates its own dependency vs container injects it">
  <defs>
    <marker id="a16" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b16" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Left side: traditional -->
  <text x="150" y="18" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Traditional (you in control)</text>
  <rect x="50" y="30" width="200" height="52" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="150" y="52" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="150" y="72" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">new EmailService() ← creates dep</text>

  <rect x="100" y="115" width="100" height="38" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="150" y="138" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">EmailService</text>
  <line x1="150" y1="82" x2="150" y2="113" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a16)"/>
  <text x="150" y="175" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">coupling: cannot swap</text>

  <!-- Right side: IoC -->
  <text x="520" y="18" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">IoC (container in control)</text>
  <rect x="390" y="30" width="150" height="52" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="465" y="52" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">IoC Container</text>
  <text x="465" y="69" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">creates + wires beans</text>

  <rect x="570" y="30" width="100" height="52" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="620" y="52" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="620" y="68" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">declares dep only</text>

  <rect x="440" y="115" width="110" height="38" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="495" y="131" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">EmailService</text>
  <text x="495" y="146" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(or SmsService)</text>

  <line x1="540" y1="56" x2="572" y2="56" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b16)"/>
  <line x1="495" y1="82" x2="495" y2="113" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a16)"/>
  <line x1="550" y1="134" x2="572" y2="72" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#a16)"/>
  <text x="620" y="160" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">injected ↑</text>

  <text x="520" y="185" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">swap impl → change container config only</text>
</svg>

Traditional: the object calls `new` and owns its dependency. IoC: the container owns construction; the object only declares what it needs.

## 5. Runnable example

Scenario: a logging pipeline that writes audit records. It needs a *transport* (stdout, file, remote). We show how coupling to one transport becomes a problem, then fix it with IoC.

### Level 1 — Basic

Tight coupling: `AuditLogger` creates its own transport inside the constructor.

```java
// IoCDemo.java — run with: java IoCDemo.java
public class IoCDemo {

    // Transport hard-coded inside the logger — no IoC
    static class ConsoleTransport {
        void write(String msg) { System.out.println("[CONSOLE] " + msg); }
    }

    static class AuditLogger {
        private final ConsoleTransport transport;

        AuditLogger() {
            this.transport = new ConsoleTransport();  // object controls its own dep
        }

        void log(String event) {
            transport.write("AUDIT: " + event);
        }
    }

    public static void main(String[] args) {
        AuditLogger logger = new AuditLogger();
        logger.log("user.login  user=alice");
        logger.log("order.placed  id=101");
    }
}
```

How to run: `java IoCDemo.java`

`AuditLogger` is glued to `ConsoleTransport`. A test cannot inject a silent transport; switching to file transport requires editing the class. Every caller gets the same hard-coded choice.

### Level 2 — Intermediate

Manual IoC: the caller constructs the transport and *passes it in*. Control is inverted — the caller decides which transport to use.

```java
// IoCDemoV2.java — run with: java IoCDemoV2.java
public class IoCDemoV2 {

    // Abstraction — the logger depends on this interface, not a concrete class
    interface Transport {
        void write(String msg);
    }

    static class ConsoleTransport implements Transport {
        public void write(String msg) { System.out.println("[CONSOLE] " + msg); }
    }

    static class FileTransport implements Transport {
        private final String path;
        FileTransport(String path) { this.path = path; }
        public void write(String msg) { System.out.println("[FILE:" + path + "] " + msg); }
    }

    // AuditLogger no longer decides its transport — it receives it
    static class AuditLogger {
        private final Transport transport;

        AuditLogger(Transport transport) {   // <-- IoC: caller injects
            this.transport = transport;
        }

        void log(String event) {
            transport.write("AUDIT: " + event);
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Production: console transport ===");
        AuditLogger prod = new AuditLogger(new ConsoleTransport());
        prod.log("user.login  user=alice");

        System.out.println("\n=== Ops: file transport ===");
        AuditLogger ops = new AuditLogger(new FileTransport("/var/log/audit.log"));
        ops.log("order.placed  id=101");

        System.out.println("\n=== Test: silent (no-op) transport ===");
        AuditLogger test = new AuditLogger(msg -> {});  // lambda Transport — no output
        test.log("order.placed  id=999");
        System.out.println("(nothing printed — test transport swallows output)");
    }
}
```

How to run: `java IoCDemoV2.java`

The `main` method now plays the role of the IoC container: it creates the transport and injects it. Three different transports, zero changes to `AuditLogger`. The lambda `msg -> {}` shows a silent test transport.

### Level 3 — Advanced

A mini IoC container handles construction and injection automatically, mirroring what Spring's `ApplicationContext` does. Same scenario — just the container now drives everything.

```java
// IoCDemoV3.java — run with: java IoCDemoV3.java
import java.util.*;
import java.lang.reflect.*;
import java.util.function.*;

public class IoCDemoV3 {

    @interface Inject {}   // stand-in for @Autowired

    interface Transport { void write(String msg); }

    static class ConsoleTransport implements Transport {
        public void write(String msg) { System.out.println("[CONSOLE] " + msg); }
    }

    static class AuditLogger {
        private final Transport transport;
        @Inject
        AuditLogger(Transport transport) { this.transport = transport; }
        void log(String event) { transport.write("AUDIT: " + event); }
    }

    static class OrderService {
        private final AuditLogger auditLogger;
        @Inject
        OrderService(AuditLogger auditLogger) { this.auditLogger = auditLogger; }
        void placeOrder(String item) {
            System.out.println("Placing order: " + item);
            auditLogger.log("order.placed  item=" + item);
        }
    }

    // --- Mini IoC container ---
    static class Container {
        private final Map<Class<?>, Supplier<?>> factories = new LinkedHashMap<>();
        private final Map<Class<?>, Object> singletons = new LinkedHashMap<>();

        <T> void register(Class<T> type, Supplier<T> factory) {
            factories.put(type, factory);
        }

        @SuppressWarnings("unchecked")
        <T> T get(Class<T> type) {
            return (T) singletons.computeIfAbsent(type, t -> factories.get(t).get());
        }

        // Auto-wire: find @Inject constructor, resolve parameter beans, instantiate
        void scan(Class<?>... classes) throws Exception {
            for (Class<?> cls : classes) {
                Constructor<?> ctor = Arrays.stream(cls.getDeclaredConstructors())
                    .filter(c -> c.isAnnotationPresent(Inject.class))
                    .findFirst()
                    .orElse(cls.getDeclaredConstructors()[0]);
                factories.put(cls, () -> {
                    try {
                        Object[] deps = Arrays.stream(ctor.getParameterTypes())
                            .map(this::get).toArray();
                        return ctor.newInstance(deps);
                    } catch (Exception e) { throw new RuntimeException(e); }
                });
                System.out.println("  Scanned: " + cls.getSimpleName());
            }
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Container startup ===");
        Container ctx = new Container();

        // Register the Transport implementation (the "configuration")
        ctx.register(Transport.class, ConsoleTransport::new);

        // Scan components — container discovers deps via @Inject constructors
        ctx.scan(ConsoleTransport.class, AuditLogger.class, OrderService.class);

        System.out.println("\n=== Application running ===");
        OrderService svc = ctx.get(OrderService.class);
        svc.placeOrder("Laptop");
        svc.placeOrder("Monitor");

        System.out.println("\n=== Swap transport — no OrderService change needed ===");
        Container ctx2 = new Container();
        ctx2.register(Transport.class, () -> msg -> System.out.println("[FILE] " + msg));
        ctx2.scan(AuditLogger.class, OrderService.class);
        ctx2.get(OrderService.class).placeOrder("Keyboard");
    }
}
```

How to run: `java IoCDemoV3.java`

The container scans classes, reads `@Inject` constructors, and resolves dependency types from its registry — then instantiates in the correct order. The second `ctx2` shows swapping `Transport` to a file-style lambda without touching `AuditLogger` or `OrderService` at all. Spring's real `ApplicationContext` does exactly this with more features (scope, AOP, events, lifecycle).

## 6. Walkthrough

**Entry point** — `main` creates `Container`, registers `ConsoleTransport` as the `Transport` implementation, then calls `scan(ConsoleTransport.class, AuditLogger.class, OrderService.class)`.

**Scan phase (mirrors Spring's component scan):**
1. For `ConsoleTransport` — no `@Inject` constructor found, takes the only constructor (no params). Factory stored.
2. For `AuditLogger` — `@Inject` constructor found with `Transport` parameter. Factory stored as a lambda that will call `get(Transport.class)` when invoked.
3. For `OrderService` — `@Inject` constructor found with `AuditLogger` parameter. Factory stored similarly.

Nothing is instantiated yet. Spring calls this the *bean definition phase*.

**First `get(OrderService.class)` call — instantiation in dependency order:**
- `singletons` has no `OrderService` → invoke factory.
- Factory needs `AuditLogger` → invoke `AuditLogger` factory.
- `AuditLogger` factory needs `Transport` → invoke `Transport` factory → `new ConsoleTransport()` created and cached.
- `AuditLogger` constructed with the `ConsoleTransport` → cached.
- `OrderService` constructed with the `AuditLogger` → cached.

**`placeOrder("Laptop")` execution:**
```
placeOrder("Laptop")
  → System.out.println("Placing order: Laptop")
  → auditLogger.log("order.placed  item=Laptop")
      → transport.write("AUDIT: order.placed  item=Laptop")
          → [CONSOLE] AUDIT: order.placed  item=Laptop
```

**Second container (`ctx2`) — swap transport:**
The only change is `ctx2.register(Transport.class, () -> msg -> System.out.println("[FILE] " + msg))`. `AuditLogger` and `OrderService` classes are identical. The container re-wires with the new implementation. This is IoC in its most useful form: change config, not code.

## 7. Gotchas & takeaways

> **IoC is a principle, not a library.** Even the Level 2 manual wiring (passing deps through constructors) *is* IoC. Spring automates it, but the pattern's value exists independent of any framework.

> **The container must know about an object to manage it.** If you call `new OrderService()` inside a Spring component, Spring cannot inject that instance's dependencies, apply AOP, or manage its lifecycle. Never `new` a Spring bean manually.

- Objects that control their own deps are hard to test; objects that receive deps are trivially testable with mocks.
- IoC dependency order is resolved at container startup — circular dependencies are caught early, not at runtime.
- Spring defaults to singleton scope: one instance per bean definition. This is nearly always what you want for stateless services.
- Constructor injection is preferred: it makes all dependencies visible and allows `final` fields.
- `@Component` (any bean) vs `@Service` (service layer) vs `@Repository` (data layer) vs `@Controller` (web layer) are semantically equivalent to the container — the distinctions aid readability and enable layer-specific exception translation.
