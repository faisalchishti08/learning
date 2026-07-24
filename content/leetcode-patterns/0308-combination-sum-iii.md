---
card: leetcode-patterns
gi: 308
slug: combination-sum-iii
title: Combination Sum III
---

## 1. What it is

Find all valid combinations of exactly `k` distinct numbers, chosen from `1` to `9`, that sum to `n`. Each number may be used at most once, and the same combination may not appear twice (in any order). Example: `k = 3`, `n = 7` → `[[1,2,4]]`.

## 2. Why & when

This is a bounded-choice backtracking problem: build up a combination one number at a time, from a small fixed pool (`1` to `9`), pruning as soon as the running sum exceeds `n` or too many numbers have been chosen. Use this shape whenever a problem wants combinations (order does not matter) drawn from a small, fixed set, meeting both a COUNT constraint and a SUM constraint.

## 3. Core concept

**Key idea:** try each number from `1` to `9` in increasing order, only ever moving FORWARD through the pool (never revisiting a smaller number), to avoid generating the same combination in a different order.

**Steps:**
1. Define `backtrack(start, remainingCount, remainingSum, current)`.
2. **Base case:** if `remainingCount == 0`: if `remainingSum == 0`, record `current` as valid; either way, return.
3. **Prune:** if `remainingSum <= 0` or `start > 9`, stop early (no way to still succeed).
4. **Loop:** for `num` from `start` to `9`: if `num > remainingSum`, stop the loop entirely (every later `num` is even bigger, since the pool is scanned in increasing order); otherwise, choose `num` (add to `current`), recurse with `start = num + 1`, `remainingCount - 1`, `remainingSum - num`, then un-choose.

**Why it is correct:** always advancing `start` forward (never back to a smaller number) guarantees every combination is generated in exactly one increasing order, so no duplicate combination (like `[1,2,4]` and `[2,1,4]`) is ever produced. Breaking the loop as soon as `num > remainingSum` is a valid prune specifically because the pool is scanned in increasing order — every number after `num` is even larger, so none of them could possibly fit either.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Backtracking search for k=3 numbers summing to 7, pruning branches where the running sum exceeds the target">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">k=3, n=7</text>
    <text x="10" y="45">choose 1 -&gt; remaining count=2, sum=6</text>
    <text x="10" y="65">choose 2 (from start=2) -&gt; remaining count=1, sum=4</text>
    <text x="10" y="85">choose 4 (from start=3) -&gt; remaining count=0, sum=0 -&gt; valid!</text>
    <text x="10" y="105">un-choose 4, try 5,6,7,... but 5&gt;4 so loop stops (prune)</text>
    <rect x="10" y="120" width="150" height="24" fill="#3fb950"/><text x="85" y="137" fill="#0d1117" text-anchor="middle" font-size="10">found: [1,2,4]</text>
  </g>
</svg>

Always scanning candidates in increasing order lets the search stop the loop the instant a candidate is too big.

## 5. Runnable example

```java
// CombinationSumIII.java
import java.util.*;

public class CombinationSumIII {

    // KEY INSIGHT: scanning candidates 1..9 in strictly increasing
    // order, using a "start" index that only moves forward, prevents
    // duplicate combinations without needing to sort or deduplicate
    // results afterward.

    static List<List<Integer>> combinationSum3(int k, int n) {
        List<List<Integer>> results = new ArrayList<>();
        backtrack(1, k, n, new ArrayList<>(), results);
        return results;
    }

    static void backtrack(int start, int remainingCount, int remainingSum,
                           List<Integer> current, List<List<Integer>> results) {
        if (remainingCount == 0) {
            if (remainingSum == 0) results.add(new ArrayList<>(current));
            return;
        }
        for (int num = start; num <= 9 && num <= remainingSum; num++) {
            current.add(num);                                              // choose
            backtrack(num + 1, remainingCount - 1, remainingSum - num, current, results); // recurse
            current.remove(current.size() - 1);                            // un-choose
        }
    }

    public static void main(String[] args) {
        System.out.println(combinationSum3(3, 7));
        // [[1, 2, 4]]
        System.out.println(combinationSum3(3, 9));
        // [[1, 2, 6], [1, 3, 5], [2, 3, 4]]
    }
}
```

**How to run:** `java CombinationSumIII.java`

## 6. Walkthrough

Trace `combinationSum3(3, 7)`:

| current | start | remainingCount | remainingSum | action |
|---|---|---|---|---|
| [] | 1 | 3 | 7 | try num=1 |
| [1] | 2 | 2 | 6 | try num=2 |
| [1,2] | 3 | 1 | 4 | try num=3 (3&lt;=4, continue) then num=4 |
| [1,2,4] | 5 | 0 | 0 | remainingCount==0 and remainingSum==0 -&gt; record [1,2,4] |
| [1,2] | back to trying num=5 | — | 4 &lt; 5 | loop condition num&lt;=remainingSum fails, stop |

After exhausting the `[1,2,...]` branch and backtracking further, no other combination reaches exactly `7` with 3 distinct numbers from `1`–`9`. Final result: `[[1,2,4]]`. Time complexity is bounded by O(C(9,k)), the number of ways to choose `k` numbers from `9`, since the search space itself is small and fixed. Space is O(k), for the recursion depth and current combination.

## 7. Gotchas & takeaways

> Gotcha: the loop condition `num <= remainingSum` is a PRUNE, not just an optimization — without it, the search would still be correct (the base case would reject invalid sums), but it would waste time exploring branches that are already guaranteed to fail.

- The `start` parameter, always moving forward, is the standard technique for generating COMBINATIONS (order-independent) without duplicates — contrast with permutation problems, which instead track a `used[]` array and allow any order.
- Two independent prune conditions work together here: the count budget (`remainingCount`) and the sum budget (`remainingSum`) — both must reach exactly zero together for a valid result.
- Related problems: Combination Sum (allows reusing the same number multiple times, changing the recursive call's `start` argument), Letter Case Permutation (a different kind of choice — case, not selection from a pool).
