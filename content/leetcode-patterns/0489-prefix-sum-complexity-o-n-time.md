---
card: leetcode-patterns
gi: 489
slug: prefix-sum-complexity-o-n-time
title: Prefix Sum — complexity: O(n) time
---

## 1. What it is

This page explains the time and space complexity of both prefix-sum templates, and lists the named problems that use the pattern.

## 2. Why & when

Interviewers expect you to state complexity precisely, including the one-time setup cost versus the per-query cost. "It's O(1)" is only true per query, after an O(n) setup — conflating the two, or forgetting the setup cost entirely, is a common mistake worth avoiding out loud.

## 3. Core concept

**Array template — time O(n) setup, O(1) per query.** Building `prefixSum` takes one linear pass, O(n). After that, every range-sum query is a single subtraction, O(1), regardless of the range's width. For `q` queries, total time is `O(n + q)`, dramatically better than the brute-force `O(n · q)` (rescanning each range from scratch).

**Array template — space O(n).** The `prefixSum` array holds `n + 1` values, proportional to the input size.

**Hash-map template — time O(n).** A single left-to-right scan; each step does O(1) amortized work (one hash map lookup, one hash map update). Total: O(n) for the whole scan, compared to the brute-force O(n²) (checking every subarray's sum directly with nested loops).

**Hash-map template — space O(n).** In the worst case (all prefix sums distinct), the map stores up to `n` entries.

**Why the difference vs. a nested loop is O(n) vs O(n²), not just a constant factor:** the nested-loop brute force recomputes information (partial sums) that a single pass already has available cheaply. The prefix-sum techniques reuse that information instead of throwing it away and recomputing it for every new starting index.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparing brute force per-query cost against one-time prefix sum setup plus O(1) queries">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">Brute force: every query rescans its range</text>
    <text x="20" y="45" fill="#f0883e">q queries x O(n) rescan each = O(n * q) total</text>
    <text x="400" y="20" fill="#e6edf3" font-weight="bold">Prefix sum: build once, query O(1)</text>
    <text x="400" y="45" fill="#79c0ff">O(n) build + q x O(1) query = O(n + q) total</text>
    <text x="20" y="90" fill="#8b949e">For n=1000, q=1000: brute force ~ 1,000,000 ops</text>
    <text x="20" y="110" fill="#3fb950">prefix sum ~ 2,000 ops -- roughly 500x fewer for this size</text>
  </g>
</svg>

Precomputing once and querying in O(1) turns a multiplicative cost (`n * q`) into an additive one (`n + q`).

## 5. Runnable example

An instrumented comparison that counts total array accesses for brute-force range queries versus the prefix-sum approach, across many queries on the same array.

```java
// PrefixSumComplexity.java
public class PrefixSumComplexity {

    static long bruteForceAccesses(int[] nums, int[][] queries) {
        long accesses = 0;
        for (int[] q : queries) {
            for (int i = q[0]; i <= q[1]; i++) {
                accesses++; // one array access per element in the range
            }
        }
        return accesses;
    }

    static long prefixSumAccesses(int[] nums, int[][] queries) {
        long accesses = nums.length; // building the prefix sum touches every element once
        for (int[] q : queries) {
            accesses += 2; // each query is exactly two array accesses (two subtractions' operands)
        }
        return accesses;
    }

    public static void main(String[] args) {
        int n = 1000;
        int[] nums = new int[n];
        for (int i = 0; i < n; i++) nums[i] = i;

        int[][] queries = new int[1000][2];
        for (int i = 0; i < queries.length; i++) {
            queries[i][0] = 0;
            queries[i][1] = n - 1; // worst case: every query spans the whole array
        }

        System.out.println("brute force accesses: " + bruteForceAccesses(nums, queries));
        System.out.println("prefix sum accesses:  " + prefixSumAccesses(nums, queries));
    }
}
```

**How to run:** save as `PrefixSumComplexity.java`, then run `java PrefixSumComplexity.java`.

## 6. Walkthrough

1. `nums` has `1000` elements; `queries` contains `1000` full-array range requests (`[0, 999]` each), the worst case for the brute-force approach.
2. `bruteForceAccesses` rescans all `1000` elements for every one of the `1000` queries, totaling `1000 * 1000 = 1,000,000` accesses.
3. `prefixSumAccesses` builds the prefix sum array once (`1000` accesses), then answers each of the `1000` queries with exactly `2` array accesses (`prefixSum[right+1]` and `prefixSum[left]`), totaling `1000 + 1000 * 2 = 3000` accesses.
4. The gap between `1,000,000` and `3,000` illustrates the difference between `O(n · q)` and `O(n + q)` directly: as `q` grows, the brute-force cost grows proportionally to both `n` and `q` multiplied together, while the prefix-sum cost grows only as their sum.
5. This holds regardless of which specific ranges are queried — the brute-force cost depends on the *width* of each range, but the prefix-sum cost is always exactly `2` accesses per query.

## 7. Gotchas & takeaways

> Gotcha: quoting prefix sums as "O(1)" without mentioning the O(n) setup cost is technically incomplete — always state both: O(n) to build, O(1) per query afterward.

- Array template: O(n) time to build, O(1) time per query, O(n) space.
- Hash-map template: O(n) time total (one pass, O(1) amortized per step), O(n) space in the worst case.
- Reference problems that use this pattern: Range Sum Query - Immutable, Range Sum Query 2D - Immutable, Subarray Sum Equals K, Contiguous Array, Continuous Subarray Sum, Subarray Sums Divisible by K, Product of Array Except Self.
