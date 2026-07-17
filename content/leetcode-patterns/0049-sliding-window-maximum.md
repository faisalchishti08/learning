---
card: leetcode-patterns
gi: 49
slug: sliding-window-maximum
title: Sliding Window Maximum
---

## 1. What it is

Given an array `nums` and an integer `k`, a window of size `k` slides from the left of the array to the right, one position at a time. Return an array of the maximum value in the window at each position. Example: `nums = [1,3,-1,-3,5,3,6,7]`, `k = 3` → answer `[3,3,5,5,6,7]`.

## 2. Why & when

Unlike a running sum, a window's *maximum* cannot be updated in O(1) when an element leaves the window — the departing element might have been the maximum, forcing a rescan. A **monotonic deque** (double-ended queue) solves this: it keeps the window's candidates for "could still be the max" in decreasing order, so the current maximum is always available at the front in O(1).

## 3. Core concept

**Key idea:** if a new element entering the window is greater than or equal to elements already waiting in the deque, those smaller waiting elements can never become the maximum again (the new, larger element will outlast them in the window) — discard them immediately. The deque holds indices, always in decreasing order of their values, front to back.

**Steps:**
1. Create an empty deque `dq` storing indices.
2. For each index `i` from 0 to `length - 1`:
   - While `dq` is not empty and `nums[dq.peekLast()] <= nums[i]`, remove from the back (those indices can never be the max again).
   - Add `i` to the back of `dq`.
   - If `dq.peekFirst()` is outside the current window (i.e., `<= i - k`), remove it from the front.
   - Once `i >= k - 1` (the window is fully formed), record `nums[dq.peekFirst()]` as the max for this window position.
3. Return the recorded maximums.

**Why it is correct:** the deque maintains the invariant that its values are strictly decreasing front to back, and that every index still in the deque could still be the maximum for some future window (nothing larger has appeared after it, and it has not yet expired). The front is always the largest surviving candidate, and expired indices are dropped as the window slides past them — every index enters and leaves the deque at most once, giving O(n) total work.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sliding window maximum monotonic deque">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">nums = [1, 3, -1, -3, 5, 3, 6, 7], k = 3</text>
    <text x="20" y="55" fill="#8b949e">i=0,1,2: deque holds indices with decreasing values -&gt; after 1,3,-1: deque=[1(val3),2(val-1)]</text>
    <text x="20" y="80" fill="#79c0ff">front of deque = index 1 (val 3) -&gt; window[0,2] max = 3</text>
    <text x="20" y="105" fill="#8b949e">i=4 (val 5): pop back while smaller -&gt; pops -1, pops 3 -&gt; deque=[4(val5)]</text>
    <text x="20" y="130" fill="#f0883e">new max instantly available at front: 5</text>
  </g>
</svg>

The deque discards smaller elements from the back as bigger ones arrive, and expired elements from the front as the window slides — the current max is always at the front.

## 5. Runnable example

```java
// SlidingWindowMaximum.java
import java.util.ArrayDeque;
import java.util.Deque;

public class SlidingWindowMaximum {

    // Level 1 -- Brute force: scan the whole window for its max at every
    // position. O(n * k) time, O(1) space.
    static int[] bruteForce(int[] nums, int k) {
        int n = nums.length;
        int[] result = new int[n - k + 1];
        for (int i = 0; i + k <= n; i++) {
            int max = Integer.MIN_VALUE;
            for (int j = i; j < i + k; j++) max = Math.max(max, nums[j]);
            result[i] = max;
        }
        return result;
    }

    // KEY INSIGHT: a monotonic deque of indices, kept in decreasing order
    // of value, always has the current window's maximum at its front,
    // updated in amortized O(1) per element.

    // Level 2 -- Optimal: monotonic deque. O(n) time, O(k) space.
    public static int[] maxSlidingWindow(int[] nums, int k) {
        int n = nums.length;
        int[] result = new int[n - k + 1];
        Deque<Integer> dq = new ArrayDeque<>(); // stores indices

        for (int i = 0; i < n; i++) {
            while (!dq.isEmpty() && nums[dq.peekLast()] <= nums[i]) {
                dq.pollLast();
            }
            dq.offerLast(i);

            if (dq.peekFirst() <= i - k) {
                dq.pollFirst();
            }

            if (i >= k - 1) {
                result[i - k + 1] = nums[dq.peekFirst()];
            }
        }
        return result;
    }

    // Level 3 -- Hardened: k == 1 returns nums unchanged (every "window"
    // is a single element), since the deque never removes anything from
    // the back in that case.
    static int[] hardened(int[] nums, int k) {
        if (nums == null || k <= 0 || k > nums.length) {
            throw new IllegalArgumentException("invalid k for this array");
        }
        return maxSlidingWindow(nums, k);
    }

    public static void main(String[] args) {
        int[] nums = {1, 3, -1, -3, 5, 3, 6, 7};
        System.out.println("brute force: " + java.util.Arrays.toString(bruteForce(nums, 3)));
        System.out.println("optimal:     " + java.util.Arrays.toString(maxSlidingWindow(nums, 3)));
        System.out.println("k == 1:      " + java.util.Arrays.toString(hardened(new int[] {4, 5}, 1)));
    }
}
```

How to run: save as `SlidingWindowMaximum.java`, then run `java SlidingWindowMaximum.java`.

## 6. Walkthrough

Dry run of `maxSlidingWindow({1, 3, -1, -3, 5, 3, 6, 7}, k = 3)`, focused on the deque's contents (shown as index:value pairs):

| i | nums[i] | pop from back | deque after push | expire front? | window max |
|---|---|---|---|---|---|
| 0 | 1 | none | [0:1] | no | — |
| 1 | 3 | pop 0:1 (1<=3) | [1:3] | no | — |
| 2 | -1 | none | [1:3, 2:-1] | no | 3 |
| 3 | -3 | none | [1:3, 2:-1, 3:-3] | no | 3 |
| 4 | 5 | pop 3:-3, pop 2:-1, pop 1:3 (all <=5) | [4:5] | no | 5 |
| 5 | 3 | none | [4:5, 5:3] | no | 5 |
| 6 | 6 | pop 5:3, pop 4:5 (both <=6) | [6:6] | no | 6 |
| 7 | 7 | pop 6:6 (<=7) | [7:7] | no | 7 |

Final result: `[3, 3, 5, 5, 6, 7]`. Time complexity: O(n), each index is pushed once and popped at most once. Space complexity: O(k), the deque never holds more than `k` indices.

## 7. Gotchas & takeaways

> Gotcha: comparing with `<` instead of `<=` when popping from the back keeps duplicate values in the deque unnecessarily — using `<=` correctly discards an old duplicate in favor of the newer one at the same value, since the newer one will outlast it in the window.

- The monotonic deque is a distinct tool from the "shrink with a while loop" sliding-window template used elsewhere in this section — it is needed specifically when the window's tracked statistic (here, the max) cannot be updated incrementally in O(1) using only addition and subtraction.
- Related problems: Maximum Average Subarray I (a fixed window where the sum update IS O(1), so no deque is needed), Shortest Subarray with Sum at Least K (uses a monotonic deque over prefix sums), Longest Continuous Subarray With Absolute Diff Less Than or Equal to Limit (uses two monotonic deques, one for max and one for min).
