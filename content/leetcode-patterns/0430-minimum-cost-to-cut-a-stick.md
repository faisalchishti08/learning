---
card: leetcode-patterns
gi: 430
slug: minimum-cost-to-cut-a-stick
title: Minimum Cost to Cut a Stick
---

## 1. What it is

Given a stick of length `n` and a list of positions to cut it at, each cut costs the CURRENT length of the piece being cut (before that cut splits it further). Return the MINIMUM total cost to perform all the cuts, in any order you choose. Example: `n = 7`, `cuts = [1, 3, 4, 5]` → `16`.

## 2. Why & when

Use this shape whenever a problem gives you a set of "cut points" (or similar markers) inside a range, and the ORDER you process them in changes the total cost — because each action's cost depends on the CURRENT size of whatever piece it acts on. This is interval DP over the cut POSITIONS themselves, not over the stick's raw length.

## 3. Core concept

**Key idea:** add `0` and `n` as two extra "sentinel" cut positions (the stick's own ends), then SORT every position (real cuts plus the two sentinels). Build `dp[i][j]` = the minimum cost to perform all cuts that fall STRICTLY BETWEEN sorted position `i` and sorted position `j`, given that `i` and `j` themselves are already-fixed boundaries of the current piece.

**Steps:**
1. Combine `cuts` with `{0, n}`, and sort the result into an array `c` of length `m + 2` (where `m` is the number of original cuts).
2. Base case: `dp[i][j] = 0` whenever `j - i <= 1` (no real cut position lies strictly between two adjacent sorted positions).
3. For each range of sorted-position indices `[i, j]` (processed by increasing index-length), try every index `k` strictly between `i` and `j`: `dp[i][j] = min over k of (dp[i][k] + dp[k][j] + (c[j] - c[i]))`.
4. The answer is `dp[0][m+1]`.

**Why the cost term is `c[j] - c[i]`, added ONCE per range, not per cut:** whichever cut position `k` is chosen to be made FIRST inside the range `[c[i], c[j]]`, that cut acts on a piece of length EXACTLY `c[j] - c[i]` (the piece has not been split yet by anything outside this range). Every range's boundary cost is therefore fixed and known BEFORE deciding which internal cut happens first — trying every `k` as "the first cut in this range" and recursing on the two resulting halves covers every possible cutting ORDER.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="sorted cut positions with sentinels at both ends, choosing k as the first cut inside the range which costs the full current piece length">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">c = [0, 1, 3, 4, 5, 7] (sorted cuts, plus sentinels 0 and n=7)</text>
    <text x="10" y="45">choose k as the FIRST cut inside [i, j] -- costs c[j] - c[i] (the whole current piece)</text>
    <rect x="10" y="65" width="330" height="24" fill="#3fb950"/><text x="175" y="82" fill="#0d1117" text-anchor="middle" font-size="10">dp[i][j] = min over k of dp[i][k] + dp[k][j] + (c[j]-c[i])</text>
  </g>
</svg>

Whichever cut happens first inside a range pays for the entire current piece length, then splits into two independent sub-ranges.

## 5. Runnable example

```java
// MinimumCostToCutAStick.java
import java.util.*;

public class MinimumCostToCutAStick {

    // KEY INSIGHT: whichever cut is made FIRST inside a range pays the
    // full current piece length (c[j] - c[i]) -- trying every cut as
    // "first" and recursing covers every possible cutting order.

    static int minCost(int n, int[] cuts) {
        int m = cuts.length;
        Integer[] c = new Integer[m + 2];
        for (int i = 0; i < m; i++) c[i + 1] = cuts[i];
        c[0] = 0;
        c[m + 1] = n;
        Arrays.sort(c);

        int[][] dp = new int[m + 2][m + 2];
        for (int len = 2; len <= m + 1; len++) {
            for (int i = 0; i + len <= m + 1; i++) {
                int j = i + len;
                int best = Integer.MAX_VALUE;
                for (int k = i + 1; k < j; k++) {
                    best = Math.min(best, dp[i][k] + dp[k][j] + (c[j] - c[i]));
                }
                dp[i][j] = (best == Integer.MAX_VALUE) ? 0 : best;
            }
        }
        return dp[0][m + 1];
    }

    public static void main(String[] args) {
        System.out.println(minCost(7, new int[]{1, 3, 4, 5}));
        // 16
        System.out.println(minCost(9, new int[]{5, 6, 1, 4, 2}));
        // 22
    }
}
```

**How to run:** `java MinimumCostToCutAStick.java`

## 6. Walkthrough

Trace `c = [0, 1, 3, 4, 5, 7]` for `n = 7`, `cuts = [1, 3, 4, 5]` (sorted-index ranges of length `2`, meaning no cut strictly between, all start at `dp = 0`):

| range (sorted indices) | length-3+ computation | dp value |
|---|---|---|
| [0,2] (values 0,1,3) | dp[0][1]+dp[1][2]+(3-0) = 0+0+3 | 3 |
| [2,4] (values 3,4,5) | dp[2][3]+dp[3][4]+(5-3) = 0+0+2 | 2 |
| [0,4] (values 0,1,3,4,5) | best over k, at k=2 (value 3): dp[0][2]+dp[2][4]+(5-0) = 3+2+5 | 10 |
| [0,5] (full range) | best over all k, at k=2 (value 3): dp[0][2]+dp[2][5]+(7-0) = 3+6+7 | 16 |

`dp[0][5] = 16`, matching the expected answer, achieved by cutting at position `3` first (splitting the length-`7` stick, cost `7`), then optimally cutting each resulting half. Time complexity is O(m^3), where `m` is the number of cuts (the sorted position array has `m+2` entries). Space is O(m^2).

## 7. Gotchas & takeaways

> Gotcha: the cost added at each range is `c[j] - c[i]` (the DISTANCE between sorted positions), not the number of cuts inside the range — a common mistake is trying to count cuts instead of measuring the piece's physical length, which is what the problem actually charges for.

- Sorting the cuts, then padding with `0` and `n` as sentinels, turns "cut positions on a stick" into a clean interval-DP problem over the sorted position array's INDICES, not the stick's raw length.
- `dp[i][j] = min over k of (dp[i][k] + dp[k][j] + (c[j] - c[i]))`: every range's boundary cost is fixed (the current piece's length) regardless of which internal cut happens first — only the SPLIT choice varies.
- Related problems: Burst Balloons (a very similar "pick the first/last action, pay a fixed boundary cost, recurse on both halves" shape), Minimum Cost to Merge Stones (splits a range too, but under a fixed group-size constraint `K`, not a free choice of split point).
