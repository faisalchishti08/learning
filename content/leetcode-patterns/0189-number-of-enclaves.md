---
card: leetcode-patterns
gi: 189
slug: number-of-enclaves
title: Number of Enclaves
---

## 1. What it is

Given a grid of `0`s (water) and `1`s (land), an "enclave" is a land cell that CANNOT reach the grid boundary by moving 4-directionally through other land cells. Return the total NUMBER of such enclave land cells. Example: `grid = [[0,0,0,0],[1,0,1,0],[0,1,1,0],[0,0,0,0]]` → `3`.

## 2. Why & when

This is Number of Closed Islands with the answer measured in individual CELLS rather than in REGIONS — apply the exact same "remove border-connected land first" two-pass idea, then count cells instead of counting fills.

## 3. Core concept

**Key idea:** flood fill away every land region connected to the border (they can always escape, so they are not enclaves). Whatever land remains must be enclosed, since it has no path to the border — count those remaining land cells directly.

**Steps:**
1. Flood fill from every land cell on the grid's border, flipping the whole connected region it belongs to from land to water.
2. After this cleanup pass, scan the entire grid and count every remaining `1` cell — each one is, by construction, unable to reach the border.
3. Return that count.

**Why it is correct:** a land cell can reach the boundary if and only if it is in the same connected component as some border land cell — removing every border-connected component in the first pass leaves exactly the land cells with no path out. Counting them directly (no further traversal needed) gives the correct enclave total, since "count remaining land" and "count enclave cells" are the same set after the cleanup pass.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Border-connected land removed first; remaining isolated land cells counted individually as enclaves">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="20" width="200" height="140" fill="none" stroke="#30363d"/>
    <rect x="20" y="20" width="30" height="30" fill="#f85149" opacity="0.5"/>
    <text x="60" y="40" fill="#e6edf3">border land -&gt; removed</text>
    <rect x="100" y="80" width="30" height="30" fill="#3fb950"/>
    <rect x="130" y="80" width="30" height="30" fill="#3fb950"/>
    <rect x="100" y="110" width="30" height="30" fill="#3fb950"/>
    <text x="160" y="100" fill="#e6edf3">3 enclave cells</text>
    <text x="10" y="15" fill="#e6edf3">remove border-connected land, then count each remaining land cell individually</text>
  </g>
</svg>

After removing border-connected land, every remaining land cell is counted individually — the total cell count, not the region count, is the answer.

## 5. Runnable example

```java
// NumberOfEnclaves.java
public class NumberOfEnclaves {

    // Level 1 -- Brute force: for every land cell, run a separate
    // BFS/DFS checking whether ANY cell in its connected region
    // touches the border, counting it only if none do. Correct, but
    // repeats the same region's border-check once per cell in it.

    // KEY INSIGHT: removing border-connected regions FIRST (identical
    // to Number of Closed Islands) leaves only enclave cells behind --
    // counting them is then a single direct scan, no further
    // traversal needed.

    // Level 2 -- Optimal: remove border-touching land first, then
    // count remaining land cells directly.
    static int numEnclaves(int[][] grid) {
        int rows = grid.length, cols = grid[0].length;
        for (int c = 0; c < cols; c++) {
            removeLand(grid, 0, c);
            removeLand(grid, rows - 1, c);
        }
        for (int r = 0; r < rows; r++) {
            removeLand(grid, r, 0);
            removeLand(grid, r, cols - 1);
        }

        int count = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (grid[r][c] == 1) count++;
            }
        }
        return count;
    }

    static void removeLand(int[][] grid, int r, int c) {
        if (r < 0 || r >= grid.length || c < 0 || c >= grid[0].length) return;
        if (grid[r][c] != 1) return;
        grid[r][c] = 0;
        removeLand(grid, r + 1, c);
        removeLand(grid, r - 1, c);
        removeLand(grid, r, c + 1);
        removeLand(grid, r, c - 1);
    }

    // Level 3 -- Hardened: a grid where every land cell touches the
    // border correctly returns 0, since the cleanup pass removes
    // everything before the final counting scan runs.

    public static void main(String[] args) {
        System.out.println(numEnclaves(new int[][]{
            {0,0,0,0},{1,0,1,0},{0,1,1,0},{0,0,0,0}
        })); // 3
        System.out.println(numEnclaves(new int[][]{{0,1,1,0},{0,0,1,0},{0,0,1,0},{0,0,0,0}})); // 0
    }
}
```

**How to run:** `java NumberOfEnclaves.java`

## 6. Walkthrough

Trace the example `grid = [[0,0,0,0],[1,0,1,0],[0,1,1,0],[0,0,0,0]]`:

| Step | Action | Result |
|---|---|---|
| 1 | border cleanup: scan top/bottom rows and left/right columns for land, flood-fill remove each | `(1,0)` is border land, flood fill removes just `{(1,0)}` (no connected land neighbors within the interior) |
| 2 | remaining land after cleanup | `{(1,2),(2,1),(2,2)}` — the interior blob, untouched since it never reached the border |
| 3 | final scan counts remaining `1`s | count = 3 |

Result matches the expected `3`. Time complexity is O(rows × cols) across the cleanup pass and the counting scan; space is O(rows × cols) worst case for recursion depth.

## 7. Gotchas & takeaways

> Gotcha: counting land cells DURING the border-removal pass (instead of in a separate final scan) risks counting cells that later turn out to belong to a still-being-removed border region, since the removal pass and the counting pass must not interleave.

- This problem only needs a final COUNT, not connected-region tracking — simpler than Number of Closed Islands, which must count regions, not cells.
- The exact same two-pass structure (remove border-connected, then process what remains) is the reusable core shared by Surrounded Regions, Number of Closed Islands, and this problem — only the final step differs (flip values / count regions / count cells).
- Related problems: Number of Closed Islands (count regions instead of cells), Surrounded Regions (flip values instead of counting).
