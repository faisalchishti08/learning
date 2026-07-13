---
card: microservices
gi: 314
slug: cqrs-read-models-materialized-views
title: "CQRS read models / materialized views"
---

## 1. What it is

A CQRS read model (also called a materialized view in this context) is a pre-built, denormalized data structure maintained specifically to answer one particular kind of query as fast and simply as possible — typically a straightforward lookup by key, with no joins, no aggregation, and no computation needed at read time, because all of that work was already done when the read model was built or updated. A single system commonly maintains several different read models simultaneously, each shaped for a different query pattern, all derived from the same underlying source(s) of truth on the command side.

## 2. Why & when

The core idea in [CQRS](0313-command-query-responsibility-segregation-cqrs.md) is separating write and read models; a read model is the concrete artifact that separation produces on the read side. Rather than computing a display-ready shape from normalized source data on every single read (as [API composition](0312-api-composition-pattern.md) does at request time, or as a naive shared-model system does with repeated joins), a read model does that computation once, ahead of time, and stores the *result* — so a read becomes a trivial, fast lookup instead of repeated work.

Use a dedicated read model when a specific query pattern is hit frequently enough that doing its underlying joins/aggregation on every read is a genuine performance concern, or when the data needed spans multiple services and synchronous [API composition](0312-api-composition-pattern.md) per request is too slow or too fragile (too many services in the critical path). It's common and often correct to maintain several different read models for the same underlying data, each shaped for a specific screen or query — a "customer order history" read model shaped very differently from an "admin analytics dashboard" read model, even though both ultimately derive from the same order data.

## 3. Core concept

A read model is populated and kept current by consuming events from the command side (see [keeping read models in sync via events](0315-keeping-read-models-in-sync-via-events.md)); reads against it are simple, direct lookups with no runtime joining.

```java
// The READ MODEL: pre-joined, pre-formatted, purpose-built for ONE query pattern.
@Entity
class OrderHistoryReadModel {
    @Id String orderId;
    String customerName;      // DENORMALIZED from CustomerService
    String productSummary;    // DENORMALIZED, pre-formatted from OrderService + ProductService
    LocalDateTime placedAt;
}

// The QUERY: a trivial lookup, no joins, no per-request assembly.
@Service
class OrderHistoryQueryService {
    List<OrderHistoryReadModel> getOrderHistory(String customerId) {
        return orderHistoryRepository.findByCustomerId(customerId); // ONE simple query, already denormalized
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same underlying order data feeds two differently shaped read models built ahead of time for two different query patterns: a customer-facing order history view and an admin analytics dashboard, each optimized purely for its own specific read pattern, so both reads are simple, fast lookups with no runtime joining">
  <rect x="30" y="60" width="160" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="80" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Command-side source data</text>
  <text x="110" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(orders, customers, products)</text>

  <line x1="190" y1="70" x2="330" y2="35" stroke="#8b949e" marker-end="url(#arr314)"/>
  <line x1="190" y1="95" x2="330" y2="130" stroke="#8b949e" marker-end="url(#arr314)"/>

  <rect x="340" y="15" width="230" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="455" y="33" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Order History read model</text>
  <text x="455" y="48" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">shaped for: customer-facing history page</text>

  <rect x="340" y="110" width="230" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="455" y="128" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Analytics Dashboard read model</text>
  <text x="455" y="143" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">shaped for: admin aggregation queries</text>

  <defs><marker id="arr314" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The same source data feeds multiple, differently-shaped read models, each purpose-built for its own specific query pattern.

## 5. Runnable example

Scenario: a single generic query method forced to reshape raw data differently for two different callers on every call, extended to two dedicated read models pre-built for each caller's specific need, and finally showing how the read models can diverge structurally far beyond what a single generic shape could ever efficiently serve — one flat and denormalized for display, one pre-aggregated for analytics.

### Level 1 — Basic

```java
// File: OneGenericQueryReshapedRepeatedly.java -- ONE generic method
// returns raw order data; EVERY caller has to reshape it themselves,
// repeating the SAME transformation work independently.
import java.util.*;

