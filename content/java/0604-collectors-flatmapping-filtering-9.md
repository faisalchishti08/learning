---
card: java
gi: 604
slug: collectors-flatmapping-filtering-9
title: Collectors.flatMapping / filtering (9)
---

## 1. What it is

Java 9 added two new static methods to `java.util.stream.Collectors`: `flatMapping` and `filtering`. These are **downstream collectors** — they are not terminal operations but composable collectors meant to be passed as the second argument to grouping collectors like `groupingBy` or `partitioningBy`. `Collectors.filtering(predicate, downstream)` filters stream elements before passing them to the downstream collector, applying the filter *after* the grouping key is determined. `Collectors.flatMapping(mapper, downstream)` maps each element to a stream and flattens the results before passing them to the downstream collector. Both enable multi-step aggregation in a single `groupingBy` call, eliminating the need for intermediate `filter`/`flatMap` stages on each group.

## 2. Why & when

Before Java 9, filtering inside a `groupingBy` was awkward. If you wanted to group orders by customer but only include orders above a certain value, you had to pre-filter the stream — which meant the groups for customers with no qualifying orders would be absent from the map entirely, rather than appearing as empty groups. Similarly, if each element mapped to multiple derived values (e.g. each order contained multiple items and you wanted items grouped by category), you needed a separate `flatMap` before the grouping, which collapsed the element-to-group relationship. `filtering` and `flatMapping` solve both problems by embedding the filter or flatten inside the collector itself, applied per-group after the grouping logic runs — giving you control over what goes into each group's bucket without losing groups that end up empty.

## 3. Core concept

```java
// Group orders by customer, but only include orders > $100
Map<String, List<Order>> bigOrdersByCustomer = orders.stream()
    .collect(Collectors.groupingBy(
        Order::customer,
        Collectors.filtering(o -> o.total() > 100, Collectors.toList())
    ));

// Group by category, collecting all tags from items (each item has multiple tags)
Map<String, Set<String>> tagsByCategory = items.stream()
    .collect(Collectors.groupingBy(
        Item::category,
        Collectors.flatMapping(
            item -> item.tags().stream(),
            Collectors.toSet()
        )
    ));
```

In the first example, `filtering` runs *after* each order is assigned to a customer bucket — orders ≤ $100 are excluded from that customer's list. In the second, `flatMapping` expands each item's tags into individual strings and collects them into a set per category.

## 4. Diagram

<svg viewBox="0 0 620 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="filtering and flatMapping as downstream collectors inside groupingBy">
  <rect x="20" y="10" width="580" height="180" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="40" y="30" width="200" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="140" y="55" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">stream of elements</text>

  <text x="250" y="55" fill="#8b949e" font-size="10" font-family="monospace">──►</text>

  <rect x="260" y="25" width="140" height="50" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="330" y="43" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">groupingBy(key)</text>
  <text x="330" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">→ per-group bucket</text>

  <text x="410" y="50" fill="#8b949e" font-size="10" font-family="monospace">──►</text>

  <rect x="420" y="30" width="170" height="40" rx="4" fill="#f0883e" stroke="#f0883e"/>
  <text x="505" y="55" fill="#f0883e" font-size="10" text-anchor="middle" font-family="monospace">filtering / flatMapping</text>

  <text x="40" y="100" fill="#8b949e" font-size="10" font-family="sans-serif">filtering example:</text>
  <text x="40" y="118" fill="#8b949e" font-size="9" font-family="monospace">  groupingBy(Customer, filtering(o → o.total() &gt; 100, toList()))</text>
  <text x="40" y="135" fill="#6db33f" font-size="9" font-family="monospace">  → each customer bucket only gets their orders above $100</text>

  <text x="40" y="158" fill="#8b949e" font-size="10" font-family="sans-serif">flatMapping example:</text>
  <text x="40" y="176" fill="#8b949e" font-size="9" font-family="monospace">  groupingBy(Category, flatMapping(item → item.tags().stream(), toSet()))</text>
  <text x="40" y="193" fill="#6db33f" font-size="9" font-family="monospace">  → each category bucket gets all tags from all its items, de-duplicated</text>
</svg>

The filter or flatten happens *inside* the collector, after grouping, so empty groups are preserved in the map.

## 5. Runnable example

Scenario: a sales reporting system that groups transactions by region and computes filtered/flattened statistics — starting with a basic filtered group, extending to a flat-mapped item-tag aggregation, and finally combining both in a complex multi-level report.

### Level 1 — Basic

