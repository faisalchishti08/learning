---
card: data-structures
gi: 24
slug: kadane-s-maximum-subarray-technique
title: Kadane's maximum-subarray technique
---

## 1. What it is

**Kadane's algorithm** finds the contiguous sub-array with the largest sum, in a single O(n) pass over the array. At each position, it decides between two choices: extend the running sub-array by including the current element, or abandon everything before it and start fresh at the current element — whichever gives a larger sum right now.

## 2. Why & when

The naive approach checks every possible sub-array's sum — O(n²) or worse. Kadane's algorithm is the standard tool whenever a problem asks for the best contiguous run inside an array: maximum profit from one buy/sell, longest streak with best net score, or any "best contiguous window" problem where the window's sum, not its length, is the target.

## 3. Core concept

**The key decision at each step.** Let `currentSum` be the best sum of a sub-array ending exactly at the current index. At each new element `x`, `currentSum` becomes `max(x, currentSum + x)` — either `x` starts a brand-new sub-array, or it extends the previous best-ending-here sub-array.

**Why "restart if negative" is correct.** If `currentSum` before adding `x` is negative, adding it to `x` only drags the sum down — so `x` alone is always at least as good as extending. This is exactly what `max(x, currentSum + x)` captures: when `currentSum` is negative, `x` on its own wins.

**Tracking the global best separately.** `currentSum` only tracks the best sub-array *ending at* the current position, which can shrink and grow as the scan proceeds. A separate `bestSum` variable records the largest `currentSum` seen at any point, since the true maximum sub-array might have ended earlier in the scan, not at the very last index.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Scanning an array while tracking currentSum ending at each position and the running bestSum seen so far">
  <g font-family="sans-serif" font-size="11">
    <text x="330" y="16" fill="#8b949e" text-anchor="middle">arr: -2  1  -3  4  -1  2  1  -5  4</text>
    <rect x="30" y="30" width="50" height="26" fill="#161b22" stroke="#8b949e"/><text x="55" y="48" fill="#e6edf3" text-anchor="middle" font-size="10">-2</text>
    <rect x="80" y="30" width="50" height="26" fill="#161b22" stroke="#8b949e"/><text x="105" y="48" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <rect x="130" y="30" width="50" height="26" fill="#161b22" stroke="#8b949e"/><text x="155" y="48" fill="#e6edf3" text-anchor="middle" font-size="10">-3</text>
    <rect x="180" y="30" width="50" height="26" fill="#0d1117" stroke="#3fb950"/><text x="205" y="48" fill="#e6edf3" text-anchor="middle" font-size="10">4</text>
    <rect x="230" y="30" width="50" height="26" fill="#0d1117" stroke="#3fb950"/><text x="255" y="48" fill="#e6edf3" text-anchor="middle" font-size="10">-1</text>
    <rect x="280" y="30" width="50" height="26" fill="#0d1117" stroke="#3fb950"/><text x="305" y="48" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <rect x="330" y="30" width="50" height="26" fill="#0d1117" stroke="#3fb950"/><text x="355" y="48" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <rect x="380" y="30" width="50" height="26" fill="#161b22" stroke="#8b949e"/><text x="405" y="48" fill="#e6edf3" text-anchor="middle" font-size="10">-5</text>
    <rect x="430" y="30" width="50" height="26" fill="#161b22" stroke="#8b949e"/><text x="455" y="48" fill="#e6edf3" text-anchor="middle" font-size="10">4</text>
    <text x="280" y="80" fill="#79c0ff" text-anchor="middle">best sub-array: [4, -1, 2, 1] -&gt; sum = 6</text>
    <text x="280" y="105" fill="#8b949e" text-anchor="middle" font-size="10">currentSum resets to just "4" right after the -3, since -3 dragged the running sum negative</text>
  </g>
</svg>

The highlighted run `[4, -1, 2, 1]` is the best contiguous sub-array. Everything before it was abandoned once the running sum went negative.

## 5. Runnable example

