---
card: data-structures
gi: 76
slug: monotonic-queue-technique
title: Monotonic queue technique
---

## 1. What it is

A **monotonic queue** is a deque kept in strictly increasing or decreasing order from front to back, by popping elements from the **back** before pushing a new one — the same pruning idea as a monotonic stack, but applied to a structure where you also need to evict expired elements from the **front**. It is the standard technique behind "sliding window maximum/minimum" problems.

## 2. Why & when

Use it whenever a problem asks for the maximum or minimum inside every window of a fixed size as the window slides across an array. The naive approach recomputes the max/min for every window position by scanning it, at O(n · k) for `n` positions and window size `k`. A monotonic queue answers each window in amortized O(1), for O(n) total.

## 3. Core concept

**Key idea in one sentence.** Keep a deque of *indices*, front-to-back in decreasing order of value (for a maximum-tracking queue); the front index is always the current window's maximum, and both ends get trimmed as the window slides.

**Two kinds of trimming, one at each end.**
- **Back trimming (like a monotonic stack):** before pushing the current index, pop indices off the back whose values are smaller than the current value — they can never be the maximum again while the current, bigger value is still in the window.
- **Front trimming (new, because the window has a fixed size):** before reading the window's maximum, pop the front index if it has fallen outside the window (its index is too far behind the current position).

**Why the front of the deque is always the window's maximum.** Back-trimming guarantees the deque's values are strictly decreasing front to back, so the front is always the largest *value* currently in the deque. Front-trimming guarantees every remaining index is still inside the window. Together, the front index is the largest value that is both still in the window and was never dominated by a later, bigger value.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sliding a window of size 3 across the array 1, 3, -1, -3, showing the deque of indices trimmed at the back for smaller values and at the front for out of window indices">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="18" fill="#8b949e">array: [1, 3, -1, -3, 5], window size 3</text>
    <text x="20" y="42" fill="#e6edf3">i=0 (1): push 0 -&gt; deque [0]</text>
    <text x="20" y="62" fill="#79c0ff">i=1 (3): 3&gt;1, pop 0 (back); push 1 -&gt; deque [1]</text>
    <text x="20" y="82" fill="#e6edf3">i=2 (-1): -1&lt;3, no pop; push 2 -&gt; deque [1, 2]; window [1,3,-1] complete, max = arr[front=1] = 3</text>
    <text x="20" y="102" fill="#e6edf3">i=3 (-3): -3&lt;-1, no pop; push 3 -&gt; deque [1, 2, 3]; window [3,-1,-3], max = arr[1] = 3</text>
    <text x="20" y="122" fill="#f0883e">i=4 (5): front idx 1 &lt;= i-3=1 -&gt; evict front; then 5 &gt; all -&gt; pop 2, pop 3; push 4 -&gt; deque [4]; max = 5</text>
    <text x="20" y="150" fill="#a5d6ff">window maxima: 3, 3, 5</text>
  </g>
</svg>

The front of the deque always holds the index of the current window's maximum, kept correct by trimming stale (out-of-window) indices from the front and dominated (smaller) values from the back.

## 5. Runnable example

```java
// MonotonicQueueTemplate.java
import java.util.ArrayDeque;
import java.util.Deque;

public class MonotonicQueueTemplate {

    // The reusable template: sliding window maximum, O(n) total.
    static int[] slidingWindowMaximum(int[] nums, int k) {
        int n = nums.length;
        int[] result = new int[n - k + 1];
        Deque<Integer> deque = new ArrayDeque<>(); // indices, values strictly decreasing front to back

        for (int i = 0; i < n; i++) {
            if (!deque.isEmpty() && deque.peekFirst() <= i - k) deque.pollFirst(); // evict out-of-window front

            while (!deque.isEmpty() && nums[deque.peekLast()] < nums[i]) deque.pollLast(); // evict dominated back values

            deque.offerLast(i);

            if (i >= k - 1) result[i - k + 1] = nums[deque.peekFirst()]; // window complete, record its maximum
        }
        return result;
    }

    static void basicLevel() {
        int[] nums = {1, 3, -1, -3, 5, 3, 6, 7};
        System.out.println("basic: slidingWindowMaximum(k=3) -> " + java.util.Arrays.toString(slidingWindowMaximum(nums, 3)));
    }

    // Intermediate: sliding window MINIMUM -- same template, comparison direction flipped.
    static int[] slidingWindowMinimum(int[] nums, int k) {
        int n = nums.length;
        int[] result = new int[n - k + 1];
        Deque<Integer> deque = new ArrayDeque<>(); // indices, values strictly increasing front to back

        for (int i = 0; i < n; i++) {
            if (!deque.isEmpty() && deque.peekFirst() <= i - k) deque.pollFirst();
            while (!deque.isEmpty() && nums[deque.peekLast()] > nums[i]) deque.pollLast();
            deque.offerLast(i);
            if (i >= k - 1) result[i - k + 1] = nums[deque.peekFirst()];
        }
        return result;
    }

    static void intermediateLevel() {
        int[] nums = {1, 3, -1, -3, 5, 3, 6, 7};
        System.out.println("intermediate: slidingWindowMinimum(k=3) -> " + java.util.Arrays.toString(slidingWindowMinimum(nums, 3)));
    }

    // Advanced: window size larger than the array, and k=1 (every element is its own window).
    static void advancedLevel() {
        int[] tiny = {4, 2};
        System.out.println("advanced: k=1 (every element is its own max) -> " + java.util.Arrays.toString(slidingWindowMaximum(tiny, 1)));

        int[] single = {7};
        System.out.println("advanced: single-element array, k=1 -> " + java.util.Arrays.toString(slidingWindowMaximum(single, 1)));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `MonotonicQueueTemplate.java`, then run `java MonotonicQueueTemplate.java`.

## 6. Walkthrough

Dry-run `slidingWindowMaximum([1, 3, -1, -3, 5], 3)`:

| i | nums[i] | front-evict? | back-evicts | deque after push | window max recorded |
|---|---|---|---|---|---|
| 0 | 1 | no | none | `[0]` | — (window not full) |
| 1 | 3 | no | pop 0 (1<3) | `[1]` | — |
| 2 | -1 | no | none | `[1,2]` | i=2: `nums[1]=3` |
| 3 | -3 | no | none | `[1,2,3]` | i=3: `nums[1]=3` |
| 4 | 5 | front idx 1 <= 4-3=1, evict | pop 2, pop 3 (both <5) | `[4]` | i=4: `nums[4]=5` |

Result: `[3, 3, 5]` — three windows: `[1,3,-1]` max `3`, `[3,-1,-3]` max `3`, `[-1,-3,5]` max `5`. Each index enters and leaves the deque at most once across the whole run, so the total cost is O(n).

## 7. Gotchas & takeaways

> Gotcha: the front-eviction check must use `deque.peekFirst() <= i - k`, not `< i - k` — an index is out of the window exactly when it is `k` or more positions behind the current one; using the wrong comparison keeps one stale index too many, or evicts one index too early.

- A monotonic queue trims the back like a monotonic stack (drop dominated values) and additionally trims the front (drop out-of-window indices) — two invariants instead of one.
- Store indices, not values, in the deque, so you can check whether an index has fallen outside the current window.
- Each index is pushed once and popped at most once, giving O(n) total for all windows combined.
- Related concepts: [Sliding-window maximum with a deque](0079-sliding-window-maximum-with-a-deque.md), [Monotonic stack technique](0068-monotonic-stack-technique.md).
