---
card: spring-framework
gi: 321
slug: responseentity
title: "ResponseEntity"
---

## 1. What it is

`ResponseEntity<T>` is the explicit HTTP response wrapper — it combines a body (`T`), `HttpStatus` code, and `HttpHeaders` into a single return value. It implies `@ResponseBody` automatically:

```java
@GetMapping("/products/{id}")
public ResponseEntity<Product> getProduct(@PathVariable long id) {
    Product p = repo.findById(id).orElse(null);
    if (p == null) return ResponseEntity.notFound().build();      // 404, no body
    return ResponseEntity.ok(p);                                   // 200 + JSON body
}
```

`ResponseEntity` lets you control status code, headers, and body from within the method body — unlike annotations, which are static per-mapping.

---

## 2. Why & when

Use `ResponseEntity` when:
- Different code paths within one handler need different status codes (200 vs 404 vs 409).
- Response headers must be set dynamically (ETag, Location, Cache-Control).
- You want to return a body alongside a non-200 status (e.g. 201 Created with a Location header).
- Implementing HTTP conditional requests (`If-None-Match`, `checkNotModified()`).

Avoid `ResponseEntity` when all paths return the same status and no dynamic headers are needed — a plain return type with `@ResponseBody` is cleaner.

---

## 3. Core concept

```
ResponseEntity.ok(product)
  = ResponseEntity<Product>(body=product, status=200, headers={})

ResponseEntity.status(HttpStatus.CREATED)
             .location(URI.create("/products/42"))
             .body(product)
  = ResponseEntity<Product>(body=product, status=201,
      headers={Location: /products/42})

ResponseEntity.noContent().build()
  = ResponseEntity<Void>(body=null, status=204, headers={})

ResponseEntity.notFound().build()
  = ResponseEntity<Void>(body=null, status=404, headers={})

Return value handler: HttpEntityMethodProcessor
  → sets response status from entity.getStatusCode()
  → copies entity.getHeaders() to response headers
  → if body != null: serializes via HttpMessageConverter
```

---

## 4. Diagram

<svg viewBox="0 0 740 250" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="250" fill="#0d1117"/>

  <!-- handler -->
  <rect x="10" y="50" width="180" height="100" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="68" text-anchor="middle" fill="#79c0ff">Handler</text>
  <text x="20" y="85" fill="#8b949e" font-size="10">if not found:</text>
  <text x="20" y="99" fill="#e74c3c" font-size="10">  ResponseEntity.notFound()</text>
  <text x="20" y="113" fill="#8b949e" font-size="10">if conflict:</text>
  <text x="20" y="127" fill="#e74c3c" font-size="10">  ResponseEntity.status(409)...</text>
  <text x="20" y="141" fill="#8b949e" font-size="10">else:</text>
  <text x="20" y="155" fill="#6db33f" font-size="10">  ResponseEntity.ok(product)</text>

  <line x1="190" y1="100" x2="225" y2="100" stroke="#8b949e" marker-end="url(#arre)"/>

  <!-- processor -->
  <rect x="225" y="50" width="220" height="100" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="335" y="70" text-anchor="middle" fill="#6db33f">HttpEntity</text>
  <text x="335" y="85" text-anchor="middle" fill="#6db33f">MethodProcessor</text>
  <text x="235" y="105" fill="#8b949e" font-size="10">response.setStatus(entity.getStatus())</text>
  <text x="235" y="120" fill="#8b949e" font-size="10">response.addHeaders(entity.getHeaders())</text>
  <text x="235" y="135" fill="#8b949e" font-size="10">if body: HttpMessageConverter.write()</text>

  <line x1="445" y1="100" x2="480" y2="100" stroke="#8b949e" marker-end="url(#arre)"/>

  <!-- response -->
  <rect x="480" y="50" width="240" height="100" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="600" y="70" text-anchor="middle" fill="#6db33f">HTTP Response</text>
  <text x="490" y="90" fill="#8b949e" font-size="10">Status:  200 / 201 / 204 / 404 / 409</text>
  <text x="490" y="106" fill="#8b949e" font-size="10">Headers: Location / ETag / Cache-Control</text>
  <text x="490" y="122" fill="#e6edf3" font-size="11">Body:    JSON product (or empty)</text>

  <!-- builder chain -->
  <rect x="100" y="185" width="480" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="340" y="200" text-anchor="middle" fill="#8b949e">Builder API</text>
  <text x="340" y="218" text-anchor="middle" fill="#8b949e" font-size="10">ResponseEntity.status(201).location(uri).eTag("\"v1\"").cacheControl(CacheControl.maxAge(60, SECONDS)).body(obj)</text>

  <text x="370" y="245" text-anchor="middle" fill="#8b949e" font-size="11">Status + headers + body set independently; no @ResponseBody annotation required</text>

  <defs>
    <marker id="arre" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`ResponseEntity` builder API composes status + headers + body fluently; `HttpEntityMethodProcessor` writes each component to the servlet response.*

