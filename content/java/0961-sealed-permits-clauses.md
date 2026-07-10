---
card: java
gi: 961
slug: sealed-permits-clauses
title: sealed / permits clauses
---

## 1. What it is

A sealed class or interface, standardized in Java 17, restricts exactly which other classes or interfaces are allowed to extend or implement it — declared with the `sealed` modifier and a `permits` clause listing the specific permitted subtypes by name: `sealed interface Shape permits Circle, Rectangle, Triangle {}`. Every class named in the `permits` list must itself declare how it continues the hierarchy — as `final` (no further subclassing allowed at all), `sealed` (restricting its own subclasses with its own `permits` clause), or `non-sealed` (explicitly reopening that one specific branch to unrestricted, ordinary subclassing) — this is a deliberate requirement, not an omission, forcing every permitted subtype to state its own intention explicitly rather than silently inheriting an ambiguous default. If every permitted subtype and the sealed type are declared in the same file, the `permits` clause can be omitted entirely, since the compiler can already see the complete set of subtypes directly from the file's contents.

## 2. Why & when

Sealing a hierarchy is the right choice whenever you want to express "these are *all* the possible variants of this concept, and no others should ever be added without deliberately revisiting this declaration" — a fixed, closed set of shapes, a fixed set of arithmetic expression node types, a fixed set of possible API response outcomes. This is a fundamentally different design intent from an ordinary, unsealed interface, which deliberately invites unknown, unlimited future implementers; sealing trades away that extensibility in exchange for a powerful benefit: the compiler now knows, completely and statically, every possible subtype, which is exactly what makes exhaustiveness checking in `switch` expressions possible (covered in [exhaustiveness in switch](0964-exhaustiveness-in-switch.md)) — a `switch` over a sealed type's variants can be verified, at compile time, to cover every case, with no `default` branch needed and no risk of a forgotten case silently falling through at runtime. Reach for `sealed` specifically when you have a genuinely closed, "this is the complete list" concept in your domain; keep an interface unsealed when you genuinely want to allow arbitrary third-party or future implementations you can't enumerate in advance.

## 3. Core concept

```
sealed interface Shape permits Circle, Rectangle, Triangle {}

final class Circle implements Shape { ... }           // FINAL -- ends this branch, no further subclassing

sealed class Rectangle implements Shape
        permits Square {}                              // SEALED -- has its OWN restricted subtypes

final class Square extends Rectangle { ... }            // must itself resolve: final here

non-sealed class Triangle implements Shape { ... }      // NON-SEALED -- deliberately REOPENS this branch;
                                                          // Triangle can now be extended without restriction

// Every class in Shape's permits list MUST be exactly one of: final, sealed, or non-sealed.
// This is enforced by the COMPILER -- omitting all three is a compile error.
```

The `permits` clause names the closed, complete set of direct subtypes; each of those subtypes must then explicitly declare whether the closure continues (`final`/`sealed`) or is deliberately broken open again (`non-sealed`) at that specific point in the hierarchy.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A sealed Shape interface permitting exactly Circle, Rectangle, and Triangle, where Circle is final, Rectangle is itself sealed permitting only Square, and Triangle is non-sealed and open to further extension" >
  <rect x="240" y="10" width="160" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="29" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">sealed interface Shape</text>

  <rect x="60" y="70" width="130" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="125" y="89" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">final class Circle</text>

  <rect x="250" y="70" width="140" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="320" y="89" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">sealed class Rectangle</text>

  <rect x="450" y="70" width="150" height="30" fill="#1c2430" stroke="#e6edf3"/>
  <text x="525" y="89" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">non-sealed class Triangle</text>

  <rect x="250" y="130" width="140" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="149" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">final class Square</text>

  <rect x="450" y="130" width="150" height="30" fill="none" stroke="#8b949e" stroke-dasharray="3"/>
  <text x="525" y="149" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">...any future subclass...</text>

  <line x1="200" y1="30" x2="125" y2="70" stroke="#8b949e"/>
  <line x1="280" y1="30" x2="320" y2="70" stroke="#8b949e"/>
  <line x1="360" y1="30" x2="525" y2="70" stroke="#8b949e"/>
  <line x1="320" y1="100" x2="320" y2="130" stroke="#8b949e"/>
  <line x1="525" y1="100" x2="525" y2="130" stroke="#8b949e" stroke-dasharray="3"/>
