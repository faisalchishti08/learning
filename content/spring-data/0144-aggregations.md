---
card: spring-data
gi: 144
slug: aggregations
title: "Aggregations"
---

## 1. What it is

Elasticsearch **aggregations** compute summary statistics — counts, averages, grouped buckets — across the documents matching a query, computed server-side in the same request as the search itself, similar in purpose to the MongoDB aggregation framework covered earlier in this course but built specifically around Elasticsearch's search-and-analytics engine. `NativeQuery` (the earlier card) is how aggregations are attached to a search request in Spring Data Elasticsearch.

```java
NativeQuery query = NativeQuery.builder()
    .withAggregation("orders_by_status", Aggregation.of(a -> a
        .terms(t -> t.field("status"))))
    .build();

SearchHits<Order> hits = elasticsearchOperations.search(query, Order.class);
ElasticsearchAggregations aggregations = (ElasticsearchAggregations) hits.getAggregations();
```

## 2. Why & when

Every earlier card in this section returned individual matching documents. Often what's actually needed is a *summary* over many documents — "how many orders are in each status," "average order total per category" — and computing that by fetching every matching document into the application and summarizing in Java would be enormously wasteful for a large result set. Aggregations push that summarization down to where the data already lives, computing it across potentially millions of documents in one request.

Reach for aggregations when:

- You need counts, sums, or averages grouped by some field — a dashboard showing "orders by status," a facet count next to search filters ("Electronics (42), Books (17), ..."), or any "group and summarize" reporting need.
- You want the summary computed over the *entire* matching set, not just the page of results being displayed — aggregations run against every document matching the query, independent of pagination.
- Building faceted search UI, where each filter option needs to show how many results it would produce if selected — a classic aggregation use case.

## 3. Core concept

```
 Query: match everything

 terms aggregation on "status":
   { "buckets": [
       { "key": "SHIPPED",   "doc_count": 42 },
       { "key": "PENDING",   "doc_count": 17 },
       { "key": "DELIVERED", "doc_count": 8  }
   ]}

 -- computed over the ENTIRE matching set, in the SAME request as the search itself
 -- returns alongside the search hits, not as a separate query
```

Aggregations answer "how are the matching documents distributed" in the same request that answers "what are the matching documents" — one round trip for both.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single search request returns both individual search hits and a terms aggregation bucketing them by status">
  <rect x="20" y="20" width="220" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">search(query, Order.class)</text>

  <rect x="280" y="20" width="150" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="355" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">SearchHits (page)</text>

  <rect x="460" y="20" width="160" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="40" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Aggregations</text>
  <text x="540" y="54" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">(over ALL matches)</text>

  <line x1="240" y1="35" x2="275" y2="35" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="240" y1="50" x2="455" y2="50" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

One search request returns both a page of individual hits and aggregation results computed across the full matching set.

## 5. Runnable example

The scenario: summarizing order data, evolving from a basic terms aggregation (bucketing by status), to a metric aggregation (average total per bucket), to a nested aggregation combining both — grouping and computing a metric within each group in one pass.

### Level 1 — Basic

Model a `terms` aggregation: bucketing documents by a field's distinct values and counting each bucket.

```java
import java.util.*;
import java.util.stream.*;

public class AggregationsLevel1 {
    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "SHIPPED", 50.0),
            new Order("2", "SHIPPED", 150.0),
            new Order("3", "PENDING", 200.0),
            new Order("4", "DELIVERED", 75.0),
            new Order("5", "SHIPPED", 30.0)
        );

        // Mirrors: Aggregation.of(a -> a.terms(t -> t.field("status")))
        Map<String, Long> statusBuckets = termsAggregation(orders, o -> o.status);
        System.out.println("Orders by status (terms aggregation):");
        statusBuckets.forEach((status, count) -> System.out.println("  " + status + ": " + count));
    }

    static <T> Map<T, Long> termsAggregation(List<Order> orders, java.util.function.Function<Order, T> field) {
        return orders.stream().collect(Collectors.groupingBy(field, Collectors.counting()));
    }
}

class Order { String id; String status; double total; Order(String id, String status, double total) { this.id = id; this.status = status; this.total = total; } }
```

How to run: `java AggregationsLevel1.java`

`termsAggregation` groups orders by their `status` value and counts each group, mirroring exactly what an Elasticsearch `terms` aggregation on the `status` field returns: a bucket per distinct value with a `doc_count` for each. This computation happens over *all* five orders in one pass, regardless of how many (or few) would actually be shown on a results page.

### Level 2 — Intermediate

Compute a **metric** aggregation — average total — matching Elasticsearch's `avg` aggregation, applied globally across the whole matching set.

```java
import java.util.*;
import java.util.stream.*;

public class AggregationsLevel2 {
    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "SHIPPED", 50.0),
            new Order("2", "SHIPPED", 150.0),
            new Order("3", "PENDING", 200.0),
            new Order("4", "DELIVERED", 75.0),
            new Order("5", "SHIPPED", 30.0)
        );

        // Mirrors: Aggregation.of(a -> a.avg(avg -> avg.field("total")))
        double overallAverage = avgAggregation(orders);
        System.out.println("Average order total across ALL matching orders: " + overallAverage);

        // Mirrors: Aggregation.of(a -> a.max(max -> max.field("total")))
        double maxTotal = orders.stream().mapToDouble(o -> o.total).max().orElse(0);
        System.out.println("Max order total: " + maxTotal);
    }

    static double avgAggregation(List<Order> orders) {
        return orders.stream().mapToDouble(o -> o.total).average().orElse(0);
    }
}

class Order { String id; String status; double total; Order(String id, String status, double total) { this.id = id; this.status = status; this.total = total; } }
```

