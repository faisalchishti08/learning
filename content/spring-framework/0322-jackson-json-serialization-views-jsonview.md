---
card: spring-framework
gi: 322
slug: jackson-json-serialization-views-jsonview
title: "Jackson JSON serialization views (@JsonView)"
---

## 1. What it is

`@JsonView` is a Jackson annotation that controls which fields are included in serialization/deserialization based on a named **view interface**. Spring MVC's `@ResponseBody` and `@RequestBody` integration lets you select a view per handler method:

```java
// View marker interfaces
public interface Views {
    interface Public {}
    interface Internal extends Public {}  // extends = superset
}

public class Product {
    @JsonView(Views.Public.class)   public long id;
    @JsonView(Views.Public.class)   public String name;
    @JsonView(Views.Internal.class) public double costPrice;  // hidden from Public view
}

@GetMapping("/products/{id}")
@JsonView(Views.Public.class)   // serializes only id + name
public Product getPublic(@PathVariable long id) { ... }

@GetMapping("/admin/products/{id}")
@JsonView(Views.Internal.class) // serializes id + name + costPrice
public Product getAdmin(@PathVariable long id) { ... }
```

`@JsonView` controls field visibility without creating separate DTOs.

---

## 2. Why & when

Use `@JsonView` when:
- The same domain object must be serialized differently for different roles (public vs admin, summary vs detail).
- You want to avoid multiple DTOs mapping the same entity with different field subsets.
- A list endpoint should return fewer fields than a detail endpoint (summary vs full).
- `@RequestBody` should deserialize only a subset of fields (ignore read-only fields on create).

Avoid `@JsonView` when the serialization difference is too large — if fewer than 30% of fields are shared, separate response types are clearer.

---

## 3. Core concept

```
Views hierarchy:
  interface Public {}
  interface Internal extends Public {}

Product fields:
  @JsonView(Public)   id       → visible in Public view AND Internal view
  @JsonView(Public)   name     → visible in Public view AND Internal view
  @JsonView(Internal) costPrice → visible ONLY in Internal view

Handler:
  @JsonView(Views.Public.class)
  @GetMapping("/products")
  public List<Product> listPublic()
  
  → MappingJackson2HttpMessageConverter writes with objectMapper
      .writerWithView(Views.Public.class)
  → costPrice is skipped (not annotated with Public or a parent of Public)
  → output: [{"id":1,"name":"Drill"}, ...]

  @JsonView(Views.Internal.class)
  @GetMapping("/admin/products")
  public List<Product> listAdmin()
  → writerWithView(Views.Internal.class)
  → output: [{"id":1,"name":"Drill","costPrice":18.50}, ...]
```

---

## 4. Diagram

<svg viewBox="0 0 740 240" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="240" fill="#0d1117"/>

  <!-- views hierarchy -->
  <rect x="10" y="30" width="200" height="80" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="110" y="48" text-anchor="middle" fill="#8b949e">Views hierarchy</text>
  <text x="30" y="66" fill="#6db33f" font-size="10">interface Public {}</text>
  <text x="30" y="82" fill="#79c0ff" font-size="10">interface Internal extends Public {}</text>
  <text x="30" y="98" fill="#8b949e" font-size="10">Internal ⊃ Public (superset)</text>

  <!-- product fields -->
  <rect x="230" y="30" width="220" height="100" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="48" text-anchor="middle" fill="#6db33f">Product fields</text>
  <text x="240" y="66" fill="#6db33f" font-size="10">@JsonView(Public) id</text>
  <text x="240" y="81" fill="#6db33f" font-size="10">@JsonView(Public) name</text>
  <text x="240" y="97" fill="#79c0ff" font-size="10">@JsonView(Internal) costPrice</text>
  <text x="240" y="112" fill="#8b949e" font-size="10">no @JsonView → hidden (default OFF)</text>

  <!-- handler views -->
  <rect x="470" y="30" width="250" height="100" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="595" y="48" text-anchor="middle" fill="#6db33f">Handler @JsonView</text>
  <text x="480" y="65" fill="#6db33f" font-size="11">@JsonView(Public)</text>
  <text x="480" y="80" fill="#8b949e" font-size="10">→ id, name</text>
  <text x="480" y="95" fill="#79c0ff" font-size="11">@JsonView(Internal)</text>
  <text x="480" y="110" fill="#8b949e" font-size="10">→ id, name, costPrice</text>

  <!-- Jackson writer -->
  <rect x="230" y="155" width="460" height="50" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="460" y="172" text-anchor="middle" fill="#8b949e">MappingJackson2HttpMessageConverter</text>
  <text x="460" y="190" text-anchor="middle" fill="#8b949e" font-size="10">objectMapper.writerWithView(handlerView).writeValue(stream, obj)</text>
  <text x="460" y="204" text-anchor="middle" fill="#8b949e" font-size="10">field included if: field's @JsonView is same as or parent of handler view</text>

  <text x="370" y="230" text-anchor="middle" fill="#8b949e" font-size="11">@JsonView on handler selects which annotated fields are included — non-annotated fields excluded by default</text>

  <defs></defs>
