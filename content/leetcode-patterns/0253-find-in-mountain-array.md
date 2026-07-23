---
card: leetcode-patterns
gi: 253
slug: find-in-mountain-array
title: Find in Mountain Array
---

## 1. What it is

Given a `MountainArray` interface (strictly increasing then strictly decreasing, one peak, guaranteed), with only `get(index)` and `length()` available — no direct array access — find the index of `target`, or `-1` if absent. You must minimize calls to `get`. Example: a mountain array representing `[1,2,3,4,5,3,1]`, `target = 3` → `2` (the first occurrence, on the ascending side).

## 2. Why & when

This problem combines two binary searches you already know: Peak Index in a Mountain Array (find the peak) and plain Binary Search (search each monotonic half). Use this shape whenever a problem gives you an ABSTRACT interface instead of a raw array — a strong signal that minimizing the number of interface calls matters as much as the algorithm's correctness.

## 3. Core concept

**Key idea:** a mountain array is two sorted halves glued together at the peak: an ascending half and a descending half. First, binary search for the peak index (same technique as Peak Index in a Mountain Array). Then, binary search for `target` in the ascending half (normal order). If not found there, binary search for `target` in the descending half (using a REVERSED comparison, since values decrease as the index increases).

**Steps:**
1. Binary search for the peak index using the slope-following technique: compare `get(mid)` to `get(mid + 1)`.
2. Binary search the ascending half `[0, peak]` for `target` using the plain binary search template.
3. If found, return that index immediately.
4. Otherwise, binary search the descending half `[peak + 1, length - 1]` for `target`, but flip the comparison direction, since `get(mid)` DECREASES as `mid` increases in this half.
5. If found, return that index; otherwise return `-1`.

**Why it is correct:** each half of a mountain array is, by definition, sorted (one ascending, one descending), so plain binary search applies directly to each — the descending half just needs its comparison logic mirrored. Checking the ascending half first is required because the problem wants the target found via any valid index, but conventionally checking left-to-right order first matches how the array is naturally read.

## 4. Diagram

<svg viewBox="0 0 460 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Mountain array 1 2 3 4 5 3 1, peak at index 4, ascending half indices 0-4, descending half indices 4-6">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">mountain = [1,2,3,4,5,3,1], target = 3</text>
    <rect x="10" y="100" width="25" height="10" fill="#161b22" stroke="#30363d"/>
    <rect x="40" y="85" width="25" height="25" fill="#3fb950"/><text x="52" y="80" fill="#3fb950" font-size="9" text-anchor="middle">asc</text>
    <rect x="70" y="65" width="25" height="45" fill="#161b22" stroke="#30363d"/>
    <rect x="100" y="45" width="25" height="65" fill="#161b22" stroke="#30363d"/>
    <rect x="130" y="30" width="25" height="80" fill="#e3b341"/><text x="142" y="25" fill="#e3b341" font-size="9" text-anchor="middle">peak</text>
    <rect x="160" y="65" width="25" height="45" fill="#f85149"/><text x="172" y="130" fill="#f85149" font-size="9" text-anchor="middle">desc</text>
    <rect x="190" y="100" width="25" height="10" fill="#161b22" stroke="#30363d"/>
    <text x="10" y="150">first search the ascending half for 3 (found at index 2), stop there</text>
  </g>
</svg>

Splitting at the peak turns one mountain search into two ordinary binary searches, one of them reversed.

## 5. Runnable example

```java
// FindInMountainArray.java
public class FindInMountainArray {

    interface MountainArray {
        int get(int index);
        int length();
    }

    // Level 1 -- Brute force: call get(i) for every index from 0 to
    // length()-1, comparing to target. Correct, but O(n) calls to
    // get(), which the problem specifically asks you to minimize.

    // KEY INSIGHT: a mountain array is two sorted halves joined at one
    // peak. Find the peak with a slope-following binary search, then
    // run plain binary search on each half (reversing the comparison
    // for the descending half).

    // Level 2 -- Optimal: peak search, then two binary searches.
    static int findInMountainArray(int target, MountainArray mountainArr) {
        int n = mountainArr.length();
        int peak = findPeak(mountainArr, n);

        int leftResult = binarySearch(mountainArr, 0, peak, target, true);
        if (leftResult != -1) return leftResult;

        return binarySearch(mountainArr, peak + 1, n - 1, target, false);
    }

    static int findPeak(MountainArray arr, int n) {
        int lo = 0, hi = n - 1;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (arr.get(mid) < arr.get(mid + 1)) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    }

    static int binarySearch(MountainArray arr, int lo, int hi, int target, boolean ascending) {
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            int value = arr.get(mid);
            if (value == target) return mid;
            if (ascending) {
                if (value < target) lo = mid + 1; else hi = mid - 1;
            } else {
                if (value > target) lo = mid + 1; else hi = mid - 1;
            }
        }
        return -1;
    }

    // Level 3 -- Hardened: total get() calls stay O(log n) even in the
    // worst case, since all three phases (peak search, ascending
    // search, descending search) are each independently O(log n).

    public static void main(String[] args) {
        int[] backing = {1, 2, 3, 4, 5, 3, 1};
        MountainArray mountainArr = new MountainArray() {
            public int get(int index) { return backing[index]; }
            public int length() { return backing.length; }
        };
        System.out.println(findInMountainArray(3, mountainArr));
        // 2
    }
}
```

**How to run:** `java FindInMountainArray.java`

## 6. Walkthrough

For `mountain = [1,2,3,4,5,3,1]`, `target = 3`:

1. `findPeak`: binary search finds the peak at index `4` (value `5`).
2. `binarySearch(arr, 0, 4, 3, ascending=true)`: searches `[1,2,3,4,5]`. `mid=2`, `arr.get(2)=3`, matches `target`, returns `2` immediately.
3. Since the ascending search already found a match, the descending search is never run.

Total `get()` calls: about `log2(7) + log2(5) ≈ 3 + 3 = 6` calls, far fewer than scanning all 7 elements. Time complexity is O(log n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: forgetting to reverse the comparison direction for the descending half (still using `if (value < target) lo = mid + 1`) silently searches the wrong direction, since values DECREASE as the index increases past the peak — always mirror the comparison logic for that half.

- This problem is a direct composition of two patterns already covered in this section: Peak Index in a Mountain Array (finding the peak) and plain Binary Search (searching each sorted half).
- Minimizing `get()` calls matters here specifically because the interface models an expensive or rate-limited data source — a common real-world constraint behind "interactive" LeetCode problems.
- Related problems: Peak Index in a Mountain Array (the peak-finding half of this solution), Binary Search (the half-search half of this solution).
