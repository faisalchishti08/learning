---
card: spring-framework
gi: 372
slug: functional-endpoints-routerfunctions
title: "Functional endpoints (RouterFunctions)"
---

## 1. What it is

WebFlux's functional endpoints let you define routes using `RouterFunction<ServerResponse>` and `HandlerFunction<ServerResponse>` — plain Java code composing request predicates to handler lambdas — as a complete alternative to `@RestController`/`@GetMapping` annotations. This mirrors the `RouterFunction`-based functional endpoints covered for Spring MVC in an earlier card, but WebFlux's versions work with reactive types (`Mono<ServerResponse>`) throughout, and this style is considerably more central to how WebFlux applications are commonly built.

```java
@Bean
public RouterFunction<ServerResponse> productRoutes(ProductHandler handler) {
    return RouterFunctions.route()
        .GET("/api/products/{id}", handler::get)
        .POST("/api/products", handler::create)
        .build();
}
```

## 2. Why & when

Functional endpoints in WebFlux offer the same benefits described in the MVC version of this card (full route table visibility in one place, testable handler logic as plain functions, programmatic route composition) — but they carry additional weight in the WebFlux ecosystem specifically because:

- Many of Spring's own WebFlux reference examples and much community content default to this style, making it worth genuine fluency rather than passing familiarity.
- The reactive types (`Mono<ServerRequest>` → `Mono<ServerResponse>`) compose particularly naturally with functional-style route definitions, since both the routing layer and the handler logic are expressed in the same declarative, chainable idiom.
- Some teams specifically choose WebFlux *and* functional endpoints together as a deliberate architectural choice favoring explicit, code-visible routing over annotation-driven "magic" — understanding this style well matters for reading and contributing to such codebases.

## 3. Core concept

```
RouterFunction<ServerResponse> — the SAME predicate-to-handler
composition model as Spring MVC's functional endpoints, but:

  HandlerFunction<ServerResponse>:  ServerRequest -> Mono<ServerResponse>
                                     (REACTIVE — returns a Mono, not a ServerResponse directly)

  ServerRequest.bodyToMono(Class<T>)   — read the request body reactively
  ServerRequest.bodyToFlux(Class<T>)   — read a streaming request body reactively

  ServerResponse.ok().bodyValue(x)         — a KNOWN value, wrapped
  ServerResponse.ok().body(mono, Class)     — a Mono/Flux BODY, streamed reactively

RouterFunctions.route()
    .GET("/products/{id}", handler::get)
    .POST("/products", handler::create)
    .build()

Composition (nest, filter) — IDENTICAL in spirit to Spring MVC's version:
  RouterFunctions.nest(path("/api/products"), productRoutes)
  .filter((request, next) -> next.handle(request).onErrorResume(...))
```

## 4. Diagram

<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="200" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">ServerRequest -&gt; HandlerFunction -&gt; Mono&lt;ServerResponse&gt;</text>

  <rect x="20" y="50" width="180" height="60" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="80" text-anchor="middle" fill="#79c0ff" font-size="10">GET /products/1</text>

  <line x1="200" y1="80" x2="260" y2="80" stroke="#8b949e" marker-end="url(#a48)"/>

  <rect x="260" y="50" width="200" height="60" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="360" y="72" text-anchor="middle" fill="#6db33f" font-size="10">handler::get</text>
  <text x="360" y="90" text-anchor="middle" fill="#8b949e" font-size="9">ServerRequest -&gt; Mono&lt;ServerResponse&gt;</text>

  <line x1="460" y1="80" x2="520" y2="80" stroke="#8b949e" marker-end="url(#a48)"/>

  <rect x="520" y="50" width="180" height="60" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="610" y="80" text-anchor="middle" fill="#e6edf3" font-size="10">200 OK + body</text>

  <defs>
    <marker id="a48" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Every handler function returns a `Mono<ServerResponse>` — even the response itself is a reactive value, not a direct one.*

