---
card: leetcode-patterns
gi: 391
slug: dp-longest-increasing-subsequence-template-dp-i-best-ending
title: "DP: Longest Increasing Subsequence — template: dp[i] = best ending at i, or patience sorting with binary search"
---

## 1. What it is

This page gives the two reusable templates for LIS-length problems: the O(n^2) DP template (simple, flexible, works for any compatibility rule), and the O(n log n) PATIENCE SORTING template (faster, but only computes the LENGTH, not the actual subsequence, without extra bookkeeping).

## 2. Why & when

Use the O(n^2) DP template when the compatibility rule is complex (arithmetic differences, string chains, multi-criteria comparisons), or when you need to reconstruct the actual subsequence, or count HOW MANY distinct longest subsequences exist. Use the O(n log n) patience-sorting template when the input can be large (`n` up to `10^5` or more) and you only need the LENGTH of the longest chain, with a plain "strictly increasing" rule.

## 3. Core concept

**Template A — O(n^2) DP.**
1. Create `dp[n]`, all initialized to `1` (every single element is a chain of length 1 by itself).
2. For `i` from `1` to `n-1`, for `j` from `0` to `i-1`: if `nums[j] < nums[i]`, `dp[i] = max(dp[i], dp[j] + 1)`.
3. The answer is `max(dp)` over all indices.

**Template B — O(n log n) patience sorting.**
1. Maintain a list `tails`, where `tails[k]` = the SMALLEST possible value that can end an increasing subsequence of length `k + 1`, seen so far.
2. For each `num` in `nums`: binary search `tails` for the first position where `tails[pos] >= num` (the "lower bound"). If no such position exists (`num` is bigger than everything in `tails`), APPEND `num` to `tails`. Otherwise, REPLACE `tails[pos]` with `num`.
3. The answer is `tails.length` after processing every element.

**Why Template B is correct despite `tails` not being an actual subsequence:** `tails[k]` only needs to track the SMALLEST ending value achievable for length `k+1` — replacing a larger ending value with a smaller one at the same length can only help FUTURE elements extend a chain, never hurt. The final LENGTH of `tails` is exactly the LIS length, even though the actual VALUES in `tails` may not form a real subsequence of the input.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="tails array evolving as elements are processed, showing a replacement when a smaller ending value is found for an existing length">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [10, 9, 2, 5, 3, 7, 101, 18]</text>
    <text x="10" y="45">after 10: tails=[10]; after 9: tails=[9] (replace, smaller ending for length 1)</text>
    <text x="10" y="65">after 2: tails=[2]; after 5: tails=[2,5]; after 3: tails=[2,3] (replace 5)</text>
    <text x="10" y="85">after 7: tails=[2,3,7]; after 101: tails=[2,3,7,101]; after 18: tails=[2,3,7,18]</text>
    <rect x="10" y="105" width="240" height="24" fill="#3fb950"/><text x="130" y="122" fill="#0d1117" text-anchor="middle" font-size="10">final length = 4</text>
  </g>
</svg>

`tails` always stays sorted, and its length at the end is the LIS length, even though `tails` itself may not be a real subsequence.

## 5. Runnable example

```java
// LongestIncreasingSubsequenceTemplate.java
import java.util.*;

public class LongestIncreasingSubsequenceTemplate {

    // Template A: O(n^2) DP.
    static int lisDP(int[] nums) {
        int n = nums.length;
        int[] dp = new int[n];
        Arrays.fill(dp, 1);
        int maxLen = 1;
        for (int i = 1; i < n; i++) {
            for (int j = 0; j < i; j++) {
                if (nums[j] < nums[i]) dp[i] = Math.max(dp[i], dp[j] + 1);
            }
            maxLen = Math.max(maxLen, dp[i]);
        }
        return maxLen;
    }

    // Template B: O(n log n) patience sorting with binary search.
    static int lisPatience(int[] nums) {
        List<Integer> tails = new ArrayList<>();
        for (int num : nums) {
            int pos = Collections.binarySearch(tails, num);
            if (pos < 0) pos = -(pos + 1); // lower bound
            if (pos == tails.size()) {
                tails.add(num);
            } else {
                tails.set(pos, num);
            }
        }
        return tails.size();
    }

    public static void main(String[] args) {
        int[] nums = {10, 9, 2, 5, 3, 7, 101, 18};
        System.out.println(lisDP(nums));
        // 4
        System.out.println(lisPatience(nums));
        // 4
    }
}
```

**How to run:** `java LongestIncreasingSubsequenceTemplate.java`

## 6. Walkthrough

1. `lisDP` fills an array of size `8`, each cell scanning all earlier compatible elements, giving `maxLen = 4`.
2. `lisPatience` processes the same input, maintaining `tails` as shown in the diagram, ending with `tails = [2,3,7,18]`, length `4`.
3. Both agree on the answer `4`, confirming the faster technique computes the identical LENGTH.
4. Tracing `lisPatience`'s replacements shows `9` replacing `10` (both length-1 endings, `9` is smaller and thus more useful for future extensions), and `3` replacing `5` (both length-2 endings, same logic).
5. This template applies directly to Longest Increasing Subsequence itself; other problems in this section (with more complex compatibility rules) generally need Template A instead.

## 7. Gotchas & takeaways

> Gotcha: `tails` after patience sorting is NOT necessarily a valid subsequence of the original array (in this example, `[2,3,7,18]` happens to be, but this is not guaranteed in general) — never use `tails`' final contents as "the answer subsequence," only its LENGTH.

- O(n^2) DP: flexible, handles any compatibility rule, and supports reconstruction/counting with extra bookkeeping.
- O(n log n) patience sorting: much faster, but LENGTH-ONLY, and strictly requires the simple "greater than" (or "greater than or equal," with a small binary-search tweak) compatibility rule.
- Java's `Collections.binarySearch` returns `-(insertion point) - 1` when the exact value is not found — the `pos = -(pos + 1)` line converts this back into the correct insertion index (the "lower bound").
