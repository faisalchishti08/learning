---
card: spring-framework
gi: 319
slug: httpentity-requestentity
title: "HttpEntity / RequestEntity"
---

## 1. What it is

`HttpEntity<T>` wraps both HTTP headers and a body as a single parameter. `RequestEntity<T>` extends it with the HTTP method and URI — useful when the controller needs to inspect routing metadata:

```java
// Receive headers + body together
@PostMapping("/products")
public Product create(HttpEntity<ProductRequest> entity) {
    HttpHeaders headers = entity.getHeaders();  // all request headers
    ProductRequest body = entity.getBody();      // deserialized via HttpMessageConverter
    ...
}

// Receive method + URI + headers + body
@PostMapping("/products")
public Product create(RequestEntity<ProductRequest> entity) {
    HttpMethod method = entity.getMethod();  // POST
    URI uri = entity.getUrl();               // http://localhost:8080/products
    ...
}
```

Unlike `@RequestBody`, `HttpEntity` does **not** require any annotation — Spring detects the type automatically.

---

## 2. Why & when

Use `HttpEntity<T>` when a handler needs both the body **and** specific request headers without declaring multiple `@RequestHeader` parameters:
- Reading `Content-Type`, `Content-Length`, or `Accept` alongside the body.
- Signature verification headers (`X-Signature`) correlated with the body they sign.
- Generic proxy or adapter handlers that forward headers upstream.

Use `RequestEntity<T>` (adds method + URI) when:
- Building RESTful relay/proxy — pass the full `RequestEntity` to `RestTemplate.exchange()`.
- The handler is generic and needs to know which HTTP method was invoked.

For most cases where you only need the body, prefer `@RequestBody` — it is more explicit about intent.

---

## 3. Core concept

```
POST /products HTTP/1.1
Content-Type: application/json
X-Signature: abc123
{"name":"Drill","price":29.99}

HttpEntity<ProductRequest> entity
  entity.getHeaders()
    → HttpHeaders{Content-Type=application/json, X-Signature=abc123, ...}
  entity.getBody()
    → ProductRequest{name="Drill", price=29.99}
    (deserialized by MappingJackson2HttpMessageConverter, same as @RequestBody)

RequestEntity<ProductRequest> entity (extends HttpEntity)
  entity.getMethod() → HttpMethod.POST
  entity.getUrl()    → URI("http://localhost:8080/products")
```

---

## 4. Diagram

<svg viewBox="0 0 740 230" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="230" fill="#0d1117"/>

  <!-- request -->
  <rect x="10" y="40" width="200" height="80" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="58" text-anchor="middle" fill="#79c0ff">HTTP Request</text>
  <text x="20" y="75" fill="#8b949e" font-size="10">Method:  POST</text>
  <text x="20" y="90" fill="#8b949e" font-size="10">URI:     /products</text>
  <text x="20" y="105" fill="#8b949e" font-size="10">Headers: Content-Type, X-Sig</text>
  <text x="20" y="120" fill="#8b949e" font-size="10">Body:    {"name":"Drill",...}</text>

  <line x1="210" y1="80" x2="245" y2="80" stroke="#8b949e" marker-end="url(#arhe)"/>

  <!-- resolver -->
  <rect x="245" y="40" width="200" height="80" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="345" y="60" text-anchor="middle" fill="#6db33f">HttpEntityMethod</text>
  <text x="345" y="75" text-anchor="middle" fill="#6db33f">ArgumentResolver</text>
  <text x="255" y="92" fill="#8b949e" font-size="10">reads headers into HttpHeaders</text>
  <text x="255" y="107" fill="#8b949e" font-size="10">delegates body to HttpMessageConverter</text>
  <text x="255" y="119" fill="#8b949e" font-size="10">for RequestEntity: adds method+URI</text>

  <line x1="445" y1="80" x2="480" y2="80" stroke="#8b949e" marker-end="url(#arhe)"/>

  <!-- entity -->
  <rect x="480" y="30" width="240" height="100" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="600" y="50" text-anchor="middle" fill="#6db33f">HttpEntity / RequestEntity</text>
  <text x="490" y="68" fill="#e6edf3" font-size="11">getHeaders() → HttpHeaders</text>
  <text x="490" y="84" fill="#e6edf3" font-size="11">getBody() → ProductRequest</text>
  <text x="490" y="100" fill="#8b949e" font-size="10">--- RequestEntity only ---</text>
  <text x="490" y="116" fill="#e6edf3" font-size="11">getMethod() → POST</text>
  <text x="490" y="130" fill="#e6edf3" font-size="11">getUrl()    → URI</text>

  <text x="370" y="215" text-anchor="middle" fill="#8b949e" font-size="11">HttpEntity = headers + body; RequestEntity adds method + URI; body via same HttpMessageConverter chain</text>

  <defs>
    <marker id="arhe" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`RequestEntity` is a superset of `HttpEntity` — use `RequestEntity` only when the method or URI is needed.*