public class OneGenericQueryReshapedRepeatedly {
    record RawOrder(String id, String customerId, double totalCents, String status) {}

    static List<RawOrder> rawOrders = List.of(
            new RawOrder("order-1", "cust-1", 4999, "SHIPPED"),
            new RawOrder("order-2", "cust-1", 2999, "PLACED"),
            new RawOrder("order-3", "cust-2", 9999, "SHIPPED")
    );

    // Caller 1: customer-facing history page reshapes it its own way.
    static List<String> buildCustomerHistoryDisplay(String customerId) {
        List<String> lines = new ArrayList<>();
        for (RawOrder o : rawOrders) if (o.customerId().equals(customerId))
            lines.add("Order " + o.id() + ": $" + (o.totalCents() / 100) + " (" + o.status() + ")");
        return lines;
    }

    // Caller 2: admin dashboard ALSO has to reshape the SAME raw data, independently.
    static double buildTotalRevenueForShippedOrders() {
        double total = 0;
        for (RawOrder o : rawOrders) if (o.status().equals("SHIPPED")) total += o.totalCents();
        return total / 100;
    }

    public static void main(String[] args) {
        System.out.println("Customer history: " + buildCustomerHistoryDisplay("cust-1"));
        System.out.println("Total shipped revenue: $" + buildTotalRevenueForShippedOrders()
                + " -- BOTH callers independently scan and reshape the SAME raw data, every single call.");
    }
}
```

How to run: `java OneGenericQueryReshapedRepeatedly.java`

Both `buildCustomerHistoryDisplay` and `buildTotalRevenueForShippedOrders` independently scan the same `rawOrders` list and reshape it for their own purposes, every time they're called — no shared, pre-built structure exists for either specific need, so both do their own full scan-and-transform work on every call.

### Level 2 — Intermediate

```java
// File: TwoDedicatedReadModels.java -- TWO separate read models are
// built AHEAD of time, each shaped EXACTLY for its own query pattern;
// reads become trivial lookups, no scanning or reshaping at read time.
import java.util.*;

public class TwoDedicatedReadModels {
    record RawOrder(String id, String customerId, double totalCents, String status) {}
    static List<RawOrder> rawOrders = List.of(
            new RawOrder("order-1", "cust-1", 4999, "SHIPPED"),
            new RawOrder("order-2", "cust-1", 2999, "PLACED"),
            new RawOrder("order-3", "cust-2", 9999, "SHIPPED")
    );

    // READ MODEL 1: pre-built, keyed by customer, ready-to-display strings.
    static Map<String, List<String>> customerHistoryReadModel = new HashMap<>();
    // READ MODEL 2: pre-aggregated total, a SINGLE number, always current.
    static double shippedRevenueReadModel = 0;

    static void rebuildReadModels() {
        customerHistoryReadModel.clear();
        shippedRevenueReadModel = 0;
        for (RawOrder o : rawOrders) {
            customerHistoryReadModel
                    .computeIfAbsent(o.customerId(), k -> new ArrayList<>())
                    .add("Order " + o.id() + ": $" + (o.totalCents() / 100) + " (" + o.status() + ")");
            if (o.status().equals("SHIPPED")) shippedRevenueReadModel += o.totalCents() / 100;
        }
    }

