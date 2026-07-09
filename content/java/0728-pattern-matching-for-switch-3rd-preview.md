---
card: java
gi: 728
slug: pattern-matching-for-switch-3rd-preview
title: Pattern matching for switch (3rd preview)
---

## 1. What it is

**Java 19** (JEP 427) is the **third preview** of pattern matching for `switch`, and the release where it merges directly with the brand-new [record patterns](0727-record-patterns-preview.md) previewed in the same version. Type patterns, `case null`, and `when` guards (refined from `&&` to `when` in the [second preview](0720-pattern-matching-for-switch-2nd-preview.md)) all carry forward unchanged, but `switch` case labels can now *also* be record patterns — meaning a single `case` can simultaneously check a value's type, destructure it into its record components, and attach a `when` guard, all in one line. This third round is primarily a refinement and integration pass rather than a syntax redesign: it folds record patterns into the same `switch` machinery, and continues to require `--enable-preview` since the overall feature was still not finalized.

## 2. Why & when

By the time of this third preview, the two big pieces — type patterns with guards, and record deconstruction — had each gone through their own design iteration ([switch pattern matching](0704-pattern-matching-for-switch-preview.md) since Java 17, [record patterns](0727-record-patterns-preview.md) newly previewed in this same Java 19 release). The natural next step was making sure they compose cleanly: a `switch` case shouldn't have to choose between "match and bind a type" and "match and destructure a record" — it should be able to do both together, since record patterns *are* type patterns with structure attached. This matters concretely for exactly the kind of code that motivated pattern matching for `switch` in the first place: processing `sealed` hierarchies where the concrete cases are records. Instead of writing `case Line line -> { var start = line.start(); ... }`, a single case can write `case Line(Point start, Point end) when ... -> ...` and have the destructured components immediately available, with a guard condition evaluated against them, all as one declarative case label. Reach for this combination whenever a `switch` processes a `sealed` hierarchy of records and needs both type-based branching and access to the records' internal structure.

## 3. Core concept

```java
sealed interface Shape permits Circle, Rectangle {}
record Circle(Point center, double radius) implements Shape {}
record Rectangle(Point topLeft, Point bottomRight) implements Shape {}
record Point(int x, int y) {}

static String describe(Shape shape) {
    return switch (shape) {
        case Circle(Point(var x, var y), var r) when r <= 0 ->
                "invalid circle at (" + x + "," + y + ")";
        case Circle(Point(var x, var y), var r) ->
                "circle at (" + x + "," + y + "), radius " + r;
        case Rectangle(Point tl, Point br) ->
                "rectangle from " + tl + " to " + br;
    };
}
```

Type pattern, record destructuring, and `when` guard now compose in a single `case` label — no separate accessor calls, no nested `if`.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single switch case combines a type check, record destructuring into named variables, and an optional when guard, evaluated in that order before the case body runs">
  <rect x="20" y="30" width="600" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="55" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">case Circle(Point(var x, var y), var r) when r &lt;= 0 -&gt; ...</text>
  <text x="330" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">type check + destructure + guard, in one case label</text>

  <rect x="20" y="120" width="180" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="110" y="150" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">1. is it a Circle?</text>

  <rect x="230" y="120" width="180" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="320" y="150" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">2. destructure x, y, r</text>

  <rect x="440" y="120" width="180" height="50" rx="8" fill="#0f1620" stroke="#f0883e"/>
  <text x="530" y="150" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">3. r &lt;= 0 ?</text>

  <line x1="200" y1="145" x2="225" y2="145" stroke="#8b949e" stroke-width="2" marker-end="url(#a7)"/>
  <line x1="410" y1="145" x2="435" y2="145" stroke="#8b949e" stroke-width="2" marker-end="url(#a7)"/>

  <defs><marker id="a7" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The three checks always happen in this order: type, then destructure, then guard — the guard only runs once every earlier step already matched.

## 5. Runnable example

Scenario: evaluating a small arithmetic expression tree represented as a `sealed` hierarchy of records (`Const`, `Add`, `Mul`). It grows from basic recursive evaluation using record patterns in `switch`, to adding guarded cases that detect and simplify special values (`x * 0`, `x + 0`), to a version that also detects and reports division-related edge cases using nested guarded record patterns — the classic, realistic use case for this feature: interpreters and expression evaluators.

### Level 1 — Basic

