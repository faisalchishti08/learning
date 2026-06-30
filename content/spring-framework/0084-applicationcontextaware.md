---
card: spring-framework
gi: 84
slug: applicationcontextaware
title: ApplicationContextAware
---

## 1. What it is

`ApplicationContextAware` is a Spring interface with one method — `setApplicationContext(ApplicationContext ctx)` — that Spring calls **before `@PostConstruct`** to give a bean direct access to the full `ApplicationContext`. `ApplicationContext` extends `BeanFactory` and adds event publication, message resolution (i18n), resource loading, and environment access — making it the Swiss Army knife of the Spring container.

```java
import org.springframework.context.ApplicationContext;
import org.springframework.context.ApplicationContextAware;

@Component
public class ServiceLocator implements ApplicationContextAware {

    private ApplicationContext ctx;

    @Override
    public void setApplicationContext(ApplicationContext ctx) {
        this.ctx = ctx;
    }

    public <T> T getService(Class<T> serviceType) {
        return ctx.getBean(serviceType);
    }

    public void publishOrderEvent(String orderId) {
        ctx.publishEvent(new OrderPlacedEvent(this, orderId));
    }
}
```

In one sentence: **`ApplicationContextAware` injects the full `ApplicationContext` into a bean before `@PostConstruct`, providing access to bean lookup, event publishing, i18n message resolution, resource loading, and environment — but prefer `@Autowired ApplicationContext` for simpler cases.**

## 2. Why & when

Use `ApplicationContextAware` when:

- You need **dynamic bean lookup** by name or type at runtime (service locator / plugin pattern).
- You need to **publish application events** programmatically from non-`@Component` code.
- You need access to `ApplicationContext` in a **static utility / holder** class that can't be `@Autowired` (the classic `ApplicationContextHolder` pattern for legacy code).
- You are writing a **framework component** that cannot take `@Autowired ApplicationContext` and must receive it via interface injection.

Simpler alternative: `@Autowired ApplicationContext ctx` achieves the same result for `@Component` beans. Use `ApplicationContextAware` only when you need the interface contract (testability, base class injection) or when `@Autowired` isn't available.

## 3. Core concept

```
ApplicationContext extends BeanFactory and adds:

BeanFactory (core IoC):
  getBean(name) / getBean(type) / containsBean(name)
  isSingleton / isPrototype / getType / getAliases

ApplicationContext adds:
  publishEvent(ApplicationEvent)        → fire events to @EventListener beans
  getMessage(code, args, locale)        → i18n message resolution (MessageSource)
  getResource(location)                 → load classpath/file/URL resources
  getEnvironment()                      → active profiles + properties
  getBeanDefinitionNames()              → all registered bean names
  getParent()                           → parent context (if hierarchical)
  getId() / getApplicationName()        → context identity

Firing order:
  ① Constructor
  ② @Autowired injection
  ③ setBeanName()      (BeanNameAware)
  ④ setBeanFactory()   (BeanFactoryAware)
  ⑤ setApplicationContext() ← ApplicationContextAware fires HERE
  ⑥ BeanPostProcessor.postProcessBeforeInitialization()
  ⑦ @PostConstruct / afterPropertiesSet / init-method
  ⑧ bean ready

ApplicationContextHolder pattern (static access for legacy code):
  @Component
  public class AppCtxHolder implements ApplicationContextAware {
      private static ApplicationContext ctx;
      @Override
      public void setApplicationContext(ApplicationContext c) { ctx = c; }
      public static ApplicationContext get()                  { return ctx; }
  }
```

## 4. Diagram

