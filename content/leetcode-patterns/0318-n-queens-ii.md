---
card: leetcode-patterns
gi: 318
slug: n-queens-ii
title: N-Queens II
---

## 1. What it is

Given an integer `n`, return the NUMBER of distinct solutions to the `n`-queens puzzle (placing `n` queens on an `n x n` board so none attack each other), without needing to return the boards themselves. Example: `n = 4` → `2`.

## 2. Why & when

This is N-Queens with the output simplified to a count: identical search, but instead of building a board's string representation at each success, you simply increment a counter. Use this shape whenever a problem only needs to COUNT valid backtracking outcomes, not enumerate them — it means you can skip whatever work N-Queens spent on constructing and storing each result.

## 3. Core concept

**Key idea:** run the exact same row-by-row queen placement search as N-Queens, using the same column and diagonal tracking, but replace "build and record the board" with "increment a counter."

**Steps:**
1. Track `usedCols`, `usedDiag1` (`row - col`), `usedDiag2` (`row + col`), all as sets (or bitmasks for a faster version).
2. Define `backtrack(row)`. **Base case:** if `row == n`, increment `count`, and return — no board construction needed.
3. **Loop:** for `col` from `0` to `n - 1`: skip if `col`, `row - col`, or `row + col` is already used (prune).
4. Otherwise, mark all three (choose), recurse to `row + 1`, then unmark all three (un-choose).
5. Return `count` after the initial call finishes.

**Why it is correct:** the validity rules (one queen per row, no shared column or diagonal) are unchanged from N-Queens, so the SAME search explores the exact same set of valid full placements — the only difference is what happens at a successful base case. Since the problem only asks "how many," skipping the board-construction step is a safe simplification that saves work without affecting which placements are found valid.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Same backtracking search as N-Queens, but incrementing a counter instead of building a board string at each success">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">n = 4</text>
    <text x="10" y="45">search finds valid full placement #1 (row 4 reached) -&gt; count = 1</text>
    <text x="10" y="65">backtrack, search continues, finds valid full placement #2 -&gt; count = 2</text>
    <text x="10" y="85">search exhausts all branches, no more valid placements</text>
    <rect x="10" y="100" width="100" height="24" fill="#3fb950"/><text x="60" y="117" fill="#0d1117" text-anchor="middle" font-size="10">return 2</text>
  </g>
</svg>

The search tree is identical to N-Queens; only the action taken at a successful leaf changes.

## 5. Runnable example

```java
// NQueensII.java
import java.util.HashSet;
import java.util.Set;

public class NQueensII {

    static int count;

    // KEY INSIGHT: identical search to N-Queens, but the base case
    // increments a counter instead of constructing and storing a
    // board string -- saves work when only the count is needed.

    static int totalNQueens(int n) {
        count = 0;
        Set<Integer> usedCols = new HashSet<>();
        Set<Integer> usedDiag1 = new HashSet<>();
        Set<Integer> usedDiag2 = new HashSet<>();
        backtrack(0, n, usedCols, usedDiag1, usedDiag2);
        return count;
    }

    static void backtrack(int row, int n, Set<Integer> usedCols,
                           Set<Integer> usedDiag1, Set<Integer> usedDiag2) {
        if (row == n) {
            count++;
            return;
        }
        for (int col = 0; col < n; col++) {
            int d1 = row - col, d2 = row + col;
            if (usedCols.contains(col) || usedDiag1.contains(d1) || usedDiag2.contains(d2)) {
                continue;
            }
            usedCols.add(col); usedDiag1.add(d1); usedDiag2.add(d2);
            backtrack(row + 1, n, usedCols, usedDiag1, usedDiag2);
            usedCols.remove(col); usedDiag1.remove(d1); usedDiag2.remove(d2);
        }
    }

    public static void main(String[] args) {
        System.out.println(totalNQueens(4));
        // 2
        System.out.println(totalNQueens(8));
        // 92
    }
}
```

**How to run:** `java NQueensII.java`

## 6. Walkthrough

For `n = 4`, the search tree is identical to N-Queens' search tree: it explores the same partial placements, prunes the same conflicting columns and diagonals, and reaches exactly 2 full valid placements (`row == 4`). Each time `row == n` is reached, `count` increments once, ending at `count = 2`. Time complexity is O(n!) in the worst case, same as N-Queens, since the search space is identical. Space is O(n), for the sets and recursion depth — notably LESS than N-Queens' space at the RESULT level, since no boards are stored.

## 7. Gotchas & takeaways

> Gotcha: it is tempting to think counting is "easier" than enumerating, but the SEARCH cost is identical — the only savings versus N-Queens is skipping the O(n) board-construction step at each success, not any reduction in how many branches get explored.

- When a problem only asks for a COUNT, look for ways to strip out any per-result construction work from an otherwise-identical search — a common, easy optimization.
- The three-set (or bitmask) column/diagonal tracking technique from N-Queens transfers here completely unchanged.
- Related problems: N-Queens (returns the actual boards instead of just a count), Combination Sum III (also counts implicitly, but by structure rather than choosing to skip result-construction).
