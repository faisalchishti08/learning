---
card: java
gi: 133
slug: default-case
title: default case
---

## 1. What it is

The `default` label in a `switch` statement marks the block of code to run when the switch expression's value does not match any of the explicit `case` labels. It is optional, may appear anywhere among the `case` labels (though convention places it last), and behaves exactly like any other `case` body once entered — including participating in fall-through if it lacks a `break`.

```java
int score = 55;
switch (score / 10) {
    case 10:
    case 9:
        System.out.println("A");
        break;
    case 8:
        System.out.println("B");
        break;
    default:
        System.out.println("F");
}
```

Here `score / 10` evaluates to `5`, which matches none of `10`, `9`, or `8`, so control jumps to `default:` and prints `"F"`.

## 2. Why & when

`default` exists to give a `switch` an explicit fallback so that unexpected or out-of-range values are handled deliberately rather than silently ignored:

- **Catching genuinely unexpected input** — logging or rejecting a value nobody planned for, instead of letting the switch do nothing.
- **Providing a sensible fallback behavior** — e.g., treating any unrecognized command the same way ("show help").
- **Surfacing bugs early** — a `default` that throws an exception turns "this should never happen" into a loud failure instead of a silent no-op, which is invaluable while a codebase is still evolving.

Omitting `default` is reasonable only when every possible value of the switch expression is provably covered by explicit `case` labels — for example, switching over every constant of a small `enum`. Even then, many teams still add a `default` that throws, as insurance against a new enum constant being added later without updating every switch that handles it.

## 3. Core concept

```java
public class DefaultCaseDemo {
    public static void main(String[] args) {
        int[] inputs = { 1, 2, 99 };

        for (int input : inputs) {
            switch (input) {
                case 1:
                    System.out.println("One");
                    break;
                case 2:
                    System.out.println("Two");
                    break;
                default:
                    System.out.println("Unrecognized value: " + input);
            }
        }
    }
}
```

Without the `default:` branch, the call with `99` would simply produce no output at all — the switch would silently do nothing, which is often worse than an explicit "I don't know what this is" message.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Default case diagram: switch expression value 99 is compared against case 1 and case 2, matches neither, so control falls to the default label and prints an unrecognized value message.">
  <rect x="8" y="8" width="684" height="154" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">switch (input) with input = 99 — no explicit case matches</text>

  <rect x="30" y="45" width="120" height="26" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="90" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">case 1: (no match)</text>

  <rect x="170" y="45" width="120" height="26" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="230" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">case 2: (no match)</text>

  <rect x="330" y="45" width="140" height="26" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="400" y="62" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="monospace">default: MATCH ✓</text>

  <path d="M 400 71 L 400 95" stroke="#6db33f" stroke-width="2" marker-end="url(#a)"/>
  <rect x="290" y="95" width="220" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="400" y="114" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">print "Unrecognized value: 99"</text>

  <text x="400" y="145" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">default acts as the catch-all when nothing else matches.</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

`default` is reached only after every explicit `case` label has failed to match.

## 5. Runnable example

Scenario: a small vending machine that maps a numeric button code to a product name — starting basic, then adding a fallback for unknown buttons, then hardening it so unexpected codes are treated as a real error condition rather than a message.

### Level 1 — Basic

```java
public class VendingBasic {
    public static void main(String[] args) {
        int button = 1;

        switch (button) {
            case 1:
                System.out.println("Dispensing: Water");
                break;
            case 2:
                System.out.println("Dispensing: Soda");
                break;
        }
    }
}
```

**How to run:** `java VendingBasic.java`

With `button = 1`, this matches `case 1:` and prints `"Dispensing: Water"`. There is no `default`, so if `button` were, say, `5`, the switch would simply do nothing — no output, no error — which is a silent failure mode worth noticing before adding safety nets.

### Level 2 — Intermediate

Same vending machine, now iterating over several button codes and adding a `default` so unknown codes get an explicit, visible response instead of silence.

