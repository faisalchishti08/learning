---
card: leetcode-patterns
gi: 412
slug: where-will-the-ball-fall
title: Where Will the Ball Fall
---

## 1. What it is

A grid represents a box with diagonal boards in each cell: `1` means the board deflects a ball to the RIGHT, `-1` means it deflects LEFT. For each column, drop a ball from the top and simulate it falling row by row. Return, for every starting column, the column it exits from at the bottom, or `-1` if it gets stuck. Example: `grid = [[1,1,1,-1,-1],[1,1,1,-1,-1],[-1,-1,-1,1,1],[1,1,1,1,-1],[-1,-1,-1,-1,-1]]` → `[1,-1,-1,-1,-1]`.

## 2. Why & when

Use this shape whenever a problem describes something moving row by row (or step by step) through a grid, where each cell's board or rule determines the next position DIRECTLY, with no branching choice to optimize over. It still belongs to grid-DP because the state (current column) only ever depends on the ROW ABOVE, exactly like the path problems earlier in this section — the transition is just a direct lookup instead of a `min`/`max`/sum.

## 3. Core concept

**Key idea:** for each starting column, track the ball's CURRENT column as it moves down one row at a time. At each row, look at the board there; the ball either moves to `col + 1` or `col - 1` for the next row — or gets STUCK, if either the target column is off the grid, or the ADJACENT board disagrees (forming a "V" that traps the ball).

**Steps:**
1. For each starting column `startCol` from `0` to `n-1`, set `col = startCol`.
2. For each row from `0` to `m-1`: let `d = grid[row][col]` (`1` or `-1`); let `nextCol = col + d`.
3. If `nextCol` is out of bounds, OR `grid[row][nextCol] != d` (the neighboring board points the opposite way, forming a trap), the ball is stuck: record `-1` for this starting column and stop.
4. Otherwise, set `col = nextCol` and continue to the next row. If the ball survives every row, record the final `col`.

**Why it is correct:** a ball at `(row, col)` is deflected by exactly the board at that cell, sending it to one specific neighboring column in the next row — there is no other possibility to consider, so a direct simulation (no branching search) always finds the correct outcome. The "V-trap" check (`grid[row][nextCol] != d`) is necessary because a right-deflecting board next to a left-deflecting board funnels the ball into the gap between them, where it can fall no further.

## 4. Diagram

<svg viewBox="0 0 480 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a v shaped trap where a right deflecting board sits next to a left deflecting board, catching the ball between them">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">V-trap: grid[row][col] = 1 (deflect right), grid[row][col+1] = -1 (deflect left)</text>
    <rect x="60" y="40" width="60" height="30" fill="#30363d" stroke="#8b949e"/><text x="90" y="60" text-anchor="middle" font-size="10">board: 1</text>
    <rect x="120" y="40" width="60" height="30" fill="#30363d" stroke="#8b949e"/><text x="150" y="60" text-anchor="middle" font-size="10">board: -1</text>
    <text x="60" y="90">ball enters col (left board) -&gt; wants col+1 -&gt; but col+1's board sends it back -&gt; stuck</text>
    <rect x="10" y="105" width="300" height="24" fill="#3fb950"/><text x="160" y="122" fill="#0d1117" text-anchor="middle" font-size="10">opposing boards trap the ball between them</text>
  </g>
</svg>

Two boards deflecting toward each other trap the ball in the gap between them.

## 5. Runnable example

```java
// WhereWillTheBallFall.java
public class WhereWillTheBallFall {

    // KEY INSIGHT: the ball's next column is a direct lookup from the
    // current row's board, plus a check that the neighboring board
    // agrees -- no search or optimization needed, just simulation.

    static int[] findBall(int[][] grid) {
        int rows = grid.length, cols = grid[0].length;
        int[] result = new int[cols];

        for (int startCol = 0; startCol < cols; startCol++) {
            int col = startCol;
            for (int row = 0; row < rows; row++) {
                int d = grid[row][col];
                int nextCol = col + d;
                if (nextCol < 0 || nextCol >= cols || grid[row][nextCol] != d) {
                    col = -1;
                    break;
                }
                col = nextCol;
            }
            result[startCol] = col;
        }
        return result;
    }

    public static void main(String[] args) {
        int[][] grid = {
            {1, 1, 1, -1, -1},
            {1, 1, 1, -1, -1},
            {-1, -1, -1, 1, 1},
            {1, 1, 1, 1, -1},
            {-1, -1, -1, -1, -1}
        };
        System.out.println(java.util.Arrays.toString(findBall(grid)));
        // [1, -1, -1, -1, -1]
    }
}
```

**How to run:** `java WhereWillTheBallFall.java`

## 6. Walkthrough

Trace the ball starting at column `0`:

| row | col before | board | next col | check |
|---|---|---|---|---|
| 0 | 0 | 1 | 1 | grid[0][1]=1, matches, OK |
| 1 | 1 | 1 | 2 | grid[1][2]=1, matches, OK |
| 2 | 2 | -1 | 1 | grid[2][1]=-1, matches, OK |
| 3 | 1 | 1 | 2 | grid[3][2]=1, matches, OK |
| 4 | 2 | -1 | 1 | grid[4][1]=-1, matches, OK |

The ball exits at column `1`, matching `result[0] = 1`. Time complexity is O(m·n) (each of the `n` starting columns takes O(m) rows). Space is O(n) for the output array (O(1) extra per simulation).

## 7. Gotchas & takeaways

> Gotcha: checking only `nextCol`'s bounds is not enough — you must ALSO check that `grid[row][nextCol]` agrees with the CURRENT board's direction, or a V-trap between two opposing boards is missed, and the ball is wrongly reported as passing through.

- The transition is a direct lookup, not a `min`/`max`/sum over neighbors — this still belongs to grid-DP because each row's state depends only on the row above, but the "combining rule" degenerates to a single deterministic move.
- Running one full O(m) simulation per starting column is simplest and fully sufficient at typical constraint sizes; the overall O(m·n) bound is the same order as every other problem in this section.
- Related problems: Unique Paths and Minimum Path Sum (also read only from the row above, but combine multiple neighbors instead of following one deterministic rule).