<svg viewBox="0 0 680 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ApplicationContextAware — fires after BeanFactoryAware, ApplicationContext capabilities">
  <defs>
    <marker id="a84" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="183" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">ApplicationContextAware — last Aware callback, gives full context access</text>

  <!-- Timeline -->
  <rect x="8"   y="33" width="60" height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="38"  y="51" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">construct</text>
  <line x1="68" y1="47" x2="74" y2="47" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a84)"/>
  <rect x="77"  y="33" width="60" height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="107" y="51" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">inject</text>
  <line x1="137" y1="47" x2="143" y2="47" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a84)"/>
  <rect x="146" y="33" width="80" height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="186" y="51" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">setBeanName</text>
  <line x1="226" y1="47" x2="232" y2="47" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a84)"/>
  <rect x="235" y="33" width="85" height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="277" y="51" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">setBeanFactory</text>
  <line x1="320" y1="47" x2="326" y2="47" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a84)"/>
  <rect x="329" y="33" width="120" height="28" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.8"/>
  <text x="389" y="47" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">setApplicationContext</text>
  <text x="389" y="58" fill="#6db33f" font-size="6.5" text-anchor="middle" font-family="sans-serif">← HERE (last Aware)</text>
  <line x1="449" y1="47" x2="455" y2="47" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a84)"/>
  <rect x="458" y="33" width="90" height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="503" y="51" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">@PostConstruct</text>

  <!-- Capabilities table -->
  <rect x="10" y="75" width="655" height="100" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.8"/>
  <text x="22" y="92" fill="#8b949e" font-size="9" font-family="monospace">ApplicationContext capabilities (via setApplicationContext):</text>
  <line x1="12" y1="96" x2="662" y2="96" stroke="#8b949e" stroke-width="0.5"/>
  <text x="22" y="111" fill="#6db33f" font-size="9" font-family="monospace">ctx.getBean(type/name)          → dynamic bean lookup</text>
  <text x="22" y="125" fill="#6db33f" font-size="9" font-family="monospace">ctx.publishEvent(event)         → fire application events</text>
  <text x="22" y="139" fill="#8b949e" font-size="9" font-family="monospace">ctx.getMessage(code, args, loc) → i18n message lookup</text>
  <text x="22" y="153" fill="#8b949e" font-size="9" font-family="monospace">ctx.getResource(location)       → load classpath/file/URL</text>
  <text x="22" y="167" fill="#8b949e" font-size="9" font-family="monospace">ctx.getEnvironment()            → properties + active profiles</text>
</svg>

`setApplicationContext()` fires last among Aware callbacks — the context is fully available before `@PostConstruct`.

## 5. Runnable example

Scenario: a `PluginDispatcher` that discovers plugin beans at startup via the `ApplicationContext` and dispatches incoming events to them at runtime — an extensible plugin system.

### Level 1 — Basic

`ApplicationContextAware` used to look up all beans of a given type after the context is ready.

```java
// ApplicationContextAwareDemo.java — run with: java ApplicationContextAwareDemo.java
import java.util.*;

public class ApplicationContextAwareDemo {

    interface ApplicationContextAware { void setApplicationContext(FakeCtx ctx); }

    // ── Plugin contract ───────────────────────────────────────────────
    interface EventPlugin { void onEvent(String eventType, String payload); String pluginName(); }

    // ── Concrete plugins ──────────────────────────────────────────────
    static class AuditPlugin    implements EventPlugin { @Override public void onEvent(String t, String p) { System.out.println("    [AUDIT]    " + t + " → " + p); } @Override public String pluginName() { return "auditPlugin"; } }
    static class MetricsPlugin  implements EventPlugin { @Override public void onEvent(String t, String p) { System.out.println("    [METRICS]  " + t + " counter++"); } @Override public String pluginName() { return "metricsPlugin"; } }
    static class AlertingPlugin implements EventPlugin { @Override public void onEvent(String t, String p) { if (t.contains("error")) System.out.println("    [ALERT]    ERROR detected! " + p); } @Override public String pluginName() { return "alertingPlugin"; } }

    // ── Fake ApplicationContext ────────────────────────────────────────
    static class FakeCtx {
        private final Map<String, Object> beans;
        FakeCtx(Map<String, Object> beans) { this.beans = beans; }
        @SuppressWarnings("unchecked")
        <T> Map<String, T> getBeansOfType(Class<T> type) {
            Map<String, T> result = new LinkedHashMap<>();
            beans.forEach((name, bean) -> { if (type.isInstance(bean)) result.put(name, type.cast(bean)); });
            return result;
        }
        int getBeanDefinitionCount() { return beans.size(); }
    }

    // ── Dispatcher: discovers plugins via ApplicationContext ──────────
    static class PluginDispatcher implements ApplicationContextAware {
        private FakeCtx ctx;
        private final List<EventPlugin> plugins = new ArrayList<>();

        @Override
        public void setApplicationContext(FakeCtx ctx) {
            this.ctx = ctx;
            System.out.println("  [setApplicationContext] context set, total beans=" + ctx.getBeanDefinitionCount());
        }

        void postConstruct() {
            // Discover all EventPlugin beans from context — extensible without code changes
            Map<String, EventPlugin> found = ctx.getBeansOfType(EventPlugin.class);
            plugins.addAll(found.values());
            System.out.println("  [@PostConstruct] discovered " + plugins.size() + " plugins: "
                + found.keySet());
        }

        void dispatch(String eventType, String payload) {
            System.out.println("[DISPATCH] event='" + eventType + "' payload='" + payload + "'");
            plugins.forEach(p -> p.onEvent(eventType, payload));
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Container starting ===");
        Map<String, Object> beans = new LinkedHashMap<>();
        beans.put("auditPlugin",    new AuditPlugin());
        beans.put("metricsPlugin",  new MetricsPlugin());
        beans.put("alertingPlugin", new AlertingPlugin());
        FakeCtx ctx = new FakeCtx(beans);

        PluginDispatcher dispatcher = new PluginDispatcher();
        dispatcher.setApplicationContext(ctx);   // ApplicationContextAware
        dispatcher.postConstruct();              // @PostConstruct

        System.out.println("\n=== Dispatching events ===");
        dispatcher.dispatch("order.placed",    "ORD-1001");
        dispatcher.dispatch("payment.error",   "DECLINED: insufficient funds");
        dispatcher.dispatch("order.shipped",   "ORD-1001");
    }
}
```

