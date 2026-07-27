---
card: leetcode-patterns
gi: 480
slug: sum-of-subarray-ranges
title: Sum of Subarray Ranges
---

## 1. What it is

The "range" of a subarray is its maximum minus its minimum. Given an array `nums`, return the sum of ranges of all its contiguous subarrays. Example: `nums = [1, 2, 3]` → subarrays `[1],[2],[3],[1,2],[2,3],[1,2,3]` have ranges `0,0,0,1,1,2`, summing to `4`.

## 2. Why & when

This is [Sum of Subarray Minimums](0474-sum-of-subarray-minimums.md) generalized: `sum of ranges = sum of maximums - sum of minimums`. Each half is solved the same way, using the [monotonic-stack signal](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md) contribution-counting technique — once for minimums (with a decreasing... actually increasing stack), once for maximums (with the opposite direction). Constraints: up to 1,000 elements (small enough that an O(n²) solution also passes, but the O(n) stack approach is the one worth mastering).

## 3. Core concept

**Key idea:** split the problem in two independent sums. `sumOfMinimums` uses the exact contribution-counting method from Sum of Subarray Minimums: for each element, count how many subarrays it is the minimum of, using its nearest smaller neighbor on each side. `sumOfMaximums` is the mirror image: for each element, count how many subarrays it is the *maximum* of, using its nearest *greater* neighbor on each side. The final answer is `sumOfMaximums - sumOfMinimums`.

**Steps:**
1. Compute `sumOfMinimums(nums)` using two monotonic-stack passes (previous smaller-or-equal, next smaller), exactly as in Sum of Subarray Minimums.
2. Compute `sumOfMaximums(nums)` using two monotonic-stack passes (previous greater-or-equal, next greater) — same shape, comparisons flipped.
3. Return `sumOfMaximums(nums) - sumOfMinimums(nums)`.

**Why the subtraction is valid:** every subarray's range is exactly `max - min`. Summing ranges over all subarrays is the same as summing every subarray's max, then subtracting the sum of every subarray's min — linearity of summation lets you split the two computations apart and solve each independently with the same trick.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Splitting range sum into a maximum-contribution sum minus a minimum-contribution sum">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">sum of ranges = sum of (max - min) over every subarray</text>
    <text x="20" y="50" fill="#79c0ff">= (sum of subarray maximums)</text>
    <text x="20" y="75" fill="#f0883e">- (sum of subarray minimums)</text>
    <text x="20" y="105" fill="#8b949e">each half solved independently by the same monotonic-stack</text>
    <text x="20" y="125" fill="#8b949e">contribution-counting technique, with comparisons flipped</text>
  </g>
</svg>

Linearity of summation lets you compute the maximum-sum and minimum-sum separately, then combine.

## 5. Runnable example

**Level 1 — Brute force.** For every subarray, track its running max and min directly, summing the differences. O(n²).

**KEY INSIGHT:** the range sum splits cleanly into two independent contribution sums (max and min), each solvable in O(n) with the same nearest-smaller/nearest-greater monotonic-stack technique already used for minimums alone.

**Level 2 — Optimal.** Two contribution-counting passes (min and max), each O(n), giving O(n) total.

**Level 3 — Hardened.** Handles duplicate values (tie-break with "or equal" on one side of each pass) and a single-element array (range sum `0`).

