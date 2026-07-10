---
card: spring-framework
gi: 388
slug: reactive-libraries-adaptation-rxjava-etc
title: "Reactive libraries adaptation (RxJava, etc.)"
---

## 1. What it is

Spring WebFlux's controller method return-type support isn't limited to Project Reactor's `Mono`/`Flux` — because RxJava's `Single`/`Maybe`/`Observable`/`Flowable` and other Reactive-Streams-compliant types all conform to the same underlying specification (covered in the Reactive Streams spec card), Spring can adapt between them automatically via `ReactiveAdapterRegistry`, letting you return an RxJava type directly from a `@RestController` method, or convert freely between RxJava and Reactor types within your own code.

```java
@GetMapping("/products/{id}")
public Single<Product> get(@PathVariable long id) {   // RxJava's Single, NOT Reactor's Mono
    return productRepository.findByIdRx(id);
}
```

## 2. Why & when

Most new Spring WebFlux code uses Project Reactor directly, since it's the library Spring itself is built on and ships with by default — there's rarely a compelling reason to introduce RxJava into a brand-new WebFlux project. Understanding this adaptation layer matters when:

- Integrating with an existing codebase, library, or team that already uses RxJava extensively (common in Android-adjacent backend teams, or organizations with pre-existing RxJava investment) and wants to adopt WebFlux without a full rewrite to Reactor types.
- Consuming a third-party library or SDK that exposes RxJava types natively, needing to bridge its results into your Reactor-based WebFlux pipeline (or vice versa).
- Understanding `ReactiveAdapterRegistry` conceptually reinforces the Reactive Streams specification card's core lesson: because all these libraries implement the same underlying contract, interoperability is a natural, well-supported capability, not a hacky workaround.

## 3. Core concept

```
ReactiveAdapterRegistry — Spring's central registry mapping reactive
types to/from the Reactive Streams Publisher interface:

  Reactor:  Mono<T>, Flux<T>
  RxJava 3: Single<T>, Maybe<T>, Completable, Observable<T>, Flowable<T>
  (RxJava 2 similarly, with its own type names)

WebFlux controller methods CAN return any REGISTERED reactive type
directly — Spring's argument/return-value handling machinery consults
ReactiveAdapterRegistry to know how to treat it (subscribe to it,
apply backpressure correctly, etc.) regardless of which library it's from.

Manual conversion (when you need to bridge WITHIN your own code,
not just at the controller boundary):

  RxJava -> Reactor:
    Mono.from(rxJavaSingle.toFlowable())      (or via RxJava2Adapter /
                                                 similar bridging utilities,
                                                 depending on RxJava version)
  Reactor -> RxJava:
    Flowable.fromPublisher(reactorFlux)
    Single.fromPublisher(reactorMono)          (RxJava 3's OWN bridging methods,
                                                  since Reactor types ARE Publishers)

Type mapping (rough conceptual equivalence):
  Reactor Mono<T>   <-> RxJava Single<T> (always emits) / Maybe<T> (0 or 1) / Completable (no value)
  Reactor Flux<T>    <-> RxJava Observable<T> (no backpressure) / Flowable<T> (WITH backpressure)
```

## 4. Diagram

<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="200" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">ReactiveAdapterRegistry bridges multiple Reactive-Streams-compliant libraries</text>

  <rect x="270" y="40" width="180" height="45" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="360" y="67" text-anchor="middle" fill="#e6edf3" font-size="10">Reactive Streams Publisher</text>

  <line x1="330" y1="85" x2="160" y2="130" stroke="#8b949e" marker-end="url(#a64)"/>
  <line x1="390" y1="85" x2="560" y2="130" stroke="#8b949e" marker-end="url(#a64)"/>

  <rect x="60" y="130" width="200" height="45" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="157" text-anchor="middle" fill="#6db33f" font-size="10">Reactor Mono&lt;T&gt;/Flux&lt;T&gt;</text>

  <rect x="460" y="130" width="200" height="45" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="560" y="157" text-anchor="middle" fill="#79c0ff" font-size="10">RxJava Single/Flowable</text>

  <defs>
    <marker id="a64" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Because both libraries implement the same Reactive Streams specification, `ReactiveAdapterRegistry` bridges them without custom per-library conversion code.*

