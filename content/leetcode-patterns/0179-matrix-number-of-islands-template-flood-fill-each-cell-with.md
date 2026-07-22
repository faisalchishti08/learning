---
card: leetcode-patterns
gi: 179
slug: matrix-number-of-islands-template-flood-fill-each-cell-with
title: Matrix / Number of Islands — template: flood-fill each cell with BFS/DFS, mark visited
---

## 1. What it is

A template is the reusable skeleton of code you write first, before filling in problem-specific logic. For matrix flood fill, there are two skeletons: the **DFS flood fill** (recursive, visits one region depth-first) and the **BFS flood fill** (queue-based, visits one region layer by layer). Both scan the whole grid once, starting a fresh fill at every unvisited matching cell.

## 2. Why & when

Memorizing both templates means you spend your problem-solving time deciding WHAT counts as "connected" and what to do with each region (count it, measure it, mark it), instead of re-deriving the traversal mechanics from scratch each time.

Use DFS when you only need to fully visit each region (counting islands, summing area, marking a region). Use BFS when you need distance information (shortest path to/from a region) or want to avoid deep recursion on very large grids (BFS uses an explicit queue, not the call stack).

## 3. Core concept

**DFS flood-fill template.** A recursive helper takes the grid, current row/column, and marks the cell visited immediately upon entry (before recursing). It returns early if the cell is out of bounds, already visited, or does not match the target condition. Otherwise, it recurses into all 4 neighbors. The outer loop scans every cell; whenever it finds an unvisited matching cell, it calls the DFS helper and increments a counter (or accumulates whatever the region tracks).

**BFS flood-fill template.** A queue starts with one matching cell, marked visited immediately when enqueued. The loop dequeues a cell, processes it, then examines its 4 neighbors — any unvisited matching neighbor is marked visited and enqueued. The outer loop scans every cell exactly like the DFS version, starting a new BFS at each unvisited matching cell found.

Both templates share the same invariant: a cell is marked visited THE MOMENT it enters the frontier (recursion call or queue), never later — this guarantees each cell is processed exactly once, which is what keeps the whole algorithm at O(rows × cols).

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DFS template goes deep first; BFS template expands in layers">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">DFS: depth-first, one branch at a time</text>
    <circle cx="40" cy="60" r="14" fill="#161b22" stroke="#3fb950"/><text x="40" y="64" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="40" cy="110" r="14" fill="#161b22" stroke="#79c0ff"/><text x="40" y="114" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="40" cy="160" r="14" fill="#161b22" stroke="#e3b341"/><text x="40" y="164" fill="#e6edf3" text-anchor="middle">3</text>
    <line x1="40" y1="74" x2="40" y2="96" stroke="#8b949e"/>
    <line x1="40" y1="124" x2="40" y2="146" stroke="#8b949e"/>

    <text x="400" y="20" fill="#e6edf3" font-weight="bold">BFS: layer by layer, all neighbors first</text>
    <circle cx="420" cy="100" r="14" fill="#161b22" stroke="#3fb950"/><text x="420" y="104" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="480" cy="70" r="14" fill="#161b22" stroke="#79c0ff"/><text x="480" y="74" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="480" cy="130" r="14" fill="#161b22" stroke="#79c0ff"/><text x="480" y="134" fill="#e6edf3" text-anchor="middle">2</text>
    <line x1="432" y1="92" x2="468" y2="76" stroke="#8b949e"/>
    <line x1="432" y1="108" x2="468" y2="124" stroke="#8b949e"/>
  </g>
</svg>

DFS numbers cells in the order it visits them along one deep path; BFS numbers cells by distance layer from the start.

## 5. Runnable example

Both templates side by side, counting the number of connected `1`-regions in a small grid — the same result from two different traversal orders.

```java
// FloodFillTemplates.java
import java.util.*;

public class FloodFillTemplates {

    static int countIslandsDFS(int[][] grid) {
        boolean[][] visited = new boolean[grid.length][grid[0].length];
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
        if (visited[r][c] || grid[r][c] == 0) return;
        visited[r][c] = true;
        dfs(grid, visited, r + 1, c);
        dfs(grid, visited, r - 1, c);
        dfs(grid, visited, r, c + 1);
        dfs(grid, visited, r, c - 1);
    }

    static int countIslandsBFS(int[][] grid) {
        boolean[][] visited = new boolean[grid.length][grid[0].length];
        int[][] dirs = {{0,1},{0,-1},{1,0},{-1,0}};
        int count = 0;
        for (int r = 0; r < grid.length; r++) {
            for (int c = 0; c < grid[0].length; c++) {
                if (grid[r][c] == 1 && !visited[r][c]) {
                    Queue<int[]> queue = new LinkedList<>();
                    queue.add(new int[]{r, c});
                    visited[r][c] = true;
                    while (!queue.isEmpty()) {
                        int[] cell = queue.poll();
                        for (int[] d : dirs) {
                            int nr = cell[0] + d[0], nc = cell[1] + d[1];
                            if (nr < 0 || nr >= grid.length || nc < 0 || nc >= grid[0].length) continue;
                            if (visited[nr][nc] || grid[nr][nc] == 0) continue;
                            visited[nr][nc] = true;
                            queue.add(new int[]{nr, nc});
                        }
                    }
                    count++;
                }
            }
        }
        return count;
    }

    public static void main(String[] args) {
        int[][] grid = {
            {1, 1, 0},
            {0, 1, 0},
            {0, 0, 1}
        };
        System.out.println("DFS island count: " + countIslandsDFS(grid)); // 2
        System.out.println("BFS island count: " + countIslandsBFS(grid)); // 2
    }
}
```

**How to run:** `java FloodFillTemplates.java`

## 6. Walkthrough

1. The outer double loop scans `grid` row by row, column by column.
2. At `(0,0)`, value is `1` and unvisited — start a fill. DFS recurses into `(0,1)` (also `1`), which recurses into its neighbors, all already visited or water, so it backtracks. This whole fill marks `{(0,0),(0,1),(1,1)}` visited and increments `count` to 1.
3. Scanning continues; `(0,2)`, `(1,0)`, `(1,2)`, `(2,0)`, `(2,1)` are all water or already visited, so nothing happens.
4. At `(2,2)`, value is `1` and unvisited — start a second fill. It has no matching neighbors, so this fill only marks `{(2,2)}` and increments `count` to 2.
5. The BFS version produces the identical count (`2`) by the same scan-and-fill logic, just using a queue instead of recursion for each fill.

## 7. Gotchas & takeaways

> Gotcha: using DFS recursion on a very large grid (e.g. 1000×1000, all land) can overflow the call stack, since the recursion depth can reach the total cell count; BFS with an explicit queue avoids this because it never recurses.

- Both templates give identical results for "count connected regions" — pick DFS for brevity, BFS when recursion depth is a concern or distances matter.
- The outer scan loop must check `visited` before starting a new fill, or the same island gets counted multiple times.
- Mutating the grid in place (writing over `1` with `0` or `2`) is a common shortcut that avoids allocating a separate `visited` array, when the input can be modified.
