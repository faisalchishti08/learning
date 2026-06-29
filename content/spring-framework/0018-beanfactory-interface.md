---
card: spring-framework
gi: 18
slug: beanfactory-interface
title: BeanFactory interface
---

## 1. What it is

`BeanFactory` is the root interface of Spring's IoC container. It defines the most fundamental contract: given a bean name or type, produce an instance.

Key methods on the interface:

```java
Object getBean(String name)
<T> T getBean(Class<T> requiredType)
<T> T getBean(String name, Class<T> requiredType)
boolean containsBean(String name)
boolean isSingleton(String name)
boolean isPrototype(String name)
Class<?> getType(String name)
```

`BeanFactory` is an abstraction — you never instantiate it directly. In practice you use `DefaultListableBeanFactory` (the concrete low-level implementation) or, far more commonly, one of the `ApplicationContext` implementations that extend `BeanFactory`.

In one sentence: **`BeanFactory` is the minimal interface contract for "give me a bean by name or type," and `DefaultListableBeanFactory` is its full implementation.**

## 2. Why & when

`BeanFactory` exists to separate the *what* (the bean retrieval contract) from the *how* (the scanning, autowiring, and lifecycle machinery that `ApplicationContext` adds on top).

You encounter `BeanFactory` directly in two situations:
1. **Embedded Spring in a constrained environment** — e.g., a library or a lightweight tool that needs IoC but not a full application context, or when startup time must be minimised and you forego `ApplicationContext`'s pre-instantiation of singletons.
2. **Reading Spring internals or framework code** — most Spring extension APIs (`BeanFactoryPostProcessor`, `BeanPostProcessor`) receive a `BeanFactory` reference.

For production applications, prefer `ApplicationContext`. Use `BeanFactory` directly only when you have a specific size or startup constraint.

## 3. Core concept

Think of `BeanFactory` as a warehouse registry. You register items by name and type; when you ask for an item by name or type, the registry returns the right one.

The key implementation detail: `BeanFactory` supports **lazy instantiation by default**. Beans are created only when `getBean()` is first called. `ApplicationContext` pre-instantiates all singletons at startup to catch configuration errors early — `BeanFactory` does not.

```
BeanFactory (interface)
  └── HierarchicalBeanFactory (adds parent-context lookup)
        └── ConfigurableBeanFactory (adds lifecycle + scope management)
              └── ConfigurableListableBeanFactory (adds enumeration + freeze)
                    └── DefaultListableBeanFactory (concrete implementation)
                              ↑
                    used internally by all ApplicationContext implementations
```

`DefaultListableBeanFactory` is the workhorse. Every `ApplicationContext` holds one internally. You can use it standalone — register `BeanDefinition` objects, then call `getBean()`.

## 4. Diagram

<svg viewBox="0 0 680 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BeanFactory interface hierarchy and DefaultListableBeanFactory with lazy vs eager instantiation">
  <defs>
    <marker id="a18" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Interface hierarchy left side -->
  <rect x="10" y="10" width="220" height="36" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="33" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">BeanFactory  (interface)</text>

  <rect x="10" y="65" width="220" height="36" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="87" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">HierarchicalBeanFactory  (interface)</text>

  <rect x="10" y="120" width="220" height="36" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="142" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ConfigurableListableBeanFactory</text>

  <rect x="10" y="175" width="220" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="120" y="195" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">DefaultListableBeanFactory</text>
  <text x="120" y="210" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">concrete — used inside every AppContext</text>

  <line x1="120" y1="46" x2="120" y2="63" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a18)"/>
  <line x1="120" y1="101" x2="120" y2="118" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a18)"/>
  <line x1="120" y1="156" x2="120" y2="173" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a18)"/>

  <!-- Right side: lazy vs eager -->
  <rect x="280" y="10" width="380" height="80" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="470" y="34" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">BeanFactory  — Lazy init</text>
  <text x="470" y="54" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Beans created only on first getBean() call</text>
  <text x="470" y="72" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Config errors surface at runtime, not startup</text>

  <rect x="280" y="110" width="380" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="134" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">ApplicationContext  — Eager init</text>
  <text x="470" y="154" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">All singletons created at refresh()</text>
  <text x="470" y="172" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Config errors fail fast at startup ✓</text>

  <text x="470" y="220" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ApplicationContext extends BeanFactory — adds events, i18n, AOP, lifecycle</text>
