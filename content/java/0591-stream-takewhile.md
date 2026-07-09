---
card: java
gi: 591
slug: stream-takewhile
title: Stream.takeWhile
---

## 1. What it is

`Stream.takeWhile(predicate)` returns a stream of elements taken from the start of the source stream, stopping — permanently — at the first element that fails the predicate. Unlike `filter(predicate)`, which checks every element and keeps only the matching ones, `takeWhile` stops looking entirely the moment it hits the first non-matching element, even if later elements would have matched.

## 2. Why & when

`filter(predicate)` is the right tool when you want *every* element matching a condition, scattered anywhere throughout the stream. But a common, different need is "take elements only while some condition holds, then stop as soon as it doesn't" — like reading lines from a sorted log until timestamps stop being in order, or taking numbers from a sequence until the first negative one appears. Using `filter` for this is not just less efficient (it can't short-circuit on an infinite or very large stream, since it must inspect every element even after the "stop" condition would have been met) — it's also semantically wrong, since `filter` would happily skip over a later non-matching element and keep collecting matches after it, which isn't the "take until the streak ends" behavior actually wanted. `takeWhile` was added in Java 9 specifically to express this "take a prefix, stop at the first failure" pattern correctly and efficiently, including on infinite streams.

## 3. Core concept

```java
List<Integer> numbers = List.of(2, 4, 6, 7, 8, 10);

List<Integer> evenPrefix = numbers.stream()
    .takeWhile(n -> n % 2 == 0)
    .toList();
System.out.println(evenPrefix); // [2, 4, 6]  — stops at 7, never looks at 8 or 10

List<Integer> allEvens = numbers.stream()
    .filter(n -> n % 2 == 0)
    .toList();
System.out.println(allEvens); // [2, 4, 6, 8, 10] — filter checks every element, keeps ALL matches
```

`takeWhile` stops at `7` (the first odd number) and never evaluates the predicate against `8` or `10` at all, even though `8` and `10` are also even — this is the fundamental difference from `filter`, which would have included them.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="takeWhile stops permanently at the first non-matching element; filter keeps checking every element regardless">
  <text x="20" y="25" fill="#8b949e" font-size="11" font-family="sans-serif">Source: 2, 4, 6, 7, 8, 10</text>

  <text x="20" y="55" fill="#8b949e" font-size="10" font-family="sans-serif">takeWhile(even):</text>
  <g font-family="monospace" font-size="12">
    <rect x="130" y="42" width="26" height="24" fill="#1c2430" stroke="#6db33f"/><text x="143" y="59" fill="#6db33f" text-anchor="middle">2</text>
    <rect x="160" y="42" width="26" height="24" fill="#1c2430" stroke="#6db33f"/><text x="173" y="59" fill="#6db33f" text-anchor="middle">4</text>
    <rect x="190" y="42" width="26" height="24" fill="#1c2430" stroke="#6db33f"/><text x="203" y="59" fill="#6db33f" text-anchor="middle">6</text>
    <rect x="220" y="42" width="26" height="24" fill="#0d1117" stroke="#f85149"/><text x="233" y="59" fill="#f85149" text-anchor="middle">7</text>
  </g>
  <text x="260" y="59" fill="#f85149" font-size="10" font-family="sans-serif">&lt;- STOPS here, 8 &amp; 10 never even checked</text>

  <text x="20" y="105" fill="#8b949e" font-size="10" font-family="sans-serif">filter(even):</text>
  <g font-family="monospace" font-size="12">
    <rect x="130" y="92" width="26" height="24" fill="#1c2430" stroke="#6db33f"/><text x="143" y="109" fill="#6db33f" text-anchor="middle">2</text>
    <rect x="160" y="92" width="26" height="24" fill="#1c2430" stroke="#6db33f"/><text x="173" y="109" fill="#6db33f" text-anchor="middle">4</text>
    <rect x="190" y="92" width="26" height="24" fill="#1c2430" stroke="#6db33f"/><text x="203" y="109" fill="#6db33f" text-anchor="middle">6</text>
    <rect x="220" y="92" width="26" height="24" fill="#0d1117" stroke="#8b949e"/><text x="233" y="109" fill="#8b949e" text-anchor="middle">7</text>
    <rect x="250" y="92" width="26" height="24" fill="#1c2430" stroke="#6db33f"/><text x="263" y="109" fill="#6db33f" text-anchor="middle">8</text>
    <rect x="280" y="92" width="26" height="24" fill="#1c2430" stroke="#6db33f"/><text x="296" y="109" fill="#6db33f" text-anchor="middle">10</text>
  </g>
  <text x="330" y="109" fill="#8b949e" font-size="10" font-family="sans-serif">&lt;- checks EVERY element, keeps all matches</text>
</svg>

Same predicate, fundamentally different behavior: `takeWhile` produces a prefix and stops for good; `filter` produces every match anywhere in the stream.

## 5. Runnable example

Scenario: processing a stream of sensor readings that should be trusted only until the first anomalous (out-of-range) reading appears — starting with a simple numeric prefix example contrasting `takeWhile` and `filter`, then applying it to sensor readings with a realistic stopping condition, then combining `takeWhile` with an infinite stream to show it terminates a computation that would otherwise run forever.

### Level 1 — Basic

```java
import java.util.*;

public class TakeWhileBasic {
    public static void main(String[] args) {
        List<Integer> numbers = List.of(2, 4, 6, 7, 8, 10);

        List<Integer> takeWhileResult = numbers.stream()
            .takeWhile(n -> n % 2 == 0)
            .toList();

        List<Integer> filterResult = numbers.stream()
            .filter(n -> n % 2 == 0)
            .toList();

        System.out.println("takeWhile: " + takeWhileResult);
        System.out.println("filter:    " + filterResult);
    }
}
```

**How to run:** `java TakeWhileBasic.java`

Expected output:
```
takeWhile: [2, 4, 6]
filter:    [2, 4, 6, 8, 10]
```

`takeWhile(n -> n % 2 == 0)` takes `2`, `4`, `6` (all even), then encounters `7` — odd, fails the predicate — and stops immediately, never considering `8` or `10` at all, regardless of their values. `filter(n -> n % 2 == 0)` evaluates the predicate against every element independently, keeping `2`, `4`, `6`, `8`, `10` and only excluding `7` — the two produce genuinely different results from the identical predicate, because they answer different questions ("the leading run of matches" versus "every match anywhere").

### Level 2 — Intermediate

```java
import java.util.*;

public class TakeWhileSensors {
    record Reading(int timestamp, double value) {}

    public static void main(String[] args) {
        List<Reading> readings = List.of(
            new Reading(0, 20.1),
            new Reading(1, 20.3),
            new Reading(2, 20.5),
            new Reading(3, 150.0), // anomalous — sensor malfunction or spike
            new Reading(4, 20.4),  // back to normal, but should NOT be trusted after the anomaly
            new Reading(5, 20.6)
        );

        List<Reading> trustedReadings = readings.stream()
            .takeWhile(r -> r.value() < 100.0)
            .toList();

        System.out.println("Trusted readings: " + trustedReadings.size());
        trustedReadings.forEach(r -> System.out.println("  t=" + r.timestamp() + ": " + r.value()));
    }
}
```

**How to run:** `java TakeWhileSensors.java`

Expected output:
```
Trusted readings: 3
  t=0: 20.1
  t=1: 20.3
  t=2: 20.5
```

The real-world concern this adds: **correctly stopping trust at the first anomaly**, even though a later reading (`t=4`, value `20.4`) would also individually satisfy the predicate. This is exactly the case where `filter` would give the *wrong* answer: `filter(r -> r.value() < 100.0)` would incorrectly include `t=4` and `t=5` alongside the three genuinely trustworthy leading readings, silently treating post-anomaly data as trustworthy again — `takeWhile` correctly reflects that once an anomaly occurs, nothing after it should be trusted without further investigation, regardless of whether individual later values happen to look normal again.

### Level 3 — Advanced

```java
import java.util.stream.*;

public class TakeWhileInfinite {
    public static void main(String[] args) {
        // An infinite stream of powers of 2: 1, 2, 4, 8, 16, ...
        var powersOfTwo = Stream.iterate(1L, n -> n * 2);

        // Without takeWhile, calling .toList() directly on this stream would run forever.
        var underOneMillion = powersOfTwo
            .takeWhile(n -> n < 1_000_000)
            .toList();

        System.out.println(underOneMillion);
        System.out.println("Count: " + underOneMillion.size());

        // Combine takeWhile with other intermediate operations, same short-circuiting benefit.
        long sumOfSmallPowers = Stream.iterate(1L, n -> n * 2)
            .takeWhile(n -> n < 1000)
            .mapToLong(Long::longValue)
            .sum();

        System.out.println("Sum of powers of 2 under 1000: " + sumOfSmallPowers);
    }
}
```

**How to run:** `java TakeWhileInfinite.java`

Expected output:
```
[1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288]
Count: 20
Sum of powers of 2 under 1000: 1023
```

This handles the production-flavoured case of **terminating an infinite stream safely**: `Stream.iterate(1L, n -> n * 2)` produces an infinite sequence of powers of two with no inherent end. Calling `.toList()` directly on it would hang forever, since the stream never signals completion on its own. `takeWhile(n -> n < 1_000_000)` makes the pipeline genuinely finite — the moment an element fails the predicate (the first power of two reaching or exceeding one million), the stream stops pulling further elements from the infinite generator entirely, letting `.toList()` (and any downstream terminal operation) complete normally.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `Stream.iterate(1L, n -> n * 2)` creates a lazy, infinite stream: conceptually `1, 2, 4, 8, 16, ...` forever, with each element generated on demand from the previous one, never all computed upfront.

`underOneMillion` is built by chaining `.takeWhile(n -> n < 1_000_000)` and `.toList()`. Because streams are lazy, nothing actually executes until `.toList()` (the terminal operation) is called — at that point, the pipeline starts pulling elements one at a time from `Stream.iterate`'s generator:

```
Stream.iterate pulls one element at a time; takeWhile checks each as it arrives:

pull 1       -> 1 < 1,000,000?       yes -> keep, ask generator for next
pull 2       -> 2 < 1,000,000?       yes -> keep, ask generator for next
pull 4       -> ...                  yes -> keep
...
pull 524288  -> 524288 < 1,000,000?  yes -> keep, ask generator for next
pull 1048576 -> 1048576 < 1,000,000? NO  -> STOP, generator never asked for another element
```

Each doubling continues — `1, 2, 4, 8, ..., 524288` — until the generator produces `1048576` (2^20), the first power of two that is not less than `1,000,000`. At that point, `takeWhile`'s predicate fails, and the entire pipeline stops: `Stream.iterate` is never asked to generate `2097152` or any further value, because `takeWhile` short-circuits the whole upstream pull-based chain the instant it encounters a failing element. `.toList()` collects everything gathered before that point — the twenty powers of two from `1` through `524288` — into `underOneMillion`.

`main` prints `underOneMillion` (the full list of twenty values) and its `size()` (`20`).

The second computation, `sumOfSmallPowers`, follows the identical pattern with a smaller threshold (`1000`) and an additional `.mapToLong(Long::longValue)` step (converting the `Stream<Long>` to a primitive `LongStream` for efficient summation) before the terminal `.sum()`. `takeWhile(n -> n < 1000)` keeps `1, 2, 4, 8, 16, 32, 64, 128, 256, 512` (ten values; the next power, `1024`, fails the predicate and stops the pipeline), and `.sum()` adds them: `1+2+4+8+16+32+64+128+256+512 = 1023` — notably, one less than the next power of two (`1024`), a property of summing consecutive powers of two starting from `1`. `main` prints `"Sum of powers of 2 under 1000: 1023"`.

## 7. Gotchas & takeaways

> `takeWhile` on an **unordered** stream (one derived from a source like `HashSet` with no defined encounter order) has unspecified behavior regarding exactly which elements get taken — the "prefix" concept only has a well-defined meaning when the stream has a guaranteed encounter order (as `List`-derived streams and `Stream.iterate` always do). Using `takeWhile` on a stream from an unordered source is legal but its exact result may not be what you expect, since there's no guaranteed "first" element to start taking from consistently.

- `takeWhile`'s natural counterpart is `dropWhile(predicate)` (also added in Java 9): it *skips* the same leading prefix `takeWhile` would have kept, then returns everything after — the two are complementary halves of splitting a stream at the first predicate failure.
- `takeWhile` is a genuinely **short-circuiting** intermediate operation — unlike `filter`, it can make an otherwise-infinite stream pipeline terminate, which is precisely why it's essential for safely using `Stream.iterate` or `Stream.generate` (both infinite by default) in practice.
- Once `takeWhile`'s predicate fails for one element, it never re-evaluates the predicate against any subsequent element, even if a later element would have passed — this is the fundamental behavioral distinction from `filter`, and exactly the property that makes `takeWhile` correct for "trust ends at the first anomaly" scenarios like the Level 2 sensor-reading example.
- For a finite, already-materialized `List`, achieving the same "prefix" result without `takeWhile` (pre-Java-9) required a manual loop with an early `break` — `takeWhile` expresses that same imperative idea declaratively, as part of a stream pipeline, composable with `map`, `filter`, and other stream operations before the final terminal operation.
- `takeWhile` evaluates its predicate lazily, in encounter order, one element at a time — for a stream backed by an expensive-to-compute source (a paginated API call, a database cursor), this means work genuinely stops being done the moment the condition first fails, not merely that results stop being *returned* after already having been fully computed.
