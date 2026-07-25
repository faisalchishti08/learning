---
card: leetcode-patterns
gi: 373
slug: uncrossed-lines
title: Uncrossed Lines
---

## 1. What it is

Given two integer arrays `nums1` and `nums2`, draw connecting lines between EQUAL values (one line per pair), such that no two lines CROSS each other. Return the MAXIMUM number of connecting lines you can draw. Example: `nums1 = [1,4,2]`, `nums2 = [1,2,4]` → `2`.

## 2. Why & when

This is Longest Common Subsequence wearing a geometric costume: a set of non-crossing connecting lines between two arrays is EXACTLY a common subsequence, since "no crossing" means the connected pairs must appear in the SAME RELATIVE ORDER in both arrays — precisely what a subsequence preserves. Use this shape whenever a problem describes connecting or pairing elements between two sequences without allowing the connections to cross.

## 3. Core concept

**Key idea:** the maximum number of non-crossing lines equals the length of the LONGEST COMMON SUBSEQUENCE of `nums1` and `nums2` — run the exact same LCS DP, just over integer arrays instead of characters.

**Steps:**
1. Create `dp[m+1][n+1]`, all zeros.
2. For `i` from `1` to `m`, for `j` from `1` to `n`: if `nums1[i-1] == nums2[j-1]`, `dp[i][j] = dp[i-1][j-1] + 1`; else `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`.
3. Return `dp[m][n]`.

**Why it is correct:** two lines cross precisely when their connected pairs are OUT OF ORDER relative to each other (a line from an earlier `nums1` index to a LATER `nums2` index than another line's, or vice versa). Avoiding all crossings is the same constraint as choosing pairs that preserve relative order in both arrays — which is the exact definition of a common subsequence, so maximizing non-crossing lines is identical to maximizing common-subsequence length.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="two arrays with connecting lines between matching values, showing that non-crossing lines correspond to a common subsequence">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums1 = [1, 4, 2]</text>
    <text x="60" y="90">|</text>
    <text x="10" y="115">nums2 = [1, 2, 4]</text>
    <text x="10" y="45">line 1-1: index 0 to index 0 (no crossing risk yet)</text>
    <text x="10" y="65">line 2-2: index 2 (value 2) to index 1 (value 2)</text>
    <rect x="10" y="135" width="260" height="24" fill="#3fb950"/><text x="140" y="152" fill="#0d1117" text-anchor="middle" font-size="10">2 non-crossing lines = LCS length 2</text>
  </g>
</svg>

Connecting `1` to `1` and `2` to `2` keeps both connections in matching relative order — no crossing.

## 5. Runnable example

```java
// UncrossedLines.java
public class UncrossedLines {

    // KEY INSIGHT: non-crossing connecting lines between two arrays
    // is exactly a common subsequence -- run the plain LCS DP over
    // integers instead of characters.

    static int maxUncrossedLines(int[] nums1, int[] nums2) {
        int m = nums1.length, n = nums2.length;
        int[][] dp = new int[m + 1][n + 1];

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (nums1[i - 1] == nums2[j - 1]) {
                    dp[i][j] = dp[i - 1][j - 1] + 1;
                } else {
                    dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
                }
            }
        }
        return dp[m][n];
    }

    public static void main(String[] args) {
        System.out.println(maxUncrossedLines(new int[]{1, 4, 2}, new int[]{1, 2, 4}));
        // 2
        System.out.println(maxUncrossedLines(new int[]{2, 5, 1, 2, 5}, new int[]{10, 5, 2, 1, 5, 2}));
        // 3
    }
}
```

**How to run:** `java UncrossedLines.java`

## 6. Walkthrough

Trace `maxUncrossedLines([1,4,2], [1,2,4])`:

| i,j | values | match? | dp[i][j] |
|---|---|---|---|
| 1,1 | 1,1 | yes | dp[0][0]+1=1 |
| 2,2 | 4,2 | no | max(dp[1][2], dp[2][1])=1 |
| 3,2 | 2,2 | yes | dp[2][1]+1=2 |

`dp[3][3] = 2` (following the table through to completion), matching the expected `2`. Time complexity is O(m · n). Space is O(m · n) (reducible to O(min(m,n))).

## 7. Gotchas & takeaways

> Gotcha: trying to solve this with a GREEDY approach (always connect the first available equal pair) fails — an early greedy connection can block a LARGER later set of connections; only the DP correctly explores every ordering trade-off.

- This problem needs ZERO new logic beyond recognizing it as LCS on integer arrays — the "no crossing" geometric constraint IS the "preserve relative order" subsequence constraint.
- Values can repeat in either array; the DP handles this naturally, since it works on POSITIONS (indices), not on the uniqueness of values.
- Related problems: Longest Common Subsequence (the string version of this exact same DP), Maximum Length of Repeated Subarray (a superficially similar two-array DP, but requiring CONTIGUOUS matches, which changes the transition).