---

## 5. Runnable example

### Level 1 — Basic

An endpoint that reads the `Content-Language` header alongside the body using `HttpEntity`:

```java
// ProductController.java
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/products")
public class ProductController {

    record ProductRequest(String name, double price) {}

    @PostMapping
    public String create(HttpEntity<ProductRequest> entity) {
        String contentLang = entity.getHeaders()
                .getFirst(HttpHeaders.CONTENT_LANGUAGE);
        ProductRequest body = entity.getBody();

        return "lang=" + contentLang + " name=" + body.name() + " price=" + body.price();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -X POST http://localhost:8080/products \
     -H "Content-Type: application/json" \
     -H "Content-Language: fr" \
     -d '{"name":"Perceuse","price":39.99}'
# lang=fr name=Perceuse price=39.99

# Missing Content-Language → null
curl -X POST http://localhost:8080/products \
     -H "Content-Type: application/json" \
     -d '{"name":"Drill","price":29.99}'
# lang=null name=Drill price=29.99
```

`entity.getHeaders()` gives all request headers as an `HttpHeaders` map. `getFirst(HttpHeaders.CONTENT_LANGUAGE)` returns `null` if absent — no 400, unlike `@RequestHeader` with `required=true`.

---

### Level 2 — Intermediate

Webhook endpoint that verifies an HMAC signature from the `X-Signature` header against the JSON body:

```java
// WebhookController.java
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.util.Base64;

@RestController
@RequestMapping("/webhooks")
public class WebhookController {

    private static final String SECRET = "webhook-secret-32bytes-long!!!!!";

    @PostMapping("/products")
    public ResponseEntity<String> receive(HttpEntity<String> entity) {
        String signature = entity.getHeaders().getFirst("X-Signature");
        String body = entity.getBody(); // raw JSON string

        if (!verifySignature(body, signature)) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body("Signature mismatch");
        }

        // Parse body as needed downstream
        return ResponseEntity.ok("Webhook accepted: " + body.length() + " bytes");
    }

    private boolean verifySignature(String body, String signature) {
        if (signature == null || body == null) return false;
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(SECRET.getBytes(), "HmacSHA256"));
            String expected = Base64.getEncoder().encodeToString(mac.doFinal(body.getBytes()));
            return MessageDigest.isEqual(expected.getBytes(), signature.getBytes());
        } catch (Exception e) {
            return false;
        }
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

BODY='{"event":"product.created","name":"Drill"}'
SECRET="webhook-secret-32bytes-long!!!!!"
SIG=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "$SECRET" -binary | base64)

curl -X POST http://localhost:8080/webhooks/products \
     -H "Content-Type: application/json" \
     -H "X-Signature: $SIG" \
     -d "$BODY"
# Webhook accepted: 42 bytes

# Tampered signature
curl -X POST http://localhost:8080/webhooks/products \
     -H "Content-Type: application/json" \
     -H "X-Signature: invalidsig" \
     -d "$BODY"
# 401 Signature mismatch
```

**What changed:** `HttpEntity<String>` receives the raw JSON body as a `String` — essential for HMAC verification, since parsing to an object first would re-serialize slightly differently and break the signature. Headers and body arrive together without two separate resolver calls.

---

### Level 3 — Advanced

A generic REST relay that forwards an incoming `RequestEntity` to an upstream service, inspecting the method and URI to build the outbound call:

```java
// RelayController.java
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import java.net.URI;

@RestController
@RequestMapping("/relay")
public class RelayController {

    private final RestTemplate rest = new RestTemplate();
    private static final String UPSTREAM = "https://api.internal/";

    @RequestMapping(value = "/**", method = {
            RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT,
            RequestMethod.DELETE, RequestMethod.PATCH})
    public ResponseEntity<String> relay(RequestEntity<String> incoming) {
        // Strip /relay prefix, keep the rest of the path
        String path = incoming.getUrl().getPath().replaceFirst("^/relay", "");
        String query = incoming.getUrl().getRawQuery();
        String target = UPSTREAM + path + (query != null ? "?" + query : "");

        // Forward headers (drop hop-by-hop)
        HttpHeaders forwardHeaders = new HttpHeaders();
        incoming.getHeaders().forEach((name, values) -> {
            String lower = name.toLowerCase();
            if (!lower.equals("host") && !lower.equals("connection")) {
                forwardHeaders.addAll(name, values);
            }
        });

        RequestEntity<String> outbound = new RequestEntity<>(
                incoming.getBody(),
                forwardHeaders,
                incoming.getMethod(),
                URI.create(target));

        try {
            return rest.exchange(outbound, String.class);
        } catch (org.springframework.web.client.HttpStatusCodeException ex) {
            return ResponseEntity.status(ex.getStatusCode())
                    .body(ex.getResponseBodyAsString());
        }
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# GET relayed to upstream (example using httpbin as upstream substitute)
curl "http://localhost:8080/relay/get?foo=bar"
# upstream response forwarded back

# POST relayed
curl -X POST http://localhost:8080/relay/post \
     -H "Content-Type: application/json" \
     -d '{"name":"Drill"}'
```

