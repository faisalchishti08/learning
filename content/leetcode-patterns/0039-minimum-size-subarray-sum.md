---
card: leetcode-patterns
gi: 39
slug: minimum-size-subarray-sum
title: Minimum Size Subarray Sum
---

## 1. What it is

Given an array of positive integers `nums` and a positive integer `target`, find the length of the shortest contiguous subarray whose sum is greater than or equal to `target`. Return `0` if no such subarray exists. Example: `nums = [2, 3, 1, 2, 4, 3]`, `target = 7` → answer `2`, from the subarray `[4, 3]`.

## 2. Why & when

"Shortest subarray with sum at least target" is the "shortest window" variant of sliding window — the opposite goal of the "longest window" problems seen so far, but the same mechanics: expand `right` to grow the sum, shrink `left` as much as possible once the condition is met, recording the minimum length along the way.

## 3. Core concept

**Key idea:** once the window's sum reaches `target`, shrinking from the left can only help (a shorter window is always preferred if it still meets the target) — so shrink as much as possible before letting `right` expand again.

**Steps:**
1. Set `left = 0`, `sum = 0`, `best = Integer.MAX_VALUE` (a sentinel for "no valid window found yet").
2. For each index `right` from 0 to `length - 1`:
   - Add `nums[right]` to `sum`.
   - While `sum >= target`: update `best = min(best, right - left + 1)`; then subtract `nums[left]` from `sum` and `left++` (try to shrink further).
3. Return `best` if it was updated, else `0`.

**Why it is correct:** because all values are positive, removing an element from the left of a valid window can only decrease its sum, never increase it — so shrinking greedily while the window stays valid always finds the shortest valid window that starts furthest right for a given `right`. Recording `best` *inside* the shrink loop (not after) is what captures every shrink step's length, not just the first or last.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Minimum size subarray sum shrinking to shortest valid window">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">nums = [2, 3, 1, 2, 4, 3], target = 7</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="100" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="140" y="40" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="80" y="60" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="120" y="60" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="160" y="60" fill="#e6edf3" text-anchor="middle">4</text>
    <text x="20" y="95" fill="#8b949e">window [3,1,2,4] sum=10 &gt;= 7 -&gt; record length 4, shrink</text>
    <text x="20" y="118" fill="#8b949e">remove 3: [1,2,4] sum=7 &gt;= 7 -&gt; record length 3, shrink further</text>
  </g>
</svg>

Once the window's sum meets the target, it keeps shrinking from the left, recording each shorter valid length, until it breaks.

## 5. Runnable example

```java
// MinSizeSubarraySum.java
public class MinSizeSubarraySum {

    // Level 1 -- Brute force: check every subarray's sum directly. O(n^2)
    // time, O(1) space.
    static int bruteForce(int[] nums, int target) {
        int best = Integer.MAX_VALUE;
        for (int i = 0; i < nums.length; i++) {
            int sum = 0;
            for (int j = i; j < nums.length; j++) {
                sum += nums[j];
                if (sum >= target) {
                    best = Math.min(best, j - i + 1);
                    break;
                }
            }
        }
        return best == Integer.MAX_VALUE ? 0 : best;
    }

    // KEY INSIGHT: since all values are positive, shrinking a valid
    // window from the left can only reduce its sum -- so greedily
    // shrinking while still valid always finds the shortest window ending
    // at each right, in a single linear pass.

    // Level 2 -- Optimal: sliding window, shrink-while-valid. O(n) time,
    // O(1) space.
    public static int minSubArrayLen(int target, int[] nums) {
        int left = 0, sum = 0, best = Integer.MAX_VALUE;
        for (int right = 0; right < nums.length; right++) {
            sum += nums[right];
            while (sum >= target) {
                best = Math.min(best, right - left + 1);
                sum -= nums[left];
                left++;
            }
        }
        return best == Integer.MAX_VALUE ? 0 : best;
    }

    // Level 3 -- Hardened: a target greater than the sum of the entire
    // array correctly returns 0, since the while loop's condition
    // (sum >= target) never triggers.
    static int hardened(int target, int[] nums) {
        if (nums == null || target <= 0) throw new IllegalArgumentException("invalid input");
        return minSubArrayLen(target, nums);
    }

    public static void main(String[] args) {
        int[] nums = {2, 3, 1, 2, 4, 3};
        System.out.println("brute force: " + bruteForce(nums, 7));
        System.out.println("optimal:     " + minSubArrayLen(7, nums));
        System.out.println("impossible:  " + hardened(100, nums));
    }
}
```

How to run: save as `MinSizeSubarraySum.java`, then run `java MinSizeSubarraySum.java`.

## 6. Walkthrough

Dry run of `minSubArrayLen(7, {2, 3, 1, 2, 4, 3})`:

| right | nums[right] | sum | shrink steps | best after |
|---|---|---|---|---|
| 0 | 2 | 2 | none (2<7) | MAX |
| 1 | 3 | 5 | none (5<7) | MAX |
| 2 | 1 | 6 | none (6<7) | MAX |
| 3 | 2 | 8 | record len 4; remove 2, sum=6, left=1 (6<7, stop) | 4 |
| 4 | 4 | 10 | record len 4; remove 3, sum=7, left=2, record len 3; remove 1, sum=6, left=3 (6<7, stop) | 3 |
| 5 | 3 | 9 | record len 3; remove 2, sum=7, left=4, record len 2; remove 4, sum=3, left=5 (3<7, stop) | 2 |

Final answer: `2`, from the window `[4, 3]` (indices 4-5). Time complexity: O(n). Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: this shrink-while-valid trick relies on all values being **positive** — if the array could contain negative numbers, removing an element from the window would not reliably decrease the sum, and the greedy shrink would no longer be correct (a different technique, like a prefix-sum plus a monotonic deque, would be needed instead).

- Record the best length *inside* the shrink loop for shortest-window problems, versus *after* the shrink loop for longest-window problems — this is the one-line difference between the two template variants.
- Related problems: Fruit Into Baskets, Longest Repeating Character Replacement, Subarray Product Less Than K.
