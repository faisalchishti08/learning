---
card: java
gi: 518
slug: mapping
title: mapping()
---

## 1. What it is

`Collectors.mapping(mapper, downstream)` is a collector that first transforms each element with `mapper`, then feeds the transformed results into another collector, `downstream`. It's essentially `Stream.map(...)` expressed as a `Collector` rather than an intermediate stream operation — which matters specifically because it lets a transformation happen *inside* a `groupingBy`'s downstream position, where a plain `.map(...)` call on the outer stream can't reach.

## 2. Why & when

Without `mapping`, if you wanted each group's elements transformed before collecting them, you'd need to `.map(...)` the *entire* stream first, before grouping — but that only works if the transformed value still contains whatever field the classifier needs to group by. If the classifier needs the original object's field, but you want each group's *collected* elements to be something *other* than the original object, `mapping` is what lets you do both: group by a property of the original element, while collecting a transformed version of it into each group.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

record Employee(String department, String name) {}

List<Employee> employees = List.of(
        new Employee("Engineering", "Alice"), new Employee("Engineering", "Bob"), new Employee("Sales", "Carol"));

Map<String, List<String>> namesByDept = employees.stream()
        .collect(Collectors.groupingBy(
                Employee::department,
                Collectors.mapping(Employee::name, Collectors.toList())));
// {Engineering=[Alice, Bob], Sales=[Carol]} -- grouped by department, but each group holds just names
```

`mapping` transforms each element (`Employee` to `String` name) before the inner `toList()` collector gathers the transformed values — the classifier still sees the original `Employee` to determine the group.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="mapping transforms elements before an inner collector gathers the transformed results">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="20" width="140" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="90" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Employee(Eng, Alice)</text>
  <rect x="170" y="20" width="140" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="240" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Employee(Eng, Bob)</text>
  <text x="165" y="65" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">groupingBy(dept, mapping(name, toList()))</text>
  <line x1="165" y1="50" x2="165" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowMP)"/>
  <rect x="90" y="85" width="150" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="165" y="105" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Eng -&gt; [Alice, Bob]</text>
  <defs><marker id="arrowMP" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Grouping still happens by the original `Employee`'s `department`, but each group's collected values are just the extracted `name` strings, not the full `Employee` objects.

## 5. Runnable example

Scenario: building per-category product name listings from a catalog — evolved from a basic name-extraction-while-grouping, through combining `mapping` with `joining` for a formatted per-group string, to a version chaining `mapping` with a numeric downstream collector.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class MappingBasic {
    record Product(String category, String name, double price) {}

    public static void main(String[] args) {
        List<Product> products = List.of(
                new Product("Electronics", "Laptop", 999.0),
                new Product("Electronics", "Mouse", 25.0),
                new Product("Books", "Java Guide", 40.0)
        );

        Map<String, List<String>> namesByCategory = products.stream()
                .collect(Collectors.groupingBy(
                        Product::category,
                        Collectors.mapping(Product::name, Collectors.toList())));

        new TreeMap<>(namesByCategory).forEach((cat, names) -> System.out.println(cat + ": " + names));
    }
}
```

**How to run:** `java MappingBasic.java`

Expected output:
```
Books: [Java Guide]
Electronics: [Laptop, Mouse]
```

Grouping happens by `category` (needing the original `Product`), but `Collectors.mapping(Product::name, Collectors.toList())` transforms each product down to just its `name` before collecting — the result holds lists of plain product names, not full `Product` objects, per category.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class MappingWithJoining {
    record Product(String category, String name, double price) {}

    public static void main(String[] args) {
        List<Product> products = List.of(
                new Product("Electronics", "Laptop", 999.0),
                new Product("Electronics", "Mouse", 25.0),
                new Product("Books", "Java Guide", 40.0),
                new Product("Books", "Streams Deep Dive", 35.0)
        );

        Map<String, String> catalogByCategory = products.stream()
                .collect(Collectors.groupingBy(
                        Product::category,
                        Collectors.mapping(Product::name, Collectors.joining(", "))));

        new TreeMap<>(catalogByCategory).forEach((cat, listing) -> System.out.println(cat + ": " + listing));
    }
}
```

**How to run:** `java MappingWithJoining.java`

Expected output:
```
Books: Java Guide, Streams Deep Dive
Electronics: Laptop, Mouse
```

The real-world concern this adds: instead of a `List<String>` per category, `mapping`'s downstream is now `Collectors.joining(", ")` instead of `toList()` — the mapped product names within each category are joined directly into one readable `String`, producing `Map<String, String>` (category to a formatted listing) rather than `Map<String, List<String>>`.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class MappingWithSum {
    record Product(String category, String name, double price, int stock) {}

    public static void main(String[] args) {
        List<Product> products = List.of(
                new Product("Electronics", "Laptop", 999.0, 5),
                new Product("Electronics", "Mouse", 25.0, 40),
                new Product("Books", "Java Guide", 40.0, 12),
                new Product("Books", "Streams Deep Dive", 35.0, 8)
        );

        // Map each product to its inventory VALUE (price * stock), then sum that per category.
        Map<String, Double> inventoryValueByCategory = products.stream()
                .collect(Collectors.groupingBy(
                        Product::category,
                        Collectors.mapping(
                                p -> p.price() * p.stock(),
                                Collectors.summingDouble(Double::doubleValue))));

        new TreeMap<>(inventoryValueByCategory).forEach((cat, value) ->
                System.out.printf("%s: $%.2f in inventory%n", cat, value));
    }
}
```

