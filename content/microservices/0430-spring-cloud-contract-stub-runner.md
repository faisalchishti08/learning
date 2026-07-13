---
card: microservices
gi: 430
slug: spring-cloud-contract-stub-runner
title: "Spring Cloud Contract stub runner"
---

## 1. What it is

The **Spring Cloud Contract Stub Runner** is the consumer-side counterpart to [Spring Cloud Contract](0429-spring-cloud-contract-consumer-driven-contracts.md): a test dependency (`@AutoConfigureStubRunner`) that downloads the WireMock stub artifact a provider's build generated from its contracts, starts an in-process WireMock server pre-loaded with those stubs, and points your consumer's HTTP client at it — all automatically, from a single annotation specifying which provider and which version to pull. Instead of hand-writing a WireMock stub that hopes to match what the provider actually does, the consumer runs against a stub *generated directly from the provider's own verified contract*, so drift between "what we assume the provider does" and "what the provider's contract actually promises" becomes structurally impossible.

## 2. Why & when

You reach for the stub runner specifically to solve the problem plain [service virtualization](0419-service-virtualization-stubbing-dependencies.md) and hand-written [WireMock](0431-wiremock-for-http-stubbing.md) stubs can't solve on their own: keeping a consumer's local stub honest as the real provider evolves:

- **A hand-written WireMock stub is only as accurate as whoever wrote it, on the day they wrote it.** If the provider changes its API and nobody updates the consumer's hand-maintained stub, the consumer's tests keep passing against a shape production no longer returns.
- **The stub runner's stub is generated from the provider's own contract, not guessed by the consumer team.** Every time the provider's contract changes and a new stub version is published, the consumer can pull the updated stub and immediately find out — via a failing local test — that their integration assumptions are now stale.
- **It requires no real provider running anywhere.** The consumer's build pulls a versioned stub artifact from the shared artifact repository (or a local Maven repository during development) and runs entirely offline against it, keeping tests fast and independent, exactly the benefit [service virtualization](0419-service-virtualization-stubbing-dependencies.md) is built around generally.
- **Version pinning makes compatibility explicit.** Specifying `provider:1.4.0` in `@AutoConfigureStubRunner` states, in code, exactly which provider version this consumer's tests currently assume — bumping that version number is a visible, reviewable act of taking on a new provider contract.

You reach for the stub runner whenever your consumer depends on a provider that publishes Spring Cloud Contract stubs, as the default way to test against that dependency locally and in CI, reserving a small number of real end-to-end tests for final cross-service confirmation.

## 3. Core concept

Picture ordering a specific, certified replacement part for a car repair, rather than fabricating a part yourself based on a photo of the original. The stub runner is the parts catalog: you specify exactly which part (which provider, which version) you need, it's delivered pre-certified to match the real manufacturer's specification (the contract), and you install and test against it without ever needing the original factory (the real running provider) on-site. If the manufacturer issues a new part revision, ordering the old part number still gets you the old, known-compatible part — you only get the new behavior when you deliberately order the new part number.

Concretely, using the stub runner has three parts:

1. **`@AutoConfigureStubRunner`** on a Spring Boot test class, specifying `ids = "com.example:product-catalog-provider:+:stubs:8090"` — group:artifact:version:classifier:port, where `+` means "latest available" and a fixed version number pins to an exact contract.
2. **Automatic resolution and startup** — the stub runner resolves that artifact (from a local Maven repository, or a remote one configured for CI), extracts the stub definitions bundled inside it, and starts a real, in-process WireMock server loaded with them on the specified port.
3. **The consumer's real HTTP client** is configured (directly, or via [service discovery](0419-service-virtualization-stubbing-dependencies.md)-aware configuration in the test) to call `localhost:8090` instead of the real provider, and the test proceeds exactly as if it were an ordinary [WireMock](0431-wiremock-for-http-stubbing.md)-backed test — except every stubbed interaction is guaranteed to match what the provider's own contract-verification build actually checked.

```java
@SpringBootTest
@AutoConfigureStubRunner(
    ids = "com.example:product-catalog-provider:+:stubs:8090",
    stubsMode = StubRunnerProperties.StubsMode.LOCAL
)
class ProductClientContractTest {
    @Autowired ProductClient productClient;

    @Test
    void fetchesProductFromProviderStub() {
        Product product = productClient.fetch("42");
        assertThat(product.name()).isEqualTo("Wireless Mouse");
    }
}
```

