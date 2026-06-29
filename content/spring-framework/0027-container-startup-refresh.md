---
card: spring-framework
gi: 27
slug: container-startup-refresh
title: Container startup & refresh()
---

## 1. What it is

`refresh()` is the method that brings a Spring `ApplicationContext` to life. It orchestrates the complete container startup sequence: parsing configuration, running post-processors, creating all singleton beans, and firing the `ContextRefreshedEvent`.

Every `ApplicationContext` constructor that accepts a configuration source calls `refresh()` internally. You can also call it manually on a `GenericApplicationContext` or `ConfigurableApplicationContext` after programmatic setup.

The method signature lives in `ConfigurableApplicationContext`:

```java
void refresh() throws BeansException, IllegalStateException;
```

In one sentence: **`refresh()` is the 12-step startup sequence that transforms `BeanDefinition` metadata into a live, fully-wired container — the single most important method in Spring's container lifecycle.**

## 2. Why & when

Understanding `refresh()` matters because:

- **Startup failures surface here.** Missing beans, unsatisfied dependencies, invalid property values — all throw during `refresh()`, giving you a precise stack trace.
- **Post-processors apply here.** `@Transactional`, `@Async`, AOP proxies, `@Value` injection — all applied during `refresh()` via `BeanPostProcessor` and `BeanFactoryPostProcessor`.
- **Extension points live here.** Custom `BeanFactoryPostProcessor` implementations (e.g., for property variable substitution) run during `refresh()`. You hook into it to modify or register bean definitions before singletons are created.
- **Context hot-swap.** Some application frameworks call `refresh()` again (on an `AbstractRefreshableApplicationContext`) to pick up configuration changes — understanding the sequence tells you what state is re-initialized.

You call `refresh()` manually when:
- Using `GenericApplicationContext` (no auto-refresh in constructor).
- Setting active profiles or additional property sources *after* creating the context but *before* creating beans.

## 3. Core concept

`AbstractApplicationContext.refresh()` executes 12 sequential steps. They are grouped into three phases:

**Phase 1 — Preparation (steps 1–4):** Set up the bean factory, run `BeanFactoryPostProcessor`s that modify `BeanDefinition`s before beans are created.

**Phase 2 — Post-processors (steps 5–8):** Register `BeanPostProcessor`s that wrap beans after creation; initialize message source, event multicaster.

**Phase 3 — Instantiation (steps 9–12):** Create all singleton beans, call `SmartLifecycle.start()`, fire `ContextRefreshedEvent`.

```
refresh()
  1.  prepareRefresh()                       — validate environment, mark active
  2.  obtainFreshBeanFactory()               — (re)create BeanFactory, load defs
  3.  prepareBeanFactory(beanFactory)        — add standard BeanPostProcessors
  4.  postProcessBeanFactory(beanFactory)    — subclass hook (e.g., web features)
  5.  invokeBeanFactoryPostProcessors()      — run @PropertySource, @ComponentScan
  6.  registerBeanPostProcessors()           — register @Autowired, AOP processors
  7.  initMessageSource()                    — i18n MessageSource bean
  8.  initApplicationEventMulticaster()      — event bus
  9.  onRefresh()                            — subclass hook (e.g., web server start)
  10. registerListeners()                    — add ApplicationListener beans
  11. finishBeanFactoryInitialization()      — instantiate ALL singletons ← main work
  12. finishRefresh()                        — publish ContextRefreshedEvent, lifecycle
```

