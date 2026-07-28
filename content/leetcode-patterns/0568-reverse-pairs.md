---
card: leetcode-patterns
gi: 568
slug: reverse-pairs
title: Reverse Pairs
---

## 1. What it is

Given an integer array `nums`, count the number of pairs `(i, j)` where `i < j` **and** `nums[i] > 2 * nums[j]`. Example: `nums = [1,3,2,3,1]` → `2` (pairs `(1,4)`: `3 > 2*1`, and `(3,4)`: `3 > 2*1`).

## 2. Why & when

This looks like [Count of Smaller Numbers After Self](0567-count-of-smaller-numbers-after-self.md), but the condition `nums[i] > 2 * nums[j]` is not a simple "smaller than" comparison — it involves a scaling factor, which breaks a naive single-pass Fenwick-tree-while-scanning approach unless handled carefully. Process the array from right to left exactly as before, but for each `nums[i]`, first **query** how many already-seen values `nums[j]` satisfy `nums[j] < nums[i] / 2.0`, *before* inserting `nums[i]` itself. Constraints: up to 50,000 elements.

## 3. Core concept

**Key idea:** same right-to-left Fenwick-tree-over-ranks scan as before, but the query condition changes: for index `i`, count how many already-inserted values `nums[j]` (which are all at indices `j > i`, since we go right to left) satisfy `nums[j] < nums[i] / 2.0`, equivalently `2 * nums[j] < nums[i]`. Because ranks are precomputed once from the *original* array, this query must be phrased as "how many already-inserted ranks are less than the rank of the largest value strictly less than `nums[i] / 2.0`" — found via a binary search on the sorted distinct values.

**Steps:**
1. Build a sorted list of distinct values from `nums`, and a rank map (coordinate compression).
2. Initialize a Fenwick tree sized to the number of distinct values.
3. Process `nums` from the last index to the first: for `nums[i]`, binary-search the sorted distinct values for the count of values strictly less than `nums[i] / 2.0` (equivalently, values `v` with `2 * v < nums[i]`) — this count corresponds to a rank boundary; query the Fenwick tree's prefix sum up to that rank boundary.
4. Add the query result to a running total.
5. Insert `nums[i]`'s own rank into the Fenwick tree.
6. Return the running total.

**Why the query must use a *different* threshold than the value being inserted:** unlike a plain "count smaller" query, this problem's condition (`nums[i] > 2 * nums[j]`, i.e. `nums[j] < nums[i] / 2.0`) means the boundary value being searched for (`nums[i] / 2.0`) is not itself one of the array's actual values — a direct rank lookup does not work, and a binary search over the sorted distinct values is needed to find how many of them fall below that computed threshold.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="For value 3, the threshold is 1.5, so query counts how many already-inserted values are below 1.5">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">processing nums[i] = 3: threshold = 3 / 2.0 = 1.5</text>
    <text x="20" y="50" fill="#79c0ff">binary search sorted distinct values for count &lt; 1.5</text>
    <text x="20" y="80" fill="#3fb950">query fenwick.prefixSum(that count) -&gt; number of already-seen values satisfying nums[j] &lt; 1.5</text>
    <text x="20" y="115" fill="#f0883e">then separately insert value 3's own rank (a different rank than the query used)</text>
  </g>
</svg>

The query threshold (`nums[i] / 2.0`) is computed fresh for each element and is generally not one of the array's own values, requiring a binary search rather than a direct rank lookup.

## 5. Runnable example

**Level 1 — Brute force.** For every pair `(i, j)` with `i < j`, check `nums[i] > 2 * nums[j]` directly. O(n²).

**KEY INSIGHT:** the same right-to-left Fenwick tree scan from Count of Smaller Numbers After Self applies here, but the query threshold must be computed as `nums[i] / 2.0` and located via binary search, since it is not a value that was itself compressed into a rank.

**Level 2 — Optimal.** Coordinate compression, Fenwick tree, and a binary search per query, O(n log n).

**Level 3 — Hardened.** Handles negative numbers (the `/2.0` division and comparison logic works the same way for negatives) and potential integer overflow (`2 * nums[j]` can overflow `int` for large values — use `long` arithmetic in the comparison).

```java
// ReversePairs.java
import java.util.*;

public class ReversePairs {

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

    static int reversePairs(int[] nums) {
        int[] sorted = nums.clone();
        Arrays.sort(sorted);
        Map<Integer, Integer> rank = new HashMap<>();
        int r = 0;
        for (int val : sorted) {
            if (!rank.containsKey(val)) rank.put(val, ++r);
        }

        Fenwick fenwick = new Fenwick(rank.size());
        int total = 0;

        for (int i = nums.length - 1; i >= 0; i--) {
            // count how many distinct sorted values v satisfy 2L * v < nums[i]
            int lo = 0, hi = sorted.length; // binary search for first index NOT satisfying 2*v < nums[i]
            while (lo < hi) {
                int mid = (lo + hi) / 2;
                if (2L * sorted[mid] < nums[i]) lo = mid + 1;
                else hi = mid;
            }
            // lo = count of sorted values with 2*v < nums[i]
            total += fenwick.prefixSum(lo); // ranks 1..lo correspond to sorted[0..lo-1]

            fenwick.update(rank.get(nums[i]), 1);
        }
        return total;
    }

    public static void main(String[] args) {
        System.out.println(reversePairs(new int[]{1, 3, 2, 3, 1})); // 2
        System.out.println(reversePairs(new int[]{2, 4, 3, 5, 1})); // 3
    }
}
```

**How to run:** save as `ReversePairs.java`, then run `java ReversePairs.java`.

## 6. Walkthrough

Trace `reversePairs([1,3,2,3,1])`, sorted distinct values `[1,2,3]`:

| i | nums[i] | binary search: count of v with 2v < nums[i] | fenwick prefixSum(that count) | running total | insert |
|---|---|---|---|---|---|
| 4 | 1 | none (2*1=2 not < 1) -> 0 | prefixSum(0)=0 | 0 | rank(1)=1 |
| 3 | 3 | v=1: 2<3 yes; v=2: 4<3 no -> 1 | prefixSum(1)=1 (rank 1 present) | 1 | rank(3)=3 |
| 2 | 2 | v=1: 2<2 no -> 0 | prefixSum(0)=0 | 1 | rank(2)=2 |
| 1 | 3 | count=1 (same as before) | prefixSum(1)=1 (rank 1 present) | 2 | rank(3)=3 |
| 0 | 1 | count=0 | prefixSum(0)=0 | 2 | rank(1)=1 |

Final total: `2`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: computing `2 * nums[j] < nums[i]` using plain `int` arithmetic can silently overflow for large input values — cast to `long` (as `2L * sorted[mid]`) before comparing, to avoid a wrapped-around, incorrect comparison result.

- Signal: a "count pairs satisfying a scaled/shifted comparison" problem still fits the right-to-left Fenwick-tree-over-ranks pattern, but the query threshold must be computed per element and located via binary search, not a direct rank lookup.
- Query for the count *before* inserting the current element's own rank, exactly as in the simpler "count smaller" variant — this keeps `i < j` correctly enforced.
- Related problems: Count of Smaller Numbers After Self (the direct, unscaled version), Count of Range Sum (a prefix-sum-based comparison instead of an element-based one).
