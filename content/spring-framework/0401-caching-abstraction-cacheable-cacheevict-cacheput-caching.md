---
card: spring-framework
gi: 401
slug: caching-abstraction-cacheable-cacheevict-cacheput-caching
title: "Caching abstraction (@Cacheable, @CacheEvict, @CachePut, @Caching)"
---

## 1. What it is

Spring's caching abstraction lets you add caching to a method with a single annotation, without changing the method's code or manually checking/populating a cache map. `@Cacheable` caches a method's return value keyed by its arguments and skips the method body entirely on a cache hit; `@CacheEvict` removes entries; `@CachePut` always runs the method but updates the cache with its result; `@Caching` groups several caching annotations on one method.

```java
@Service
class ProductService {
    @Cacheable("products")
    Product findById(long id) {
        return expensiveDatabaseLookup(id);  // only runs on a cache miss
    }
}
```

## 2. Why & when

Recomputing an expensive or slow operation — a complex query, an external API call, a heavy calculation — every single time it's requested wastes time and resources when the result rarely changes between calls. Writing caching logic by hand means manually checking a map, populating it on miss, and invalidating it on writes, scattered across every method that needs it. Spring's caching abstraction centralizes that pattern behind annotations, the same declarative approach `@Transactional` uses for transactions, so the method body stays focused on business logic.

Reach for it when:

- A method is expensive relative to how often its result actually changes (a lookup against a slow external service, an aggregation query, a computed report).
- You want caching behavior to be visible and adjustable at the method level (which cache, what key, how long) without threading a cache client through your business logic.
- You need to invalidate cached data precisely when the underlying data changes — pairing `@Cacheable` reads with `@CacheEvict`/`@CachePut` on the corresponding write methods.

Don't cache data that changes on every read, or where staleness has real consequences (financial balances, security decisions) unless you've deliberately reasoned about the staleness window.

## 3. Core concept

```
 @Cacheable("products")
 findById(id)
        |
        v
   is (products, id) already in cache?
    /                          \
  yes                           no
   |                             |
   v                             v
 return cached value    run method body, store result in cache, return it


 @CacheEvict("products")           @CachePut("products")
 update(id, ...)                    update(id, ...)
        |                                  |
        v                                  v
 always runs method,               always runs method,
 THEN removes (products,id)        THEN stores fresh result
 from cache                        under (products,id)
```

`@Cacheable` is the only one of the three that can *skip* running the method body — `@CacheEvict` and `@CachePut` always execute the method, since they need its result (or the fact that it ran) to update the cache correctly.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cacheable call checks cache first, falls through to the method only on a miss">
  <rect x="10" y="20" width="160" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">findById(42)</text>

  <rect x="230" y="20" width="160" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="310" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">cache lookup</text>

  <rect x="450" y="20" width="160" height="46" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="530" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">HIT: return cached</text>

  <rect x="450" y="120" width="160" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="530" y="140" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MISS: run method,</text>
  <text x="530" y="155" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">store, return</text>

  <line x1="170" y1="43" x2="225" y2="43" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="390" y1="43" x2="445" y2="43" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <line x1="390" y1="55" x2="450" y2="130" stroke="#6db33f" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The AOP proxy around the method intercepts the call and decides, before the method body runs, whether it needs to run at all.

## 5. Runnable example

### Level 1 — Basic

A `@Cacheable` method whose body prints a line only when it actually runs, so cache hits are visible by their *absence* of output.

```java
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.*;

public class CachingBasic {

    record Product(long id, String name) {}

    static class ProductService {
        @Cacheable("products")
        Product findById(long id) {
            System.out.println("Loading product " + id + " from the database...");
            return new Product(id, "Product #" + id);
        }
    }

    @Configuration
    @EnableCaching
    static class Config {
        @Bean
        ProductService productService() { return new ProductService(); }
    }

    public static void main(String[] args) {
        var context = new AnnotationConfigApplicationContext(Config.class);
        ProductService service = context.getBean(ProductService.class);

        System.out.println(service.findById(1));
        System.out.println(service.findById(1)); // no "Loading..." this time — cache hit
        System.out.println(service.findById(2)); // different key — cache miss

        context.close();
    }
}
```

How to run: add `spring-context` on the classpath, then `java CachingBasic.java`.

