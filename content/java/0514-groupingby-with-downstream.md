---
card: java
gi: 514
slug: groupingby-with-downstream
title: groupingBy with downstream
---

## 1. What it is

`Collectors.groupingBy(classifier, downstream)` is the two-argument overload of `groupingBy` that lets you control what happens *within* each group, instead of always collecting into a plain `List<T>`. The `downstream` argument is itself a `Collector`, applied to each group's elements — `Collectors.counting()` to get a count per group, `Collectors.summingInt(...)` to sum a field per group, `Collectors.mapping(...)` to transform elements before collecting them, or even a nested `groupingBy` to group within a group.

## 2. Why & when

Plain `groupingBy(classifier)` always gives you `Map<K, List<T>>`. Often what you actually want is a per-group *aggregate* — how many elements per group, the total or average of some field per group, or a further-processed version of each group's elements — not the raw grouped list itself. Rather than grouping into lists and then running a second pass over each list to compute the aggregate, a downstream collector computes it directly as part of the same single grouping pass, and produces a more directly useful result type like `Map<K, Long>` or `Map<K, Double>`.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

record Sale(String region, double amount) {}

List<Sale> sales = List.of(
        new Sale("West", 100.0), new Sale("East", 50.0), new Sale("West", 75.0));

Map<String, Long> countByRegion = sales.stream()
        .collect(Collectors.groupingBy(Sale::region, Collectors.counting()));
// {West=2, East=1}

Map<String, Double> totalByRegion = sales.stream()
        .collect(Collectors.groupingBy(Sale::region, Collectors.summingDouble(Sale::amount)));
// {West=175.0, East=50.0}
```

The downstream collector determines the *value type* of the resulting map — `counting()` gives `Long` values, `summingDouble(...)` gives `Double` values, and so on, all computed within each group during the same pass.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="groupingBy with a downstream collector computes a per-group aggregate instead of a raw list">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="20" width="100" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="70" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">West, 100</text>
  <rect x="130" y="20" width="100" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="180" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">East, 50</text>
  <rect x="240" y="20" width="100" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="290" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">West, 75</text>
  <text x="180" y="65" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">groupingBy(region, summingDouble(amount))</text>
  <line x1="180" y1="50" x2="180" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowGD)"/>
  <rect x="60" y="85" width="120" height="40" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="120" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">West -&gt; 175.0</text>
  <rect x="200" y="85" width="120" height="40" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="260" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">East -&gt; 50.0</text>
  <defs><marker id="arrowGD" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Instead of `{West=[Sale,Sale], East=[Sale]}`, the downstream collector directly produces the *sum* per group: `{West=175.0, East=50.0}`.

## 5. Runnable example

Scenario: analyzing employee data across departments — evolved from a plain per-group count, through per-group sums, to a version chaining multiple downstream collectors together (grouping, then mapping, then joining) for a formatted report.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class GroupingDownstreamCount {
    record Employee(String name, String department) {}

    public static void main(String[] args) {
        List<Employee> employees = List.of(
                new Employee("Alice", "Engineering"),
                new Employee("Bob", "Sales"),
                new Employee("Carol", "Engineering"),
                new Employee("Dave", "Engineering")
        );

        Map<String, Long> countByDept = employees.stream()
                .collect(Collectors.groupingBy(Employee::department, Collectors.counting()));

        new TreeMap<>(countByDept).forEach((dept, count) -> System.out.println(dept + ": " + count));
    }
}
```

**How to run:** `java GroupingDownstreamCount.java`

Expected output:
```
Engineering: 3
Sales: 1
```

`Collectors.counting()` as the downstream collector produces the *count* of elements in each group directly, so `groupingBy` returns `Map<String, Long>` (department to count) instead of `Map<String, List<Employee>>` — no need for a separate `.mapValues(List::size)`-style step afterward, which `Map` doesn't even directly support.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class GroupingDownstreamSum {
    record Employee(String name, String department, double salary) {}

    public static void main(String[] args) {
        List<Employee> employees = List.of(
                new Employee("Alice", "Engineering", 95000),
                new Employee("Bob", "Sales", 70000),
                new Employee("Carol", "Engineering", 105000),
                new Employee("Dave", "Engineering", 88000)
        );

        Map<String, Double> totalSalaryByDept = employees.stream()
                .collect(Collectors.groupingBy(Employee::department, Collectors.summingDouble(Employee::salary)));

        new TreeMap<>(totalSalaryByDept).forEach((dept, total) ->
                System.out.printf("%s: $%.2f%n", dept, total));
    }
}
```

**How to run:** `java GroupingDownstreamSum.java`

Expected output:
```
Engineering: $288000.00
Sales: $70000.00
```

The real-world concern this adds: a per-group aggregate that's a computed number, not just a count. `Collectors.summingDouble(Employee::salary)` sums the `salary` field of every employee within each department, giving `Engineering`'s total payroll (`95000 + 105000 + 88000 = 288000`) directly, in the same single pass that groups the data.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class GroupingDownstreamChained {
    record Employee(String name, String department, double salary) {}

    public static void main(String[] args) {
        List<Employee> employees = List.of(
                new Employee("Alice", "Engineering", 95000),
                new Employee("Bob", "Sales", 70000),
                new Employee("Carol", "Engineering", 105000),
                new Employee("Dave", "Engineering", 88000)
        );

        // Group by department, then within each group: map to "name ($salary)" strings, then join them.
        Map<String, String> rosterByDept = employees.stream()
                .collect(Collectors.groupingBy(
                        Employee::department,
                        Collectors.mapping(
                                e -> e.name() + " ($" + (int) e.salary() + ")",
                                Collectors.joining(", "))));

        new TreeMap<>(rosterByDept).forEach((dept, roster) -> System.out.println(dept + ": " + roster));
    }
}
```

