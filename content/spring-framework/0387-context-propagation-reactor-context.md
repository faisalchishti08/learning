---
card: spring-framework
gi: 387
slug: context-propagation-reactor-context
title: "Context propagation (Reactor Context)"
---

## 1. What it is

Reactor `Context` is a per-subscription, immutable key-value store that travels *alongside* a `Mono`/`Flux` chain — the reactive replacement for `ThreadLocal`, which doesn't work reliably in reactive code because a single logical operation can genuinely execute across multiple different threads over its lifetime (as noted in the WebHandler API card). `Context` is written using `.contextWrite(...)` and read using `Mono.deferContextual(...)`/`Flux.deferContextual(...)`, propagating automatically downstream-to-upstream through an operator chain.

```java
Mono<String> withContext = Mono.deferContextual(ctx ->
        Mono.just("Hello, " + ctx.get("username")))
    .contextWrite(Context.of("username", "Alice"));
```

## 2. Why & when

Common cross-cutting needs — a request's correlation/trace ID, the current authenticated user, a tenant identifier in a multi-tenant system — are traditionally carried via `ThreadLocal` in imperative Java code, set once at the start of request processing and implicitly available anywhere downstream on the *same thread*. Reactive pipelines break this assumption: `subscribeOn`/`publishOn` can move execution to different threads mid-chain, and a single subscription might interleave with others on a shared thread pool — a `ThreadLocal` value set in a `WebFilter` might simply not be visible by the time a downstream operator or service method actually runs, because it's executing on a different thread entirely.

Reactor `Context` solves this by attaching contextual data to the **subscription** itself, not the thread — it's carried through the reactive chain's own internal machinery, correctly available regardless of which thread ends up executing any given operator. Use it whenever you need request-scoped data (correlation IDs, security context, tenant info) accessible deep within a reactive call chain, especially across multiple layers (controller → service → repository) that might not share a thread.

## 3. Core concept

```
Context propagates DOWNSTREAM-TO-UPSTREAM at SUBSCRIPTION time,
then READS flow UPSTREAM-TO-DOWNSTREAM as data flows through:

  Mono.deferContextual(ctx -> {
      String value = ctx.get("key");     <- READ the context here
      return Mono.just(value);
  })
  .map(...)
  .contextWrite(Context.of("key", "value"))   <- WRITE happens here,
                                                   but is visible to
                                                   EVERYTHING UPSTREAM
                                                   of this point in the chain

CRITICAL RULE: .contextWrite(...) only makes its values visible to
operators ABOVE it (earlier in the chain, closer to the source) —
NOT to operators below/after it. This is the OPPOSITE of how you'd
intuitively expect a "write" to propagate in a top-to-bottom reading
of the code, and is the single most common source of confusion.

  source.doSomething()
      .contextWrite(ctx -> ctx.put("k","v"))   <- writes here
  .subscribe()

  Everything ABOVE (earlier/upstream of) contextWrite CAN see "k".
  Anything chained AFTER subscribe() or in a SEPARATE, later
  .map()/.flatMap() appended AFTER contextWrite cannot see it
  unless contextWrite is placed even later still.

In WebFlux: the ServerWebExchange's context is automatically
merged into the Reactor Context for the request's processing chain,
letting exchange attributes be accessible via Context reads too.
```

## 4. Diagram

<svg viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="210" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Context flows UPWARD from contextWrite to earlier operators</text>

  <rect x="60" y="50" width="180" height="40" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="75" text-anchor="middle" fill="#6db33f" font-size="10">deferContextual (READS)</text>

  <line x1="150" y1="90" x2="150" y2="130" stroke="#8b949e" stroke-dasharray="2,2"/>
  <text x="230" y="115" fill="#8b949e" font-size="9">context VISIBLE here (upstream)</text>

  <rect x="60" y="130" width="180" height="40" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="155" text-anchor="middle" fill="#79c0ff" font-size="10">.contextWrite(...)</text>

  <rect x="320" y="130" width="180" height="40" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="410" y="155" text-anchor="middle" fill="#8b949e" font-size="9">operators AFTER — NOT visible</text>

  <line x1="240" y1="150" x2="320" y2="150" stroke="#8b949e" marker-end="url(#a63)"/>

  <defs>
    <marker id="a63" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`contextWrite` only makes its values visible to operators earlier in the chain (upstream), not later ones — a frequently counterintuitive rule.*

## 5. Runnable example

### Level 1 — Basic

A minimal demonstration of the write-then-read pattern and the upstream-only visibility rule:

```java
// ContextDemo.java
import reactor.core.publisher.Mono;
import reactor.util.context.Context;

public class ContextDemo {
    public static void main(String[] args) {
        Mono<String> withValue = Mono.deferContextual(ctx ->
                Mono.just("Hello, " + ctx.get("username")))
            .contextWrite(Context.of("username", "Alice"));

        withValue.subscribe(System.out::println);
        // Hello, Alice

        Mono<String> wrongOrder = Mono.deferContextual(ctx ->
                Mono.just("Hello, " + ctx.getOrDefault("username", "UNKNOWN")))
            .map(s -> s)   // an operator...
            .contextWrite(Context.of("username", "Bob"));
        // contextWrite is placed AFTER (downstream of) map, but deferContextual
        // is EARLIER (upstream) than BOTH — so the write is still visible here,
        // since contextWrite's placement relative to the SOURCE matters, not
        // its position relative to any specific intermediate operator alone.

        wrongOrder.subscribe(System.out::println);
        // Hello, Bob    (the write DOES reach the upstream deferContextual)
    }
}
```

**How to run:**
```bash
java ContextDemo.java
# Hello, Alice
# Hello, Bob
```

Both examples succeed here because `contextWrite` is placed at the very end of each chain, making its written value visible to every operator earlier in that same chain, including `deferContextual` at the source — the confusion in practice typically arises when `contextWrite` is placed on a *different*, unrelated chain, or after a point where the read has *already* happened via a different mechanism (demonstrated in Level 2).

### Level 2 — Intermediate

The classic mistake — `contextWrite` placed too late to be visible where it's needed — followed by the corrected version:

```java
// ContextMistakeDemo.java
import reactor.core.publisher.Mono;
import reactor.util.context.Context;

public class ContextMistakeDemo {

    static Mono<String> greet() {
        return Mono.deferContextual(ctx -> Mono.just("Hello, " + ctx.getOrDefault("username", "UNKNOWN")));
    }

    public static void main(String[] args) {
        // MISTAKE: contextWrite is on a SEPARATE Mono entirely (subscribe() ends
        // the chain before contextWrite ever gets a chance to affect greet()'s OWN read).
        Mono<String> broken = greet();
        broken.subscribe(System.out::println);
        // Hello, UNKNOWN     <- greet() subscribed with NO context attached at all

        // CORRECTED: contextWrite is chained AFTER greet(), so it becomes visible
        // to greet()'s internal deferContextual read (which is UPSTREAM of this write).
        Mono<String> fixed = greet().contextWrite(Context.of("username", "Alice"));
        fixed.subscribe(System.out::println);
        // Hello, Alice
    }
}
```

**How to run:**
```bash
java ContextMistakeDemo.java
# Hello, UNKNOWN
# Hello, Alice
```

**What changed:** `broken` calls `greet()` and subscribes directly, with no `contextWrite` anywhere in that specific chain — the internal `deferContextual` read finds no `"username"` key and falls back to `"UNKNOWN"`. `fixed` chains `.contextWrite(...)` immediately after `greet()`'s returned `Mono`, making it visible to that `Mono`'s own internal, upstream `deferContextual` call — this is the correct pattern: `contextWrite` must appear somewhere in the *same* chain, downstream of (i.e., chained after) the operator whose read needs to see it.

### Level 3 — Advanced

Production pattern: a correlation ID set by a `WebFilter` (per the WebHandler API card) and propagated via Reactor `Context` all the way down through a controller and a service layer, demonstrating the realistic, multi-layer use case this mechanism exists for:

```java
// CorrelationIdWebFilter.java
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import reactor.core.publisher.Mono;
import reactor.util.context.Context;

import java.util.UUID;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class CorrelationIdWebFilter implements WebFilter {
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        String correlationId = UUID.randomUUID().toString();
        return chain.filter(exchange)
            .contextWrite(Context.of("correlationId", correlationId));
    }
}
```

```java
// ProductService.java — reads the correlation ID DEEP within a service layer,
// with NO explicit parameter passing needed to get it there.
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

@Service
public class ProductService {

    private static final Logger log = LoggerFactory.getLogger(ProductService.class);
    record Product(long id, String name) {}

    public Mono<Product> findById(long id) {
        return Mono.deferContextual(ctx -> {
            String correlationId = ctx.getOrDefault("correlationId", "none");
            log.info("[{}] Looking up product {}", correlationId, id);
            return Mono.just(new Product(id, "Drill"));
        });
    }
}
```

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
public class ProductController {

    private final ProductService productService;
    public ProductController(ProductService productService) { this.productService = productService; }

