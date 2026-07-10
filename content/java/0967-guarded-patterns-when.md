---
card: java
gi: 967
slug: guarded-patterns-when
title: "Guarded patterns (when)"
---

## 1. What it is

A guarded pattern adds an extra boolean condition to a `switch` case label, using the `when` keyword: `case Integer i when i < 0 -> "negative"` matches only if the value is both an `Integer` *and* satisfies the additional condition, `i < 0`. Without `when`, a pattern's case label can only express "is this value this specific type (and shape, for record patterns)" — `when` lets you layer an arbitrary boolean expression on top, referencing the pattern's own bound variables, to further refine exactly which values that case should actually handle, without needing a separate `if` statement inside the case's body (which, notably, would also break the compiler's ability to reason about that case as fully "handling" its matched type for exhaustiveness purposes in certain situations).

## 2. Why & when

Guarded patterns matter whenever a single type isn't a fine enough distinction for your logic — you don't just want "is this an `Integer`," you want "is this an `Integer` that's negative," and you want a *different*, later case to still be able to catch "any other `Integer`" as its own, separate, unconditional branch. Before `when`, this required either nesting an `if` inside the case body (losing the flat, declarative one-condition-per-case readability `switch` is meant to provide) or restructuring the type hierarchy itself to encode the distinction as a separate type (often infeasible or overly heavy-handed for a simple numeric or string condition). It's especially valuable combined with record patterns: `case Point(int x, int y) when x == y -> "on the diagonal"` expresses a shape-plus-value condition in one readable line, exactly the kind of refined matching real domain logic (validating ranges, categorizing values, handling edge cases specially) frequently needs.

## 3. Core concept

```
switch (obj) {
    case Integer i when i < 0 -> "negative integer";     // GUARDED: type + extra condition
    case Integer i when i == 0 -> "zero";                 // GUARDED: a DIFFERENT condition, same type
    case Integer i -> "positive integer";                 // UNGUARDED: catches any remaining Integer
    default -> "not an integer";
}
```

Guards are checked *after* the type/shape match succeeds, and cases are still evaluated top to bottom — if a guard's condition is false, the `switch` moves on to try the *next* case, even if that next case matches the exact same type, letting you express a genuine priority-ordered sequence of type-plus-condition refinements.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three case labels all matching Integer, distinguished by guard conditions checked in order: negative, zero, and an unguarded catch-all for anything else" >
  <rect x="20" y="30" width="180" height="40" fill="#1c2430" stroke="#f0883e"/>
  <text x="110" y="49" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">Integer i when i &lt; 0</text>
  <text x="110" y="63" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">match type, THEN check guard</text>

  <rect x="230" y="30" width="180" height="40" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="49" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Integer i when i == 0</text>
  <text x="320" y="63" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">tried if guard #1 was false</text>

  <rect x="440" y="30" width="180" height="40" fill="#1c2430" stroke="#6db33f"/>
  <text x="530" y="49" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Integer i (no guard)</text>
  <text x="530" y="63" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">catches ANY remaining Integer</text>

  <line x1="200" y1="50" x2="230" y2="50" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="410" y1="50" x2="440" y2="50" stroke="#8b949e" marker-end="url(#a)"/>

  <text x="320" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Guards checked in DECLARATION order -- a failed guard falls through to the NEXT case,</text>
  <text x="320" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">even if that next case matches the exact same underlying type</text>
</svg>

*Guarded cases are tried in declaration order; a failed guard moves on to the next case, even one matching the same type.*

## 5. Runnable example

Scenario: build a small grade-categorization function using guarded patterns, evolving from a basic numeric-range guard, to a realistic combination of type patterns and guards over mixed input, to a more advanced case combining a guarded record pattern for a genuinely shape-plus-value condition.

### Level 1 — Basic

```java
public class GuardedPatternBasic {
    static String categorize(int score) {
        return switch ((Integer) score) {
            case Integer s when s >= 90 -> "A";
            case Integer s when s >= 80 -> "B";
            case Integer s when s >= 70 -> "C";
            case Integer s -> "F";
        };
    }

    public static void main(String[] args) {
        for (int score : new int[]{95, 82, 71, 40}) {
            System.out.println(score + " -> " + categorize(score));
        }
    }
}
```

**How to run:** `java GuardedPatternBasic.java` (JDK 21+; guarded patterns require Java 21+).

Expected output:
```
95 -> A
82 -> B
71 -> C
40 -> F
```

Each guarded case checks a progressively lower threshold, evaluated top to bottom — for `82`, the first guard (`s >= 90`) fails, so the `switch` proceeds to the second (`s >= 80`), which succeeds, producing `"B"`; the final, unguarded `case Integer s` acts as the catch-all for anything not matching any preceding guard.

### Level 2 — Intermediate

```java
public class GuardedPatternMixedTypes {
    static String validate(Object input) {
        return switch (input) {
            case null -> "input is null";
            case String s when s.isBlank() -> "blank string";
            case String s when s.length() > 100 -> "string too long";
            case String s -> "valid string: " + s;
            case Integer i when i < 0 -> "negative number not allowed";
            case Integer i -> "valid number: " + i;
            default -> "unsupported input type";
        };
    }

    public static void main(String[] args) {
        System.out.println(validate("hello"));
        System.out.println(validate("   "));
        System.out.println(validate(-5));
        System.out.println(validate(42));
        System.out.println(validate(null));
    }
}
```

**How to run:** `java GuardedPatternMixedTypes.java` (JDK 21+).

Expected output:
```
valid string: hello
blank string
negative number not allowed
valid number: 42
input is null
```

