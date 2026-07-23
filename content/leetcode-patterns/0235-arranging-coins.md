---
card: leetcode-patterns
gi: 235
slug: arranging-coins
title: Arranging Coins
---

## 1. What it is

You have `n` coins, and you want to build a "staircase": row `1` has `1` coin, row `2` has `2` coins, row `3` has `3` coins, and so on. Return the number of COMPLETE rows you can build. Example: `n = 5` → `2` (row 1 uses 1 coin, row 2 uses 2 coins, totalling 3; only 2 coins remain, not enough for row 3's 3 coins).

## 2. Why & when

This is binary search on the answer where the predicate is "can `k` complete rows be built with `n` coins?" That predicate is monotonic: if `k` rows fit, every smaller number of rows also fits; if `k` rows don't fit, no larger number does either. Use this shape whenever the problem asks "how many steps/rows/items fit" under a total-resource constraint that grows predictably (here, triangularly) with the count.

## 3. Core concept

**Key idea:** the total coins needed for `k` complete rows is the sum `1 + 2 + ... + k`, which has the closed form `k * (k + 1) / 2` (the triangular number formula). Binary search over candidate row counts `k`, checking whether `k * (k + 1) / 2 <= n`, to find the largest `k` that still fits.

**Steps:**
1. Set `lo = 0`, `hi = n` (you can never need more rows than coins, since row `k` alone needs `k` coins).
2. While `lo < hi`: compute `mid = lo + (hi - lo + 1) / 2` (round up, searching for the largest valid value).
3. Compute `coinsNeeded = mid * (mid + 1) / 2` using `long` arithmetic to avoid overflow.
4. If `coinsNeeded <= n`, `mid` rows fit, and more might also fit: set `lo = mid`.
5. Otherwise, `mid` rows don't fit: set `hi = mid - 1`.
6. When the loop ends, `lo == hi` is the largest number of complete rows.

**Why it is correct:** the triangular number formula grows strictly with `k`, so "does `k` rows worth of coins fit in `n`" is monotonic — true for small `k`, false for large `k`, with exactly one flip point. Binary search finds that flip point directly, without simulating the staircase row by row.

## 4. Diagram

<svg viewBox="0 0 460 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Staircase using 1 then 2 coins for rows 1 and 2, with 2 coins left over, not enough for row 3">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">n = 5 coins</text>
    <rect x="10" y="30" width="20" height="20" fill="#3fb950"/>
    <text x="40" y="45">row 1: 1 coin used (total 1)</text>
    <rect x="10" y="55" width="20" height="20" fill="#3fb950"/><rect x="35" y="55" width="20" height="20" fill="#3fb950"/>
    <text x="65" y="70">row 2: 2 coins used (total 3)</text>
    <rect x="10" y="80" width="20" height="20" fill="#161b22" stroke="#f85149"/><rect x="35" y="80" width="20" height="20" fill="#161b22" stroke="#f85149"/><rect x="60" y="80" width="20" height="20" fill="#161b22" stroke="#f85149"/>
    <text x="90" y="95" fill="#f85149">row 3 needs 3, only 2 remain</text>
    <text x="10" y="130">complete rows: 2</text>
  </g>
</svg>

Binary search checks the triangular-number formula directly, instead of subtracting coins row by row until they run out.

## 5. Runnable example

```java
// ArrangingCoins.java
public class ArrangingCoins {

    // Level 1 -- Brute force: simulate row by row, subtracting row
    // number k from a remaining-coins counter until it would go
    // negative. Correct, but O(sqrt(n)) rows in the worst case, and
    // O(sqrt(n)) time either way since that many rows fit into n coins.

    // KEY INSIGHT: "k complete rows fit" is equivalent to the closed
    // form k*(k+1)/2 <= n, a monotonic condition in k -- so binary
    // search over k finds the answer in O(log n) instead of a
    // row-by-row simulation.

    // Level 2 -- Optimal: binary search on the answer, rounding mid up.
    static int arrangeCoins(int n) {
        int lo = 0, hi = n;
        while (lo < hi) {
            int mid = lo + (hi - lo + 1) / 2;
            long coinsNeeded = (long) mid * (mid + 1) / 2;
            if (coinsNeeded <= n) lo = mid;
            else hi = mid - 1;
        }
        return lo;
    }

    // Level 3 -- Hardened: uses long for coinsNeeded so mid*(mid+1)
    // does not overflow int when n is near Integer.MAX_VALUE.

    public static void main(String[] args) {
        System.out.println(arrangeCoins(5));
        // 2
        System.out.println(arrangeCoins(8));
        // 3
    }
}
```

**How to run:** `java ArrangingCoins.java`

## 6. Walkthrough

Trace `arrangeCoins(5)`, `lo = 0`, `hi = 5`:

| lo | hi | mid (round up) | coinsNeeded | <= 5? | action |
|---|---|---|---|---|---|
| 0 | 5 | 3 | 6 | no | hi = 2 |
| 0 | 2 | 1 | 1 | yes | lo = 1 |
| 1 | 2 | 2 | 3 | yes | lo = 2 |
| 2 | 2 | — | — | loop ends | return 2 |

The result `2` matches the manual staircase check: rows 1 and 2 use 3 coins total, and row 3 (needing 3 more) does not fit in the remaining `5 - 3 = 2` coins. Time complexity is O(log n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: computing `mid * (mid + 1)` as a plain `int` overflows for large `n` (since `mid` can be close to `n`, and the product grows quadratically) — cast to `long` before multiplying, exactly as in Sqrt(x).

- This problem is Sqrt(x)'s twin: both search for the largest `k` where a monotonic formula stays under a limit, and both need the round-up `mid` variant of the answer template.
- The closed-form triangular number formula (`k*(k+1)/2`) turns an O(sqrt(n)) simulation into an O(log n) search — recognizing the formula is the key step, before binary search even applies.
- Related problems: Sqrt(x) (identical search shape over a different monotonic formula), Find First and Last Position of Element in Sorted Array (a different flavor of "find the boundary" search).
