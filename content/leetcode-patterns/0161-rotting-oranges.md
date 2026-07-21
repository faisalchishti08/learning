---
card: leetcode-patterns
gi: 161
slug: rotting-oranges
title: Rotting Oranges
---

## 1. What it is

Given an `m x n` grid where each cell is `0` (empty), `1` (fresh orange), or `2` (rotten orange), every minute any fresh orange adjacent (up, down, left, right) to a rotten orange also becomes rotten. Return the minimum number of minutes until no fresh orange remains, or `-1` if that is impossible. Example: `grid = [[2,1,1],[1,1,0],[0,1,1]]` → `4`.

## 2. Why & when

Rot spreads outward one step per minute from EVERY rotten orange simultaneously — this is exactly what multi-source BFS models: seed the queue with ALL rotten oranges at once (not just one), and each full "round" the queue processes corresponds to exactly one minute passing. It belongs in Graph BFS/DFS because BFS naturally processes nodes in order of distance from the source(s), and here "distance" directly means "minutes until rotten."

## 3. Core concept

**Key idea:** start BFS with every initially-rotten orange already in the queue (multi-source BFS), and process the queue one full LEVEL (one minute) at a time, exactly like the Tree BFS `levelSize` trick — except here, the "level" boundary marks a minute passing, not a tree depth.

**Steps:**
1. Scan the grid once: enqueue the `(row, col)` of every cell that starts as `2` (rotten); count every cell that starts as `1` (fresh) into a `freshCount`.
2. If `freshCount == 0` at the start, return `0` immediately (nothing to rot).
3. Set `minutes = 0`. While the queue is not empty AND `freshCount > 0`: save `levelSize = queue.size()`; process exactly `levelSize` oranges (dequeue, check each of its 4 neighbors — if a neighbor is fresh, rot it, decrement `freshCount`, enqueue it); after the inner loop, increment `minutes`.
4. After the loop: if `freshCount > 0`, some fresh oranges were unreachable — return `-1`. Otherwise return `minutes`.

**Why it is correct:** seeding the queue with every rotten orange at once means the BFS explores outward from ALL of them in lockstep, so everything at "distance 1 minute" from any rotten orange is processed together, in one full level-drain, before anything at "distance 2 minutes" begins — exactly matching how rot spreads simultaneously in the real simulation.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multi-source BFS: every initially rotten cell starts in the queue together">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="20" width="40" height="40" fill="#161b22" stroke="#f85149"/><text x="40" y="45" fill="#e6edf3" text-anchor="middle">2</text>
    <rect x="60" y="20" width="40" height="40" fill="#161b22" stroke="#3fb950"/><text x="80" y="45" fill="#e6edf3" text-anchor="middle">1</text>
    <rect x="100" y="20" width="40" height="40" fill="#161b22" stroke="#3fb950"/><text x="120" y="45" fill="#e6edf3" text-anchor="middle">1</text>
    <rect x="20" y="60" width="40" height="40" fill="#161b22" stroke="#3fb950"/><text x="40" y="85" fill="#e6edf3" text-anchor="middle">1</text>
    <rect x="60" y="60" width="40" height="40" fill="#161b22" stroke="#3fb950"/><text x="80" y="85" fill="#e6edf3" text-anchor="middle">1</text>
    <rect x="100" y="60" width="40" height="40" fill="#161b22" stroke="#8b949e"/><text x="120" y="85" fill="#e6edf3" text-anchor="middle">0</text>
    <text x="10" y="15" fill="#e6edf3">Minute 0: one rotten orange (2, red) seeds the queue</text>
    <text x="200" y="45" fill="#e6edf3">Minute 1: its two fresh neighbors (right and below) rot</text>
    <text x="200" y="70" fill="#e6edf3">Minute 2: their fresh neighbors rot next</text>
    <text x="10" y="175" fill="#e6edf3">All rotten cells present at minute 0 spread OUTWARD TOGETHER, one ring per minute</text>
  </g>
</svg>

The single rotten orange spreads to its neighbors first, then to their neighbors, one full ring (minute) at a time.

## 5. Runnable example

