---
card: leetcode-patterns
gi: 336
slug: number-of-ways-to-earn-points
title: Number of Ways to Earn Points
---

## 1. What it is

An exam has several TYPES of questions. `types[i] = [count, marks]` means there are `count` questions of a type, each worth `marks` points. Given `target` (points needed) and `types`, return the number of ways to answer questions so the total points equal EXACTLY `target`. Two ways differ if the number of questions answered from some type differs. Example: `target = 6`, `types = [[6,1],[3,2],[2,3]]` → `7`.

## 2. Why & when

This combines Maximum Value of K Coins From Piles' "grouped choice" idea (choose how many questions of THIS type to answer, from `0` to `count`) with Target Sum's "count the ways" idea (accumulate counts, not just track reachability or maximize a value). Use this shape whenever a problem counts the number of ways to hit an EXACT target, where items come in GROUPS offering a small range of quantities each.

## 3. Core concept

**Key idea:** `dp[p]` = the number of ways to reach EXACTLY `p` points using types processed so far. For each type, try every possible NUMBER of questions answered from that type (`0` to `count`), accumulating into a fresh table.

**Steps:**
1. Create `dp[target+1]`, with `dp[0] = 1` (one way to reach `0` points: answer nothing).
2. For each type `(count, marks)`: build `newDp`, a COPY of `dp` (representing "answer 0 questions of this type").
3. For `k` from `1` to `count`: for `p` from `target` DOWN TO `k * marks`: `newDp[p] = (newDp[p] + dp[p - k*marks]) % MOD` (answering exactly `k` questions of this type, worth `k*marks` points, combined with every way to reach the remaining `p - k*marks` points using EARLIER types only).
4. Set `dp = newDp` after each type. Return `dp[target]`.

**Why it is correct:** this is the SAME grouped-choice mechanism as Maximum Value of K Coins From Piles (exactly one quantity chosen per type, from a bounded range), combined with the SAME accumulate-counts mechanism as Target Sum (`+=` instead of `max` or `OR`). Reading every `k` against the PRE-type `dp` (not the partially-updated `newDp`) ensures each type contributes its chosen quantity exactly once per counted way, avoiding any double-counting of the same type's questions.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="For a type with count 3 and marks 2, trying k=1,2,3 questions, each adding dp of the remaining points before this type">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">type = [count=3, marks=2], target=6; dp before this type = [1,0,0,0,0,0,0]</text>
    <text x="10" y="45">k=1 (2 pts): newDp[2] += dp[0] = 1; newDp[4] += dp[2]=0; newDp[6] += dp[4]=0</text>
    <text x="10" y="65">k=2 (4 pts): newDp[4] += dp[0] = 1; newDp[6] += dp[2]=0</text>
    <text x="10" y="85">k=3 (6 pts): newDp[6] += dp[0] = 1</text>
    <rect x="10" y="100" width="200" height="24" fill="#3fb950"/><text x="110" y="117" fill="#0d1117" text-anchor="middle" font-size="10">newDp[6] = 1 after this type alone</text>
  </g>
</svg>

Each quantity `k` for this type reads from the PRE-type `dp`, so contributions from different `k` values (and different types) never overlap incorrectly.

## 5. Runnable example

```java
// NumberOfWaysToEarnPoints.java
public class NumberOfWaysToEarnPoints {

    static final int MOD = 1_000_000_007;

    // KEY INSIGHT: combines grouped-choice DP (pick a quantity 0..
    // count per type) with counting-ways DP (accumulate, not max) --
    // each k reads the PRE-type dp to avoid double-counting.

    static int waysToReachTarget(int target, int[][] types) {
        int[] dp = new int[target + 1];
        dp[0] = 1;

        for (int[] type : types) {
            int count = type[0], marks = type[1];
            int[] newDp = dp.clone();

            for (int k = 1; k <= count; k++) {
                int cost = k * marks;
                for (int p = target; p >= cost; p--) {
                    newDp[p] = (newDp[p] + dp[p - cost]) % MOD;
                }
            }
            dp = newDp;
        }
        return dp[target];
    }

    public static void main(String[] args) {
        System.out.println(waysToReachTarget(6, new int[][]{{6, 1}, {3, 2}, {2, 3}}));
        // 7
        System.out.println(waysToReachTarget(5, new int[][]{{50, 1}, {50, 2}, {50, 5}}));
        // 4
    }
}
```

**How to run:** `java NumberOfWaysToEarnPoints.java`

## 6. Walkthrough

Trace the effect of the FIRST type `[6, 1]` (up to 6 questions, each worth 1 point) on `dp`, starting from `dp = [1,0,0,0,0,0,0]`:

| k (questions answered) | cost | update |
|---|---|---|
| 1 | 1 | newDp[1] += dp[0] = 1 |
| 2 | 2 | newDp[2] += dp[0] = 1 |
| 3 | 3 | newDp[3] += dp[0] = 1 |
| 4 | 4 | newDp[4] += dp[0] = 1 |
| 5 | 5 | newDp[5] += dp[0] = 1 |
| 6 | 6 | newDp[6] += dp[0] = 1 |

After this type, `dp = [1,1,1,1,1,1,1]` (exactly one way to reach each point total from `0` to `6`, by answering that many 1-point questions). Continuing through the remaining two types eventually reaches `dp[6] = 7`, matching the expected answer. Time complexity is O(target · sum of all counts), since each type's inner double loop is bounded by `count * target`. Space is O(target), for the 1D DP array.

## 7. Gotchas & takeaways

> Gotcha: reading from `dp` (the PRE-type array) rather than `newDp` inside the `k` loop is essential — reading from `newDp` instead would let one type's OWN partial updates (for a smaller `k`) feed into a later `k` for the SAME type, incorrectly allowing that type's questions to be counted in combinations that do not correspond to any real, single choice of `k`.

- This problem is a direct combination of two techniques already seen on this card: Maximum Value of K Coins From Piles' grouped-choice loop, and Target Sum's accumulate-counts update.
- The modulus (`10^9 + 7`) matters here specifically because the number of ways can grow combinatorially large across many types — always apply it at each accumulation step, not just at the very end, to avoid integer overflow.
- Related problems: Maximum Value of K Coins From Piles (grouped choice, but maximizing value instead of counting ways), Target Sum (counting ways, but with a binary +/- choice instead of a grouped quantity choice).
