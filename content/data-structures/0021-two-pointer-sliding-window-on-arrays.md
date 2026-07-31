---
card: data-structures
gi: 21
slug: two-pointer-sliding-window-on-arrays
title: Two-pointer & sliding-window on arrays
---

## 1. What it is

**Two-pointer** is a technique where you walk an array with two index variables at once instead of one, moving them based on some condition — often starting at opposite ends and moving inward. **Sliding window** is a related technique where you track a contiguous range `[left, right]` that "slides" across the array, growing or shrinking one end at a time to maintain some property (like a running sum or a set of unique characters).

## 2. Why & when

Both techniques replace a naive nested loop (checking every pair or every sub-range, O(n²)) with a single pass, O(n). Use two-pointer when the array is sorted and you are looking for a pair or comparing from both ends (e.g., "does a pair sum to a target?"). Use sliding window when you need the best contiguous sub-array or sub-string satisfying a condition (e.g., "longest sub-array with sum ≤ k").

## 3. Core concept

**Why two-pointer avoids re-scanning.** On a sorted array, if `arr[left] + arr[right]` is too small, increasing `left` is the only way to grow the sum — decreasing `right` could only make it smaller. This lets you rule out a whole set of pairs with one comparison, instead of checking every pair individually.

**Why sliding window avoids re-summing.** A naive "sum of every sub-array" approach recomputes each sub-array's sum from scratch — O(n²) total. A sliding window instead updates the sum incrementally: when `right` moves forward, add `arr[right]`; when `left` moves forward, subtract the old `arr[left]`. Each element is added and removed from the running total at most once — O(n) total.

**The invariant each technique maintains.** Two-pointer maintains "everything between `left` and `right` is still a candidate region worth searching." Sliding window maintains "the window `[left, right]` currently satisfies (or is being adjusted to satisfy) the target condition" — shrinking from the left when the condition breaks, growing from the right to explore further.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two pointers starting at opposite ends and moving inward, versus a sliding window of variable width moving across the array">
  <g font-family="sans-serif" font-size="12">
    <text x="320" y="20" fill="#8b949e" text-anchor="middle">two-pointer: left and right converge</text>
    <rect x="30" y="35" width="50" height="30" fill="#161b22" stroke="#3fb950"/><text x="55" y="55" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <rect x="80" y="35" width="50" height="30" fill="#161b22" stroke="#8b949e"/><text x="105" y="55" fill="#e6edf3" text-anchor="middle" font-size="10">5</text>
    <rect x="130" y="35" width="50" height="30" fill="#161b22" stroke="#8b949e"/><text x="155" y="55" fill="#e6edf3" text-anchor="middle" font-size="10">7</text>
    <rect x="180" y="35" width="50" height="30" fill="#161b22" stroke="#3fb950"/><text x="205" y="55" fill="#e6edf3" text-anchor="middle" font-size="10">11</text>
    <text x="55" y="85" fill="#79c0ff" text-anchor="middle" font-size="10">left</text>
    <text x="205" y="85" fill="#79c0ff" text-anchor="middle" font-size="10">right</text>

    <text x="480" y="20" fill="#8b949e" text-anchor="middle">sliding window: [left, right] grows/shrinks</text>
    <rect x="380" y="35" width="35" height="30" fill="#161b22" stroke="#8b949e"/><text x="397" y="55" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <rect x="415" y="35" width="35" height="30" fill="#0d1117" stroke="#3fb950"/><text x="432" y="55" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <rect x="450" y="35" width="35" height="30" fill="#0d1117" stroke="#3fb950"/><text x="467" y="55" fill="#e6edf3" text-anchor="middle" font-size="10">3</text>
    <rect x="485" y="35" width="35" height="30" fill="#161b22" stroke="#8b949e"/><text x="502" y="55" fill="#e6edf3" text-anchor="middle" font-size="10">4</text>
    <text x="432" y="85" fill="#79c0ff" text-anchor="middle" font-size="10">window [1,2] sum tracked incrementally</text>
    <text x="320" y="150" fill="#79c0ff" text-anchor="middle">both turn an O(n^2) scan into a single O(n) pass</text>
  </g>
</svg>

Two-pointer narrows a search from both ends. Sliding window keeps a running total for a moving range, updating it incrementally instead of recomputing.

## 5. Runnable example

