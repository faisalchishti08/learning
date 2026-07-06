---
card: java
gi: 356
slug: upper-bounded-wildcard-extends-t
title: Upper-bounded wildcard (? extends T)
---

## 1. What it is

An upper-bounded wildcard, `? extends T`, restricts an unknown type to "T or some subtype of T" — `List<? extends Number>` means "a list of some specific type that is `Number` or a subtype of it (`Integer`, `Double`, and so on), we just don't know exactly which." Combined with generic invariance, this is what finally lets a method accept `List<Integer>`, `List<Double>`, and `List<Number>` all through a single parameter, something a plain `List<Number>` parameter could never do.

```java
import java.util.List;

public class UpperBoundedDemo {
    static double sumAll(List<? extends Number> numbers) { // accepts List<Integer>, List<Double>, etc.
        double total = 0;
        for (Number n : numbers) total += n.doubleValue(); // reading is safe -- always at least a Number
        return total;
    }

    public static void main(String[] args) {
        System.out.println(sumAll(List.of(1, 2, 3)));       // List<Integer>
        System.out.println(sumAll(List.of(1.5, 2.5)));      // List<Double>
    }
}
```

`sumAll(List<? extends Number> numbers)` accepts both `List<Integer>` and `List<Double>` — a parameter typed `List<Number>` would reject both, since `List<Integer>` is not a subtype of `List<Number>` even though `Integer` is a subtype of `Number`.

## 2. Why & when

Upper-bounded wildcards exist specifically to make read-heavy generic APIs flexible without sacrificing type safety — they're the standard tool for "I want to accept a collection of this type *or any subtype*," which comes up constantly whenever a method processes but doesn't need to add unrelated elements to a generic collection.

- **Accepting a producer of a specific type family** — a method that reads numbers, shapes, or any type hierarchy's elements from a collection, without needing the exact concrete type to match precisely.
- **Widening an API's usability without changing its safety** — `List<? extends Number>` is strictly more flexible than `List<Number>` for callers, while still guaranteeing every element read out is at least a `Number`.
- **Following the standard "read from it" half of the PECS guideline** — Producer Extends: when a generic parameter is only ever read from (produces values for you), an upper-bounded wildcard is usually the right choice.

An upper-bounded wildcard makes a collection effectively **read-only** for adding new elements (beyond `null`) — the compiler knows every element is *at least* `T`, but doesn't know which specific subtype the collection actually holds, so it can't verify that anything you try to add matches; this is the same restriction as a bare `?` wildcard, just with a more specific known lower limit on what comes *out*.

## 3. Core concept

```java
import java.util.List;

public class UpperBoundedCore {
    static class Animal { String name() { return "Animal"; } }
    static class Dog extends Animal { String name() { return "Dog"; } }
    static class Cat extends Animal { String name() { return "Cat"; } }

    static void greetAll(List<? extends Animal> animals) { // accepts List<Dog>, List<Cat>, List<Animal>
        for (Animal a : animals) System.out.println("Hello, " + a.name());
    }

    public static void main(String[] args) {
        greetAll(List.of(new Dog(), new Dog()));
        greetAll(List.of(new Cat()));
        greetAll(List.of(new Animal(), new Dog())); // mixed, but all ARE Animal
    }
}
```

**How to run:** `java UpperBoundedCore.java`

`greetAll` reads each element as an `Animal` (the upper bound), regardless of whether the actual list is `List<Dog>`, `List<Cat>`, or a mixed `List<Animal>` — every element is guaranteed to be *at least* an `Animal`, which is all `greetAll` needs to call `name()`.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="an upper-bounded wildcard List<? extends Animal> accepts a list of Animal or any of its subtypes, with elements always readable as at least an Animal">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="260" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="52" fill="#79c0ff" font-size="10" text-anchor="middle">greetAll(List&lt;? extends Animal&gt;)</text>

  <text x="300" y="50" fill="#8b949e" font-size="10">accepts:</text>
  <rect x="360" y="15" width="100" height="25" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="410" y="32" fill="#6db33f" font-size="9" text-anchor="middle">List&lt;Dog&gt;</text>
  <rect x="360" y="45" width="100" height="25" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="410" y="62" fill="#6db33f" font-size="9" text-anchor="middle">List&lt;Cat&gt;</text>
  <rect x="360" y="75" width="100" height="25" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="410" y="92" fill="#6db33f" font-size="9" text-anchor="middle">List&lt;Animal&gt;</text>
