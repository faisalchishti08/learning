---
card: java
gi: 701
slug: sealed-classes-interfaces-standardized
title: Sealed classes & interfaces — standardized
---

## 1. What it is

**Sealed classes and interfaces** became a **permanent, standard language feature** in **Java 17** (JEP 409), after two preview rounds in [Java 15](0678-sealed-classes-preview.md) and [Java 16](0689-sealed-classes-2nd-preview.md). A sealed type declares, up front, the *complete, closed list* of classes or interfaces allowed to extend or implement it: `sealed interface Shape permits Circle, Square {}`. From Java 17 onward, this is ordinary syntax — no `--enable-preview` flag, no risk of the feature changing shape again. The semantics carried over unchanged from the second preview: every class named in a `permits` clause must itself be declared `final`, `sealed`, or `non-sealed`, so the compiler can always answer, exhaustively, "what are all the possible subtypes of this type?"

## 2. Why & when

Two preview rounds gave the OpenJDK team time to validate sealed types against real code, especially their interaction with records (a record is implicitly `final`, so a sealed interface whose permitted subtypes are all records "just works" with no extra modifiers) and to settle the reflection surface (`Class.isSealed()`, `Class.getPermittedSubclasses()`). None of that changed between the second preview and standardization — Java 17 simply removed the preview-feature flag requirement and gave the feature the API-stability guarantee that comes with being part of the standard Java SE specification. Reach for sealed types whenever you're modeling a fixed, closed set of alternatives: a shape hierarchy, a result type (success/failure/pending), an AST node hierarchy, or a state machine's states — anywhere you want the compiler to guarantee that a switch or `instanceof` chain over the type's subtypes is provably exhaustive, and to reject any external code's attempt to add an unanticipated new subtype.

## 3. Core concept

```java
// Java 17 — sealed types are now standard syntax, no --enable-preview needed
sealed interface Shape permits Circle, Square, Triangle {}

final class Circle implements Shape {
    final double radius;
    Circle(double radius) { this.radius = radius; }
}
final class Square implements Shape {
    final double side;
    Square(double side) { this.side = side; }
}
final class Triangle implements Shape {
    final double base, height;
    Triangle(double base, double height) { this.base = base; this.height = height; }
}
```

`Shape`'s `permits` clause is the complete, compiler-checked list of every class allowed to implement it — no other class, anywhere, can add itself to this hierarchy.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A sealed Shape interface permits exactly Circle, Square, and Triangle; no other class may implement Shape">
  <rect x="230" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">sealed Shape</text>
  <text x="320" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">permits Circle, Square, Triangle</text>

  <line x1="280" y1="70" x2="120" y2="130" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="320" y1="70" x2="320" y2="130" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="360" y1="70" x2="520" y2="130" stroke="#79c0ff" stroke-width="1.5"/>

  <rect x="50" y="130" width="140" height="45" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="120" y="157" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">final Circle</text>

  <rect x="250" y="130" width="140" height="45" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="320" y="157" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">final Square</text>

  <rect x="450" y="130" width="140" height="45" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="520" y="157" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">final Triangle</text>

  <text x="320" y="205" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">any 4th "class Pentagon implements Shape" elsewhere fails to compile</text>
</svg>

The `permits` list is exhaustive and compiler-enforced — the hierarchy cannot silently grow from outside code.

## 5. Runnable example

Scenario: an area calculator over a closed `Shape` hierarchy — first the standardized sealed hierarchy with an exhaustive `instanceof` dispatch, then extending the hierarchy with a new permitted subtype to show the compiler-enforced ripple effect, then using reflection to introspect the finalized hierarchy at runtime, exactly as a serialization or validation framework might.

### Level 1 — Basic

```java
// File: ShapeAreaBasic.java
public class ShapeAreaBasic {
    sealed interface Shape permits Circle, Square {}
    record Circle(double radius) implements Shape {}
    record Square(double side) implements Shape {}

    static double area(Shape shape) {
        if (shape instanceof Circle c) return Math.PI * c.radius() * c.radius();
        if (shape instanceof Square s) return s.side() * s.side();
        throw new IllegalStateException("unreachable: sealed to Circle, Square");
    }

    public static void main(String[] args) {
        Shape[] shapes = { new Circle(2.0), new Square(3.0) };
        for (Shape shape : shapes) {
            System.out.printf("%s area = %.2f%n", shape, area(shape));
        }
    }
}
```

**How to run:**
```
java ShapeAreaBasic.java
```

Expected output:
```
ShapeAreaBasic$Circle[radius=2.0] area = 12.57
ShapeAreaBasic$Square[side=3.0] area = 9.00
```

### Level 2 — Intermediate

