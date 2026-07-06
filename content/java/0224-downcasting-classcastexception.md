---
card: java
gi: 224
slug: downcasting-classcastexception
title: Downcasting & ClassCastException
---

## 1. What it is

**Downcasting** is converting a supertype reference back to a more specific subtype reference — the reverse of upcasting — and unlike upcasting, it requires **explicit** cast syntax (`(SubType) reference`) and is **not guaranteed safe**: the compiler allows it, but the JVM checks at runtime whether the object being cast is genuinely an instance of that subtype. If it isn't, the JVM throws `ClassCastException` immediately.

```java
class Animal {}
class Dog extends Animal { void bark() { System.out.println("Woof"); } }
class Cat extends Animal { void meow() { System.out.println("Meow"); } }

Animal a = new Dog(); // upcast, safe, implicit

Dog d = (Dog) a; // downcast — explicit cast required
d.bark();          // fine — 'a' really does refer to a Dog underneath

Animal a2 = new Cat();
Dog d2 = (Dog) a2; // COMPILES, but throws ClassCastException at RUNTIME — a2 is really a Cat, not a Dog
```

`(Dog) a` succeeds because the object `a` actually refers to really is a `Dog`; `(Dog) a2` compiles identically (the compiler only checks that `Dog` and `Animal` are related by inheritance, not what the object *actually* is), but throws `ClassCastException` the instant it runs, since the real object is a `Cat`, not a `Dog`.

## 2. Why & when

Downcasting is needed specifically when code has an object through a general supertype reference but genuinely needs to use subtype-specific behaviour that the general type doesn't expose:

- **Regaining subtype-specific capability** — after upcasting (perhaps implicitly, by storing objects in a `List<Animal>`), if code needs to call a method that only `Dog` has, it must downcast back to `Dog` first.
- **The `instanceof` check-then-cast pattern** — safely downcasting means checking `if (obj instanceof Dog)` *before* casting, so the cast is only ever attempted when it's known to succeed, avoiding `ClassCastException` entirely.
- **Modern pattern-matching `instanceof`** — Java's `instanceof` with pattern variables (`if (obj instanceof Dog dog)`) combines the check and the cast into a single, safer expression, binding the correctly-typed variable only inside the branch where the check passed.

You downcast specifically when you're certain (or have just verified with `instanceof`) that an object referenced through a general type is actually a specific subtype, and you need to use that subtype's own additional members — reaching for downcasting without first verifying is a common source of runtime crashes.

## 3. Core concept

```java
class Animal {}
class Dog extends Animal { void bark() { System.out.println("Woof"); } }

void makeNoiseIfDog(Animal a) {
    if (a instanceof Dog) { // check FIRST
        Dog d = (Dog) a;    // THEN cast, guaranteed safe at this point
        d.bark();
    } else {
        System.out.println("Not a dog, staying quiet");
    }
}

makeNoiseIfDog(new Dog()); // Woof
makeNoiseIfDog(new Animal()); // Not a dog, staying quiet — no exception, since the cast was never attempted
```

Checking `a instanceof Dog` *before* attempting `(Dog) a` guarantees the cast can never fail — this "check, then cast" pattern is the standard, safe way to downcast, entirely avoiding the risk of `ClassCastException` at runtime.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An Animal reference checked with instanceof Dog first, branching to a safe cast and bark call if true, or a quiet fallback message if false, contrasted with an unchecked direct cast that risks throwing ClassCastException at runtime if the object is not actually a Dog">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="220" y="20" width="160" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="300" y="42" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">a instanceof Dog?</text>

  <line x1="260" y1="55" x2="150" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#dc)"/>
  <text x="150" y="75" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">true</text>
  <rect x="60" y="95" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="120" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">(Dog) a — SAFE cast, then bark()</text>

  <line x1="340" y1="55" x2="450" y2="90" stroke="#f85149" stroke-width="1.5" marker-end="url(#dc)"/>
  <text x="450" y="75" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">false</text>
  <rect x="360" y="95" width="180" height="40" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="450" y="120" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">skip cast — no exception risk</text>

  <text x="300" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Checking first eliminates the possibility of ClassCastException entirely.</text>

  <defs><marker id="dc" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Checking with `instanceof` before casting guarantees the cast will always succeed.

## 5. Runnable example

Scenario: processing a mixed list of shapes needing type-specific behaviour beyond the shared supertype — starting with a basic unchecked downcast that risks an exception, then extending with the safe `instanceof`-guarded pattern, then hardening into modern pattern-matching `instanceof` handling multiple subtypes cleanly.

### Level 1 — Basic

```java
public class DowncastBasic {
    static class Shape {}
    static class Circle extends Shape {
        double radius = 5;
    }

    public static void main(String[] args) {
        Shape s = new Circle(); // upcast at declaration

        Circle c = (Circle) s; // downcast — succeeds here, since s really is a Circle
        System.out.println("Radius: " + c.radius);
    }
}
```

**How to run:** `java DowncastBasic.java`

`(Circle) s` succeeds because `s` genuinely refers to a `Circle` object underneath its `Shape`-typed declaration — this cast is safe in this specific case, but nothing in the code *guarantees* that safety; it depends entirely on knowing, externally, what `s` actually is.

### Level 2 — Intermediate

