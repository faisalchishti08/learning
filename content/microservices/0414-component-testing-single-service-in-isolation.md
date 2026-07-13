---
card: microservices
gi: 414
slug: component-testing-single-service-in-isolation
title: "Component testing (single service in isolation)"
---

## 1. What it is

A **component test** exercises one whole microservice through its real, external API boundary — sending it actual HTTP requests or actual messages, exactly like a real caller would — while every dependency *outside* the service (other services, third-party APIs) is replaced with a stub or virtual double. The service's own internals, including its own database or broker where practical, stay real. It's the layer directly above [integration testing](0413-integration-testing-service-its-db-broker.md) and directly below [end-to-end testing](0417-end-to-end-testing-its-fragility.md) in the [test pyramid](0411-test-pyramid-for-microservices.md): broader than testing one class, narrower than testing the whole system.

## 2. Why & when

You write a component test when you need confidence that a service behaves correctly *as a whole, from the outside*, without paying the cost and fragility of running every other service it talks to. This fills a real gap that unit and integration tests leave open: a service can have perfectly correct classes and perfectly correct database queries, and still be wired together wrong — the wrong exception mapped to the wrong HTTP status, a validation rule that only fires when checked at the controller level, a header that never gets read by the layer that's supposed to read it.

- **Wiring bugs only show up end-to-end within the service.** Dependency injection misconfigurations, filter ordering issues, or a `@ControllerAdvice` that doesn't actually catch the exception it claims to — none of these are visible from a single class's unit test.
- **You get real API-contract confidence without a live dependency graph.** By stubbing out downstream services (with a tool like WireMock — see [service virtualization](0419-service-virtualization-stubbing-dependencies.md)) instead of running them for real, the test stays fast and deterministic while still exercising the service's actual request/response handling, serialization, and status-code logic.
- **It isolates fault, cleanly.** If a component test for `OrderService` fails, the bug is inside `OrderService` — its stubbed dependencies returned exactly what the test told them to, so the service's own code is what misbehaved. Compare that to an end-to-end test failure, which could be caused by any of several real services.
- **It's the natural place to test a service's resilience to a misbehaving dependency** — what happens when the stubbed `PaymentClient` returns a 500, or times out? A component test can simulate that deterministically in a way a live dependency rarely lets you reproduce on demand.

## 3. Core concept

Picture a component test as taking a single finished car off the assembly line and running it on a dynamometer — a machine that spins the wheels and measures real engine output, real transmission behavior, real braking — without needing an actual road, actual traffic, or actual other cars. It's the real vehicle, tested rigorously as a complete unit, in a controlled environment that simulates the outside world just enough to give an honest answer.

The defining line is the service's own network boundary:

- **Inside the boundary, everything is real**: the real Spring context, the real controllers, the real internal service classes, and — for a meaningful component test — usually a real (containerized) database too, so the test also incidentally validates the integration layer.
- **Outside the boundary, everything is stubbed**: any HTTP call to another service is intercepted by a stub (WireMock is the standard tool) that returns a scripted response instead of hitting a real network address.
- **The test drives the service exactly like a real caller would**: an HTTP client sending real requests to the service's real endpoints (e.g. Spring's `TestRestTemplate` or `WebTestClient` against a running embedded server), asserting on the real HTTP response — status code, headers, body — not on internal method calls.

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
class OrderServiceComponentTest {
    @RegisterExtension
    static WireMockExtension paymentStub = WireMockExtension.newInstance().build();

