---
card: spring-framework
gi: 371
slug: annotated-controllers-reactive
title: "Annotated controllers (reactive)"
---

## 1. What it is

Reactive annotated controllers are Spring WebFlux's `@RestController`/`@Controller` classes, using the same `@GetMapping`/`@PostMapping`/`@PathVariable`/`@RequestParam` family of annotations as Spring MVC, but with handler methods returning `Mono<T>`/`Flux<T>` (or, less commonly, other Reactive-Streams-compatible types) instead of direct values — this card focuses specifically and practically on writing these controllers, building on the conceptual comparison from the previous card.

```java
@RestController
@RequestMapping("/api/products")
public class ProductController {

    @GetMapping("/{id}")
    public Mono<Product> get(@PathVariable long id) {
        return productRepository.findById(id);
    }

    @GetMapping
    public Flux<Product> list() {
        return productRepository.findAll();
    }
}
```

## 2. Why & when

If your team already knows Spring MVC's annotation-based controller style, reactive annotated controllers are the lowest-friction entry point into WebFlux — the routing, argument resolution, and validation annotations behave almost identically, so most of what transfers is genuinely transferable knowledge, not just superficially similar syntax. Use this style (rather than functional endpoints, covered next) when:

- Your team's existing mental model and tooling familiarity are built around Spring MVC's annotation conventions.
- You want IDE support (navigate-to-mapping, endpoint discovery tooling) that's typically stronger for annotation-based routing than for functional route tables.
- The application mixes reactive and traditional concerns in ways that benefit from the same `@ExceptionHandler`/`@ControllerAdvice`/`@Valid` machinery already familiar from MVC.

## 3. Core concept

```
Return type mapping (Spring MVC -> Spring WebFlux):

  T                    -> Mono<T>
  List<T>              -> Flux<T>
  ResponseEntity<T>     -> Mono<ResponseEntity<T>>
  void (just a status)  -> Mono<Void>

Parameter binding — LARGELY IDENTICAL:

  @PathVariable long id              — SAME in both
  @RequestParam String query          — SAME in both
  @RequestBody Product product         — WebFlux ALSO supports @RequestBody Mono<Product>
                                          for full non-blocking body reading
  @Valid @RequestBody Product product  — SAME validation annotations, SAME BindingResult
                                          semantics (Errors/BindingResult must immediately follow)

Handler method body — the KEY difference:

  MVC: imperative code, can call blocking methods freely
  WebFlux: build a REACTIVE PIPELINE (map/flatMap/etc.), never
           call a blocking method directly without isolating it
           (see the imperative-vs-reactive trade-offs card)
```

## 4. Diagram

<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="200" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Return-type swap: the visible surface of reactive controllers</text>

  <rect x="20" y="50" width="320" height="70" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="180" y="72" text-anchor="middle" fill="#79c0ff" font-size="11">public Product get(...)</text>
  <text x="180" y="92" text-anchor="middle" fill="#8b949e" font-size="9">Spring MVC: direct value</text>

  <rect x="380" y="50" width="320" height="70" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="540" y="72" text-anchor="middle" fill="#6db33f" font-size="11">public Mono&lt;Product&gt; get(...)</text>
  <text x="540" y="92" text-anchor="middle" fill="#8b949e" font-size="9">WebFlux: reactive wrapper</text>

  <text x="360" y="150" text-anchor="middle" fill="#8b949e" font-size="10">@GetMapping, @PathVariable, @Valid, @ExceptionHandler — IDENTICAL either way</text>

  <defs>
    <marker id="a47" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The annotation vocabulary is shared; only the return type and internal method body genuinely change.*

## 5. Runnable example

### Level 1 — Basic

A minimal reactive CRUD controller backed by an in-memory reactive-style store:

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@RestController
@RequestMapping("/api/products")
public class ProductController {

    record Product(long id, String name, double price) {}

    private final Map<Long, Product> store = new ConcurrentHashMap<>();
    private final AtomicLong seq = new AtomicLong(1);

    @GetMapping("/{id}")
    public Mono<Product> get(@PathVariable long id) {
        return Mono.justOrEmpty(store.get(id));
    }

    @GetMapping
    public Flux<Product> list() {
        return Flux.fromIterable(store.values());
    }

