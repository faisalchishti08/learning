---
card: spring-framework
gi: 326
slug: model-modelmap
title: "Model & ModelMap"
---

## 1. What it is

`Model` and `ModelMap` are handler-method parameter types Spring MVC injects into controller methods so you can add attributes that a view (Thymeleaf, JSP, Freemarker) will render. Both are essentially a name-to-object map that gets merged into the view's rendering context — `Model` is an interface, `ModelMap` is a concrete `LinkedHashMap`-backed implementation. Spring supplies an instance automatically; you never construct one yourself.

```java
@GetMapping("/products/{id}")
public String productPage(@PathVariable long id, Model model) {
    model.addAttribute("product", productService.find(id));
    model.addAttribute("relatedCount", 5);
    return "product-detail";          // view name; model attributes available in the template
}
```

## 2. Why & when

Use `Model`/`ModelMap` when a controller method returns a **view name** (server-side rendered HTML) rather than a `@ResponseBody`/`ResponseEntity`. They are the bridge between your Java data and the template engine — without them, the view has nothing to render beyond static markup.

They matter specifically for:
- Traditional MVC apps (Thymeleaf, JSP) where the server renders HTML.
- Passing computed values, lists, or form-backing objects to a template.
- Adding cross-cutting attributes (e.g. current user, flash messages) that multiple views need — often via `@ModelAttribute`-annotated methods that run before every handler in a controller.

For pure REST APIs returning JSON/XML (`@RestController`, `@ResponseBody`), `Model` is irrelevant — the return value itself becomes the response body, and there is no view to populate.

## 3. Core concept

```
Model / ModelMap: name -> Object map

Controller method:
  model.addAttribute("product", productObj)
  model.addAttribute("user", currentUser)

        |
        v
  Spring merges Model attributes + any @ModelAttribute-annotated
  methods' return values into one map

        |
        v
  ViewResolver resolves "product-detail" -> product-detail.html

        |
        v
  Template engine renders, reading attributes by name:
    Thymeleaf: <span th:text="${product.name}"></span>
    JSP:       <c:out value="${product.name}"/>

Model (interface)  <---- implemented by ---- ModelMap (LinkedHashMap subclass)
                                              |
                                    ModelAndView also wraps a ModelMap
                                    internally when you use that return type
```

`Model` is generally preferred in method signatures because it's an interface (looser coupling); `ModelMap` exposes extra `Map`-style methods (`addAllAttributes`, `mergeAttributes`) that are occasionally handy but rarely required.

## 4. Diagram

<svg viewBox="0 0 720 240" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="240" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Controller → Model → View rendering</text>

  <rect x="20" y="50" width="180" height="70" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="72" text-anchor="middle" fill="#6db33f">Controller method</text>
  <text x="110" y="90" text-anchor="middle" fill="#8b949e" font-size="10">model.addAttribute(</text>
  <text x="110" y="104" text-anchor="middle" fill="#8b949e" font-size="10">  "product", p)</text>

  <line x1="200" y1="85" x2="260" y2="85" stroke="#8b949e" marker-end="url(#a2)"/>

  <rect x="260" y="50" width="180" height="70" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="350" y="72" text-anchor="middle" fill="#79c0ff">Model / ModelMap</text>
  <text x="350" y="90" text-anchor="middle" fill="#e6edf3" font-size="10">{"product": Product,</text>
  <text x="350" y="104" text-anchor="middle" fill="#e6edf3" font-size="10">"relatedCount": 5}</text>

  <line x1="440" y1="85" x2="500" y2="85" stroke="#8b949e" marker-end="url(#a2)"/>

  <rect x="500" y="50" width="200" height="70" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="600" y="72" text-anchor="middle" fill="#8b949e">ViewResolver</text>
  <text x="600" y="90" text-anchor="middle" fill="#8b949e" font-size="10">"product-detail"</text>
  <text x="600" y="104" text-anchor="middle" fill="#8b949e" font-size="10">-> product-detail.html</text>

  <line x1="600" y1="120" x2="350" y2="160" stroke="#8b949e" marker-end="url(#a2)"/>
  <rect x="180" y="160" width="340" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="182" text-anchor="middle" fill="#e6edf3" font-size="11">&lt;span th:text="${product.name}"&gt;&lt;/span&gt;</text>
  <text x="350" y="200" text-anchor="middle" fill="#8b949e" font-size="10">rendered HTML sent to browser</text>

  <defs>
    <marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Attributes added to `Model` are looked up by name in the resolved template during rendering.*

