---
card: spring-framework
gi: 303
slug: controller
title: "@Controller"
---

## 1. What it is

`@Controller` is a Spring stereotype annotation that marks a class as a **web controller** — the component responsible for handling HTTP requests, building a model, and returning a view name (or writing a response body directly).

```java
@Controller          // marks this as a web controller bean
public class HomeController {
    @GetMapping("/")
    public String home(Model model) {
        model.addAttribute("message", "Hello");
        return "home"; // logical view name → resolved to home.html
    }
}
```

Key facts:

- `@Controller` is a specialisation of `@Component` — Spring picks it up during component scan.
- It does **not** add `@ResponseBody` to methods automatically; returned `String`s are view names, not response bodies.
- `@RestController` = `@Controller` + `@ResponseBody` on every method — use it for JSON/XML APIs.
- A controller class can mix view-returning methods and body-writing methods (the latter annotated with `@ResponseBody`).

---

## 2. Why & when

Use `@Controller` when:

- The handler must return an **HTML view** (Thymeleaf, JSP, FreeMarker).
- Some methods return views and others return JSON (mixed controller).

Use `@RestController` when all methods return serialised data (pure REST API).  `@Controller` stays the right choice for traditional server-side-rendered applications and for MVC controllers that also expose a few JSON endpoints via `@ResponseBody`.

---

## 3. Core concept

```
@Controller class lifecycle:
  1. Component-scan finds @Controller class
  2. Spring creates a singleton bean
  3. RequestMappingHandlerMapping scans the bean
     → builds method → @RequestMapping metadata map
  4. Per request:
     DispatcherServlet → HandlerMapping.getHandler()
       → HandlerExecutionChain (controller bean + interceptors)
     HandlerAdapter.handle()
       → resolves arguments
       → calls controller method
       → processes return value (String → view name, or Object → body)
```

---

## 4. Diagram

<svg viewBox="0 0 740 280" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="280" fill="#0d1117"/>

  <!-- startup path -->
  <rect x="10" y="20" width="130" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="75" y="38" text-anchor="middle" fill="#6db33f">@Controller class</text>
  <text x="75" y="54" text-anchor="middle" fill="#8b949e" font-size="10">component-scan</text>

  <line x1="140" y1="40" x2="180" y2="40" stroke="#8b949e" marker-end="url(#ac)"/>

  <rect x="180" y="20" width="155" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="257" y="38" text-anchor="middle" fill="#6db33f">RequestMapping</text>
  <text x="257" y="54" text-anchor="middle" fill="#8b949e" font-size="10">HandlerMapping (startup)</text>

  <line x1="335" y1="40" x2="375" y2="40" stroke="#8b949e" marker-end="url(#ac)"/>

  <rect x="375" y="20" width="155" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="452" y="38" text-anchor="middle" fill="#e6edf3">Method → URL map</text>
  <text x="452" y="54" text-anchor="middle" fill="#8b949e" font-size="10">built once at startup</text>

  <!-- runtime path -->
  <rect x="10" y="110" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="133" text-anchor="middle" fill="#79c0ff">HTTP Request</text>

  <line x1="140" y1="130" x2="180" y2="130" stroke="#8b949e" marker-end="url(#ac)"/>

  <rect x="180" y="110" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="245" y="133" text-anchor="middle" fill="#79c0ff">DispatcherServlet</text>

  <line x1="310" y1="130" x2="350" y2="130" stroke="#8b949e" marker-end="url(#ac)"/>

  <rect x="350" y="110" width="160" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="430" y="128" text-anchor="middle" fill="#6db33f">Controller method</text>
  <text x="430" y="144" text-anchor="middle" fill="#8b949e" font-size="10">args resolved, method called</text>

  <line x1="510" y1="130" x2="550" y2="130" stroke="#8b949e" marker-end="url(#ac)"/>

  <!-- return value fork -->
  <rect x="550" y="90" width="170" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="635" y="112" text-anchor="middle" fill="#8b949e">String "viewName"</text>
  <text x="635" y="125" text-anchor="middle" fill="#8b949e" font-size="10">→ ViewResolver → HTML</text>

  <rect x="550" y="140" width="170" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="635" y="160" text-anchor="middle" fill="#6db33f">@ResponseBody Object</text>
  <text x="635" y="174" text-anchor="middle" fill="#8b949e" font-size="10">→ HttpMessageConverter → JSON</text>

  <line x1="510" y1="120" x2="548" y2="108" stroke="#8b949e" stroke-dasharray="3,2"/>
  <line x1="510" y1="140" x2="548" y2="158" stroke="#6db33f" stroke-dasharray="3,2"/>

  <!-- caption -->
  <text x="370" y="230" text-anchor="middle" fill="#8b949e" font-size="11">@Controller handles both view (String) and body (@ResponseBody) return types</text>

  <defs>
    <marker id="ac" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Startup builds the URL→method map once; runtime looks up the method and processes its return value.*

