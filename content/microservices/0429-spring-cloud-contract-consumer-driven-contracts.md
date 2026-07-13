---
card: microservices
gi: 429
slug: spring-cloud-contract-consumer-driven-contracts
title: "Spring Cloud Contract (consumer-driven contracts)"
---

## 1. What it is

**Spring Cloud Contract** is a framework that implements [consumer-driven contract testing](0415-contract-testing-consumer-driven-contracts.md) inside the Spring ecosystem, with a distinctive design choice: contracts are written as plain **Groovy or YAML DSL files** checked into the *provider's* codebase, rather than recorded automatically from consumer test runs (the Pact approach). From each contract file, Spring Cloud Contract's build plugin generates two things at build time: a real JUnit test that runs against the provider's actual controller, verifying the provider satisfies the contract, and a **WireMock stub** that consumers can pull down and run against locally, so their own tests can exercise a realistic fake of the provider without either service needing to be deployed anywhere.

## 2. Why & when

You reach for Spring Cloud Contract specifically when your team wants consumer-driven contract testing but prefers contracts to live as reviewable, version-controlled specification files in the provider's own repository, generated automatically into both a verification test and a distributable stub:

- **The contract lives with the provider team, reviewable in code review.** Since the contract is a DSL file in the provider's repository, changing the provider's API and updating its contract happen in the same pull request, making incompatible changes visible to reviewers before they ever merge.
- **Verification is generated, not hand-written.** The Maven/Gradle plugin turns each contract into a real JUnit test automatically — no test-writing effort duplicated between "what the contract says" and "what the test checks."
- **The generated WireMock stub is the same artifact consumers actually run against.** There's no risk of a hand-maintained mock drifting from the real contract, because the stub *is* generated directly from it — see [Spring Cloud Contract stub runner](0430-spring-cloud-contract-stub-runner.md) for how consumers pull and use it.
- **It fits naturally into a Maven/Gradle-centric Spring shop**, generating artifacts (a stub JAR) that publish to the same artifact repository (Nexus, Artifactory) already used for application JARs, rather than requiring a separate broker service — though a [contract test broker](0423-contract-test-broker-pact-broker.md)-style tool can still be layered on top for discovery and `can-i-deploy`-style checks.

You reach for Spring Cloud Contract over a recording-based tool like Pact specifically when your organization is Spring/Maven-centric and prefers contracts as explicit, provider-owned specification files rather than artifacts automatically captured from consumer test runs.

## 3. Core concept

Picture an architect's blueprint that two different subcontractors both build from. The plumber (provider) builds the actual pipes according to the blueprint, and a separate inspection automatically checks the real pipes against it. The blueprint is *also* handed to the general contractor (consumer) as a life-sized mockup they can practice fitting cabinets around, without needing the real plumbing installed yet. One blueprint, two uses: real verification for the side that builds the thing, and a faithful practice replica for the side that depends on it.

Concretely, the Spring Cloud Contract workflow has four steps:

1. **Write the contract** as a Groovy or YAML DSL file in the provider's repository, under `src/test/resources/contracts/`, describing one request/response interaction: `request { method GET(); url '/products/42' }` paired with `response { status 200; body(name: 'Wireless Mouse', price: 24.99) }`.
2. **Generate a verification test** — the `spring-cloud-contract-maven-plugin` (or Gradle equivalent) processes every contract file at build time and generates a JUnit test class that sends exactly that request to the provider's real controller and asserts the real response matches.
3. **Generate a stub JAR** — the same build step also packages a WireMock-compatible stub definition matching the contract, published as a separate artifact (often with an `-stubs` classifier) to the team's artifact repository.
4. **Consumers pull the stub**, using the [stub runner](0430-spring-cloud-contract-stub-runner.md), to run their own tests against a realistic fake of the provider without the provider needing to be deployed anywhere.

```groovy
// src/test/resources/contracts/shouldReturnProductById.groovy
Contract.make {
    description "returns product 42 with name and price"
    request {
        method GET()
        url '/products/42'
    }
    response {
        status 200
        headers { contentType(applicationJson()) }
        body(name: 'Wireless Mouse', price: 24.99)
    }
}
```

