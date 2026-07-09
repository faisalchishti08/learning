---
card: java
gi: 733
slug: record-patterns-2nd-preview
title: Record patterns (2nd preview)
---

## 1. What it is

**Java 20** (JEP 432) is the **second preview** of [record patterns](0727-record-patterns-preview.md), refining the feature first previewed in Java 19. The core capability — destructuring a record's components directly in an `instanceof` or `switch` pattern, with support for nesting — carries forward unchanged. What's new in this round is support for record patterns in the **enhanced `for` loop**: a `for (Point(var x, var y) : points)` can now destructure each element of an iterable directly in the loop header, extending record-pattern destructuring beyond `instanceof` and `switch` into a third syntactic position. As with all preview features, it requires `--enable-preview` and remained subject to further refinement.

## 2. Why & when

Once record patterns proved useful for destructuring inside `instanceof` and `switch`, an obvious follow-up question was: what about iterating over a collection of records? Before this addition, looping over a `List<Point>` and wanting each point's `x` and `y` as separate local variables meant either calling `.x()`/`.y()` accessors inside the loop body, or destructuring via a `switch` expression inside the loop — both extra ceremony for something that's conceptually just "destructure each element as I go." Extending record patterns into the enhanced `for` loop closes this gap directly: `for (Point(var x, var y) : points)` reads naturally as "for each point, taking apart its x and y," matching the same destructuring syntax already familiar from `instanceof` and `switch`, applied at the most common place records get iterated — a loop. This is a small, surgical addition rather than a new capability, but it removes a recurring bit of friction anywhere code iterates over a collection of records and immediately wants to work with their components rather than the record object itself.

## 3. Core concept

```java
record Point(int x, int y) {}
List<Point> points = List.of(new Point(1, 2), new Point(3, 4));

// Before: accessor calls inside the loop body.
for (Point p : points) {
    System.out.println(p.x() + p.y());
}

// Java 20 2nd preview: destructure directly in the for-loop header.
for (Point(var x, var y) : points) {
    System.out.println(x + y); // x and y already bound, no p.x()/p.y()
}
```

The pattern in the `for` header works exactly like the pattern in an `instanceof` or `switch` case — type check plus destructuring, just applied once per loop iteration.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A for loop with a record pattern in its header destructures each element of the iterable directly, binding component variables fresh on every iteration">
  <rect x="20" y="20" width="600" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="45" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">for (Point(var x, var y) : points) { ... }</text>
  <text x="330" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">destructure applied once per element, fresh each iteration</text>

  <rect x="30" y="110" width="90" height="40" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="75" y="134" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Point(1,2)</text>
  <text x="75" y="170" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">x=1, y=2</text>

  <rect x="140" y="110" width="90" height="40" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="185" y="134" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Point(3,4)</text>
  <text x="185" y="170" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">x=3, y=4</text>
</svg>

Each list element is destructured on entry to that iteration, exactly as if written as a fresh `instanceof` check each time.

## 5. Runnable example

Scenario: processing a batch of 2D points read from a data source. It grows from basic for-loop destructuring computing distances, to nested record-pattern destructuring over a list of `Line`s extracting all four leaf coordinates per iteration, to a version filtering and aggregating using destructured values directly, combined with a guard-like conditional inside the loop — the realistic shape of quick data-processing code over a collection of records.

### Level 1 — Basic

```java
// File: ForLoopPatternBasic.java
// Run with --enable-preview: record patterns (2nd preview) in Java 20 adds
// destructuring support to the enhanced for loop.
import java.util.List;

public class ForLoopPatternBasic {
    record Point(int x, int y) {}

    public static void main(String[] args) {
        List<Point> points = List.of(new Point(3, 4), new Point(6, 8), new Point(1, 1));

        for (Point(var x, var y) : points) {
            double distance = Math.sqrt(x * x + y * y);
            System.out.println("(" + x + "," + y + ") distance from origin: " + distance);
        }
    }
}
```

**How to run:**
```
javac --release 20 --enable-preview ForLoopPatternBasic.java
java --enable-preview ForLoopPatternBasic
```

Expected output:
```
(3,4) distance from origin: 5.0
(6,8) distance from origin: 10.0
(1,1) distance from origin: 1.4142135623730951
```

### Level 2 — Intermediate

```java
// File: ForLoopPatternNestedIntermediate.java
// Extends to NESTED record patterns in the for-loop header, destructuring a
// list of Lines all the way down to their four leaf int coordinates per
// iteration — the real-world concern of processing structured records at scale.
import java.util.List;

public class ForLoopPatternNestedIntermediate {
    record Point(int x, int y) {}
    record Line(Point start, Point end) {}

    public static void main(String[] args) {
        List<Line> lines = List.of(
                new Line(new Point(0, 0), new Point(3, 4)),
                new Line(new Point(1, 1), new Point(1, 5)),
                new Line(new Point(2, 2), new Point(2, 2)));

        double totalLength = 0;
        for (Line(Point(var x1, var y1), Point(var x2, var y2)) : lines) {
            double length = Math.hypot(x2 - x1, y2 - y1);
            System.out.println("line (" + x1 + "," + y1 + ")->(" + x2 + "," + y2 + "): length=" + length);
            totalLength += length;
        }
        System.out.println("Total length: " + totalLength);
    }
}
```

**How to run:**
```
javac --release 20 --enable-preview ForLoopPatternNestedIntermediate.java
java --enable-preview ForLoopPatternNestedIntermediate
```

Expected output:
```
line (0,0)->(3,4): length=5.0
line (1,1)->(1,5): length=4.0
line (2,2)->(2,2): length=0.0
Total length: 9.0
```

### Level 3 — Advanced

