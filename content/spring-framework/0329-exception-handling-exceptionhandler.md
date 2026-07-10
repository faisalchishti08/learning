---
card: spring-framework
gi: 329
slug: exception-handling-exceptionhandler
title: "Exception handling (@ExceptionHandler)"
---

## 1. What it is

`@ExceptionHandler` marks a method that handles exceptions thrown by request-handling code, converting them into a controlled HTTP response instead of letting the exception propagate to a generic error page or stack trace. It can be declared inside a single controller (scoped to that controller only) or inside a `@ControllerAdvice` class (applies globally — see the next card).

```java
@RestController
public class ProductController {

    @GetMapping("/products/{id}")
    public Product get(@PathVariable long id) {
        return repository.findById(id).orElseThrow(() -> new ProductNotFoundException(id));
    }

    @ExceptionHandler(ProductNotFoundException.class)
    public ResponseEntity<String> handleNotFound(ProductNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(ex.getMessage());
    }
}
```

## 2. Why & when

Without `@ExceptionHandler`, an uncaught exception in a handler method propagates up and Spring Boot's default `BasicErrorController` produces a generic `500` response (a JSON blob with `timestamp`, `status`, `error`, `path` — no domain-specific detail). That's rarely what an API consumer needs.

Use `@ExceptionHandler` to:
- Map specific exception types to specific HTTP status codes (`ProductNotFoundException` → `404`, `InsufficientStockException` → `409`).
- Return a consistent, structured error body (error code, message, field details) instead of a stack trace.
- Keep business logic clean — throw exceptions where problems are detected, handle the HTTP translation in one place.
- Avoid defensive `try/catch` scattered through every handler method.

A method-local `@ExceptionHandler` is right for exceptions specific to one controller's domain; shared exception types (validation errors, generic `RuntimeException` fallback) belong in a global `@ControllerAdvice`.

## 3. Core concept

```
Handler method throws:
  ProductNotFoundException("id 99 not found")
                |
                v
  Spring searches for a matching @ExceptionHandler, in order of specificity:
    1. @ExceptionHandler(ProductNotFoundException.class) in the SAME controller
    2. @ExceptionHandler(ProductNotFoundException.class) in a @ControllerAdvice
    3. @ExceptionHandler(more general superclass) in either scope
    4. Spring Boot's default error handling (500, generic body)
                |
                v
  Matching handler method invoked with the exception as argument,
  returns ResponseEntity (or view name, or @ResponseBody object)
                |
                v
  That return value becomes the actual HTTP response
```

Exception-type matching picks the **most specific** applicable handler — if you have handlers for both `ProductNotFoundException` and its superclass `RuntimeException`, the more specific one wins.

## 4. Diagram

<svg viewBox="0 0 720 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="220" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Exception thrown → matched to @ExceptionHandler → HTTP response</text>

  <rect x="20" y="50" width="180" height="60" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="72" text-anchor="middle" fill="#79c0ff">Controller method</text>
  <text x="110" y="90" text-anchor="middle" fill="#8b949e" font-size="10">throws NotFoundException</text>

  <line x1="200" y1="80" x2="260" y2="80" stroke="#8b949e" marker-end="url(#a5)"/>

  <rect x="260" y="50" width="200" height="60" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="360" y="72" text-anchor="middle" fill="#8b949e">exception resolver</text>
  <text x="360" y="90" text-anchor="middle" fill="#8b949e" font-size="10">finds best-match handler</text>

  <line x1="460" y1="80" x2="520" y2="80" stroke="#8b949e" marker-end="url(#a5)"/>

  <rect x="520" y="50" width="180" height="60" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="610" y="72" text-anchor="middle" fill="#6db33f">@ExceptionHandler</text>
  <text x="610" y="90" text-anchor="middle" fill="#8b949e" font-size="10">builds 404 response</text>

  <line x1="610" y1="110" x2="360" y2="150" stroke="#6db33f" marker-end="url(#a5)"/>
  <rect x="200" y="150" width="320" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="180" text-anchor="middle" fill="#e6edf3" font-size="11">HTTP/1.1 404 Not Found — "id 99 not found"</text>

  <defs>
    <marker id="a5" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The exception resolver picks the most specific matching handler and its return value becomes the response.*

## 5. Runnable example

### Level 1 — Basic

A single custom exception mapped to `404`:

