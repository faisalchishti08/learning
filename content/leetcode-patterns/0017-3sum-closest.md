---
card: leetcode-patterns
gi: 17
slug: 3sum-closest
title: 3Sum Closest
---

## 1. What it is

Given an integer array `nums` and an integer `target`, find three numbers whose sum is closest to `target`, and return that sum. Assume exactly one closest answer exists. Example: `nums = [-1, 2, 1, -4]`, `target = 1` → the closest sum is `2` (from `-1 + 2 + 1`).

## 2. Why & when

This is 3Sum's skeleton — fix one element, two-pointer the rest — but instead of looking for an *exact* zero sum, you track the *closest* sum seen so far. Same reduction, different stopping/recording rule.

## 3. Core concept

**Key idea:** while scanning with two pointers for a fixed `i`, every sum you compute is a candidate; keep the one whose distance from `target` is smallest, and use the comparison to `target` to decide which pointer to move, exactly like Two Sum II.

**Steps:**
1. Sort `nums`. Initialize `closestSum` to the sum of the first three elements (a valid starting candidate).
2. For each index `i` from 0 to `length - 3`:
   - Set `left = i + 1`, `right = length - 1`.
   - While `left < right`: compute `sum = nums[i] + nums[left] + nums[right]`.
     - If `abs(sum - target) < abs(closestSum - target)`, update `closestSum = sum`.
     - If `sum == target`, you cannot do better — return `target` immediately.
     - If `sum < target`, move `left++` (need a larger sum).
     - Else move `right--` (need a smaller sum).
3. Return `closestSum`.

**Why it is correct:** the two-pointer movement rule is identical to Two Sum II's: an exact match is impossible to improve on, and moving toward the target direction can only bring future sums closer, never systematically worse, because the array is sorted. Recording the best sum seen at every step (not just at a match) is what turns the exact-match search into a closest-match search.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="3Sum Closest tracking best sum while pointers converge">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">sorted nums = [-4, -1, 1, 2], target = 1, i fixed at -4</text>
    <text x="20" y="55" fill="#8b949e">left=1(-1), right=3(2): sum=-4-1+2=-3, |dist|=4 -&gt; closest=-3</text>
    <text x="20" y="80" fill="#8b949e">sum &lt; target -&gt; left++</text>
    <text x="20" y="105" fill="#8b949e">left=2(1), right=3(2): sum=-4+1+2=-1, |dist|=2 -&gt; closest=-1</text>
    <text x="20" y="130" fill="#8b949e">closer to target than before, keep updating as pointers converge</text>
  </g>
</svg>

Every sum computed while the pointers converge is a candidate; the best one seen so far is kept.

## 5. Runnable example

```java
// ThreeSumClosest.java
import java.util.Arrays;

public class ThreeSumClosest {

    // Level 1 -- Brute force: check every triplet directly, tracking the
    // closest sum. O(n^3) time, O(1) space.
    static int bruteForce(int[] nums, int target) {
        int n = nums.length;
        int closest = nums[0] + nums[1] + nums[2];
        for (int i = 0; i < n; i++)
            for (int j = i + 1; j < n; j++)
                for (int k = j + 1; k < n; k++) {
                    int sum = nums[i] + nums[j] + nums[k];
                    if (Math.abs(sum - target) < Math.abs(closest - target)) closest = sum;
                }
        return closest;
    }

    // KEY INSIGHT: this is 3Sum's fix-one-plus-two-pointers reduction, just
    // tracking the best sum seen instead of stopping only at an exact match.

    // Level 2 -- Optimal: sort + fix + two pointers, tracking best. O(n^2)
    // time, O(1) extra space.
    public static int threeSumClosest(int[] nums, int target) {
        Arrays.sort(nums);
        int n = nums.length;
        int closest = nums[0] + nums[1] + nums[2];
        for (int i = 0; i < n - 2; i++) {
            int left = i + 1, right = n - 1;
            while (left < right) {
                int sum = nums[i] + nums[left] + nums[right];
                if (Math.abs(sum - target) < Math.abs(closest - target)) {
                    closest = sum;
                }
                if (sum == target) {
                    return target; // cannot do better than exact
                } else if (sum < target) {
                    left++;
                } else {
                    right--;
                }
            }
        }
        return closest;
    }

    // Level 3 -- Hardened: exactly 3 elements skips the search loop's
    // meaningful work (only one i, one left/right pass) but still returns
    // the only possible sum correctly.
    static int hardened(int[] nums, int target) {
        if (nums == null || nums.length < 3) {
            throw new IllegalArgumentException("need at least three numbers");
        }
        return threeSumClosest(nums, target);
    }

    public static void main(String[] args) {
        int[] nums = {-1, 2, 1, -4};
        System.out.println("brute force: " + bruteForce(nums, 1));
        System.out.println("optimal:     " + threeSumClosest(nums, 1));
        System.out.println("exactly 3:   " + hardened(new int[] {0, 1, 2}, 3));
    }
}
```

How to run: save as `ThreeSumClosest.java`, then run `java ThreeSumClosest.java`.

## 6. Walkthrough

Dry run on sorted `nums = [-4, -1, 1, 2]`, `target = 1`, for `i = 0` (`nums[0] = -4`):

| step | left | right | sum | \|sum-target\| | closest updated? | next action |
|---|---|---|---|---|---|---|
| 1 | 1 | 3 | -4-1+2=-3 | 4 | closest=-3 | -3<1, left++ |
| 2 | 2 | 3 | -4+1+2=-1 | 2 | closest=-1 (2<4) | -1<1, left++ |
| 3 | 3 | 3 | left>=right, loop ends | — | — | — |

For `i = 1` (`nums[1] = -1`): `left=2, right=3` → `sum = -1+1+2 = 2`, `|dist| = 1`, which beats the previous best of `2` — `closest` updates to `2`. Final answer: `2`. Time complexity: O(n²). Space complexity: O(1) extra.

## 7. Gotchas & takeaways

> Gotcha: returning as soon as you find *any* sum, instead of comparing distances with `Math.abs`, gives the wrong answer whenever a later, closer sum exists — you must keep scanning (except on an exact match) and always compare against the best distance seen so far.

- Reuse the 3Sum reduction; the only change is what you do with each computed sum (compare-and-keep instead of collect-if-zero).
- Related problems: 3Sum, 3Sum Smaller, 4Sum.
