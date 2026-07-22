---
card: leetcode-patterns
gi: 184
slug: max-area-of-island
title: Max Area of Island
---

## 1. What it is

Given a grid of `0`s and `1`s, return the area (cell count) of the LARGEST island — a group of `1`s connected 4-directionally. Return `0` if there is no island. Example: `grid = [[0,0,1,0],[0,1,1,0],[0,0,1,0],[0,0,0,0]]` → `4`.

## 2. Why & when

This is Number of Islands with the counter changed from "how many fills happened" to "how big was each fill" — the same scan-and-fill skeleton, but the flood fill now returns a size instead of just marking cells, and you track the maximum instead of a running count.

## 3. Core concept

**Key idea:** flood fill from each unvisited land cell as before, but have the DFS/BFS RETURN the number of cells it visited (its island's area), instead of just marking them. Track the maximum area seen across all fills.

**Steps:**
1. Scan every cell; when an unvisited `1` is found, call the flood-fill helper starting there.
2. The flood-fill helper marks the current cell visited, then returns `1 + the sum of the areas returned by recursing into all 4 valid neighbors`.
3. Compare the returned area against the running maximum; update the maximum if this island is larger.
4. Return the maximum area found after the full scan.

**Why it is correct:** the recursive helper's return value — `1` for itself plus the recursive area of each neighbor branch — exactly equals the total number of cells in the connected region reachable from the starting cell, since every cell in that region is visited exactly once (by the visited-marking discipline) and contributes exactly `1` to exactly one branch's return value.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each flood fill returns its region's cell count; the maximum across all fills is tracked">
  <g font-family="sans-serif" font-size="12">
    <rect x="80" y="30" width="30" height="30" fill="#3fb950"/>
    <rect x="50" y="60" width="30" height="30" fill="#3fb950"/>
    <rect x="80" y="60" width="30" height="30" fill="#3fb950"/>
    <rect x="80" y="90" width="30" height="30" fill="#3fb950"/>
    <text x="120" y="80" fill="#e6edf3">area = 4</text>
    <rect x="250" y="90" width="30" height="30" fill="#79c0ff"/>
    <text x="290" y="110" fill="#e6edf3">area = 1</text>
    <text x="10" y="15" fill="#e6edf3">two islands: sizes 4 and 1 -- max area returned is 4</text>
  </g>
</svg>

Each island's flood fill returns its own cell count; comparing all returned sizes finds the maximum.

## 5. Runnable example

```java
// MaxAreaOfIsland.java
public class MaxAreaOfIsland {

    // Level 1 -- Brute force: flood fill to find and store every
    // island as a list of its cells, then take the max of each list's
    // size after all fills complete. Correct, but storing full cell
    // lists uses more memory than needed when only the COUNT of each
    // region matters, not its actual member cells.

    // KEY INSIGHT: have the DFS/BFS helper itself RETURN a running
    // count (1 + sum of neighbor branch counts) instead of collecting
    // cells into a list -- the recursive return value naturally
    // accumulates the region's size with no extra storage.

    // Level 2 -- Optimal: DFS returns area directly.
    static int maxAreaOfIsland(int[][] grid) {
        int maxArea = 0;
        for (int r = 0; r < grid.length; r++) {
            for (int c = 0; c < grid[0].length; c++) {
                if (grid[r][c] == 1) {
                    maxArea = Math.max(maxArea, areaOfIsland(grid, r, c));
                }
            }
        }
        return maxArea;
    }

    static int areaOfIsland(int[][] grid, int r, int c) {
        if (r < 0 || r >= grid.length || c < 0 || c >= grid[0].length) return 0;
        if (grid[r][c] != 1) return 0;
        grid[r][c] = 0;
        return 1
            + areaOfIsland(grid, r + 1, c)
            + areaOfIsland(grid, r - 1, c)
            + areaOfIsland(grid, r, c + 1)
            + areaOfIsland(grid, r, c - 1);
    }

    // Level 3 -- Hardened: an all-water grid correctly returns 0
    // (maxArea never updated), and a single-cell island correctly
    // returns 1 (base case: 1 + four zero-branches).

    public static void main(String[] args) {
        System.out.println(maxAreaOfIsland(new int[][]{
            {0,0,1,0},{0,1,1,0},{0,0,1,0},{0,0,0,0}
        })); // 4
        System.out.println(maxAreaOfIsland(new int[][]{{0,0,0},{0,0,0}})); // 0
        System.out.println(maxAreaOfIsland(new int[][]{{1}})); // 1
    }
}
```

**How to run:** `java MaxAreaOfIsland.java`

## 6. Walkthrough

Trace `areaOfIsland` starting at `(0,2)` on the example grid:

| Call | Cell | Own contribution | Recursion result |
|---|---|---|---|
| areaOfIsland(0,2) | (0,2) | 1 | 1 + area(1,2) |
| areaOfIsland(1,2) | (1,2) | 1 | 1 + area(2,2) + area(1,1) |
| areaOfIsland(2,2) | (2,2) | 1 | 1 (no further land neighbors) |
| areaOfIsland(1,1) | (1,1) | 1 | 1 (no further land neighbors) |

Unwinding: `area(1,2) = 1 + 1 + 1 = 3`, so `area(0,2) = 1 + 3 = 4`. Time complexity is O(rows × cols), since every cell contributes to exactly one recursive call chain; space is O(rows × cols) worst case for recursion depth.

## 7. Gotchas & takeaways

> Gotcha: forgetting the `1 +` term (only summing neighbor areas, not counting the current cell itself) undercounts every island's area by exactly the number of recursive calls made — an easy off-by-one that only shows up as a wrong total, not a crash.

- The recursive return-value accumulation pattern (`1 + sum of branches`) generalizes beyond area — it is the same shape used for counting nodes in a subtree, summing values in a tree, and similar "aggregate over a connected region" problems.
- `Math.max` is applied at the OUTER scan level, comparing across islands — not inside the recursive helper, which only computes ONE island's size per call.
- Related problems: Number of Islands (count regions, ignore size), Number of Closed Islands (filter by border-touching before counting/measuring).
