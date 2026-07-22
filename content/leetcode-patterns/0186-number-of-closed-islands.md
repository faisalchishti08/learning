---
card: leetcode-patterns
gi: 186
slug: number-of-closed-islands
title: Number of Closed Islands
---

## 1. What it is

Given a grid of `0`s (land) and `1`s (water) — note the values are SWAPPED from the usual convention — return the number of "closed islands": land regions fully surrounded by water, meaning they do NOT touch the grid border. Example: `grid = [[1,1,1,1,1,1,1,0],[1,0,0,0,0,1,1,0],[1,0,1,0,1,1,1,0],[1,0,0,0,0,1,0,1],[1,1,1,1,1,1,1,0]]` → `2`.

## 2. Why & when

This combines Surrounded Regions' "eliminate border-touching regions first" idea with Number of Islands' "count remaining regions" idea. A closed island, by definition, never touches the border, so the safest approach is to remove any land region that DOES touch the border before counting what's left.

## 3. Core concept

**Key idea:** first flood fill away (flip to water) every land region connected to the border — those can never be closed islands, since they touch the edge directly or transitively. Then run the standard "count connected regions" flood fill on what remains; every land region left is, by construction, fully enclosed.

**Steps:**
1. Flood fill from every land cell on the border, flipping the whole connected region it belongs to from land to water. Do this for all 4 edges.
2. After that cleanup pass, scan the entire grid; every remaining land cell is guaranteed to not touch the border (directly or transitively), since any that did was already removed.
3. For each unvisited remaining land cell found, flood fill to mark its whole region visited, and increment a counter.
4. Return the counter after the scan completes.

**Why it is correct:** a land region touches the border if and only if flood fill from a border land cell reaches it — the first pass removes exactly those regions. What remains is exactly the set of land cells belonging to regions with no path to the border, which is the definition of "closed island." Counting connected regions among what remains, using the standard Number of Islands technique, gives the correct closed-island count.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Border-touching land region removed first; remaining interior regions counted as closed islands">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="20" width="200" height="140" fill="none" stroke="#30363d"/>
    <rect x="20" y="20" width="30" height="30" fill="#f85149" opacity="0.5"/>
    <text x="60" y="40" fill="#e6edf3">border land -&gt; removed (step 1)</text>
    <rect x="100" y="80" width="30" height="30" fill="#3fb950"/>
    <text x="140" y="100" fill="#e6edf3">closed island -&gt; counted (step 2)</text>
    <text x="10" y="15" fill="#e6edf3">remove border-connected land, then count what's left as before</text>
  </g>
</svg>

Step 1 removes any land touching the border; step 2 counts the connected land regions that remain, using the standard flood-fill-and-count skeleton.

## 5. Runnable example

```java
// NumberOfClosedIslands.java
public class NumberOfClosedIslands {

    // Level 1 -- Brute force: for each land region found by a normal
    // island-counting scan, separately DFS again to check whether ANY
    // of its cells lie on the border, discarding it from the count if
    // so. Correct, but does the connectivity work twice per region --
    // once to find it, once to check its border status.

    // KEY INSIGHT: removing border-connected regions FIRST (as a
    // separate cleanup pass) means the later counting pass can safely
    // assume every remaining land cell is automatically "closed" --
    // no per-region border check needed during counting.

    // Level 2 -- Optimal: remove border-touching land first, then
    // count remaining islands.
    static int closedIsland(int[][] grid) {
        int rows = grid.length, cols = grid[0].length;
        for (int c = 0; c < cols; c++) {
            fillWater(grid, 0, c);
            fillWater(grid, rows - 1, c);
        }
        for (int r = 0; r < rows; r++) {
            fillWater(grid, r, 0);
            fillWater(grid, r, cols - 1);
        }

        int count = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (grid[r][c] == 0) {
                    fillWater(grid, r, c);
                    count++;
                }
            }
        }
        return count;
    }

    static void fillWater(int[][] grid, int r, int c) {
        if (r < 0 || r >= grid.length || c < 0 || c >= grid[0].length) return;
        if (grid[r][c] != 0) return;
        grid[r][c] = 1;
        fillWater(grid, r + 1, c);
        fillWater(grid, r - 1, c);
        fillWater(grid, r, c + 1);
        fillWater(grid, r, c - 1);
    }

    // Level 3 -- Hardened: a grid entirely made of border-touching
    // land correctly returns 0, since the cleanup pass removes
    // everything before the counting pass ever runs.

    public static void main(String[] args) {
        System.out.println(closedIsland(new int[][]{
            {1,1,1,1,1,1,1,0},
            {1,0,0,0,0,1,1,0},
            {1,0,1,0,1,1,1,0},
            {1,0,0,0,0,1,0,1},
            {1,1,1,1,1,1,1,0}
        })); // 2
        System.out.println(closedIsland(new int[][]{{0,0,1,0,0},{0,1,0,1,0},{0,1,1,1,0}})); // 1
    }
}
```

**How to run:** `java NumberOfClosedIslands.java`

## 6. Walkthrough

Trace the smaller example `[[0,0,1,0,0],[0,1,0,1,0],[0,1,1,1,0]]`:

| Step | Action | Result |
|---|---|---|
| 1 | border cleanup: flood fill from every border `0` | all border-touching `0`s flipped to `1` |
| 2 | after cleanup, only `{(1,2)}` remains as `0` (fully enclosed by the `1`s at (1,1),(1,3),(2,1),(2,2),(2,3)) | 1 region left |
| 3 | counting scan finds `(1,2)`, flood fills it (trivial, single cell), increments count | count = 1 |

Result matches the expected `1`. Time complexity is O(rows × cols) across both the cleanup pass and the counting pass; space is O(rows × cols) worst case for recursion depth.

## 7. Gotchas & takeaways

> Gotcha: running the counting pass BEFORE the border-cleanup pass would count border-touching regions as if they were closed, since nothing yet distinguishes them — the order of the two passes is not interchangeable.

- The values in this problem are swapped from usual convention (`0` = land, `1` = water) — always confirm the exact meaning from the problem statement before writing flood-fill conditions.
- This two-pass structure (remove border-connected first, then count) is directly reusable for Number of Enclaves and Surrounded Regions.
- Related problems: Surrounded Regions (same two-pass idea, flips values instead of counting), Number of Enclaves (same idea, counts total cells instead of regions).
