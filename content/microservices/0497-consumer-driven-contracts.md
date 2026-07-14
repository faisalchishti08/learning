---
card: microservices
gi: 497
slug: consumer-driven-contracts
title: "Consumer-driven contracts"
---

## 1. What it is

**Consumer-driven contract testing** flips the direction of API contract ownership: instead of a provider unilaterally deciding what its contract looks like, each **consumer** writes a contract describing exactly what it actually depends on — specific fields, specific values it cares about — and the **provider's** CI pipeline runs every consumer's contract against the real provider implementation. If the provider ever makes a change that would break a real consumer's stated expectations, the provider's own build fails, catching the incompatibility before it ships.

## 2. Why & when

You adopt consumer-driven contracts specifically to catch cross-service breaking changes automatically, without requiring full end-to-end integration test environments:

- **A provider often doesn't actually know which fields consumers genuinely depend on.** Removing a field that looks unused from the provider's own perspective can silently break a consumer relying on it — consumer-driven contracts make that dependency explicit and machine-checkable, rather than tribal knowledge.
- **Full end-to-end integration testing across many services is slow, flaky, and expensive to maintain.** Consumer-driven contracts get much of the same safety — catching real breaking changes — without needing every consumer's full runtime stood up together in one test environment.
- **The provider's CI pipeline becomes the enforcement point**, catching a breaking change the moment it's introduced, in the provider's own build, before it's ever deployed — far cheaper than discovering the break in a shared staging environment or, worse, in production.
- **You adopt this once you have multiple consumers of an API who might have different, potentially conflicting expectations** — for an API with a single consumer maintained by the same team as the provider, the overhead of formal contract tests may exceed the benefit.

## 3. Core concept

Think of a set of separate suppliers to a factory, each stating precisely which specifications of a shared component they actually depend on — supplier A needs the bolt's diameter and thread count, supplier B only needs its material composition — and the component manufacturer runs every supplier's stated specification as a check against each new batch before shipping it. If a manufacturing change would violate any supplier's stated spec, the manufacturer catches it themselves, before that batch ever reaches a supplier and causes a problem on their assembly line.

Concretely, the workflow:

1. **Each consumer writes a contract** stating specific expectations of the provider — "when I call `GET /orders/{id}`, the response must include a `status` field that is one of these values" — using only the parts of the response the consumer actually uses.
2. **These consumer contracts are published somewhere the provider's CI can access them** — often a shared contract broker or repository.
3. **The provider's CI pipeline runs every published consumer contract against the real, current provider implementation** as part of its normal build — not against a mock, against the actual code being considered for release.
4. **A contract violation fails the provider's build**, exactly where and when the breaking change was introduced, with a clear indication of *which consumer* would be broken and *how*.
5. **Multiple consumers' contracts run independently and are all satisfied simultaneously** — the provider must remain compatible with every consumer's stated expectations at once, not just the one a developer happened to be thinking about when making a change.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two consumers publish contracts stating their expectations; the provider's CI runs both contracts against the real implementation and fails the build if either is violated">
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">order-service contract</text>

  <rect x="20" y="90" width="180" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="110" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">reporting-service contract</text>

  <rect x="280" y="55" width="180" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="370" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">contract broker</text>

  <rect x="530" y="55" width="120" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="590" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">provider CI</text>

  <line x1="200" y1="45" x2="280" y2="70" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="200" y1="115" x2="280" y2="90" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="460" y1="80" x2="530" y2="80" stroke="#6db33f" stroke-width="2" marker-end="url(#a1)"/>

  <text x="590" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">build FAILS if EITHER contract is violated</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

Every consumer's contract is checked against the real provider implementation as part of the provider's own build.

## 5. Runnable example

Scenario: two consumers with different, specific expectations of a shared provider, both verified against the same provider implementation. We start with a basic single-consumer contract check, extend it to two consumers verified independently, then handle the hard case: a provider change that satisfies one consumer's contract but breaks the other's, which must be caught precisely, attributing the failure to the specific consumer affected.

### Level 1 — Basic

