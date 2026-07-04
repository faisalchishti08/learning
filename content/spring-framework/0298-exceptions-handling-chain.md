---
card: spring-framework
gi: 298
slug: exceptions-handling-chain
title: "Exceptions handling chain"
---

## 1. What it is

Spring MVC's **exception handling chain** is an ordered sequence of `HandlerExceptionResolver` implementations that `DispatcherServlet` consults when a handler method (or interceptor) throws an exception.  Each resolver inspects the exception and either:

- **Handles it** — writes the response and returns a `ModelAndView` (possibly empty), ending the chain; or
- **Passes** — returns `null`, letting the next resolver try.

If no resolver handles the exception, it propagates to the servlet container (e.g. Tomcat), which renders its own error page.

Default resolver order (highest to lowest priority):

| Priority | Resolver | What it handles |
|---|---|---|
| 1 | `ExceptionHandlerExceptionResolver` | `@ExceptionHandler` methods in `@Controller` / `@ControllerAdvice` |
| 2 | `ResponseStatusExceptionResolver` | `@ResponseStatus` on the exception class |
| 3 | `DefaultHandlerExceptionResolver` | Standard Spring MVC exceptions (e.g. `MethodArgumentNotValidException`, `HttpMessageNotReadableException`) |

---

## 2. Why & when

Without a handling chain every uncaught exception exposes a raw stack trace or a generic 500 page.  The chain lets you:

- Map **application exceptions** to specific HTTP status codes and JSON bodies without polluting controllers.
- Write **one `@ControllerAdvice`** class to handle exceptions from every controller.
- Add **custom `HandlerExceptionResolver`** implementations when `@ExceptionHandler` is not flexible enough (e.g. logging + metrics on every unhandled exception).

---

## 3. Core concept

```
Exception thrown in handler or interceptor
   ↓
DispatcherServlet.processHandlerException()
   ↓
for each resolver in order:
   resolver.resolveException(req, res, handler, ex)
     ↓ null  → try next
     ↓ ModelAndView (non-null, even if empty) → stop chain, render/write

If all return null → rethrow to container
```

`@ExceptionHandler` methods are discovered by `ExceptionHandlerExceptionResolver` at startup — it builds a method-to-exception-type map for each controller and for each `@ControllerAdvice` class.  At runtime it selects the most specific exception-type match (e.g. `IOException` preferred over `Exception` for an `IOException`).

---

## 4. Diagram

<svg viewBox="0 0 760 330" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="760" height="330" fill="#0d1117"/>

  <!-- Exception source -->
  <rect x="20" y="20" width="140" height="40" rx="5" fill="#1c2430" stroke="#e74c3c" stroke-width="1.5"/>
  <text x="90" y="40" text-anchor="middle" fill="#e74c3c">Exception thrown</text>
  <text x="90" y="54" text-anchor="middle" fill="#8b949e" font-size="10">in handler / interceptor</text>

  <!-- DispatcherServlet -->
  <line x1="90" y1="60" x2="90" y2="90" stroke="#8b949e" marker-end="url(#ae)"/>
  <rect x="20" y="90" width="140" height="36" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="113" text-anchor="middle" fill="#79c0ff">DispatcherServlet</text>

  <!-- Resolver 1 -->
  <line x1="160" y1="108" x2="220" y2="108" stroke="#8b949e" marker-end="url(#ae)"/>
  <rect x="220" y="90" width="180" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="108" text-anchor="middle" fill="#6db33f">ExceptionHandler</text>
  <text x="310" y="120" text-anchor="middle" fill="#8b949e" font-size="10">ExceptionResolver (1st)</text>

  <!-- null path -->
  <line x1="400" y1="108" x2="450" y2="108" stroke="#8b949e" stroke-dasharray="4,3" marker-end="url(#ae)"/>
  <text x="425" y="102" text-anchor="middle" fill="#8b949e" font-size="10">null</text>

  <!-- Resolver 2 -->
  <rect x="450" y="90" width="180" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="108" text-anchor="middle" fill="#6db33f">ResponseStatus</text>
  <text x="540" y="120" text-anchor="middle" fill="#8b949e" font-size="10">ExceptionResolver (2nd)</text>

  <!-- null path 2 -->
  <line x1="630" y1="108" x2="680" y2="108" stroke="#8b949e" stroke-dasharray="4,3" marker-end="url(#ae)"/>
  <text x="655" y="102" text-anchor="middle" fill="#8b949e" font-size="10">null</text>

  <!-- Resolver 3 -->
  <rect x="680" y="90" width="70" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="715" y="108" text-anchor="middle" fill="#6db33f" font-size="11">Default</text>
  <text x="715" y="120" text-anchor="middle" fill="#8b949e" font-size="9">Resolver (3rd)</text>

  <!-- handled path from resolver 1 -->
  <line x1="310" y1="126" x2="310" y2="200" stroke="#6db33f" stroke-dasharray="3,2" marker-end="url(#ae)"/>
  <rect x="220" y="200" width="180" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="218" text-anchor="middle" fill="#6db33f">ModelAndView returned</text>
  <text x="310" y="232" text-anchor="middle" fill="#8b949e" font-size="10">(non-null → stop chain)</text>

  <!-- response -->
  <line x1="310" y1="236" x2="310" y2="280" stroke="#8b949e" marker-end="url(#ae)"/>
  <rect x="220" y="280" width="180" height="36" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="310" y="301" text-anchor="middle" fill="#79c0ff">HTTP Response</text>
  <text x="310" y="314" text-anchor="middle" fill="#8b949e" font-size="10">e.g. 404 JSON body</text>

  <!-- caption -->
  <text x="380" y="330" text-anchor="middle" fill="#8b949e" font-size="10">Chain stops at first non-null ModelAndView; otherwise container renders 500</text>

  <defs>
    <marker id="ae" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Exception resolvers are tried in priority order; the first non-null `ModelAndView` wins.*

