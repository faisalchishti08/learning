---
card: java
gi: 741
slug: record-deconstruction-patterns
title: Record deconstruction patterns
---

## 1. What it is

Record deconstruction is the specific mechanic **inside** [record patterns](0740-record-patterns-standardized.md): the compiler takes a record type's declared component list and generates, for free, the ability to pull those components apart in a pattern — including **recursively**, through as many levels of nested records as the data actually has. "Deconstruction" is the general term for this: turning a structured value back into its constituent parts via pattern matching, the mirror image of a record's constructor putting parts together into a whole. This entry goes deeper than the basic case in [record patterns — standardized](0740-record-patterns-standardized.md) to cover **multi-level nesting**, deconstruction combined with **generics**, and deconstruction inside collection-processing code.

## 2. Why & when

Real data is rarely flat. A tree-shaped or graph-shaped structure — an AST node, a JSON document model, a linked list of events — is naturally represented as records nested inside records inside records, and processing it means repeatedly asking "what shape is this subtree, and what are its parts?" Without deconstruction patterns, walking such a structure means chains of `instanceof` checks and getter calls at every level, with the nesting depth directly reflected in code depth and repetition. Deconstruction patterns let you write the **shape you expect** as a single pattern literal that mirrors the data's actual structure, and the compiler fills in all the intermediate type checks and accessor calls. This is the same reason functional languages with algebraic data types (Haskell, ML, Scala, Rust) have had pattern matching on nested structures for decades — once your data has a tree shape, code that processes it reads far more clearly when it's shaped the same way as the data.

## 3. Core concept

```java
record Point(int x, int y) {}
record Line(Point start, Point end) {}
record Path(Line first, Line second) {}

static int totalHorizontalSpan(Object obj) {
    // three levels deep: Path -> Line -> Point, all in one pattern
    if (obj instanceof Path(Line(Point(var x1, var y1), Point(var x2, var y2)),
                             Line(Point(var x3, var y3), Point(var x4, var y4)))) {
        return Math.abs(x2 - x1) + Math.abs(x4 - x3);
    }
    return 0;
}
```

One pattern reaches through `Path` → `Line` → `Point` and names eight leaf variables directly; no intermediate variable for the `Line`s or inner `Point`s is ever created.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A nested record structure and the single deconstruction pattern that reaches all the way to its leaves">
  <rect x="260" y="15" width="120" height="36" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="38" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Path</text>

  <line x1="290" y1="51" x2="150" y2="80" stroke="#8b949e"/>
  <line x1="350" y1="51" x2="490" y2="80" stroke="#8b949e"/>

  <rect x="90" y="80" width="120" height="36" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="103" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Line (first)</text>
  <rect x="430" y="80" width="120" height="36" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="490" y="103" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Line (second)</text>

  <line x1="120" y1="116" x2="60" y2="145" stroke="#8b949e"/>
  <line x1="180" y1="116" x2="240" y2="145" stroke="#8b949e"/>
  <line x1="460" y1="116" x2="400" y2="145" stroke="#8b949e"/>
  <line x1="520" y1="116" x2="580" y2="145" stroke="#8b949e"/>

  <rect x="10" y="145" width="100" height="34" rx="6" fill="#0f1620" stroke="#8b949e"/>
  <text x="60" y="167" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Point(x1,y1)</text>
  <rect x="190" y="145" width="100" height="34" rx="6" fill="#0f1620" stroke="#8b949e"/>
  <text x="240" y="167" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Point(x2,y2)</text>
  <rect x="350" y="145" width="100" height="34" rx="6" fill="#0f1620" stroke="#8b949e"/>
  <text x="400" y="167" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Point(x3,y3)</text>
  <rect x="530" y="145" width="100" height="34" rx="6" fill="#0f1620" stroke="#8b949e"/>
  <text x="580" y="167" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Point(x4,y4)</text>

  <text x="320" y="215" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">One pattern literal reaches every leaf variable across three nesting levels</text>
</svg>

*Deconstruction patterns mirror a data structure's actual shape, however deeply nested it is.*

## 5. Runnable example

Scenario: processing a small tree of line segments (a `Path` made of `Line`s made of `Point`s), growing from a single flat destructure to a generic, list-processing version.

### Level 1 — Basic

```java
record Point(int x, int y) {}
record Line(Point start, Point end) {}

public class DeconstructBasic {
    static double length(Object obj) {
        if (obj instanceof Line(Point(var x1, var y1), Point(var x2, var y2))) {
            return Math.hypot(x2 - x1, y2 - y1);
        }
        return 0.0;
    }

    public static void main(String[] args) {
        System.out.println(length(new Line(new Point(0, 0), new Point(3, 4))));
    }
}
```

**How to run:** `java DeconstructBasic.java` (JDK 21+). Expected output: `5.0`.

This is a two-level deconstruction: `Line` → two `Point`s → four `int`s, all bound directly in the `instanceof` condition.

### Level 2 — Intermediate

