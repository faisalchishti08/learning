---
card: leetcode-patterns
gi: 596
slug: math-geometry-signal-number-theory-matrix-manipulation-or-co
title: Math & Geometry — signal: number theory, matrix manipulation, or coordinate geometry
---

## 1. What it is

"Math & Geometry" problems have no single shared algorithm — they group problems solved by direct mathematical reasoning about numbers, digits, matrices, or coordinates, rather than by a general-purpose data structure or graph technique. What unites them is that the fastest solution usually comes from a mathematical property of the input (a digit relationship, a modular identity, a geometric fact) instead of simulation or search.

## 2. Why & when

Recognize this family whenever a problem is phrased purely in terms of numbers, digits, or 2D positions, with no graph, tree, or interval structure to exploit. These problems often *look* solvable by brute-force simulation, and often are for small inputs — the skill is spotting when a mathematical shortcut turns an O(n) or O(n^2) simulation into O(1) or O(log n).

Signals to watch for in the problem statement:

- **"Without converting to a string"** or **"without extra space"** on a number problem (Palindrome Number, Reverse Integer) — a hint that direct digit-by-digit arithmetic (`% 10`, `/ 10`) is expected instead of string manipulation.
- **Digit sums, digit roots, or repeated digit operations** ("Add Digits," "Happy Number") — often solvable with a modular-arithmetic identity, avoiding the loop entirely.
- **"Power of X" / "is a multiple of only these prime factors"** (Power of Three, Ugly Number) — number-theory questions about divisibility, often solvable by repeated division or a fixed formula, not iteration up to the value.
- **Matrix operations "in place"** (Rotate Image, Set Matrix Zeroes) — a hint that index arithmetic (swapping via transpose-then-reflect, or using the matrix's own border as scratch space) replaces allocating a second matrix.
- **Coordinates, slopes, or geometric alignment** ("Max Points on a Line") — a hint to reduce the geometry to a mathematical relationship (like a normalized slope) and count matches.

The alternative — brute-force simulation (build the full string, allocate a second matrix, check every pair) — usually still gives a *correct* answer; the mathematical shortcut is about efficiency and, often, elegance, not correctness.

## 3. Core concept

**Key idea:** before reaching for a data structure, ask what mathematical fact makes this problem's specific check easier. Three recurring facts cover most of this section:

- **Digit extraction is arithmetic, not string parsing:** `n % 10` gives the last digit; `n / 10` (integer division) drops it. Repeating this walks every digit without ever converting to a `String`.
- **Divisibility chains replace iteration:** checking "is `n` a power of `k`" by repeated division (`while n % k == 0: n /= k`, then check `n == 1`) avoids computing powers up to `n`.
- **In-place matrix transforms compose simple moves:** a 90-degree rotation is a transpose (swap `matrix[i][j]` with `matrix[j][i]`) followed by reversing each row — two well-understood O(n^2) passes, no second matrix.

**Why these are worth knowing by name:** interviewers and graders often specifically constrain space ("O(1) extra space," "without converting to a string") precisely to force you toward the mathematical identity instead of the simulation — recognizing the identity ahead of time avoids getting stuck.

## 4. Diagram

<svg viewBox="0 0 700 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three recurring math tricks: digit extraction via mod/div, divisibility via repeated division, matrix rotation via transpose plus row reversal">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="20" width="200" height="50" rx="6" fill="#161b22" stroke="#3fb950"/>
    <text x="120" y="42" fill="#e6edf3" text-anchor="middle" font-size="11">n % 10, n / 10</text>
    <text x="120" y="60" fill="#8b949e" text-anchor="middle" font-size="10">digit-by-digit, no string</text>
    <rect x="250" y="20" width="200" height="50" rx="6" fill="#161b22" stroke="#f0883e"/>
    <text x="350" y="42" fill="#e6edf3" text-anchor="middle" font-size="11">while n % k == 0: n /= k</text>
    <text x="350" y="60" fill="#8b949e" text-anchor="middle" font-size="10">divisibility, no loop to n</text>
    <rect x="480" y="20" width="200" height="50" rx="6" fill="#161b22" stroke="#79c0ff"/>
    <text x="580" y="42" fill="#e6edf3" text-anchor="middle" font-size="11">transpose + reverse rows</text>
    <text x="580" y="60" fill="#8b949e" text-anchor="middle" font-size="10">rotate in place, no 2nd matrix</text>
    <text x="350" y="120" fill="#79c0ff" text-anchor="middle">each trick trades a simulation loop or extra allocation for a direct arithmetic identity</text>
  </g>
</svg>

Each recurring trick swaps a brute-force simulation (string building, iteration up to n, allocating a second matrix) for a direct arithmetic or geometric identity.

## 5. Runnable example

The artifact below is a signal-checker: it compares a naive string-based digit check against a pure-arithmetic one, showing both agree while only one avoids extra space.

```java
// MathGeometrySignal.java
public class MathGeometrySignal {

    // Naive: converts to a string, uses extra space proportional to digit count.
    static boolean isPalindromeNaive(int n) {
        if (n < 0) return false;
        String s = String.valueOf(n);
        return s.equals(new StringBuilder(s).reverse().toString());
    }

    // Math: reverses only half the digits arithmetically, O(1) extra space.
    static boolean isPalindromeMath(int n) {
        if (n < 0 || (n % 10 == 0 && n != 0)) return false;
        int reversedHalf = 0;
        while (n > reversedHalf) {
            reversedHalf = reversedHalf * 10 + n % 10;
            n /= 10;
        }
        return n == reversedHalf || n == reversedHalf / 10;
    }

    public static void main(String[] args) {
        int[] tests = {121, 123, 12321, 10};
        for (int t : tests) {
            System.out.println(t + " -> naive=" + isPalindromeNaive(t) + ", math=" + isPalindromeMath(t));
        }
    }
}
```

**How to run:** save as `MathGeometrySignal.java`, then run `java MathGeometrySignal.java`.

## 6. Walkthrough

1. You read a problem about numbers, digits, or coordinates with no graph or interval structure — the Math & Geometry signal.
2. You check the constraints: "without converting to a string" or "O(1) extra space" both signal a pure-arithmetic approach is expected, not string manipulation.
3. For `isPalindromeMath(121)`: `reversedHalf` builds up from the last digits while `n` shrinks from the front, stopping once `n <= reversedHalf` (the midpoint). `n=1`, `reversedHalf=12`... tracing further reaches `n=1, reversedHalf=1` after processing the middle digit, and `n == reversedHalf` holds.
4. Both `isPalindromeNaive` and `isPalindromeMath` agree on every test case, confirming the arithmetic approach is correct, while only the arithmetic version avoids allocating a `String` and a `StringBuilder`.
5. This is the general Math & Geometry loop: identify the property being asked about, then find the arithmetic or geometric identity that computes it directly.

## 7. Gotchas & takeaways

> Gotcha: assuming every Math & Geometry problem needs a "clever" identity — sometimes brute-force simulation (build the string, allocate the second matrix) is perfectly acceptable and clearer, unless the problem explicitly constrains space or forbids a specific technique like string conversion.

- Signal words: "without converting to a string," "in place," "O(1) extra space," explicit mentions of digits, powers, primes, or coordinates/slopes.
- Three recurring identities: digit extraction via `% 10`/`/ 10`, divisibility via repeated division, matrix rotation via transpose-then-reverse.
- Related pattern-meta pages: [Math & Geometry — template: modular arithmetic, in-place matrix moves, line slopes](0597-math-geometry-template-modular-arithmetic-in-place-matrix-mo.md), [Math & Geometry — complexity: varies by problem](0598-math-geometry-complexity-varies-by-problem.md).
