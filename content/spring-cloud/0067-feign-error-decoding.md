---
card: spring-cloud
gi: 67
slug: feign-error-decoding
title: "Feign error decoding"
---

## 1. What it is

By default, any non-2xx response from a Feign call throws a generic `FeignException` (or one of its status-specific subclasses like `FeignException.NotFound`), carrying the raw status code and response body. A custom `ErrorDecoder` bean (touched on in the earlier custom-configuration card, examined in depth here) intercepts this and can translate the raw HTTP failure into whatever exception type — a business-specific exception, a retryable wrapper, a swallowed default — actually fits the calling code's needs.

```java
@Configuration
class BillingFeignConfig {
    @Bean
    ErrorDecoder errorDecoder() {
        return (methodKey, response) -> switch (response.status()) {
            case 404 -> new InvoiceNotFoundException();
            case 429 -> new RetryableException(response.status(), "rate limited", null, null, null);
            default -> new ErrorDecoder.Default().decode(methodKey, response); // fall back to Feign's default
        };
    }
}
```

## 2. Why & when

`FeignException` alone forces every caller to inspect a raw status code (`e.status() == 404`) to figure out what actually went wrong — brittle, repetitive, and easy to get subtly wrong across many call sites. A custom `ErrorDecoder` moves that translation to one place, so calling code can catch specific, meaningfully-named exception types instead, and — critically — can signal Feign's *retry* mechanism (from the earlier LoadBalancer retry card) by throwing a `RetryableException`, something a generic `FeignException` doesn't do on its own.

Reach for a custom `ErrorDecoder` when:

- Calling code needs to distinguish between different failure reasons (not found vs. rate limited vs. server error) with more than a raw status code check — specific exception types make this a compile-time-checkable `catch` clause instead of a runtime status comparison.
- Certain failures should trigger Feign's retry mechanism, but aren't naturally recognized as retryable by default — throwing `RetryableException` from the `ErrorDecoder` is exactly how to opt specific failure conditions into automatic retry.
- The downstream service's error response body carries structured information (an error code, a message) worth extracting into the thrown exception, rather than discarding it along with the rest of the raw response.

## 3. Core concept

```
 non-2xx response arrives
        |
        v
 ErrorDecoder.decode(methodKey, response)
        |
        |-- inspect response.status() and/or response.body()
        |
        |-- return a RuntimeException:
                a specific business exception       -> caller catches it specifically
                a RetryableException                 -> Feign's retry mechanism retries automatically
                ErrorDecoder.Default's own decoding   -> falls back to ordinary FeignException behavior
```

The `ErrorDecoder` is the single place that turns "the HTTP call failed" into "here is exactly what that means and what should happen next."

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A non 2xx response is routed through a custom ErrorDecoder that inspects the status code and returns either a specific business exception, a retryable exception that triggers Feign retry, or falls back to default handling">
  <rect x="30" y="70" width="150" height="40" rx="8" fill="#e6494930" stroke="#e64949" stroke-width="1.3"/>
  <text x="105" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">non-2xx response</text>

  <rect x="230" y="60" width="170" height="60" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="315" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">ErrorDecoder</text>
  <text x="315" y="98" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">inspect status + body</text>

  <rect x="450" y="15" width="160" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="530" y="36" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">specific business exception</text>

  <rect x="450" y="65" width="160" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="530" y="86" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">RetryableException</text>

  <rect x="450" y="115" width="160" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="530" y="136" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">default FeignException</text>

  <line x1="180" y1="90" x2="228" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a67)"/>
  <line x1="400" y1="75" x2="448" y2="35" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a67)"/>
  <line x1="400" y1="85" x2="448" y2="82" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a67)"/>
  <line x1="400" y1="100" x2="448" y2="130" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a67)"/>

  <defs><marker id="a67" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One decoder, three possible outcomes per failure — a specific exception, an automatic retry trigger, or a fallback to default behavior.

## 5. Runnable example

The scenario: decode failures from `BillingClient` calls meaningfully. Start with generic exception handling (the status-code-checking problem), then add a custom decoder producing specific exception types, then add retryable exception signaling for a rate-limit response.

### Level 1 — Basic

Generic exception handling — every caller inspects a raw status code.

