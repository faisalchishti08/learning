---
card: spring-framework
gi: 364
slug: error-handling-pages
title: "Error handling pages"
---

## 1. What it is

Error handling pages are Spring Boot's mechanism for rendering a human-friendly HTML (or JSON) response when a request fails with an error the application didn't explicitly handle — a `404` for an unmapped URL, a `500` for an uncaught exception, or any other error status reaching the servlet container's error-handling machinery. Spring Boot autoconfigures a `BasicErrorController` and a default `/error` mapping; you customize the *appearance* by dropping a template named after the status code (or a generic fallback) into a conventional location, and customize the *data* via `ErrorAttributes`.

```
src/main/resources/templates/error/404.html
src/main/resources/templates/error/5xx.html
src/main/resources/templates/error/error.html   <- generic fallback for any status
```

## 2. Why & when

Every application eventually serves an error a developer didn't anticipate — a mistyped URL, a downstream service outage causing a `500`, a client requesting a resource that no longer exists. Spring Boot's default error page (a generic Whitelabel error page, or a bare JSON error body for API clients) is functional but unbranded and unhelpful to end users. Custom error pages matter when:

- The application serves human users in a browser, and a raw stack trace or generic Whitelabel page would look broken/unprofessional compared to the rest of the site's design.
- Different error categories deserve different messaging — a `404` ("page not found, here's a search box") is a fundamentally different user experience than a `500` ("something went wrong on our end, we've been notified").
- An API needs structured, consistent JSON error bodies (tying back to the `ProblemDetail`/`ErrorResponse` cards) rather than Boot's default error JSON shape, for programmatic clients.

## 3. Core concept

```
Error occurs (404, 500, uncaught exception, etc.)
        |
        v
Servlet container's error-page mechanism, configured internally
by Spring Boot, forwards the request to "/error"
        |
        v
BasicErrorController (autoconfigured) handles /error:
        |
        +-- request wants HTML (Accept: text/html)?
        |       |
        |       v
        |   resolve a VIEW for the error:
        |     templates/error/404.html         (specific status)
        |     templates/error/5xx.html          (status class fallback, e.g. any 5xx)
        |     templates/error/error.html        (generic fallback, any status)
        |
        +-- request wants JSON (Accept: application/json)?
                |
                v
            ErrorAttributes builds a Map: {timestamp, status, error, message, path}
            serialized as the JSON error response body

Template resolution precedence: EXACT status code file wins,
falling back to Nxx (status class) wins, falling back to
the generic error.html as the last resort.
```

## 4. Diagram

<svg viewBox="0 0 720 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="220" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Error template resolution: most specific to most general</text>

  <rect x="20" y="50" width="200" height="50" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="70" text-anchor="middle" fill="#6db33f" font-size="10">templates/error/404.html</text>
  <text x="120" y="88" text-anchor="middle" fill="#8b949e" font-size="9">exact status — checked FIRST</text>

  <rect x="260" y="50" width="200" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="360" y="70" text-anchor="middle" fill="#79c0ff" font-size="10">templates/error/5xx.html</text>
  <text x="360" y="88" text-anchor="middle" fill="#8b949e" font-size="9">status class fallback</text>

  <rect x="500" y="50" width="200" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="600" y="70" text-anchor="middle" fill="#8b949e" font-size="10">templates/error/error.html</text>
  <text x="600" y="88" text-anchor="middle" fill="#8b949e" font-size="9">generic last resort</text>

  <line x1="220" y1="75" x2="260" y2="75" stroke="#8b949e" stroke-dasharray="2,2" marker-end="url(#a40)"/>
  <line x1="460" y1="75" x2="500" y2="75" stroke="#8b949e" stroke-dasharray="2,2" marker-end="url(#a40)"/>
  <text x="360" y="130" text-anchor="middle" fill="#8b949e" font-size="9">tried in this order until one exists</text>

  <defs>
    <marker id="a40" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Spring Boot checks for an exact-status template first, then a status-class fallback, then the generic error page.*

## 5. Runnable example

### Level 1 — Basic

A custom `404` page and a generic fallback, using Spring Boot's conventional template locations:

```html
<!-- templates/error/404.html -->
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
<body>
  <h1>Page not found</h1>
  <p>We couldn't find <span th:text="${path}">this page</span>. Try our <a href="/">homepage</a>.</p>
</body>
</html>
```

```html
<!-- templates/error/error.html — generic fallback for anything else -->
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
<body>
  <h1>Something went wrong</h1>
  <p>Error <span th:text="${status}">500</span>. We've been notified.</p>
</body>
</html>
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/nonexistent-page
# <html>...<h1>Page not found</h1>...We couldn't find /nonexistent-page...</html>

curl http://localhost:8080/products/-1   # assume this triggers an unhandled exception -> 500
# <html>...<h1>Something went wrong</h1>...Error 500...</html>
```

