---
card: spring-framework
gi: 307
slug: consumable-producible-media-types-consumes-produces
title: "Consumable/producible media types (consumes/produces)"
---

## 1. What it is

`consumes` and `produces` are conditions on `@RequestMapping` (and composed shortcuts) that restrict which handler method is selected based on HTTP content negotiation:

- **`consumes`** — matches when the request's `Content-Type` header satisfies the declared media type(s). Restricts which requests a handler accepts.
- **`produces`** — matches when the response media type the handler can produce satisfies the client's `Accept` header. Restricts which responses a handler offers.

```java
@PostMapping(path = "/users", consumes = "application/json", produces = "application/json")
public User create(@RequestBody User user) { ... }
```

If `consumes` does not match → `415 Unsupported Media Type`.  
If `produces` does not match → `406 Not Acceptable`.

---

## 2. Why & when

Use `consumes` and `produces` to:

- **Distinguish handlers by format** — a `GET /data` that produces JSON vs one that produces CSV from the same URL.
- **Enforce API contracts** — reject XML bodies on a JSON-only endpoint with a clear 415 rather than a parse error.
- **Support content negotiation** — same controller, different representations, without URL changes.

Without `produces`, Spring uses `HttpMessageConverter` negotiation at the response stage (not at handler selection), which can lead to `HttpMediaTypeNotAcceptableException` after the handler runs.  Declaring `produces` makes the selection fail fast at routing.

---

## 3. Core concept

```
Client request:
  POST /api/data
  Content-Type: application/json        ← checked against consumes
  Accept: application/xml               ← checked against produces

Handler candidates:
  A: consumes=application/json, produces=application/json  → consumes ✓  produces ✗ (client wants XML)
  B: consumes=application/json, produces=application/xml   → consumes ✓  produces ✓  ← selected

Wildcards:
  consumes=application/*    matches application/json, application/xml, …
  produces=*/*              matches any Accept (like no produces constraint)

Negation:
  consumes=!application/xml  matches any Content-Type EXCEPT application/xml
```

---

## 4. Diagram

<svg viewBox="0 0 740 290" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="290" fill="#0d1117"/>

  <!-- Request -->
  <rect x="10" y="120" width="160" height="60" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="140" text-anchor="middle" fill="#79c0ff">POST /api/data</text>
  <text x="90" y="156" text-anchor="middle" fill="#8b949e" font-size="10">Content-Type: application/json</text>
  <text x="90" y="170" text-anchor="middle" fill="#8b949e" font-size="10">Accept: application/xml</text>

  <!-- arrow -->
  <line x1="170" y1="150" x2="215" y2="150" stroke="#8b949e" marker-end="url(#acp)"/>

  <!-- HandlerMapping box -->
  <rect x="215" y="80" width="200" height="140" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="315" y="100" text-anchor="middle" fill="#6db33f">HandlerMapping</text>
  <text x="315" y="118" text-anchor="middle" fill="#8b949e" font-size="10">evaluate candidates:</text>
  <!-- candidate A -->
  <rect x="225" y="125" width="180" height="30" rx="3" fill="#0d1117" stroke="#e74c3c"/>
  <text x="315" y="140" text-anchor="middle" fill="#e74c3c" font-size="10">A: produces=application/json ✗</text>
  <text x="315" y="152" text-anchor="middle" fill="#8b949e" font-size="9">client wants XML, not JSON</text>
  <!-- candidate B -->
  <rect x="225" y="160" width="180" height="30" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="315" y="175" text-anchor="middle" fill="#6db33f" font-size="10">B: produces=application/xml ✓</text>
  <text x="315" y="187" text-anchor="middle" fill="#8b949e" font-size="9">matches client Accept header</text>
  <text x="315" y="210" text-anchor="middle" fill="#6db33f" font-size="10">→ B selected</text>

  <!-- arrow -->
  <line x1="415" y1="150" x2="460" y2="150" stroke="#6db33f" marker-end="url(#acp)"/>

  <!-- Handler B -->
  <rect x="460" y="110" width="200" height="80" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="560" y="130" text-anchor="middle" fill="#6db33f">createXml()</text>
  <text x="560" y="148" text-anchor="middle" fill="#8b949e" font-size="10">@PostMapping(</text>
  <text x="560" y="162" text-anchor="middle" fill="#8b949e" font-size="10">consumes="application/json"</text>
  <text x="560" y="176" text-anchor="middle" fill="#8b949e" font-size="10">produces="application/xml")</text>

  <!-- response -->
  <line x1="560" y1="190" x2="560" y2="240" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#acp)"/>
  <rect x="460" y="240" width="200" height="36" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="560" y="258" text-anchor="middle" fill="#79c0ff">200 OK  Content-Type: application/xml</text>

  <!-- caption -->
  <text x="370" y="285" text-anchor="middle" fill="#8b949e" font-size="11">consumes filters on Content-Type; produces filters on Accept — fail-fast at routing</text>

  <defs>
    <marker id="acp" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`produces` matching happens at handler selection, not after — the right handler is picked before any business logic runs.*

---

## 5. Runnable example

### Level 1 — Basic

