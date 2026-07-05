---
card: spring-framework
gi: 302
slug: logging-request-details
title: "Logging request details"
---

## 1. What it is

Spring MVC provides built-in mechanisms for logging HTTP request details:

- **`CommonsRequestLoggingFilter`** — a servlet filter that logs request URI, query string, headers, and body before and/or after each request.
- **`AbstractRequestLoggingFilter`** — the base class; extend it to write to any target.
- **`WebRequestInterceptor` / `HandlerInterceptor`** — hook into the MVC pipeline for structured request logging.
- **Log levels** — `DispatcherServlet` itself logs at `TRACE`/`DEBUG` level when the logger `org.springframework.web.servlet.DispatcherServlet` is enabled.

For production use, structured logging with correlation IDs is the standard pattern — covered in Level 3.

---

## 2. Why & when

Logging request details is essential for:

- **Debugging** production issues by replaying the exact request that caused an error.
- **Auditing** which users called which endpoints.
- **Performance analysis** — correlating slow DB queries with specific request payloads.

`CommonsRequestLoggingFilter` is appropriate for development or low-traffic debugging.  In production, log only what is needed (URI + method + status + duration + correlation ID) and avoid logging request bodies to prevent leaking PII or credentials.

---

## 3. Core concept

```
Request → CommonsRequestLoggingFilter.beforeRequest()  → log "Before request [...]"
        → DispatcherServlet (controller runs)
        → CommonsRequestLoggingFilter.afterRequest()   → log "After request [...]"

Log line format:
  Before request [GET /api/users, headers={Accept=[application/json]}]
  After  request [GET /api/users, headers={Accept=[application/json]}, payload={}]
```

`CommonsRequestLoggingFilter` wraps the request in a `ContentCachingRequestWrapper` to buffer the body for after-request logging — without this wrapper the body input stream can only be read once (by the controller).

---

## 4. Diagram

<svg viewBox="0 0 740 260" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="260" fill="#0d1117"/>

  <!-- Request -->
  <rect x="10" y="110" width="90" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="55" y="133" text-anchor="middle" fill="#79c0ff">Request</text>

  <line x1="100" y1="130" x2="140" y2="130" stroke="#8b949e" marker-end="url(#alg)"/>

  <!-- Logging filter -->
  <rect x="140" y="90" width="160" height="80" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="220" y="112" text-anchor="middle" fill="#6db33f">CommonsRequest</text>
  <text x="220" y="126" text-anchor="middle" fill="#6db33f">LoggingFilter</text>
  <text x="220" y="144" text-anchor="middle" fill="#8b949e" font-size="10">beforeRequest() → LOG</text>
  <text x="220" y="158" text-anchor="middle" fill="#8b949e" font-size="10">wraps in CachingWrapper</text>

  <line x1="300" y1="130" x2="340" y2="130" stroke="#8b949e" marker-end="url(#alg)"/>

  <!-- DispatcherServlet -->
  <rect x="340" y="110" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="405" y="133" text-anchor="middle" fill="#79c0ff">DispatcherServlet</text>

  <line x1="470" y1="130" x2="510" y2="130" stroke="#8b949e" marker-end="url(#alg)"/>

  <!-- Controller -->
  <rect x="510" y="110" width="100" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="560" y="133" text-anchor="middle" fill="#e6edf3">Controller</text>

  <!-- Response back -->
  <line x1="510" y1="150" x2="300" y2="178" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#alg)"/>
  <text x="405" y="170" text-anchor="middle" fill="#8b949e" font-size="10">response</text>

  <!-- afterRequest -->
  <rect x="140" y="178" width="160" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="220" y="196" text-anchor="middle" fill="#6db33f">afterRequest()</text>
  <text x="220" y="212" text-anchor="middle" fill="#8b949e" font-size="10">logs cached body</text>

  <!-- Log target -->
  <line x1="140" y1="198" x2="80" y2="198" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#alg)"/>
  <rect x="10" y="180" width="70" height="36" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="45" y="202" text-anchor="middle" fill="#8b949e">SLF4J log</text>

  <!-- caption -->
  <text x="370" y="248" text-anchor="middle" fill="#8b949e" font-size="11">Filter wraps request to cache body; before/after hooks write to configured logger</text>

  <defs>
    <marker id="alg" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`ContentCachingRequestWrapper` buffers the body so `afterRequest()` can log it after the controller already consumed the stream.*

---

## 5. Runnable example

### Level 1 — Basic

Enable `CommonsRequestLoggingFilter` with a single bean declaration:

```java
// RequestLoggingConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.filter.CommonsRequestLoggingFilter;

@Configuration
public class RequestLoggingConfig {

    @Bean
    public CommonsRequestLoggingFilter loggingFilter() {
        CommonsRequestLoggingFilter filter = new CommonsRequestLoggingFilter();
        filter.setIncludeQueryString(true);
        filter.setIncludeHeaders(false);   // avoid logging auth tokens by default
        filter.setIncludeClientInfo(true);
        filter.setMaxPayloadLength(200);   // truncate body at 200 chars
        filter.setIncludePayload(false);   // body off by default — turn on only for debug
        return filter;
    }
}
```