## 5. Runnable example

### Level 1 — Basic

A product detail page populated from `Model`:

```java
// ProductController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

@Controller
public class ProductController {

    record Product(long id, String name, double price) {}

    @GetMapping("/products/{id}")
    public String detail(@PathVariable long id, Model model) {
        Product product = new Product(id, "Drill", 29.99);
        model.addAttribute("product", product);
        return "product-detail";     // resolves to templates/product-detail.html
    }
}
```

`src/main/resources/templates/product-detail.html` (Thymeleaf):
```html
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
<body>
  <h1 th:text="${product.name}">Name</h1>
  <p th:text="${'$' + product.price}">Price</p>
</body>
</html>
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# <html>...<h1>Drill</h1><p>$29.99</p>...</html>
```

Spring instantiates the `Model` before invoking `detail()`. Whatever you add to it is available in the template by the same attribute name.

### Level 2 — Intermediate

Add related data and a shared attribute (current user) supplied via `@ModelAttribute`, plus a computed value:

```java
// ProductController.java (extended)
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.ui.ModelMap;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Controller
public class ProductController {

    record Product(long id, String name, double price) {}
    record User(String username) {}

    // Runs before EVERY handler in this controller, adds shared attribute
    @ModelAttribute("currentUser")
    public User currentUser() {
        return new User("faisal");     // in real code, pulled from security context
    }

    @GetMapping("/products/{id}")
    public String detail(@PathVariable long id, Model model) {
        Product product = new Product(id, "Drill", 29.99);
        List<Product> related = List.of(new Product(2, "Hammer", 14.99));

        model.addAttribute("product", product);
        model.addAttribute("related", related);
        model.addAttribute("relatedCount", related.size());
        return "product-detail";
    }

    @GetMapping("/products/{id}/summary")
    public String summary(@PathVariable long id, ModelMap modelMap) {
        modelMap.addAttribute("productId", id);
        modelMap.mergeAttributes(java.util.Map.of("compact", true));
        return "product-summary";
    }
}
```

`product-detail.html` (updated):
```html
<h1 th:text="${product.name}">Name</h1>
<p>Logged in as <span th:text="${currentUser.username}">user</span></p>
<p th:text="${relatedCount} + ' related items'">count</p>
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# HTML includes "Logged in as faisal" and "1 related items"
```

**What changed:** `@ModelAttribute("currentUser")` runs before *every* handler method in the controller, so `currentUser` is available in every view this controller renders without repeating `model.addAttribute` each time. `ModelMap.mergeAttributes` bulk-adds a `Map` of attributes in one call — useful when combining data from multiple sources.

### Level 3 — Advanced

Production concern: avoid leaking sensitive data into the model, handle a missing product gracefully, and separate a reusable `@ControllerAdvice`-based global model attribute (e.g. site-wide navigation data) from per-request data:

```java
// GlobalModelAdvice.java — shared across ALL controllers, not just one
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ModelAttribute;

@ControllerAdvice
public class GlobalModelAdvice {

    @ModelAttribute
    public void addGlobalAttributes(Model model) {
        model.addAttribute("siteName", "Acme Tools");
        model.addAttribute("currentYear", java.time.Year.now().getValue());
    }
}
```

```java
// ProductController.java (production version)
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.util.Optional;

@Controller
public class ProductController {

    record Product(long id, String name, double price) {}

    private final ProductRepository repository;   // injected in real code

    public ProductController(ProductRepository repository) {
        this.repository = repository;
    }

    @GetMapping("/products/{id}")
    public String detail(@PathVariable long id, Model model) {
        Optional<Product> product = repository.findById(id);

        if (product.isEmpty()) {
            model.addAttribute("errorMessage", "Product " + id + " not found");
            return "error-404";                  // separate error view, no product data
        }

        model.addAttribute("product", product.get());
        // Deliberately NOT adding internal fields like cost price or supplier — model
        // attributes are rendering data, not a dumping ground for the whole entity.
        return "product-detail";
    }

    interface ProductRepository {
        Optional<Product> findById(long id);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/1
# renders product-detail.html with siteName, currentYear (from GlobalModelAdvice)
# and product (from this handler)

curl http://localhost:8080/products/999
# renders error-404.html with errorMessage — no "product" attribute present,
# so the template must not assume product always exists
```

