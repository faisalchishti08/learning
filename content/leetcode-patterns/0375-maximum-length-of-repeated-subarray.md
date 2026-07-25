---
card: leetcode-patterns
gi: 375
slug: maximum-length-of-repeated-subarray
title: Maximum Length of Repeated Subarray
---

## 1. What it is

Given two integer arrays `nums1` and `nums2`, return the length of their LONGEST COMMON, CONTIGUOUS subarray — a stretch of elements that appears identically (in the same order, with no gaps) in both arrays. Example: `nums1 = [1,2,3,2,1]`, `nums2 = [3,2,1,4,7]` → `3` (`[3,2,1]`).

## 2. Why & when

This looks like Longest Common Subsequence, but the CONTIGUOUS requirement changes the transition: a subarray cannot "skip" elements, so a mismatch must RESET the running match to zero, rather than falling back to a neighboring cell's best value. Use this shape whenever a problem asks for a common SUBARRAY or SUBSTRING (contiguous), not a subsequence (which allows gaps).

## 3. Core concept

**Key idea:** build `dp[i][j]` = the length of the common contiguous run ENDING exactly at `nums1[i-1]` and `nums2[j-1]`, for every `i, j`. Track the overall maximum separately, since the answer can end anywhere, not just at the final cell.

**Steps:**
1. Create `dp[m+1][n+1]`, all zeros. Initialize `maxLen = 0`.
2. For `i` from `1` to `m`, for `j` from `1` to `n`: if `nums1[i-1] == nums2[j-1]`, `dp[i][j] = dp[i-1][j-1] + 1`; else `dp[i][j] = 0` (RESET, not a fallback to a neighbor).
3. Update `maxLen = max(maxLen, dp[i][j])` after each cell. Return `maxLen`.

**Why it is correct:** a contiguous common run ending at `(i, j)` can ONLY exist if the immediately preceding elements also matched — there is no way to "skip" an element and stay contiguous. A mismatch breaks any run passing through that cell entirely, so `dp[i][j]` must drop to `0`, not fall back to `dp[i-1][j]` or `dp[i][j-1]` (which would incorrectly reintroduce a gap).

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp table contrasted with plain lcs showing a mismatch resetting to zero instead of falling back to a neighbor">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums1=[1,2,3,2,1], nums2=[3,2,1,4,7]</text>
    <text x="10" y="45">matching run 3,2,1 gives dp values 1, 2, 3 along the diagonal</text>
    <text x="10" y="65">next comparison (2 vs 4): mismatch -&gt; dp[i][j] = 0 (reset, not max(...))</text>
    <rect x="10" y="85" width="280" height="24" fill="#3fb950"/><text x="150" y="102" fill="#0d1117" text-anchor="middle" font-size="10">maxLen tracked separately = 3</text>
  </g>
</svg>

Unlike LCS, a mismatch here zeroes the run instead of carrying a value forward from a neighbor.

## 5. Runnable example

```java
// MaximumLengthOfRepeatedSubarray.java
public class MaximumLengthOfRepeatedSubarray {

    // KEY INSIGHT: "contiguous" means a mismatch must RESET dp[i][j]
    // to 0, not fall back to a neighbor like plain LCS -- and the
    // answer is the MAXIMUM over all cells, not just the last one.

    static int findLength(int[] nums1, int[] nums2) {
        int m = nums1.length, n = nums2.length;
        int[][] dp = new int[m + 1][n + 1];
        int maxLen = 0;

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (nums1[i - 1] == nums2[j - 1]) {
                    dp[i][j] = dp[i - 1][j - 1] + 1;
                    maxLen = Math.max(maxLen, dp[i][j]);
                }
                // else dp[i][j] stays 0 (default)
            }
        }
        return maxLen;
    }

    public static void main(String[] args) {
        System.out.println(findLength(new int[]{1, 2, 3, 2, 1}, new int[]{3, 2, 1, 4, 7}));
        // 3
        System.out.println(findLength(new int[]{0, 0, 0}, new int[]{0, 0, 0}));
        // 3
    }
}
```

**How to run:** `java MaximumLengthOfRepeatedSubarray.java`

## 6. Walkthrough

Trace key diagonal cells for `findLength([1,2,3,2,1], [3,2,1,4,7])`:

| i,j | values | match? | dp[i][j] | maxLen |
|---|---|---|---|---|
| 3,1 | 3,3 | yes | dp[2][0]+1=1 | 1 |
| 4,2 | 2,2 | yes | dp[3][1]+1=2 | 2 |
| 5,3 | 1,1 | yes | dp[4][2]+1=3 | 3 |

`maxLen = 3`, matching the expected `3` (`[3,2,1]`). Time complexity is O(m · n). Space is O(m · n) (reducible to O(min(m,n))).

## 7. Gotchas & takeaways

> Gotcha: reusing the plain LCS mismatch rule (`max(dp[i-1][j], dp[i][j-1])`) instead of resetting to `0` silently turns this into the (wrong) subsequence-length answer instead of the contiguous-subarray answer — always double check whether a problem wants "subarray/substring" (reset) or "subsequence" (fallback).

- `dp[i][j] = dp[i-1][j-1]+1` on match, `0` on mismatch: the contiguous variant of the LCS-family template.
- The answer is `max` over ALL cells, not `dp[m][n]` — the longest repeated run can end anywhere in either array, not necessarily at the very last elements.
- Related problems: Longest Common Subsequence (the non-contiguous version, using fallback instead of reset), Longest Palindromic Substring (a different pattern, but shares the "contiguous run resets on failure" intuition).
