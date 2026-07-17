---
card: leetcode-patterns
gi: 44
slug: maximum-points-you-can-obtain-from-cards
title: Maximum Points You Can Obtain from Cards
---

## 1. What it is

You are given an array `cardPoints`, and you must take exactly `k` cards, each turn taking one from either the front or the back of the remaining row. Return the maximum score you can achieve. Example: `cardPoints = [1, 2, 3, 4, 5, 6, 1]`, `k = 3` → answer `12` (take the last three cards: `5 + 6 + 1 = 12`).

## 2. Why & when

Taking `k` cards from the two ends is equivalent to *leaving behind* a contiguous subarray of length `n - k` in the middle. Minimizing the sum of what is left behind maximizes what you take — turning a two-ended greedy-looking problem into a single fixed-size sliding window that finds the minimum-sum middle segment.

## 3. Core concept

**Key idea:** whatever combination of front and back cards you take, the untaken cards always form one contiguous block in the middle (since taking always removes from the outside in). So instead of searching over all front/back split combinations directly, search over all possible positions of that middle block of size `n - k`, and pick the one with the smallest sum.

**Steps:**
1. Compute `total`, the sum of all of `cardPoints`.
2. If `k == n`, return `total` (you take every card, nothing is left behind).
3. Set `windowSize = n - k`. Compute the sum of the first `windowSize` elements as the initial `windowSum` and `minWindowSum`.
4. Slide this fixed-size window across the rest of the array (same technique as Maximum Average Subarray I), tracking the minimum sum seen.
5. Return `total - minWindowSum`.

**Why it is correct:** every valid way of taking exactly `k` cards from the two ends corresponds to exactly one contiguous "leftover" block of size `n - k` somewhere in the array (the leftover block's start position ranges from 0, meaning you took all `k` from the back, to `k`, meaning you took all `k` from the front). Since `total` is fixed, maximizing the taken sum is equivalent to minimizing the leftover sum — and scanning every possible leftover block position with a fixed-size sliding window finds that minimum directly.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Maximum points from cards leftover window in the middle">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">cardPoints = [1,2,3,4,5,6,1], k=3, n=7, leftover window size = 4</text>
    <rect x="20" y="40" width="30" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="50" y="40" width="30" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="80" y="40" width="30" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="110" y="40" width="30" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="140" y="40" width="30" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="170" y="40" width="30" height="30" fill="#161b22" stroke="#f0883e"/>
    <rect x="200" y="40" width="30" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="35" y="60" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="65" y="60" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="95" y="60" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="125" y="60" fill="#e6edf3" text-anchor="middle">4</text>
    <text x="155" y="60" fill="#e6edf3" text-anchor="middle">5</text>
    <text x="185" y="60" fill="#e6edf3" text-anchor="middle">6</text>
    <text x="215" y="60" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="20" y="95" fill="#8b949e">taking front=1, back=2 leaves middle window [1,4] = [2,3,4,5] as leftover</text>
    <text x="20" y="118" fill="#8b949e">slide this size-4 window across all positions; pick the smallest sum</text>
  </g>
</svg>

Whatever cards you take from the ends, the untaken cards always form one contiguous block — sliding a fixed-size window over every possible position of that block finds the best split.

## 5. Runnable example

```java
// MaxPointsFromCards.java
public class MaxPointsFromCards {

    // Level 1 -- Brute force: try every split of k cards between front and
    // back directly. O(k) time, O(1) space -- actually already efficient,
    // but framed without the "leftover window" insight, so it doesn't
    // generalize as cleanly to related problems.
    static int bruteForce(int[] cardPoints, int k) {
        int n = cardPoints.length, best = 0;
        for (int front = 0; front <= k; front++) {
            int back = k - front;
            int sum = 0;
            for (int i = 0; i < front; i++) sum += cardPoints[i];
            for (int i = 0; i < back; i++) sum += cardPoints[n - 1 - i];
            best = Math.max(best, sum);
        }
        return best;
    }

    // KEY INSIGHT: the untaken cards always form one contiguous middle
    // block, so minimizing that block's sum (a fixed-size sliding window)
    // is equivalent to maximizing the taken sum.

    // Level 2 -- Optimal: total minus minimum fixed-size window. O(n)
    // time, O(1) space.
    public static int maxScore(int[] cardPoints, int k) {
        int n = cardPoints.length;
        int total = 0;
        for (int c : cardPoints) total += c;
        if (k == n) return total;

        int windowSize = n - k;
        int windowSum = 0;
        for (int i = 0; i < windowSize; i++) windowSum += cardPoints[i];
        int minWindowSum = windowSum;

        for (int i = windowSize; i < n; i++) {
            windowSum += cardPoints[i] - cardPoints[i - windowSize];
            minWindowSum = Math.min(minWindowSum, windowSum);
        }

        return total - minWindowSum;
    }

    // Level 3 -- Hardened: k == 0 means you take nothing, and the leftover
    // window covers the whole array, so total - minWindowSum correctly
    // evaluates to 0.
    static int hardened(int[] cardPoints, int k) {
        if (cardPoints == null || k < 0 || k > cardPoints.length) {
            throw new IllegalArgumentException("invalid k for this array");
        }
        return maxScore(cardPoints, k);
    }

    public static void main(String[] args) {
        int[] cardPoints = {1, 2, 3, 4, 5, 6, 1};
        System.out.println("brute force: " + bruteForce(cardPoints, 3));
        System.out.println("optimal:     " + maxScore(cardPoints, 3));
        System.out.println("k == 0:      " + hardened(cardPoints, 0));
    }
}
```

How to run: save as `MaxPointsFromCards.java`, then run `java MaxPointsFromCards.java`.

## 6. Walkthrough

Dry run of `maxScore({1,2,3,4,5,6,1}, k = 3)`: `total = 22`, `windowSize = 7 - 3 = 4`.

| step | window | windowSum | minWindowSum |
|---|---|---|---|
| init | [0,3] = [1,2,3,4] | 10 | 10 |
| i=4 | [1,4] = [2,3,4,5] | 10+5-1=14 | 10 |
| i=5 | [2,5] = [3,4,5,6] | 14+6-2=18 | 10 |
| i=6 | [3,6] = [4,5,6,1] | 18+1-3=16 | 10 |

Minimum leftover sum: `10` (the first window `[1,2,3,4]`). Answer: `total - minWindowSum = 22 - 10 = 12`. Time complexity: O(n). Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: forgetting the `k == n` special case causes `windowSize` to become `0`, and a zero-length window's sum is trivially `0` — while technically correct in that edge case, it's clearer and safer to handle it explicitly.

- "Complement the problem" — turning "maximize what you take from the ends" into "minimize what's left in the middle" — is a reusable reframing whenever a problem describes removing from both ends of a fixed-size selection.
- Related problems: Maximum Average Subarray I, Grumpy Bookstore Owner (a similar fixed-window-bonus framing).
