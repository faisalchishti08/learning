---
card: spring-framework
gi: 333
slug: building-rest-apis
title: "Building REST APIs"
---

## 1. What it is

"Building REST APIs" in Spring MVC means composing the pieces covered in earlier cards — `@RestController`, `@GetMapping`/`@PostMapping`/etc., `@RequestBody`/`@PathVariable`/`@RequestParam`, `ResponseEntity`, `@Valid`/`BindingResult`, and `@ExceptionHandler`/`@ControllerAdvice` — into a coherent, resource-oriented API that follows REST conventions: nouns for URLs, HTTP methods for actions, status codes for outcomes.

```java
@RestController
@RequestMapping("/api/products")
public class ProductController {
    @GetMapping public List<Product> list() { ... }
    @GetMapping("/{id}") public ResponseEntity<Product> get(@PathVariable long id) { ... }
    @PostMapping public ResponseEntity<Product> create(@Valid @RequestBody ProductRequest req) { ... }
    @PutMapping("/{id}") public ResponseEntity<Product> update(@PathVariable long id, @Valid @RequestBody ProductRequest req) { ... }
    @DeleteMapping("/{id}") public ResponseEntity<Void> delete(@PathVariable long id) { ... }
}
```

## 2. Why & when

A well-built REST API is predictable: a client that has never seen your specific endpoints can still guess `DELETE /products/1` deletes product 1, and that a `404` means "not found" and a `201` means "created." This predictability comes from consistently applying REST conventions rather than each endpoint inventing its own shape.

Apply these conventions when:
- The API is consumed by external clients, other teams, or a frontend built independently of the backend — consistency reduces onboarding friction and documentation burden.
- You want HTTP itself (methods, status codes, headers) to carry semantic meaning instead of encoding everything into the response body.
- You need the API to compose well with standard HTTP tooling (caching proxies, API gateways, monitoring) that understands REST semantics but not your bespoke conventions.

## 3. Core concept

```
Resource: /products               (collection)     /products/{id}       (single item)

  GET    /products        -> 200, list of products
  POST   /products         -> 201, created product + Location header
  GET    /products/{id}   -> 200, product | 404 if missing
  PUT    /products/{id}   -> 200, updated product | 404 if missing
  PATCH  /products/{id}   -> 200, partially updated product
  DELETE /products/{id}   -> 204, no body | 404 if missing

Layered request flow for a typical POST /products:

  Request body (JSON)
        |
        v
  Controller: @RequestBody deserialize -> @Valid validate
        |
        v
  Service layer: business rules, orchestration
        |
        v
  Repository layer: persistence (DB read/write)
        |
        v
  Controller: wrap saved entity in 201 ResponseEntity + Location header
        |
        v
  Response body (JSON) + status + headers
```

Each layer transforms the data: raw JSON becomes a validated request DTO, the service turns it into a persisted entity, and the controller shapes the final response — the client never sees internal layers, only the resource representation.

## 4. Diagram

<svg viewBox="0 0 740 260" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="260" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">Layered REST API request flow</text>

  <rect x="20" y="50" width="150" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="80" text-anchor="middle" fill="#79c0ff" font-size="11">Client</text>

  <line x1="170" y1="75" x2="220" y2="75" stroke="#8b949e" marker-end="url(#a9)"/>

  <rect x="220" y="50" width="150" height="50" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="295" y="72" text-anchor="middle" fill="#6db33f" font-size="11">Controller</text>
  <text x="295" y="88" text-anchor="middle" fill="#8b949e" font-size="9">validate + map</text>

  <line x1="370" y1="75" x2="420" y2="75" stroke="#8b949e" marker-end="url(#a9)"/>

  <rect x="420" y="50" width="150" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="495" y="72" text-anchor="middle" fill="#8b949e" font-size="11">Service</text>
  <text x="495" y="88" text-anchor="middle" fill="#8b949e" font-size="9">business rules</text>

  <line x1="570" y1="75" x2="620" y2="75" stroke="#8b949e" marker-end="url(#a9)"/>

  <rect x="620" y="50" width="100" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="670" y="80" text-anchor="middle" fill="#8b949e" font-size="11">DB</text>

  <line x1="670" y1="100" x2="670" y2="140" stroke="#8b949e" marker-end="url(#a9)"/>
  <line x1="620" y1="165" x2="570" y2="165" stroke="#8b949e" marker-end="url(#a9)"/>
  <line x1="420" y1="165" x2="370" y2="165" stroke="#8b949e" marker-end="url(#a9)"/>
  <line x1="220" y1="165" x2="170" y2="165" stroke="#6db33f" marker-end="url(#a9)"/>

  <rect x="20" y="140" width="700" height="50" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="370" y="170" text-anchor="middle" fill="#8b949e" font-size="10">entity flows back up, each layer shaping it, until the controller returns 201 + Location + body</text>

  <text x="370" y="230" text-anchor="middle" fill="#8b949e" font-size="10">Same request travels down through layers, transformed at each; response travels back up, reshaped for the client</text>

  <defs>
    <marker id="a9" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Data crosses each architectural layer in a different shape: JSON → validated DTO → domain entity → persisted row → response DTO → JSON.*