---

## 5. Runnable example

### Level 1 — Basic

CRUD product API using `ResponseEntity` for all status codes:

```java
// ProductController.java
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.net.URI;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@RestController
@RequestMapping("/products")
public class ProductController {

    record Product(long id, String name, double price) {}

    private final Map<Long, Product> store = new ConcurrentHashMap<>();
    private final AtomicLong seq = new AtomicLong(1);

    @GetMapping("/{id}")
    public ResponseEntity<Product> get(@PathVariable long id) {
        Product p = store.get(id);
        return p != null ? ResponseEntity.ok(p) : ResponseEntity.notFound().build();
    }

    @PostMapping
    public ResponseEntity<Product> create(@RequestBody Product req) {
        long id = seq.getAndIncrement();
        Product p = new Product(id, req.name(), req.price());
        store.put(id, p);
        return ResponseEntity.created(URI.create("/products/" + id)).body(p);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable long id) {
        return store.remove(id) != null
                ? ResponseEntity.noContent().build()   // 204
                : ResponseEntity.notFound().build();   // 404
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Create → 201 with Location header
curl -i -X POST http://localhost:8080/products \
     -H "Content-Type: application/json" \
     -d '{"name":"Drill","price":29.99}'
# HTTP/1.1 201 Created
# Location: /products/1
# {"id":1,"name":"Drill","price":29.99}

# Get → 200
curl http://localhost:8080/products/1

# Delete → 204
curl -i -X DELETE http://localhost:8080/products/1

# Get missing → 404
curl -i http://localhost:8080/products/99
```

`ResponseEntity.created(uri)` sets status 201 and `Location` header in one call. `ResponseEntity.noContent().build()` returns 204 with no body. `ResponseEntity.notFound().build()` returns 404 with no body.

---

### Level 2 — Intermediate

Same API — adding ETag-based conditional GET, caching headers, and `If-Match` for optimistic locking on PUT:

```java
// ProductController.java (extended)
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.context.request.WebRequest;
import java.net.URI;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@RestController
@RequestMapping("/products")
public class ProductController {

    record Product(long id, String name, double price, long version) {}

    private final Map<Long, Product> store = new ConcurrentHashMap<>();
    private final AtomicLong seq = new AtomicLong(1);

    @GetMapping("/{id}")
    public ResponseEntity<Product> get(@PathVariable long id, WebRequest webRequest) {
        Product p = store.get(id);
        if (p == null) return ResponseEntity.notFound().build();

        String etag = "\"v" + p.version() + "\"";
        if (webRequest.checkNotModified(etag)) {
            return ResponseEntity.status(HttpStatus.NOT_MODIFIED).build();  // 304
        }

        return ResponseEntity.ok()
                .eTag(etag)
                .cacheControl(CacheControl.maxAge(60, java.util.concurrent.TimeUnit.SECONDS))
                .body(p);
    }

    @PostMapping
    public ResponseEntity<Product> create(@RequestBody Product req) {
        long id = seq.getAndIncrement();
        Product p = new Product(id, req.name(), req.price(), 1L);
        store.put(id, p);
        return ResponseEntity.created(URI.create("/products/" + id)).body(p);
    }

    @PutMapping("/{id}")
    public ResponseEntity<Product> update(
            @PathVariable long id,
            @RequestHeader(value = "If-Match", required = false) String ifMatch,
            @RequestBody Product req) {

        Product existing = store.get(id);
        if (existing == null) return ResponseEntity.notFound().build();

        String currentEtag = "\"v" + existing.version() + "\"";
        if (ifMatch != null && !ifMatch.equals(currentEtag)) {
            return ResponseEntity.status(HttpStatus.PRECONDITION_FAILED).build();  // 412
        }

        Product updated = new Product(id, req.name(), req.price(), existing.version() + 1);
        store.put(id, updated);
        String newEtag = "\"v" + updated.version() + "\"";
        return ResponseEntity.ok().eTag(newEtag).body(updated);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Create
curl -i -X POST http://localhost:8080/products \
     -H "Content-Type: application/json" \
     -d '{"name":"Drill","price":29.99}'
# 201; ETag: "v1"

# Conditional GET — cache hit
curl -i -H 'If-None-Match: "v1"' http://localhost:8080/products/1
# 304 Not Modified (no body)

# Update with ETag
curl -i -X PUT http://localhost:8080/products/1 \
     -H "Content-Type: application/json" \
     -H 'If-Match: "v1"' \
     -d '{"name":"Power Drill","price":39.99}'
# 200 OK; ETag: "v2"

# Stale update — fails
curl -i -X PUT http://localhost:8080/products/1 \
     -H "Content-Type: application/json" \
     -H 'If-Match: "v1"' \
     -d '{"name":"Old Drill","price":19.99}'
# 412 Precondition Failed
```

