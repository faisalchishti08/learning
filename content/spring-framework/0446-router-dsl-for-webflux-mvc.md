---
card: spring-framework
gi: 446
slug: router-dsl-for-webflux-mvc
title: "Router DSL for WebFlux/MVC"
---

## 1. What it is

The router DSL (`router { }` for WebFlux, `router { }` for Spring MVC's functional variant too — both share the same Kotlin DSL shape) is a Kotlin-idiomatic wrapper over Spring's functional endpoint API (`RouterFunctions`/`RouterFunction<ServerResponse>`), letting you declare HTTP routes with a concise, nested block syntax instead of chaining `RouterFunctions.route(...)` calls or using `@RestController`/`@GetMapping` annotations.

```kotlin
val routes = router {
    GET("/products/{id}") { request ->
        val id = request.pathVariable("id").toLong()
        ServerResponse.ok().bodyValue(Product(id, "Laptop"))
    }
    "/admin".nest {
        GET("/stats") { ServerResponse.ok().bodyValue(mapOf("status" to "ok")) }
    }
}
```

## 2. Why & when

Spring's functional endpoint style (`RouterFunction`, covered without Kotlin in the WebFlux section of this content) is already an alternative to annotated `@RestController`s — routes described as data (a `RouterFunction`) rather than discovered via annotation scanning. Kotlin's router DSL takes that functional style and makes it read even more naturally in Kotlin: nested route grouping via `.nest { }`, trailing-lambda handlers, and no need for the more verbose `RequestPredicates.GET(...)`/`.andRoute(...)` chaining the Java functional API requires.

Reach for the router DSL when:

- You're already using Spring's functional endpoint style (rather than annotated controllers) in a Kotlin codebase, and want routes expressed in idiomatic Kotlin rather than Java-shaped functional chaining.
- You want route definitions to read as a compact, visually nested tree of paths and methods — particularly valuable for APIs with many related sub-routes under a common prefix.
- You're building a WebFlux application where routes and their handlers are meant to be easily testable as plain functions, independent of Spring's component-scanning/annotation-discovery machinery.

## 3. Core concept

```
 router {
     GET("/products/{id}") { request -> ... }        <- a single route, inline handler lambda
     "/admin".nest {                                     <- grouped routes under a shared prefix
         GET("/stats") { ... }
         POST("/reset") { ... }
     }
     accept(MediaType.APPLICATION_JSON).nest {            <- grouped routes under a shared PREDICATE
         GET("/products") { ... }
     }
 }
        |
        v
 produces a RouterFunction<ServerResponse>   <- an ordinary Spring bean, registered like any other
        |
        v
 HttpHandler / DispatcherHandler dispatches incoming requests
 by matching against this RouterFunction, same mechanism as the
 Java-style functional endpoints covered elsewhere in this content
```

Everything the DSL produces is a genuine `RouterFunction<ServerResponse>` — the DSL is purely a more pleasant way to *construct* one, not a different underlying request-dispatch mechanism.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Router DSL block compiles to a RouterFunction, dispatched by the same mechanism as Java functional endpoints">
  <rect x="10" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">router { GET(...) }</text>
  <text x="100" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Kotlin DSL</text>

  <rect x="240" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RouterFunction</text>
  <text x="330" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ordinary Spring bean</text>

  <rect x="470" y="20" width="160" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">DispatcherHandler</text>
  <text x="550" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">dispatches by route match</text>

  <line x1="190" y1="45" x2="235" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="45" x2="465" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The DSL is purely a construction convenience over the same dispatch mechanism functional endpoints already use.

## 5. Runnable example

### Level 1 — Basic

A minimal router DSL block with one GET route, tested directly against the built `RouterFunction` via `WebTestClient` (from the earlier testing card) rather than a full server.

```kotlin
import org.springframework.test.web.reactive.server.WebTestClient
import org.springframework.web.reactive.function.server.ServerResponse
import org.springframework.web.reactive.function.server.router

data class Product(val id: Long, val name: String)

fun main() {
    val routes = router {
        GET("/products/{id}") { request ->
            val id = request.pathVariable("id").toLong()
            ServerResponse.ok().bodyValue(Product(id, "Laptop"))
        }
    }

    val client = WebTestClient.bindToRouterFunction(routes).build()

    client.get().uri("/products/42")
        .exchange()
        .expectStatus().isOk
        .expectBody()
        .jsonPath("$.id").isEqualTo(42)
        .jsonPath("$.name").isEqualTo("Laptop")

    println("Router DSL route correctly handled a GET request -- PASS")
}
```

How to run: add `spring-webflux`, `spring-test`, `reactor-core`, Jackson, and the Kotlin standard library to the classpath, then `kotlinc AppConfig.kt -include-runtime -d app.jar && java -jar app.jar`.

`router { GET("/products/{id}") { request -> ... } }` builds a `RouterFunction<ServerResponse>` with one route; `request.pathVariable("id")` extracts the path variable exactly as the Java functional API's `ServerRequest.pathVariable(...)` would, since `ServerRequest`/`ServerResponse` are the same types either way — only the route-declaration syntax differs. `WebTestClient.bindToRouterFunction(routes)` tests this `RouterFunction` directly, in-memory, without needing a full application context or real server.

### Level 2 — Intermediate

`.nest { }` for grouping related routes under a shared path prefix, and a predicate-based nesting (grouping by `Accept` header) — both DSL capabilities that make a moderately-sized API's route structure visually clear.

```kotlin
import org.springframework.http.MediaType
import org.springframework.test.web.reactive.server.WebTestClient
import org.springframework.web.reactive.function.server.ServerResponse
import org.springframework.web.reactive.function.server.router

data class Product(val id: Long, val name: String)

fun main() {
    val products = mapOf(1L to Product(1, "Laptop"), 2L to Product(2, "Mouse"))

    val routes = router {
        "/products".nest {
            GET("") { ServerResponse.ok().bodyValue(products.values.toList()) }
            GET("/{id}") { request ->
                val id = request.pathVariable("id").toLong()
                val product = products[id]
                if (product != null) ServerResponse.ok().bodyValue(product)
                else ServerResponse.notFound().build()
            }
        }
        (accept(MediaType.APPLICATION_JSON) and path("/health")).nest {
            GET("") { ServerResponse.ok().bodyValue(mapOf("status" to "UP")) }
        }
    }

    val client = WebTestClient.bindToRouterFunction(routes).build()

    client.get().uri("/products").exchange().expectStatus().isOk
        .expectBody().jsonPath("$.length()").isEqualTo(2)
    println("GET /products (nested under prefix) -- PASS")

    client.get().uri("/products/2").exchange().expectStatus().isOk
        .expectBody().jsonPath("$.name").isEqualTo("Mouse")
    println("GET /products/2 (nested route with path variable) -- PASS")

    client.get().uri("/products/999").exchange().expectStatus().isNotFound
    println("GET /products/999 (not found, correctly returns 404) -- PASS")

    client.get().uri("/health").accept(MediaType.APPLICATION_JSON)
        .exchange().expectStatus().isOk
        .expectBody().jsonPath("$.status").isEqualTo("UP")
    println("GET /health (predicate-nested route) -- PASS")
}
```

How to run: same dependencies as Level 1, then compile and run identically.

`"/products".nest { GET("") { ... }; GET("/{id}") { ... } }` groups two related routes under a shared `/products` prefix, so neither inner `GET(...)` call needs to repeat that prefix — visually communicating that these routes belong together. `(accept(MediaType.APPLICATION_JSON) and path("/health")).nest { ... }` groups by a *predicate combination* rather than just a path prefix, using the same `RequestPredicate` composition (`and`, `or`) available in the Java functional API, just expressed through Kotlin's more concise DSL syntax.

### Level 3 — Advanced

Compose router DSL blocks from multiple functions (mirroring how a larger application splits routes across modules), combine the DSL with a handler class (rather than only inline lambdas) for more substantial business logic, and add a filter applied across an entire nested group — demonstrating the DSL scales to a realistic, multi-module API structure.

```kotlin
import org.springframework.http.HttpStatus
import org.springframework.test.web.reactive.server.WebTestClient
import org.springframework.web.reactive.function.server.*
import reactor.core.publisher.Mono

data class Order(val id: Long, val status: String)

class OrderHandler(private val orders: MutableMap<Long, Order>) {
    fun getOrder(request: ServerRequest): Mono<ServerResponse> {
        val id = request.pathVariable("id").toLong()
        val order = orders[id]
        return if (order != null) ServerResponse.ok().bodyValue(order)
        else ServerResponse.status(HttpStatus.NOT_FOUND).build()
    }

    fun cancelOrder(request: ServerRequest): Mono<ServerResponse> {
        val id = request.pathVariable("id").toLong()
        val order = orders[id] ?: return ServerResponse.status(HttpStatus.NOT_FOUND).build()
        orders[id] = order.copy(status = "CANCELLED")
        return ServerResponse.ok().bodyValue(orders[id]!!)
    }
}

// Splitting routes into a separate function, mirroring how a larger app organizes routes by module.
fun orderRoutes(handler: OrderHandler) = router {
    "/orders".nest {
        GET("/{id}", handler::getOrder)
        POST("/{id}/cancel", handler::cancelOrder)

        filter { request, next ->
            // A filter applied to every route WITHIN this nested group only.
            println("Filter: handling ${request.method()} ${request.path()}")
            next.handle(request)
        }
    }
}

fun healthRoutes() = router {
    GET("/health") { ServerResponse.ok().bodyValue(mapOf("status" to "UP")) }
}

fun main() {
    val orders = mutableMapOf(1L to Order(1, "PENDING"))
    val handler = OrderHandler(orders)

    // Composing multiple independently-defined router blocks into one combined RouterFunction,
    // exactly like combining multiple @Configuration classes' worth of routes.
    val allRoutes = orderRoutes(handler).and(healthRoutes())

    val client = WebTestClient.bindToRouterFunction(allRoutes).build()

    client.get().uri("/orders/1").exchange().expectStatus().isOk
        .expectBody().jsonPath("$.status").isEqualTo("PENDING")
    println("GET /orders/1 -- PASS")

    client.post().uri("/orders/1/cancel").exchange().expectStatus().isOk
        .expectBody().jsonPath("$.status").isEqualTo("CANCELLED")
    println("POST /orders/1/cancel -- PASS")

    client.get().uri("/health").exchange().expectStatus().isOk
    println("GET /health (from the separately-composed route block) -- PASS")

    println("Composed router DSL blocks, handler class methods, and a nested filter -- PASS")
}
```

How to run: same dependencies as Level 1, then compile and run identically.

`GET("/{id}", handler::getOrder)` passes a Kotlin method reference directly as the route handler — cleaner than an inline lambda once handler logic grows substantial enough to deserve its own named method on a dedicated class. `orderRoutes(handler).and(healthRoutes())` combines two independently-built `RouterFunction`s into one, exactly mirroring how multiple `@Configuration` classes' bean definitions combine into one `ApplicationContext` — route organization scales the same way configuration organization does. `filter { request, next -> ... }` nested inside the `"/orders".nest { }` block applies only to routes within that specific group, not globally — a scoped filter, analogous to registering an interceptor for just one URL pattern in the annotation-based MVC style.

## 6. Walkthrough

Trace the `POST /orders/1/cancel` request in `main()`:

1. **Request dispatch.** `client.post().uri("/orders/1/cancel").exchange()` sends a mock `POST` request; `WebTestClient` routes it through the combined `allRoutes` `RouterFunction` (built from `orderRoutes(handler).and(healthRoutes())`).
2. **Route matching.** The router evaluates registered routes in order — `orderRoutes`' `"/orders".nest { ... }` group matches the `/orders/1/cancel` path prefix, and within that group, `POST("/{id}/cancel", handler::cancelOrder)` matches both the HTTP method and the specific path pattern, extracting `id = "1"` as a path variable.
3. **Filter runs first.** Because a `filter { ... }` was registered within the same `"/orders".nest { }` block, it wraps the eventual handler invocation — it prints `"Filter: handling POST /orders/1/cancel"` and then calls `next.handle(request)`, passing control onward to the actual matched route handler.
4. **Handler method invoked.** `handler.cancelOrder(request)` runs: it parses `id = 1L` from the path variable, looks up `orders[1]` (finding `Order(1, "PENDING")`), and since it's non-null, updates the map entry to `order.copy(status = "CANCELLED")` — Kotlin's `data class` `copy()` producing a new `Order` instance with just the `status` field changed.
5. **Response built.** `ServerResponse.ok().bodyValue(orders[1]!!)` constructs a `200 OK` response with the now-updated order as its JSON body.
6. **Assertion.** `expectBody().jsonPath("$.status").isEqualTo("CANCELLED")` confirms the response body reflects the update — proving the whole chain (composed routes, nested group, scoped filter, handler-class method, mutable in-memory state update) worked correctly end to end.

```
POST /orders/1/cancel
   -> allRoutes (orderRoutes + healthRoutes, combined via .and())
   -> matches "/orders".nest { ... } group
   -> filter { } runs first: prints, calls next.handle(request)
   -> POST("/{id}/cancel", handler::cancelOrder) matches
   -> cancelOrder(request): id=1, orders[1] found, status updated to CANCELLED
   -> ServerResponse.ok().bodyValue(updated order)
   -> expectBody jsonPath("$.status") == "CANCELLED" -- PASS
```

## 7. Gotchas & takeaways

> Gotcha: `.nest { }` groups routes by a shared prefix or predicate for *declaration convenience and filter scoping*, but route matching within a `RouterFunction` still generally follows first-match-wins evaluation order across the whole composed structure — a broadly-matching route declared *before* a more specific nested group can shadow it, exactly the same ordering sensitivity the Java functional endpoint API has. When a route "should" match but doesn't seem to, checking declaration order (broader/earlier routes potentially intercepting the request first) is a useful first diagnostic step, just as it would be with the non-DSL functional API.

- The router DSL is purely a Kotlin-idiomatic construction convenience over the same `RouterFunction<ServerResponse>` and `HttpHandler`/`DispatcherHandler` dispatch mechanism the Java functional endpoint API uses — no different runtime behavior, just more pleasant declaration syntax.
- `.nest { }` groups routes by a shared path prefix or predicate, and any `filter { }` declared within a nested group applies scoped to just that group's routes, not globally.
- Router DSL blocks are ordinary functions returning `RouterFunction<ServerResponse>` values — they compose via `.and(...)`, split across multiple functions/files exactly like a larger application splits `@Configuration` classes by module.
- Handler logic can live as inline lambdas for simple cases or as named methods on a dedicated handler class (referenced via Kotlin method references) once the logic grows substantial — the DSL doesn't force everything into inline closures.
