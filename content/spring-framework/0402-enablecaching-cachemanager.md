---
card: spring-framework
gi: 402
slug: enablecaching-cachemanager
title: "@EnableCaching & CacheManager"
---

## 1. What it is

`@EnableCaching` is the switch that activates Spring's caching AOP infrastructure — without it, `@Cacheable`/`@CacheEvict`/`@CachePut` annotations are simply ignored. `CacheManager` is the interface that provides and manages named `Cache` instances (like the `"products"` cache used in the caching abstraction card); it's the pluggable seam between the declarative annotations and whatever actually stores the cached data underneath.

```java
@Configuration
@EnableCaching
class CacheConfig {
    @Bean
    CacheManager cacheManager() {
        return new ConcurrentMapCacheManager("products", "categories");
    }
}
```

## 2. Why & when

`@Cacheable` and friends describe *what* to cache and *how to key it*, but they say nothing about *where* cached data actually lives — a plain `HashMap`, an off-heap Caffeine cache, a distributed Redis instance. `CacheManager` is that separation point: the same `@Cacheable("products")` annotation works unchanged whether the underlying `CacheManager` bean is backed by an in-memory map for a quick prototype or a Redis cluster shared across a fleet of instances in production.

You need `@EnableCaching` any time you use the caching annotations at all — it's a one-line prerequisite easy to forget and then wonder why caching "isn't working." You choose a specific `CacheManager` implementation based on your deployment:

- **`ConcurrentMapCacheManager`** — a plain in-memory `ConcurrentHashMap` per cache name. Zero dependencies, no eviction policy, no expiration. Fine for quick demos and tests, unsuitable for production (unbounded growth, no TTL).
- **`CaffeineCacheManager`** — backed by the Caffeine library, in-process, with real eviction policies (size-based, time-based). The standard choice for a single-instance local cache in production.
- **`RedisCacheManager`** — backed by a Redis server, shared across multiple application instances. Needed whenever cached data must be consistent across a horizontally-scaled deployment, not just cached per-instance.
- **`JCacheCacheManager`** — adapts any JSR-107 (JCache)-compliant provider (Ehcache, Hazelcast, Infinispan) into Spring's abstraction.

## 3. Core concept

```
 @EnableCaching
        |
        | activates AOP proxying for @Cacheable/@CacheEvict/@CachePut
        v
 CacheInterceptor  (the AOP advice that actually intercepts calls)
        |
        | looks up the named cache via
        v
 CacheManager.getCache("products")
        |
        | returns a
        v
 Cache  (get/put/evict on this specific named cache)
        |
        +-- ConcurrentMapCacheManager -> in-memory HashMap-backed Cache
        +-- CaffeineCacheManager      -> Caffeine-backed Cache (size/TTL limits)
        +-- RedisCacheManager         -> Redis-backed Cache (shared, distributed)
```

`@EnableCaching` wires the plumbing; the `CacheManager` bean you register decides the actual storage technology behind every `Cache` it hands out by name.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="EnableCaching activates interception, CacheManager supplies the storage-backed Cache instance">
  <rect x="10" y="70" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@EnableCaching</text>

  <rect x="230" y="70" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="99" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">CacheManager bean</text>

  <rect x="470" y="30" width="150" height="36" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="545" y="53" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ConcurrentMap</text>

  <rect x="470" y="80" width="150" height="36" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="545" y="103" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Caffeine</text>

  <rect x="470" y="130" width="150" height="36" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="545" y="153" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Redis</text>

  <line x1="170" y1="95" x2="225" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="410" y1="85" x2="465" y2="55" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="410" y1="95" x2="465" y2="98" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="410" y1="105" x2="465" y2="145" stroke="#8b949e" stroke-width="1.5"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Swapping the `CacheManager` bean changes storage technology without touching any `@Cacheable`-annotated code.

## 5. Runnable example

### Level 1 — Basic

Forget `@EnableCaching` on purpose, observe caching silently doing nothing, then add it and observe the difference — the clearest way to see what the annotation actually does.