```java
public class FeignErrorDecodingLevel1 {
    static class FeignException extends RuntimeException {
        int status;
        FeignException(int status, String message) { super(message); this.status = status; }
    }

    static String getInvoice(String id, int simulatedStatus) {
        if (simulatedStatus >= 400) throw new FeignException(simulatedStatus, "call failed");
        return "{\"id\":\"" + id + "\"}";
    }

    public static void main(String[] args) {
        try {
            getInvoice("999", 404);
        } catch (FeignException e) {
            // every caller has to remember to check the raw status code themselves
            if (e.status == 404) {
                System.out.println("handled: invoice not found");
            } else {
                System.out.println("unhandled failure, status=" + e.status);
                throw e;
            }
        }
    }
}
```

How to run: `java FeignErrorDecodingLevel1.java`

Every call site that wants to handle a `404` specially has to remember to check `e.status == 404` itself — repeated, easy to get wrong, and gives no compile-time signal about which failure types are expected versus accidentally unhandled.

### Level 2 — Intermediate

Add a custom `ErrorDecoder` that translates status codes into specific, meaningfully-named exception types.

```java
public class FeignErrorDecodingLevel2 {
    static class FeignHttpFailure { int status; String body; FeignHttpFailure(int status, String body) { this.status = status; this.body = body; } }

    static class InvoiceNotFoundException extends RuntimeException {
        InvoiceNotFoundException(String id) { super("invoice " + id + " not found"); }
    }
    static class BillingServiceUnavailableException extends RuntimeException {
        BillingServiceUnavailableException() { super("billing-service is unavailable"); }
    }
    static class UnknownBillingException extends RuntimeException {
        UnknownBillingException(int status) { super("unexpected billing-service error: " + status); }
    }

    interface ErrorDecoder { RuntimeException decode(String requestedId, FeignHttpFailure failure); }

    static ErrorDecoder billingErrorDecoder = (id, failure) -> switch (failure.status) {
        case 404 -> new InvoiceNotFoundException(id);
        case 503 -> new BillingServiceUnavailableException();
        default -> new UnknownBillingException(failure.status);
    };

    static String getInvoice(String id, FeignHttpFailure simulatedFailure) {
        if (simulatedFailure != null) throw billingErrorDecoder.decode(id, simulatedFailure);
        return "{\"id\":\"" + id + "\"}";
    }

    public static void main(String[] args) {
        try { getInvoice("999", new FeignHttpFailure(404, "")); }
        catch (InvoiceNotFoundException e) { System.out.println("caught specifically: " + e.getMessage()); }

        try { getInvoice("42", new FeignHttpFailure(503, "")); }
        catch (BillingServiceUnavailableException e) { System.out.println("caught specifically: " + e.getMessage()); }
    }
}
```

How to run: `java FeignErrorDecodingLevel2.java`

`billingErrorDecoder` maps each status code to its own specific exception type — calling code now catches `InvoiceNotFoundException` and `BillingServiceUnavailableException` as distinct, named types rather than branching on a raw status field, which the compiler can help enforce (unhandled specific `catch` clauses are visible in the code, rather than an easily-missed `if (status == ...)` check).

### Level 3 — Advanced

Add retryable exception signaling: a `429 Too Many Requests` response should trigger Feign's automatic retry mechanism (from the earlier LoadBalancer retry card) rather than immediately failing, since rate limiting is often transient.

