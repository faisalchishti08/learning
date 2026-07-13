---
card: microservices
gi: 419
slug: service-virtualization-stubbing-dependencies
title: "Service virtualization / stubbing dependencies"
---

## 1. What it is

**Service virtualization** is the practice of replacing a real dependency your service calls — another microservice, a third-party API, a legacy system — with a lightweight, scriptable stand-in that speaks the same protocol (usually HTTP) and returns responses you control, without ever hitting the real thing. Tools like **WireMock** are the standard way to do this in the Spring/Java ecosystem: they run an actual small HTTP server, in-process or as a sidecar, that you configure with rules like "when a `POST` arrives at `/charge` with this body, respond with this status and this JSON." Your service under test doesn't know the difference — it makes a real HTTP call, over real sockets, to what it believes is the dependency, and gets back a real, scripted HTTP response.

## 2. Why & when

You reach for service virtualization specifically to make [component tests](0414-component-testing-single-service-in-isolation.md) — and sometimes local development itself — fast, deterministic, and independent of dependencies you don't own or can't control:

- **Dependencies you don't own can't be scripted to fail on demand.** You need to test what happens when a third-party payment provider returns a 500, times out, or sends back malformed JSON — a real payment provider's sandbox environment rarely lets you reliably trigger those exact conditions whenever your test suite runs.
- **Real dependencies make tests slow and flaky.** A real network call to a real service — even one you own — adds latency, and adds a chance of failing for reasons that have nothing to do with the code under test, exactly the fragility problem discussed in [end-to-end testing & its fragility](0417-end-to-end-testing-its-fragility.md).
- **Dependencies you don't own may not have a usable test environment at all**, or might rate-limit you, charge you per call, or simply not exist yet if you're developing against an API another team hasn't finished building.
- **Local development gets faster and more independent.** A developer working on `OrderService` shouldn't need `PaymentService`, `InventoryService`, and three other teams' services all running locally just to exercise their own code — pointing at virtualized stubs for everything except the service actually being worked on removes that whole class of setup friction.

You reach for a hand-rolled fake (as in earlier unit-testing examples) when a dependency is accessed through a Java interface you control; you reach for service virtualization specifically when the dependency is accessed over the network — HTTP, gRPC — because a virtualized stub needs to actually behave like a network service: real status codes, real headers, real latency you can simulate, real malformed responses you can script.

## 3. Core concept

Picture a flight simulator used to train pilots. It isn't a real plane, and it doesn't need a real sky, real air traffic control, or real weather — but from inside the cockpit, every gauge, every control response, and every scenario the trainer configures (an engine failure, a storm, a bird strike) behaves exactly like the real thing would. A virtualized dependency is that simulator for your service's dependency: your service's HTTP client makes a completely real request over a completely real socket, and the response it gets back is indistinguishable, at the protocol level, from what the real service would have sent — except the "storm" (a timeout, a malformed body, a 503) is scripted, repeatable, and available on demand.

Concretely, a virtualized stub configuration has three parts:

1. **A request matcher** — which incoming requests this rule applies to (path, method, headers, body content).
2. **A scripted response** — the exact status code, headers, and body to return when a request matches.
3. **Optional behavior** — a simulated delay (to test timeout handling), a stateful sequence (different responses on the 1st vs. 2nd call, useful for simulating "fails once then recovers"), or a deliberate fault (a dropped connection, a malformed response body).

```java
@RegisterExtension
static WireMockExtension paymentStub = WireMockExtension.newInstance().options(wireMockConfig().port(8089)).build();

@Test
void handlesSlowPaymentGatewayGracefully() {
    paymentStub.stubFor(post(urlEqualTo("/charge"))
            .willReturn(aResponse().withStatus(200).withFixedDelay(3000).withBody("{\"approved\":true}")));

    // service under test calls http://localhost:8089/charge and must handle the 3s delay
    // according to its own configured timeout, without the test needing a real slow payment provider.
}
```

