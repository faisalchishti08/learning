---
card: leetcode-patterns
gi: 260
slug: counting-bits
title: Counting Bits
---

## 1. What it is

Given an integer `n`, return an array `ans` of length `n + 1`, where `ans[i]` is the number of `1` bits in the binary representation of `i`, for every `i` from `0` to `n`. Example: `n = 5` → `[0,1,1,2,1,2]` (0=`000`→0 bits, 1=`001`→1, 2=`010`→1, 3=`011`→2, 4=`100`→1, 5=`101`→2).

## 2. Why & when

Running Number of 1 Bits independently for every value from `0` to `n` works, but each call redoes work that a smaller value already computed. Recognizing that `i`'s bit count relates directly to a SMALLER value already in the output array turns this into a dynamic programming problem built on top of a bit trick. Use this shape whenever a problem asks for a bit-count (or similar property) across a whole RANGE of numbers, not just one.

## 3. Core concept

**Key idea:** for any `i > 0`, `i & (i - 1)` clears the lowest set bit of `i`, producing a SMALLER number that is guaranteed to already be in `ans` (since the array is built in increasing order). The bit count of `i` is exactly one more than the bit count of `i & (i - 1)`, because clearing the lowest set bit removes exactly one `1` bit.

**Steps:**
1. Create an array `ans` of size `n + 1`. Set `ans[0] = 0` (base case: zero has no set bits).
2. For `i` from `1` to `n`: compute `ans[i] = ans[i & (i - 1)] + 1`.
3. Return `ans`.

**Why it is correct:** `i & (i - 1)` is always strictly smaller than `i` (when `i > 0`), so by the time you compute `ans[i]`, `ans[i & (i - 1)]` has already been filled in — this is a valid bottom-up dynamic programming order. Since `i & (i - 1)` differs from `i` by exactly one cleared bit, its bit count is exactly one LESS than `i`'s, so adding `1` gives the correct count for `i`.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ans array built up to n=5, each ans[i] computed from a smaller already-known value ans[i and i-1]">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">ans = [0, 1, 1, 2, 1, 2]  (index = value)</text>
    <text x="10" y="45">i=5 (101): i&amp;(i-1) = 101 &amp; 100 = 100 = 4</text>
    <rect x="10" y="55" width="30" height="24" fill="#3fb950"/><text x="25" y="72" fill="#0d1117" text-anchor="middle" font-size="9">ans[4]=1</text>
    <text x="50" y="72">+1 = ans[5] = 2</text>
    <text x="10" y="105">i=3 (011): i&amp;(i-1) = 011 &amp; 010 = 010 = 2</text>
    <rect x="10" y="115" width="30" height="24" fill="#3fb950"/><text x="25" y="132" fill="#0d1117" text-anchor="middle" font-size="9">ans[2]=1</text>
    <text x="50" y="132">+1 = ans[3] = 2</text>
  </g>
</svg>

Every value's bit count is derived from an already-computed smaller value, one addition away.

## 5. Runnable example

```java
// CountingBits.java
public class CountingBits {

    // Level 1 -- Brute force: for each i from 0 to n, run the
    // independent Number of 1 Bits loop (n &= n-1 until 0) from
    // scratch. Correct, but O(n * average bits) -- ignores that
    // smaller values' answers are already sitting in the output array.

    // KEY INSIGHT: i & (i - 1) clears the lowest set bit, producing a
    // SMALLER number whose bit count is already known -- so ans[i] =
    // ans[i & (i-1)] + 1, a dynamic programming recurrence built on
    // the same bit trick from Number of 1 Bits.

    // Level 2 -- Optimal: bottom-up dynamic programming.
    static int[] countBits(int n) {
        int[] ans = new int[n + 1];
        for (int i = 1; i <= n; i++) {
            ans[i] = ans[i & (i - 1)] + 1;
        }
        return ans;
    }

    // Level 3 -- Hardened: works unchanged for n=0 (returns just
    // [0], since the loop from 1 to 0 never runs), and the recurrence
    // never reads an uncomputed index, since i & (i-1) is always
    // strictly less than i for i > 0.

    public static void main(String[] args) {
        System.out.println(java.util.Arrays.toString(countBits(5)));
        // [0, 1, 1, 2, 1, 2]
    }
}
```

**How to run:** `java CountingBits.java`

## 6. Walkthrough

Trace `countBits(5)`, building `ans` left to right:

| i | i (binary) | i & (i-1) | ans[i & (i-1)] | ans[i] |
|---|---|---|---|---|
| 0 | 000 | — | — | 0 (base case) |
| 1 | 001 | 000 = 0 | 0 | 1 |
| 2 | 010 | 000 = 0 | 0 | 1 |
| 3 | 011 | 010 = 2 | 1 | 2 |
| 4 | 100 | 000 = 0 | 0 | 1 |
| 5 | 101 | 100 = 4 | 1 | 2 |

Final `ans = [0,1,1,2,1,2]`, matching the expected output. Time complexity is O(n), one O(1) computation per index. Space is O(n) for the output array (required by the problem itself).

## 7. Gotchas & takeaways

> Gotcha: computing each `ans[i]` independently with the Number of 1 Bits loop is still O(n) overall in most practical inputs, but it does strictly more total work than the dynamic programming version, which does exactly ONE `&` and one addition per index — always mention the redundant-work argument when justifying the DP approach.

- This problem is a direct extension of Number of 1 Bits: instead of one bit-counting loop per query, the whole range is filled in with one O(1) step per index, reusing prior results.
- The recurrence `ans[i] = ans[i >> 1] + (i & 1)` is an equally valid alternative (based on right-shifting instead of clearing the lowest bit), and produces the same result — both are standard "bit DP" recurrences worth knowing.
- Related problems: Number of 1 Bits (the single-value version this problem builds on), Power of Two (also reads off a bit count, checking for exactly one set bit).
