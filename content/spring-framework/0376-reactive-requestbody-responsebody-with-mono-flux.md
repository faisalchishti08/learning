---
card: spring-framework
gi: 376
slug: reactive-requestbody-responsebody-with-mono-flux
title: "Reactive @RequestBody / @ResponseBody with Mono/Flux"
---

## 1. What it is

In Spring WebFlux, `@RequestBody` and the implicit `@ResponseBody` behavior of `@RestController` both support `Mono<T>`/`Flux<T>` directly as the parameter or return type — letting request and response bodies be read and written in a genuinely non-blocking, streaming-capable way, closing the loop on the reactive annotated-controllers card's brief mention of this pattern with a focused, detailed look at exactly how body handling works.

```java
@PostMapping("/products")
public Mono<Product> create(@RequestBody Mono<Product> productMono) {
    return productMono.map(this::save);
}

@GetMapping(value = "/products/stream", produces = MediaType.APPLICATION_NDJSON_VALUE)
public Flux<Product> stream() {
    return productRepository.findAll();
}
```

## 2. Why & when

Request and response bodies are, at the network level, streams of bytes arriving/departing over time — not instantaneously available blobs. Spring MVC hides this reality (it buffers the whole body before your handler runs, and buffers your whole response before writing it), which is fine for typical, modestly-sized JSON payloads but becomes a genuine limitation for very large bodies or bodies that should be processed incrementally. WebFlux's `Mono`/`Flux`-based body handling exposes this streaming reality directly:

- Use `@RequestBody Mono<T>` (a single object) when you want the framework to fully deserialize a request body but retain non-blocking behavior while waiting for the bytes to arrive — appropriate for typical request bodies, offering non-blocking benefit with minimal API complexity.
- Use `@RequestBody Flux<T>` when the request body itself represents a *stream* of objects (e.g., newline-delimited JSON, or a client uploading many records incrementally) that you want to process one at a time as they arrive, rather than waiting for the entire body.
- Use `Flux<T>` as a **return type** with a streaming-friendly media type (`application/x-ndjson`, `text/event-stream`) when the response itself should be delivered incrementally to the client — the direct complement of `SseEmitter`/`StreamingResponseBody` in Spring MVC, but expressed natively through the same reactive types used everywhere else in a WebFlux application.

## 3. Core concept

```
@RequestBody variants:

  @RequestBody Product product        — buffered: framework waits for the FULL
                                          body, deserializes, THEN invokes handler
                                          (simplest, still non-blocking overall,
                                           but no fine-grained streaming benefit)

  @RequestBody Mono<Product> product   — TRUE streaming read: handler is invoked
                                          IMMEDIATELY with a Mono describing "the
                                          eventual deserialized object" — your code
                                          composes with flatMap/map rather than
                                          having the object already in hand

  @RequestBody Flux<Product> products  — for a body representing MULTIPLE objects
                                          arriving over time (e.g. NDJSON input)

Return type -> response behavior:

  Mono<T>           — single JSON object response (buffered internally, same
                        shape as a normal REST response)
  Flux<T>, default
    produces          — BUFFERED into a single JSON array before sending
                        (matches typical API client expectations)
  Flux<T>, streaming
    produces           — STREAMED, element by element, as each is emitted
    (application/x-ndjson, text/event-stream)

The MEDIA TYPE is what determines whether a Flux response streams or buffers —
the return type alone (Flux vs Mono) does not automatically imply streaming.
```

## 4. Diagram

<svg viewBox="0 0 740 210" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="210" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">Media type determines Flux response behavior, not the return type alone</text>

  <rect x="20" y="50" width="330" height="80" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="185" y="72" text-anchor="middle" fill="#79c0ff" font-size="11">Flux&lt;Product&gt; + application/json</text>
  <text x="35" y="95" fill="#8b949e" font-size="9">framework BUFFERS all elements,</text>
  <text x="35" y="113" fill="#8b949e" font-size="9">sends ONE JSON array response</text>

  <rect x="390" y="50" width="330" height="80" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="555" y="72" text-anchor="middle" fill="#6db33f" font-size="11">Flux&lt;Product&gt; + application/x-ndjson</text>
  <text x="405" y="95" fill="#8b949e" font-size="9">each element WRITTEN as it arrives,</text>
  <text x="405" y="113" fill="#8b949e" font-size="9">client sees data PROGRESSIVELY</text>

  <defs>
    <marker id="a52" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The exact same `Flux<Product>` return type behaves completely differently depending on the response's negotiated media type.*

