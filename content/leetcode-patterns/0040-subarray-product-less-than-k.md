---
card: leetcode-patterns
gi: 40
slug: subarray-product-less-than-k
title: Subarray Product Less Than K
---

## 1. What it is

Given an array of positive integers `nums` and an integer `k`, return the number of contiguous subarrays where the product of all elements is strictly less than `k`. Example: `nums = [10, 5, 2, 6]`, `k = 100` → answer `8` (subarrays: `[10]`, `[5]`, `[2]`, `[6]`, `[10,5]`, `[5,2]`, `[2,6]`, `[5,2,6]`).

## 2. Why & when

The condition "product < k" shrinks or grows predictably as elements are added or removed (since all values are positive, multiplying only increases the product), so it is sliding window. The twist is that the question asks for a **count** of valid subarrays, not just the longest one — this needs a small counting trick on top of the usual window mechanics.

## 3. Core concept

**Key idea:** for a valid window ending at `right`, every subarray that starts anywhere from `left` to `right` (and ends at `right`) is also valid, because removing elements from the front of a valid window (all positive) only decreases the product further. So the number of new valid subarrays added when `right` advances is exactly `right - left + 1`.

**Steps:**
1. If `k <= 1`, return `0` immediately (no product of positive integers can be less than 1 or less than a non-positive number).
2. Set `left = 0`, `product = 1`, `count = 0`.
3. For each index `right` from 0 to `length - 1`:
   - Multiply `product *= nums[right]`.
   - While `product >= k`: divide `product /= nums[left]`; `left++`.
   - Add `right - left + 1` to `count` (every subarray ending at `right` and starting between `left` and `right` is valid).
4. Return `count`.

**Why it is correct:** once the window `[left, right]` is valid, every suffix of it that still ends at `right` — i.e., starting at any index from `left` to `right` — is also valid, since a shorter product with the same positive factors removed is smaller. Counting `right - left + 1` new subarrays at each step avoids re-enumerating them individually, keeping the whole scan O(n).

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Subarray product less than k counting subarrays ending at right">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">nums = [10, 5, 2, 6], k = 100</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="100" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="140" y="40" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle">10</text>
    <text x="80" y="60" fill="#e6edf3" text-anchor="middle">5</text>
    <text x="120" y="60" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="160" y="60" fill="#e6edf3" text-anchor="middle">6</text>
    <text x="20" y="95" fill="#8b949e">window [1,3] = [5,2,6], product=60 &lt; 100 -&gt; valid</text>
    <text x="20" y="118" fill="#8b949e">new subarrays ending at 3: [6],[2,6],[5,2,6] -&gt; add (3-1+1)=3 to count</text>
  </g>
</svg>

Every valid window contributes `right - left + 1` new subarrays — all the suffixes ending at `right`.

## 5. Runnable example

```java
// SubarrayProductLessThanK.java
public class SubarrayProductLessThanK {

    // Level 1 -- Brute force: check every subarray's product directly.
    // O(n^2) time, O(1) space.
    static int bruteForce(int[] nums, int k) {
        int count = 0;
        for (int i = 0; i < nums.length; i++) {
            long product = 1;
            for (int j = i; j < nums.length; j++) {
                product *= nums[j];
                if (product < k) count++;
                else break;
            }
        }
        return count;
    }

    // KEY INSIGHT: once a window is valid, every subarray ending at right
    // and starting anywhere from left to right is also valid -- counting
    // (right - left + 1) new subarrays per step avoids enumerating them.

    // Level 2 -- Optimal: sliding window with a counting trick. O(n) time,
    // O(1) space.
    public static int numSubarrayProductLessThanK(int[] nums, int k) {
        if (k <= 1) return 0;
        long product = 1;
        int left = 0, count = 0;
        for (int right = 0; right < nums.length; right++) {
            product *= nums[right];
            while (product >= k) {
                product /= nums[left];
                left++;
            }
            count += right - left + 1;
        }
        return count;
    }

    // Level 3 -- Hardened: k == 1 (or less) returns 0 immediately, since
    // no product of positive integers can be strictly less than 1.
    static int hardened(int[] nums, int k) {
        if (nums == null) throw new IllegalArgumentException("nums must not be null");
        return numSubarrayProductLessThanK(nums, k);
    }

    public static void main(String[] args) {
        int[] nums = {10, 5, 2, 6};
        System.out.println("brute force: " + bruteForce(nums, 100));
        System.out.println("optimal:     " + numSubarrayProductLessThanK(nums, 100));
        System.out.println("k == 1:      " + hardened(nums, 1));
    }
}
```

How to run: save as `SubarrayProductLessThanK.java`, then run `java SubarrayProductLessThanK.java`.

## 6. Walkthrough

Dry run of `numSubarrayProductLessThanK({10, 5, 2, 6}, k = 100)`:

| right | nums[right] | product | shrink? | left | count += | count total |
|---|---|---|---|---|---|---|
| 0 | 10 | 10 | no | 0 | 1 | 1 |
| 1 | 5 | 50 | no | 0 | 2 | 3 |
| 2 | 2 | 100 | yes: /10 -> 10, left=1 | 1 | 2 | 5 |
| 3 | 6 | 60 | no | 1 | 3 | 8 |

Final answer: `8`. Time complexity: O(n). Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: forgetting the `k <= 1` early return causes a division-by-product bug or an incorrect count, since a window can never be "valid" when `k <= 1` but the loop would still try to shrink indefinitely without a base case.

- The "count subarrays ending at right" trick (`right - left + 1`) generalizes to any sliding-window counting problem where validity is monotonic in window size.
- Related problems: Minimum Size Subarray Sum, Count Number of Nice Subarrays, Binary Subarrays With Sum.
