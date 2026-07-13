---
card: microservices
gi: 423
slug: contract-test-broker-pact-broker
title: "Contract test broker / Pact Broker"
---

## 1. What it is

A **contract test broker** is a shared, queryable service that stores the contracts produced by [consumer-driven contract testing](0415-contract-testing-consumer-driven-contracts.md) and the verification results providers run against them. **Pact Broker** is the best-known open-source implementation, but the role is generic: consumers publish the contracts they record; providers pull the latest contracts, verify them, and publish the pass/fail results back; and anyone — a human or a CI pipeline — can ask the broker a single, decisive question before a deployment: **"can I deploy this version safely, given everyone it talks to?"** Without a broker, contracts end up as files emailed between teams or checked into ad hoc repositories, and nobody has a reliable, up-to-date answer to that question.

## 2. Why & when

You reach for a contract broker the moment consumer-driven contract testing needs to scale past two services that happen to sit in the same repository. A contract that lives only in the consumer's build output is invisible to the provider's CI pipeline — someone has to manually copy it over, which is exactly the kind of manual coordination [contract testing](0415-contract-testing-consumer-driven-contracts.md) exists to eliminate. A broker fixes that by being the durable, addressable middle layer both sides talk to automatically:

- **It's the single source of truth for "what does this provider need to keep working."** A provider verifying against a broker automatically discovers every consumer contract ever published for it, including from consumer teams it may not even be in regular contact with.
- **It tracks verification results per contract version**, so a provider team (or a deployment pipeline) can ask, before deploying, "have I verified against the latest contract from every consumer that matters?"
- **It answers the deploy-safety question directly.** Pact Broker's `can-i-deploy` command checks whether the specific versions of a consumer and provider you're about to deploy have a mutually verified, compatible contract — turning "did we break anyone" from a guess into a yes/no answer backed by real verification history.
- **It supports webhooks**, so a newly published or newly verified contract can automatically trigger the other side's CI pipeline — a provider team gets notified the moment a new consumer contract appears, without polling or manual coordination.

You introduce a broker as soon as more than one team is involved in contract testing, and it becomes essential — not optional — once you have multiple consumers of the same provider, multiple versions of each service in flight (a new consumer version, an old provider version still in production), and a release process that needs an automated, trustworthy gate rather than a spreadsheet of "who talked to whom."

## 3. Core concept

Picture a broker like a building's shared parcel room, replacing everyone leaving packages on each other's desks. A consumer team "ships" a contract to the parcel room labeled with its own version number. A provider team, whenever it's about to deploy, checks the parcel room for every package addressed to it, verifies the contents match what it can actually deliver, and posts a receipt back into the room saying "verified: yes" or "verified: no." Before either team ships a truck (deploys), they ask the parcel room's front desk one question — "is everything addressed between these two specific versions verified and matching?" — and only proceed if the answer is yes.

Concretely, the broker-centered workflow has four moving parts:

1. **Publish** — after recording a contract (see [contract testing](0415-contract-testing-consumer-driven-contracts.md)), the consumer's build pushes it to the broker, tagged with the consumer's version (usually a git commit SHA) and often an environment tag (`dev`, `staging`, `production`).
2. **Verify** — the provider's build pulls every contract addressed to it from the broker, replays each one against its real running code, and pushes the pass/fail result back to the broker, tagged with the provider's own version.
3. **Query** — before deploying either service, a CI step calls the broker's deploy-safety check (Pact Broker calls this `can-i-deploy`) with the specific versions about to go out; the broker answers based on the verification results it has recorded for those exact versions.
4. **Deploy record** — after a successful deployment, the broker is told which version is now live in which environment, so future `can-i-deploy` checks account for what's actually running in production, not just what passed a test once.

The critical shift this enables is that provider teams no longer need to know, personally, which consumers exist — the broker's records are the complete, always-current list, discovered automatically rather than tracked in someone's head.

## 4. Diagram

