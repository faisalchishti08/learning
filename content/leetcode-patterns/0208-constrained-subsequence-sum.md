---
card: leetcode-patterns
gi: 208
slug: constrained-subsequence-sum
title: Constrained Subsequence Sum
---

## 1. What it is

Given an integer array `nums` and an integer `k`, find the maximum sum of a non-empty subsequence such that for every two consecutive chosen elements at indices `i < j`, `j - i <= k`. Example: `nums = [10,2,-10,5,20]`, `k = 2` → `37` (choosing `10, 2, 20`).

## 2. Why & when

This is dynamic programming where `dp[i]` (the best subsequence sum ending at index `i`) depends on `max(dp[i-k..i-1], 0) + nums[i]` — a SLIDING WINDOW MAXIMUM over the last `k` DP values. A max-heap holding `[dpValue, index]` pairs, with lazy deletion for indices that have slid out of the window, answers "what is the max dp value in the last k positions" without rescanning the window every time.

## 3. Core concept

**Key idea:** compute `dp[i]` left to right. To get the best PREVIOUS value within the last `k` positions quickly, keep a max-heap of `[dpValue, index]` pairs seen so far. Before using the heap's top, discard (lazily) any entries whose index is now more than `k` positions behind the current one — those are out of range and can never be used again.

**Steps:**
1. Initialize a max-heap ordered by `dpValue`, and a `dp` array (or track only the needed values with a rolling variable, if space matters).
2. For each index `i` from `0` to `n-1`: pop from the heap any entries whose index is `< i - k` (out of the allowed window), discarding them permanently.
3. Compute `dp[i] = nums[i] + max(0, heap top's dpValue if any)` — the `max(0, ...)` term means you can always start a fresh subsequence at `i` if extending a previous one would hurt.
4. Push `[dp[i], i]` onto the heap.
5. Track the maximum `dp[i]` seen across the whole array; return it after the loop.

**Why it is correct:** the heap always exposes the LARGEST dp value among indices still within the last `k` positions, since stale (too-old) entries are discarded before being trusted. The `max(0, ...)` term correctly allows a chosen element to either extend a previous good subsequence or start fresh, whichever yields a larger sum, since a subsequence of one negative-contributing element is never forced to be extended.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Max-heap of dp values within the last k indices, stale entries discarded as the window slides">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="60" width="200" height="40" fill="none" stroke="#30363d"/>
    <text x="30" y="85" fill="#e6edf3">window: indices [i-k, i-1]</text>
    <circle cx="280" cy="80" r="18" fill="#161b22" stroke="#f85149"/><text x="280" y="84" fill="#e6edf3" text-anchor="middle" font-size="9">stale</text>
    <text x="10" y="15" fill="#e6edf3">heap top with an index older than i-k is discarded before use, keeping only in-window candidates valid</text>
  </g>
</svg>

Before trusting the heap's top for the current `dp[i]` computation, any entry whose index has aged out of the last `k` positions is popped and discarded.

## 5. Runnable example

```java
// ConstrainedSubsequenceSum.java
import java.util.*;

public class ConstrainedSubsequenceSum {

    // Level 1 -- Brute force: for each index i, scan back up to k
    // positions to find the maximum dp value in that range directly.
    // Correct, but O(n*k) total -- rescanning the window from scratch
    // at every index instead of maintaining it incrementally.

    // KEY INSIGHT: a max-heap of [dpValue, index] pairs, with entries
    // outside the window lazily discarded, answers "max dp value in
    // the last k positions" in O(log n) instead of O(k) per index.

    // Level 2 -- Optimal: max-heap with lazy deletion of out-of-window
    // indices.
    static int constrainedSubsetSum(int[] nums, int k) {
        int n = nums.length;
        int[] dp = new int[n];
        PriorityQueue<int[]> heap = new PriorityQueue<>((a, b) -> b[0] - a[0]);
        int best = Integer.MIN_VALUE;

        for (int i = 0; i < n; i++) {
            while (!heap.isEmpty() && heap.peek()[1] < i - k) heap.poll();
            int prevBest = heap.isEmpty() ? 0 : Math.max(0, heap.peek()[0]);
            dp[i] = nums[i] + prevBest;
            heap.add(new int[]{dp[i], i});
            best = Math.max(best, dp[i]);
        }
        return best;
    }

    // Level 3 -- Hardened: `Math.max(0, heap.peek()[0])` correctly
    // handles the case where every reachable previous dp value is
    // negative, letting the current element start a fresh subsequence
    // instead of being forced to extend a losing one.

    public static void main(String[] args) {
        System.out.println(constrainedSubsetSum(new int[]{10,2,-10,5,20}, 2)); // 37
        System.out.println(constrainedSubsetSum(new int[]{-1,-2,-3}, 1)); // -1
        System.out.println(constrainedSubsetSum(new int[]{10,-2,-10,-5,20}, 2)); // 23
    }
}
```

**How to run:** `java ConstrainedSubsequenceSum.java`

## 6. Walkthrough

Trace `nums = [10,2,-10,5,20]`, `k = 2`:

| i | nums[i] | Heap top (valid) | prevBest | dp[i] | best |
|---|---|---|---|---|---|
| 0 | 10 | none | 0 | 10 | 10 |
| 1 | 2 | [10,0] | 10 | 12 | 12 |
| 2 | -10 | [12,1] (10,0 still in window too) | 12 | 2 | 12 |
| 3 | 5 | [12,1] (index0 now out: 0 < 3-2=1, discarded) | 12 | 17 | 17 |
| 4 | 20 | [17,3] (index1 now out: 1 < 4-2=2, discarded) | 17 | 37 | 37 |

Result is `37`, matching the expected output. Time complexity is O(n log n), since each index pushes once and is popped at most once across the whole run; space is O(n) for the heap and dp array.

## 7. Gotchas & takeaways

> Gotcha: checking the window bound as `heap.peek()[1] <= i - k` (using `<=` instead of `<`) off-by-one's the discard condition, incorrectly evicting an index that is still exactly `k` positions back and therefore still valid.

- This is a DP problem wearing a "sliding window maximum" hat — recognizing the recurrence `dp[i] = nums[i] + max(0, best of dp[i-k..i-1])` is the key step before reaching for the heap.
- The `dp` array itself is not strictly required if only the running maximum answer is needed — but keeping it makes reconstructing the actual subsequence possible if a follow-up asks for it.
- Related problems: Sliding Window Median (same lazy-deletion-from-heap technique, different statistic), Sliding Window Maximum (the same "max over a window" idea, solved with a monotonic deque instead of a heap).
