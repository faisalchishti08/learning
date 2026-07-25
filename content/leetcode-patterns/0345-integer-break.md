---
card: leetcode-patterns
gi: 345
slug: integer-break
title: Integer Break
---

## 1. What it is

Given an integer `n` (`n >= 2`), break it into a sum of AT LEAST two positive integers, and return the MAXIMUM PRODUCT of those integers. Example: `n = 10` → `36` (`3 + 3 + 4`, product `3 * 3 * 4 = 36`).

## 2. Why & when

This is Unbounded Knapsack's MAXIMIZE variant, but the "item" being reused is not a fixed list — it is EVERY smaller positive integer, since any piece from `1` to `n-1` is a valid "first cut." Recognize this shape whenever a problem asks you to split a number or sequence into reusable pieces and optimize a product or sum over the pieces, with the piece sizes themselves being part of the decision.

## 3. Core concept

**Key idea:** build `dp[a]` = the maximum product obtainable by breaking `a` into two or more positive parts, for every `a` from `2` to `n`, by trying every possible FIRST piece and combining it with the best answer for what remains.

**Steps:**
1. Create `dp[n + 1]`, with `dp[1] = 1` (a base case, not itself a valid answer but useful as a building block).
2. For `a` from `2` to `n`, for each `piece` from `1` to `a - 1`: candidate `= max(piece * (a - piece), piece * dp[a - piece])` (either stop after exactly two pieces, or break the remainder further using its own best answer).
3. `dp[a] = max(dp[a], candidate)` over every `piece`.
4. Return `dp[n]`.

**Why it is correct:** any optimal breakdown of `a` has SOME first piece; the rest of the breakdown (everything after that piece) is itself a smaller instance of the same problem. Trying `piece * (a - piece)` (stop here) versus `piece * dp[a - piece]` (break further) and taking the maximum over EVERY possible first piece guarantees the true optimum, because one of those first-piece choices must match the optimal solution's actual first piece.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp array for n=10 trying every first piece from 1 to 9 and combining with either stopping or breaking further">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">n=10; trying piece=3: remainder=7</text>
    <text x="10" y="45">stop: 3 * 7 = 21</text>
    <text x="10" y="65">break further: 3 * dp[7] = 3 * 12 = 36</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[10] considers 36 among all pieces</text>
  </g>
</svg>

Every piece choice is tried both ways (stop or break further), and the best across all pieces becomes `dp[a]`.

## 5. Runnable example

```java
// IntegerBreak.java
public class IntegerBreak {

    // KEY INSIGHT: maximize-product unbounded knapsack where the
    // "item list" is every integer 1..a-1 -- try each as the first
    // piece, either stopping there or breaking the remainder further.

    static int integerBreak(int n) {
        int[] dp = new int[n + 1];
        dp[1] = 1;

        for (int a = 2; a <= n; a++) {
            for (int piece = 1; piece < a; piece++) {
                int stopHere = piece * (a - piece);
                int breakFurther = piece * dp[a - piece];
                dp[a] = Math.max(dp[a], Math.max(stopHere, breakFurther));
            }
        }
        return dp[n];
    }

    public static void main(String[] args) {
        System.out.println(integerBreak(10));
        // 36
        System.out.println(integerBreak(2));
        // 1
    }
}
```

**How to run:** `java IntegerBreak.java`

## 6. Walkthrough

Trace key values building up to `integerBreak(10)`:

| a | dp[a] | best breakdown |
|---|---|---|
| 2 | 1 | 1+1 |
| 3 | 2 | 1+2 |
| 4 | 4 | 2+2 |
| 6 | 9 | 3+3 |
| 7 | 12 | 3+4 |
| 10 | 36 | 3+3+4 (piece=3, break dp[7]=12, 3*12=36) |

`dp[10] = 36`, matching `3 * 3 * 4`. Time complexity is O(n^2), since for each `a` the inner loop tries up to `a` pieces. Space is O(n).

## 7. Gotchas & takeaways

> Gotcha: `dp[1] = 1` looks like it means "the answer for `n=1` is `1`," but `n=1` is never a valid input (the problem requires `n >= 2`) — `dp[1]` exists purely as a helper value so `piece * dp[a - piece]` works cleanly when `a - piece = 1`.

- Trying BOTH `piece * (a - piece)` (stop) and `piece * dp[a - piece]` (break further) at every step is essential — always breaking further, or never breaking further, both miss the true optimum for some inputs.
- A useful shortcut once you understand the DP: the optimal breakdown never uses a piece larger than `4`, and never more than two `2`s (three `2`s are always beaten by a `2` and a `3`) — but the DP finds this without needing that number theory fact hardcoded.
- Related problems: Perfect Squares (same "try every way to split off a piece" DP shape, minimizing count instead of maximizing product), Word Break (splits a STRING instead of a number, checking reachability instead of optimizing a product).