How to run: `java ApplicationContextAwareDemo.java`

`postConstruct()` calls `ctx.getBeansOfType(EventPlugin.class)` to discover all plugin implementations without knowing their names or count. Adding a new plugin to the context is enough — `PluginDispatcher` picks it up automatically.

### Level 2 — Intermediate

`ApplicationContextHolder` pattern for static context access — enabling legacy non-Spring code to use Spring beans.

```java
// ApplicationContextAwareDemo2.java — run with: java ApplicationContextAwareDemo2.java
import java.util.*;
import java.util.function.*;

public class ApplicationContextAwareDemo2 {

    interface ApplicationContextAware { void setApplicationContext(FakeCtx ctx); }

    static class FakeCtx {
        private final Map<String, Object> beans;
        FakeCtx(Map<String, Object> beans) { this.beans = beans; }
        @SuppressWarnings("unchecked")
        <T> T getBean(String name, Class<T> type) { return type.cast(Objects.requireNonNull(beans.get(name), "No bean: " + name)); }
        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) { return (T) beans.values().stream().filter(type::isInstance).findFirst().orElseThrow(); }
    }

    // ── Services in the context ───────────────────────────────────────
    static class UserService  { String findUser(String id) { return "User{id=" + id + ",name=Alice}"; } }
    static class OrderService { String placeOrder(String userId, String product) { return "ORD-" + (int)(Math.random()*9000+1000); } }

    // ── ApplicationContextHolder — static access for legacy code ──────
    static class AppCtxHolder implements ApplicationContextAware {
        private static volatile FakeCtx instance;

        @Override
        public void setApplicationContext(FakeCtx ctx) {
            instance = ctx;
            System.out.println("  [AppCtxHolder] context stored for static access");
        }

        static <T> T getBean(String name, Class<T> type) {
            if (instance == null) throw new IllegalStateException("Context not initialised");
            return instance.getBean(name, type);
        }

        static <T> T getBean(Class<T> type) {
            if (instance == null) throw new IllegalStateException("Context not initialised");
            return instance.getBean(type);
        }

        static boolean isInitialised() { return instance != null; }
    }

    // ── Legacy utility class (no @Autowired, no Spring injection) ─────
    static class LegacyOrderProcessor {
        // This class is instantiated by old code — it can't use @Autowired.
        // It uses AppCtxHolder to access Spring beans.
        String processOrder(String userId, String product) {
            System.out.println("  [LEGACY] processOrder called — fetching services via AppCtxHolder");
            UserService  users  = AppCtxHolder.getBean("userService", UserService.class);
            OrderService orders = AppCtxHolder.getBean(OrderService.class);
            String user  = users.findUser(userId);
            String ordId = orders.placeOrder(userId, product);
            return String.format("[LEGACY ORDER] %s placed order for '%s' → %s", user, product, ordId);
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Container starting ===");
        Map<String, Object> beans = new LinkedHashMap<>();
        beans.put("userService",  new UserService());
        beans.put("orderService", new OrderService());
        FakeCtx ctx = new FakeCtx(beans);

        AppCtxHolder holder = new AppCtxHolder();
        holder.setApplicationContext(ctx);  // Spring calls this

        System.out.println("\n=== Legacy code (not Spring-managed) uses AppCtxHolder ===");
        System.out.println("[isInitialised] " + AppCtxHolder.isInitialised());
        LegacyOrderProcessor legacyProc = new LegacyOrderProcessor(); // no Spring injection
        System.out.println(legacyProc.processOrder("U-42", "Notebook"));
        System.out.println(legacyProc.processOrder("U-17", "Backpack"));
    }
}
```

