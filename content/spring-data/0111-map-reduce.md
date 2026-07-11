---
card: spring-data
gi: 111
slug: map-reduce
title: "Map-reduce"
---

## 1. What it is

Map-reduce is an older MongoDB computation mechanism predating the aggregation framework: a **map** function emits key/value pairs from each document, and a **reduce** function combines all values sharing the same key into one result — Spring Data MongoDB exposed this through `MapReduceOperations`, but MongoDB itself has deprecated map-reduce in favor of the aggregation framework's `$group`/`$accumulator` stages, which are generally faster and easier to reason about for the same computations.

```java
// Historical, largely superseded by Aggregation.group(...) covered in the earlier aggregation card:
MapReduceResults<CustomerTotal> results = mongoTemplate.mapReduce(
    "orders", "classpath:map.js", "classpath:reduce.js", CustomerTotal.class);
```

## 2. Why & when

This card closes out the section by explaining a mechanism you're now equipped to recognize but should rarely, if ever, reach for in new code: map-reduce solves the same "compute grouped results across a collection" problem the aggregation framework card just covered, but through a more general (and correspondingly slower and more complex) two-function model, and MongoDB itself now recommends the aggregation pipeline instead for virtually all use cases map-reduce used to handle.

Reach for an understanding of map-reduce specifically when:

- You encounter existing code using `MapReduceOperations`/`mongoTemplate.mapReduce(...)` and need to understand what it's doing — recognizing the map/reduce pattern is the key to reading it, even if you'd write it differently today.
- You're migrating legacy map-reduce logic to the aggregation framework — recognizing which map-reduce pattern maps to which aggregation stage (`$group` most commonly) is the core translation skill.
- You're evaluating whether a genuinely complex computation still needs map-reduce's more general JavaScript-function model — this is rare in practice, since the aggregation framework's stages (plus `$function`/`$accumulator` for custom logic) cover the overwhelming majority of real cases now.

## 3. Core concept

```
 MAP function: runs once PER DOCUMENT, emits (key, value) pairs
   function() { emit(this.customerId, this.total); }

 REDUCE function: runs once PER UNIQUE KEY, combines all values for that key
   function(key, values) { return Array.sum(values); }

 Map-reduce (historical):                   Aggregation framework (current, preferred):
   map: emit(customerId, total)                Aggregation.group("customerId").sum("total").as("totalSpent")
   reduce: sum the values per key               -- ONE stage expresses the same computation
   -- two separate JS functions, slower          -- built-in, optimized, no custom JS needed
```

The same "sum per group" computation that once required two hand-written JavaScript functions is now a single, optimized aggregation stage.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Map-reduce's two-function model and the aggregation framework's single group stage both compute the same grouped sum, but the aggregation framework is preferred">
  <text x="20" y="20" fill="#e6edf3" font-size="10" font-family="sans-serif">Map-reduce (historical, deprecated)</text>
  <rect x="20" y="30" width="180" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="110" y="50" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">map: emit(key, value)</text>
  <text x="110" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">per document</text>
  <rect x="230" y="30" width="180" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="50" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">reduce: combine values</text>
  <text x="320" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">per unique key</text>

  <text x="20" y="115" fill="#e6edf3" font-size="10" font-family="sans-serif">Aggregation framework (preferred)</text>
  <rect x="20" y="125" width="390" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="215" y="147" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Aggregation.group("customerId").sum("total")</text>
</svg>

Two hand-written JavaScript functions in the historical model collapse into one built-in aggregation stage in the current, preferred approach.

## 5. Runnable example

The scenario: computing total spending per customer (the same computation from the aggregation framework card), evolving from a map-reduce-style two-function model, to translating it into an aggregation-style equivalent, to a side-by-side comparison confirming both produce identical results.

### Level 1 — Basic

Model the map-reduce pattern directly: a map step emitting key/value pairs, followed by a reduce step combining them per key.

