---
card: leetcode-patterns
gi: 420
slug: dp-interval-partition-template-dp-i-j-over-subintervals-try
title: "DP: Interval / Partition — template: dp[i][j] over subintervals, try every split point"
---

## 1. What it is

This page gives the one reusable template for interval-DP problems: fill `dp[i][j]` by increasing RANGE LENGTH, trying every split point `k` inside each range, and combining the two resulting sub-ranges with a boundary cost specific to the problem.

## 2. Why & when

Use this template any time you have classified a problem as interval/partition DP: a best-split-or-combine problem over a contiguous range. The only thing that changes between problems is the boundary COST function plugged into the transition — the iteration structure (by increasing length, trying every `k`) stays the same.

## 3. Core concept

**The general template.**
1. Choose the array (or a padded version of it — see the gotcha below) that the range indexes into.
2. Set base cases for the smallest ranges (usually length `1` or `2`), where no split is possible.
3. For `len` from the smallest valid range size up to the full array length: for every starting index `i` such that the range `[i, i+len-1]` (call its end `j`) fits inside the array, try every split point `k` strictly between `i` and `j`, and take the best (`min` or `max`, depending on the problem) of `dp[i][k] + dp[k][j] + cost(i, k, j)`.
4. The final answer is `dp[first][last]`, covering the entire original range.

**Why processing ranges by increasing length is required:** the transition for `dp[i][j]` reads `dp[i][k]` and `dp[k][j]`, both STRICTLY SMALLER ranges than `[i, j]`. Filling by increasing length guarantees both are already computed by the time `[i, j]` is processed — filling in any other order (e.g. by starting index alone) risks reading a cell that has not been filled in yet.

**A common trick — padding with sentinel values:** several problems (Burst Balloons, Minimum Cost to Cut a Stick) add virtual boundary values (`1`s at both ends, or `0` and `n` as extra "cut points") so that the boundary cost formula works uniformly, even for ranges touching the true edges of the original array.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ranges filled in order of increasing length, from length 1 or 2 up to the full array, each depending only on shorter ranges">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">fill order: length 1/2 first, then length 3, then length 4, ... up to n</text>
    <rect x="10" y="40" width="60" height="24" fill="#30363d" stroke="#8b949e"/><text x="40" y="57" text-anchor="middle" font-size="10">len 2</text>
    <rect x="80" y="40" width="90" height="24" fill="#30363d" stroke="#8b949e"/><text x="125" y="57" text-anchor="middle" font-size="10">len 3</text>
    <rect x="180" y="40" width="120" height="24" fill="#3fb950"/><text x="240" y="57" text-anchor="middle" font-size="10" fill="#0d1117">len 4 (full)</text>
    <rect x="10" y="75" width="300" height="24" fill="#3fb950"/><text x="160" y="92" fill="#0d1117" text-anchor="middle" font-size="10">each longer range only reads already-finished shorter ranges</text>
  </g>
</svg>

Shorter ranges are always filled before the longer ranges that depend on them.

## 5. Runnable example

```java
// IntervalPartitionTemplate.java
public class IntervalPartitionTemplate {

    // General template: dp[i][j] by increasing length, trying every
    // split point k, combining with a problem-specific boundary cost.
    static int solve(int[] values) {
        int n = values.length;
        int[][] dp = new int[n][n];
        // base case: length-2 adjacent ranges need no split (cost 0)

        for (int len = 2; len < n; len++) {
            for (int i = 0; i + len < n; i++) {
                int j = i + len;
                int best = Integer.MAX_VALUE;
                for (int k = i + 1; k < j; k++) {
                    int cost = values[i] * values[k] * values[j]; // problem-specific
                    best = Math.min(best, dp[i][k] + dp[k][j] + cost);
                }
                dp[i][j] = best;
            }
        }
        return dp[0][n - 1];
    }

    public static void main(String[] args) {
        System.out.println(solve(new int[]{3, 7, 4, 5}));
        // 144 (minimum score triangulation of this polygon)
    }
}
```

**How to run:** `java IntervalPartitionTemplate.java`

## 6. Walkthrough

1. Length-`2` ranges (`dp[i][i+1]`) start at `0`, since two adjacent points have no split to try.
2. Length-`3` ranges try exactly ONE split point (`k = i+1`), since it is the only index strictly between `i` and `j`.
3. Length-`4` ranges (the full array here) try TWO split points, each combining two already-solved shorter ranges plus the boundary cost.
4. `dp[0][3] = 144` for `values = [3,7,4,5]` confirms the template finds the correct minimum, matching the known answer for this exact triangulation problem.
5. Every problem in this section reuses this exact iteration shape; only the `cost(i, k, j)` expression, the base case, and `min` vs. `max` change.

## 7. Gotchas & takeaways

> Gotcha: forgetting to pad the array with sentinel values (where a problem calls for it, like Burst Balloons' `1`s at both ends) breaks the boundary cost formula right at the true edges of the original array — always check whether the problem's cost function needs a virtual "outside" value at position `-1` or `n`.

- The template's shape never changes: fill by increasing length, try every split point, combine two sub-ranges plus a boundary cost.
- Two-player "take from either end" games (Predict the Winner, Stone Game) simplify the inner loop to exactly two choices instead of scanning every `k` — still the same overall length-ordered structure.
- Some problems (Remove Boxes) need an EXTRA state dimension beyond `i` and `j` (like a count of attached identical boxes) — recognize when two indices are not enough to capture the sub-problem.
