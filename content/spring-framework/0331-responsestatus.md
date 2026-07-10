---
card: spring-framework
gi: 331
slug: responsestatus
title: "@ResponseStatus"
---

## 1. What it is

`@ResponseStatus` sets the HTTP status code for a response, either on a handler method (the status used whenever that method returns normally) or on an exception class (the status used automatically whenever that exception is thrown and reaches Spring's default exception handling, with no `@ExceptionHandler` needed).

```java
@ResponseStatus(HttpStatus.CREATED)
@PostMapping("/products")
public Product create(@RequestBody Product p) {
    return save(p);
}

@ResponseStatus(HttpStatus.NOT_FOUND)
class ProductNotFoundException extends RuntimeException { ... }
```

## 2. Why & when

Use `@ResponseStatus` on a **method** when the default `200 OK` isn't the right status for a successful response — e.g. `201 Created` for a resource-creation endpoint, `202 Accepted` for an async-processing endpoint, `204 No Content` for a delete that returns nothing.

Use `@ResponseStatus` on an **exception class** as a lightweight alternative to writing an `@ExceptionHandler`: when an exception is simple (just "map this type to this status, with an optional reason string"), annotating the class avoids boilerplate handler methods entirely. It's best for small, self-contained exception types; for anything needing a structured error body (JSON with fields), prefer `@ExceptionHandler`/`@ControllerAdvice`, since `@ResponseStatus` on its own only sets the status line, not a rich response body.

## 3. Core concept

```
@ResponseStatus on a METHOD:
  handler returns normally
       |
       v
  Spring sets the HTTP status line to the annotated value
  (instead of the default 200, or the ResponseEntity's own status if used)

@ResponseStatus on an EXCEPTION CLASS:
  handler throws MyException
       |
       v
  no @ExceptionHandler matches?
       |
       v
  Spring checks: does MyException carry @ResponseStatus?
       |
       v
  yes -> response status set to that value, body = default error page
         (reason string, if provided, becomes part of the error body)

Precedence: an @ExceptionHandler for the same exception type, if one
exists, takes priority over @ResponseStatus on the exception class.
```

## 4. Diagram

<svg viewBox="0 0 720 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="220" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">@ResponseStatus: two placements, two effects</text>

  <rect x="20" y="50" width="320" height="70" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="180" y="72" text-anchor="middle" fill="#6db33f">On a handler method</text>
  <text x="180" y="90" text-anchor="middle" fill="#8b949e" font-size="10">@ResponseStatus(CREATED)</text>
  <text x="180" y="106" text-anchor="middle" fill="#8b949e" font-size="10">successful return -> 201</text>

  <rect x="380" y="50" width="320" height="70" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="540" y="72" text-anchor="middle" fill="#79c0ff">On an exception class</text>
  <text x="540" y="90" text-anchor="middle" fill="#8b949e" font-size="10">@ResponseStatus(NOT_FOUND)</text>
  <text x="540" y="106" text-anchor="middle" fill="#8b949e" font-size="10">thrown, uncaught -> 404</text>

  <line x1="180" y1="120" x2="180" y2="160" stroke="#6db33f" marker-end="url(#a7)"/>
  <line x1="540" y1="120" x2="540" y2="160" stroke="#79c0ff" marker-end="url(#a7)"/>

  <rect x="60" y="160" width="240" height="40" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="180" y="184" text-anchor="middle" fill="#e6edf3" font-size="10">HTTP/1.1 201 Created</text>

  <rect x="420" y="160" width="240" height="40" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="540" y="184" text-anchor="middle" fill="#e6edf3" font-size="10">HTTP/1.1 404 Not Found</text>

  <defs>
    <marker id="a7" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The same annotation drives success-status on methods and error-status on exception classes.*

## 5. Runnable example

### Level 1 — Basic

`201 Created` for a POST endpoint, `204 No Content` for a DELETE endpoint:

```java
// ProductController.java
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@RestController
public class ProductController {

    record Product(long id, String name) {}
    private final Map<Long, Product> store = new ConcurrentHashMap<>();
    private final AtomicLong seq = new AtomicLong(1);

    @ResponseStatus(HttpStatus.CREATED)
    @PostMapping("/products")
    public Product create(@RequestParam String name) {
        long id = seq.getAndIncrement();
        Product p = new Product(id, name);
        store.put(id, p);
        return p;
    }

    @ResponseStatus(HttpStatus.NO_CONTENT)
    @DeleteMapping("/products/{id}")
    public void delete(@PathVariable long id) {
        store.remove(id);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -X POST "http://localhost:8080/products?name=Drill"
# HTTP/1.1 201 Created
# {"id":1,"name":"Drill"}

curl -i -X DELETE http://localhost:8080/products/1
# HTTP/1.1 204 No Content
# (empty body)
```

Without `@ResponseStatus`, both endpoints would return the default `200 OK`. Annotating the method lets the handler stay focused on returning the domain object — the status is declared once, separately from the return logic.

### Level 2 — Intermediate

`@ResponseStatus` on custom exception classes, including a `reason` string that becomes part of the default error response:

```java
// exceptions.java
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(value = HttpStatus.NOT_FOUND, reason = "Product not found")
class ProductNotFoundException extends RuntimeException {
    ProductNotFoundException(long id) { super("id=" + id); }
}

@ResponseStatus(value = HttpStatus.CONFLICT, reason = "Duplicate SKU")
class DuplicateSkuException extends RuntimeException {}
```

```java
// ProductController.java (extended)
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    @GetMapping("/products/{id}")
    public String get(@PathVariable long id) {
        if (id != 1) throw new ProductNotFoundException(id);
        return "Drill";
    }

    @PostMapping("/products/validate-sku")
    public String validateSku(@RequestParam String sku) {
        if ("DUPLICATE".equals(sku)) throw new DuplicateSkuException();
        return "OK";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/99
# HTTP/1.1 404 Not Found
# {"timestamp":"...","status":404,"error":"Not Found","message":"Product not found","path":"/products/99"}

curl -i -X POST "http://localhost:8080/products/validate-sku?sku=DUPLICATE"
# HTTP/1.1 409 Conflict
# {"timestamp":"...","status":409,"error":"Conflict","message":"Duplicate SKU","path":"..."}
```

**What changed:** No `@ExceptionHandler` method exists anywhere — Spring Boot's default error handling reads the `@ResponseStatus` metadata straight off the exception class and produces the standard error JSON body automatically, using `reason` as the `message` field. This is far less code than writing a matching `@ExceptionHandler` for every simple exception type.

### Level 3 — Advanced

Production concern: know when `@ResponseStatus` on an exception class is no longer enough (you need a structured, field-rich error body) and migrate to `@ExceptionHandler` — while keeping `@ResponseStatus` for the simple success-status cases where it remains the cleanest option:

```java
// ProductController.java (production version)
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/products")
public class ProductController {

    record Product(long id, String name, int stock) {}

    // Simple status change on success — @ResponseStatus remains the cleanest tool here
    @ResponseStatus(HttpStatus.ACCEPTED)
    @PostMapping("/{id}/reindex")
    public void triggerReindex(@PathVariable long id) {
        // enqueue async work; 202 tells the client "accepted, not yet done"
    }

    // A "simple" not-found case still works fine with @ResponseStatus on the exception
    @GetMapping("/{id}")
    public Product get(@PathVariable long id) {
        if (id != 1) throw new ProductNotFoundException(id);
        return new Product(1, "Drill", 3);
    }

    // A RICH error case (needs field-level detail) outgrows @ResponseStatus —
    // handled explicitly instead of relying on the exception's annotation
    @PostMapping("/{id}/reserve")
    public ResponseEntity<?> reserve(@PathVariable long id, @RequestParam int quantity) {
        int available = 3;
        if (quantity > available) {
            throw new InsufficientStockException(id, quantity, available);
        }
        return ResponseEntity.ok("reserved " + quantity);
    }

    @ExceptionHandler(InsufficientStockException.class)
    public ProblemDetail handleInsufficientStock(InsufficientStockException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, ex.getMessage());
        problem.setProperty("productId", ex.productId);
        problem.setProperty("requested", ex.requested);
        problem.setProperty("available", ex.available);
        return problem;
    }
}
```

```java
// exceptions.java (production version)
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(value = HttpStatus.NOT_FOUND, reason = "Product not found")
class ProductNotFoundException extends RuntimeException {
    ProductNotFoundException(long id) { super("id=" + id); }
}

// No @ResponseStatus here — deliberately handled via @ExceptionHandler instead,
// because the error body needs structured fields the annotation alone can't provide.
class InsufficientStockException extends RuntimeException {
    final long productId; final int requested; final int available;
    InsufficientStockException(long productId, int requested, int available) {
        super("Insufficient stock for product " + productId);
        this.productId = productId; this.requested = requested; this.available = available;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -X POST http://localhost:8080/products/1/reindex
# HTTP/1.1 202 Accepted

curl -i http://localhost:8080/products/99
# HTTP/1.1 404 Not Found  (simple default error body, from @ResponseStatus on the exception)

curl -i -X POST "http://localhost:8080/products/1/reserve?quantity=10"
# HTTP/1.1 409 Conflict
# {"status":409,"detail":"Insufficient stock for product 1",
#  "productId":1,"requested":10,"available":3}
```

**What changed and why:**
- `triggerReindex` keeps `@ResponseStatus(ACCEPTED)` — a plain method-level status change with no error handling involved, exactly what the annotation is best at.
- `ProductNotFoundException` keeps its class-level `@ResponseStatus` — the default error body (timestamp, status, message, path) is sufficient for a simple "not found."
- `InsufficientStockException` deliberately has **no** `@ResponseStatus` — instead an `@ExceptionHandler` builds a `ProblemDetail` with extra structured fields (`productId`, `requested`, `available`) that a client can programmatically use (e.g. to show "only 3 left" in the UI). This is the signal for when to graduate from `@ResponseStatus` to a real handler: the moment the error response needs more than a status code and a message string.

## 6. Walkthrough

**Request: `GET /products/99` (Level 3 code, product not found).**

1. `DispatcherServlet` dispatches to `get(99)`. Since `id != 1`, it throws `new ProductNotFoundException(99)`.
2. Spring's exception resolution checks for a matching `@ExceptionHandler` in the controller or any applicable advice — none exists for `ProductNotFoundException`.
3. It falls back further and inspects the exception class itself for `@ResponseStatus` metadata — finds `value = NOT_FOUND, reason = "Product not found"`.
4. `ResponseStatusExceptionResolver` (a built-in Spring component) sets the response status to `404` and delegates to the container's/Boot's default error page mechanism, which produces the standard error JSON using the `reason` as the message:
   ```
   HTTP/1.1 404 Not Found
   Content-Type: application/json

   {"timestamp":"2026-07-10T10:00:00Z","status":404,"error":"Not Found","message":"Product not found","path":"/products/99"}
   ```

**Request: `POST /products/1/reserve?quantity=10` (insufficient stock — the richer error case).**

1. `DispatcherServlet` dispatches to `reserve(1, 10)`. `available = 3`, `quantity (10) > available (3)` → throws `new InsufficientStockException(1, 10, 3)`.
2. Spring checks for a matching `@ExceptionHandler` — finds `handleInsufficientStock(InsufficientStockException)` right there in `ProductController`. This local handler takes priority; the exception's lack of `@ResponseStatus` is irrelevant since a handler exists.
3. `handleInsufficientStock` executes: builds a `ProblemDetail` with `status=409`, `detail="Insufficient stock for product 1"`, then adds three custom properties via `setProperty` — `productId`, `requested`, `available` — extra structured data no plain `@ResponseStatus` annotation could produce.
4. Response returned:
   ```
   HTTP/1.1 409 Conflict
   Content-Type: application/problem+json

   {"status":409,"detail":"Insufficient stock for product 1","productId":1,"requested":10,"available":3}
   ```

The client-side code handling this response can read `available` directly (`3`) to show a precise message ("Only 3 left in stock") — something a plain string `reason` from `@ResponseStatus` could never provide structurally.

## 7. Gotchas & takeaways

> **`@ResponseStatus` on an exception class is silently ignored if any `@ExceptionHandler` (local or in an advice) matches that exception type.** This is by design — handlers take priority — but it can confuse newcomers who add `@ResponseStatus` to an exception, don't see the expected status, and don't realize a broader catch-all handler (like `@ExceptionHandler(Exception.class)`) is intercepting it first.

> **`@ResponseStatus` on a method is overridden if the method itself returns a `ResponseEntity` with an explicit status.** `ResponseEntity.status(...)` always wins over the method-level annotation — don't set both and expect the annotation to apply; pick one mechanism per method.

> **The default error body produced by `@ResponseStatus`'s `reason` is Spring Boot's generic error shape** (`timestamp`, `status`, `error`, `message`, `path`) — it is not customizable per exception beyond the message text. The moment you need extra fields, custom JSON shape, or conditional logic, you must switch to `@ExceptionHandler`.

- Use `@ResponseStatus` on a method for simple success-status overrides (`201`, `202`, `204`).
- Use `@ResponseStatus` on an exception class only for simple, message-only error cases — it's the lightest-weight option, not the most flexible.
- The moment an error response needs structured fields or conditional formatting, migrate that exception to an `@ExceptionHandler`/`@ControllerAdvice` instead.
- `@ExceptionHandler` (local or global) always takes priority over an exception class's own `@ResponseStatus`.
