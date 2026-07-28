---
card: leetcode-patterns
gi: 535
slug: number-of-islands-ii
title: Number of Islands II
---

## 1. What it is

You start with an `m x n` grid entirely made of water. You are given a sequence of `positions`, each turning one cell into land. After each single land addition, report the current number of islands (an island is a group of land cells connected horizontally or vertically). Example: `m=3, n=3`, `positions = [[0,0],[0,1],[1,2],[2,1]]` → `[1,1,2,3]` (after each addition, in order).

## 2. Why & when

Land is added incrementally, and after every addition you must report a live count of connected groups — exactly the [union-find signal](0523-union-find-signal-dynamic-connectivity-or-grouping-by-equiva.md) of "dynamic connectivity with a running group count." Re-running breadth-first search or depth-first search over the whole grid after every single addition would cost O(k · m · n) for k additions — union-find answers each addition in near O(1) instead. Constraints: up to 10,000 positions, grid up to 10,000 cells total.

## 3. Core concept

**Key idea:** map each grid cell `(r, c)` to a single integer index `r * n + c` so it can be a union-find item. Keep every cell initially "not land" (not yet part of any group). When a position is added: if it is already land (duplicate position), report the current count unchanged. Otherwise, mark it as land (this alone adds one new island), then union it with every one of its up-to-4 neighbors that is *already* land, decrementing the island count once per successful union.

**Steps:**
1. Initialize union-find sized `m * n`, plus a `boolean[] isLand` array (all `false`), and `islandCount = 0`.
2. For each position `(r, c)`: if `isLand[r*n+c]` is already `true`, append the current `islandCount` to the result and skip the rest.
3. Otherwise, set `isLand[r*n+c] = true` and `islandCount++` (this new cell starts as its own island).
4. For each of the 4 neighbors that is in bounds and already land: if `find(neighbor) != find(cell)`, `union` them and decrement `islandCount`.
5. Append `islandCount` to the result and move to the next position.

**Why checking `isLand` on neighbors (not just bounds) matters:** a neighbor cell that is still water is not part of any island yet, and unioning with it would incorrectly merge the new land cell into a "group" that does not represent an actual island — only union with neighbors that are already confirmed land.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Adding land cells one at a time, merging into neighboring land and updating the island count">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">add (0,0): new island, count=1</text>
    <rect x="20" y="30" width="30" height="30" fill="#3fb950" stroke="#30363d"/>
    <rect x="50" y="30" width="30" height="30" fill="#161b22" stroke="#30363d"/>
    <text x="220" y="20" fill="#e6edf3" font-weight="bold">add (0,1): touches (0,0)'s land, count stays 1</text>
    <rect x="220" y="30" width="30" height="30" fill="#3fb950" stroke="#30363d"/>
    <rect x="250" y="30" width="30" height="30" fill="#3fb950" stroke="#30363d"/>
    <text x="450" y="20" fill="#e6edf3" font-weight="bold">add (2,1): no land neighbor, count=2</text>
    <rect x="450" y="30" width="30" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="480" y="30" width="30" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="450" y="90" width="30" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="480" y="90" width="30" height="30" fill="#3fb950" stroke="#30363d"/>
  </g>
</svg>

Each new land cell starts its own island, then merges with any already-land neighbor — the count only drops when a merge with an existing island actually happens.

## 5. Runnable example

**Level 1 — Brute force.** After each position is added, run a fresh breadth-first search or depth-first search over the entire grid to recount islands. O(k · m · n) for k additions.

**KEY INSIGHT:** each addition only needs to check its own up-to-4 neighbors and union with any that are already land — no full grid rescan is needed.

**Level 2 — Optimal.** Union-find over grid cells, checked against a `isLand` marker array, O(k · α(m·n)).

**Level 3 — Hardened.** Handles duplicate positions (adding the same cell twice) without incorrectly incrementing the count.

```java
// NumberOfIslandsII.java
import java.util.*;

public class NumberOfIslandsII {

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
        boolean union(int a, int b) {
            int rootA = find(a), rootB = find(b);
            if (rootA == rootB) return false;
            parent[rootA] = rootB;
            return true;
        }
    }

    static List<Integer> numIslands2(int m, int n, int[][] positions) {
        DSU dsu = new DSU(m * n);
        boolean[] isLand = new boolean[m * n];
        int islandCount = 0;
        List<Integer> result = new ArrayList<>();
        int[][] directions = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};

        for (int[] pos : positions) {
            int r = pos[0], c = pos[1];
            int idx = r * n + c;
            if (isLand[idx]) {
                result.add(islandCount); // duplicate addition, no change
                continue;
            }
            isLand[idx] = true;
            islandCount++;

            for (int[] d : directions) {
                int nr = r + d[0], nc = c + d[1];
                if (nr < 0 || nr >= m || nc < 0 || nc >= n) continue;
                int nIdx = nr * n + nc;
                if (isLand[nIdx] && dsu.union(idx, nIdx)) {
                    islandCount--;
                }
            }
            result.add(islandCount);
        }
        return result;
    }

    public static void main(String[] args) {
        int[][] positions = {{0, 0}, {0, 1}, {1, 2}, {2, 1}};
        System.out.println(numIslands2(3, 3, positions)); // [1, 1, 2, 3]
    }
}
```

**How to run:** save as `NumberOfIslandsII.java`, then run `java NumberOfIslandsII.java`.

## 6. Walkthrough

Trace `numIslands2(3, 3, [[0,0],[0,1],[1,2],[2,1]])`:

| position | new island? | land neighbors found | unions | islandCount | result so far |
|---|---|---|---|---|---|
| (0,0) | yes | none (grid was all water) | 0 | 1 | [1] |
| (0,1) | yes (count->2) | (0,0) is land | 1 union, count->1 | 1 | [1,1] |
| (1,2) | yes (count->2) | none adjacent is land | 0 | 2 | [1,1,2] |
| (2,1) | yes (count->3) | none adjacent is land yet | 0 | 3 | [1,1,2,3] |

Each row shows the count rising by 1 for the new cell, then dropping by 1 per successful merge with an existing island.

## 7. Gotchas & takeaways

> Gotcha: forgetting to check `isLand[neighbor]` before attempting a union treats every neighboring cell (even water) as a potential island member, which would merge groups that should not exist yet and undercount islands.

- Signal: "cells are added one at a time; report the live count of connected groups after each addition" is dynamic connectivity, answered by a running union-find group counter.
- Map 2D grid coordinates to a single integer index (`r * n + c`) so a standard 1D union-find array works directly.
- Related problems: Number of Connected Components in an Undirected Graph, Swim in Rising Water (union-find on a grid with an ordering twist).
