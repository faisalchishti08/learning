---
card: spring-framework
gi: 324
slug: requestmapping-on-type-method-combining
title: "@RequestMapping on type & method (combining)"
---

## 1. What it is

`@RequestMapping` can be placed at the **class level** (type-level) to set a base path and shared constraints, and at the **method level** to refine or extend them. Spring MVC combines the two mappings:

```java
@RestController
@RequestMapping(path = "/api/v1/products",    // type-level
                produces = "application/json")
public class ProductController {

    @GetMapping("/{id}")                        // combined: GET /api/v1/products/{id}
    public Product get(@PathVariable long id) { ... }

    @PostMapping                                // combined: POST /api/v1/products
    public Product create(@RequestBody Product p) { ... }

    @DeleteMapping("/{id}")                     // combined: DELETE /api/v1/products/{id}
    public void delete(@PathVariable long id) { ... }
}
```

Type-level attributes (`produces`, `consumes`, `headers`, `params`) are inherited by all method mappings. Method-level attributes **narrow** or **override** per-attribute — the combination rules differ by attribute.

---

## 2. Why & when

Use type-level `@RequestMapping` to:
- Share a common path prefix across all methods in a controller (avoids repeating `/api/v1/products` on every method).
- Set a default `produces` or `consumes` for all methods (e.g. the whole controller speaks JSON).
- Apply `params` or `headers` conditions to the entire controller (e.g. require `X-API-Version: 2` on all routes).

Use method-level composed annotations (`@GetMapping`, `@PostMapping`, etc.) to:
- Specify the HTTP method.
- Add a method-specific sub-path.
- Override or narrow the type-level `produces`/`consumes` for that one handler.

---

## 3. Core concept

```
Combining rules by attribute:

path:
  Type:   /api/v1/products
  Method: /{id}
  Result: /api/v1/products/{id}          ← concatenated

method (HTTP verb):
  Type:   (unset — any)
  Method: GET
  Result: GET only                        ← method level wins

produces:
  Type:   application/json
  Method: (unset)
  Result: application/json               ← inherited from type

  Type:   application/json
  Method: application/xml
  Result: application/xml                ← method level overrides type

consumes / headers / params:
  Type + Method conditions are ANDed:
  Type:   params="version=1"
  Method: params="lang=en"
  Result: must satisfy BOTH version=1 AND lang=en

Request matching:
  Spring evaluates type-level conditions first.
  If they fail, the controller is not a candidate.
  If type-level passes, method-level conditions evaluated.
```

---

## 4. Diagram

<svg viewBox="0 0 740 260" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="260" fill="#0d1117"/>

  <!-- type level -->
  <rect x="10" y="30" width="320" height="100" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="170" y="48" text-anchor="middle" fill="#8b949e">@RequestMapping (type level)</text>
  <text x="20" y="67" fill="#6db33f" font-size="11">path     = "/api/v1/products"</text>
  <text x="20" y="83" fill="#79c0ff" font-size="11">produces = "application/json"</text>
  <text x="20" y="99" fill="#8b949e" font-size="11">method   = (all)</text>
  <text x="20" y="115" fill="#8b949e" font-size="11">params   = (none)</text>

  <!-- method level -->
  <rect x="10" y="155" width="320" height="80" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="170" y="173" text-anchor="middle" fill="#6db33f">@GetMapping("/{id}")  (method level)</text>
  <text x="20" y="191" fill="#6db33f" font-size="11">path   = "/{id}"</text>
  <text x="20" y="207" fill="#6db33f" font-size="11">method = GET</text>
  <text x="20" y="222" fill="#8b949e" font-size="11">produces = (inherited: application/json)</text>

  <!-- combined -->
  <line x1="330" y1="100" x2="370" y2="160" stroke="#8b949e" marker-end="url(#arca)"/>
  <line x1="330" y1="195" x2="370" y2="175" stroke="#8b949e" marker-end="url(#arca)"/>

  <rect x="380" y="80" width="340" height="100" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="550" y="100" text-anchor="middle" fill="#6db33f">Combined mapping</text>
  <text x="390" y="120" fill="#e6edf3" font-size="11">GET /api/v1/products/{id}</text>
  <text x="390" y="137" fill="#e6edf3" font-size="11">produces: application/json</text>
  <text x="390" y="154" fill="#e6edf3" font-size="11">method:   GET</text>
  <text x="390" y="170" fill="#8b949e" font-size="10">type path + method path concatenated</text>

  <text x="370" y="248" text-anchor="middle" fill="#8b949e" font-size="11">path concatenated; method/produces/consumes: method overrides type; params/headers: ANDed</text>

  <defs>
    <marker id="arca" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Path is concatenated; `produces`/`consumes`/method specified at the method level override the type-level value; `params`/`headers` conditions are ANDed.*

