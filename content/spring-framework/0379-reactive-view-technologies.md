---
card: spring-framework
gi: 379
slug: reactive-view-technologies
title: "Reactive view technologies"
---

## 1. What it is

Spring WebFlux supports server-side view rendering (Thymeleaf being the primary, well-integrated option) for `@Controller`-based applications that render HTML rather than JSON — the reactive counterpart to the `View`/`ViewResolver` machinery covered in the Spring MVC section, adapted so that both the model-population step and the actual rendering happen without blocking, and so that a template can even render progressively against a `Flux` of data rather than requiring a fully-materialized model upfront.

```java
@Controller
public class ProductController {

    @GetMapping("/products/{id}")
    public Mono<String> detail(@PathVariable long id, Model model) {
        return productRepository.findById(id)
            .doOnNext(product -> model.addAttribute("product", product))
            .thenReturn("product-detail");   // view name, resolved reactively
    }
}
```

## 2. Why & when

Most WebFlux applications are pure JSON/REST APIs, where server-side HTML rendering is unnecessary — but WebFlux does fully support the classic `@Controller`-returns-a-view-name pattern for teams that want a reactive backend serving traditional server-rendered pages (perhaps migrating an existing Thymeleaf-based Spring MVC application to WebFlux for its concurrency benefits, while keeping the same rendering approach). Use reactive view technologies when:

- You need server-rendered HTML from a WebFlux application, rather than a pure JSON API consumed by a separate frontend.
- You want to stream a template's rendering against a genuinely large or slowly-arriving dataset (e.g., a report with thousands of rows arriving from a reactive database query) without buffering the entire result set in memory first.
- You're migrating an existing Thymeleaf-based Spring MVC application to WebFlux and want to preserve the same templates and rendering approach with minimal disruption.

## 3. Core concept

```
Thymeleaf's reactive integration (spring-boot-starter-thymeleaf ALSO
works for WebFlux, autoconfiguring reactive-aware rendering):

  Controller method returns Mono<String> (the view name, wrapped)
       |
       v
  Model population happens via reactive composition (doOnNext, etc.)
  rather than direct, synchronous model.addAttribute(...) calls
       |
       v
  ThymeleafReactiveView renders — CAN operate in two modes:

    FULL mode (default): renders the ENTIRE template to a buffer,
      THEN writes it as one response — simpler, most templates use this

    CHUNKED/DATA-DRIVEN mode: for a template iterating over a Flux
      (via a DataDriverContextVariable), Thymeleaf renders and FLUSHES
      output progressively AS EACH Flux element becomes available —
      genuine streaming HTML generation

Model attributes CAN be reactive types themselves:
  model.addAttribute("products", productFlux)   <- a Flux directly!
  Thymeleaf's reactive dialect can iterate a Flux in a template,
  in DATA-DRIVEN mode, without the controller ever collecting it
  into a List first.
```

## 4. Diagram

<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="200" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Full vs data-driven (streaming) Thymeleaf rendering</text>

  <rect x="20" y="50" width="320" height="80" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="180" y="72" text-anchor="middle" fill="#79c0ff" font-size="11">FULL mode (default)</text>
  <text x="35" y="95" fill="#8b949e" font-size="9">wait for ALL data, render ENTIRE</text>
  <text x="35" y="113" fill="#8b949e" font-size="9">template, THEN send one response</text>

  <rect x="380" y="50" width="320" height="80" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="540" y="72" text-anchor="middle" fill="#6db33f" font-size="11">DATA-DRIVEN mode</text>
  <text x="395" y="95" fill="#8b949e" font-size="9">render + FLUSH chunks as Flux</text>
  <text x="395" y="113" fill="#8b949e" font-size="9">elements arrive — true streaming HTML</text>

  <defs>
    <marker id="a55" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Data-driven mode lets a template's HTML output flush progressively as a `Flux` source emits, instead of waiting for the whole collection.*

## 5. Runnable example

### Level 1 — Basic

A minimal reactive Thymeleaf controller, full-mode rendering:

```java
// ProductController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import reactor.core.publisher.Mono;

@Controller
public class ProductController {

    record Product(long id, String name, double price) {}

    @GetMapping("/products/{id}")
    public Mono<String> detail(@PathVariable long id, Model model) {
        return Mono.just(new Product(id, "Drill", 29.99))
            .doOnNext(product -> model.addAttribute("product", product))
            .thenReturn("product-detail");
    }
}
```

