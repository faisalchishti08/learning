---
card: java
gi: 678
slug: sealed-classes-preview
title: Sealed classes (preview)
---

## 1. What it is

**Sealed classes and interfaces**, introduced as a **preview** feature in **Java 15** (JEP 360), let a class or interface declare exactly which other classes are allowed to extend or implement it, using a new `permits` clause. A `sealed` type lists its permitted direct subtypes explicitly (`sealed class Shape permits Circle, Square, Triangle`), and every one of those subtypes must in turn declare itself as `final`, `sealed` (with its own further-restricted `permits` list), or `non-sealed` (reopening extension to anyone, but explicitly opting back in). This sits between `final` (no subclassing at all) and an ordinary open class (anyone can extend it) — sealing gives you a *closed, known set* of subtypes while still allowing genuine polymorphism among them.

## 2. Why & when

Java previously offered only two extremes for controlling inheritance: seal a class completely with `final`, or leave it wide open. Neither fits a very common domain-modeling need: "this type has exactly these variants, and I want the compiler to know that." Modeling a `Shape` as `Circle`, `Square`, or `Triangle` — and nothing else — means a `switch` over those types can, in principle, be checked for exhaustiveness by the compiler (a capability sealed types set up, later completed alongside pattern matching for switch). Before sealed types, library authors wanting a fixed, closed type hierarchy had to rely on documentation and package-private constructors as informal conventions, not something the language enforced. Reach for sealed types when you're modeling an **algebraic-style closed set of alternatives** — a JSON value that's one of `JsonString`, `JsonNumber`, `JsonArray`, etc., an AST node that's one of a fixed set of expression kinds, or a result type that's one of `Success` or `Failure` — where you want the compiler, not just documentation, to guarantee no one adds a surprise fourth case elsewhere in the codebase.

## 3. Core concept

```java
// Java 15 preview — requires --enable-preview --release 15 to compile and run
sealed interface Shape permits Circle, Square, Triangle {}

final class Circle implements Shape {
    double radius;
    Circle(double radius) { this.radius = radius; }
}

final class Square implements Shape {
    double side;
    Square(double side) { this.side = side; }
}

final class Triangle implements Shape {
    double base, height;
    Triangle(double base, double height) { this.base = base; this.height = height; }
}
```

Every permitted subtype must be `final`, `sealed`, or `non-sealed` — there is no fourth option, which is exactly what makes the set of implementers closed and knowable just from reading the `sealed` declaration.

## 4. Diagram

<svg viewBox="0 0 620 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sealed interface Shape permits exactly Circle, Square, and Triangle; no other class may implement it">
  <rect x="230" y="20" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">sealed Shape</text>
  <text x="310" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">permits Circle, Square, Triangle</text>

  <line x1="270" y1="70" x2="120" y2="130" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="310" y1="70" x2="310" y2="130" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="350" y1="70" x2="500" y2="130" stroke="#79c0ff" stroke-width="1.5"/>

  <rect x="60" y="130" width="120" height="46" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="120" y="158" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">final Circle</text>

  <rect x="250" y="130" width="120" height="46" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="310" y="158" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">final Square</text>

  <rect x="440" y="130" width="120" height="46" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="500" y="158" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">final Triangle</text>

  <text x="310" y="205" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">no other class may implement Shape — compiler-enforced</text>
</svg>

The `permits` list is the complete, compiler-checked membership of the hierarchy — nothing outside it can join.

## 5. Runnable example

Scenario: a small shape-area calculator — first with a plain sealed hierarchy and an `instanceof` chain, then adding a new permitted subtype to show the compiler forces every consumer to be updated, then using an exhaustive `switch` over the sealed type (pattern-matching switch was itself still in preview in Java 15, so this level narrates the exhaustiveness benefit even where full switch-pattern syntax matured in later releases).

### Level 1 — Basic

