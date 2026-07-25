---
card: leetcode-patterns
gi: 393
slug: longest-increasing-subsequence
title: Longest Increasing Subsequence
---

## 1. What it is

Given an integer array `nums`, return the length of the LONGEST STRICTLY INCREASING subsequence — elements chosen in their original order, each strictly greater than the one before it, but not necessarily contiguous. Example: `nums = [10,9,2,5,3,7,101,18]` → `4` (`[2,3,7,18]` or `[2,3,7,101]`).

## 2. Why & when

This is the textbook LIS problem, the exact pattern this section is named after. Use this shape whenever you need the length of the longest chain of elements from ONE array, picked in order, each strictly greater than the previous.

## 3. Core concept

**Key idea:** build `dp[i]` = the length of the longest increasing subsequence ENDING exactly at index `i`, for every `i`, by checking every earlier index for compatibility.

**Steps (O(n^2) version):**
1. Create `dp[n]`, all initialized to `1`.
2. For `i` from `1` to `n-1`, for `j` from `0` to `i-1`: if `nums[j] < nums[i]`, `dp[i] = max(dp[i], dp[j] + 1)`.
3. Return `max(dp)`.

**Why it is correct:** the longest increasing subsequence ending at `i` either is just `nums[i]` alone (length `1`), or extends some earlier increasing subsequence ending at a SMALLER value. Checking every earlier index `j` where `nums[j] < nums[i]` and taking the best `dp[j] + 1` covers every possible way to extend into `i`.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp array for the example input showing index 5 value 7 extending from index 4 value 3">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [10,9,2,5,3,7,101,18]</text>
    <text x="10" y="45">dp = [1, 1, 1, 2, 2, 3, 4, 4]</text>
    <rect x="10" y="65" width="240" height="24" fill="#3fb950"/><text x="130" y="82" fill="#0d1117" text-anchor="middle" font-size="10">max(dp) = 4</text>
  </g>
</svg>

Each position's best chain length is the max over every compatible earlier chain, plus one.

## 5. Runnable example

```java
// LongestIncreasingSubsequence.java
public class LongestIncreasingSubsequence {

    // KEY INSIGHT: dp[i] extends the best chain among ALL earlier
    // elements smaller than nums[i], not just the immediately
    // preceding one.

    static int lengthOfLIS(int[] nums) {
        int n = nums.length;
        int[] dp = new int[n];
        java.util.Arrays.fill(dp, 1);
        int maxLen = 1;

        for (int i = 1; i < n; i++) {
            for (int j = 0; j < i; j++) {
                if (nums[j] < nums[i]) {
                    dp[i] = Math.max(dp[i], dp[j] + 1);
                }
            }
            maxLen = Math.max(maxLen, dp[i]);
        }
        return maxLen;
    }

    public static void main(String[] args) {
        System.out.println(lengthOfLIS(new int[]{10, 9, 2, 5, 3, 7, 101, 18}));
        // 4
        System.out.println(lengthOfLIS(new int[]{7, 7, 7, 7}));
        // 1
    }
}
```

**How to run:** `java LongestIncreasingSubsequence.java`

## 6. Walkthrough

Trace `lengthOfLIS([10,9,2,5,3,7,101,18])`:

| i | value | best j | dp[i] |
|---|---|---|---|
| 2 | 2 | (none smaller before it) | 1 |
| 4 | 3 | j=2 (value 2) | 2 |
| 5 | 7 | j=4 (value 3, dp=2) | 3 |
| 6 | 101 | j=5 (value 7, dp=3) | 4 |

`max(dp) = 4`, matching the expected answer. Time complexity is O(n^2) for the DP version (O(n log n) with patience sorting). Space is O(n).

## 7. Gotchas & takeaways

> Gotcha: this problem asks for STRICTLY increasing — using `nums[j] <= nums[i]` instead of `<` would silently solve the wrong problem (non-decreasing subsequence) for inputs with duplicate values, like `[7,7,7,7]`.

- `dp[i] = max over compatible j of dp[j] + 1`: the exact template every other problem in this section builds from.
- For large `n`, switch to the O(n log n) patience-sorting technique from the template page — it computes the same length faster, though it does not directly hand you the actual subsequence.
- Related problems: Russian Doll Envelopes (LIS applied to 2D pairs, after sorting), Number of Longest Increasing Subsequence (counts HOW MANY chains achieve the max length, needing an extra `count[i]` array alongside `dp[i]`).
