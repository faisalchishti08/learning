---
card: leetcode-patterns
gi: 457
slug: partition-array-into-disjoint-intervals
title: Partition Array into Disjoint Intervals
---

## 1. What it is

Split an array into a LEFT part and a RIGHT part (both non-empty) such that EVERY element in the left part is `<=` EVERY element in the right part, and the left part is as SHORT as possible. Return the length of the left part. Example: `nums = [5,0,3,8,6]` → `3` (left = `[5,0,3]`, right = `[8,6]`).

## 2. Why & when

Use this shape whenever a problem asks for the EARLIEST valid split point of an array, where a global ordering condition (every left element `<=` every right element) must hold. The greedy rule: track the maximum value seen SO FAR in a candidate left partition, and the maximum value seen ANYWHERE so far; whenever a new element is SMALLER than the candidate partition's maximum, the partition must extend to include it.

## 3. Core concept

**Key idea:** track `leftMax` (the maximum allowed value for the CURRENT candidate left partition) and `overallMax` (the maximum value seen anywhere in the scan so far). Track `partitionIndex`, the current best candidate for where the left partition ends.

**Steps:**
1. Initialize `leftMax = overallMax = nums[0]`, `partitionIndex = 0`.
2. For each `i` from `1` to `n-1`: update `overallMax = max(overallMax, nums[i])`.
3. If `nums[i] < leftMax`, this element is SMALLER than something already committed to the left partition, so the partition MUST extend to include index `i`: set `leftMax = overallMax` (the partition's new ceiling is everything seen so far) and `partitionIndex = i`.
4. Return `partitionIndex + 1` (the LENGTH of the left partition).

**Why extending the partition to `overallMax` (not just to `nums[i]`) is correct:** the moment `nums[i]` violates the CURRENT candidate partition (`nums[i] < leftMax`), the partition must grow to absorb `nums[i]` — but since the partition boundary can only move FORWARD, every value between the old boundary and `i` (whatever the largest of them was, `overallMax`) is now ALSO inside the left partition, and must be respected as the new ceiling for anything still to come.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a candidate partition boundary forced to extend forward whenever a later element is smaller than the current left partitions maximum">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [5, 0, 3, 8, 6]</text>
    <text x="10" y="45">i=1 (0): 0 &lt; leftMax(5) -- extend: leftMax=overallMax=5, partitionIndex=1</text>
    <text x="10" y="65">i=2 (3): 3 &lt; leftMax(5) -- extend: leftMax=overallMax=5, partitionIndex=2</text>
    <rect x="10" y="85" width="280" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">i=3 (8), i=4 (6): both &gt;= 5 -- partition stays at index 2, length 3</text>
  </g>
</svg>

Any element smaller than the current partition's ceiling forces the partition boundary to move forward and absorb it.

## 5. Runnable example

```java
// PartitionArrayIntoDisjointIntervals.java
public class PartitionArrayIntoDisjointIntervals {

    // KEY INSIGHT: an element smaller than the current partition's max
    // forces the partition to extend and absorb everything up to it --
    // the new ceiling becomes the overall max seen so far.

    static int partitionDisjoint(int[] nums) {
        int leftMax = nums[0], overallMax = nums[0], partitionIndex = 0;
        for (int i = 1; i < nums.length; i++) {
            overallMax = Math.max(overallMax, nums[i]);
            if (nums[i] < leftMax) {
                leftMax = overallMax;
                partitionIndex = i;
            }
        }
        return partitionIndex + 1;
    }

    public static void main(String[] args) {
        System.out.println(partitionDisjoint(new int[]{5, 0, 3, 8, 6}));
        // 3
        System.out.println(partitionDisjoint(new int[]{1, 1, 1, 0, 6, 12}));
        // 4
    }
}
```

**How to run:** `java PartitionArrayIntoDisjointIntervals.java`

## 6. Walkthrough

Trace `partitionDisjoint([5,0,3,8,6])`:

| i | nums[i] | overallMax after | nums[i] < leftMax? | leftMax after | partitionIndex after |
|---|---|---|---|---|---|
| 1 | 0 | 5 | 0 < 5? yes | 5 | 1 |
| 2 | 3 | 5 | 3 < 5? yes | 5 | 2 |
| 3 | 8 | 8 | 8 < 5? no | 5 | 2 |
| 4 | 6 | 8 | 6 < 5? no | 5 | 2 |

Final `partitionIndex = 2`, so the returned length is `3`, matching the expected answer. Time complexity is O(n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: setting `leftMax = nums[i]` instead of `leftMax = overallMax` on an extension is a common mistake — the new left partition includes EVERYTHING up to index `i`, not just `nums[i]` itself, so its ceiling must be the LARGEST value across that whole extended range, which is exactly `overallMax`.

- Two running maximums (`leftMax` for the current partition, `overallMax` for everything seen) working together: `overallMax` becomes the NEW `leftMax` whenever the partition needs to grow.
- The partition only ever moves FORWARD — once `partitionIndex` advances, it never needs to reconsider an earlier position, making this a genuine single, linear pass.
- Related problems: Non-decreasing Array (a different single-pass structural check, focused on fixing a single local violation rather than finding a global split point).
