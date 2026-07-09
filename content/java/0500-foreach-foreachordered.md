---
card: java
gi: 500
slug: foreach-foreachordered
title: forEach() / forEachOrdered()
---

## 1. What it is

`Stream.forEach(consumer)` is a **terminal** operation that runs a given `Consumer<T>` once for each element of the stream, purely for its side effects — it doesn't produce a new stream or a return value. `forEachOrdered(consumer)` does the same thing but *guarantees* the elements are visited in the stream's encounter order, even for a parallel stream, where plain `forEach` explicitly does **not** make that guarantee.

## 2. Why & when

`forEach` is how a stream pipeline ends when the goal is a side effect (printing, saving, sending, mutating external state) rather than producing a transformed collection. For a sequential stream, `forEach` and `forEachOrdered` behave identically — order is naturally preserved. The distinction only matters for **parallel** streams: `forEach` may process and emit elements in whatever order threads happen to finish, which can be faster since it doesn't need to coordinate ordering, while `forEachOrdered` forces the results to be reported in the original order, at some cost to parallel performance.

You reach for `forEach` by default when performing a side effect on each element and order genuinely doesn't matter (or the stream is sequential, where order is preserved anyway). You reach for `forEachOrdered` specifically when processing a **parallel** stream but the *side effect itself* (e.g. printing a numbered report) must happen in the original order.

## 3. Core concept

```java
import java.util.stream.*;

Stream.of("a", "b", "c").forEach(System.out::println); // sequential: order preserved naturally

Stream.of("a", "b", "c").parallel()
        .forEach(System.out::println); // parallel: order NOT guaranteed

Stream.of("a", "b", "c").parallel()
        .forEachOrdered(System.out::println); // parallel: order guaranteed, "a" "b" "c"
```

`forEach` and `forEachOrdered` both consume the stream by running a side-effecting action on each element; only `forEachOrdered` guarantees that action happens in the original encounter order under parallel execution.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="forEach on a parallel stream may run out of order; forEachOrdered guarantees original order">
  <rect x="8" y="8" width="624" height="124" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#8b949e" font-size="11" font-family="sans-serif">parallel().forEach(print):</text>
  <rect x="230" y="15" width="40" height="28" fill="#1c2430" stroke="#f85149"/><text x="250" y="34" fill="#f85149" font-size="12" text-anchor="middle" font-family="monospace">c</text>
  <rect x="275" y="15" width="40" height="28" fill="#1c2430" stroke="#f85149"/><text x="295" y="34" fill="#f85149" font-size="12" text-anchor="middle" font-family="monospace">a</text>
  <rect x="320" y="15" width="40" height="28" fill="#1c2430" stroke="#f85149"/><text x="340" y="34" fill="#f85149" font-size="12" text-anchor="middle" font-family="monospace">b</text>
  <text x="390" y="34" fill="#f85149" font-size="10" font-family="sans-serif">(order varies by run)</text>

  <text x="20" y="80" fill="#8b949e" font-size="11" font-family="sans-serif">parallel().forEachOrdered(print):</text>
  <rect x="230" y="65" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="250" y="84" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">a</text>
  <rect x="275" y="65" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="295" y="84" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">b</text>
  <rect x="320" y="65" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="340" y="84" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">c</text>
  <text x="390" y="84" fill="#6db33f" font-size="10" font-family="sans-serif">(always original order)</text>
  <text x="20" y="120" fill="#8b949e" font-size="10" font-family="sans-serif">On a sequential stream, both methods behave identically -- order is always preserved.</text>
</svg>

Parallel `forEach` may report elements in any completion order; `forEachOrdered` always reports them in the stream's defined encounter order.

## 5. Runnable example

Scenario: printing a numbered processing report for a batch of orders — evolved from a plain sequential `forEach`, through demonstrating parallel `forEach`'s unordered behavior, to a version using `forEachOrdered` to guarantee a correctly-numbered report even when processed in parallel.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class ForEachBasic {
    public static void main(String[] args) {
        List<String> orders = List.of("order-1", "order-2", "order-3");

        orders.stream().forEach(order -> System.out.println("Processing " + order));
    }
}
```

**How to run:** `java ForEachBasic.java`

Expected output:
```
Processing order-1
Processing order-2
Processing order-3
```

On this sequential stream, `.forEach(...)` visits each element in the list's natural order and runs the side-effecting print for each — no ordering surprises, since sequential streams always process elements front to back.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class ForEachParallelUnordered {
    public static void main(String[] args) {
        List<Integer> orderIds = IntStream.rangeClosed(1, 8).boxed().toList();

        System.out.println("parallel().forEach output (order may vary between runs):");
        orderIds.parallelStream()
                .forEach(id -> System.out.println("  Handled order-" + id));
    }
}
```

