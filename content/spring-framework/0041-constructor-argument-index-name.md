---
card: spring-framework
gi: 41
slug: constructor-argument-index-name
title: Constructor argument index/name
---

## 1. What it is

**Constructor argument index and name** are two additional resolution strategies for `<constructor-arg>` in XML that target a specific parameter by its position (0-based `index`) or its declared name (`name`).

```xml
<!-- Index-based: first arg (index=0) gets the URL -->
<bean id="repo" class="com.example.UserRepository">
    <constructor-arg index="0" value="jdbc:postgresql://db:5432/app"/>
    <constructor-arg index="1" value="10"/>
</bean>

<!-- Name-based: arg named 'maxPoolSize' gets the value -->
<bean id="repo" class="com.example.UserRepository">
    <constructor-arg name="dataSourceUrl" value="jdbc:postgresql://db:5432/app"/>
    <constructor-arg name="maxPoolSize"   value="10"/>
</bean>
```

In Java config the equivalent is writing arguments in order in the `@Bean` method body. In annotation-driven code, `@Qualifier` or `@Value` annotations on constructor parameters provide the same control.

In one sentence: **Index resolves constructor arguments by their 0-based position in the parameter list; name resolves them by the declared parameter name — both eliminate ambiguity when type matching alone cannot distinguish two parameters of the same type.**

## 2. Why & when

- **Two parameters of the same type.** `ConnectionPool(String readUrl, String writeUrl)` — type alone cannot tell them apart. `index=0` / `index=1` or `name="readUrl"` / `name="writeUrl"` fix this.
- **XML where order matters.** Without explicit index or name, Spring uses positional order from the XML file — fragile if anyone reorders `<constructor-arg>` elements.
- **Name-based resolution requires parameter name info.** Names are available when the class is compiled with `-parameters` (`javac -parameters`) or when `@ConstructorProperties` is declared on the constructor.
- **Prefer name over index** in XML: names survive constructor signature refactoring; indices break if a parameter is inserted.

## 3. Core concept

```
Constructor: ConnectionPool(String readUrl, String writeUrl, int maxSize)

Index-based resolution:
  index=0 → readUrl   argument
  index=1 → writeUrl  argument
  index=2 → maxSize   argument (type coercion: "10" → 10)

Name-based resolution (requires -parameters or @ConstructorProperties):
  name="readUrl"   → first  String arg
  name="writeUrl"  → second String arg
  name="maxSize"   → int arg

Annotation-based (Java/annotation config):
  @Value("${db.read.url}")  String readUrl
  @Value("${db.write.url}") String writeUrl
  @Value("${db.pool.max}")  int maxSize
```

## 4. Diagram

