---
card: spring-framework
gi: 34
slug: instantiation-with-a-static-factory-method
title: Instantiation with a static factory method
---

## 1. What it is

**Static factory method instantiation** tells Spring to create a bean by calling a static method on a class rather than calling `new` directly.

```java
// @Bean factory method in @Configuration (most common form):
@Bean
public static DataSource dataSource() {
    return DataSourceBuilder.create()
        .url("jdbc:postgresql://localhost/mydb")
        .build();
}

// Or pointing to an external static factory:
// XML: <bean class="java.util.Calendar" factory-method="getInstance"/>
// Java: ctx.registerBeanDefinition("calendar",
//     BeanDefinitionBuilder.genericBeanDefinition(Calendar.class)
//         .setFactoryMethod("getInstance").getBeanDefinition());
```

Spring calls the static method, caches the result as a singleton (by default), and injects it wherever the return type is required.

In one sentence: **Static factory method instantiation delegates bean creation to a static method on any class, enabling Spring to manage objects whose constructors are hidden or whose creation requires complex logic.**

## 2. Why & when

Use a static factory method when:

- **Constructor is private.** Many well-designed APIs (e.g., `Connection`, `Logger`, `UUID`) hide their constructors behind factory methods.
- **Creation requires logic.** The factory can choose between implementations, apply environment-based configuration, or validate inputs before returning an instance.
- **Third-party class.** You cannot annotate a class you don't own — a `@Bean` method in your `@Configuration` class acts as the factory.
- **Named constructors.** `Payment.forStripe(apiKey)` is more expressive than `new Payment(apiKey, "stripe", null, null, ...)`.

In Spring Boot apps, `@Bean` methods in `@Configuration` classes are the standard way to wrap third-party objects in managed beans — they are all static-factory-style.

## 3. Core concept

When a `BeanDefinition` has a `factoryMethodName`, the container:

```
BeanDefinition:
  beanClass = "com.example.AppConfig"  (or the class that owns the factory)
  factoryMethodName = "dataSource"     (static method name)
  constructorArgumentValues = []       (method arguments)

Instantiation:
  → find the static method: AppConfig.dataSource()
  → resolve method parameter types → inject from context
  → Method.invoke(null, args)          ← null receiver = static call
  → cache result as singleton
```

The return type of the static method is the bean type — not the class that declares the factory. `AppConfig.dataSource()` returns `DataSource`, so the bean type is `DataSource`.

`@Bean` methods in `@Configuration` classes are NOT static by default — they are instance methods on the config class. Only mark them `static` when they are `BeanFactoryPostProcessor` or `BeanDefinitionRegistryPostProcessor` — those must be static to avoid CGLIB issues.

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Static factory method instantiation: container resolves method args, invokes static method, receives returned bean instance">
  <defs>
    <marker id="a34" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Config class -->
  <rect x="10" y="40" width="200" height="90" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="64" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">AppConfig</text>
  <text x="110" y="82" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Bean</text>
  <text x="110" y="97" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">static DataSource dataSource()</text>
  <text x="110" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">{ return DataSourceBuilder...build(); }</text>

  <!-- Container resolves args -->
  <rect x="285" y="30" width="165" height="56" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="368" y="54" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">resolve method parameters</text>
  <text x="368" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">by type / @Qualifier</text>

  <line x1="210" y1="70" x2="283" y2="58" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a34)"/>

  <!-- Invoke static method -->
  <rect x="285" y="110" width="165" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="368" y="133" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Method.invoke(null, args)</text>
  <text x="368" y="149" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">static → receiver is null</text>

  <line x1="368" y1="86" x2="368" y2="108" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a34)"/>

  <!-- Bean returned -->
  <rect x="525" y="80" width="145" height="56" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="597" y="103" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">DataSource</text>
  <text x="597" y="121" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">bean type = return type</text>

  <line x1="450" y1="135" x2="523" y2="108" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a34)"/>

  <text x="340" y="185" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Return type of factory method = bean type. Class declaring method ≠ bean type.</text>
</svg>

The container invokes the static factory method (null receiver), captures the returned object as the bean, and caches it. The bean type is the return type of the factory method.

## 5. Runnable example

Scenario: a `ConnectionPool` that can only be created via a static factory (`ConnectionPool.forUrl(...)`), not via `new`. Spring must use the factory method.

### Level 1 — Basic

A class with a private constructor and public static factory — Spring calls the factory.

