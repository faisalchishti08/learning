---
card: spring-cloud
gi: 121
slug: spring-cloud-contract-consumer-driven-contracts
title: "Spring Cloud Contract (consumer-driven contracts)"
---

## 1. What it is

Spring Cloud Contract lets a service's API be defined as a set of contracts — concrete request/response (or message) examples describing exactly how consumers expect the service to behave — from which it generates both a producer-side test verifying the real implementation actually satisfies each contract, and a consumer-side stub (a WireMock-backed fake) that consumers can run against in their own tests, so both sides of an API relationship stay verifiably in sync without either team needing the other's service actually running to test against.

```groovy
// src/test/resources/contracts/shouldReturnOrder.groovy
Contract.make {
    request {
        method GET()
        url '/orders/42'
    }
    response {
        status OK()
        body(id: 42, status: "CONFIRMED")
        headers { contentType(applicationJson()) }
    }
}
```

```java
// generated automatically FROM the contract above -- fails if the real controller doesn't match it
@Test
void validate_shouldReturnOrder() { ... }
```

## 2. Why & when

Integration testing across service boundaries traditionally means either running the real dependency service during tests (slow, flaky, requires environment setup) or hand-writing mocks that silently drift out of sync with the real service's actual behavior as it evolves — a mock returning a shape the real service stopped producing months ago gives false confidence right up until a production failure reveals the gap. Consumer-driven contract testing solves both problems at once: the contract is the single source of truth for an interaction, a generated producer-side test fails the *producer's* build the moment its implementation diverges from what the contract promises, and a generated consumer-side stub gives the *consumer* something to test against that's mechanically guaranteed to match the producer's actual behavior, since both artifacts are generated from the identical contract definition.

Reach for Spring Cloud Contract when:

- Multiple teams or services depend on a specific API's exact request/response shape, and integration test flakiness or drift between mocked and real behavior has caused production incidents — contracts give both sides an enforced, verifiable agreement rather than an informal, easily-stale understanding.
- Consumer teams want to test against a dependency without needing that dependency's real service running (with real data, real infrastructure) during their own test suite — a generated stub, automatically kept accurate, replaces a hand-maintained mock that would otherwise need manual updates every time the producer's API changes.
- A producer team wants confidence that a change to their implementation doesn't silently break any of their known consumers' expectations — the generated producer-side tests fail the producer's own build immediately if a contract is violated, catching a breaking change before it ships rather than after a consumer reports it.

## 3. Core concept

```
 ONE contract (a request/response example) is the shared source of truth:

        contract
        /      \
       /        \
 producer-side    consumer-side
 test generated   stub generated
       |                |
       v                v
 runs against the    consumers run their OWN
 REAL implementation  tests against this stub
 -- FAILS the build   -- guaranteed to match the
 if behavior diverges    real producer's actual behavior
    from the contract    (since both come from the SAME contract)
```

Neither side manually maintains the other's testing artifact — both the producer's verification test and the consumer's stub are mechanically derived from the identical contract file, which is what guarantees they can never silently drift apart from each other.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single contract file generates both a producer side test that verifies the real implementation and a consumer side WireMock stub that consumers test against with both artifacts guaranteed consistent because they derive from the same source contract">
  <rect x="230" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="48" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">contract (source of truth)</text>

  <rect x="30" y="120" width="220" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="140" y="142" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">producer-side test</text>
  <text x="140" y="156" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">verifies REAL implementation</text>

  <rect x="390" y="120" width="220" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="500" y="142" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">consumer-side stub (WireMock)</text>
  <text x="500" y="156" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">consumers test AGAINST this</text>

  <defs><marker id="a121" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="280" y1="66" x2="150" y2="120" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a121)"/>
  <line x1="360" y1="66" x2="490" y2="120" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a121)"/>
</svg>

Both artifacts trace back to the same single contract file — this common origin is what guarantees they can never drift apart from each other.

## 5. Runnable example

The scenario: model a contract's request/response definition, a producer-side verification derived from it (checking a real implementation against the contract), and a consumer-side stub derived from the same contract (returning the promised response without a real implementation). Start with just the contract as data, then add producer-side verification, then add the consumer-side stub, proving both are consistent because both read the identical contract.

### Level 1 — Basic

A contract, modeled as a plain data structure — the single source of truth both later artifacts derive from.

