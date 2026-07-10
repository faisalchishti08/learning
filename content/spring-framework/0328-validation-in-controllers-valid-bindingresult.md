---
card: spring-framework
gi: 328
slug: validation-in-controllers-valid-bindingresult
title: "Validation in controllers (@Valid + BindingResult)"
---

## 1. What it is

`@Valid` (or Spring's `@Validated`) on a controller method parameter triggers JSR-380 (Bean Validation) checks against a request body or form-bound object, using constraint annotations like `@NotNull`, `@Size`, `@Min` declared on the target class. `BindingResult`, when present as the **very next parameter**, captures validation errors instead of Spring throwing an exception, letting the handler decide how to respond.

```java
@PostMapping("/products")
public ResponseEntity<?> create(@Valid @RequestBody Product product, BindingResult result) {
    if (result.hasErrors()) {
        return ResponseEntity.badRequest().body(result.getFieldErrors());
    }
    return ResponseEntity.ok(save(product));
}
```

## 2. Why & when

Input validation belongs at the boundary — reject malformed or invalid data before it reaches business logic or persistence. `@Valid` + `BindingResult` gives you:

- Declarative validation rules colocated with the data class (`@NotBlank String name`, `@Positive double price`), instead of scattered manual `if` checks in every handler.
- A structured error response instead of a raw exception stack trace.
- Reusability — the same annotated class validates consistently whether bound from JSON, form data, or path/query parameters.

Use `BindingResult` when you want to **handle** validation errors yourself (custom error response shape, partial success, logging). Omit `BindingResult` when you're fine letting Spring throw `MethodArgumentNotValidException` and handling it centrally with `@ExceptionHandler`/`@ControllerAdvice` — that's often the cleaner pattern for REST APIs (see the "Exception handling" and "Controller advice" cards).

## 3. Core concept

```
Product class:
  @NotBlank        String name;
  @Positive        double price;
  @Min(0) @Max(10) int    rating;

Request body: {"name": "", "price": -5, "rating": 20}

              @Valid triggers validation
                       |
                       v
        Each constraint checked against the field value
                       |
          name: "" fails @NotBlank
          price: -5 fails @Positive
          rating: 20 fails @Max(10)
                       |
                       v
        WITH BindingResult param:          WITHOUT BindingResult param:
        errors collected into it,          Spring throws
        handler method still invoked       MethodArgumentNotValidException
        (must check hasErrors())           (handler method NEVER invoked;
                                             caught by @ExceptionHandler
                                             or default error page)
```

The position of `BindingResult` matters: it must immediately follow the `@Valid`-annotated parameter, or Spring won't associate the two and will throw instead.

## 4. Diagram

<svg viewBox="0 0 740 240" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="240" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">@Valid validation branch: with vs without BindingResult</text>

  <rect x="20" y="50" width="200" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="72" text-anchor="middle" fill="#79c0ff">Invalid request body</text>
  <text x="120" y="88" text-anchor="middle" fill="#8b949e" font-size="10">{"name":"","price":-5}</text>

  <line x1="220" y1="75" x2="280" y2="75" stroke="#8b949e" marker-end="url(#a4)"/>

  <rect x="280" y="50" width="180" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="370" y="72" text-anchor="middle" fill="#8b949e">@Valid checks</text>
  <text x="370" y="88" text-anchor="middle" fill="#8b949e" font-size="10">constraints fail</text>

  <line x1="370" y1="100" x2="240" y2="140" stroke="#6db33f" marker-end="url(#a4)"/>
  <line x1="370" y1="100" x2="500" y2="140" stroke="#e6edf3" marker-end="url(#a4)"/>

  <rect x="120" y="140" width="220" height="70" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="230" y="160" text-anchor="middle" fill="#6db33f">has BindingResult</text>
  <text x="230" y="178" text-anchor="middle" fill="#8b949e" font-size="10">handler invoked,</text>
  <text x="230" y="193" text-anchor="middle" fill="#8b949e" font-size="10">result.hasErrors()==true</text>

  <rect x="400" y="140" width="240" height="70" rx="5" fill="#1c2430" stroke="#e6edf3"/>
  <text x="520" y="160" text-anchor="middle" fill="#e6edf3">no BindingResult</text>
  <text x="520" y="178" text-anchor="middle" fill="#8b949e" font-size="10">MethodArgumentNotValidException</text>
  <text x="520" y="193" text-anchor="middle" fill="#8b949e" font-size="10">handler method never runs</text>

  <defs>
    <marker id="a4" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The presence of `BindingResult` right after `@Valid` decides whether errors are caught locally or thrown as an exception.*

## 5. Runnable example

### Level 1 — Basic

Validate a product creation request and return field errors as JSON:

```java
// Product.java
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;

public class Product {
    @NotBlank(message = "name is required")
    public String name;

    @Positive(message = "price must be positive")
    public double price;
}
```

```java
// ProductController.java
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindingResult;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
public class ProductController {

    @PostMapping("/products")
    public ResponseEntity<?> create(@Valid @RequestBody Product product, BindingResult result) {
        if (result.hasErrors()) {
            List<Map<String, String>> errors = result.getFieldErrors().stream()
                .map(fe -> Map.of("field", fe.getField(), "message", fe.getDefaultMessage()))
                .collect(Collectors.toList());
            return ResponseEntity.badRequest().body(errors);
        }
        return ResponseEntity.ok("Created: " + product.name);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -X POST http://localhost:8080/products -H "Content-Type: application/json" -d '{"name":"","price":-5}'
# 400 Bad Request
# [{"field":"name","message":"name is required"},{"field":"price","message":"price must be positive"}]

curl -X POST http://localhost:8080/products -H "Content-Type: application/json" -d '{"name":"Drill","price":29.99}'
# 200 OK
# Created: Drill
```

`@Valid` triggers checking of every annotated field on `product`. Because `BindingResult` immediately follows, errors are captured there instead of throwing — the handler runs regardless and decides the response shape.

### Level 2 — Intermediate

Nested object validation, custom cross-field validation via a class-level constraint, and grouped validation for create vs. update:

```java
// Product.java (extended)
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;

public class Product {
    @NotBlank
    public String name;

    @Positive
    public double price;

    @NotNull @Valid                 // nested object also validated
    public Dimensions dimensions;

    public static class Dimensions {
        @Positive(message = "width must be positive")
        public double width;
        @Positive(message = "height must be positive")
        public double height;
    }
}
```

```java
// ProductController.java (extended)
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    @PostMapping("/products")
    public ResponseEntity<?> create(@Valid @RequestBody Product product, BindingResult result) {
        if (result.hasErrors()) {
            return ResponseEntity.badRequest().body(
                result.getAllErrors().stream().map(e -> e.getDefaultMessage()).toList());
        }
        return ResponseEntity.ok("Created: " + product.name);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -X POST http://localhost:8080/products -H "Content-Type: application/json" \
     -d '{"name":"Drill","price":29.99,"dimensions":{"width":-1,"height":10}}'
# 400 Bad Request
# ["width must be positive"]

curl -X POST http://localhost:8080/products -H "Content-Type: application/json" \
     -d '{"name":"Drill","price":29.99,"dimensions":{"width":5,"height":10}}'
# 200 OK
```

**What changed:** `@Valid` on the `dimensions` field cascades validation into the nested `Dimensions` object — without it, Bean Validation would only check `Product`'s own fields and skip `dimensions` entirely, even though `Dimensions` itself has constraints. `result.getAllErrors()` includes both field-level and object-level errors, useful when validation spans nested structures.

### Level 3 — Advanced

Production pattern: custom cross-field validator (price must exceed a minimum for a given category), validation groups to distinguish create vs. update rules, and converting `BindingResult` into a structured API error response with field paths for nested errors:

```java
// ValidCategoryPrice.java — custom class-level constraint
import jakarta.validation.Constraint;
import jakarta.validation.Payload;
import java.lang.annotation.*;

@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = CategoryPriceValidator.class)
public @interface ValidCategoryPrice {
    String message() default "price too low for category";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}
```

```java
// CategoryPriceValidator.java
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;

public class CategoryPriceValidator implements ConstraintValidator<ValidCategoryPrice, Product> {
    public boolean isValid(Product p, ConstraintValidatorContext ctx) {
        if (p == null || p.category == null) return true;   // let @NotNull handle nulls separately
        double minPrice = "premium".equals(p.category) ? 100.0 : 0.0;
        return p.price >= minPrice;
    }
}
```

```java
// Product.java (production version)
import jakarta.validation.constraints.*;
import jakarta.validation.groups.Default;

@ValidCategoryPrice
public class Product {
    public interface OnCreate {}     // validation group: no id required
    public interface OnUpdate {}     // validation group: id required

    @Null(groups = OnCreate.class, message = "id must not be set on create")
    @NotNull(groups = OnUpdate.class, message = "id is required for update")
    public Long id;

    @NotBlank(groups = {OnCreate.class, OnUpdate.class})
    public String name;

    @Positive(groups = {OnCreate.class, OnUpdate.class})
    public double price;

    public String category;
}
```

```java
// ProductController.java (production version)
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindingResult;
import org.springframework.validation.FieldError;
import org.springframework.validation.ObjectError;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.LinkedHashMap;
import java.util.Map;

@RestController
public class ProductController {

    @PostMapping("/products")
    public ResponseEntity<?> create(@Validated(Product.OnCreate.class) @RequestBody Product product,
                                     BindingResult result) {
        if (result.hasErrors()) return ResponseEntity.badRequest().body(toErrorMap(result));
        product.id = 42L;
        return ResponseEntity.ok(Map.of("id", product.id, "name", product.name));
    }

    @PutMapping("/products/{id}")
    public ResponseEntity<?> update(@PathVariable long id,
                                     @Validated(Product.OnUpdate.class) @RequestBody Product product,
                                     BindingResult result) {
        if (result.hasErrors()) return ResponseEntity.badRequest().body(toErrorMap(result));
        return ResponseEntity.ok(Map.of("id", product.id, "name", product.name));
    }

    private Map<String, String> toErrorMap(BindingResult result) {
        Map<String, String> errors = new LinkedHashMap<>();
        for (FieldError fe : result.getFieldErrors()) errors.put(fe.getField(), fe.getDefaultMessage());
        for (ObjectError oe : result.getGlobalErrors()) errors.put("_global", oe.getDefaultMessage());
        return errors;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Create: id must be absent, premium category needs price >= 100
curl -X POST http://localhost:8080/products -H "Content-Type: application/json" \
     -d '{"name":"Drill","price":50,"category":"premium"}'
# 400 Bad Request  {"_global":"price too low for category"}

curl -X POST http://localhost:8080/products -H "Content-Type: application/json" \
     -d '{"name":"Drill","price":150,"category":"premium"}'
# 200 OK  {"id":42,"name":"Drill"}

# Update: id is now required
curl -X PUT http://localhost:8080/products/42 -H "Content-Type: application/json" \
     -d '{"name":"Drill","price":29.99}'
# 400 Bad Request  {"id":"id is required for update"}
```

**What changed and why:**
- `@Validated(Product.OnCreate.class)` vs `@Validated(Product.OnUpdate.class)` applies **different constraint subsets** to the same class depending on the operation — `id` must be absent on create but present on update, expressed once on the model instead of two near-duplicate DTOs.
- The custom `@ValidCategoryPrice` class-level constraint expresses a cross-field business rule (minimum price by category) that a single-field annotation like `@Positive` cannot capture.
- `toErrorMap` normalizes both field-level (`getFieldErrors`) and object-level (`getGlobalErrors`, where class-level constraints report) errors into one flat, client-friendly structure.

## 6. Walkthrough

**Request: `POST /products` with `{"name":"Drill","price":50,"category":"premium"}` (Level 3 code).**

1. `DispatcherServlet` resolves `ProductController.create(...)`. It must first construct the `@RequestBody Product` argument by deserializing the JSON via Jackson: `Product{id=null, name="Drill", price=50.0, category="premium"}`.
2. Because the parameter carries `@Validated(Product.OnCreate.class)`, Spring's validation post-processor runs Bean Validation against `product`, restricted to constraints tagged with `OnCreate.class` (or no group, which defaults to `Default`).
3. Field-level checks run: `id` — `@Null(groups=OnCreate.class)` — `null` satisfies `@Null` → pass. `name` — `@NotBlank` → `"Drill"` is non-blank → pass. `price` — `@Positive` → `50.0 > 0` → pass.
4. Class-level check runs: `@ValidCategoryPrice` invokes `CategoryPriceValidator.isValid(product, ctx)` — category is `"premium"`, so `minPrice = 100.0`; `50.0 >= 100.0` is `false` → **constraint violated**.
5. Because `BindingResult` follows immediately, Spring does not throw — it packages the violation as a `ObjectError` (class-level errors have no single field, so they land in `getGlobalErrors()`) and invokes `create(product, result)` anyway.
6. Handler checks `result.hasErrors()` → `true`. Calls `toErrorMap(result)`, which iterates `getFieldErrors()` (empty here) and `getGlobalErrors()` (one entry: `"price too low for category"`), producing `{"_global": "price too low for category"}`.
7. Response returned:
   ```
   HTTP/1.1 400 Bad Request
   Content-Type: application/json

   {"_global":"price too low for category"}
   ```

**Second request, `price: 150`:** Step 4's `CategoryPriceValidator` now evaluates `150.0 >= 100.0` → `true` → no violation. `result.hasErrors()` is `false`. Handler assigns `product.id = 42L` (server-controlled) and returns `200 OK` with `{"id":42,"name":"Drill"}`.

## 7. Gotchas & takeaways

> **`BindingResult` must be the parameter immediately after the `@Valid`/`@Validated` argument.** If you insert any other parameter between them (e.g. `@Valid Product product, HttpServletRequest req, BindingResult result`), Spring can't associate the two and throws `IllegalStateException: An Errors/BindingResult argument is expected to be declared immediately after the model attribute`.

> **Without `BindingResult`, validation failure throws `MethodArgumentNotValidException` and the handler body never executes** — you must handle it via `@ExceptionHandler`/`@ControllerAdvice` (see that card) or accept Spring Boot's default error response. Mixing both styles inconsistently across a codebase makes error responses unpredictable for API clients.

> **Nested objects are only validated if the containing field is itself annotated `@Valid`.** Forgetting `@Valid` on a nested field means its own constraint annotations are silently skipped — a very easy mistake with deeply nested request bodies.

- `@Valid` (JSR-380 standard) triggers validation with no group support; `@Validated` (Spring-specific) supports validation groups for context-dependent rule sets.
- Class-level constraints (custom `ConstraintValidator<Annotation, TargetType>`) are the right tool for cross-field/business rules that single-field annotations can't express.
- `result.getFieldErrors()` for per-field messages, `result.getGlobalErrors()` for object/class-level messages — merge both when building an API error response.
- Keep the validated model close to the API contract; use validation groups (`OnCreate`/`OnUpdate`) instead of duplicating near-identical classes for each operation.