---

## 5. Runnable example

### Level 1 — Basic

A controller that throws a custom exception and a `@ControllerAdvice` that maps it to a 404 JSON body:

```java
// UserNotFoundException.java
public class UserNotFoundException extends RuntimeException {
    public UserNotFoundException(long id) {
        super("User " + id + " not found");
    }
}
```

```java
// UserController.java
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {
    @GetMapping("/{id}")
    public String getUser(@PathVariable long id) {
        if (id > 0) throw new UserNotFoundException(id); // simulate missing user
        return "{\"id\":" + id + "}";
    }
}
```

```java
// GlobalExceptionHandler.java
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(UserNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleNotFound(UserNotFoundException ex) {
        return new ErrorResponse("NOT_FOUND", ex.getMessage());
    }

    record ErrorResponse(String code, String message) {}
}
```

**How to run:**
```bash
./mvnw spring-boot:run
curl -i http://localhost:8080/api/users/99
# HTTP/1.1 404
# Content-Type: application/json
# {"code":"NOT_FOUND","message":"User 99 not found"}
```

`ExceptionHandlerExceptionResolver` discovers `handleNotFound` at startup.  When `UserController.getUser` throws `UserNotFoundException`, the resolver invokes `handleNotFound`, serialises the `ErrorResponse` to JSON, sets status 404, and returns a non-null (empty) `ModelAndView` — chain stops.

---

### Level 2 — Intermediate

Same scenario — exception handling — but now adding **validation errors** and a **fallback** for unexpected exceptions:

```java
// CreateUserRequest.java
import jakarta.validation.constraints.*;

public record CreateUserRequest(
    @NotBlank String name,
    @Email   String email,
    @Min(0) @Max(150) int age
) {}
```

```java
// UserController.java (extended)
@PostMapping
public ResponseEntity<String> createUser(@RequestBody @Valid CreateUserRequest req) {
    return ResponseEntity.status(201).body("{\"created\":true}");
}
```

```java
// GlobalExceptionHandler.java (extended)
import org.springframework.web.bind.MethodArgumentNotValidException;
import java.util.*;
import java.util.stream.*;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(UserNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleNotFound(UserNotFoundException ex) {
        return new ErrorResponse("NOT_FOUND", ex.getMessage(), null);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorResponse handleValidation(MethodArgumentNotValidException ex) {
        List<String> errors = ex.getBindingResult().getFieldErrors().stream()
                .map(fe -> fe.getField() + ": " + fe.getDefaultMessage())
                .collect(Collectors.toList());
        return new ErrorResponse("VALIDATION_FAILED", "Request invalid", errors);
    }

    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ErrorResponse handleAll(Exception ex) {
        // Log here in real code; never return stack traces to clients
        return new ErrorResponse("INTERNAL_ERROR", "Unexpected error", null);
    }

    record ErrorResponse(String code, String message, List<String> details) {}
}
```

