---
card: java
gi: 516
slug: counting
title: counting()
---

## 1. What it is

`Collectors.counting()` is a collector that produces the number of elements it processed, as a `Long`. Used directly as the terminal collector for a stream, it's equivalent to (but less efficient than) calling `.count()` directly on the stream. Its real value shows up as a **downstream** collector, most commonly with `Collectors.groupingBy(...)` (see [[groupingby-with-downstream]]), where it computes the count *within each group* rather than for the whole stream.

## 2. Why & when

On its own, `stream.collect(Collectors.counting())` is a roundabout way to get what `stream.count()` gives you more directly — so `counting()` alone is rarely the right choice. Its purpose is to compose: since `groupingBy`'s second argument expects a `Collector`, and `counting()` *is* a `Collector` that yields a count, passing it as the downstream collector to `groupingBy` gives you a per-group tally in one step, which `.count()` alone (being a terminal operation on a whole stream) cannot do.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

record Order(String customer, double amount) {}

List<Order> orders = List.of(
        new Order("Alice", 50.0), new Order("Bob", 30.0), new Order("Alice", 20.0));

// Standalone -- unusual, .count() is simpler for this
long total = orders.stream().collect(Collectors.counting()); // 3

// As a downstream collector -- the common, useful case
Map<String, Long> ordersPerCustomer = orders.stream()
        .collect(Collectors.groupingBy(Order::customer, Collectors.counting()));
// {Alice=2, Bob=1}
```

`counting()` used alone just counts the whole stream (redundant with `.count()`); used as a downstream collector inside `groupingBy`, it counts each group's elements independently.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="counting as a downstream collector tallies how many elements fall into each group">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="20" width="90" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="65" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Alice, 50</text>
  <rect x="120" y="20" width="90" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="165" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Bob, 30</text>
  <rect x="220" y="20" width="90" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="265" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Alice, 20</text>
  <text x="165" y="65" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">groupingBy(customer, counting())</text>
  <line x1="165" y1="50" x2="165" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowCT)"/>
  <rect x="90" y="85" width="90" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="135" y="105" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Alice: 2</text>
  <rect x="190" y="85" width="90" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="235" y="105" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Bob: 1</text>
  <defs><marker id="arrowCT" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`counting()` inside `groupingBy` tallies each group's members independently, without ever materializing the group's actual list of elements.

## 5. Runnable example

Scenario: analyzing word frequency in a block of text — evolved from a plain per-word count, through filtering low-frequency words out of the result, to a version ranking words by frequency using the counts as a sort key.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class CountingBasic {
    public static void main(String[] args) {
        List<String> words = List.of("the", "quick", "fox", "the", "lazy", "the", "fox");

        Map<String, Long> wordCounts = words.stream()
                .collect(Collectors.groupingBy(w -> w, Collectors.counting()));

        new TreeMap<>(wordCounts).forEach((word, count) -> System.out.println(word + ": " + count));
    }
}
```

**How to run:** `java CountingBasic.java`

Expected output:
```
fox: 2
lazy: 1
quick: 1
the: 3
```

`Collectors.groupingBy(w -> w, Collectors.counting())` groups each word by itself (the identity function `w -> w` is the classifier), and `Collectors.counting()` tallies how many times each distinct word appears — a direct, one-line word-frequency count.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class CountingFiltered {
    public static void main(String[] args) {
        List<String> words = List.of("the", "quick", "fox", "the", "lazy", "the", "fox", "jumps");

        Map<String, Long> wordCounts = words.stream()
                .collect(Collectors.groupingBy(w -> w, Collectors.counting()));

        // Only words appearing more than once are "notable" -- filter the resulting map's entries.
        List<String> frequentWords = wordCounts.entrySet().stream()
                .filter(entry -> entry.getValue() > 1)
                .map(Map.Entry::getKey)
                .sorted()
                .toList();

        System.out.println("Frequent words: " + frequentWords);
    }
}
```

**How to run:** `java CountingFiltered.java`

Expected output:
```
Frequent words: [fox, the]
```

The real-world concern this adds: after computing the counts, a second pass filters the resulting `Map<String, Long>` (via its `.entrySet().stream()`) to keep only entries whose count exceeds `1` — a common two-stage pattern: aggregate first with `groupingBy`/`counting`, then filter or rank the aggregated results in a follow-up pipeline over the map's entries.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class CountingRanked {
    public static void main(String[] args) {
        List<String> words = List.of(
                "the", "quick", "fox", "the", "lazy", "the", "fox", "jumps", "over", "lazy", "the");

        Map<String, Long> wordCounts = words.stream()
                .collect(Collectors.groupingBy(w -> w, Collectors.counting()));

        // Rank words by frequency, highest first, breaking ties alphabetically.
        List<Map.Entry<String, Long>> ranked = wordCounts.entrySet().stream()
                .sorted(Map.Entry.<String, Long>comparingByValue().reversed()
                        .thenComparing(Map.Entry.comparingByKey()))
                .toList();

        int rank = 1;
        for (Map.Entry<String, Long> entry : ranked) {
            System.out.println(rank++ + ". " + entry.getKey() + " (" + entry.getValue() + ")");
        }
    }
}
```

