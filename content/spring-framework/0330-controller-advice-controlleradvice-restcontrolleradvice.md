---
card: spring-framework
gi: 330
slug: controller-advice-controlleradvice-restcontrolleradvice
title: "Controller advice (@ControllerAdvice / @RestControllerAdvice)"
---

## 1. What it is

`@ControllerAdvice` is a class-level annotation that turns a class into a **global** helper applied across many (or all) controllers — most commonly for centralizing `@ExceptionHandler` methods, but also `@ModelAttribute` and `@InitBinder` methods. `@RestControllerAdvice` is a shortcut combining `@ControllerAdvice` and `@ResponseBody`, so handler return values in it are serialized directly to the response body (JSON/XML), matching how `@RestController` behaves for regular request handlers.

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ProductNotFoundException.class)
    public ResponseEntity<String> handleNotFound(ProductNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(ex.getMessage());
    }
}
```

## 2. Why & when

Controller-local `@ExceptionHandler` methods (previous card) only cover exceptions thrown within that one controller. Real applications have many controllers that all need consistent handling for common exception types — validation failures, "not found" errors, access-denied errors, unexpected runtime errors. Repeating the same handler methods in every controller is duplication and, worse, a source of inconsistent error response shapes as the codebase grows.

Use `@ControllerAdvice`/`@RestControllerAdvice` to:
- Centralize exception-to-HTTP-response mapping across the whole application (or a targeted subset via `basePackages`, `assignableTypes`, or annotation-based selectors).
- Add shared model attributes to every view-rendering controller (see the `Model`/`ModelMap` card).
- Apply shared `@InitBinder` customizations globally (see the `DataBinder` card).
- Keep individual controllers focused purely on their own business logic, not error-formatting boilerplate.

## 3. Core concept

```
@RestControllerAdvice targeting scope (default: ALL controllers in the app)

           ┌─────────────────────────────┐
           │   @RestControllerAdvice      │
           │   GlobalExceptionHandler      │
           │                                │
           │   @ExceptionHandler(NotFound)  │
           │   @ExceptionHandler(Validation)│
           │   @ExceptionHandler(Exception) │  <- catch-all
           └───────────────┬────────────────┘
                            │ applies to
        ┌───────────────────┼───────────────────┐
        v                    v                    v
ProductController   OrderController      UserController
  (no local          (no local            (local override
   handlers needed)   handlers needed)     for one specific
                                            exception type)

Resolution order when an exception is thrown in a controller method:
  1. Check LOCAL @ExceptionHandler in that same controller — most specific wins if present
  2. Fall back to matching @ExceptionHandler in an applicable @ControllerAdvice
  3. Fall back to Spring Boot's default error handling
```

A controller-local handler always takes priority over an advice's handler for the same exception type — advice is the fallback layer, not an override mechanism.

## 4. Diagram

<svg viewBox="0 0 740 260" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="260" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">One @RestControllerAdvice serves many controllers</text>

  <rect x="270" y="40" width="200" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="62" text-anchor="middle" fill="#6db33f">@RestControllerAdvice</text>
  <text x="370" y="80" text-anchor="middle" fill="#8b949e" font-size="10">GlobalExceptionHandler</text>

  <line x1="330" y1="100" x2="150" y2="150" stroke="#8b949e" marker-end="url(#a6)"/>
  <line x1="370" y1="100" x2="370" y2="150" stroke="#8b949e" marker-end="url(#a6)"/>
  <line x1="410" y1="100" x2="590" y2="150" stroke="#8b949e" marker-end="url(#a6)"/>

  <rect x="60" y="150" width="180" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="180" text-anchor="middle" fill="#79c0ff" font-size="11">ProductController</text>

  <rect x="280" y="150" width="180" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="370" y="180" text-anchor="middle" fill="#79c0ff" font-size="11">OrderController</text>

  <rect x="500" y="150" width="180" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="590" y="180" text-anchor="middle" fill="#79c0ff" font-size="11">UserController</text>

  <text x="370" y="230" text-anchor="middle" fill="#8b949e" font-size="10">a controller-local @ExceptionHandler still wins over the advice's, for that controller only</text>

  <defs>
    <marker id="a6" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*A single advice class handles exceptions from every controller unless a controller declares its own more specific handler.*

## 5. Runnable example

### Level 1 — Basic

A global handler covering two controllers with no local exception handlers:

```java
// exceptions.java
class ProductNotFoundException extends RuntimeException {
    ProductNotFoundException(long id) { super("Product " + id + " not found"); }
}
class OrderNotFoundException extends RuntimeException {
    OrderNotFoundException(long id) { super("Order " + id + " not found"); }
}
```

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {
    @GetMapping("/products/{id}")
    public String get(@PathVariable long id) {
        if (id != 1) throw new ProductNotFoundException(id);
        return "Drill";
    }
}
```