Steps 5 and 6 are the most important for understanding how annotations work: `ConfigurationClassPostProcessor` (step 5) scans and processes `@Configuration` classes; `AutowiredAnnotationBeanPostProcessor` (step 6) handles `@Autowired` injection.

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="refresh() 12 steps grouped into three phases: preparation, post-processors, instantiation">
  <defs>
    <marker id="a27" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Phase labels -->
  <text x="90"  y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Phase 1: Preparation</text>
  <text x="340" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Phase 2: Post-processors</text>
  <text x="580" y="14" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Phase 3: Instantiation</text>

  <!-- Phase 1 boxes -->
  <rect x="10"  y="22" width="155" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="87"  y="42" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1. prepareRefresh</text>
  <rect x="10"  y="58" width="155" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="87"  y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">2. obtainFreshBeanFactory</text>
  <rect x="10"  y="94" width="155" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="87"  y="114" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">3. prepareBeanFactory</text>
  <rect x="10"  y="130" width="155" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="87"  y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">4. postProcessBeanFactory</text>

  <!-- Phase 2 boxes -->
  <rect x="253" y="22" width="172" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="339" y="42" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">5. invokeBFPostProcessors</text>
  <rect x="253" y="58" width="172" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="339" y="78" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">6. registerBeanPostProcessors</text>
  <rect x="253" y="94" width="172" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="339" y="114" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">7. initMessageSource</text>
  <rect x="253" y="130" width="172" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="339" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">8. initEventMulticaster</text>

  <!-- Phase 3 boxes -->
  <rect x="505" y="22" width="165" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="587" y="42" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">9. onRefresh</text>
  <rect x="505" y="58" width="165" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="587" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">10. registerListeners</text>
  <rect x="505" y="94" width="165" height="46" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="587" y="115" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">11. finishBeanFactory</text>
  <text x="587" y="130" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Initialization ← main work</text>
  <rect x="505" y="148" width="165" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="587" y="168" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">12. finishRefresh → event</text>

  <!-- Arrows between phases -->
  <line x1="165" y1="90" x2="251" y2="90" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a27)"/>
  <line x1="425" y1="90" x2="503" y2="90" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a27)"/>

  <text x="340" y="215" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Steps 1-4: prepare  •  Steps 5-8: register processors  •  Steps 9-12: create beans + fire events</text>
  <text x="340" y="232" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Step 11 is where 99% of the work happens — all singletons instantiated in dependency order</text>
</svg>

Steps 1–10 prepare the container machinery. Step 11 is the main work: every singleton bean is created, every dependency injected, every `@PostConstruct` called. Step 12 fires `ContextRefreshedEvent` to signal that the context is live.

## 5. Runnable example

Scenario: a subscription billing system. `BillingService` depends on `PaymentGateway` and `InvoiceGenerator`. We simulate `refresh()` step by step, showing what happens at each phase.

### Level 1 — Basic

A minimal refresh: no post-processors, just bean creation in dependency order.

```java
// RefreshDemo.java — run with: java RefreshDemo.java
import java.util.*;
import java.util.function.*;

public class RefreshDemo {

    record Invoice(int id, String customer, double amount) {}

    static class InvoiceGenerator {
        private int nextId = 1000;
        Invoice generate(String customer, double amount) {
            return new Invoice(nextId++, customer, amount);
        }
    }

    static class PaymentGateway {
        boolean charge(String customer, double amount) {
            System.out.printf("  [GATEWAY] Charging %s: $%.2f → OK%n", customer, amount);
            return true;
        }
    }

    static class BillingService {
        private final PaymentGateway  gateway;
        private final InvoiceGenerator invoiceGen;
        BillingService(PaymentGateway gw, InvoiceGenerator ig) {
            this.gateway = gw; this.invoiceGen = ig;
        }
        void bill(String customer, double amount) {
            if (gateway.charge(customer, amount)) {
                Invoice inv = invoiceGen.generate(customer, amount);
                System.out.println("  [BILLING] Invoice generated: " + inv);
            }
        }
    }

    // --- Minimal refresh() simulation ---
    static class MinimalCtx {
        private final Map<Class<?>, Supplier<Object>> defs = new LinkedHashMap<>();
        private final Map<Class<?>, Object>           beans = new LinkedHashMap<>();
        private boolean active = false;

        <T> void register(Class<T> type, Supplier<T> factory) {
            defs.put(type, (Supplier<Object>) factory);
        }

        void refresh() {
            System.out.println("[REFRESH] Step 11: finishBeanFactoryInitialization...");
            for (var e : defs.entrySet()) {
                if (!beans.containsKey(e.getKey())) {
                    Object bean = e.getValue().get();
                    beans.put(e.getKey(), bean);
                    System.out.println("  Singleton ready: " + e.getKey().getSimpleName());
                }
            }
            active = true;
            System.out.println("[REFRESH] Step 12: ContextRefreshedEvent fired\n");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) {
            if (!active) throw new IllegalStateException("Context not refreshed");
            return (T) beans.entrySet().stream()
                .filter(e -> type.isAssignableFrom(e.getKey()))
                .map(Map.Entry::getValue).findFirst()
                .orElseThrow();
        }
    }

    public static void main(String[] args) {
        MinimalCtx ctx = new MinimalCtx();

        InvoiceGenerator ig = new InvoiceGenerator();
        PaymentGateway   gw = new PaymentGateway();

        ctx.register(InvoiceGenerator.class, () -> ig);
        ctx.register(PaymentGateway.class,   () -> gw);
        ctx.register(BillingService.class,   () -> new BillingService(gw, ig));

        ctx.refresh();  // creates all singletons

        BillingService billing = ctx.getBean(BillingService.class);
        billing.bill("alice", 49.99);
        billing.bill("bob",   99.00);
    }
}
```

