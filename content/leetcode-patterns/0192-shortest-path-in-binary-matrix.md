---
card: leetcode-patterns
gi: 192
slug: shortest-path-in-binary-matrix
title: Shortest Path in Binary Matrix
---

## 1. What it is

Given an `n x n` binary grid, return the length of the shortest CLEAR path from the top-left cell `(0,0)` to the bottom-right cell `(n-1,n-1)`, moving through 8-directionally connected cells with value `0` (including diagonals). Return `-1` if no such path exists. Example: `grid = [[0,1],[1,0]]` → `2`.

## 2. Why & when

"Shortest path" between two specific points in an unweighted grid is the direct BFS signal. The only twist versus earlier problems is that movement is 8-directional (includes diagonals), not 4-directional — a detail that changes the neighbor-generation step but nothing else about the BFS logic.

## 3. Core concept

**Key idea:** BFS from `(0,0)`, treating each of the 8 surrounding cells as a potential neighbor at each step. The first time BFS reaches `(n-1, n-1)`, its layer number (converted to path length by counting cells, not edges) is the answer.

**Steps:**
1. If the start or end cell is blocked (`grid[0][0] != 0` or `grid[n-1][n-1] != 0`), return `-1` immediately.
2. Start BFS from `(0,0)` with path length `1` (counting the starting cell itself).
3. For each cell dequeued, generate its 8 neighbors (up, down, left, right, and all 4 diagonals).
4. Skip a neighbor if it is out of bounds, blocked (`1`), or already visited.
5. If a neighbor is `(n-1, n-1)`, return the current path length + 1.
6. Otherwise, mark it visited and enqueue it with path length + 1.
7. If the queue empties without reaching the target, return `-1`.

**Why it is correct:** BFS explores cells in strict order of distance (path length) from the start. The first time the target cell is reached, no shorter clear path could exist, since BFS never skips over a shorter route when one is available through unblocked cells.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="8-directional BFS including diagonal moves finds the shortest clear path">
  <g font-family="sans-serif" font-size="12">
    <circle cx="60" cy="60" r="16" fill="#161b22" stroke="#3fb950"/><text x="60" y="64" fill="#e6edf3" text-anchor="middle" font-size="10">start</text>
    <circle cx="180" cy="130" r="16" fill="#161b22" stroke="#e3b341"/><text x="180" y="134" fill="#e6edf3" text-anchor="middle" font-size="10">end</text>
    <line x1="75" y1="72" x2="165" y2="118" stroke="#8b949e" stroke-dasharray="4,3"/>
    <text x="10" y="15" fill="#e6edf3">diagonal move (dashed) is allowed -- one step covers both a row and column shift</text>
  </g>
</svg>

A diagonal move counts as a single step, letting BFS reach the target cell in fewer steps than 4-directional movement would allow.

## 5. Runnable example

```java
// ShortestPathInBinaryMatrix.java
import java.util.*;

public class ShortestPathInBinaryMatrix {

    // Level 1 -- Brute force: DFS trying every possible clear path,
    // tracking the minimum length found. Correct, but DFS explores far
    // more paths than needed and has no natural early-stopping
    // guarantee for shortest without extra bookkeeping.

    // KEY INSIGHT: this is shortest-path-in-an-unweighted-graph, just
    // with 8-directional edges instead of 4 -- BFS finds it directly,
    // by exploring in distance order regardless of how many directions
    // each step can move in.

    // Level 2 -- Optimal: BFS with 8-directional neighbor generation.
    static int shortestPathBinaryMatrix(int[][] grid) {
        int n = grid.length;
        if (grid[0][0] != 0 || grid[n-1][n-1] != 0) return -1;
        if (n == 1) return 1;

        boolean[][] visited = new boolean[n][n];
        Queue<int[]> queue = new LinkedList<>();
        queue.add(new int[]{0, 0});
        visited[0][0] = true;
        int[][] dirs = {{0,1},{0,-1},{1,0},{-1,0},{1,1},{1,-1},{-1,1},{-1,-1}};
        int length = 1;

        while (!queue.isEmpty()) {
            int size = queue.size();
            for (int i = 0; i < size; i++) {
                int[] cell = queue.poll();
                if (cell[0] == n - 1 && cell[1] == n - 1) return length;
                for (int[] d : dirs) {
                    int nr = cell[0] + d[0], nc = cell[1] + d[1];
                    if (nr < 0 || nr >= n || nc < 0 || nc >= n || visited[nr][nc] || grid[nr][nc] != 0) continue;
                    visited[nr][nc] = true;
                    queue.add(new int[]{nr, nc});
                }
            }
            length++;
        }
        return -1;
    }

    // Level 3 -- Hardened: the n == 1 case (single-cell grid, start
    // equals end) is checked explicitly and returns 1, since the main
    // BFS loop's "check on dequeue" logic would otherwise need an
    // extra check before entering the loop.

    public static void main(String[] args) {
        System.out.println(shortestPathBinaryMatrix(new int[][]{{0,1},{1,0}})); // 2
        System.out.println(shortestPathBinaryMatrix(new int[][]{{0,0,0},{1,1,0},{1,1,0}})); // 4
        System.out.println(shortestPathBinaryMatrix(new int[][]{{1,0,0},{1,1,0},{1,1,0}})); // -1
    }
}
```

**How to run:** `java ShortestPathInBinaryMatrix.java`

## 6. Walkthrough

Trace `grid = [[0,1],[1,0]]`, `n = 2`:

| Step | Queue | length | Action |
|---|---|---|---|
| 1 | [(0,0)] | 1 | dequeue (0,0), not target; check 8 neighbors — only (1,1) is in bounds and unblocked (diagonal move) |
| 2 | [(1,1)] | 1 | enqueue (1,1) | 
| 3 | — | 2 | new layer; dequeue (1,1), equals target (n-1,n-1) → return 2 |

Time complexity is O(n²), since each of the n² cells is visited at most once, each with 8 constant-time neighbor checks; space is O(n²) for the visited array and queue.

## 7. Gotchas & takeaways

> Gotcha: using only 4-directional movement (forgetting the 4 diagonal directions) gives a WRONG (too large, or `-1` when a path actually exists) answer for this specific problem — always confirm from the problem statement whether diagonal movement is allowed.

- Check the target cell equality WHEN DEQUEUING (or when generating it as a neighbor) — both work, but be consistent about which point you increment `length` relative to.
- The `n == 1` edge case (single-cell grid) needs an explicit check, since the main loop structure assumes at least one BFS layer expansion happens.
- Related problems: Nearest Exit from Entrance in Maze (4-directional BFS to a set of targets), Rotting Oranges (multi-source BFS, 4-directional).
