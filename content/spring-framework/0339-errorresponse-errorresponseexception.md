---
card: spring-framework
gi: 339
slug: errorresponse-errorresponseexception
title: "ErrorResponse / ErrorResponseException"
---

## 1. What it is

`ErrorResponse` is an interface Spring exceptions can implement to expose a `ProblemDetail`-shaped error response directly from the exception itself — no `@ExceptionHandler` required, because Spring's built-in exception resolvers know how to read it. `ErrorResponseException` is a ready-to-use `RuntimeException` base class that already implements `ErrorResponse`, letting you build custom exceptions that automatically produce a `ProblemDetail` response the moment they're thrown, uncaught, from a controller.

```java
class ProductNotFoundException extends ErrorResponseException {
    ProductNotFoundException(long id) {
        super(HttpStatus.NOT_FOUND, asProblemDetail(id), null);
    }
    private static ProblemDetail asProblemDetail(long id) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, "Product " + id + " not found");
    }
}
```

Throwing `new ProductNotFoundException(99)` from any controller produces a full `ProblemDetail` `404` response — with zero `@ExceptionHandler` code anywhere.

## 2. Why & when

The `ProblemDetail` card showed building a `ProblemDetail` inside an `@ExceptionHandler` method. `ErrorResponse`/`ErrorResponseException` moves that construction logic **into the exception class itself**, so the exception is self-describing — it knows its own HTTP status and problem detail, and Spring's framework-level exception handling (specifically `ResponseEntityExceptionHandler`, which Spring Boot wires in automatically) picks it up without any handler method needing to exist.

This is also exactly how Spring's **own built-in exceptions** work: `HttpMediaTypeNotAcceptableException`, `MissingServletRequestParameterException`, `MethodArgumentTypeMismatchException`, and many others all implement `ErrorResponse`, which is why they already produce sensible `ProblemDetail` responses automatically, even in an application with zero custom exception handling.

Use `ErrorResponseException` when:
- You want a custom exception to be entirely self-contained — its `ProblemDetail` shape travels with it, rather than living in a separate handler method that must stay in sync.
- You're extending/customizing how one of Spring's built-in framework exceptions renders, by overriding `ResponseEntityExceptionHandler` methods (see Level 3).
- You want new exception types added to a codebase to "just work" with existing global exception infrastructure without writing a matching `@ExceptionHandler` for each one.

## 3. Core concept

```
ErrorResponse interface:
  HttpStatusCode getStatusCode()
  ProblemDetail  getBody()
  HttpHeaders    getHeaders()      (optional, defaults empty)

ErrorResponseException implements ErrorResponse — a ready base class.

Exception thrown, uncaught by any @ExceptionHandler
        |
        v
Does the exception implement ErrorResponse?
        |
   yes -+-------------------------+-- no
        v                          v
ResponseEntityExceptionHandler   fall through to generic
reads getStatusCode()/getBody()  error handling (no
automatically, no handler         ProblemDetail shape)
method needed
        |
        v
ProblemDetail response produced automatically

This is exactly the mechanism behind Spring's OWN built-in exceptions
(missing parameter, type mismatch, unsupported media type, etc.) —
they all implement ErrorResponse already.
```

## 4. Diagram

<svg viewBox="0 0 720 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="220" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Self-describing exceptions via ErrorResponse</text>

  <rect x="20" y="50" width="260" height="80" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="72" text-anchor="middle" fill="#79c0ff">ProductNotFoundException</text>
  <text x="150" y="90" text-anchor="middle" fill="#8b949e" font-size="10">extends ErrorResponseException</text>
  <text x="150" y="106" text-anchor="middle" fill="#8b949e" font-size="10">carries its own ProblemDetail</text>

  <line x1="280" y1="90" x2="340" y2="90" stroke="#8b949e" marker-end="url(#a15)"/>

  <rect x="340" y="50" width="340" height="80" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="510" y="72" text-anchor="middle" fill="#6db33f">ResponseEntityExceptionHandler</text>
  <text x="510" y="90" text-anchor="middle" fill="#8b949e" font-size="10">(built into Spring Boot)</text>
  <text x="510" y="106" text-anchor="middle" fill="#8b949e" font-size="10">reads getStatusCode()/getBody() directly</text>

  <line x1="510" y1="130" x2="510" y2="160" stroke="#6db33f" marker-end="url(#a15)"/>
  <rect x="330" y="160" width="360" height="45" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="510" y="187" text-anchor="middle" fill="#e6edf3" font-size="10">404 + ProblemDetail — no @ExceptionHandler written</text>

  <defs>
    <marker id="a15" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The exception itself supplies status and body; Spring's built-in handler reads them off automatically.*

## 5. Runnable example

### Level 1 — Basic

