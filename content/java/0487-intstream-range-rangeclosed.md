---
card: java
gi: 487
slug: intstream-range-rangeclosed
title: IntStream.range / rangeClosed
---

## 1. What it is

`IntStream.range(start, end)` produces a stream of `int` values from `start` up to but **excluding** `end`. `IntStream.rangeClosed(start, end)` does the same but **includes** `end`. Both are the streams-based replacement for a classic `for (int i = start; i < end; i++)` loop, and both work on the primitive `IntStream`, avoiding the boxing overhead of a `Stream<Integer>`.

## 2. Why & when

Counting loops are everywhere: iterating a fixed number of times, generating array indices, building a sequence of page numbers, running a simulation a set number of iterations. `IntStream.range`/`rangeClosed` let you express "count from here to there" directly as a stream, so it can be filtered, mapped, reduced, or turned parallel with the same stream API used for everything else — instead of a separate imperative loop with its own accumulator variables.

You reach for `range` when you're thinking in terms of a half-open interval (e.g. valid array indices `0` to `array.length`, which is naturally exclusive at the top). You reach for `rangeClosed` when the upper bound is itself meant to be included (e.g. "days 1 through 31", "attempts 1 through 5").

## 3. Core concept

```java
import java.util.stream.*;

IntStream.range(0, 5).forEach(System.out::println);        // 0 1 2 3 4  (end excluded)
IntStream.rangeClosed(1, 5).forEach(System.out::println);   // 1 2 3 4 5  (end included)

int sum = IntStream.rangeClosed(1, 100).sum(); // 5050 -- Gauss's classic sum
```

The only difference between the two is whether `end` itself is part of the sequence — `range` stops one short, `rangeClosed` includes it.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="IntStream.range excludes the end value; IntStream.rangeClosed includes it">
  <rect x="8" y="8" width="624" height="124" rx="8" fill="#0d1117"/>
  <text x="20" y="35" fill="#8b949e" font-size="11" font-family="sans-serif">range(1, 5):</text>
  <rect x="130" y="18" width="40" height="28" fill="#1c2430" stroke="#79c0ff"/><text x="150" y="37" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">1</text>
  <rect x="175" y="18" width="40" height="28" fill="#1c2430" stroke="#79c0ff"/><text x="195" y="37" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">2</text>
  <rect x="220" y="18" width="40" height="28" fill="#1c2430" stroke="#79c0ff"/><text x="240" y="37" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">3</text>
  <rect x="265" y="18" width="40" height="28" fill="#1c2430" stroke="#79c0ff"/><text x="285" y="37" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">4</text>
  <rect x="310" y="18" width="40" height="28" fill="#0d1117" stroke="#8b949e" stroke-dasharray="3,2"/><text x="330" y="37" fill="#8b949e" font-size="12" text-anchor="middle" font-family="monospace">5</text>
  <text x="360" y="37" fill="#8b949e" font-size="10" font-family="sans-serif">excluded</text>

  <text x="20" y="90" fill="#8b949e" font-size="11" font-family="sans-serif">rangeClosed(1, 5):</text>
  <rect x="130" y="73" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="150" y="92" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">1</text>
  <rect x="175" y="73" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="195" y="92" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">2</text>
  <rect x="220" y="73" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="240" y="92" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">3</text>
  <rect x="265" y="73" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="285" y="92" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">4</text>
  <rect x="310" y="73" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="330" y="92" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">5</text>
  <text x="360" y="92" fill="#6db33f" font-size="10" font-family="sans-serif">included</text>
</svg>

`range` stops before the end value; `rangeClosed` includes it — otherwise both count sequentially from the start.

## 5. Runnable example

Scenario: paging through a list of search results — evolved from computing zero-based array-slice boundaries with `range`, through generating one-based, human-facing page numbers with `rangeClosed`, to a version that builds full page-boundary metadata for a UI pager.

### Level 1 — Basic

```java
import java.util.stream.*;

public class RangeBasic {
    public static void main(String[] args) {
        int pageSize = 3;
        String[] results = {"a", "b", "c", "d", "e", "f", "g"};

        // Valid array indices: 0 up to (but excluding) results.length -- a natural fit for range().
        IntStream.range(0, results.length)
                .filter(i -> i % pageSize == 0)
                .forEach(i -> System.out.println("Page starts at index " + i));
    }
}
```

**How to run:** `java RangeBasic.java`

Expected output:
```
Page starts at index 0
Page starts at index 3
Page starts at index 6
```

