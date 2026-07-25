---
card: leetcode-patterns
gi: 401
slug: minimum-number-of-removals-to-make-mountain-array
title: Minimum Number of Removals to Make Mountain Array
---

## 1. What it is

A MOUNTAIN ARRAY strictly increases to a single peak, then strictly decreases, with at least one element on each side of the peak. Given an array `nums`, return the MINIMUM number of elements to remove so the remaining elements form a mountain array. Example: `nums = [2,1,1,5,6,2,3,1]` → `3` (keep `[1,5,6,3,1]`).

## 2. Why & when

This problem runs LIS TWICE — once left-to-right for the increasing "uphill" side, once right-to-left for the decreasing "downhill" side — and combines the two results at every possible PEAK position. Use this shape whenever a problem needs to find the best split point between an increasing prefix and a decreasing suffix, since computing both LIS DIRECTIONS separately and combining them at each candidate peak is a general technique for "peak-shaped" chain problems.

## 3. Core concept

**Key idea:** for every index `i`, compute `lis[i]` = the length of the longest strictly increasing subsequence ENDING at `i` (looking left), and `rds[i]` = the length of the longest strictly decreasing subsequence STARTING at `i` (looking right). If `i` can be a valid peak (`lis[i] > 1` and `rds[i] > 1`, meaning there is at least one element on each side), the mountain centered at `i` has length `lis[i] + rds[i] - 1` (subtracting 1 since `i` itself is counted in both).

**Steps:**
1. Compute `lis[i]` for every `i`, using the standard LIS DP scanning `j < i`.
2. Compute `rds[i]` for every `i`, using the SAME LIS DP idea but scanning `j > i` with `nums[j] < nums[i]` (equivalent to running LIS on the reversed array).
3. For every `i` where `lis[i] > 1` AND `rds[i] > 1`, compute the candidate mountain length `lis[i] + rds[i] - 1`. Track the maximum such length.
4. Return `nums.length - maxMountainLength`.

**Why it is correct:** any valid mountain array has exactly one peak; removing every element NOT on the increasing run leading up to that peak, or the decreasing run leading away from it, leaves the LONGEST possible mountain centered there. Trying EVERY index as a candidate peak, and combining the best increasing run ending there with the best decreasing run starting there, is guaranteed to find the globally longest possible mountain, since the true optimal mountain's peak is one of these candidates.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="index 4 combining its longest increasing run of length 3 and longest decreasing run of length 3 into a mountain of length 5">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums=[2,1,1,5,6,2,3,1]; at i=4 (value 6)</text>
    <text x="10" y="45">lis[4] = 3 (e.g. 1,5,6); rds[4] = 3 (e.g. 6,3,1)</text>
    <rect x="10" y="65" width="260" height="24" fill="#3fb950"/><text x="140" y="82" fill="#0d1117" text-anchor="middle" font-size="10">mountain length = 3 + 3 - 1 = 5</text>
  </g>
</svg>

Each index's best uphill and downhill runs combine (minus the shared peak) into a candidate mountain length.

## 5. Runnable example

```java
// MinimumNumberOfRemovalsToMakeMountainArray.java
public class MinimumNumberOfRemovalsToMakeMountainArray {

    // KEY INSIGHT: run LIS in both directions -- increasing ending at
    // i, decreasing starting at i -- then combine at every candidate
    // peak, subtracting 1 for the shared peak element.

    static int minimumMountainRemovals(int[] nums) {
        int n = nums.length;
        int[] lis = new int[n];
        int[] rds = new int[n];
        java.util.Arrays.fill(lis, 1);
        java.util.Arrays.fill(rds, 1);

        for (int i = 0; i < n; i++) {
            for (int j = 0; j < i; j++) {
                if (nums[j] < nums[i]) lis[i] = Math.max(lis[i], lis[j] + 1);
            }
        }
        for (int i = n - 1; i >= 0; i--) {
            for (int j = i + 1; j < n; j++) {
                if (nums[j] < nums[i]) rds[i] = Math.max(rds[i], rds[j] + 1);
            }
        }

        int maxMountain = 0;
        for (int i = 0; i < n; i++) {
            if (lis[i] > 1 && rds[i] > 1) {
                maxMountain = Math.max(maxMountain, lis[i] + rds[i] - 1);
            }
        }
        return n - maxMountain;
    }

    public static void main(String[] args) {
        System.out.println(minimumMountainRemovals(new int[]{2, 1, 1, 5, 6, 2, 3, 1}));
        // 3
        System.out.println(minimumMountainRemovals(new int[]{4, 3, 2, 1, 1, 2, 3, 1}));
        // 4
    }
}
```

**How to run:** `java MinimumNumberOfRemovalsToMakeMountainArray.java`

## 6. Walkthrough

Trace key indices for `minimumMountainRemovals([2,1,1,5,6,2,3,1])`, `n=8`:

| i | value | lis[i] | rds[i] | valid peak? | mountain length |
|---|---|---|---|---|---|
| 3 | 5 | 2 | 3 | yes | 4 |
| 4 | 6 | 3 | 3 | yes | 5 |
| 6 | 3 | 3 | 2 | yes | 4 |

`maxMountain = 5` (at `i=4`). Removals: `8 - 5 = 3`, matching the expected answer. Time complexity is O(n^2) for both LIS passes. Space is O(n).

## 7. Gotchas & takeaways

> Gotcha: forgetting the `lis[i] > 1 && rds[i] > 1` guard would allow indices at the very START or END of the array (where one side is empty) to be counted as valid peaks — a true mountain needs AT LEAST ONE element on each side of the peak, so a peak with an empty uphill or downhill side is invalid.

- Running the SAME DP technique in both directions (left-to-right and right-to-left) and combining the results at every position is a general technique for "peak" or "valley" shaped problems.
- The `-1` in `lis[i] + rds[i] - 1` corrects for double-counting the peak element itself, which appears in both `lis[i]` and `rds[i]`.
- Related problems: Longest Increasing Subsequence (the single-direction building block this problem runs twice), Longest Arithmetic Subsequence (a different LIS variant, but also built from a per-position DP scanning all earlier compatible elements).