```java
// ProductController.java
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
public class ProductController {

    static class ProductNotFoundException extends RuntimeException {
        ProductNotFoundException(long id) { super("Product " + id + " not found"); }
    }

    @GetMapping("/products/{id}")
    public Map<String, Object> get(@PathVariable long id) {
        if (id != 1) throw new ProductNotFoundException(id);
        return Map.of("id", id, "name", "Drill");
    }

    @ExceptionHandler(ProductNotFoundException.class)
    public ResponseEntity<Map<String, String>> handleNotFound(ProductNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", ex.getMessage()));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/1
# 200 OK  {"id":1,"name":"Drill"}

curl -i http://localhost:8080/products/99
# 404 Not Found  {"error":"Product 99 not found"}
```

Throwing `ProductNotFoundException` inside `get()` doesn't crash the request — Spring intercepts it, finds the matching `@ExceptionHandler` in the same controller, and uses its return value as the response.

### Level 2 — Intermediate

Multiple exception types mapped to different statuses, plus handling several exception classes with one method:

```java
// ProductController.java (extended)
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
public class ProductController {

    static class ProductNotFoundException extends RuntimeException {
        ProductNotFoundException(long id) { super("Product " + id + " not found"); }
    }
    static class InsufficientStockException extends RuntimeException {
        InsufficientStockException(long id, int requested, int available) {
            super("Product " + id + ": requested " + requested + ", only " + available + " available");
        }
    }
    static class InvalidPriceException extends RuntimeException {
        InvalidPriceException(String msg) { super(msg); }
    }

    @PostMapping("/products/{id}/reserve")
    public Map<String, Object> reserve(@PathVariable long id, @RequestParam int quantity) {
        if (id != 1) throw new ProductNotFoundException(id);
        if (quantity > 5) throw new InsufficientStockException(id, quantity, 5);
        return Map.of("id", id, "reserved", quantity);
    }

    @ExceptionHandler(ProductNotFoundException.class)
    public ResponseEntity<Map<String, String>> handleNotFound(ProductNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", ex.getMessage()));
    }

    // One handler for multiple related exception types
    @ExceptionHandler({InsufficientStockException.class, InvalidPriceException.class})
    public ResponseEntity<Map<String, String>> handleConflict(RuntimeException ex) {
        return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("error", ex.getMessage()));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -X POST "http://localhost:8080/products/1/reserve?quantity=3"
# 200 OK  {"id":1,"reserved":3}

curl -i -X POST "http://localhost:8080/products/1/reserve?quantity=10"
# 409 Conflict  {"error":"Product 1: requested 10, only 5 available"}

curl -i -X POST "http://localhost:8080/products/99/reserve?quantity=1"
# 404 Not Found  {"error":"Product 99 not found"}
```

**What changed:** `handleConflict` accepts an array of exception classes and a common supertype parameter (`RuntimeException`) — one method services two distinct business error conditions that both deserve `409 Conflict`, avoiding duplicate handler methods with identical bodies.

### Level 3 — Advanced