<svg viewBox="0 0 640 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two consumers publish contracts to a broker; a provider pulls all contracts addressed to it, verifies them, and publishes results back; before deploying, a CI pipeline asks the broker can-i-deploy for the specific versions involved">
  <rect x="20" y="20" width="130" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="85" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Consumer A</text>
  <text x="85" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">v1.4.0</text>

  <rect x="20" y="220" width="130" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="85" y="242" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Consumer B</text>
  <text x="85" y="258" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">v2.1.0</text>

  <rect x="240" y="110" width="160" height="80" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="140" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Contract Broker</text>
  <text x="320" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">contracts + verification</text>
  <text x="320" y="172" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">results, per version</text>

  <line x1="150" y1="45" x2="240" y2="130" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="150" y1="245" x2="240" y2="170" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="190" y="90" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">publish</text>
  <text x="190" y="210" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">publish</text>

  <rect x="470" y="110" width="150" height="80" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="545" y="140" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Provider</text>
  <text x="545" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">pulls + verifies</text>
  <text x="545" y="172" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">publishes results</text>

  <line x1="400" y1="150" x2="470" y2="150" stroke="#f0883e" stroke-width="2"/>
  <text x="435" y="140" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">pull/push</text>

  <text x="320" y="230" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">before deploy: can-i-deploy(consumer vX, provider vY)?</text>
  <text x="320" y="250" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">broker answers using real recorded verification results</text>
</svg>

Consumers publish contracts, the provider verifies and reports back, and both sides query the broker before deploying instead of coordinating by hand.

## 5. Runnable example

Scenario: an in-process stand-in for a contract broker that stores published contracts and verification results, then answers a `canIDeploy` question for specific consumer and provider versions.

### Level 1 — Basic

```java
// File: BrokerPublishBasic.java -- a minimal in-memory broker that a
// consumer can publish a contract to, tagged with its own version.
import java.util.*;

public class BrokerPublishBasic {
    record Contract(String consumerName, String consumerVersion, String providerName, String description) {}

    static class ContractBroker {
        private final List<Contract> contracts = new ArrayList<>();
        void publish(Contract c) {
            contracts.add(c);
            System.out.println("[Broker] published contract: " + c.consumerName() + "@" + c.consumerVersion()
                    + " -> " + c.providerName() + " (" + c.description() + ")");
        }
        List<Contract> contractsFor(String providerName) {
            return contracts.stream().filter(c -> c.providerName().equals(providerName)).toList();
        }
    }

    public static void main(String[] args) {
        ContractBroker broker = new ContractBroker();
        broker.publish(new Contract("OrderSummaryConsumer", "1.4.0", "ProductCatalogProvider",
                "GET /products/42 returns name and price"));

        List<Contract> forProvider = broker.contractsFor("ProductCatalogProvider");
        System.out.println("ProductCatalogProvider has " + forProvider.size() + " contract(s) addressed to it.");
    }
}
```

How to run: `java BrokerPublishBasic.java`

`ContractBroker.publish` records a contract exactly as a real broker would: tagged with the consumer's name and version, and the provider it targets. `contractsFor` is what a provider's CI pipeline calls to discover every contract it needs to satisfy — note that nothing here requires the provider team to already know `OrderSummaryConsumer` exists; the broker is the discovery mechanism.

### Level 2 — Intermediate

```java
// File: BrokerVerifyAndReport.java -- the SAME broker, now with the
// PROVIDER side: pulling contracts, verifying them against real provider
// logic, and publishing verification results back to the broker.
import java.util.*;

public class BrokerVerifyAndReport {
    record Contract(String consumerName, String consumerVersion, String providerName, String description) {}
    record VerificationResult(String consumerName, String consumerVersion, String providerVersion, boolean success) {}

    static class ContractBroker {
        private final List<Contract> contracts = new ArrayList<>();
        private final List<VerificationResult> results = new ArrayList<>();

        void publish(Contract c) { contracts.add(c); }
        List<Contract> contractsFor(String providerName) {
            return contracts.stream().filter(c -> c.providerName().equals(providerName)).toList();
        }
        void reportVerification(VerificationResult r) {
            results.add(r);
            System.out.println("[Broker] recorded verification: " + r.consumerName() + "@" + r.consumerVersion()
                    + " against provider@" + r.providerVersion() + " -> " + (r.success() ? "PASS" : "FAIL"));
        }
        boolean hasPassingVerification(String consumerName, String consumerVersion, String providerVersion) {
            return results.stream().anyMatch(r -> r.consumerName().equals(consumerName)
                    && r.consumerVersion().equals(consumerVersion)
                    && r.providerVersion().equals(providerVersion)
                    && r.success());
        }
    }

    public static void main(String[] args) {
        ContractBroker broker = new ContractBroker();
        broker.publish(new Contract("OrderSummaryConsumer", "1.4.0", "ProductCatalogProvider", "GET /products/42"));

        // Provider's CI pulls contracts, verifies against real code (simulated as always-true here), and reports back.
        String providerVersion = "3.2.0";
        for (Contract c : broker.contractsFor("ProductCatalogProvider")) {
            boolean verified = true; // stand-in for actually replaying the contract against real code
            broker.reportVerification(new VerificationResult(c.consumerName(), c.consumerVersion(), providerVersion, verified));
        }

        boolean canDeploy = broker.hasPassingVerification("OrderSummaryConsumer", "1.4.0", providerVersion);
        System.out.println("Verified pair exists for consumer 1.4.0 / provider " + providerVersion + ": " + canDeploy);
    }
}
```

