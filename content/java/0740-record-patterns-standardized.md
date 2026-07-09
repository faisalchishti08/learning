---
card: java
gi: 740
slug: record-patterns-standardized
title: Record patterns — standardized
---

## 1. What it is

**Java 21** (JEP 440) makes **record patterns** a permanent, standard language feature — no `--enable-preview` flag required. A record pattern lets you match a value against a record type **and simultaneously extract its components into variables** in one step, using `instanceof` or `switch`. Instead of writing `if (obj instanceof Point p) { int x = p.x(); int y = p.y(); ... }`, you write `if (obj instanceof Point(int x, int y))` and `x`/`y` are already bound, ready to use — the pattern both tests the type and destructures it.

## 2. Why & when

Records ([Java 16](0654-records-standardized.md), if present, or the records feature generally) gave Java a concise way to declare immutable data carriers, but using them still meant manually calling accessor methods (`p.x()`, `p.y()`) every time you needed a component after a type check. Record patterns close that gap: since a record's shape (its components, in order) is fixed and known at compile time, the compiler can generate the destructuring for you. This matters most once you have a **hierarchy of records** representing structured data — geometric shapes, AST nodes, JSON-like trees, event payloads — where code constantly needs to ask "is this a `Rectangle`? if so, give me its corners" or "is this a `Circle`? if so, give me its center and radius." Record patterns turn that from an `instanceof`-then-getter dance into a single, readable condition, and because the pattern names the record type explicitly, refactoring a record's components (adding, removing, or reordering fields) produces a clear compile error everywhere the old shape was assumed, rather than a silent runtime bug.

## 3. Core concept

```java
record Point(int x, int y) {}
record Rectangle(Point topLeft, Point bottomRight) {}

static int area(Object shape) {
    if (shape instanceof Rectangle(Point(int x1, int y1), Point(int x2, int y2))) {
        return Math.abs(x2 - x1) * Math.abs(y2 - y1);
    }
    return 0;
}
```

The pattern `Rectangle(Point(int x1, int y1), Point(int x2, int y2))` both confirms `shape` is a `Rectangle` **and** deconstructs its two nested `Point` records into four local `int` variables, all in the `instanceof` condition itself.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A record pattern matches the outer record type and simultaneously destructures nested record components into local variables">
  <rect x="20" y="20" width="600" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">shape instanceof Rectangle(Point(int x1,int y1), Point(int x2,int y2))</text>

  <rect x="40" y="100" width="150" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="115" y="130" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">type check</text>

  <rect x="230" y="100" width="150" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="305" y="130" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">nested destructure</text>

  <rect x="420" y="100" width="180" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="510" y="130" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">x1,y1,x2,y2 bound</text>

  <text x="320" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">One condition replaces a type check plus four accessor calls</text>
</svg>

*Record patterns fold "is it this type" and "give me its fields" into a single expression.*

## 5. Runnable example

Scenario: a tiny shape hierarchy with a function that reports each shape's area — grown from flat records to nested ones with real destructuring.

### Level 1 — Basic

```java
record Point(int x, int y) {}
record Rectangle(Point topLeft, Point bottomRight) {}

public class ShapesBasic {
    static String describe(Object shape) {
        if (shape instanceof Rectangle r) {
            Point tl = r.topLeft();
            Point br = r.bottomRight();
            int w = Math.abs(br.x() - tl.x());
            int h = Math.abs(br.y() - tl.y());
            return "rectangle " + w + "x" + h;
        }
        return "unknown shape";
    }

    public static void main(String[] args) {
        System.out.println(describe(new Rectangle(new Point(0, 0), new Point(4, 3))));
    }
}
```

**How to run:** `java ShapesBasic.java` (JDK 21+).

This is the **pre-record-pattern** style: `instanceof Rectangle r` only tests the type and binds the whole record to `r`; getting at the nested `Point` fields still needs explicit `r.topLeft()`, `r.bottomRight()`, then `.x()`/`.y()` calls on each.

### Level 2 — Intermediate

```java
record Point(int x, int y) {}
record Rectangle(Point topLeft, Point bottomRight) {}

public class ShapesPattern {
    static String describe(Object shape) {
        if (shape instanceof Rectangle(Point(int x1, int y1), Point(int x2, int y2))) {
            int w = Math.abs(x2 - x1);
            int h = Math.abs(y2 - y1);
            return "rectangle " + w + "x" + h;
        }
        return "unknown shape";
    }

    public static void main(String[] args) {
        System.out.println(describe(new Rectangle(new Point(0, 0), new Point(4, 3))));
        System.out.println(describe("not a shape"));
    }
}
```