```java
// KadaneMaximumSubarray.java
public class KadaneMaximumSubarray {

    // Basic: Kadane's algorithm, tracking just the maximum sum.
    static int maxSubarraySum(int[] arr) {
        int currentSum = arr[0];
        int bestSum = arr[0];
        for (int i = 1; i < arr.length; i++) {
            currentSum = Math.max(arr[i], currentSum + arr[i]); // extend or restart
            bestSum = Math.max(bestSum, currentSum);            // remember the best seen so far
        }
        return bestSum;
    }

    static void basicLevel() {
        int[] arr = {-2, 1, -3, 4, -1, 2, 1, -5, 4};
        System.out.println("basic: max sub-array sum -> " + maxSubarraySum(arr));
    }

    // Intermediate: extend Kadane's to also return the actual sub-array's start and end indices.
    static int[] maxSubarrayBounds(int[] arr) {
        int currentSum = arr[0], bestSum = arr[0];
        int tempStart = 0, bestStart = 0, bestEnd = 0;
        for (int i = 1; i < arr.length; i++) {
            if (arr[i] > currentSum + arr[i]) {
                currentSum = arr[i];
                tempStart = i; // restarting: this index becomes the new candidate start
            } else {
                currentSum = currentSum + arr[i]; // extending the existing run
            }
            if (currentSum > bestSum) {
                bestSum = currentSum;
                bestStart = tempStart;
                bestEnd = i;
            }
        }
        return new int[]{bestSum, bestStart, bestEnd};
    }

    static void intermediateLevel() {
        int[] arr = {-2, 1, -3, 4, -1, 2, 1, -5, 4};
        int[] result = maxSubarrayBounds(arr);
        System.out.println("intermediate: sum=" + result[0] + " start=" + result[1] + " end=" + result[2]);
    }

    // Advanced: an all-negative array -- must still pick the least-negative single element, not zero.
    static void advancedLevel() {
        int[] allNegative = {-8, -3, -6, -2, -5, -4};
        int result = maxSubarraySum(allNegative);
        System.out.println("advanced: all-negative array best sum -> " + result); // -2, the single best element
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `KadaneMaximumSubarray.java`, then run `java KadaneMaximumSubarray.java`.

## 6. Walkthrough

1. `basicLevel()` scans `{-2, 1, -3, 4, -1, 2, 1, -5, 4}`. `currentSum` starts at `-2`. At `1`: `max(1, -2+1=-1)=1`. At `-3`: `max(-3, 1-3=-2)=-2`. At `4`: `max(4, -2+4=2)=4` — the run restarts here since `4` alone beats extending the negative run.
2. Continuing: at `-1`, `max(-1, 4-1=3)=3`; at `2`, `max(2, 3+2=5)=5`; at `1`, `max(1, 5+1=6)=6` — `bestSum` updates to `6` here, the true answer.
3. `intermediateLevel()` tracks the same logic but also records `tempStart` whenever a restart happens, and snapshots `bestStart`/`bestEnd` whenever `bestSum` improves — this recovers the actual sub-array `[4, -1, 2, 1]` (indices 3 to 6), not just its sum.
4. `advancedLevel()` runs the same algorithm on an all-negative array. Since every restart candidate (`arr[i]` alone) is compared against `currentSum + arr[i]`, and both are negative, the algorithm still correctly converges on the single least-negative element (`-2`), never defaulting to `0` for "no elements".

## 7. Gotchas & takeaways

> Gotcha: initializing `bestSum = 0` instead of `bestSum = arr[0]` silently breaks the all-negative case — it would incorrectly report `0` (an empty sub-array) as the best sum, even though the problem requires a non-empty contiguous sub-array. Always initialize both `currentSum` and `bestSum` from `arr[0]`.

- Kadane's algorithm finds the maximum-sum contiguous sub-array in one O(n) pass, using O(1) extra space.
- At each step, choose `max(current element, running sum + current element)` — restart if the running sum would drag the total down.
- Track the best sum seen *across* the whole scan separately from the sum ending at the current position, since the optimal sub-array may not end at the last index.
- Related concepts: [Two-pointer & sliding-window on arrays](0021-two-pointer-sliding-window-on-arrays.md), [Prefix-sum & difference arrays](0022-prefix-sum-difference-arrays.md).
