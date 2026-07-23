---
card: leetcode-patterns
gi: 271
slug: bitwise-and-of-numbers-range
title: Bitwise AND of Numbers Range
---

## 1. What it is

Given two integers `left` and `right` representing a range `[left, right]`, return the bitwise AND of ALL numbers in that range, inclusive. Example: `left = 5`, `right = 7` → `4` (AND of `5 (101)`, `6 (110)`, `7 (111)` is `100 = 4`).

## 2. Why & when

ANDing a large range of numbers together might look like it needs a loop over every value, but any bit that DIFFERS somewhere in the range gets cleared to `0` by the AND — so only the bits that are IDENTICAL across the entire range survive. Use this shape whenever a problem asks for the AND (or a similar "what's common across a range" operation) over a contiguous range of integers, since the answer is exactly the range's common binary prefix.

## 3. Core concept

**Key idea:** as numbers count up from `left` to `right`, the lower bits toggle rapidly, but the higher bits stay stable until a number crosses a power-of-two boundary. The bitwise AND of the whole range equals the COMMON PREFIX of `left` and `right`'s binary representations, with all bits after that common prefix set to `0`. Find that common prefix by repeatedly right-shifting both numbers until they become equal, counting the shifts, then shifting the result back left by that same count.

**Steps:**
1. Initialize `shift = 0`.
2. While `left != right`: right-shift both `left >>= 1` and `right >>= 1`, and increment `shift`.
3. Once `left == right`, that value IS the common prefix (with the lower `shift` bits removed).
4. Return `left << shift` (shift the common prefix back to its original bit positions, filling the removed lower bits with `0`).

**Why it is correct:** shifting both `left` and `right` right by one bit at a time simulates "zooming out" until their most significant differing bits are removed — once `left == right` after shifting, every bit from that point up is identical across the ENTIRE original range (since a common bit that survives shifting doesn't change until a boundary is crossed, and once the shifted values are equal, no boundary crossing remains ambiguous). Any bit below that common prefix must differ somewhere in the range, since incrementing an integer always eventually flips those lower bits, so the AND of the whole range clears them all to `0`.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="left=101, right=111, shift right once to 10 and 11 (still differ), shift again to 1 and 1 (equal), shift=2, result 1 shifted left 2 = 100">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">left = 5 (101), right = 7 (111)</text>
    <text x="10" y="45">shift 1: left=10 (2), right=11 (3) -- still differ</text>
    <text x="10" y="65">shift 2: left=1, right=1 -- equal! shift count = 2</text>
    <rect x="10" y="80" width="30" height="24" fill="#3fb950"/><text x="25" y="97" fill="#0d1117" text-anchor="middle" font-size="9">1</text>
    <text x="45" y="97">1 &lt;&lt; 2 = 100 = 4</text>
  </g>
</svg>

Shifting both bounds right until they match finds the shared high-order prefix; shifting that prefix back left restores it to the correct bit positions, with the volatile low bits zeroed.

## 5. Runnable example

```java
// BitwiseANDOfNumbersRange.java
public class BitwiseANDOfNumbersRange {

    // Level 1 -- Brute force: AND every number from left to right
    // together in a loop. Correct, but O(right - left) time, which is
    // far too slow when the range is huge (e.g. left=1, right=2
    // billion).

    // KEY INSIGHT: the AND of an entire range equals the common
    // binary PREFIX of left and right, with all lower bits zeroed --
    // find that prefix by shifting both numbers right until they
    // match, then shift back left.

    // Level 2 -- Optimal: find the common prefix via repeated shifts.
    static int rangeBitwiseAnd(int left, int right) {
        int shift = 0;
        while (left != right) {
            left >>= 1;
            right >>= 1;
            shift++;
        }
        return left << shift;
    }

    // Level 3 -- Hardened: works unchanged when left == right (loop
    // never runs, shift stays 0, correctly returns left itself, the
    // AND of a single-element range).

    public static void main(String[] args) {
        System.out.println(rangeBitwiseAnd(5, 7));
        // 4
        System.out.println(rangeBitwiseAnd(0, 1));
        // 0 (0 and 1 share no common high bits)
        System.out.println(rangeBitwiseAnd(8, 8));
        // 8
    }
}
```

**How to run:** `java BitwiseANDOfNumbersRange.java`

## 6. Walkthrough

Trace `rangeBitwiseAnd(5, 7)`, `left = 101`, `right = 111`:

| shift so far | left (binary) | right (binary) | equal? |
|---|---|---|---|
| 0 | 101 | 111 | no |
| 1 | 010 | 011 | no |
| 2 | 001 | 001 | yes |

Loop ends with `shift = 2`, `left = 001`. Result is `001 << 2 = 100 = 4`, matching the manually computed AND of `5, 6, 7`. Time complexity is O(log(right)), since each iteration halves the values via right shift, bounded by the bit width of the input. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: it is tempting to think the answer is just `left & right`, but that is WRONG whenever the range spans more than two numbers — the numbers strictly BETWEEN `left` and `right` can clear additional bits that `left & right` alone would miss confirming; the shift-until-equal method correctly accounts for the entire range, not just its endpoints.

- This is the second problem in this section (after Median of Two Sorted Arrays) where the key insight is about finding a shared PREFIX or partition, rather than a per-element operation.
- The number of shifts needed is at most 31 (the bit width of a 32-bit integer), so the loop is effectively O(1) in practice, even though it is described as O(log(right)).
- Related problems: Complement of Base 10 Integer (another problem about a number's exact significant bit width), Kth Smallest Number in Multiplication Table (a different problem solved by reasoning about ranges rather than individual values).