**What changed:** ETag added dynamically via `ResponseEntity.ok().eTag(etag)` — static annotations can't express version-derived ETags. `If-Match` enforced in the PUT handler returns 412 on mismatch — optimistic locking without a database transaction.

---

### Level 3 — Advanced

Production scenario: conditional request with `checkNotModified`, paginated list with `Link` headers, and a `Content-Disposition` attachment download:

```java
// ProductController.java (production)
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.context.request.WebRequest;
import java.net.URI;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.*;

@RestController
@RequestMapping("/products")
public class ProductController {

    record Product(long id, String name, double price) {}

    private final Map<Long, Product> store = new ConcurrentHashMap<>(Map.of(
            1L, new Product(1, "Drill", 29.99),
            2L, new Product(2, "Hammer", 14.99),
            3L, new Product(3, "Saw", 49.99)));
    private final AtomicLong seq = new AtomicLong(4);

    // Paginated list with Link headers
    @GetMapping
    public ResponseEntity<List<Product>> list(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "2") int size) {

        List<Product> all = new ArrayList<>(store.values());
        int total = all.size();
        int from = Math.min(page * size, total);
        int to   = Math.min(from + size, total);
        List<Product> pageData = all.subList(from, to);

        HttpHeaders headers = new HttpHeaders();
        headers.add("X-Total-Count", String.valueOf(total));
        if (to < total) {
            headers.add("Link",
                    "</products?page=" + (page + 1) + "&size=" + size + ">; rel=\"next\"");
        }
        if (page > 0) {
            headers.add("Link",
                    "</products?page=" + (page - 1) + "&size=" + size + ">; rel=\"prev\"");
        }

        return ResponseEntity.ok().headers(headers).body(pageData);
    }

    // Conditional GET with Last-Modified
    @GetMapping("/{id}")
    public ResponseEntity<Product> get(@PathVariable long id, WebRequest webRequest) {
        Product p = store.get(id);
        if (p == null) return ResponseEntity.notFound().build();

        long lastModified = 1_700_000_000_000L + p.id() * 1000;
        if (webRequest.checkNotModified(lastModified)) {
            return ResponseEntity.status(304).build();
        }

        return ResponseEntity.ok()
                .lastModified(lastModified)
                .cacheControl(CacheControl.maxAge(300, java.util.concurrent.TimeUnit.SECONDS))
                .body(p);
    }

    // CSV export as attachment
    @GetMapping(value = "/export", produces = "text/csv")
    public ResponseEntity<byte[]> export() {
        String csv = store.values().stream()
                .sorted(Comparator.comparingLong(Product::id))
                .map(p -> p.id() + "," + p.name() + "," + p.price())
                .collect(Collectors.joining("\n", "id,name,price\n", ""));

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        "attachment; filename=\"products.csv\"")
                .contentType(MediaType.parseMediaType("text/csv"))
                .body(csv.getBytes());
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Paginated list with Link header
curl -i "http://localhost:8080/products?page=0&size=2"
# X-Total-Count: 3
# Link: </products?page=1&size=2>; rel="next"
# [product1, product2]

# Conditional GET
curl -i http://localhost:8080/products/1
# Last-Modified: Mon, ...
curl -i -H "If-Modified-Since: <date from above>" http://localhost:8080/products/1
# 304 Not Modified

# CSV download
curl -O -J http://localhost:8080/products/export
# saves products.csv
```

