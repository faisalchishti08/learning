---
card: spring-framework
gi: 36
slug: factorybean-interface
title: FactoryBean interface
---

## 1. What it is

**`FactoryBean<T>`** is Spring's built-in interface for beans that act as factories. A bean implementing `FactoryBean<T>` does not expose itself to callers — it exposes the **product** it creates via `getObject()`.

```java
public interface FactoryBean<T> {
    T getObject() throws Exception;        // what is returned when getBean("myBean") is called
    Class<?> getObjectType();              // used by the container for type matching
    default boolean isSingleton() { return true; }  // cache the product?
}
```

When Spring's container resolves `getBean("myFactoryBean")`, it calls `myFactoryBean.getObject()` and returns the **product**, not the `FactoryBean` instance. To get the factory itself, prefix the name with `&`: `getBean("&myFactoryBean")`.

In one sentence: **`FactoryBean<T>` is a contract that lets a Spring bean act as a factory, hiding complex object creation behind a simple name — when you look up the bean by name you get the product, and `&name` gives you the factory itself.**

## 2. Why & when

Use `FactoryBean` when:

- **Object creation is complex** and spans multiple steps (building a JPA `EntityManagerFactory`, configuring an SSL `SSLContext`, or building a proxy).
- **The product is not a Spring bean** — e.g., a third-party object that has no Spring annotations but must be created with specific parameters and registered in the container.
- **Product lifetime may differ from factory lifetime.** With `isSingleton()` returning `false`, a new product is created on each `getBean()` call.
- **Type information must be declared** before the object is created — `getObjectType()` enables type-based autowiring to work without calling `getObject()` first.

The `FactoryBean` pattern predates Java config (`@Bean` methods). Today, `@Bean` methods handle most of these use cases. `FactoryBean` is still found in Spring's own internals (e.g., `LocalEntityManagerFactoryBean`, `ProxyFactoryBean`).

## 3. Core concept

```
Container resolves "connectionPool":
  → looks up "connectionPool"
  → finds a ConnectionPoolFactory (implements FactoryBean<ConnectionPool>)
  → calls factory.getObject()
  → returns ConnectionPool (the product)

Container resolves "&connectionPool":
  → prefix & → skip getObject()
  → returns ConnectionPoolFactory (the factory bean itself)

isSingleton() == true:
  → product cached after first getObject() call
  → same instance returned on every lookup

isSingleton() == false:
  → getObject() called on every lookup
  → new product each time
```

The `&` prefix is the only way to distinguish "I want the factory" from "I want the product."

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="FactoryBean: lookup by name returns product; lookup by &name returns the factory itself">
  <defs>
    <marker id="a36" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b36" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Container -->
  <rect x="10" y="10" width="650" height="195" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="335" y="30" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Container</text>

  <!-- FactoryBean -->
  <rect x="40" y="50" width="180" height="100" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="130" y="74" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ConnectionPoolFactory</text>
  <text x="130" y="92" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implements FactoryBean&lt;CP&gt;</text>
  <text x="130" y="112" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">getObject() → new ConnectionPool</text>
  <text x="130" y="128" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">getObjectType() → ConnectionPool.class</text>
  <text x="130" y="144" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">isSingleton() → true</text>

  <!-- Product -->
  <rect x="440" y="55" width="190" height="70" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/>
  <text x="535" y="79" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">ConnectionPool</text>
  <text x="535" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">the product bean (cached)</text>
  <text x="535" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">returned by getBean("connectionPool")</text>

  <!-- getBean("connectionPool") path -->
  <line x1="220" y1="85" x2="435" y2="85" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a36)" stroke-dasharray="4,3"/>
  <text x="328" y="79" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">getBean("connectionPool") → getObject()</text>

  <!-- getBean("&connectionPool") path -->
  <rect x="440" y="150" width="190" height="42" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="535" y="168" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ConnectionPoolFactory</text>
  <text x="535" y="184" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">returned by getBean("&amp;connectionPool")</text>

  <line x1="220" y1="130" x2="435" y2="168" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b36)" stroke-dasharray="4,3"/>
  <text x="310" y="162" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">getBean("&amp;connectionPool")</text>
</svg>

`getBean("connectionPool")` calls `getObject()` on the factory and returns the product. `getBean("&connectionPool")` bypasses `getObject()` and returns the factory bean itself.

