---
card: leetcode-patterns
gi: 248
slug: search-in-rotated-sorted-array-ii
title: Search in Rotated Sorted Array II
---

## 1. What it is

The same setup as Search in Rotated Sorted Array, but `nums` MAY contain duplicate values. Return `true` if `target` exists in the rotated array, `false` otherwise. Example: `nums = [2,5,6,0,0,1,2]`, `target = 0` → `true`.

## 2. Why & when

Duplicates break the trick that decided which half was sorted in the distinct-values version: comparing `nums[lo]` to `nums[mid]` can no longer tell you anything when they happen to be EQUAL, since that could mean either half is the sorted one. Use the extra "shrink and skip" step from this problem whenever a rotated sorted array is allowed to contain duplicate values.

## 3. Core concept

**Key idea:** keep the same overall binary search shape as the distinct-values version. But when `nums[lo] == nums[mid]` (the ambiguous case), you cannot tell which half is sorted — so simply shrink the search range by moving `lo` forward by one, and try again. This sacrifices the guaranteed O(log n) bound in rare adversarial cases, but keeps the algorithm correct.

**Steps:**
1. Set `lo = 0`, `hi = nums.length - 1`.
2. While `lo <= hi`: compute `mid = lo + (hi - lo) / 2`.
3. If `nums[mid] == target`, return `true`.
4. If `nums[lo] == nums[mid]` AND `nums[mid] != nums[hi]`... actually, simpler: if `nums[lo] == nums[mid]`, we cannot determine sortedness from this pair — shrink: `lo++`. Continue the loop.
5. Otherwise, apply the same logic as the distinct-values version: if `nums[lo] < nums[mid]` (left half sorted), check if `target` falls in `[nums[lo], nums[mid])`; if so, `hi = mid - 1`, else `lo = mid + 1`.
6. If the right half is sorted instead, check if `target` falls in `(nums[mid], nums[hi]]`; if so, `lo = mid + 1`, else `hi = mid - 1`.
7. If the loop ends without a match, return `false`.

**Why it is correct:** when `nums[lo] != nums[mid]`, the distinct-values reasoning still applies exactly — one of the two halves is guaranteed properly sorted. When `nums[lo] == nums[mid]`, you genuinely cannot tell (for example `[1,0,1,1,1]` versus `[1,1,1,0,1]` look identical at `lo` and `mid`), so the only safe move is to shrink the ambiguous edge by one and re-evaluate — this never skips over the target, since `lo` only advances past a value equal to `nums[mid]`, which was already checked, or was proven not to be the target by the direct check at step 3 on a prior iteration.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Array 1 0 1 1 1, nums lo equals nums mid, ambiguous, shrink lo by one">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [1, 0, 1, 1, 1], target = 0</text>
    <rect x="10" y="30" width="30" height="24" fill="#e3b341"/><text x="25" y="47" fill="#0d1117" text-anchor="middle" font-size="9">1 lo</text>
    <rect x="40" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="55" y="47" text-anchor="middle" font-size="9">0</text>
    <rect x="70" y="30" width="30" height="24" fill="#e3b341"/><text x="85" y="47" fill="#0d1117" text-anchor="middle" font-size="9">1 mid</text>
    <rect x="100" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="115" y="47" text-anchor="middle" font-size="9">1</text>
    <rect x="130" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="145" y="47" text-anchor="middle" font-size="9">1 hi</text>
    <text x="10" y="80">nums[lo]==nums[mid]==1: cannot tell which half is sorted</text>
    <text x="10" y="105">shrink: lo++ (skip the ambiguous duplicate), re-check</text>
  </g>
</svg>

When the boundary values tie, the algorithm gives up trying to be clever for that step and just narrows the range by one instead.

## 5. Runnable example

```java
// SearchInRotatedSortedArrayII.java
public class SearchInRotatedSortedArrayII {

    // Level 1 -- Brute force: scan every element left to right,
    // comparing it to target. Correct, and simple, but O(n) always --
    // duplicates make the "which half is sorted" trick unreliable, so
    // a naive port of the distinct-values binary search would be
    // incorrect without the extra ambiguity-handling step below.

    // KEY INSIGHT: when nums[lo] == nums[mid], sortedness cannot be
    // determined from that comparison alone -- shrinking lo by one
    // resolves the ambiguity without ever skipping past the target.

    // Level 2 -- Optimal: binary search with an ambiguity-skip step.
    static boolean search(int[] nums, int target) {
        int lo = 0, hi = nums.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] == target) return true;

            if (nums[lo] == nums[mid]) {
                lo++; // ambiguous, shrink and retry
                continue;
            }

            if (nums[lo] < nums[mid]) { // left half sorted
                if (nums[lo] <= target && target < nums[mid]) hi = mid - 1;
                else lo = mid + 1;
            } else { // right half sorted
                if (nums[mid] < target && target <= nums[hi]) lo = mid + 1;
                else hi = mid - 1;
            }
        }
        return false;
    }

    // Level 3 -- Hardened: in the worst case (e.g. all elements equal
    // except one), the ambiguity-skip step degrades to O(n), which is
    // an accepted and unavoidable tradeoff for correctness with
    // duplicates -- worth stating explicitly in an interview.

    public static void main(String[] args) {
        System.out.println(search(new int[]{2, 5, 6, 0, 0, 1, 2}, 0));
        // true
        System.out.println(search(new int[]{2, 5, 6, 0, 0, 1, 2}, 3));
        // false
    }
}
```

**How to run:** `java SearchInRotatedSortedArrayII.java`

## 6. Walkthrough

Trace `search(nums, 0)` on `nums = [2,5,6,0,0,1,2]`:

| lo | hi | mid | nums[mid] | nums[lo] | ambiguous? | action |
|---|---|---|---|---|---|---|
| 0 | 6 | 3 | 0 | 2 | no | 0 == target -> return true |

Found immediately since `mid` lands on the target directly. Time complexity is O(log n) in the average case, degrading to O(n) in the worst case (many duplicate values), because the ambiguity-skip step only removes one element at a time. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: this problem's worst-case time complexity is genuinely worse than the distinct-values version — an interviewer expects you to name this tradeoff explicitly (e.g. an array like `[1,1,1,1,1,1,0,1]`), not just present the same code with a small patch and claim O(log n) unconditionally.

- The only new logic versus Search in Rotated Sorted Array is the `nums[lo] == nums[mid]` ambiguity check; every other branch is identical.
- This shrink-by-one approach is safe because it only ever discards a value already proven not to be `target` (checked directly, or equal to a value already checked).
- Related problems: Search in Rotated Sorted Array (the distinct-values base case, guaranteed O(log n)), Find Minimum in Rotated Sorted Array (a related problem that also gets harder with duplicates, for the same underlying reason).
