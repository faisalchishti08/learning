---
card: leetcode-patterns
gi: 332
slug: maximum-value-of-k-coins-from-piles
title: Maximum Value of K Coins From Piles
---

## 1. What it is

Given a list of piles, each a list of positive integers (coin values, top to bottom meaning you must take coins from the TOP of a pile in order), and an integer `k`, choose exactly `k` coins total, by taking any prefix (`0` or more coins from the top) of each pile, to MAXIMIZE the total value. Example: `piles = [[1,100,3],[7,8,9]]`, `k = 2` → `101` (take the top 2 coins from the first pile: `1 + 100`).

## 2. Why & when

This generalizes 0/1 knapsack: instead of choosing "take or skip" for each individual ITEM, you choose how MANY coins (a prefix count, `0` to `pile.length`) to take from each PILE — a GROUPED choice. Use this shape whenever a problem's items are organized into GROUPS, and you must choose exactly one option (here, a prefix length) from each group, subject to a shared total budget.

## 3. Core concept

**Key idea:** precompute prefix sums for each pile (the value of taking the top `1, 2, 3, ...` coins). Then run a knapsack-style DP over piles, where the "capacity" is the number of coins chosen so far, and each pile's "choices" are its own prefix sums.

**Steps:**
1. For each pile, compute `prefixSums[j]` = sum of the top `j` coins, for `j` from `0` to `pile.length`.
2. Create `dp[k+1]`, an integer array, all zeros: `dp[c]` = the max value achievable using `c` coins from piles processed so far.
3. For each pile: create a NEW array `newDp` (a copy of `dp`, since this differs from single-item knapsack — you must consider "take `j` coins from THIS pile" against the state BEFORE this pile, and `j` can range over multiple values, not just 0 or 1).
4. For `c` from `0` to `k`: for `j` from `0` to `min(pile.length, c)`: `newDp[c] = max(newDp[c], dp[c - j] + prefixSums[j])`.
5. Set `dp = newDp` after each pile. Return `dp[k]`.

**Why it is correct:** each pile contributes a GROUP of mutually exclusive choices (take `0` coins, take `1` coin, ..., take all coins from this pile) — exactly ONE of these choices is made per pile, which is why the DP must consider ALL of a pile's prefix options against the PRE-pile state, not just a binary take/skip. This is 0/1 knapsack's "each item once" idea generalized to "each group contributes exactly one of several mutually exclusive options."

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="For pile 1,100,3 with prefix sums 0,1,101,104, updating dp for k=2 by trying each possible prefix count against the pre-pile state">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">pile = [1,100,3], prefixSums = [0,1,101,104]; before this pile, dp=[0,0,0] (k=0,1,2)</text>
    <text x="10" y="45">newDp[2] candidates: j=0: dp[2]+0=0; j=1: dp[1]+1=1; j=2: dp[0]+101=101</text>
    <rect x="10" y="60" width="200" height="24" fill="#3fb950"/><text x="110" y="77" fill="#0d1117" text-anchor="middle" font-size="10">newDp[2] = max(0,1,101) = 101</text>
  </g>
</svg>

Each pile's prefix sums act as a set of mutually exclusive "how many coins from here" options.

## 5. Runnable example

```java
// MaximumValueOfKCoinsFromPiles.java
import java.util.List;

public class MaximumValueOfKCoinsFromPiles {

    // KEY INSIGHT: each pile contributes exactly ONE choice (a prefix
    // length), generalizing 0/1 knapsack's binary take/skip to a
    // multi-way "take j coins from this group" choice per pile.

    static int maxValueOfCoins(List<List<Integer>> piles, int k) {
        int[] dp = new int[k + 1];

        for (List<Integer> pile : piles) {
            int[] prefixSums = new int[pile.size() + 1];
            for (int j = 1; j <= pile.size(); j++) {
                prefixSums[j] = prefixSums[j - 1] + pile.get(j - 1);
            }

            int[] newDp = dp.clone();
            for (int c = 0; c <= k; c++) {
                for (int j = 1; j <= Math.min(pile.size(), c); j++) {
                    newDp[c] = Math.max(newDp[c], dp[c - j] + prefixSums[j]);
                }
            }
            dp = newDp;
        }
        return dp[k];
    }

    public static void main(String[] args) {
        List<List<Integer>> piles = List.of(List.of(1, 100, 3), List.of(7, 8, 9));
        System.out.println(maxValueOfCoins(piles, 2));
        // 101
    }
}
```

**How to run:** `java MaximumValueOfKCoinsFromPiles.java`

## 6. Walkthrough

Trace `maxValueOfCoins([[1,100,3],[7,8,9]], 2)`:

| pile processed | prefixSums | dp after this pile (indices 0,1,2) |
|---|---|---|
| start | — | [0, 0, 0] |
| [1,100,3] | [0,1,101,104] | newDp[0]=0; newDp[1]=max(0(skip), dp[0]+1=1)=1; newDp[2]=max(0(skip), dp[1]+1=1, dp[0]+101=101)=101 -&gt; [0,1,101] |
| [7,8,9] | [0,7,15,24] | newDp[2]=max(101(skip pile2 entirely), dp[1]+7=1+7=8, dp[0]+15=15)=101 (skipping pile 2 wins) -&gt; [0,7,101] |

Final `dp[2] = 101`, matching the expected answer (taking `1` and `100` from the first pile, none from the second). Time complexity is O(k · N), where `N` is the total number of coins across all piles, since each pile's inner double loop is bounded by `pile.size() * k` but sums to O(N · k) across all piles. Space is O(k), for the DP array (plus temporary prefix sums per pile).

## 7. Gotchas & takeaways

> Gotcha: using the SAME array for both reading (`dp`) and writing (`newDp`) — instead of a separate copy — would let a pile's own prior updates (for a smaller `j` within the SAME pile) leak into later `j` calculations for that SAME pile, incorrectly allowing more than one "choice" from a single pile to combine.

- Grouped-choice knapsack (exactly one option per GROUP, from several mutually exclusive options) is a common generalization of 0/1 knapsack — recognize it whenever items come pre-organized into groups with an implicit "pick one" rule.
- Precomputing prefix sums per pile turns "value of taking the top `j` coins" into an O(1) lookup instead of an O(j) resum every time.
- Related problems: Ones and Zeroes (0/1 knapsack extended by extra CAPACITY dimensions, not extra CHOICES per item), Filling Bookcase Shelves (another grouped/sequential-choice DP, but over consecutive book groupings instead of pile prefixes).
