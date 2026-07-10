---
card: java
gi: 948
slug: recursive-type-bounds-t-extends-comparable-t
title: "Recursive type bounds (T extends Comparable<T>)"
---

## 1. What it is

A recursive type bound is a generic type parameter declaration where the bound itself refers back to the type parameter being declared — the canonical example is `<T extends Comparable<T>>`, read as "T must be a type that can be compared *to itself*." This is sometimes called the "curiously recurring generic pattern." It exists to solve a real precision problem: a plain bound like `<T extends Comparable>` (raw, unparameterized) or even `<T extends Object>` would let you call `compareTo` but wouldn't guarantee the argument to `compareTo` is the *same type* `T` — with `T extends Comparable<T>`, the compiler enforces that whatever concrete type is substituted for `T` (say, `Integer`) implements `Comparable` specifically parameterized with itself (`Integer implements Comparable<Integer>`), so a method generic over such a `T` can safely call `a.compareTo(b)` knowing both `a` and `b` are guaranteed to be mutually comparable, not just "comparable to something."

## 2. Why & when

This pattern matters anywhere you write a generic method or class that needs to compare, sort, or order values of an unknown-but-consistent type — a generic `max` function, a generic sorted collection, or a custom `Comparable`-based data structure. Without the recursive bound, you'd either need an unsafe unchecked cast inside the method body (casting the `Comparable`'s type parameter to whatever you assume it is, which the compiler cannot verify and which could fail at runtime with a `ClassCastException`), or you'd have to give up on generics for this scenario entirely and accept raw types, losing all compile-time type safety. It's also exactly the pattern the JDK itself relies on: `Collections.max`, `Collections.sort` (the `Comparable`-based overloads), and the `Comparable` interface's own contract implicitly assume this pattern for any class that correctly implements it — when you write `class MyValue implements Comparable<MyValue>`, you are participating in exactly this recursive relationship, whether or not you think of it in those terms.

## 3. Core concept

```
interface Comparable<T> {
    int compareTo(T o);
}

class Money implements Comparable<Money> {     // T = Money -- "Money is comparable to Money"
    public int compareTo(Money other) { ... }
}

// A generic method wanting to accept ANY type that is comparable TO ITSELF:
static <T extends Comparable<T>> T max(T a, T b) {
    return a.compareTo(b) >= 0 ? a : b;
}

max(moneyA, moneyB);      // OK: Money implements Comparable<Money> -- T=Money satisfies the bound
max(3, "hello");           // COMPILE ERROR: no single T is Comparable<T> for BOTH an Integer and a String
```

The bound `T extends Comparable<T>` is read: "substitute any type for T, as long as that same type also appears as the type argument to Comparable" — a self-referential constraint the compiler checks at every call site.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Money implementing Comparable of Money, forming a self-referential loop that the bound T extends Comparable of T requires" >
  <rect x="240" y="40" width="160" height="50" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="60" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">class Money</text>
  <text x="320" y="76" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">implements Comparable&lt;Money&gt;</text>

  <path d="M 400 55 C 470 30, 470 100, 400 75" fill="none" stroke="#79c0ff" marker-end="url(#a)"/>
  <text x="470" y="65" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">refers to</text>
  <text x="470" y="78" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">itself</text>

  <text x="320" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">T extends Comparable&lt;T&gt; requires exactly this self-referential shape --</text>
  <text x="320" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">a type that is comparable specifically to ITSELF, not to something else</text>
</svg>

*A recursive type bound requires the substituted type to loop back and reference itself as the comparison target.*

## 5. Runnable example

Scenario: build a small generic ranking utility around the recursive bound — starting with a basic generic `max` using it directly, then extending to a custom domain class that must correctly implement the recursive relationship to participate, then handling the harder real case of a class hierarchy where a naive bound would incorrectly reject valid subclass comparisons.

### Level 1 — Basic

```java
public class RecursiveBoundBasic {
    static <T extends Comparable<T>> T max(T a, T b) {
        return a.compareTo(b) >= 0 ? a : b;
    }

    public static void main(String[] args) {
        System.out.println(max(3, 9));              // Integer implements Comparable<Integer>
        System.out.println(max("pear", "apple"));    // String implements Comparable<String>
    }
}
```

**How to run:** `java RecursiveBoundBasic.java` (JDK 17+).

Expected output:
```
9
pear
```

Both `Integer` and `String` already implement `Comparable` parameterized with themselves (`Comparable<Integer>` and `Comparable<String>` respectively), so both satisfy the bound `T extends Comparable<T>` directly, and `max` works for either without any casting or unsafe operations.

### Level 2 — Intermediate

```java
public class RecursiveBoundCustomType {
    static class Money implements Comparable<Money> {
        final long cents;
        Money(long cents) { this.cents = cents; }
        public int compareTo(Money other) { return Long.compare(this.cents, other.cents); }
        public String toString() { return "$" + (cents / 100.0); }
    }

    static <T extends Comparable<T>> T max(T a, T b) {
        return a.compareTo(b) >= 0 ? a : b;
    }

    public static void main(String[] args) {
        Money price1 = new Money(1999);
        Money price2 = new Money(2499);
        System.out.println("higher price: " + max(price1, price2));
    }
}
```

**How to run:** `java RecursiveBoundCustomType.java` (JDK 17+).

Expected output:
```
higher price: $24.99
```

The real-world concern added: `Money` is a custom domain type, not a JDK built-in, and it must explicitly declare `implements Comparable<Money>` (not just `implements Comparable`) to participate in the recursive bound at all — this is the exact obligation `T extends Comparable<T>` places on any class that wants to be usable with generic comparison utilities like this `max` method, and getting it wrong (e.g., accidentally implementing raw `Comparable` without the type argument) would produce compiler warnings and lose this type safety.