```java
// StaticFactoryDemo.java — run with: java StaticFactoryDemo.java
import java.lang.reflect.*;
import java.util.*;

public class StaticFactoryDemo {

    // ConnectionPool: private constructor — must use static factory
    static class ConnectionPool {
        private final String url;
        private final int    maxConns;
        private int          available;

        // Private constructor — cannot call new ConnectionPool(...)
        private ConnectionPool(String url, int maxConns) {
            this.url = url; this.maxConns = maxConns; this.available = maxConns;
            System.out.println("  [POOL] Created: " + url + " max=" + maxConns);
        }

        // Static factory method — the only public creation path
        public static ConnectionPool forUrl(String url, int maxConns) {
            System.out.println("  [FACTORY] ConnectionPool.forUrl(" + url + ", " + maxConns + ")");
            return new ConnectionPool(url, maxConns);
        }

        String borrow()   { available--; return "conn-" + (maxConns - available); }
        void   release()  { available++; }
        int    available(){ return available; }
        @Override public String toString() { return "ConnectionPool[" + url + " avail=" + available + "]"; }
    }

    // Static factory bean container
    static class StaticFactoryCtx {
        private final Map<Class<?>, Object> beans = new LinkedHashMap<>();

        // Register a bean via a static factory method
        void registerViaStaticFactory(Class<?> factoryClass, String methodName, Object... args)
            throws Exception {
            Class<?>[] argTypes = Arrays.stream(args).map(Object::getClass).toArray(Class[]::new);
            Method m = factoryClass.getDeclaredMethod(methodName, argTypes);
            Object bean = m.invoke(null, args);  // null receiver = static method
            beans.put(m.getReturnType(), bean);
            System.out.println("  [CTX] Bean created via " + factoryClass.getSimpleName()
                + "." + methodName + "() → " + bean.getClass().getSimpleName());
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> type) { return (T) beans.get(type); }
    }

    public static void main(String[] args) throws Exception {
        StaticFactoryCtx ctx = new StaticFactoryCtx();

        System.out.println("=== Container startup via static factory ===");
        ctx.registerViaStaticFactory(ConnectionPool.class, "forUrl",
            "jdbc:postgresql://prod:5432/orders", 10);

        System.out.println("\n=== Application using the pool ===");
        ConnectionPool pool = ctx.getBean(ConnectionPool.class);
        System.out.println("  Pool: " + pool);

        String c1 = pool.borrow();
        String c2 = pool.borrow();
        System.out.println("  Borrowed: " + c1 + ", " + c2 + " | Available: " + pool.available());
        pool.release();
        System.out.println("  After release. Available: " + pool.available());
    }
}
```

How to run: `java StaticFactoryDemo.java`

`ConnectionPool.forUrl(url, maxConns)` is the only way to create a pool. The container calls it via `Method.invoke(null, args)` — `null` receiver because it's a static method. The returned `ConnectionPool` is cached as a singleton with type `ConnectionPool`.

### Level 2 — Intermediate

Environment-based factory: the static method chooses between implementations based on a configuration property.

