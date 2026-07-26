---
card: leetcode-patterns
gi: 450
slug: jump-game-ii
title: Jump Game II
---

## 1. What it is

Same setup as Jump Game, but now assume you can ALWAYS reach the last index — return the MINIMUM number of jumps needed to get there. Example: `nums = [2,3,1,1,4]` → `2` (jump from index `0` to index `1`, then from index `1` to index `4`).

## 2. Why & when

Use this shape whenever a reachability problem also asks for the FEWEST steps, and each step can reach a whole RANGE of positions (not just one fixed neighbor). This is a greedy "level by level" idea: process one JUMP'S worth of reachable positions at a time, counting jumps only when the current range is fully explored.

## 3. Core concept

**Key idea:** think of the array as divided into "jump levels" — the SET of positions reachable using at most `k` jumps forms a growing range. Track the END of the CURRENT level (`curEnd`), and the FARTHEST any position within the current level could reach (`farthest`).

**Steps:**
1. Initialize `jumps = 0`, `curEnd = 0`, `farthest = 0`.
2. For each index `i` from `0` to `n-2` (no jump is needed FROM the last index): update `farthest = max(farthest, i + nums[i])`.
3. If `i == curEnd` (the current level's range has just been fully scanned), increment `jumps`, and set `curEnd = farthest` (the next level's range extends to the farthest reach found while exploring the current one).
4. Return `jumps` once the loop completes.

**Why this level-by-level greedy finds the MINIMUM jump count:** every position within the current level is reachable using the SAME number of jumps taken so far — so the moment the scan finishes exploring the current level (`i == curEnd`), the FARTHEST position found (`farthest`) is DEFINITELY reachable with exactly ONE more jump, and nothing closer can be reached with fewer. This means each level transition corresponds to exactly one additional REQUIRED jump, and expanding to the farthest possible range at each level guarantees the fewest total levels (jumps) are used.

## 4. Diagram

<svg viewBox="0 0 480 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="positions grouped into levels by number of jumps needed with the current level fully scanned before moving to the next level using the farthest reach found">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">nums = [2, 3, 1, 1, 4] -- level 0: {0}, level 1: {1,2}, level 2: {3,4}</text>
    <rect x="20" y="40" width="60" height="26" fill="#3fb950"/><text x="50" y="58" text-anchor="middle" font-size="10" fill="#0d1117">i=0</text>
    <rect x="100" y="40" width="120" height="26" fill="#30363d" stroke="#8b949e"/><text x="160" y="58" text-anchor="middle" font-size="10">i=1,2 (level 1)</text>
    <rect x="240" y="40" width="120" height="26" fill="#30363d" stroke="#8b949e"/><text x="300" y="58" text-anchor="middle" font-size="10">i=3,4 (level 2)</text>
    <rect x="10" y="80" width="330" height="24" fill="#3fb950"/><text x="175" y="97" fill="#0d1117" text-anchor="middle" font-size="10">reaching the end of a level forces exactly one more jump</text>
  </g>
</svg>

Positions group naturally into "levels" by minimum jump count — finishing one level's scan always triggers exactly one more required jump.

## 5. Runnable example

```java
// JumpGameII.java
public class JumpGameII {

    // KEY INSIGHT: positions reachable with the SAME jump count form a
    // "level" -- finishing a level's scan (i == curEnd) means exactly
    // one more jump is needed to reach the next level's farthest point.

    static int jump(int[] nums) {
        int jumps = 0, curEnd = 0, farthest = 0;
        for (int i = 0; i < nums.length - 1; i++) {
            farthest = Math.max(farthest, i + nums[i]);
            if (i == curEnd) {
                jumps++;
                curEnd = farthest;
            }
        }
        return jumps;
    }

    public static void main(String[] args) {
        System.out.println(jump(new int[]{2, 3, 1, 1, 4}));
        // 2
        System.out.println(jump(new int[]{2, 3, 0, 1, 4}));
        // 2
    }
}
```

**How to run:** `java JumpGameII.java`

## 6. Walkthrough

Trace `jump([2,3,1,1,4])`:

| i | farthest after update | i == curEnd? | jumps after | curEnd after |
|---|---|---|---|---|
| 0 | max(0,0+2)=2 | 0==0? yes | 1 | 2 |
| 1 | max(2,1+3)=4 | 1==2? no | 1 | 2 |
| 2 | max(4,2+1)=4 | 2==2? yes | 2 | 4 |
| 3 | max(4,3+1)=4 | 3==4? no | 2 | 4 |

Final `jumps = 2`, matching the expected answer: index `0` to index `1` (level 1), then index `1` to index `4` (level 2). Time complexity is O(n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: the loop condition is `i < nums.length - 1`, not `i < nums.length` — no jump is ever needed FROM the last index (you are already there), so including it would risk an incorrect extra jump count, or reading past useful bounds in edge cases.

- Grouping positions into "jump levels," expanding to the farthest reach at each level transition: the key insight that turns "minimum jumps" into a greedy, single-pass problem instead of a BFS or DP.
- `curEnd` marks WHEN to increment the jump count; `farthest` tracks WHAT the next level's boundary will be — these are two DIFFERENT running values, both needed together.
- Related problems: Jump Game (the simpler feasibility-only version, without counting the minimum number of jumps), Gas Station (a different single-pass greedy, tracking a cumulative balance rather than level boundaries).