**How to run:** `java CountingRanked.java`

Expected output:
```
1. the (4)
2. fox (2)
3. lazy (2)
4. jumps (1)
5. over (1)
6. quick (1)
```

This builds a full frequency ranking from the counted map: `Map.Entry.<String, Long>comparingByValue().reversed()` orders entries by count, highest first, and `.thenComparing(Map.Entry.comparingByKey())` breaks ties (`fox` and `lazy` both appear twice) alphabetically — turning the raw `groupingBy`+`counting` result into a genuinely useful, ordered report.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `words` holds eleven entries, with `"the"` appearing four times, `"fox"` and `"lazy"` each twice, and `"quick"`, `"jumps"`, `"over"` each once.

`words.stream().collect(Collectors.groupingBy(w -> w, Collectors.counting()))` processes each word, using the word itself as the grouping key (via the identity classifier `w -> w`), and `Collectors.counting()` tallies occurrences within each group. After processing all eleven words, the resulting `wordCounts` map holds: `"the"=4`, `"fox"=2`, `"lazy"=2`, `"quick"=1`, `"jumps"=1`, `"over"=1`.

`wordCounts.entrySet().stream().sorted(Map.Entry.<String, Long>comparingByValue().reversed().thenComparing(Map.Entry.comparingByKey()))` sorts the six entries. `comparingByValue()` compares by the `Long` count; `.reversed()` flips it so higher counts sort first. Comparing `"the"=4` against everything else, it has the highest count, so it sorts first regardless of the tiebreaker. Comparing `"fox"=2` and `"lazy"=2`: their counts are equal, so `.thenComparing(Map.Entry.comparingByKey())` breaks the tie alphabetically — `"fox"` comes before `"lazy"`. Comparing `"quick"=1`, `"jumps"=1`, `"over"=1`: all tied at count `1`, so alphabetical order applies: `"jumps"`, `"over"`, `"quick"`.

```
Counts: the=4, fox=2, lazy=2, quick=1, jumps=1, over=1

Sort by count descending, ties broken alphabetically:
  the (4)      -- highest count, no tie
  fox (2)      -- tied with lazy at 2, "fox" < "lazy" alphabetically
  lazy (2)
  jumps (1)    -- tied with over, quick at 1, alphabetical: jumps < over < quick
  over (1)
  quick (1)
```

The `for` loop then walks the sorted `ranked` list, printing each entry with an incrementing rank number: `"1. the (4)"`, `"2. fox (2)"`, `"3. lazy (2)"`, `"4. jumps (1)"`, `"5. over (1)"`, `"6. quick (1)"` — a complete, deterministic frequency ranking built entirely from the initial `counting()`-based aggregation followed by a comparator-driven sort.

## 7. Gotchas & takeaways

> `Collectors.counting()` returns `Long`, not `int` or `long` — this matters when using the count in arithmetic or comparisons involving `int` values, where an explicit or automatic unboxing conversion may be needed. It also means comparing counts with `==` on boxed `Long` values outside the cached `-128` to `127` range compares object identity, not numeric equality — always use `.equals(...)` or unbox first (e.g. via `.longValue()`) when comparing `Long` counts for equality directly, though `Comparator`-based sorting (as used in Level 3) sidesteps this entirely.

- `Collectors.counting()` produces a `Long` count of the elements it processed — used alone it's a roundabout equivalent of `.count()`, but as a downstream collector it enables per-group counting.
- `Collectors.groupingBy(classifier, Collectors.counting())` is the standard idiom for "how many of each" — word frequency, orders per customer, occurrences per category.
- The identity function (`w -> w`) as a classifier groups elements by themselves, useful when counting occurrences of the elements directly rather than some derived property.
- Once a frequency map exists, further processing (filtering by a minimum count, ranking by frequency) operates on the map's `entrySet()` stream, using `Map.Entry.comparingByValue()`/`comparingByKey()` as ready-made comparators.
- `Collectors.counting()` returns a boxed `Long`; prefer comparator-based comparisons (`Map.Entry.comparingByValue()`) over raw `==`/`<` on the boxed values to avoid identity-comparison pitfalls.
