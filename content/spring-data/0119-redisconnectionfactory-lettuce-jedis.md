---
card: spring-data
gi: 119
slug: redisconnectionfactory-lettuce-jedis
title: "RedisConnectionFactory (Lettuce / Jedis)"
---

## 1. What it is

`RedisConnectionFactory` is Spring Data Redis's abstraction for opening connections to a Redis server, with two interchangeable driver implementations behind it: `LettuceConnectionFactory` (async, netty-based, thread-safe to share) and `JedisConnectionFactory` (synchronous, traditionally pooled). Every higher-level Redis API this section covers — `RedisTemplate`, repositories, pub/sub — is built on top of whichever connection factory is configured.

```java
@Bean
RedisConnectionFactory redisConnectionFactory() {
    return new LettuceConnectionFactory(new RedisStandaloneConfiguration("localhost", 6379));
}
```

## 2. Why & when

This card opens a new section — Spring Data Redis — covering Redis, an in-memory key-value data structure store, as opposed to the document (MongoDB) or relational (JPA/JDBC/R2DBC) storage covered so far. Just as `MongoTemplate` needed a `MongoClient` and JDBC needed a `DataSource`, every Redis operation needs a connection, and `RedisConnectionFactory` is that entry point — swapping the underlying client library (Lettuce vs. Jedis) without touching any application code that depends on the factory.

Reach for configuring `RedisConnectionFactory` directly when:

- Setting up a Spring Boot application's Redis connectivity for the first time — this bean is the foundation everything else in this section is built on.
- Choosing between Lettuce (the Spring Boot default: single shared connection, async-capable, works naturally with reactive code) and Jedis (simpler, blocking, traditionally used with a connection pool) based on your application's concurrency model.
- Configuring connection details that don't have a simpler property-based path — custom SSL, Redis Sentinel, or Redis Cluster topology (the last covered in a later card in this section).

## 3. Core concept

```
              RedisConnectionFactory (interface)
                    /              \
     LettuceConnectionFactory      JedisConnectionFactory
     -- one shared netty connection   -- pooled, blocking connections
     -- naturally async/reactive      -- simple, synchronous
     -- Spring Boot's default          -- opt-in alternative

  RedisTemplate / StringRedisTemplate / repositories
        all depend on RedisConnectionFactory,
        NOT on Lettuce or Jedis directly
```

Application code talks to `RedisConnectionFactory` (or higher-level APIs built on it), never to Lettuce or Jedis classes directly — swapping the driver is a one-bean change.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RedisTemplate depends on RedisConnectionFactory, which can be backed by either Lettuce or Jedis">
  <rect x="230" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RedisTemplate</text>

  <rect x="230" y="90" width="180" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="117" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RedisConnectionFactory</text>

  <line x1="320" y1="65" x2="320" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a1)"/>

  <rect x="60" y="140" width="200" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="160" y="160" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">LettuceConnectionFactory</text>

  <rect x="380" y="140" width="200" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="480" y="160" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">JedisConnectionFactory</text>

  <line x1="280" y1="135" x2="200" y2="140" stroke="#8b949e" stroke-width="1.3"/>
  <line x1="360" y1="135" x2="450" y2="140" stroke="#8b949e" stroke-width="1.3"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`RedisTemplate` depends only on the `RedisConnectionFactory` interface — either driver satisfies it identically from the caller's perspective.

## 5. Runnable example

The scenario: opening and using a Redis connection to set and get a value, evolving from a basic single-connection model standing in for Lettuce's shared-connection style, to a pooled model standing in for Jedis, to a factory abstraction that lets application code depend on neither driver directly.

### Level 1 — Basic

Model Lettuce's style: one shared, reusable connection object.

```java
import java.util.*;

public class RedisConnectionLevel1 {
    public static void main(String[] args) {
        LettuceStyleConnectionFactory factory = new LettuceStyleConnectionFactory("localhost", 6379);
        RedisConnection connection = factory.getConnection(); // the SAME connection is reused across calls

        connection.set("order:1:status", "PENDING");
        String value = connection.get("order:1:status");
        System.out.println("Read back: " + value);

        RedisConnection sameConnectionAgain = factory.getConnection();
        System.out.println("Same connection instance reused: " + (connection == sameConnectionAgain));
    }
}

// Stands in for a real Redis server -- an in-memory key/value store.
class RedisServer { Map<String, String> data = new HashMap<>(); }

class RedisConnection {
    private final RedisServer server;
    RedisConnection(RedisServer server) { this.server = server; }
    void set(String key, String value) { server.data.put(key, value); }
    String get(String key) { return server.data.get(key); }
}

// Stands in for org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory --
// Lettuce keeps ONE shared, thread-safe connection rather than pooling many.
class LettuceStyleConnectionFactory {
    private final RedisServer server = new RedisServer();
    private final RedisConnection sharedConnection = new RedisConnection(server);
    LettuceStyleConnectionFactory(String host, int port) { /* real Lettuce would connect here */ }
    RedisConnection getConnection() { return sharedConnection; } // ALWAYS the same instance
}
```