`@EnableCaching` activates Spring's caching infrastructure, which wraps `ProductService` in an AOP proxy. The first `findById(1)` call misses the (empty) `"products"` cache, runs the method, and stores the result under key `1`. The second call with the same argument hits the cache and never prints `"Loading product..."` — the method body genuinely does not execute.

### Level 2 — Intermediate

Pair `@Cacheable` reads with `@CacheEvict` on the write path, so updating a product invalidates its stale cached entry — a bare `@Cacheable` alone would silently serve outdated data forever.

```java
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.*;

import java.util.HashMap;
import java.util.Map;

public class CachingIntermediate {

    record Product(long id, String name) {}

    static class ProductService {
        private final Map<Long, Product> database = new HashMap<>();

        ProductService() { database.put(1L, new Product(1, "Original Name")); }

        @Cacheable("products")
        Product findById(long id) {
            System.out.println("Loading product " + id + " from the database...");
            return database.get(id);
        }

        @CacheEvict(value = "products", key = "#id")
        void rename(long id, String newName) {
            System.out.println("Renaming product " + id + " to " + newName);
            database.put(id, new Product(id, newName));
        }
    }

    @Configuration
    @EnableCaching
    static class Config {
        @Bean
        ProductService productService() { return new ProductService(); }
    }

    public static void main(String[] args) {
        var context = new AnnotationConfigApplicationContext(Config.class);
        ProductService service = context.getBean(ProductService.class);

        System.out.println(service.findById(1));   // miss: loads "Original Name"
        System.out.println(service.findById(1));   // hit: still "Original Name" (cached)

        service.rename(1, "New Name");              // evicts key 1 from "products"

        System.out.println(service.findById(1));   // miss again: loads fresh "New Name"

        context.close();
    }
}
```

How to run: `java CachingIntermediate.java` (same classpath as Level 1).

`@CacheEvict(value = "products", key = "#id")` uses a SpEL expression (`#id`) to evict exactly the entry for the renamed product, not the whole cache. Without this eviction, the second `findById(1)` after the rename would still return the stale `"Original Name"` from the first load — the demo's final `findById(1)` call proves the eviction worked by printing `"Loading product..."` again and returning the updated name.

### Level 3 — Advanced