```java
// StaticFactoryDemo2.java — run with: java StaticFactoryDemo2.java
import java.lang.reflect.*;
import java.util.*;

public class StaticFactoryDemo2 {

    interface CacheProvider {
        void put(String k, String v);
        Optional<String> get(String k);
        String type();
    }

    static class InMemoryCache implements CacheProvider {
        private final Map<String, String> store = new HashMap<>();
        public void put(String k, String v) { store.put(k, v); }
        public Optional<String> get(String k) { return Optional.ofNullable(store.get(k)); }
        public String type() { return "in-memory"; }
    }

    static class NoOpCache implements CacheProvider {
        public void put(String k, String v) { /* no-op */ }
        public Optional<String> get(String k) { return Optional.empty(); }
        public String type() { return "no-op"; }
    }

    // Static factory that makes a decision — which implementation to use
    static class CacheFactory {
        // This is what @Bean methods do: static factory logic in Java config
        public static CacheProvider create(String mode) {
            System.out.println("  [FACTORY] CacheFactory.create(mode=" + mode + ")");
            return switch (mode) {
                case "enabled"  -> new InMemoryCache();
                case "disabled" -> new NoOpCache();
                default         -> throw new IllegalArgumentException("Unknown cache mode: " + mode);
            };
        }
    }

    // ProductService that uses the cache
    static class ProductService {
        private final CacheProvider cache;
        ProductService(CacheProvider cache) {
            this.cache = cache;
            System.out.println("  [BEAN] ProductService + cache=" + cache.type());
        }

        String getProductName(int id) {
            String key = "product:" + id;
            return cache.get(key).orElseGet(() -> {
                String name = "Product-" + id;  // simulate DB lookup
                cache.put(key, name);
                System.out.println("  [DB] Loaded product " + id + " → " + name);
                return name;
            });
        }
    }

    static class FactoryCtx {
        private final Map<Class<?>, Object> beans = new LinkedHashMap<>();

        void registerViaStaticFactory(Class<?> factory, String method, Object... args) throws Exception {
            Method m = factory.getDeclaredMethod(method,
                Arrays.stream(args).map(Object::getClass).toArray(Class[]::new));
            Object bean = m.invoke(null, args);
            beans.put(m.getReturnType(), bean);
            for (Class<?> iface : bean.getClass().getInterfaces()) beans.put(iface, bean);
            System.out.println("  [CTX] " + bean.getClass().getSimpleName() + " registered");
        }

        void registerWithDeps(Class<?> cls) throws Exception {
            var ctor = cls.getDeclaredConstructors()[0];
            Object[] deps = Arrays.stream(ctor.getParameterTypes())
                .map(t -> beans.entrySet().stream()
                    .filter(e -> t.isAssignableFrom(e.getKey()))
                    .map(Map.Entry::getValue).findFirst()
                    .orElseThrow(() -> new RuntimeException("No dep: " + t.getSimpleName())))
                .toArray();
            Object bean = ctor.newInstance(deps);
            beans.put(cls, bean);
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(Class<T> t) {
            return (T) beans.entrySet().stream()
                .filter(e -> t.isAssignableFrom(e.getKey()))
                .map(Map.Entry::getValue).findFirst().orElseThrow();
        }
    }

    public static void main(String[] args) throws Exception {
        // Simulate two environments: "enabled" and "disabled" cache
        for (String mode : List.of("enabled", "disabled")) {
            System.out.println("\n=== Environment: cache=" + mode + " ===");

            FactoryCtx ctx = new FactoryCtx();
            ctx.registerViaStaticFactory(CacheFactory.class, "create", mode);
            ctx.registerWithDeps(ProductService.class);

            ProductService svc = ctx.getBean(ProductService.class);
            System.out.println("  First call:  " + svc.getProductName(42));
            System.out.println("  Second call: " + svc.getProductName(42));  // cache hit or miss
        }
    }
}
```

How to run: `java StaticFactoryDemo2.java`

With `mode="enabled"`: the second `getProductName(42)` hits the cache — no `[DB]` line printed. With `mode="disabled"`: the `NoOpCache` never stores anything — `[DB]` is printed both times. The `ProductService` code is identical; only the factory-created `CacheProvider` changes.

### Level 3 — Advanced

Static factory with generic return type: a typed `EventBus<T>` created by a factory, showing how the container handles generic factory methods.

```java
// StaticFactoryDemo3.java — run with: java StaticFactoryDemo3.java
import java.util.*;
import java.util.function.*;

public class StaticFactoryDemo3 {

    record OrderEvent(String orderId, String type, double amount) {}
    record PaymentEvent(String paymentId, String status) {}

    // Generic event bus — created via static factory
    static class EventBus<T> {
        private final String name;
        private final List<Consumer<T>> subscribers = new ArrayList<>();
        private final List<T>           history     = new ArrayList<>();

        private EventBus(String name) {
            this.name = name;
            System.out.println("  [FACTORY] EventBus.create(name=" + name + ")");
        }

        // Static factory — named constructor pattern
        public static <T> EventBus<T> create(String name) {
            return new EventBus<>(name);
        }

        void subscribe(Consumer<T> listener) { subscribers.add(listener); }

        void publish(T event) {
            history.add(event);
            System.out.println("  [" + name + "] Publishing: " + event);
            subscribers.forEach(l -> l.accept(event));
        }

        List<T> getHistory() { return Collections.unmodifiableList(history); }
        String  getName()    { return name; }
    }

    static class OrderProcessor {
        private final EventBus<OrderEvent>   orderBus;
        private final EventBus<PaymentEvent> paymentBus;

        OrderProcessor(EventBus<OrderEvent> orderBus, EventBus<PaymentEvent> paymentBus) {
            this.orderBus = orderBus; this.paymentBus = paymentBus;
            System.out.println("  [BEAN] OrderProcessor wired with " + orderBus.getName()
                + " + " + paymentBus.getName());
        }

        void processOrder(String id, double amount) {
            orderBus.publish(new OrderEvent(id, "PLACED", amount));
            paymentBus.publish(new PaymentEvent("PAY-" + id, "PENDING"));
        }
    }

    @SuppressWarnings("unchecked")
    public static void main(String[] args) throws Exception {
        // Build beans via static factories
        System.out.println("=== Container startup ===");

        // These @Bean methods would look like:
        // @Bean EventBus<OrderEvent>   orderEventBus()   { return EventBus.create("order-events"); }
        // @Bean EventBus<PaymentEvent> paymentEventBus() { return EventBus.create("payment-events"); }
        EventBus<OrderEvent>   orderBus   = EventBus.create("order-events");
        EventBus<PaymentEvent> paymentBus = EventBus.create("payment-events");

        // Register listeners (mirrors @EventListener / subscribe patterns)
        orderBus.subscribe(e ->
            System.out.println("  [AUDIT] Order " + e.orderId() + " " + e.type() + " $" + e.amount()));
        orderBus.subscribe(e ->
            System.out.println("  [INVENTORY] Reserve stock for order " + e.orderId()));
        paymentBus.subscribe(e ->
            System.out.println("  [EMAIL] Notify customer: payment " + e.paymentId() + " is " + e.status()));

        OrderProcessor processor = new OrderProcessor(orderBus, paymentBus);

        System.out.println("\n=== Processing orders ===");
        processor.processOrder("ORD-001", 149.99);
        System.out.println();
        processor.processOrder("ORD-002", 299.00);

        System.out.println("\n=== Event history ===");
        System.out.println("  Order events:   " + orderBus.getHistory().size());
        System.out.println("  Payment events: " + paymentBus.getHistory().size());
    }
}
```

