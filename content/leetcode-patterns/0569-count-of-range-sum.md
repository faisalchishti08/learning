---
card: leetcode-patterns
gi: 569
slug: count-of-range-sum
title: Count of Range Sum
---

## 1. What it is

Given an integer array `nums` and two bounds `lower` and `upper`, count the number of contiguous subarray sums that fall within `[lower, upper]`, inclusive. Example: `nums = [-2,5,-1]`, `lower=-2`, `upper=2` → `3` (subarrays `[0,0]=-2`, `[2,2]=-1`, `[0,2]=2` all have sums in range).

## 2. Why & when

A subarray's sum is `prefixSum[j] - prefixSum[i]` for some `i < j` (the same [prefix-sum](0488-prefix-sum-template-precompute-cumulative-sums-use-a-hash-ma.md) identity from Subarray Sum Equals K). The condition `lower <= prefixSum[j] - prefixSum[i] <= upper` rearranges to `prefixSum[j] - upper <= prefixSum[i] <= prefixSum[j] - lower` — a **range** query on already-seen prefix sums, not a single-value lookup. That range query, repeated as you scan and insert each new prefix sum, is exactly the [Fenwick tree over compressed ranks](0567-count-of-smaller-numbers-after-self.md) pattern. Constraints: up to 100,000 elements.

## 3. Core concept

**Key idea:** compute all prefix sums first (including the empty prefix, `0`), compress them into ranks, then scan left to right: for each `prefixSum[j]`, query how many *already-inserted* prefix sums fall within `[prefixSum[j] - upper, prefixSum[j] - lower]` — a **range** count, done as `rankUpperBound - rankLowerBound` on the Fenwick tree, since a Fenwick tree only exposes prefix (single-boundary) queries directly.

**Steps:**
1. Compute all `n + 1` prefix sums (`prefixSum[0] = 0`, then running totals).
2. Coordinate-compress all `n + 1` prefix sums into ranks.
3. Initialize a Fenwick tree sized to the number of distinct prefix sums. Insert `prefixSum[0]`'s rank first (representing the empty prefix, available before any real element is processed).
4. For each `j` from `1` to `n`: find, via binary search over the sorted distinct prefix sums, the count of already-inserted values `<= prefixSum[j] - lower` and the count of already-inserted values `< prefixSum[j] - upper` (using Fenwick prefix sums at those computed rank boundaries); the difference is the count of valid `i` for this `j`. Add to the running total. Then insert `prefixSum[j]`'s own rank.
5. Return the running total.

**Why the empty prefix (`prefixSum[0] = 0`) must be inserted before the loop starts:** a subarray can start at index `0`, meaning `i = 0` uses the empty prefix (`prefixSum[0]`) as its "before" boundary. Skipping this insertion would silently miss every valid subarray that starts at the very first element.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A range query on already-inserted prefix sums, bounded by prefixSum[j] minus upper and minus lower">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">for prefixSum[j], valid prefixSum[i] satisfies:</text>
    <text x="20" y="50" fill="#79c0ff">prefixSum[j] - upper &lt;= prefixSum[i] &lt;= prefixSum[j] - lower</text>
    <text x="20" y="85" fill="#3fb950">count = fenwick.rangeCount(prefixSum[j]-upper, prefixSum[j]-lower)</text>
    <text x="20" y="115" fill="#f0883e">a RANGE query, built from two Fenwick prefix-sum lookups via binary search boundaries</text>
  </g>
</svg>

Each query needs both a lower and upper rank boundary, found by binary search, then answered as the difference of two Fenwick prefix sums.

## 5. Runnable example

**Level 1 — Brute force.** Compute every subarray sum directly and check it against `[lower, upper]`. O(n²).

**KEY INSIGHT:** rewriting the range condition on subarray sums as a range condition on prefix sums, then answering it with a Fenwick tree over compressed prefix-sum ranks, avoids recomputing sums and avoids the O(n²) pair scan.

**Level 2 — Optimal.** Coordinate compression, Fenwick tree, two binary searches per query, O(n log n).

**Level 3 — Hardened.** Handles negative numbers (prefix sums can be negative; compression handles any range), and `lower == upper` (a single exact-sum target).

