---
card: microservices
gi: 536
slug: problem-details-rfc-7807-support-in-spring-6
title: "Problem Details (RFC 7807) support in Spring 6"
---

## 1. What it is

**Problem Details** is Spring 6's (and Spring Boot 3's) built-in support for [RFC 7807 error response standardization](0500-error-response-standardization-rfc-7807-problem-details.md), via the `ProblemDetail` class and `ErrorResponse` interface. Instead of every service inventing its own ad-hoc error JSON shape, Spring provides a standard structure (`type`, `title`, `status`, `detail`, `instance`, plus arbitrary extension properties) and wires it automatically into exception handling — `@ExceptionHandler` methods can simply return a `ProblemDetail`, and Spring's default error handling for common exceptions (like validation failures) already produces RFC 7807-shaped responses out of the box.

## 2. Why & when

You use `ProblemDetail` whenever a service returns machine-parseable error responses, because a consistent, standard shape is far more useful to API consumers than an ad-hoc one that varies endpoint to endpoint or service to service:

- **Before Spring 6, every team tended to invent its own error response JSON shape** — some services returned `{"error": "message"}`, others `{"errorCode": 123, "errorMessage": "..."}`, others something else entirely. A client integrating with several such services needed custom error-parsing logic per service, since there was no shared convention to write generic handling against.
- **RFC 7807 defines a standard, extensible shape**: `type` (a URI identifying the error category), `title` (a short, human-readable summary), `status` (the HTTP status code, duplicated in the body for convenience), `detail` (a specific, request-scoped explanation), `instance` (a URI identifying this specific occurrence), plus any additional fields a service wants to add for its own domain (like a list of field-level validation errors).
- **Spring's built-in exception handling for common cases (like `@Valid` request body validation failures) already returns `ProblemDetail`-shaped responses automatically**, with zero custom code required — you only need to reach for manual `ProblemDetail` construction when you have a custom, domain-specific exception that Spring doesn't already know how to translate.
- **Standardizing on this shape pays off most as an API gains more consumers** — a single client library, or a generic error-handling middleware, can be written once against the RFC 7807 shape and reused across every service that adopts it, rather than needing bespoke parsing logic per service.

## 3. Core concept

Think of RFC 7807 as a standard incident report form used across every department of a large organization, instead of each department inventing its own paperwork. Regardless of which department (which service) files the report, anyone reading it (any client parsing the response) already knows where to find the incident type, a short summary, the severity, and the detailed explanation — because the form's layout is fixed and shared, even though the actual content of any individual field is specific to that particular incident. A department can still add extra fields relevant to its own domain (an extension property), but the core layout everyone already knows how to read stays consistent.

Concretely:

1. **`ProblemDetail` is a class with the RFC 7807 standard fields built in** — `status`, `title`, `detail`, `type`, `instance` — plus a `setProperty(name, value)` method for adding arbitrary extension fields specific to your domain (like `errors: [...]` for a list of field validation failures).
2. **`ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, "Order 42 not found")`** is the common construction pattern — a static factory that fills in `status` and `detail` at minimum, with `title` defaulting to the standard HTTP status reason phrase unless explicitly overridden.
3. **`@ExceptionHandler` methods can return `ProblemDetail` directly**, and Spring serializes it with the correct `application/problem+json` content type automatically — no manual JSON construction or content-type header setting required.
4. **Spring's own built-in exception handling (for `MethodArgumentNotValidException` from `@Valid` failures, for instance) already produces `ProblemDetail` responses by default in Spring Boot 3+** — for the most common error cases, you get RFC 7807 compliance without writing any exception-handling code at all; custom `@ExceptionHandler` methods are for your own domain-specific exceptions Spring doesn't already know about.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Before Spring 6, each service invents its own ad-hoc error JSON shape; ProblemDetail gives every service the same standard RFC 7807 fields, with room for domain-specific extensions">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Ad-hoc (pre-Spring 6)</text>
  <rect x="20" y="35" width="260" height="30" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service A: {"error": "..."}</text>
  <rect x="20" y="70" width="260" height="30" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="90" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service B: {"errorCode":1,"msg":"..."}</text>
  <text x="150" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">every client needs custom parsing PER service</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">ProblemDetail (RFC 7807)</text>
  <rect x="380" y="35" width="260" height="65" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="52" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">type, title, status, detail, instance</text>
  <text x="510" y="66" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">+ optional domain extensions</text>
  <text x="510" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">SAME shape, every service</text>
  <text x="510" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">one generic client-side parser works everywhere</text>
</svg>

Standardizing on RFC 7807's fixed field set lets one client-side error parser work against every conforming service, instead of bespoke logic per service.

