---
card: leetcode-patterns
gi: 249
slug: maximum-number-of-removable-characters
title: Maximum Number of Removable Characters
---

## 1. What it is

Given a string `s`, a string `p` that is a subsequence of `s`, and an array `removable` listing indices into `s` in the order they may be removed, find the MAXIMUM number `k` such that removing the first `k` indices in `removable` from `s` still leaves `p` as a subsequence of the result. Example: `s = "abcacb"`, `p = "ab"`, `removable = [3,1,0]` → `2` (removing indices `3` and `1` still leaves `p` a subsequence; removing index `0` too would not).

## 2. Why & when

Removing MORE characters can only make it harder (or equally hard) to keep `p` as a subsequence, never easier — a clean monotonic relationship. Use this shape whenever a problem asks for the maximum count of some destructive or restrictive operation that still satisfies a condition, and doing more of the operation never helps satisfy that condition.

## 3. Core concept

**Key idea:** define `isSubsequenceAfterRemoving(k)`: mark the first `k` indices from `removable` as removed, then check whether `p` is still a subsequence of `s` with those positions skipped. This check is monotonic — if it is true for some `k`, it is true for every smaller `k` too (removing fewer characters is always at least as safe). Binary search over `k` from `0` to `removable.length` for the LARGEST value where the check is still true.

**Steps:**
1. Set `lo = 0`, `hi = removable.length`.
2. While `lo < hi`: compute `mid = lo + (hi - lo + 1) / 2` (round up, searching for the largest valid value).
3. Build a boolean array marking the first `mid` indices from `removable` as removed.
4. Check if `p` is still a subsequence of `s` (walking `s` left to right, skipping removed positions, matching characters of `p` in order).
5. If `p` is still a subsequence, `mid` removals are safe, and more might also be safe: set `lo = mid`.
6. Otherwise, set `hi = mid - 1`.
7. When the loop ends, `lo == hi` is the maximum safe number of removals.

**Why it is correct:** "is `p` still a subsequence after removing the first `k` indices" is false for all `k` above some threshold and true for all `k` at or below it, because removing strictly more characters (a superset of removed positions) can never turn a failed subsequence check back into a success. Binary search finds that exact threshold — the largest `k` where the check still passes.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="s=abcacb, p=ab, removable = 3,1,0, k=2 removes indices 3 and 1, p still a subsequence">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s = "abcacb", p = "ab", removable = [3,1,0]</text>
    <rect x="10" y="30" width="30" height="24" fill="#3fb950"/><text x="25" y="47" fill="#0d1117" text-anchor="middle" font-size="9">a</text>
    <rect x="40" y="30" width="30" height="24" fill="#161b22" stroke="#f85149"/><text x="55" y="47" text-anchor="middle" font-size="9">b(rm)</text>
    <rect x="70" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="85" y="47" text-anchor="middle" font-size="9">c</text>
    <rect x="100" y="30" width="30" height="24" fill="#161b22" stroke="#f85149"/><text x="115" y="47" text-anchor="middle" font-size="9">a(rm)</text>
    <rect x="130" y="30" width="30" height="24" fill="#161b22" stroke="#30363d"/><text x="145" y="47" text-anchor="middle" font-size="9">c</text>
    <rect x="160" y="30" width="30" height="24" fill="#3fb950"/><text x="175" y="47" fill="#0d1117" text-anchor="middle" font-size="9">b</text>
    <text x="10" y="80">k=2 removes indices 1 and 3; remaining "a_c_cb" still has "ab" as subsequence</text>
    <text x="10" y="105">k=3 also removes index 0 ("a"); "ab" is no longer a subsequence</text>
  </g>
</svg>

Each candidate `k` marks a growing set of removed positions; the check flips from true to false exactly once as `k` increases.

## 5. Runnable example

```java
// MaximumNumberOfRemovableCharacters.java
public class MaximumNumberOfRemovableCharacters {

    // Level 1 -- Brute force: try k = 0, 1, 2, ... increasing by one,
    // rebuilding the removed-set and re-checking the subsequence each
    // time, stopping at the last k that still works. Correct, but
    // O(removable.length * |s|) in the worst case, checking every k.

    // KEY INSIGHT: "p is still a subsequence after removing the first
    // k indices" is monotonic in k (true, true, ..., false, false),
    // so binary search over k finds the maximum safe count directly.

    // Level 2 -- Optimal: binary search on the answer.
    static int maximumRemovals(String s, String p, int[] removable) {
        int lo = 0, hi = removable.length;
        while (lo < hi) {
            int mid = lo + (hi - lo + 1) / 2;
            if (isSubsequenceAfterRemoving(s, p, removable, mid)) lo = mid;
            else hi = mid - 1;
        }
        return lo;
    }

    static boolean isSubsequenceAfterRemoving(String s, String p, int[] removable, int k) {
        boolean[] removed = new boolean[s.length()];
        for (int i = 0; i < k; i++) removed[removable[i]] = true;

        int j = 0; // pointer into p
        for (int i = 0; i < s.length() && j < p.length(); i++) {
            if (!removed[i] && s.charAt(i) == p.charAt(j)) j++;
        }
        return j == p.length();
    }

    // Level 3 -- Hardened: works unchanged when k=0 (nothing removed,
    // must always succeed since p is guaranteed a subsequence of s to
    // start with) and when k=removable.length (every listed index
    // removed, the strictest possible check).

    public static void main(String[] args) {
        System.out.println(maximumRemovals("abcacb", "ab", new int[]{3, 1, 0}));
        // 2
    }
}
```

**How to run:** `java MaximumNumberOfRemovableCharacters.java`

## 6. Walkthrough

Trace `maximumRemovals("abcacb", "ab", [3,1,0])`, `lo=0, hi=3`:

| lo | hi | mid (round up) | removed indices | "ab" still subsequence? | action |
|---|---|---|---|---|---|
| 0 | 3 | 2 | {3, 1} | yes ("a_c_cb" has a...b) | lo = 2 |
| 2 | 3 | 3 | {3, 1, 0} | no (index 0's 'a' gone, no 'a' before the remaining 'b') | hi = 2 |
| 2 | 2 | — | — | loop ends | return 2 |

The maximum safe removal count `2` matches the expected answer. Time complexity is O(|s| · log(removable.length)), since each check scans `s` once and the search runs O(log(removable.length)) times. Space is O(|s|) for the removed-marker array.

## 7. Gotchas & takeaways

> Gotcha: rebuilding the `removed` boolean array from scratch on every check (as shown here) is simple and correct, but for very large inputs, you could instead pass the current `k` as a threshold and check `removableIndex < k` directly using a precomputed rank array, avoiding repeated allocation — a valid optimization to mention if pressed on performance.

- This is binary search on the answer where the "resource" being consumed is removal budget, and the monotonic predicate is a subsequence check rather than a numeric comparison.
- The round-up `mid` (searching for the largest true value) matches the same pattern as Sqrt(x) and Arranging Coins — any "maximum k that still satisfies a shrinking condition" problem uses this variant.
- Related problems: Sqrt(x) (same round-up search shape, a numeric formula instead of a subsequence check), Successful Pairs of Spells and Potions (a different per-item binary search, run many times).