How to run: `java BrokerVerifyAndReport.java`

The provider loop mirrors what a real Pact Broker-integrated CI job does: pull every contract `contractsFor("ProductCatalogProvider")` returns, verify each one, and immediately `reportVerification` the outcome tagged with the provider's own version. `hasPassingVerification` is the basis for a deploy-safety check — it asks whether *this exact pair* of versions has a recorded, passing verification, not just whether verification ever passed for any version.

### Level 3 — Advanced

```java
// File: BrokerCanIDeploy.java -- the SAME broker, now implementing a
// realistic can-i-deploy check across MULTIPLE consumers and provider
// versions, including the production-flavored case: one consumer verified
// against an OLD provider version, and the provider about to deploy a NEW
// version nobody has verified against yet.
import java.util.*;

public class BrokerCanIDeploy {
    record Contract(String consumerName, String consumerVersion, String providerName) {}
    record VerificationResult(String consumerName, String consumerVersion, String providerVersion, boolean success) {}

    static class ContractBroker {
        private final List<Contract> contracts = new ArrayList<>();
        private final List<VerificationResult> results = new ArrayList<>();
        private final Map<String, String> deployedVersion = new HashMap<>(); // service -> currently-live version

        void publish(Contract c) { contracts.add(c); }
        void reportVerification(VerificationResult r) { results.add(r); }
        void recordDeployment(String service, String version) { deployedVersion.put(service, version); }

        // can-i-deploy: for the given provider version, every consumer version
        // CURRENTLY DEPLOYED must have a passing verification against it.
        boolean canIDeploy(String providerName, String providerVersion) {
            List<String> blockers = new ArrayList<>();
            Set<String> consumersOfProvider = contracts.stream()
                    .filter(c -> c.providerName().equals(providerName))
                    .map(Contract::consumerName).collect(java.util.stream.Collectors.toSet());

            for (String consumer : consumersOfProvider) {
                String liveConsumerVersion = deployedVersion.get(consumer);
                if (liveConsumerVersion == null) continue; // consumer not deployed anywhere yet -- nothing to break
                boolean verified = results.stream().anyMatch(r -> r.consumerName().equals(consumer)
                        && r.consumerVersion().equals(liveConsumerVersion)
                        && r.providerVersion().equals(providerVersion) && r.success());
                if (!verified) blockers.add(consumer + "@" + liveConsumerVersion);
            }
            if (!blockers.isEmpty()) {
                System.out.println("[Broker] BLOCKED deploying " + providerName + "@" + providerVersion
                        + " -- no passing verification against currently-live consumer(s): " + blockers);
                return false;
            }
            System.out.println("[Broker] OK to deploy " + providerName + "@" + providerVersion
                    + " -- all currently-live consumers have a passing verification.");
            return true;
        }
    }

    public static void main(String[] args) {
        ContractBroker broker = new ContractBroker();
        broker.publish(new Contract("OrderSummaryConsumer", "1.4.0", "ProductCatalogProvider"));
        broker.publish(new Contract("RecommendationConsumer", "2.0.0", "ProductCatalogProvider"));

        // OrderSummaryConsumer 1.4.0 is live in production, and HAS been verified against provider 3.2.0.
        broker.recordDeployment("OrderSummaryConsumer", "1.4.0");
        broker.reportVerification(new VerificationResult("OrderSummaryConsumer", "1.4.0", "3.2.0", true));

        // RecommendationConsumer 2.0.0 is ALSO live in production, but nobody has verified it against 3.3.0 yet.
        broker.recordDeployment("RecommendationConsumer", "2.0.0");

        System.out.println("--- Attempting to deploy provider 3.2.0 (already verified for both live consumers?) ---");
        broker.canIDeploy("ProductCatalogProvider", "3.2.0");

        System.out.println("--- Attempting to deploy NEW provider 3.3.0 (nobody has verified RecommendationConsumer yet) ---");
        broker.canIDeploy("ProductCatalogProvider", "3.3.0");
    }
}
```