```java
public class VendingIntermediate {
    public static void main(String[] args) {
        int[] buttons = { 1, 2, 5 };

        for (int button : buttons) {
            switch (button) {
                case 1:
                    System.out.println("Dispensing: Water");
                    break;
                case 2:
                    System.out.println("Dispensing: Soda");
                    break;
                default:
                    System.out.println("Button " + button + " is not wired to any product.");
            }
        }
    }
}
```

**How to run:** `java VendingIntermediate.java`

Adding `default:` turns the previously silent case (`button = 5`) into a clear, visible message. This is the most common and most important use of `default`: converting "nothing happened" into "here is what happened and why."

### Level 3 — Advanced

Same machine, now treating an unrecognized button as a genuine error (throwing an exception) rather than merely printing a message, and validating that the machine only ever proceeds with a real, known product.

```java
public class VendingAdvanced {

    static String dispense(int button) {
        switch (button) {
            case 1:
                return "Water";
            case 2:
                return "Soda";
            case 3:
                return "Chips";
            default:
                throw new IllegalArgumentException("No product mapped to button " + button);
        }
    }

    public static void main(String[] args) {
        int[] buttons = { 1, 3, 2, 42 };

        for (int button : buttons) {
            try {
                String product = dispense(button);
                System.out.println("Button " + button + " -> " + product);
            } catch (IllegalArgumentException e) {
                System.out.println("Machine fault: " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java VendingAdvanced.java`

Here `default:` no longer prints a soft warning — it `throw`s an `IllegalArgumentException`, converting an invalid button press into a hard failure that the caller must explicitly handle with a `try`/`catch`. This is a common production pattern: once code has matured past "just log it," an unmapped value in a `default` branch is usually a sign of a bug elsewhere (a new button was wired up in hardware but never added to this switch), and failing loudly surfaces that bug immediately instead of letting it hide.

## 6. Walkthrough

Trace the call `dispense(42)` from Level 3:

**Entry.** `main` iterates over `{1, 3, 2, 42}` and calls `dispense(button)` inside a `try` block for each one.

**Matching.** Inside `dispense(42)`, the `switch (button)` statement compares `42` against `case 1:`, `case 2:`, and `case 3:` in turn. None match.

**Falling to default.** Because no explicit `case` matched, control jumps to `default:`, which executes `throw new IllegalArgumentException("No product mapped to button 42");`. This immediately exits both the `switch` and the `dispense` method — `return` statements in the other branches are never relevant here since we never reached them.

**Propagation and catch.** The thrown exception propagates up to the `try`/`catch` in `main`, which catches it as `e` and prints `"Machine fault: No product mapped to button 42"`.

```
dispense(42):

switch(42) -> no case matches 1, 2, or 3
        |
        v
   default: throw IllegalArgumentException("No product mapped to button 42")
        |
        v
  caught in main's try/catch -> "Machine fault: ..." printed
```

**Final output.** For the full array `{1, 3, 2, 42}`, the program prints `Button 1 -> Water`, `Button 3 -> Chips`, `Button 2 -> Soda`, and finally `Machine fault: No product mapped to button 42` for the last, unmapped button.

## 7. Gotchas & takeaways

> **A missing `default` does not cause an error — it causes silent inaction.** If none of the `case` labels match and there is no `default`, the entire `switch` statement simply completes with no branch executed at all. This is easy to miss in testing if your test data happens to always hit a known case.

> **`default` can fall through just like any other `case`**, and it doesn't have to be the last label physically — but placing it anywhere other than last is confusing to readers and is almost always avoided by convention, even though the compiler allows it.

- `default` runs when the switch expression matches no explicit `case` label; it is optional but strongly recommended.
- Use `default` to log, provide a fallback, or (in mature code) throw an exception for values that should never legitimately occur.
- Don't rely on "there's no default so nothing bad can happen" — no default just means no branch runs, which can itself be the bug.
- Even for switches over `enum` values that appear exhaustive today, a `default` that throws is cheap insurance against a new constant being added later.
