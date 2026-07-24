---
card: leetcode-patterns
gi: 334
slug: profitable-schemes
title: Profitable Schemes
---

## 1. What it is

A gang has `n` members. Given `group[i]` (members needed) and `profit[i]` (profit earned) for each of several possible crimes, and integers `minProfit`, count the number of DIFFERENT SUBSETS of crimes where the total members used does not exceed `n`, AND the total profit is AT LEAST `minProfit`. Example: `n = 5`, `minProfit = 3`, `group = [2,2]`, `profit = [2,3]` → `2`.

## 2. Why & when

This is 0/1 knapsack with TWO independent constraints tracked together: a capacity limit (member count, `<= n`) and a THRESHOLD to MEET OR EXCEED (profit, `>= minProfit`), while COUNTING the number of valid subsets. Use this shape whenever a problem counts subsets subject to both an upper-bound resource limit and a lower-bound target requirement.

## 3. Core concept

**Key idea:** extend the state to `dp[membersUsed][profitCapped]`, where `profitCapped` is CLAMPED at `minProfit` (any profit at or above `minProfit` is treated as equally "successful," since the problem only asks whether the threshold is met, not by how much).

**Steps:**
1. Create `dp[n+1][minProfit+1]`, all zeros, with `dp[0][0] = 1` (one way: the empty subset, using 0 members, earning 0 profit).
2. For each crime `i` (needing `group[i]` members, earning `profit[i]`): loop `members` from `n` DOWN TO `group[i]`, and for each `members`, loop `p` from `minProfit` DOWN TO `0`: let `newProfit = min(minProfit, p + profit[i])` (clamp at the threshold). Add `dp[members - group[i]][p]` to `dp[members][newProfit]`.
3. Sum `dp[members][minProfit]` over ALL `members` from `0` to `n` — this counts every subset whose members fit within `n` and whose profit reaches at least `minProfit` (since profit is clamped, index `minProfit` represents "at least `minProfit`").
4. Take the result modulo `10^9 + 7` (the problem's required modulus, since the count can be very large).

**Why it is correct:** this is the 0/1 knapsack COUNTING template (like Target Sum), extended with a SECOND dimension for profit, and a CLAMPING trick that collapses "any profit `>= minProfit`" into a single bucket (index `minProfit`), which is valid because the problem only cares about REACHING the threshold, not the exact excess amount. Descending loops on BOTH `members` and `p` preserve the "each crime used at most once" guarantee across both dimensions.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="2D dp table over members used and clamped profit, updating as each crime is considered, summing the minProfit column at the end">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">n=5, minProfit=3, crimes: group=[2,2], profit=[2,3]</text>
    <text x="10" y="45">crime 0 (2 members, profit 2): dp[2][2] += dp[0][0] = 1</text>
    <text x="10" y="65">crime 1 (2 members, profit 3): dp[2][3] += dp[0][0] = 1 (clamped: 0+3=3)</text>
    <text x="10" y="85">also: dp[4][3] += dp[2][min(3,2+3)] ... considering both crimes together</text>
    <rect x="10" y="100" width="220" height="24" fill="#3fb950"/><text x="120" y="117" fill="#0d1117" text-anchor="middle" font-size="10">sum over members of dp[members][3] = 2</text>
  </g>
</svg>

Profit beyond `minProfit` is clamped into the same final bucket, since only "reaching the threshold" matters.

## 5. Runnable example

```java
// ProfitableSchemes.java
public class ProfitableSchemes {

    static final int MOD = 1_000_000_007;

    // KEY INSIGHT: clamp profit at minProfit, since any profit AT
    // LEAST minProfit counts the same -- this bounds the profit
    // dimension to a fixed, small size instead of growing unbounded.

    static int profitableSchemes(int n, int minProfit, int[] group, int[] profit) {
        int[][] dp = new int[n + 1][minProfit + 1];
        dp[0][0] = 1;

        for (int i = 0; i < group.length; i++) {
            int members = group[i], gain = profit[i];
            for (int m = n; m >= members; m--) {
                for (int p = minProfit; p >= 0; p--) {
                    int newProfit = Math.min(minProfit, p + gain);
                    dp[m][newProfit] = (dp[m][newProfit] + dp[m - members][p]) % MOD;
                }
            }
        }

        int total = 0;
        for (int m = 0; m <= n; m++) {
            total = (total + dp[m][minProfit]) % MOD;
        }
        return total;
    }

    public static void main(String[] args) {
        System.out.println(profitableSchemes(5, 3, new int[]{2, 2}, new int[]{2, 3}));
        // 2
        System.out.println(profitableSchemes(10, 5, new int[]{2, 3, 5}, new int[]{6, 7, 8}));
        // 7
    }
}
```

**How to run:** `java ProfitableSchemes.java`

## 6. Walkthrough

Trace `profitableSchemes(5, 3, [2,2], [2,3])`:

| crime | members, gain | key updates |
|---|---|---|
| 0 | 2, 2 | dp[2][2] += dp[0][0] = 1 |
| 1 | 2, 3 | dp[2][3] += dp[0][0] = 1 (clamped 0+3=3); dp[4][min(3,2+3)]=dp[4][3] += dp[2][2] = 1 |

Final table has `dp[2][3] = 1` (crime 1 alone) and `dp[4][3] = 1` (both crimes together, `2+2=4` members, `2+3=5` profit clamped to `3`). Summing `dp[m][3]` over all `m` gives `1 + 1 = 2`, matching the expected answer. Time complexity is O(G · n · minProfit), where `G` is the number of crimes. Space is O(n · minProfit), for the 2D table.

## 7. Gotchas & takeaways

> Gotcha: forgetting to clamp `p + gain` at `minProfit` (using an UNCLAMPED profit dimension instead) would require a MUCH larger table (sized to the maximum possible total profit, not just `minProfit`), and would need to separately sum every profit index `>= minProfit` at the end instead of reading a single clamped bucket.

- Clamping a dimension at its THRESHOLD (rather than letting it grow unbounded) is a general technique whenever a problem only cares about "at least X," not the exact value.
- This combines THREE 0/1 knapsack ideas at once: counting (like Target Sum), a capacity limit (like classic knapsack), and a clamped threshold dimension (unique to problems like this one).
- Related problems: Target Sum (0/1 knapsack counting without a second dimension), Ones and Zeroes (0/1 knapsack with two UNCLAMPED capacity dimensions, both upper-bounded rather than one being a lower-bound threshold).