Same scenario, now demonstrating the risk directly: an unchecked downcast that fails, and the safe `instanceof`-guarded alternative that avoids the crash.

```java
public class DowncastIntermediate {
    static class Shape {}
    static class Circle extends Shape { double radius = 5; }
    static class Square extends Shape { double side = 3; }

    public static void main(String[] args) {
        Shape s = new Square(); // NOT actually a Circle

        try {
            Circle c = (Circle) s; // unchecked — throws ClassCastException
            System.out.println("Radius: " + c.radius);
        } catch (ClassCastException e) {
            System.out.println("Unchecked cast failed: " + e.getMessage());
        }

        if (s instanceof Circle) { // safe pattern: check first
            Circle c = (Circle) s;
            System.out.println("Radius: " + c.radius);
        } else {
            System.out.println("Not a Circle — safely skipped the cast entirely");
        }
    }
}
```

**How to run:** `java DowncastIntermediate.java`

The first block deliberately attempts an unchecked `(Circle) s` when `s` is actually a `Square`, catching the resulting `ClassCastException`; the second block checks `s instanceof Circle` first, correctly determines it's `false`, and safely skips the cast entirely — demonstrating both the risk of unchecked downcasting and the safe alternative side by side.

### Level 3 — Advanced

Same scenario, now using modern pattern-matching `instanceof` to handle a mixed list of shapes cleanly, combining the check and the cast into one expression per subtype, with no risk of `ClassCastException` anywhere.

```java
import java.util.List;

public class DowncastAdvanced {
    static class Shape {}
    static class Circle extends Shape { double radius; Circle(double r) { radius = r; } }
    static class Square extends Shape { double side; Square(double s) { side = s; } }
    static class Triangle extends Shape { double base, height; Triangle(double b, double h) { base = b; height = h; } }

    static double areaOf(Shape s) {
        if (s instanceof Circle circle) { // pattern matching: check AND bind in one step
            return Math.PI * circle.radius * circle.radius;
        } else if (s instanceof Square square) {
            return square.side * square.side;
        } else if (s instanceof Triangle triangle) {
            return 0.5 * triangle.base * triangle.height;
        }
        return 0.0; // unknown shape type
    }

    public static void main(String[] args) {
        List<Shape> shapes = List.of(new Circle(3), new Square(4), new Triangle(6, 2));

        for (Shape s : shapes) {
            System.out.printf("%s area: %.2f%n", s.getClass().getSimpleName(), areaOf(s));
        }
    }
}
```

**How to run:** `java DowncastAdvanced.java`

`s instanceof Circle circle` checks the type *and*, only if it matches, binds `circle` as a properly-typed `Circle` variable usable directly inside that branch — no separate explicit `(Circle) s` cast is even written; this pattern-matching form combines safety (the check always happens first) with conciseness (no repeated, separately-written cast).

## 6. Walkthrough

Trace `areaOf(new Triangle(6, 2))` from `DowncastAdvanced.main`:

**First check.** `s instanceof Circle circle` — the actual object is a `Triangle`, not a `Circle` — this evaluates `false`; the `circle` variable is never bound, and this branch is skipped entirely.

**Second check.** `s instanceof Square square` — still `false`, since the object is a `Triangle`, not a `Square`; skipped.

**Third check.** `s instanceof Triangle triangle` — `true`, since the object genuinely is a `Triangle`. The pattern variable `triangle` is bound, correctly typed as `Triangle`, giving direct access to `triangle.base` and `triangle.height`.

**Calculation.** `return 0.5 * triangle.base * triangle.height` computes `0.5 * 6 * 2 = 6.0`.

```
areaOf(Triangle(base=6, height=2)):
  instanceof Circle?   false -> skip
  instanceof Square?   false -> skip
  instanceof Triangle? true  -> triangle bound, base=6, height=2
  return 0.5 * 6 * 2 = 6.0
```

**Final output.** For all three shapes in the list, the loop prints each one's class name and computed area: `"Circle area: 28.27"`, `"Square area: 16.00"`, `"Triangle area: 6.00"` — each correctly routed to the matching `instanceof` branch, with no unchecked cast anywhere in the code, and therefore no possibility of `ClassCastException` at all.

## 7. Gotchas & takeaways

> **The compiler only verifies that a downcast's target type is *related* by inheritance to the source reference's declared type — it cannot verify what the object actually is at compile time.** `(Dog) someAnimalReference` always compiles as long as `Dog` is a subclass of `Animal`, regardless of what the object actually turns out to be at runtime; the real safety check only happens when the cast executes.

> **Modern pattern-matching `instanceof` (`if (obj instanceof Type variable)`) is generally preferred over the older separate check-then-cast pattern**, since it eliminates the possibility of forgetting the explicit cast after the check, or mistakenly casting to a different type than what was actually checked — a subtle bug the combined syntax makes structurally impossible.

- Downcasting requires an explicit cast and is checked by the JVM at runtime — if the object isn't genuinely an instance of the target type, `ClassCastException` is thrown immediately.
- Always check with `instanceof` before downcasting, unless you have some other absolute guarantee about the object's actual type.
- Pattern-matching `instanceof` (`if (obj instanceof Type var)`) combines the check and the cast safely into a single expression.
- The compiler only verifies type *relatedness* for a cast, not the object's actual runtime type — that verification only happens when the cast is actually executed.
