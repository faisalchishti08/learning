---
card: leetcode-patterns
gi: 4
slug: two-sum-ii-input-array-is-sorted
title: Two Sum II - Input Array Is Sorted
---

## 1. What it is

You are given a 1-indexed array `numbers` sorted in non-decreasing order, and an integer `target`. Find two numbers that add up to `target` and return their 1-indexed positions as `[index1, index2]` with `index1 < index2`. Example: `numbers = [2, 7, 11, 15]`, `target = 9` → return `[1, 2]`, since `numbers[1] + numbers[2] = 2 + 7 = 9`.

## 2. Why & when

Constraints: exactly one solution exists, you may not use the same element twice, and the array is already sorted — that sortedness is the signal for the **two pointers** pattern (opposite-ends variant). This problem is the canonical introduction to that pattern and appears, in disguise, inside harder problems like 3Sum and 4Sum.

## 3. Core concept

**Key idea:** because the array is sorted, the sum of the smallest and largest remaining elements moves predictably as you change which elements you pick.

**Steps:**
1. Set `left = 0` (first index) and `right = numbers.length - 1` (last index).
2. Compute `sum = numbers[left] + numbers[right]`.
3. If `sum == target`, you found the pair — return `[left + 1, right + 1]` (converting back to 1-indexed).
4. If `sum < target`, the sum is too small. Since the array is sorted, moving `right` left could only make the sum smaller or equal — never larger. So you must increase the sum: move `left` right, to the next larger value.
5. If `sum > target`, symmetric reasoning says move `right` left, to the next smaller value.

**Why it is correct:** at every step, you eliminate one element from consideration and *prove* it cannot be part of the answer. If `numbers[left] + numbers[right] < target`, then `numbers[left]` paired with anything at or before `right` is even smaller (array is sorted), so `numbers[left]` can never reach the target with any index ≤ `right`. It is safe to discard it by moving `left` forward. The symmetric argument holds for `right`.

## 4. Diagram

<svg viewBox="0 0 700 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two Sum II pointers converging on numbers 2 7 11 15 target 9">
  <g font-family="sans-serif" font-size="13">
    <rect x="20" y="20" width="60" height="36" fill="#161b22" stroke="#79c0ff" stroke-width="2"/>
    <rect x="80" y="20" width="60" height="36" fill="#161b22" stroke="#f0883e" stroke-width="2"/>
    <rect x="140" y="20" width="60" height="36" fill="#161b22" stroke="#30363d"/>
    <rect x="200" y="20" width="60" height="36" fill="#161b22" stroke="#30363d"/>
    <text x="50" y="43" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="110" y="43" fill="#e6edf3" text-anchor="middle">7</text>
    <text x="170" y="43" fill="#e6edf3" text-anchor="middle">11</text>
    <text x="230" y="43" fill="#e6edf3" text-anchor="middle">15</text>
    <text x="50" y="74" fill="#79c0ff" text-anchor="middle">left=0</text>
    <text x="230" y="74" fill="#f0883e" text-anchor="middle">right=3</text>
    <text x="20" y="100" fill="#8b949e">step 1: 2+15=17 &gt; 9  -&gt; move right left</text>
    <text x="20" y="120" fill="#8b949e">step 2: 2+11=13 &gt; 9  -&gt; move right left</text>
    <text x="20" y="140" fill="#8b949e">step 3: 2+7=9 == 9   -&gt; return [1,2]</text>
  </g>
</svg>

Right starts at the largest value and steps left each time the sum is too big, until it lands on the value that pairs correctly with left.

## 5. Runnable example

```java
// TwoSumII.java
import java.util.Arrays;

public class TwoSumII {

    // Level 1 -- Brute force: check every pair. O(n^2) time, O(1) space.
    // Wastes work: re-checks pairs whose failure was already implied by
    // earlier comparisons, because it ignores that the array is sorted.
    static int[] bruteForce(int[] numbers, int target) {
        for (int i = 0; i < numbers.length; i++) {
            for (int j = i + 1; j < numbers.length; j++) {
                if (numbers[i] + numbers[j] == target) {
                    return new int[] { i + 1, j + 1 };
                }
            }
        }
        return new int[0];
    }

    // KEY INSIGHT: sorted order means the sum moves monotonically as the
    // pointers move, so each comparison rules out one element for good --
    // no need to ever re-check it.

    // Level 2 -- Optimal: two pointers. O(n) time, O(1) space.
    public static int[] twoSum(int[] numbers, int target) {
        int left = 0, right = numbers.length - 1;
        while (left < right) {
            int sum = numbers[left] + numbers[right];
            if (sum == target) {
                return new int[] { left + 1, right + 1 };
            } else if (sum < target) {
                left++;
            } else {
                right--;
            }
        }
        return new int[0]; // problem guarantees a solution exists
    }

    // Level 3 -- Hardened: handles duplicate values and negative numbers,
    // both of which the core algorithm already covers correctly, plus an
    // explicit guard for arrays shorter than 2.
    static int[] hardened(int[] numbers, int target) {
        if (numbers == null || numbers.length < 2) {
            throw new IllegalArgumentException("need at least two numbers");
        }
        return twoSum(numbers, target);
    }

    public static void main(String[] args) {
        int[] numbers = {2, 7, 11, 15};
        System.out.println("brute force: " + Arrays.toString(bruteForce(numbers, 9)));
        System.out.println("optimal:     " + Arrays.toString(twoSum(numbers, 9)));

        int[] withNegatives = {-3, -1, 0, 2, 4, 8};
        System.out.println("with negatives (target 1): "
            + Arrays.toString(hardened(withNegatives, 1)));
    }
}
```

How to run: save as `TwoSumII.java`, then run `java TwoSumII.java`.

## 6. Walkthrough

Dry run of `twoSum({2, 7, 11, 15}, 9)`:

| step | left | right | numbers[left] | numbers[right] | sum | action |
|---|---|---|---|---|---|---|
| start | 0 | 3 | 2 | 15 | 17 | 17 > 9, right-- |
| 1 | 0 | 2 | 2 | 11 | 13 | 13 > 9, right-- |
| 2 | 0 | 1 | 2 | 7 | 9 | 9 == 9, return [1, 2] |

Final answer: `[1, 2]`, matching the 1-indexed positions of `2` and `7`. Time complexity: O(n), one pass with two pointers. Space complexity: O(1), only `left` and `right` are extra state.

## 7. Gotchas & takeaways

> Gotcha: forgetting to convert back to 1-indexed positions (`left + 1`, `right + 1`) is the most common mistake — the array itself uses normal 0-indexing in Java, but LeetCode's `numbers` array is defined as 1-indexed in the problem statement.

- Sorted input + pair-sum target is the strongest signal for opposite-ends two pointers.
- Never move both pointers on the same iteration — only the one implicated by the comparison.
- Related problems: 3Sum (fix one element, two-pointer the rest), 4Sum, Container With Most Water, Two Sum (unsorted, uses a hash map instead).
