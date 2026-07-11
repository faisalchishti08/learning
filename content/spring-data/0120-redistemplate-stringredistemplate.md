---
card: spring-data
gi: 120
slug: redistemplate-stringredistemplate
title: "RedisTemplate / StringRedisTemplate"
---

## 1. What it is

`RedisTemplate<K, V>` is Spring Data Redis's central, blocking API for working with Redis — get/set values, manipulate lists/sets/hashes, and more, all built on top of a `RedisConnectionFactory` (the previous card). `StringRedisTemplate` is a pre-configured convenience subclass that assumes `String` keys and values, which is what most applications actually want, since Redis itself is fundamentally a byte-string store.

```java
@Autowired StringRedisTemplate redisTemplate;

redisTemplate.opsForValue().set("order:1:status", "PENDING");
String status = redisTemplate.opsForValue().get("order:1:status");
```

## 2. Why & when

Redis stores everything as bytes; a generic `RedisTemplate<Object, Object>` needs to know how to turn your Java objects into bytes and back — that's the job of the serializers covered in the next card. `RedisTemplate` handles that translation and exposes Redis's rich data structure operations (strings, lists, sets, hashes, sorted sets) through typed, convenient methods, instead of every call site working with raw bytes and manual serialization.

Reach for `RedisTemplate`/`StringRedisTemplate` when:

- You need direct, imperative access to Redis operations — caching a computed value, incrementing a counter, pushing onto a list — without a repository abstraction in between.
- Your keys and values are naturally strings (session tokens, cache keys, JSON blobs) — `StringRedisTemplate` is the default, low-friction choice for this, which covers the large majority of real usage.
- You need a custom key/value type that isn't a plain string — a full `RedisTemplate<K, V>` with explicitly configured serializers (the next card) gives you that flexibility.

## 3. Core concept

```
 RedisTemplate<Object, Object>       -- generic, needs serializers configured explicitly
      |
      +-- StringRedisTemplate        -- RedisTemplate<String, String> with StringRedisSerializer
                                          pre-wired for keys AND values

 redisTemplate.opsForValue().set("order:1:status", "PENDING")
      |
      v
 SET order:1:status "PENDING"     (the actual Redis command sent over the wire)
```

`StringRedisTemplate` is not a different API — it's `RedisTemplate` with the most common serializer configuration already applied, so most applications never need to configure serializers themselves.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Java call through RedisTemplate is serialized and sent to Redis as a raw SET command">
  <rect x="20" y="50" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="72" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">opsForValue().set(</text>
  <text x="110" y="86" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">"order:1:status", "PENDING")</text>

  <rect x="250" y="50" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">serialize to bytes</text>

  <rect x="440" y="50" width="180" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="530" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">SET order:1:status PENDING</text>

  <line x1="200" y1="75" x2="245" y2="75" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="390" y1="75" x2="435" y2="75" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Every `RedisTemplate` call is translated into a raw Redis protocol command, serialized through whatever serializer is configured for keys and values.

## 5. Runnable example

The scenario: tracking an order's status in Redis, evolving from a `StringRedisTemplate`-style value operation, to using `opsForValue().increment` for a numeric counter (a common cache/rate-limit pattern), to combining several operations with an expiration, matching real caching usage.

### Level 1 — Basic

Model `StringRedisTemplate`'s core value operations against an in-memory stand-in for Redis.

```java
import java.util.*;

public class RedisTemplateLevel1 {
    public static void main(String[] args) {
        StringRedisTemplate redisTemplate = new StringRedisTemplate();

        redisTemplate.opsForValue().set("order:1:status", "PENDING");
        String status = redisTemplate.opsForValue().get("order:1:status");
        System.out.println("Status: " + status);

        redisTemplate.opsForValue().set("order:1:status", "SHIPPED"); // SET overwrites the previous value
        System.out.println("Updated status: " + redisTemplate.opsForValue().get("order:1:status"));

        System.out.println("Missing key returns: " + redisTemplate.opsForValue().get("order:999:status"));
    }
}

// Stands in for the raw Redis server -- a String-to-String key/value store.
class RedisServer { Map<String, String> data = new HashMap<>(); }

class ValueOperations {
    private final RedisServer server;
    ValueOperations(RedisServer server) { this.server = server; }
    void set(String key, String value) { server.data.put(key, value); }
    String get(String key) { return server.data.get(key); } // null if absent, matching real Redis GET on a missing key
}

// Stands in for org.springframework.data.redis.core.StringRedisTemplate.
class StringRedisTemplate {
    private final RedisServer server = new RedisServer();
    private final ValueOperations valueOps = new ValueOperations(server);
    ValueOperations opsForValue() { return valueOps; }
}
```

