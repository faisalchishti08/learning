---
card: leetcode-patterns
gi: 182
slug: island-perimeter
title: Island Perimeter
---

## 1. What it is

Given a grid of `0`s (water) and `1`s (land) with EXACTLY one island (no lakes, all land cells connected), return the perimeter of that island. Example: `grid = [[0,1,0,0],[1,1,1,0],[0,1,0,0],[1,1,0,0]]` → `16`.

## 2. Why & when

Each land cell contributes up to 4 units of perimeter (one per side), but any side touching ANOTHER land cell is an internal border, not perimeter. This is flood fill with a twist: instead of just marking cells visited, you accumulate a running count based on each cell's neighbors.

## 3. Core concept

**Key idea:** for every land cell, count how many of its 4 sides face water or the grid boundary — that count is its contribution to the total perimeter. Summing this over all land cells gives the island's total perimeter, since interior-facing sides (land touching land) never contribute.

**Steps:**
1. Scan every cell in the grid.
2. For each land cell (`grid[r][c] == 1`), check all 4 directions.
3. For each direction that is either out of bounds or water (`0`), add `1` to the running perimeter total.
4. Return the accumulated total after scanning the whole grid.

**Why it is correct:** every unit of perimeter is exactly one side of one land cell that does NOT border another land cell. Since the island is a single connected region with no lakes, summing "water-or-boundary-facing sides" across every land cell counts each perimeter unit exactly once, with no double-counting (land-land borders are correctly excluded since they never satisfy the water-or-boundary condition).

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each land cell contributes one perimeter unit per side facing water or the grid edge">
  <g font-family="sans-serif" font-size="12">
    <rect x="60" y="30" width="40" height="40" fill="#3fb950"/>
    <rect x="100" y="30" width="40" height="40" fill="#3fb950"/>
    <line x1="60" y1="30" x2="60" y2="70" stroke="#e3b341" stroke-width="3"/>
    <line x1="60" y1="30" x2="100" y2="30" stroke="#e3b341" stroke-width="3"/>
    <line x1="60" y1="70" x2="140" y2="70" stroke="#e3b341" stroke-width="3"/>
    <line x1="100" y1="30" x2="140" y2="30" stroke="#e3b341" stroke-width="3"/>
    <line x1="140" y1="30" x2="140" y2="70" stroke="#e3b341" stroke-width="3"/>
    <text x="10" y="15" fill="#e6edf3">gold edges = perimeter (water/boundary-facing); the shared middle edge between the two cells is NOT perimeter</text>
  </g>
</svg>

The shared edge between two adjacent land cells is internal and excluded; only edges facing water or the grid boundary count.

## 5. Runnable example

```java
// IslandPerimeter.java
public class IslandPerimeter {

    // Level 1 -- Brute force: flood fill to visit every land cell,
    // and for each one separately re-scan all 4 neighbors checking
    // in-bounds and value. Functionally identical to the optimal
    // approach here, since flood fill is not actually needed --
    // computing per-cell perimeter contribution does not require
    // connectivity information, just a direct grid scan.

    // KEY INSIGHT: perimeter is a LOCAL property of each land cell (how
    // many of its 4 sides are NOT land) -- no traversal/visited-marking
    // is needed at all, just a straightforward double loop over every
    // cell.

    // Level 2 -- Optimal: direct scan, no traversal needed.
    static int islandPerimeter(int[][] grid) {
        int perimeter = 0;
        int rows = grid.length, cols = grid[0].length;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (grid[r][c] == 1) {
                    perimeter += countExposedSides(grid, r, c);
                }
            }
        }
        return perimeter;
    }

    static int countExposedSides(int[][] grid, int r, int c) {
        int[][] dirs = {{0,1},{0,-1},{1,0},{-1,0}};
        int exposed = 0;
        for (int[] d : dirs) {
            int nr = r + d[0], nc = c + d[1];
            if (nr < 0 || nr >= grid.length || nc < 0 || nc >= grid[0].length || grid[nr][nc] == 0) {
                exposed++;
            }
        }
        return exposed;
    }

    // Level 3 -- Hardened: correctly handles a single isolated land
    // cell (perimeter 4, all sides exposed) and a fully enclosed grid
    // edge case, since bounds checks and water checks are combined in
    // one condition per direction.

    public static void main(String[] args) {
        System.out.println(islandPerimeter(new int[][]{
            {0,1,0,0},{1,1,1,0},{0,1,0,0},{1,1,0,0}
        })); // 16
        System.out.println(islandPerimeter(new int[][]{{1}})); // 4
        System.out.println(islandPerimeter(new int[][]{{1,0}})); // 4
    }
}
```

**How to run:** `java IslandPerimeter.java`

## 6. Walkthrough

Trace the cell at `(1,1)` (value `1`) in the example grid, with neighbors `(0,1)=1`, `(2,1)=1`, `(1,0)=1`, `(1,2)=1`:

| Direction | Neighbor value | Exposed? |
|---|---|---|
| up (0,1) | 1 | no |
| down (2,1) | 1 | no |
| left (1,0) | 1 | no |
| right (1,2) | 1 | no |

Cell `(1,1)` contributes `0` to the perimeter — fully surrounded by land. Compare cell `(0,1)` (value `1`), with neighbors `(0,0)=0`, `(0,2)=0`, out-of-bounds up, `(1,1)=1`: contributes `3`. Summing every land cell's contribution over the whole grid gives `16`. Time complexity is O(rows × cols), since every cell is checked once with 4 constant-time neighbor checks; space is O(1) beyond the input.

## 7. Gotchas & takeaways

> Gotcha: assuming the island might have holes (lakes) or might be disconnected changes nothing about this per-cell counting approach — but if the problem allows MULTIPLE islands, you would need to first flood fill to isolate the target one before summing.

- No `visited` array or traversal is needed here — perimeter is a purely local, per-cell computation, unlike counting or measuring connected regions.
- Out-of-bounds and "neighbor is water" are the same case for this problem — both count as an exposed side — so they can share one condition.
- Related problems: Number of Islands (needs traversal, since it counts distinct regions), Max Area of Island (needs traversal, since area is a connectivity-dependent sum).