How to run: `java RefreshDemo.java`

`refresh()` creates all three singletons in registration order. Calling `getBean()` before `refresh()` throws — the context is not active. After `refresh()` the same singletons are reused on every `getBean()` call.

### Level 2 — Intermediate

Add a `BeanFactoryPostProcessor` (step 5) that runs before singletons are created and modifies bean definitions — simulating `@PropertySource` and `PropertySourcesPlaceholderConfigurer`.

```java
// RefreshDemo2.java — run with: java RefreshDemo2.java
import java.util.*;
import java.util.function.*;

public class RefreshDemo2 {

    record Invoice(int id, String customer, double amount) {}

    static class PaymentGateway {
        private final String endpoint;
        PaymentGateway(String endpoint) { this.endpoint = endpoint; }
        boolean charge(String customer, double amount) {
            System.out.printf("  [GATEWAY:%s] Charging %s: $%.2f → OK%n", endpoint, customer, amount);
            return true;
        }
    }

    static class InvoiceGenerator {
        private final int startId;
        InvoiceGenerator(int startId) { this.startId = startId; }
        private int nextId = 0;
        Invoice generate(String customer, double amount) {
            return new Invoice(startId + nextId++, customer, amount);
        }
    }

    static class BillingService {
        private final PaymentGateway  gateway;
        private final InvoiceGenerator invoiceGen;
        BillingService(PaymentGateway gw, InvoiceGenerator ig) {
            this.gateway = gw; this.invoiceGen = ig;
        }
        void bill(String customer, double amount) {
            if (gateway.charge(customer, amount)) {
                System.out.println("  [BILLING] Invoice: " + invoiceGen.generate(customer, amount));
            }
        }
    }

    // --- BeanDefinition with configurable properties ---
    record BeanDefWithProps(String beanName, Map<String, String> props, Factory factory) {}
    interface Factory { Object create(Map<String, String> resolvedProps); }

    // --- BeanFactoryPostProcessor: resolves ${key} value expressions ---
    interface BeanFactoryPostProcessor {
        void postProcess(List<BeanDefWithProps> defs, Map<String, String> properties);
    }

    static class PropertyPlaceholderConfigurer implements BeanFactoryPostProcessor {
        private final Map<String, String> props;
        PropertyPlaceholderConfigurer(Map<String, String> props) { this.props = props; }
        public void postProcess(List<BeanDefWithProps> defs, Map<String, String> properties) {
            System.out.println("[STEP 5] PropertyPlaceholderConfigurer: resolving placeholders...");
            for (BeanDefWithProps def : defs) {
                for (var e : def.props().entrySet()) {
                    String val = e.getValue();
                    if (val.startsWith("${") && val.endsWith("}")) {
                        String key = val.substring(2, val.length() - 1);
                        String resolved = props.getOrDefault(key, val);
                        def.props().put(e.getKey(), resolved);
                        System.out.println("  Resolved " + def.beanName() + "." + e.getKey()
                            + ": " + val + " → " + resolved);
                    }
                }
            }
        }
    }

    static class TwoPhaseCtx {
        private final List<BeanDefWithProps>          defs      = new ArrayList<>();
        private final List<BeanFactoryPostProcessor>  bfpp      = new ArrayList<>();
        private final Map<Class<?>, Object>           beans     = new LinkedHashMap<>();

        void addBFPostProcessor(BeanFactoryPostProcessor pp) { bfpp.add(pp); }
        void registerDef(BeanDefWithProps def) { defs.add(def); }

        void refresh() {
            System.out.println("[REFRESH] Step 5: BeanFactoryPostProcessors...");
            Map<String, String> shared = new HashMap<>();
            for (var pp : bfpp) pp.postProcess(defs, shared);

            System.out.println("\n[REFRESH] Step 11: Creating singletons...");
            for (var def : defs) {
                Object bean = def.factory().create(def.props());
                beans.put(bean.getClass(), bean);
                System.out.println("  Ready: " + def.beanName());
            }
            System.out.println("[REFRESH] Step 12: ContextRefreshedEvent\n");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) {
            return (T) beans.entrySet().stream()
                .filter(e -> type.isAssignableFrom(e.getKey()))
                .map(Map.Entry::getValue).findFirst().orElseThrow();
        }
    }

    public static void main(String[] args) {
        TwoPhaseCtx ctx = new TwoPhaseCtx();

        // Simulates @PropertySource("classpath:app.properties")
        ctx.addBFPostProcessor(new PropertyPlaceholderConfigurer(Map.of(
            "gateway.endpoint", "https://payments.example.com/v2",
            "invoice.start.id", "5000"
        )));

        // Register beans with ${key} expressions resolved at refresh time
        Map<String, String> gwProps = new HashMap<>(Map.of("endpoint", "${gateway.endpoint}"));
        ctx.registerDef(new BeanDefWithProps("paymentGateway", gwProps,
            props -> new PaymentGateway(props.get("endpoint"))));

        Map<String, String> igProps = new HashMap<>(Map.of("startId", "${invoice.start.id}"));
        ctx.registerDef(new BeanDefWithProps("invoiceGenerator", igProps,
            props -> new InvoiceGenerator(Integer.parseInt(props.get("startId")))));

        // Closure captures already-registered beans
        PaymentGateway[]   gwRef = new PaymentGateway[1];
        InvoiceGenerator[] igRef = new InvoiceGenerator[1];
        ctx.registerDef(new BeanDefWithProps("billingService", new HashMap<>(), props -> {
            gwRef[0] = ctx.getBean(PaymentGateway.class);
            igRef[0] = ctx.getBean(InvoiceGenerator.class);
            return new BillingService(gwRef[0], igRef[0]);
        }));

        ctx.refresh();

        ctx.getBean(BillingService.class).bill("alice", 49.99);
        ctx.getBean(BillingService.class).bill("bob",   199.00);
    }
}
```

