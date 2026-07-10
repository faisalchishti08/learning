---
card: spring-framework
gi: 332
slug: restcontroller
title: "@RestController"
---

## 1. What it is

`@RestController` is a class-level annotation that combines `@Controller` and `@ResponseBody`. It marks a class as a Spring MVC controller where **every** handler method's return value is written directly to the HTTP response body (typically serialized to JSON via Jackson), rather than being resolved as a view name to render.

```java
@RestController
public class ProductController {

    @GetMapping("/products/{id}")
    public Product get(@PathVariable long id) {
        return repository.findById(id);   // serialized straight to JSON, no view involved
    }
}
```

## 2. Why & when

Plain `@Controller` methods return a `String` or `ModelAndView` that Spring resolves to a template (Thymeleaf, JSP) to render HTML — the return value is a *view name*, not the response content. That's correct for server-rendered pages but wrong for APIs, where you want the return value to *be* the response.

Before `@RestController` existed (Spring 4.0+), you had to write `@Controller` plus `@ResponseBody` on every single method — tedious and easy to forget on one method, causing a confusing `Circular view path` error where Spring tries to resolve your JSON data as a template name.

Use `@RestController` when:
- Building a REST/JSON API — every method returns data, never a view name.
- You want to skip repeating `@ResponseBody` on each handler.

Use plain `@Controller` (with method-level `@ResponseBody` only where needed) when a controller is mostly rendering server-side views but occasionally needs one JSON endpoint (e.g. an AJAX autocomplete call within an otherwise HTML-rendering controller) — mixing the two in one `@RestController` class isn't possible since `@ResponseBody` applies to everything.

## 3. Core concept

```
@Controller (no @ResponseBody):
  method returns "product-detail"
       |
       v
  treated as a VIEW NAME
       |
       v
  ViewResolver -> templates/product-detail.html -> rendered HTML response

@RestController (= @Controller + @ResponseBody):
  method returns Product{id=1, name="Drill"}
       |
       v
  treated as RESPONSE BODY DATA
       |
       v
  HttpMessageConverter (Jackson) -> JSON -> written directly to response

@Controller + method-level @ResponseBody (equivalent, for ONE method):
  @ResponseBody
  @GetMapping("/api/search")
  public List<String> search(...) { ... }   // this ONE method returns JSON
                                             // other methods in the SAME class can still return view names
```

## 4. Diagram

<svg viewBox="0 0 720 230" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="230" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">@Controller vs @RestController return-value handling</text>

  <rect x="20" y="50" width="320" height="70" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="180" y="72" text-anchor="middle" fill="#79c0ff">@Controller</text>
  <text x="180" y="90" text-anchor="middle" fill="#8b949e" font-size="10">return "product-detail"</text>
  <text x="180" y="106" text-anchor="middle" fill="#8b949e" font-size="10">-> resolved as VIEW NAME</text>

  <rect x="380" y="50" width="320" height="70" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="540" y="72" text-anchor="middle" fill="#6db33f">@RestController</text>
  <text x="540" y="90" text-anchor="middle" fill="#8b949e" font-size="10">return product object</text>
  <text x="540" y="106" text-anchor="middle" fill="#8b949e" font-size="10">-> written as RESPONSE BODY</text>

  <line x1="180" y1="120" x2="180" y2="160" stroke="#79c0ff" marker-end="url(#a8)"/>
  <line x1="540" y1="120" x2="540" y2="160" stroke="#6db33f" marker-end="url(#a8)"/>

  <rect x="40" y="160" width="280" height="45" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="180" y="187" text-anchor="middle" fill="#e6edf3" font-size="10">Content-Type: text/html — rendered page</text>

  <rect x="400" y="160" width="280" height="45" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="540" y="187" text-anchor="middle" fill="#e6edf3" font-size="10">Content-Type: application/json — {"id":1,...}</text>

  <defs>
    <marker id="a8" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The exact same return-value type is interpreted completely differently depending on whether `@ResponseBody` (directly or via `@RestController`) is present.*

## 5. Runnable example

### Level 1 — Basic