## 5. Runnable example

Scenario: a `HttpClientFactory` that builds a configured `HttpClient` (simulated) with connection pool, timeout, and retry settings. Complex setup logic is hidden behind the `FactoryBean` contract.

### Level 1 — Basic

Simplest `FactoryBean` implementation: creates one product, caches it.

```java
// FactoryBeanDemo.java — run with: java FactoryBeanDemo.java
import java.util.*;

public class FactoryBeanDemo {

    // Product bean — complex to create
    static class HttpClient {
        private final int    connectionTimeout;
        private final int    readTimeout;
        private final int    maxConnections;
        private final String baseUrl;

        HttpClient(int connTimeout, int readTimeout, int maxConns, String baseUrl) {
            this.connectionTimeout = connTimeout;
            this.readTimeout       = readTimeout;
            this.maxConnections    = maxConns;
            this.baseUrl           = baseUrl;
            System.out.println("  [PRODUCT] HttpClient(" + baseUrl
                + " connTimeout=" + connTimeout + " maxConns=" + maxConns + ")");
        }

        String get(String path) {
            return "HTTP/1.1 200 OK [" + baseUrl + path + "]";
        }
    }

    // FactoryBean implementation
    interface FactoryBean<T> {
        T getObject() throws Exception;
        Class<?> getObjectType();
        default boolean isSingleton() { return true; }
    }

    static class HttpClientFactory implements FactoryBean<HttpClient> {
        private String  baseUrl          = "http://localhost:8080";
        private int     connectionTimeout = 3000;
        private int     readTimeout       = 10000;
        private int     maxConnections    = 10;

        HttpClientFactory() {
            System.out.println("  [FACTORY BEAN] HttpClientFactory created");
        }

        // Setters — factory bean's own properties
        void setBaseUrl(String u)          { this.baseUrl = u; }
        void setConnectionTimeout(int t)   { this.connectionTimeout = t; }
        void setReadTimeout(int t)         { this.readTimeout = t; }
        void setMaxConnections(int n)      { this.maxConnections = n; }

        @Override
        public HttpClient getObject() throws Exception {
            System.out.println("  [FACTORY BEAN] getObject() called");
            return new HttpClient(connectionTimeout, readTimeout, maxConnections, baseUrl);
        }

        @Override public Class<?> getObjectType() { return HttpClient.class; }
        @Override public boolean isSingleton()    { return true; }
    }

    // Minimal container with FactoryBean support
    static class Ctx {
        private final Map<String, Object> beans         = new HashMap<>();
        private final Map<String, Object> productCache  = new HashMap<>();

        void register(String name, Object bean) { beans.put(name, bean); }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) throws Exception {
            if (name.startsWith("&")) {
                // Return the factory bean itself
                return (T) beans.get(name.substring(1));
            }
            Object raw = beans.get(name);
            if (raw instanceof FactoryBean<?> fb) {
                if (fb.isSingleton()) {
                    return (T) productCache.computeIfAbsent(name, k -> {
                        try { return fb.getObject(); }
                        catch (Exception e) { throw new RuntimeException(e); }
                    });
                }
                return (T) fb.getObject();
            }
            return (T) raw;
        }
    }

    public static void main(String[] args) throws Exception {
        Ctx ctx = new Ctx();

        System.out.println("=== Container startup ===");
        HttpClientFactory factory = new HttpClientFactory();
        factory.setBaseUrl("https://api.example.com");
        factory.setConnectionTimeout(5000);
        factory.setMaxConnections(20);
        ctx.register("httpClient", factory);

        System.out.println("\n=== Application uses the product bean ===");
        // getBean("httpClient") returns HttpClient (via getObject())
        HttpClient client1 = ctx.getBean("httpClient");
        HttpClient client2 = ctx.getBean("httpClient");  // same instance (singleton)
        System.out.println("  Same instance? " + (client1 == client2));
        System.out.println("  GET: " + client1.get("/users/42"));

        System.out.println("\n=== Get the factory bean itself ===");
        HttpClientFactory factoryBean = ctx.getBean("&httpClient");
        System.out.println("  Factory type: " + factoryBean.getClass().getSimpleName());
        System.out.println("  Product type: " + factoryBean.getObjectType().getSimpleName());
    }
}
```

How to run: `java FactoryBeanDemo.java`

