---
card: leetcode-patterns
gi: 319
slug: sudoku-solver
title: Sudoku Solver
---

## 1. What it is

Given a partially filled `9x9` Sudoku board, fill in the empty cells (marked `'.'`) so the board satisfies Sudoku's rules: each row, each column, and each of the nine `3x3` sub-boxes contains the digits `1`–`9` with no repeats. The board is guaranteed to have exactly one solution; modify it in place. Example: a standard partially-filled Sudoku puzzle → its unique completed solution.

## 2. Why & when

This is grid placement backtracking with THREE simultaneous conflict rules (row, column, and 3x3 box), instead of N-Queens' two (column, diagonal). Use this shape whenever a problem fills a grid under MULTIPLE overlapping uniqueness constraints, all of which must hold at once.

## 3. Core concept

**Key idea:** scan for the next empty cell; try digits `1`–`9` in it, checking all three rules; recurse; if every remaining cell eventually fills successfully, the whole board is solved — return `true` all the way up. If no digit works, backtrack.

**Steps:**
1. Track `usedInRow[9][10]`, `usedInCol[9][10]`, `usedInBox[9][10]` (boolean arrays, sized for digits `1`–`9`), pre-filled from the board's initial given digits. The box index for cell `(r, c)` is `(r / 3) * 3 + (c / 3)`.
2. Define `solve()`: find the first empty cell `(r, c)`, scanning row by row. If none remain, the board is fully and validly filled — return `true`.
3. **Loop:** for `digit` from `1` to `9`: skip if `usedInRow[r][digit]`, `usedInCol[c][digit]`, or `usedInBox[box][digit]` is true (prune).
4. Otherwise, place `digit` on the board and mark all three tracking arrays (choose); recurse; if the recursive call returns `true`, propagate `true` immediately. Otherwise, remove `digit` and unmark all three (un-choose).
5. If no digit works for this cell, return `false` (this whole branch fails, forcing the caller to try a different earlier digit).

**Why it is correct:** the three tracking structures directly encode Sudoku's three rules, so a digit is only ever placed where it violates none of them — every complete board found this way is automatically a valid solution. Because the problem guarantees exactly one solution, the moment `solve()` succeeds all the way through, that success propagates back up through every recursive call (`return true` immediately, no further alternatives explored), stopping the search precisely at the correct board.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Filling an empty cell by checking row, column, and 3x3 box tracking arrays before placing a digit">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">empty cell at (0,2), box index = (0/3)*3+(2/3) = 0</text>
    <text x="10" y="45">try digit 1: usedInRow[0][1]=false, usedInCol[2][1]=false, usedInBox[0][1]=false -&gt; place</text>
    <text x="10" y="65">mark usedInRow[0][1]=true, usedInCol[2][1]=true, usedInBox[0][1]=true</text>
    <text x="10" y="85">recurse to next empty cell...</text>
    <rect x="10" y="100" width="180" height="24" fill="#3fb950"/><text x="100" y="117" fill="#0d1117" text-anchor="middle" font-size="10">continues until board is full</text>
  </g>
</svg>

Each placement is checked against all three overlapping rule sets before the search commits to it.

## 5. Runnable example

```java
// SudokuSolver.java
public class SudokuSolver {

    static boolean[][] usedInRow = new boolean[9][10];
    static boolean[][] usedInCol = new boolean[9][10];
    static boolean[][] usedInBox = new boolean[9][10];
    static char[][] board;

    // KEY INSIGHT: tracking row/col/box usage in boolean arrays turns
    // an O(9) scan-the-row-column-box conflict check into an O(1)
    // lookup per candidate digit.

    static void solveSudoku(char[][] inputBoard) {
        board = inputBoard;
        for (int r = 0; r < 9; r++) {
            for (int c = 0; c < 9; c++) {
                if (board[r][c] != '.') {
                    int digit = board[r][c] - '0';
                    mark(r, c, digit, true);
                }
            }
        }
        solve();
    }

    static boolean solve() {
        for (int r = 0; r < 9; r++) {
            for (int c = 0; c < 9; c++) {
                if (board[r][c] != '.') continue;

                for (int digit = 1; digit <= 9; digit++) {
                    int box = (r / 3) * 3 + (c / 3);
                    if (usedInRow[r][digit] || usedInCol[c][digit] || usedInBox[box][digit]) {
                        continue; // prune
                    }

                    board[r][c] = (char) ('0' + digit);
                    mark(r, c, digit, true);                 // choose

                    if (solve()) return true;                // recurse

                    board[r][c] = '.';
                    mark(r, c, digit, false);                // un-choose
                }
                return false; // no digit worked for this cell
            }
        }
        return true; // no empty cells left, board solved
    }

    static void mark(int r, int c, int digit, boolean used) {
        usedInRow[r][digit] = used;
        usedInCol[c][digit] = used;
        usedInBox[(r / 3) * 3 + (c / 3)][digit] = used;
    }

    public static void main(String[] args) {
        char[][] board = {
            {'5','3','.','.','7','.','.','.','.'},
            {'6','.','.','1','9','5','.','.','.'},
            {'.','9','8','.','.','.','.','6','.'},
            {'8','.','.','.','6','.','.','.','3'},
            {'4','.','.','8','.','3','.','.','1'},
            {'7','.','.','.','2','.','.','.','6'},
            {'.','6','.','.','.','.','2','8','.'},
            {'.','.','.','4','1','9','.','.','5'},
            {'.','.','.','.','8','.','.','7','9'}
        };
        solveSudoku(board);
        for (char[] row : board) System.out.println(new String(row));
    }
}
```

**How to run:** `java SudokuSolver.java`

## 6. Walkthrough

Trace the FIRST placement attempt at `(0, 2)`, the board's first empty cell:

| digit | usedInRow[0][d] | usedInCol[2][d] | usedInBox[0][d] | placed? |
|---|---|---|---|---|
| 1 | false | false | false | yes -&gt; board[0][2]='1', recurse |
| (if that branch eventually fails) | — | — | — | un-choose, try digit 2 next |

Because the board has a unique solution, the first fully successful chain of choices propagates `true` back through every recursive call, and the search stops immediately without exploring further alternatives. Time complexity is, in the worst case, exponential in the number of empty cells (roughly O(9^m) for `m` empty cells before pruning), but the O(1) conflict checks and immediate `return true` on success make it fast in practice for real puzzles. Space is O(1) extra beyond the fixed-size tracking arrays (81 cells, 9 rows/cols/boxes), plus O(m) recursion depth.

## 7. Gotchas & takeaways

> Gotcha: returning `false` from inside the `digit` loop (after trying all 9 digits) must happen INSIDE that same cell's iteration, immediately via a `return false` right after the loop — placing this check at the wrong nesting level would either skip cells incorrectly or fail to propagate a dead end back up to the caller.

- Precomputing `usedInRow`, `usedInCol`, `usedInBox` from the GIVEN digits before starting the search is essential — skipping this step would let the solver place a digit that conflicts with an already-fixed clue.
- The immediate `return true` propagation the instant a full solution is found is what keeps the search from wastefully exploring alternate solutions when the problem guarantees only one exists.
- Related problems: N-Queens (a simpler 2-constraint placement backtracking problem), Word Search (grid backtracking with a path constraint instead of a uniqueness constraint).
