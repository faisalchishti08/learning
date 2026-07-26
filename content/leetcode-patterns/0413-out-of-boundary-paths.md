---
card: leetcode-patterns
gi: 413
slug: out-of-boundary-paths
title: Out of Boundary Paths
---

## 1. What it is

Given an `m x n` grid, a ball starts at `(startRow, startColumn)`. You may move it up, down, left, or right, at most `maxMove` times. Count how many distinct paths move the ball OUT of the grid's boundary, modulo `1_000_000_007`. Example: `m = 2, n = 2, maxMove = 2, startRow = 0, startColumn = 0` → `6`.

## 2. Why & when

Use this shape whenever a grid problem counts paths that are allowed to move in ALL FOUR directions (not just right/down), constrained by a LIMITED number of moves, and the goal is reaching a boundary condition (here, stepping off the grid) rather than a fixed target cell. The extra dimension — the number of moves used so far — is what separates this from the simpler two-direction path problems earlier in this section.

## 3. Core concept

**Key idea:** build `dp[k][r][c]` = the number of ways the ball can be sitting AT `(r, c)`, still inside the grid, after using exactly `k` moves. Every time a move would step OFF the grid, that move contributes to the answer instead of to any `dp` cell.

**Steps:**
1. Set `dp[0][startRow][startColumn] = 1` (one way to be at the start, having used zero moves), and everything else at step `0` is `0`.
2. For each step from `1` to `maxMove`: for every cell `(r, c)` with `dp[step-1][r][c] > 0`, try each of the four directions. If the resulting cell is OUT of bounds, add `dp[step-1][r][c]` to the running `answer`. Otherwise, add `dp[step-1][r][c]` to `dp[step][newR][newC]`.
3. Return `answer % 1_000_000_007` after all `maxMove` steps are processed.

**Why it is correct:** each way of being at `(r, c)` after `k-1` moves can be EXTENDED by one more move in any of four directions, and each extension is a genuinely distinct path (since the sequence of moves differs). Counting every extension that steps off the grid, at every step from `1` to `maxMove`, counts every path that exits at ANY point within the move budget — not just paths that exit on the very last move.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ball at a cell with four possible moves, one of which steps off the grid and contributes directly to the answer">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">at step k, ball at (r,c) with count dp[k-1][r][c] tries 4 moves</text>
    <rect x="150" y="40" width="60" height="30" fill="#3fb950"/><text x="180" y="60" text-anchor="middle" font-size="10" fill="#0d1117">r,c</text>
    <text x="10" y="90">up/down/left/right: 3 stay in bounds -&gt; add to dp[k][newR][newC]</text>
    <text x="10" y="110">1 direction (e.g. left, at column 0) steps off the grid -&gt; add to answer</text>
    <rect x="10" y="125" width="300" height="24" fill="#3fb950"/><text x="160" y="142" fill="#0d1117" text-anchor="middle" font-size="10">every out-of-bounds move at any step counts toward the answer</text>
  </g>
</svg>

Each move either lands on another in-grid cell (feeding the next step) or exits the grid (feeding the answer directly).

## 5. Runnable example

```java
// OutOfBoundaryPaths.java
public class OutOfBoundaryPaths {

    static final int MOD = 1_000_000_007;
    static final int[][] DIRECTIONS = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};

    // KEY INSIGHT: an out-of-bounds move at ANY step contributes to the
    // answer directly -- it does not need to be the LAST move used.

    static int findPaths(int m, int n, int maxMove, int startRow, int startColumn) {
        int[][] dp = new int[m][n];
        dp[startRow][startColumn] = 1;
        long answer = 0;

        for (int step = 1; step <= maxMove; step++) {
            int[][] next = new int[m][n];
            for (int r = 0; r < m; r++) {
                for (int c = 0; c < n; c++) {
                    if (dp[r][c] == 0) continue;
                    for (int[] d : DIRECTIONS) {
                        int nr = r + d[0], nc = c + d[1];
                        if (nr < 0 || nr >= m || nc < 0 || nc >= n) {
                            answer = (answer + dp[r][c]) % MOD;
                        } else {
                            next[nr][nc] = (next[nr][nc] + dp[r][c]) % MOD;
                        }
                    }
                }
            }
            dp = next;
        }
        return (int) answer;
    }

    public static void main(String[] args) {
        System.out.println(findPaths(2, 2, 2, 0, 0));
        // 6
    }
}
```

**How to run:** `java OutOfBoundaryPaths.java`

## 6. Walkthrough

Trace `findPaths(2, 2, 2, 0, 0)` (a 2x2 grid, ball starts at `(0,0)`):

| step | dp grid (in-bounds counts) | answer so far |
|---|---|---|
| 0 | dp[0][0]=1, rest 0 | 0 |
| 1 | dp[0][1]=1, dp[1][0]=1 (from (0,0)'s right/down moves) | 2 (from (0,0)'s up/left moves, both off-grid) |
| 2 | (values from step 1 spreading further) | 6 (adds 4 more exits from step 2) |

The final `answer = 6`, matching the expected result. Time complexity is O(maxMove · m · n) (four directions checked at every cell, every step). Space is O(m·n) with the rolling `dp`/`next` pair shown above.

## 7. Gotchas & takeaways

> Gotcha: forgetting to apply `% MOD` at EVERY addition (not just at the very end) lets `answer` or `dp` values overflow silently for larger inputs — always reduce modulo `1_000_000_007` right after each addition, not only on the final return.

- The state has an EXTRA dimension (`k`, the move count) compared to earlier problems in this section, since the ball is not just "at a cell" but "at a cell after using exactly this many moves."
- An out-of-bounds move contributes to the answer THE MOMENT it happens, at any step from `1` to `maxMove` — it is not reserved only for the final step.
- Related problems: Unique Paths and Minimum Path Sum (two directions only, no move limit, fixed start/end), Knight Dialer (a similar move-budget counting DP, but over a keypad graph instead of a grid boundary).
