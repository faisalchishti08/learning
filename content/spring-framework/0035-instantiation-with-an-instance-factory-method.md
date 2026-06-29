---
card: spring-framework
gi: 35
slug: instantiation-with-an-instance-factory-method
title: Instantiation with an instance factory method
---

## 1. What it is

**Instance factory method instantiation** tells Spring to create a bean by calling a **non-static** method on an already-registered factory bean.

```java
// In @Configuration class (most common form):
@Bean
public DataSourceFactory dataSourceFactory() {
    return new DataSourceFactory();      // factory bean registered first
}

@Bean
public DataSource dataSource() {
    return dataSourceFactory().create(); // instance method called on factory bean
}

// Low-level XML equivalent:
// <bean id="dataSourceFactory" class="DataSourceFactory"/>
// <bean id="dataSource" factory-bean="dataSourceFactory"
//                       factory-method="create"/>
```

The key difference from static factory: the method is called on an instance of a factory bean that Spring must itself create and manage.

In one sentence: **Instance factory method instantiation delegates bean creation to a method on another Spring-managed bean, enabling factory classes that hold state, configuration, or resources needed for creating the product bean.**

## 2. Why & when

Use instance factory methods when:

- **The factory needs state.** A `ConnectionPoolFactory` needs database credentials, pool sizes, and a clock — it is a stateful object that builds connection pools. Its `create()` method is not static because it reads from instance fields.
- **Factory implements an interface.** The factory itself is a bean with dependencies injected, making it testable and replaceable.
- **Delegating to a builder API.** `DataSourceBuilder.create().url(...).build()` must be called on an instance — a `@Bean` method in a `@Configuration` class handles this naturally.
- **The `FactoryBean<T>` interface** — Spring's built-in way to declare a factory bean (covered in the next tutorial).

The `@Bean` method pattern in Spring `@Configuration` classes is the modern instance factory method: the method runs on the config class instance, and Spring caches the results.

## 3. Core concept

```
BeanDefinition for "dataSource":
  factoryBeanName = "dataSourceFactory"  (the factory bean's name)
  factoryMethodName = "create"           (the instance method to call)

Instantiation:
  1. Get factory bean: ctx.getBean("dataSourceFactory")
                        → DataSourceFactory instance
  2. Call instance method: dataSourceFactory.create()
                        → DataSource instance
  3. Cache result as "dataSource" singleton
```

The factory bean and the product bean are separate singletons. The container creates the factory bean first, then uses it to create the product bean.

```
Container singleton cache:
  "dataSourceFactory" → DataSourceFactory (factory)
  "dataSource"        → DataSource        (product)
```

Both can be injected as separate beans. A factory bean can create multiple product beans.

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Instance factory method: factory bean created first, then its method called to create the product bean">
  <defs>
    <marker id="a35" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Factory bean creation -->
  <rect x="10" y="20" width="160" height="70" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="44" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">1. Create factory bean</text>
  <text x="90" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">DataSourceFactory</text>
  <text x="90" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">singleton in context</text>

  <!-- BeanDef -->
  <rect x="10" y="120" width="160" height="68" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="143" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">BeanDef "dataSource"</text>
  <text x="90" y="159" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">factoryBean=factory</text>
  <text x="90" y="174" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">factoryMethod="create"</text>

  <!-- 2. Invoke instance method -->
  <rect x="255" y="60" width="195" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="353" y="84" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">2. factory.create()</text>
  <text x="353" y="102" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">instance method on factory bean</text>

  <line x1="170" y1="55"  x2="253" y2="80"  stroke="#8b949e" stroke-width="1.5" marker-end="url(#a35)"/>
  <line x1="170" y1="154" x2="253" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a35)"/>

  <!-- Product bean -->
  <rect x="530" y="65" width="140" height="56" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="600" y="88" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">DataSource</text>
  <text x="600" y="106" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">product bean (singleton)</text>

  <line x1="450" y1="90" x2="528" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a35)"/>

  <text x="340" y="185" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Factory and product are separate singletons. Factory creates product; both injected independently.</text>
</svg>

