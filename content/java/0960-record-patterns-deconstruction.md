---
card: java
gi: 960
slug: record-patterns-deconstruction
title: Record patterns / deconstruction
---

## 1. What it is

A record pattern is a syntax, standardized in Java 21, that lets you check whether an object is a specific record type *and* simultaneously extract ("deconstruct") its components into individual local variables, all in one expression — `if (obj instanceof Point(int x, int y))` checks that `obj` is a `Point` and, if so, binds `x` and `y` directly to that `Point`'s component values, without ever needing to call `.x()` or `.y()` explicitly. This works because a record's component list is public, structural information the compiler already knows completely (it generated the accessors itself), so the language can offer a shorthand that mirrors the record's own declaration shape directly in the pattern — deconstruction is essentially the reverse of construction, syntactically almost identical to the constructor call that built the object in the first place.

## 2. Why & when

Record patterns solve the repetitive, easy-to-get-wrong sequence of "check the type, then call every accessor one by one to pull out the values you actually care about" that pattern matching without deconstruction requires — `if (obj instanceof Point p) { int x = p.x(); int y = p.y(); ... }` versus the deconstructed `if (obj instanceof Point(int x, int y)) { ... }`, which is shorter, reads more like the record's own declaration, and scales much better once you're matching against records that themselves contain other records (nested patterns, covered separately). They matter most in exactly the scenarios [sealed classes](0961-sealed-permits-clauses.md) are designed for: a closed hierarchy of record variants representing different cases of some domain concept (shapes, arithmetic expressions, API responses), where a `switch` over that hierarchy, using a record pattern per case, lets you both dispatch on the specific variant *and* immediately access its specific data in a single, readable case label — this combination (sealed types + records + pattern matching) is explored as its own topic in [sealed + records + pattern matching synergy](0963-sealed-records-pattern-matching-synergy.md).

## 3. Core concept

```
record Point(int x, int y) {}

Object obj = new Point(3, 4);

// WITHOUT record patterns (pre-Java 21 style):
if (obj instanceof Point p) {
    int x = p.x();      // manual accessor calls, one per component
    int y = p.y();
    System.out.println(x + y);
}

// WITH record patterns (Java 21+):
if (obj instanceof Point(int x, int y)) {   // type check AND destructuring, in one expression
    System.out.println(x + y);              // x, y are ALREADY bound -- no accessor calls needed
}
```

The record pattern's shape — `Point(int x, int y)` — deliberately mirrors the record's own declaration, `record Point(int x, int y)`, making deconstruction read as the visual and conceptual inverse of construction.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A record pattern simultaneously performing a type check and binding each component to a local variable, contrasted with the manual accessor-call approach it replaces" >
  <rect x="20" y="30" width="260" height="90" fill="#1c2430" stroke="#f0883e"/>
  <text x="150" y="48" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Without record pattern</text>
  <text x="150" y="68" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instanceof Point p</text>
  <text x="150" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">int x = p.x();  int y = p.y();</text>
  <text x="150" y="100" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">2 extra manual accessor calls</text>

  <rect x="340" y="30" width="280" height="90" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="48" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">With record pattern</text>
  <text x="480" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instanceof Point(int x, int y)</text>
  <text x="480" y="95" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">type check + x, y bound -- ONE step</text>
</svg>

*A record pattern folds the type check and every accessor call into a single, declarative expression.*

## 5. Runnable example

Scenario: process shape data through pattern matching, evolving from a basic single-record deconstruction, to `switch`-based dispatch over multiple record types, to a more advanced case with nested record patterns reaching into a record contained within another record.

### Level 1 — Basic

```java
public class RecordPatternBasic {
    record Point(int x, int y) {}

    static String describe(Object obj) {
        if (obj instanceof Point(int x, int y)) {
            return "Point at (" + x + ", " + y + "), distance from origin: "
                 + String.format("%.2f", Math.sqrt(x * x + y * y));
        }
        return "not a point";
    }

    public static void main(String[] args) {
        System.out.println(describe(new Point(3, 4)));
        System.out.println(describe("hello"));
    }
}
```

**How to run:** `java RecordPatternBasic.java` (JDK 21+; record patterns are standardized starting in Java 21).

Expected output:
```
Point at (3, 4), distance from origin: 5.00
not a point
```

`obj instanceof Point(int x, int y)` performs both the type check (is `obj` a `Point`?) and, if true, binds `x` and `y` directly from the record's components — both are immediately usable inside the `if` block's body without a single explicit call to `.x()` or `.y()`.

### Level 2 — Intermediate

```java
public class RecordPatternSwitch {
    sealed interface Shape permits Circle, Rectangle {}
    record Circle(double radius) implements Shape {}
    record Rectangle(double width, double height) implements Shape {}

    static double area(Shape shape) {
        return switch (shape) {
            case Circle(double radius) -> Math.PI * radius * radius;
            case Rectangle(double width, double height) -> width * height;
        };
    }

    public static void main(String[] args) {
        Shape c = new Circle(2.0);
        Shape r = new Rectangle(3.0, 4.0);
        System.out.printf("circle area: %.2f%n", area(c));
        System.out.printf("rectangle area: %.2f%n", area(r));
    }
}
```