**What changed and why:**
- `@ControllerAdvice` + `@ModelAttribute` centralizes attributes needed by *every* page (site name, year for a footer copyright) so individual controllers don't repeat boilerplate.
- The handler explicitly picks which fields go into the model instead of dumping a whole entity — this avoids accidentally exposing internal-only data (e.g. supplier cost) to a template that a designer might carelessly render.
- Missing-data is handled by branching to a different view name with a different, smaller model — the template for `product-detail` never has to defensively null-check `product`.

## 6. Walkthrough

**Request: `GET /products/1` (Level 3 code, product exists).**

1. `DispatcherServlet` matches the request to `ProductController.detail(1, model)`. Before invoking it, Spring first invokes any `@ModelAttribute`-annotated methods that apply — including `GlobalModelAdvice.addGlobalAttributes`, because `@ControllerAdvice` applies globally.
2. `addGlobalAttributes(model)` runs, adding `siteName = "Acme Tools"` and `currentYear = 2026` to the shared `Model` instance.
3. Spring then invokes `detail(1, model)` with the *same* `Model` instance (attributes accumulate, they don't reset per method).
4. Inside `detail`, `repository.findById(1)` returns `Optional.of(Product(1, "Drill", 29.99))`.
5. `model.addAttribute("product", product.get())` adds the product. The `Model` now holds: `{siteName, currentYear, product}`.
6. Handler returns the string `"product-detail"` — Spring treats this as a **view name**, not a response body (because the class is `@Controller`, not `@RestController`).
7. `ViewResolver` (Thymeleaf's, configured by Spring Boot autoconfiguration) resolves `"product-detail"` to `templates/product-detail.html`.
8. The template engine renders the HTML, substituting `${product.name}` → `"Drill"`, `${siteName}` → `"Acme Tools"`, etc.
9. Final HTML is written to the `HttpServletResponse` body:
   ```
   HTTP/1.1 200 OK
   Content-Type: text/html;charset=UTF-8

   <html>...<h1>Drill</h1>...<footer>Acme Tools 2026</footer>...</html>
   ```

**Request: `GET /products/999` (product missing).** Steps 1–3 identical. At step 4, `findById(999)` returns `Optional.empty()`. The handler adds `errorMessage` instead of `product` and returns `"error-404"`. A different template renders — one that never references `${product}` — avoiding a template-rendering exception from a null reference.

## 7. Gotchas & takeaways

> **`Model` attributes are per-request, not shared across requests.** Spring creates a fresh `Model` for every incoming request; there is no cross-request state here. Don't confuse it with `HttpSession` — if you need data to persist between requests, use the session or a database, not the model.

> **Attribute names must match exactly what the template expects**, and there's no compile-time checking. A typo like `model.addAttribute("prduct", p)` compiles fine but silently renders nothing (or throws at render time if the template does a strict property access) — always double-check the attribute name string against the template.

> **`@ModelAttribute`-annotated methods on a controller run before every `@RequestMapping` handler in that controller**, even ones that don't need the extra data — this can add unnecessary work (e.g. a database call) to every request. Move truly global attributes to a `@ControllerAdvice` and keep per-controller `@ModelAttribute` methods lean.

- `Model` is an interface; `ModelMap` is the concrete `LinkedHashMap`-based implementation — prefer `Model` in method signatures for looser coupling.
- Attributes are only meaningful when the handler returns a view name (or `ModelAndView`) — irrelevant for `@ResponseBody`/`@RestController` methods.
- `@ControllerAdvice` + `@ModelAttribute` is the standard way to inject data needed by many/all views (navigation, current user, site metadata).
- Only add what the view actually needs — treat the model as a rendering contract, not a full entity dump.
