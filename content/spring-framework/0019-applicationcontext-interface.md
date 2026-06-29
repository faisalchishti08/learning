---
card: spring-framework
gi: 19
slug: applicationcontext-interface
title: ApplicationContext interface
---

## 1. What it is

`ApplicationContext` is the central Spring interface for accessing the IoC container. It extends `BeanFactory` and adds everything needed for a real application: event publishing, internationalisation (i18n), resource loading, environment abstraction, and eager singleton initialisation.

Key capabilities beyond `BeanFactory`:

| Feature | API |
|---|---|
| Bean lookup (inherited) | `getBean(Class)`, `getBean(String)` |
| Event publishing | `publishEvent(ApplicationEvent)` |
| Message source (i18n) | `getMessage(String code, ...)` |
| Resource loading | `getResource("classpath:data.json")` |
| Environment | `getEnvironment().getProperty("db.url")` |
| Lifecycle management | `refresh()`, `close()`, `start()`, `stop()` |
| Bean enumeration | `getBeanDefinitionNames()`, `getBeansOfType(Class)` |

In practice you never instantiate `ApplicationContext` directly — you use one of its concrete implementations: `AnnotationConfigApplicationContext`, `ClassPathXmlApplicationContext`, etc.

In one sentence: **`ApplicationContext` is the full Spring container — it is `BeanFactory` plus events, environment, resources, and lifecycle.**

## 2. Why & when

Most Spring applications use `ApplicationContext` for every bean container need. The rare cases for raw `BeanFactory` are discussed in tutorial 18; everything else — web apps, CLI apps, batch jobs, integration tests — uses `ApplicationContext`.

The extra features matter in real apps:
- **Events** let beans communicate without hard coupling (`OrderService` publishes `OrderPlacedEvent`; `EmailService` listens).
- **i18n** lets you keep message strings in properties files and localise them.
- **Environment** provides a unified view of properties from files, system environment, and command-line args.
- **Eager init** fails fast — a misconfigured bean is discovered at startup, not when a production request hits it.

## 3. Core concept

`ApplicationContext` is the assembled application. After `refresh()` completes, every singleton bean is created, every `@Autowired` dependency is satisfied, every `@PostConstruct` has run, and every `BeanPostProcessor` has been applied.

```
ApplicationContext interface
  extends BeanFactory
  extends MessageSource          (i18n)
  extends ApplicationEventPublisher
  extends ResourcePatternResolver
  extends EnvironmentCapable
  extends Lifecycle
```

The container is both the factory and the event bus:
- Any bean can receive `ApplicationEvent` by implementing `ApplicationListener<E>`.
- Any bean can publish events by injecting `ApplicationEventPublisher` (the context itself satisfies this).

Spring Boot wraps `ApplicationContext` in `SpringApplication.run()`, returning a `ConfigurableApplicationContext`. You can still call all the methods above on the returned context.

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ApplicationContext extends BeanFactory and adds events, i18n, environment, resources, and lifecycle">
  <defs>
    <marker id="a19" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b19" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- BeanFactory -->
  <rect x="230" y="10" width="220" height="38" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="340" y="34" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">BeanFactory  (getBean, scope, type)</text>

  <!-- ApplicationContext box -->
  <rect x="150" y="70" width="380" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="340" y="92" fill="#79c0ff" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">ApplicationContext</text>
  <text x="340" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ events  + i18n  + resources  + environment  + lifecycle</text>

  <line x1="340" y1="48" x2="340" y2="68" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a19)"/>

  <!-- Feature boxes -->
  <rect x="10"  y="155" width="110" height="44" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="65"  y="174" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">getBean()</text>
  <text x="65"  y="190" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">inherited</text>

  <rect x="135" y="155" width="110" height="44" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="190" y="174" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">publishEvent()</text>
  <text x="190" y="190" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">event bus</text>

  <rect x="260" y="155" width="110" height="44" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="315" y="174" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">getMessage()</text>
  <text x="315" y="190" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">i18n / MessageSource</text>

  <rect x="385" y="155" width="110" height="44" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="440" y="174" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">getResource()</text>
  <text x="440" y="190" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ResourceLoader</text>

  <rect x="510" y="155" width="115" height="44" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="567" y="174" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">getEnvironment()</text>
  <text x="567" y="190" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">properties + profiles</text>

  <line x1="200" y1="120" x2="65"  y2="153" stroke="#6db33f" stroke-width="1" marker-end="url(#a19)"/>
  <line x1="260" y1="120" x2="190" y2="153" stroke="#6db33f" stroke-width="1" marker-end="url(#a19)"/>
  <line x1="320" y1="120" x2="315" y2="153" stroke="#6db33f" stroke-width="1" marker-end="url(#a19)"/>
  <line x1="390" y1="120" x2="440" y2="153" stroke="#6db33f" stroke-width="1" marker-end="url(#a19)"/>
  <line x1="450" y1="120" x2="567" y2="153" stroke="#6db33f" stroke-width="1" marker-end="url(#a19)"/>

  <text x="340" y="230" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">After refresh(): all singletons created, all deps injected, all post-processors applied</text>