</svg>

`DefaultListableBeanFactory` implements the full hierarchy. `ApplicationContext` wraps it and adds eager instantiation and richer features.

## 5. Runnable example

Scenario: a product catalog where you look up `Product` beans by name. We simulate the `BeanFactory` pattern in plain Java, then show the Spring API signature.

### Level 1 — Basic

A hand-rolled `BeanFactory`-style registry that resolves beans by name lazily (only on first request).

```java
// BeanFactoryDemo.java — run with: java BeanFactoryDemo.java
import java.util.*;
import java.util.function.*;

public class BeanFactoryDemo {

    record Product(int id, String name, double price) {}

    // --- Minimal BeanFactory simulation ---
    static class SimpleBeanFactory {
        private final Map<String, Supplier<?>> definitions = new LinkedHashMap<>();
        private final Map<String, Object>      singletons  = new LinkedHashMap<>();

        <T> void registerSingleton(String name, Supplier<T> factory) {
            definitions.put(name, factory);
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name, Class<T> type) {
            if (!definitions.containsKey(name))
                throw new RuntimeException("No bean named: " + name);
            Object bean = singletons.computeIfAbsent(name, k -> {
                System.out.println("  [LAZY INIT] Creating bean: " + k);
                return definitions.get(k).get();
            });
            return type.cast(bean);
        }

        boolean containsBean(String name) { return definitions.containsKey(name); }
    }

    public static void main(String[] args) {
        SimpleBeanFactory factory = new SimpleBeanFactory();

        // Registration — no objects created yet (lazy)
        factory.registerSingleton("laptop",  () -> new Product(1, "Laptop",  1299.99));
        factory.registerSingleton("monitor", () -> new Product(2, "Monitor",  449.99));
        factory.registerSingleton("keyboard",() -> new Product(3, "Keyboard",  79.99));

        System.out.println("=== Factory registered — no beans created yet ===\n");

        // First getBean — triggers lazy init
        Product p1 = factory.getBean("laptop", Product.class);
        System.out.println("Got: " + p1);

        // Second getBean — returns same singleton (no re-init)
        Product p2 = factory.getBean("laptop", Product.class);
        System.out.println("Same instance: " + (p1 == p2));

        System.out.println("Has monitor: " + factory.containsBean("monitor"));
    }
}
```

How to run: `java BeanFactoryDemo.java`

"No bean created yet" proves lazy initialisation: the `Supplier` runs only when `getBean()` is called. The second `getBean("laptop")` returns the cached singleton — no second print of `[LAZY INIT]`.

### Level 2 — Intermediate

Add bean aliases (multiple names → same bean) and type-based lookup, matching what `DefaultListableBeanFactory` provides.

```java
// BeanFactoryDemo2.java — run with: java BeanFactoryDemo2.java
import java.util.*;
import java.util.function.*;

public class BeanFactoryDemo2 {

    interface CatalogItem { String display(); }
    record Product(int id, String name, double price) implements CatalogItem {
        public String display() { return String.format("Product[%d] %s @ $%.2f", id, name, price); }
    }
    record Bundle(String name, List<Product> items) implements CatalogItem {
        public String display() { return "Bundle[" + name + "] x" + items.size() + " items"; }
    }

    static class BeanRegistry {
        private final Map<String, Supplier<?>>  defs     = new LinkedHashMap<>();
        private final Map<String, String>       aliases  = new LinkedHashMap<>();
        private final Map<String, Object>       cache    = new LinkedHashMap<>();

        <T> void register(String name, Supplier<T> factory) { defs.put(name, factory); }
        void alias(String alias, String canonical)           { aliases.put(alias, canonical); }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name, Class<T> type) {
            String canonical = aliases.getOrDefault(name, name);
            if (!defs.containsKey(canonical)) throw new RuntimeException("No bean: " + canonical);
            return type.cast(cache.computeIfAbsent(canonical, k -> {
                System.out.println("  [INIT] " + k);
                return defs.get(k).get();
            }));
        }

        @SuppressWarnings("unchecked")
        <T> List<T> getBeansOfType(Class<T> type) {
            List<T> result = new ArrayList<>();
            for (String name : defs.keySet()) {
                Object b = cache.computeIfAbsent(name, k -> defs.get(k).get());
                if (type.isInstance(b)) result.add((T) b);
            }
            return result;
        }
    }

    public static void main(String[] args) {
        BeanRegistry reg = new BeanRegistry();

        Product laptop   = new Product(1, "Laptop",   1299.99);
        Product monitor  = new Product(2, "Monitor",   449.99);

        reg.register("laptop",      () -> laptop);
        reg.register("monitor",     () -> monitor);
        reg.register("devBundle",   () -> new Bundle("Dev Kit", List.of(laptop, monitor)));

        // Aliases — alternative names for the same bean
        reg.alias("primaryLaptop", "laptop");
        reg.alias("display",       "monitor");

        System.out.println("=== Bean lookup by primary name ===");
        System.out.println(reg.getBean("laptop",    Product.class).display());

        System.out.println("\n=== Bean lookup by alias ===");
        System.out.println(reg.getBean("display",   Product.class).display());   // → monitor
        System.out.println("Same obj as 'monitor': " +
            (reg.getBean("display", Product.class) == reg.getBean("monitor", Product.class)));

        System.out.println("\n=== Get all CatalogItem beans ===");
        reg.getBeansOfType(CatalogItem.class).forEach(i -> System.out.println("  " + i.display()));
    }
}
```

