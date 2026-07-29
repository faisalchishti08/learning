---
card: leetcode-patterns
gi: 620
slug: factorial-trailing-zeroes
title: Factorial Trailing Zeroes
---

## 1. What it is

Given an integer `n`, return the number of trailing zeroes in `n!` (`n` factorial), without actually computing the (potentially enormous) factorial value. Example: `n=5` → `1` (`5! = 120`, one trailing zero); `n=10` → `2` (`10! = 3628800`, two trailing zeroes).

## 2. Why & when

Computing `n!` directly and counting trailing zeroes fails for even moderately large `n` — factorials grow astronomically fast and quickly overflow any fixed-size numeric type. The number-theory shortcut: a trailing zero comes from a factor of `10 = 2 x 5` in the product. Since factors of `2` are always far more abundant than factors of `5` in any factorial (every other number contributes a `2`, but only every fifth number contributes a `5`), the count of trailing zeroes is determined entirely by **how many times `5` divides into the numbers `1` through `n`**.

## 3. Core concept

**Key idea:** count the total number of times `5` appears as a factor across all numbers from `1` to `n`. This is not simply "how many multiples of 5 are there," because some numbers (like `25`, `125`) contribute **more than one** factor of `5` each (`25 = 5 x 5`, contributing two factors of 5).

**Steps:**
1. Count multiples of `5` up to `n`: `n / 5` (each contributes at least one factor of 5).
2. Count multiples of `25` up to `n`: `n / 25` (each of these contributes one *additional* factor of 5, beyond the one already counted in step 1).
3. Count multiples of `125`: `n / 125` (yet another additional factor, for numbers like `125` that have three factors of 5).
4. Continue with `625, 3125, ...` (powers of `5`) until the divisor exceeds `n`. Sum all these counts.

**Why summing `n/5 + n/25 + n/125 + ...` correctly counts every factor of 5, not just distinct multiples of 5:** a number like `25` is counted once in the `n/5` term (as a multiple of 5) and once again in the `n/25` term (as a multiple of 25) — the two counts together correctly total its two factors of 5. In general, a number `k` that is divisible by `5^m` (but not `5^(m+1)`) gets counted exactly `m` times across the first `m` terms of this sum, matching its true number of factor-of-5 contributions.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Counting factors of 5 in 1..25: multiples of 5 contribute once, multiples of 25 contribute an extra time">
  <g font-family="sans-serif" font-size="12">
    <text x="150" y="20" fill="#8b949e" text-anchor="middle">multiples of 5 in [1,25]: 5,10,15,20,25 -&gt; 5 (=25/5)</text>
    <text x="530" y="20" fill="#8b949e" text-anchor="middle">multiples of 25 in [1,25]: 25 -&gt; 1 (=25/25)</text>
    <rect x="60" y="30" width="260" height="35" fill="#161b22" stroke="#3fb950"/><text x="190" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">25/5 + 25/25 = 5 + 1 = 6</text>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">25! has exactly 6 trailing zeroes (25 alone contributes 2 factors of 5)</text>
  </g>
</svg>

Each power of 5 that divides into the range `[1,n]` contributes one more count — numbers like `25` (which is `5^2`) are counted in both the `n/5` and `n/25` terms.

## 5. Runnable example

**Level 1 — Brute force.** Compute `n!` using `BigInteger` (to avoid overflow), then convert to a string and count trailing `'0'` characters. Correct, but does a huge amount of unnecessary multiplication work — computing the full factorial just to examine its trailing digits.

**KEY INSIGHT:** the number of trailing zeroes equals the number of times `10 = 2 x 5` divides the factorial, and since factors of `2` always vastly outnumber factors of `5`, only counting factors of `5` across `1..n` is needed — reducing an O(n) multiplication problem (with numbers that grow to astronomical size) to an O(log₅ n) counting problem using only small integer division.

**Level 2 — Optimal.** Sum `n/5 + n/25 + n/125 + ...` until the divisor exceeds `n`, O(log₅ n) time, O(1) space.

**Level 3 — Hardened.** Uses `long` for the divisor to avoid overflow for very large `n` (the divisor grows by a factor of 5 each iteration and could otherwise overflow `int` for `n` near `Integer.MAX_VALUE`), and correctly stops once the divisor exceeds `n`.

```java
// FactorialTrailingZeroes.java
public class FactorialTrailingZeroes {

    public static int trailingZeroes(int n) {
        int count = 0;
        for (long divisor = 5; divisor <= n; divisor *= 5) {
            count += n / divisor;
        }
        return count;
    }

    public static void main(String[] args) {
        System.out.println(trailingZeroes(5));  // 1
        System.out.println(trailingZeroes(10)); // 2
        System.out.println(trailingZeroes(25)); // 6
    }
}
```

**How to run:** save as `FactorialTrailingZeroes.java`, then run `java FactorialTrailingZeroes.java`.

## 6. Walkthrough

Dry-run `trailingZeroes(25)`:

| divisor | n / divisor | running count |
|---|---|---|
| 5 | 25/5=5 | 5 |
| 25 | 25/25=1 | 6 |
| 125 | 125 > 25, stop | 6 |

Final count: `6`. This matches direct computation: `25! = 15511210043330985984000000`, which has exactly 6 trailing zeroes.

## 7. Gotchas & takeaways

> Gotcha: using `int divisor` instead of `long divisor` in the loop can overflow for very large `n` (the divisor keeps multiplying by 5 and could exceed `Integer.MAX_VALUE` before the loop condition catches it) — using `long` for the divisor avoids this edge case.

- Signal: "count trailing zeroes in a factorial" is the count-factors-of-5 signal — factors of 2 are irrelevant since they are never the limiting factor.
- A number can contribute more than one factor of 5 (like `25`, `125`), which is why summing `n/5 + n/25 + ...` (not just counting multiples of 5 once) is necessary.
- Related problems: Count Primes (a different but related number-theory counting problem, using a sieve instead of a divisor-power sum).
