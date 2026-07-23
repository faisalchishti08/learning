---
card: leetcode-patterns
gi: 245
slug: peak-index-in-a-mountain-array
title: Peak Index in a Mountain Array
---

## 1. What it is

A "mountain array" strictly increases, then strictly decreases, guaranteed to have exactly one peak. Given such an array `arr`, return the index of that peak. Example: `arr = [0,2,4,6,8,3,1]` → `4` (value `8` is the unique peak).

## 2. Why & when

This is a restricted, guaranteed-single-peak version of Find Peak Element. Use it whenever a problem explicitly promises a "mountain" shape (strictly up, then strictly down, exactly one peak), since it lets you use the same slope-following binary search with a simpler mental model — there's only ever one right answer, not several valid peaks.

## 3. Core concept

**Key idea:** at any index `mid` (except the last), compare `arr[mid]` to `arr[mid + 1]`. If `arr[mid] < arr[mid + 1]`, you are still on the increasing side, so the peak is to the right. If `arr[mid] > arr[mid + 1]`, you are on the decreasing side (or exactly at the peak), so the peak is at `mid` or to its left.

**Steps:**
1. Set `lo = 0`, `hi = arr.length - 1`.
2. While `lo < hi`: compute `mid = lo + (hi - lo) / 2`.
3. If `arr[mid] < arr[mid + 1]`, still climbing: set `lo = mid + 1`.
4. Otherwise, past the peak or at it: set `hi = mid`.
5. When the loop ends, `lo == hi` is the peak index.

**Why it is correct:** the mountain guarantee means the slope changes direction EXACTLY once, so "is `arr[mid] < arr[mid + 1]`?" is a clean monotonic condition — true for every index before the peak, false from the peak onward. Binary search finds that exact flip point directly, and because the mountain shape guarantees uniqueness, the found index is THE peak, not just a valid one among several.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Mountain array 0 2 4 6 8 3 1, climbing to index 4, then falling, peak at index 4">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">arr = [0, 2, 4, 6, 8, 3, 1]</text>
    <rect x="10" y="100" width="25" height="10" fill="#161b22" stroke="#30363d"/>
    <rect x="40" y="85" width="25" height="25" fill="#161b22" stroke="#30363d"/>
    <rect x="70" y="65" width="25" height="45" fill="#161b22" stroke="#30363d"/>
    <rect x="100" y="45" width="25" height="65" fill="#161b22" stroke="#30363d"/>
    <rect x="130" y="30" width="25" height="80" fill="#3fb950"/><text x="142" y="25" fill="#3fb950" font-size="10" text-anchor="middle">peak</text>
    <rect x="160" y="80" width="25" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="190" y="100" width="25" height="10" fill="#161b22" stroke="#30363d"/>
    <text x="10" y="135">indices 0-4 climbing, index 4 is the peak, indices 4-6 falling</text>
  </g>
</svg>

The single flip from climbing to falling is guaranteed exactly once, so the binary search lands on the unique peak.

## 5. Runnable example

```java
// PeakIndexInAMountainArray.java
public class PeakIndexInAMountainArray {

    // Level 1 -- Brute force: scan every index, comparing each
    // element to its next neighbor, and return the index where the
    // climb stops. Correct, but O(n) -- ignores the guaranteed
    // single-peak structure that allows a faster search.

    // KEY INSIGHT: "still climbing at this index" is a monotonic
    // condition (true up to the peak, false after), because the
    // mountain guarantee rules out any other shape -- binary search
    // finds the exact flip point.

    // Level 2 -- Optimal: binary search following the climb.
    static int peakIndexInMountainArray(int[] arr) {
        int lo = 0, hi = arr.length - 1;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (arr[mid] < arr[mid + 1]) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    }

    // Level 3 -- Hardened: works unchanged when the peak is at either
    // extreme allowed by the problem's constraints (index 1 or
    // arr.length - 2, since a true mountain always has at least one
    // element on each side of the peak).

    public static void main(String[] args) {
        System.out.println(peakIndexInMountainArray(new int[]{0, 2, 4, 6, 8, 3, 1}));
        // 4
        System.out.println(peakIndexInMountainArray(new int[]{0, 10, 5, 2}));
        // 1
    }
}
```

**How to run:** `java PeakIndexInAMountainArray.java`

## 6. Walkthrough

Trace `peakIndexInMountainArray(arr)` on `arr = [0,2,4,6,8,3,1]`:

| lo | hi | mid | arr[mid] | arr[mid+1] | comparison | action |
|---|---|---|---|---|---|---|
| 0 | 6 | 3 | 6 | 8 | 6 < 8 (climbing) | lo = 4 |
| 4 | 6 | 5 | 3 | 1 | 3 > 1 (falling) | hi = 5 |
| 4 | 5 | 4 | 8 | 3 | 8 > 3 (falling) | hi = 4 |
| 4 | 4 | — | — | — | loop ends | return 4 |

Index `4` (value `8`) is the peak. Time complexity is O(log n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: this problem's guarantee of exactly one peak (a true "mountain" shape) means the answer is always unique and well-defined — do not confuse it with Find Peak Element, which allows an unsorted array with multiple valid peaks and only asks for any one of them.

- The algorithm here is identical in shape to Find Peak Element's solution, but the guarantee of a single, well-formed mountain makes the correctness argument simpler and the result unambiguous.
- Because the mountain strictly increases then strictly decreases, `arr[mid] == arr[mid + 1]` never happens, so the comparison never needs a tie-breaking case.
- Related problems: Find Peak Element (the general unsorted-array version, any valid peak accepted), Find Minimum in Rotated Sorted Array (a similar "find the bend" binary search on a different array shape).
