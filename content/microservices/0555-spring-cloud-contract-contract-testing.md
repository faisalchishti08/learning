---
card: microservices
gi: 555
slug: spring-cloud-contract-contract-testing
title: "Spring Cloud Contract (contract testing)"
---

## 1. What it is

**Spring Cloud Contract** implements [consumer-driven contract testing](0497-consumer-driven-contracts.md) concretely for Spring applications: a provider team writes contracts (Groovy DSL or YAML) describing exactly what requests their API accepts and what responses it returns; Spring Cloud Contract generates both a suite of provider-side tests (verifying the real implementation actually matches every contract) and consumer-side stubs (a WireMock-based fake server that behaves exactly like the contract describes, for consumers to test against without needing the real provider running at all). This turns "does our API still match what consumers expect" and "does our client code still work against the provider's actual contract" into automated, CI-enforced checks, rather than assumptions that quietly go stale.

## 2. Why & when

You reach for Spring Cloud Contract whenever a provider service has consumers whose expectations need to be continuously verified against the provider's actual, evolving behavior:

- **A contract written once and never re-verified is just documentation, prone to going stale the moment the provider's implementation changes** — Spring Cloud Contract generates real, executable tests from the contract that run against the provider's actual code in CI, failing loudly the moment the provider's real behavior diverges from what's contracted, rather than that divergence only being discovered later when a consumer breaks in production.
- **Consumers testing against a real, running instance of the provider is often impractical** — spinning up an entire provider service (with its own database, its own dependencies) just to run a consumer's unit tests is slow and brittle; Spring Cloud Contract's generated stub (a WireMock server configured to respond exactly as the contract specifies) lets consumers test their integration logic quickly and in isolation, without any real provider infrastructure at all.
- **The same contract artifact drives both sides**, which is what makes this genuinely "consumer-driven" rather than just "provider self-documentation" — a contract, once agreed and published, becomes both the provider's test suite input and the consumer's stub source, so both sides are verified against the identical, single source of truth rather than potentially-diverging separate descriptions.
- **You reach for this specifically when a provider has meaningful cross-team (or cross-repository) consumers** whose breakage would otherwise only surface in an integration environment or production — for a service with no external consumers, or where consumer and provider are developed in lockstep by the same team with tight coordination, the overhead of maintaining explicit contracts may not be justified.

## 3. Core concept

Recall the tailor's specification sheet from [consumer-driven contracts](0497-consumer-driven-contracts.md): a written, agreed specification of exactly what a customer needs from a garment, which both protects the customer (a garment failing the spec is caught before delivery) and gives the tailor freedom to change their process as long as the spec is still met. Spring Cloud Contract automates checking the garment against that spec on the tailor's side (generated provider tests, run every time the tailor changes anything) *and* gives the customer a stand-in mannequin dressed exactly to spec to fit their other garments against, without needing to visit the tailor's shop at all (the generated consumer stub) — both sides verified against the identical specification document.

Concretely:

1. **A contract is written (Groovy DSL, or YAML) describing one specific interaction**: a request (method, URL, headers, body) and the response it should produce (status, headers, body) — often with pattern-matching for fields that can vary (a matcher for "any string" or "any number matching this regex," rather than requiring an exact literal match).
2. **On the provider side, the Spring Cloud Contract Verifier plugin generates a JUnit test class from each contract** at build time — this test sends the specified request to the provider's real implementation (via `MockMvc`/`WebTestClient`, or a genuinely running instance) and asserts the actual response matches the contract, failing the build if it doesn't.
3. **The same contracts are published as a stub artifact** (typically a JAR containing WireMock mapping files derived from the contracts) to an artifact repository — consumers depend on this stub artifact and use Spring Cloud Contract's WireMock integration to stand up a fake server that responds exactly per the contracts, without needing the real provider running.
4. **When the provider changes its contract** (intentionally, as part of an agreed API evolution) and republishes updated contracts and stubs, consumers pulling the latest stub artifact automatically test against the new expected behavior — and if the provider's actual implementation ever drifts from what a contract specifies without the contract itself being updated, the provider-side generated tests fail immediately in CI.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One contract generates provider-side verification tests against the real implementation, and a consumer-side WireMock stub artifact, keeping both sides verified against the same specification">
  <rect x="230" y="20" width="200" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Contract (Groovy/YAML)</text>

  <rect x="40" y="100" width="220" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Provider-side test</text>
  <text x="150" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">verifies REAL impl matches contract</text>

  <rect x="400" y="100" width="220" height="60" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="510" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Consumer-side WireMock stub</text>
  <text x="510" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">fake server, behaves EXACTLY per contract</text>

  <line x1="290" y1="60" x2="150" y2="100" stroke="#8b949e" marker-end="url(#a15)"/>
  <line x1="370" y1="60" x2="510" y2="100" stroke="#8b949e" marker-end="url(#a15)"/>
  <defs><marker id="a15" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

