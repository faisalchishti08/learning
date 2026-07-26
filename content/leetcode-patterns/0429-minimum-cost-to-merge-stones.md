---
card: leetcode-patterns
gi: 429
slug: minimum-cost-to-merge-stones
title: Minimum Cost to Merge Stones
---

## 1. What it is

Given `n` piles of stones in a row, you may merge exactly `K` CONSECUTIVE piles into one pile, paying a cost equal to the total number of stones in those `K` piles. Return the MINIMUM total cost to merge everything into ONE pile, or `-1` if it is impossible. Example: `stones = [3,2,4,1]`, `K = 2` → `20`.

## 2. Why & when

Use this shape whenever a problem merges FIXED-SIZE groups of `K` adjacent items at a time, rather than merging any two adjacent items freely. The `K`-at-a-time constraint changes both FEASIBILITY (not every `n` can be reduced to one pile) and the DP's split points (only certain range lengths are even valid intermediate states).

## 3. Core concept

**Key idea:** first check feasibility: reducing `n` piles to `1`, `K` at a time, removes `K - 1` piles per merge — so `n` must satisfy `(n - 1) % (K - 1) == 0`; otherwise, return `-1` immediately. Otherwise, build `dp[i][j]` = the minimum cost to merge `stones[i..j]` down to the FEWEST piles possible (not necessarily just one pile) using valid `K`-at-a-time merges.

**Steps:**
1. If `(n - 1) % (K - 1) != 0`, return `-1`.
2. Precompute a PREFIX SUM array, so the total stones in any range `[i, j]` is a single subtraction.
3. For each range `[i, j]` (processed by increasing length, only lengths where `(len - 1) % (K - 1) == 0` can ever fully merge to one pile — but ALL lengths need a `dp` entry for the "merge down as far as possible" sub-cost): try every split point `mid`, STEPPING BY `K - 1` (not `1`), so only VALID sub-range boundaries are considered: `dp[i][j] = min over such mid of (dp[i][mid] + dp[mid+1][j])`.
4. If `(j - i) % (K - 1) == 0` (this range CAN be merged all the way down to a single pile), ADD the range's total stone sum to `dp[i][j]` — this is the cost of the FINAL merge that combines the `K` remaining piles into one.
5. The answer is `dp[0][n-1]`.

**Why the split step size is `K - 1`, not `1`:** merging `K` piles at a time always reduces a group's pile count by multiples of `K - 1` per merge. A sub-range can only ever be reduced to exactly ONE pile if its length satisfies the same `(length - 1) % (K - 1) == 0` rule as the whole problem — stepping the split point by `K - 1` skips over invalid, unreachable intermediate boundaries, keeping the DP correct and efficient.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a range split at boundaries spaced K minus 1 apart, since merging K piles at a time only produces certain valid sub range lengths">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">K = 2 (merges are pairwise) -- split step = K - 1 = 1 (every position valid)</text>
    <text x="10" y="45">K = 3 -- split step = K - 1 = 2 (only every other position is a valid boundary)</text>
    <rect x="10" y="65" width="320" height="24" fill="#3fb950"/><text x="170" y="82" fill="#0d1117" text-anchor="middle" font-size="10">a range can fully merge to 1 pile only if (length-1) % (K-1) == 0</text>
  </g>
</svg>

Only certain range lengths can ever be reduced to a single pile, spaced by multiples of `K - 1`.

## 5. Runnable example

```java
// MinimumCostToMergeStones.java
public class MinimumCostToMergeStones {

    // KEY INSIGHT: merging K piles removes K-1 piles each time -- valid
    // split boundaries (and full single-pile merges) only occur at
    // lengths that are multiples of K-1 plus 1.

    static int mergeStones(int[] stones, int K) {
        int n = stones.length;
        if ((n - 1) % (K - 1) != 0) return -1;

        int[] prefix = new int[n + 1];
        for (int i = 0; i < n; i++) prefix[i + 1] = prefix[i] + stones[i];

        int[][] dp = new int[n][n];
        for (int len = K; len <= n; len++) {
            for (int i = 0; i + len - 1 < n; i++) {
                int j = i + len - 1;
                dp[i][j] = Integer.MAX_VALUE;
                for (int mid = i; mid < j; mid += K - 1) {
                    dp[i][j] = Math.min(dp[i][j], dp[i][mid] + dp[mid + 1][j]);
                }
                if ((len - 1) % (K - 1) == 0) {
                    dp[i][j] += prefix[j + 1] - prefix[i];
                }
            }
        }
        return dp[0][n - 1];
    }

    public static void main(String[] args) {
        System.out.println(mergeStones(new int[]{3, 2, 4, 1}, 2));
        // 20
        System.out.println(mergeStones(new int[]{3, 2, 4, 1}, 3));
        // -1
    }
}
```

**How to run:** `java MinimumCostToMergeStones.java`

## 6. Walkthrough

Trace `dp` for `stones = [3, 2, 4, 1]`, `K = 2` (so every split step is `1`, and every length can fully merge):

| range | best split | dp value (after adding range sum) |
|---|---|---|
| [0,1] | merge {3,2} | dp=0+0, +sum(5) = 5 |
| [1,2] | merge {2,4} | dp=0+0, +sum(6) = 6 |
| [2,3] | merge {4,1} | dp=0+0, +sum(5) = 5 |
| [0,2] | min(dp[0][0]+dp[1][2], dp[0][1]+dp[2][2]) = min(6,5) = 5, +sum(9) | 14 |
| [1,3] | min(dp[1][1]+dp[2][3], dp[1][2]+dp[3][3]) = min(5,6) = 5, +sum(7) | 12 |
| [0,3] | min(dp[0][0]+dp[1][3], dp[0][1]+dp[2][3], dp[0][2]+dp[3][3]) = min(12, 10, 14) = 10, +sum(10) | 20 |

`dp[0][3] = 20`, matching the expected answer. Time complexity is O(n^3 / K) (O(n^2) ranges, each trying O(n/K) split points). Space is O(n^2).

## 7. Gotchas & takeaways

> Gotcha: checking `(len - 1) % (K - 1) == 0` and adding the range's SUM must happen AFTER computing the best split — that sum represents the cost of the FINAL merge that reduces this range's piles down to exactly one, which only makes sense once the range is already reduced to `K` (or fewer, structurally guaranteed to be exactly `K`) piles.

- The feasibility check `(n - 1) % (K - 1) == 0` must run FIRST — without it, the main DP loop can silently compute a meaningless number instead of correctly reporting `-1`.
- Stepping split points by `K - 1` (not `1`) is what keeps the DP both CORRECT (skipping unreachable states) and efficient.
- Related problems: Burst Balloons and Minimum Score Triangulation (unconstrained split points, `K` effectively unlimited), Minimum Cost to Cut a Stick (a related range-merging idea, but working with CUT positions instead of stone piles).
