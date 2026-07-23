---
card: leetcode-patterns
gi: 240
slug: find-peak-element
title: Find Peak Element
---

## 1. What it is

A peak element is one that is strictly greater than both its neighbors (treat elements outside the array as negative infinity). Given `nums`, return the index of ANY peak. Example: `nums = [1,2,3,1]` → `2` (value `3` is a peak: greater than `2` on the left and `1` on the right).

## 2. Why & when

Even though `nums` is not sorted, the SLOPE at any point (whether it is climbing or falling) is enough information to binary search, because moving in the direction of a climbing slope is guaranteed to lead toward a peak. Use this shape whenever a problem allows ANY valid answer among possibly several, and there is a local comparison (not a global sort) that still lets you discard half the search space.

## 3. Core concept

**Key idea:** at any index `mid`, compare `nums[mid]` to `nums[mid + 1]`. If `nums[mid] < nums[mid + 1]`, the array is climbing at `mid`, so a peak must exist somewhere to the right (worst case, the very last element, since the array is treated as bounded by negative infinity beyond its edges). If `nums[mid] > nums[mid + 1]`, the array is falling, so a peak must exist at `mid` or to its left.

**Steps:**
1. Set `lo = 0`, `hi = nums.length - 1`.
2. While `lo < hi`: compute `mid = lo + (hi - lo) / 2`.
3. If `nums[mid] < nums[mid + 1]`, the slope is climbing: set `lo = mid + 1`.
4. Otherwise, the slope is falling (or flat at a peak): set `hi = mid`.
5. When the loop ends, `lo == hi` is the index of a peak.

**Why it is correct:** if `nums[mid] < nums[mid + 1]`, then following that upward slope guarantees a peak exists at `mid + 1` or further right — you can never "run out" of climbing room without hitting a peak, because the array's boundary counts as negative infinity. Symmetrically, a falling or equal slope at `mid` guarantees a peak at `mid` or to its left. Either way, one comparison discards half the search space with certainty, and the two bounds converge on a valid peak index.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Array 1 2 3 1, climbing slope at index 0 to 1 to 2, then falling to index 3, peak at index 2">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [1, 2, 3, 1]</text>
    <rect x="10" y="90" width="30" height="20" fill="#161b22" stroke="#30363d"/><text x="25" y="105" text-anchor="middle" font-size="9">1</text>
    <rect x="40" y="70" width="30" height="40" fill="#161b22" stroke="#30363d"/><text x="55" y="105" text-anchor="middle" font-size="9">2</text>
    <rect x="70" y="30" width="30" height="80" fill="#3fb950"/><text x="85" y="105" fill="#0d1117" text-anchor="middle" font-size="9">3</text>
    <rect x="100" y="90" width="30" height="20" fill="#161b22" stroke="#30363d"/><text x="115" y="105" text-anchor="middle" font-size="9">1</text>
    <text x="10" y="135">climbing 1&lt;2&lt;3, then falling 3&gt;1: peak at index 2</text>
  </g>
</svg>

Comparing `nums[mid]` to its right neighbor tells you which direction is "uphill," and a peak always exists in that direction.

## 5. Runnable example

```java
// FindPeakElement.java
public class FindPeakElement {

    // Level 1 -- Brute force: scan every index, comparing each
    // element to both neighbors (treating out-of-bounds as negative
    // infinity), and return the first index that is a peak. Correct,
    // but O(n) -- ignores that the local slope alone can guide a
    // faster search.

    // KEY INSIGHT: comparing nums[mid] to nums[mid+1] tells you which
    // direction guarantees a peak, letting you discard half the array
    // per comparison, without the array being globally sorted at all.

    // Level 2 -- Optimal: binary search following the upward slope.
    static int findPeakElement(int[] nums) {
        int lo = 0, hi = nums.length - 1;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] < nums[mid + 1]) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    }

    // Level 3 -- Hardened: works unchanged for a single-element array
    // (loop never runs, lo=hi=0 is trivially a peak) and for a fully
    // increasing or fully decreasing array (converges on the last or
    // first index respectively).

    public static void main(String[] args) {
        System.out.println(findPeakElement(new int[]{1, 2, 3, 1}));
        // 2
        System.out.println(findPeakElement(new int[]{1, 2, 1, 3, 5, 6, 4}));
        // 1 or 5, both valid peaks
    }
}
```

**How to run:** `java FindPeakElement.java`

## 6. Walkthrough

Trace `findPeakElement(nums)` on `nums = [1,2,3,1]`:

| lo | hi | mid | nums[mid] | nums[mid+1] | comparison | action |
|---|---|---|---|---|---|---|
| 0 | 3 | 1 | 2 | 3 | 2 < 3 (climbing) | lo = 2 |
| 2 | 3 | 2 | 3 | 1 | 3 > 1 (falling) | hi = 2 |
| 2 | 2 | — | — | — | loop ends | return 2 |

Index `2` (value `3`) is confirmed a peak: greater than `nums[1]=2` and `nums[3]=1`. Time complexity is O(log n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: the problem only guarantees finding A peak, not THE global maximum — for `nums = [1,2,1,3,5,6,4]`, both index `1` (value `2`) and index `5` (value `6`) are valid peaks, and this algorithm may return either depending on which slope it follows first.

- The array does not need to be sorted at all — only the LOCAL slope at each comparison matters, which is what makes this a binary search problem despite the unsorted input.
- Treating both ends of the array as bounded by negative infinity is what guarantees a peak always exists, so the search never runs off the edge without an answer.
- Related problems: Peak Index in a Mountain Array (a constrained version where the array is guaranteed to have exactly one peak), Search in Rotated Sorted Array (another binary search over a non-globally-sorted array).