</svg>

*Field included when: the field's `@JsonView` class is the same as or an ancestor of the handler's active view.*

---

## 5. Runnable example

### Level 1 — Basic

Public vs admin product views — admin sees cost price, public does not:

```java
// Product.java
import com.fasterxml.jackson.annotation.JsonView;

public class Product {

    public interface Views {
        interface Public {}
        interface Admin extends Public {}
    }

    @JsonView(Views.Public.class)  public long   id;
    @JsonView(Views.Public.class)  public String name;
    @JsonView(Views.Public.class)  public double salePrice;
    @JsonView(Views.Admin.class)   public double costPrice;
    @JsonView(Views.Admin.class)   public int    stock;

    public Product() {}
    public Product(long id, String name, double salePrice, double costPrice, int stock) {
        this.id = id; this.name = name; this.salePrice = salePrice;
        this.costPrice = costPrice; this.stock = stock;
    }
}

// ProductController.java
import com.fasterxml.jackson.annotation.JsonView;
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    private final Product product = new Product(1, "Drill", 49.99, 18.50, 25);

    @GetMapping("/products/{id}")
    @JsonView(Product.Views.Public.class)
    public Product getPublic(@PathVariable long id) { return product; }

    @GetMapping("/admin/products/{id}")
    @JsonView(Product.Views.Admin.class)
    public Product getAdmin(@PathVariable long id) { return product; }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/1
# {"id":1,"name":"Drill","salePrice":49.99}

curl http://localhost:8080/admin/products/1
# {"id":1,"name":"Drill","salePrice":49.99,"costPrice":18.50,"stock":25}
```

`@JsonView(Views.Admin.class)` on the handler activates Jackson's view writer. Fields annotated `@JsonView(Public)` appear in both views because `Admin extends Public` — inheritance propagates visibility. Fields without any `@JsonView` are excluded from both views (Jackson's default when a view is active).

---

### Level 2 — Intermediate

Same product — adding summary view for list endpoints, and `@JsonView` on `@RequestBody` to ignore read-only fields on create:

```java
// Product.java
import com.fasterxml.jackson.annotation.JsonView;

public class Product {

    public interface Views {
        interface Summary {}
        interface Detail extends Summary {}
        interface Write {}  // for deserialization only
    }

    @JsonView({Views.Summary.class, Views.Write.class}) public long   id;
    @JsonView({Views.Summary.class, Views.Write.class}) public String name;
    @JsonView(Views.Detail.class)                       public double salePrice;
    @JsonView(Views.Detail.class)                       public String description;
    // createdAt is server-set — no Write view, so @RequestBody ignores it
    @JsonView(Views.Detail.class)                       public String createdAt;

    // constructor omitted for brevity
}

// ProductController.java
import com.fasterxml.jackson.annotation.JsonView;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/products")
public class ProductController {

    private static final List<Product> store = List.of(
            new Product(1L, "Drill", 49.99, "Cordless 18V", "2024-01-01"),
            new Product(2L, "Hammer", 14.99, "Claw hammer 16oz", "2024-01-02"));

    // Summary view — list endpoint returns fewer fields
    @GetMapping
    @JsonView(Product.Views.Summary.class)
    public List<Product> list() { return store; }

    // Detail view — single product returns all fields
    @GetMapping("/{id}")
    @JsonView(Product.Views.Detail.class)
    public Product get(@PathVariable long id) {
        return store.stream().filter(p -> p.id == id).findFirst().orElse(null);
    }

    // Write view on @RequestBody — createdAt is ignored even if client sends it
    @PostMapping
    @JsonView(Product.Views.Detail.class)
    public Product create(@RequestBody @JsonView(Product.Views.Write.class) Product req) {
        req.createdAt = java.time.LocalDate.now().toString(); // server-set
        return req;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# List — summary only
curl http://localhost:8080/products
# [{"id":1,"name":"Drill"},{"id":2,"name":"Hammer"}]

# Detail
curl http://localhost:8080/products/1
# {"id":1,"name":"Drill","salePrice":49.99,"description":"Cordless 18V","createdAt":"2024-01-01"}

# Create — client sends createdAt but it's ignored
curl -X POST http://localhost:8080/products \
     -H "Content-Type: application/json" \
     -d '{"name":"Saw","salePrice":29.99,"createdAt":"2000-01-01"}'
# response: createdAt=today (server-set, not client value)
```

