---
card: spring-framework
gi: 25
slug: genericapplicationcontext
title: GenericApplicationContext
---

## 1. What it is

`GenericApplicationContext` is the most flexible, lowest-level `ApplicationContext` implementation. Unlike `ClassPathXmlApplicationContext` or `AnnotationConfigApplicationContext`, it does **not** commit to a single configuration format at construction time. You populate it programmatically by registering `BeanDefinition` objects directly or by plugging in any `BeanDefinitionReader`.

```java
GenericApplicationContext ctx = new GenericApplicationContext();

// Register beans programmatically
ctx.registerBeanDefinition("orderService",
    BeanDefinitionBuilder.genericBeanDefinition(OrderService.class)
        .addConstructorArgReference("emailService")
        .getBeanDefinition());

// Or use a reader to load from a source
new XmlBeanDefinitionReader(ctx).loadBeanDefinitions("classpath:beans.xml");
new AnnotatedBeanDefinitionReader(ctx).register(AppConfig.class);

ctx.refresh();  // manual refresh required
```

Because `GenericApplicationContext` does not refresh itself in the constructor, you fully control *when* the container is initialized — essential for programmatic bean registration in tests or embedded scenarios.

In one sentence: **`GenericApplicationContext` is the flexible, format-agnostic context you use when you need programmatic bean registration, mixed sources, or precise refresh timing.**

## 2. Why & when

Use `GenericApplicationContext` when:

- **Programmatic bean registration** — you want to register `BeanDefinition` objects in code rather than using XML or annotations.
- **Mixing configuration sources** — load some beans from XML and others from a `@Configuration` class in the same context.
- **Framework development** — building tools that create Spring contexts on demand (test frameworks, plugin systems, embedded containers).
- **Precise refresh control** — you need to configure the environment or register post-processors *after* construction but *before* `refresh()`.

Spring Boot's `SpringApplication` internally uses `GenericWebApplicationContext` (a subclass) for the same reason — it needs to compose configuration from multiple auto-configuration classes discovered at runtime.

For everyday application code, prefer `AnnotationConfigApplicationContext` (Java config) or let Spring Boot handle it. Reach for `GenericApplicationContext` when you are writing infrastructure or test utilities.

## 3. Core concept

`GenericApplicationContext` holds a `DefaultListableBeanFactory` and delegates all bean management to it. The context itself adds the `ApplicationContext` features: events, environment, resources, and lifecycle.

```
GenericApplicationContext
  ├── holds DefaultListableBeanFactory  (registers/stores BeanDefinitions)
  └── extends AbstractApplicationContext (refresh lifecycle, events, env)

Programmatic registration:
  ctx.registerBeanDefinition(name, BeanDefinition)
  → stored in DefaultListableBeanFactory.beanDefinitionMap

ctx.refresh()
  → same 12-step lifecycle as all ApplicationContext implementations
  → finishBeanFactoryInitialization() — instantiate all singletons
```

`BeanDefinition` is the metadata object Spring stores for each bean. You can build one with:

```java
// Using builder (type-safe)
BeanDefinition def = BeanDefinitionBuilder
    .genericBeanDefinition(OrderService.class)
    .addConstructorArgReference("emailService")
    .setScope("singleton")
    .getBeanDefinition();

// Using RootBeanDefinition (low-level)
RootBeanDefinition rbd = new RootBeanDefinition(OrderService.class);
rbd.getConstructorArgumentValues().addIndexedArgumentValue(0, emailServiceRef);
```

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GenericApplicationContext with multiple registration paths converging to DefaultListableBeanFactory then refresh">
  <defs>
    <marker id="a25" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Input sources -->
  <rect x="10" y="10" width="160" height="38" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="90" y="34" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">registerBeanDefinition()</text>

  <rect x="10" y="65" width="160" height="38" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="90" y="89" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">XmlBeanDefinitionReader</text>

  <rect x="10" y="120" width="160" height="38" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="90" y="144" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">AnnotatedBeanDefReader</text>

  <!-- GenericApplicationContext / DefaultListableBeanFactory -->
  <rect x="245" y="40" width="185" height="90" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="337" y="65" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">GenericApplication</text>
  <text x="337" y="81" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Context</text>
  <text x="337" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">DefaultListableBeanFactory</text>
  <text x="337" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">beanDefinitionMap</text>

  <line x1="170" y1="29"  x2="243" y2="72"  stroke="#8b949e" stroke-width="1.5" marker-end="url(#a25)"/>
  <line x1="170" y1="84"  x2="243" y2="90"  stroke="#8b949e" stroke-width="1.5" marker-end="url(#a25)"/>
  <line x1="170" y1="139" x2="243" y2="108" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a25)"/>

  <!-- refresh() -->
  <rect x="505" y="50" width="165" height="70" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="587" y="74" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">refresh()</text>
  <text x="587" y="92" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">must be called manually</text>
  <text x="587" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">singletons ready after</text>

  <line x1="430" y1="85" x2="503" y2="85" stroke="#6db33f" stroke-width="2" marker-end="url(#a25)"/>

  <text x="340" y="190" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Any combination of readers/registrations → one context. refresh() always required.</text>
