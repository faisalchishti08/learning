---
card: spring-framework
gi: 304
slug: request-mapping-requestmapping
title: "Request mapping (@RequestMapping)"
---

## 1. What it is

`@RequestMapping` is the core annotation that maps HTTP requests to handler methods or controller classes.  It matches on any combination of:

- **URL pattern** (`value` / `path`)
- **HTTP method** (`method`)
- **Consumed media type** (`consumes`)
- **Produced media type** (`produces`)
- **Request parameters** (`params`)
- **Request headers** (`headers`)

```java
@RequestMapping(
    value   = "/api/users/{id}",
    method  = RequestMethod.GET,
    produces = "application/json"
)
public UserDto getUser(@PathVariable long id) { ... }
```

The shortcut annotations `@GetMapping`, `@PostMapping`, etc. are composed annotations that pin `method` to a specific `RequestMethod` value — they are `@RequestMapping` under the hood.

---

## 2. Why & when

Use `@RequestMapping` (the full form) when you need to specify multiple HTTP methods for one handler (e.g. `method = {GET, HEAD}`), or when you need fine-grained control over `consumes`/`produces`/`params`/`headers` conditions.  For the common single-method cases, use the composed shortcuts (`@GetMapping`, `@PostMapping`, etc.) for clarity.

`@RequestMapping` at **class level** sets a common URL prefix for all handler methods in the controller — methods then specify only their relative path.

---

## 3. Core concept

```
@Controller
@RequestMapping("/api/users")           ← class-level prefix
class UserController {

    @RequestMapping(method = GET)       ← resolves to GET /api/users
    List<User> list() { ... }

    @RequestMapping("/{id}", method = GET) ← resolves to GET /api/users/{id}
    User get(@PathVariable long id) { ... }

    @RequestMapping(method = {GET, HEAD})  ← matches both methods
    ResponseEntity<Void> check() { ... }
}
```

`RequestMappingHandlerMapping` collects all `@RequestMapping` metadata at startup and builds a composite `RequestMappingInfo` for each method.  At runtime it scores each candidate against the incoming request — the highest-scoring candidate wins.

---

## 4. Diagram

<svg viewBox="0 0 740 290" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="290" fill="#0d1117"/>

  <!-- Request box -->
  <rect x="10" y="120" width="140" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="80" y="140" text-anchor="middle" fill="#79c0ff">HTTP Request</text>
  <text x="80" y="156" text-anchor="middle" fill="#8b949e" font-size="10">GET /api/users/1</text>
  <text x="80" y="168" text-anchor="middle" fill="#8b949e" font-size="10">Accept: application/json</text>

  <!-- arrow -->
  <line x1="150" y1="145" x2="195" y2="145" stroke="#8b949e" marker-end="url(#arm)"/>

  <!-- HandlerMapping -->
  <rect x="195" y="100" width="200" height="90" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="295" y="120" text-anchor="middle" fill="#6db33f">RequestMappingHandler</text>
  <text x="295" y="135" text-anchor="middle" fill="#6db33f">Mapping</text>
  <text x="295" y="153" text-anchor="middle" fill="#8b949e" font-size="10">score each RequestMappingInfo</text>
  <text x="295" y="168" text-anchor="middle" fill="#8b949e" font-size="10">path + method + produces match?</text>
  <text x="295" y="183" text-anchor="middle" fill="#6db33f" font-size="10">→ best match wins</text>

  <!-- arrow -->
  <line x1="395" y1="145" x2="440" y2="145" stroke="#8b949e" marker-end="url(#arm)"/>

  <!-- Method box -->
  <rect x="440" y="100" width="200" height="90" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="540" y="120" text-anchor="middle" fill="#79c0ff">UserController#get</text>
  <text x="540" y="137" text-anchor="middle" fill="#8b949e" font-size="10">@RequestMapping("/{id}"</text>
  <text x="540" y="152" text-anchor="middle" fill="#8b949e" font-size="10">method=GET</text>
  <text x="540" y="167" text-anchor="middle" fill="#8b949e" font-size="10">produces="application/json")</text>
  <text x="540" y="182" text-anchor="middle" fill="#6db33f" font-size="10">args resolved → executed</text>

  <!-- class-level annotation -->
  <rect x="195" y="20" width="200" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="295" y="37" text-anchor="middle" fill="#8b949e">@RequestMapping("/api/users")</text>
  <text x="295" y="52" text-anchor="middle" fill="#8b949e" font-size="10">class-level prefix combined with method-level path</text>
  <line x1="295" y1="56" x2="295" y2="100" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#arm)"/>

  <!-- caption -->
  <text x="370" y="255" text-anchor="middle" fill="#8b949e" font-size="11">Class-level prefix + method-level path → full URL pattern; HandlerMapping scores all candidates</text>

  <defs>
    <marker id="arm" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Class-level `@RequestMapping` provides the prefix; method-level annotations refine it.*

---

## 5. Runnable example

### Level 1 — Basic

A controller using `@RequestMapping` explicitly for both GET and POST:

```java
// OrderController.java
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import java.util.*;

@RestController
@RequestMapping("/api/orders")
public class OrderController {

    private final List<String> orders = new ArrayList<>(List.of("order-1", "order-2"));

    // GET /api/orders
    @RequestMapping(method = RequestMethod.GET, produces = "application/json")
    public List<String> list() {
        return orders;
    }

    // POST /api/orders
    @RequestMapping(method = RequestMethod.POST, consumes = "application/json")
    public ResponseEntity<String> create(@RequestBody String name) {
        orders.add(name);
        return ResponseEntity.status(201).body(name);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/api/orders
# ["order-1","order-2"]

curl -X POST -H "Content-Type: application/json" \
     -d '"order-3"' http://localhost:8080/api/orders
# "order-3"
```

`@RequestMapping` on the class sets the `/api/orders` prefix.  Each method-level `@RequestMapping` adds the HTTP-method condition.  `produces` and `consumes` conditions tell `RequestMappingHandlerMapping` to only match this handler when the `Accept` / `Content-Type` headers align.

---

### Level 2 — Intermediate

Same order scenario — now using `params` and `headers` conditions to version the API without URL changes:

```java
// OrderController.java (extended)
@RestController
@RequestMapping("/api/orders")
public class OrderController {

    // Version 1 — selected by ?version=1 query param
    @RequestMapping(method = RequestMethod.GET, params = "version=1")
    public String listV1() {
        return "[{\"id\":1,\"name\":\"order-1\"}]"; // v1 format
    }

    // Version 2 — selected by X-API-Version: 2 header
    @RequestMapping(method = RequestMethod.GET, headers = "X-API-Version=2")
    public String listV2() {
        return "[{\"orderId\":1,\"label\":\"order-1\",\"status\":\"OPEN\"}]"; // v2 richer format
    }

    // Default — no version condition
    @RequestMapping(method = RequestMethod.GET)
    public String listDefault() {
        return "[\"order-1\",\"order-2\"]";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl "http://localhost:8080/api/orders?version=1"
# [{"id":1,"name":"order-1"}]

curl -H "X-API-Version: 2" http://localhost:8080/api/orders
# [{"orderId":1,"label":"order-1","status":"OPEN"}]

curl http://localhost:8080/api/orders
# ["order-1","order-2"]
```

**What changed:** `params = "version=1"` is a condition — the handler only matches when `?version=1` is in the query string.  `headers = "X-API-Version=2"` requires the header to be present with value `"2"`.  More specific conditions score higher, so all three can coexist without ambiguity.

---

### Level 3 — Advanced

Production scenario: fine-grained `@RequestMapping` for both GET and HEAD (for cacheability probing), with `params` negation to separate public vs internal endpoints, and `ETag` support:

```java
// OrderController.java (production)
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.context.request.WebRequest;

@RestController
@RequestMapping("/api/orders")
public class OrderController {

    // Public list — GET and HEAD both served (HEAD for cache probe)
    @RequestMapping(
        method  = {RequestMethod.GET, RequestMethod.HEAD},
        produces = MediaType.APPLICATION_JSON_VALUE,
        params  = "!internal"    // does NOT match if ?internal is present
    )
    public ResponseEntity<String> listPublic(WebRequest webRequest) {
        String etag = "\"v1-orders-hash\"";
        if (webRequest.checkNotModified(etag)) {
            return ResponseEntity.status(304).build(); // 304 Not Modified — no body
        }
        return ResponseEntity.ok()
                .eTag(etag)
                .body("[\"order-1\",\"order-2\"]");
    }

    // Internal list — only matches when ?internal present
    @RequestMapping(
        method  = RequestMethod.GET,
        params  = "internal",    // matches only when ?internal in query
        headers = "X-Internal-Token=secret"
    )
    public String listInternal() {
        return "[\"order-1\",\"order-2\",\"order-3-internal\"]";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Public GET
curl -i http://localhost:8080/api/orders
# HTTP/1.1 200 OK  ETag: "v1-orders-hash"
# ["order-1","order-2"]

# HEAD (cache probe — no body)
curl -i -X HEAD http://localhost:8080/api/orders
# HTTP/1.1 200 OK  ETag: "v1-orders-hash"  (no body)

# Conditional GET with matching ETag — 304
curl -i -H 'If-None-Match: "v1-orders-hash"' http://localhost:8080/api/orders
# HTTP/1.1 304 Not Modified

# Internal endpoint
curl -H "X-Internal-Token: secret" "http://localhost:8080/api/orders?internal"
# ["order-1","order-2","order-3-internal"]
```

