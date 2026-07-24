---
card: leetcode-patterns
gi: 331
slug: ones-and-zeroes
title: Ones and Zeroes
---

## 1. What it is

Given an array of binary strings `strs`, and integers `m` and `n`, find the size of the LARGEST subset of `strs` such that the subset contains AT MOST `m` `'0'`s and AT MOST `n` `'1'`s IN TOTAL. Example: `strs = ["10","0001","111001","1","0"]`, `m = 5`, `n = 3` → `4`.

## 2. Why & when

This is 0/1 knapsack with TWO independent capacity dimensions instead of one: each string "costs" some number of `0`s (one capacity) and some number of `1`s (another capacity), and "value" is simply `1` (counting how many strings fit). Use this shape whenever a problem has items with MULTIPLE independent resource costs, all constrained simultaneously.

## 3. Core concept

**Key idea:** extend the state from `dp[capacity]` to `dp[zerosUsed][onesUsed]`, representing the maximum number of strings selectable while using AT MOST that many zeros and ones. Process each string, updating the table in DESCENDING order on BOTH dimensions.

**Steps:**
1. Create `dp[m+1][n+1]`, all zeros. `dp[i][j]` = max strings selectable using at most `i` zeros and `j` ones.
2. For each string `s` in `strs`: count `zeros = number of '0's in s`, `ones = number of '1's in s`.
3. Loop `i` from `m` DOWN TO `zeros`, and for each `i`, loop `j` from `n` DOWN TO `ones`: `dp[i][j] = max(dp[i][j], dp[i - zeros][j - ones] + 1)` (skip this string, or take it and gain `1`, using up `zeros` and `ones` from the two capacities).
4. Return `dp[m][n]`.

**Why it is correct:** this is the exact 0/1 knapsack transition, generalized to 2 dimensions — a string is either included (reducing BOTH remaining capacities by its own zero-count and one-count, and adding `1` to the count) or excluded (leaving the state unchanged). Looping BOTH `i` and `j` in descending order preserves the "each string used at most once" guarantee in both dimensions simultaneously, exactly as the 1D descending loop does for a single capacity.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="2D dp table cell update for a string costing 2 zeros and 1 one, comparing skip versus take across both capacity dimensions">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">string "0011" costs zeros=2, ones=2; state m=5,n=3 processing dp[5][3]</text>
    <text x="10" y="45">skip: dp[5][3] stays as it was</text>
    <text x="10" y="65">take: dp[5][3] candidate = dp[5-2][3-2] + 1 = dp[3][1] + 1</text>
    <rect x="10" y="80" width="260" height="24" fill="#3fb950"/><text x="140" y="97" fill="#0d1117" text-anchor="middle" font-size="10">dp[5][3] = max(skip, take)</text>
  </g>
</svg>

Each string reduces BOTH the zero-budget and the one-budget when taken, so the DP tracks a 2D grid of remaining capacities.

## 5. Runnable example

```java
// OnesAndZeroes.java
public class OnesAndZeroes {

    // KEY INSIGHT: 0/1 knapsack generalizes cleanly to multiple
    // independent capacity dimensions -- here, zeros and ones -- by
    // extending the state to dp[zerosUsed][onesUsed] and looping
    // BOTH dimensions in descending order.

    static int findMaxForm(String[] strs, int m, int n) {
        int[][] dp = new int[m + 1][n + 1];

        for (String s : strs) {
            int zeros = 0, ones = 0;
            for (char c : s.toCharArray()) {
                if (c == '0') zeros++; else ones++;
            }

            for (int i = m; i >= zeros; i--) {
                for (int j = n; j >= ones; j--) {
                    dp[i][j] = Math.max(dp[i][j], dp[i - zeros][j - ones] + 1);
                }
            }
        }
        return dp[m][n];
    }

    public static void main(String[] args) {
        System.out.println(findMaxForm(new String[]{"10", "0001", "111001", "1", "0"}, 5, 3));
        // 4
        System.out.println(findMaxForm(new String[]{"10", "0", "1"}, 1, 1));
        // 2
    }
}
```

**How to run:** `java OnesAndZeroes.java`

## 6. Walkthrough

Trace the effect of processing string `"10"` (zeros=1, ones=1) on a few cells of `dp`, starting from all zeros:

| cell | before | candidate (take) | after |
|---|---|---|---|
| dp[5][3] | 0 | dp[4][2] + 1 = 0 + 1 = 1 | 1 |
| dp[1][1] | 0 | dp[0][0] + 1 = 0 + 1 = 1 | 1 |
| dp[0][0] | 0 | zeros=1 &gt; 0, loop never reaches this cell for this string | 0 (unchanged) |

Continuing this process for all 5 strings in the full example eventually reaches `dp[5][3] = 4`, meaning `4` strings (`"10"`, `"0001"`, `"1"`, `"0"`) fit within 5 zeros and 3 ones total. Time complexity is O(L · m · n), where `L` is the number of strings — each string does an O(m · n) table update. Space is O(m · n), for the 2D table.

## 7. Gotchas & takeaways

> Gotcha: looping only ONE of the two dimensions (`i`) in descending order while looping the other (`j`) ascending would let a string be "double counted" along the ascending dimension — BOTH loops must be descending to preserve the 0/1 (use-at-most-once) guarantee in both capacity dimensions simultaneously.

- This problem is the clearest example of extending 0/1 knapsack to MULTIPLE capacity dimensions — the same "skip vs take, descending loop" discipline just gets nested one level deeper per extra dimension.
- "Value" here is simply `1` per string (maximizing COUNT), but the same 2D-capacity technique works equally well if each string carried its own distinct value to maximize instead.
- Related problems: Partition Equal Subset Sum (single-dimension 0/1 knapsack reachability), Maximum Value of K Coins From Piles (a different kind of 0/1 knapsack extension, over grouped/sequential choices instead of extra capacity dimensions).
