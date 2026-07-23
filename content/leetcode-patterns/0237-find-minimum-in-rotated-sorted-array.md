---
card: leetcode-patterns
gi: 237
slug: find-minimum-in-rotated-sorted-array
title: Find Minimum in Rotated Sorted Array
---

## 1. What it is

A sorted array with distinct values has been rotated at some unknown pivot. Find the minimum element in O(log n) time. Example: `nums = [4,5,6,7,0,1,2]` → `0`; `nums = [3,4,5,1,2]` → `1`.

## 2. Why & when

The minimum element is exactly the rotation point — the one place where a larger value is immediately followed by a smaller one. Use this shape whenever you need to locate the "seam" in a rotated sorted array, either as the final answer or as a first step before searching for a specific target (see Search in Rotated Sorted Array).

## 3. Core concept

**Key idea:** compare `nums[mid]` to `nums[hi]`. If `nums[mid] > nums[hi]`, the rotation point (and therefore the minimum) must be somewhere to the RIGHT of `mid`, since a value greater than the rightmost element means the array is still "high" at `mid` and hasn't dropped yet. If `nums[mid] <= nums[hi]`, the right half from `mid` onward is already sorted, so the minimum is at `mid` or to its LEFT.

**Steps:**
1. Set `lo = 0`, `hi = nums.length - 1`.
2. While `lo < hi`: compute `mid = lo + (hi - lo) / 2`.
3. If `nums[mid] > nums[hi]`, the minimum is to the right of `mid`: set `lo = mid + 1`.
4. Otherwise, the minimum is at `mid` or to its left: set `hi = mid`.
5. When the loop ends, `lo == hi` is the index of the minimum element.

**Why it is correct:** comparing against `nums[hi]` (not `nums[lo]`) is what makes this work with a `hi = mid` (not `mid - 1`) update: `mid` is never ruled out when `nums[mid] <= nums[hi]`, because `mid` itself could BE the minimum. Every step, either the minimum is confirmed to the right of `mid` (safe to move `lo` past it), or `mid` remains a valid candidate for the minimum (keep it in range with `hi = mid`). The two bounds converge exactly on the rotation point.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Rotated array 4 5 6 7 0 1 2, comparing nums mid to nums hi to find the drop point at index 4">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [4,5,6,7,0,1,2]</text>
    <rect x="10" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="25" y="47" text-anchor="middle" font-size="9">4</text>
    <rect x="40" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="55" y="47" text-anchor="middle" font-size="9">5</text>
    <rect x="70" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="85" y="47" text-anchor="middle" font-size="9">6</text>
    <rect x="100" y="30" width="30" height="24" fill="#e3b341"/><text x="115" y="47" fill="#0d1117" text-anchor="middle" font-size="9">7 mid</text>
    <rect x="130" y="30" width="30" height="24" fill="#3fb950"/><text x="145" y="47" fill="#0d1117" text-anchor="middle" font-size="9">0</text>
    <rect x="160" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="175" y="47" text-anchor="middle" font-size="9">1</text>
    <rect x="190" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="205" y="47" text-anchor="middle" font-size="9">2 hi</text>
    <text x="10" y="80">nums[mid]=7 &gt; nums[hi]=2 -&gt; minimum is right of mid</text>
    <text x="10" y="105">lo = mid + 1 = 4; converges on index 4 (value 0)</text>
  </g>
</svg>

The comparison against `nums[hi]` tells you which side of `mid` the "drop" from high values to low values happens on.

## 5. Runnable example

```java
// FindMinimumInRotatedSortedArray.java
public class FindMinimumInRotatedSortedArray {

    // Level 1 -- Brute force: scan every element, tracking the
    // smallest seen. Correct, but O(n) -- ignores that the array is
    // sorted except for one rotation point.

    // KEY INSIGHT: comparing nums[mid] to nums[hi] tells you which
    // side of mid the rotation point (the minimum) is on, letting you
    // discard half the array each step, exactly like plain binary
    // search but hunting for the "seam" instead of a target value.

    // Level 2 -- Optimal: binary search for the rotation point.
    static int findMin(int[] nums) {
        int lo = 0, hi = nums.length - 1;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] > nums[hi]) lo = mid + 1;
            else hi = mid;
        }
        return nums[lo];
    }

    // Level 3 -- Hardened: works unchanged when the array is NOT
    // rotated at all (nums[mid] <= nums[hi] holds throughout, so hi
    // converges down to index 0, the true minimum).

    public static void main(String[] args) {
        System.out.println(findMin(new int[]{4, 5, 6, 7, 0, 1, 2}));
        // 0
        System.out.println(findMin(new int[]{3, 4, 5, 1, 2}));
        // 1
        System.out.println(findMin(new int[]{1, 2, 3, 4, 5}));
        // 1 (not rotated)
    }
}
```

**How to run:** `java FindMinimumInRotatedSortedArray.java`

## 6. Walkthrough

Trace `findMin(nums)` on `nums = [4,5,6,7,0,1,2]`:

| lo | hi | mid | nums[mid] | nums[hi] | comparison | action |
|---|---|---|---|---|---|---|
| 0 | 6 | 3 | 7 | 2 | 7 > 2 | lo = 4 |
| 4 | 6 | 5 | 1 | 2 | 1 <= 2 | hi = 5 |
| 4 | 5 | 4 | 0 | 1 | 0 <= 1 | hi = 4 |
| 4 | 4 | — | — | — | loop ends | return nums[4] = 0 |

Found the minimum, `0`, in 3 comparisons instead of scanning all 7 elements. Time complexity is O(log n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: comparing `nums[mid]` to `nums[lo]` instead of `nums[hi]` is a common mistake here — it works for Search in Rotated Sorted Array's "which half is sorted" question, but for finding the minimum specifically, comparing against `nums[hi]` is what lets you safely use `hi = mid` (keeping `mid` as a candidate) instead of always excluding it.

- This is effectively the "search on answer" template applied to array indices: the predicate is "is index `mid` at or before the rotation point," which is monotonic across the array.
- The result of this search (the rotation point index) is exactly the pivot that Search in Rotated Sorted Array must reason about implicitly — solving this problem first is a valid way to simplify that one.
- Related problems: Search in Rotated Sorted Array (uses the same sorted-half reasoning to locate a target instead of the minimum), Binary Search (the un-rotated base case).
