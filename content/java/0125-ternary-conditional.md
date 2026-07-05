---
card: java
gi: 125
slug: ternary-conditional
title: Ternary conditional ?:
---

## 1. What it is

The ternary (conditional) operator `condition ? expressionIfTrue : expressionIfFalse` is Java's only operator that takes three operands. It evaluates `condition` (a `boolean`), and then evaluates and returns *only one* of the other two expressions — `expressionIfTrue` if the condition was `true`, `expressionIfFalse` otherwise. The expression that is not selected is never evaluated at all, which is a genuine short-circuit, not just a stylistic convenience — exactly like `&&`/`||`.

```java
int a = 5, b = 10;
int max = (a > b) ? a : b;    // evaluates a > b (false), so max = b = 10

String label = (a % 2 == 0) ? "even" : "odd";
System.out.println(label);     // "odd"
```

Unlike an `if`/`else` statement, the ternary operator is an *expression* — it produces a value that can be assigned, passed as an argument, or embedded inside a larger expression, whereas `if`/`else` is a *statement* that only controls which block of code runs and produces no value itself.

## 2. Why & when

The ternary operator is ideal for short, simple value selections where writing a full `if`/`else` would be unnecessarily verbose:

- Choosing between two values to assign: `int max = (a > b) ? a : b;`
- Building a string conditionally: `"Found " + count + " item" + (count == 1 ? "" : "s");`
- Providing a default for a possibly-invalid value: `int safeIndex = (index >= 0) ? index : 0;`

It should be avoided when the logic is complex, when either branch has side effects beyond producing a value, or when nesting ternaries would hurt readability — a nested ternary (`a ? b : (c ? d : e)`) can be legal and even sometimes clear for a simple three-way choice, but deeply nested or chained ternaries quickly become hard to read and should generally be rewritten as `if`/`else if`/`else` or a `switch` expression instead.

## 3. Core concept