Production caching needs conditional caching (don't cache null or error results), composite keys for multi-parameter methods, and time-to-live via a real cache provider instead of the simple in-memory default — this uses Caffeine, a high-performance local cache library, configured with expiration.

```java
import com.github.benmanes.caffeine.cache.Caffeine;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.CachePut;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.caffeine.CaffeineCacheManager;
import org.springframework.context.annotation.*;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

public class CachingAdvanced {

    record Product(long id, String category, String name) {}

    static class ProductService {
        private final Map<String, Product> database = new HashMap<>();

        ProductService() { database.put("electronics:1", new Product(1, "electronics", "Laptop")); }

        @Cacheable(value = "products", key = "#category + ':' + #id", unless = "#result == null")
        Product find(String category, long id) {
            System.out.println("Loading " + category + ":" + id + " from the database...");
            return database.get(category + ":" + id); // may be null -> not cached, per 'unless'
        }

        @CachePut(value = "products", key = "#result.category() + ':' + #result.id()")
        Product save(Product product) {
            System.out.println("Saving " + product);
            database.put(product.category() + ":" + product.id(), product);
            return product; // cache is updated with the FRESH value, no extra read needed
        }
    }

    @Configuration
    @EnableCaching
    static class Config {
        @Bean
        CacheManager cacheManager() {
            var manager = new CaffeineCacheManager("products");
            manager.setCaffeine(Caffeine.newBuilder()
                    .expireAfterWrite(Duration.ofMinutes(10))
                    .maximumSize(10_000));
            return manager;
        }

        @Bean
        ProductService productService() { return new ProductService(); }
    }

    public static void main(String[] args) {
        var context = new AnnotationConfigApplicationContext(Config.class);
        ProductService service = context.getBean(ProductService.class);

        System.out.println(service.find("electronics", 1)); // miss
        System.out.println(service.find("electronics", 1)); // hit

        Product updated = service.save(new Product(1, "electronics", "Gaming Laptop"));
        System.out.println("Saved: " + updated);

        System.out.println(service.find("electronics", 1)); // hit, already fresh from @CachePut

        System.out.println(service.find("electronics", 999)); // miss, null result, not cached (unless)
        System.out.println(service.find("electronics", 999)); // miss AGAIN — nulls were never cached

        context.close();
    }
}
```

How to run: add `com.github.ben-manes.caffeine:caffeine` and `spring-context-support` to the classpath, then `java CachingAdvanced.java`.

`CaffeineCacheManager` with `expireAfterWrite(10 minutes)` bounds staleness automatically. `key = "#category + ':' + #id"` builds a composite cache key from two method parameters via SpEL. `unless = "#result == null"` prevents caching misses, so a not-found lookup is retried on every call instead of being "poisoned" as a permanent null. `@CachePut` on `save` updates the cache with the method's fresh return value directly — unlike `@CacheEvict`, it avoids an extra round trip where the next read would otherwise reload from the database.

## 6. Walkthrough

Trace `CachingAdvanced.main` for the `save`/re-read sequence:

1. **First read.** `service.find("electronics", 1)` computes the SpEL key `"electronics:1"`, finds no entry in the `"products"` Caffeine cache, runs the method body (prints `"Loading electronics:1..."`), gets the `Product(1, "electronics", "Laptop")`, and — since the result is non-null, so `unless` doesn't block it — stores it under key `"electronics:1"` before returning it.
2. **Second read (cache hit).** The same call now finds `"electronics:1"` already present, returns it directly, and the method body never runs — no `"Loading..."` line prints.
3. **Save.** `service.save(new Product(1, "electronics", "Gaming Laptop"))` is `@CachePut`, so it unconditionally runs the method body (prints `"Saving..."`, updates the in-memory `database` map), then evaluates its key SpEL against the *result*: `#result.category() + ':' + #result.id()` → `"electronics:1"`, and stores the fresh `Product("Gaming Laptop")` under that same key, overwriting the stale `"Laptop"` entry.
4. **Third read (cache hit, but fresh).** `service.find("electronics", 1)` again resolves key `"electronics:1"`, finds it cached — but this time it's the `"Gaming Laptop"` value written in step 3, not the original — so it returns the updated product without ever re-querying the database.
5. **Miss on unknown id.** `service.find("electronics", 999)` computes key `"electronics:999"`, misses, runs the method, gets `null` back from the map lookup. Because `unless = "#result == null"` evaluates true, Spring does *not* store this `null` result in the cache.
6. **Repeated miss.** The next call to `find("electronics", 999)` misses again (prints `"Loading..."` a second time) precisely because step 5's `unless` condition prevented the null from being cached — without `unless`, this would have wrongly cached "not found" forever.

```
find(electronics,1)  -> miss -> load -> cache["electronics:1"]=Laptop
find(electronics,1)  -> hit  -> Laptop
save(Gaming Laptop)  -> always runs -> cache["electronics:1"]=Gaming Laptop
find(electronics,1)  -> hit  -> Gaming Laptop  (fresh, no reload)
find(electronics,999)-> miss -> null -> NOT cached (unless)
find(electronics,999)-> miss again -> null -> still not cached
```

## 7. Gotchas & takeaways

> Gotcha: like `@Transactional` and `@Async`, `@Cacheable`/`@CacheEvict`/`@CachePut` rely on a Spring AOP proxy wrapping the bean — calling an annotated method from *another method on the same object* (`this.findById(...)`) bypasses the proxy entirely, so the caching logic silently never runs. Always call cached methods through the Spring-managed bean reference (injected from elsewhere), never via internal self-invocation.

- `@Cacheable` can skip the method entirely on a hit; `@CacheEvict`/`@CachePut` always run the method, since eviction/update needs its outcome.
- Always pair cache reads with eviction or put logic on the corresponding writes — a `@Cacheable` method with no invalidation path will serve stale data indefinitely.
- Use `unless`/`condition` (SpEL) to avoid caching null results, error states, or specific argument values that shouldn't be cached.
- The default `ConcurrentMapCacheManager` (used implicitly if no `CacheManager` bean is defined) never expires or bounds entries — for production, configure a real provider (Caffeine, Redis, JCache) with explicit expiration and size limits, covered in the next card.
