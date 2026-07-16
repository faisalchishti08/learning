---
card: spring-integration
gi: 66
slug: mongodb-redis-cassandra-adapters
title: "MongoDB / Redis / Cassandra adapters"
---

## 1. What it is

The NoSQL store adapters (`MongoDb.inboundAdapter(...)`/`outboundAdapter(...)`, `Redis.inboundAdapter(...)`/`outboundAdapter(...)`/`Redis.storeOutboundAdapter(...)`, `Cassandra.inboundAdapter(...)`/`outboundAdapter(...)`) connect a flow to a document store, a key/value store, or a wide-column store, each following that store's own data model rather than the relational rows-and-columns model the JDBC adapter (card 0064) speaks. Each adapter maps the same message-in/message-out shape onto a fundamentally different underlying storage engine.

## 2. Why & when

You reach for one of these adapters when the integration point is a NoSQL store whose data shape doesn't fit relational tables:

- **MongoDB**, when the data is naturally document-shaped — nested JSON-like structures (an order with embedded line items) that would otherwise need several joined relational tables.
- **Redis**, when the store is being used for fast key/value lookups, caching, or as a lightweight pub/sub or queue (Redis lists/streams) alongside its primary role as a cache — an outbound adapter can write-through a flow's result into a cache, and an inbound adapter can poll a Redis list as a work queue.
- **Cassandra**, when the workload demands high write throughput and horizontal scale across a cluster with tunable consistency, common for time-series or event-log style data where relational joins were never needed in the first place.

## 3. Core concept

Think of a relational database as a filing cabinet with rigid, pre-printed forms (every row in a table has the same fixed columns). MongoDB is like a cabinet of manila folders where each folder can hold a differently structured note. Redis is like a wall of labeled cubbyholes — you know the label (key), you get back whatever's in that cubby (value), instantly, with no searching. Cassandra is like a wall of cubbyholes replicated across many buildings (nodes) at once, built for extremely fast writes and reads even as buildings come and go, at the cost of possibly reading a slightly stale copy from a distant building.

```java
@Bean
public IntegrationFlow redisCacheFlow(RedisTemplate<String, Object> redisTemplate) {
    return IntegrationFlow.from("priceUpdates")
        .handle(Redis.outboundAdapter(redisTemplate)
            .keyExpression("headers['symbol']")
            .valueExpression("payload"))
        .get();
}
```

Every message on `priceUpdates` writes its payload into Redis under a key derived from the message's `symbol` header — an instant cache update, no query needed to read it back later.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="MongoDB stores flexible documents, Redis stores key-value pairs for instant lookup, Cassandra stores wide-column data replicated across a cluster for high write throughput" >
  <rect x="10" y="20" width="195" height="120" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="107" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">MongoDB</text>
  <text x="25" y="45" fill="#e6edf3" font-size="7" font-family="monospace">{ order: 1,</text>
  <text x="25" y="60" fill="#e6edf3" font-size="7" font-family="monospace">  lines: [...] }</text>
  <text x="25" y="90" fill="#8b949e" font-size="7" font-family="sans-serif">flexible, nested</text>
  <text x="25" y="105" fill="#8b949e" font-size="7" font-family="sans-serif">documents</text>

  <rect x="222" y="20" width="195" height="120" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="319" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Redis</text>
  <text x="237" y="45" fill="#e6edf3" font-size="7" font-family="monospace">"ACME" -&gt; 101.25</text>
  <text x="237" y="90" fill="#8b949e" font-size="7" font-family="sans-serif">key -&gt; value,</text>
  <text x="237" y="105" fill="#8b949e" font-size="7" font-family="sans-serif">in-memory, instant</text>

  <rect x="434" y="20" width="195" height="120" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="531" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Cassandra</text>
  <text x="449" y="45" fill="#e6edf3" font-size="7" font-family="monospace">row across N nodes</text>
  <text x="449" y="90" fill="#8b949e" font-size="7" font-family="sans-serif">wide-column, replicated,</text>
  <text x="449" y="105" fill="#8b949e" font-size="7" font-family="sans-serif">high write throughput</text>
</svg>

Each store adapter maps messages onto that store's native shape: documents, key/value pairs, or replicated wide-column rows.

## 5. Runnable example

The scenario: caching the latest price per symbol so lookups are instant, simulated with a `HashMap` standing in for a Redis-backed store (no real Redis server needed to demonstrate the write-through and lookup logic), starting with a basic write, then adding a TTL-like expiry check, then handling a cache-miss fallback to a slower source.

### Level 1 — Basic

```java
// PriceCacheDemo.java
import java.util.*;

public class PriceCacheDemo {
    // Stand-in for RedisTemplate.opsForValue(): a plain key-value store.
    static final Map<String, Double> cache = new HashMap<>();

    static void writeThrough(String symbol, double price) {
        cache.put(symbol, price);
        System.out.println("Cached " + symbol + " = " + price);
    }

    public static void main(String[] args) {
        writeThrough("ACME", 101.25);
        System.out.println("Lookup ACME: " + cache.get("ACME"));
    }
}
```

How to run: `java PriceCacheDemo.java`. Expected output: `Cached ACME = 101.25` then `Lookup ACME: 101.25` — an instant key-based read, no query needed.

### Level 2 — Intermediate