**How to run:**
```bash
curl -i -X POST http://localhost:8080/api/users \
     -H "Content-Type: application/json" \
     -d '{"name":"","email":"bad","age":200}'
# HTTP/1.1 400
# {"code":"VALIDATION_FAILED","message":"Request invalid",
#  "details":["age: must be less than or equal to 150",
#             "email: must be a well-formed email address",
#             "name: must not be blank"]}
```

**What changed:** `MethodArgumentNotValidException` is thrown by Spring's `@Valid` integration inside `HandlerAdapter` before the controller body runs.  `ExceptionHandlerExceptionResolver` picks it up and calls `handleValidation`.  The fallback `Exception.class` handler catches anything unexpected — **most specific match wins**, so this only fires when no other handler matches.

---

### Level 3 — Advanced

Production scenario: a **custom `HandlerExceptionResolver`** that records metrics + enriches the error response with a trace ID, sitting alongside the standard chain:

```java
// MetricsExceptionResolver.java
import io.micrometer.core.instrument.MeterRegistry;
import jakarta.servlet.http.*;
import org.springframework.core.Ordered;
import org.springframework.web.servlet.*;
import org.springframework.http.HttpStatus;

public class MetricsExceptionResolver implements HandlerExceptionResolver, Ordered {

    private final MeterRegistry registry;

    public MetricsExceptionResolver(MeterRegistry registry) {
        this.registry = registry;
    }

    @Override
    public int getOrder() {
        return Ordered.HIGHEST_PRECEDENCE; // runs BEFORE ExceptionHandlerExceptionResolver
    }

    @Override
    public ModelAndView resolveException(HttpServletRequest req, HttpServletResponse res,
                                         Object handler, Exception ex) {
        // Record counter — every exception type gets its own metric tag
        registry.counter("mvc.exception",
                "type", ex.getClass().getSimpleName(),
                "uri",  req.getRequestURI()).increment();
        // Attach trace ID so the real handler can include it in the response
        req.setAttribute("traceId", java.util.UUID.randomUUID().toString().substring(0, 8));
        return null; // DO NOT handle — let ExceptionHandlerExceptionResolver do the real work
    }
}
```

```java
// GlobalExceptionHandler.java (trace-aware)
@ExceptionHandler(UserNotFoundException.class)
@ResponseStatus(HttpStatus.NOT_FOUND)
public ErrorResponse handleNotFound(UserNotFoundException ex, HttpServletRequest req) {
    String traceId = (String) req.getAttribute("traceId");
    return new ErrorResponse("NOT_FOUND", ex.getMessage(), null, traceId);
}

record ErrorResponse(String code, String message, List<String> details, String traceId) {}
```

```java
// MvcConfig.java
@Configuration
public class MvcConfig implements WebMvcConfigurer {
    @Bean
    public MetricsExceptionResolver metricsExceptionResolver(MeterRegistry registry) {
        return new MetricsExceptionResolver(registry);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run
curl -i http://localhost:8080/api/users/99
# HTTP/1.1 404
# {"code":"NOT_FOUND","message":"User 99 not found","details":null,"traceId":"a3f9b21c"}

# Prometheus endpoint:
curl http://localhost:8080/actuator/prometheus | grep mvc_exception
# mvc_exception_total{type="UserNotFoundException",uri="/api/users/99"} 1.0
```

