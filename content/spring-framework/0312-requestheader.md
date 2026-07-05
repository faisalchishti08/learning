---
card: spring-framework
gi: 312
slug: requestheader
title: "@RequestHeader"
---

## 1. What it is

`@RequestHeader` binds an HTTP request header value to a method parameter in a Spring MVC handler:

```java
@GetMapping("/api/data")
public String getData(
    @RequestHeader("Authorization") String auth,              // required
    @RequestHeader(value = "X-Tenant-ID",
                   required = false) String tenantId,         // optional → null if absent
    @RequestHeader(value = "X-Retry-Count",
                   defaultValue = "0") int retryCount,        // with default
    @RequestHeader Map<String, String> allHeaders              // all headers as map
) { ... }
```

Spring converts the header value string to the declared parameter type via `ConversionService`. For multi-value headers (e.g. `Accept: text/html, application/json`) use `List<String>` or `String[]`.

---

## 2. Why & when

Use `@RequestHeader` to read protocol metadata that belongs in headers rather than the URL:

- **Authentication** — `Authorization: Bearer <token>` (but in practice use Spring Security)
- **Tenant routing** — `X-Tenant-ID: acme`
- **API versioning** — `X-API-Version: 2`
- **Idempotency keys** — `Idempotency-Key: <uuid>`
- **Client identity** — `User-Agent`, `X-Client-Version`
- **Correlation IDs** — `X-Correlation-ID` (often set/read by interceptors, not controllers)

Avoid reading headers that Spring or a filter already processes (`Content-Type`, `Accept`, `Authorization` when using Spring Security) — let the framework handle those.

---

## 3. Core concept

```
Request:
  GET /api/data
  Authorization: Bearer tok123
  X-Tenant-ID: acme
  Accept: text/html, application/json;q=0.9

Header resolution:
  @RequestHeader("Authorization")  → "Bearer tok123"
  @RequestHeader("X-Tenant-ID")    → "acme"
  @RequestHeader("Accept")         → "text/html, application/json;q=0.9"  (single string)
  @RequestHeader("Accept") List<String> → ["text/html", "application/json;q=0.9"]  (split on ,)
  @RequestHeader Map<String,String>    → all headers, first value per name

Header name matching is case-insensitive (HTTP/1.1 spec).
```

---

## 4. Diagram

<svg viewBox="0 0 740 260" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="260" fill="#0d1117"/>

  <!-- HTTP header block -->
  <rect x="10" y="20" width="220" height="130" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="120" y="38" text-anchor="middle" fill="#8b949e">HTTP Headers</text>
  <text x="25" y="56" fill="#79c0ff" font-size="11">Authorization: Bearer tok123</text>
  <text x="25" y="73" fill="#79c0ff" font-size="11">X-Tenant-ID: acme</text>
  <text x="25" y="90" fill="#79c0ff" font-size="11">X-API-Version: 2</text>
  <text x="25" y="107" fill="#79c0ff" font-size="11">X-Retry-Count: 3</text>
  <text x="25" y="124" fill="#8b949e" font-size="11">Accept: text/html</text>
  <text x="25" y="140" fill="#8b949e" font-size="11">User-Agent: curl/7.x</text>

  <line x1="230" y1="85" x2="270" y2="85" stroke="#8b949e" marker-end="url(#arh)"/>

  <!-- resolver -->
  <rect x="270" y="40" width="200" height="90" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="58" text-anchor="middle" fill="#6db33f">RequestHeader</text>
  <text x="370" y="73" text-anchor="middle" fill="#6db33f">ArgumentResolver</text>
  <text x="370" y="92" text-anchor="middle" fill="#8b949e" font-size="10">case-insensitive name lookup</text>
  <text x="370" y="107" text-anchor="middle" fill="#8b949e" font-size="10">ConversionService for type</text>
  <text x="370" y="122" text-anchor="middle" fill="#8b949e" font-size="10">required check → 400 if missing</text>

  <line x1="470" y1="85" x2="510" y2="85" stroke="#8b949e" marker-end="url(#arh)"/>

  <!-- bound params -->
  <rect x="510" y="30" width="220" height="130" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="620" y="48" text-anchor="middle" fill="#6db33f">Bound Parameters</text>
  <text x="520" y="66" fill="#e6edf3" font-size="11">String auth = "Bearer tok123"</text>
  <text x="520" y="83" fill="#e6edf3" font-size="11">String tenantId = "acme"</text>
  <text x="520" y="100" fill="#e6edf3" font-size="11">int apiVersion = 2</text>
  <text x="520" y="117" fill="#e6edf3" font-size="11">int retryCount = 3</text>
  <text x="520" y="134" fill="#8b949e" font-size="10">Map allHeaders = {all}</text>
  <text x="520" y="150" fill="#8b949e" font-size="10">absent optional → null</text>

  <text x="370" y="225" text-anchor="middle" fill="#8b949e" font-size="11">Header names are case-insensitive; values are type-converted; absent required header → 400</text>

  <defs>
    <marker id="arh" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Header name lookup is case-insensitive; value type conversion is automatic via `ConversionService`.*

