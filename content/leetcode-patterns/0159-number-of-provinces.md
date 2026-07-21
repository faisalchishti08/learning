---
card: leetcode-patterns
gi: 159
slug: number-of-provinces
title: Number of Provinces
---

## 1. What it is

Given an `n x n` matrix `isConnected` where `isConnected[i][j] = 1` if cities `i` and `j` are directly connected (and `0` otherwise), return the number of provinces — groups of cities connected directly or indirectly, forming connected components. Example: `isConnected = [[1,1,0],[1,1,0],[0,0,1]]` → `2` (cities `0` and `1` form one province; city `2` is its own province).

## 2. Why & when

This is the canonical "count connected components" problem: loop over every node, and each time you find one that has not been visited yet, that is the start of a NEW province — run a full DFS or BFS from it to mark every city reachable from it as visited (so they are not counted again), then increment the province count. It belongs in Graph BFS/DFS because the matrix is an adjacency matrix representation of a graph, and "province" is just this problem's name for "connected component."

## 3. Core concept

**Key idea:** iterate over every city. If it has not been visited, it must belong to a province no one has counted yet — increment the count, then DFS/BFS from it to mark its ENTIRE connected component as visited (so none of those cities trigger a duplicate count later in the loop).

**Steps:**
1. Keep a `visited` boolean array of size `n`, all `false` initially. Keep `provinceCount = 0`.
2. Loop `i` from `0` to `n - 1`: if `visited[i]` is already `true`, skip it (already counted as part of an earlier province).
3. Otherwise: increment `provinceCount`. Run DFS (or BFS) starting at `i`, marking every reachable city (`j` where `isConnected[i][j] == 1`, and transitively) as `visited`.
4. After the loop, return `provinceCount`.

**Why it is correct:** every city belongs to exactly one connected component, so the first time the loop encounters an unvisited city, that city's ENTIRE component gets marked visited by the DFS/BFS call, guaranteeing no other city in that same component will ever be seen as "unvisited" later in the loop — so each component is counted exactly once, at the moment its first (lowest-indexed) city is reached.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Looping over unvisited cities, each triggering a full DFS over its province">
  <g font-family="sans-serif" font-size="12">
    <circle cx="80" cy="60" r="16" fill="#161b22" stroke="#3fb950"/><text x="80" y="64" fill="#e6edf3" text-anchor="middle">0</text>
    <circle cx="150" cy="60" r="16" fill="#161b22" stroke="#3fb950"/><text x="150" y="64" fill="#e6edf3" text-anchor="middle">1</text>
    <line x1="96" y1="60" x2="134" y2="60" stroke="#3fb950" stroke-width="2"/>
    <circle cx="280" cy="60" r="16" fill="#161b22" stroke="#79c0ff"/><text x="280" y="64" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="10" y="15" fill="#e6edf3">Loop reaches city 0 (unvisited): province #1, DFS marks 0 and 1 visited.</text>
    <text x="10" y="120" fill="#e6edf3">Loop reaches city 1: already visited, skip.</text>
    <text x="10" y="150" fill="#e6edf3">Loop reaches city 2 (unvisited): province #2, DFS marks just 2 (no connections).</text>
    <text x="10" y="180" fill="#e6edf3">Total provinces: 2</text>
  </g>
</svg>

City `1` is skipped in the outer loop because it was already marked visited while exploring city `0`'s province.

## 5. Runnable example

```java
// NumberOfProvinces.java
public class NumberOfProvinces {

    // Level 1 -- Brute force: use Union-Find (disjoint set), unioning
    // every connected pair, then counting distinct roots. Correct and
    // actually efficient (near O(n^2 * alpha(n))), but requires a
    // separate data structure (parent array, union/find operations)
    // instead of the simpler direct DFS a matrix already supports well.
    static int bruteForce(int[][] isConnected) {
        int n = isConnected.length;
        int[] parent = new int[n];
        for (int i = 0; i < n; i++) parent[i] = i;

        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                if (isConnected[i][j] == 1) union(parent, i, j);
            }
        }
        int count = 0;
        for (int i = 0; i < n; i++) if (find(parent, i) == i) count++;
        return count;
    }

    static int find(int[] parent, int x) {
        while (parent[x] != x) x = parent[x];
        return x;
    }

    static void union(int[] parent, int a, int b) {
        int rootA = find(parent, a), rootB = find(parent, b);
        if (rootA != rootB) parent[rootA] = rootB;
    }

    // KEY INSIGHT: since the input is already a full adjacency MATRIX
    // (not a sparse edge list), a direct DFS/BFS over it needs no extra
    // data structure at all -- just a visited array and a nested loop
    // to find each city's directly connected neighbors.

    // Level 2 -- Optimal: DFS from each unvisited city, marking its
    // whole component visited. O(n^2) time (matrix scan dominates),
    // O(n) space (visited array plus recursion stack).
    public static int findCircleNum(int[][] isConnected) {
        int n = isConnected.length;
        boolean[] visited = new boolean[n];
        int provinceCount = 0;

        for (int i = 0; i < n; i++) {
            if (!visited[i]) {
                provinceCount++;
                dfs(isConnected, visited, i);
            }
        }
        return provinceCount;
    }

    static void dfs(int[][] isConnected, boolean[] visited, int city) {
        visited[city] = true;
        for (int neighbor = 0; neighbor < isConnected.length; neighbor++) {
            if (isConnected[city][neighbor] == 1 && !visited[neighbor]) {
                dfs(isConnected, visited, neighbor);
            }
        }
    }

    // Level 3 -- Hardened: a matrix where every city is isolated
    // (identity matrix, only self-connections) must return n provinces,
    // one per city.
    static int hardened(int[][] isConnected) {
        return findCircleNum(isConnected);
    }

    public static void main(String[] args) {
        int[][] isConnected = {{1,1,0},{1,1,0},{0,0,1}};

        System.out.println(bruteForce(isConnected));
        System.out.println(findCircleNum(isConnected));

        int[][] allIsolated = {{1,0,0},{0,1,0},{0,0,1}};
        System.out.println(hardened(allIsolated));
    }
}
```

How to run: save as `NumberOfProvinces.java`, then run `java NumberOfProvinces.java`.

## 6. Walkthrough

Dry run of `findCircleNum` on `isConnected = [[1,1,0],[1,1,0],[0,0,1]]`:

| outer loop i | visited[i]? | action | provinceCount after |
|---|---|---|---|
| 0 | false | new province; DFS marks 0 and 1 visited (since `isConnected[0][1]==1`) | 1 |
| 1 | true (marked during i=0's DFS) | skip | 1 |
| 2 | false | new province; DFS marks only 2 visited (no connections) | 2 |

Final `provinceCount = 2`. Time complexity: O(n^2), dominated by scanning each row of the adjacency matrix during DFS. Space complexity: O(n) for the visited array plus the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: incrementing `provinceCount` inside the DFS helper (once per city visited) instead of once per OUTER loop iteration that finds an unvisited city would count every city in a province as its own separate province — the increment must happen exactly once, right before starting a new DFS from an unvisited city in the outer loop.

- Because the input is a full adjacency MATRIX (not a list of edges), the "neighbors of city `i`" are found by scanning an entire row (`isConnected[i][...]`), which is why this specific solution costs O(n^2) rather than O(V + E) — the matrix itself has `O(n^2)` cells to potentially examine.
- Related problems: Clone Graph (also traverses a graph with cycles, but needs to build a parallel structure instead of just counting components), Is Graph Bipartite? (also loops over every node to handle disconnected components, but checks a 2-coloring property instead of counting groups).
