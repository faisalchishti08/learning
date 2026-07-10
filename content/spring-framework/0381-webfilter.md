---
card: spring-framework
gi: 381
slug: webfilter
title: "WebFilter"
---

## 1. What it is

`WebFilter` is WebFlux's general-purpose interface for cross-cutting request/response logic — introduced conceptually in the `WebHandler` API card, this card focuses specifically on `WebFilter` as a topic in its own right: how filters are discovered and ordered, the built-in `WebFilter` implementations Spring provides out of the box, and how `WebFilter` relates to the narrower `HandlerFilterFunction` used specifically within functional endpoints.

```java
@Component
@Order(1)
public class MyWebFilter implements WebFilter {
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        // logic BEFORE the rest of the chain
        return chain.filter(exchange)
            .then(Mono.fromRunnable(() -> { /* logic AFTER */ }));
    }
}
```

## 2. Why & when

Any `WebFilter` bean registered in the application context is automatically discovered by Spring Boot's WebFlux autoconfiguration and inserted into the filter chain — no manual registration step (unlike Spring MVC's `FilterRegistrationBean`, which explicitly controls Servlet filter registration and URL patterns) is strictly required, though `@Order` (or implementing `Ordered`) controls execution sequence when multiple filters are present. Use `WebFilter` for concerns that must apply broadly, early, and before `DispatcherHandler`'s own handler-resolution logic runs — authentication checks, request/response logging, header manipulation, and (as the previous card showed) CORS enforcement, which Spring itself implements as a built-in `WebFilter`.

## 3. Core concept

```
WebFilter discovery and ordering:

  ANY @Component/@Bean implementing WebFilter is AUTO-DISCOVERED
  by WebFlux autoconfiguration — added to the chain automatically

  Ordering (when multiple WebFilters exist):
    @Order(n) annotation, OR
    implements Ordered { int getOrder() { return n; } }
    LOWER values run FIRST (same convention as Spring MVC interceptors)

Built-in WebFilters Spring itself registers (when relevant config exists):

  CorsWebFilter              — CORS enforcement (previous card)
  HiddenHttpMethodFilter (reactive) — form _method override, same as MVC's
  ForwardedHeaderFilter (via ForwardedHeaderTransformer) — X-Forwarded-* handling
  ServerHttpObservationFilter — metrics/observability instrumentation (Micrometer)

WebFilter vs HandlerFilterFunction (a DIFFERENT, narrower mechanism):

  WebFilter            — applies APPLICATION-WIDE (or per configured pattern),
                           runs for EVERY request regardless of routing style
                           (annotated controllers OR functional endpoints)

  HandlerFilterFunction — applies ONLY within a SPECIFIC RouterFunction's
                           .filter(...) call (see the functional endpoints card) —
                           scoped to just that route table, not global
```

## 4. Diagram

<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="200" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">WebFilter scope (global) vs HandlerFilterFunction scope (per-route-table)</text>

  <rect x="20" y="50" width="330" height="120" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="185" y="72" text-anchor="middle" fill="#6db33f" font-size="11">WebFilter</text>
  <text x="35" y="95" fill="#8b949e" font-size="9">applies to EVERY request, application-wide</text>
  <text x="35" y="113" fill="#8b949e" font-size="9">works regardless of routing style</text>
  <text x="35" y="131" fill="#8b949e" font-size="9">(annotated controllers OR functional)</text>

  <rect x="390" y="50" width="330" height="120" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="555" y="72" text-anchor="middle" fill="#79c0ff" font-size="11">HandlerFilterFunction</text>
  <text x="405" y="95" fill="#8b949e" font-size="9">scoped to ONE RouterFunction's routes</text>
  <text x="405" y="113" fill="#8b949e" font-size="9">only relevant for functional endpoints</text>

  <defs>
    <marker id="a57" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`WebFilter` is application-wide and routing-style-agnostic; `HandlerFilterFunction` is scoped to a specific functional route table.*

## 5. Runnable example

### Level 1 — Basic

A rate-limiting `WebFilter` demonstrating auto-discovery — no manual registration beyond `@Component`:

```java
// RateLimitWebFilter.java
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

@Component
@Order(1)
public class RateLimitWebFilter implements WebFilter {

    private final Map<String, AtomicInteger> requestCounts = new ConcurrentHashMap<>();
    private static final int LIMIT = 5;

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        String clientIp = exchange.getRequest().getRemoteAddress() != null
            ? exchange.getRequest().getRemoteAddress().getHostString() : "unknown";

        int count = requestCounts.computeIfAbsent(clientIp, k -> new AtomicInteger(0)).incrementAndGet();
        if (count > LIMIT) {
            exchange.getResponse().setStatusCode(HttpStatus.TOO_MANY_REQUESTS);
            return exchange.getResponse().setComplete();
        }
        return chain.filter(exchange);
    }
}
```

```java
// ProductController.java — this class knows NOTHING about the rate limiter
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {
    @GetMapping("/products/{id}")
    public Mono<String> get(@PathVariable long id) {
        return Mono.just("Drill");
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

for i in 1 2 3 4 5 6; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/products/1; done
# 200
# 200
# 200
# 200
# 200
# 429
```