---

## 5. Runnable example

### Level 1 — Basic

A tenant-aware endpoint that reads a custom header:

```java
// DataController.java
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/data")
public class DataController {

    @GetMapping
    public ResponseEntity<String> getData(
            @RequestHeader(value = "X-Tenant-ID", required = false) String tenantId,
            @RequestHeader(value = "X-API-Version", defaultValue = "1") int apiVersion) {

        if (tenantId == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("X-Tenant-ID required");
        }
        return ResponseEntity.ok(String.format(
                "tenant=%s apiVersion=%d data={...}", tenantId, apiVersion));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# With tenant header
curl -H "X-Tenant-ID: acme" -H "X-API-Version: 2" http://localhost:8080/api/data
# tenant=acme apiVersion=2 data={...}

# Missing tenant
curl http://localhost:8080/api/data
# 401 X-Tenant-ID required

# Missing API version — uses default
curl -H "X-Tenant-ID: acme" http://localhost:8080/api/data
# tenant=acme apiVersion=1 data={...}
```

`required = false` makes `tenantId` optional — `null` when absent; we check it manually for a semantic 401. `defaultValue = "1"` makes `apiVersion` optional with a fallback, avoiding `NullPointerException` on the `int` parameter. `ConversionService` converts `"2"` to `int 2`.

---

### Level 2 — Intermediate

Same data endpoint — now adding **idempotency key** tracking and reading `User-Agent` to detect API clients:

```java
// DataController.java (extended)
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@RestController
@RequestMapping("/api/data")
public class DataController {

    private final Map<String, String> processedKeys = new ConcurrentHashMap<>();

    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<String> processData(
            @RequestBody String payload,
            @RequestHeader("X-Tenant-ID") String tenantId,             // required
            @RequestHeader(value = "Idempotency-Key",
                           required = false) String idempotencyKey,     // optional
            @RequestHeader(value = "User-Agent",
                           defaultValue = "unknown") String userAgent) {

        // Idempotency check
        if (idempotencyKey != null) {
            String previous = processedKeys.get(idempotencyKey);
            if (previous != null) {
                return ResponseEntity.ok("(idempotent) " + previous);
            }
        }

        String result = "processed by tenant=" + tenantId + " client=" + userAgent;

        if (idempotencyKey != null) {
            processedKeys.put(idempotencyKey, result);
        }

        return ResponseEntity.status(201).body(result);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# First request with idempotency key
curl -i -X POST -H "Content-Type: application/json" \
     -H "X-Tenant-ID: acme" \
     -H "Idempotency-Key: req-abc-001" \
     -d '{"value":42}' http://localhost:8080/api/data
# 201  processed by tenant=acme client=curl/7.x

# Retry with same key — idempotent response
curl -i -X POST -H "Content-Type: application/json" \
     -H "X-Tenant-ID: acme" \
     -H "Idempotency-Key: req-abc-001" \
     -d '{"value":42}' http://localhost:8080/api/data
# 200  (idempotent) processed by tenant=acme client=curl/7.x

# Missing required header → 400
curl -X POST -H "Content-Type: application/json" -d '{}' http://localhost:8080/api/data
# 400 MissingRequestHeaderException: Required header 'X-Tenant-ID' is not present
```

**What changed:** `@RequestHeader("X-Tenant-ID")` is required (no `required=false`) — Spring returns `400` with a clear message if missing. `Idempotency-Key` is optional; its absence means "don't deduplicate". `User-Agent` has a `defaultValue` so non-browser clients that omit it don't cause a NPE.

---

### Level 3 — Advanced

Production scenario: reading **all headers** into a `Map`, extracting a **custom signed-request signature** header, and using `@RequestHeader HttpHeaders` to access the full typed header object:

