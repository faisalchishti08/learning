---
card: leetcode-patterns
gi: 259
slug: number-of-1-bits
title: Number of 1 Bits
---

## 1. What it is

Given an unsigned 32-bit integer `n`, return the number of `1` bits in its binary representation (its "Hamming weight"). Example: `n = 11` (binary `00000000000000000000000000001011`) → `3`.

## 2. Why & when

This is the direct application of the lowest-set-bit trick: instead of checking all 32 bit positions one by one, you can clear one set bit per loop iteration and count how many iterations it takes. Use this shape whenever a problem needs a count of set bits, and you want the loop to run proportional to the number of SET bits, not the total bit width.

## 3. Core concept

**Key idea:** `n & (n - 1)` always clears exactly the LOWEST set bit of `n`, leaving every other bit unchanged. Repeating this operation, counting each time, until `n` becomes `0`, counts exactly how many bits were set.

**Steps:**
1. Initialize `count = 0`.
2. While `n != 0`: compute `n = n & (n - 1)` (clears the lowest set bit), then `count++`.
3. When `n` reaches `0`, return `count`.

**Why it is correct:** subtracting `1` from `n` flips every bit from the lowest set bit downward (the lowest set bit becomes `0`, and every `0` bit below it becomes `1`, due to how binary subtraction borrows). ANDing this with the original `n` keeps only the bits that were `1` in BOTH — which is every bit of `n` except that lowest set bit, now cleared. Each loop iteration removes exactly one set bit, so the loop runs exactly as many times as there are set bits.

## 4. Diagram

<svg viewBox="0 0 460 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="n=1011, n-1=1010, n and n-1 = 1010, clearing the lowest set bit">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">n = 11 (binary 1011)</text>
    <text x="10" y="45" font-family="monospace">n     = 1011</text>
    <text x="10" y="65" font-family="monospace">n-1   = 1010</text>
    <text x="10" y="85" fill="#3fb950" font-family="monospace">n&amp;(n-1)= 1010 (lowest 1 cleared, count=1)</text>
    <text x="10" y="110">repeat: 1010 -&gt; 1000 (count=2) -&gt; 0000 (count=3)</text>
  </g>
</svg>

Each application of `n & (n - 1)` strips exactly one set bit, so the loop terminates after exactly as many steps as there are 1 bits.

## 5. Runnable example

```java
// NumberOf1Bits.java
public class NumberOf1Bits {

    // Level 1 -- Brute force: loop over all 32 bit positions, checking
    // (n >> i) & 1 for each, summing the 1s. Correct, and still O(1)
    // per number since 32 is fixed, but always does exactly 32
    // iterations regardless of how many bits are actually set.

    // KEY INSIGHT: n & (n - 1) clears exactly the lowest set bit, so
    // looping until n becomes 0 only takes as many steps as there are
    // SET bits -- faster in practice for sparse numbers.

    // Level 2 -- Optimal: the lowest-set-bit-clearing loop.
    static int hammingWeight(int n) {
        int count = 0;
        while (n != 0) {
            n &= (n - 1);
            count++;
        }
        return count;
    }

    // Level 3 -- Hardened: works correctly for negative int values
    // too (Java ints are signed, but the bitwise operators treat them
    // as their raw 32-bit two's-complement pattern), since n & (n-1)
    // operates on bits directly, not on the number's signed value.

    public static void main(String[] args) {
        System.out.println(hammingWeight(11));
        // 3
        System.out.println(hammingWeight(128));
        // 1
        System.out.println(hammingWeight(-1));
        // 32 (all bits set in two's complement)
    }
}
```

**How to run:** `java NumberOf1Bits.java`

## 6. Walkthrough

Trace `hammingWeight(11)`, `n = 1011` in binary:

| n before (binary) | n - 1 (binary) | n & (n-1) (binary) | count |
|---|---|---|---|
| 1011 | 1010 | 1010 | 1 |
| 1010 | 1001 | 1000 | 2 |
| 1000 | 0111 | 0000 | 3 |

Loop ends when `n` reaches `0`. Final `count = 3`, matching the three set bits in `1011`. Time complexity is O(k), where `k` is the number of set bits (at most 32 for a 32-bit integer, so effectively O(1)). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: Java's `int` is signed, so a negative number like `-1` has ALL 32 bits set in two's-complement representation — `hammingWeight(-1)` correctly returns `32`, which can look surprising if you expect the input to always be a small positive number.

- The brute-force 32-iteration loop is also O(1) per number (since 32 is a fixed constant), so this optimization matters mainly in practice (fewer iterations for sparse numbers), not in asymptotic Big-O terms.
- Java also provides a built-in `Integer.bitCount(n)` that does exactly this — worth mentioning as the production choice, while still explaining the underlying trick in an interview.
- Related problems: Counting Bits (this same technique applied to every number from `0` to `n`, with a dynamic programming twist to avoid recomputing from scratch), Power of Two (checks if the set-bit count is exactly one).
