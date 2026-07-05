---
card: spring-framework
gi: 314
slug: modelattribute-method-argument
title: "@ModelAttribute (method & argument)"
---

## 1. What it is

`@ModelAttribute` has two distinct uses in Spring MVC:

**1. On a method** — marks a method that populates the model *before* any handler method in the same controller (or `@ControllerAdvice`) runs:

```java
@ModelAttribute("categories")
public List<String> loadCategories() {
    return List.of("tools", "decor", "garden");
}
// → "categories" is now in the model for every handler in this controller
```

**2. On a method parameter** — binds form fields (or query params) to a Java object, optionally validated:

```java
@PostMapping("/products")
public String create(@ModelAttribute @Valid ProductForm form, BindingResult errors) {
    // form.name, form.price etc. populated from request
}
```

Both usages feed into Spring's `Model` — the `Map<String,Object>` passed to view templates.

---

## 2. Why & when

Use **method-level** `@ModelAttribute` for data that every view in a controller needs: navigation menus, look-up lists, current user, config values. It runs before every handler, so controllers never repeat the lookup.

Use **parameter-level** `@ModelAttribute` for HTML form binding — the alternative to `@RequestBody` for traditional form submissions (`Content-Type: application/x-www-form-urlencoded`). It binds each form field by name to a matching bean property, and integrates with `BindingResult` for field-level validation errors.

---

## 3. Core concept

```
Method-level: runs BEFORE any handler in the controller

  @ModelAttribute("categories")        @ModelAttribute("currentUser")
  List<String> loadCategories()  +     User loadUser(Principal p)
         ↓                                     ↓
     model["categories"] = [...]         model["currentUser"] = User{...}

  THEN handler runs:
  @GetMapping("/products")
  String list(Model model) {
      // model already has "categories" and "currentUser"
      return "products/list";
  }

Parameter-level: binds request → object

  POST /products  Content-Type: application/x-www-form-urlencoded
  Body: name=Hammer&price=9.99&category=tools

  @PostMapping
  String create(@ModelAttribute ProductForm form)
  // form.name = "Hammer", form.price = 9.99, form.category = "tools"
  // also added to model as "productForm" (uncapitalized class name)
```

---

## 4. Diagram

<svg viewBox="0 0 740 300" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="300" fill="#0d1117"/>

  <!-- startup / per-request flow -->
  <!-- @ModelAttribute methods -->
  <rect x="10" y="30" width="190" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="50" text-anchor="middle" fill="#6db33f">@ModelAttribute methods</text>
  <text x="105" y="67" text-anchor="middle" fill="#8b949e" font-size="10">loadCategories(), loadUser() …</text>

  <line x1="200" y1="55" x2="240" y2="55" stroke="#6db33f" marker-end="url(#ama)"/>

  <!-- Model -->
  <rect x="240" y="20" width="160" height="70" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="320" y="40" text-anchor="middle" fill="#6db33f">Model</text>
  <text x="320" y="57" text-anchor="middle" fill="#8b949e" font-size="10">categories=[tools,decor]</text>
  <text x="320" y="72" text-anchor="middle" fill="#8b949e" font-size="10">currentUser=User{alice}</text>

  <line x1="400" y1="55" x2="440" y2="55" stroke="#8b949e" marker-end="url(#ama)"/>

  <!-- Handler method -->
  <rect x="440" y="20" width="200" height="70" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="40" text-anchor="middle" fill="#79c0ff">Handler method runs</text>
  <text x="540" y="57" text-anchor="middle" fill="#8b949e" font-size="10">model already populated;</text>
  <text x="540" y="72" text-anchor="middle" fill="#8b949e" font-size="10">can add more, then → view</text>

  <!-- Form binding path -->
  <rect x="10" y="160" width="190" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="178" text-anchor="middle" fill="#79c0ff">POST form data</text>
  <text x="105" y="193" text-anchor="middle" fill="#8b949e" font-size="10">name=Hammer&amp;price=9.99</text>

  <line x1="200" y1="185" x2="240" y2="185" stroke="#8b949e" marker-end="url(#ama)"/>

  <rect x="240" y="155" width="200" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="340" y="175" text-anchor="middle" fill="#6db33f">@ModelAttribute binding</text>
  <text x="340" y="192" text-anchor="middle" fill="#8b949e" font-size="10">setters called per field name</text>
  <text x="340" y="207" text-anchor="middle" fill="#8b949e" font-size="10">"price" → ConversionService → 9.99</text>

  <line x1="440" y1="185" x2="480" y2="185" stroke="#8b949e" marker-end="url(#ama)"/>

  <rect x="480" y="155" width="180" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="570" y="175" text-anchor="middle" fill="#6db33f">ProductForm{</text>
  <text x="570" y="192" text-anchor="middle" fill="#8b949e" font-size="10">name="Hammer",price=9.99}</text>
  <text x="570" y="207" text-anchor="middle" fill="#8b949e" font-size="10">also added to model</text>

  <text x="370" y="268" text-anchor="middle" fill="#8b949e" font-size="11">Method @ModelAttribute populates shared model; parameter @ModelAttribute binds form data</text>

  <defs>
    <marker id="ama" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`@ModelAttribute` methods run first, populating the shared model; parameter binding runs when resolving handler arguments.*