```java
// OrderController.java
import org.springframework.web.bind.annotation.*;

@RestController
public class OrderController {
    @GetMapping("/orders/{id}")
    public String get(@PathVariable long id) {
        if (id != 1) throw new OrderNotFoundException(id);
        return "Order #1";
    }
}
```

```java
// GlobalExceptionHandler.java
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler({ProductNotFoundException.class, OrderNotFoundException.class})
    public ResponseEntity<String> handleNotFound(RuntimeException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(ex.getMessage());
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/99
# 404 Not Found
# Product 99 not found

curl -i http://localhost:8080/orders/99
# 404 Not Found
# Order 99 not found
```

Neither `ProductController` nor `OrderController` declares any `@ExceptionHandler` — one advice class in `GlobalExceptionHandler` covers both, and any future controller in the app automatically inherits this behavior too.

### Level 2 — Intermediate

Scoping an advice to a package, and a controller-local override taking priority for one specific case:

```java
// GlobalExceptionHandler.java (extended)
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestControllerAdvice(basePackages = "com.example.shop.api")   // only applies to controllers in this package
public class GlobalExceptionHandler {

    @ExceptionHandler(ProductNotFoundException.class)
    public ResponseEntity<String> handleNotFound(ProductNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body("shop: " + ex.getMessage());
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<String> handleGeneric(Exception ex) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("shop: unexpected error");
    }
}
```

```java
// AdminProductController.java — has its OWN handler that overrides the advice for this exception
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
public class AdminProductController {

    @GetMapping("/admin/products/{id}")
    public String get(@PathVariable long id) {
        if (id != 1) throw new ProductNotFoundException(id);
        return "Drill (admin view)";
    }

    // Local handler wins over the global advice's handler for THIS controller only
    @ExceptionHandler(ProductNotFoundException.class)
    public ResponseEntity<String> handleNotFoundLocally(ProductNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body("admin: " + ex.getMessage());
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/99
# 404 Not Found
# shop: Product 99 not found        <- from the global advice

curl -i http://localhost:8080/admin/products/99
# 404 Not Found
# admin: Product 99 not found       <- from the LOCAL handler, which takes priority
```

**What changed:** `basePackages` restricts which controllers the advice applies to — useful in large applications with genuinely different API surfaces (public shop API vs. internal admin API) needing different error conventions. `AdminProductController`'s local `@ExceptionHandler` for the exact same exception type wins over the advice for that controller, demonstrating the priority rule.

### Level 3 — Advanced

Production pattern: a single advice combining validation error handling, a domain error hierarchy, and a structured `ProblemDetail` response with a correlation id for support/debugging, applied application-wide:

```java
// ApiException.java — base class for all domain exceptions, carries an HTTP status
public abstract class ApiException extends RuntimeException {
    private final org.springframework.http.HttpStatus status;
    protected ApiException(org.springframework.http.HttpStatus status, String message) {
        super(message);
        this.status = status;
    }
    public org.springframework.http.HttpStatus getStatus() { return status; }
}

class ProductNotFoundException extends ApiException {
    ProductNotFoundException(long id) {
        super(org.springframework.http.HttpStatus.NOT_FOUND, "Product " + id + " not found");
    }
}
class InsufficientStockException extends ApiException {
    InsufficientStockException(long id) {
        super(org.springframework.http.HttpStatus.CONFLICT, "Product " + id + " out of stock");
    }
}
```

```java
// GlobalExceptionHandler.java (production version)
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;

import java.util.UUID;
import java.util.stream.Collectors;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    // One handler for the ENTIRE domain exception hierarchy — status comes from the exception itself
    @ExceptionHandler(ApiException.class)
    public ProblemDetail handleApiException(ApiException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(ex.getStatus(), ex.getMessage());
        problem.setTitle(ex.getClass().getSimpleName());
        return problem;
    }

    // Bean Validation failures thrown when @Valid has no local BindingResult
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        String detail = ex.getBindingResult().getFieldErrors().stream()
            .map(FieldError::getDefaultMessage)
            .collect(Collectors.joining("; "));
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, detail);
        problem.setTitle("Validation failed");
        return problem;
    }

    // Catch-all: log with a correlation id, never expose internals
    @ExceptionHandler(Exception.class)
    public ProblemDetail handleUnexpected(Exception ex, WebRequest request) {
        String correlationId = UUID.randomUUID().toString();
        log.error("[{}] Unhandled exception on {}", correlationId, request.getDescription(false), ex);
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.INTERNAL_SERVER_ERROR, "Unexpected error. Reference: " + correlationId);
        problem.setTitle("Internal error");
        return problem;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/99/reserve
# 409 Conflict  {"title":"InsufficientStockException","status":409,"detail":"Product 99 out of stock"}

curl -i -X POST http://localhost:8080/products -H "Content-Type: application/json" -d '{"name":""}'
# 400 Bad Request  {"title":"Validation failed","status":400,"detail":"name is required"}

# Any uncaught bug anywhere in the app:
# 500 Internal Server Error  {"title":"Internal error","status":500,"detail":"Unexpected error. Reference: 7c9e...ff2"}
# server log: "[7c9e...ff2] Unhandled exception on uri=/products/-1" + full stack trace
```