</svg>

`ApplicationContext` is a superset of `BeanFactory`. After `refresh()` the container is fully assembled and all features are available.

## 5. Runnable example

Scenario: an order processing system where `OrderService` publishes events when an order is placed, and `AuditService` listens to those events. We start with basic bean lookup and evolve to full event-driven communication.

### Level 1 — Basic

Basic `ApplicationContext` usage: creating a context, looking up a bean, and calling it.

```java
// AppContextDemo.java — run with: java AppContextDemo.java
// Shows ApplicationContext API pattern without Spring JARs (plain simulation)
import java.util.*;

public class AppContextDemo {

    record Order(int id, String customer, String item) {}

    static class OrderService {
        private int nextId = 1;
        Order place(String customer, String item) {
            return new Order(nextId++, customer, item);
        }
    }

    // --- Minimal ApplicationContext simulation ---
    static class AppContext {
        private final Map<Class<?>, Object> beans = new LinkedHashMap<>();

        <T> void register(Class<T> type, T instance) { beans.put(type, instance); }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) {
            Object b = beans.get(type);
            if (b == null) throw new RuntimeException("No bean of type: " + type.getSimpleName());
            return (T) b;
        }

        String[] getBeanNames() {
            return beans.values().stream()
                .map(b -> b.getClass().getSimpleName()).toArray(String[]::new);
        }
    }

    public static void main(String[] args) {
        AppContext ctx = new AppContext();

        // Register beans (simulates Spring's component scan / @Bean)
        ctx.register(OrderService.class, new OrderService());

        System.out.println("=== Beans in context: " + Arrays.toString(ctx.getBeanNames()));

        OrderService svc = ctx.getBean(OrderService.class);
        Order o1 = svc.place("alice", "Laptop");
        Order o2 = svc.place("bob",   "Monitor");

        System.out.println("Placed: " + o1);
        System.out.println("Placed: " + o2);
    }
}
```

How to run: `java AppContextDemo.java`

`getBean(OrderService.class)` retrieves the singleton by type. The same instance is returned every time — a singleton shared across the application.

### Level 2 — Intermediate

Add event publishing. `OrderService` fires an `OrderPlacedEvent`; `AuditService` listens and records it — with zero direct coupling between them.

```java
// AppContextDemo2.java — run with: java AppContextDemo2.java
import java.util.*;

public class AppContextDemo2 {

    record Order(int id, String customer, String item) {}

    // --- Minimal event system ---
    static class OrderPlacedEvent { final Order order; OrderPlacedEvent(Order o) { order = o; } }

    interface ApplicationListener<E> { void onEvent(E event); }

    static class EventPublisher {
        private final Map<Class<?>, List<ApplicationListener<?>>> listeners = new HashMap<>();

        @SuppressWarnings("unchecked")
        <E> void register(Class<E> type, ApplicationListener<E> l) {
            listeners.computeIfAbsent(type, k -> new ArrayList<>()).add(l);
        }

        @SuppressWarnings("unchecked")
        <E> void publish(E event) {
            List<ApplicationListener<?>> ls = listeners.getOrDefault(event.getClass(), List.of());
            for (ApplicationListener<?> l : ls) ((ApplicationListener<E>) l).onEvent(event);
        }
    }

    static class OrderService {
        private final EventPublisher publisher;
        private int nextId = 1;

        OrderService(EventPublisher publisher) { this.publisher = publisher; }

        Order place(String customer, String item) {
            Order order = new Order(nextId++, customer, item);
            System.out.println("OrderService: placed " + order);
            publisher.publish(new OrderPlacedEvent(order));  // fire event
            return order;
        }
    }

    static class AuditService implements ApplicationListener<OrderPlacedEvent> {
        private final List<String> log = new ArrayList<>();

        public void onEvent(OrderPlacedEvent e) {
            String entry = "AUDIT id=" + e.order.id() + " customer=" + e.order.customer();
            log.add(entry);
            System.out.println("AuditService: " + entry);
        }

        List<String> getLog() { return Collections.unmodifiableList(log); }
    }

    public static void main(String[] args) {
        EventPublisher publisher = new EventPublisher();
        AuditService   audit     = new AuditService();
        publisher.register(OrderPlacedEvent.class, audit);

        OrderService orders = new OrderService(publisher);

        orders.place("alice", "Laptop");
        orders.place("bob",   "Monitor");

        System.out.println("\nAudit log: " + audit.getLog());
    }
}
```

