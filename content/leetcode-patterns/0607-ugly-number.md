---
card: leetcode-patterns
gi: 607
slug: ugly-number
title: Ugly Number
---

## 1. What it is

Given an integer `n`, return `true` if `n` is an **ugly number** — a positive integer whose only prime factors are `2`, `3`, and `5` — and `false` otherwise. Example: `n=6` → `true` (`6 = 2 x 3`); `n=8` → `true` (`8 = 2^3`); `n=14` → `false` (`14 = 2 x 7`, and `7` is not `2`, `3`, or `5`); `n=1` is considered ugly by convention (an empty product of allowed primes).

## 2. Why & when

This extends [Power of Three](0604-power-of-three)'s "repeated exact division" idea to **three** primes at once instead of one: strip out every factor of `2`, then every factor of `3`, then every factor of `5`. If what remains after all three passes is exactly `1`, the original number had no other prime factors, so it is ugly.

## 3. Core concept

**Key idea:** repeatedly divide `n` by each of `2`, `3`, and `5` for as long as it divides evenly, one prime at a time. After exhausting all factors of `2`, then all factors of `3`, then all factors of `5`, whatever value of `n` remains reflects any *other* prime factors it had. If that remainder is `1`, no other prime factors existed.

**Steps:**
1. If `n <= 0`, return `false` (ugly numbers are defined as positive).
2. While `n % 2 == 0`, divide `n` by `2`.
3. While `n % 3 == 0`, divide `n` by `3`.
4. While `n % 5 == 0`, divide `n` by `5`.
5. Return whether `n == 1` after all three passes.

**Why processing one prime completely before moving to the next is correct, rather than interleaving the checks:** each `while` loop for a given prime removes *every* occurrence of that prime factor from `n`'s factorization before moving on — the order among the three primes does not matter for correctness (any order fully strips all factors of `2`, `3`, and `5` eventually), only that each prime's loop runs to completion (fully exhausts that factor) before the final check, so no factor of `2`, `3`, or `5` is left behind to incorrectly cause a `false` result.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Stripping factors of 2, then 3, then 5 from 300, ending at 1, confirming it is ugly">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="30" width="80" height="35" fill="#161b22" stroke="#30363d"/><text x="60" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">300</text>
    <rect x="140" y="30" width="80" height="35" fill="#161b22" stroke="#3fb950"/><text x="180" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">/2/2=75</text>
    <rect x="260" y="30" width="80" height="35" fill="#161b22" stroke="#f0883e"/><text x="300" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">/3=25</text>
    <rect x="380" y="30" width="80" height="35" fill="#161b22" stroke="#79c0ff"/><text x="420" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">/5/5=1</text>
    <line x1="100" y1="47" x2="140" y2="47" stroke="#8b949e" marker-end="url(#a15)"/>
    <line x1="220" y1="47" x2="260" y2="47" stroke="#8b949e" marker-end="url(#a15)"/>
    <line x1="340" y1="47" x2="380" y2="47" stroke="#8b949e" marker-end="url(#a15)"/>
    <defs><marker id="a15" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">300 = 2^2 x 3 x 5^2, fully consumed by the three passes -&gt; ugly</text>
  </g>
</svg>

Each pass strips one prime's factors completely — reaching exactly `1` after all three passes proves no other prime factor was hiding in the number.

## 5. Runnable example

**Level 1 — Brute force.** Factor `n` completely using trial division by every integer from `2` up to `sqrt(n)`, collecting all distinct prime factors, then check that the set of factors is a subset of `{2, 3, 5}`. Correct, but does far more work than necessary — full factorization is not needed, only confirming the *absence* of any factor outside `{2,3,5}`.

**KEY INSIGHT:** you do not need to find every prime factor of `n` — you only need to strip out all factors of `2`, `3`, and `5` and check what is left. If the leftover is `1`, no other prime factor could have existed; any other value proves one did, without needing to identify what it is.

**Level 2 — Optimal.** Three sequential `while` loops, one per allowed prime, O(log n) time total (each loop divides `n` down, so total divisions are bounded by `log₂ n`).

**Level 3 — Hardened.** Correctly rejects `n <= 0` up front (ugly numbers are positive by definition), and correctly handles `n = 1` (no loop divides it further, and the final check `n == 1` passes directly).

```java
// UglyNumber.java
public class UglyNumber {

    public static boolean isUgly(int n) {
        if (n <= 0) return false;

        for (int prime : new int[]{2, 3, 5}) {
            while (n % prime == 0) {
                n /= prime;
            }
        }

        return n == 1;
    }

    public static void main(String[] args) {
        System.out.println(isUgly(6));  // true, 2 x 3
        System.out.println(isUgly(8));  // true, 2^3
        System.out.println(isUgly(14)); // false, 2 x 7
        System.out.println(isUgly(1));  // true, by convention
    }
}
```

**How to run:** save as `UglyNumber.java`, then run `java UglyNumber.java`.

## 6. Walkthrough

Dry-run `isUgly(14)`:

| prime | n before | divisions | n after |
|---|---|---|---|
| 2 | 14 | 14/2=7 (7%2 != 0, stop) | 7 |
| 3 | 7 | 7%3 != 0, no division | 7 |
| 5 | 7 | 7%5 != 0, no division | 7 |

After all three passes, `n = 7`, not `1`. Return `false` — correctly identifying that `14 = 2 x 7` has the disallowed prime factor `7` remaining after stripping out its single factor of `2`.

## 7. Gotchas & takeaways

> Gotcha: forgetting the `n <= 0` check lets `0` reach the loops, where `0 % prime == 0` is always true for every prime, causing an infinite loop (dividing `0` by anything stays `0`) — always reject non-positive `n` before the stripping loops.

- Signal: "is n's factorization limited to a small fixed set of primes" is the repeated-division-per-prime signal, a direct extension of the single-prime "power of k" check.
- Processing each prime to full completion (with its own `while` loop) before moving to the next is what guarantees no factor is missed, regardless of the order primes are tried in.
- Related problems: Power of Three (the single-prime version of this same technique), Ugly Number II (finds the n-th ugly number in sequence, needing a different generative approach — a min-heap or three-pointer merge — rather than checking one given number).
