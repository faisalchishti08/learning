---
card: leetcode-patterns
gi: 604
slug: power-of-three
title: Power of Three
---

## 1. What it is

Given an integer `n`, return `true` if `n` is a power of three (`n = 3^x` for some non-negative integer `x`), and `false` otherwise. Example: `n=27` → `true` (`3^3`); `n=0` → `false` (no power of `3` equals `0`); `n=45` → `false` (`45 = 9 x 5`, and `5` is not a power of `3`).

## 2. Why & when

This is a direct number-theory divisibility question: `n` is a power of `3` exactly when repeatedly dividing `n` by `3` eventually reaches exactly `1`, with no remainder at any step along the way. Constraints: `n` fits in a 32-bit signed integer, and a follow-up asks for a solution without using loops or recursion — achievable using the fact that `3` is prime and `Integer.MAX_VALUE` has a known largest power of 3 that fits.

## 3. Core concept

**Key idea:** repeatedly divide `n` by `3` as long as it divides evenly. If this process ends at exactly `1`, `n` was a power of `3`. If at any point `n` is not evenly divisible by `3` (and is not yet `1`), it cannot be a power of `3`.

**Steps (loop approach):**
1. If `n <= 0`, return `false` immediately (no non-positive number is a power of 3).
2. While `n % 3 == 0`, divide `n` by `3`.
3. After the loop, return whether `n == 1`.

**Alternative (no-loop approach), using the largest power of 3 that fits in a 32-bit int:** since `3` is a prime number, `3^x` divides `3^y` (for `x <= y`) if and only if `x <= y` — equivalently, `n` (itself a power of `3`) must be a divisor of the **largest power of 3 that fits in an int**, `3^19 = 1162261467` (since `3^20` overflows a 32-bit signed integer). So checking `1162261467 % n == 0` (for positive `n`) directly answers the question in O(1), no loop needed.

**Why the no-loop trick only works because 3 is prime:** if `n` divides `3^19` evenly, the only factors `n` can have are powers of `3` (since `3` has no other prime factors) — so `n` itself must be some `3^x` with `x <= 19`. This would not work for a non-prime base, since a composite base's largest fitting power could be evenly divided by numbers that are *not* themselves powers of that base.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Repeated division by 3 for n=27, ending exactly at 1, confirming it is a power of 3">
  <g font-family="sans-serif" font-size="12">
    <rect x="30" y="30" width="60" height="35" fill="#161b22" stroke="#30363d"/><text x="60" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">27</text>
    <rect x="130" y="30" width="60" height="35" fill="#161b22" stroke="#30363d"/><text x="160" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">9</text>
    <rect x="230" y="30" width="60" height="35" fill="#161b22" stroke="#30363d"/><text x="260" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <rect x="330" y="30" width="60" height="35" fill="#161b22" stroke="#3fb950"/><text x="360" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <line x1="90" y1="47" x2="130" y2="47" stroke="#8b949e" marker-end="url(#a12)"/>
    <line x1="190" y1="47" x2="230" y2="47" stroke="#8b949e" marker-end="url(#a12)"/>
    <line x1="290" y1="47" x2="330" y2="47" stroke="#8b949e" marker-end="url(#a12)"/>
    <defs><marker id="a12" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
    <text x="360" y="90" fill="#79c0ff" text-anchor="middle">each step divides by 3 exactly, landing on 1 - confirms power of 3</text>
  </g>
</svg>

Each division either lands cleanly (no remainder) or fails — reaching exactly `1` after only clean divisions confirms `n` had no prime factor other than `3`.

## 5. Runnable example

**Level 1 — Brute force.** Compute successive powers of `3` (`1, 3, 9, 27, ...`) upward until reaching or exceeding `n`, then compare. O(log₃ n) time, similar cost to the division approach but building up instead of dividing down.

**KEY INSIGHT:** because `3` is prime, `n` is a power of `3` exactly when repeated exact division by `3` reaches `1` — and, further, since `3^19` is the largest power of `3` fitting in a 32-bit int, checking whether `n` evenly divides `3^19` answers the question in true O(1), with no loop at all.

**Level 2 — Optimal.** Repeated division by `3`, checking for a zero remainder at each step, O(log₃ n) time, O(1) space.

**Level 3 — Hardened.** The no-loop O(1) variant, using the precomputed largest power of `3` that fits in an `int`, plus correct handling of `n <= 0`.

```java
// PowerOfThree.java
public class PowerOfThree {

    // Level 2: repeated division.
    static boolean isPowerOfThreeLoop(int n) {
        if (n <= 0) return false;
        while (n % 3 == 0) {
            n /= 3;
        }
        return n == 1;
    }

    // Level 3: O(1), no loop - relies on 3 being prime and 3^19 being the largest fitting power.
    static boolean isPowerOfThreeNoLoop(int n) {
        return n > 0 && 1162261467 % n == 0; // 1162261467 == 3^19
    }

    public static void main(String[] args) {
        int[] tests = {27, 0, 45, 1, 3};
        for (int n : tests) {
            System.out.println(n + " -> loop=" + isPowerOfThreeLoop(n) + ", noLoop=" + isPowerOfThreeNoLoop(n));
        }
    }
}
```

**How to run:** save as `PowerOfThree.java`, then run `java PowerOfThree.java`.

## 6. Walkthrough

Dry-run `isPowerOfThreeLoop(45)`:

| step | n | n % 3 | action |
|---|---|---|---|
| start | 45 | 0 | divide: n=15 |
| iter 1 | 15 | 0 | divide: n=5 |
| iter 2 | 5 | 2 | stop, remainder nonzero |

Loop stops with `n=5`, `n % 3 != 0`. Return `n == 1`? `5 == 1` is `false`. Correctly reports `45` is not a power of `3`, since `45 = 3^2 x 5`, and `5` is not itself a power of `3`.

## 7. Gotchas & takeaways

> Gotcha: forgetting the `n <= 0` check lets `0` slip into the loop, where `0 % 3 == 0` is always true, causing an infinite loop (`0 / 3` stays `0` forever) — always reject non-positive `n` before entering the division loop.

- Signal: "is n a power of k" for a small fixed `k` is the repeated-exact-division-by-k signal; for `k` prime, it also enables the O(1) largest-fitting-power-divisibility trick.
- The O(1) trick only works because `3` is prime — it generalizes to any prime base, but not directly to composite bases.
- Related problems: Power of Two (the same idea, but base 2 has an even simpler O(1) bitwise check: `n > 0 && (n & (n-1)) == 0`), Ugly Number (checks divisibility by several small primes at once, 2, 3, and 5).
