---
card: leetcode-patterns
gi: 392
slug: dp-longest-increasing-subsequence-complexity-o-n-log-n-with
title: "DP: Longest Increasing Subsequence — complexity: O(n log n) with binary search"
---

## 1. What it is

This page states and justifies the complexity of both LIS templates, and lists the problems that use this pattern, so you can confirm you have picked the right tool before coding.

## 2. Why & when

Knowing the complexity upfront lets you sanity-check a proposed solution against a problem's constraints BEFORE you write code. If `n` can be up to `1000`, the simple O(n^2) DP (about `10^6` operations) is fast enough and easier to adapt to complex compatibility rules. If `n` can be up to `10^5` or more, only the O(n log n) patience-sorting technique will finish in time — but it only works for the plain "strictly increasing" rule.

## 3. Core concept

**Time complexity, Template A (DP): O(n^2).** For each of the `n` elements, the inner loop scans up to `n` earlier elements, giving O(n^2) total comparisons.

**Time complexity, Template B (patience sorting): O(n log n).** For each of the `n` elements, a binary search into the `tails` list costs O(log n) (since `tails` has at most `n` entries, and stays sorted throughout), giving O(n log n) total.

**Space complexity:** O(n) for both templates — Template A's `dp` array, or Template B's `tails` list.

**Why patience sorting achieves the faster bound:** the key insight is that `tails` stays SORTED at all times, which is what makes binary search valid. Each new element either extends `tails` by one (if it is bigger than every current tail) or REPLACES exactly one existing tail (if it can improve — shrink — the ending value for some length) — both operations take O(log n) once the correct position is found via binary search.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="comparison of the n squared full scan approach versus the n log n binary search approach">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">Template A: for each of n elements, scan up to n earlier ones -&gt; O(n^2)</text>
    <text x="10" y="45" font-weight="bold">Template B: for each of n elements, binary search a sorted list -&gt; O(n log n)</text>
    <rect x="10" y="65" width="280" height="24" fill="#3fb950"/><text x="150" y="82" fill="#0d1117" text-anchor="middle" font-size="10">keeping tails sorted is what enables binary search</text>
  </g>
</svg>

Maintaining a sorted auxiliary structure trades a full linear scan for a logarithmic lookup, at each step.

## 5. Runnable example

```java
// LongestIncreasingSubsequenceComplexity.java
import java.util.*;

public class LongestIncreasingSubsequenceComplexity {

    // Confirms O(n log n): counts binary search comparisons done.
    static int lisPatienceWithCounter(int[] nums, long[] ops) {
        List<Integer> tails = new ArrayList<>();
        for (int num : nums) {
            int lo = 0, hi = tails.size();
            while (lo < hi) {
                ops[0]++;
                int mid = (lo + hi) / 2;
                if (tails.get(mid) < num) lo = mid + 1;
                else hi = mid;
            }
            if (lo == tails.size()) tails.add(num);
            else tails.set(lo, num);
        }
        return tails.size();
    }

    public static void main(String[] args) {
        int[] nums = {10, 9, 2, 5, 3, 7, 101, 18};
        long[] ops = {0};
        int len = lisPatienceWithCounter(nums, ops);
        System.out.println("len=" + len + " ops=" + ops[0]);
        // ops stays well under n * log2(n) = 8 * 3 = 24
    }
}
```

**How to run:** `java LongestIncreasingSubsequenceComplexity.java`

## 6. Walkthrough

1. `lisPatienceWithCounter` runs the standard patience-sorting template while counting every binary-search comparison in `ops`.
2. For `nums` of length `8`, the printed `ops` count stays well under `n * ceil(log2(n)) = 8 * 3 = 24`, confirming the search cost per element is logarithmic, not linear.
3. Each binary search touches only O(log(current tails size)) elements, never the full `tails` list.
4. Compare this to Template A, which would perform up to `7 + 6 + ... + 1 = 28` comparisons for this same 8-element input — already more than Template B's bound, and the gap widens fast as `n` grows.
5. This confirms Template B is worth the extra complexity specifically when `n` is large and the compatibility rule is the plain "strictly increasing" check — otherwise, Template A's simplicity is usually the better trade-off.

## 7. Gotchas & takeaways

> Gotcha: patience sorting's O(n log n) bound applies ONLY to computing the LENGTH — reconstructing the actual longest subsequence, or counting how many distinct longest subsequences exist, generally requires EXTRA bookkeeping (parent pointers, or falling back to the O(n^2) DP), which can raise the effective complexity back toward O(n^2).

- Time: O(n^2) for Template A, O(n log n) for Template B; space: O(n) for both.
- The O(n log n) bound is a genuine algorithmic improvement (not just a constant-factor speedup) — it changes which input sizes are feasible within typical time limits.
- Problems that use this pattern: Longest Increasing Subsequence, Largest Divisible Subset, Number of Longest Increasing Subsequence, Maximum Length of Pair Chain, Longest Arithmetic Subsequence, Longest String Chain, Best Team With No Conflicts, Russian Doll Envelopes, Minimum Number of Removals to Make Mountain Array.
