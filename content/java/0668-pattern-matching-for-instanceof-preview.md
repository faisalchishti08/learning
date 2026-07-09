---
card: java
gi: 668
slug: pattern-matching-for-instanceof-preview
title: Pattern matching for instanceof (preview)
---

## 1. What it is

**Pattern matching for `instanceof`**, introduced as a **preview feature** (JEP 305) in **Java 14**, lets you combine a type check and a cast into one expression: `if (obj instanceof String s) { ... }` checks whether `obj` is a `String` **and**, if so, binds it to a new local variable `s` of type `String`, usable immediately inside the `if` block — no separate cast statement needed. Before this, the idiom was always two steps: `if (obj instanceof String) { String s = (String) obj; ... }` — check, then redundantly cast something you'd literally just proven the type of. The pattern variable (`s` here) is only definitely in scope where the compiler can prove the `instanceof` check succeeded, following what's called "flow scoping" — a novel scoping rule tied to control flow rather than simple lexical nesting.

## 2. Why & when

The check-then-cast pattern was so common that most Java developers wrote it thousands of times without a second thought, but it's still boilerplate: you name the type twice, and if you're not careful, the cast can throw `ClassCastException` if it doesn't exactly mirror the `instanceof` check it followed. Pattern matching removes the duplication and the redundant cast entirely — the compiler already proved the type inside the `if` branch, so it just hands you a correctly-typed variable directly. Reach for this any time you'd otherwise write an `instanceof` check immediately followed by a cast to the same type — it's a strict improvement with no downside, and it composes especially well with early-return guard clauses and `&&`-chained conditions, since the pattern variable's scope can extend past the `if` block in specific, well-defined situations.

## 3. Core concept

```java
Object obj = "hello";

// Before: check, then separately cast
if (obj instanceof String) {
    String s = (String) obj;
    System.out.println(s.length());
}

// With pattern matching: check AND bind in one expression
if (obj instanceof String s) {
    System.out.println(s.length()); // s is already a String here
}

// Flow scoping: the pattern variable can extend beyond the if-block
// when control flow guarantees it's still valid.
if (!(obj instanceof String s)) {
    return; // if we get past this, obj definitely WAS a String
}
System.out.println(s.length()); // s is in scope HERE too
```

The pattern variable `s` follows the type check's truthiness through the surrounding control flow — it's in scope wherever the compiler can prove, from the structure of the code, that the `instanceof` check must have succeeded for execution to reach that point.

## 4. Diagram

<svg viewBox="0 0 620 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Traditional instanceof check followed by a separate cast versus pattern matching that checks and binds in one step">
  <rect x="10" y="20" width="290" height="130" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="155" y="42" fill="#f85149" font-size="12" text-anchor="middle" font-family="sans-serif">Before: check then cast</text>
  <text x="25" y="65" fill="#e6edf3" font-size="10" font-family="monospace">if (obj instanceof String) {</text>
  <text x="25" y="85" fill="#f85149" font-size="10" font-family="monospace">  String s = (String) obj;</text>
  <text x="25" y="100" fill="#8b949e" font-size="9" font-family="sans-serif">  // redundant cast — type</text>
  <text x="25" y="113" fill="#8b949e" font-size="9" font-family="sans-serif">  // was already proven above</text>
  <text x="25" y="130" fill="#e6edf3" font-size="10" font-family="monospace">}</text>

  <rect x="320" y="20" width="290" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Pattern matching: check + bind</text>
  <text x="335" y="65" fill="#e6edf3" font-size="10" font-family="monospace">if (obj instanceof String s) {</text>
  <text x="335" y="85" fill="#79c0ff" font-size="10" font-family="monospace">  // s is already a String</text>
  <text x="335" y="100" fill="#79c0ff" font-size="10" font-family="monospace">  s.length();</text>
  <text x="335" y="130" fill="#e6edf3" font-size="10" font-family="monospace">}</text>
</svg>

Pattern matching folds the type check and the cast into a single, compiler-verified step, eliminating the redundant explicit cast entirely.

## 5. Runnable example

Scenario: processing a heterogeneous list of `Object`s representing shapes and computing their areas — first the traditional check-then-cast approach, then the pattern-matching equivalent, then a more elaborate version that chains multiple pattern checks with `&&` and uses flow-scoping guard clauses to keep the main logic flat and readable.

