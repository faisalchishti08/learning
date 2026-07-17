---
card: leetcode-patterns
gi: 19
slug: sort-colors
title: Sort Colors
---

## 1. What it is

Given an array `nums` with only the values `0`, `1`, and `2` (representing red, white, and blue), sort it in place so all `0`s come first, then all `1`s, then all `2`s — without using a library sort. Example: `nums = [2, 0, 2, 1, 1, 0]` → `[0, 0, 1, 1, 2, 2]`.

## 2. Why & when

With only three distinct values, a full comparison sort is overkill. This calls for a **three-way partition**, a variant of two pointers that uses *three* markers instead of two: one for the boundary of `0`s, one for the boundary of `2`s, and a scanner walking between them. It is the same-direction filtering idea from Move Zeroes, extended to three buckets instead of two.

## 3. Core concept

**Key idea:** maintain three regions in the array at all times — `[0, low)` are confirmed `0`s, `[low, mid)` are confirmed `1`s, `[high+1, end)` are confirmed `2`s, and `[mid, high]` is unexamined.

**Steps:**
1. Set `low = 0`, `mid = 0`, `high = nums.length - 1`.
2. While `mid <= high`:
   - If `nums[mid] == 0`, swap `nums[low]` and `nums[mid]`, then `low++`, `mid++` (a `0` moves to the front region; the swapped-in value from `low` was already `1` or already handled, so `mid` is safe to also advance).
   - If `nums[mid] == 1`, it is already in the right region — just `mid++`.
   - If `nums[mid] == 2`, swap `nums[mid]` and `nums[high]`, then `high--` (do **not** advance `mid`, because the value swapped in from `high` has not been examined yet).
3. When `mid > high`, every element has been classified — the array is sorted.

**Why it is correct:** the invariant "everything before `low` is 0, everything from `low` to `mid` is 1, everything after `high` is 2" holds before and after every swap. The reason `mid` does not advance after a swap with `high` is that the incoming value is unknown; advancing `mid` there could skip classifying it.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sort colors three pointer partition">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">nums = [2, 0, 2, 1, 1, 0]</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#8b5cf6"/>
    <rect x="100" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="140" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="180" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="220" y="40" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="80" y="60" fill="#e6edf3" text-anchor="middle">0</text>
    <text x="120" y="60" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="160" y="60" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="200" y="60" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="240" y="60" fill="#e6edf3" text-anchor="middle">0</text>
    <text x="40" y="90" fill="#79c0ff" text-anchor="middle">low</text>
    <text x="80" y="90" fill="#8b5cf6" text-anchor="middle">mid</text>
    <text x="240" y="90" fill="#f0883e" text-anchor="middle">high</text>
    <text x="20" y="130" fill="#8b949e">nums[mid]=0 -&gt; swap(low, mid) -&gt; [0,2,2,1,1,0], low++, mid++</text>
  </g>
</svg>

Three pointers divide the array into a confirmed-0s region, a confirmed-1s region, and a confirmed-2s region, with `mid` scanning the unclassified middle.

## 5. Runnable example

```java
// SortColors.java
import java.util.Arrays;

public class SortColors {

    // Level 1 -- Brute force: count each value, then overwrite the array.
    // O(n) time, O(1) space -- correct and actually efficient, but it is a
    // counting-sort trick, not the three-pointer partition the problem is
    // testing; shown here to contrast approaches.
    static void bruteForce(int[] nums) {
        int[] count = new int[3];
        for (int v : nums) count[v]++;
        int idx = 0;
        for (int color = 0; color < 3; color++) {
            for (int c = 0; c < count[color]; c++) nums[idx++] = color;
        }
    }

    // KEY INSIGHT: with only three distinct values, one pass with three
    // pointers can fully classify every element by swapping it directly
    // into its final region -- no counting pass and no second pass needed.

    // Level 2 -- Optimal: Dutch National Flag three-way partition. O(n)
    // time, O(1) space, single pass.
    public static void sortColors(int[] nums) {
        int low = 0, mid = 0, high = nums.length - 1;
        while (mid <= high) {
            if (nums[mid] == 0) {
                swap(nums, low, mid);
                low++;
                mid++;
            } else if (nums[mid] == 1) {
                mid++;
            } else {
                swap(nums, mid, high);
                high--;
            }
        }
    }

    private static void swap(int[] a, int i, int j) {
        int tmp = a[i]; a[i] = a[j]; a[j] = tmp;
    }

    // Level 3 -- Hardened: an array that is already sorted, or one made of
    // a single repeated value, both terminate correctly since every branch
    // still respects the mid <= high invariant.
    static void hardened(int[] nums) {
        if (nums == null) throw new IllegalArgumentException("nums must not be null");
        sortColors(nums);
    }

    public static void main(String[] args) {
        int[] a = {2, 0, 2, 1, 1, 0};
        sortColors(a);
        System.out.println("optimal: " + Arrays.toString(a));

        int[] allOnes = {1, 1, 1};
        hardened(allOnes);
        System.out.println("all ones: " + Arrays.toString(allOnes));
    }
}
```

How to run: save as `SortColors.java`, then run `java SortColors.java`.

## 6. Walkthrough

Dry run of `sortColors({2, 0, 2, 1, 1, 0})`:

| step | low | mid | high | nums[mid] | action | array after |
|---|---|---|---|---|---|---|
| 1 | 0 | 0 | 5 | 2 | swap(mid,high), high-- | [0,0,2,1,1,2] |
| 2 | 0 | 0 | 4 | 0 | swap(low,mid), low++, mid++ | [0,0,2,1,1,2] |
| 3 | 1 | 1 | 4 | 0 | swap(low,mid) (no-op, same index), low++, mid++ | [0,0,2,1,1,2] |
| 4 | 2 | 2 | 4 | 2 | swap(mid,high), high-- | [0,0,1,1,2,2] |
| 5 | 2 | 2 | 3 | 1 | mid++ | [0,0,1,1,2,2] |
| 6 | 2 | 3 | 3 | 1 | mid++ | [0,0,1,1,2,2] |

`mid` (4) now exceeds `high` (3), loop stops. Final array: `[0, 0, 1, 1, 2, 2]`. Time complexity: O(n), one pass. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: advancing `mid` after a swap with `high` is the most common bug — the value just swapped in from `high` has never been classified, so skipping it (by advancing `mid`) can leave a `0` or `2` unsorted.

- This three-pointer shape is called the "Dutch National Flag" partition, after Edsger Dijkstra's original formulation.
- Related problems: Move Zeroes (two-way version of this same idea), Partition Array, Quicksort's partition step (the same three-way idea handles duplicate pivots efficiently).