## 5. Runnable example

### Level 1 — Basic

A minimal, in-memory CRUD REST API for products:

```java
// ProductController.java
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.Collection;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@RestController
@RequestMapping("/api/products")
public class ProductController {

    record Product(long id, String name, double price) {}

    private final Map<Long, Product> store = new ConcurrentHashMap<>();
    private final AtomicLong seq = new AtomicLong(1);

    @GetMapping
    public Collection<Product> list() {
        return store.values();
    }

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
        return ResponseEntity.created(URI.create("/api/products/" + id)).body(p);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable long id) {
        return store.remove(id) != null ? ResponseEntity.noContent().build() : ResponseEntity.notFound().build();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -X POST http://localhost:8080/api/products -H "Content-Type: application/json" -d '{"name":"Drill","price":29.99}'
# 201 Created
# Location: /api/products/1
# {"id":1,"name":"Drill","price":29.99}

curl http://localhost:8080/api/products
# [{"id":1,"name":"Drill","price":29.99}]

curl -i -X DELETE http://localhost:8080/api/products/1
# 204 No Content

curl -i http://localhost:8080/api/products/1
# 404 Not Found
```

Each HTTP method maps to exactly one CRUD operation on the `/products` resource; status codes (`201`, `204`, `404`) communicate the outcome without needing to parse the body.

### Level 2 — Intermediate

Add request validation, separate request/response DTOs from the internal entity, and pagination for the list endpoint:

```java
// dto.java
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;

record ProductRequest(@NotBlank String name, @Positive double price) {}
record ProductResponse(long id, String name, double price) {}
record Page<T>(java.util.List<T> items, int page, int size, long total) {}
```

```java
// ProductController.java (extended)
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/products")
public class ProductController {

    private final Map<Long, ProductResponse> store = new ConcurrentHashMap<>();
    private final AtomicLong seq = new AtomicLong(1);

    @GetMapping
    public Page<ProductResponse> list(@RequestParam(defaultValue = "0") int page,
                                       @RequestParam(defaultValue = "10") int size) {
        List<ProductResponse> all = List.copyOf(store.values());
        List<ProductResponse> pageItems = all.stream()
            .skip((long) page * size).limit(size).collect(Collectors.toList());
        return new Page<>(pageItems, page, size, all.size());
    }

    @PostMapping
    public ResponseEntity<ProductResponse> create(@Valid @RequestBody ProductRequest req) {
        long id = seq.getAndIncrement();
        ProductResponse p = new ProductResponse(id, req.name(), req.price());
        store.put(id, p);
        return ResponseEntity.created(URI.create("/api/products/" + id)).body(p);
    }

    @GetMapping("/{id}")
    public ResponseEntity<ProductResponse> get(@PathVariable long id) {
        ProductResponse p = store.get(id);
        return p != null ? ResponseEntity.ok(p) : ResponseEntity.notFound().build();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -X POST http://localhost:8080/api/products -H "Content-Type: application/json" -d '{"name":"","price":-1}'
# 400 Bad Request  (from Spring's default validation error handling)

curl http://localhost:8080/api/products?page=0&size=1
# {"items":[{"id":1,"name":"Drill","price":29.99}],"page":0,"size":1,"total":1}
```

