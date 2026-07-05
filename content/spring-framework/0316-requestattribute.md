---
card: spring-framework
gi: 316
slug: requestattribute
title: "@RequestAttribute"
---

## 1. What it is

`@RequestAttribute` binds a **request-scoped attribute** — a value stored in `HttpServletRequest` via `setAttribute(name, value)` — to a handler method parameter:

```java
@GetMapping("/api/data")
public String data(
    @RequestAttribute("correlationId") String correlationId,       // required
    @RequestAttribute(value = "tenantId", required = false) String tenantId  // optional
) { ... }
```

Request attributes are set by filters or interceptors that run before the handler, and are typically used to pass cross-cutting metadata (correlation IDs, authenticated user objects, parsed tokens) into controllers without polluting the URL or headers.

---

## 2. Why & when

Use `@RequestAttribute` to receive data placed in the request by:

- **Filters** — servlet filters that authenticate, rate-limit, or enrich the request (e.g. set the decoded JWT payload as a request attribute).
- **HandlerInterceptors** — `preHandle()` that validates and parses a header, stores the parsed value.
- **Servlet forwards** — `RequestDispatcher.forward()` passes the original request with its attributes to the forwarded resource.

It is cleaner than injecting `HttpServletRequest` and calling `getAttribute()` manually — the attribute name is declared in the signature, making intent clear and tests easier.

---

## 3. Core concept

```
Filter / Interceptor:
  req.setAttribute("correlationId", UUID.randomUUID().toString());
  req.setAttribute("parsedToken",   jwtService.parse(bearerHeader));

Handler method:
  @RequestAttribute("correlationId") String corrId   → from request attr
  @RequestAttribute("parsedToken")   JwtClaims claims → type-cast from Object

If required=true (default) and attribute absent:
  → 500 ServletRequestBindingException (not 400; it's a programming error, not client error)
```

---

## 4. Diagram

<svg viewBox="0 0 740 260" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="260" fill="#0d1117"/>

  <!-- Filter/Interceptor -->
  <rect x="10" y="80" width="190" height="80" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="100" text-anchor="middle" fill="#6db33f">Filter / Interceptor</text>
  <text x="105" y="116" text-anchor="middle" fill="#8b949e" font-size="10">req.setAttribute(</text>
  <text x="105" y="130" text-anchor="middle" fill="#8b949e" font-size="10">  "correlationId", uuid)</text>
  <text x="105" y="144" text-anchor="middle" fill="#8b949e" font-size="10">  "parsedToken", claims)</text>

  <line x1="200" y1="120" x2="240" y2="120" stroke="#6db33f" marker-end="url(#ara)"/>

  <!-- Request attrs -->
  <rect x="240" y="60" width="200" height="120" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="340" y="80" text-anchor="middle" fill="#8b949e">HttpServletRequest attrs</text>
  <rect x="250" y="90" width="180" height="24" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="340" y="106" text-anchor="middle" fill="#6db33f" font-size="11">correlationId = "abc-123"</text>
  <rect x="250" y="118" width="180" height="24" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="340" y="134" text-anchor="middle" fill="#6db33f" font-size="11">parsedToken = JwtClaims{...}</text>
  <rect x="250" y="146" width="180" height="24" rx="3" fill="#0d1117" stroke="#8b949e"/>
  <text x="340" y="162" text-anchor="middle" fill="#8b949e" font-size="11">startMs = 1700000000</text>

  <line x1="440" y1="120" x2="480" y2="120" stroke="#8b949e" marker-end="url(#ara)"/>

  <!-- Handler -->
  <rect x="480" y="60" width="250" height="120" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="605" y="80" text-anchor="middle" fill="#79c0ff">Handler method</text>
  <text x="490" y="98" fill="#e6edf3" font-size="11">@RequestAttribute</text>
  <text x="490" y="113" fill="#8b949e" font-size="10"> "correlationId" → String</text>
  <text x="490" y="128" fill="#e6edf3" font-size="11">@RequestAttribute</text>
  <text x="490" y="143" fill="#8b949e" font-size="10"> "parsedToken" → JwtClaims</text>
  <text x="490" y="163" fill="#8b949e" font-size="10"> (auto-cast from Object)</text>

  <text x="370" y="225" text-anchor="middle" fill="#8b949e" font-size="11">Request attributes scope: one request only — never cross thread boundaries or requests</text>

  <defs>
    <marker id="ara" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Filters/interceptors set attributes; `@RequestAttribute` reads them — zero boilerplate `request.getAttribute()` in the controller.*

---

## 5. Runnable example

### Level 1 — Basic

An interceptor sets a correlation ID; the controller reads it via `@RequestAttribute`:

```java
// CorrelationInterceptor.java
import org.springframework.web.servlet.HandlerInterceptor;
import jakarta.servlet.http.*;
import java.util.UUID;

public class CorrelationInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse res, Object handler) {
        String id = req.getHeader("X-Correlation-ID");
        if (id == null) id = UUID.randomUUID().toString().substring(0, 8);
        req.setAttribute("correlationId", id);
        res.setHeader("X-Correlation-ID", id);
        return true;
    }
}
```

