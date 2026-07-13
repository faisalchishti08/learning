---
card: microservices
gi: 427
slug: mockmvc-webtestclient
title: "MockMvc / WebTestClient"
---

## 1. What it is

**`MockMvc`** and **`WebTestClient`** are the two client APIs Spring provides for driving HTTP-shaped requests through your application's real web-dispatch machinery in a test, and asserting on the result with a fluent, readable API. `MockMvc` targets the servlet stack (Spring MVC): it sends a request through `DispatcherServlet` *without* opening a real network socket — everything happens in-process, in-memory, but through the genuine routing, filter, and serialization pipeline. `WebTestClient` targets both the reactive stack (Spring WebFlux) and, when configured against a real port, any HTTP server at all — it can run entirely in-memory like `MockMvc`, or make genuine network calls against a running server, using the same fluent assertion API either way.

## 2. Why & when

You reach for `MockMvc` or `WebTestClient` specifically because calling a controller method directly, as plain Java, skips everything that actually makes an HTTP endpoint behave like an HTTP endpoint:

- **Routing is real.** `mockMvc.perform(get("/orders/42"))` proves the path actually maps to the method you think it maps to — a direct method call can't catch a typo'd `@GetMapping` path or an ambiguous route collision.
- **Serialization is real.** The request body is actually deserialized from JSON by the same `HttpMessageConverter` machinery production uses, and the response body is actually serialized back — catching mapping mismatches a direct call, which just passes Java objects around, would never see.
- **Validation and exception handling are real.** `@Valid` constraint checks and `@ExceptionHandler`/`@ControllerAdvice` mappings only run as part of the dispatch pipeline — see [web layer tests](0425-web-layer-tests-webmvctest-webfluxtest.md) for how this matters for `@WebMvcTest`/`@WebFluxTest` slices specifically.
- **The assertion API reads like the HTTP contract it's checking**, chaining status code, header, and body assertions in one fluent call, which keeps tests readable as specifications of behavior rather than as implementation-detail checks.
- **`WebTestClient` additionally works against a real running server**, so the exact same test code can run in-memory against a mocked slice *or* over real sockets against a fully booted application (with `webEnvironment = RANDOM_PORT`) — letting you reuse test logic across a component-level and a more integration-flavored check.

You reach for `MockMvc` for servlet-based (Spring MVC) endpoints and `WebTestClient` for reactive (Spring WebFlux) endpoints, or whenever you want a single client capable of testing both in-memory and over a real port.

## 3. Core concept

Picture a mystery-shopper program for a retail chain. `MockMvc` is a shopper who walks through a real, physically-built store replica — real aisles, real checkout scanners, real receipt printer — but the whole replica sits inside a single closed warehouse, not connected to the actual public street. `WebTestClient` is a shopper who can do the exact same walk-through in that same closed warehouse, *or* drive to an actual live store and shop there for real, using the identical shopping checklist either way. Both shoppers interact with the real point-of-sale system, not a cardboard cutout of one — the only difference is whether real sockets and a real network are involved.

Concretely, both APIs share the same three-part structure:

1. **Build the request** — `.perform(get("/orders/42"))` for `MockMvc`, `.get().uri("/orders/42")` for `WebTestClient` — specifying method, path, headers, and body.
2. **Execute it against real dispatch machinery** — either in-memory (both APIs support this) or, for `WebTestClient` only, over a real socket against a genuinely running server.
3. **Assert on the response fluently** — `.andExpect(status().isOk())` for `MockMvc`, `.expectStatus().isOk()` for `WebTestClient` — chaining status, header, and body checks, with `WebTestClient` additionally supporting reactive-aware assertions (`.expectBody().jsonPath(...)`) that understand `Mono`/`Flux` response bodies.

```java
// MockMvc -- servlet stack, always in-memory
mockMvc.perform(get("/orders/42").accept(MediaType.APPLICATION_JSON))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.orderId").value("42"));

// WebTestClient -- reactive stack, or servlet stack over a real port
webTestClient.get().uri("/orders/42").accept(MediaType.APPLICATION_JSON)
        .exchange()
        .expectStatus().isOk()
        .expectBody().jsonPath("$.orderId").isEqualTo("42");
```

