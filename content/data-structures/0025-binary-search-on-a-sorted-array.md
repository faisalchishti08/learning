---
card: data-structures
gi: 25
slug: binary-search-on-a-sorted-array
title: Binary search on a sorted array
---

## 1. What it is

**Binary search** finds a target value in a **sorted** array by repeatedly checking the middle element and discarding the half of the array that cannot contain the target. Instead of scanning element by element (linear search, O(n)), it halves the search space at every step, finding the target — or proving it is absent — in O(log n) comparisons.

## 2. Why & when

Use binary search any time you need to search a sorted array (or any structure offering O(1) random access, like an array, but not a linked list) repeatedly or on large data. It relies entirely on the array being sorted; running it on unsorted data gives wrong, unpredictable results without any error or warning.

## 3. Core concept

**The invariant: the target, if present, always lies within `[lo, hi]`.** Before the loop starts, this is trivially true (the whole array). Each step either finds the target or narrows `[lo, hi]` in a way that provably preserves this invariant, because the sorted order guarantees everything outside the new range cannot be the target.

**Why checking the midpoint discards half.** Because the array is sorted, if `target > arr[mid]`, then `target` cannot be at `mid` or anywhere to its left (everything there is `<= arr[mid] < target`) — so the entire left half, including `mid`, is safely discarded, and the search continues in `[mid+1, hi]`. The symmetric argument discards the right half when `target < arr[mid]`.

**Why this gives O(log n).** Each comparison halves the remaining range. Starting from `n` elements, the range shrinks to `n/2`, then `n/4`, then `n/8`, and so on — reaching a single element after about `log2(n)` steps. Doubling the array size adds only one more comparison, not double the work.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Binary search narrowing a sorted array's search range by half at each of three steps until it finds the target">
  <g font-family="sans-serif" font-size="11">
    <text x="320" y="16" fill="#8b949e" text-anchor="middle">searching for 23 in a sorted array of 9 elements</text>
    <text x="320" y="42" fill="#e6edf3" text-anchor="middle">step 1: [1 5 9 12 [18] 23 27 31 40]  mid=18 &lt; 23 -&gt; search right half</text>
    <text x="320" y="70" fill="#e6edf3" text-anchor="middle">step 2: [23 27 [31] 40]  wait -- mid=27 &gt; 23 -&gt; search left half</text>
    <text x="320" y="98" fill="#e6edf3" text-anchor="middle">step 3: [[23]]  mid=23 -&gt; found at this index</text>
    <text x="320" y="140" fill="#79c0ff" text-anchor="middle">9 elements -&gt; found in 3 comparisons (log2(9) is about 3.2)</text>
  </g>
</svg>

Each comparison halves the search range. Nine elements reduce to the answer in about three steps, not nine.

## 5. Runnable example

```java
// BinarySearchSortedArray.java
public class BinarySearchSortedArray {

    // Basic: classic binary search, returns the index or -1 if not found.
    static int binarySearch(int[] sorted, int target) {
        int lo = 0, hi = sorted.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2; // avoids overflow vs (lo+hi)/2
            if (sorted[mid] == target) return mid;
            if (sorted[mid] < target) lo = mid + 1; // discard left half, including mid
            else hi = mid - 1;                       // discard right half, including mid
        }
        return -1; // target is not in the array
    }

    static void basicLevel() {
        int[] sorted = {1, 5, 9, 12, 18, 23, 27, 31, 40};
        System.out.println("basic: index of 23 -> " + binarySearch(sorted, 23));
        System.out.println("basic: index of 100 (absent) -> " + binarySearch(sorted, 100));
    }

    // Intermediate: lower bound -- first index where arr[i] >= target (works even with duplicates).
    static int lowerBound(int[] sorted, int target) {
        int lo = 0, hi = sorted.length; // hi is exclusive here
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (sorted[mid] < target) lo = mid + 1;
            else hi = mid; // sorted[mid] >= target, keep mid as a candidate
        }
        return lo; // first index with value >= target
    }

    static void intermediateLevel() {
        int[] sortedWithDupes = {1, 3, 3, 3, 5, 7, 9};
        int firstThree = lowerBound(sortedWithDupes, 3);
        System.out.println("intermediate: first index >= 3 -> " + firstThree); // index 1
    }

    // Advanced: search a sorted, rotated array -- one half is always still sorted.
    static int searchRotated(int[] rotated, int target) {
        int lo = 0, hi = rotated.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (rotated[mid] == target) return mid;
            if (rotated[lo] <= rotated[mid]) { // left half [lo..mid] is sorted
                if (rotated[lo] <= target && target < rotated[mid]) hi = mid - 1;
                else lo = mid + 1;
            } else { // right half [mid..hi] is sorted instead
                if (rotated[mid] < target && target <= rotated[hi]) lo = mid + 1;
                else hi = mid - 1;
            }
        }
        return -1;
    }

    static void advancedLevel() {
        int[] rotated = {4, 5, 6, 7, 0, 1, 2}; // originally sorted, then rotated
        System.out.println("advanced: index of 0 in rotated array -> " + searchRotated(rotated, 0));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `BinarySearchSortedArray.java`, then run `java BinarySearchSortedArray.java`.

## 6. Walkthrough

1. `basicLevel()` searches `{1,5,9,12,18,23,27,31,40}` for `23`. `mid=4` (`18`); `18 < 23`, so `lo` moves to `5`. `mid=7` (`31`); `31 > 23`, so `hi` moves to `6`. `mid=5` (`23`) matches — return index `5`.
2. Searching for `100` narrows the range each step until `lo > hi`, at which point the loop exits and `-1` is returned — `100` is provably absent since the invariant guarantees it would have been found if present.
3. `intermediateLevel()`'s `lowerBound` uses a half-open range `[lo, hi)` and keeps narrowing toward the *first* index whose value is `>= target`, even when duplicates exist — this is why it correctly returns index `1`, the first `3`, not one of the later duplicate `3`s.
4. `advancedLevel()`'s `searchRotated` handles a sorted array that has been rotated at an unknown pivot. At each `mid`, one of the two halves is still guaranteed to be sorted (`rotated[lo] <= rotated[mid]` tells you which one) — the algorithm uses that sorted half's bounds to decide which side can safely be discarded.

## 7. Gotchas & takeaways

> Gotcha: `(lo + hi) / 2` can overflow for very large arrays if `lo` and `hi` are both close to `Integer.MAX_VALUE`, since their sum can exceed the `int` range before the division happens. Use `lo + (hi - lo) / 2` instead, which never lets the intermediate sum overflow.

- Binary search requires sorted input — running it on unsorted data gives silently wrong answers, not an error.
- Each comparison halves the search range, giving O(log n) total comparisons instead of O(n) for a linear scan.
- Variants like `lowerBound` (first index `>= target`) and rotated-array search reuse the same halving idea with a different narrowing rule.
- Related concepts: [Random access by index (O(1))](0018-random-access-by-index-o-1.md) (why binary search needs array-like structures), [Two-pointer & sliding-window on arrays](0021-two-pointer-sliding-window-on-arrays.md).