---

## 5. Runnable example

### Level 1 — Basic

A product form controller using `@ModelAttribute` for both lookup data and form binding:

```java
// ProductController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@Controller
@RequestMapping("/products")
public class ProductController {

    // Method-level: called before EVERY handler in this controller
    @ModelAttribute("categories")
    public List<String> loadCategories() {
        return List.of("tools", "decor", "garden");
    }

    // Show create form — categories already in model
    @GetMapping("/new")
    public String newForm(@ModelAttribute ProductForm form) {
        // form is an empty ProductForm added to model as "productForm"
        return "products/form";
    }

    // Handle form submission — form fields bound to ProductForm
    @PostMapping
    public String create(@ModelAttribute ProductForm form, Model model) {
        model.addAttribute("created", form.getName());
        return "products/created";
    }

    static class ProductForm {
        private String name;
        private String category;
        private double price;
        // getters and setters required for binding
        public String getName() { return name; }
        public void setName(String n) { name = n; }
        public String getCategory() { return category; }
        public void setCategory(String c) { category = c; }
        public double getPrice() { return price; }
        public void setPrice(double p) { price = p; }
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# GET form — model has categories from @ModelAttribute method
curl http://localhost:8080/products/new
# renders form; ${categories} = [tools, decor, garden]

# POST form
curl -X POST -d "name=Hammer&category=tools&price=9.99" \
     http://localhost:8080/products
# renders "created" view with created=Hammer
```

`@ModelAttribute("categories")` is called before both `newForm` and `create` — any handler in this controller gets the categories list in the model. `@ModelAttribute ProductForm form` in `newForm` creates an empty form object and adds it to the model as `"productForm"` (uncapitalized class name), making it available to the view.

---

### Level 2 — Intermediate

Same product form — now adding `@Valid` validation, `BindingResult`, and a `@ControllerAdvice` that injects data into every controller's model:

```java
// ProductController.java (extended)
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@Controller
@RequestMapping("/products")
public class ProductController {

    @ModelAttribute("categories")
    public List<String> loadCategories() {
        return List.of("tools", "decor", "garden");
    }

    @GetMapping("/new")
    public String newForm(@ModelAttribute("productForm") ProductForm form) {
        return "products/form";
    }

    @PostMapping
    public String create(
            @ModelAttribute("productForm") @Valid ProductForm form,
            BindingResult errors,  // must immediately follow @Valid param
            Model model) {

        if (errors.hasErrors()) {
            // Re-render form; model has productForm + categories + appVersion
            return "products/form";
        }
        model.addAttribute("created", form.getName());
        return "products/created";
    }

    static class ProductForm {
        @NotBlank @Size(max = 100)
        private String name;
        @NotBlank
        private String category;
        @Min(0) @Max(99999)
        private double price;
        // getters/setters
        public String getName() { return name; }
        public void setName(String n) { name = n; }
        public String getCategory() { return category; }
        public void setCategory(String c) { category = c; }
        public double getPrice() { return price; }
        public void setPrice(double p) { price = p; }
    }
}
```

```java
// GlobalModelAdvice.java
import org.springframework.web.bind.annotation.*;

@ControllerAdvice
public class GlobalModelAdvice {
    @ModelAttribute("appVersion")
    public String appVersion() { return "2.1.0"; }
}
```

**How to run:**
```bash
# Valid submission
curl -X POST -d "name=Hammer&category=tools&price=9.99" \
     http://localhost:8080/products
# renders "products/created"; model has appVersion=2.1.0

# Invalid — blank name
curl -X POST -d "name=&category=tools&price=9.99" \
     http://localhost:8080/products
# re-renders form; errors.getFieldError("name").defaultMessage = "must not be blank"
```