```java
// File: ShapeArea.java
// compile & run with: --enable-preview --release 15
public class ShapeArea {
    sealed interface Shape permits Circle, Square {}
    record Circle(double radius) implements Shape {}
    record Square(double side) implements Shape {}

    static double area(Shape s) {
        if (s instanceof Circle c) return Math.PI * c.radius() * c.radius();
        if (s instanceof Square sq) return sq.side() * sq.side();
        throw new IllegalStateException("unreachable: Shape is sealed to Circle, Square");
    }

    public static void main(String[] args) {
        System.out.printf("Circle area: %.2f%n", area(new Circle(2.0)));
        System.out.printf("Square area: %.2f%n", area(new Square(3.0)));
    }
}
```

**How to run:**
```
javac --enable-preview --release 15 ShapeArea.java
java --enable-preview ShapeArea
```

Expected output:
```
Circle area: 12.57
Square area: 9.00
```

### Level 2 — Intermediate

```java
// File: ShapeAreaWithTriangle.java
// compile & run with: --enable-preview --release 15
public class ShapeAreaWithTriangle {
    sealed interface Shape permits Circle, Square, Triangle {}
    record Circle(double radius) implements Shape {}
    record Square(double side) implements Shape {}
    record Triangle(double base, double height) implements Shape {}

    static double area(Shape s) {
        if (s instanceof Circle c) return Math.PI * c.radius() * c.radius();
        if (s instanceof Square sq) return sq.side() * sq.side();
        if (s instanceof Triangle t) return 0.5 * t.base() * t.height();
        throw new IllegalStateException("unreachable: Shape is sealed to Circle, Square, Triangle");
    }

    public static void main(String[] args) {
        System.out.printf("Circle area: %.2f%n", area(new Circle(2.0)));
        System.out.printf("Square area: %.2f%n", area(new Square(3.0)));
        System.out.printf("Triangle area: %.2f%n", area(new Triangle(4.0, 5.0)));
    }
}
```

**How to run:**
```
javac --enable-preview --release 15 ShapeAreaWithTriangle.java
java --enable-preview ShapeAreaWithTriangle
```

Expected output:
```
Circle area: 12.57
Square area: 9.00
Triangle area: 10.00
```

