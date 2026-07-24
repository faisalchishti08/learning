---
card: leetcode-patterns
gi: 317
slug: n-queens
title: N-Queens
---

## 1. What it is

The `n`-queens puzzle places `n` chess queens on an `n x n` board so that no two queens attack each other (no shared row, column, or diagonal). Given `n`, return ALL distinct board arrangements, each represented as a list of strings, where `'Q'` marks a queen and `'.'` marks an empty cell. Example: `n = 4` → 2 solutions.

## 2. Why & when

This is the archetypal placement backtracking problem: place one queen per row, checking column and diagonal conflicts against ALL previously placed queens before committing. Use this shape whenever a problem places items one at a time onto a grid or sequence, where each new placement must be validated against everything placed so far.

## 3. Core concept

**Key idea:** place exactly one queen per row, working row by row. For each row, try every column; a column is valid only if no earlier queen shares that column or either diagonal.

**Steps:**
1. Track `columns[row]`, the column index of the queen placed in each row (or use 3 boolean sets: used columns, used "row - col" diagonals, used "row + col" diagonals, for O(1) conflict checks).
2. Define `backtrack(row)`. **Base case:** if `row == n`, a full valid placement was found — convert `columns[]` into the board's string format and record it.
3. **Loop:** for `col` from `0` to `n - 1`: skip if `col` is already used, or `row - col` matches an already-used "/" diagonal, or `row + col` matches an already-used "\" diagonal (prune).
4. Otherwise, mark `col`, `row - col`, and `row + col` as used (choose), recurse to `row + 1`, then unmark all three (un-choose).

**Why it is correct:** two queens conflict if they share a row (avoided automatically, since only one queen is placed per row), a column (`col` equal), or a diagonal — and every cell on the same "/" diagonal shares the same value of `row - col`, while every cell on the same "\" diagonal shares the same value of `row + col`. Tracking these 3 sets turns an O(n) conflict check against every previous queen into an O(1) lookup, without changing correctness at all.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Placing 4 queens row by row on a 4x4 board, using column and diagonal tracking to skip conflicting positions">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">n = 4, one valid solution</text>
    <text x="10" y="45">row 0: place at col 1 -&gt; .Q..</text>
    <text x="10" y="65">row 1: col 0,1 blocked (col/diag) -&gt; place at col 3 -&gt; ...Q</text>
    <text x="10" y="85">row 2: place at col 0 -&gt; Q...</text>
    <text x="10" y="105">row 3: place at col 2 -&gt; ..Q.</text>
    <rect x="10" y="120" width="150" height="24" fill="#3fb950"/><text x="85" y="137" fill="#0d1117" text-anchor="middle" font-size="10">[.Q.., ...Q, Q..., ..Q.]</text>
  </g>
</svg>

Each row's queen must avoid every column and diagonal already claimed by queens in earlier rows.

## 5. Runnable example

```java
// NQueens.java
import java.util.*;

public class NQueens {

    // KEY INSIGHT: tracking used columns and both diagonal families
    // (row-col and row+col) as sets turns an O(row) conflict check
    // against every earlier queen into an O(1) lookup per candidate.

    static List<List<String>> solveNQueens(int n) {
        List<List<String>> results = new ArrayList<>();
        int[] columns = new int[n];
        Set<Integer> usedCols = new HashSet<>();
        Set<Integer> usedDiag1 = new HashSet<>(); // row - col
        Set<Integer> usedDiag2 = new HashSet<>(); // row + col

        backtrack(0, n, columns, usedCols, usedDiag1, usedDiag2, results);
        return results;
    }

    static void backtrack(int row, int n, int[] columns, Set<Integer> usedCols,
                           Set<Integer> usedDiag1, Set<Integer> usedDiag2,
                           List<List<String>> results) {
        if (row == n) {
            results.add(buildBoard(columns, n));
            return;
        }

        for (int col = 0; col < n; col++) {
            int d1 = row - col, d2 = row + col;
            if (usedCols.contains(col) || usedDiag1.contains(d1) || usedDiag2.contains(d2)) {
                continue; // prune: conflict
            }

            columns[row] = col;
            usedCols.add(col); usedDiag1.add(d1); usedDiag2.add(d2); // choose
            backtrack(row + 1, n, columns, usedCols, usedDiag1, usedDiag2, results); // recurse
            usedCols.remove(col); usedDiag1.remove(d1); usedDiag2.remove(d2); // un-choose
        }
    }

    static List<String> buildBoard(int[] columns, int n) {
        List<String> board = new ArrayList<>();
        for (int col : columns) {
            char[] row = new char[n];
            Arrays.fill(row, '.');
            row[col] = 'Q';
            board.add(new String(row));
        }
        return board;
    }

    public static void main(String[] args) {
        List<List<String>> solutions = solveNQueens(4);
        System.out.println("solutions: " + solutions.size());
        for (String row : solutions.get(0)) System.out.println(row);
    }
}
```

**How to run:** `java NQueens.java`

## 6. Walkthrough

Trace the start of `solveNQueens(4)`:

| row | tried col | usedCols | usedDiag1 (row-col) | usedDiag2 (row+col) | outcome |
|---|---|---|---|---|---|
| 0 | 0 | {} | {} | {} | place col=0 |
| 1 | 0 | {0} | {0} | {0} | conflict (col 0 used), try col=1: d1=0 (used!), conflict; try col=2: d1=-1, d2=3, ok |
| 2 | ... | {0,2} | {0,-1} | {0,3} | continues checking each column against all 3 sets |

Eventually this branch (starting `col=0` at row 0) fails to complete for `n=4`, and the search backtracks all the way to row 0 to try `col=1`, which succeeds. Time complexity is O(n!) in the worst case (roughly `n` choices at row 0, `n-1` at row 1, and so on), heavily pruned in practice by the O(1) conflict checks. Space is O(n), for the sets and recursion depth.

## 7. Gotchas & takeaways

> Gotcha: forgetting to remove ALL THREE tracked values (`col`, `d1`, `d2`) during un-choose — removing only `col` but leaving a stale diagonal entry — causes valid later placements to be incorrectly rejected as conflicting with a queen that no longer exists on the board.

- Reducing the search to "one queen per row" eliminates the row-conflict check ENTIRELY, cutting the problem down to just column and diagonal checks.
- The `row - col` / `row + col` trick for identifying diagonals is a general grid technique, reusable in any problem involving diagonal relationships on a 2D board.
- Related problems: N-Queens II (the same search, but counting solutions instead of returning them), Sudoku Solver (placement backtracking on a grid with a different, more complex conflict rule).