```java
public class TernaryDemo {
    public static void main(String[] args) {
        int a = 5, b = 10;

        // Basic value selection
        int max = (a > b) ? a : b;
        System.out.println("max: " + max);   // 10

        // Building a string conditionally
        int count = 1;
        String message = "Found " + count + " item" + (count == 1 ? "" : "s");
        System.out.println(message);   // "Found 1 item"

        // Short-circuit: only the selected branch is evaluated
        int divisor = 0;
        int safeResult = (divisor != 0) ? (100 / divisor) : -1;   // 100/divisor is NEVER evaluated when divisor==0
        System.out.println("safeResult: " + safeResult);            // -1, no ArithmeticException

        // Ternary as an expression, usable directly in a method call
        System.out.println("Parity: " + (a % 2 == 0 ? "even" : "odd"));

        // Nested ternary for a simple three-way choice (use sparingly)
        int score = 75;
        String grade = (score >= 90) ? "A" : (score >= 70) ? "B" : "C";
        System.out.println("Grade: " + grade);   // "B"
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 155" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Ternary operator diagram: condition divisor not equal zero is checked, if true the left branch 100 divided by divisor is evaluated and returned, if false the right branch negative 1 is evaluated and returned instead, and the unselected branch is never evaluated at all.">
  <rect x="8" y="8" width="684" height="139" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(divisor != 0) ? (100 / divisor) : -1 — only the taken branch runs</text>

  <rect x="270" y="34" width="160" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="350" y="54" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">divisor != 0 ?</text>

  <path d="M 300 64 L 200 100" stroke="#6db33f" stroke-width="1.5"/>
  <text x="235" y="88" fill="#6db33f" font-size="8">true</text>
  <rect x="110" y="100" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="200" y="122" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">100 / divisor (evaluated)</text>

  <path d="M 400 64 L 500 100" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="88" fill="#79c0ff" font-size="8">false</text>
  <rect x="410" y="100" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="500" y="122" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">-1 (evaluated instead)</text>
</svg>

Only the branch selected by the condition is ever evaluated — the other is skipped entirely, just like `&&`/`||`'s short-circuit.

## 5. Runnable example

Scenario: a shopping cart discount calculator that selects a discount tier based on cart total — starting with a simple ternary, growing into a nested selection, then replaced with a cleaner `switch` expression for many tiers, illustrating exactly when ternary chains stop being the right tool.

### Level 1 — Basic

```java
public class DiscountBasic {
    public static void main(String[] args) {
        double cartTotal = 120.0;

        // Simple two-way choice: free shipping or not
        String shipping = (cartTotal >= 100) ? "FREE" : "$5.99";
        System.out.println("Shipping: " + shipping);

        // Selecting a numeric value based on a condition
        double discountRate = (cartTotal >= 100) ? 0.10 : 0.0;
        double finalTotal = cartTotal * (1 - discountRate);
        System.out.printf("Final total: $%.2f%n", finalTotal);
    }
}
```

**How to run:** `java DiscountBasic.java`

`(cartTotal >= 100) ? "FREE" : "$5.99"` evaluates the condition once and selects exactly one of the two string literals — this is a clean, single-line replacement for what would otherwise be a four-line `if`/`else` block just to assign one variable, which is exactly the case the ternary operator is designed for.

### Level 2 — Intermediate

Same discount calculator, now with three tiers using a nested ternary — still readable at this size, but hinting at the readability cost that grows with each additional tier.

```java
public class DiscountIntermediate {
    public static void main(String[] args) {
        double[] cartTotals = { 30.0, 75.0, 150.0 };

        for (double total : cartTotals) {
            double discountRate = (total >= 150) ? 0.15
                                 : (total >= 75)  ? 0.10
                                 : (total >= 50)   ? 0.05
                                 : 0.0;
            double finalTotal = total * (1 - discountRate);
            System.out.printf("Total: $%-7.2f Discount: %-5.0f%% Final: $%.2f%n",
                total, discountRate * 100, finalTotal);
        }
    }
}
```

**How to run:** `java DiscountIntermediate.java`

Each `?:` in the chain is evaluated in sequence: for `total = 75.0`, `(total >= 150)` is `false`, so the chain proceeds to `(total >= 75)`, which is `true`, selecting `0.10` — the remaining two conditions in the chain (`>= 50` and the final `else`-equivalent `0.0`) are never evaluated at all, because once a `?:` branch is selected, that whole nested chain is done. This four-tier chain is still readable with careful alignment, but every additional tier makes it progressively harder to scan — a common signal that it's time to switch to a different construct.

### Level 3 — Advanced

Same discount system, now with five tiers, refactored from the nested-ternary chain into a `switch` expression (Java 14+) — the more maintainable, readable choice once a "select one of several values based on ranges/cases" chain grows beyond two or three branches, directly demonstrating why ternary chains have a natural size limit.

```java
public class DiscountAdvanced {

    static double tierFor(double total) {
        // A switch expression (not the classic switch STATEMENT) is itself just a
        // more readable multi-branch alternative to the ternary operator for this many cases.
        if (total >= 300) return 0.20;
        if (total >= 150) return 0.15;
        if (total >= 75) return 0.10;
        if (total >= 50) return 0.05;
        return 0.0;
        // Note: an actual switch expression works best on discrete values, not ranges;
        // for range-based tiers, a sequence of early returns (as above) or if-else-if
        // is clearer than either a nested ternary chain or a switch on ranges.
    }