One contract generates both a provider verification test and a consumer-side stub, keeping both sides checked against the same specification.

## 5. Runnable example

Scenario: verifying an order-lookup endpoint's contract. We start with a plain Java model of the contract-verification idea, extend it to a stub-generation model for consumers, then show the real Spring Cloud Contract DSL and generated test shape.

### Level 1 — Basic

```java
// File: ContractVerificationConcept.java -- models the CORE idea: a
// contract describes an expected request/response; a generated test
// checks the REAL implementation against it.
import java.util.*;

public class ContractVerificationConcept {
    record Contract(String requestPath, String expectedResponseBody) {}

    // the REAL provider implementation, which the contract will be checked against
    static String realGetOrder(String path) {
        String orderId = path.substring(path.lastIndexOf('/') + 1);
        return "{\"orderId\":\"" + orderId + "\",\"status\":\"SUBMITTED\"}";
    }

    static boolean verifyContract(Contract contract) {
        String actualResponse = realGetOrder(contract.requestPath());
        boolean matches = actualResponse.equals(contract.expectedResponseBody());
        System.out.println("Contract for " + contract.requestPath() + " -- expected: " + contract.expectedResponseBody());
        System.out.println("                                actual:   " + actualResponse);
        return matches;
    }

    public static void main(String[] args) {
        Contract contract = new Contract("/orders/42", "{\"orderId\":\"42\",\"status\":\"SUBMITTED\"}");
        System.out.println("Contract satisfied? " + verifyContract(contract));
    }
}
```

How to run: `java ContractVerificationConcept.java`

`verifyContract` calls the *real* `realGetOrder` implementation and checks its actual output against what the contract says should be returned — exactly the core idea Spring Cloud Contract automates: generating this kind of check automatically from a written contract, run against the real provider code in CI, rather than someone manually writing and maintaining this comparison by hand.

### Level 2 — Intermediate

```java
// File: StubGenerationModel.java -- models generating a CONSUMER-SIDE
// STUB from the same contract, so consumers can test WITHOUT the real provider.
import java.util.*;

public class StubGenerationModel {
    record Contract(String requestPath, String responseBody) {}

    // a FAKE server, generated purely from the contract -- no real provider code involved at all
    static class GeneratedStub {
        Map<String, String> stubbedResponses = new HashMap<>();
        void loadFromContract(Contract contract) { stubbedResponses.put(contract.requestPath(), contract.responseBody()); }
        String handleRequest(String path) { return stubbedResponses.getOrDefault(path, "404 - no stub for this path"); }
    }

    // a CONSUMER, testing its own integration logic against the STUB, not the real provider
    static String consumerCallsOrderService(GeneratedStub stub, String orderId) {
        return stub.handleRequest("/orders/" + orderId);
    }

    public static void main(String[] args) {
        Contract contract = new Contract("/orders/42", "{\"orderId\":\"42\",\"status\":\"SUBMITTED\"}");
        GeneratedStub stub = new GeneratedStub();
        stub.loadFromContract(contract);

        System.out.println("Consumer's result (from STUB, no real provider running): " + consumerCallsOrderService(stub, "42"));
    }
}
```

How to run: `java StubGenerationModel.java`

`GeneratedStub` is populated purely from the contract's data, with no connection to the real provider implementation at all — `consumerCallsOrderService` tests exactly as it would against the real service, but entirely against this generated stand-in, modeling how Spring Cloud Contract's WireMock-based stub lets consumers test their integration code quickly and in isolation.

### Level 3 — Advanced

