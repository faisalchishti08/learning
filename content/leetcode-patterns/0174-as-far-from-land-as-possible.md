---
card: leetcode-patterns
gi: 174
slug: as-far-from-land-as-possible
title: As Far from Land as Possible
---

## 1. What it is

Given an `n x n` grid of `0`s (water) and `1`s (land), find the water cell whose Manhattan distance to the nearest land cell is as LARGE as possible, and return that distance. Return `-1` if the grid is all land or all water. Example: `grid = [[1,0,1],[0,0,0],[1,0,1]]` → `2`.

## 2. Why & when

"Distance from the nearest of many sources" is the multi-source BFS signal. Instead of running BFS separately from every land cell (slow), seed the BFS queue with ALL land cells at once, at distance 0, and let it expand outward together — the layer at which the last water cell is reached is the answer.

## 3. Core concept

**Key idea:** treat every land cell as a BFS starting point simultaneously. BFS naturally computes, for every water cell, its distance to the NEAREST land cell, because the closest source reaches each water cell first. The last cell BFS reaches gives the maximum such distance.

**Steps:**
1. Enqueue every land cell (`grid[r][c] == 1`) into the BFS queue at distance 0, marking all of them visited.
2. If there is no land, or no water, return `-1` immediately (no valid answer).
3. Run BFS layer by layer; each new layer is one step farther from the nearest land.
4. Track the last layer number reached (the maximum distance assigned to any water cell).
5. Return that maximum.

**Why it is correct:** multi-source BFS assigns each water cell the distance to whichever source reaches it FIRST, which is exactly the nearest land cell, because BFS explores in increasing distance order from all sources at once. The final (largest) layer number is therefore the maximum "distance to nearest land" over the whole grid.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multi-source BFS from all land cells simultaneously, rings expanding into water">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="30" width="30" height="30" fill="#3fb950"/>
    <rect x="80" y="30" width="30" height="30" fill="#3fb950"/>
    <rect x="50" y="30" width="30" height="30" fill="#e3b341" opacity="0.6"/>
    <rect x="20" y="90" width="30" height="30" fill="#3fb950"/>
    <rect x="80" y="90" width="30" height="30" fill="#3fb950"/>
    <rect x="50" y="90" width="30" height="30" fill="#e3b341" opacity="0.6"/>
    <rect x="50" y="60" width="30" height="30" fill="#79c0ff"/>
    <text x="10" y="15" fill="#e6edf3">land cells (green) seed BFS together; center water cell (blue) is farthest, distance 2</text>
  </g>
</svg>

All land cells seed the BFS at once; the water cell equidistant from several land cells (in the middle) is reached last, at the maximum distance.

## 5. Runnable example

```java
// AsFarFromLandAsPossible.java
import java.util.*;

public class AsFarFromLandAsPossible {

    // Level 1 -- Brute force: for every water cell, scan all land
    // cells and take the minimum Manhattan distance, then take the
    // maximum of those minimums. Correct, but O(n^4) for an n x n grid
    // -- comparing every water cell against every land cell directly.

    // KEY INSIGHT: multi-source BFS computes "distance to nearest
    // source" for every cell in ONE traversal, instead of one scan per
    // water cell -- exactly because a cell reached from several
    // directions is always reached first by the truly nearest source.

    // Level 2 -- Optimal: multi-source BFS from all land cells.
    static int maxDistance(int[][] grid) {
        int n = grid.length;
        Queue<int[]> queue = new LinkedList<>();
        boolean[][] visited = new boolean[n][n];

        for (int r = 0; r < n; r++) {
            for (int c = 0; c < n; c++) {
                if (grid[r][c] == 1) {
                    queue.add(new int[]{r, c});
                    visited[r][c] = true;
                }
            }
        }
        if (queue.isEmpty() || queue.size() == n * n) return -1;

        int[][] dirs = {{0,1},{0,-1},{1,0},{-1,0}};
        int distance = -1;
        while (!queue.isEmpty()) {
            int size = queue.size();
            distance++;
            for (int i = 0; i < size; i++) {
                int[] cell = queue.poll();
                for (int[] d : dirs) {
                    int nr = cell[0] + d[0], nc = cell[1] + d[1];
                    if (nr < 0 || nr >= n || nc < 0 || nc >= n || visited[nr][nc]) continue;
                    visited[nr][nc] = true;
                    queue.add(new int[]{nr, nc});
                }
            }
        }
        return distance;
    }

    // Level 3 -- Hardened: all-land and all-water grids are checked
    // up front and return -1, before BFS even starts, avoiding a
    // meaningless distance of 0 or an empty-queue edge case.

    public static void main(String[] args) {
        System.out.println(maxDistance(new int[][]{{1,0,1},{0,0,0},{1,0,1}})); // 2
        System.out.println(maxDistance(new int[][]{{1,0,0},{0,0,0},{0,0,0}})); // 4
        System.out.println(maxDistance(new int[][]{{1,1},{1,1}})); // -1
    }
}
```

**How to run:** `java AsFarFromLandAsPossible.java`

## 6. Walkthrough

Trace `grid = [[1,0,1],[0,0,0],[1,0,1]]`:

| Step | Layer | distance | Cells reached |
|---|---|---|---|
| seed | — | -1 → 0 (first increment) | 4 land cells at (0,0),(0,2),(2,0),(2,2) |
| 1 | ring 1 | 1 | (0,1),(1,0),(1,2),(2,1) |
| 2 | ring 2 | 2 | (1,1) — the center cell |

Center cell `(1,1)` is reached last, at distance `2`. Time complexity is O(n²), since each of the n² cells enters the queue at most once; space is O(n²) for the visited array and queue.

## 7. Gotchas & takeaways

> Starting `distance` at `0` instead of `-1` and incrementing AFTER processing the seed layer counts the land cells themselves as "distance 1," shifting every answer up by one.

- Check for all-land / all-water grids before starting BFS — a grid with no water has no valid answer, and neither does a grid with no land.
- The `distance` variable is incremented once per BFS layer, including the very first expansion away from land — increment before processing each layer's neighbors, not after.
- Related problems: Rotting Oranges (multi-source BFS with a similar layer-counting pattern), Shortest Bridge (multi-source BFS from one region to reach another).