```java
import java.util.*;

public class ContractTestingLevel1 {
    record Contract(String method, String url, int expectedStatus, Map<String, Object> expectedBody) {}

    public static void main(String[] args) {
        Contract shouldReturnOrder = new Contract(
                "GET", "/orders/42", 200, Map.of("id", 42, "status", "CONFIRMED")
        );

        System.out.println("contract: " + shouldReturnOrder.method() + " " + shouldReturnOrder.url()
                + " -> " + shouldReturnOrder.expectedStatus() + " " + shouldReturnOrder.expectedBody());
    }
}
```

How to run: `java ContractTestingLevel1.java`

`Contract` is just data — a `method`, a `url`, and the expected response — this is the plain-language equivalent of the Groovy/YAML DSL contract file shown in Part 1, before either the producer or consumer artifact is generated from it.

### Level 2 — Intermediate

Add producer-side verification: given a (simulated) real implementation, check it against the contract and fail loudly on any mismatch.

```java
import java.util.*;
import java.util.function.Function;

public class ContractTestingLevel2 {
    record Contract(String method, String url, int expectedStatus, Map<String, Object> expectedBody) {}
    record HttpResponse(int status, Map<String, Object> body) {}

    // stands in for the PRODUCER's real controller/implementation
    static HttpResponse realImplementation(String url) {
        if (url.equals("/orders/42")) {
            return new HttpResponse(200, Map.of("id", 42, "status", "CONFIRMED"));
        }
        return new HttpResponse(404, Map.of());
    }

    // generated FROM the contract -- verifies the real implementation actually matches it
    static void verifyProducer(Contract contract, Function<String, HttpResponse> implementation) {
        HttpResponse actual = implementation.apply(contract.url());
        if (actual.status() != contract.expectedStatus()) {
            throw new AssertionError("status mismatch: expected " + contract.expectedStatus() + " but got " + actual.status());
        }
        if (!actual.body().equals(contract.expectedBody())) {
            throw new AssertionError("body mismatch: expected " + contract.expectedBody() + " but got " + actual.body());
        }
        System.out.println("PRODUCER TEST PASSED: implementation matches contract");
    }

    public static void main(String[] args) {
        Contract shouldReturnOrder = new Contract("GET", "/orders/42", 200, Map.of("id", 42, "status", "CONFIRMED"));

        verifyProducer(shouldReturnOrder, ContractTestingLevel2::realImplementation);
    }
}
```

How to run: `java ContractTestingLevel2.java`

`verifyProducer` calls the real (simulated) implementation and checks its actual response against exactly what the contract promised — this is the mechanism that fails a producer's build the moment their implementation diverges from a contract, and here it passes because `realImplementation` genuinely does return what `shouldReturnOrder` expects.

### Level 3 — Advanced

Add the consumer-side stub, generated from the same contract, and a deliberately broken producer implementation to demonstrate the producer-side test correctly catching a contract violation the stub itself would never reveal to a consumer.

```java
import java.util.*;
import java.util.function.Function;

public class ContractTestingLevel3 {
    record Contract(String method, String url, int expectedStatus, Map<String, Object> expectedBody) {}
    record HttpResponse(int status, Map<String, Object> body) {}

    static void verifyProducer(Contract contract, Function<String, HttpResponse> implementation) {
        HttpResponse actual = implementation.apply(contract.url());
        if (actual.status() != contract.expectedStatus() || !actual.body().equals(contract.expectedBody())) {
            throw new AssertionError("CONTRACT VIOLATION: producer's real implementation does not match the contract");
        }
        System.out.println("PRODUCER TEST PASSED");
    }

    // generated FROM the SAME contract -- a WireMock-style stub the CONSUMER tests against
    static class ConsumerStub {
        Contract contract;
        ConsumerStub(Contract contract) { this.contract = contract; }
        HttpResponse handle(String url) {
            if (url.equals(contract.url())) return new HttpResponse(contract.expectedStatus(), contract.expectedBody());
            return new HttpResponse(404, Map.of());
        }
    }

    // simulates a producer implementation that has DRIFTED from the contract (a real, easy-to-introduce bug)
    static HttpResponse brokenImplementation(String url) {
        if (url.equals("/orders/42")) {
            return new HttpResponse(200, Map.of("id", 42, "status", "PENDING")); // WRONG status value
        }
        return new HttpResponse(404, Map.of());
    }

    public static void main(String[] args) {
        Contract shouldReturnOrder = new Contract("GET", "/orders/42", 200, Map.of("id", 42, "status", "CONFIRMED"));

        // consumer's own test, run against the STUB -- always passes, since the stub is DERIVED FROM the contract
        ConsumerStub stub = new ConsumerStub(shouldReturnOrder);
        HttpResponse stubResponse = stub.handle("/orders/42");
        System.out.println("consumer test against stub: " + stubResponse + " (always matches contract, by construction)");

        // meanwhile, the PRODUCER's real implementation has quietly drifted -- their OWN build should catch this
        try {
            verifyProducer(shouldReturnOrder, ContractTestingLevel3::brokenImplementation);
        } catch (AssertionError e) {
            System.out.println("producer's own build correctly FAILS: " + e.getMessage());
        }
    }
}
```