```java
// File: SingleConsumerContract.java -- models ONE consumer's contract,
// verified against the REAL provider implementation.
import java.util.*;

public class SingleConsumerContract {
    // The REAL provider implementation.
    static Map<String, Object> providerGetOrder(String orderId) {
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("orderId", orderId);
        response.put("status", "SHIPPED");
        response.put("totalAmount", 79.50);
        return response;
    }

    // order-service's CONTRACT: what IT specifically depends on.
    static List<String> verifyOrderServiceContract(Map<String, Object> response) {
        List<String> violations = new ArrayList<>();
        if (!response.containsKey("orderId")) violations.add("order-service needs 'orderId'");
        if (!response.containsKey("status")) violations.add("order-service needs 'status'");
        return violations;
    }

    public static void main(String[] args) {
        Map<String, Object> response = providerGetOrder("42");
        List<String> violations = verifyOrderServiceContract(response);
        System.out.println("[contract check] order-service: " + (violations.isEmpty() ? "SATISFIED" : violations));
    }
}
```

How to run: `java SingleConsumerContract.java`

`verifyOrderServiceContract` checks the real provider's actual response against exactly what `order-service` declared it depends on — this is the fundamental mechanism: a contract check that runs against real provider output, not a hand-maintained mock, catching genuine drift.

### Level 2 — Intermediate

```java
// File: TwoConsumerContracts.java -- the SAME verification, now
// EXTENDED to TWO consumers, each with their OWN distinct contract,
// verified INDEPENDENTLY against the SAME real provider implementation.
import java.util.*;

public class TwoConsumerContracts {
    static Map<String, Object> providerGetOrder(String orderId) {
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("orderId", orderId);
        response.put("status", "SHIPPED");
        response.put("totalAmount", 79.50);
        response.put("customerEmail", "buyer@example.com");
        return response;
    }

    static List<String> verifyOrderServiceContract(Map<String, Object> response) {
        List<String> violations = new ArrayList<>();
        if (!response.containsKey("orderId")) violations.add("order-service needs 'orderId'");
        if (!response.containsKey("status")) violations.add("order-service needs 'status'");
        return violations;
    }

    // reporting-service has a DIFFERENT set of dependencies -- financial data, not status.
    static List<String> verifyReportingServiceContract(Map<String, Object> response) {
        List<String> violations = new ArrayList<>();
        if (!response.containsKey("orderId")) violations.add("reporting-service needs 'orderId'");
        if (!response.containsKey("totalAmount")) violations.add("reporting-service needs 'totalAmount'");
        return violations;
    }

    public static void main(String[] args) {
        Map<String, Object> response = providerGetOrder("42");

        List<String> orderServiceViolations = verifyOrderServiceContract(response);
        List<String> reportingServiceViolations = verifyReportingServiceContract(response);

        System.out.println("[contract check] order-service: " + (orderServiceViolations.isEmpty() ? "SATISFIED" : orderServiceViolations));
        System.out.println("[contract check] reporting-service: " + (reportingServiceViolations.isEmpty() ? "SATISFIED" : reportingServiceViolations));
    }
}
```

How to run: `java TwoConsumerContracts.java`

`verifyOrderServiceContract` and `verifyReportingServiceContract` check entirely different fields, reflecting each consumer's genuinely different dependency on the shared provider — both run independently against the exact same `response` object, and both are satisfied here, since the current provider implementation happens to include everything both consumers need.

### Level 3 — Advanced

```java
// File: ProviderChangeBreaksOneConsumer.java -- the SAME two-consumer
// verification, now handling the PRODUCTION-FLAVORED hard case: a
// provider developer makes a change (removing "totalAmount", which
// LOOKED unused from the provider's own code) that SATISFIES
// order-service's contract but BREAKS reporting-service's contract. This
// must be caught PRECISELY, attributed to the SPECIFIC affected consumer,
// failing the provider's build before this change ever ships.
import java.util.*;

public class ProviderChangeBreaksOneConsumer {
    // A developer "cleans up" the response, removing a field that LOOKS unused...
    static Map<String, Object> providerGetOrderAfterChange(String orderId) {
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("orderId", orderId);
        response.put("status", "SHIPPED");
        response.put("customerEmail", "buyer@example.com");
        // "totalAmount" REMOVED -- looked unused from the provider team's own perspective.
        return response;
    }

    static List<String> verifyOrderServiceContract(Map<String, Object> response) {
        List<String> violations = new ArrayList<>();
        if (!response.containsKey("orderId")) violations.add("order-service needs 'orderId'");
        if (!response.containsKey("status")) violations.add("order-service needs 'status'");
        return violations;
    }

    static List<String> verifyReportingServiceContract(Map<String, Object> response) {
        List<String> violations = new ArrayList<>();
        if (!response.containsKey("orderId")) violations.add("reporting-service needs 'orderId'");
        if (!response.containsKey("totalAmount")) violations.add("reporting-service needs 'totalAmount'");
        return violations;
    }

    public static void main(String[] args) {
        Map<String, Object> response = providerGetOrderAfterChange("42");

        List<String> orderServiceViolations = verifyOrderServiceContract(response);
        List<String> reportingServiceViolations = verifyReportingServiceContract(response);

        System.out.println("[CI] running ALL published consumer contracts against this build...");
        System.out.println("[contract check] order-service: " + (orderServiceViolations.isEmpty() ? "SATISFIED" : orderServiceViolations));
        System.out.println("[contract check] reporting-service: " + (reportingServiceViolations.isEmpty() ? "SATISFIED" : reportingServiceViolations));

        boolean anyViolations = !orderServiceViolations.isEmpty() || !reportingServiceViolations.isEmpty();
        if (anyViolations) {
            System.out.println("[CI] BUILD FAILED -- this change breaks at least one published consumer contract, blocking the release");
        } else {
            System.out.println("[CI] BUILD PASSED -- safe to release");
        }
    }
}
```

