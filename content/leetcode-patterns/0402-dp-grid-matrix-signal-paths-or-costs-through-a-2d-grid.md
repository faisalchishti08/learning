---
card: leetcode-patterns
gi: 402
slug: dp-grid-matrix-signal-paths-or-costs-through-a-2d-grid
title: "DP: Grid / Matrix — signal: paths or costs through a 2D grid"
---

## 1. What it is

Grid (or matrix) DP is the pattern for problems that ask about paths, sums, or shapes across a 2D grid, where movement is restricted to a small set of directions (usually right and down). Each cell's answer is built from one or more NEIGHBOR cells that were already computed. Think of filling in a spreadsheet cell by cell, where each cell's formula only reads from cells above it or to its left.

## 2. Why & when

Reach for this pattern whenever a problem gives you a 2D grid and asks for a COUNT of paths, a MINIMUM or MAXIMUM cost path, or the SIZE of some shape (like a square) inside the grid. The grid itself IS the state space: every cell corresponds to one sub-problem, and the answer for the whole grid is built up from smaller, already-solved cells.

Learn to recognize these signals in a problem statement:

- **"How many unique paths from the top-left to the bottom-right corner?"** — a path-counting variant, moving only right and down.
- **"Minimum path sum from top-left to bottom-right"** or **"minimum falling path sum"** — a path-cost variant, moving right/down or into the row directly below.
- **"Adjacent numbers on the row below"** (Triangle) — the same shape, phrased as a triangle instead of a rectangle.
- **"Largest square containing only 1s"** — a shape-growing variant, where each cell's answer depends on three neighbors, not two.

The alternative — trying every possible path with plain recursion — costs exponential time, since the number of paths grows combinatorially with the grid's size. Filling a `dp` grid cell by cell reduces this to a single pass, reusing each neighbor's answer instead of recomputing it.

## 3. Core concept

Every grid-DP problem reduces to the SAME per-cell decision, using only cells already filled:

**The state.** `dp[r][c]` = the answer (a count, a minimum sum, or a shape size) for the sub-grid ending exactly at row `r`, column `c`.

**The transition.** For a plain rectangular grid, `dp[r][c]` combines `dp[r-1][c]` (the cell above) and `dp[r][c-1]` (the cell to the left) — by SUMMING them (path counting) or by taking their MINIMUM or MAXIMUM plus the current cell's own cost (path-sum problems). Triangle and falling-path variants instead read from the ROW ABOVE, at the same column and its two diagonal neighbors.

**Why the DP works:** the KEY property is that `dp[r][c]` depends only on cells with a smaller row or column index. Filling the grid row by row (or top to bottom) guarantees every dependency is ready before it is needed. The base case is the first row and first column (or the single top row of a triangle), which have no earlier neighbors to draw from.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="grid cell r c reading its value from the cell above and the cell to its left">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">grid, 3 rows x 3 cols -- filling dp[r][c] from already-computed neighbors</text>
    <rect x="150" y="40" width="60" height="30" fill="#30363d" stroke="#8b949e"/><text x="180" y="60" text-anchor="middle">dp[r-1][c]</text>
    <rect x="70" y="80" width="60" height="30" fill="#30363d" stroke="#8b949e"/><text x="100" y="100" text-anchor="middle">dp[r][c-1]</text>
    <rect x="150" y="80" width="60" height="30" fill="#3fb950"/><text x="180" y="100" text-anchor="middle" fill="#0d1117">dp[r][c]</text>
    <line x1="180" y1="70" x2="180" y2="80" stroke="#e6edf3" marker-end="url(#a)"/>
    <line x1="130" y1="95" x2="150" y2="95" stroke="#e6edf3" marker-end="url(#a)"/>
    <defs><marker id="a" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#e6edf3"/></marker></defs>
  </g>
</svg>

Each cell's value is built only from the cell above it and the cell to its left, both already filled in.

## 5. Runnable example

```java
// GridMatrixSignal.java
public class GridMatrixSignal {

    // Signal check: path-counting through a grid -- dp[r][c] sums
    // dp[r-1][c] and dp[r][c-1], with the first row/column as base cases.
    static int countPaths(int rows, int cols) {
        int[][] dp = new int[rows][cols];
        for (int r = 0; r < rows; r++) dp[r][0] = 1;
        for (int c = 0; c < cols; c++) dp[0][c] = 1;

        for (int r = 1; r < rows; r++) {
            for (int c = 1; c < cols; c++) {
                dp[r][c] = dp[r - 1][c] + dp[r][c - 1];
            }
        }
        return dp[rows - 1][cols - 1];
    }

    public static void main(String[] args) {
        System.out.println(countPaths(3, 3));
        // 6
    }
}
```

**How to run:** `java GridMatrixSignal.java`

## 6. Walkthrough

1. You read a problem statement. "Unique paths," "minimum path sum," "triangle," or "largest square" are all grid-DP signals.
2. Running `countPaths(3, 3)` confirms there are `6` distinct ways to move from the top-left to the bottom-right of a 3-by-3 grid, moving only right and down.
3. The first row and first column are filled with `1`s directly (only one way to reach any cell along an edge: keep moving in the single available direction).
4. Every interior cell then sums its top and left neighbors, since any path reaching it must have arrived from exactly one of those two cells.
5. This upfront classification (path counting vs. path cost vs. shape growing) tells you which specific transition on the next page to reach for.

## 7. Gotchas & takeaways

> Gotcha: forgetting to initialize the first row AND first column correctly (both should usually be `1` for counting, or a running sum for cost problems) breaks every cell that depends on them — the base case is not optional, since it seeds the entire grid.

- The state `dp[r][c]`, built from `dp[r-1][c]` and `dp[r][c-1]` (or the row above for triangles): the core grid-DP signal, always reading only from smaller row/column indices.
- Some variants (Maximal Square) read from THREE neighbors instead of two (top, left, and top-left diagonal) — always check exactly which neighbors a problem's transition needs before coding.
- Many grid-DP problems can shrink space from O(m·n) to O(n) using a rolling 1D array, since each row only depends on the row directly above it.
