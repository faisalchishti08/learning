---
card: java
gi: 508
slug: sum-average-summarystatistics-primitive-streams
title: sum / average / summaryStatistics (primitive streams)
---

## 1. What it is

`IntStream`, `LongStream`, and `DoubleStream` each provide three built-in numeric aggregation methods that a plain `Stream<T>` doesn't have: `.sum()` returns the total (as `int`/`long`/`double` respectively), `.average()` returns the mean as an `OptionalDouble` (empty for an empty stream, since there's no meaningful average of zero numbers), and `.summaryStatistics()` computes count, sum, min, max, and average all at once, bundled into an `IntSummaryStatistics`/`LongSummaryStatistics`/`DoubleSummaryStatistics` object.

## 2. Why & when

These methods exist specifically on the primitive stream types because numeric aggregation is such a common need that it deserves direct, efficient, purpose-built methods rather than always going through the more general `reduce` or `collect`. You reach for `.sum()`/`.average()` when you need just one of those values; you reach for `.summaryStatistics()` when you need several of them together, since it computes all five in a single pass over the data rather than requiring separate passes (or separate `reduce`/`collect` calls) for each one.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

int total = IntStream.of(4, 8, 15, 16, 23, 42).sum(); // 108
OptionalDouble avg = IntStream.of(4, 8, 15, 16, 23, 42).average(); // OptionalDouble[18.0]

IntSummaryStatistics stats = IntStream.of(4, 8, 15, 16, 23, 42).summaryStatistics();
// stats.getCount()=6, getSum()=108, getMin()=4, getMax()=42, getAverage()=18.0
```

`sum()` and `average()` each require their own pass if called separately; `summaryStatistics()` computes count, sum, min, max, and average together in one traversal.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="summaryStatistics computes count, sum, min, max, and average in a single pass">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="120" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="90" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">IntStream</text>
  <text x="200" y="42" fill="#8b949e" font-size="12" font-family="sans-serif">.summaryStatistics()</text>
  <line x1="150" y1="35" x2="330" y2="35" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowSS)"/>
  <rect x="340" y="60" width="90" height="26" rx="3" fill="#1c2430" stroke="#6db33f"/><text x="385" y="78" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">count</text>
  <rect x="430" y="60" width="80" height="26" rx="3" fill="#1c2430" stroke="#6db33f"/><text x="470" y="78" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">sum</text>
  <rect x="340" y="90" width="60" height="26" rx="3" fill="#1c2430" stroke="#6db33f"/><text x="370" y="108" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">min</text>
  <rect x="400" y="90" width="60" height="26" rx="3" fill="#1c2430" stroke="#6db33f"/><text x="430" y="108" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">max</text>
  <rect x="460" y="90" width="90" height="26" rx="3" fill="#1c2430" stroke="#6db33f"/><text x="505" y="108" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">average</text>
  <defs><marker id="arrowSS" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One call to `summaryStatistics()` produces five numbers at once, all computed together during a single traversal of the stream.

## 5. Runnable example

Scenario: analyzing response-time measurements for a service health report — evolved from basic sum/average calls, through switching to a single `summaryStatistics()` call, to a version that computes summary statistics per group using a downstream collector.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class SumAverageBasic {
    public static void main(String[] args) {
        int[] responseTimesMs = {120, 95, 340, 88, 210};

        int total = IntStream.of(responseTimesMs).sum();
        OptionalDouble average = IntStream.of(responseTimesMs).average();

        System.out.println("Total: " + total + "ms");
        System.out.printf("Average: %.1fms%n", average.orElse(0));
    }
}
```

**How to run:** `java SumAverageBasic.java`

Expected output:
```
Total: 853ms
Average: 170.6ms
```

`IntStream.of(responseTimesMs).sum()` adds all five response times: `120+95+340+88+210 = 853`. A separate `IntStream.of(responseTimesMs).average()` call recomputes over a fresh stream (since the first was already consumed), returning `OptionalDouble[170.6]` — `average()` returns `OptionalDouble` rather than a plain `double` because an empty stream has no meaningful average.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class SummaryStatisticsBasic {
    public static void main(String[] args) {
        int[] responseTimesMs = {120, 95, 340, 88, 210};

        IntSummaryStatistics stats = IntStream.of(responseTimesMs).summaryStatistics();

        System.out.println("Count: " + stats.getCount());
        System.out.println("Sum: " + stats.getSum() + "ms");
        System.out.println("Min: " + stats.getMin() + "ms");
        System.out.println("Max: " + stats.getMax() + "ms");
        System.out.printf("Average: %.1fms%n", stats.getAverage());
    }
}
```

**How to run:** `java SummaryStatisticsBasic.java`

Expected output:
```
Count: 5
Sum: 853ms
Min: 88ms
Max: 340ms
Average: 170.6ms
```

The real-world concern this adds: a real health report needs more than just sum and average — min and max matter too (the fastest and slowest response recorded). `.summaryStatistics()` computes all five values (count, sum, min, max, average) in a **single pass** over `responseTimesMs`, instead of the several separate passes that calling `.sum()`, `.min()`, `.max()`, and `.average()` individually would require.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class SummaryStatisticsGrouped {
    record Measurement(String endpoint, int responseTimeMs) {}

    public static void main(String[] args) {
        List<Measurement> measurements = List.of(
                new Measurement("/login", 120),
                new Measurement("/search", 340),
                new Measurement("/login", 95),
                new Measurement("/search", 210),
                new Measurement("/login", 88)
        );

        // groupingBy + summarizingInt: full per-endpoint statistics in one pass over the data.
        Map<String, IntSummaryStatistics> statsByEndpoint = measurements.stream()
                .collect(Collectors.groupingBy(
                        Measurement::endpoint,
                        Collectors.summarizingInt(Measurement::responseTimeMs)));

        new TreeMap<>(statsByEndpoint).forEach((endpoint, stats) ->
                System.out.printf("%s: count=%d, avg=%.1fms, max=%dms%n",
                        endpoint, stats.getCount(), stats.getAverage(), stats.getMax()));
    }
}
```

