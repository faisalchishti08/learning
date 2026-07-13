---
card: microservices
gi: 432
slug: mockbean-mockitobean-for-collaborators
title: "@MockBean / @MockitoBean for collaborators"
---

## 1. What it is

`@MockBean` (and its replacement, `@MockitoBean`, introduced in Spring Boot 3.4 as `@MockBean` moves toward deprecation) is the annotation that tells Spring's test context to replace a real bean in the `ApplicationContext` with a Mockito mock. Wherever the application would normally `@Autowired` the real implementation, it instead receives the mock — fully scripted, fully controllable, and automatically reset between test methods. This is the mechanism that makes test slices like [`@WebMvcTest`](0425-web-layer-tests-webmvctest-webfluxtest.md) practical at all: a slice loads only a controller, but that controller still needs *something* to satisfy its service dependency, and `@MockBean`/`@MockitoBean` is how that something gets supplied without constructing the real service (and everything the real service, in turn, depends on).

## 2. Why & when

You reach for `@MockBean`/`@MockitoBean` specifically when a Spring-managed bean under test has a dependency you want to control completely, without needing that dependency's real implementation constructed at all:

- **It replaces a bean inside a real Spring context**, which is different from a plain Mockito `@Mock` used in a non-Spring unit test — the mock is actually wired into the `ApplicationContext` via dependency injection, so any bean that `@Autowired`s the mocked type receives the mock automatically, with no manual wiring code.
- **It lets a test slice work at all.** [`@WebMvcTest`](0425-web-layer-tests-webmvctest-webfluxtest.md) doesn't construct your `@Service` beans; if your controller depends on one, the context fails to start unless that dependency is supplied as a `@MockitoBean` (or otherwise excluded).
- **Every stubbed behavior is explicit and scoped to the test**, avoiding the class of bug where a *real* collaborator's side effects (a real database write, a real outbound HTTP call) leak into what's supposed to be a narrowly scoped test.
- **`@MockitoBean` fixes reset-and-caching problems `@MockBean` had.** In older Spring Boot versions, `@MockBean` could interact awkwardly with context caching (see [`@SpringBootTest` slices](0424-springboottest-slices-full-context-tests.md)) — each unique combination of mocked beans created a new cache key, and mock state wasn't always reset as cleanly between tests as expected. `@MockitoBean`, aligned with plain Mockito's JUnit 5 extension model, addresses these more consistently.

You reach for `@MockBean`/`@MockitoBean` whenever a Spring test needs to control a bean's collaborator precisely — almost always paired with a test slice, but also usable inside a full [`@SpringBootTest`](0424-springboottest-slices-full-context-tests.md) when you want most of the real context but need to override one specific bean (a flaky third-party client, for instance).

## 3. Core concept

Picture a theater rehearsal where every actor is real except one role played by a stagehand reading scripted lines off a card. The rest of the cast performs their real parts, interacting with the stand-in exactly as they would with the real actor — cues, timing, blocking all function normally — but the stand-in's every line is entirely predetermined by whoever wrote the cue card for this rehearsal. `@MockBean`/`@MockitoBean` is that cue-card stand-in: it's inserted into the real cast (the real `ApplicationContext`) in place of one real performer, and every other bean that interacts with it does so through completely normal dependency injection, unaware anything has been substituted.

Concretely, using `@MockitoBean` has three parts:

1. **Declaration** — `@MockitoBean OrderLookupService orderLookupService;` on a test class field. Spring's test context registers a Mockito mock of that type into the `ApplicationContext`, replacing (or supplying, if none existed) the real bean.
2. **Scripting** — `when(orderLookupService.lookup("42")).thenReturn(...)` configures what the mock returns for specific inputs, exactly like any Mockito mock, using the familiar `when`/`thenReturn`/`thenThrow` API.
3. **Verification** — `verify(orderLookupService).lookup("42")` (or `verifyNoInteractions(...)`) asserts on how the mock was actually called, letting a test prove not just "the controller returned the right response" but "the controller called its collaborator correctly, or not at all."

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired MockMvc mockMvc;
    @MockitoBean OrderLookupService orderLookupService;

    @Test
    void delegatesToServiceAndReturnsItsResult() throws Exception {
        when(orderLookupService.lookup("42")).thenReturn("{\"orderId\":\"42\"}");
        mockMvc.perform(get("/orders/42")).andExpect(status().isOk());
        verify(orderLookupService).lookup("42");
    }
}
```

`orderLookupService` is never a real implementation here — no real database, no real downstream call — but `OrderController` interacts with it exactly as it would in production, through ordinary dependency injection.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A real Spring ApplicationContext contains a real controller bean; its OrderLookupService dependency is replaced by a MockitoBean mock, wired in via the same dependency injection the real bean would have used, and scripted/verified with Mockito's when and verify API">
  <rect x="30" y="30" width="580" height="140" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="52" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Spring ApplicationContext (test slice)</text>

  <rect x="60" y="70" width="160" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="140" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OrderController</text>
  <text x="140" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">real bean</text>

  <line x1="220" y1="105" x2="330" y2="105" stroke="#f0883e" stroke-width="2"/>
  <text x="275" y="95" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">@Autowired</text>

  <rect x="330" y="70" width="230" height="70" rx="8" fill="#1c2430" stroke="#f85149" stroke-dasharray="4,2"/>
  <text x="445" y="93" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@MockitoBean OrderLookupService</text>
  <text x="445" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Mockito mock, scripted with when()</text>
  <text x="445" y="126" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">checked with verify()</text>

  <text x="320" y="195" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">the controller is unaware its collaborator was substituted</text>
</svg>

The controller is real and wired through normal dependency injection; its collaborator is a Mockito mock substituted directly into the same context.

## 5. Runnable example

Scenario: an `OrderController` depending on `OrderLookupService`. We model the substitution idea in plain Java first, then show the real `@MockitoBean` shape, then handle a production-flavored case: verifying a controller correctly propagates arguments to a mocked collaborator and reacts to different scripted outcomes.

### Level 1 — Basic

```java
// File: BeanSubstitutionBasic.java -- models the CORE idea @MockitoBean
// automates: swap a real dependency for a scripted stand-in, wired in via
// the SAME constructor injection the real bean would have used.
public class BeanSubstitutionBasic {
    interface OrderLookupService { String lookup(String orderId); }

    static class OrderController {
        private final OrderLookupService service;
        OrderController(OrderLookupService service) { this.service = service; } // ordinary DI
        String handleGet(String orderId) { return service.lookup(orderId); }
    }

    // A hand-rolled stand-in for what Mockito generates automatically for @MockitoBean.
    static class ScriptedOrderLookupService implements OrderLookupService {
        private final java.util.Map<String, String> scriptedResponses = new java.util.HashMap<>();
        void when(String orderId, String response) { scriptedResponses.put(orderId, response); }
        public String lookup(String orderId) {
            System.out.println("[ScriptedOrderLookupService] lookup(" + orderId + ") -- no real service involved");
            return scriptedResponses.get(orderId);
        }
    }