**How to run:** `java MappingWithSum.java`

Expected output:
```
Books: $760.00 in inventory
Electronics: $5995.00 in inventory
```

This chains `mapping` with a numeric downstream collector: each `Product` is first transformed into a *computed* `Double` value (`price * stock`, its total inventory value) via `mapping`'s transform function, and then `Collectors.summingDouble(Double::doubleValue)` sums those computed values within each category — combining a per-element computation with a per-group aggregation in a single `groupingBy` pass.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Four products are defined: two `"Electronics"` (`Laptop`: price `999.0`, stock `5`; `Mouse`: price `25.0`, stock `40`) and two `"Books"` (`Java Guide`: price `40.0`, stock `12`; `Streams Deep Dive`: price `35.0`, stock `8`).

`products.stream().collect(Collectors.groupingBy(Product::category, Collectors.mapping(p -> p.price() * p.stock(), Collectors.summingDouble(Double::doubleValue))))` processes each product. For `Laptop` (`"Electronics"`, `999.0`, `5`): the classifier gives key `"Electronics"`, a new group is created. `mapping`'s transform computes `999.0 * 5 = 4995.0`, and this value is fed to the inner `summingDouble` accumulator — running sum for `"Electronics"` becomes `4995.0`.

For `Mouse` (`"Electronics"`, `25.0`, `40`): existing `"Electronics"` group. Transform computes `25.0 * 40 = 1000.0`, added to the running sum: `4995.0 + 1000.0 = 5995.0`.

For `Java Guide` (`"Books"`, `40.0`, `12`): new group `"Books"`. Transform computes `40.0 * 12 = 480.0`, running sum for `"Books"` becomes `480.0`.

For `Streams Deep Dive` (`"Books"`, `35.0`, `8`): existing `"Books"` group. Transform computes `35.0 * 8 = 280.0`, added: `480.0 + 280.0 = 760.0`.

```
Laptop (Electronics, 999.0 x 5=4995.0)      -> new group "Electronics", sum=4995.0
Mouse (Electronics, 25.0 x 40=1000.0)       -> existing,                sum=4995.0+1000.0=5995.0
Java Guide (Books, 40.0 x 12=480.0)         -> new group "Books",       sum=480.0
Streams Deep Dive (Books, 35.0 x 8=280.0)   -> existing,                sum=480.0+280.0=760.0
```

The final map is `{"Electronics"=5995.0, "Books"=760.0}`. `new TreeMap<>(...)` orders alphabetically, and the `forEach` prints `"Books: $760.00 in inventory"` then `"Electronics: $5995.00 in inventory"` — the total dollar value of stock on hand in each category, computed entirely within the single `groupingBy` traversal.

## 7. Gotchas & takeaways

> `mapping`'s transform function runs on the **original** stream element (`Product`, with all its fields), even though the classifier that decides the group might use a *different* field — the two functions (classifier and `mapping`'s transform) are independent, each free to look at whatever part of the element they need. This is exactly what makes `mapping` useful: you're not limited to grouping by the same field you're extracting for collection.

- `Collectors.mapping(transform, downstream)` transforms each element before an inner collector gathers the transformed results — a `Collector`-level equivalent of `Stream.map(...)`.
- Its main use is as a `groupingBy` downstream argument, letting you group by one property of an element while collecting a *different*, transformed property (or computed value) per group.
- `mapping` can chain with any downstream collector — `toList()`, `joining()`, `summingDouble()`, or even a nested `groupingBy` — for arbitrarily composed per-group processing.
- The classifier (deciding the group) and the `mapping` transform (deciding what's collected) both see the full original element independently — they don't have to relate to each other.
- For simple cases where the whole stream (not just each group) needs transforming before any grouping happens, a plain `.map(...)` before `.collect(Collectors.groupingBy(...))` is simpler — reach for `mapping` specifically when the classifier needs the *original*, untransformed element.
