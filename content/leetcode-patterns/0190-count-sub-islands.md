---
card: leetcode-patterns
gi: 190
slug: count-sub-islands
title: Count Sub Islands
---

## 1. What it is

Given two grids `grid1` and `grid2` of the same size, both containing `0`s (water) and `1`s (land), an island in `grid2` is a "sub-island" if every one of its land cells is ALSO land in `grid1`. Return the count of sub-islands in `grid2`. Example: `grid1 = [[1,1,1,0,0],[0,1,1,1,1],[0,0,0,0,0],[1,0,0,0,0],[1,1,0,1,1]]`, `grid2 = [[1,1,1,0,0],[0,0,1,1,1],[0,1,0,0,0],[1,0,1,1,0],[0,1,0,1,0]]` → `3`.

## 2. Why & when

This is Number of Islands with a validity condition added: instead of counting every region, count only the regions in `grid2` that fully "fit inside" the land of `grid1`. It combines flood fill's return-value pattern (like Max Area of Island) with a boolean check accumulated across the region.

## 3. Core concept

**Key idea:** flood fill each island in `grid2` as usual, but while visiting each cell, also check whether `grid1` has land there. If ANY cell in the island fails this check, the whole island is disqualified — but the flood fill must still visit every cell of the island (to mark it processed), so the check accumulates across the whole traversal rather than short-circuiting.

**Steps:**
1. Scan `grid2`; for every unvisited land cell, start a flood fill.
2. The flood-fill helper visits every cell of the region (marking each visited so it's not reprocessed), and returns `true` only if EVERY cell it visited was also land in `grid1` — computed as `isValid = grid1Match && recurse(neighbor1) && recurse(neighbor2) && ...` for all 4 neighbors, always visiting all of them regardless of an early mismatch.
3. If the flood fill's overall result is `true`, increment the sub-island counter.
4. Return the counter after the scan completes.

**Why it is correct:** the flood fill must continue into every cell of the region even after finding one mismatch, otherwise cells would be left unvisited and could incorrectly start a NEW flood fill later, corrupting the region count. Using boolean AND across the whole traversal (without short-circuit-skipping the recursive calls) ensures every cell gets marked visited while still correctly tracking whether the entire region qualifies.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An island in grid2 checked cell by cell against grid1; one mismatch disqualifies the whole island">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="30" width="30" height="30" fill="#3fb950"/>
    <rect x="50" y="30" width="30" height="30" fill="#3fb950"/>
    <rect x="20" y="60" width="30" height="30" fill="#f85149"/>
    <text x="10" y="15" fill="#e6edf3">grid2 island: two cells match grid1 (green), one does NOT (red) -- whole island disqualified</text>
  </g>
</svg>

Every cell of a `grid2` island is checked against `grid1`; even one mismatched cell disqualifies the entire island as a sub-island.

## 5. Runnable example

```java
// CountSubIslands.java
public class CountSubIslands {

    // Level 1 -- Brute force: flood fill to collect the full cell list
    // of each grid2 island first, THEN separately loop over that list
    // checking grid1 at each position. Correct, and actually similar
    // in complexity, but storing the whole cell list is unnecessary
    // when the check can be folded directly into the traversal.

    // KEY INSIGHT: accumulate the "is this a sub-island" boolean AS
    // the flood fill happens (via AND across all recursive results),
    // instead of in a separate pass -- one traversal does both jobs.

    // Level 2 -- Optimal: flood fill grid2, accumulate a boolean
    // sub-island check as it goes.
    static int countSubIslands(int[][] grid1, int[][] grid2) {
        int count = 0;
        for (int r = 0; r < grid2.length; r++) {
            for (int c = 0; c < grid2[0].length; c++) {
                if (grid2[r][c] == 1) {
                    if (dfs(grid1, grid2, r, c)) count++;
                }
            }
        }
        return count;
    }

    static boolean dfs(int[][] grid1, int[][] grid2, int r, int c) {
        if (r < 0 || r >= grid2.length || c < 0 || c >= grid2[0].length) return true;
        if (grid2[r][c] != 1) return true;
        grid2[r][c] = 0;
        boolean isValid = grid1[r][c] == 1;
        // Do NOT short-circuit -- visit all 4 neighbors regardless,
        // so every cell of the island gets marked visited.
        boolean down = dfs(grid1, grid2, r + 1, c);
        boolean up = dfs(grid1, grid2, r - 1, c);
        boolean right = dfs(grid1, grid2, r, c + 1);
        boolean left = dfs(grid1, grid2, r, c - 1);
        return isValid && down && up && right && left;
    }

    // Level 3 -- Hardened: computing all 4 recursive calls into local
    // variables BEFORE combining them with && avoids Java's
    // short-circuit evaluation skipping a neighbor visit, which would
    // otherwise leave part of the island unvisited.

    public static void main(String[] args) {
        int[][] grid1 = {{1,1,1,0,0},{0,1,1,1,1},{0,0,0,0,0},{1,0,0,0,0},{1,1,0,1,1}};
        int[][] grid2 = {{1,1,1,0,0},{0,0,1,1,1},{0,1,0,0,0},{1,0,1,1,0},{0,1,0,1,0}};
        System.out.println(countSubIslands(grid1, grid2)); // 3
    }
}
```

**How to run:** `java CountSubIslands.java`

## 6. Walkthrough

Trace the top-left island in `grid2` starting at `(0,0)` (cells `{(0,0),(0,1),(0,2)}`):

| Step | Cell | grid1 value | isValid so far |
|---|---|---|---|
| 1 | (0,0) | 1 | true |
| 2 | (0,1) | 1 | true |
| 3 | (0,2) | 1 | true |

All 4 recursive branches return `true` (out-of-bounds or non-land neighbors return `true` by the base case), so `isValid && true && true && true && true = true` — counted as a sub-island. Time complexity is O(rows × cols), since each cell is visited a bounded number of times; space is O(rows × cols) worst case for recursion depth.

## 7. Gotchas & takeaways

> Gotcha: writing `return isValid && dfs(...) && dfs(...) && ...` directly (instead of computing each recursive call into a variable FIRST) triggers Java's short-circuit evaluation — the moment `isValid` is `false`, the remaining `dfs` calls never run, leaving part of the island unvisited and able to incorrectly start a fresh flood fill later.

- The base case returning `true` for out-of-bounds and non-land cells is deliberate — those are "no constraint violated," not "constraint failed," so they must not drag `isValid` to `false`.
- This "visit everything, accumulate a boolean without short-circuiting" pattern generalizes to any flood fill that needs a global property checked across the whole region.
- Related problems: Number of Islands (no validity check, just count), Max Area of Island (accumulate a sum instead of a boolean).