This one file becomes both a generated JUnit test in the provider's build (proving the real controller returns exactly this shape) and a generated WireMock stub any consumer can run against.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A contract DSL file lives in the provider's repository; the build plugin generates a JUnit verification test that runs against the real provider controller, and a WireMock stub JAR that gets published for consumers to pull and run against">
  <rect x="30" y="100" width="140" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="100" y="125" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Contract DSL</text>
  <text x="100" y="142" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(Groovy/YAML, provider repo)</text>

  <line x1="170" y1="130" x2="230" y2="70" stroke="#79c0ff" stroke-width="2"/>
  <line x1="170" y1="130" x2="230" y2="190" stroke="#f0883e" stroke-width="2"/>
  <text x="195" y="90" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">build plugin</text>

  <rect x="230" y="40" width="170" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="315" y="65" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">generated JUnit test</text>
  <text x="315" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">runs against REAL controller</text>

  <rect x="230" y="160" width="170" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="315" y="185" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">generated WireMock stub</text>
  <text x="315" y="202" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">packaged as -stubs artifact</text>

  <line x1="400" y1="190" x2="470" y2="190" stroke="#f0883e" stroke-width="2"/>

  <rect x="470" y="160" width="140" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="540" y="185" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Consumer's tests</text>
  <text x="540" y="202" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">pull stub via stub runner</text>

  <text x="320" y="240" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">one contract file drives both real-provider verification and a distributable consumer stub</text>
</svg>

One contract DSL file, checked into the provider's repository, generates both the provider's own verification test and the stub consumers pull to test against.

## 5. Runnable example

Scenario: a `ProductCatalogProvider` with a contract describing its `/products/{id}` endpoint. We model the essential generated-test-and-stub relationship in plain Java first, then show the real contract DSL and its generated test shape, then handle a production-flavored case where a contract catches a provider regression before it ships.

### Level 1 — Basic

```java
// File: ContractDrivenVerificationBasic.java -- models the CORE idea a
// contract DSL file drives: one specification producing BOTH a verification
// check against real logic AND a reusable scripted stub, before any real
// Spring Cloud Contract tooling is involved.
import java.util.*;

public class ContractDrivenVerificationBasic {
    // Represents the contract file's content: one request/response pair.
    record ContractSpec(String path, Map<String, Object> expectedBody) {}

    // The REAL provider logic being verified (stands in for a real @RestController).
    static Map<String, Object> realProviderHandler(String path) {
        if (path.equals("/products/42")) {
            return Map.of("name", "Wireless Mouse", "price", 24.99);
        }
        throw new NoSuchElementException("no such product");
    }

    // The GENERATED verification test: run the real handler, compare to the contract.
    static boolean verifyContract(ContractSpec spec) {
        Map<String, Object> actual = realProviderHandler(spec.path());
        boolean matches = actual.equals(spec.expectedBody());
        System.out.println("Verifying contract for " + spec.path() + " -> " + (matches ? "PASS" : "FAIL"));
        return matches;
    }

    public static void main(String[] args) {
        ContractSpec contract = new ContractSpec("/products/42", Map.of("name", "Wireless Mouse", "price", 24.99));
        verifyContract(contract);
    }
}
```

How to run: `java ContractDrivenVerificationBasic.java`

`verifyContract` mirrors what the generated JUnit test does for real: it exercises `realProviderHandler` — the actual provider logic — and compares the actual output against exactly what the contract specifies. This is the essential shape Spring Cloud Contract automates: no hand-written test asserting the same thing separately, just a generated check derived directly from the contract file.

### Level 2 — Intermediate

