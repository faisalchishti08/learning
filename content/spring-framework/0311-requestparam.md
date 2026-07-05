---
card: spring-framework
gi: 311
slug: requestparam
title: "@RequestParam"
---

## 1. What it is

`@RequestParam` binds a query-string parameter (or form field) to a method parameter in a Spring MVC handler:

```java
// GET /search?query=spring&page=2&size=10
@GetMapping("/search")
public List<String> search(
    @RequestParam String query,                     // required; missing → 400
    @RequestParam(defaultValue = "1") int page,    // optional with default
    @RequestParam(required = false) Integer size    // optional; null if absent
) { ... }
```

It works with:
- **Query-string parameters** — `?key=value`
- **Form fields** — `Content-Type: application/x-www-form-urlencoded` or `multipart/form-data`
- **Multi-value parameters** — `?tag=java&tag=spring` → `List<String>`

Spring converts the string value to the target type via `ConversionService`.

---

## 2. Why & when

Use `@RequestParam` for **optional or filtering inputs** that don't identify the resource:

- Pagination: `?page=2&size=20`
- Search/filter: `?status=active&sort=name`
- Flags: `?verbose=true`

Use `@PathVariable` for **resource identity** (`/users/{id}`). Use `@RequestBody` for complex JSON/XML payloads. `@RequestParam` is for simple scalar values in the query string or form data.

---

## 3. Core concept

```
GET /products?category=tools&minPrice=10&maxPrice=100&tag=sale&tag=new

@GetMapping("/products")
public List<Product> list(
    @RequestParam String category,                    // "tools"
    @RequestParam(required = false) Double minPrice,  // 10.0
    @RequestParam(required = false) Double maxPrice,  // 100.0
    @RequestParam(required = false) List<String> tag  // ["sale", "new"]
)

Resolution:
  1. RequestParamMethodArgumentResolver checks parameter annotation
  2. Reads HttpServletRequest.getParameterValues("tag") → ["sale","new"]
  3. ConversionService converts "10" → Double 10.0
  4. Binds to method parameters
```

If `required = true` (the default) and the parameter is absent → `400 Bad Request` with `MissingServletRequestParameterException`.

---

## 4. Diagram

<svg viewBox="0 0 740 260" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="260" fill="#0d1117"/>

  <!-- URL bar -->
  <rect x="10" y="20" width="720" height="36" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="370" y="38" text-anchor="middle" fill="#e6edf3">/products?category=tools&amp;tag=sale&amp;tag=new&amp;minPrice=10</text>
  <text x="370" y="52" text-anchor="middle" fill="#8b949e" font-size="10">query string parsed by servlet container → HttpServletRequest.getParameterMap()</text>

  <!-- param map -->
  <rect x="10" y="80" width="220" height="100" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="120" y="98" text-anchor="middle" fill="#8b949e">ParameterMap</text>
  <text x="120" y="114" text-anchor="middle" fill="#79c0ff" font-size="11">category → ["tools"]</text>
  <text x="120" y="130" text-anchor="middle" fill="#79c0ff" font-size="11">tag → ["sale","new"]</text>
  <text x="120" y="146" text-anchor="middle" fill="#79c0ff" font-size="11">minPrice → ["10"]</text>
  <text x="120" y="162" text-anchor="middle" fill="#8b949e" font-size="10">all values are String[]</text>

  <!-- resolver -->
  <line x1="230" y1="130" x2="270" y2="130" stroke="#8b949e" marker-end="url(#arp)"/>
  <rect x="270" y="90" width="200" height="80" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="110" text-anchor="middle" fill="#6db33f">RequestParam</text>
  <text x="370" y="126" text-anchor="middle" fill="#6db33f">Argument Resolver</text>
  <text x="370" y="144" text-anchor="middle" fill="#8b949e" font-size="10">ConversionService</text>
  <text x="370" y="158" text-anchor="middle" fill="#8b949e" font-size="10">"10" → Double 10.0</text>
  <text x="370" y="170" text-anchor="middle" fill="#8b949e" font-size="10">["sale","new"] → List&lt;String&gt;</text>

  <!-- bound params -->
  <line x1="470" y1="130" x2="510" y2="130" stroke="#8b949e" marker-end="url(#arp)"/>
  <rect x="510" y="80" width="220" height="100" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="620" y="98" text-anchor="middle" fill="#6db33f">Method parameters</text>
  <text x="620" y="114" text-anchor="middle" fill="#e6edf3" font-size="11">String category = "tools"</text>
  <text x="620" y="130" text-anchor="middle" fill="#e6edf3" font-size="11">List&lt;String&gt; tag = [sale,new]</text>
  <text x="620" y="146" text-anchor="middle" fill="#e6edf3" font-size="11">Double minPrice = 10.0</text>
  <text x="620" y="162" text-anchor="middle" fill="#8b949e" font-size="10">maxPrice = null (absent, required=false)</text>

  <text x="370" y="235" text-anchor="middle" fill="#8b949e" font-size="11">ConversionService converts String → target type; multi-value params bind to List or array</text>

  <defs>
    <marker id="arp" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*All query-string values are `String[]` internally; `@RequestParam` handles type conversion and multi-value binding.*