---

## 5. Runnable example

### Level 1 — Basic

Product CRUD controller with type-level path prefix:

```java
// ProductController.java
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;

@RestController
@RequestMapping("/api/v1/products")           // type-level prefix
public class ProductController {

    record Product(long id, String name, double price) {}

    private final Map<Long, Product> store = new ConcurrentHashMap<>();
    private final AtomicLong seq = new AtomicLong(1);

    @GetMapping                               // GET /api/v1/products
    public Collection<Product> list() {
        return store.values();
    }

    @GetMapping("/{id}")                      // GET /api/v1/products/{id}
    public ResponseEntity<Product> get(@PathVariable long id) {
        Product p = store.get(id);
        return p != null ? ResponseEntity.ok(p) : ResponseEntity.notFound().build();
    }

    @PostMapping                              // POST /api/v1/products
    public ResponseEntity<Product> create(@RequestBody Product req) {
        long id = seq.getAndIncrement();
        Product p = new Product(id, req.name(), req.price());
        store.put(id, p);
        return ResponseEntity.status(HttpStatus.CREATED).body(p);
    }

    @DeleteMapping("/{id}")                   // DELETE /api/v1/products/{id}
    public ResponseEntity<Void> delete(@PathVariable long id) {
        return store.remove(id) != null
                ? ResponseEntity.noContent().build()
                : ResponseEntity.notFound().build();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -X POST http://localhost:8080/api/v1/products \
     -H "Content-Type: application/json" \
     -d '{"name":"Drill","price":29.99}'
# {"id":1,"name":"Drill","price":29.99}

curl http://localhost:8080/api/v1/products
# [{"id":1,...}]

curl -X DELETE http://localhost:8080/api/v1/products/1
# 204 No Content
```

All methods inherit `/api/v1/products` as the base path. No repetition on each method. Sub-paths on methods are appended automatically.

---

### Level 2 — Intermediate

Version-negotiated controller: type-level `produces` defaults to JSON; one method overrides to produce both JSON and XML; type-level `params` requires API version:

```java
// ProductController.java (extended)
import jakarta.xml.bind.annotation.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping(
    path    = "/api/products",
    params  = "version=2",            // type-level: all methods require ?version=2
    produces = MediaType.APPLICATION_JSON_VALUE  // default for all methods
)
public class ProductController {

    @XmlRootElement @XmlAccessorType(XmlAccessType.FIELD)
    public static class Product {
        public long   id;
        public String name;
        public double price;
        Product() {}
        Product(long id, String name, double price) { this.id=id; this.name=name; this.price=price; }
    }

    // Inherits type-level produces → JSON only
    @GetMapping
    public Product[] list() {
        return new Product[]{ new Product(1,"Drill",29.99), new Product(2,"Hammer",14.99) };
    }

    // Method-level overrides produces → accepts JSON or XML negotiation
    @GetMapping(value = "/{id}",
                produces = {MediaType.APPLICATION_JSON_VALUE, MediaType.APPLICATION_XML_VALUE})
    public Product get(@PathVariable long id) {
        return new Product(id, "Drill", 29.99);
    }

    // No ?version=2 → 404 (no method matches without the param)
}
```

Add JAXB dependency for XML support.