How to run: `java ProviderChangeBreaksOneConsumer.java`

`providerGetOrderAfterChange` no longer includes `totalAmount` in its response. `verifyOrderServiceContract` checks pass cleanly, since `order-service` never depended on that field — but `verifyReportingServiceContract`'s check for `totalAmount` fails, since it's now genuinely missing. The `anyViolations` check at the end catches this specific, precise failure and fails the whole CI build, even though one of the two consumers (the one a developer might have been focused on) was completely unaffected.

## 6. Walkthrough

Trace `ProviderChangeBreaksOneConsumer.main` in order. **First**, `providerGetOrderAfterChange("42")` runs and returns a response map containing `orderId`, `status`, and `customerEmail` — `totalAmount` is conspicuously absent, reflecting the developer's change.

**Next**, `verifyOrderServiceContract(response)` runs its two checks: `response.containsKey("orderId")` is `true`, and `response.containsKey("status")` is `true` — neither check adds a violation, so `orderServiceViolations` ends up empty.

**Then**, `verifyReportingServiceContract(response)` runs its own two checks: `response.containsKey("orderId")` is `true`, contributing no violation, but `response.containsKey("totalAmount")` is `false`, since that field was removed — this adds a specific violation message to `reportingServiceViolations`, naming exactly which consumer and exactly which field is affected.

**After that**, `main` prints both contract check results — `order-service` reporting `SATISFIED`, and `reporting-service` reporting its one specific violation — giving immediate, precise visibility into exactly which consumer is impacted by this change, rather than a vague "something broke" signal.

**Finally**, `anyViolations` evaluates `!orderServiceViolations.isEmpty() || !reportingServiceViolations.isEmpty()`, which is `false || true`, giving `true` overall — the build-failed branch runs, printing an explicit message that the change breaks a published consumer contract and blocking the release, exactly the safety net consumer-driven contracts are meant to provide: catching this specific incompatibility in the provider's own CI, before the change ever reaches production and actually breaks `reporting-service` for real.

```
[CI] running ALL published consumer contracts against this build...
[contract check] order-service: SATISFIED
[contract check] reporting-service: [reporting-service needs 'totalAmount']
[CI] BUILD FAILED -- this change breaks at least one published consumer contract, blocking the release
```

## 7. Gotchas & takeaways

> A field that "looks unused" from the provider team's own codebase and documentation is exactly the trap consumer-driven contracts exist to catch — the provider team has no visibility into every consumer's actual runtime dependency on a field unless that dependency is made explicit and checkable, which is precisely what a published consumer contract provides.
- The provider must run *every* published consumer's contract on *every* build, not just the ones a specific developer remembers to check — automation is what makes this reliable; manually remembering to check with every consumer team does not scale and will eventually be forgotten.
- This pairs directly with the [tolerant reader pattern](0496-tolerant-reader-pattern.md) — a consumer's contract should reflect exactly what its tolerant reader actually extracts, no more, keeping the provider's freedom to evolve everything else as wide as possible.
- Consumer-driven contracts catch *known, stated* dependencies — they don't replace the need for careful communication about genuinely new consumer needs or planned breaking changes; they specifically catch the case where an existing, previously-agreed dependency gets accidentally broken.
- The precision of the failure message matters enormously for this pattern's real-world value — a vague "some contract failed somewhere" is far less actionable than the specific "reporting-service needs 'totalAmount'" shown here, which tells a developer exactly what broke and for whom.
