---
card: java
gi: 666
slug: yield-in-switch
title: yield in switch
---

## 1. What it is

`yield`, finalized alongside switch expressions in **Java 14**, is the statement that produces a value from a switch expression's arm. What's easy to miss is that `yield` isn't tied exclusively to the arrow (`->`) syntax — it also works inside the **classic colon-labeled** form when that `switch` is being used as an expression. `int x = switch (day) { case MONDAY: yield 1; default: yield 0; };` is entirely legal: colon labels, but the whole construct is still an expression because `yield` (not a bare statement) supplies the value, and no `break` is needed since `yield` itself exits the arm. This means there are, in total, four combinations to be aware of: colon-statement (needs `break`, no value), arrow-statement (no fall-through, no value, no `yield`), colon-expression (`yield` required per arm, no fall-through once `yield` runs), and arrow-expression (`yield` in block arms, direct value in expression arms).

## 2. Why & when

Understanding `yield` as a general "produce this switch expression's value" mechanism — independent of which label style you chose — clarifies a lot of otherwise-confusing corner cases, especially when reading code that mixes an older colon-based style with expression usage, or when migrating existing colon-labeled switch statements into switch expressions without also wanting to rewrite every label to use arrows. You'd choose `yield` inside colon-labeled arms specifically when you're converting a switch that already relies on colon-style multi-case fall-through-into-shared-code patterns (`case A: case B: yield sharedValue();`) into an expression, without rewriting to the arrow style. In practice, most new code uses arrow arms specifically to get the fall-through safety in addition to the expression value, but recognizing colon-based `yield` is essential for reading and maintaining any codebase using it.

## 3. Core concept

```java
// yield with ARROW labels: single expression arms need no yield,
// only block { } arms do.
int a = switch (x) {
    case 1 -> 10;                 // no yield — direct expression value
    case 2 -> { yield 20; }       // yield required inside a block
    default -> 0;
};

// yield with COLON labels: every reachable path must yield (or throw).
// Multiple colon labels can still share fall-through-style grouping.
int b = switch (x) {
    case 1:
    case 2:
        yield 100;   // shared by both case 1 and case 2, like old fall-through
    default:
        yield 0;
};
```

In the colon-labeled expression form, `case 1: case 2: yield 100;` behaves like the old fall-through idiom (both labels lead to the same code), but it's now explicit and controlled by `yield`, not an accidentally-omitted `break`.

## 4. Diagram

<svg viewBox="0 0 620 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four combinations of switch: colon or arrow labels, crossed with statement or expression usage, and where yield applies">
  <rect x="10" y="10" width="600" height="30" fill="#1c2430"/>
  <text x="150" y="30" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">colon labels (:)</text>
  <text x="470" y="30" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">arrow labels (->)</text>

  <rect x="10" y="45" width="290" height="70" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="155" y="65" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">STATEMENT: needs break,</text>
  <text x="155" y="80" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">no yield, falls through</text>
  <text x="155" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">the classic, bug-prone form</text>

  <rect x="320" y="45" width="290" height="70" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="65" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">STATEMENT: no fall-through,</text>
  <text x="465" y="80" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">no yield needed or allowed</text>
  <text x="465" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">safe control flow, no value</text>

  <rect x="10" y="125" width="290" height="65" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="155" y="145" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">EXPRESSION: yield required</text>
  <text x="155" y="160" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">on every reachable path</text>
  <text x="155" y="178" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">rarer, but legal and explicit</text>

  <rect x="320" y="125" width="290" height="65" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="465" y="145" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">EXPRESSION: yield in { }</text>
  <text x="465" y="160" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">arms; direct value otherwise</text>
  <text x="465" y="178" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">the common, idiomatic form</text>
</svg>

`yield` matters only in the two "EXPRESSION" quadrants — whether those quadrants use colon or arrow labels is a separate, orthogonal choice.

## 5. Runnable example

Scenario: computing a shipping cost multiplier from a package size category — first the idiomatic arrow-expression form, then the same logic rewritten with colon labels and `yield` to show the equivalence, then a version demonstrating grouped colon labels sharing one `yield`, mirroring old-style fall-through but made explicit and safe.

### Level 1 — Basic

```java
// File: MultiplierArrow.java
public class MultiplierArrow {
    enum Size { SMALL, MEDIUM, LARGE, OVERSIZED }

    static double multiplier(Size size) {
        return switch (size) {
            case SMALL -> 1.0;
            case MEDIUM -> 1.5;
            case LARGE -> 2.0;
            case OVERSIZED -> {
                System.out.println("  (oversized surcharge applied)");
                yield 3.5;
            }
        };
    }

    public static void main(String[] args) {
        for (Size s : Size.values()) {
            System.out.println(s + " -> x" + multiplier(s));
        }
    }
}
```

**How to run:** `java MultiplierArrow.java`

Expected output:
```
SMALL -> x1.0
MEDIUM -> x1.5
LARGE -> x2.0
  (oversized surcharge applied)
OVERSIZED -> x3.5
```

### Level 2 — Intermediate

```java
// File: MultiplierColon.java
public class MultiplierColon {
    enum Size { SMALL, MEDIUM, LARGE, OVERSIZED }

    static double multiplier(Size size) {
        return switch (size) {
            case SMALL:
                yield 1.0;
            case MEDIUM:
                yield 1.5;
            case LARGE:
                yield 2.0;
            case OVERSIZED:
                System.out.println("  (oversized surcharge applied)");
                yield 3.5;
        };
    }

    public static void main(String[] args) {
        for (Size s : Size.values()) {
            System.out.println(s + " -> x" + multiplier(s));
        }
    }
}
```

