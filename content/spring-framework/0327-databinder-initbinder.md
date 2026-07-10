---
card: spring-framework
gi: 327
slug: databinder-initbinder
title: "DataBinder & @InitBinder"
---

## 1. What it is

`DataBinder` is the Spring MVC component that converts incoming request data (query params, form fields, path variables) from strings into typed Java objects and binds them onto a target object's fields. `@InitBinder` marks a controller method that customizes the `WebDataBinder` used for a request — registering custom property editors, converters, or validators before binding happens.

```java
@InitBinder
public void initBinder(WebDataBinder binder) {
    binder.registerCustomEditor(LocalDate.class,
        new CustomDateEditor(new SimpleDateFormat("yyyy-MM-dd"), false));
}
```

## 2. Why & when

By default, Spring's binding handles common types (`String`, primitives, wrappers, and anything with a registered `Converter`) automatically. You need `@InitBinder` when:

- A form field's string format doesn't match Spring's default conversion (e.g. dates in `dd/MM/yyyy` instead of ISO format).
- You want to **whitelist or blacklist** which fields can be bound from request parameters onto a model object (`setAllowedFields`/`setDisallowedFields`) — a security-relevant control against mass-assignment attacks.
- You need to trim whitespace, treat empty strings as `null`, or apply another `PropertyEditor`-level transformation before binding.
- You want validation to run automatically as part of binding, via `binder.addValidators(...)`.

This mostly applies to classic form-backed MVC controllers using `@ModelAttribute` on command objects; JSON bodies bound via `@RequestBody` go through `HttpMessageConverter`/Jackson instead, which `@InitBinder` does not affect.

## 3. Core concept

```
Request params:  name=Drill&price=29.99&createdAt=25/12/2026
                              |
                              v
                     WebDataBinder (per-request, per-target-object)
                       - property editors (String -> Date, etc.)
                       - allowed/disallowed fields
                       - attached Validators
                              |
                              v
                     target object populated:
                       Product { name="Drill", price=29.99, createdAt=2026-12-25 }

@InitBinder runs BEFORE the handler method, once per request,
to CONFIGURE the binder used for THAT request's binding step.

@InitBinder                    @InitBinder("product")
  (no value)                     (value = target attribute name)
  applies to ALL                 applies ONLY when binding
  @ModelAttribute /               the attribute named "product"
  @RequestParam targets
```

## 4. Diagram

<svg viewBox="0 0 720 230" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="230" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">@InitBinder configures WebDataBinder before binding</text>

  <rect x="20" y="50" width="180" height="60" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="72" text-anchor="middle" fill="#79c0ff">Request params</text>
  <text x="110" y="90" text-anchor="middle" fill="#8b949e" font-size="10">createdAt=25/12/2026</text>

  <line x1="200" y1="80" x2="260" y2="80" stroke="#8b949e" marker-end="url(#a3)"/>

  <rect x="260" y="30" width="200" height="50" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="360" y="50" text-anchor="middle" fill="#6db33f">@InitBinder method</text>
  <text x="360" y="67" text-anchor="middle" fill="#8b949e" font-size="10">registers date editor</text>

  <line x1="360" y1="80" x2="360" y2="110" stroke="#6db33f" marker-end="url(#a3)"/>

  <rect x="260" y="110" width="200" height="60" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="360" y="130" text-anchor="middle" fill="#8b949e">WebDataBinder</text>
  <text x="360" y="148" text-anchor="middle" fill="#8b949e" font-size="10">converts + validates</text>

  <line x1="460" y1="140" x2="520" y2="140" stroke="#8b949e" marker-end="url(#a3)"/>

  <rect x="520" y="110" width="180" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="610" y="130" text-anchor="middle" fill="#e6edf3" font-size="11">Product object</text>
  <text x="610" y="148" text-anchor="middle" fill="#e6edf3" font-size="10">createdAt=2026-12-25</text>

  <defs>
    <marker id="a3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`@InitBinder` runs first to configure conversion rules; the configured `WebDataBinder` then converts and populates the target object.*

## 5. Runnable example

### Level 1 — Basic

Custom date format binding for a form:

