---
card: spring-framework
gi: 82
slug: beannameaware
title: BeanNameAware
---

## 1. What it is

`BeanNameAware` is a Spring interface with one method — `setBeanName(String name)` — that Spring calls **before `@PostConstruct`** to inject the bean's own name as registered in the container. The name is the key in the `ApplicationContext`'s bean registry — typically the class name lowercased for `@Component` beans, or the method name for `@Bean` factory methods.

```java
import org.springframework.beans.factory.BeanNameAware;

@Component("orderService")
public class OrderService implements BeanNameAware {

    private String beanName;

    @Override
    public void setBeanName(String name) {
        this.beanName = name;  // "orderService" — injected by Spring before @PostConstruct
    }

    public void processOrder(String orderId) {
        System.out.printf("[%s] processing order %s%n", beanName, orderId);
    }
}
```

In one sentence: **`BeanNameAware.setBeanName()` lets a bean discover its own registered name in the Spring container — useful for logging, JMX naming, and diagnostic messages — fired before `@PostConstruct`, so the name is available during initialisation.**

## 2. Why & when

Use `BeanNameAware` when:

- A bean writes diagnostic or structured **log messages** that should include the bean name, especially when there are multiple instances registered under different names.
- A bean registers itself as a **JMX MBean** and needs its bean name for the `ObjectName`.
- A bean registers itself in a **shared registry** (metrics, health checks, tracing) and uses the bean name as the registration key.
- A framework bean needs to identify itself in error messages or stack trace labels.

Do NOT use `BeanNameAware` if you just need the class name — use `getClass().getSimpleName()` instead. `BeanNameAware` gives you the _registration_ name, which may differ from the class name (e.g., `@Component("myAlias")`).

## 3. Core concept

```
When is setBeanName() called?

  ① Constructor
  ② @Autowired / @Value injection
  ③ setBeanName(name)       ← BeanNameAware fires HERE (first Aware interface)
  ④ setBeanFactory / setApplicationContext (other Aware interfaces)
  ⑤ BeanPostProcessor.postProcessBeforeInitialization()
  ⑥ @PostConstruct / afterPropertiesSet() / init-method
  ⑦ BeanPostProcessor.postProcessAfterInitialization()
  ⑧ Bean ready

What name is passed?
  @Component          → class name lowercased:     "OrderService" → "orderService"
  @Component("myName") → explicit name:            "myName"
  @Bean               → method name:               method "createOrderService" → "createOrderService"
  XML <bean id="...">  → the id attribute value:   "orderServiceBean"
  @Bean(name={"a","b"}) → primary name: "a"        (only the first alias is passed)
  AliasFor / @AliasFor  → underlying bean name     (not the alias)
```

## 4. Diagram

<svg viewBox="0 0 680 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BeanNameAware position in lifecycle and example bean names">
  <defs>
    <marker id="a82" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="178" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">BeanNameAware fires first among Aware interfaces, before @PostConstruct</text>

  <!-- Lifecycle steps -->
  <rect x="10"  y="33" width="75"  height="30" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="47"  y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">① construct</text>
  <line x1="85" y1="48" x2="93" y2="48" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a82)"/>
  <rect x="96"  y="33" width="75"  height="30" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="133" y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">② inject</text>
  <line x1="171" y1="48" x2="179" y2="48" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a82)"/>
  <rect x="182" y="33" width="130" height="30" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.8"/>
  <text x="247" y="48" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">③ setBeanName()</text>
  <text x="247" y="60" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">← BeanNameAware</text>
  <line x1="312" y1="48" x2="320" y2="48" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a82)"/>
  <rect x="323" y="33" width="115" height="30" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="380" y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">④ other Aware</text>
  <line x1="438" y1="48" x2="446" y2="48" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a82)"/>
  <rect x="449" y="33" width="115" height="30" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="506" y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">⑤ @PostConstruct</text>

  <!-- Bean name examples -->
  <rect x="10" y="78" width="655" height="96" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.8"/>
  <text x="22" y="96" fill="#8b949e" font-size="9" font-family="monospace">How the bean name is determined — what setBeanName() receives:</text>
  <line x1="12" y1="100" x2="662" y2="100" stroke="#8b949e" stroke-width="0.5"/>
  <text x="22" y="115" fill="#6db33f" font-size="9" font-family="monospace">@Component                  → "orderService"  (class name lowercased)</text>
  <text x="22" y="129" fill="#6db33f" font-size="9" font-family="monospace">@Component("myAlias")       → "myAlias"       (explicit name wins)</text>
  <text x="22" y="143" fill="#8b949e" font-size="9" font-family="monospace">@Bean                       → "createDbPool"  (method name)</text>
  <text x="22" y="157" fill="#8b949e" font-size="9" font-family="monospace">@Bean(name="dbPool")        → "dbPool"        (explicit name wins)</text>
  <text x="22" y="167" fill="#8b949e" font-size="7.5" font-family="sans-serif">XML: &lt;bean id="beanId" .../&gt; → "beanId"</text>
