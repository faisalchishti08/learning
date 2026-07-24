---
card: leetcode-patterns
gi: 311
slug: matchsticks-to-square
title: Matchsticks to Square
---

## 1. What it is

Given an integer array `matchsticks`, where each value is the length of one matchstick, return `true` if all the matchsticks can be arranged to form a square, using every matchstick exactly once, with no breaking or overlapping. Example: `matchsticks = [1,1,2,2,2]` → `true` (the square has side length `2`: one side uses the two `1`s, and each of the other three sides uses one `2`).

## 2. Why & when

This is a group-partitioning backtracking problem: assign each matchstick to one of 4 sides, backing off whenever a side's running length would exceed the target, or the totals cannot possibly divide evenly. Use this shape whenever a problem asks whether a set of items can be split into a FIXED NUMBER of equal (or otherwise constrained) groups.

## 3. Core concept

**Key idea:** the target side length is `sum(matchsticks) / 4` (must divide evenly, or the answer is immediately `false`). Try placing each matchstick, largest first, into one of the 4 sides, backtracking whenever a side overflows.

**Steps:**
1. Compute `total = sum(matchsticks)`. If `total % 4 != 0`, return `false` immediately (prune before any search).
2. Compute `side = total / 4`. Sort `matchsticks` DESCENDING (placing large sticks first fails faster, pruning more of the search tree earlier).
3. Track `sides[4]`, the running length of each of the 4 sides, all starting at `0`.
4. Define `backtrack(index)`. **Base case:** if `index == matchsticks.length`, check that ALL 4 sides equal `side` exactly; return that result.
5. **Loop:** for each of the 4 sides: if `sides[i] + matchsticks[index] > side`, skip (prune). Otherwise, add the matchstick to `sides[i]` (choose), recurse to `index + 1`, then subtract it back out (un-choose). If a side is currently `0` and this attempt fails, skip trying any OTHER currently-empty side too (they are equivalent, so trying more than one wastes time).

**Why it is correct:** a valid square must have all 4 sides exactly equal to `side = total / 4`, so any partial assignment where a side already exceeds `side` can never be completed correctly — pruning it immediately is safe. Sorting descending places the hardest-to-fit sticks first, which fails bad branches sooner rather than discovering the same failure deep in the recursion. Skipping duplicate attempts at multiple EMPTY sides avoids redundant work, since placing a stick into "the first empty side" versus "the second empty side" explores functionally identical states.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Assigning matchsticks 2,2,2,1,1 sorted descending to 4 sides each targeting length 2, backtracking when a side would overflow">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">matchsticks = [2,2,2,1,1] (sorted desc), sum=8, target side = 8/4 = 2</text>
    <text x="10" y="45">place 2 -&gt; side[0]=2 (done)</text>
    <text x="10" y="65">place 2 -&gt; side[1]=2 (done)</text>
    <text x="10" y="85">place 2 -&gt; side[2]=2 (done)</text>
    <text x="10" y="105">place 1 -&gt; side[3]=1; place 1 -&gt; side[3]=2 (done)</text>
    <rect x="10" y="120" width="220" height="24" fill="#3fb950"/><text x="120" y="137" fill="#0d1117" text-anchor="middle" font-size="10">all 4 sides = 2 -&gt; true</text>
  </g>
</svg>

Sorting descending places the three `2`-length sticks first, each completing its own side immediately, before the two `1`s combine to finish the fourth.

## 5. Runnable example

```java
// MatchsticksToSquare.java
import java.util.*;

public class MatchsticksToSquare {

    // KEY INSIGHT: a valid square needs sum(matchsticks)/4 as an exact
    // integer side length; sorting sticks descending fails bad
    // branches faster, since the hardest-to-place sticks are tried
    // first, pruning more of the search tree earlier.

    static boolean makesquare(int[] matchsticks) {
        int total = 0;
        for (int stick : matchsticks) total += stick;
        if (total % 4 != 0) return false;

        int side = total / 4;
        Integer[] sticks = new Integer[matchsticks.length];
        for (int i = 0; i < matchsticks.length; i++) sticks[i] = matchsticks[i];
        Arrays.sort(sticks, Collections.reverseOrder());

        int[] sides = new int[4];
        return backtrack(sticks, 0, sides, side);
    }

    static boolean backtrack(Integer[] sticks, int index, int[] sides, int target) {
        if (index == sticks.length) {
            return sides[0] == target && sides[1] == target && sides[2] == target;
            // sides[3] must equal target too, guaranteed by the total sum check
        }

        for (int i = 0; i < 4; i++) {
            if (sides[i] + sticks[index] > target) continue; // prune: would overflow this side

            sides[i] += sticks[index];                 // choose
            if (backtrack(sticks, index + 1, sides, target)) return true; // recurse
            sides[i] -= sticks[index];                 // un-choose

            if (sides[i] == 0) break; // prune: skip other equally-empty sides
        }
        return false;
    }

    public static void main(String[] args) {
        System.out.println(makesquare(new int[]{1, 1, 2, 2, 2}));
        // true
        System.out.println(makesquare(new int[]{3, 3, 3, 3, 4}));
        // false
    }
}
```

**How to run:** `java MatchsticksToSquare.java`

## 6. Walkthrough

Trace `makesquare([1,1,2,2,2])`, sorted descending to `[2,2,2,1,1]`, `target = 2`:

| index | stick | tried side | sides before | fits? | sides after |
|---|---|---|---|---|---|
| 0 | 2 | side 0 | [0,0,0,0] | yes (0+2<=2) | [2,0,0,0] |
| 1 | 2 | side 0 fails (2+2&gt;2), try side 1 | [2,0,0,0] | yes | [2,2,0,0] |
| 2 | 2 | side 2 | [2,2,0,0] | yes | [2,2,2,0] |
| 3 | 1 | side 3 | [2,2,2,0] | yes | [2,2,2,1] |
| 4 | 1 | side 3 | [2,2,2,1] | yes (1+1&lt;=2) | [2,2,2,2] |
| 5 (index==length) | — | — | check sides[0..2]==2 | all true | return true |

Final result: `true`. Time complexity is O(4^n) in the worst case, `n` sticks each tried against up to 4 sides — but the "skip duplicate empty sides" and descending-sort prunes cut this drastically in practice. Space is O(n), for the recursion depth and the `sides` array.

## 7. Gotchas & takeaways

> Gotcha: the base case only needs to check `sides[0]`, `sides[1]`, and `sides[2]` equal `target` — `sides[3]` is guaranteed to equal `target` too, since the total of all 4 sides always equals the fixed `total` sum, and 3 sides already summing to `3 * target` forces the 4th to be exactly `total - 3*target = target`.

- Sorting descending before searching is a general backtracking optimization: placing the most CONSTRAINING choices first fails invalid branches sooner.
- The "skip other empty sides" prune (`if (sides[i] == 0) break;`) is a classic technique for problems with INTERCHANGEABLE empty groups — without it, correctness is unaffected, but performance suffers badly on inputs with many small sticks.
- Related problems: Partition to K Equal Sum Subsets (the direct generalization of this problem to `k` groups instead of a fixed 4), Partition Equal Subset Sum (the `k=2` special case, often solved with dynamic programming instead).
