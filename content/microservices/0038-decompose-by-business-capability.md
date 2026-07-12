---
card: microservices
gi: 38
slug: decompose-by-business-capability
title: Decompose by business capability
---

## 1. What it is

**Decomposing by business capability** is a specific, concrete technique for finding service boundaries: start from a **business capability model** — a structured list of what the business *does*, independent of any org chart or existing codebase (things like "Order Management," "Payment Processing," "Inventory Management," "Customer Support") — and create one service per capability. This differs from just picking boundaries intuitively: the capability model is typically produced by interviewing business stakeholders and documenting the business's own structure, then used as an input to the technical decomposition, rather than deriving boundaries purely from how the code or the org happens to already be organized.

## 2. Why & when

Business capabilities tend to be relatively stable over time, even as the specific features and implementation details built on top of them change constantly — "Order Management" as a capability existed before any particular checkout flow, and will likely still exist after that flow is redesigned five times. Anchoring service boundaries to capabilities, rather than to today's specific feature set or team structure, tends to produce boundaries that survive longer without needing to be redrawn.

Use business-capability decomposition as your starting technique when you have (or can build) a genuine capability model from business stakeholders — this works especially well for established organizations with a reasonably well-understood business structure. It's a less reliable starting point for a brand-new product where the "business capabilities" themselves are still being discovered (in which case [monolith-first](0027-monolith-first-strategy.md) is usually the safer path).

## 3. Core concept

The technique, concretely, in three steps:

1. **Build the capability model.** Interview business stakeholders and list what the business does, independent of current systems: "Manage orders," "Process payments," "Track inventory," "Handle returns."
2. **Map each capability to a candidate service.** Each capability becomes a first-draft service boundary: `OrderManagementService`, `PaymentProcessingService`, `InventoryManagementService`, `ReturnsService`.
3. **Refine using other signals.** Cross-check against data ownership, team structure, and change-frequency patterns — capabilities that always change together might actually be one service; a capability that's really two unrelated concerns bundled together might need splitting further.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A business capability model listing what the business does maps directly to candidate service boundaries">
  <rect x="30" y="30" width="220" height="110" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Capability model</text>
  <text x="140" y="70" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Manage orders</text>
  <text x="140" y="85" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Process payments</text>
  <text x="140" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Track inventory</text>
  <text x="140" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Handle returns</text>

  <rect x="390" y="30" width="220" height="110" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Candidate services</text>
  <text x="500" y="70" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">OrderManagementService</text>
  <text x="500" y="85" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">PaymentProcessingService</text>
  <text x="500" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">InventoryManagementService</text>
  <text x="500" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ReturnsService</text>

  <line x1="250" y1="85" x2="390" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a38)"/>
  <defs><marker id="a38" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each entry in the business capability model becomes a first-draft candidate service.

## 5. Runnable example

Scenario: modeling the capability-to-service mapping technique — first a raw capability list, then mapped to candidate services, then refined using data-ownership signals to merge or flag capabilities.

### Level 1 — Basic

```java
// File: CapabilityModel.java -- a raw business capability model, gathered
// from stakeholder interviews, INDEPENDENT of any current system structure.
import java.util.*;

public class CapabilityModel {
    public static void main(String[] args) {
        List<String> capabilities = List.of(
            "Manage orders", "Process payments", "Track inventory", "Handle returns"
        );
        System.out.println("Business capabilities identified:");
        for (String capability : capabilities) System.out.println("  - " + capability);
    }
}
```

**How to run:** `javac CapabilityModel.java && java CapabilityModel` (JDK 17+).

Expected output:
```
Business capabilities identified:
  - Manage orders
  - Process payments
  - Track inventory
  - Handle returns
```

This list comes purely from understanding what the business does — no code, team structure, or existing system was consulted to produce it.

### Level 2 — Intermediate

```java
// File: MapToServices.java -- mechanically map each capability to a
// candidate service name -- the FIRST DRAFT of the decomposition.
import java.util.*;

public class MapToServices {
    public static void main(String[] args) {
        List<String> capabilities = List.of("Manage orders", "Process payments", "Track inventory", "Handle returns");
        List<String> candidateServices = List.of("OrderManagementService", "PaymentProcessingService", "InventoryTrackingService", "ReturnsHandlingService");

        for (int i = 0; i < capabilities.size(); i++) {
            System.out.println(capabilities.get(i) + " -> " + candidateServices.get(i));
        }
    }
}
```

**How to run:** `javac MapToServices.java && java MapToServices` (JDK 17+).

Expected output:
```
Manage orders -> OrderManagementService
Process payments -> PaymentProcessingService
Track inventory -> InventoryTrackingService
Handle returns -> ReturnsHandlingService
```

Each capability now has a concrete, named candidate service — a first draft, ready for refinement against other signals like data ownership and change frequency.

### Level 3 — Advanced

