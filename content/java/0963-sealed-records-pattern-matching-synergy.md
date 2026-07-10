---
card: java
gi: 963
slug: sealed-records-pattern-matching-synergy
title: Sealed + records + pattern matching synergy
---

## 1. What it is

Sealed types, records, and pattern matching are three separate Java features that were deliberately designed to work together as a single, coherent style for modeling "algebraic data types" — a fixed, closed set of variants, each carrying its own specific data, processed through exhaustively-checked dispatch. [Sealed types](0961-sealed-permits-clauses.md) supply the closed, enumerable set of variants; [records](0954-record-components-canonical-constructor.md) supply each variant's data as a plain, transparent, immutable carrier with automatic accessors and destructuring support; and [pattern matching](0960-record-patterns-deconstruction.md) (specifically `switch` with record patterns) supplies the exhaustive, type-safe, self-destructuring dispatch mechanism that ties the other two together. None of the three pieces alone gives you the complete picture: sealing without records still requires manual accessor calls after each `instanceof`; records without sealing lose compiler-verified exhaustiveness (nothing stops a rogue extra variant from silently going unhandled); and pattern matching without either still works, but has nothing structurally closed and self-describing to match against.

## 2. Why & when

This combination is the idiomatic modern replacement for a whole family of design patterns Java developers historically reached for out of necessity rather than preference — the Visitor pattern (an elaborate double-dispatch mechanism built specifically to work around the lack of exhaustive type-based dispatch), a `type` tag field plus a manual `switch` on it (with no compiler-enforced correspondence between the tag and the actual runtime type, and no protection against a forgotten case), or a hierarchy of classes each implementing an abstract method (workable, but requiring every operation to be baked into the type hierarchy itself, rather than expressed as an external, freely-added function operating on the closed set of variants). Reach for this combination whenever you're modeling a genuinely closed set of "kinds of thing" — an arithmetic expression tree (literal, addition, multiplication), an HTTP response outcome (success, client error, server error), a parsed command — where you want to add *new operations* over these variants easily (as ordinary methods or functions using `switch`) without needing to touch the variant types themselves each time, which is exactly the flexibility the Visitor pattern existed to provide, now achieved far more simply.

## 3. Core concept

```
sealed interface Expr permits Literal, Add, Multiply {}
record Literal(double value) implements Expr {}
record Add(Expr left, Expr right) implements Expr {}
record Multiply(Expr left, Expr right) implements Expr {}

// ONE operation, expressed as an ordinary function -- no changes needed to Expr itself:
static double evaluate(Expr expr) {
    return switch (expr) {
        case Literal(double v) -> v;
        case Add(Expr l, Expr r) -> evaluate(l) + evaluate(r);
        case Multiply(Expr l, Expr r) -> evaluate(l) * evaluate(r);
    }; // EXHAUSTIVE, checked by the compiler -- no default needed
}

// ANOTHER operation, added later, with ZERO changes to Expr, Literal, Add, or Multiply:
static String render(Expr expr) {
    return switch (expr) {
        case Literal(double v) -> String.valueOf(v);
        case Add(Expr l, Expr r) -> "(" + render(l) + " + " + render(r) + ")";
        case Multiply(Expr l, Expr r) -> "(" + render(l) + " * " + render(r) + ")";
    };
}
```

Adding a brand-new operation over the closed `Expr` hierarchy requires writing exactly one new function, with the compiler itself verifying every variant is handled — no visitor interface, no double dispatch, no modification to any of the existing variant types.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A sealed Expr hierarchy with three record variants, and two independent operations, evaluate and render, each implemented as a single exhaustive switch requiring no changes to the variant types themselves" >
  <rect x="20" y="20" width="600" height="50" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">sealed interface Expr permits Literal, Add, Multiply</text>
  <text x="320" y="58" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">three record variants -- fixed, closed, self-destructuring</text>

  <rect x="60" y="100" width="220" height="60" fill="#1c2430" stroke="#79c0ff"/>
  <text x="170" y="120" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">evaluate(Expr) -- switch</text>
  <text x="170" y="140" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">handles all 3 variants</text>
  <text x="170" y="152" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">compiler-verified exhaustive</text>

  <rect x="360" y="100" width="220" height="60" fill="#1c2430" stroke="#f0883e"/>
  <text x="470" y="120" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">render(Expr) -- switch</text>
  <text x="470" y="140" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">ALSO handles all 3 variants</text>
  <text x="470" y="152" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">added later, zero changes to Expr</text>
