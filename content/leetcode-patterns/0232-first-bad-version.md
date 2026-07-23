---
card: leetcode-patterns
gi: 232
slug: first-bad-version
title: First Bad Version
---

## 1. What it is

You have `n` versions, numbered `1` to `n`, released in order. At some unknown version, the product became bad, and every version after it is also bad. You are given an API `isBadVersion(version)` that returns `true` or `false`. Find the FIRST bad version, using as few calls to `isBadVersion` as possible. Example: `n = 5`, versions `[good, good, good, bad, bad]` → the first bad version is `4`.

## 2. Why & when

This is the clearest possible example of binary search on the answer: there is no array to index into, only a boolean predicate that is `false` for a while and then flips to `true` forever after. Use this shape whenever a problem gives you a monotonic yes/no check instead of a data structure, and asks for the exact point where the answer flips.

## 3. Core concept

**Key idea:** `isBadVersion` is monotonic — once it returns `true` for some version, it returns `true` for every later version too. That monotonic property is exactly what binary search on the answer needs: treat the version numbers `1..n` as the search range, and binary search for the smallest version where `isBadVersion` is `true`.

**Steps:**
1. Set `lo = 1`, `hi = n`.
2. While `lo < hi`: compute `mid = lo + (hi - lo) / 2`.
3. If `isBadVersion(mid)` is `true`, the first bad version is `mid` or earlier, so set `hi = mid`.
4. Otherwise, the first bad version must be later, so set `lo = mid + 1`.
5. When the loop ends, `lo == hi` is the first bad version.

**Why it is correct:** the loop condition `lo < hi` (not `lo <= hi`) together with `hi = mid` (not `mid - 1`) is deliberate: `mid` is never ruled out when `isBadVersion(mid)` is true, since `mid` itself might be the answer. `lo` only advances past versions confirmed good. The two bounds converge on exactly the first version where the flip from good to bad happens.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Versions 1 to 5, good good good bad bad, lo and hi converge on version 4">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">versions 1..5: good, good, good, bad, bad</text>
    <rect x="10" y="30" width="50" height="24" fill="#161b22" stroke="#3fb950"/><text x="35" y="47" text-anchor="middle" font-size="9">1 good</text>
    <rect x="65" y="30" width="50" height="24" fill="#161b22" stroke="#3fb950"/><text x="90" y="47" text-anchor="middle" font-size="9">2 good</text>
    <rect x="120" y="30" width="50" height="24" fill="#161b22" stroke="#3fb950"/><text x="145" y="47" text-anchor="middle" font-size="9">3 good</text>
    <rect x="175" y="30" width="50" height="24" fill="#f85149"/><text x="200" y="47" fill="#0d1117" text-anchor="middle" font-size="9">4 bad</text>
    <rect x="230" y="30" width="50" height="24" fill="#f85149"/><text x="255" y="47" fill="#0d1117" text-anchor="middle" font-size="9">5 bad</text>
    <text x="10" y="80">check mid=3: good -&gt; lo=4</text>
    <text x="10" y="100">check mid=4: bad -&gt; hi=4</text>
    <text x="10" y="120">lo == hi == 4: first bad version is 4</text>
  </g>
</svg>

The search converges exactly at the version boundary where the API flips from good to bad.

## 5. Runnable example

```java
// FirstBadVersion.java
public class FirstBadVersion {

    // Level 1 -- Brute force: call isBadVersion(1), isBadVersion(2),
    // ... in order until one returns true, and return that version.
    // Correct, but O(n) calls in the worst case, when the API is
    // usually an expensive network or build check in practice.

    // KEY INSIGHT: isBadVersion is monotonic (false...false, then
    // true...true forever), so binary search on the version range
    // finds the flip point in O(log n) calls instead of O(n).

    // Level 2 -- Optimal: binary search on the answer.
    static int firstBadVersion(int n, java.util.function.IntPredicate isBadVersion) {
        int lo = 1, hi = n;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (isBadVersion.test(mid)) hi = mid;
            else lo = mid + 1;
        }
        return lo;
    }

    // Level 3 -- Hardened: works unchanged when version 1 is already
    // bad (hi collapses to 1 immediately) or only version n is bad
    // (lo climbs all the way to n before the loop ends).

    public static void main(String[] args) {
        int n = 5;
        int firstBad = 4;
        java.util.function.IntPredicate isBadVersion = v -> v >= firstBad;

        System.out.println(firstBadVersion(n, isBadVersion));
        // 4
    }
}
```

**How to run:** `java FirstBadVersion.java`

## 6. Walkthrough

Trace `firstBadVersion(5, isBadVersion)` where the first bad version is `4`:

| lo | hi | mid | isBadVersion(mid) | action |
|---|---|---|---|---|
| 1 | 5 | 3 | false | lo = 4 |
| 4 | 5 | 4 | true | hi = 4 |
| 4 | 4 | — | loop ends (lo == hi) | return 4 |

Found in 2 calls to `isBadVersion` instead of up to 4 with a linear scan. Time complexity is O(log n) calls to the API. Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: using `lo <= hi` with `hi = mid - 1` (the plain search-on-index template) here would incorrectly skip over `mid` when it is bad, since `mid` itself could be the first bad version and must stay a candidate — this is why the answer template uses `lo < hi` and `hi = mid` instead.

- This problem is the cleanest real-world instance of "binary search on the answer": no array exists, only a monotonic predicate over a range of integers.
- Minimizing calls to `isBadVersion` matters in practice, since it usually represents an expensive check (e.g. running a real build or deployment).
- Related problems: Guess Number Higher or Lower (same monotonic-predicate shape with a three-way comparison instead of boolean), Sqrt(x) (same shape, predicate is `x*x <= n`).