**What changed and why:**
- `method = {GET, HEAD}` — `HEAD` responses have all headers but no body; useful for clients checking `ETag`/`Last-Modified` before fetching.
- `params = "!internal"` (exclamation prefix) means "condition true when this param is **absent**" — precise routing without path duplication.
- `webRequest.checkNotModified(etag)` sets the `ETag` response header and returns `true` when the client sent a matching `If-None-Match` — Spring then commits a `304` and the method should return immediately.
- `params = "internal"` + `headers = "X-Internal-Token=secret"` is a compound condition; both must match.

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="200" fill="#0d1117"/>
  <!-- condition matching table -->
  <rect x="10" y="20" width="680" height="140" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="350" y="42" text-anchor="middle" fill="#6db33f" font-weight="bold">RequestMappingInfo scoring</text>
  <!-- row headers -->
  <text x="30" y="62" fill="#8b949e">Condition</text>
  <text x="200" y="62" fill="#8b949e">Request</text>
  <text x="400" y="62" fill="#8b949e">Match?</text>
  <text x="520" y="62" fill="#8b949e">Score (higher = more specific)</text>
  <line x1="20" y1="68" x2="680" y2="68" stroke="#8b949e" stroke-width="0.5"/>
  <!-- rows -->
  <text x="30" y="84" fill="#e6edf3">params="!internal"</text>
  <text x="200" y="84" fill="#e6edf3">no ?internal param</text>
  <text x="400" y="84" fill="#6db33f">yes</text>
  <text x="520" y="84" fill="#8b949e">+1</text>

  <text x="30" y="102" fill="#e6edf3">params="internal"</text>
  <text x="200" y="102" fill="#e6edf3">?internal present</text>
  <text x="400" y="102" fill="#6db33f">yes</text>
  <text x="520" y="102" fill="#8b949e">+1 (combined with header)</text>

  <text x="30" y="120" fill="#e6edf3">method={GET,HEAD}</text>
  <text x="200" y="120" fill="#e6edf3">HEAD /api/orders</text>
  <text x="400" y="120" fill="#6db33f">yes</text>
  <text x="520" y="120" fill="#8b949e">+method specificity</text>

  <text x="30" y="138" fill="#e6edf3">produces="application/json"</text>
  <text x="200" y="138" fill="#e6edf3">Accept: text/html</text>
  <text x="400" y="138" fill="#e74c3c">no</text>
  <text x="520" y="138" fill="#8b949e">→ 406 Not Acceptable</text>

  <text x="350" y="178" text-anchor="middle" fill="#8b949e" font-size="10">Spring evaluates all conditions; the handler with the most conditions satisfied and highest score wins</text>
</svg>

---

## 6. Walkthrough

**Startup:**

1. `RequestMappingHandlerMapping.afterPropertiesSet()` scans all `@Controller` beans.
2. For `OrderController`: class-level `@RequestMapping("/api/orders")` gives the prefix.
3. `listPublic` produces `RequestMappingInfo{path=/api/orders, method={GET,HEAD}, produces=application/json, params=!internal}`.
4. `listInternal` produces `RequestMappingInfo{path=/api/orders, method=GET, params=internal, headers=X-Internal-Token=secret}`.
5. Both are stored in the internal registry.

**Per-request: `HEAD /api/orders` with `If-None-Match: "v1-orders-hash"`:**

6. `DispatcherServlet.doDispatch()` asks `RequestMappingHandlerMapping.getHandler()`.
7. Evaluates `listPublic` conditions: path matches, method `HEAD` is in `{GET,HEAD}`, `Accept: */*` satisfies `produces`, no `?internal` → all conditions satisfied.
8. Evaluates `listInternal` conditions: no `?internal` param → fails `params="internal"`. Score 0.
9. `listPublic` wins. Handler resolved.
10. `HandlerAdapter.handle()` calls `listPublic(webRequest)`.
11. `webRequest.checkNotModified("\"v1-orders-hash\"")` compares with `If-None-Match: "v1-orders-hash"` — match. Marks response as `304`, returns `true`.
12. Method returns early: `ResponseEntity.status(304).build()`.
13. Because it's a `HEAD` request, `DispatcherServlet` strips the body (HEAD responses must not have one).
14. Response: `HTTP/1.1 304 Not Modified  ETag: "v1-orders-hash"` (no body).

**State at each stage:**

| Stage | Data |
|---|---|
| Startup | `RequestMappingInfo` objects stored in registry |
| getHandler() | candidates scored, `listPublic` selected |
| checkNotModified | ETag compared → match → 304 committed |
| Response | 304, no body |

---

## 7. Gotchas & takeaways

> **Ambiguous handler mappings throw `IllegalStateException` at startup.**  If two methods have identical conditions, Spring refuses to start.  Use `params`, `headers`, `consumes`, or `produces` to disambiguate — they all contribute to specificity scoring.

> **`params = "!key"` (negation) only matches when the param is absent.**  It does NOT match when the param is present with value `""`.  If a client sends `?key=`, the negated condition fails.

> **`@RequestMapping` at class level with no method specified matches all HTTP methods.**  A bare `@RequestMapping("/api/users")` on a class allows GET, POST, PUT, DELETE — everything.  Usually you want method-level restrictions.

- `@RequestMapping` is the parent of `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@PatchMapping` — they are composed shortcuts.
- Class-level prefix + method-level path are concatenated: `/api/users` + `/{id}` → `/api/users/{id}`.
- `params`, `headers`, `consumes`, `produces` all add specificity; more conditions = higher score = beats less-specific handlers.
- `HEAD` is handled by Spring MVC automatically for any `GET` handler (response body stripped) — or you can declare it explicitly in `method = {GET, HEAD}` for `ETag` support.
