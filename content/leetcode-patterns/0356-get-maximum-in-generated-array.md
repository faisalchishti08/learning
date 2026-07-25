---
card: leetcode-patterns
gi: 356
slug: get-maximum-in-generated-array
title: Get Maximum in Generated Array
---

## 1. What it is

Build an array `nums` of size `n + 1` using these rules: `nums[0] = 0`, `nums[1] = 1`, and for `2 <= i <= n`: if `i` is even, `nums[i] = nums[i / 2]`; if `i` is odd, `nums[i] = nums[i / 2] + nums[i / 2 + 1]` (integer division). Return the MAXIMUM value in `nums`. Example: `n = 7` → `3` (generated array: `[0,1,1,2,1,3,2,3]`).

## 2. Why & when

This is a linear DP where each `nums[i]` depends on a SMALLER already-computed index (`i / 2`, or `i / 2` and `i / 2 + 1`), not always the immediately preceding one or two — it still belongs to the Fibonacci/Linear family because each value is built directly from a FIXED, small number of earlier values, computed once in a single forward pass. Use this shape whenever a sequence is defined by an explicit formula referencing smaller indices, rather than something you need to search for.

## 3. Core concept

**Key idea:** build `dp[i] = nums[i]` directly from the problem's own formula, filling the array from `0` up to `n` in order, and track the running maximum as you go.

**Steps:**
1. If `n == 0`, return `0` immediately (only `nums[0]` exists).
2. Create `dp[n + 1]`, with `dp[0] = 0`, `dp[1] = 1`.
3. For `i` from `2` to `n`: if `i` is even, `dp[i] = dp[i / 2]`; if `i` is odd, `dp[i] = dp[i / 2] + dp[i / 2 + 1]`.
4. Return the maximum value across `dp[0..n]`.

**Why it is correct:** this directly implements the given recurrence. Since `i / 2` and `i / 2 + 1` are always STRICTLY SMALLER than `i` for `i >= 2`, both referenced values are already computed by the time `dp[i]` is needed — filling the array in increasing index order guarantees every dependency is ready.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp array for n=7 showing dp of 5 built from dp of 2 and dp of 3">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">dp = [0,1,1,2,1,?,2,3] so far; computing dp[5] (odd)</text>
    <text x="10" y="45">dp[5] = dp[5/2] + dp[5/2+1] = dp[2] + dp[3] = 1 + 2 = 3</text>
    <rect x="10" y="65" width="240" height="24" fill="#3fb950"/><text x="130" y="82" fill="#0d1117" text-anchor="middle" font-size="10">dp[5] = 3, new running max</text>
  </g>
</svg>

Odd indices combine two smaller, already-computed values; even indices simply copy one.

## 5. Runnable example

```java
// GetMaximumInGeneratedArray.java
public class GetMaximumInGeneratedArray {

    // KEY INSIGHT: each dp[i] references only smaller, already-filled
    // indices (i/2, i/2+1) -- a single forward pass fills every value
    // in dependency order.

    static int getMaximumGenerated(int n) {
        if (n == 0) return 0;
        int[] dp = new int[n + 1];
        dp[1] = 1;
        int max = 1;

        for (int i = 2; i <= n; i++) {
            dp[i] = (i % 2 == 0) ? dp[i / 2] : dp[i / 2] + dp[i / 2 + 1];
            max = Math.max(max, dp[i]);
        }
        return max;
    }

    public static void main(String[] args) {
        System.out.println(getMaximumGenerated(7));
        // 3
        System.out.println(getMaximumGenerated(2));
        // 1
    }
}
```

**How to run:** `java GetMaximumInGeneratedArray.java`

## 6. Walkthrough

Trace `getMaximumGenerated(7)`:

| i | even/odd | formula | dp[i] |
|---|---|---|---|
| 2 | even | dp[1] | 1 |
| 3 | odd | dp[1]+dp[2] | 2 |
| 4 | even | dp[2] | 1 |
| 5 | odd | dp[2]+dp[3] | 3 |
| 6 | even | dp[3] | 2 |
| 7 | odd | dp[3]+dp[4] | 3 |

Full array: `[0,1,1,2,1,3,2,3]`, maximum `3`. Time complexity is O(n). Space is O(n) (or O(1) extra if you overwrite in place and only track the max, though the array itself is still needed for lookups).

## 7. Gotchas & takeaways

> Gotcha: using `i / 2 + 1` versus `(i + 1) / 2` for the odd case looks different but is MATHEMATICALLY IDENTICAL for odd `i` — double-check whichever form you use against the problem statement's exact wording, since a sign or rounding slip here silently reads the wrong earlier index.

- Not every "small look-back" DP looks back at `i-1`/`i-2` specifically — the defining trait of this family is a SMALL, FIXED set of smaller-index dependencies, filled in one forward pass.
- The `n == 0` edge case is easy to miss, since the general loop never runs and `dp[1]` would be accessed out of bounds without the early return.
- Related problems: Climbing Stairs and Fibonacci Number (both look back at `i-1`/`i-2` specifically, the more common sub-case of this same "smaller-index dependency" family).