</svg>

*Shape's closure is total for Circle (final) and precisely bounded for Rectangle (sealed to only Square), but deliberately reopened at Triangle (non-sealed).*

## 5. Runnable example

Scenario: model a small closed shape hierarchy end to end, evolving from a basic sealed interface with final implementers, to a realistic case adding a nested sealed subtype, to a more advanced case demonstrating the compile-time enforcement that makes sealing meaningfully different from an ordinary interface.

### Level 1 — Basic

```java
public class SealedBasic {
    sealed interface Shape permits Circle, Square {}
    record Circle(double radius) implements Shape {}
    record Square(double side) implements Shape {}

    static double area(Shape shape) {
        if (shape instanceof Circle c) return Math.PI * c.radius() * c.radius();
        if (shape instanceof Square s) return s.side() * s.side();
        throw new IllegalStateException("unreachable -- Shape is sealed to exactly these two types");
    }

    public static void main(String[] args) {
        System.out.printf("circle area: %.2f%n", area(new Circle(2.0)));
        System.out.printf("square area: %.2f%n", area(new Square(3.0)));
    }
}
```

**How to run:** `java SealedBasic.java` (JDK 17+).

Expected output:
```
circle area: 12.57
square area: 9.00
```

`Shape` permits exactly `Circle` and `Square` (both records, which are implicitly `final`, satisfying the requirement that every permitted subtype resolve its own continuation) — attempting to declare a third class implementing `Shape` anywhere in the codebase would be a compile error, since it isn't named in the `permits` clause.

### Level 2 — Intermediate

```java
public class SealedNestedHierarchy {
    sealed interface Shape permits Circle, Quadrilateral {}
    record Circle(double radius) implements Shape {}

    sealed interface Quadrilateral extends Shape permits Square, Rectangle {}
    record Square(double side) implements Quadrilateral {}
    record Rectangle(double width, double height) implements Quadrilateral {}

    static double area(Shape shape) {
        return switch (shape) {
            case Circle c -> Math.PI * c.radius() * c.radius();
            case Square s -> s.side() * s.side();
            case Rectangle r -> r.width() * r.height();
        }; // no default needed -- compiler verifies EVERY Shape variant is covered
    }

    public static void main(String[] args) {
        System.out.printf("circle: %.2f%n", area(new Circle(1.5)));
        System.out.printf("square: %.2f%n", area(new Square(4.0)));
        System.out.printf("rectangle: %.2f%n", area(new Rectangle(3.0, 5.0)));
    }
}
```

**How to run:** `java SealedNestedHierarchy.java` (JDK 17+).

Expected output:
```
circle: 4.71
square: 16.00
rectangle: 15.00
```

The real-world concern added: `Quadrilateral` is itself a sealed interface, nested within `Shape`'s own sealed hierarchy — permitting `Square` and `Rectangle` specifically — demonstrating that sealing composes across multiple levels; the `switch` in `area` covers all three ultimate concrete variants (`Circle`, `Square`, `Rectangle`) with no `default` branch, and the compiler genuinely verifies this exhaustiveness by walking the complete, closed hierarchy from `Shape` down through `Quadrilateral`.

### Level 3 — Advanced

```java
public class SealedEnforcement {
    sealed interface PaymentResult permits Success, Failure {}
    record Success(String transactionId, double amount) implements PaymentResult {}
    sealed interface Failure extends PaymentResult permits InsufficientFunds, CardDeclined {}
    record InsufficientFunds(double shortfall) implements Failure {}
    record CardDeclined(String reason) implements Failure {}

    // The following would be a COMPILE ERROR if uncommented, since PaymentResult's
    // permits clause does not include it:
    // record Timeout() implements PaymentResult {}

    static String describe(PaymentResult result) {
        return switch (result) {
            case Success(String id, double amount) -> "Success: " + id + " for $" + amount;
            case InsufficientFunds(double shortfall) -> "Failed: short by $" + shortfall;
            case CardDeclined(String reason) -> "Failed: card declined (" + reason + ")";
        };
    }

    public static void main(String[] args) {
        System.out.println(describe(new Success("tx-001", 49.99)));
        System.out.println(describe(new InsufficientFunds(10.50)));
        System.out.println(describe(new CardDeclined("expired")));
    }
}
```

