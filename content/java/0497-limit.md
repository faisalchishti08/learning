---
card: java
gi: 497
slug: limit
title: limit()
---

## 1. What it is

`Stream.limit(maxSize)` returns a stream containing at most the first `maxSize` elements of the source stream — once that many elements have been produced, the stream stops, regardless of how many more the source could provide. It's a **short-circuiting** intermediate operation: for an infinite source (like `Stream.iterate` or `Stream.generate`), `limit` is what makes processing actually terminate.

## 2. Why & when

`limit` is how you cap a stream's length — taking the top N results, the first page of a paginated list, or turning an infinite generator into a finite, usable sequence. It's most essential when paired with `Stream.iterate`/`Stream.generate`, both of which produce infinite streams by default: without a `.limit(n)` call (or an equivalent stopping mechanism), a terminal operation on either would never complete. But it's just as commonly used on ordinary finite streams too — "give me the top 5 highest scores," "show only the first 10 search results."

## 3. Core concept

```java
import java.util.stream.*;

List<Integer> firstThree = Stream.of(10, 20, 30, 40, 50)
        .limit(3)
        .toList(); // [10, 20, 30]

List<Integer> firstFivePowers = Stream.iterate(1, n -> n * 2)
        .limit(5)
        .toList(); // [1, 2, 4, 8, 16] -- caps an otherwise-infinite stream
```

`limit` stops the pipeline once the requested count of elements has been produced — later elements, if any, are never generated or processed at all.

## 4. Diagram

<svg viewBox="0 0 640 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="limit takes only the first N elements and stops the pipeline">
  <rect x="8" y="8" width="624" height="104" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="50" height="30" fill="#1c2430" stroke="#6db33f"/><text x="55" y="50" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">10</text>
  <rect x="90" y="30" width="50" height="30" fill="#1c2430" stroke="#6db33f"/><text x="115" y="50" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">20</text>
  <rect x="150" y="30" width="50" height="30" fill="#1c2430" stroke="#6db33f"/><text x="175" y="50" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">30</text>
  <rect x="210" y="30" width="50" height="30" fill="#0d1117" stroke="#8b949e" stroke-dasharray="3,2"/><text x="235" y="50" fill="#8b949e" font-size="12" text-anchor="middle" font-family="monospace">40</text>
  <rect x="270" y="30" width="50" height="30" fill="#0d1117" stroke="#8b949e" stroke-dasharray="3,2"/><text x="295" y="50" fill="#8b949e" font-size="12" text-anchor="middle" font-family="monospace">50</text>
  <line x1="205" y1="20" x2="205" y2="75" stroke="#f85149" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="205" y="95" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">limit(3) cuts here -- rest never processed</text>
</svg>

`limit(3)` keeps the first three elements and stops — the remaining elements are neither generated (for an infinite source) nor evaluated (for a finite one).

## 5. Runnable example

Scenario: showing a "top scorers" leaderboard preview — evolved from a plain top-N cut on a sorted list, through combining `limit` with an infinite `Stream.iterate` sequence, to a version that demonstrates `limit`'s short-circuiting behavior stopping expensive work early.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class LimitBasic {
    public static void main(String[] args) {
        List<Integer> scores = List.of(42, 99, 17, 88, 56, 73);

        List<Integer> top3 = scores.stream()
                .sorted(Comparator.reverseOrder())
                .limit(3)
                .toList();

        System.out.println("Top 3: " + top3);
    }
}
```

**How to run:** `java LimitBasic.java`

Expected output:
```
Top 3: [99, 88, 73]
```

`.sorted(Comparator.reverseOrder())` arranges scores highest first: `99, 88, 73, 56, 42, 17`. `.limit(3)` then keeps only the first three of that sorted order — the three highest scores overall.

### Level 2 — Intermediate

```java
import java.util.stream.*;

public class LimitInfinite {
    public static void main(String[] args) {
        // An infinite doubling sequence, made finite and usable only via limit().
        List<Long> firstSixPowers = Stream.iterate(1L, n -> n * 2)
                .limit(6)
                .toList();

        System.out.println("First six powers of two: " + firstSixPowers);
    }
}
```

**How to run:** `java LimitInfinite.java`

Expected output:
```
First six powers of two: [1, 2, 4, 8, 16, 32]
```

The real-world concern this adds: `Stream.iterate(1L, n -> n * 2)` (see [[stream-iterate]]) never stops on its own — without `.limit(6)`, calling `.toList()` on it would run forever, generating ever-larger numbers until memory or time ran out. `limit` is what makes an infinite generator usable at all in a pipeline that needs a finite result.

### Level 3 — Advanced

```java
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.*;