</svg>

Multiple registration paths feed into one `DefaultListableBeanFactory`. Unlike other `ApplicationContext` subclasses, `GenericApplicationContext` never refreshes automatically — you must call `refresh()`.

## 5. Runnable example

Scenario: an order fulfillment pipeline that is assembled from two teams' bean definitions — one team uses XML-style, another uses Java-config-style. `GenericApplicationContext` merges them into one context.

### Level 1 — Basic

Programmatic bean definition: register `BeanDefinition` objects directly in code — no XML, no annotations required.

```java
// GacDemo.java — run with: java GacDemo.java
import java.util.*;
import java.util.function.*;

public class GacDemo {

    record Order(int id, String customer, String item) {}

    static class EmailService {
        void sendConfirmation(Order o) {
            System.out.println("  [EMAIL] Confirmation → " + o.customer() + " for " + o.item());
        }
    }

    static class OrderService {
        private final EmailService email;
        OrderService(EmailService email) { this.email = email; }
        Order place(String customer, String item) {
            Order o = new Order((int)(Math.random()*1000), customer, item);
            System.out.println("  [ORDER] Placed: " + o);
            email.sendConfirmation(o);
            return o;
        }
    }

    // --- BeanDefinition (minimal) ---
    record BeanDef(Class<?> beanClass, List<String> ctorRefs) {}

    // --- GenericApplicationContext simulation ---
    static class GenericCtx {
        private final Map<String, BeanDef>    defs  = new LinkedHashMap<>();
        private final Map<String, Object>     beans = new LinkedHashMap<>();
        private boolean refreshed = false;

        // Programmatic registration — equivalent to ctx.registerBeanDefinition(name, def)
        void registerBeanDefinition(String name, Class<?> cls, String... ctorRefs) {
            if (refreshed) throw new IllegalStateException("Already refreshed");
            defs.put(name, new BeanDef(cls, List.of(ctorRefs)));
            System.out.println("  [REGISTER] " + name + " → " + cls.getSimpleName());
        }

        void refresh() throws Exception {
            System.out.println("[REFRESH] Instantiating singletons...");
            for (var e : defs.entrySet()) {
                BeanDef def = e.getValue();
                Object[] deps = def.ctorRefs().stream().map(beans::get).toArray();
                var ctor = def.beanClass().getDeclaredConstructors()[0];
                beans.put(e.getKey(), ctor.newInstance(deps));
                System.out.println("  Ready: " + e.getKey());
            }
            refreshed = true;
            System.out.println("[REFRESH] Complete\n");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) { return (T) beans.get(name); }
    }

    public static void main(String[] args) throws Exception {
        GenericCtx ctx = new GenericCtx();

        System.out.println("=== Programmatic registration ===");
        ctx.registerBeanDefinition("emailService", EmailService.class);
        ctx.registerBeanDefinition("orderService", OrderService.class, "emailService");

        ctx.refresh();  // manual — no auto-refresh

        OrderService svc = ctx.getBean("orderService");
        svc.place("alice", "Laptop");
        svc.place("bob",   "Monitor");
    }
}
```

How to run: `java GacDemo.java`

`registerBeanDefinition` stores metadata. Nothing is created until `refresh()` is called explicitly. After refresh, `getBean()` returns ready singletons. Calling `registerBeanDefinition` after `refresh()` throws — the context is sealed.

### Level 2 — Intermediate

