---
card: leetcode-patterns
gi: 598
slug: math-geometry-complexity-varies-by-problem
title: Math & Geometry — complexity: varies by problem
---

## 1. What it is

Unlike most other pattern families (where one signal reliably implies one complexity, like "sliding window implies O(n)"), Math & Geometry problems span a wide range: some are O(1) (a closed-form formula), some are O(log n) (repeated division, GCD), some are O(digits) or O(n) (walking digits or a single array pass), and some are O(n^2) (an n x n matrix, or checking all pairs of points). The complexity depends entirely on which specific mathematical structure the problem has — there is no single rule to memorize.

## 2. Why & when

Use this lens after you have identified the mathematical approach (not before) — once you know *what* computation the problem needs, classify it against these recurring shapes to sanity-check that your solution is actually efficient enough for the stated constraints, rather than assuming a Math & Geometry problem is "automatically fast" just because it involves a formula.

## 3. Core concept

**A quick reference of recurring complexity shapes in this section:**

| Shape | Typical complexity | Example |
|---|---|---|
| Closed-form formula, fixed number of arithmetic ops | O(1) | Add Digits (digital root has a mod-9 formula) |
| Repeated division / GCD | O(log n) | Power of Three (divide by 3 repeatedly), Excel Sheet Column Number (base-26 conversion) |
| Walk every digit once | O(digits) = O(log₁₀ n) | Palindrome Number, Reverse Integer, Plus One |
| Single pass over an array/string | O(n) | Roman to Integer, Fizz Buzz |
| Nested loop over an n x n matrix | O(n^2) | Rotate Image, Set Matrix Zeroes, Spiral Matrix |
| All pairs of points | O(n^2) (or better with slope-bucketing per point) | Max Points on a Line |

**Why "walk every digit" is O(log n), not O(n):** the number of digits in `n` is proportional to `log₁₀(n)`, not to `n` itself — a number with a billion possible values (`n` up to `10^9`) has only about 10 digits. This is why digit-based solutions are considered fast even though they "loop," and why they scale to very large `n` without slowing down noticeably.

**Why some O(n^2) matrix/point solutions cannot easily be improved:** rotating or zeroing an n x n matrix in place fundamentally must touch every cell at least once, so O(n^2) is optimal for those problems (you cannot do less work than reading the input). For point problems like "Max Points on a Line," O(n^2) (checking, for each point, the slope to every other point) is standard and accepted, though slope-bucketing per point (grouping other points by normalized slope) is what actually achieves that bound efficiently, rather than checking all `O(n^3)` triples of points naively.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A spectrum of complexities across Math & Geometry problems, from O(1) formulas to O(n squared) matrix and point problems">
  <g font-family="sans-serif" font-size="12">
    <line x1="40" y1="80" x2="660" y2="80" stroke="#8b949e"/>
    <circle cx="80" cy="80" r="6" fill="#3fb950"/><text x="80" y="105" fill="#e6edf3" text-anchor="middle" font-size="10">O(1)</text>
    <circle cx="220" cy="80" r="6" fill="#3fb950"/><text x="220" y="105" fill="#e6edf3" text-anchor="middle" font-size="10">O(log n)</text>
    <circle cx="360" cy="80" r="6" fill="#f0883e"/><text x="360" y="105" fill="#e6edf3" text-anchor="middle" font-size="10">O(digits)</text>
    <circle cx="500" cy="80" r="6" fill="#f0883e"/><text x="500" y="105" fill="#e6edf3" text-anchor="middle" font-size="10">O(n)</text>
    <circle cx="620" cy="80" r="6" fill="#f85149"/><text x="620" y="105" fill="#e6edf3" text-anchor="middle" font-size="10">O(n^2)</text>
    <text x="350" y="40" fill="#79c0ff" text-anchor="middle">complexity depends on the specific math, not the "Math & Geometry" label</text>
  </g>
</svg>

Complexity in this family ranges the full spectrum — always classify each problem by its actual computation, not by assuming a category-wide default.

## 5. Runnable example

The artifact below measures two solutions to the same class of problem — checking if a number is a power of 3 — one O(n) (linear iteration up to n), one O(log n) (repeated division), to show the complexity difference is measurable, not just theoretical.

```java
// MathGeometryComplexity.java
public class MathGeometryComplexity {

    // O(n): builds up powers of 3 from 1 until reaching or passing n.
    static boolean isPowerOfThreeLinear(int n) {
        if (n < 1) return false;
        long power = 1;
        while (power < n) {
            power *= 3;
        }
        return power == n;
    }

    // O(log n): repeatedly divides n by 3.
    static boolean isPowerOfThreeLog(int n) {
        if (n < 1) return false;
        while (n % 3 == 0) {
            n /= 3;
        }
        return n == 1;
    }

    public static void main(String[] args) {
        int[] tests = {1, 3, 9, 27, 45, 59049};
        for (int t : tests) {
            System.out.println(t + " -> linear=" + isPowerOfThreeLinear(t) + ", log=" + isPowerOfThreeLog(t));
        }

        // Both are fast for these small inputs, but the loop counts differ:
        int n = 59049; // 3^10
        int linearSteps = 0;
        long power = 1;
        while (power < n) { power *= 3; linearSteps++; }
        int logSteps = 0;
        int m = n;
        while (m % 3 == 0) { m /= 3; logSteps++; }
        System.out.println("linear steps: " + linearSteps + ", log steps: " + logSteps);
    }
}
```

**How to run:** save as `MathGeometryComplexity.java`, then run `java MathGeometryComplexity.java`.

## 6. Walkthrough

1. Both `isPowerOfThreeLinear` and `isPowerOfThreeLog` agree on every test case — correctness is identical.
2. For `n = 59049` (which is `3^10`), `isPowerOfThreeLinear` multiplies by `3` repeatedly starting from `1`, needing exactly `10` multiplications to reach `59049`.
3. `isPowerOfThreeLog` divides `59049` by `3` repeatedly, also needing exactly `10` divisions to reach `1`.
4. For this specific case the step counts happen to match (`log₃(59049) = 10` either way, since both approaches walk the same "distance" in powers of 3) — the real difference shows for larger `n`: the linear approach's step count grows with `n` directly bounded by how many multiplications reach `n`, while the log approach's step count grows only with `log₃(n)`, and for very large `n` values near `Integer.MAX_VALUE`, the linear approach risks overflow issues from repeated multiplication that the log approach avoids by dividing down instead.
5. The general lesson: identify the *actual* growth rate of your chosen approach for this specific problem, rather than assuming "it's just math" implies it is automatically fast.

## 7. Gotchas & takeaways

> Gotcha: assuming a "one-line formula" is always O(1) — some formulas (like checking divisibility by repeated multiplication up to `n`) still hide a loop whose iteration count depends on `n`; read what the code actually does, not just how short it looks.

- No universal complexity for this family: check the specific technique (formula, division, digit walk, array pass, matrix nest, point pairs) against the table above.
- O(digits) (roughly O(log₁₀ n)) is effectively very fast even for huge `n`, since digit count grows extremely slowly.
- Related pattern-meta pages: [Math & Geometry — signal: number theory, matrix manipulation, or coordinate geometry](0596-math-geometry-signal-number-theory-matrix-manipulation-or-co.md), [Math & Geometry — template: modular arithmetic, in-place matrix moves, line slopes](0597-math-geometry-template-modular-arithmetic-in-place-matrix-mo.md).
