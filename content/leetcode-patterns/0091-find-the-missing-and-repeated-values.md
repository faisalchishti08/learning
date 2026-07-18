---
card: leetcode-patterns
gi: 91
slug: find-the-missing-and-repeated-values
title: Find the Missing and Repeated Values
---

## 1. What it is

You are given a 2D `n x n` grid that was meant to contain each integer from `1` to `n²` exactly once, but one number `a` got duplicated and, as a result, another number `b` is missing. Return `[a, b]`. Example: `grid = [[1,3],[2,2]]` → `[2, 4]` (`2` is duplicated, `4` is missing).

## 2. Why & when

This is Set Mismatch's direct generalization to a 2D grid: the same "exactly one duplicate, exactly one missing" structure applies, just flattened from an `n x n` grid instead of a 1D array of length `n`. Treating the grid as a flat array of `n²` values and applying cyclic sort reduces it to the exact same algorithm.

## 3. Core concept

**Key idea:** flatten the grid into a 1D array of length `n²` (either by copying, or by computing row/column indices on the fly). Apply the same cyclic sort placement used in Set Mismatch: place each value `v` at flat index `v - 1`. The one leftover mismatch reveals both the duplicate and the missing value.

**Steps:**
1. Flatten the `n x n` grid into a 1D array `nums` of length `n²`, where `nums[r * n + c] = grid[r][c]`.
2. Run cyclic sort: place each value `v` at index `v - 1` by swapping, exactly as in Set Mismatch.
3. Scan for the one index `i` where `nums[i] != i + 1`. The duplicate is `nums[i]`; the missing number is `i + 1`.

**Why it is correct:** flattening a 2D grid into a 1D array preserves every value and its multiplicity — the grid's 2D shape has no bearing on which values are duplicated or missing. Once flattened, the problem is identical to Set Mismatch, so the same cyclic sort proof applies unchanged.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Flattening a 2D grid into a 1D array for cyclic sort">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">grid = [[1,3],[2,2]]  (n=2, values should be 1..4)</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/><text x="40" y="60" fill="#e6edf3" text-anchor="middle">1</text>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/><text x="80" y="60" fill="#e6edf3" text-anchor="middle">3</text>
    <rect x="20" y="70" width="40" height="30" fill="#161b22" stroke="#79c0ff"/><text x="40" y="90" fill="#e6edf3" text-anchor="middle">2</text>
    <rect x="60" y="70" width="40" height="30" fill="#161b22" stroke="#79c0ff"/><text x="80" y="90" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="150" y="60" fill="#8b949e">flatten row by row (r*n+c) -&gt;</text>
    <rect x="330" y="55" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="345" y="71" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <rect x="360" y="55" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="375" y="71" fill="#e6edf3" text-anchor="middle" font-size="10">3</text>
    <rect x="390" y="55" width="30" height="24" fill="#161b22" stroke="#3fb950"/><text x="405" y="71" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <rect x="420" y="55" width="30" height="24" fill="#161b22" stroke="#f0883e"/><text x="435" y="71" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <text x="20" y="140" fill="#8b949e">flat array = [1,3,2,2] -&gt; cyclic sort finds index 3 mismatched -&gt; duplicate=2, missing=4</text>
  </g>
</svg>

Flattening `grid` row by row turns the 2D duplicate/missing problem into the exact same 1D cyclic sort problem solved in Set Mismatch.

## 5. Runnable example