How to run: `java StaticFactoryDemo3.java`

`EventBus.create("order-events")` uses a named constructor pattern — the static factory name is more expressive than `new EventBus<>()`. Two different `EventBus` instances for different event types are registered as separate beans. In a real Spring `@Configuration` class, these would be two `@Bean` methods with different return types, and Spring would inject the correct typed bus into `OrderProcessor`'s constructor.

## 6. Walkthrough

**Level 2 — environment-based factory decision:**

```
ctx.registerViaStaticFactory(CacheFactory.class, "create", "enabled")
  → Method m = CacheFactory.getDeclaredMethod("create", String.class)
  → m.invoke(null, "enabled")   ← null = static call
      → CacheFactory.create("enabled")
          → switch("enabled") → new InMemoryCache()
          → "[FACTORY] CacheFactory.create(mode=enabled)"
  → bean = InMemoryCache instance
  → beans[CacheProvider.class] = InMemoryCache
  → beans[InMemoryCache.class] = InMemoryCache
```

**`svc.getProductName(42)` — first call (cache miss, cache enabled):**
```
getProductName(42)
  → key = "product:42"
  → cache.get("product:42") → Optional.empty()  (cold cache)
  → name = "Product-42"  (simulated DB load)
  → "[DB] Loaded product 42 → Product-42"
  → cache.put("product:42", "Product-42")
  → return "Product-42"
```

**`svc.getProductName(42)` — second call (cache hit, cache enabled):**
```
getProductName(42)
  → cache.get("product:42") → Optional["Product-42"]  (cache hit)
  → return "Product-42"   (no [DB] line)
```

**Factory method vs constructor — key differences:**

| Aspect | `new MyClass(args)` | `MyClass.create(args)` |
|---|---|---|
| Return type | exactly `MyClass` | can be a subtype |
| Constructor visibility | must be accessible | constructor can be private |
| Logic | limited to constructor body | full factory logic |
| Name expressiveness | one name only | multiple descriptive names |

## 7. Gotchas & takeaways

> **`@Bean` methods in `@Configuration` classes are NOT static by default.** They are instance factory methods, not static factory methods. Mark a `@Bean` method `static` only when it creates a `BeanFactoryPostProcessor` — static `@Bean` methods bypass CGLIB interception and should be used sparingly.

> **The return type of the factory method is the bean type.** If `create()` returns an interface type, Spring registers the bean under that interface. If it returns a concrete type, you can inject it by the concrete type or any interface it implements.

- External static factories (non-Spring classes): use XML `factory-method="getInstance"` or `BeanDefinitionBuilder.genericBeanDefinition(Calendar.class).setFactoryMethod("getInstance")`.
- `@Bean` methods receive their parameters from the Spring context — you can declare any Spring-managed bean as a parameter, just like constructor injection.
- Static factory methods in `@Configuration` can call each other — Spring's CGLIB proxy returns the cached singleton, not a new instance, on repeated calls.
- `@Bean(initMethod = "init", destroyMethod = "close")` on a `@Bean` method adds lifecycle callbacks to the factory-created bean.
- Use the named-constructor factory pattern (`Payment.forCreditCard(...)`, `Payment.forBankTransfer(...)`) to create expressive, self-documenting Spring beans.
