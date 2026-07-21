---
card: leetcode-patterns
gi: 160
slug: pacific-atlantic-water-flow
title: Pacific Atlantic Water Flow
---

## 1. What it is

Given an `m x n` grid of heights representing a continent's terrain, the Pacific Ocean touches the top and left edges, and the Atlantic touches the bottom and right edges. Water can flow from a cell to a neighboring cell only if the neighbor's height is less than or equal to the current cell's height. Return every cell from which water can reach BOTH oceans. Example: a small grid where corner and edge cells with generally decreasing height toward the borders qualify.

## 2. Why & when

The naive approach — for every cell, run a DFS/BFS to see if it can reach the Pacific AND separately the Atlantic — is expensive, since it repeats a full grid traversal for every single cell. The efficient trick is to REVERSE the direction of the search: instead of asking "can water flow FROM this cell TO the ocean," start the search FROM each ocean's border cells and ask "which cells could flow water INTO here" (equivalently, walk uphill or equal from the border, since flow only goes downhill or level). Running this once from the Pacific border and once from the Atlantic border, then intersecting the two reachable sets, replaces `O(cells)` separate traversals with just two.

## 3. Core concept

**Key idea:** run a DFS/BFS from every Pacific-adjacent border cell simultaneously, moving to a neighbor only if the neighbor's height is `>=` the current cell's height (walking "uphill or level", the reverse of water's actual downhill flow) — this marks every cell that can reach the Pacific. Do the same from every Atlantic-adjacent border cell. The answer is every cell marked reachable in BOTH searches.

**Steps:**
1. Create two boolean grids, `canReachPacific` and `canReachAtlantic`, both initialized to `false`.
2. Seed the Pacific search: every cell on the top row or left column starts a DFS/BFS, marking `canReachPacific[r][c] = true` as each cell is visited, moving only to unvisited neighbors with height `>= current height`.
3. Seed the Atlantic search: every cell on the bottom row or right column starts a similar DFS/BFS into `canReachAtlantic`.
4. Scan every cell: if `canReachPacific[r][c] && canReachAtlantic[r][c]`, add `(r, c)` to the result.

**Why it is correct:** water flows from a HIGHER (or equal) cell to a LOWER (or equal) one, so reversing the search — walking from a border cell to a neighbor only when that neighbor is AT LEAST as high — exactly retraces every path water COULD have taken to reach that border, in the opposite direction; running this once per ocean, then intersecting, finds every cell with a valid downhill path to both borders without ever re-searching from an individual interior cell.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Searching backward (uphill) from each ocean's border, then intersecting reachable sets">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="20" width="360" height="130" fill="none" stroke="#8b949e"/>
    <text x="10" y="15" fill="#3fb950">Pacific (top + left)</text>
    <text x="300" y="165" fill="#79c0ff">Atlantic (bottom + right)</text>
    <circle cx="60" cy="60" r="4" fill="#3fb950"/>
    <circle cx="60" cy="100" r="4" fill="#3fb950"/>
    <circle cx="100" cy="60" r="4" fill="#3fb950"/>
    <circle cx="340" cy="110" r="4" fill="#79c0ff"/>
    <circle cx="340" cy="70" r="4" fill="#79c0ff"/>
    <circle cx="300" cy="110" r="4" fill="#79c0ff"/>
    <circle cx="200" cy="85" r="6" fill="#161b22" stroke="#f85149" stroke-width="2"/>
    <text x="10" y="185" fill="#e6edf3">Green search fans out from Pacific border, blue from Atlantic border -- a cell reached by BOTH (red) qualifies.</text>
  </g>
</svg>

The two backward searches expand independently; only cells touched by both are part of the final answer.

## 5. Runnable example

```java
// PacificAtlanticWaterFlow.java
import java.util.*;

public class PacificAtlanticWaterFlow {

    // Level 1 -- Brute force: for every single cell, run a fresh DFS to
    // check if it can reach the Pacific border, and a separate DFS to
    // check the Atlantic border. O((rows*cols)^2) time worst case,
    // since every cell triggers its own full grid traversal.
    static List<int[]> bruteForce(int[][] heights) {
        int rows = heights.length, cols = heights[0].length;
        List<int[]> result = new ArrayList<>();
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (canReach(heights, r, c, true) && canReach(heights, r, c, false)) {
                    result.add(new int[]{r, c});
                }
            }
        }
        return result;
    }

    static boolean canReach(int[][] heights, int r, int c, boolean pacific) {
        int rows = heights.length, cols = heights[0].length;
        boolean[][] visited = new boolean[rows][cols];
        return canReachHelper(heights, r, c, visited, pacific);
    }

    static boolean canReachHelper(int[][] heights, int r, int c, boolean[][] visited, boolean pacific) {
        int rows = heights.length, cols = heights[0].length;
        if (pacific && (r == 0 || c == 0)) return true;
        if (!pacific && (r == rows - 1 || c == cols - 1)) return true;
        visited[r][c] = true;
        int[][] dirs = {{-1,0},{1,0},{0,-1},{0,1}};
        for (int[] d : dirs) {
            int nr = r + d[0], nc = c + d[1];
            if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && !visited[nr][nc] && heights[nr][nc] <= heights[r][c]) {
                if (canReachHelper(heights, nr, nc, visited, pacific)) return true;
            }
        }
        return false;
    }

    // KEY INSIGHT: instead of asking "can water flow FROM this cell TO
    // the border" for every cell, search BACKWARD from the border cells
    // themselves -- one traversal per ocean finds every cell that ocean
    // can reach, instead of one traversal PER CELL.

    // Level 2 -- Optimal: DFS from each ocean's border cells, walking
    // "uphill or equal", then intersect the two reachable sets.
    // O(rows * cols) time, O(rows * cols) space.
    public static List<int[]> pacificAtlantic(int[][] heights) {
        int rows = heights.length, cols = heights[0].length;
        boolean[][] canReachPacific = new boolean[rows][cols];
        boolean[][] canReachAtlantic = new boolean[rows][cols];

        for (int c = 0; c < cols; c++) {
            dfs(heights, 0, c, canReachPacific);
            dfs(heights, rows - 1, c, canReachAtlantic);
        }
        for (int r = 0; r < rows; r++) {
            dfs(heights, r, 0, canReachPacific);
            dfs(heights, r, cols - 1, canReachAtlantic);
        }

        List<int[]> result = new ArrayList<>();
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (canReachPacific[r][c] && canReachAtlantic[r][c]) result.add(new int[]{r, c});
            }
        }
        return result;
    }

    static void dfs(int[][] heights, int r, int c, boolean[][] canReach) {
        if (canReach[r][c]) return;
        canReach[r][c] = true;
        int rows = heights.length, cols = heights[0].length;
        int[][] dirs = {{-1,0},{1,0},{0,-1},{0,1}};
        for (int[] d : dirs) {
            int nr = r + d[0], nc = c + d[1];
            if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && !canReach[nr][nc] && heights[nr][nc] >= heights[r][c]) {
                dfs(heights, nr, nc, canReach);
            }
        }
    }

    // Level 3 -- Hardened: a completely flat grid (all equal heights)
    // must return every single cell, since all heights tie (>= and <=
    // both hold everywhere).
    static List<int[]> hardened(int[][] heights) {
        return pacificAtlantic(heights);
    }

    public static void main(String[] args) {
        int[][] heights = {
            {1, 2, 2, 3, 5},
            {3, 2, 3, 4, 4},
            {2, 4, 5, 3, 1},
            {6, 7, 1, 4, 5},
            {5, 1, 1, 2, 4}
        };

        System.out.println(bruteForce(heights).size());
        System.out.println(pacificAtlantic(heights).size());

        int[][] flat = {{1,1},{1,1}};
        System.out.println(hardened(flat).size());
    }
}
```

How to run: save as `PacificAtlanticWaterFlow.java`, then run `java PacificAtlanticWaterFlow.java`.

## 6. Walkthrough

Trace of the Pacific DFS seeded from `(0, 0)` (height `1`) on a small corner of the example grid:

1. Start at `(0,0)`, height `1`. Mark `canReachPacific[0][0] = true`.
2. Check neighbor `(0,1)`, height `2`: `2 >= 1`, so recurse — walking "uphill" is allowed, mark it reachable.
3. Check neighbor `(1,0)`, height `3`: `3 >= 1`, recurse, mark it reachable.
4. Continue outward from each newly marked cell, always requiring the next cell's height to be `>=` the current cell's height.

Every cell reached this way genuinely CAN flow downhill back to `(0,0)` and out to the Pacific, since the search retraces a valid downhill path in reverse. Doing this once from every Pacific-border cell (and once from every Atlantic-border cell) covers the whole grid in two traversals total. Time complexity: O(rows * cols), each cell visited a constant number of times across both searches. Space complexity: O(rows * cols) for the two boolean grids plus the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: using `>` instead of `>=` when deciding whether to recurse into a neighbor (during the backward "uphill" search) would incorrectly reject FLAT stretches of land — water CAN flow between cells of EQUAL height, so the backward search must also be allowed to move to equal-height neighbors, not just strictly higher ones.

- The trick of "search backward from the destination instead of forward from every source" generalizes beyond this problem: whenever a question asks "which starting points can reach ALL of a set of targets," searching from each target backward is usually far cheaper than searching from each starting point forward.
- Related problems: Rotting Oranges (BFS spreading forward from multiple sources simultaneously, the same "multi-source" idea used here but in the natural forward direction), Number of Provinces (also marks reachable sets with DFS, but to count components rather than to intersect two directions of reachability).