**How to run:** `java SealedEnforcement.java` (JDK 17+; uncomment the `Timeout` record to see the actual compile error the sealed hierarchy produces).

Expected output:
```
Success: tx-001 for $49.99
Failed: short by $10.5
Failed: card declined (expired)
```

The production-flavored hard case: `PaymentResult`'s two-level sealed hierarchy (splitting `Failure` into its own further-sealed sub-hierarchy) models a realistic "closed set of outcomes" domain concept — a payment either succeeds or fails for one of exactly two reasons, and nothing else is possible by design; the commented-out `Timeout` record demonstrates concretely that attempting to add a fourth variant without updating the `permits` clauses is rejected by the compiler immediately, at the exact point of the illegal declaration, not discovered later as a missing `switch` case at runtime.

## 6. Walkthrough

Tracing the compiler's enforcement process when attempting to uncomment `record Timeout() implements PaymentResult {}` in `SealedEnforcement`:

1. The compiler encounters `record Timeout() implements PaymentResult`, and before accepting this declaration, it checks `PaymentResult`'s `permits` clause — which explicitly lists only `Success` and `Failure`.
2. `Timeout` is not named in that list, so the compiler rejects the declaration outright with a compile error (something like "class Timeout is not allowed to extend sealed interface PaymentResult: Timeout is not listed in its permits clause") — this rejection happens at the exact point of the illegal declaration, during compilation, well before the program could ever run.
3. This is the direct payoff of sealing: without `sealed`/`permits`, `PaymentResult` would be an ordinary, open interface, and `Timeout` could freely implement it — but then every existing `switch` over `PaymentResult` elsewhere in the codebase (like `describe`) would suddenly have an uncovered case, silently, with no compiler warning unless that `switch` happened to include a `default` branch that might handle it incorrectly, or not at all.
4. Because `PaymentResult` is sealed, the compiler instead catches this exact scenario at its true root cause — the moment a new variant is introduced — rather than at some later point where an exhaustiveness gap might only surface as an unhandled case at runtime, or as a compile error in a `switch` far away from where the actual new type was added.
5. If a fourth variant genuinely needs to be added to this hierarchy, the correct process is: add the new record, *and* update `PaymentResult`'s `permits` clause to include it — at which point every existing `switch` over `PaymentResult` (like `describe`) immediately becomes a compile error too, specifically flagging that it is no longer exhaustive, forcing every affected call site to be deliberately updated to handle the new case, rather than silently ignoring it.
6. This is precisely the safety net sealing is designed to provide: any change to the hierarchy's shape is guaranteed to be caught, at compile time, everywhere in the codebase that depends on that shape being complete — turning what would otherwise be a class of runtime bugs (an unhandled case reached only under specific, rare data) into an unmissable compile-time signal instead.

## 7. Gotchas & takeaways

> **Gotcha:** every class or interface named in a `permits` clause must be in the same module (or, for an unnamed module, the same package) as the sealed type itself — you cannot seal a type and then permit an implementer defined in some completely separate, unrelated module; this is a deliberate restriction ensuring the complete hierarchy is always knowable and verifiable from within a single compilation unit's accessible scope, not scattered unpredictably across independently-versioned modules.

- `sealed` with a `permits` clause restricts exactly which classes or interfaces may extend or implement a type — every permitted subtype must itself declare `final`, `sealed`, or `non-sealed`, explicitly stating whether the closure continues or is deliberately reopened.
- If every permitted subtype is declared in the same source file as the sealed type, the `permits` clause can be omitted, since the compiler can already see the complete set directly.
- Sealing composes across multiple levels — a permitted subtype can itself be `sealed` with its own further-restricted `permits` clause, building an arbitrarily deep but still fully closed hierarchy.
- The primary payoff of sealing is enabling compiler-verified exhaustiveness checking in `switch` expressions over the sealed type's variants, with no `default` branch required, and any hierarchy change immediately flagging every now-incomplete `switch` elsewhere in the codebase.
- Every class named in a `permits` clause must reside in the same module or package as the sealed type — sealing cannot span arbitrary, independently-compiled modules.
- See [non-sealed subclasses](0962-non-sealed-subclasses.md) for exactly what deliberately reopening a branch of a sealed hierarchy means and when it's the right choice, and [exhaustiveness in switch](0964-exhaustiveness-in-switch.md) for the compiler-verification payoff sealing directly enables.