</svg>

*New operations are added as ordinary functions, each independently exhaustive-checked, with no modification to the closed variant hierarchy itself.*

## 5. Runnable example

Scenario: model a small arithmetic expression evaluator and demonstrate exactly the "add new operations without touching existing types" flexibility this combination provides — starting with a basic two-variant expression tree and one operation, then adding a third variant and updating both operations, then adding an entirely new third operation with zero changes to any variant type.

### Level 1 — Basic

```java
public class SealedRecordSynergyBasic {
    sealed interface Expr permits Literal, Add {}
    record Literal(double value) implements Expr {}
    record Add(Expr left, Expr right) implements Expr {}

    static double evaluate(Expr expr) {
        return switch (expr) {
            case Literal(double v) -> v;
            case Add(Expr l, Expr r) -> evaluate(l) + evaluate(r);
        };
    }

    public static void main(String[] args) {
        Expr expr = new Add(new Literal(3), new Add(new Literal(4), new Literal(5)));
        System.out.println("result: " + evaluate(expr));
    }
}
```

**How to run:** `java SealedRecordSynergyBasic.java` (JDK 21+; record patterns in switch require Java 21+).

Expected output:
```
result: 12.0
```

`Expr` is sealed to exactly `Literal` and `Add`; `evaluate` deconstructs each variant directly in its `switch` cases and recurses for nested `Add` expressions — `3 + (4 + 5) = 12.0` — with the compiler verifying both variants are handled, no `default` needed.

### Level 2 — Intermediate

```java
public class SealedRecordSynergyExtended {
    sealed interface Expr permits Literal, Add, Multiply {}
    record Literal(double value) implements Expr {}
    record Add(Expr left, Expr right) implements Expr {}
    record Multiply(Expr left, Expr right) implements Expr {} // NEW variant added

    static double evaluate(Expr expr) {
        return switch (expr) {
            case Literal(double v) -> v;
            case Add(Expr l, Expr r) -> evaluate(l) + evaluate(r);
            case Multiply(Expr l, Expr r) -> evaluate(l) * evaluate(r); // updated to handle it
        };
    }

    static String render(Expr expr) {
        return switch (expr) {
            case Literal(double v) -> String.valueOf(v);
            case Add(Expr l, Expr r) -> "(" + render(l) + " + " + render(r) + ")";
            case Multiply(Expr l, Expr r) -> "(" + render(l) + " * " + render(r) + ")";
        };
    }

    public static void main(String[] args) {
        Expr expr = new Multiply(new Add(new Literal(2), new Literal(3)), new Literal(4));
        System.out.println(render(expr) + " = " + evaluate(expr));
    }
}
```

**How to run:** `java SealedRecordSynergyExtended.java` (JDK 21+).

Expected output:
```
(2.0 + 3.0) * 4.0 = 20.0
```

The real-world concern added: adding `Multiply` as a new variant requires updating `Expr`'s `permits` clause *and* updating both existing operations (`evaluate` and `render`) — but critically, the compiler forces this update by making both `switch` expressions fail to compile (as non-exhaustive) the instant `Multiply` is added and not yet handled, guaranteeing you cannot forget to update an operation when the variant set changes.

### Level 3 — Advanced

```java
public class SealedRecordSynergyNewOperation {
    sealed interface Expr permits Literal, Add, Multiply {}
    record Literal(double value) implements Expr {}
    record Add(Expr left, Expr right) implements Expr {}
    record Multiply(Expr left, Expr right) implements Expr {}

    static double evaluate(Expr expr) {
        return switch (expr) {
            case Literal(double v) -> v;
            case Add(Expr l, Expr r) -> evaluate(l) + evaluate(r);
            case Multiply(Expr l, Expr r) -> evaluate(l) * evaluate(r);
        };
    }

    // ENTIRELY NEW operation -- counts how many Literal nodes appear in the tree.
    // ZERO changes needed to Expr, Literal, Add, or Multiply to add this.
    static int countLiterals(Expr expr) {
        return switch (expr) {
            case Literal l -> 1;
            case Add(Expr l, Expr r) -> countLiterals(l) + countLiterals(r);
            case Multiply(Expr l, Expr r) -> countLiterals(l) + countLiterals(r);
        };
    }

    public static void main(String[] args) {
        Expr expr = new Multiply(new Add(new Literal(2), new Literal(3)), new Add(new Literal(4), new Literal(1)));
        System.out.println("value: " + evaluate(expr));
        System.out.println("literal count: " + countLiterals(expr));
    }
}
```

