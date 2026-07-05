---
card: java
gi: 106
slug: division-integer-vs-float
title: Division / (integer vs float)
---

## 1. What it is

The `/` operator behaves completely differently depending on its operand types. If both operands are integer types (`int`, `long`, `short`, `byte`, `char`), `/` performs **integer division**: it truncates toward zero and discards any remainder — `7 / 2` is `3`, not `3.5`. If either operand is a floating-point type (`float` or `double`), `/` performs **floating-point division**, producing a decimal result, and division by zero produces `Infinity`/`NaN` instead of throwing. Integer division by zero, by contrast, always throws `ArithmeticException`.

```java
System.out.println(7 / 2);       // 3 (integer division, truncated)
System.out.println(7.0 / 2);     // 3.5 (float division: one operand is double)
System.out.println(7 / 2.0);     // 3.5 (float division: one operand is double)
System.out.println(-7 / 2);      // -3 (truncates toward zero, not floor: not -4)

try {
    System.out.println(7 / 0);   // throws
} catch (ArithmeticException e) {
    System.out.println("int / 0 throws: " + e.getMessage());
}
System.out.println(7.0 / 0);      // Infinity, does not throw
```

Which behavior you get is decided entirely by the *compile-time types* of the operands, not their runtime values — `int a = 7, b = 2; a / b` is always integer division, no matter what `a` and `b` happen to hold.

## 2. Why & when

Both forms of division are essential, and mixing them up is one of the most common Java bugs:

- Integer division is used for exact quantities: splitting items into groups (`totalItems / groupSize`), computing page counts, array indices.
- Floating-point division is used for ratios, percentages, and averages where fractional precision matters (`score / maxScore * 100`).

The classic bug is computing a percentage or ratio using integer division by accident: `int correct = 3, total = 4; double pct = correct / total * 100;` gives `0.0`, because `correct / total` is integer division (`3 / 4 = 0`) that happens *before* the multiplication by `100` or the assignment to `double` — the fix is to force at least one operand to be floating-point before the division happens: `(double) correct / total * 100`.

## 3. Core concept

```java
public class DivisionDemo {
    public static void main(String[] args) {
        // Integer division truncates toward zero
        System.out.println("7 / 2   = " + (7 / 2));     // 3
        System.out.println("-7 / 2  = " + (-7 / 2));     // -3, not -4 (truncation, not floor)
        System.out.println("7 / -2  = " + (7 / -2));     // -3

        // Floating-point division: any float/double operand switches the behavior
        System.out.println("7.0 / 2 = " + (7.0 / 2));     // 3.5
        System.out.println("7 / 2.0 = " + (7 / 2.0));     // 3.5

        // The classic percentage bug
        int correct = 3, total = 4;
        double buggyPct = correct / total * 100;          // int / int FIRST = 0, then * 100 = 0.0
        double fixedPct = (double) correct / total * 100;  // cast forces float division
        System.out.println("Buggy percentage: " + buggyPct);
        System.out.println("Fixed percentage: " + fixedPct);

        // Division by zero: int throws, double does not
        try {
            int x = 7 / 0;
        } catch (ArithmeticException e) {
            System.out.println("int 7/0 threw: " + e.getMessage());
        }
        System.out.println("double 7.0/0.0 = " + (7.0 / 0.0));  // Infinity
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Division diagram: correct divided by total divided by int gives zero because integer division truncates before multiplying by 100, but casting correct to double before dividing gives the correct 75 percent.">
  <rect x="8" y="8" width="684" height="174" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">correct=3, total=4 — same numbers, different division semantics</text>

  <rect x="16" y="34" width="320" height="132" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="176" y="50" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">correct / total * 100</text>
  <text x="30" y="72" fill="#e6edf3" font-size="8" font-family="monospace">3 / 4  → int division</text>
  <text x="30" y="90" fill="#79c0ff" font-size="9" font-family="monospace">= 0  (truncated, not 0.75)</text>
  <text x="30" y="108" fill="#e6edf3" font-size="8" font-family="monospace">0 * 100 = 0</text>
  <text x="30" y="128" fill="#6db33f" font-size="7.5" font-family="sans-serif">Result: 0.0 — WRONG,</text>
  <text x="30" y="142" fill="#6db33f" font-size="7.5" font-family="sans-serif">the truncation happened</text>
  <text x="30" y="154" fill="#6db33f" font-size="7.5" font-family="sans-serif">before the multiply.</text>

  <rect x="352" y="34" width="332" height="132" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="518" y="50" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">(double) correct / total * 100</text>
  <text x="366" y="72" fill="#e6edf3" font-size="8" font-family="monospace">(double) 3 → 3.0</text>
  <text x="366" y="90" fill="#e6edf3" font-size="8" font-family="monospace">3.0 / 4  → float division</text>
  <text x="366" y="108" fill="#79c0ff" font-size="9" font-family="monospace">= 0.75</text>
  <text x="366" y="126" fill="#e6edf3" font-size="8" font-family="monospace">0.75 * 100 = 75.0</text>
  <text x="366" y="146" fill="#6db33f" font-size="7.5" font-family="sans-serif">Result: 75.0 — correct.</text>
</svg>

Casting one operand to a floating-point type before the division switches the whole expression to float arithmetic.

## 5. Runnable example

Scenario: a quiz-grading tool that computes a student's score percentage and distributes items evenly among groups — one problem naturally needs integer division, the other needs floating-point division, and mixing them up produces silently wrong results.

### Level 1 — Basic

```java
public class DivisionBasic {
    public static void main(String[] args) {
        int correctAnswers = 17, totalQuestions = 20;

        // BUG: integer division happens before the percentage math
        double percentage = correctAnswers / totalQuestions * 100;
        System.out.println("Score: " + percentage + "%");   // 0.0% — wrong!

        // Grouping items: integer division IS what we want here
        int totalItems = 47, itemsPerBox = 6;
        int fullBoxes = totalItems / itemsPerBox;
        System.out.println("Full boxes: " + fullBoxes);       // 7 — correct, truncation is intended
    }
}
```

**How to run:** `java DivisionBasic.java`

`correctAnswers / totalQuestions` is `17 / 20`, both `int`, so it computes as integer division: `0` (truncated from `0.85`). Multiplying that `0` by `100` gives `0`, and only *then* is the result treated as a `double` for the assignment — far too late to recover the fractional part. The boxes calculation, by contrast, genuinely wants integer division: `47 / 6 = 7` full boxes is the correct real-world answer, with 5 items left over that a separate `%` calculation would find.

### Level 2 — Intermediate

Same grading tool, now fixed to compute percentages correctly, and extended to also report the leftover items after boxing using both `/` and `%` together.

```java
public class DivisionIntermediate {

