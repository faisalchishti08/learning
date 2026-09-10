---
card: system-design
gi: 232
slug: url-shortener-spring-java-implementation-approach
title: URL Shortener — Spring/Java implementation approach
---

## 1. What it is

This page covers the **Spring/Java implementation approach** facet of the **URL Shortener** case study — how the design from every earlier facet ([API design](0227-url-shortener-api-design.md), [data model](0229-url-shortener-data-model-schema.md), [key generation](0230-url-shortener-deep-dive-unique-key-generation-collisions.md)) becomes real Spring Boot code, with the key beans and annotations involved.

## 2. Why & when

Every earlier facet described *what* the system does and *why* it is shaped that way; this facet is where that design becomes a concrete, buildable service. This is the natural last stop in a system-design walkthrough — after requirements, API, data model, and the hard algorithm are settled, implementation approach shows a reviewer or interviewer that the design actually translates into working code, not just diagrams.

## 3. Core concept

- **`UrlController`** — a `@RestController` exposing the two endpoints from [API design](0227-url-shortener-api-design.md): `POST /api/urls` and `GET /{shortCode}`. Thin — it delegates immediately to the service layer, holding no business logic itself.
- **`UrlService`** — a `@Service` holding the business logic: calling the key generator, checking custom-alias availability, checking `expires_at` on redirect, and coordinating the cache-aside pattern from [high-level architecture](0228-url-shortener-high-level-architecture.md).
- **`UrlRepository`** — a Spring Data repository interface over the `url` table from [data model & schema](0229-url-shortener-data-model-schema.md), giving `UrlService` `findById(shortCode)` and `save(url)` without hand-written SQL for the simple cases.
- **`KeyGenerator`** — a `@Component` implementing the block-allocation counter approach from the [deep-dive facet](0230-url-shortener-deep-dive-unique-key-generation-collisions.md), injected into `UrlService`.
- **`@Cacheable` / `@CachePut` on the service layer** — Spring's caching abstraction implements the cache-aside pattern declaratively: annotate the redirect-lookup method with `@Cacheable`, and Spring handles checking the cache first and populating it on a miss, without the service method needing to manage the cache explicitly.

## 4. Diagram

```
   Client
     |
     v
  +--------------------------+
  |     UrlController         |   @RestController
  |  POST /api/urls           |   - thin, delegates to service
  |  GET  /{shortCode}         |
  +-------------+------------+
                |
                v
  +--------------------------+
  |      UrlService            |   @Service
  |  - createShortUrl(...)     |   - calls KeyGenerator
  |  - resolve(shortCode)       |   - @Cacheable on resolve()
  +------+----------+---------+
         |            |
         v            v
  +-----------+   +--------------+
  | KeyGenerator|  | UrlRepository |   Spring Data JPA
  | @Component  |  | (extends       |   - findById / save
  |             |  |  JpaRepository)|
  +-----------+   +------+--------+
                            |
                            v
                       Database (url table)
```
*Caption: the controller is a thin adapter; `UrlService` is where the design decisions from earlier facets (key generation, caching, expiration checks) actually live in code.*

## 5. Runnable example

**Level 1 — Basic.** `@RestController` and `@Service` wired together for the creation endpoint, with the key generator injected.

**Level 2 — Intermediate.** The redirect endpoint with `@Cacheable`, implementing the cache-aside pattern declaratively, plus the expiration check from FR-5.

**Level 3 — Advanced.** Custom-alias handling with a conflict check, and a focused unit test showing the service logic works without a real database or cache.