    public static void main(String[] args) {
        rebuildReadModels(); // in a real system, this happens incrementally, per event -- see next level

        // BOTH reads are now TRIVIAL lookups -- no scanning, no reshaping.
        System.out.println("Customer history (trivial lookup): " + customerHistoryReadModel.get("cust-1"));
        System.out.println("Total shipped revenue (trivial lookup): $" + shippedRevenueReadModel);
    }
}
```

How to run: `java TwoDedicatedReadModels.java`

`customerHistoryReadModel` and `shippedRevenueReadModel` are built once by `rebuildReadModels` (standing in for an incremental, event-driven update in a real system), each shaped exactly for its own consumer. Reading either one afterward is a direct map lookup or field access — no scanning, no per-call transformation — regardless of how large `rawOrders` might grow.

### Level 3 — Advanced

```java
// File: DivergentReadModelShapes.java -- shows the read models diverging
// FAR beyond what one generic query shape could serve well: one becomes
// a flat, per-customer LIST for display; the other becomes a fully
// PRE-AGGREGATED breakdown by status AND by day, something that would be
// expensive to compute on every read from raw data, but is essentially
// free to read once maintained incrementally.
import java.util.*;
import java.time.LocalDate;

public class DivergentReadModelShapes {
    record RawOrder(String id, String customerId, double totalCents, String status, LocalDate placedOn) {}
    static List<RawOrder> rawOrders = List.of(
            new RawOrder("order-1", "cust-1", 4999, "SHIPPED", LocalDate.of(2026, 7, 1)),
            new RawOrder("order-2", "cust-1", 2999, "PLACED", LocalDate.of(2026, 7, 1)),
            new RawOrder("order-3", "cust-2", 9999, "SHIPPED", LocalDate.of(2026, 7, 2))
    );

    // Read model A: flat, per-customer DISPLAY strings.
    record CustomerHistoryEntry(String display) {}
    static Map<String, List<CustomerHistoryEntry>> customerHistoryReadModel = new HashMap<>();

    // Read model B: DEEPLY pre-aggregated -- revenue by (status, day), a
    // multi-dimensional breakdown that would be an expensive GROUP BY
    // computed live, but is a trivial lookup once pre-aggregated.
    record StatusDayKey(String status, LocalDate day) {}
    static Map<StatusDayKey, Double> revenueByStatusAndDayReadModel = new HashMap<>();

    static void applyOrder(RawOrder o) {
        customerHistoryReadModel.computeIfAbsent(o.customerId(), k -> new ArrayList<>())
                .add(new CustomerHistoryEntry("Order " + o.id() + ": $" + (o.totalCents() / 100)));

        StatusDayKey key = new StatusDayKey(o.status(), o.placedOn());
        revenueByStatusAndDayReadModel.merge(key, o.totalCents() / 100, Double::sum);
    }

