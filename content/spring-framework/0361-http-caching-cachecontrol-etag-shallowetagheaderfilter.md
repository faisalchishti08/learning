---
card: spring-framework
gi: 361
slug: http-caching-cachecontrol-etag-shallowetagheaderfilter
title: "HTTP caching (CacheControl, ETag, ShallowEtagHeaderFilter)"
---

## 1. What it is

Spring MVC provides three complementary tools for HTTP-level response caching: `CacheControl`, a fluent builder for the `Cache-Control` response header (telling clients/proxies *how long* and *how* they may cache a response); `ETag` support built into `ResponseEntity` (an opaque identifier for a specific version of a resource, letting clients ask "has this changed since I last saw ETag X?"); and `ShallowEtagHeaderFilter`, a servlet filter that automatically generates ETags for any response by hashing its body, with no controller code changes required.

```java
@GetMapping("/products/{id}")
public ResponseEntity<Product> get(@PathVariable long id) {
    Product product = repository.findById(id);
    return ResponseEntity.ok()
        .cacheControl(CacheControl.maxAge(Duration.ofMinutes(10)))
        .eTag(String.valueOf(product.getVersion()))
        .body(product);
}
```

## 2. Why & when

Caching reduces load and latency in two distinct ways: `Cache-Control` avoids the request entirely (the client serves a stored copy without contacting the server at all, until the max-age expires), while `ETag`-based **conditional requests** avoid re-sending the response body when nothing has changed (the client still contacts the server, but a `304 Not Modified` response has no body, saving bandwidth and giving the server a chance to check freshness without doing full work).

Use `Cache-Control` when a resource is safe to serve from cache for a known duration without re-checking (public data, versioned static-like resources). Use `ETag`/conditional requests when a resource *might* change at any time but you want clients to avoid re-downloading the body unnecessarily — the server still does a (usually cheap) freshness check on every request, but skips the expensive part (serialization, transfer) when nothing changed. Use `ShallowEtagHeaderFilter` when you want automatic ETag generation across many endpoints without manually computing and setting an `ETag` in every handler.

## 3. Core concept

```
Cache-Control (time-based, no server round-trip needed within max-age):
  Client:  GET /products/1
  Server:  200 OK, Cache-Control: max-age=600
  Client:  (within 600s) serves from LOCAL CACHE, no request sent at all

ETag (conditional request, server round-trip still happens):
  Client:  GET /products/1
  Server:  200 OK, ETag: "v3"
  Client:  (later) GET /products/1, If-None-Match: "v3"
  Server:  compares "v3" to CURRENT version
             unchanged -> 304 Not Modified (NO BODY, cheap)
             changed   -> 200 OK, new ETag, FULL BODY

ShallowEtagHeaderFilter:
  wraps the response, lets the handler run NORMALLY (full body computed),
  THEN hashes the resulting body bytes to generate an ETag automatically
  — saves BANDWIDTH on a 304, but NOT server-side computation,
    since the handler still runs fully every time to produce the body to hash
```

The key distinction in the last point: `ShallowEtagHeaderFilter`'s automatic ETags save bandwidth on unchanged responses but not server-side work, whereas a manually-set `ETag` (as in the code example, derived from a cheap `version` field) can let you skip expensive work entirely by checking the condition *before* doing it.

## 4. Diagram

<svg viewBox="0 0 740 230" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="230" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">Cache-Control avoids the trip; ETag avoids the body</text>

  <rect x="20" y="50" width="330" height="80" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="185" y="72" text-anchor="middle" fill="#6db33f">Cache-Control: max-age=600</text>
  <text x="35" y="95" fill="#8b949e" font-size="10">1st request: full round-trip, 200 + body</text>
  <text x="35" y="113" fill="#8b949e" font-size="10">next 600s: NO request sent at all</text>

  <rect x="390" y="50" width="330" height="80" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="555" y="72" text-anchor="middle" fill="#79c0ff">ETag / If-None-Match</text>
  <text x="405" y="95" fill="#8b949e" font-size="10">every request STILL sent to server</text>
  <text x="405" y="113" fill="#8b949e" font-size="10">unchanged -&gt; 304, no body transferred</text>

  <text x="370" y="170" text-anchor="middle" fill="#8b949e" font-size="10">Often combined: Cache-Control for the common case, ETag as a fallback once max-age expires</text>

  <defs>
    <marker id="a37" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`Cache-Control` skips the request entirely within its window; `ETag` skips only the response body once the client re-checks.*

## 5. Runnable example

### Level 1 — Basic

A product endpoint with a simple time-based cache policy:

```java
// ProductController.java
import org.springframework.http.CacheControl;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;

@RestController
public class ProductController {

    record Product(long id, String name, double price) {}

    @GetMapping("/products/{id}")
    public ResponseEntity<Product> get(@PathVariable long id) {
        Product product = new Product(id, "Drill", 29.99);
        return ResponseEntity.ok()
            .cacheControl(CacheControl.maxAge(Duration.ofMinutes(10)))
            .body(product);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/1
# HTTP/1.1 200 OK
# Cache-Control: max-age=600
# {"id":1,"name":"Drill","price":29.99}
```