```java
// File: FilteringCollectorDemo.java
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class FilteringCollectorDemo {
    record Transaction(String region, int amount) {}

    public static void main(String[] args) {
        List<Transaction> txns = List.of(
            new Transaction("EU",  150),
            new Transaction("EU",   50),
            new Transaction("EU",  300),
            new Transaction("US",  200),
            new Transaction("US",   75),
            new Transaction("ASIA", 10)
        );

        // Group by region, but only include transactions > $100
        Map<String, List<Transaction>> largeByRegion = txns.stream()
            .collect(Collectors.groupingBy(
                Transaction::region,
                Collectors.filtering(t -> t.amount() > 100, Collectors.toList())
            ));

        System.out.println("Large transactions (>$100) by region:");
        largeByRegion.forEach((region, list) -> {
            System.out.print("  " + region + ": ");
            System.out.println(list.stream()
                .map(t -> "$" + t.amount())
                .collect(Collectors.joining(", ")));
        });
    }
}
```

**How to run:** `java FilteringCollectorDemo.java`

Expected output:
```
Large transactions (>$100) by region:
  ASIA: 
  US: $200
  EU: $150, $300
```

The simplest filtering collector: `ASIA` appears in the map even though it has zero qualifying transactions — the empty group is preserved. This is the key difference from pre-filtering the stream before `groupingBy`, which would have omitted `ASIA` entirely from the output map.

### Level 2 — Intermediate

```java
// File: FlatMappingCollectorDemo.java
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

public class FlatMappingCollectorDemo {
    record Product(String category, List<String> tags) {}

    public static void main(String[] args) {
        List<Product> products = List.of(
            new Product("Electronics", List.of("bluetooth", "wireless", "premium")),
            new Product("Electronics", List.of("wired", "budget")),
            new Product("Clothing",    List.of("cotton", "summer", "casual")),
            new Product("Clothing",    List.of("wool", "winter", "premium")),
            new Product("Clothing",    List.of("cotton", "casual", "budget"))
        );

        // Group by category, collecting all unique tags across products
        Map<String, Set<String>> tagsByCategory = products.stream()
            .collect(Collectors.groupingBy(
                Product::category,
                Collectors.flatMapping(
                    p -> p.tags().stream(),
                    Collectors.toSet()
                )
            ));

        System.out.println("Tags by category:");
        tagsByCategory.forEach((cat, tags) ->
            System.out.println("  " + cat + ": " + tags));
    }
}
```

**How to run:** `java FlatMappingCollectorDemo.java`

Expected output:
```
Tags by category:
  Electronics: [budget, wired, wireless, bluetooth, premium]
  Clothing: [summer, casual, wool, winter, cotton, budget, premium]
```

The real-world concern added: each product has multiple tags, and we want all unique tags per category. `flatMapping` expands each product's `tags` list into a stream of individual tags, and `toSet()` collects them with deduplication. Notice that `"premium"` appears in both Electronics and Clothing, and `"cotton"` appears in two Clothing products — `toSet()` deduplicates within each category.

### Level 3 — Advanced

```java
// File: SalesReport.java
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class SalesReport {
    record Order(String region, String product, int amount) {}

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("EU",  "Laptop",  1500),
            new Order("EU",  "Mouse",      25),
            new Order("EU",  "Monitor",   400),
            new Order("US",  "Laptop",  1200),
            new Order("US",  "Keyboard",   80),
            new Order("US",  "Monitor",   450),
            new Order("US",  "Mouse",      30),
            new Order("ASIA","Laptop",  1100),
            new Order("ASIA","USB Cable",  10)
        );

        // Report: per region, list of high-value products (>$200) as uppercase names,
        // and count of low-value items (≤$200)
        record RegionReport(List<String> highValueProducts, long lowValueCount) {}

        Map<String, RegionReport> report = orders.stream()
            .collect(Collectors.groupingBy(
                Order::region,
                Collectors.teeing(
                    // downstream 1: high-value product names
                    Collectors.filtering(
                        o -> o.amount() > 200,
                        Collectors.mapping(
                            o -> o.product().toUpperCase(),
                            Collectors.toList()
                        )
                    ),
                    // downstream 2: count of low-value orders
                    Collectors.filtering(
                        o -> o.amount() <= 200,
                        Collectors.counting()
                    ),
                    RegionReport::new
                )
            ));

        System.out.println("Sales Report by Region:\n");
        report.forEach((region, r) -> {
            System.out.println(region + ":");
            System.out.println("  High-value: " + r.highValueProducts());
            System.out.println("  Low-value count: " + r.lowValueCount());
        });
    }
}
```