Both assertions check exactly the same thing — a 200 status and a specific JSON field — but `WebTestClient`'s fluent chain is built around `exchange()`, reflecting that the underlying call may genuinely be asynchronous and non-blocking.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="MockMvc drives requests in-memory through the servlet dispatch stack only; WebTestClient can drive requests in-memory through the reactive dispatch stack, or over a real socket against any running HTTP server, using the same fluent assertion API">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">MockMvc</text>
  <rect x="40" y="35" width="220" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="150" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">in-memory only</text>
  <text x="150" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">servlet stack (Spring MVC)</text>

  <text x="480" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">WebTestClient</text>
  <rect x="330" y="35" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="405" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">in-memory</text>
  <text x="405" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">reactive (WebFlux)</text>

  <rect x="490" y="35" width="150" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="565" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">real socket</text>
  <text x="565" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">any running server</text>

  <rect x="330" y="130" width="310" height="70" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="485" y="155" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">same fluent assertion API</text>
  <text x="485" y="173" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">.expectStatus() / .expectBody().jsonPath(...)</text>
  <text x="485" y="189" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">works identically in both modes</text>

  <line x1="405" y1="95" x2="405" y2="130" stroke="#6db33f" stroke-dasharray="3,2"/>
  <line x1="565" y1="95" x2="485" y2="130" stroke="#f0883e" stroke-dasharray="3,2"/>
</svg>

MockMvc always runs in-memory against the servlet stack; WebTestClient can run in-memory against the reactive stack or over a real socket, using one consistent assertion API.

## 5. Runnable example

Scenario: an `OrderController` returning order details, exercised first conceptually, then with real `MockMvc`, then with `WebTestClient` handling a production-flavored asynchronous/reactive response with a genuinely tricky edge case (an empty result vs. a not-found error).

### Level 1 — Basic

```java
// File: RequestResponseModelBasic.java -- models the CONCEPT both MockMvc
// and WebTestClient are built around: build a request, dispatch it through
// routing logic, get back a status + body, assert on both.
import java.util.*;

public class RequestResponseModelBasic {
    record Request(String method, String path) {}
    record Response(int status, String body) {}

    // A tiny stand-in for DispatcherServlet's routing.
    static Response dispatch(Request req, Map<String, String> orders) {
        if (!req.method().equals("GET")) return new Response(405, "");
        String id = req.path().replace("/orders/", "");
        String order = orders.get(id);
        if (order == null) return new Response(404, "{\"error\":\"not found\"}");
        return new Response(200, "{\"orderId\":\"" + id + "\",\"details\":\"" + order + "\"}");
    }

    public static void main(String[] args) {
        Map<String, String> orders = Map.of("42", "Widget x3");
        Response found = dispatch(new Request("GET", "/orders/42"), orders);
        Response missing = dispatch(new Request("GET", "/orders/99"), orders);

        System.out.println("found -> status=" + found.status() + " body=" + found.body());
        System.out.println("missing -> status=" + missing.status() + " body=" + missing.body());
    }
}
```

How to run: `java RequestResponseModelBasic.java`

This isolates the shape of "build a request, dispatch it, check status and body" that both `MockMvc` and `WebTestClient` are ultimately built around, before introducing any real Spring dependencies. It's deliberately simple so the framework-specific pieces added in later levels are easy to recognize against this baseline.

### Level 2 — Intermediate