```java
record Point(int x, int y) {}
record Line(Point start, Point end) {}
record Path(Line first, Line second) {}

public class DeconstructPath {
    static double totalLength(Object obj) {
        if (obj instanceof Path(
                Line(Point(var x1, var y1), Point(var x2, var y2)),
                Line(Point(var x3, var y3), Point(var x4, var y4)))) {
            double a = Math.hypot(x2 - x1, y2 - y1);
            double b = Math.hypot(x4 - x3, y4 - y3);
            return a + b;
        }
        return 0.0;
    }

    public static void main(String[] args) {
        Path path = new Path(
            new Line(new Point(0, 0), new Point(3, 4)),
            new Line(new Point(3, 4), new Point(6, 8))
        );
        System.out.println(totalLength(path));
    }
}
```

**How to run:** `java DeconstructPath.java`. Expected output: `10.0`.

The real-world concern added: a **three-level** nesting (`Path` → `Line` → `Point`), which is where deconstruction patterns start to pay for themselves — the equivalent code with manual getters would need six chained accessor calls (`path.first().start().x()`, etc.) before reaching a single usable `int`.

### Level 3 — Advanced

```java
import java.util.*;

record Point(int x, int y) {}
record Line(Point start, Point end) {}

public class DeconstructGeneric {
    // works over any list of Line-shaped records, deconstructing each one
    static double totalLength(List<Line> lines) {
        double total = 0.0;
        for (Object obj : lines) {
            if (obj instanceof Line(Point(var x1, var y1), Point(var x2, var y2))) {
                total += Math.hypot(x2 - x1, y2 - y1);
            } else {
                throw new IllegalArgumentException("not a valid Line: " + obj);
            }
        }
        return total;
    }

    public static void main(String[] args) {
        List<Line> lines = List.of(
            new Line(new Point(0, 0), new Point(3, 4)),
            new Line(new Point(3, 4), new Point(6, 8)),
            new Line(new Point(6, 8), new Point(6, 0))
        );
        System.out.printf("total length = %.2f%n", totalLength(lines));

        List<Line> empty = List.of();
        System.out.printf("total length = %.2f%n", totalLength(empty));
    }
}
```

**How to run:** `java DeconstructGeneric.java`.

This handles the production-flavored hard case: deconstruction applied inside a **loop over a generic `List<Line>`**, with an explicit `else` branch that fails loudly (`IllegalArgumentException`) rather than silently skipping malformed input — important once the deconstructed values come from a heterogeneous or externally-sourced collection rather than a single known literal.

## 6. Walkthrough

Tracing `DeconstructGeneric.main`:

1. `main` builds a `List<Line>` of three connected segments and calls `totalLength(lines)`.
2. Inside `totalLength`, the `for` loop iterates each element as `Object obj` (deliberately widened, to demonstrate the deconstruction actually re-validates the type at each step rather than assuming it).
3. For the first `Line`, `obj instanceof Line(Point(var x1, var y1), Point(var x2, var y2))` runs: it checks `obj` is a `Line`, then reaches into `start()` and `end()` and deconstructs each into two `int`s — `x1=0, y1=0, x2=3, y2=4` — binding all four in the `if` condition.
4. `Math.hypot(x2 - x1, y2 - y1)` computes `hypot(3, 4) = 5.0`, added to `total`.
5. The loop repeats for the second segment (`hypot(3,4) = 5.0`) and third segment (`hypot(0,-8) = 8.0`), accumulating `total = 5.0 + 5.0 + 8.0 = 18.0`.
6. `totalLength` returns `18.0`, and `main` prints it with two decimal places.
7. The second call, `totalLength(empty)`, loops zero times (the `for` body never executes), so `total` stays `0.0` and the method returns immediately — demonstrating the deconstruction logic degrades safely to an empty collection with no special-casing needed.

Expected output:
```
total length = 18.00
total length = 0.00
```

## 7. Gotchas & takeaways

> **Gotcha:** a deconstruction pattern requires **every** component to be named (or replaced with `var` or `_` — see [unnamed patterns & variables](0751-unnamed-patterns-variables-preview.md), a later preview feature). You can't partially deconstruct a record and leave the rest as the whole record object in the same pattern — if you only care about one field, use plain `instanceof Line l` and call `l.start()` instead of forcing an unused variable into the pattern.

- Deconstruction nests to arbitrary depth — the pattern's shape should mirror the data's actual shape.
- Prefer `var` for inner component types once the record declarations make the types obvious — it keeps deeply nested patterns readable.
- Combine with a `for` loop or stream `map`/`filter` to deconstruct every element of a collection uniformly.
- When deconstruction might not match (heterogeneous input), decide explicitly whether a non-match should be skipped, defaulted, or thrown as an error — don't let it fail silently.
- The compiler generates the deconstruction from the record's canonical component list, so adding, removing, or reordering components is a compile-time break at every pattern site that assumed the old shape — treat that as a helpful signal, not friction to route around.