How to run: `java AppContextDemo2.java`

`OrderService` never imports `AuditService`. It only publishes an event. Any number of listeners can react without `OrderService` knowing. In Spring, any `@Component` implementing `ApplicationListener<OrderPlacedEvent>` receives the event automatically.

### Level 3 — Advanced

Add environment property resolution and a typed `getMessage` (i18n) lookup — showing the full `ApplicationContext` feature set in one system.

```java
// AppContextDemo3.java — run with: java AppContextDemo3.java
import java.util.*;
import java.util.function.*;

public class AppContextDemo3 {

    record Order(int id, String customer, String item, double total) {}

    // --- Environment (property source) ---
    static class Environment {
        private final Map<String, String> props;
        Environment(Map<String, String> props) { this.props = props; }
        String getProperty(String key) { return props.getOrDefault(key, ""); }
        String getProperty(String key, String def) { return props.getOrDefault(key, def); }
    }

    // --- MessageSource (i18n) ---
    static class MessageSource {
        private final Map<String, String> messages;
        MessageSource(Map<String, String> msgs) { this.messages = msgs; }
        String getMessage(String code, Object... args) {
            String tmpl = messages.getOrDefault(code, code);
            for (int i = 0; i < args.length; i++) tmpl = tmpl.replace("{" + i + "}", String.valueOf(args[i]));
            return tmpl;
        }
    }

    // --- Event bus ---
    record OrderPlacedEvent(Order order) {}
    interface Listener<E> { void on(E e); }
    static class EventBus {
        private final Map<Class<?>, List<Listener<?>>> ls = new HashMap<>();
        @SuppressWarnings("unchecked")
        <E> void on(Class<E> t, Listener<E> l) { ls.computeIfAbsent(t, k -> new ArrayList<>()).add(l); }
        @SuppressWarnings("unchecked")
        <E> void fire(E e) { ls.getOrDefault(e.getClass(), List.of()).forEach(l -> ((Listener<E>)l).on(e)); }
    }

    // --- Services ---
    static class PricingService {
        private final Environment env;
        PricingService(Environment env) { this.env = env; }
        double computeTotal(String item) {
            double tax = Double.parseDouble(env.getProperty("tax.rate", "0.10"));
            double base = item.length() * 50.0;  // silly formula
            return base * (1 + tax);
        }
    }

    static class OrderService {
        private final PricingService pricing;
        private final EventBus events;
        private final MessageSource msg;
        private int nextId = 1;

        OrderService(PricingService pricing, EventBus events, MessageSource msg) {
            this.pricing = pricing; this.events = events; this.msg = msg;
        }

        Order place(String customer, String item) {
            double total = pricing.computeTotal(item);
            Order o = new Order(nextId++, customer, item, total);
            System.out.println(msg.getMessage("order.placed", o.id(), customer, item, total));
            events.fire(new OrderPlacedEvent(o));
            return o;
        }
    }

    static class EmailNotifier {
        private final MessageSource msg;
        EmailNotifier(MessageSource msg) { this.msg = msg; }
        void onOrderPlaced(OrderPlacedEvent e) {
            System.out.println("  [EMAIL] " + msg.getMessage("email.subject", e.order().id()));
            System.out.println("  [EMAIL] " + msg.getMessage("email.body",
                e.order().customer(), e.order().item(), e.order().total()));
        }
    }

    public static void main(String[] args) {
        // --- Wire the context ---
        Environment env = new Environment(Map.of(
            "tax.rate", "0.08",
            "app.name", "OrderHub"
        ));

        MessageSource msg = new MessageSource(Map.of(
            "order.placed",  "Order #{0} placed for {1}: {2} @ ${3,.2f}",
            "email.subject", "Your order #{0} is confirmed",
            "email.body",    "Hi {0}, your {1} costs ${2,.2f}"
        ));

        EventBus events = new EventBus();
        PricingService pricing = new PricingService(env);
        OrderService orders = new OrderService(pricing, events, msg);
        EmailNotifier notifier = new EmailNotifier(msg);

        events.on(OrderPlacedEvent.class, notifier::onOrderPlaced);

        System.out.println("App: " + env.getProperty("app.name"));
        System.out.println("Tax rate: " + env.getProperty("tax.rate") + "\n");

        orders.place("alice", "Laptop");
        System.out.println();
        orders.place("bob", "Monitor");
    }
}
```