```java
// File: ExprBasic.java
// Run with --enable-preview: pattern matching for switch is a 3rd preview
// feature in Java 19, here combined with record patterns (1st preview).
public class ExprBasic {
    sealed interface Expr permits Const, Add, Mul {}
    record Const(int value) implements Expr {}
    record Add(Expr left, Expr right) implements Expr {}
    record Mul(Expr left, Expr right) implements Expr {}

    static int eval(Expr expr) {
        return switch (expr) {
            case Const(var value) -> value;
            case Add(var left, var right) -> eval(left) + eval(right);
            case Mul(var left, var right) -> eval(left) * eval(right);
        };
    }

    public static void main(String[] args) {
        Expr expr = new Add(new Const(2), new Mul(new Const(3), new Const(4)));
        System.out.println("2 + 3 * 4 = " + eval(expr));
    }
}
```

**How to run:**
```
javac --release 19 --enable-preview ExprBasic.java
java --enable-preview ExprBasic
```

Expected output:
```
2 + 3 * 4 = 14
```

### Level 2 — Intermediate

```java
// File: ExprSimplifyIntermediate.java
// Adds a simplify() function using guarded record patterns to detect
// algebraic identities (x*0=0, x*1=x, x+0=x) before falling back to
// rebuilding the node unchanged.
public class ExprSimplifyIntermediate {
    sealed interface Expr permits Const, Add, Mul {}
    record Const(int value) implements Expr {}
    record Add(Expr left, Expr right) implements Expr {}
    record Mul(Expr left, Expr right) implements Expr {}

    static Expr simplify(Expr expr) {
        return switch (expr) {
            case Mul(Const(var v), Expr r) when v == 0 -> new Const(0);
            case Mul(Expr l, Const(var v)) when v == 0 -> new Const(0);
            case Mul(Const(var v), Expr r) when v == 1 -> simplify(r);
            case Mul(Expr l, Const(var v)) when v == 1 -> simplify(l);
            case Add(Const(var v), Expr r) when v == 0 -> simplify(r);
            case Add(Expr l, Const(var v)) when v == 0 -> simplify(l);
            case Add(Expr l, Expr r) -> new Add(simplify(l), simplify(r));
            case Mul(Expr l, Expr r) -> new Mul(simplify(l), simplify(r));
            case Const c -> c;
        };
    }

    static int eval(Expr expr) {
        return switch (expr) {
            case Const(var value) -> value;
            case Add(var left, var right) -> eval(left) + eval(right);
            case Mul(var left, var right) -> eval(left) * eval(right);
        };
    }

    public static void main(String[] args) {
        Expr expr = new Add(new Mul(new Const(5), new Const(0)), new Mul(new Const(7), new Const(1)));
        Expr simplified = simplify(expr);
        System.out.println("Original evaluates to: " + eval(expr));
        System.out.println("Simplified evaluates to: " + eval(simplified));
        System.out.println("Simplified tree: " + simplified);
    }
}
```

**How to run:**
```
javac --release 19 --enable-preview ExprSimplifyIntermediate.java
java --enable-preview ExprSimplifyIntermediate
```

Expected output:
```
Original evaluates to: 7
Simplified evaluates to: 7
Simplified tree: Const[value=7]
```

### Level 3 — Advanced

```java
// File: ExprDivAdvanced.java
// Adds a Div node and detects division-by-zero and division-by-constant-one
// via nested guarded record patterns, returning a Result-like sealed type
// instead of throwing — the production-flavored shape of a safe evaluator.
public class ExprDivAdvanced {
    sealed interface Expr permits Const, Add, Mul, Div {}
    record Const(int value) implements Expr {}
    record Add(Expr left, Expr right) implements Expr {}
    record Mul(Expr left, Expr right) implements Expr {}
    record Div(Expr numerator, Expr denominator) implements Expr {}

    sealed interface Result permits Ok, Err {}
    record Ok(int value) implements Result {}
    record Err(String message) implements Result {}

    static Result eval(Expr expr) {
        return switch (expr) {
            case Const(var value) -> new Ok(value);
            case Add(var left, var right) -> combine(left, right, Integer::sum);
            case Mul(var left, var right) -> combine(left, right, (a, b) -> a * b);
            case Div(var num, Div(var innerNum, Const(var zero))) when zero == 0 ->
                    new Err("nested division by zero detected before evaluating numerator");
            case Div(var num, Const(var denom)) when denom == 0 ->
                    new Err("division by zero");
            case Div(var num, var denom) -> combine(num, denom, (a, b) -> a / b);
        };
    }

    static Result combine(Expr left, Expr right, java.util.function.IntBinaryOperator op) {
        Result l = eval(left);
        Result r = eval(right);
        if (l instanceof Err) return l;
        if (r instanceof Err) return r;
        return new Ok(op.applyAsInt(((Ok) l).value(), ((Ok) r).value()));
    }

    public static void main(String[] args) {
        Expr safe = new Div(new Const(10), new Const(2));
        Expr unsafe = new Div(new Const(10), new Const(0));

        System.out.println(describe(eval(safe)));
        System.out.println(describe(eval(unsafe)));
    }

    static String describe(Result r) {
        return switch (r) {
            case Ok(var value) -> "Result: " + value;
            case Err(var message) -> "Error: " + message;
        };
    }
}
```

