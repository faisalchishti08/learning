---
card: spring-data
gi: 122
slug: serializers-string-json-jdk-etc
title: "Serializers (String, JSON, JDK, etc.)"
---

## 1. What it is

Redis stores everything as raw bytes — it has no concept of a Java object. A `RedisSerializer<T>` is the piece of `RedisTemplate` configuration that converts a Java value to bytes on write and back to a Java value on read. Spring Data Redis ships several: `StringRedisSerializer` (UTF-8 text), `GenericJackson2JsonRedisSerializer` (JSON, human-readable and interoperable), and `JdkSerializationRedisSerializer` (Java's built-in binary serialization, the default for a plain `RedisTemplate`).

```java
@Bean
RedisTemplate<String, Order> orderRedisTemplate(RedisConnectionFactory cf) {
    RedisTemplate<String, Order> template = new RedisTemplate<>();
    template.setConnectionFactory(cf);
    template.setKeySerializer(new StringRedisSerializer());
    template.setValueSerializer(new GenericJackson2JsonRedisSerializer());
    return template;
}
```

## 2. Why & when

The previous card used `StringRedisTemplate`, which quietly handles serialization for you using `StringRedisSerializer` on both keys and values. The moment you need to store something that isn't a plain string — a whole `Order` object, for instance — you need to choose and configure a serializer explicitly, and that choice has real consequences for readability, interoperability, and even correctness across application versions.

Reach for explicit serializer configuration when:

- Caching whole objects (not just strings) — `GenericJackson2JsonRedisSerializer` stores them as readable JSON, which you can inspect with `redis-cli GET key` and which other, non-Java services can also read.
- You need keys to stay human-readable in Redis (for debugging, monitoring, or `redis-cli` exploration) even while values use a richer format — mixing `StringRedisSerializer` for keys with a JSON serializer for values is the common combination.
- You're maintaining or migrating away from `JdkSerializationRedisSerializer` — it's Java-only, produces unreadable binary blobs, and (like all Java serialization) is brittle across class changes and a well-known source of `InvalidClassException` after a redeploy.

## 3. Core concept

```
 Java value:  new Order("1", "PENDING")

 StringRedisSerializer      -- only works on String -- N/A for a whole Order object
 JdkSerializationRedisSerializer  -> [0xAC 0xED 0x00 0x05 ...]   (binary, Java-only, opaque in redis-cli)
 GenericJackson2JsonRedisSerializer -> {"@class":"Order","id":"1","status":"PENDING"}   (readable, cross-language)
```

The same Java object produces a completely different byte representation in Redis depending on which serializer is configured — and only the reader using the *same* serializer can correctly decode it back.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same Order object serializes to opaque binary via JDK serialization or to readable JSON via Jackson">
  <rect x="20" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Order("1", "PENDING")</text>

  <line x1="200" y1="35" x2="260" y2="35" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>
  <rect x="270" y="15" width="220" height="40" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.3"/>
  <text x="380" y="39" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">JDK: binary, Java-only, opaque</text>

  <line x1="200" y1="90" x2="260" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>
  <rect x="270" y="70" width="220" height="40" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.3"/>
  <text x="380" y="94" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">Jackson: JSON, readable, portable</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Two serializers, two very different wire formats for the exact same Java object.

## 5. Runnable example

The scenario: storing whole `Order` objects in Redis, evolving from a JDK-style binary serializer that only round-trips correctly within the same Java class definition, to a JSON serializer that produces readable, interoperable output, to a `RedisTemplate` configured with **different** serializers for keys versus values — the realistic mixed configuration.

### Level 1 — Basic

Model JDK-style serialization: opaque, binary, and Java-only.

```java
import java.io.*;
import java.util.*;

public class SerializersLevel1 {
    public static void main(String[] args) throws Exception {
        JdkSerializationRedisSerializer serializer = new JdkSerializationRedisSerializer();
        Order order = new Order("1", "PENDING");

        byte[] bytes = serializer.serialize(order);
        System.out.println("Serialized to " + bytes.length + " raw bytes (opaque -- try reading these in redis-cli).");

        Order roundTripped = (Order) serializer.deserialize(bytes);
        System.out.println("Deserialized: " + roundTripped);
    }
}

class Order implements Serializable { String id; String status; Order(String id, String status) { this.id = id; this.status = status; } public String toString() { return "Order{" + id + "," + status + "}"; } }

// Stands in for org.springframework.data.redis.serializer.JdkSerializationRedisSerializer.
class JdkSerializationRedisSerializer {
    byte[] serialize(Object obj) throws IOException {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (ObjectOutputStream oos = new ObjectOutputStream(bos)) { oos.writeObject(obj); }
        return bos.toByteArray();
    }
    Object deserialize(byte[] bytes) throws IOException, ClassNotFoundException {
        try (ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(bytes))) { return ois.readObject(); }
    }
}
```

How to run: `java SerializersLevel1.java`

`serialize` produces a raw `byte[]` using Java's own `ObjectOutputStream` — this is exactly what `JdkSerializationRedisSerializer` does under the hood. The bytes round-trip correctly *within this same program*, but they're binary, prefixed with Java-serialization-specific magic numbers, and completely unreadable to `redis-cli`, another language's Redis client, or a future version of the `Order` class with a different `serialVersionUID`.

### Level 2 — Intermediate

Model JSON serialization: a human-readable, cross-language-compatible alternative, matching `GenericJackson2JsonRedisSerializer`.

```java
import java.util.*;

public class SerializersLevel2 {
    public static void main(String[] args) {
        JsonRedisSerializer serializer = new JsonRedisSerializer();
        Order order = new Order("1", "PENDING");

        byte[] bytes = serializer.serialize(order);
        System.out.println("Serialized (what redis-cli GET would actually show): " + new String(bytes));

        Order roundTripped = serializer.deserialize(bytes);
        System.out.println("Deserialized: id=" + roundTripped.id + ", status=" + roundTripped.status);
    }
}

class Order { String id; String status; Order(String id, String status) { this.id = id; this.status = status; } }

// Stands in for org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer (hand-rolled, no library needed here).
class JsonRedisSerializer {
    byte[] serialize(Order order) {
        String json = "{\"id\":\"" + order.id + "\",\"status\":\"" + order.status + "\"}";
        return json.getBytes();
    }
    Order deserialize(byte[] bytes) {
        String json = new String(bytes);
        String id = json.replaceAll(".*\"id\":\"([^\"]+)\".*", "$1");
        String status = json.replaceAll(".*\"status\":\"([^\"]+)\".*", "$1");
        return new Order(id, status);
    }
}
```

How to run: `java SerializersLevel2.java`

Unlike Level 1's opaque binary, the serialized bytes here are readable text — `{"id":"1","status":"PENDING"}` — exactly what a real `GenericJackson2JsonRedisSerializer` would produce (using actual Jackson, not the manual string-building shown here for a dependency-free demo). Anyone running `redis-cli GET order:1` against a real Redis instance using this serializer sees this same readable JSON, and a Python or Node.js service reading the same key can parse it without needing any Java-specific library.

### Level 3 — Advanced

Configure a `RedisTemplate` with **different** serializers for keys (`StringRedisSerializer`) versus values (the JSON serializer) — the realistic mixed setup, matching the intro snippet's `orderRedisTemplate` bean.

```java
import java.util.*;

public class SerializersLevel3 {
    public static void main(String[] args) {
        RedisTemplate template = new RedisTemplate();
        template.setValueSerializer(new JsonRedisSerializer());

        template.set("order:1", new Order("1", "PENDING"));
        template.set("order:2", new Order("2", "SHIPPED"));

        System.out.println("Keys stored as plain, readable strings:");
        template.printRawKeys();

        Order fetched = template.get("order:1");
        System.out.println("Fetched order:1 -> id=" + fetched.id + ", status=" + fetched.status);
    }
}

interface RedisSerializer<T> { byte[] serialize(T value); T deserializeAs(byte[] bytes); }

class StringRedisSerializer implements RedisSerializer<String> {
    public byte[] serialize(String value) { return value.getBytes(); }
    public String deserializeAs(byte[] bytes) { return new String(bytes); }
}

class Order { String id; String status; Order(String id, String status) { this.id = id; this.status = status; } }

class JsonRedisSerializer implements RedisSerializer<Order> {
    public byte[] serialize(Order order) { return ("{\"id\":\"" + order.id + "\",\"status\":\"" + order.status + "\"}").getBytes(); }
    public Order deserializeAs(byte[] bytes) {
        String json = new String(bytes);
        return new Order(json.replaceAll(".*\"id\":\"([^\"]+)\".*", "$1"), json.replaceAll(".*\"status\":\"([^\"]+)\".*", "$1"));
    }
}

// Stands in for a RedisTemplate<String, Order> with setKeySerializer/setValueSerializer configured independently.
class RedisTemplate {
    private final Map<byte[], byte[]> rawStore = new LinkedHashMap<>(); // simulates raw bytes stored in Redis
    RedisSerializer<String> keySerializer = new StringRedisSerializer();
    RedisSerializer<Order> valueSerializer;

    void setValueSerializer(RedisSerializer<Order> s) { this.valueSerializer = s; }

    void set(String key, Order value) {
        rawStore.put(keySerializer.serialize(key), valueSerializer.serialize(value));
    }
    Order get(String key) {
        byte[] rawKey = keySerializer.serialize(key);
        for (var entry : rawStore.entrySet()) {
            if (Arrays.equals(entry.getKey(), rawKey)) return valueSerializer.deserializeAs(entry.getValue());
        }
        return null;
    }
    void printRawKeys() {
        for (byte[] k : rawStore.keySet()) System.out.println("  raw key bytes decode as: " + keySerializer.deserializeAs(k));
    }
}
```

How to run: `java SerializersLevel3.java`

`RedisTemplate` here uses `StringRedisSerializer` for keys unconditionally, and whatever value serializer is injected via `setValueSerializer` (JSON, in this case) — exactly matching the mixed configuration from the intro snippet. Keys remain plain, `redis-cli`-friendly strings (`"order:1"`, `"order:2"`) even though values are serialized as JSON `Order` objects, which is the standard combination for a Redis-backed cache of structured data.

## 6. Walkthrough

Execution starts in `main` for Level 3. `template.setValueSerializer(new JsonRedisSerializer())` wires the JSON serializer for values, while `keySerializer` stays at its default, `StringRedisSerializer`.

`template.set("order:1", new Order("1", "PENDING"))` calls `keySerializer.serialize("order:1")`, producing the plain UTF-8 bytes for `"order:1"`, and `valueSerializer.serialize(order)`, producing the JSON bytes `{"id":"1","status":"PENDING"}`. Both byte arrays are stored as one entry in `rawStore`. The same happens for `"order:2"`.

`template.printRawKeys()` iterates `rawStore.keySet()` and decodes each raw key back through `keySerializer.deserializeAs(...)`, printing `"order:1"` and `"order:2"` as plain readable text — demonstrating that even though the *values* went through JSON serialization, the *keys* stayed simple strings the whole time, because they used a different, independently-configured serializer.

`template.get("order:1")` re-serializes `"order:1"` with `keySerializer` to get the matching raw key bytes, scans `rawStore` for a byte-for-byte match (`Arrays.equals`, since raw `byte[]` doesn't support `.equals` by value), and decodes the matching value's bytes back into an `Order` via `valueSerializer.deserializeAs(...)`.

```
Keys stored as plain, readable strings:
  raw key bytes decode as: order:1
  raw key bytes decode as: order:2
Fetched order:1 -> id=1, status=PENDING
```

In real Spring Data Redis, this same `RedisTemplate<String, Order>` bean, built with `setKeySerializer(new StringRedisSerializer())` and `setValueSerializer(new GenericJackson2JsonRedisSerializer())`, produces keys and values in exactly this shape when inspected with `redis-cli` — `KEYS order:*` returns readable key names, and `GET order:1` returns readable JSON, which is invaluable for debugging a cache in production without writing a Java program to decode it.

## 7. Gotchas & takeaways

> Gotcha: switching a `RedisTemplate`'s serializer after data already exists in Redis makes all existing entries unreadable — the new serializer can't decode bytes written by the old one. Plan serializer changes as a migration (write with the new format, backfill or let old keys naturally expire), not a drop-in swap.

> Gotcha: `JdkSerializationRedisSerializer` (the plain `RedisTemplate`'s default) ties every cached value to the exact class bytecode that wrote it — adding a field, changing a type, or even just recompiling with a different `serialVersionUID` can make previously-cached entries fail to deserialize after a routine deploy.

- Redis only stores bytes; a `RedisSerializer<T>` is what converts Java values to and from those bytes for both keys and values, configured independently on a `RedisTemplate`.
- `StringRedisSerializer` (readable text) is the right default for keys, almost always.
- `GenericJackson2JsonRedisSerializer` (readable JSON) is generally preferable to `JdkSerializationRedisSerializer` (opaque, Java-only binary) for values, since it's debuggable and cross-language compatible.
- `StringRedisTemplate` is just `RedisTemplate` pre-configured with `StringRedisSerializer` for both keys and values — reach for a manually configured `RedisTemplate` once you need to store non-string values.
