---
card: leetcode-patterns
gi: 397
slug: longest-arithmetic-subsequence
title: Longest Arithmetic Subsequence
---

## 1. What it is

Given an integer array `nums`, return the length of the LONGEST subsequence that forms an ARITHMETIC sequence — a chain where consecutive elements differ by the SAME constant amount. Example: `nums = [3,6,9,12]` → `4` (the whole array, common difference `3`).

## 2. Why & when

This is LIS with a twist: "compatible" is no longer a simple `<` check — it depends on WHICH common difference the chain is using, and a single element can be the END of MANY different chains, one per possible difference. Use this shape whenever a problem's chain-extension rule depends on a VALUE (like a difference) that must be tracked per state, not just a single boolean compatibility check.

## 3. Core concept

**Key idea:** build `dp[i]`, a MAP from "common difference" to "length of the longest arithmetic subsequence ending at `i` with that difference," for every `i`.

**Steps:**
1. Create an array of `n` empty maps, `dp[0..n-1]`.
2. For `i` from `1` to `n-1`, for `j` from `0` to `i-1`: compute `diff = nums[i] - nums[j]`. Look up `dp[j].getOrDefault(diff, 1)` — the length of the best chain ending at `j` with this SAME difference (default `1`, meaning `j` alone starts a new chain). Set `dp[i][diff] = dp[j].getOrDefault(diff, 1) + 1`.
3. Track the maximum value seen across every `dp[i][diff]` entry throughout the process. Return that maximum.

**Why it is correct:** a chain ending at `i` with difference `d` is valid only if there is some EARLIER element `j` such that `nums[i] - nums[j] == d`, AND `j` itself ends a chain with the SAME difference `d` (or is a fresh start, length `1`, if no such chain existed at `j`). Indexing the DP state by `(position, difference)` — instead of just `position` — is what lets the algorithm track many DIFFERENT possible chains ending at the same element simultaneously.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp map for index 2 value 9 looking up difference 3 in the map for index 1 value 6">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums=[3,6,9,12]; at i=2 (value 9), j=1 (value 6): diff = 9-6 = 3</text>
    <text x="10" y="45">dp[1] map: {3: 2} (chain 3,6 has length 2 with diff 3)</text>
    <text x="10" y="65">dp[2][3] = dp[1].getOrDefault(3,1) + 1 = 2 + 1 = 3</text>
    <rect x="10" y="85" width="240" height="24" fill="#3fb950"/><text x="130" y="102" fill="#0d1117" text-anchor="middle" font-size="10">chain 3,6,9 has length 3</text>
  </g>
</svg>

Each element's map holds one entry per distinct difference it could be the end of, looked up from an earlier element's own map.

## 5. Runnable example

```java
// LongestArithmeticSubsequence.java
import java.util.HashMap;
import java.util.Map;

public class LongestArithmeticSubsequence {

    // KEY INSIGHT: index the DP state by (position, difference), not
    // just position -- a map per index tracks every distinct chain
    // that could end there.

    static int longestArithSeqLength(int[] nums) {
        int n = nums.length;
        Map<Integer, Integer>[] dp = new HashMap[n];
        for (int i = 0; i < n; i++) dp[i] = new HashMap<>();

        int maxLen = 2;
        for (int i = 1; i < n; i++) {
            for (int j = 0; j < i; j++) {
                int diff = nums[i] - nums[j];
                int len = dp[j].getOrDefault(diff, 1) + 1;
                dp[i].put(diff, len);
                maxLen = Math.max(maxLen, len);
            }
        }
        return maxLen;
    }

    public static void main(String[] args) {
        System.out.println(longestArithSeqLength(new int[]{3, 6, 9, 12}));
        // 4
        System.out.println(longestArithSeqLength(new int[]{9, 4, 7, 2, 10}));
        // 3
    }
}
```

**How to run:** `java LongestArithmeticSubsequence.java`

## 6. Walkthrough

Trace `longestArithSeqLength([3,6,9,12])`:

| i | j | diff | dp[j] lookup | dp[i][diff] |
|---|---|---|---|---|
| 1 | 0 | 3 | dp[0] empty, default 1 | 2 |
| 2 | 1 | 3 | dp[1][3]=2 | 3 |
| 3 | 2 | 3 | dp[2][3]=3 | 4 |

`maxLen = 4`, matching the expected full-array answer. Time complexity is O(n^2), since each pair `(i, j)` does O(1) amortized map work. Space is O(n^2) in the worst case (each of `n` maps can hold up to `n` distinct differences).

## 7. Gotchas & takeaways

> Gotcha: `dp[j].getOrDefault(diff, 1)` (default `1`, not `0`) is essential — even if `j` has never been part of a chain with this exact difference before, `j` itself is always a valid length-1 starting point for a NEW chain with this difference.

- Using a MAP (keyed by difference) instead of a plain array-of-integers is the general technique whenever a chain's compatibility depends on a VALUE that must be matched exactly (a difference here; a ratio, a specific delta, or a category in other variants).
- `maxLen` starts at `2` (not `1`), since a valid arithmetic sequence needs at least two elements to have a defined common difference in the first place.
- Related problems: Longest Increasing Subsequence (the simpler single-array-state version of this same idea), Longest String Chain (a similar chain-building DP, but over word transformations instead of numeric differences).