```java
// SecureDataController.java
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.security.MessageDigest;
import java.util.*;

@RestController
@RequestMapping("/api/secure")
public class SecureDataController {

    private static final String SECRET = "mysecret";

    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String,Object>> secureProcess(
            @RequestBody String payload,
            // HttpHeaders gives access to all headers with typed getters
            @RequestHeader HttpHeaders headers,
            // Named headers extracted individually
            @RequestHeader("X-Timestamp") long timestamp,
            @RequestHeader("X-Signature") String signature,
            @RequestHeader(value = "X-Forwarded-For",
                           required = false) String forwardedFor) throws Exception {

        // 1. Validate timestamp to prevent replay attacks (5 min window)
        long now = System.currentTimeMillis() / 1000;
        if (Math.abs(now - timestamp) > 300) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Timestamp too old or in future"));
        }

        // 2. Verify HMAC signature: SHA-256(SECRET + timestamp + payload)
        String expected = sha256(SECRET + timestamp + payload);
        if (!MessageDigest.isEqual(expected.getBytes(), signature.getBytes())) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Invalid signature"));
        }

        // 3. Use HttpHeaders typed API
        List<MediaType> accepted = headers.getAccept();
        String contentType = headers.getFirst(HttpHeaders.CONTENT_TYPE);
        String clientIp = forwardedFor != null ? forwardedFor.split(",")[0].trim()
                                               : "direct";

        return ResponseEntity.ok(Map.of(
                "status", "processed",
                "clientIp", clientIp,
                "accept", accepted.toString(),
                "contentType", contentType));
    }

    private static String sha256(String input) throws Exception {
        var digest = MessageDigest.getInstance("SHA-256");
        byte[] hash = digest.digest(input.getBytes("UTF-8"));
        var sb = new StringBuilder();
        for (byte b : hash) sb.append(String.format("%02x", b));
        return sb.toString();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

PAYLOAD='{"value":42}'
TS=$(date +%s)
SIG=$(echo -n "mysecret${TS}${PAYLOAD}" | sha256sum | cut -d' ' -f1)

curl -i -X POST \
     -H "Content-Type: application/json" \
     -H "X-Timestamp: $TS" \
     -H "X-Signature: $SIG" \
     -H "Accept: application/json" \
     -d "$PAYLOAD" http://localhost:8080/api/secure
# 200 OK
# {"status":"processed","clientIp":"direct","accept":"[application/json]","contentType":"application/json"}

# Wrong signature
curl -X POST -H "Content-Type: application/json" \
     -H "X-Timestamp: $TS" \
     -H "X-Signature: wrongsig" \
     -d "$PAYLOAD" http://localhost:8080/api/secure
# 401 {"error":"Invalid signature"}
```

**What changed and why:**
- `@RequestHeader HttpHeaders headers` gives the full `org.springframework.http.HttpHeaders` object — typed API for `getAccept()`, `getContentType()`, `getFirst("X-Custom")`, iteration, etc. — instead of pulling each header individually.
- `@RequestHeader("X-Timestamp") long timestamp` — `ConversionService` converts the string epoch to `long` automatically.
- `MessageDigest.isEqual(a, b)` is a **constant-time comparison** — prevents timing-based signature oracle attacks that `String.equals()` would allow.
- `X-Forwarded-For` value is split on `,` to extract the real client IP (proxies append their address to the list).

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="190" fill="#0d1117"/>
  <!-- signature verification flow -->
  <rect x="10" y="40" width="130" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="59" text-anchor="middle" fill="#79c0ff">X-Timestamp: 1700000</text>
  <rect x="10" y="80" width="130" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="99" text-anchor="middle" fill="#79c0ff">X-Signature: a3f9...</text>
  <rect x="10" y="120" width="130" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="139" text-anchor="middle" fill="#79c0ff">payload: {value:42}</text>

  <!-- step 1: timestamp check -->
  <line x1="140" y1="55" x2="175" y2="80" stroke="#8b949e" marker-end="url(#arh2)"/>
  <line x1="140" y1="95" x2="175" y2="85" stroke="#8b949e" marker-end="url(#arh2)"/>
  <line x1="140" y1="135" x2="175" y2="92" stroke="#8b949e" marker-end="url(#arh2)"/>

  <rect x="175" y="60" width="160" height="50" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="255" y="80" text-anchor="middle" fill="#6db33f">|now - timestamp|</text>
  <text x="255" y="95" text-anchor="middle" fill="#6db33f">&lt; 300s?</text>
  <text x="255" y="108" text-anchor="middle" fill="#8b949e" font-size="10">replay attack window</text>

  <line x1="335" y1="85" x2="370" y2="85" stroke="#8b949e" marker-end="url(#arh2)"/>
  <text x="352" y="79" fill="#6db33f" font-size="10">ok</text>

  <rect x="370" y="60" width="180" height="50" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="460" y="80" text-anchor="middle" fill="#6db33f">SHA-256(secret+ts+body)</text>
  <text x="460" y="96" text-anchor="middle" fill="#6db33f">== X-Signature?</text>
  <text x="460" y="108" text-anchor="middle" fill="#8b949e" font-size="10">constant-time compare</text>

  <line x1="550" y1="85" x2="585" y2="85" stroke="#8b949e" marker-end="url(#arh2)"/>
  <text x="567" y="79" fill="#6db33f" font-size="10">ok</text>
  <rect x="585" y="70" width="100" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="635" y="89" text-anchor="middle" fill="#e6edf3">200 OK</text>

  <text x="350" y="165" text-anchor="middle" fill="#8b949e" font-size="10">MessageDigest.isEqual() is constant-time — prevents timing oracle attacks on signature verification</text>
  <defs><marker id="arh2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Per-request: `POST /api/secure` with correct headers and signature:**

