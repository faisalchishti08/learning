---
card: leetcode-patterns
gi: 414
slug: longest-increasing-path-in-a-matrix
title: Longest Increasing Path in a Matrix
---

## 1. What it is

Given an `m x n` integer matrix, find the length of the longest path where every step moves to a strictly LARGER neighbor (up, down, left, or right — no diagonals). Example: `matrix = [[9,9,4],[6,6,8],[2,1,1]]` → `4` (path `1 -> 2 -> 6 -> 9`).

## 2. Why & when

Use this shape whenever a grid problem asks for the longest (or best) path where movement is allowed in ALL FOUR directions, but a STRICT ordering rule (here, strictly increasing values) prevents cycles. Because values only ever increase along the path, the same cell can never be revisited, which is what makes memoized recursion — not a full graph cycle-detection algorithm — safe and correct.

## 3. Core concept

**Key idea:** let `dp[r][c]` = the length of the longest increasing path STARTING at `(r, c)`. Compute it recursively, with memoization, by checking all four neighbors.

**Steps:**
1. For each cell `(r, c)`, look at each of its four neighbors `(nr, nc)`.
2. If `matrix[nr][nc] > matrix[r][c]`, the path can extend into that neighbor: recursively compute `dp[nr][nc]`, and track the best one found.
3. `dp[r][c] = 1 + max(dp[nr][nc] over all valid, larger neighbors)`, or just `1` if no neighbor is larger.
4. Memoize every `dp[r][c]` the first time it is computed, so it is never recomputed. The answer is the MAXIMUM `dp[r][c]` over the whole grid.

**Why memoization is safe here (no cycle risk):** a path can only move to STRICTLY larger values, so it can never loop back to a cell it already visited — every recursive call chain is guaranteed to terminate. This means each cell's true answer depends only on cells with larger values, so computing `dp[r][c]` once and reusing it is always correct, regardless of the order cells are visited in.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="matrix cell exploring its four neighbors and recursing only into strictly larger ones">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">matrix = [[9,9,4],[6,6,8],[2,1,1]]</text>
    <text x="10" y="45">from (2,1)=1: neighbors are 2, 1, 6 -- only 2 and 6 are larger</text>
    <text x="10" y="65">dp(2,1) = 1 + max(dp going to 2), (dp going to 6)</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">path 1-&gt;2-&gt;6-&gt;9 gives the longest chain, length 4</text>
  </g>
</svg>

Recursion only follows edges into strictly larger neighbors, so no cell can ever be revisited.

## 5. Runnable example

```java
// LongestIncreasingPathInAMatrix.java
public class LongestIncreasingPathInAMatrix {

    static int[][] dirs = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};

    // KEY INSIGHT: values only increase along any path, so recursion
    // can never cycle back -- memoization is always safe.
    static int longestIncreasingPath(int[][] matrix) {
        int rows = matrix.length, cols = matrix[0].length;
        int[][] memo = new int[rows][cols];
        int best = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                best = Math.max(best, dfs(matrix, r, c, memo));
            }
        }
        return best;
    }

    static int dfs(int[][] matrix, int r, int c, int[][] memo) {
        if (memo[r][c] != 0) return memo[r][c];
        int rows = matrix.length, cols = matrix[0].length;
        int best = 1;
        for (int[] d : dirs) {
            int nr = r + d[0], nc = c + d[1];
            if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && matrix[nr][nc] > matrix[r][c]) {
                best = Math.max(best, 1 + dfs(matrix, nr, nc, memo));
            }
        }
        memo[r][c] = best;
        return best;
    }

    public static void main(String[] args) {
        int[][] matrix = {{9, 9, 4}, {6, 6, 8}, {2, 1, 1}};
        System.out.println(longestIncreasingPath(matrix));
        // 4
    }
}
```

**How to run:** `java LongestIncreasingPathInAMatrix.java`

## 6. Walkthrough

Trace `dfs` starting from `(2, 1)` (value `1`):

| call | value | larger neighbors | result |
|---|---|---|---|
| dfs(2,1) | 1 | (2,0)=2, (1,1)=6 | 1 + max(dfs(2,0), dfs(1,1)) |
| dfs(2,0) | 2 | (1,0)=6 | 1 + dfs(1,0) |
| dfs(1,0) | 6 | (0,0)=9 | 1 + dfs(0,0) |
| dfs(0,0) | 9 | none larger | 1 |

Unwinding: `dfs(0,0)=1`, `dfs(1,0)=2`, `dfs(2,0)=3`, `dfs(2,1)=4`. The grid-wide maximum across all starting cells is `4`. Time complexity is O(m·n) (each cell computed once, thanks to memoization). Space is O(m·n) for the memo table and the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: without memoization, this becomes exponential — the same cell can be reached as a starting point of many different downstream explorations, and recomputing its full sub-path every time revisits enormous overlapping work.

- `dp[r][c] = 1 + max(dp of strictly larger neighbors)`, memoized: a graph-shaped DP, using the STRICT ordering to guarantee no cycles instead of a fixed "top and left" direction restriction.
- This differs from every earlier problem in this section by allowing movement in all four directions — the ordering constraint on VALUES, not the grid's shape, is what keeps it acyclic.
- Related problems: Unique Paths III (also explores all four directions, but backtracks with an explicit visited set instead of relying on a value ordering).
