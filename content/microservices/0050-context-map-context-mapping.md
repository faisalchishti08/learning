---
card: microservices
gi: 50
slug: context-map-context-mapping
title: "Context map & context mapping"
---

## 1. What it is

A **context map** is a single artifact — a diagram or, just as usefully, a structured document — that shows every bounded context in a system and, critically, the specific relationship pattern (Shared Kernel, Customer-Supplier, Conformist, Anticorruption Layer, Open Host Service) connecting each pair that depends on one another. **Context mapping** is the activity of producing and maintaining that artifact: identifying every context, and for each dependency between two contexts, explicitly naming which relationship pattern actually governs it, rather than leaving that relationship implicit and undocumented.

## 2. Why & when

Without an explicit context map, the relationships between bounded contexts tend to exist only informally — in individual engineers' heads, inconsistently applied, and invisible to anyone new joining the team or trying to understand the system's structure at a glance. A context map makes those relationships an explicit, shared, reviewable artifact: it becomes possible to ask "is this really a Conformist relationship, or has it quietly become something messier over time?" and to spot, at a glance, contexts with too many dependencies (a sign of excessive coupling) or relationships that were never deliberately chosen.

Produce and maintain a context map whenever a system has more than a couple of bounded contexts with real dependencies between them — treat it as a living document, updated whenever a new context is added or an existing relationship's pattern changes, not a one-time diagram drawn once and forgotten.

## 3. Core concept

A context map is fundamentally a graph: contexts as nodes, relationships as labeled edges.

```
OrdersContext --[Customer-Supplier]--> InventoryContext
OrdersContext --[Conformist]---------> PaymentGatewayContext (third-party, no negotiation power)
OrdersContext --[Shared Kernel]------> BillingContext (jointly-owned Money value object)
CatalogContext --[Anticorruption Layer]--> LegacyProductSystem
```

Each edge answers: which context depends on which, and specifically how is that dependency managed?

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A context map shows contexts as nodes and their relationships, labeled by pattern, as edges between them">
  <rect x="30" y="30" width="120" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="57" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrdersContext</text>

  <rect x="250" y="30" width="130" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="315" y="57" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">InventoryContext</text>

  <rect x="250" y="110" width="150" height="45" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="325" y="137" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">PaymentGatewayContext</text>

  <rect x="480" y="30" width="130" height="45" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="545" y="57" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">BillingContext</text>

  <line x1="150" y1="50" x2="250" y2="50" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a50)"/>
  <text x="200" y="42" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Customer-Supplier</text>

  <line x1="130" y1="75" x2="280" y2="110" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a50)"/>
  <text x="170" y="100" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Conformist</text>

  <line x1="150" y1="45" x2="480" y2="50" stroke="#8b949e" stroke-width="1.5"/>
  <text x="400" y="35" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Shared Kernel</text>
  <defs><marker id="a50" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Every edge on a real context map names both the direction of dependency and the specific relationship pattern governing it.

## 5. Runnable example

Scenario: building and querying a context map programmatically — first as a flat list of relationships, then queryable for problem signals, then used to flag a context with excessive, undifferentiated dependencies.

### Level 1 — Basic

```java
// File: BasicContextMap.java -- a context map as a simple list of labeled relationships
import java.util.*;

public class BasicContextMap {
    record Relationship(String from, String to, String pattern) { }

    public static void main(String[] args) {
        List<Relationship> contextMap = List.of(
            new Relationship("OrdersContext", "InventoryContext", "Customer-Supplier"),
            new Relationship("OrdersContext", "PaymentGatewayContext", "Conformist"),
            new Relationship("OrdersContext", "BillingContext", "Shared Kernel"),
            new Relationship("CatalogContext", "LegacyProductSystem", "Anticorruption Layer")
        );

        for (Relationship r : contextMap) {
            System.out.println(r.from() + " --[" + r.pattern() + "]--> " + r.to());
        }
    }
}
```

**How to run:** `javac BasicContextMap.java && java BasicContextMap` (JDK 17+).

Expected output:
```
OrdersContext --[Customer-Supplier]--> InventoryContext
OrdersContext --[Conformist]--> PaymentGatewayContext
OrdersContext --[Shared Kernel]--> BillingContext
CatalogContext --[Anticorruption Layer]--> LegacyProductSystem
```

Every dependency in the system is now an explicit, named entry — not an implicit assumption living only in individual engineers' heads.

### Level 2 — Intermediate

```java
// File: QueryableContextMap.java -- query the map for a SPECIFIC context's
// dependencies and dependents.
import java.util.*;
import java.util.stream.*;

public class QueryableContextMap {
    record Relationship(String from, String to, String pattern) { }

    static List<Relationship> contextMap = List.of(
        new Relationship("OrdersContext", "InventoryContext", "Customer-Supplier"),
        new Relationship("OrdersContext", "PaymentGatewayContext", "Conformist"),
        new Relationship("OrdersContext", "BillingContext", "Shared Kernel"),
        new Relationship("CatalogContext", "LegacyProductSystem", "Anticorruption Layer")
    );

    static List<Relationship> dependenciesOf(String context) {
        return contextMap.stream().filter(r -> r.from().equals(context)).collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Relationship> ordersDependencies = dependenciesOf("OrdersContext");
        System.out.println("OrdersContext depends on " + ordersDependencies.size() + " other context(s):");
        for (Relationship r : ordersDependencies) System.out.println("  " + r.to() + " via " + r.pattern());
    }
}
```