**How to run:** `java MultiplierColon.java`

Expected output is identical to Level 1:
```
SMALL -> x1.0
MEDIUM -> x1.5
LARGE -> x2.0
  (oversized surcharge applied)
OVERSIZED -> x3.5
```

Same behavior, same exhaustiveness guarantee (no `default` needed since all four `Size` values are covered), but written with colon labels — each arm still must end in `yield` (or `throw`), and critically, `yield` here also means "stop, don't fall through to the next label," even though these are colon labels which would fall through in a plain *statement* context.

### Level 3 — Advanced

```java
// File: MultiplierGrouped.java
public class MultiplierGrouped {
    enum Size { SMALL, MEDIUM, LARGE, OVERSIZED, FRAGILE_SMALL, FRAGILE_LARGE }

    static double multiplier(Size size) {
        return switch (size) {
            case SMALL:
            case FRAGILE_SMALL:
                // Both labels share this one yield — like old-style fall-through,
                // but explicit: there's no way to accidentally continue further.
                yield size.name().startsWith("FRAGILE") ? 1.3 : 1.0;
            case MEDIUM:
                yield 1.5;
            case LARGE:
            case FRAGILE_LARGE:
                yield size.name().startsWith("FRAGILE") ? 2.6 : 2.0;
            case OVERSIZED:
                yield 3.5;
        };
    }

    public static void main(String[] args) {
        for (Size s : Size.values()) {
            System.out.println(s + " -> x" + multiplier(s));
        }
    }
}
```

**How to run:** `java MultiplierGrouped.java`

Expected output:
```
SMALL -> x1.0
MEDIUM -> x1.5
LARGE -> x2.0
OVERSIZED -> x3.5
FRAGILE_SMALL -> x1.3
FRAGILE_LARGE -> x2.6
```

Level 3 groups `SMALL` with `FRAGILE_SMALL` (and `LARGE` with `FRAGILE_LARGE`) under shared colon labels that both reach the *same* `yield` statement — this deliberately recreates the classic "stacked case labels with shared code" idiom colon-labeled switches were often used for, except now it's `yield`-driven and cannot accidentally continue past its intended stopping point the way a missing `break` could in the old fall-through statement form.

## 6. Walkthrough

1. `main` iterates `Size.values()` in declaration order; when it reaches `Size.FRAGILE_SMALL`, it calls `multiplier(FRAGILE_SMALL)`.
2. Control enters `switch (size)`. The switch checks labels top to bottom: `case SMALL:` doesn't match `FRAGILE_SMALL`, but because there's no `yield` or `break` immediately after `case SMALL:` — just another label, `case FRAGILE_SMALL:` — the compiler groups these two colon labels together as leading into the same code, exactly like traditional fall-through label-stacking. `FRAGILE_SMALL` **does** match the second label, so control enters this shared arm's code.
3. `size.name()` returns `"FRAGILE_SMALL"`; `.startsWith("FRAGILE")` evaluates `true`, so the ternary selects `1.3`.
4. `yield 1.3;` executes, immediately exiting the switch expression with `1.3` as its value — there is no possibility of continuing past this point into `case MEDIUM:`'s code, because `yield` (unlike the absence of `break` in a plain switch statement) always terminates the switch expression's evaluation right there.
5. `multiplier` returns `1.3` to `main`, and `System.out.println` prints `"FRAGILE_SMALL -> x1.3"`.
6. Now consider `Size.SMALL` itself (processed earlier in the loop): it matches the *first* of the two stacked labels. Execution falls through the label declaration itself (that's the intentional "labels share code" grouping) into the very same shared block, but `size.name()` here is `"SMALL"`, so `.startsWith("FRAGILE")` is `false`, and the ternary selects `1.0` instead. `yield 1.0;` then exits with that value.
7. This demonstrates the key distinction `yield` introduces: colon labels can still be **stacked to share code** (a useful, intentional pattern), but once execution reaches a `yield` statement, there is no ambiguity or risk of continuing further — `yield` always means "the switch expression's value is this, and evaluation of the switch stops now," regardless of whether the labels leading to it were colons or arrows.

```
case SMALL:            ┐
case FRAGILE_SMALL:     ├─► shared code ─► yield (name-dependent value) ─► switch exits
                        ┘
   (both labels reach the same yield; yield itself never falls through further)
```

## 7. Gotchas & takeaways

> `yield` is required on **every reachable path** of a colon-labeled switch expression's arms — if any label's code path could fall off the end without hitting a `yield` or `throw`, the compiler rejects the whole switch expression as non-exhaustive/incomplete. This is stricter than a colon-labeled switch *statement*, where falling through to the next label (or off the end) is completely legal, just often a bug.

- `yield` works identically whether the enclosing switch expression uses colon or arrow labels — its meaning ("produce this value, stop evaluating the switch") doesn't depend on label style.
- Colon labels can still be stacked to intentionally share one block of code (and one `yield`) across multiple case values — a controlled, explicit version of the old fall-through idiom.
- A `yield` statement always terminates evaluation of its enclosing switch expression; there's no way for execution to "continue past" a `yield` into a subsequent label, unlike a missing `break` in a colon-labeled switch statement.
- Single-expression arrow arms (`case X -> value;`) never need `yield` — only `{ }` block arrow arms and colon-labeled arms require it.
- When reading unfamiliar code, check whether a `switch`'s result is being assigned/returned/used as a value — that's what tells you whether `yield` statements inside it are meaningful expression-producers or would be a compile error if misplaced.
