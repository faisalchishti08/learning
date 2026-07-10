---
card: spring-framework
gi: 377
slug: reactive-exception-handling
title: "Reactive exception handling"
---

## 1. What it is

Reactive exception handling covers how errors propagate and are handled in WebFlux — both the framework-level mechanisms (`@ExceptionHandler`/`@ControllerAdvice`, working almost identically to Spring MVC) and the reactive-pipeline-level operators (`onErrorResume`, `onErrorReturn`, `onErrorMap`, `retry`) used *inside* `Mono`/`Flux` chains to handle errors before they even reach the framework's own exception-handling layer.

```java
@GetMapping("/products/{id}")
public Mono<Product> get(@PathVariable long id) {
    return productRepository.findById(id)
        .switchIfEmpty(Mono.error(new ProductNotFoundException(id)));
}

@ExceptionHandler(ProductNotFoundException.class)
public ResponseEntity<String> handle(ProductNotFoundException ex) {
    return ResponseEntity.status(404).body(ex.getMessage());
}
```

## 2. Why & when

An exception thrown imperatively (`throw new RuntimeException(...)`) inside ordinary Java code immediately unwinds the call stack. In a reactive pipeline, "throwing" doesn't quite work the same way — an error becomes a **signal** (`onError`, per the Reactive Streams specification covered earlier) that propagates downstream through the operator chain, and each operator gets an opportunity to observe, transform, or recover from it before it ever reaches `@ExceptionHandler`/`@ControllerAdvice` (which still function as the final, framework-level safety net, exactly as in Spring MVC).

Understanding both layers matters because:

- **Operator-level handling** (`onErrorResume`, etc.) is often the *right* place to recover from an error close to where it occurred — providing a fallback value, retrying a transient failure, or transforming one exception type into another more meaningful one for the caller.
- **`@ExceptionHandler`/`@ControllerAdvice`** remains the right place for consistent, application-wide HTTP-response formatting for errors that *do* reach the controller boundary — the two layers are complementary, not competing.
- A reactive pipeline that never handles an error at the operator level and never has a matching `@ExceptionHandler` will still produce *some* response (typically a generic `500`), but understanding exactly where and how errors are caught avoids both silent failures and overly broad, unhelpful catch-alls.

## 3. Core concept

```
Error propagation through a reactive pipeline:

  source.map(fn1).filter(pred).flatMap(fn2).subscribe(...)

  If fn1 throws (or the source itself errors):
    the ERROR SIGNAL skips REMAINING onNext-style operators
    (filter, flatMap's normal path) and propagates directly
    downstream looking for an error-HANDLING operator

Operator-level recovery (applied INLINE in the pipeline):

  .onErrorReturn(fallbackValue)          — replace error with a FIXED value
  .onErrorResume(ex -> Mono.just(...))    — replace error with ANOTHER Mono/Flux
  .onErrorMap(ex -> new OtherException()) — TRANSFORM the exception type, still errors
  .retry(3)                                — RESUBSCRIBE (retry) up to 3 times on error
  .retryWhen(spec)                         — retry with backoff/conditional logic

Framework-level handling (the FINAL safety net, same as Spring MVC):

  @ExceptionHandler(SpecificException.class)  — in the same controller
  @RestControllerAdvice                        — application-wide

  If NEITHER operator-level recovery NOR a matching @ExceptionHandler
  exists, WebFlux's default error handling produces a generic 500.
```

## 4. Diagram