## 5. Runnable example

### Level 1 — Basic

A minimal functional endpoint reading a path variable and returning a value:

```java
// ProductHandler.java
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.server.ServerRequest;
import org.springframework.web.reactive.function.server.ServerResponse;
import reactor.core.publisher.Mono;

@Component
public class ProductHandler {

    record Product(long id, String name) {}

    public Mono<ServerResponse> get(ServerRequest request) {
        long id = Long.parseLong(request.pathVariable("id"));
        Product product = new Product(id, "Drill");
        return ServerResponse.ok().bodyValue(product);
    }
}
```

```java
// RouteConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.server.RouterFunction;
import org.springframework.web.reactive.function.server.RouterFunctions;
import org.springframework.web.reactive.function.server.ServerResponse;

@Configuration
public class RouteConfig {

    @Bean
    public RouterFunction<ServerResponse> productRoutes(ProductHandler handler) {
        return RouterFunctions.route()
            .GET("/api/products/{id}", handler::get)
            .build();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/api/products/1
# {"id":1,"name":"Drill"}
```

`ServerResponse.ok().bodyValue(product)` builds a `Mono<ServerResponse>` wrapping the already-known `product` value — `bodyValue` is the right choice when the body is a plain, synchronous value already in hand (as opposed to `.body(mono, Class)`, used when the body itself is asynchronous).

### Level 2 — Intermediate

A full CRUD route table with reactive body reading, `flatMap`-composed handler logic, and error handling via `onErrorResume`:

```java
// ProductHandler.java (extended)
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.server.ServerRequest;
import org.springframework.web.reactive.function.server.ServerResponse;
import reactor.core.publisher.Mono;

import java.net.URI;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@Component
public class ProductHandler {

    record Product(long id, String name, double price) {}
    record ProductRequest(String name, double price) {}

    private final Map<Long, Product> store = new ConcurrentHashMap<>();
    private final AtomicLong seq = new AtomicLong(1);

    public Mono<ServerResponse> get(ServerRequest request) {
        long id = Long.parseLong(request.pathVariable("id"));
        return Mono.justOrEmpty(store.get(id))
            .flatMap(ServerResponse.ok()::bodyValue)
            .switchIfEmpty(ServerResponse.notFound().build());
    }

    public Mono<ServerResponse> list(ServerRequest request) {
        return ServerResponse.ok().bodyValue(store.values());
    }

    public Mono<ServerResponse> create(ServerRequest request) {
        return request.bodyToMono(ProductRequest.class)
            .flatMap(req -> {
                long id = seq.getAndIncrement();
                Product product = new Product(id, req.name(), req.price());
                store.put(id, product);
                return ServerResponse.status(HttpStatus.CREATED)
                    .location(URI.create("/api/products/" + id))
                    .bodyValue(product);
            });
    }
}
```

```java
// RouteConfig.java (extended)
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.server.RouterFunction;
import org.springframework.web.reactive.function.server.RouterFunctions;
import org.springframework.web.reactive.function.server.ServerResponse;

@Configuration
public class RouteConfig {

    @Bean
    public RouterFunction<ServerResponse> productRoutes(ProductHandler handler) {
        return RouterFunctions.route()
            .GET("/api/products", handler::list)
            .GET("/api/products/{id}", handler::get)
            .POST("/api/products", handler::create)
            .build();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -X POST http://localhost:8080/api/products -H "Content-Type: application/json" -d '{"name":"Drill","price":29.99}'
# HTTP/1.1 201 Created
# Location: /api/products/1

curl http://localhost:8080/api/products/1
# {"id":1,"name":"Drill","price":29.99}

curl -i http://localhost:8080/api/products/99
# HTTP/1.1 404 Not Found
```

