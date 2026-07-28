---
card: leetcode-patterns
gi: 567
slug: count-of-smaller-numbers-after-self
title: Count of Smaller Numbers After Self
---

## 1. What it is

Given an integer array `nums`, return a new array `counts` where `counts[i]` is the number of elements to the **right** of index `i` that are **smaller** than `nums[i]`. Example: `nums = [5,2,6,1]` → `counts = [2,1,1,0]` (to the right of `5`, both `2` and `1` are smaller — count 2; to the right of `2`, only `1` is smaller — count 1; and so on).

## 2. Why & when

Processing the array from right to left, and asking "how many values already seen are smaller than this one" is the [signal](0560-segment-tree-bit-signal-range-queries-with-point-range-updat.md) for a Fenwick tree over **value ranks**, not array indices: insert each value into the tree as you see it, and query "how many inserted values are less than this one" before inserting the current one. Constraints: up to 100,000 elements, values in a bounded range.

## 3. Core concept

**Key idea:** compress the array's values into **ranks** (1 to the number of distinct values, sorted), so a Fenwick tree of that size can track "how many of each rank have been inserted so far." Process `nums` from right to left: for each element, query the Fenwick tree's prefix sum up to `rank - 1` (how many smaller values have already been inserted, since we are going right to left, "already inserted" means "to the right"), record that as the answer, then insert this element's rank into the tree.

**Steps:**
1. Build a sorted list of distinct values from `nums`, and a map from value to its 1-indexed rank in that sorted list (coordinate compression, needed since raw values can be large or negative).
2. Initialize a Fenwick tree sized to the number of distinct values.
3. Process `nums` from the last index to the first: for `nums[i]`, look up its `rank`. Query `prefixSum(rank - 1)` — the count of already-inserted (i.e., to the right) values strictly smaller than `nums[i]`. Store this as `counts[i]`.
4. Update the Fenwick tree: add `1` at `rank`, recording that this value has now been "seen."
5. Return `counts`.

**Why processing right to left (not left to right) matches the problem's definition:** the problem asks for smaller elements *after* each index. Scanning from the right and inserting into the Fenwick tree as you go means that, by the time you query for index `i`, every element already inserted is exactly the set of elements to `i`'s right — precisely what the query needs to count.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Processing [5,2,6,1] from right to left, querying the Fenwick tree before inserting each value">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">nums = [5,2,6,1], ranks: 1-&gt;1, 2-&gt;2, 5-&gt;3, 6-&gt;4</text>
    <text x="20" y="50" fill="#8b949e">i=3 (val 1, rank 1): query prefixSum(0)=0. insert rank 1.</text>
    <text x="20" y="75" fill="#8b949e">i=2 (val 6, rank 4): query prefixSum(3)=1 (rank 1 inserted). insert rank 4.</text>
    <text x="20" y="100" fill="#8b949e">i=1 (val 2, rank 2): query prefixSum(1)=1 (rank 1 inserted). insert rank 2.</text>
    <text x="20" y="125" fill="#3fb950">i=0 (val 5, rank 3): query prefixSum(2)=2 (ranks 1,2 inserted). insert rank 3. counts=[2,1,1,0]</text>
  </g>
</svg>

Each query counts how many smaller-ranked values have already been inserted — exactly the elements already processed, which are the ones to the current index's right.

## 5. Runnable example

**Level 1 — Brute force.** For each index, scan every index to its right, counting smaller values directly. O(n²).

**KEY INSIGHT:** a Fenwick tree over value ranks turns "how many smaller values have I seen so far" into an O(log n) prefix-sum query, processed in one right-to-left pass.

**Level 2 — Optimal.** Coordinate compression plus a Fenwick tree, O(n log n).

**Level 3 — Hardened.** Handles duplicate values (compression maps equal values to the same rank, and the strict "smaller than" query correctly excludes equal values via `rank - 1`) and negative numbers (compression handles any value range uniformly).

```java
// CountSmallerAfterSelf.java
import java.util.*;

public class CountSmallerAfterSelf {

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

    static List<Integer> countSmaller(int[] nums) {
        int[] sorted = nums.clone();
        Arrays.sort(sorted);
        Map<Integer, Integer> rank = new HashMap<>();
        int r = 0;
        for (int val : sorted) {
            if (!rank.containsKey(val)) rank.put(val, ++r);
        }

        Fenwick fenwick = new Fenwick(rank.size());
        Integer[] counts = new Integer[nums.length];
        for (int i = nums.length - 1; i >= 0; i--) {
            int valRank = rank.get(nums[i]);
            counts[i] = fenwick.prefixSum(valRank - 1);
            fenwick.update(valRank, 1);
        }
        return Arrays.asList(counts);
    }

    public static void main(String[] args) {
        System.out.println(countSmaller(new int[]{5, 2, 6, 1})); // [2, 1, 1, 0]
        System.out.println(countSmaller(new int[]{-1, -1})); // [0, 0], duplicates
    }
}
```

**How to run:** save as `CountSmallerAfterSelf.java`, then run `java CountSmallerAfterSelf.java`.

## 6. Walkthrough

Trace `countSmaller([5,2,6,1])`, ranks `1->1, 2->2, 5->3, 6->4`:

| i | value | rank | prefixSum(rank-1) | counts[i] | fenwick after insert |
|---|---|---|---|---|---|
| 3 | 1 | 1 | prefixSum(0)=0 | 0 | {1} |
| 2 | 6 | 4 | prefixSum(3)=1 (rank 1 seen) | 1 | {1,4} |
| 1 | 2 | 2 | prefixSum(1)=1 (rank 1 seen) | 1 | {1,2,4} |
| 0 | 5 | 3 | prefixSum(2)=2 (ranks 1,2 seen) | 2 | {1,2,3,4} |

Final `counts = [2,1,1,0]`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: querying `prefixSum(rank)` instead of `prefixSum(rank - 1)` incorrectly counts values *equal to* the current element as "smaller," since the Fenwick tree's rank for equal values is identical — always subtract 1 to get a strict "less than" count.

- Signal: "count smaller/larger elements to one side, as you scan the array" is solved by inserting into a Fenwick tree over compressed value ranks, one element at a time, in the direction that matches the problem's "before/after" requirement.
- Coordinate compression is required whenever raw values are too large, sparse, or negative to index a Fenwick tree directly.
- Related problems: Reverse Pairs (a related but trickier ratio condition), Count of Range Sum (counts smaller ranges, not smaller elements).
