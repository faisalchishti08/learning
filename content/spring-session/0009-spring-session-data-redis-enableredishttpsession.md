---
card: spring-session
gi: 9
slug: spring-session-data-redis-enableredishttpsession
title: "Spring Session Data Redis (@EnableRedisHttpSession)"
---

## 1. What it is

`spring-session-data-redis` is the Redis-backed implementation of Spring Session, and `@EnableRedisHttpSession` is the annotation that wires it up — composing `@EnableSpringHttpSession`'s generic servlet plumbing (card 0005) with a `RedisIndexedSessionRepository` bean, Redis-specific serialization, and the key-naming and TTL conventions Redis-backed sessions rely on.

## 2. Why & when

Redis is the most common backing store for Spring Session in production, and for good reason: it's fast (in-memory, sub-millisecond round-trips), it has native key expiration (TTL) that maps naturally onto session expiration (card 0007) without needing a separate cleanup task, and it's already a common piece of infrastructure many teams run for caching regardless of session storage. `@EnableRedisHttpSession` is the single annotation that gets a fully working, production-grade clustered session setup running with minimal configuration.

Reach for `@EnableRedisHttpSession` when:

- Standing up clustered sessions for a new multi-instance deployment and Redis is available (or easy to add) as infrastructure — this is the default, most common choice for a reason.
- Needing session reads and writes to be fast — Redis's in-memory nature keeps the added latency of external session storage (card 0001) to a minimum compared to a relational database round-trip.
- Deciding between Redis and JDBC (card 0012) — prefer Redis when raw performance and native expiration matter most; prefer JDBC when the team wants to avoid adding a new infrastructure dependency and already operates a relational database reliably.

## 3. Core concept

Think of `@EnableRedisHttpSession` as ordering a fully assembled appliance rather than a kit of parts — where the generic `@EnableSpringHttpSession` (card 0005) is a bare electrical outlet standard waiting for someone to plug in a compatible appliance, `@EnableRedisHttpSession` is Redis already plugged in, pre-configured, and running, ready to use the moment the annotation is applied. Under the hood it's doing exactly the same composition any custom setup could do by hand (generic wiring plus a `RedisIndexedSessionRepository` bean) — it's just doing it correctly, with sensible defaults, in one line.

```java
@Configuration
@EnableRedisHttpSession
public class RedisSessionConfig {
    // That's it. A RedisConnectionFactory bean must exist in the context
    // (Spring Boot's Redis starter provides one automatically), and everything else is wired.
}
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="EnableRedisHttpSession composes generic session wiring with a RedisIndexedSessionRepository and Redis connection">
  <rect x="20" y="20" width="220" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="48" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@EnableSpringHttpSession</text>

  <rect x="20" y="90" width="220" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="118" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RedisIndexedSessionRepository</text>

  <rect x="20" y="160" width="220" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="188" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RedisConnectionFactory</text>

  <rect x="330" y="80" width="280" height="90" rx="10" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="470" y="105" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">@EnableRedisHttpSession</text>
  <text x="470" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">composes all three, plus</text>
  <text x="470" y="146" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">key naming + TTL conventions</text>

  <line x1="240" y1="43" x2="325" y2="105" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="240" y1="113" x2="325" y2="120" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="240" y1="183" x2="325" y2="140" stroke="#8b949e" stroke-width="1.5"/>
</svg>

One annotation replaces three separate pieces of manual configuration a hand-rolled setup would otherwise need.

## 5. Runnable example

The scenario: enabling Redis-backed sessions for a simple app, growing to customize the session timeout and key namespace for a multi-application shared Redis instance, and finally to configure Redis connection resilience so a transient Redis blip doesn't crash the whole application.

### Level 1 — Basic

```java
// RedisSessionConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.session.data.redis.config.annotation.web.http.EnableRedisHttpSession;

@Configuration
@EnableRedisHttpSession
public class RedisSessionConfig {
}
```

```properties
# application.properties
spring.data.redis.host=localhost
spring.data.redis.port=6379
```

**How to run:** with `spring-boot-starter-data-redis` and `spring-session-data-redis` on the classpath, a local Redis running, and this configuration class present, start the app and make a request that touches the session. Expected result: `redis-cli KEYS "spring:session:*"` shows session keys immediately — no further configuration needed for a fully working clustered session setup.

### Level 2 — Intermediate

Running multiple applications against the same shared Redis instance requires a distinct key namespace per application to avoid session key collisions, and the timeout should typically be tuned per application rather than left at the 30-minute default.

```java
import org.springframework.context.annotation.Configuration;
import org.springframework.session.data.redis.config.annotation.web.http.EnableRedisHttpSession;

@Configuration
@EnableRedisHttpSession(
        maxInactiveIntervalInSeconds = 900, // 15 minutes, tighter than the 30-minute default
        redisNamespace = "taskapp:sessions" // avoids colliding with other apps sharing this Redis
)
public class RedisSessionConfig {
}
```

**How to run:** run two different applications (or two configuration variants) against the same Redis instance, one with `redisNamespace = "taskapp:sessions"` and another with a different namespace (or the default). Expected behavior: `redis-cli KEYS "taskapp:sessions:*"` shows only this application's sessions, cleanly separated from any other application's session keys in the same Redis instance — and sessions expire after 15 minutes of inactivity instead of 30.

What changed: the shared Redis infrastructure now safely supports multiple independent applications without any risk of one application's session keys colliding with or being mistaken for another's, and the timeout matches this specific application's actual security requirements rather than a generic default.

### Level 3 — Advanced

Production deployments need to handle Redis being temporarily unavailable gracefully — a naive setup either hangs indefinitely or crashes the application on every request when Redis has a momentary blip, so connection timeouts and retry behavior need explicit configuration.

```properties
# application.properties
spring.data.redis.host=redis.internal
spring.data.redis.port=6379
spring.data.redis.timeout=2000ms
spring.data.redis.connect-timeout=1000ms