Adding `Triangle` to the `permits` list is the real-world case sealing is built for: because `Shape` names its permitted subtypes explicitly, adding one is a deliberate, visible edit to the interface declaration — and every place with an exhaustive check over the hierarchy (like `area`'s `if` chain) needs a matching update, which sealing surfaces at compile/review time rather than as a silent runtime gap.

### Level 3 — Advanced

```java
// File: ShapeAreaExhaustive.java
// compile & run with: --enable-preview --release 15
public class ShapeAreaExhaustive {
    sealed interface Shape permits Circle, Square, Triangle {}
    record Circle(double radius) implements Shape {}
    record Square(double side) implements Shape {}
    record Triangle(double base, double height) implements Shape {}

    static double area(Shape s) {
        double result;
        if (s instanceof Circle c) {
            result = Math.PI * c.radius() * c.radius();
        } else if (s instanceof Square sq) {
            result = sq.side() * sq.side();
        } else if (s instanceof Triangle t) {
            result = 0.5 * t.base() * t.height();
        } else {
            // Sealed hierarchy guarantees this is unreachable as long as
            // every permitted subtype is handled above.
            throw new AssertionError("Unhandled Shape subtype: " + s.getClass());
        }
        return result;
    }

    static String describe(Shape s) {
        String kind = switch (s) {
            case Circle c -> "circle r=" + c.radius();
            case Square sq -> "square side=" + sq.side();
            case Triangle t -> "triangle base=" + t.base() + " height=" + t.height();
        };
        return kind + " -> area=" + String.format("%.2f", area(s));
    }

    public static void main(String[] args) {
        Shape[] shapes = { new Circle(2.0), new Square(3.0), new Triangle(4.0, 5.0) };
        for (Shape s : shapes) {
            System.out.println(describe(s));
        }
    }
}
```

**How to run:**
```
javac --enable-preview --release 15 ShapeAreaExhaustive.java
java --enable-preview ShapeAreaExhaustive
```

Expected output:
```
circle r=2.0 -> area=12.57
square side=3.0 -> area=9.00
triangle base=4.0 height=5.0 -> area=10.00
```

Level 3's `describe` uses a `switch` expression whose `case` arms cover `Circle`, `Square`, and `Triangle` with **no `default` branch** — this compiles precisely *because* `Shape` is sealed and the compiler can see the complete, closed set of permitted subtypes, proving every possible case is handled. (Pattern-matching `switch` itself matured across later JDK versions; the point sealed types establish here is that the *hierarchy* is closed enough to make such exhaustiveness checking possible at all.)

## 6. Walkthrough

1. `Shape` is declared `sealed ... permits Circle, Square, Triangle` — this single line is the complete, authoritative list of every class allowed to implement `Shape` anywhere in the program; the compiler rejects any other class attempting `implements Shape`.
2. Each of `Circle`, `Square`, and `Triangle` is a `record` — records are implicitly `final`, which satisfies the rule that every permitted subtype must itself be `final`, `sealed`, or `non-sealed`.
3. `main` builds an array of three `Shape` values, one of each permitted kind, and iterates it calling `describe(s)` for each.
4. Inside `describe`, the `switch (s)` expression pattern-matches on `s`'s runtime type: for a `Circle` it binds a local `c` and returns a description string; likewise for `Square` and `Triangle`. Because these three arms exhaust `Shape`'s complete, sealed set of subtypes, no `default` arm is required — the compiler has enough information (from the `permits` list) to prove the `switch` handles every possibility.
5. `describe` also calls `area(s)`, which uses an `if`/`else if` chain of `instanceof` pattern checks (the exhaustive-switch-over-sealed-types syntax used in `describe` and the classic `instanceof`-chain style in `area` are shown side by side to illustrate both approaches work, though the `switch` form is where sealing's exhaustiveness guarantee becomes most visible).
6. `area`'s final `else` branch is a safety net (`AssertionError`) that would only trigger if some future edit added a new permitted subtype to `Shape` without updating `area` — precisely the class of bug sealing is meant to catch early, ideally at compile time via a `switch`'s exhaustiveness check rather than at runtime via this fallback.
7. `System.out.println(describe(s))` prints each shape's description and computed area in turn, one line per shape, in the same order the `shapes` array was constructed.

```
Shape (sealed) ──permits──► Circle | Square | Triangle
                                 │
                    switch(s) case Circle -> ...
                                case Square -> ...
                                case Triangle -> ...
                    (no default needed — compiler proves exhaustiveness
                     from the sealed hierarchy's permits list)
```

## 7. Gotchas & takeaways

> Sealed classes were a **preview feature in Java 15** (and again in Java 16's second preview) — code using `sealed`/`permits`/`non-sealed` needed `--enable-preview` on both `javac` and `java`, and was not guaranteed source- or binary-compatible with the final, standardized version that arrived later. Don't ship preview-dependent code to production without re-checking against the release that finalized the feature.

- Every permitted subtype must declare itself as exactly one of `final`, `sealed`, or `non-sealed` — there's no implicit fourth state, which is what keeps the hierarchy's membership fully explicit.
- `non-sealed` deliberately reopens a branch of an otherwise closed hierarchy to arbitrary further subclassing — useful when one variant genuinely needs to be extensible while the rest of the family stays closed.
- Sealed types and `record`s pair naturally: records give you concise, final data carriers, and sealing gives you a closed, exhaustively-checkable family of them — together this is Java's approach to what other languages call algebraic data types.
- Permitted subtypes normally must be in the same module (or same package, for unnamed modules) as the sealed type, unless declared in the same source file — sealing is a compile-time, source-visible guarantee, not something enforced only by convention across arbitrary modules.
- If a sealed type and all its permitted subtypes are declared in one source file, the `permits` clause can be omitted — the compiler infers permitted subtypes from what's physically present in that file.