The factory bean is created first as a managed singleton. Spring then calls its instance `create()` method to produce the product bean. Both live in the container.

## 5. Runnable example

Scenario: a `ReportGeneratorFactory` that holds report templates (loaded at startup from resources) and creates `ReportGenerator` instances. The factory is stateful — it cannot be static.

### Level 1 — Basic

Factory bean with a no-arg `create()` method produces a product bean.

```java
// InstanceFactoryDemo.java — run with: java InstanceFactoryDemo.java
import java.util.*;

public class InstanceFactoryDemo {

    record Report(String title, List<String> sections) {}

    // Product bean
    static class ReportGenerator {
        private final String template;
        ReportGenerator(String template) {
            System.out.println("  [PRODUCT] ReportGenerator created (template: " + template + ")");
            this.template = template;
        }
        Report generate(String subject, String... data) {
            List<String> sections = new ArrayList<>();
            sections.add("Title: " + subject + " [template=" + template + "]");
            sections.addAll(List.of(data));
            return new Report(subject, sections);
        }
    }

    // Factory bean — creates ReportGenerator instances
    static class ReportGeneratorFactory {
        private String defaultTemplate = "standard-v1";

        ReportGeneratorFactory() {
            System.out.println("  [FACTORY BEAN] ReportGeneratorFactory created");
        }

        // Instance factory method — Spring calls this on the factory bean
        ReportGenerator create() {
            System.out.println("  [FACTORY METHOD] create() called on factory bean");
            return new ReportGenerator(defaultTemplate);
        }

        void setDefaultTemplate(String t) { this.defaultTemplate = t; }
    }

    // Container supporting factory-bean / factory-method pattern
    static class FactoryBeanCtx {
        private final Map<String, Object> beans = new LinkedHashMap<>();

        void register(String name, Object bean) {
            beans.put(name, bean);
            System.out.println("  [CTX] Registered: '" + name + "' → " + bean.getClass().getSimpleName());
        }

        // factory-bean + factory-method instantiation
        void registerViaInstanceFactory(String productName, String factoryBeanName,
                                         String methodName) throws Exception {
            Object factory = beans.get(factoryBeanName);
            if (factory == null)
                throw new RuntimeException("Factory bean not found: " + factoryBeanName);
            Object product = factory.getClass().getDeclaredMethod(methodName).invoke(factory);
            beans.put(productName, product);
            System.out.println("  [CTX] '" + productName + "' created via " + factoryBeanName
                + "." + methodName + "()");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) { return (T) beans.get(name); }
    }

    public static void main(String[] args) throws Exception {
        FactoryBeanCtx ctx = new FactoryBeanCtx();

        System.out.println("=== Container startup ===");
        ctx.register("reportGeneratorFactory", new ReportGeneratorFactory());
        ctx.registerViaInstanceFactory("reportGenerator", "reportGeneratorFactory", "create");

        System.out.println("\n=== Application using the product bean ===");
        ReportGenerator gen = ctx.getBean("reportGenerator");
        Report r = gen.generate("Q1 Sales",
            "Total revenue: $1.2M", "YoY growth: +18%", "Top region: APAC");
        System.out.println("  Report: " + r.title());
        r.sections().forEach(s -> System.out.println("    " + s));
    }
}
```

How to run: `java InstanceFactoryDemo.java`

`reportGeneratorFactory` is created first and registered as its own singleton. `reportGenerator` is created by calling `create()` on that factory — an instance method call. Both `reportGeneratorFactory` and `reportGenerator` exist independently in the container and can be injected separately.

### Level 2 — Intermediate

Stateful factory: the factory holds injected configuration and creates product beans that reflect that state.