**What changed and why:**
- A single `ApiException` base class lets ONE handler (`handleApiException`) cover an entire, growing family of domain exceptions — adding a new exception type just means subclassing `ApiException` with the right status, no new handler method required.
- `MethodArgumentNotValidException` is what Spring throws automatically when `@Valid` fails and there's **no** `BindingResult` parameter (see the validation card) — handling it here means individual controllers don't need `BindingResult` boilerplate at all; they can just declare `@Valid` and let the advice format the error.
- The correlation id logged alongside the full exception (and returned to the client in the safe message) lets support/ops correlate a user's bug report with the exact server-side log entry, without ever exposing the actual exception message or stack trace externally.

## 6. Walkthrough

**Request: `GET /products/99/reserve` (Level 3 code, product exists but has no stock).**

1. `DispatcherServlet` dispatches to the relevant controller method, which internally throws `new InsufficientStockException(99)` — a subclass of `ApiException` carrying `HttpStatus.CONFLICT`.
2. Spring's exception resolution machinery checks the throwing controller for a local `@ExceptionHandler` matching `InsufficientStockException` or a superclass — none exists locally.
3. It falls back to `GlobalExceptionHandler` (a `@RestControllerAdvice` with no `basePackages` restriction, so it applies globally). `handleApiException(ApiException)` matches, because `InsufficientStockException` **is-a** `ApiException`.
4. `handleApiException` executes: reads `ex.getStatus()` → `CONFLICT`, `ex.getMessage()` → `"Product 99 out of stock"`. Builds a `ProblemDetail` with `status=409`, `title="InsufficientStockException"`, `detail="Product 99 out of stock"`.
5. Because the advice is `@RestControllerAdvice` (implies `@ResponseBody`), the returned `ProblemDetail` is serialized directly to the response body via the configured `HttpMessageConverter` (Jackson):
   ```
   HTTP/1.1 409 Conflict
   Content-Type: application/problem+json

   {"title":"InsufficientStockException","status":409,"detail":"Product 99 out of stock"}
   ```

**Request causing an unanticipated exception (e.g. a `NullPointerException` from a bug deep in a service layer):**

1. No `ApiException` subclass matches — the thrown exception is a plain `NullPointerException`.
2. Neither `handleApiException` nor `handleValidation` matches its type. Spring falls back to `handleUnexpected(Exception, WebRequest)`, the most general applicable handler.
3. A random `correlationId` is generated. `log.error("[{}] Unhandled exception on {}", correlationId, ..., ex)` writes the full exception with stack trace to the application log, tagged with that id.
4. A `ProblemDetail` with `status=500` and `detail="Unexpected error. Reference: <correlationId>"` is returned — the client sees only the reference id, never the real cause.
5. Later, when the user reports "I got error reference 7c9e...ff2", an operator greps the logs for that id and finds the exact stack trace instantly — without the client having exposed any internal information.

## 7. Gotchas & takeaways

> **A controller-local `@ExceptionHandler` always wins over an advice's handler for the same exception type**, even if the advice's handler is "more specific" in some abstract sense — locality trumps everything. This is useful for overrides but can also cause confusing behavior if a forgotten local handler shadows an intended global one.

> **Multiple `@ControllerAdvice` beans with overlapping exception mappings and no explicit `@Order` produce non-deterministic-feeling results** — Spring picks one based on bean definition order, which is fragile. If you have more than one advice class, scope them with `basePackages`/`assignableTypes` so their responsibilities don't overlap, or use `@Order` to make precedence explicit.

> **`@RestControllerAdvice` implies `@ResponseBody` on every handler in it.** If you actually want a mix of view-returning and body-returning handlers in one advice, use plain `@ControllerAdvice` and annotate individual methods with `@ResponseBody` as needed — don't fight the annotation's default.

- `@ControllerAdvice` also supports `@ModelAttribute` and `@InitBinder` methods, not just `@ExceptionHandler` — it's a general cross-cutting-concern mechanism for controllers, not exception handling only.
- Scope advice classes with `basePackages`, `assignableTypes`, or `annotations` when different parts of an application need different error-handling conventions (e.g. a public API vs. an internal admin API).
- A shared base exception class (like `ApiException` carrying its own `HttpStatus`) lets one handler method cover an entire, growing exception hierarchy.
- Never return raw exception messages or stack traces to the client for unanticipated errors — log the detail server-side (ideally with a correlation id) and return a generic, safe message.
