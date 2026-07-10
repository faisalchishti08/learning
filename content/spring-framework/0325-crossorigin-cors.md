---
card: spring-framework
gi: 325
slug: crossorigin-cors
title: "@CrossOrigin (CORS)"
---

## 1. What it is

`@CrossOrigin` is a Spring MVC annotation that enables Cross-Origin Resource Sharing (CORS) for a controller class or a single handler method. It tells the browser, via response headers, which other origins (scheme + host + port) are allowed to call this endpoint from client-side JavaScript. Without it, a browser blocks cross-origin `fetch`/`XMLHttpRequest` calls by default, even though the server would happily respond.

```java
@RestController
@RequestMapping("/api/products")
@CrossOrigin(origins = "https://shop.example.com")
public class ProductController {

    @GetMapping("/{id}")
    public Product get(@PathVariable long id) { ... }
}
```

## 2. Why & when

Browsers enforce the **same-origin policy**: a page served from `https://app.example.com` cannot script-call `https://api.example.com` unless the API explicitly allows it via CORS response headers. This matters constantly in modern web architectures where a frontend (React/Vue/Angular, often on its own domain or port during development) talks to a separately deployed backend API.

Use `@CrossOrigin` when:
- Your API is consumed by a browser-based frontend hosted on a different origin (different domain, subdomain, or port — `localhost:3000` calling `localhost:8080` counts as cross-origin).
- You need fine-grained control per controller or per endpoint (public read endpoints open to any origin, write endpoints restricted to a known frontend).
- You don't want to enable CORS globally for the whole application.

For application-wide CORS policy, a global `WebMvcConfigurer.addCorsMappings` bean is usually cleaner than annotating every controller — `@CrossOrigin` is best for exceptions or endpoint-specific rules.

## 3. Core concept

```
Browser same-origin policy blocks cross-origin script calls by default.
CORS is a set of response headers that opt back in.

Simple request (GET, POST with simple content-type):
  Browser --request (with Origin header)--> Server
  Server --response (with Access-Control-Allow-Origin)--> Browser
  Browser checks header, allows/blocks script access to response

Preflighted request (PUT/DELETE, custom headers, JSON content-type):
  Browser sends OPTIONS request FIRST (the "preflight"):
    OPTIONS /api/products/1
    Origin: https://shop.example.com
    Access-Control-Request-Method: DELETE
    Access-Control-Request-Headers: Authorization

  Server responds (handled automatically by Spring's CORS support):
    Access-Control-Allow-Origin: https://shop.example.com
    Access-Control-Allow-Methods: GET, POST, DELETE
    Access-Control-Allow-Headers: Authorization
    Access-Control-Max-Age: 3600

  Only if preflight succeeds does the browser send the real DELETE request.
```

`@CrossOrigin` configures the values Spring uses to answer both the preflight `OPTIONS` request and to stamp headers on the real response.

## 4. Diagram

<svg viewBox="0 0 720 260" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="260" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Cross-origin request from browser to API</text>

  <rect x="20" y="50" width="180" height="70" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="72" text-anchor="middle" fill="#79c0ff">Browser page</text>
  <text x="110" y="90" text-anchor="middle" fill="#8b949e" font-size="10">https://shop.example.com</text>

  <rect x="270" y="50" width="200" height="70" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="370" y="72" text-anchor="middle" fill="#6db33f">Spring API</text>
  <text x="370" y="90" text-anchor="middle" fill="#8b949e" font-size="10">https://api.example.com</text>

  <line x1="200" y1="70" x2="270" y2="70" stroke="#8b949e" marker-end="url(#a1)"/>
  <text x="235" y="63" text-anchor="middle" fill="#8b949e" font-size="9">1. OPTIONS preflight</text>

  <line x1="270" y1="100" x2="200" y2="100" stroke="#6db33f" marker-end="url(#a1)"/>
  <text x="235" y="115" text-anchor="middle" fill="#6db33f" font-size="9">2. Allow-Origin: shop.example.com</text>

  <line x1="110" y1="120" x2="110" y2="160" stroke="#79c0ff" marker-end="url(#a1)"/>
  <line x1="200" y1="180" x2="270" y2="180" stroke="#8b949e" marker-end="url(#a1)"/>
  <text x="235" y="173" text-anchor="middle" fill="#8b949e" font-size="9">3. real GET request</text>

  <rect x="20" y="160" width="180" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="110" y="184" text-anchor="middle" fill="#8b949e" font-size="10">browser allows script to read response</text>

  <line x1="270" y1="200" x2="200" y2="200" stroke="#6db33f" marker-end="url(#a1)"/>
  <text x="235" y="215" text-anchor="middle" fill="#6db33f" font-size="9">4. 200 OK + Allow-Origin header</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The browser sends a preflight `OPTIONS` request for "unsafe" methods; Spring answers it and stamps `Access-Control-Allow-Origin` on the real response.*