A custom exception that needs no `@ExceptionHandler`:

```java
// ProductNotFoundException.java
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.ErrorResponseException;

public class ProductNotFoundException extends ErrorResponseException {
    public ProductNotFoundException(long id) {
        super(HttpStatus.NOT_FOUND, asProblemDetail(id), null);
    }
    private static ProblemDetail asProblemDetail(long id) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, "Product " + id + " not found");
    }
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

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/99
# HTTP/1.1 404 Not Found
# Content-Type: application/problem+json
# {"type":"about:blank","title":"Not Found","status":404,"detail":"Product 99 not found","instance":"/products/99"}
```

No `@ExceptionHandler` method exists in this file or anywhere in the application. Spring Boot's autoconfigured exception handling recognizes `ErrorResponseException` and reads the status/body straight off the thrown instance.

### Level 2 — Intermediate

Adding response headers via the exception, and observing how Spring's own built-in exceptions behave identically (missing request parameter):

```java
// RateLimitExceededException.java — carries a custom header
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.ErrorResponseException;

public class RateLimitExceededException extends ErrorResponseException {
    public RateLimitExceededException(int retryAfterSeconds) {
        super(HttpStatus.TOO_MANY_REQUESTS,
              ProblemDetail.forStatusAndDetail(HttpStatus.TOO_MANY_REQUESTS, "Rate limit exceeded"),
              null);
        getHeaders().add(HttpHeaders.RETRY_AFTER, String.valueOf(retryAfterSeconds));
    }
}
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

    @GetMapping("/products/expensive-search")
    public String search(@RequestParam(required = false) String query,   // demonstrates Spring's OWN built-in ErrorResponse
                          @RequestHeader("X-Client-Id") String clientId) {
        if ("throttled-client".equals(clientId)) throw new RateLimitExceededException(30);
        return "results for " + query;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -H "X-Client-Id: throttled-client" http://localhost:8080/products/expensive-search
# HTTP/1.1 429 Too Many Requests
# Retry-After: 30
# Content-Type: application/problem+json
# {"type":"about:blank","title":"Too Many Requests","status":429,"detail":"Rate limit exceeded",...}

# Spring's OWN built-in exception (MissingRequestHeaderException) behaves the SAME way:
curl -i "http://localhost:8080/products/expensive-search?query=drills"
# HTTP/1.1 400 Bad Request
# Content-Type: application/problem+json
# {"type":"about:blank","title":"Bad Request","status":400,
#  "detail":"Required header 'X-Client-Id' is not present.","instance":"/products/expensive-search"}
```

**What changed:** `getHeaders().add(...)` inside the exception's constructor lets it contribute custom response headers (`Retry-After`), not just status and body — `ResponseEntityExceptionHandler` reads all three (`getStatusCode`, `getBody`, `getHeaders`) automatically. The second `curl` (missing the required `X-Client-Id` header) triggers Spring's own `MissingRequestHeaderException` — never written by you — and it produces a `ProblemDetail` `400` through the exact same `ErrorResponse` mechanism, proving custom and built-in exceptions are handled uniformly.

### Level 3 — Advanced

Production pattern: extending `ResponseEntityExceptionHandler` to customize how Spring's *own* built-in `ErrorResponse` exceptions render (adding a correlation id to every framework-level error, not just custom ones), while still leaning on the automatic mechanism for anything not explicitly overridden:

```java
// GlobalExceptionHandler.java
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

import java.util.UUID;

@RestControllerAdvice
public class GlobalExceptionHandler extends ResponseEntityExceptionHandler {

    // Override ONE specific built-in exception's handling — everything else Spring
    // handles automatically via ErrorResponse, unchanged.
    @Override
    protected ResponseEntity<Object> handleMissingServletRequestParameter(
            MissingServletRequestParameterException ex, HttpHeaders headers,
            HttpStatusCode status, WebRequest request) {

        ProblemDetail problem = ex.getBody();          // the ProblemDetail the exception already built
        String correlationId = UUID.randomUUID().toString();
        problem.setProperty("correlationId", correlationId);
        problem.setProperty("missingParameter", ex.getParameterName());

        return ResponseEntity.status(status).headers(headers).body(problem);
    }
}
```

```java
// ProductController.java (production version)
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    @GetMapping("/products/{id}")
    public String get(@PathVariable long id) {
        if (id != 1) throw new ProductNotFoundException(id);
        return "Drill";
    }

    @GetMapping("/products/search")
    public String search(@RequestParam String query) {   // required, no default -> triggers built-in exception if missing
        return "results for " + query;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/99
# 404 — ProductNotFoundException, unchanged, handled automatically via ErrorResponse (no override needed)

curl -i http://localhost:8080/products/search
# HTTP/1.1 400 Bad Request
# {"type":"about:blank","title":"Bad Request","status":400,
#  "detail":"Required parameter 'query' is not present.","instance":"/products/search",
#  "correlationId":"7c9e...ff2","missingParameter":"query"}
```

