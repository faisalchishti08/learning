---
card: leetcode-patterns
gi: 8
slug: squares-of-a-sorted-array
title: Squares of a Sorted Array
---

## 1. What it is

Given an integer array `nums` sorted in non-decreasing order (it may include negative numbers), return a new array of the squares of each number, also sorted in non-decreasing order. Example: `nums = [-4, -1, 0, 3, 10]` → squares are `[16, 1, 0, 9, 100]`, sorted: `[0, 1, 9, 16, 100]`.

## 2. Why & when

Negative numbers make squaring non-monotonic — the most negative value can produce the largest square. A full re-sort costs O(n log n). But the input's sortedness still helps: the **largest** squares always come from the two ends of the original array (the most negative or the most positive value), which is the two-pointers signal, used here to build the answer from the outside in.

## 3. Core concept

**Key idea:** at any point, the largest unplaced square is the square of whichever end (`nums[left]` or `nums[right]`) has the larger absolute value. Filling the result array from its **last** slot backward lets you place that largest value directly, without moving anything afterward.

**Steps:**
1. Create a result array the same length as `nums`. Set `left = 0`, `right = nums.length - 1`, `write = nums.length - 1`.
2. While `left <= right`:
   - Compare `abs(nums[left])` and `abs(nums[right])`.
   - Whichever is larger, square it, place that square at `result[write]`, move that pointer inward (`left++` or `right--`), and `write--`.
3. When `left > right`, the result array is fully filled, largest to smallest from the back.

**Why it is correct:** the candidate for "largest remaining square" can only ever be one of the two extremes of the still-unprocessed window `[left, right]`, because squaring is monotonic in absolute value, and the array is sorted so absolute values only decrease as you move inward from either end. Comparing just the two ends at each step, rather than scanning the whole window, is what makes this O(n).

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Squares of sorted array filling result from the back">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">nums = [-4, -1, 0, 3, 10]</text>
    <rect x="20" y="40" width="44" height="34" fill="#161b22" stroke="#79c0ff"/>
    <rect x="64" y="40" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="108" y="40" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="152" y="40" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="196" y="40" width="44" height="34" fill="#161b22" stroke="#f0883e"/>
    <text x="42" y="63" fill="#e6edf3" text-anchor="middle">-4</text>
    <text x="86" y="63" fill="#e6edf3" text-anchor="middle">-1</text>
    <text x="130" y="63" fill="#e6edf3" text-anchor="middle">0</text>
    <text x="174" y="63" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="218" y="63" fill="#e6edf3" text-anchor="middle">10</text>
    <text x="42" y="95" fill="#79c0ff" text-anchor="middle">left</text>
    <text x="218" y="95" fill="#f0883e" text-anchor="middle">right</text>
    <text x="20" y="130" fill="#8b949e">|10| &gt; |-4| -&gt; result[4]=100, right--, write--</text>
    <text x="20" y="152" fill="#8b949e">largest square always comes from one of the two ends</text>
  </g>
</svg>

The pointer with the larger absolute value produces the next-largest square, which is placed from the back of the result array.

## 5. Runnable example

```java
// SquaresSortedArray.java
import java.util.Arrays;

public class SquaresSortedArray {

    // Level 1 -- Brute force: square every element, then sort. O(n log n)
    // time -- ignores that the original order already tells you where the
    // largest values will come from.
    static int[] bruteForce(int[] nums) {
        int[] result = new int[nums.length];
        for (int i = 0; i < nums.length; i++) result[i] = nums[i] * nums[i];
        Arrays.sort(result);
        return result;
    }

    // KEY INSIGHT: the largest square is always at one of the two ends of
    // the sorted input, so filling the answer from its own back, largest
    // first, needs only one linear pass with two pointers.

    // Level 2 -- Optimal: two pointers filling from the back. O(n) time, O(n)
    // space for the output (required, since we must return a new array).
    public static int[] sortedSquares(int[] nums) {
        int n = nums.length;
        int[] result = new int[n];
        int left = 0, right = n - 1, write = n - 1;
        while (left <= right) {
            int leftSq = nums[left] * nums[left];
            int rightSq = nums[right] * nums[right];
            if (leftSq > rightSq) {
                result[write--] = leftSq;
                left++;
            } else {
                result[write--] = rightSq;
                right--;
            }
        }
        return result;
    }

    // Level 3 -- Hardened: an array of all non-negative or all negative
    // values still works, because the comparison only relies on absolute
    // value, not sign.
    static int[] hardened(int[] nums) {
        if (nums == null || nums.length == 0) return new int[0];
        return sortedSquares(nums);
    }

    public static void main(String[] args) {
        int[] nums = {-4, -1, 0, 3, 10};
        System.out.println("brute force: " + Arrays.toString(bruteForce(nums)));
        System.out.println("optimal:     " + Arrays.toString(sortedSquares(nums)));

        int[] allNegative = {-7, -3, -1};
        System.out.println("all negative: " + Arrays.toString(hardened(allNegative)));
    }
}
```

How to run: save as `SquaresSortedArray.java`, then run `java SquaresSortedArray.java`.

## 6. Walkthrough

Dry run of `sortedSquares({-4, -1, 0, 3, 10})`:

| step | left (val) | right (val) | leftSq | rightSq | winner | write index |
|---|---|---|---|---|---|---|
| 1 | 0 (-4) | 4 (10) | 16 | 100 | right (100) | 4 |
| 2 | 0 (-4) | 3 (3) | 16 | 9 | left (16) | 3 |
| 3 | 1 (-1) | 3 (3) | 1 | 9 | right (9) | 2 |
| 4 | 1 (-1) | 2 (0) | 1 | 0 | left (1) | 1 |
| 5 | 2 (0) | 2 (0) | 0 | 0 | right (0), right-- crosses left | 0 |

Result array filled from index 4 down to 0: `[0, 1, 9, 16, 100]`. Time complexity: O(n). Space complexity: O(n) for the required output array, O(1) beyond that.

## 7. Gotchas & takeaways

> Gotcha: comparing `nums[left]` and `nums[right]` directly (instead of their squares or absolute values) gives the wrong winner whenever a negative number's magnitude exceeds a positive one — always compare magnitude, not signed value.

- The output array itself is unavoidably O(n) space here — the O(1) space in this pattern usually refers to *auxiliary* space beyond the required output.
- Filling from the back is the trick whenever "the answer's largest values come from the input's edges."
- Related problems: Merge Sorted Array (also fills from the back), Sort an Array, Container With Most Water.
