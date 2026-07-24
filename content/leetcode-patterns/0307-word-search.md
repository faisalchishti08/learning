---
card: leetcode-patterns
gi: 307
slug: word-search
title: Word Search
---

## 1. What it is

Given an `m x n` grid of characters `board` and a string `word`, return `true` if `word` can be formed by a path of adjacent cells (up, down, left, right), using each cell AT MOST ONCE. Example: `board = [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]]`, `word = "ABCCED"` → `true`.

## 2. Why & when

This is a grid-path backtracking problem: at each step, choose a direction to move, recurse to try matching the next character, and un-choose (unmark the cell as visited) if that direction fails. Use this shape whenever a problem asks whether a path exists in a grid that satisfies a sequence of conditions, using each cell no more than once.

## 3. Core concept

**Key idea:** try starting the search from every cell that matches `word`'s first character. From each starting cell, recursively try all 4 directions, matching one character of `word` at a time, marking cells as visited so the same cell is never reused within one path.

**Steps:**
1. For every cell `(row, col)` in `board`, if `board[row][col] == word[0]`, start a depth-first search from there.
2. In the search, if the current index equals `word.length()`, the whole word has matched — return `true`.
3. If the current cell is out of bounds, already visited, or does not match `word[index]`, return `false` (prune this branch).
4. Otherwise, temporarily mark the cell visited (a common trick: overwrite it with a sentinel character), recurse into all 4 neighbors for `index + 1`, then UN-MARK the cell (restore its original character) before returning.
5. Return `true` as soon as any starting cell's search succeeds.

**Why it is correct:** marking a cell visited before recursing, and un-marking it right after, ensures no single path reuses a cell, while still allowing DIFFERENT paths (explored later, from other starting points or other directions) to freely use that same cell again. The prune check (`out of bounds`, `visited`, `mismatch`) stops the search immediately on any wrong turn, instead of exploring further characters that could never match.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Grid search matching ABCCED by moving right, right, down, down, left, up and marking visited cells along the path">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">word = "ABCCED"</text>
    <text x="10" y="45">start at (0,0)='A' -&gt; matches word[0]</text>
    <text x="10" y="65">move right to (0,1)='B' -&gt; matches word[1]</text>
    <text x="10" y="85">move right to (0,2)='C' -&gt; matches word[2]</text>
    <text x="10" y="105">move down to (1,2)='C' -&gt; matches word[3]</text>
    <text x="10" y="125">move down to (2,2)='E' -&gt; matches word[4]</text>
    <text x="10" y="145">move left to (2,1)='D' -&gt; matches word[5], index=6=word.length</text>
    <rect x="10" y="155" width="80" height="24" fill="#3fb950"/><text x="50" y="172" fill="#0d1117" text-anchor="middle" font-size="10">true</text>
  </g>
</svg>

Each successful match advances the path by one cell; a mismatch or revisit prunes that direction immediately.

## 5. Runnable example

```java
// WordSearch.java
public class WordSearch {

    // KEY INSIGHT: temporarily overwrite a visited cell with a
    // sentinel character to mark it "in use" for the current path,
    // then restore it after backtracking -- this avoids needing a
    // separate boolean visited grid.

    static boolean exist(char[][] board, String word) {
        int rows = board.length, cols = board[0].length;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (search(board, word, r, c, 0)) return true;
            }
        }
        return false;
    }

    static boolean search(char[][] board, String word, int r, int c, int index) {
        if (index == word.length()) return true; // full word matched

        if (r < 0 || r >= board.length || c < 0 || c >= board[0].length
                || board[r][c] != word.charAt(index)) {
            return false; // prune: out of bounds or mismatch
        }

        char original = board[r][c];
        board[r][c] = '#'; // choose: mark visited

        boolean found = search(board, word, r + 1, c, index + 1)
                || search(board, word, r - 1, c, index + 1)
                || search(board, word, r, c + 1, index + 1)
                || search(board, word, r, c - 1, index + 1);

        board[r][c] = original; // un-choose: restore
        return found;
    }

    public static void main(String[] args) {
        char[][] board = {
            {'A', 'B', 'C', 'E'},
            {'S', 'F', 'C', 'S'},
            {'A', 'D', 'E', 'E'}
        };
        System.out.println(exist(board, "ABCCED"));
        // true
        System.out.println(exist(board, "SEE"));
        // true
        System.out.println(exist(board, "ABCB"));
        // false (reusing the same 'B' cell is not allowed)
    }
}
```

**How to run:** `java WordSearch.java`

## 6. Walkthrough

Trace `exist(board, "ABCCED")` starting at `(0,0)`:

| step | cell | word[index] | match? | action |
|---|---|---|---|---|
| 1 | (0,0)='A' | 'A' (index 0) | yes | mark visited, recurse index=1 |
| 2 | (0,1)='B' | 'B' (index 1) | yes | mark visited, recurse index=2 |
| 3 | (0,2)='C' | 'C' (index 2) | yes | mark visited, recurse index=3 |
| 4 | (1,2)='C' | 'C' (index 3) | yes | mark visited, recurse index=4 |
| 5 | (2,2)='E' | 'E' (index 4) | yes | mark visited, recurse index=5 |
| 6 | (2,1)='D' | 'D' (index 5) | yes | index becomes 6 = word.length(), return true |

Every cell is un-marked as the recursion unwinds back up. Time complexity is O(rows · cols · 4^L), where `L` is `word.length()`: one search attempt per starting cell, each exploring up to 4 directions per character. Space is O(L), for the recursion stack depth.

## 7. Gotchas & takeaways

> Gotcha: restoring `board[r][c] = original` must happen AFTER all 4 recursive calls, not before — restoring it too early would let a LATER direction from the SAME cell revisit it, breaking the "each cell used at most once per path" rule.

- Overwriting the board in place (instead of a separate visited array) saves memory but requires careful restoration — always restore immediately before returning from that recursive call, not conditionally.
- The `||` short-circuit across all 4 directions means recursion stops trying further directions the moment one succeeds — no wasted work after a match is found.
- Related problems: Number of Islands (a similar grid DFS, but marking permanently instead of restoring), Restore IP Addresses (a different kind of build-and-prune backtracking, over string positions instead of grid cells).