```java
// InstanceFactoryDemo2.java — run with: java InstanceFactoryDemo2.java
import java.util.*;
import java.util.function.*;

public class InstanceFactoryDemo2 {

    record EmailMessage(String from, String to, String subject, String body) {}

    // Product bean
    static class EmailSender {
        private final String host;
        private final int    port;
        private final String from;

        EmailSender(String host, int port, String from) {
            this.host = host; this.port = port; this.from = from;
            System.out.println("  [PRODUCT] EmailSender(" + host + ":" + port + " from=" + from + ")");
        }

        void send(String to, String subject, String body) {
            EmailMessage m = new EmailMessage(from, to, subject, body);
            System.out.printf("  [EMAIL %s:%d] %s → %s | %s%n", host, port, m.from(), m.to(), m.subject());
        }
    }

    // Stateful factory bean — holds SMTP config, creates EmailSender instances
    static class EmailSenderFactory {
        private final String smtpHost;
        private final int    smtpPort;
        private final String senderAddress;

        // Factory itself is injected with config
        EmailSenderFactory(String host, int port, String sender) {
            this.smtpHost = host; this.smtpPort = port; this.senderAddress = sender;
            System.out.println("  [FACTORY BEAN] EmailSenderFactory created (host=" + host + ")");
        }

        // Instance factory method
        EmailSender createSender() {
            System.out.println("  [FACTORY METHOD] EmailSenderFactory.createSender()");
            return new EmailSender(smtpHost, smtpPort, senderAddress);
        }

        // Can create specialized variants
        EmailSender createNoReplySender() {
            System.out.println("  [FACTORY METHOD] EmailSenderFactory.createNoReplySender()");
            return new EmailSender(smtpHost, smtpPort, "noreply@" + smtpHost.replace("smtp.", ""));
        }
    }

    static class NotificationService {
        private final EmailSender mainSender;
        private final EmailSender noReplySender;

        NotificationService(EmailSender mainSender, EmailSender noReplySender) {
            this.mainSender = mainSender; this.noReplySender = noReplySender;
            System.out.println("  [BEAN] NotificationService created");
        }

        void sendWelcome(String user) {
            mainSender.send(user, "Welcome!", "Thanks for joining.");
        }

        void sendOrderConfirmation(String user, String orderId) {
            noReplySender.send(user, "Order #" + orderId + " confirmed", "Your order is confirmed.");
        }
    }

    static class StatefulFactoryCtx {
        private final Map<String, Object> beans = new LinkedHashMap<>();

        void register(String name, Object b) { beans.put(name, b); }

        void registerViaFactory(String productName, String factoryName, String method) throws Exception {
            Object factory = beans.get(factoryName);
            Object product = factory.getClass().getDeclaredMethod(method).invoke(factory);
            beans.put(productName, product);
            System.out.println("  [CTX] '" + productName + "' ← " + factoryName + "." + method + "()");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String n) { return (T) beans.get(n); }
    }

    public static void main(String[] args) throws Exception {
        StatefulFactoryCtx ctx = new StatefulFactoryCtx();

        System.out.println("=== Container startup ===");
        // 1. Register the stateful factory bean (with config injected)
        ctx.register("emailSenderFactory",
            new EmailSenderFactory("smtp.example.com", 587, "support@example.com"));

        // 2. Create product beans via factory instance methods
        ctx.registerViaFactory("mainEmailSender",    "emailSenderFactory", "createSender");
        ctx.registerViaFactory("noReplyEmailSender", "emailSenderFactory", "createNoReplySender");

        // 3. Wire the notification service with both product beans
        ctx.register("notificationService",
            new NotificationService(
                ctx.getBean("mainEmailSender"),
                ctx.getBean("noReplyEmailSender")
            )
        );

        System.out.println("\n=== Application running ===");
        NotificationService svc = ctx.getBean("notificationService");
        svc.sendWelcome("alice@example.com");
        svc.sendOrderConfirmation("bob@example.com", "ORD-42");
    }
}
```

How to run: `java InstanceFactoryDemo2.java`

`EmailSenderFactory` is injected with `smtpHost`, `smtpPort`, and `senderAddress` — it is a stateful factory. Two product beans (`mainEmailSender`, `noReplyEmailSender`) are created by calling different instance methods on the same factory. The factory's state (SMTP config) is shared by both products.

### Level 3 — Advanced

Multiple product beans from one factory, lazy creation, and factory bean with its own lifecycle.

