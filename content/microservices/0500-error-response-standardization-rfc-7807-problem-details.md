---
card: microservices
gi: 500
slug: error-response-standardization-rfc-7807-problem-details
title: "Error response standardization (RFC 7807 problem details)"
---

## 1. What it is

**RFC 7807 (Problem Details for HTTP APIs)** is a standardized JSON structure for error responses — `type`, `title`, `status`, `detail`, and `instance` fields, plus room for extension fields specific to the error — used consistently across every endpoint of an API instead of each endpoint (or each error case) inventing its own ad hoc error shape. A consumer that knows how to parse one RFC 7807 error from your API can parse *every* error from it, and often from other APIs following the same standard too.

## 2. Why & when

You adopt a standardized error format across an API's entire surface because inconsistent, ad hoc error shapes make error handling in consumers unnecessarily fragile and repetitive:

- **Different error shapes per endpoint force consumers to write different error-parsing logic per endpoint.** If one endpoint returns `{"error": "..."}`, another returns `{"message": "...", "code": 123}`, and a third returns a plain text string, a consumer integrating with all three needs three separate, brittle parsing paths for what's conceptually the same operation — reporting that something went wrong.
- **A standard format is broadly tooled and understood.** RFC 7807 is a published, well-known standard — consumer libraries, API gateways, and monitoring tools already know how to parse and act on it, rather than needing custom logic for your API's specific, invented error shape.
- **Consistent error structure makes automated handling (retry logic, user-facing error translation, alerting) genuinely programmatic.** A consumer can reliably extract `status` and `type` to decide "should I retry this" or "what user-facing message maps to this error" using the same logic across your entire API, rather than per-endpoint special-casing.
- **You adopt this format from the very first endpoint of a new API** — retrofitting a standard error format onto an API that's already shipped several different, inconsistent error shapes across different endpoints is itself a breaking change for every consumer's existing error-handling code.

## 3. Core concept

Think of a standardized incident report form used across every department of a large organization — regardless of which department files it, the form always has the same fields (what happened, severity, where, when), so anyone reading incident reports across the whole organization can process them the same way, rather than each department inventing its own report format that requires separately learning to interpret.

Concretely, RFC 7807's core fields:

1. **`type`**: a URI identifying the specific error type — ideally dereferenceable to human-readable documentation about that error, though it can also just be a stable, unique identifier string.
2. **`title`**: a short, human-readable summary of the error type, meant to be the same across every occurrence of this specific error (not including request-specific detail).
3. **`status`**: the HTTP status code, duplicated here for convenience even though it's also present in the actual HTTP response status line.
4. **`detail`**: a human-readable explanation *specific to this occurrence* of the error — unlike `title`, this can vary between two errors of the same `type`.
5. **`instance`**: a URI identifying this specific occurrence of the problem, often useful for correlating with logs or support requests.
6. **Extension fields**: additional, error-specific data beyond the standard fields — a validation error might add a `errors` array listing which specific fields failed and why.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A standard RFC 7807 error response structure with type, title, status, detail, and instance fields, consistent across every endpoint">
  <rect x="20" y="20" width="620" height="160" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="45" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">application/problem+json</text>
  <text x="50" y="75" fill="#e6edf3" font-size="9" font-family="sans-serif">"type": "https://api.example.com/errors/insufficient-stock"</text>
  <text x="50" y="95" fill="#e6edf3" font-size="9" font-family="sans-serif">"title": "Insufficient Stock"</text>
  <text x="50" y="115" fill="#e6edf3" font-size="9" font-family="sans-serif">"status": 409</text>
  <text x="50" y="135" fill="#e6edf3" font-size="9" font-family="sans-serif">"detail": "Only 2 units of sku-123 remain, 5 requested"</text>
  <text x="50" y="155" fill="#e6edf3" font-size="9" font-family="sans-serif">"instance": "/orders/42"</text>
</svg>

Every error response, regardless of endpoint, shares this same standardized structure.

## 5. Runnable example

Scenario: an error-handling layer producing standardized RFC 7807 responses across different failure kinds. We start with a basic problem-details construction for one error type, extend it to multiple distinct error types sharing the same structure, then handle the hard case: a validation error with per-field detail as an extension field, correctly composed alongside the standard fields rather than replacing them.

### Level 1 — Basic