A browser (or any HTTP-cache-aware client) receiving this response will serve subsequent requests for the same URL from its local cache for 600 seconds, without contacting the server at all — no `304`, no round-trip, nothing.

### Level 2 — Intermediate

Adding `ETag`-based conditional requests, manually computed from a cheap version field, avoiding expensive re-serialization when nothing changed:

```java
// ProductController.java (extended)
import org.springframework.http.CacheControl;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@RestController
public class ProductController {

    record Product(long id, String name, double price, int version) {}

    private final Map<Long, Product> store = new ConcurrentHashMap<>(
        Map.of(1L, new Product(1, "Drill", 29.99, 3)));

    @GetMapping("/products/{id}")
    public ResponseEntity<Product> get(@PathVariable long id) {
        Product product = store.get(id);
        String currentETag = "\"" + product.version() + "\"";

        return ResponseEntity.ok()
            .cacheControl(CacheControl.maxAge(Duration.ofMinutes(1)))
            .eTag(currentETag)
            .body(product);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/1
# HTTP/1.1 200 OK
# ETag: "3"
# {"id":1,"name":"Drill","price":29.99,"version":3}

curl -i -H 'If-None-Match: "3"' http://localhost:8080/products/1
# HTTP/1.1 304 Not Modified
# (no body at all)

curl -i -H 'If-None-Match: "2"' http://localhost:8080/products/1
# HTTP/1.1 200 OK
# ETag: "3"
# {"id":1,"name":"Drill","price":29.99,"version":3}
```

**What changed:** `.eTag(currentETag)` sets the response's `ETag` header, and — critically — `ResponseEntity`'s handling automatically compares it against any `If-None-Match` header the client sent, short-circuiting to `304 Not Modified` when they match, *before* the framework needs to serialize `product` to JSON at all for that response. This is a genuine server-side compute saving, not just a bandwidth saving, because `version` is a cheap field to check compared to constructing and serializing the full response body.

### Level 3 — Advanced

Production pattern: `ShallowEtagHeaderFilter` applied globally for endpoints where a manual version field isn't available, combined with explicit `ETag` handling for the specific high-traffic endpoint where server-side compute savings genuinely matter — showing both tools used together, each where it fits:

```java
// FilterConfig.java
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.filter.ShallowEtagHeaderFilter;

@Configuration
public class FilterConfig {

    @Bean
    public FilterRegistrationBean<ShallowEtagHeaderFilter> shallowEtagHeaderFilter() {
        FilterRegistrationBean<ShallowEtagHeaderFilter> registration =
            new FilterRegistrationBean<>(new ShallowEtagHeaderFilter());
        registration.addUrlPatterns("/api/catalog/*");   // scoped — NOT applied to every endpoint
        return registration;
    }
}
```

```java
// CatalogController.java — relies on the AUTOMATIC filter-based ETag (no manual version tracking here)
import org.springframework.web.bind.annotation.*;

@RestController
public class CatalogController {

    @GetMapping("/api/catalog/summary")
    public String summary() {
        // Computed freshly every time — ShallowEtagHeaderFilter hashes the OUTPUT,
        // so bandwidth is saved on unchanged responses, but this method still runs in full.
        return "{\"categories\":12,\"totalProducts\":348}";
    }
}
```

```java
// ProductController.java (production version) — MANUAL ETag, skips expensive work entirely
import org.springframework.http.CacheControl;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;

@RestController
public class ProductController {

    record ProductVersion(long id, int version) {}
    record Product(long id, String name, double price, String expensivelyComputedField) {}

    private final ProductVersionRepository versionRepository;   // CHEAP lookup, e.g. an indexed column
    private final ProductRepository productRepository;           // EXPENSIVE: joins, computed fields, etc.

    public ProductController(ProductVersionRepository versionRepository, ProductRepository productRepository) {
        this.versionRepository = versionRepository;
        this.productRepository = productRepository;
    }

    @GetMapping("/api/products/{id}")
    public ResponseEntity<Product> get(@PathVariable long id, @RequestHeader(value = "If-None-Match", required = false) String ifNoneMatch) {
        int currentVersion = versionRepository.getVersion(id);   // cheap check FIRST
        String eTag = "\"" + currentVersion + "\"";

        if (eTag.equals(ifNoneMatch)) {
            return ResponseEntity.status(304).eTag(eTag).build();   // EXPENSIVE work never runs
        }

        Product product = productRepository.findExpensively(id);   // only reached when actually needed
        return ResponseEntity.ok().cacheControl(CacheControl.noCache()).eTag(eTag).body(product);
    }

    interface ProductVersionRepository { int getVersion(long id); }
    interface ProductRepository { Product findExpensively(long id); }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/api/catalog/summary
# ETag automatically added by ShallowEtagHeaderFilter, computed from the response body hash

curl -i -H 'If-None-Match: "3"' http://localhost:8080/api/products/1
# 304 Not Modified — the EXPENSIVE findExpensively(id) call never executes at all
```

