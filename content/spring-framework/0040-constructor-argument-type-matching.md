---
card: spring-framework
gi: 40
slug: constructor-argument-type-matching
title: Constructor argument type matching
---

## 1. What it is

**Constructor argument type matching** is the strategy Spring uses when constructor arguments are specified with an explicit `type` attribute (XML) or when the container must select among overloaded constructors by matching parameter types.

In Java configuration this appears as `@Bean` methods: Spring picks the constructor whose parameter list best matches the available beans. In XML it surfaces as `<constructor-arg type="int" value="7500"/>` — telling Spring which overloaded constructor to use when multiple constructors share a parameter name.

```xml
<!-- XML type-matching: disambiguate int vs String for same parameter position -->
<bean id="connectionPool" class="com.example.ConnectionPool">
    <constructor-arg type="java.lang.String" value="jdbc:postgresql://db/shop"/>
    <constructor-arg type="int"              value="10"/>
</bean>
```

```java
// Java config equivalent — Spring resolves by type automatically
@Bean
public ConnectionPool connectionPool() {
    return new ConnectionPool("jdbc:postgresql://db/shop", 10);
}
```

In one sentence: **Constructor argument type matching lets you specify the Java type of each constructor argument to disambiguate overloaded constructors or force coercion of XML string values to primitives — `type="int"` tells Spring to cast `"10"` to `10`.**

## 2. Why & when

Type matching matters specifically when:

- **Overloaded constructors exist.** `ConnectionPool(String url, int maxSize)` vs `ConnectionPool(int maxSize, String url)` — if values are supplied without type hints, Spring may pick the wrong overload.
- **XML values are all strings.** XML has no type system; `"10"` is a string. `type="int"` tells Spring to convert it.
- **Primitives and wrappers.** `int` and `Integer` are resolved differently — `type="java.lang.Integer"` vs `type="int"` — though Spring usually handles both.
- **Same-type ambiguity.** Two `String` parameters that cannot be differentiated by name without debug symbols.

In annotation-driven code (`@Autowired` constructors), type matching is automatic for bean references. Type coercion for scalars requires `@Value("${...}")`.

## 3. Core concept

```
Constructor overload resolution by type:

  Class has two constructors:
    A(String url, int maxSize)
    A(int maxSize, String url)

  Type-matched args given:
    type="java.lang.String" value="jdbc:..."
    type="int"              value="10"

  Spring builds a type signature: [String, int]
  Matches constructor A(String, int) → call it

Without type hints (XML):
  <constructor-arg value="jdbc:..."/>
  <constructor-arg value="10"/>
  Both are strings; Spring tries both constructors and may pick wrong one.

With type hints:
  <constructor-arg type="java.lang.String" value="jdbc:..."/>
  <constructor-arg type="int"              value="10"/>
  Unambiguous: only A(String, int) matches.
```

## 4. Diagram

<svg viewBox="0 0 680 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Type matching: two constructor signatures; type hints select the correct one">
  <defs>
    <marker id="a40" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b40" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#e06c75"/></marker>
  </defs>

  <!-- Args with types -->
  <rect x="10" y="30" width="200" height="48" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="51" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">type=String value="jdbc:..."</text>
  <rect x="10" y="96" width="200" height="48" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="117" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">type=int value="10"</text>

  <!-- Resolver -->
  <rect x="255" y="55" width="180" height="65" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="345" y="76" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Spring type resolver</text>
  <text x="345" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">builds [String, int] signature</text>
  <text x="345" y="109" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">matches constructors</text>

  <line x1="210" y1="54"  x2="252" y2="78"  stroke="#6db33f" stroke-width="1.5" marker-end="url(#a40)"/>
  <line x1="210" y1="120" x2="252" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a40)"/>

  <!-- Two constructors -->
  <rect x="485" y="28" width="185" height="42" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="578" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">A(String url, int maxSize) ✓</text>

  <rect x="485" y="120" width="185" height="42" rx="5" fill="#1c2430" stroke="#e06c75" stroke-width="1.5"/>
  <text x="578" y="143" fill="#e06c75" font-size="9" text-anchor="middle" font-family="sans-serif">A(int maxSize, String url) ✗</text>

  <line x1="435" y1="75" x2="482" y2="49"  stroke="#6db33f" stroke-width="1.5" marker-end="url(#a40)"/>
  <line x1="435" y1="88" x2="482" y2="141" stroke="#e06c75" stroke-width="1.5" marker-end="url(#b40)"/>

  <text x="340" y="175" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Type hints [String, int] uniquely selects A(String, int). Without hints both signatures look like [String, String] from XML.</text>