```java
// File: MockMvcRealShapeIntermediate.java -- the SAME scenario, now in its
// REAL Spring MVC form using MockMvc and @WebMvcTest, as it would really be
// written and run under Maven/Gradle with spring-boot-starter-test on the
// classpath.
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockitoBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class MockMvcRealShapeIntermediate {

    interface OrderLookupService { Map<String, Object> lookup(String id); }

    @RestController
    static class OrderController {
        private final OrderLookupService service;
        OrderController(OrderLookupService service) { this.service = service; }

        @GetMapping(value = "/orders/{id}", produces = MediaType.APPLICATION_JSON_VALUE)
        Map<String, Object> getOrder(@PathVariable String id) { return service.lookup(id); }
    }

    @WebMvcTest(OrderController.class)
    static class OrderControllerTest {
        @Autowired MockMvc mockMvc;
        @MockitoBean OrderLookupService orderLookupService;

        @Test
        void returnsOrderDetailsAsJson() throws Exception {
            when(orderLookupService.lookup("42")).thenReturn(Map.of("orderId", "42", "items", 3));

            mockMvc.perform(get("/orders/42").accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.orderId").value("42"))
                    .andExpect(jsonPath("$.items").value(3));
        }
    }
}
```

How to run: requires `spring-boot-starter-test` and `spring-boot-starter-web` on the classpath; run as a JUnit 5 test via `mvn test` or your IDE's test runner.

`mockMvc.perform(get(...))` dispatches a real, in-memory request through Spring MVC's actual routing. `jsonPath("$.orderId")` parses the *actual serialized JSON response body* and asserts on a specific field — a genuinely different check than asserting on a raw Java `Map`, because it proves the real `HttpMessageConverter` serialized the response the way a real HTTP client would receive it.

### Level 3 — Advanced

```java
// File: WebTestClientReactiveAdvanced.java -- the SAME kind of scenario,
// now on the REACTIVE stack with WebTestClient and @WebFluxTest, handling a
// PRODUCTION-FLAVORED hard case: distinguishing "found nothing" (Mono.empty,
// -> 404) from "found something" using reactive-aware assertions.
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.WebFluxTest;
import org.springframework.boot.test.mock.mockito.MockitoBean;
import org.springframework.http.MediaType;
import org.springframework.http.HttpStatus;
import org.springframework.test.web.reactive.server.WebTestClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;
import reactor.core.publisher.Mono;

import java.util.Map;

import static org.mockito.Mockito.when;

public class WebTestClientReactiveAdvanced {

    interface ReactiveOrderLookupService { Mono<Map<String, Object>> lookup(String id); }

    @RestController
    static class OrderController {
        private final ReactiveOrderLookupService service;
        OrderController(ReactiveOrderLookupService service) { this.service = service; }

        @GetMapping(value = "/orders/{id}", produces = MediaType.APPLICATION_JSON_VALUE)
        Mono<Map<String, Object>> getOrder(@PathVariable String id) {
            return service.lookup(id)
                    .switchIfEmpty(Mono.error(new ResponseStatusException(HttpStatus.NOT_FOUND, "order " + id + " not found")));
        }
    }

    @WebFluxTest(OrderController.class)
    static class OrderControllerReactiveTest {
        @Autowired WebTestClient webTestClient;
        @MockitoBean ReactiveOrderLookupService reactiveOrderLookupService;

        @Test
        void returns200WithBodyWhenOrderEmitsValue() {
            when(reactiveOrderLookupService.lookup("42"))
                    .thenReturn(Mono.just(Map.of("orderId", "42", "items", 3)));

            webTestClient.get().uri("/orders/42").accept(MediaType.APPLICATION_JSON)
                    .exchange()
                    .expectStatus().isOk()
                    .expectBody()
                    .jsonPath("$.orderId").isEqualTo("42")
                    .jsonPath("$.items").isEqualTo(3);
        }

        @Test
        void returns404WhenMonoCompletesEmpty() {
            // The tricky part: Mono.empty() means "completed with NO value", which is
            // subtly different from an error -- switchIfEmpty converts it to a 404.
            when(reactiveOrderLookupService.lookup("missing")).thenReturn(Mono.empty());

            webTestClient.get().uri("/orders/missing").accept(MediaType.APPLICATION_JSON)
                    .exchange()
                    .expectStatus().isNotFound();
        }
    }
}
```