`IntStream.range(0, results.length)` produces `0, 1, 2, 3, 4, 5, 6` — exactly the valid indices into `results` (`results.length` itself, `7`, is correctly excluded since it isn't a valid index). `.filter(i -> i % pageSize == 0)` keeps only the indices where a new page of size `3` begins.

### Level 2 — Intermediate

```java
import java.util.stream.*;

public class RangeClosedPages {
    public static void main(String[] args) {
        int totalResults = 7;
        int pageSize = 3;
        int totalPages = (int) Math.ceil((double) totalResults / pageSize);

        // Human-facing page numbers start at 1 and include the last page -- rangeClosed fits naturally.
        IntStream.rangeClosed(1, totalPages)
                .forEach(page -> System.out.println("Page " + page + " of " + totalPages));
    }
}
```

**How to run:** `java RangeClosedPages.java`

Expected output:
```
Page 1 of 3
Page 2 of 3
Page 3 of 3
```

The real-world concern this adds: switching from zero-based *array indices* (Level 1) to one-based *human-facing page numbers* (Level 2). Because "page 3 of 3" must actually include page `3`, `rangeClosed(1, totalPages)` is the correct choice here — using `range(1, totalPages)` would silently drop the final page.

### Level 3 — Advanced

```java
import java.util.stream.*;

public class RangePagerMetadata {
    record PageInfo(int pageNumber, int startIndex, int endIndexExclusive) {}

    public static void main(String[] args) {
        int totalResults = 7;
        int pageSize = 3;
        int totalPages = (int) Math.ceil((double) totalResults / pageSize);

        IntStream.rangeClosed(1, totalPages)
                .mapToObj(page -> {
                    int start = (page - 1) * pageSize;
                    // clamp the last page's exclusive end to totalResults, since it may be a partial page
                    int end = Math.min(start + pageSize, totalResults);
                    return new PageInfo(page, start, end);
                })
                .forEach(info -> System.out.println(
                        "Page " + info.pageNumber() + ": indices [" + info.startIndex() + ", " + info.endIndexExclusive() + ")"));
    }
}
```

**How to run:** `java RangePagerMetadata.java`

Expected output:
```
Page 1: indices [0, 3)
Page 2: indices [3, 6)
Page 3: indices [6, 7)
```

This combines both ideas: `rangeClosed(1, totalPages)` still drives the one-based page numbers, but `.mapToObj(...)` now converts each page number into a full `PageInfo` record carrying the zero-based, half-open `[start, end)` index range for that page — reusing the exclusive-end convention from Level 1's `range()` for the slice boundaries, while `Math.min(...)` correctly clamps the final, partial page's end index to `totalResults`.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `totalResults` is `7`, `pageSize` is `3`, so `totalPages` is `Math.ceil(7.0 / 3) = Math.ceil(2.33...) = 3`.

`IntStream.rangeClosed(1, 3)` produces the sequence `1, 2, 3` (inclusive of `3`, since this is `rangeClosed`).

For page `1`: `.mapToObj(...)` computes `start = (1 - 1) * 3 = 0`, then `end = Math.min(0 + 3, 7) = Math.min(3, 7) = 3`. It builds `PageInfo(1, 0, 3)`, and `.forEach` prints `"Page 1: indices [0, 3)"`.

For page `2`: `start = (2 - 1) * 3 = 3`, `end = Math.min(3 + 3, 7) = Math.min(6, 7) = 6`. `PageInfo(2, 3, 6)` prints as `"Page 2: indices [3, 6)"`.

For page `3`: `start = (3 - 1) * 3 = 6`, `end = Math.min(6 + 3, 7) = Math.min(9, 7) = 7` — here the clamp matters, since a full page would have ended at index `9`, but only `7` results exist. `PageInfo(3, 6, 7)` prints as `"Page 3: indices [6, 7)"`.

```
page 1: start=(1-1)*3=0  end=min(0+3,7)=3  -> [0,3)  (3 results: indices 0,1,2)
page 2: start=(2-1)*3=3  end=min(3+3,7)=6  -> [3,6)  (3 results: indices 3,4,5)
page 3: start=(3-1)*3=6  end=min(6+3,7)=7  -> [6,7)  (1 result:  index 6 -- partial page, clamped)
```

The last page's exclusive-end index of `7` matches `totalResults` exactly, confirming no result is left unaccounted for and none is double-counted across pages.

## 7. Gotchas & takeaways

> Mixing up `range` and `rangeClosed` is a classic off-by-one bug source: using `range(1, totalPages)` for one-based, inclusive page numbers silently drops the last page, while using `rangeClosed(0, array.length)` for zero-based array indices generates one index *past* the end of the array (`array.length` itself is not a valid index and would throw `ArrayIndexOutOfBoundsException` if used directly).

- `IntStream.range(start, end)` is half-open: `end` is excluded — the natural fit for zero-based array/index bounds.
- `IntStream.rangeClosed(start, end)` is fully closed: `end` is included — the natural fit for one-based, human-facing counts.
- Both return a primitive `IntStream`, avoiding the boxing cost of building a `Stream<Integer>` for simple counting loops.
- `.mapToObj(...)` is the bridge from a primitive `IntStream` back to a `Stream<T>` of richer objects, as used here to build `PageInfo` records from plain page numbers.
- When converting a business-facing range (e.g. one-based page numbers) into index math (zero-based, half-open), be explicit about which convention each variable uses to avoid off-by-one errors like the ones described above.
