---
card: spring-framework
gi: 337
slug: functional-endpoints-routerfunction-handlerfunction
title: "Functional endpoints (RouterFunction / HandlerFunction)"
---

## 1. What it is

Functional endpoints are an alternative to annotation-based controllers (`@RestController`/`@GetMapping`) for defining Spring MVC routes: instead of annotations, you compose a `RouterFunction<ServerResponse>` that maps request predicates (path, method, headers) to `HandlerFunction<ServerResponse>` lambdas, all in plain Java code.

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

Annotation-based controllers scatter routing information across annotations on individual methods — to see all routes for a resource, you scan every method signature in a class. Functional endpoints instead define **all** routes for a resource in one explicit, readable declaration, with routing logic expressed as regular Java code (composable, testable without a servlet container, easy to conditionally build up).

Use functional endpoints when:
- You want the entire route table for a module visible in one place, rather than distributed across annotated methods.
- Routing needs to be built conditionally or programmatically (e.g. different subsets of routes registered based on configuration/feature flags).
- You're already comfortable with a more functional, composition-based style and want routing and handling logic cleanly separated (`RouterFunction` for routing, `HandlerFunction` for handling).
- You're working in a reactive (WebFlux) codebase, where functional endpoints are equally supported and quite common — the same mental model applies to MVC's Servlet-based version.

For most everyday CRUD APIs, `@RestController`/`@RequestMapping` remains simpler and more familiar to most teams — functional endpoints are a deliberate style choice, not a strict upgrade.

## 3. Core concept

```
RouterFunction<ServerResponse>: a composable chain of
  (predicate: RequestPredicate) -> (handler: HandlerFunction)

RouterFunctions.route()
    .GET("/products/{id}", handler::get)      <- predicate: GET + path match
    .POST("/products", handler::create)       <- predicate: POST + path match
    .GET("/products", handler::list)
    .build()

Incoming request
      |
      v
Each route's predicate tested in declaration order
      |
      v
First matching predicate's HandlerFunction is invoked
      |
      v
HandlerFunction: (ServerRequest) -> ServerResponse
      |
      v
ServerResponse built explicitly: ServerResponse.ok().body(product)

No annotations involved anywhere in this chain — routing IS the code.
```

`HandlerFunction<ServerResponse>` is a functional interface (`ServerRequest -> ServerResponse`), so handler logic is naturally testable as a plain function call, with no servlet mocking required.

## 4. Diagram

<svg viewBox="0 0 720 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="220" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">RouterFunction: predicate chain to HandlerFunction</text>

  <rect x="20" y="50" width="180" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="80" text-anchor="middle" fill="#79c0ff" font-size="11">GET /products/1</text>

  <line x1="200" y1="75" x2="260" y2="75" stroke="#8b949e" marker-end="url(#a13)"/>

  <rect x="260" y="50" width="400" height="120" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="460" y="70" text-anchor="middle" fill="#8b949e" font-size="10">RouterFunction (tested top to bottom)</text>
  <text x="280" y="92" fill="#6db33f" font-size="10">GET  /products/{id} -&gt; handler::get      ✓ match</text>
  <text x="280" y="112" fill="#8b949e" font-size="10">POST /products       -&gt; handler::create</text>
  <text x="280" y="132" fill="#8b949e" font-size="10">GET  /products        -&gt; handler::list</text>

  <line x1="460" y1="170" x2="460" y2="195" stroke="#6db33f" marker-end="url(#a13)"/>
  <rect x="330" y="195" width="260" height="1" fill="none"/>
  <text x="460" y="205" text-anchor="middle" fill="#6db33f" font-size="11">handler.get(request) -&gt; ServerResponse.ok().body(product)</text>

  <defs>
    <marker id="a13" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Route predicates are checked in order; the first match's handler function builds the response explicitly.*

## 5. Runnable example

### Level 1 — Basic

A minimal functional endpoint for reading a product:

```java
// ProductHandler.java
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.function.ServerRequest;
import org.springframework.web.servlet.function.ServerResponse;

@Component
public class ProductHandler {

    record Product(long id, String name) {}

    public ServerResponse get(ServerRequest request) {
        long id = Long.parseLong(request.pathVariable("id"));
        Product product = new Product(id, "Drill");
        return ServerResponse.ok().body(product);
    }
}
```