```java
// File: ProblemDetailsBasic.java -- models constructing ONE standardized
// RFC 7807 error response for a single failure case.
import java.util.*;

public class ProblemDetailsBasic {
    record ProblemDetails(String type, String title, int status, String detail, String instance) {}

    static ProblemDetails insufficientStockError(String sku, int available, int requested, String orderPath) {
        return new ProblemDetails(
            "https://api.example.com/errors/insufficient-stock",
            "Insufficient Stock",
            409,
            "Only " + available + " units of " + sku + " remain, " + requested + " requested",
            orderPath
        );
    }

    public static void main(String[] args) {
        ProblemDetails error = insufficientStockError("sku-123", 2, 5, "/orders/42");
        System.out.println("[response 409 application/problem+json]");
        System.out.println("  type: " + error.type());
        System.out.println("  title: " + error.title());
        System.out.println("  status: " + error.status());
        System.out.println("  detail: " + error.detail());
        System.out.println("  instance: " + error.instance());
    }
}
```

How to run: `java ProblemDetailsBasic.java`

`ProblemDetails` models the five standard RFC 7807 fields as a fixed structure, and `insufficientStockError` populates them for one specific failure case — `title` stays generic and reusable ("Insufficient Stock"), while `detail` carries the request-specific numbers, matching the standard's distinction between the two fields.

### Level 2 — Intermediate

```java
// File: ProblemDetailsMultipleTypes.java -- the SAME structure, now
// producing MULTIPLE distinct error types, all sharing the IDENTICAL
// standardized shape -- a consumer's parsing logic never needs to change
// per error type, only the VALUES differ.
import java.util.*;

public class ProblemDetailsMultipleTypes {
    record ProblemDetails(String type, String title, int status, String detail, String instance) {}

    static ProblemDetails insufficientStockError(String sku, int available, int requested, String path) {
        return new ProblemDetails("https://api.example.com/errors/insufficient-stock", "Insufficient Stock", 409,
                "Only " + available + " units of " + sku + " remain, " + requested + " requested", path);
    }

    static ProblemDetails orderNotFoundError(String orderId, String path) {
        return new ProblemDetails("https://api.example.com/errors/order-not-found", "Order Not Found", 404,
                "No order exists with id '" + orderId + "'", path);
    }

    static ProblemDetails unauthorizedError(String path) {
        return new ProblemDetails("https://api.example.com/errors/unauthorized", "Unauthorized", 401,
                "A valid authentication token is required for this operation", path);
    }

    // The CONSUMER's error handling: works IDENTICALLY regardless of which error type it received.
    static void consumerHandleError(ProblemDetails error) {
        System.out.println("[consumer] received " + error.status() + " " + error.title() + ": " + error.detail());
    }

    public static void main(String[] args) {
        consumerHandleError(insufficientStockError("sku-123", 2, 5, "/orders/42"));
        consumerHandleError(orderNotFoundError("order-999", "/orders/999"));
        consumerHandleError(unauthorizedError("/orders/42"));
    }
}
```

How to run: `java ProblemDetailsMultipleTypes.java`

`consumerHandleError` is a single method that reads only the standard `ProblemDetails` fields, and it's called identically for all three genuinely different error types — the exact payoff of standardization: consumer error-handling logic doesn't branch per error type at the structural level, it just reads the same shape and reacts based on the *values*, not a different parsing path per error.

### Level 3 — Advanced

```java
// File: ProblemDetailsValidationExtension.java -- the SAME standardized
// shape, now handling the PRODUCTION-FLAVORED hard case: a VALIDATION
// error needs PER-FIELD detail (which fields failed, and why) beyond what
// the five standard fields can express. RFC 7807 explicitly supports
// EXTENSION fields for exactly this -- added ALONGSIDE the standard
// fields, never replacing them, so a consumer's baseline parsing still works.
import java.util.*;

public class ProblemDetailsValidationExtension {
    record FieldError(String field, String message) {}

    record ProblemDetails(
        String type, String title, int status, String detail, String instance,
        List<FieldError> validationErrors // EXTENSION field, specific to this error type
    ) {}

    static ProblemDetails validationError(String path, List<FieldError> fieldErrors) {
        return new ProblemDetails(
            "https://api.example.com/errors/validation-failed",
            "Validation Failed",
            400,
            fieldErrors.size() + " field(s) failed validation",
            path,
            fieldErrors
        );
    }

    // The consumer's BASELINE handling still works, reading ONLY the standard fields.
    static void consumerBaselineHandling(ProblemDetails error) {
        System.out.println("[consumer, baseline] " + error.status() + " " + error.title() + ": " + error.detail());
    }

    // A consumer that SPECIFICALLY understands validation errors can ALSO read the extension.
    static void consumerValidationAwareHandling(ProblemDetails error) {
        consumerBaselineHandling(error); // still calls the baseline handling first
        if (error.validationErrors() != null && !error.validationErrors().isEmpty()) {
            System.out.println("[consumer, validation-aware] per-field detail:");
            for (FieldError fieldError : error.validationErrors()) {
                System.out.println("  - " + fieldError.field() + ": " + fieldError.message());
            }
        }
    }

    public static void main(String[] args) {
        List<FieldError> fieldErrors = List.of(
            new FieldError("customerEmail", "must be a valid email address"),
            new FieldError("quantity", "must be greater than zero")
        );
        ProblemDetails error = validationError("/orders", fieldErrors);

        System.out.println("--- a GENERIC consumer, unaware of the validation extension ---");
        consumerBaselineHandling(error);

        System.out.println();
        System.out.println("--- a VALIDATION-AWARE consumer, reading the extension too ---");
        consumerValidationAwareHandling(error);
    }
}
```