```java
// DataController.java
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/data")
public class DataController {

    @GetMapping
    public String getData(
            @RequestAttribute("correlationId") String correlationId) {
        return "data served  [corr=" + correlationId + "]";
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
        registry.addInterceptor(new CorrelationInterceptor());
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/api/data
# data served  [corr=a3f9b21c]
# Response header: X-Correlation-ID: a3f9b21c

curl -H "X-Correlation-ID: my-trace" http://localhost:8080/api/data
# data served  [corr=my-trace]
```

`CorrelationInterceptor.preHandle()` stores the ID in the request attributes before the handler runs. `@RequestAttribute("correlationId")` reads it — no `HttpServletRequest` injection needed in the controller.

---

### Level 2 — Intermediate

Same scenario — now an authentication filter parses a JWT and stores the claims; the controller reads the typed claims object:

```java
// JwtFilter.java
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import org.springframework.web.filter.OncePerRequestFilter;
import java.io.IOException;
import java.util.Map;

public class JwtFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res,
                                    FilterChain chain) throws ServletException, IOException {
        String auth = req.getHeader("Authorization");
        if (auth != null && auth.startsWith("Bearer ")) {
            String token = auth.substring(7);
            // Simulate JWT parsing (real code uses a JWT library)
            Map<String, String> claims = parseToken(token);
            req.setAttribute("jwtClaims", claims);
        }
        chain.doFilter(req, res);
    }

    private Map<String, String> parseToken(String token) {
        // Fake decode: token = "user:role" for demo
        String[] parts = token.split(":");
        return parts.length == 2
                ? Map.of("sub", parts[0], "role", parts[1])
                : Map.of("sub", "anonymous", "role", "NONE");
    }
}
```

```java
// DataController.java (extended)
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/data")
public class DataController {

    @GetMapping
    public ResponseEntity<String> getData(
            @RequestAttribute("correlationId") String correlationId,
            @RequestAttribute(value = "jwtClaims", required = false)
            Map<String, String> claims) {

        if (claims == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body("Authentication required");
        }
        if (!"ADMIN".equals(claims.get("role"))) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body("Admin role required");
        }
        return ResponseEntity.ok(
                "data for " + claims.get("sub") + " [corr=" + correlationId + "]");
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# No token
curl http://localhost:8080/api/data
# 401 Authentication required

# User token (not admin)
curl -H "Authorization: Bearer alice:USER" http://localhost:8080/api/data
# 403 Admin role required

# Admin token
curl -H "Authorization: Bearer alice:ADMIN" http://localhost:8080/api/data
# 200 data for alice [corr=...]
```

**What changed:** `JwtFilter` stores parsed claims as a `Map<String,String>` request attribute. `@RequestAttribute(required=false)` binds it — `null` when no token provided. The controller checks authorization without touching the `Authorization` header itself.

---

### Level 3 — Advanced

Production scenario: a filter stores a rich `RequestContext` object; the controller reads it, and a `HandlerInterceptor` adds timing data:

```java
// RequestContext.java
public record RequestContext(
    String correlationId,
    String tenantId,
    String userId,
    String role,
    long   startNanos
) {}
```

```java
// RequestContextFilter.java
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import org.springframework.web.filter.OncePerRequestFilter;
import java.io.IOException;
import java.util.UUID;

public class RequestContextFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res,
                                    FilterChain chain) throws ServletException, IOException {
        String corrId = req.getHeader("X-Correlation-ID");
        if (corrId == null) corrId = UUID.randomUUID().toString().substring(0, 8);

        String auth = req.getHeader("Authorization");
        String userId = "anonymous", role = "NONE";
        if (auth != null && auth.startsWith("Bearer ")) {
            String[] parts = auth.substring(7).split(":");
            if (parts.length == 2) { userId = parts[0]; role = parts[1]; }
        }

        String tenantId = req.getHeader("X-Tenant-ID");

        req.setAttribute("requestContext", new RequestContext(
                corrId, tenantId, userId, role, System.nanoTime()));

        res.setHeader("X-Correlation-ID", corrId);
        chain.doFilter(req, res);
    }
}
```

```java
// DataController.java (production)
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/data")
public class DataController {

    @GetMapping
    public ResponseEntity<String> getData(
            @RequestAttribute("requestContext") RequestContext ctx) {

        if ("anonymous".equals(ctx.userId())) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body("Please authenticate");
        }
        if (ctx.tenantId() == null) {
            return ResponseEntity.badRequest().body("X-Tenant-ID header required");
        }

        long elapsed = (System.nanoTime() - ctx.startNanos()) / 1_000_000;
        return ResponseEntity.ok(String.format(
                "tenant=%s user=%s role=%s corr=%s elapsed=%dms",
                ctx.tenantId(), ctx.userId(), ctx.role(), ctx.correlationId(), elapsed));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -H "Authorization: Bearer alice:ADMIN" \
     -H "X-Tenant-ID: acme" \
     http://localhost:8080/api/data
# tenant=acme user=alice role=ADMIN corr=a3f9b21c elapsed=3ms

curl http://localhost:8080/api/data
# 401 Please authenticate
```

