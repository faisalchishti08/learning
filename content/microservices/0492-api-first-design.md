---
card: microservices
gi: 492
slug: api-first-design
title: "API-first design"
---

## 1. What it is

**API-first design** means designing and agreeing on a service's API contract — its endpoints, request/response shapes, and behavior — **before** writing the implementation, rather than letting the API emerge as an afterthought of whatever the implementation happens to produce. The contract becomes the first artifact of the work, reviewed and agreed upon by both the API's producer and its consumers, with implementation following from it.

## 2. Why & when

You design API-first specifically when a service has real consumers — other teams, other services — who need to build against a stable, agreed-upon interface:

- **Consumer teams can start building against the contract immediately, in parallel with the provider's implementation.** If the API shape is agreed and documented first, a consuming team can write and test their integration against a mock generated from that contract, without waiting for the real service to be finished.
- **Designing the API in isolation, focused purely on what the interface *should* look like, produces better interfaces than designing it as a byproduct of implementation convenience.** An API that emerges from "whatever fields my internal data model happens to have" often leaks implementation details that make no sense to a consumer and are painful to change later.
- **A documented, agreed contract becomes the basis for automated verification** — [consumer-driven contract tests](0497-consumer-driven-contracts.md) and API validation tooling need a concrete contract artifact ([OpenAPI/Swagger](0493-api-contracts-openapi-swagger.md)) to check against, which API-first design naturally produces.
- **You use this approach for any service with external or cross-team consumers** — for a purely internal, single-team service with no other consumers, the ceremony of full API-first design may be more process than the situation actually needs.

## 3. Core concept

Think of an architect creating detailed blueprints and getting them approved by the client before any construction begins, versus a crew starting to build immediately and figuring out the layout as they go — the blueprint-first approach lets the client (and other stakeholders like electricians and plumbers) plan their own work against an agreed, stable design, while build-first construction risks costly rework every time the "design" changes because someone discovers, mid-build, that a wall needs to move.

Concretely, an API-first workflow looks like:

1. **Draft the API contract** — endpoints, methods, request/response schemas, status codes — typically as an [OpenAPI specification](0493-api-contracts-openapi-swagger.md), before writing implementation code.
2. **Review the contract with consumers** — the teams who will actually call this API weigh in on whether the shape meets their needs, catching mismatches while they're still just a document edit, not a code change.
3. **Generate scaffolding and mocks from the agreed contract** — server-side interface stubs for the provider to implement against, and a mock server consumers can integrate against immediately, both derived automatically from the same source of truth.
4. **Implement against the contract, not the other way around** — the provider's implementation must conform to what was agreed, rather than the contract being reverse-engineered from whatever the implementation happened to produce.
5. **The contract remains the source of truth going forward** — changes to the API start as contract changes, reviewed the same way, before any implementation changes follow.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The API contract is drafted and agreed first; the provider's implementation and the consumer's integration both proceed from that same agreed contract, in parallel">
  <rect x="240" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">agreed API contract</text>

  <rect x="40" y="120" width="220" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="145" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">provider implements against it</text>

  <rect x="400" y="120" width="220" height="55" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="510" y="145" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">consumer builds against a mock of it</text>

  <line x1="290" y1="70" x2="160" y2="120" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="370" y1="70" x2="500" y2="120" stroke="#8b949e" marker-end="url(#a1)"/>

  <text x="330" y="180" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">both sides work IN PARALLEL, from the SAME agreed contract</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

The contract is agreed first; provider and consumer then build in parallel against that same shared artifact.

## 5. Runnable example

Scenario: a contract-first workflow where the API shape is defined once and used to validate both a mock consumer integration and the real provider implementation. We start with a basic contract definition and mock-based consumer usage, extend it to validating the real implementation against that same contract, then handle the hard case: catching a provider implementation that has drifted from the agreed contract, which must be flagged clearly rather than silently shipped.

### Level 1 — Basic

```java
// File: ApiContractBasic.java -- models DEFINING an API contract FIRST,
// then a CONSUMER building against a MOCK derived from it, all before any
// real implementation exists.
import java.util.*;

public class ApiContractBasic {
    // The AGREED contract: field names and types, defined BEFORE implementation.
    record OrderResponseContract(String orderId, String status, double totalAmount) {}

    // A MOCK server, generated conceptually FROM the contract -- consumer builds against THIS.
    static OrderResponseContract mockGetOrder(String orderId) {
        return new OrderResponseContract(orderId, "PENDING", 49.99);
    }

    // The CONSUMER, integrating against the mock -- written BEFORE the real service exists.
    static void consumerIntegration() {
        OrderResponseContract mockResponse = mockGetOrder("order-42");
        System.out.println("[consumer] built against contract, received mock: " + mockResponse);
    }

    public static void main(String[] args) {
        System.out.println("[contract] agreed shape: orderId, status, totalAmount");
        consumerIntegration();
    }
}
```

