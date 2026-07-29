---
card: leetcode-patterns
gi: 617
slug: count-primes
title: Count Primes
---

## 1. What it is

Given an integer `n`, return the count of prime numbers strictly less than `n`. Example: `n=10` → `4` (the primes `2, 3, 5, 7` are all less than `10`); `n=0` or `n=1` → `0` (no primes less than `0` or `1`).

## 2. Why & when

Checking each number individually for primality (trial division up to its square root) and counting the primes works, but costs O(n * sqrt(n)) overall — too slow for large `n` (up to `5 x 10^6`). The **Sieve of Eratosthenes** is the classic number-theory algorithm for finding all primes up to a limit at once, in O(n log log n) — far faster than checking each number independently.

## 3. Core concept

**Key idea:** instead of asking "is this number prime?" for each number separately, work forward from known primes and **mark off their multiples** as composite (not prime). Any number that is never marked by this process must be prime, since it has no smaller factor other than `1` and itself.

**Steps:**
1. Create a boolean array `isComposite` of size `n`, initialized to `false` (assume everything is prime until proven otherwise).
2. For each `i` from `2` up to `sqrt(n)`: if `isComposite[i]` is still `false` (meaning `i` is prime), mark every multiple of `i` starting from `i*i` (not `2*i`) as composite: `isComposite[i*i], isComposite[i*i + i], isComposite[i*i + 2i], ...` up to `n-1`.
3. Count how many indices from `2` to `n-1` remain `false` (not marked composite) — this count is the answer.

**Why marking starts at `i*i`, not `2*i`:** any composite multiple of `i` smaller than `i*i` (like `2*i`, `3*i`, ..., `(i-1)*i`) must already have been marked by a smaller prime factor earlier in the sieve — for example, `2*i` was already marked when `i=2` was processed (as `2`'s multiple), assuming `2 < i`. Starting at `i*i` skips this redundant re-marking, which is one of the key optimizations that makes the sieve run in O(n log log n) rather than a slower bound.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sieve of Eratosthenes marking multiples of 2 then 3 as composite, leaving primes unmarked">
  <g font-family="sans-serif" font-size="11">
    <text x="350" y="20" fill="#8b949e" text-anchor="middle">numbers 2..10</text>
    <rect x="30" y="30" width="50" height="30" fill="#161b22" stroke="#3fb950"/><text x="55" y="50" fill="#e6edf3" text-anchor="middle">2</text>
    <rect x="90" y="30" width="50" height="30" fill="#161b22" stroke="#3fb950"/><text x="115" y="50" fill="#e6edf3" text-anchor="middle">3</text>
    <rect x="150" y="30" width="50" height="30" fill="#161b22" stroke="#f85149"/><text x="175" y="50" fill="#e6edf3" text-anchor="middle">4</text>
    <rect x="210" y="30" width="50" height="30" fill="#161b22" stroke="#3fb950"/><text x="235" y="50" fill="#e6edf3" text-anchor="middle">5</text>
    <rect x="270" y="30" width="50" height="30" fill="#161b22" stroke="#f85149"/><text x="295" y="50" fill="#e6edf3" text-anchor="middle">6</text>
    <rect x="330" y="30" width="50" height="30" fill="#161b22" stroke="#3fb950"/><text x="355" y="50" fill="#e6edf3" text-anchor="middle">7</text>
    <rect x="390" y="30" width="50" height="30" fill="#161b22" stroke="#f85149"/><text x="415" y="50" fill="#e6edf3" text-anchor="middle">8</text>
    <rect x="450" y="30" width="50" height="30" fill="#161b22" stroke="#f85149"/><text x="475" y="50" fill="#e6edf3" text-anchor="middle">9</text>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">green = still unmarked (prime); red = marked composite by a smaller prime's multiples</text>
  </g>
</svg>

Each prime found marks off its own multiples going forward — every remaining unmarked number was never a multiple of any smaller prime, so it must itself be prime.

## 5. Runnable example

**Level 1 — Brute force.** For each number from `2` to `n-1`, trial-divide by every integer up to its square root to check primality, counting how many pass. O(n * sqrt(n)) time — correct, but far slower for large `n`.

**KEY INSIGHT:** instead of independently testing each number's primality, propagate the *known* primes forward, marking their multiples as composite — this reuses the work done for smaller primes instead of repeating divisibility checks from scratch for every number.

**Level 2 — Optimal.** Sieve of Eratosthenes, marking multiples starting from `i*i`, O(n log log n) time, O(n) space.

**Level 3 — Hardened.** Correctly handles `n <= 2` (returns `0` immediately, since there are no primes less than `2`), and correctly bounds the outer sieve loop at `sqrt(n)` (any composite number less than `n` must have a factor at most `sqrt(n)`, so primes beyond that cannot mark anything new within range).

```java
// CountPrimes.java
public class CountPrimes {

    public static int countPrimes(int n) {
        if (n <= 2) return 0;

        boolean[] isComposite = new boolean[n];
        int count = 0;

        for (int i = 2; i < n; i++) {
            if (!isComposite[i]) {
                count++;
                if ((long) i * i < n) {
                    for (long j = (long) i * i; j < n; j += i) {
                        isComposite[(int) j] = true;
                    }
                }
            }
        }

        return count;
    }

    public static void main(String[] args) {
        System.out.println(countPrimes(10)); // 4 (2, 3, 5, 7)
        System.out.println(countPrimes(0));  // 0
        System.out.println(countPrimes(1));  // 0
    }
}
```

**How to run:** save as `CountPrimes.java`, then run `java CountPrimes.java`.

## 6. Walkthrough

Trace `countPrimes(10)` (`isComposite` array indices `0..9`):

1. `i=2`: not composite, `count=1`. Mark multiples from `4`: `isComposite[4]=true, isComposite[6]=true, isComposite[8]=true`.
2. `i=3`: not composite, `count=2`. Mark multiples from `9`: `isComposite[9]=true`.
3. `i=4`: `isComposite[4]` is `true` (already marked by `2`), skip — no counting, no marking.
4. `i=5`: not composite, `count=3`. `5*5=25 >= 10`, so no marking needed (its multiples within range would already have been marked by smaller primes).
5. `i=6,7,8,9`: `6` is composite (skip). `7` is not composite, `count=4`. `8,9` are composite (skip).

Final count: `4`, matching the primes `2, 3, 5, 7`.

## 7. Gotchas & takeaways

> Gotcha: using `int j = i * i` instead of `long j = (long) i * i` for the inner marking loop can overflow for large `i` near `sqrt(Integer.MAX_VALUE)`, wrapping to a negative or incorrect value before the loop even starts — casting to `long` for the multiplication avoids this.

- Signal: "find/count all primes up to a limit" (as opposed to testing a single number's primality) is the Sieve of Eratosthenes signal — propagate known primes forward instead of testing each number independently.
- Starting each prime's marking at `i*i` (not `2*i`) skips redundant work already done by smaller primes.
- Related problems: Ugly Number (checks divisibility by a small fixed set of primes, unrelated to sieving), Four Divisors (a related number-theory counting problem, using trial division per number rather than a sieve, since it needs each number's actual divisors, not just primality).