    public static void main(String[] args) {
        ScriptedOrderLookupService mock = new ScriptedOrderLookupService();
        mock.when("42", "{\"orderId\":\"42\",\"items\":3}");

        OrderController controller = new OrderController(mock); // same DI point a real service would occupy
        System.out.println("Controller result: " + controller.handleGet("42"));
    }
}
```

How to run: `java BeanSubstitutionBasic.java`

`ScriptedOrderLookupService` occupies exactly the dependency-injection slot a real `OrderLookupService` implementation would occupy — `OrderController`'s constructor has no idea whether it received a real service or a scripted stand-in. This is precisely what `@MockitoBean` automates inside a real Spring context: the substitution point is identical, only the mechanism for creating the stand-in (Mockito's dynamic proxy generation, versus a hand-rolled class here) differs.

### Level 2 — Intermediate

```java
// File: MockitoBeanRealShapeIntermediate.java -- the SAME substitution, now
// in its REAL Spring Boot form using @MockitoBean inside a @WebMvcTest, as
// it would really be written and run under Maven/Gradle with
// spring-boot-starter-test (Spring Boot 3.4+) on the classpath.
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class MockitoBeanRealShapeIntermediate {

    interface OrderLookupService { String lookup(String orderId); }

    @RestController
    static class OrderController {
        private final OrderLookupService service;
        OrderController(OrderLookupService service) { this.service = service; }

        @GetMapping("/orders/{id}")
        String getOrder(@PathVariable String id) { return service.lookup(id); }
    }

    @WebMvcTest(OrderController.class)
    static class OrderControllerTest {
        @Autowired MockMvc mockMvc;
        @MockitoBean OrderLookupService orderLookupService;

        @Test
        void delegatesToServiceAndReturnsItsResult() throws Exception {
            when(orderLookupService.lookup("42")).thenReturn("{\"orderId\":\"42\"}");

            mockMvc.perform(get("/orders/42"))
                    .andExpect(status().isOk())
                    .andExpect(content().string("{\"orderId\":\"42\"}"));

            // Verify the controller called its collaborator with the RIGHT argument.
            verify(orderLookupService).lookup("42");
        }
    }
}
```

How to run: requires Spring Boot 3.4+ (for `@MockitoBean`; earlier versions use `org.springframework.boot.test.mock.mockito.MockBean` with the same usage pattern), `spring-boot-starter-test`, and `spring-boot-starter-web` on the classpath; run as a JUnit 5 test via `mvn test` or your IDE's test runner.

`@MockitoBean OrderLookupService orderLookupService` registers a Mockito mock directly into the `@WebMvcTest`-scoped `ApplicationContext`, which `OrderController` receives through its normal constructor injection. `when(...).thenReturn(...)` scripts the response, and `verify(orderLookupService).lookup("42")` confirms the controller actually called `lookup` with exactly `"42"` — proving correct argument propagation, not just a correct final HTTP response.

### Level 3 — Advanced

```java
// File: MockitoBeanMultipleOutcomesAdvanced.java -- the SAME controller,
// now handling a PRODUCTION-FLAVORED hard case: scripting THREE different
// outcomes from the SAME mocked collaborator across different test methods
// -- success, a domain exception mapped to 404, and an unexpected runtime
// exception mapped to 500 -- proving the controller's error-mapping logic
// handles the full range of what a real service could do.
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.HttpStatus;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.bind.annotation.*;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class MockitoBeanMultipleOutcomesAdvanced {

    static class OrderNotFoundException extends RuntimeException {
        OrderNotFoundException(String id) { super("order not found: " + id); }
    }

    interface OrderLookupService { String lookup(String orderId); }

    @RestController
    static class OrderController {
        private final OrderLookupService service;
        OrderController(OrderLookupService service) { this.service = service; }

        @GetMapping("/orders/{id}")
        String getOrder(@PathVariable String id) { return service.lookup(id); }

        @ExceptionHandler(OrderNotFoundException.class)
        @ResponseStatus(HttpStatus.NOT_FOUND)
        void handleNotFound() {}

        @ExceptionHandler(RuntimeException.class)
        @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
        void handleUnexpected() {}
    }

    @WebMvcTest(OrderController.class)
    static class OrderControllerErrorMappingTest {
        @Autowired MockMvc mockMvc;
        @MockitoBean OrderLookupService orderLookupService;

        @Test
        void returns200OnSuccess() throws Exception {
            when(orderLookupService.lookup("42")).thenReturn("{\"orderId\":\"42\"}");
            mockMvc.perform(get("/orders/42")).andExpect(status().isOk());
        }

        @Test
        void returns404OnDomainException() throws Exception {
            when(orderLookupService.lookup("missing")).thenThrow(new OrderNotFoundException("missing"));
            mockMvc.perform(get("/orders/missing")).andExpect(status().isNotFound());
        }

        @Test
        void returns500OnUnexpectedException() throws Exception {
            // Scripting a DIFFERENT, unrelated failure mode from the SAME mock --
            // e.g. the real service's database connection dropped mid-call.
            when(orderLookupService.lookup("boom")).thenThrow(new IllegalStateException("connection pool exhausted"));
            mockMvc.perform(get("/orders/boom")).andExpect(status().isInternalServerError());
        }
    }
}
```

How to run: requires the same Spring Boot 3.4+ test dependencies as Level 2; run as a JUnit 5 test via `mvn test` or your IDE's test runner.

Each test method scripts a completely different outcome from `orderLookupService.lookup(...)` — a successful return, a specific domain exception, and an unrelated runtime exception — and each is independent: because `@MockitoBean` resets mock interactions between test methods automatically, scripting `thenThrow` for `"boom"` in the third test doesn't leak into or affect the first test's scripted success for `"42"`. This is what lets one mocked collaborator exercise a controller's *entire* error-mapping surface across a small number of focused tests, each proving one specific status-code mapping is correct.

## 6. Walkthrough

Trace `returns500OnUnexpectedException` in order. **First**, the `@WebMvcTest`-scoped context boots (or reuses a cached one) with `OrderController` and `orderLookupService` registered as a fresh `@MockitoBean` mock — Spring's test framework resets mock state before this test method runs, so no stubbing from a previous test method carries over.

**Next**, `when(orderLookupService.lookup("boom")).thenThrow(new IllegalStateException("connection pool exhausted"))` scripts this specific mock to throw when called with `"boom"` — simulating a real service encountering an unexpected infrastructure failure, something no domain-specific exception type was written to model.

**Then**, `mockMvc.perform(get("/orders/boom"))` dispatches a real request through Spring MVC's routing to `getOrder("boom")`, which calls `service.lookup("boom")`. Because `orderLookupService` is the mock, this call doesn't touch any real logic — it immediately throws the scripted `IllegalStateException`.

**Finally**, that exception propagates out of `getOrder`, and Spring MVC's exception-resolution machinery looks for a matching `@ExceptionHandler`. `handleUnexpected`, annotated for `RuntimeException.class`, matches (since `IllegalStateException` is a `RuntimeException`, and no more specific handler applies), mapping the response to `HttpStatus.INTERNAL_SERVER_ERROR`. `mockMvc`'s assertion `status().isInternalServerError()` passes, confirming the controller's catch-all error mapping works correctly for a failure mode the mock scripted but that a hand-written fake would rarely think to simulate.

```
GET /orders/boom
  -> orderLookupService.lookup("boom") [MOCKED] throws IllegalStateException("connection pool exhausted")
  -> no OrderNotFoundException handler matches (wrong exception type)
  -> RuntimeException handler matches -> mapped to HTTP 500

