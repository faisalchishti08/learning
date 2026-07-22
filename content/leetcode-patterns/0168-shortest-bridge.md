---
card: leetcode-patterns
gi: 168
slug: shortest-bridge
title: Shortest Bridge
---

## 1. What it is

Given a binary grid with exactly two islands (groups of `1`s connected 4-directionally, surrounded by `0`s / water), return the minimum number of `0`s you must flip to `1` to connect the two islands. Example: `grid = [[0,1],[1,0]]` → `1`.

## 2. Why & when

This problem combines two graph traversals: DFS to find and mark one whole island, then multi-source BFS to expand outward from every cell of that island simultaneously until it touches the other island. It is the classic "find shortest distance between two regions" pattern.

## 3. Core concept

**Key idea:** DFS finds the first island and adds all its cells to a BFS queue as multiple starting points. BFS then expands outward one ring of water at a time; the ring number where it first touches a `1` belonging to the second island is the answer.

**Steps:**
1. Scan the grid to find any cell of island 1. DFS from there, marking every connected `1` as visited and pushing each into a BFS queue (these are the multi-source starting points).
2. Run BFS layer by layer from that whole set of cells simultaneously.
3. At each layer, expand into adjacent water (`0`) cells, marking them visited and incrementing a step counter after the layer completes.
4. If an expansion step lands on an unvisited `1` (a cell of the second island), return the current step count.

**Why it is correct:** multi-source BFS explores water rings in order of distance from island 1. The first `1` cell it reaches — belonging to island 2 by construction — is reached in the minimum number of flips, because BFS never skips a shorter path in an unweighted graph.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multi-source BFS expanding rings of water from island 1 until it reaches island 2">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="60" width="30" height="30" fill="#3fb950"/>
    <rect x="50" y="60" width="30" height="30" fill="#3fb950"/>
    <rect x="110" y="60" width="30" height="30" fill="#e3b341" opacity="0.6"/>
    <rect x="140" y="60" width="30" height="30" fill="#e3b341" opacity="0.3"/>
    <rect x="170" y="60" width="30" height="30" fill="#79c0ff"/>
    <text x="20" y="50" fill="#e6edf3">island 1 (DFS-marked)</text>
    <text x="110" y="50" fill="#e6edf3">BFS rings expand</text>
    <text x="170" y="50" fill="#e6edf3">island 2 (target)</text>
  </g>
</svg>

BFS rings (gold, fading with distance) spread from island 1 (green) until they touch island 2 (blue).

## 5. Runnable example

```java
// ShortestBridge.java
import java.util.*;

public class ShortestBridge {

    // Level 1 -- Brute force: BFS from every single cell of island 1
    // independently to find the nearest cell of island 2, taking the
    // minimum over all of them. Correct, but redoing a full BFS per
    // starting cell is far more work than necessary.

    // KEY INSIGHT: run ONE multi-source BFS that starts from ALL of
    // island 1's cells at once (distance 0 for every one of them) --
    // the rings still expand outward correctly, in a single pass.

    // Level 2 -- Optimal: DFS to mark and collect island 1, then
    // multi-source BFS.
    static int shortestBridge(int[][] grid) {
        int n = grid.length;
        boolean[][] visited = new boolean[n][n];
        Queue<int[]> queue = new LinkedList<>();

        outer:
        for (int r = 0; r < n; r++) {
            for (int c = 0; c < n; c++) {
                if (grid[r][c] == 1) {
                    dfsMark(grid, visited, r, c, queue);
                    break outer;
                }
            }
        }

        int[][] dirs = {{0,1},{0,-1},{1,0},{-1,0}};
        int steps = 0;
        while (!queue.isEmpty()) {
            int size = queue.size();
            for (int i = 0; i < size; i++) {
                int[] cell = queue.poll();
                for (int[] d : dirs) {
                    int nr = cell[0] + d[0], nc = cell[1] + d[1];
                    if (nr < 0 || nr >= n || nc < 0 || nc >= n || visited[nr][nc]) continue;
                    if (grid[nr][nc] == 1) return steps;
                    visited[nr][nc] = true;
                    queue.add(new int[]{nr, nc});
                }
            }
            steps++;
        }
        return -1;
    }

    static void dfsMark(int[][] grid, boolean[][] visited, int r, int c, Queue<int[]> queue) {
        int n = grid.length;
        if (r < 0 || r >= n || c < 0 || c >= n || visited[r][c] || grid[r][c] == 0) return;
        visited[r][c] = true;
        queue.add(new int[]{r, c});
        dfsMark(grid, visited, r + 1, c, queue);
        dfsMark(grid, visited, r - 1, c, queue);
        dfsMark(grid, visited, r, c + 1, queue);
        dfsMark(grid, visited, r, c - 1, queue);
    }

    // Level 3 -- Hardened: works for islands of any shape, including a
    // single-cell island, because DFS marks whatever is connected and
    // BFS seeds from that exact set of queue entries.

    public static void main(String[] args) {
        System.out.println(shortestBridge(new int[][]{{0,1},{1,0}})); // 1
        System.out.println(shortestBridge(new int[][]{{0,1,0},{0,0,0},{0,0,1}})); // 2
        System.out.println(shortestBridge(new int[][]{
            {1,1,1,1,1},{1,0,0,0,1},{1,0,1,0,1},{1,0,0,0,1},{1,1,1,1,1}
        })); // 1
    }
}
```

**How to run:** `java ShortestBridge.java`

## 6. Walkthrough

Trace `grid = [[0,1],[1,0]]`:

| Step | Action | State |
|---|---|---|
| 1 | Find first `1` at `(0,1)` | DFS marks `(0,1)`, queue = `[(0,1)]` |
| 2 | BFS layer 0, steps=0 | expand `(0,1)` → `(1,1)` is `0`, mark visited, enqueue |
| 3 | steps becomes 1 | queue = `[(1,1)]` |
| 4 | BFS layer 1 | expand `(1,1)` → `(1,0)` is `1` → return steps = 1 |

Time complexity is O(n²) for the grid scan, DFS, and BFS combined; space is O(n²) for the visited array and queue.

## 7. Gotchas & takeaways

> Starting a fresh BFS distance count of 0 at the wrong point — counting island 1's own cells as a "step" — off-by-one's the answer; the counter should only increment after expanding into water, and return happens before incrementing on the ring that finds island 2.

- The `break outer` pattern (or an early `return` from a helper) is needed so DFS only marks the FIRST island found, not both.
- Multi-source BFS is the reusable trick here: seed the queue with every starting cell at distance 0, not just one.
- Related problems: Rotting Oranges (multi-source BFS), As Far from Land as Possible (same multi-source BFS pattern, different question).
