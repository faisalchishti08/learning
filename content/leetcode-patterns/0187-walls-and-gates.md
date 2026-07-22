---
card: leetcode-patterns
gi: 187
slug: walls-and-gates
title: Walls and Gates
---

## 1. What it is

Given a grid where `-1` is a wall, `0` is a gate, and `2147483647` (INF) is an empty room, fill each empty room with the distance to its NEAREST gate. If a room cannot reach any gate, it stays `INF`. Example: a grid with one gate at `(0,4)` fills the room directly left of it with `1`, the next with `2`, and so on, stopping at walls.

## 2. Why & when

"Distance to the nearest of several sources" is the multi-source BFS signal, just like As Far from Land as Possible — except here EVERY gate seeds the BFS and every reached room gets WRITTEN its distance directly into the grid, rather than just tracked for a maximum.

## 3. Core concept

**Key idea:** enqueue every gate cell at once, each at distance `0`. BFS expands outward in rings; every time a room is reached for the first time, its distance equals the current ring number, and that value is written directly into the grid at that cell.

**Steps:**
1. Scan the grid; enqueue every cell with value `0` (a gate) into the BFS queue.
2. Run BFS layer by layer. For each cell dequeued, check its 4 neighbors.
3. If a neighbor is an empty room (`INF`), it has never been reached before — set it to `current distance + 1` and enqueue it.
4. Skip neighbors that are walls (`-1`) or already-filled rooms (any value other than `INF`).
5. Continue until the queue empties; any room never reached stays `INF`.

**Why it is correct:** multi-source BFS visits every reachable room in strict order of distance from the nearest gate, because all gates start at distance 0 simultaneously and BFS never revisits a filled-in cell. The first (and only) time a room is reached, the distance assigned is therefore its true shortest distance to the nearest gate.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multi-source BFS from every gate writes shortest distance into each room it reaches">
  <g font-family="sans-serif" font-size="12">
    <rect x="200" y="80" width="30" height="30" fill="#3fb950"/><text x="215" y="100" fill="#0d1117" text-anchor="middle">0</text>
    <rect x="160" y="80" width="30" height="30" fill="#e3b341" opacity="0.6"/><text x="175" y="100" fill="#0d1117" text-anchor="middle">1</text>
    <rect x="120" y="80" width="30" height="30" fill="#79c0ff"/><text x="135" y="100" fill="#0d1117" text-anchor="middle">2</text>
    <rect x="80" y="80" width="30" height="30" fill="#161b22" stroke="#f85149"/><text x="95" y="100" fill="#f85149" text-anchor="middle">-1</text>
    <text x="10" y="15" fill="#e6edf3">gate (green,0) seeds BFS; distance grows outward, wall (red) blocks further spread</text>
  </g>
</svg>

BFS spreads outward from the gate, writing the correct distance into each room as it is first reached, stopping at walls.

## 5. Runnable example

```java
// WallsAndGates.java
import java.util.*;

public class WallsAndGates {
    static final int INF = 2147483647;

    // Level 1 -- Brute force: for every empty room, run a separate
    // BFS/DFS to find the nearest gate, writing that distance in.
    // Correct, but redoes a full search per room instead of computing
    // all rooms' distances together in one pass.

    // KEY INSIGHT: seed the BFS with ALL gates at once (distance 0 for
    // every one of them) -- the first ring to reach a given room IS
    // automatically its nearest gate, computed for every room
    // simultaneously in one traversal.

    // Level 2 -- Optimal: multi-source BFS from all gates.
    static void wallsAndGates(int[][] rooms) {
        if (rooms.length == 0) return;
        int rows = rooms.length, cols = rooms[0].length;
        Queue<int[]> queue = new LinkedList<>();
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (rooms[r][c] == 0) queue.add(new int[]{r, c});
            }
        }

        int[][] dirs = {{0,1},{0,-1},{1,0},{-1,0}};
        while (!queue.isEmpty()) {
            int[] cell = queue.poll();
            for (int[] d : dirs) {
                int nr = cell[0] + d[0], nc = cell[1] + d[1];
                if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
                if (rooms[nr][nc] != INF) continue;
                rooms[nr][nc] = rooms[cell[0]][cell[1]] + 1;
                queue.add(new int[]{nr, nc});
            }
        }
    }

    // Level 3 -- Hardened: rooms with no path to any gate (isolated by
    // walls) are never reached by BFS, so they correctly remain INF,
    // with no special-case code needed.

    public static void main(String[] args) {
        int[][] rooms = {
            {INF, -1, 0, INF},
            {INF, INF, INF, -1},
            {INF, -1, INF, -1},
            {0, -1, INF, INF}
        };
        wallsAndGates(rooms);
        for (int[] row : rooms) System.out.println(Arrays.toString(row));
        // [3, -1, 0, 1]
        // [2, 2, 1, -1]
        // [1, -1, 2, -1]
        // [0, -1, 3, 4]
    }
}
```

**How to run:** `java WallsAndGates.java`

## 6. Walkthrough

Trace the gate at `(0,2)` expanding outward (one of two gates in the example):

| Layer | Cells reached | Distance written |
|---|---|---|
| seed | (0,2) | 0 (gate itself) |
| 1 | (0,3), (1,2) | 1 |
| 2 | (1,1) — via (1,2) | 2 |
| 3 | (1,0) — via (1,1) | 3 |

The second gate at `(3,0)` seeds its own expansion simultaneously; where both gates' rings could reach the same room, whichever ring arrives FIRST (by BFS's simultaneous multi-source property) sets the room's distance, guaranteeing it reflects the nearer gate. Time complexity is O(rows × cols), since each room is written exactly once; space is O(rows × cols) for the queue.

## 7. Gotchas & takeaways

> Gotcha: checking `rooms[nr][nc] == INF` is essential — without it, BFS would re-enqueue and re-process already-filled rooms (and walls/gates), breaking both correctness and the O(rows × cols) time bound.

- Writing the distance directly into the grid doubles as the "visited" marker — no separate `visited` array is needed, since `INF` unambiguously means "not yet reached."
- All gates seed the BFS queue simultaneously, at the SAME initial distance of 0 — this is what makes "nearest gate" come out correct instead of "nearest to whichever gate ran first."
- Related problems: As Far from Land as Possible (same multi-source BFS, but tracks a maximum instead of writing every cell), 01 Matrix (identical structure, `0`s are the multi-source seeds instead of gates).
