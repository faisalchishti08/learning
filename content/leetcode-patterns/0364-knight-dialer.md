---
card: leetcode-patterns
gi: 364
slug: knight-dialer
title: Knight Dialer
---

## 1. What it is

A chess knight sits on a phone keypad (digits `0`-`9` arranged in the standard 3-row layout). Starting on any digit, the knight makes `n - 1` valid knight moves (hops), pressing the digit it lands on each time. Return the NUMBER OF DISTINCT PHONE NUMBERS of length `n` this can dial, modulo `10^9 + 7`. Example: `n = 2` → `20` (each of the 10 starting digits has some number of valid knight moves; summing them gives `20`).

## 2. Why & when

Like Count Vowels Permutation, this is a small-alphabet transition-rule DP — here the "alphabet" is the 10 keypad digits, and the "transition rule" is which digits a knight can jump to from each digit. Use this shape whenever a problem counts sequences built by repeatedly moving between a small, FIXED set of states according to a graph of allowed transitions.

## 3. Core concept

**Key idea:** track `dp[i][d]` = the number of length-`i` sequences ENDING on digit `d`, for each of the 10 digits, built from the previous length's counts at each digit's NEIGHBORS (the digits a knight could have jumped FROM to land on `d` — knight moves are symmetric, so "can jump to" and "can jump from" use the same neighbor list).

**Steps:**
1. Define the neighbor list for each digit (the digits a knight can reach in one move from it): `0->[4,6]`, `1->[6,8]`, `2->[7,9]`, `3->[4,8]`, `4->[0,3,9]`, `5->[]`, `6->[0,1,7]`, `7->[2,6]`, `8->[1,3]`, `9->[2,4]`.
2. Base case: `dp[1][d] = 1` for every digit `d` (a length-1 number is just that starting digit, one way each).
3. For `i` from `2` to `n`, for each digit `d`: `dp[i][d] = sum of dp[i-1][neighbor]` over every `neighbor` in `d`'s neighbor list.
4. Return the sum of `dp[n][d]` over all 10 digits, modulo `10^9 + 7`.

**Why it is correct:** a length-`i` sequence ending on digit `d` is exactly a length-`(i-1)` sequence ending on some digit the knight could have jumped FROM, with one more hop onto `d`. Since knight moves are reversible (if the knight can jump from `a` to `b`, it can also jump from `b` to `a`), the same neighbor list works for building the count both ways.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp for digit 0 at length 2 summing counts from its neighbors 4 and 6 at length 1">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">digit 0's neighbors: {4, 6}</text>
    <text x="10" y="45">dp[1][4]=1, dp[1][6]=1</text>
    <text x="10" y="65">dp[2][0] = dp[1][4] + dp[1][6] = 1 + 1 = 2</text>
    <rect x="10" y="85" width="240" height="24" fill="#3fb950"/><text x="130" y="102" fill="#0d1117" text-anchor="middle" font-size="10">2 length-2 numbers ending on 0: "40","60"</text>
  </g>
</svg>

Each digit's count sums the previous length's counts across exactly its knight-move neighbors.

## 5. Runnable example

```java
// KnightDialer.java
public class KnightDialer {

    static final int MOD = 1_000_000_007;
    static final int[][] NEIGHBORS = {
        {4, 6}, {6, 8}, {7, 9}, {4, 8}, {0, 3, 9},
        {}, {0, 1, 7}, {2, 6}, {1, 3}, {2, 4}
    };

    // KEY INSIGHT: a fixed transition graph (knight moves on a keypad)
    // over 10 states -- same rolling-array template as Count Vowels
    // Permutation, generalized to more states via a neighbor list.

    static int knightDialer(int n) {
        long[] dp = new long[10];
        java.util.Arrays.fill(dp, 1);

        for (int step = 2; step <= n; step++) {
            long[] next = new long[10];
            for (int d = 0; d < 10; d++) {
                for (int neighbor : NEIGHBORS[d]) {
                    next[d] = (next[d] + dp[neighbor]) % MOD;
                }
            }
            dp = next;
        }

        long total = 0;
        for (long count : dp) total = (total + count) % MOD;
        return (int) total;
    }

    public static void main(String[] args) {
        System.out.println(knightDialer(2));
        // 20
        System.out.println(knightDialer(1));
        // 10
    }
}
```

**How to run:** `java KnightDialer.java`

## 6. Walkthrough

Trace `knightDialer(2)`:

| digit d | neighbors | dp[2][d] |
|---|---|---|
| 0 | 4,6 | 1+1=2 |
| 1 | 6,8 | 1+1=2 |
| 2 | 7,9 | 1+1=2 |
| 3 | 4,8 | 1+1=2 |
| 4 | 0,3,9 | 1+1+1=3 |
| 5 | (none) | 0 |
| 6 | 0,1,7 | 1+1+1=3 |
| 7 | 2,6 | 1+1=2 |
| 8 | 1,3 | 1+1=2 |
| 9 | 2,4 | 1+1=2 |

Sum: `2+2+2+2+3+0+3+2+2+2 = 20`, matching the expected answer. Time complexity is O(n) (each step visits at most 10 digits, each with at most 3 neighbors — constant work per step). Space is O(1) extra (fixed-size arrays of length 10).

## 7. Gotchas & takeaways

> Gotcha: digit `5` has NO valid knight moves (it sits in the center of the keypad), so `dp[i][5] = 0` for every `i > 1` — forgetting to give it an empty neighbor list (instead of omitting it entirely) would cause an array index error.

- Encoding the transition graph as a neighbor-list array (indexed by state) is the general technique for small, fixed-alphabet transition DP — the SAME shape as Count Vowels Permutation, just with more states and neighbors read from a lookup table instead of hardcoded per-vowel formulas.
- Building `next` into a FRESH array each step (rather than updating `dp` in place) avoids reading a value that was already updated for the current step.
- Related problems: Count Vowels Permutation (identical DP shape, 5 states instead of 10), N-th Tribonacci Number (a single-state version of the same "sum over a fixed set of prior states" idea).