## 5. Runnable example

Scenario: an order lookup endpoint that needs to return a structured error when an order isn't found. We start with a plain Java model of an ad-hoc error shape (showing the inconsistency problem), extend it to the real `ProblemDetail`-returning `@ExceptionHandler`, then handle the hard case: adding domain-specific extension properties for a validation failure with multiple field errors.

### Level 1 — Basic

```java
// File: AdHocErrorShape.java -- models the PRE-STANDARDIZATION problem:
// each "service" invents its own error JSON shape, with NO shared convention.
import java.util.*;

public class AdHocErrorShape {
    static Map<String, Object> serviceAError(String message) {
        return Map.of("error", message); // Service A's own invented shape
    }
    static Map<String, Object> serviceBError(int code, String msg) {
        return Map.of("errorCode", code, "msg", msg); // Service B's DIFFERENT invented shape
    }

    static void genericClientParse(Map<String, Object> errorResponse) {
        // a generic client has NO reliable field name to read -- "error"? "msg"? "message"?
        System.out.println("Attempting generic parse: " + errorResponse + " -- no shared field name to rely on!");
    }

    public static void main(String[] args) {
        genericClientParse(serviceAError("Order 42 not found"));
        genericClientParse(serviceBError(404, "Order 42 not found"));
        System.out.println("Problem: a generic error-handling client can't be written once against BOTH shapes.");
    }
}
```

How to run: `java AdHocErrorShape.java`

`serviceAError` and `serviceBError` produce structurally different JSON shapes for conceptually the same kind of error — a client trying to handle errors generically across both services has no consistent field to extract a human-readable message from, forcing bespoke parsing logic per service, exactly the fragmentation problem RFC 7807 standardization solves.

### Level 2 — Intermediate

```java
// File: ProblemDetailRealShape.java -- the REAL Spring 6 shape: an
// @ExceptionHandler returning a STANDARD ProblemDetail, with zero custom
// JSON shape invented -- every service using this returns the SAME fields.
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.*;

public class ProblemDetailRealShape {

    static class OrderNotFoundException extends RuntimeException {
        OrderNotFoundException(String orderId) { super("Order " + orderId + " not found"); }
    }

    @RestControllerAdvice
    static class GlobalExceptionHandler {
        @ExceptionHandler(OrderNotFoundException.class)
        public ProblemDetail handleOrderNotFound(OrderNotFoundException ex) {
            ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
            problem.setTitle("Order Not Found");
            problem.setType(java.net.URI.create("https://api.example.com/errors/order-not-found"));
            return problem; // Spring serializes this with content-type application/problem+json automatically
        }
    }

    @RestController
    static class OrderController {
        @GetMapping("/orders/{id}")
        public String getOrder(@PathVariable String id) {
            if (id.equals("missing")) throw new OrderNotFoundException(id);
            return "{\"orderId\":\"" + id + "\"}";
        }
    }
}
```

How to run: requires `spring-boot-starter-web` (Spring Boot 3.x, Spring Framework 6+); run via `mvn spring-boot:run` and `GET /orders/missing` to receive a `404` response with `Content-Type: application/problem+json` and body `{"type":"https://api.example.com/errors/order-not-found","title":"Order Not Found","status":404,"detail":"Order missing not found","instance":"/orders/missing"}`.

`ProblemDetail.forStatusAndDetail(...)` builds the standard RFC 7807 fields in one call; `setTitle` and `setType` further enrich it. `@ExceptionHandler` methods returning `ProblemDetail` require no manual `HttpServletResponse` manipulation or custom JSON construction — Spring recognizes the return type and serializes it with the correct standard content type automatically, and `instance` is populated automatically from the request path.

### Level 3 — Advanced

```java
// File: ProblemDetailWithExtensions.java -- adds DOMAIN-SPECIFIC
// EXTENSION properties to a ProblemDetail for a validation failure with
// MULTIPLE field errors -- the standard fields PLUS custom ones, together.
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.stream.Collectors;

public class ProblemDetailWithExtensions {

    record CreateOrderRequest(@NotBlank String customerId, @Min(1) int quantity) {}

    @RestControllerAdvice
    static class GlobalExceptionHandler {

        // Spring Boot 3+ ALREADY handles MethodArgumentNotValidException with a
        // default ProblemDetail response; this custom handler shows how to
        // ENRICH it with a domain-specific "errors" extension listing every field problem.
        @ExceptionHandler(MethodArgumentNotValidException.class)
        public ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
            ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.BAD_REQUEST, "Request validation failed");
            problem.setTitle("Validation Error");

            // extension property: a structured list of every individual field failure,
            // beyond what the standard RFC 7807 fields alone would express
            List<Map<String, String>> fieldErrors = ex.getBindingResult().getFieldErrors().stream()
                .map(fe -> Map.of("field", fe.getField(), "message", Objects.requireNonNullElse(fe.getDefaultMessage(), "invalid")))
                .collect(Collectors.toList());
            problem.setProperty("errors", fieldErrors);

            return problem;
        }
    }

    @RestController
    static class OrderController {
        @PostMapping("/orders")
        public String createOrder(@Valid @RequestBody CreateOrderRequest request) {
            return "{\"status\":\"created\"}";
        }
    }
}
```