```java
// TwoPointerSlidingWindow.java
public class TwoPointerSlidingWindow {

    // Basic: two-pointer on a sorted array -- find a pair that sums to target.
    static int[] twoSumSorted(int[] sorted, int target) {
        int left = 0, right = sorted.length - 1;
        while (left < right) {
            int sum = sorted[left] + sorted[right];
            if (sum == target) return new int[]{left, right};
            if (sum < target) left++;  // sum too small: only increasing left can help
            else right--;              // sum too large: only decreasing right can help
        }
        return new int[]{-1, -1};
    }

    static void basicLevel() {
        int[] sorted = {2, 5, 7, 11, 15};
        int[] result = twoSumSorted(sorted, 18); // 7 + 11
        System.out.println("basic: pair indices -> [" + result[0] + ", " + result[1] + "]");
    }

    // Intermediate: fixed-size sliding window -- max sum of any window of size k.
    static int maxSumFixedWindow(int[] arr, int k) {
        int windowSum = 0;
        for (int i = 0; i < k; i++) windowSum += arr[i]; // build the first window
        int best = windowSum;
        for (int right = k; right < arr.length; right++) {
            windowSum += arr[right] - arr[right - k]; // add new right, drop the element leaving the window
            best = Math.max(best, windowSum);
        }
        return best;
    }

    static void intermediateLevel() {
        int[] arr = {2, 1, 5, 1, 3, 2};
        int best = maxSumFixedWindow(arr, 3);
        System.out.println("intermediate: max sum of any window of size 3 -> " + best);
    }

    // Advanced: variable-size sliding window -- shortest sub-array with sum >= target.
    static int shortestSubarrayAtLeast(int[] arr, int target) {
        int left = 0, sum = 0, best = Integer.MAX_VALUE;
        for (int right = 0; right < arr.length; right++) {
            sum += arr[right]; // grow the window
            while (sum >= target) {
                best = Math.min(best, right - left + 1); // record and try to shrink
                sum -= arr[left];
                left++;
            }
        }
        return best == Integer.MAX_VALUE ? 0 : best;
    }

    static void advancedLevel() {
        int[] arr = {2, 3, 1, 2, 4, 3};
        int result = shortestSubarrayAtLeast(arr, 7);
        System.out.println("advanced: shortest sub-array with sum >= 7 -> length " + result);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `TwoPointerSlidingWindow.java`, then run `java TwoPointerSlidingWindow.java`.

## 6. Walkthrough

1. `basicLevel()` starts `left=0` (value 2) and `right=4` (value 15) on `{2,5,7,11,15}`, target 18. `2+15=17`, too small, so `left++`. `5+15=20`, too large, so `right--`. `5+11=16`, too small, `left++`. `7+11=18` matches — return indices `[2,3]`.
2. `intermediateLevel()` builds the first window `{2,1,5}` (sum 8), then slides right: at `right=3` it adds `arr[3]=1` and drops `arr[0]=2` (sum 7); at `right=4` adds `3`, drops `1` (sum 9, new best); at `right=5` adds `2`, drops `5` (sum 6). Best stays 9.
3. `advancedLevel()` grows the window by advancing `right` and adding each value to `sum`. Once `sum >= 7`, it records the window length and shrinks from the left (subtracting `arr[left]`, advancing `left`) as long as the condition still holds, always tracking the shortest qualifying window seen.
4. Each element enters and leaves the window's `sum` at most once across the whole scan, which is why both sliding-window functions run in O(n) despite exploring many candidate sub-arrays.

## 7. Gotchas & takeaways

> Gotcha: two-pointer's "move the pointer that can't help" logic (in `twoSumSorted`) only works because the array is **sorted** — on an unsorted array, increasing `left` does not reliably shrink the search space, and the technique gives wrong answers. Sort first, or use a different approach (like a hash set) for unsorted input.

- Two-pointer replaces an O(n²) pair search with O(n) by eliminating a whole set of candidates per comparison — but requires sorted input to reason correctly about which pointer to move.
- Sliding window replaces O(n²) sub-array scanning with O(n) by updating a running value incrementally instead of recomputing it.
- Fixed-size windows only add/drop one element per step; variable-size windows grow and shrink based on a condition, using a `while` loop to shrink.
- Related concepts: [Prefix-sum & difference arrays](0022-prefix-sum-difference-arrays.md), [Binary search on a sorted array](0025-binary-search-on-a-sorted-array.md).
