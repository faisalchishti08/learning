---
card: java
gi: 727
slug: record-patterns-preview
title: Record patterns (preview)
---

## 1. What it is

**Java 19** (JEP 405) previews **record patterns**: an extension to `instanceof` and `switch` pattern matching that lets a single pattern both check a value's type *and* destructure it into its components in one step, when that type is a [record](0687-records-standardized.md). Instead of matching `case Point p` and then separately calling `p.x()` and `p.y()`, a record pattern writes `case Point(int x, int y)` directly — the match succeeds only if the value is a `Point`, and if it does, `x` and `y` are bound immediately as local variables holding the record's component values, no accessor calls needed. Record patterns can also **nest**, letting one pattern destructure a record containing other records several levels deep in a single expression. Being a preview feature in Java 19, it requires `--enable-preview`.

## 2. Why & when

Records ([standardized in Java 16](0687-records-standardized.md)) are transparent, immutable data carriers — their whole design point is that a record's shape *is* its public contract, exposed automatically through generated accessor methods. Pattern matching for `instanceof` and `switch` (finalized around the same era) already let code check a value's type without an explicit cast, but for records specifically, the natural next step is obvious: since a record's components are already public and known, why require a second step of calling accessors to get at them? Code processing nested record structures — a `Point(int x, int y)` inside a `Line(Point start, Point end)`, or a JSON-like tree of records — otherwise ends up as a chain of type checks followed by a chain of accessor calls, each redundant with the pattern that just proved the type. Record patterns collapse both steps into one: the type check and the destructuring happen together, syntactically visible right where the case is declared, mirroring how algebraic data types are matched and destructured in many other languages. This matters most for code processing `sealed` hierarchies of records — parsing expression trees, geometric shapes, protocol messages — where nested destructuring is common and repetitive accessor chains genuinely hurt readability.

## 3. Core concept

```java
record Point(int x, int y) {}

// Before record patterns: type check, then separate accessor calls.
if (obj instanceof Point p) {
    int x = p.x();
    int y = p.y();
    System.out.println(x + y);
}

// With record patterns: type check AND destructuring in one step.
if (obj instanceof Point(int x, int y)) {
    System.out.println(x + y); // x and y are already bound, no p.x()/p.y() needed
}
```

The same pattern form works inside `switch` cases, and can nest arbitrarily deep for records containing other records.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A record pattern like Line(Point(int x1,int y1), Point(int x2,int y2)) both checks the type at every level and binds every leaf component in one expression">
  <rect x="20" y="20" width="600" height="160" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="45" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">Line(Point(int x1, int y1), Point(int x2, int y2))</text>

  <rect x="60" y="70" width="240" height="90" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="180" y="92" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Point(int x1, int y1)</text>
  <text x="180" y="115" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">checks: is this a Point?</text>
  <text x="180" y="135" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">binds: x1, y1</text>

  <rect x="340" y="70" width="240" height="90" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="460" y="92" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Point(int x2, int y2)</text>
  <text x="460" y="115" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">checks: is this a Point?</text>
  <text x="460" y="135" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">binds: x2, y2</text>
</svg>

One pattern, two nesting levels, four bound variables — no accessor calls written anywhere.

## 5. Runnable example

Scenario: processing 2D geometric shapes built from nested records (`Point`, `Line`, `Rectangle`). The example grows from a basic single-level destructuring, to nested record patterns extracting coordinates from a `Line`'s two `Point`s directly, to a `switch` over a `sealed` shape hierarchy combining nested record patterns with `when` guards for a realistic geometry-processing routine.

### Level 1 — Basic

```java
// File: RecordPatternBasic.java
// Run with --enable-preview: record patterns are a preview feature in Java 19.
public class RecordPatternBasic {
    record Point(int x, int y) {}

    static String describe(Object obj) {
        if (obj instanceof Point(int x, int y)) {
            return "Point at (" + x + ", " + y + "), distance from origin: "
                    + Math.sqrt(x * x + y * y);
        }
        return "not a point";
    }

    public static void main(String[] args) {
        System.out.println(describe(new Point(3, 4)));
        System.out.println(describe("hello"));
    }
}
```

