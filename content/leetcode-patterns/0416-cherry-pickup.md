---
card: leetcode-patterns
gi: 416
slug: cherry-pickup
title: Cherry Pickup
---

## 1. What it is

Given an `n x n` grid where each cell is `0` (empty), `1` (a cherry), or `-1` (a thorn, impassable), a person walks from `(0,0)` to `(n-1,n-1)` (only right or down moves), collecting any cherry on their path, then walks BACK from `(n-1,n-1)` to `(0,0)` (only left or up moves), collecting any REMAINING cherry. Return the maximum cherries collected. Example: `grid = [[0,1,-1],[1,0,-1],[1,1,1]]` → `5`.

## 2. Why & when

Use this shape whenever a problem needs TWO separate paths across the same grid, and the paths interact (here, a cell's cherry can only be collected ONCE, even if both paths pass through it). The trick that makes this tractable: a round trip from `(0,0)` to `(n-1,n-1)` and back is EQUIVALENT to two people walking from `(0,0)` to `(n-1,n-1)` AT THE SAME TIME, taking the same total number of steps — this reframing turns a "there and back" problem into a "two synchronized walkers" grid-DP problem.

## 3. Core concept

**Key idea:** since both walkers make only right/down moves and take the same number of total steps, after `step` moves, walker 1 is at `(r1, step - r1)` and walker 2 is at `(r2, step - r2)` — so the state is fully described by `(step, r1, r2)`. Build `dp[step][r1][r2]` = the maximum cherries collected by both walkers after `step` moves each.

**Steps:**
1. Base case: `dp[0][0][0] = grid[0][0]` (both walkers start at the origin).
2. For each `step` from `1` to `2n-2`: for every `(r1, r2)` pair, compute `c1 = step - r1` and `c2 = step - r2` (the columns). Skip if either column is out of bounds, or if the underlying cell is a thorn.
3. `dp[step][r1][r2] = max` over the four combinations of "walker 1 arrived from above or from the left" AND "walker 2 arrived from above or from the left" of `dp[step-1][prev_r1][prev_r2]`, PLUS the cherry value at `(r1, c1)`, PLUS the cherry value at `(r2, c2)` ONLY IF `r1 != r2` (same cell: count it once, not twice).
4. The answer is `max(0, dp[2n-2][n-1][n-1])`.

**Why the reframing is correct:** any round trip corresponds to exactly one pair of forward paths taking the same number of steps, and vice versa — so maximizing over "two walkers moving together" explores exactly the same set of possible round trips as the original "there and back" formulation, without needing to track a full path history.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="two walkers at the same step count, columns derived from step minus row, sharing a cell means the cherry counts once">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">round trip == two walkers moving forward together, same step count</text>
    <text x="10" y="45">step = r1 + c1 = r2 + c2, so c1 = step - r1, c2 = step - r2</text>
    <text x="10" y="65">if r1 == r2 (same cell): add grid value ONCE, not twice</text>
    <rect x="10" y="85" width="320" height="24" fill="#3fb950"/><text x="170" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[step][r1][r2] tracks both walkers' combined best total</text>
  </g>
</svg>

Two walkers moving forward in lockstep explore every possible round-trip pair of paths.

## 5. Runnable example

```java
// CherryPickup.java
public class CherryPickup {

    // KEY INSIGHT: a round trip equals two forward walkers moving
    // together, same step count -- state (step, r1, r2) is enough,
    // since columns follow from step - row.

    static int cherryPickup(int[][] grid) {
        int n = grid.length;
        int[][][] dp = new int[2 * n - 1][n][n];
        for (int[][] layer : dp) for (int[] row : layer) java.util.Arrays.fill(row, Integer.MIN_VALUE);
        dp[0][0][0] = grid[0][0];

        for (int step = 1; step <= 2 * n - 2; step++) {
            for (int r1 = Math.max(0, step - n + 1); r1 <= Math.min(step, n - 1); r1++) {
                for (int r2 = r1; r2 <= Math.min(step, n - 1); r2++) {
                    int c1 = step - r1, c2 = step - r2;
                    if (c1 < 0 || c1 >= n || c2 < 0 || c2 >= n) continue;
                    if (grid[r1][c1] == -1 || grid[r2][c2] == -1) continue;

                    int best = Integer.MIN_VALUE;
                    int[] prevR1 = {r1, r1 - 1};
                    for (int pr1 : prevR1) {
                        if (pr1 < 0) continue;
                        int[] prevR2 = {r2, r2 - 1};
                        for (int pr2 : prevR2) {
                            if (pr2 < 0) continue;
                            if (dp[step - 1][pr1][pr2] != Integer.MIN_VALUE) {
                                best = Math.max(best, dp[step - 1][pr1][pr2]);
                            }
                        }
                    }
                    if (best == Integer.MIN_VALUE) continue;

                    int gain = grid[r1][c1] + (r1 == r2 ? 0 : grid[r2][c2]);
                    dp[step][r1][r2] = best + gain;
                }
            }
        }
        int result = dp[2 * n - 2][n - 1][n - 1];
        return Math.max(0, result);
    }

    public static void main(String[] args) {
        int[][] grid = {{0, 1, -1}, {1, 0, -1}, {1, 1, 1}};
        System.out.println(cherryPickup(grid));
        // 5
    }
}
```

**How to run:** `java CherryPickup.java`

## 6. Walkthrough

Trace the final steps for the `3x3` example (`n=3`, so `2n-2 = 4` total steps):

| step | r1, r2 | c1, c2 | note |
|---|---|---|---|
| 0 | 0,0 | 0,0 | dp=0 (grid[0][0]=0) |
| 2 | 1,0 | 1,2 | one walker at (1,1)=0, other at (0,2)=-1: skipped (thorn) |
| 2 | 1,1 | 1,1 | both at (1,1)=0: dp builds toward the good path down column 1 |
| 4 | 2,2 | 2,2 | both walkers meet at (2,2)=1: final cell |

The best combined total the DP finds is `5`: one walker goes down column `0` then right along row `2` (collecting `(1,0)=1`, `(2,0)=1`, `(2,1)=1`, `(2,2)=1`); the other goes right along row `0` then down column `1` (collecting `(0,1)=1`, `(1,1)=0`, then rejoining at the shared cells `(2,1)` and `(2,2)`, not double-counted). Total distinct cherries: `1+1+1+1+1 = 5`, matching the expected answer. Time complexity is O(n^3) (O(n^2) states per step, O(n) steps... more precisely O(n) steps times O(n^2) `(r1,r2)` pairs times O(4) combinations = O(n^3)). Space is O(n^3) for the full `dp` array (reducible to O(n^2) with a rolling step).

## 7. Gotchas & takeaways

> Gotcha: when `r1 == r2` (both walkers on the same cell), add that cell's cherry value ONLY ONCE — adding it twice overcounts, since the problem states a cell's cherry can only ever be collected once, no matter how many walkers pass through it.

- The reframing "round trip = two synchronized forward walkers" is the single idea that makes this problem solvable with polynomial-time DP instead of an intractable search over path pairs.
- The state needs only `(step, r1, r2)`, since `c1` and `c2` are always determined by `step - r1` and `step - r2` — tracking all four coordinates directly would be redundant.
- Related problems: Unique Paths (a single forward walker, no interaction), Dungeon Game (a single walker, but computed backward from the destination instead of forward from the start).
