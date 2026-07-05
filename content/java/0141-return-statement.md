---
card: java
gi: 141
slug: return-statement
title: return statement
---

## 1. What it is

The `return` statement immediately exits the current method, handing control back to whatever called it. If the method has a non-`void` return type, `return` must be followed by an expression whose value becomes the method's result; if the method is declared `void`, `return` is used alone (with no expression) purely to exit early — or is simply omitted, since a `void` method returns automatically when it reaches its closing brace.

```java
public class ReturnDemo {
    static int absoluteValue(int n) {
        if (n < 0) {
            return -n; // exits here for negative input; the line below never runs
        }
        return n;
    }

    public static void main(String[] args) {
        System.out.println(absoluteValue(-7)); // 7
        System.out.println(absoluteValue(7));  // 7
    }
}
```

Whichever `return` executes first ends the method immediately — a method can have several `return` statements on different branches, but at most one of them ever actually runs per call.

## 2. Why & when

`return` is how a method produces its result and, more broadly, how a method exits before reaching its final line:

- **Producing a value** — every non-`void` method needs at least one reachable `return expression;` on every possible execution path, or the code fails to compile.
- **Early exit / guard clauses** — returning as soon as a special case is detected (invalid input, an already-known answer) avoids deeply nested `if`/`else` chains.
- **Exiting loops from within a method** — as seen in earlier loop topics, `return` inside a loop stops both the loop and the method in one step, useful when the method's whole purpose is answered by something found mid-loop.

The compiler enforces that a non-`void` method's every possible path ends in a `return` (or a `throw`) — this is why an `if`/`else if` with no final `else`, for instance, often needs an extra `return` after the chain, unless every branch already returns.

## 3. Core concept

```java
public class GuardClauseDemo {
    static String classify(int age) {
        if (age < 0) {
            return "Invalid age"; // guard clause: handle the bad case first and exit immediately
        }
        if (age < 13) {
            return "Child";
        }
        if (age < 20) {
            return "Teenager";
        }
        return "Adult"; // reached only if none of the above returned
    }

    public static void main(String[] args) {
        System.out.println(classify(-5));
        System.out.println(classify(8));
        System.out.println(classify(16));
        System.out.println(classify(30));
    }
}
```

