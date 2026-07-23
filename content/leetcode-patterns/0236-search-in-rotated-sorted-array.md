---
card: leetcode-patterns
gi: 236
slug: search-in-rotated-sorted-array
title: Search in Rotated Sorted Array
---

## 1. What it is

A sorted array with distinct values has been rotated at some unknown pivot (for example, `[0,1,2,4,5,6,7]` rotated to `[4,5,6,7,0,1,2]`). Given the rotated array and a `target`, return its index, or `-1` if not present, in O(log n) time. Example: `nums = [4,5,6,7,0,1,2]`, `target = 0` → `4`.

## 2. Why & when

This extends plain binary search to handle the one twist of a rotation: the whole array is no longer sorted, but at least ONE of the two halves around any midpoint always still is. Use this shape whenever an array is described as "sorted then rotated" and you need better than O(n) search.

## 3. Core concept

**Key idea:** at every `mid`, compare `nums[lo]` to `nums[mid]`. If `nums[lo] <= nums[mid]`, the LEFT half (`lo..mid`) is properly sorted (no rotation point inside it). Otherwise, the RIGHT half (`mid..hi`) must be the sorted one. Once you know which half is sorted, check whether `target` falls within that half's value range — if it does, search there; otherwise, search the other half.

**Steps:**
1. Set `lo = 0`, `hi = nums.length - 1`.
2. While `lo <= hi`: compute `mid = lo + (hi - lo) / 2`.
3. If `nums[mid] == target`, return `mid`.
4. If `nums[lo] <= nums[mid]` (left half is sorted): if `nums[lo] <= target < nums[mid]`, the target must be in the left half, so set `hi = mid - 1`; otherwise set `lo = mid + 1`.
5. Otherwise (right half is sorted): if `nums[mid] < target <= nums[hi]`, the target must be in the right half, so set `lo = mid + 1`; otherwise set `hi = mid - 1`.
6. If the loop ends without a match, return `-1`.

**Why it is correct:** a single rotation point can only exist in one of the two halves around any midpoint — the other half is guaranteed to be a normal, contiguous sorted range. Once you identify which half is properly sorted, a simple range check (`nums[lo] <= target < nums[mid]`, or the mirrored version) tells you with certainty whether `target` can be in that half, letting you discard the other half exactly as in plain binary search.

## 4. Diagram

<svg viewBox="0 0 460 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Rotated array 4 5 6 7 0 1 2, left half sorted since nums[lo] less or equal nums[mid]">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [4,5,6,7,0,1,2], target = 0</text>
    <rect x="10" y="30" width="30" height="24" fill="#3fb950"/><text x="25" y="47" fill="#0d1117" text-anchor="middle" font-size="9">4</text>
    <rect x="40" y="30" width="30" height="24" fill="#3fb950"/><text x="55" y="47" fill="#0d1117" text-anchor="middle" font-size="9">5</text>
    <rect x="70" y="30" width="30" height="24" fill="#3fb950"/><text x="85" y="47" fill="#0d1117" text-anchor="middle" font-size="9">6</text>
    <rect x="100" y="30" width="30" height="24" fill="#161b22" stroke="#e3b341"/><text x="115" y="47" text-anchor="middle" font-size="9">7 mid</text>
    <rect x="130" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="145" y="47" text-anchor="middle" font-size="9">0</text>
    <rect x="160" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="175" y="47" text-anchor="middle" font-size="9">1</text>
    <rect x="190" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="205" y="47" text-anchor="middle" font-size="9">2</text>
    <text x="10" y="80">left half [4..7] is sorted (nums[lo]=4 &lt;= nums[mid]=7)</text>
    <text x="10" y="100">target 0 not in [4,7) -&gt; search right half instead</text>
    <text x="10" y="130">lo = mid + 1 = 4; next mid finds 0 at index 4</text>
  </g>
</svg>

The green half is confirmed sorted; the target's value decides whether to search inside it or jump to the other, unsorted-looking half.

## 5. Runnable example

```java
// SearchInRotatedSortedArray.java
public class SearchInRotatedSortedArray {

    // Level 1 -- Brute force: scan every element left to right,
    // comparing it to target. Correct, but O(n) -- ignores that most
    // of the array is still locally sorted around the rotation point.

    // KEY INSIGHT: at any midpoint, one of the two halves is always a
    // normal contiguous sorted range, even though the whole array is
    // not. Identify that half, then discard the other half exactly as
    // in plain binary search.

    // Level 2 -- Optimal: binary search with a sorted-half check.
    static int search(int[] nums, int target) {
        int lo = 0, hi = nums.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] == target) return mid;

            if (nums[lo] <= nums[mid]) { // left half sorted
                if (nums[lo] <= target && target < nums[mid]) hi = mid - 1;
                else lo = mid + 1;
            } else { // right half sorted
                if (nums[mid] < target && target <= nums[hi]) lo = mid + 1;
                else hi = mid - 1;
            }
        }
        return -1;
    }

    // Level 3 -- Hardened: works unchanged when the array is NOT
    // rotated at all (rotation point at index 0), since nums[lo] <=
    // nums[mid] holds for the whole array and the logic degrades to
    // plain binary search.

    public static void main(String[] args) {
        int[] nums = {4, 5, 6, 7, 0, 1, 2};
        System.out.println(search(nums, 0));
        // 4
        System.out.println(search(nums, 3));
        // -1
    }
}
```

**How to run:** `java SearchInRotatedSortedArray.java`

## 6. Walkthrough

Trace `search(nums, 0)` on `nums = [4,5,6,7,0,1,2]`:

| lo | hi | mid | nums[mid] | which half sorted | target in that half? | action |
|---|---|---|---|---|---|---|
| 0 | 6 | 3 | 7 | left (4<=7) | 0 not in [4,7) | lo = 4 |
| 4 | 6 | 5 | 1 | left (0<=1) | 0 in [0,1)? no (0 not < 1... check: target=0, nums[lo]=0<=0<1, yes) | hi = 4 |
| 4 | 4 | 4 | 0 | match | — | return 4 |

Found in 3 comparisons instead of scanning up to 5 elements. Time complexity is O(log n), matching plain binary search. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: comparing `nums[lo]` to `nums[mid]` (not `nums[mid]` to `nums[hi]`) to decide which half is sorted is important — using the wrong pair, or using a strict `<` instead of `<=` when `lo == mid`, can misclassify a single-element range and break the search.

- Distinct values are required for this exact comparison trick; if duplicates are allowed, `nums[lo] == nums[mid]` no longer tells you which half is sorted, and the worst case degrades to O(n) (see the "II" variant of this problem).
- The core loop shape (`lo <= hi`, `mid ± 1`) is unchanged from plain Binary Search — only the "which half do I search" decision is new.
- Related problems: Find Minimum in Rotated Sorted Array (uses the same sorted-half idea to find the rotation point itself), Binary Search (the un-rotated base case).