**How to run:**
```
javac --release 19 --enable-preview RecordPatternBasic.java
java --enable-preview RecordPatternBasic
```

Expected output:
```
Point at (3, 4), distance from origin: 5.0
not a point
```

### Level 2 — Intermediate

```java
// File: RecordPatternNestedIntermediate.java
// Extends to a NESTED record (Line containing two Points), destructured in
// one pattern down to the leaf int components — no p.x()/p.y() anywhere.
public class RecordPatternNestedIntermediate {
    record Point(int x, int y) {}
    record Line(Point start, Point end) {}

    static double length(Object obj) {
        if (obj instanceof Line(Point(int x1, int y1), Point(int x2, int y2))) {
            int dx = x2 - x1;
            int dy = y2 - y1;
            return Math.sqrt(dx * dx + dy * dy);
        }
        throw new IllegalArgumentException("not a line");
    }

    public static void main(String[] args) {
        Line line = new Line(new Point(0, 0), new Point(3, 4));
        System.out.println("Line length: " + length(line));
    }
}
```

**How to run:**
```
javac --release 19 --enable-preview RecordPatternNestedIntermediate.java
java --enable-preview RecordPatternNestedIntermediate
```

Expected output:
```
Line length: 5.0
```

This adds the real-world concern: a two-level nested pattern binding four leaf variables (`x1, y1, x2, y2`) in one `instanceof` check, replacing what would otherwise be `line.start().x()`, `line.start().y()`, `line.end().x()`, `line.end().y()`.

### Level 3 — Advanced

```java
// File: RecordPatternSwitchAdvanced.java
// Combines nested record patterns with a switch over a sealed shape
// hierarchy and `when` guards — the production-flavored shape of a
// geometry-processing routine handling several shape kinds and edge cases.
public class RecordPatternSwitchAdvanced {
    record Point(int x, int y) {}

    sealed interface Shape permits Line, Rectangle {}
    record Line(Point start, Point end) implements Shape {}
    record Rectangle(Point topLeft, Point bottomRight) implements Shape {}

    static String classify(Shape shape) {
        return switch (shape) {
            case Line(Point(var x1, var y1), Point(var x2, var y2)) when x1 == x2 && y1 == y2 ->
                    "degenerate line (both points identical)";
            case Line(Point(var x1, var y1), Point(var x2, var y2)) ->
                    "line from (" + x1 + "," + y1 + ") to (" + x2 + "," + y2 + "), length="
                            + String.format("%.2f", Math.hypot(x2 - x1, y2 - y1));
            case Rectangle(Point(var lx, var ly), Point(var rx, var ry)) when rx <= lx || ry <= ly ->
                    "invalid rectangle (non-positive width or height)";
            case Rectangle(Point(var lx, var ly), Point(var rx, var ry)) ->
                    "rectangle " + (rx - lx) + "x" + (ry - ly) + " at (" + lx + "," + ly + ")";
        };
    }

    public static void main(String[] args) {
        System.out.println(classify(new Line(new Point(1, 1), new Point(1, 1))));
        System.out.println(classify(new Line(new Point(0, 0), new Point(3, 4))));
        System.out.println(classify(new Rectangle(new Point(0, 0), new Point(-1, 5))));
        System.out.println(classify(new Rectangle(new Point(0, 0), new Point(4, 3))));
    }
}
```

**How to run:**
```
javac --release 19 --enable-preview RecordPatternSwitchAdvanced.java
java --enable-preview RecordPatternSwitchAdvanced
```

Expected output:
```
degenerate line (both points identical)
line from (0,0) to (3,4), length=5.00
invalid rectangle (non-positive width or height)
rectangle 4x3 at (0,0)
```

## 6. Walkthrough