No controller code was written for either page — Spring Boot's `BasicErrorController` automatically forwards any unhandled `404`/`500`/other error to the `/error` endpoint, which resolves these templates purely by naming convention (`404.html` for exact status, `error.html` as the catch-all).

### Level 2 — Intermediate

Customizing which error attributes are exposed, and adding a status-class fallback (`5xx.html`) for any server error not covered by a more specific template:

```java
// CustomErrorAttributes.java
import org.springframework.boot.web.error.ErrorAttributeOptions;
import org.springframework.boot.web.servlet.error.DefaultErrorAttributes;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.WebRequest;

import java.util.Map;
import java.util.UUID;

@Component
public class CustomErrorAttributes extends DefaultErrorAttributes {

    @Override
    public Map<String, Object> getErrorAttributes(WebRequest webRequest, ErrorAttributeOptions options) {
        Map<String, Object> attributes = super.getErrorAttributes(webRequest, options);
        // Add a correlation id for support/debugging, remove the raw exception field
        // (present by default when options include STACK_TRACE) so it's never accidentally
        // rendered into an HTML page shown to end users.
        attributes.put("correlationId", UUID.randomUUID().toString());
        attributes.remove("exception");
        attributes.remove("trace");
        return attributes;
    }
}
```

```html
<!-- templates/error/5xx.html — status CLASS fallback: covers 500, 502, 503, etc. -->
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
<body>
  <h1>Something went wrong on our end</h1>
  <p>Reference: <span th:text="${correlationId}">abc-123</span></p>
  <p><a href="/">Return home</a></p>
</body>
</html>
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/-1
# <html>...<h1>Something went wrong on our end</h1>...Reference: 7c9e...ff2...</html>
```

**What changed:** `CustomErrorAttributes` extends Boot's `DefaultErrorAttributes`, adding a `correlationId` (for matching a user's report against server logs — see the `@ControllerAdvice` card's similar pattern) and explicitly stripping potentially sensitive fields (`exception`, `trace`) that could otherwise leak internal class names or stack details into a page shown to end users. `5xx.html` covers any `5xx`-class status without needing a dedicated `500.html`, `502.html`, `503.html`, etc.

### Level 3 — Advanced

Production pattern: dual HTML/JSON error handling from the same underlying error data — browsers get a styled page, API clients get structured `ProblemDetail`-shaped JSON — by overriding `BasicErrorController` behavior with a custom controller that branches on content negotiation, tying together concepts from the content-negotiation and `ProblemDetail` cards:

```java
// CustomErrorController.java
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.boot.web.error.ErrorAttributeOptions;
import org.springframework.boot.web.servlet.error.ErrorAttributes;
import org.springframework.boot.web.servlet.error.ErrorController;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ProblemDetail;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.context.request.ServletWebRequest;
import org.springframework.web.context.request.WebRequest;

import java.util.Map;

@Controller
public class CustomErrorController implements ErrorController {

    private final ErrorAttributes errorAttributes;
    public CustomErrorController(ErrorAttributes errorAttributes) { this.errorAttributes = errorAttributes; }

    @RequestMapping("/error")
    public Object handleError(HttpServletRequest request) {
        WebRequest webRequest = new ServletWebRequest(request);
        Map<String, Object> attrs = errorAttributes.getErrorAttributes(
            webRequest, ErrorAttributeOptions.of(ErrorAttributeOptions.Include.MESSAGE));

        int status = (int) attrs.getOrDefault("status", 500);
        String acceptHeader = request.getHeader("Accept");

        if (acceptHeader != null && acceptHeader.contains(MediaType.APPLICATION_JSON_VALUE)) {
            // API client: structured ProblemDetail JSON, consistent with the rest of the API's errors
            ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.valueOf(status), String.valueOf(attrs.get("message")));
            problem.setProperty("path", attrs.get("path"));
            return withJsonBody(problem, status);
        }

        // Browser client: render a status-specific or generic HTML template, as in earlier levels
        return "error/" + (status == 404 ? "404" : "error");
    }

    @ResponseBody
    private org.springframework.http.ResponseEntity<ProblemDetail> withJsonBody(ProblemDetail problem, int status) {
        return org.springframework.http.ResponseEntity.status(status).body(problem);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -H "Accept: text/html" http://localhost:8080/nonexistent
# <html>...<h1>Page not found</h1>...</html>

curl -H "Accept: application/json" http://localhost:8080/nonexistent
# {"status":404,"detail":"No message available","path":"/nonexistent"}
```