How to run: `java AppContextDemo3.java`

The `Environment` holds typed properties (tax rate, app name) that services read without hardcoding. `MessageSource` provides parameterised messages that can be swapped for different locales. `EventBus` decouples `OrderService` from `EmailNotifier`. This mirrors exactly how Spring's `ApplicationContext` unifies all three concerns through a single container interface.

## 6. Walkthrough

**Wiring (container startup):**
1. `Environment` built from `Map` — holds `tax.rate=0.08`.
2. `MessageSource` built from message map.
3. `EventBus` created.
4. `PricingService` constructed with `Environment`.
5. `OrderService` constructed with `PricingService`, `EventBus`, `MessageSource`.
6. `EmailNotifier` constructed with `MessageSource`.
7. `events.on(OrderPlacedEvent.class, notifier::onOrderPlaced)` — registers the listener.

**`orders.place("alice", "Laptop")` execution, step by step:**
```
place("alice", "Laptop")
  → pricing.computeTotal("Laptop")
      → env.getProperty("tax.rate") → "0.08" → 0.08
      → base = "Laptop".length() * 50 = 6 * 50 = 300
      → total = 300 * 1.08 = 324.0
  → new Order(1, "alice", "Laptop", 324.0)
  → msg.getMessage("order.placed", 1, "alice", "Laptop", 324.0)
      → "Order #1 placed for alice: Laptop @ $324.00"
  → events.fire(new OrderPlacedEvent(order))
      → notifier.onOrderPlaced(event)
          → msg.getMessage("email.subject", 1) → "Your order #1 is confirmed"
          → msg.getMessage("email.body", "alice", "Laptop", 324.0)
              → "Hi alice, your Laptop costs $324.00"
```

**Data state at each layer:**

| Layer | Input | State/Output |
|---|---|---|
| `Environment.getProperty` | `"tax.rate"` | `"0.08"` → `0.08` |
| `PricingService.computeTotal` | `"Laptop"` | `300 * 1.08 = 324.0` |
| `OrderService.place` | customer + item | `Order(1, alice, Laptop, 324.0)` |
| `EventBus.fire` | `OrderPlacedEvent` | dispatches to `EmailNotifier` |
| `EmailNotifier.onOrderPlaced` | event | two formatted email lines |

In real Spring, `ApplicationContext.publishEvent()` sends the event synchronously to all `@EventListener` methods or `ApplicationListener` beans registered in the same context.

## 7. Gotchas & takeaways

> **Never call `getBean()` in application code outside of the entry point.** Injecting `ApplicationContext` and calling `getBean(SomeClass.class)` everywhere is the service-locator anti-pattern — it hides dependencies and defeats testability. Inject the specific bean you need instead.

> **`ApplicationContext.refresh()` is called once during startup.** Calling it again re-initialises the context from scratch, destroying all existing singletons. This is intentional for testing context hot-reloading but should never happen in a running production application.

- Spring Boot's `SpringApplication.run()` creates and refreshes a `ConfigurableApplicationContext` for you — you rarely call `refresh()` manually.
- Access `ApplicationContext` in a bean by implementing `ApplicationContextAware` or injecting `ApplicationContext` directly.
- Use `getBeansOfType(SomeInterface.class)` to discover all beans implementing an interface — useful for plugin registries.
- `ContextRefreshedEvent` fires after every successful `refresh()` — a good hook for post-startup initialisation that needs all beans to be ready.
- `@EventListener(ContextClosedEvent.class)` lets beans clean up resources when the container shuts down.