How to run: `java ContractTestingLevel3.java`

The consumer's test against `stub` always passes, since `ConsumerStub.handle` simply returns whatever the contract specifies, by construction — the consumer has no visibility into the producer's actual implementation at all; meanwhile `verifyProducer` against `brokenImplementation` correctly throws, because that implementation's real response (`status: "PENDING"`) doesn't match the contract's promised `status: "CONFIRMED"` — this is precisely the value proposition: the producer's own build catches this drift immediately, well before a consumer relying on the (contractually correct, but now inaccurate) stub would ever encounter the real, broken behavior in production.

## 6. Walkthrough

Trace both verification paths in Level 3.

1. `stub.handle("/orders/42")` is called — inside `ConsumerStub.handle`, `url.equals(contract.url())` is `true` (`"/orders/42".equals("/orders/42")`), so it returns `new HttpResponse(contract.expectedStatus(), contract.expectedBody())`, which is exactly `HttpResponse(200, {id: 42, status: "CONFIRMED"})` — this response is generated purely from the contract's own data, with no reference to any producer implementation, real or broken.
2. The consumer's `println` reports this stub response, correctly noting it always matches the contract "by construction" — no amount of producer-side drift can ever cause the stub itself to return something inconsistent with the contract, since the stub *is* the contract's data, re-served.
3. `verifyProducer(shouldReturnOrder, ContractTestingLevel3::brokenImplementation)` is called — inside, `implementation.apply("/orders/42")` calls `brokenImplementation`, which returns `HttpResponse(200, {id: 42, status: "PENDING"})`.
4. The status check (`actual.status() != contract.expectedStatus()`) is `false` (both are `200`), but the body check (`!actual.body().equals(contract.expectedBody())`) is `true`, because `{id: 42, status: "PENDING"}` does not equal `{id: 42, status: "CONFIRMED"}` — the combined `if` condition is `true`, so `verifyProducer` throws `AssertionError`.
5. This exception propagates to the `catch` block in `main`, which prints the failure message — in a real Spring Cloud Contract setup, this exact failure would occur automatically as part of the producer's own Maven/Gradle build, blocking that build from succeeding (and, typically, blocking a release) until the implementation is fixed to actually match what the contract promises.

```
consumer's test:  stub.handle("/orders/42") -> {id:42, status:CONFIRMED}  (matches contract ALWAYS, by construction)
producer's test:  verifyProducer(contract, brokenImplementation)
                     -> brokenImplementation returns {id:42, status:PENDING}
                     -> body mismatch vs contract's {id:42, status:CONFIRMED}
                     -> AssertionError -- PRODUCER'S OWN BUILD FAILS
```

## 7. Gotchas & takeaways

> **Gotcha:** a contract only enforces what it actually specifies — a contract asserting only `status: 200` without checking the response body's specific fields would let `brokenImplementation`'s drift (the wrong `status` field value) pass silently, since nothing in a looser contract would have caught it. Writing contracts precise enough to catch the specific behaviors consumers actually depend on (not just "some 200 response came back") is essential to the whole approach's value — an overly loose contract provides a false sense of safety.

- Consumer-driven contract testing's core mechanism is generating both the producer's verification test and the consumer's stub from one shared contract definition, which is what structurally guarantees the two can never silently drift apart from each other, unlike independently hand-maintained mocks and integration tests.
- A producer-side contract violation is caught at the producer's own build time, before any consumer is affected — this shifts a class of integration bug from "discovered in production, or in a flaky end-to-end test" to "caught immediately, locally, in the producer's own CI pipeline."
- A consumer testing against a generated stub gets test isolation (no real producer service needs to be running) without sacrificing accuracy, since the stub's behavior is mechanically derived from, and therefore guaranteed consistent with, whatever the contract actually specifies.
- The next cards in this section cover the concrete mechanics: the contract DSL itself (Groovy/YAML) for actually writing contracts, the Stub Runner/WireMock tooling that serves generated stubs to consumers, and the specific test-generation process on both the producer and consumer sides.
