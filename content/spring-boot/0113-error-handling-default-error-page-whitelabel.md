---
card: spring-boot
gi: 113
slug: error-handling-default-error-page-whitelabel
title: Error handling (default error page / whitelabel)
---

## 1. What it is

Spring Boot provides automatic error handling through `BasicErrorController`, which maps to `/error` and serves error responses in two formats:
- **HTML**: returns the "Whitelabel Error Page" for browser requests (`Accept: text/html`).
- **JSON**: returns a machine-readable error body for API clients (`Accept: application/json`).

The default JSON error response:
```json
{
  "timestamp": "2026-06-28T10:15:30.000+00:00",
  "status": 404,
  "error": "Not Found",
  "path": "/api/missing"
}
```

The **Whitelabel Error Page** is the HTML fallback Spring Boot shows in a browser when no custom error template exists. It shows the HTTP status, a short description, and the exception message. It is intentionally minimal — designed to be replaced in production.

`ErrorMvcAutoConfiguration` wires all of this:
- Registers `BasicErrorController` at `/error`.
- Sets the Servlet error page to point at `/error` for all error codes.
- Registers `DefaultErrorAttributes` to populate the error model.

## 2. Why & when

The default error handler works immediately with zero configuration. Understanding it helps when:
- You want to **suppress the Whitelabel Error Page** to show a custom HTML error page.
- You want to return a **custom JSON error body** (different field names, extra fields, no stack trace).
- You need different error behavior for browser vs. API clients (the default already does this via `Accept` header).
- You are building a **REST API** and want consistent, structured error responses for all exception types.
- You need to **log exceptions** at the error handler level.

## 3. Core concept

Error flow:

```
Exception thrown in @Controller
  → ExceptionHandlerExceptionResolver tries @ExceptionHandler / @ControllerAdvice
  → If unhandled: Servlet sets error attributes on request, forwards to /error
  → BasicErrorController at /error reads error attributes
  → Content negotiation: HTML → Whitelabel page | JSON → error body
```

`DefaultErrorAttributes` populates these keys:
- `timestamp` — when the error occurred.
- `status` — HTTP status code.
- `error` — HTTP status reason phrase.
- `exception` — exception class name (only if `server.error.include-exception=true`).
- `message` — exception message (only if `server.error.include-message=always`).
- `trace` — stack trace (only if `server.error.include-stacktrace=always`).
- `path` — request URI.

Key properties:
```properties
server.error.include-message=always        # include exception message in response
server.error.include-stacktrace=never      # never expose stack traces to clients
server.error.include-exception=false       # hide exception class name
server.error.whitelabel.enabled=false      # disable Whitelabel HTML page
server.error.path=/error                   # path to error controller (default)
```

## 4. Diagram