Production concern: a structured, consistent error response shape (error code, message, timestamp, request path) shared across all exceptions, using `ProblemDetail` (Spring 6 / Spring Boot 3's built-in RFC 7807 support) plus logging of unexpected errors without leaking internals to the client:

```java
// ProductController.java (production version)
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.context.request.WebRequest;

import java.net.URI;
import java.util.Map;

@RestController
public class ProductController {

    private static final Logger log = LoggerFactory.getLogger(ProductController.class);

    static class ProductNotFoundException extends RuntimeException {
        ProductNotFoundException(long id) { super("Product " + id + " not found"); }
    }

    @GetMapping("/products/{id}")
    public Map<String, Object> get(@PathVariable long id) {
        if (id < 0) throw new IllegalStateException("corrupted inventory index");   // simulated bug
        if (id != 1) throw new ProductNotFoundException(id);
        return Map.of("id", id, "name", "Drill");
    }

    @ExceptionHandler(ProductNotFoundException.class)
    public ProblemDetail handleNotFound(ProductNotFoundException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        problem.setType(URI.create("https://api.example.com/errors/not-found"));
        problem.setTitle("Product not found");
        return problem;
    }

    // Catch-all for anything unanticipated — never leak the raw exception message to the client
    @ExceptionHandler(Exception.class)
    public ProblemDetail handleUnexpected(Exception ex, WebRequest request) {
        log.error("Unhandled exception on {}: {}", request.getDescription(false), ex.getMessage(), ex);
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.INTERNAL_SERVER_ERROR, "An unexpected error occurred. Please contact support.");
        problem.setTitle("Internal error");
        return problem;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/99
# 404 Not Found
# Content-Type: application/problem+json
# {"type":"https://api.example.com/errors/not-found","title":"Product not found",
#  "status":404,"detail":"Product 99 not found"}

curl -i http://localhost:8080/products/-1
# 500 Internal Server Error
# {"title":"Internal error","status":500,
#  "detail":"An unexpected error occurred. Please contact support."}
# (server log shows the real "corrupted inventory index" message + stack trace)
```

`id < 0` is checked first so it triggers the simulated bug (`IllegalStateException`) before the not-found check runs; any other id besides `1` falls through to the not-found branch.

**What changed and why:**
- `ProblemDetail` (RFC 7807 "Problem Details for HTTP APIs") gives every error response a consistent, standardized shape — `type`, `title`, `status`, `detail` — that API clients and tooling can parse uniformly instead of a bespoke per-team JSON schema.
- The catch-all `@ExceptionHandler(Exception.class)` guarantees no exception ever reaches the client as a raw stack trace or leaks internal detail like `"corrupted inventory index"` — that detail goes to the server log (with full stack trace via `log.error(..., ex)`), while the client only sees a generic, safe message.
- Because Spring matches the **most specific** handler first, `ProductNotFoundException` still gets its dedicated `404` response — the catch-all only fires for exception types with no more specific handler.

## 6. Walkthrough

**Request: `GET /products/99` (Level 3 code — triggers the expected `ProductNotFoundException`).**

1. `DispatcherServlet` dispatches to `ProductController.get(99)`.
2. Inside `get`, `id < 0` is `false` (skip), `id != 1` is `true` → throws `ProductNotFoundException("Product 99 not found")`.
3. Spring's exception resolution machinery catches the thrown exception before it reaches the servlet container's default error handling.
4. It searches `@ExceptionHandler` methods declared in `ProductController`, matching by exception type: `ProductNotFoundException` exactly matches `handleNotFound(ProductNotFoundException)` — most specific match wins over the catch-all `handleUnexpected(Exception)`.
5. `handleNotFound` executes: builds a `ProblemDetail` with `status=404`, `detail="Product 99 not found"`, `type=".../not-found"`.
6. Spring serializes the returned `ProblemDetail` to the response body as `application/problem+json`:
   ```
   HTTP/1.1 404 Not Found
   Content-Type: application/problem+json

   {"type":"https://api.example.com/errors/not-found","title":"Product not found","status":404,"detail":"Product 99 not found"}
   ```

**Request: `GET /products/-1` (triggers the unanticipated `IllegalStateException`).**

1. `DispatcherServlet` dispatches to `ProductController.get(-1)`.
2. Inside `get`, `id < 0` is `true` → throws `IllegalStateException("corrupted inventory index")` immediately, before the not-found check runs.
3. Spring's exception resolver searches `@ExceptionHandler` methods again. There is no handler declared for `IllegalStateException` specifically, so it falls back to the most general applicable handler: `handleUnexpected(Exception, WebRequest)`.
4. `handleUnexpected` runs: `log.error(...)` writes the real message and full stack trace to the server log (visible to operators, not the client), then builds a generic `ProblemDetail` with `status=500` and the safe message `"An unexpected error occurred. Please contact support."` — no mention of `"corrupted inventory index"`.
5. Response sent to the client:
   ```
   HTTP/1.1 500 Internal Server Error
   Content-Type: application/problem+json

   {"title":"Internal error","status":500,"detail":"An unexpected error occurred. Please contact support."}
   ```

This is the key benefit of layering a specific handler (`ProductNotFoundException` → `404`) alongside a catch-all (`Exception` → `500`): expected domain errors get precise, informative responses, while truly unexpected bugs are contained, logged for diagnosis, and never leak implementation detail to the client.

## 7. Gotchas & takeaways

> **A method-local `@ExceptionHandler` only covers exceptions thrown within that same controller.** If ten controllers each need to handle `ProductNotFoundException`, either duplicate the handler ten times or (better) move it to a `@ControllerAdvice` — see the next card.

> **Order of handler declaration doesn't matter; specificity does.** Spring always picks the most specific matching exception type in the class hierarchy, regardless of which handler method is declared first in the source file.

> **A catch-all `@ExceptionHandler(Exception.class)` can accidentally swallow exceptions Spring itself relies on for control flow** (like `ResponseStatusException` used for redirects, or exceptions from async processing). Test that framework-level exception handling (e.g. `404` for unmapped URLs) still works correctly once you add a broad catch-all.

- Method-local `@ExceptionHandler` methods are scoped to the declaring controller only.
- `ProblemDetail` (Spring 6+) is the modern, standardized way to shape error responses — prefer it over ad hoc `Map`/DTO error bodies for new code.
- Always log the real exception detail server-side even when you return a sanitized message to the client — don't lose the diagnostic information.
- Multiple exception types can share one handler via `@ExceptionHandler({TypeA.class, TypeB.class})` when they deserve the same HTTP status and response shape.