`withFixedDelay(3000)` makes the stub deliberately slow — something you could rarely, reliably reproduce against a real third-party sandbox on demand — letting the test verify the service's own timeout and fallback behavior deterministically.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A service under test makes a real HTTP call, believing it is talking to a real dependency, but the request actually lands on a virtualized stub server that returns a scripted response instead of contacting the real third-party or downstream service">
  <rect x="30" y="70" width="150" height="70" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="105" y="100" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="105" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(real code under test)</text>

  <line x1="180" y1="105" x2="260" y2="105" stroke="#79c0ff" stroke-width="2"/>
  <text x="220" y="95" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">real HTTP call</text>

  <rect x="260" y="70" width="160" height="70" rx="10" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="340" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">WireMock stub</text>
  <text x="340" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">scripted responses</text>
  <text x="340" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(status, delay, body)</text>

  <rect x="470" y="70" width="140" height="70" rx="10" fill="#1c2430" stroke="#f85149" stroke-dasharray="4,2"/>
  <text x="540" y="100" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">real PaymentService</text>
  <text x="540" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">NEVER contacted</text>

  <text x="340" y="175" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">the service under test cannot tell the difference at the protocol level</text>
</svg>

The service under test makes a genuine network call; the virtualized stub intercepts it and returns a fully scripted response, leaving the real dependency untouched.

## 5. Runnable example

