---
card: leetcode-patterns
gi: 7
slug: merge-sorted-array
title: Merge Sorted Array
---

## 1. What it is

You are given two sorted integer arrays `nums1` and `nums2`, with `nums1` having length `m + n`: the first `m` slots hold its real elements, and the last `n` slots are `0` placeholders reserved for `nums2`'s elements. Merge `nums2` into `nums1` in place, so `nums1` becomes one sorted array of length `m + n`. Example: `nums1 = [1, 2, 3, 0, 0, 0]`, `m = 3`, `nums2 = [2, 5, 6]`, `n = 3` → result `[1, 2, 2, 3, 5, 6]`.

## 2. Why & when

Both inputs are sorted, and the merge must happen in place with no extra array — the classic signal for two pointers, but with a twist: merging from the front would overwrite `nums1` values you have not read yet. The fix is to merge **from the back**, since `nums1` conveniently has empty space there.

## 3. Core concept

**Key idea:** placing the largest remaining values first, at the end of `nums1`, never overwrites data you still need, because you always write into a slot at or beyond the largest index you have read from either array.

**Steps:**
1. Set three pointers: `p1 = m - 1` (last real element of `nums1`), `p2 = n - 1` (last element of `nums2`), `write = m + n - 1` (last slot of `nums1`, to fill next).
2. While `p1 >= 0` and `p2 >= 0`: compare `nums1[p1]` and `nums2[p2]`. Write the larger one at `nums1[write]`, then decrement that source pointer and `write`.
3. When `p2` runs out, `nums1`'s remaining prefix is already in place — nothing more to do.
4. When `p1` runs out first, copy any remaining `nums2` elements directly, since they are the smallest remaining values.

**Why it is correct:** merging from the back means every write target (`write`) is always at or after the highest index either `p1` or `p2` has read from, in `nums1`'s own storage. So you can never clobber a value before you have read it — the two live regions (unread `nums1` prefix, written suffix) never collide.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Merge sorted array writing from the back">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">nums1 = [1, 2, 3, 0, 0, 0]   nums2 = [2, 5, 6]</text>
    <rect x="20" y="40" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="64" y="40" width="44" height="34" fill="#161b22" stroke="#79c0ff"/>
    <rect x="108" y="40" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="152" y="40" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="196" y="40" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="240" y="40" width="44" height="34" fill="#f0883e" stroke="#f0883e"/>
    <text x="42" y="63" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="86" y="63" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="130" y="63" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="174" y="63" fill="#e6edf3" text-anchor="middle">.</text>
    <text x="218" y="63" fill="#e6edf3" text-anchor="middle">.</text>
    <text x="262" y="63" fill="#1a1a1a" text-anchor="middle">6</text>
    <text x="86" y="95" fill="#79c0ff" text-anchor="middle">p1=2 (val 3)</text>
    <text x="262" y="95" fill="#f0883e" text-anchor="middle">write=5</text>
    <text x="20" y="130" fill="#8b949e">compare nums1[p1]=3 vs nums2[p2]=6 -&gt; 6 is bigger -&gt; write 6, p2--, write--</text>
    <text x="20" y="152" fill="#8b949e">writing from the back never overwrites an unread nums1 value</text>
  </g>
</svg>

Writing from the highest index down keeps unread `nums1` values safe until they are actually read.

## 5. Runnable example

```java
// MergeSortedArray.java
import java.util.Arrays;

public class MergeSortedArray {

    // Level 1 -- Brute force: copy nums2 into the tail of nums1, then sort
    // the whole thing. O((m+n) log(m+n)) time, ignores that both halves are
    // already individually sorted.
    static void bruteForce(int[] nums1, int m, int[] nums2, int n) {
        for (int i = 0; i < n; i++) {
            nums1[m + i] = nums2[i];
        }
        Arrays.sort(nums1);
    }

    // KEY INSIGHT: nums1 has empty space exactly at its tail, so filling
    // from the back -- largest values first -- lets two pointers merge in
    // one linear pass without ever overwriting an unread value.

    // Level 2 -- Optimal: two pointers from the back. O(m+n) time, O(1) space.
    public static void merge(int[] nums1, int m, int[] nums2, int n) {
        int p1 = m - 1, p2 = n - 1, write = m + n - 1;
        while (p1 >= 0 && p2 >= 0) {
            if (nums1[p1] > nums2[p2]) {
                nums1[write--] = nums1[p1--];
            } else {
                nums1[write--] = nums2[p2--];
            }
        }
        while (p2 >= 0) {
            nums1[write--] = nums2[p2--];
        }
        // any remaining nums1[0..p1] is already correctly placed
    }

    // Level 3 -- Hardened: n == 0 (nothing to merge) and m == 0 (nums1 is
    // entirely placeholders) both fall out of the same loops correctly.
    static void hardened(int[] nums1, int m, int[] nums2, int n) {
        if (nums1.length != m + n) {
            throw new IllegalArgumentException("nums1 must have length m + n");
        }
        merge(nums1, m, nums2, n);
    }

    public static void main(String[] args) {
        int[] nums1 = {1, 2, 3, 0, 0, 0};
        merge(nums1, 3, new int[] {2, 5, 6}, 3);
        System.out.println("merged: " + Arrays.toString(nums1));

        int[] emptyM = {0, 0, 0};
        hardened(emptyM, 0, new int[] {1, 2, 3}, 3);
        System.out.println("m=0 case: " + Arrays.toString(emptyM));
    }
}
```

How to run: save as `MergeSortedArray.java`, then run `java MergeSortedArray.java`.

## 6. Walkthrough

Dry run of `merge({1,2,3,0,0,0}, 3, {2,5,6}, 3)`:

| step | p1 (val) | p2 (val) | write | write value | 
|---|---|---|---|---|
| 1 | 2 (3) | 2 (6) | 5 | 6 (nums2 wins) |
| 2 | 2 (3) | 1 (5) | 4 | 5 (nums2 wins) |
| 3 | 2 (3) | 0 (2) | 3 | 3 (nums1 wins) |
| 4 | 1 (2) | 0 (2) | 2 | 2 (tie, nums1[p1] not > nums2[p2], so nums2 wins) |
| 5 | 1 (2) | -1 | — | p2 exhausted, loop ends |

`nums1[0..1]` already holds `[1, 2]`, correctly placed. Final array: `[1, 2, 2, 3, 5, 6]`. Time complexity: O(m + n), one backward pass. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: merging from the **front** instead of the back overwrites `nums1` values you have not read yet, because the write pointer and the `p1` read pointer would occupy the same low-index region. Always merge from the back when the destination array's free space is at the end.

- The "in-place merge with reserved trailing space" shape is a strong signal to write from the back, not the front.
- After the main loop, only a `p2` leftover copy is needed — any leftover `nums1[0..p1]` is already in the right place.
- Related problems: Merge Two Sorted Lists (linked-list version, same back-to-front idea does not apply since lists have no trailing space — merge forward into a new list instead), Sort Colors.