**What changed:** `@JsonView` on `@RequestBody` controls *deserialization* — fields outside the `Write` view are ignored when reading the request body. `createdAt` (annotated `Detail`, not `Write`) is silently skipped even if the client sends it — the server assigns it after binding.

---

### Level 3 — Advanced

Production scenario: role-based view selection at runtime using `MappingJacksonValue`, and a `ResponseBodyAdvice` that applies the correct view for the authenticated role:

```java
// ProductViews.java
public interface ProductViews {
    interface Customer {}
    interface Seller extends Customer {}
    interface Admin extends Seller {}
}

// Product.java
import com.fasterxml.jackson.annotation.JsonView;

public class Product {
    @JsonView(ProductViews.Customer.class) public long   id;
    @JsonView(ProductViews.Customer.class) public String name;
    @JsonView(ProductViews.Customer.class) public double salePrice;
    @JsonView(ProductViews.Seller.class)   public int    stock;
    @JsonView(ProductViews.Admin.class)    public double costPrice;
    @JsonView(ProductViews.Admin.class)    public String supplierId;

    public Product(long id, String name, double salePrice, double costPrice, int stock, String supplierId) {
        this.id = id; this.name = name; this.salePrice = salePrice;
        this.costPrice = costPrice; this.stock = stock; this.supplierId = supplierId;
    }
}

// ProductController.java — returns MappingJacksonValue for runtime view selection
import com.fasterxml.jackson.databind.ser.impl.SimpleBeanPropertyFilter;
import org.springframework.http.converter.json.MappingJacksonValue;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/products")
public class ProductController {

    private final Product product =
            new Product(1, "Drill", 49.99, 18.50, 25, "SUP-7");

    @GetMapping("/{id}")
    public MappingJacksonValue get(@PathVariable long id,
            @RequestHeader(value = "X-Role", defaultValue = "CUSTOMER") String role) {

        MappingJacksonValue wrapper = new MappingJacksonValue(product);
        wrapper.setSerializationView(switch (role) {
            case "ADMIN"  -> ProductViews.Admin.class;
            case "SELLER" -> ProductViews.Seller.class;
            default       -> ProductViews.Customer.class;
        });
        return wrapper;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Customer view
curl -H "X-Role: CUSTOMER" http://localhost:8080/products/1
# {"id":1,"name":"Drill","salePrice":49.99}

# Seller view
curl -H "X-Role: SELLER" http://localhost:8080/products/1
# {"id":1,"name":"Drill","salePrice":49.99,"stock":25}

# Admin view
curl -H "X-Role: ADMIN" http://localhost:8080/products/1
# {"id":1,"name":"Drill","salePrice":49.99,"stock":25,"costPrice":18.5,"supplierId":"SUP-7"}
```