`getBean("httpClient")` returns an `HttpClient` (the product). `getBean("&httpClient")` returns the `HttpClientFactory`. The `isSingleton()=true` path caches the product — `client1 == client2` is `true`.

### Level 2 — Intermediate

`isSingleton() = false`: each lookup creates a new product. Useful for stateful objects that should not be shared.

```java
// FactoryBeanDemo2.java — run with: java FactoryBeanDemo2.java
import java.util.*;

public class FactoryBeanDemo2 {

    static class DbConnection {
        private final String id;
        private final String url;
        private boolean closed = false;

        DbConnection(String id, String url) {
            this.id = id; this.url = url;
            System.out.println("  [PRODUCT] DbConnection created id=" + id);
        }

        String query(String sql) {
            if (closed) throw new IllegalStateException("Connection " + id + " is closed");
            return "RESULT[" + id + "]: " + sql;
        }
        void close() {
            closed = true;
            System.out.println("  [PRODUCT] DbConnection closed id=" + id);
        }
        String getId() { return id; }
    }

    interface FactoryBean<T> {
        T getObject() throws Exception;
        Class<?> getObjectType();
        default boolean isSingleton() { return true; }
    }

    // Prototype-scoped FactoryBean — produces a new DbConnection on each getBean()
    static class DbConnectionFactory implements FactoryBean<DbConnection> {
        private final String url;
        private int nextId = 1;

        DbConnectionFactory(String url) {
            System.out.println("  [FACTORY BEAN] DbConnectionFactory created url=" + url);
            this.url = url;
        }

        @Override
        public DbConnection getObject() {
            System.out.println("  [FACTORY BEAN] getObject() → new connection");
            return new DbConnection("conn-" + nextId++, url);
        }

        @Override public Class<?> getObjectType() { return DbConnection.class; }
        @Override public boolean isSingleton()    { return false; }  // prototype
    }

    static class Ctx {
        private final Map<String, Object> beans        = new HashMap<>();
        private final Map<String, Object> productCache = new HashMap<>();

        void register(String name, Object bean) { beans.put(name, bean); }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) throws Exception {
            if (name.startsWith("&")) return (T) beans.get(name.substring(1));
            Object raw = beans.get(name);
            if (raw instanceof FactoryBean<?> fb) {
                if (fb.isSingleton()) {
                    return (T) productCache.computeIfAbsent(name, k -> {
                        try { return fb.getObject(); }
                        catch (Exception e) { throw new RuntimeException(e); }
                    });
                }
                return (T) fb.getObject();   // new instance each time
            }
            return (T) raw;
        }
    }

    public static void main(String[] args) throws Exception {
        Ctx ctx = new Ctx();

        System.out.println("=== Container startup ===");
        ctx.register("dbConnection", new DbConnectionFactory("jdbc:postgresql://db:5432/shop"));

        System.out.println("\n=== Application borrows connections ===");
        DbConnection c1 = ctx.getBean("dbConnection");
        DbConnection c2 = ctx.getBean("dbConnection");
        System.out.println("  Same instance? " + (c1 == c2));    // false — prototype
        System.out.println("  c1: " + c1.query("SELECT * FROM orders LIMIT 5"));
        System.out.println("  c2: " + c2.query("SELECT count(*) FROM products"));
        c1.close();

        // c1 is closed, c2 still usable
        try {
            c1.query("SELECT 1");
        } catch (IllegalStateException e) {
            System.out.println("  c1 error: " + e.getMessage());
        }
        System.out.println("  c2 still works: " + c2.query("SELECT 1"));
        c2.close();
    }
}
```

How to run: `java FactoryBeanDemo2.java`

`isSingleton()=false` means `getBean("dbConnection")` calls `getObject()` every time, producing a new `DbConnection`. `c1 == c2` is `false`. Each connection has an independent lifecycle.

### Level 3 — Advanced

`FactoryBean` with `getObjectType()` enabling type-based resolution, and `&name` introspection in a diagnostics service.