<svg viewBox="0 0 740 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="220" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">Two layers of reactive error handling</text>

  <rect x="20" y="50" width="330" height="70" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="185" y="72" text-anchor="middle" fill="#6db33f" font-size="11">Operator-level (inline in the pipeline)</text>
  <text x="35" y="95" fill="#8b949e" font-size="9">onErrorResume / onErrorReturn / retry</text>
  <text x="35" y="110" fill="#8b949e" font-size="9">close to the source, most specific</text>

  <rect x="390" y="50" width="330" height="70" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="555" y="72" text-anchor="middle" fill="#79c0ff" font-size="11">Framework-level (final safety net)</text>
  <text x="405" y="95" fill="#8b949e" font-size="9">@ExceptionHandler / @ControllerAdvice</text>
  <text x="405" y="110" fill="#8b949e" font-size="9">consistent HTTP response shaping</text>

  <line x1="185" y1="120" x2="350" y2="160" stroke="#8b949e" marker-end="url(#a53)"/>
  <line x1="555" y1="120" x2="390" y2="160" stroke="#8b949e" marker-end="url(#a53)"/>

  <rect x="220" y="160" width="300" height="40" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="370" y="185" text-anchor="middle" fill="#e6edf3" font-size="10">unhandled -&gt; generic 500</text>

  <defs>
    <marker id="a53" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*An error that's recovered from at the operator level never reaches `@ExceptionHandler`; only errors that genuinely propagate to the controller boundary do.*

## 5. Runnable example

### Level 1 — Basic

`@ExceptionHandler` in a reactive controller — nearly identical to the Spring MVC version:

```java
// ProductController.java
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {

    static class ProductNotFoundException extends RuntimeException {
        ProductNotFoundException(long id) { super("Product " + id + " not found"); }
    }

    @GetMapping("/products/{id}")
    public Mono<String> get(@PathVariable long id) {
        if (id != 1) {
            return Mono.error(new ProductNotFoundException(id));
        }
        return Mono.just("Drill");
    }

    @ExceptionHandler(ProductNotFoundException.class)
    public ResponseEntity<String> handleNotFound(ProductNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(ex.getMessage());
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/1
# HTTP/1.1 200 OK
# Drill

curl -i http://localhost:8080/products/99
# HTTP/1.1 404 Not Found
# Product 99 not found
```

`Mono.error(new ProductNotFoundException(99))` constructs a `Mono` that, once subscribed, immediately emits an error signal instead of a value — this error signal propagates all the way to WebFlux's exception-resolution machinery, which finds and invokes the matching `@ExceptionHandler`, exactly mirroring the equivalent Spring MVC mechanism.

### Level 2 — Intermediate

Operator-level recovery with `onErrorResume`, intercepting an error *before* it would otherwise reach `@ExceptionHandler` — demonstrating that operator-level handling takes priority simply by virtue of being earlier in the pipeline:

```java
// ProductController.java (extended)
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.time.Duration;

@RestController
public class ProductController {

    static class ExternalServiceException extends RuntimeException {
        ExternalServiceException(String msg) { super(msg); }
    }

    @GetMapping("/products/{id}/price")
    public Mono<Double> getPrice(@PathVariable long id) {
        return fetchPriceFromExternalService(id)
            .onErrorResume(ExternalServiceException.class, ex -> {
                System.out.println("External service failed, using cached fallback: " + ex.getMessage());
                return Mono.just(0.0);   // fallback: a cached/default price instead of failing the request
            });
    }

    private Mono<Double> fetchPriceFromExternalService(long id) {
        if (id == 99) {
            return Mono.error(new ExternalServiceException("pricing service timeout"));
        }
        return Mono.just(29.99);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/1/price
# 29.99

curl http://localhost:8080/products/99/price
# 0.0
# server log: "External service failed, using cached fallback: pricing service timeout"
```

**What changed:** The `ExternalServiceException` never reaches any `@ExceptionHandler` at all — `onErrorResume` intercepts it right where it's most relevant (immediately after the call that could fail) and substitutes a fallback value, so the client receives a normal `200 OK` with a default price rather than any error response whatsoever. This is a deliberate choice appropriate when a sensible fallback exists; contrast with Level 1, where no fallback made sense and letting the error propagate to a `404` response was the correct behavior.

### Level 3 — Advanced