spring.data.redis.lettuce.pool.max-active=16
spring.data.redis.lettuce.pool.max-wait=1000ms
spring.data.redis.lettuce.pool.min-idle=2
```

```java
import io.lettuce.core.ClientOptions;
import io.lettuce.core.SocketOptions;
import org.springframework.boot.autoconfigure.data.redis.LettuceClientConfigurationBuilderCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;

@Configuration
public class RedisResilienceConfig {

    @Bean
    public LettuceClientConfigurationBuilderCustomizer lettuceCustomizer() {
        return builder -> builder.clientOptions(
                ClientOptions.builder()
                        .socketOptions(SocketOptions.builder()
                                .connectTimeout(Duration.ofMillis(1000))
                                .keepAlive(true)
                                .build())
                        .autoReconnect(true) // automatically re-establish connection after a blip
                        .build());
    }
}
```

**How to run:** simulate a Redis outage (stop the local Redis container briefly) while the application is under light traffic, then restart Redis. Expected behavior: requests during the outage fail fast (within the configured ~1-2 second timeout) with a clear error, rather than hanging indefinitely; once Redis comes back, `autoReconnect(true)` re-establishes the connection automatically and session operations resume working without an application restart.

What changed and why it's production-flavored: this trades "hang forever waiting for a dead connection" for "fail fast and recover automatically" — a Redis blip in production (a failover, a brief network partition) now degrades gracefully for the duration of the outage and self-heals afterward, instead of taking the whole application down with it.

## 6. Walkthrough

Tracing a request through a Redis-backed session setup, in execution order:

1. `@EnableRedisHttpSession` has, at startup, composed and registered `SessionRepositoryFilter` (card 0004) backed by a `RedisIndexedSessionRepository`, itself using a `RedisConnectionFactory` (configured via the Lettuce client, per Level 3's resilience settings) pointing at the configured Redis instance.
2. A request arrives with a `SESSION` cookie; `SessionRepositoryFilter` wraps it, and when `getSession()` is eventually called, `RedisIndexedSessionRepository.findById(...)` issues Redis commands to load the session's hash structure by key (namespaced per Level 2's `redisNamespace`).
3. The controller reads and writes attributes via the standard `HttpSession` API, unaware of Redis specifically (card 0006's transparency).
4. At request completion, `SessionRepositoryFilter` calls `save(...)`, which serializes any changed attributes and writes them to Redis — refreshing the key's TTL to match `maxInactiveIntervalInSeconds` (Level 2's 900-second configuration) in the same operation, so an actively-used session's expiration clock keeps resetting on every touch.
5. If Redis is briefly unreachable during any of this (Level 3's scenario), the configured connection timeout ensures the request fails within roughly a second or two rather than hanging, and `autoReconnect` means the very next request, once Redis is back, succeeds without any manual intervention.
6. Should the session sit idle past its TTL, Redis's own internal expiration (card 0007) removes the key automatically — the next request bearing that now-stale cookie finds nothing on `findById` and is treated as a fresh, unauthenticated session.

```
Request -> SessionRepositoryFilter -> RedisIndexedSessionRepository.findById(key)
   |                                          |
   |                              Redis unreachable? --yes--> fail fast (~1-2s timeout)
   |                                          |  no
   |                              return session data (or null if expired/missing)
   |
controller: getAttribute/setAttribute (transparent, card 0006)
   |
save() -> write changed attributes + refresh TTL (900s) -> Redis
```

## 7. Gotchas & takeaways

> `maxInactiveIntervalInSeconds` set via `@EnableRedisHttpSession` and `server.servlet.session.timeout` set via Spring Boot properties both influence session timeout — when both are present and disagree, know which one actually takes effect for the specific Spring Boot version in use, and prefer configuring it in exactly one place to avoid confusing drift between the two.

- Redis-backed sessions require a `RedisConnectionFactory` bean to already exist in the application context — Spring Boot's `spring-boot-starter-data-redis` provides this automatically from `spring.data.redis.*` properties, but a from-scratch (non-Boot) setup needs to define it explicitly.
- Always namespace sessions (`redisNamespace`, Level 2) when a Redis instance is shared across multiple applications or environments — the default namespace is generic enough that two unrelated applications pointed at the same Redis without distinct namespaces risk genuinely colliding session keys.
- Connection resilience (Level 3) isn't optional for production — the default Lettuce client behavior is reasonable but not tuned for any specific application's latency and availability requirements; explicitly setting timeouts is the difference between a Redis blip being a brief, contained degradation versus a full application outage.
- `RedisIndexedSessionRepository` maintains additional index structures beyond the raw session data (to support `findByPrincipalName`, card 0003) — this means Redis-backed sessions use somewhat more storage and involve slightly more write overhead than the absolute minimum needed to store just the raw attributes, a reasonable and usually worthwhile trade for the indexed-lookup capability it enables.
- When debugging "sessions aren't showing up in Redis at all," check first that `@EnableRedisHttpSession` (or `@EnableSpringHttpSession` plus a manually wired Redis repository) is actually being picked up by component scanning, and that the `RedisConnectionFactory` is genuinely pointed at the Redis instance being inspected — a surprising number of these issues are simply inspecting the wrong Redis instance or database index.
