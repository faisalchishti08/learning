---
card: microservices
gi: 425
slug: web-layer-tests-webmvctest-webfluxtest
title: "Web layer tests (@WebMvcTest, @WebFluxTest)"
---

## 1. What it is

`@WebMvcTest` and `@WebFluxTest` are Spring Boot test slices (see [@SpringBootTest slices & full-context tests](0424-springboottest-slices-full-context-tests.md)) that boot **only the web layer** — controllers, filters, `@ControllerAdvice` exception handlers, JSON serialization, and request-mapping infrastructure — for the servlet stack (`@WebMvcTest`, Spring MVC) or the reactive stack (`@WebFluxTest`, Spring WebFlux). Everything below the web layer — services, repositories, real databases — is deliberately left out of the context; any controller dependency has to be supplied as a mock. The result is a test that verifies exactly one thing precisely: does this controller correctly translate HTTP requests into calls on its collaborators, and correctly translate the collaborators' results back into HTTP responses?

## 2. Why & when

You reach for a web-layer slice whenever you want to test controller behavior — routing, request validation, status codes, response shape, exception-to-HTTP-status mapping — without paying the cost, or accepting the ambiguity, of booting real services and a real database:

- **It isolates web-layer bugs from everything else.** If a `@WebMvcTest` fails, the bug is in the controller, a filter, or the JSON mapping — not in a repository or a downstream service, because those aren't even in the context to blame.
- **It's fast**, because the object graph is small: a handful of web-infrastructure beans and the controllers under test, not the full application.
- **It exercises real HTTP-adjacent machinery** that a plain unit test of a controller class, called directly as a Java method, would skip entirely — request-body deserialization, validation annotations (`@Valid`), content negotiation, and `@ExceptionHandler` mapping all actually run, because [MockMvc or WebTestClient](0427-mockmvc-webtestclient.md) drives requests through the real Spring MVC/WebFlux dispatch machinery, not through direct method calls.
- **`@WebFluxTest` specifically matters for reactive controllers** — ones returning `Mono<T>` or `Flux<T>` — because a plain method-level unit test can't easily verify that a reactive pipeline subscribes, emits, and completes the way a real reactive HTTP client would observe it; `WebTestClient` against a `@WebFluxTest` slice can.

You reach for a web-layer slice for the large majority of your controller-level tests, and reserve full [`@SpringBootTest`](0424-springboottest-slices-full-context-tests.md) for the smaller number of tests that specifically need to prove the controller wires correctly to *real* services underneath it.

## 3. Core concept

Picture a restaurant's front-of-house staff — the servers taking orders and delivering plates — being trained and evaluated completely separately from the kitchen. You can verify a server correctly writes down an order, correctly relays modifications, and correctly explains a "we're out of that" response to a customer, all without a single real dish ever being cooked — the kitchen is played by a stand-in who just hands back whatever plate the test script says to hand back. `@WebMvcTest` and `@WebFluxTest` are that isolated front-of-house rehearsal: the controller (the server) is real, the service layer (the kitchen) is a scripted stand-in.

Concretely, a web-layer slice test has three ingredients:

1. **`@WebMvcTest(SomeController.class)` or `@WebFluxTest(SomeController.class)`** — scopes the context to that controller (and shared web infrastructure like `@ControllerAdvice`), narrowing which class is actually under test rather than loading every controller in the application.
2. **`@MockBean`/`@MockitoBean`** for every collaborator the controller `@Autowired`s — a service, a repository, anything the controller calls — so its behavior is fully scripted and deterministic (see [@MockBean / @MockitoBean for collaborators](0432-mockbean-mockitobean-for-collaborators.md)).
3. **A driver** — `MockMvc` for `@WebMvcTest`, `WebTestClient` for `@WebFluxTest` — that sends a real, fully-dispatched HTTP-shaped request through Spring's actual routing and serialization machinery, and lets you assert on the actual HTTP response (see [MockMvc / WebTestClient](0427-mockmvc-webtestclient.md)).

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired MockMvc mockMvc;
    @MockitoBean OrderLookupService orderLookupService;

    @Test
    void returns404WhenOrderMissing() throws Exception {
        when(orderLookupService.lookup("missing")).thenThrow(new OrderNotFoundException("missing"));
        mockMvc.perform(get("/orders/missing")).andExpect(status().isNotFound());
    }
}
```

The controller, its `@ExceptionHandler`, and Spring MVC's dispatch machinery are all real; `orderLookupService` is entirely scripted, so the test proves the controller correctly maps a domain exception to a 404 — a mapping that lives in the controller layer and belongs in a controller-layer test.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A WebMvcTest or WebFluxTest slice loads only the controller and web infrastructure; a mocked service stands in for the real service layer; MockMvc or WebTestClient drives a real HTTP-shaped request through the real dispatch machinery and asserts on the real response">
  <rect x="30" y="30" width="160" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="110" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">MockMvc / WebTestClient</text>
  <text x="110" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">sends real HTTP-shaped request</text>

  <line x1="190" y1="60" x2="250" y2="60" stroke="#79c0ff" stroke-width="2"/>

  <rect x="250" y="20" width="150" height="120" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="325" y="42" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Web layer (real)</text>
  <text x="325" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Controller</text>
  <text x="325" y="76" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@ControllerAdvice</text>
  <text x="325" y="92" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JSON (de)serialization</text>
  <text x="325" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Valid validation</text>

  <line x1="400" y1="80" x2="460" y2="80" stroke="#f0883e" stroke-width="2" stroke-dasharray="4,2"/>

  <rect x="460" y="50" width="150" height="60" rx="8" fill="#1c2430" stroke="#f85149" stroke-dasharray="4,2"/>
  <text x="535" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Service (mocked)</text>
  <text x="535" y="92" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">scripted, no real DB</text>

  <text x="320" y="190" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">only the web layer and its real dispatch machinery are under test;</text>
  <text x="320" y="208" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">everything below the controller boundary is scripted</text>
</svg>

MockMvc or WebTestClient drives a real request through the real controller and web infrastructure; the service layer beneath it is entirely mocked.

## 5. Runnable example

Scenario: an `OrderController` (servlet-style) that looks up an order via an `OrderLookupService` and returns 404 when it's missing. We model the essential behavior in plain Java first, then show the real `@WebMvcTest` shape, then handle a production-flavored validation-plus-exception-mapping case.

### Level 1 — Basic

```java
// File: OrderControllerLogicBasic.java -- the CORE controller logic, in
// plain Java, before wiring it into Spring at all: given an order id,
// return a body or a 404-shaped result.
import java.util.*;

public class OrderControllerLogicBasic {
    static class OrderNotFoundException extends RuntimeException {
        OrderNotFoundException(String orderId) { super("order not found: " + orderId); }
    }

    interface OrderLookupService { String lookup(String orderId); }

    static class OrderController {
        final OrderLookupService service;
        OrderController(OrderLookupService service) { this.service = service; }

        record HttpResult(int status, String body) {}

        HttpResult getOrder(String orderId) {
            try {
                String order = service.lookup(orderId);
                return new HttpResult(200, order);
            } catch (OrderNotFoundException e) {
                return new HttpResult(404, "{\"error\":\"" + e.getMessage() + "\"}");
            }
        }
    }

