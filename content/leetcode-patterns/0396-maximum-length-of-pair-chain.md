---
card: leetcode-patterns
gi: 396
slug: maximum-length-of-pair-chain
title: Maximum Length of Pair Chain
---

## 1. What it is

Given an array of pairs `pairs[i] = [left_i, right_i]`, a pair `(c, d)` can follow a pair `(a, b)` in a chain if `b < c`. Return the length of the LONGEST chain that can be formed, using pairs from the array in any order you choose. Example: `pairs = [[1,2],[2,3],[3,4]]` → `2` (`[1,2] -> [3,4]`).

## 2. Why & when

This is LIS applied to PAIRS instead of single numbers: "compatible" now means "the next pair's left value exceeds the current pair's right value." Like Largest Divisible Subset, this needs a SORT first (by the pair's first value) to make the LIS-style left-to-right scan valid. Use this shape whenever a problem chains together INTERVALS or pairs under a non-overlapping or ordering condition.

## 3. Core concept

**Key idea:** sort `pairs` by their first element. Then build `dp[i]` = the length of the longest chain ENDING at `pairs[i]`, using the same "check every earlier compatible pair" DP as LIS, with compatibility being `pairs[j][1] < pairs[i][0]`.

**Steps:**
1. Sort `pairs` by `pairs[i][0]` (the first element of each pair), ascending.
2. Create `dp[n]`, all `1`.
3. For `i` from `1` to `n-1`, for `j` from `0` to `i-1`: if `pairs[j][1] < pairs[i][0]`, `dp[i] = max(dp[i], dp[j] + 1)`.
4. Return `max(dp)`.

**Why sorting first helps (though it is not strictly required for correctness, only for the simple linear scan to make sense):** sorting by the first element ensures that when scanning `j < i`, every pair with a SMALLER starting value has already been considered — matching the same left-to-right, "extend from an earlier compatible element" logic used throughout the LIS family.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="sorted pairs showing pair 3,4 chaining after pair 1,2 because 2 is less than 3">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">sorted pairs = [[1,2],[2,3],[3,4]]</text>
    <text x="10" y="45">pairs[2][0]=3 &gt; pairs[0][1]=2 -&gt; compatible: dp[2]=max(dp[2],dp[0]+1)=2</text>
    <text x="10" y="65">pairs[2][0]=3, pairs[1][1]=3 -&gt; NOT &lt; 3, incompatible with pairs[1]</text>
    <rect x="10" y="85" width="240" height="24" fill="#3fb950"/><text x="130" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp = [1,1,2]; max chain length 2</text>
  </g>
</svg>

Each pair only chains onto an earlier pair whose right value is STRICTLY less than its own left value.

## 5. Runnable example

```java
// MaximumLengthOfPairChain.java
import java.util.Arrays;
import java.util.Comparator;

public class MaximumLengthOfPairChain {

    // KEY INSIGHT: sort pairs by their first value, then run the LIS
    // template with "pairs[j][1] < pairs[i][0]" as the compatibility
    // check.

    static int findLongestChain(int[][] pairs) {
        Arrays.sort(pairs, Comparator.comparingInt(p -> p[0]));
        int n = pairs.length;
        int[] dp = new int[n];
        Arrays.fill(dp, 1);
        int maxLen = 1;

        for (int i = 1; i < n; i++) {
            for (int j = 0; j < i; j++) {
                if (pairs[j][1] < pairs[i][0]) {
                    dp[i] = Math.max(dp[i], dp[j] + 1);
                }
            }
            maxLen = Math.max(maxLen, dp[i]);
        }
        return maxLen;
    }

    public static void main(String[] args) {
        System.out.println(findLongestChain(new int[][]{{1, 2}, {2, 3}, {3, 4}}));
        // 2
        System.out.println(findLongestChain(new int[][]{{1, 2}, {7, 8}, {4, 5}}));
        // 3
    }
}
```

**How to run:** `java MaximumLengthOfPairChain.java`

## 6. Walkthrough

Trace `findLongestChain([[1,2],[2,3],[3,4]])` (already sorted by first element):

| i | pair | best j | dp[i] |
|---|---|---|---|
| 0 | [1,2] | - | 1 |
| 1 | [2,3] | pairs[0][1]=2, not &lt; 2 | 1 |
| 2 | [3,4] | pairs[0][1]=2 &lt; 3 | 2 |

`max(dp) = 2`, matching the expected answer. Time complexity is O(n^2) for the DP (plus O(n log n) for sorting). Space is O(n).

## 7. Gotchas & takeaways

> Gotcha: this specific problem also has a well-known O(n log n) GREEDY solution (sort by the SECOND element instead, then greedily pick every pair whose left value exceeds the last chosen pair's right value) — the DP approach shown here is more general and directly transfers the LIS pattern, but if `n` is large, the greedy alternative is faster.

- Sorting by the FIRST element (for the DP approach) versus the SECOND element (for the greedy approach) are different strategies suited to different algorithms — mixing them up breaks either approach's correctness.
- The compatibility check `pairs[j][1] < pairs[i][0]` (strict inequality) matches the problem's own definition of "can follow" — double-check whether a similar problem uses `<=` instead, which would change the answer for touching intervals.
- Related problems: Longest Increasing Subsequence (the single-number version of this exact chain-building idea), Largest Divisible Subset (also needs a sort-first step before running the LIS-style scan).