```java
// File: SpringCloudContractRealShape.java -- the REAL Spring Cloud
// Contract shape: a Groovy contract DSL definition, shown as an
// illustrative string, and the JUnit test/stub it GENERATES.
public class SpringCloudContractRealShape {

    static final String CONTRACT_GROOVY_DSL = """
        // File: src/test/resources/contracts/shouldReturnOrder.groovy
        Contract.make {
            request {
                method GET()
                url '/orders/42'
            }
            response {
                status OK()
                headers { contentType(applicationJson()) }
                body(
                    orderId: '42',
                    status: 'SUBMITTED'
                )
            }
        }
        """;

    // GENERATED PROVIDER-SIDE test (produced automatically by the
    // Spring Cloud Contract Verifier Maven/Gradle plugin at build time):
    static final String GENERATED_PROVIDER_TEST = """
        // File: (generated) OrderBaseTest -> ContractVerifierTest
        @Test
        public void validate_shouldReturnOrder() throws Exception {
            MockMvcRequestSpecification request = given();
            ResponseOptions response = given().spec(request)
                .get("/orders/42");

            assertThat(response.statusCode()).isEqualTo(200);
            assertThatJson(response.getBody().asString())
                .field("orderId").isEqualTo("42");
            assertThatJson(response.getBody().asString())
                .field("status").isEqualTo("SUBMITTED");
        }
        """;

    public static void main(String[] args) {
        System.out.println(CONTRACT_GROOVY_DSL);
        System.out.println(GENERATED_PROVIDER_TEST);
        System.out.println("The SAME contract also produces a WireMock stub JAR published for consumers to depend on.");
    }
}
```

How to run: `java SpringCloudContractRealShape.java` prints the illustrative contract and generated test; in a real Maven/Gradle build with the `spring-cloud-contract-maven-plugin` (or Gradle equivalent) configured and this `.groovy` contract file present under `src/test/resources/contracts/`, running `mvn test` actually generates and executes the shown JUnit test against your real `OrderController` implementation, and running `mvn install` additionally publishes a stub JAR consumers can depend on.

The `CONTRACT_GROOVY_DSL` is a real Spring Cloud Contract definition — `request { ... }`/`response { ... }` blocks describe exactly one HTTP interaction. The `GENERATED_PROVIDER_TEST` is what the Contract Verifier plugin actually produces from this contract at build time: a real JUnit test asserting the provider's actual running implementation (via a base test class you supply, wiring up `MockMvc` or a real server) returns exactly what the contract specifies — if `OrderController`'s real behavior ever diverges from this (say, someone changes the status field's default value), this generated test fails the build immediately.

## 6. Walkthrough

Trace what happens across a full Spring Cloud Contract workflow, from a contract change through to a consumer's build, end to end:

1. **The provider team writes (or modifies) a contract** under `src/test/resources/contracts/shouldReturnOrder.groovy`, as shown above, describing the expected request/response for `GET /orders/42`.
2. **The provider runs `mvn test` (or the Gradle equivalent).** The Spring Cloud Contract Verifier plugin scans the contracts directory, generates a JUnit test class from each contract file, and compiles it alongside the project's own test sources.
3. **The generated test executes against the provider's actual, real implementation** (via a base test class the provider supplies, typically setting up `MockMvc` against the real `OrderController`) — if `OrderController.getOrder("42")` returns anything other than exactly `{"orderId":"42","status":"SUBMITTED"}`, this generated test fails, immediately signaling in CI that the provider's real behavior has drifted from what the contract promises.
4. **Assuming the test passes, the provider runs `mvn install` (or a CI deploy step)**, which additionally packages the contracts into a stub JAR (containing WireMock mapping files derived from each contract) and publishes it to the team's artifact repository.
5. **A consumer team's build depends on this stub JAR** (via a test-scoped dependency) and uses Spring Cloud Contract's WireMock integration to start a stub server, configured automatically from the JAR's contents, that responds to `GET /orders/42` exactly as the contract specifies — without the consumer's build ever needing the real `order-service` running anywhere.
6. **The consumer's own integration tests run against this stub server**, verifying their client-side code (parsing the response, handling the status field correctly) behaves properly — and because the stub server is generated from the *same* contract the provider's tests verified in step 3, both sides are checked against one identical specification, rather than the consumer's assumptions and the provider's actual behavior potentially having quietly diverged.

## 7. Gotchas & takeaways

> **Gotcha:** a contract change that the provider makes and successfully verifies against their own implementation (step 3 passes) still requires the consumer to actually pull the *updated* stub JAR and re-run their own tests before they'll notice anything changed — if a consumer's build pins an old stub JAR version and never updates it, their tests will keep passing against outdated, stale expectations even after the provider's real API has genuinely changed, silently defeating the contract-testing safety net; keep stub JAR versions current, ideally as part of routine dependency updates, not an afterthought.

- Spring Cloud Contract generates real, executable tests from a written contract on the provider side, and a WireMock-based stub for consumers, both derived from the identical specification.
- Provider-side generated tests catch drift between the provider's actual implementation and what's contracted, failing loudly in CI rather than only being discovered when a consumer breaks later.
- Consumer-side stubs let integration tests run quickly and in isolation, without needing the real provider service running at all.
- The safety net only holds as long as consumers keep pulling updated stub JARs — a stale, pinned stub dependency silently defeats the purpose of contract testing.