How to run: requires `spring-boot-starter-web` and `spring-boot-starter-validation`; run via `mvn spring-boot:run` and `POST /orders` with body `{"customerId": "", "quantity": 0}` to receive a `400` response with the standard RFC 7807 fields plus an `"errors"` array listing both the blank `customerId` and out-of-range `quantity` field failures.

`problem.setProperty("errors", fieldErrors)` adds a domain-specific extension property alongside the standard `type`/`title`/`status`/`detail` fields — RFC 7807 explicitly permits this, and Spring's `ProblemDetail` serializes extension properties as additional top-level JSON fields, so a client parsing this response can rely on the standard fields for generic error handling while also reading the `errors` array for field-level detail when it needs to display validation feedback to a user.

## 6. Walkthrough

Trace what happens when a client sends `POST /orders` with body `{"customerId": "", "quantity": 0}` against the Level 3 controller, end to end:

1. **Spring routes the request to `createOrder`**, and because the parameter is `@Valid @RequestBody CreateOrderRequest`, Bean Validation runs against the deserialized request *before* `createOrder`'s body executes.
2. **Validation checks `customerId = ""` against `@NotBlank`** — fails, since it's blank. **Validation checks `quantity = 0` against `@Min(1)`** — also fails, since 0 is below the minimum. Both failures are collected into the validation result; Spring throws `MethodArgumentNotValidException` carrying both field errors, before `createOrder`'s body ever runs.
3. **`GlobalExceptionHandler.handleValidation` catches the exception.** It first builds a standard `ProblemDetail` via `forStatusAndDetail(BAD_REQUEST, "Request validation failed")`, then sets the title.
4. **It calls `ex.getBindingResult().getFieldErrors()`**, which returns both collected field errors (`customerId`, `quantity`), and maps each into a small `Map` with `"field"` and `"message"` keys — building the `fieldErrors` list containing two entries.
5. **`problem.setProperty("errors", fieldErrors)` attaches this list as an extension property** on the `ProblemDetail` object, alongside its standard fields.
6. **Spring serializes the returned `ProblemDetail` as the HTTP response body**, with `Content-Type: application/problem+json` and status `400`.

Response shape (conceptually):

```json
{
  "type": "about:blank",
  "title": "Validation Error",
  "status": 400,
  "detail": "Request validation failed",
  "instance": "/orders",
  "errors": [
    { "field": "customerId", "message": "must not be blank" },
    { "field": "quantity", "message": "must be greater than or equal to 1" }
  ]
}
```

A client written generically against RFC 7807 can read `title`, `status`, and `detail` to display or log a general error summary, without knowing anything about this specific service's domain — and a client that specifically understands this service's API can additionally read the `errors` extension array to show field-by-field validation feedback in a form. Both levels of consumption are served by the same single response shape.

## 7. Gotchas & takeaways

> **Gotcha:** returning a `ProblemDetail` from an `@ExceptionHandler` sets the response `Content-Type` to `application/problem+json` automatically — a client or test that asserts on `application/json` specifically (rather than checking the response body's structure) can unexpectedly fail after adopting `ProblemDetail`, since the content type itself changed even though the body is still valid JSON.

- `ProblemDetail`'s standard fields (`type`, `title`, `status`, `detail`, `instance`) give every conforming service a consistent, generically-parseable error shape, replacing the ad-hoc, per-service JSON error formats common before Spring 6.
- Spring Boot 3+ already returns `ProblemDetail`-shaped responses automatically for common cases like `@Valid` validation failures — custom `@ExceptionHandler` methods are for enriching those defaults or handling your own domain-specific exceptions.
- Extension properties via `setProperty(name, value)` let a service add domain-specific detail (like a structured list of field validation errors) without breaking the standard shape generic clients rely on.
- Standardizing error shapes pays off most as an API gains external or cross-team consumers — the value is in letting one generic error-handling implementation work across every conforming service, rather than requiring bespoke parsing per service.
