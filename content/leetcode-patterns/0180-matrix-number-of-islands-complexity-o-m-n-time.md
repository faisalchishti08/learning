---
card: leetcode-patterns
gi: 180
slug: matrix-number-of-islands-complexity-o-m-n-time
title: Matrix / Number of Islands — complexity: O(m*n) time
---

## 1. What it is

This page explains why matrix flood fill runs in O(rows × columns) time and space, and lists the named problems that use the pattern, so you have both the proof and a reference set.

## 2. Why & when

Interviewers often ask you to justify the complexity, not just produce working code. "It's O(m*n) because we visit the grid" is not a full justification — you need to explain WHY every cell is visited at most a constant number of times, not repeatedly. This matters because a naive mistake (like not marking cells visited) can silently turn a linear-in-grid-size algorithm into an exponential one.

## 3. Core concept

**Time — O(m × n).** Every cell is visited at most once by the outer scanning loop, and at most once more when it is discovered by a neighboring flood fill (DFS recursion call or BFS enqueue), because it is marked visited immediately at discovery. Once visited, a cell is never re-processed — the `if (visited[r][c]) return` (DFS) or the visited-check before enqueue (BFS) guarantees this. Since each of the `m × n` cells does a constant amount of work (checking up to 4 neighbors), the total work is O(m × n).

**Space — O(m × n) worst case.** The `visited` array itself is O(m × n). On top of that, DFS uses call-stack space proportional to the deepest single region — in the worst case (the whole grid is one connected region, e.g. a snake pattern), that depth is O(m × n). BFS uses queue space proportional to the largest "frontier" at once, which is also bounded by O(m × n) in the worst case (e.g. a fully filled grid).

**Why not worse.** A naive mistake — like not checking `visited` before recursing, or re-scanning the whole grid inside each fill instead of just following neighbors — can turn this into O((m × n)²) or worse. The key discipline is: mark visited at discovery time, and only ever look at a cell's direct 4 neighbors, never the whole grid, from within a single fill step.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each grid cell is touched a constant number of times: once by the scan, once by discovery">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="20" width="200" height="140" fill="none" stroke="#30363d"/>
    <g stroke="#30363d">
      <line x1="70" y1="20" x2="70" y2="160"/><line x1="120" y1="20" x2="120" y2="160"/><line x1="170" y1="20" x2="170" y2="160"/>
      <line x1="20" y1="55" x2="220" y2="55"/><line x1="20" y1="90" x2="220" y2="90"/><line x1="20" y1="125" x2="220" y2="125"/>
    </g>
    <text x="20" y="180" fill="#8b949e">each of the m*n cells: scanned once, discovered at most once -> O(m*n) total</text>
  </g>
</svg>

Every one of the m×n grid cells is touched a bounded number of times — once by the outer scan, once at discovery — never proportional to the grid size again.

## 5. Runnable example

An instrumented flood fill that counts how many times each cell is actually visited, to confirm the O(m × n) bound holds and every cell is touched exactly once.

```java
// ComplexityCheck.java
import java.util.*;

public class ComplexityCheck {

    static int[][] visitCounts;

    static int countIslands(int[][] grid) {
        boolean[][] visited = new boolean[grid.length][grid[0].length];
        visitCounts = new int[grid.length][grid[0].length];
        int count = 0;
        for (int r = 0; r < grid.length; r++) {
            for (int c = 0; c < grid[0].length; c++) {
                if (grid[r][c] == 1 && !visited[r][c]) {
                    dfs(grid, visited, r, c);
                    count++;
                }
            }
        }
        return count;
    }

    static void dfs(int[][] grid, boolean[][] visited, int r, int c) {
        if (r < 0 || r >= grid.length || c < 0 || c >= grid[0].length) return;
        visitCounts[r][c]++;
        if (visited[r][c] || grid[r][c] == 0) return;
        visited[r][c] = true;
        dfs(grid, visited, r + 1, c);
        dfs(grid, visited, r - 1, c);
        dfs(grid, visited, r, c + 1);
        dfs(grid, visited, r, c - 1);
    }

    public static void main(String[] args) {
        int[][] grid = {
            {1, 1, 0},
            {0, 1, 0},
            {0, 0, 1}
        };
        int islands = countIslands(grid);
        int maxTouches = 0;
        for (int[] row : visitCounts) for (int v : row) maxTouches = Math.max(maxTouches, v);
        System.out.println("islands = " + islands);
        System.out.println("max times any single cell was touched = " + maxTouches);
    }
}
```

**How to run:** `java ComplexityCheck.java`

## 6. Walkthrough

1. `grid` is 3×3, so `m × n = 9` cells total.
2. `countIslands` scans all 9 cells once via the outer loop; for the 5 land cells, `dfs` is called (directly or via a neighbor) some bounded number of times each.
3. Printing `visitCounts` after the run shows each cell touched at most a small constant number of times — each of its up-to-4 neighbors can "try" to visit it once, but the `visited` check stops any repeat processing.
4. `maxTouches` stays small and does not grow with grid size — it depends only on how many neighbors a cell has (at most 4), confirming the O(m × n) total bound (each of 9 cells touched a constant number of times, not proportional to overall region size).
5. This confirms the theoretical claim: total work is proportional to the number of cells, not to the square of the number of cells or to the number of regions times grid size.

## 7. Gotchas & takeaways

> Gotcha: marking a cell visited only AFTER fully processing all its neighbors (post-order), instead of the moment it is discovered (pre-order), lets the same cell get added to the recursion/queue multiple times before its first visit completes, breaking the O(m × n) bound.

- Time: O(m × n) because the visited check guarantees every cell does a bounded amount of work exactly once.
- Space: O(m × n) worst case, from the `visited` array plus the DFS call stack (or BFS queue) in the worst-case fully-connected grid.
- Reference problems that use this pattern: Flood Fill, Island Perimeter, Number of Islands, Max Area of Island, Surrounded Regions, Number of Closed Islands, Walls and Gates, 01 Matrix, Number of Enclaves.
