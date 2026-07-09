---
card: java
gi: 521
slug: minby-maxby
title: minBy / maxBy
---

## 1. What it is

`Collectors.minBy(comparator)` and `Collectors.maxBy(comparator)` are collectors that find the smallest or largest element according to a `Comparator`, returning `Optional<T>` — the collector equivalent of `Stream.min`/`Stream.max` (see [[min-max]]), but packaged as a `Collector` so they can be used as a `groupingBy` downstream, where the stream-level `min`/`max` methods cannot be used directly.

## 2. Why & when

`Stream.min`/`Stream.max` work great for finding the extreme element of a *whole* stream. But when you need the extreme element *within each group* of a `groupingBy` operation — the highest-paid employee per department, the cheapest product per category — `Stream.min`/`Stream.max` can't be plugged into `groupingBy`'s downstream position, since that position requires a `Collector`. `Collectors.minBy`/`maxBy` fill exactly that gap.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

record Employee(String department, String name, double salary) {}

List<Employee> employees = List.of(
        new Employee("Engineering", "Alice", 95000),
        new Employee("Engineering", "Bob", 105000),
        new Employee("Sales", "Carol", 70000));

Map<String, Optional<Employee>> topEarnerByDept = employees.stream()
        .collect(Collectors.groupingBy(
                Employee::department,
                Collectors.maxBy(Comparator.comparing(Employee::salary))));
// {Engineering=Optional[Bob], Sales=Optional[Carol]}
```

`maxBy`/`minBy` scan each group's elements and return the extreme one wrapped in `Optional`, exactly like `Stream.max`/`Stream.min` do for a whole stream.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="maxBy as a groupingBy downstream finds the highest-value element within each group">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="20" width="140" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="90" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Alice, $95k</text>
  <rect x="170" y="20" width="140" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="240" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Bob, $105k</text>
  <text x="165" y="65" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">groupingBy(dept, maxBy(salary))</text>
  <line x1="165" y1="50" x2="165" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowMB)"/>
  <rect x="90" y="85" width="150" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="165" y="105" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Eng -&gt; Bob ($105k)</text>
  <defs><marker id="arrowMB" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Within the `Engineering` group, `Bob` has the higher salary, so `maxBy` selects him as that group's result.

## 5. Runnable example

Scenario: identifying top performers within each sales region — evolved from a plain per-group maximum, through unwrapping the `Optional` results into a clean map, to a version finding both the best and worst performer per group at once.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class MaxByBasic {
    record SalesRep(String region, String name, double sales) {}

    public static void main(String[] args) {
        List<SalesRep> reps = List.of(
                new SalesRep("West", "Alice", 120000),
                new SalesRep("West", "Bob", 95000),
                new SalesRep("East", "Carol", 110000)
        );

        Map<String, Optional<SalesRep>> topByRegion = reps.stream()
                .collect(Collectors.groupingBy(
                        SalesRep::region,
                        Collectors.maxBy(Comparator.comparing(SalesRep::sales))));

        new TreeMap<>(topByRegion).forEach((region, top) ->
                top.ifPresent(rep -> System.out.println(region + ": " + rep.name() + " ($" + rep.sales() + ")")));
    }
}
```

**How to run:** `java MaxByBasic.java`

Expected output:
```
East: Carol ($110000.0)
West: Alice ($120000.0)
```

`Collectors.maxBy(Comparator.comparing(SalesRep::sales))` finds the highest-`sales` rep within each region group. `West` has two reps; `Alice` (`120000`) beats `Bob` (`95000`), so `Alice` is `West`'s result. `East` has only `Carol`, so she's automatically the max of her one-element group.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class MaxByUnwrapped {
    record SalesRep(String region, String name, double sales) {}

    public static void main(String[] args) {
        List<SalesRep> reps = List.of(
                new SalesRep("West", "Alice", 120000),
                new SalesRep("West", "Bob", 95000),
                new SalesRep("East", "Carol", 110000)
        );

        // collectingAndThen unwraps the Optional immediately -- safe here since every group has >=1 element.
        Map<String, SalesRep> topByRegion = reps.stream()
                .collect(Collectors.groupingBy(
                        SalesRep::region,
                        Collectors.collectingAndThen(
                                Collectors.maxBy(Comparator.comparing(SalesRep::sales)),
                                Optional::get)));

        new TreeMap<>(topByRegion).forEach((region, top) ->
                System.out.println(region + " top performer: " + top.name()));
    }
}
```

**How to run:** `java MaxByUnwrapped.java`

Expected output:
```
East top performer: Carol
West top performer: Alice
```

The real-world concern this adds: `Optional<SalesRep>` per group is awkward to use downstream if every group is *guaranteed* non-empty (which is always true for `groupingBy`, since a group only exists if at least one element produced that key). `Collectors.collectingAndThen(maxBy(...), Optional::get)` (see [[collectingandthen]]) unwraps the `Optional` immediately, producing a cleaner `Map<String, SalesRep>` directly — safe here specifically because `groupingBy` never creates an empty group.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class MinMaxByCombined {
    record SalesRep(String region, String name, double sales) {}
    record RegionSpread(SalesRep top, SalesRep bottom) {}

    public static void main(String[] args) {
        List<SalesRep> reps = List.of(
                new SalesRep("West", "Alice", 120000),
                new SalesRep("West", "Bob", 95000),
                new SalesRep("West", "Eve", 80000),
                new SalesRep("East", "Carol", 110000),
                new SalesRep("East", "Dave", 60000)
        );

        Comparator<SalesRep> bySales = Comparator.comparing(SalesRep::sales);

        // teeing combines minBy and maxBy results into one RegionSpread per group, in a single pass.
        Map<String, RegionSpread> spreadByRegion = reps.stream()
                .collect(Collectors.groupingBy(
                        SalesRep::region,
                        Collectors.teeing(
                                Collectors.collectingAndThen(Collectors.maxBy(bySales), Optional::get),
                                Collectors.collectingAndThen(Collectors.minBy(bySales), Optional::get),
                                RegionSpread::new)));

        new TreeMap<>(spreadByRegion).forEach((region, spread) ->
                System.out.printf("%s: top=%s ($%.0f), bottom=%s ($%.0f), gap=$%.0f%n",
                        region, spread.top().name(), spread.top().sales(),
                        spread.bottom().name(), spread.bottom().sales(),
                        spread.top().sales() - spread.bottom().sales()));
    }
}
```