`stubsMode = LOCAL` tells the runner to resolve the stub artifact from the local Maven repository (useful while developing against a provider still in progress); `REMOTE` or `CLASSPATH` are the other common modes for CI and self-contained builds respectively.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The provider's build publishes a versioned stub artifact to an artifact repository; the consumer's test uses AutoConfigureStubRunner to download that exact artifact, start an in-process WireMock server loaded with its stubs, and point the consumer's real HTTP client at it">
  <rect x="20" y="30" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="95" y="52" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Provider build</text>
  <text x="95" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">generates stub JAR</text>

  <line x1="170" y1="60" x2="240" y2="60" stroke="#6db33f" stroke-width="2"/>

  <rect x="240" y="30" width="170" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="325" y="52" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Artifact repository</text>
  <text x="325" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">product-catalog-provider:1.4.0:stubs</text>

  <line x1="410" y1="60" x2="470" y2="60" stroke="#79c0ff" stroke-width="2"/>
  <text x="440" y="45" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">pull</text>

  <rect x="470" y="30" width="150" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="545" y="52" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@AutoConfigureStubRunner</text>
  <text x="545" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">starts in-process WireMock</text>

  <line x1="545" y1="90" x2="545" y2="140" stroke="#f0883e" stroke-width="2" stroke-dasharray="3,2"/>

  <rect x="450" y="140" width="190" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="545" y="165" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">local WireMock stub</text>
  <text x="545" y="182" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">matches provider's real contract</text>

  <line x1="450" y1="170" x2="290" y2="170" stroke="#6db33f" stroke-width="2"/>

  <rect x="90" y="140" width="200" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="190" y="165" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Consumer's real HTTP client</text>
  <text x="190" y="182" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">calls localhost:8090</text>

  <text x="320" y="225" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">the stub is generated FROM the provider's contract, not guessed by the consumer</text>
</svg>

The stub runner downloads a versioned stub artifact the provider's own build generated, starts it locally, and points the consumer's real client at it — no guessed mocks involved.

## 5. Runnable example

Scenario: a `ProductClient` consumer that depends on `ProductCatalogProvider`'s stub. We model the essential version-pinning and stub-serving behavior in plain Java first, then show the real `@AutoConfigureStubRunner` shape, then handle a production-flavored case: a consumer test catching the moment a stub version bump introduces a breaking shape change.

### Level 1 — Basic

```java
// File: StubArtifactResolutionBasic.java -- models the CORE idea: a stub
// is fetched by an EXACT version, and the consumer's client is pointed at
// whatever that resolved stub returns -- before real Maven/WireMock tooling.
import java.util.*;

public class StubArtifactResolutionBasic {
    // Simulates a repository of published stub artifacts, keyed by version.
    static final Map<String, Map<String, Object>> STUB_REPOSITORY = Map.of(
            "1.4.0", Map.of("name", "Wireless Mouse", "price", 24.99)
    );

    static Map<String, Object> resolveStub(String providerArtifact, String version) {
        Map<String, Object> stub = STUB_REPOSITORY.get(version);
        if (stub == null) throw new NoSuchElementException("no stub artifact for " + providerArtifact + ":" + version);
        System.out.println("Resolved stub for " + providerArtifact + ":" + version + " -> " + stub);
        return stub;
    }

    // The consumer's real client, pointed at whatever the resolved stub returns.
    static String fetchProductName(Map<String, Object> stubResponse) {
        return (String) stubResponse.get("name");
    }

    public static void main(String[] args) {
        Map<String, Object> stub = resolveStub("com.example:product-catalog-provider", "1.4.0");
        System.out.println("Consumer fetched product name: " + fetchProductName(stub));
    }
}
```

How to run: `java StubArtifactResolutionBasic.java`

`resolveStub` mirrors the core act `@AutoConfigureStubRunner` performs for real: given an exact group:artifact:version, fetch the matching stub content. `fetchProductName` represents the consumer's real client code, which never knows or cares that it's talking to a resolved stub instead of a real provider — that transparency is the whole point of the stub runner.