**What changed:** `ProductRequest` is a separate, validated input DTO — it has no `id` field, because the client never assigns ids. `ProductResponse` is a separate output shape — decoupling request/response DTOs from any internal entity means the API contract can stay stable even as internal representations evolve. `Page<T>` wraps the list with pagination metadata instead of returning a bare array, which lets clients discover `total` without a separate count endpoint.

### Level 3 — Advanced

Production-shaped API: a real service/repository split, optimistic concurrency via `ETag`/`If-Match`, structured error responses, and `PATCH` for partial updates — the pieces working together as a system:

```java
// ProductService.java
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@Service
public class ProductService {

    record Product(long id, String name, double price, int version) {}

    private final Map<Long, Product> store = new ConcurrentHashMap<>();
    private final AtomicLong seq = new AtomicLong(1);

    public Optional<Product> find(long id) { return Optional.ofNullable(store.get(id)); }

    public Product create(String name, double price) {
        long id = seq.getAndIncrement();
        Product p = new Product(id, name, price, 1);
        store.put(id, p);
        return p;
    }

    public Optional<Product> updateIfVersionMatches(long id, String name, double price, int expectedVersion) {
        Product current = store.get(id);
        if (current == null || current.version() != expectedVersion) return Optional.empty();
        Product updated = new Product(id, name, price, current.version() + 1);
        store.put(id, updated);
        return Optional.of(updated);
    }
}
```

```java
// ProductController.java (production version)
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

import java.net.URI;

@RestController
@RequestMapping("/api/products")
public class ProductController {

    record ProductRequest(@NotBlank String name, @Positive double price) {}

    private final ProductService service;
    public ProductController(ProductService service) { this.service = service; }

    @PostMapping
    public ResponseEntity<?> create(@Valid @RequestBody ProductRequest req) {
        var p = service.create(req.name(), req.price());
        return ResponseEntity.created(URI.create("/api/products/" + p.id()))
                .eTag("\"" + p.version() + "\"")
                .body(p);
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> get(@PathVariable long id) {
        return service.find(id)
            .map(p -> ResponseEntity.ok().eTag("\"" + p.version() + "\"").body(p))
            .orElseGet(() -> ResponseEntity.notFound().build());
    }

    // Optimistic concurrency: client must send If-Match with the version it last saw
    @PutMapping("/{id}")
    public ResponseEntity<?> update(@PathVariable long id,
                                     @Valid @RequestBody ProductRequest req,
                                     @RequestHeader("If-Match") String ifMatch) {
        int expectedVersion = Integer.parseInt(ifMatch.replace("\"", ""));
        return service.updateIfVersionMatches(id, req.name(), req.price(), expectedVersion)
            .map(p -> ResponseEntity.ok().eTag("\"" + p.version() + "\"").body(p))
            .orElseGet(() -> ResponseEntity.status(HttpStatus.PRECONDITION_FAILED)
                .body("Version mismatch — resource was modified by someone else"));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -X POST http://localhost:8080/api/products -H "Content-Type: application/json" -d '{"name":"Drill","price":29.99}'
# 201 Created
# ETag: "1"
# {"id":1,"name":"Drill","price":29.99,"version":1}

# Update WITHOUT knowing the current version fails:
curl -i -X PUT http://localhost:8080/api/products/1 -H "Content-Type: application/json" -H 'If-Match: "99"' -d '{"name":"Drill Pro","price":39.99}'
# 412 Precondition Failed
# Version mismatch — resource was modified by someone else

# Update WITH the correct version succeeds:
curl -i -X PUT http://localhost:8080/api/products/1 -H "Content-Type: application/json" -H 'If-Match: "1"' -d '{"name":"Drill Pro","price":39.99}'
# 200 OK
# ETag: "2"
# {"id":1,"name":"Drill Pro","price":39.99,"version":2}
```

