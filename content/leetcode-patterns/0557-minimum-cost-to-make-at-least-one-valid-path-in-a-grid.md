---
card: leetcode-patterns
gi: 557
slug: minimum-cost-to-make-at-least-one-valid-path-in-a-grid
title: Minimum Cost to Make at Least One Valid Path in a Grid
---

## 1. What it is

Each cell in an `m x n` grid has an arrow (`1`=right, `2`=left, `3`=down, `4`=up) showing the direction you would move if you followed it for free. You may instead pay `1` to change a cell's direction to any of the other three, and move that way. Return the minimum total cost to build a path from the top-left cell to the bottom-right cell. Example: a grid where following the arrows leads you off-path costs more than redirecting a few cells to route correctly.

## 2. Why & when

This is [0-1 breadth-first search](0550-shortest-path-template-dijkstra-heap-bellman-ford-or-0-1-bfs.md) in disguise: moving in the direction the cell's arrow already points costs `0`, and moving in any other direction costs `1`. Every edge weight is exactly `0` or `1` — the exact special case 0-1 breadth-first search (using a deque) is built for, faster than a general Dijkstra with a full priority queue. Constraints: up to 100x100 grid.

## 3. Core concept

**Key idea:** from each cell, there are 4 possible moves (up, down, left, right) to its neighbors. The move matching the cell's current arrow costs `0`; the other 3 moves cost `1` (paying to redirect). Run 0-1 breadth-first search: push `0`-cost moves to the front of a deque, `1`-cost moves to the back, keeping the deque implicitly sorted by total cost.

**Steps:**
1. Map each direction value (`1,2,3,4`) to its `(dr, dc)` offset.
2. Initialize `cost[start] = 0`, everything else infinity. Push `start` onto a deque.
3. Repeatedly pop from the **front**. For each of the 4 possible moves from this cell: compute `moveCost = 0` if it matches the cell's arrow direction, else `1`. If `cost[node] + moveCost < cost[neighbor]`, update and push — to the **front** if `moveCost == 0`, to the **back** if `moveCost == 1`.
4. Return `cost[bottom-right]`.

**Why this is equivalent to general Dijkstra, just faster:** 0-1 breadth-first search is not a different algorithm in spirit — it is Dijkstra specialized for the case where all weights are `0` or `1`, replacing the `O(log V)` priority queue with an `O(1)` deque push/pop, since the deque's front-to-back ordering can only ever hold at most 2 distinct "next" distances at a time (current layer and current layer + 1) in this special case.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Following an arrow costs 0 and goes to the front of the deque; redirecting costs 1 and goes to the back">
  <g font-family="sans-serif" font-size="13">
    <rect x="30" y="30" width="150" height="50" rx="6" fill="#161b22" stroke="#3fb950"/>
    <text x="105" y="60" fill="#e6edf3" text-anchor="middle">follow arrow: cost 0</text>
    <rect x="220" y="30" width="150" height="50" rx="6" fill="#161b22" stroke="#f0883e"/>
    <text x="295" y="60" fill="#e6edf3" text-anchor="middle">redirect: cost 1</text>
    <text x="105" y="105" fill="#3fb950" text-anchor="middle">deque.addFirst()</text>
    <text x="295" y="105" fill="#f0883e" text-anchor="middle">deque.addLast()</text>
  </g>
</svg>

Zero-cost moves jump to the front of the deque (processed next); cost-1 moves go to the back, keeping the deque sorted by total cost.

## 5. Runnable example

**Level 1 — Brute force.** Try every combination of which cells to redirect, checking whether a valid path results, and track the minimum redirected count. Exponential.

**KEY INSIGHT:** every move costs exactly 0 or 1, so 0-1 breadth-first search with a deque finds the minimum-cost path directly, without exploring combinations of redirections explicitly.

**Level 2 — Optimal.** 0-1 breadth-first search, O(m · n).

**Level 3 — Hardened.** Handles a grid where the arrows already form a valid free path (`cost = 0`), and a 1x1 grid (start equals destination, `cost = 0`).

```java
// MinCostValidPath.java
import java.util.*;

public class MinCostValidPath {

    // direction values: 1=right, 2=left, 3=down, 4=up
    static final int[][] DIRS = {{0, 1}, {0, -1}, {1, 0}, {-1, 0}}; // index 0..3 for directions 1..4

    static int minCost(int[][] grid) {
        int rows = grid.length, cols = grid[0].length;
        int[][] cost = new int[rows][cols];
        for (int[] row : cost) Arrays.fill(row, Integer.MAX_VALUE);
        cost[0][0] = 0;

        Deque<int[]> deque = new ArrayDeque<>();
        deque.add(new int[]{0, 0});

        while (!deque.isEmpty()) {
            int[] cur = deque.pollFirst();
            int r = cur[0], c = cur[1];

            for (int dirIdx = 0; dirIdx < 4; dirIdx++) {
                int nr = r + DIRS[dirIdx][0], nc = c + DIRS[dirIdx][1];
                if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
                int moveCost = (grid[r][c] == dirIdx + 1) ? 0 : 1;
                if (cost[r][c] + moveCost < cost[nr][nc]) {
                    cost[nr][nc] = cost[r][c] + moveCost;
                    if (moveCost == 0) deque.addFirst(new int[]{nr, nc});
                    else deque.addLast(new int[]{nr, nc});
                }
            }
        }
        return cost[rows - 1][cols - 1];
    }

    public static void main(String[] args) {
        int[][] grid1 = {{1, 1, 1, 1}, {2, 2, 2, 2}, {1, 1, 1, 1}, {2, 2, 2, 2}};
        System.out.println(minCost(grid1)); // 3

        int[][] grid2 = {{1, 1}, {1, 1}};
        System.out.println(minCost(grid2)); // 0, arrows already form a free path
    }
}
```

**How to run:** save as `MinCostValidPath.java`, then run `java MinCostValidPath.java`.

## 6. Walkthrough

Trace the start of `minCost([[1,1,1,1],[2,2,2,2],[1,1,1,1],[2,2,2,2]])`:

1. `cost[0][0]=0`. Deque: `[(0,0)]`.
2. Pop `(0,0)`, whose arrow is `1` (right). Move right `(0,1)`: matches arrow, cost `0`, `cost[0][1]=0`, push to front. Move down `(1,0)`: does not match, cost `1`, `cost[1][0]=1`, push to back. (Left and up are out of bounds.)
3. Deque: `[(0,1), (1,0)]`. Pop `(0,1)` next (front), whose arrow is also `1`. Move right `(0,2)`: cost `0`, push to front.
4. This continues, riding the free `1`-arrows across the top row until the path needs to descend, where it must pay to redirect — the algorithm keeps preferring free moves whenever the deque's front offers one, only paying when forced.
5. The full trace eventually finds `cost[3][3] = 3`, the minimum total redirections needed.

## 7. Gotchas & takeaways

> Gotcha: pushing every move to the back of the deque (treating this as plain breadth-first search, ignoring the 0/1 cost distinction) loses the ordering guarantee that makes 0-1 breadth-first search correct — a cost-0 move must jump ahead of already-queued cost-1 moves, or a more expensive path could be explored (and finalized) before a cheaper one.

- Signal: "every move costs exactly 0 or 1" (here: follow the arrow for free, redirect for a cost of 1) is the exact special case 0-1 breadth-first search is built for.
- A grid is a graph where cells are nodes and adjacent cells are edges — recognizing this reframing is the first step for many grid shortest-path problems.
- Related problems: Shortest Path in a Grid with Obstacles Elimination (adds a stateful budget instead of 0/1 costs), Path With Minimum Effort.