```java
import java.util.*;
import java.util.function.*;

class Order { String customerId; double total; Order(String customerId, double total) { this.customerId = customerId; this.total = total; } }

public class MapReduceLevel1 {
    // MAP: function() { emit(this.customerId, this.total); }
    static List<Map.Entry<String, Double>> map(List<Order> orders) {
        List<Map.Entry<String, Double>> emitted = new ArrayList<>();
        for (Order o : orders) emitted.add(Map.entry(o.customerId, o.total)); // one emit() per document
        return emitted;
    }

    // REDUCE: function(key, values) { return Array.sum(values); }
    static Map<String, Double> reduce(List<Map.Entry<String, Double>> emitted) {
        Map<String, Double> result = new HashMap<>();
        for (Map.Entry<String, Double> pair : emitted) {
            result.merge(pair.getKey(), pair.getValue(), Double::sum); // combines ALL values sharing a key
        }
        return result;
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("cust-A", 50), new Order("cust-A", 75), new Order("cust-B", 300)
        );

        List<Map.Entry<String, Double>> mapped = map(orders);
        Map<String, Double> reduced = reduce(mapped);

        System.out.println("Emitted pairs: " + mapped);
        System.out.println("Reduced totals: " + reduced);
    }
}
```

How to run: `java MapReduceLevel1.java`

`map` emits one `(customerId, total)` pair per order (three pairs for three orders); `reduce` then combines pairs sharing the same key — `cust-A`'s two pairs (`50`, `75`) merge into `125`, while `cust-B`'s single pair stays `300`. This two-step process is exactly how MongoDB's historical map-reduce mechanism computes a grouped sum.

### Level 2 — Intermediate

Compute the same result using the aggregation-framework style from the earlier card, confirming it produces an identical answer with a single, more direct step.

```java
import java.util.*;
import java.util.stream.*;

class Order { String customerId; double total; Order(String customerId, double total) { this.customerId = customerId; this.total = total; } }
record CustomerSpending(String customerId, double totalSpent) {}

public class MapReduceLevel2 {
    // Aggregation.group("customerId").sum("total").as("totalSpent") -- ONE step, no separate map/reduce functions.
    static List<CustomerSpending> groupStage(List<Order> orders) {
        Map<String, Double> sums = orders.stream()
            .collect(Collectors.groupingBy(o -> o.customerId, Collectors.summingDouble(o -> o.total)));
        return sums.entrySet().stream().map(e -> new CustomerSpending(e.getKey(), e.getValue())).collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("cust-A", 50), new Order("cust-A", 75), new Order("cust-B", 300)
        );

        List<CustomerSpending> results = groupStage(orders);
        for (CustomerSpending cs : results) System.out.println(cs.customerId() + ": " + cs.totalSpent());
    }
}
```

How to run: `java MapReduceLevel2.java`

`groupStage` computes the identical grouped sum (`cust-A: 125`, `cust-B: 300`) in a single pass, using `Collectors.groupingBy`/`summingDouble` — standing in for `Aggregation.group(...).sum(...)`, which performs this same computation as one built-in, optimized aggregation stage rather than two separate hand-written functions.

### Level 3 — Advanced