Scenario: `OrderService` depends on an external `PaymentGateway` over HTTP. We simulate a virtualized stub server in plain Java (standing in for WireMock's configuration model), first with a basic scripted response, then with request matching so different requests get different responses, then with a fault injection scenario to test a hard, production-flavored timeout-handling case.

### Level 1 — Basic

```java
// File: VirtualizedStubBasic.java -- a minimal STUB SERVER (standing in for
// WireMock) that returns a fixed, scripted response for any request,
// exercised by a real caller exactly like a real HTTP client would call it.
public class VirtualizedStubBasic {
    // A scripted stub: no real network, no real payment provider, just a
    // pre-configured response -- the core idea behind service virtualization.
    static class StubPaymentServer {
        record ScriptedResponse(int statusCode, String body) {}
        private ScriptedResponse configuredResponse = new ScriptedResponse(200, "{\"approved\":true,\"ref\":\"stub-ref-1\"}");

        void stubFor(int statusCode, String body) { configuredResponse = new ScriptedResponse(statusCode, body); }
        ScriptedResponse handle(String path, String requestBody) {
            System.out.println("[StubPaymentServer] received " + path + " with body " + requestBody + " -> returning scripted response");
            return configuredResponse;
        }
    }

    // A caller that behaves exactly like a real HTTP client would.
    static String callPaymentGateway(StubPaymentServer stub, double amount) {
        StubPaymentServer.ScriptedResponse response = stub.handle("/charge", "{\"amount\":" + amount + "}");
        return "status=" + response.statusCode() + " body=" + response.body();
    }

    public static void main(String[] args) {
        StubPaymentServer stub = new StubPaymentServer();
        System.out.println(callPaymentGateway(stub, 49.99));
    }
}
```

How to run: `java VirtualizedStubBasic.java`

`StubPaymentServer` plays the role of a WireMock instance: it has a `handle` method that looks exactly like a real server's request handling from the caller's perspective, but internally it just returns whatever was pre-configured with `stubFor`. `callPaymentGateway` doesn't know or care that it's talking to a stub instead of a real payment provider — this is the essential property of service virtualization: the calling code is completely unaware.

### Level 2 — Intermediate

```java
// File: VirtualizedStubMatching.java -- the SAME stub server, now with
// REQUEST MATCHING (like WireMock's stubFor(...).withRequestBody(...)), so
// different requests get different scripted responses -- letting one test
// exercise both an approved and a declined payment without any real gateway.
import java.util.*;

public class VirtualizedStubMatching {
    record ScriptedResponse(int statusCode, String body) {}
    record StubRule(String matchIfBodyContains, ScriptedResponse response) {}

    static class StubPaymentServer {
        private final List<StubRule> rules = new ArrayList<>();
        private final ScriptedResponse defaultResponse = new ScriptedResponse(404, "{\"error\":\"no stub matched\"}");

        void stubFor(String matchIfBodyContains, int statusCode, String body) {
            rules.add(new StubRule(matchIfBodyContains, new ScriptedResponse(statusCode, body)));
        }

        ScriptedResponse handle(String path, String requestBody) {
            for (StubRule rule : rules) {
                if (requestBody.contains(rule.matchIfBodyContains())) {
                    System.out.println("[StubPaymentServer] " + path + " matched rule '" + rule.matchIfBodyContains() + "'");
                    return rule.response();
                }
            }
            System.out.println("[StubPaymentServer] " + path + " matched NO rule, returning default");
            return defaultResponse;
        }
    }

    public static void main(String[] args) {
        StubPaymentServer stub = new StubPaymentServer();
        stub.stubFor("\"cardNumber\":\"4111", 200, "{\"approved\":true,\"ref\":\"approved-ref\"}"); // Visa test card -> approved
        stub.stubFor("\"cardNumber\":\"4000\"", 402, "{\"approved\":false,\"reason\":\"insufficient_funds\"}"); // declined test card

        ScriptedResponse approved = stub.handle("/charge", "{\"amount\":50,\"cardNumber\":\"4111111111111111\"}");
        System.out.println("approved case -> status=" + approved.statusCode() + " body=" + approved.body());

        ScriptedResponse declined = stub.handle("/charge", "{\"amount\":50,\"cardNumber\":\"4000\"}");
        System.out.println("declined case -> status=" + declined.statusCode() + " body=" + declined.body());
    }
}
```

How to run: `java VirtualizedStubMatching.java`

Two rules are configured, each matching a different request-body pattern — a realistic mirror of how WireMock's `withRequestBody(containing(...))` matchers work. The same stub server now scripts two different real-world outcomes (approved, declined) based purely on what's in the incoming request, which is exactly how a real test would drive both the happy path and an error path through a service's real request-handling code without ever configuring two entirely separate stub instances.

### Level 3 — Advanced

```java
// File: VirtualizedStubFaultInjection.java -- the SAME stub server, now
// injecting a REALISTIC FAULT (a simulated timeout) that a real third-party
// sandbox would rarely let you trigger reliably, and testing that OUR
// service's own timeout-handling code degrades gracefully -- the
// production-flavored hard case service virtualization is best at.
public class VirtualizedStubFaultInjection {
    record ScriptedResponse(int statusCode, String body, long simulatedDelayMs) {}

    static class StubPaymentServer {
        private ScriptedResponse configured = new ScriptedResponse(200, "{\"approved\":true}", 0);
        void stubWithDelay(int statusCode, String body, long delayMs) {
            configured = new ScriptedResponse(statusCode, body, delayMs);
        }
        // Returns the scripted response, but reports how long it "took" --
        // standing in for WireMock's withFixedDelay(...).
        ScriptedResponse handle() { return configured; }
    }

    // The REAL client code under test: it must respect its OWN configured
    // timeout, regardless of how slow the dependency scripted itself to be.
    static class PaymentClient {
        private final StubPaymentServer server;
        private final long clientTimeoutMs;
        PaymentClient(StubPaymentServer server, long clientTimeoutMs) {
            this.server = server; this.clientTimeoutMs = clientTimeoutMs;
        }

        String charge(double amount) {
            ScriptedResponse response = server.handle();
            if (response.simulatedDelayMs() > clientTimeoutMs) {
                return "TIMEOUT: gateway took " + response.simulatedDelayMs() + "ms, exceeding our " + clientTimeoutMs + "ms timeout -- falling back";
            }
            return "status=" + response.statusCode() + " body=" + response.body();
        }
    }

    public static void main(String[] args) {
        StubPaymentServer stub = new StubPaymentServer();

        // Case 1: gateway responds within our timeout budget.
        stub.stubWithDelay(200, "{\"approved\":true}", 300);
        PaymentClient fastClient = new PaymentClient(stub, 2000);
        System.out.println("Fast case: " + fastClient.charge(50.0));

        // Case 2: gateway is scripted to be catastrophically slow -- something
        // a real third-party sandbox would rarely reproduce reliably on demand.
        stub.stubWithDelay(200, "{\"approved\":true}", 8000);
        PaymentClient timeoutTestClient = new PaymentClient(stub, 2000);
        System.out.println("Slow case: " + timeoutTestClient.charge(50.0));
    }
}
```

How to run: `java VirtualizedStubFaultInjection.java`

`stubWithDelay` scripts exactly how slow the fake dependency should claim to be — including an 8-second delay that would be genuinely difficult to reproduce reliably against a real payment provider's sandbox on demand (you can't ask a real vendor to "please be exactly 8 seconds slow for this one test run"). `PaymentClient.charge` checks the scripted delay against its own configured timeout and returns a graceful fallback message instead of hanging — this is the actual behavior under test: not whether the stub is slow (that's scripted, not real), but whether *our* client code respects its own timeout budget and degrades gracefully when a dependency is too slow, exactly the kind of resilience behavior [component tests](0414-component-testing-single-service-in-isolation.md) built on service virtualization are best positioned to verify deterministically.

## 6. Walkthrough

Trace `VirtualizedStubFaultInjection.main` in order. **First**, `stub.stubWithDelay(200, "{\"approved\":true}", 300)` configures the stub to report a 300ms simulated delay. `fastClient.charge(50.0)` calls `server.handle()`, which returns that configured response. Inside `charge`, `response.simulatedDelayMs()` (300) is checked against `clientTimeoutMs` (2000) — `300 > 2000` is `false`, so the timeout branch is skipped, and `charge` returns the normal success string: `"status=200 body={\"approved\":true}"`.

**Next**, `stub.stubWithDelay(200, "{\"approved\":true}", 8000)` reconfigures the *same* stub to now report an 8000ms delay — instantly, with no real 8-second wait, because the delay is only a scripted number being compared, not an actual `Thread.sleep`. **Then**, `timeoutTestClient.charge(50.0)` runs, using its own `clientTimeoutMs` of 2000. `response.simulatedDelayMs()` (8000) is checked: `8000 > 2000` is `true`, so the timeout branch fires and `charge` returns `"TIMEOUT: gateway took 8000ms, exceeding our 2000ms timeout -- falling back"` instead of the success body.

**Finally**, both results print, showing the same `PaymentClient` code correctly branching between a normal response and a graceful timeout fallback purely based on scripted stub behavior — proving the client's own timeout-handling logic works correctly under both conditions, deterministically, on every single test run, which would be far harder to guarantee against a real, variable-latency third-party dependency.

```
Fast case: status=200 body={"approved":true}
Slow case: TIMEOUT: gateway took 8000ms, exceeding our 2000ms timeout -- falling back
```

## 7. Gotchas & takeaways

> A stub that's configured once and never revisited slowly drifts away from what the real dependency actually does — the real `PaymentGateway` team might add a required field, or change an error response shape, and your stubs keep happily returning the old shape forever, giving your tests false confidence. Pair service virtualization with [contract testing](0415-contract-testing-consumer-driven-contracts.md) against the real provider wherever the dependency is another service you can coordinate with — the stub keeps your tests fast, and the contract keeps the stub honest.

- Service virtualization targets dependencies reached over the network (HTTP, gRPC); dependencies reached through a plain Java interface are better handled with a hand-rolled fake or mock, as in [unit testing services](0412-unit-testing-services.md).
- The biggest practical win is scripting failure modes — timeouts, malformed responses, specific error codes — that a real dependency, especially a third-party one, rarely lets you reproduce reliably on demand.
- WireMock and similar tools run a real HTTP server your code talks to over real sockets, so the code under test genuinely cannot tell it isn't talking to the real dependency — this is what makes the test meaningful.
- Virtualized stubs make [component tests](0414-component-testing-single-service-in-isolation.md) fast and deterministic, and they're just as useful for local development as for automated tests — no need to run five other teams' services locally just to work on your own.
- A stub only proves your code handles the *scripted* shape correctly; it says nothing about whether the real dependency still matches that shape — that residual risk is what [contract testing](0415-contract-testing-consumer-driven-contracts.md) and a thin layer of [end-to-end tests](0417-end-to-end-testing-its-fragility.md) exist to catch.