```java
import java.util.*;
import java.util.function.Supplier;

public class FeignErrorDecodingLevel3 {
    static class FeignHttpFailure { int status; FeignHttpFailure(int status) { this.status = status; } }

    static class InvoiceNotFoundException extends RuntimeException {
        InvoiceNotFoundException(String id) { super("invoice " + id + " not found"); }
    }
    static class RetryableException extends RuntimeException {
        RetryableException(String message) { super(message); }
    }

    interface ErrorDecoder { RuntimeException decode(String requestedId, FeignHttpFailure failure); }

    static ErrorDecoder billingErrorDecoder = (id, failure) -> switch (failure.status) {
        case 404 -> new InvoiceNotFoundException(id);
        case 429 -> new RetryableException("rate limited, safe to retry"); // signals: try again
        default -> new RuntimeException("unexpected error: " + failure.status);
    };

    // models Feign's retry-aware call dispatch: RetryableException triggers automatic retry, others propagate directly
    static String callWithRetryAwareness(String id, Supplier<FeignHttpFailure> simulatedFailures, int maxRetries) {
        RuntimeException lastError = null;
        for (int attempt = 0; attempt <= maxRetries; attempt++) {
            FeignHttpFailure failure = simulatedFailures.get();
            if (failure == null) return "{\"id\":\"" + id + "\"}"; // success
            RuntimeException decoded = billingErrorDecoder.decode(id, failure);
            if (decoded instanceof RetryableException) {
                System.out.println("attempt " + attempt + ": retryable failure (" + decoded.getMessage() + "), retrying");
                lastError = decoded;
                continue; // Feign's retry mechanism would automatically re-attempt here
            }
            throw decoded; // non-retryable -- propagate immediately, no further attempts
        }
        throw lastError; // exhausted retries
    }

    public static void main(String[] args) {
        int[] callCount = {0};
        Supplier<FeignHttpFailure> rateLimitedThenSucceeds = () -> {
            callCount[0]++;
            return callCount[0] < 3 ? new FeignHttpFailure(429) : null; // fails twice with 429, then succeeds
        };

        String result = callWithRetryAwareness("42", rateLimitedThenSucceeds, 3);
        System.out.println("final result: " + result);
    }
}
```

How to run: `java FeignErrorDecodingLevel3.java`

`billingErrorDecoder` maps `429` to a `RetryableException` rather than an immediately-fatal one — `callWithRetryAwareness` checks specifically for that type and, when it sees one, continues its retry loop instead of throwing, modeling how Feign's own retry mechanism recognizes `RetryableException` as a signal to automatically re-attempt the call. The simulated backend fails with `429` twice before succeeding, and the retry loop correctly absorbs both failures, ultimately returning the successful response to the caller.

## 6. Walkthrough

Trace `callWithRetryAwareness`'s execution in Level 3.

1. `attempt=0` runs first — `simulatedFailures.get()` increments `callCount` to `1`, and since `1 < 3`, returns `FeignHttpFailure(429)`. `billingErrorDecoder.decode("42", failure)` matches `case 429`, returning a `RetryableException`. The `instanceof RetryableException` check is `true`, so the method prints the retry message and `continue`s the loop rather than throwing.
2. `attempt=1` runs — `callCount` becomes `2`, still `< 3`, so another `FeignHttpFailure(429)` comes back, decoded to another `RetryableException`, and the loop retries again.
3. `attempt=2` runs — `callCount` becomes `3`, no longer `< 3`, so `simulatedFailures.get()` returns `null` this time, meaning success. `callWithRetryAwareness` returns the successful response string immediately, without ever reaching the `RetryableException` handling for this attempt.
4. The final `println` shows `{"id":"42"}` — the caller received a successful result despite two underlying `429` failures, because the `ErrorDecoder`'s choice to classify `429` as retryable let the retry loop absorb both transient failures transparently.

```
attempt 0 -> 429 -> RetryableException -> retry
attempt 1 -> 429 -> RetryableException -> retry
attempt 2 -> success -> return {"id":"42"} immediately
```

## 7. Gotchas & takeaways

> **Gotcha:** throwing `RetryableException` from an `ErrorDecoder` for a status code that *isn't* actually safe to retry (a `POST` that might have partially succeeded server-side before failing, for instance) reintroduces the exact double-execution risk covered in the earlier Gateway `Retry` filter card — `ErrorDecoder`-driven retry needs the same idempotency discipline as any other automatic retry mechanism, not an exemption from it just because the decision lives in a different layer.

- A custom `ErrorDecoder` turns generic HTTP failure handling into specific, meaningfully-named exception types that calling code can catch precisely, replacing scattered raw status-code checks with a single, centralized translation.
- Returning `RetryableException` from the decoder is the specific mechanism for opting a failure condition into Feign's automatic retry behavior — not every failure should be retryable, and the decoder is exactly where that judgment call belongs.
- Falling back to `new ErrorDecoder.Default().decode(methodKey, response)` for status codes the custom logic doesn't specifically handle keeps the rest of Feign's default exception behavior intact — a custom decoder doesn't need to reinvent handling for every possible status code, only the ones worth specific treatment.
- This pattern — a single point of translation between a raw failure signal and a meaningful application-level type — mirrors the Gateway `ErrorDecoder`/`CircuitBreaker` and LoadBalancer retry concepts covered earlier; recognizing the recurring shape (raw failure in, meaningful decision out) makes each new instance of it faster to understand.
