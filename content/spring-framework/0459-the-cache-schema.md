---
card: spring-framework
gi: 459
slug: the-cache-schema
title: "The cache schema"
---

## 1. What it is

The `cache` namespace (`xmlns:cache="http://www.springframework.org/schema/cache")` is the XML equivalent of `@EnableCaching`/`@Cacheable`/`@CacheEvict`/`@CachePut`, covered earlier in this guide's caching-abstraction cards: `<cache:annotation-driven>` activates those annotations from XML, and `<cache:advice>` paired with an AOP pointcut lets caching behavior be applied *declaratively without any annotations at all*, by naming methods directly in XML instead.

```xml
<cache:advice id="cacheAdvice" cache-manager="cacheManager">
    <cache:caching cache="products">
        <cache:cacheable method="findById"/>
        <cache:cache-evict method="save" all-entries="true"/>
    </cache:caching>
</cache:advice>

<aop:config>
    <aop:advisor advice-ref="cacheAdvice" pointcut="execution(* ProductService.*(..))"/>
</aop:config>
```

## 2. Why & when

`@Cacheable`/`@CacheEvict` require annotating the target class directly — fine for code you own, but not an option for a class you can't modify (a third-party library class, generated code) or don't want to couple to Spring's caching annotations. `<cache:advice>` solves that the same way `<aop:aspect>` solves the equivalent problem for general AOP: it applies caching behavior by naming methods from *outside* the class, via a pointcut, leaving the target class completely untouched.

Reach for the `cache` schema specifically when:

- You're maintaining legacy XML-configured Spring applications where caching behavior is already declared this way, and need to add, modify, or trace which methods are cached and under what cache name.
- You need to apply caching to methods on classes you can't annotate — the same rationale as the `aop` schema, applied specifically to caching.
- You want `<cache:annotation-driven>` to activate `@Cacheable`/`@CacheEvict`/`@CachePut` processing in an XML-rooted application, the direct equivalent of `@EnableCaching` on a `@Configuration` class.

For new code, `@EnableCaching` plus `@Cacheable`/`@CacheEvict` annotations directly on methods is almost always simpler and far more common — the `cache` schema's `<cache:advice>` form specifically earns its keep only when annotating the target class isn't possible or desirable.

## 3. Core concept

```
 <cache:advice id="cacheAdvice" cache-manager="cacheManager">
     <cache:caching cache="products">
         <cache:cacheable method="findById"/>          -- read-through caching
         <cache:cache-evict method="save" all-entries="true"/>  -- invalidation
     </cache:caching>
 </cache:advice>
        |
        v
 produces a real Advice object (like any other AOP advice)
        |
        | combined with a pointcut, via <aop:advisor>
        v
 <aop:config><aop:advisor advice-ref="cacheAdvice" pointcut="execution(...)"/></aop:config>
        |
        v
 Spring proxies matching beans; calls to findById() check the cache first,
 calls to save() clear the "products" cache afterward
```

`cache:advice` alone declares *what* the caching behavior should be; an `aop:advisor` (or equivalent pointcut wiring) is what says *where* it applies — the two are deliberately separate, the same separation `aop:aspect` uses.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="cache:advice defines cacheable and evict behavior, applied to matching beans via an aop:advisor pointcut">
  <rect x="10" y="20" width="190" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;cache:advice&gt;</text>
  <text x="105" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">cacheable + cache-evict rules</text>

  <rect x="250" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;aop:advisor&gt;</text>
  <text x="340" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">pointcut names WHERE</text>

  <rect x="480" y="20" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ProductService</text>
  <text x="555" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">unannotated, proxied</text>

  <rect x="250" y="120" width="180" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="340" y="142" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">"products" cache</text>
  <text x="340" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">CacheManager-backed</text>

  <line x1="200" y1="45" x2="245" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="430" y1="45" x2="475" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="340" y1="70" x2="340" y2="115" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`cache:advice` defines the caching rules; `aop:advisor` decides which beans they apply to; both act on a completely unannotated target class.

## 5. Runnable example

The scenario: a `ProductService` with a slow `findById` lookup, cached without any annotations on the class itself — evolving from a basic `cache:cacheable` rule, to adding `cache:cache-evict` for invalidation on save, to a full setup with a real `ConcurrentMapCacheManager` and cache-hit/miss verification.

### Level 1 — Basic

Wire `<cache:advice>` with a single `<cache:cacheable>` rule against an unannotated `findById` method and confirm repeated calls hit the cache.

```java
import org.springframework.cache.CacheManager;
import org.springframework.cache.concurrent.ConcurrentMapCacheManager;
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicInteger;

public class CacheSchemaLevel1 {

    public static class ProductService {
        final AtomicInteger lookups = new AtomicInteger();
        public String findById(String id) {
            lookups.incrementAndGet();
            System.out.println("[db] looking up product " + id);
            return "Product-" + id;
        }
    }

    public static void main(String[] args) {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:aop="http://www.springframework.org/schema/aop"
                   xmlns:cache="http://www.springframework.org/schema/cache"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/aop
                       https://www.springframework.org/schema/aop/spring-aop.xsd
                       http://www.springframework.org/schema/cache
                       https://www.springframework.org/schema/cache/spring-cache.xsd">

                <bean id="cacheManager" class="org.springframework.cache.concurrent.ConcurrentMapCacheManager"/>
                <bean id="productService" class="CacheSchemaLevel1$ProductService"/>

                <cache:advice id="cacheAdvice" cache-manager="cacheManager">
                    <cache:caching cache="products">
                        <cache:cacheable method="findById"/>
                    </cache:caching>
                </cache:advice>

                <aop:config>
                    <aop:advisor advice-ref="cacheAdvice"
                        pointcut="execution(* CacheSchemaLevel1.ProductService.findById(..))"/>
                </aop:config>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        ProductService service = ctx.getBean(ProductService.class);
        System.out.println(service.findById("42"));
        System.out.println(service.findById("42"));
        System.out.println(service.findById("42"));

        int lookups = service.lookups.get();
        System.out.println("actual DB lookups = " + lookups);
        if (lookups != 1) throw new AssertionError("Expected only 1 real lookup, cache should have served the rest, got " + lookups);
        System.out.println("cache:cacheable served repeated calls from cache -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-context`, `spring-aop`, `spring-context-support` (for the cache abstraction), and `aspectjweaver` on the classpath, then `java CacheSchemaLevel1.java` on JDK 17+.

`<cache:cacheable method="findById"/>` inside `<cache:caching cache="products">` says: cache the result of `findById`, keyed by its argument, in a cache named `"products"`. The `<aop:advisor>` names the pointcut — here, exactly `ProductService.findById` — that this advice applies to. Three calls with the same argument produce only one real lookup; the `lookups` counter proves the cache genuinely intercepted the second and third calls before they reached the real method body.

### Level 2 — Intermediate

Add `<cache:cache-evict>` on a `save` method so updating a product clears its cached entry, the paired read/write pattern any real caching layer needs.

```java
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

public class CacheSchemaLevel2 {

    public static class ProductService {
        final Map<String, String> store = new HashMap<>(Map.of("42", "Product-42-v1"));
        final AtomicInteger lookups = new AtomicInteger();

        public String findById(String id) {
            lookups.incrementAndGet();
            System.out.println("[db] looking up product " + id);
            return store.get(id);
        }

        public void save(String id, String value) {
            System.out.println("[db] saving product " + id + " = " + value);
            store.put(id, value);
        }
    }

    public static void main(String[] args) {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:aop="http://www.springframework.org/schema/aop"
                   xmlns:cache="http://www.springframework.org/schema/cache"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/aop
                       https://www.springframework.org/schema/aop/spring-aop.xsd
                       http://www.springframework.org/schema/cache
                       https://www.springframework.org/schema/cache/spring-cache.xsd">

                <bean id="cacheManager" class="org.springframework.cache.concurrent.ConcurrentMapCacheManager"/>
                <bean id="productService" class="CacheSchemaLevel2$ProductService"/>

                <cache:advice id="cacheAdvice" cache-manager="cacheManager">
                    <cache:caching cache="products">
                        <cache:cacheable method="findById"/>
                        <cache:cache-evict method="save" all-entries="true"/>
                    </cache:caching>
                </cache:advice>

                <aop:config>
                    <aop:advisor advice-ref="cacheAdvice"
                        pointcut="execution(* CacheSchemaLevel2.ProductService.*(..))"/>
                </aop:config>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        ProductService service = ctx.getBean(ProductService.class);
        System.out.println(service.findById("42")); // real lookup, cached
        System.out.println(service.findById("42")); // served from cache

        service.save("42", "Product-42-v2"); // evicts the whole "products" cache
        System.out.println(service.findById("42")); // must be a real lookup again, returning v2

        int lookups = service.lookups.get();
        System.out.println("total real lookups = " + lookups);
        if (lookups != 2) throw new AssertionError("Expected exactly 2 real lookups (before and after eviction), got " + lookups);
        System.out.println("cache:cache-evict invalidated the cache on save -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java CacheSchemaLevel2.java`.

`<cache:cache-evict method="save" all-entries="true"/>` clears the entire `"products"` cache whenever `save` is called. The sequence — lookup (real, cached), lookup (cached), save (evicts), lookup (real again, sees the updated value) — produces exactly 2 real database lookups, confirming both caching and invalidation worked; note the pointcut was widened to `ProductService.*(..)` here since both `findById` and `save` now need to be proxied.

### Level 3 — Advanced

Add a `key` expression (SpEL) for multi-argument cache keys and a `condition` to skip caching for certain inputs, the production-flavored refinements needed once a real method takes more than one argument or shouldn't always be cached.

```java
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicInteger;

public class CacheSchemaLevel3 {

    public static class ProductService {
        final AtomicInteger lookups = new AtomicInteger();

        public String findByIdAndRegion(String id, String region) {
            lookups.incrementAndGet();
            System.out.println("[db] looking up product " + id + " in region " + region);
            return "Product-" + id + "@" + region;
        }
    }

    public static void main(String[] args) {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:aop="http://www.springframework.org/schema/aop"
                   xmlns:cache="http://www.springframework.org/schema/cache"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/aop
                       https://www.springframework.org/schema/aop/spring-aop.xsd
                       http://www.springframework.org/schema/cache
                       https://www.springframework.org/schema/cache/spring-cache.xsd">

                <bean id="cacheManager" class="org.springframework.cache.concurrent.ConcurrentMapCacheManager"/>
                <bean id="productService" class="CacheSchemaLevel3$ProductService"/>

                <cache:advice id="cacheAdvice" cache-manager="cacheManager">
                    <cache:caching cache="products">
                        <cache:cacheable method="findByIdAndRegion"
                            key="#id + ':' + #region"
                            condition="#region != 'UNCACHED'"/>
                    </cache:caching>
                </cache:advice>

                <aop:config>
                    <aop:advisor advice-ref="cacheAdvice"
                        pointcut="execution(* CacheSchemaLevel3.ProductService.*(..))"/>
                </aop:config>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        ProductService service = ctx.getBean(ProductService.class);

        System.out.println(service.findByIdAndRegion("42", "eu-west")); // real
        System.out.println(service.findByIdAndRegion("42", "eu-west")); // cached (same key)
        System.out.println(service.findByIdAndRegion("42", "us-east")); // real (different key)
        System.out.println(service.findByIdAndRegion("42", "UNCACHED")); // real (condition fails)
        System.out.println(service.findByIdAndRegion("42", "UNCACHED")); // real again (never cached)

        int lookups = service.lookups.get();
        System.out.println("total real lookups = " + lookups);
        if (lookups != 4) throw new AssertionError("Expected 4 real lookups (eu-west once, us-east once, UNCACHED twice), got " + lookups);
        System.out.println("multi-arg key + condition worked correctly -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java CacheSchemaLevel3.java`.

`key="#id + ':' + #region"` builds a composite cache key from both method arguments using SpEL, so `("42","eu-west")` and `("42","us-east")` are cached separately rather than colliding — without an explicit `key`, the default key generator would combine all arguments similarly, but an explicit expression makes the exact keying strategy visible and controllable. `condition="#region != 'UNCACHED'"` is evaluated *before* the method runs; when it evaluates `false`, caching is skipped entirely for that call, which is why both `UNCACHED` calls hit the real method.

## 6. Walkthrough

Trace Level 3's five calls in order.

1. **`findByIdAndRegion("42", "eu-west")`** — the proxy evaluates `condition="#region != 'UNCACHED'"`: `"eu-west" != "UNCACHED"` is `true`, so caching applies. It evaluates `key="#id + ':' + #region"` → `"42:eu-west"`, checks the `"products"` cache for that key, finds nothing, so it calls the real method (`lookups` → 1), gets `"Product-42@eu-west"`, and stores it under key `"42:eu-west"` before returning it.
2. **Second call, same args** — same key `"42:eu-west"` is computed, found in the cache this time, so the real method is skipped entirely; `lookups` stays at 1.
3. **`findByIdAndRegion("42", "us-east")`** — condition passes, key computes to `"42:us-east"`, a *different* key, not found in the cache, so the real method runs (`lookups` → 2) and the result is stored under this new key.
4. **`findByIdAndRegion("42", "UNCACHED")`** — condition evaluates `"UNCACHED" != "UNCACHED"` → `false`, so the cache is bypassed entirely: no lookup, no storage, straight to the real method (`lookups` → 3).
5. **Fifth call, same `"UNCACHED"` args** — condition still evaluates `false` every time, so caching never engages for this region regardless of repetition; the real method runs again (`lookups` → 4).
6. **Verification**: the program checks `lookups.get()` equals exactly 4 — one for `eu-west`, one for `us-east`, and two (never cached) for `UNCACHED` — confirming both the composite key and the condition worked as intended.

```
 call 1: ("42","eu-west")  -> condition true, key "42:eu-west"  -> MISS -> real call (lookups=1) -> store
 call 2: ("42","eu-west")  -> condition true, key "42:eu-west"  -> HIT  -> no real call
 call 3: ("42","us-east")  -> condition true, key "42:us-east"  -> MISS -> real call (lookups=2) -> store
 call 4: ("42","UNCACHED") -> condition FALSE                   -> real call (lookups=3), no caching
 call 5: ("42","UNCACHED") -> condition FALSE                   -> real call (lookups=4), no caching
```

## 7. Gotchas & takeaways

> **Gotcha:** `<cache:cache-evict method="save" all-entries="true"/>` clears the *entire named cache*, not just the entry related to the saved item — for a large cache, that's a much bigger invalidation than might be intended. A more targeted eviction uses a `key` attribute on `cache-evict` matching the specific entry, the same way `cache:cacheable`'s `key` targets a specific entry to read.

- `cache:advice` plus `aop:advisor` is the "apply to code you can't annotate" escape hatch for caching, mirroring the `aop:aspect` "apply to code you can't annotate" pattern for AOP generally.
- `key` and `condition` accept SpEL expressions with method parameter names available via `#paramName` — the same SpEL surface `@Cacheable(key=..., condition=...)` uses, so knowledge of one transfers directly to the other.
- A `condition` that evaluates `false` bypasses caching entirely for that call — no read, no write — distinct from a cache miss, which still writes the result afterward.
- `<cache:annotation-driven>` (the XML equivalent of `@EnableCaching`) is the right choice when the target classes *can* be annotated with `@Cacheable`/`@CacheEvict` directly — reach for `<cache:advice>` specifically when they can't or shouldn't be.