Mix two registration sources: a "team A" XML-style loader and a "team B" Java-config loader — both feeding into one `GenericApplicationContext`.

```java
// GacDemo2.java — run with: java GacDemo2.java
import java.lang.annotation.*;
import java.util.*;
import java.util.function.*;

public class GacDemo2 {

    @Retention(RetentionPolicy.RUNTIME) @interface Bean {}

    record Order(int id, String customer, String item, double price) {}

    static class PriceEngine {
        double compute(String item) { return item.length() * 25.0; }
    }

    static class EmailService {
        void sendConfirmation(Order o) {
            System.out.printf("  [EMAIL] %s confirmed: %s @ $%.2f%n",
                o.customer(), o.item(), o.price());
        }
    }

    static class OrderService {
        private final PriceEngine  pricing;
        private final EmailService email;
        OrderService(PriceEngine pricing, EmailService email) {
            this.pricing = pricing; this.email = email;
        }
        Order place(String customer, String item) {
            double price = pricing.compute(item);
            Order o = new Order(new Random().nextInt(1000), customer, item, price);
            System.out.printf("  [ORDER] Placed: %s%n", o);
            email.sendConfirmation(o);
            return o;
        }
    }

    // --- Team B: Java-config (@Bean methods) ---
    static class TeamBConfig {
        @Bean EmailService emailService() { return new EmailService(); }
        @Bean PriceEngine  priceEngine()  { return new PriceEngine();  }
    }

    // --- GenericApplicationContext that accepts both sources ---
    static class GenericMultiSourceCtx {
        record BeanDef(Supplier<Object> factory) {}

        private final Map<String, BeanDef>  defs  = new LinkedHashMap<>();
        private final Map<String, Object>   beans = new LinkedHashMap<>();
        private final Map<Class<?>, Object> typed = new LinkedHashMap<>();

        // Source 1: XML-style (team A) — string-based definitions
        void loadXmlStyle(Map<String, Supplier<Object>> xmlDefs) {
            System.out.println("[XML READER] Loading team-A bean definitions...");
            xmlDefs.forEach((name, factory) -> {
                defs.put(name, new BeanDef(factory));
                System.out.println("  Defined: " + name);
            });
        }

        // Source 2: Java-config (team B) — @Bean methods via reflection
        void processConfig(Object config) throws Exception {
            System.out.println("[CONFIG READER] Loading team-B @Configuration...");
            for (var m : config.getClass().getDeclaredMethods()) {
                if (!m.isAnnotationPresent(Bean.class)) continue;
                final var method = m;
                defs.put(m.getName(), new BeanDef(() -> {
                    try { return method.invoke(config); }
                    catch (Exception e) { throw new RuntimeException(e); }
                }));
                System.out.println("  Defined: " + m.getName());
            }
        }

        void refresh() {
            System.out.println("[REFRESH] Instantiating all beans...");
            for (var e : defs.entrySet()) {
                Object bean = e.getValue().factory().get();
                beans.put(e.getKey(), bean);
                typed.put(bean.getClass(), bean);
                for (var iface : bean.getClass().getInterfaces()) typed.put(iface, bean);
                System.out.println("  Ready: " + e.getKey());
            }
            System.out.println("[REFRESH] Complete\n");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) {
            return (T) typed.entrySet().stream()
                .filter(e -> type.isAssignableFrom(e.getKey()))
                .map(Map.Entry::getValue).findFirst()
                .orElseThrow(() -> new RuntimeException("No bean: " + type.getSimpleName()));
        }
    }

    public static void main(String[] args) throws Exception {
        GenericMultiSourceCtx ctx = new GenericMultiSourceCtx();

        // Team A's definitions (XML-style)
        PriceEngine  pe    = new PriceEngine();
        EmailService email = new EmailService();
        ctx.loadXmlStyle(new LinkedHashMap<>(Map.of(
            "orderService", () -> new OrderService(pe, email)
        )));

        // Team B's definitions (Java-config)
        ctx.processConfig(new TeamBConfig());  // adds emailService + priceEngine

        ctx.refresh();  // merges both

        OrderService svc = ctx.getBean(OrderService.class);
        svc.place("alice", "Laptop");
        svc.place("bob",   "Keyboard");
    }
}
```