How to run: `java RefreshDemo2.java`

Step 5 (`BeanFactoryPostProcessor`) resolves `${gateway.endpoint}` → `https://payments.example.com/v2` **before** `PaymentGateway` is created. Step 11 then creates `PaymentGateway` with the resolved value. This is exactly how Spring's `@Value("${property}")` injection works.

### Level 3 — Advanced

Add a `BeanPostProcessor` (step 6) that wraps beans in timing proxies after creation — simulating how `@Transactional` and AOP proxies work.

```java
// RefreshDemo3.java — run with: java RefreshDemo3.java
import java.util.*;
import java.util.function.*;
import java.lang.reflect.*;

public class RefreshDemo3 {

    record Invoice(int id, String customer, double amount) {}

    interface PaymentGateway {
        boolean charge(String customer, double amount);
    }

    static class StripeGateway implements PaymentGateway {
        public boolean charge(String customer, double amount) {
            System.out.printf("  [STRIPE] Charging %s: $%.2f%n", customer, amount);
            return true;
        }
    }

    static class InvoiceGenerator {
        private int nextId = 1000;
        Invoice generate(String customer, double amount) {
            return new Invoice(nextId++, customer, amount);
        }
    }

    static class BillingService {
        private final PaymentGateway  gateway;
        private final InvoiceGenerator invoiceGen;
        BillingService(PaymentGateway gw, InvoiceGenerator ig) {
            this.gateway = gw; this.invoiceGen = ig;
        }
        Invoice bill(String customer, double amount) {
            if (gateway.charge(customer, amount)) {
                Invoice inv = invoiceGen.generate(customer, amount);
                System.out.println("  [BILLING] Invoice: " + inv);
                return inv;
            }
            throw new RuntimeException("Payment failed");
        }
    }

    // --- BeanPostProcessor: wraps all beans in a timing proxy ---
    interface BeanPostProcessor {
        Object postProcessAfterInitialization(Object bean, String name);
    }

    static class TimingBeanPostProcessor implements BeanPostProcessor {
        public Object postProcessAfterInitialization(Object bean, String name) {
            Class<?>[] ifaces = bean.getClass().getInterfaces();
            if (ifaces.length == 0) {
                System.out.println("  [BPP] Skipping proxy for " + name + " (no interface)");
                return bean;
            }
            System.out.println("  [BPP] Wrapping " + name + " in timing proxy");
            return Proxy.newProxyInstance(
                bean.getClass().getClassLoader(),
                ifaces,
                (proxy, method, args) -> {
                    long start = System.nanoTime();
                    Object result = method.invoke(bean, args);
                    long ms = (System.nanoTime() - start) / 1_000_000;
                    System.out.printf("    [TIMING] %s.%s: %dms%n", name, method.getName(), ms);
                    return result;
                }
            );
        }
    }

    static class FullRefreshCtx {
        record BeanEntry(String name, Class<?> type, Supplier<Object> factory) {}
        private final List<BeanPostProcessor> bpps   = new ArrayList<>();
        private final List<BeanEntry>         entries = new ArrayList<>();
        private final Map<Class<?>, Object>   beans  = new LinkedHashMap<>();
        private final Map<String,   Object>   named  = new LinkedHashMap<>();

        void addBeanPostProcessor(BeanPostProcessor pp) { bpps.add(pp); }
        void register(String name, Class<?> type, Supplier<Object> f) {
            entries.add(new BeanEntry(name, type, f));
        }

        void refresh() {
            System.out.println("[STEP 6] Registering BeanPostProcessors...");
            for (var pp : bpps) System.out.println("  Registered: " + pp.getClass().getSimpleName());

            System.out.println("\n[STEP 11] Creating singletons...");
            for (var e : entries) {
                Object raw = e.factory().get();
                System.out.println("  Created raw: " + e.name());
                // Apply all BeanPostProcessors
                Object processed = raw;
                for (var pp : bpps) processed = pp.postProcessAfterInitialization(processed, e.name());
                beans.put(e.type(), processed);
                named.put(e.name(), processed);
            }
            System.out.println("\n[STEP 12] ContextRefreshedEvent fired\n");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) {
            return (T) beans.entrySet().stream()
                .filter(en -> type.isAssignableFrom(en.getKey()))
                .map(Map.Entry::getValue).findFirst()
                .orElseThrow();
        }
    }

    public static void main(String[] args) {
        FullRefreshCtx ctx = new FullRefreshCtx();

        // Step 6: register BeanPostProcessor before singletons are created
        ctx.addBeanPostProcessor(new TimingBeanPostProcessor());

        // Register beans
        PaymentGateway   gw = new StripeGateway();
        InvoiceGenerator ig = new InvoiceGenerator();
        ctx.register("paymentGateway",  PaymentGateway.class, () -> gw);
        ctx.register("invoiceGenerator", InvoiceGenerator.class, () -> ig);
        ctx.register("billingService",  BillingService.class,
            () -> new BillingService(ctx.getBean(PaymentGateway.class), ig));

        ctx.refresh();

        System.out.println("=== Application running ===");
        BillingService billing = ctx.getBean(BillingService.class);
        billing.bill("alice", 49.99);
        System.out.println();
        billing.bill("bob", 199.00);
    }
}
```