How to run: `java RedisConnectionLevel1.java`

`getConnection()` always returns the same `sharedConnection` instance, standing in for Lettuce's real behavior — a single, thread-safe, multiplexed connection shared across the whole application rather than a new connection per call. `set`/`get` operate through that one connection against the simulated Redis server.

### Level 2 — Intermediate

Model Jedis's style: a pool of connections, one checked out and returned per operation, matching how `JedisConnectionFactory` is traditionally configured with `JedisPoolConfig`.

```java
import java.util.*;

public class RedisConnectionLevel2 {
    public static void main(String[] args) {
        JedisStyleConnectionFactory factory = new JedisStyleConnectionFactory("localhost", 6379, 3); // pool size 3

        try (PooledRedisConnection c1 = factory.getConnection()) {
            c1.set("order:1:status", "PENDING");
        } // connection automatically returned to the pool here

        try (PooledRedisConnection c2 = factory.getConnection()) {
            System.out.println("Read back: " + c2.get("order:1:status"));
        }

        System.out.println("Available connections in pool after use: " + factory.availableCount());
    }
}

class RedisServer { Map<String, String> data = new HashMap<>(); }

// AutoCloseable so try-with-resources returns the connection to the pool -- matches Jedis's borrow/return pattern.
class PooledRedisConnection implements AutoCloseable {
    private final RedisServer server; private final JedisStyleConnectionFactory owner;
    PooledRedisConnection(RedisServer server, JedisStyleConnectionFactory owner) { this.server = server; this.owner = owner; }
    void set(String key, String value) { server.data.put(key, value); }
    String get(String key) { return server.data.get(key); }
    public void close() { owner.returnConnection(this); } // borrowed connection goes BACK to the pool, not closed
}

// Stands in for org.springframework.data.redis.connection.jedis.JedisConnectionFactory + JedisPoolConfig.
class JedisStyleConnectionFactory {
    private final RedisServer server = new RedisServer();
    private final Deque<PooledRedisConnection> pool = new ArrayDeque<>();

    JedisStyleConnectionFactory(String host, int port, int poolSize) {
        for (int i = 0; i < poolSize; i++) pool.push(new PooledRedisConnection(server, this));
    }
    PooledRedisConnection getConnection() { return pool.pop(); }   // BORROW from the pool
    void returnConnection(PooledRedisConnection c) { pool.push(c); } // RETURN to the pool
    int availableCount() { return pool.size(); }
}
```

How to run: `java RedisConnectionLevel2.java`

Unlike Level 1's single shared connection, each `getConnection()` call here borrows one connection object out of a fixed-size pool; `try`-with-resources returns it via `close()` when the block ends. This mirrors Jedis's traditional pooled model — a caller must give the connection back before another caller can use it, which is why Jedis is typically paired with a connection pool sized to expected concurrency.

### Level 3 — Advanced

Write application code against the `RedisConnectionFactory` **abstraction only**, and swap the underlying driver (Lettuce-style vs. Jedis-style) without changing that code at all — the actual point of the factory interface.

