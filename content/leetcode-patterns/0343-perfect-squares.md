---
card: leetcode-patterns
gi: 343
slug: perfect-squares
title: Perfect Squares
---

## 1. What it is

Given an integer `n`, return the LEAST number of perfect square numbers (`1, 4, 9, 16, ...`) that sum to exactly `n`. Example: `n = 12` → `3` (`4 + 4 + 4`). Example: `n = 13` → `2` (`4 + 9`).

## 2. Why & when

This is Coin Change with a twist: the "coins" are not given directly, they are the perfect squares up to `n` (`1, 4, 9, ...`), each reusable any number of times. Recognize this shape whenever a problem's "pieces" are a MATHEMATICALLY GENERATED set (squares, powers, Fibonacci numbers) rather than an explicit input array — you build the piece list yourself before running the same unbounded-knapsack minimize template.

## 3. Core concept

**Key idea:** build `dp[a]` = fewest perfect squares summing to `a`, for every `a` from `0` to `n`, treating each square `1, 4, 9, ..., k^2 <= n` as a reusable "coin."

**Steps:**
1. Create `dp[n + 1]`, filled with a large sentinel. Set `dp[0] = 0`.
2. For `a` from `1` to `n`, for each `s` such that `s = k*k` and `s <= a` (`k` from `1` while `k*k <= a`): `dp[a] = min(dp[a], dp[a - s] + 1)`.
3. Return `dp[n]`.

**Why it is correct:** any way to sum to `a` using perfect squares uses some LAST square `s`; removing it leaves an optimal way to sum to `a - s`. Trying every possible last square and taking the minimum is the same minimize-count transition as Coin Change, just with the "coin list" generated on the fly as `1, 4, 9, ...` up to `a`.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp array for n=12 built from squares 1,4,9, showing dp 12 as three fours">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">n=12; squares up to 12: 1, 4, 9</text>
    <text x="10" y="45">dp[8] = 2 (4+4)</text>
    <text x="10" y="65">dp[12] = min(dp[11]+1, dp[8]+1, dp[3]+1) = min(_, 2+1, _) = 3</text>
    <rect x="10" y="85" width="260" height="24" fill="#3fb950"/><text x="140" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[12] = 3: 4+4+4</text>
  </g>
</svg>

The square candidates (`1, 4, 9, ...`) act exactly like the coin list in Coin Change, generated instead of given.

## 5. Runnable example

```java
// PerfectSquares.java
public class PerfectSquares {

    // KEY INSIGHT: same unbounded-knapsack MINIMIZE template as Coin
    // Change, but the "coin list" is generated: every perfect square
    // 1, 4, 9, ... up to n.

    static int numSquares(int n) {
        int[] dp = new int[n + 1];
        java.util.Arrays.fill(dp, n + 1);
        dp[0] = 0;

        for (int a = 1; a <= n; a++) {
            for (int k = 1; k * k <= a; k++) {
                int square = k * k;
                dp[a] = Math.min(dp[a], dp[a - square] + 1);
            }
        }
        return dp[n];
    }

    public static void main(String[] args) {
        System.out.println(numSquares(12));
        // 3
        System.out.println(numSquares(13));
        // 2
    }
}
```

**How to run:** `java PerfectSquares.java`

## 6. Walkthrough

Trace `numSquares(13)`:

| amount a | best last square | dp[a] |
|---|---|---|
| 4 | 4 (2^2) | 1 |
| 9 | 9 (3^2) | 1 |
| 13 | 4 (dp[9]+1 = 1+1 = 2) | 2 |

`dp[13] = 2`, matching `4 + 9`. Time complexity is O(n · sqrt(n)), since the inner loop over `k` runs up to `sqrt(a)` times for each amount. Space is O(n).

## 7. Gotchas & takeaways

> Gotcha: recomputing `k * k <= a` from `k = 1` every single time inside the outer loop is correct but slightly wasteful; it is still fast enough for typical constraints (`n` up to `10^4`), since O(n · sqrt(n)) stays well under common time limits.

- Generating the "item list" from a formula (squares, powers of two) instead of reading it from input is a common Unbounded Knapsack variant — the DP shape is identical once the list exists.
- `dp[a] = min(dp[a], dp[a - square] + 1)`: the same minimize-count transition as Coin Change, applied to a different item source.
- Related problems: Coin Change (identical transition, explicit coin array instead of generated squares), Word Break (also builds `dp[a]` from smaller `dp` values, but checks reachability over string prefixes instead of minimizing a count).
