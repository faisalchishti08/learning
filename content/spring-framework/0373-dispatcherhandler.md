---
card: spring-framework
gi: 373
slug: dispatcherhandler
title: "DispatcherHandler"
---

## 1. What it is

`DispatcherHandler` is Spring WebFlux's central request-processing component — the direct architectural counterpart to Spring MVC's `DispatcherServlet`, but built entirely around reactive types and the `WebHandler`/`HandlerMapping`/`HandlerAdapter` abstractions rather than the Servlet API. Every request, whether ultimately handled by an `@RestController` method or a functional `RouterFunction`, flows through `DispatcherHandler`, which coordinates handler discovery, invocation, and response writing — all without blocking a thread at any stage.

```java
// You never instantiate or call DispatcherHandler directly — Spring Boot's
// WebFlux autoconfiguration wires it in as the single entry point for every request.
// Understanding it explains WHAT actually happens between "a request arrives"
// and "your @GetMapping method (or RouterFunction) gets invoked."
```

## 2. Why & when

You rarely interact with `DispatcherHandler` directly in application code — it's autoconfigured and invisible in normal usage. Understanding its role matters when:

- You want a genuine mental model of what WebFlux does with a request end-to-end, beyond "annotations magically work" — useful for debugging routing issues, understanding handler resolution order, or reasoning about where custom cross-cutting logic (a `WebFilter`, covered in relation to this) should plug in.
- You're comparing WebFlux's architecture to Spring MVC's `DispatcherServlet` (an earlier, foundational card) to understand exactly which concepts transfer directly and which are WebFlux-specific.
- You're implementing genuinely low-level customizations — a custom `HandlerMapping`, a custom `HandlerResultHandler` — which requires understanding how `DispatcherHandler` discovers and delegates to these pluggable strategy components.

## 3. Core concept

```
DispatcherServlet (Spring MVC)          DispatcherHandler (Spring WebFlux)
────────────────────────────────────────────────────────────────────────
extends HttpServlet                     implements WebHandler
tied to the Servlet API                  Reactive-Streams-native, no Servlet
                                          API dependency at its core

Request lifecycle (WebFlux):

  1. ServerWebExchange arrives (wraps ServerHttpRequest/Response —
     WebFlux's OWN reactive abstraction, not HttpServletRequest/Response)
        |
        v
  2. DispatcherHandler asks each registered HandlerMapping, in order,
     "can you resolve a handler for this exchange?"
       RequestMappingHandlerMapping  — for @RestController/@GetMapping
       RouterFunctionMapping          — for RouterFunction-based routes
       (first non-empty Mono<Object> result wins)
        |
        v
  3. DispatcherHandler finds the matching HandlerAdapter for
     the resolved handler's TYPE, and invokes it
        |
        v
  4. The handler executes (your @GetMapping method, or a
     HandlerFunction), producing a Mono<HandlerResult> (or,
     for functional endpoints, directly a Mono<ServerResponse>)
        |
        v
  5. A HandlerResultHandler writes the result to the response
     (serializing to JSON, etc.) — reactively, non-blocking throughout
```

## 4. Diagram

<svg viewBox="0 0 740 230" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="230" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">DispatcherHandler orchestrates handler discovery and invocation</text>

  <rect x="20" y="50" width="160" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="100" y="80" text-anchor="middle" fill="#79c0ff" font-size="10">ServerWebExchange</text>

  <line x1="180" y1="75" x2="230" y2="75" stroke="#8b949e" marker-end="url(#a49)"/>

  <rect x="230" y="50" width="240" height="50" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="350" y="80" text-anchor="middle" fill="#6db33f" font-size="10">DispatcherHandler</text>

  <line x1="350" y1="100" x2="350" y2="130" stroke="#8b949e" marker-end="url(#a49)"/>

  <rect x="230" y="130" width="240" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="350" y="155" text-anchor="middle" fill="#8b949e" font-size="9">HandlerMapping chain (tries each)</text>

  <line x1="470" y1="75" x2="540" y2="75" stroke="#8b949e" marker-end="url(#a49)"/>

  <rect x="540" y="50" width="180" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="630" y="80" text-anchor="middle" fill="#e6edf3" font-size="10">HandlerAdapter -&gt; invoke</text>

  <defs>
    <marker id="a49" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`DispatcherHandler` consults each `HandlerMapping` in turn, then delegates invocation to the appropriate `HandlerAdapter` for whichever handler type was resolved.*

## 5. Runnable example

### Level 1 — Basic

Observing `DispatcherHandler`'s work indirectly, by registering a `WebFilter` that runs immediately before it — the standard way application code can hook into the request pipeline surrounding `DispatcherHandler`:

```java
// LoggingWebFilter.java
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;

@Component
public class LoggingWebFilter implements WebFilter {
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        System.out.println("Before DispatcherHandler: " + exchange.getRequest().getPath());
        return chain.filter(exchange)   // hands off to DispatcherHandler (or the next filter)
            .doFinally(signal -> System.out.println("After DispatcherHandler: status="
                + exchange.getResponse().getStatusCode()));
    }
}
```

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {

    record Product(long id, String name) {}

    @GetMapping("/products/{id}")
    public Mono<Product> get(@PathVariable long id) {
        return Mono.just(new Product(id, "Drill"));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/1
# {"id":1,"name":"Drill"}

# server log:
# Before DispatcherHandler: /products/1
# After DispatcherHandler: status=200 OK
```

`WebFilter` is WebFlux's equivalent of a Servlet `Filter` (an MVC concept from an earlier card) — it runs *around* `DispatcherHandler`'s own work, which is exactly what lets the log lines bracket the actual handler resolution and invocation happening inside `DispatcherHandler` itself, even though application code never calls `DispatcherHandler` directly.

### Level 2 — Intermediate

Two handler-resolution mechanisms — annotated controller and functional endpoint — coexisting in the same application, demonstrating `DispatcherHandler`'s role in trying multiple `HandlerMapping`s until one matches:

```java
// ProductController.java — resolved via RequestMappingHandlerMapping
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {
    record Product(long id, String name) {}

    @GetMapping("/annotated/products/{id}")
    public Mono<Product> get(@PathVariable long id) {
        return Mono.just(new Product(id, "Drill"));
    }
}
```

```java
// RouteConfig.java — resolved via RouterFunctionMapping
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.server.RouterFunction;
import org.springframework.web.reactive.function.server.RouterFunctions;
import org.springframework.web.reactive.function.server.ServerResponse;

@Configuration
public class RouteConfig {

    record Product(long id, String name) {}

    @Bean
    public RouterFunction<ServerResponse> productRoutes() {
        return RouterFunctions.route()
            .GET("/functional/products/{id}", request -> {
                long id = Long.parseLong(request.pathVariable("id"));
                return ServerResponse.ok().bodyValue(new Product(id, "Drill"));
            })
            .build();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/annotated/products/1
# {"id":1,"name":"Drill"}     <- resolved via RequestMappingHandlerMapping

curl http://localhost:8080/functional/products/1
# {"id":1,"name":"Drill"}     <- resolved via RouterFunctionMapping
```

**What changed:** Both endpoints work through the *same* `DispatcherHandler`, which tries its ordered list of `HandlerMapping`s for each incoming request — `RequestMappingHandlerMapping` (for annotations) is generally checked, and separately `RouterFunctionMapping` (for functional routes) is also checked; whichever mapping actually recognizes the request's path resolves it. Application code (and, from the outside, the HTTP client) has no visibility into which mechanism ultimately served a given request — `DispatcherHandler`'s job is precisely to make this uniform.

### Level 3 — Advanced

A minimal custom `HandlerMapping`/`HandlerAdapter` pair, demonstrating the low-level extension points `DispatcherHandler` itself is built around — genuinely rare to need in practice, but illuminating for understanding exactly how `@GetMapping` and `RouterFunction` both plug into the same dispatch mechanism:

```java
// PingHandlerMapping.java — a THIRD, custom HandlerMapping, alongside the two built-in ones
import org.springframework.core.Ordered;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.HandlerMapping;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

@Component
public class PingHandlerMapping implements HandlerMapping, Ordered {

    @Override
    public Mono<Object> getHandler(ServerWebExchange exchange) {
        if ("/ping".equals(exchange.getRequest().getPath().value())) {
            // Returning the STRING "pong" itself as the "handler" — paired with
            // a custom HandlerAdapter (below) that knows how to process String handlers.
            return Mono.just("pong");
        }
        return Mono.empty();   // "not my concern" — DispatcherHandler tries the NEXT mapping
    }

    @Override
    public int getOrder() { return Ordered.HIGHEST_PRECEDENCE; }   // check this FIRST
}
```

```java
// PingHandlerAdapter.java — knows how to invoke a "String" handler
import org.springframework.core.Ordered;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.HandlerAdapter;
import org.springframework.web.reactive.HandlerResult;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

@Component
public class PingHandlerAdapter implements HandlerAdapter, Ordered {

    @Override
    public boolean supports(Object handler) {
        return handler instanceof String;   // this adapter ONLY handles String-typed handlers
    }

    @Override
    public Mono<HandlerResult> handle(ServerWebExchange exchange, Object handler) {
        return Mono.just(new HandlerResult(handler, handler, null));   // returns "pong" as the result
    }

    @Override
    public int getOrder() { return Ordered.HIGHEST_PRECEDENCE; }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/ping
# pong

curl http://localhost:8080/annotated/products/1
# {"id":1,"name":"Drill"}     <- unaffected; PingHandlerMapping returned empty for this path,
#                                 so DispatcherHandler moved on to RequestMappingHandlerMapping
```

**What changed and why:**
- `PingHandlerMapping.getHandler` returns `Mono.empty()` for any path other than `/ping` — this is the exact same "not my concern, try the next one" contract seen in Spring MVC's `ViewResolver` chain (an earlier card) and elsewhere in Spring's pluggable-strategy patterns, just expressed reactively (`Mono.empty()` instead of returning `null`).
- `PingHandlerAdapter.supports(Object)` lets `DispatcherHandler` know this specific adapter knows how to invoke a `String`-typed "handler" — in a real `RequestMappingHandlerMapping`/`RequestMappingHandlerAdapter` pairing, the handler object is actually a `HandlerMethod` (wrapping a controller instance and a reflective `Method` reference), and the built-in adapter knows how to invoke it, resolve its arguments, and process its return value; this toy example substitutes a bare `String` purely to keep the illustration minimal.
- This demonstrates concretely that `@GetMapping` methods and `RouterFunction`-based routes are not special-cased inside `DispatcherHandler` itself — they're both just particular `HandlerMapping`/`HandlerAdapter` implementations plugged into the same, genuinely open, extensible dispatch mechanism that this toy `PingHandlerMapping`/`PingHandlerAdapter` pair also plugs into.

## 6. Walkthrough

**Request: `GET /annotated/products/1` (Level 2 code, with the Level 3 custom mapping also present).**

1. The reactive server (Netty, by default) receives the raw request and, via WebFlux's `HttpHandler` adapter layer (covered in the next card), constructs a `ServerWebExchange` wrapping the request/response — WebFlux's own reactive abstraction, analogous to but distinct from the Servlet API's `HttpServletRequest`/`Response`.
2. This exchange is handed to `DispatcherHandler.handle(exchange)`, the single entry point for all WebFlux request processing.
3. `DispatcherHandler` iterates its registered `HandlerMapping`s in order (by their `Ordered` priority). First, `PingHandlerMapping` (registered with `HIGHEST_PRECEDENCE`) is consulted: `exchange.getRequest().getPath().value()` is `/annotated/products/1`, not `/ping`, so it returns `Mono.empty()`.
4. `DispatcherHandler` moves to the next mapping — `RequestMappingHandlerMapping` (the built-in one backing `@GetMapping`). It matches `/annotated/products/1` against `ProductController.get`'s `@GetMapping("/annotated/products/{id}")` pattern — a match, binding `id = "1"`. It returns `Mono.just(handlerMethodWrappingProductControllerGet)`.
5. Because a non-empty result was found, `DispatcherHandler` stops checking further mappings (`RouterFunctionMapping` is never even consulted for this specific request) and proceeds to find a `HandlerAdapter` whose `supports(handler)` returns `true` for this specific handler object — `RequestMappingHandlerAdapter` (the built-in one) recognizes `HandlerMethod` instances and claims it.
6. `RequestMappingHandlerAdapter.handle(exchange, handler)` performs argument resolution (extracting `id=1` from the path, converting it to `long`), then invokes `ProductController.get(1)` reflectively.
7. `get(1)` executes, returning `Mono.just(new Product(1, "Drill"))` — this `Mono` becomes part of the `HandlerResult` the adapter produces.
8. `DispatcherHandler` locates an appropriate `HandlerResultHandler` (one capable of processing this kind of result — here, one that knows how to serialize a returned object to the response body, mirroring `@ResponseBody` semantics), which subscribes to the inner `Mono<Product>`, serializes the eventually-emitted `Product` to JSON via Jackson, and writes it to the response.
9. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   {"id":1,"name":"Drill"}
   ```

## 7. Gotchas & takeaways

> **`DispatcherHandler` tries `HandlerMapping`s strictly in priority order and stops at the first non-empty result** — a custom mapping registered with too broad a matching condition and too high a priority can silently shadow built-in mappings for overlapping paths, exactly as an overly broad custom `ViewResolver` can shadow Thymeleaf's in Spring MVC. Scope custom mappings' matching logic as narrowly as possible.

> **`DispatcherHandler` itself has no dependency on the Servlet API** — this is precisely what allows WebFlux applications to run on genuinely non-Servlet reactive servers like Netty directly, unlike Spring MVC's `DispatcherServlet`, which is fundamentally a `HttpServlet` subclass and therefore requires a Servlet container. The next card (`HttpHandler` & adapters) explains exactly how this server-agnosticism is achieved.

> **You almost never need to implement a custom `HandlerMapping`/`HandlerAdapter` pair** — the Level 3 example exists purely to illuminate the mechanism; in practice, `@RestController`/`@GetMapping` (via the built-in `RequestMappingHandlerMapping`/`Adapter`) and `RouterFunction` (via `RouterFunctionMapping`) cover essentially every real-world routing need.

- `DispatcherHandler` is WebFlux's central dispatcher, directly analogous to Spring MVC's `DispatcherServlet` but built entirely on reactive types with no Servlet API dependency at its core.
- It consults registered `HandlerMapping`s in priority order, delegating to the first one that resolves a handler for the request, then finds a matching `HandlerAdapter` to actually invoke that handler.
- Both `@RestController`/`@GetMapping` (via `RequestMappingHandlerMapping`) and `RouterFunction`-based routes (via `RouterFunctionMapping`) are just two of potentially many pluggable `HandlerMapping` implementations — the mechanism is genuinely open and extensible.
- `WebFilter` is the standard way application code hooks into the request pipeline surrounding `DispatcherHandler`'s own work, mirroring Servlet `Filter`s in the MVC world.
