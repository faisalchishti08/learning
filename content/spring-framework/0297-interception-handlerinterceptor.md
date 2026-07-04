---
card: spring-framework
gi: 297
slug: interception-handlerinterceptor
title: "Interception (HandlerInterceptor)"
---

## 1. What it is

A **`HandlerInterceptor`** is a hook that runs around every request handled by `DispatcherServlet`.  Think of it as servlet middleware — code that executes before the controller, after the controller (but before the view renders), and after the entire response is committed.

Interface:

```java
public interface HandlerInterceptor {
    // runs BEFORE the handler method; return false to abort
    default boolean preHandle(HttpServletRequest req, HttpServletResponse res, Object handler) throws Exception { return true; }

    // runs AFTER the handler, BEFORE view rendering; only called when preHandle returned true
    default void postHandle(HttpServletRequest req, HttpServletResponse res, Object handler, ModelAndView mav) throws Exception {}

    // always runs after the full response (even on exception); only when preHandle returned true
    default void afterCompletion(HttpServletRequest req, HttpServletResponse res, Object handler, Exception ex) throws Exception {}
}
```

`preHandle` returning `false` short-circuits the entire chain — no controller, no `postHandle`, no view.

---

## 2. Why & when

Use `HandlerInterceptor` when logic must run **for every (or many) requests** and must not be part of the controller itself:

- Authentication / authorization checks before the handler executes
- Request/response logging with timing
- Injecting common model attributes (e.g. current user) before view rendering
- Cleaning up thread-local state in `afterCompletion`

Prefer `HandlerInterceptor` over `javax.servlet.Filter` when you need access to the **resolved handler** (i.e. the controller method) or want to add model attributes after the handler runs.

---

## 3. Core concept

```
Interceptor chain (ordered list):
  [ I1, I2, I3 ]

preHandle  phase: I1.pre → I2.pre → I3.pre → controller
postHandle phase:                   I3.post → I2.post → I1.post
afterCompletion:                    I3.after → I2.after → I1.after

If I2.preHandle returns false:
  preHandle  phase: I1.pre → I2.pre (stops)
  postHandle phase: (skipped)
  afterCompletion:  I1.after  ← only interceptors whose preHandle returned true
```

The reversal in `postHandle` / `afterCompletion` mirrors how servlet filters wrap their `chain.doFilter()` call — inner interceptors run first in post-processing.

---

## 4. Diagram

<svg viewBox="0 0 760 310" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="760" height="310" fill="#0d1117"/>

  <!-- timeline arrow -->
  <line x1="30" y1="155" x2="730" y2="155" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="370" y="175" text-anchor="middle" fill="#8b949e" font-size="10">time →</text>

  <!-- boxes -->
  <!-- pre handles -->
  <rect x="40" y="100" width="95" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="87" y="122" text-anchor="middle" fill="#6db33f">I1.preHandle</text>

  <rect x="150" y="100" width="95" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="197" y="122" text-anchor="middle" fill="#6db33f">I2.preHandle</text>

  <!-- controller -->
  <rect x="270" y="88" width="110" height="58" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="325" y="110" text-anchor="middle" fill="#79c0ff" font-weight="bold">Controller</text>
  <text x="325" y="128" text-anchor="middle" fill="#8b949e" font-size="10">@GetMapping method</text>
  <text x="325" y="142" text-anchor="middle" fill="#8b949e" font-size="10">returns ModelAndView</text>

  <!-- post handles -->
  <rect x="400" y="100" width="95" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="447" y="122" text-anchor="middle" fill="#6db33f">I2.postHandle</text>

  <rect x="510" y="100" width="95" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="557" y="122" text-anchor="middle" fill="#6db33f">I1.postHandle</text>

  <!-- view -->
  <rect x="620" y="100" width="110" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="675" y="122" text-anchor="middle" fill="#e6edf3">View.render()</text>

  <!-- after completion row -->
  <rect x="40" y="208" width="95" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="87" y="224" text-anchor="middle" fill="#8b949e">I1.after</text>
  <text x="87" y="238" text-anchor="middle" fill="#8b949e" font-size="10">Completion</text>

  <rect x="150" y="208" width="95" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="197" y="224" text-anchor="middle" fill="#8b949e">I2.after</text>
  <text x="197" y="238" text-anchor="middle" fill="#8b949e" font-size="10">Completion</text>

  <!-- arrows pre -->
  <line x1="135" y1="118" x2="148" y2="118" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ga)"/>
  <line x1="245" y1="118" x2="268" y2="118" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ga)"/>
  <line x1="380" y1="118" x2="398" y2="118" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ga)"/>
  <line x1="495" y1="118" x2="508" y2="118" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ga)"/>
  <line x1="605" y1="118" x2="618" y2="118" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ga)"/>

  <!-- after completion arrows (reversed) -->
  <line x1="248" y1="226" x2="210" y2="226" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ga2)"/>
  <line x1="148" y1="226" x2="138" y2="226" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ga2)"/>

  <!-- caption -->
  <text x="380" y="280" text-anchor="middle" fill="#8b949e" font-size="11">postHandle and afterCompletion run in REVERSE interceptor order</text>

  <defs>
    <marker id="ga" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
    <marker id="ga2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`preHandle` runs in registration order; `postHandle` and `afterCompletion` run in reverse order.*