How to run: `java RedisTemplateLevel1.java`

`opsForValue()` returns a handle to Redis's simple string-value operations (`GET`/`SET`), matching `StringRedisTemplate.opsForValue()`. `set` on an existing key overwrites it, and `get` on a key that was never set returns `null` — exactly Redis's own semantics for a missing key.

### Level 2 — Intermediate

Add `increment`, matching Redis's atomic `INCR` command — a value stored as a number that Redis (not the application) increments server-side, avoiding a read-modify-write race.

```java
import java.util.*;

public class RedisTemplateLevel2 {
    public static void main(String[] args) {
        StringRedisTemplate redisTemplate = new StringRedisTemplate();

        redisTemplate.opsForValue().set("order:1:viewCount", "0");

        long v1 = redisTemplate.opsForValue().increment("order:1:viewCount"); // INCR -- atomic, server-side
        long v2 = redisTemplate.opsForValue().increment("order:1:viewCount");
        long v3 = redisTemplate.opsForValue().increment("order:1:viewCount");

        System.out.println("View count after 3 increments: " + v3);

        long byFive = redisTemplate.opsForValue().incrementBy("order:1:viewCount", 5); // INCRBY
        System.out.println("View count after +5: " + byFive);
    }
}

class RedisServer { Map<String, String> data = new HashMap<>(); }

class ValueOperations {
    private final RedisServer server;
    ValueOperations(RedisServer server) { this.server = server; }
    void set(String key, String value) { server.data.put(key, value); }
    String get(String key) { return server.data.get(key); }

    long increment(String key) { return incrementBy(key, 1); }
    long incrementBy(String key, long delta) {
        long current = server.data.containsKey(key) ? Long.parseLong(server.data.get(key)) : 0;
        long updated = current + delta;
        server.data.put(key, String.valueOf(updated)); // Redis stores the result BACK as a string
        return updated;
    }
}

class StringRedisTemplate {
    private final RedisServer server = new RedisServer();
    private final ValueOperations valueOps = new ValueOperations(server);
    ValueOperations opsForValue() { return valueOps; }
}
```

How to run: `java RedisTemplateLevel2.java`

`increment`/`incrementBy` mirror Redis's `INCR`/`INCRBY` commands: the increment happens atomically on the "server" (here, inside `ValueOperations`), avoiding the read-modify-write race a naive `get`, add in Java, `set` sequence would have under concurrent access — the same atomicity concern the earlier optimistic-locking card raised for MongoDB, solved here by Redis's native atomic counter commands instead.

### Level 3 — Advanced

Combine a value write with an **expiration** (`SET ... EX`), matching a common caching pattern: cache a computed value for a bounded time, and recompute it once the entry expires.

```java
import java.util.*;

public class RedisTemplateLevel3 {
    // Simulates an expensive computation (e.g. a slow database aggregate) that we want to cache.
    static int callCount = 0;
    static String computeExpensiveOrderSummary(String orderId) {
        callCount++;
        return "summary-for-" + orderId + "-v" + callCount;
    }

    static String getCachedSummary(StringRedisTemplate redisTemplate, String orderId, long nowMillis) {
        String cacheKey = "order:" + orderId + ":summary";
        String cached = redisTemplate.opsForValue().getIfNotExpired(cacheKey, nowMillis);
        if (cached != null) {
            System.out.println("  cache HIT for " + cacheKey);
            return cached;
        }
        System.out.println("  cache MISS for " + cacheKey + " -- recomputing");
        String fresh = computeExpensiveOrderSummary(orderId);
        redisTemplate.opsForValue().setWithExpiry(cacheKey, fresh, 5000, nowMillis); // TTL: 5000 ms
        return fresh;
    }

    public static void main(String[] args) {
        StringRedisTemplate redisTemplate = new StringRedisTemplate();
        long t0 = 0;

        System.out.println("t=0ms:    " + getCachedSummary(redisTemplate, "1", t0));       // MISS -- computes v1
        System.out.println("t=1000ms: " + getCachedSummary(redisTemplate, "1", t0 + 1000)); // HIT  -- still cached
        System.out.println("t=6000ms: " + getCachedSummary(redisTemplate, "1", t0 + 6000)); // MISS -- TTL expired, recomputes v2
    }
}

class RedisServer {
    Map<String, String> data = new HashMap<>();
    Map<String, Long> expiresAtMillis = new HashMap<>(); // Redis tracks a per-key expiry internally, same idea here
}

class ValueOperations {
    private final RedisServer server;
    ValueOperations(RedisServer server) { this.server = server; }

    // Mirrors SET key value EX ttlSeconds -- write plus a TTL in ONE atomic call.
    void setWithExpiry(String key, String value, long ttlMillis, long nowMillis) {
        server.data.put(key, value);
        server.expiresAtMillis.put(key, nowMillis + ttlMillis);
    }

    // Mirrors Redis evaluating a key's TTL automatically before returning it on GET.
    String getIfNotExpired(String key, long nowMillis) {
        Long expiresAt = server.expiresAtMillis.get(key);
        if (expiresAt != null && nowMillis >= expiresAt) {
            server.data.remove(key); server.expiresAtMillis.remove(key); // Redis evicts expired keys lazily, like this
            return null;
        }
        return server.data.get(key);
    }
}

class StringRedisTemplate {
    private final RedisServer server = new RedisServer();
    private final ValueOperations valueOps = new ValueOperations(server);
    ValueOperations opsForValue() { return valueOps; }
}
```