```java
import org.springframework.cache.annotation.Cacheable;
import org.springframework.context.annotation.*;

public class EnableCachingBasic {

    static class Service {
        @Cacheable("greetings")
        String greet(String name) {
            System.out.println("Computing greeting for " + name);
            return "Hello, " + name;
        }
    }

    @Configuration
    // NOTE: @EnableCaching intentionally omitted here
    static class ConfigWithoutCaching {
        @Bean
        Service service() { return new Service(); }
    }

    public static void main(String[] args) {
        var context = new AnnotationConfigApplicationContext(ConfigWithoutCaching.class);
        Service service = context.getBean(Service.class);

        System.out.println(service.greet("Ada"));
        System.out.println(service.greet("Ada")); // still recomputes: @Cacheable does nothing here

        context.close();
    }
}
```

How to run: add `spring-context` to the classpath, then `java EnableCachingBasic.java`. Notice `"Computing greeting for Ada"` prints twice.

Without `@EnableCaching`, Spring never creates the AOP proxy that intercepts `@Cacheable` calls — the annotation is present in the bytecode but nothing reads it, so `greet` behaves exactly like an unannotated method, recomputing every time.

### Level 2 — Intermediate

Add `@EnableCaching` and an explicit `ConcurrentMapCacheManager`, and see the same method start actually caching.

```java
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.concurrent.ConcurrentMapCacheManager;
import org.springframework.context.annotation.*;

public class EnableCachingIntermediate {

    static class Service {
        @Cacheable("greetings")
        String greet(String name) {
            System.out.println("Computing greeting for " + name);
            return "Hello, " + name;
        }
    }

    @Configuration
    @EnableCaching
    static class Config {
        @Bean
        CacheManager cacheManager() {
            return new ConcurrentMapCacheManager("greetings");
        }

        @Bean
        Service service() { return new Service(); }
    }

    public static void main(String[] args) {
        var context = new AnnotationConfigApplicationContext(Config.class);
        Service service = context.getBean(Service.class);

        System.out.println(service.greet("Ada"));
        System.out.println(service.greet("Ada")); // now a real cache hit — no recompute

        CacheManager cacheManager = context.getBean(CacheManager.class);
        System.out.println("Cache names: " + cacheManager.getCacheNames());

        context.close();
    }
}
```

How to run: `java EnableCachingIntermediate.java` (same classpath as Level 1). Notice `"Computing greeting for Ada"` now prints only once.

`@EnableCaching` activates the `CacheInterceptor` advice; the explicit `ConcurrentMapCacheManager("greetings")` bean pre-declares the `"greetings"` cache name it will manage. Reading `cacheManager.getCacheNames()` shows the manager is genuinely tracking that named cache, confirming the wiring end to end.

### Level 3 — Advanced

Register multiple `CacheManager`-like configurations for different use cases side by side — a fast local Caffeine cache for hot, single-instance data, and a composite fallback — using `@Primary` to disambiguate which one `@Cacheable` uses by default, and explicit `cacheManager` attributes to opt specific methods into the other.

```java
import com.github.benmanes.caffeine.cache.Caffeine;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.caffeine.CaffeineCacheManager;
import org.springframework.cache.concurrent.ConcurrentMapCacheManager;
import org.springframework.context.annotation.*;

import java.time.Duration;

public class EnableCachingAdvanced {

    static class Service {
        // Uses the @Primary CacheManager (fast, size-bounded Caffeine) implicitly.
        @Cacheable("hot-data")
        String loadHot(String key) {
            System.out.println("Loading hot data for " + key);
            return "hot:" + key;
        }

        // Explicitly opts into the simple unbounded manager for rarely-changing static data.
        @Cacheable(cacheNames = "static-data", cacheManager = "staticCacheManager")
        String loadStatic(String key) {
            System.out.println("Loading static data for " + key);
            return "static:" + key;
        }
    }

    @Configuration
    @EnableCaching
    static class Config {
        @Bean
        @Primary
        CacheManager hotCacheManager() {
            var manager = new CaffeineCacheManager("hot-data");
            manager.setCaffeine(Caffeine.newBuilder()
                    .expireAfterWrite(Duration.ofSeconds(30))
                    .maximumSize(1000));
            return manager;
        }

        @Bean
        @Qualifier("staticCacheManager")
        CacheManager staticCacheManager() {
            return new ConcurrentMapCacheManager("static-data"); // no eviction: truly static data only
        }

        @Bean
        Service service() { return new Service(); }
    }

    public static void main(String[] args) {
        var context = new AnnotationConfigApplicationContext(Config.class);
        Service service = context.getBean(Service.class);

        service.loadHot("A");
        service.loadHot("A"); // hit on the @Primary Caffeine manager

        service.loadStatic("B");
        service.loadStatic("B"); // hit on the explicitly-named staticCacheManager

        context.close();
    }
}
```

