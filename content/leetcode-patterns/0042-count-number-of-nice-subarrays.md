---
card: leetcode-patterns
gi: 42
slug: count-number-of-nice-subarrays
title: Count Number of Nice Subarrays
---

## 1. What it is

Given an array `nums` and an integer `k`, a subarray is "nice" if it contains exactly `k` odd numbers. Return the number of nice subarrays. Example: `nums = [1, 1, 2, 1, 1]`, `k = 3` → answer `2`.

## 2. Why & when

"Exactly k" is awkward for a direct sliding window (window validity is not simply monotonic the way "at most k" is), but it factors neatly into two "at most" sliding windows: `exactly(k) = atMost(k) - atMost(k - 1)`. This is the same counting trick as Subarray Product Less Than K, applied twice and subtracted.

## 3. Core concept

**Key idea:** the number of subarrays with *exactly* `k` odd numbers equals the number with *at most* `k` odd numbers, minus the number with *at most* `k - 1` odd numbers — every subarray with more than `k` odds is excluded from both, and every subarray with fewer than `k` odds is excluded from the subtraction cleanly.

**Steps:**
1. Write a helper `atMostK(nums, k)` that counts subarrays with at most `k` odd numbers, using the same sliding-window counting trick as Subarray Product Less Than K: track a running count of odd numbers in the window, shrink when it exceeds `k`, and add `right - left + 1` at each step.
2. Return `atMostK(nums, k) - atMostK(nums, k - 1)`.

**Why it is correct:** the set of subarrays counted by `atMostK(nums, k)` is exactly the union of subarrays with 0, 1, …, k odd numbers. The set counted by `atMostK(nums, k - 1)` is the same union up to `k - 1`. Their difference is exactly the subarrays with precisely `k` odd numbers — no more, no less. This "exactly = atMost(k) − atMost(k−1)" transform works for any monotonic window condition, turning an "exactly" counting problem into two "at most" ones.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Count nice subarrays via atMost k minus atMost k minus 1">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">nums = [1, 1, 2, 1, 1], k = 3</text>
    <text x="20" y="55" fill="#8b949e">atMost(3): every subarray with 0,1,2, or 3 odd numbers -&gt; count = 14</text>
    <text x="20" y="80" fill="#8b949e">atMost(2): every subarray with 0,1, or 2 odd numbers -&gt; count = 12</text>
    <text x="20" y="105" fill="#79c0ff">exactly(3) = atMost(3) - atMost(2) = 14 - 12 = 2</text>
  </g>
</svg>

Subtracting "at most k-1" from "at most k" isolates exactly the subarrays with precisely k odd numbers.

## 5. Runnable example

```java
// CountNiceSubarrays.java
public class CountNiceSubarrays {

    // Level 1 -- Brute force: check every subarray, counting its odd
    // numbers directly. O(n^2) time, O(1) space.
    static int bruteForce(int[] nums, int k) {
        int count = 0;
        for (int i = 0; i < nums.length; i++) {
            int odds = 0;
            for (int j = i; j < nums.length; j++) {
                if (nums[j] % 2 == 1) odds++;
                if (odds == k) count++;
                if (odds > k) break;
            }
        }
        return count;
    }

    // KEY INSIGHT: "exactly k odd numbers" splits into
    // atMost(k) - atMost(k-1), turning an awkward "exactly" condition into
    // two easy monotonic "at most" sliding-window counts.

    // Level 2 -- Optimal: two atMost sliding windows. O(n) time, O(1) space.
    private static int atMostK(int[] nums, int k) {
        if (k < 0) return 0;
        int left = 0, odds = 0, count = 0;
        for (int right = 0; right < nums.length; right++) {
            if (nums[right] % 2 == 1) odds++;
            while (odds > k) {
                if (nums[left] % 2 == 1) odds--;
                left++;
            }
            count += right - left + 1;
        }
        return count;
    }

    public static int numberOfSubarrays(int[] nums, int k) {
        return atMostK(nums, k) - atMostK(nums, k - 1);
    }

    // Level 3 -- Hardened: k == 0 correctly counts only subarrays made
    // entirely of even numbers, since atMostK(nums, -1) returns 0.
    static int hardened(int[] nums, int k) {
        if (nums == null || k < 0) throw new IllegalArgumentException("invalid input");
        return numberOfSubarrays(nums, k);
    }

    public static void main(String[] args) {
        int[] nums = {1, 1, 2, 1, 1};
        System.out.println("brute force: " + bruteForce(nums, 3));
        System.out.println("optimal:     " + numberOfSubarrays(nums, 3));
        System.out.println("k == 0:      " + hardened(new int[] {2, 4, 6}, 0));
    }
}
```

How to run: save as `CountNiceSubarrays.java`, then run `java CountNiceSubarrays.java`.

## 6. Walkthrough

Dry run of `atMostK({1, 1, 2, 1, 1}, k = 3)`:

| right | nums[right] | odds | shrink? | left | count += | total |
|---|---|---|---|---|---|---|
| 0 | 1 | 1 | no | 0 | 1 | 1 |
| 1 | 1 | 2 | no | 0 | 2 | 3 |
| 2 | 2 | 2 | no | 0 | 3 | 6 |
| 3 | 1 | 3 | no (3<=3) | 0 | 4 | 10 |
| 4 | 1 | 4 | yes: remove nums[0]=1, odds=3, left=1 | 1 | 4 | 14 |

`atMostK(nums, 3) = 14`. Dry run of `atMostK({1, 1, 2, 1, 1}, k = 2)`:

| right | nums[right] | odds | shrink? | left | count += | total |
|---|---|---|---|---|---|---|
| 0 | 1 | 1 | no | 0 | 1 | 1 |
| 1 | 1 | 2 | no | 0 | 2 | 3 |
| 2 | 2 | 2 | no | 0 | 3 | 6 |
| 3 | 1 | 3 | yes: remove nums[0]=1, odds=2, left=1 | 1 | 3 | 9 |
| 4 | 1 | 3 | yes: remove nums[1]=1, odds=2, left=2 | 2 | 3 | 12 |

`atMostK(nums, 2) = 12`. Final answer: `numberOfSubarrays = 14 - 12 = 2`, matching the expected result. Time complexity: O(n) for each `atMostK` call, so O(n) overall. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: calling `atMostK(nums, k - 1)` when `k == 0` passes `-1`, which must return `0` directly (no subarray can have at most −1 odd numbers) — the helper's guard clause handles this.

- The `exactly(k) = atMost(k) - atMost(k-1)` transform is a general-purpose trick for any sliding-window counting problem where "at most" is easy but "exactly" is not.
- Related problems: Subarray Product Less Than K, Binary Subarrays With Sum (uses the exact same atMost-minus-atMost transform), Number of Substrings Containing All Three Characters.
