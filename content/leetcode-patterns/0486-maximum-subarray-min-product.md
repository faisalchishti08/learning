---
card: leetcode-patterns
gi: 486
slug: maximum-subarray-min-product
title: Maximum Subarray Min-Product
---

## 1. What it is

The "min-product" of a subarray is its minimum element multiplied by the sum of all its elements. Given an array of positive integers `nums`, find the maximum min-product over all non-empty contiguous subarrays, modulo `10^9 + 7`. Example: `nums = [1, 2, 3, 2]` → `14` (the subarray `[2, 3, 2]` has minimum `2` and sum `7`, giving `2 * 7 = 14`).

## 2. Why & when

Fixing "which subarray has this element as its minimum" is exactly the [Sum of Subarray Minimums](0474-sum-of-subarray-minimums.md) contribution question, but instead of just summing minimums, you want the single **widest** subarray for each element where it is the minimum, then multiply by that subarray's sum. This is the [monotonic-stack signal](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md) family applied to a different combining function (max product instead of sum). Constraints: up to 100,000 elements.

## 3. Core concept

**Key idea:** for each element, the best min-product where *it* is the limiting minimum uses the widest possible subarray with that minimum — extending left until a strictly smaller element (or the start) and right until a strictly smaller element (or the end), exactly like [Largest Rectangle in Histogram](0483-largest-rectangle-in-histogram.md). Multiply that element by the sum of that whole span (using a prefix sum array for O(1) range sums), and take the maximum over every element.

**Steps:**
1. Build a prefix-sum array so any range sum `[left, right]` is computed in O(1).
2. Use an increasing monotonic stack (holding indices) to find, for each index `i`, the nearest strictly smaller element to the left (`previousSmaller[i]`, or `-1`) and to the right (`nextSmaller[i]`, or `n`).
3. For each index `i`: the widest subarray where `nums[i]` is the minimum spans from `previousSmaller[i] + 1` to `nextSmaller[i] - 1`.
4. Compute that range's sum using the prefix-sum array, multiply by `nums[i]`, and track the maximum, applying the modulo only to the final result (not intermediate comparisons, since you need exact comparison to find the true maximum before reducing).

**Why the widest span is always optimal for that minimum:** the min-product for a fixed minimum value grows with the subarray's sum (all elements are positive), so among all subarrays where `nums[i]` is the minimum, the widest one has the largest sum — and therefore the largest min-product using that minimum.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Widest span for the minimum element multiplied by that span's sum">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [1, 2, 3, 2], element at index 1 (value 2)</text>
    <text x="20" y="45" fill="#8b949e">previousSmaller[1] = index 0 (value 1) -&gt; span starts at index 1</text>
    <text x="20" y="65" fill="#8b949e">nextSmaller[1] = n (no smaller to the right) -&gt; span ends at index 3</text>
    <text x="20" y="90" fill="#79c0ff">widest span with min=2: indices [1,3] = [2,3,2], sum=7</text>
    <text x="20" y="115" fill="#3fb950">min-product = 2 * 7 = 14 (the answer)</text>
  </g>
</svg>

The widest subarray where an element is the minimum gives the biggest possible min-product for that minimum.

## 5. Runnable example

**Level 1 — Brute force.** For every subarray, track its minimum and sum directly, computing the product. O(n²).

**KEY INSIGHT:** since all values are positive, the widest subarray with a given minimum always has the largest sum for that minimum — reducing the search to one widest-span computation per element, using the same nearest-smaller-neighbor technique as the histogram problem.

**Level 2 — Optimal.** Prefix sums + monotonic-stack widest-span computation, O(n).