How to run: `java RefreshDemo3.java`

`TimingBeanPostProcessor` wraps every interface-backed bean in a JDK proxy during step 11. `BillingService.bill()` calls `gateway.charge()` through the proxy — the timing interceptor measures and prints execution time. This is exactly how Spring's AOP (`@Transactional`, `@Cacheable`) works: `BeanPostProcessor`s replace beans with proxies that intercept method calls.

## 6. Walkthrough

**Level 3 — full refresh() sequence:**

```
ctx.refresh()

[STEP 6] Register BeanPostProcessors
  → TimingBeanPostProcessor registered

[STEP 11] Instantiate singletons
  "paymentGateway":
    → factory() → StripeGateway instance (raw)
    → TimingBeanPostProcessor.postProcessAfterInitialization(stripe, "paymentGateway")
        → StripeGateway implements PaymentGateway (interface exists)
        → Proxy.newProxyInstance(ifaces=[PaymentGateway], handler=timingHandler)
        → beans[PaymentGateway] = proxy wrapping StripeGateway

  "invoiceGenerator":
    → factory() → InvoiceGenerator (raw)
    → TimingBeanPostProcessor.postProcess → no interface → returned as-is

  "billingService":
    → factory() → ctx.getBean(PaymentGateway) → returns PROXY (not raw StripeGateway)
    → new BillingService(proxy, ig) — receives the proxy
    → TimingBeanPostProcessor.postProcess → no interface → returned as-is

[STEP 12] ContextRefreshedEvent fired
```