```java
// CountOfRangeSum.java
import java.util.*;

public class CountOfRangeSum {

    static class Fenwick {
        int[] tree;
        int n;
        Fenwick(int n) {
            this.n = n;
            tree = new int[n + 1];
        }
        void update(int i, int delta) {
            for (; i <= n; i += i & (-i)) tree[i] += delta;
        }
        int prefixSum(int i) {
            int sum = 0;
            for (; i > 0; i -= i & (-i)) sum += tree[i];
            return sum;
        }
    }

    static int countRangeSum(int[] nums, int lower, int upper) {
        int n = nums.length;
        long[] prefix = new long[n + 1];
        for (int i = 0; i < n; i++) prefix[i + 1] = prefix[i] + nums[i];

        long[] sorted = prefix.clone();
        Arrays.sort(sorted);
        Map<Long, Integer> rank = new HashMap<>();
        int r = 0;
        for (long val : sorted) {
            if (!rank.containsKey(val)) rank.put(val, ++r);
        }

        Fenwick fenwick = new Fenwick(rank.size());
        fenwick.update(rank.get(prefix[0]), 1); // insert empty prefix first

        int total = 0;
        for (int j = 1; j <= n; j++) {
            long loBound = prefix[j] - upper;
            long hiBound = prefix[j] - lower;
            int loRank = lowerBoundRank(sorted, loBound); // count of values < loBound
            int hiRank = upperBoundRank(sorted, hiBound);  // count of values <= hiBound
            total += fenwick.prefixSum(hiRank) - fenwick.prefixSum(loRank);
            fenwick.update(rank.get(prefix[j]), 1);
        }
        return total;
    }

    static int lowerBoundRank(long[] sorted, long target) {
        int lo = 0, hi = sorted.length;
        while (lo < hi) {
            int mid = (lo + hi) / 2;
            if (sorted[mid] < target) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    }

    static int upperBoundRank(long[] sorted, long target) {
        int lo = 0, hi = sorted.length;
        while (lo < hi) {
            int mid = (lo + hi) / 2;
            if (sorted[mid] <= target) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    }

    public static void main(String[] args) {
        System.out.println(countRangeSum(new int[]{-2, 5, -1}, -2, 2)); // 3
        System.out.println(countRangeSum(new int[]{0}, 0, 0)); // 1
    }
}
```

**How to run:** save as `CountOfRangeSum.java`, then run `java CountOfRangeSum.java`.

## 6. Walkthrough

Trace the key step for `countRangeSum([-2,5,-1], -2, 2)`, prefix sums `[0, -2, 3, 2]`:

1. Insert `prefix[0]=0`'s rank first.
2. `j=1`, `prefix[1]=-2`. Bounds: `loBound = -2-2=-4`, `hiBound = -2-(-2)=0`. Query counts already-inserted values (`{0}`) in `[-4, 0]` — `0` qualifies, so `count=1`. Total: `1`. Insert `prefix[1]=-2`.
3. `j=2`, `prefix[2]=3`. Bounds: `loBound = 3-2=1`, `hiBound = 3-(-2)=5`. Already-inserted values `{0,-2}` — neither is in `[1,5]`. `count=0`. Total stays `1`. Insert `prefix[2]=3`.
4. `j=3`, `prefix[3]=2`. Bounds: `loBound = 2-2=0`, `hiBound = 2-(-2)=4`. Already-inserted values `{0,-2,3}` — `0` and `3` both fall in `[0,4]`. `count=2`. Total: `1+2=3`.

Final total: `3`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: using plain `int` for prefix sums can overflow when the array is large and values are large — always accumulate prefix sums in `long`, and compress ranks using `Long` keys, not `Integer`.

- Signal: a range condition on subarray sums (`lower <= sum <= upper`) rewrites as a range condition on prefix sums, answered with a Fenwick tree over compressed prefix-sum ranks — the range-query generalization of the single-value lookup used in Subarray Sum Equals K.
- Always insert the empty prefix (`prefixSum[0] = 0`) into the structure before processing any real element, or subarrays starting at index 0 are missed.
- Related problems: Subarray Sum Equals K (the exact-match, hash-map version), Count of Smaller Numbers After Self, Reverse Pairs.
