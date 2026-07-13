---
card: microservices
gi: 415
slug: contract-testing-consumer-driven-contracts
title: "Contract testing (consumer-driven contracts)"
---

## 1. What it is

**Contract testing** verifies that two services agree on the shape of the API between them — the requests one sends and the responses the other returns — without either service needing to run the other for real. In the **consumer-driven** flavor, the *consumer* of an API (the service making the call) writes down exactly what it expects from the *provider* (the service being called) as a machine-readable **contract**: specific requests it will send and the specific response shapes it needs back. That contract is then replayed against the real provider in the provider's own test suite, so the provider finds out immediately if a change would break a real consumer — before either side ever deploys.

## 2. Why & when

You reach for contract testing to close a gap that neither [component testing](0414-component-testing-single-service-in-isolation.md) nor [end-to-end testing](0417-end-to-end-testing-its-fragility.md) fills well. A component test stubs the provider based on the *consumer team's assumptions* about what the provider returns — if those assumptions are wrong, or the provider changes without telling anyone, the stub silently drifts out of sync with reality and the component test keeps passing while production breaks. An end-to-end test would catch that drift, but only by running every service together, slowly and fragilely, for every single check.

- **It catches breaking changes at the source, before deployment.** If a provider team removes a field a consumer depends on, running the consumer's contract against the provider's own test suite fails immediately, in the provider's own CI pipeline — not three days later when the consumer's production traffic starts erroring.
- **It replaces a whole class of end-to-end tests.** Instead of running consumer and provider together to check they're compatible, you check compatibility statically and fast — which is exactly what the [test pyramid](0411-test-pyramid-for-microservices.md) wants: push what you can out of the slow, expensive top layer.
- **It documents the real, exercised contract, not an aspirational one.** An OpenAPI spec describes what a provider *could* return; a consumer-driven contract describes exactly what a real consumer *actually* depends on, which is often a meaningful subset — and catching a break only in the fields consumers truly use avoids false alarms over unused parts of the API.
- **It scales independently of team count.** As more consumers depend on a provider, each consumer contributes its own contract; the provider verifies against all of them without needing to spin up every consumer service.

You adopt contract testing specifically at team boundaries — wherever one team's service calls another team's service — and it becomes more valuable, not less, as the number of services and teams grows, because that's exactly when informal "just talk to the other team" coordination stops scaling.

## 3. Core concept

Picture a contract like a furniture delivery order form. The customer (consumer) doesn't design the whole factory's catalog — they fill out a specific order: "I need a table that is 120cm long, brown, with four legs." The factory (provider) doesn't need to guess what the customer wants; it just needs to keep satisfying every order form it has been given. If the factory changes how it makes tables, it re-checks every outstanding order form first — and if a change would leave any order unfulfillable, that's caught before the table ships, not after the customer unpacks it and finds it doesn't fit.

The consumer-driven contract-testing workflow has four steps:

1. **The consumer writes a contract** describing specific interactions it depends on: "when I `POST /orders` with this shape, I expect back a `201` with a body containing an `orderId` field." This is usually done by running the consumer's own tests against a mock provider (a tool like Pact records the interactions automatically) rather than hand-writing the contract file.
2. **The contract is published** to a shared location — a **contract broker** (see [provider vs consumer contracts](0416-provider-vs-consumer-contracts.md) for the provider side of this workflow, and the dedicated contract-broker topic for the shared-storage piece) — where both teams can find it.
3. **The provider verifies the contract** by replaying every recorded interaction against its own *real*, running code (typically in the provider's own CI pipeline) and checking that the real responses match what each contract expects.
4. **A failed verification blocks the provider's deployment**, or at minimum raises a loud, immediate signal — turning "we broke a consumer" from a production incident into a failed CI build.

The key property that makes this fast and reliable, compared to an end-to-end test, is that verification never requires the consumer and provider to run *simultaneously*: the consumer records its expectations once, and the provider replays them independently, on its own schedule, against its own code.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A consumer writes a contract describing the interactions it depends on and publishes it to a broker; the provider later pulls that contract and verifies its real code satisfies every recorded interaction, without the two services ever running together">
  <rect x="30" y="30" width="150" height="60" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="105" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Consumer</text>
  <text x="105" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">records expectations</text>

  <line x1="180" y1="60" x2="250" y2="60" stroke="#79c0ff" stroke-width="2"/>
  <text x="215" y="50" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">1. publish</text>

  <rect x="250" y="90" width="140" height="60" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Contract broker</text>
  <text x="320" y="132" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">stores contracts</text>

  <line x1="320" y1="90" x2="320" y2="60" stroke="#8b949e" stroke-dasharray="3,2"/>

  <line x1="390" y1="120" x2="460" y2="90" stroke="#f0883e" stroke-width="2"/>
  <text x="440" y="105" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">2. pull</text>

  <rect x="460" y="30" width="150" height="60" rx="10" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="535" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Provider</text>
  <text x="535" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">verifies real code against it</text>

  <text x="320" y="200" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">consumer and provider never need to run at the same time</text>
  <text x="320" y="218" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">the broker is the asynchronous handoff between them</text>
</svg>

The consumer publishes what it depends on; the provider independently verifies its real implementation still satisfies it, with the broker as the asynchronous handoff.

## 5. Runnable example

Scenario: an `OrderSummaryConsumer` that depends on a specific shape from a `ProductCatalogProvider`'s `/products/{id}` endpoint. We first record a contract from the consumer's expectations, then replay it against a real (in-process, simulated) provider implementation, then show what happens when the provider changes in a way that breaks the contract.

### Level 1 — Basic

```java
// File: ContractRecordingBasic.java -- the CONSUMER side: record a contract
// describing exactly what this consumer expects from the provider, based on
// how the consumer's own code actually uses the response.
import java.util.*;

public class ContractRecordingBasic {
    // A CONTRACT: one specific interaction the consumer depends on.
    record Contract(String description, String request, Map<String, String> expectedResponseFields) {}

    // The consumer's own code, showing WHICH fields it actually reads --
    // this is what a real contract-recording tool observes automatically.
    static String describeProduct(Map<String, String> productResponse) {
        return productResponse.get("name") + " ($" + productResponse.get("price") + ")";
    }

    public static void main(String[] args) {
        // The consumer only reads "name" and "price" -- so the contract only
        // needs to promise those two fields exist, nothing more.
        Contract contract = new Contract(
                "GET /products/42 returns a product with name and price",
                "GET /products/42",
                Map.of("name", "Wireless Mouse", "price", "24.99")
        );

        System.out.println("Recorded contract: " + contract.description());
        System.out.println("Consumer needs fields: " + contract.expectedResponseFields().keySet());

        // Prove the consumer's own logic works against exactly this shape.
        String rendered = describeProduct(contract.expectedResponseFields());
        System.out.println("Consumer renders: " + rendered);
    }
}
```

How to run: `java ContractRecordingBasic.java`

The `Contract` here captures only what `describeProduct` actually reads (`name` and `price`) — not every field the provider might return. This mirrors how a real consumer-driven contract-testing tool (like Pact) works: it records the *actual* interactions your consumer's tests make against a mock provider, so the contract reflects real usage rather than a hand-guessed superset of fields. A narrow contract is a feature, not a limitation — it means the provider is only held to promises consumers actually rely on.

### Level 2 — Intermediate

```java
// File: ContractVerificationBasic.java -- the PROVIDER side: replay the
// SAME contract from Level 1 against a real (in-process) provider
// implementation, verifying the real code satisfies every recorded field --
// this is what runs in the provider's own CI pipeline.
import java.util.*;

public class ContractVerificationBasic {
    record Contract(String description, String request, Map<String, String> expectedResponseFields) {}

    // The REAL provider implementation being verified.
    static class ProductCatalogProvider {
        Map<String, String> getProduct(String id) {
            if (!id.equals("42")) throw new NoSuchElementException("no such product: " + id);
            Map<String, String> response = new HashMap<>();
            response.put("name", "Wireless Mouse");
            response.put("price", "24.99");
            response.put("sku", "WM-42"); // extra field the consumer doesn't use -- fine
            return response;
        }
    }

    // Verifies the provider's REAL response satisfies every field the contract requires.
    static boolean verify(Contract contract, Map<String, String> realResponse) {
        for (Map.Entry<String, String> expected : contract.expectedResponseFields().entrySet()) {
            String actual = realResponse.get(expected.getKey());
            if (!Objects.equals(expected.getValue(), actual)) {
                System.out.println("CONTRACT VIOLATION: field '" + expected.getKey()
                        + "' expected '" + expected.getValue() + "' but provider returned '" + actual + "'");
                return false;
            }
        }
        return true;
    }

    public static void main(String[] args) {
        Contract contract = new Contract(
                "GET /products/42 returns a product with name and price",
                "GET /products/42",
                Map.of("name", "Wireless Mouse", "price", "24.99")
        );

        ProductCatalogProvider provider = new ProductCatalogProvider();
        Map<String, String> realResponse = provider.getProduct("42");

        boolean verified = verify(contract, realResponse);
        System.out.println("Contract verified against REAL provider code: " + verified);
        System.out.println("Provider's real response also includes 'sku', which the contract never required -- that's fine.");
    }
}
```

How to run: `java ContractVerificationBasic.java`

`verify` replays the contract against `provider.getProduct("42")` — real provider code, not a mock — and checks that every field the consumer actually depends on is present with the right value. Notice the provider's real response also includes a `sku` field the contract never mentioned; that's completely fine, because the contract only asserts on what the consumer reads. This asymmetry (the provider can add fields freely; it can't remove or change ones a contract depends on) is central to how consumer-driven contracts let providers evolve without breaking consumers unnecessarily.

### Level 3 — Advanced

```java
// File: ContractVerificationBreakingChange.java -- the SAME contract, now
// verified against a provider that has been REFACTORED in a way that
// silently breaks a real consumer -- the production-flavored case contract
// testing exists to catch BEFORE the provider deploys.
import java.util.*;

public class ContractVerificationBreakingChange {
    record Contract(String description, String request, Map<String, String> expectedResponseFields) {}

    // Version 1: the ORIGINAL provider the contract was recorded against.
    static class ProductCatalogProviderV1 {
        Map<String, String> getProduct(String id) {
            Map<String, String> r = new HashMap<>();
            r.put("name", "Wireless Mouse");
            r.put("price", "24.99");
            return r;
        }
    }

    // Version 2: the provider team renamed "price" to "unitPrice" during a
    // refactor, and rounded it to a whole number -- looks harmless internally,
    // but silently breaks any consumer still reading the old field name/shape.
    static class ProductCatalogProviderV2 {
        Map<String, String> getProduct(String id) {
            Map<String, String> r = new HashMap<>();
            r.put("name", "Wireless Mouse");
            r.put("unitPrice", "25"); // renamed AND changed precision
            return r;
        }
    }

    static boolean verify(Contract contract, Map<String, String> realResponse) {
        boolean allOk = true;
        for (Map.Entry<String, String> expected : contract.expectedResponseFields().entrySet()) {
            String actual = realResponse.get(expected.getKey());
            if (!Objects.equals(expected.getValue(), actual)) {
                System.out.println("CONTRACT VIOLATION: field '" + expected.getKey()
                        + "' expected '" + expected.getValue() + "' but provider returned '" + actual + "'");
                allOk = false;
            }
        }
        return allOk;
    }

    public static void main(String[] args) {
        Contract contract = new Contract(
                "GET /products/42 returns a product with name and price",
                "GET /products/42",
                Map.of("name", "Wireless Mouse", "price", "24.99")
        );

        System.out.println("--- Verifying against provider V1 (before refactor) ---");
        boolean v1Ok = verify(contract, new ProductCatalogProviderV1().getProduct("42"));
        System.out.println("V1 verification passed: " + v1Ok);

        System.out.println("--- Verifying against provider V2 (after refactor) ---");
        boolean v2Ok = verify(contract, new ProductCatalogProviderV2().getProduct("42"));
        System.out.println("V2 verification passed: " + v2Ok
                + " -- this FAILS THE PROVIDER'S OWN BUILD, catching the break before deployment.");
    }
}
```

How to run: `java ContractVerificationBreakingChange.java`

`ProductCatalogProviderV2` represents a refactor that looks entirely reasonable in isolation — renaming a field for clarity, tightening precision — but the consumer's contract still expects a field literally named `price`. Running `verify` against `V2`'s response fails loudly with a specific, actionable message (`field 'price' expected '24.99' but provider returned 'null'`), because `unitPrice` isn't `price` as far as the contract is concerned. This is the entire point of consumer-driven contract testing: this failure happens in the *provider's own CI pipeline*, against the provider's *own real code*, without the consumer service needing to be running anywhere — catching a breaking change during code review or a pre-merge build instead of during a production incident days or weeks later.

## 6. Walkthrough

Trace `ContractVerificationBreakingChange.main` in order. **First**, `new ProductCatalogProviderV1().getProduct("42")` runs, returning a real map with `name="Wireless Mouse"` and `price="24.99"`. `verify(contract, ...)` loops over the contract's two expected fields: `name` matches exactly, `price` matches exactly. No violation is printed, and `v1Ok` is `true` — the original provider satisfies the consumer's contract, as expected, since the contract was recorded against this exact shape.

**Next**, `new ProductCatalogProviderV2().getProduct("42")` runs, returning a map with `name="Wireless Mouse"` and `unitPrice="25"` — note there is no `price` key at all anymore. **Then**, `verify` loops over the same contract fields again. The `name` check passes as before. The `price` check calls `realResponse.get("price")`, which returns `null` because the key was renamed to `unitPrice`. Since `Objects.equals("24.99", null)` is `false`, the violation branch fires: it prints `CONTRACT VIOLATION: field 'price' expected '24.99' but provider returned 'null'` and sets `allOk` to `false`.

**Finally**, `main` prints `V2 verification passed: false`, along with a note that this failure would fail the provider's own build. In a real Pact-based setup, this exact failure would show up as a failed provider-verification task in the provider team's CI pipeline, with the contract's `description` field ("GET /products/42 returns a product with name and price") making it immediately clear which consumer and which specific interaction broke — turning what could have been a silent production incident into a specific, actionable CI failure.

```
--- Verifying against provider V1 (before refactor) ---
V1 verification passed: true
--- Verifying against provider V2 (after refactor) ---
CONTRACT VIOLATION: field 'price' expected '24.99' but provider returned 'null'
V2 verification passed: false -- this FAILS THE PROVIDER'S OWN BUILD, catching the break before deployment.
```

## 7. Gotchas & takeaways

> A contract that's too broad — asserting on every field a provider happens to return, rather than only the fields the consumer actually reads — turns into exactly the brittleness contract testing is supposed to prevent: the provider can no longer add or reorganize unused fields without "breaking" a contract that never needed to depend on them. Keep contracts narrow, matching real consumer usage, not the full response shape.

- Consumer-driven means the *consumer* defines what must stay true; the provider is free to change anything a contract doesn't assert on — this is what lets providers evolve without needing to coordinate every change with every consumer team.
- Contract verification runs fast and without needing both services live simultaneously, which is why it replaces a large chunk of what an [end-to-end test](0417-end-to-end-testing-its-fragility.md) would otherwise have to catch, at a fraction of the cost.
- See [provider vs consumer contracts](0416-provider-vs-consumer-contracts.md) for how the two sides' responsibilities and workflows differ in practice.
- Contract testing sits between [component testing](0414-component-testing-single-service-in-isolation.md) and end-to-end testing in the [test pyramid](0411-test-pyramid-for-microservices.md) — it directly targets the cross-service compatibility risk that component tests (with hand-guessed stubs) can silently miss.
- A failed contract verification should block deployment, or at minimum page the responsible team immediately — the entire value of the practice comes from catching the break before it reaches production, not after.