A single endpoint that returns JSON when `Accept: application/json` and a plain string otherwise:

```java
// DataController.java
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/data")
public class DataController {

    // Serves JSON
    @GetMapping(produces = MediaType.APPLICATION_JSON_VALUE)
    public Map<String, Object> dataAsJson() {
        return Map.of("value", 42, "unit", "kg");
    }

    // Serves plain text
    @GetMapping(produces = MediaType.TEXT_PLAIN_VALUE)
    public String dataAsText() {
        return "value=42 unit=kg";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -H "Accept: application/json" http://localhost:8080/api/data
# {"value":42,"unit":"kg"}

curl -H "Accept: text/plain" http://localhost:8080/api/data
# value=42 unit=kg

curl http://localhost:8080/api/data
# {"value":42,"unit":"kg"}  (default when Accept: */* — JSON wins as first match)

curl -H "Accept: application/xml" http://localhost:8080/api/data
# 406 Not Acceptable
```

`RequestMappingHandlerMapping` evaluates `produces` conditions for both methods against the client's `Accept` header.  When two methods match the same path but differ in `produces`, the one whose media type matches `Accept` wins.  Sending `Accept: application/xml` matches neither → 406.

---

### Level 2 — Intermediate

Same data scenario — now adding **CSV export** and a **JSON POST** with strict `consumes` enforcement:

```java
// DataController.java (extended)
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/api/data")
public class DataController {

    @GetMapping(produces = MediaType.APPLICATION_JSON_VALUE)
    public List<Map<String, Object>> listJson() {
        return List.of(Map.of("id", 1, "value", 42), Map.of("id", 2, "value", 17));
    }

    @GetMapping(produces = "text/csv")
    public String listCsv() {
        return "id,value\n1,42\n2,17\n";
    }

    // Only accepts application/json — rejects application/x-www-form-urlencoded etc.
    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE,
                 produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String, Object>> create(@RequestBody Map<String, Object> payload) {
        payload.put("id", 3);
        return ResponseEntity.status(201).body(payload);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# JSON list
curl -H "Accept: application/json" http://localhost:8080/api/data
# [{"id":1,"value":42},{"id":2,"value":17}]

# CSV export
curl -H "Accept: text/csv" http://localhost:8080/api/data
# id,value
# 1,42
# 2,17

# Correct POST
curl -X POST -H "Content-Type: application/json" \
     -H "Accept: application/json" \
     -d '{"value":99}' http://localhost:8080/api/data
# 201  {"value":99,"id":3}

# Wrong Content-Type → 415
curl -X POST -H "Content-Type: application/x-www-form-urlencoded" \
     -d "value=99" http://localhost:8080/api/data
# 415 Unsupported Media Type
```

**What changed:** adding `"text/csv"` as a produced type lets the same URL serve CSV to tools like Excel or Pandas without a different URL.  `consumes = "application/json"` on the POST makes the 415 error appear immediately at routing — before Spring tries to parse the body — giving the caller a precise error.

---

### Level 3 — Advanced

Production scenario: **versioned API representations** via `Accept` header versioning (vendor media types), and negation to exclude a legacy client:

```java
// UserController.java
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users/{id}")
public class UserController {

    // v1 format — simple, used by old clients
    @GetMapping(produces = "application/vnd.myapp.user.v1+json")
    public UserV1 getUserV1(@PathVariable long id) {
        return new UserV1(id, "Alice");
    }

    // v2 format — richer, used by new clients
    @GetMapping(produces = "application/vnd.myapp.user.v2+json")
    public UserV2 getUserV2(@PathVariable long id) {
        return new UserV2(id, "Alice", "alice@example.com", "2024-01-01");
    }

    // Default JSON — for clients that just send Accept: application/json
    // Exclude vendor-specific types with negation
    @GetMapping(produces = {MediaType.APPLICATION_JSON_VALUE})
    public UserV2 getUserDefault(@PathVariable long id) {
        return new UserV2(id, "Alice", "alice@example.com", "2024-01-01");
    }

    // POST — accepts only v2 format bodies; rejects v1
    @PostMapping(
        consumes  = "application/vnd.myapp.user.v2+json",
        produces  = "application/vnd.myapp.user.v2+json"
    )
    public ResponseEntity<UserV2> createV2(@RequestBody UserV2 user) {
        return ResponseEntity.status(201).body(user);
    }

    record UserV1(long id, String name) {}
    record UserV2(long id, String name, String email, String createdAt) {}
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# v1 client
curl -H "Accept: application/vnd.myapp.user.v1+json" http://localhost:8080/api/users/1
# {"id":1,"name":"Alice"}

# v2 client
curl -H "Accept: application/vnd.myapp.user.v2+json" http://localhost:8080/api/users/1
# {"id":1,"name":"Alice","email":"alice@example.com","createdAt":"2024-01-01"}

# Generic JSON client — gets v2 format as default
curl -H "Accept: application/json" http://localhost:8080/api/users/1
# {"id":1,"name":"Alice","email":"alice@example.com","createdAt":"2024-01-01"}

# POST v2 body
curl -X POST -H "Content-Type: application/vnd.myapp.user.v2+json" \
     -H "Accept: application/vnd.myapp.user.v2+json" \
     -d '{"id":2,"name":"Bob","email":"bob@example.com","createdAt":"2024-06-01"}' \
     http://localhost:8080/api/users/2
# 201 Created
```