<svg viewBox="0 0 680 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Index vs name resolution: both map values to constructor parameters; index uses position, name uses parameter name">
  <defs>
    <marker id="a41" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b41" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Index column -->
  <text x="110" y="22" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Index-based</text>
  <rect x="10"  y="32" width="200" height="36" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">index=0 → "jdbc:..../read"</text>
  <rect x="10"  y="76" width="200" height="36" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="99" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">index=1 → "jdbc:..../write"</text>
  <rect x="10"  y="120" width="200" height="36" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="143" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">index=2 → "10"</text>

  <!-- Name column -->
  <text x="380" y="22" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Name-based</text>
  <rect x="280" y="32" width="200" height="36" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="380" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">name="readUrl" → "jdbc:.../read"</text>
  <rect x="280" y="76" width="200" height="36" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="380" y="99" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">name="writeUrl" → "jdbc:.../write"</text>
  <rect x="280" y="120" width="200" height="36" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="380" y="143" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">name="maxSize" → "10"</text>

  <!-- Constructor -->
  <rect x="510" y="55" width="165" height="70" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="593" y="76" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ConnectionPool(</text>
  <text x="593" y="93" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">  String readUrl,</text>
  <text x="593" y="109" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">  String writeUrl,</text>
  <text x="593" y="123" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">  int maxSize)</text>

  <line x1="210" y1="104" x2="508" y2="90"  stroke="#6db33f" stroke-width="1.2" marker-end="url(#a41)"/>
  <line x1="480" y1="104" x2="508" y2="90"  stroke="#79c0ff" stroke-width="1.2" marker-end="url(#b41)"/>

  <text x="340" y="176" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Both strategies inject the same constructor. Index is brittle to reordering; name requires parameter name info.</text>
</svg>

Index and name are alternative paths to the same constructor. Name is more resilient but requires `-parameters` or `@ConstructorProperties`.

## 5. Runnable example

Scenario: a `ReplicationConfig` with a read URL, write URL, and pool size — two `String` parameters that cannot be disambiguated by type alone.

### Level 1 — Basic

Index-based resolution: position 0, 1, 2.

```java
// CtorIndexNameDemo.java — run with: java CtorIndexNameDemo.java
import java.lang.reflect.*;
import java.util.*;

public class CtorIndexNameDemo {

    static class ReplicationConfig {
        final String readUrl;
        final String writeUrl;
        final int    maxPoolSize;

        // Two String params + one int — type alone cannot distinguish read vs write
        ReplicationConfig(String readUrl, String writeUrl, int maxPoolSize) {
            this.readUrl = readUrl; this.writeUrl = writeUrl; this.maxPoolSize = maxPoolSize;
            System.out.printf("  [BEAN] ReplicationConfig(read=%s write=%s pool=%d)%n",
                readUrl, writeUrl, maxPoolSize);
        }
    }

    // Arg spec: index + value (mirrors <constructor-arg index="0" value="..."/>)
    record IndexedArg(int index, String value, String javaType) {}

    static Object createByIndex(Class<?> clazz, IndexedArg... specs) throws Exception {
        // Sort specs by index
        IndexedArg[] sorted = Arrays.copyOf(specs, specs.length);
        Arrays.sort(sorted, Comparator.comparingInt(IndexedArg::index));

        // Get the single constructor (or choose by param count)
        Constructor<?> ctor = Arrays.stream(clazz.getDeclaredConstructors())
            .filter(c -> c.getParameterCount() == sorted.length)
            .findFirst().orElseThrow(() -> new RuntimeException("No matching constructor"));

        Object[] args = new Object[sorted.length];
        Class<?>[] paramTypes = ctor.getParameterTypes();
        for (IndexedArg spec : sorted) {
            int i = spec.index();
            args[i] = switch (paramTypes[i].getName()) {
                case "int"              -> Integer.parseInt(spec.value());
                case "java.lang.String" -> spec.value();
                default                 -> spec.value();
            };
            System.out.printf("  [CTX] index=%d type=%-20s value=%s%n",
                i, paramTypes[i].getSimpleName(), args[i]);
        }
        return ctor.newInstance(args);
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Index-based constructor arg resolution ===");
        ReplicationConfig cfg = (ReplicationConfig) createByIndex(ReplicationConfig.class,
            new IndexedArg(0, "jdbc:postgresql://read-replica:5432/app",  "java.lang.String"),
            new IndexedArg(1, "jdbc:postgresql://primary:5432/app",       "java.lang.String"),
            new IndexedArg(2, "15",                                        "int")
        );
        System.out.println("\n  readUrl:     " + cfg.readUrl);
        System.out.println("  writeUrl:    " + cfg.writeUrl);
        System.out.println("  maxPoolSize: " + cfg.maxPoolSize);
    }
}
```

How to run: `java CtorIndexNameDemo.java`

Specs are sorted by index then applied in order. `index=0` targets the first parameter (`readUrl`), `index=1` the second (`writeUrl`), `index=2` the third (`maxPoolSize`). Coercion to `int` is driven by the actual parameter type from reflection, not the `javaType` hint.

### Level 2 — Intermediate

Name-based resolution using `@ConstructorProperties`.

```java
// CtorIndexNameDemo2.java — run with: java CtorIndexNameDemo2.java
import java.beans.ConstructorProperties;
import java.lang.reflect.*;
import java.util.*;

public class CtorIndexNameDemo2 {

    static class ShardConfig {
        final String shardId;
        final String primaryUrl;
        final String replicaUrl;
        final int    maxConnections;

        @ConstructorProperties({"shardId", "primaryUrl", "replicaUrl", "maxConnections"})
        ShardConfig(String shardId, String primaryUrl, String replicaUrl, int maxConnections) {
            this.shardId = shardId; this.primaryUrl = primaryUrl;
            this.replicaUrl = replicaUrl; this.maxConnections = maxConnections;
            System.out.printf("  [BEAN] ShardConfig(shard=%s primary=%s replica=%s maxConn=%d)%n",
                shardId, primaryUrl, replicaUrl, maxConnections);
        }
    }

    // Named arg spec: mirrors <constructor-arg name="shardId" value="..."/>
    record NamedArg(String name, String value) {}

    static Object createByName(Class<?> clazz, NamedArg... specs) throws Exception {
        // Build a name→value map
        Map<String, String> argMap = new LinkedHashMap<>();
        for (NamedArg spec : specs) argMap.put(spec.name(), spec.value());

        // Find constructor with @ConstructorProperties
        Constructor<?> target = null;
        String[] paramNames   = null;
        for (Constructor<?> c : clazz.getDeclaredConstructors()) {
            ConstructorProperties cp = c.getAnnotation(ConstructorProperties.class);
            if (cp != null) { target = c; paramNames = cp.value(); break; }
        }
        if (target == null) throw new RuntimeException("No @ConstructorProperties constructor");

        Class<?>[] paramTypes = target.getParameterTypes();
        Object[] resolved = new Object[paramNames.length];
        for (int i = 0; i < paramNames.length; i++) {
            String n = paramNames[i];
            String v = argMap.get(n);
            if (v == null) throw new RuntimeException("No value for param: " + n);
            resolved[i] = paramTypes[i] == int.class ? Integer.parseInt(v) : v;
            System.out.printf("  [CTX] name=%-20s type=%-12s value=%s%n",
                n, paramTypes[i].getSimpleName(), resolved[i]);
        }
        return target.newInstance(resolved);
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Name-based constructor arg resolution ===");
        ShardConfig cfg = (ShardConfig) createByName(ShardConfig.class,
            // Order in XML does not matter — resolved by name
            new NamedArg("replicaUrl",     "jdbc:postgresql://shard1-replica:5432/app"),
            new NamedArg("maxConnections", "8"),
            new NamedArg("shardId",        "shard-1"),
            new NamedArg("primaryUrl",     "jdbc:postgresql://shard1-primary:5432/app")
        );
        System.out.println("\n  shardId:        " + cfg.shardId);
        System.out.println("  primaryUrl:     " + cfg.primaryUrl);
        System.out.println("  replicaUrl:     " + cfg.replicaUrl);
        System.out.println("  maxConnections: " + cfg.maxConnections);
    }
}
```

How to run: `java CtorIndexNameDemo2.java`

`@ConstructorProperties({"shardId","primaryUrl","replicaUrl","maxConnections"})` provides the parameter names at runtime. The named-arg map intentionally supplies them out of constructor order (`replicaUrl` first, `shardId` last) — the resolver uses names to place each value in the correct position. This mirrors the XML behaviour where `<constructor-arg>` elements can appear in any order when `name=` is used.

### Level 3 — Advanced

Multiple beans of the same type in a registry: index-based vs name-based resolution compared side by side, with error detection for missing or duplicate names.

```java
// CtorIndexNameDemo3.java — run with: java CtorIndexNameDemo3.java
import java.beans.ConstructorProperties;
import java.lang.reflect.*;
import java.util.*;

public class CtorIndexNameDemo3 {

    @ConstructorProperties({"topic", "bootstrapServers", "groupId", "maxPollRecords"})
    static class KafkaConsumerConfig {
        final String topic; final String bootstrapServers; final String groupId; final int maxPollRecords;
        KafkaConsumerConfig(String topic, String bootstrapServers, String groupId, int maxPollRecords) {
            this.topic = topic; this.bootstrapServers = bootstrapServers;
            this.groupId = groupId; this.maxPollRecords = maxPollRecords;
            System.out.printf("  [BEAN] KafkaConsumerConfig(topic=%s group=%s maxPoll=%d)%n",
                topic, groupId, maxPollRecords);
        }
    }

    @ConstructorProperties({"topic", "bootstrapServers", "acks", "batchSize"})
    static class KafkaProducerConfig {
        final String topic; final String bootstrapServers; final String acks; final int batchSize;
        KafkaProducerConfig(String topic, String bootstrapServers, String acks, int batchSize) {
            this.topic = topic; this.bootstrapServers = bootstrapServers;
            this.acks = acks; this.batchSize = batchSize;
            System.out.printf("  [BEAN] KafkaProducerConfig(topic=%s acks=%s batchSize=%d)%n",
                topic, acks, batchSize);
        }
    }

    enum Strategy { INDEX, NAME }

    record ArgDef(Strategy strategy, int index, String name, String value) {
        static ArgDef byIndex(int idx, String value) { return new ArgDef(Strategy.INDEX, idx, null, value); }
        static ArgDef byName(String name, String value) { return new ArgDef(Strategy.NAME, -1, name, value); }
    }

    static Object create(Class<?> clazz, ArgDef... defs) throws Exception {
        // Determine strategy (must be homogeneous for simplicity)
        Strategy strat = defs[0].strategy();

        Constructor<?> ctor = null;
        String[] paramNames = null;
        for (Constructor<?> c : clazz.getDeclaredConstructors()) {
            ConstructorProperties cp = c.getAnnotation(ConstructorProperties.class);
            if (cp != null && c.getParameterCount() == defs.length) {
                ctor = c; paramNames = cp.value(); break;
            }
        }
        if (ctor == null) throw new RuntimeException("No matching constructor found");

        Class<?>[] paramTypes = ctor.getParameterTypes();
        Object[] resolved = new Object[paramTypes.length];

        if (strat == Strategy.INDEX) {
            for (ArgDef d : defs) {
                int i = d.index();
                resolved[i] = paramTypes[i] == int.class ? Integer.parseInt(d.value()) : d.value();
                System.out.printf("  [CTX-IDX] index=%d → %s%n", i, resolved[i]);
            }
        } else {
            Map<String, String> byName = new LinkedHashMap<>();
            for (ArgDef d : defs) byName.put(d.name(), d.value());
            for (int i = 0; i < paramNames.length; i++) {
                String n = paramNames[i];
                String v = byName.get(n);
                if (v == null) throw new RuntimeException("Missing named arg: " + n);
                resolved[i] = paramTypes[i] == int.class ? Integer.parseInt(v) : v;
                System.out.printf("  [CTX-NAME] name=%-20s → %s%n", n, resolved[i]);
            }
        }
        return ctor.newInstance(resolved);
    }

    public static void main(String[] args) throws Exception {
        String BROKERS = "broker1:9092,broker2:9092";

        System.out.println("=== Consumer config (index-based) ===");
        KafkaConsumerConfig consumer = (KafkaConsumerConfig) create(KafkaConsumerConfig.class,
            ArgDef.byIndex(0, "orders"),
            ArgDef.byIndex(1, BROKERS),
            ArgDef.byIndex(2, "billing-consumers"),
            ArgDef.byIndex(3, "500")
        );
        System.out.println("  group=" + consumer.groupId + " maxPoll=" + consumer.maxPollRecords);

        System.out.println("\n=== Producer config (name-based, out-of-order in defs) ===");
        KafkaProducerConfig producer = (KafkaProducerConfig) create(KafkaProducerConfig.class,
            ArgDef.byName("batchSize",        "16384"),
            ArgDef.byName("topic",            "orders"),
            ArgDef.byName("acks",             "all"),
            ArgDef.byName("bootstrapServers", BROKERS)
        );
        System.out.println("  acks=" + producer.acks + " batchSize=" + producer.batchSize);

        System.out.println("\n=== Comparison: same class, wrong index order would produce wrong result ===");
        System.out.println("  With index: order of ArgDef.byIndex(i, v) determines which param gets v");
        System.out.println("  With name:  ArgDef.byName defs can be in any order — name is authoritative");
    }
}
```

How to run: `java CtorIndexNameDemo3.java`

`KafkaConsumerConfig` registered with index-based args in order 0–3. `KafkaProducerConfig` registered with name-based args intentionally out of order (`batchSize` first). Both resolve to the same correct constructor call. The final print demonstrates the key difference: index order in `ArgDef` definitions matters; name order does not.

## 6. Walkthrough

**Level 3 — producer name-based:**

```
ArgDef defs (in definition order):
  name="batchSize"        value="16384"
  name="topic"            value="orders"
  name="acks"             value="all"
  name="bootstrapServers" value="broker1:9092,..."

@ConstructorProperties names array (constructor order):
  [0] "topic"
  [1] "bootstrapServers"
  [2] "acks"
  [3] "batchSize"

Resolution:
  i=0: name="topic"             → byName["topic"]="orders"
  i=1: name="bootstrapServers"  → byName["bootstrapServers"]="broker1:9092,..."
  i=2: name="acks"              → byName["acks"]="all"
  i=3: name="batchSize"         → byName["batchSize"]="16384" → Integer.parseInt → 16384

Constructor call: KafkaProducerConfig("orders", "broker1:...", "all", 16384) ✓
```

## 7. Gotchas & takeaways

> **Name-based resolution requires parameter names in the bytecode.** Without `-parameters` javac flag or `@ConstructorProperties`, Spring cannot resolve by name and falls back to type, potentially failing for same-type parameters.

> **Index is 0-based and fragile.** Adding a parameter before index=2 shifts all subsequent parameters — XML definitions with hard-coded indices break silently by injecting the wrong values into the wrong positions.

- `@ConstructorProperties` is a standard Java annotation (`java.beans`) that explicitly provides parameter names — no compiler flag needed.
- In Spring's XML, `<constructor-arg name="..." value="..."/>` is safer than `<constructor-arg index="..."/>` because names survive insertion/deletion of other parameters.
- In annotation config, `@Qualifier("name")` on constructor parameters is the idiomatic replacement for name-based XML resolution.
- Index and name can be mixed in the same XML bean definition, but this is unusual and prone to conflicts.
- Spring's `ConstructorResolver` class handles this logic internally — it ranks candidate constructors and picks the best match.