```java
// ProductController.java
import org.springframework.beans.propertyeditors.CustomDateEditor;
import org.springframework.web.bind.WebDataBinder;
import org.springframework.web.bind.annotation.*;

import java.text.SimpleDateFormat;
import java.util.Date;

@RestController
public class ProductController {

    static class Product {
        public String name;
        public Date createdAt;   // bound from "dd/MM/yyyy" strings
    }

    @InitBinder
    public void initBinder(WebDataBinder binder) {
        SimpleDateFormat format = new SimpleDateFormat("dd/MM/yyyy");
        format.setLenient(false);
        binder.registerCustomEditor(Date.class, new CustomDateEditor(format, false));
    }

    @PostMapping("/products")
    public String create(@ModelAttribute Product product) {
        return "Created: " + product.name + " on " + product.createdAt;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -X POST "http://localhost:8080/products?name=Drill&createdAt=25/12/2026"
# Created: Drill on Fri Dec 25 00:00:00 UTC 2026
```

Without `@InitBinder`, Spring's default binder wouldn't know how to parse `25/12/2026` into a `Date` and would throw a `TypeMismatchException`. The registered `CustomDateEditor` teaches it the expected format.

### Level 2 — Intermediate

Field whitelisting to prevent mass assignment, plus attaching a `Validator`:

```java
// ProductController.java (extended)
import org.springframework.validation.Errors;
import org.springframework.validation.Validator;
import org.springframework.web.bind.WebDataBinder;
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    static class Product {
        public long id;
        public String name;
        public double price;
        public boolean isAdmin;   // dangerous if bindable from request params
    }

    static class ProductValidator implements Validator {
        public boolean supports(Class<?> clazz) { return Product.class.equals(clazz); }
        public void validate(Object target, Errors errors) {
            Product p = (Product) target;
            if (p.price < 0) errors.rejectValue("price", "price.negative", "Price cannot be negative");
        }
    }

    @InitBinder("product")
    public void initBinder(WebDataBinder binder) {
        // Whitelist: only these fields can be set from request parameters
        binder.setAllowedFields("name", "price");
        binder.addValidators(new ProductValidator());
    }

    @PostMapping("/products")
    public String create(@ModelAttribute("product") @org.springframework.validation.annotation.Validated Product product,
                          org.springframework.validation.BindingResult result) {
        if (result.hasErrors()) {
            return "Invalid: " + result.getFieldError().getDefaultMessage();
        }
        return "Created: " + product.name + ", admin=" + product.isAdmin;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Attempt to sneak in isAdmin=true via request params
curl -X POST "http://localhost:8080/products?name=Drill&price=29.99&isAdmin=true"
# Created: Drill, admin=false     <- isAdmin ignored, not in allowed fields

curl -X POST "http://localhost:8080/products?name=Drill&price=-5"
# Invalid: Price cannot be negative
```

**What changed:** `@InitBinder("product")` scopes the customization to only the `@ModelAttribute("product")` target — `setAllowedFields("name", "price")` means any other request parameter (like `isAdmin`) is silently ignored during binding, closing a mass-assignment security hole. The attached `Validator` runs during binding, and `BindingResult` captures any violations for the handler to inspect.

### Level 3 — Advanced

Production pattern: a shared base `@InitBinder` in a `@ControllerAdvice`, trimming whitespace from all string fields, converting empty strings to `null`, and per-controller field restrictions layered on top:

```java
// GlobalBindingAdvice.java — applies to every controller
import org.springframework.web.bind.WebDataBinder;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.InitBinder;

@ControllerAdvice
public class GlobalBindingAdvice {

    @InitBinder
    public void initBinder(WebDataBinder binder) {
        // Trim strings and convert "" to null across ALL controllers
        binder.registerCustomEditor(String.class,
            new org.springframework.beans.propertyeditors.StringTrimmerEditor(true));
    }
}
```

```java
// ProductController.java (production version)
import org.springframework.validation.BindingResult;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.WebDataBinder;
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    record ProductForm(String name, double price) {}   // records are immutable — bound via constructor

    static class Product {
        public long id;
        public String name;
        public double price;
    }

    @InitBinder("product")
    public void initProductBinder(WebDataBinder binder) {
        // Controller-specific restriction, layered on top of the global trimming from the advice
        binder.setDisallowedFields("id");   // id is server-assigned, never client-settable
    }

    @PostMapping("/products")
    public ResponseEntity<String> create(@ModelAttribute("product") @Validated Product product,
                                          BindingResult result) {
        if (result.hasErrors()) {
            return ResponseEntity.badRequest().body(
                "Validation failed: " + result.getFieldErrors().size() + " error(s)");
        }
        product.id = 42;   // server assigns the real id, ignoring any client-supplied value
        return ResponseEntity.ok("Created product " + product.id + ": " + product.name);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -X POST "http://localhost:8080/products?id=999&name=%20%20Drill%20%20&price=29.99"
# Created product 42: Drill
# ("id=999" is ignored (disallowed field); name is trimmed by the global StringTrimmerEditor)
```