</svg>

Type hints in `<constructor-arg>` build a signature `[String, int]` that matches exactly one constructor. Without hints, XML supplies `["jdbc:...", "10"]` — two strings — and Spring may guess wrong.

## 5. Runnable example

Scenario: a `ConnectionPool` with two overloaded constructors. Demonstrate type-based selection at the container level.

### Level 1 — Basic

Single constructor with primitive and String — show type coercion from string values.

```java
// CtorTypeMatchDemo.java — run with: java CtorTypeMatchDemo.java
import java.util.*;

public class CtorTypeMatchDemo {

    static class ConnectionPool {
        final String url;
        final int    maxSize;
        final long   timeoutMs;

        // Single constructor: String + int + long
        ConnectionPool(String url, int maxSize, long timeoutMs) {
            this.url = url; this.maxSize = maxSize; this.timeoutMs = timeoutMs;
            System.out.printf("  [BEAN] ConnectionPool(url=%s maxSize=%d timeout=%d)%n",
                url, maxSize, timeoutMs);
        }

        @Override public String toString() {
            return "ConnectionPool{url=" + url + ", maxSize=" + maxSize + ", timeoutMs=" + timeoutMs + "}";
        }
    }

    // Container arg descriptor (mirrors <constructor-arg type="..." value="..."/>)
    record ConstructorArg(String type, String value, Object beanRef) {
        static ConstructorArg ofValue(String type, String value) {
            return new ConstructorArg(type, value, null);
        }
        static ConstructorArg ofBean(Object bean) {
            return new ConstructorArg(null, null, bean);
        }
    }

    static Object coerce(String type, String value) {
        return switch (type) {
            case "java.lang.String", "String" -> value;
            case "int", "java.lang.Integer"  -> Integer.parseInt(value);
            case "long", "java.lang.Long"    -> Long.parseLong(value);
            case "boolean"                   -> Boolean.parseBoolean(value);
            default -> throw new RuntimeException("Unknown type: " + type);
        };
    }

    static class Ctx {
        private final Map<String, Object> beans = new LinkedHashMap<>();

        void registerWithArgs(String name, Class<?> clazz, ConstructorArg... argDefs) throws Exception {
            // Build type signature from arg descriptors
            Object[] resolved = new Object[argDefs.length];
            Class<?>[] types  = new Class<?>[argDefs.length];
            for (int i = 0; i < argDefs.length; i++) {
                ConstructorArg d = argDefs[i];
                if (d.beanRef() != null) {
                    resolved[i] = d.beanRef();
                    types[i]    = d.beanRef().getClass();
                } else {
                    resolved[i] = coerce(d.type(), d.value());
                    types[i]    = resolved[i].getClass();
                    // map primitives
                    if ("int".equals(d.type()) || "java.lang.Integer".equals(d.type()))
                        types[i] = int.class;
                    if ("long".equals(d.type()) || "java.lang.Long".equals(d.type()))
                        types[i] = long.class;
                }
                System.out.printf("  [CTX] arg[%d] type=%-24s value=%s%n", i, types[i].getName(), resolved[i]);
            }
            var ctor = clazz.getDeclaredConstructor(types);
            Object bean = ctor.newInstance(resolved);
            beans.put(name, bean);
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) { return (T) beans.get(name); }
    }

    public static void main(String[] args) throws Exception {
        Ctx ctx = new Ctx();
        System.out.println("=== Container startup (XML-style type-matching) ===");
        ctx.registerWithArgs("primaryPool", ConnectionPool.class,
            ConstructorArg.ofValue("java.lang.String", "jdbc:postgresql://primary:5432/shop"),
            ConstructorArg.ofValue("int",              "20"),
            ConstructorArg.ofValue("long",             "5000")
        );

        System.out.println("\n=== Use the bean ===");
        ConnectionPool pool = ctx.getBean("primaryPool");
        System.out.println("  " + pool);
    }
}
```

