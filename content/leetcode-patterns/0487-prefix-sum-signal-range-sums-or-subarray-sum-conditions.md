---
card: leetcode-patterns
gi: 487
slug: prefix-sum-signal-range-sums-or-subarray-sum-conditions
title: Prefix Sum — signal: range sums or subarray-sum conditions
---

## 1. What it is

A prefix sum array stores, at each index `i`, the running total of all elements from the start of the array up to and including `i`. Once you have it, the sum of any range `[left, right]` is a single subtraction: `prefixSum[right] - prefixSum[left - 1]`, instead of a fresh loop over that range every time.

## 2. Why & when

Reach for prefix sums whenever a brute-force solution recomputes a range sum from scratch for every query, giving O(n) per query and O(n · q) for `q` queries (or O(n²) when the "queries" are all possible subarrays). Precomputing prefix sums turns every range sum into O(1), after a one-time O(n) setup.

Learn to recognize these signals in a problem statement:

- **"Sum of a range `[i, j]`"**, asked repeatedly for different `i` and `j`. This is the direct use case: precompute once, answer every query in O(1).
- **"Number of subarrays whose sum equals (or is divisible by) some target."** Rephrase the condition using prefix sums: a subarray `[i+1, j]` sums to `k` exactly when `prefixSum[j] - prefixSum[i] = k`, i.e. `prefixSum[i] = prefixSum[j] - k`. Counting how many earlier prefixes equal that value (with a hash map) answers the question in one pass.
- **"Equal number of 0s and 1s"** or similar balance conditions — map one value to `+1` and the other to `-1`; a balanced subarray is one where the prefix sum returns to a previously seen value.
- **2D grid range-sum queries** ("sum of a submatrix") extend the same idea to two dimensions with a 2D prefix-sum table.
- **"Divisible by k"** conditions on subarray sums — use `prefixSum % k` as the hash map key, since two prefixes with the same remainder bound a subarray divisible by `k`.

The alternative is recomputing each range sum with a fresh loop (O(n) per query) or, for the "count subarrays matching a condition" variant, a nested loop over every start and end (O(n²)). Prefix sums answer both in O(n) total.

## 3. Core concept

**Key idea:** build an array `prefixSum` where `prefixSum[i]` is the sum of `nums[0..i-1]` (using a 1-indexed convention with `prefixSum[0] = 0` avoids edge-case checks for ranges starting at index 0). Any range sum `nums[left..right]` (inclusive) is then `prefixSum[right + 1] - prefixSum[left]`.

**Two use patterns:**

1. **Direct range queries.** Precompute the array once; answer each `[left, right]` query with one subtraction. Best for "many queries on a fixed array."
2. **Counting subarrays matching a sum condition.** Scan once, maintaining a running prefix sum and a hash map of "how many times has each prefix sum value (or remainder) been seen so far." At each step, check whether `runningSum - target` (or the appropriate remainder) already exists in the map — every match is one valid subarray ending here.

**Why the hash map trick works:** if `prefixSum[j] - prefixSum[i] = k`, rearranging gives `prefixSum[i] = prefixSum[j] - k`. So for each new prefix sum `prefixSum[j]`, you are really asking "how many earlier prefixes equal `prefixSum[j] - k`" — a single hash map lookup, updated as you go, replaces a nested loop over every earlier index.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Prefix sum array turning a range sum into one subtraction">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [3, 1, 4, 1, 5]</text>
    <text x="20" y="45" fill="#8b949e">prefixSum = [0, 3, 4, 8, 9, 14] (prefixSum[i] = sum of nums[0..i-1])</text>
    <text x="20" y="70" fill="#79c0ff">sum of nums[1..3] (values 1,4,1) = prefixSum[4] - prefixSum[1] = 9 - 3 = 6</text>
    <rect x="20" y="90" width="50" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="70" y="90" width="50" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="120" y="90" width="50" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="170" y="90" width="50" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="220" y="90" width="50" height="30" fill="#161b22" stroke="#30363d"/>
    <text x="45" y="110" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="95" y="110" fill="#79c0ff" text-anchor="middle">1</text>
    <text x="145" y="110" fill="#79c0ff" text-anchor="middle">4</text>
    <text x="195" y="110" fill="#79c0ff" text-anchor="middle">1</text>
    <text x="245" y="110" fill="#e6edf3" text-anchor="middle">5</text>
    <text x="145" y="140" fill="#3fb950" text-anchor="middle">range [1,3] sums to 6, computed in O(1)</text>
  </g>
</svg>

Any range's sum is the difference between two precomputed running totals — no rescanning needed.

## 5. Runnable example

The artifact below is a reusable signal-checker: it compares brute-force range-sum time (rescanning) against the prefix-sum approach (one subtraction), on a batch of queries.

### Signal-checker

```java
// PrefixSumSignal.java
public class PrefixSumSignal {

    static int bruteForceRangeSum(int[] nums, int left, int right) {
        int sum = 0;
        for (int i = left; i <= right; i++) sum += nums[i];
        return sum;
    }

    static int[] buildPrefixSum(int[] nums) {
        int[] prefixSum = new int[nums.length + 1];
        for (int i = 0; i < nums.length; i++) {
            prefixSum[i + 1] = prefixSum[i] + nums[i];
        }
        return prefixSum;
    }

    static int rangeSumFromPrefix(int[] prefixSum, int left, int right) {
        return prefixSum[right + 1] - prefixSum[left];
    }

    public static void main(String[] args) {
        int[] nums = {3, 1, 4, 1, 5};
        int[] prefixSum = buildPrefixSum(nums);

        System.out.println("brute force sum[1..3]: " + bruteForceRangeSum(nums, 1, 3));
        System.out.println("prefix sum   sum[1..3]: " + rangeSumFromPrefix(prefixSum, 1, 3));
        System.out.println("brute force sum[0..4]: " + bruteForceRangeSum(nums, 0, 4));
        System.out.println("prefix sum   sum[0..4]: " + rangeSumFromPrefix(prefixSum, 0, 4));
    }
}
```

**How to run:** save as `PrefixSumSignal.java`, then run `java PrefixSumSignal.java`.

## 6. Walkthrough

1. You read a problem asking for the sum of `nums[1..3]` and, separately, `nums[0..4]`, possibly repeated many times across different query ranges. That is the "range sum, asked repeatedly" signal.
2. You build `prefixSum` once: `[0, 3, 4, 8, 9, 14]`, where `prefixSum[i]` sums everything before index `i` in the original array.
3. For `nums[1..3]`, you compute `prefixSum[4] - prefixSum[1] = 9 - 3 = 6`, matching the brute-force scan of `1 + 4 + 1 = 6`.
4. For `nums[0..4]`, you compute `prefixSum[5] - prefixSum[0] = 14 - 0 = 14`, matching the full-array scan `3+1+4+1+5=14`.
5. Both queries took O(1) once `prefixSum` was built, regardless of how wide the range was.

## 7. Gotchas & takeaways

> Gotcha: mixing up 0-indexed and 1-indexed prefix sum conventions causes off-by-one errors. Using `prefixSum[0] = 0` and `prefixSum[i+1] = prefixSum[i] + nums[i]` (as shown here) means the sum of `nums[left..right]` is always `prefixSum[right+1] - prefixSum[left]`, with no special case for `left = 0`.

- Signal words: "sum of a range," "many queries," "count subarrays with sum/remainder equal to," "equal number of X and Y."
- Direct range queries: precompute once, answer in O(1) each. Counting subarrays by sum: scan once with a running sum and a hash map.
- Both variants turn an O(n) or O(n²) brute force into O(n) total.
