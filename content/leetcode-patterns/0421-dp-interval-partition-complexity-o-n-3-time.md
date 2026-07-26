---
card: leetcode-patterns
gi: 421
slug: dp-interval-partition-complexity-o-n-3-time
title: "DP: Interval / Partition — complexity: O(n^3) time"
---

## 1. What it is

This page states and justifies the complexity of the interval-DP template, and lists the problems that use this pattern, so you can confirm you have picked the right tool before coding.

## 2. Why & when

Knowing the complexity upfront lets you sanity-check a proposed solution against a problem's constraints BEFORE you write code. Interval-DP problems typically cap their input size much lower than array-DP problems (often `n <= 300` or `n <= 500`), precisely BECAUSE the O(n^3) bound grows fast — `n = 500` already means over a hundred million operations.

## 3. Core concept

**Time complexity: O(n^3).** There are O(n^2) distinct ranges `[i, j]` (choosing a start and an end from `n` positions). For each range, the inner loop tries up to O(n) split points `k`. Multiplying gives O(n^2) times O(n) = O(n^3) total.

**Space complexity: O(n^2)** for the `dp[i][j]` table — one entry per range, and no reduction to O(n) is generally possible, since a range's answer can depend on split points anywhere inside it, not just on a single "previous row."

**Why some variants need MORE dimensions:** Remove Boxes needs `dp[i][j][k]`, adding a third dimension for the count of identical boxes attached to the left — this raises both the state count and the total time complexity by a factor of `n`, since `k` itself ranges up to `n`.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="n squared ranges each trying n split points multiply to n cubed total operations">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">O(n^2) ranges [i,j] -- each tries up to O(n) split points k</text>
    <rect x="10" y="40" width="300" height="24" fill="#3fb950"/><text x="160" y="57" fill="#0d1117" text-anchor="middle" font-size="10">O(n^2) * O(n) = O(n^3) total operations</text>
    <text x="10" y="85">Remove Boxes: dp[i][j][k] adds a third dimension -&gt; higher bound still</text>
  </g>
</svg>

The number of ranges times the number of split points per range gives the cubic bound.

## 5. Runnable example

```java
// IntervalPartitionComplexity.java
public class IntervalPartitionComplexity {

    // Confirms O(n^3): counts every (i, j, k) combination visited.
    static int solveCountingOps(int[] values, long[] ops) {
        int n = values.length;
        int[][] dp = new int[n][n];
        for (int len = 2; len < n; len++) {
            for (int i = 0; i + len < n; i++) {
                int j = i + len;
                int best = Integer.MAX_VALUE;
                for (int k = i + 1; k < j; k++) {
                    ops[0]++;
                    best = Math.min(best, dp[i][k] + dp[k][j] + values[i] * values[k] * values[j]);
                }
                dp[i][j] = best;
            }
        }
        return dp[0][n - 1];
    }

    public static void main(String[] args) {
        int[] values = {3, 7, 4, 5, 6};
        long[] ops = {0};
        int result = solveCountingOps(values, ops);
        System.out.println("result=" + result + " ops=" + ops[0]);
        // ops stays close to, but under, n^3 = 125
    }
}
```

**How to run:** `java IntervalPartitionComplexity.java`

## 6. Walkthrough

1. `solveCountingOps` runs the standard interval-DP template while counting every split-point check in `ops`.
2. For `n = 5`, the printed `ops` count is well under `n^3 = 125`, since the true count follows a smaller triangular-sum formula, but it clearly grows with the CUBE of `n`, not just its square.
3. Doubling `n` roughly multiplies `ops` by about `8` (`2^3`), confirming the cubic growth rate — a hallmark of interval DP that plain grid or linear DP does not share.
4. This is why interval-DP problems keep `n` small: an `n` of `500` would already push `ops` into the hundreds of millions, right at the edge of what typically fits a few seconds of runtime.
5. Compare this to grid DP's O(m·n) bound (linear in the number of cells) — interval DP is fundamentally more expensive, because every range must consider splitting at every OTHER position inside it, not just a fixed constant number of neighbors.

## 7. Gotchas & takeaways

> Gotcha: assuming interval DP scales like grid DP (O(n^2) instead of O(n^3)) leads to a wrong time-limit estimate — always multiply "number of ranges" (O(n^2)) by "split points per range" (O(n)) separately, rather than treating the range count alone as the total cost.

- Time: O(n^3) for standard two-index interval DP; space: O(n^2).
- Problems needing an extra state dimension (Remove Boxes) push the bound higher still — always check the actual number of dimensions in `dp[...]` before estimating complexity.
- Problems that use this pattern: Guess Number Higher or Lower II, Predict the Winner, Stone Game, Minimum Score Triangulation of Polygon, Burst Balloons, Strange Printer, Remove Boxes, Minimum Cost to Merge Stones, Minimum Cost to Cut a Stick.