Production pattern: combining `retry` (for transient failures), `onErrorMap` (translating a low-level exception into a domain-meaningful one), and a global `@RestControllerAdvice` for the final, unrecovered cases — layering all three mechanisms coherently:

```java
// GlobalExceptionHandler.java
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ProductController.ProductNotFoundException.class)
    public ProblemDetail handleNotFound(ProductController.ProductNotFoundException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
    }

    @ExceptionHandler(ProductController.PricingUnavailableException.class)
    public ProblemDetail handlePricingUnavailable(ProductController.PricingUnavailableException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.SERVICE_UNAVAILABLE, ex.getMessage());
    }

    // Catch-all — anything that reaches HERE was neither recovered at the
    // operator level nor matched a more specific handler above.
    @ExceptionHandler(Exception.class)
    public ProblemDetail handleUnexpected(Exception ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.INTERNAL_SERVER_ERROR, "Unexpected error occurred");
    }
}
```

```java
// ProductController.java (production version)
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;
import reactor.util.retry.Retry;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;

@RestController
public class ProductController {

    static class ProductNotFoundException extends RuntimeException {
        ProductNotFoundException(long id) { super("Product " + id + " not found"); }
    }
    static class PricingUnavailableException extends RuntimeException {
        PricingUnavailableException(String msg) { super(msg); }
    }
    static class TransientServiceException extends RuntimeException {
        TransientServiceException(String msg) { super(msg); }
    }

    private final AtomicInteger attemptCounter = new AtomicInteger(0);

    @GetMapping("/products/{id}/price")
    public Mono<Double> getPrice(@PathVariable long id) {
        return callPricingService(id)
            // Retry up to 2 times for TRANSIENT failures, with a short backoff
            .retryWhen(Retry.backoff(2, Duration.ofMillis(100))
                .filter(ex -> ex instanceof TransientServiceException))
            // Translate a LOW-LEVEL exception into a MEANINGFUL domain one,
            // only reached if retries are exhausted
            .onErrorMap(TransientServiceException.class,
                ex -> new PricingUnavailableException("Pricing temporarily unavailable"));
    }

    private Mono<Double> callPricingService(long id) {
        int attempt = attemptCounter.incrementAndGet();
        if (attempt < 3) {
            return Mono.error(new TransientServiceException("attempt " + attempt + " failed"));
        }
        return Mono.just(29.99);   // succeeds on the 3rd attempt (2 retries)
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/1/price
# 29.99     <- succeeds after internal retries (transparent to the client)

curl -i http://localhost:8080/products/99
# 404 Not Found — {"status":404,"detail":"Product 99 not found"}   (via GlobalExceptionHandler)
```

**What changed and why:**
- `.retryWhen(Retry.backoff(2, Duration.ofMillis(100)).filter(...))` automatically re-subscribes to `callPricingService(id)` up to twice more (three total attempts) with a short delay between attempts, specifically only for `TransientServiceException` — this is the reactive idiom for resilience against genuinely transient failures (a momentary network blip, a brief service restart), handled entirely within the pipeline, invisible to the client if it eventually succeeds.
- `.onErrorMap(TransientServiceException.class, ex -> new PricingUnavailableException(...))` only fires if retries are exhausted and the error still persists — it translates the low-level, implementation-specific exception into a domain-meaningful one (`PricingUnavailableException`) that `GlobalExceptionHandler` has a specific, well-formatted response for, rather than letting the raw `TransientServiceException` leak to the client or fall into the generic catch-all.
- The generic `@ExceptionHandler(Exception.class)` in `GlobalExceptionHandler` remains as the final safety net for anything genuinely unanticipated — exactly mirroring the equivalent Spring MVC pattern from earlier cards, demonstrating that this framework-level layer works identically regardless of how much operator-level recovery happens upstream.

## 6. Walkthrough

**Request: `GET /products/1/price` (Level 3 code, transient failures then success).**