`templates/product-detail.html`:
```html
<html xmlns:th="http://www.thymeleaf.org">
<body><h1 th:text="${product.name}">Default</h1></body>
</html>
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# <html>...<h1>Drill</h1>...</html>
```

`.doOnNext(product -> model.addAttribute(...))` populates the model as a side effect once the (here, trivially fast) `Mono<Product>` resolves, and `.thenReturn("product-detail")` produces the view name afterward — this composition pattern (do side-effecting work, then return a fixed value) is the reactive idiom replacing the direct, synchronous `model.addAttribute(...); return "view-name";` pattern familiar from Spring MVC.

### Level 2 — Intermediate

A collection page rendered from a `Flux<Product>`, still in full (buffered) mode — the default and simplest approach for genuinely small-to-moderate collections:

```java
// ProductController.java (extended)
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.List;

@Controller
public class ProductController {

    record Product(long id, String name) {}

    @GetMapping("/products")
    public Mono<String> list(Model model) {
        Flux<Product> products = Flux.just(new Product(1, "Drill"), new Product(2, "Hammer"));
        return products.collectList()
            .doOnNext(list -> model.addAttribute("products", list))
            .thenReturn("product-list");
    }
}
```

`templates/product-list.html`:
```html
<html xmlns:th="http://www.thymeleaf.org">
<body>
  <ul>
    <li th:each="product : ${products}" th:text="${product.name}">Name</li>
  </ul>
</body>
</html>
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/products
# <html>...<ul><li>Drill</li><li>Hammer</li></ul>...</html>
```

**What changed:** `.collectList()` explicitly materializes the `Flux<Product>` into a `Mono<List<Product>>` before adding it to the model — this is the standard, simple approach: fully buffer a (presumably reasonably-sized) collection into memory, then let Thymeleaf's ordinary `th:each` iterate it exactly as it would in a non-reactive template. This remains entirely appropriate for typical list sizes; genuine streaming (next level) is a deliberate opt-in for cases where it specifically matters.

### Level 3 — Advanced

Data-driven (genuinely streaming) rendering for a large or slowly-arriving dataset, using Thymeleaf's `reactiveDataDriverContextVariable` — the HTML response begins flushing to the client before the entire product list has even finished arriving from its source:

```java
// ProductController.java (production version)
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.thymeleaf.spring6.context.webflux.ReactiveDataDriverContextVariable;
import reactor.core.publisher.Flux;

import java.time.Duration;

@Controller
public class ProductController {

    record Product(long id, String name) {}

    @GetMapping("/products/stream")
    public String streamingList(Model model) {
        // Simulates a slow, incrementally-arriving source — e.g. a large
        // result set from a reactive database query, arriving row by row.
        Flux<Product> slowProducts = Flux.range(1, 20)
            .delayElements(Duration.ofMillis(100))
            .map(i -> new Product(i, "Product " + i));

        // ReactiveDataDriverContextVariable tells Thymeleaf to render and
        // FLUSH the template's iteration chunk-by-chunk, as elements arrive,
        // rather than waiting for the ENTIRE Flux to complete first.
        model.addAttribute("products", new ReactiveDataDriverContextVariable(slowProducts, 5));
        return "product-list";   // no Mono wrapper needed — Thymeleaf handles the Flux internally
    }
}
```

`templates/product-list.html` (unchanged from Level 2 — the SAME template works for both modes):
```html
<html xmlns:th="http://www.thymeleaf.org">
<body>
  <ul>
    <li th:each="product : ${products}" th:text="${product.name}">Name</li>
  </ul>
</body>
</html>
```

**How to run:**
```bash
./mvnw spring-boot:run

curl --no-buffer http://localhost:8080/products/stream
# <html>...<ul>
# <li>Product 1</li><li>Product 2</li>...<li>Product 5</li>    <- FIRST CHUNK arrives after ~500ms
# (pause)
# <li>Product 6</li>...<li>Product 10</li>                       <- SECOND CHUNK arrives ~500ms later
# ... continues in chunks of 5 until all 20 are rendered, THEN </ul></html> closes the response
```