1. `RecordPatternSwitchAdvanced.main` calls `classify` on four different `Shape` values, exercising each of the four `case` arms in order.
2. For `switch (shape)` with the first value (a `Line` with two identical points), the JVM evaluates cases top to bottom. `case Line(Point(var x1, var y1), Point(var x2, var y2))` first checks: is `shape` a `Line`? Yes. Then, because `Line`'s first component is itself required to match `Point(var x1, var y1)`, it checks: is `line.start()` a `Point`? Yes — and binds `x1`, `y1` to its components without ever explicitly calling `.start().x()`. The same happens for the second component against `x2`, `y2`. All of this destructuring happens as part of a single pattern-match check, before the `when` guard is even evaluated.
3. Only once the full nested pattern has matched and bound all four variables does the `when x1 == x2 && y1 == y2` guard run. For the first input, it's `true`, so `"degenerate line..."` is selected.
4. For the second input (`Line((0,0),(3,4))`), the same nested pattern matches and binds `x1=0, y1=0, x2=3, y2=4`, but this time the guard is `false`, so control falls through to the next `case`: the second `Line(...)` pattern, unguarded, which always matches once a `Line` has been ruled degenerate by the guard above it. It computes the length using `Math.hypot`, printing `5.00`.
5. For the third input (a `Rectangle` where `bottomRight.x()` is `-1`, less than `topLeft.x()` of `0`), the third `case` — `Rectangle(Point(var lx, var ly), Point(var rx, var ry)) when rx <= lx || ry <= ly` — matches the type and destructures all four coordinates, then the guard `rx <= lx || ry <= ly` evaluates `true` (since `rx = -1 <= lx = 0`), producing the invalid-rectangle message.
6. For the fourth input (a valid `Rectangle`), the guarded case's condition is `false`, so control falls through to the final, unguarded `Rectangle(...)` pattern, which computes width and height directly from the bound `lx, ly, rx, ry` variables and formats the result.
7. Throughout, `var` is used inside the nested patterns (`Point(var x1, var y1)`) — record patterns support both explicit types (as in Level 1 and 2, `Point(int x, int y)`) and inferred `var` bindings, chosen here purely for brevity since the compiler already knows each component's type from the record's declaration.

```
classify(new Rectangle(new Point(0,0), new Point(-1,5)))
   |
   v
case Line(...)?                         -> type mismatch (it's a Rectangle), skip
   |
   v
case Rectangle(Point(lx,ly), Point(rx,ry)) when rx<=lx || ry<=ly?
   |
   +-- type matches: Rectangle, both components are Points -> bind lx=0, ly=0, rx=-1, ry=5
   |
   +-- guard: rx(-1) <= lx(0)  -> TRUE
   |
   v
"invalid rectangle (non-positive width or height)"   [STOP]
```

## 7. Gotchas & takeaways

> This is a **preview feature in Java 19** — `javac` needs `--release 19 --enable-preview` and `java` needs `--enable-preview`; nested record patterns and their exact grammar continued to be refined (this was in fact the *first* preview round, distinct from pattern matching for `switch`'s third preview shipping in the same release) before finalization in a later JDK.
- Record patterns only work against **records** — attempting `case SomeClass(int a)` where `SomeClass` is an ordinary class (not a record) is a compile error, since destructuring relies on the record's compiler-known, fixed set of components and accessors.
- Nested record patterns can go arbitrarily deep (`Outer(Middle(Inner(var x)))`), but readability suffers past two or three levels — for deeply nested structures, consider destructuring one level at a time across multiple `case` arms or helper methods instead of one giant nested pattern.
- A record pattern's component patterns can mix explicit types and `var` freely, and can themselves be further type patterns (not just nested records) — e.g. `case Box(Number n)` matches any `Box` whose single component is any kind of `Number`, binding it as `n` with that narrowed type.
- Combining record patterns with `sealed` hierarchies (as in Level 3) is where this feature is most valuable: the compiler can verify a `switch` over a `sealed` interface's record implementations is exhaustive at the *type* level, while `when` guards handle the additional, non-exhaustive-by-construction business rules (degenerate shapes, invalid ranges) layered on top.
