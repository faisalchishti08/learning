---
card: spring-boot
gi: 114
slug: custom-error-pages-controlleradvice
title: Custom error pages & @ControllerAdvice
---

## 1. What it is

Spring Boot provides two complementary mechanisms for customising error responses:

**1. Custom error pages** — template-based HTML error pages. Place a template named `error.html` (or `error/404.html`, `error/5xx.html`) in `src/main/resources/templates/`. Spring Boot's `DefaultErrorViewResolver` serves them automatically for browser requests.

**2. `@ControllerAdvice` with `@ExceptionHandler`** — programmatic exception handling for controllers. A class annotated `@ControllerAdvice` acts as a global `@Controller` that can handle exceptions thrown by any `@Controller` in the application. Return a custom error response object or a view name.

Both work together:
- `@ControllerAdvice` intercepts exceptions **before** they reach `BasicErrorController`.
- Custom error templates handle errors that slip through (HTTP-level 404s, unhandled exceptions).

## 2. Why & when

Use **custom error templates** when:
- You want a branded HTML error page (with your app's header, footer, support email).
- You serve a mix of HTML and JSON and need separate error presentation for the browser.
- You want per-status-code pages (`404.html`, `500.html`, `503.html`).

Use **`@ControllerAdvice`** when:
- You build a REST API and want all exceptions to produce a consistent JSON error body.
- You want to map specific exception types to specific HTTP status codes (`ResourceNotFoundException` → 404).
- You want to log exceptions centrally or add request-correlation IDs to error responses.
- You want to return validation errors in a custom format.

## 3. Core concept

**Custom error templates** — name resolution:

```
templates/error/404.html     ← most specific (exact status)
templates/error/4xx.html     ← medium (status series)
templates/error/error.html   ← least specific (catch-all)
templates/error.html         ← also catch-all (root level)
```

The Thymeleaf model available in these templates:
- `${status}` — HTTP status code
- `${error}` — HTTP status reason
- `${message}` — error message (if `server.error.include-message=always`)
- `${path}` — request path
- `${timestamp}` — error time

**`@ControllerAdvice`** structure:

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleNotFound(ResourceNotFoundException ex) {
        return new ErrorResponse("NOT_FOUND", ex.getMessage());
    }

    @ExceptionHandler(ConstraintViolationException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorResponse handleValidation(ConstraintViolationException ex) {
        return new ErrorResponse("VALIDATION_ERROR", ex.getMessage());
    }

    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ErrorResponse handleGeneral(Exception ex) {
        log.error("Unexpected error", ex);
        return new ErrorResponse("INTERNAL_ERROR", "An unexpected error occurred");
    }
}
```

`@RestControllerAdvice` = `@ControllerAdvice` + `@ResponseBody`. Use `@ControllerAdvice` for controllers that return view names, `@RestControllerAdvice` for JSON APIs.

## 4. Diagram

<svg viewBox="0 0 680 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Custom error pages and @ControllerAdvice: two complementary paths. @ControllerAdvice intercepts before /error; custom templates served by BasicErrorController for HTML clients.">
  <rect x="8" y="8" width="664" height="264" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Custom Error Handling — Two Paths</text>

  <!-- Exception -->
  <rect x="270" y="50" width="140" height="36" rx="5" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="340" y="68" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Exception thrown</text>
  <text x="340" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">in @Controller</text>

  <defs><marker id="ce" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#8b949e"/></marker></defs>

  <!-- Left path: @ControllerAdvice -->
  <line x1="270" y1="68" x2="195" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ce)"/>
  <rect x="20" y="103" width="220" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="130" y="121" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@ControllerAdvice</text>
  <text x="130" y="136" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@ExceptionHandler methods</text>
  <text x="130" y="150" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">intercept BEFORE /error</text>

  <line x1="130" y1="165" x2="130" y2="185" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ce)"/>
  <rect x="20" y="187" width="220" height="44" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="204" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Custom JSON / view response</text>
  <text x="130" y="218" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">ErrorResponse{code, message}</text>

  <!-- Right path: error templates -->
  <line x1="410" y1="68" x2="480" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ce)"/>
  <rect x="440" y="103" width="220" height="60" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="121" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">BasicErrorController</text>
  <text x="550" y="136" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">forwards to /error</text>
  <text x="550" y="150" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">DefaultErrorViewResolver</text>

  <line x1="550" y1="165" x2="550" y2="185" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ce)"/>
  <rect x="440" y="187" width="220" height="44" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="204" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Custom error templates</text>
  <text x="550" y="218" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">error/404.html  error/5xx.html</text>

  <!-- Center label -->
  <text x="340" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">dispatched to</text>
  <text x="198" y="92" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">@ExceptionHandler match</text>
  <text x="487" y="92" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">no handler match</text>

  <!-- Template resolution box -->
  <rect x="270" y="250" width="140" height="18" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="340" y="263" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">404 → 4xx → error (specificity order)</text>
</svg>

`@ControllerAdvice` intercepts first; custom templates handle HTML fallback via `BasicErrorController`.

## 5. Runnable example

```java
// CustomErrorPages.java — run: java CustomErrorPages.java  (JDK 17+)
// Simulates @ControllerAdvice exception dispatch and custom error template selection.

import java.util.*;

public class CustomErrorPages {

    // ── Custom exception types ────────────────────────────────────────────────
    static class ResourceNotFoundException extends RuntimeException {
        ResourceNotFoundException(String msg) { super(msg); }
    }
    static class AccessDeniedException extends RuntimeException {
        AccessDeniedException(String msg) { super(msg); }
    }
    static class ValidationException extends RuntimeException {
        ValidationException(String msg) { super(msg); }
    }

    // ── Custom error response body ────────────────────────────────────────────
    record ErrorResponse(String code, String message, int status) {
        @Override public String toString() {
            return String.format("{\"code\":\"%s\",\"message\":\"%s\",\"status\":%d}",
                    code, message, status);
        }
    }

    // ── @ControllerAdvice simulation ─────────────────────────────────────────
    static Optional<ErrorResponse> handleWithAdvice(Exception ex) {
        if (ex instanceof ResourceNotFoundException e)
            return Optional.of(new ErrorResponse("NOT_FOUND", e.getMessage(), 404));
        if (ex instanceof AccessDeniedException e)
            return Optional.of(new ErrorResponse("FORBIDDEN", e.getMessage(), 403));
        if (ex instanceof ValidationException e)
            return Optional.of(new ErrorResponse("VALIDATION_ERROR", e.getMessage(), 400));
        return Optional.empty(); // no @ExceptionHandler for this exception type
    }

    // ── Custom error template resolution ─────────────────────────────────────
    static final Set<String> TEMPLATES = Set.of(
        "error/404.html",   // exact status
        "error/5xx.html",   // 5xx series
        "error/error.html"  // catch-all
    );

    static String resolveErrorTemplate(int status) {
        // Exact match: 404 → error/404.html
        String exact = "error/" + status + ".html";
        if (TEMPLATES.contains(exact)) return exact;
        // Series match: 500, 503 → error/5xx.html
        String series = "error/" + (status / 100) + "xx.html";
        if (TEMPLATES.contains(series)) return series;
        // Catch-all
        return TEMPLATES.contains("error/error.html") ? "error/error.html" : "Whitelabel";
    }

    static void handle(String scenario, Exception ex, String acceptHeader) {
        System.out.println("Scenario: " + scenario);
        System.out.println("  Exception: " + ex.getClass().getSimpleName() + " — " + ex.getMessage());
        System.out.println("  Accept: " + acceptHeader);

        Optional<ErrorResponse> advice = handleWithAdvice(ex);
        if (advice.isPresent()) {
            ErrorResponse resp = advice.get();
            System.out.println("  @ControllerAdvice handled: HTTP " + resp.status());
            if (acceptHeader.contains("application/json")) {
                System.out.println("  Response: " + resp);
            } else {
                System.out.println("  Template: error/" + resp.status() + ".html (if exists)");
            }
        } else {
            System.out.println("  No @ExceptionHandler → forward to /error");
            System.out.println("  Status: 500 (default unhandled exception)");
            System.out.println("  Template: " + resolveErrorTemplate(500));
        }
        System.out.println();
    }

    public static void main(String[] args) {
        System.out.println("=== @ControllerAdvice + custom error templates ===\n");

        handle("API: 404 not found", new ResourceNotFoundException("Order 42 not found"),
               "application/json");

        handle("Browser: 404 not found", new ResourceNotFoundException("Order 42 not found"),
               "text/html");

        handle("API: 403 forbidden", new AccessDeniedException("Admin access required"),
               "application/json");

        handle("Unhandled exception → fallback", new NullPointerException("Null ref in service"),
               "text/html");

        System.out.println("=== Custom error template resolution ===");
        int[] statuses = {400, 404, 403, 500, 503, 429};
        for (int s : statuses)
            System.out.printf("  %d → %s%n", s, resolveErrorTemplate(s));

        System.out.println("\n=== @ControllerAdvice scope control ===");
        System.out.println("@ControllerAdvice                   → all controllers");
        System.out.println("@ControllerAdvice(basePackages=…)   → specific package");
        System.out.println("@ControllerAdvice(assignableTypes=…) → specific controllers");
    }
}
```

**How to run:** `java CustomErrorPages.java`

## 6. Walkthrough

- `handleWithAdvice(ex)` checks the exception type in the order `@ExceptionHandler` methods would be tried. `ResourceNotFoundException` → 404; `AccessDeniedException` → 403; `ValidationException` → 400; anything else → empty (no handler).
- **API + 404**: advice handles it; returns `{"code":"NOT_FOUND","message":"Order 42 not found","status":404}` as JSON. `BasicErrorController` is never called.
- **Browser + 404**: advice still handles it (finds the `@ExceptionHandler` for `ResourceNotFoundException`). With `@ControllerAdvice` (not `@RestControllerAdvice`), returning a `String` view name like `"error/404"` is valid. Or the handler can set `@ResponseStatus(404)` and redirect to the template path.
- **Unhandled NullPointerException**: no `@ExceptionHandler` matches → Spring MVC forward to `/error` → `BasicErrorController` → `DefaultErrorViewResolver` tries `error/500.html` (not in our set) → `error/5xx.html` (in our set) → serves it.
- `resolveErrorTemplate(503)` → checks `error/503.html` (absent), checks `error/5xx.html` (present) → returns `error/5xx.html`. This matches `DefaultErrorViewResolver`'s resolution logic exactly.

## 7. Gotchas & takeaways

> **`@ExceptionHandler` in `@ControllerAdvice` does NOT handle errors produced by Spring Security filters.** Security exceptions (`AccessDeniedException`, `AuthenticationException`) are thrown inside servlet filters, before the `DispatcherServlet`. They bypass `@ControllerAdvice`. Handle them in Spring Security's `AuthenticationEntryPoint` or `AccessDeniedHandler`.

> **A `@ControllerAdvice` that handles `Exception.class` as a catch-all must log carefully.** Every unhandled exception in every controller goes through it. Without careful logging, you lose the original stack trace. Always log at `ERROR` level with the original exception: `log.error("Unhandled error", ex)`.

- Place `@ControllerAdvice` in a shared package visible to all controllers — typically `com.example.error` or alongside `@SpringBootApplication`.
- `@ResponseStatus` on the `@ExceptionHandler` method sets the HTTP status. Alternatively, return `ResponseEntity<ErrorResponse>` with the status set programmatically.
- Custom error templates receive the same Thymeleaf model as the Whitelabel page: `${status}`, `${error}`, `${message}`, `${path}`, `${timestamp}`.
- `ProblemDetail` (Spring 6 / Spring Boot 3) is the RFC 9457–standard error response format — use it instead of a custom `ErrorResponse` record for interoperable APIs.
- `@ControllerAdvice` advice beans are ordered by `@Order` / `Ordered` — lower value runs first. Useful when multiple advice classes handle overlapping exception hierarchies.
