---
card: leetcode-patterns
gi: 274
slug: divide-two-integers
title: Divide Two Integers
---

## 1. What it is

Given two integers `dividend` and `divisor`, divide them without using multiplication, division, or the modulo operator, and return the quotient, truncated toward zero. Example: `dividend = 10`, `divisor = 3` → `3` (since `10 / 3 = 3.33`, truncated to `3`).

## 2. Why & when

Repeatedly subtracting `divisor` from `dividend` one at a time correctly computes division, but takes O(dividend / divisor) steps — far too slow for large inputs. Using bit shifts to subtract the LARGEST possible multiple of `divisor` at each step (doubling it repeatedly) turns this into a fast O(log) process, similar to how long division works by hand. Use this shape whenever a problem restricts you from using multiplication or division directly and needs an efficient implementation.

## 3. Core concept

**Key idea:** instead of subtracting `divisor` one copy at a time, find the largest value `divisor << k` (divisor shifted left by `k`, i.e., divisor times `2^k`) that still fits under the remaining `dividend`. Subtract that whole chunk at once, add `2^k` to the running quotient, and repeat with the smaller remaining dividend.

**Steps:**
1. Handle the sign separately: compute `negative = (dividend < 0) != (divisor < 0)`, then work with the absolute values (using `long` to safely negate `Integer.MIN_VALUE` without overflow).
2. Initialize `quotient = 0`.
3. While `dividend >= divisor`: find the largest `k` such that `divisor << k <= dividend`, by starting `k` at `0` and doubling `divisor << k` while it still fits.
4. Subtract `divisor << k` from `dividend`, and add `1 << k` to `quotient`.
5. Repeat until `dividend < divisor`.
6. Apply the sign, and clamp the result to the 32-bit signed integer range (`Integer.MIN_VALUE` to `Integer.MAX_VALUE`), per the problem's constraints.

**Why it is correct:** this is long division implemented with powers of two instead of powers of ten. Each outer loop iteration removes the LARGEST possible power-of-two multiple of `divisor` that still fits, which is the greedy, correct way to minimize the number of iterations — exactly analogous to how long division tries the largest digit at each step. Since each such removal at least roughly halves the remaining `dividend` (or makes rapid progress), the total number of outer iterations is bounded by O(log(dividend)), with an inner O(log(dividend)) doubling loop each time.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Dividend 10, divisor 3, find largest divisor shifted that fits, subtract, repeat">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">dividend = 10, divisor = 3</text>
    <text x="10" y="45">3&lt;&lt;0=3 fits, 3&lt;&lt;1=6 fits, 3&lt;&lt;2=12 doesn't fit -&gt; use k=1</text>
    <rect x="10" y="55" width="30" height="24" fill="#3fb950"/><text x="25" y="72" fill="#0d1117" text-anchor="middle" font-size="9">6</text>
    <text x="45" y="72">subtract 6, dividend=4, quotient += 2 (1&lt;&lt;1)</text>
    <text x="10" y="105">4 &gt;= 3: 3&lt;&lt;0=3 fits, 3&lt;&lt;1=6 doesn't -&gt; use k=0</text>
    <text x="10" y="125">subtract 3, dividend=1, quotient += 1 -&gt; quotient = 3</text>
  </g>
</svg>

Each pass removes the largest possible doubled chunk of the divisor at once, making rapid progress instead of subtracting one copy at a time.

## 5. Runnable example

```java
// DivideTwoIntegers.java
public class DivideTwoIntegers {

    // Level 1 -- Brute force: repeatedly subtract divisor from
    // dividend, one copy at a time, counting how many subtractions
    // succeed. Correct, but O(dividend / divisor) -- extremely slow
    // for cases like dividend=Integer.MAX_VALUE, divisor=1.

    // KEY INSIGHT: subtract the LARGEST doubled multiple of divisor
    // that still fits, using bit shifts, instead of one copy at a
    // time -- exactly how long division works with powers of two.

    // Level 2 -- Optimal: doubling-subtraction using bit shifts.
    static int divide(int dividendInt, int divisorInt) {
        if (dividendInt == Integer.MIN_VALUE && divisorInt == -1) return Integer.MAX_VALUE;

        boolean negative = (dividendInt < 0) != (divisorInt < 0);
        long dividend = Math.abs((long) dividendInt);
        long divisor = Math.abs((long) divisorInt);

        long quotient = 0;
        while (dividend >= divisor) {
            long chunk = divisor;
            long multiple = 1;
            while (dividend >= (chunk << 1)) {
                chunk <<= 1;
                multiple <<= 1;
            }
            dividend -= chunk;
            quotient += multiple;
        }

        return (int) (negative ? -quotient : quotient);
    }

    // Level 3 -- Hardened: special-cases dividendInt=Integer.MIN_VALUE
    // and divisorInt=-1 upfront, since that combination's true result
    // (2^31) overflows a 32-bit signed int, and the problem requires
    // clamping to Integer.MAX_VALUE in that case.

    public static void main(String[] args) {
        System.out.println(divide(10, 3));
        // 3
        System.out.println(divide(7, -3));
        // -2
    }
}
```

**How to run:** `java DivideTwoIntegers.java`

## 6. Walkthrough

Trace `divide(10, 3)`, `dividend = 10`, `divisor = 3`:

| outer iteration | chunk doubling | final chunk, multiple | dividend -= chunk | quotient += multiple |
|---|---|---|---|---|
| 1 | 3→6 (12 too big) | chunk=6, multiple=2 | 10-6=4 | quotient=2 |
| 2 | 3 (6 too big for 4) | chunk=3, multiple=1 | 4-3=1 | quotient=3 |

`dividend = 1 < divisor = 3`, loop ends. Final `quotient = 3`, matching `10 / 3` truncated. Time complexity is O(log²(dividend)) — the outer loop runs O(log(dividend)) times, and each inner doubling loop is also O(log(dividend)). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: negating `Integer.MIN_VALUE` directly overflows (since its magnitude, `2^31`, has no positive `int` counterpart) — always widen to `long` before taking the absolute value, and special-case the specific `Integer.MIN_VALUE / -1` combination, which is the one input whose true mathematical result cannot fit in a 32-bit signed integer at all.

- This problem is essentially binary long division: instead of trying digits `0-9` at each decimal place, you try powers of two, doubling the divisor as far as it fits before subtracting.
- Handling the sign separately (working with absolute values, then reapplying the sign at the end) simplifies the core loop significantly, avoiding sign-related edge cases inside the doubling logic itself.
- Related problems: Sum of Two Integers (another "implement arithmetic using only bit operations" problem), Sqrt(x) (a different integer-arithmetic problem, solved with binary search instead of bit shifting).
