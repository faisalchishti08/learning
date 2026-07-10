---
card: spring-framework
gi: 338
slug: problemdetail-rfc-9457-error-responses
title: "ProblemDetail (RFC 9457) & error responses"
---

## 1. What it is

`ProblemDetail` is a Spring class (introduced in Spring 6 / Spring Boot 3) that implements RFC 9457 ("Problem Details for HTTP APIs", the successor to RFC 7807) — a standardized JSON/XML shape for representing errors in HTTP APIs, with fields `type`, `title`, `status`, `detail`, and `instance`, plus support for arbitrary extension properties.

```java
@ExceptionHandler(ProductNotFoundException.class)
public ProblemDetail handle(ProductNotFoundException ex) {
    return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
}
```

Response:
```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "Product 99 not found",
  "instance": "/products/99"
}
```

## 2. Why & when

Before RFC 7807/9457, every team invented its own error response shape — some used `{"error": "..."}`, others `{"message": "...", "code": "..."}`, others yet another convention. This made generic error-handling tooling (API gateways, client SDKs, monitoring) impossible to build once and reuse across services, since every API had a bespoke error contract.

Use `ProblemDetail` when:
- Building a new REST API and want a standardized, well-understood error shape from day one, rather than inventing your own.
- Consuming or integrating with other RFC 9457-compliant APIs and want response consistency across your own service boundary.
- You need to add extension fields (validation error lists, correlation ids) to an error response in a structured, standard-adjacent way via `setProperty`.

Spring MVC also has built-in exceptions (`ErrorResponseException` and its subtypes — see the next card) that automatically produce `ProblemDetail` responses without you writing any handler code at all, for many common framework-level errors (missing parameters, type mismatches, unsupported media types).

## 3. Core concept

```
RFC 9457 fields:
  type      - URI identifying the problem type (default "about:blank" if unspecified)
  title     - short, human-readable summary (often the HTTP reason phrase)
  status    - the HTTP status code
  detail    - human-readable explanation specific to this occurrence
  instance  - URI identifying this specific occurrence (often the request path)
  + any number of custom extension properties (arbitrary key/value pairs)

Building one:
  ProblemDetail.forStatus(HttpStatus.NOT_FOUND)
  ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, "Product 99 not found")

  problem.setType(URI.create("https://api.example.com/errors/not-found"))
  problem.setTitle("Product not found")
  problem.setInstance(URI.create("/products/99"))
  problem.setProperty("productId", 99)     <- extension field

Content-Type on the wire: application/problem+json (or +xml)
  — distinct from plain application/json, signaling to clients
    "this response follows the Problem Details convention"
```

## 4. Diagram

<svg viewBox="0 0 720 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="220" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">ProblemDetail: standardized error shape</text>

  <rect x="40" y="50" width="640" height="140" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="60" y="72" fill="#6db33f" font-size="12">application/problem+json</text>
  <text x="60" y="95" fill="#79c0ff" font-size="11">type</text><text x="160" y="95" fill="#e6edf3" font-size="11">"https://api.example.com/errors/not-found"</text>
  <text x="60" y="113" fill="#79c0ff" font-size="11">title</text><text x="160" y="113" fill="#e6edf3" font-size="11">"Product not found"</text>
  <text x="60" y="131" fill="#79c0ff" font-size="11">status</text><text x="160" y="131" fill="#e6edf3" font-size="11">404</text>
  <text x="60" y="149" fill="#79c0ff" font-size="11">detail</text><text x="160" y="149" fill="#e6edf3" font-size="11">"Product 99 not found"</text>
  <text x="60" y="167" fill="#8b949e" font-size="11">productId (extension)</text><text x="280" y="167" fill="#e6edf3" font-size="11">99</text>

  <defs>
    <marker id="a14" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*A `ProblemDetail` response carries five standard fields plus any number of custom extension properties.*

## 5. Runnable example

### Level 1 — Basic

A single exception mapped to a basic `ProblemDetail`:

```java
// ProductController.java
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    static class ProductNotFoundException extends RuntimeException {
        ProductNotFoundException(long id) { super("Product " + id + " not found"); }
    }

    @GetMapping("/products/{id}")
    public String get(@PathVariable long id) {
        if (id != 1) throw new ProductNotFoundException(id);
        return "Drill";
    }

    @ExceptionHandler(ProductNotFoundException.class)
    public ProblemDetail handle(ProductNotFoundException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/99
# HTTP/1.1 404 Not Found
# Content-Type: application/problem+json
# {"type":"about:blank","title":"Not Found","status":404,"detail":"Product 99 not found","instance":"/products/99"}
```