**How to run:** `java SalesReport.java`

Expected output:
```
Sales Report by Region:

ASIA:
  High-value: [LAPTOP]
  Low-value count: 1
US:
  High-value: [LAPTOP, MONITOR]
  Low-value count: 2
EU:
  High-value: [LAPTOP, MONITOR]
  Low-value count: 1
```

The production-flavoured report combines `filtering` with `Collectors.teeing` (Java 12+) to produce a structured per-region report with two computed fields: a list of uppercase high-value product names and a count of low-value orders. The `filtering` collector is used in both downstream branches — one filtering for high-value (with an additional `mapping` to uppercase), the other filtering for low-value (with `counting`). Each region group sees both branches, and `teeing` merges the two results into a `RegionReport` record.

## 6. Walkthrough

Tracing the Level 3 report pipeline for the "US" region:

1. The stream consumes `orders` sequentially. As each `Order` is processed, `groupingBy(Order::region)` routes it to a region bucket based on `o.region()`.

2. Five orders land in the "US" bucket: `[Laptop $1200, Keyboard $80, Monitor $450, Mouse $30, ...]` — wait, we only had 4 US orders. Let me re-check: US has Laptop 1200, Keyboard 80, Monitor 450, Mouse 30. That's 4 US orders.

3. The downstream is `Collectors.teeing(highValueCollector, lowValueCollector, RegionReport::new)`. `teeing` fans out the US bucket's elements to both collectors simultaneously.

4. **High-value collector**: `filtering(o -> o.amount() > 200, mapping(o -> o.product().toUpperCase(), toList()))`
   - Laptop $1200: `1200 > 200` → passes filter → mapped to `"LAPTOP"` → added to list.
   - Keyboard $80: `80 > 200` → fails filter → discarded.
   - Monitor $450: `450 > 200` → passes → mapped to `"MONITOR"` → added to list.
   - Mouse $30: `30 > 200` → fails filter → discarded.
   - Result: `["LAPTOP", "MONITOR"]`.

5. **Low-value collector**: `filtering(o -> o.amount() <= 200, counting())`
   - Laptop $1200: `1200 <= 200` → fails → not counted.
   - Keyboard $80: `80 <= 200` → passes → counted (1).
   - Monitor $450: fails → not counted.
   - Mouse $30: passes → counted (2).
   - Result: `2`.

6. `RegionReport::new` constructs `RegionReport(["LAPTOP", "MONITOR"], 2)`.

7. The map entry for "US" stores this `RegionReport`. The `forEach` prints it:
```
US:
  High-value: [LAPTOP, MONITOR]
  Low-value count: 2
```

```
orders.stream()
  │
  ▼
groupingBy(Order::region)
  │
  ├── EU  bucket ──► filtering(>200, mapping(upper, toList())) → [LAPTOP, MONITOR]
  │                            filtering(≤200, counting())     → 1
  │                            RegionReport → EU report
  │
  ├── US  bucket ──► filtering(>200, ...) → [LAPTOP, MONITOR]
  │                  filtering(≤200, ...) → 2
  │                  RegionReport → US report
  │
  └── ASIA bucket ─► filtering(>200, ...) → [LAPTOP]
                     filtering(≤200, ...) → 1
                     RegionReport → ASIA report
```

## 7. Gotchas & takeaways

> `filtering` and `flatMapping` are **downstream collectors**, not stream operations — they must be passed as arguments to `groupingBy`, `partitioningBy`, `teeing`, or another collector that accepts a downstream. Calling `Collectors.filtering(pred, collector)` alone does nothing; you need `.collect(Collectors.filtering(...))` or nest it inside a grouping collector.

- The filter in `Collectors.filtering` runs **after** grouping — this means groups where all elements are filtered out still appear in the resulting map with an empty collection. This is the key behavioural difference from calling `.filter()` on the stream before `groupingBy`.
- `flatMapping` applies the mapper function per-element and concatenates the resulting streams — equivalent to `stream.flatMap(mapper).collect(downstream)` but scoped to each grouping bucket.
- Combining `filtering` with `counting()` is the idiomatic way to get per-group counts with a condition: `groupingBy(key, filtering(pred, counting()))` gives you "how many items per group satisfy the predicate."
- These collectors compose with any downstream collector — `toList()`, `toSet()`, `toMap()`, `joining()`, `summingInt()`, or even another `groupingBy` for multi-level aggregation.
- `flatMapping` is not the same as `mapping` — `mapping` transforms each element into exactly one output element, while `flatMapping` can produce zero, one, or many output elements per input element. 