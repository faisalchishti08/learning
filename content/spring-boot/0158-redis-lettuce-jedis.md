---
card: spring-boot
gi: 158
slug: redis-lettuce-jedis
title: Redis (Lettuce/Jedis)
---

## 1. What it is

**Redis** is an in-memory data structure store used for caching, session storage, pub/sub messaging, rate limiting, and distributed locks. Spring Boot auto-configures Redis via `spring-boot-starter-data-redis`, providing both a high-level `RedisTemplate<K,V>` / `StringRedisTemplate` and Spring Data Redis repositories. The underlying client is **Lettuce** by default (non-blocking, Netty-based); **Jedis** is the alternative (blocking, thread-safe). Connection is configured with `spring.data.redis.*` properties.

## 2. Why & when

Redis is the Swiss-army knife of backend infrastructure. Use it for:

- **Caching** — `@Cacheable` with Spring Cache + Redis stores results in milliseconds.
- **Session storage** — Spring Session stores `HttpSession` in Redis for distributed session sharing.
- **Pub/Sub** — `RedisMessageListenerContainer` subscribes to Redis channels.
- **Rate limiting** — atomic `INCR` + `EXPIRE` commands implement counters.
- **Distributed locks** — `SETNX` (SET if Not eXists) creates advisory locks.

Choose **Lettuce** (default) for non-blocking, reactive, and WebFlux applications. Choose **Jedis** when you need simple synchronous access or are migrating from legacy code.

## 3. Core concept

`RedisAutoConfiguration` creates:

- `LettuceConnectionFactory` (or `JedisConnectionFactory`) from `spring.data.redis.*`.
- `RedisTemplate<Object, Object>` — general-purpose; serialises keys and values with JDK serialisation by default.
- `StringRedisTemplate` — specialised for `String` keys and values; uses `StringRedisSerializer`.

`RedisTemplate` operations mirror Redis commands:

| Redis command | `RedisTemplate` method |
|---|---|
| `SET k v` | `ops.opsForValue().set(k, v)` |
| `GET k` | `ops.opsForValue().get(k)` |
| `HSET k f v` | `ops.opsForHash().put(k, f, v)` |
| `LPUSH k v` | `ops.opsForList().leftPush(k, v)` |
| `SADD k v` | `ops.opsForSet().add(k, v)` |

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="110" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Your Service</text>
  <rect x="235" y="55" width="175" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="322" y="79" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">StringRedisTemplate</text>
  <rect x="235" y="115" width="175" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="322" y="139" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">LettuceConnectionFactory</text>
  <rect x="490" y="80" width="165" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="572" y="110" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Redis server</text>
  <line x1="162" y1="105" x2="231" y2="78" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rd)"/>
  <line x1="322" y1="97" x2="322" y2="113" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#rd2)"/>
  <line x1="412" y1="135" x2="486" y2="115" stroke="#8b949e" stroke-width="1.5" marker-end="url(#rd3)"/>
  <defs>
    <marker id="rd" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="rd2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="rd3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`StringRedisTemplate` routes operations through `LettuceConnectionFactory` to the Redis server over a persistent Netty connection.

## 5. Runnable example

```java
// RedisApp.java — Spring Boot project with spring-boot-starter-data-redis
// application.properties:
//   spring.data.redis.host=localhost
//   spring.data.redis.port=6379
// Start Redis: docker run -p 6379:6379 redis:7-alpine

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;

@SpringBootApplication
public class RedisApp {
    public static void main(String[] args) {
        SpringApplication.run(RedisApp.class, args);
    }
}

@RestController
@RequestMapping("/cache")
class CacheController {

    private final StringRedisTemplate redis;

    CacheController(StringRedisTemplate redis) { this.redis = redis; }

    // Store a value with optional TTL
    @PostMapping
    public String set(@RequestParam String key,
                      @RequestParam String value,
                      @RequestParam(defaultValue = "60") long ttlSeconds) {
        redis.opsForValue().set(key, value, Duration.ofSeconds(ttlSeconds));
        return "Stored: " + key + "=" + value + " (TTL " + ttlSeconds + "s)";
    }

    // Retrieve a value
    @GetMapping
    public String get(@RequestParam String key) {
        String val = redis.opsForValue().get(key);
        return val != null ? val : "key not found (may have expired)";
    }

    // Atomic counter (e.g. for rate limiting)
    @PostMapping("/increment")
    public String increment(@RequestParam String counter) {
        Long count = redis.opsForValue().increment(counter);
        return counter + " = " + count;
    }

    // Delete a key
    @DeleteMapping
    public String delete(@RequestParam String key) {
        Boolean deleted = redis.delete(key);
        return Boolean.TRUE.equals(deleted) ? "Deleted" : "Key not found";
    }
}
```

**How to run:**
1. Start Redis: `docker run -p 6379:6379 redis:7-alpine`
2. Add `spring-boot-starter-data-redis` to `pom.xml`, start the app.
3. `curl -X POST "http://localhost:8080/cache?key=greeting&value=hello&ttlSeconds=120"`
4. `curl "http://localhost:8080/cache?key=greeting"` → `hello`
5. `curl -X POST "http://localhost:8080/cache/increment?counter=visits"` → `visits = 1`

## 6. Walkthrough

- `spring-boot-starter-data-redis` adds `lettuce-core` (Lettuce client) and triggers `RedisAutoConfiguration`. It creates `LettuceConnectionFactory` from `spring.data.redis.host` and `spring.data.redis.port`, and registers `StringRedisTemplate` and `RedisTemplate<Object,Object>`.
- `StringRedisTemplate` serialises both key and value as UTF-8 strings — the simplest and most interoperable Redis usage. `redis.opsForValue()` returns operations for Redis `STRING` type.
- `.set(key, value, Duration.ofSeconds(ttlSeconds))` maps to `SET key value EX ttlSeconds` — an atomic set with expiry. After TTL seconds Redis removes the key automatically.
- `.increment(counter)` maps to `INCR counter` — an atomic 64-bit integer increment. Two threads calling it simultaneously never get the same value; Redis is single-threaded for commands.
- `.delete(key)` maps to `DEL key`; returns `true` if the key existed. The `Boolean.TRUE.equals(deleted)` guard handles the case where the key had already expired.
- To switch to Jedis: exclude Lettuce (`<exclusion>io.lettuce:lettuce-core</exclusion>`) and add `redis.clients:jedis`. Spring Boot detects Jedis and creates `JedisConnectionFactory` instead.

## 7. Gotchas & takeaways

> `RedisTemplate<Object, Object>` uses JDK serialisation by default — stored bytes are not human-readable in `redis-cli`. Use `StringRedisTemplate` for string values, or configure a `Jackson2JsonRedisSerializer` for JSON storage.

> Lettuce connections are multiplexed over a single socket — all threads share one connection by default. Under very high concurrency, switch to `LettucePoolingClientConfiguration` with a connection pool.

- `spring.data.redis.timeout` is the command timeout (not connection timeout) — default is unlimited.
- Lettuce supports Redis Sentinel and Redis Cluster via `spring.data.redis.sentinel.*` and `spring.data.redis.cluster.*`.
- `@Cacheable` with `spring.cache.type=redis` integrates Redis with Spring's caching abstraction — no `RedisTemplate` calls needed for basic caching.
- For reactive Redis access (WebFlux), inject `ReactiveRedisTemplate` — Lettuce supports reactive streams natively; Jedis does not.
- `spring.data.redis.password` sets the AUTH password for password-protected Redis instances.