**How to run:** `java SealedRecordSynergyNewOperation.java` (JDK 21+).

Expected output:
```
value: 30.0
literal count: 4
```

The production-flavored hard case: `countLiterals` is a brand-new operation over the exact same `Expr` hierarchy, added purely as an ordinary static method — no interface to implement, no existing type to modify, no double-dispatch mechanism to wire up — and the compiler independently verifies *this* new `switch` is also exhaustive over all three variants; this is precisely the flexibility advantage this combination has over a classic Visitor-pattern or abstract-method-per-operation design, where adding a new operation would otherwise require touching every single variant class.

## 6. Walkthrough

Tracing `countLiterals(expr)` end to end from `SealedRecordSynergyNewOperation.main`, where `expr = Multiply(Add(Literal(2), Literal(3)), Add(Literal(4), Literal(1)))`:

1. `countLiterals` is called on the outer `Multiply` node — the `switch` checks its cases in order; `case Literal l` fails (it's not a `Literal`), so it proceeds to `case Add(...)`, which also fails, until it reaches `case Multiply(Expr l, Expr r)`, which matches and destructures the `Multiply` into its `left` and `right` sub-expressions.
2. This case's body, `countLiterals(l) + countLiterals(r)`, recursively calls `countLiterals` on the left sub-expression, `Add(Literal(2), Literal(3))`.
3. That recursive call's `switch` matches `case Add(Expr l, Expr r)`, destructuring into `Literal(2)` and `Literal(3)`, and again recurses: `countLiterals(Literal(2))` matches `case Literal l`, returning `1`; `countLiterals(Literal(3))` likewise returns `1`; their sum, `2`, is returned as the count for the entire left `Add` sub-expression.
4. Back in the outer `Multiply` call, the same process now runs for the right sub-expression, `Add(Literal(4), Literal(1))` — following the identical recursive pattern, this also resolves to `1 + 1 = 2`.
5. The outer `Multiply` case's body sums these two sub-results: `2 (from the left Add) + 2 (from the right Add) = 4`, which is the final count of `Literal` nodes across the entire tree.
6. `main` prints `literal count: 4`, confirming the correct count across all four leaf `Literal` nodes in the tree — and critically, this entire new operation was written without touching `Expr`, `Literal`, `Add`, or `Multiply` at all, demonstrating the exact "add operations freely, without modifying the closed variant hierarchy" flexibility that sealed types, records, and pattern matching together are specifically designed to provide.

## 7. Gotchas & takeaways

> **Gotcha:** this combination optimizes specifically for "adding new *operations* over a fixed set of variants is easy; adding a new *variant* requires touching every existing operation" — this is the exact inverse tradeoff of a classic object-oriented design (where each variant is a class implementing an abstract method per operation, making new variants easy to add but new operations require touching every class); choose sealed+records+pattern-matching when your domain's variant set is genuinely more stable than its operation set, and prefer the classic OO approach when the reverse is true.

- Sealed types provide the closed, enumerable variant set; records provide each variant's transparent, self-destructuring data; pattern matching (`switch` with record patterns) ties them together with exhaustive, type-safe dispatch — together replacing the classic Visitor pattern and tag-plus-switch approaches.
- Adding a new operation over an existing sealed hierarchy requires writing exactly one new function using an exhaustive `switch` — no changes needed to any of the variant types themselves.
- Adding a new variant to the hierarchy requires updating the `permits` clause and every existing `switch`-based operation — but the compiler enforces this by making every affected `switch` fail to compile until updated, guaranteeing nothing is silently missed.
- This combination is the inverse tradeoff of classic per-variant abstract-method polymorphism: variants are hard to add (every operation must be updated), but operations are easy to add (a single new function, with no changes to existing types).
- Choose this style specifically when your domain's set of "kinds of thing" is meant to be fixed and stable, while the set of operations performed over them is expected to keep growing.
- See [sealed / permits clauses](0961-sealed-permits-clauses.md), [record components & canonical constructor](0954-record-components-canonical-constructor.md), and [record patterns / deconstruction](0960-record-patterns-deconstruction.md) for each individual piece of this combination in isolation.