<svg viewBox="0 0 680 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot error handling: exception goes through exception resolvers, falls to BasicErrorController at /error which returns JSON or HTML based on Accept header">
  <rect x="8" y="8" width="664" height="254" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Default Error Handling Pipeline</text>

  <!-- Exception -->
  <rect x="20" y="55" width="150" height="44" rx="5" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="95" y="73" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Exception thrown</text>
  <text x="95" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">in @Controller</text>

  <defs><marker id="eh" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="172" y1="77" x2="200" y2="77" stroke="#8b949e" stroke-width="1.5" marker-end="url(#eh)"/>

  <!-- @ExceptionHandler -->
  <rect x="202" y="55" width="165" height="44" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="284" y="73" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">@ExceptionHandler /</text>
  <text x="284" y="87" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">@ControllerAdvice</text>

  <!-- No match → /error -->
  <line x1="369" y1="77" x2="397" y2="77" stroke="#8b949e" stroke-width="1" stroke-dasharray="3 2" marker-end="url(#eh)"/>
  <text x="383" y="70" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">no match</text>

  <!-- Servlet error -->
  <rect x="399" y="55" width="175" height="44" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="486" y="73" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Servlet sets error attrs</text>
  <text x="486" y="87" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">forward to /error</text>

  <line x1="486" y1="100" x2="486" y2="120" stroke="#8b949e" stroke-width="1.5" marker-end="url(#eh)"/>

  <!-- BasicErrorController -->
  <rect x="270" y="122" width="220" height="44" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="380" y="140" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">BasicErrorController at /error</text>
  <text x="380" y="155" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">reads DefaultErrorAttributes</text>

  <line x1="486" y1="120" x2="445" y2="122" stroke="#8b949e" stroke-width="1" marker-end="url(#eh)"/>

  <!-- Content negotiation -->
  <line x1="380" y1="167" x2="380" y2="187" stroke="#8b949e" stroke-width="1.5" marker-end="url(#eh)"/>

  <rect x="100" y="189" width="200" height="52" rx="5" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="200" y="207" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">Accept: text/html</text>
  <text x="200" y="220" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Whitelabel HTML page</text>
  <text x="200" y="233" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(or custom error template)</text>

  <rect x="382" y="189" width="200" height="52" rx="5" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="482" y="207" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">Accept: application/json</text>
  <text x="482" y="220" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">{"status":404,"error":…}</text>
  <text x="482" y="233" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(machine-readable)</text>

  <line x1="270" y1="200" x2="260" y2="200" stroke="#8b949e" stroke-width="1" marker-end="url(#eh)"/>
  <line x1="490" y1="167" x2="490" y2="187" stroke="#8b949e" stroke-width="1" stroke-dasharray="3 2"/>
</svg>

`BasicErrorController` content-negotiates: HTML for browser, JSON for API clients.

## 5. Runnable example

```java
// DefaultErrorHandling.java — run: java DefaultErrorHandling.java  (JDK 17+)
// Simulates Spring Boot's error attribute collection and response format selection.

import java.time.Instant;
import java.util.*;

public class DefaultErrorHandling {

    // Simulates DefaultErrorAttributes populated during error forwarding
    static Map<String, Object> buildErrorAttributes(
            int status, String errorReason, String exceptionMessage,
            String path, boolean includeMessage, boolean includeTrace, String trace) {

        Map<String, Object> attrs = new LinkedHashMap<>();
        attrs.put("timestamp", Instant.now().toString());
        attrs.put("status", status);
        attrs.put("error", errorReason);
        if (includeMessage && exceptionMessage != null)
            attrs.put("message", exceptionMessage);
        if (includeTrace && trace != null)
            attrs.put("trace", trace);
        attrs.put("path", path);
        return attrs;
    }

    // Simulates BasicErrorController's JSON response
    static String toJson(Map<String, Object> attrs) {
        StringBuilder sb = new StringBuilder("{\n");
        attrs.forEach((k, v) ->
            sb.append("  \"").append(k).append("\": \"").append(v).append("\",\n"));
        if (sb.length() > 2) sb.setLength(sb.length() - 2);
        return sb.append("\n}").toString();
    }

    // Simulates the Whitelabel HTML page
    static String toWhitelabelHtml(Map<String, Object> attrs) {
        return String.format("""
<html><body>
<h1>Whitelabel Error Page</h1>
<p>This application has no explicit mapping for /error,
   so you are seeing this as a fallback.</p>
<div id='created'>%s</div>
<div>There was an unexpected error (type=%s, status=%s).</div>
<div>%s</div>
</body></html>""",
                attrs.get("timestamp"), attrs.get("error"), attrs.get("status"),
                attrs.getOrDefault("message", "No message available"));
    }

    static void simulate(String scenario, int status, String reason,
                          String msg, String path, String acceptHeader,
                          boolean includeMessage) {
        System.out.println("Scenario: " + scenario);
        System.out.println("  Status=" + status + " Accept=" + acceptHeader);
        Map<String, Object> attrs = buildErrorAttributes(status, reason, msg, path,
                includeMessage, false, null);
        if (acceptHeader.contains("text/html")) {
            System.out.println("  Response (HTML):");
            System.out.println("  " + toWhitelabelHtml(attrs).replace("\n", "\n  "));
        } else {
            System.out.println("  Response (JSON):");
            System.out.println("  " + toJson(attrs).replace("\n", "\n  "));
        }
        System.out.println();
    }

    public static void main(String[] args) {
        System.out.println("=== Default Spring Boot error responses ===\n");

        simulate("404 from browser (Whitelabel page)",
                404, "Not Found", "No message available", "/api/missing",
                "text/html,application/xhtml+xml", false);

        simulate("404 from API client (JSON)",
                404, "Not Found", null, "/api/missing",
                "application/json", false);

        simulate("500 with message exposed (server.error.include-message=always)",
                500, "Internal Server Error",
                "NullPointerException in OrderService.findById",
                "/api/orders/99", "application/json", true);

        System.out.println("=== Disable Whitelabel page ===");
        System.out.println("server.error.whitelabel.enabled=false");
        System.out.println("→ Spring returns empty response; provide templates/error.html");
        System.out.println();
        System.out.println("=== Security: never expose in production ===");
        System.out.println("server.error.include-stacktrace=never   (default)");
        System.out.println("server.error.include-message=never      (default — safe)");
        System.out.println("server.error.include-exception=false    (default)");
    }
}
```