    public static void main(String[] args) {
        OrderLookupService scriptedFound = id -> "{\"orderId\":\"" + id + "\",\"items\":3}";
        OrderController controller = new OrderController(scriptedFound);
        System.out.println(controller.getOrder("order-1"));
    }
}
```

How to run: `java OrderControllerLogicBasic.java`

This isolates the core routing decision a web layer test cares about: given a scripted `OrderLookupService` result, what HTTP status and body does the controller produce? There's no real Spring context yet — this level just proves the logic itself is sound before wiring in the real web-dispatch machinery.

### Level 2 — Intermediate

```java
// File: OrderControllerSpringShapeIntermediate.java -- the SAME controller,
// now shown in its REAL Spring Boot form using actual @WebMvcTest-style
// annotations and MockMvc, as it would really be written and run under
// Maven/Gradle with the spring-boot-starter-test dependency on the classpath.
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockitoBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.http.HttpStatus;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class OrderControllerSpringShapeIntermediate {

    static class OrderNotFoundException extends RuntimeException {
        OrderNotFoundException(String orderId) { super("order not found: " + orderId); }
    }

    interface OrderLookupService { String lookup(String orderId); }

    @RestController
    static class OrderController {
        private final OrderLookupService service;
        OrderController(OrderLookupService service) { this.service = service; }

        @GetMapping(value = "/orders/{id}", produces = MediaType.APPLICATION_JSON_VALUE)
        String getOrder(@PathVariable("id") String id) {
            return service.lookup(id);
        }

        @ExceptionHandler(OrderNotFoundException.class)
        @ResponseStatus(HttpStatus.NOT_FOUND)
        void handleNotFound() { /* body intentionally empty -- status code is the assertion */ }
    }

    @WebMvcTest(OrderController.class)
    static class OrderControllerTest {
        @Autowired MockMvc mockMvc;
        @MockitoBean OrderLookupService orderLookupService;

        @Test
        void returnsOrderJsonWhenFound() throws Exception {
            when(orderLookupService.lookup("order-1")).thenReturn("{\"orderId\":\"order-1\",\"items\":3}");
            mockMvc.perform(get("/orders/order-1"))
                    .andExpect(status().isOk())
                    .andExpect(content().json("{\"orderId\":\"order-1\",\"items\":3}"));
        }

        @Test
        void returns404WhenOrderMissing() throws Exception {
            when(orderLookupService.lookup("missing")).thenThrow(new OrderNotFoundException("missing"));
            mockMvc.perform(get("/orders/missing")).andExpect(status().isNotFound());
        }
    }
}
```

How to run: this file requires the `spring-boot-starter-test`, `spring-boot-starter-web`, and JUnit 5 dependencies on the classpath; run it as a JUnit 5 test via `mvn test` or your IDE's test runner, not with plain `java`.

`@WebMvcTest(OrderController.class)` boots only `OrderController` and Spring MVC's dispatch infrastructure; `@MockitoBean OrderLookupService` supplies a fully scripted collaborator. `mockMvc.perform(get(...))` sends a request through the *real* `DispatcherServlet` machinery — real `@PathVariable` binding, real content negotiation, real `@ExceptionHandler` resolution — which is exactly what distinguishes this from calling `controller.getOrder("order-1")` directly as a plain Java method: the routing and exception-mapping logic is actually exercised, not assumed.

### Level 3 — Advanced

```java
// File: OrderControllerValidationAdvanced.java -- the SAME controller, now
// handling a PRODUCTION-FLAVORED hard case: request-body validation via
// @Valid failing BEFORE the service is ever called, verified with
// @WebMvcTest so the real validation and exception-mapping pipeline runs.
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockitoBean;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.bind.annotation.*;

