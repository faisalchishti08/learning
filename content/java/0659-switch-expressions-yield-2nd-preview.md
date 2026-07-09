---
card: java
gi: 659
slug: switch-expressions-yield-2nd-preview
title: Switch expressions yield (2nd preview)
---

## 1. What it is

Java 13's **second preview** of switch expressions (JEP 354) refined the syntax introduced as a first preview in Java 12, most visibly by replacing the earlier `break value;` form for returning a value from a `{ ... }` block arm with a dedicated **`yield value;`** statement. In the Java 12 preview, you wrote `break 6;` inside a block arm to produce a value from a switch expression — but that overloaded `break`'s existing meaning (exiting a loop or switch *statement*) in a confusing way, especially inside nested loops or switches. Java 13 replaced this with `yield`, a new contextual keyword that means exactly one thing: "this is the value this switch expression block arm produces," distinct from `break`'s "stop executing this construct" meaning.

## 2. Why & when

Reusing `break value;` in the first preview created real ambiguity: inside a `{ }` block arm of a switch expression, if that block also contained a loop, would `break;` (no value) exit the loop or the switch? The two meanings of `break` — "exit early" and "produce this value" — don't compose cleanly once you nest control structures inside a switch expression's block arms. Java's designers introduced `yield` as an unambiguous, purpose-built keyword specifically for "this block arm's result is this value," leaving `break` free to keep its traditional, unambiguous meaning everywhere else, including inside a switch expression's block arm if you genuinely need to break out of an inner loop. You'd write `yield` any time a switch expression's arm needs more than one statement to compute its value — validation, intermediate calculations, or logging — before producing the final result.

## 3. Core concept

```java
// Java 12 preview (now superseded): break used to "return" a value — ambiguous
int result = switch (day) {
    case MONDAY -> {
        int x = 6;
        break x;      // confusing: looks like it might exit a loop instead
    }
    default -> 0;
};

// Java 13 second preview: yield is unambiguous
int result2 = switch (day) {
    case MONDAY -> {
        int x = 6;
        yield x;      // clearly: "this block's result is x"
    }
    default -> 0;
};
```

`yield` is only meaningful inside a switch expression's block arm (or inside an old-style `switch` statement being used as an expression via the traditional `:`/`case` form) — it is a *contextual* keyword, not a reserved word, so it can still be used as a regular identifier elsewhere in your code.

## 4. Diagram

<svg viewBox="0 0 620 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="break was ambiguous inside nested loops in a switch expression block; yield unambiguously produces the switch expression's value">
  <rect x="10" y="15" width="290" height="150" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="155" y="35" fill="#f85149" font-size="12" text-anchor="middle" font-family="sans-serif">Java 12 preview: break value</text>
  <text x="25" y="60" fill="#e6edf3" font-size="10" font-family="monospace">case X -> {</text>
  <text x="25" y="75" fill="#e6edf3" font-size="10" font-family="monospace">  for (...) {</text>
  <text x="25" y="90" fill="#f85149" font-size="10" font-family="monospace">    break; // loop or switch?!</text>
  <text x="25" y="105" fill="#e6edf3" font-size="10" font-family="monospace">  }</text>
  <text x="25" y="120" fill="#e6edf3" font-size="10" font-family="monospace">  break someValue;</text>
  <text x="25" y="135" fill="#e6edf3" font-size="10" font-family="monospace">}</text>
  <text x="25" y="155" fill="#f85149" font-size="9" font-family="sans-serif">Ambiguous meaning near loops.</text>

  <rect x="320" y="15" width="290" height="150" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="35" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 13 2nd preview: yield</text>
  <text x="335" y="60" fill="#e6edf3" font-size="10" font-family="monospace">case X -> {</text>
  <text x="335" y="75" fill="#e6edf3" font-size="10" font-family="monospace">  for (...) {</text>
  <text x="335" y="90" fill="#6db33f" font-size="10" font-family="monospace">    break; // unambiguous: loop</text>
  <text x="335" y="105" fill="#e6edf3" font-size="10" font-family="monospace">  }</text>
  <text x="335" y="120" fill="#79c0ff" font-size="10" font-family="monospace">  yield someValue;</text>
  <text x="335" y="135" fill="#e6edf3" font-size="10" font-family="monospace">}</text>
  <text x="335" y="155" fill="#6db33f" font-size="9" font-family="sans-serif">break=exit loop, yield=produce value.</text>
