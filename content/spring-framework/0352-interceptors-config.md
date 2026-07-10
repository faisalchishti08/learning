---
card: spring-framework
gi: 352
slug: interceptors-config
title: "Interceptors config"
---

## 1. What it is

A `HandlerInterceptor` is a Spring MVC component that runs cross-cutting logic around handler method execution — before the handler runs, after it completes but before the view renders, and after the view has fully rendered. You register interceptors, and scope them to specific URL patterns, via `WebMvcConfigurer.addInterceptors(InterceptorRegistry registry)`.

```java
@Override
public void addInterceptors(InterceptorRegistry registry) {
    registry.addInterceptor(new AuthInterceptor()).addPathPatterns("/api/**").excludePathPatterns("/api/public/**");
}
```

## 2. Why & when

Interceptors sit at a layer between raw servlet `Filter`s (which run for *every* request, before Spring MVC even identifies a handler) and `@ExceptionHandler`/`@ControllerAdvice` (which run only around exceptions). Use a `HandlerInterceptor` when you need logic that:

- Should run for a specific subset of MVC-mapped routes (not literally every request, which is what a `Filter` handles), and needs access to the *resolved handler* (which controller method is about to execute) — useful for annotation-driven checks like "does this handler have a `@RequireRole` annotation?"
- Needs to run both before AND after the handler (timing/logging around the actual controller execution), or specifically after the view has rendered (cleanup, response header finalization).
- Is genuinely MVC-specific — filters are servlet-container-level and don't know about Spring MVC's handler mapping at all, so they can't easily answer "which controller method is this request going to?"

For simple authentication/authorization that must run before Spring MVC dispatch at all (and before static resources, actuator endpoints, etc.), a `Filter` (or Spring Security) is usually more appropriate — interceptors are for logic specifically tied to MVC's request-handling lifecycle.

## 3. Core concept

```
HandlerInterceptor lifecycle (three methods, all optional to override):

  preHandle(request, response, handler)  -> boolean
      runs BEFORE the handler method executes
      return false to SHORT-CIRCUIT — handler never runs,
        interceptor itself must write the response

  postHandle(request, response, handler, modelAndView)
      runs AFTER the handler executes, BEFORE the view renders
      can still modify the model/view at this point
      SKIPPED if preHandle returned false, or an exception was thrown

  afterCompletion(request, response, handler, ex)
      runs AFTER the view has fully rendered (or an exception occurred)
      good for cleanup, timing, logging — always runs if preHandle
        returned true, REGARDLESS of exceptions

Multiple interceptors chain in REGISTRATION order for preHandle,
REVERSE order for postHandle/afterCompletion — like nested brackets:

  preHandle A -> preHandle B -> [HANDLER RUNS] -> postHandle B -> postHandle A
                                                 -> afterCompletion B -> afterCompletion A
```

## 4. Diagram

<svg viewBox="0 0 740 240" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="240" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">Interceptor chain: nested around the handler, like brackets</text>

  <rect x="20" y="50" width="700" height="160" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="370" y="72" text-anchor="middle" fill="#8b949e" font-size="10">Interceptor A</text>

  <rect x="60" y="90" width="620" height="100" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="370" y="110" text-anchor="middle" fill="#79c0ff" font-size="10">Interceptor B</text>

  <rect x="260" y="125" width="220" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="150" text-anchor="middle" fill="#6db33f" font-size="10">Handler method runs</text>

  <text x="90" y="180" fill="#79c0ff" font-size="9">preHandle B -></text>
  <text x="480" y="180" fill="#79c0ff" font-size="9">-&gt; postHandle B</text>
  <text x="30" y="200" fill="#8b949e" font-size="9">preHandle A -></text>
  <text x="620" y="200" fill="#8b949e" font-size="9">-&gt; postHandle A</text>

  <defs>
    <marker id="a28" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Registration order determines `preHandle` order; `postHandle`/`afterCompletion` unwind in reverse, like nested brackets.*

## 5. Runnable example

### Level 1 — Basic

A simple logging interceptor scoped to one path pattern:

```java
// LoggingInterceptor.java
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.servlet.HandlerInterceptor;

public class LoggingInterceptor implements HandlerInterceptor {
    private static final Logger log = LoggerFactory.getLogger(LoggingInterceptor.class);

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        log.info("--> {} {}", request.getMethod(), request.getRequestURI());
        return true;   // continue processing
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        log.info("<-- {} {} status={}", request.getMethod(), request.getRequestURI(), response.getStatus());
    }
}
```

