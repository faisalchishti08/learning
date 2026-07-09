---
card: java
gi: 517
slug: summingint-averagingint
title: summingInt / averagingInt
---

## 1. What it is

`Collectors.summingInt(mapper)` (and its `summingLong`/`summingDouble` siblings) is a collector that extracts a numeric value from each element via `mapper` and sums them, producing an `int`/`long`/`double` total. `Collectors.averagingInt(mapper)` (and `averagingLong`/`averagingDouble`) does the same extraction but computes the mean instead, always producing a `Double` — regardless of whether the source values were `int`, `long`, or `double`. Both are designed to be used as downstream collectors alongside `groupingBy`, just like `Collectors.counting()`.

## 2. Why & when

These collectors exist to compute numeric aggregates — sums and averages — directly within a `Collectors` pipeline, most usefully as the downstream argument to `groupingBy` for per-group totals and averages. They're the `Collectors`-world equivalent of `mapToInt(...).sum()`/`.average()` on a primitive stream (see [[sum-average-summarystatistics-primitive-streams]]), but composable inside `groupingBy` in a way primitive stream methods aren't, since `groupingBy` needs its downstream argument to be a `Collector`, not a separate stream pipeline.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

record Sale(String region, int amount) {}

List<Sale> sales = List.of(
        new Sale("West", 100), new Sale("East", 50), new Sale("West", 75));

Map<String, Integer> totalByRegion = sales.stream()
        .collect(Collectors.groupingBy(Sale::region, Collectors.summingInt(Sale::amount)));
// {West=175, East=50}

Map<String, Double> avgByRegion = sales.stream()
        .collect(Collectors.groupingBy(Sale::region, Collectors.averagingInt(Sale::amount)));
// {West=87.5, East=50.0}
```

`summingInt` extracts and sums a numeric field per group; `averagingInt` extracts the same kind of field but computes the mean, always as a `Double`.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="summingInt and averagingInt compute per-group totals and means as downstream collectors">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="20" width="90" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="65" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">West, 100</text>
  <rect x="120" y="20" width="90" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="165" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">West, 75</text>
  <text x="115" y="65" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">summingInt / averagingInt</text>
  <line x1="115" y1="50" x2="115" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowSI)"/>
  <rect x="30" y="85" width="90" height="28" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="75" y="104" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">sum: 175</text>
  <rect x="130" y="85" width="90" height="28" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="175" y="104" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">avg: 87.5</text>
  <defs><marker id="arrowSI" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both collectors extract the same numeric field, but `summingInt` totals it while `averagingInt` computes its mean.

## 5. Runnable example

Scenario: analyzing delivery times across warehouses — evolved from a basic per-warehouse sum, through per-warehouse average, to a version computing both together for a full efficiency report.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class SummingIntBasic {
    record Delivery(String warehouse, int itemCount) {}

    public static void main(String[] args) {
        List<Delivery> deliveries = List.of(
                new Delivery("North", 12),
                new Delivery("South", 8),
                new Delivery("North", 5),
                new Delivery("South", 20)
        );

        Map<String, Integer> totalItemsByWarehouse = deliveries.stream()
                .collect(Collectors.groupingBy(Delivery::warehouse, Collectors.summingInt(Delivery::itemCount)));

        new TreeMap<>(totalItemsByWarehouse).forEach((wh, total) -> System.out.println(wh + ": " + total + " items"));
    }
}
```

**How to run:** `java SummingIntBasic.java`

Expected output:
```
North: 17 items
South: 28 items
```

`Collectors.summingInt(Delivery::itemCount)` sums the `itemCount` field within each warehouse group: `North` gets `12 + 5 = 17`, `South` gets `8 + 20 = 28` — the total item volume shipped from each location.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class AveragingIntBasic {
    record Delivery(String warehouse, int deliveryTimeMinutes) {}

    public static void main(String[] args) {
        List<Delivery> deliveries = List.of(
                new Delivery("North", 45),
                new Delivery("South", 60),
                new Delivery("North", 30),
                new Delivery("South", 50),
                new Delivery("North", 55)
        );

        Map<String, Double> avgTimeByWarehouse = deliveries.stream()
                .collect(Collectors.groupingBy(Delivery::warehouse, Collectors.averagingInt(Delivery::deliveryTimeMinutes)));

        new TreeMap<>(avgTimeByWarehouse).forEach((wh, avg) -> System.out.printf("%s: %.1f min avg%n", wh, avg));
    }
}
```

**How to run:** `java AveragingIntBasic.java`

Expected output:
```
North: 43.3 min avg
South: 55.0 min avg
```

The real-world concern this adds: a per-group *average*, not a total, is often the more meaningful comparison — a warehouse shipping more items isn't necessarily slower, so average delivery time per warehouse (`North`: `(45+30+55)/3 = 43.33...`, `South`: `(60+50)/2 = 55.0`) gives a fairer efficiency comparison than raw totals would.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class SummingAveragingCombined {
    record Delivery(String warehouse, int itemCount, int deliveryTimeMinutes) {}
    record WarehouseReport(int totalItems, double avgDeliveryTime) {}

    public static void main(String[] args) {
        List<Delivery> deliveries = List.of(
                new Delivery("North", 12, 45),
                new Delivery("South", 8, 60),
                new Delivery("North", 5, 30),
                new Delivery("South", 20, 50),
                new Delivery("North", 9, 55)
        );

        // Compute BOTH a sum and an average per group, combined via Collectors.teeing.
        Map<String, WarehouseReport> reportByWarehouse = deliveries.stream()
                .collect(Collectors.groupingBy(
                        Delivery::warehouse,
                        Collectors.teeing(
                                Collectors.summingInt(Delivery::itemCount),
                                Collectors.averagingInt(Delivery::deliveryTimeMinutes),
                                WarehouseReport::new)));

        new TreeMap<>(reportByWarehouse).forEach((wh, report) ->
                System.out.printf("%s: %d items total, %.1f min avg delivery%n", wh, report.totalItems(), report.avgDeliveryTime()));
    }
}
```

