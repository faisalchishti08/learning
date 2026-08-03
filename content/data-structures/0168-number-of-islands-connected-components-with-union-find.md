---
card: data-structures
gi: 168
slug: number-of-islands-connected-components-with-union-find
title: Number of islands / connected components with union-find
---

## 1. What it is

"Number of islands" and "count connected components" are classic problems where you count the number of separate connected groups in a grid or graph. Both can be solved with BFS/DFS, but they are also a direct, clean application of [union-find](0162-disjoint-set-data-structure.md): union every pair of adjacent same-type cells (or connected nodes), and the final answer is the number of distinct roots remaining.

## 2. Why & when

Use the union-find approach when the input arrives as a **stream of connections** rather than a fixed structure you can traverse once — for example, land cells being added to a grid over time ("Number of Islands II"), or edges being added to a graph incrementally. BFS/DFS is often simpler for a single, static grid; union-find shines when you need the component count to stay correct as more connections are added, without redoing a full traversal each time.

## 3. Core concept

**The core idea.** Treat each grid cell (or graph node) as an item in a disjoint-set structure. Initialize every land cell (or every node) as its own group, so the initial component count equals the number of land cells. Then, for every pair of adjacent land cells, call `union` — each successful `union` (one that actually merges two different groups) decreases the component count by exactly `1`.

**Mapping a 2D grid to a 1D union-find index.** A grid cell `(row, col)` in a grid with `cols` columns maps to a single integer index `row * cols + col`. This lets you reuse the same flat `parent[]` array design as any other union-find problem.

**Why counting merges works.** Every group starts as its own component. A `union` call either merges two previously-separate components into one (component count decreases by `1`) or does nothing because they were already the same component (count unchanged). Tracking this running count avoids a final `O(n)` pass to count distinct roots.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A grid with land and water cells, showing adjacent land cells unioned into two separate island components">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <g transform="translate(20,20)">
      <rect x="0" y="0" width="40" height="40" fill="#3fb950" fill-opacity="0.3" stroke="#3fb950"/><text x="20" y="24" text-anchor="middle">L</text>
      <rect x="40" y="0" width="40" height="40" fill="#3fb950" fill-opacity="0.3" stroke="#3fb950"/><text x="60" y="24" text-anchor="middle">L</text>
      <rect x="80" y="0" width="40" height="40" fill="#0d1117" stroke="#8b949e"/><text x="100" y="24" text-anchor="middle">W</text>
      <rect x="120" y="0" width="40" height="40" fill="#f0883e" fill-opacity="0.3" stroke="#f0883e"/><text x="140" y="24" text-anchor="middle">L</text>

      <rect x="0" y="40" width="40" height="40" fill="#0d1117" stroke="#8b949e"/><text x="20" y="64" text-anchor="middle">W</text>
      <rect x="40" y="40" width="40" height="40" fill="#0d1117" stroke="#8b949e"/><text x="60" y="64" text-anchor="middle">W</text>
      <rect x="80" y="40" width="40" height="40" fill="#0d1117" stroke="#8b949e"/><text x="100" y="64" text-anchor="middle">W</text>
      <rect x="120" y="40" width="40" height="40" fill="#f0883e" fill-opacity="0.3" stroke="#f0883e"/><text x="140" y="64" text-anchor="middle">L</text>
    </g>
    <text x="320" y="40" font-size="9">Green cells (0,0)-(0,1): union -&gt; 1 component</text>
    <text x="320" y="60" font-size="9">Orange cells (0,3)-(1,3): union -&gt; 1 component</text>
    <text x="320" y="90" font-size="9" fill="#8b949e">Total land cells: 5. After unions: 2 components (islands).</text>
  </g>
</svg>

Adjacent land cells merge into one component; the final distinct-root count is the island count.

## 5. Runnable example