### Level 2 — Intermediate

```java
// File: StubRunnerRealShapeIntermediate.java -- the SAME resolve-and-serve
// idea, now in its REAL Spring Cloud Contract form using
// @AutoConfigureStubRunner, as it would really be written and run under
// Maven/Gradle with spring-cloud-starter-contract-stub-runner on the
// classpath (and the provider's stub artifact available, locally or
// remotely).
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.cloud.contract.stubrunner.spring.AutoConfigureStubRunner;
import org.springframework.cloud.contract.stubrunner.StubRunnerProperties;
import org.springframework.web.client.RestClient;

import static org.assertj.core.api.Assertions.assertThat;

public class StubRunnerRealShapeIntermediate {

    // The consumer's real client code -- exactly what runs in production,
    // pointed at whatever base URL it's configured with.
    static class ProductClient {
        private final RestClient restClient;
        ProductClient(String baseUrl) { this.restClient = RestClient.create(baseUrl); }

        record ProductResponse(String name, double price) {}

        ProductResponse fetch(String id) {
            return restClient.get().uri("/products/{id}", id).retrieve().body(ProductResponse.class);
        }
    }

    @SpringBootTest
    @AutoConfigureStubRunner(
            ids = "com.example:product-catalog-provider:+:stubs:8090",
            stubsMode = StubRunnerProperties.StubsMode.LOCAL
    )
    static class ProductClientContractTest {

        @Test
        void fetchesProductFromProviderStub() {
            // The stub runner has already started a WireMock server on :8090,
            // pre-loaded with stubs generated from the provider's real contract.
            ProductClient client = new ProductClient("http://localhost:8090");
            ProductClient.ProductResponse product = client.fetch("42");

            assertThat(product.name()).isEqualTo("Wireless Mouse");
            assertThat(product.price()).isEqualTo(24.99);
        }
    }
}
```

How to run: requires `spring-cloud-starter-contract-stub-runner` on the classpath, the provider's `product-catalog-provider` stub artifact installed in the local Maven repository (via `mvn install` on the provider project, or resolvable remotely), and JUnit 5; run as a test via `mvn test` or your IDE's test runner.

`@AutoConfigureStubRunner`'s `ids` attribute names the exact artifact coordinates (`+` for "latest," or a pinned version like `1.4.0`), and `stubsMode = LOCAL` tells it to resolve from the local Maven repository — useful while iterating locally against a provider still in development. The stub runner starts a real WireMock server on port `8090` before the test runs, and `ProductClient` — genuinely the same client class used in production — calls it exactly as it would call the real provider.

### Level 3 — Advanced

```java
// File: StubVersionBumpBreaksAdvanced.java -- the SAME consumer, now
// handling a PRODUCTION-FLAVORED hard case: bumping the pinned stub version
// to a new provider release that changed its response shape -- the failure
// this test SHOULD surface, proving the value of pinning explicit versions
// rather than always tracking "+" (latest).
import java.util.*;

public class StubVersionBumpBreaksAdvanced {
    // Simulates TWO published stub versions -- 1.4.0 (what the consumer currently
    // pins to) and 2.0.0 (a new provider release with a restructured response).
    static final Map<String, Map<String, Object>> STUB_REPOSITORY = new LinkedHashMap<>();
    static {
        STUB_REPOSITORY.put("1.4.0", Map.of("name", "Wireless Mouse", "price", 24.99));
        STUB_REPOSITORY.put("2.0.0", Map.of("name", "Wireless Mouse", "pricing", Map.of("amount", 24.99, "currency", "USD")));
    }

    static Map<String, Object> resolveStub(String version) {
        Map<String, Object> stub = STUB_REPOSITORY.get(version);
        if (stub == null) throw new NoSuchElementException("no stub for version " + version);
        return stub;
    }

    // The CONSUMER's real client code, written against the OLD (1.4.0) shape --
    // it has not been updated for the new "pricing" structure yet.
    static double extractPrice(Map<String, Object> productResponse) {
        Object price = productResponse.get("price");
        if (price == null) {
            throw new IllegalStateException(
                    "expected top-level 'price' field but it was missing -- provider shape may have changed");
        }
        return (double) price;
    }

    static void runConsumerTestAgainstPinnedVersion(String pinnedVersion) {
        System.out.println("--- Running consumer test pinned to stub version " + pinnedVersion + " ---");
        Map<String, Object> stub = resolveStub(pinnedVersion);
        try {
            double price = extractPrice(stub);
            System.out.println("Consumer test PASSED, extracted price=" + price);
        } catch (IllegalStateException e) {
            System.out.println("Consumer test FAILED: " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        // Consumer currently pins 1.4.0 -- passes, matching what production actually calls.
        runConsumerTestAgainstPinnedVersion("1.4.0");

        // A developer experimentally bumps the pin to 2.0.0 to see what breaks
        // BEFORE actually deploying against the new provider version.
        runConsumerTestAgainstPinnedVersion("2.0.0");
    }
}
```