</svg>

## 5. Runnable example

Scenario: a small shape-area calculator, evolved from one accepting only an exact type, into one accepting any subtype via an upper-bounded wildcard, into a production-style calculator that also demonstrates the write restriction upper bounds impose.

### Level 1 — Basic

```java
import java.util.List;

public class ShapeAreaBasic {
    static class Shape { double area() { return 0; } }
    static class Circle extends Shape { double area() { return 3.14 * 2 * 2; } }

    static double totalArea(List<Shape> shapes) { // requires the EXACT type List<Shape>
        double total = 0;
        for (Shape s : shapes) total += s.area();
        return total;
    }

    public static void main(String[] args) {
        List<Shape> shapes = List.of(new Circle(), new Circle());
        System.out.println("Total area: " + totalArea(shapes));
        // totalArea(List.of(new Circle(), new Circle())); // would need List<Shape>, not List<Circle>
    }
}
```

**How to run:** `java ShapeAreaBasic.java`

`totalArea` requires exactly `List<Shape>` — a `List<Circle>` (a perfectly reasonable "list of shapes" conceptually) is rejected, since generics are invariant and `List<Circle>` is not a subtype of `List<Shape>`.

### Level 2 — Intermediate

```java
import java.util.List;

public class ShapeAreaIntermediate {
    static class Shape { double area() { return 0; } }
    static class Circle extends Shape { double area() { return 3.14 * 2 * 2; } }
    static class Square extends Shape { double area() { return 4 * 4; } }

    static double totalArea(List<? extends Shape> shapes) { // upper-bounded wildcard
        double total = 0;
        for (Shape s : shapes) total += s.area();
        return total;
    }

    public static void main(String[] args) {
        System.out.println("Circles: " + totalArea(List.of(new Circle(), new Circle())));
        System.out.println("Squares: " + totalArea(List.of(new Square())));
        System.out.println("Mixed: " + totalArea(List.of(new Circle(), new Square())));
    }
}
```

**How to run:** `java ShapeAreaIntermediate.java`

Switching to `List<? extends Shape>` now correctly accepts `List<Circle>`, `List<Square>`, and a mixed `List<Shape>` — each element is still readable as at least a `Shape` (enough to call `area()`), regardless of which specific subtype the underlying list actually holds.

### Level 3 — Advanced

```java
import java.util.List;
import java.util.ArrayList;

public class ShapeAreaAdvanced {
    static class Shape { double area() { return 0; } String label() { return "Shape"; } }
    static class Circle extends Shape { double area() { return 3.14 * 2 * 2; } String label() { return "Circle"; } }
    static class Square extends Shape { double area() { return 4 * 4; } String label() { return "Square"; } }

    static String describeTotal(List<? extends Shape> shapes) {
        double total = 0;
        StringBuilder labels = new StringBuilder();
        for (Shape s : shapes) {
            total += s.area();
            labels.append(s.label()).append(" ");
        }
        // shapes.add(new Circle()); // would NOT compile -- can't know the list's real element type
        return "Shapes [" + labels.toString().trim() + "] total area: " + total;
    }

    public static void main(String[] args) {
        List<Circle> circles = new ArrayList<>(List.of(new Circle(), new Circle()));
        System.out.println(describeTotal(circles));

        List<Shape> mixed = new ArrayList<>(List.of(new Circle(), new Square()));
        System.out.println(describeTotal(mixed));

        // Demonstrating the write restriction concretely:
        List<? extends Shape> readOnlyView = circles;
        System.out.println("Read-only view size: " + readOnlyView.size()); // reading is fine
    }
}
```

**How to run:** `java ShapeAreaAdvanced.java`