**How to run:** `javac QueryableContextMap.java && java QueryableContextMap` (JDK 17+).

Expected output:
```
OrdersContext depends on 3 other context(s):
  InventoryContext via Customer-Supplier
  PaymentGatewayContext via Conformist
  BillingContext via Shared Kernel
```

`dependenciesOf` turns the map into an actionable query — instantly answering "what does OrdersContext depend on, and how?" without needing to search through scattered documentation or ask around the team.

### Level 3 — Advanced

```java
// File: FlagExcessiveCoupling.java -- use the context map to AUTOMATICALLY
// flag a context with too many dependencies, a concrete coupling signal.
import java.util.*;
import java.util.stream.*;

public class FlagExcessiveCoupling {
    record Relationship(String from, String to, String pattern) { }

    static List<Relationship> contextMap = List.of(
        new Relationship("OrdersContext", "InventoryContext", "Customer-Supplier"),
        new Relationship("OrdersContext", "PaymentGatewayContext", "Conformist"),
        new Relationship("OrdersContext", "BillingContext", "Shared Kernel"),
        new Relationship("OrdersContext", "NotificationContext", "Open Host Service"),
        new Relationship("OrdersContext", "AnalyticsContext", "Conformist"),
        new Relationship("CatalogContext", "LegacyProductSystem", "Anticorruption Layer")
    );

    static Map<String, Long> dependencyCountByContext() {
        return contextMap.stream().collect(Collectors.groupingBy(Relationship::from, Collectors.counting()));
    }

    public static void main(String[] args) {
        int threshold = 4;
        Map<String, Long> counts = dependencyCountByContext();
        System.out.println("Dependency counts per context:");
        for (var entry : counts.entrySet()) {
            System.out.println("  " + entry.getKey() + ": " + entry.getValue());
        }

        System.out.println("Contexts exceeding the healthy threshold of " + threshold + " dependencies:");
        for (var entry : counts.entrySet()) {
            if (entry.getValue() > threshold) {
                System.out.println("  FLAGGED: " + entry.getKey() + " has " + entry.getValue() + " dependencies -- review for excessive coupling");
            }
        }
    }
}
```

**How to run:** `javac FlagExcessiveCoupling.java && java FlagExcessiveCoupling` (JDK 17+).

Expected output:
```
Dependency counts per context:
  OrdersContext: 5
  CatalogContext: 1
Contexts exceeding the healthy threshold of 4 dependencies:
  FLAGGED: OrdersContext has 5 dependencies -- review for excessive coupling
```

The production-flavored payoff: `dependencyCountByContext` groups the raw relationship list and counts entries per source context, turning a subjective feeling ("OrdersContext seems to depend on a lot of things") into a concrete number. `OrdersContext`'s 5 dependencies exceed the chosen threshold of 4, flagging it automatically as worth reviewing — perhaps some of its capabilities should be reconsidered, or some relationships consolidated, rather than continuing to accumulate dependencies unnoticed.

## 6. Walkthrough

1. `dependencyCountByContext()` calls `contextMap.stream().collect(Collectors.groupingBy(Relationship::from, Collectors.counting()))` — this groups every `Relationship` by its `from()` field (the dependent context) and counts how many relationships share each group.
2. `OrdersContext` appears as the `from()` value in 5 of the 6 entries in `contextMap` (Inventory, PaymentGateway, Billing, Notification, Analytics), so its count is `5`. `CatalogContext` appears in exactly 1 entry, so its count is `1`.
3. The first loop prints both counts directly, giving a full, at-a-glance picture of every context's outgoing dependency count.
4. The second loop iterates the same `counts` map again, this time checking `entry.getValue() > threshold` (`4`). Only `OrdersContext`'s count of `5` exceeds `4`, so it's the only entry that triggers the `FLAGGED` message; `CatalogContext`'s count of `1` does not.
5. This concrete, automatable check is exactly the kind of ongoing value a maintained context map provides beyond just documentation — it can be re-run as the system evolves, catching a context's dependency count creeping upward before it becomes a genuinely unmanageable [god service](0047-avoiding-god-services-too-coarse-grained.md)-style coupling problem.

```
contextMap grouped by 'from':
  OrdersContext:  [Inventory, PaymentGateway, Billing, Notification, Analytics] -> count 5 -> FLAGGED (> 4)
  CatalogContext: [LegacyProductSystem]                                        -> count 1 -> OK
```

## 7. Gotchas & takeaways

> **Gotcha:** a context map is only useful if it's kept current — a stale context map that no longer reflects reality is worse than no map at all, since it actively misleads anyone relying on it. Treat updating the context map as part of the definition of "done" whenever a context's dependencies or relationship patterns change, not a separate, optional documentation task.

- A context map is an explicit artifact listing every bounded context and the specific relationship pattern governing each dependency between them, rather than leaving those relationships implicit and undocumented.
- Making the map queryable and structured (not just a static picture) lets it answer concrete questions directly — what does context X depend on, and how — rather than requiring manual searching or asking around the team.
- A context map can be used as an ongoing, automatable health check: flagging contexts with an excessive or fast-growing number of dependencies is a concrete, measurable coupling signal worth investigating.
- Keep the map current as a discipline tied to any change in a context's dependencies — a stale map is actively misleading, not merely unhelpful.