**What changed and why:**
- `ResponseEntityExceptionHandler` is the class Spring Boot's autoconfiguration already wires in behind the scenes to handle every `ErrorResponse`-implementing exception (built-in and custom) — extending it and overriding just `handleMissingServletRequestParameter` lets you enrich **only** that one specific case (adding `correlationId` and `missingParameter` extension fields) without writing a full custom handler for every other built-in exception type.
- `ex.getBody()` retrieves the `ProblemDetail` Spring's own `MissingServletRequestParameterException` already constructed internally — you're enhancing it, not rebuilding it from scratch, which keeps your override resilient to any future changes in Spring's default `detail` message wording.
- `ProductNotFoundException` (a custom `ErrorResponseException`) continues to work exactly as before, completely untouched by this override — demonstrating that overriding one specific handler method doesn't disturb the automatic handling of everything else.

## 6. Walkthrough

**Request: `GET /products/search` with no `query` parameter (Level 3 code).**

1. `DispatcherServlet` attempts to invoke `search(String query)`. Because `@RequestParam String query` has no `defaultValue` and isn't marked optional, Spring's argument resolution fails before the method body ever runs — it throws `MissingServletRequestParameterException("query", "String")` internally. This exception, built into Spring itself, already implements `ErrorResponse` and has a pre-built `ProblemDetail` (`status=400`, `detail="Required parameter 'query' is not present."`).
2. Spring's exception resolution searches for handling. Because `GlobalExceptionHandler extends ResponseEntityExceptionHandler` and overrides `handleMissingServletRequestParameter`, that specific override method is invoked instead of the framework's default handling for this exception type.
3. Inside the override: `ex.getBody()` retrieves the `ProblemDetail` the exception already carries. `problem.setProperty("correlationId", UUID.randomUUID())` and `problem.setProperty("missingParameter", "query")` add two extension fields on top of it.
4. Returns `ResponseEntity.status(status).headers(headers).body(problem)` — reusing the original `status`/`headers` Spring computed, but with the enriched body.
5. Response sent:
   ```
   HTTP/1.1 400 Bad Request
   Content-Type: application/problem+json

   {"type":"about:blank","title":"Bad Request","status":400,"detail":"Required parameter 'query' is not present.","instance":"/products/search","correlationId":"7c9e...ff2","missingParameter":"query"}
   ```

**Request: `GET /products/99` (custom `ProductNotFoundException`, unaffected by the override).**

1. `search`'s handling above only overrides `handleMissingServletRequestParameter` — a completely different exception type. `ProductNotFoundException` still flows through the *default*, un-overridden path: `ResponseEntityExceptionHandler`'s base implementation reads `getStatusCode()`/`getBody()`/`getHeaders()` off the exception directly (the mechanism from Level 1), producing the plain `404` `ProblemDetail` with no `correlationId` — exactly as it did before `GlobalExceptionHandler` existed.

## 7. Gotchas & takeaways

> **`ErrorResponseException`'s automatic handling only fires if no `@ExceptionHandler` for that exception type (or a more specific one) already matches.** A local `@ExceptionHandler(ProductNotFoundException.class)` in some other controller would still take priority over the automatic `ErrorResponse` mechanism — the priority rules from the `@ExceptionHandler`/`@ControllerAdvice` cards still apply on top of this.

> **`ResponseEntityExceptionHandler` has dozens of overridable `handleXxx` methods, one per built-in Spring MVC exception type** (`handleHttpMediaTypeNotAcceptable`, `handleMethodArgumentNotValid`, `handleMissingServletRequestParameter`, etc.). Overriding the wrong one, or misreading which exception maps to which method, is a common source of "why isn't my override being called" confusion — check the exact exception class Spring is actually throwing before assuming which method to override.

> **Building a `ProblemDetail` and passing `null` for the third `ErrorResponseException` constructor argument (as in the examples) is fine** — that argument is an optional `Throwable` cause; pass the original cause if wrapping another exception, for better stack traces in logs.

- `ErrorResponse` is the interface; `ErrorResponseException` is a ready-to-extend base class for custom self-describing exceptions.
- Spring's own built-in framework exceptions already implement `ErrorResponse` — that's why they produce sensible `ProblemDetail` responses automatically, with zero handler code.
- `ResponseEntityExceptionHandler` is the class doing this automatic handling; extend it and override specific `handleXxx` methods to customize individual built-in exception types.
- Prefer `ErrorResponseException` over a separate `@ExceptionHandler` when you want an exception to be fully self-contained and reusable across controllers without any matching handler code.