## 5. Runnable example

### Level 1 — Basic

A WebFlux controller returning RxJava's `Single<T>` directly, with no Reactor types anywhere:

```xml
<!-- pom.xml -->
<dependency>
    <groupId>io.reactivex.rxjava3</groupId>
    <artifactId>rxjava</artifactId>
</dependency>
```

```java
// ProductController.java
import io.reactivex.rxjava3.core.Single;
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    record Product(long id, String name) {}

    @GetMapping("/products/{id}")
    public Single<Product> get(@PathVariable long id) {
        return Single.just(new Product(id, "Drill"));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# {"id":1,"name":"Drill"}
```

No explicit conversion code was written anywhere — Spring's return-value handling machinery consults `ReactiveAdapterRegistry`, recognizes `Single<T>` as a registered, Reactive-Streams-compliant type, and processes it correctly (subscribing, extracting the eventual value, serializing it as the response body) exactly as it would a `Mono<T>`.

### Level 2 — Intermediate

Manual, explicit conversion between RxJava and Reactor within application code — needed when a service layer uses RxJava internally (perhaps calling an RxJava-based third-party client) but the surrounding WebFlux application is built on Reactor types:

```java
// LegacyRxJavaClient.java — simulates a third-party SDK that only exposes RxJava types
import io.reactivex.rxjava3.core.Single;

public class LegacyRxJavaClient {
    record Product(long id, String name) {}

    public Single<Product> fetchProduct(long id) {
        return Single.just(new Product(id, "Drill"));   // in reality, a real RxJava-based HTTP call
    }
}
```

```java
// ProductService.java — bridges RxJava (from the legacy client) INTO Reactor (for the rest of the app)
import io.reactivex.rxjava3.core.Flowable;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

@Service
public class ProductService {

    record Product(long id, String name) {}
    private final LegacyRxJavaClient legacyClient = new LegacyRxJavaClient();

    public Mono<Product> getProduct(long id) {
        // RxJava's Single -> Reactor's Mono: via toFlowable() (RxJava's own bridging
        // method, converting to a Publisher) then Mono.from(...) (Reactor's own
        // bridging method, accepting ANY Publisher).
        return Mono.from(
            legacyClient.fetchProduct(id)
                .map(legacyProduct -> new Product(legacyProduct.id(), legacyProduct.name()))
                .toFlowable());
    }
}
```

```java
// ProductController.java — SEES ONLY Reactor types, unaware RxJava is used internally
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {

    private final ProductService productService;
    public ProductController(ProductService productService) { this.productService = productService; }

    @GetMapping("/products/{id}")
    public Mono<ProductService.Product> get(@PathVariable long id) {
        return productService.getProduct(id);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# {"id":1,"name":"Drill"}
```