**What changed:** `request.bodyToMono(ProductRequest.class)` reactively reads and deserializes the request body — the handler function itself doesn't block waiting for those bytes; it describes what to do once they arrive, via `flatMap`. `Mono.justOrEmpty(...).flatMap(...).switchIfEmpty(...)` composes the "found vs not found" branching declaratively, mirroring the same pattern seen in the reactive annotated-controllers card, just expressed as a functional pipeline instead of inside an `@GetMapping` method body.

### Level 3 — Advanced

Production pattern: composed, nested routing with a shared error-handling filter, and a streaming response using `Flux` directly in the body — demonstrating functional endpoints' natural fit for reactive composition at scale:

```java
// ProductHandler.java (production version)
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.server.ServerRequest;
import org.springframework.web.reactive.function.server.ServerResponse;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;

@Component
public class ProductHandler {

    record Product(long id, String name) {}

    static class ProductNotFoundException extends RuntimeException {
        ProductNotFoundException(long id) { super("Product " + id + " not found"); }
    }

    public Mono<ServerResponse> get(ServerRequest request) {
        long id = Long.parseLong(request.pathVariable("id"));
        return Mono.<Product>justOrEmpty(id == 1 ? new Product(1, "Drill") : null)
            .switchIfEmpty(Mono.error(new ProductNotFoundException(id)))
            .flatMap(ServerResponse.ok()::bodyValue);
    }

    // Streams elements incrementally, using Flux DIRECTLY as the response body —
    // functional endpoints make this natural, since ServerResponse.body(Flux, Class)
    // is just another method call in the same fluent chain.
    public Mono<ServerResponse> stream(ServerRequest request) {
        Flux<Product> slowStream = Flux.just(new Product(1, "Drill"), new Product(2, "Hammer"))
            .delayElements(Duration.ofMillis(200));
        return ServerResponse.ok()
            .contentType(MediaType.APPLICATION_NDJSON)
            .body(slowStream, Product.class);
    }
}
```

```java
// RouteConfig.java (production version)
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.web.reactive.function.server.*;

@Configuration
public class RouteConfig {

    @Bean
    public RouterFunction<ServerResponse> allRoutes(ProductHandler handler) {
        RouterFunction<ServerResponse> productRoutes = RouterFunctions.route()
            .GET("/{id}", handler::get)
            .GET("/stream", handler::stream)
            .build()
            .filter((request, next) ->
                next.handle(request)
                    .onErrorResume(ProductHandler.ProductNotFoundException.class,
                        ex -> ServerResponse.status(HttpStatus.NOT_FOUND).bodyValue(ex.getMessage())));

        return RouterFunctions.nest(RequestPredicates.path("/api/products"), productRoutes);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/api/products/99
# HTTP/1.1 404 Not Found
# Product 99 not found

curl --no-buffer http://localhost:8080/api/products/stream
# {"id":1,"name":"Drill"}
# (pause ~200ms)
# {"id":2,"name":"Hammer"}
```

**What changed and why:**
- `.filter((request, next) -> next.handle(request).onErrorResume(...))` is the functional-endpoint equivalent of `@ExceptionHandler`/`@ControllerAdvice` — a `Mono`-returning error-recovery operator wraps the entire nested route table, catching `ProductNotFoundException` from any handler within it and converting it to a `404` response, all expressed as ordinary reactive operator composition rather than a separate annotated class.
- `ServerResponse.ok().body(slowStream, Product.class)` accepts a `Flux<Product>` **directly** as the response body — functional endpoints express streaming as naturally as any other response, since the whole API is built around reactive types from the ground up; there's no annotation-vs-streaming distinction to reason about, unlike the `produces = APPLICATION_NDJSON_VALUE` special-casing needed in the annotated-controller version.
- `RouterFunctions.nest(path("/api/products"), productRoutes)` composes the sub-route-table under a shared prefix exactly as in the MVC version of functional endpoints — this composition model, combined with the filter-based error handling, is a genuinely coherent, fully-reactive way to build an entire application's routing and cross-cutting concerns as pure, composable functions.

