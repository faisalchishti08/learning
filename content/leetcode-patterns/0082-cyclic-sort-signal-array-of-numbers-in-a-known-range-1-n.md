---
card: leetcode-patterns
gi: 82
slug: cyclic-sort-signal-array-of-numbers-in-a-known-range-1-n
title: Cyclic Sort — signal: array of numbers in a known range [1..n]
---

## 1. What it is

Cyclic sort is a technique for arrays containing `n` numbers drawn from a known, bounded range — typically `[1, n]` or `[0, n-1]` — where each value's correct sorted position is computable directly from the value itself (value `v` belongs at index `v - 1`, for example). You place each number at its correct index by repeatedly swapping, without comparisons.

## 2. Why & when

A general-purpose sort like quicksort or mergesort needs O(n log n) time because it does not know anything about the range of values. But when the array holds exactly the numbers `1` through `n` (possibly with some missing or duplicated), the target index for each value is known in advance — no comparisons are needed, just place each value where it belongs.

Learn to recognize these signals in a problem statement:

- **"Array of `n` numbers in the range `[1, n]`"** (or `[0, n-1]`), possibly with duplicates or missing values — the strongest signal.
- **"Find the missing number(s)"** or **"find the duplicate number(s)"** in such a bounded array.
- **"Sort in O(n) time and O(1) space"** where the values themselves define their target positions.
- **A constraint that values and indices are related**, such as "every integer appears once except one which appears twice, and one which is missing."

The alternative is a full comparison-based sort (O(n log n)) or a hash set to track seen values (O(n) extra space). Cyclic sort is the answer specifically when the value range matches the array length, letting index arithmetic replace both the sort and the extra memory.

## 3. Core concept

**Key idea:** walk through the array with an index `i`. At each position, check whether the value there belongs at that position (`nums[i] == i + 1` for a `[1,n]` range). If not, swap it with whatever is at its correct target index. Only advance `i` once the value at position `i` is correctly placed (or is a duplicate/out-of-range value that can never be placed there).

**Steps:**
1. Set `i = 0`.
2. While `i < n`:
   - Compute `correctIndex = nums[i] - 1` (for a `[1,n]` range).
   - If `nums[i]` is within range and `nums[i] != nums[correctIndex]`, swap `nums[i]` and `nums[correctIndex]`.
   - Otherwise, advance `i++`.
3. After the loop, every value that could be placed correctly is at its correct index; any position where `nums[i] != i + 1` reveals a missing or duplicated value.

**Why it works:** each swap places at least one number into its final, correct position — a number never needs to move again once `nums[correctIndex] == correctIndex + 1`. Since there are at most `n` numbers and each swap fixes one, the total number of swaps across the whole array is bounded by `n`.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cyclic sort placing each value at its index by swapping">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">nums = [3, 1, 2], target: value v belongs at index v-1</text>
    <rect x="20" y="45" width="40" height="26" fill="#161b22" stroke="#f0883e"/><text x="40" y="63" fill="#e6edf3" text-anchor="middle">3</text>
    <rect x="60" y="45" width="40" height="26" fill="#161b22" stroke="#30363d"/><text x="80" y="63" fill="#e6edf3" text-anchor="middle">1</text>
    <rect x="100" y="45" width="40" height="26" fill="#161b22" stroke="#30363d"/><text x="120" y="63" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="20" y="35" fill="#8b949e" font-size="10">idx 0</text><text x="60" y="35" fill="#8b949e" font-size="10">idx 1</text><text x="100" y="35" fill="#8b949e" font-size="10">idx 2</text>
    <text x="20" y="100" fill="#8b949e">nums[0]=3 belongs at index 2 -&gt; swap with nums[2]=2 -&gt; [2,1,3]</text>
    <text x="20" y="120" fill="#8b949e">nums[0]=2 belongs at index 1 -&gt; swap with nums[1]=1 -&gt; [1,2,3]</text>
    <text x="20" y="140" fill="#3fb950">nums[0]=1 is at index 0 -&gt; correct, advance -&gt; fully sorted</text>
  </g>
</svg>

Each swap sends a value directly to its correct index; the loop only advances past positions that are already correctly placed.

## 5. Runnable example

A generic cyclic sort skeleton you can adapt to related problems in this pattern.

```java
// CyclicSortSignal.java
public class CyclicSortSignal {

    static void cyclicSort(int[] nums) {
        int i = 0;
        while (i < nums.length) {
            int correctIndex = nums[i] - 1;
            if (nums[i] >= 1 && nums[i] <= nums.length && nums[i] != nums[correctIndex]) {
                swap(nums, i, correctIndex);
            } else {
                i++;
            }
        }
    }

    static void swap(int[] nums, int a, int b) {
        int temp = nums[a];
        nums[a] = nums[b];
        nums[b] = temp;
    }

    public static void main(String[] args) {
        int[] nums = {3, 1, 2};
        cyclicSort(nums);
        System.out.println(java.util.Arrays.toString(nums));
    }
}
```

How to run: save as `CyclicSortSignal.java`, then run `java CyclicSortSignal.java`.

## 6. Walkthrough

1. `i = 0`: `nums[0] = 3`, belongs at index `2`. `nums[2] = 2 != 3`, so swap: `[2, 1, 3]`.
2. `i = 0` (unchanged, re-check): `nums[0] = 2`, belongs at index `1`. `nums[1] = 1 != 2`, so swap: `[1, 2, 3]`.
3. `i = 0` (unchanged, re-check): `nums[0] = 1`, belongs at index `0`. Already correct — advance `i = 1`.
4. `i = 1`: `nums[1] = 2`, belongs at index `1`. Already correct — advance `i = 2`.
5. `i = 2`: `nums[2] = 3`, belongs at index `2`. Already correct — advance `i = 3`. Loop ends. Array is fully sorted: `[1, 2, 3]`.

## 7. Gotchas & takeaways

> Gotcha: incrementing `i` after every swap (instead of only when the current position is already correct) can leave a value unswapped, since the value just moved into position `i` still needs to be checked before moving on.

- Cyclic sort only needs O(1) extra space, unlike a hash-set approach which needs O(n).
- This pattern only works because the value range is tied to the array length — it does not generalize to arbitrary unsorted arrays.
