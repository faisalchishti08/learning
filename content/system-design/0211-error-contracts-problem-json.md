---
card: system-design
gi: 211
slug: error-contracts-problem-json
title: Error contracts & problem+json
---

## 1. What it is

An **error contract** is a consistent, documented shape every error response from an API follows, so clients can parse errors the same way regardless of which endpoint or which failure produced them. **`application/problem+json`** (RFC 7807/9457) is a standard error shape with fields `type`, `title`, `status`, `detail`, and `instance`, designed so this consistency does not have to be invented from scratch by every API.

## 2. Why & when

An API where every endpoint returns errors in a different shape — one returns `{"error": "not found"}`, another returns `{"message": "Not Found", "code": 404}`, a third returns a bare string — forces client code to special-case error parsing per endpoint. A single, consistent error contract lets client code parse *any* error response from the API the same way, once.

Adopt an error contract from the very first endpoint you build — retrofitting consistent errors across an API that already has clients depending on inconsistent shapes is a breaking change requiring careful [versioning](0208-versioning-strategies.md). `application/problem+json` is a reasonable default choice because it is a real IETF standard, meaning some HTTP tooling and client libraries already understand it, rather than a shape you invent and must document yourself.

## 3. Core concept

- **`type`** — a URI identifying the specific error category (e.g. `https://api.example.com/errors/insufficient-stock`). Clients can match on this to handle specific error types programmatically, without parsing human-readable text.
- **`title`** — a short, human-readable summary of the error category, the same for every occurrence of this `type` (e.g. `"Insufficient Stock"`).
- **`status`** — the HTTP status code, repeated in the body for convenience (some clients only easily see the body, not response headers/status).
- **`detail`** — a human-readable explanation specific to *this* occurrence (e.g. `"Only 2 units of SKU 'MOUSE-01' are in stock, but 5 were requested."`), not the same across every instance of this error type.
- **`instance`** — a URI identifying this specific occurrence, often used to correlate the error with server-side logs or [distributed tracing](0188-distributed-tracing-correlation-ids.md) — very useful when a support request references "error at `instance: /errors/instances/a1b2c3`."
- **Validation errors need one more thing: field-level detail.** For a request that failed validation on multiple fields, extend the base shape with an `errors` array (field name + specific problem per entry), so the client can highlight every invalid field in a form at once, not just the first one found.

## 4. Diagram

```
  Client                                   Server

  POST /orders                             validates request...
  { items: [], customerId: "" }            two problems found:
                                             - items must not be empty
                                             - customerId must not be blank
       |                                          |
       |<----------- 400 Bad Request -------------|
       |  Content-Type: application/problem+json   |
       |  {                                          |
       |    "type": ".../errors/validation-failed", |
       |    "title": "Validation Failed",            |
       |    "status": 400,                           |
       |    "detail": "2 fields failed validation.", |
       |    "instance": "/errors/instances/xy9",      |
       |    "errors": [                               |
       |      {"field":"items","detail":"must not be empty"},
       |      {"field":"customerId","detail":"must not be blank"}
       |    ]                                          |
       |  }                                             |
```
*Caption: every field of the standard shape is present, and the extra `errors` array adds the field-level detail a validation failure specifically needs — the base shape is unchanged.*

## 5. Runnable example

**Level 1 — Basic.** Build a `problem+json`-shaped error response for a single, simple error (a not-found).

**Level 2 — Intermediate.** Extend the shape with field-level `errors` for a multi-field validation failure.

**Level 3 — Advanced.** A central error handler that maps different exception types to the correct `problem+json` response consistently, so every endpoint gets the same shape without repeating the mapping logic.

