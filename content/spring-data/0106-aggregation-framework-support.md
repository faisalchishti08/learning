---
card: spring-data
gi: 106
slug: aggregation-framework-support
title: "Aggregation framework support"
---

## 1. What it is

MongoDB's aggregation framework processes documents through a **pipeline** of stages (`$match`, `$group`, `$sort`, `$project`, `$lookup`, ...), each transforming the documents flowing through it — Spring Data MongoDB's `Aggregation` class builds these pipelines as composable Java objects, and `mongoTemplate.aggregate(aggregation, ...)` executes them, returning computed results no simple `find` query could produce.

```java
Aggregation aggregation = Aggregation.newAggregation(
    Aggregation.match(Criteria.where("status").is("SHIPPED")),
    Aggregation.group("customerId").sum("total").as("totalSpent"),
    Aggregation.sort(Sort.Direction.DESC, "totalSpent")
);
AggregationResults<CustomerSpending> results = mongoTemplate.aggregate(aggregation, "orders", CustomerSpending.class);
```

## 2. Why & when

Everything covered so far — derived queries, `@Query`, `Criteria`/`Query` — filters and shapes individual documents, but none of it *computes* across documents the way a relational `GROUP BY`/`JOIN`/window function does (echoing the JPA/JDBC sections' aggregate-query and window-function cards). MongoDB's aggregation pipeline is the document-store equivalent: a sequence of stages, each one transforming the stream of documents flowing through it, ending in a computed result.

Reach for the aggregation framework specifically when:

- You need computed, grouped results — totals, counts, or averages per group — the MongoDB equivalent of a SQL `GROUP BY` with aggregate functions.
- You need to reshape documents (rename/compute/drop fields) as part of producing a report, not just filter which documents come back — `$project` handles this.
- You need to combine data from two collections (MongoDB's rough equivalent of a join) — `$lookup` performs this, though with different tradeoffs than a relational join, since MongoDB is not optimized for cross-collection joins the way a relational database is.

## 3. Core concept

```
 Aggregation.newAggregation(
     Aggregation.match(...),         -- STAGE 1: filter documents, like a WHERE clause
     Aggregation.group("customerId").sum("total").as("totalSpent"),  -- STAGE 2: group + compute
     Aggregation.sort(...)            -- STAGE 3: order the grouped results
 )

 Documents flow through EACH stage in order:
   raw orders --match--> filtered orders --group--> {customerId, totalSpent} --sort--> final results
```

Each stage transforms the stream of documents flowing through the pipeline; the final stage's output is what the aggregation returns.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Documents flow through match, group, and sort stages in sequence, each transforming the data before the next stage">
  <rect x="20" y="45" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="67" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">$match</text>
  <text x="90" y="82" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">filter documents</text>

  <rect x="250" y="45" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="67" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">$group</text>
  <text x="320" y="82" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">group + sum(total)</text>

  <rect x="480" y="45" width="140" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="550" y="67" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">$sort</text>
  <text x="550" y="82" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">order by totalSpent</text>

  <line x1="160" y1="70" x2="245" y2="70" stroke="#8b949e" stroke-width="1.3" marker-end="url(#ag)"/>
  <line x1="390" y1="70" x2="475" y2="70" stroke="#8b949e" stroke-width="1.3" marker-end="url(#ag)"/>
  <defs><marker id="ag" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each pipeline stage's output becomes the next stage's input, building up the final computed result step by step.

## 5. Runnable example

The scenario: computing total spending per customer, evolving from a plain filter, to a filter-then-group pipeline, to a full match-group-sort pipeline matching the concept section's example exactly.

### Level 1 — Basic

Model a single `$match`-equivalent stage, standing in for the simplest possible pipeline (one stage, just filtering).

```java
import java.util.*;
import java.util.stream.*;

class Order { String customerId; String status; double total; Order(String customerId, String status, double total) { this.customerId = customerId; this.status = status; this.total = total; } }

public class AggregationLevel1 {
    // Aggregation.newAggregation(Aggregation.match(Criteria.where("status").is("SHIPPED")))
    static List<Order> matchStage(List<Order> orders, String status) {
        return orders.stream().filter(o -> o.status.equals(status)).collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("cust-A", "SHIPPED", 50), new Order("cust-A", "PENDING", 30), new Order("cust-B", "SHIPPED", 100)
        );
        List<Order> shipped = matchStage(orders, "SHIPPED");
        System.out.println("After $match stage: " + shipped.size() + " document(s)");
    }
}
```

How to run: `java AggregationLevel1.java`

`matchStage` mirrors `Aggregation.match(...)` — the simplest possible pipeline stage, filtering documents exactly like a regular `find` query would, before any grouping or computation happens.

### Level 2 — Intermediate

Add a `$group`-equivalent stage that sums `total` per `customerId`, chaining it after the `$match` stage.

```java
import java.util.*;
import java.util.stream.*;

class Order { String customerId; String status; double total; Order(String customerId, String status, double total) { this.customerId = customerId; this.status = status; this.total = total; } }
record CustomerSpending(String customerId, double totalSpent) {}

public class AggregationLevel2 {
    static List<Order> matchStage(List<Order> orders, String status) {
        return orders.stream().filter(o -> o.status.equals(status)).collect(Collectors.toList());
    }

    // Aggregation.group("customerId").sum("total").as("totalSpent")
    static List<CustomerSpending> groupStage(List<Order> orders) {
        Map<String, Double> sums = orders.stream()
            .collect(Collectors.groupingBy(o -> o.customerId, Collectors.summingDouble(o -> o.total)));
        return sums.entrySet().stream()
            .map(e -> new CustomerSpending(e.getKey(), e.getValue()))
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("cust-A", "SHIPPED", 50), new Order("cust-A", "SHIPPED", 75),
            new Order("cust-A", "PENDING", 30), new Order("cust-B", "SHIPPED", 100)
        );

        List<Order> matched = matchStage(orders, "SHIPPED"); // stage 1
        List<CustomerSpending> grouped = groupStage(matched); // stage 2, chained after stage 1

        for (CustomerSpending cs : grouped) System.out.println(cs.customerId() + ": totalSpent=" + cs.totalSpent());
    }
}
```

How to run: `java AggregationLevel2.java`

`groupStage`'s input is `matched`'s *output* — exactly the pipeline-chaining behavior of a real `Aggregation`: documents pass from one stage to the next, and `cust-A`'s `totalSpent` correctly reflects only their two `SHIPPED` orders (`50 + 75 = 125`), since the `PENDING` order was already filtered out by the `$match` stage before grouping ever happened.

### Level 3 — Advanced

Add a `$sort`-equivalent final stage, completing the full three-stage pipeline from the concept section, and print the results in the computed order.

```java
import java.util.*;
import java.util.stream.*;

class Order { String customerId; String status; double total; Order(String customerId, String status, double total) { this.customerId = customerId; this.status = status; this.total = total; } }
record CustomerSpending(String customerId, double totalSpent) {}

public class AggregationLevel3 {
    static List<Order> matchStage(List<Order> orders, String status) {
        return orders.stream().filter(o -> o.status.equals(status)).collect(Collectors.toList());
    }

    static List<CustomerSpending> groupStage(List<Order> orders) {
        Map<String, Double> sums = orders.stream()
            .collect(Collectors.groupingBy(o -> o.customerId, Collectors.summingDouble(o -> o.total)));
        return sums.entrySet().stream().map(e -> new CustomerSpending(e.getKey(), e.getValue())).collect(Collectors.toList());
    }

    // Aggregation.sort(Sort.Direction.DESC, "totalSpent")
    static List<CustomerSpending> sortStage(List<CustomerSpending> grouped) {
        return grouped.stream()
            .sorted(Comparator.comparingDouble(CustomerSpending::totalSpent).reversed())
            .collect(Collectors.toList());
    }

    // Full pipeline, composed exactly like Aggregation.newAggregation(match, group, sort).
    static List<CustomerSpending> runPipeline(List<Order> orders, String status) {
        List<Order> matched = matchStage(orders, status);
        List<CustomerSpending> grouped = groupStage(matched);
        return sortStage(grouped);
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("cust-A", "SHIPPED", 50), new Order("cust-A", "SHIPPED", 75),
            new Order("cust-B", "SHIPPED", 300), new Order("cust-C", "SHIPPED", 20),
            new Order("cust-B", "PENDING", 999) // excluded by $match -- must not affect cust-B's total
        );

        List<CustomerSpending> results = runPipeline(orders, "SHIPPED");
        System.out.println("Customer spending, highest first:");
        for (CustomerSpending cs : results) System.out.println("  " + cs.customerId() + ": " + cs.totalSpent());
    }
}
```

How to run: `java AggregationLevel3.java`

`runPipeline` chains all three stages exactly like `Aggregation.newAggregation(match, group, sort)` would — `cust-B`'s huge `PENDING` order (`999`) never enters the pipeline at all (filtered out by `$match` before grouping), so `cust-B`'s computed `totalSpent` is correctly `300`, not `1299`; the final sorted output shows `cust-B` (300) first, then `cust-A` (125), then `cust-C` (20).

## 6. Walkthrough

Execution starts in `main` for Level 3. First, five orders are built across three customers, including one `PENDING` order for `cust-B` with a deliberately large total (`999`) to verify it gets correctly excluded.

`runPipeline(orders, "SHIPPED")` runs. First, `matchStage(orders, "SHIPPED")` filters the five orders down to four — every order except `cust-B`'s `PENDING` one. This is the pipeline's `$match` stage output, which becomes the next stage's input.

Next, `groupStage(matched)` runs on those four filtered orders: `Collectors.groupingBy(o -> o.customerId, Collectors.summingDouble(o -> o.total))` groups them by customer and sums each group's totals — `cust-A`'s two orders (`50 + 75`) sum to `125`; `cust-B`'s one remaining order (the `PENDING` one is gone) is `300`; `cust-C`'s one order is `20`. This produces three `CustomerSpending` records, in whatever order the underlying map iteration happens to produce.

Finally, `sortStage(grouped)` sorts these three records descending by `totalSpent`: `cust-B` (`300`) first, `cust-A` (`125`) second, `cust-C` (`20`) third. The loop in `main` prints this final, sorted order.

```
matchStage(orders, "SHIPPED"):  5 orders -> 4 (cust-B's PENDING 999 order excluded)
groupStage(matched):             cust-A: 50+75=125,  cust-B: 300,  cust-C: 20
sortStage(grouped):               [cust-B:300, cust-A:125, cust-C:20]  (descending by totalSpent)
```

In a real Spring Data MongoDB application, `mongoTemplate.aggregate(Aggregation.newAggregation(match, group, sort), "orders", CustomerSpending.class)` sends the entire three-stage pipeline to MongoDB as a single `aggregate` command — MongoDB executes all three stages server-side, in sequence, without ever transferring intermediate results back to the application; only the final stage's output (the sorted, grouped totals) crosses the network, which is both far more efficient than fetching every raw order and computing sums in application code, and exactly what this example's chained Java methods simulate in simplified form.

## 7. Gotchas & takeaways

> Gotcha: stage order genuinely matters and changes both correctness and performance — putting `$match` *after* `$group` (instead of before, as this example does) would force MongoDB to group every document first and only filter afterward, discarding the performance benefit of filtering down the working set before the more expensive grouping computation runs, and potentially producing wrong aggregate values if the filter was meant to exclude documents from a sum.

- The aggregation framework processes documents through a pipeline of stages, each transforming the data flowing through it — the document-store equivalent of a relational `GROUP BY`/computed-report query.
- `Aggregation.match(...)` filters (like a `WHERE`/`find` condition); `Aggregation.group(...).sum(...)` groups and computes; `Aggregation.sort(...)` orders the final results.
- Stage order matters for both correctness and performance — filter early (`$match` first) to shrink the working set before expensive grouping/computation stages run.
- The whole pipeline executes server-side in MongoDB — only the final stage's output crosses the network back to the application, unlike fetching raw documents and computing aggregates in application code.