**What changed and why:**
- `ReactiveDataDriverContextVariable(slowProducts, 5)` wraps the `Flux` with a **buffer size hint** (`5`) — Thymeleaf accumulates this many elements from the source before rendering and flushing that chunk of the `th:each` loop's output, then waits for the next batch, repeating until the `Flux` completes. This produces genuinely incremental HTML delivery, directly analogous to the `Flux<Product>` NDJSON streaming pattern from the reactive `@RequestBody`/`@ResponseBody` card, but for HTML template rendering instead of JSON serialization.
- The **same template** (`product-list.html`) works unchanged for both the buffered (`List<Product>`, Level 2) and data-driven (`Flux<Product>` wrapped in `ReactiveDataDriverContextVariable`, Level 3) approaches — Thymeleaf's `th:each` doesn't need to know or care which mode is in play; the difference is entirely in how the controller populates the model.
- This capability has no direct equivalent in Spring MVC's view rendering (which is fundamentally built around a complete, synchronous model before any rendering begins) — it's a genuine, WebFlux-specific advantage for use cases where a large, slowly-materializing dataset needs to start reaching the browser before the full result is available server-side.

## 6. Walkthrough

**Request: `GET /products/stream` (Level 3 code, data-driven rendering).**

1. `DispatcherHandler` dispatches to `streamingList(model)`. The method constructs `slowProducts` (a `Flux<Product>` emitting 20 elements, each 100ms apart) and wraps it in `ReactiveDataDriverContextVariable(slowProducts, 5)`, adding this wrapper — not a plain list, not a plain `Flux` — as the `"products"` model attribute. It returns the plain `String` view name `"product-detail"` (no `Mono` wrapper needed here, since Thymeleaf's reactive integration handles the asynchronous data-driving internally, once it recognizes this special context-variable type).
2. Thymeleaf's reactive `ViewResolver` resolves `"product-list"` to the template and begins rendering — because it detects the `"products"` model attribute is a `ReactiveDataDriverContextVariable`, it switches into data-driven rendering mode specifically for the portion of the template that iterates this variable.
3. Rendering proceeds through the static HTML preceding the `th:each` loop (`<html><body><ul>`) immediately, flushing these bytes to the response as soon as they're rendered — the response has already started transmitting before any product data has even arrived.
4. Thymeleaf begins consuming `slowProducts`. As each `Product` element is emitted (one every 100ms), it's accumulated into an internal buffer. Once 5 elements have accumulated (matching the configured buffer size hint), Thymeleaf renders the `<li>...</li>` markup for those 5 products and flushes that chunk of HTML to the response.
5. This buffering-and-flushing cycle repeats: the next 5 elements accumulate (taking another ~500ms, since each element is 100ms apart), get rendered, and flushed — and so on, until all 20 products have been processed across 4 total chunks.
6. Once `slowProducts` completes (all 20 elements emitted and processed), Thymeleaf renders the remaining static template content following the `th:each` loop (`</ul></body></html>`) and flushes this final chunk, completing the response.
7. From the client's perspective (observable via `curl --no-buffer`): the page's outer HTML structure appears almost immediately, then product list items appear in visible batches of 5 roughly every half-second, and finally the closing tags appear once the last batch is rendered — the entire page is never held back waiting for all 20 products to be ready server-side.

## 7. Gotchas & takeaways

> **`ReactiveDataDriverContextVariable` requires the specific Thymeleaf-for-WebFlux integration classes (`org.thymeleaf.spring6.context.webflux.*`)** — this data-driven streaming capability is specific to Thymeleaf's reactive module and does not exist for other template engines' WebFlux integrations in the same form; verify equivalent capability (or its absence) before assuming a non-Thymeleaf template engine supports the same streaming pattern.

> **The buffer size hint passed to `ReactiveDataDriverContextVariable` is a genuine tuning parameter, not just documentation** — too small a value means many small flushes (more overhead per chunk); too large approaches the same "wait for everything" behavior as full-mode rendering, defeating the purpose. Tune it based on the actual data arrival pattern and desired responsiveness.

> **Most WebFlux applications never need data-driven rendering at all** — it's a specific optimization for large or genuinely slow-arriving datasets rendered as HTML. For typical page sizes (tens to low hundreds of rows), the simpler `.collectList()` full-mode approach from Level 2 remains entirely appropriate and considerably easier to reason about.

- Reactive view technologies (primarily Thymeleaf) let WebFlux applications render server-side HTML with the same template syntax as Spring MVC, adapted for non-blocking model population and response writing.
- Full-mode rendering (the default, and simplest) buffers the model completely before rendering — appropriate for typical page sizes.
- `ReactiveDataDriverContextVariable` enables genuine, chunked streaming HTML generation directly from a `Flux` source, flushing rendered output progressively as elements arrive.
- The same Thymeleaf template works unchanged for both full and data-driven modes — the distinction lives entirely in how the controller populates the model.