**How to run:** `java GroupingDownstreamChained.java`

Expected output:
```
Engineering: Alice ($95000), Carol ($105000), Dave ($88000)
Sales: Bob ($70000)
```

This chains **two** downstream collectors: `Collectors.mapping(transformFunction, furtherDownstream)` first transforms each `Employee` within a group into a formatted `"name ($salary)"` string, then feeds those strings into `Collectors.joining(", ")` to combine them into one readable roster string per department — all within the single `groupingBy` pass, producing `Map<String, String>` directly, with no separate post-processing step needed after grouping.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Four employees are defined: three in `"Engineering"` (`Alice`, `Carol`, `Dave`) and one in `"Sales"` (`Bob`).

`employees.stream().collect(Collectors.groupingBy(Employee::department, Collectors.mapping(e -> e.name() + " ($" + (int) e.salary() + ")", Collectors.joining(", "))))` processes each employee. For `Alice` (`Engineering`, `95000`): the classifier gives key `"Engineering"`, no existing group, a new `mapping`+`joining` downstream accumulator is created for it. The `mapping` collector first transforms `Alice` into `"Alice ($95000)"` (note `(int) e.salary()` truncates `95000.0` to `95000`), then feeds that string into the inner `joining(", ")` accumulator — the running joined string for `"Engineering"` becomes `"Alice ($95000)"`.

For `Bob` (`Sales`, `70000`): key `"Sales"`, new group created, transformed to `"Bob ($70000)"`, joined string becomes `"Bob ($70000)"`.

For `Carol` (`Engineering`, `105000`): key `"Engineering"` already exists. Transformed to `"Carol ($105000)"`, and the inner `joining` accumulator appends it with the `", "` delimiter to the existing `"Alice ($95000)"`, producing `"Alice ($95000), Carol ($105000)"`.

For `Dave` (`Engineering`, `88000`): key `"Engineering"` exists. Transformed to `"Dave ($88000)"`, appended: `"Alice ($95000), Carol ($105000), Dave ($88000)"`.

```
Alice (Eng, 95000)  -> new group "Engineering", joined = "Alice ($95000)"
Bob (Sales, 70000)  -> new group "Sales",       joined = "Bob ($70000)"
Carol (Eng, 105000) -> existing "Engineering",  joined = "Alice ($95000), Carol ($105000)"
Dave (Eng, 88000)   -> existing "Engineering",  joined = "Alice ($95000), Carol ($105000), Dave ($88000)"
```

The final `rosterByDept` map has `"Engineering"` mapped to the fully joined three-name roster string, and `"Sales"` mapped to just `"Bob ($70000)"`. `new TreeMap<>(...)` orders the departments alphabetically, and the `forEach` prints each department's complete, formatted roster on one line.

## 7. Gotchas & takeaways

> `Collectors.mapping(transform, downstream)` is itself a downstream collector — it can be nested inside `groupingBy`'s downstream argument to first transform each group's elements before further collecting them, as shown chaining `mapping` and `joining` together in Level 3. Many `Collectors` methods are designed to compose this way, letting you build fairly sophisticated per-group processing entirely declaratively, without a manual loop.

- `Collectors.groupingBy(classifier, downstream)` computes a per-group aggregate directly, instead of always producing `Map<K, List<T>>`.
- `Collectors.counting()`, `summingInt`/`summingDouble`/`summingLong`, `averagingInt`/etc., and `summarizingInt`/etc. are common downstream collectors for per-group numeric aggregates.
- `Collectors.mapping(transform, downstream)` transforms each group's elements before passing them to another downstream collector — useful for chaining multiple processing steps within a single grouping pass.
- Nesting collectors this way computes the entire result in one traversal of the source data, rather than grouping into lists first and then running a separate pass to aggregate each list afterward.
- When the raw grouped `List<T>` genuinely is what you need (not an aggregate), the plain one-argument `groupingBy(classifier)` (see [[groupingby]]) remains the simpler, more direct choice.
