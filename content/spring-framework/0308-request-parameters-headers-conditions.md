---
card: spring-framework
gi: 308
slug: request-parameters-headers-conditions
title: "Request parameters & headers conditions"
---

## 1. What it is

`params` and `headers` are **routing conditions** on `@RequestMapping` (and its composed shortcuts) that narrow handler selection beyond path + HTTP method.

- **`params`** — matches against query-string parameters (presence, absence, or value equality).
- **`headers`** — matches against request headers (presence, absence, or value equality).

```java
// only matches GET /api/users?format=detailed
@GetMapping(value = "/api/users", params = "format=detailed")
public List<UserDetail> detailed() { ... }

// only matches when X-Internal-Token header is present
@GetMapping(value = "/api/users", headers = "X-Internal-Token")
public List<User> internal() { ... }
```

These conditions complement `consumes`/`produces` — all four are evaluated together during handler selection.

---

## 2. Why & when

Use `params` conditions to:
- Distinguish API **versions** via a query parameter (`?version=2`).
- Serve **different representations** from the same URL (`?format=csv`).
- Route **special modes** (debug, verbose, paginated vs. full).

Use `headers` conditions to:
- Guard **internal-only endpoints** with a secret header.
- Route by **custom protocol version** header (`X-API-Version: 2`).
- Differentiate requests from specific clients (`User-Agent` prefix matching).

Both avoid URL proliferation — same path, different behaviour based on request metadata.

---

## 3. Core concept

```
Condition syntax (same for params and headers):

  "key"          — param/header must be present (any value)
  "!key"         — param/header must be absent
  "key=value"    — param/header must equal value exactly
  "key!=value"   — param/header must not equal value

Multiple conditions in one annotation = AND (all must match):
  params = {"version=2", "format=json"}   ← both must match

Multiple values inside one string = not supported (use separate conditions).
```

All `params`/`headers` conditions must pass for a handler to be selected. The handler with the most conditions satisfied (highest specificity score) wins over a less specific one.

---

## 4. Diagram

<svg viewBox="0 0 740 280" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="280" fill="#0d1117"/>

  <!-- request -->
  <rect x="10" y="110" width="180" height="60" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="130" text-anchor="middle" fill="#79c0ff">GET /api/users</text>
  <text x="100" y="147" text-anchor="middle" fill="#8b949e" font-size="10">?version=2&amp;format=csv</text>
  <text x="100" y="163" text-anchor="middle" fill="#8b949e" font-size="10">X-Client: dashboard</text>

  <line x1="190" y1="140" x2="230" y2="140" stroke="#8b949e" marker-end="url(#ach)"/>

  <!-- Mapping box -->
  <rect x="230" y="60" width="220" height="160" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="80" text-anchor="middle" fill="#6db33f">HandlerMapping</text>
  <text x="340" y="96" text-anchor="middle" fill="#8b949e" font-size="10">evaluate params+headers:</text>

  <!-- candidate A -->
  <rect x="240" y="103" width="200" height="32" rx="3" fill="#0d1117" stroke="#e74c3c"/>
  <text x="340" y="118" text-anchor="middle" fill="#e74c3c" font-size="10">A: params="version=1" ✗</text>
  <text x="340" y="130" text-anchor="middle" fill="#8b949e" font-size="9">request has version=2</text>

  <!-- candidate B -->
  <rect x="240" y="140" width="200" height="32" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="340" y="155" text-anchor="middle" fill="#6db33f" font-size="10">B: params="version=2" ✓</text>
  <text x="340" y="167" text-anchor="middle" fill="#8b949e" font-size="9">headers="X-Client" ✓ → selected</text>

  <!-- candidate C -->
  <rect x="240" y="177" width="200" height="28" rx="3" fill="#0d1117" stroke="#8b949e"/>
  <text x="340" y="193" text-anchor="middle" fill="#8b949e" font-size="10">C: no conditions → lower score</text>

  <!-- winner arrow -->
  <line x1="450" y1="140" x2="490" y2="140" stroke="#6db33f" marker-end="url(#ach)"/>
  <rect x="490" y="110" width="200" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="590" y="133" text-anchor="middle" fill="#6db33f">listV2Csv()</text>
  <text x="590" y="150" text-anchor="middle" fill="#8b949e" font-size="10">params={"version=2","format=csv"}</text>
  <text x="590" y="163" text-anchor="middle" fill="#8b949e" font-size="10">headers="X-Client"</text>

  <text x="370" y="250" text-anchor="middle" fill="#8b949e" font-size="11">More conditions = higher specificity score = beats less-specific handlers</text>

  <defs>
    <marker id="ach" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*All conditions are AND'd; the handler with the most satisfied conditions wins.*

---

## 5. Runnable example

### Level 1 — Basic

Two handlers on the same path distinguished by `params`:

```java
// ReportController.java
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/reports")
public class ReportController {

    // Default — no param condition
    @GetMapping
    public String summary() {
        return "id,total\n1,100\n2,200";
    }

    // Only when ?detailed=true
    @GetMapping(params = "detailed=true")
    public String detailed() {
        return "id,name,total,tax\n1,Alice,100,10\n2,Bob,200,20";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/api/reports
# id,total
# 1,100

curl "http://localhost:8080/api/reports?detailed=true"
# id,name,total,tax
# 1,Alice,100,10
```

`params = "detailed=true"` scores higher than no condition, so `?detailed=true` routes to `detailed()` while bare `/api/reports` falls through to `summary()`. Spring evaluates `params` during handler selection — the method body never needs to check the parameter itself.

---

### Level 2 — Intermediate

Same report scenario — now adding `headers` condition for an internal-only endpoint, and `params` negation to explicitly exclude debug mode:

```java
// ReportController.java (extended)
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/reports")
public class ReportController {

    // Public summary — excludes requests with ?debug param
    @GetMapping(params = "!debug")
    public String summary() {
        return "{\"total\":300}";
    }

    // Debug mode — only when ?debug present
    @GetMapping(params = "debug")
    public String debug() {
        return "{\"total\":300,\"breakdown\":[100,200],\"sql\":\"SELECT SUM(amount) FROM orders\"}";
    }

    // Internal full dump — requires secret header
    @GetMapping(headers = "X-Internal-Token=s3cr3t")
    public String internalDump() {
        return "{\"total\":300,\"userIds\":[1,2],\"rawData\":true}";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Public
curl http://localhost:8080/api/reports
# {"total":300}

# Debug mode
curl "http://localhost:8080/api/reports?debug"
# {"total":300,"breakdown":[100,200],"sql":"..."}

# Internal — header required
curl -H "X-Internal-Token: s3cr3t" http://localhost:8080/api/reports
# {"total":300,"userIds":[1,2],"rawData":true}

# Wrong token value — no match (headers condition fails) → falls to summary
curl -H "X-Internal-Token: wrong" http://localhost:8080/api/reports
# {"total":300}
```

**What changed:** `params = "!debug"` explicitly excludes debug requests from the public handler — without this, both `summary` and `debug` would match `?debug` (the debug one more specifically, but the intent is clearer with negation). `headers = "X-Internal-Token=s3cr3t"` — value comparison is case-sensitive and exact. A wrong token value fails the condition; the request falls to the next match (`summary`).

---

### Level 3 — Advanced

Production scenario: a versioned reporting API using `params` + `headers` together for a compound routing scheme — supporting both query-param versioning (legacy clients) and header versioning (modern clients):

```java
// ReportController.java (production)
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/reports")
public class ReportController {

    // v1 via query param — legacy clients
    @GetMapping(params = "version=1", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String,Object>> v1ByParam() {
        return ResponseEntity.ok(Map.of("schema", "v1", "total", 300));
    }

    // v2 via query param — newer query-param clients
    @GetMapping(params = "version=2", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String,Object>> v2ByParam() {
        return ResponseEntity.ok(Map.of("schema", "v2", "total", 300, "currency", "USD"));
    }

    // v2 via header — modern header-versioning clients (higher specificity)
    @GetMapping(
        headers  = "X-API-Version=2",
        produces = MediaType.APPLICATION_JSON_VALUE
    )
    public ResponseEntity<Map<String,Object>> v2ByHeader() {
        return ResponseEntity.ok(Map.of("schema", "v2-header", "total", 300, "currency", "USD"));
    }

    // v3 via header only
    @GetMapping(
        headers  = "X-API-Version=3",
        produces = MediaType.APPLICATION_JSON_VALUE
    )
    public ResponseEntity<Map<String,Object>> v3ByHeader() {
        return ResponseEntity.ok(Map.of("schema", "v3", "total", 300, "currency", "USD", "breakdown", true));
    }

    // Default — no version specified (lowest priority)
    @GetMapping(produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String,Object>> defaultReport() {
        return ResponseEntity.ok(Map.of("schema", "v1", "total", 300));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Legacy client
curl "http://localhost:8080/api/reports?version=1"
# {"schema":"v1","total":300}

# Query-param v2
curl "http://localhost:8080/api/reports?version=2"
# {"schema":"v2","total":300,"currency":"USD"}

# Header v2
curl -H "X-API-Version: 2" http://localhost:8080/api/reports
# {"schema":"v2-header","total":300,"currency":"USD"}

# Header v3
curl -H "X-API-Version: 3" http://localhost:8080/api/reports
# {"schema":"v3","total":300,"currency":"USD","breakdown":true}

# No version — default
curl http://localhost:8080/api/reports
# {"schema":"v1","total":300}
```

