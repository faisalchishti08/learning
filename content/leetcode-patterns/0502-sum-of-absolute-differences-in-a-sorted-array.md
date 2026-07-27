---
card: leetcode-patterns
gi: 502
slug: sum-of-absolute-differences-in-a-sorted-array
title: Sum of Absolute Differences in a Sorted Array
---

## 1. What it is

Given a **sorted** array `nums` (non-decreasing), return an array `result` where `result[i]` is the sum of absolute differences between `nums[i]` and every other element in the array. Example: `nums = [2, 3, 5]` → `[4, 3, 5]` (`result[0] = |2-3|+|2-5| = 1+3 = 4`).

## 2. Why & when

Because `nums` is sorted, every element to the left of index `i` is less than or equal to `nums[i]`, and every element to the right is greater than or equal to it. That means `|nums[i] - nums[j]|` simplifies to `nums[i] - nums[j]` for `j < i`, and `nums[j] - nums[i]` for `j > i` — removing the absolute value entirely and turning the whole computation into two prefix-sum-style range sums, from the [prefix-sum signal](0487-prefix-sum-signal-range-sums-or-subarray-sum-conditions.md) family. Constraints: up to 100,000 elements, no duplicates required (sorted, may repeat).

## 3. Core concept

**Key idea:** for index `i`, split the sum into a left part and a right part. The left part is `i * nums[i] - (sum of nums[0..i-1])` (every one of the `i` elements to the left contributes `nums[i]` minus itself). The right part is `(sum of nums[i+1..n-1]) - (n - 1 - i) * nums[i]` (every one of the remaining elements contributes itself minus `nums[i]`). Both parts use a precomputed prefix sum for O(1) range sums.

**Steps:**
1. Build a prefix-sum array over `nums`.
2. For each index `i`: compute `leftSum = prefixSum[i]` (sum of everything before `i`) and `leftCount = i`.
3. Left contribution: `leftCount * nums[i] - leftSum`.
4. Compute `rightSum = total - prefixSum[i+1]` (sum of everything after `i`) and `rightCount = n - 1 - i`.
5. Right contribution: `rightSum - rightCount * nums[i]`.
6. `result[i] = leftContribution + rightContribution`.

**Why sortedness removes the need for `Math.abs`:** the absolute value of a difference between two sorted elements is fixed by their relative position — an element to the left is never bigger, and an element to the right is never smaller, so the sign of the subtraction is always known in advance without checking it at runtime.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Splitting the absolute-difference sum into a left part and a right part using sortedness">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [2, 3, 5], index i=1 (value 3)</text>
    <text x="20" y="45" fill="#8b949e">left: 1 element (2) &lt;= 3. contribution = 1*3 - 2 = 1</text>
    <text x="20" y="65" fill="#8b949e">right: 1 element (5) &gt;= 3. contribution = 5 - 1*3 = 2</text>
    <text x="20" y="90" fill="#3fb950">result[1] = 1 + 2 = 3</text>
  </g>
</svg>

Sortedness guarantees the sign of every difference, letting each side be computed as a simple linear formula.

## 5. Runnable example

**Level 1 — Brute force.** For each index, sum `Math.abs(nums[i] - nums[j])` over every other index. O(n²).

**KEY INSIGHT:** sortedness fixes the sign of every difference in advance, turning the absolute-value sum into two simple prefix-sum-based formulas — no per-pair comparison needed.

**Level 2 — Optimal.** Prefix sums + the left/right formula per index, O(n).

**Level 3 — Hardened.** Handles duplicate values (difference `0` contributes nothing) and a 2-element array.

```java
// SumOfAbsoluteDifferences.java
import java.util.Arrays;

public class SumOfAbsoluteDifferences {

    // Level 1: brute force, O(n^2)
    static int[] bruteForce(int[] nums) {
        int n = nums.length;
        int[] result = new int[n];
        for (int i = 0; i < n; i++) {
            int sum = 0;
            for (int j = 0; j < n; j++) {
                if (j != i) sum += Math.abs(nums[i] - nums[j]);
            }
            result[i] = sum;
        }
        return result;
    }

    // Level 2 & 3: prefix sums + left/right formula, O(n)
    static int[] getSumAbsoluteDifferences(int[] nums) {
        int n = nums.length;
        int[] prefixSum = new int[n + 1];
        for (int i = 0; i < n; i++) prefixSum[i + 1] = prefixSum[i] + nums[i];
        int total = prefixSum[n];

        int[] result = new int[n];
        for (int i = 0; i < n; i++) {
            int leftSum = prefixSum[i];
            int leftContribution = i * nums[i] - leftSum;

            int rightSum = total - prefixSum[i + 1];
            int rightCount = n - 1 - i;
            int rightContribution = rightSum - rightCount * nums[i];

            result[i] = leftContribution + rightContribution;
        }
        return result;
    }

    public static void main(String[] args) {
        int[] nums = {2, 3, 5};
        System.out.println("brute force: " + Arrays.toString(bruteForce(nums)));
        System.out.println("optimal:     " + Arrays.toString(getSumAbsoluteDifferences(nums)));

        System.out.println("duplicates: " + Arrays.toString(getSumAbsoluteDifferences(new int[]{1, 1, 1, 2})));
    }
}
```

**How to run:** save as `SumOfAbsoluteDifferences.java`, then run `java SumOfAbsoluteDifferences.java`.

## 6. Walkthrough

Trace `getSumAbsoluteDifferences({2, 3, 5})`. `prefixSum = [0, 2, 5, 10]`, `total = 10`.

| i | nums[i] | leftSum | leftContribution | rightSum | rightCount | rightContribution | result[i] |
|---|---|---|---|---|---|---|---|
| 0 | 2 | 0 | 0*2-0=0 | 10-2=8 | 2 | 8-2*2=4 | 4 |
| 1 | 3 | 2 | 1*3-2=1 | 10-5=5 | 1 | 5-1*3=2 | 3 |
| 2 | 5 | 5 | 2*5-5=5 | 10-10=0 | 0 | 0-0*5=0 | 5 |

Final `result = [4, 3, 5]`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: applying this formula to an **unsorted** array gives wrong answers, since the left/right split relies entirely on sortedness to fix the sign of each difference — if the input is not already sorted, you must sort it first (and remember the original indices if the output needs to match the original order).

- Sortedness turns `Math.abs(a - b)` into a predictable-sign subtraction, avoiding per-pair comparisons.
- The formula splits cleanly into a left contribution and a right contribution, both computed from prefix sums in O(1) per index.
- Time: O(n) — one pass to build the prefix sum, one pass to compute every result.