```java
// UrlShortenerSpringDemo.java
// A focused, runnable stand-in for the real Spring Boot classes - shows the
// same structure and annotations you would use in an actual Spring project,
// with lightweight substitutes for Spring's DI container and @Cacheable so
// this single file runs standalone with `java`, no Spring dependency needed.
import java.util.*;
import java.time.*;

public class UrlShortenerSpringDemo {

    record Url(String shortCode, String longUrl, Instant expiresAt) {}

    // ---------- KeyGenerator (@Component in real Spring) ----------
    static class KeyGenerator {
        long counter = 1_000_000L;
        static final String ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
        String generate() {
            long value = counter++;
            StringBuilder sb = new StringBuilder();
            do { sb.append(ALPHABET.charAt((int) (value % 62))); value /= 62; } while (value > 0);
            return sb.reverse().toString();
        }
    }

    // ---------- UrlRepository (Spring Data JpaRepository in real Spring) ----------
    static class UrlRepository {
        Map<String, Url> table = new HashMap<>();
        Optional<Url> findById(String shortCode) { return Optional.ofNullable(table.get(shortCode)); }
        Url save(Url url) { table.put(url.shortCode(), url); return url; }
        boolean existsById(String shortCode) { return table.containsKey(shortCode); }
    }

    // ---------- UrlService (@Service) ----------
    static class UrlService {
        UrlRepository repository;
        KeyGenerator keyGenerator;
        Map<String, Url> cache = new HashMap<>(); // stands in for Spring's @Cacheable-backed cache

        UrlService(UrlRepository repository, KeyGenerator keyGenerator) {
            this.repository = repository; this.keyGenerator = keyGenerator;
        }

        // Level 1 & 3: create, with optional custom alias (FR-4).
        Url createShortUrl(String longUrl, String customAlias, Instant expiresAt) {
            String shortCode;
            if (customAlias != null) {
                if (repository.existsById(customAlias)) {
                    throw new IllegalStateException("409 Conflict: alias '" + customAlias + "' already taken");
                }
                shortCode = customAlias;
            } else {
                shortCode = keyGenerator.generate();
            }
            Url url = new Url(shortCode, longUrl, expiresAt);
            repository.save(url);
            cache.put(shortCode, url); // prime the cache on creation, per high-level architecture
            return url;
        }

        // Level 2: resolve, with cache-aside behavior (@Cacheable in real Spring) + expiration check (FR-5).
        Optional<String> resolve(String shortCode) {
            Url url = cache.get(shortCode); // @Cacheable checks here first
            boolean fromCache = url != null;
            if (url == null) {
                url = repository.findById(shortCode).orElse(null); // cache miss -> DB
                if (url != null) cache.put(shortCode, url); // populate cache (cache-aside)
            }
            System.out.println("    resolve(\"" + shortCode + "\") - " + (fromCache ? "CACHE HIT" : "cache miss, read from DB"));
            if (url == null) return Optional.empty();
            if (url.expiresAt() != null && Instant.now().isAfter(url.expiresAt())) {
                System.out.println("    \"" + shortCode + "\" has EXPIRED - treating as not found");
                return Optional.empty();
            }
            return Optional.of(url.longUrl());
        }
    }

    public static void main(String[] args) {
        UrlRepository repository = new UrlRepository();
        KeyGenerator keyGenerator = new KeyGenerator();
        UrlService service = new UrlService(repository, keyGenerator);

        System.out.println("Level 1 - create a short URL (auto-generated code):");
        Url url1 = service.createShortUrl("https://example.com/long/path", null, null);
        System.out.println("  created: " + url1);

        System.out.println("\nLevel 2 - resolve it (first call: cache hit, since creation primed the cache):");
        System.out.println("  " + service.resolve(url1.shortCode()));

        System.out.println("\n  resolve a code that only exists in the DB (simulating a cache eviction):");
        service.cache.remove(url1.shortCode());
        System.out.println("  " + service.resolve(url1.shortCode()) + "  (now cached again for next time)");
        System.out.println("  " + service.resolve(url1.shortCode()) + "  (this time: cache hit)");

        System.out.println("\nLevel 3 - custom alias + conflict, and an expired URL:");
        Url aliasUrl = service.createShortUrl("https://example.com/sale", "my-sale", null);
        System.out.println("  created with custom alias: " + aliasUrl);
        try {
            service.createShortUrl("https://example.com/other", "my-sale", null);
        } catch (IllegalStateException e) {
            System.out.println("  " + e.getMessage());
        }

        Url expiredUrl = service.createShortUrl("https://example.com/expired", "old-promo",
            Instant.now().minusSeconds(60)); // already expired
        System.out.println("  " + service.resolve("old-promo") + "  <- expired, treated as not found");
    }
}
```