**What changed and why:**
- A single `/error` handler now branches explicitly on the `Accept` header — this centralizes error presentation logic that would otherwise be split confusingly between Boot's default `BasicErrorController` behavior (which does something similar internally, but less directly customizable) and any per-controller `@ExceptionHandler`s.
- The JSON branch reuses `ProblemDetail`, tying this generic, catch-all error handling into the *same* response shape used throughout the API by `@ExceptionHandler` methods (see the `ProblemDetail` and `ErrorResponse` cards) — an API client sees one consistent error contract whether the error came from a specific `@ExceptionHandler` or fell through to this generic catch-all.
- Implementing `ErrorController` and mapping `/error` explicitly is what tells Spring Boot's autoconfiguration to use *this* controller instead of its own `BasicErrorController` for the conventional error-forwarding path — the servlet container's error-page configuration (set up automatically by Boot) still forwards failed requests to `/error`; this class simply becomes the thing that handles that forwarded request.

## 6. Walkthrough

**Request: `GET /nonexistent` with `Accept: application/json` (Level 3 code, no matching route exists).**

1. `DispatcherServlet` finds no `HandlerMapping` willing to handle `/nonexistent` — no `@RequestMapping` matches, no static resource handler matches, nothing.
2. This results in a `404` status being set on the response by the servlet container's request-handling machinery. Because Spring Boot has configured the servlet container's error pages (via `ErrorPageRegistrar`, set up automatically) to forward any error status to `/error`, the container performs an internal **forward** (not a redirect — recall the redirect/forward card) to `/error`, carrying the original error details as request attributes.
3. `DispatcherServlet` now dispatches this forwarded `/error` request — this time, it *does* match a handler: `CustomErrorController.handleError(request)`, because it's explicitly mapped via `@RequestMapping("/error")` and implements `ErrorController` (the marker interface Boot's autoconfiguration recognizes to know this bean should take over Boot's default error handling instead of `BasicErrorController`).
4. Inside `handleError`: `errorAttributes.getErrorAttributes(webRequest, ...)` reads the error details the servlet container attached as request attributes during the forward (status `404`, the original request path `/nonexistent`, and a message) into a `Map`.
5. `status = 404` is extracted. The method checks the *original* request's `Accept` header — `"application/json"` — and because it contains `application/json`, the JSON branch executes.
6. A `ProblemDetail` is built: `status=404`, `detail` from the error message, plus a `path` extension property set from the original failed request's path.
7. `withJsonBody` wraps it in a `ResponseEntity` with the matching status code, and — because this private helper is annotated `@ResponseBody` — Spring serializes the `ProblemDetail` directly to the response body.
8. Response:
   ```
   HTTP/1.1 404 Not Found
   Content-Type: application/json

   {"status":404,"detail":"No message available","path":"/nonexistent"}
   ```

**Same failed request, but from a browser (`Accept: text/html`).**

1–4. Identical up through building the `attrs` map.
5. `status = 404` extracted. The `Accept` header check finds no `application/json`, so the JSON branch is skipped.
6. The method returns the *view name* `"error/404"` (since `status == 404`) — a `String`, treated as a view name because `CustomErrorController` is `@Controller` (not `@RestController`) and this particular method has no `@ResponseBody`.
7. View resolution locates `templates/error/404.html` (Thymeleaf's autoconfigured resolver), renders it — the template can reference `${status}`/`${path}`/etc. if added to the model, or simply present static, friendly copy as in the earlier levels.
8. Response:
   ```
   HTTP/1.1 404 Not Found
   Content-Type: text/html;charset=UTF-8

   <html>...<h1>Page not found</h1>...</html>
   ```

## 7. Gotchas & takeaways

> **Custom error page templates must live under the exact conventional path (`templates/error/`) and be named by status code or status class for Spring Boot's default `BasicErrorController` to find them automatically** — a typo in the directory name or filename means Boot silently falls back to its generic Whitelabel error page, with no error or warning indicating the custom template was never found.

> **Error attributes can include sensitive internal details (stack traces, exception class names) by default depending on `ErrorAttributeOptions` configuration** — always audit exactly what's exposed to end users versus what's logged server-side only, especially for any custom `ErrorAttributes` override, as demonstrated by explicitly stripping `exception`/`trace` fields in the Level 2 example.

> **Implementing a custom `ErrorController` (as in Level 3) completely replaces Boot's `BasicErrorController` for the `/error` path** — if your implementation doesn't handle every error scenario Boot's default did (certain edge cases around async errors, for instance), you can inadvertently regress behavior that "just worked" before the customization. Test thoroughly across the range of error scenarios the application can realistically produce.

- Spring Boot resolves error templates by convention: exact status code first (`404.html`), then status class (`5xx.html`), then a generic fallback (`error.html`).
- Override `ErrorAttributes`/`DefaultErrorAttributes` to control exactly what data is exposed in error responses, stripping sensitive internal details before they reach end users.
- For dual HTML/JSON error handling with a consistent `ProblemDetail`-shaped API contract, implement a custom `ErrorController` that branches on the request's `Accept` header.
- A custom `ErrorController` fully replaces Boot's default `BasicErrorController` — test it against the full range of error scenarios the application can produce, not just the one you were originally customizing for.