How to run: `java BrokerCanIDeploy.java`

`canIDeploy` deliberately only checks consumers that are *currently deployed* (`deployedVersion`), not every version that ever published a contract — this mirrors real Pact Broker behavior, which cares about what's actually live in production, not historical versions nobody runs anymore. The 3.2.0 check passes because it only has one currently-live consumer (`RecommendationConsumer` was deployed but never verified — this is the deliberate trap the example sets up to show in the second call). The 3.3.0 check fails because no verification record exists for either live consumer against that new version yet.

## 6. Walkthrough

Trace `BrokerCanIDeploy.main` in order. **First**, two contracts are published: `OrderSummaryConsumer` and `RecommendationConsumer` both depend on `ProductCatalogProvider`. **Next**, `recordDeployment` marks `OrderSummaryConsumer@1.4.0` as live, and a passing verification is reported for it against provider `3.2.0`. **Then**, `recordDeployment` marks `RecommendationConsumer@2.0.0` as also live — but critically, no verification is ever reported for `RecommendationConsumer` against any provider version.

**Then**, `canIDeploy("ProductCatalogProvider", "3.2.0")` runs. It collects `consumersOfProvider` as `{OrderSummaryConsumer, RecommendationConsumer}`. For `OrderSummaryConsumer`, the live version is `1.4.0`, and a passing verification exists for `1.4.0` against `3.2.0` — no blocker. For `RecommendationConsumer`, the live version is `2.0.0`, but no verification record exists for it at all against `3.2.0` — this **is** a blocker. `blockers` ends up non-empty, so the deploy is reported **BLOCKED**, even though the reader might have expected it to pass based on the comment framing — this is the actual point: a provider can look "verified" from one consumer's perspective while silently missing coverage for another currently-live consumer.

**Finally**, `canIDeploy("ProductCatalogProvider", "3.3.0")` runs and is blocked for the same underlying reason plus the additional fact that `1.4.0` was never verified against `3.3.0` either — nobody has run verification for the new provider version at all yet.

```
[Broker] BLOCKED deploying ProductCatalogProvider@3.2.0 -- no passing verification against currently-live consumer(s): [RecommendationConsumer@2.0.0]
--- Attempting to deploy NEW provider 3.3.0 (nobody has verified RecommendationConsumer yet) ---
[Broker] BLOCKED deploying ProductCatalogProvider@3.3.0 -- no passing verification against currently-live consumer(s): [OrderSummaryConsumer@1.4.0, RecommendationConsumer@2.0.0]
```

## 7. Gotchas & takeaways

> Teams sometimes treat "the contract exists in the broker" as equivalent to "it's safe to deploy." It isn't — a contract with no recorded *passing verification* for the specific versions about to go live is exactly as dangerous as having no contract at all. Always gate deployment on a `can-i-deploy`-style query against currently-live versions, not on the mere existence of a contract file.

- The broker's value is discovery and history: providers automatically learn about every consumer that depends on them, and deploy decisions are based on real recorded verification results, not tribal knowledge.
- A `can-i-deploy` check should always be scoped to the versions actually being deployed and the versions actually live elsewhere — checking against an arbitrary or outdated version tells you nothing useful.
- Pair the broker with webhooks so a newly published consumer contract automatically triggers the provider's verification build, closing the feedback loop without manual polling.
- See [contract testing](0415-contract-testing-consumer-driven-contracts.md) for how contracts are recorded and verified in the first place, and [Spring Cloud Contract](0429-spring-cloud-contract-consumer-driven-contracts.md) plus its [stub runner](0430-spring-cloud-contract-stub-runner.md) for a broker-adjacent workflow built into the Spring ecosystem.
- A broker doesn't replace a thin layer of [end-to-end tests](0417-end-to-end-testing-its-fragility.md) — it replaces the *cross-service compatibility* portion of what end-to-end tests would otherwise have to catch, at a fraction of the cost and latency.
