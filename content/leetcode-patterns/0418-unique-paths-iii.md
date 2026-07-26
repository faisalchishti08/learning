---
card: leetcode-patterns
gi: 418
slug: unique-paths-iii
title: Unique Paths III
---

## 1. What it is

A grid has exactly one starting square (`1`), exactly one ending square (`2`), some empty squares (`0`), and some obstacles (`-1`). Count the number of distinct paths from start to end, moving up/down/left/right, that walk over EVERY non-obstacle square EXACTLY ONCE. Example: `grid = [[1,0,0,0],[0,0,0,0],[0,0,2,-1]]` → `2`.

## 2. Why & when

Use this shape whenever a grid problem requires visiting EVERY empty cell exactly once (a Hamiltonian-path-style constraint), not just reaching a destination. This "visit everything, exactly once" requirement rules out any `dp[r][c]` table approach — the answer depends on the FULL set of cells already visited, which cannot be summarized by position alone. BACKTRACKING with an explicit visited count is the correct, and really the only practical, tool.

## 3. Core concept

**Key idea:** count how many empty (or start/end) squares must be visited (`target`). Then DFS from the start, marking cells visited, and counting a successful path only when the walk reaches the end cell HAVING VISITED EXACTLY `target` squares.

**Steps:**
1. Scan the grid once: locate the start cell, and count `target` = the total number of non-obstacle squares (all `0`s, plus the start `1`, plus the end `2`).
2. DFS from the start cell, tracking how many squares have been visited so far (`steps`), and temporarily marking each visited cell (e.g. by changing it to `-1`) so it cannot be revisited.
3. If the DFS reaches the end cell (`2`): count it as ONE valid path if and only if `steps` equals `target` (every non-obstacle cell was visited); otherwise this branch does not count, even though it reached the end.
4. After trying all four directions from a cell, UN-MARK it (restore its original value) so other branches of the search can still use it.

**Why backtracking is required, not a `dp[r][c]` table:** two different paths can both be AT `(r, c)` having visited totally different subsets of the grid so far — one might have covered the left half, another the right half — and only one of those subsets might still allow reaching every remaining cell. Since the "remaining reachability" depends on exactly WHICH cells are already used, not just the current position, no simple `dp[r][c]` summarizes it; the algorithm must explore the actual path, backtracking when a branch fails.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dfs marking cells visited as it walks, only counting a path when it reaches the end having visited exactly the target number of cells">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">grid = [[1,0,0,0],[0,0,0,0],[0,0,2,-1]]; target = 11 non-obstacle cells</text>
    <text x="10" y="45">DFS walks, marking each cell visited; reaching '2' with steps == 11 counts</text>
    <rect x="10" y="65" width="300" height="24" fill="#3fb950"/><text x="160" y="82" fill="#0d1117" text-anchor="middle" font-size="10">reaching the end EARLY (steps &lt; target) does NOT count</text>
  </g>
</svg>

A path only counts when it reaches the end cell after visiting every single non-obstacle square.

## 5. Runnable example

```java
// UniquePathsIII.java
public class UniquePathsIII {

    static int[][] dirs = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};
    static int count = 0;

    // KEY INSIGHT: the answer depends on the FULL set of cells already
    // visited, not just the current position -- backtracking with an
    // explicit "steps visited" count is required, not a dp[r][c] table.
    static int uniquePathsIII(int[][] grid) {
        int rows = grid.length, cols = grid[0].length;
        int startR = -1, startC = -1, target = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (grid[r][c] == 1) { startR = r; startC = c; target++; }
                else if (grid[r][c] != -1) { target++; }
            }
        }
        count = 0;
        dfs(grid, startR, startC, 1, target);
        return count;
    }

    static void dfs(int[][] grid, int r, int c, int steps, int target) {
        int rows = grid.length, cols = grid[0].length;
        if (r < 0 || r >= rows || c < 0 || c >= cols || grid[r][c] == -1) return;

        if (grid[r][c] == 2) {
            if (steps == target) count++;
            return;
        }

        int original = grid[r][c];
        grid[r][c] = -1; // mark visited
        for (int[] d : dirs) {
            dfs(grid, r + d[0], c + d[1], steps + 1, target);
        }
        grid[r][c] = original; // backtrack
    }

    public static void main(String[] args) {
        int[][] grid = {{1, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 2, -1}};
        System.out.println(uniquePathsIII(grid));
        // 2
    }
}
```

**How to run:** `java UniquePathsIII.java`

## 6. Walkthrough

Trace the setup and one successful branch:

| step | action | note |
|---|---|---|
| scan | find start (0,0); count target | 11 non-obstacle cells total |
| dfs(0,0,steps=1) | mark (0,0) visited | try 4 directions |
| ... | walk covers every remaining `0` cell | steps increments each move |
| dfs(2,2,steps=11) | grid[2][2] == 2 (end) | steps == target(11): count++ |

Two distinct orderings of covering every cell before reaching `(2,2)` both succeed, giving `count = 2`, matching the expected answer. Time complexity is O(4^k) in the worst case, where `k` is the number of empty cells (genuine path enumeration, not polynomial DP) — acceptable since the problem caps the grid at a small size specifically because this is a backtracking problem. Space is O(k) for the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: reaching the end cell is NOT automatically a valid path — a branch that reaches `(end)` too early (having skipped some empty cells) must be REJECTED, which is why the `steps == target` check, not just "did we reach the end," decides whether to count a path.

- Backtracking (mark, recurse in all directions, un-mark) is required here for the same reason as Path with Maximum Gold: the answer depends on the full path history, which a position-only `dp[r][c]` cannot capture.
- Counting `target` up front (every non-obstacle cell) turns "visit everything" into a simple equality check (`steps == target`) at the moment the end is reached, instead of a more complex bookkeeping structure.
- Related problems: Path with Maximum Gold (the same backtracking shape, optimizing a sum instead of counting exact-coverage paths), Longest Increasing Path in a Matrix (also explores four directions, but a strict value ordering makes memoized DP safe there, unlike here).
