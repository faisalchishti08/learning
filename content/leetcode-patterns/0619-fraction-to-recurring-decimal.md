---
card: leetcode-patterns
gi: 619
slug: fraction-to-recurring-decimal
title: Fraction to Recurring Decimal
---

## 1. What it is

Given two integers `numerator` and `denominator` representing a fraction, return it as a string in decimal form. If the decimal part repeats forever, enclose the repeating part in parentheses. Example: `numerator=1, denominator=2` → `"0.5"`; `numerator=2, denominator=1` → `"2"`; `numerator=4, denominator=333` → `"0.(012)"` (the digits `012` repeat forever).

## 2. Why & when

Long division by hand reveals the signal directly: when dividing, if a **remainder value repeats**, the resulting decimal digits from that point onward must also repeat (since the same remainder always produces the same next digit and the same next remainder). Detecting a repeated remainder — not a repeated digit — is the key insight, and a `HashMap` tracking "which position in the output string did we first see this remainder" is exactly the tool for detecting that repetition and knowing where to insert the opening parenthesis.

## 3. Core concept

**Key idea:** perform long division manually, one decimal digit at a time, using integer arithmetic (`%` and `*10` to bring down the next digit, mimicking grade-school long division). After each step, record the **remainder** and the **string position** where its corresponding digit was written. If the same remainder ever reappears, the decimal expansion has started repeating — insert `"("` at the position where that remainder was first seen, and `")"` at the end.