```java
// PriceCacheDemo.java
import java.util.*;

public class PriceCacheDemo {
    record Entry(double price, long expiresAtMillis) {}

    // Real-world concern: cached prices go stale; Redis TTLs (EXPIRE) model this at the store
    // level, so here each entry tracks its own expiry and a lookup checks it before returning.
    static final Map<String, Entry> cache = new HashMap<>();

    static void writeThrough(String symbol, double price, long ttlMillis) {
        cache.put(symbol, new Entry(price, System.currentTimeMillis() + ttlMillis));
        System.out.println("Cached " + symbol + " = " + price + " (ttl " + ttlMillis + "ms)");
    }

    static Optional<Double> lookup(String symbol) {
        Entry e = cache.get(symbol);
        if (e == null || System.currentTimeMillis() > e.expiresAtMillis()) return Optional.empty();
        return Optional.of(e.price());
    }

    public static void main(String[] args) throws InterruptedException {
        writeThrough("ACME", 101.25, 50);
        System.out.println("Immediate lookup: " + lookup("ACME"));
        Thread.sleep(100);
        System.out.println("Lookup after ttl expiry: " + lookup("ACME"));
    }
}
```

How to run: `java PriceCacheDemo.java`. Expected output: `Immediate lookup: Optional[101.25]` then, after the sleep exceeds the 50ms TTL, `Lookup after ttl expiry: Optional.empty` — mirroring how a Redis key set with `EXPIRE` silently disappears once its TTL elapses.

### Level 3 — Advanced

```java
// PriceCacheDemo.java
import java.util.*;
import java.util.function.*;

public class PriceCacheDemo {
    record Entry(double price, long expiresAtMillis) {}

    static final Map<String, Entry> cache = new HashMap<>();

    static void writeThrough(String symbol, double price, long ttlMillis) {
        cache.put(symbol, new Entry(price, System.currentTimeMillis() + ttlMillis));
    }

    static Optional<Double> rawLookup(String symbol) {
        Entry e = cache.get(symbol);
        if (e == null || System.currentTimeMillis() > e.expiresAtMillis()) return Optional.empty();
        return Optional.of(e.price());
    }

    // Production concern: a cache miss must fall back to the slower source of truth and
    // repopulate the cache, rather than the flow failing outright when Redis has no entry.
    static double lookupOrFetch(String symbol, Function<String, Double> slowSourceLookup) {
        return rawLookup(symbol).orElseGet(() -> {
            System.out.println("Cache miss for " + symbol + ", falling back to slow source");
            double fetched = slowSourceLookup.apply(symbol);
            writeThrough(symbol, fetched, 5000);
            return fetched;
        });
    }

    public static void main(String[] args) {
        Function<String, Double> slowSource = symbol -> {
            System.out.println("  (querying upstream pricing service for " + symbol + ")");
            return 99.99;
        };

        double first = lookupOrFetch("XYZ", slowSource);  // miss, populates cache
        double second = lookupOrFetch("XYZ", slowSource); // hit, no upstream call

        System.out.println("First: " + first + ", Second: " + second);
    }
}
```

How to run: `java PriceCacheDemo.java`. Expected output: the first call prints the cache-miss message and the upstream query line, returning `99.99`; the second call hits the now-populated cache silently and returns `99.99` without querying upstream — the write-through-on-miss pattern that keeps a Redis-backed adapter from repeatedly hammering a slow source of truth.

## 6. Walkthrough

Trace a price lookup through a Redis-backed flow, including the miss path.

1. **Request arrives**: a message asking for `ACME`'s current price enters the flow, perhaps from an inbound HTTP gateway.
2. **Cache check**: a `.handle(...)` step calls `Redis.outboundGateway(...)` (or equivalent `RedisTemplate` lookup) with the key derived from the message — analogous to `rawLookup("ACME")` in the example.
3. **Cache hit**: if Redis has the key and it hasn't expired, the value comes back immediately — no query to any other system, sub-millisecond latency, and the flow returns the cached value straight to the response channel.
4. **Cache miss**: if Redis has no entry (never written, or its TTL expired), the flow routes to a fallback branch that queries the actual pricing service, gets the fresh value, and issues a `Redis.outboundAdapter` write to repopulate the cache with a fresh TTL — the `writeThrough` call in the example.
5. **Response**: either path converges on the same value being returned to the original caller — the caller cannot tell from the response whether it came from cache or from the slow path, only the latency differs.
6. **MongoDB/Cassandra variants**: the same shape applies for a document or wide-column read — a `MongoDb.outboundGateway` runs a query against a collection and returns matching documents as messages; a `Cassandra.outboundGateway` runs a CQL statement against a table spread across the cluster and returns matching rows, with consistency level configuration determining how many replicas must agree before the read (or write) is considered successful.

```
request for ACME price
  -> Redis GET "ACME"
       hit  -> return cached value immediately
       miss -> query pricing service (slow path)
                 -> Redis SET "ACME" value EX ttl   (repopulate)
                   -> return fresh value
```

## 7. Gotchas & takeaways

> **Gotcha:** a cache-aside pattern like the one above has a window between the slow-source fetch and the cache write where a concurrent request can also miss and also hit the slow source — under high concurrency, this can cause a "thundering herd" of redundant upstream calls right after a popular key's TTL expires; production systems typically add a short-lived lock or request-coalescing to avoid this.

- Each store has a different consistency model: Redis is effectively single-threaded and immediately consistent for a single key; MongoDB offers configurable read/write concerns; Cassandra's tunable consistency (`ONE`, `QUORUM`, `ALL`) trades latency against how many replicas must agree, and picking the wrong level for the use case is a common source of "stale read" surprises.
- TTL expiry is silent — a key just stops existing, with no notification (unless keyspace notifications are explicitly enabled), so any flow relying on freshness needs its own miss-and-refetch logic, not an assumption that the cache will proactively tell it something expired.
- MongoDB's flexible document shape means the same collection can hold documents with different fields over time (schema evolution without a migration), but that flexibility pushes validation responsibility onto the application, since the store itself won't reject a differently-shaped document.
- Cassandra is optimized for high write throughput and denormalized, query-shaped tables — modeling it like a relational schema with joins works against its design and leads to poor performance.
