---
card: spring-framework
gi: 370
slug: webflux-vs-webmvc-comparison
title: "WebFlux vs WebMVC comparison"
---

## 1. What it is

Spring WebFlux and Spring MVC are two parallel, largely API-compatible web frameworks within Spring — WebMVC is the original, Servlet-API-based, imperative/blocking framework; WebFlux is the newer, reactive, non-blocking framework built on the Reactive Streams specification, capable of running on either a Servlet 3.1+ container or a fully non-Servlet, reactive server like Netty. This card compares them concretely, side by side, at the framework-mechanics level (building on the previous card's higher-level tradeoff discussion).

```java
// Spring MVC controller
@RestController
public class ProductController {
    @GetMapping("/products/{id}")
    public Product get(@PathVariable long id) { ... }   // returns T directly
}

// Spring WebFlux controller — nearly IDENTICAL annotations, different return type
@RestController
public class ProductController {
    @GetMapping("/products/{id}")
    public Mono<Product> get(@PathVariable long id) { ... }   // returns Mono<T>
}
```

## 2. Why & when

Spring deliberately kept WebFlux's annotation-based programming model (`@RestController`, `@GetMapping`, `@PathVariable`, etc.) nearly identical to WebMVC's — the main visible difference in typical controller code is swapping direct return types (`Product`, `List<Product>`) for their reactive equivalents (`Mono<Product>`, `Flux<Product>`). This design choice deliberately minimizes the *syntactic* learning curve, even though the *underlying execution model* and *architectural implications* differ substantially — understanding exactly where they're similar and where they genuinely diverge is essential for making an informed choice (the previous card) and avoiding subtle mistakes when working in either.

## 3. Core concept

```
                         Spring MVC              Spring WebFlux
──────────────────────────────────────────────────────────────────────
Underlying spec           Servlet API              Reactive Streams
Server options             Tomcat, Jetty,           Netty (default),
                            Undertow (Servlet)        Tomcat, Jetty,
                                                       Undertow (all
                                                       via reactive adapters)
Controller return type     T, List<T>,               Mono<T>, Flux<T>
                            ResponseEntity<T>          Mono<ResponseEntity<T>>
Request body binding       @RequestBody T             @RequestBody Mono<T>
                                                        (or T directly, buffered)
Programming styles         annotation-based           BOTH annotation-based
 available                  ONLY                        AND functional
                                                          (RouterFunction)
Database access             JDBC, JPA (blocking)       R2DBC (non-blocking)
                                                          for full reactive benefit
Thread model                thread-per-request          small event-loop pool
Testing                     MockMvc                     WebTestClient

WHAT'S THE SAME:
  @GetMapping/@PostMapping/etc., @PathVariable, @RequestParam,
  @Valid, @ExceptionHandler, @ControllerAdvice — virtually
  IDENTICAL annotations and semantics across both frameworks
```

## 4. Diagram

<svg viewBox="0 0 740 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="220" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">Same annotations, different execution models underneath</text>

  <rect x="20" y="50" width="330" height="60" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="185" y="75" text-anchor="middle" fill="#e6edf3" font-size="11">@GetMapping / @PathVariable / @Valid</text>
  <text x="185" y="93" text-anchor="middle" fill="#8b949e" font-size="9">SHARED annotation vocabulary</text>

  <rect x="390" y="50" width="330" height="60" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="555" y="75" text-anchor="middle" fill="#e6edf3" font-size="11">@ExceptionHandler / @ControllerAdvice</text>
  <text x="555" y="93" text-anchor="middle" fill="#8b949e" font-size="9">SHARED annotation vocabulary</text>

  <rect x="20" y="130" width="330" height="60" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="185" y="155" text-anchor="middle" fill="#79c0ff" font-size="11">Servlet API, thread-per-request</text>
  <text x="185" y="173" text-anchor="middle" fill="#8b949e" font-size="9">WebMVC underneath</text>

  <rect x="390" y="130" width="330" height="60" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="555" y="155" text-anchor="middle" fill="#6db33f" font-size="11">Reactive Streams, event-loop</text>
  <text x="555" y="173" text-anchor="middle" fill="#8b949e" font-size="9">WebFlux underneath</text>

  <defs>
    <marker id="a46" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The annotation-based programming model is nearly identical; the execution model underneath differs completely.*

## 5. Runnable example

### Level 1 — Basic

The same product resource implemented in both frameworks side by side, highlighting exactly what changes and what stays the same:

```xml
<!-- pom.xml — MVC variant -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
```

```java
// ProductController.java — Spring MVC
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    record Product(long id, String name) {}

    @GetMapping("/products/{id}")
    public Product get(@PathVariable long id) {
        return new Product(id, "Drill");
    }
}
```

```xml
<!-- pom.xml — WebFlux variant (a SEPARATE project/module) -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-webflux</artifactId>
</dependency>
```

```java
// ProductController.java — Spring WebFlux
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
# MVC variant
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# {"id":1,"name":"Drill"}

# WebFlux variant (separate project, different starter dependency)
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# {"id":1,"name":"Drill"}     <- IDENTICAL response, IDENTICAL client-visible behavior
```

Every annotation (`@RestController`, `@GetMapping`, `@PathVariable`) is used identically in both versions — the only code difference is the return type (`Product` vs `Mono<Product>`) and how the value is constructed (`new Product(...)` directly vs `Mono.just(new Product(...))`). Both starters (`spring-boot-starter-web` and `spring-boot-starter-webflux`) are mutually exclusive within one application — you choose one framework per application, not both simultaneously for the same controllers.

### Level 2 — Intermediate

A collection endpoint (`Flux<T>` vs `List<T>`) and request body handling, showing how the reactive types propagate through the whole request/response cycle:

```java
// ProductController.java — Spring MVC
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
public class ProductController {

    record Product(long id, String name, double price) {}

    @GetMapping("/products")
    public List<Product> list() {
        return List.of(new Product(1, "Drill", 29.99), new Product(2, "Hammer", 14.99));
    }

    @PostMapping("/products")
    public Product create(@RequestBody Product product) {
        return product;   // blocks until the FULL request body is read
    }
}
```

```java
// ProductController.java — Spring WebFlux
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {

    record Product(long id, String name, double price) {}

    @GetMapping("/products")
    public Flux<Product> list() {
        return Flux.just(new Product(1, "Drill", 29.99), new Product(2, "Hammer", 14.99));
    }

    @PostMapping("/products")
    public Mono<Product> create(@RequestBody Mono<Product> product) {
        // The BODY ITSELF is reactive too — this doesn't block waiting for bytes to arrive;
        // it describes "when the body eventually arrives, do this."
        return product.map(p -> p);
    }
}
```

**How to run (WebFlux variant):**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products
# [{"id":1,"name":"Drill","price":29.99},{"id":2,"name":"Hammer","price":14.99}]

curl -X POST http://localhost:8080/products -H "Content-Type: application/json" -d '{"id":3,"name":"Nail","price":0.50}'
# {"id":3,"name":"Nail","price":0.50}
```

**What changed:** `Flux<Product>` replaces `List<Product>` for the collection endpoint — from the client's perspective, both produce identical JSON array output, but internally WebFlux can stream the `Flux`'s elements as they become available (useful for large or slowly-generated collections) rather than requiring the whole list to be assembled in memory first, as WebMVC's `List<T>` inherently does. `@RequestBody Mono<Product>` similarly makes the *incoming* body reactive — the framework doesn't block a thread waiting for the request body's bytes to fully arrive over the network; it processes them as they stream in.

### Level 3 — Advanced

Testing each framework with its dedicated test client (`MockMvc` vs `WebTestClient`), and a functional-endpoint-style WebFlux alternative to the annotation-based style (foreshadowing the dedicated Functional Endpoints card) — demonstrating that WebFlux, unlike WebMVC, offers a genuine second programming model, not just annotations:

```java
// ProductControllerTest.java — Spring MVC testing
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class ProductControllerTest {

    @Autowired MockMvc mockMvc;

    @Test
    void getReturnsProduct() throws Exception {
        mockMvc.perform(get("/products/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("Drill"));
    }
}
```

```java
// ProductControllerTest.java — Spring WebFlux testing
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.reactive.server.WebTestClient;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class ProductControllerTest {

    @Autowired WebTestClient webTestClient;

    @Test
    void getReturnsProduct() {
        webTestClient.get().uri("/products/1")
            .exchange()
            .expectStatus().isOk()
            .expectBody()
            .jsonPath("$.name").isEqualTo("Drill");
    }
}
```

```java
// RouteConfig.java — WebFlux's SECOND programming model: functional endpoints
// (Spring MVC ALSO has functional endpoints — see the corresponding earlier card —
//  but they are far more central to WebFlux's identity and commonly used there)
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.server.RouterFunction;
import org.springframework.web.reactive.function.server.RouterFunctions;
import org.springframework.web.reactive.function.server.ServerResponse;
import reactor.core.publisher.Mono;

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
./mvnw test
# both MockMvc and WebTestClient tests pass, using EACH framework's own dedicated test tooling

./mvnw spring-boot:run
curl http://localhost:8080/functional/products/1
# {"id":1,"name":"Drill"}     <- SAME data, via WebFlux's functional (non-annotation) style
```

**What changed and why:**
- `MockMvc` (Spring MVC's test client) performs *synchronous* mock requests, matching the blocking nature of the framework under test; `WebTestClient` (WebFlux's test client) is built around the reactive `exchange()`/`expectStatus()`/`expectBody()` chain, matching WebFlux's asynchronous model — each framework's testing approach mirrors its underlying execution model, and mixing them (using `MockMvc` against a WebFlux app, for instance) doesn't work correctly.
- `RouterFunction`-based functional endpoints are available in *both* WebMVC and WebFlux (an earlier card covered the MVC version), but they're a much more prominent, commonly-used alternative specifically within the WebFlux ecosystem — many WebFlux-focused examples and tutorials default to this style, whereas MVC code overwhelmingly favors annotations. Both frameworks support both styles, but community convention differs.
- `WebTestClient` can also be used to test a running WebFlux application over real HTTP (not just mocked dispatch), and — notably — can even test a Spring MVC application, since it's fundamentally an HTTP client wrapper; the reverse (using `MockMvc` against WebFlux) is not supported, since `MockMvc` is fundamentally built around the Servlet API's mock request/response objects, which WebFlux doesn't use at all.

## 6. Walkthrough

**Request: `GET /products/1` against the Spring WebFlux variant (Level 1 code).**

1. The request arrives at the embedded server — by default, Netty for a WebFlux application (unless explicitly configured otherwise), which is itself built on a non-blocking, event-loop I/O model, distinct from the Servlet-API-based Tomcat that Spring MVC typically uses.
2. Instead of `DispatcherServlet` (Spring MVC's central dispatcher, tied to the Servlet API), WebFlux uses `DispatcherHandler` — a conceptually parallel but Reactive-Streams-native central dispatcher (covered in its own dedicated card later in this section).
3. `DispatcherHandler` resolves the request to `ProductController.get(1)` using the same `RequestMappingHandlerMapping`-style matching logic as Spring MVC (the annotation-processing infrastructure is deliberately shared/parallel between the two frameworks).
4. `get(1)` executes, returning `Mono.just(new Product(1, "Drill"))` — this `Mono` is *not* immediately resolved; it's handed back to `DispatcherHandler` as a description of the eventual response.
5. `DispatcherHandler` subscribes to this `Mono`. Because `Mono.just(...)` wraps an already-known value, the subscription resolves essentially instantly — but architecturally, this subscription-based resolution is what allows a *slower* `Mono` (backed by a genuine non-blocking database call, for instance) to work identically, without the calling code needing any different handling.
6. Once the `Product` value is available, WebFlux's response-writing machinery serializes it to JSON via Jackson (the same JSON serialization library WebMVC uses, applied through WebFlux's own reactive-aware message writer abstraction) and writes it to the response — again, using Netty's non-blocking I/O to write the response bytes without blocking any thread on the write operation itself.
7. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   {"id":1,"name":"Drill"}
   ```

Every step in this flow has a direct structural parallel in Spring MVC's request handling (`DispatcherServlet` instead of `DispatcherHandler`, `HandlerMapping` shared in spirit, Jackson serialization identical) — the deliberate architectural symmetry between the two frameworks is what makes learning WebFlux, for a developer already familiar with Spring MVC, primarily about understanding the *reactive execution model*, not about learning an entirely unfamiliar annotation vocabulary from scratch.

## 7. Gotchas & takeaways

> **You cannot mix `spring-boot-starter-web` and `spring-boot-starter-webflux` in the same application expecting both frameworks to coexist for the same controllers** — including both dependencies typically causes Spring Boot's autoconfiguration to favor one (usually MVC, if both are present) and can produce confusing, hard-to-diagnose startup or routing issues. Choose one framework per application (though a large system can certainly have *some* services built with MVC and others with WebFlux, as separate applications).

> **`@RequestBody Mono<Product>` and `@RequestBody Product` are both valid in WebFlux, but behave differently** — the `Mono<Product>` form preserves full non-blocking behavior all the way through body reading; the plain `Product` form still works (WebFlux buffers the body internally before handing it to your handler) but forfeits some of the non-blocking benefit for that specific binding, since the framework must fully materialize the object before your method can even be called.

> **`MockMvc` and `WebTestClient` are not interchangeable — `MockMvc` only works against Spring MVC (Servlet-API-based) applications**, while `WebTestClient` works against both WebFlux applications directly and any application (including Spring MVC) over real HTTP. Attempting to use `MockMvc` in a WebFlux-only project (with no Servlet API present at all) simply won't have the necessary infrastructure to function.

- Spring WebFlux and Spring MVC share a nearly identical annotation-based programming model (`@RestController`, `@GetMapping`, `@PathVariable`, `@Valid`, `@ExceptionHandler`) — the primary code-level difference is reactive return/parameter types (`Mono`/`Flux`) versus direct types.
- The underlying execution model differs completely: Servlet-API-based, thread-per-request (MVC) versus Reactive-Streams-based, event-loop (WebFlux) — this is invisible in simple examples but has major implications under real load, and for which server/database drivers you can use.
- WebFlux offers a genuine second, commonly-used programming style (functional endpoints via `RouterFunction`) more prominently than MVC does, though MVC supports the equivalent pattern too.
- Choose one framework per application; use each framework's own dedicated test client (`MockMvc` for MVC, `WebTestClient` for WebFlux) rather than attempting to mix them.