```java
// File: ForLoopPatternAggregateAdvanced.java
// Filters and aggregates directly using destructured loop variables,
// combined with a conditional inside the loop body — the production-flavored
// shape of a quick report over a batch of structured records.
import java.util.List;

public class ForLoopPatternAggregateAdvanced {
    record Point(int x, int y) {}
    record Line(String label, Point start, Point end) {}

    public static void main(String[] args) {
        List<Line> lines = List.of(
                new Line("A", new Point(0, 0), new Point(3, 4)),
                new Line("B", new Point(1, 1), new Point(1, 1)),   // degenerate: zero length
                new Line("C", new Point(0, 0), new Point(6, 8)),
                new Line("D", new Point(2, 2), new Point(2, 6)));

        int validCount = 0;
        int degenerateCount = 0;
        double longestLength = 0;
        String longestLabel = "";

        for (Line(var label, Point(var x1, var y1), Point(var x2, var y2)) : lines) {
            double length = Math.hypot(x2 - x1, y2 - y1);
            if (length == 0) {
                degenerateCount++;
                System.out.println("skipping degenerate line: " + label);
                continue;
            }
            validCount++;
            if (length > longestLength) {
                longestLength = length;
                longestLabel = label;
            }
            System.out.println("line " + label + ": length=" + length);
        }

        System.out.println("Valid lines: " + validCount + ", degenerate: " + degenerateCount);
        System.out.println("Longest: " + longestLabel + " (" + longestLength + ")");
    }
}
```

**How to run:**
```
javac --release 20 --enable-preview ForLoopPatternAggregateAdvanced.java
java --enable-preview ForLoopPatternAggregateAdvanced
```

Expected output:
```
line A: length=5.0
skipping degenerate line: B
line C: length=10.0
line D: length=4.0
Valid lines: 3, degenerate: 1
Longest: C (10.0)
```

## 6. Walkthrough

1. `ForLoopPatternAggregateAdvanced.main` builds a list of four `Line` records, one deliberately degenerate (start and end points identical), and begins the enhanced `for` loop with the header pattern `Line(var label, Point(var x1, var y1), Point(var x2, var y2))`.
2. On the **first** iteration, the loop takes the first `Line` element (`"A"`, from `(0,0)` to `(3,4)`) and destructures it against that pattern: `label = "A"`, and because `Line`'s second and third components are themselves matched against nested `Point(var x1, var y1)`/`Point(var x2, var y2)` patterns, all four coordinate variables are bound too — `x1=0, y1=0, x2=3, y2=4` — all before a single line of the loop body runs.
3. The loop body computes `length = Math.hypot(3, 4) = 5.0`, which is nonzero, so `validCount` increments and the line is printed as-is.
4. On the **second** iteration, `Line("B", Point(1,1), Point(1,1))` is destructured the same way, binding `x1=1, y1=1, x2=1, y2=1`. `length` computes to `0.0`, so the `if (length == 0)` branch runs: `degenerateCount` increments, a message prints, and `continue` skips straight to the next iteration — leaving `validCount` and `longestLength` untouched for this element.
5. This pattern repeats for `"C"` (length `10.0`, becoming the new longest) and `"D"` (length `4.0`, not longer than `"C"`'s), with fresh `label, x1, y1, x2, y2` bindings destructured anew at the start of each iteration — variables from one iteration never leak into or affect the next, since each iteration's pattern match is entirely independent.
6. After the loop finishes all four elements, the accumulated `validCount` (`3`), `degenerateCount` (`1`), and `longestLabel`/`longestLength` (`"C"`, `10.0`) are printed — demonstrating that ordinary loop-scoped aggregation logic (counters, running maximums) composes naturally with per-iteration record-pattern destructuring, exactly as it would with any other `for` loop variable.

```
for (Line(label, Point(x1,y1), Point(x2,y2)) : lines)

iteration 1: Line("A", Point(0,0), Point(3,4))
    -> destructure -> label="A", x1=0,y1=0,x2=3,y2=4
    -> length=5.0 (nonzero) -> validCount++, print

iteration 2: Line("B", Point(1,1), Point(1,1))
    -> destructure -> label="B", x1=1,y1=1,x2=1,y2=1
    -> length=0.0 -> degenerateCount++, continue (skip rest of body)

iteration 3, 4: same pattern, fresh bindings each time
```

## 7. Gotchas & takeaways

> This is a **preview feature in Java 20** (second preview of record patterns) — `javac` needs `--release 20 --enable-preview` and `java` needs `--enable-preview`; the enhanced-for-loop destructuring capability shown here was new in this specific round and continued toward eventual joint finalization with the rest of record patterns in a later JDK.
- The pattern in a `for` loop header must be **irrefutable** for the element type being iterated — if `points` were a `List<Object>` containing a mix of types, `for (Point(var x, var y) : points)` would not compile, since the compiler cannot guarantee every element actually is a `Point`; this differs from `instanceof` and guarded `switch` cases, which are explicitly designed to handle possible non-matches.
- Variables bound by a for-loop record pattern are scoped to that single iteration's loop body, exactly like an ordinary `for (Point p : points)` loop variable — they do not persist or accumulate across iterations, which is why the aggregation counters in Level 3 are declared *outside* the loop.
- This addition is best understood as filling a gap, not introducing new semantics: the destructuring rules (nesting, `var` vs explicit types) are identical to record patterns in `instanceof` and `switch`, just applied automatically once per loop iteration instead of once per explicit check.
- Combining destructuring with early-exit control flow (`continue`, as in Level 3's degenerate-line skip) works exactly as it would in any ordinary loop — the pattern match happens once at the top of each iteration, and normal loop control statements operate on the loop as a whole, unaffected by how the current element got destructured.