**What changed and why:**
- `ShallowEtagHeaderFilter` is scoped to `/api/catalog/*` only, not the whole application — it's a convenient, zero-code-change way to get bandwidth-saving ETags, but it does nothing for server-side compute cost, since the handler always runs fully to produce a body to hash. It's the right tool when server-side compute is already cheap and bandwidth is the actual concern.
- `ProductController.get` demonstrates the opposite, more powerful pattern: check a *cheap* version indicator (`versionRepository.getVersion`, likely a fast indexed lookup) **before** doing the *expensive* work (`productRepository.findExpensively`, perhaps involving joins or computed aggregates). When the client's `If-None-Match` matches, the expensive path is never even reached — this is a genuine server-side optimization, not just a bandwidth one.
- Choosing between these two approaches is a real architectural decision: use `ShallowEtagHeaderFilter` broadly for convenience where compute is cheap; hand-roll version-based `ETag` checks for the specific hot-path endpoints where the expensive-work-avoidance actually matters.

## 6. Walkthrough

**Request: `GET /api/products/1` with `If-None-Match: "3"`, where the product's current version is `3` (Level 3 code).**

1. `DispatcherServlet` dispatches to `ProductController.get(1, "\"3\"")`. `@RequestHeader` extracts the raw `If-None-Match` header value.
2. `versionRepository.getVersion(1)` executes — a cheap, fast lookup (e.g. `SELECT version FROM products WHERE id = 1`, hitting an indexed column) — returns `3`.
3. `eTag = "\"3\""` is constructed to match the format the client would have received previously.
4. `eTag.equals(ifNoneMatch)` → `"\"3\"".equals("\"3\"")` → `true`. The condition is met.
5. The method immediately returns `ResponseEntity.status(304).eTag(eTag).build()` — **crucially, `productRepository.findExpensively(1)` is never called**, because the code path that would call it is skipped entirely by this early return.
6. Response:
   ```
   HTTP/1.1 304 Not Modified
   ETag: "3"

   (no body)
   ```
7. The client, receiving `304`, knows its previously cached copy of the product (from an earlier `200` response) is still valid and continues using it — no new data was transferred, and the server did minimal work (one cheap version lookup, no expensive query).

**Request: same URL, but the product was updated in the meantime (`version` is now `4`), with the client still sending `If-None-Match: "3"`.**

1–3. Identical steps; `versionRepository.getVersion(1)` now returns `4`, so `eTag = "\"4\""`.
4. `eTag.equals(ifNoneMatch)` → `"\"4\"".equals("\"3\"")` → `false`. The condition is not met — the resource has genuinely changed since the client's cached version.
5. Execution falls through to `productRepository.findExpensively(1)` — the full, expensive lookup now runs, since a fresh body genuinely needs to be sent.
6. Response:
   ```
   HTTP/1.1 200 OK
   ETag: "4"
   Cache-Control: no-cache

   {"id":1,"name":"Drill","price":29.99,"expensivelyComputedField":"..."}
   ```
7. The client updates its local cache with this new version (`"4"`) and the fresh body — the next request will send `If-None-Match: "4"`, repeating the cycle.

## 7. Gotchas & takeaways

> **`ShallowEtagHeaderFilter` does NOT save server-side computation — the handler still runs in full every single time to produce the body that gets hashed.** It only saves response *transfer* bandwidth on a `304`. If your goal is reducing server load (not just network traffic), you need a manual, cheap-precondition-check approach like the `ProductController` example, not this filter.

> **`Cache-Control: no-cache` does NOT mean "don't cache" despite the name** — it means "cache, but always revalidate with the server before using the cached copy" (which is exactly the ETag-based conditional-request flow). If you genuinely want to prevent any caching at all, use `Cache-Control: no-store` instead — a frequently confused pair of directives.

> **`ETag` comparison is a byte-exact string match** — if your `ETag` generation isn't perfectly deterministic (e.g. accidentally including a timestamp, or JSON key ordering that varies between serialization runs), conditional requests will never match, silently defeating the entire optimization while still appearing to "work" (just always returning `200` instead of `304`).

- `Cache-Control` avoids the round-trip entirely within its `max-age` window; `ETag`/conditional requests still contact the server but can avoid transferring (and, if checked early, computing) the response body.
- `ShallowEtagHeaderFilter` gives automatic, zero-code-change bandwidth savings but no server-side compute savings, since it hashes the fully-computed response.
- For genuine server-side compute savings, check a cheap version/freshness indicator *before* doing expensive work, and short-circuit to `304` when it matches the client's `If-None-Match`.
- `no-cache` means "always revalidate," not "never cache" — use `no-store` for that; the naming is a common point of confusion.