Each `if` is a **guard clause**: it checks one condition and returns immediately if it matches, so the rest of the method only ever deals with cases that survived every guard above it — there is no `else` needed anywhere, because `return` already removes those cases from consideration.

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Return statement diagram: a chain of guard clauses, each checking one condition and returning immediately if it matches, with a final return reached only if none of the guards matched.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">classify(16) — falls through two guards, matches the third</text>

  <rect x="30" y="45" width="150" height="26" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="105" y="62" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="monospace">age &lt; 0? no</text>

  <rect x="200" y="45" width="150" height="26" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="275" y="62" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="monospace">age &lt; 13? no</text>

  <rect x="370" y="45" width="150" height="26" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="445" y="62" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="monospace">age &lt; 20? YES</text>

  <path d="M 445 71 L 445 95" stroke="#6db33f" stroke-width="2" marker-end="url(#a)"/>
  <rect x="365" y="95" width="160" height="28" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="445" y="114" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">return "Teenager"</text>

  <text x="600" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(final "Adult"</text>
  <text x="600" y="74" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">never reached)</text>

  <text x="350" y="150" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Each guard that doesn't match falls through to the next one; the first match returns immediately.</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

Only the first matching guard's `return` executes; every guard after it is skipped entirely.

## 5. Runnable example

Scenario: validating and pricing a shopping cart order — starting with a basic method that returns a total, then adding guard clauses for invalid input, then hardening it to return early from inside a loop the moment an unpriceable item is found, propagating a clear failure signal rather than a wrong total.

### Level 1 — Basic

```java
public class OrderTotalBasic {
    static double total(double[] prices) {
        double sum = 0.0;
        for (double price : prices) {
            sum += price;
        }
        return sum; // the one and only return, reached after the loop finishes
    }

    public static void main(String[] args) {
        System.out.println(total(new double[]{ 9.99, 4.50, 2.25 }));
    }
}
```

**How to run:** `java OrderTotalBasic.java`

`total` has a single `return sum;` at the very end, reached only after the `for` loop has finished summing every price. There is no early exit yet — every element of `prices` is always visited before the method returns.

### Level 2 — Intermediate

Same order total, now with a **guard clause** at the top that returns immediately for an invalid (empty) cart, before the summing loop even begins — avoiding a meaningless "total of nothing" computation.

```java
public class OrderTotalIntermediate {
    static double total(double[] prices) {
        if (prices == null || prices.length == 0) {
            return 0.0; // guard clause: nothing to sum, exit immediately
        }

        double sum = 0.0;
        for (double price : prices) {
            sum += price;
        }
        return sum;
    }

    public static void main(String[] args) {
        System.out.println(total(new double[]{ 9.99, 4.50, 2.25 }));
        System.out.println(total(new double[]{}));
        System.out.println(total(null));
    }
}
```

**How to run:** `java OrderTotalIntermediate.java`

The guard clause `if (prices == null || prices.length == 0) return 0.0;` handles both edge cases (`null` and an empty array) in one place, at the very top, before any of the "normal" logic runs — this is the guard-clause pattern from part 3 applied to input validation rather than classification.

### Level 3 — Advanced

Same order total, now returning early from **inside** the summing loop the moment a genuinely invalid price (negative, which should never occur in real data) is encountered — using `return` to signal failure immediately rather than letting a bad value silently corrupt the total.

```java
public class OrderTotalAdvanced {

    static Double total(double[] prices) { // Double (boxed) so null can signal failure
        if (prices == null || prices.length == 0) {
            return 0.0;
        }

        double sum = 0.0;
        for (int i = 0; i < prices.length; i++) {
            if (prices[i] < 0) {
                System.out.println("Invalid negative price at index " + i + ": " + prices[i]);
                return null; // abandon the whole computation — don't return a partial, misleading total
            }
            sum += prices[i];
        }
        return sum;
    }

    public static void main(String[] args) {
        Double t1 = total(new double[]{ 9.99, 4.50, 2.25 });
        Double t2 = total(new double[]{ 9.99, -1.00, 2.25 });

        System.out.println(t1 == null ? "Order rejected" : "Total: " + t1);
        System.out.println(t2 == null ? "Order rejected" : "Total: " + t2);
    }
}
```

**How to run:** `java OrderTotalAdvanced.java`

The method now returns `Double` (the boxed wrapper, which can be `null`) instead of primitive `double`, specifically so that `return null;` can signal "this computation failed" distinctly from any real numeric total, including `0.0`. The moment a negative price is found inside the loop, `return null;` exits immediately — `sum` at that point is discarded entirely, so the caller never sees a partial, misleadingly-low total for an order that actually contains bad data.

## 6. Walkthrough

Trace `total(new double[]{ 9.99, -1.00, 2.25 })`:

**Guard clause.** `prices` is neither `null` nor empty, so the first `if` does not return; execution falls through to the loop.

**i = 0.** `prices[0] = 9.99`. Not negative, so `sum += 9.99` (`sum = 9.99`).

**i = 1.** `prices[1] = -1.00`. This *is* negative — the inner `if` matches. The method prints `"Invalid negative price at index 1: -1.0"` and immediately executes `return null;`. Index 2 (`2.25`) is never examined, and the partial `sum` value of `9.99` is discarded entirely — it never reaches any `return`.

```
prices = {9.99, -1.00, 2.25}
i=0: 9.99  -> not negative -> sum = 9.99
i=1: -1.00 -> NEGATIVE! print message -> return null (index 2 never checked, sum=9.99 discarded)
```

**Back in `main`.** `t2` is assigned `null` (auto-unboxing does not occur here since `t2` is itself declared `Double`). The ternary `t2 == null ? "Order rejected" : ...` evaluates its `null` check first and prints `"Order rejected"` — the caller never sees any numeric total for this order, correct or otherwise.

**For comparison**, the first call, `total(new double[]{ 9.99, 4.50, 2.25 })`, has no negative prices, so the loop runs to completion and `return sum;` executes with `sum = 16.74`, printing `"Total: 16.74"`.

## 7. Gotchas & takeaways

> **Every possible execution path through a non-`void` method must reach a `return` (or a `throw`) — the compiler enforces this ("missing return statement") even if you, as the programmer, know a particular path is logically unreachable.** An `if`/`else if` chain with no final `else`, for instance, needs a trailing `return` after it unless every branch inside already returns.

> **`return` inside a loop exits the entire method, not just the loop** — this is different from `break`, which only exits the loop. If you meant to just stop looping but keep running code afterward in the same method, use `break`, not `return`.

- `return expr;` both produces the method's result and immediately exits — no code after it in that method call ever runs for that invocation.
- Guard clauses (an early `if` that returns immediately for a special case) often read more clearly than deeply nested `if`/`else` chains.
- A boxed return type (like `Double` instead of `double`) can use `null` as a distinct "no valid result" signal — but only where the caller is expected to check for it, since it also reintroduces the possibility of a `NullPointerException` if the caller forgets to.
- Returning early from inside a loop the moment invalid data is found avoids computing and accidentally returning a partial, misleading result.
