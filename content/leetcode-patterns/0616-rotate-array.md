---
card: leetcode-patterns
gi: 616
slug: rotate-array
title: Rotate Array
---

## 1. What it is

Given an integer array `nums`, rotate it to the right by `k` steps, in place. Example: `nums=[1,2,3,4,5,6,7], k=3` → `[5,6,7,1,2,3,4]` (the last 3 elements move to the front, and everything else shifts right by 3).

## 2. Why & when

The naive approach — rotate one step at a time, `k` times — is O(n*k), too slow for large `k`. A single-pass O(n) shifting approach using a temporary array is simple but uses O(n) extra space. The elegant in-place, O(1)-extra-space solution uses a geometric trick: **three reversals**, which is worth recognizing as a general technique for "rotate a sequence" problems whenever O(1) space is required.

## 3. Core concept

**Key idea:** rotating an array right by `k` steps is equivalent to reversing the *whole* array, then reversing each of its two resulting segments (the first `k` elements, and the remaining `n-k` elements) independently. This three-step reversal sequence achieves the rotation using only O(1) extra space (a few index variables for the in-place reversal), no temporary array.

**Steps:**
1. Normalize `k`: since rotating by `n` steps returns the array to its original order, only `k % n` actually matters — compute `k = k % n` first (this also handles `k > n`, and avoids wasted work).
2. Reverse the entire array, `[0, n-1]`.
3. Reverse the first `k` elements, `[0, k-1]`.
4. Reverse the remaining `n-k` elements, `[k, n-1]`.

**Why three reversals of specific ranges produce a right rotation:** reversing the whole array puts every element in reverse order, but also puts the elements that need to end up at the front (the original last `k` elements) at the very front, just in reverse order among themselves. Re-reversing just that front segment (`[0, k-1]`) restores their correct relative order. Symmetrically, re-reversing the remaining segment (`[k, n-1]`) restores the correct relative order of the rest. Both segments are now individually correct, and their combined position (first-`k`-then-rest) is exactly a right rotation by `k`.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Rotating [1,2,3,4,5,6,7] right by 3 using three reversals: whole array, then each of the two resulting segments">
  <g font-family="sans-serif" font-size="11">
    <text x="120" y="20" fill="#8b949e" text-anchor="middle">original</text>
    <text x="120" y="35" fill="#e6edf3" text-anchor="middle">1 2 3 4 5 6 7</text>
    <text x="350" y="20" fill="#8b949e" text-anchor="middle">after reversing whole array</text>
    <text x="350" y="35" fill="#f0883e" text-anchor="middle">7 6 5 4 3 2 1</text>
    <text x="580" y="20" fill="#8b949e" text-anchor="middle">after reversing [0,2] and [3,6]</text>
    <text x="580" y="35" fill="#3fb950" text-anchor="middle">5 6 7 1 2 3 4</text>
    <text x="350" y="100" fill="#79c0ff" text-anchor="middle">segment [0,2] "765" -&gt; reversed to "567"; segment [3,6] "4321" -&gt; reversed to "1234"</text>
  </g>
</svg>

Reversing the whole array first, then re-reversing each of the two segments that should end up in the front and back, produces the rotation without any extra array.

## 5. Runnable example

**Level 1 — Brute force.** Rotate one position at a time, `k` times, shifting every element right by one and wrapping the last element to the front on each pass. O(n*k) time — too slow for large `k`.

**KEY INSIGHT:** a right rotation by `k` is exactly "reverse the whole thing, then un-reverse each of the two pieces that make it up" — this geometric identity turns an O(n*k) repeated-shift approach into a single O(n) pass (three reversals, each touching disjoint or overlapping ranges, but the total work across all three is still linear in `n`).

**Level 2 — Optimal.** Three in-place reversals (whole array, first `k`, remaining `n-k`), O(n) time, O(1) extra space.

**Level 3 — Hardened.** Correctly normalizes `k` with `k % n` first, handling `k >= n` (and `k == 0`, which becomes a no-op rotation after normalization).

```java
// RotateArray.java
import java.util.*;

public class RotateArray {

    private static void reverse(int[] nums, int left, int right) {
        while (left < right) {
            int tmp = nums[left];
            nums[left] = nums[right];
            nums[right] = tmp;
            left++;
            right--;
        }
    }

    public static void rotate(int[] nums, int k) {
        int n = nums.length;
        k %= n;

        reverse(nums, 0, n - 1);
        reverse(nums, 0, k - 1);
        reverse(nums, k, n - 1);
    }

    public static void main(String[] args) {
        int[] nums = {1, 2, 3, 4, 5, 6, 7};
        rotate(nums, 3);
        System.out.println(Arrays.toString(nums)); // [5, 6, 7, 1, 2, 3, 4]
    }
}
```

**How to run:** save as `RotateArray.java`, then run `java RotateArray.java`.

## 6. Walkthrough

Trace `rotate([1,2,3,4,5,6,7], 3)`:

1. `k = 3 % 7 = 3` (no change, already less than `n`).
2. Reverse whole array `[0,6]`: `[1,2,3,4,5,6,7]` -> `[7,6,5,4,3,2,1]`.
3. Reverse first `k=3` elements, `[0,2]`: segment `[7,6,5]` -> `[5,6,7]`. Array: `[5,6,7,4,3,2,1]`.
4. Reverse remaining `n-k=4` elements, `[3,6]`: segment `[4,3,2,1]` -> `[1,2,3,4]`. Array: `[5,6,7,1,2,3,4]`.

Final: `[5,6,7,1,2,3,4]` — the last 3 original elements (`5,6,7`) are now at the front, in their original relative order, matching the expected right rotation by 3.

## 7. Gotchas & takeaways

> Gotcha: forgetting to normalize `k` with `k %= n` before using it as a range boundary causes an `ArrayIndexOutOfBoundsException` (or worse, silently wrong behavior) whenever `k >= n` — a rotation by exactly `n` (or any multiple of `n`) should leave the array unchanged, which only happens correctly if `k` is reduced modulo `n` first.

- Signal: "rotate a sequence in place, O(1) extra space" is the three-reversals signal — reverse the whole, then re-reverse each of the two resulting pieces.
- The technique generalizes to left rotation too, by swapping which segment (`[0,k-1]` vs `[k,n-1]`) corresponds to which end of the rotation.
- Related problems: Reverse Words in a String (a related application of the same "reverse the whole, then re-reverse the pieces" idea, applied to word order within a sentence).
