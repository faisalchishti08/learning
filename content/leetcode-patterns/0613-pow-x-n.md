---
card: leetcode-patterns
gi: 613
slug: pow-x-n
title: Pow(x, n)
---

## 1. What it is

Implement `pow(x, n)`, computing `x` raised to the integer power `n`, where `n` can be negative (meaning `1 / x^(-n)`). Example: `x=2.0, n=10` → `1024.0`; `x=2.0, n=-2` → `0.25`; `x=2.1, n=3` → `9.261`.

## 2. Why & when

The naive approach — multiply `x` by itself `n` times in a loop — is O(n), which is too slow for large `n` (up to `2^31 - 1` or as negative as `-2^31`). The mathematical shortcut, **exponentiation by squaring**, computes the same result in O(log n) by repeatedly squaring the base and halving the exponent, using the identity `x^n = (x^2)^(n/2)` (for even `n`) or `x * (x^2)^((n-1)/2)` (for odd `n`).

## 3. Core concept

**Key idea:** to compute `x^n`, recursively (or iteratively) compute `x^(n/2)` once, then square that single result — instead of computing `x^(n/2)` as two *separate* recursive calls (which would cost O(n) again due to redundant work), reusing the one computed value cuts the problem size in half at each step, giving O(log n) total multiplications.

**Steps (iterative, avoids recursion overhead):**
1. If `n < 0`, convert the problem to `1 / x^(-n)` — but be careful: negating `Integer.MIN_VALUE` overflows a 32-bit int, so promote `n` to a `long` before negating.
2. Initialize `result = 1.0` and treat `n` as its absolute value from here on.
3. While `n > 0`: if `n` is odd (`n % 2 == 1`), multiply `result *= x` (peel off one factor of `x`) and decrement `n` by `1`. Then square the base: `x *= x`, and halve the exponent: `n /= 2`.
4. Return `result` (or `1 / result` if the original `n` was negative).

**Why squaring the base and halving the exponent is safe, even though it "changes what x means" partway through:** the invariant `result * x^n` (using the *current* values of `result`, `x`, and `n` at any point in the loop) always equals the original `x^n_original`. Each loop iteration preserves this invariant exactly: squaring `x` while halving `n` leaves `x^n` unchanged (`(x^2)^(n/2) = x^n`), and peeling off a factor into `result` when `n` is odd also preserves it (`x * x^(n-1) = x^n`). This invariant is what guarantees the final `result` is correct once `n` reaches `0`.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Computing 2^10 via exponentiation by squaring: base squares while exponent halves, four iterations instead of ten multiplications">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="30" width="120" height="35" fill="#161b22" stroke="#30363d"/><text x="80" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">x=2,n=10</text>
    <rect x="180" y="30" width="120" height="35" fill="#161b22" stroke="#30363d"/><text x="240" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">x=4,n=5</text>
    <rect x="340" y="30" width="120" height="35" fill="#161b22" stroke="#30363d"/><text x="400" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">x=16,n=2</text>
    <rect x="500" y="30" width="120" height="35" fill="#161b22" stroke="#3fb950"/><text x="560" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">x=256,n=0</text>
    <line x1="140" y1="47" x2="180" y2="47" stroke="#8b949e" marker-end="url(#a17)"/>
    <line x1="300" y1="47" x2="340" y2="47" stroke="#8b949e" marker-end="url(#a17)"/>
    <line x1="460" y1="47" x2="500" y2="47" stroke="#8b949e" marker-end="url(#a17)"/>
    <defs><marker id="a17" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">4 iterations (log2(10)~4) instead of 10 sequential multiplications</text>
  </g>
</svg>

The exponent halves every iteration while the base squares — the number of iterations grows only logarithmically with `n`, not linearly.

## 5. Runnable example

**Level 1 — Brute force.** Multiply `result *= x` in a loop running `n` times (or `-n` times for negative `n`, then invert). O(n) time — correct, but far too slow for `n` near `2^31`.

**KEY INSIGHT:** since `x^n = (x^2)^(n/2)`, computing `x^(n/2)` once and squaring it avoids the redundant work of computing it twice — this halves the problem size at every step, turning O(n) sequential multiplications into O(log n).

**Level 2 — Optimal.** Iterative exponentiation by squaring, O(log n) time, O(1) space.

**Level 3 — Hardened.** Correctly promotes `n` to `long` before negating, avoiding overflow when `n == Integer.MIN_VALUE` (whose absolute value does not fit in a 32-bit `int`).

```java
// PowXN.java
public class PowXN {

    public static double myPow(double x, int n) {
        long exponent = n; // promote before negating, to avoid overflow at Integer.MIN_VALUE
        if (exponent < 0) {
            x = 1 / x;
            exponent = -exponent;
        }

        double result = 1.0;
        while (exponent > 0) {
            if (exponent % 2 == 1) {
                result *= x;
                exponent--;
            }
            x *= x;
            exponent /= 2;
        }
        return result;
    }

    public static void main(String[] args) {
        System.out.println(myPow(2.0, 10)); // 1024.0
        System.out.println(myPow(2.0, -2)); // 0.25
        System.out.println(myPow(2.1, 3));  // 9.261
    }
}
```

**How to run:** save as `PowXN.java`, then run `java PowXN.java`.

## 6. Walkthrough

Dry-run `myPow(2.0, 10)`, tracing each loop iteration in order:

| iteration | exponent (start) | odd? | result update | x update | exponent (end) |
|---|---|---|---|---|---|
| 1 | 10 | no | result stays 1 | x: 2 -> 4 | 5 |
| 2 | 5 | yes | result: 1*4=4; exponent->4 | x: 4 -> 16 | 2 |
| 3 | 2 | no | result stays 4 | x: 16 -> 256 | 1 |
| 4 | 1 | yes | result: 4*256=1024; exponent->0 | x: 256 -> 65536 | 0 |

Loop ends (`exponent=0`). Return `result=1024.0`, matching `2^10`. Only 4 iterations were needed instead of 10 sequential multiplications.

## 7. Gotchas & takeaways

> Gotcha: negating `n` directly with `exponent = -n` when `n` is still an `int` overflows for `n == Integer.MIN_VALUE` (`-(-2147483648)` does not fit in a 32-bit `int`) — promoting `n` to a `long` *before* negating avoids this specific edge case.

- Signal: "compute x raised to a large integer power efficiently" is the exponentiation-by-squaring signal, achieving O(log n) instead of O(n).
- The core identity, `x^n = (x^2)^(n/2)`, halves the exponent every step by computing the halved power only once and squaring it, rather than computing it redundantly twice.
- Related problems: Sqrt(x) (a related numeric-approximation problem, though usually solved with binary search rather than exponentiation by squaring), Super Pow (an extension using modular exponentiation for very large exponents represented as an array of digits).
