---
card: leetcode-patterns
gi: 191
slug: coloring-a-border
title: Coloring A Border
---

## 1. What it is

Given a grid, a starting cell `(row, col)`, and a `color`, find the connected component containing the starting cell (cells sharing the starting cell's original value, connected 4-directionally), and recolor only the BORDER cells of that component — cells with at least one neighbor that is out of bounds or belongs to a DIFFERENT component. Return the modified grid.

## 2. Why & when

This is Flood Fill with a twist on WHAT gets recolored: instead of recoloring every cell in the region, only the boundary cells change. It requires knowing whether a cell is a border cell, which depends on comparing it to ITS OWN neighbors' original values — a comparison that becomes unreliable once cells start getting mutated mid-traversal, so a separate `visited` array is required here (unlike plain Flood Fill).

## 3. Core concept

**Key idea:** DFS from the starting cell using a `visited` array (NOT grid mutation, since the original values are needed for comparison throughout the traversal). A cell is a border cell if any of its 4 neighbors is out of bounds, or has a DIFFERENT value from the starting cell's original color, or is itself the boundary of the grid. After DFS finishes visiting the whole component, recolor exactly the cells flagged as border cells.

**Steps:**
1. Record `originalColor = grid[row][col]`.
2. DFS from `(row, col)`, marking cells visited in a separate boolean array (the grid itself stays unmodified during traversal).
3. For each visited cell, check its 4 neighbors: if any is out of bounds OR has a value different from `originalColor`, mark the CURRENT cell as a border cell.
4. Only recurse into neighbors that are in bounds, unvisited, and match `originalColor`.
5. After the DFS completes, do a second pass: recolor every cell flagged as a border cell to `color`.

**Why it is correct:** using a separate `visited` array (rather than mutating the grid) preserves the original values needed to correctly judge every cell's border status, even cells visited early in the traversal whose neighbors are checked later. Deferring the actual recoloring to a second pass ensures a cell's PRE-mutation value is what gets compared, avoiding a cell that was already recolored being mistaken for "a different color" by a still-unprocessed neighbor.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Only cells with a neighbor outside the connected component are recolored as border cells">
  <g font-family="sans-serif" font-size="12">
    <rect x="60" y="30" width="30" height="30" fill="#e3b341"/>
    <rect x="90" y="30" width="30" height="30" fill="#e3b341"/>
    <rect x="120" y="30" width="30" height="30" fill="#e3b341"/>
    <rect x="60" y="60" width="30" height="30" fill="#e3b341"/>
    <rect x="90" y="60" width="30" height="30" fill="#3fb950"/>
    <rect x="120" y="60" width="30" height="30" fill="#e3b341"/>
    <rect x="60" y="90" width="30" height="30" fill="#e3b341"/>
    <rect x="90" y="90" width="30" height="30" fill="#e3b341"/>
    <rect x="120" y="90" width="30" height="30" fill="#e3b341"/>
    <text x="10" y="15" fill="#e6edf3">3x3 region: outer ring (gold) recolored as border; center cell (green) has all same-value neighbors, stays unchanged</text>
  </g>
</svg>

The center cell has 4 same-component neighbors, so it is NOT a border cell; every outer cell has at least one differing or out-of-bounds neighbor.

## 5. Runnable example

```java
// ColoringABorder.java
public class ColoringABorder {

    // Level 1 -- Brute force: after a normal flood fill visits and
    // recolors every cell of the component (mutating the grid
    // directly), do a second scan re-checking each cell's ORIGINAL
    // neighbors from a saved COPY of the grid to determine border
    // status, then only keep the recolor for actual border cells,
    // restoring interior cells from the copy. Correct, but needs a
    // full grid copy just to remember original values.

    // KEY INSIGHT: use a `visited` boolean array (not grid mutation)
    // during the FIRST pass, so original values stay intact for every
    // neighbor comparison -- then apply the actual recoloring only in
    // a SEPARATE second pass, once border status is fully determined.

    // Level 2 -- Optimal: DFS with visited array + border flags,
    // recolor in second pass.
    static int[][] colorBorder(int[][] grid, int row, int col, int color) {
        int originalColor = grid[row][col];
        boolean[][] visited = new boolean[grid.length][grid[0].length];
        java.util.List<int[]> borderCells = new java.util.ArrayList<>();
        dfs(grid, visited, row, col, originalColor, borderCells);
        for (int[] cell : borderCells) {
            grid[cell[0]][cell[1]] = color;
        }
        return grid;
    }

    static void dfs(int[][] grid, boolean[][] visited, int r, int c, int originalColor, java.util.List<int[]> borderCells) {
        visited[r][c] = true;
        int[][] dirs = {{0,1},{0,-1},{1,0},{-1,0}};
        boolean isBorder = false;
        for (int[] d : dirs) {
            int nr = r + d[0], nc = c + d[1];
            if (nr < 0 || nr >= grid.length || nc < 0 || nc >= grid[0].length) {
                isBorder = true;
            } else if (grid[nr][nc] != originalColor) {
                isBorder = true;
            } else if (!visited[nr][nc]) {
                dfs(grid, visited, nr, nc, originalColor, borderCells);
            }
        }
        if (isBorder) borderCells.add(new int[]{r, c});
    }

    // Level 3 -- Hardened: comparing `grid[nr][nc] != originalColor`
    // works correctly even for an ALREADY-recolored neighbor from a
    // PREVIOUS call to this function, since the grid is never mutated
    // during the DFS pass itself -- only in the final recolor pass.

    public static void main(String[] args) {
        int[][] grid = {{1,1},{1,2}};
        int[][] result = colorBorder(grid, 0, 0, 3);
        for (int[] row : result) System.out.println(java.util.Arrays.toString(row));
        // [3, 3]
        // [3, 2]
    }
}
```

**How to run:** `java ColoringABorder.java`

## 6. Walkthrough

Trace `colorBorder(grid, 0, 0, 3)` on `[[1,1],[1,2]]`, `originalColor = 1`:

| Call | Cell | Neighbors checked | isBorder | Recurse into |
|---|---|---|---|---|
| dfs(0,0) | (0,0) | right=(0,1)=1 match, down=(1,0)=1 match; up/left out of bounds | true (out-of-bounds neighbors) | (0,1), (1,0) |
| dfs(0,1) | (0,1) | right out of bounds, down=(1,1)=2 mismatch | true | none new |
| dfs(1,0) | (1,0) | down out of bounds, right=(1,1)=2 mismatch | true | none new |

All 3 visited cells are flagged as border, so all become `3`; cell `(1,1)` (value `2`) is never visited since it does not match `originalColor`. Time complexity is O(rows × cols), since each cell in the component is visited once; space is O(rows × cols) for `visited` and the border list.

## 7. Gotchas & takeaways

> Gotcha: mutating `grid` directly during the DFS (instead of using a separate `visited` array and a deferred recolor pass) corrupts later border checks — an already-recolored cell's new value no longer matches `originalColor`, making its still-unvisited same-component neighbors incorrectly think they found a border.

- The two-pass structure (determine border cells first, recolor second) is required whenever a flood fill's OUTPUT would interfere with its OWN traversal condition — plain Flood Fill avoids this issue because it does not need original values after visiting a cell.
- A cell adjacent to the grid boundary (row 0, last row, column 0, last column) is automatically a border cell, since one of its 4 neighbor checks goes out of bounds.
- Related problems: Flood Fill (the base case with no border-only restriction), Surrounded Regions (also distinguishes border-connected from fully-interior cells, but with a different final action).
