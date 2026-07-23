---
card: leetcode-patterns
gi: 227
slug: modified-binary-search-signal-sorted-or-rotated-input-or-mon
title: Modified Binary Search — signal: sorted (or rotated) input, or monotonic answer space
---

## 1. What it is

Modified Binary Search is the family of problems solved by repeatedly cutting a search space in half, the same core idea as classic binary search, but applied to inputs that are not a plain sorted array — a rotated sorted array, an implicit "yes/no" function, or a range of possible answers instead of array indices.

## 2. Why & when

Reach for this pattern whenever a brute-force scan would be O(n), but the data has some ordering property that lets you discard half the remaining possibilities after one check. This is much faster than scanning, and works even when the array is not literally sorted, as long as SOME monotonic (always increasing, or always one-directional) property still holds.

Learn to recognize these signals in a problem statement:

- **"Find a target in a sorted array"** — the direct case; compare the middle element to the target.
- **"Sorted array, but rotated at an unknown pivot"** — one half of any split is still sorted; use that half to decide which way to go.
- **"Find the smallest/largest value where some condition first becomes true/false"** — a monotonic predicate over a range of possible answers (binary search ON THE ANSWER, not on an array index).
- **"Find the square root," "the first bad version," "how many coins can you afford"** — a numeric range where increasing the guess makes the condition flip exactly once.

The alternative — a plain linear scan — is O(n) and always correct, but wasteful whenever a monotonic property exists to exploit. If the input is sorted, rotated-but-sorted, or the answer space grows/shrinks in one direction only, binary search cuts the work to O(log n).

## 3. Core concept

Every variant keeps three pointers: `lo`, `hi` (the current search boundaries) and `mid` (the midpoint being checked). Each iteration checks `mid` against a condition, then discards HALF the remaining range based on that check — either the array indices, or a range of candidate answer values.

Two shapes cover almost every variant:

**Binary search on index.** The array (or a rotated version of it) is sorted. Compare `nums[mid]` to the target. If they match, done. Otherwise, figure out which half is still properly ordered, check if the target could be in that half, and move `lo` or `hi` accordingly.

**Binary search on the answer.** There is no array — instead, a function `check(x)` returns true or false, and that function is monotonic (once it becomes true, it stays true, or vice versa). Binary search over the range of possible `x` values to find the boundary where `check(x)` flips.

The key insight: in both shapes, every iteration must shrink the range by roughly half, or the algorithm is not actually binary search — the O(log n) guarantee depends on real, provable halving at every step.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Binary search on array index versus binary search on a range of candidate answers">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">On index: array [2,5,8,12,16,23,38,56,72,91]</text>
    <rect x="20" y="35" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="35" y="52" fill="#8b949e" text-anchor="middle" font-size="10">lo</text>
    <rect x="140" y="35" width="30" height="24" fill="#3fb950"/><text x="155" y="52" fill="#0d1117" text-anchor="middle" font-size="10">mid</text>
    <rect x="260" y="35" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="275" y="52" fill="#8b949e" text-anchor="middle" font-size="10">hi</text>
    <text x="20" y="80" fill="#8b949e">target &lt; nums[mid] -&gt; discard right half, hi = mid-1</text>

    <text x="20" y="120" fill="#e6edf3" font-weight="bold">On answer: check(x) is false...false, true...true</text>
    <rect x="20" y="135" width="24" height="24" fill="#161b22" stroke="#f85149"/><rect x="46" y="135" width="24" height="24" fill="#161b22" stroke="#f85149"/>
    <rect x="72" y="135" width="24" height="24" fill="#3fb950"/><rect x="98" y="135" width="24" height="24" fill="#3fb950"/><rect x="124" y="135" width="24" height="24" fill="#3fb950"/>
    <text x="20" y="180" fill="#8b949e">find the first x where check(x) flips from false to true</text>
  </g>
</svg>

Both shapes throw away half the remaining candidates on every step, based on one comparison at the midpoint.

## 5. Runnable example

```java
// ModifiedBinarySearchSignal.java
public class ModifiedBinarySearchSignal {

    // Signal check 1: plain sorted array -> binary search on index.
    static boolean isSortedIndexCase(int[] nums) {
        for (int i = 1; i < nums.length; i++) {
            if (nums[i] < nums[i - 1]) return false;
        }
        return true;
    }

    // Signal check 2: a monotonic predicate over a numeric range ->
    // binary search on the answer. Example predicate: "is x*x >= n?"
    static boolean check(int x, int n) {
        return (long) x * x >= n;
    }

    public static void main(String[] args) {
        int[] sorted = {2, 5, 8, 12, 16};
        System.out.println("sorted array -> search on index: " + isSortedIndexCase(sorted));

        int n = 30;
        System.out.println("smallest x where x*x >= " + n + ":");
        for (int x = 0; x <= 6; x++) {
            System.out.println("  check(" + x + ") = " + check(x, n));
        }
        // false until x=6 (36 >= 30), confirming a monotonic flip point
    }
}
```

**How to run:** `java ModifiedBinarySearchSignal.java`

## 6. Walkthrough

1. You read a problem statement. If it names a sorted array directly, or a "rotated sorted array," that is the search-on-index signal.
2. If instead it describes a condition that becomes true at some unknown point and stays true (or false) afterward — "smallest x such that...", "first bad version", "can you afford k coins with x rows" — that is the search-on-answer signal.
3. Running the checker above confirms `x*x >= 30` is false for `x = 0..5` and becomes true exactly at `x = 6`, a clean monotonic flip — exactly the shape binary search on the answer needs.
4. Once you know which shape applies, the template on the next page gives you the exact loop structure to write.

## 7. Gotchas & takeaways

> Gotcha: applying binary search to an array or a predicate that is NOT actually monotonic silently gives a wrong answer instead of an error — always confirm the sorted or monotonic property holds before reaching for this pattern.

- Search on index: the array (or a rotated version of it) is sorted; compare `nums[mid]` to the target directly.
- Search on the answer: no array at all; a `check(x)` function is monotonic across a range of candidate values `x`.
- Rotated arrays are still searchable in O(log n), because even after rotation, at least one half of any split remains properly sorted.