`RateLimitWebFilter` was never explicitly registered anywhere — Spring Boot's WebFlux autoconfiguration discovers it purely by virtue of being a `@Component` implementing `WebFilter`, and its `@Order(1)` places it appropriately relative to other filters (including built-in ones like `CorsWebFilter`, which by default run at a specific, well-known precedence).

### Level 2 — Intermediate

`WebFilter` applying uniformly across both an annotated controller and a functional endpoint — demonstrating the "routing-style-agnostic" characteristic directly:

```java
// LoggingWebFilter.java
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;

@Component
@Order(0)
public class LoggingWebFilter implements WebFilter {
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        System.out.println("Request: " + exchange.getRequest().getPath());
        return chain.filter(exchange);
    }
}
```

```java
// ProductController.java — annotated style
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {
    @GetMapping("/annotated/products/{id}")
    public Mono<String> get(@PathVariable long id) { return Mono.just("Drill"); }
}
```

```java
// RouteConfig.java — functional style
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.server.RouterFunction;
import org.springframework.web.reactive.function.server.RouterFunctions;
import org.springframework.web.reactive.function.server.ServerResponse;

@Configuration
public class RouteConfig {
    @Bean
    public RouterFunction<ServerResponse> functionalRoutes() {
        return RouterFunctions.route()
            .GET("/functional/products/{id}", request -> ServerResponse.ok().bodyValue("Drill"))
            .build();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/annotated/products/1
# server log: "Request: /annotated/products/1"

curl http://localhost:8080/functional/products/1
# server log: "Request: /functional/products/1"
```

**What changed:** `LoggingWebFilter` logs both requests identically, despite one being handled by an `@RestController` method and the other by a `RouterFunction`-based `HandlerFunction`. This confirms `WebFilter` operates at a layer entirely above the routing-style distinction — it wraps `DispatcherHandler`'s work as a whole (per the `DispatcherHandler` card), regardless of which internal `HandlerMapping` ultimately resolves the request.

### Level 3 — Advanced

Production concern: correctly ordering a custom `WebFilter` relative to Spring's own built-in filters (specifically `CorsWebFilter`), and understanding why CORS-related filters generally need to run *before* authentication/authorization filters — mirroring a genuinely important, easy-to-get-wrong production consideration:

```java
// SecurityAuditWebFilter.java
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;

@Component
// Ordered AFTER CORS (Spring's own CorsWebFilter typically runs at a very
// high precedence) but BEFORE the actual handler — CORS preflight (OPTIONS)
// requests should NEVER be rejected by an auth check, since they carry no
// credentials by design; if auth ran before CORS, legitimate preflight
// requests would be incorrectly blocked, breaking CORS entirely for
// authenticated endpoints.
@Order(Ordered.HIGHEST_PRECEDENCE + 10)
public class SecurityAuditWebFilter implements WebFilter {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        if (exchange.getRequest().getMethod().name().equals("OPTIONS")) {
            // Preflight requests: skip auth entirely, let CORS's own
            // (already-run, higher-precedence) handling take care of it.
            return chain.filter(exchange);
        }

        String token = exchange.getRequest().getHeaders().getFirst("X-Auth-Token");
        if (!"secret-token".equals(token)) {
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }

        System.out.println("Authenticated request: " + exchange.getRequest().getPath());
        return chain.filter(exchange);
    }
}
```

```java
// CorsConfig.java — registered with default (high) precedence, runs BEFORE SecurityAuditWebFilter
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
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(List.of("http://localhost:3000"));
        config.setAllowedMethods(List.of("GET", "POST"));

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);
        return new CorsWebFilter(source);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# A browser's automatic preflight OPTIONS request — must succeed WITHOUT auth:
curl -i -X OPTIONS http://localhost:8080/products/1 \
     -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET"
# HTTP/1.1 200 OK
# Access-Control-Allow-Origin: http://localhost:3000
# (CorsWebFilter handled this BEFORE SecurityAuditWebFilter's OPTIONS bypass even mattered,
#  but the explicit bypass in SecurityAuditWebFilter is still correct defensive practice)

curl -i -H "Origin: http://localhost:3000" http://localhost:8080/products/1
# HTTP/1.1 401 Unauthorized     <- the REAL GET request still requires auth
```