```java
// FindTheMissingAndRepeatedValues.java
import java.util.*;

public class FindTheMissingAndRepeatedValues {

    // Level 1 -- Brute force: count occurrences of every value 1..n^2
    // using a counts array, scan for count-2 (duplicate) and count-0
    // (missing). O(n^2) time, O(n^2) space -- wastes memory the
    // cyclic-sort in-place approach does not need.
    static int[] bruteForce(int[][] grid) {
        int n = grid.length;
        int[] count = new int[n * n + 1];
        for (int[] row : grid) for (int v : row) count[v]++;
        int duplicate = -1, missing = -1;
        for (int v = 1; v <= n * n; v++) {
            if (count[v] == 2) duplicate = v;
            if (count[v] == 0) missing = v;
        }
        return new int[] {duplicate, missing};
    }

    // KEY INSIGHT: flattening the grid turns this into EXACTLY the Set
    // Mismatch problem -- the 2D shape carries no extra information
    // relevant to finding the one duplicate and one missing value.

    // Level 2 -- Optimal: flatten, cyclic sort, find the one mismatch.
    // O(n^2) time, O(1) extra space (beyond the flattened copy).
    public static int[] findMissingAndRepeatedValues(int[][] grid) {
        int n = grid.length;
        int size = n * n;
        int[] nums = new int[size];
        for (int r = 0; r < n; r++) {
            for (int c = 0; c < n; c++) {
                nums[r * n + c] = grid[r][c];
            }
        }

        int i = 0;
        while (i < size) {
            int correct = nums[i] - 1;
            if (nums[i] != nums[correct]) {
                int temp = nums[i];
                nums[i] = nums[correct];
                nums[correct] = temp;
            } else {
                i++;
            }
        }

        for (i = 0; i < size; i++) {
            if (nums[i] != i + 1) {
                return new int[] {nums[i], i + 1};
            }
        }
        return new int[] {-1, -1};
    }

    // Level 3 -- Hardened: a 1x1 grid, where the only possible value
    // must be 1 -- no duplicate or missing value is possible in that
    // degenerate case, but the general grid sizes used here are 2x2+.
    static int[] hardened(int[][] grid) {
        return findMissingAndRepeatedValues(grid);
    }

    public static void main(String[] args) {
        int[][] grid = {{1, 3}, {2, 2}};
        System.out.println("brute force: " + Arrays.toString(bruteForce(grid)));
        System.out.println("optimal:     " + Arrays.toString(findMissingAndRepeatedValues(grid)));

        int[][] larger = {{9, 1, 7}, {8, 9, 2}, {3, 4, 6}};
        System.out.println("3x3 grid:    " + Arrays.toString(hardened(larger)));
    }
}
```

How to run: save as `FindTheMissingAndRepeatedValues.java`, then run `java FindTheMissingAndRepeatedValues.java`.

## 6. Walkthrough

Dry run of `findMissingAndRepeatedValues([[1,3],[2,2]])`, flattened to `nums = [1,3,2,2]`, `size = 4`:

| step | i | nums[i] | correct | nums[correct] | equal? | action |
|---|---|---|---|---|---|---|
| 1 | 0 | 1 | 0 | 1 | yes | advance |
| 2 | 1 | 3 | 2 | 2 | no | swap nums[1],nums[2] -> [1,2,3,2] |
| 3 | 1 | 2 | 1 | 2 | yes | advance |
| 4 | 2 | 3 | 2 | 3 | yes | advance |
| 5 | 3 | 2 | 1 | 2 | yes | advance |

Placement loop ends. Scan: index `3` holds `2` but expects `4` — mismatch. Return `[2, 4]` (duplicate `2`, missing `4`). Time complexity: O(n²), matching the number of grid cells. Space complexity: O(n²) for the flattened copy, or O(1) extra if the grid can be flattened via index arithmetic in place.

## 7. Gotchas & takeaways

> Gotcha: forgetting to convert between the flat index and the 2D grid coordinates correctly (`row = i / n`, `col = i % n`) if you choose to answer using grid positions instead of just the values — the values themselves (as computed above) do not need this conversion, but a variant asking for grid *positions* would.

- Recognizing this as Set Mismatch after a simple flatten is the whole difficulty — no new algorithm is needed once the grid becomes a 1D array.
- Related problems: Set Mismatch (the direct 1D version), Find All Duplicates in an Array (multiple duplicates instead of exactly one).