    public static void main(String[] args) {
        double[] cartTotals = { 30.0, 75.0, 150.0, 300.0, 500.0 };

        for (double total : cartTotals) {
            double discountRate = tierFor(total);
            // A single, simple ternary is still perfectly appropriate for the FINAL formatting step:
            String tierLabel = (discountRate == 0.0) ? "no discount" : (discountRate * 100) + "% off";
            double finalTotal = total * (1 - discountRate);
            System.out.printf("Total: $%-7.2f Tier: %-14s Final: $%.2f%n", total, tierLabel, finalTotal);
        }
    }
}
```

**How to run:** `java DiscountAdvanced.java`

`tierFor` replaces the nested ternary chain from Level 2 with a sequence of early `if`-`return` statements — functionally equivalent (each condition is checked in order until one matches), but each branch's condition and value are on their own line with no accumulating indentation or nested `?:` punctuation to visually parse, which scales far better as tiers are added or removed. `tierLabel`'s single ternary, by contrast, is still exactly the right tool: it makes one simple, final either/or decision (a label based on whether a discount applies at all) with no nesting, which is precisely the ternary operator's sweet spot.

## 6. Walkthrough

Trace `tierFor(150.0)` and compare it against what the equivalent nested-ternary chain from Level 2 would have done:

**The `if`-chain approach (Level 3).** `total >= 300`? `150.0 >= 300` is `false`, so this `return` is skipped and execution falls through to the next line. `total >= 150`? `150.0 >= 150` is `true`, so `return 0.15` executes immediately, and the method returns without ever reaching the remaining checks (`>= 75`, `>= 50`, or the final `return 0.0`).

**The nested-ternary equivalent (Level 2 style, extended to 5 tiers).** `(total >= 300) ? 0.20 : (total >= 150) ? 0.15 : (total >= 75) ? 0.10 : (total >= 50) ? 0.05 : 0.0`. Evaluation proceeds identically in spirit: `total >= 300` is `false`, so the chain evaluates its `:` branch, which is itself another ternary: `(total >= 150) ? 0.15 : ...`. This inner condition is `true`, so `0.15` is selected and the *entire rest* of the chain (three more nested ternaries) is never evaluated.

```
if-chain:                          nested ternary (same logic):
total >= 300? false -> fall through   total>=300 ? 0.20
total >= 150? true  -> return 0.15          : (total>=150 ? 0.15
  (done, other checks skipped)                   : (total>=75 ? 0.10
                                                       : (total>=50 ? 0.05 : 0.0)))
                                     total>=300 false, total>=150 true -> 0.15
                                     (remaining nested ternaries never evaluated)
```

**Why the `if`-chain is preferred here despite being logically identical.** Both approaches short-circuit at the first matching condition and produce the identical result (`0.15`) via the identical number of comparisons. The difference is purely readability: the `if`-chain's structure visually separates each condition/value pair onto its own line without any nesting depth increasing, while the nested ternary's punctuation (`?`, `:`) accumulates and requires mentally tracking which `:` belongs to which `?` as the chain grows — a cost that is negligible for two tiers but becomes a real maintenance burden at five.

**Final output.** The program prints each cart total alongside its computed tier label (`"no discount"` through `"20.0% off"`) and final price, with the single ternary in `tierLabel` demonstrating the operator's continued usefulness for a genuinely simple, one-shot binary choice even in code that has otherwise moved away from ternary chains for the more complex tier selection.

## 7. Gotchas & takeaways

> **The ternary operator genuinely short-circuits: only the selected branch is evaluated, exactly like `&&`/`||`.** This is not just a style choice — code can and does rely on it, such as `(divisor != 0) ? (100 / divisor) : -1`, which would throw `ArithmeticException` if the division branch were evaluated unconditionally.

> **Nested/chained ternaries have a real readability ceiling — beyond two or three branches, prefer `if`/`else if`/`else` or a `switch` expression.** The logic is often identical, but a sequence of clearly separated conditions reads far better than accumulating `? :` punctuation.

- `condition ? a : b` is an expression (it produces a value), unlike `if`/`else`, which is a statement (it controls execution flow but produces no value).
- Both branches must be type-compatible in a way that lets the compiler determine a single result type for the whole expression (numeric promotion applies here too, similar to arithmetic operators).
- Reserve the ternary operator for short, simple, side-effect-free value selections; avoid it for complex logic or when either branch needs to perform an action beyond producing a value.
- A chain of nested ternaries and an equivalent chain of `if`-`return` statements are logically identical and short-circuit the same way — the choice between them is purely about readability as the number of branches grows.