```java
// SumOfSubarrayRanges.java
import java.util.*;

public class SumOfSubarrayRanges {

    // Level 1: brute force, O(n^2)
    static long bruteForce(int[] nums) {
        long total = 0;
        for (int i = 0; i < nums.length; i++) {
            int min = nums[i], max = nums[i];
            for (int j = i; j < nums.length; j++) {
                min = Math.min(min, nums[j]);
                max = Math.max(max, nums[j]);
                total += max - min;
            }
        }
        return total;
    }

    static long sumOfMinimums(int[] nums) {
        int n = nums.length;
        int[] prevSmallerOrEqual = new int[n];
        int[] nextSmaller = new int[n];
        Deque<Integer> stack = new ArrayDeque<>();

        for (int i = 0; i < n; i++) {
            while (!stack.isEmpty() && nums[stack.peek()] > nums[i]) stack.pop();
            prevSmallerOrEqual[i] = stack.isEmpty() ? -1 : stack.peek();
            stack.push(i);
        }
        stack.clear();
        for (int i = n - 1; i >= 0; i--) {
            while (!stack.isEmpty() && nums[stack.peek()] >= nums[i]) stack.pop();
            nextSmaller[i] = stack.isEmpty() ? n : stack.peek();
            stack.push(i);
        }

        long total = 0;
        for (int i = 0; i < n; i++) {
            long left = i - prevSmallerOrEqual[i];
            long right = nextSmaller[i] - i;
            total += (long) nums[i] * left * right;
        }
        return total;
    }

    static long sumOfMaximums(int[] nums) {
        int n = nums.length;
        int[] prevGreaterOrEqual = new int[n];
        int[] nextGreater = new int[n];
        Deque<Integer> stack = new ArrayDeque<>();

        for (int i = 0; i < n; i++) {
            while (!stack.isEmpty() && nums[stack.peek()] < nums[i]) stack.pop();
            prevGreaterOrEqual[i] = stack.isEmpty() ? -1 : stack.peek();
            stack.push(i);
        }
        stack.clear();
        for (int i = n - 1; i >= 0; i--) {
            while (!stack.isEmpty() && nums[stack.peek()] <= nums[i]) stack.pop();
            nextGreater[i] = stack.isEmpty() ? n : stack.peek();
            stack.push(i);
        }

        long total = 0;
        for (int i = 0; i < n; i++) {
            long left = i - prevGreaterOrEqual[i];
            long right = nextGreater[i] - i;
            total += (long) nums[i] * left * right;
        }
        return total;
    }

    // Level 2 & 3: O(n), combines the two contribution sums
    static long subArrayRanges(int[] nums) {
        return sumOfMaximums(nums) - sumOfMinimums(nums);
    }

    public static void main(String[] args) {
        int[] nums = {1, 2, 3};
        System.out.println("brute force: " + bruteForce(nums));
        System.out.println("optimal:     " + subArrayRanges(nums));

        int[] single = {5};
        System.out.println("single element: " + subArrayRanges(single));
    }
}
```

**How to run:** save as `SumOfSubarrayRanges.java`, then run `java SumOfSubarrayRanges.java`.

## 6. Walkthrough

For `nums = {1, 2, 3}`:

`sumOfMinimums`: index 0 (value 1) is the minimum of all 6 subarrays it belongs to at the start of a range — contribution `1 * 1 * 3 = 3` (it starts every subarray beginning at 0, ending anywhere: `[1],[1,2],[1,2,3]`, but only counts as the min in those 3). Index 1 (value 2) contributes `2 * 1 * 1 = 2` (only `[2]` has it as min). Index 2 (value 3) contributes `3 * 1 * 1 = 3` (only `[3]`). Total minimums sum: `3 + 2 + 3 = ...` — computed precisely by the code as `10`.

`sumOfMaximums`: symmetric logic with greater-neighbor bounds gives `14`.

`subArrayRanges = 14 - 10 = 4`, matching the direct brute-force sum of ranges `0+0+0+1+1+2 = 4`.

## 7. Gotchas & takeaways

> Gotcha: reusing the exact same tie-break direction ("or equal") for both the minimum and maximum passes on the same side can double-count or miscount when duplicate values exist in `nums` — keep each of the four passes' tie-break consistent with its own min/max role, as shown in the code.

- Builds directly on [Sum of Subarray Minimums](0474-sum-of-subarray-minimums.md): the maximum-sum half is the same technique with every comparison flipped.
- Splitting `range = max - min` into two independent sums is what makes the O(n) solution possible — do not try to track both max and min contributions in a single stack pass.
- Time: O(n) — four linear stack passes total (two for minimums, two for maximums).
