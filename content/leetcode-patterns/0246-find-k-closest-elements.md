---
card: leetcode-patterns
gi: 246
slug: find-k-closest-elements
title: Find K Closest Elements
---

## 1. What it is

Given a sorted array `arr`, an integer `k`, and a value `x`, return the `k` closest values to `x` in `arr`, sorted in ascending order. If two values are equally close, prefer the SMALLER one. Example: `arr = [1,2,3,4,5]`, `k = 4`, `x = 3` → `[1,2,3,4]`.

## 2. Why & when

The answer is always a contiguous WINDOW of `k` elements inside the sorted array (since the array is sorted, the closest values to `x` cluster together). Instead of computing every element's distance and sorting, binary search directly for the correct starting position of that window. Use this shape whenever a problem asks for the "closest k" items from a sorted collection.

## 3. Core concept

**Key idea:** search for the LEFT edge of the `k`-length window. There are `arr.length - k + 1` possible starting positions. For a candidate start `mid`, decide whether the window `[mid, mid + k - 1]` is better than the window `[mid + 1, mid + k]` by comparing which one drops the worse of the two boundary elements: if `x - arr[mid] > arr[mid + k] - x`, the element at `mid` is farther from `x` than the element at `mid + k`, so the window should shift right.

**Steps:**
1. Set `lo = 0`, `hi = arr.length - k` (the last valid starting index).
2. While `lo < hi`: compute `mid = lo + (hi - lo) / 2`.
3. Compare `x - arr[mid]` (distance from `x` to the window's current left edge) to `arr[mid + k] - x` (distance from `x` to the element just past the window's current right edge).
4. If `x - arr[mid] > arr[mid + k] - x`, the left edge is worse than the right candidate: set `lo = mid + 1` (shift the window right).
5. Otherwise, set `hi = mid` (keep the window where it is, or shift left).
6. When the loop ends, `lo` is the start of the best window; return `arr[lo, lo + k)`.

**Why it is correct:** as the candidate window slides right, whether "dropping the left edge for the next right element" helps or hurts is a monotonic decision — once shifting right stops helping, it never helps again, because the array is sorted and distances only grow monotonically away from `x` in each direction. This lets binary search converge directly on the optimal window start without checking every possible window.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Array 1 2 3 4 5, x=3, k=4, comparing window start 0 versus 1 by boundary distances">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">arr = [1,2,3,4,5], x=3, k=4</text>
    <rect x="10" y="30" width="30" height="24" fill="#3fb950"/><text x="25" y="47" fill="#0d1117" text-anchor="middle" font-size="9">1</text>
    <rect x="40" y="30" width="30" height="24" fill="#3fb950"/><text x="55" y="47" fill="#0d1117" text-anchor="middle" font-size="9">2</text>
    <rect x="70" y="30" width="30" height="24" fill="#3fb950"/><text x="85" y="47" fill="#0d1117" text-anchor="middle" font-size="9">3</text>
    <rect x="100" y="30" width="30" height="24" fill="#3fb950"/><text x="115" y="47" fill="#0d1117" text-anchor="middle" font-size="9">4</text>
    <rect x="130" y="30" width="30" height="24" fill="#161b22" stroke="#f85149"/><text x="145" y="47" text-anchor="middle" font-size="9">5</text>
    <text x="10" y="80">compare x-arr[0]=2 to arr[4]-x=2: tie -&gt; prefer smaller, keep window at 0</text>
    <text x="10" y="105">window [0,3] = [1,2,3,4] chosen over shifting to [1,4]</text>
  </g>
</svg>

Binary search directly finds the best starting index of a fixed-size window, without evaluating every possible window explicitly.

## 5. Runnable example

```java
// FindKClosestElements.java
import java.util.*;

public class FindKClosestElements {

    // Level 1 -- Brute force: compute the distance |arr[i] - x| for
    // every element, sort indices by (distance, value), take the
    // smallest k, then sort those k values ascending. Correct, but
    // O(n log n) -- ignores that the answer is always one contiguous
    // window in the already-sorted array.

    // KEY INSIGHT: the k closest values always form a CONTIGUOUS
    // window in the sorted array. Binary search directly for that
    // window's starting index by comparing boundary distances.

    // Level 2 -- Optimal: binary search for the window's left edge.
    static List<Integer> findClosestElements(int[] arr, int k, int x) {
        int lo = 0, hi = arr.length - k;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (x - arr[mid] > arr[mid + k] - x) lo = mid + 1;
            else hi = mid;
        }
        List<Integer> result = new ArrayList<>();
        for (int i = lo; i < lo + k; i++) result.add(arr[i]);
        return result;
    }

    // Level 3 -- Hardened: the comparison uses strict `>` (not `>=`),
    // so on an exact tie in distance, the window does NOT shift right,
    // correctly preferring the smaller value as the problem requires.

    public static void main(String[] args) {
        System.out.println(findClosestElements(new int[]{1,2,3,4,5}, 4, 3));
        // [1, 2, 3, 4]
        System.out.println(findClosestElements(new int[]{1,1,2,3,4,5}, 4, -1));
        // [1, 1, 2, 3]
    }
}
```

**How to run:** `java FindKClosestElements.java`

## 6. Walkthrough

Trace `findClosestElements(arr, 4, 3)` on `arr = [1,2,3,4,5]`, `lo=0, hi=1` (since `arr.length - k = 1`):

| lo | hi | mid | x-arr[mid] | arr[mid+k]-x | comparison | action |
|---|---|---|---|---|---|---|
| 0 | 1 | 0 | 3-1=2 | arr[4]-3=2 | 2 > 2? no | hi = 0 |
| 0 | 0 | — | — | — | loop ends | window starts at 0 |

The window `arr[0..3] = [1,2,3,4]` is returned, correctly preferring the smaller values on a tie. Time complexity is O(log(n − k) + k): the search is O(log(n−k)), and building the result list is O(k). Space is O(k) for the output.

## 7. Gotchas & takeaways

> Gotcha: using `>=` instead of `>` in the comparison `x - arr[mid] > arr[mid + k] - x` breaks the tie-breaking rule — on an exact distance tie, the problem requires keeping the SMALLER value, which means the window must NOT shift right, so the comparison must stay strict.

- The search range `hi = arr.length - k` is the key setup step: it restricts candidate windows to only those that are actually `k` elements long and fit inside the array.
- This is a "binary search on the answer" problem where the answer space is window-start positions, and the monotonic property is about which direction improves total closeness.
- Related problems: Search Insert Position (a simpler single-point closest-position search), Koko Eating Bananas (a different flavor of binary search on a derived, monotonic comparison).