**What changed and why:**
- Business logic (versioning, storage) moved into `ProductService` — the controller's job is now purely HTTP concerns: parsing, validating, mapping outcomes to status codes and headers.
- `ETag`/`If-Match` implement **optimistic concurrency control** — a standard HTTP mechanism preventing lost updates when two clients edit the same resource concurrently, using status codes the HTTP spec already defines (`412 Precondition Failed`) instead of a bespoke conflict-flag field in the body.
- This mirrors how production REST APIs are actually built: `Controller → Service → Repository`, each layer with a narrow responsibility, wired together through Spring's dependency injection (`ProductController`'s constructor receives `ProductService` automatically).

## 6. Walkthrough

**Request: `PUT /api/products/1` with `If-Match: "1"` and body `{"name":"Drill Pro","price":39.99}` (Level 3 code, current stored version is `1`).**

1. `DispatcherServlet` routes to `ProductController.update(1, req, "\"1\"")`.
2. Spring deserializes the JSON body into `ProductRequest{name="Drill Pro", price=39.99}`, then runs `@Valid` — both fields pass (`@NotBlank`, `@Positive`).
3. `@RequestHeader("If-Match")` extracts the raw header value `"\"1\""` from the request.
4. Handler parses `ifMatch` by stripping quotes → `expectedVersion = 1`.
5. Calls `service.updateIfVersionMatches(1, "Drill Pro", 39.99, 1)`. Inside the service: `store.get(1)` returns the current `Product{id=1, name="Drill", price=29.99, version=1}`. `current.version() (1) == expectedVersion (1)` → match.
6. Service builds a new `Product{id=1, name="Drill Pro", price=39.99, version=2}`, stores it (overwriting the old entry), and returns `Optional.of(updated)`.
7. Back in the controller, `.map(p -> ResponseEntity.ok().eTag("\"2\"").body(p))` builds the success response.
8. Response sent:
   ```
   HTTP/1.1 200 OK
   ETag: "2"
   Content-Type: application/json

   {"id":1,"name":"Drill Pro","price":39.99,"version":2}
   ```

**Same request replayed with a stale `If-Match: "1"` (after the update above already advanced the version to `2`):**

1–4. Identical parsing steps; `expectedVersion = 1`.
5. `service.updateIfVersionMatches(1, ..., 1)`: `store.get(1)` now has `version=2`. `current.version() (2) == expectedVersion (1)` → **no match** → returns `Optional.empty()`.
6. Controller's `.orElseGet(...)` branch runs instead: builds `ResponseEntity.status(PRECONDITION_FAILED).body("Version mismatch...")`.
7. Response sent:
   ```
   HTTP/1.1 412 Precondition Failed
   Content-Type: text/plain

   Version mismatch — resource was modified by someone else
   ```

The client is forced to `GET` the resource again to learn the current version (and current data) before retrying — this is exactly how optimistic concurrency prevents a second client from silently clobbering a first client's update.

## 7. Gotchas & takeaways

> **Returning `200 OK` for every outcome, encoding success/failure only in the body, throws away the entire value of HTTP status codes** — caches, proxies, monitoring, and API gateways all key off status codes. A REST API that always returns `200` forces every consumer to parse the body just to know if a request even succeeded.

> **Mixing internal entity fields into the API response** (e.g. exposing an internal `costPrice` or `supplierId` meant only for internal reporting) is a common mistake that couples your API contract to your database schema. Keep request/response DTOs separate from persistence entities, as in the Level 2/3 examples.

> **Forgetting pagination on a list endpoint works fine in development with 5 rows and becomes a production incident with 5 million.** Design list endpoints with pagination (or at least a hard limit) from day one — retrofitting it later is a breaking API change for existing clients.

- Nouns for resource URLs (`/products`), HTTP methods for actions (`GET`/`POST`/`PUT`/`DELETE`), status codes for outcomes.
- Separate request DTOs (validated input), response DTOs (output shape), and internal entities (persistence) — don't let one class serve all three roles.
- Use `Location` header on `201 Created` responses so clients know where to find the new resource without parsing the body.
- Optimistic concurrency (`ETag`/`If-Match` → `412`) is the standard HTTP-native way to prevent lost updates, cheaper than pessimistic locking for most APIs.
