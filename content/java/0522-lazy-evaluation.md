---
card: java
gi: 522
slug: lazy-evaluation
title: Lazy evaluation
---

## 1. What it is

**Lazy evaluation** is the rule that governs how streams execute: intermediate operations (`filter`, `map`, `sorted`, `peek`, and so on) don't do any actual work when you call them — they just build up a description of the pipeline. Nothing happens until a **terminal** operation (`forEach`, `collect`, `count`, `findFirst`, etc.) is invoked, at which point the entire pipeline runs, pulling elements through all the intermediate steps one at a time.

## 2. Why & when

Laziness is what makes streams both efficient and safe to compose freely. Because intermediate operations don't execute immediately, the stream implementation can fuse them together and process each element through the *entire* chain before moving to the next element, rather than materializing a full intermediate list after every step. It's also what makes infinite streams (`Stream.iterate`, `Stream.generate`) usable at all — an infinite source combined with `filter`/`map` never actually tries to process infinitely many elements unless a terminal operation demands it, and even then, only as many as that terminal operation (often combined with `limit`) actually needs.

## 3. Core concept

```java
import java.util.stream.*;

Stream<Integer> pipeline = Stream.of(1, 2, 3)
        .peek(n -> System.out.println("saw: " + n)) // nothing prints yet -- just building the pipeline
        .filter(n -> n > 1);

System.out.println("Pipeline built, nothing has run yet.");

long count = pipeline.count(); // NOW the pipeline actually executes
```

Building the pipeline (chaining `.peek(...).filter(...)`) does no work at all — only calling `.count()` (a terminal operation) triggers execution, and even then it processes each element through the whole chain in one traversal.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Intermediate operations build a pipeline description; only a terminal operation triggers execution">
  <rect x="8" y="8" width="624" height="124" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="100" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/><text x="80" y="40" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">.filter(...)</text>
  <text x="140" y="40" fill="#8b949e" font-size="12" font-family="sans-serif">-&gt;</text>
  <rect x="155" y="20" width="100" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/><text x="205" y="40" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">.map(...)</text>
  <text x="20" y="65" fill="#8b949e" font-size="10" font-family="sans-serif">Building the pipeline: no work happens, just a description.</text>

  <rect x="30" y="85" width="100" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="80" y="105" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">.filter(...)</text>
  <text x="140" y="105" fill="#6db33f" font-size="12" font-family="sans-serif">-&gt;</text>
  <rect x="155" y="85" width="100" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="205" y="105" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">.map(...)</text>
  <text x="280" y="105" fill="#6db33f" font-size="12" font-family="sans-serif">-&gt;</text>
  <rect x="300" y="85" width="110" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="355" y="105" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">.collect(...)</text>
  <text x="20" y="130" fill="#6db33f" font-size="10" font-family="sans-serif">Terminal operation called: the whole pipeline runs now, element by element.</text>
</svg>

The pipeline sits idle until a terminal operation appears — only then does execution actually happen.

## 5. Runnable example

Scenario: searching a large in-memory dataset for the first record meeting several conditions — evolved from demonstrating that intermediate operations do nothing on their own, through observing per-element traversal order with `peek`, to a version exploiting laziness with an infinite generator and short-circuiting to avoid unnecessary work.

### Level 1 — Basic

```java
import java.util.stream.*;

public class LazyBasic {
    public static void main(String[] args) {
        System.out.println("Building pipeline...");
        Stream<Integer> pipeline = Stream.of(1, 2, 3, 4, 5)
                .filter(n -> {
                    System.out.println("filtering: " + n);
                    return n % 2 == 0;
                });
        System.out.println("Pipeline built -- notice nothing printed above except this message.");

        System.out.println("Now calling a terminal operation:");
        long count = pipeline.count();
        System.out.println("Count: " + count);
    }
}
```

**How to run:** `java LazyBasic.java`

Expected output:
```
Building pipeline...
Pipeline built -- notice nothing printed above except this message.
Now calling a terminal operation:
filtering: 1
filtering: 2
filtering: 3
filtering: 4
filtering: 5
Count: 2
```

Building `pipeline` with `.filter(...)` does not run the filter's lambda at all — the `"filtering: N"` messages only appear *after* `.count()` (a terminal operation) is called, proving that intermediate operations are purely descriptive until execution is actually triggered.

### Level 2 — Intermediate

```java
import java.util.stream.*;

public class LazyPerElementOrder {
    public static void main(String[] args) {
        Stream.of(1, 2, 3)
                .peek(n -> System.out.println("filter stage sees: " + n))
                .filter(n -> n % 2 != 0)
                .peek(n -> System.out.println("map stage sees: " + n))
                .map(n -> n * 10)
                .forEach(n -> System.out.println("final result: " + n));
    }
}
```

**How to run:** `java LazyPerElementOrder.java`

Expected output:
```
filter stage sees: 1
map stage sees: 1
final result: 10
filter stage sees: 2
filter stage sees: 3
map stage sees: 3
final result: 30
```

