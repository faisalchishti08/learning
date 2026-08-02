---
card: data-structures
gi: 149
slug: connected-components-flood-fill
title: Connected components & flood fill
---

## 1. What it is

**Flood fill** is connected-components logic applied to a 2D grid: starting from one cell, it spreads to every adjacent cell that shares the same property (usually the same color or value), marking the whole connected region. It is the algorithm behind a paint bucket tool, and it is the same idea as [Connectivity & components](0138-connectivity-components.md), just with a grid's implicit up/down/left/right adjacency instead of an explicit edge list.

## 2. Why & when

Any time you need to find a connected region in a grid — the paint bucket tool in an image editor, counting islands in a 2D map, finding connected regions of the same terrain type in a game map — flood fill is the direct tool. It reframes the grid as an implicit graph: each cell is a vertex, and edges connect it to its (usually 4) orthogonal neighbors, with no adjacency list ever explicitly built.

## 3. Core concept

**How the operation works.** Starting from a cell `(row, col)`, if it matches the target property and has not yet been visited, mark it visited (or change its value, for a paint-bucket-style fill) and recursively (or iteratively, via a queue/stack) visit its 4 orthogonal neighbors: up, down, left, right. Stop expanding from any cell that is out of bounds, does not match the target property, or has already been visited.

**Why a grid needs no explicit adjacency list.** A cell `(row, col)`'s neighbors are always `(row-1, col)`, `(row+1, col)`, `(row, col-1)`, `(row, col+1)` — computed directly from its coordinates, exactly like a heap's array-index arithmetic. This is why flood fill never needs to build a `Map<Vertex, List<Vertex>>` the way a general graph algorithm does.

**BFS or DFS — both work.** Flood fill can be implemented with either a queue (BFS-style, level by level) or a stack/recursion (DFS-style, depth-first) — unlike shortest-path problems, where BFS specifically matters for finding the fewest-hop route, flood fill only cares about *which* cells are reachable, not the order or distance, so either traversal strategy gives the same final result.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A grid where flood fill starting from one blue cell spreads to all orthogonally connected blue cells, stopping at cells of a different color">
  <g font-family="sans-serif" font-size="11">
    <rect x="40" y="30" width="50" height="50" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/>
    <rect x="90" y="30" width="50" height="50" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/>
    <rect x="140" y="30" width="50" height="50" fill="#161b22" stroke="#8b949e"/>
    <rect x="40" y="80" width="50" height="50" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/>
    <rect x="90" y="80" width="50" height="50" fill="#161b22" stroke="#8b949e"/>
    <rect x="140" y="80" width="50" height="50" fill="#161b22" stroke="#8b949e"/>
    <text x="65" y="60" fill="#79c0ff" text-anchor="middle" font-size="9">start</text>
    <text x="115" y="60" fill="#79c0ff" text-anchor="middle" font-size="9">fill</text>
    <text x="65" y="110" fill="#79c0ff" text-anchor="middle" font-size="9">fill</text>
    <text x="165" y="60" fill="#8b949e" text-anchor="middle" font-size="9">stop</text>
    <text x="115" y="110" fill="#8b949e" text-anchor="middle" font-size="9">stop</text>
    <text x="165" y="110" fill="#8b949e" text-anchor="middle" font-size="9">stop</text>
    <text x="330" y="65" fill="#79c0ff" font-size="10">flood fill spreads through matching orthogonal neighbors</text>
    <text x="330" y="90" fill="#8b949e" font-size="10">and stops the instant a cell's value differs from the target</text>
  </g>
</svg>

Starting from the top-left cell, flood fill spreads to its matching orthogonal neighbors (right, then down), but stops immediately at any cell with a different value — those cells are never visited or changed.

## 5. Runnable example