**What changed:** `@Valid` triggers Bean Validation on `ProductForm`. `BindingResult` (immediately following) receives field errors instead of throwing an exception — allows re-rendering the form with inline errors. `@ControllerAdvice` + `@ModelAttribute` on `GlobalModelAdvice` injects `appVersion` into every controller's model automatically.

---

### Level 3 — Advanced

Production scenario: `@ModelAttribute` used with `@SessionAttributes` for a multi-step wizard, plus a method-level `@ModelAttribute` that performs a database lookup based on a path variable:

```java
// ProductEditController.java
import jakarta.validation.*;
import org.springframework.stereotype.Controller;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.support.SessionStatus;
import java.util.*;

@Controller
@RequestMapping("/products/{productId}/edit")
@SessionAttributes("editForm")   // persist editForm across steps
public class ProductEditController {

    private final Map<Long, ProductDto> db = new HashMap<>(Map.of(
            1L, new ProductDto(1L, "Hammer", "tools", 9.99),
            2L, new ProductDto(2L, "Drill",  "tools", 49.99)));

    // Method @ModelAttribute — loads product from DB by path variable
    // Called BEFORE handler; result stored under "editForm" and in session
    @ModelAttribute("editForm")
    public ProductForm loadProduct(@PathVariable long productId) {
        ProductDto dto = db.get(productId);
        if (dto == null) throw new IllegalArgumentException("Not found: " + productId);
        return new ProductForm(dto.name(), dto.category(), dto.price());
    }

    @GetMapping
    public String editStep1(@ModelAttribute("editForm") ProductForm form) {
        return "products/edit-step1"; // form pre-filled from DB
    }

    @PostMapping("/step2")
    public String editStep2(
            @ModelAttribute("editForm") @Valid ProductForm form,
            BindingResult errors) {
        if (errors.hasErrors()) return "products/edit-step1";
        return "products/edit-step2"; // session holds updated form
    }

    @PostMapping("/save")
    public String save(
            @PathVariable long productId,
            @ModelAttribute("editForm") ProductForm form,
            BindingResult errors,
            SessionStatus status) {

        if (errors.hasErrors()) return "products/edit-step2";
        db.put(productId, new ProductDto(productId, form.getName(), form.getCategory(), form.getPrice()));
        status.setComplete(); // clear session attribute — MUST do this
        return "redirect:/products/" + productId;
    }

    record ProductDto(long id, String name, String category, double price) {}

    static class ProductForm {
        @NotBlank private String name;
        @NotBlank private String category;
        @Min(0)   private double price;
        ProductForm(String n, String c, double p) { name=n; category=c; price=p; }
        public String getName() { return name; }  public void setName(String n) { name=n; }
        public String getCategory() { return category; } public void setCategory(String c) { category=c; }
        public double getPrice() { return price; } public void setPrice(double p) { price=p; }
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Start edit — loads from DB, stores in session
curl -c cookies.txt http://localhost:8080/products/1/edit
# renders step1; form pre-filled with Hammer/tools/9.99

# Post step2 — form mutated in session
curl -c cookies.txt -b cookies.txt \
     -X POST -d "name=Hammer+Pro&category=tools&price=14.99" \
     http://localhost:8080/products/1/edit/step2
# renders step2; session form now has name=Hammer Pro

# Save — persist to DB, clear session
curl -c cookies.txt -b cookies.txt \
     -X POST -d "name=Hammer+Pro&category=tools&price=14.99" \
     http://localhost:8080/products/1/edit/save
# 302 → /products/1  (session cleared)
```

