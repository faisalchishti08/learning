---
card: leetcode-patterns
gi: 417
slug: dungeon-game
title: Dungeon Game
---

## 1. What it is

A knight must rescue a princess in the bottom-right corner of a dungeon grid, starting at the top-left, moving only right or down. Each cell adds to or subtracts from the knight's health (negative values are demons, positive values are potions). The knight's health must stay ABOVE `0` at every point along the path. Find the MINIMUM starting health needed to guarantee survival. Example: `dungeon = [[-2,-3,3],[-5,-10,1],[10,30,-5]]` → `7`.

## 2. Why & when

Use this shape whenever a grid path problem asks for the minimum STARTING resource needed to survive a path, where the resource can go up or down along the way, and must never touch zero or below. The forward direction (start to end) is awkward here, because the required starting health depends on the WORST point still ahead, not the best point already passed — so this problem is solved working BACKWARD, from the destination to the start.

## 3. Core concept

**Key idea:** let `dp[r][c]` = the minimum health needed WHEN ENTERING cell `(r, c)` to guarantee survival all the way to the destination. Compute it from the bottom-right corner backward to the top-left.

**Steps:**
1. Base case: `dp[n-1][m-1] = max(1, 1 - dungeon[n-1][m-1])` (after taking this cell's effect, health must still be at least `1`; work out what it needed to be BEFORE entering, to end up at least at `1`).
2. For the last row and last column, there is only one direction back (right or down, respectively): `dp[r][c] = max(1, dp[r][c+1] - dungeon[r][c])` for the last row; `dp[r][c] = max(1, dp[r+1][c] - dungeon[r][c])` for the last column.
3. For every other cell: `dp[r][c] = max(1, min(dp[r+1][c], dp[r][c+1]) - dungeon[r][c])` — pick whichever NEXT cell demands less health, since the knight will choose the easier direction.
4. The answer is `dp[0][0]`.

**Why working backward is correct:** the health needed ENTERING a cell depends on the health needed for the REST of the path (still ahead), not on how much health has already been spent — so the sub-problem naturally decomposes from the destination backward. `max(1, needed - dungeon[r][c])` reverses the forward rule "health after this cell = health before + dungeon[r][c]," and the `max(1, ...)` clamp accounts for potions so large that no minimum health is actually required to survive this step (health can never need to be less than `1` entering any cell).

## 4. Diagram

<svg viewBox="0 0 480 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="cell computing the minimum health needed to enter it by looking at the smaller requirement of the two cells ahead">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">dp[r][c] = max(1, min(dp[r+1][c], dp[r][c+1]) - dungeon[r][c])</text>
    <rect x="180" y="40" width="60" height="26" fill="#3fb950"/><text x="210" y="58" text-anchor="middle" font-size="10" fill="#0d1117">r,c</text>
    <rect x="180" y="76" width="60" height="26" fill="#30363d" stroke="#8b949e"/><text x="210" y="94" text-anchor="middle" font-size="10">down</text>
    <rect x="250" y="40" width="60" height="26" fill="#30363d" stroke="#8b949e"/><text x="280" y="58" text-anchor="middle" font-size="10">right</text>
    <rect x="10" y="115" width="330" height="24" fill="#3fb950"/><text x="175" y="132" fill="#0d1117" text-anchor="middle" font-size="10">computed backward: destination first, origin last</text>
  </g>
</svg>

Each cell's required entering health picks the easier of its two forward paths, computed from the destination back to the start.

## 5. Runnable example

```java
// DungeonGame.java
public class DungeonGame {

    // KEY INSIGHT: work backward from the destination -- the health
    // needed entering a cell depends on the path still AHEAD, so the
    // destination's requirement must be known first.

    static int calculateMinimumHP(int[][] dungeon) {
        int rows = dungeon.length, cols = dungeon[0].length;
        int[][] dp = new int[rows][cols];

        for (int r = rows - 1; r >= 0; r--) {
            for (int c = cols - 1; c >= 0; c--) {
                int needed;
                if (r == rows - 1 && c == cols - 1) {
                    needed = 1 - dungeon[r][c];
                } else if (r == rows - 1) {
                    needed = dp[r][c + 1] - dungeon[r][c];
                } else if (c == cols - 1) {
                    needed = dp[r + 1][c] - dungeon[r][c];
                } else {
                    needed = Math.min(dp[r + 1][c], dp[r][c + 1]) - dungeon[r][c];
                }
                dp[r][c] = Math.max(1, needed);
            }
        }
        return dp[0][0];
    }

    public static void main(String[] args) {
        int[][] dungeon = {{-2, -3, 3}, {-5, -10, 1}, {10, 30, -5}};
        System.out.println(calculateMinimumHP(dungeon));
        // 7
    }
}
```

**How to run:** `java DungeonGame.java`

## 6. Walkthrough

Trace `dp`, filled from bottom-right backward:

| r,c | dungeon value | needed (before clamp) | dp[r][c] |
|---|---|---|---|
| 2,2 | -5 | 1-(-5)=6 | 6 |
| 2,1 | 30 | 6-30=-24 | 1 |
| 2,0 | 10 | 1-10=-9 | 1 |
| 1,2 | 1 | 6-1=5 | 5 |
| 0,0 | -2 | min(dp[1][0],dp[0][1]) - (-2) | 7 |

`dp[0][0] = 7`, matching the expected answer: starting with `7` health, the knight can follow the path `-2 -> -3 -> 3 -> 1 -> -5` (or an equivalent route) and never drop to `0` or below. Time complexity is O(m·n). Space is O(m·n) (reducible to O(n) with a rolling row).

## 7. Gotchas & takeaways

> Gotcha: the `max(1, ...)` clamp is required at EVERY cell, not just the destination — a large potion partway through the dungeon can make the "needed" value negative or zero, but health can never legitimately need to be less than `1` entering any cell, since the knight must stay alive at every single step, not just at the end.

- Working BACKWARD (destination to origin) is the key structural choice — forward DP does not work directly here, since "the best health so far" does not determine "the minimum needed to survive what is still ahead."
- `dp[r][c] = max(1, min(next cells) - dungeon[r][c])`: reverses the forward accumulation rule, picking whichever next cell is less demanding.
- Related problems: Minimum Path Sum (forward DP, since costs simply accumulate and do not need a survival floor), Triangle (also solved bottom-up, for a similar reason: the answer from a cell depends on what's still ahead, not what came before).