</svg>

`setBeanName()` is the first Aware callback — the bean name is available from that point onward, including in `@PostConstruct`.

## 5. Runnable example

Scenario: multiple `ReportGenerator` instances registered under different names — each uses `BeanNameAware` to include its own name in generated report headers and metric keys.

### Level 1 — Basic

Single bean that logs its own name in every output line.

```java
// BeanNameAwareDemo.java — run with: java BeanNameAwareDemo.java
import java.util.*;

public class BeanNameAwareDemo {

    interface BeanNameAware { void setBeanName(String name); }

    static class ReportGenerator implements BeanNameAware {
        private String beanName;
        private final String reportType;

        ReportGenerator(String reportType) {
            this.reportType = reportType;
            System.out.println("  [CONSTRUCT] ReportGenerator type=" + reportType
                + " (beanName not yet set)");
        }

        @Override
        public void setBeanName(String name) {
            this.beanName = name;
            System.out.println("  [setBeanName] beanName='" + name + "'");
        }

        void postConstruct() {
            // beanName available here — setBeanName fired before @PostConstruct
            System.out.println("  [@PostConstruct] " + beanName + " ready (type=" + reportType + ")");
        }

        String generate(String title) {
            return String.format("[%s] %s Report: %s — generated at %d",
                beanName, reportType, title, System.currentTimeMillis());
        }
    }

    static ReportGenerator createBean(String name, String type) {
        ReportGenerator b = new ReportGenerator(type);
        b.setBeanName(name);    // Spring calls this
        b.postConstruct();      // @PostConstruct
        return b;
    }

    public static void main(String[] args) {
        System.out.println("=== Container starting ===");
        ReportGenerator salesGen  = createBean("salesReportGenerator",  "Sales");
        ReportGenerator auditGen  = createBean("auditReportGenerator",  "Audit");
        ReportGenerator financeGen = createBean("financeReportGenerator", "Finance");

        System.out.println("\n=== Generating reports ===");
        System.out.println(salesGen.generate("Q4 2025"));
        System.out.println(auditGen.generate("Annual Review"));
        System.out.println(financeGen.generate("Balance Sheet"));
    }
}
```

How to run: `java BeanNameAwareDemo.java`

Each bean's `generate()` output includes its own `beanName` in the prefix — useful when three instances of the same class produce different reports. The name is injected via `setBeanName()` before `@PostConstruct`, so it's available in the initialisation phase.

### Level 2 — Intermediate

`BeanNameAware` used for JMX-style registration: each bean registers itself with a shared registry under its own bean name.