```java
// NumberOfIslands.java
import java.util.*;

public class NumberOfIslands {

    static class DSU {
        int[] parent, rank;
        int components;

        DSU(int n) {
            parent = new int[n];
            rank = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i;
        }

        int find(int x) {
            if (parent[x] != x) parent[x] = find(parent[x]);
            return parent[x];
        }

        void union(int x, int y) {
            int rootX = find(x), rootY = find(y);
            if (rootX == rootY) return;
            if (rank[rootX] < rank[rootY]) parent[rootX] = rootY;
            else if (rank[rootX] > rank[rootY]) parent[rootY] = rootX;
            else { parent[rootY] = rootX; rank[rootX]++; }
            components--;
        }
    }

    // Basic: count islands in a fixed grid by unioning every adjacent pair of land cells.
    static int numIslands(char[][] grid) {
        int rows = grid.length, cols = grid[0].length;
        DSU dsu = new DSU(rows * cols);
        dsu.components = 0;

        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (grid[r][c] == '1') dsu.components++;
            }
        }

        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (grid[r][c] != '1') continue;
                int index = r * cols + c;
                if (r + 1 < rows && grid[r + 1][c] == '1') dsu.union(index, (r + 1) * cols + c);
                if (c + 1 < cols && grid[r][c + 1] == '1') dsu.union(index, r * cols + (c + 1));
            }
        }
        return dsu.components;
    }

    static void basicLevel() {
        char[][] grid = {
            {'1', '1', '0', '1'},
            {'0', '0', '0', '1'}
        };
        System.out.println("basic: numIslands -> " + numIslands(grid));
    }

    // Intermediate: general connected-component counting on a graph given as an edge list (not a grid).
    static int countComponents(int n, int[][] edges) {
        DSU dsu = new DSU(n);
        dsu.components = n;
        for (int[] edge : edges) dsu.union(edge[0], edge[1]);
        return dsu.components;
    }

    static void intermediateLevel() {
        int[][] edges = {{0, 1}, {1, 2}, {3, 4}};
        System.out.println("intermediate: countComponents(6 nodes) -> " + countComponents(6, edges));
    }

    // Advanced: "Number of Islands II" -- land cells are ADDED one at a time; report the running island count after each addition.
    static List<Integer> numIslandsII(int rows, int cols, int[][] addedLand) {
        DSU dsu = new DSU(rows * cols);
        boolean[][] isLand = new boolean[rows][cols];
        List<Integer> results = new ArrayList<>();
        int[][] directions = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};

        for (int[] cell : addedLand) {
            int r = cell[0], c = cell[1];
            if (isLand[r][c]) { results.add(dsu.components); continue; } // duplicate addition, no change
            isLand[r][c] = true;
            dsu.components++;
            int index = r * cols + c;
            for (int[] d : directions) {
                int nr = r + d[0], nc = c + d[1];
                if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && isLand[nr][nc]) {
                    dsu.union(index, nr * cols + nc);
                }
            }
            results.add(dsu.components);
        }
        return results;
    }

    static void advancedLevel() {
        int[][] added = {{0, 0}, {0, 1}, {1, 2}, {1, 0}, {0, 1}};
        List<Integer> history = numIslandsII(3, 3, added);
        System.out.println("advanced: island count after each addition -> " + history);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java NumberOfIslands.java`

## 6. Walkthrough

Trace `numIslands` on the grid:
```
1 1 0 1
0 0 0 1
```
Count land cells first: `(0,0), (0,1), (0,3), (1,3)` — 4 land cells, so `components` starts at `4`.

Scan for adjacent land pairs. `(0,0)` and `(0,1)` are both land and horizontally adjacent: `union` merges them, `components` drops to `3`. `(0,3)` and `(1,3)` are both land and vertically adjacent: `union` merges them, `components` drops to `2`. No other adjacent land pairs exist. Final answer: `2` islands — matching the two visually separate clusters in the diagram.

For `numIslandsII`, land is added incrementally: `(0,0)`, then `(0,1)` (adjacent to `(0,0)`, merges, count `2` -> stays consistent), `(1,2)` (isolated, count increases), `(1,0)` (adjacent to `(0,0)`'s group, merges), and finally a duplicate `(0,1)` which is skipped since it is already land. The running count after each step shows the island count evolving in real time — something a fresh BFS/DFS per step would compute far less efficiently.

**Complexity.** Grid version: `O(rows * cols * α(rows * cols))`, essentially linear in the grid size. `numIslandsII` with `k` additions: `O(k * α(rows * cols))`, far better than re-running BFS/DFS from scratch after each addition, which would cost `O(k * rows * cols)`.

## 7. Gotchas & takeaways

> Only check two directions (down and right) when unioning a static grid, not all four — checking all four directions still gives the right answer but does duplicate work, since each adjacency gets visited from both cells otherwise.

- For a static, one-time grid, BFS/DFS flood-fill is simpler to write and equally efficient — reach for union-find specifically when cells or edges arrive incrementally, as in `numIslandsII`.
- Always map 2D coordinates to a single 1D index consistently (`row * cols + col`); a mismatched mapping is a common source of bugs in grid union-find code.
- Track the component count as a running counter updated inside `union`, rather than recomputing it by scanning for distinct roots — that scan alone would cost `O(n)` and defeat the point of incremental tracking.