**What changed:** `legacyClient.fetchProduct(id).toFlowable()` converts RxJava's `Single<Product>` into RxJava's `Flowable<Product>` (a genuine, backpressure-aware Reactive Streams `Publisher`), and `Mono.from(...)` (Reactor's own bridging factory method, accepting any `Publisher`) wraps that into a proper `Mono<Product>` — this bridging is entirely explicit, contained within `ProductService`, so the controller and everything else in the application only ever sees ordinary Reactor types, cleanly isolating the RxJava dependency to the one place it's actually needed.

### Level 3 — Advanced

Bridging in the opposite direction — exposing a Reactor-based internal pipeline as an RxJava `Flowable` for a hypothetical downstream consumer that specifically expects RxJava types (e.g., integrating with an RxJava-based Android client's shared business-logic module, or a legacy RxJava-based batch-processing framework) — plus a demonstration of `ReactiveAdapterRegistry` used programmatically for a genuinely dynamic scenario:

```java
// ReportExportService.java — internal logic built entirely on Reactor
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

import java.time.Duration;

@Service
public class ReportExportService {

    record ReportRow(int rowNum, String data) {}

    public Flux<ReportRow> generateReport() {
        return Flux.range(1, 5)
            .delayElements(Duration.ofMillis(100))
            .map(i -> new ReportRow(i, "Row data " + i));
    }
}
```

```java
// RxJavaReportBridge.java — exposes the SAME Reactor-based logic as RxJava's Flowable,
// for a consumer that specifically needs that type (e.g. a shared module also used
// by an RxJava-based Android app, reusing this same backend service's core logic).
import io.reactivex.rxjava3.core.Flowable;
import org.springframework.stereotype.Component;

@Component
public class RxJavaReportBridge {

    private final ReportExportService reportExportService;
    public RxJavaReportBridge(ReportExportService reportExportService) {
        this.reportExportService = reportExportService;
    }

    public Flowable<ReportExportService.ReportRow> generateReportRx() {
        // Reactor's Flux IS a Reactive Streams Publisher already — RxJava's
        // Flowable.fromPublisher(...) accepts it DIRECTLY, no intermediate
        // conversion step needed (unlike the reverse direction in Level 2,
        // which needed toFlowable() as an explicit RxJava-side step first).
        return Flowable.fromPublisher(reportExportService.generateReport());
    }
}
```

```java
// ReactiveAdapterRegistryDemo.java — programmatic use of the registry itself,
// illustrating what Spring does INTERNALLY when it sees a Single/Flowable return type.
import org.springframework.core.ReactiveAdapter;
import org.springframework.core.ReactiveAdapterRegistry;
import io.reactivex.rxjava3.core.Single;
import reactor.core.publisher.Mono;

public class ReactiveAdapterRegistryDemo {
    public static void main(String[] args) {
        ReactiveAdapterRegistry registry = ReactiveAdapterRegistry.getSharedInstance();

        Single<String> rxSingle = Single.just("Drill");

        ReactiveAdapter adapter = registry.getAdapter(Single.class);
        Mono<String> converted = Mono.from(adapter.toPublisher(rxSingle));

        converted.subscribe(value -> System.out.println("Converted via registry: " + value));
    }
}
```

**How to run:**
```bash
java ReactiveAdapterRegistryDemo.java
# Converted via registry: Drill

./mvnw spring-boot:run
# (RxJavaReportBridge available as a Spring bean, callable by RxJava-consuming code
#  elsewhere in a larger, mixed-library codebase)
```

**What changed and why:**
- `Flowable.fromPublisher(reactorFlux)` works directly because Reactor's `Flux` already *is* a Reactive Streams `Publisher` — no Reactor-side conversion method is needed at all for this direction, contrasted with Level 2's RxJava-to-Reactor bridging, which required RxJava's own `.toFlowable()` first (since RxJava's `Single` is *not itself* directly a `Publisher` — only `Flowable`, RxJava's backpressure-aware type, implements that interface).
- `ReactiveAdapterRegistryDemo` demonstrates, explicitly and programmatically, the exact mechanism Spring's WebFlux argument/return-value-handling infrastructure uses internally whenever it encounters a non-Reactor reactive type in a controller method signature — `registry.getAdapter(Single.class)` looks up the appropriate bridging logic, and `adapter.toPublisher(...)` performs the actual conversion to a standard `Publisher`, which Reactor's `Mono.from(...)` can then wrap. This is precisely why Level 1's controller "just worked" with no explicit conversion code — Spring was doing exactly this, automatically, behind the scenes.
- This pattern (isolating library-specific bridging to a small number of dedicated adapter classes, like `RxJavaReportBridge`) is the recommended approach for any codebase genuinely needing to support multiple reactive libraries side by side — keep the bridging explicit and localized, rather than letting both libraries' types leak throughout the broader codebase.

## 6. Walkthrough

**Request: `GET /products/1` against the Level 1 controller (returning RxJava's `Single<Product>` directly).**

1. `DispatcherHandler` dispatches to `ProductController.get(1)`. Spring's argument/return-value resolution machinery inspects the method's declared return type: `Single<Product>` (from `io.reactivex.rxjava3.core`), not a Reactor type.
2. Before invoking the method, Spring's `HandlerMethodReturnValueHandler` infrastructure (specifically, the reactive-type-aware handler responsible for processing controller return values) checks `ReactiveAdapterRegistry.getSharedInstance().getAdapter(Single.class)` — because RxJava's types are registered by default (RxJava being a common enough reactive library that Spring ships built-in adapter support for it), this lookup succeeds, returning a `ReactiveAdapter` instance that knows how to bridge `Single` to/from the standard `Publisher` interface.
3. `get(1)` executes normally, returning `Single.just(new Product(1, "Drill"))` — an actual RxJava `Single` instance.
4. Spring's return-value handling uses the `ReactiveAdapter` obtained in step 2 to convert this `Single<Product>` into a standard `Publisher<Product>` (internally, via the same `toFlowable()`-then-wrap mechanism demonstrated explicitly in the Level 3 `ReactiveAdapterRegistryDemo`), then typically further wraps it as a `Mono<Product>` for Spring's own internal processing, since Spring's core machinery is built around Reactor types.
5. This resulting `Mono<Product>` is subscribed to (as part of WebFlux's normal response-writing process, per the `DispatcherHandler` card) and, once it emits `Product(1, "Drill")`, that value is serialized to JSON exactly as it would be for a return type that was natively a Reactor `Mono<Product>` to begin with.
6. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   {"id":1,"name":"Drill"}
   ```

The controller author never had to think about `ReactiveAdapterRegistry`, `Publisher`, or any conversion logic at all — they wrote an ordinary-looking `@GetMapping` method returning `Single<Product>`, and Spring's infrastructure handled the entire bridging process transparently, precisely because both RxJava and Reactor conform to the same underlying Reactive Streams specification this whole section has built toward understanding.

## 7. Gotchas & takeaways

> **Mixing RxJava and Reactor types freely throughout a codebase (rather than isolating bridging to a small number of dedicated adapter classes, as the Level 3 example demonstrates) makes the code substantially harder to reason about** — two different reactive libraries with subtly different operator names, slightly different semantics for certain edge cases, and different idiomatic conventions coexisting throughout a codebase is a genuine maintenance burden. Prefer standardizing on one library (Reactor, for new Spring code) and localizing any necessary interop to clear, well-documented boundary points.

> **`ReactiveAdapterRegistry`'s automatic support covers well-known reactive libraries (RxJava 2/3, and a few others) out of the box, but is not universal** — a genuinely obscure or custom Reactive-Streams-compliant type not registered with the shared instance would need explicit, manual `Mono.from(...)`/`Flux.from(...)` conversion (since these Reactor factory methods accept any `Publisher` directly) rather than relying on automatic controller return-type handling.

> **Reactor's `Mono`/`Flux` genuinely ARE `Publisher` implementations directly**, while RxJava's `Single`/`Maybe`/`Observable` are NOT directly `Publisher`s (only `Flowable` is) — this asymmetry is why converting *from* RxJava's `Single` to a `Publisher`-based type requires an explicit `.toFlowable()` step first, while converting *from* Reactor's `Mono`/`Flux` to RxJava's `Flowable` needs no equivalent intermediate step, as demonstrated in the Level 3 example's two different conversion directions.

- WebFlux controller methods can return RxJava (or other Reactive-Streams-compliant library) types directly, thanks to `ReactiveAdapterRegistry` automatically bridging them to the `Publisher` interface Spring's core machinery understands.
- Manual conversion uses each library's own bridging methods: RxJava's `.toFlowable()` (since only `Flowable` is directly a `Publisher`) paired with Reactor's `Mono.from(...)`/`Flux.from(...)` (which accept any `Publisher`).
- Isolate reactive-library interop to a small number of dedicated bridging classes rather than letting multiple libraries' types spread throughout a codebase.
- This interoperability is a direct, practical payoff of the Reactive Streams specification (covered earlier in this section) — because both libraries implement the same underlying contract, bridging between them requires no custom, library-specific adapter code beyond what Spring and the libraries themselves already provide.