```java
// BeanNameAwareDemo2.java — run with: java BeanNameAwareDemo2.java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class BeanNameAwareDemo2 {

    interface BeanNameAware { void setBeanName(String name); }

    // ── Shared registry (imagine MBeanServer or health-check registry) ─
    static class ServiceRegistry {
        private final Map<String, ServiceInfo> registered = new ConcurrentHashMap<>();

        void register(String name, ServiceInfo info) {
            registered.put(name, info);
            System.out.println("  [REGISTRY] registered '" + name + "' — " + info);
        }

        void printAll() {
            System.out.println("[REGISTRY] all services:");
            registered.forEach((k, v) -> System.out.println("  " + k + " → " + v));
        }

        ServiceInfo get(String name) { return registered.get(name); }
    }

    record ServiceInfo(String type, AtomicLong requestCount) {
        @Override public String toString() {
            return "ServiceInfo{type=" + type + ", requests=" + requestCount.get() + "}";
        }
    }

    // ── Service bean using BeanNameAware for registry key ────────────
    static class ManagedService implements BeanNameAware {
        private String        beanName;
        private final String  serviceType;
        private final ServiceRegistry registry;
        private ServiceInfo   info;

        ManagedService(String serviceType, ServiceRegistry registry) {
            this.serviceType = serviceType;
            this.registry    = registry;
        }

        @Override
        public void setBeanName(String name) {
            this.beanName = name;
            System.out.println("  [setBeanName] '" + name + "' (serviceType=" + serviceType + ")");
        }

        void postConstruct() {
            // Register under own bean name in the shared registry
            info = new ServiceInfo(serviceType, new AtomicLong());
            registry.register(beanName, info);
            System.out.println("  [@PostConstruct] '" + beanName + "' registered");
        }

        void handle(String request) {
            long count = info.requestCount().incrementAndGet();
            System.out.printf("  [%s] handling request '%s' (#%d)%n", beanName, request, count);
        }

        long requestCount() { return info.requestCount().get(); }
        String name()       { return beanName; }
    }

    static ManagedService createBean(String name, String type, ServiceRegistry reg) {
        ManagedService s = new ManagedService(type, reg);
        s.setBeanName(name);
        s.postConstruct();
        return s;
    }

    public static void main(String[] args) {
        System.out.println("=== Container starting ===");
        ServiceRegistry registry = new ServiceRegistry();
        ManagedService auth    = createBean("authService",    "Authentication",  registry);
        ManagedService payment = createBean("paymentService", "Payment",         registry);
        ManagedService notify  = createBean("notifyService",  "Notification",    registry);

        System.out.println("\n=== Handling requests ===");
        auth.handle("login:alice");
        auth.handle("login:bob");
        payment.handle("charge:$99.99");
        notify.handle("email:welcome");
        notify.handle("sms:verification");
        notify.handle("push:order-shipped");

        System.out.println("\n=== Registry state ===");
        registry.printAll();

        System.out.println("\n=== Per-service request counts ===");
        for (ManagedService s : List.of(auth, payment, notify))
            System.out.printf("  %s: %d requests%n", s.name(), s.requestCount());
    }
}
```

How to run: `java BeanNameAwareDemo2.java`

Each `ManagedService` registers itself in `ServiceRegistry` using its `beanName` as the key. If three services of the same class are registered under different names, each gets a separate entry in the registry. `BeanNameAware` provides the registration key without hardcoding strings in the class.

### Level 3 — Advanced

`BeanNameAware` in a base class — subclasses inherit name injection and use it for structured metrics tagging.

```java
// BeanNameAwareDemo3.java — run with: java BeanNameAwareDemo3.java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class BeanNameAwareDemo3 {

    interface BeanNameAware { void setBeanName(String name); }

    // ── Base class: handles BeanNameAware plumbing ─────────────────────
    static abstract class MetricPublishingBean implements BeanNameAware {
        protected String beanName;
        protected Map<String, AtomicLong> metrics = new ConcurrentHashMap<>();

        @Override
        public final void setBeanName(String name) {
            this.beanName = name;
            System.out.println("  [BASE.setBeanName] '" + name + "'");
            onBeanNameSet(name); // hook for subclasses
        }

        protected void onBeanNameSet(String name) {}  // optional hook

        protected void recordMetric(String key, long value) {
            // Tag metric with bean name: "beanName.key"
            String taggedKey = beanName + "." + key;
            metrics.computeIfAbsent(taggedKey, k -> new AtomicLong()).addAndGet(value);
        }

        void printMetrics() {
            System.out.println("  [METRICS for '" + beanName + "']");
            metrics.entrySet().stream()
                .sorted(Map.Entry.comparingByKey())
                .forEach(e -> System.out.println("    " + e.getKey() + " = " + e.getValue().get()));
        }
    }

    // ── Concrete subclass A ────────────────────────────────────────────
    static class ProductService extends MetricPublishingBean {
        private final List<String> products = new ArrayList<>();

        void postConstruct() {
            System.out.println("  [ProductService.@PostConstruct] beanName='" + beanName + "'");
            // pre-load seed data
            products.addAll(List.of("Notebook", "Pen", "Ruler"));
            recordMetric("startup.products", products.size());
        }

        List<String> search(String query) {
            long start = System.nanoTime();
            List<String> results = products.stream()
                .filter(p -> p.toLowerCase().contains(query.toLowerCase())).toList();
            long ms = (System.nanoTime() - start) / 1_000_000;
            recordMetric("search.calls",   1);
            recordMetric("search.results", results.size());
            recordMetric("search.latency_ms", ms);
            return results;
        }

        void addProduct(String name) {
            products.add(name);
            recordMetric("add.calls", 1);
        }
    }

    // ── Concrete subclass B ────────────────────────────────────────────
    static class OrderService extends MetricPublishingBean {
        private final List<String> orders = new ArrayList<>();

        @Override
        protected void onBeanNameSet(String name) {
            System.out.println("  [OrderService.onBeanNameSet] '" + name + "' — setting up early metric key prefix");
        }

        void postConstruct() {
            System.out.println("  [OrderService.@PostConstruct] beanName='" + beanName + "'");
            recordMetric("startup.orders", 0);
        }

        String placeOrder(String productId, String customerId) {
            String orderId = "ORD-" + (orders.size() + 1);
            orders.add(orderId);
            recordMetric("place.calls", 1);
            recordMetric("total.orders", orders.size());
            System.out.printf("  [%s] placed %s for product=%s customer=%s%n",
                beanName, orderId, productId, customerId);
            return orderId;
        }
    }

    static <T extends MetricPublishingBean> T createBean(T bean, String name) {
        bean.setBeanName(name);    // Spring calls this
        return bean;
    }

    public static void main(String[] args) {
        System.out.println("=== Container startup ===");
        ProductService products = createBean(new ProductService(), "productService");
        products.postConstruct();
        OrderService   orders   = createBean(new OrderService(),   "orderService");
        orders.postConstruct();

        System.out.println("\n=== Application ===");
        products.addProduct("Backpack");
        products.addProduct("Wallet");
        List<String> results = products.search("book");
        System.out.println("[SEARCH 'book'] " + results);

        orders.placeOrder("Notebook",  "customer:alice");
        orders.placeOrder("Backpack",  "customer:bob");
        orders.placeOrder("Pen",       "customer:alice");

        System.out.println("\n=== Metrics (bean name in key) ===");
        products.printMetrics();
        orders.printMetrics();
    }
}
```

