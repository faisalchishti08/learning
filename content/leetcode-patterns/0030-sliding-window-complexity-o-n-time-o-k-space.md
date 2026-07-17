---
card: leetcode-patterns
gi: 30
slug: sliding-window-complexity-o-n-time-o-k-space
title: Sliding Window — complexity: O(n) time, O(k) space
---

## 1. What it is

This page explains why sliding window runs in O(n) time despite its nested-loop appearance, and why its space cost is O(k) — proportional to the window's tracked state, not the input size — with a reference list of problems that use the pattern.

## 2. Why & when

The template's `for` loop with an inner `while` loop looks like it could be O(n²), the same shape as a naive nested loop. Being able to prove it is actually O(n) — and explain why — is often exactly what an interviewer is testing when they ask "what's the time complexity?" after you present a sliding-window solution.

## 3. Core concept

**Time — O(n).** The key is that `left` and `right` each only ever move forward, never backward, and each is bounded between `0` and `n - 1`. Across the *entire* scan (all iterations of the outer loop combined), `right` advances at most `n` times, and `left` advances at most `n` times in total across all the inner `while` loops combined — not per outer iteration. This is an **amortized** analysis: even though a single outer iteration's inner `while` might shrink the window by many steps, the total shrinking across the whole run cannot exceed `n`, because `left` cannot un-advance. Summing: at most `n` (for `right`) + `n` (for `left`, total) = `2n` pointer moves, which is O(n).

**Space — O(k).** The window itself needs no extra array — it is just two integer indices. The `state` tracker is what costs space, and its size depends on what you are tracking: a running sum is O(1); a `HashMap` of character counts is bounded by the alphabet size or the number of distinct elements allowed in a valid window, often written as O(k) where k is that bound (e.g., 26 for lowercase letters, or the "at most k distinct" limit itself).

**Contrast with brute force.** The brute-force approach — checking every contiguous subarray — costs O(n²) time just to enumerate the subarrays, before even evaluating each one (which can add another factor). Sliding window's amortized-linear pointer movement is what removes that redundant re-scanning.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Amortized analysis of sliding window pointer movement">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3">right pointer: moves 0,1,2,3,4,5 -- exactly n steps total</text>
    <line x1="20" y1="40" x2="620" y2="40" stroke="#79c0ff" stroke-width="3"/>
    <circle cx="20" cy="40" r="4" fill="#79c0ff"/><circle cx="120" cy="40" r="4" fill="#79c0ff"/>
    <circle cx="220" cy="40" r="4" fill="#79c0ff"/><circle cx="320" cy="40" r="4" fill="#79c0ff"/>
    <circle cx="420" cy="40" r="4" fill="#79c0ff"/><circle cx="520" cy="40" r="4" fill="#79c0ff"/>

    <text x="20" y="80" fill="#e6edf3">left pointer: shrinks by varying amounts each step, but never exceeds n total</text>
    <line x1="20" y1="100" x2="20" y2="100" stroke="#f0883e" stroke-width="3"/>
    <line x1="20" y1="100" x2="80" y2="100" stroke="#f0883e" stroke-width="3"/>
    <line x1="80" y1="120" x2="80" y2="120" stroke="#f0883e"/>
    <line x1="80" y1="140" x2="260" y2="140" stroke="#f0883e" stroke-width="3"/>
    <text x="20" y="170" fill="#8b949e">even though a single "while" can loop several times, the SUM across all</text>
    <text x="20" y="190" fill="#8b949e">outer iterations is capped at n, since left only ever moves forward</text>
  </g>
</svg>

`right` and `left` each traverse the array once over the full run — the inner loop's cost is paid for by future outer iterations skipping already-shrunk ground.

## 5. Runnable example

An instrumented longest-window scan that counts total pointer moves, to see the O(n) bound hold on real input.

```java
// SlidingWindowComplexity.java
public class SlidingWindowComplexity {

    static int[] longestWithCounts(int[] arr, int limit) {
        int left = 0, sum = 0, best = 0;
        int rightMoves = 0, leftMoves = 0;
        for (int right = 0; right < arr.length; right++) {
            sum += arr[right];
            rightMoves++;
            while (sum > limit) {
                sum -= arr[left];
                left++;
                leftMoves++;
            }
            best = Math.max(best, right - left + 1);
        }
        return new int[] { best, rightMoves, leftMoves };
    }

    public static void main(String[] args) {
        int[] arr = {2, 1, 5, 2, 8, 1, 5, 2, 3, 2};
        int n = arr.length;
        int[] result = longestWithCounts(arr, 7);
        System.out.println("n = " + n);
        System.out.println("best window length = " + result[0]);
        System.out.println("right moves = " + result[1] + " (== n)");
        System.out.println("left moves total = " + result[2] + " (<= n)");
    }
}
```

How to run: save as `SlidingWindowComplexity.java`, then run `java SlidingWindowComplexity.java`. `rightMoves` always equals `n`; `leftMoves` stays at or below `n`, no matter how the input is shaped.

## 6. Walkthrough

1. `arr` has 10 elements. The scan runs `right` from 0 to 9 — exactly 10 outer iterations, so `rightMoves = 10`.
2. Each outer iteration's inner `while` shrinks `left` by however many steps are needed to restore `sum <= limit`. Some iterations shrink by 0 steps, some by 2 or 3.
3. Summing `leftMoves` across every iteration never exceeds `10`, because `left` only ever increases and is capped at index 9 — it cannot be "shrunk" more times than there are elements to remove.
4. Printing both counts confirms `rightMoves = n` exactly and `leftMoves <= n`, giving a total of at most `2n` pointer operations — linear in `n`, regardless of how the shrinking happens to be distributed across iterations.

## 7. Gotchas & takeaways

> Gotcha: analyzing the inner `while` loop "locally" (as if it could run up to `n` times on *every* outer iteration) leads to an incorrect O(n²) estimate — the correct analysis is amortized, summing `left`'s total movement across the *whole* run, not per iteration.

- Time: O(n), amortized — `left` and `right` together make at most `2n` moves across the entire scan.
- Space: O(k), where k is the size of whatever state you track — O(1) for a sum, O(alphabet size) or O(distinct-element limit) for a counts map.
- Reference problems that use this pattern: Maximum Average Subarray I, Longest Substring Without Repeating Characters, Longest Repeating Character Replacement, Permutation in String, Find All Anagrams in a String, Max Consecutive Ones III, Fruit Into Baskets, Minimum Size Subarray Sum, Minimum Window Substring.
