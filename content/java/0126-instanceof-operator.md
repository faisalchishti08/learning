---
card: java
gi: 126
slug: instanceof-operator
title: instanceof operator
---

## 1. What it is

`instanceof` tests whether an object is an instance of a given class, interface, or array type, producing a `boolean`. It checks the object's *actual runtime type* (and everything that type extends or implements), not the type of the reference variable used to access it — this is what makes it useful for distinguishing between different subtypes stored through a common supertype reference. `null` is never an instance of anything: `x instanceof AnyType` is always `false` if `x` is `null`, and this check never throws `NullPointerException`.

```java
Object obj = "hello";
System.out.println(obj instanceof String);    // true — the actual object is a String
System.out.println(obj instanceof Integer);    // false

Object nullObj = null;
System.out.println(nullObj instanceof String);  // false — never throws, even for null

// Since Java 16: pattern matching lets you test-and-cast in one step
if (obj instanceof String s) {
    System.out.println("Length: " + s.length());   // `s` is already cast to String here
}
```

The modern **pattern-matching form** (`instanceof String s`) both performs the type check and, if it succeeds, declares a new variable (`s`) already cast to that type — eliminating the separate explicit cast that older code required.

## 2. Why & when

`instanceof` is used whenever code needs to branch on an object's concrete type, most commonly:

- Overriding `equals(Object other)`: checking `other instanceof MyClass` before casting and comparing fields is the standard idiom.
- Handling a heterogeneous collection where elements might be of several related types (e.g., different `Shape` subclasses) and different logic is needed per type.
- Defensive programming at API boundaries, where an `Object` parameter's actual type must be validated before being cast and used.