**What changed and why:**
- `MappingJacksonValue` wraps the domain object and carries the view class to the converter — enabling runtime view selection without separate handler methods.
- `switch (role)` picks the view dynamically — in production, replace `X-Role` header with `SecurityContextHolder.getContext().getAuthentication()` role extraction.
- Hierarchy: `Admin extends Seller extends Customer` — Admin view includes all Customer and Seller fields automatically. No duplication of `@JsonView` annotations.

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="190" fill="#0d1117"/>
  <text x="350" y="20" text-anchor="middle" fill="#8b949e">@JsonView field visibility by view hierarchy</text>

  <!-- fields -->
  <rect x="10" y="35" width="160" height="130" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="90" y="53" text-anchor="middle" fill="#8b949e">Fields</text>
  <text x="20" y="70" fill="#6db33f" font-size="10">@JsonView(Customer) id</text>
  <text x="20" y="85" fill="#6db33f" font-size="10">@JsonView(Customer) name</text>
  <text x="20" y="100" fill="#6db33f" font-size="10">@JsonView(Customer) salePrice</text>
  <text x="20" y="115" fill="#79c0ff" font-size="10">@JsonView(Seller) stock</text>
  <text x="20" y="130" fill="#e74c3c" font-size="10">@JsonView(Admin) costPrice</text>
  <text x="20" y="145" fill="#e74c3c" font-size="10">@JsonView(Admin) supplierId</text>

  <!-- customer -->
  <rect x="190" y="35" width="140" height="75" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="260" y="53" text-anchor="middle" fill="#6db33f">Customer view</text>
  <text x="200" y="70" fill="#6db33f" font-size="10">✓ id</text>
  <text x="200" y="85" fill="#6db33f" font-size="10">✓ name</text>
  <text x="200" y="100" fill="#6db33f" font-size="10">✓ salePrice</text>

  <!-- seller -->
  <rect x="350" y="35" width="140" height="95" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="420" y="53" text-anchor="middle" fill="#79c0ff">Seller view</text>
  <text x="360" y="70" fill="#6db33f" font-size="10">✓ id</text>
  <text x="360" y="85" fill="#6db33f" font-size="10">✓ name</text>
  <text x="360" y="100" fill="#6db33f" font-size="10">✓ salePrice</text>
  <text x="360" y="115" fill="#79c0ff" font-size="10">✓ stock</text>

  <!-- admin -->
  <rect x="510" y="35" width="170" height="130" rx="4" fill="#1c2430" stroke="#e74c3c"/>
  <text x="595" y="53" text-anchor="middle" fill="#e74c3c">Admin view</text>
  <text x="520" y="70" fill="#6db33f" font-size="10">✓ id</text>
  <text x="520" y="85" fill="#6db33f" font-size="10">✓ name</text>
  <text x="520" y="100" fill="#6db33f" font-size="10">✓ salePrice</text>
  <text x="520" y="115" fill="#79c0ff" font-size="10">✓ stock</text>
  <text x="520" y="130" fill="#e74c3c" font-size="10">✓ costPrice</text>
  <text x="520" y="145" fill="#e74c3c" font-size="10">✓ supplierId</text>

  <text x="350" y="178" text-anchor="middle" fill="#8b949e" font-size="10">Admin extends Seller extends Customer — each view is a superset of its parent</text>
</svg>

---

## 6. Walkthrough

**Per-request: `GET /products/1` with `X-Role: SELLER`:**

1. Handler `get(1, "SELLER")` executes.
2. `switch("SELLER")` → `ProductViews.Seller.class`.
3. `MappingJacksonValue wrapper` wraps `product` with view `Seller`.
4. `MappingJacksonValue2HttpMessageConverter` (return value handler) detects `MappingJacksonValue`.
5. Calls `objectMapper.writerWithView(ProductViews.Seller.class).writeValue(stream, product)`.
6. For each field:
   - `id`: `@JsonView(Customer)` — `Customer` is parent of `Seller` → **included**.
   - `salePrice`: `@JsonView(Customer)` → **included**.
   - `stock`: `@JsonView(Seller)` — same as active view → **included**.
   - `costPrice`: `@JsonView(Admin)` — `Admin` is a child of `Seller`, not a parent → **excluded**.
   - `supplierId`: `@JsonView(Admin)` → **excluded**.
7. Response: `{"id":1,"name":"Drill","salePrice":49.99,"stock":25}`.

---

## 7. Gotchas & takeaways

> **Fields without `@JsonView` are excluded when any view is active.** Jackson's default: if `defaultViewInclusion = false` (default), unannotated fields are invisible when a view is active. If you want unannotated fields to always appear, set `objectMapper.disable(MapperFeature.DEFAULT_VIEW_INCLUSION)` to false.

> **`@JsonView` on handler method applies to the serialized return value only, not to nested objects unless they are also annotated.** Nested `@JsonView` annotations on related entities must be added to those classes separately.

> **`@JsonView` on `@RequestBody` works in Spring MVC but requires the annotation on the parameter, not the method.** `@RequestBody @JsonView(MyView.class) Product product` — the `@JsonView` here controls *deserialization*.

- View hierarchy: child view includes parent view's fields automatically (`extends`).
- `MappingJacksonValue` wraps return value with runtime view — enables dynamic role-based field selection.
- Fields without `@JsonView` excluded by default when a view is active — annotate all fields you want to include.
- `@JsonView` on `@RequestBody` parameter ignores fields outside the view during deserialization.
- Avoid deeply nested view hierarchies — 3 levels (public/seller/admin) is the practical maximum before readability suffers.