How to run: requires `spring-boot-starter-webflux`, `spring-boot-starter-test`, and Reactor Test on the classpath; run as a JUnit 5 test via `mvn test` or your IDE's test runner.

The hard case is `Mono.empty()` — a reactive publisher that completes successfully but emits *zero* values, which is a genuinely different signal than either "emits a value" or "emits an error," and easy to mishandle if `switchIfEmpty` is forgotten. `WebTestClient.exchange()` subscribes to the reactive response and waits for it to fully resolve (success, empty, or error) before any assertion runs, which is exactly the reactive-aware behavior a synchronous test client cannot provide — asserting on a `Mono` before it has actually completed would be meaningless.

## 6. Walkthrough

Trace `returns404WhenMonoCompletesEmpty` in order. **First**, the `@WebFluxTest`-scoped context boots (or reuses a cached one) with `OrderController` and reactive dispatch infrastructure; `reactiveOrderLookupService` is a `@MockitoBean` stubbed to return `Mono.empty()` for `"missing"`.

**Next**, `webTestClient.get().uri("/orders/missing")...exchange()` sends a real (in-memory, reactive-stack) GET request. Spring WebFlux routes it to `getOrder("missing")`, which calls `service.lookup("missing")`, returning the stubbed `Mono.empty()`.

**Then**, `.switchIfEmpty(Mono.error(new ResponseStatusException(HttpStatus.NOT_FOUND, ...)))` is applied to that empty `Mono`. Because the upstream `Mono` completed with no value (not an error, not a value), `switchIfEmpty`'s replacement publisher activates, converting the empty completion into an error signal carrying a `404` status.

**Finally**, Spring WebFlux's exception handling for `ResponseStatusException` maps that error into an actual HTTP 404 response. `exchange()` waits for this whole reactive pipeline to fully resolve before returning control, and `expectStatus().isNotFound()` asserts against the final, fully-resolved response — passing, because the empty `Mono` was correctly translated into a 404 rather than, say, an empty 200 body (a common reactive-code mistake when `switchIfEmpty` is left out).

```
GET /orders/missing
  -> reactiveOrderLookupService.lookup("missing") returns Mono.empty()
  -> switchIfEmpty triggers: Mono.error(ResponseStatusException(404, "order missing not found"))
  -> WebFlux exception handling maps error -> HTTP 404

Test result: returns404WhenMonoCompletesEmpty PASSED
  expectStatus().isNotFound() -- OK
```

## 7. Gotchas & takeaways

> Forgetting `.exchange()` (or, in `MockMvc`, forgetting that `.perform()` already dispatches synchronously) leads to assertions that silently check nothing meaningful — `WebTestClient`'s fluent builder methods only *configure* the request; nothing is actually sent until `.exchange()` is called, and no reactive pipeline resolves until then either. A test that compiles but never calls `.exchange()` will simply pass or fail for the wrong reasons, if it runs at all.

- `MockMvc` always operates in-memory against the servlet stack; use it for Spring MVC controllers tested via [web layer tests](0425-web-layer-tests-webmvctest-webfluxtest.md)'s `@WebMvcTest`.
- `WebTestClient` operates in-memory against the reactive stack for `@WebFluxTest`, or over a real socket when pointed at a running server (e.g. with `webEnvironment = RANDOM_PORT` in a full [`@SpringBootTest`](0424-springboottest-slices-full-context-tests.md)) — the same test code works in both modes.
- `jsonPath(...)` assertions check the *actual serialized response body*, catching serialization mismatches a direct Java-object comparison would miss entirely.
- For reactive endpoints, always account for `Mono.empty()` as a distinct case from both a value and an error — it's a common source of subtle bugs in endpoint code, and exactly what `WebTestClient`'s reactive-aware `exchange()` is built to test correctly.
- Both APIs pair naturally with [@MockBean / @MockitoBean](0432-mockbean-mockitobean-for-collaborators.md) to keep the collaborator layer scripted while the dispatch machinery under test stays completely real.