How to run: `java CtorTypeMatchDemo.java`

`ConstructorArg.ofValue("int", "20")` mirrors `<constructor-arg type="int" value="20"/>`. The container parses `"20"` into `int 20`, builds the type signature `[String, int, long]`, and finds the matching constructor exactly.

### Level 2 — Intermediate

Overloaded constructors — wrong signature without type hints, correct with type hints.

```java
// CtorTypeMatchDemo2.java — run with: java CtorTypeMatchDemo2.java
import java.lang.reflect.*;
import java.util.*;

public class CtorTypeMatchDemo2 {

    static class ServiceConfig {
        final String host;
        final int    port;
        final String protocol;

        // Overload 1: host, port, protocol
        ServiceConfig(String host, int port, String protocol) {
            this.host = host; this.port = port; this.protocol = protocol;
            System.out.printf("  [CTOR-1] ServiceConfig(host=%s, port=%d, protocol=%s)%n",
                host, port, protocol);
        }

        // Overload 2: protocol, port, host (different order)
        ServiceConfig(String protocol, int port, String host) {
            this.protocol = protocol; this.port = port; this.host = host;
            System.out.printf("  [CTOR-2] ServiceConfig(protocol=%s, port=%d, host=%s)%n",
                protocol, port, host);
        }

        @Override public String toString() {
            return "ServiceConfig{host=" + host + ", port=" + port + ", protocol=" + protocol + "}";
        }
    }

    static Object coerce(String javaType, String value) {
        return switch (javaType) {
            case "java.lang.String" -> value;
            case "int"              -> Integer.parseInt(value);
            default -> throw new RuntimeException("Unknown type: " + javaType);
        };
    }

    // Resolve constructor by matching exact type signature
    static Object createWithTypeSignature(Class<?> clazz,
                                          String[] javaTypes, String[] values) throws Exception {
        Class<?>[] paramTypes = new Class<?>[javaTypes.length];
        Object[]   resolved   = new Object[javaTypes.length];
        for (int i = 0; i < javaTypes.length; i++) {
            paramTypes[i] = javaTypes[i].equals("int") ? int.class
                : Class.forName(javaTypes[i]);
            resolved[i] = coerce(javaTypes[i], values[i]);
        }
        System.out.println("  [CTX] looking for constructor with types: " + Arrays.toString(paramTypes));
        Constructor<?> ctor = clazz.getDeclaredConstructor(paramTypes);
        System.out.println("  [CTX] found: " + ctor);
        return ctor.newInstance(resolved);
    }

    // Without type hints: Spring gets a String[] and guesses — may pick wrong overload
    static Object createWithoutTypeHints(Class<?> clazz, String... values) throws Exception {
        System.out.println("  [CTX] no type hints — all args as String: " + Arrays.toString(values));
        // Convert to String-typed params (as XML without type would)
        try {
            Constructor<?> ctor = clazz.getDeclaredConstructor(String.class, int.class, String.class);
            // XML coercion: Spring tries each constructor in declaration order and picks first parseable
            System.out.println("  [CTX] trying (String, int, String)...");
            return ctor.newInstance(values[0], Integer.parseInt(values[1]), values[2]);
        } catch (Exception e) {
            System.out.println("  [CTX] failed: " + e.getMessage());
            return null;
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Without type hints ===");
        Object c1 = createWithoutTypeHints(ServiceConfig.class,
            "api.example.com", "8443", "https");
        System.out.println("  result: " + c1);

        System.out.println("\n=== With type hints (ctor-1 order) ===");
        Object c2 = createWithTypeSignature(ServiceConfig.class,
            new String[]{"java.lang.String", "int", "java.lang.String"},
            new String[]{"api.example.com",  "8443", "https"});
        System.out.println("  result: " + c2);

        System.out.println("\n=== With type hints (ctor-2 order: protocol, port, host) ===");
        Object c3 = createWithTypeSignature(ServiceConfig.class,
            new String[]{"java.lang.String", "int", "java.lang.String"},
            new String[]{"https",            "8443", "api.example.com"});
        System.out.println("  result (note: host/protocol swapped): " + c3);
    }
}
```