How to run: `java ProblemDetailsValidationExtension.java`

`ProblemDetails` gains a `validationErrors` field beyond the five standard ones — an extension, exactly as RFC 7807 permits. `consumerBaselineHandling` reads only the five standard fields and works correctly on this error exactly as it would on any other, completely ignorant of the extension's existence — demonstrating [tolerant reader](0496-tolerant-reader-pattern.md) behavior in practice. `consumerValidationAwareHandling` calls that same baseline method first, then additionally reads `validationErrors` for consumers sophisticated enough to want that extra, error-specific detail.

## 6. Walkthrough

Trace `ProblemDetailsValidationExtension.main` in order. **First**, `fieldErrors` is built with two entries, and `validationError("/orders", fieldErrors)` constructs a `ProblemDetails` with `status = 400`, a generic `detail` summarizing the count, and `validationErrors` set to the full list of per-field failures.

**Next**, the generic-consumer section calls `consumerBaselineHandling(error)`. This method reads only `error.status()`, `error.title()`, and `error.detail()` — it prints a complete, useful error summary ("400 Validation Failed: 2 field(s) failed validation") without ever touching `validationErrors` at all, exactly like a consumer that only knows the standard RFC 7807 shape and has never heard of this particular API's validation extension.

**Then**, the validation-aware section calls `consumerValidationAwareHandling(error)`. Inside it, the very first line calls `consumerBaselineHandling(error)` again — so the same standard summary prints first, identically to before.

**After that**, the `if (error.validationErrors() != null && !error.validationErrors().isEmpty())` check runs: `validationErrors` is non-null and contains two entries, so the condition is `true`, and the loop below it prints each `FieldError`'s specific field name and message individually — detail the baseline handling never had access to, because it never looked for it.

**Finally**, comparing the two consumer sections' output side by side shows the core value of RFC 7807's extension-field approach: a completely generic consumer gets a correct, useful baseline error message with zero special code, while a more sophisticated consumer that specifically knows about this API's validation extension gets richer, actionable per-field detail on top of that same baseline — both consumers parsing the exact same response object successfully, at their own respective levels of understanding.

```
--- a GENERIC consumer, unaware of the validation extension ---
[consumer, baseline] 400 Validation Failed: 2 field(s) failed validation

--- a VALIDATION-AWARE consumer, reading the extension too ---
[consumer, baseline] 400 Validation Failed: 2 field(s) failed validation
[consumer, validation-aware] per-field detail:
  - customerEmail: must be a valid email address
  - quantity: must be greater than zero
```

## 7. Gotchas & takeaways

> Putting genuinely important, universally-needed information *only* in an extension field, with nothing meaningful in the standard `detail` field, defeats the purpose of standardization — a generic consumer relying only on the baseline fields should still get a complete, useful error message, with extensions adding richness for consumers sophisticated enough to use them, never being the *only* source of essential information.
- Use the `application/problem+json` content type specifically for these responses, distinct from your API's normal success content type — this lets consumers (and tooling) reliably detect "this is a standardized error response" from the `Content-Type` header alone, before even parsing the body.
- `type` URIs don't need to actually be dereferenceable to a live webpage, but making them so (linking to real documentation about that specific error) is a meaningful usability improvement for developers debugging against your API.
- This standardization pairs naturally with the [tolerant reader pattern](0496-tolerant-reader-pattern.md) — a well-behaved consumer reads the standard fields it needs and safely ignores any extension fields it doesn't understand, exactly as demonstrated by `consumerBaselineHandling` here.
- Keep `title` stable and generic across every occurrence of the same error `type` — reserve request-specific detail for the `detail` field, so a consumer grouping or deduplicating errors by `title` gets meaningful, consistent grouping rather than every occurrence looking unique.