How to run: `java ApiContractBasic.java`

`OrderResponseContract` is the agreed shape, defined once. `mockGetOrder` stands in for a mock server generated from that contract, and `consumerIntegration` builds against it — none of this requires the real provider implementation to exist yet, demonstrating the parallel-work benefit of designing the contract first.

### Level 2 — Intermediate

```java
// File: ApiContractValidation.java -- the SAME contract, now used to
// VALIDATE that the REAL provider implementation actually conforms to it
// -- the contract isn't just documentation, it's a checkable artifact.
import java.util.*;

public class ApiContractValidation {
    record OrderResponseContract(String orderId, String status, double totalAmount) {}

    // The REAL implementation, built to conform to the contract.
    static OrderResponseContract realGetOrder(String orderId) {
        return new OrderResponseContract(orderId, "SHIPPED", 79.50);
    }

    static List<String> validateAgainstContract(OrderResponseContract response) {
        List<String> violations = new ArrayList<>();
        if (response.orderId() == null || response.orderId().isEmpty()) {
            violations.add("orderId must not be empty");
        }
        Set<String> validStatuses = Set.of("PENDING", "SHIPPED", "DELIVERED", "CANCELLED");
        if (!validStatuses.contains(response.status())) {
            violations.add("status '" + response.status() + "' is not one of the contract's allowed values");
        }
        if (response.totalAmount() < 0) {
            violations.add("totalAmount must not be negative");
        }
        return violations;
    }

    public static void main(String[] args) {
        OrderResponseContract response = realGetOrder("order-42");
        List<String> violations = validateAgainstContract(response);
        System.out.println("[validation] real response: " + response);
        System.out.println("[validation] contract violations: " + (violations.isEmpty() ? "none -- CONFORMS" : violations));
    }
}
```

How to run: `java ApiContractValidation.java`

`validateAgainstContract` checks the real implementation's actual response against the rules the contract establishes — a non-empty `orderId`, a `status` from the agreed set of values, a non-negative `totalAmount`. This run's response conforms to all three rules, so `violations` comes back empty, confirming the real implementation genuinely matches what was agreed.

### Level 3 — Advanced

```java
// File: ApiContractDriftDetection.java -- the SAME validation, now
// handling the PRODUCTION-FLAVORED hard case: the REAL implementation has
// DRIFTED from the agreed contract (a developer added a status value the
// contract never agreed to, and returned a negative amount due to a
// refund-calculation bug). This drift MUST be caught and reported
// clearly, not silently shipped to consumers who built against the
// original agreed contract.
import java.util.*;

public class ApiContractDriftDetection {
    record OrderResponseContract(String orderId, String status, double totalAmount) {}

    // The contract's agreed rules -- established BEFORE this implementation existed.
    static final Set<String> AGREED_STATUS_VALUES = Set.of("PENDING", "SHIPPED", "DELIVERED", "CANCELLED");

    // The REAL implementation has DRIFTED: a new status was added without updating the contract,
    // and a refund calculation bug produces a negative amount.
    static OrderResponseContract driftedRealImplementation(String orderId) {
        return new OrderResponseContract(orderId, "AWAITING_MANUAL_REVIEW", -15.00);
    }

    static List<String> validateAgainstContract(OrderResponseContract response) {
        List<String> violations = new ArrayList<>();
        if (response.orderId() == null || response.orderId().isEmpty()) {
            violations.add("orderId must not be empty");
        }
        if (!AGREED_STATUS_VALUES.contains(response.status())) {
            violations.add("status '" + response.status() + "' is NOT in the agreed contract's allowed values "
                    + AGREED_STATUS_VALUES + " -- this is a BREAKING, UNAGREED change");
        }
        if (response.totalAmount() < 0) {
            violations.add("totalAmount is negative (" + response.totalAmount() + ") -- violates the contract's non-negative rule, likely an implementation bug");
        }
        return violations;
    }

    public static void main(String[] args) {
        OrderResponseContract response = driftedRealImplementation("order-99");
        List<String> violations = validateAgainstContract(response);

        System.out.println("[validation] real response: " + response);
        if (violations.isEmpty()) {
            System.out.println("[validation] CONFORMS to contract");
        } else {
            System.out.println("[validation] CONTRACT DRIFT DETECTED -- " + violations.size() + " violation(s):");
            for (String violation : violations) {
                System.out.println("  - " + violation);
            }
            System.out.println("[validation] BLOCKING deploy until this drift is resolved -- consumers built against the ORIGINAL agreed contract");
        }
    }
}
```

