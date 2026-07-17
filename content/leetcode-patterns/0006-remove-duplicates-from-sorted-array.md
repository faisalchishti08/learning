---
card: leetcode-patterns
gi: 6
slug: remove-duplicates-from-sorted-array
title: Remove Duplicates from Sorted Array
---

## 1. What it is

Given an integer array `nums` sorted in non-decreasing order, remove the duplicates in place so each unique value appears only once, keeping the relative order. Return `k`, the number of unique elements; the first `k` slots of `nums` must hold those unique values. Example: `nums = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]` → after the operation, the first 5 slots are `[0, 1, 2, 3, 4]`, and the method returns `5`.

## 2. Why & when

The constraint "in place, O(1) extra memory" plus "sorted array" is the signal for same-direction two pointers. Because the array is sorted, every duplicate of a value sits immediately next to the value — you never need to look further than the previous kept element to know whether the current one is a duplicate.

## 3. Core concept

**Key idea:** `slow` marks the end of the unique-elements-so-far region; `fast` scans forward looking for the next value different from the last one kept.

**Steps:**
1. If the array is empty, return 0.
2. Set `slow = 0` (the first element is always unique, being the first).
3. For `fast` from 1 to the end:
   - If `nums[fast] != nums[slow]`, it is a new unique value. Increment `slow`, then set `nums[slow] = nums[fast]`.
   - If `nums[fast] == nums[slow]`, it is a duplicate — do nothing, just let `fast` keep scanning.
4. Return `slow + 1`, the count of unique elements.

**Why it is correct:** because the array is sorted, all copies of a given value are contiguous. Comparing `nums[fast]` only to `nums[slow]` (the last kept unique value) is enough to detect a duplicate — you never need to compare against every previously kept value, because a value cannot reappear after a different value has appeared (sorted order forbids that).

## 4. Diagram

<svg viewBox="0 0 700 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Remove duplicates slow and fast pointers on 0 0 1 1 1 2">
  <g font-family="sans-serif" font-size="13">
    <rect x="20" y="20" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="64" y="20" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="108" y="20" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="152" y="20" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="196" y="20" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="240" y="20" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <text x="42" y="43" fill="#e6edf3" text-anchor="middle">0</text>
    <text x="86" y="43" fill="#e6edf3" text-anchor="middle">0</text>
    <text x="130" y="43" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="174" y="43" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="218" y="43" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="262" y="43" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="42" y="75" fill="#79c0ff" text-anchor="middle">slow</text>
    <text x="130" y="75" fill="#f0883e" text-anchor="middle">fast</text>
    <text x="20" y="110" fill="#8b949e">nums[fast]=1 != nums[slow]=0 -&gt; slow++, write 1 at slow</text>
    <text x="20" y="135" fill="#8b949e">result prefix grows one unique value at a time</text>
  </g>
</svg>

`slow` only advances when `fast` finds a genuinely new value, so duplicates are silently skipped over.

## 5. Runnable example

```java
// RemoveDuplicates.java
import java.util.Arrays;

public class RemoveDuplicates {

    // Level 1 -- Brute force: copy unique values into a new array using a
    // HashSet to detect duplicates, then copy back. O(n) time, O(n) space --
    // wastes space the in-place constraint says you should not need.
    static int bruteForce(int[] nums) {
        if (nums.length == 0) return 0;
        java.util.LinkedHashSet<Integer> seen = new java.util.LinkedHashSet<>();
        for (int n : nums) seen.add(n);
        int i = 0;
        for (int v : seen) nums[i++] = v;
        return seen.size();
    }

    // KEY INSIGHT: sorted order means duplicates of a value are always
    // adjacent, so comparing only against the last KEPT value (not every
    // value seen so far) is enough -- no set needed at all.

    // Level 2 -- Optimal: same-direction two pointers. O(n) time, O(1) space.
    public static int removeDuplicates(int[] nums) {
        if (nums.length == 0) return 0;
        int slow = 0;
        for (int fast = 1; fast < nums.length; fast++) {
            if (nums[fast] != nums[slow]) {
                slow++;
                nums[slow] = nums[fast];
            }
        }
        return slow + 1;
    }

    // Level 3 -- Hardened: works whether nums is empty, has one element, or
    // is entirely one repeated value -- all handled by the same loop, no
    // extra branches needed beyond the initial empty-array guard.
    static int hardened(int[] nums) {
        if (nums == null) throw new IllegalArgumentException("nums must not be null");
        return removeDuplicates(nums);
    }

    public static void main(String[] args) {
        int[] a = {0, 0, 1, 1, 1, 2, 2, 3, 3, 4};
        int k = removeDuplicates(a);
        System.out.println("k = " + k + ", unique prefix = "
            + Arrays.toString(Arrays.copyOf(a, k)));

        int[] single = {7};
        System.out.println("single element k = " + hardened(single));
    }
}
```

How to run: save as `RemoveDuplicates.java`, then run `java RemoveDuplicates.java`.

## 6. Walkthrough

Dry run of `removeDuplicates({0, 0, 1, 1, 1, 2})`:

| fast | nums[fast] | nums[slow] | action | slow after |
|---|---|---|---|---|
| 1 | 0 | 0 | duplicate, skip | 0 |
| 2 | 1 | 0 | new value: slow++, write 1 at index 1 | 1 |
| 3 | 1 | 1 | duplicate, skip | 1 |
| 4 | 1 | 1 | duplicate, skip | 1 |
| 5 | 2 | 1 | new value: slow++, write 2 at index 2 | 2 |

Final `slow = 2`, so `k = slow + 1 = 3`. The first 3 slots hold `[0, 1, 2]`. Time complexity: O(n), one pass. Space complexity: O(1), only `slow` and `fast` are extra.

## 7. Gotchas & takeaways

> Gotcha: comparing `nums[fast]` against `nums[fast - 1]` instead of `nums[slow]` looks similar but is wrong once you have written values out of their original positions — `slow` is the correct reference because it points at the last value actually *kept*, not the last value *scanned*.

- The "sorted + in-place + O(1) space" combination always points to same-direction two pointers, never a hash set.
- `slow` never moves unless a genuinely new value is found; it lags behind `fast` by exactly the number of duplicates skipped so far.
- Related problems: Remove Duplicates from Sorted Array II (allow up to two copies), Remove Element, Move Zeroes.
