---
card: java
gi: 503
slug: collect
title: collect()
---

## 1. What it is

`Stream.collect(Collector)` is a terminal operation that gathers a stream's elements into a result container — a `List`, `Set`, `Map`, a joined `String`, grouped buckets, or a custom accumulation — driven by a `Collector` object. The `Collectors` utility class provides ready-made collectors for nearly every common case: `Collectors.toList()`, `Collectors.joining(...)`, `Collectors.groupingBy(...)`, `Collectors.toMap(...)`, and many more. `collect` is the general-purpose "reduce into a mutable container" operation, more flexible than `reduce` for building collections because it can efficiently accumulate into a mutable structure rather than repeatedly creating new immutable results.

## 2. Why & when

While `.toList()` covers the single most common case directly, `collect(Collectors...)` is what you reach for whenever you need something more structured than a flat list: grouping elements by a key, partitioning into two buckets by a condition, joining strings with a delimiter, building a `Map` from elements, or computing multiple statistics at once. `Collectors.groupingBy` in particular is one of the most powerful tools in the Streams API — it turns a flat stream into a `Map<K, List<V>>` (or richer nested structures) in one call, replacing what would otherwise be a manual loop with a mutable `HashMap` and `computeIfAbsent` calls.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

record Employee(String name, String department) {}

List<Employee> employees = List.of(
        new Employee("Alice", "Engineering"),
        new Employee("Bob", "Sales"),
        new Employee("Carol", "Engineering")
);

Map<String, List<Employee>> byDept = employees.stream()
        .collect(Collectors.groupingBy(Employee::department));
// {Engineering=[Alice, Carol], Sales=[Bob]}

String joined = employees.stream()
        .map(Employee::name)
        .collect(Collectors.joining(", ", "[", "]")); // "[Alice, Bob, Carol]"
```

`collect` takes a `Collector` that knows how to build up a mutable result container from the stream's elements — `Collectors.groupingBy` and `Collectors.joining` are two of the many ready-made collectors available.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="collect with groupingBy buckets elements into a Map keyed by a derived value">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="20" width="90" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="65" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Alice (Eng)</text>
  <rect x="120" y="20" width="90" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="165" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Bob (Sales)</text>
  <rect x="220" y="20" width="90" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="265" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Carol (Eng)</text>
  <text x="160" y="70" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">collect(groupingBy(department))</text>
  <line x1="160" y1="55" x2="160" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowC)"/>
  <rect x="30" y="90" width="180" height="50" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="120" y="110" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Engineering</text><text x="120" y="128" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">[Alice, Carol]</text>
  <rect x="230" y="90" width="140" height="50" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="300" y="110" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Sales</text><text x="300" y="128" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">[Bob]</text>
  <defs><marker id="arrowC" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`groupingBy` sorts every element into a bucket keyed by the result of the classifier function — one list per distinct key.

## 5. Runnable example

Scenario: analyzing a batch of customer orders for a sales dashboard — evolved from a basic string-joining collect, through grouping orders by region, to a version that computes per-region totals using a downstream collector.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class CollectBasic {
    public static void main(String[] args) {
        List<String> customerNames = List.of("Alice", "Bob", "Carol");

        String summary = customerNames.stream()
                .collect(Collectors.joining(", ", "Customers: ", "."));

        System.out.println(summary);
    }
}
```

**How to run:** `java CollectBasic.java`

Expected output:
```
Customers: Alice, Bob, Carol.
```

`Collectors.joining(", ", "Customers: ", ".")` builds a single `String` by concatenating each element with `", "` between them, prefixed with `"Customers: "` and suffixed with `"."` — a common alternative to manually managing a `StringBuilder` and delimiter logic.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class CollectGroupingBy {
    record Order(String id, String region, double amount) {}

    public static void main(String[] args) {
        List<Order> orders = List.of(
                new Order("O1", "West", 120.00),
                new Order("O2", "East", 85.50),
                new Order("O3", "West", 60.00),
                new Order("O4", "East", 200.00)
        );

        Map<String, List<Order>> byRegion = orders.stream()
                .collect(Collectors.groupingBy(Order::region));

        // TreeMap just to print in a deterministic, sorted order for this example
        new TreeMap<>(byRegion).forEach((region, regionOrders) ->
                System.out.println(region + ": " + regionOrders.size() + " orders"));
    }
}
```

**How to run:** `java CollectGroupingBy.java`

Expected output:
```
East: 2 orders
West: 2 orders
```

The real-world concern this adds: instead of a flat result, orders are now sorted into buckets by `region` using `Collectors.groupingBy(Order::region)`, which returns a `Map<String, List<Order>>` — one entry per distinct region, each holding all the orders that belong to it. This is the streams equivalent of a manual `HashMap<String, List<Order>>` with `computeIfAbsent(...).add(order)` in a loop, done in a single collect call.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class CollectGroupingDownstream {
    record Order(String id, String region, double amount) {}

    public static void main(String[] args) {
        List<Order> orders = List.of(
                new Order("O1", "West", 120.00),
                new Order("O2", "East", 85.50),
                new Order("O3", "West", 60.00),
                new Order("O4", "East", 200.00)
        );

        // groupingBy with a downstream collector: sum each group's amounts directly, no intermediate List.
        Map<String, Double> totalByRegion = orders.stream()
                .collect(Collectors.groupingBy(
                        Order::region,
                        Collectors.summingDouble(Order::amount)));

        new TreeMap<>(totalByRegion).forEach((region, total) ->
                System.out.printf("%s: $%.2f%n", region, total));
    }
}
```