How to run: `java BeanFactoryDemo2.java`

Aliases resolve to the same singleton — `getBean("display")` and `getBean("monitor")` return the same object. `getBeansOfType` scans all registered beans and returns those matching the requested interface, which is how Spring's `ApplicationContext.getBeansOfType(Class)` works.

### Level 3 — Advanced

Add `BeanPostProcessor` hooks — callbacks fired after each bean is created but before it is returned. This is how Spring applies AOP proxies, `@PostConstruct`, and validation.

```java
// BeanFactoryDemo3.java — run with: java BeanFactoryDemo3.java
import java.util.*;
import java.util.function.*;

public class BeanFactoryDemo3 {

    // --- Domain ---
    interface Validator { void validate(Object bean, String name); }
    record Product(int id, String name, double price) {}

    // --- BeanPostProcessor contract (mirrors Spring's) ---
    interface BeanPostProcessor {
        default Object postProcessBeforeInit(Object bean, String name) { return bean; }
        default Object postProcessAfterInit(Object bean, String name)  { return bean; }
    }

    // --- Validation post-processor ---
    static class ValidationPostProcessor implements BeanPostProcessor {
        public Object postProcessBeforeInit(Object bean, String name) {
            if (bean instanceof Product p && p.price() < 0)
                throw new RuntimeException("Product price must be >= 0: " + name);
            System.out.println("  [VALIDATE] " + name + " passed validation");
            return bean;
        }
    }

    // --- Logging post-processor (wraps bean in a proxy) ---
    static class LoggingPostProcessor implements BeanPostProcessor {
        public Object postProcessAfterInit(Object bean, String name) {
            System.out.println("  [LOG PROXY] wrapping: " + name);
            return bean;  // in real Spring: return a JDK/CGLIB proxy here
        }
    }

    // --- BeanFactory with post-processor support ---
    static class PostProcessorAwareBeanFactory {
        private final List<BeanPostProcessor> processors = new ArrayList<>();
        private final Map<String, Supplier<?>> defs      = new LinkedHashMap<>();
        private final Map<String, Object>      cache     = new LinkedHashMap<>();

        void addPostProcessor(BeanPostProcessor pp) { processors.add(pp); }
        <T> void register(String name, Supplier<T> f) { defs.put(name, f); }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name, Class<T> type) {
            return type.cast(cache.computeIfAbsent(name, k -> {
                Object raw = defs.get(k).get();
                System.out.println("  [CREATE] " + k);
                for (BeanPostProcessor pp : processors)
                    raw = pp.postProcessBeforeInit(raw, k);
                for (BeanPostProcessor pp : processors)
                    raw = pp.postProcessAfterInit(raw, k);
                return raw;
            }));
        }
    }

    public static void main(String[] args) {
        PostProcessorAwareBeanFactory factory = new PostProcessorAwareBeanFactory();
        factory.addPostProcessor(new ValidationPostProcessor());
        factory.addPostProcessor(new LoggingPostProcessor());

        factory.register("laptop",   () -> new Product(1, "Laptop",   1299.99));
        factory.register("monitor",  () -> new Product(2, "Monitor",   449.99));
        factory.register("freebies", () -> new Product(3, "Freebie",     0.00));

        System.out.println("=== Requesting beans (lazy init + post-processing) ===\n");
        System.out.println(factory.getBean("laptop",   Product.class));
        System.out.println();
        System.out.println(factory.getBean("freebies", Product.class));
        System.out.println();
        System.out.println("=== Second request — cached (post-processors NOT re-run) ===");
        System.out.println(factory.getBean("laptop", Product.class));

        System.out.println("\n=== Negative price would throw at first getBean() call ===");
        factory.register("broken", () -> new Product(99, "Bad", -1.0));
        try { factory.getBean("broken", Product.class); }
        catch (RuntimeException e) { System.out.println("  CAUGHT: " + e.getMessage()); }
    }
}
```

