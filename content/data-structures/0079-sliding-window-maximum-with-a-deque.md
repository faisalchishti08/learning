---
card: data-structures
gi: 79
slug: sliding-window-maximum-with-a-deque
title: Sliding-window maximum with a deque
---

## 1. What it is

**Sliding-window maximum** is a named problem: given an array and a window size `k`, return the maximum value inside every window of size `k` as it slides across the array from left to right, one step at a time. For `nums = [1,3,-1,-3,5,3,6,7]` and `k = 3`, the answer is `[3,3,5,5,6,7]` — one maximum per window position.

## 2. Why & when

This is the concrete problem that the monotonic-queue technique exists to solve efficiently, and it is one of the most frequently asked interview questions involving a deque. It tests whether you recognize that repeatedly scanning each window is wasteful, and that a deque can track "the current candidates for maximum" incrementally as the window slides.

## 3. Core concept

**Level 1 — Brute force.** For each of the `n - k + 1` window positions, scan all `k` elements inside it and find the maximum directly. This is correct but O(n · k) — for `n = 100,000` and `k = 1,000`, that is up to 100 million comparisons.

**KEY INSIGHT.** Most of that brute-force work is wasted: once a new, bigger element enters the window, every smaller element to its left inside the window can *never* be the maximum again, for as long as the bigger element stays in the window. There is no need to re-compare them — they can be discarded permanently, the moment the bigger element arrives.

**Level 2 — Optimal: a deque of indices, decreasing values.** Maintain a deque holding indices whose values are strictly decreasing from front to back. As the window advances by one position: (1) discard the front index if it has slid outside the window; (2) discard back indices whose values are smaller than the new element (they are permanently dominated); (3) push the new index; (4) the front index is always the current window's maximum.

**Level 3 — Hardened.** Handle `k == 1` (every element is its own window, answer equals the input array), `k == n` (a single window covering the whole array), and confirm the deque never grows unboundedly, since each index is pushed once and popped at most once.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sliding a window of size three across the array 1, 3, negative one, negative three, 5, showing the window boundary moving right and the deque of indices adjusting at both ends">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">array: [1, 3, -1, -3, 5], k=3</text>
    <rect x="20" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="40" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">1</text>
    <rect x="60" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="80" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <rect x="100" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="120" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">-1</text>
    <rect x="140" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="160" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">-3</text>
    <rect x="180" y="30" width="40" height="26" fill="#0d1117" stroke="#f0883e"/><text x="200" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>
    <rect x="58" y="26" width="124" height="34" fill="none" stroke="#79c0ff" stroke-dasharray="3,3"/>
    <text x="120" y="80" fill="#79c0ff" text-anchor="middle" font-size="9">window [3,-1,-3] -&gt; deque holds index of 3 -&gt; max = 3</text>
    <text x="120" y="120" fill="#f0883e" text-anchor="middle" font-size="9">window slides to [-1,-3,5]: 5 dominates everything -&gt; deque = [index of 5] -&gt; max = 5</text>
  </g>
</svg>

As the window slides right, the deque drops indices that fell behind, and drops values dominated by a newer, bigger value — only real candidates survive.

## 5. Runnable example

```java
// SlidingWindowMaximum.java
import java.util.ArrayDeque;
import java.util.Deque;

public class SlidingWindowMaximum {

    // Level 1: brute force, O(n*k).
    static int[] maxSlidingWindowBruteForce(int[] nums, int k) {
        int[] result = new int[nums.length - k + 1];
        for (int i = 0; i <= nums.length - k; i++) {
            int max = Integer.MIN_VALUE;
            for (int j = i; j < i + k; j++) max = Math.max(max, nums[j]); // rescans the whole window every time
            result[i] = max;
        }
        return result;
    }

    static void basicLevel() {
        int[] nums = {1, 3, -1, -3, 5, 3, 6, 7};
        System.out.println("basic: brute force -> " + java.util.Arrays.toString(maxSlidingWindowBruteForce(nums, 3)));
    }

    // Level 2: optimal, O(n) -- deque of indices, decreasing values.
    static int[] maxSlidingWindow(int[] nums, int k) {
        int n = nums.length;
        int[] result = new int[n - k + 1];
        Deque<Integer> deque = new ArrayDeque<>();

        for (int i = 0; i < n; i++) {
            if (!deque.isEmpty() && deque.peekFirst() <= i - k) deque.pollFirst(); // drop stale front
            while (!deque.isEmpty() && nums[deque.peekLast()] < nums[i]) deque.pollLast(); // drop dominated back values
            deque.offerLast(i);
            if (i >= k - 1) result[i - k + 1] = nums[deque.peekFirst()];
        }
        return result;
    }

    static void intermediateLevel() {
        int[] nums = {1, 3, -1, -3, 5, 3, 6, 7};
        System.out.println("intermediate: optimal -> " + java.util.Arrays.toString(maxSlidingWindow(nums, 3)));
        System.out.println("intermediate: matches brute force -> "
            + java.util.Arrays.equals(maxSlidingWindow(nums, 3), maxSlidingWindowBruteForce(nums, 3)));
    }

    // Level 3: hardened -- k=1 and k=n edge cases.
    static void advancedLevel() {
        int[] nums = {5, 2, 8, 1};
        System.out.println("advanced: k=1 (every element is its own window) -> " + java.util.Arrays.toString(maxSlidingWindow(nums, 1)));
        System.out.println("advanced: k=n (single window over the whole array) -> " + java.util.Arrays.toString(maxSlidingWindow(nums, nums.length)));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `SlidingWindowMaximum.java`, then run `java SlidingWindowMaximum.java`.

## 6. Walkthrough

Trace `maxSlidingWindow([1, 3, -1, -3, 5], 3)` (the first 5 elements only, for brevity):

| i | nums[i] | front-evict | back-evicts | deque after | result recorded |
|---|---|---|---|---|---|
| 0 | 1 | no | none | `[0]` | — |
| 1 | 3 | no | pop 0 | `[1]` | — |
| 2 | -1 | no | none | `[1,2]` | i=2: `nums[1]=3` |
| 3 | -3 | no | none | `[1,2,3]` | i=3: `nums[1]=3` |
| 4 | 5 | idx 1<=1, evict | pop 2, pop 3 | `[4]` | i=4: `nums[4]=5` |

Result: `[3, 3, 5, ...]`, matching the brute-force answer for the same windows. Total work across the whole array is O(n), since every index is pushed exactly once and popped at most once — not O(n · k) like the brute-force scan.

## 7. Gotchas & takeaways

> Gotcha: the result array has length `n - k + 1`, not `n` — a common off-by-one bug is sizing the result array wrong, or writing to `result[i]` instead of `result[i - k + 1]` once the window is complete (which only starts at `i = k - 1`).

- The brute-force approach rescans each window fully, at O(n · k); the deque approach discards dominated values permanently, at O(n) total.
- Store indices (not values) in the deque, so out-of-window detection is possible via index comparison.
- The front of the deque always holds the current window's maximum, once both trimming rules are applied every step.
- Related concepts: [Monotonic queue technique](0076-monotonic-queue-technique.md), [Double-ended queue (deque)](0073-double-ended-queue-deque.md).
