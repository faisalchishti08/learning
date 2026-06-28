---
card: spring-boot
gi: 118
slug: rfc-9457-problemdetail-support
title: RFC 9457 ProblemDetail support
---

## 1. What it is

**RFC 9457** (successor to RFC 7807) is a standard JSON format for HTTP API error responses. Instead of ad-hoc error shapes, every API error returns a consistent object with well-known fields: `type`, `title`, `status`, `detail`, and `instance`. Spring Framework 6.0+ and Spring Boot 3.0+ ship a `ProblemDetail` class and auto-configuration that makes `@ExceptionHandler` methods return this format with minimal boilerplate.

## 2. Why & when

Without a standard, every API invents its own error JSON — `{"error": "..."}`, `{"message": "..."}`, `{"code": 42, "reason": "..."}`. Clients must understand each shape separately. RFC 9457 gives a universal shape so generic clients, API gateways, and monitoring tools can parse errors predictably.

Use it when:

- You want your API errors to follow an open standard.
- You're building APIs consumed by diverse clients (mobile, third-party, microservices).
- You're already on Spring Boot 3.x / Spring 6.x — it costs almost nothing to enable.

Enable via `spring.mvc.problemdetails.enabled=true` (Spring MVC) or `spring.webflux.problemdetails.enabled=true` (WebFlux).

## 3. Core concept

A Problem Detail response looks like this:

```json
{
  "type": "https://example.com/problems/out-of-stock",
  "title": "Product Out of Stock",
  "status": 409,
  "detail": "Widget #42 has 0 units remaining.",
  "instance": "/orders/99"
}
```

Fields:

| Field | Required | Purpose |
|---|---|---|
| `type` | no (defaults to `about:blank`) | URI identifying the problem type |
| `title` | no | Short human-readable summary |
| `status` | yes | HTTP status code |
| `detail` | no | Human explanation of this occurrence |
| `instance` | no | URI of the specific request |

You can extend it with custom properties. `ProblemDetail` exposes `setProperty(key, value)` for extras.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="115" text-anchor="middle" fill="#e6edf3" font-size="13" font-family="sans-serif">Exception thrown</text>
  <rect x="250" y="60" width="170" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="335" y="88" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">@ExceptionHandler</text>
  <text x="335" y="106" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">returns ProblemDetail</text>
  <rect x="250" y="145" width="170" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="335" y="165" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Content-Type:</text>
  <text x="335" y="182" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">application/problem+json</text>
  <rect x="510" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="580" y="115" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">RFC 9457 JSON</text>
  <line x1="162" y1="110" x2="246" y2="96" stroke="#e6edf3" stroke-width="1.5" marker-end="url(#pd)"/>
  <line x1="335" y1="122" x2="335" y2="142" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#pd2)"/>
  <line x1="422" y1="170" x2="506" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#pd3)"/>
  <defs>
    <marker id="pd" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#e6edf3"/></marker>
    <marker id="pd2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="pd3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Exception → `@ExceptionHandler` builds a `ProblemDetail` → serialised with `Content-Type: application/problem+json`.

## 5. Runnable example

```java
// ProblemDetailApp.java  —  Spring Boot 3.x project, enable with property below
// application.properties: spring.mvc.problemdetails.enabled=true

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.*;

import java.net.URI;

@SpringBootApplication
public class ProblemDetailApp {
    public static void main(String[] args) {
        SpringApplication.run(ProblemDetailApp.class, args);
    }
}

class OutOfStockException extends RuntimeException {
    final long productId;
    OutOfStockException(long id) {
        super("Product " + id + " is out of stock");
        this.productId = id;
    }
}

@RestController
@RequestMapping("/orders")
class OrderController {

    @PostMapping
    public String placeOrder(@RequestParam long productId) {
        // Simulate stock check
        if (productId == 42) throw new OutOfStockException(productId);
        return "Order placed for product " + productId;
    }
}

@RestControllerAdvice
class ProblemAdvice {

    @ExceptionHandler(OutOfStockException.class)
    public ProblemDetail handleOutOfStock(OutOfStockException ex) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(
                HttpStatus.CONFLICT, ex.getMessage());
        pd.setType(URI.create("https://api.example.com/problems/out-of-stock"));
        pd.setTitle("Product Out of Stock");
        pd.setProperty("productId", ex.productId);
        return pd;
    }
}
```

**How to run:** start the app, then:
```
curl -X POST "http://localhost:8080/orders?productId=42" -H "Accept: application/json"
```
Returns `409 Conflict` with `Content-Type: application/problem+json` and a structured body.

## 6. Walkthrough

- `spring.mvc.problemdetails.enabled=true` activates `ProblemDetailsExceptionHandler`, which handles Spring MVC's own exceptions (`MethodArgumentNotValidException`, `NoResourceFoundException`, etc.) as `ProblemDetail` automatically — before you add any custom handlers.
- `@RestControllerAdvice` makes `ProblemAdvice` a global exception handler. `@ExceptionHandler(OutOfStockException.class)` catches that specific type.
- `ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, ex.getMessage())` creates a `ProblemDetail` with `status = 409` and the `detail` field set to the exception message.
- `.setType(URI.create(...))` sets the `type` URI identifying the problem category — clients can look it up for documentation.
- `.setProperty("productId", ex.productId)` adds an extension field. RFC 9457 allows any extra properties alongside the standard ones.
- Spring serialises the return value with `Content-Type: application/problem+json` automatically when the return type is `ProblemDetail`.

## 7. Gotchas & takeaways

> `spring.mvc.problemdetails.enabled=true` only affects Spring MVC's built-in exceptions. Your own exceptions still need `@ExceptionHandler` methods — but those can return `ProblemDetail` directly.

> `type` defaults to `about:blank` if omitted. That's valid per the spec but not very useful; always set a meaningful URI for problem types you own.

- `ProblemDetail` is in `org.springframework.http` (Spring Framework), not Spring Boot — usable in plain Spring 6 apps too.
- Set `instance` to the request URI with `pd.setInstance(URI.create(request.getRequestURI()))` for full spec compliance.
- Extension properties must be JSON-serialisable; they appear at the top level of the JSON object.
- For WebFlux, use `spring.webflux.problemdetails.enabled=true`.
- `ErrorResponseException` is a Spring 6 base class you can extend instead of building `ProblemDetail` manually inside an `@ExceptionHandler`.