**What changed and why:**
- `params = "version=1"` and `params = "version=2"` route legacy query-param callers without touching the URL structure.
- `headers = "X-API-Version=2"` routes modern clients using header versioning — the same URL `/api/reports`, zero URL proliferation.
- When both `?version=2` *and* `X-API-Version: 2` are sent, `v2ByHeader` wins because header conditions score higher than param conditions in Spring's specificity ordering when combined with the same path.
- `defaultReport` has no `params`/`headers` conditions — lowest specificity, matched only when nothing else does.

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="190" fill="#0d1117"/>
  <text x="350" y="22" text-anchor="middle" fill="#6db33f" font-weight="bold">Specificity ordering (GET /api/reports)</text>
  <!-- rows -->
  <rect x="10" y="35" width="680" height="24" rx="3" fill="#1c2430" stroke="#6db33f"/>
  <text x="20" y="51" fill="#6db33f">headers="X-API-Version=2"  +  produces</text>
  <text x="500" y="51" fill="#6db33f">← highest (header+produces)</text>

  <rect x="10" y="63" width="680" height="24" rx="3" fill="#1c2430" stroke="#79c0ff"/>
  <text x="20" y="79" fill="#79c0ff">params="version=2"  +  produces</text>
  <text x="500" y="79" fill="#79c0ff">← param+produces</text>

  <rect x="10" y="91" width="680" height="24" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="20" y="107" fill="#8b949e">produces only</text>
  <text x="500" y="107" fill="#8b949e">← produces alone</text>

  <rect x="10" y="119" width="680" height="24" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="20" y="135" fill="#8b949e">no conditions</text>
  <text x="500" y="135" fill="#8b949e">← fallback (lowest)</text>

  <text x="350" y="168" text-anchor="middle" fill="#8b949e" font-size="10">Spring selects the highest-specificity handler that satisfies ALL its conditions</text>
</svg>

---

## 6. Walkthrough

**Startup:**

1. `RequestMappingHandlerMapping` scans `ReportController`, building five `RequestMappingInfo` objects — all share path `/api/reports` and `method=GET`, but differ in `params`, `headers`, and `produces` conditions.
2. Each condition adds specificity weight to the handler's score.

**Per-request: `GET /api/reports?version=2` with `Accept: application/json`:**

3. `DispatcherServlet.doDispatch()` → `HandlerMapping.getHandler()`.
4. Evaluates all five candidates:
   - `v1ByParam`: `params="version=1"` — request has `version=2` → fails.
   - `v2ByParam`: `params="version=2"` → matches. `produces="application/json"` vs `Accept: */*` → matches. Score = params+produces.
   - `v2ByHeader`: `headers="X-API-Version=2"` — no such header → fails.
   - `v3ByHeader`: `headers="X-API-Version=3"` → fails.
   - `defaultReport`: no conditions → matches, lowest score.
5. `v2ByParam` wins (higher score than default).
6. `HandlerAdapter` calls `v2ByParam()`.
7. Returns `Map.of("schema","v2","total",300,"currency","USD")`.
8. `MappingJackson2HttpMessageConverter` serialises to JSON.
9. Response: `200 OK  Content-Type: application/json  {"schema":"v2","total":300,"currency":"USD"}`.

**Per-request: `GET /api/reports` with `X-API-Version: 3`:**

4b. Evaluates candidates: `v3ByHeader` → `headers="X-API-Version=3"` matches. Scores headers+produces.
5b. `v3ByHeader` wins.
9b. Response: `{"schema":"v3","total":300,"currency":"USD","breakdown":true}`.

**State changes:**

| Stage | Data |
|---|---|
| Incoming request | path, method, headers, params |
| HandlerMapping | all five candidates scored; highest-scoring wins |
| HandlerAdapter | method called, Map produced |
| MessageConverter | Map → JSON bytes |
| Response | 200 + JSON body |

---

## 7. Gotchas & takeaways

> **`params` and `headers` conditions are case-sensitive for values.**  `headers = "X-API-Version=2"` does not match `X-API-Version: 2 ` (trailing space) or `x-api-version: 2` (lowercase header name in HTTP/1.1 is fine — Spring normalises header names, but values are exact).

> **Overusing `params` conditions creates invisible routing complexity.**  A caller looking at the URL `/api/reports` cannot know how many hidden variants exist. Document all `params`/`headers` routing branches in API docs or OpenAPI annotations.

> **`headers` condition can match any header, including `Content-Type` and `Accept` — but use `consumes`/`produces` for those.**  `headers = "Content-Type=application/json"` works but does not participate in the standard content-negotiation scoring the way `consumes` does.

- `params = "key"` = present (any value); `params = "key=val"` = exact value; `params = "!key"` = absent.
- `headers` uses the same syntax; header names are case-insensitive, values are case-sensitive.
- Multiple conditions in one annotation are AND'd; more conditions = higher specificity = beats less-specific handlers.
- Use `params` for query-param versioning, `headers` for header versioning — both are valid patterns without URL changes.
- Prefer `consumes`/`produces` over `headers="Content-Type=..."` / `headers="Accept=..."` — they integrate with Spring's content-negotiation infrastructure.