---

## 5. Runnable example

### Level 1 — Basic

A single interceptor that logs the URL and total request duration:

```java
// LoggingInterceptor.java
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.ModelAndView;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

public class LoggingInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse res, Object handler) {
        req.setAttribute("startMs", System.currentTimeMillis());
        System.out.println("[PRE]  " + req.getMethod() + " " + req.getRequestURI());
        return true; // allow the request to continue
    }

    @Override
    public void afterCompletion(HttpServletRequest req, HttpServletResponse res, Object handler, Exception ex) {
        long elapsed = System.currentTimeMillis() - (long) req.getAttribute("startMs");
        System.out.printf("[DONE] %s %s → %d  (%dms)%n",
                req.getMethod(), req.getRequestURI(), res.getStatus(), elapsed);
    }
}
```

```java
// MvcConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.*;

@Configuration
public class MvcConfig implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new LoggingInterceptor());
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/api/users
# Console: [PRE] GET /api/users
#          [DONE] GET /api/users → 200  (12ms)
```

`preHandle` stamps a start time onto the request object (safe thread-local storage).  `afterCompletion` subtracts to compute elapsed time and logs with the final HTTP status.  Returning `true` from `preHandle` tells Spring to continue to the next interceptor (or controller).

---

### Level 2 — Intermediate

Same scenario — request interception — but now adding an **authorization check** in `preHandle` that rejects unauthenticated requests, plus injecting a common model attribute in `postHandle`:

```java
// AuthInterceptor.java
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.ModelAndView;
import jakarta.servlet.http.*;

public class AuthInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse res, Object handler) throws Exception {
        String token = req.getHeader("Authorization");
        if (token == null || !token.startsWith("Bearer ")) {
            res.sendError(HttpServletResponse.SC_UNAUTHORIZED, "Missing token");
            return false; // abort — controller never runs
        }
        // Store parsed principal for downstream use
        req.setAttribute("principal", token.substring(7));
        return true;
    }

    @Override
    public void postHandle(HttpServletRequest req, HttpServletResponse res,
                           Object handler, ModelAndView mav) {
        // Inject current user into every view model automatically
        if (mav != null) {
            mav.addObject("currentUser", req.getAttribute("principal"));
        }
    }
}
```

```java
// MvcConfig.java (updated)
@Override
public void addInterceptors(InterceptorRegistry registry) {
    registry.addInterceptor(new LoggingInterceptor());                  // order 0
    registry.addInterceptor(new AuthInterceptor())
            .addPathPatterns("/api/**")                                  // only secure paths
            .excludePathPatterns("/api/public/**");                      // except public endpoints
}
```

**How to run:**
```bash
curl -H "Authorization: Bearer alice-token" http://localhost:8080/api/users
# → 200 OK, view gets currentUser="alice-token"

curl http://localhost:8080/api/users
# → 401 Unauthorized: Missing token

curl http://localhost:8080/api/public/health
# → 200 (AuthInterceptor skipped for this path)
```

**What changed:** `addPathPatterns()` and `excludePathPatterns()` scope the interceptor to a URL subset — a critical production pattern that prevents the auth check from running on health endpoints.  `postHandle` injects `currentUser` into the view model without every controller needing to do it.

---

### Level 3 — Advanced

Production scenario: a chained interceptor stack with **rate-limiting**, correlation IDs, and cleanup — demonstrating chain abort behaviour and `afterCompletion` for resource teardown:

```java
// CorrelationInterceptor.java
import org.slf4j.MDC;
import org.springframework.web.servlet.HandlerInterceptor;
import jakarta.servlet.http.*;
import java.util.UUID;

public class CorrelationInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse res, Object handler) {
        String id = req.getHeader("X-Correlation-ID");
        if (id == null) id = UUID.randomUUID().toString();
        MDC.put("correlationId", id);          // available in all log lines this thread
        res.setHeader("X-Correlation-ID", id); // echo back to caller
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest req, HttpServletResponse res,
                                Object handler, Exception ex) {
        MDC.clear(); // MUST clean up or thread-pool reuse leaks IDs to the next request
    }
}
```

```java
// RateLimitInterceptor.java
import org.springframework.http.HttpStatus;
import org.springframework.web.servlet.HandlerInterceptor;
import jakarta.servlet.http.*;
import java.util.Map;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class RateLimitInterceptor implements HandlerInterceptor {
    // Simple in-memory token bucket per IP (replace with Redis in prod)
    private final Map<String, AtomicInteger> counters = new ConcurrentHashMap<>();

    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse res, Object handler) throws Exception {
        String ip = req.getRemoteAddr();
        int count = counters.computeIfAbsent(ip, k -> new AtomicInteger(0)).incrementAndGet();
        if (count > 100) {
            res.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
            res.setHeader("Retry-After", "60");
            res.getWriter().write("{\"error\":\"rate limit exceeded\"}");
            return false; // abort chain — no controller, no postHandle
        }
        return true;
    }
}
```

```java
// MvcConfig.java (final)
@Override
public void addInterceptors(InterceptorRegistry registry) {
    registry.addInterceptor(new CorrelationInterceptor());   // always runs; sets up MDC
    registry.addInterceptor(new RateLimitInterceptor())
            .addPathPatterns("/api/**");
    registry.addInterceptor(new AuthInterceptor())
            .addPathPatterns("/api/**")
            .excludePathPatterns("/api/public/**");
    registry.addInterceptor(new LoggingInterceptor());       // must be last to time everything
}
```

**How to run:**
```bash
./mvnw spring-boot:run
curl -H "Authorization: Bearer tok" http://localhost:8080/api/users
# Response header: X-Correlation-ID: <uuid>
# Console log line includes correlationId=<uuid> in MDC
```

**What changed and why:**
- `CorrelationInterceptor` sets an MDC key so every log line produced by this request thread includes `correlationId` automatically — zero controller changes needed.
- `afterCompletion` **must** call `MDC.clear()` because Tomcat / Jetty reuse threads; a missing clear leaks the previous request's ID into the next request's logs.
- `RateLimitInterceptor` short-circuits with `return false` — downstream interceptors (`AuthInterceptor`, `LoggingInterceptor`) never run, but `CorrelationInterceptor.afterCompletion` *does* run because its `preHandle` already returned `true`.
- Registration order matters: correlation ID must be first (it sets up logging context), rate-limit second (fast reject), auth third (reject before business logic), logging last (captures full timing including auth overhead).

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="230" fill="#0d1117"/>
  <!-- labels left -->
  <text x="10" y="55" fill="#8b949e">Correlation</text>
  <text x="10" y="105" fill="#8b949e">RateLimit</text>
  <text x="10" y="155" fill="#8b949e">Auth</text>
  <text x="10" y="205" fill="#8b949e">Logging</text>
  <!-- pre bars -->
  <rect x="90" y="40" width="60" height="24" rx="3" fill="#6db33f" opacity="0.8"/>
  <text x="120" y="56" text-anchor="middle" fill="#0d1117" font-size="10">pre</text>
  <rect x="90" y="90" width="60" height="24" rx="3" fill="#6db33f" opacity="0.8"/>
  <text x="120" y="106" text-anchor="middle" fill="#0d1117" font-size="10">pre</text>
  <rect x="90" y="140" width="60" height="24" rx="3" fill="#6db33f" opacity="0.8"/>
  <text x="120" y="156" text-anchor="middle" fill="#0d1117" font-size="10">pre</text>
  <rect x="90" y="190" width="60" height="24" rx="3" fill="#6db33f" opacity="0.8"/>
  <text x="120" y="206" text-anchor="middle" fill="#0d1117" font-size="10">pre</text>
  <!-- controller -->
  <rect x="270" y="60" width="90" height="100" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="315" y="115" text-anchor="middle" fill="#79c0ff">Controller</text>
  <!-- post bars -->
  <rect x="375" y="40" width="60" height="24" rx="3" fill="#6db33f" opacity="0.5"/>
  <text x="405" y="56" text-anchor="middle" fill="#0d1117" font-size="10">post</text>
  <rect x="375" y="190" width="60" height="24" rx="3" fill="#6db33f" opacity="0.5"/>
  <text x="405" y="206" text-anchor="middle" fill="#0d1117" font-size="10">post</text>
  <!-- after bars -->
  <rect x="460" y="40" width="60" height="24" rx="3" fill="#8b949e" opacity="0.5"/>
  <text x="490" y="56" text-anchor="middle" fill="#0d1117" font-size="10">after</text>
  <!-- rate-limit abort label -->
  <text x="156" y="103" fill="#e74c3c" font-size="11">→ 429 abort</text>
  <!-- flow arrows -->
  <line x1="150" y1="52" x2="268" y2="52" stroke="#8b949e" stroke-dasharray="3,2"/>
  <line x1="150" y1="102" x2="155" y2="102" stroke="#e74c3c"/>
  <line x1="365" y1="170" x2="375" y2="52" stroke="#8b949e" stroke-dasharray="3,2" transform="translate(0,0)"/>
  <text x="350" y="195" text-anchor="middle" fill="#8b949e" font-size="10">RateLimit abort stops Auth/Logging pre. Correlation.after still runs.</text>