### Level 1 — Basic

```java
// File: ShapeAreaOld.java
import java.util.List;

public class ShapeAreaOld {
    static class Circle { double radius; Circle(double r) { radius = r; } }
    static class Rectangle { double width, height; Rectangle(double w, double h) { width = w; height = h; } }

    static double area(Object shape) {
        if (shape instanceof Circle) {
            Circle c = (Circle) shape;
            return Math.PI * c.radius * c.radius;
        } else if (shape instanceof Rectangle) {
            Rectangle r = (Rectangle) shape;
            return r.width * r.height;
        }
        return 0.0;
    }

    public static void main(String[] args) {
        List<Object> shapes = List.of(new Circle(2), new Rectangle(3, 4));
        for (Object s : shapes) {
            System.out.printf("%.2f%n", area(s));
        }
    }
}
```

**How to run:** `java ShapeAreaOld.java`

Expected output:
```
12.57
12.00
```

### Level 2 — Intermediate

```java
// File: ShapeAreaPattern.java
import java.util.List;

public class ShapeAreaPattern {
    static class Circle { double radius; Circle(double r) { radius = r; } }
    static class Rectangle { double width, height; Rectangle(double w, double h) { width = w; height = h; } }

    static double area(Object shape) {
        if (shape instanceof Circle c) {
            return Math.PI * c.radius * c.radius;
        } else if (shape instanceof Rectangle r) {
            return r.width * r.height;
        }
        return 0.0;
    }

    public static void main(String[] args) {
        List<Object> shapes = List.of(new Circle(2), new Rectangle(3, 4));
        for (Object s : shapes) {
            System.out.printf("%.2f%n", area(s));
        }
    }
}
```

**How to run:** requires the preview flag since this is a Java 14 preview feature:
```
javac --release 14 --enable-preview ShapeAreaPattern.java
java --enable-preview ShapeAreaPattern
```
(On modern JDKs 16+, `instanceof` pattern matching is permanent and no flags are needed.)

Expected output is identical to Level 1's:
```
12.57
12.00
```

Each branch's redundant `Circle c = (Circle) shape;`-style cast has vanished — the pattern variable (`c`, `r`) is bound directly by the `instanceof` check.

### Level 3 — Advanced