```properties
# application.properties
logging.level.org.springframework.web.filter.CommonsRequestLoggingFilter=DEBUG
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/api/users?page=1
# Log output:
# DEBUG CommonsRequestLoggingFilter - Before request [GET /api/users?page=1, client=127.0.0.1]
# DEBUG CommonsRequestLoggingFilter - After  request [GET /api/users?page=1, client=127.0.0.1]
```

Setting the logger to `DEBUG` activates the filter's output.  `setIncludeClientInfo(true)` adds the remote IP; `setIncludeQueryString(true)` appends the query string so you can replay the exact request.  Body logging is off — it stays off until deliberately enabled during an incident investigation.

---

### Level 2 — Intermediate

Same logging scenario — now a custom `HandlerInterceptor` that logs method, URI, handler name, and elapsed time in a single structured log line using SLF4J:

```java
// RequestTimingInterceptor.java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerInterceptor;
import jakarta.servlet.http.*;

public class RequestTimingInterceptor implements HandlerInterceptor {

    private static final Logger log = LoggerFactory.getLogger(RequestTimingInterceptor.class);

    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse res, Object handler) {
        req.setAttribute("__start", System.nanoTime());
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest req, HttpServletResponse res,
                                Object handler, Exception ex) {
        long ms = (System.nanoTime() - (long) req.getAttribute("__start")) / 1_000_000;
        String method = handler instanceof HandlerMethod hm
                ? hm.getBeanType().getSimpleName() + "#" + hm.getMethod().getName()
                : handler.getClass().getSimpleName();
        log.info("method={} uri={} status={} elapsed={}ms",
                req.getMethod(), req.getRequestURI(), res.getStatus(), ms);
    }
}
```

```java
// MvcConfig.java
@Override
public void addInterceptors(InterceptorRegistry registry) {
    registry.addInterceptor(new RequestTimingInterceptor());
}
```

**How to run:**
```bash
curl http://localhost:8080/api/users/1
# INFO  RequestTimingInterceptor - method=GET uri=/api/users/1 status=200 elapsed=14ms
```

**What changed:** the interceptor runs inside the MVC pipeline (after handler resolution) so it logs the actual status code set by the controller.  Using SLF4J key=value pairs (logfmt format) makes the output parseable by Loki, Splunk, and similar log aggregators.

---

### Level 3 — Advanced

Production scenario: a `ContentCachingRequestWrapper` + `ContentCachingResponseWrapper` filter that logs request + response bodies **only when the response status is ≥ 400**, avoiding PII logging for normal traffic:

```java
// ErrorBodyLoggingFilter.java
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import org.slf4j.*;
import org.springframework.web.filter.OncePerRequestFilter;
import org.springframework.web.util.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

public class ErrorBodyLoggingFilter extends OncePerRequestFilter {

    private static final Logger log = LoggerFactory.getLogger(ErrorBodyLoggingFilter.class);

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res,
                                    FilterChain chain) throws ServletException, IOException {

        ContentCachingRequestWrapper  wrappedReq = new ContentCachingRequestWrapper(req);
        ContentCachingResponseWrapper wrappedRes = new ContentCachingResponseWrapper(res);

        try {
            chain.doFilter(wrappedReq, wrappedRes);
        } finally {
            int status = wrappedRes.getStatus();
            if (status >= 400) {
                String reqBody = new String(wrappedReq.getContentAsByteArray(), StandardCharsets.UTF_8);
                String resBody = new String(wrappedRes.getContentAsByteArray(), StandardCharsets.UTF_8);
                log.warn("ERROR_REQUEST method={} uri={} status={} reqBody={} resBody={}",
                        req.getMethod(), req.getRequestURI(), status,
                        truncate(reqBody, 500), truncate(resBody, 500));
            }
            // MUST copy response body back — ContentCachingResponseWrapper buffers it
            wrappedRes.copyBodyToResponse();
        }
    }

    private String truncate(String s, int max) {
        return s.length() <= max ? s : s.substring(0, max) + "...[truncated]";
    }
}
```

```java
// FilterConfig.java
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.*;
import jakarta.servlet.DispatcherType;

@Configuration
public class FilterConfig {
    @Bean
    public FilterRegistrationBean<ErrorBodyLoggingFilter> errorBodyFilter() {
        FilterRegistrationBean<ErrorBodyLoggingFilter> reg = new FilterRegistrationBean<>(new ErrorBodyLoggingFilter());
        reg.addUrlPatterns("/api/*");
        reg.setDispatcherTypes(DispatcherType.REQUEST, DispatcherType.ERROR);
        reg.setOrder(1);
        return reg;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# 200 response — no body logged
curl http://localhost:8080/api/users/1

# 404 response — request + response body logged
curl http://localhost:8080/api/users/9999
# WARN ErrorBodyLoggingFilter - ERROR_REQUEST method=GET uri=/api/users/9999 status=404
#   reqBody= resBody={"code":"NOT_FOUND","message":"User 9999 not found"}
```

