---
card: leetcode-patterns
gi: 262
slug: hamming-distance
title: Hamming Distance
---

## 1. What it is

The Hamming distance between two integers is the number of positions where their binary representations differ. Given `x` and `y`, return their Hamming distance. Example: `x = 1` (binary `0001`), `y = 4` (binary `0100`) → `2` (they differ at 2 bit positions).

## 2. Why & when

This problem chains together two ideas from this section: XOR marks every DIFFERING bit position with a `1`, and the lowest-set-bit-counting trick then counts how many positions differ. Use this shape whenever a problem asks "how many bit positions differ between two numbers" — a common building block in problems about binary similarity or error-correcting codes.

## 3. Core concept

**Key idea:** `x ^ y` produces a number where bit `i` is `1` exactly when `x` and `y` differ at bit `i`, and `0` when they match at bit `i` (since XOR of two equal bits is `0`, and XOR of two different bits is `1`). Counting the set bits of `x ^ y` (using the same `n & (n - 1)` trick from Number of 1 Bits) gives the Hamming distance directly.

**Steps:**
1. Compute `diff = x ^ y`.
2. Count the set bits of `diff` using the lowest-set-bit trick: initialize `count = 0`, then while `diff != 0`, do `diff &= (diff - 1)` and `count++`.
3. Return `count`.

**Why it is correct:** XOR's definition — `1` when inputs differ, `0` when they match — turns "count the differing bit positions" directly into "count the set bits of the XOR." The bit-counting trick from Number of 1 Bits is already proven to count set bits correctly and efficiently, so combining the two operations solves this problem in a single, short pipeline.

## 4. Diagram

<svg viewBox="0 0 460 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="x=0001, y=0100, XOR=0101, two set bits mark the two differing positions">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">x = 0001, y = 0100</text>
    <text x="10" y="45" font-family="monospace">x     = 0001</text>
    <text x="10" y="65" font-family="monospace">y     = 0100</text>
    <text x="10" y="85" fill="#3fb950" font-family="monospace">x ^ y = 0101  (2 set bits = 2 differing positions)</text>
    <text x="10" y="110">Hamming distance = 2</text>
  </g>
</svg>

XOR marks every differing bit position with a 1; counting those 1s gives the Hamming distance in one step.

## 5. Runnable example

```java
// HammingDistance.java
public class HammingDistance {

    // Level 1 -- Brute force: loop over all 32 bit positions,
    // comparing (x >> i) & 1 to (y >> i) & 1 directly, counting
    // mismatches. Correct, and still O(1) since 32 is fixed, but does
    // more explicit comparison work than combining XOR with the
    // lowest-set-bit trick.

    // KEY INSIGHT: x ^ y already marks every differing bit with a 1
    // and every matching bit with a 0 -- counting its set bits (via
    // the n & (n-1) trick) directly gives the Hamming distance.

    // Level 2 -- Optimal: XOR, then count set bits.
    static int hammingDistance(int x, int y) {
        int diff = x ^ y;
        int count = 0;
        while (diff != 0) {
            diff &= (diff - 1);
            count++;
        }
        return count;
    }

    // Level 3 -- Hardened: works unchanged for x == y (diff becomes 0,
    // loop never runs, correctly returns 0) and for negative inputs
    // (XOR and the bit-clearing trick both operate on the raw
    // two's-complement bit pattern regardless of sign).

    public static void main(String[] args) {
        System.out.println(hammingDistance(1, 4));
        // 2
        System.out.println(hammingDistance(3, 1));
        // 1
    }
}
```

**How to run:** `java HammingDistance.java`

## 6. Walkthrough

Trace `hammingDistance(1, 4)`:

| Step | Value (binary) |
|---|---|
| x | 0001 |
| y | 0100 |
| diff = x ^ y | 0101 |

Counting set bits of `0101`: `0101 & 0100 = 0100` (count=1), `0100 & 0011 = 0000` (count=2). Final `count = 2`, matching the expected Hamming distance. Time complexity is O(1), since the bit-counting loop runs at most 32 times for a fixed-width integer. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: computing the Hamming distance by comparing decimal digit-by-digit (thinking of `x` and `y` in base 10) is a common conceptual mistake — the problem is entirely about the BINARY representation, so always convert your mental model to bits first, not decimal digits.

- This problem is a clean, two-step composition of ideas already covered: XOR (to mark differences) plus the lowest-set-bit-counting loop (to count them) — no new bit trick is introduced here.
- Java's built-in `Integer.bitCount(x ^ y)` computes this in one line and is the idiomatic production choice, though explaining the manual loop demonstrates understanding of the underlying mechanism.
- Related problems: Number of 1 Bits (the bit-counting half of this solution), Single Number (a different XOR application, cancellation instead of difference-marking).