## 5. Runnable example

### Level 1 — Basic

A single endpoint opened to one trusted frontend origin:

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/products")
public class ProductController {

    record Product(long id, String name) {}

    @CrossOrigin(origins = "http://localhost:3000")
    @GetMapping("/{id}")
    public Product get(@PathVariable long id) {
        return new Product(id, "Drill");
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -H "Origin: http://localhost:3000" http://localhost:8080/api/products/1
# HTTP/1.1 200
# Access-Control-Allow-Origin: http://localhost:3000
# {"id":1,"name":"Drill"}

curl -i -H "Origin: http://evil.example.com" http://localhost:8080/api/products/1
# HTTP/1.1 200   (curl itself isn't blocked — a real browser would refuse to expose the body to JS
#                 because Access-Control-Allow-Origin doesn't match evil.example.com)
```

The endpoint itself still runs for any origin — CORS is enforced by the *browser*, not the server. The server only decides which `Access-Control-Allow-Origin` value to send back, and the browser uses that to decide whether to let the calling script see the response.

### Level 2 — Intermediate

Class-level defaults with per-method overrides, multiple origins, and credentials (cookies) support:

```java
// ProductController.java (extended)
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/products")
@CrossOrigin(
    origins = {"https://shop.example.com", "https://admin.example.com"},
    allowCredentials = "true",           // allow cookies/auth headers cross-origin
    maxAge = 3600                        // cache preflight result for 1 hour
)
public class ProductController {

    record Product(long id, String name, double price) {}

    @GetMapping("/{id}")                 // inherits class-level CORS config
    public Product get(@PathVariable long id) {
        return new Product(id, "Drill", 29.99);
    }

    // Public catalog read — override to allow ANY origin, no credentials
    @CrossOrigin(origins = "*", allowCredentials = "false")
    @GetMapping
    public Product[] list() {
        return new Product[]{ new Product(1, "Drill", 29.99) };
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -H "Origin: https://shop.example.com" http://localhost:8080/api/products/1
# Access-Control-Allow-Origin: https://shop.example.com
# Access-Control-Allow-Credentials: true

curl -i -H "Origin: https://random-site.com" http://localhost:8080/api/products
# Access-Control-Allow-Origin: *   (public list endpoint allows all)
```

**What changed:** `get()` inherits the restrictive class-level policy (two named origins, credentials allowed). `list()` overrides with a wide-open policy for a public, cookie-free endpoint. `allowCredentials = "true"` cannot be combined with `origins = "*"` per the CORS spec — Spring rejects that combination at startup, which is why the public endpoint explicitly disables credentials.

### Level 3 — Advanced

Production setup: CORS driven by externalized configuration (so allowed origins differ per environment) using a global `CorsConfigurationSource` bean instead of scattering `@CrossOrigin` everywhere, plus a preflight-aware security filter chain:

```java
// CorsConfig.java
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.List;

@Configuration
public class CorsConfig {

    @Value("${app.cors.allowed-origins}")   // e.g. from application-prod.yml
    private List<String> allowedOrigins;

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(allowedOrigins);
        config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
        config.setAllowedHeaders(List.of("Authorization", "Content-Type"));
        config.setAllowCredentials(true);
        config.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/api/**", config);   // applies to all /api/* endpoints
        return source;
    }
}
```

`application-prod.yml`:
```yaml
app:
  cors:
    allowed-origins:
      - https://shop.example.com
      - https://admin.example.com
```

`application-dev.yml`:
```yaml
app:
  cors:
    allowed-origins:
      - http://localhost:3000
```

**How to run:**
```bash
./mvnw spring-boot:run -Dspring-boot.run.profiles=dev

curl -i -X OPTIONS http://localhost:8080/api/products \
     -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type,Authorization"
# HTTP/1.1 200
# Access-Control-Allow-Origin: http://localhost:3000
# Access-Control-Allow-Methods: GET,POST,PUT,DELETE
# Access-Control-Allow-Headers: Authorization,Content-Type
# Access-Control-Max-Age: 3600
```

**What changed and why:**
- A single `CorsConfigurationSource` bean applies to every path matching `/api/**` — no need for `@CrossOrigin` on each controller. This centralizes the policy and makes it easy to audit.
- Allowed origins come from environment-specific config, so `dev` opens `localhost:3000` while `prod` restricts to the real frontend domains — the same code deploys everywhere without hardcoding origins.
- `registerCorsConfiguration` is picked up automatically by Spring's `CorsFilter` (or by Spring Security's CORS integration if Spring Security is on the classpath), so it runs before both MVC dispatch and security filters — critical because a preflight `OPTIONS` request carries no auth headers and would otherwise be rejected by a security filter before CORS headers are even added.

## 6. Walkthrough

**Request: browser JS on `http://localhost:3000` calls `POST /api/products` with a JSON body (Level 3 config).**

1. Because the request has `Content-Type: application/json` (not a "simple" content type) and method `POST` combined with a custom header, the browser first sends a **preflight**:
   ```
   OPTIONS /api/products HTTP/1.1
   Origin: http://localhost:3000
   Access-Control-Request-Method: POST
   Access-Control-Request-Headers: Content-Type,Authorization
   ```
2. Spring's `CorsFilter` intercepts the `OPTIONS` request before it reaches any controller or (if present) security filter that would otherwise reject an unauthenticated `OPTIONS` call.
3. The filter looks up the registered `CorsConfiguration` for path `/api/products` — finds the `/api/**` mapping — and checks: is `http://localhost:3000` in `allowedOrigins`? Yes (dev profile). Is `POST` in `allowedMethods`? Yes. Are `Content-Type` and `Authorization` in `allowedHeaders`? Yes.
4. Filter short-circuits with a `200 OK` and CORS response headers — the request never reaches `DispatcherServlet` or the controller:
   ```
   HTTP/1.1 200 OK
   Access-Control-Allow-Origin: http://localhost:3000
   Access-Control-Allow-Methods: GET,POST,PUT,DELETE
   Access-Control-Allow-Headers: Content-Type,Authorization
   Access-Control-Max-Age: 3600
   ```
5. Browser caches this result for `3600` seconds (per `Access-Control-Max-Age`) and sends the real request:
   ```
   POST /api/products HTTP/1.1
   Origin: http://localhost:3000
   Content-Type: application/json

   {"name":"Hammer","price":14.99}
   ```
6. This time the `CorsFilter` adds `Access-Control-Allow-Origin` to the response but lets the request continue to `DispatcherServlet` → controller → normal handling.
7. Controller returns the created `Product`; the response carries both the JSON body and the CORS header:
   ```
   HTTP/1.1 201 Created
   Access-Control-Allow-Origin: http://localhost:3000
   Content-Type: application/json

   {"id":2,"name":"Hammer","price":14.99}
   ```
8. Browser sees a matching `Access-Control-Allow-Origin` and exposes the response body to the calling JavaScript `fetch()` promise.

## 7. Gotchas & takeaways

> **CORS is enforced by the browser, not the server.** Tools like `curl` or Postman ignore `Access-Control-Allow-Origin` entirely and will show you the response regardless. Never mistake "curl can reach my API from anywhere" for "my API is CORS-protected" — it isn't protection at all, it's a browser-side opt-in for scripts.

> **`allowCredentials = true` cannot be paired with `origins = "*"`.** The CORS spec forbids wildcard origins when credentials (cookies, `Authorization` headers) are allowed, because that would let any site make authenticated requests on a logged-in user's behalf. Spring throws a startup or runtime error if you try — list explicit origins instead.

> **A missing preflight response looks like a mysterious network error in the browser console**, not a clear 403. If a security filter chain rejects the `OPTIONS` preflight (e.g. because it requires authentication), the browser reports a generic CORS failure with no useful detail — always verify the `CorsFilter` runs *before* authentication filters.

- `@CrossOrigin` on a method overrides (not merges with) the class-level configuration for that method.
- Preflight requests are triggered by non-"simple" methods (`PUT`, `DELETE`, `PATCH`), custom headers, or non-simple content types like `application/json`.
- For app-wide policy, prefer one `CorsConfigurationSource` or `WebMvcConfigurer.addCorsMappings` bean over annotating every controller.
- `maxAge` reduces preflight traffic by letting the browser cache the OPTIONS result — tune it based on how often the policy changes.
