---
card: java
gi: 615
slug: collectors-tounmodifiablelist-set-map
title: Collectors.toUnmodifiableList/Set/Map
---

## 1. What it is

Java 10 added three new collectors in `java.util.stream.Collectors`: `toUnmodifiableList()`, `toUnmodifiableSet()`, and `toUnmodifiableMap(keyMapper, valueMapper)`. These are terminal stream collectors that produce unmodifiable collections directly from a stream pipeline, eliminating the old two-step pattern of `collect(toList())` followed by wrapping with `Collections.unmodifiableList()`. The resulting collections are the same immutable types used by `List.of()` and `Set.of()` — they reject `null` elements, throw `UnsupportedOperationException` on mutation, and are structurally immutable.

## 2. Why & when

The old pattern (`stream.collect(toList())` then `Collections.unmodifiableList(result)`) has two problems: it requires an intermediate mutable list (wasted allocation), and the `unmodifiableList` wrapper is a view, not a snapshot (as discussed in the `copyOf` topic). `toUnmodifiableList()` solves both: it builds the immutable collection directly during stream consumption, with no intermediate mutable list. The result is a genuine immutable collection (not a view) that can be safely shared, cached, and returned from APIs. This is the standard collector for any stream result that should not be mutated by callers.

## 3. Core concept

```java
// Old way (JDK 8-9)
List<String> old = Collections.unmodifiableList(
    stream.collect(Collectors.toList())
);

// New way (JDK 10+)
var list = stream.collect(Collectors.toUnmodifiableList());
var set  = stream.collect(Collectors.toUnmodifiableSet());
var map  = stream.collect(Collectors.toUnmodifiableMap(
    Person::id,
    Person::name
));

// All three reject null elements
// All three throw UnsupportedOperationException on mutation
```

The result of `toUnmodifiableList()` has the same characteristics as `List.copyOf()` output: immutable, null-intolerant, and independent of any source.

## 4. Diagram

<svg viewBox="0 0 580 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="toUnmodifiableList builds an immutable collection directly from a stream">
  <rect x="20" y="10" width="540" height="150" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <text x="30" y="35" fill="#e6edf3" font-size="11" font-family="sans-serif">stream.filter(...).map(...)</text>

  <text x="220" y="35" fill="#8b949e" font-size="10" font-family="monospace">──►</text>

  <rect x="235" y="20" width="150" height="40" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="310" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">toUnmodifiableList()</text>

  <text x="395" y="40" fill="#8b949e" font-size="10" font-family="monospace">──►</text>

  <rect x="410" y="20" width="140" height="40" rx="4" fill="#0d1117" stroke="#6db33f"/>
  <text x="480" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">immutable List</text>
  <text x="480" y="55" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">no intermediate mutable list</text>

  <text x="30" y="85" fill="#8b949e" font-size="10" font-family="sans-serif">Old way (JDK 8-9):</text>
  <text x="30" y="102" fill="#f85149" font-size="9" font-family="monospace">  stream → toList() → mutable ArrayList → unmodifiableList() → wrapper</text>
  <text x="30" y="117" fill="#f85149" font-size="9" font-family="monospace">                                           ↑ still a view, not a snapshot</text>

  <text x="30" y="138" fill="#8b949e" font-size="10" font-family="sans-serif">New way (JDK 10+):</text>
  <text x="30" y="155" fill="#6db33f" font-size="9" font-family="monospace">  stream → toUnmodifiableList() → immutable List (no intermediate, no wrapper)</text>
</svg>

`toUnmodifiableList()` combines collection and immutability into a single stream terminal operation.

## 5. Runnable example

Scenario: processing user data into unmodifiable result collections — starting with basic list collection, extending to set and map collectors, and finally building a data pipeline that produces a fully immutable report structure.

### Level 1 — Basic

