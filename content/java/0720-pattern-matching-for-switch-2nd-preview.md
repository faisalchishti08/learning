---
card: java
gi: 720
slug: pattern-matching-for-switch-2nd-preview
title: Pattern matching for switch (2nd preview)
---

## 1. What it is

**Java 18** (JEP 420) is the **second preview** of pattern matching for `switch`, refining the feature first previewed in [Java 17](0704-pattern-matching-for-switch-preview.md). It keeps type-pattern `case` labels and `null` handling inside `switch`, but reworks two things based on feedback from the first preview: **guarded patterns** change syntax from `case Pattern p && guardExpr` to `case Pattern p when guardExpr`, and the feature drops parenthesized patterns, simplifying the grammar. Being a *second preview*, it remains an experimental, opt-in feature — code using it must be compiled and run with `--enable-preview`, and it was still not final in Java 18.

## 2. Why & when

The first preview (Java 17) used `&&` to attach a boolean condition to a type pattern, e.g. `case Integer i && i > 0 -> ...`. Early feedback found this confusing: `&&` visually reads as "and this other pattern," when what's actually meant is "and this extra condition on the same binding." The Java language team switched to the keyword `when`, borrowed from a similar role in other languages' pattern-matching constructs, making the intent unambiguous: `case Integer i when i > 0 -> ...` reads naturally as "case Integer, when positive." This is exactly the kind of refinement previews exist for — ship an experimental feature, gather real usage feedback, and adjust the syntax before it becomes a permanent, unchangeable part of the language. Reach for pattern matching in `switch` any time you're writing a chain of `instanceof` checks and casts against a value's type — a `sealed` type hierarchy processed by kind, a heterogeneous `Object` payload, or any case where the *shape* of the data should drive the branch, not just a single equality check.

## 3. Core concept

```java
// Java 17 (1st preview): guard uses &&
static String describe(Object obj) {
    return switch (obj) {
        case Integer i && i > 0 -> "positive integer";
        case Integer i          -> "non-positive integer";
        case String s            -> "string of length " + s.length();
        case null                -> "null";
        default                  -> "something else";
    };
}

// Java 18 (2nd preview): guard uses `when` instead of &&
static String describe(Object obj) {
    return switch (obj) {
        case Integer i when i > 0 -> "positive integer";
        case Integer i             -> "non-positive integer";
        case String s               -> "string of length " + s.length();
        case null                   -> "null";
        default                     -> "something else";
    };
}
```

The `when` clause reads as an extra condition attached to a matched pattern, evaluated only if the type pattern itself already matched.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A switch pattern match first checks the type pattern, then evaluates the when guard only if the type matched, falling through to the next case otherwise">
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="50" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">switch (obj)</text>

  <line x1="110" y1="70" x2="110" y2="100" stroke="#8b949e" stroke-width="2" marker-end="url(#a3)"/>
  <rect x="20" y="100" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="122" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">case Integer i</text>
  <text x="110" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">type pattern matches?</text>

  <line x1="200" y1="125" x2="320" y2="125" stroke="#3fb950" stroke-width="2" marker-end="url(#a3)"/>
  <text x="260" y="115" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">yes</text>
  <rect x="325" y="100" width="180" height="50" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="415" y="122" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">when i &gt; 0</text>
  <text x="415" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">guard true?</text>

  <line x1="110" y1="150" x2="110" y2="190" stroke="#f0883e" stroke-width="2" marker-end="url(#a3)"/>
  <text x="130" y="175" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">no -&gt; next case</text>

  <line x1="415" y1="150" x2="415" y2="190" stroke="#f0883e" stroke-width="2" marker-end="url(#a3)"/>
  <text x="440" y="175" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">no -&gt; next case</text>

  <defs><marker id="a3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A `when` guard only runs after its pattern already matched; failing the guard falls through to the next `case`, not to `default` directly.

## 5. Runnable example

Scenario: classifying shapes represented as a sealed hierarchy, starting with plain type patterns, adding `when` guards to distinguish special cases of the same type, then combining guards with record patterns and `null` handling for a realistic geometry-processing switch.

### Level 1 — Basic

```java
// File: ShapeBasic.java
// Run with --enable-preview: pattern matching for switch is a 2nd preview feature in Java 18.
sealed interface Shape permits Circle, Square {}
record Circle(double radius) implements Shape {}
record Square(double side) implements Shape {}

public class ShapeBasic {
    static String describe(Shape shape) {
        return switch (shape) {
            case Circle c -> "circle with radius " + c.radius();
            case Square s -> "square with side " + s.side();
        };
    }

    public static void main(String[] args) {
        System.out.println(describe(new Circle(2.0)));
        System.out.println(describe(new Square(3.0)));
    }
}
```

**How to run:**
```
javac --release 18 --enable-preview ShapeBasic.java
java --enable-preview ShapeBasic
```

Expected output:
```
circle with radius 2.0
square with side 3.0
```

### Level 2 — Intermediate

```java
// File: ShapeIntermediate.java
// Adds `when` guards to distinguish special cases within the same type pattern.
sealed interface Shape permits Circle, Square {}
record Circle(double radius) implements Shape {}
record Square(double side) implements Shape {}

public class ShapeIntermediate {
    static String describe(Shape shape) {
        return switch (shape) {
            case Circle c when c.radius() == 0 -> "degenerate circle (a point)";
            case Circle c when c.radius() > 100 -> "huge circle, radius " + c.radius();
            case Circle c -> "circle with radius " + c.radius();
            case Square s when s.side() == 0 -> "degenerate square (a point)";
            case Square s -> "square with side " + s.side();
        };
    }

    public static void main(String[] args) {
        System.out.println(describe(new Circle(0)));
        System.out.println(describe(new Circle(500)));
        System.out.println(describe(new Circle(2.0)));
        System.out.println(describe(new Square(0)));
    }
}
```