How to run: `java GacDemo2.java`

Team A registers `OrderService` via an XML-style map. Team B registers `EmailService` and `PriceEngine` via `@Bean` methods. Both end up in the same `GenericApplicationContext`. This is exactly how Spring Boot merges auto-configuration classes from multiple JARs — each contributes bean definitions to the same `GenericApplicationContext` during `refresh()`.

### Level 3 — Advanced

Add `BeanDefinitionRegistryPostProcessor` — a callback that runs before singletons are created and can register additional bean definitions programmatically. This is how Spring's `@ComponentScan` works internally.

```java
// GacDemo3.java — run with: java GacDemo3.java
import java.util.*;
import java.util.function.*;

public class GacDemo3 {

    record Order(int id, String customer, double amount) {}

    // Domain beans
    static class FraudDetector {
        boolean isSuspicious(Order o) { return o.amount() > 10000.0; }
    }

    static class NotificationService {
        void alert(String msg) { System.out.println("  [ALERT] " + msg); }
    }

    static class OrderValidator {
        private final FraudDetector detector;
        private final NotificationService notifier;
        OrderValidator(FraudDetector detector, NotificationService notifier) {
            this.detector = detector; this.notifier = notifier;
        }
        boolean validate(Order o) {
            if (detector.isSuspicious(o)) {
                notifier.alert("Suspicious order: " + o);
                return false;
            }
            System.out.println("  [VALID] Order OK: " + o);
            return true;
        }
    }

    // --- BeanDefinitionRegistryPostProcessor (fires before singletons, can add more defs) ---
    interface BeanDefinitionRegistryPostProcessor {
        void postProcessBeanDefinitionRegistry(Map<String, Supplier<Object>> registry);
    }

    // Dynamic registration: adds "fraudDetector" only if a system property says to
    static class FraudDetectorRegistrar implements BeanDefinitionRegistryPostProcessor {
        public void postProcessBeanDefinitionRegistry(Map<String, Supplier<Object>> registry) {
            System.out.println("  [POST-PROCESSOR] FraudDetectorRegistrar: registering extra bean");
            registry.put("fraudDetector",     FraudDetector::new);
            registry.put("notificationService", NotificationService::new);
        }
    }

    static class GenericAdvancedCtx {
        private final Map<String, Supplier<Object>>     defs       = new LinkedHashMap<>();
        private final Map<String, Object>               beans      = new LinkedHashMap<>();
        private final Map<Class<?>, Object>             typed      = new LinkedHashMap<>();
        private final List<BeanDefinitionRegistryPostProcessor> postProcs = new ArrayList<>();

        void registerBeanDefinition(String name, Supplier<Object> factory) {
            defs.put(name, factory);
            System.out.println("  [REGISTER] " + name);
        }

        void addRegistryPostProcessor(BeanDefinitionRegistryPostProcessor pp) {
            postProcs.add(pp);
        }

        void refresh() throws Exception {
            // 1. BeanDefinitionRegistryPostProcessors run BEFORE singletons
            System.out.println("[REFRESH] Step 1: BeanDefinitionRegistryPostProcessors...");
            for (var pp : postProcs) pp.postProcessBeanDefinitionRegistry(defs);

            // 2. Instantiate all singletons
            System.out.println("[REFRESH] Step 2: Instantiate singletons...");
            for (var e : defs.entrySet()) {
                Object bean = e.getValue().get();
                beans.put(e.getKey(), bean);
                typed.put(bean.getClass(), bean);
                for (var iface : bean.getClass().getInterfaces()) typed.put(iface, bean);
                System.out.println("  Ready: " + e.getKey());
            }
            System.out.println("[REFRESH] Complete\n");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) {
            return (T) typed.entrySet().stream()
                .filter(e -> type.isAssignableFrom(e.getKey()))
                .map(Map.Entry::getValue).findFirst()
                .orElseThrow(() -> new RuntimeException("No bean: " + type.getSimpleName()));
        }
    }

    public static void main(String[] args) throws Exception {
        GenericAdvancedCtx ctx = new GenericAdvancedCtx();

        // Register core bean — depends on FraudDetector and NotificationService
        // which will be added by the post-processor
        System.out.println("=== Registration phase ===");
        ctx.addRegistryPostProcessor(new FraudDetectorRegistrar());

        // orderValidator registered AFTER post-processor will add its deps
        ctx.registerBeanDefinition("orderValidator",
            () -> new OrderValidator(
                (FraudDetector)     ctx.getBean(FraudDetector.class),
                (NotificationService) ctx.getBean(NotificationService.class)
            )
        );

        System.out.println("\n=== Refresh ===");
        ctx.refresh();

        OrderValidator validator = ctx.getBean(OrderValidator.class);
        List.of(
            new Order(1, "alice", 250.00),
            new Order(2, "bob",   15000.00),
            new Order(3, "carol",  999.99)
        ).forEach(validator::validate);
    }
}
```