    public static void main(String[] args) {
        for (RawOrder o : rawOrders) applyOrder(o); // incremental, ONE order at a time, as events would arrive

        System.out.println("Read model A (flat, per-customer display): " + customerHistoryReadModel.get("cust-1"));
        System.out.println("Read model B (deeply pre-aggregated, by status+day):");
        revenueByStatusAndDayReadModel.forEach((key, revenue) ->
                System.out.println("  " + key.status() + " on " + key.day() + ": $" + revenue));
        System.out.println("Both are TRIVIAL lookups now, despite representing very DIFFERENT shapes of the SAME underlying order data.");
    }
}
```

How to run: `java DivergentReadModelShapes.java`

`applyOrder` is called once per order, incrementally — exactly mirroring how a real read model is updated one event at a time as orders are placed, rather than rebuilt from scratch. `customerHistoryReadModel` stays a flat list of display strings per customer. `revenueByStatusAndDayReadModel`, in contrast, becomes a genuinely multi-dimensional aggregate — revenue broken down by both status *and* day simultaneously, using `merge` to incrementally accumulate sums as each order is processed. Reading either read model afterward is a trivial, direct lookup, even though `revenueByStatusAndDayReadModel` represents a computation (`GROUP BY status, day, SUM(total)`) that would be comparatively expensive to run live against raw data on every single read — this is the concrete value of maintaining it as a materialized, incrementally-updated view instead.

## 6. Walkthrough

Trace `DivergentReadModelShapes.main`'s processing of the three orders in order. **Order 1** (`"order-1"`, customer `"cust-1"`, `$49.99`, `"SHIPPED"`, `2026-07-01`): `applyOrder` first appends a `CustomerHistoryEntry` to `customerHistoryReadModel.get("cust-1")` (creating the list via `computeIfAbsent` since this is the first order for this customer). It then computes `key = StatusDayKey("SHIPPED", 2026-07-01)` and calls `revenueByStatusAndDayReadModel.merge(key, 49.99, Double::sum)` — since this key doesn't exist yet, `merge` simply inserts `49.99` as its initial value.

**Order 2** (`"order-2"`, customer `"cust-1"`, `$29.99`, `"PLACED"`, `2026-07-01`): a second entry is appended to `customerHistoryReadModel.get("cust-1")`, now holding two entries. A *different* key, `StatusDayKey("PLACED", 2026-07-01)`, is computed (different status than order 1, same day) — since this key is also new, `merge` inserts `29.99` as its value; the `"SHIPPED"`/`2026-07-01` entry from order 1 is untouched.

**Order 3** (`"order-3"`, customer `"cust-2"`, `$99.99`, `"SHIPPED"`, `2026-07-02`): a new entry list is created for `"cust-2"` (a different customer, via `computeIfAbsent` again). The key `StatusDayKey("SHIPPED", 2026-07-02)` is computed — different day than order 1's `SHIPPED` entry, so this is also a new key, and `merge` inserts `99.99`.

**After all three orders are applied**, `revenueByStatusAndDayReadModel` holds exactly three distinct entries: `("SHIPPED", 2026-07-01) -> 49.99`, `("PLACED", 2026-07-01) -> 29.99`, `("SHIPPED", 2026-07-02) -> 99.99` — note that no two orders shared an identical `(status, day)` combination in this dataset, so every `merge` call was effectively an insert rather than an accumulation; had a fourth `SHIPPED` order also landed on `2026-07-01`, its total would have been *added* to the existing `49.99` via the `Double::sum` merge function, incrementally growing that specific aggregate.

**Reading either read model afterward** (as the final `System.out.println` calls do) is then a direct, already-computed lookup — `customerHistoryReadModel.get("cust-1")` and iterating `revenueByStatusAndDayReadModel`'s entries both retrieve already-assembled results, with none of the grouping, filtering, or summing logic re-executed at read time.

```
applyOrder(order-1: SHIPPED, 07-01, $49.99) -> history[cust-1] += entry; revenueByStatusDay[SHIPPED,07-01] = 49.99 (new)
applyOrder(order-2: PLACED,  07-01, $29.99) -> history[cust-1] += entry; revenueByStatusDay[PLACED, 07-01] = 29.99 (new)
applyOrder(order-3: SHIPPED, 07-02, $99.99) -> history[cust-2] += entry; revenueByStatusDay[SHIPPED,07-02] = 99.99 (new)
                                    (a 4th SHIPPED/07-01 order would instead ADD to the existing 49.99)
```

## 7. Gotchas & takeaways

> A read model that tries to be generically useful for many different query patterns at once tends to converge back toward the original, un-denormalized shape — the whole value of a read model comes from shaping it deliberately and narrowly for one specific, known query pattern; resist the urge to make it "flexible" at the cost of the performance benefit that narrow shaping provides.

- A read model's entire purpose is doing the expensive work (joining, filtering, aggregating) once, ahead of time, so that reads become trivial, fast lookups — this is the direct payoff of accepting CQRS's added complexity.
- It's normal and often correct to maintain multiple differently-shaped read models derived from the same underlying source data, each purpose-built for one specific query pattern, rather than trying to serve every read from one shared shape.
- Read models are always derived, never authoritative — the actual [system of record](0311-data-ownership-system-of-record.md) remains on the command side; a read model can always in principle be rebuilt from scratch by replaying the source events, which is a valuable property for recovering from bugs in the read-model-building logic itself.
- See [keeping read models in sync via events](0315-keeping-read-models-in-sync-via-events.md) for the mechanics of how a read model is incrementally updated as new events arrive, rather than rebuilt from scratch on every change.