```java
// FactoryBeanDemo3.java — run with: java FactoryBeanDemo3.java
import java.util.*;

public class FactoryBeanDemo3 {

    // Product interface
    interface MessageQueue {
        void publish(String topic, String message);
        List<String> drain(String topic);
    }

    // Product implementation
    static class InMemoryMessageQueue implements MessageQueue {
        private final String name;
        private final Map<String, List<String>> store = new HashMap<>();

        InMemoryMessageQueue(String name) {
            System.out.println("  [PRODUCT] InMemoryMessageQueue(name=" + name + ")");
            this.name = name;
        }

        @Override
        public void publish(String topic, String msg) {
            store.computeIfAbsent(topic, k -> new ArrayList<>()).add(msg);
            System.out.println("  [MQ:" + name + "] published → " + topic + ": " + msg);
        }

        @Override
        public List<String> drain(String topic) {
            return store.getOrDefault(topic, List.of());
        }
    }

    interface FactoryBean<T> {
        T getObject() throws Exception;
        Class<?> getObjectType();
        default boolean isSingleton() { return true; }
        default String description()  { return "FactoryBean<" + getObjectType().getSimpleName() + ">"; }
    }

    // FactoryBean that creates an InMemoryMessageQueue with specific settings
    static class MessageQueueFactory implements FactoryBean<MessageQueue> {
        private final String queueName;
        private final int    capacity;
        private final boolean durable;

        MessageQueueFactory(String queueName, int capacity, boolean durable) {
            System.out.println("  [FACTORY BEAN] MessageQueueFactory(queue=" + queueName + ")");
            this.queueName = queueName; this.capacity = capacity; this.durable = durable;
        }

        @Override
        public MessageQueue getObject() {
            System.out.printf("  [FACTORY BEAN] getObject() → queue=%s cap=%d durable=%s%n",
                queueName, capacity, durable);
            return new InMemoryMessageQueue(queueName);
        }

        @Override public Class<?> getObjectType() { return MessageQueue.class; }
        @Override public boolean isSingleton()    { return true; }
        @Override public String description() {
            return String.format("MessageQueueFactory[%s, cap=%d, durable=%s]",
                queueName, capacity, durable);
        }
        String getQueueName() { return queueName; }
    }

    // Container with type-based lookup and factory introspection
    static class Ctx {
        private final Map<String, Object> beans       = new HashMap<>();
        private final Map<String, Object> prodCache   = new HashMap<>();

        void register(String name, Object bean) { beans.put(name, bean); }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) throws Exception {
            if (name.startsWith("&")) return (T) beans.get(name.substring(1));
            Object raw = beans.get(name);
            if (raw instanceof FactoryBean<?> fb) {
                if (fb.isSingleton())
                    return (T) prodCache.computeIfAbsent(name, k -> {
                        try { return fb.getObject(); }
                        catch (Exception e) { throw new RuntimeException(e); }
                    });
                return (T) fb.getObject();
            }
            return (T) raw;
        }

        // Type-based lookup — finds beans whose product type matches
        @SuppressWarnings("unchecked")
        <T> Map<String, T> getBeansOfType(Class<T> type) {
            Map<String, T> result = new LinkedHashMap<>();
            for (var entry : beans.entrySet()) {
                Object raw = entry.getValue();
                Class<?> productType = (raw instanceof FactoryBean<?> fb)
                    ? fb.getObjectType() : raw.getClass();
                if (type.isAssignableFrom(productType)) {
                    try { result.put(entry.getKey(), getBean(entry.getKey())); }
                    catch (Exception e) { throw new RuntimeException(e); }
                }
            }
            return result;
        }

        // Diagnostics — introspect all registered FactoryBeans
        void printFactoryBeanReport() {
            System.out.println("  === Factory Bean Report ===");
            for (var entry : beans.entrySet()) {
                if (entry.getValue() instanceof FactoryBean<?> fb) {
                    boolean cached = prodCache.containsKey(entry.getKey());
                    System.out.printf("  %-20s | product=%-18s | singleton=%-5s | cached=%-5s | %s%n",
                        entry.getKey(),
                        fb.getObjectType().getSimpleName(),
                        fb.isSingleton(), cached,
                        fb.description());
                }
            }
        }
    }

    // Service that injects a MessageQueue by type
    static class OrderEventService {
        private final MessageQueue queue;
        OrderEventService(MessageQueue queue) {
            this.queue = queue;
            System.out.println("  [BEAN] OrderEventService created");
        }
        void placeOrder(String orderId, String customer) {
            queue.publish("orders", orderId + ":" + customer);
            queue.publish("audit",  "PLACED:" + orderId);
        }
        List<String> getOrderEvents() { return queue.drain("orders"); }
    }

    public static void main(String[] args) throws Exception {
        Ctx ctx = new Ctx();

        System.out.println("=== Container startup ===");
        ctx.register("orderQueue",   new MessageQueueFactory("order-queue",   1000, true));
        ctx.register("auditQueue",   new MessageQueueFactory("audit-queue",   5000, false));
        ctx.register("metricsQueue", new MessageQueueFactory("metrics-queue", 500,  false));

        // Inject the 'orderQueue' product by name
        MessageQueue mq = ctx.getBean("orderQueue");
        ctx.register("orderEventService", new OrderEventService(mq));

        System.out.println("\n=== Application running ===");
        OrderEventService svc = ctx.getBean("orderEventService");
        svc.placeOrder("ORD-001", "alice");
        svc.placeOrder("ORD-002", "bob");
        System.out.println("  Order events: " + svc.getOrderEvents());

        System.out.println("\n=== Type-based lookup (all MessageQueue beans) ===");
        Map<String, MessageQueue> queues = ctx.getBeansOfType(MessageQueue.class);
        System.out.println("  Found " + queues.size() + " MessageQueue beans: " + queues.keySet());

        System.out.println("\n=== Factory bean introspection via &name ===");
        MessageQueueFactory f = ctx.getBean("&orderQueue");
        System.out.println("  Factory name: " + f.getQueueName());
        System.out.println("  Factory description: " + f.description());

        System.out.println("\n=== Diagnostics ===");
        ctx.printFactoryBeanReport();
    }
}
```

