---
card: spring-boot
gi: 115
slug: errorattributes-errorcontroller
title: ErrorAttributes & ErrorController
---

## 1. What it is

Spring Boot auto-configures a `/error` endpoint that catches every unhandled exception and produces a consistent error response (JSON for REST clients, an HTML page for browsers). Two interfaces drive this:

- **`ErrorAttributes`** — extracts the attributes that appear in the error response (timestamp, status, error, message, path, etc.).
- **`ErrorController`** — the controller that *handles* the `/error` route and turns those attributes into an HTTP response.

The default implementations are `DefaultErrorAttributes` and `BasicErrorController`. You replace or extend them to take full control of error output.

## 2. Why & when

Without a standard error-handling layer every exception bubbles up as a 500 with a stack trace — or worse, no body at all. Spring Boot's `/error` whitelist page ensures:

- REST clients always get a structured JSON body.
- Browsers get a human-readable "Whitelabel Error Page".
- Error details (status, message, path) are consistent across the app.

Extend `ErrorAttributes` when you want to **add or remove fields** from the error body (e.g., add a correlation ID). Implement `ErrorController` when you need completely custom routing logic for different error codes.

## 3. Core concept

Think of it as a funnel. Any exception that isn't caught by a `@ExceptionHandler` or `@ControllerAdvice` falls into Servlet error dispatch, which forwards to `/error`. `BasicErrorController` receives that forwarded request, calls `ErrorAttributes.getErrorAttributes()` to build a `Map`, then returns it as JSON or HTML depending on the `Accept` header.

Key flow:

1. Exception escapes your controller.
2. Servlet container forwards to `/error`.
3. `BasicErrorController.error()` runs.
4. It calls `DefaultErrorAttributes.getErrorAttributes()`.
5. Result returned as `ResponseEntity<Map>` (JSON) or `ModelAndView` (HTML).

Custom `ErrorAttributes` just replace step 4; custom `ErrorController` replaces steps 3–5.

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="90" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="119" text-anchor="middle" fill="#e6edf3" font-size="13" font-family="sans-serif">Your Controller</text>
  <rect x="220" y="90" width="140" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="290" y="112" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Servlet Error</text>
  <text x="290" y="128" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Dispatch → /error</text>
  <rect x="430" y="70" width="155" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="507" y="98" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">BasicErrorController</text>
  <rect x="430" y="140" width="155" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="507" y="168" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">DefaultErrorAttributes</text>
  <line x1="155" y1="115" x2="215" y2="115" stroke="#e6edf3" stroke-width="1.5" marker-end="url(#ea)"/>
  <text x="185" y="108" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">throws</text>
  <line x1="365" y1="115" x2="425" y2="100" stroke="#e6edf3" stroke-width="1.5" marker-end="url(#ea)"/>
  <line x1="507" y1="122" x2="507" y2="136" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ea)"/>
  <text x="520" y="133" fill="#8b949e" font-size="10" font-family="sans-serif">calls</text>
  <defs><marker id="ea" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#e6edf3"/></marker></defs>
</svg>

Exceptions travel right → into Servlet dispatch → `BasicErrorController` delegates attribute extraction to `DefaultErrorAttributes`.

## 5. Runnable example

```java
// ErrorDemoApp.java  —  run with: java ErrorDemoApp.java  (JDK 17+, needs spring-boot on classpath)
// Minimal demo: extend DefaultErrorAttributes to add a correlationId field.

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.error.ErrorAttributeOptions;
import org.springframework.boot.web.servlet.error.DefaultErrorAttributes;
import org.springframework.context.annotation.Bean;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.context.request.WebRequest;

import java.util.Map;
import java.util.UUID;

@SpringBootApplication
public class ErrorDemoApp {

    public static void main(String[] args) {
        SpringApplication.run(ErrorDemoApp.class, args);
    }

    // Replace DefaultErrorAttributes with our enriched version
    @Bean
    public DefaultErrorAttributes errorAttributes() {
        return new DefaultErrorAttributes() {
            @Override
            public Map<String, Object> getErrorAttributes(
                    WebRequest request, ErrorAttributeOptions options) {
                Map<String, Object> attrs = super.getErrorAttributes(request, options);
                // Add a correlation ID to every error response
                attrs.put("correlationId", UUID.randomUUID().toString());
                return attrs;
            }
        };
    }
}

@RestController
class DemoController {

    @GetMapping("/boom")
    public String boom() {
        throw new IllegalStateException("Something went wrong!");
    }
}
```

**How to run:** add to a Spring Boot project, start the app, then `curl http://localhost:8080/boom`. The JSON response will include a `correlationId` field alongside the standard `status`, `error`, `message`, and `path`.

## 6. Walkthrough

- `@SpringBootApplication` triggers auto-configuration, including `ErrorMvcAutoConfiguration`, which registers `BasicErrorController` and `DefaultErrorAttributes` as beans — but only if no user-provided beans of those types exist.
- The `@Bean defaultErrorAttributes()` method returns an anonymous subclass of `DefaultErrorAttributes`. Because Spring Boot uses `@ConditionalOnMissingBean`, our bean wins over the auto-configured one.
- Inside `getErrorAttributes()`, calling `super.getErrorAttributes(request, options)` fills in the standard fields (timestamp, status, error, message, path). We then put our `correlationId` into the same map.
- When `/boom` is hit, the `IllegalStateException` escapes the controller. The Servlet container forwards to `/error`. `BasicErrorController` asks our `DefaultErrorAttributes` for the map, gets back the enriched version, and serialises it as JSON.
- `ErrorAttributeOptions` controls which optional fields appear (e.g. stack trace, binding errors) — pass `ErrorAttributeOptions.of(Include.STACK_TRACE)` if you need them in dev.

## 7. Gotchas & takeaways

> Never expose the full stack trace in production. `DefaultErrorAttributes` omits it by default; adding `server.error.include-stacktrace=always` in `application.properties` enables it — fine locally, dangerous in prod.

> If you register a `@ControllerAdvice` with `@ExceptionHandler`, that handler fires *before* the `/error` route. Your custom `ErrorAttributes` only sees exceptions that *escape* all `@ExceptionHandler` methods.

- `BasicErrorController` returns JSON when the `Accept` header includes `application/json`; HTML otherwise.
- To fully replace the error page, implement `ErrorController` and map `@RequestMapping(${server.error.path:/error})`.
- `ErrorAttributeOptions.defaults()` skips stack trace and binding errors — always start from defaults and opt in.
- Custom `ErrorAttributes` apply globally; `@ExceptionHandler` is per-controller or per-advice — use both layers together.
