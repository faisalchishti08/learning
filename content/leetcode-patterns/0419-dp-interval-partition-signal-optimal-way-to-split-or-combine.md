---
card: leetcode-patterns
gi: 419
slug: dp-interval-partition-signal-optimal-way-to-split-or-combine
title: "DP: Interval / Partition — signal: optimal way to split or combine a range"
---

## 1. What it is

Interval (or partition) DP is the pattern for problems that ask for the best way to SPLIT a range into pieces, or COMBINE a range into one final result, where the cost of joining two pieces depends on their boundary values. Think of merging stacks of stones two at a time, or picking which balloon to pop LAST inside a stretch of balloons — the answer for a whole range is built from the best answer of every way to break it into two smaller ranges.

## 2. Why & when

Reach for this pattern whenever a problem gives you a RANGE (an array, a string, a polygon's vertices) and asks for the minimum cost, maximum score, or best strategy for processing the WHOLE range by repeatedly splitting it or combining pieces of it. The defining trait: the cost of combining two adjacent pieces depends on VALUES AT THE BOUNDARY of the range, not on the pieces' internal contents.

Learn to recognize these signals in a problem statement:

- **"Guess a number, and if wrong, pay the number you guessed"** — an interval game, where a range `[i, j]` of possible answers needs a worst-case-optimal guess.
- **"Take numbers from either end of the array to maximize your score"** — a two-player interval game, where each choice shrinks the range from one side.
- **"Merge k adjacent piles into one, paying the sum each time"** — a partition problem, where the range's cost depends on how it is broken into merge-able chunks.
- **"Burst a balloon, gaining `nums[left] * nums[i] * nums[right]`"** — a combine problem, where the LAST action inside a range determines its boundary cost.

The alternative — trying every possible split order with plain recursion — costs exponential time, since there are exponentially many ways to nest splits inside a range. The DP formulation reduces this to polynomial time by reusing the best answer for every SUB-range once, instead of recomputing it for every larger range that contains it.

## 3. Core concept

Every interval-DP problem reduces to the SAME per-range decision, tried over every possible split point:

**The state.** `dp[i][j]` = the best answer (a minimum cost, a maximum score, or a game-optimal value) for the range spanning index `i` to index `j`.

**The transition.** For each range `[i, j]`, try every split point `k` strictly between `i` and `j`: `dp[i][j] = best over k of (dp[i][k] + dp[k][j] + cost(i, k, j))`, where `cost(i, k, j)` is whatever the problem charges for combining (or splitting at) that particular boundary.

**Why the DP works:** the KEY property is that `dp[i][j]` depends only on SMALLER ranges strictly inside `[i, j]`. Filling ranges in order of INCREASING LENGTH guarantees every smaller range's answer is ready before a larger range needs it. The base case is usually the smallest possible range (a single element, or two adjacent elements), which has no further split to try.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a range from i to j being split at every possible point k, combining the two resulting sub-ranges plus a boundary cost">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">range [i, j] -- try every split point k strictly between i and j</text>
    <rect x="10" y="40" width="90" height="24" fill="#30363d" stroke="#8b949e"/><text x="55" y="57" text-anchor="middle" font-size="10">dp[i][k]</text>
    <rect x="110" y="40" width="90" height="24" fill="#30363d" stroke="#8b949e"/><text x="155" y="57" text-anchor="middle" font-size="10">dp[k][j]</text>
    <rect x="10" y="75" width="300" height="24" fill="#3fb950"/><text x="160" y="92" fill="#0d1117" text-anchor="middle" font-size="10">dp[i][j] = best over all k of dp[i][k] + dp[k][j] + cost(i,k,j)</text>
  </g>
</svg>

Every range's answer is the best combination over all possible ways to split it into two smaller ranges.

## 5. Runnable example

```java
// IntervalPartitionSignal.java
public class IntervalPartitionSignal {

    // Signal check: minimum-score triangulation -- dp[i][j] tries every
    // split point k, combining two sub-ranges plus a boundary cost.
    static int minScoreTriangulation(int[] values) {
        int n = values.length;
        int[][] dp = new int[n][n];
        for (int len = 2; len < n; len++) {
            for (int i = 0; i + len < n; i++) {
                int j = i + len;
                int best = Integer.MAX_VALUE;
                for (int k = i + 1; k < j; k++) {
                    best = Math.min(best, dp[i][k] + dp[k][j] + values[i] * values[k] * values[j]);
                }
                dp[i][j] = best;
            }
        }
        return dp[0][n - 1];
    }

    public static void main(String[] args) {
        System.out.println(minScoreTriangulation(new int[]{1, 2, 3}));
        // 6
    }
}
```

**How to run:** `java IntervalPartitionSignal.java`

## 6. Walkthrough

1. You read a problem statement. "Guess a number and pay a penalty," "take from either end," "merge adjacent piles," or "burst a balloon" are all interval-DP signals.
2. Running `minScoreTriangulation([1,2,3])` confirms the only possible triangle `(1,2,3)` scores `1*2*3 = 6`.
3. `dp[i][j]` is filled by LENGTH, from the smallest ranges (adjacent pairs, needing no split) up to the full range — every split point `k` reuses two already-solved sub-ranges.
4. If instead the problem involves TWO PLAYERS choosing from either end, the split points collapse to just two choices (take the left end, or take the right end) instead of scanning every `k` — a specialized, faster version of the same idea.
5. This upfront classification (game over a range vs. merge cost vs. combine-last-action) tells you which specific boundary cost function the next page's template plugs in.

## 7. Gotchas & takeaways

> Gotcha: filling `dp[i][j]` in the WRONG order (e.g. row by row instead of by increasing length) can read an unfilled cell — the loop must guarantee every smaller sub-range referenced by `dp[i][k]` and `dp[k][j]` is already computed, which the "increasing length" iteration order always provides.

- The state `dp[i][j]`, built by trying every split point `k` strictly inside `[i, j]`: the core interval-DP signal, distinguishing it from the fixed, small look-back of Fibonacci/Linear DP or the two-neighbor look-back of grid DP.
- Two-player "take from either end" games are a special case where the split collapses to exactly two options (leftmost or rightmost element), not a full scan over `k` — recognize this shortcut when it applies.
- Watch for how the boundary cost `cost(i, k, j)` is defined: it can use just the two endpoints (`values[i] * values[k] * values[j]`), a prefix sum over the whole range, or something problem-specific — always confirm this before reusing a template.
