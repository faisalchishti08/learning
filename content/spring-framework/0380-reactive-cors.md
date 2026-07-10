---
card: spring-framework
gi: 380
slug: reactive-cors
title: "Reactive CORS"
---

## 1. What it is

Reactive CORS is Spring WebFlux's Cross-Origin Resource Sharing support — functionally equivalent to Spring MVC's CORS handling (both the `@CrossOrigin` annotation and global `addCorsMappings` configuration), but implemented via `CorsWebFilter` (a `WebFilter`, per the WebHandler API card) instead of a Servlet `Filter`, since WebFlux has no Servlet API to build on.

```java
@Bean
public CorsWebFilter corsWebFilter() {
    CorsConfiguration config = new CorsConfiguration();
    config.setAllowedOrigins(List.of("https://app.example.com"));
    config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));

    UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/api/**", config);
    return new CorsWebFilter(source);
}
```

## 2. Why & when

The underlying CORS *concepts* — preflight requests, `Access-Control-Allow-Origin`, credentials handling, the browser-enforced-not-server-enforced nature of the whole mechanism — are identical regardless of which Spring web framework is in play (see the Spring MVC CORS cards for the full conceptual treatment). What differs in WebFlux is purely the *configuration mechanism*: `@CrossOrigin` still works on `@RestController` methods exactly as in MVC, but the global configuration approach uses `CorsWebFilter` with a `CorsConfigurationSource`, registered as a Spring bean, rather than a `WebMvcConfigurer.addCorsMappings` override (which doesn't exist in WebFlux, since `WebMvcConfigurer` is MVC-specific).

Use `CorsWebFilter` when you want a single, centrally-configured CORS policy applied broadly across a WebFlux application's routes — the direct reactive equivalent of the `addCorsMappings`-based approach from the Spring MVC section.

## 3. Core concept

```
Spring MVC                              Spring WebFlux
──────────────────────────────────────────────────────────────
@CrossOrigin (per-controller/method)     @CrossOrigin — SAME annotation, works identically

addCorsMappings(CorsRegistry)             CorsWebFilter bean, backed by a
 (WebMvcConfigurer override)               CorsConfigurationSource

Internally: registers a CorsFilter        Internally: registers a CorsWebFilter
 (a javax.servlet.Filter)                  (a WebFilter, per the WebHandler API card)

CorsConfiguration itself (allowedOrigins, allowedMethods,
 allowCredentials, maxAge, etc.) — the SAME class, SAME
 fields, used identically by BOTH frameworks

UrlBasedCorsConfigurationSource — ALSO the same class,
 mapping URL patterns to CorsConfiguration objects,
 shared between BOTH frameworks
```

The `CorsConfiguration`/`CorsConfigurationSource` classes are genuinely shared infrastructure between Spring MVC and WebFlux — only the *filter* wrapping them differs (`CorsFilter` for Servlet-based MVC, `CorsWebFilter` for WebFlux).

## 4. Diagram

<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="200" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Shared CorsConfiguration, different filter wrapper per framework</text>

  <rect x="220" y="40" width="280" height="50" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="360" y="70" text-anchor="middle" fill="#e6edf3" font-size="11">CorsConfiguration (SHARED)</text>

  <line x1="300" y1="90" x2="180" y2="140" stroke="#8b949e" marker-end="url(#a56)"/>
  <line x1="420" y1="90" x2="540" y2="140" stroke="#8b949e" marker-end="url(#a56)"/>

  <rect x="60" y="140" width="240" height="40" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="180" y="165" text-anchor="middle" fill="#79c0ff" font-size="10">CorsFilter (Spring MVC)</text>

  <rect x="420" y="140" width="240" height="40" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="540" y="165" text-anchor="middle" fill="#6db33f" font-size="10">CorsWebFilter (WebFlux)</text>

  <defs>
    <marker id="a56" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The same `CorsConfiguration`/`CorsConfigurationSource` classes back both frameworks' CORS enforcement — only the filter type differs.*

## 5. Runnable example

### Level 1 — Basic

A single application-wide CORS policy for a WebFlux API, using `CorsWebFilter`:

```java
// CorsConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.reactive.CorsConfigurationSource;
import org.springframework.web.cors.reactive.CorsWebFilter;
import org.springframework.web.cors.reactive.UrlBasedCorsConfigurationSource;

import java.util.List;

@Configuration
public class CorsConfig {

    @Bean
    public CorsWebFilter corsWebFilter() {
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(List.of("http://localhost:3000"));
        config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/api/**", config);
        return new CorsWebFilter(source);
    }
}
```

```java
// ProductController.java — no @CrossOrigin needed anywhere
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {

    @GetMapping("/api/products/{id}")
    public Mono<String> get(@PathVariable long id) {
        return Mono.just("Drill");
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -H "Origin: http://localhost:3000" http://localhost:8080/api/products/1
# Access-Control-Allow-Origin: http://localhost:3000

curl -i -H "Origin: http://evil.example.com" http://localhost:8080/api/products/1
# no Access-Control-Allow-Origin header
```

Note the import package: `org.springframework.web.cors.reactive.*` for `CorsWebFilter`/`CorsConfigurationSource`/`UrlBasedCorsConfigurationSource`, distinct from the (non-reactive) `org.springframework.web.cors.*` package used in Spring MVC — the `CorsConfiguration` class itself, however, is shared and imported from the common, non-reactive-specific package in both frameworks.

### Level 2 — Intermediate

Multiple pattern-scoped policies, directly mirroring the Spring MVC global CORS card's equivalent example:

```java
// CorsConfig.java (extended)
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.reactive.CorsWebFilter;
import org.springframework.web.cors.reactive.UrlBasedCorsConfigurationSource;

import java.util.List;

@Configuration
public class CorsConfig {

    @Bean
    public CorsWebFilter corsWebFilter() {
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();

        CorsConfiguration publicConfig = new CorsConfiguration();
        publicConfig.setAllowedOrigins(List.of("*"));
        publicConfig.setAllowedMethods(List.of("GET"));
        source.registerCorsConfiguration("/api/public/**", publicConfig);

        CorsConfiguration adminConfig = new CorsConfiguration();
        adminConfig.setAllowedOrigins(List.of("https://admin.example.com"));
        adminConfig.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
        adminConfig.setAllowCredentials(true);
        source.registerCorsConfiguration("/api/admin/**", adminConfig);

        return new CorsWebFilter(source);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -H "Origin: https://random-site.com" http://localhost:8080/api/public/products
# Access-Control-Allow-Origin: *

curl -i -H "Origin: https://random-site.com" http://localhost:8080/api/admin/products
# no Access-Control-Allow-Origin — random-site.com not in the admin config's allowed origins

curl -i -H "Origin: https://admin.example.com" http://localhost:8080/api/admin/products
# Access-Control-Allow-Origin: https://admin.example.com
# Access-Control-Allow-Credentials: true
```

**What changed:** This is structurally identical to the Spring MVC global CORS card's multi-pattern example — `registerCorsConfiguration` accepts multiple pattern-to-`CorsConfiguration` registrations on the same source object, resolved by most-specific-match at request time, entirely independent of which web framework ultimately enforces them.

### Level 3 — Advanced

Production pattern: externalized, environment-specific allowed origins (mirroring the Spring MVC card's equivalent production pattern) combined with `@CrossOrigin` on a specific method for a documented, deliberate exception to the global policy — demonstrating that both mechanisms coexist correctly in WebFlux exactly as they do in MVC:

```java
// CorsConfig.java (production version)
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.reactive.CorsWebFilter;
import org.springframework.web.cors.reactive.UrlBasedCorsConfigurationSource;

import java.util.List;

@Configuration
public class CorsConfig {

    @Value("#{'${app.cors.allowed-origins}'.split(',')}")
    private List<String> allowedOrigins;

    @Bean
    public CorsWebFilter corsWebFilter() {
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(allowedOrigins);
        config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
        config.setAllowedHeaders(List.of("Authorization", "Content-Type"));
        config.setAllowCredentials(true);
        config.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/api/**", config);
        return new CorsWebFilter(source);
    }
}
```

```java
// ProductController.java (production version) — @CrossOrigin overrides the global filter for ONE endpoint
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {

    @GetMapping("/api/products/{id}")
    public Mono<String> get(@PathVariable long id) {
        return Mono.just("Drill");
    }

    // Public read-only endpoint, deliberately opened wider than the global policy —
    // @CrossOrigin works IDENTICALLY in WebFlux as it does in Spring MVC.
    @CrossOrigin(origins = "*")
    @GetMapping("/api/products/{id}/public-summary")
    public Mono<String> publicSummary(@PathVariable long id) {
        return Mono.just("Drill - starting at $29.99");
    }
}
```

`application-dev.yml`:
```yaml
app:
  cors:
    allowed-origins: http://localhost:3000
```

`application-prod.yml`:
```yaml
app:
  cors:
    allowed-origins: https://app.example.com
```

**How to run:**
```bash
./mvnw spring-boot:run -Dspring-boot.run.profiles=prod

curl -i -H "Origin: http://localhost:3000" http://localhost:8080/api/products/1
# no Access-Control-Allow-Origin — rejected under prod profile's restricted origin list

curl -i -H "Origin: http://localhost:3000" http://localhost:8080/api/products/1/public-summary
# Access-Control-Allow-Origin: *      <- @CrossOrigin's wider policy applies for THIS endpoint
```

**What changed and why:**
- Externalizing `allowedOrigins` via `@Value` and profile-specific YAML files works identically to the Spring MVC pattern — the environment-driven configuration approach is a Spring-wide idiom, not framework-specific.
- `@CrossOrigin(origins = "*")` on `publicSummary` demonstrates that method-level annotation-based CORS configuration and the global `CorsWebFilter` policy coexist correctly in WebFlux, with the more specific, method-level annotation taking precedence for that endpoint — exactly mirroring the local-overrides-global precedence pattern established in the Spring MVC CORS cards.
- This confirms a practically important point for teams migrating from Spring MVC to WebFlux: virtually all CORS *design decisions* (which endpoints need wider/narrower policies, where to draw the public/private line) transfer directly; only the underlying *implementation mechanism* (`CorsWebFilter`/`CorsConfigurationSource` instead of `CorsFilter`/`WebMvcConfigurer`) needs adjustment.

## 6. Walkthrough

**Request: browser JavaScript on `https://app.example.com` sends `GET /api/products/1` (Level 3 code, prod profile).**

1. WebFlux's `WebFilter` chain (per the WebHandler API card) processes this request before it reaches `DispatcherHandler`. `CorsWebFilter`, registered as a Spring bean, participates in this chain like any other `WebFilter`.
2. Inside `CorsWebFilter.filter(exchange, chain)` (implemented internally by Spring, following the same `WebFilter` contract covered in the earlier card): it consults its configured `CorsConfigurationSource`, looking up the `CorsConfiguration` registered for the request's path, `/api/products/1` — matches the `/api/**` pattern.
3. It checks: is `https://app.example.com` (the request's `Origin` header value) present in the configured `allowedOrigins` (loaded from `application-prod.yml`)? Yes.
4. `CorsWebFilter` adds `Access-Control-Allow-Origin: https://app.example.com` (and `Access-Control-Allow-Credentials: true`, since `allowCredentials(true)` was configured) to the exchange's response, then calls `chain.filter(exchange)` to continue processing — allowing the request to proceed normally toward `DispatcherHandler` and ultimately `ProductController.get(1)`.
5. `get(1)` executes, returning `Mono.just("Drill")`. This resolves and is written as the response body.
6. Final response, combining the CORS headers set by the filter (step 4) with the body produced by the controller (step 5):
   ```
   HTTP/1.1 200 OK
   Access-Control-Allow-Origin: https://app.example.com
   Access-Control-Allow-Credentials: true
   Content-Type: text/plain

   Drill
   ```

**Request from `http://localhost:3000` against the same endpoint (rejected under the prod-configured origin list).**

1–2. Identical filter processing up through the origin lookup.
3. `allowedOrigins` (loaded from `application-prod.yml`) is `["https://app.example.com"]` — `http://localhost:3000` is not present.
4. `CorsWebFilter` does not add an `Access-Control-Allow-Origin` header. It still calls `chain.filter(exchange)`, allowing the underlying request to proceed and `get(1)` to execute normally — exactly as established in the Spring MVC CORS card, the *server* still processes the request; only the *browser*, upon seeing no matching CORS header in the response, will refuse to expose the response body to the calling JavaScript.
5. Response is sent with a `200` status and the correct body, but without the CORS header — the browser-side `fetch()` call would reject with a CORS error, even though the server-side request handling completed successfully.

## 7. Gotchas & takeaways

> **The import packages differ between frameworks even though the core `CorsConfiguration` class is shared** — `CorsWebFilter`/`CorsConfigurationSource`/`UrlBasedCorsConfigurationSource` for WebFlux come from `org.springframework.web.cors.reactive.*`, while Spring MVC's equivalents come from `org.springframework.web.cors.*` (non-reactive package) and `org.springframework.web.filter.CorsFilter`. Importing the wrong package for your framework is a common copy-paste mistake when consulting mixed MVC/WebFlux documentation or examples.

> **`CorsWebFilter` must be registered as a genuine Spring bean** (as shown in every example here) for Spring Boot's autoconfiguration to pick it up and wire it into the `WebFilter` chain correctly — simply instantiating a `CorsWebFilter` object without exposing it via `@Bean` has no effect.

> **CORS remains a browser-enforced, not server-enforced, mechanism regardless of framework** — this fundamental characteristic (covered in depth in the Spring MVC `@CrossOrigin` card) applies identically in WebFlux; `curl` and other non-browser HTTP clients ignore CORS headers entirely, so testing with `curl` only verifies the *headers* are correct, not that browser-side enforcement will behave as expected.

- Reactive CORS uses `CorsWebFilter` (a `WebFilter`) instead of Spring MVC's Servlet-based `CorsFilter`, but shares the identical `CorsConfiguration`/`CorsConfigurationSource` classes underneath.
- `@CrossOrigin` works identically on WebFlux `@RestController` methods as it does in Spring MVC, taking precedence over the global `CorsWebFilter` policy for that specific endpoint.
- Externalizing allowed origins via profile-specific configuration remains the same best practice in WebFlux as in Spring MVC — no framework-specific difference in this design decision.
- Watch for the different import package (`org.springframework.web.cors.reactive.*`) required for WebFlux's CORS classes compared to Spring MVC's non-reactive equivalents.