**What changed and why:**
- `CorsWebFilter` (registered by Spring Boot's CORS autoconfiguration path) typically runs at a very high precedence by default, generally before custom application filters — `SecurityAuditWebFilter`'s explicit `@Order(HIGHEST_PRECEDENCE + 10)` deliberately places it *after* that default CORS handling, and its own explicit `OPTIONS` bypass is a belt-and-suspenders defensive measure ensuring preflight requests are never blocked by auth logic regardless of exact ordering nuances across Spring versions or configuration changes.
- This ordering concern is genuinely important in production: browsers automatically send preflight `OPTIONS` requests before many real cross-origin requests (per the CORS specification, covered in the Spring MVC `@CrossOrigin` card), and these preflight requests carry no authentication credentials by design — if an authentication filter ran before CORS handling (or itself rejected `OPTIONS` requests), legitimate cross-origin API calls would fail entirely, with an error that's often confusingly reported as a generic "CORS error" in browser developer tools rather than clearly pointing to "auth filter blocked the preflight."
- This pattern — CORS enforcement first, then authentication, with an explicit auth bypass for `OPTIONS` as extra insurance — is a standard, recommended structure for any WebFlux application combining CORS support with custom authentication `WebFilter`s.

## 6. Walkthrough

**Request: browser's automatic preflight `OPTIONS /products/1` (Level 3 code, before the real `GET` request).**

1. The WebFlux `WebFilter` chain processes this request in priority order. `CorsWebFilter` (Spring's own, registered at a high default precedence) runs first.
2. `CorsWebFilter` recognizes this as a CORS preflight request (`OPTIONS` method with `Access-Control-Request-Method` header present) and, per the CORS specification's preflight handling, responds directly with the appropriate `Access-Control-Allow-*` headers and a `200` status — **without** ever calling `chain.filter(exchange)` to continue further, since a preflight response doesn't need to reach the actual application logic at all.
3. Because `CorsWebFilter` already short-circuited the chain, `SecurityAuditWebFilter` (which would run next, at `HIGHEST_PRECEDENCE + 10`) is never even invoked for this specific request — its `OPTIONS`-bypass logic exists as defense-in-depth for scenarios where ordering might differ, but in this specific, well-configured setup, `CorsWebFilter` handles the preflight completely on its own.
4. Response:
   ```
   HTTP/1.1 200 OK
   Access-Control-Allow-Origin: http://localhost:3000
   Access-Control-Allow-Methods: GET,POST
   ```

**The subsequent real request: `GET /products/1` (with `Origin: http://localhost:3000`, no `X-Auth-Token`).**

1. `CorsWebFilter` runs first again: this is not a preflight request (no `Access-Control-Request-Method` header, and the method is `GET` not `OPTIONS`), so it adds the appropriate `Access-Control-Allow-Origin` response header for the eventual response and calls `chain.filter(exchange)` to continue.
2. `SecurityAuditWebFilter` runs next: `exchange.getRequest().getMethod().name()` is `"GET"`, not `"OPTIONS"`, so the bypass condition is `false` — it proceeds to the actual auth check. `X-Auth-Token` header is absent (`null`), which doesn't equal `"secret-token"` — the condition fails.
3. `exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED)` is set, and `exchange.getResponse().setComplete()` is returned directly — `DispatcherHandler` (and therefore `ProductController.get`) is never reached for this request.
4. Because `CorsWebFilter` already added its `Access-Control-Allow-Origin` header earlier in step 1 (before handing off via `chain.filter`), that header is still present on this final `401` response — the browser will correctly see this as a legitimate, CORS-permitted `401` response (allowing the calling JavaScript to actually read and handle the `401` status), rather than a confusing CORS failure masking the real authentication issue.
5. Response:
   ```
   HTTP/1.1 401 Unauthorized
   Access-Control-Allow-Origin: http://localhost:3000
   ```

## 7. Gotchas & takeaways

> **A custom `WebFilter` that rejects `OPTIONS` requests (or otherwise interferes with preflight handling) before `CorsWebFilter` gets a chance to run breaks CORS entirely for any endpoint that filter applies to** — always verify custom security/auth filters either run after CORS handling or explicitly bypass `OPTIONS` requests, as demonstrated in the Level 3 example.

> **`WebFilter` ordering across multiple `@Component`-registered filters, plus any Spring-internal filters (CORS, observability), can be genuinely subtle** — when debugging unexpected filter interaction, explicitly log each filter's entry/exit (as several examples in this and related cards do) to observe the actual runtime order, rather than assuming it purely from `@Order` values without verification, since some built-in filters' precedence isn't always obvious from documentation alone.

> **`HandlerFilterFunction` (used within a `RouterFunction`'s `.filter(...)` call, from the functional endpoints card) is a genuinely different, narrower mechanism than `WebFilter`** — don't confuse the two; a `HandlerFilterFunction` only wraps the specific `RouterFunction` it's attached to, while a `WebFilter` bean applies application-wide regardless of routing style.

- `WebFilter` beans are auto-discovered by Spring Boot's WebFlux autoconfiguration; `@Order`/`Ordered` controls their execution sequence relative to each other and to Spring's own built-in filters.
- `WebFilter` applies uniformly across both annotated (`@RestController`) and functional (`RouterFunction`) routing styles, since it wraps `DispatcherHandler`'s work as a whole.
- CORS-related filters must run before authentication/authorization filters, with explicit `OPTIONS` bypasses in auth filters as defense-in-depth, to avoid breaking preflight requests.
- `WebFilter` (global) and `HandlerFilterFunction` (scoped to one `RouterFunction`) are distinct mechanisms serving different scopes — don't conflate them when designing cross-cutting logic.
