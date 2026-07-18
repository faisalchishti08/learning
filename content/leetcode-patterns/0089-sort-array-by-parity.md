---
card: leetcode-patterns
gi: 89
slug: sort-array-by-parity
title: Sort Array By Parity
---

## 1. What it is

Given an integer array `nums`, move all the even integers to the front, followed by all the odd integers, in any order within each group. Return the resulting array. Example: `nums = [3,1,2,4]` → a valid answer is `[2,4,3,1]` (evens first, odds after, in any order).

## 2. Why & when

This problem is grouped with cyclic sort because it uses the same "in-place, index-driven partitioning" style — one pointer advances only when its position holds a value that already belongs in the current segment, and a swap otherwise moves a value directly to where it should go, without a full comparison sort.

## 3. Core concept

**Key idea:** use two pointers, `left` starting at the beginning and `right` starting at the end. If `nums[left]` is already even, it is correctly placed — advance `left`. If `nums[right]` is already odd, it is correctly placed — retreat `right`. Otherwise, `nums[left]` is odd and `nums[right]` is even, so swap them — both become correctly placed in one move.

**Steps:**
1. Set `left = 0`, `right = nums.length - 1`.
2. While `left < right`:
   - If `nums[left]` is even, `left++` (it belongs in the front segment already).
   - Else if `nums[right]` is odd, `right--` (it belongs in the back segment already).
   - Else, swap `nums[left]` and `nums[right]` (an odd value at `left` trades places with an even value at `right`).
3. Return `nums`.

**Why it is correct:** every swap places one odd number into the back half and one even number into the front half simultaneously — both moves happen in a single operation and neither value needs to move again. The two pointers converge toward the middle, and since every element is examined at most once by each pointer, the partition finishes in one linear pass.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two pointers partitioning even and odd numbers">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">nums = [3, 1, 2, 4]</text>
    <rect x="20" y="45" width="40" height="26" fill="#161b22" stroke="#f0883e"/><text x="40" y="63" fill="#e6edf3" text-anchor="middle">3</text>
    <rect x="60" y="45" width="40" height="26" fill="#161b22" stroke="#30363d"/><text x="80" y="63" fill="#e6edf3" text-anchor="middle">1</text>
    <rect x="100" y="45" width="40" height="26" fill="#161b22" stroke="#30363d"/><text x="120" y="63" fill="#e6edf3" text-anchor="middle">2</text>
    <rect x="140" y="45" width="40" height="26" fill="#161b22" stroke="#79c0ff"/><text x="160" y="63" fill="#e6edf3" text-anchor="middle">4</text>
    <text x="40" y="35" fill="#f0883e" font-size="10">left (odd)</text>
    <text x="160" y="35" fill="#79c0ff" font-size="10">right (even)</text>
    <text x="20" y="100" fill="#8b949e">left holds odd 3, right holds even 4 -&gt; swap -&gt; [4, 1, 2, 3]</text>
    <text x="20" y="125" fill="#8b949e">pointers converge; result has evens (4,2) before odds (1,3)</text>
  </g>
</svg>

`nums[left] = 3` is odd and `nums[right] = 4` is even, so a single swap correctly places both — one becomes the new front-most even, the other the new back-most odd.

## 5. Runnable example

```java
// SortArrayByParity.java
import java.util.*;

public class SortArrayByParity {

    // Level 1 -- Brute force: build two new lists (evens, odds), then
    // concatenate. O(n) time, O(n) space -- wastes memory an in-place
    // two-pointer swap does not need.
    static int[] bruteForce(int[] nums) {
        List<Integer> evens = new ArrayList<>(), odds = new ArrayList<>();
        for (int v : nums) {
            if (v % 2 == 0) evens.add(v); else odds.add(v);
        }
        evens.addAll(odds);
        int[] result = new int[nums.length];
        for (int i = 0; i < result.length; i++) result[i] = evens.get(i);
        return result;
    }

    // KEY INSIGHT: a value that is already correctly placed (even at the
    // front, odd at the back) never needs to move -- only a mismatched
    // pair (odd at front, even at back) needs a single swap to fix BOTH
    // positions at once.

    // Level 2 -- Optimal: two pointers converging from both ends.
    // O(n) time, O(1) extra space.
    public static int[] sortArrayByParity(int[] nums) {
        int left = 0, right = nums.length - 1;
        while (left < right) {
            if (nums[left] % 2 == 0) {
                left++;
            } else if (nums[right] % 2 != 0) {
                right--;
            } else {
                int temp = nums[left];
                nums[left] = nums[right];
                nums[right] = temp;
            }
        }
        return nums;
    }

    // Level 3 -- Hardened: all-even and all-odd arrays, where the
    // pointers should simply scan through without ever swapping.
    static int[] hardened(int[] nums) {
        return sortArrayByParity(nums);
    }

    public static void main(String[] args) {
        int[] a = {3, 1, 2, 4};
        System.out.println("brute force: " + Arrays.toString(bruteForce(a.clone())));
        System.out.println("optimal:     " + Arrays.toString(sortArrayByParity(a)));

        int[] allOdd = {1, 3, 5};
        System.out.println("all odd:  " + Arrays.toString(hardened(allOdd)));
    }
}
```

How to run: save as `SortArrayByParity.java`, then run `java SortArrayByParity.java`.

## 6. Walkthrough

Dry run of `sortArrayByParity({3, 1, 2, 4})`:

| step | left | right | nums[left] | nums[right] | action | array |
|---|---|---|---|---|---|---|
| start | 0 | 3 | 3 | 4 | 3 odd, 4 even -> swap | [4,1,2,3] |
| 1 | 0 | 3 | 4 | 3 | 4 even -> left++ | [4,1,2,3] |
| 2 | 1 | 3 | 1 | 3 | 3 (right) odd -> right-- | [4,1,2,3] |
| 3 | 1 | 2 | 1 | 2 | 1 odd, 2 even -> swap | [4,2,1,3] |
| 4 | 1 | 2 | 2 | 1 | 2 even -> left++ | [4,2,1,3] |
| — | 2 | 2 | — | — | left == right, loop ends | |

Result: `[4, 2, 1, 3]` — evens `4, 2` before odds `1, 3`. Time complexity: O(n), one pass with pointers converging. Space complexity: O(1), fully in place.

## 7. Gotchas & takeaways

> Gotcha: using `if`/`else if`/`else` incorrectly (e.g. checking `nums[left]` odd and `nums[right]` even as two separate independent `if` statements instead of a true 3-way branch) can cause both pointers to move past each other without ever performing the needed swap.

- Order within each half (evens, odds) is unspecified by the problem, which is what allows an O(1)-space, single-pass swap solution instead of a stable partition.
- Related problems: Cyclic sort's core template (index-driven, in-place placement), Sort Colors (three-way partitioning instead of two).