**What changed and why:**
- `RequestContext` is a `record` — immutable, typed, and self-documenting. Binding it as `@RequestAttribute("requestContext")` gives the controller a single clean object instead of five separate `getAttribute()` calls.
- `startNanos` in the context lets the controller compute elapsed time since filter processing started — useful for per-handler SLA tracking without a separate interceptor.
- A single filter sets everything — simpler than multiple interceptors each setting one attribute.

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="180" fill="#0d1117"/>
  <rect x="10" y="40" width="130" height="50" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="75" y="58" text-anchor="middle" fill="#6db33f">Filter</text>
  <text x="75" y="74" text-anchor="middle" fill="#8b949e" font-size="10">builds RequestContext</text>
  <text x="75" y="88" text-anchor="middle" fill="#8b949e" font-size="10">req.setAttribute(...)</text>
  <line x1="140" y1="65" x2="175" y2="65" stroke="#8b949e" marker-end="url(#ara2)"/>
  <rect x="175" y="40" width="160" height="50" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="255" y="58" text-anchor="middle" fill="#8b949e">HttpServletRequest</text>
  <text x="255" y="73" text-anchor="middle" fill="#8b949e" font-size="10">attrs: RequestContext{</text>
  <text x="255" y="87" text-anchor="middle" fill="#8b949e" font-size="10">corrId,tenant,user,...}</text>
  <line x1="335" y1="65" x2="370" y2="65" stroke="#8b949e" marker-end="url(#ara2)"/>
  <rect x="370" y="40" width="200" height="50" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="470" y="58" text-anchor="middle" fill="#79c0ff">Controller</text>
  <text x="470" y="72" text-anchor="middle" fill="#8b949e" font-size="10">@RequestAttribute</text>
  <text x="470" y="86" text-anchor="middle" fill="#8b949e" font-size="10">RequestContext ctx → typed access</text>
  <text x="350" y="145" text-anchor="middle" fill="#8b949e" font-size="10">Request attribute scope = one HTTP request. Never store mutable state or callbacks — they don't survive redirects.</text>
  <defs><marker id="ara2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Per-request: `GET /api/data` with `Authorization: Bearer alice:ADMIN` and `X-Tenant-ID: acme`:**

1. `RequestContextFilter.doFilterInternal()` executes first (filter chain order).
2. Parses headers → builds `RequestContext{correlationId="a3f9b21c", tenantId="acme", userId="alice", role="ADMIN", startNanos=...}`.
3. `req.setAttribute("requestContext", ctx)`.
4. `chain.doFilter(req, res)` → proceeds to `DispatcherServlet`.
5. `CorrelationInterceptor.preHandle()` runs (if registered).
6. `HandlerAdapter.invokeHandlerMethod()` resolves arguments:
   - `@RequestAttribute("requestContext") RequestContext ctx` → `RequestAttributeMethodArgumentResolver` calls `req.getAttribute("requestContext")` → casts to `RequestContext`.
7. `getData(ctx)` executes. `ctx.userId()` = `"alice"` (not anonymous). `ctx.tenantId()` = `"acme"` (not null). All checks pass.
8. `elapsed` = `(currentNanos - ctx.startNanos()) / 1_000_000` → elapsed ms since filter entry.
9. Returns `200 OK  "tenant=acme user=alice role=ADMIN corr=a3f9b21c elapsed=3ms"`.

**State at each layer:**

| Layer | Data |
|---|---|
| Filter | Builds `RequestContext`, stores in request attrs |
| Request attribute map | `{requestContext: RequestContext{...}}` |
| Argument resolver | reads attr, casts to `RequestContext` |
| Controller | uses typed fields directly |
| Response | 200 + formatted string |

---

## 7. Gotchas & takeaways

> **Missing required `@RequestAttribute` → `500 ServletRequestBindingException`, not `400`.**  This is a programming error (the filter that should set the attribute is missing or misconfigured) — not a client error. Use `required = false` when the attribute may legitimately be absent.

> **Request attributes do NOT survive redirects.**  A `"redirect:/new-path"` creates a new request — the new request's attribute map is empty. Use `RedirectAttributes.addFlashAttribute()` (stored in session for one redirect) if you need data after a redirect.

> **Forwarded requests share the request attribute map.**  `RequestDispatcher.forward()` keeps the original `HttpServletRequest`, so attributes set before the forward are visible to the forwarded handler. This is intentional for internal routing.

- `@RequestAttribute` is the clean alternative to `(String) request.getAttribute("name")` in controllers.
- Set attributes in filters or interceptors; read them in controllers — clear separation of concerns.
- Use typed objects (records, POJOs) as attribute values rather than setting many individual string attributes.
- Request attribute scope = one HTTP request thread — never store lambdas, futures, or mutable shared state.
- `required = false` is safe when the attribute may be absent; `required = true` (default) makes missing attributes a server error.
