---
card: leetcode-patterns
gi: 536
slug: swim-in-rising-water
title: Swim in Rising Water
---

## 1. What it is

You are given an `n x n` grid where `grid[r][c]` is the elevation of that cell. Water starts rising at time `0`, and at time `t` every cell with elevation `<= t` is submerged and swimmable. You start at `(0,0)` and want to reach `(n-1, n-1)`, moving only through cells with elevation `<= t` at whatever time you pass through them. Return the minimum `t` at which a path from start to end exists. Example: `grid = [[0,2],[1,3]]` → `3` (at `t=3`, every cell is `<= 3`, and a path exists; at `t=2`, cell `(1,1)=3` blocks the only route).

## 2. Why & when

This is a disguised connectivity problem: "what is the smallest threshold `t` such that start and end become connected, using only cells `<= t`" is exactly what [union-find](0524-union-find-template-disjoint-sets-with-union-by-rank-path-co.md) answers when you add cells in increasing order of elevation and check connectivity after each addition. It is also solvable with a priority-queue Dijkstra-style search or binary search plus breadth-first search, but the union-find framing directly matches "process items in a specific order, stop as soon as two points connect." Constraints: up to 50x50 grid.

## 3. Core concept

**Key idea:** sort all cells by elevation. Add them to the grid one at a time, in that order, unioning each newly added cell with any already-added neighbor. The answer is the elevation of the cell whose addition first causes `(0,0)` and `(n-1,n-1)` to share a group — because that is the smallest `t` at which every cell used so far (and hence every cell on some path) has elevation `<= t`.

**Steps:**
1. Collect all cells with their elevations, and sort them by elevation ascending.
2. Initialize union-find over all `n*n` cells, plus a `boolean[] added` array (all `false`).
3. For each cell in sorted order: mark it `added`, then union it with every neighbor that is already `added`.
4. After processing this cell, check if `find(start) == find(end)`. If so, this cell's elevation is the answer — stop.

**Why processing in ascending elevation order gives the *minimum* valid `t`:** at the moment `(0,0)` and `(n-1,n-1)` first become connected, every cell that contributed to that connection has an elevation less than or equal to the current cell's elevation (since cells are added in increasing order). No smaller `t` could have connected them, since that would require some cell in the path to still be unprocessed (elevation greater than `t`), meaning it is not yet swimmable at that time.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cells added in increasing elevation order until start and end connect">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">grid = [[0,2],[1,3]], sorted cells: 0,1,2,3</text>
    <rect x="40" y="40" width="60" height="60" fill="#3fb950" stroke="#30363d"/>
    <text x="70" y="75" fill="#0d1117" text-anchor="middle" font-size="16">0</text>
    <rect x="100" y="40" width="60" height="60" fill="#161b22" stroke="#30363d"/>
    <text x="130" y="75" fill="#e6edf3" text-anchor="middle" font-size="16">2</text>
    <rect x="40" y="100" width="60" height="60" fill="#161b22" stroke="#30363d"/>
    <text x="70" y="135" fill="#e6edf3" text-anchor="middle" font-size="16">1</text>
    <rect x="100" y="100" width="60" height="60" fill="#161b22" stroke="#30363d"/>
    <text x="130" y="135" fill="#e6edf3" text-anchor="middle" font-size="16">3</text>
    <text x="400" y="60" fill="#8b949e">t=0: add (0,0)=0. start alone.</text>
    <text x="400" y="85" fill="#8b949e">t=1: add (1,0)=1, unions with (0,0).</text>
    <text x="400" y="110" fill="#8b949e">t=2: add (0,1)=2, unions with (0,0).</text>
    <text x="400" y="135" fill="#3fb950">t=3: add (1,1)=3, unions with (0,1) and (1,0) -&gt; start and end connect. answer=3</text>
  </g>
</svg>

Cells are added in increasing elevation order; the answer is the elevation at which start and end first share a union-find group.

## 5. Runnable example

**Level 1 — Brute force.** Binary search on `t`, and for each candidate `t`, run a breadth-first search using only cells `<= t` to check if start reaches end. O(n² log(n²)).