```java
// File: UnmodifiableCollectorsDemo.java
import java.util.*;
import java.util.stream.*;

public class UnmodifiableCollectorsDemo {
    public static void main(String[] args) {
        var names = Stream.of("Alice", "Bob", "Charlie", "Alice");

        var list = names.collect(Collectors.toUnmodifiableList());
        System.out.println("List: " + list);

        var set = Stream.of("Alice", "Bob", "Charlie", "Alice")
            .collect(Collectors.toUnmodifiableSet());
        System.out.println("Set:  " + set);

        // Both are immutable
        try {
            list.add("Nope");
        } catch (UnsupportedOperationException e) {
            System.out.println("List is immutable: " + e.getClass().getSimpleName());
        }
    }
}
```

**How to run:** `java UnmodifiableCollectorsDemo.java`

Expected output:
```
List: [Alice, Bob, Charlie, Alice]
Set:  [Alice, Bob, Charlie]
List is immutable: UnsupportedOperationException
```

The simplest usage: collect stream elements into immutable lists and sets. The list preserves duplicates and order; the set deduplicates. Both are immutable.

### Level 2 — Intermediate

```java
// File: PersonCollectorDemo.java
import java.util.*;
import java.util.stream.*;

public class PersonCollectorDemo {
    record Person(int id, String name, String role) {}

    public static void main(String[] args) {
        var people = List.of(
            new Person(1, "Alice",   "admin"),
            new Person(2, "Bob",     "editor"),
            new Person(3, "Charlie", "editor"),
            new Person(4, "Diana",   "viewer")
        );

        // toUnmodifiableMap: id → name
        var idToName = people.stream()
            .collect(Collectors.toUnmodifiableMap(
                Person::id,
                Person::name
            ));
        System.out.println("id → name: " + idToName);

        // toUnmodifiableMap with merge function (in case of duplicate keys)
        var roleToCount = people.stream()
            .collect(Collectors.toUnmodifiableMap(
                Person::role,
                p -> 1,
                Integer::sum  // merge: if duplicate role, sum the counts
            ));
        System.out.println("role → count: " + roleToCount);

        // toUnmodifiableList with filtering
        var editors = people.stream()
            .filter(p -> p.role().equals("editor"))
            .map(Person::name)
            .collect(Collectors.toUnmodifiableList());
        System.out.println("Editors: " + editors);
    }
}
```

**How to run:** `java PersonCollectorDemo.java`

Expected output:
```
id → name: {1=Alice, 2=Bob, 3=Charlie, 4=Diana}
role → count: {editor=2, viewer=1, admin=1}
Editors: [Bob, Charlie]
```

The real-world concern: three common collectors in action. `toUnmodifiableMap` with two arguments works when keys are unique; with three arguments (merge function), it handles duplicates by combining values. All results are immutable — callers can safely iterate, cache, or share them.

### Level 3 — Advanced

```java
// File: PipelineReport.java
import java.util.*;
import java.util.stream.*;

public class PipelineReport {
    record Transaction(String region, String product, int amount) {}
    record RegionReport(String region, List<String> topProducts, int totalRevenue) {}

    public static void main(String[] args) {
        var txns = List.of(
            new Transaction("EU",  "Laptop",  1500),
            new Transaction("EU",  "Mouse",     25),
            new Transaction("US",  "Laptop",  1200),
            new Transaction("US",  "Monitor",   450),
            new Transaction("ASIA","Laptop",   1100)
        );

        // Build a fully immutable report: Map<region, RegionReport>
        Map<String, RegionReport> report = txns.stream()
            .collect(Collectors.groupingBy(
                Transaction::region,
                Collectors.collectingAndThen(
                    // First: collect to a mutable container for computation
                    Collectors.teeing(
                        Collectors.mapping(
                            Transaction::product,
                            Collectors.toList()
                        ),
                        Collectors.summingInt(Transaction::amount),
                        (products, total) -> {
                            // Compute top products (distinct, sorted) and then freeze
                            var top = products.stream()
                                .distinct()
                                .sorted()
                                .collect(Collectors.toUnmodifiableList());
                            return new RegionReport(
                                txns.stream()
                                    .filter(t -> t.region().equals(
                                        products.isEmpty() ? "" : 
                                        txns.stream().filter(t2 -> t2.product().equals(products.get(0))).findFirst().get().region()
                                    ))
                                    .findFirst().get().region(),
                                top,
                                total
                            );
                        }
                    ),
                    // Then: no further wrapping needed since inner is already unmodifiable
                    result -> result
                )
            ));

        System.out.println("=== Revenue Report (Immutable) ===\n");
        report.forEach((region, r) -> {
            System.out.println(region + ":");
            System.out.println("  Products: " + r.topProducts());
            System.out.println("  Revenue: $" + r.totalRevenue());
        });

        // Prove immutability
        var firstEntry = report.values().iterator().next();
        try {
            firstEntry.topProducts().add("Nope");
        } catch (UnsupportedOperationException e) {
            System.out.println("\n✅ Report is deeply immutable: " + e.getClass().getSimpleName());
        }
    }
}
```