How to run: `java FactoryBeanDemo3.java`

`getBeansOfType(MessageQueue.class)` uses `getObjectType()` to match factories without calling `getObject()`. `getBean("&orderQueue")` returns the `MessageQueueFactory` for introspection. `printFactoryBeanReport()` shows factory metadata and whether the product has been created yet.

## 6. Walkthrough

**Level 3 — `getBeansOfType(MessageQueue.class)`:**

```
ctx.getBeansOfType(MessageQueue.class):
  for "orderQueue"   → raw = MessageQueueFactory → getObjectType() = MessageQueue.class ✓
  for "auditQueue"   → raw = MessageQueueFactory → getObjectType() = MessageQueue.class ✓
  for "metricsQueue" → raw = MessageQueueFactory → getObjectType() = MessageQueue.class ✓
  for "orderEventService" → raw = OrderEventService → not assignable → skip

  Trigger getBean() for each matching key:
    "orderQueue"   → already in prodCache → return cached InMemoryMessageQueue
    "auditQueue"   → not in cache → getObject() → new InMemoryMessageQueue("audit-queue")
    "metricsQueue" → not in cache → getObject() → new InMemoryMessageQueue("metrics-queue")

  Returns map: {orderQueue → MQ, auditQueue → MQ, metricsQueue → MQ}
```

**Factory bean report:**

| name | product type | singleton | cached |
|---|---|---|---|
| `orderQueue` | `MessageQueue` | true | true (used by `OrderEventService`) |
| `auditQueue` | `MessageQueue` | true | true (resolved by `getBeansOfType`) |
| `metricsQueue` | `MessageQueue` | true | true (resolved by `getBeansOfType`) |

## 7. Gotchas & takeaways

> **`getBean("name")` vs `getBean("&name")`:** Without the `&` prefix, the container returns the product, not the factory. If you accidentally inject a `FactoryBean` instead of its product, you may get the factory bean wired — always use the product name directly in `@Autowired` fields.

> **Type-based lookup uses `getObjectType()`, not `getObject()`:** Spring can wire a `FactoryBean`-produced type by type (`@Autowired DataSource ds`) without triggering the factory yet. If `getObjectType()` returns `null`, Spring cannot resolve the type before creating the object.

- `isSingleton()=false` means every `getBean()` call invokes `getObject()` — equivalent to prototype scope.
- Spring's own infrastructure uses `FactoryBean` extensively: `LocalEntityManagerFactoryBean`, `SqlSessionFactoryBean` (MyBatis), `ProxyFactoryBean` (AOP).
- Modern code prefers `@Bean` methods over custom `FactoryBean` implementations. Use `FactoryBean` only when integrating with frameworks that expect it.
- `SmartFactoryBean` extends `FactoryBean` with `isEagerInit()` — lets the factory signal it wants eager initialization at context startup.