```java
// FloodFill.java
public class FloodFill {

    // Basic: recursive flood fill -- paint-bucket style, replacing one value with another.
    static void floodFill(int[][] grid, int row, int col, int targetValue, int newValue) {
        if (row < 0 || row >= grid.length || col < 0 || col >= grid[0].length) return; // out of bounds
        if (grid[row][col] != targetValue) return; // doesn't match -- stop spreading here
        if (targetValue == newValue) return; // avoid infinite recursion if the fill value equals the target

        grid[row][col] = newValue;
        floodFill(grid, row - 1, col, targetValue, newValue); // up
        floodFill(grid, row + 1, col, targetValue, newValue); // down
        floodFill(grid, row, col - 1, targetValue, newValue); // left
        floodFill(grid, row, col + 1, targetValue, newValue); // right
    }

    static void printGrid(int[][] grid) {
        for (int[] row : grid) System.out.println("  " + java.util.Arrays.toString(row));
    }

    static void basicLevel() {
        int[][] grid = {
            {1, 1, 0},
            {1, 0, 0},
            {0, 0, 1}
        };
        System.out.println("basic: before flood fill from (0,0):");
        printGrid(grid);
        floodFill(grid, 0, 0, 1, 2);
        System.out.println("basic: after flood fill (1 -> 2), starting at (0,0):");
        printGrid(grid);
    }

    // Intermediate: count connected components (islands) in a grid -- flood fill restarted from each unvisited land cell.
    static void markVisited(int[][] grid, boolean[][] visited, int row, int col) {
        if (row < 0 || row >= grid.length || col < 0 || col >= grid[0].length) return;
        if (visited[row][col] || grid[row][col] == 0) return;

        visited[row][col] = true;
        markVisited(grid, visited, row - 1, col);
        markVisited(grid, visited, row + 1, col);
        markVisited(grid, visited, row, col - 1);
        markVisited(grid, visited, row, col + 1);
    }

    static int countIslands(int[][] grid) {
        boolean[][] visited = new boolean[grid.length][grid[0].length];
        int islands = 0;
        for (int row = 0; row < grid.length; row++) {
            for (int col = 0; col < grid[0].length; col++) {
                if (grid[row][col] == 1 && !visited[row][col]) {
                    islands++;
                    markVisited(grid, visited, row, col);
                }
            }
        }
        return islands;
    }

    static void intermediateLevel() {
        int[][] grid = {
            {1, 1, 0, 0},
            {1, 0, 0, 1},
            {0, 0, 1, 1}
        };
        System.out.println("intermediate: number of islands -> " + countIslands(grid) + " (expected 3)");
    }

    // Advanced: iterative (queue-based) flood fill -- avoids recursion depth limits on very large grids.
    static void floodFillIterative(int[][] grid, int startRow, int startCol, int targetValue, int newValue) {
        if (grid[startRow][startCol] != targetValue || targetValue == newValue) return;

        java.util.Queue<int[]> queue = new java.util.LinkedList<>();
        queue.offer(new int[]{startRow, startCol});
        grid[startRow][startCol] = newValue;

        int[][] directions = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};
        while (!queue.isEmpty()) {
            int[] cell = queue.poll();
            for (int[] direction : directions) {
                int newRow = cell[0] + direction[0], newCol = cell[1] + direction[1];
                if (newRow >= 0 && newRow < grid.length && newCol >= 0 && newCol < grid[0].length
                    && grid[newRow][newCol] == targetValue) {
                    grid[newRow][newCol] = newValue;
                    queue.offer(new int[]{newRow, newCol});
                }
            }
        }
    }

    static void advancedLevel() {
        int[][] grid = {
            {1, 1, 0},
            {1, 1, 0},
            {0, 0, 1}
        };
        floodFillIterative(grid, 0, 0, 1, 9);
        System.out.println("advanced: after iterative flood fill (1 -> 9) from (0,0):");
        printGrid(grid);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `FloodFill.java`, then run `java FloodFill.java`.

## 6. Walkthrough

1. `basicLevel()` starts flood fill at `(0,0)`, which holds `1`. It changes that cell to `2`, then recurses in all 4 directions. `(0,1)` also holds `1`, so it too becomes `2`, and recursion continues from there. `(1,0)` similarly becomes `2`. The cell `(0,2)` (value `0`) and the isolated `1` at `(2,2)` are never touched, since flood fill never reaches them from the starting region — they are not orthogonally connected to it.
2. `intermediateLevel()` restarts a flood-fill-style marking from every unvisited `1`-cell, counting how many separate restarts are needed — exactly the connected-components pattern from [Connectivity & components](0138-connectivity-components.md), applied to a grid. The result correctly counts `3` separate islands of connected `1`s.
3. `advancedLevel()` performs the same fill using an explicit queue instead of recursion, processing one cell at a time and checking all 4 directions via a small `directions` array. This avoids relying on the call stack, which matters for very large or very "wide" connected regions where recursion could hit a stack-depth limit.

## 7. Gotchas & takeaways

> Gotcha: forgetting the `targetValue == newValue` guard causes infinite recursion (or an infinite loop, in the iterative form) when the fill color happens to already match the target — each cell would re-trigger a "fill" that changes nothing but never terminates.

- Flood fill is connected-components logic on a grid, using each cell's 4 (or 8) orthogonal/diagonal neighbors as its implicit adjacency, computed directly from coordinates.
- Either BFS (queue) or DFS (recursion/stack) works correctly, since flood fill only cares about which cells are reachable, not the order or distance.
- Counting connected regions (islands) reuses the exact same "restart from every unvisited starting cell" pattern as counting connected components in a general graph.
- Related concepts: [Connectivity & components](0138-connectivity-components.md), [Breadth-first search (BFS)](0144-breadth-first-search-bfs.md), [Depth-first search (DFS)](0145-depth-first-search-dfs.md).
