---
card: leetcode-patterns
gi: 194
slug: making-a-large-island
title: Making A Large Island
---

## 1. What it is

Given an `n x n` binary grid, you may change AT MOST one `0` to a `1`. Return the size of the largest possible island after doing so (or the largest existing island, if no `0` exists to flip, or if flipping does not help). Example: `grid = [[1,0],[0,1]]` → `3`.

## 2. Why & when

This combines Max Area of Island (measuring region sizes) with a clever twist: instead of trying every possible `0`-to-`1` flip and re-measuring the whole grid each time (slow), pre-compute every island's size ONCE, tag each island with an ID, then for each `0` cell, sum the DISTINCT neighboring islands' sizes in O(1) using the precomputed table.

## 3. Core concept

**Key idea:** first pass: flood fill every island, assigning each a unique ID (starting from 2, since `0` and `1` are taken) and recording its size in a map `id -> size`. Second pass: for every `0` cell, look at its up to 4 neighboring islands, sum the sizes of the DISTINCT ones (using a set to avoid double-counting an island touched from two sides), add `1` for the flipped cell itself, and track the maximum.

**Steps:**
1. Scan the grid; for every unvisited land cell, flood fill it with a unique ID (e.g. `2`, `3`, `4`, ...), recording each ID's total cell count in a map.
2. If no `0` cell exists anywhere, the answer is simply the grid's total cell count (everything is already one connected block, or the whole grid is land).
3. Scan the grid again; for every `0` cell, collect the SET of distinct island IDs among its 4 neighbors.
4. Sum the sizes of those distinct IDs (via the map from step 1), add `1` for the cell itself, and update a running maximum.
5. Return the maximum found — or, if no `0` cell existed, the total land count from step 1.

**Why it is correct:** relabeling each island with a unique ID lets you distinguish "two neighbors belong to the SAME island" (don't double count) from "two neighbors belong to DIFFERENT islands" (both must be counted, since flipping the `0` connects them together). Precomputing sizes once turns each `0`-cell's potential new size into an O(1) lookup and sum, instead of an O(rows × cols) re-flood-fill per candidate cell.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Flipping a 0 cell that touches two distinct islands merges both plus the flipped cell itself">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="60" width="30" height="30" fill="#3fb950"/><text x="35" y="80" fill="#0d1117" text-anchor="middle">2</text>
    <rect x="50" y="60" width="30" height="30" fill="#e3b341"/><text x="65" y="80" fill="#0d1117" text-anchor="middle">0</text>
    <rect x="80" y="60" width="30" height="30" fill="#79c0ff"/><text x="95" y="80" fill="#0d1117" text-anchor="middle">3</text>
    <text x="10" y="15" fill="#e6edf3">flipping the middle 0 merges island 2 and island 3 plus itself -- size(2) + size(3) + 1</text>
  </g>
</svg>

Flipping the `0` between two differently-labeled islands merges both, so its potential new size is `size(island 2) + size(island 3) + 1`.

## 5. Runnable example

```java
// MakingALargeIsland.java
import java.util.*;

public class MakingALargeIsland {

    // Level 1 -- Brute force: for every single 0 cell, flip it to 1,
    // re-run a full flood fill to measure the resulting island's size,
    // then flip it back. Correct, but O(n^4) -- for each of up to n^2
    // candidate cells, a full O(n^2) flood fill.

    // KEY INSIGHT: pre-label every island with a unique ID and its size
    // ONCE (O(n^2) total), so each 0 cell's potential new size becomes
    // an O(1) lookup-and-sum over its (at most 4) distinct neighboring
    // island IDs, instead of a fresh flood fill per candidate.

    // Level 2 -- Optimal: label islands once, then O(1) per-cell
    // lookup.
    static int largestIsland(int[][] grid) {
        int n = grid.length;
        Map<Integer, Integer> sizeById = new HashMap<>();
        int id = 2;

        for (int r = 0; r < n; r++) {
            for (int c = 0; c < n; c++) {
                if (grid[r][c] == 1) {
                    int size = labelIsland(grid, r, c, id);
                    sizeById.put(id, size);
                    id++;
                }
            }
        }

        int maxArea = sizeById.values().stream().mapToInt(Integer::intValue).max().orElse(0);
        int[][] dirs = {{0,1},{0,-1},{1,0},{-1,0}};

        for (int r = 0; r < n; r++) {
            for (int c = 0; c < n; c++) {
                if (grid[r][c] == 0) {
                    Set<Integer> seen = new HashSet<>();
                    for (int[] d : dirs) {
                        int nr = r + d[0], nc = c + d[1];
                        if (nr >= 0 && nr < n && nc >= 0 && nc < n && grid[nr][nc] > 1) {
                            seen.add(grid[nr][nc]);
                        }
                    }
                    int total = 1;
                    for (int neighborId : seen) total += sizeById.get(neighborId);
                    maxArea = Math.max(maxArea, total);
                }
            }
        }
        return maxArea;
    }

    static int labelIsland(int[][] grid, int r, int c, int id) {
        if (r < 0 || r >= grid.length || c < 0 || c >= grid.length || grid[r][c] != 1) return 0;
        grid[r][c] = id;
        return 1
            + labelIsland(grid, r + 1, c, id)
            + labelIsland(grid, r - 1, c, id)
            + labelIsland(grid, r, c + 1, id)
            + labelIsland(grid, r, c - 1, id);
    }

    // Level 3 -- Hardened: a grid entirely made of 1s (no 0 to flip)
    // correctly returns the total cell count via the maxArea
    // initialization from sizeById, since the second scan never finds
    // a 0 cell to improve on it.

    public static void main(String[] args) {
        System.out.println(largestIsland(new int[][]{{1,0},{0,1}})); // 3
        System.out.println(largestIsland(new int[][]{{1,1},{1,0}})); // 4
        System.out.println(largestIsland(new int[][]{{1,1},{1,1}})); // 4
    }
}
```

**How to run:** `java MakingALargeIsland.java`

## 6. Walkthrough

Trace `grid = [[1,0],[0,1]]`:

| Step | Action | Result |
|---|---|---|
| 1 | label island at (0,0) with ID 2 | sizeById = {2: 1} |
| 2 | label island at (1,1) with ID 3 | sizeById = {2: 1, 3: 1} |
| 3 | maxArea initialized to max(1, 1) = 1 | — |
| 4 | check (0,1)=0: neighbors are (0,0)=2 and (1,1)=3 | distinct IDs {2,3}, total = 1+1+1 = 3 |
| 5 | check (1,0)=0: neighbors are (0,0)=2 and (1,1)=3 | total = 3 again |

Final `maxArea = 3`. Time complexity is O(n²), since both scans and the labeling pass each touch every cell a bounded number of times; space is O(n²) for the map and recursion depth.

## 7. Gotchas & takeaways

> Gotcha: using a `List` instead of a `Set` for the neighboring island IDs double-counts an island touched from TWO different directions by the same `0` cell (e.g. an L-shaped island touching a 0 cell on both its right and bottom side) — the `Set` is what prevents this.

- Start island IDs at `2` (not `1`), since `0` and `1` are already used by the grid's original values, and the ID must be distinguishable from both when scanning neighbors.
- If no `0` cell exists in the grid, the max computed from `sizeById` alone (before the second scan) is already the correct answer — the second scan simply never improves on it.
- Related problems: Number of Islands (label without measuring merge potential), Max Area of Island (measure existing islands only, no hypothetical flip).
