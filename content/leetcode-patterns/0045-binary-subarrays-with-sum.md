---
card: leetcode-patterns
gi: 45
slug: binary-subarrays-with-sum
title: Binary Subarrays With Sum
---

## 1. What it is

Given a binary array `nums` and an integer `goal`, return the number of non-empty contiguous subarrays whose sum equals `goal`. Example: `nums = [1, 0, 1, 0, 1]`, `goal = 2` → answer `4`.

## 2. Why & when

This is Count Number of Nice Subarrays wearing a different costume: "exactly `goal` ones" is the same "exactly k" counting shape, since the array is binary (sum equals the count of `1`s). The same `atMost(goal) - atMost(goal - 1)` transform applies directly.

## 3. Core concept

**Key idea:** for a binary array, the sum of a subarray equals its count of `1`s — so counting subarrays with sum exactly `goal` is identical to counting subarrays with exactly `goal` ones, which reduces to two "at most" sliding-window counts.

**Steps:**
1. Write `atMostGoal(nums, goal)`: a sliding window that counts subarrays with sum at most `goal`, using the same running-sum-and-shrink-and-count-`right-left+1` technique as Subarray Product Less Than K.
2. Return `atMostGoal(nums, goal) - atMostGoal(nums, goal - 1)`.

**Why it is correct:** the same reasoning as Count Number of Nice Subarrays applies — the set of subarrays with sum at most `goal` minus the set with sum at most `goal - 1` leaves exactly the subarrays with sum equal to `goal`. Because the array is binary, "sum" and "count of ones" are the same quantity, so this is a direct instance of the exact-count-via-two-at-most-windows trick, without needing a separate frequency structure.

## 4. Diagram

<svg viewBox="0 0 700 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Binary subarrays with sum via atMost goal minus atMost goal minus 1">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">nums = [1, 0, 1, 0, 1], goal = 2</text>
    <text x="20" y="55" fill="#8b949e">atMost(2): subarrays with sum 0, 1, or 2 -&gt; count = 14</text>
    <text x="20" y="80" fill="#8b949e">atMost(1): subarrays with sum 0 or 1 -&gt; count = 10</text>
    <text x="20" y="105" fill="#79c0ff">exactly(2) = atMost(2) - atMost(1) = 14 - 10 = 4</text>
  </g>
</svg>

Same "at most minus at most" subtraction as Count Number of Nice Subarrays, here applied to a binary array's running sum directly.

## 5. Runnable example

```java
// BinarySubarraysWithSum.java
public class BinarySubarraysWithSum {

    // Level 1 -- Brute force: check every subarray's sum directly.
    // O(n^2) time, O(1) space.
    static int bruteForce(int[] nums, int goal) {
        int count = 0;
        for (int i = 0; i < nums.length; i++) {
            int sum = 0;
            for (int j = i; j < nums.length; j++) {
                sum += nums[j];
                if (sum == goal) count++;
                if (sum > goal) break;
            }
        }
        return count;
    }

    // KEY INSIGHT: for a binary array, sum equals the count of ones, so
    // "exactly goal" reduces to the same atMost(goal) - atMost(goal-1)
    // trick used for counting problems with a monotonic condition.

    // Level 2 -- Optimal: two atMost sliding windows. O(n) time, O(1) space.
    private static int atMostGoal(int[] nums, int goal) {
        if (goal < 0) return 0;
        int left = 0, sum = 0, count = 0;
        for (int right = 0; right < nums.length; right++) {
            sum += nums[right];
            while (sum > goal) {
                sum -= nums[left];
                left++;
            }
            count += right - left + 1;
        }
        return count;
    }

    public static int numSubarraysWithSum(int[] nums, int goal) {
        return atMostGoal(nums, goal) - atMostGoal(nums, goal - 1);
    }

    // Level 3 -- Hardened: goal == 0 correctly counts only subarrays made
    // entirely of zeroes, since atMostGoal(nums, -1) returns 0.
    static int hardened(int[] nums, int goal) {
        if (nums == null || goal < 0) throw new IllegalArgumentException("invalid input");
        return numSubarraysWithSum(nums, goal);
    }

    public static void main(String[] args) {
        int[] nums = {1, 0, 1, 0, 1};
        System.out.println("brute force: " + bruteForce(nums, 2));
        System.out.println("optimal:     " + numSubarraysWithSum(nums, 2));
        System.out.println("goal == 0:   " + hardened(new int[] {0, 0, 1}, 0));
    }
}
```

How to run: save as `BinarySubarraysWithSum.java`, then run `java BinarySubarraysWithSum.java`.

## 6. Walkthrough

Dry run of `atMostGoal({1, 0, 1, 0, 1}, goal = 2)`:

| right | nums[right] | sum | shrink? | left | count += | total |
|---|---|---|---|---|---|---|
| 0 | 1 | 1 | no | 0 | 1 | 1 |
| 1 | 0 | 1 | no | 0 | 2 | 3 |
| 2 | 1 | 2 | no | 0 | 3 | 6 |
| 3 | 0 | 2 | no | 0 | 4 | 10 |
| 4 | 1 | 3 | yes: remove nums[0]=1, sum=2, left=1 | 1 | 4 | 14 |

`atMostGoal(nums, 2) = 14`. A similar trace for `atMostGoal(nums, 1)` (shrinking whenever `sum > 1`) gives `10`. Final answer: `numSubarraysWithSum = 14 - 10 = 4`, matching the expected result. Time complexity: O(n). Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: passing `goal - 1` directly without a `goal < 0` guard in `atMostGoal` breaks when `goal == 0`, since the recursive-feeling call would need to handle `-1` — the guard clause returns `0` immediately for negative targets.

- Recognize "binary array + exact sum" as identical in structure to "exact count of a specific value" — the same subtraction trick applies whenever the target quantity increases monotonically with window size.
- Related problems: Count Number of Nice Subarrays, Subarray Product Less Than K, Subarray Sum Equals K (a related problem, but usually solved with prefix sums and a hash map instead, since general integers make sliding window's monotonicity argument fail).
