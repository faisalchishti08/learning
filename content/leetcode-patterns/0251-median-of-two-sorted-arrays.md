---
card: leetcode-patterns
gi: 251
slug: median-of-two-sorted-arrays
title: Median of Two Sorted Arrays
---

## 1. What it is

Given two sorted arrays `nums1` and `nums2`, return the median of the combined sorted array, in O(log(min(m, n))) time. Example: `nums1 = [1,3]`, `nums2 = [2]` → `2.0`; `nums1 = [1,2]`, `nums2 = [3,4]` → `2.5`.

## 2. Why & when

Merging both arrays and finding the middle is easy but O(m + n). The O(log(min(m, n))) requirement is a strong signal for binary search on a PARTITION point, not on a value — you search for the split that divides both arrays' combined elements evenly, without ever merging them. Use this shape whenever a problem demands sub-linear time to find a positional statistic (median, a specific rank) across two or more sorted sequences.

## 3. Core concept

**Key idea:** binary search on how many elements to take from the SMALLER array's left side. Call it `cut1` (from `0` to `m`, the smaller array's length). The number to take from the larger array's left side is then forced: `cut2 = (m + n + 1) / 2 - cut1`, so the two left halves together always hold exactly half (or half, rounded up) of all elements. A partition is correct when every element in the left halves is `<=` every element in the right halves.

**Steps:**
1. Ensure `nums1` is the shorter array (swap if needed), so the binary search runs over the smaller length `m`.
2. Set `lo = 0`, `hi = m`.
3. While `lo <= hi`: `cut1 = lo + (hi - lo) / 2`, `cut2 = (m + n + 1) / 2 - cut1`.
4. Read the four boundary values: `left1 = nums1[cut1-1]` (or -infinity if `cut1==0`), `right1 = nums1[cut1]` (or +infinity if `cut1==m`), and the same for `left2`/`right2` from `nums2`.
5. If `left1 <= right2` AND `left2 <= right1`, the partition is correct: compute the median from these four boundary values and return.
6. If `left1 > right2`, `cut1` is too far right: set `hi = cut1 - 1`.
7. Otherwise, `cut1` is too far left: set `lo = cut1 + 1`.

**Why it is correct:** any valid partition of the combined array into a left half and a right half of the correct sizes must satisfy "every left element `<=` every right element." Because both arrays are individually sorted, checking just the four boundary values (`left1`, `right1`, `left2`, `right2`) is enough to confirm this for the WHOLE partition. As `cut1` increases, `left1` grows and `left2`'s counterpart on the other side shrinks in a monotonic way, so binary search on `cut1` converges to the unique valid partition.

## 4. Diagram

<svg viewBox="0 0 460 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="nums1 1 3 and nums2 2 partitioned so left half is 1,2 and right half is 3, median from boundary values">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums1 = [1, 3], nums2 = [2]</text>
    <rect x="10" y="30" width="30" height="24" fill="#3fb950"/><text x="25" y="47" fill="#0d1117" text-anchor="middle" font-size="9">1</text>
    <rect x="40" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="55" y="47" text-anchor="middle" font-size="9">3</text>
    <text x="10" y="80">cut1=1: left1=1, right1=3</text>
    <rect x="10" y="90" width="30" height="24" fill="#3fb950"/><text x="25" y="107" fill="#0d1117" text-anchor="middle" font-size="9">2</text>
    <text x="10" y="140">cut2=1: left2=2, right2=+inf</text>
    <text x="10" y="160">left1(1)&lt;=right2(+inf) and left2(2)&lt;=right1(3): valid; median=max(1,2)=2</text>
  </g>
</svg>

Only the four boundary values around a candidate cut need checking to confirm the whole partition is valid, since each array is already sorted internally.

## 5. Runnable example

```java
// MedianOfTwoSortedArrays.java
public class MedianOfTwoSortedArrays {

    // Level 1 -- Brute force: merge both arrays into one sorted array
    // (or merge just far enough to reach the middle), then read off
    // the median. Correct, but O(m + n) -- does not meet the required
    // O(log(min(m,n))) bound.

    // KEY INSIGHT: you never need to merge anything. Binary search
    // directly for the PARTITION point where the combined left half
    // and right half are correctly ordered, checked using only four
    // boundary values.

    // Level 2 -- Optimal: binary search on the partition index.
    static double findMedianSortedArrays(int[] nums1, int[] nums2) {
        if (nums1.length > nums2.length) return findMedianSortedArrays(nums2, nums1);

        int m = nums1.length, n = nums2.length;
        int lo = 0, hi = m;
        while (lo <= hi) {
            int cut1 = lo + (hi - lo) / 2;
            int cut2 = (m + n + 1) / 2 - cut1;

            int left1 = cut1 == 0 ? Integer.MIN_VALUE : nums1[cut1 - 1];
            int right1 = cut1 == m ? Integer.MAX_VALUE : nums1[cut1];
            int left2 = cut2 == 0 ? Integer.MIN_VALUE : nums2[cut2 - 1];
            int right2 = cut2 == n ? Integer.MAX_VALUE : nums2[cut2];

            if (left1 <= right2 && left2 <= right1) {
                if ((m + n) % 2 == 0) {
                    return (Math.max(left1, left2) + Math.min(right1, right2)) / 2.0;
                } else {
                    return Math.max(left1, left2);
                }
            } else if (left1 > right2) {
                hi = cut1 - 1;
            } else {
                lo = cut1 + 1;
            }
        }
        throw new IllegalArgumentException("input arrays are not sorted");
    }

    // Level 3 -- Hardened: always binary searches on the SHORTER
    // array (swapping if needed), guaranteeing the O(log(min(m,n)))
    // bound instead of accidentally searching the longer one.

    public static void main(String[] args) {
        System.out.println(findMedianSortedArrays(new int[]{1, 3}, new int[]{2}));
        // 2.0
        System.out.println(findMedianSortedArrays(new int[]{1, 2}, new int[]{3, 4}));
        // 2.5
    }
}
```

**How to run:** `java MedianOfTwoSortedArrays.java`

## 6. Walkthrough

Trace `findMedianSortedArrays([1,2], [3,4])`, `m=2, n=2`, `lo=0, hi=2`:

| lo | hi | cut1 | cut2 | left1,right1 | left2,right2 | valid? | action |
|---|---|---|---|---|---|---|---|
| 0 | 2 | 1 | 1 | 1, 2 | 3, 4 | left1(1)<=right2(4) and left2(3)<=right1(2)? no (3>2) | lo = 2 |
| 2 | 2 | 2 | 0 | 2, +inf | -inf, 3 | left1(2)<=right2(3) and left2(-inf)<=right1(+inf)? yes | valid |

Combined length is even, so median is `(max(2,-inf) + min(+inf,3)) / 2 = (2 + 3) / 2 = 2.5`, matching the expected answer. Time complexity is O(log(min(m, n))). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: always binary searching on the shorter array (swapping the arguments if `nums1` is longer) is required both for correctness of the `cut2` formula's bounds and for meeting the O(log(min(m,n))) time requirement — searching on the longer array can leave `cut2` out of its valid `[0, n]` range.

- The four boundary values (using `Integer.MIN_VALUE`/`MAX_VALUE` as sentinels for an empty side) let a single comparison confirm the WHOLE partition is valid, thanks to each array already being internally sorted.
- This is the hardest problem in this section because it binary searches on a PARTITION INDEX, not a value or a simple monotonic predicate — the "correctness" condition itself is a two-part comparison.
- Related problems: Kth Smallest Number in Multiplication Table (a different two-dimensional binary search), Split Array Largest Sum (another binary search where the check function does real work per candidate).