---

## 5. Runnable example

### Level 1 — Basic

A `@Controller` returning an HTML view and injecting a model attribute:

```java
// ProductController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

@Controller
@RequestMapping("/products")
public class ProductController {

    @GetMapping("/{id}")
    public String detail(@PathVariable long id, Model model) {
        model.addAttribute("productId", id);
        model.addAttribute("productName", "Widget #" + id);
        return "products/detail"; // → templates/products/detail.html
    }
}
```

```html
<!-- src/main/resources/templates/products/detail.html -->
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
<body>
  <h1 th:text="${productName}">Product</h1>
  <p>ID: <span th:text="${productId}">0</span></p>
</body>
</html>
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/products/42
# <h1>Widget #42</h1> <p>ID: 42</p>
```

`@Controller` + `@GetMapping("/{id}")` routes `GET /products/{id}` to `detail()`.  The `Model` parameter is a `Map<String,Object>` populated by Spring.  The returned `String` is the logical view name; `ThymeleafViewResolver` finds `templates/products/detail.html` and merges the model.

---

### Level 2 — Intermediate

Same product scenario — now the same controller exposes a **JSON endpoint** via `@ResponseBody` alongside the HTML view method, demonstrating mixed use:

```java
// ProductController.java (extended)
import com.fasterxml.jackson.annotation.JsonProperty;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

@Controller
@RequestMapping("/products")
public class ProductController {

    // View-returning method (no @ResponseBody)
    @GetMapping("/{id}")
    public String detail(@PathVariable long id, Model model) {
        model.addAttribute("productId", id);
        model.addAttribute("productName", "Widget #" + id);
        return "products/detail";
    }

    // JSON API method on the same controller
    @GetMapping(value = "/{id}/json", produces = "application/json")
    @ResponseBody
    public ProductDto detailJson(@PathVariable long id) {
        return new ProductDto(id, "Widget #" + id, 9.99);
    }

    // POST that processes form submission and redirects
    @PostMapping
    public String create(@RequestParam String name, Model model) {
        model.addAttribute("created", name);
        return "redirect:/products/1"; // POST/Redirect/GET pattern
    }

    record ProductDto(@JsonProperty("id") long id,
                      @JsonProperty("name") String name,
                      @JsonProperty("price") double price) {}
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# HTML view
curl http://localhost:8080/products/1
# <h1>Widget #1</h1>

# JSON endpoint
curl -H "Accept: application/json" http://localhost:8080/products/1/json
# {"id":1,"name":"Widget #1","price":9.99}

# Form POST + redirect
curl -i -X POST -d "name=Gadget" http://localhost:8080/products
# HTTP/1.1 302  Location: /products/1
```

**What changed:** `@ResponseBody` on `detailJson` tells Spring to write the return value directly to the response via `MappingJackson2HttpMessageConverter` instead of passing it to a `ViewResolver`.  The form `@PostMapping` returns `"redirect:/products/1"` — a special view name that makes `DispatcherServlet` send a `302` redirect (the POST/Redirect/GET pattern prevents form re-submission on browser refresh).

---

### Level 3 — Advanced

Production scenario: a `@Controller` with **model attribute setup**, **`@SessionAttributes`** to persist the product being edited across multiple form steps, and a `@ControllerAdvice` for shared model data:

