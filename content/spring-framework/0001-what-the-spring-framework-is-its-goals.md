---
card: spring-framework
gi: 1
slug: what-the-spring-framework-is-its-goals
title: What the Spring Framework is & its goals
---

## 1. What it is

The **Spring Framework** is a comprehensive Java application framework built around one core idea: your application's objects should not create or look up the things they depend on — the framework hands them in.

This design pattern is called **Inversion of Control (IoC)**. Spring implements it through a **container** that creates objects (called **beans**), wires them together, and manages their entire lifecycle. The container reads your configuration (annotations, Java classes, or XML) and assembles the application automatically.

On top of IoC, Spring provides a rich set of modules: web MVC, JDBC/ORM integration, declarative transaction management, AOP (Aspect-Oriented Programming), testing support, messaging, and more — all sharing the same container and configuration model.

In one sentence: **Spring is a container that assembles and wires your Java objects, plus a toolkit of production-grade modules built on that container.**

## 2. Why & when

Before Spring (early 2000s), the standard Java EE approach required plain business objects to inherit from heavy framework classes, reference JNDI registries, or contain explicit lookup calls to find dependencies. This made code:

- Hard to test (objects wired themselves, making isolation impossible).
- Tightly coupled to the container (no container = no object).
- Verbose (factory patterns and JNDI calls everywhere).

Spring's goals (stated in its original 2003 design document by Rod Johnson) are:

1. **Plain Old Java Objects (POJOs)** — your classes stay ordinary; no framework base classes required.
2. **Testability** — dependencies injected as constructor or setter arguments, so unit tests can pass mocks directly.
3. **No vendor lock-in** — interfaces over concrete implementations; swap JDBC with JPA without rewriting business logic.
4. **Coherent layered architecture** — web, service, repository layers wired together consistently.
5. **Progressive adoption** — use only the modules you need; Spring does not force an all-or-nothing choice.

Use Spring when you need: web applications, REST APIs, database access, transaction management, scheduling, messaging, or any complex Java backend where managing object creation and cross-cutting concerns by hand would be expensive.

## 3. Core concept

The heart of Spring is the **`ApplicationContext`** — the container that holds every bean.

```
Your code:           @Component class OrderService { ... }
                     @Component class EmailService { ... }
                         ↓
ApplicationContext reads metadata, creates both objects,
sees OrderService depends on EmailService,
injects EmailService into OrderService's constructor,
stores both beans, ready to serve.
```

**Inversion of Control** means the control over object creation and lifecycle has moved from your code into the framework. Instead of `new EmailService()` inside `OrderService`, you declare a dependency and the container fulfils it.

**Dependency Injection (DI)** is the mechanism: the container *injects* (passes in) the dependencies. Three styles:

| Style | How |
|---|---|
| Constructor | `OrderService(EmailService email)` — preferred |
| Setter | `setEmailService(EmailService e)` |
| Field | `@Autowired EmailService email` — convenient but hurts testability |

**AOP** (Aspect-Oriented Programming) lets you attach behaviour (logging, transactions, security) to method calls without touching the method's own code — by wrapping beans in proxies at container startup.

## 4. Diagram

<svg viewBox="0 0 700 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ApplicationContext reads configuration, creates beans, wires dependencies, and serves the assembled application">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Config sources -->
  <rect x="10" y="30" width="140" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Component classes</text>

  <rect x="10" y="85" width="140" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80" y="110" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Configuration + @Bean</text>

  <rect x="10" y="140" width="140" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80" y="165" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">application.properties</text>

  <!-- ApplicationContext -->
  <rect x="195" y="50" width="190" height="130" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="290" y="80" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="sans-serif">ApplicationContext</text>
  <text x="290" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">reads metadata</text>
  <text x="290" y="118" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">creates beans (singletons)</text>
  <text x="290" y="136" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">wires dependencies (DI)</text>
  <text x="290" y="154" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">applies AOP proxies</text>
  <text x="290" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">manages lifecycle</text>

  <!-- Output beans -->
  <rect x="430" y="55" width="130" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="76" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="495" y="93" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">← EmailService injected</text>

  <rect x="430" y="120" width="130" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="141" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">EmailService</text>
  <text x="495" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ready singleton</text>

  <!-- Your code -->
  <rect x="600" y="80" width="90" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="645" y="107" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Your code</text>
  <text x="645" y="123" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ctx.getBean(</text>
  <text x="645" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService)</text>

  <line x1="150" y1="52" x2="193" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="150" y1="105" x2="193" y2="115" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="150" y1="160" x2="193" y2="140" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="385" y1="90" x2="428" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="385" y1="130" x2="428" y2="145" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="560" y1="115" x2="598" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <text x="350" y="235" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Container assembles the whole application from metadata — your objects stay plain Java classes</text>