1. `DispatcherHandler` dispatches to `getPrice(1)`. The method builds a pipeline: `callPricingService(1).retryWhen(...).onErrorMap(...)`, then returns this composed `Mono<Double>` — no actual work has happened yet, per reactive laziness.
2. WebFlux subscribes to this returned `Mono` to produce the response. This triggers `callPricingService(1)`'s first execution: `attemptCounter.incrementAndGet()` → `1`. Since `1 < 3`, it returns `Mono.error(new TransientServiceException("attempt 1 failed"))`.
3. This error signal reaches `.retryWhen(...)`. The configured `Retry.backoff(2, ...)` spec checks its `.filter(ex -> ex instanceof TransientServiceException)` — the thrown exception matches, so a retry is permitted. `retryWhen` waits approximately 100ms (the configured backoff), then **re-subscribes** to the entire upstream `callPricingService(1)` call — this is a genuine re-execution, not a replay of cached data.
4. Second attempt: `attemptCounter.incrementAndGet()` → `2`. Still `2 < 3`, so it errors again with `"attempt 2 failed"`. `retryWhen` permits a second retry (within its configured maximum of `2`), waits again, and re-subscribes.
5. Third attempt: `attemptCounter.incrementAndGet()` → `3`. Now `3 < 3` is `false`, so `callPricingService` returns `Mono.just(29.99)` — a genuine success this time.
6. Because this attempt succeeded, `retryWhen`'s job is done — the successful value `29.99` propagates downstream. `.onErrorMap(...)` is an error-signal-only operator; since no error signal reached it (the pipeline succeeded), it has no effect and simply passes `29.99` through unchanged.
7. The handler's `Mono<Double>` resolves to `29.99`, which WebFlux serializes as the response body.
8. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   29.99
   ```

The entire retry sequence (two failed attempts, ~200ms of backoff delay, one successful attempt) happens transparently within the reactive pipeline — from the client's perspective, this was a single request that simply took slightly longer than usual to succeed, with no visibility into the internal retries at all.

## 7. Gotchas & takeaways

> **`onErrorResume`/`onErrorReturn` placed too early in a pipeline can accidentally swallow errors that a later, more specific handler downstream was meant to catch.** Order matters: place broad catch-alls (`onErrorResume(Exception.class, ...)`) after more specific ones (`onErrorResume(SpecificException.class, ...)`) in the same chain, or better, avoid overly broad operator-level catches entirely and let genuinely unanticipated errors reach `@ExceptionHandler`'s catch-all instead.

> **`retryWhen` re-executes the ENTIRE upstream pipeline on each retry, not just the specific operation that failed** — if upstream operators have side effects (writing to a database, sending a notification), a naive `retry`/`retryWhen` can cause those side effects to repeat unintentionally. Scope retries narrowly around just the specific, genuinely-retriable operation, not an entire multi-step pipeline with side effects.

> **An error signal that reaches `subscribe()` without an explicit error callback is either logged (via Reactor's default `Operators.onErrorDropped` hook, often producing confusing "operator called default onErrorDropped" log messages) or silently swallowed, depending on context** — always provide an explicit error handler in `subscribe(onNext, onError)` calls outside the WebFlux request-handling context (which does supply its own error handling automatically), such as in fire-and-forget background subscriptions.

- Reactive errors propagate as `onError` signals through the pipeline, giving each operator a chance to observe, transform, or recover before reaching `@ExceptionHandler`/`@ControllerAdvice`, WebFlux's framework-level final safety net.
- `onErrorResume`/`onErrorReturn` provide inline fallback values; `onErrorMap` translates exception types; `retry`/`retryWhen` re-attempt a failed operation, often with backoff, for transient failures.
- `@ExceptionHandler`/`@ControllerAdvice` work almost identically to Spring MVC — only errors that aren't fully recovered at the operator level reach this layer.
- Scope retries narrowly around the specific retriable operation to avoid unintentionally repeating upstream side effects on each retry attempt.