How to run: `java CtorTypeMatchDemo2.java`

Without type hints Spring tries constructors in declaration order — it happens to pick Ctor-1, but `host` and `protocol` may be confused if the values look alike. With type hints the signature `[String, int, String]` is the same for both overloads, so the only disambiguation is the value order — which is why `index` or `name` is needed for truly ambiguous cases (tutorial 41).

### Level 3 — Advanced

Registry of multiple beans where each constructor has a different type profile. Container selects correct constructor per bean definition.

```java
// CtorTypeMatchDemo3.java — run with: java CtorTypeMatchDemo3.java
import java.lang.reflect.*;
import java.util.*;

public class CtorTypeMatchDemo3 {

    interface Worker { String work(String task); }

    static class BatchWorker implements Worker {
        final int batchSize; final long intervalMs;
        BatchWorker(int batchSize, long intervalMs) {
            System.out.printf("  [BEAN] BatchWorker(batchSize=%d intervalMs=%d)%n", batchSize, intervalMs);
            this.batchSize = batchSize; this.intervalMs = intervalMs;
        }
        @Override public String work(String t) {
            return String.format("BATCH[size=%d interval=%dms] processing '%s'", batchSize, intervalMs, t);
        }
    }

    static class QueueWorker implements Worker {
        final String queueName; final int maxRetries;
        QueueWorker(String queueName, int maxRetries) {
            System.out.printf("  [BEAN] QueueWorker(queue=%s retries=%d)%n", queueName, maxRetries);
            this.queueName = queueName; this.maxRetries = maxRetries;
        }
        @Override public String work(String t) {
            return String.format("QUEUE[%s retries=%d] processing '%s'", queueName, maxRetries, t);
        }
    }

    static class StreamWorker implements Worker {
        final String topic; final String groupId; final int partitions;
        StreamWorker(String topic, String groupId, int partitions) {
            System.out.printf("  [BEAN] StreamWorker(topic=%s group=%s partitions=%d)%n",
                topic, groupId, partitions);
            this.topic = topic; this.groupId = groupId; this.partitions = partitions;
        }
        @Override public String work(String t) {
            return String.format("STREAM[%s/%s p=%d] processing '%s'", topic, groupId, partitions, t);
        }
    }

    // Arg spec for type-matched registration
    record ArgSpec(String javaType, String value) {}

    static class Ctx {
        private final Map<String, Worker> beans = new LinkedHashMap<>();

        static Object coerce(String javaType, String value) {
            return switch (javaType) {
                case "java.lang.String" -> value;
                case "int"              -> Integer.parseInt(value);
                case "long"             -> Long.parseLong(value);
                default -> throw new RuntimeException("Unknown: " + javaType);
            };
        }

        void register(String name, Class<? extends Worker> clazz, ArgSpec... specs) throws Exception {
            Class<?>[] types   = new Class<?>[specs.length];
            Object[]   values  = new Object[specs.length];
            for (int i = 0; i < specs.length; i++) {
                types[i]  = specs[i].javaType().equals("int")  ? int.class
                           : specs[i].javaType().equals("long") ? long.class
                           : Class.forName(specs[i].javaType());
                values[i] = coerce(specs[i].javaType(), specs[i].value());
            }
            System.out.print("  [CTX] '" + name + "' constructor types: ");
            System.out.println(Arrays.toString(types));
            Worker w = (Worker) clazz.getDeclaredConstructor(types).newInstance(values);
            beans.put(name, w);
        }

        Worker getBean(String name) { return beans.get(name); }
        Map<String, Worker> getAll() { return Collections.unmodifiableMap(beans); }
    }

    public static void main(String[] args) throws Exception {
        Ctx ctx = new Ctx();

        System.out.println("=== Container startup ===");
        ctx.register("batchWorker", BatchWorker.class,
            new ArgSpec("int",  "50"),
            new ArgSpec("long", "1000")
        );
        ctx.register("queueWorker", QueueWorker.class,
            new ArgSpec("java.lang.String", "order-queue"),
            new ArgSpec("int",              "3")
        );
        ctx.register("streamWorker", StreamWorker.class,
            new ArgSpec("java.lang.String", "orders"),
            new ArgSpec("java.lang.String", "billing-group"),
            new ArgSpec("int",              "12")
        );

        System.out.println("\n=== Workers processing tasks ===");
        ctx.getAll().forEach((name, worker) ->
            System.out.println("  [" + name + "] " + worker.work("process-order-42")));
    }
}
```