**How to run:** `java DefaultErrorHandling.java`

## 6. Walkthrough

- `buildErrorAttributes` mirrors `DefaultErrorAttributes.getErrorAttributes()`. The `includeMessage` flag corresponds to `server.error.include-message=always`; default is `never`, meaning the `message` field is omitted from the response. This prevents leaking internal error messages to clients.
- `toWhitelabelHtml(attrs)` renders the classic Spring Boot error HTML. The "Whitelabel Error Page" is a hard-coded template in `spring-webmvc` — it cannot be customised without disabling it. Disable it with `server.error.whitelabel.enabled=false` and provide `templates/error.html` instead.
- **Browser scenario (404)**: `Accept: text/html,…` → HTML path. `BasicErrorController.errorHtml()` is called, which tries template resolvers. No `error.html` template → Whitelabel fallback.
- **API scenario (404)**: `Accept: application/json` → JSON path. `BasicErrorController.error()` returns a `ResponseEntity<Map>` with `DefaultErrorAttributes`. The `message` field is absent by default.
- **500 with message**: `include-message=always` adds `"message": "NullPointerException…"` to the response. This helps debugging but can leak implementation details. Use `always` only in development profiles.

## 7. Gotchas & takeaways

> **Never set `server.error.include-stacktrace=always` in production.** Stack traces reveal internal package structure, library versions, and logic paths — all useful to an attacker for crafting more targeted exploits. Spring Boot defaults to `never`; keep it that way in production.

> **The Whitelabel Error Page appears when no custom error template exists.** It is not an error in itself — it's a fallback view. To replace it: (1) add `templates/error.html` (Thymeleaf) or (2) set `server.error.whitelabel.enabled=false`. If you disable it with no replacement, browsers receive an empty HTML response body.

- `server.error.include-message=on-param` (Spring Boot 2.3+) exposes the message only when the request includes `?message=true` — useful for a debug-on-demand pattern.
- `ErrorController` interface: to replace `BasicErrorController` entirely, implement `ErrorController` and declare the `@RequestMapping("/error")` method yourself. Spring Boot backs off its `BasicErrorController`.
- `DefaultErrorAttributes` can be extended: declare a `@Bean DefaultErrorAttributes` subclass to add or remove fields from the error model.
- HTTP 400 (Bad Request) from validation failures (`@Valid`): Spring Boot includes a `errors` list in the response (each binding error). This is separate from the `message` field and is always included when validation fails via `MethodArgumentNotValidException`.
