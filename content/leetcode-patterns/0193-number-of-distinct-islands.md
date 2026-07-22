---
card: leetcode-patterns
gi: 193
slug: number-of-distinct-islands
title: Number of Distinct Islands
---

## 1. What it is

Given a grid of `0`s and `1`s, return the number of DISTINCT island shapes, where two islands are considered the same shape if one can be translated (shifted, not rotated or reflected) to exactly match the other. Example: `grid = [[1,1,0,0,0],[1,1,0,0,0],[0,0,0,1,1],[0,0,0,1,1]]` → `1` (both islands are 2×2 squares).

## 2. Why & when

This is Number of Islands with each region's SHAPE captured and deduplicated, instead of just counted. The key challenge is representing a shape in a way that is independent of WHERE the island sits in the grid (translation-invariant), so two islands with identical shapes but different positions compare equal.

## 3. Core concept

**Key idea:** flood fill each island, but instead of just marking cells visited, record the SEQUENCE of moves (or relative coordinates) taken during the traversal. Because DFS always explores neighbors in the same fixed order, two islands with the same shape produce the identical move sequence, regardless of their absolute position. Store these sequences in a set; the set's size is the answer.

**Steps:**
1. Scan the grid; for every unvisited land cell, start a DFS that also builds a signature string.
2. During DFS, append a direction character (e.g. `'D'`, `'U'`, `'L'`, `'R'`) each time you move INTO a cell, and a distinct backtrack marker (e.g. `'B'`) each time you return from a recursive call — this captures the exact shape of the traversal, not just which cells were visited.
3. Add the completed signature string to a `Set<String>` after each island's DFS finishes.
4. Return the set's size after scanning the whole grid.

**Why it is correct:** DFS visiting neighbors in a FIXED, consistent order (e.g. always try down, then up, then right, then left) means the sequence of moves it makes is entirely determined by the island's shape relative to its own starting cell — not by the island's absolute grid position. The backtrack markers are essential: without them, two differently-shaped islands could still produce the same multiset of directional moves; encoding the full recursive call structure (including returns) makes the signature a true, unambiguous shape fingerprint.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two islands of the same shape but different positions produce identical DFS signature strings">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="30" width="30" height="30" fill="#3fb950"/>
    <rect x="50" y="30" width="30" height="30" fill="#3fb950"/>
    <rect x="200" y="90" width="30" height="30" fill="#79c0ff"/>
    <rect x="230" y="90" width="30" height="30" fill="#79c0ff"/>
    <text x="10" y="15" fill="#e6edf3">same 1x2 shape at different positions -- both DFS signatures = "R B" -- counted once</text>
  </g>
</svg>

Both islands have the identical shape (a horizontal domino), so their DFS signature strings match, even though they sit at different grid coordinates.

## 5. Runnable example

```java
// NumberOfDistinctIslands.java
import java.util.*;

public class NumberOfDistinctIslands {

    // Level 1 -- Brute force: collect each island's ABSOLUTE cell
    // coordinates, then for every pair of islands, try shifting one by
    // every possible offset to see if it matches the other. Correct,
    // but comparing every pair of islands with brute-force translation
    // checks is far more expensive than building a translation-
    // invariant signature directly during the flood fill.

    // KEY INSIGHT: DFS visiting neighbors in a FIXED order produces a
    // move sequence that is a direct, translation-invariant fingerprint
    // of the island's shape -- no separate comparison step needed, just
    // put each signature in a set.

    // Level 2 -- Optimal: DFS building a path signature per island,
    // dedupe via a Set.
    static int numDistinctIslands(int[][] grid) {
        boolean[][] visited = new boolean[grid.length][grid[0].length];
        Set<String> shapes = new HashSet<>();

        for (int r = 0; r < grid.length; r++) {
            for (int c = 0; c < grid[0].length; c++) {
                if (grid[r][c] == 1 && !visited[r][c]) {
                    StringBuilder signature = new StringBuilder();
                    dfs(grid, visited, r, c, signature);
                    shapes.add(signature.toString());
                }
            }
        }
        return shapes.size();
    }

    static void dfs(int[][] grid, boolean[][] visited, int r, int c, StringBuilder signature) {
        if (r < 0 || r >= grid.length || c < 0 || c >= grid[0].length) return;
        if (visited[r][c] || grid[r][c] == 0) return;
        visited[r][c] = true;

        signature.append('D');
        dfs(grid, visited, r + 1, c, signature);
        signature.append('U');
        dfs(grid, visited, r - 1, c, signature);
        signature.append('R');
        dfs(grid, visited, r, c + 1, signature);
        signature.append('L');
        dfs(grid, visited, r, c - 1, signature);
        signature.append('B');
    }

    // Level 3 -- Hardened: appending a direction character BEFORE each
    // recursive call and a backtrack marker AFTER, for every one of
    // the 4 calls (not just the ones that actually move somewhere),
    // ensures dead-end branches are recorded too, distinguishing
    // shapes that would otherwise collide.

    public static void main(String[] args) {
        System.out.println(numDistinctIslands(new int[][]{
            {1,1,0,0,0},{1,1,0,0,0},{0,0,0,1,1},{0,0,0,1,1}
        })); // 1
        System.out.println(numDistinctIslands(new int[][]{
            {1,1,0,1,1},{1,0,0,0,0},{0,0,0,0,1},{1,1,0,1,1}
        })); // 3
    }
}
```

**How to run:** `java NumberOfDistinctIslands.java`

## 6. Walkthrough

Trace the DFS signature for the top-left island (cells `{(0,0),(0,1),(1,0),(1,1)}`) starting at `(0,0)`:

| Call | Direction appended | Action |
|---|---|---|
| dfs(0,0) | — | mark visited |
| → dfs(1,0) | 'D' | mark visited, recurse further into (1,1) via 'R' from here |
| → dfs(-1,0) | 'U' | out of bounds, return immediately, no append |
| → dfs(0,1) | 'R' | mark visited, recurse into (1,1) via 'D' |
| → dfs(0,-1) | 'L' | out of bounds, return |
| back at (0,0) | 'B' | backtrack marker |

The full signature string uniquely encodes this 2×2 square shape; the second island in the example (also a 2×2 square) produces the identical string, so the set ends up with size `1`. Time complexity is O(rows × cols), since each cell contributes a constant number of signature characters; space is O(rows × cols) for the visited array and the signature strings.

## 7. Gotchas & takeaways

> Gotcha: omitting the backtrack marker (`'B'`) after each recursive call can make two genuinely different shapes produce the SAME signature string, since the sequence of "moves into cells" alone does not always capture the full branching structure of the traversal.

- The direction characters must be appended in a CONSISTENT order across all calls (always down, then up, then right, then left, or any fixed order) — an inconsistent order breaks translation-invariance.
- This signature technique generalizes to any "deduplicate shapes found by traversal" problem, not just grids — the core idea is: fixed traversal order + full call-structure encoding = shape fingerprint.
- Related problems: Number of Islands (count without deduplicating shape), Max Area of Island (measure size instead of shape).