How to run: `java BeanNameAwareDemo3.java`

The base class `MetricPublishingBean` handles `BeanNameAware` — subclasses just call `recordMetric()` and the metric key is automatically tagged with the bean name: `productService.search.calls`, `orderService.place.calls`. If two `ProductService` instances were registered under different names, their metrics would be separate. The `onBeanNameSet()` hook lets subclasses react early (before `@PostConstruct`).

## 6. Walkthrough

**Level 3 init sequence and metric key formation:**

```
createBean(new ProductService(), "productService"):
  ① new ProductService()                 → constructor, beanName=null
  ② setBeanName("productService")        ← BeanNameAware
      beanName = "productService"
      [BASE.setBeanName] 'productService'
  ③ products.postConstruct()
      products=[Notebook, Pen, Ruler]
      recordMetric("startup.products", 3)
        key = beanName + "." + "startup.products"
            = "productService.startup.products"

createBean(new OrderService(), "orderService"):
  ① new OrderService()                   → constructor
  ② setBeanName("orderService")
      [BASE.setBeanName] 'orderService'
      [OrderService.onBeanNameSet] 'orderService' ← override hook fires
  ③ orders.postConstruct()
      recordMetric("startup.orders", 0)
        key = "orderService.startup.orders"

Application:
  products.addProduct("Backpack")  → metric "productService.add.calls" = 1
  products.search("book")          → metric "productService.search.calls" = 1
  orders.placeOrder(...)           → metric "orderService.place.calls" = 1 (etc.)

Metrics output:
  productService.add.calls = 2
  productService.search.calls = 1
  productService.search.results = 1
  orderService.place.calls = 3
  orderService.total.orders = 3
```

## 7. Gotchas & takeaways

> **`setBeanName()` is called with the _primary_ bean name — not aliases.** If a bean is registered as `@Bean(name = {"primary", "alias1", "alias2"})`, `setBeanName()` receives `"primary"`. Aliases are stored separately in the context's alias registry.

> **`beanName` is `null` in the constructor.** `setBeanName()` fires after construction and after `@Autowired` injection — never access `beanName` in the constructor or in a field initialiser that depends on `beanName`.

- Using `BeanNameAware` in a base class (as in Level 3) is a clean pattern: subclasses never need to implement the interface themselves — they just use `beanName` via the protected field.
- Alternative to `BeanNameAware` for simpler cases: `@Value("#{beanName}")` — SpEL can inject the bean name as a string field without needing to implement an interface.
- `BeanNameAware` is the first Aware interface called. `BeanFactoryAware` and `ApplicationContextAware` fire after.
- In a Spring Boot test with `@MockBean`, the mock's name may differ from the real bean's name — don't rely on `BeanNameAware` in test doubles.