**Level 3 — Hardened.** Handles a single-element array and a strictly increasing array (the last, smallest-index element's span still only goes as wide as its neighbors allow).

```java
// MaximumSubarrayMinProduct.java
import java.util.*;

public class MaximumSubarrayMinProduct {

    static final int MOD = 1_000_000_007;

    // Level 1: brute force, O(n^2)
    static int bruteForce(int[] nums) {
        long best = 0;
        for (int i = 0; i < nums.length; i++) {
            long min = nums[i], sum = 0;
            for (int j = i; j < nums.length; j++) {
                min = Math.min(min, nums[j]);
                sum += nums[j];
                best = Math.max(best, min * sum);
            }
        }
        return (int) (best % MOD);
    }

    // Level 2 & 3: prefix sums + monotonic stack widest span, O(n)
    static int maxSumMinProduct(int[] nums) {
        int n = nums.length;
        long[] prefixSum = new long[n + 1];
        for (int i = 0; i < n; i++) prefixSum[i + 1] = prefixSum[i] + nums[i];

        int[] previousSmaller = new int[n];
        int[] nextSmaller = new int[n];
        Deque<Integer> stack = new ArrayDeque<>();

        for (int i = 0; i < n; i++) {
            while (!stack.isEmpty() && nums[stack.peek()] >= nums[i]) stack.pop();
            previousSmaller[i] = stack.isEmpty() ? -1 : stack.peek();
            stack.push(i);
        }
        stack.clear();
        for (int i = n - 1; i >= 0; i--) {
            while (!stack.isEmpty() && nums[stack.peek()] >= nums[i]) stack.pop();
            nextSmaller[i] = stack.isEmpty() ? n : stack.peek();
            stack.push(i);
        }

        long best = 0;
        for (int i = 0; i < n; i++) {
            int left = previousSmaller[i] + 1;
            int right = nextSmaller[i] - 1;
            long rangeSum = prefixSum[right + 1] - prefixSum[left];
            best = Math.max(best, (long) nums[i] * rangeSum);
        }
        return (int) (best % MOD);
    }

    public static void main(String[] args) {
        int[] nums = {1, 2, 3, 2};
        System.out.println("brute force: " + bruteForce(nums));
        System.out.println("optimal:     " + maxSumMinProduct(nums));

        int[] single = {5};
        System.out.println("single element: " + maxSumMinProduct(single));

        int[] increasing = {1, 2, 3, 4};
        System.out.println("increasing:      " + maxSumMinProduct(increasing));
    }
}
```

**How to run:** save as `MaximumSubarrayMinProduct.java`, then run `java MaximumSubarrayMinProduct.java`.

## 6. Walkthrough

Trace `maxSumMinProduct({1, 2, 3, 2})`. Prefix sums: `[0, 1, 3, 6, 8]`.

`previousSmaller` (increasing stack, strict `>=` pop, left to right): index 0 → -1. index 1 (val 2) → pop nothing bigger-or-equal below it except checking against 1 (1<2, stop) → -1... precisely: stack starts empty, i=0 push. i=1 (val2): top is index0(val1), 1>=2? no, stop → previousSmaller[1]=0. i=2(val3): top index1(val2), 2>=3?no → previousSmaller[2]=1. i=3(val2): pop index2(val3, 3>=2), pop index1(val2, 2>=2) → stack has index0(val1) → previousSmaller[3]=0.

`nextSmaller` (right to left): i=3(val2): stack empty → nextSmaller[3]=4(n). i=2(val3): top val2 (index3), 2>=3?no → nextSmaller[2]=3. i=1(val2): pop index2(val3,3>=2), pop index3(val2,2>=2) → stack empty → nextSmaller[1]=4. i=0(val1): everything popped (all >=1) → nextSmaller[0]=4.

For index 1 (value 2): `left = previousSmaller[1]+1 = 1`, `right = nextSmaller[1]-1 = 3`. `rangeSum = prefixSum[4] - prefixSum[1] = 8 - 1 = 7`. Min-product: `2 * 7 = 14`. Checking the other indices gives smaller products, so the maximum is `14`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: applying the modulo to intermediate products before comparing them can corrupt the comparison (a smaller true value might look bigger after wrapping around the modulus) — always compare true `long` values, and apply the modulo only to the final answer.

- Builds on the same nearest-smaller-neighbor technique as [Sum of Subarray Minimums](0474-sum-of-subarray-minimums.md) and [Largest Rectangle in Histogram](0483-largest-rectangle-in-histogram.md), swapping "count subarrays" for "compute the widest span's sum."
- All values being positive is what guarantees the widest span is also the best-sum span for a fixed minimum — this would not hold with negative numbers.
- Time: O(n) — two monotonic-stack passes plus one prefix-sum pass, all linear.
