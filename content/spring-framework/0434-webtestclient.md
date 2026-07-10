---
card: spring-framework
gi: 434
slug: webtestclient
title: "WebTestClient"
---

## 1. What it is

`WebTestClient` is the reactive-stack counterpart to `MockMvc` — a fluent, `WebClient`-styled test client for WebFlux applications, usable in two modes: bound to a controller/router function directly (in-memory, no server, analogous to `MockMvc`'s `standaloneSetup`), or bound to a real running server over an actual socket (analogous to a full end-to-end test). It works for both reactive (`Mono`/`Flux`-returning) and traditional Spring MVC endpoints, making it the more broadly applicable of the two test clients when a project uses WebFlux anywhere.

```java
WebTestClient client = WebTestClient.bindToController(new ProductController()).build();

client.get().uri("/products/42")
        .exchange()
        .expectStatus().isOk()
        .expectBody().jsonPath("$.name").isEqualTo("Laptop");
```

## 2. Why & when

`MockMvc` is built around the Servlet API's blocking request/response model — it doesn't understand `Mono`/`Flux` return types or WebFlux's non-blocking dispatch mechanism, so it can't test a genuinely reactive endpoint's behavior correctly. `WebTestClient` exists specifically to test WebFlux applications with the same in-memory, no-real-server efficiency `MockMvc` provides for Spring MVC, while also being able to test *streaming* responses (a `Flux` emitting multiple items over time) that a simple synchronous assertion can't express.

Reach for `WebTestClient` when:

- Testing a WebFlux application's `@RestController` or functional `RouterFunction` endpoints, especially ones returning `Mono`/`Flux`.
- Verifying streaming behavior — a Server-Sent Events endpoint, or any response that emits multiple values over time rather than one complete body at once.
- You want one consistent test client API across both a full end-to-end test (bound to a real server) and a fast in-memory test (bound directly to a controller), since `WebTestClient` supports both binding modes with the same fluent API.

For a traditional (non-reactive) Spring MVC application, `MockMvc` remains the more natural fit — but `WebTestClient` can also test MVC endpoints (it just issues real, if in-memory-simulated, HTTP calls), which matters for projects with a mix of MVC and WebFlux controllers wanting one unified test client style.

## 3. Core concept

```
 WebTestClient.bindToController(controller)   <- in-memory, no server (like MockMvc standalone)
 WebTestClient.bindToApplicationContext(ctx)    <- in-memory, full context (like MockMvc webAppContextSetup)
 WebTestClient.bindToServer().baseUrl(url)       <- real running server, real socket (end-to-end)
        |
        v
 client.get().uri("/products/{id}", 42)
        |
        v
 .exchange()   <- performs the request, returns a spec for assertions
        |
        v
 .expectStatus().isOk()
 .expectBody().jsonPath("$.name").isEqualTo("Laptop")
 .expectBodyList(Product.class).hasSize(3)   <- for Flux/streaming responses
```

Regardless of binding mode, the fluent assertion API is identical — the same test code style works whether you're testing in-memory against one controller or against a fully deployed server.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="WebTestClient supports three binding modes, all sharing the same fluent assertion API">
  <rect x="10" y="20" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="100" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">bindToController(...)</text>

  <rect x="10" y="65" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="100" y="87" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">bindToApplicationContext(...)</text>

  <rect x="10" y="110" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="100" y="132" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">bindToServer().baseUrl(...)</text>

  <rect x="300" y="60" width="150" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="375" y="88" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">WebTestClient</text>

  <rect x="510" y="60" width="120" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="570" y="88" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">.exchange()</text>

  <line x1="190" y1="37" x2="295" y2="70" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="190" y1="82" x2="295" y2="83" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="190" y1="127" x2="295" y2="95" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="450" y1="83" x2="505" y2="83" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Three ways to bind, one fluent assertion API regardless of which you pick.

## 5. Runnable example

### Level 1 — Basic

`bindToController(...)` for a fast, in-memory test of a reactive `@RestController` method returning a `Mono`.

```java
import org.springframework.test.web.reactive.server.WebTestClient;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

public class WebTestClientBasic {

    record Product(long id, String name) {}

    @RestController
    static class ProductController {
        @GetMapping("/products/{id}")
        Mono<Product> get(@PathVariable long id) {
            return Mono.just(new Product(id, "Laptop"));
        }
    }

    public static void main(String[] args) {
        WebTestClient client = WebTestClient.bindToController(new ProductController()).build();

        client.get().uri("/products/42")
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.id").isEqualTo(42)
                .jsonPath("$.name").isEqualTo("Laptop");

        System.out.println("Basic reactive GET test -- PASS");
    }
}
```

How to run: add `spring-test`, `spring-webflux`, `reactor-core`, and Jackson to the classpath, then `java WebTestClientBasic.java`.

`bindToController(new ProductController())` builds a `WebTestClient` scoped to just this controller, no real server — the WebFlux equivalent of `MockMvc.standaloneSetup(...)`. `.exchange()` performs the request and subscribes to the returned `Mono` internally, so the fluent `expectStatus()`/`expectBody()` assertions can run against the fully-resolved response without the test itself needing to manually subscribe or block.

### Level 2 — Intermediate

Test a streaming `Flux` endpoint, using `expectBodyList(...)` to assert on multiple emitted items — something `MockMvc` has no equivalent for, since it has no concept of a response emitting values incrementally.

```java
import org.springframework.http.MediaType;
import org.springframework.test.web.reactive.server.WebTestClient;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;

import java.time.Duration;
import java.util.List;

public class WebTestClientIntermediate {

    record PriceUpdate(String symbol, double price) {}

    @RestController
    static class PriceStreamController {
        @GetMapping(value = "/prices/stream", produces = MediaType.APPLICATION_NDJSON_VALUE)
        Flux<PriceUpdate> streamPrices() {
            return Flux.just(
                    new PriceUpdate("AAPL", 189.50),
                    new PriceUpdate("GOOG", 141.20),
                    new PriceUpdate("MSFT", 402.10)
            );
        }
    }

    public static void main(String[] args) {
        WebTestClient client = WebTestClient.bindToController(new PriceStreamController()).build();

        List<PriceUpdate> updates = client.get().uri("/prices/stream")
                .exchange()
                .expectStatus().isOk()
                .returnResult(PriceUpdate.class)
                .getResponseBody()
                .collectList()
                .block(Duration.ofSeconds(2)); // acceptable in test code: bounded wait on a finite stream

        System.out.println("Received price updates: " + updates);
        if (updates.size() != 3) throw new AssertionError("Expected 3 updates, got " + updates.size());
        if (!updates.get(0).symbol().equals("AAPL")) throw new AssertionError("Expected AAPL first");
        System.out.println("Streaming Flux endpoint test -- PASS");
    }
}
```

How to run: same dependencies as Level 1, then `java WebTestClientIntermediate.java`.

`produces = MediaType.APPLICATION_NDJSON_VALUE` marks this endpoint as a streaming, newline-delimited-JSON response — each `PriceUpdate` is a separate emitted item, not one combined array. `.returnResult(PriceUpdate.class).getResponseBody()` returns a `Flux<PriceUpdate>` the test can operate on directly with Reactor operators (`.collectList()`), then `.block(...)` waits for the finite stream to complete — acceptable specifically in test code driving a bounded, known-finite stream, unlike blocking in production reactive code (a concern the WebClient card raised in an earlier section).

### Level 3 — Advanced

`bindToApplicationContext(...)` with a full Spring context (including a `@ControllerAdvice`), verifying error handling, and demonstrating `WebTestClient`'s ability to test a traditional (non-reactive) Spring MVC endpoint too — showing the "one client style across both stacks" benefit directly.

```java
import org.springframework.context.annotation.*;
import org.springframework.http.HttpStatus;
import org.springframework.test.web.reactive.server.WebTestClient;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.context.support.GenericWebApplicationContext;
import reactor.core.publisher.Mono;

import java.util.Map;

public class WebTestClientAdvanced {

    record Product(long id, String name) {}

    static class ProductNotFoundException extends RuntimeException {
        ProductNotFoundException(long id) { super("Product not found: " + id); }
    }

    @RestController
    static class ProductController {
        @GetMapping("/products/{id}")
        Mono<Product> get(@PathVariable long id) {
            if (id != 1) return Mono.error(new ProductNotFoundException(id));
            return Mono.just(new Product(1, "Laptop"));
        }
    }

    @RestControllerAdvice
    static class ErrorHandler {
        @ExceptionHandler(ProductNotFoundException.class)
        @ResponseStatus(HttpStatus.NOT_FOUND)
        Map<String, String> handleNotFound(ProductNotFoundException e) {
            return Map.of("error", e.getMessage());
        }
    }

    public static void main(String[] args) {
        var context = new GenericWebApplicationContext();
        context.registerBean(ProductController.class);
        context.registerBean(ErrorHandler.class);
        context.refresh();

        WebTestClient client = WebTestClient.bindToApplicationContext(context).build();

        // Success case
        client.get().uri("/products/1")
                .exchange()
                .expectStatus().isOk()
                .expectBody().jsonPath("$.name").isEqualTo("Laptop");
        System.out.println("Success case -- PASS");

        // Error case: verifies the @ControllerAdvice-based translation works end to end
        client.get().uri("/products/999")
                .exchange()
                .expectStatus().isNotFound()
                .expectBody().jsonPath("$.error").isEqualTo("Product not found: 999");
        System.out.println("Error-handling case correctly returned 404 with error body -- PASS");
    }
}
```

How to run: same dependencies as Level 1; then `java WebTestClientAdvanced.java`.

`bindToApplicationContext(context)` exercises the *full* configuration registered in that context — including `@RestControllerAdvice`, exactly like `MockMvc.webAppContextSetup(...)` does for the Servlet stack — rather than testing `ProductController` in isolation. The 404 case confirms the whole exception-to-response translation pipeline works correctly, not just that the controller method itself returns the right value on the happy path.

## 6. Walkthrough

Trace `WebTestClientAdvanced.main`'s error-case request:

1. **Context assembly.** `GenericWebApplicationContext` registers both `ProductController` and `ErrorHandler` as beans and refreshes — a minimal but genuine Spring context, comparable to the `WebApplicationContext` used in `MockMvc.webAppContextSetup` examples from earlier cards.
2. **Client binding.** `WebTestClient.bindToApplicationContext(context).build()` wires the test client to route requests through this context's registered controllers and advice, entirely in-memory.
3. **Request issued.** `client.get().uri("/products/999").exchange()` builds and dispatches a `GET /products/999` request through the reactive dispatch machinery.
4. **Controller returns an error signal.** `ProductController.get(999)` checks `id != 1` (true here) and returns `Mono.error(new ProductNotFoundException(999))` — in the reactive world, this is the equivalent of throwing an exception, but expressed as an error signal on the `Mono` rather than a thrown `Throwable` on the calling thread.
5. **Exception handling.** WebFlux's exception-resolution mechanism, seeing the error signal propagate, finds `ErrorHandler`'s `@ExceptionHandler(ProductNotFoundException.class)` method (registered via the same context), invokes it, and applies its `@ResponseStatus(NOT_FOUND)` to the response.
6. **Response captured.** `.exchange()` completes with a response carrying status `404` and a JSON body `{"error":"Product not found: 999"}`.
7. **Assertions.** `.expectStatus().isNotFound()` and `.expectBody().jsonPath("$.error").isEqualTo(...)` inspect that captured response and confirm both facts — proving the reactive error-handling pipeline (`Mono.error` → `@ExceptionHandler` → status + body) works correctly end to end, the WebFlux equivalent of the `MockMvc` exception-handling verification from the Spring MVC Test card.

```
GET /products/999
   -> ProductController.get(999) -> Mono.error(ProductNotFoundException)
   -> WebFlux exception resolution -> ErrorHandler.handleNotFound
   -> 404 + {"error": "Product not found: 999"}
   -> expectStatus().isNotFound() -- check
   -> expectBody().jsonPath("$.error")... -- check
```

## 7. Gotchas & takeaways

> Gotcha: `WebTestClient`'s fluent assertions (`.expectStatus()`, `.expectBody()`) internally handle subscribing to and waiting for the reactive response, but code that steps *outside* that fluent chain (like Level 2's `.returnResult(...).getResponseBody()` followed by manual `.block(...)`) reintroduces the same blocking-in-a-reactive-context concerns the `WebClient` card raised — acceptable in test code operating on a known-finite response, but a reminder that `WebTestClient` doesn't magically make blocking safe, it just doesn't require it for the common assertion cases.

- `WebTestClient` is the reactive-stack test client, filling the role `MockMvc` fills for the Servlet stack — supporting both in-memory (`bindToController`/`bindToApplicationContext`) and real-server (`bindToServer`) modes behind one consistent fluent API.
- Its ability to test streaming `Flux` responses (multiple emitted items over time) is a capability `MockMvc` has no equivalent for, since the Servlet stack has no concept of an incrementally-emitting response body.
- `bindToApplicationContext(...)` exercises full context configuration (including `@ControllerAdvice`), just like `MockMvc.webAppContextSetup(...)` does — the deliberate choice between narrow and full-configuration testing applies here exactly as it did for `MockMvc`.
- `WebTestClient` can also test traditional (non-reactive) Spring MVC endpoints, making it a viable single test client choice for projects mixing MVC and WebFlux controllers.
