---
card: spring-framework
gi: 37
slug: determining-a-bean-s-runtime-type
title: Determining a bean's runtime type
---

## 1. What it is

A **bean's runtime type** is the actual `Class<?>` of the object that lives in the singleton cache — which may differ from the declared type in the `BeanDefinition`.

Three common reasons the runtime type diverges from the declared type:

1. **`FactoryBean<T>`** — `getBean("myFactory")` returns `T`, not `FactoryBean`.
2. **AOP proxy** — `@Transactional` on a class wraps it in a CGLIB subclass; on an interface in a JDK dynamic proxy.
3. **Static factory method** — the declared class is the factory; the runtime type is the return type.

Spring exposes two API points to inspect runtime type without instantiating the bean:

```java
// Ask the container for the type it would return for this name
Class<?> type = ctx.getType("myBean");           // null if indeterminate

// Resolved name → type after FactoryBean and proxy unwrapping
boolean isProduct = ctx.isTypeMatch("myBean", SomeInterface.class);
```

In one sentence: **Determining a bean's runtime type means asking the container what `Class<?>` it will actually give you for a given name — accounting for `FactoryBean` wrapping, AOP proxying, and static/instance factory returns.**

## 2. Why & when

Inspecting runtime type matters when:

- **Type-based autowiring** (`@Autowired`) must resolve the correct implementation from multiple candidates.
- **`BeanPostProcessor`** needs to skip beans of certain types.
- **Debugging** an unexpected injection — the declared type is `ServiceImpl`, but the autowired field receives a `$Proxy42`.
- **Programmatic container introspection** — listing all beans of a given interface for a plugin system.

Concretely: after `@Transactional` is processed, `ctx.getType("userService")` may return `UserService$$EnhancerBySpringCGLIB$$...`, not `UserService`.

## 3. Core concept