    @PostMapping
    public Mono<Product> create(@RequestBody Product request) {
        long id = seq.getAndIncrement();
        Product product = new Product(id, request.name(), request.price());
        store.put(id, product);
        return Mono.just(product);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -X POST http://localhost:8080/api/products -H "Content-Type: application/json" -d '{"name":"Drill","price":29.99}'
# {"id":1,"name":"Drill","price":29.99}

curl http://localhost:8080/api/products/1
# {"id":1,"name":"Drill","price":29.99}

curl http://localhost:8080/api/products
# [{"id":1,"name":"Drill","price":29.99}]
```

`Mono.justOrEmpty(...)` handles the "might not exist" case — if `store.get(id)` returns `null`, the resulting `Mono` completes empty (equivalent to a `404` via WebFlux's default handling for an empty `Mono` from a `@GetMapping`), without needing an explicit `Optional`-style null check in the handler body.

### Level 2 — Intermediate

Validation, `ResponseEntity`, and status-code control — showing these MVC-familiar patterns translate directly, wrapped in `Mono`:

```java
// ProductController.java (extended)
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.net.URI;

@RestController
@RequestMapping("/api/products")
public class ProductController {

    record ProductRequest(@NotBlank String name, @Positive double price) {}
    record Product(long id, String name, double price) {}

    private final java.util.Map<Long, Product> store = new java.util.concurrent.ConcurrentHashMap<>();
    private final java.util.concurrent.atomic.AtomicLong seq = new java.util.concurrent.atomic.AtomicLong(1);

    @PostMapping
    public Mono<ResponseEntity<Product>> create(@Valid @RequestBody Mono<ProductRequest> requestMono) {
        return requestMono.map(request -> {
            long id = seq.getAndIncrement();
            Product product = new Product(id, request.name(), request.price());
            store.put(id, product);
            return ResponseEntity.created(URI.create("/api/products/" + id)).body(product);
        });
    }

    @GetMapping("/{id}")
    public Mono<ResponseEntity<Product>> get(@PathVariable long id) {
        return Mono.justOrEmpty(store.get(id))
            .map(ResponseEntity::ok)
            .defaultIfEmpty(ResponseEntity.status(HttpStatus.NOT_FOUND).build());
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -X POST http://localhost:8080/api/products -H "Content-Type: application/json" -d '{"name":"Drill","price":29.99}'
# HTTP/1.1 201 Created
# Location: /api/products/1

curl -i http://localhost:8080/api/products/99
# HTTP/1.1 404 Not Found
```

**What changed:** `@Valid @RequestBody Mono<ProductRequest>` combines full non-blocking body reading with Bean Validation — validation runs once the body actually arrives and is deserialized, still without blocking any thread while waiting for those bytes. `Mono<ResponseEntity<Product>>` mirrors MVC's `ResponseEntity<Product>` pattern exactly, just wrapped — `defaultIfEmpty(...)` is the reactive idiom for "if the Mono completed with nothing, use this fallback instead," here producing a `404` when the lookup misses.

### Level 3 — Advanced

Production concern: exception handling (`@ExceptionHandler`/`@ControllerAdvice`, identical to MVC in structure) combined with a genuinely non-blocking downstream call, and streaming a `Flux` response incrementally rather than buffering it entirely:

```java
// GlobalExceptionHandler.java — IDENTICAL structure to the Spring MVC version
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    static class ProductNotFoundException extends RuntimeException {
        ProductNotFoundException(long id) { super("Product " + id + " not found"); }
    }

    @ExceptionHandler(ProductNotFoundException.class)
    public ProblemDetail handleNotFound(ProductNotFoundException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
    }
}
```

```java
// ProductController.java (production version)
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;

@RestController
@RequestMapping("/api/products")
public class ProductController {

    record Product(long id, String name, double price) {}

    private final ProductRepository repository;
    public ProductController(ProductRepository repository) { this.repository = repository; }

    @GetMapping("/{id}")
    public Mono<Product> get(@PathVariable long id) {
        return repository.findById(id)
            .switchIfEmpty(Mono.error(new GlobalExceptionHandler.ProductNotFoundException(id)));
    }

    // Streams results AS THEY ARRIVE from a slow source — the client starts
    // receiving JSON array elements progressively, not all at once at the end.
    @GetMapping(value = "/stream", produces = MediaType.APPLICATION_NDJSON_VALUE)
    public Flux<Product> stream() {
        return repository.findAll()
            .delayElements(Duration.ofMillis(200));   // simulates a slow, incrementally-arriving source
    }

    interface ProductRepository {
        Mono<Product> findById(long id);
        Flux<Product> findAll();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/api/products/99
# HTTP/1.1 404 Not Found
# Content-Type: application/problem+json
# {"status":404,"detail":"Product 99 not found"}

curl --no-buffer http://localhost:8080/api/products/stream
# {"id":1,"name":"Drill","price":29.99}
# (pause ~200ms)
# {"id":2,"name":"Hammer","price":14.99}
# (pause ~200ms)
# ... each JSON object arrives as a SEPARATE line, as it becomes available,
#     rather than the client waiting for the ENTIRE collection to buffer first
```

**What changed and why:**
- `switchIfEmpty(Mono.error(...))` is the reactive idiom for "if this Mono completes empty, treat that as an error instead" — replacing an imperative `if (result == null) throw ...` check. The thrown `ProductNotFoundException` then flows through `@ExceptionHandler`/`@RestControllerAdvice` exactly as it would in Spring MVC — this entire exception-handling layer is genuinely shared infrastructure between the two frameworks, not just superficially similar.
- `produces = MediaType.APPLICATION_NDJSON_VALUE` (newline-delimited JSON) combined with returning a `Flux<Product>` directly enables WebFlux's **streaming** response mode — each element is serialized and flushed to the client as it becomes available from the source `Flux`, rather than WebFlux waiting for the entire stream to complete before writing anything (which is closer to how a `List<Product>`/regular JSON array response behaves). This is a capability with no direct, equivalent counterpart in ordinary Spring MVC controller methods, since MVC's response model is fundamentally built around a complete-then-send model rather than genuine incremental streaming (`SseEmitter`/`StreamingResponseBody`, covered in earlier MVC cards, are MVC's own separate mechanisms for a similar effect).
- `delayElements` simulates a genuinely slow, incrementally-arriving source (a real-world equivalent might be a `Flux` backed by a database cursor yielding rows over time, or a message queue consumer) — the client-visible effect (data arriving progressively rather than all at once) is a direct, natural consequence of `Flux`'s fundamentally time-aware nature.

## 6. Walkthrough

**Request: `GET /api/products/stream` (Level 3 code, streaming NDJSON response).**

1. `DispatcherHandler` (WebFlux's central dispatcher) matches the request to `ProductController.stream()`. The handler builds and returns `repository.findAll().delayElements(Duration.ofMillis(200))` — a `Flux<Product>` describing a sequence of products, each delayed 200ms relative to the previous.
2. Because `produces = APPLICATION_NDJSON_VALUE` and the return type is `Flux<Product>`, WebFlux's response-writing machinery recognizes this as a **streaming** response scenario rather than a complete-then-send one — it begins subscribing to the `Flux` and writing each emitted element to the response body as an individual JSON object followed by a newline, as soon as that element arrives, without waiting for the `Flux` to complete.
3. The underlying `repository.findAll()` (assume it's backed by a genuinely reactive data source) begins emitting `Product` values one at a time. `delayElements` inserts a 200ms gap before each emission reaches downstream — again, this delay does **not** block any thread; it's implemented via Reactor's internal, non-blocking scheduling.
4. As each `Product` element is emitted from the (delayed) `Flux`, WebFlux's response writer serializes it to a single JSON object and flushes those bytes immediately to the underlying Netty (or other reactive server) connection, then continues waiting for the next element.
5. From the client's perspective (using `curl --no-buffer` to disable its own local output buffering and see this effect directly): the first product's JSON appears on screen almost immediately, then a visible ~200ms pause, then the second product's JSON appears, and so on — the response is genuinely, observably incremental, not an artifact of network buffering.
6. Once the source `Flux` completes (all products emitted), WebFlux finalizes the HTTP response (closing the chunked/streamed body appropriately) and the connection either closes or, depending on server configuration, remains available for a subsequent request (HTTP keep-alive).

## 7. Gotchas & takeaways

> **Returning `Flux<T>` from a handler with the default `application/json` produces type does NOT stream by default** — WebFlux typically buffers the entire `Flux` into a single JSON array before writing the response, matching a regular API's expected array output shape. Genuine element-by-element streaming (as in the Level 3 example) requires an explicitly streaming-friendly media type like `application/x-ndjson` or `text/event-stream` (for Server-Sent Events).

> **`@RequestBody Product` (a direct, non-`Mono`-wrapped type) still works in WebFlux, but WebFlux must fully buffer the request body before invoking your handler** — this is a legitimate, common pattern (especially for small request bodies where the non-blocking benefit of streaming a body is negligible), but it's worth knowing it's a deliberate simplification, not "true" end-to-end reactive body handling.

> **Forgetting `switchIfEmpty`/`defaultIfEmpty` for a lookup that might not find anything means an empty `Mono` silently produces WebFlux's own default (often a `404` with no body, or in some configurations a `200` with an empty body) rather than your intended, more specific error response** — always be deliberate about what an empty result should mean for each specific endpoint, exactly as you would with an `Optional.empty()` case in imperative code.

- Reactive annotated controllers share nearly the entire annotation vocabulary with Spring MVC — routing, path/query parameter binding, validation, and exception handling all work almost identically.
- The core difference is return types (`Mono<T>`/`Flux<T>`) and building handler logic as a reactive pipeline (`map`/`flatMap`/`switchIfEmpty`) rather than imperative sequential code.
- `Flux<T>` can genuinely stream elements to the client incrementally, but only with an explicitly streaming-friendly media type (`application/x-ndjson`, SSE) — the default JSON array output still buffers the full collection first.
- `@ExceptionHandler`/`@ControllerAdvice` work identically to Spring MVC, making error-handling knowledge fully transferable between the two frameworks.