How to run: `java StubVersionBumpBreaksAdvanced.java`

Bumping the pinned version from `1.4.0` to `2.0.0` is a single, explicit, reviewable change — exactly like changing any other dependency version — and it immediately surfaces that the consumer's `extractPrice` logic doesn't understand the new `pricing` object shape. This is the version-pinning payoff: the consumer team controls exactly when they take on a new provider contract, and bumping the pin becomes a deliberate act of integration testing rather than something that silently happens because a shared "latest" stub moved underneath them.

## 6. Walkthrough

Trace `StubVersionBumpBreaksAdvanced.main` in order. **First**, `runConsumerTestAgainstPinnedVersion("1.4.0")` runs. `resolveStub("1.4.0")` returns the map with a top-level `price` key. `extractPrice` finds `productResponse.get("price")` is non-null (`24.99`), so it returns that value directly, and the test prints **PASSED**.

**Next**, `runConsumerTestAgainstPinnedVersion("2.0.0")` runs. `resolveStub("2.0.0")` returns the *new* map shape, where pricing information now lives under a nested `pricing` key instead of a top-level `price` key. `extractPrice` calls `productResponse.get("price")`, which returns `null` because that top-level key no longer exists in this version's stub.

**Then**, the `null` check inside `extractPrice` fires, throwing an `IllegalStateException` with a message explaining exactly what went wrong: the expected top-level field is missing. **Finally**, the `catch` block in `runConsumerTestAgainstPinnedVersion` catches that exception and prints **FAILED** with the specific reason — giving the consumer team a precise, actionable signal about exactly what changed, before they've deployed anything against the real, new provider version in production.

```
--- Running consumer test pinned to stub version 1.4.0 ---
Consumer test PASSED, extracted price=24.99
--- Running consumer test pinned to stub version 2.0.0 ---
Consumer test FAILED: expected top-level 'price' field but it was missing -- provider shape may have changed
```

## 7. Gotchas & takeaways

> Using `+` (latest) instead of a pinned version number in `@AutoConfigureStubRunner` feels convenient during active development, but in a stable CI pipeline it means the exact same test code can start failing on an unrelated day purely because the provider published a new stub — with no code change on the consumer's side to point to. Pin an explicit version in any test that runs in CI, and treat bumping that version as a deliberate, reviewed integration step, exactly like bumping any other dependency.

- The stub runner's core value is that the consumer's local stub is generated *from* the provider's real, verified contract — never hand-guessed, so it can't independently drift from what the provider actually promises.
- `stubsMode` (`LOCAL`, `REMOTE`, `CLASSPATH`) controls where the stub artifact is resolved from — `LOCAL` is convenient during coordinated local development against an in-progress provider, `REMOTE` is typical for CI pulling from a shared artifact repository.
- Pair the stub runner with [Spring Cloud Contract](0429-spring-cloud-contract-consumer-driven-contracts.md) on the provider side — the stub the runner downloads only exists because the provider's build generated it from a contract file.
- Bumping the pinned stub version is a visible, reviewable act of taking on a new provider release — treat a failing test after a version bump exactly like a genuine, valuable finding, not an annoyance to work around.
- The stub runner replaces hand-written [WireMock](0431-wiremock-for-http-stubbing.md) stubs specifically for dependencies whose provider team publishes Spring Cloud Contract stubs; for dependencies without that (third-party APIs, legacy systems), hand-written WireMock stubs remain the right tool.
