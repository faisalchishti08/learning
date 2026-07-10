---
card: spring-framework
gi: 359
slug: cors-config-global
title: "CORS config (global)"
---

## 1. What it is

Global CORS configuration is the `WebMvcConfigurer.addCorsMappings(CorsRegistry)` override that defines Cross-Origin Resource Sharing policy for the entire application (or broad URL patterns within it) in one central place, rather than scattering `@CrossOrigin` annotations across individual controllers. It's the recommended approach whenever a consistent CORS policy applies to most or all of an application's API surface.

```java
@Override
public void addCorsMappings(CorsRegistry registry) {
    registry.addMapping("/api/**")
        .allowedOrigins("https://app.example.com")
        .allowedMethods("GET", "POST", "PUT", "DELETE")
        .allowCredentials(true);
}
```

## 2. Why & when

The earlier `@CrossOrigin` card covered per-controller/per-method CORS configuration — appropriate for exceptions to a general policy. `addCorsMappings` is the right tool when:

- The **entire API** (or a large, consistent portion of it, like everything under `/api/**`) shares the same CORS policy — declaring it once avoids repeating `@CrossOrigin` on every controller.
- You want the policy centrally visible and auditable in one configuration class, rather than needing to check every controller individually to understand the application's full CORS surface.
- You need environment-specific origins (different allowed origins for dev/staging/prod) driven by externalized configuration, which is easier to manage in one `WebMvcConfigurer` bean than across scattered annotations.

`@CrossOrigin` and `addCorsMappings` can coexist — a method-level `@CrossOrigin` overrides the global mapping for that specific endpoint, exactly like the local-vs-global pattern seen in the `@ControllerAdvice` card for exception handling.

## 3. Core concept

```
CorsRegistry.addMapping(pattern) returns a CorsRegistration,
configured with the SAME semantics as @CrossOrigin's attributes:

  registry.addMapping("/api/**")
      .allowedOrigins("https://app.example.com")
      .allowedMethods("GET", "POST")
      .allowedHeaders("Authorization", "Content-Type")
      .allowCredentials(true)
      .maxAge(3600)

Multiple mappings can be registered for different URL patterns
with DIFFERENT policies:

  registry.addMapping("/api/public/**")
      .allowedOrigins("*")               <- open, no credentials

  registry.addMapping("/api/admin/**")
      .allowedOrigins("https://admin.example.com")
      .allowCredentials(true)             <- restricted, credentials allowed

Resolution for a given request: the MOST SPECIFIC matching
pattern's CorsConfiguration applies (same general principle as
other Ant/Path-pattern-based Spring MVC matching).
```

## 4. Diagram