**What changed and why:**
- `ResponseEntity.ok().headers(httpHeaders).body(...)` builder accepts pre-built `HttpHeaders` — useful when multiple headers are computed in a loop (pagination `Link` headers).
- `checkNotModified(lastModified)` sets `Last-Modified` and handles `If-Modified-Since` negotiation — returns `true` when the client's copy is current, so the handler returns early with 304.
- `Content-Disposition: attachment; filename="..."` triggers browser download instead of inline display — set dynamically based on query params (e.g. export filename).

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="180" fill="#0d1117"/>
  <text x="350" y="20" text-anchor="middle" fill="#8b949e">ResponseEntity builder API — composing status, headers, body</text>

  <rect x="10" y="35" width="310" height="110" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="165" y="55" text-anchor="middle" fill="#6db33f">Common builders</text>
  <text x="20" y="73" fill="#e6edf3" font-size="10">ResponseEntity.ok(body)                → 200 + body</text>
  <text x="20" y="89" fill="#e6edf3" font-size="10">ResponseEntity.created(uri)            → 201 + Location</text>
  <text x="20" y="105" fill="#e6edf3" font-size="10">ResponseEntity.noContent().build()     → 204 no body</text>
  <text x="20" y="121" fill="#e6edf3" font-size="10">ResponseEntity.notFound().build()      → 404 no body</text>
  <text x="20" y="137" fill="#e6edf3" font-size="10">ResponseEntity.status(409).body(err)   → 409 + error</text>

  <rect x="340" y="35" width="340" height="110" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="510" y="55" text-anchor="middle" fill="#79c0ff">Fluent headers</text>
  <text x="350" y="73" fill="#e6edf3" font-size="10">.eTag("\"v1\"")                         → ETag header</text>
  <text x="350" y="89" fill="#e6edf3" font-size="10">.lastModified(epochMs)                  → Last-Modified</text>
  <text x="350" y="105" fill="#e6edf3" font-size="10">.cacheControl(CacheControl.maxAge(60)) → Cache-Control</text>
  <text x="350" y="121" fill="#e6edf3" font-size="10">.location(URI.create(...))              → Location</text>
  <text x="350" y="137" fill="#e6edf3" font-size="10">.header("X-Custom", "value")            → arbitrary</text>

  <text x="350" y="165" text-anchor="middle" fill="#8b949e" font-size="10">All return BodyBuilder; .body(T) or .build() terminates the chain</text>
</svg>

---

## 6. Walkthrough

**Per-request: `GET /products/1` with `If-None-Match: "v1"`:**

1. `DispatcherServlet` routes to `get(1, webRequest)`.
2. `store.get(1)` → `Product{1,"Drill",29.99,version=1}`.
3. `etag = "\"v1\""`.
4. `webRequest.checkNotModified("\"v1\"")` → compares with `If-None-Match: "v1"` → match → returns `true`.
5. Handler returns `ResponseEntity.status(304).build()`.
6. `HttpEntityMethodProcessor` sets response status 304, no body.
7. Browser uses cached response.

**On next update (PUT increments version to 2):**

8. `GET /products/1` with `If-None-Match: "v1"` → `checkNotModified("\"v2\"")` → mismatch → returns `false`.
9. Handler returns `ResponseEntity.ok().eTag("\"v2\"").body(product)`.
10. Response: 200 OK, `ETag: "v2"`, JSON body.
11. Browser caches new version.

---

## 7. Gotchas & takeaways

> **`ResponseEntity.notFound().build()` cannot carry a body.** `notFound()` returns a `HeadersBuilder`, not a `BodyBuilder`. If you need a 404 with an error body, use `ResponseEntity.status(404).body(errorDto)`.

> **Returning `ResponseEntity<?>` with a wildcard disables generic type inference for `HttpMessageConverter`.** The serializer may not pick the right type. Use concrete generic types (`ResponseEntity<Product>`) when possible.

> **`checkNotModified()` modifies the response directly.** It sets `ETag`/`Last-Modified` headers on the response immediately when called — even if you then return a 304. Don't set these headers again in the `ResponseEntity` builder or they'll be duplicated.

- `ResponseEntity.ok(body)` → 200 + body; `created(uri)` → 201 + Location; `noContent()` → 204; `notFound()` → 404.
- Fluent builder: `.eTag()`, `.cacheControl()`, `.lastModified()`, `.header()`, `.body()`.
- `checkNotModified(etag|lastModified)` handles conditional GET; return `status(304).build()` when it returns `true`.
- Use concrete generic type (`ResponseEntity<Product>`) not wildcard (`ResponseEntity<?>`) for correct serialization.
- Combine with `@ExceptionHandler` returning `ResponseEntity` for consistent error shapes across the API.
