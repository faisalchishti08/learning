---
card: java
gi: 651
slug: collectors-teeing
title: Collectors.teeing()
---

## 1. What it is

`Collectors.teeing(Collector<T,?,R1> downstream1, Collector<T,?,R2> downstream2, BiFunction<R1,R2,R> merger)`, added in **Java 12**, lets a single stream feed **two collectors at once**, then combines their two results into one final result with a merge function. The name comes from a plumbing "tee" fitting that splits one pipe into two. Every element of the stream is passed to *both* downstream collectors as the stream is consumed in a single pass; once the stream is exhausted, `merger` is called once with both collectors' final results to produce the overall result.

## 2. Why & when

Before `teeing()`, computing two different aggregates from the same stream — say, both an average and a count, or both a min and a max — meant either collecting the stream into an intermediate `List` first (extra memory, two passes) or writing an awkward custom `Collector` by hand. `teeing()` runs both aggregations in a **single pass** over the stream and hands you both results together, already combined. Reach for it whenever you need two related summary statistics from one stream and want to avoid materializing the data twice or traversing it twice — computing an average alongside a count, a sum alongside a max, or a "matching items" count alongside a "total items" count for a ratio.

## 3. Core concept

```java
List<Integer> numbers = List.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);

double averageOfEvens = numbers.stream()
    .filter(n -> n % 2 == 0)
    .collect(Collectors.teeing(
        Collectors.summingInt(Integer::intValue), // downstream 1
        Collectors.counting(),                     // downstream 2
        (sum, count) -> (double) sum / count        // merger
    ));
// averageOfEvens = (2+4+6+8+10) / 5 = 6.0
```

Both `summingInt` and `counting` see every even number as the stream flows through once; the `merger` `BiFunction` runs exactly once at the end, combining the sum and the count into an average.

## 4. Diagram

<svg viewBox="0 0 600 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A stream tees into two collectors that both process every element, then a merger combines their two results into one">
  <rect x="10" y="80" width="120" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="70" y="107" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">stream</text>

  <line x1="130" y1="102" x2="200" y2="55" stroke="#79c0ff" stroke-width="2" marker-end="url(#t1)"/>
  <line x1="130" y1="102" x2="200" y2="150" stroke="#79c0ff" stroke-width="2" marker-end="url(#t2)"/>

  <rect x="200" y="25" width="170" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="285" y="52" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">downstream1 (sum)</text>

  <rect x="200" y="128" width="170" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="285" y="155" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">downstream2 (count)</text>

  <line x1="370" y1="47" x2="440" y2="90" stroke="#6db33f" stroke-width="2" marker-end="url(#t3)"/>
  <line x1="370" y1="150" x2="440" y2="105" stroke="#6db33f" stroke-width="2" marker-end="url(#t4)"/>

  <rect x="440" y="75" width="150" height="55" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="515" y="98" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">merger(R1, R2)</text>
  <text x="515" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ final result</text>

  <defs>
    <marker id="t1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="t2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="t3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="t4" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

One stream traversal feeds both collectors simultaneously; `merger` runs once, after the stream is fully consumed, to combine `R1` and `R2` into `R`.

## 5. Runnable example

Scenario: analyzing a stream of order amounts — first computing an average with two collectors, then extending to min/max in one pass, then building a richer statistics summary that combines four downstream collectors via nested `teeing()` calls.

### Level 1 — Basic

```java
// File: TeeingBasic.java
import java.util.List;
import java.util.stream.Collectors;

public class TeeingBasic {
    public static void main(String[] args) {
        List<Integer> orderAmounts = List.of(50, 75, 20, 100, 45);

        double average = orderAmounts.stream()
            .collect(Collectors.teeing(
                Collectors.summingInt(Integer::intValue),
                Collectors.counting(),
                (sum, count) -> (double) sum / count
            ));

        System.out.println("Average order amount: " + average);
    }
}
```

**How to run:** `java TeeingBasic.java`

Expected output:
```
Average order amount: 58.0
```

### Level 2 — Intermediate

```java
// File: TeeingMinMax.java
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

public class TeeingMinMax {
    record Range(int min, int max) {}

    public static void main(String[] args) {
        List<Integer> orderAmounts = List.of(50, 75, 20, 100, 45);

        Range range = orderAmounts.stream()
            .collect(Collectors.teeing(
                Collectors.minBy(Integer::compareTo),
                Collectors.maxBy(Integer::compareTo),
                (min, max) -> new Range(min.orElseThrow(), max.orElseThrow())
            ));

        System.out.println("Range: " + range);
    }
}
```

**How to run:** `java TeeingMinMax.java`

Expected output:
```
Range: Range[min=20, max=100]
```