```java
// RouteConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.function.RouterFunction;
import org.springframework.web.servlet.function.RouterFunctions;
import org.springframework.web.servlet.function.ServerResponse;

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

No `@RestController`, no `@GetMapping` anywhere — the route is declared explicitly in `RouteConfig`, and `handler::get` is just a method reference matching `HandlerFunction`'s signature (`ServerRequest -> ServerResponse`).

### Level 2 — Intermediate

A full CRUD route table, request body parsing, and composed predicates (path + `Accept` header):

```java
// ProductHandler.java (extended)
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.function.ServerRequest;
import org.springframework.web.servlet.function.ServerResponse;

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

    public ServerResponse list(ServerRequest request) {
        return ServerResponse.ok().body(store.values());
    }

    public ServerResponse get(ServerRequest request) {
        long id = Long.parseLong(request.pathVariable("id"));
        Product p = store.get(id);
        return p != null ? ServerResponse.ok().body(p) : ServerResponse.notFound().build();
    }

    public ServerResponse create(ServerRequest request) throws Exception {
        ProductRequest req = request.body(ProductRequest.class);
        long id = seq.getAndIncrement();
        Product p = new Product(id, req.name(), req.price());
        store.put(id, p);
        return ServerResponse.status(HttpStatus.CREATED)
            .location(URI.create("/api/products/" + id))
            .body(p);
    }

    public ServerResponse delete(ServerRequest request) {
        long id = Long.parseLong(request.pathVariable("id"));
        return store.remove(id) != null ? ServerResponse.noContent().build() : ServerResponse.notFound().build();
    }
}
```

```java
// RouteConfig.java (extended)
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.MediaType;
import org.springframework.web.servlet.function.RouterFunction;
import org.springframework.web.servlet.function.RouterFunctions;
import org.springframework.web.servlet.function.ServerResponse;

@Configuration
public class RouteConfig {

    @Bean
    public RouterFunction<ServerResponse> productRoutes(ProductHandler handler) {
        return RouterFunctions.route()
            .GET("/api/products", accept(MediaType.APPLICATION_JSON), handler::list)
            .GET("/api/products/{id}", handler::get)
            .POST("/api/products", handler::create)
            .DELETE("/api/products/{id}", handler::delete)
            .build();
    }

