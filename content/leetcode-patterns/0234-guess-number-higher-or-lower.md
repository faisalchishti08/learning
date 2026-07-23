---
card: leetcode-patterns
gi: 234
slug: guess-number-higher-or-lower
title: Guess Number Higher or Lower
---

## 1. What it is

A number-guessing game: a number is picked from `1` to `n`. You call `guess(num)`, which returns `-1` if the picked number is lower than `num`, `1` if it is higher, and `0` if `num` is correct. Find the picked number using as few calls as possible. Example: `n = 10`, picked number is `6` → calling `guess(6)` returns `0`.

## 2. Why & when

This is binary search on the answer with a three-way comparison instead of a boolean predicate — the classic "guess a number" game everyone has played by hand. Use this shape whenever an API tells you "too high," "too low," or "correct" instead of a plain true/false, but the underlying search is still over a single sorted range of candidates.

## 3. Core concept

**Key idea:** the range `1..n` is implicitly sorted (the picked number is a single fixed value inside it), and `guess` tells you which direction to move. This is exactly the search-on-index template, but with `guess(mid)` replacing the array comparison `nums[mid]` versus `target`.

**Steps:**
1. Set `lo = 1`, `hi = n`.
2. While `lo <= hi`: compute `mid = lo + (hi - lo) / 2`.
3. Call `result = guess(mid)`.
4. If `result == 0`, `mid` is the picked number: return it.
5. If `result == -1` (the picked number is lower than `mid`), set `hi = mid - 1`.
6. If `result == 1` (the picked number is higher than `mid`), set `lo = mid + 1`.

**Why it is correct:** `guess` gives a direct three-way comparison against the hidden picked number, exactly like comparing `nums[mid]` to `target` in plain binary search. Each call eliminates half the remaining range with certainty, so the same halving argument that makes plain binary search correct and O(log n) applies here unchanged.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Range 1 to 10, guessing 6, guess(5) returns higher, narrows to 6-10">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">n = 10, picked number = 6</text>
    <rect x="10" y="30" width="400" height="24" fill="#161b22" stroke="#30363d"/>
    <rect x="200" y="30" width="40" height="24" fill="#3fb950"/><text x="220" y="47" fill="#0d1117" text-anchor="middle" font-size="9">mid=5</text>
    <text x="10" y="80">guess(5) = 1 (picked number is higher) -&gt; lo = 6</text>
    <rect x="240" y="95" width="40" height="24" fill="#3fb950"/><text x="260" y="112" fill="#0d1117" text-anchor="middle" font-size="9">mid=6</text>
    <text x="10" y="140">guess(6) = 0 -&gt; found</text>
  </g>
</svg>

Each call to `guess` plays the same role as comparing `nums[mid]` to `target`, cutting the remaining range in half.

## 5. Runnable example

```java
// GuessNumberHigherOrLower.java
public class GuessNumberHigherOrLower {

    // Level 1 -- Brute force: call guess(1), guess(2), ... in order
    // until one returns 0. Correct, but O(n) calls in the worst case.

    // KEY INSIGHT: guess gives a three-way comparison against a fixed
    // hidden value, exactly like comparing nums[mid] to target in
    // plain binary search -- so the same halving strategy applies.

    // Level 2 -- Optimal: binary search using the three-way result.
    interface GuessApi { int guess(int num); }

    static int guessNumber(int n, GuessApi api) {
        int lo = 1, hi = n;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            int result = api.guess(mid);
            if (result == 0) return mid;
            if (result == -1) hi = mid - 1;
            else lo = mid + 1;
        }
        return -1; // guaranteed not to happen per problem constraints
    }

    // Level 3 -- Hardened: works unchanged whether the picked number
    // is at the very first guess tried, or at either extreme (1 or n).

    public static void main(String[] args) {
        int picked = 6;
        GuessApi api = num -> {
            if (num < picked) return 1;
            if (num > picked) return -1;
            return 0;
        };

        System.out.println(guessNumber(10, api));
        // 6
    }
}
```

**How to run:** `java GuessNumberHigherOrLower.java`

## 6. Walkthrough

Trace `guessNumber(10, api)` with picked number `6`:

| lo | hi | mid | guess(mid) | meaning | action |
|---|---|---|---|---|---|
| 1 | 10 | 5 | 1 | picked number is higher | lo = 6 |
| 6 | 10 | 8 | -1 | picked number is lower | hi = 7 |
| 6 | 7 | 6 | 0 | correct | return 6 |

Found in 3 calls instead of up to 6 with a linear scan. Time complexity is O(log n) calls to `guess`. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: mixing up the sign convention (`guess` returns `-1` when the picked number is LOWER, meaning you should move `hi` down, not `lo` up) is an easy off-by-direction bug — always re-derive which bound moves from the API's documented meaning, rather than assuming it matches a different problem's convention.

- This is the plain search-on-index template with the array comparison replaced by an external API call — the loop shape (`lo <= hi`, `mid ± 1`) is identical to Binary Search.
- The three-way result (`-1`, `0`, `1`) is functionally the same information as `nums[mid]` compared to `target`; only the source of the comparison changes.
- Related problems: Binary Search (identical loop structure over an explicit array), First Bad Version (a two-way version of this same idea, searching for a boundary instead of an exact match).
