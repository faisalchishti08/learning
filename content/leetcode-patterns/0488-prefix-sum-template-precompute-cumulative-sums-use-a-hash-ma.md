---
card: leetcode-patterns
gi: 488
slug: prefix-sum-template-precompute-cumulative-sums-use-a-hash-ma
title: Prefix Sum — template: precompute cumulative sums; use a hash map of prefixes
---

## 1. What it is

There are two prefix-sum templates. The **array template** precomputes every prefix sum up front, for O(1) range queries afterward. The **hash-map template** builds the running sum on the fly, in a single pass, using a hash map to count or look up previously seen prefix values — used for counting subarrays that match a sum condition.

## 2. Why & when

Use the array template when the input is fixed and you will answer many range-sum queries against it (or need random access to arbitrary ranges). Use the hash-map template when the question is "how many subarrays satisfy some sum condition," since you never need to store every prefix sum permanently — only a running count of which values (or remainders) have appeared so far.

## 3. Core concept

**Array template.** Build `prefixSum[0] = 0`, then `prefixSum[i+1] = prefixSum[i] + nums[i]`. Any query `[left, right]` is answered by `prefixSum[right+1] - prefixSum[left]`, in O(1), using the precomputed array.

**Hash-map template.** Scan left to right, maintaining a running sum and a `Map<Integer, Integer>` from "prefix sum value seen so far" to "how many times." Initialize the map with `{0: 1}` (an empty prefix, representing "the subarray starting at index 0" as a valid case). At each index: add the current value to the running sum; look up `runningSum - target` in the map — every hit is one subarray ending here that sums to `target`; then record the current `runningSum` in the map (increment its count).

**Why seeding the map with `{0: 1}` matters:** without it, a subarray that starts at index 0 and sums exactly to `target` would never be counted, because there is no "prefix before index 0" to subtract — the seed entry represents exactly that empty prefix.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two prefix sum templates: precomputed array versus running hash map">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">Array template: precompute once, query in O(1)</text>
    <text x="20" y="45" fill="#8b949e">prefixSum = [0, 3, 4, 8, 9, 14]</text>
    <text x="20" y="65" fill="#79c0ff">query(left, right) = prefixSum[right+1] - prefixSum[left]</text>
    <text x="20" y="100" fill="#e6edf3" font-weight="bold">Hash-map template: one pass, count matches</text>
    <text x="20" y="125" fill="#8b949e">map starts {0: 1}. running sum updates as you scan.</text>
    <text x="20" y="145" fill="#f0883e">count += map.getOrDefault(runningSum - target, 0)</text>
    <text x="20" y="165" fill="#f0883e">map[runningSum] += 1</text>
  </g>
</svg>

The array template answers range queries in O(1) after setup; the hash-map template counts matching subarrays in one linear pass.

## 5. Runnable example

Both templates as generic, reusable methods.

```java
// PrefixSumTemplates.java
import java.util.*;

public class PrefixSumTemplates {

    // Array template: precompute, then O(1) range queries
    static int[] buildPrefixSum(int[] nums) {
        int[] prefixSum = new int[nums.length + 1];
        for (int i = 0; i < nums.length; i++) {
            prefixSum[i + 1] = prefixSum[i] + nums[i];
        }
        return prefixSum;
    }

    static int rangeSum(int[] prefixSum, int left, int right) {
        return prefixSum[right + 1] - prefixSum[left];
    }

    // Hash-map template: count subarrays summing to target, O(n)
    static int countSubarraysWithSum(int[] nums, int target) {
        Map<Integer, Integer> seenCount = new HashMap<>();
        seenCount.put(0, 1); // empty prefix, for subarrays starting at index 0
        int runningSum = 0;
        int count = 0;

        for (int num : nums) {
            runningSum += num;
            count += seenCount.getOrDefault(runningSum - target, 0);
            seenCount.merge(runningSum, 1, Integer::sum);
        }
        return count;
    }

    public static void main(String[] args) {
        int[] nums = {3, 1, 4, 1, 5};
        int[] prefixSum = buildPrefixSum(nums);
        System.out.println("range[1,3]: " + rangeSum(prefixSum, 1, 3));

        int[] target1 = {1, 1, 1};
        System.out.println("subarrays summing to 2 in [1,1,1]: " + countSubarraysWithSum(target1, 2));
    }
}
```

**How to run:** save as `PrefixSumTemplates.java`, then run `java PrefixSumTemplates.java`.

## 6. Walkthrough

1. `countSubarraysWithSum({1, 1, 1}, 2)` starts with `seenCount = {0: 1}`, `runningSum = 0`, `count = 0`.
2. First `1`: `runningSum = 1`. Look up `1 - 2 = -1` in the map: not present, `count` stays `0`. Record `runningSum=1` in the map: `{0:1, 1:1}`.
3. Second `1`: `runningSum = 2`. Look up `2 - 2 = 0`: present with count `1` — `count` becomes `1` (the subarray `[1,1]`, indices 0-1). Record `runningSum=2`: `{0:1, 1:1, 2:1}`.
4. Third `1`: `runningSum = 3`. Look up `3 - 2 = 1`: present with count `1` — `count` becomes `2` (the subarray `[1,1]`, indices 1-2). Record `runningSum=3`.
5. Final count: `2`, matching the two subarrays `[1,1]` (positions 0-1 and 1-2) that sum to `2`.

## 7. Gotchas & takeaways

> Gotcha: forgetting to seed the hash map with `{0: 1}` silently misses every valid subarray that starts at index 0 — always initialize with the empty-prefix entry before scanning.

- Array template: precompute once, O(1) per query — best for a fixed array with many range queries.
- Hash-map template: one pass, O(1) amortized per step — best for counting subarrays matching a sum (or remainder) condition.
- Both are variations of the same idea: turn "sum over a range" into a difference (or lookup) of two running totals.