**How to run:** `java CollectGroupingDownstream.java`

Expected output:
```
East: $285.50
West: $180.00
```

This adds a **downstream collector**: `Collectors.groupingBy` accepts a second argument that determines what happens *within* each group, instead of always collecting into a `List`. `Collectors.summingDouble(Order::amount)` sums the `amount` field of every order within each region group directly, producing `Map<String, Double>` (region to total) rather than `Map<String, List<Order>>` — skipping the intermediate list entirely and computing the aggregate in the same pass.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Four orders are defined: two in `"West"` (`120.00`, `60.00`) and two in `"East"` (`85.50`, `200.00`).

`orders.stream().collect(Collectors.groupingBy(Order::region, Collectors.summingDouble(Order::amount)))` processes the stream. Internally, `groupingBy` maintains a working `Map<String, ...>` (conceptually a `HashMap` by default) and, for each order, first determines its group key by calling the classifier, `Order::region`.

For `O1` (`"West"`, `120.00`): the key `"West"` has no existing group yet, so a new downstream accumulator (from `Collectors.summingDouble`) is created for it, and `O1`'s amount, `120.00`, is added to it — the running sum for `"West"` becomes `120.00`.

For `O2` (`"East"`, `85.50`): the key `"East"` has no existing group, a new accumulator is created, and `85.50` is added — running sum for `"East"` is `85.50`.

For `O3` (`"West"`, `60.00`): the key `"West"` already has an accumulator (from `O1`), so `60.00` is added to the existing running sum: `120.00 + 60.00 = 180.00`.

For `O4` (`"East"`, `200.00`): the key `"East"` already has an accumulator (from `O2`), so `200.00` is added: `85.50 + 200.00 = 285.50`.

```
O1 (West, 120.00)  -> new group "West",  running sum = 120.00
O2 (East, 85.50)   -> new group "East",  running sum = 85.50
O3 (West, 60.00)   -> existing "West",   running sum = 120.00 + 60.00  = 180.00
O4 (East, 200.00)  -> existing "East",   running sum = 85.50 + 200.00 = 285.50

Final map: {West=180.00, East=285.50}
```

Once every order has been processed, each group's `summingDouble` accumulator finishes with its final total, and `groupingBy` assembles the result `Map<String, Double>`: `{"West"=180.00, "East"=285.50}`. `new TreeMap<>(totalByRegion)` wraps it just to guarantee alphabetical print order (`HashMap`'s own iteration order isn't guaranteed), and the `forEach` prints `"East: $285.50"` then `"West: $180.00"`.

## 7. Gotchas & takeaways

> `Collectors.groupingBy(classifier)` without a downstream collector defaults to grouping into `List<T>` per key — but it's easy to reach for a `List` grouping and then manually sum/count/reduce each list afterward in a second pass, when a downstream collector (`Collectors.summingDouble`, `Collectors.counting()`, `Collectors.mapping(...)`, etc.) can compute the same result directly in the single grouping pass, which is both more efficient and more concise.

- `collect(Collector)` is the general-purpose way to accumulate a stream into a structured result — `List`, `Set`, `Map`, joined `String`, or a custom container.
- `Collectors.groupingBy(classifier)` buckets elements by a derived key into `Map<K, List<V>>`; adding a downstream collector as a second argument changes what happens within each bucket.
- `Collectors.joining(delimiter, prefix, suffix)` builds a formatted `String` from a stream of strings, avoiding manual `StringBuilder` management.
- `Collectors.partitioningBy(predicate)` is a specialized two-bucket version of `groupingBy`, always producing exactly `Map<Boolean, List<T>>` for a `true`/`false` split.
- The default `Map` implementation returned by `groupingBy` (typically `HashMap`) has no guaranteed iteration order — wrap the result in a `TreeMap` (as done here) or use `Collectors.groupingBy(..., TreeMap::new, ...)` if a specific key order matters for display.