How to run: `java RedisTemplateLevel3.java`

`getCachedSummary` checks the cache first; on a miss, it computes the value and stores it with a `5000`ms TTL via `setWithExpiry`, mirroring `redisTemplate.opsForValue().set(key, value, Duration.ofMillis(5000))`. At `t=1000ms`, the cached entry hasn't expired yet, so it's returned without recomputation. At `t=6000ms`, `6000 >= expiresAt (5000)`, so `getIfNotExpired` evicts the stale entry and returns `null`, forcing a fresh computation.

## 6. Walkthrough

Execution starts in `main` for Level 3. At `t=0`, `getCachedSummary(redisTemplate, "1", 0)` is called. `getIfNotExpired` checks `expiresAtMillis` for `"order:1:summary"` — nothing is stored yet, so `expiresAt` is `null` and the method returns `server.data.get(key)`, which is also `null`. This counts as a cache miss: `computeExpensiveOrderSummary("1")` runs, incrementing `callCount` to `1` and returning `"summary-for-1-v1"`. `setWithExpiry` stores that value along with `expiresAtMillis = 0 + 5000 = 5000`.

At `t=1000`, `getIfNotExpired` finds `expiresAt = 5000`. Since `1000 >= 5000` is `false`, the entry is still valid, and the cached value `"summary-for-1-v1"` is returned directly — `computeExpensiveOrderSummary` is not called again, and `callCount` stays at `1`.

At `t=6000`, `getIfNotExpired` finds the same `expiresAt = 5000`. Since `6000 >= 5000` is `true`, the entry is treated as expired: it's removed from both `data` and `expiresAtMillis`, and `null` is returned. This is a cache miss again, so `computeExpensiveOrderSummary("1")` runs a second time, incrementing `callCount` to `2` and producing `"summary-for-1-v2"`, which is stored fresh with a new expiry of `6000 + 5000 = 11000`.

```
t=0ms:      cache MISS for order:1:summary -- recomputing
t=0ms:    summary-for-1-v1
t=1000ms:   cache HIT for order:1:summary
t=1000ms: summary-for-1-v1
t=6000ms:   cache MISS for order:1:summary -- recomputing
t=6000ms: summary-for-1-v2
```

In real Spring Data Redis, `redisTemplate.opsForValue().set(key, value, Duration.ofSeconds(5))` sends Redis's `SET key value EX 5` command in one round trip, and `redisTemplate.opsForValue().get(key)` transparently returns `null` once Redis's own internal TTL clock has expired the key — the application never has to check timestamps itself; Redis handles expiry natively. This example models that same client-visible behavior in Java for illustration.

## 7. Gotchas & takeaways

> Gotcha: `RedisTemplate<Object, Object>` without explicit serializer configuration uses Java's default (JDK) serialization for both keys and values by default, which produces unreadable binary keys in Redis (bad for debugging with `redis-cli`) and is generally not what you want — reach for `StringRedisTemplate`, or configure serializers explicitly (the next card), for anything you'll want to inspect or interoperate with.

> Gotcha: `increment`/`incrementBy` require the stored value to actually parse as a number — calling it on a key holding a non-numeric string throws an error from Redis, just like `INCR` does on a non-integer value.

- `RedisTemplate<K, V>` is the general-purpose, blocking API for Redis operations; `StringRedisTemplate` is the same thing pre-configured for `String` keys and values, which covers most real applications.
- `opsForValue()` exposes simple get/set/increment operations; later cards in this section cover the operations for lists, sets, hashes, and sorted sets.
- Atomic operations like `increment` run entirely on the Redis server, avoiding read-modify-write races that a manual get-then-set in application code would have.
- Setting a value with an expiration (`Duration`) is the standard caching pattern — Redis evicts the key automatically once the TTL elapses, with no polling or manual cleanup needed from the application.
