---
card: leetcode-patterns
gi: 31
slug: maximum-average-subarray-i
title: Maximum Average Subarray I
---

## 1. What it is

Given an integer array `nums` and an integer `k`, find the contiguous subarray of length exactly `k` that has the maximum average value, and return that average. Example: `nums = [1, 12, -5, -6, 50, 3]`, `k = 4` → the subarray `[12, -5, -6, 50]` has sum `51`, average `12.75`, the maximum.

## 2. Why & when

The window size is fixed at `k`, which makes this the simplest possible sliding window: no shrink condition to check, just slide a window of constant width across the array, updating its sum incrementally.

## 3. Core concept

**Key idea:** the sum of a window sliding by one position can be updated in O(1) — add the new right element, subtract the element that just left the window on the left — instead of re-summing the whole window from scratch.

**Steps:**
1. Compute the sum of the first `k` elements; this is the initial window sum and the initial best.
2. For each position from `k` to `length - 1`: update `sum = sum + nums[i] - nums[i - k]` (add the new element, remove the one that fell out of the window).
3. Track the maximum sum seen.
4. Return `maxSum / (double) k`.

**Why it is correct:** for a fixed-size window, sliding it by one position always adds exactly one new element and removes exactly one old element — the element now `k` positions behind the current right edge. Tracking the running sum this way avoids the O(k) cost of re-summing every window from scratch, which would make the whole scan O(n·k) instead of O(n).

## 4. Diagram

<svg viewBox="0 0 700 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Fixed size sliding window updating sum incrementally">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">nums = [1, 12, -5, -6, 50, 3], k = 4</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="100" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="140" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="180" y="40" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="80" y="60" fill="#e6edf3" text-anchor="middle">12</text>
    <text x="120" y="60" fill="#e6edf3" text-anchor="middle">-5</text>
    <text x="160" y="60" fill="#e6edf3" text-anchor="middle">-6</text>
    <text x="200" y="60" fill="#e6edf3" text-anchor="middle">50</text>
    <text x="20" y="95" fill="#8b949e">window0 sum = 1+12-5-6 = 2</text>
    <text x="20" y="118" fill="#8b949e">slide: sum = 2 + 50 - 1 = 51 -&gt; new best</text>
  </g>
</svg>

Sliding the fixed-width window by one adds the new right element and subtracts the element that exits on the left.

## 5. Runnable example

```java
// MaxAverageSubarray.java
public class MaxAverageSubarray {

    // Level 1 -- Brute force: recompute the sum of each length-k window
    // from scratch. O(n * k) time, O(1) space.
    static double bruteForce(int[] nums, int k) {
        int maxSum = Integer.MIN_VALUE;
        for (int i = 0; i + k <= nums.length; i++) {
            int sum = 0;
            for (int j = i; j < i + k; j++) sum += nums[j];
            maxSum = Math.max(maxSum, sum);
        }
        return maxSum / (double) k;
    }

    // KEY INSIGHT: a fixed-size window's sum can be updated in O(1) per
    // slide by adding the new element and removing the one that fell out
    // -- no need to re-sum the whole window each time.

    // Level 2 -- Optimal: fixed-size sliding window. O(n) time, O(1) space.
    public static double findMaxAverage(int[] nums, int k) {
        int sum = 0;
        for (int i = 0; i < k; i++) sum += nums[i];
        int maxSum = sum;
        for (int i = k; i < nums.length; i++) {
            sum += nums[i] - nums[i - k];
            maxSum = Math.max(maxSum, sum);
        }
        return maxSum / (double) k;
    }

    // Level 3 -- Hardened: k equal to the array's full length just
    // computes one window's average, since the second loop never runs.
    static double hardened(int[] nums, int k) {
        if (nums == null || k <= 0 || k > nums.length) {
            throw new IllegalArgumentException("invalid k for this array");
        }
        return findMaxAverage(nums, k);
    }

    public static void main(String[] args) {
        int[] nums = {1, 12, -5, -6, 50, 3};
        System.out.println("brute force: " + bruteForce(nums, 4));
        System.out.println("optimal:     " + findMaxAverage(nums, 4));
        System.out.println("k == length: " + hardened(new int[] {5, 5}, 2));
    }
}
```

How to run: save as `MaxAverageSubarray.java`, then run `java MaxAverageSubarray.java`.

## 6. Walkthrough

Dry run of `findMaxAverage({1, 12, -5, -6, 50, 3}, k = 4)`:

| step | window | sum | maxSum |
|---|---|---|---|
| init | [1,12,-5,-6] | 2 | 2 |
| i=4 | [12,-5,-6,50] | 2 + 50 - 1 = 51 | 51 |
| i=5 | [-5,-6,50,3] | 51 + 3 - 12 = 42 | 51 |

Final `maxSum = 51`, average `51 / 4 = 12.75`. Time complexity: O(n), one pass after the initial window sum. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: dividing by `k` using integer division (`maxSum / k` instead of `maxSum / (double) k`) truncates the result — always cast to `double` before dividing when the answer can be fractional.

- Fixed-size windows are the simplest sliding-window case: no shrink condition, just an O(1) update per slide.
- Related problems: Sliding Window Maximum (fixed size, but tracking the max element needs a monotonic deque, not just a running sum), Minimum Size Subarray Sum (variable-size window).