**How to run:**
```bash
./mvnw spring-boot:run

# Missing version param → 404
curl http://localhost:8080/api/products

# With version=2 → 200 JSON
curl "http://localhost:8080/api/products?version=2"
# [{"id":1,...},{"id":2,...}]

# Detail: JSON
curl -H "Accept: application/json" "http://localhost:8080/api/products/1?version=2"
# {"id":1,"name":"Drill","price":29.99}

# Detail: XML (overrides type-level produces)
curl -H "Accept: application/xml" "http://localhost:8080/api/products/1?version=2"
# <product><id>1</id><name>Drill</name><price>29.99</price></product>
```

**What changed:** Type-level `params = "version=2"` gates the entire controller — no method in the controller matches without the param. `get()` overrides `produces` to add XML support; `list()` inherits JSON-only. The `version=2` constraint is still required for `get()` because params conditions are ANDed.

---

### Level 3 — Advanced

Production scenario: a versioned API family with a v1 and v2 controller sharing the same path structure, discriminated by `Accept` header version:

```java
// ProductsV1Controller.java — responds to Accept: application/vnd.acme.product.v1+json
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping(
    path    = "/products",
    produces = "application/vnd.acme.product.v1+json"
)
public class ProductsV1Controller {

    record ProductV1(long id, String name) {}           // v1: no price

    @GetMapping("/{id}")
    public ProductV1 get(@PathVariable long id) {
        return new ProductV1(id, "Drill");
    }

    @GetMapping
    public ProductV1[] list() {
        return new ProductV1[]{ new ProductV1(1,"Drill"), new ProductV1(2,"Hammer") };
    }
}

// ProductsV2Controller.java — responds to Accept: application/vnd.acme.product.v2+json
@RestController
@RequestMapping(
    path    = "/products",
    produces = "application/vnd.acme.product.v2+json"
)
public class ProductsV2Controller {

    record ProductV2(long id, String name, double price, String description) {}

    @GetMapping("/{id}")
    public ProductV2 get(@PathVariable long id) {
        return new ProductV2(id, "Drill", 29.99, "Cordless 18V drill");
    }

    @GetMapping
    public ProductV2[] list() {
        return new ProductV2[]{ new ProductV2(1,"Drill",29.99,"18V"), new ProductV2(2,"Hammer",14.99,"16oz") };
    }
}
```

`WebConfig.java`:
```java
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.MediaType;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;

@Configuration
public class WebConfig {
    @Bean
    public MappingJackson2HttpMessageConverter customConverter(ObjectMapper mapper) {
        MappingJackson2HttpMessageConverter converter = new MappingJackson2HttpMessageConverter(mapper);
        converter.setSupportedMediaTypes(java.util.List.of(
                MediaType.APPLICATION_JSON,
                MediaType.parseMediaType("application/vnd.acme.product.v1+json"),
                MediaType.parseMediaType("application/vnd.acme.product.v2+json")));
        return converter;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# v1 — returns ProductV1 (id + name only)
curl -H "Accept: application/vnd.acme.product.v1+json" http://localhost:8080/products/1
# {"id":1,"name":"Drill"}

# v2 — returns ProductV2 (id + name + price + description)
curl -H "Accept: application/vnd.acme.product.v2+json" http://localhost:8080/products/1
# {"id":1,"name":"Drill","price":29.99,"description":"Cordless 18V drill"}

# No Accept header → 406 (no controller matches */* without content negotiation)
curl http://localhost:8080/products/1
```

