---
card: java
gi: 128
slug: if-statement
title: if statement
---

## 1. What it is

The `if` statement conditionally executes a block of code: it evaluates a `boolean` expression, and if the result is `true`, it executes the associated statement (or block, if wrapped in `{ }`); if `false`, it skips that statement entirely and continues with whatever comes after. Unlike the ternary operator, `if` is a *statement*, not an expression — it produces no value and cannot be used inside a larger expression; it only controls which piece of code runs.

```java
int age = 20;
if (age >= 18) {
    System.out.println("Adult");
}
// execution continues here regardless of the condition

// Braces are technically optional for a single statement, but omitting them is risky:
if (age >= 18) System.out.println("Adult (no braces)");
```

Java requires the condition to be a genuine `boolean` expression — unlike C or JavaScript, an `int` cannot be used directly as a condition (`if (someInt)` does not compile in Java), which eliminates an entire class of "assignment instead of comparison" bugs (`if (x = 5)` is a compile error in Java, whereas in C it silently assigns `5` to `x` and then evaluates the assignment's truthiness).

## 2. Why & when

`if` is the fundamental building block of conditional logic in Java, used anywhere a decision needs to change what code executes next — validating input, branching on state, guarding against invalid operations, and so on. It is preferred over the ternary operator whenever:

- The action to take is a statement with side effects (printing, throwing, modifying state) rather than producing a single value to assign.
- The logic requires more than a simple two-way value choice, especially when combined with `else if`/`else` chains (covered separately) for multi-way branching.
- Readability benefits from an explicit block, especially when the condition or the action is non-trivial.

## 3. Core concept

```java
public class IfDemo {
    public static void main(String[] args) {
        int temperature = 35;

        // Basic if: executes only when the condition is true
        if (temperature > 30) {
            System.out.println("It's hot outside!");
        }

        // Single-statement if without braces (legal, but risky — see gotchas)
        if (temperature > 30)
            System.out.println("Still hot (no braces).");

        // A common bug: adding a second statement, forgetting it needs braces
        if (temperature > 30)
            System.out.println("This runs only when hot.");
            System.out.println("This ALWAYS runs, regardless of temperature!");  // NOT part of the if!

        // Boolean expressions only — no truthy/falsy int coercion
        boolean isHot = temperature > 30;
        if (isHot) {
            System.out.println("Confirmed hot via boolean variable.");
        }

        // A guard clause: exit early if a precondition fails
        int[] data = {};
        if (data.length == 0) {
            System.out.println("No data to process.");
        }
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 165" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="if statement control flow diagram: execution reaches the condition check, if true it enters the if block and runs its statements, if false it skips the block entirely, and either way execution continues at the same point after the if statement.">
  <rect x="8" y="8" width="684" height="149" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">if (condition) { ... } — the block is skipped entirely when the condition is false</text>

  <rect x="290" y="34" width="120" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="350" y="54" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">condition?</text>

  <path d="M 320 64 L 220 100" stroke="#6db33f" stroke-width="1.5"/>
  <text x="255" y="88" fill="#6db33f" font-size="8">true</text>
  <rect x="120" y="100" width="200" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="220" y="122" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">if-block executes</text>

  <path d="M 380 64 L 480 100" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="445" y="88" fill="#79c0ff" font-size="8">false</text>
  <rect x="400" y="100" width="200" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="500" y="122" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">block SKIPPED entirely</text>

  <text x="350" y="152" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Either way, execution continues at the same point after the if statement.</text>
</svg>

An `if` block either runs completely or is skipped completely — there is no partial execution.

## 5. Runnable example

Scenario: an order-validation guard that checks a shipment is ready to send — starting with a bare, brace-less `if` that hides a classic bug, then fixed and hardened with explicit braces and early-return guard clauses.

### Level 1 — Basic

```java
public class OrderBasic {
    public static void main(String[] args) {
        int itemCount = 3;
        boolean paymentConfirmed = true;

        if (paymentConfirmed)
            System.out.println("Payment confirmed.");
            System.out.println("Preparing shipment...");   // BUG: this always runs, indentation is misleading

        if (itemCount == 0) {
            System.out.println("Cannot ship an empty order.");
        }
    }
}
```

**How to run:** `java OrderBasic.java`

Without braces, `if (paymentConfirmed)` only controls the single statement immediately following it — `System.out.println("Payment confirmed.")`. The next line, `System.out.println("Preparing shipment...")`, is *not* part of the `if` at all, despite its matching indentation visually suggesting it is; it is a completely separate statement that runs unconditionally every time, regardless of `paymentConfirmed`'s value. This is one of the most common sources of subtle bugs when developers omit braces and later add a second line inside what they believe is the `if` block.

### Level 2 — Intermediate

Same order validator, now with braces always used (removing the ambiguity entirely) and restructured as early-return guard clauses, a common and readable pattern for validating multiple independent preconditions.

```java
public class OrderIntermediate {

    static boolean validateOrder(int itemCount, boolean paymentConfirmed, double totalWeight) {
        if (itemCount == 0) {
            System.out.println("Rejected: order has no items.");
            return false;
        }
        if (!paymentConfirmed) {
            System.out.println("Rejected: payment not confirmed.");
            return false;
        }
        if (totalWeight > 50.0) {
            System.out.println("Rejected: shipment exceeds weight limit.");
            return false;
        }
        System.out.println("Order validated successfully.");
        return true;
    }

    public static void main(String[] args) {
        validateOrder(3, true, 12.5);    // passes all checks
        validateOrder(0, true, 12.5);     // fails on item count
        validateOrder(3, false, 12.5);     // fails on payment
    }
}
```

**How to run:** `java OrderIntermediate.java`

Each `if` here is a guard clause: it checks one specific failure condition and, if triggered, prints a message and returns immediately — every block always uses braces, so there is no ambiguity about what each `if` controls, even as more lines are added inside a block later. This "check each failure case early, return immediately" style avoids deeply nested `if`/`else` structures and keeps each precondition's logic visually self-contained.

### Level 3 — Advanced

Same validator, now demonstrating a related but distinct gotcha — the "dangling else" ambiguity that can arise from nested `if` statements without braces — and showing how braces resolve it unambiguously, alongside a defensive coding style that always uses braces specifically to prevent this class of bug regardless of how the code is edited later.

```java
public class OrderAdvanced {

    static void checkPriority(boolean isExpressShipping, boolean isFragile) {
        // Without braces, this "else" binds to the NEAREST unmatched "if" — which may not be the
        // one the indentation visually suggests it belongs to. This is the "dangling else" problem.
        if (isExpressShipping)
            if (isFragile)
                System.out.println("Express + fragile: handle with extra care, priority lane.");
            else
                System.out.println("This 'else' binds to the INNER if (isFragile), not the outer one!");
        // If isExpressShipping is false, NEITHER message prints — even though the indentation
        // makes the else look like it's paired with the outer "if (isExpressShipping)".

        System.out.println("---");

        // Fixed: explicit braces make the intended grouping unambiguous
        if (isExpressShipping) {
            if (isFragile) {
                System.out.println("Express + fragile: handle with extra care, priority lane.");
            } else {
                System.out.println("Express, not fragile: priority lane, standard handling.");
            }
        } else {
            System.out.println("Standard shipping: normal queue.");
        }
    }

    public static void main(String[] args) {
        System.out.println("Case: express=false, fragile=true (should show 'Standard shipping' after the fix)");
        checkPriority(false, true);
    }
}
```

**How to run:** `java OrderAdvanced.java`

In the brace-less version, `if (isExpressShipping) if (isFragile) ... else ...` has its `else` bind to the *nearest* unmatched `if`, which is `if (isFragile)`, not `if (isExpressShipping)` — regardless of how the code is indented, Java's grammar always resolves a dangling `else` to the closest preceding `if` that doesn't already have its own `else`. This means that when `isExpressShipping` is `false`, the entire nested `if`/`else` is skipped and *nothing* prints from that section, even though the indentation visually suggests the `else` should handle the "not express shipping" case. The braced version removes all ambiguity: each `{ }` explicitly delimits exactly which `if` each `else` belongs to, correctly producing "Standard shipping: normal queue." when `isExpressShipping` is `false` — matching the intended three-way logic (express+fragile, express+not fragile, not express at all).

## 6. Walkthrough

Trace the brace-less version's dangling-else behavior for `checkPriority(false, true)`:

**Outer condition check.** `if (isExpressShipping)` evaluates `false`. Because this `if` has no braces, it controls only the single statement that would immediately follow it in the parsed grammar — which, due to how the nested `if`/`else` is parsed, is the *entire* `if (isFragile) ... else ...` construct treated as one statement.

**The whole nested construct is skipped.** Since the outer condition is `false`, the single statement it controls (the entire inner `if/else`) is skipped in its entirety — not just the `if (isFragile)` branch, but its paired `else` too, because that `else` was never a separate, outer-level `else`; it was already consumed as part of the inner `if`'s own structure.

**Nothing prints.** Execution falls through past the entire nested construct without printing either "Express + fragile..." or "This 'else' binds to the INNER if...", landing directly on the `"---"` separator line.

```
if (isExpressShipping)              <- false, no braces
    if (isFragile)                   <- this WHOLE if/else is the single statement
        print("Express + fragile")     controlled by the outer if
    else
        print("inner else message")

Outer condition false -> skip the ENTIRE inner if/else construct -> nothing prints
```

**The braced version, by contrast.** `if (isExpressShipping) { ... } else { ... }` has an explicit, separate `else` at the *outer* level, paired unambiguously with `if (isExpressShipping)` by the braces. Since `isExpressShipping` is `false`, this outer `else` block runs, printing `"Standard shipping: normal queue."` — the behavior a reader would naturally expect from the indentation, now guaranteed correct by the braces rather than merely suggested by whitespace.

## 7. Gotchas & takeaways

> **Braces are technically optional around a single-statement `if` body, but omitting them invites two classic bugs: accidentally adding a second "unguarded" statement that always runs, and the "dangling else" ambiguity in nested `if` statements, where an `else` binds to the nearest `if`, not necessarily the one the indentation suggests.** Always use braces, even for single-statement bodies, as a matter of defensive style.

> **Java requires a genuine `boolean` expression as an `if` condition — there is no implicit truthy/falsy coercion from `int` or other types**, unlike C or JavaScript. This eliminates the classic `if (x = 5)` assignment-instead-of-comparison bug at compile time, since `x = 5` evaluates to an `int`, not a `boolean`, and Java refuses to compile it as a condition.

- `if` is a statement (controls execution flow, produces no value), unlike the ternary operator, which is an expression (produces a value).
- Always wrap the body in braces `{ }`, even for a single statement — this prevents both the "extra unguarded statement" bug and the "dangling else" ambiguity in nested conditionals.
- Guard clauses (an early `if` check followed by an immediate `return`) are a common, readable pattern for validating multiple independent preconditions without deep nesting.
- Java's requirement that `if` conditions be genuine `boolean` expressions (not `int` or other coercible types) prevents an entire class of assignment-versus-comparison bugs at compile time.