How to run: `java GacDemo3.java`

`FraudDetectorRegistrar.postProcessBeanDefinitionRegistry` fires during `refresh()` Step 1, adding `fraudDetector` and `notificationService` to the registry **before** any bean is instantiated. `OrderValidator` (Step 2) then finds them both available. This is how Spring's `ConfigurationClassPostProcessor` works: it scans `@Configuration` classes and registers all discovered `@Bean` definitions before singletons are created.

## 6. Walkthrough

**Level 3 — refresh() in two stages:**

**Stage 1 — BeanDefinitionRegistryPostProcessors:**
```
ctx.refresh()
  → for each postProcessor:
      FraudDetectorRegistrar.postProcessBeanDefinitionRegistry(defs)
        → defs.put("fraudDetector",      FraudDetector::new)
        → defs.put("notificationService", NotificationService::new)
  defs now contains: orderValidator, fraudDetector, notificationService
```

**Stage 2 — singleton instantiation (in registration order):**
```
"orderValidator" factory runs:
  → ctx.getBean(FraudDetector.class)
      → "fraudDetector" not yet in beans → factory runs → new FraudDetector()
      → cached in beans + typed
  → ctx.getBean(NotificationService.class)
      → "notificationService" factory runs → new NotificationService()
      → cached
  → new OrderValidator(fraudDetector, notificationService)
  → cached as "orderValidator"
```

**`validator.validate(Order(2, "bob", 15000.00))`:**
```
validate(Order{id=2, customer=bob, amount=15000.0})
  → detector.isSuspicious(o) → 15000 > 10000 → true
  → notifier.alert("Suspicious order: ...")
      → "[ALERT] Suspicious order: Order[id=2, customer=bob, amount=15000.0]"
  → returns false
```

**Data flow across stages:**

| Stage | Input | Output |
|---|---|---|
| Post-processor | `defs` map (1 entry) | `defs` map (3 entries) |
| Singleton init | 3 `BeanDef` suppliers | 3 singleton objects in `beans` |
| `validate(Order, 15000)` | `Order` amount | fraud check → alert → false |

## 7. Gotchas & takeaways

> **`GenericApplicationContext` is not refreshable.** After the first `refresh()`, calling `refresh()` again throws `IllegalStateException: GenericApplicationContext does not support multiple refresh attempts`. Use `GenericXmlApplicationContext` or the abstract refreshable variants if you need re-initialization (e.g., tests that rebuild the context).

> **`BeanDefinitionRegistryPostProcessor` is the correct hook for dynamic bean registration.** Do not register beans by calling `ctx.registerBeanDefinition()` after `refresh()` — singletons are already instantiated and the new definition will not be picked up by dependent beans. Always register before `refresh()` or inside a `BeanDefinitionRegistryPostProcessor`.

- `GenericApplicationContext` is the foundation of Spring Boot's internal context — you can retrieve it as `ConfigurableApplicationContext` from `SpringApplication.run()`.
- Use `ctx.getBeanFactory().registerSingleton("name", instance)` to manually inject a pre-built object (no factory, no lifecycle callbacks) — useful for injecting mocks in integration tests.
- `BeanDefinitionBuilder.genericBeanDefinition(Class).setScope("prototype").getBeanDefinition()` registers a prototype-scoped bean — a new instance is created on every `getBean()` call.
- `AnnotationConfigApplicationContext` extends `GenericApplicationContext` — it adds the annotation readers on top but inherits all programmatic registration capabilities.
- For tests, Spring's `@SpringExtension` wraps a `GenericApplicationContext` and caches it across tests in the same test class to avoid expensive re-initialization.