**What changed and why:** `MetricsExceptionResolver` runs at `HIGHEST_PRECEDENCE` — before everything else.  It records the metric and stamps the `traceId` onto the request, but returns `null` so `ExceptionHandlerExceptionResolver` still does the actual handling.  This is the correct pattern for cross-cutting concerns that should not change the response themselves.

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="210" fill="#0d1117"/>
  <!-- chain -->
  <rect x="10" y="80" width="140" height="40" rx="4" fill="#1c2430" stroke="#e74c3c" stroke-width="1.5"/>
  <text x="80" y="100" text-anchor="middle" fill="#e74c3c">MetricsResolver</text>
  <text x="80" y="113" text-anchor="middle" fill="#8b949e" font-size="10">records metric, returns null</text>

  <line x1="150" y1="100" x2="185" y2="100" stroke="#8b949e" marker-end="url(#am)"/>
  <text x="167" y="95" text-anchor="middle" fill="#8b949e" font-size="10">null</text>

  <rect x="185" y="80" width="155" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="262" y="98" text-anchor="middle" fill="#6db33f">ExceptionHandler</text>
  <text x="262" y="112" text-anchor="middle" fill="#8b949e" font-size="10">ExceptionResolver</text>

  <line x1="340" y1="100" x2="375" y2="100" stroke="#6db33f" marker-end="url(#am)"/>
  <text x="357" y="95" text-anchor="middle" fill="#6db33f" font-size="10">MaV</text>

  <rect x="375" y="80" width="130" height="40" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="440" y="100" text-anchor="middle" fill="#79c0ff">JSON Response</text>
  <text x="440" y="112" text-anchor="middle" fill="#8b949e" font-size="10">404 + traceId</text>

  <!-- side effect -->
  <line x1="80" y1="80" x2="80" y2="45" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#am)"/>
  <rect x="10" y="20" width="140" height="24" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="80" y="36" text-anchor="middle" fill="#8b949e">Micrometer counter++</text>

  <text x="350" y="185" text-anchor="middle" fill="#8b949e" font-size="10">Metrics resolver runs first (HIGHEST_PRECEDENCE) but defers to ExceptionHandlerResolver for the actual response</text>
  <defs><marker id="am" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Startup:**

1. Spring Boot auto-configures `ExceptionHandlerExceptionResolver`, `ResponseStatusExceptionResolver`, `DefaultHandlerExceptionResolver` in that order.
2. `ExceptionHandlerExceptionResolver` scans all `@ControllerAdvice` beans and builds an exception-type → method map (e.g. `UserNotFoundException → handleNotFound`).
3. `MetricsExceptionResolver` bean is picked up, and its `getOrder()` = `HIGHEST_PRECEDENCE` (Integer.MIN_VALUE) places it before all three defaults.

**Per-request exception flow:**

4. `GET /api/users/99` arrives → `UserController.getUser(99)` throws `UserNotFoundException("User 99 not found")`.
5. `DispatcherServlet.processHandlerException()` iterates resolvers:
   - **MetricsExceptionResolver.resolveException** — increments Micrometer counter `mvc.exception{type=UserNotFoundException, uri=/api/users/99}`, stamps `traceId="a3f9b21c"` on request object. Returns `null` → continue.
   - **ExceptionHandlerExceptionResolver.resolveException** — looks up exception type `UserNotFoundException` in its map, finds `handleNotFound`. Calls `handleNotFound(ex, req)`. Method returns `ErrorResponse{code=NOT_FOUND, message=User 99 not found, traceId=a3f9b21c}`. Serialises to JSON using `HttpMessageConverter`. Sets status `404`. Returns a non-null (empty) `ModelAndView` → chain stops.
6. Response committed: `HTTP/1.1 404` with JSON body.

**Request / Response state at each layer:**

| Step | State |
|---|---|
| Exception thrown | exception object on call stack |
| MetricsResolver | traceId on request attrs; counter incremented |
| ExceptionHandlerResolver | traceId read from request; JSON body produced |
| Response | 404 + `{"traceId":"a3f9b21c",...}` |

---

## 7. Gotchas & takeaways

> **`@ExceptionHandler` in a `@Controller` only catches exceptions from that controller.**  Put it in `@ControllerAdvice` (or `@RestControllerAdvice`) to handle exceptions from all controllers.  If both exist, the controller-local handler wins for that controller's exceptions.

> **Exception type specificity matters.**  If you have handlers for both `IOException` and `Exception`, and a controller throws `IOException`, Spring selects `IOException` — the most specific match.  A bare `Exception` handler acts as the catch-all; without one, unmatched exceptions propagate to the container.

> **`ResponseStatusExceptionResolver` only reads `@ResponseStatus` from the exception class, not from the handler method.**  Annotate the exception class itself, or throw `ResponseStatusException` (a Spring class) from the controller for ad-hoc status codes.

- Default resolver priority: `ExceptionHandlerExceptionResolver` (1) → `ResponseStatusExceptionResolver` (2) → `DefaultHandlerExceptionResolver` (3).
- Custom `HandlerExceptionResolver` with `return null` enriches the request without taking over the response — the right pattern for cross-cutting concerns.
- `@RestControllerAdvice` = `@ControllerAdvice` + `@ResponseBody` — use it when all your handlers return JSON.
- Never return stack traces to clients — log them, return a trace ID.
- `MethodArgumentNotValidException` is thrown by the framework before the controller body runs; it is handled by the same chain.