```java
// File: ShapeAreaWithTriangle.java
public class ShapeAreaWithTriangle {
    sealed interface Shape permits Circle, Square, Triangle {}
    record Circle(double radius) implements Shape {}
    record Square(double side) implements Shape {}
    record Triangle(double base, double height) implements Shape {}

    static double area(Shape shape) {
        if (shape instanceof Circle c) return Math.PI * c.radius() * c.radius();
        if (shape instanceof Square s) return s.side() * s.side();
        if (shape instanceof Triangle t) return 0.5 * t.base() * t.height();
        throw new IllegalStateException("unreachable: sealed to Circle, Square, Triangle");
    }

    public static void main(String[] args) {
        Shape[] shapes = { new Circle(2.0), new Square(3.0), new Triangle(4.0, 5.0) };
        for (Shape shape : shapes) {
            System.out.printf("%s area = %.2f%n", shape, area(shape));
        }
    }
}
```

**How to run:**
```
java ShapeAreaWithTriangle.java
```

Expected output:
```
ShapeAreaWithTriangle$Circle[radius=2.0] area = 12.57
ShapeAreaWithTriangle$Square[side=3.0] area = 9.00
ShapeAreaWithTriangle$Triangle[base=4.0, height=5.0] area = 10.00
```

Adding `Triangle` to `Shape`'s `permits` list requires updating `area`'s `instanceof` chain in lockstep — miss it, and the fallback `throw` fires for every `Triangle` at runtime, which is exactly the kind of gap sealing is designed to surface loudly during development rather than let slip silently into production.

### Level 3 — Advanced

```java
// File: ShapeIntrospection.java
public class ShapeIntrospection {
    sealed interface Shape permits Circle, Square, Triangle {}
    record Circle(double radius) implements Shape {}
    record Square(double side) implements Shape {}
    record Triangle(double base, double height) implements Shape {}

    public static void main(String[] args) {
        Class<Shape> shapeClass = Shape.class;

        System.out.println("Shape.class.isSealed(): " + shapeClass.isSealed());
        System.out.println("Permitted subclasses:");
        for (Class<?> permitted : shapeClass.getPermittedSubclasses()) {
            boolean isFinal = java.lang.reflect.Modifier.isFinal(permitted.getModifiers());
            System.out.println("  " + permitted.getSimpleName() + " (final=" + isFinal + ")");
        }
    }
}
```

**How to run:**
```
java ShapeIntrospection.java
```

Expected output:
```
Shape.class.isSealed(): true
Permitted subclasses:
  Circle (final=true)
  Square (final=true)
  Triangle (final=true)
```

## 6. Walkthrough

1. `main` obtains `Shape.class` and calls `.isSealed()`, which returns `true` because `Shape` carries the `sealed` modifier and a `permits` clause — this reflective check is stable, standard API from Java 17 onward, no longer tied to a preview feature that could still change.
2. `.getPermittedSubclasses()` returns exactly the `Class` objects named in `Shape`'s `permits` clause — `Circle`, `Square`, `Triangle` — in the order declared, with no need to scan the classpath.
3. The loop checks `Modifier.isFinal(...)` on each: since all three are `record`s, all report `final=true` automatically, satisfying sealed's requirement without any explicit modifier on the records themselves.
4. In `ShapeAreaWithTriangle` (Level 2), `area`'s `instanceof` chain checks `Circle`, then `Square`, then `Triangle` in turn, computing each shape's area formula and falling through to a defensive `throw` only if some future subtype were added to `permits` without a matching `instanceof` branch — a case sealing makes loudly visible rather than silently wrong.
5. `main` builds an array mixing all three shapes and loops over it, printing each shape's default record `toString()` (`Circle[radius=2.0]`, etc.) alongside its computed area, formatted to two decimal places via `%.2f`.

```
Shape (sealed) ──permits──► Circle | Square | Triangle
                              (all implicitly final, since all are records)
Class.isSealed() -> true
Class.getPermittedSubclasses() -> [Circle, Square, Triangle]
```

## 7. Gotchas & takeaways

> Standardization in Java 17 changed **nothing about the semantics** validated across the two preview rounds — the only practical change is that `--enable-preview` is no longer required, and the feature (including its reflection APIs) is now covered by Java SE's normal backward-compatibility guarantees. Code written against the [second preview](0689-sealed-classes-2nd-preview.md) needs only the preview flags removed to run unchanged on Java 17.
- A sealed type's `permits` clause can be **omitted entirely** if every permitted subtype is declared in the same source file as the sealed type itself — the compiler infers the list from the file's contents.
- Permitted subtypes must generally reside in the same module (or same package, for the unnamed module) as the sealed type — sealing is a compile-time and module-boundary guarantee, not just a naming convention.
- Combining sealed interfaces with records (as in this example) is Java's closest built-in equivalent to algebraic data types: a closed, exhaustively-checkable set of immutable data variants.
- See [sealed / permits / non-sealed keywords](0702-sealed-permits-non-sealed-keywords.md) for a deep dive into the three modifiers themselves, including how `non-sealed` deliberately reopens one branch of an otherwise closed hierarchy.
- This standardization landed in Java 17 alongside a **preview** of pattern matching for `switch` (JEP 406) — sealed types are what eventually lets the compiler verify a `switch` over a sealed hierarchy is exhaustive without a `default` branch, though that exhaustiveness-checking behavior itself matured over several more releases.