The real-world concern added: combining `null` handling, type patterns, and guards on multiple different types in one `switch` expresses a complete validation specification in one readable, linear sequence — each guarded case narrows down exactly which strings or integers are "invalid" for a specific reason, while the unguarded fallback cases (`case String s`, `case Integer i`) catch everything that passed all the preceding, more specific guards.

### Level 3 — Advanced

```java
public class GuardedRecordPattern {
    record Point(int x, int y) {}

    static String classify(Object obj) {
        return switch (obj) {
            case Point(int x, int y) when x == 0 && y == 0 -> "origin";
            case Point(int x, int y) when x == y -> "on the main diagonal";
            case Point(int x, int y) when x == -y -> "on the anti-diagonal";
            case Point(int x, int y) when x == 0 -> "on the y-axis";
            case Point(int x, int y) when y == 0 -> "on the x-axis";
            case Point p -> "general point: (" + p.x() + ", " + p.y() + ")";
            default -> "not a point";
        };
    }

    public static void main(String[] args) {
        System.out.println(classify(new Point(0, 0)));
        System.out.println(classify(new Point(3, 3)));
        System.out.println(classify(new Point(4, -4)));
        System.out.println(classify(new Point(0, 5)));
        System.out.println(classify(new Point(2, 7)));
    }
}
```

**How to run:** `java GuardedRecordPattern.java` (JDK 21+).

Expected output:
```
origin
on the main diagonal
on the anti-diagonal
on the y-axis
general point: (2, 7)
```

The production-flavored hard case: each case combines a record pattern's destructuring (`Point(int x, int y)`) with a guard condition referencing the just-bound `x` and `y` variables directly — expressing several genuinely distinct geometric classifications, each checked in a deliberate priority order (origin first, since it satisfies several of the later conditions too, would otherwise be miscategorized if checked after the diagonal cases), demonstrating that guard conditions can reference pattern-bound variables from record deconstruction just as naturally as from a simple type pattern.

## 6. Walkthrough

Tracing `classify(new Point(0, 0))` end to end from `GuardedRecordPattern.main`:

1. `classify` is called with a `Point(0, 0)` instance — the `switch`'s first case, `case Point(int x, int y) when x == 0 && y == 0`, first checks the record pattern's shape: is `obj` a `Point`? It is, so it destructures, binding `x = 0` and `y = 0`.
2. With the pattern successfully matched and its variables bound, the guard condition `x == 0 && y == 0` is evaluated: both are true, so the entire guard evaluates to `true`, and this case is selected — the `switch` immediately returns `"origin"`, without ever evaluating any of the later case labels.
3. Consider, by contrast, why the case order matters here: if `case Point(int x, int y) when x == y` had been placed *before* the origin check, `Point(0, 0)` would have matched that case instead (since `0 == 0` is also true for the diagonal condition), incorrectly reporting "on the main diagonal" instead of the more specific, intended "origin" — this is precisely why the origin case, being the most specific single-point match, is deliberately checked first.
4. Tracing a different call, `classify(new Point(4, -4))`: the origin guard (`x == 0 && y == 0`) fails, since neither `x` nor `y` is `0`; the diagonal guard (`x == y`) fails too, since `4 != -4`; the anti-diagonal guard (`x == -y`) is checked next and succeeds, since `4 == -(-4) = 4`, so this case matches and `"on the anti-diagonal"` is returned.
5. For `classify(new Point(2, 7))`, every guarded case's condition fails in turn (it's not the origin, not on either diagonal, and neither coordinate is zero), so the `switch` falls through to the final guarded cases and, finding none of them match either, reaches the unguarded `case Point p`, which matches unconditionally for any remaining `Point` — producing `"general point: (2, 7)"`.
6. This demonstrates the complete guard-evaluation process: for each case in declaration order, the pattern's shape is checked first, and only if that succeeds is the `when` condition evaluated; a failed guard (at either the shape or the condition level) moves on to try the next case entirely, continuing until some case matches unconditionally or a `default` is reached, giving you a natural way to express an ordered sequence of increasingly general fallback conditions.

## 7. Gotchas & takeaways

> **Gotcha:** because a guard is evaluated *after* the type/shape match succeeds, a `switch` with only guarded cases for a given type (and no final unguarded case for that same type) is *not* considered exhaustive by the compiler, even over a sealed hierarchy — the compiler cannot statically prove a boolean guard expression will cover every possible value, so it requires either an unguarded fallback case for that type or an explicit `default` to compile as a `switch` expression; always include an unconditional case (or `default`) as the final safety net whenever any earlier case for that same type is guarded.

- A guarded pattern (`case Type var when condition ->`) adds an extra boolean condition on top of a type or record pattern's match, letting one `switch` express several distinct refinements of the same underlying type.
- Guards are evaluated in declaration order, after the pattern's shape has already matched — a failed guard moves on to try the next case, even one matching the exact same type.
- Guard conditions can reference variables bound by the pattern itself, including components destructured from a record pattern, letting you express shape-plus-value conditions in a single, readable case label.
- Case ordering matters critically with guards, exactly as it does with overlapping type patterns — a more specific condition must be checked before a more general one that would otherwise also match the same values.
- A `switch` with only guarded cases for a given type is never considered exhaustive by the compiler on its own — an unguarded fallback case (or `default`) is always required as the final safety net.
- See [switch type patterns](0966-switch-type-patterns.md) for the underlying type-pattern mechanism guards refine, and [record deconstruction patterns](0968-record-deconstruction-patterns.md) for more on the destructuring guards frequently combine with.