    private static org.springframework.web.servlet.function.RequestPredicate accept(MediaType type) {
        return org.springframework.web.servlet.function.RequestPredicates.accept(type);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -X POST http://localhost:8080/api/products -H "Content-Type: application/json" -d '{"name":"Drill","price":29.99}'
# 201 Created
# Location: /api/products/1
# {"id":1,"name":"Drill","price":29.99}

curl -H "Accept: application/json" http://localhost:8080/api/products
# [{"id":1,"name":"Drill","price":29.99}]

curl -i -X DELETE http://localhost:8080/api/products/1
# 204 No Content
```

**What changed:** `RequestPredicates.accept(...)` composes with the path/method predicate — the `list` route now only matches requests that also declare `Accept: application/json`. `request.body(ProductRequest.class)` explicitly deserializes the request body (equivalent to `@RequestBody`, but called imperatively). Building the `Location` header and status is done with the same fluent `ServerResponse` builder used for every response.

### Level 3 — Advanced

Production pattern: separating routes into multiple `RouterFunction` beans composed together, nested routing under a shared path prefix, and centralized error handling via `.filter(...)`:

```java
// ProductHandler.java (production version, error handling via exceptions)
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.function.ServerRequest;
import org.springframework.web.servlet.function.ServerResponse;

@Component
public class ProductHandler {

    record Product(long id, String name) {}
    static class ProductNotFoundException extends RuntimeException {
        ProductNotFoundException(long id) { super("Product " + id + " not found"); }
    }

    public ServerResponse get(ServerRequest request) {
        long id = Long.parseLong(request.pathVariable("id"));
        if (id != 1) throw new ProductNotFoundException(id);
        return ServerResponse.ok().body(new Product(1, "Drill"));
    }
}
```

```java
// AdminHandler.java — a separate resource, its own handler
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.function.ServerRequest;
import org.springframework.web.servlet.function.ServerResponse;

@Component
public class AdminHandler {
    public ServerResponse stats(ServerRequest request) {
        return ServerResponse.ok().body(java.util.Map.of("uptime", "3h12m"));
    }
}
```

```java
// RouteConfig.java (production version)
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.web.servlet.function.*;

@Configuration
public class RouteConfig {

    @Bean
    public RouterFunction<ServerResponse> productRoutes(ProductHandler handler) {
        return RouterFunctions.route()
            .GET("/{id}", handler::get)
            .build()
            .filter((request, next) -> {
                try {
                    return next.handle(request);
                } catch (ProductHandler.ProductNotFoundException ex) {
                    return ServerResponse.status(HttpStatus.NOT_FOUND).body(ex.getMessage());
                }
            });
    }

    @Bean
    public RouterFunction<ServerResponse> adminRoutes(AdminHandler handler) {
        return RouterFunctions.route()
            .GET("/stats", handler::stats)
            .build();
    }

    // Compose independently-defined RouterFunctions under shared path prefixes
    @Bean
    public RouterFunction<ServerResponse> allRoutes(RouterFunction<ServerResponse> productRoutes,
                                                      RouterFunction<ServerResponse> adminRoutes) {
        return RouterFunctions.nest(RequestPredicates.path("/api/products"), productRoutes)
            .and(RouterFunctions.nest(RequestPredicates.path("/api/admin"), adminRoutes));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/api/products/1
# {"id":1,"name":"Drill"}

curl -i http://localhost:8080/api/products/99
# 404 Not Found
# Product 99 not found

curl http://localhost:8080/api/admin/stats
# {"uptime":"3h12m"}
```

**What changed and why:**
- `RouterFunctions.nest(path, routerFunction)` lets each resource's routes be defined relative to its own base path (`ProductHandler`'s routes just say `"/{id}"`, not `"/api/products/{id}"`) and composed together in `allRoutes` — this mirrors how `@RequestMapping` at the class level provides a shared prefix, but here it's explicit function composition instead of an annotation.
- `.filter((request, next) -> ...)` wraps a `RouterFunction` with cross-cutting behavior — here, catching a domain exception and converting it to a `404` response — the functional equivalent of an `@ExceptionHandler`/`@ControllerAdvice`, expressed as a composable function instead of annotated methods.
- Splitting `productRoutes` and `adminRoutes` into separate beans keeps each resource's routing table small and focused, while `allRoutes` is the single place that shows how they're all wired together — valuable in a codebase with many resources.

## 6. Walkthrough

**Request: `GET /api/products/99` (Level 3 code, id doesn't exist).**

1. The servlet container hands the request to Spring MVC's `DispatcherServlet`, which for functional endpoints delegates matching to the composed `RouterFunction` (built by `allRoutes`).
2. `RouterFunctions.nest(path("/api/products"), productRoutes)` first checks whether the request path starts with `/api/products` — it does. The remaining path segment `/99` is then matched against `productRoutes`'s own predicates, which declare `GET "/{id}"`. This matches, binding `id = "99"`.
3. Because `productRoutes` was built with `.filter(...)`, every matched request actually flows through the filter function first: `(request, next) -> { try { return next.handle(request); } catch (...) { ... } }`. The filter calls `next.handle(request)`, which invokes the *actual* route's handler — `handler::get`.
4. Inside `get(request)`: `request.pathVariable("id")` returns `"99"`, parsed to `99L`. Since `99 != 1`, throws `new ProductNotFoundException(99)`.
5. This exception propagates back out of `next.handle(request)` inside the filter — caught by the filter's `catch (ProductHandler.ProductNotFoundException ex)` block.
6. The filter builds and returns `ServerResponse.status(NOT_FOUND).body("Product 99 not found")` directly — this becomes the final response, since it's what the filter (wrapping the whole route) returns.
7. Response sent to the client:
   ```
   HTTP/1.1 404 Not Found
   Content-Type: text/plain

   Product 99 not found
   ```

**Request: `GET /api/admin/stats`.**

1. `allRoutes` checks `RouterFunctions.nest(path("/api/products"), ...)` first — path doesn't start with `/api/products`, no match. Falls through to `.and(RouterFunctions.nest(path("/api/admin"), adminRoutes))` — path starts with `/api/admin`, remaining segment `/stats` matches `adminRoutes`'s `GET "/stats"` predicate.
2. `handler::stats` (in `AdminHandler`) is invoked directly — no filter wraps this route, so no exception-catching layer applies here (illustrating that filters are opt-in per composed `RouterFunction`, not automatically global).
3. Returns `ServerResponse.ok().body(Map.of("uptime", "3h12m"))`, serialized to JSON:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   {"uptime":"3h12m"}
   ```

## 7. Gotchas & takeaways

> **Route order matters, and there's no annotation-based "most specific wins" resolution like `@RequestMapping` has.** `RouterFunctions.route()` tests predicates in the exact order they're declared — a broad predicate declared before a narrow one can shadow it entirely. Always order routes from most specific to least specific.

> **`.filter(...)` only wraps the `RouterFunction` it's attached to.** In the Level 3 example, the exception-catching filter is on `productRoutes` only — `adminRoutes` has no such filter, so an exception thrown inside `AdminHandler.stats` would propagate unhandled (falling back to Spring Boot's default error page) unless a filter or global exception handling is added there too.

> **Mixing functional endpoints and annotation-based `@RestController`s in the same application works fine**, but mixing styles within what should be one cohesive resource's API creates confusion about where to look for a given route — pick one style per resource/module, even if the application as a whole uses both.

- `RouterFunction<ServerResponse>` maps request predicates to `HandlerFunction<ServerResponse>` — routing table and handler logic are both plain Java, not annotations.
- `RouterFunctions.nest(path, routerFunction)` composes sub-route-tables under a shared path prefix, similar in spirit to a class-level `@RequestMapping`.
- `.filter(...)` is the functional-endpoint equivalent of a servlet filter/`@ControllerAdvice` — cross-cutting behavior wrapped explicitly around a route table.
- Functional endpoints shine when you want the full route table visible in one place or need to build routing programmatically; annotation-based controllers remain simpler for typical CRUD APIs.