## 6. Walkthrough

**Request: `GET /api/products/99` (Level 3 code, triggers `ProductNotFoundException`).**

1. The request reaches `DispatcherHandler`, which delegates to the composed `RouterFunction` from `allRoutes`. `RouterFunctions.nest(path("/api/products"), productRoutes)` first checks that the path starts with `/api/products` — it does — then matches the remaining segment `/99` against `productRoutes`'s own `GET "/{id}"` predicate, binding `id = "99"`.
2. Because `productRoutes` was built with `.filter(...)`, the matched route's actual handler invocation happens *through* this filter: the filter function receives `(request, next)`, where `next` represents the underlying `handler::get` call. It invokes `next.handle(request)`, which returns a `Mono<ServerResponse>` describing the eventual result of `handler.get(request)`.
3. Inside `handler.get(request)`: `id = 99` is parsed. `Mono.justOrEmpty(id == 1 ? ... : null)` evaluates the ternary — since `id != 1`, this produces `Mono.justOrEmpty(null)`, which is an **empty** `Mono`.
4. `.switchIfEmpty(Mono.error(new ProductNotFoundException(99)))` fires, since the preceding `Mono` was empty — this replaces the empty completion with an **error** signal instead.
5. This error signal propagates up through `get`'s return value (the `flatMap(...)` after it is never reached, since the pipeline is already in an error state) and back to the `next.handle(request)` call inside the filter from step 2 — the `Mono<ServerResponse>` that `next.handle(...)` returned is itself now in an error state.
6. The filter's `.onErrorResume(ProductHandler.ProductNotFoundException.class, ex -> ServerResponse.status(HttpStatus.NOT_FOUND).bodyValue(ex.getMessage()))` intercepts this specific exception type, replacing the errored `Mono` with a new one producing a `404` `ServerResponse` carrying the exception's message as the body.
7. This recovered `Mono<ServerResponse>` is what the filter ultimately returns — becoming the actual response for this request.
8. Response:
   ```
   HTTP/1.1 404 Not Found
   Content-Type: text/plain

   Product 99 not found
   ```

## 7. Gotchas & takeaways

> **Every `HandlerFunction` must return `Mono<ServerResponse>`, never `ServerResponse` directly** — even a response built from an already-known, synchronous value still needs wrapping (`ServerResponse.ok().bodyValue(x)` itself returns a `Mono<ServerResponse>`, not a `ServerResponse`). Forgetting this and trying to return a bare `ServerResponse` simply won't compile, which at least fails loudly rather than silently.

> **`.filter(...)` on a `RouterFunction` only wraps the specific `RouterFunction` it's attached to** — exactly as in the Spring MVC version of this pattern, a filter applied to one nested route table does not automatically apply to a sibling route table composed alongside it via `.and(...)`, unless that sibling has its own filter (or a shared, outer filter wraps the whole composition).

> **`ServerResponse.body(flux, Class)` streams a `Flux` naturally, but the response's `Content-Type` must genuinely support element-by-element delivery** (`application/x-ndjson`, `text/event-stream`) for the client to observe true incremental arrival — using a plain `application/json` content type with a `Flux` body typically still buffers the full array before responding, exactly as in the annotated-controller equivalent.

- WebFlux's functional endpoints mirror Spring MVC's `RouterFunction`/`HandlerFunction` model, but every handler returns `Mono<ServerResponse>`, and the whole API embraces reactive types throughout.
- `ServerRequest.bodyToMono`/`bodyToFlux` provide fully non-blocking request body reading, composing naturally with `flatMap`-based handler logic.
- `.filter(...)` on a `RouterFunction` is the functional equivalent of `@ExceptionHandler`/`@ControllerAdvice`, using `onErrorResume` for centralized error recovery.
- Streaming a `Flux` directly as a response body is a first-class, natural operation in functional endpoints, requiring only an appropriate streaming-friendly media type.