Overuse of `instanceof`-based branching to distinguish subtypes is often considered a design smell — extensive chains of `if (x instanceof A) ... else if (x instanceof B) ...` frequently indicate that the logic would be better expressed through polymorphism (an overridden method on each subtype) instead. `instanceof` is legitimate and idiomatic for `equals()` implementations, defensive checks, and genuinely small, stable sets of type-based cases (Java's `switch` pattern matching, covered elsewhere, formalizes larger versions of this into a cleaner construct).

## 3. Core concept

```java
public class InstanceofDemo {
    public static void main(String[] args) {
        Object[] items = { "hello", 42, 3.14, true, null };

        for (Object item : items) {
            // Classic pre-Java-16 style: check, then cast separately
            if (item instanceof String) {
                String s = (String) item;
                System.out.println("String of length " + s.length());
            } else if (item instanceof Integer) {
                Integer i = (Integer) item;
                System.out.println("Integer: " + (i * 2));
            } else if (item == null) {
                System.out.println("null value");
            } else {
                System.out.println("Other type: " + item.getClass().getSimpleName());
            }
        }

        // Modern pattern-matching form: test and bind in one step
        Object obj = "pattern matching";
        if (obj instanceof String s && s.length() > 5) {
            System.out.println("Long string: " + s);
        }
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 165" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="instanceof checks the runtime type of the actual object, not the compile time type of the reference variable. An Object reference pointing to a String object returns true for instanceof String because the actual object is a String, regardless of the reference's declared type.">
  <rect x="8" y="8" width="684" height="149" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Object obj = "hello";  obj instanceof String  →  checks the ACTUAL object, not the variable's declared type</text>

  <rect x="60" y="44" width="140" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="130" y="66" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">obj (declared: Object)</text>

  <path d="M 130 78 L 130 100" stroke="#79c0ff" stroke-width="1.5"/>

  <rect x="60" y="100" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="130" y="124" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">"hello" (actual: String)</text>

  <text x="450" y="70" fill="#e6edf3" font-size="10" font-family="monospace">obj instanceof String</text>
  <text x="450" y="90" fill="#6db33f" font-size="12" font-family="monospace">→ true</text>
  <text x="450" y="112" fill="#8b949e" font-size="8" font-family="sans-serif">because the OBJECT is a String,</text>
  <text x="450" y="126" fill="#8b949e" font-size="8" font-family="sans-serif">even though obj is declared as Object.</text>
</svg>

`instanceof` follows the reference down to the actual object and checks its real, runtime type — the declared type of the variable is irrelevant.

## 5. Runnable example

Scenario: a simple shape-area calculator processing a mixed list of shapes stored as a common `Shape` supertype — demonstrating classic `instanceof`-and-cast, then the modern pattern-matching form, then a discussion of when to prefer polymorphism instead.

### Level 1 — Basic

```java
import java.util.*;

public class ShapeBasic {

    static class Shape {}
    static class Circle extends Shape { double radius; Circle(double r) { radius = r; } }
    static class Rectangle extends Shape { double width, height; Rectangle(double w, double h) { width = w; height = h; } }

    static double area(Shape shape) {
        if (shape instanceof Circle) {
            Circle c = (Circle) shape;         // classic style: separate cast after the check
            return Math.PI * c.radius * c.radius;
        } else if (shape instanceof Rectangle) {
            Rectangle r = (Rectangle) shape;
            return r.width * r.height;
        }
        return 0.0;
    }

    public static void main(String[] args) {
        List<Shape> shapes = List.of(new Circle(3.0), new Rectangle(4.0, 5.0));
        for (Shape s : shapes) {
            System.out.printf("%s area: %.2f%n", s.getClass().getSimpleName(), area(s));
        }
    }
}
```

**How to run:** `java ShapeBasic.java`

`shape instanceof Circle` checks whether the object actually referenced by `shape` (whose declared type is the more general `Shape`) is, at runtime, a `Circle` instance. If so, `(Circle) shape` performs the explicit cast, and only then can `c.radius` be accessed — this two-step "check, then cast" pattern was the only option before Java 16 introduced pattern matching.

### Level 2 — Intermediate

Same shape calculator, now rewritten with the modern pattern-matching form of `instanceof`, which combines the check and the cast into a single expression, eliminating the separate cast line entirely.

```java
import java.util.*;

public class ShapeIntermediate {

    static class Shape {}
    static class Circle extends Shape { double radius; Circle(double r) { radius = r; } }
    static class Rectangle extends Shape { double width, height; Rectangle(double w, double h) { width = w; height = h; } }

    static double area(Shape shape) {
        if (shape instanceof Circle c) {           // pattern variable `c` is already cast to Circle here
            return Math.PI * c.radius * c.radius;
        } else if (shape instanceof Rectangle r) {   // pattern variable `r` is already cast to Rectangle here
            return r.width * r.height;
        }
        return 0.0;
    }

    public static void main(String[] args) {
        List<Shape> shapes = List.of(new Circle(3.0), new Rectangle(4.0, 5.0));
        for (Shape s : shapes) {
            System.out.printf("%s area: %.2f%n", s.getClass().getSimpleName(), area(s));
        }

        // The pattern variable's scope extends only where it's guaranteed to be that type
        Object mystery = "text";
        if (mystery instanceof String str && str.length() > 3) {
            System.out.println("A sufficiently long string: " + str);
        }
        // `str` is not accessible here, outside the if-block's scope
    }
}
```

**How to run:** `java ShapeIntermediate.java`

`shape instanceof Circle c` performs the identical runtime check as before, but if it succeeds, the compiler automatically introduces `c` as a new local variable of type `Circle`, already cast — there is no separate `(Circle) shape` line needed at all. The pattern variable's scope is carefully defined by the compiler to include only the code paths where it is guaranteed to have matched: inside the `if` block's body (and, for `&&`-chained conditions like `mystery instanceof String str && str.length() > 3`, within the rest of that same `&&` chain), but not in the `else` branch or after the `if` statement, since the match might not have succeeded there.

### Level 3 — Advanced

Same shape system, now demonstrating where `instanceof`-based dispatch becomes unwieldy as more shape types are added, and refactoring to polymorphism (an overridden method on each subclass) — directly illustrating the design tradeoff `instanceof` chains eventually force.

```java
import java.util.*;

public class ShapeAdvanced {

    // Polymorphic approach: each shape knows how to compute its own area
    static abstract class Shape {
        abstract double area();
    }

    static class Circle extends Shape {
        double radius;
        Circle(double radius) { this.radius = radius; }
        @Override double area() { return Math.PI * radius * radius; }
    }

    static class Rectangle extends Shape {
        double width, height;
        Rectangle(double width, double height) { this.width = width; this.height = height; }
        @Override double area() { return width * height; }
    }

    static class Triangle extends Shape {
        double base, height;
        Triangle(double base, double height) { this.base = base; this.height = height; }
        @Override double area() { return 0.5 * base * height; }
    }

    public static void main(String[] args) {
        List<Shape> shapes = List.of(
            new Circle(3.0), new Rectangle(4.0, 5.0), new Triangle(6.0, 2.0));

        // No instanceof needed at all: each shape computes its own area polymorphically
        double totalArea = 0.0;
        for (Shape s : shapes) {
            double a = s.area();   // calls the correct overridden area() automatically
            System.out.printf("%s area: %.2f%n", s.getClass().getSimpleName(), a);
            totalArea += a;
        }
        System.out.printf("Total area: %.2f%n", totalArea);

        // instanceof is STILL appropriate here: a targeted, one-off type check for a specific behavior
        // that doesn't belong on every Shape (e.g., only circles have a meaningful "circumference")
        for (Shape s : shapes) {
            if (s instanceof Circle c) {
                System.out.printf("  (%s has circumference %.2f)%n", c.getClass().getSimpleName(), 2 * Math.PI * c.radius);
            }
        }
    }
}
```

**How to run:** `java ShapeAdvanced.java`

Adding `Triangle` in the polymorphic design requires only a new subclass with its own `area()` override — the `main` loop's `s.area()` call needs no modification at all. In the `instanceof`-chain style from Levels 1–2, adding `Triangle` would have required adding a *third* `else if (shape instanceof Triangle t)` branch to the `area` method, and every other method that similarly dispatches on shape type would need the same new branch added — this duplication and the risk of forgetting a branch somewhere is exactly why `instanceof` chains for routine, per-type behavior are considered a design smell as the number of types grows. The final loop shows `instanceof` still being entirely appropriate: circumference genuinely only makes sense for `Circle` (not `Rectangle` or `Triangle`), so a one-off, targeted `instanceof` check here is simpler and more honest than forcing every `Shape` subclass to implement a `circumference()` method that would be meaningless for most of them.

## 6. Walkthrough

Trace the polymorphic loop `for (Shape s : shapes) { double a = s.area(); ... }` for the second element, `new Rectangle(4.0, 5.0)`:

**Static type versus dynamic dispatch.** `s`'s declared (static) type is `Shape`, but the actual object it refers to is a `Rectangle`. When `s.area()` is called, the JVM does not simply call some generic `Shape.area()` — since `area()` is `abstract` on `Shape` and overridden differently by each subclass, Java performs **dynamic dispatch**: it looks up the *actual* runtime class of the object (`Rectangle`) and invokes *that* class's `area()` override.

**Executing `Rectangle.area()`.** This override computes `width * height` using the object's own fields: `4.0 * 5.0 = 20.0`.

**No `instanceof` was needed anywhere in this path.** Compare this to the `instanceof`-chain version from Level 1/2, which would have explicitly asked "is this a `Circle`? Is this a `Rectangle`?" for every single shape, every time `area` needed to be computed — the polymorphic version instead lets each object answer that question implicitly, simply by virtue of which class's overridden method actually gets invoked.

```
Polymorphic dispatch (no instanceof):
  s.area()  ->  JVM looks up actual runtime class of s: Rectangle
             ->  invokes Rectangle's area() override directly
             ->  20.0 * 1 = 20.0  (width * height)

instanceof-chain equivalent (Level 1/2 style):
  if (s instanceof Circle c) ... area = pi*r*r
  else if (s instanceof Rectangle r) ... area = w*h   <- this branch matches, but had to be CHECKED explicitly
  else if (s instanceof Triangle t) ... area = 0.5*b*h  <- a NEW branch needed for every new shape type
```

**Final output.** The polymorphic loop prints each shape's area (computed via its own overridden method) and accumulates a running total, followed by a separate, explicit `instanceof Circle` check used only for the circumference calculation — a case where a targeted type check is the right tool precisely because the behavior genuinely doesn't apply to every shape in the hierarchy.

## 7. Gotchas & takeaways

> **`x instanceof SomeType` is always `false` if `x` is `null` — it never throws `NullPointerException`.** This makes `instanceof` a safe way to test a possibly-null reference's type without a separate null check, though the pattern-matched variable is still only usable inside the branch where the match succeeded.

> **Long chains of `instanceof` checks that branch on an object's concrete type to decide routine, per-type behavior are usually a sign that polymorphism (an overridden method on each subtype) would be a better design.** `instanceof` remains entirely appropriate for `equals()` implementations, defensive type validation, and genuinely one-off checks for behavior that doesn't belong on every subtype.

- `instanceof` checks an object's actual runtime type, not the declared/static type of the reference variable used to access it.
- The modern pattern-matching form (`x instanceof Type t`) combines the check and the cast into one expression, with the new variable scoped only to the branches where the match is guaranteed to have succeeded.
- Prefer polymorphism over `instanceof`-based type dispatch when the same set of types will repeatedly need type-specific behavior across many methods, since adding a new type then requires touching only the new subclass, not every dispatch site.
- `instanceof` is still the right, idiomatic tool for `equals()` overrides, defensive API boundary checks, and small, stable, one-off type-specific branches.