**How to run:** `java ShapesPattern.java`.

The real-world concern added here: the same logic now reads as **one destructuring condition** instead of type-check-then-getters, and it correctly falls through to `"unknown shape"` for non-matching input (`"not a shape"`) — the pattern match simply fails and the `if` is skipped, no `ClassCastException` risk.

### Level 3 — Advanced

```java
sealed interface Shape permits Rectangle, Circle {}
record Point(int x, int y) {}
record Rectangle(Point topLeft, Point bottomRight) implements Shape {}
record Circle(Point center, int radius) implements Shape {}

public class ShapesAdvanced {
    static double area(Shape shape) {
        return switch (shape) {
            case Rectangle(Point(var x1, var y1), Point(var x2, var y2)) ->
                Math.abs((x2 - x1) * (y2 - y1));
            case Circle(Point(var cx, var cy), var r) -> Math.PI * r * r;
        };
    }

    public static void main(String[] args) {
        Shape[] shapes = {
            new Rectangle(new Point(0, 0), new Point(4, 3)),
            new Circle(new Point(1, 1), 5),
        };
        for (Shape s : shapes) {
            System.out.printf("%s -> area=%.2f%n", s, area(s));
        }
    }
}
```

**How to run:** `java ShapesAdvanced.java`.

This adds the hard, production-flavored case: a **sealed hierarchy** with two shape kinds, combined with **record patterns inside a `switch` expression** (not just `instanceof`), and `var` in place of explicit types since the compiler can infer `x1`, `y1`, `cx`, `r`, etc. from the record's declared component types. Because `Shape` is sealed with exactly two permitted subtypes and both are handled, the compiler can verify the switch is exhaustive with no `default` branch needed — see [exhaustiveness checking in switch](0745-exhaustiveness-checking-in-switch.md) for that guarantee in depth.

## 6. Walkthrough

Tracing `ShapesAdvanced.main`:

1. `main` builds an array holding one `Rectangle` and one `Circle`, both typed as `Shape` (their sealed common interface).
2. The loop calls `area(s)` for each. Inside `area`, the `switch (shape)` expression evaluates `shape`'s runtime type against each `case` pattern **in order**.
3. For the `Rectangle` instance: the pattern `Rectangle(Point(var x1, var y1), Point(var x2, var y2))` matches. The switch first confirms `shape` is a `Rectangle`, then recurses into its two `Point` components, deconstructing each into two `var`-inferred `int`s — `x1=0, y1=0, x2=4, y2=3` — all bound in a single case label, no manual accessor calls anywhere in the arm's body.
4. The arm's body `Math.abs((x2 - x1) * (y2 - y1))` computes `abs((4-0)*(3-0)) = 12.0` and that becomes the switch expression's value, which `area` returns.
5. For the `Circle` instance: the first case's `Rectangle` pattern fails to match (wrong runtime type), so the switch tries the next: `Circle(Point(var cx, var cy), var r)` matches, binding `cx=1, cy=1, r=5`. The arm computes `Math.PI * 5 * 5 ≈ 78.5398`.
6. Back in `main`, `System.out.printf` prints each shape's `toString()` (records get a generated one automatically, e.g. `Rectangle[topLeft=Point[x=0, y=0], bottomRight=Point[x=4, y=3]]`) alongside its computed area.

Expected output:
```
Rectangle[topLeft=Point[x=0, y=0], bottomRight=Point[x=4, y=3]] -> area=12.00
Circle[center=Point[x=1, y=1], radius=5] -> area=78.54
```

## 7. Gotchas & takeaways

> **Gotcha:** a record pattern only matches when the runtime type is **exactly** that record (or a subtype, for non-final hierarchies) — if `shape` were `null`, `instanceof Rectangle(...)` simply evaluates to `false` rather than throwing `NullPointerException`, since `instanceof` has always been null-safe. But in a `switch`, an unhandled `null` still throws `NullPointerException` unless you add `case null` explicitly — see [null handling in switch](0744-null-handling-in-switch-case-null.md).

- Standardized in Java 21 — safe for production, no preview flag.
- Record patterns nest arbitrarily deep: `Outer(Inner(int a, int b), int c)` deconstructs multiple levels in one expression.
- Use `var` inside a record pattern's components when the types are obvious from the record declaration, to cut visual noise.
- Combine with sealed interfaces and `switch` for exhaustive, compiler-checked handling of a whole type hierarchy — see [pattern matching for switch — standardized](0742-pattern-matching-for-switch-standardized.md).
- Refactoring a record's component list (add/remove/reorder) breaks every pattern that assumed the old shape at **compile time**, which is a feature, not a bug — it surfaces every call site that needs updating.