```java
// WebConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new LoggingInterceptor()).addPathPatterns("/api/**");
    }
}
```

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {
    @GetMapping("/api/products/{id}")
    public String get(@PathVariable long id) { return "Drill"; }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/api/products/1
# server log:
# --> GET /api/products/1
# <-- GET /api/products/1 status=200
```

`preHandle` logs before the handler runs; `afterCompletion` logs after the response is fully complete, including the final status code — useful for timing/audit logging that must observe the true final outcome.

### Level 2 — Intermediate

Two chained interceptors — a timing interceptor and an authentication check that short-circuits with `preHandle` returning `false` — demonstrating ordering and early termination:

```java
// TimingInterceptor.java
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.servlet.HandlerInterceptor;

public class TimingInterceptor implements HandlerInterceptor {
    private static final Logger log = LoggerFactory.getLogger(TimingInterceptor.class);
    private static final String START_ATTR = "requestStartTime";

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        request.setAttribute(START_ATTR, System.currentTimeMillis());
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        long start = (long) request.getAttribute(START_ATTR);
        log.info("{} took {}ms", request.getRequestURI(), System.currentTimeMillis() - start);
    }
}
```

```java
// AuthInterceptor.java
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.servlet.HandlerInterceptor;

public class AuthInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        String token = request.getHeader("X-Auth-Token");
        if (token == null || !token.equals("secret-token")) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            response.getWriter().write("Unauthorized");
            return false;   // SHORT-CIRCUIT: handler method never runs
        }
        return true;
    }
}
```

```java
// WebConfig.java (extended)
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        // Order matters: Timing wraps EVERYTHING, including auth rejections,
        // so we see accurate timing even for requests that get rejected.
        registry.addInterceptor(new TimingInterceptor()).addPathPatterns("/api/**");
        registry.addInterceptor(new AuthInterceptor()).addPathPatterns("/api/**");
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/api/products/1
# HTTP/1.1 401
# Unauthorized
# server log: "GET /api/products/1 took 2ms"   <- TimingInterceptor STILL logs, even though auth rejected it

curl -i -H "X-Auth-Token: secret-token" http://localhost:8080/api/products/1
# HTTP/1.1 200
# Drill
```

**What changed:** `TimingInterceptor` is registered first, so its `preHandle` runs before `AuthInterceptor`'s. When `AuthInterceptor.preHandle` returns `false`, the handler method never runs, and `AuthInterceptor.postHandle`/`afterCompletion` are skipped (they only fire following a `true` `preHandle` from that *same* interceptor) — but `TimingInterceptor.afterCompletion` still fires, since its own `preHandle` returned `true`. This ordering is exactly why registering timing/logging concerns *before* gate-keeping concerns is deliberate: you want observability even for rejected requests.

### Level 3 — Advanced

Production pattern: an annotation-driven interceptor that inspects the resolved handler method for a custom annotation (`@RateLimited`), demonstrating the key capability filters lack — awareness of *which specific handler* is about to run, not just the raw request:

```java
// RateLimited.java
import java.lang.annotation.*;

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface RateLimited {
    int requestsPerMinute() default 60;
}
```

```java
// RateLimitInterceptor.java
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerInterceptor;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

@Component
public class RateLimitInterceptor implements HandlerInterceptor {

    private final Map<String, AtomicInteger> requestCounts = new ConcurrentHashMap<>();

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        // Only HandlerMethod instances (actual @Controller methods) carry annotation metadata —
        // static resource handlers or other handler TYPES would not, so we check the type first.
        if (!(handler instanceof HandlerMethod handlerMethod)) return true;

        RateLimited annotation = handlerMethod.getMethodAnnotation(RateLimited.class);
        if (annotation == null) return true;   // handler has no @RateLimited — no limit applies

        String key = request.getRemoteAddr() + ":" + request.getRequestURI();
        AtomicInteger count = requestCounts.computeIfAbsent(key, k -> new AtomicInteger(0));

        if (count.incrementAndGet() > annotation.requestsPerMinute()) {
            response.setStatus(429);
            response.setHeader("Retry-After", "60");
            response.getWriter().write("Rate limit exceeded");
            return false;
        }
        return true;
    }
}
```

```java
// ProductController.java (production version)
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    @RateLimited(requestsPerMinute = 3)
    @GetMapping("/api/products/{id}/expensive-report")
    public String expensiveReport(@PathVariable long id) {
        return "Generated report for product " + id;
    }

    @GetMapping("/api/products/{id}")     // NO @RateLimited — unaffected
    public String get(@PathVariable long id) {
        return "Drill";
    }
}
```

```java
// WebConfig.java (production version)
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    private final RateLimitInterceptor rateLimitInterceptor;
    public WebConfig(RateLimitInterceptor rateLimitInterceptor) { this.rateLimitInterceptor = rateLimitInterceptor; }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(rateLimitInterceptor).addPathPatterns("/api/**");
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

for i in 1 2 3 4; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/api/products/1/expensive-report; done
# 200
# 200
# 200
# 429                          <- 4th request within the same minute exceeds the limit of 3

curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/api/products/1
# 200                          <- unaffected, no @RateLimited on this handler
```

**What changed and why:**
- Casting `handler` to `HandlerMethod` and calling `getMethodAnnotation(RateLimited.class)` is exactly the capability a plain servlet `Filter` cannot replicate cleanly — a filter only sees the raw `HttpServletRequest`, with no idea which specific `@Controller` method (or its annotations) is about to handle it. `HandlerInterceptor` runs *after* Spring MVC has already resolved the target handler, giving it this richer context.
- The rate limit only applies to handlers explicitly annotated `@RateLimited` — `get()` has no such annotation, so `preHandle` returns `true` immediately for it without consulting the rate-limit counters at all.
- This in-memory `ConcurrentHashMap`-based counter resets only on application restart and doesn't expire old entries — a genuinely production-grade rate limiter would use a proper sliding-window algorithm backed by Redis or similar for both correctness under multiple instances and automatic expiry, but the interceptor placement and annotation-inspection pattern shown here is exactly how such a system would hook into Spring MVC.

## 6. Walkthrough

**Request: 4th call within a minute to `GET /api/products/1/expensive-report` (Level 3 code).**

1. `DispatcherServlet` resolves the request to the handler method `ProductController.expensiveReport(1)`, wrapped internally as a `HandlerMethod` object carrying full reflective metadata (including method-level annotations).
2. Before invoking the handler, `DispatcherServlet` runs the registered interceptor chain's `preHandle` methods in order — here, just `RateLimitInterceptor.preHandle(request, response, handler)`.
3. Inside `preHandle`: `handler instanceof HandlerMethod` is `true` (this is a real controller method, not a static resource handler). `handlerMethod.getMethodAnnotation(RateLimited.class)` retrieves the `@RateLimited(requestsPerMinute = 3)` annotation instance directly from the method's reflective metadata.
4. `key = "127.0.0.1:/api/products/1/expensive-report"` (client IP + URI). `requestCounts.computeIfAbsent(key, ...)` retrieves the existing counter (already at `3` from the prior three successful requests) and `incrementAndGet()` brings it to `4`.
5. `4 > annotation.requestsPerMinute() (3)` is `true` → the rate limit is exceeded. `response.setStatus(429)`, `Retry-After: 60` header set, response body written directly: `"Rate limit exceeded"`.
6. `preHandle` returns `false` — this signals `DispatcherServlet` to **stop processing immediately**: `expensiveReport(1)` is never invoked, no `postHandle` runs (since this interceptor's own `preHandle` returned `false`), and the response already written by the interceptor becomes the final response.
7. Response sent to the client:
   ```
   HTTP/1.1 429
   Retry-After: 60

   Rate limit exceeded
   ```

**Contrast — a concurrent request to `GET /api/products/1` (no `@RateLimited`) at the same moment:**

1. `DispatcherServlet` resolves to `ProductController.get(1)`, again wrapped as a `HandlerMethod`.
2. `RateLimitInterceptor.preHandle` runs: `getMethodAnnotation(RateLimited.class)` returns `null` for this method (it was never annotated).
3. `preHandle` returns `true` immediately at the `if (annotation == null) return true;` line — the rate-limiting logic below is never reached for this handler.
4. `get(1)` executes normally, returning `"Drill"`.
5. Response: `200 OK`, body `"Drill"` — entirely unaffected by the other endpoint's rate limiting, because the interceptor's logic is scoped per-handler via the annotation check, not per-path-pattern alone.

## 7. Gotchas & takeaways

> **`preHandle` returning `false` means YOUR interceptor is fully responsible for writing a complete response** — forgetting to write a status code and body (as `AuthInterceptor`/`RateLimitInterceptor` do explicitly) leaves the client with an empty, unexplained response, since the handler that would normally produce one never runs.

> **`postHandle` does not run if an exception is thrown by the handler** (or by an earlier interceptor's `preHandle`) — only `afterCompletion` is guaranteed to run for any interceptor whose own `preHandle` returned `true`, making it the right place for cleanup logic that must always execute, exception or not.

> **Interceptors registered with overlapping `addPathPatterns` execute in REGISTRATION order for `preHandle`, but REVERSE order for `postHandle`/`afterCompletion`** — like nested brackets. Getting this backwards when reasoning about interaction between two interceptors (e.g. assuming a later-registered interceptor's cleanup runs after an earlier one's) is a common source of subtle bugs.

- `HandlerInterceptor` provides `preHandle`/`postHandle`/`afterCompletion` hooks scoped to specific MVC-mapped path patterns, with access to the *resolved handler* — richer than a plain servlet `Filter`.
- `preHandle` returning `false` short-circuits the request; the interceptor itself must write the complete response.
- `afterCompletion` always runs (for interceptors whose `preHandle` returned `true`), regardless of exceptions — the right place for guaranteed cleanup/logging.
- Casting `handler` to `HandlerMethod` unlocks annotation-driven, per-handler-method logic (rate limiting, custom authorization checks) that a filter cannot express as cleanly.