How to run: `java AggregationsLevel2.java`

`avgAggregation` computes the mean `total` across every order, mirroring an `avg` metric aggregation — like the `terms` aggregation in Level 1, this runs over the *entire* matching set at once, in the same request as the search, rather than requiring the application to fetch every document and average them client-side.

### Level 3 — Advanced

Combine both: a nested aggregation computing the average total **within each status bucket**, matching a real `terms` aggregation with a nested `avg` sub-aggregation — the compound pattern behind most real reporting dashboards.

```java
import java.util.*;
import java.util.stream.*;

public class AggregationsLevel3 {
    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("1", "SHIPPED", 50.0),
            new Order("2", "SHIPPED", 150.0),
            new Order("3", "PENDING", 200.0),
            new Order("4", "DELIVERED", 75.0),
            new Order("5", "SHIPPED", 30.0),
            new Order("6", "PENDING", 100.0)
        );

        // Mirrors: Aggregation.of(a -> a.terms(t -> t.field("status")).aggregations("avg_total", sub -> sub.avg(avg -> avg.field("total"))))
        Map<String, DoubleSummaryStatistics> byStatus = nestedAggregation(orders);

        System.out.println("Orders by status, with average total PER bucket:");
        byStatus.forEach((status, stats) ->
            System.out.println("  " + status + ": count=" + stats.getCount() + ", avgTotal=" + stats.getAverage()));
    }

    static Map<String, DoubleSummaryStatistics> nestedAggregation(List<Order> orders) {
        return orders.stream().collect(
            Collectors.groupingBy(o -> o.status, Collectors.summarizingDouble(o -> o.total)));
    }
}

class Order { String id; String status; double total; Order(String id, String status, double total) { this.id = id; this.status = status; this.total = total; } }
```

How to run: `java AggregationsLevel3.java`

`nestedAggregation` groups orders by `status` (the outer `terms` aggregation), and for each group computes a `DoubleSummaryStatistics` capturing count and average `total` (standing in for a nested `avg` sub-aggregation within each bucket). This mirrors a single Elasticsearch request that returns "for each status, both how many orders and their average total" in one pass — a nested aggregation, not two separate queries.

## 6. Walkthrough

Execution starts in `main` for Level 3. Six orders are defined with statuses `SHIPPED` (×3), `PENDING` (×2), `DELIVERED` (×1).

`nestedAggregation(orders)` calls `Collectors.groupingBy(o -> o.status, Collectors.summarizingDouble(o -> o.total))`. This is a two-level collector: the outer `groupingBy` partitions orders into buckets keyed by `status`, and for each bucket, the inner `summarizingDouble` collector computes count, sum, min, max, and average over that bucket's `total` values — exactly the "group, then summarize within each group" shape of a `terms` aggregation with a nested `avg` sub-aggregation.

For the `SHIPPED` bucket, orders `1` (`50.0`), `2` (`150.0`), and `5` (`30.0`) are grouped together; their average is `(50 + 150 + 30) / 3 = 76.67`. For the `PENDING` bucket, orders `3` (`200.0`) and `6` (`100.0`) average to `150.0`. For the `DELIVERED` bucket, only order `4` (`75.0`) is present, so its average is simply `75.0`.

```
Orders by status, with average total PER bucket:
  SHIPPED: count=3, avgTotal=76.66666666666667
  PENDING: count=2, avgTotal=150.0
  DELIVERED: count=1, avgTotal=75.0
```

In real Spring Data Elasticsearch, this is expressed as a `terms` aggregation on `status` with a nested `avg` sub-aggregation on `total`, attached to a `NativeQuery` via `withAggregation(...)`, and the response comes back as a single `Aggregations` object containing, for each status bucket, both a document count and the nested average — all computed by Elasticsearch across every matching document in one request, which is dramatically more efficient than fetching every document into the application and computing this breakdown in Java, especially once the matching set grows into the millions.

## 7. Gotchas & takeaways

> Gotcha: a `terms` aggregation on a `text`-mapped field (rather than `keyword`) buckets by individual *tokens*, not whole field values — aggregating on an unanalyzed `description` field would produce buckets like `"wireless"`, `"mouse"`, `"keyboard"` (individual words) rather than whole descriptions, which is almost never what's intended. This is the same `text`-vs-`keyword` mapping distinction from the earlier document-mapping card, showing up again here.

> Gotcha: by default, a `terms` aggregation only returns a limited number of the top buckets (ranked by document count), not necessarily every distinct value — for a field with many distinct values (like a free-form tag field), some legitimate values may be silently missing from the results unless the aggregation's size is configured appropriately.

- Aggregations compute summary statistics (counts, averages, groupings) across the *entire* set of documents matching a query, in the same request as the search itself.
- `terms` aggregations bucket documents by a field's distinct values; metric aggregations (`avg`, `sum`, `max`, `min`) compute a single number, either globally or nested within buckets.
- Nested aggregations (a metric computed within each `terms` bucket) answer "grouped summary" questions — like average total per status — in one request rather than one query per group.
- `terms` aggregations require a `keyword`-mapped (not `text`-mapped) field to bucket by whole values rather than individual analyzed tokens.