**How to run:**
```
javac --release 18 --enable-preview ShapeIntermediate.java
java --enable-preview ShapeIntermediate
```

Expected output:
```
degenerate circle (a point)
huge circle, radius 500.0
circle with radius 2.0
degenerate square (a point)
```

This adds the real-world concern: multiple `when`-guarded cases against the *same* type, evaluated top to bottom, with the first matching guard winning — exactly like an `if`/`else if` chain, but scoped inside the exhaustive `switch`.

### Level 3 — Advanced

```java
// File: ShapeAdvanced.java
// Combines `when` guards with explicit null handling and a default, for a
// production-flavored switch over shapes that might legitimately be null
// (e.g. "no shape selected yet" from a UI) and must remain exhaustive.
sealed interface Shape permits Circle, Square, Triangle {}
record Circle(double radius) implements Shape {}
record Square(double side) implements Shape {}
record Triangle(double base, double height) implements Shape {}

public class ShapeAdvanced {
    static String classify(Shape shape) {
        return switch (shape) {
            case null -> "no shape selected";
            case Circle c when c.radius() <= 0 -> "invalid circle";
            case Square s when s.side() <= 0 -> "invalid square";
            case Triangle t when t.base() <= 0 || t.height() <= 0 -> "invalid triangle";
            case Circle c -> String.format("valid circle, area=%.2f", Math.PI * c.radius() * c.radius());
            case Square s -> String.format("valid square, area=%.2f", s.side() * s.side());
            case Triangle t -> String.format("valid triangle, area=%.2f", 0.5 * t.base() * t.height());
        };
    }

    public static void main(String[] args) {
        Shape[] shapes = { null, new Circle(-1), new Circle(2), new Square(4), new Triangle(3, 4) };
        for (Shape s : shapes) {
            System.out.println(classify(s));
        }
    }
}
```

**How to run:**
```
javac --release 18 --enable-preview ShapeAdvanced.java
java --enable-preview ShapeAdvanced
```

Expected output:
```
no shape selected
invalid circle
valid circle, area=12.57
valid square, area=16.00
valid triangle, area=6.00
```

## 6. Walkthrough

1. `ShapeAdvanced.main` builds an array mixing `null` with valid and invalid shapes, then calls `classify` on each — this mirrors a realistic entry point, such as data arriving from a UI form or a deserialized payload where any of these states could occur.
2. `switch (shape)` first checks `case null`. Ordinary `switch` on a reference type throws `NullPointerException` if the selector is `null` and no `case null` exists; pattern-matching `switch` lets `null` be handled as an explicit, ordinary case instead, which is why it's listed first here.
3. For a non-null `shape`, the JVM checks each `case` top to bottom. `case Circle c when c.radius() <= 0` first tests whether `shape` is a `Circle` (a type pattern match, binding `c`); only if that succeeds does it then evaluate the `when` guard `c.radius() <= 0`. If the guard is false, control falls through to try the *next* case — it does not stop at `default` or throw.
4. For `new Circle(-1)`, the type pattern `Circle c` matches and the guard `c.radius() <= 0` is `true`, so `"invalid circle"` is selected immediately — the later, unguarded `case Circle c ->` is never reached for this value.
5. For `new Circle(2)`, the type pattern matches but the guard `c.radius() <= 0` is `false`, so this case is skipped; execution falls through to the next `Circle`-related case — the unguarded `case Circle c ->` — which always matches once the guarded case above it has been ruled out. This is the exhaustiveness guarantee: because `Shape` is `sealed` with exactly three permitted subtypes, and every subtype has both a guarded and unguarded case, the compiler can verify no `Shape` value falls through unhandled, without needing a `default` branch.
6. The area calculation for the matched case runs using the bound pattern variable (`c`, `s`, or `t`), exactly as if an `instanceof` cast had been performed manually — except the compiler already proved the type, so no explicit cast is needed inside the arm.

```
classify(new Circle(-1))
   |
   v
case null?                    -> no (shape is a Circle)
   |
   v
case Circle c when radius<=0? -> type matches, guard true  -> "invalid circle"  [STOP]

classify(new Circle(2))
   |
   v
case null?                    -> no
   |
   v
case Circle c when radius<=0? -> type matches, guard FALSE -> fall through
   |
   v
case Circle c (unguarded)     -> matches                    -> "valid circle, area=..."  [STOP]
```

## 7. Gotchas & takeaways

> This is a **preview feature in Java 18** — both `javac` and `java` require `--enable-preview` (and `javac` additionally needs `--release 18` or a matching `--source`/`--target`), and preview APIs can still change or be dropped before finalization. Code written against the Java 18 second preview should not be treated as permanently stable syntax.
- The syntax change from Java 17's `case Pattern p && guard` to Java 18's `case Pattern p when guard` was made specifically in response to preview feedback that `&&` was misleading — this is the preview process working as intended: ship, gather feedback, refine before finalizing.
- `when` guards are evaluated **only after** their associated pattern already matched, and only **once per case**, top to bottom — order matters, exactly like `if`/`else if`, so put more specific guarded cases before the general unguarded case for the same type.
- `case null` can be combined with a type pattern using `case null, Circle c -> ...` to handle `null` and a specific type identically in one arm — useful when `null` should be treated the same as some particular case rather than getting its own branch.
- Pairing pattern-matching `switch` with a `sealed` hierarchy (as in this example, `sealed interface Shape permits Circle, Square, Triangle`) is what lets the compiler enforce exhaustiveness without a `default` arm — remove `sealed` and add a fourth implementing class, and the compiler can no longer prove every case is covered, forcing a `default` (or a compile error) to appear.