    @Test
    void rejectsCheckoutWhenPaymentServiceDeclines() {
        paymentStub.stubFor(post("/charge").willReturn(aResponse().withStatus(402)));
        ResponseEntity<String> response = restTemplate.postForEntity("/orders/checkout", request, String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.PAYMENT_REQUIRED);
    }
}
```

The service under test is fully running, with a real embedded server and real internal wiring; only `PaymentService` — genuinely a separate deployable — is replaced by `paymentStub`, a scripted HTTP server that returns exactly the response the test needs to exercise a specific behavior.

## 4. Diagram

<svg viewBox="0 0 640 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A component test drives the service under test through its real HTTP API with the service's own internals and database real, while every downstream dependency such as a payment service is replaced by a stub" font-family="sans-serif">
  <rect x="30" y="30" width="90" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="54" fill="#79c0ff" font-size="10" text-anchor="middle">Test client</text>
  <line x1="120" y1="50" x2="180" y2="50" stroke="#79c0ff" stroke-width="2"/>
  <text x="150" y="42" fill="#79c0ff" font-size="9" text-anchor="middle">real HTTP</text>

  <rect x="180" y="20" width="260" height="140" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="310" y="40" fill="#e6edf3" font-size="11" text-anchor="middle">OrderService (real, fully wired)</text>
  <rect x="200" y="55" width="100" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="250" y="76" fill="#8b949e" font-size="9" text-anchor="middle">Controller</text>
  <rect x="320" y="55" width="100" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="370" y="76" fill="#8b949e" font-size="9" text-anchor="middle">Domain logic</text>
  <rect x="260" y="105" width="140" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="330" y="126" fill="#8b949e" font-size="9" text-anchor="middle">real database</text>

  <line x1="440" y1="90" x2="500" y2="90" stroke="#f0883e" stroke-width="2" stroke-dasharray="4,2"/>
  <text x="470" y="80" fill="#f0883e" font-size="9" text-anchor="middle">stubbed HTTP</text>
  <rect x="500" y="65" width="110" height="50" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="555" y="88" fill="#f0883e" font-size="9" text-anchor="middle">PaymentService</text>
  <text x="555" y="103" fill="#8b949e" font-size="8" text-anchor="middle">WireMock stub</text>

  <text x="335" y="200" fill="#8b949e" font-size="10" text-anchor="middle">everything inside the box is real; everything outside is a scripted stub</text>
</svg>

A component test drives the real service through its real API boundary while replacing every external dependency with a controllable stub.

## 5. Runnable example

Scenario: an order-checkout HTTP endpoint that depends on an external `PaymentGateway`. We model the service's real HTTP-handling logic and simulate driving it with real "requests," while the payment dependency is a stub we script per test — first a simple success stub, then a stub returning different responses per call, then a stub simulating a slow/failing dependency to test the service's own timeout-handling behavior.

### Level 1 — Basic

```java
// File: CheckoutComponentBasic.java -- drive the service's real request-
// handling logic through a request/response shape exactly like a caller
// would, with the external PaymentGateway replaced by a scripted stub.
public class CheckoutComponentBasic {
    record CheckoutRequest(String orderId, double amount) {}
    record CheckoutResponse(int statusCode, String body) {}

    interface PaymentGateway { PaymentResult charge(double amount); }
    record PaymentResult(boolean approved, String reference) {}

    // The REAL service code under test: request handling, real logic.
    static class OrderService {
        private final PaymentGateway paymentGateway;
        OrderService(PaymentGateway paymentGateway) { this.paymentGateway = paymentGateway; }

        CheckoutResponse handleCheckout(CheckoutRequest request) {
            if (request.amount() <= 0) return new CheckoutResponse(400, "invalid amount");
            PaymentResult result = paymentGateway.charge(request.amount());
            if (!result.approved()) return new CheckoutResponse(402, "payment declined");
            return new CheckoutResponse(200, "order " + request.orderId() + " confirmed, ref=" + result.reference());
        }
    }

    // A STUB standing in for the external payment service (like a WireMock stub in a real component test).
    static class StubPaymentGateway implements PaymentGateway {
        public PaymentResult charge(double amount) { return new PaymentResult(true, "ref-123"); }
    }

    static void assertTrue(String label, boolean condition) {
        System.out.println((condition ? "PASS" : "FAIL") + ": " + label);
    }

    public static void main(String[] args) {
        OrderService service = new OrderService(new StubPaymentGateway());

        CheckoutResponse response = service.handleCheckout(new CheckoutRequest("order-1", 49.99));
        assertTrue("checkout succeeds through the real handler with a stubbed gateway",
                response.statusCode() == 200 && response.body().contains("order-1 confirmed"));
    }
}
```

How to run: `java CheckoutComponentBasic.java`

`OrderService.handleCheckout` is exercised exactly the way a real caller would call it — a request object in, a response object out — with the entire method's real logic running (validation, calling the gateway, mapping the result to a status code). Only `PaymentGateway` is replaced, by `StubPaymentGateway`, which always approves. This is a component test in miniature: the unit under test is the *whole service's request handling*, not one isolated class, but the dependency that lives outside the service is scripted rather than real.

### Level 2 — Intermediate

```java
// File: CheckoutComponentScriptedStub.java -- the SAME service, now with a
// SCRIPTED stub that returns a DIFFERENT response per call (the way
// WireMock lets you script a sequence of stub responses), so one test run
// can exercise both the approved path and the declined path.
import java.util.*;

public class CheckoutComponentScriptedStub {
    record CheckoutRequest(String orderId, double amount) {}
    record CheckoutResponse(int statusCode, String body) {}
    interface PaymentGateway { PaymentResult charge(double amount); }
    record PaymentResult(boolean approved, String reference) {}