</svg>

`yield` gives switch-expression block arms their own unambiguous "produce this value" statement, freeing `break` to keep meaning "exit early" everywhere, including inside nested loops.

## 5. Runnable example

Scenario: computing a shipping discount tier from an order total — first a simple `yield`-based block arm, then extending it with validation logic that needs multiple statements before producing a value, then a version with a nested loop inside a block arm to show `break` and `yield` cleanly coexisting.

### Level 1 — Basic

```java
// File: YieldBasic.java
public class YieldBasic {
    static String discountTier(int orderTotal) {
        return switch (Integer.signum(orderTotal)) {
            case -1 -> "invalid";
            case 0  -> "none";
            case 1  -> {
                String tier;
                if (orderTotal >= 100) {
                    tier = "gold";
                } else if (orderTotal >= 50) {
                    tier = "silver";
                } else {
                    tier = "bronze";
                }
                yield tier;
            }
            default -> throw new IllegalStateException("unreachable");
        };
    }

    public static void main(String[] args) {
        for (int total : new int[]{-10, 0, 30, 75, 150}) {
            System.out.println(total + " -> " + discountTier(total));
        }
    }
}
```

**How to run:** requires the preview flag since this is still a preview feature in Java 13:
```
javac --release 13 --enable-preview YieldBasic.java
java --enable-preview YieldBasic
```

Expected output:
```
-10 -> invalid
0 -> none
30 -> bronze
75 -> silver
150 -> gold
```

### Level 2 — Intermediate

```java
// File: YieldValidating.java
public class YieldValidating {
    static String discountTier(int orderTotal, boolean hasCoupon) {
        return switch (Integer.signum(orderTotal)) {
            case -1 -> throw new IllegalArgumentException("negative total: " + orderTotal);
            case 0  -> "none";
            case 1  -> {
                int effectiveTotal = orderTotal;
                if (hasCoupon) {
                    effectiveTotal += 20; // coupon nudges the tier calculation up
                    System.out.println("  (coupon applied, effective total = " + effectiveTotal + ")");
                }
                String tier = effectiveTotal >= 100 ? "gold" : effectiveTotal >= 50 ? "silver" : "bronze";
                yield tier;
            }
            default -> throw new IllegalStateException("unreachable");
        };
    }

    public static void main(String[] args) {
        System.out.println("75, no coupon: " + discountTier(75, false));
        System.out.println("75, with coupon: " + discountTier(75, true));
        try {
            discountTier(-5, false);
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac --release 13 --enable-preview YieldValidating.java && java --enable-preview YieldValidating`

Expected output:
```
75, no coupon: silver
  (coupon applied, effective total = 95)
75, with coupon: silver
Rejected: negative total: -5
```

The block arm for `case 1` now runs several statements — conditionally adjusting `effectiveTotal`, printing a diagnostic — before finally computing and `yield`ing the tier; note that a `throw` in another arm (`case -1`) is still valid because throwing never needs to produce a value.

### Level 3 — Advanced