</svg>

The container is the assembler: your objects declare what they need, the container provides it.

## 5. Runnable example

We'll build a simple order-notification flow where `OrderService` depends on `EmailService`, wired together by a hand-rolled mini-container — then progressively add what Spring's real container does.

### Level 1 — Basic

The simplest form: manual dependency injection without any framework — just to see the pattern before adding Spring.

```java
// SpringGoalsDemo.java — run with: java SpringGoalsDemo.java

public class SpringGoalsDemo {

    // A dependency — in real Spring this would be @Component
    static class EmailService {
        void send(String to, String message) {
            System.out.println("EMAIL to " + to + ": " + message);
        }
    }

    // The consumer — depends on EmailService; doesn't create it
    static class OrderService {
        private final EmailService emailService;

        // Constructor injection: the caller decides what EmailService to use
        OrderService(EmailService emailService) {
            this.emailService = emailService;
        }

        void placeOrder(String customer, String item) {
            System.out.println("Order placed: " + item + " for " + customer);
            emailService.send(customer, "Your order for " + item + " is confirmed!");
        }
    }

    public static void main(String[] args) {
        // YOU are the container right now — manually wiring dependencies
        EmailService email = new EmailService();
        OrderService orders = new OrderService(email);  // inject the dependency

        orders.placeOrder("alice@example.com", "Laptop");
    }
}
```

How to run: `java SpringGoalsDemo.java`

`OrderService` never calls `new EmailService()` — the dependency is passed in. This is the pattern Spring automates. In a unit test you could pass a mock `EmailService` here without touching `OrderService` at all.

### Level 2 — Intermediate

Now we build a minimal IoC container: it stores beans by type and injects them by examining constructor parameters. This is conceptually what Spring's `ApplicationContext` does.

```java
// SpringGoalsDemoV2.java — run with: java SpringGoalsDemoV2.java
import java.util.*;
import java.lang.reflect.*;

public class SpringGoalsDemoV2 {

    static class EmailService {
        void send(String to, String message) {
            System.out.println("EMAIL to " + to + ": " + message);
        }
    }

    static class NotificationService {
        private final EmailService emailService;
        NotificationService(EmailService emailService) { this.emailService = emailService; }
        void notifyShipped(String customer, String trackingId) {
            emailService.send(customer, "Shipped! Track: " + trackingId);
        }
    }

    static class OrderService {
        private final EmailService emailService;
        private final NotificationService notificationService;
        OrderService(EmailService e, NotificationService n) {
            this.emailService = e; this.notificationService = n;
        }
        void placeOrder(String customer, String item) {
            System.out.println("Order placed: " + item);
            emailService.send(customer, "Order confirmed: " + item);
            notificationService.notifyShipped(customer, "TRK-" + item.hashCode());
        }
    }

    // --- Mini IoC container ---
    static class MiniContext {
        private final Map<Class<?>, Object> beans = new HashMap<>();

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) { return (T) beans.get(type); }

        void register(Class<?>... classes) throws Exception {
            for (Class<?> cls : classes) {
                Constructor<?> ctor = cls.getDeclaredConstructors()[0];
                Object[] args = Arrays.stream(ctor.getParameterTypes())
                    .map(t -> beans.get(t))
                    .toArray();
                beans.put(cls, ctor.newInstance(args));
                System.out.println("  Registered bean: " + cls.getSimpleName());
            }
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Mini IoC Container Startup ===");
        MiniContext ctx = new MiniContext();
        // Order matters: register dependencies before consumers
        ctx.register(EmailService.class, NotificationService.class, OrderService.class);

        System.out.println("\n=== Application Running ===");
        OrderService orders = ctx.getBean(OrderService.class);
        orders.placeOrder("alice@example.com", "Keyboard");
    }
}
```