**What changed and why:**
- `GlobalBindingAdvice` centralizes a cross-cutting binding rule (trim all strings) that every controller in the app benefits from, without repeating `StringTrimmerEditor` registration everywhere.
- `initProductBinder`'s `setDisallowedFields("id")` layers a controller-specific security rule on top: even if a malicious client passes `id=999`, the binder refuses to set it — the server always assigns the authoritative id afterward.
- Combining `setDisallowedFields`/`setAllowedFields` with `@Validated` + `BindingResult` gives two independent layers of defense: field-level access control during binding, and business-rule validation after.

## 6. Walkthrough

**Request: `POST /products?id=999&name=%20%20Drill%20%20&price=29.99` (Level 3 code).**

1. `DispatcherServlet` resolves the handler `ProductController.create(...)`. Before invoking it, Spring must construct and populate the `@ModelAttribute("product")` argument — this requires a `WebDataBinder`.
2. Spring first runs **all applicable `@InitBinder` methods**, in order: the global one in `GlobalBindingAdvice` (registers `StringTrimmerEditor` for `String.class`), then the controller-local `initProductBinder` (adds `id` to disallowed fields, because it's scoped with `@InitBinder("product")` and this parameter is bound to `"product"`).
3. The now-configured `WebDataBinder` processes each request parameter against the `Product` target:
   - `id=999` → **rejected** (disallowed field) — the object's `id` field is left at its default (`0`).
   - `name=  Drill  ` → bound as a `String`, then passed through `StringTrimmerEditor` → `"Drill"` (whitespace trimmed).
   - `price=29.99` → bound as `double` via default conversion → `29.99`.
4. Because the parameter is annotated `@Validated`, the binder also runs registered validators (none explicitly added here beyond JSR-380 annotations, if present on the class) and records any errors into `BindingResult`.
5. `result.hasErrors()` is `false` (valid data), so the handler proceeds: `product.id = 42` — the server overwrites whatever (rejected) id was attempted, assigning the authoritative value.
6. Handler returns `ResponseEntity.ok("Created product 42: Drill")`.
7. Response sent to client:
   ```
   HTTP/1.1 200 OK
   Content-Type: text/plain

   Created product 42: Drill
   ```

Notice the client's attempted `id=999` never reaches the object — the `WebDataBinder` configured by `@InitBinder` silently drops it before the handler method even runs, which is a stronger guarantee than checking and overwriting it manually inside the handler body.

## 7. Gotchas & takeaways

> **`@InitBinder` only affects binding for `@ModelAttribute`/`@RequestParam`-style parameters — not `@RequestBody`.** JSON payloads deserialized via Jackson bypass `WebDataBinder` entirely; use Jackson's own mechanisms (`@JsonIgnore`, DTOs) to control what JSON fields populate an object.

> **Forgetting `setAllowedFields`/`setDisallowedFields` on objects with sensitive fields (like `isAdmin`, `role`, `id`) is a classic mass-assignment vulnerability.** If a client can guess or discover a field name, a naive `@ModelAttribute`-bound entity can be manipulated via extra request parameters the form never intended to expose.

> **`@InitBinder("name")` must match the exact `@ModelAttribute` name it targets**, including the implicit name derived from the parameter's type when no explicit name is given (e.g. `Product product` implicitly binds to attribute name `"product"`, lowercase first letter of the class name). A mismatched name means the customization silently never applies.

- `@InitBinder` methods run once per request, before the corresponding binding occurs — not once at startup.
- Prefer immutable records/DTOs bound via constructor for new code where possible — they sidestep mass-assignment risk entirely since there are no setters to abuse.
- Global binding rules belong in a `@ControllerAdvice`; controller-specific restrictions belong in that controller's own `@InitBinder`.
- Always explicitly allow/disallow fields on any object with a server-controlled or sensitive property that a form-bound `@ModelAttribute` might otherwise expose.
