---
card: leetcode-patterns
gi: 390
slug: dp-longest-increasing-subsequence-signal-longest-optimal-inc
title: "DP: Longest Increasing Subsequence — signal: longest/optimal increasing chain"
---

## 1. What it is

Longest Increasing Subsequence (LIS) is the pattern for finding the longest CHAIN of elements from a single array, picked in order, where each element is "compatible" with (usually strictly greater than) the one before it. Elements can be skipped; only relative order and the compatibility rule matter. Think of stacking boxes where each one must be strictly bigger than the one below it — you want the tallest possible stack using boxes in their given left-to-right order.

## 2. Why & when

Reach for this pattern whenever a problem asks for the longest (or best-scoring) CHAIN of elements from one sequence, where each next element must satisfy some ordering or compatibility rule relative to the previous one — and elements NOT in the chain can simply be skipped. The single-sequence, chain-building nature is the tell: unlike LCS (two sequences) or palindrome DP (a range folding inward), LIS builds a chain moving strictly FORWARD through one sequence.

Learn to recognize these signals in a problem statement:

- **"Longest increasing/non-decreasing subsequence"** — the defining LIS framing directly.
- **"Chain pairs where the second number of one pair is less than the first number of the next"** — a pair-chaining variant, still fundamentally "pick elements in order satisfying a compatibility rule."
- **"Build the longest string chain by adding one letter at a time"** — a word-chain variant, where "compatible" means "one word is the other plus one inserted letter."
- **"Longest arithmetic subsequence"** — an LIS variant where the "chain rule" is a constant difference, not just increasing order.

The alternative — trying every possible subsequence directly — costs exponential time (`O(2^n)`). The DP formulation reduces this to `O(n^2)` by reusing the best chain length ending at each earlier position; the further-optimized version using binary search reduces it to `O(n log n)`.

## 3. Core concept

Every LIS-family problem reduces to the SAME per-element decision, checked against every earlier compatible element:

**The state.** `dp[i]` = the length (or best score) of the longest valid chain ENDING exactly at element `i`.

**The transition.** For each `i`, look at every EARLIER element `j < i`: if element `j` is "compatible" with element `i` (usually `nums[j] < nums[i]`), then `dp[i]` could be extended from `dp[j]`: `dp[i] = max(dp[i], dp[j] + 1)`.

**Why the DP works:** the KEY property is that `dp[i]` depends only on `dp[j]` for `j < i` — filling the array left to right guarantees every dependency is ready before it is needed. The overall answer is the MAXIMUM over all `dp[i]`, since the longest chain can end anywhere, not necessarily at the last element.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp array showing element i extending the best chain from any earlier compatible element j">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">nums = [10, 9, 2, 5, 3, 7, 101, 18]</text>
    <text x="10" y="45">at i=5 (value 7): check j=0..4 for nums[j] &lt; 7</text>
    <text x="10" y="65">j=2 (2): dp[2]=1; j=3 (5): dp[3]=2; j=4 (3): dp[4]=2</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[5] = max(dp[3],dp[4]) + 1 = 3</text>
  </g>
</svg>

Each element's best chain length is built from the best compatible chain among ALL earlier elements, not just the immediately preceding one.

## 5. Runnable example

```java
// LongestIncreasingSubsequenceSignal.java
public class LongestIncreasingSubsequenceSignal {

    // Signal check: longest increasing chain -- each dp[i] checks
    // every earlier compatible element, not just i-1.
    static int lengthOfLIS(int[] nums) {
        int n = nums.length;
        int[] dp = new int[n];
        java.util.Arrays.fill(dp, 1);
        int maxLen = 1;

        for (int i = 1; i < n; i++) {
            for (int j = 0; j < i; j++) {
                if (nums[j] < nums[i]) {
                    dp[i] = Math.max(dp[i], dp[j] + 1);
                }
            }
            maxLen = Math.max(maxLen, dp[i]);
        }
        return maxLen;
    }

    public static void main(String[] args) {
        System.out.println(lengthOfLIS(new int[]{10, 9, 2, 5, 3, 7, 101, 18}));
        // 4 ([2,3,7,101] or [2,3,7,18])
    }
}
```

**How to run:** `java LongestIncreasingSubsequenceSignal.java`

## 6. Walkthrough

1. You read a problem statement. "Longest increasing subsequence," "chain of pairs/words," or "longest arithmetic subsequence" is the LIS-family signal.
2. Running `lengthOfLIS` on `[10,9,2,5,3,7,101,18]` confirms the longest increasing chain has length `4`.
3. At every index `i`, the algorithm checks EVERY earlier index `j`, not just `i-1` — this is what distinguishes LIS from the simpler Fibonacci/Linear pattern, whose look-back is always a small, fixed number of positions.
4. If instead the problem needs the chain in O(n log n), recognize the "patience sorting" variant: maintain a separate array of the smallest possible "tail" value for each chain length, and binary search into it instead of scanning all earlier elements.
5. This upfront classification (plain LIS vs. a chain over pairs/words vs. an arithmetic-difference chain) tells you which template on the next page to reach for.

## 7. Gotchas & takeaways

> Gotcha: the answer is `max(dp[i])` over ALL positions, not `dp[n-1]` — unlike LCS-family problems (whose answer is always the final cell `dp[m][n]`), an LIS chain can end at any position, so the maximum must be tracked separately.

- The state `dp[i]`, built by scanning ALL earlier `j < i` for compatibility: the core LIS-family signal, distinguishing it from the small, fixed look-back of Fibonacci/Linear DP.
- The O(n^2) DP scan is always correct; the O(n log n) patience-sorting technique is an OPTIMIZATION for the specific case of counting LENGTH only (reconstructing the actual sequence, or counting HOW MANY such sequences exist, often still needs the O(n^2) version or extra bookkeeping).
- Watch for variants where "compatible" is not simply `nums[j] < nums[i]` — pair chains, string chains, and arithmetic sequences all redefine the compatibility check while keeping the same DP shape.