**How to run:** `java ForEachParallelUnordered.java`

Expected output (order of lines varies run to run — this is the point):
```
parallel().forEach output (order may vary between runs):
  Handled order-5
  Handled order-1
  Handled order-7
  Handled order-3
  Handled order-2
  Handled order-8
  Handled order-4
  Handled order-6
```

The real-world concern this adds: `.parallelStream()` splits the work across multiple threads, and plain `.forEach(...)` reports each element's result as soon as that thread finishes — with no guarantee about which thread finishes first. The eight `"Handled order-N"` lines will still all appear, but potentially in a different order each time the program runs, which is fine for independent side effects but wrong whenever the *order of output itself* matters.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class ForEachOrderedReport {
    public static void main(String[] args) {
        List<Integer> orderIds = IntStream.rangeClosed(1, 8).boxed().toList();

        System.out.println("parallel().forEachOrdered output (always this order):");
        orderIds.parallelStream()
                .map(id -> "  Line " + id + ": order-" + id + " handled")
                .forEachOrdered(System.out::println); // guarantees original order even though work ran in parallel
    }
}
```

**How to run:** `java ForEachOrderedReport.java`

Expected output:
```
parallel().forEachOrdered output (always this order):
  Line 1: order-1 handled
  Line 2: order-2 handled
  Line 3: order-3 handled
  Line 4: order-4 handled
  Line 5: order-5 handled
  Line 6: order-6 handled
  Line 7: order-7 handled
  Line 8: order-8 handled
```

This fixes the Level 2 problem: the underlying `.map(...)` work can still be distributed across threads for speed, but `.forEachOrdered(...)` buffers and re-sequences the results so the final printed report is always numbered `1` through `8` in order — every run, regardless of which thread happened to finish which element's work first. This is the correct choice whenever a parallel stream's side effects must be observed in the original order, such as a report, log, or ordered file write.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `orderIds` is built as `[1, 2, 3, 4, 5, 6, 7, 8]` via `IntStream.rangeClosed(1, 8).boxed().toList()` (see [[intstream-range-rangeclosed]] and [[boxed]]).

`orderIds.parallelStream()` creates a parallel stream, which the JVM's common `ForkJoinPool` may split across multiple worker threads, each processing a different chunk of the eight elements concurrently. `.map(id -> "  Line " + id + ": order-" + id + " handled")` transforms each `Integer` into a formatted line string — this transformation work itself may happen in any order across threads, and for elements like `5` or `3`, their formatted string might be *computed* before element `1`'s string is.

`.forEachOrdered(System.out::println)` is the terminal operation. Despite the `map` step's work potentially finishing out of order across threads, `forEachOrdered` is specifically documented to process results in the stream's encounter order — internally, it coordinates so that even though thread A might finish computing the line for `id=6` before thread B finishes `id=2`, the *printing* still happens strictly in order: line for `1`, then `2`, then `3`, and so on, waiting as needed for earlier elements' results to become available before printing later ones.

```
Parallel computation (order of completion may vary):
  thread X computes: "Line 5: ...", "Line 6: ...", ...
  thread Y computes: "Line 1: ...", "Line 2: ...", ...
  thread Z computes: "Line 3: ...", "Line 4: ...", ...

forEachOrdered printing (always in encounter order):
  print "Line 1: ..."  (waits if not yet computed)
  print "Line 2: ..."
  print "Line 3: ..."
  ... through "Line 8: ..."
```

The final printed output is always `Line 1` through `Line 8` in strict numeric order, every time the program runs — even though the underlying `map` computation was free to run in parallel across threads for speed, `forEachOrdered` guarantees the *observable side effect* (the print) respects the original sequence.

## 7. Gotchas & takeaways

> `forEach` on a **sequential** stream already preserves encounter order — there's no difference in behavior from `forEachOrdered` in that case, only in name. The distinction only matters once `.parallel()`/`.parallelStream()` is involved; using `forEachOrdered` on a sequential stream just adds an unnecessary (if harmless) hint with no behavioral effect.

- `forEach(consumer)` is a terminal operation for side effects; it does not guarantee order on a parallel stream.
- `forEachOrdered(consumer)` guarantees the side effect runs in the stream's original encounter order, even under parallel execution — at the cost of some parallel-execution efficiency, since results must be coordinated back into order.
- On a sequential stream, both behave identically; the choice only matters once a stream is (or might become) parallel.
- Use `forEachOrdered` when a parallel stream's side effects (printing, ordered writes, numbered reports) must reflect the original sequence; use plain `forEach` when the side effects are independent of each other and order doesn't matter.
- Both are terminal operations — like all terminal operations, calling either consumes the stream, and the stream cannot be reused afterward.