```java
// File: SpringCloudContractRealShapeIntermediate.java -- the SAME kind of
// verification, now shown as it would REALLY be generated by the
// spring-cloud-contract-maven-plugin: a base test class the plugin extends
// with generated test methods, and the real controller under test.
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class SpringCloudContractRealShapeIntermediate {

    @RestController
    static class ProductController {
        @GetMapping("/products/{id}")
        Map<String, Object> getProduct(@PathVariable String id) {
            if (!id.equals("42")) throw new java.util.NoSuchElementException("no such product: " + id);
            return Map.of("name", "Wireless Mouse", "price", 24.99);
        }
    }

    // A hand-written stand-in for what spring-cloud-contract-maven-plugin
    // GENERATES automatically from contracts/shouldReturnProductById.groovy --
    // real Spring Cloud Contract projects never hand-write this class.
    static abstract class ContractVerifierBase {
        MockMvc mockMvc;
        void setup() { mockMvc = MockMvcBuilders.standaloneSetup(new ProductController()).build(); }
    }

    static class ContractVerifierTest extends ContractVerifierBase {
        @Test
        void validate_shouldReturnProductById() throws Exception {
            setup();
            mockMvc.perform(get("/products/42"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.name").value("Wireless Mouse"))
                    .andExpect(jsonPath("$.price").value(24.99));
        }
    }
}
```

How to run: requires `spring-boot-starter-test` and `spring-boot-starter-web` on the classpath; run as a JUnit 5 test via `mvn test` or your IDE's test runner. In a real project, `ContractVerifierTest`'s method would be entirely generated by the `spring-cloud-contract-maven-plugin` from a `.groovy`/`.yml` contract file at build time — it's shown here written by hand only to make the generated shape concrete.

The important structural detail is `validate_shouldReturnProductById` — its name is derived directly from the contract's `description`, and its body is generated automatically to send exactly the request the contract specifies and assert exactly the response the contract specifies, using real `MockMvc` against the real `ProductController`, exactly matching the pattern from [MockMvc / WebTestClient](0427-mockmvc-webtestclient.md).

### Level 3 — Advanced

```java
// File: ContractCatchesRegressionAdvanced.java -- the SAME contract idea,
// now handling a PRODUCTION-FLAVORED hard case: a provider refactor that
// silently breaks the contract, caught by the GENERATED verification test
// before the provider ever ships -- exactly the failure mode Spring Cloud
// Contract exists to catch at build time.
import java.util.*;

public class ContractCatchesRegressionAdvanced {
    record ContractSpec(String description, String path, Map<String, Object> expectedBody) {}

    // Version 1: matches the contract exactly (the version the contract was written against).
    static Map<String, Object> providerV1(String path) {
        if (!path.equals("/products/42")) throw new NoSuchElementException();
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("name", "Wireless Mouse");
        body.put("price", 24.99);
        return body;
    }

    // Version 2: a refactor changes "price" to a nested "pricing.amount" object --
    // looks like a reasonable API evolution, but breaks the existing contract.
    static Map<String, Object> providerV2(String path) {
        if (!path.equals("/products/42")) throw new NoSuchElementException();
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("name", "Wireless Mouse");
        body.put("pricing", Map.of("amount", 24.99, "currency", "USD"));
        return body;
    }

    static boolean verify(ContractSpec spec, java.util.function.Function<String, Map<String, Object>> handler) {
        Map<String, Object> actual = handler.apply(spec.path());
        List<String> mismatches = new ArrayList<>();
        for (Map.Entry<String, Object> expected : spec.expectedBody().entrySet()) {
            Object actualValue = actual.get(expected.getKey());
            if (!Objects.equals(expected.getValue(), actualValue)) {
                mismatches.add(expected.getKey() + ": expected=" + expected.getValue() + " actual=" + actualValue);
            }
        }
        if (!mismatches.isEmpty()) {
            System.out.println("CONTRACT '" + spec.description() + "' FAILED: " + mismatches);
            return false;
        }
        System.out.println("CONTRACT '" + spec.description() + "' PASSED");
        return true;
    }

    public static void main(String[] args) {
        ContractSpec contract = new ContractSpec(
                "returns product 42 with name and price",
                "/products/42",
                Map.of("name", "Wireless Mouse", "price", 24.99));

        System.out.println("--- Building against provider V1 ---");
        boolean v1Ok = verify(contract, ContractCatchesRegressionAdvanced::providerV1);

        System.out.println("--- Building against provider V2 (after refactor) ---");
        boolean v2Ok = verify(contract, ContractCatchesRegressionAdvanced::providerV2);
        System.out.println("V2 build would FAIL with v2Ok=" + v2Ok + " -- the generated test blocks the merge/release.");
    }
}
```