## 5. Runnable example

### Level 1 — Basic

Comparing buffered `@RequestBody Product` versus streaming `@RequestBody Mono<Product>` for the same create operation:

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {

    record Product(long id, String name, double price) {}
    record ProductRequest(String name, double price) {}

    // Buffered: framework waits for the FULL body, then hands you the object
    @PostMapping("/products/buffered")
    public Mono<Product> createBuffered(@RequestBody ProductRequest request) {
        return Mono.just(new Product(1, request.name(), request.price()));
    }

    // Streaming: framework hands you a Mono immediately, describing the
    // EVENTUAL parsed object — your code composes with it via map/flatMap
    @PostMapping("/products/streaming")
    public Mono<Product> createStreaming(@RequestBody Mono<ProductRequest> requestMono) {
        return requestMono.map(request -> new Product(1, request.name(), request.price()));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -X POST http://localhost:8080/products/buffered -H "Content-Type: application/json" -d '{"name":"Drill","price":29.99}'
# {"id":1,"name":"Drill","price":29.99}

curl -X POST http://localhost:8080/products/streaming -H "Content-Type: application/json" -d '{"name":"Drill","price":29.99}'
# {"id":1,"name":"Drill","price":29.99}     <- IDENTICAL client-visible result
```

Both endpoints produce identical responses for this small request body — the difference is architectural, not client-observable at this scale: `createBuffered` receives the already-deserialized `ProductRequest` object directly, while `createStreaming` receives a `Mono<ProductRequest>` and must compose with `.map(...)` to work with the eventual value, preserving true non-blocking behavior all the way through body deserialization.

### Level 2 — Intermediate

A `Flux<T>` response demonstrating the media-type-dependent behavior directly — the same source data, requested with two different `Accept`/`produces` configurations:

```java
// ProductController.java (extended)
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;

import java.time.Duration;

@RestController
public class ProductController {

    record Product(long id, String name) {}

    private Flux<Product> allProducts() {
        return Flux.just(new Product(1, "Drill"), new Product(2, "Hammer"), new Product(3, "Nail"))
            .delayElements(Duration.ofMillis(300));   // simulates a slow, incrementally-arriving source
    }

    // Default JSON: BUFFERED — client waits for ALL elements, then gets one array
    @GetMapping(value = "/products/buffered", produces = MediaType.APPLICATION_JSON_VALUE)
    public Flux<Product> listBuffered() {
        return allProducts();
    }

    // NDJSON: STREAMED — client receives each element as it becomes available
    @GetMapping(value = "/products/streamed", produces = MediaType.APPLICATION_NDJSON_VALUE)
    public Flux<Product> listStreamed() {
        return allProducts();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

time curl http://localhost:8080/products/buffered
# {"id":1,"name":"Drill"} arrives all at once, AFTER ~900ms (waits for ALL 3 delayed elements)
# real  0m0.9xxs

curl --no-buffer http://localhost:8080/products/streamed
# {"id":1,"name":"Drill"}      <- appears almost immediately
# (pause ~300ms)
# {"id":2,"name":"Hammer"}     <- appears here
# (pause ~300ms)
# {"id":3,"name":"Nail"}       <- appears here
```

**What changed:** Both handlers return the *exact same* `allProducts()` `Flux`, with the identical 300ms-per-element delay — only the `produces` media type differs. `APPLICATION_JSON_VALUE` causes WebFlux to buffer the entire `Flux` into one JSON array before writing any response bytes at all (hence the client waiting the full ~900ms before seeing anything). `APPLICATION_NDJSON_VALUE` causes WebFlux to write each element as an individual, newline-terminated JSON object the instant it's emitted, making the incremental arrival directly observable to the client.

### Level 3 — Advanced

A `Flux<T>` **request** body — processing a client-uploaded stream of records one at a time as they arrive, without ever buffering the whole upload into memory, combined with per-element validation and error handling:

```java
// ProductUploadController.java
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.concurrent.atomic.AtomicInteger;

@RestController
public class ProductUploadController {

    record ProductRecord(@NotBlank String name, @Positive double price) {}
    record UploadSummary(int accepted, int rejected) {}

    @PostMapping(value = "/products/bulk-upload", consumes = MediaType.APPLICATION_NDJSON_VALUE)
    public Mono<UploadSummary> bulkUpload(@RequestBody Flux<ProductRecord> records) {
        AtomicInteger accepted = new AtomicInteger(0);
        AtomicInteger rejected = new AtomicInteger(0);

        return records
            // Each record is validated and PERSISTED (simulated here) AS IT ARRIVES —
            // the entire upload is never held in memory at once, regardless of how
            // many thousands of records the client streams.
            .flatMap(record -> {
                if (record.price() <= 0 || record.name().isBlank()) {
                    rejected.incrementAndGet();
                    return Mono.empty();   // skip invalid records, don't fail the whole upload
                }
                return saveAsync(record).doOnSuccess(v -> accepted.incrementAndGet());
            })
            .then(Mono.fromSupplier(() -> new UploadSummary(accepted.get(), rejected.get())));
    }

    private Mono<Void> saveAsync(ProductRecord record) {
        // Simulates an async persistence call (e.g. R2DBC) — never blocks a thread.
        return Mono.delay(java.time.Duration.ofMillis(5)).then();
    }

    @ExceptionHandler(org.springframework.web.bind.support.WebExchangeBindException.class)
    public org.springframework.http.ResponseEntity<String> handleValidation(Exception ex) {
        return org.springframework.http.ResponseEntity.status(HttpStatus.BAD_REQUEST).body("Invalid record in upload stream");
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

printf '{"name":"Drill","price":29.99}\n{"name":"","price":-1}\n{"name":"Hammer","price":14.99}\n' | \
  curl -X POST http://localhost:8080/products/bulk-upload \
       -H "Content-Type: application/x-ndjson" --data-binary @-
# {"accepted":2,"rejected":1}
```

**What changed and why:**
- `@RequestBody Flux<ProductRecord>` combined with `consumes = APPLICATION_NDJSON_VALUE` means the request body is parsed as a stream of newline-delimited JSON objects, each deserialized and delivered to the `flatMap` pipeline individually — a client could stream **millions** of records this way, and the server's memory usage stays bounded to roughly one record (plus whatever `flatMap`'s internal concurrency allows) at a time, never the full upload.
- Invalid records are skipped (`Mono.empty()`, incrementing a `rejected` counter) rather than failing the entire upload — a deliberate resilience choice appropriate for bulk-import scenarios where one bad record among thousands shouldn't abort the whole operation; a different business requirement might instead choose to fail fast on the first invalid record, which would use `Mono.error(...)` instead.
- `.then(Mono.fromSupplier(() -> new UploadSummary(...)))` waits for the entire `flatMap`-driven processing pipeline to complete (all records processed, whether accepted or rejected) before producing the final summary — the `Mono<UploadSummary>` returned from the handler only resolves once every element of the incoming `Flux` has been consumed.

## 6. Walkthrough

**Request: `POST /products/bulk-upload` with an NDJSON body containing three records, one invalid (Level 3 code).**

1. `DispatcherHandler` resolves the request to `bulkUpload(Flux<ProductRecord> records)`. Because the parameter is `@RequestBody Flux<ProductRecord>` and the request's `Content-Type` matches the declared `consumes = APPLICATION_NDJSON_VALUE`, WebFlux's NDJSON-aware `HttpMessageReader` is selected to parse the body.
2. Rather than reading the entire request body into memory first, this reader incrementally parses the incoming byte stream, splitting on newlines and deserializing each line into a `ProductRecord` as its bytes become available — this is precisely what makes `records` a genuine `Flux<ProductRecord>` rather than a pre-materialized list.
3. The handler method is invoked essentially immediately (the framework does not wait for the whole body to arrive before calling `bulkUpload`) with this `Flux` as the `records` parameter. The method body composes a reactive pipeline (`flatMap` chain) describing what to do with each eventual element, then returns.
4. As the underlying NDJSON reader parses the first line, `{"name":"Drill","price":29.99}` → `ProductRecord("Drill", 29.99)` is emitted into the `records` Flux, flowing into `.flatMap(record -> {...})`.
5. Inside the `flatMap` lambda: `record.price() (29.99) <= 0` is `false`, `record.name().isBlank()` is `false` — validation passes. `saveAsync(record)` is called, returning a `Mono<Void>` that resolves after a simulated 5ms delay, at which point `.doOnSuccess(v -> accepted.incrementAndGet())` fires, bumping `accepted` to `1`.
6. The second line, `{"name":"","price":-1}` → `ProductRecord("", -1.0)`, is parsed and emitted next. Inside `flatMap`: `record.price() (-1) <= 0` is `true` — the validation check fails. `rejected.incrementAndGet()` bumps `rejected` to `1`, and `Mono.empty()` is returned — this element contributes nothing further to the pipeline's output, but processing continues to the next record without error.
7. The third line, `{"name":"Hammer","price":14.99}`, is processed identically to the first: passes validation, `saveAsync` succeeds, `accepted` becomes `2`.
8. Once the underlying NDJSON reader reaches the end of the request body (no more lines), the `records` `Flux` completes — this completion signal propagates through the `flatMap` chain, and `.then(Mono.fromSupplier(...))` fires, constructing `new UploadSummary(accepted.get()=2, rejected.get()=1)`.
9. This `UploadSummary` becomes the handler's overall result, serialized to JSON as the response body:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   {"accepted":2,"rejected":1}
   ```

## 7. Gotchas & takeaways

> **`@RequestBody Product` (a direct, non-reactive type) still works in WebFlux, but forces the framework to buffer the entire request body before your handler is invoked** — perfectly reasonable for typical small JSON bodies, but forfeits the streaming benefit for large or slow-arriving request bodies. Reach for `Mono<T>`/`Flux<T>` request body types specifically when that streaming benefit genuinely matters for your use case.

> **A `Flux<T>` response's streaming behavior is entirely determined by the response's negotiated media type, not by the return type alone** — returning `Flux<Product>` with `produces = application/json` still buffers the whole collection into one array response. This surprises developers who assume `Flux` inherently implies element-by-element streaming; it only does so with an explicitly streaming-aware media type (`application/x-ndjson`, `text/event-stream`).

> **`@RequestBody Flux<T>` for request bodies requires the client to actually send data in a format the framework's streaming-aware readers understand** (typically newline-delimited JSON) — a client sending a single, standard JSON array (`[{...}, {...}]`) with `Content-Type: application/json` will not be parsed element-by-element into a `Flux` the same way; that shape is more naturally consumed as `Mono<List<T>>` or `Flux<T>` via a JSON-array-aware reader, which behaves differently from NDJSON's line-by-line streaming semantics.

- `@RequestBody Mono<T>`/`Flux<T>` enable genuinely non-blocking, streaming-capable request body reading, contrasted with the simpler but fully-buffered `@RequestBody T` form.
- A `Flux<T>` response's actual streaming behavior depends entirely on the negotiated/declared media type (`application/x-ndjson`, `text/event-stream` stream; `application/json` buffers into a single array).
- `Flux<T>` request bodies are the tool for processing large or unbounded client uploads incrementally, keeping memory usage bounded regardless of the total upload size.
- Choose between fully-buffered and truly-streaming body handling deliberately based on payload size and latency requirements, not by default — the buffered form remains simpler and entirely appropriate for typical, modestly-sized request/response bodies.
