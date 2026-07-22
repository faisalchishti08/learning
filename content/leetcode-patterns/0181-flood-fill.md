---
card: leetcode-patterns
gi: 181
slug: flood-fill
title: Flood Fill
---

## 1. What it is

Given an `image` (2D grid of integers), a starting pixel `(sr, sc)`, and a `color`, change the starting pixel's color to `color`, and repeat for every pixel connected to it 4-directionally that shares the STARTING pixel's original color. Return the modified image. Example: `image = [[1,1,1],[1,1,0],[1,0,1]]`, `sr=1, sc=1, color=2` → `[[2,2,2],[2,2,0],[2,0,1]]`.

## 2. Why & when

This is the canonical, literal flood fill: exactly the paint-bucket tool in an image editor. It is the direct template application — no extra reasoning needed beyond "start here, spread to same-colored neighbors, recolor as you go."

## 3. Core concept

**Key idea:** DFS (or BFS) from `(sr, sc)`, only spreading into neighbors that still have the ORIGINAL starting color, recoloring each one as it is visited so it is never revisited and never mistaken for a still-unprocessed original-colored pixel.

**Steps:**
1. Record `startColor = image[sr][sc]`. If `startColor == color` already, return the image unchanged (recoloring would cause infinite recursion, since every already-matching neighbor would look "still needing a fill").
2. DFS from `(sr, sc)`: if out of bounds, or `image[r][c] != startColor`, return.
3. Otherwise, set `image[r][c] = color`, then recurse into all 4 neighbors.
4. Return the modified image once the DFS completes.

**Why it is correct:** DFS visits exactly the maximal connected region of pixels matching `startColor`, reachable via 4-directional steps from `(sr, sc)`, because it only recurses into cells that still equal `startColor` — recoloring immediately prevents any cell from being processed twice or mistaken for unvisited after its own recoloring.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DFS recolors the connected region matching the start pixel's original color">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="30" width="40" height="40" fill="#3fb950"/>
    <rect x="60" y="30" width="40" height="40" fill="#3fb950"/>
    <rect x="60" y="70" width="40" height="40" fill="#3fb950"/>
    <rect x="100" y="70" width="40" height="40" fill="#161b22" stroke="#30363d"/>
    <text x="10" y="15" fill="#e6edf3">DFS from the start pixel spreads into same-colored neighbors (green), recoloring each as visited</text>
  </g>
</svg>

DFS recolors every pixel of the connected region sharing the start pixel's original color, stopping at differently-colored or out-of-bounds cells.

## 5. Runnable example

```java
// FloodFill.java
public class FloodFill {

    // Level 1 -- Brute force: repeatedly scan the whole image, each
    // pass recoloring any original-colored pixel adjacent to an
    // already-recolored one, stopping when a full pass makes no
    // change. Correct, but re-scans the entire grid on every pass
    // instead of following the region's actual boundary directly.

    // KEY INSIGHT: DFS follows only the ACTUAL connected region, one
    // recursive call per pixel in it, instead of repeatedly re-checking
    // the whole grid to see whether anything new became reachable.

    // Level 2 -- Optimal: DFS with immediate recoloring.
    static int[][] floodFill(int[][] image, int sr, int sc, int color) {
        int startColor = image[sr][sc];
        if (startColor != color) dfs(image, sr, sc, startColor, color);
        return image;
    }

    static void dfs(int[][] image, int r, int c, int startColor, int color) {
        if (r < 0 || r >= image.length || c < 0 || c >= image[0].length) return;
        if (image[r][c] != startColor) return;
        image[r][c] = color;
        dfs(image, r + 1, c, startColor, color);
        dfs(image, r - 1, c, startColor, color);
        dfs(image, r, c + 1, startColor, color);
        dfs(image, r, c - 1, startColor, color);
    }

    // Level 3 -- Hardened: the `startColor != color` guard at the top
    // prevents infinite recursion when the fill color equals the
    // starting color, which would otherwise make every already-filled
    // neighbor look like it still needs filling.

    public static void main(String[] args) {
        int[][] image = {{1,1,1},{1,1,0},{1,0,1}};
        int[][] result = floodFill(image, 1, 1, 2);
        for (int[] row : result) System.out.println(java.util.Arrays.toString(row));
        // [2, 2, 2]
        // [2, 2, 0]
        // [2, 0, 1]
    }
}
```

**How to run:** `java FloodFill.java`

## 6. Walkthrough

Trace `sr=1, sc=1, color=2` on `[[1,1,1],[1,1,0],[1,0,1]]`, `startColor = 1`:

| Call | Cell | image[r][c] before | Action |
|---|---|---|---|
| dfs(1,1) | (1,1) | 1 | recolor to 2, recurse 4 ways |
| dfs(2,1) | (2,1) | 0 | ≠ startColor, return |
| dfs(0,1) | (0,1) | 1 | recolor to 2, recurse |
| dfs(0,0) | (0,0) | 1 | recolor to 2, recurse (further calls hit bounds/mismatches) |
| dfs(0,2) | (0,2) | 1 | recolor to 2 |
| dfs(1,2) | (1,2) | 0 | ≠ startColor, return |
| dfs(1,0) | (1,0) | 1 | recolor to 2 |

Final image has every originally-`1`-connected-to-(1,1) pixel recolored to `2`; the isolated `1` at `(2,2)` stays untouched since it is not 4-connected to the start. Time complexity is O(rows × cols), since each cell is visited a bounded number of times; space is O(rows × cols) for the worst-case recursion depth.

## 7. Gotchas & takeaways

> Gotcha: skipping the `startColor != color` check causes infinite recursion when `color` equals the original color — every neighbor, even after being "recolored" to the same value, still matches `startColor`, so DFS never terminates.

- Recolor in place (no separate visited array needed) — the color change itself marks a cell as processed.
- 4-directional connectivity is standard for this problem; confirm from the prompt if diagonals also count.
- Related problems: Number of Islands (count regions instead of recoloring one), Max Area of Island (measure region size instead of recoloring).
