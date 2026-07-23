---
card: leetcode-patterns
gi: 230
slug: binary-search
title: Binary Search
---

## 1. What it is

Given a sorted array `nums` of distinct integers and a `target`, return the index of `target` in `nums`, or `-1` if it is not present. Example: `nums = [-1,0,3,5,9,12]`, `target = 9` → `4`.

## 2. Why & when

This is the direct, textbook form of binary search and the base case every other problem in this section builds on. Use it whenever you need to find a value inside a sorted array faster than a linear scan, and there is no rotation or extra twist to handle.

## 3. Core concept

**Key idea:** keep two bounds, `lo` and `hi`, that always contain the target if it exists. Repeatedly check the middle element. If it is the target, done. Otherwise, the sorted order tells you which half to keep checking, so discard the other half entirely.

**Steps:**
1. Set `lo = 0`, `hi = nums.length - 1`.
2. While `lo <= hi`: compute `mid = lo + (hi - lo) / 2`.
3. If `nums[mid] == target`, return `mid`.
4. If `nums[mid] < target`, the target (if present) must be to the right, so set `lo = mid + 1`.
5. Otherwise, set `hi = mid - 1`.
6. If the loop ends without returning, the target is not in the array; return `-1`.

**Why it is correct:** the array is sorted, so if `nums[mid] < target`, every element at or before `mid` is also less than `target` — none of them can be the answer, so it is safe to discard the whole left half. The same logic applies in reverse when `nums[mid] > target`. The search range shrinks by half every iteration and always still contains the target if it exists, so the loop is guaranteed to either find it or exhaust the range.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Binary search narrowing lo and hi around index 4 while searching for 9">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [-1, 0, 3, 5, 9, 12], target = 9</text>
    <rect x="10" y="30" width="60" height="24" fill="#161b22" stroke="#30363d"/><text x="40" y="47" text-anchor="middle" font-size="10">lo=0</text>
    <rect x="190" y="30" width="60" height="24" fill="#3fb950"/><text x="220" y="47" fill="#0d1117" text-anchor="middle" font-size="10">mid=2 (3)</text>
    <rect x="370" y="30" width="60" height="24" fill="#161b22" stroke="#30363d"/><text x="400" y="47" text-anchor="middle" font-size="10">hi=5</text>
    <text x="10" y="80">3 &lt; 9 -&gt; lo = mid+1 = 3, discard left half</text>
    <rect x="280" y="95" width="60" height="24" fill="#3fb950"/><text x="310" y="112" fill="#0d1117" text-anchor="middle" font-size="10">mid=4 (9)</text>
    <text x="10" y="140">9 == 9 -&gt; return index 4</text>
  </g>
</svg>

Each comparison eliminates one whole half of the remaining range, converging on the target in a handful of steps.

## 5. Runnable example

```java
// BinarySearch.java
public class BinarySearch {

    // Level 1 -- Brute force: scan every element left to right,
    // comparing it to target, and return its index if found. Correct,
    // but O(n) -- it never uses the fact that the array is sorted.

    // KEY INSIGHT: sorted order means one comparison at the midpoint
    // tells you which entire half can be discarded, without ever
    // checking any element inside that half.

    // Level 2 -- Optimal: binary search on index.
    static int search(int[] nums, int target) {
        int lo = 0, hi = nums.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] == target) return mid;
            if (nums[mid] < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return -1;
    }

    // Level 3 -- Hardened: works unchanged when target is smaller than
    // every element (hi becomes -1 immediately) or larger than every
    // element (lo exceeds hi from the right side); both cases correctly
    // fall through to the final "not found" return of -1.

    public static void main(String[] args) {
        int[] nums = {-1, 0, 3, 5, 9, 12};
        System.out.println(search(nums, 9));
        // 4
        System.out.println(search(nums, 2));
        // -1
    }
}
```

**How to run:** `java BinarySearch.java`

## 6. Walkthrough

Trace `search(nums, 9)` on `nums = [-1, 0, 3, 5, 9, 12]`:

| lo | hi | mid | nums[mid] | comparison | action |
|---|---|---|---|---|---|
| 0 | 5 | 2 | 3 | 3 < 9 | lo = 3 |
| 3 | 5 | 4 | 9 | match | return 4 |

Found in 2 comparisons instead of scanning up to 5. Time complexity is O(log n), since each comparison halves the search range. Space is O(1), using only three integer variables regardless of array size.

## 7. Gotchas & takeaways

> Gotcha: writing `mid = (lo + hi) / 2` instead of `mid = lo + (hi - lo) / 2` risks integer overflow when `lo` and `hi` are both near the maximum `int` value, producing a negative `mid` and breaking the search — always use the overflow-safe form.

- This is the base template for the whole Modified Binary Search section: every other problem here adds one twist (rotation, a boolean predicate, an insertion point) on top of this exact loop shape.
- The array must be sorted for this to work at all; running it on an unsorted array gives an undefined, often wrong, result with no error raised.
- Related problems: Search Insert Position (same loop, returns `lo` instead of `-1` on a miss), Search in Rotated Sorted Array (same loop, with an extra check for which half is sorted).