How to run: `java ApplicationContextAwareDemo2.java`

`AppCtxHolder.setApplicationContext()` stores the context in a `static` field. `LegacyOrderProcessor` is not a Spring bean — it can't be `@Autowired`. It calls `AppCtxHolder.getBean(...)` to retrieve `UserService` and `OrderService` at runtime.

### Level 3 — Advanced

`ApplicationContextAware` used to publish custom events — the dispatcher publishes, and multiple `@EventListener` beans react.

```java
// ApplicationContextAwareDemo3.java — run with: java ApplicationContextAwareDemo3.java
import java.util.*;

public class ApplicationContextAwareDemo3 {

    interface ApplicationContextAware { void setApplicationContext(FakeCtx ctx); }

    // ── Custom application event ───────────────────────────────────────
    record OrderEvent(String type, String orderId, String detail) {
        @Override public String toString() { return type + "[" + orderId + "]: " + detail; }
    }

    // ── Fake ApplicationContext that supports event publication ───────
    static class FakeCtx {
        private final List<Consumer<OrderEvent>> listeners = new ArrayList<>();
        @FunctionalInterface interface Consumer<T> { void accept(T t); }
        void addListener(Consumer<OrderEvent> l) { listeners.add(l); }
        void publishEvent(OrderEvent event) {
            System.out.println("  [publishEvent] " + event);
            listeners.forEach(l -> l.accept(event));
        }
        int getBeanDefinitionCount() { return 5; }
    }

    // ── @EventListener beans ──────────────────────────────────────────
    static class AuditListener {
        final List<String> log = new ArrayList<>();
        void onOrderEvent(OrderEvent e) { log.add(e.toString()); System.out.println("    [AUDIT] logged: " + e); }
    }

    static class NotificationListener {
        void onOrderEvent(OrderEvent e) {
            if ("placed".equals(e.type()))   System.out.println("    [NOTIFY] email sent for " + e.orderId());
            if ("cancelled".equals(e.type())) System.out.println("    [NOTIFY] cancellation alert for " + e.orderId());
        }
    }

    static class MetricsListener {
        final Map<String, Integer> counts = new LinkedHashMap<>();
        void onOrderEvent(OrderEvent e) {
            counts.merge(e.type(), 1, Integer::sum);
            System.out.println("    [METRICS] " + e.type() + " count=" + counts.get(e.type()));
        }
    }

    // ── Service using ApplicationContextAware to publish events ───────
    static class OrderService implements ApplicationContextAware {
        private FakeCtx ctx;
        private int orderSeq = 0;

        @Override
        public void setApplicationContext(FakeCtx ctx) {
            this.ctx = ctx;
            System.out.println("  [setApplicationContext] OrderService ready to publish events");
        }

        String placeOrder(String product, String customerId) {
            String orderId = "ORD-" + (++orderSeq);
            System.out.println("[placeOrder] " + orderId + " product=" + product);
            ctx.publishEvent(new OrderEvent("placed", orderId, "customer=" + customerId + " product=" + product));
            return orderId;
        }

        void cancelOrder(String orderId, String reason) {
            System.out.println("[cancelOrder] " + orderId + " reason=" + reason);
            ctx.publishEvent(new OrderEvent("cancelled", orderId, "reason=" + reason));
        }

        void shipOrder(String orderId) {
            System.out.println("[shipOrder] " + orderId);
            ctx.publishEvent(new OrderEvent("shipped", orderId, "carrier=FedEx"));
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Container starting ===");
        FakeCtx ctx = new FakeCtx();

        AuditListener        audit   = new AuditListener();
        NotificationListener notify  = new NotificationListener();
        MetricsListener      metrics = new MetricsListener();
        ctx.addListener(audit::onOrderEvent);
        ctx.addListener(notify::onOrderEvent);
        ctx.addListener(metrics::onOrderEvent);

        OrderService svc = new OrderService();
        svc.setApplicationContext(ctx);

        System.out.println("\n=== Processing orders ===");
        String o1 = svc.placeOrder("Notebook", "alice");
        String o2 = svc.placeOrder("Pen",      "bob");
        svc.shipOrder(o1);
        svc.cancelOrder(o2, "out of stock");
        String o3 = svc.placeOrder("Backpack", "alice");
        svc.shipOrder(o3);

        System.out.println("\n=== State after processing ===");
        System.out.println("[AUDIT LOG] " + audit.log);
        System.out.println("[METRICS]   " + metrics.counts);
    }
}
```

