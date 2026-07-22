---
card: leetcode-patterns
gi: 178
slug: matrix-number-of-islands-signal-connected-regions-in-a-2d-gr
title: Matrix / Number of Islands — signal: connected regions in a 2D grid
---

## 1. What it is

Matrix flood fill is the technique of exploring a group of connected cells in a 2D grid that share a property — usually the same value, like `1` for land. You start at one cell and spread outward to every neighbor that still qualifies, exactly like paint flooding across connected regions of a bucket-fill tool.

## 2. Why & when

A brute-force approach might try to compare every cell to every other cell to see if they are connected, which is needlessly expensive and hard to reason about. Flood fill instead starts from one cell and only visits cells that are actually reachable through valid neighbors, which is both simpler to write and tight in complexity.

Learn to recognize these signals in a problem statement:

- **"Grid" or "2D matrix" of `0`s and `1`s (or similar binary/categorical values).** This is the base data shape for the pattern.
- **"Connected region", "island", "component", or "group"** of cells sharing a value, connected 4-directionally (sometimes 8-directionally).
- **"Count how many separate groups"** or **"find the size/perimeter/boundary of a group."** These all require visiting one connected region fully before moving to the next.
- **"Flood fill", "paint", or "fill with a new value"** stated explicitly — a direct restatement of the pattern's name.

The alternative is Union-Find (disjoint set), which is useful when connectivity queries interleave with grid updates, but flood fill (BFS/DFS) is simpler and equally fast for a single full-grid pass.

## 3. Core concept

Flood fill always follows the same shape: pick an unvisited cell that matches the target condition, then explore every reachable neighbor (typically up/down/left/right) that also matches, marking each one visited so it is never processed twice. Repeat over the whole grid to visit every connected region exactly once.

Two implementations achieve this:

**DFS (recursive or explicit stack).** From the starting cell, recurse into each of its 4 valid neighbors immediately, going as deep as possible before backtracking. This is compact and natural for problems that only need to VISIT every cell in the region (counting regions, summing area).

**BFS (queue).** From the starting cell, enqueue all its valid neighbors, then process the queue one layer at a time. This is required whenever you need shortest-distance information (like "distance from a source cell"), since BFS visits cells in order of increasing distance.

The key insight: marking a cell visited THE MOMENT it is discovered (not when it is fully processed) prevents it from being added to the frontier more than once, keeping total work bounded by the grid size.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Flood fill spreading from a start cell to all connected same-value neighbors">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="30" width="30" height="30" fill="#3fb950"/>
    <rect x="50" y="30" width="30" height="30" fill="#3fb950" opacity="0.7"/>
    <rect x="20" y="60" width="30" height="30" fill="#3fb950" opacity="0.7"/>
    <rect x="80" y="30" width="30" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="20" y="90" width="30" height="30" fill="#161b22" stroke="#30363d"/>
    <text x="10" y="15" fill="#e6edf3">start cell (bright green) floods into connected land neighbors (faded green); water cells (grey) stop the spread</text>
  </g>
</svg>

Flood fill spreads from the start cell into every connected land cell, stopping the instant it hits water or the grid edge.

## 5. Runnable example

A tiny probe that checks whether a grid position and its neighbors match the "flood fill" signal condition, to confirm the pattern applies before writing the full traversal.

### Signal-checker

```java
// FloodFillSignal.java
public class FloodFillSignal {
    static boolean isValidGridCell(int[][] grid, int r, int c) {
        return r >= 0 && r < grid.length && c >= 0 && c < grid[0].length;
    }

    public static void main(String[] args) {
        int[][] grid = {
            {1, 1, 0},
            {0, 1, 0},
            {0, 0, 1}
        };
        System.out.println("Is (1,1) a valid in-bounds cell? " + isValidGridCell(grid, 1, 1));
        System.out.println("Is (1,1) land (value 1)? " + (grid[1][1] == 1));
        System.out.println("-> both true means flood fill can start here");
    }
}
```

**How to run:** `java FloodFillSignal.java`

## 6. Walkthrough

1. You read the problem statement. It mentions a grid of `0`s and `1`s and asks you to "count the number of islands" — connected groups of `1`s.
2. "Grid" plus "connected group" is the flood-fill signal: you need to visit every cell of one island fully before counting the next.
3. You scan the grid left to right, top to bottom. The first `1` you find that is not yet visited starts a new flood fill.
4. Running the checker above on `(1,1)` confirms it is both in bounds and land, so a flood fill can begin there, marking every cell of that island visited.
5. After the flood fill from `(1,1)` finishes, you continue scanning; any `1` still unvisited starts another separate island.

## 7. Gotchas & takeaways

> Gotcha: forgetting to mark a cell visited before recursing into it (or right when it is enqueued in BFS) makes the same cell get processed multiple times, sometimes causing infinite recursion in a cycle-shaped region.

- Flood fill needs a way to mark visited cells — either mutating the grid in place (e.g. `1` → `0`) or a separate `visited` boolean array, if the input must stay unmodified.
- 4-directional connectivity (up/down/left/right) is the default; some problems specify 8-directional (including diagonals) — read the problem statement carefully.
- If you see "grid" plus "connected component/region/island," it is almost always flood fill (BFS or DFS), not Union-Find, unless the problem also involves incremental updates.