How to run: add `com.github.ben-manes.caffeine:caffeine` and `spring-context-support` to the classpath, then `java EnableCachingAdvanced.java`.

`@Cacheable("hot-data")` with no `cacheManager` attribute resolves to whichever `CacheManager` bean is `@Primary` — here, the bounded, expiring Caffeine one, appropriate for volatile "hot" data. `@Cacheable(cacheNames = "static-data", cacheManager = "staticCacheManager")` explicitly overrides that default to use the unbounded `ConcurrentMapCacheManager` instead, appropriate only because `static-data` genuinely never needs eviction. Having two `CacheManager` beans requires resolving the ambiguity — `@Primary` for the implicit default, and the `cacheManager` attribute for explicit opt-outs.

## 6. Walkthrough

Trace `EnableCachingAdvanced.main`:

1. **Context startup.** Two `CacheManager` beans are created: `hotCacheManager` (Caffeine, 30-second TTL, marked `@Primary`) and `staticCacheManager` (plain `ConcurrentMapCacheManager`, qualified `"staticCacheManager"`). `@EnableCaching` wires the `CacheInterceptor` to consult whichever manager each `@Cacheable` call resolves to.
2. **First hot call.** `service.loadHot("A")` is proxied; the interceptor resolves the cache manager for this call. Since no `cacheManager` attribute is set on `@Cacheable("hot-data")`, Spring uses the `@Primary` bean — `hotCacheManager`. It asks that manager for its `"hot-data"` `Cache`, misses (empty), runs `loadHot`'s body (prints `"Loading hot data for A"`), and stores `"hot:A"` under key `"A"` with a 30-second expiry.
3. **Second hot call.** Same key, same primary manager, cache hit within the 30-second window — `loadHot`'s body does not run again.
4. **First static call.** `service.loadStatic("B")` has an explicit `cacheManager = "staticCacheManager"` attribute, so the interceptor bypasses the `@Primary` resolution entirely and looks up the bean named `"staticCacheManager"` directly. It asks that manager for its `"static-data"` `Cache`, misses, runs the method (prints `"Loading static data for B"`), and stores `"static:B"` — with no expiration, since `ConcurrentMapCacheManager` has none.
5. **Second static call.** Same key resolves against `staticCacheManager` again, hits, and the method body is skipped.

```
loadHot("A")    -> @Primary (hotCacheManager)   -> miss -> load -> cache (30s TTL)
loadHot("A")    -> @Primary (hotCacheManager)   -> hit
loadStatic("B") -> explicit staticCacheManager  -> miss -> load -> cache (no TTL)
loadStatic("B") -> explicit staticCacheManager  -> hit
```

Each method's cache resolution is independent — `loadHot` never touches `staticCacheManager` and vice versa, because the `cacheManager` attribute (or its absence, falling back to `@Primary`) is evaluated per annotated method.

## 7. Gotchas & takeaways

> Gotcha: forgetting `@EnableCaching` is the single most common cause of "my `@Cacheable` isn't working" — the annotation is silently a no-op without it, with no warning or error at startup, which is exactly what Level 1 demonstrates. Always verify `@EnableCaching` is present on some `@Configuration` class when caching behavior seems absent.

- `@EnableCaching` turns the annotations on; `CacheManager` decides where cached data actually lives — they're independent concerns you configure together.
- Never rely on the default `ConcurrentMapCacheManager` in production — it never expires or bounds its size, which is an unbounded-memory-growth risk for any cache with an unbounded key space.
- When registering more than one `CacheManager` bean, mark one `@Primary` for the implicit default and use `@Cacheable`'s `cacheManager` attribute to route specific methods to a different one.
- Choose the `CacheManager` implementation based on deployment shape: in-process (Caffeine) for single-instance hot data, distributed (Redis) when multiple instances must share a consistent cache.