1. `DispatcherServlet` delegates to `SecureDataController.secureProcess`.
2. `HandlerAdapter` resolves arguments:
   - `@RequestBody String payload` — reads raw JSON string from input stream.
   - `@RequestHeader HttpHeaders headers` — `RequestHeaderMapMethodArgumentResolver` wraps the native header map in an `HttpHeaders` object (typed, immutable view).
   - `@RequestHeader("X-Timestamp") long timestamp` — reads header string `"1700000000"`, converts to `long` via `ConversionService`.
   - `@RequestHeader("X-Signature") String signature` — reads header string.
   - `@RequestHeader(value="X-Forwarded-For", required=false) String forwardedFor` — absent → `null`.
3. `secureProcess(payload, headers, 1700000000L, "a3f9...", null)` executes.
4. `|now - 1700000000| < 300` — timestamp valid.
5. `sha256("mysecret" + 1700000000 + '{"value":42}')` computed. Compared to `"a3f9..."` using `MessageDigest.isEqual()` — constant-time comparison.
6. `headers.getAccept()` → `[application/json]`. `headers.getFirst("Content-Type")` → `"application/json"`.
7. `forwardedFor == null` → `clientIp = "direct"`.
8. Returns `200 OK` with JSON result.

**State changes at each layer:**

| Layer | Data |
|---|---|
| Incoming headers | raw HTTP header strings |
| `@RequestHeader long timestamp` | `"1700000000"` → `long` |
| `HttpHeaders headers` | typed wrapper; `.getAccept()` returns `List<MediaType>` |
| Signature check | sha256 computed, constant-time compared |
| Response | `200 + JSON` or `401 + error` |

---

## 7. Gotchas & takeaways

> **HTTP header names are case-insensitive; Spring normalises them.**  `@RequestHeader("x-tenant-id")` and `@RequestHeader("X-Tenant-ID")` both work correctly. Header values are case-sensitive — `Authorization: bearer tok` vs `Authorization: Bearer tok` are different strings.

> **Never use `String.equals()` for security tokens or signatures — use `MessageDigest.isEqual()`.**  `String.equals()` short-circuits on the first mismatching byte, leaking timing information. Constant-time comparison prevents timing oracle attacks.

> **`@RequestHeader HttpHeaders headers` gives all headers — useful for logging or forwarding.**  It wraps the native header map with typed getters and multi-value support. Do NOT log the full `HttpHeaders` object in production — it includes `Authorization` and other sensitive values.

- `required = false` + null check is safer than `defaultValue = ""` for headers that have semantic meaning when absent.
- `@RequestHeader Map<String,String>` binds first value per header; `MultiValueMap<String,String>` binds all values.
- `@RequestHeader HttpHeaders` gives the full typed API — `getAccept()`, `getContentType()`, `getFirst("X-Custom")`.
- `X-Forwarded-For` can contain multiple IPs (comma-separated) when passing through multiple proxies — always split and take the first for the real client IP.
- Use `@RequestHeader` for custom protocol headers; let Spring Security handle `Authorization`.