`minBy`/`maxBy` return `Optional<Integer>` because an empty stream has no min or max; the merger unwraps both with `orElseThrow()` since we know the list is non-empty, combining them into one `Range` in a single pass.

### Level 3 — Advanced

```java
// File: TeeingStats.java
import java.util.List;
import java.util.stream.Collectors;

public class TeeingStats {
    record Stats(double average, int min, int max, long count) {}

    public static void main(String[] args) {
        List<Integer> orderAmounts = List.of(50, 75, 20, 100, 45, 60);

        // Nest teeing() calls to combine more than two downstream collectors.
        Stats stats = orderAmounts.stream()
            .collect(Collectors.teeing(
                Collectors.teeing(
                    Collectors.averagingInt(Integer::intValue),
                    Collectors.minBy(Integer::compareTo),
                    (avg, min) -> new Object[]{avg, min}
                ),
                Collectors.teeing(
                    Collectors.maxBy(Integer::compareTo),
                    Collectors.counting(),
                    (max, count) -> new Object[]{max, count}
                ),
                (left, right) -> new Stats(
                    (double) left[0],
                    ((java.util.Optional<Integer>) left[1]).orElseThrow(),
                    ((java.util.Optional<Integer>) right[0]).orElseThrow(),
                    (long) right[1]
                )
            ));

        System.out.println(stats);
    }
}
```

**How to run:** `java TeeingStats.java`

Expected output:
```
Stats[average=58.333333333333336, min=20, max=100, count=6]
```

Level 3 nests `teeing()` inside `teeing()` to combine **four** downstream collectors (average, min, max, count) from a single stream pass — each inner `teeing()` produces an intermediate pair packed into an `Object[]`, and the outer merger unpacks both pairs into one `Stats` record.

## 6. Walkthrough

1. `main` calls `.stream().collect(Collectors.teeing(...))` on `orderAmounts`. The outer `teeing()` is built from two *inner* `teeing()` collectors as its `downstream1` and `downstream2`.
2. The stream engine begins consuming elements one at a time (`50`, `75`, `20`, `100`, `45`, `60`). For **each** element, it feeds that single value into *all four* leaf collectors simultaneously in this one pass: `averagingInt`, `minBy`, `maxBy`, and `counting` — none of them see the whole list at once, each just accumulates state incrementally as elements arrive.
3. After the last element (`60`) is processed, the stream is exhausted and each leaf collector's `finisher` runs: `averagingInt` finishes to `58.33...`, `minBy` finishes to `Optional.of(20)`, `maxBy` finishes to `Optional.of(100)`, `counting` finishes to `6L`.
4. The **inner-left** `teeing()`'s merger runs first: `(avg, min) -> new Object[]{avg, min}` packs `58.33...` and `Optional.of(20)` into a 2-element array — this becomes `left`.
5. The **inner-right** `teeing()`'s merger runs: `(max, count) -> new Object[]{max, count}` packs `Optional.of(100)` and `6L` into another array — this becomes `right`.
6. The **outer** merger now runs once, given `left` and `right`: it reads `left[0]` (the average, cast to `double`), `left[1]` (the min `Optional`, unwrapped via `orElseThrow()`), `right[0]` (the max `Optional`, unwrapped), and `right[1]` (the count, cast to `long`), assembling them into `new Stats(58.33..., 20, 100, 6)`.
7. `System.out.println(stats)` prints the record's auto-generated `toString()`, showing all four statistics computed from one single traversal of `orderAmounts`.

```
stream: 50,75,20,100,45,60
   │        │        │        │
   ▼        ▼        ▼        ▼
 avg      min       max     count     (all 4 accumulate together, one pass)
  58.3     20        100      6
   └──┬────┘          └───┬────┘
   inner-left tee      inner-right tee
      └───────────┬───────────┘
              outer tee
                  │
              Stats[avg=58.3, min=20, max=100, count=6]
```

## 7. Gotchas & takeaways

> `teeing()` runs both downstream collectors over the **same single pass**, not two separate passes — so it's a genuine efficiency win over collecting to a `List` and then computing each aggregate separately, especially for large or infinite streams where materializing an intermediate list would be wasteful or impossible.

- Both downstream collectors see every stream element; there's no way to route different elements to different collectors with `teeing()` alone (use `Collectors.partitioningBy` or `groupingBy` for that).
- The `merger` `BiFunction` runs exactly once, after the stream finishes, combining the two finished results.
- `teeing()` calls can be nested to combine more than two aggregates in one pass, as shown in Level 3, though beyond two or three it often reads more clearly as a manual reduction or a purpose-built accumulator class.
- Works with parallel streams too — Java correctly merges partial results from both downstream collectors before the final `merger` call.
- Don't reach for `teeing()` when you only need one aggregate — plain `Collectors.summingInt`, `Collectors.averagingInt`, etc. are simpler and sufficient on their own.