The commented-out `shapes.add(new Circle())` line marks exactly where the upper bound's restriction bites: even though every element read out is guaranteed to be *at least* a `Shape`, the compiler can't verify that a `Circle` you're trying to *add* actually matches whatever the real, unknown, specific list type is (it might really be a `List<Square>` being passed through a `List<? extends Shape>` reference) — so all additions except `null` are rejected.

## 6. Walkthrough

Execution starts in `main`, which creates `circles` (a genuine `List<Circle>`) and calls `describeTotal(circles)`.

Inside `describeTotal`, the parameter type `List<? extends Shape>` accepts the `List<Circle>` argument directly — `Circle` is a subtype of `Shape`, satisfying the upper bound. The `for (Shape s : shapes)` loop reads each element as a `Shape` (the compiler's known common ground, even though every actual element here is really a `Circle`): first `Circle`, `s.area()` returns `12.56` and `s.label()` returns `"Circle"`; same for the second `Circle`. `total` becomes `25.12`, `labels` becomes `"Circle Circle "`. The method returns `"Shapes [Circle Circle] total area: 25.12"`, which `main` prints.

`main` then creates `mixed` (a genuine `List<Shape>` containing one `Circle` and one `Square`) and calls `describeTotal(mixed)`. This time, the loop's first iteration reads a `Circle` (`area()` = `12.56`, `label()` = `"Circle"`); the second reads a `Square` (`area()` = `16.0`, `label()` = `"Square"`). `total` becomes `28.56`, `labels` becomes `"Circle Square "`. The method returns `"Shapes [Circle Square] total area: 28.56"`.

Finally, `main` assigns `circles` to a variable declared as `List<? extends Shape> readOnlyView` — this assignment is allowed (a `List<Circle>` genuinely satisfies "a list of some type extending `Shape`"), and `readOnlyView.size()` is called, returning `2`. This demonstrates that reading (including calling non-generic methods like `size()`) remains completely unrestricted through an upper-bounded wildcard reference — only *adding* a new, specific element to `shapes`/`readOnlyView` would have been rejected by the compiler.

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="both a homogeneous Circle list and a mixed Shape list are accepted by the same wildcard-typed method, each element read generically as Shape regardless of its real specific type">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">describeTotal(List&lt;Circle&gt;): each element read as Shape -&gt; area 12.56+12.56=25.12, labels "Circle Circle"</text>
  <text x="20" y="55" fill="#79c0ff" font-size="10">describeTotal(List&lt;Shape&gt; mixed): Circle then Square read as Shape -&gt; area 12.56+16.0=28.56</text>
  <text x="20" y="85" fill="#6db33f" font-size="10">List&lt;? extends Shape&gt; readOnlyView = circles -&gt; size() works fine (reading always safe)</text>
  <text x="20" y="110" fill="#f85149" font-size="10">shapes.add(new Circle()) -&gt; would NOT compile: real list type unknown, could be List&lt;Square&gt; underneath</text>
</svg>

## 7. Gotchas & takeaways

> An upper-bounded wildcard reference might genuinely be pointing at a list of a *different* subtype than the one you'd naively expect — `List<? extends Shape> shapes` could be backed by a real `List<Square>`, so `shapes.add(new Circle())` is correctly rejected, since adding a `Circle` to what's actually a `List<Square>` would silently corrupt it.

- `? extends T` means "T or some unknown subtype of T" — every element read out is guaranteed to be at least a `T`.
- Reading from an upper-bounded wildcard collection is always safe (elements come out typed as at least the bound); adding anything other than `null` is rejected, since the real specific element type is unknown.
- Use an upper-bounded wildcard when a generic parameter is a "producer" — something your method only reads values *from* — following the Producer Extends half of the PECS guideline.
- `List<? extends Number>` is strictly more flexible for callers than `List<Number>`, accepting `List<Integer>`, `List<Double>`, and any other `Number` subtype list, in addition to `List<Number>` itself.
- Choose an upper-bounded wildcard specifically (rather than a plain `?`) when your method body needs to call methods on the elements beyond what `Object` provides — the bound is what unlocks those specific methods.