<svg viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="210" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">One CorsRegistry, multiple pattern-scoped policies</text>

  <rect x="20" y="50" width="320" height="60" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="180" y="72" text-anchor="middle" fill="#6db33f" font-size="10">/api/public/**</text>
  <text x="180" y="90" text-anchor="middle" fill="#8b949e" font-size="9">allowedOrigins("*"), no credentials</text>

  <rect x="380" y="50" width="320" height="60" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="540" y="72" text-anchor="middle" fill="#79c0ff" font-size="10">/api/admin/**</text>
  <text x="540" y="90" text-anchor="middle" fill="#8b949e" font-size="9">restricted origin, credentials allowed</text>

  <rect x="200" y="140" width="320" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="360" y="170" text-anchor="middle" fill="#8b949e" font-size="10">one CorsRegistry bean, all policies visible together</text>

  <line x1="180" y1="110" x2="300" y2="140" stroke="#8b949e" marker-end="url(#a35)"/>
  <line x1="540" y1="110" x2="420" y2="140" stroke="#8b949e" marker-end="url(#a35)"/>

  <defs>
    <marker id="a35" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Multiple pattern-scoped policies live together in one place, easier to audit than annotations spread across many controllers.*

## 5. Runnable example

### Level 1 — Basic

A single, application-wide CORS policy for everything under `/api/**`:

```java
// WebConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("http://localhost:3000")
            .allowedMethods("GET", "POST", "PUT", "DELETE");
    }
}
```

```java
// ProductController.java — NO @CrossOrigin needed anywhere
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/products")
public class ProductController {

    @GetMapping("/{id}")
    public String get(@PathVariable long id) { return "Drill"; }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -H "Origin: http://localhost:3000" http://localhost:8080/api/products/1
# Access-Control-Allow-Origin: http://localhost:3000

curl -i -H "Origin: http://evil.example.com" http://localhost:8080/api/products/1
# no Access-Control-Allow-Origin header — a real browser would block script access to this response
```

Every controller under `/api/**` inherits this single, centrally declared CORS policy — no `@CrossOrigin` annotation exists anywhere in the codebase, yet CORS is fully and correctly configured.

### Level 2 — Intermediate

Different policies for different API areas — a wide-open public section and a credential-requiring admin section:

```java
// WebConfig.java (extended)
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/public/**")
            .allowedOrigins("*")
            .allowedMethods("GET");

        registry.addMapping("/api/admin/**")
            .allowedOrigins("https://admin.example.com")
            .allowedMethods("GET", "POST", "PUT", "DELETE")
            .allowCredentials(true)
            .maxAge(3600);
    }
}
```

```java
// ProductController.java (extended)
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    @GetMapping("/api/public/products")
    public String publicList() { return "[]"; }

    @GetMapping("/api/admin/products")
    public String adminList() { return "[]"; }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -H "Origin: https://random-site.com" http://localhost:8080/api/public/products
# Access-Control-Allow-Origin: *

curl -i -H "Origin: https://random-site.com" http://localhost:8080/api/admin/products
# no Access-Control-Allow-Origin — random-site.com is NOT in the admin mapping's allowed origins

curl -i -H "Origin: https://admin.example.com" http://localhost:8080/api/admin/products
# Access-Control-Allow-Origin: https://admin.example.com
# Access-Control-Allow-Credentials: true
```

**What changed:** Two separate `addMapping` calls define entirely independent policies for two different URL sub-trees — the public endpoints are wide open (any origin, no credentials), while admin endpoints are tightly restricted to one specific, trusted origin with credentials allowed. Both policies are visible together in one place, making the application's full CORS posture auditable at a glance.

### Level 3 — Advanced

Production pattern: environment-specific allowed origins driven by externalized configuration, avoiding hardcoded origins that would need a code change (and redeploy) to update — critical for supporting different frontend domains across dev/staging/production without maintaining separate builds:

```java
// WebConfig.java (production version)
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.util.List;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Value("#{'${app.cors.allowed-origins}'.split(',')}")
    private List<String> allowedOrigins;

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins(allowedOrigins.toArray(new String[0]))
            .allowedMethods("GET", "POST", "PUT", "DELETE")
            .allowedHeaders("Authorization", "Content-Type")
            .allowCredentials(true)
            .maxAge(3600);
    }
}
```

`application-dev.yml`:
```yaml
app:
  cors:
    allowed-origins: http://localhost:3000,http://localhost:5173
```

`application-prod.yml`:
```yaml
app:
  cors:
    allowed-origins: https://app.example.com,https://admin.example.com
```

```java
// ProductController.java — UNCHANGED, no per-controller CORS code at all
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/products")
public class ProductController {
    @GetMapping("/{id}")
    public String get(@PathVariable long id) { return "Drill"; }
}
```

**How to run:**
```bash
./mvnw spring-boot:run -Dspring-boot.run.profiles=dev

curl -i -H "Origin: http://localhost:3000" http://localhost:8080/api/products/1
# Access-Control-Allow-Origin: http://localhost:3000    <- allowed under the DEV profile

./mvnw spring-boot:run -Dspring-boot.run.profiles=prod

curl -i -H "Origin: http://localhost:3000" http://localhost:8080/api/products/1
# no Access-Control-Allow-Origin — localhost is correctly rejected under the PROD profile
```

**What changed and why:**
- `@Value` with Spring Expression Language (`#{'...'.split(',')}`) reads a comma-separated list of origins from externalized configuration, so the exact same compiled application deploys correctly across environments — only the properties file (or environment variable) differs, never the code.
- This eliminates a dangerous class of mistake: hardcoding `http://localhost:3000` as an allowed origin and accidentally shipping that to production, which would leave a production API permanently accepting cross-origin requests from any developer's local machine.
- Because this is a single, centralized `addCorsMappings` override, updating the allowed-origins list for a new frontend domain is a one-line configuration change, not a hunt through the codebase for scattered `@CrossOrigin` annotations that might also need updating.

## 6. Walkthrough

**Request: browser JavaScript on `https://app.example.com` sends `GET /api/products/1` (Level 3 code, prod profile active).**

1. Because this is a "simple" `GET` request with no custom headers, the browser does **not** send a preflight `OPTIONS` request first — it sends the actual request directly, with an `Origin: https://app.example.com` header attached automatically by the browser.
2. Spring's `CorsFilter` (registered automatically because `addCorsMappings` configuration exists) intercepts the request before it reaches `DispatcherServlet`'s normal handler dispatch.
3. The filter looks up the registered `CorsConfiguration` for the request path `/api/products/1` — matches the `/api/**` pattern from `addCorsMappings`.
4. It checks: is `https://app.example.com` in the configured `allowedOrigins` (loaded from `application-prod.yml`, which lists `https://app.example.com,https://admin.example.com`)? Yes.
5. The filter adds `Access-Control-Allow-Origin: https://app.example.com` (and `Access-Control-Allow-Credentials: true`, since `allowCredentials(true)` was configured) to the response, then lets the request continue normally to `DispatcherServlet`.
6. `DispatcherServlet` routes to `ProductController.get(1)` as usual, returns `"Drill"`.
7. Response:
   ```
   HTTP/1.1 200 OK
   Access-Control-Allow-Origin: https://app.example.com
   Access-Control-Allow-Credentials: true
   Content-Type: text/plain

   Drill
   ```
8. The browser sees a matching `Access-Control-Allow-Origin` value and exposes the response to the calling JavaScript.

**Same request, but the browser is at `http://localhost:3000` (a dev-only origin, prod profile active).**

1–3. Identical up through pattern matching.
4. The filter checks: is `http://localhost:3000` in `allowedOrigins` (the *prod* list — `https://app.example.com,https://admin.example.com`)? **No.**
5. The filter does not add an `Access-Control-Allow-Origin` header at all. The underlying request still proceeds to `DispatcherServlet` (CORS restrictions are enforced by the browser reading response headers, not by the server refusing to process the request — recall the earlier `@CrossOrigin` card's gotcha about this), and `ProductController.get(1)` still executes normally.
6. Response is sent with a `200` status and the correct body, but **without** the `Access-Control-Allow-Origin` header:
   ```
   HTTP/1.1 200 OK
   Content-Type: text/plain

   Drill
   ```
7. The browser receives this response but, seeing no matching (or no) `Access-Control-Allow-Origin` header, refuses to expose the response body to the calling JavaScript — the network request technically succeeded, but the script's `fetch()` promise rejects with a CORS error.

## 7. Gotchas & takeaways

> **`addCorsMappings` and per-method `@CrossOrigin` can both apply to the same application — the more specific one (a method-level `@CrossOrigin`) overrides the global mapping for that specific endpoint**, exactly like local vs. global exception handler precedence. Mixing both without a clear convention can make it hard to determine the *actual* effective policy for a given endpoint without checking both the controller and the global configuration.

> **A CORS policy check happens on the server, but the actual access decision is enforced entirely by the browser** — the server "denying" a CORS request just means omitting the `Access-Control-Allow-Origin` header; the underlying request is still processed and can still have side effects (like a `POST` that writes to a database) even though the browser will hide the *response* from the calling script. Never rely on CORS configuration as your only defense against unauthorized cross-origin actions — pair it with proper authentication/authorization.

> **Reloading `allowedOrigins` from configuration at `@Value` injection time means changing the property requires an application restart** — this is not a hot-reloadable setting by default. For a system needing runtime-configurable CORS origins without a restart, a custom `CorsConfigurationSource` bean reading from a database or config service (refreshed periodically) would be needed instead of the simple `@Value` approach shown here.

- `addCorsMappings` centralizes CORS policy for broad URL patterns in one place — preferred over scattering `@CrossOrigin` when a consistent policy applies across most of an API.
- Multiple `addMapping` calls can define independent policies for different URL sub-trees within the same application.
- Externalize allowed origins via application properties/profiles so the same compiled application deploys safely and correctly across dev/staging/production without code changes.
- CORS is enforced by the browser reading response headers — the underlying request still reaches and can be processed by the server regardless of the CORS outcome, so it is not a substitute for real authentication/authorization.
