---
card: leetcode-patterns
gi: 183
slug: number-of-islands
title: Number of Islands
---

## 1. What it is

Given an `m x n` grid of `'1'`s (land) and `'0'`s (water), return the number of islands. An island is a group of `'1'`s connected 4-directionally, surrounded by water or the grid edge. Example: `grid = [["1","1","0","0"],["1","1","0","0"],["0","0","1","0"],["0","0","0","1"]]` → `3`.

## 2. Why & when

This is the pattern's namesake problem: the direct application of "scan the grid, flood fill each unvisited land cell, count how many fills happen." It is the template with nothing added — a perfect baseline before tackling variants that measure or transform each region.

## 3. Core concept

**Key idea:** scan every cell; each time an unvisited land cell is found, it must be the start of a NEW island (any island it belonged to would have already been fully visited by an earlier fill). Flood fill from there marks the whole island visited, and a counter increments once per fill.

**Steps:**
1. Scan the grid row by row, column by column.
2. When an unvisited `'1'` is found, increment the island counter.
3. Flood fill (DFS or BFS) from that cell, marking every connected `'1'` visited.
4. Continue scanning; repeat steps 2–3 for the next unvisited `'1'` found.
5. Return the total island counter after the scan completes.

**Why it is correct:** the scan-and-fill invariant guarantees that any land cell reached DURING a fill was already part of the CURRENT island being counted (via connectivity), so it can never be mistaken for a new island's start. Any land cell found UNVISITED by the outer scan must belong to a distinct, not-yet-counted island, since it was not reachable from any previously processed one.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Grid scan finds three separate unvisited land regions, each flood-filled and counted once">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="30" width="30" height="30" fill="#3fb950"/>
    <rect x="50" y="30" width="30" height="30" fill="#3fb950"/>
    <rect x="20" y="60" width="30" height="30" fill="#3fb950"/>
    <rect x="50" y="60" width="30" height="30" fill="#3fb950"/>
    <rect x="140" y="90" width="30" height="30" fill="#79c0ff"/>
    <rect x="200" y="120" width="30" height="30" fill="#e3b341"/>
    <text x="10" y="15" fill="#e6edf3">three separate connected regions -- each flood-filled and counted once -- total 3 islands</text>
  </g>
</svg>

Three distinct connected regions of land, each discovered once by the outer scan and fully consumed by one flood fill.

## 5. Runnable example

```java
// NumberOfIslands.java
public class NumberOfIslands {

    // Level 1 -- Brute force: for every land cell, run a full BFS/DFS
    // to find its ENTIRE connected region, storing all such regions in
    // a list, then deduplicate identical/overlapping regions at the
    // end. Correct, but wildly wasteful -- rediscovers the same island
    // once per cell in it instead of once total.

    // KEY INSIGHT: mark cells visited (or mutate them) THE MOMENT a
    // fill discovers them, so the outer scan naturally skips every cell
    // already claimed by an earlier fill -- turning O(cells^2) rework
    // into a single O(cells) pass.

    // Level 2 -- Optimal: scan + flood-fill + count, mutate grid to
    // mark visited.
    static int numIslands(char[][] grid) {
        int count = 0;
        for (int r = 0; r < grid.length; r++) {
            for (int c = 0; c < grid[0].length; c++) {
                if (grid[r][c] == '1') {
                    dfs(grid, r, c);
                    count++;
                }
            }
        }
        return count;
    }

    static void dfs(char[][] grid, int r, int c) {
        if (r < 0 || r >= grid.length || c < 0 || c >= grid[0].length) return;
        if (grid[r][c] != '1') return;
        grid[r][c] = '0';
        dfs(grid, r + 1, c);
        dfs(grid, r - 1, c);
        dfs(grid, r, c + 1);
        dfs(grid, r, c - 1);
    }

    // Level 3 -- Hardened: mutating the input grid works here because
    // the problem does not require preserving it; if it did, swap in a
    // separate `boolean[][] visited` array instead of overwriting
    // `grid[r][c]`.

    public static void main(String[] args) {
        System.out.println(numIslands(new char[][]{
            {'1','1','0','0'},{'1','1','0','0'},{'0','0','1','0'},{'0','0','0','1'}
        })); // 3
        System.out.println(numIslands(new char[][]{
            {'1','1','1'},{'0','1','0'},{'1','1','1'}
        })); // 1
    }
}
```

**How to run:** `java NumberOfIslands.java`

## 6. Walkthrough

Trace the example grid, scanning row by row:

| Step | Cell scanned | Action | count |
|---|---|---|---|
| 1 | (0,0) = '1' | new island; DFS marks {(0,0),(0,1),(1,0),(1,1)} as '0' | 1 |
| 2 | (0,1),(1,0),(1,1) | already '0' (visited), skip | 1 |
| 3 | (2,2) = '1' | new island; DFS marks {(2,2)} as '0' | 2 |
| 4 | (3,3) = '1' | new island; DFS marks {(3,3)} as '0' | 3 |

Final count is `3`. Time complexity is O(rows × cols), since each cell is visited a bounded number of times across the whole run; space is O(rows × cols) worst case for the DFS recursion depth on an all-land grid.

## 7. Gotchas & takeaways

> Gotcha: mutating the grid in place changes the caller's original data — if the grid must be preserved (e.g. used again later), use a separate `visited` array instead of overwriting `'1'` with `'0'`.

- The counter increments exactly once per flood-fill CALL from the outer scan, never inside the DFS/BFS helper itself.
- This is the reference/baseline problem for the whole pattern — every variant (perimeter, max area, closed islands) reuses this exact scan-and-fill skeleton with a different per-region computation.
- Related problems: Max Area of Island (track size instead of just counting), Number of Closed Islands (only count regions NOT touching the border), Number of Provinces (same idea, graph adjacency matrix instead of a grid).
