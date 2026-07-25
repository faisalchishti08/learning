---
card: leetcode-patterns
gi: 395
slug: number-of-longest-increasing-subsequence
title: Number of Longest Increasing Subsequence
---

## 1. What it is

Given an integer array `nums`, return the NUMBER OF DISTINCT longest increasing subsequences. Example: `nums = [1,3,5,4,7]` → `2` (the two longest increasing subsequences, both length 4, are `[1,3,4,7]` and `[1,3,5,7]`).

## 2. Why & when

This extends the standard LIS DP with a SECOND array tracking counts: alongside `dp[i]` (the longest chain length ending at `i`), track `count[i]` (how many DISTINCT chains of that maximum length end at `i`). Use this shape whenever a problem asks not just for the LIS length, but for HOW MANY subsequences achieve that length.

## 3. Core concept

**Key idea:** build `dp[i]` and `count[i]` together, for every `i`, by checking every earlier compatible element and combining based on whether it TIES or BEATS the current best.

**Steps:**
1. Create `dp[n]`, all `1`, and `count[n]`, all `1` (every single element is itself one chain of length 1).
2. For `i` from `1` to `n-1`, for `j` from `0` to `i-1` with `nums[j] < nums[i]`:
   - If `dp[j] + 1 > dp[i]`: a NEW LONGER chain is found through `j` — set `dp[i] = dp[j] + 1` and `count[i] = count[j]` (RESET the count, discarding any shorter chains previously found).
   - Else if `dp[j] + 1 == dp[i]`: this `j` offers an EQUALLY long chain — add `count[i] += count[j]` (accumulate, do not reset).
3. Find `maxLen = max(dp)`. Return the sum of `count[i]` for every `i` where `dp[i] == maxLen`.

**Why it is correct:** `count[i]` must be RESET (not accumulated) whenever a strictly longer chain is discovered, because all previously counted chains ending at `i` were shorter and are no longer relevant to the new maximum length. When a TIE is found, the counts from that tying source must be ADDED, since each way of reaching `dp[j]`'s length independently extends into a distinct way of reaching `dp[i]`'s length.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp and count arrays for the example input showing a reset when a longer chain is found and an accumulation when chains tie">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums=[1,3,5,4,7]; at i=4 (value 7), checking j=1(3,dp2,cnt1), j=2(5,dp3,cnt1), j=3(4,dp3,cnt1)</text>
    <text x="10" y="45">j=1: dp[1]+1=3 &lt; current dp[4] so far -&gt; skip until better found</text>
    <text x="10" y="65">j=2: dp[2]+1=4 &gt; dp[4]=1 -&gt; RESET: dp[4]=4, count[4]=count[2]=1</text>
    <text x="10" y="85">j=3: dp[3]+1=4 == dp[4]=4 -&gt; ACCUMULATE: count[4] += count[3] = 1+1 = 2</text>
    <rect x="10" y="105" width="260" height="24" fill="#3fb950"/><text x="140" y="122" fill="#0d1117" text-anchor="middle" font-size="10">count[4] = 2 distinct length-4 chains ending at 7</text>
  </g>
</svg>

A strictly longer chain resets the count; an equally long chain adds to it.

## 5. Runnable example

```java
// NumberOfLongestIncreasingSubsequence.java
public class NumberOfLongestIncreasingSubsequence {

    // KEY INSIGHT: track dp[i] (longest chain length ending at i) AND
    // count[i] (how many such longest chains) together -- reset the
    // count on a strictly longer find, accumulate on a tie.

    static int findNumberOfLIS(int[] nums) {
        int n = nums.length;
        int[] dp = new int[n];
        int[] count = new int[n];
        java.util.Arrays.fill(dp, 1);
        java.util.Arrays.fill(count, 1);

        int maxLen = 1;
        for (int i = 1; i < n; i++) {
            for (int j = 0; j < i; j++) {
                if (nums[j] < nums[i]) {
                    if (dp[j] + 1 > dp[i]) {
                        dp[i] = dp[j] + 1;
                        count[i] = count[j];
                    } else if (dp[j] + 1 == dp[i]) {
                        count[i] += count[j];
                    }
                }
            }
            maxLen = Math.max(maxLen, dp[i]);
        }

        int total = 0;
        for (int i = 0; i < n; i++) {
            if (dp[i] == maxLen) total += count[i];
        }
        return total;
    }

    public static void main(String[] args) {
        System.out.println(findNumberOfLIS(new int[]{1, 3, 5, 4, 7}));
        // 2
        System.out.println(findNumberOfLIS(new int[]{2, 2, 2, 2, 2}));
        // 5
    }
}
```

**How to run:** `java NumberOfLongestIncreasingSubsequence.java`

## 6. Walkthrough

Trace `findNumberOfLIS([1,3,5,4,7])`:

| i | value | dp[i] | count[i] |
|---|---|---|---|
| 0 | 1 | 1 | 1 |
| 1 | 3 | 2 | 1 |
| 2 | 5 | 3 | 1 |
| 3 | 4 | 3 | 1 |
| 4 | 7 | 4 | 2 |

`maxLen = 4`; only `i=4` has `dp[i]==4`, contributing `count[4]=2`. Total: `2`, matching the expected answer. Time complexity is O(n^2). Space is O(n).

## 7. Gotchas & takeaways

> Gotcha: using `count[i] = count[j]` (an assignment) on EVERY compatible `j`, instead of only on a strict improvement, silently loses previously accumulated ties — the reset-vs-accumulate distinction (`>` triggers reset, `==` triggers accumulate) must be checked as two separate branches, not merged.

- `dp[i]` and `count[i]`, updated together with a reset-on-improve, accumulate-on-tie rule: the counting extension of the plain LIS template.
- All-equal inputs (like `[2,2,2,2,2]`) give `maxLen=1` and `count[i]=1` for every `i`, so the total is `n` — every single element is its own valid length-1 "longest" subsequence.
- Related problems: Longest Increasing Subsequence (the length-only version this problem extends), Distinct Subsequences (a different counting DP, over two strings instead of one array's chains).