How to run: `java BeanFactoryDemo3.java`

`BeanPostProcessor` hooks run *after* creation but *before* the bean enters the cache. Real Spring uses this to apply `@PostConstruct`, `@PreDestroy`, `@Validated`, and AOP proxies. The broken product's negative price is caught by the validation processor at first `getBean()` — analogous to Spring failing fast when a bean is misconfigured.

## 6. Walkthrough

**Startup — registration phase:**
`factory.register("laptop", ...)` stores a `Supplier<Product>` in `defs`. Nothing is instantiated. Post-processors are registered separately.

**First `getBean("laptop", Product.class)` call:**
1. `cache` has no "laptop" entry → invoke `computeIfAbsent`.
2. `defs.get("laptop").get()` → `new Product(1, "Laptop", 1299.99)` → printed `[CREATE] laptop`.
3. Before-init loop: `ValidationPostProcessor.postProcessBeforeInit` → checks `price >= 0` → passes → prints `[VALIDATE]`. Returns same object.
4. After-init loop: `LoggingPostProcessor.postProcessAfterInit` → prints `[LOG PROXY]`. Returns same object (real Spring returns a proxy).
5. Result stored in `cache`.

**Second `getBean("laptop")` call:**
- `cache` already has "laptop" → returns cached value directly. Post-processors not re-run.

**`getBean("broken")` call:**
1. Creates `Product(99, "Bad", -1.0)`.
2. `ValidationPostProcessor.postProcessBeforeInit` → price < 0 → throws `RuntimeException("Product price must be >= 0: broken")`.
3. Exception propagates to caller; "broken" is NOT cached — next call would retry creation.

In real Spring, `DefaultListableBeanFactory`:
```java
// Real Spring equivalent — uses Spring JARs:
DefaultListableBeanFactory factory = new DefaultListableBeanFactory();
factory.addBeanPostProcessor(new AutowiredAnnotationBeanPostProcessor());
// Register bean definitions via BeanDefinitionReader or manually:
GenericBeanDefinition def = new GenericBeanDefinition();
def.setBeanClass(Product.class);
factory.registerBeanDefinition("laptop", def);
Product p = factory.getBean("laptop", Product.class);
```

## 7. Gotchas & takeaways

> **`BeanFactory` does not pre-instantiate singletons.** Configuration errors (missing dep, invalid value) only surface when `getBean()` is called, not at startup. In production apps this is dangerous — an error in a rarely-used bean goes undetected until it's first requested at runtime. That's the main reason to prefer `ApplicationContext`.

> **`BeanPostProcessor` beans registered in `DefaultListableBeanFactory` must be added manually** (`factory.addBeanPostProcessor(...)`). In `ApplicationContext` they are auto-detected from the bean definitions — no manual registration needed.

- `DefaultListableBeanFactory` is the concrete implementation used internally by all `ApplicationContext` variants.
- Access it via `((ConfigurableApplicationContext) ctx).getBeanFactory()` when you need low-level inspection or programmatic bean registration in a running context.
- Scope defaults to singleton. Use `factory.registerScope("prototype", ...)` or the `@Scope` annotation for other scopes.
- `isPrototype(name)` and `isSingleton(name)` are quick membership checks without triggering instantiation.
- Never use `BeanFactory`'s `getBean` as a service-locator pattern throughout your code — that defeats DI. `getBean` belongs only in application entry points and framework integration code.
