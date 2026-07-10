---
card: spring-framework
gi: 375
slug: webhandler-api
title: "WebHandler API"
---

## 1. What it is

The `WebHandler` API is the layer directly above `HttpHandler` (previous card) and directly implemented by `DispatcherHandler` itself — a single-method interface (`Mono<Void> handle(ServerWebExchange)`) that operates on `ServerWebExchange` (a higher-level, more convenient wrapper around the request/response pair than the raw `ServerHttpRequest`/`ServerHttpResponse`) rather than the two separate parameters `HttpHandler` uses. `WebFilter` (WebFlux's filter abstraction, briefly introduced in the `DispatcherHandler` card) is built specifically around this `ServerWebExchange`-centric model.

```java
public interface WebHandler {
    Mono<Void> handle(ServerWebExchange exchange);
}

public interface WebFilter {
    Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain);
}
```

## 2. Why & when

`ServerWebExchange` bundles the request, response, session access, locale/principal resolution, and a mutable attribute map into one convenient object — rather than passing request and response as two separate parameters everywhere (as raw `HttpHandler` does), the `WebHandler` API and everything built on it (`WebFilter`, `DispatcherHandler`) works with this single, richer exchange object. Understanding this layer matters when:

- Writing a `WebFilter` — WebFlux's primary mechanism for cross-cutting request/response logic (authentication checks, logging, header manipulation) that should apply broadly, the direct reactive counterpart to a Servlet `Filter` in Spring MVC.
- Understanding how request-scoped data (attributes, session access) flows through a reactive pipeline where there's no `ThreadLocal`-friendly single thread handling the whole request — `ServerWebExchange` is explicitly designed to carry this context reactively instead.
- Composing multiple `WebFilter`s and understanding their execution order, which mirrors (but is architecturally distinct from) Spring MVC's `HandlerInterceptor` chain.

## 3. Core concept

```
ServerWebExchange — bundles everything about ONE request/response pair:

  exchange.getRequest()     -> ServerHttpRequest
  exchange.getResponse()    -> ServerHttpResponse
  exchange.getAttributes()  -> Map<String,Object> (request-scoped data, NOT ThreadLocal —
                                 explicitly passed through the reactive chain instead)
  exchange.getSession()     -> Mono<WebSession> (reactive — session access ITSELF is async)
  exchange.getPrincipal()   -> Mono<Principal>   (reactive — auth info ITSELF is async)

WebFilter chain (mirrors HandlerInterceptor conceptually, but reactive):

  filter1.filter(exchange, chain) calls chain.filter(exchange)
    -> filter2.filter(exchange, chain) calls chain.filter(exchange)
      -> ... -> eventually DispatcherHandler.handle(exchange)
        <- Mono<Void> propagates back up through each filter,
           each able to run additional logic via .then()/.doFinally()/etc.
           on the way back, since Mono composition naturally supports this

Layering, complete picture:
  WebFilter chain  (operates on ServerWebExchange)
        |
  DispatcherHandler (implements WebHandler, operates on ServerWebExchange)
        |
  (wrapped into a single HttpHandler by WebHttpHandlerBuilder)
        |
  Server-specific HttpHandler adapter (operates on ServerHttpRequest/Response separately)
```

## 4. Diagram

<svg viewBox="0 0 740 210" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="210" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">WebFilter chain wraps DispatcherHandler, both operating on ServerWebExchange</text>

  <rect x="20" y="50" width="700" height="130" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="370" y="72" text-anchor="middle" fill="#8b949e" font-size="10">WebFilter 1</text>

  <rect x="60" y="90" width="620" height="70" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="370" y="110" text-anchor="middle" fill="#79c0ff" font-size="10">WebFilter 2</text>

  <rect x="260" y="125" width="220" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="145" text-anchor="middle" fill="#6db33f" font-size="9">DispatcherHandler.handle(exchange)</text>

  <text x="370" y="195" text-anchor="middle" fill="#8b949e" font-size="9">Mono&lt;Void&gt; propagates back through each filter — chain.filter() composes them</text>

  <defs>
    <marker id="a51" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`WebFilter`s nest around `DispatcherHandler`'s own `WebHandler.handle` call, all sharing the same `ServerWebExchange`.*

## 5. Runnable example

### Level 1 — Basic

A single `WebFilter` reading and mutating exchange attributes — the reactive equivalent of setting a request attribute in a Servlet filter:

```java
// RequestIdWebFilter.java
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class RequestIdWebFilter implements WebFilter {
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        String requestId = UUID.randomUUID().toString();
        exchange.getAttributes().put("requestId", requestId);   // stored on the EXCHANGE, not a ThreadLocal
        exchange.getResponse().getHeaders().add("X-Request-Id", requestId);
        return chain.filter(exchange);   // hand off to the next filter / DispatcherHandler
    }
}
```

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {

    record Product(long id, String name, String requestId) {}

    @GetMapping("/products/{id}")
    public Mono<Product> get(@PathVariable long id, ServerWebExchange exchange) {
        String requestId = exchange.getAttribute("requestId");
        return Mono.just(new Product(id, "Drill", requestId));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/1
# HTTP/1.1 200 OK
# X-Request-Id: 7c9e6679-...
# {"id":1,"name":"Drill","requestId":"7c9e6679-..."}
```

`ServerWebExchange` can be injected directly as a handler method parameter (WebFlux recognizes this type specially, alongside the usual `@PathVariable`/`@RequestParam` parameters), giving controller code direct access to attributes a `WebFilter` set earlier in the chain — the reactive equivalent of reading a Servlet request attribute set by an earlier `Filter`.

### Level 2 — Intermediate

Multiple `WebFilter`s composed with explicit ordering, one short-circuiting the chain (the WebFlux equivalent of `HandlerInterceptor.preHandle` returning `false`):

```java
// AuthWebFilter.java
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 1)   // runs AFTER RequestIdWebFilter, before the handler
public class AuthWebFilter implements WebFilter {
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        String token = exchange.getRequest().getHeaders().getFirst("X-Auth-Token");
        if (!"secret-token".equals(token)) {
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();   // SHORT-CIRCUITS: chain.filter() never called
        }
        return chain.filter(exchange);   // continue to the next filter / handler
    }
}
```

```java
// TimingWebFilter.java
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;

import java.time.Instant;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE)   // runs BEFORE AuthWebFilter — measures the FULL cycle, even rejections
public class TimingWebFilter implements WebFilter {
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        Instant start = Instant.now();
        return chain.filter(exchange)
            .doFinally(signal -> System.out.println(exchange.getRequest().getPath()
                + " took " + java.time.Duration.between(start, Instant.now()).toMillis() + "ms, status="
                + exchange.getResponse().getStatusCode()));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/1
# HTTP/1.1 401 Unauthorized
# server log: "/products/1 took 2ms, status=401 UNAUTHORIZED"

curl -i -H "X-Auth-Token: secret-token" http://localhost:8080/products/1
# HTTP/1.1 200 OK
# server log: "/products/1 took 5ms, status=200 OK"
```

**What changed:** `AuthWebFilter.filter` returns `exchange.getResponse().setComplete()` directly instead of calling `chain.filter(exchange)` — this is the reactive short-circuit mechanism, the direct equivalent of a `HandlerInterceptor.preHandle` returning `false`. `TimingWebFilter`, registered with a higher priority (lower order value, runs first), wraps the *entire* remaining chain via `.doFinally(...)` — meaning it correctly measures and logs even requests that `AuthWebFilter` rejects, exactly mirroring the ordering lesson from the MVC interceptors card.

### Level 3 — Advanced

Production concern: accessing the reactive `WebSession` and `Principal` (both inherently `Mono`-returning, since even session/auth lookup can be an async operation in a fully reactive stack) inside a `WebFilter`, composing multiple async lookups before deciding whether to proceed:

```java
// SessionAwareWebFilter.java
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import org.springframework.web.server.WebSession;
import reactor.core.publisher.Mono;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 2)
public class SessionAwareWebFilter implements WebFilter {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        // getSession() itself returns a Mono — session access is asynchronous,
        // consistent with everything else in a fully reactive request pipeline.
        return exchange.getSession()
            .flatMap(session -> {
                Integer visitCount = session.getAttributeOrDefault("visitCount", 0);
                session.getAttributes().put("visitCount", visitCount + 1);

                if (visitCount >= 100) {
                    exchange.getResponse().setStatusCode(HttpStatus.TOO_MANY_REQUESTS);
                    return exchange.getResponse().setComplete();
                }

                exchange.getAttributes().put("visitCount", visitCount + 1);
                return chain.filter(exchange);
            });
    }
}
```

```java
// ProductController.java (production version)
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {

    record Product(long id, String name, int visitCount) {}

    @GetMapping("/products/{id}")
    public Mono<Product> get(@PathVariable long id, ServerWebExchange exchange) {
        Integer visitCount = exchange.getAttribute("visitCount");
        return Mono.just(new Product(id, "Drill", visitCount != null ? visitCount : 0));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/products/1
# {"id":1,"name":"Drill","visitCount":1}

curl -i http://localhost:8080/products/1
# {"id":1,"name":"Drill","visitCount":2}
# (repeated visits from the same session increment the count)
```

**What changed and why:**
- `exchange.getSession()` returns a `Mono<WebSession>` rather than a direct `WebSession` object — this reflects a genuinely reactive stack's consistency principle: even something as seemingly simple as "get the current session" is treated as a potentially asynchronous operation (a session store might be backed by Redis or another external system reached over the network), so the `WebFilter` must `flatMap` into it rather than accessing it synchronously.
- The entire filter's logic — reading the session, checking a threshold, conditionally short-circuiting — is expressed as a single composed reactive chain (`flatMap` containing the conditional logic), never blocking to "wait for" the session to resolve; the filter method itself returns immediately with a `Mono<Void>` describing this eventual work, exactly mirroring the laziness principles from the reactive programming overview card.
- This demonstrates the practical reality of writing `WebFilter`s in a fully reactive application: essentially every piece of contextual information (session, principal, even sometimes configuration lookups) may itself be `Mono`-wrapped, requiring filter logic to be composed via `flatMap`/`then`/etc. rather than written as a sequence of synchronous statements, a real and persistent complexity cost relative to the equivalent Spring MVC `HandlerInterceptor` code.

## 6. Walkthrough

**Request: `GET /products/1` (Level 2 code, valid `X-Auth-Token` header present).**

1. `DispatcherHandler`'s enclosing `HttpHandler` (built by `WebHttpHandlerBuilder`, per the previous card) begins processing by constructing the `WebFilter` chain in priority order: `TimingWebFilter` (order `HIGHEST_PRECEDENCE`) first, then `AuthWebFilter` (order `HIGHEST_PRECEDENCE + 1`).
2. `TimingWebFilter.filter(exchange, chain)` executes: records `start = Instant.now()`, then calls `chain.filter(exchange)` — this hands control to the next filter in the chain, `AuthWebFilter`, while `TimingWebFilter`'s own `Mono<Void>` chain (via `.doFinally(...)`) remains attached, ready to run once everything downstream eventually completes.
3. `AuthWebFilter.filter(exchange, chain)` executes: reads `X-Auth-Token` from the request headers, finds it equals `"secret-token"` — the condition passes, so it calls `chain.filter(exchange)` itself, handing control further down the chain toward `DispatcherHandler`.
4. `DispatcherHandler.handle(exchange)` (implementing the base `WebHandler` interface this whole filter chain ultimately wraps) proceeds with its own handler-resolution logic (from the earlier `DispatcherHandler` card) — resolving and invoking `ProductController.get(1, exchange)`, eventually writing the JSON response body and setting a `200` status on `exchange.getResponse()`.
5. This completion signal propagates back **up** through the chain: `AuthWebFilter`'s returned `Mono<Void>` (which was just `chain.filter(exchange)`, with no additional `.then()`/`.doFinally()` composition of its own) completes once `DispatcherHandler`'s work completes.
6. Back in `TimingWebFilter`: the `.doFinally(signal -> {...})` callback attached earlier now fires, since the `chain.filter(exchange)` `Mono` it was wrapping has completed. It reads `exchange.getResponse().getStatusCode()` — now `200 OK`, since `DispatcherHandler` set it — and logs the elapsed time and final status.
7. The overall response, fully written by this point, is sent to the client:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   {"id":1,"name":"Drill","requestId":"..."}
   ```

**Same request, but with a missing/invalid `X-Auth-Token` header.**

1–2. Identical: `TimingWebFilter` records `start`, calls `chain.filter(exchange)`.
3. `AuthWebFilter.filter` executes: the token check fails this time. It sets `HttpStatus.UNAUTHORIZED` on the response and returns `exchange.getResponse().setComplete()` **directly** — critically, it never calls `chain.filter(exchange)`, so `DispatcherHandler` is never invoked at all for this request; `ProductController.get` never executes.
4. `exchange.getResponse().setComplete()` returns a `Mono<Void>` representing "the response is now finished being written" — this immediately satisfies the `Mono<Void>` that `AuthWebFilter.filter` returns, which in turn satisfies the `chain.filter(exchange)` call `TimingWebFilter` made back in step 2.
5. `TimingWebFilter`'s `.doFinally(...)` fires just as before — reading `exchange.getResponse().getStatusCode()`, now `401 UNAUTHORIZED` (set by `AuthWebFilter` in step 3), and logs it correctly, demonstrating that the timing filter's placement (wrapping the *entire* chain, including short-circuited paths) captures accurate metrics regardless of where in the chain a request is ultimately rejected.
6. Response:
   ```
   HTTP/1.1 401 Unauthorized
   ```

## 7. Gotchas & takeaways

> **`ServerWebExchange` attributes are explicitly passed through the reactive chain, not stored in a `ThreadLocal`** — this is a deliberate and necessary design choice, since a single logical request in WebFlux can genuinely be processed across multiple different threads over its lifetime (as operations move between Reactor's schedulers). Code assuming `ThreadLocal`-style request-scoped state (a common pattern in Spring MVC, e.g. via `RequestContextHolder`) does not translate directly to WebFlux — always use `ServerWebExchange` attributes instead.

> **Forgetting to call `chain.filter(exchange)` in a `WebFilter` (other than a deliberate short-circuit) silently stops the entire request from ever reaching `DispatcherHandler`** — with no explicit error, the client simply receives whatever partial response state existed at that point (often an incomplete or empty response), which can be confusing to debug without realizing a filter forgot this call.

> **`exchange.getSession()`/`exchange.getPrincipal()` returning `Mono` rather than a direct value is easy to overlook when translating Spring MVC `HttpSession`-based code**, where session access is always synchronous. Attempting to treat these as synchronous (e.g., accidentally calling `.block()` on them) reintroduces blocking into what should be a fully non-blocking pipeline — always compose with `flatMap` instead.

- `WebHandler` (`Mono<Void> handle(ServerWebExchange)`) is the layer `DispatcherHandler` itself implements, sitting above the lower-level `HttpHandler` abstraction, operating on the richer `ServerWebExchange` object.
- `WebFilter` is WebFlux's reactive counterpart to a Servlet `Filter`, composing around `DispatcherHandler`'s own work via the same `ServerWebExchange`, with explicit short-circuiting via `exchange.getResponse().setComplete()` instead of calling `chain.filter(exchange)`.
- Request-scoped state flows through `ServerWebExchange` attributes, not `ThreadLocal`, since a single request's processing can span multiple threads in a reactive pipeline.
- Session, principal, and other contextual lookups are themselves `Mono`-wrapped in WebFlux, requiring `flatMap`-based composition rather than the synchronous access patterns familiar from Spring MVC.