The real-world concern this adds: laziness doesn't just mean "delayed" — it means each element is pushed through the **entire pipeline, one element at a time**, rather than the stream fully filtering all elements first, then fully mapping all survivors. Element `1` passes through `filter` (kept) then immediately through `map` and `forEach`, entirely before element `2` is even looked at — `2` fails the filter and is discarded on the spot, never reaching the `map` stage at all. This element-by-element traversal is what allows laziness to combine naturally with short-circuiting operations like `findFirst`/`limit`.

### Level 3 — Advanced

```java
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.*;

public class LazyInfiniteShortCircuit {
    public static void main(String[] args) {
        AtomicInteger generatedCount = new AtomicInteger(0);

        // An infinite stream of candidate IDs -- only as many are generated as are actually needed.
        var firstValidId = Stream.iterate(1, id -> id + 1)
                .peek(id -> generatedCount.incrementAndGet())
                .filter(LazyInfiniteShortCircuit::isValidId)
                .findFirst();

        System.out.println("First valid ID: " + firstValidId.orElse(-1));
        System.out.println("IDs generated to find it: " + generatedCount.get());
    }

    static boolean isValidId(int id) {
        // Simulates an expensive validity check -- pretend only multiples of 7 above 20 are valid.
        return id > 20 && id % 7 == 0;
    }
}
```

**How to run:** `java LazyInfiniteShortCircuit.java`

Expected output:
```
First valid ID: 21
IDs generated to find it: 21
```

This combines laziness with an **infinite** source (`Stream.iterate`, see [[stream-iterate]]) and a **short-circuiting** terminal operation (`findFirst`). Even though `Stream.iterate(1, id -> id + 1)` could generate infinitely many IDs, laziness ensures only as many are actually generated as `findFirst` needs to find its answer — exactly `21` IDs here, stopping the instant a valid one (`21`, the first multiple of `7` above `20`) is found, rather than generating some arbitrary batch upfront or running forever.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `generatedCount` starts at `0`.

`Stream.iterate(1, id -> id + 1)` describes an infinite, lazy sequence `1, 2, 3, ...` — no values are actually produced yet. `.peek(id -> generatedCount.incrementAndGet())` and `.filter(LazyInfiniteShortCircuit::isValidId)` chain onto it, still lazily — no execution has happened at this point, only pipeline construction. `.findFirst()` is the terminal operation that finally triggers execution.

`findFirst()` begins pulling elements one at a time, driving each one through the full chain before requesting the next. It pulls `1`: `peek` runs, `generatedCount` becomes `1`; `filter` checks `isValidId(1)`, i.e. `1 > 20 && 1 % 7 == 0` — `1 > 20` is `false`, so the whole condition is `false`, `1` is rejected. `findFirst` requests the next element.

It pulls `2`: `peek` runs, `generatedCount` becomes `2`; `isValidId(2)` is `false` (same reason). This continues, one element at a time, up through `20`: each pulled, `peek`'s counter incremented, each failing `isValidId` since none satisfy `id > 20` yet.

It pulls `21`: `peek` runs, `generatedCount` becomes `21`; `isValidId(21)` checks `21 > 20 && 21 % 7 == 0` — `21 > 20` is `true`, `21 % 7 == 0` is `true` (since `21 = 3 * 7`), so the whole condition is `true`. `21` passes the filter. `findFirst()` now has its answer and stops immediately — `Stream.iterate` is never asked for `22` or beyond.

```
pull 1  -> peek(count=1)  -> isValidId(1):  1>20 false          -> rejected
pull 2  -> peek(count=2)  -> isValidId(2):  false                -> rejected
...     (continues through 20, each rejected, count incrementing each time)
pull 20 -> peek(count=20) -> isValidId(20): 20>20 false          -> rejected
pull 21 -> peek(count=21) -> isValidId(21): 21>20 true, 21%7==0 true -> ACCEPTED, findFirst stops
```

`firstValidId` is `Optional.of(21)`, printed via `.orElse(-1)` as `"First valid ID: 21"`. `generatedCount.get()` is `21`, printed as `"IDs generated to find it: 21"` — confirming that laziness plus short-circuiting together ensured exactly the minimum necessary work was done, out of an otherwise-infinite source.

## 7. Gotchas & takeaways

> A stream pipeline built but never given a terminal operation does **nothing at all** — not even a syntax or runtime error, just silent inaction. If a `peek` or side-effecting `map` you expected to run never seems to fire, check whether a terminal operation was actually called on that stream; a common bug is building a pipeline and forgetting to `.collect(...)`/`.forEach(...)`/etc. it.

- Intermediate operations (`filter`, `map`, `sorted`, `peek`, ...) are lazy: they only describe the pipeline, doing no actual work when called.
- A terminal operation (`forEach`, `collect`, `count`, `findFirst`, ...) is what triggers the entire pipeline to actually execute.
- Execution proceeds element by element through the *whole* chain, not stage by stage across all elements — one element can finish the entire pipeline before the next element is even examined.
- Laziness is what makes infinite sources (`Stream.iterate`, `Stream.generate`) usable, and what lets short-circuiting operations (`findFirst`, `anyMatch`, `limit`) avoid unnecessary work.
- `sorted()` is a notable exception to pure element-by-element laziness — it must see the *entire* stream before producing its first output element, since any element could affect any other's final position.