**What changed and why:**
- **Vendor media types** (`application/vnd.myapp.user.v1+json`) encode the API version in the `Accept` header — URLs stay stable across versions.
- Two `@GetMapping` methods on the same path coexist because they differ in `produces` — Spring selects based on the client's `Accept`.
- `consumes = "application/vnd.myapp.user.v2+json"` on POST ensures only v2-format bodies are accepted for creation.  Old clients sending v1 bodies get `415`.

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="200" fill="#0d1117"/>
  <!-- negotiation table -->
  <rect x="10" y="20" width="680" height="150" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="350" y="40" text-anchor="middle" fill="#6db33f" font-weight="bold">Content negotiation — handler selection</text>
  <text x="30" y="60" fill="#8b949e">Client Accept header</text>
  <text x="300" y="60" fill="#8b949e">Selected handler</text>
  <text x="520" y="60" fill="#8b949e">Response Content-Type</text>
  <line x1="20" y1="65" x2="680" y2="65" stroke="#8b949e" stroke-width="0.5"/>
  <text x="30" y="83" fill="#e6edf3">application/vnd.myapp.user.v1+json</text>
  <text x="300" y="83" fill="#6db33f">getUserV1()</text>
  <text x="520" y="83" fill="#e6edf3">…user.v1+json</text>
  <text x="30" y="103" fill="#e6edf3">application/vnd.myapp.user.v2+json</text>
  <text x="300" y="103" fill="#6db33f">getUserV2()</text>
  <text x="520" y="103" fill="#e6edf3">…user.v2+json</text>
  <text x="30" y="123" fill="#e6edf3">application/json</text>
  <text x="300" y="123" fill="#6db33f">getUserDefault()</text>
  <text x="520" y="123" fill="#e6edf3">application/json</text>
  <text x="30" y="143" fill="#e6edf3">application/xml</text>
  <text x="300" y="143" fill="#e74c3c">no match</text>
  <text x="520" y="143" fill="#e74c3c">406 Not Acceptable</text>
  <text x="350" y="183" text-anchor="middle" fill="#8b949e" font-size="10">Handler selection happens BEFORE controller code runs — routing failure gives exact HTTP error code</text>
</svg>

---

## 6. Walkthrough

**Startup:**

1. Spring scans `UserController`, builds three `RequestMappingInfo` for the three `@GetMapping` methods — each with a different `produces` condition.
2. `RequestMappingHandlerMapping` stores them all under path `/api/users/{id}` method=GET.

**Per-request: `GET /api/users/1` with `Accept: application/vnd.myapp.user.v2+json`:**

3. `HandlerMapping.getHandler()` evaluates all three candidates:
   - `getUserV1`: `produces = "…v1+json"` vs `Accept: "…v2+json"` → no match.
   - `getUserV2`: `produces = "…v2+json"` vs `Accept: "…v2+json"` → match. Score = 1.
   - `getUserDefault`: `produces = "application/json"` vs `Accept: "…v2+json"` → no match (vendor type not compatible with `application/json`).
4. `getUserV2` wins.
5. `HandlerAdapter` calls `getUserV2(1)` → `UserV2{id=1, name="Alice", ...}`.
6. `MappingJackson2HttpMessageConverter` serialises the record to JSON.
7. Sets `Content-Type: application/vnd.myapp.user.v2+json` on response.
8. Response: `200 OK  Content-Type: application/vnd.myapp.user.v2+json`.

**Per-request: `POST /api/users/2` with `Content-Type: application/json`:**

Content-Type `application/json` does not match `consumes = "application/vnd.myapp.user.v2+json"` → `415 Unsupported Media Type` — controller is never invoked.

---

## 7. Gotchas & takeaways

> **`produces` specifies what the handler CAN produce, not what it always will produce.**  Spring selects the handler based on the declared `produces`, then lets `HttpMessageConverter` do the actual serialisation.  If no `HttpMessageConverter` can write the type, `HttpMediaTypeNotAcceptableException` is thrown even if handler selection succeeded.

> **`consumes` and `produces` conditions are OR-matched within a single annotation.**  `produces = {"application/json", "text/plain"}` matches if the client's `Accept` header accepts either type.  To require both simultaneously is not supported — use separate handlers.

> **`!` negation in `consumes`** — `consumes = "!application/xml"` matches any `Content-Type` except `application/xml`.  Useful for blocking a legacy format without listing all accepted alternatives.

- `consumes` guards what goes in; `produces` guards what comes out — both fail at routing with precise 4xx codes.
- Multiple `@GetMapping` methods on the same path can coexist if they differ in `produces` — content negotiation selects the right one.
- Vendor media types (`application/vnd.x.v2+json`) enable URL-stable API versioning via headers.
- Without `produces` declared, `HttpMessageConverter` selection happens at response time — a mismatch becomes `HttpMediaTypeNotAcceptableException` after the handler runs.