How to run: `java SpringGoalsDemoV2.java`

The `MiniContext.register()` method introspects each class's constructor, finds already-registered beans matching the parameter types, and passes them in — exactly Spring's autowiring algorithm in miniature.

### Level 3 — Advanced

Now use Spring's actual `ApplicationContext` via annotations. The container handles bean ordering, circular dependency detection, lifecycle callbacks, and AOP — all the things our mini-container omits.

```java
// SpringGoalsDemoV3.java — run with: java SpringGoalsDemoV3.java
// Requires: spring-context jar on classpath.
// To run standalone: compile with spring-context-6.x.jar + spring-beans + spring-core + spring-aop + spring-expression + commons-logging on classpath.
// In a Spring Boot app this is always available.

// This file shows the ANNOTATION-DRIVEN Spring pattern
// (not runnable as a single .java file without the Spring JARs, but
//  this is exactly the code you'd place in a Spring Boot project)

/*
@SpringBootApplication
public class SpringGoalsDemoV3 {

    @Service
    static class EmailService {
        void send(String to, String msg) {
            System.out.println("EMAIL to " + to + ": " + msg);
        }
    }

    @Service
    static class NotificationService {
        private final EmailService email;
        NotificationService(EmailService email) { this.email = email; }

        void notifyShipped(String customer, String trackingId) {
            email.send(customer, "Shipped! Track: " + trackingId);
        }
    }

    @Service
    static class OrderService {
        private final EmailService email;
        private final NotificationService notification;
        OrderService(EmailService e, NotificationService n) {
            this.email = e; this.notification = n;
        }

        @Transactional    // AOP: Spring wraps this in a transaction proxy
        public void placeOrder(String customer, String item) {
            System.out.println("Placing order: " + item);
            email.send(customer, "Order confirmed: " + item);
            notification.notifyShipped(customer, "TRK-" + item.hashCode());
        }
    }

    public static void main(String[] args) {
        ApplicationContext ctx = SpringApplication.run(SpringGoalsDemoV3.class, args);
        OrderService orders = ctx.getBean(OrderService.class);
        orders.placeOrder("alice@example.com", "Monitor");
    }
}
*/

// --- Self-contained illustration of Spring's goals without Spring JARs ---
public class SpringGoalsDemoV3 {

    interface MessageSender { void send(String to, String msg); }

    static class EmailSender implements MessageSender {
        public void send(String to, String msg) {
            System.out.println("[EMAIL]  to=" + to + "  msg=" + msg);
        }
    }

    static class SmsSender implements MessageSender {
        public void send(String to, String msg) {
            System.out.println("[SMS]    to=" + to + "  msg=" + msg);
        }
    }

    static class NotificationService {
        private final MessageSender sender;
        NotificationService(MessageSender sender) { this.sender = sender; }
        void notifyShipped(String customer, String trackingId) {
            sender.send(customer, "Shipped! Track: " + trackingId);
        }
    }

    static class OrderService {
        private final MessageSender email;
        private final NotificationService notification;
        OrderService(MessageSender email, NotificationService notification) {
            this.email = email; this.notification = notification;
        }
        void placeOrder(String customer, String item) {
            System.out.println("Order placed: " + item + " for " + customer);
            email.send(customer, "Order confirmed: " + item);
            notification.notifyShipped(customer, "TRK-" + Math.abs(item.hashCode() % 10000));
        }
    }

    // Production wiring: swap EmailSender for SmsSender without touching OrderService
    static Object[] wireProduction() {
        MessageSender email = new EmailSender();
        NotificationService notification = new NotificationService(new SmsSender()); // SMS for shipping
        OrderService orders = new OrderService(email, notification);
        return new Object[]{orders};
    }

    // Test wiring: inject a recording mock
    static class RecordingSender implements MessageSender {
        final java.util.List<String> sent = new java.util.ArrayList<>();
        public void send(String to, String msg) { sent.add(to + ": " + msg); }
    }

    public static void main(String[] args) {
        System.out.println("=== Production wiring ===");
        OrderService orders = (OrderService) wireProduction()[0];
        orders.placeOrder("alice@example.com", "Laptop");

        System.out.println("\n=== Test wiring (mock sender) ===");
        RecordingSender mock = new RecordingSender();
        OrderService testOrders = new OrderService(mock, new NotificationService(mock));
        testOrders.placeOrder("test@test.com", "Keyboard");
        System.out.println("Messages recorded: " + mock.sent);

        System.out.println("\n=== Spring goals demonstrated ===");
        System.out.println("  POJO: OrderService has no framework imports");
        System.out.println("  Testable: swap real sender for mock at construction time");
        System.out.println("  No lock-in: interface MessageSender works with Email or SMS");
        System.out.println("  In real Spring: @Service + constructor injection + @Transactional achieves all three");
    }
}
```