How to run: `java ApplicationContextAwareDemo3.java`

`OrderService.setApplicationContext()` stores the context. Each service operation publishes an `OrderEvent` via `ctx.publishEvent()`. Three listeners react: `AuditListener` logs every event, `NotificationListener` sends emails/alerts, `MetricsListener` counts event types. The event-driven design decouples `OrderService` from its observers.

## 6. Walkthrough

**Level 3 event flow for `placeOrder("Notebook", "alice")`:**

```
OrderService.placeOrder("Notebook", "alice"):
  orderId = "ORD-1"
  ctx.publishEvent(OrderEvent("placed", "ORD-1", "customer=alice product=Notebook"))
    → [publishEvent] placed[ORD-1]: customer=alice product=Notebook
    
    Listener 1: audit.onOrderEvent(event)
      log.add("placed[ORD-1]: customer=alice product=Notebook")
      → [AUDIT] logged: placed[ORD-1]: ...

    Listener 2: notify.onOrderEvent(event)
      event.type()="placed" → send email
      → [NOTIFY] email sent for ORD-1

    Listener 3: metrics.onOrderEvent(event)
      counts.merge("placed", 1, Integer::sum) → counts={placed:1}
      → [METRICS] placed count=1

Final state:
  audit.log = [placed[ORD-1]:..., placed[ORD-2]:..., shipped[ORD-1]:..., ...]
  metrics.counts = {placed:3, shipped:2, cancelled:1}
```

## 7. Gotchas & takeaways

> **`ApplicationContextAware` creates tight coupling to the Spring API.** The `ApplicationContextHolder` static pattern is especially risky — it makes the context globally accessible, which undermines testability and makes dependencies invisible. Use it only for genuine legacy integration where `@Autowired` isn't possible.

> **`ctx.getBean()` inside `@PostConstruct` can trigger circular dependency resolution.** If the bean you look up depends on the bean currently being initialised, Spring throws `BeanCurrentlyInCreationException`. Use `@Lazy` injection or an `ObjectProvider<T>` to break the cycle.

- `@Autowired ApplicationContext ctx` is functionally identical to `ApplicationContextAware.setApplicationContext()` for `@Component` beans — use `@Autowired` for application code; reserve `ApplicationContextAware` for framework code.
- In tests, `setApplicationContext()` is called by the test infrastructure — you can verify it's set in a `@SpringBootTest` by autowiring the context directly.
- `ApplicationContext.publishEvent()` fires synchronously by default — all listeners run on the publisher's thread before `publishEvent()` returns. Use `@Async @EventListener` for asynchronous dispatch.
- In a parent/child context hierarchy, `getBean()` walks up to the parent — so beans from the parent context are visible in the child's `ApplicationContext`.