Test result: returns500OnUnexpectedException PASSED
  status = 500 Internal Server Error
```

## 7. Gotchas & takeaways

> `@MockBean` and `@MockitoBean` are not drop-in identical — mixing them across test classes in the same suite can create separate context-cache entries even when the rest of the configuration is identical, because Spring treats them as different context customizations. Standardize on `@MockitoBean` in any Spring Boot 3.4+ codebase, and migrate `@MockBean` usages deliberately rather than leaving both scattered through the suite.

- `@MockitoBean` substitutes a Mockito mock directly into the real `ApplicationContext`, which is what makes narrow test slices like [`@WebMvcTest`/`@WebFluxTest`](0425-web-layer-tests-webmvctest-webfluxtest.md) and [`@DataJpaTest`](0426-data-layer-tests-datajpatest-etc.md) possible without constructing every real dependency transitively.
- Script every outcome a real collaborator could plausibly produce — success, expected domain exceptions, and unexpected runtime exceptions — to exercise a controller's full error-mapping surface cheaply.
- Pair scripted stubbing (`when...thenReturn`) with call verification (`verify(...)`) when the test's point is proving *how* a collaborator was called, not just what the final HTTP response looked like.
- Mock state resets automatically between test methods within a class, so tests can safely script different, even contradictory, behaviors from the same mocked type across different methods.
- `@MockitoBean` inside a full [`@SpringBootTest`](0424-springboottest-slices-full-context-tests.md) is a legitimate way to keep most of a real context while overriding just one flaky or expensive real dependency, not only a tool for narrow slices.