### Level 3 — Advanced

```java
public class RecursiveBoundHierarchy {
    static abstract class Shape implements Comparable<Shape> {
        abstract double area();
        public int compareTo(Shape other) { return Double.compare(this.area(), other.area()); }
    }
    static class Circle extends Shape {
        double radius;
        Circle(double radius) { this.radius = radius; }
        double area() { return Math.PI * radius * radius; }
        public String toString() { return "Circle(r=" + radius + ", area=" + String.format("%.2f", area()) + ")"; }
    }
    static class Square extends Shape {
        double side;
        Square(double side) { this.side = side; }
        double area() { return side * side; }
        public String toString() { return "Square(s=" + side + ", area=" + String.format("%.2f", area()) + ")"; }
    }

    // Note the bound here is "T extends Comparable<? super T>" -- NOT "Comparable<T>" --
    // this is the standard, more permissive bound (as used by Collections.max in the JDK)
    // that correctly allows comparing subclasses whose comparison logic lives in a SUPERCLASS.
    static <T extends Comparable<? super T>> T largest(T a, T b) {
        return a.compareTo(b) >= 0 ? a : b;
    }

    public static void main(String[] args) {
        Circle c = new Circle(3.0);
        Square s = new Square(5.0);
        Shape bigger = largest(c, s); // mixing Circle and Square, both are Shapes
        System.out.println("bigger shape: " + bigger);
    }
}
```

**How to run:** `java RecursiveBoundHierarchy.java` (JDK 17+).

Expected output:
```
bigger shape: Circle(r=3.0, area=28.27)
```

The production-flavored hard case: `Circle` and `Square` don't implement `Comparable<Circle>` or `Comparable<Square>` directly — their comparison logic is inherited from `Shape`, which implements `Comparable<Shape>`; a strict bound of `T extends Comparable<T>` would actually reject calling `largest(c, s)` with `T` inferred as `Shape`, since neither `Circle` nor `Square` implements `Comparable<Shape>` *by name* even though they inherit exactly that behavior — using the more permissive `Comparable<? super T>` bound (matching what `Collections.max` actually uses in the JDK) correctly accepts this common real-world pattern, where comparison logic is defined once in a shared superclass rather than redeclared in every subclass.

## 6. Walkthrough

Tracing `RecursiveBoundHierarchy.main` end to end:

1. `largest(c, s)` is called with a `Circle` and a `Square` — the compiler must infer a single `T` that both arguments share and that satisfies the method's bound, `T extends Comparable<? super T>`.
2. The most specific common supertype of `Circle` and `Square` is `Shape`, so the compiler infers `T = Shape` — it then checks the bound: does `Shape` implement `Comparable<? super Shape>`? Since `Shape` implements `Comparable<Shape>` directly, and `Shape` is trivially a "super" of itself in this wildcard sense, the bound is satisfied.
3. Crucially, this inference would fail with the stricter `T extends Comparable<T>` bound from the earlier examples, because neither `Circle` nor `Square` implements `Comparable<Shape>` by name — only `Shape` itself does, and the stricter bound doesn't account for inherited comparison logic living in a common ancestor; this is exactly why the JDK's own `Collections.max` uses the more permissive `? super T` form.
4. Inside `largest`, `a.compareTo(b)` is called — since `a` and `b` are both statically typed as `Shape` at this point (the inferred `T`), this resolves, via ordinary virtual dispatch, to `Shape.compareTo`, which calls `this.area()` and `other.area()` — themselves virtual calls that resolve to whichever subclass's `area()` override is appropriate for the actual runtime object (`Circle.area()` for `c`, `Square.area()` for `s`).
5. `Circle`'s area is `π × 3² ≈ 28.27`; `Square`'s area is `5² = 25.0` — since `a=c` and `b=s` in this call, `a.compareTo(b)` evaluates `Double.compare(28.27, 25.0)`, which is positive, so `a.compareTo(b) >= 0` is true and `a` (the circle) is returned as the larger shape.
6. The returned shape is printed via its own `toString()` override — the key structural lesson demonstrated end to end is that the recursive-bound relationship (`Comparable<T>` or, more permissively, `Comparable<? super T>`) is what allows a single generic method to safely and correctly dispatch comparison logic across an entire class hierarchy, not just a single concrete type.

## 7. Gotchas & takeaways

> **Gotcha:** the strict bound `T extends Comparable<T>` silently rejects any class hierarchy where comparison logic is defined in a common superclass rather than redeclared per-subclass — this is a common, easy-to-miss compile error when generifying code that works with class hierarchies; the standard, more permissive fix, matching the JDK's own `Collections.max`/`Collections.sort`, is `T extends Comparable<? super T>`.

- `T extends Comparable<T>` requires the type substituted for `T` to implement `Comparable` parameterized with itself — guaranteeing type-safe, self-consistent comparisons without unsafe casts.
- Any custom class wanting to participate must explicitly declare `implements Comparable<ThatClass>` (not raw `Comparable`) to satisfy the bound.
- For class hierarchies where comparison logic is inherited from a shared superclass, the stricter `Comparable<T>` bound incorrectly rejects valid subclass comparisons — use the more permissive `Comparable<? super T>` instead, matching the JDK's own convention.
- This pattern (sometimes called the "curiously recurring generic pattern") appears throughout the JDK, including in `Collections.max`, `Collections.sort`, and any API built around natural ordering.
- See [generic method type inference](0947-generic-method-type-inference.md) for how the compiler resolves `T` at each call site given this kind of bound, and [wildcard capture](0949-wildcard-capture.md) for the mechanics behind the `? super T` wildcard used in the more permissive variant.