**Steps:**
1. Handle the sign: if exactly one of `numerator`/`denominator` is negative, the result is negative (note this, then work with absolute values from here on, being careful with `Integer.MIN_VALUE`'s absolute value overflowing `int`, so use `long`).
2. Compute the integer part: `numerator / denominator`. If there is a remainder (`numerator % denominator != 0`), a decimal point and fractional digits follow; otherwise, this integer part is the entire answer.
3. For the fractional part, track `remainder = numerator % denominator`. Use a `HashMap<Long, Integer>` mapping a remainder value to the string-builder position where its digit was appended.
4. While `remainder != 0`: if this `remainder` has been seen before (it is in the map), insert `"("` at the recorded position, append `")"` at the end, and stop. Otherwise, record the current position for this `remainder`, multiply `remainder` by `10`, append `remainder / denominator` as the next digit, and update `remainder = remainder % denominator`.

**Why tracking the remainder (not the digit) is what correctly detects a repeating cycle:** two different points in the division could coincidentally produce the same *digit* without starting a repeating cycle, but if the same *remainder* recurs, every subsequent step is fully determined and must reproduce the exact same sequence of digits and remainders as before — a repeated remainder is both necessary and sufficient for a repeating decimal cycle to have begun.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Long division for 4/333: remainder 4 repeats after three digits, marking the start of the repeating cycle">
  <g font-family="sans-serif" font-size="12">
    <text x="150" y="20" fill="#8b949e" text-anchor="middle">step: remainder -&gt; digit -&gt; new remainder</text>
    <rect x="20" y="30" width="150" height="30" fill="#161b22" stroke="#30363d"/><text x="95" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">rem=4 -&gt; digit=0 -&gt; rem=40</text>
    <rect x="190" y="30" width="150" height="30" fill="#161b22" stroke="#30363d"/><text x="265" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">rem=40 -&gt; digit=1 -&gt; rem=67</text>
    <rect x="360" y="30" width="150" height="30" fill="#161b22" stroke="#30363d"/><text x="435" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">rem=67 -&gt; digit=2 -&gt; rem=4</text>
    <rect x="530" y="30" width="150" height="30" fill="#161b22" stroke="#f0883e"/><text x="605" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">rem=4 seen before!</text>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">remainder 4 reappears - insert "(" before the digit written when rem=4 first appeared</text>
    <text x="350" y="140" fill="#8b949e" text-anchor="middle">result: "0.(012)"</text>
  </g>
</svg>

The remainder `4` reappears after producing digits `0,1,2` — since the same remainder must produce the same following digits again, this marks exactly where the repeating cycle begins.

## 5. Runnable example

**Level 1 — Brute force.** Compute the division as a `double` and format it to some fixed number of decimal places. Fails for repeating decimals in general (a `double` has limited precision and no way to represent "this part repeats forever" as a formatted string), so it does not actually solve the problem correctly.

**KEY INSIGHT:** the sequence of remainders in long division is what determines the sequence of digits — tracking each remainder's first-seen position in a map detects the exact moment a repeating cycle begins, since a repeated remainder guarantees the digits from that point on must repeat identically to before.

**Level 2 — Optimal.** Manual long division with a `HashMap<Long, Integer>` tracking remainder-to-position, O(denominator) time in the worst case (a repeating cycle can be as long as `denominator - 1` digits), O(denominator) space for the map.

**Level 3 — Hardened.** Correctly handles the sign (exactly one of numerator/denominator negative), correctly promotes to `long` to avoid overflow when negating `Integer.MIN_VALUE`, and correctly handles a zero remainder (terminating decimal, no parentheses needed).

```java
// FractionToRecurringDecimal.java
import java.util.*;

public class FractionToRecurringDecimal {

    public static String fractionToDecimal(int numerator, int denominator) {
        if (numerator == 0) return "0";

        StringBuilder result = new StringBuilder();
        if ((numerator < 0) != (denominator < 0)) {
            result.append('-');
        }

        long num = Math.abs((long) numerator);
        long den = Math.abs((long) denominator);

        result.append(num / den);
        long remainder = num % den;
        if (remainder == 0) {
            return result.toString();
        }

        result.append('.');
        Map<Long, Integer> seen = new HashMap<>();
        while (remainder != 0) {
            if (seen.containsKey(remainder)) {
                int pos = seen.get(remainder);
                result.insert(pos, "(");
                result.append(')');
                break;
            }
            seen.put(remainder, result.length());
            remainder *= 10;
            result.append(remainder / den);
            remainder %= den;
        }

        return result.toString();
    }

    public static void main(String[] args) {
        System.out.println(fractionToDecimal(1, 2));   // 0.5
        System.out.println(fractionToDecimal(2, 1));   // 2
        System.out.println(fractionToDecimal(4, 333)); // 0.(012)
    }
}
```

**How to run:** save as `FractionToRecurringDecimal.java`, then run `java FractionToRecurringDecimal.java`.

## 6. Walkthrough

Trace the fractional part of `fractionToDecimal(4, 333)` (`num/den = 0` remainder `4`, so integer part is `"0"`, then `"."`):

| step | remainder before | seen before? | recorded position | digit=remainder*10/den | remainder after |
|---|---|---|---|---|---|
| 1 | 4 | no | pos 2 (after "0.") | 40/333=0 | 40 |
| 2 | 40 | no | pos 3 | 400/333=1 | 67 |
| 3 | 67 | no | pos 4 | 670/333=2 | 4 |
| 4 | 4 | **yes**, at pos 2 | — | — | stop |

At step 4, `remainder=4` is found in the map, recorded at position `2` (right after `"0."`). Insert `"("` at position `2`, append `")"` at the end: `"0." + "(" + "012" + ")"` = `"0.(012)"`.

## 7. Gotchas & takeaways

> Gotcha: negating `numerator` or `denominator` while still an `int` overflows for `Integer.MIN_VALUE` (`-(-2147483648)` does not fit in a 32-bit `int`) — promoting to `long` (via `Math.abs((long) numerator)`) before taking the absolute value avoids this specific edge case.

- Signal: "convert a fraction to decimal, detect a repeating pattern" is the long-division-with-remainder-tracking signal — the remainder sequence, not the digit sequence, determines when a cycle begins.
- A repeating cycle can be up to `denominator - 1` digits long, so both the time and space cost scale with the denominator's magnitude.
- Related problems: Divide Two Integers (a related integer-division problem, without the decimal-expansion or repeating-cycle aspect).
