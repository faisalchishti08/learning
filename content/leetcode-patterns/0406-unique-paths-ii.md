---
card: leetcode-patterns
gi: 406
slug: unique-paths-ii
title: Unique Paths II
---

## 1. What it is

Same setup as Unique Paths, but the grid now contains OBSTACLES, marked `1` (a normal cell is `0`). Return the number of unique paths from top-left to bottom-right, moving only down or right, that never pass through an obstacle. Example: `grid = [[0,0,0],[0,1,0],[0,0,0]]` → `2`.

## 2. Why & when

Use this shape whenever a grid path-counting problem adds BLOCKED cells. Any cell marked as an obstacle can never be reached by any path — including cells that would otherwise have depended on it.

## 3. Core concept

**Key idea:** build the same `dp[r][c]` = number of ways to reach `(r, c)`, but FORCE `dp[r][c] = 0` whenever `grid[r][c]` is an obstacle, regardless of what its neighbors say.

**Steps:**
1. If `grid[0][0]` is an obstacle, return `0` immediately (no path can even start).
2. Fill the first row and first column with `1`s, but STOP early (leave the rest as `0`) the moment an obstacle is hit, since nothing past a blocked edge cell can be reached along that edge.
3. For `r` from `1` to `m-1`, for `c` from `1` to `n-1`: if `grid[r][c]` is an obstacle, `dp[r][c] = 0`; otherwise `dp[r][c] = dp[r-1][c] + dp[r][c-1]`.
4. Return `dp[m-1][n-1]`.

**Why it is correct:** an obstacle cell can never be part of any valid path, so its count must be exactly `0` — and since every other cell's count is built by SUMMING its neighbors, a `0` at an obstacle correctly stops that count from propagating any further into the grid.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="3 by 3 grid with an obstacle at the center cell, blocking counts from propagating through it">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">grid = [[0,0,0], [0,1,0], [0,0,0]] (1 = obstacle)</text>
    <text x="10" y="45">dp = [[1,1,1], [1,0,1], [1,1,2]]</text>
    <rect x="10" y="65" width="260" height="24" fill="#3fb950"/><text x="140" y="82" fill="#0d1117" text-anchor="middle" font-size="10">center cell forced to 0 -- no path can pass through it</text>
  </g>
</svg>

An obstacle cell is forced to zero, which stops its count from reaching any cell further into the grid.

## 5. Runnable example

```java
// UniquePathsII.java
public class UniquePathsII {

    // KEY INSIGHT: an obstacle cell is forced to 0, regardless of its
    // neighbors -- this correctly blocks every path that would pass
    // through it.

    static int uniquePathsWithObstacles(int[][] grid) {
        int rows = grid.length, cols = grid[0].length;
        if (grid[0][0] == 1) return 0;

        int[][] dp = new int[rows][cols];
        dp[0][0] = 1;
        for (int c = 1; c < cols; c++) {
            dp[0][c] = (grid[0][c] == 1) ? 0 : dp[0][c - 1];
        }
        for (int r = 1; r < rows; r++) {
            dp[r][0] = (grid[r][0] == 1) ? 0 : dp[r - 1][0];
        }

        for (int r = 1; r < rows; r++) {
            for (int c = 1; c < cols; c++) {
                if (grid[r][c] == 1) {
                    dp[r][c] = 0;
                } else {
                    dp[r][c] = dp[r - 1][c] + dp[r][c - 1];
                }
            }
        }
        return dp[rows - 1][cols - 1];
    }

    public static void main(String[] args) {
        System.out.println(uniquePathsWithObstacles(new int[][]{{0, 0, 0}, {0, 1, 0}, {0, 0, 0}}));
        // 2
        System.out.println(uniquePathsWithObstacles(new int[][]{{0, 1}, {0, 0}}));
        // 1
    }
}
```

**How to run:** `java UniquePathsII.java`

## 6. Walkthrough

Trace `uniquePathsWithObstacles([[0,0,0],[0,1,0],[0,0,0]])`:

| row | dp row values |
|---|---|
| 0 | [1, 1, 1] |
| 1 | [1, 0, 1] (center forced to 0) |
| 2 | [1, 1, 2] |

`dp[2][2] = dp[1][2] + dp[2][1] = 1 + 1 = 2`, matching the expected answer. Time complexity is O(m·n). Space is O(m·n) (reducible to O(n)).

## 7. Gotchas & takeaways

> Gotcha: the first row and first column need a `0`-CHECK too, not just a blanket `1` — once an obstacle appears along an edge, every cell PAST it on that same edge must also become unreachable (`0`), since there is no other way to reach them from the corner.

- `dp[r][c] = 0` on an obstacle, else the same sum as plain Unique Paths: the obstacle check is the only addition to the base template.
- If `grid[0][0]` or `grid[m-1][n-1]` itself is an obstacle, the answer is `0` immediately — handle the start cell as a special case before the main loop.
- Related problems: Unique Paths (the obstacle-free base case), Minimum Path Sum (a cost variant that could add obstacles the same way, by forcing blocked cells to infinity instead of zero).
