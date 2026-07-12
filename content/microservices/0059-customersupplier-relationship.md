---
card: microservices
gi: 59
slug: customersupplier-relationship
title: "Customer–supplier relationship"
---

## 1. What it is

A **Customer-Supplier** relationship between two bounded contexts is an upstream/downstream dependency where the upstream team (the "supplier") genuinely takes the downstream team's (the "customer's") needs into account when planning their own roadmap — the downstream team has real influence, even a seat at the planning table, even though they don't own the upstream context's code. This is distinct from [Conformist](0060-conformist-relationship.md), where the downstream has no such influence and simply accepts whatever the upstream provides.

## 2. Why & when

A Customer-Supplier relationship works when both contexts are within the same organization (or a close, cooperative partnership) and the upstream team has both the willingness and the practical ability to prioritize the downstream's needs alongside their own. In practice, this often means the downstream team can request specific API changes, get them scheduled into the upstream's roadmap, and have automated tests (supplied by the downstream, run as part of the upstream's own build) that catch breaking changes before they ship — a concrete, collaborative mechanism rather than an informal request process.

Establish a Customer-Supplier relationship when the downstream context's needs are significant enough, and the organizational relationship close enough, to justify this level of coordination. When the upstream context is a third party with no reason to prioritize your specific needs (a public API, a widely-used external service), a genuine Customer-Supplier relationship generally isn't achievable — you're more likely dealing with a Conformist relationship whether you'd prefer that or not.

## 3. Core concept

The defining mechanism, made concrete: the downstream team supplies automated tests that express their actual needs from the upstream API, and those tests run as part of the upstream team's own build — a breaking change fails the upstream's own CI before it ever ships, giving the downstream team real, structural influence without needing to own the upstream code directly.

```
DownstreamTeam supplies:  "OrderStatusTests" (expresses exactly what DownstreamTeam needs from the API)
        |
UpstreamTeam's build:     compile -> unit tests -> "OrderStatusTests" (from DownstreamTeam) -> deploy
                                                            |
                                            a breaking change FAILS the upstream's OWN build
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The downstream customer supplies tests that run inside the upstream supplier's own build pipeline, giving the downstream real structural influence over changes">
  <rect x="30" y="60" width="150" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Downstream (Customer)</text>

  <rect x="450" y="60" width="150" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="525" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Upstream (Supplier)</text>

  <rect x="240" y="30" width="170" height="110" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="325" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Upstream's own build:</text>
  <text x="325" y="75" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">compile</text>
  <text x="325" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">supplier's own tests</text>
  <text x="325" y="105" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">CUSTOMER'S tests (supplied)</text>
  <text x="325" y="120" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">deploy</text>

  <line x1="180" y1="85" x2="240" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a59)"/>
  <line x1="410" y1="85" x2="450" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a59)"/>
  <defs><marker id="a59" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Downstream-supplied tests run inside the upstream's own build, giving downstream real, automated influence.

## 5. Runnable example

Scenario: an `InventoryService` (supplier) with an API `OrderService` (customer) depends on, first with no protective mechanism, then with customer-supplied tests running against the supplier's own build, catching a breaking change before it ships.

### Level 1 — Basic

```java
// File: NoProtection.java -- InventoryService's API, no mechanism ensuring
// OrderService's needs are considered before a change ships.
public class NoProtection {
    static class InventoryService {
        int getStockLevel(String item) { return 5; } // OrderService's ENTIRE dependency on this API
    }

    public static void main(String[] args) {
        InventoryService inventory = new InventoryService();
        System.out.println("stock level: " + inventory.getStockLevel("widget"));
    }
}
```

**How to run:** `javac NoProtection.java && java NoProtection` (JDK 17+).

Expected output:
```
stock level: 5
```

Nothing here would catch `InventoryTeam` accidentally changing `getStockLevel`'s behavior (say, returning `-1` for out-of-stock instead of `0`) before it ships and breaks `OrderService` in production.

### Level 2 — Intermediate

```java
// File: CustomerSuppliedTests.java -- DownstreamTeam (OrderService) supplies
// tests expressing THEIR needs; these run against UpstreamTeam's own code.
public class CustomerSuppliedTests {
    static class InventoryService { // UpstreamTeam's code
        int getStockLevel(String item) {
            if (item.equals("widget")) return 5;
            return 0; // out of stock represented as 0, NOT -1 -- a contract OrderService depends on
        }
    }

    // SUPPLIED BY DownstreamTeam (OrderService), run as part of UpstreamTeam's OWN build
    static void orderServiceContractTests(InventoryService inventory) {
        assertEqual("known item returns positive stock", inventory.getStockLevel("widget") > 0, true);
        assertEqual("unknown item returns ZERO, not negative", inventory.getStockLevel("unknown-item") >= 0, true);
        System.out.println("All customer-supplied contract tests PASSED");
    }

    static void assertEqual(String description, boolean actual, boolean expected) {
        if (actual != expected) throw new AssertionError("FAILED: " + description);
    }

    public static void main(String[] args) {
        InventoryService inventory = new InventoryService();
        orderServiceContractTests(inventory); // runs as part of InventoryTeam's OWN build pipeline
    }
}
```

**How to run:** `javac CustomerSuppliedTests.java && java CustomerSuppliedTests` (JDK 17+).

Expected output:
```
All customer-supplied contract tests PASSED
```

`orderServiceContractTests`, written by `OrderService`'s team, expresses exactly what they actually need from `InventoryService`'s API. Running it against `InventoryTeam`'s own code gives `OrderService` real, structural influence — without `OrderService`'s team owning or modifying `InventoryService`'s code directly.

### Level 3 — Advanced

```java
// File: BreakingChangeCaught.java -- InventoryTeam makes a change that
// WOULD have broken OrderService; the customer-supplied test CATCHES it
// in InventoryTeam's OWN build, before it ever ships.
public class BreakingChangeCaught {
    static class InventoryServiceV2 { // InventoryTeam's proposed NEW version
        int getStockLevel(String item) {
            if (item.equals("widget")) return 5;
            return -1; // CHANGED: -1 now means "unknown item" -- seemed reasonable to InventoryTeam in isolation
        }
    }

    // the SAME customer-supplied contract tests from Level 2, UNCHANGED
    static void orderServiceContractTests(InventoryServiceV2 inventory) {
        assertEqual("known item returns positive stock", inventory.getStockLevel("widget") > 0, true);
        assertEqual("unknown item returns ZERO or more, not negative", inventory.getStockLevel("unknown-item") >= 0, true);
    }

    static void assertEqual(String description, boolean actual, boolean expected) {
        if (actual != expected) throw new AssertionError("CONTRACT VIOLATION: " + description);
    }

    public static void main(String[] args) {
        InventoryServiceV2 inventory = new InventoryServiceV2();
        try {
            orderServiceContractTests(inventory); // runs in InventoryTeam's OWN build, BEFORE deploy
            System.out.println("Tests passed -- safe to deploy");
        } catch (AssertionError e) {
            System.out.println("BUILD FAILED: " + e.getMessage());
            System.out.println("InventoryTeam catches this BEFORE deploying, thanks to OrderService's supplied tests");
        }
    }
}
```

**How to run:** `javac BreakingChangeCaught.java && java BreakingChangeCaught` (JDK 17+).

Expected output:
```
BUILD FAILED: CONTRACT VIOLATION: unknown item returns ZERO or more, not negative
InventoryTeam catches this BEFORE deploying, thanks to OrderService's supplied tests
```

The production-flavored payoff: `InventoryTeam`'s proposed change (returning `-1` for unknown items) would have broken `OrderService`'s assumption that stock levels are never negative — but because `OrderService`'s contract test runs as part of `InventoryTeam`'s own build, the violation is caught immediately, in `InventoryTeam`'s own CI, before the change ever reaches production. This is the concrete mechanism that makes a Customer-Supplier relationship more than just a polite agreement — it's structurally enforced.

## 6. Walkthrough

1. `orderServiceContractTests(inventory)` is called with the new `InventoryServiceV2` instance, inside a `try` block.
2. The first assertion, `inventory.getStockLevel("widget") > 0`, evaluates `5 > 0`, which is `true`, matching the expected `true` — this assertion passes without incident.
3. The second assertion, `inventory.getStockLevel("unknown-item") >= 0`, calls `getStockLevel` with an item that isn't `"widget"`, hitting the `return -1` branch. The expression `-1 >= 0` evaluates to `false`, which does *not* match the expected `true` — `assertEqual` detects this mismatch and throws `AssertionError` with the message `"CONTRACT VIOLATION: unknown item returns ZERO or more, not negative"`.
4. Because this throw happens inside `orderServiceContractTests`, which was called inside `main`'s `try` block, control jumps immediately to the `catch (AssertionError e)` block, printing the failure message and the explanatory note.
5. In a real CI pipeline, this exact failure would halt `InventoryTeam`'s build — the `-1` change to `getStockLevel` would never be deployed, because `OrderService`'s supplied contract test caught the violation automatically, without requiring any manual cross-team review to happen first.

```
InventoryServiceV2.getStockLevel("unknown-item") -> returns -1 (InventoryTeam's proposed change)
        |
OrderService's contract test: -1 >= 0 ?  -> FALSE -> AssertionError thrown
        |
InventoryTeam's OWN build FAILS -- change never ships, OrderService never sees the broken behavior
```

## 7. Gotchas & takeaways

> **Gotcha:** a Customer-Supplier relationship requires the upstream team to genuinely value and maintain the downstream-supplied tests over time — if `InventoryTeam` starts treating `OrderService`'s contract tests as an annoyance to work around (deleting or skipping them under deadline pressure) rather than a meaningful safety net, the relationship has effectively degraded back into an unprotected dependency, no better than [Conformist](0060-conformist-relationship.md) without even the honesty of acknowledging that's what it's become.

- A Customer-Supplier relationship gives the downstream context genuine influence over the upstream's roadmap and changes, in contrast to a Conformist relationship where the downstream has no such influence.
- The concrete, structural mechanism is customer-supplied tests running as part of the supplier's own build — a breaking change fails the supplier's own CI, rather than relying purely on informal communication or manual review.
- This relationship requires an organizational context where the upstream team both can and will prioritize the downstream's needs — it's generally not achievable with a third-party or public API with no reason to accommodate any one specific consumer.
- The relationship only stays healthy as long as the upstream team genuinely maintains and respects the downstream-supplied tests — treating them as disposable under pressure quietly degrades the relationship back into an unprotected dependency.
