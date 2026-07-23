---
card: leetcode-patterns
gi: 252
slug: split-array-largest-sum
title: Split Array Largest Sum
---

## 1. What it is

Given an array `nums` and an integer `k`, split `nums` into `k` non-empty CONTIGUOUS subarrays, minimizing the LARGEST sum among the subarrays. Return that minimized largest sum. Example: `nums = [7,2,5,10,8]`, `k = 2` → `18` (split as `[7,2,5]` and `[10,8]`; sums `14` and `18`; the largest, `18`, is the smallest possible largest-sum over all valid splits).

## 2. Why & when

This is Capacity To Ship Packages Within D Days wearing yet another costume: the "largest sum allowed per subarray" plays the role of ship capacity, and "number of subarrays needed" plays the role of days used. A bigger allowed sum always needs fewer or equal subarrays — monotonic, and ready for binary search on the answer. Use this shape whenever a problem asks to MINIMIZE THE MAXIMUM of some quantity across a fixed number of groups.

## 3. Core concept

**Key idea:** define `subarraysNeeded(limit)`: greedily walk `nums`, adding each element to the current subarray's running sum if it fits under `limit`; when it doesn't fit, start a new subarray. This function is monotonic — decreasing as `limit` increases. Binary search over candidate limits for the smallest one where `subarraysNeeded(limit) <= k`.

**Steps:**
1. Set `lo = max(nums)` (any subarray must fit at least the single largest element), `hi = sum(nums)` (one subarray holding everything always "fits," needing only 1 subarray).
2. While `lo < hi`: compute `mid = lo + (hi - lo) / 2`.
3. Compute `count = subarraysNeeded(nums, mid)` via the greedy simulation.
4. If `count <= k`, limit `mid` works, and a smaller limit might also work: set `hi = mid`.
5. Otherwise, `mid` is too small (needs too many subarrays): set `lo = mid + 1`.
6. When the loop ends, `lo == hi` is the minimized largest sum.

**Why it is correct:** `subarraysNeeded(limit)` strictly decreases (or stays the same) as `limit` increases, exactly like the days-needed function in the shipping problem — a bigger allowed sum per subarray can only merge more elements together, never require more subarrays. This monotonic relationship means binary search finds the exact smallest limit where the split still fits within `k` subarrays.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Array 7 2 5 10 8, k=2, limit 18 splits into 7,2,5 and 10,8, needing exactly 2 subarrays">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [7,2,5,10,8], k = 2</text>
    <text x="10" y="45">limit 18: group1=[7,2,5]=14, group2=[10,8]=18 -&gt; 2 groups, fits</text>
    <rect x="10" y="60" width="30" height="24" fill="#161b22" stroke="#f85149"/><text x="25" y="77" text-anchor="middle" font-size="9">17</text>
    <rect x="40" y="60" width="30" height="24" fill="#3fb950"/><text x="55" y="77" fill="#0d1117" text-anchor="middle" font-size="9">18</text>
    <text x="10" y="110">limit 17: group1=[7,2,5]=14, next elem 10 doesn't fit alone with... needs 3 groups (too many)</text>
    <text x="10" y="135">minimized largest sum: 18</text>
  </g>
</svg>

A larger allowed limit per group always needs fewer or equal groups; the search finds the smallest limit that still fits within `k` groups.

## 5. Runnable example

```java
// SplitArrayLargestSum.java
public class SplitArrayLargestSum {

    // Level 1 -- Brute force: try every way to place k-1 split points
    // among the array's n-1 possible gaps, computing the largest
    // subarray sum for each split, and keep the minimum. Correct, but
    // O(C(n-1, k-1)) splits tried -- exponential in the worst case.

    // KEY INSIGHT: subarraysNeeded(limit) is monotonically
    // non-increasing in limit, exactly like the shipping-capacity
    // problem, so binary search over candidate limits finds the
    // minimized largest sum in O(n log(sum(nums))) instead.

    // Level 2 -- Optimal: binary search on the answer.
    static int splitArray(int[] nums, int k) {
        int lo = 0, hi = 0;
        for (int num : nums) {
            lo = Math.max(lo, num);
            hi += num;
        }

        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (subarraysNeeded(nums, mid) <= k) hi = mid;
            else lo = mid + 1;
        }
        return lo;
    }

    static int subarraysNeeded(int[] nums, int limit) {
        int count = 1, currentSum = 0;
        for (int num : nums) {
            if (currentSum + num > limit) {
                count++;
                currentSum = 0;
            }
            currentSum += num;
        }
        return count;
    }

    // Level 3 -- Hardened: lo starts at max(nums), not 0, since any
    // limit smaller than the largest single element makes the greedy
    // simulation impossible to satisfy for that element alone.

    public static void main(String[] args) {
        System.out.println(splitArray(new int[]{7, 2, 5, 10, 8}, 2));
        // 18
    }
}
```

**How to run:** `java SplitArrayLargestSum.java`

## 6. Walkthrough

Trace `splitArray(nums, 2)` on `nums = [7,2,5,10,8]`, `lo=10, hi=32`:

| lo | hi | mid | subarraysNeeded(mid) | <= 2? | action |
|---|---|---|---|---|---|
| 10 | 32 | 21 | 2 | yes | hi = 21 |
| 10 | 21 | 15 | 3 | no | lo = 16 |
| 16 | 21 | 18 | 2 | yes | hi = 18 |
| 16 | 18 | 17 | 3 | no | lo = 18 |
| 18 | 18 | — | — | loop ends | return 18 |

The minimized largest sum `18` matches the expected answer, achieved by splitting into `[7,2,5]` (sum 14) and `[10,8]` (sum 18). Time complexity is O(n · log(sum(nums))). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: this problem, Koko Eating Bananas, and Capacity To Ship Packages Within D Days are structurally identical (binary search on a monotonic "resource limit," checked with a greedy simulation) — recognizing this family lets you write the binary search skeleton from memory and focus entirely on getting the `subarraysNeeded`-equivalent function right for the specific problem.

- The greedy simulation (`subarraysNeeded`) is itself optimal for a FIXED limit: always filling the current group as much as possible before starting a new one never uses more groups than necessary.
- `lo = max(nums)` is a required starting bound, not just an optimization — any smaller limit makes the simulation undefined for the largest element.
- Related problems: Capacity To Ship Packages Within D Days (identical shape, different simulation function), Koko Eating Bananas (same shape, a per-item ceiling-division simulation).