```java
// File: RefineWithDataOwnership.java -- refine the FIRST DRAFT using a
// concrete signal: which capabilities read/write the SAME data, suggesting
// they might actually be one service, not two.
import java.util.*;

public class RefineWithDataOwnership {
    record Capability(String name, Set<String> dataEntitiesTouched) { }

    static Map<String, Set<String>> findSharedDataOwnership(List<Capability> capabilities) {
        Map<String, Set<String>> entityToCapabilities = new TreeMap<>();
        for (Capability c : capabilities) {
            for (String entity : c.dataEntitiesTouched()) {
                entityToCapabilities.computeIfAbsent(entity, k -> new TreeSet<>()).add(c.name());
            }
        }
        // keep only entities touched by MORE THAN ONE capability -- a signal worth investigating
        Map<String, Set<String>> shared = new TreeMap<>();
        for (var entry : entityToCapabilities.entrySet()) {
            if (entry.getValue().size() > 1) shared.put(entry.getKey(), entry.getValue());
        }
        return shared;
    }

    public static void main(String[] args) {
        List<Capability> capabilities = List.of(
            new Capability("Manage orders", Set.of("Order", "OrderLineItem")),
            new Capability("Process payments", Set.of("Payment", "Order")), // ALSO touches Order -- a signal
            new Capability("Track inventory", Set.of("StockLevel")),
            new Capability("Handle returns", Set.of("Return", "Order")) // ALSO touches Order
        );

        Map<String, Set<String>> sharedOwnership = findSharedDataOwnership(capabilities);
        System.out.println("Capabilities modeled: " + capabilities.size());
        System.out.println("Shared data entities requiring refinement:");
        for (var entry : sharedOwnership.entrySet()) {
            System.out.println("  " + entry.getKey() + " is touched by: " + entry.getValue() + " -- consider which capability should OWN it");
        }
    }
}
```

**How to run:** `javac RefineWithDataOwnership.java && java RefineWithDataOwnership` (JDK 17+).

Expected output:
```
Capabilities modeled: 4
Shared data entities requiring refinement:
  Order is touched by: [Handle returns, Manage orders, Process payments] -- consider which capability should OWN it
```

The production-flavored refinement step: `findSharedDataOwnership` reveals that three separate capabilities all touch the `Order` entity — a concrete, actionable signal that the initial four-way split needs a decision about which service actually *owns* `Order` data, with the other two capabilities accessing it only through that owning service's API (per [decentralized data management](0009-decentralized-data-management.md)), rather than each maintaining their own conflicting copy.

## 6. Walkthrough

1. `findSharedDataOwnership(capabilities)` iterates each `Capability` in the list, and for each `dataEntitiesTouched` entry, records that entity as touched by this capability's name inside `entityToCapabilities`, a map from entity name to the set of capability names touching it.
2. After the first loop, `entityToCapabilities` contains: `"Order" -> {Manage orders, Process payments, Handle returns}`, `"OrderLineItem" -> {Manage orders}`, `"Payment" -> {Process payments}`, `"StockLevel" -> {Track inventory}`, `"Return" -> {Handle returns}`.
3. The second loop filters this map down to only entries where more than one capability appears — `"Order"` is the only entity with 3 capabilities in its set, so it's the only entry copied into `shared`.
4. The final print shows that `Order` is touched by three of the four candidate services — a concrete, specific signal that this initial capability-based split needs refinement: does `Order` truly belong to `OrderManagementService`, with `PaymentProcessingService` and `ReturnsHandlingService` accessing it only via API calls, or does this reveal that these three capabilities are more entangled than the raw capability list suggested?
5. This is exactly the kind of concrete, data-driven refinement step that turns a first-draft capability mapping into a genuinely workable service decomposition — capability names alone aren't enough; checking what data each capability actually needs is what surfaces hidden coupling.

```
Manage orders    -> touches {Order, OrderLineItem}
Process payments -> touches {Payment, Order}       <- shares "Order"
Handle returns    -> touches {Return, Order}         <- shares "Order"
Track inventory   -> touches {StockLevel}            <- no overlap, clean boundary
        |
"Order" touched by 3 capabilities -> needs an explicit OWNERSHIP decision
```

## 7. Gotchas & takeaways

> **Gotcha:** a capability model gathered purely from stakeholder interviews can reflect how the business *talks about itself* rather than how data and processes actually flow — always cross-check the resulting candidate services against concrete signals (like shared data entities, as shown above, or team structure) rather than treating the initial capability list as a final answer.

- Decomposing by business capability starts from a capability model — what the business does, gathered independently of current systems — and maps each capability to a first-draft candidate service.
- Capabilities tend to be more stable over time than specific features or current team structure, which is why they're a good starting anchor for service boundaries.
- Always refine the initial mapping using concrete signals like shared data ownership — capabilities that turn out to touch the same core data entity are a strong signal they may need to be merged, or that one needs to clearly own that data while the others access it only through its API.
- This technique works best for organizations with an established, reasonably well-understood business structure; for a brand-new product still discovering its own capabilities, [monolith-first](0027-monolith-first-strategy.md) is usually the safer starting point.
