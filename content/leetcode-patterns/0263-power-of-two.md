---
card: leetcode-patterns
gi: 263
slug: power-of-two
title: Power of Two
---

## 1. What it is

Given an integer `n`, return `true` if it is a power of two (`1, 2, 4, 8, 16, ...`), `false` otherwise. Example: `n = 16` → `true`; `n = 3` → `false`.

## 2. Why & when

A power of two has EXACTLY ONE set bit in its binary representation (`1 = 0001`, `2 = 0010`, `4 = 0100`, `8 = 1000`). That is precisely the condition the `n & (n - 1)` trick can check in a single O(1) operation, without any loop at all. Use this shape whenever a problem asks "is this value a power of some base-2 quantity," or more generally, "does this number have exactly one set bit."

## 3. Core concept

**Key idea:** `n & (n - 1)` clears the lowest set bit of `n`. If `n` has EXACTLY one set bit (a power of two), clearing that one bit leaves `0`. If `n` has more than one set bit, clearing just the lowest one leaves some other set bits behind, so the result is nonzero.

**Steps:**
1. If `n <= 0`, return `false` immediately (powers of two are always positive; `0` has no set bits at all, so it fails the check differently and must be excluded explicitly).
2. Compute `n & (n - 1)`.
3. Return `true` if the result is exactly `0`, `false` otherwise.

**Why it is correct:** a number has exactly one set bit if and only if it is a power of two (by definition of binary representation — `2^k` is a `1` followed by `k` zeros). `n & (n - 1) == 0` is true precisely when clearing the lowest set bit leaves nothing behind, which only happens when there was exactly one set bit to begin with. The explicit `n > 0` check is needed because `0 & (0 - 1)` also equals `0` in two's complement arithmetic, which would incorrectly pass the check for `n = 0`, a value that is not a power of two.

## 4. Diagram

<svg viewBox="0 0 460 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="n=16 is 10000, n-1 is 01111, AND gives 00000, confirming a single set bit">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">n = 16 (binary 10000)</text>
    <text x="10" y="45" font-family="monospace">n     = 10000</text>
    <text x="10" y="65" font-family="monospace">n-1   = 01111</text>
    <text x="10" y="85" fill="#3fb950" font-family="monospace">n&amp;(n-1)= 00000  (zero -&gt; power of two)</text>
    <text x="10" y="110">n = 12 (1100): n-1=1011, n&amp;(n-1)=1000 (nonzero -&gt; not a power of two)</text>
  </g>
</svg>

A single set bit clears to zero when its lowest (and only) bit is removed; more than one set bit always leaves something behind.

## 5. Runnable example

```java
// PowerOfTwo.java
public class PowerOfTwo {

    // Level 1 -- Brute force: repeatedly divide n by 2 while it is
    // even, checking if it reaches exactly 1. Correct, but O(log n)
    // iterations, and needs careful handling of the n <= 0 edge case.

    // KEY INSIGHT: a power of two has exactly one set bit, and n &
    // (n - 1) clears that one bit -- checking if the result is 0
    // answers the question in a single O(1) operation, no loop needed.

    // Level 2 -- Optimal: single-bit check via n & (n - 1).
    static boolean isPowerOfTwo(int n) {
        return n > 0 && (n & (n - 1)) == 0;
    }

    // Level 3 -- Hardened: the `n > 0` check is required, since 0 & -1
    // also equals 0 in two's-complement arithmetic, which would
    // otherwise incorrectly classify 0 as a power of two.

    public static void main(String[] args) {
        System.out.println(isPowerOfTwo(16));
        // true
        System.out.println(isPowerOfTwo(3));
        // false
        System.out.println(isPowerOfTwo(0));
        // false
        System.out.println(isPowerOfTwo(1));
        // true (2^0)
    }
}
```

**How to run:** `java PowerOfTwo.java`

## 6. Walkthrough

Trace `isPowerOfTwo(16)`: `n = 16 > 0` passes. `16` is binary `10000`, `15` is binary `01111`. `16 & 15 = 00000 = 0`. Since the result is `0`, return `true`.

Trace `isPowerOfTwo(12)`: `n = 12 > 0` passes. `12` is binary `1100`, `11` is binary `1011`. `12 & 11 = 1000 = 8`. Since the result is nonzero, return `false`.

Time complexity is O(1), a single bitwise AND and comparison. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: forgetting the `n > 0` guard causes `isPowerOfTwo(0)` to incorrectly return `true`, since `0 - 1` underflows to `-1` (all bits set in two's complement), and `0 & -1 = 0` — always test the `n = 0` edge case explicitly when using this trick.

- This is the simplest possible use of the lowest-set-bit trick: instead of counting how many times it takes to reach zero (Number of 1 Bits), you only need to check if ONE application reaches zero.
- The same trick generalizes to detecting powers of four with one extra check (single set bit, AND at an even position), though that variant needs an additional mask.
- Related problems: Number of 1 Bits (the general bit-counting version this problem specializes), Counting Bits (computes bit counts for a whole range, from which power-of-two values are exactly those with a count of 1).