    static class OrderService {
        private final PaymentGateway paymentGateway;
        OrderService(PaymentGateway paymentGateway) { this.paymentGateway = paymentGateway; }
        CheckoutResponse handleCheckout(CheckoutRequest request) {
            if (request.amount() <= 0) return new CheckoutResponse(400, "invalid amount");
            PaymentResult result = paymentGateway.charge(request.amount());
            if (!result.approved()) return new CheckoutResponse(402, "payment declined");
            return new CheckoutResponse(200, "order " + request.orderId() + " confirmed, ref=" + result.reference());
        }
    }

    // A scripted stub: each call pops the NEXT scripted result, like configuring
    // WireMock scenarios/stateful behavior for a sequence of calls.
    static class ScriptedPaymentGateway implements PaymentGateway {
        private final Deque<PaymentResult> scriptedResults;
        ScriptedPaymentGateway(List<PaymentResult> script) { this.scriptedResults = new ArrayDeque<>(script); }
        public PaymentResult charge(double amount) {
            if (scriptedResults.isEmpty()) throw new IllegalStateException("stub script exhausted");
            return scriptedResults.poll();
        }
    }

    static void assertTrue(String label, boolean condition) {
        System.out.println((condition ? "PASS" : "FAIL") + ": " + label);
    }

    public static void main(String[] args) {
        ScriptedPaymentGateway scriptedGateway = new ScriptedPaymentGateway(List.of(
                new PaymentResult(true, "ref-1"),
                new PaymentResult(false, null)
        ));
        OrderService service = new OrderService(scriptedGateway);

        CheckoutResponse first = service.handleCheckout(new CheckoutRequest("order-1", 30.00));
        assertTrue("first scripted call: approved", first.statusCode() == 200);

        CheckoutResponse second = service.handleCheckout(new CheckoutRequest("order-2", 15.00));
        assertTrue("second scripted call: declined", second.statusCode() == 402 && second.body().equals("payment declined"));
    }
}
```

How to run: `java CheckoutComponentScriptedStub.java`

`ScriptedPaymentGateway` returns a *different* result on each call, popped from a pre-configured sequence — exactly how a real WireMock stub can be configured to return different responses across successive calls in the same test (via scenarios or stateful stubbing). This lets one component test exercise two different code paths through `handleCheckout` — the approved branch and the declined branch — without needing two separately wired test setups, and without ever touching a real payment service.

### Level 3 — Advanced

```java
// File: CheckoutComponentResilience.java -- the SAME service, now with a
// stub that simulates the dependency being SLOW or throwing an exception
// (the production-flavored hard case: what does OUR service do when a
// downstream dependency misbehaves?), verifying our own timeout/error
// handling rather than the dependency's behavior.
public class CheckoutComponentResilience {
    record CheckoutRequest(String orderId, double amount) {}
    record CheckoutResponse(int statusCode, String body) {}
    interface PaymentGateway { PaymentResult charge(double amount) throws PaymentGatewayException; }
    record PaymentResult(boolean approved, String reference) {}
    static class PaymentGatewayException extends Exception {
        PaymentGatewayException(String message) { super(message); }
    }

    // The service now handles a FAILING dependency explicitly, mapping it to a 503
    // instead of letting the exception crash the request -- the behavior under test.
    static class OrderService {
        private final PaymentGateway paymentGateway;
        OrderService(PaymentGateway paymentGateway) { this.paymentGateway = paymentGateway; }
        CheckoutResponse handleCheckout(CheckoutRequest request) {
            if (request.amount() <= 0) return new CheckoutResponse(400, "invalid amount");
            PaymentResult result;
            try {
                result = paymentGateway.charge(request.amount());
            } catch (PaymentGatewayException e) {
                return new CheckoutResponse(503, "payment gateway unavailable: " + e.getMessage());
            }
            if (!result.approved()) return new CheckoutResponse(402, "payment declined");
            return new CheckoutResponse(200, "order " + request.orderId() + " confirmed, ref=" + result.reference());
        }
    }

    // A stub simulating the dependency throwing (standing in for WireMock configured
    // to return a fault, e.g. aResponse().withFault(CONNECTION_RESET_BY_PEER)).
    static class FailingPaymentGateway implements PaymentGateway {
        public PaymentResult charge(double amount) throws PaymentGatewayException {
            throw new PaymentGatewayException("connection reset (simulated network fault)");
        }
    }

    static void assertTrue(String label, boolean condition) {
        System.out.println((condition ? "PASS" : "FAIL") + ": " + label);
    }