    static double scorePercentage(int correct, int total) {
        if (total == 0) {
            throw new IllegalArgumentException("Cannot compute percentage of zero questions");
        }
        return (double) correct / total * 100;  // cast forces float division from the start
    }

    static String describeBoxes(int totalItems, int itemsPerBox) {
        int fullBoxes = totalItems / itemsPerBox;    // integer division: how many full boxes
        int leftover  = totalItems % itemsPerBox;     // remainder: items that don't fill a box
        return fullBoxes + " full boxes, " + leftover + " items left over";
    }

    public static void main(String[] args) {
        double pct = scorePercentage(17, 20);
        System.out.printf("Score: %.1f%%%n", pct);            // 85.0%

        System.out.println(describeBoxes(47, 6));               // 7 full boxes, 5 items left over

        try {
            scorePercentage(5, 0);
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java DivisionIntermediate.java`

`(double) correct / total * 100` casts `correct` to `double` *before* the division, so `correct / total` executes as floating-point division (`17.0 / 20 = 0.85`) — the subsequent multiplication by `100` then correctly yields `85.0`. `describeBoxes` deliberately uses integer `/` for `fullBoxes` (truncation is exactly the desired "how many complete boxes fit" semantics) paired with `%` for the `leftover` remainder — together they always satisfy `fullBoxes * itemsPerBox + leftover == totalItems`. The explicit `total == 0` check turns a potential `ArithmeticException` (division by zero on integers) into a clearer, intention-revealing exception at the API boundary.

### Level 3 — Advanced

Same tools combined into a batch-grading report, now handling negative adjustments (extra-credit deductions) correctly with truncation-toward-zero semantics, and using `Math.floorDiv`/`Math.floorMod` where floor semantics (rather than truncation) are actually the correct choice — for example, wrapping a zero-indexed item position around a fixed number of shelves.

```java
public class DivisionAdvanced {

    static double scorePercentage(int correct, int total) {
        if (total == 0) throw new IllegalArgumentException("total cannot be zero");
        return (double) correct / total * 100;
    }

    public static void main(String[] args) {
        // Negative adjustment: a penalty makes "correct" negative temporarily
        int rawCorrect = 18, penalty = 20, total = 20;
        int adjustedCorrect = rawCorrect - penalty; // -2 (over-penalized, hypothetically)

        // Regular / truncates toward zero: -2 / 20 = 0 (not -0.1 as an int, obviously, but watch the mixed case)
        System.out.println("Truncated: " + (adjustedCorrect / total));         // 0

        // For percentage, floating point still works correctly with negative numbers
        System.out.println("Adjusted percentage: " + scorePercentage(adjustedCorrect, total)); // -10.0%

        // Where floor semantics differ from truncation: wrapping a position around N shelves
        int position = -3, shelvesCount = 5;
        int truncatedShelf = position % shelvesCount;      // -3 (Java % keeps the sign of the dividend)
        int flooredShelf   = Math.floorMod(position, shelvesCount); // 2 (always non-negative, true "wrap")
        System.out.println("position % shelves       = " + truncatedShelf);
        System.out.println("Math.floorMod(pos, shelves) = " + flooredShelf);

        // floorDiv vs regular / for negative dividends
        System.out.println("-7 / 2            = " + (-7 / 2));               // -3 (truncation)
        System.out.println("Math.floorDiv(-7,2) = " + Math.floorDiv(-7, 2)); // -4 (floor)
    }
}
```

**How to run:** `java DivisionAdvanced.java`

`adjustedCorrect / total` is `-2 / 20`, both `int`: truncation toward zero gives `0` (the true value `-0.1` rounds toward zero, not down). The percentage calculation still works correctly for negative numbers because `(double) correct / total * 100` performs genuine floating-point division: `-2.0 / 20 * 100 = -10.0`, which correctly represents a 10% deduction. The shelf-wrapping example shows where truncating `%` gives an unwanted negative result (`-3 % 5 = -3` in Java, since `%` preserves the sign of the dividend) when what's really needed is a true mathematical "wrap around" — `Math.floorMod(-3, 5) = 2`, always non-negative for a positive modulus, is the correct tool for indexing into a fixed-size circular structure like shelves. `Math.floorDiv` is the paired operation: `-7 / 2` truncates to `-3`, but `Math.floorDiv(-7, 2)` rounds toward negative infinity, giving `-4` — the two must be used together (`floorDiv` with `floorMod`, or `/` with `%`) since mixing them breaks the identity `a == floorDiv(a,b)*b + floorMod(a,b)` (or the equivalent identity for `/` and `%`).

## 6. Walkthrough

Trace the shelf-wrapping calculation for `position = -3, shelvesCount = 5`:

**Regular `%`.** Java's `%` is defined so that `a % b` always has the same sign as `a` (the dividend), and satisfies `a == (a / b) * b + (a % b)`. For `-3 % 5`: `-3 / 5` truncates toward zero to `0`, so `-3 % 5 = -3 - (0 * 5) = -3`. This is mathematically consistent but not "wrapped" — a negative shelf index is not usable as an array index.

**`Math.floorMod`.** `Math.floorMod(a, b)` instead satisfies floor semantics: the result always has the same sign as the *divisor* `b` (when `b > 0`, the result is always in `[0, b)`). For `Math.floorMod(-3, 5)`: conceptually, this rounds `-3/5 = -0.6` down to the next lower integer, `-1` (floor, not truncation), then computes `-3 - (-1 * 5) = -3 + 5 = 2`. The result `2` is a valid, non-negative shelf index — position `-3` "wraps around" to shelf `2`, exactly like a clock face.

```
position = -3, shelvesCount = 5

Truncating %:  -3 / 5 truncates to 0   ->  -3 - (0*5)  = -3   (negative, unusable as index)
floorMod:      -3 / 5 floors to -1     ->  -3 - (-1*5) = 2    (wraps correctly, non-negative)
```

**Final output.** The program prints the truncated (unwrapped, negative) result first, then the correctly wrapped `floorMod` result, followed by the analogous `floorDiv` versus `/` comparison for `-7` and `2`, making the truncation-versus-floor distinction concrete with matching numbers.

## 7. Gotchas & takeaways

> **`int / int` truncates toward zero, not floor.** `-7 / 2` is `-3`, not `-4`. If you need floor semantics (e.g., wrapping indices, calendar math), use `Math.floorDiv` and `Math.floorMod` instead of `/` and `%`.

> **The classic percentage bug: integer division happens before you get a chance to cast.** `int a, b; double pct = a / b * 100;` computes `a / b` as integer division *first* — cast an operand explicitly and early: `(double) a / b * 100`.

- `/` means integer (truncating) division when both operands are integer types, and floating-point division the moment either operand is `float`/`double`.
- Integer division by zero always throws `ArithmeticException`; floating-point division by zero produces `Infinity`/`NaN` instead.
- Cast an operand (not the whole expression, and not after the fact) to force floating-point division: `(double) a / b`, not `(double) (a / b)`.
- Use `Math.floorDiv`/`Math.floorMod` when you need mathematical floor/wrap semantics instead of Java's default truncation-toward-zero.