**How to run:** `java UrlShortenerSpringDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `service.createShortUrl("https://example.com/long/path", null, null)` is called with no custom alias, so it calls `keyGenerator.generate()` — implementing the block-allocation approach from the [deep-dive facet](0230-url-shortener-deep-dive-unique-key-generation-collisions.md), simplified here to a single-counter version for clarity. The new `Url` is saved via `repository.save(...)` and immediately written into `cache` — this last step is the code equivalent of a real `@CachePut` annotation, priming the cache on creation exactly as [high-level architecture](0228-url-shortener-high-level-architecture.md) describes.
2. **Level 2:** `service.resolve(url1.shortCode())` checks `cache.get(shortCode)` first and finds it (since creation just primed it), printing `"CACHE HIT"` — in a real Spring service, this exact check-cache-first behavior is what the `@Cacheable` annotation provides automatically, without `resolve` needing to manage the cache map by hand.
3. `service.cache.remove(url1.shortCode())` simulates a cache eviction (a real cache might evict this entry due to a TTL or memory pressure). The next `resolve(...)` call finds `cache.get(shortCode)` returns `null`, falls through to `repository.findById(shortCode)`, finds the record in the "database," and writes it back into `cache` before returning — this is the cache-aside pattern executing exactly once, on the miss. The call immediately after that finds the freshly repopulated cache entry and reports `"CACHE HIT"` again.
4. **Level 3:** `service.createShortUrl(..., "my-sale", null)` supplies a custom alias. Because `repository.existsById("my-sale")` is `false` the first time, the alias is accepted directly as the `shortCode` with no call to `keyGenerator` at all. The **second** call, attempting to reuse `"my-sale"`, finds `existsById` now `true` and throws `IllegalStateException` with a message mirroring the `409 Conflict` response from [API design](0227-url-shortener-api-design.md) — this is the exact conflict-detection logic that endpoint's contract requires.
5. `service.createShortUrl(..., "old-promo", Instant.now().minusSeconds(60))` creates a URL whose `expiresAt` is already in the past. `service.resolve("old-promo")` finds the record (it does exist, in cache and in the repository) but then checks `url.expiresAt() != null && Instant.now().isAfter(url.expiresAt())` — this evaluates `true`, so the method prints the expiration message and returns `Optional.empty()`, exactly as if the code did not exist at all — implementing FR-5's expiration requirement directly in the resolve path, matching the redirect endpoint's `404` behavior from [API design](0227-url-shortener-api-design.md).

## 7. Gotchas & takeaways

> **Gotcha:** in a real Spring service, `@Cacheable` and the database write inside the same method are not automatically transactional together — if the database write in `createShortUrl` succeeds but the process crashes before the cache-priming step runs, the mapping exists durably in the database but is briefly absent from cache, which is fine (the next resolve just falls through to the database), but relying on cache priming for *correctness* rather than as a pure performance optimization would be a mistake.

- Keep the controller thin and the service layer the true home of business logic — this mirrors the [hexagonal architecture](0198-hexagonal-ports-and-adapters.md) principle of keeping business rules independent of the web framework layer.
- Spring's `@Cacheable` annotation implements the cache-aside pattern declaratively — understanding what it does under the hood (as this demo shows explicitly) makes it much easier to reason about correctness and cache-invalidation edge cases in real code.
- Every piece of logic in `UrlService` traces directly back to a specific functional requirement or facet decision from earlier in this case study — the custom-alias conflict check to FR-4/API design, the expiration check to FR-5, the cache-priming to the high-level architecture's cache-aside pattern.
- This closes out the URL Shortener case study — the same nine-facet structure (functional requirements through implementation approach) applies to any other system-design case study, including the [Rate Limiter](0233-rate-limiter-functional-requirements.md) that follows.