```java
// RottingOranges.java
import java.util.*;

public class RottingOranges {

    // Level 1 -- Brute force: repeatedly scan the ENTIRE grid, rotting
    // any fresh orange adjacent to a rotten one, until a full pass makes
    // no changes. O(rows * cols) per pass, times O(rows * cols) passes
    // in the worst case (rot spreading one cell per full grid scan),
    // giving O((rows*cols)^2) overall -- versus BFS's single O(rows*cols) pass.
    static int bruteForce(int[][] grid) {
        int rows = grid.length, cols = grid[0].length;
        int minutes = 0;
        while (true) {
            boolean anyChanged = false;
            int[][] toRot = new int[rows * cols][2];
            int toRotCount = 0;
            for (int r = 0; r < rows; r++) {
                for (int c = 0; c < cols; c++) {
                    if (grid[r][c] == 1 && hasRottenNeighbor(grid, r, c)) {
                        toRot[toRotCount][0] = r; toRot[toRotCount][1] = c; toRotCount++;
                    }
                }
            }
            for (int i = 0; i < toRotCount; i++) { grid[toRot[i][0]][toRot[i][1]] = 2; anyChanged = true; }
            if (!anyChanged) break;
            minutes++;
        }
        for (int[] row : grid) for (int cell : row) if (cell == 1) return -1;
        return minutes;
    }

    static boolean hasRottenNeighbor(int[][] grid, int r, int c) {
        int[][] dirs = {{-1,0},{1,0},{0,-1},{0,1}};
        for (int[] d : dirs) {
            int nr = r + d[0], nc = c + d[1];
            if (nr >= 0 && nr < grid.length && nc >= 0 && nc < grid[0].length && grid[nr][nc] == 2) return true;
        }
        return false;
    }

    // KEY INSIGHT: seeding a BFS queue with EVERY rotten orange at once
    // (multi-source BFS), then draining it one levelSize at a time,
    // simulates every minute in a single O(rows*cols) pass -- no need to
    // repeatedly rescan the whole grid.

    // Level 2 -- Optimal: multi-source BFS, one level per minute.
    // O(rows * cols) time, O(rows * cols) space (queue plus grid scan).
    public static int orangesRotting(int[][] grid) {
        int rows = grid.length, cols = grid[0].length;
        Queue<int[]> queue = new LinkedList<>();
        int freshCount = 0;

        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (grid[r][c] == 2) queue.offer(new int[]{r, c});
                else if (grid[r][c] == 1) freshCount++;
            }
        }

        if (freshCount == 0) return 0;

        int minutes = 0;
        int[][] dirs = {{-1,0},{1,0},{0,-1},{0,1}};
        while (!queue.isEmpty() && freshCount > 0) {
            int levelSize = queue.size();
            for (int i = 0; i < levelSize; i++) {
                int[] cell = queue.poll();
                for (int[] d : dirs) {
                    int nr = cell[0] + d[0], nc = cell[1] + d[1];
                    if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] == 1) {
                        grid[nr][nc] = 2;
                        freshCount--;
                        queue.offer(new int[]{nr, nc});
                    }
                }
            }
            minutes++;
        }
        return freshCount == 0 ? minutes : -1;
    }

    // Level 3 -- Hardened: a grid with fresh oranges that are completely
    // isolated (surrounded by empty cells, unreachable from any rotten
    // orange) must return -1, and a grid with zero fresh oranges must
    // return 0 immediately.
    static int hardened(int[][] grid) {
        return orangesRotting(grid);
    }

    public static void main(String[] args) {
        int[][] grid1 = {{2,1,1},{1,1,0},{0,1,1}};
        System.out.println(bruteForce(deepCopy(grid1)));
        System.out.println(orangesRotting(deepCopy(grid1)));

        int[][] unreachable = {{2,1,1},{0,0,0},{0,1,2}};
        System.out.println(hardened(unreachable));
    }

    static int[][] deepCopy(int[][] grid) {
        int[][] copy = new int[grid.length][];
        for (int i = 0; i < grid.length; i++) copy[i] = grid[i].clone();
        return copy;
    }
}
```

How to run: save as `RottingOranges.java`, then run `java RottingOranges.java`.

## 6. Walkthrough

Dry run of `orangesRotting` on `[[2,1,1],[1,1,0],[0,1,1]]` (one rotten orange at `(0,0)`, `freshCount = 6`):

| minute | levelSize | cells processed | newly rotted | freshCount after |
|---|---|---|---|---|
| 1 | 1 | (0,0) | (0,1), (1,0) | 4 |
| 2 | 2 | (0,1), (1,0) | (0,2), (1,1) | 2 |
| 3 | 2 | (0,2), (1,1) | (2,1) | 1 |
| 4 | 1 | (2,1) | (2,2) | 0 |

After minute 4, `freshCount == 0`, so the loop stops (its condition is checked before starting the next level) and `minutes = 4` is returned. Time complexity: O(rows * cols), each cell enqueued and processed at most once. Space complexity: O(rows * cols) for the queue in the worst case.

## 7. Gotchas & takeaways

> Gotcha: checking for unreachable fresh oranges (`freshCount > 0` after the loop) is essential — a fresh orange that has no path (through adjacent fresh/rotten cells) to any originally-rotten orange will NEVER be rotted, and the function must return `-1` in that case rather than just returning whatever `minutes` happened to reach.

- Seeding the queue with ALL rotten oranges before the loop even starts (rather than adding them one at a time in some order) is what makes this "multi-source" — it is the direct grid analogue of BFS from multiple starting nodes at once in a general graph.
- Related problems: Pacific Atlantic Water Flow (also runs BFS/DFS from multiple border sources simultaneously, there to compute reachability rather than to count elapsed time), Binary Tree Level Order Traversal (the same `levelSize`-per-round technique, there for tree depth rather than elapsed minutes).