</svg>

---

## 6. Walkthrough

**Startup (once):**

1. `WebMvcConfigurer.addInterceptors()` is called; Spring stores `[CorrelationInterceptor, RateLimitInterceptor, AuthInterceptor, LoggingInterceptor]` in an ordered `List<HandlerInterceptorAdapter>`.
2. `DispatcherServlet` wraps the resolved handler in a `HandlerExecutionChain` containing this list (filtered by path patterns).

**Per-request — normal flow:**

3. Request arrives: `GET /api/users` with `Authorization: Bearer tok`.
4. `DispatcherServlet.doDispatch()` calls `chain.applyPreHandle()`.
5. **Correlation.preHandle** — generates UUID, sets MDC `correlationId`, sets response header. Returns `true`.
6. **RateLimit.preHandle** — count < 100, returns `true`.
7. **Auth.preHandle** — header present, stores principal in request attribute, returns `true`.
8. **Logging.preHandle** — records `startMs`. Returns `true`.
9. `HandlerAdapter.handle()` — controller executes, produces JSON response body (or `ModelAndView`).
10. `chain.applyPostHandle()` — called in **reverse**: Logging.post (no-op) → Auth.post (injects `currentUser` into model if present) → Correlation.post (no-op).
11. View resolves and renders (if applicable).
12. `chain.triggerAfterCompletion()` — **reverse**: Logging.after (logs elapsed + status) → Auth.after (no-op) → RateLimit.after (no-op) → Correlation.after (**`MDC.clear()`**).

**State changes at each layer:**

| Layer | Request state | Response state |
|---|---|---|
| Correlation.pre | `correlationId` added to MDC + request attr | `X-Correlation-ID` header set |
| RateLimit.pre | counter incremented | (unchanged) |
| Auth.pre | `principal` added to request attrs | (unchanged) |
| Controller | DB query executed | body written |
| Auth.post | (reads `principal`) | `currentUser` in model |
| Logging.after | reads `startMs` | (unchanged) |
| Correlation.after | MDC **cleared** | (unchanged) |

**Abort path (rate limit exceeded):**

RateLimit.preHandle increments counter past 100 → writes `429` body directly to `res.getWriter()` → returns `false`.  Spring's `applyPreHandle()` immediately calls `triggerAfterCompletion()` for interceptors 0..current (only Correlation, index 0) — so `MDC.clear()` still runs.  Controllers, postHandle, view never execute.

---

## 7. Gotchas & takeaways

> **`afterCompletion` runs even when `preHandle` aborts the chain** — but only for interceptors whose `preHandle` already returned `true`.  This is intentional: anything you set up in `preHandle` must be tearable in `afterCompletion`.  Always design interceptors as matched setup/teardown pairs.

> **Do not write the response body in `postHandle`.**  At `postHandle` time the response may already be partially committed (for `@ResponseBody` methods) — writing more bytes causes `IllegalStateException`.  Only `preHandle` (before the handler) and `afterCompletion` (when the response is already fully committed) are safe for response manipulation at the byte level.

- `preHandle` returning `false` aborts the chain but does **not** prevent `afterCompletion` from running for already-executed interceptors.
- Registration order = `preHandle` order; reverse = `postHandle`/`afterCompletion` order.
- Use `addPathPatterns()` / `excludePathPatterns()` to scope interceptors rather than building conditional logic inside `preHandle`.
- `MDC.clear()` in `afterCompletion` is mandatory when using `MDC` — thread pools reuse threads across requests.
- Never store request-scoped state in interceptor instance fields — interceptors are singletons shared across all threads.