```
BeanDefinition declared type vs. runtime type:

  Case 1: Direct bean
    declared = UserServiceImpl.class
    runtime  = UserServiceImpl.class          ← same

  Case 2: FactoryBean
    declared = SqlSessionFactoryBean.class    ← what is registered
    runtime  = SqlSessionFactory.class        ← what getBean() returns

  Case 3: CGLIB proxy (e.g. @Transactional)
    declared = OrderService.class
    runtime  = OrderService$$EnhancerByCGLIB$$12ab34.class

  Case 4: JDK dynamic proxy (class implements interface)
    declared = PaymentServiceImpl.class
    runtime  = $Proxy42 (implements PaymentService)

ctx.getType("beanName"):
  → checks BeanDefinition
  → if FactoryBean, calls getObjectType() without full init if possible
  → returns the effective product type, not the factory type
```

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Declared type in BeanDefinition vs actual runtime type returned by getBean">
  <defs>
    <marker id="a37" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b37" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- 3 column headers -->
  <text x="100" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">BeanDefinition</text>
  <text x="340" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Container Processing</text>
  <text x="580" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Runtime Object</text>

  <!-- Row 1: Direct -->
  <rect x="10" y="30" width="180" height="38" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="100" y="49" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">UserServiceImpl.class</text>
  <text x="100" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">declared type</text>
  <line x1="190" y1="49" x2="490" y2="49" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3" marker-end="url(#a37)"/>
  <text x="340" y="44" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">direct instantiation</text>
  <rect x="500" y="30" width="170" height="38" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="585" y="54" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">UserServiceImpl ← same</text>

  <!-- Row 2: FactoryBean -->
  <rect x="10" y="80" width="180" height="38" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="100" y="99" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">SqlSessionFactoryBean</text>
  <text x="100" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">implements FactoryBean</text>
  <line x1="190" y1="99" x2="490" y2="99" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,3" marker-end="url(#b37)"/>
  <text x="340" y="94" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">getObjectType() / getObject()</text>
  <rect x="500" y="80" width="170" height="38" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="585" y="104" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">SqlSessionFactory ← different</text>

  <!-- Row 3: CGLIB proxy -->
  <rect x="10" y="130" width="180" height="38" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="100" y="149" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService.class</text>
  <text x="100" y="162" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">declared type</text>
  <line x1="190" y1="149" x2="490" y2="149" stroke="#6db33f" stroke-width="1" stroke-dasharray="3,3" marker-end="url(#a37)"/>
  <text x="340" y="144" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">@Transactional → CGLIB subclass</text>
  <rect x="500" y="130" width="170" height="38" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="585" y="150" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService$$CGLIB</text>
  <text x="585" y="163" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">← subclass proxy</text>
</svg>

Declared type in `BeanDefinition` is a hint, not the runtime truth. Always use `ctx.getType()` or `instanceof` checks at runtime.

## 5. Runnable example

Scenario: a `PluginRegistry` that discovers all `Plugin` implementations from the container, including ones created by `FactoryBean` and ones wrapped in a timing proxy.

### Level 1 — Basic

Show the difference between declared class and `getObject()` type.

```java
// BeanRuntimeTypeDemo.java — run with: java BeanRuntimeTypeDemo.java
import java.util.*;

public class BeanRuntimeTypeDemo {

    interface Plugin {
        String name();
        String execute(String input);
    }

    static class LoggingPlugin implements Plugin {
        @Override public String name()              { return "logging"; }
        @Override public String execute(String in)  { return "[LOG] " + in; }
    }

    static class ValidationPlugin implements Plugin {
        @Override public String name()              { return "validation"; }
        @Override public String execute(String in)  { return in.isBlank() ? "[INVALID] empty" : "[VALID] " + in; }
    }

    // A FactoryBean that produces a Plugin
    interface FactoryBean<T> {
        T getObject();
        Class<?> getObjectType();
        default boolean isSingleton() { return true; }
    }

    static class UpperCasePluginFactory implements FactoryBean<Plugin> {
        @Override
        public Plugin getObject() {
            System.out.println("  [FACTORY BEAN] UpperCasePluginFactory.getObject()");
            return new Plugin() {
                @Override public String name()             { return "uppercase"; }
                @Override public String execute(String in) { return in.toUpperCase(); }
            };
        }
        @Override public Class<?> getObjectType() { return Plugin.class; }
    }

    static class BeanEntry {
        final String name;
        final Object rawBean;       // what was registered (may be a FactoryBean)
        final Class<?> declaredType;

        BeanEntry(String name, Object raw) {
            this.name = name; this.rawBean = raw; this.declaredType = raw.getClass();
        }
    }

    static class Ctx {
        private final List<BeanEntry> registry = new ArrayList<>();
        private final Map<String, Object> cache = new HashMap<>();

        void register(String name, Object bean) {
            registry.add(new BeanEntry(name, bean));
            System.out.println("  [CTX] registered '" + name + "' declared=" + bean.getClass().getSimpleName());
        }

        Object getBean(String name) {
            for (BeanEntry e : registry) {
                if (!e.name.equals(name)) continue;
                if (e.rawBean instanceof FactoryBean<?> fb) {
                    return cache.computeIfAbsent(name, k -> fb.getObject());
                }
                return e.rawBean;
            }
            throw new RuntimeException("No bean: " + name);
        }

        // getType(): return the effective type (product type for FactoryBean, declared type otherwise)
        Class<?> getType(String name) {
            for (BeanEntry e : registry) {
                if (!e.name.equals(name)) continue;
                if (e.rawBean instanceof FactoryBean<?> fb) return fb.getObjectType();
                return e.rawBean.getClass();
            }
            throw new RuntimeException("No bean: " + name);
        }

        void printTypeReport() {
            System.out.println("  Name               | Declared type              | Runtime type (getType)");
            System.out.println("  -------------------|----------------------------|-----------------------");
            for (BeanEntry e : registry) {
                String runtimeType = getType(e.name).getSimpleName();
                String declared    = e.declaredType.getSimpleName();
                String diverges    = declared.equals(runtimeType) ? "" : " ← DIFFERENT";
                System.out.printf("  %-18s | %-26s | %s%s%n",
                    e.name, declared, runtimeType, diverges);
            }
        }
    }

    public static void main(String[] args) {
        Ctx ctx = new Ctx();
        System.out.println("=== Container startup ===");
        ctx.register("loggingPlugin",    new LoggingPlugin());
        ctx.register("validationPlugin", new ValidationPlugin());
        ctx.register("uppercasePlugin",  new UpperCasePluginFactory());

        System.out.println("\n=== Type report (before product created) ===");
        ctx.printTypeReport();

        System.out.println("\n=== getBean calls ===");
        Plugin p1 = (Plugin) ctx.getBean("loggingPlugin");
        Plugin p2 = (Plugin) ctx.getBean("uppercasePlugin");   // triggers getObject()
        System.out.println("  logging: " + p1.execute("event=login"));
        System.out.println("  uppercase: " + p2.execute("hello world"));

        System.out.println("\n=== Type report (after product created) ===");
        ctx.printTypeReport();
    }
}
```

How to run: `java BeanRuntimeTypeDemo.java`

`getType("uppercasePlugin")` returns `Plugin.class` (from `getObjectType()`) even before `getObject()` is called. The declared class is `UpperCasePluginFactory`, but the runtime type is `Plugin`. The type report shows "DIFFERENT" for the `FactoryBean` entry.

### Level 2 — Intermediate

Proxy wrapping changes runtime type. Demonstrate with a timing proxy that wraps a `Plugin`.

```java
// BeanRuntimeTypeDemo2.java — run with: java BeanRuntimeTypeDemo2.java
import java.util.*;
import java.lang.reflect.*;

public class BeanRuntimeTypeDemo2 {

    interface Plugin {
        String name();
        String execute(String input);
    }

    static class AnalyticsPlugin implements Plugin {
        @Override public String name()             { return "analytics"; }
        @Override public String execute(String in) {
            System.out.println("  [ANALYTICS] processing: " + in);
            return "analytics:" + in.length();
        }
    }

    // Timing proxy (simulates AOP @Transactional-style wrapping)
    static Object wrapWithTimingProxy(Object target, Class<?>... interfaces) {
        return Proxy.newProxyInstance(
            target.getClass().getClassLoader(), interfaces,
            (proxy, method, args) -> {
                long start = System.nanoTime();
                Object result = method.invoke(target, args);
                long elapsedMicros = (System.nanoTime() - start) / 1_000;
                System.out.printf("  [TIMING] %s.%s() = %dµs%n",
                    target.getClass().getSimpleName(), method.getName(), elapsedMicros);
                return result;
            }
        );
    }

    static class Ctx {
        record BeanEntry(String name, Object bean, Class<?> declaredType, Class<?> runtimeType) {}
        private final List<BeanEntry> beans  = new ArrayList<>();
        private final Map<String, Object> cache = new HashMap<>();

        void registerDirect(String name, Object bean) {
            beans.add(new BeanEntry(name, bean, bean.getClass(), bean.getClass()));
            System.out.println("  [CTX] '" + name + "' direct → " + bean.getClass().getSimpleName());
        }

        void registerProxied(String name, Object target, Class<?>... ifaces) {
            Object proxy = wrapWithTimingProxy(target, ifaces);
            beans.add(new BeanEntry(name, proxy, target.getClass(), proxy.getClass()));
            System.out.println("  [CTX] '" + name + "' proxied → declared="
                + target.getClass().getSimpleName() + " runtime=" + proxy.getClass().getSimpleName());
        }

        Object getBean(String name) {
            return beans.stream().filter(e -> e.name().equals(name)).findFirst()
                .map(BeanEntry::bean).orElseThrow(() -> new RuntimeException("No bean: " + name));
        }

        Class<?> getType(String name) {
            return beans.stream().filter(e -> e.name().equals(name)).findFirst()
                .map(BeanEntry::runtimeType).orElseThrow();
        }

        void printTypeReport() {
            System.out.println("  Bean              | Declared               | Runtime                | isProxy");
            System.out.println("  ------------------|------------------------|------------------------|--------");
            for (var e : beans) {
                boolean isProxy = Proxy.isProxyClass(e.runtimeType());
                System.out.printf("  %-17s | %-22s | %-22s | %s%n",
                    e.name(),
                    e.declaredType().getSimpleName(),
                    e.runtimeType().getSimpleName().replaceAll("\\$\\d+", "$N"),
                    isProxy ? "YES" : "no");
            }
        }

        // getBeansOfType uses runtime type (or declared for interfaces)
        @SuppressWarnings("unchecked")
        <T> Map<String, T> getBeansOfType(Class<T> type) {
            Map<String, T> result = new LinkedHashMap<>();
            for (var e : beans) {
                if (type.isInstance(e.bean())) result.put(e.name(), (T) e.bean());
            }
            return result;
        }
    }

    public static void main(String[] args) {
        Ctx ctx = new Ctx();
        System.out.println("=== Container startup ===");
        ctx.registerDirect("rawPlugin", new AnalyticsPlugin());
        ctx.registerProxied("timedPlugin", new AnalyticsPlugin(), Plugin.class);

        System.out.println("\n=== Type report ===");
        ctx.printTypeReport();

        System.out.println("\n=== Using both beans ===");
        Plugin raw   = (Plugin) ctx.getBean("rawPlugin");
        Plugin timed = (Plugin) ctx.getBean("timedPlugin");
        System.out.println("  raw result:   " + raw.execute("click"));
        System.out.println("  timed result: " + timed.execute("purchase"));

        System.out.println("\n=== Runtime type checks ===");
        System.out.println("  rawPlugin instanceof AnalyticsPlugin: "
            + (ctx.getBean("rawPlugin") instanceof AnalyticsPlugin));
        System.out.println("  timedPlugin instanceof AnalyticsPlugin: "
            + (ctx.getBean("timedPlugin") instanceof AnalyticsPlugin));   // false — proxy!
        System.out.println("  timedPlugin instanceof Plugin: "
            + (ctx.getBean("timedPlugin") instanceof Plugin));             // true — implements interface

        System.out.println("\n=== getBeansOfType(Plugin.class) ===");
        var plugins = ctx.getBeansOfType(Plugin.class);
        System.out.println("  Found: " + plugins.keySet());
    }
}
```

How to run: `java BeanRuntimeTypeDemo2.java`

`timedPlugin` is a JDK dynamic proxy. `ctx.getBean("timedPlugin") instanceof AnalyticsPlugin` is `false` because the proxy class does not extend `AnalyticsPlugin`. But `instanceof Plugin` is `true` because the proxy implements `Plugin`. This is the exact behavior of Spring AOP with `proxyTargetClass=false`.

### Level 3 — Advanced

Combine `FactoryBean` + proxy wrapping. Inspect runtime types programmatically to build a plugin catalog.

```java
// BeanRuntimeTypeDemo3.java — run with: java BeanRuntimeTypeDemo3.java
import java.util.*;
import java.lang.reflect.*;

public class BeanRuntimeTypeDemo3 {

    interface Transformer {
        String transform(String input);
        String getName();
    }

    static class TrimTransformer implements Transformer {
        @Override public String transform(String in) { return in.strip(); }
        @Override public String getName() { return "trim"; }
    }

    static class HashTransformer implements Transformer {
        @Override public String transform(String in) { return "HASH:" + Math.abs(in.hashCode()); }
        @Override public String getName() { return "hash"; }
    }

    interface FactoryBean<T> {
        T getObject();
        Class<?> getObjectType();
        default boolean isSingleton() { return true; }
    }

    static class EncryptTransformerFactory implements FactoryBean<Transformer> {
        private final String algorithm;
        EncryptTransformerFactory(String algo) { this.algorithm = algo; }
        @Override
        public Transformer getObject() {
            System.out.println("  [FACTORY BEAN] EncryptTransformerFactory.getObject()");
            return new Transformer() {
                @Override public String transform(String in) {
                    return algorithm.toUpperCase() + ":" + Integer.toHexString(in.hashCode());
                }
                @Override public String getName() { return "encrypt-" + algorithm; }
            };
        }
        @Override public Class<?> getObjectType() { return Transformer.class; }
    }

    static Object proxy(Object target, Class<?> iface) {
        return Proxy.newProxyInstance(
            target.getClass().getClassLoader(), new Class<?>[]{iface},
            (px, m, as) -> {
                if ("transform".equals(m.getName())) {
                    System.out.println("  [PROXY] intercepting transform()");
                }
                return m.invoke(target, as);
            }
        );
    }

    record BeanMeta(String name, Object raw, Object resolved,
                    Class<?> declaredType, Class<?> runtimeType,
                    boolean isProxy, boolean fromFactory) {}

    static class Ctx {
        private final List<BeanMeta> registry = new ArrayList<>();
        private final Map<String, Object> prodCache = new HashMap<>();

        void registerDirect(String name, Object bean) {
            registry.add(new BeanMeta(name, bean, bean,
                bean.getClass(), bean.getClass(), false, false));
        }

        void registerProxied(String name, Object target, Class<?> iface) {
            Object px = proxy(target, iface);
            registry.add(new BeanMeta(name, target, px,
                target.getClass(), px.getClass(), true, false));
        }

        void registerFactory(String name, FactoryBean<?> fb) {
            // Resolve product now for simplicity (eager init)
            Object product = prodCache.computeIfAbsent(name, k -> fb.getObject());
            registry.add(new BeanMeta(name, fb, product,
                fb.getClass(), fb.getObjectType(), false, true));
        }

        void registerFactoryProxied(String name, FactoryBean<?> fb, Class<?> iface) {
            Object product = fb.getObject();
            Object px = proxy(product, iface);
            prodCache.put(name, px);
            registry.add(new BeanMeta(name, fb, px,
                fb.getClass(), px.getClass(), true, true));
        }

        Object getBean(String name) {
            return registry.stream().filter(m -> m.name().equals(name)).findFirst()
                .map(BeanMeta::resolved).orElseThrow();
        }

        Class<?> getType(String name) {
            return registry.stream().filter(m -> m.name().equals(name)).findFirst()
                .map(BeanMeta::runtimeType).orElseThrow();
        }

        @SuppressWarnings("unchecked")
        <T> Map<String, T> getBeansOfType(Class<T> type) {
            Map<String, T> result = new LinkedHashMap<>();
            for (var m : registry)
                if (type.isInstance(m.resolved())) result.put(m.name(), (T) m.resolved());
            return result;
        }

        void printTypeReport() {
            System.out.println("  Name                | Declared           | Runtime            | Proxy | Factory");
            System.out.println("  -------------------|--------------------|--------------------|-------|--------");
            for (var m : registry) {
                String rt = m.runtimeType().getSimpleName().replaceAll("\\$\\d+", "$N");
                System.out.printf("  %-19s | %-18s | %-18s | %-5s | %s%n",
                    m.name(),
                    m.declaredType().getSimpleName(),
                    rt,
                    m.isProxy() ? "YES" : "no",
                    m.fromFactory() ? "YES" : "no");
            }
        }
    }

    public static void main(String[] args) {
        Ctx ctx = new Ctx();
        System.out.println("=== Container startup ===");
        ctx.registerDirect("trimTransformer",  new TrimTransformer());
        ctx.registerProxied("hashTransformer", new HashTransformer(), Transformer.class);
        ctx.registerFactory("encryptTransformerAES",  new EncryptTransformerFactory("aes"));
        ctx.registerFactoryProxied("encryptTransformerRSA",
            new EncryptTransformerFactory("rsa"), Transformer.class);

        System.out.println("\n=== Type report ===");
        ctx.printTypeReport();

        System.out.println("\n=== Use all transformers ===");
        String input = "secret-data";
        ctx.getBeansOfType(Transformer.class).forEach((name, t) ->
            System.out.printf("  %-30s → %s%n", name, t.transform(input))
        );

        System.out.println("\n=== Runtime type checks ===");
        Object hash = ctx.getBean("hashTransformer");
        System.out.println("  hashTransformer instanceof HashTransformer: " + (hash instanceof HashTransformer));
        System.out.println("  hashTransformer instanceof Transformer:     " + (hash instanceof Transformer));
        System.out.println("  getType(hashTransformer): " + ctx.getType("hashTransformer").getSimpleName());
        System.out.println("  getType(encryptTransformerAES): " + ctx.getType("encryptTransformerAES").getSimpleName());
    }
}
```

How to run: `java BeanRuntimeTypeDemo3.java`

Four beans show four different runtime type situations: direct (declared == runtime), proxied direct (declared=impl, runtime=proxy), factory (declared=FactoryBean, runtime=product), factory+proxied (declared=FactoryBean, runtime=proxy). `getBeansOfType(Transformer.class)` finds all four because the resolved objects all implement `Transformer`.

## 6. Walkthrough

**Level 3 — type report:**

| Name | Declared | Runtime | Proxy | Factory |
|---|---|---|---|---|
| `trimTransformer` | `TrimTransformer` | `TrimTransformer` | no | no |
| `hashTransformer` | `HashTransformer` | `$Proxy$N` | YES | no |
| `encryptTransformerAES` | `EncryptTransformerFactory` | `Transformer` | no | YES |
| `encryptTransformerRSA` | `EncryptTransformerFactory` | `$Proxy$N` | YES | YES |

**`getType("encryptTransformerAES")`** returns `Transformer.class` — the `FactoryBean.getObjectType()` value, not the factory class.

**`getType("encryptTransformerRSA")`** returns `$Proxy$N.class` — the proxy class. The proxy implements `Transformer`, so `isAssignableFrom(Transformer.class)` is still true for type-based lookup.

## 7. Gotchas & takeaways

> **`instanceof` on a proxied bean fails for the concrete class.** `orderService instanceof OrderServiceImpl` is `false` when Spring wraps it in a CGLIB or JDK proxy. Use interface-level checks (`instanceof OrderService`) or `ctx.getType()` instead.

> **`FactoryBean.getObjectType()` must be accurate.** If it returns `null` or the wrong type, type-based autowiring silently skips the bean — you get `NoSuchBeanDefinitionException` even though the bean exists.

- `ctx.getType(name)` consults `getObjectType()` for `FactoryBean` entries, avoiding a premature `getObject()` call.
- CGLIB proxies are subclasses, so `instanceof ConcreteClass` still works. JDK dynamic proxies are NOT subclasses, so only interface checks work.
- `ctx.isTypeMatch(name, type)` is the Spring API equivalent of `type.isAssignableFrom(ctx.getType(name))`.
- When debugging an unexpected null injection, print the runtime type: `System.out.println(ctx.getBean("name").getClass())` reveals any proxy wrapping.
- Spring's `@Primary` and `@Qualifier` work on the runtime type, not the declared type, which is why proxy-wrapped beans still participate in type-based injection.
