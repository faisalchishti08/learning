---
card: leetcode-patterns
gi: 238
slug: find-first-and-last-position-of-element-in-sorted-array
title: Find First and Last Position of Element in Sorted Array
---

## 1. What it is

Given a sorted array `nums` that MAY contain duplicates, and a `target`, return the first and last index where `target` appears, as a two-element array `[first, last]`. If `target` is not present, return `[-1, -1]`. Example: `nums = [5,7,7,8,8,10]`, `target = 8` → `[3,4]`.

## 2. Why & when

This problem needs two separate binary searches — one biased to find the LEFTMOST occurrence, one biased to find the RIGHTMOST — because plain binary search only guarantees finding SOME occurrence of a duplicated target, not a specific end. Use this "two-boundary search" shape whenever a problem asks for a range of matching positions inside a sorted array with duplicates.

## 3. Core concept

**Key idea:** reuse the search-on-answer template twice, with two different monotonic predicates. For the first (leftmost) occurrence, search for the smallest index where `nums[index] >= target`. For the last (rightmost) occurrence, search for the largest index where `nums[index] <= target`. Then confirm the found index actually holds `target` (it might not, if `target` is absent entirely).

**Steps:**
1. **Find first:** binary search with `lo = 0`, `hi = n - 1`. While `lo < hi`: if `nums[mid] < target`, set `lo = mid + 1`; otherwise set `hi = mid` (keep `mid`, since it could be the first occurrence).
2. After the loop, check `nums[lo] == target`. If not, `target` is absent: return `[-1, -1]`.
3. **Find last:** binary search again with `lo = 0`, `hi = n - 1`. While `lo < hi`: compute `mid` rounded UP; if `nums[mid] > target`, set `hi = mid - 1`; otherwise set `lo = mid` (keep `mid`, since it could be the last occurrence).
4. Return `[first, last]`.

**Why it is correct:** "is `nums[index] >= target`" is monotonic (false for all indices before the first occurrence, true from the first occurrence onward), so the answer-search template finds that exact boundary. Symmetrically, "is `nums[index] <= target`" is monotonic in the other direction, finding the last occurrence. Running both searches independently, each in O(log n), gives the full range.

## 4. Diagram

<svg viewBox="0 0 460 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Array 5 7 7 8 8 10, target 8, first search finds index 3, second search finds index 4">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [5, 7, 7, 8, 8, 10], target = 8</text>
    <rect x="10" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="25" y="47" text-anchor="middle" font-size="9">5</text>
    <rect x="40" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="55" y="47" text-anchor="middle" font-size="9">7</text>
    <rect x="70" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="85" y="47" text-anchor="middle" font-size="9">7</text>
    <rect x="100" y="30" width="30" height="24" fill="#3fb950"/><text x="115" y="47" fill="#0d1117" text-anchor="middle" font-size="9">8</text>
    <rect x="130" y="30" width="30" height="24" fill="#3fb950"/><text x="145" y="47" fill="#0d1117" text-anchor="middle" font-size="9">8</text>
    <rect x="160" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="175" y="47" text-anchor="middle" font-size="9">10</text>
    <text x="10" y="80">search 1 (first index where nums[i] &gt;= 8): index 3</text>
    <text x="10" y="105">search 2 (last index where nums[i] &lt;= 8): index 4</text>
    <text x="10" y="130">result: [3, 4]</text>
  </g>
</svg>

Two independent boundary searches over the same array find the left and right edges of the block of matching values.

## 5. Runnable example

```java
// FindFirstAndLastPosition.java
public class FindFirstAndLastPosition {

    // Level 1 -- Brute force: scan every element left to right,
    // tracking the first and last index where nums[i] == target.
    // Correct, but O(n) -- ignores that the array is sorted.

    // KEY INSIGHT: "first occurrence" and "last occurrence" are each
    // just a boundary in a monotonic condition (nums[i] >= target, or
    // nums[i] <= target), so each one is a separate O(log n)
    // search-on-answer call, run independently.

    // Level 2 -- Optimal: two binary searches.
    static int[] searchRange(int[] nums, int target) {
        if (nums.length == 0) return new int[]{-1, -1};

        int first = findFirst(nums, target);
        if (first == -1) return new int[]{-1, -1};
        int last = findLast(nums, target);
        return new int[]{first, last};
    }

    static int findFirst(int[] nums, int target) {
        int lo = 0, hi = nums.length - 1;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] < target) lo = mid + 1;
            else hi = mid;
        }
        return nums[lo] == target ? lo : -1;
    }

    static int findLast(int[] nums, int target) {
        int lo = 0, hi = nums.length - 1;
        while (lo < hi) {
            int mid = lo + (hi - lo + 1) / 2;
            if (nums[mid] > target) hi = mid - 1;
            else lo = mid;
        }
        return lo;
    }

    // Level 3 -- Hardened: findLast is only called after findFirst
    // already confirmed target is present, so it never needs its own
    // "not found" check -- it is guaranteed to land on a real match.

    public static void main(String[] args) {
        int[] nums = {5, 7, 7, 8, 8, 10};
        System.out.println(java.util.Arrays.toString(searchRange(nums, 8)));
        // [3, 4]
        System.out.println(java.util.Arrays.toString(searchRange(nums, 6)));
        // [-1, -1]
    }
}
```

**How to run:** `java FindFirstAndLastPosition.java`

## 6. Walkthrough

Trace `findFirst(nums, 8)` on `nums = [5,7,7,8,8,10]`:

| lo | hi | mid | nums[mid] | action |
|---|---|---|---|---|
| 0 | 5 | 2 | 7 | 7 < 8, lo = 3 |
| 3 | 5 | 4 | 8 | 8 >= 8, hi = 4 |
| 3 | 4 | 3 | 8 | 8 >= 8, hi = 3 |
| 3 | 3 | — | loop ends | nums[3]==8, return 3 |

Trace `findLast(nums, 8)` starting fresh with `lo=0, hi=5`:

| lo | hi | mid (round up) | nums[mid] | action |
|---|---|---|---|---|
| 0 | 5 | 3 | 8 | 8 <= 8, lo = 3 |
| 3 | 5 | 4 | 8 | 8 <= 8, lo = 4 |
| 4 | 5 | 5 | 10 | 10 > 8, hi = 4 |
| 4 | 4 | — | loop ends | return 4 |

Result: `[3, 4]`. Time complexity is O(log n) — two independent binary searches. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: forgetting to check `nums[lo] == target` after the `findFirst` search returns a wrong non-`-1` index when the target is absent entirely — `findFirst` always lands on SOME index (the first place `target` could be inserted), which is not the same as confirming `target` is actually there.

- `findFirst` rounds `mid` down (`hi = mid`, searching for the smallest true value); `findLast` rounds `mid` up (`lo = mid`, searching for the largest true value) — mixing these up causes the loop to stall or converge on the wrong boundary.
- Once `findFirst` confirms `target` is present, `findLast` is guaranteed to find a valid match too, so it does not need its own presence check.
- Related problems: Search Insert Position (the same "first index >= target" idea, used for a different purpose), Binary Search (the base template both boundary searches build on).