import static org.mockito.Mockito.verifyNoInteractions;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class OrderControllerValidationAdvanced {

    record CreateOrderRequest(@NotBlank String customerId, @Min(1) int quantity) {}

    interface OrderCreationService { String create(CreateOrderRequest request); }

    @RestController
    static class OrderController {
        private final OrderCreationService service;
        OrderController(OrderCreationService service) { this.service = service; }

        @PostMapping(value = "/orders", consumes = MediaType.APPLICATION_JSON_VALUE)
        @ResponseStatus(HttpStatus.CREATED)
        String createOrder(@org.springframework.web.bind.annotation.RequestBody @jakarta.validation.Valid CreateOrderRequest request) {
            return service.create(request);
        }
    }

    @WebMvcTest(OrderController.class)
    static class OrderControllerValidationTest {
        @Autowired MockMvc mockMvc;
        @MockitoBean OrderCreationService orderCreationService;

        @Test
        void rejectsInvalidRequestBeforeCallingService() throws Exception {
            // quantity = 0 violates @Min(1); customerId is blank -- BOTH violate @Valid constraints.
            String invalidBody = "{\"customerId\":\"\",\"quantity\":0}";

            mockMvc.perform(post("/orders")
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(invalidBody))
                    .andExpect(status().isBadRequest());

            // The KEY assertion: the service must NEVER be invoked, because validation
            // failed in the web layer BEFORE the request reached the service boundary.
            verifyNoInteractions(orderCreationService);
        }

        @Test
        void acceptsValidRequestAndDelegatesToService() throws Exception {
            org.mockito.Mockito.when(orderCreationService.create(org.mockito.ArgumentMatchers.any()))
                    .thenReturn("order-99");

            String validBody = "{\"customerId\":\"cust-1\",\"quantity\":2}";
            mockMvc.perform(post("/orders")
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(validBody))
                    .andExpect(status().isCreated());
        }
    }
}
```

How to run: requires the same Spring Boot test dependencies as Level 2, plus `spring-boot-starter-validation` on the classpath for `@Valid`/`@NotBlank`/`@Min`; run as a JUnit 5 test via `mvn test` or your IDE.

The hard case here is proving a *negative*: that an invalid request never reaches `orderCreationService` at all, because Spring's validation pipeline rejects it first. `verifyNoInteractions(orderCreationService)` is the assertion that makes this concrete — without it, a bug where validation is accidentally bypassed (say, the `@Valid` annotation gets dropped during a refactor) would still return a 400 if the service happened to also validate internally, silently masking a regression in the web layer specifically.

## 6. Walkthrough

Trace `rejectsInvalidRequestBeforeCallingService` in order. **First**, JUnit starts the `@WebMvcTest`-scoped Spring context (or reuses a cached one, per [context caching](0424-springboottest-slices-full-context-tests.md)) containing `OrderController` and MVC infrastructure, with `orderCreationService` supplied as a `@MockitoBean` — no real implementation is ever constructed.

**Next**, `mockMvc.perform(post("/orders")...)` sends a POST request with body `{"customerId":"","quantity":0}` through the real `DispatcherServlet`. Spring resolves the request to `createOrder`, and because the parameter is annotated `@Valid`, the framework runs constraint validation on the deserialized `CreateOrderRequest` *before* the method body executes.

**Then**, validation finds two violations: `customerId` is blank (violating `@NotBlank`) and `quantity` is `0` (violating `@Min(1)`). Spring's default behavior on a validation failure is to throw a `MethodArgumentNotValidException`, which Spring MVC's built-in exception handling maps to an HTTP 400 response — `createOrder`'s method body, and therefore `service.create(...)`, is never reached.

**Finally**, `mockMvc` asserts `status().isBadRequest()`, which passes, and `verifyNoInteractions(orderCreationService)` confirms the mock recorded zero calls — proof that the rejection happened in the web layer, not because the (mocked) service happened to also reject the input.

```
POST /orders  body={"customerId":"","quantity":0}
  -> @Valid constraint violations: customerId (NotBlank), quantity (Min)
  -> MethodArgumentNotValidException -> mapped to HTTP 400
  -> orderCreationService.create(...) NEVER invoked

Test result: rejectsInvalidRequestBeforeCallingService PASSED
  status = 400 Bad Request
  verifyNoInteractions(orderCreationService) = OK (0 interactions)
```

## 7. Gotchas & takeaways

> A `@WebMvcTest` that mocks the service but forgets to assert `verifyNoInteractions` (or an equivalent "never called" check) for a validation-rejection test can pass even after someone accidentally removes the `@Valid` annotation — the mocked service, having no real logic, simply returns whatever was stubbed regardless of whether validation should have blocked the call first. Always assert both the HTTP outcome *and* that the collaborator was (or wasn't) invoked when the test's whole point is proving something never reaches the service layer.

- `@WebMvcTest` and `@WebFluxTest` load only web-layer beans; anything a controller depends on must be supplied as a mock, which is exactly why they pair so tightly with [@MockBean / @MockitoBean](0432-mockbean-mockitobean-for-collaborators.md).
- Use [MockMvc or WebTestClient](0427-mockmvc-webtestclient.md) to drive requests through the *real* dispatch machinery — calling a controller method directly as plain Java skips routing, validation, and exception mapping entirely, defeating the purpose of the slice.
- `@WebFluxTest` matters specifically for reactive endpoints returning `Mono`/`Flux`, where `WebTestClient`'s reactive-aware assertions can verify subscription and emission behavior that a synchronous call cannot.
- Pair web-layer slices with [data layer tests](0426-data-layer-tests-datajpatest-etc.md) to cover the two ends of the stack cheaply, reserving full [`@SpringBootTest`](0424-springboottest-slices-full-context-tests.md) for verifying the layers actually wire together.
- A web-layer test should assert on HTTP-observable behavior — status codes, response bodies, headers — not on internal implementation details a real HTTP client could never see.
