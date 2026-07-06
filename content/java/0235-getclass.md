---
card: java
gi: 235
slug: getclass
title: getClass()
---

## 1. What it is

`getClass()` is a `final` method inherited from `Object` (it cannot be overridden — every object gets exactly `Object`'s implementation) that returns a `Class` object describing the object's *actual runtime type*. It answers "what class was this object really constructed as?" regardless of what type the reference variable pointing to it is declared as.

```java
class Animal { }
class Dog extends Animal { }

public class GetClassDemo {
    public static void main(String[] args) {
        Animal a = new Dog(); // declared type Animal, actual type Dog
        System.out.println(a.getClass());           // class Dog
        System.out.println(a.getClass().getSimpleName()); // Dog
        System.out.println(a instanceof Animal);     // true
    }
}
```

Even though `a` is declared as `Animal`, `a.getClass()` reports `Dog` — `getClass()` always reflects the actual object created at runtime with `new`, never the compile-time declared type of the variable referring to it.

## 2. Why & when

`getClass()` is used whenever code needs to know or compare an object's exact runtime type, which comes up in a handful of common, important situations.

- **Precise `equals()` comparisons** — as the previous topic covered, `getClass() != obj.getClass()` is the standard way to require an exact type match inside `equals`, which avoids the symmetry problems that `instanceof` can introduce across a class hierarchy.
- **Reflection and diagnostics** — `getClass()` is the entry point into Java's reflection API (`getClass().getMethods()`, `getClass().getFields()`, and so on), useful for frameworks, debugging tools, and generic logging that needs to describe "what kind of object is this" without knowing the type in advance.
- **Runtime type dispatch outside of polymorphism** — occasionally code needs to branch on exact type (for example, choosing a serialization strategy), and comparing `getClass()` values (or using `switch` on a sealed hierarchy, a modern alternative) achieves that.

Prefer `instanceof` and polymorphism (overriding a method) for everyday "does this object behave like an X" checks, since they respect subclassing naturally; reach for `getClass()` specifically when you need the *exact* type, not "is-a" compatibility — the `equals()` contract is the most common legitimate case.

## 3. Core concept

```java
class Shape { }
class Circle extends Shape { }
class Square extends Shape { }

public class GetClassCore {
    public static void main(String[] args) {
        Shape s1 = new Circle();
        Shape s2 = new Circle();
        Shape s3 = new Square();

        System.out.println(s1.getClass() == s2.getClass()); // true — both are exactly Circle
        System.out.println(s1.getClass() == s3.getClass()); // false — Circle vs Square
    }
}
```

`getClass()` returns the same `Class` object instance for every object of the same runtime type (there is exactly one `Class` object per loaded class in the JVM), so comparing `getClass()` results with `==` is a safe, exact way to check "are these two objects of the identical runtime type."

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A reference declared as the supertype but pointing to a subtype instance reports the subtype when getClass is called, always the true runtime type">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="40" y="25" width="200" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="47" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Animal a = new Dog();</text>

  <line x1="140" y1="60" x2="140" y2="85" stroke="#8b949e" stroke-width="1.5"/>
  <text x="140" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">a.getClass()</text>

  <rect x="40" y="90" width="200" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="140" y="112" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">reports: class Dog</text>

  <text x="450" y="55" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Declared type (Animal) is a</text>
  <text x="450" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">compile-time label only.</text>
  <text x="450" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getClass() always reports the</text>
  <text x="450" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">true runtime type: Dog, here.</text>
</svg>

`getClass()` always reveals the true runtime type, never the compile-time declared type of the variable.

## 5. Runnable example

Scenario: a shape-processing system that groups objects by exact type using `getClass()`, evolved from a simple type check into a working type-counting tool, then hardened with an exact-match `equals()` that relies on `getClass()` correctly.

### Level 1 — Basic

```java
public class GetClassBasic {
    static class Shape { }
    static class Circle extends Shape { }
    static class Square extends Shape { }

    public static void main(String[] args) {
        Shape s = new Circle();
        System.out.println(s.getClass().getSimpleName()); // Circle, not Shape
    }
}
```

**How to run:** `java GetClassBasic.java`

Even though `s` is declared as `Shape`, `s.getClass().getSimpleName()` prints `"Circle"` — the *declared* type never appears here, only the actual class used with `new`.

### Level 2 — Intermediate

Same shapes, now counting how many of each exact type appear in a list, using `getClass()` as a grouping key — something `instanceof` checks alone could not do as cleanly for many types at once.

```java
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class GetClassIntermediate {
    static class Shape { }
    static class Circle extends Shape { }
    static class Square extends Shape { }

    public static void main(String[] args) {
        List<Shape> shapes = List.of(new Circle(), new Square(), new Circle(), new Circle());

        Map<String, Integer> counts = new HashMap<>();
        for (Shape s : shapes) {
            String typeName = s.getClass().getSimpleName();
            counts.merge(typeName, 1, Integer::sum); // group by exact runtime type
        }
        System.out.println(counts); // {Circle=3, Square=1}
    }
}
```

**How to run:** `java GetClassIntermediate.java`

`s.getClass().getSimpleName()` is used as the grouping key for each shape, so `Circle` instances and `Square` instances are tallied separately based on their true runtime type, giving an accurate per-type count regardless of the fact that every element in the list is declared only as `Shape`.

### Level 3 — Advanced

Same shape system, now with a `Shape` subclass carrying data and an `equals()` override that uses `getClass()` for an exact-type match, demonstrating the interaction between `getClass()` and the equals contract from the previous topic in a concrete, runnable scenario.

```java
import java.util.Objects;

public class GetClassAdvanced {
    static class Shape {
        double area;
        Shape(double area) { this.area = area; }

        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (obj == null || getClass() != obj.getClass()) return false; // exact type match
            Shape other = (Shape) obj;
            return Double.compare(this.area, other.area) == 0;
        }

        @Override
        public int hashCode() { return Objects.hash(area); }
    }

    static class Circle extends Shape {
        Circle(double area) { super(area); }
    }

    static class Square extends Shape {
        Square(double area) { super(area); }
    }

    public static void main(String[] args) {
        Shape plainShape = new Shape(10.0);
        Circle circle = new Circle(10.0);
        Square square = new Square(10.0);

        System.out.println(plainShape.equals(circle)); // false — Shape.class != Circle.class
        System.out.println(circle.equals(square));     // false — Circle.class != Square.class

        Circle circle2 = new Circle(10.0);
        System.out.println(circle.equals(circle2));    // true — both exactly Circle, same area
    }
}
```

**How to run:** `java GetClassAdvanced.java`

`getClass() != obj.getClass()` requires both objects to share the exact same runtime class, so a `Shape` and a `Circle` with matching `area` are still never equal (`Shape.class` and `Circle.class` are different `Class` objects), and neither are a `Circle` and a `Square` — only two objects of the exact same class, `Circle` in this case, with matching `area` are considered equal.

## 6. Walkthrough

Trace all three `equals` calls in `GetClassAdvanced.main`.

**`plainShape.equals(circle)`.** `this == obj` is `false`. `obj == null` is `false`. `getClass()` on `plainShape` returns `Shape.class`; `obj.getClass()` on `circle` returns `Circle.class`. `Shape.class != Circle.class` is `true` (they are different `Class` objects, one per loaded class), so the condition `getClass() != obj.getClass()` is `true`, and `equals` returns `false` immediately — the `area` values are never even compared.

**`circle.equals(square)`.** Same pattern: `getClass()` on `circle` is `Circle.class`, `getClass()` on `square` is `Square.class`. These differ, so `equals` again returns `false` without comparing `area`.

**`circle.equals(circle2)`.** `this == obj` is `false` (distinct objects). `getClass()` on both is `Circle.class` — since there is exactly one `Class` object per loaded class in the JVM, `Circle.class == Circle.class` is `true`, so `getClass() != obj.getClass()` is `false`, and execution proceeds. The cast `(Shape) obj` succeeds. `Double.compare(10.0, 10.0)` returns `0`, so the comparison is `true`, and `equals` returns `true`.

```
plainShape.equals(circle): Shape.class != Circle.class -> false (area never checked)
circle.equals(square):     Circle.class != Square.class -> false (area never checked)
circle.equals(circle2):    Circle.class == Circle.class -> proceed -> area 10.0 == 10.0 -> true
```

**Final output.** `false`, `false`, `true` — three lines demonstrating that `getClass()`-based equality requires an exact runtime type match before any field is even compared, which is precisely why a `Shape`, a `Circle`, and a `Square` with identical `area` values are still mostly considered distinct from one another.

## 7. Gotchas & takeaways

> **`getClass()` is `final` and cannot be overridden** — unlike `toString()`, `equals()`, and `hashCode()`, there is no way to customize what `getClass()` reports; it always faithfully returns the true runtime class, which is exactly what makes it trustworthy for exact-type checks like the `equals()` pattern shown here.

> **`getClass()` and `instanceof` answer different questions** — `obj instanceof Shape` is `true` for a `Shape`, a `Circle`, or a `Square` (anything "is-a" `Shape`), while `obj.getClass() == Shape.class` is `true` only for an object constructed exactly as `Shape`, never for a subclass instance. Confusing the two is a common source of subtle bugs, especially inside `equals()` overrides.

- `getClass()` always returns the object's true runtime type, regardless of the declared type of the variable referencing it.
- There is exactly one `Class` object per loaded class, so `getClass()` results can be safely compared with `==` for an exact-type match.
- `getClass() != obj.getClass()` inside `equals()` requires exact type equality, avoiding the symmetry issues `instanceof` can introduce across a hierarchy.
- Prefer `instanceof` and polymorphism for ordinary "is-a" checks and behaviour; reach for `getClass()` specifically when exact type identity matters.
