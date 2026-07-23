---
card: leetcode-patterns
gi: 243
slug: single-element-in-a-sorted-array
title: Single Element in a Sorted Array
---

## 1. What it is

Given a sorted array where every element appears exactly twice, except for one element that appears exactly once, find that single element in O(log n) time. Example: `nums = [1,1,2,3,3,4,4,8,8]` → `2`.

## 2. Why & when

Before the single element, every pair sits at an (even index, odd index) position — like `(0,1)`, `(2,3)`. After it, that alignment shifts to (odd index, even index). That shift is a monotonic boolean condition over the array, letting you binary search for exactly where it flips. Use this shape whenever a sorted array has a "paired" structure with one broken pair, and you need to find the break point faster than a linear scan.

## 3. Core concept

**Key idea:** before the single element, for any even index `i`, `nums[i] == nums[i+1]` (pairs are aligned normally). After the single element, that alignment breaks: for an even index `i` at or past the single element, `nums[i] != nums[i+1]`. Binary search for the first even index where the pairing breaks — that index holds the single element.

**Steps:**
1. Set `lo = 0`, `hi = nums.length - 1`.
2. While `lo < hi`: compute `mid = lo + (hi - lo) / 2`. Force `mid` to be EVEN by subtracting 1 if it is odd (`if (mid % 2 == 1) mid--`).
3. If `nums[mid] == nums[mid + 1]`, the pairing is still intact at `mid`, so the single element is further right: set `lo = mid + 2`.
4. Otherwise, the pairing is already broken at `mid`, so the single element is at `mid` or to its left: set `hi = mid`.
5. When the loop ends, `lo == hi` is the index of the single element.

**Why it is correct:** forcing `mid` to be even and comparing `nums[mid]` to `nums[mid + 1]` checks exactly one "pair slot." Every pair slot before the single element is intact; the first broken pair slot marks the single element's position (rounded to the nearest even index at or before it). This gives a clean monotonic false-then-true condition ("is the pairing broken by this point"), which binary search finds directly.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Array 1 1 2 3 3 4 4 8 8, pairing intact at indices 0-1, breaks at index 2, single element at index 2">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = [1,1,2,3,3,4,4,8,8]  (indices 0..8)</text>
    <rect x="10" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="25" y="47" text-anchor="middle" font-size="9">1</text>
    <rect x="40" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="55" y="47" text-anchor="middle" font-size="9">1</text>
    <rect x="70" y="30" width="30" height="24" fill="#3fb950"/><text x="85" y="47" fill="#0d1117" text-anchor="middle" font-size="9">2</text>
    <rect x="100" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="115" y="47" text-anchor="middle" font-size="9">3</text>
    <rect x="130" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="145" y="47" text-anchor="middle" font-size="9">3</text>
    <text x="10" y="80">index 0 (even): nums[0]==nums[1] -> pairing intact</text>
    <text x="10" y="100">index 2 (even): nums[2]=2 != nums[3]=3 -> pairing broken here</text>
    <text x="10" y="130">single element found at index 2</text>
  </g>
</svg>

Checking whether an even-indexed pair is still aligned tells you which side of the single element you are on.

## 5. Runnable example

```java
// SingleElementInASortedArray.java
public class SingleElementInASortedArray {

    // Level 1 -- Brute force: XOR every element together; pairs cancel
    // out (a XOR a == 0), leaving only the single element. Correct and
    // actually O(n) time O(1) space, but does not use the SORTED
    // property at all, and the problem specifically asks for O(log n).

    // KEY INSIGHT: "is the even-index pairing still intact by this
    // point" is a monotonic condition (true, true, ..., false, false)
    // over the array, so binary search finds the exact break point.

    // Level 2 -- Optimal: binary search on the pairing alignment.
    static int singleNonDuplicate(int[] nums) {
        int lo = 0, hi = nums.length - 1;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (mid % 2 == 1) mid--;
            if (nums[mid] == nums[mid + 1]) lo = mid + 2;
            else hi = mid;
        }
        return nums[lo];
    }

    // Level 3 -- Hardened: works unchanged for a single-element array
    // (loop never runs, lo=hi=0 is the answer) and when the single
    // element is at either the very first or very last position.

    public static void main(String[] args) {
        System.out.println(singleNonDuplicate(new int[]{1,1,2,3,3,4,4,8,8}));
        // 2
        System.out.println(singleNonDuplicate(new int[]{3,3,7,7,10,11,11}));
        // 10
    }
}
```

**How to run:** `java SingleElementInASortedArray.java`

## 6. Walkthrough

Trace `singleNonDuplicate(nums)` on `nums = [1,1,2,3,3,4,4,8,8]`, `lo=0, hi=8`:

| lo | hi | mid (forced even) | nums[mid] | nums[mid+1] | comparison | action |
|---|---|---|---|---|---|---|
| 0 | 8 | 4 | 3 | 4 | not equal | hi = 4 |
| 0 | 4 | 2 | 2 | 3 | not equal | hi = 2 |
| 0 | 2 | 0 | 1 | 1 | equal | lo = 2 |
| 2 | 2 | — | — | — | loop ends | return nums[2] = 2 |

Found the single element, `2`, in 3 comparisons instead of scanning up to 9 elements. Time complexity is O(log n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: forgetting to force `mid` to be even (`if (mid % 2 == 1) mid--`) breaks the algorithm silently — comparing an odd-indexed element to its neighbor checks the WRONG half of a pair, giving an inconsistent, non-monotonic signal.

- The simple O(n) XOR trick is a valid alternative if the problem does not require O(log n), but it ignores the sorted structure entirely — worth mentioning both approaches in an interview.
- This is a "search on answer" problem where the answer space is array indices, and the monotonic predicate is about pairing alignment rather than a direct value comparison.
- Related problems: Find Minimum in Rotated Sorted Array (a different structural signal, same binary-search-on-index shape), Find First and Last Position of Element in Sorted Array (another problem exploiting a structural property of a sorted array with duplicates).