**`billing.bill("alice", 49.99)` call chain:**
```
billing.bill("alice", 49.99)
  → gateway.charge("alice", 49.99)
      ↑ gateway is a PROXY
      → InvocationHandler intercepts
      → start = nanoTime()
      → StripeGateway.charge("alice", 49.99)
          → "[STRIPE] Charging alice: $49.99"
          → returns true
      → elapsed = (nanoTime() - start) / 1_000_000 ms
      → "[TIMING] paymentGateway.charge: Xms"
  → invoiceGen.generate("alice", 49.99) → Invoice(1000, alice, 49.99)
  → "[BILLING] Invoice: Invoice[id=1000, customer=alice, amount=49.99]"
```

**Data state at each refresh() step:**

| Step | Container state |
|---|---|
| Before step 5 | `BeanDefinition`s with `${...}` placeholders |
| After step 5 | Placeholders resolved to real values |
| After step 6 | `BeanPostProcessor`s registered (no beans yet) |
| During step 11 | Raw beans created, then wrapped by post-processors |
| After step 12 | All beans are proxied singletons; `ContextRefreshedEvent` sent |

## 7. Gotchas & takeaways

> **`BeanPostProcessor` beans must be registered before step 6.** If you register a `BeanPostProcessor` as a regular `@Bean` inside a `@Configuration` class, it is detected automatically. But if your `@Configuration` class imports a bean that *uses* a `BeanPostProcessor` (e.g., `@Transactional`), that service bean must be created *after* step 6. Never use `@Transactional` on a bean created inside a `BeanFactoryPostProcessor` — the transaction proxy hasn't been registered yet.

> **`ContextRefreshedEvent` fires on every `refresh()` call, including Spring MVC's `DispatcherServlet` child context.** If you listen for `ContextRefreshedEvent` to run one-time startup logic, guard with a flag — otherwise it runs twice (once for root context, once for child).

- `@PostConstruct` methods run during step 11, *after* all dependencies are injected but *before* `ContextRefreshedEvent`. Safe to use for startup logic that needs the bean's own deps.
- `SmartLifecycle.start()` runs in step 12, after `ContextRefreshedEvent`. Use it for things that must start after the context is fully live (scheduler threads, message listener containers).
- `@EventListener(ContextRefreshedEvent.class)` is equivalent to `SmartLifecycle.start()` for simple use cases and easier to read.
- Calling `ctx.close()` triggers `ContextClosedEvent`, `SmartLifecycle.stop()`, `@PreDestroy`, and `DisposableBean.destroy()` in reverse order of bean creation.
- Spring Boot's DevTools calls `refresh()` on the child context after class reload (hot swap). This is why stateless singletons survive restarts cleanly while stateful objects (thread-local state, cached connections) can break.