```java
// ErrorContractDemo.java
import java.util.*;

public class ErrorContractDemo {

    // ---------- Level 1: the base problem+json shape ----------
    record Problem(String type, String title, int status, String detail, String instance) {
        String toJson() {
            return String.format(
                "{\"type\":\"%s\",\"title\":\"%s\",\"status\":%d,\"detail\":\"%s\",\"instance\":\"%s\"}",
                type, title, status, detail, instance);
        }
    }

    static Problem notFound(String orderId, String instanceId) {
        return new Problem(
            "https://api.example.com/errors/order-not-found",
            "Order Not Found",
            404,
            "No order exists with id '" + orderId + "'.",
            "/errors/instances/" + instanceId);
    }

    // ---------- Level 2: validation error extends the base shape with field-level detail ----------
    record FieldError(String field, String detail) {
        String toJson() { return String.format("{\"field\":\"%s\",\"detail\":\"%s\"}", field, detail); }
    }
    record ValidationProblem(Problem base, List<FieldError> errors) {
        String toJson() {
            StringBuilder fieldErrorsJson = new StringBuilder();
            for (int i = 0; i < errors.size(); i++) {
                fieldErrorsJson.append(errors.get(i).toJson());
                if (i < errors.size() - 1) fieldErrorsJson.append(",");
            }
            String baseJson = base.toJson();
            return baseJson.substring(0, baseJson.length() - 1) + ",\"errors\":[" + fieldErrorsJson + "]}";
        }
    }

    // ---------- Level 3: exceptions mapped to problem+json centrally, once ----------
    static class OrderNotFoundException extends RuntimeException {
        String orderId;
        OrderNotFoundException(String orderId) { this.orderId = orderId; }
    }
    static class ValidationException extends RuntimeException {
        List<FieldError> fieldErrors;
        ValidationException(List<FieldError> fieldErrors) { this.fieldErrors = fieldErrors; }
    }
    static class InsufficientStockException extends RuntimeException {
        String sku; int requested, available;
        InsufficientStockException(String sku, int requested, int available) {
            this.sku = sku; this.requested = requested; this.available = available;
        }
    }

    static String centralErrorHandler(RuntimeException e, String instanceId) {
        if (e instanceof OrderNotFoundException nf) {
            return notFound(nf.orderId, instanceId).toJson();
        }
        if (e instanceof ValidationException ve) {
            Problem base = new Problem(
                "https://api.example.com/errors/validation-failed", "Validation Failed", 400,
                ve.fieldErrors.size() + " field(s) failed validation.", "/errors/instances/" + instanceId);
            return new ValidationProblem(base, ve.fieldErrors).toJson();
        }
        if (e instanceof InsufficientStockException is) {
            Problem p = new Problem(
                "https://api.example.com/errors/insufficient-stock", "Insufficient Stock", 409,
                "Only " + is.available + " units of SKU '" + is.sku + "' are in stock, but " +
                    is.requested + " were requested.",
                "/errors/instances/" + instanceId);
            return p.toJson();
        }
        Problem generic = new Problem("about:blank", "Internal Server Error", 500,
            "An unexpected error occurred.", "/errors/instances/" + instanceId);
        return generic.toJson();
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - basic problem+json for a not-found error:");
        System.out.println("  " + notFound("ORD-99", "abc123").toJson());

        System.out.println("\nLevel 2 - validation error with field-level detail:");
        ValidationProblem vp = new ValidationProblem(
            new Problem("https://api.example.com/errors/validation-failed", "Validation Failed", 400,
                "2 field(s) failed validation.", "/errors/instances/xy9"),
            List.of(new FieldError("items", "must not be empty"),
                    new FieldError("customerId", "must not be blank")));
        System.out.println("  " + vp.toJson());

        System.out.println("\nLevel 3 - central handler maps different exceptions to the SAME consistent shape:");
        System.out.println("  " + centralErrorHandler(new OrderNotFoundException("ORD-1"), "i-001"));
        System.out.println("  " + centralErrorHandler(
            new ValidationException(List.of(new FieldError("amount", "must be positive"))), "i-002"));
        System.out.println("  " + centralErrorHandler(
            new InsufficientStockException("MOUSE-01", 5, 2), "i-003"));
        System.out.println("  " + centralErrorHandler(new RuntimeException("unexpected npe"), "i-004"));
    }
}
```

**How to run:** `java ErrorContractDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `notFound("ORD-99", "abc123")` builds a `Problem` record with all five standard fields filled in — `type` identifies the category, `detail` names the specific order ID that was missing, `instance` gives this specific occurrence a traceable identifier. `toJson()` renders it as the `application/problem+json` shape.
2. **Level 2:** `ValidationProblem` wraps a base `Problem` and adds an `errors` list of `FieldError` entries. `toJson()` takes the base `Problem`'s JSON, strips its closing `}`, and appends `,"errors":[...]` before closing it again — this shows the extension is additive: every field a base `Problem` has is still present, with one more array added for the validation-specific detail.
3. **Level 3:** `centralErrorHandler` is the single place in the whole application that knows how to turn an exception into a `problem+json` response. Each `instanceof` branch handles one exception type and builds the matching `Problem` (or `ValidationProblem`) shape.
4. Calling it with an `OrderNotFoundException` produces the same `type`/`title` pattern as Level 1's manual call — because it is calling the same `notFound(...)` helper internally. Calling it with a `ValidationException` produces the same shape as Level 2's manual `ValidationProblem`.
5. The final call passes a plain `RuntimeException` with no matching `instanceof` branch — the handler falls through to the generic `500` case, still returning a valid `problem+json` shape rather than an unstructured stack trace. Every one of the four calls, despite originating from completely different failure conditions, comes back through the exact same five-field (or five-plus-`errors`-field) shape — this is the entire point of a shared error contract.

## 7. Gotchas & takeaways

> **Gotcha:** leaking implementation detail into `detail` — like a raw database exception message or a stack trace — both confuses API consumers (who cannot act on "NullPointerException at line 42") and can expose internal system information to a public client. Keep `detail` a clear, business-level description of what went wrong.

- Pick one error shape (ideally `application/problem+json`, since it is a real, documented standard) and route every error path through it, including unexpected/uncaught exceptions — never let an endpoint fall back to a default framework error page with a different shape.
- Use `type` for machine-matchable error categories and `detail` for the specific, human-readable explanation of this occurrence — do not conflate the two.
- Correlate `instance` with your [distributed tracing](0188-distributed-tracing-correlation-ids.md) IDs so a support ticket referencing an error instance can be traced directly to the relevant logs and spans.
- A consistent error contract is what makes [idempotency](0210-idempotency-safe-methods.md) retries and client-side error handling reliable — a client cannot decide whether to retry an error it cannot reliably parse.