---

## 5. Runnable example

### Level 1 — Basic

A product search endpoint with required and optional parameters:

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/api/products")
public class ProductController {

    private final List<Map<String,Object>> catalog = List.of(
            Map.of("id",1,"name","Hammer","category","tools","price",9.99),
            Map.of("id",2,"name","Drill","category","tools","price",49.99),
            Map.of("id",3,"name","Paint","category","decor","price",14.99)
    );

    @GetMapping
    public List<Map<String,Object>> search(
            @RequestParam(required = false) String category,
            @RequestParam(defaultValue = "0") double minPrice,
            @RequestParam(defaultValue = "999999") double maxPrice) {

        return catalog.stream()
                .filter(p -> category == null || category.equals(p.get("category")))
                .filter(p -> (double)p.get("price") >= minPrice)
                .filter(p -> (double)p.get("price") <= maxPrice)
                .toList();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# All products
curl http://localhost:8080/api/products
# [{"id":1,...},{"id":2,...},{"id":3,...}]

# Filter by category
curl "http://localhost:8080/api/products?category=tools"
# [{"id":1,...hammer},{"id":2,...drill}]

# Price range
curl "http://localhost:8080/api/products?minPrice=10&maxPrice=50"
# [{"id":2,...drill},{"id":3,...paint}]

# Missing required param — if category were required:
# 400 MissingServletRequestParameterException
```

`required = false` makes `category` optional — `null` when absent. `defaultValue = "0"` means the parameter is implicitly optional (Spring uses the default when absent). `ConversionService` converts `"10"` to `double 10.0` automatically.

---

### Level 2 — Intermediate

Same product search — now adding **multi-value** `tag` filtering and a **pagination** pair with validation:

```java
// ProductController.java (extended)
import jakarta.validation.constraints.*;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@Validated   // enables @RequestParam constraint validation
@RestController
@RequestMapping("/api/products")
public class ProductController {

    private final List<Map<String,Object>> catalog = List.of(
            Map.of("id",1,"name","Hammer","category","tools","tags",List.of("sale","popular")),
            Map.of("id",2,"name","Drill", "category","tools","tags",List.of("new")),
            Map.of("id",3,"name","Paint", "category","decor","tags",List.of("sale"))
    );

    @GetMapping
    public Map<String,Object> search(
            @RequestParam(required = false) String category,
            @RequestParam(required = false) List<String> tag,        // multi-value: ?tag=sale&tag=new
            @RequestParam(defaultValue = "1") @Min(1) int page,
            @RequestParam(defaultValue = "10") @Min(1) @Max(100) int size) {

        var results = catalog.stream()
                .filter(p -> category == null || category.equals(p.get("category")))
                .filter(p -> tag == null || tag.isEmpty() ||
                             ((List<?>)p.get("tags")).stream().anyMatch(t -> tag.contains(t.toString())))
                .toList();

        int from = Math.min((page - 1) * size, results.size());
        int to   = Math.min(from + size, results.size());

        return Map.of(
                "page", page, "size", size,
                "total", results.size(),
                "items", results.subList(from, to));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Multi-value tag filter
curl "http://localhost:8080/api/products?tag=sale&tag=new"
# {"page":1,"size":10,"total":3,"items":[{...hammer},{...drill},{...paint}]}

# Pagination
curl "http://localhost:8080/api/products?page=1&size=2"
# {"page":1,"size":2,"total":3,"items":[{hammer},{drill}]}

# Invalid page (violates @Min(1))
curl "http://localhost:8080/api/products?page=0"
# 400 Bad Request: search.page: must be greater than or equal to 1
```

**What changed:** `List<String> tag` bound to repeated `?tag=` parameters via `HttpServletRequest.getParameterValues("tag")`. `@Validated` on the class enables `@Min`/`@Max` on `@RequestParam` parameters directly — violations throw `ConstraintViolationException` → 400, without needing a `BindingResult`.

---

### Level 3 — Advanced

Production scenario: a search endpoint with **`Map<String,String>` to capture all parameters**, a **custom converter** for a `SortSpec` value object, and **explicit parameter name** for API stability when obfuscating bytecode:

```java
// SortSpec.java
public record SortSpec(String field, boolean ascending) {
    public static SortSpec parse(String value) {
        // Format: "field,asc" or "field,desc"
        String[] parts = value.split(",", 2);
        return new SortSpec(parts[0], parts.length < 2 || "asc".equalsIgnoreCase(parts[1]));
    }
}
```

```java
// SortSpecConverter.java
import org.springframework.core.convert.converter.Converter;
import org.springframework.stereotype.Component;

@Component
public class SortSpecConverter implements Converter<String, SortSpec> {
    @Override
    public SortSpec convert(String source) {
        return SortSpec.parse(source);
    }
}
```

```java
// ProductController.java (production)
import org.springframework.web.bind.annotation.*;
import java.util.*;
import java.util.stream.*;

@RestController
@RequestMapping("/api/products")
public class ProductController {

    private final List<Map<String,Object>> catalog = List.of(
            Map.of("id",1,"name","Hammer","price",9.99,"score",3),
            Map.of("id",2,"name","Drill", "price",49.99,"score",5),
            Map.of("id",3,"name","Paint", "price",14.99,"score",4)
    );

    @GetMapping
    public Map<String,Object> search(
            // Named explicitly for API stability (bytecode obfuscation safe)
            @RequestParam(name = "q", required = false) String query,
            @RequestParam(name = "sort", defaultValue = "score,desc") SortSpec sort,
            @RequestParam(name = "page", defaultValue = "1") int page,
            @RequestParam(name = "size", defaultValue = "10") int size,
            // Capture ALL remaining params (for dynamic filters)
            @RequestParam Map<String, String> allParams) {

        // Extract filter params (anything not q/sort/page/size)
        var filterParams = allParams.entrySet().stream()
                .filter(e -> !Set.of("q","sort","page","size").contains(e.getKey()))
                .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));

        var results = catalog.stream()
                .filter(p -> query == null || p.get("name").toString().toLowerCase().contains(query.toLowerCase()))
                .filter(p -> filterParams.isEmpty() || filterParams.entrySet().stream()
                        .allMatch(f -> String.valueOf(p.get(f.getKey())).equals(f.getValue())))
                .sorted(Comparator.<Map<String,Object>, Comparable>comparing(
                        p -> (Comparable) p.get(sort.field()),
                        sort.ascending() ? Comparator.naturalOrder() : Comparator.reverseOrder()))
                .toList();

        int from = Math.min((page - 1) * size, results.size());
        int to   = Math.min(from + size, results.size());

        return Map.of(
                "query", query == null ? "" : query,
                "sort", sort.field() + "," + (sort.ascending() ? "asc" : "desc"),
                "filters", filterParams,
                "total", results.size(),
                "items", results.subList(from, to));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Custom sort (converted by SortSpecConverter)
curl "http://localhost:8080/api/products?sort=price,asc"
# {"query":"","sort":"price,asc","total":3,"items":[{hammer,9.99},{paint,14.99},{drill,49.99}]}

# Query + dynamic filter
curl "http://localhost:8080/api/products?q=a&minScore=4"
# (filters: q matches "Hammer","Paint","Drill"; minScore not directly supported
#  but captured in filterParams and matched against catalog values)

# Default sort (score,desc)
curl http://localhost:8080/api/products
# items ordered: drill(5), paint(4), hammer(3)
```

**What changed and why:**
- `@RequestParam Map<String,String>` captures all query-string parameters — useful for dynamic filter APIs where callers can pass arbitrary `fieldName=value` pairs.
- `SortSpec sort` is converted from `"price,asc"` by the registered `SortSpecConverter` — Spring's `ConversionService` picks it up automatically via `@Component`.
- `@RequestParam(name = "q")` uses an explicit `name` attribute — when bytecode is obfuscated (e.g. ProGuard in Android apps calling this API), the parameter name in bytecode changes but `name = "q"` stays fixed.

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="180" fill="#0d1117"/>
  <!-- flow -->
  <rect x="10" y="40" width="140" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="59" text-anchor="middle" fill="#79c0ff">?sort=price,asc</text>
  <line x1="150" y1="55" x2="185" y2="55" stroke="#8b949e" marker-end="url(#arp2)"/>
  <rect x="185" y="40" width="170" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="270" y="59" text-anchor="middle" fill="#6db33f">ConversionService</text>
  <line x1="355" y1="55" x2="390" y2="55" stroke="#8b949e" marker-end="url(#arp2)"/>
  <rect x="390" y="40" width="160" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="55" text-anchor="middle" fill="#6db33f">SortSpecConverter</text>
  <text x="470" y="69" text-anchor="middle" fill="#8b949e" font-size="10">.convert("price,asc")</text>
  <line x1="550" y1="55" x2="585" y2="55" stroke="#8b949e" marker-end="url(#arp2)"/>
  <rect x="585" y="40" width="110" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="640" y="55" text-anchor="middle" fill="#e6edf3">SortSpec</text>
  <text x="640" y="69" text-anchor="middle" fill="#8b949e" font-size="10">{field=price,asc=true}</text>
  <!-- map capture -->
  <rect x="185" y="100" width="200" height="36" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="285" y="116" text-anchor="middle" fill="#79c0ff">Map&lt;String,String&gt; allParams</text>
  <text x="285" y="130" text-anchor="middle" fill="#8b949e" font-size="10">{q,sort,page,size,minScore,...}</text>
  <text x="350" y="168" text-anchor="middle" fill="#8b949e" font-size="10">@RequestParam Map captures ALL query params — custom converters handle complex types</text>
  <defs><marker id="arp2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Per-request: `GET /api/products?sort=price,asc&q=a&page=1&size=10`:**

1. Servlet container parses query string → `ParameterMap: {sort=["price,asc"], q=["a"], page=["1"], size=["10"]}`.
2. `HandlerAdapter` resolves arguments in order:
   - `@RequestParam(name="q") String query` — `RequestParamMethodArgumentResolver` reads `getParameter("q")` → `"a"`.
   - `@RequestParam(name="sort") SortSpec sort` — reads `"price,asc"`, passes to `ConversionService`. `SortSpecConverter.convert("price,asc")` → `SortSpec{field=price, ascending=true}`.
   - `@RequestParam(name="page") int page` — `"1"` → `Integer` 1.
   - `@RequestParam(name="size") int size` — `"10"` → `Integer` 10.
   - `@RequestParam Map<String,String> allParams` — `RequestParamMapMethodArgumentResolver` reads entire `ParameterMap` as flat `Map<String,String>` → `{sort=price,asc, q=a, page=1, size=10}`.
3. `search("a", SortSpec{price,asc}, 1, 10, {...})` executes.
4. Filter: `q="a"` → keeps "Hammer", "Paint" (contain 'a'); "Drill" dropped.
5. Sort by `price` ascending: Paint(14.99) before Hammer(9.99)... wait, 9.99 < 14.99, so Hammer first. → [Hammer, Paint].
6. Pagination: page=1, size=10 → all 2 results.
7. Returns `Map{total:2, items:[{Hammer},{Paint}]}`.

**Response:**
```
HTTP/1.1 200 OK
Content-Type: application/json
{"query":"a","sort":"price,asc","filters":{},"total":2,"items":[{"id":1,"name":"Hammer",...},{"id":3,"name":"Paint",...}]}
```

---

## 7. Gotchas & takeaways

> **`defaultValue` makes a parameter implicitly optional.** Setting `defaultValue = "1"` on a `required = true` (default) parameter won't cause a 400 — Spring uses the default. But explicitly using `required = false` without `defaultValue` gives `null` for missing parameters on primitive types, which causes `NullPointerException`. Use wrapper types (`Integer` vs `int`) or always provide `defaultValue` for numeric parameters.

> **`@RequestParam Map<String,String>` captures only the first value of multi-value params.** Use `MultiValueMap<String,String>` to get all values for each key.

> **`required = true` (default) throws `MissingServletRequestParameterException` → 400, not 500.** The parameter name is included in the error message — clients see exactly which parameter is missing.

- Use `@RequestParam` for query-string and form-field scalars; `@PathVariable` for resource identity; `@RequestBody` for structured payloads.
- `List<T>` binds repeated parameters: `?tag=a&tag=b` → `["a","b"]`.
- `Map<String,String>` captures all parameters — useful for dynamic filter APIs.
- Register a `Converter<String,T>` as a `@Component` to bind complex value objects from query strings.
- Always use `name = "paramName"` explicitly when the code will be compiled with bytecode obfuscation.