```java
// ProductEditController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.support.SessionStatus;

@Controller
@RequestMapping("/products/{id}/edit")
@SessionAttributes("editProduct")  // keeps "editProduct" in HTTP session across requests
public class ProductEditController {

    // Called before any handler method — populates model with fresh product
    @ModelAttribute("editProduct")
    public ProductForm loadProduct(@PathVariable long id) {
        return new ProductForm(id, "Widget #" + id, 9.99); // load from DB in real app
    }

    @GetMapping
    public String editForm(@ModelAttribute("editProduct") ProductForm form) {
        return "products/edit"; // renders form pre-populated from session
    }

    @PostMapping("/step2")
    public String step2(@ModelAttribute("editProduct") ProductForm form,
                         @RequestParam double price) {
        form.setPrice(price);  // mutates the session-held object
        return "products/edit-step2";
    }

    @PostMapping("/save")
    public String save(@ModelAttribute("editProduct") ProductForm form,
                        SessionStatus status) {
        // persist form to DB here
        status.setComplete();  // clears @SessionAttributes — MUST do this or session leaks
        return "redirect:/products/" + form.getId();
    }

    static class ProductForm {
        private final long id;
        private String name;
        private double price;
        ProductForm(long id, String name, double price) { this.id=id; this.name=name; this.price=price; }
        public long getId() { return id; }
        public String getName() { return name; }
        public double getPrice() { return price; }
        public void setPrice(double price) { this.price = price; }
    }
}
```

```java
// GlobalModelAdvice.java — adds data to every @Controller's model
import org.springframework.web.bind.annotation.*;

@ControllerAdvice
public class GlobalModelAdvice {
    @ModelAttribute("appVersion")
    public String appVersion() { return "2.1.0"; }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Start edit flow
curl -c cookies.txt http://localhost:8080/products/1/edit
# renders edit form; session starts with editProduct={id=1, name=Widget #1, price=9.99}

# Update price in step 2
curl -c cookies.txt -b cookies.txt -X POST -d "price=14.99" http://localhost:8080/products/1/edit/step2
# session editProduct.price updated to 14.99

# Save
curl -c cookies.txt -b cookies.txt -X POST http://localhost:8080/products/1/edit/save
# 302 → /products/1  (session attribute cleared)
```

**What changed and why:**
- `@SessionAttributes("editProduct")` stores the model attribute in the HTTP session so it persists between the three step requests without the controller explicitly managing `HttpSession`.
- `@ModelAttribute` on the `loadProduct` method is called **before** every handler method — it acts as a `@BeforeEach` for the model.
- `SessionStatus.setComplete()` in the `save` handler removes the session attribute — omitting this leaks the session-bound object until the session expires.
- `@ControllerAdvice` + `@ModelAttribute` in `GlobalModelAdvice` injects `appVersion` into every controller's model automatically — no per-controller code needed.

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="210" fill="#0d1117"/>
  <!-- steps -->
  <rect x="10" y="60" width="120" height="40" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="78" text-anchor="middle" fill="#79c0ff">GET /edit</text>
  <text x="70" y="93" text-anchor="middle" fill="#8b949e" font-size="10">@ModelAttribute → session</text>
  <line x1="130" y1="80" x2="165" y2="80" stroke="#8b949e" marker-end="url(#acc)"/>
  <rect x="165" y="60" width="130" height="40" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="230" y="78" text-anchor="middle" fill="#6db33f">POST /step2</text>
  <text x="230" y="93" text-anchor="middle" fill="#8b949e" font-size="10">mutate session object</text>
  <line x1="295" y1="80" x2="330" y2="80" stroke="#8b949e" marker-end="url(#acc)"/>
  <rect x="330" y="60" width="120" height="40" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="390" y="78" text-anchor="middle" fill="#6db33f">POST /save</text>
  <text x="390" y="93" text-anchor="middle" fill="#8b949e" font-size="10">persist + status.setComplete()</text>
  <line x1="450" y1="80" x2="485" y2="80" stroke="#8b949e" marker-end="url(#acc)"/>
  <rect x="485" y="60" width="110" height="40" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="540" y="78" text-anchor="middle" fill="#e6edf3">302 → /products/1</text>
  <text x="540" y="93" text-anchor="middle" fill="#8b949e" font-size="10">session cleared</text>
  <!-- session box -->
  <rect x="145" y="130" width="250" height="36" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="4,2"/>
  <text x="270" y="148" text-anchor="middle" fill="#8b949e">HTTP Session: editProduct {id,name,price}</text>
  <text x="270" y="162" text-anchor="middle" fill="#8b949e" font-size="10">shared across all three steps via @SessionAttributes</text>
  <!-- lines from steps to session -->
  <line x1="230" y1="100" x2="230" y2="130" stroke="#8b949e" stroke-dasharray="2,2"/>
  <line x1="390" y1="100" x2="390" y2="130" stroke="#8b949e" stroke-dasharray="2,2"/>
  <text x="350" y="195" text-anchor="middle" fill="#8b949e" font-size="10">@SessionAttributes persists model across multi-step forms without manual HttpSession management</text>
  <defs><marker id="acc" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Startup:**