**KEY INSIGHT:** instead of testing candidate thresholds one at a time, add cells in sorted elevation order once and union as you go — the answer falls out at the exact moment start and end connect, no repeated searches needed.

**Level 2 — Optimal.** Sort cells once, then a single union-find pass, O(n² log n) for the sort, near O(n²) for the unions.

**Level 3 — Hardened.** Handles the smallest possible grid (`n=1`, answer is `grid[0][0]` since start equals end) and grids where the answer is the maximum elevation in the grid.

```java
// SwimInRisingWater.java
import java.util.*;

public class SwimInRisingWater {

    static class DSU {
        int[] parent;
        DSU(int n) {
            parent = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i;
        }
        int find(int x) {
            if (parent[x] != x) parent[x] = find(parent[x]);
            return parent[x];
        }
        void union(int a, int b) {
            parent[find(a)] = find(b);
        }
    }

    static int swimInWater(int[][] grid) {
        int n = grid.length;
        if (n == 1) return grid[0][0];

        Integer[] cellsByElevation = new Integer[n * n];
        for (int i = 0; i < n * n; i++) cellsByElevation[i] = i;
        Arrays.sort(cellsByElevation, (a, b) -> grid[a / n][a % n] - grid[b / n][b % n]);

        DSU dsu = new DSU(n * n);
        boolean[] added = new boolean[n * n];
        int[][] directions = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};
        int start = 0, end = n * n - 1;

        for (int idx : cellsByElevation) {
            int r = idx / n, c = idx % n;
            added[idx] = true;

            for (int[] d : directions) {
                int nr = r + d[0], nc = c + d[1];
                if (nr < 0 || nr >= n || nc < 0 || nc >= n) continue;
                int nIdx = nr * n + nc;
                if (added[nIdx]) dsu.union(idx, nIdx);
            }

            if (dsu.find(start) == dsu.find(end)) {
                return grid[r][c];
            }
        }
        return -1; // unreachable on a valid grid
    }

    public static void main(String[] args) {
        System.out.println(swimInWater(new int[][]{{0, 2}, {1, 3}})); // 3
        System.out.println(swimInWater(new int[][]{
                {0, 1, 2, 3, 4},
                {24, 23, 22, 21, 5},
                {12, 13, 14, 15, 16},
                {11, 17, 18, 19, 20},
                {10, 9, 8, 7, 6}
        })); // 16
    }
}
```

**How to run:** save as `SwimInRisingWater.java`, then run `java SwimInRisingWater.java`.

## 6. Walkthrough

Trace `swimInWater([[0,2],[1,3]])`, indices `0=(0,0)`, `1=(0,1)`, `2=(1,0)`, `3=(1,1)`, elevations `[0,2,1,3]`, sorted order by elevation: `0 (elev 0), 2 (elev 1), 1 (elev 2), 3 (elev 3)`:

| processed cell | elevation | neighbors already added | union | start & end connected? |
|---|---|---|---|---|
| idx 0 (0,0) | 0 | none | — | no |
| idx 2 (1,0) | 1 | idx 0 | union(2,0) | no |
| idx 1 (0,1) | 2 | idx 0 | union(1,0) | no (end is idx 3, not yet added) |
| idx 3 (1,1) | 3 | idx 1, idx 2 | union(3,1), union(3,2) | **yes** |

The moment cell `(1,1)` (elevation `3`) is added and unioned, `find(0)` and `find(3)` match — return `3`.

## 7. Gotchas & takeaways

> Gotcha: checking connectivity *before* unioning the current cell with its neighbors misses the exact moment the connection forms — always union first, then check, on the same cell.

- Signal: "smallest threshold at which two points become connected" reframes as "add items in sorted order, union as you go, stop at the first connection" — a union-find variant sometimes called an offline/Kruskal-style sweep.
- The `n=1` edge case needs a direct check, since start and end are the same cell and no union ever happens.
- Related problems: Number of Islands II (union-find on a grid, different trigger for adding cells), Redundant Connection (same union-then-check shape, different stopping condition).