**What changed and why:**
- Method-level `@ModelAttribute("editForm")` takes `@PathVariable long productId` — Spring injects path variables into `@ModelAttribute` methods. The DB lookup happens once; subsequent steps read from the session.
- `@SessionAttributes("editForm")` stores the form in the session after the first step — `loadProduct` is NOT called again because Spring finds `"editForm"` in the session and uses that.
- `status.setComplete()` in `save` clears the session attribute — without this, the session leaks the old form until it expires.

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="190" fill="#0d1117"/>
  <!-- steps -->
  <rect x="10" y="50" width="110" height="36" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="65" y="65" text-anchor="middle" fill="#6db33f">GET /edit</text>
  <text x="65" y="79" text-anchor="middle" fill="#8b949e" font-size="10">DB load → session</text>
  <line x1="120" y1="68" x2="155" y2="68" stroke="#8b949e" marker-end="url(#ama2)"/>

  <rect x="155" y="50" width="130" height="36" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="220" y="65" text-anchor="middle" fill="#6db33f">POST /step2</text>
  <text x="220" y="79" text-anchor="middle" fill="#8b949e" font-size="10">session form mutated</text>
  <line x1="285" y1="68" x2="320" y2="68" stroke="#8b949e" marker-end="url(#ama2)"/>

  <rect x="320" y="50" width="110" height="36" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="375" y="65" text-anchor="middle" fill="#6db33f">POST /save</text>
  <text x="375" y="79" text-anchor="middle" fill="#8b949e" font-size="10">persist; status.setComplete()</text>
  <line x1="430" y1="68" x2="465" y2="68" stroke="#8b949e" marker-end="url(#ama2)"/>

  <rect x="465" y="50" width="100" height="36" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="515" y="65" text-anchor="middle" fill="#79c0ff">302 redirect</text>
  <text x="515" y="79" text-anchor="middle" fill="#8b949e" font-size="10">session cleared</text>

  <!-- session box -->
  <rect x="120" y="120" width="320" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="4,2"/>
  <text x="280" y="139" text-anchor="middle" fill="#8b949e">HTTP Session: editForm{name,category,price}</text>
  <line x1="220" y1="86" x2="220" y2="120" stroke="#8b949e" stroke-dasharray="2,2"/>
  <line x1="375" y1="86" x2="375" y2="120" stroke="#8b949e" stroke-dasharray="2,2"/>

  <text x="350" y="172" text-anchor="middle" fill="#8b949e" font-size="10">@ModelAttribute method runs only on step 1 (DB load); session provides form for steps 2+3</text>
  <defs><marker id="ama2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Startup:**

1. `ProductEditController` scanned; `loadProduct` identified as `@ModelAttribute("editForm")` method.
2. `RequestMappingHandlerAdapter` notes that before calling any handler method, `loadProduct` must run.

**Per-request: `GET /products/1/edit`:**

3. `@PathVariable long productId` → `1L` resolved.
4. `loadProduct(1L)` called: `db.get(1L)` → `ProductDto{Hammer, tools, 9.99}`. Returns `ProductForm{Hammer, tools, 9.99}`.
5. Result stored in model as `"editForm"` and — because of `@SessionAttributes("editForm")` — also in the HTTP session.
6. `editStep1(form)` called with the same `ProductForm`. Returns `"products/edit-step1"`.
7. View rendered with model `{editForm: ProductForm{Hammer,tools,9.99}}`.

**Per-request: `POST /products/1/edit/step2`:**

4b. `@ModelAttribute("editForm")` check: `@SessionAttributes` has `"editForm"` in session. **`loadProduct` is NOT called** — Spring uses the session-stored object.
5b. Form binding: request fields (`name=Hammer Pro`, `price=14.99`) applied to session `ProductForm` via setters. Session object mutated in place.
6b. `@Valid` validates: all constraints pass. `BindingResult.hasErrors()` = false.
7b. Returns `"products/edit-step2"`.

**Per-request: `POST /products/1/edit/save`:**

4c. Session `ProductForm` retrieved again (unchanged from step2 unless new form fields submitted).
5c. `save(1L, form, errors, status)`: `db.put(1L, ...)` — DB updated.
6c. `status.setComplete()` — Spring removes `"editForm"` from session.
7c. Returns `"redirect:/products/1"` → `302 Location: /products/1`.

---

## 7. Gotchas & takeaways

> **Method-level `@ModelAttribute` runs before every handler in the controller — even handlers that don't use that model attribute.**  An expensive DB call in `@ModelAttribute` is paid for every request. Guard with caching or move expensive lookups into the specific handlers that need them.

> **When `@SessionAttributes` is active, Spring checks the session before calling `@ModelAttribute` methods.**  If the session already has the attribute, the `@ModelAttribute` method is skipped. This is intentional for multi-step forms but can cause stale data if you forget to call `status.setComplete()`.

> **`BindingResult` must immediately follow the `@ModelAttribute` (or `@RequestBody`) parameter it belongs to.**  Spring pairs them positionally — any other parameter between them breaks the association and Spring falls back to throwing `MethodArgumentNotValidException`.

- Method `@ModelAttribute` populates shared model data; parameter `@ModelAttribute` binds form fields to a bean.
- `@ControllerAdvice` + `@ModelAttribute` injects data into every controller's model — use for site-wide data (user, version, navigation).
- `@SessionAttributes` + `@ModelAttribute` = multi-step wizard pattern without managing `HttpSession` directly.
- Always call `SessionStatus.setComplete()` in the final wizard step — otherwise session memory leaks.
- `@ModelAttribute` on a parameter also adds the bound object to the model — the view can access `${productForm}` without explicit `model.addAttribute()`.