**How to run:** `java RecordPatternSwitch.java` (JDK 21+).

Expected output:
```
circle area: 12.57
rectangle area: 12.00
```

The real-world concern added: each `switch` case both identifies which concrete `Shape` variant it's handling *and* immediately deconstructs that variant's specific components, all in one case label — no cast, no accessor calls, and (since `Shape` is [sealed](0961-sealed-permits-clauses.md) with exactly two permitted implementers) the compiler can verify this `switch` is exhaustive with no `default` branch needed at all, covered further in [exhaustiveness in switch](0964-exhaustiveness-in-switch.md).

### Level 3 — Advanced

```java
public class RecordPatternNested {
    record Point(int x, int y) {}
    record Line(Point start, Point end) {}

    static double length(Object obj) {
        // NESTED record pattern: destructuring a Line's two Point components,
        // AND each Point's own x/y components, all in one pattern.
        if (obj instanceof Line(Point(int x1, int y1), Point(int x2, int y2))) {
            int dx = x2 - x1;
            int dy = y2 - y1;
            return Math.sqrt(dx * dx + dy * dy);
        }
        throw new IllegalArgumentException("not a Line");
    }

    public static void main(String[] args) {
        Line line = new Line(new Point(0, 0), new Point(3, 4));
        System.out.printf("line length: %.2f%n", length(line));
    }
}
```

**How to run:** `java RecordPatternNested.java` (JDK 21+).

Expected output:
```
line length: 5.00
```

The production-flavored hard case: `Line(Point(int x1, int y1), Point(int x2, int y2))` reaches two levels deep in a single pattern — first confirming `obj` is a `Line`, then confirming and destructuring each of its two `Point` components in turn — collapsing what would otherwise require nested `instanceof` checks or several chained accessor calls (`line.start().x()`, `line.start().y()`, `line.end().x()`, `line.end().y()`) into one flat, readable expression, exactly the kind of case [nested patterns](0969-nested-patterns.md) explores further as its own dedicated topic.

## 6. Walkthrough

Tracing `length(line)` end to end from `RecordPatternNested.main`, where `line = new Line(new Point(0, 0), new Point(3, 4))`:

1. `obj instanceof Line(Point(int x1, int y1), Point(int x2, int y2))` first checks whether `obj` is genuinely a `Line` — it is, so the pattern proceeds to its nested structure.
2. The outer pattern's two sub-patterns correspond to `Line`'s two components, `start` and `end` (both typed `Point`) — the first sub-pattern, `Point(int x1, int y1)`, is matched against `line.start()` (which is `new Point(0, 0)`); since this value is indeed a `Point`, it's further destructured, binding `x1 = 0` and `y1 = 0`.
3. The second sub-pattern, `Point(int x2, int y2)`, is matched against `line.end()` (which is `new Point(3, 4)`); since this is also a `Point`, it's destructured too, binding `x2 = 3` and `y2 = 4`.
4. Because both nested sub-patterns matched successfully, the overall pattern match succeeds, and the `if` block's body executes with all four variables — `x1`, `y1`, `x2`, `y2` — already bound and ready to use, with no explicit accessor calls anywhere in the method body.
5. `dx = x2 - x1` computes `3 - 0 = 3`, and `dy = y2 - y1` computes `4 - 0 = 4` — these represent the horizontal and vertical distance between the line's two endpoints.
6. `Math.sqrt(dx * dx + dy * dy)` computes the Euclidean distance: `Math.sqrt(3*3 + 4*4) = Math.sqrt(9 + 16) = Math.sqrt(25) = 5.0` — this is returned and printed as `line length: 5.00`, demonstrating that the nested record pattern correctly reached two levels into the object graph (`Line` containing two `Point`s, each containing two `int`s) in a single, declarative match, rather than requiring a sequence of manual type checks and accessor calls to achieve the same result.

## 7. Gotchas & takeaways

> **Gotcha:** a record pattern's declared component types must be compatible with the record's actual component types — if you write `Point(long x, long y)` against a record whose actual components are `int`, this is only valid if `int` can be implicitly widened to `long` (which it can); attempting an incompatible or narrowing type in a record pattern's component position is a compile error, not a runtime mismatch, since the compiler already knows every record's exact component types statically.

- A record pattern (`Point(int x, int y)`) performs a type check and destructures the matched record's components into local variables in a single expression, mirroring the record's own declaration shape.
- Record patterns work in `instanceof` expressions and `switch` case labels (both traditional `switch` statements and `switch` expressions), letting each case both identify a variant and immediately access its specific data.
- Combined with [sealed types](0961-sealed-permits-clauses.md), a `switch` using record patterns across every permitted variant can be verified exhaustive by the compiler, with no `default` branch required.
- Record patterns can nest arbitrarily deep, destructuring a record's components even when those components are themselves records, collapsing what would otherwise require several chained accessor calls into one flat, readable pattern.
- A record pattern's declared component types must be assignment-compatible with the record's actual declared component types — this is checked entirely at compile time.
- See [instanceof pattern binding](0965-instanceof-pattern-binding.md) for the simpler, non-deconstructing pattern form this builds on, and [nested patterns](0969-nested-patterns.md) for a deeper look at multi-level record pattern matching specifically.