    @GetMapping("/products/{id}")
    public Mono<ProductService.Product> get(@PathVariable long id) {
        return productService.findById(id);   // NO correlationId parameter passed explicitly
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/1
# {"id":1,"name":"Drill"}
# server log: "[7c9e6679-...] Looking up product 1"
```

**What changed and why:**
- `CorrelationIdWebFilter` writes the correlation ID via `.contextWrite(...)` chained onto `chain.filter(exchange)` — the entire rest of the request-handling chain (everything `chain.filter(exchange)` eventually triggers, including `DispatcherHandler`'s dispatch to the controller and the controller's own call into the service) is upstream of this write, so the value is visible everywhere downstream in the actual request-processing sense (even though "upstream" in Reactor's own operator terminology), because `chain.filter(exchange)` represents the entire remaining pipeline as a single upstream `Mono`.
- `ProductService.findById` reads the correlation ID via `Mono.deferContextual(...)`, with **zero explicit parameter passing** required through `ProductController.get` — the correlation ID travels implicitly through the Reactor `Context` mechanism, exactly mirroring how a `ThreadLocal`-based correlation ID would travel implicitly in imperative Spring MVC code, but correctly working even though WebFlux's execution can genuinely span multiple threads.
- This is the realistic, production-relevant use case Reactor `Context` exists for: cross-cutting, request-scoped data (correlation IDs, tenant IDs, security principals) needing to be accessible at arbitrary depth within a reactive call chain, without polluting every method signature along the way with an extra parameter purely to thread that data through.

## 6. Walkthrough

**Request: `GET /products/1` (Level 3 code), tracing the correlation ID's journey.**

1. WebFlux's `WebFilter` chain processes the request. `CorrelationIdWebFilter.filter(exchange, chain)` executes: generates `correlationId = "7c9e6679-..."`, then constructs `chain.filter(exchange).contextWrite(Context.of("correlationId", correlationId))` — this composed `Mono<Void>` is what the filter returns.
2. Because `.contextWrite(...)` is chained *after* `chain.filter(exchange)` (which represents everything downstream — `DispatcherHandler`'s dispatch, the controller, the service, all the way to response completion), the written `correlationId` value becomes visible to every operator within that entire downstream (in request-processing terms) chain, per the upstream-visibility rule from the core concept section.
3. `DispatcherHandler` proceeds with its normal handler resolution (per the earlier `DispatcherHandler` card), eventually invoking `ProductController.get(1)`.
4. `get(1)` calls `productService.findById(1)`, returning the `Mono<Product>` this method produces — no correlation ID is passed as an explicit argument anywhere in this call.
5. Inside `findById`, `Mono.deferContextual(ctx -> {...})` is subscribed to as part of the overall chain's execution. Because this `Mono` sits somewhere within the chain that `CorrelationIdWebFilter`'s `.contextWrite(...)` wraps (transitively, through the whole `DispatcherHandler` → controller → service call chain), the `ctx` parameter this lambda receives genuinely contains the `"correlationId"` key written back in step 1.
6. `ctx.getOrDefault("correlationId", "none")` retrieves `"7c9e6679-..."` — the log line `"[7c9e6679-...] Looking up product 1"` is written, demonstrating the correlation ID successfully traveled from the `WebFilter` (where it was generated) down through `DispatcherHandler`'s internal dispatch machinery, the controller, and finally into the service layer — entirely via Reactor `Context`, with no explicit parameter threading anywhere along that path.
7. `findById` returns `Mono.just(new Product(1, "Drill"))`, which resolves and is serialized as the response body.
8. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   {"id":1,"name":"Drill"}
   ```

## 7. Gotchas & takeaways

> **`.contextWrite(...)` placement relative to the *specific read* it needs to reach is the single most common source of confusion** — always verify the write is chained onto (or wraps) the *same* `Mono`/`Flux` instance whose upstream operators need to see it, not a separate, unrelated chain, even if that other chain seems related in application logic.

> **`ThreadLocal` genuinely does not work reliably across a reactive pipeline** — a value set via `ThreadLocal.set(...)` before subscribing might simply not be visible in a `map`/`flatMap` lambda that Reactor happens to execute on a different thread (due to `subscribeOn`/`publishOn`, or scheduler reuse across unrelated subscriptions). This is precisely the class of bug Reactor `Context` exists to prevent — always use `Context` (or, for logging specifically, Micrometer's context-propagation-aware MDC integration) for reactive request-scoped data, never `ThreadLocal`.

> **Reactor `Context` is immutable — each `.contextWrite(...)` call produces a NEW context, layered on top of (not mutating) whatever context already existed at that point in the chain.** This is a deliberate design choice enabling safe, concurrent sharing of context data across multiple, independent subscriptions to related publishers, but it means "adding a value to the context" is conceptually a functional transformation, not an in-place mutation.

- Reactor `Context` is the reactive replacement for `ThreadLocal`, attaching request-scoped data to a subscription rather than a thread, correctly surviving `subscribeOn`/`publishOn` thread hops.
- `.contextWrite(...)` only makes its values visible to operators *upstream* of (earlier in the chain than) where it's placed — a frequently counterintuitive rule that causes real bugs when misunderstood.
- `Mono.deferContextual(...)`/`Flux.deferContextual(...)` is how a reactive pipeline reads values previously written via `contextWrite` anywhere upstream in the same logical chain.
- WebFlux's own request-processing chain (via `WebFilter`s wrapping `chain.filter(exchange)`) is a natural, realistic place to write cross-cutting, request-scoped context (correlation IDs, tenant info) that needs to reach arbitrarily deep into a controller/service call chain without explicit parameter threading.