How to run: `java SpringGoalsDemoV3.java`

The `RecordingSender` shows testability: the test can verify exactly what messages were sent without touching a real email server. In a Spring project the only difference is that the container handles the wiring — your classes stay identical.

## 6. Walkthrough

**Entry point:** `main` calls `wireProduction()` which manually mirrors what `ApplicationContext` does.

**Step 1 — Dependency order.** `EmailSender` and `SmsSender` are constructed first because they have no dependencies. `NotificationService` comes next, receiving `SmsSender`. `OrderService` comes last, receiving both `EmailSender` and `NotificationService`.

**Step 2 — `placeOrder` executes.**
- `System.out.println("Order placed: ...")` — the business method runs.
- `email.send(customer, ...)` dispatches to `EmailSender.send` → prints `[EMAIL]`.
- `notification.notifyShipped(customer, trackingId)` calls `NotificationService`, which delegates to `SmsSender.send` → prints `[SMS]`.

**Step 3 — Test wiring.** The same `OrderService` class is constructed again, but both references point to `RecordingSender`. After `placeOrder` runs, `mock.sent` contains both messages — no real email or SMS was sent. `OrderService` is unaware of the swap.

**In real Spring:**
```
ApplicationContext startup:
  1. Scans classpath for @Service, @Component, @Repository, @Controller
  2. Reads @Autowired / constructor parameter types
  3. Builds a dependency graph (bean definition registry)
  4. Instantiates beans in dependency order (topological sort)
  5. Injects each dependency
  6. Calls @PostConstruct lifecycle methods
  7. Wraps beans in AOP proxies where needed (@Transactional, @Aspect)
```

The request/response flow for a real Spring web call:
```
HTTP GET /orders/42
  → DispatcherServlet (from ApplicationContext)
  → OrderController.getOrder(42)  ← injected OrderService
  → orderService.findById(42)     ← injected OrderRepository
  → SQL SELECT … FROM orders WHERE id = 42
  → Order entity returned up the stack
  → Jackson serialises to JSON
HTTP 200 {"id":42,"item":"Laptop","customer":"alice@example.com"}
```

Each layer received its dependency from the container — none called `new`.

## 7. Gotchas & takeaways

> **`@Autowired` on fields hides dependencies.** `@Autowired private EmailService email;` works but makes the dependency invisible to callers (including test constructors). Always prefer constructor injection: it makes dependencies explicit, works with `final`, and lets tests use `new OrderService(mockEmail)` without any Spring infrastructure.

> **The container manages singleton scope by default.** Every `@Component` is created once and shared. If your bean holds mutable state it will be shared across threads. Either make it stateless or use `@Scope("prototype")` for a new instance per request.

- Spring's core value is not the modules — it's the IoC container. Everything else (MVC, JPA, transactions) plugs into the same container.
- POJO design means your domain objects are portable: they compile and test without any Spring JAR on the classpath.
- Prefer interfaces over concrete classes as dependency types — it's the `MessageSender` trick: swap implementations without changing consumers.
- `ApplicationContext` extends `BeanFactory` (the simpler container); always use `ApplicationContext` in application code for full lifecycle support.
- Spring Framework is not Spring Boot. Boot adds auto-configuration and an embedded server on top of Framework. You can use Framework without Boot for libraries, tests, or traditional WAR deployments.