```java
import java.util.*;

public class RedisConnectionLevel3 {
    public static void main(String[] args) {
        RedisServer lettuceBackedServer = new RedisServer();
        OrderStatusService withLettuce = new OrderStatusService(new LettuceStyleConnectionFactory(lettuceBackedServer));
        withLettuce.markShipped("1");
        System.out.println("Via Lettuce-backed factory: " + withLettuce.getStatus("1"));

        RedisServer jedisBackedServer = new RedisServer();
        OrderStatusService withJedis = new OrderStatusService(new JedisStyleConnectionFactory(jedisBackedServer));
        withJedis.markShipped("1");
        System.out.println("Via Jedis-backed factory:    " + withJedis.getStatus("1"));
    }
}

// The abstraction application code (and RedisTemplate, in real Spring Data Redis) depends on.
interface RedisConnectionFactory { AutoCloseableRedisConnection getConnection(); }

interface AutoCloseableRedisConnection extends AutoCloseable {
    void set(String key, String value);
    String get(String key);
    void close(); // no checked exception, for simplicity here
}

class RedisServer { Map<String, String> data = new HashMap<>(); }

class LettuceStyleConnectionFactory implements RedisConnectionFactory {
    private final RedisServer server;
    private final AutoCloseableRedisConnection shared;
    LettuceStyleConnectionFactory(RedisServer server) {
        this.server = server;
        this.shared = new AutoCloseableRedisConnection() {
            public void set(String k, String v) { LettuceStyleConnectionFactory.this.server.data.put(k, v); }
            public String get(String k) { return LettuceStyleConnectionFactory.this.server.data.get(k); }
            public void close() { /* Lettuce's shared connection is never actually closed per-call */ }
        };
    }
    public AutoCloseableRedisConnection getConnection() { return shared; }
}

class JedisStyleConnectionFactory implements RedisConnectionFactory {
    private final RedisServer server;
    JedisStyleConnectionFactory(RedisServer server) { this.server = server; }
    public AutoCloseableRedisConnection getConnection() {
        return new AutoCloseableRedisConnection() { // a FRESH connection object each call, standing in for a pool borrow
            public void set(String k, String v) { server.data.put(k, v); }
            public String get(String k) { return server.data.get(k); }
            public void close() { /* would return to the Jedis pool here */ }
        };
    }
}

// Depends ONLY on the RedisConnectionFactory interface -- exactly like RedisTemplate does in real Spring Data Redis.
class OrderStatusService {
    private final RedisConnectionFactory connectionFactory;
    OrderStatusService(RedisConnectionFactory connectionFactory) { this.connectionFactory = connectionFactory; }
    void markShipped(String orderId) {
        try (AutoCloseableRedisConnection c = connectionFactory.getConnection()) { c.set("order:" + orderId + ":status", "SHIPPED"); }
    }
    String getStatus(String orderId) {
        try (AutoCloseableRedisConnection c = connectionFactory.getConnection()) { return c.get("order:" + orderId + ":status"); }
    }
}
```

How to run: `java RedisConnectionLevel3.java`

`OrderStatusService` is written entirely against the `RedisConnectionFactory` interface — it has no idea whether it's talking to a Lettuce-style or Jedis-style implementation. Swapping `new LettuceStyleConnectionFactory(...)` for `new JedisStyleConnectionFactory(...)` in the constructor is the only change needed to change drivers; `markShipped`/`getStatus` behave identically either way.

## 6. Walkthrough

Execution starts in `main` for Level 3. Two independent `RedisServer` instances are created (standing in for two separate Redis deployments, or the same one — the point is they're independent here), and two `OrderStatusService` instances are built: one wired to a `LettuceStyleConnectionFactory`, one to a `JedisStyleConnectionFactory`.

`withLettuce.markShipped("1")` calls `connectionFactory.getConnection()`, which for the Lettuce-style factory always returns the same `shared` connection object. `c.set("order:1:status", "SHIPPED")` writes into `lettuceBackedServer.data`. The `try`-with-resources block then calls `close()` on the shared connection, which does nothing (a real Lettuce connection stays open and shared, not closed per operation). `withLettuce.getStatus("1")` repeats the same pattern for a read, returning `"SHIPPED"`.

`withJedis.markShipped("1")` calls `getConnection()` on the Jedis-style factory, which constructs a **new** anonymous connection object bound to `jedisBackedServer` for this call only — standing in for borrowing a connection from a pool. The write happens through that connection, and `close()` would, in a real `JedisConnectionFactory`, return the connection to its pool. `getStatus("1")` borrows another (logically separate) connection object and reads the value back.

```
Via Lettuce-backed factory: SHIPPED
Via Jedis-backed factory:    SHIPPED
```

Both services print the same result despite using completely different connection-management strategies underneath — which is exactly the point of the `RedisConnectionFactory` abstraction: `OrderStatusService` (standing in for `RedisTemplate` and everything built on it in later cards) never needs to know or care which driver, or which connection lifecycle strategy, is actually in use.

## 7. Gotchas & takeaways

> Gotcha: Lettuce's single shared connection is thread-safe by design and is the right default for most applications, including reactive ones — trying to "pool" Lettuce connections the way you would with Jedis is usually unnecessary and adds complexity without benefit.

> Gotcha: Jedis connections are **not** thread-safe individually — each thread (or each borrowed-and-returned unit of work) needs its own connection from the pool; sharing a single Jedis connection across concurrent threads causes protocol-level corruption, not just contention.

- `RedisConnectionFactory` is the abstraction every Redis-facing Spring Data API (`RedisTemplate`, repositories, pub/sub) is built on — application code should depend on it, not on Lettuce or Jedis classes directly.
- Lettuce (Spring Boot's default) uses one shared, async-capable, thread-safe connection; Jedis traditionally uses a pool of individually-borrowed, blocking connections.
- Choosing between them is a driver/concurrency-model decision, made once at configuration time, that the rest of the application is insulated from.
- Configure `RedisConnectionFactory` directly (rather than only relying on Spring Boot autoconfiguration properties) when you need SSL, Sentinel, or Cluster topology beyond what simple properties express.