```java
// File: YieldWithLoop.java
public class YieldWithLoop {
    static int firstDiscountThreshold(int orderTotal, int[] thresholds) {
        return switch (Integer.signum(orderTotal)) {
            case -1, 0 -> -1;
            case 1 -> {
                int found = -1;
                for (int t : thresholds) {
                    if (orderTotal >= t) {
                        found = t;
                        break; // exits the FOR loop — unambiguous, thanks to yield existing separately
                    }
                }
                yield found; // produces the switch expression's value
            }
            default -> throw new IllegalStateException("unreachable");
        };
    }

    public static void main(String[] args) {
        int[] thresholds = {100, 50, 20}; // checked in this order
        for (int total : new int[]{5, 25, 60, 120}) {
            System.out.println(total + " -> threshold " + firstDiscountThreshold(total, thresholds));
        }
    }
}
```

**How to run:** `javac --release 13 --enable-preview YieldWithLoop.java && java --enable-preview YieldWithLoop`

Expected output:
```
5 -> threshold -1
25 -> threshold 20
60 -> threshold 50
120 -> threshold 100
```

Level 3 puts a `for` loop with its own `break` **inside** a switch expression's block arm, then uses `yield` to produce the arm's actual value — this is exactly the scenario the Java 12 preview's `break value;` syntax handled ambiguously, and `yield` resolves cleanly: `break` here unambiguously exits the `for` loop, and `yield found` unambiguously produces the switch expression's result.

## 6. Walkthrough

1. `main` calls `firstDiscountThreshold(60, thresholds)`. Control enters `switch (Integer.signum(60))`. `Integer.signum(60)` returns `1` (positive), so the `case 1 ->` arm's block is entered.
2. Inside the block, `found` is initialized to `-1` as a sentinel meaning "no threshold matched yet."
3. The `for (int t : thresholds)` loop begins iterating over `{100, 50, 20}` in order. First iteration: `t = 100`. The condition `orderTotal >= t` checks `60 >= 100`, which is `false`, so the loop body's `if` doesn't run, and the loop continues to the next element.
4. Second iteration: `t = 50`. `60 >= 50` is `true`. `found` is set to `50`, and `break;` executes — this exits the **`for` loop** (its only sensible meaning here, since `yield` is what exits/produces a value for the switch expression, leaving `break` free to mean exactly what it always means for loops).
5. After the loop (whether it broke early or ran to completion), `yield found;` executes, producing `50` as the value of the entire `switch` expression for this call.
6. Back in `main`, `firstDiscountThreshold` returns `50`, and `System.out.println` prints `"60 -> threshold 50"`.
7. For `total = 5`, the loop checks `5 >= 100` (false), `5 >= 50` (false), `5 >= 20` (false) — no `break` ever fires, the loop completes normally, and `found` still holds its initial `-1`, which `yield found` then produces as the result, printed as `"5 -> threshold -1"`.

```
case 1 -> {
    found = -1
    for t in [100, 50, 20]:
        if 60 >= t: found = t; break   ◄── break exits the FOR loop
    yield found                         ◄── yield produces the SWITCH's value
}
```

## 7. Gotchas & takeaways

> This remains a **preview feature** in Java 13 — both `text-blocks-preview`-style `--enable-preview` flags are required, and the `yield` keyword itself, along with the overall switch-expression syntax, was still evolving; it became permanent (no preview flag needed) starting in Java 14. Code written against the Java 13 preview should not be assumed byte-compatible with earlier Java 12 preview code using `break value;`.

- `yield` is a **contextual keyword**: it only has special meaning inside a switch expression's block arm; you can still use `yield` as a variable or method name elsewhere without conflict.
- Inside a block arm, any loop's own `break`/`continue` keep their normal loop-scoped meaning — they no longer double as "produce the switch's value" the way `break value;` briefly did in the Java 12 preview.
- A single-expression arm (`case X -> someExpr;`) doesn't need or use `yield` — the expression's value *is* the result directly.
- A block arm (`case X -> { ... }`) must end every reachable path with either a `yield` statement or a `throw` — the compiler rejects a block arm that could "fall off the end" without producing a value.
- If you're reading older Java 12 code samples using `break value;` inside a switch expression, know that this was replaced by `yield` starting in the Java 13 preview — they're not interchangeable in Java 13+.