```java
// InstanceFactoryDemo3.java — run with: java InstanceFactoryDemo3.java
import java.util.*;
import java.util.function.*;

public class InstanceFactoryDemo3 {

    // Product: a database table accessor
    static class TableAccessor {
        private final String tableName;
        private final List<Map<String, Object>> data = new ArrayList<>();
        private int nextId = 1;

        TableAccessor(String tableName) {
            System.out.println("  [PRODUCT] TableAccessor(table=" + tableName + ")");
            this.tableName = tableName;
        }

        void insert(Map<String, Object> row) {
            Map<String, Object> r = new HashMap<>(row);
            r.put("id", nextId++);
            data.add(r);
            System.out.println("  [DB:" + tableName + "] INSERT " + r);
        }

        List<Map<String, Object>> findAll() { return Collections.unmodifiableList(data); }
        String getTableName() { return tableName; }
    }

    // Factory bean that creates TableAccessor instances — one per table
    static class DatabaseFactory {
        private final String schema;
        private boolean initialized = false;
        private final Map<String, TableAccessor> accessors = new LinkedHashMap<>();

        DatabaseFactory(String schema) {
            this.schema = schema;
            System.out.println("  [FACTORY BEAN] DatabaseFactory(schema=" + schema + ") created");
        }

        void init() {
            initialized = true;
            System.out.println("  [@PostConstruct] DatabaseFactory.init() — connected to schema: " + schema);
        }

        void destroy() {
            System.out.println("  [@PreDestroy] DatabaseFactory.destroy() — closing schema: " + schema);
        }

        // Instance factory method — creates a TableAccessor for a given table
        TableAccessor createAccessor(String table) {
            if (!initialized) throw new IllegalStateException("Factory not initialized");
            return accessors.computeIfAbsent(schema + "." + table, TableAccessor::new);
        }

        int accessorCount() { return accessors.size(); }
    }

    static class OrderRepository {
        private final TableAccessor orders;
        private final TableAccessor orderItems;

        OrderRepository(TableAccessor orders, TableAccessor orderItems) {
            this.orders = orders; this.orderItems = orderItems;
            System.out.println("  [BEAN] OrderRepository wired");
        }

        void save(String customer, List<String> items, double total) {
            orders.insert(Map.of("customer", customer, "total", total));
            items.forEach(item -> orderItems.insert(Map.of("item", item, "order_customer", customer)));
        }

        void showAll() {
            System.out.println("  orders: " + orders.findAll().size() + " rows");
            System.out.println("  order_items: " + orderItems.findAll().size() + " rows");
        }
    }

    static class LifecycleCtx {
        private final Map<String, Object> beans   = new LinkedHashMap<>();
        private final List<Object>        created = new ArrayList<>();

        void register(String name, Object b, boolean callInit) throws Exception {
            if (callInit) {
                b.getClass().getDeclaredMethod("init").invoke(b);
            }
            beans.put(name, b);
            created.add(b);
        }

        void registerViaFactory(String name, String factoryName, String method, Object... args) throws Exception {
            Object factory = beans.get(factoryName);
            Class<?>[] argTypes = Arrays.stream(args).map(Object::getClass).toArray(Class[]::new);
            Object bean = factory.getClass().getDeclaredMethod(method, argTypes).invoke(factory, args);
            beans.put(name, bean);
            System.out.println("  [CTX] '" + name + "' created via " + factoryName + "." + method + "()");
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String n) { return (T) beans.get(n); }

        void close() throws Exception {
            List<Object> reversed = new ArrayList<>(created);
            Collections.reverse(reversed);
            for (Object b : reversed) {
                try { b.getClass().getDeclaredMethod("destroy").invoke(b); }
                catch (NoSuchMethodException ignored) {}
            }
        }
    }

    public static void main(String[] args) throws Exception {
        LifecycleCtx ctx = new LifecycleCtx();

        System.out.println("=== Container startup ===");
        ctx.register("dbFactory", new DatabaseFactory("shop"), true);

        // Two product beans from the same factory
        ctx.registerViaFactory("ordersTable",      "dbFactory", "createAccessor", "orders");
        ctx.registerViaFactory("orderItemsTable",  "dbFactory", "createAccessor", "order_items");

        ctx.getBean("ordersTable");  // verify
        DatabaseFactory factory = ctx.getBean("dbFactory");
        System.out.println("  Factory accessor count: " + factory.accessorCount());

        ctx.register("orderRepository",
            new OrderRepository(ctx.getBean("ordersTable"), ctx.getBean("orderItemsTable")),
            false);

        System.out.println("\n=== Application running ===");
        OrderRepository repo = ctx.getBean("orderRepository");
        repo.save("alice", List.of("Laptop", "Mouse"),  1349.00);
        repo.save("bob",   List.of("Monitor"),            449.00);

        System.out.println("\n=== Data summary ===");
        repo.showAll();

        System.out.println("\n=== Shutdown ===");
        ctx.close();
    }
}
```

