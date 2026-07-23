---
card: leetcode-patterns
gi: 231
slug: search-insert-position
title: Search Insert Position
---

## 1. What it is

Given a sorted array `nums` of distinct integers and a `target`, return the index of `target` if it is found. If not found, return the index where it WOULD be inserted to keep the array sorted. Example: `nums = [1,3,5,6]`, `target = 5` → `2`; `target = 2` → `1` (insert between `1` and `3`).

## 2. Why & when

This is the plain binary search template with one change to what happens on a miss: instead of returning `-1`, you return the position that keeps the array sorted. Use it whenever a problem needs "the first position not less than X" — a very common building block inside bigger algorithms (for example, choosing where to place a new interval, or finding a lower bound).

## 3. Core concept

**Key idea:** run standard binary search. If the target is found, `mid` is the answer. If it is never found, watch what `lo` looks like when the loop ends: it always lands exactly at the correct insertion point, because `lo` only ever moves right past values smaller than `target`, and `hi` only ever moves left past values greater than or equal to `target`.

**Steps:**
1. Set `lo = 0`, `hi = nums.length - 1`.
2. While `lo <= hi`: compute `mid = lo + (hi - lo) / 2`.
3. If `nums[mid] == target`, return `mid` immediately.
4. If `nums[mid] < target`, set `lo = mid + 1`.
5. Otherwise, set `hi = mid - 1`.
6. If the loop ends without a match, return `lo`.

**Why it is correct:** every time `lo` advances, it is because `nums[mid] < target`, so `lo` always sits just past the last value confirmed to be smaller than `target`. Every time `hi` retreats, it is because `nums[mid] >= target`. When the loop ends (`lo > hi`), `lo` points to the first element `>= target`, which is exactly the correct sorted insertion point — whether or not `target` itself was actually present.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Searching for 2 in 1,3,5,6 lo ends at index 1, the correct insertion point">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [1, 3, 5, 6], target = 2 (not present)</text>
    <rect x="10" y="30" width="50" height="24" fill="#161b22" stroke="#30363d"/><text x="35" y="47" text-anchor="middle" font-size="9">1</text>
    <rect x="65" y="30" width="50" height="24" fill="#3fb950"/><text x="90" y="47" fill="#0d1117" text-anchor="middle" font-size="9">3 (mid)</text>
    <rect x="120" y="30" width="50" height="24" fill="#161b22" stroke="#30363d"/><text x="145" y="47" text-anchor="middle" font-size="9">5</text>
    <rect x="175" y="30" width="50" height="24" fill="#161b22" stroke="#30363d"/><text x="200" y="47" text-anchor="middle" font-size="9">6</text>
    <text x="10" y="80">2 &lt; 3 -&gt; hi = -1 (index 0's slot); loop ends with lo = 1</text>
    <text x="10" y="110">insert 2 at index 1: [1, 2, 3, 5, 6]</text>
  </g>
</svg>

`lo` naturally settles at the first index holding a value not smaller than `target`, which is exactly where `target` belongs.

## 5. Runnable example

```java
// SearchInsertPosition.java
public class SearchInsertPosition {

    // Level 1 -- Brute force: scan left to right, and return the
    // index of the first element >= target (or nums.length if none
    // exists). Correct, but O(n) -- ignores that nums is sorted.

    // KEY INSIGHT: standard binary search already computes this
    // boundary as a side effect. When the loop ends without finding
    // an exact match, lo is precisely the correct insertion index --
    // no extra logic is needed beyond the plain search template.

    // Level 2 -- Optimal: binary search, return lo on a miss.
    static int searchInsert(int[] nums, int target) {
        int lo = 0, hi = nums.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] == target) return mid;
            if (nums[mid] < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return lo;
    }

    // Level 3 -- Hardened: works unchanged for target smaller than
    // every element (lo stays 0) and target larger than every element
    // (lo reaches nums.length, meaning "insert at the very end").

    public static void main(String[] args) {
        int[] nums = {1, 3, 5, 6};
        System.out.println(searchInsert(nums, 5));
        // 2
        System.out.println(searchInsert(nums, 2));
        // 1
        System.out.println(searchInsert(nums, 7));
        // 4
    }
}
```

**How to run:** `java SearchInsertPosition.java`

## 6. Walkthrough

Trace `searchInsert(nums, 2)` on `nums = [1, 3, 5, 6]`:

| lo | hi | mid | nums[mid] | comparison | action |
|---|---|---|---|---|---|
| 0 | 3 | 1 | 3 | 2 < 3 | hi = 0 |
| 0 | 0 | 0 | 1 | 2 > 1 | lo = 1 |
| 1 | 0 | — | — | loop ends (lo > hi) | return lo = 1 |

Inserting `2` at index `1` gives `[1, 2, 3, 5, 6]`, which is correctly sorted. Time complexity is O(log n), the same as plain binary search. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: it is tempting to add a special case for "target not found," but no special case is needed — `lo`'s final resting place after the ordinary binary search loop already IS the correct answer for both the found and not-found cases.

- This exact "return `lo` on a miss" trick generalizes to any "first index where a sorted condition becomes true" problem — it is the search-on-answer template applied to array positions.
- The result is always in the valid range `[0, nums.length]` inclusive, since `lo` can advance at most one past the last valid index.
- Related problems: Binary Search (same loop, returns `-1` instead of `lo` on a miss), Find First and Last Position of Element in Sorted Array (uses this exact lower-bound idea twice, once for the start and once for the end).
