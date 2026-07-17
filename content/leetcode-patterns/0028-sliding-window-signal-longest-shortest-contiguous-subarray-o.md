---
card: leetcode-patterns
gi: 28
slug: sliding-window-signal-longest-shortest-contiguous-subarray-o
title: Sliding Window — signal: longest/shortest contiguous subarray or substring
---

## 1. What it is

Sliding window is a technique for scanning a **contiguous** range of an array or string using two pointers that define the window's boundaries — `left` and `right` — where `right` expands the window and `left` shrinks it. Unlike opposite-ends two pointers, both boundaries here start at the same end and generally move in the same direction, growing and shrinking a single moving segment rather than converging from two sides.

## 2. Why & when

The brute-force approach to "find the longest/shortest contiguous subarray satisfying some condition" checks every possible subarray — O(n²) or worse, since there are O(n²) contiguous subarrays. Sliding window exploits the fact that as the window's right edge grows, you rarely need to re-examine everything from scratch; you can incrementally update a running statistic (a sum, a character count, a distinct-element count) and only shrink from the left when the condition breaks.

Learn to recognize these signals in a problem statement:

- **"Longest / shortest / maximum-length / minimum-length substring or subarray"** that satisfies some condition — the strongest signal.
- **"Contiguous"** or **"subarray"** (not "subsequence" — subsequences allow gaps and usually need dynamic programming instead).
- **A condition that can be checked incrementally**, such as "sum ≤ k," "at most k distinct characters," "no repeating characters," or "contains all characters of another string." If adding or removing one element lets you cheaply update whether the condition holds, sliding window applies.
- **"At most k" or "exactly k"** distinct/repeated elements — often solved with two sliding windows (`atMost(k) - atMost(k-1)`).

The alternative is checking every subarray directly (O(n²) or O(n³)) or, for non-contiguous problems, dynamic programming. Sliding window is the answer specifically when the target subarray/substring must be contiguous.

## 3. Core concept

**Key idea:** grow the window by moving `right` forward one step at a time. After each expansion, check whether the window still satisfies the required condition. If it does not, shrink the window by moving `left` forward until it does again. Track the best answer (longest or shortest window) at the appropriate point in this process.

There are two common shapes:
- **"At most / valid" windows (looking for the longest):** expand `right`; whenever the window becomes invalid, shrink `left` until valid again; record the window length every time it is valid.
- **"At least" windows (looking for the shortest):** expand `right` until the window first becomes valid; then shrink `left` as much as possible while it stays valid, recording the shortest length at each valid state.

**Why it works:** the window only ever grows from the right and shrinks from the left — neither pointer moves backward. That means the total number of pointer moves across the whole scan is at most `2n` (n possible forward moves for `right`, n for `left`), giving O(n) time, versus the O(n²) of checking every subarray explicitly.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sliding window expanding and shrinking over an array">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">arr = [2, 1, 5, 2, 3, 2], target sum &lt;= 7</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="100" y="40" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <rect x="140" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="80" y="60" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="120" y="60" fill="#e6edf3" text-anchor="middle">5</text>
    <text x="160" y="60" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="20" y="95" fill="#79c0ff">window [0,2] sum=8 &gt; 7 -&gt; shrink left</text>
    <text x="20" y="120" fill="#8b949e">left moves to 1: window [1,2] sum=6 &lt;= 7 -&gt; valid, record length 2</text>
    <text x="20" y="145" fill="#8b949e">right keeps expanding; window grows and shrinks as it scans, never resetting</text>
  </g>
</svg>

The window's right edge always advances; the left edge only advances to restore a broken condition, never resetting to zero.

## 5. Runnable example

A generic "at most" sliding window skeleton you can adapt to different conditions by swapping the validity check.

```java
// SlidingWindowSignal.java
public class SlidingWindowSignal {

    // Generic longest-valid-window scan: window is valid while sum <= limit.
    static int longestWindowSumAtMost(int[] arr, int limit) {
        int left = 0, sum = 0, best = 0;
        for (int right = 0; right < arr.length; right++) {
            sum += arr[right];
            while (sum > limit) {
                sum -= arr[left];
                left++;
            }
            best = Math.max(best, right - left + 1);
        }
        return best;
    }

    public static void main(String[] args) {
        int[] arr = {2, 1, 5, 2, 3, 2};
        System.out.println("longest window with sum <= 7: "
            + longestWindowSumAtMost(arr, 7));
    }
}
```

How to run: save as `SlidingWindowSignal.java`, then run `java SlidingWindowSignal.java`.

## 6. Walkthrough

1. `right = 0`: window `[2]`, sum `2`. Valid (`<= 7`). Best length so far: `1`.
2. `right = 1`: window `[2,1]`, sum `3`. Valid. Best length: `2`.
3. `right = 2`: window `[2,1,5]`, sum `8`. Invalid — shrink: remove `arr[0]=2`, sum `6`, `left = 1`. Window `[1,5]` is now valid. Best length stays `2`.
4. `right = 3`: window `[1,5,2]`, sum `8`. Invalid — shrink: remove `arr[1]=1`, sum `7`, `left = 2`. Window `[5,2]` valid. Best length stays `2`.
5. Continuing this way, the scan finds the longest valid window without ever re-examining elements already shrunk past.

## 7. Gotchas & takeaways

> Gotcha: forgetting to shrink the window in a `while` loop (using `if` instead) can leave the window invalid after only one shrink step, when more than one element needs removing to restore validity.

- "Contiguous" is the non-negotiable signal — sliding window does not apply to subsequence problems that allow skipping elements.
- The window's total movement (both pointers combined) is bounded by 2n, which is what gives sliding window its O(n) time.