**How to run:** `java SummaryStatisticsGrouped.java`

Expected output:
```
/login: count=3, avg=101.0ms, max=120ms
/search: count=2, avg=275.0ms, max=340ms
```

This combines `summaryStatistics()`'s spirit with `groupingBy` (see [[collect]]): `Collectors.summarizingInt(Measurement::responseTimeMs)` is a downstream collector that produces an `IntSummaryStatistics` for *each group* rather than the whole stream at once — grouping by `endpoint` first, then summarizing each endpoint's response times independently, all in one traversal of `measurements`.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `measurements` holds five entries: three for `"/login"` (`120, 95, 88`) and two for `"/search"` (`340, 210`).

`measurements.stream().collect(Collectors.groupingBy(Measurement::endpoint, Collectors.summarizingInt(Measurement::responseTimeMs)))` processes each measurement once. For the first, `Measurement("/login", 120)`: `groupingBy` sees no existing group for `"/login"`, creates a new `IntSummaryStatistics` accumulator for it, and feeds `120` into it — that accumulator now has count `1`, sum `120`, min `120`, max `120`.

For `Measurement("/search", 340)`: a new group is created for `"/search"`, fed `340` — count `1`, sum `340`, min `340`, max `340`.

For `Measurement("/login", 95)`: the existing `"/login"` accumulator is fed `95` — count becomes `2`, sum becomes `120+95=215`, min becomes `min(120,95)=95`, max stays `120`.

For `Measurement("/search", 210)`: the existing `"/search"` accumulator is fed `210` — count becomes `2`, sum becomes `340+210=550`, min becomes `210`, max stays `340`.

For `Measurement("/login", 88)`: the `"/login"` accumulator is fed `88` — count becomes `3`, sum becomes `215+88=303`, min becomes `min(95,88)=88`, max stays `120`.

```
/login accumulator:  120 -> (1, sum=120)  -> +95 -> (2, sum=215, min=95) -> +88 -> (3, sum=303, min=88, max=120)
/search accumulator: 340 -> (1, sum=340)  -> +210 -> (2, sum=550, min=210, max=340)
```

Once every measurement is processed, `"/login"`'s final `IntSummaryStatistics` has count `3`, sum `303`, average `303/3=101.0`, max `120`; `"/search"`'s has count `2`, sum `550`, average `550/2=275.0`, max `340`. `new TreeMap<>(...)` orders the two endpoints alphabetically for printing, and the `forEach` prints both endpoints' full statistics on separate lines.

## 7. Gotchas & takeaways

> `.average()` returns `OptionalDouble`, not a plain `double` — calling `.getAsDouble()` on it without checking `.isPresent()` first throws `NoSuchElementException` if the stream was empty. Always use `.orElse(...)`, `.isPresent()`, or `.ifPresent(...)` to handle the empty case safely, as shown with `.orElse(0)` in Level 1.

- `sum()`, `average()`, and `summaryStatistics()` are built into the primitive stream types (`IntStream`, `LongStream`, `DoubleStream`) — not available on a plain `Stream<Integer>` without first converting via `mapToInt` (see [[maptoint-maptolong-maptodouble-maptoobj]]).
- `.summaryStatistics()` computes count, sum, min, max, and average together in one pass — more efficient than calling the individual methods separately when you need more than one of them.
- `average()` returns `OptionalDouble` because an empty stream has no meaningful mean; `sum()` returns a plain number because zero is a perfectly valid sum for an empty stream.
- `Collectors.summarizingInt`/`summarizingLong`/`summarizingDouble` bring the same single-pass statistics computation into the `Collectors` world, especially powerful combined with `groupingBy` for per-group statistics.
- For very large datasets where multiple statistics are needed, always prefer `summaryStatistics()` (or `summarizingInt` with grouping) over several separate `sum()`/`min()`/`max()`/`average()` calls, each of which would otherwise re-scan the same data.
