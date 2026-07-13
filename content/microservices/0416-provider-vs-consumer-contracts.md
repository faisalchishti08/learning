---
card: microservices
gi: 416
slug: provider-vs-consumer-contracts
title: "Provider vs consumer contracts"
---

## 1. What it is

In [contract testing](0415-contract-testing-consumer-driven-contracts.md), every interaction between two services has two distinct sides with two distinct responsibilities: the **consumer side** authors and publishes the contract, describing exactly what it needs from the API it calls; the **provider side** verifies that its real implementation satisfies every contract published against it, across every consumer that depends on it. These are not two kinds of contracts — there's one contract per consumer-provider pair — but two different roles in the same workflow, run by two different teams, at two different times, and understanding which responsibilities belong to which side is what makes the practice actually work at scale.

## 2. Why & when

You need to keep these roles straight because conflating them is the most common way teams get contract testing wrong. If a provider team writes the contracts *for* their consumers (instead of consumers writing their own), the contracts end up describing what the provider thinks consumers need — which drifts from reality exactly the way a hand-guessed API doc would. If a consumer team never runs verification and just trusts the provider's word, they lose the safety net contract testing exists to provide.

- **The consumer knows what it actually uses; the provider doesn't.** Only the team calling an API in production knows which fields their code actually reads and which response shapes their error handling actually depends on — which is why the contract has to originate on the consumer side, even though enforcement happens on the provider side.
- **A single provider often has many consumers, each with a slightly different contract.** An `OrderService` might be called by a `WebCheckoutClient`, a `MobileAppClient`, and a `PartnerIntegrationClient`, each depending on a different subset of fields. The provider's job is to satisfy *all* of them simultaneously, which only works if each consumer's real dependency is captured precisely, not guessed at collectively.
- **Verification timing matters.** The provider runs verification in *its own* CI pipeline, on *its own* schedule — typically on every change to the provider's code, and again whenever a consumer publishes an updated contract. This decouples the two teams' release cadences almost completely, which is the whole point in a microservices org with many independently deployed teams.
- **Ownership of a broken contract is asymmetric.** If verification fails because the provider changed something a consumer depends on, the provider caused the break — it should either honor the old shape (backward compatibility) or coordinate the change with the consumer before deploying. If a consumer publishes an unreasonably broad contract (asserting on fields it doesn't use), that's a consumer-side problem to fix, not something the provider should have to accommodate forever.

## 3. Core concept

Picture a landlord (provider) and several tenants (consumers) in the same building. Each tenant signs their own lease describing exactly what they're entitled to — a working lock on their specific door, heat in their specific unit, access to the specific shared laundry room their lease mentions. The landlord doesn't write the leases; tenants do, based on what they actually need. But the landlord is the one who has to keep *every* signed lease satisfied at once, and before doing any renovation, checks all outstanding leases first to make sure the renovation doesn't violate one of them.

Concretely, the two roles split like this:

| | Consumer side | Provider side |
|---|---|---|
| **Authors the contract** | Yes — based on real usage of the API | No |
| **Where verification runs** | Not run here; the consumer trusts the broker holds the latest contract | Runs the contract's recorded interactions against the provider's real code |
| **When it runs** | Whenever the consumer's own tests exercise the dependency (contract is recorded as a byproduct) | In the provider's own CI, on every change, and whenever a consumer contract changes |
| **What a failure means** | The consumer is depending on something the provider doesn't (yet) support | The provider is about to break a real, specific consumer |
| **Who fixes it** | The consumer, if the contract was wrong or overly broad | The provider, if a real change would break a currently-supported consumer |

A **contract broker** (a shared service, such as the Pact Broker) is what makes this asynchronous split practical: consumers publish contracts to it; providers pull the latest contracts from it to verify against; and the broker can further compute whether a given provider version is safe to deploy against every consumer version currently in production — sometimes called the "can I deploy" check.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple consumers each author their own contract describing what they depend on; the provider verifies its real code against every contract from every consumer before deploying" font-family="sans-serif">
  <rect x="30" y="20" width="130" height="45" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="47" fill="#e6edf3" font-size="10" text-anchor="middle">WebCheckoutClient</text>
  <rect x="30" y="80" width="130" height="45" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="107" fill="#e6edf3" font-size="10" text-anchor="middle">MobileAppClient</text>
  <rect x="30" y="140" width="130" height="45" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="167" fill="#e6edf3" font-size="10" text-anchor="middle">PartnerClient</text>
  <text x="95" y="205" fill="#8b949e" font-size="9" text-anchor="middle">each authors its OWN contract</text>

  <line x1="160" y1="42" x2="250" y2="90" stroke="#79c0ff" stroke-dasharray="3,2"/>
  <line x1="160" y1="102" x2="250" y2="102" stroke="#79c0ff" stroke-dasharray="3,2"/>
  <line x1="160" y1="162" x2="250" y2="115" stroke="#79c0ff" stroke-dasharray="3,2"/>

  <rect x="250" y="75" width="140" height="55" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="98" fill="#e6edf3" font-size="10" text-anchor="middle">Contract broker</text>
  <text x="320" y="115" fill="#8b949e" font-size="9" text-anchor="middle">3 contracts stored</text>

  <line x1="390" y1="102" x2="460" y2="102" stroke="#f0883e" stroke-width="2"/>

  <rect x="460" y="75" width="150" height="55" rx="10" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="535" y="98" fill="#e6edf3" font-size="10" text-anchor="middle">OrderService (provider)</text>
  <text x="535" y="115" fill="#8b949e" font-size="9" text-anchor="middle">verifies against ALL 3</text>

  <text x="320" y="230" fill="#8b949e" font-size="10" text-anchor="middle">the provider must satisfy every consumer's contract at once</text>
</svg>

Each consumer authors its own contract independently; the provider is responsible for satisfying every one of them simultaneously before it can safely deploy.

## 5. Runnable example

Scenario: an `OrderService` provider consumed by two different clients — `WebCheckoutClient`, which needs an order's total and status, and `PartnerClient`, which additionally needs a tracking number. We build up from a single-consumer setup to a full multi-consumer verification run, then handle the hard case: a provider change that satisfies one consumer's contract while breaking another's.

### Level 1 — Basic

```java
// File: SingleConsumerContract.java -- ONE consumer authors a contract for
// what it needs; the provider verifies its real code against just that one.
import java.util.*;

public class SingleConsumerContract {
    record Contract(String consumerName, Map<String, String> expectedFields) {}

    static class OrderServiceProvider {
        Map<String, String> getOrder(String id) {
            Map<String, String> order = new HashMap<>();
            order.put("total", "129.50");
            order.put("status", "CONFIRMED");
            return order;
        }
    }

    static boolean verify(Contract contract, Map<String, String> realResponse) {
        for (Map.Entry<String, String> field : contract.expectedFields().entrySet()) {
            if (!Objects.equals(field.getValue(), realResponse.get(field.getKey()))) {
                System.out.println("VIOLATION for consumer '" + contract.consumerName() + "': field '"
                        + field.getKey() + "' expected '" + field.getValue() + "' got '" + realResponse.get(field.getKey()) + "'");
                return false;
            }
        }
        return true;
    }

    public static void main(String[] args) {
        // WebCheckoutClient authored this contract based on what IT reads.
        Contract webCheckoutContract = new Contract("WebCheckoutClient",
                Map.of("total", "129.50", "status", "CONFIRMED"));

        OrderServiceProvider provider = new OrderServiceProvider();
        boolean ok = verify(webCheckoutContract, provider.getOrder("order-1"));
        System.out.println("Provider satisfies WebCheckoutClient's contract: " + ok);
    }
}
```

How to run: `java SingleConsumerContract.java`

`webCheckoutContract` is authored from the consumer's perspective — it lists exactly the two fields `WebCheckoutClient` reads. `verify` runs on the provider side, checking the provider's real `getOrder` output against that contract. With a single consumer, this is exactly the same shape as basic contract testing; the roles become more interesting once a second consumer, with a different set of needs, enters the picture.

### Level 2 — Intermediate

```java
// File: MultiConsumerVerification.java -- the SAME provider, now verified
// against TWO DIFFERENT consumer contracts, each authored independently by
// its own consumer team, reflecting that a provider often has to satisfy
// several different sets of expectations at once.
import java.util.*;

public class MultiConsumerVerification {
    record Contract(String consumerName, Map<String, String> expectedFields) {}

    static class OrderServiceProvider {
        Map<String, String> getOrder(String id) {
            Map<String, String> order = new HashMap<>();
            order.put("total", "129.50");
            order.put("status", "CONFIRMED");
            order.put("trackingNumber", "TRK-9981");
            return order;
        }
    }

    static boolean verify(Contract contract, Map<String, String> realResponse) {
        boolean ok = true;
        for (Map.Entry<String, String> field : contract.expectedFields().entrySet()) {
            if (!Objects.equals(field.getValue(), realResponse.get(field.getKey()))) {
                System.out.println("VIOLATION for consumer '" + contract.consumerName() + "': field '"
                        + field.getKey() + "' expected '" + field.getValue() + "' got '" + realResponse.get(field.getKey()) + "'");
                ok = false;
            }
        }
        return ok;
    }

    public static void main(String[] args) {
        // Two consumers, two independently authored contracts against the SAME provider.
        List<Contract> allContracts = List.of(
                new Contract("WebCheckoutClient", Map.of("total", "129.50", "status", "CONFIRMED")),
                new Contract("PartnerClient", Map.of("status", "CONFIRMED", "trackingNumber", "TRK-9981"))
        );

        OrderServiceProvider provider = new OrderServiceProvider();
        Map<String, String> realResponse = provider.getOrder("order-1");

        boolean allPassed = true;
        for (Contract contract : allContracts) {
            boolean ok = verify(contract, realResponse);
            System.out.println("Provider satisfies " + contract.consumerName() + "'s contract: " + ok);
            allPassed &= ok;
        }
        System.out.println("Safe to deploy against ALL known consumers: " + allPassed);
    }
}
```

How to run: `java MultiConsumerVerification.java`

The provider's real response now includes a `trackingNumber` field that `WebCheckoutClient` never asked for and doesn't care about — and that's fine, because `WebCheckoutClient`'s contract doesn't assert on it. `PartnerClient`'s contract, authored independently by a different team, *does* require `trackingNumber`. Looping over `allContracts` and verifying each one independently mirrors what a real contract broker's "can I deploy" check computes: is this provider version compatible with every consumer version currently depending on it, not just one.

### Level 3 — Advanced

```java
// File: ProviderChangeMultiConsumerImpact.java -- the SAME two-consumer
// setup, now with a REAL provider code change that satisfies one consumer's
// contract while silently breaking the other -- the production-flavored
// case: a change can look safe when checked against only one consumer.
import java.util.*;

public class ProviderChangeMultiConsumerImpact {
    record Contract(String consumerName, Map<String, String> expectedFields) {}

    // The provider team refactors the status field's values to be more descriptive --
    // this passes a quick manual check against WebCheckoutClient's docs, but nobody
    // checked PartnerClient's actual contract before making the change.
    static class OrderServiceProviderRefactored {
        Map<String, String> getOrder(String id) {
            Map<String, String> order = new HashMap<>();
            order.put("total", "129.50");
            order.put("status", "PAYMENT_CONFIRMED"); // renamed from "CONFIRMED" for clarity
            order.put("trackingNumber", "TRK-9981");
            return order;
        }
    }

    static boolean verify(Contract contract, Map<String, String> realResponse) {
        boolean ok = true;
        for (Map.Entry<String, String> field : contract.expectedFields().entrySet()) {
            if (!Objects.equals(field.getValue(), realResponse.get(field.getKey()))) {
                System.out.println("VIOLATION for consumer '" + contract.consumerName() + "': field '"
                        + field.getKey() + "' expected '" + field.getValue() + "' got '" + realResponse.get(field.getKey()) + "'");
                ok = false;
            }
        }
        return ok;
    }

    public static void main(String[] args) {
        List<Contract> allContracts = List.of(
                new Contract("WebCheckoutClient", Map.of("total", "129.50")), // doesn't check status at all
                new Contract("PartnerClient", Map.of("status", "CONFIRMED", "trackingNumber", "TRK-9981"))
        );

        OrderServiceProviderRefactored provider = new OrderServiceProviderRefactored();
        Map<String, String> realResponse = provider.getOrder("order-1");

        boolean allPassed = true;
        for (Contract contract : allContracts) {
            boolean ok = verify(contract, realResponse);
            System.out.println(contract.consumerName() + " verification: " + (ok ? "PASS" : "FAIL"));
            allPassed &= ok;
        }
        System.out.println("Safe to deploy: " + allPassed
                + " -- caught BEFORE deploy, even though WebCheckoutClient alone looked fine.");
    }
}
```

How to run: `java ProviderChangeMultiConsumerImpact.java`

If the provider team had only checked their change against `WebCheckoutClient` (which never reads `status` at all), the refactor would have looked completely safe. Running verification against *every known consumer's contract*, as a real contract broker's deploy-safety check does, reveals that `PartnerClient` — a consumer the provider team may not have even been thinking about during this refactor — depends on the exact string `"CONFIRMED"`, and the rename to `"PAYMENT_CONFIRMED"` breaks it. This is the concrete payoff of the provider/consumer split: the provider doesn't need to remember every consumer's needs from memory; it just needs to verify against the full, current set of published contracts before every deploy.

## 6. Walkthrough

Trace `ProviderChangeMultiConsumerImpact.main` in order. **First**, `provider.getOrder("order-1")` runs against the refactored provider, returning a real map with `total="129.50"`, `status="PAYMENT_CONFIRMED"`, and `trackingNumber="TRK-9981"`.

**Next**, the loop begins with `WebCheckoutClient`'s contract, which only asserts on `total`. `verify` checks `realResponse.get("total")` against `"129.50"` — they match, so no violation is printed, `ok` stays `true`, and `"WebCheckoutClient verification: PASS"` is printed.

**Then**, the loop continues with `PartnerClient`'s contract, which asserts on both `status` and `trackingNumber`. `verify` checks `status`: the contract expects `"CONFIRMED"`, but `realResponse.get("status")` is now `"PAYMENT_CONFIRMED"` — these don't match, so the violation branch fires, printing `VIOLATION for consumer 'PartnerClient': field 'status' expected 'CONFIRMED' got 'PAYMENT_CONFIRMED'`, and `ok` becomes `false`. The `trackingNumber` check still runs afterward (the loop doesn't short-circuit) and passes, but the overall `ok` for this contract is already `false` from the status failure, so `"PartnerClient verification: FAIL"` is printed.

**Finally**, `allPassed` — which started `true` and gets AND-ed with each consumer's result — ends up `false` because of `PartnerClient`'s failure, even though `WebCheckoutClient`'s check alone passed cleanly. `main` prints `Safe to deploy: false`, which in a real CI pipeline would block this provider version from deploying until the team either reverts the field rename or coordinates it with `PartnerClient`'s team.

```
WebCheckoutClient verification: PASS
VIOLATION for consumer 'PartnerClient': field 'status' expected 'CONFIRMED' got 'PAYMENT_CONFIRMED'
PartnerClient verification: FAIL
Safe to deploy: false -- caught BEFORE deploy, even though WebCheckoutClient alone looked fine.
```

## 7. Gotchas & takeaways

> A provider that only tests against the consumer contracts it remembers to check manually will eventually miss one — exactly the failure mode `ProviderChangeMultiConsumerImpact` demonstrates. The fix is process, not vigilance: the provider's CI pipeline should automatically pull *every* currently-published contract from the broker and verify against all of them on every change, so no consumer can be silently forgotten.

- The consumer authors the contract from real usage; the provider verifies its real code against it — mixing up who does which defeats the practice.
- A single provider typically satisfies many consumers' contracts simultaneously; verifying against only one consumer, or only the ones you remember, is how breaking changes slip through.
- A contract broker's "can I deploy" check exists precisely to automate the multi-consumer verification shown in Level 3 — it's the mechanism that scales this practice past a handful of manually-tracked consumers.
- Providers can freely add fields or support additional values without breaking anyone; changing or removing something an existing contract depends on is the one thing that requires either backward compatibility or coordinated rollout.
- See [contract testing](0415-contract-testing-consumer-driven-contracts.md) for the full recording-and-verification workflow this topic assumes as background.
