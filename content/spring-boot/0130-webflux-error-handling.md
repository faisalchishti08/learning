---
card: spring-boot
gi: 130
slug: webflux-error-handling
title: WebFlux error handling
---

## 1. What it is

In Spring WebFlux, errors are signals in the reactive stream (`onError`), not exceptions thrown to a call stack. Spring Boot auto-configures three error-handling layers: `@ExceptionHandler` methods in `@ControllerAdvice` classes (same as Spring MVC), `WebExceptionHandler` beans for lower-level handling, and `DefaultErrorWebExceptionHandler` (the WebFlux equivalent of `BasicErrorController`) which routes unhandled errors to a `/error` endpoint returning JSON or HTML.

## 2. Why & when

Reactive streams decouple the error from the thread that caused it. You can't simply catch an exception from a `Mono` call — the error arrives asynchronously on the subscriber's thread. WebFlux provides reactive operators (`onErrorReturn`, `onErrorResume`) for inline error handling and the annotation-based `@ExceptionHandler` for cross-cutting concerns.

Use `@ExceptionHandler` in `@RestControllerAdvice` for application-level error mapping (same pattern as Spring MVC). Use `WebExceptionHandler` beans for infrastructure concerns (cross-origin, security, routing errors) that happen before the `DispatcherHandler`.

## 3. Core concept

Error handling layers, outermost to innermost:

1. **`WebExceptionHandler` beans** — intercept `ServerWebExchange` errors before Spring's routing. Lower `@Order` → runs first.
2. **`DefaultErrorWebExceptionHandler`** — auto-configured; handles anything that reaches `/error`.
3. **`@ExceptionHandler` in `@RestControllerAdvice`** — catches exceptions that escape a controller's reactive chain.
4. **Inline reactive operators** — `mono.onErrorReturn(fallback)`, `flux.onErrorResume(ex -> ...)` — per-stream fallbacks.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="110" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">onError signal</text>
  <rect x="220" y="55" width="155" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="297" y="79" text-anchor="middle" fill="#79c0ff" font-size="11" font-family="sans-serif">@RestControllerAdvice</text>
  <rect x="220" y="108" width="155" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="297" y="132" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">WebExceptionHandler</text>
  <rect x="220" y="161" width="155" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="297" y="178" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">DefaultError</text>
  <text x="297" y="194" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">WebExceptionHandler</text>
  <rect x="460" y="90" width="185" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="552" y="117" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Error JSON / HTML</text>
  <line x1="152" y1="105" x2="216" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#we)"/>
  <line x1="152" y1="105" x2="216" y2="128" stroke="#6db33f" stroke-width="1.5" marker-end="url(#we)"/>
  <line x1="152" y1="105" x2="216" y2="180" stroke="#6db33f" stroke-width="1.5" marker-end="url(#we)"/>
  <line x1="377" y1="115" x2="456" y2="115" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#we2)"/>
  <defs>
    <marker id="we" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="we2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

An `onError` signal travels through `@RestControllerAdvice`, custom `WebExceptionHandler` beans, and finally the default handler — outermost layer catches first.

## 5. Runnable example

```java
// WebFluxErrorApp.java  —  Spring Boot project with spring-boot-starter-webflux
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ServerWebInputException;
import reactor.core.publisher.Mono;

@SpringBootApplication
public class WebFluxErrorApp {
    public static void main(String[] args) {
        SpringApplication.run(WebFluxErrorApp.class, args);
    }
}

class NotFoundException extends RuntimeException {
    NotFoundException(String msg) { super(msg); }
}

@RestController
@RequestMapping("/items")
class ItemController {

    @GetMapping("/{id}")
    public Mono<String> getItem(@PathVariable int id) {
        if (id <= 0) {
            // Inline reactive error
            return Mono.error(new NotFoundException("Item " + id + " not found"));
        }
        // Inline fallback — never propagates to @ExceptionHandler
        return Mono.just("Item #" + id)
                   .onErrorReturn("fallback-item");
    }
}

// Global error handler — maps application exceptions to HTTP responses
@RestControllerAdvice
class GlobalErrorHandler {

    @ExceptionHandler(NotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public Mono<String> handleNotFound(NotFoundException ex) {
        return Mono.just("{\"error\":\"" + ex.getMessage() + "\"}");
    }

    @ExceptionHandler(ServerWebInputException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Mono<String> handleBadInput(ServerWebInputException ex) {
        return Mono.just("{\"error\":\"Bad input: " + ex.getReason() + "\"}");
    }
}
```

**How to run:** start the app, then:
- `curl http://localhost:8080/items/5` → `Item #5`
- `curl http://localhost:8080/items/-1` → `404` with `{"error":"Item -1 not found"}`
- `curl http://localhost:8080/items/abc` → `400` with bad-input message

## 6. Walkthrough

- `Mono.error(new NotFoundException(...))` creates a reactive stream that immediately emits an `onError` signal with the exception. The calling thread never blocks — error handling is asynchronous.
- `@RestControllerAdvice` + `@ExceptionHandler(NotFoundException.class)` catches the error from the reactive stream. The return type `Mono<String>` is supported — the advice returns a reactive response, not a plain object.
- `@ResponseStatus(HttpStatus.NOT_FOUND)` sets the HTTP status to 404. Alternatively return a `ResponseEntity` from the handler for fine-grained control.
- `onErrorReturn("fallback-item")` in `getItem` demonstrates inline recovery. If any upstream operator errors, the fallback value is emitted instead of propagating the error to `@ExceptionHandler`.
- `ServerWebInputException` is Spring WebFlux's equivalent of `MethodArgumentTypeMismatchException` — thrown when path variable type conversion fails (e.g. `"abc"` for `int id`).
- `DefaultErrorWebExceptionHandler` handles anything not caught here — auto-configured by Spring Boot to return JSON or HTML at `/error`.

## 7. Gotchas & takeaways

> Never throw exceptions *out of* a reactive chain by trying to `catch` them conventionally. Use `Mono.error(...)` to propagate errors inside the stream; let `@ExceptionHandler` or `onErrorResume` handle them.

> `@ExceptionHandler` in `@RestControllerAdvice` works in WebFlux, but the method must return a `Publisher` type (`Mono`/`Flux`) or a plain value — not `ResponseEntity` with non-reactive type parameters.

- `WebExceptionHandler` (vs. `@ExceptionHandler`) fires before `DispatcherHandler` — use it for errors from WebFlux filters or request parsing, not business logic.
- `onErrorResume(ex -> alternativeMono)` is the reactive equivalent of a `try/catch` block — it switches to an alternative stream on error.
- `onErrorReturn(defaultValue)` is a shorthand for `onErrorResume(_ -> Mono.just(defaultValue))`.
- In WebFlux, `ExceptionHandlerMethodResolver` maps exceptions to handlers inside `@ControllerAdvice` — same lookup strategy as Spring MVC.