How to run: `java CtorTypeMatchDemo3.java`

Three workers, three constructor signatures: `(int, long)`, `(String, int)`, `(String, String, int)`. Each is registered with explicit `ArgSpec(javaType, value)` — mirroring `<constructor-arg type="..." value="..."/>`. Type coercion converts all string values to the correct Java types before invoking each constructor.

## 6. Walkthrough

**Level 3 — BatchWorker registration:**

```
ctx.register("batchWorker", BatchWorker.class,
    ArgSpec("int", "50"), ArgSpec("long", "1000"))

  types[0] = int.class       (javaType="int" → primitive)
  types[1] = long.class      (javaType="long" → primitive)
  values[0] = Integer.parseInt("50")  = 50
  values[1] = Long.parseLong("1000")  = 1000L

  Constructor lookup: BatchWorker.getDeclaredConstructor(int.class, long.class)
  → BatchWorker(int batchSize, long intervalMs) ← exact match

  BatchWorker(50, 1000L) → "[BEAN] BatchWorker(batchSize=50 intervalMs=1000)"
```

**Data flow per worker:**

| Worker | Type signature | Coercions |
|---|---|---|
| `BatchWorker` | `[int, long]` | `"50"` → `50`, `"1000"` → `1000L` |
| `QueueWorker` | `[String, int]` | none, `"3"` → `3` |
| `StreamWorker` | `[String, String, int]` | none, none, `"12"` → `12` |

## 7. Gotchas & takeaways

> **Spring's type coercion converts XML `String` values to primitives, but only with explicit `type=` attributes.** Without `type="int"`, Spring may not know to parse `"10"` as an integer and could throw `IllegalArgumentException` when it attempts to call a constructor that expects `int`.

> **Overloaded constructors with the same number of parameters and the same raw types cannot be disambiguated by type alone** — you must use `index` or `name` (tutorial 41). Type matching only helps when the parameter lists have different types.

- `type="int"` and `type="java.lang.Integer"` behave the same for most purposes; Spring performs unboxing automatically.
- In Java config (`@Bean` methods), the developer controls argument types directly — type-based constructor ambiguity does not arise.
- Spring tries constructors in a "greedy" order — most arguments first. If type hints are incomplete, the wrong constructor may be selected silently.
- `@ConstructorProperties({"url", "maxSize", "timeoutMs"})` on a constructor enables name-based resolution without `type=` in XML.