**What changed and why:**
- `ContentCachingRequestWrapper` buffers the request body — the controller can still call `getInputStream()` normally; the filter reads the cached bytes after.
- `ContentCachingResponseWrapper` buffers the response body — **`copyBodyToResponse()` must be called** or the client receives an empty body.
- Logging only `status >= 400` means normal traffic generates zero body log entries — PII in request payloads is not exposed under normal operation.
- `OncePerRequestFilter` guarantees the filter runs exactly once per request even if the container dispatches to `ERROR`.

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="200" fill="#0d1117"/>
  <rect x="10" y="60" width="100" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="60" y="79" text-anchor="middle" fill="#79c0ff">Request</text>
  <line x1="110" y1="75" x2="145" y2="75" stroke="#8b949e" marker-end="url(#alg2)"/>
  <rect x="145" y="50" width="160" height="50" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="225" y="70" text-anchor="middle" fill="#6db33f">CachingWrapper</text>
  <text x="225" y="86" text-anchor="middle" fill="#8b949e" font-size="10">buffers req + res bodies</text>
  <text x="225" y="100" text-anchor="middle" fill="#8b949e" font-size="10">controller reads normally</text>
  <line x1="305" y1="75" x2="340" y2="75" stroke="#8b949e" marker-end="url(#alg2)"/>
  <rect x="340" y="60" width="110" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="395" y="79" text-anchor="middle" fill="#e6edf3">Controller</text>
  <line x1="340" y1="90" x2="305" y2="120" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#alg2)"/>
  <rect x="145" y="120" width="160" height="50" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="225" y="140" text-anchor="middle" fill="#6db33f">finally block</text>
  <text x="225" y="155" text-anchor="middle" fill="#8b949e" font-size="10">status≥400? → log bodies</text>
  <text x="225" y="170" text-anchor="middle" fill="#8b949e" font-size="10">copyBodyToResponse()</text>
  <text x="400" y="170" text-anchor="middle" fill="#8b949e" font-size="10">200 OK: no body log → zero PII exposure on normal traffic</text>
  <defs><marker id="alg2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Startup:**

1. `ErrorBodyLoggingFilter` is registered by `FilterRegistrationBean` at order 1, scoped to `/api/*`.
2. Tomcat installs it in the filter chain before `DispatcherServlet`.

**Per-request flow (404 path):**

3. `GET /api/users/9999` arrives.
4. `ErrorBodyLoggingFilter.doFilterInternal()` wraps `req` in `ContentCachingRequestWrapper` and `res` in `ContentCachingResponseWrapper`.
5. `chain.doFilter(wrappedReq, wrappedRes)` — `DispatcherServlet` receives the wrapped objects.
6. `HandlerMapping` finds `UserController.getUser`, which throws `UserNotFoundException`.
7. `GlobalExceptionHandler.handleNotFound()` sets status 404, writes JSON body `{"code":"NOT_FOUND",...}` to `wrappedRes` (buffered).
8. Execution returns to the filter's `finally` block.
9. `wrappedRes.getStatus()` → 404 ≥ 400 → log is written with truncated bodies.
10. `wrappedRes.copyBodyToResponse()` flushes the buffered JSON body to the real `HttpServletResponse`. Without this, client gets empty body.

**Request / Response data at each stage:**

| Stage | Data |
|---|---|
| Incoming | raw bytes on socket |
| After wrap | bytes in `ContentCachingRequestWrapper` buffer |
| Controller | reads stream normally (backed by buffer) |
| ExceptionHandler | writes JSON to `ContentCachingResponseWrapper` buffer |
| `finally` (status ≥ 400) | reads both buffers → log line |
| `copyBodyToResponse()` | flushes buffer → real response output stream |

---

## 7. Gotchas & takeaways

> **Forgetting `copyBodyToResponse()` causes an empty response body.**  `ContentCachingResponseWrapper` intercepts writes; the real response stays empty until you explicitly copy the buffer.  This is the most common mistake when building response-logging filters.

> **`CommonsRequestLoggingFilter` logs at `DEBUG` level — the logger class must be set to `DEBUG`, not the root logger.**  Adding `logging.level.root=DEBUG` floods the console; add `logging.level.org.springframework.web.filter.CommonsRequestLoggingFilter=DEBUG` only.

> **Logging request bodies in production leaks passwords and PII.**  Only log bodies on error responses, and truncate at a safe length (e.g. 500 chars).  Ensure the truncated log is PII-reviewed before enabling.

- `CommonsRequestLoggingFilter` is a quick dev-mode tool; for production use a custom filter.
- `ContentCachingRequestWrapper` + `ContentCachingResponseWrapper` is the standard pattern for body logging.
- Structured log lines (key=value or JSON) integrate with log aggregators (Loki, Elasticsearch, Splunk) without custom parsers.
- Always log `status`, `method`, `uri`, `elapsed` — these four fields answer 80% of production debugging questions.
- `OncePerRequestFilter` prevents double-execution on `ERROR` dispatch.