**How to run:** `java SummingAveragingCombined.java`

Expected output:
```
North: 26 items total, 43.3 min avg delivery
South: 28 items total, 55.0 min avg delivery
```

This computes **both** a sum and an average per group in a single pass using `Collectors.teeing(collector1, collector2, merger)`, which runs two independent downstream collectors over the same group's elements and combines their two results with a merge function — here, building a `WarehouseReport` record directly from the item-count sum and the delivery-time average, without needing two separate `groupingBy` calls or a second pass over the data.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Five deliveries are defined: three for `"North"` (item counts `12, 5, 9`; delivery times `45, 30, 55`) and two for `"South"` (item counts `8, 20`; delivery times `60, 50`).

`deliveries.stream().collect(Collectors.groupingBy(Delivery::warehouse, Collectors.teeing(Collectors.summingInt(Delivery::itemCount), Collectors.averagingInt(Delivery::deliveryTimeMinutes), WarehouseReport::new)))` processes each delivery, grouping by `warehouse`, and within each group, `Collectors.teeing(...)` maintains **two** independent downstream accumulators simultaneously: one for `summingInt(Delivery::itemCount)`, one for `averagingInt(Delivery::deliveryTimeMinutes)`.

For `"North"`'s deliveries — `Delivery("North", 12, 45)`, `Delivery("North", 5, 30)`, `Delivery("North", 9, 55)` — the summing accumulator tracks `12 + 5 + 9 = 26`, while the averaging accumulator tracks the mean of `45, 30, 55`, which is `(45+30+55)/3 = 130/3 = 43.333...`.

For `"South"`'s deliveries — `Delivery("South", 8, 60)`, `Delivery("South", 20, 50)` — the summing accumulator tracks `8 + 20 = 28`, while the averaging accumulator tracks the mean of `60, 50`, which is `(60+50)/2 = 55.0`.

```
North: itemCounts=[12,5,9] sum=26   deliveryTimes=[45,30,55] avg=43.33
South: itemCounts=[8,20]   sum=28   deliveryTimes=[60,50]    avg=55.0
```

Once each group's elements are fully processed, `teeing`'s merge function, `WarehouseReport::new`, is called once per group with both accumulated results: for `"North"`, `new WarehouseReport(26, 43.333...)`; for `"South"`, `new WarehouseReport(28, 55.0)`. `new TreeMap<>(...)` orders the warehouses alphabetically, and the `forEach` prints each warehouse's combined report: `"North: 26 items total, 43.3 min avg delivery"` (rounded for display via `%.1f`) and `"South: 28 items total, 55.0 min avg delivery"`.

## 7. Gotchas & takeaways

> `averagingInt`/`averagingLong`/`averagingDouble` always return `Double`, regardless of the source field's type — averaging a group of `int` values still produces a `Double` mean, since an average is rarely a whole number even when the inputs are integers. Don't expect an `Integer` result from `averagingInt` despite its name referencing `int`.

- `Collectors.summingInt/Long/Double(mapper)` extracts a numeric field and sums it — most useful as a `groupingBy` downstream collector for per-group totals.
- `Collectors.averagingInt/Long/Double(mapper)` extracts the same kind of field but computes the mean, always returning `Double`.
- `Collectors.teeing(collectorA, collectorB, merger)` runs two collectors over the same elements simultaneously and combines their results — a clean way to compute multiple aggregates (like both a sum and an average) in one pass, without two separate `groupingBy` calls.
- Both collectors, like `Collectors.counting()`, are typically used as downstream arguments to `groupingBy`, not usually as the sole top-level collector for a whole stream.
- For more than two combined aggregates per group, `Collectors.summarizingInt`/`summarizingLong`/`summarizingDouble` (see [[sum-average-summarystatistics-primitive-streams]]) may be simpler than nesting multiple `teeing` calls, since a single `IntSummaryStatistics` already bundles count, sum, min, max, and average together.