A minimal JSON API controller:

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    record Product(long id, String name, double price) {}

    @GetMapping("/products/{id}")
    public Product get(@PathVariable long id) {
        return new Product(id, "Drill", 29.99);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/1
# HTTP/1.1 200 OK
# Content-Type: application/json
# {"id":1,"name":"Drill","price":29.99}
```

No template file exists anywhere in the project, and none is needed — `@RestController` means the returned `Product` record is serialized directly to JSON by Jackson (auto-configured by Spring Boot) and written as the response body.

### Level 2 — Intermediate

Demonstrating the contrast directly: a `@Controller` (HTML) alongside a `@RestController` (JSON) in the same application, plus the "forgot `@ResponseBody`" mistake made visible:

```java
// PageController.java — renders HTML views
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class PageController {

    @GetMapping("/pages/products/{id}")
    public String productPage(@PathVariable long id, Model model) {
        model.addAttribute("productName", "Drill");
        return "product-detail";        // view name -> templates/product-detail.html
    }

    // MISTAKE: forgot @ResponseBody — Spring will try to resolve this STRING as a view name,
    // fail to find a template called "Drill", and throw an error instead of returning JSON text.
    @GetMapping("/pages/products/{id}/name-broken")
    public String nameBroken(@PathVariable long id) {
        return "Drill";                 // NOT rendered as text — treated as a view name!
    }
}
```

```java
// ProductApiController.java — REST API, correctly annotated
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductApiController {

    record Product(long id, String name) {}

    @GetMapping("/api/products/{id}")
    public Product get(@PathVariable long id) {
        return new Product(id, "Drill");   // written directly as JSON
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/pages/products/1
# <html>...Drill...</html>          (rendered template)

curl -i http://localhost:8080/pages/products/1/name-broken
# HTTP/1.1 500 Internal Server Error
# (Spring tried to find a view named "Drill" and failed — classic missing-@ResponseBody bug)

curl -i http://localhost:8080/api/products/1
# HTTP/1.1 200 OK
# Content-Type: application/json
# {"id":1,"name":"Drill"}
```

**What changed:** `nameBroken` demonstrates the exact mistake `@RestController` exists to prevent — returning a plain `String` from a `@Controller` method is *always* interpreted as a view name, never as literal response text, unless `@ResponseBody` is present. `ProductApiController`, being a `@RestController`, has no such ambiguity: every return value is body content.

### Level 3 — Advanced

Production pattern: a `@RestController` combined with `ResponseEntity` for full control over status/headers, content negotiation producing both JSON and a custom media type, and a mixed-purpose controller correctly separated instead of forced into one class:

```java
// ProductApiController.java (production version)
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/products")
public class ProductApiController {

    record Product(long id, String name, double price) {}

    @GetMapping(value = "/{id}", produces = {MediaType.APPLICATION_JSON_VALUE, "application/vnd.acme.product+json"})
    public ResponseEntity<Product> get(@PathVariable long id) {
        Product product = new Product(id, "Drill", 29.99);
        return ResponseEntity.ok()
                .eTag("\"v1-" + id + "\"")
                .cacheControl(CacheControl.maxAge(java.time.Duration.ofMinutes(5)))
                .body(product);
    }

    @PostMapping
    public ResponseEntity<Product> create(@RequestBody Product request) {
        Product created = new Product(42, request.name(), request.price());
        return ResponseEntity
                .created(java.net.URI.create("/api/products/42"))
                .body(created);
    }
}
```

```java
// ProductPageController.java — deliberately a SEPARATE class from the API controller
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
@org.springframework.web.bind.annotation.RequestMapping("/products")
public class ProductPageController {

    @GetMapping("/{id}")
    public String detail(@PathVariable long id, Model model) {
        model.addAttribute("productId", id);
        model.addAttribute("productName", "Drill");
        return "product-detail";        // server-rendered HTML page for browsers
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/api/products/1
# HTTP/1.1 200 OK
# ETag: "v1-1"
# Cache-Control: max-age=300
# Content-Type: application/json
# {"id":1,"name":"Drill","price":29.99}

curl -i -X POST http://localhost:8080/api/products -H "Content-Type: application/json" -d '{"name":"Hammer","price":14.99}'
# HTTP/1.1 201 Created
# Location: /api/products/42
# {"id":42,"name":"Hammer","price":14.99}

curl http://localhost:8080/products/1
# <html>...Drill...</html>          (separate, HTML-rendering controller)
```

**What changed and why:**
- `ResponseEntity<Product>` combined with `@RestController` gives full control over status code, headers (`ETag`, `Cache-Control`, `Location`), while still benefiting from automatic JSON serialization of the body — `@RestController` and `ResponseEntity` are complementary, not exclusive.
- The API controller and the page-rendering controller are kept as **separate classes** rather than mixed in one — because `@RestController`'s `@ResponseBody` behavior applies to *every* method in the class, there is no way to have some methods return views and others return bodies within a single `@RestController`. Splitting by responsibility (API vs. page) avoids fighting that constraint.
- `produces` lists both a generic JSON type and a custom vendor media type, letting the same JSON-shaped data serve both a generic REST client and a client that specifically negotiates the vendor type — content negotiation still fully applies under `@RestController`.

## 6. Walkthrough

**Request: `GET /api/products/1` (Level 3 `ProductApiController`).**

1. `DispatcherServlet` matches the request to `ProductApiController.get(1)`.
2. Because the class is `@RestController`, Spring knows in advance that whatever this method returns will go through `@ResponseBody` handling — no view resolution will be attempted, regardless of the return type.
3. The method builds `Product{1, "Drill", 29.99}` and wraps it in a `ResponseEntity` with a `200` status, an `ETag` header, and a `Cache-Control` header, then calls `.body(product)`.
4. Spring's `RequestResponseBodyMethodProcessor` (the component that handles `@ResponseBody`-style return values) unwraps the `ResponseEntity`: takes its status and headers for the raw HTTP response, and hands the `Product` body object to content negotiation.
5. Content negotiation inspects the `Accept` header of the request (or defaults to `*/*`) against the method's declared `produces` list (`application/json`, `application/vnd.acme.product+json`) and picks a matching `HttpMessageConverter` — here, Jackson's `MappingJackson2HttpMessageConverter`.
6. Jackson serializes the `Product` record's fields (`id`, `name`, `price`) to a JSON object.
7. The final response is assembled and sent:
   ```
   HTTP/1.1 200 OK
   ETag: "v1-1"
   Cache-Control: max-age=300
   Content-Type: application/json

   {"id":1,"name":"Drill","price":29.99}
   ```

**Contrast — request: `GET /products/1` (Level 3 `ProductPageController`, plain `@Controller`).**

1. `DispatcherServlet` matches `ProductPageController.detail(1, model)`. This class has no `@ResponseBody`.
2. `model.addAttribute(...)` populates the shared `Model` with `productId` and `productName`.
3. The method returns the `String` `"product-detail"`. Because there's no `@ResponseBody` in scope, Spring interprets this string as a **view name**, not literal text.
4. `ViewResolver` maps `"product-detail"` to `templates/product-detail.html`. The template engine renders it, substituting the model attributes.
5. The rendered HTML (not the string `"product-detail"` itself) becomes the response body:
   ```
   HTTP/1.1 200 OK
   Content-Type: text/html;charset=UTF-8

   <html>...<h1>Drill</h1>...</html>
   ```

The two flows diverge entirely at step 3/4 in each — same framework, same `DispatcherServlet`, but a completely different interpretation of the method's return value based solely on the presence of `@ResponseBody` (directly or via `@RestController`).

## 7. Gotchas & takeaways

> **Returning a `String` from a `@Controller` method without `@ResponseBody` is always treated as a view name, never as literal text.** This is the single most common source of confusion for developers moving from writing plain-text/JSON APIs to Spring MVC — a method that "obviously" should return the string `"OK"` as the body instead throws a `Circular view path` or "template not found" error.

> **You cannot mix view-returning and body-returning methods within one `@RestController` class.** `@ResponseBody` applies at the class level uniformly. If a controller genuinely needs both behaviors, split it into two classes (as in the Level 3 example) or use plain `@Controller` with method-level `@ResponseBody` only where JSON output is needed.

> **`@RestController` does not prevent you from returning `ResponseEntity`** — the two work together, and using `ResponseEntity` is the correct way to control status codes and headers explicitly, rather than fighting the framework with `@ResponseStatus` for anything beyond a fixed, simple status.

- `@RestController` = `@Controller` + `@ResponseBody`, applied to every method in the class.
- Use `@RestController` for REST/JSON APIs; use `@Controller` for server-rendered HTML views.
- A controller needing both behaviors should be split into two classes rather than mixed.
- `ResponseEntity<T>` remains fully compatible with `@RestController` for fine-grained control over status and headers.