`forStatusAndDetail` auto-fills `title` from the status's reason phrase (`"Not Found"`) and `instance` from the current request path — you only had to supply the status and the specific detail message.

### Level 2 — Intermediate

Customizing `type` and `title`, and adding extension properties for structured client-side handling:

```java
// ProductController.java (extended)
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.*;

import java.net.URI;

@RestController
public class ProductController {

    static class InsufficientStockException extends RuntimeException {
        final long productId; final int requested; final int available;
        InsufficientStockException(long productId, int requested, int available) {
            super("Insufficient stock");
            this.productId = productId; this.requested = requested; this.available = available;
        }
    }

    @PostMapping("/products/{id}/reserve")
    public String reserve(@PathVariable long id, @RequestParam int quantity) {
        int available = 3;
        if (quantity > available) throw new InsufficientStockException(id, quantity, available);
        return "reserved";
    }

    @ExceptionHandler(InsufficientStockException.class)
    public ProblemDetail handle(InsufficientStockException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, ex.getMessage());
        problem.setType(URI.create("https://api.example.com/errors/insufficient-stock"));
        problem.setTitle("Insufficient stock");
        problem.setProperty("productId", ex.productId);
        problem.setProperty("requested", ex.requested);
        problem.setProperty("available", ex.available);
        return problem;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -X POST "http://localhost:8080/products/1/reserve?quantity=10"
# HTTP/1.1 409 Conflict
# Content-Type: application/problem+json
# {"type":"https://api.example.com/errors/insufficient-stock","title":"Insufficient stock",
#  "status":409,"detail":"Insufficient stock",
#  "instance":"/products/1/reserve",
#  "productId":1,"requested":10,"available":3}
```

**What changed:** `setType` gives the error a dereferenceable identifier a client (or documentation) could look up for more detail on that error category. Extension properties (`productId`, `requested`, `available`) let a client programmatically react — e.g. showing "only 3 left" — without parsing the `detail` string.

### Level 3 — Advanced

Production pattern: a shared base for all domain errors producing consistent `ProblemDetail`s via `@ControllerAdvice`, validation errors folded into the same shape with a structured `errors` array, and a locale-aware `detail` message:

```java
// ApiException.java
public abstract class ApiException extends RuntimeException {
    private final org.springframework.http.HttpStatus status;
    private final String typeSuffix;
    protected ApiException(org.springframework.http.HttpStatus status, String typeSuffix, String message) {
        super(message);
        this.status = status;
        this.typeSuffix = typeSuffix;
    }
    public org.springframework.http.HttpStatus getStatus() { return status; }
    public String getTypeSuffix() { return typeSuffix; }
}

class ProductNotFoundException extends ApiException {
    ProductNotFoundException(long id) {
        super(org.springframework.http.HttpStatus.NOT_FOUND, "not-found", "Product " + id + " not found");
    }
}
```

```java
// GlobalExceptionHandler.java
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;

import java.net.URI;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final String BASE_TYPE_URI = "https://api.example.com/errors/";

    @ExceptionHandler(ApiException.class)
    public ProblemDetail handleApi(ApiException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(ex.getStatus(), ex.getMessage());
        problem.setType(URI.create(BASE_TYPE_URI + ex.getTypeSuffix()));
        problem.setTitle(ex.getClass().getSimpleName());
        return problem;
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        List<Map<String, String>> fieldErrors = ex.getBindingResult().getFieldErrors().stream()
            .map(fe -> Map.of("field", fe.getField(), "message", fe.getDefaultMessage()))
            .collect(Collectors.toList());

        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.BAD_REQUEST, "Validation failed for " + fieldErrors.size() + " field(s)");
        problem.setType(URI.create(BASE_TYPE_URI + "validation-failed"));
        problem.setTitle("Validation failed");
        problem.setProperty("errors", fieldErrors);   // structured array extension
        return problem;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/99
# 404 Not Found
# {"type":"https://api.example.com/errors/not-found","title":"ProductNotFoundException",
#  "status":404,"detail":"Product 99 not found","instance":"/products/99"}

curl -i -X POST http://localhost:8080/products -H "Content-Type: application/json" -d '{"name":"","price":-1}'
# 400 Bad Request
# {"type":"https://api.example.com/errors/validation-failed","title":"Validation failed",
#  "status":400,"detail":"Validation failed for 2 field(s)","instance":"/products",
#  "errors":[{"field":"name","message":"must not be blank"},{"field":"price","message":"must be positive"}]}
```