public class LimitShortCircuit {
    static int expensiveCheck(int n, AtomicInteger callCount) {
        callCount.incrementAndGet(); // track how many times this "expensive" operation actually ran
        return n * n;
    }

    public static void main(String[] args) {
        AtomicInteger callCount = new AtomicInteger(0);

        var result = Stream.iterate(1, n -> n + 1)
                .map(n -> expensiveCheck(n, callCount))
                .limit(4)
                .toList();

        System.out.println("Result: " + result);
        System.out.println("Expensive check ran " + callCount.get() + " times");
    }
}
```

**How to run:** `java LimitShortCircuit.java`

Expected output:
```
Result: [1, 4, 9, 16]
Expensive check ran 4 times
```

This demonstrates `limit`'s short-circuiting nature concretely: `Stream.iterate(1, n -> n + 1)` is infinite, and `expensiveCheck` simulates costly work with an `AtomicInteger` counter tracking real invocations. Even though the source could generate infinitely many numbers, `.limit(4)` ensures `expensiveCheck` runs **exactly four times**, not once for some larger internal batch and not indefinitely — the pipeline genuinely stops pulling from the source the moment four elements have been produced.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `callCount` starts at `0`.

`Stream.iterate(1, n -> n + 1)` sets up a lazy, infinite stream of `1, 2, 3, 4, 5, ...`. `.map(n -> expensiveCheck(n, callCount))` is chained but, being lazy, doesn't run yet either. `.limit(4)` marks the pipeline to stop after four elements. `.toList()` is the terminal operation that actually drives everything.

The pipeline pulls its first element from `Stream.iterate`: `1`. `.map(...)` calls `expensiveCheck(1, callCount)`, which increments `callCount` to `1` and returns `1 * 1 = 1`. `limit` has now produced one of its four allowed elements.

The pipeline pulls the second element: `2`. `expensiveCheck(2, callCount)` increments `callCount` to `2`, returns `4`. Third element: `3`, `expensiveCheck` increments `callCount` to `3`, returns `9`. Fourth element: `4`, `expensiveCheck` increments `callCount` to `4`, returns `16`.

```
pull 1 -> expensiveCheck(1): callCount=1, returns 1   [limit: 1/4]
pull 2 -> expensiveCheck(2): callCount=2, returns 4   [limit: 2/4]
pull 3 -> expensiveCheck(3): callCount=3, returns 9   [limit: 3/4]
pull 4 -> expensiveCheck(4): callCount=4, returns 16  [limit: 4/4 -- STOP]
(element 5 and beyond are never pulled from the infinite source)
```

At this point `limit(4)` has received its full quota of four elements, so the pipeline stops — `Stream.iterate` is never asked for a fifth element, and `expensiveCheck` is never called a fifth time. `.toList()` collects the four produced results into `[1, 4, 9, 16]`, and `callCount.get()` confirms exactly `4` invocations occurred, proving the infinite source was genuinely cut short rather than exhausted or pre-computed in bulk.

## 7. Gotchas & takeaways

> `limit` is short-circuiting, but operations placed **after** it in the pipeline still only see the limited elements — while operations placed **before** it (like the `.map(...)` in Level 3) run exactly once per element actually pulled, not once per element the source *could* have produced. Understanding this ordering is key to reasoning about how much work an infinite-source pipeline actually performs.

- `limit(n)` keeps at most the first `n` elements and stops the pipeline once that many have been produced.
- It's essential for making infinite sources (`Stream.iterate`, `Stream.generate` without a self-limiting form) usable — without it, a terminal operation on an infinite stream never completes.
- `limit` is short-circuiting: it can cause the entire upstream pipeline (including any `map`/`filter` stages before it) to stop early, without processing every element the source could theoretically provide.
- On an already-sorted stream, `limit(n)` after `sorted()` is a common and efficient way to implement "top N" / "bottom N" queries.
- For a "stop when a condition is met" rule rather than a fixed count, consider `takeWhile` instead of `limit` — `limit` always caps by a specific number, regardless of the elements' actual values.