1. Component-scan finds `ProductEditController` (annotated `@Controller`), creates a singleton bean.
2. `RequestMappingHandlerMapping` inspects the bean: collects `@GetMapping`, `@PostMapping` methods, and `@ModelAttribute` methods.
3. Registers URL→method mappings in its internal registry.

**Per-request: GET /products/1/edit:**

4. `DispatcherServlet.doDispatch()` → `HandlerMapping.getHandler()` → `ProductEditController`.
5. `RequestMappingHandlerAdapter` processes the handler:
   a. Calls `@ControllerAdvice` `@ModelAttribute` methods first (adds `appVersion` to model).
   b. Calls `@ModelAttribute("editProduct") loadProduct(1)` — creates `ProductForm{id=1, name=Widget#1, price=9.99}`.
   c. Spring checks `@SessionAttributes("editProduct")` — not in session yet, so stores the new object in session.
   d. Calls `editForm(form)` — receives the same `ProductForm` from the model. Returns `"products/edit"`.
6. `ViewResolver` resolves to `templates/products/edit.html`; renders with model `{editProduct=..., appVersion=2.1.0}`.

**Per-request: POST /products/1/edit/step2:**

4–5. Same mapping process. `@ModelAttribute("editProduct")` checks session first — finds existing object. Does NOT call `loadProduct` again.
6. `step2(form, 14.99)` mutates `form.price = 14.99` — the session-held object is mutated in place.
7. Returns `"products/edit-step2"` — renders step 2 view.

**Per-request: POST /products/1/edit/save:**

6. `save(form, status)` persists data. `status.setComplete()` signals `@SessionAttributes` to remove `"editProduct"` from session.
7. Returns `"redirect:/products/1"` — `DispatcherServlet` sends `302 Location: /products/1`.

---

## 7. Gotchas & takeaways

> **Not calling `SessionStatus.setComplete()` leaks session memory.**  `@SessionAttributes` stores objects until the session expires or `setComplete()` is called.  For multi-step forms, always call `setComplete()` in the final handler.

> **`@Controller` methods returning `String` without `@ResponseBody` treat the return value as a view name.**  Adding `@ResponseBody` to the method (or switching to `@RestController`) writes the string as the response body.  Both work but serve different purposes.

> **`@ModelAttribute` methods on `@Controller` run before every handler in that controller.**  If you only want them for specific paths, put them in a narrowly scoped `@ControllerAdvice(assignableTypes=...)` or perform the setup inside the handler itself.

- `@Controller` = `@Component` + web-controller semantics; `@RestController` = `@Controller` + `@ResponseBody` on all methods.
- Return `"redirect:/path"` for the POST/Redirect/GET pattern — prevents browser form re-submission on refresh.
- `@SessionAttributes` + `@ModelAttribute` is the Spring-idiomatic way to manage multi-step form state without touching `HttpSession` directly.
- `@ControllerAdvice` with `@ModelAttribute` injects common model data into every controller's model — use it for user info, app version, navigation data.
