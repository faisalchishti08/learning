---
card: leetcode-patterns
gi: 185
slug: surrounded-regions
title: Surrounded Regions
---

## 1. What it is

Given an `m x n` grid of `'X'` and `'O'`, capture every region of `'O'`s that is fully SURROUNDED by `'X'`s (does not touch the border), by flipping those `'O'`s to `'X'`. Regions of `'O'` that touch the grid border are safe and stay `'O'`. Example: `board = [["X","X","X","X"],["X","O","O","X"],["X","X","O","X"],["X","O","X","X"]]` → `[["X","X","X","X"],["X","X","X","X"],["X","X","X","X"],["X","O","X","X"]]`.

## 2. Why & when

This is a "flip the logic" flood fill: instead of finding regions to flip DIRECTLY, it is far easier to find the regions that must NOT be flipped (any `'O'` region touching the border) and flood fill from there, marking them safe. Everything left over gets flipped.

## 3. Core concept

**Key idea:** any `'O'` connected to a border `'O'` is safe, because that connection means the whole region touches the border transitively. Flood fill from every border `'O'` first, marking all reachable `'O'`s as safe (e.g. temporarily change them to `'#'`). Then a single pass flips every remaining `'O'` (which must be fully surrounded) to `'X'`, and restores every `'#'` back to `'O'`.

**Steps:**
1. Flood fill from every `'O'` on the grid's border (all four edges), marking each reachable `'O'` with a temporary marker like `'#'`.
2. Scan the whole grid: any `'O'` still remaining (not marked `'#'`) was never reachable from a border `'O'`, so it is fully surrounded — flip it to `'X'`.
3. In the same final scan, convert every `'#'` back to `'O'`, restoring the safe regions.

**Why it is correct:** an `'O'` region is safe from capture if and only if it touches the border, either directly or through a connected chain of other `'O'`s that eventually reaches the border. Flood fill from EVERY border `'O'` correctly marks every such connected region as safe in one pass; any `'O'` left unmarked, by definition, has no path to the border and must be captured.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Border-connected O region marked safe; fully enclosed O region gets flipped">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="20" width="200" height="140" fill="none" stroke="#30363d"/>
    <rect x="20" y="90" width="30" height="30" fill="#79c0ff"/>
    <text x="60" y="110" fill="#e6edf3">border O -&gt; safe (stays O)</text>
    <rect x="120" y="90" width="30" height="30" fill="#f85149"/>
    <text x="160" y="140" fill="#e6edf3">enclosed O -&gt; flipped to X</text>
    <text x="10" y="15" fill="#e6edf3">flood fill from border O's first; anything unreached gets captured</text>
  </g>
</svg>

The blue border-touching `O` region is marked safe by flood fill; the red fully-enclosed region, never reached, gets flipped to `X`.

## 5. Runnable example

```java
// SurroundedRegions.java
public class SurroundedRegions {

    // Level 1 -- Brute force: for every interior 'O', run a full
    // flood fill checking whether it ever touches the border, undoing
    // or discarding the search if it does. Correct, but repeats work
    // for every 'O' in the same region, checking border-reachability
    // over and over instead of computing it once per region.

    // KEY INSIGHT: flip the search direction -- flood fill FROM the
    // border INWARD (once per border cell, naturally skipping already
    // marked cells) instead of from each interior cell OUTWARD toward
    // the border.

    // Level 2 -- Optimal: mark border-connected 'O's safe, flip the
    // rest.
    static void solve(char[][] board) {
        int rows = board.length, cols = board[0].length;
        for (int c = 0; c < cols; c++) {
            markSafe(board, 0, c);
            markSafe(board, rows - 1, c);
        }
        for (int r = 0; r < rows; r++) {
            markSafe(board, r, 0);
            markSafe(board, r, cols - 1);
        }

        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (board[r][c] == 'O') board[r][c] = 'X';
                else if (board[r][c] == '#') board[r][c] = 'O';
            }
        }
    }

    static void markSafe(char[][] board, int r, int c) {
        if (r < 0 || r >= board.length || c < 0 || c >= board[0].length) return;
        if (board[r][c] != 'O') return;
        board[r][c] = '#';
        markSafe(board, r + 1, c);
        markSafe(board, r - 1, c);
        markSafe(board, r, c + 1);
        markSafe(board, r, c - 1);
    }

    // Level 3 -- Hardened: a board where every 'O' touches the border
    // correctly leaves the board unchanged, since markSafe visits and
    // restores all of them; a board with no 'O' at all is a no-op.

    public static void main(String[] args) {
        char[][] board = {
            {'X','X','X','X'},
            {'X','O','O','X'},
            {'X','X','O','X'},
            {'X','O','X','X'}
        };
        solve(board);
        for (char[] row : board) System.out.println(new String(row));
        // XXXX
        // XXXX
        // XXXX
        // XOXX
    }
}
```

**How to run:** `java SurroundedRegions.java`

## 6. Walkthrough

Trace the example board: border-scan calls `markSafe` on `(3,1)` (bottom-row `'O'`), which flood fills — but `(3,1)` has no connected `'O'` neighbors within the interior region (the `(1,1)-(1,2)-(2,2)` group is not connected to it), so only `(3,1)` becomes `'#'`.

| Step | Region | Touches border? | Result |
|---|---|---|---|
| `{(1,1),(1,2),(2,2)}` | interior blob | no | flipped to `'X'` |
| `{(3,1)}` | bottom-row cell | yes (itself on border) | marked `'#'`, restored to `'O'` |

Final scan flips the remaining `'O'`s (the interior blob) to `'X'` and restores the `'#'` back to `'O'`. Time complexity is O(rows × cols), since each cell is visited a bounded number of times across border flood fills and the final scan; space is O(rows × cols) worst case for recursion depth.

## 7. Gotchas & takeaways

> Gotcha: running flood fill from interior `'O'`s FIRST (in the final scan, before border cells are marked safe) instead of border cells first would incorrectly flip border-connected regions, since the algorithm depends on doing the border pass completely before the flip pass.

- The temporary marker (`'#'`) is essential — it distinguishes "safe, confirmed border-connected" from "still `'O'`, not yet proven safe," which a plain `visited` boolean array could also do, but mutating in place saves memory.
- Do all 4 border edges (top row, bottom row, left column, right column) — missing one edge silently treats it as if that edge were water, misclassifying regions that only touch that one side.
- Related problems: Number of Enclaves (same "reachable from border" flip-the-logic idea, counting instead of mutating), Number of Closed Islands (same idea again, applied to land regions instead of `'O'` regions).