**What changed and why:**
- `RequestEntity<String>` exposes `getMethod()` and `getUrl()` — the relay uses both to reconstruct the upstream target URL and HTTP method without any explicit `@RequestMapping` method duplication.
- `HttpHeaders` forwarding with hop-by-hop filtering (`host`, `connection`) prevents proxy protocol errors.
- `rest.exchange(outbound, String.class)` accepts a `RequestEntity` directly — the same type from the incoming handler maps naturally to `RestTemplate`'s relay API.

<svg viewBox="0 0 700 160" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="160" fill="#0d1117"/>
  <rect x="10" y="50" width="140" height="60" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="70" text-anchor="middle" fill="#79c0ff">Client</text>
  <text x="80" y="88" text-anchor="middle" fill="#8b949e" font-size="10">POST /relay/orders</text>
  <text x="80" y="102" text-anchor="middle" fill="#8b949e" font-size="10">+ headers + body</text>
  <line x1="150" y1="80" x2="185" y2="80" stroke="#8b949e" marker-end="url(#arhe2)"/>

  <rect x="185" y="40" width="200" height="80" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="285" y="60" text-anchor="middle" fill="#6db33f">RelayController</text>
  <text x="285" y="78" text-anchor="middle" fill="#8b949e" font-size="10">RequestEntity: method=POST</text>
  <text x="285" y="92" text-anchor="middle" fill="#8b949e" font-size="10">url=/relay/orders</text>
  <text x="285" y="106" text-anchor="middle" fill="#8b949e" font-size="10">body + filtered headers</text>
  <line x1="385" y1="80" x2="420" y2="80" stroke="#8b949e" marker-end="url(#arhe2)"/>

  <rect x="420" y="50" width="200" height="60" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="520" y="70" text-anchor="middle" fill="#79c0ff">Upstream</text>
  <text x="520" y="88" text-anchor="middle" fill="#8b949e" font-size="10">POST api.internal/orders</text>
  <text x="520" y="102" text-anchor="middle" fill="#8b949e" font-size="10">+ forwarded headers + body</text>

  <text x="350" y="140" text-anchor="middle" fill="#8b949e" font-size="10">RequestEntity naturally maps to RestTemplate.exchange() — no reconstruction needed</text>
  <defs><marker id="arhe2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Per-request: `POST /relay/orders` via `RelayController`:**

1. `DispatcherServlet` routes to `relay(RequestEntity<String> incoming)`.
2. `HttpEntityMethodArgumentResolver` detects `RequestEntity<String>` parameter type.
3. Reads all request headers into `HttpHeaders`.
4. Selects `StringHttpMessageConverter` for `String` body type (reads raw body text).
5. Constructs `RequestEntity<String>` with headers, body, method=`POST`, url=`http://localhost:8080/relay/orders`.
6. Handler executes: strips `/relay` prefix → target = `https://api.internal/orders`.
7. Copies headers, drops `host` and `connection`.
8. Builds new `RequestEntity<String>` with upstream URI and filtered headers.
9. `rest.exchange(outbound, String.class)` sends to upstream.
10. Returns upstream `ResponseEntity<String>` directly to client.

**State at each layer:**

| Layer | Data |
|---|---|
| Incoming request | `POST /relay/orders`, headers, raw JSON body |
| `RequestEntity` parameter | method=POST, url=/relay/orders, headers, body (String) |
| Controller logic | new target URI, filtered headers |
| `RestTemplate.exchange` | outbound `RequestEntity` to upstream |
| Response | upstream response body + status forwarded |

---

## 7. Gotchas & takeaways

> **`HttpEntity` body is deserialized by `HttpMessageConverter` — same chain as `@RequestBody`.** Binding `HttpEntity<String>` reads the raw body as text; `HttpEntity<MyDto>` runs Jackson deserialization. The converter is chosen by `Content-Type` and the generic type argument.

> **`RequestEntity.getBody()` may return `null` for bodyless methods (GET, DELETE).** Check before calling methods on the body, or use `HttpEntity` only for endpoints that always have a body.

> **`HttpEntity` does not support `@Valid`.** Bean validation is not triggered on `HttpEntity` parameters. Validate the body manually after extracting it from `entity.getBody()`.

- `HttpEntity<T>` = headers + body without annotation — detected by type, not by annotation.
- `RequestEntity<T>` adds `getMethod()` and `getUrl()` — use for relay/proxy handlers.
- Body deserialized via same `HttpMessageConverter` chain as `@RequestBody`.
- Ideal for webhook signature verification (headers + raw body together), or generic relay handlers.
- Does not trigger `@Valid` — manual validation required.
