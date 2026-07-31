---
card: data-structures
gi: 28
slug: arrays-utility-class-sort-fill-copyof-binarysearch
title: Arrays utility class (sort, fill, copyOf, binarySearch)
---

## 1. What it is

`java.util.Arrays` is a utility class of `static` helper methods for working with plain arrays — you never instantiate it, you just call methods like `Arrays.sort(arr)` directly on the class. It covers the operations you would otherwise hand-write yourself: sorting, filling with a value, copying (with or without resizing), searching, comparing, and printing arrays.

## 2. Why & when

Reach for `Arrays` methods instead of hand-rolled loops whenever you need a common array operation — they are well-tested, often more optimized than a naive loop (e.g. `Arrays.sort` uses a tuned dual-pivot quicksort for primitives), and communicate intent clearly. Knowing their exact time complexity matters for choosing the right one under a performance budget.

## 3. Core concept

**`Arrays.sort(arr)` — O(n log n).** For primitive arrays it uses a dual-pivot quicksort variant; for object arrays (which need a stable sort, since equal elements' relative order can matter with custom comparators) it uses a variant of merge sort called Timsort. Both are O(n log n) average case.

**`Arrays.fill(arr, value)` — O(n).** Overwrites every slot with the same value in one pass — useful for resetting a "visited" or "distance" array before an algorithm runs.

**`Arrays.copyOf(arr, newLength)` and `Arrays.copyOfRange(arr, from, to)` — O(n).** Both allocate a *new* array and copy elements in; `copyOf` can also grow the array, filling any extra slots with the type's default value (this is exactly what `ArrayList`'s internal resize uses).

**`Arrays.binarySearch(sortedArr, target)` — O(log n), but only on sorted input.** Like manual binary search, it requires the array to already be sorted; running it on unsorted data gives an unspecified, unreliable result with no error.

**`Arrays.equals` vs `==`.** `arr1 == arr2` checks reference identity (same object); `Arrays.equals(arr1, arr2)` checks that both arrays have the same length and equal elements at every position — the content comparison you almost always actually want.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Five Arrays utility methods and their complexity: sort O(n log n), fill O(n), copyOf O(n), binarySearch O(log n)">
  <g font-family="sans-serif" font-size="12">
    <rect x="30" y="30" width="130" height="30" fill="#161b22" stroke="#3fb950"/><text x="95" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">sort() O(n log n)</text>
    <rect x="170" y="30" width="130" height="30" fill="#161b22" stroke="#3fb950"/><text x="235" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">fill() O(n)</text>
    <rect x="310" y="30" width="130" height="30" fill="#161b22" stroke="#3fb950"/><text x="375" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">copyOf() O(n)</text>
    <rect x="450" y="30" width="150" height="30" fill="#161b22" stroke="#3fb950"/><text x="525" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">binarySearch() O(log n)</text>
    <text x="320" y="100" fill="#79c0ff" text-anchor="middle">binarySearch requires sorted input -- always sort() first if unsure</text>
  </g>
</svg>

Each `Arrays` method has a known complexity; `binarySearch` is the outlier that carries a precondition (sorted input) the others do not.

## 5. Runnable example

```java
// ArraysUtilityClass.java
import java.util.Arrays;

public class ArraysUtilityClass {

    // Basic: sort, fill, and toString.
    static void basicLevel() {
        int[] nums = {5, 2, 8, 1, 9};
        Arrays.sort(nums); // O(n log n), sorts in place
        System.out.println("basic: sorted -> " + Arrays.toString(nums));

        int[] visited = new int[5];
        Arrays.fill(visited, -1); // O(n), overwrite every slot
        System.out.println("basic: filled -> " + Arrays.toString(visited));
    }

    // Intermediate: copyOf (grows/shrinks into a new array) and copyOfRange (extracts a sub-range).
    static void intermediateLevel() {
        int[] original = {1, 2, 3};
        int[] grown = Arrays.copyOf(original, 5); // new array, extra slots default to 0
        System.out.println("intermediate: copyOf grown -> " + Arrays.toString(grown));

        int[] source = {10, 20, 30, 40, 50};
        int[] middle = Arrays.copyOfRange(source, 1, 4); // indices 1..3 (end exclusive)
        System.out.println("intermediate: copyOfRange [1,4) -> " + Arrays.toString(middle));
    }

    // Advanced: binarySearch requires sorted input; equals compares content, not reference.
    static void advancedLevel() {
        int[] sorted = {2, 4, 6, 8, 10};
        int index = Arrays.binarySearch(sorted, 8); // O(log n)
        System.out.println("advanced: binarySearch(8) -> index " + index);

        int[] a = {1, 2, 3};
        int[] b = {1, 2, 3};
        System.out.println("advanced: a == b (reference) -> " + (a == b));           // false
        System.out.println("advanced: Arrays.equals(a, b) (content) -> " + Arrays.equals(a, b)); // true
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `ArraysUtilityClass.java`, then run `java ArraysUtilityClass.java`.

## 6. Walkthrough

1. `basicLevel()` sorts `{5,2,8,1,9}` in place, producing `{1,2,5,8,9}` — `Arrays.sort` mutates the original array, it does not return a new one. `Arrays.fill` then overwrites every slot of a fresh 5-element array with `-1` in one O(n) pass.
2. `intermediateLevel()`'s `Arrays.copyOf(original, 5)` allocates a brand-new 5-element array, copies the original 3 values in, and default-fills the remaining 2 slots with `0` — the original array is untouched.
3. `Arrays.copyOfRange(source, 1, 4)` extracts indices 1, 2, and 3 (the end index is exclusive) into a new array `{20, 30, 40}`.
4. `advancedLevel()`'s `Arrays.binarySearch(sorted, 8)` returns index `3`, using the same halving strategy as a hand-written binary search — it only works correctly because `sorted` really is sorted.
5. Comparing `a == b` and `Arrays.equals(a, b)` on two separately-created but equal-content arrays shows the key distinction: `==` is `false` (different objects), while `Arrays.equals` is `true` (same contents) — exactly parallel to the `.equals()` vs `==` distinction for any object.

## 7. Gotchas & takeaways

> Gotcha: `Arrays.binarySearch` on an unsorted array does not throw an exception or warn you — it silently returns an unspecified, often wrong, index. Always confirm the array is sorted (or `Arrays.sort` it first) before calling `binarySearch`.

- `Arrays.sort` (O(n log n)) mutates in place; `Arrays.copyOf`/`copyOfRange` (O(n)) allocate new arrays; `Arrays.fill` (O(n)) overwrites every slot with one value.
- `Arrays.binarySearch` is O(log n) but requires sorted input — it has no way to detect or warn about unsorted data.
- Use `Arrays.equals`/`Arrays.deepEquals` for content comparison; `==` on arrays only ever compares references.
- Related concepts: [Binary search on a sorted array](0025-binary-search-on-a-sorted-array.md), [System.arraycopy & array copying](0029-system-arraycopy-array-copying.md).
