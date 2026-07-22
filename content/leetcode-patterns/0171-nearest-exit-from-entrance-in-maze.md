---
card: leetcode-patterns
gi: 171
slug: nearest-exit-from-entrance-in-maze
title: Nearest Exit from Entrance in Maze
---

## 1. What it is

Given an `m x n` maze grid of `'.'` (empty) and `'+'` (wall) cells, and a starting `entrance` cell, return the minimum number of steps to reach any exit. An exit is any empty border cell that is NOT the entrance itself. Return `-1` if no exit is reachable. Example: `maze = [["+","+",".","+"],[".",".",".","+"],["+","+","+","."]]`, `entrance = [1,2]` → `1`.

## 2. Why & when

"Fewest steps to the nearest X" in an unweighted grid is a textbook BFS signal. BFS explores in expanding rings of distance, so the first border cell it reaches (that isn't the entrance) is guaranteed to be the nearest one.

## 3. Core concept

**Key idea:** BFS from `entrance`, treating each `'.'` cell as a graph node connected to its 4-directional `'.'` neighbors. The first time BFS dequeues a cell on the border that is not the entrance, return its distance.

**Steps:**
1. Start BFS from `entrance`, marking it visited (mutate the grid to `'+'`, or use a separate visited array) with distance `0`.
2. For each cell dequeued, check if it is a border cell (row `0`/last row, or column `0`/last column) AND it is not the entrance. If so, return its distance.
3. Otherwise, expand into its 4 unvisited, non-wall neighbors, marking them visited and enqueuing with distance + 1.
4. If the queue empties without finding an exit, return `-1`.

**Why it is correct:** BFS explores cells in strict order of distance from `entrance`. The first border cell (other than the entrance) it dequeues cannot be beaten by any cell dequeued later, since BFS processes cells in non-decreasing distance order.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BFS from entrance expanding rings, first border cell reached is the nearest exit">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="20" width="200" height="120" fill="none" stroke="#8b949e"/>
    <rect x="160" y="60" width="40" height="40" fill="#3fb950"/><text x="180" y="84" fill="#0d1117" text-anchor="middle">E</text>
    <rect x="120" y="60" width="40" height="40" fill="#e3b341" opacity="0.5"/>
    <rect x="200" y="60" width="20" height="40" fill="#79c0ff"/>
    <text x="20" y="15" fill="#e6edf3">entrance (green) at [1,2]; ring 1 (gold) expands; border cell (blue) reached first = nearest exit</text>
  </g>
</svg>

BFS ring 1 reaches the border cell to the right of the entrance first — that is the nearest exit, at distance 1.

## 5. Runnable example

```java
// NearestExitFromEntranceInMaze.java
import java.util.*;

public class NearestExitFromEntranceInMaze {

    // Level 1 -- Brute force: DFS to every reachable border cell,
    // tracking the minimum distance found so far across all of them.
    // Correct, but DFS must fully explore the maze and compare many
    // path lengths, instead of stopping the instant the nearest one is
    // found.

    // KEY INSIGHT: BFS naturally visits cells in increasing distance
    // order, so the FIRST valid exit it dequeues is automatically the
    // nearest one -- no comparison across paths needed.

    // Level 2 -- Optimal: BFS from entrance, early-return on first
    // valid border cell.
    static int nearestExit(char[][] maze, int[] entrance) {
        int rows = maze.length, cols = maze[0].length;
        boolean[][] visited = new boolean[rows][cols];
        Queue<int[]> queue = new LinkedList<>();
        queue.add(new int[]{entrance[0], entrance[1]});
        visited[entrance[0]][entrance[1]] = true;
        int[][] dirs = {{0,1},{0,-1},{1,0},{-1,0}};
        int steps = 0;

        while (!queue.isEmpty()) {
            steps++;
            int size = queue.size();
            for (int i = 0; i < size; i++) {
                int[] cell = queue.poll();
                for (int[] d : dirs) {
                    int nr = cell[0] + d[0], nc = cell[1] + d[1];
                    if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
                    if (visited[nr][nc] || maze[nr][nc] == '+') continue;
                    boolean isBorder = nr == 0 || nr == rows - 1 || nc == 0 || nc == cols - 1;
                    if (isBorder) return steps;
                    visited[nr][nc] = true;
                    queue.add(new int[]{nr, nc});
                }
            }
        }
        return -1;
    }

    // Level 3 -- Hardened: the entrance itself may sit on the border,
    // but it is excluded by construction -- the border check only runs
    // on NEWLY discovered neighbor cells, never on entrance itself.

    public static void main(String[] args) {
        System.out.println(nearestExit(new char[][]{
            {'+','+','.','+'},{'.','.','.','+'},{'+','+','+','.'}
        }, new int[]{1,2})); // 1
        System.out.println(nearestExit(new char[][]{
            {'+','+','+'},{'.','.','.'},{'+','+','+'}
        }, new int[]{1,0})); // 2
        System.out.println(nearestExit(new char[][]{{'.','+'}}, new int[]{0,0})); // -1
    }
}
```

**How to run:** `java NearestExitFromEntranceInMaze.java`

## 6. Walkthrough

Trace `entrance = [1,2]` on the example maze:

| Step | Queue before | Action | steps |
|---|---|---|---|
| 1 | `[(1,2)]` | dequeue (1,2), check neighbors | 1 |
| 2 | — | (1,1) is `.`, not border, enqueue | 1 |
| 3 | — | (2,2) is `+`, skip | 1 |
| 4 | — | (1,3) is `+`, skip | 1 |
| 5 | — | (0,2) is `.`, IS border, not entrance → return 1 | — |

Time complexity is O(rows × cols), since each cell is visited at most once; space is O(rows × cols) for the visited array and queue.

## 7. Gotchas & takeaways

> Checking "is this a border cell" on the `entrance` itself (before excluding it) returns `0` incorrectly when the entrance sits on the border — the exclusion must apply to the START cell specifically, not to every border cell in general.

- Only newly-discovered cells are checked for "is exit" — the entrance is pre-marked visited and never re-examined as a candidate.
- Mutating the grid in place (writing `'+'` over visited cells) saves the extra `visited` array's memory, if the input can be modified.
- Related problems: Rotting Oranges (multi-source BFS timing), Shortest Bridge (BFS layer counting to a target region).