Run both approaches side by side against the same data and assert they produce identical results, making the equivalence (and the aggregation framework's relative simplicity) concrete rather than just asserted.

```java
import java.util.*;
import java.util.stream.*;

class Order { String customerId; double total; Order(String customerId, double total) { this.customerId = customerId; this.total = total; } }

public class MapReduceLevel3 {
    // Map-reduce style.
    static Map<String, Double> mapReduceStyle(List<Order> orders) {
        List<Map.Entry<String, Double>> emitted = new ArrayList<>();
        for (Order o : orders) emitted.add(Map.entry(o.customerId, o.total));
        Map<String, Double> result = new HashMap<>();
        for (Map.Entry<String, Double> pair : emitted) result.merge(pair.getKey(), pair.getValue(), Double::sum);
        return result;
    }

    // Aggregation-framework style.
    static Map<String, Double> aggregationStyle(List<Order> orders) {
        return orders.stream().collect(Collectors.groupingBy(o -> o.customerId, Collectors.summingDouble(o -> o.total)));
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("cust-A", 50), new Order("cust-A", 75), new Order("cust-A", 25),
            new Order("cust-B", 300), new Order("cust-C", 10), new Order("cust-C", 90)
        );

        Map<String, Double> viaMapReduce = mapReduceStyle(orders);
        Map<String, Double> viaAggregation = aggregationStyle(orders);

        System.out.println("Map-reduce result:   " + new TreeMap<>(viaMapReduce));
        System.out.println("Aggregation result:  " + new TreeMap<>(viaAggregation));
        System.out.println("Results identical?   " + viaMapReduce.equals(viaAggregation));
    }
}
```

How to run: `java MapReduceLevel3.java`

Both `mapReduceStyle` and `aggregationStyle` compute the exact same per-customer totals from the exact same input data, and `viaMapReduce.equals(viaAggregation)` confirms `true` — the two mechanisms are computationally equivalent for this kind of grouped-sum problem, but the aggregation-framework version required no separate map/reduce function pair, no JavaScript execution, and (in a real MongoDB deployment) runs measurably faster, which is precisely why MongoDB recommends it over map-reduce for new development.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, six orders are built across three customers: `cust-A` with three orders (`50`, `75`, `25`), `cust-B` with one (`300`), and `cust-C` with two (`10`, `90`).

`mapReduceStyle(orders)` runs first: the map phase emits six `(customerId, total)` pairs, one per order. The reduce phase then folds these pairs together by key using `Map.merge`, accumulating `cust-A`'s three values into `50 + 75 + 25 = 150`, `cust-B`'s single value staying `300`, and `cust-C`'s two values combining into `10 + 90 = 100`.

`aggregationStyle(orders)` runs next, computing the identical grouped sums in one pass via `Collectors.groupingBy`/`summingDouble` — `cust-A: 150`, `cust-B: 300`, `cust-C: 100`.

Both results are printed (wrapped in `TreeMap` purely for consistent, sorted output), and `viaMapReduce.equals(viaAggregation)` compares the two `Map<String, Double>` results for equality — since both computed identical key-value pairs, this evaluates to `true`.

```
orders: cust-A(50,75,25), cust-B(300), cust-C(10,90)

mapReduceStyle:   emit all 6 pairs -> reduce by key -> {cust-A:150, cust-B:300, cust-C:100}
aggregationStyle:  groupingBy+summingDouble in one pass -> {cust-A:150, cust-B:300, cust-C:100}

viaMapReduce.equals(viaAggregation) -> true
```

In a real MongoDB deployment, both `mongoTemplate.mapReduce("orders", mapJs, reduceJs, CustomerTotal.class)` and `mongoTemplate.aggregate(Aggregation.newAggregation(Aggregation.group("customerId").sum("total").as("totalSpent")), "orders", CustomerTotal.class)` can compute the identical grouped-sum result — but map-reduce executes user-supplied JavaScript functions (historically single-threaded and comparatively slow), while the aggregation framework's `$group` stage is implemented natively in the database engine, generally runs significantly faster, and integrates with the rest of the aggregation pipeline stages (like `$match`/`$sort` from the earlier card) far more naturally. This is why virtually all new Spring Data MongoDB code should reach for `Aggregation` rather than `MapReduceOperations`.

## 7. Gotchas & takeaways

> Gotcha: MongoDB has deprecated map-reduce as of MongoDB 5.0, explicitly recommending the aggregation framework for all new development — encountering `mongoTemplate.mapReduce(...)` in a codebase is a signal that code predates this recommendation (or was written without awareness of it), and is a reasonable candidate for migration to the equivalent `Aggregation` pipeline when that code is next touched.

- Map-reduce computes grouped results via two hand-written functions: a map function emitting key/value pairs per document, and a reduce function combining values sharing the same key.
- The aggregation framework's `Aggregation.group(...)` (and other stages) express the same class of computation as a single, built-in, optimized pipeline stage — no custom JavaScript required.
- MongoDB has deprecated map-reduce in favor of the aggregation framework for virtually all use cases it used to serve — new code should use `Aggregation`, not `MapReduceOperations`.
- Recognizing the map/reduce pattern is chiefly useful for reading and migrating existing legacy code, not for writing new Spring Data MongoDB features.
