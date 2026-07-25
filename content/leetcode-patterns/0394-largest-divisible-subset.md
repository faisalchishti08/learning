---
card: leetcode-patterns
gi: 394
slug: largest-divisible-subset
title: Largest Divisible Subset
---

## 1. What it is

Given a set of DISTINCT positive integers `nums`, return the LARGEST subset such that EVERY pair `(a, b)` in it satisfies `a % b == 0` or `b % a == 0`. Example: `nums = [1,2,4,8]` → `[1,2,4,8]` (every element divides the next).

## 2. Why & when

This is LIS with the compatibility rule changed from "strictly greater" to "divides evenly" — and it needs one extra step: SORT the array first, since divisibility chains are easiest to reason about in increasing order. Use this shape whenever a problem asks for the largest chain under a DIVISIBILITY (or similar transitive) relation, rather than plain numeric ordering.

## 3. Core concept

**Key idea:** sort `nums` first. Then build `dp[i]` = the length of the largest divisible subset ENDING at `nums[i]` (after sorting), using the same "check every earlier compatible element" DP as LIS, but with the compatibility check being `nums[i] % nums[j] == 0` instead of `nums[j] < nums[i]`.

**Steps:**
1. Sort `nums` in ascending order.
2. Create `dp[n]`, all `1`, and `parent[n]`, all `-1` (for reconstruction).
3. For `i` from `1` to `n-1`, for `j` from `0` to `i-1`: if `nums[i] % nums[j] == 0` and `dp[j] + 1 > dp[i]`, set `dp[i] = dp[j] + 1` and `parent[i] = j`.
4. Find the index with the maximum `dp[i]`, then follow `parent` pointers backward to reconstruct the actual subset.

**Why sorting first is essential, and why it is correct:** after sorting, if `nums[i] % nums[j] == 0` for `j < i` (so `nums[j] <= nums[i]`), then EVERY element already in the divisible chain ending at `j` also divides `nums[i]`, because divisibility is TRANSITIVE (if `a` divides `b` and `b` divides `c`, then `a` divides `c`). This transitivity is exactly what makes the LIS-style "extend from the best smaller compatible element" transition valid here — without sorting, a later, larger element might divide an earlier, smaller one in a way that breaks the chain's transitivity.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="sorted array 1 2 4 8 showing each element divisible by the previous, extending the chain by one each time">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">sorted nums = [1, 2, 4, 8]</text>
    <text x="10" y="45">4 % 2 == 0 -&gt; dp[2] = dp[1] + 1 = 3</text>
    <text x="10" y="65">8 % 4 == 0 -&gt; dp[3] = dp[2] + 1 = 4</text>
    <rect x="10" y="85" width="220" height="24" fill="#3fb950"/><text x="120" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp = [1,2,3,4]; full chain</text>
  </g>
</svg>

Sorting guarantees every divisibility check against an earlier element is transitively valid for the whole chain.

## 5. Runnable example

```java
// LargestDivisibleSubset.java
import java.util.*;

public class LargestDivisibleSubset {

    // KEY INSIGHT: sort first, then run the LIS template with
    // "nums[i] % nums[j] == 0" as the compatibility check --
    // transitivity of divisibility makes this valid after sorting.

    static List<Integer> largestDivisibleSubset(int[] nums) {
        Arrays.sort(nums);
        int n = nums.length;
        int[] dp = new int[n];
        int[] parent = new int[n];
        Arrays.fill(dp, 1);
        Arrays.fill(parent, -1);

        int bestIndex = 0;
        for (int i = 1; i < n; i++) {
            for (int j = 0; j < i; j++) {
                if (nums[i] % nums[j] == 0 && dp[j] + 1 > dp[i]) {
                    dp[i] = dp[j] + 1;
                    parent[i] = j;
                }
            }
            if (dp[i] > dp[bestIndex]) bestIndex = i;
        }

        List<Integer> result = new ArrayList<>();
        for (int i = bestIndex; i != -1; i = parent[i]) {
            result.add(nums[i]);
        }
        Collections.reverse(result);
        return result;
    }

    public static void main(String[] args) {
        System.out.println(largestDivisibleSubset(new int[]{1, 2, 4, 8}));
        // [1, 2, 4, 8]
        System.out.println(largestDivisibleSubset(new int[]{1, 2, 4, 8, 3}));
        // [1, 2, 4, 8] (or an equally-sized alternative)
    }
}
```

**How to run:** `java LargestDivisibleSubset.java`

## 6. Walkthrough

Trace `largestDivisibleSubset([1,2,4,8])` (already sorted):

| i | value | best j | dp[i] | parent[i] |
|---|---|---|---|---|
| 0 | 1 | - | 1 | -1 |
| 1 | 2 | j=0 (1%... 2%1==0) | 2 | 0 |
| 2 | 4 | j=1 (4%2==0, dp=2) | 3 | 1 |
| 3 | 8 | j=2 (8%4==0, dp=3) | 4 | 2 |

Best index is `3` (`dp=4`); following `parent`: `3 -> 2 -> 1 -> 0`, giving `[8,4,2,1]`, reversed to `[1,2,4,8]`. Time complexity is O(n^2) for the DP, plus O(n log n) for sorting. Space is O(n).

## 7. Gotchas & takeaways

> Gotcha: skipping the sort step (or sorting in the wrong direction) breaks the transitivity argument the whole algorithm depends on — checking `nums[i] % nums[j] == 0` for `j < i` is only valid reasoning when `nums[j] <= nums[i]` is guaranteed by prior sorting.

- The compatibility check swaps from "less than" (LIS) to "divides evenly," but the surrounding DP structure — scan all earlier elements, extend the best compatible chain — is unchanged.
- Reconstructing the actual subset (not just its size) needs a `parent` array, exactly like reconstructing the actual LCS string needed a backward walk through the `dp` table.
- Related problems: Longest Increasing Subsequence (the numeric-ordering version of this same DP shape), Longest String Chain (a similar chain-building DP, with "compatible" meaning "one word is the other plus one inserted letter").