    public static void main(String[] args) {
        OrderService serviceWithFailingDependency = new OrderService(new FailingPaymentGateway());

        CheckoutResponse response = serviceWithFailingDependency.handleCheckout(new CheckoutRequest("order-3", 99.00));
        assertTrue("a failing downstream dependency maps to 503, not a crash",
                response.statusCode() == 503 && response.body().contains("payment gateway unavailable"));
        assertTrue("the failure reason from the dependency is surfaced in the response",
                response.body().contains("connection reset"));
    }
}
```

How to run: `java CheckoutComponentResilience.java`

`FailingPaymentGateway` deliberately throws on every call, standing in for a WireMock stub configured to simulate a network fault or a downstream 5xx — a scenario that's genuinely hard to reproduce on demand against a real, healthy payment service, but is exactly the kind of thing a component test needs to verify. The behavior under test isn't the payment gateway's failure — that's scripted, not real — it's whether *our* service, `OrderService`, handles that failure gracefully: catching `PaymentGatewayException` and mapping it to a `503` with a useful message, instead of letting the exception propagate uncaught and return an opaque `500` (or crash the request thread entirely). This is precisely the kind of resilience behavior that's much harder to verify in a full [end-to-end test](0417-end-to-end-testing-its-fragility.md), where you can't easily force a real dependency to fail on command.

## 6. Walkthrough

Trace `CheckoutComponentResilience.main` in order. **First**, `serviceWithFailingDependency.handleCheckout(new CheckoutRequest("order-3", 99.00))` runs. `request.amount()` is `99.00`, which passes the `<= 0` guard, so execution proceeds into the `try` block. **Next**, `paymentGateway.charge(99.00)` is called on `FailingPaymentGateway`, which immediately throws `PaymentGatewayException("connection reset (simulated network fault)")` — no real network was involved; the stub is scripted to always fail, exactly like a WireMock stub configured with `withFault(...)`.

**Then**, control jumps to the `catch (PaymentGatewayException e)` block inside `handleCheckout`. It builds and returns `new CheckoutResponse(503, "payment gateway unavailable: connection reset (simulated network fault)")` — the exception never escapes `handleCheckout`, and no other part of `OrderService`'s logic (like the `result.approved()` check, which would have thrown a `NullPointerException` on the never-assigned `result`) is ever reached, because the `catch` block returns before falling through.

**Finally**, back in `main`, `response.statusCode()` is checked to be `503` and `response.body()` is checked to contain both the general failure message and the specific underlying reason (`"connection reset"`) — proving the service not only *recovers* from the downstream failure but also *surfaces enough information* in its own response for a caller (or an on-call engineer reading a log) to understand why the checkout failed.

```
handleCheckout(order-3, $99.00) with FailingPaymentGateway
  -> paymentGateway.charge(99.00) throws PaymentGatewayException
  -> caught inside handleCheckout
  -> CheckoutResponse(503, "payment gateway unavailable: connection reset (simulated network fault)")
PASS: a failing downstream dependency maps to 503, not a crash
PASS: the failure reason from the dependency is surfaced in the response
```

## 7. Gotchas & takeaways

> Reusing the same stub configuration across many component tests can hide bugs: if every test stubs `PaymentGateway` to always approve, you'll never exercise the declined path, the timeout path, or the malformed-response path — and those are often exactly the paths with the least real-world testing otherwise. Deliberately script the unhappy paths, not just the happy one.

- A component test's boundary is the service's own real API — HTTP in, HTTP out — with only *external* dependencies stubbed; the service's own internals, and often its own database, stay real (see [integration testing](0413-integration-testing-service-its-db-broker.md) for testing that database layer specifically).
- Use component tests to verify wiring bugs (wrong status codes, misconfigured exception handling) that unit tests of individual classes can't see.
- Component tests are the best place to test a service's *own* resilience behavior — timeout handling, fallback logic — against a scripted failure, because you control exactly when and how the stubbed dependency fails.
- Tools like WireMock (see [service virtualization](0419-service-virtualization-stubbing-dependencies.md)) are the real-world equivalent of the hand-rolled stubs above: a scriptable fake HTTP server your service talks to over real HTTP, just not over a real network to a real other service.
- Component tests sit between [integration tests](0413-integration-testing-service-its-db-broker.md) and [end-to-end tests](0417-end-to-end-testing-its-fragility.md) in the [test pyramid](0411-test-pyramid-for-microservices.md) — broader confidence than a single class, without the cost and flakiness of running every real dependency.