**How to run:** `java MinMaxByCombined.java`

Expected output:
```
East: top=Carol ($110000), bottom=Dave ($60000), gap=$50000
West: top=Alice ($120000), bottom=Eve ($80000), gap=$40000
```

This finds **both** the top and bottom performer per region in a single pass, using `Collectors.teeing(...)` (see [[summingint-averagingint]]) to run `maxBy` and `minBy` simultaneously over each group's elements, combining their two results with `RegionSpread::new` — reporting the full performance range within each region, including the gap between the best and worst performer.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Five reps are defined: three for `"West"` (`Alice` $120k, `Bob` $95k, `Eve` $80k) and two for `"East"` (`Carol` $110k, `Dave` $60k).

`reps.stream().collect(Collectors.groupingBy(SalesRep::region, Collectors.teeing(...)))` processes each rep, grouping by `region`. Within each group, `Collectors.teeing(...)` maintains two independent downstream accumulators simultaneously: one running a `maxBy(bySales)` (wrapped in `collectingAndThen` with `Optional::get`), one running a `minBy(bySales)`.

For `"West"`'s three reps: the `maxBy` accumulator compares `Alice` ($120k), `Bob` ($95k), `Eve` ($80k) and settles on `Alice` as the highest. The `minBy` accumulator compares the same three and settles on `Eve` as the lowest.

For `"East"`'s two reps: the `maxBy` accumulator compares `Carol` ($110k) and `Dave` ($60k), settling on `Carol`. The `minBy` accumulator settles on `Dave`.

```
West: reps = Alice($120k), Bob($95k), Eve($80k)
  maxBy -> Alice ($120k)      minBy -> Eve ($80k)

East: reps = Carol($110k), Dave($60k)
  maxBy -> Carol ($110k)      minBy -> Dave ($60k)
```

Once each group's elements are fully processed, `teeing`'s merge function, `RegionSpread::new`, is called once per group with both results unwrapped from their `Optional`s (via the nested `collectingAndThen(..., Optional::get)`): for `"West"`, `new RegionSpread(Alice, Eve)`; for `"East"`, `new RegionSpread(Carol, Dave)`. `new TreeMap<>(...)` orders the regions alphabetically, and the `forEach` prints each region's top performer, bottom performer, and the sales gap between them — `"East"`'s gap is `110000 - 60000 = 50000`, `"West"`'s is `120000 - 80000 = 40000`.

## 7. Gotchas & takeaways

> `Collectors.maxBy`/`minBy` always return `Optional<T>`, even as a `groupingBy` downstream where every group is guaranteed to have at least one element (since a `groupingBy` key only ever exists because some element produced it). Unwrapping with `.get()` directly (as done via `collectingAndThen` in Levels 2 and 3) is safe *specifically* in this guaranteed-non-empty context — calling `.get()` on a genuinely empty `Optional` elsewhere would throw `NoSuchElementException`, so don't reach for this pattern outside a context where non-emptiness is truly guaranteed.

- `Collectors.maxBy(comparator)`/`minBy(comparator)` find the largest/smallest element per group, when used as a `groupingBy` downstream — the collector-world equivalent of `Stream.max`/`Stream.min`.
- Both return `Optional<T>`, since the general `Collector` contract must account for the possibility of an empty input, even though `groupingBy` groups are never actually empty in practice.
- `Collectors.collectingAndThen(maxBy(...), Optional::get)` is a common pattern to unwrap the `Optional` immediately when working within a `groupingBy` context where emptiness is impossible.
- `Collectors.teeing(...)` lets you compute both a `maxBy` and a `minBy` (or any two independent aggregates) per group in a single traversal, rather than two separate `groupingBy` calls.
- For a whole-stream (not per-group) minimum or maximum, `Stream.min`/`Stream.max` (see [[min-max]]) remain simpler and more direct than wrapping the same logic in `Collectors.minBy`/`maxBy`.