How to run: `java ContractCatchesRegressionAdvanced.java`

`providerV2` represents a refactor that nests pricing information — a change that might genuinely be a good API design decision in isolation — but the contract still expects a flat `price` field. Because the generated verification test runs on *every build*, this mismatch is caught immediately as a failing test in the provider's own CI pipeline, exactly like the outcome in [contract testing](0415-contract-testing-consumer-driven-contracts.md), but here the check itself was never hand-written — it was generated automatically from the same contract file that also produced the consumer-facing stub.

## 6. Walkthrough

Trace `ContractCatchesRegressionAdvanced.main` in order. **First**, `verify(contract, providerV1)` runs. `providerV1("/products/42")` returns a map with `name="Wireless Mouse"` and `price=24.99`. The loop over `contract.expectedBody()`'s two entries finds both fields present with matching values, so `mismatches` stays empty and the function prints **PASSED**, returning `true`.

**Next**, `verify(contract, providerV2)` runs. `providerV2("/products/42")` returns a map with `name="Wireless Mouse"` and `pricing={amount=24.99, currency=USD}` — there is no top-level `price` key at all anymore. **Then**, the loop checks `name` (matches) and `price`: `actual.get("price")` returns `null`, since the key was restructured into a nested object under a different name. `Objects.equals(24.99, null)` is `false`, so this mismatch is recorded, `mismatches` becomes non-empty, and the function prints **FAILED** with the specific field and values involved, returning `false`.

**Finally**, `main` prints that the V2 build would fail. In a real Spring Cloud Contract project, this exact failure happens automatically as part of `mvn test` (or `./gradlew test`) whenever the provider's contract-verification build runs — no developer needs to remember to write or update a corresponding test, because the generated test is regenerated from the same contract file every build, and it fails the moment the real controller's behavior diverges from what's specified.

```
--- Building against provider V1 ---
CONTRACT 'returns product 42 with name and price' PASSED
--- Building against provider V2 (after refactor) ---
CONTRACT 'returns product 42 with name and price' FAILED: [price: expected=24.99 actual=null]
V2 build would FAIL with v2Ok=false -- the generated test blocks the merge/release.
```

## 7. Gotchas & takeaways

> Because contracts live in the *provider's* repository rather than being recorded from real consumer test runs, it's possible for a contract to drift from what a consumer actually needs — someone updates the provider's contract file to match a new API shape without confirming a real consumer still works against it. Spring Cloud Contract verifies the provider satisfies its own stated contracts; it does not, by itself, guarantee those contracts still reflect real consumer usage the way Pact's recording-based approach more directly does. Treat contract files as a genuine cross-team artifact, reviewed with consumer teams, not just an internal provider-team specification.

- Spring Cloud Contract generates both a real JUnit verification test and a WireMock stub from one contract DSL file, keeping the provider-side test and the consumer-facing stub permanently in sync by construction.
- Because contracts are DSL files in the provider's repository, changes to the API and to the contract happen together, visible in the same code review — a structural difference from recording-based tools.
- Pair Spring Cloud Contract with the [stub runner](0430-spring-cloud-contract-stub-runner.md) on the consumer side to actually pull and run against the generated stub artifact.
- A [contract test broker](0423-contract-test-broker-pact-broker.md) can still sit alongside Spring Cloud Contract for discovery and deploy-safety checks, even though contracts themselves live in the provider's repository rather than being published to the broker directly.
- The generated verification test runs on every build, giving the same "catch the break before deployment" guarantee described in [contract testing](0415-contract-testing-consumer-driven-contracts.md), without any hand-written test duplicating what the contract already specifies.
