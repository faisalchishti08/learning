---
card: leetcode-patterns
gi: 233
slug: sqrt-x
title: Sqrt(x)
---

## 1. What it is

Given a non-negative integer `x`, return the integer square root of `x`, rounded down. Do not use a built-in power or square-root function. Example: `x = 8` → `2` (since `2*2=4 <= 8` but `3*3=9 > 8`).

## 2. Why & when

This is binary search on the answer with a very natural predicate: "is `guess * guess <= x`?" That predicate is monotonic — small guesses satisfy it, large guesses don't, and there is exactly one boundary where it flips. Use this shape whenever you need to find an integer answer defined by a threshold condition, without an efficient closed-form formula (or when you're told not to use one).

## 3. Core concept

**Key idea:** search over candidate answers from `0` to `x`. For each candidate `mid`, check whether `mid * mid <= x`. If it does, `mid` might be the answer (or the true answer could be even bigger), so keep it as a candidate and search higher. If it doesn't, `mid` is too big, so search lower. The largest `mid` that still satisfies `mid * mid <= x` is the floor of the square root.

**Steps:**
1. Set `lo = 0`, `hi = x`.
2. While `lo < hi`: compute `mid = lo + (hi - lo + 1) / 2` (round UP, since you are searching for the largest valid value).
3. If `mid * mid <= x`, `mid` is a valid candidate and the answer could be even higher: set `lo = mid`.
4. Otherwise, `mid` is too big: set `hi = mid - 1`.
5. When the loop ends, `lo == hi` is the floor of the square root.

**Why it is correct:** the predicate `guess * guess <= x` is true for every guess from `0` up to the true square root, and false for every guess above it — a single flip point. Binary search finds the largest `true` value directly. Rounding `mid` up (instead of down) is required here because the update `lo = mid` must make progress even when `hi - lo == 1`; rounding down would leave `mid == lo` and the loop could stall forever.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Guesses 0 to 8 for sqrt of 8, true up to 2, false from 3 onward">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">x = 8; check guess*guess &lt;= 8</text>
    <rect x="10" y="30" width="30" height="24" fill="#3fb950"/><text x="25" y="47" fill="#0d1117" text-anchor="middle" font-size="9">0</text>
    <rect x="40" y="30" width="30" height="24" fill="#3fb950"/><text x="55" y="47" fill="#0d1117" text-anchor="middle" font-size="9">1</text>
    <rect x="70" y="30" width="30" height="24" fill="#3fb950"/><text x="85" y="47" fill="#0d1117" text-anchor="middle" font-size="9">2</text>
    <rect x="100" y="30" width="30" height="24" fill="#161b22" stroke="#f85149"/><text x="115" y="47" text-anchor="middle" font-size="9">3</text>
    <text x="10" y="80">2*2=4 &lt;= 8 (true), 3*3=9 &lt;= 8 (false)</text>
    <text x="10" y="105">largest guess where the check is true: 2</text>
    <text x="10" y="130">floor(sqrt(8)) = 2</text>
  </g>
</svg>

The predicate stays true for guesses `0` through `2`, then flips to false at `3`; binary search finds that exact boundary.

## 5. Runnable example

```java
// SqrtX.java
public class SqrtX {

    // Level 1 -- Brute force: try guess = 0, 1, 2, ... increasing by
    // one, stop at the last guess where guess*guess <= x. Correct,
    // but O(sqrt(x)) guesses -- slow for large x.

    // KEY INSIGHT: "guess*guess <= x" is monotonic in guess, so binary
    // search finds the largest true guess in O(log x) steps instead
    // of a linear scan.

    // Level 2 -- Optimal: binary search on the answer, rounding mid up.
    static int mySqrt(int x) {
        if (x < 2) return x;
        int lo = 0, hi = x;
        while (lo < hi) {
            int mid = lo + (hi - lo + 1) / 2;
            if ((long) mid * mid <= x) lo = mid;
            else hi = mid - 1;
        }
        return lo;
    }

    // Level 3 -- Hardened: casts mid*mid to long before comparing, so
    // large x values (near Integer.MAX_VALUE) do not overflow int
    // during the multiplication.

    public static void main(String[] args) {
        System.out.println(mySqrt(8));
        // 2
        System.out.println(mySqrt(4));
        // 2
        System.out.println(mySqrt(0));
        // 0
    }
}
```

**How to run:** `java SqrtX.java`

## 6. Walkthrough

Trace `mySqrt(8)`, `lo = 0`, `hi = 8`:

| lo | hi | mid (round up) | mid*mid | <= 8? | action |
|---|---|---|---|---|---|
| 0 | 8 | 5 | 25 | no | hi = 4 |
| 0 | 4 | 2 | 4 | yes | lo = 2 |
| 2 | 4 | 3 | 9 | no | hi = 2 |
| 2 | 2 | — | — | loop ends | return 2 |

The result `2` matches `floor(sqrt(8)) = 2.828...`. Time complexity is O(log x). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: computing `mid * mid` as a plain `int` can overflow for large `x` (close to `Integer.MAX_VALUE`), since `mid` itself can be large — cast to `long` before multiplying to avoid a silent wraparound that breaks the comparison.

- This problem needs the "round `mid` up" variant of the answer template, since it searches for the LARGEST value where the predicate is true, not the smallest — the opposite direction from First Bad Version.
- `x < 2` is a base case (0 and 1 are their own square roots) that avoids an unnecessary search loop for trivial inputs.
- Related problems: First Bad Version (search for the smallest true value, round down), Guess Number Higher or Lower (same numeric range search, using a three-way comparison callback).