How to run: `java InstanceFactoryDemo3.java`

`DatabaseFactory` has its own lifecycle (`init()` / `destroy()`). Two `TableAccessor` product beans are created by the same factory via different calls to `createAccessor(tableName)`. The factory caches accessors internally — calling `createAccessor("orders")` twice returns the same instance. Both product beans are then injected into `OrderRepository`.

## 6. Walkthrough

**Level 3 — full lifecycle:**

```
ctx.register("dbFactory", new DatabaseFactory("shop"), callInit=true)
  → DatabaseFactory("shop") created → "[FACTORY BEAN] ..."
  → dbFactory.init() called → "[PostConstruct] DatabaseFactory.init()"
  → initialized = true

ctx.registerViaFactory("ordersTable", "dbFactory", "createAccessor", "orders")
  → factory = beans["dbFactory"] = DatabaseFactory
  → factory.createAccessor("orders")
      → initialized=true → proceed
      → accessors.computeIfAbsent("shop.orders", TableAccessor::new)
          → new TableAccessor("shop.orders") → "[PRODUCT] ..."
      → return accessor
  → beans["ordersTable"] = TableAccessor("shop.orders")
```

**`repo.save("alice", [...], 1349.00)`:**
```
save("alice", ["Laptop", "Mouse"], 1349.00)
  → orders.insert({customer: alice, total: 1349.0})
      → "[DB:shop.orders] INSERT {id=1, customer=alice, total=1349.0}"
  → orderItems.insert({item: Laptop, order_customer: alice})
      → "[DB:shop.order_items] INSERT {id=1, item=Laptop, ...}"
  → orderItems.insert({item: Mouse, order_customer: alice})
      → "[DB:shop.order_items] INSERT {id=2, item=Mouse, ...}"
```

**Data flow across layers:**

| Layer | Input | Output |
|---|---|---|
| `ctx` → `dbFactory.createAccessor("orders")` | table name | `TableAccessor` singleton |
| `OrderRepository.save(...)` | customer + items + total | rows inserted into both tables |
| `ctx.close()` | — | `dbFactory.destroy()` called |

## 7. Gotchas & takeaways

> **Instance factory methods create the product bean AFTER the factory bean.** If the factory's `@PostConstruct` method has not run yet (e.g., due to circular deps), the factory method is called on a partially-initialized factory. Always ensure factory beans have no circular dependencies.

> **In `@Configuration` classes, calling another `@Bean` method looks like an instance factory call, but it is CGLIB-proxied.** `dataSource()` calling `dataSourceFactory()` does not create a new factory — CGLIB intercepts the call and returns the already-cached `dataSourceFactory` singleton.

- XML: `<bean factory-bean="factoryBeanName" factory-method="methodName"/>` is the explicit instance-factory-method syntax.
- A factory bean can produce multiple product beans by exposing multiple factory methods — each produces a separate singleton with a different name.
- Factory beans participate in the full Spring lifecycle: they can use `@PostConstruct`, `@PreDestroy`, `@Autowired`, and `@Value` just like any other bean.
- Instance factory methods are the foundation of Spring's `@Configuration` class model — every `@Bean` method is an instance factory method on the config class.
- If a factory method throws, the product bean is never registered and the container startup fails with `BeanCreationException`.