How to run: `java ApiContractDriftDetection.java`

`driftedRealImplementation` returns `"AWAITING_MANUAL_REVIEW"` as its status — a value never part of `AGREED_STATUS_VALUES` — and a negative `totalAmount` of `-15.00`. `validateAgainstContract` runs the identical rules from Level 2 against this drifted response: the status check fails since the returned value isn't in the agreed set, and the amount check fails since it's negative — both violations are collected and reported with specific, actionable detail, rather than the drifted implementation silently shipping to consumers who built their integration against the original, agreed contract.

## 6. Walkthrough

Trace `ApiContractDriftDetection.main` in order. **First**, `driftedRealImplementation("order-99")` runs and returns an `OrderResponseContract` with `status = "AWAITING_MANUAL_REVIEW"` and `totalAmount = -15.00` — values that diverge from what the contract originally agreed to, representing undocumented drift introduced during implementation.

**Next**, `validateAgainstContract(response)` runs its three checks in order. The `orderId` check passes, since `"order-99"` is non-empty. The status check runs `!AGREED_STATUS_VALUES.contains("AWAITING_MANUAL_REVIEW")`, which is `true` since that value was never part of the agreed set — a detailed violation message is added to `violations`, explicitly calling out that this is a breaking, unagreed change.

**Then**, the `totalAmount` check runs `response.totalAmount() < 0`, which is `true` since `-15.00` is negative — a second violation is added, specifically noting this likely stems from an implementation bug rather than an intentional contract change.

**After that**, `validateAgainstContract` returns `violations` containing exactly these two entries, and back in `main`, the `if (violations.isEmpty())` check is `false`, so the drift-detected branch runs instead of the conforms branch.

**Finally**, `main` prints each violation individually with a clear `-` prefix, then prints an explicit statement that the deploy should be blocked until the drift is resolved — directly modeling how API-first design's real value shows up not just at initial design time, but continuously: the agreed contract remains a checkable artifact that can catch real implementation drift before it ever reaches consumers who built against the original agreement.

```
[validation] real response: OrderResponseContract[orderId=order-99, status=AWAITING_MANUAL_REVIEW, totalAmount=-15.0]
[validation] CONTRACT DRIFT DETECTED -- 2 violation(s):
  - status 'AWAITING_MANUAL_REVIEW' is NOT in the agreed contract's allowed values [PENDING, SHIPPED, DELIVERED, CANCELLED] -- this is a BREAKING, UNAGREED change
  - totalAmount is negative (-15.0) -- violates the contract's non-negative rule, likely an implementation bug
[validation] BLOCKING deploy until this drift is resolved -- consumers built against the ORIGINAL agreed contract
```

## 7. Gotchas & takeaways

> Treating the API contract as a one-time design document, checked only at the start of a project and never validated against again, lets exactly the kind of drift shown in Level 3 slip through unnoticed — the contract's real, ongoing value comes from continuously validating real behavior against it, not from writing it once and filing it away.
- Adding a genuinely new status value or field is often a legitimate need — but it should go through the same contract-review process the original design did, not silently appear in an implementation and reach consumers as an unannounced surprise.
- [OpenAPI/Swagger](0493-api-contracts-openapi-swagger.md) specifications make this validation automatable — contract-testing tools can check real API responses against a formal specification exactly like `validateAgainstContract` does here, but generated from and kept in sync with the actual document.
- API-first design pairs naturally with [consumer-driven contracts](0497-consumer-driven-contracts.md) — the initial agreed contract is the starting point, and consumer-driven contract tests are the ongoing mechanism that keeps the provider honest about it over time.
- The upfront cost of API-first design (a review cycle before any code is written) pays for itself specifically when there are real, separate consumers who'd otherwise be blocked waiting on the provider's implementation, or blindsided by unannounced changes to an API they depend on.