**What changed and why:**
- Two controllers, same path `/products` — differentiated entirely by `produces` at the type level. Spring's content negotiation routes to the correct controller based on `Accept` header.
- Type-level `produces = "application/vnd.acme.product.v1+json"` applies to `GET /products` and `GET /products/{id}` in `ProductsV1Controller` — no need to repeat on each method.
- The custom `MappingJackson2HttpMessageConverter` adds vendor media types to the converter's supported list so Jackson can write them.
- This pattern avoids URL path versioning (`/v1/products`, `/v2/products`) — the same URL works across versions; the `Accept` header selects the response shape.

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="200" fill="#0d1117"/>
  <text x="350" y="20" text-anchor="middle" fill="#8b949e">Content-type-discriminated versioning via type-level produces</text>

  <!-- request -->
  <rect x="10" y="50" width="160" height="100" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="68" text-anchor="middle" fill="#79c0ff">GET /products/1</text>
  <text x="90" y="86" text-anchor="middle" fill="#8b949e" font-size="10">Accept: vnd.acme.v1+json</text>
  <text x="90" y="100" text-anchor="middle" fill="#8b949e" font-size="10">  ↓ or</text>
  <text x="90" y="116" text-anchor="middle" fill="#8b949e" font-size="10">Accept: vnd.acme.v2+json</text>

  <!-- dispatcher -->
  <line x1="170" y1="100" x2="205" y2="100" stroke="#8b949e" marker-end="url(#arca2)"/>
  <rect x="205" y="70" width="160" height="60" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="285" y="90" text-anchor="middle" fill="#8b949e">DispatcherServlet</text>
  <text x="285" y="107" text-anchor="middle" fill="#8b949e" font-size="10">content negotiation</text>
  <text x="285" y="122" text-anchor="middle" fill="#8b949e" font-size="10">matches produces attribute</text>

  <!-- v1 -->
  <line x1="365" y1="90" x2="400" y2="75" stroke="#6db33f" marker-end="url(#arca2)"/>
  <rect x="400" y="50" width="140" height="45" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="68" text-anchor="middle" fill="#6db33f">ProductsV1Controller</text>
  <text x="470" y="84" text-anchor="middle" fill="#8b949e" font-size="10">produces v1+json</text>

  <!-- v2 -->
  <line x1="365" y1="110" x2="400" y2="125" stroke="#79c0ff" marker-end="url(#arca2)"/>
  <rect x="400" y="110" width="140" height="45" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="470" y="128" text-anchor="middle" fill="#79c0ff">ProductsV2Controller</text>
  <text x="470" y="144" text-anchor="middle" fill="#8b949e" font-size="10">produces v2+json</text>

  <text x="350" y="180" text-anchor="middle" fill="#8b949e" font-size="10">Same URL /products/{id} — two controllers, two response shapes, zero path duplication</text>
  <defs><marker id="arca2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Per-request: `GET /api/v1/products/1?version=2` (`ProductController` from Level 2):**

1. `DispatcherServlet` asks `RequestMappingHandlerMapping` to find a handler.
2. Evaluates type-level conditions: path `/api/products` — request path `/api/v1/products/1?version=2` — no match (different prefix). For the correct controller (`/api/products`), continues.
3. Type-level `params = "version=2"` checked: request has `?version=2` → **pass**.
4. Type-level `produces = application/json` checked: `Accept: application/json` (or `*/*`) → **pass**.
5. Evaluates method-level mappings within the controller.
6. `@GetMapping("/{id}")` path: combined path = `/api/products/{id}` — matches `/api/products/1` → `id=1`.
7. `@GetMapping("/{id}")` produces: `{application/json, application/xml}` — request `Accept: application/json` → **pass** (method overrides type).
8. Handler selected: `ProductController.get(1)`.
9. Executes → returns `Product{1,"Drill",29.99}`.

**Without `?version=2`:**

Step 3 fails — controller not selected. No other controller matches `/api/products`. `DispatcherServlet` returns `404`.

---

## 7. Gotchas & takeaways

> **Type-level `produces` is overridden entirely by a method-level `produces`, not merged.** If type specifies `application/json` and the method specifies `application/xml`, only XML is accepted for that method — JSON is no longer a valid response type. To support both, list both in the method's `produces`.

> **An empty string path at the method level with a trailing slash at the type level can cause surprises.** `@RequestMapping("/products/")` at type + `@GetMapping` at method → `/products/`. `@GetMapping("")` → `/products/`. Use explicit paths to avoid ambiguity.

> **`@RequestMapping` at the type level with no path still establishes conditions.** A type-level `params="version=2"` without a path gates ALL methods — requests without `?version=2` won't match any method in the controller, even with the exact URL.

- Path combining: type path + method path concatenated (no separator added — include leading `/` on method paths).
- `produces`/`consumes`: method level overrides type level entirely (not merged).
- `params`/`headers`: type and method conditions ANDed — both must be satisfied.
- `method` (HTTP verb): type level can set a default; method level overrides.
- Type-level `produces` is the cleanest way to version a REST API by content type — one controller per version, same URL structure.