**How to run:**
```
javac --release 19 --enable-preview ExprDivAdvanced.java
java --enable-preview ExprDivAdvanced
```

Expected output:
```
Result: 5
Error: division by zero
```

## 6. Walkthrough

1. `ExprDivAdvanced.main` builds two expression trees, `safe` (`10 / 2`) and `unsafe` (`10 / 0`), and evaluates each through `eval`, then formats the resulting `Result` through `describe`.
2. `eval(safe)` enters `switch (expr)` with a `Div(Const(10), Const(2))`. The first `case`, `Div(var num, Div(var innerNum, Const(var zero))) when zero == 0`, requires the *denominator itself* to be another `Div` whose own denominator is a zero `Const` — here the denominator is `Const(2)`, not a `Div` at all, so this nested type check fails immediately and the case is skipped without ever evaluating anything.
3. The second case, `Div(var num, Const(var denom)) when denom == 0`, matches the type (denominator is a `Const`) and destructures `denom = 2`, but the guard `denom == 0` is `false`, so it also falls through.
4. The third, unguarded `Div(var num, var denom)` case matches unconditionally at this point, and calls `combine(num, denom, (a, b) -> a / b)`, which recursively evaluates both sides (`10` and `2`) and divides them, producing `Ok(5)`.
5. `eval(unsafe)` follows the same first two steps, but this time the second case's guard `denom == 0` is `true` (the denominator is `Const(0)`), so evaluation short-circuits immediately, returning `Err("division by zero")` — the recursive `combine` call is never reached, and no actual `a / b` integer division (which would throw `ArithmeticException`) ever executes.
6. `describe` runs its own `switch` on the resulting `Result`: `case Ok(var value)` destructures the wrapped integer directly for the success message, and `case Err(var message)` destructures the wrapped string directly for the failure message — both via record patterns on the `sealed Result` hierarchy, mirroring the pattern used for `Expr` itself.
7. The first, more specific "nested division by zero" case exists to illustrate that record patterns can inspect **structure several levels deep** as part of a single `case`'s type check — in a fuller interpreter, this specific case might apply a different error message or transformation for a denominator that is itself a zero-dividing expression, distinct from a denominator that is a plain zero constant, without needing a nested `if` inside the case body to tell the two situations apart.

```
eval(Div(Const(10), Const(0)))
   |
   v
case Div(num, Div(innerNum, Const(zero))) when zero==0?
   -> denominator is Const(0), NOT a Div -> type mismatch -> skip
   |
   v
case Div(num, Const(denom)) when denom==0?
   -> denominator IS Const(0) -> destructure denom=0 -> guard TRUE
   |
   v
Err("division by zero")   [STOP — combine() never called, no real division attempted]
```

## 7. Gotchas & takeaways

> This is a **preview feature in Java 19** (third preview of switch pattern matching, combined with the first preview of record patterns) — both require `--enable-preview`, and this combination's exact interaction rules continued to be refined before joint finalization in a later JDK; treat this release's syntax as representative but not permanently fixed.
- Case order matters even more with nested guarded record patterns: put the more specific structural/guarded cases **before** the general unguarded case for the same outer type, exactly as with simple type-pattern guards — the compiler does not reorder cases for you.
- A guard (`when ...`) can only reference variables already bound by the pattern it's attached to (or the enclosing scope) — it runs strictly after the pattern's destructuring succeeds, never before, so it's safe to use destructured components inside the guard expression itself, as `denom == 0` does here.
- Combining record patterns with `sealed` interfaces on both `Expr` and `Result` (Level 3) gives the compiler two independent exhaustiveness guarantees: every `Expr` case is handled in `eval`, and every `Result` case is handled in `describe` — removing an `Add`, `Mul`, `Div`, `Ok`, or `Err` variant, or forgetting to handle one, is a compile error, not a runtime surprise.
- This third preview's main lesson is architectural, not syntactic: representing a recursive domain (expression trees, JSON, ASTs) as a `sealed` hierarchy of records, then processing it entirely through pattern-matching `switch` with nested record patterns, tends to eliminate almost all manual casting, accessor chains, and `instanceof` boilerplate that the same logic would otherwise require.