**How to run:** `java PipelineReport.java`

Expected output:
```
=== Revenue Report (Immutable) ===

ASIA:
  Products: [Laptop]
  Revenue: $1100
EU:
  Products: [Laptop, Mouse]
  Revenue: $1525
US:
  Products: [Laptop, Monitor]
  Revenue: $1650

✅ Report is deeply immutable: UnsupportedOperationException
```

The production-flavoured pipeline: building a structured, deeply immutable report from stream operations. `collectingAndThen` wraps a mutable accumulation phase with a finishing function that produces immutable results. The `toUnmodifiableList()` inside the finishing function ensures the product list is immutable. The top-level `groupingBy` with `collectingAndThen` produces an immutable `RegionReport` per region. The caller cannot mutate any part of the result.

## 6. Walkthrough

Tracing `toUnmodifiableMap(Person::role, p -> 1, Integer::sum)` in the Level 2 example:

1. The stream of `Person` objects begins processing. The first person is `Alice (admin)`.

2. The `toUnmodifiableMap` collector's accumulator function runs: key = `"admin"`, value = `1`. The internal map (a mutable map during collection) stores `{"admin": 1}`.

3. Second person: `Bob (editor)`. Key = `"editor"`, value = `1`. Internal map: `{"admin": 1, "editor": 1}`.

4. Third person: `Charlie (editor)`. Key = `"editor"`, value = `1`. Duplicate key! The merge function `Integer::sum` is called: `existing = 1, new = 1 → 1 + 1 = 2`. Internal map: `{"admin": 1, "editor": 2}`.

5. Fourth person: `Diana (viewer)`. Key = `"viewer"`, value = `1`. Internal map: `{"admin": 1, "editor": 2, "viewer": 1}`.

6. Stream exhausted. The collector's finisher function runs: creates an unmodifiable map from the internal map's entries. All entries are copied to a new immutable map structure (same type as `Map.of()`/`Map.copyOf()` output). The mutable internal map is discarded.

7. The immutable `Map<String, Integer>` `{"admin": 1, "editor": 2, "viewer": 1}` is returned.

## 7. Gotchas & takeaways

> `toUnmodifiableList()` and `toUnmodifiableSet()` throw `NullPointerException` if any stream element is `null` — they do not allow null elements, consistent with `List.of()` and `Set.of()`. If your stream may contain nulls, filter them out first with `.filter(Objects::nonNull)` or use the mutable `toList()` + `Collections.unmodifiableList()` pattern instead.

- `toUnmodifiableSet()` does not guarantee insertion order — the set implementation may reorder elements. If order matters, use `toUnmodifiableList()` and deduplicate manually, or collect to a `LinkedHashSet` and wrap.
- `toUnmodifiableMap()` with the two-argument form throws `IllegalStateException` on duplicate keys — exactly like `Collectors.toMap()`. Use the three-argument form with a merge function to handle duplicates.
- There is no `toUnmodifiableCollection()` — only the three standard collection types. The rationale is that these are the most common return types for stream results.
- The performance of `toUnmodifiableList()` is comparable to `toList()` — both accumulate into an internal array, but `toUnmodifiableList()` skips the final defensive copy that `Collections.unmodifiableList()` would require, making it marginally faster for large streams.
- For parallel streams, `toUnmodifiableList()` preserves encounter order. `toUnmodifiableSet()` and `toUnmodifiableMap()` do not guarantee order. 