**What changed and why:**
- `ApiException` carries its own `typeSuffix`, so `handleApi` can build a distinct `type` URI per exception subclass without a giant `if/else` chain — adding a new domain error just means subclassing `ApiException`.
- `MethodArgumentNotValidException` (thrown automatically by `@Valid` with no local `BindingResult`, see the validation card) is folded into the *same* `ProblemDetail` shape as domain errors, with the field-level detail carried in a structured `errors` extension array — a client's error-handling code can treat every error response from this API uniformly, checking `status` and optionally reading `errors` when present.
- All error responses across the entire application funnel through this one `@RestControllerAdvice`, guaranteeing shape consistency — no individual controller can accidentally return a differently-shaped error body.

## 6. Walkthrough

**Request: `POST /products` with `{"name":"","price":-1}` (Level 3 code, validation fails).**

1. `DispatcherServlet` dispatches to the create handler. Before invoking it, Spring must construct the `@Valid @RequestBody` argument and run Bean Validation — `name` fails `@NotBlank`, `price` fails `@Positive`.
2. Because no `BindingResult` parameter is present in the handler's signature (a deliberate choice here, delegating all validation-error formatting to the advice), Spring throws `MethodArgumentNotValidException` and the handler method body never executes.
3. Spring's exception resolution searches for a matching `@ExceptionHandler` — finds `handleValidation(MethodArgumentNotValidException)` in `GlobalExceptionHandler`.
4. Inside `handleValidation`: `ex.getBindingResult().getFieldErrors()` returns two `FieldError` entries (`name`, `price`). These are mapped to a `List<Map<String,String>>`: `[{"field":"name","message":"must not be blank"}, {"field":"price","message":"must be positive"}]`.
5. A `ProblemDetail` is built: `status=400`, `detail="Validation failed for 2 field(s)"`, `type=".../validation-failed"`, `title="Validation failed"`, and the field list is attached via `setProperty("errors", fieldErrors)`.
6. Because the advice is `@RestControllerAdvice`, the returned `ProblemDetail` is serialized directly as the response body:
   ```
   HTTP/1.1 400 Bad Request
   Content-Type: application/problem+json

   {"type":"https://api.example.com/errors/validation-failed","title":"Validation failed",
    "status":400,"detail":"Validation failed for 2 field(s)","instance":"/products",
    "errors":[{"field":"name","message":"must not be blank"},{"field":"price","message":"must be positive"}]}
   ```
7. A client-side error handler can check `status === 400` and `type === ".../validation-failed"` to know this is specifically a validation error, then iterate `errors` to highlight the offending form fields — all without any string-parsing of `detail`.

## 7. Gotchas & takeaways

> **`Content-Type: application/problem+json` is distinct from `application/json`.** Some naive HTTP clients or older tooling that only checks for exactly `application/json` may fail to auto-parse a `ProblemDetail` response — verify your client-side HTTP libraries handle the `+json` structured suffix, or explicitly configure them to.

> **`ProblemDetail.forStatusAndDetail` auto-populates `instance` from the current request's path**, which is convenient but means the same exception thrown from different endpoints produces different `instance` values — don't rely on `instance` being a stable identifier across occurrences; that's what a correlation id extension property is for.

> **Extension properties added via `setProperty` are flattened directly into the top-level JSON object**, not nested under a wrapper key — `problem.setProperty("productId", 99)` produces `"productId": 99` at the same level as `status`/`detail`, not `"extensions": {"productId": 99}`. Choose extension property names carefully to avoid colliding with the standard RFC fields.

- `ProblemDetail` implements RFC 9457, giving APIs a standardized, tool-friendly error response shape instead of a bespoke one.
- `forStatusAndDetail` auto-fills `title` (from the status reason phrase) and `instance` (from the request path) — override them with `setTitle`/`setInstance`/`setType` for more specific errors.
- Use `setProperty` for structured extension data (field-level validation errors, domain-specific identifiers) that a client can act on programmatically.
- Centralizing `ProblemDetail` construction in a `@RestControllerAdvice` guarantees every error response across the API shares the same shape.