```java
// File: ShapeAreaGuarded.java
import java.util.List;

public class ShapeAreaGuarded {
    static class Circle { double radius; Circle(double r) { radius = r; } }
    static class Rectangle { double width, height; Rectangle(double w, double h) { width = w; height = h; } }

    static double area(Object shape) {
        // Flow-scoped guard clause: if shape is NOT a valid, positive-radius Circle,
        // bail out early. Past this point, if it WAS a Circle, c is still in scope.
        if (!(shape instanceof Circle c) || c.radius <= 0) {
            // fall through to check Rectangle instead
        } else {
            return Math.PI * c.radius * c.radius;
        }

        if (shape instanceof Rectangle r && r.width > 0 && r.height > 0) {
            return r.width * r.height;
        }

        throw new IllegalArgumentException("Not a valid shape: " + shape);
    }

    public static void main(String[] args) {
        List<Object> shapes = List.of(new Circle(2), new Rectangle(3, 4), new Circle(-1), "not a shape");
        for (Object s : shapes) {
            try {
                System.out.printf("%.2f%n", area(s));
            } catch (IllegalArgumentException e) {
                System.out.println("Rejected: " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `javac --release 14 --enable-preview ShapeAreaGuarded.java && java --enable-preview ShapeAreaGuarded`

Expected output:
```
12.57
12.00
Rejected: Not a valid shape: ShapeAreaGuarded$Circle@<hash>
Rejected: Not a valid shape: not a shape
```

Level 3 combines pattern matching with `&&` (`shape instanceof Rectangle r && r.width > 0 && r.height > 0` — `r` is only accessed once the `instanceof` check has already short-circuited to `true`) and with a negated guard-clause form (`!(shape instanceof Circle c) || c.radius <= 0` — `c` is safely readable in the second operand of `||` because Java's short-circuit evaluation guarantees `c` was successfully bound if the first operand was `false`), showing how flow scoping lets the pattern variable remain accessible in exactly the spots where the compiler can prove the check held.

## 6. Walkthrough

1. `main` calls `area(new Circle(-1))` (the third list element). Inside, the first `if` condition is `!(shape instanceof Circle c) || c.radius <= 0`.
2. Java evaluates the left operand first: `shape instanceof Circle c` checks whether `shape` (a `Circle` instance with `radius = -1`) is a `Circle` — it is, so the check succeeds and `c` is bound to that `Circle` reference. The `!` negates the check's `true` result to `false`.
3. Because the left operand of `||` is `false`, Java must evaluate the right operand to determine the whole expression: `c.radius <= 0`. Crucially, `c` is accessible here even though it was bound *inside* the negated `instanceof` on the other side of `||` — this is flow scoping in action: the compiler proved that if we've reached the right operand of `||`, the left operand's `instanceof` must have been `true` (otherwise `!(...)` would already be `true` and short-circuit evaluation would skip the right operand entirely), so `c` is guaranteed to have been successfully bound.
4. `c.radius <= 0` evaluates `-1 <= 0`, which is `true`. So the overall `||` expression is `true`, and the `if` branch's body (currently an empty comment-only block, intentionally falling through) executes — meaning this `Circle` was rejected as invalid due to its non-positive radius, and control proceeds past the `if`/`else` to the next check.
5. The next check, `shape instanceof Rectangle r && r.width > 0 && r.height > 0`, evaluates `shape instanceof Rectangle` first: `shape` is a `Circle`, not a `Rectangle`, so this is `false`. Short-circuit evaluation means the rest of the `&&` chain (including `r.width > 0`) never executes — `r` is never even bound, avoiding any risk of using an unbound variable.
6. Since neither shape check succeeded, execution reaches `throw new IllegalArgumentException("Not a valid shape: " + shape);`, which `main`'s `catch` block catches and prints as a rejection message.
7. Compare this to `area(new Circle(2))` (the first list element, processed earlier in the loop): step 2's `instanceof` check again succeeds and binds `c`, but step 3's `c.radius <= 0` evaluates `2 <= 0` as `false` — so the whole `||` is `false`, meaning `!(...)` was `false` **and** `radius <= 0` was `false`, so the `if` condition itself is `false`, sending control to the `else` branch, which computes and returns `Math.PI * c.radius * c.radius` directly — `c` remains in scope throughout the `else` branch for exactly the same flow-scoping reason.

```
area(Circle(radius=-1)):
  !(shape instanceof Circle c) → c bound, check=true → ! → false
  || c.radius<=0 → c still in scope here → -1<=0 → true
  overall: true → guard triggers → falls through → Rectangle check fails → throw
```

## 7. Gotchas & takeaways

> This is a **preview feature** in Java 14 — it requires `--enable-preview` on both `javac` and `java`. It became permanent (no flag needed) in Java 16, with the design essentially unchanged from this preview, making Java 14/15's preview a reliable early look at the final behavior — unlike some other features from this era (like text blocks), the `instanceof` pattern-matching semantics were largely stable across its preview cycle.

- The pattern variable is only definitely in scope where the compiler can *prove*, from the code's control-flow structure, that the `instanceof` check must have succeeded — this is "flow scoping," a genuinely new kind of scoping rule in Java.
- A negated check (`if (!(x instanceof Foo f)) { return; }`) followed by code that uses `f` afterward is a common, idiomatic guard-clause pattern enabled by flow scoping.
- Inside `&&` chains, a pattern variable bound by an earlier operand is usable in later operands (`x instanceof Foo f && f.isValid()`) — short-circuit evaluation guarantees `f` was successfully bound before the later operand runs.
- Inside `||` chains, the reverse doesn't generally hold — a pattern variable bound in one operand of `||` is not usable in a sibling operand, since `||` short-circuits on `true`, meaning the second operand only runs when the first was `false` (didn't match), so the pattern variable wouldn't have been bound.
- The pattern variable's name shadows any existing variable of the same name in an enclosing scope, just like a normal local variable declaration would — pick names that don't collide with meaningful existing variables to avoid confusing shadowing.
