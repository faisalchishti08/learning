---
card: leetcode-patterns
gi: 597
slug: math-geometry-template-modular-arithmetic-in-place-matrix-mo
title: Math & Geometry — template: modular arithmetic, in-place matrix moves, line slopes
---

## 1. What it is

Three reusable, small templates that cover most Math & Geometry problems: **digit-by-digit arithmetic** (extract and rebuild numbers using `%` and `/`), **in-place matrix rotation** (transpose, then reverse each row), and **normalized slope** (reduce a direction between two points to a canonical, comparable form using the greatest common divisor, or GCD).

## 2. Why & when

Use this template whenever [the Math & Geometry signal](0596-math-geometry-signal-number-theory-matrix-manipulation-or-co.md) applies: no data structure is the star, and the fastest path is a small, direct arithmetic or geometric computation. Reach for the specific sub-template that matches the problem's shape — digits, a matrix, or coordinates.

## 3. Core concept

**Template 1 — digit-by-digit arithmetic.**
```
while (n != 0) {
    int digit = n % 10;   // extract the last digit
    n /= 10;              // drop it (integer division)
    // use digit: append to a rebuilt number, sum it, compare it, etc.
}
```
This walks every digit of `n` from least-significant to most-significant, without ever converting to a `String`. Rebuilding a number from digits reverses their order relative to extraction (`result = result * 10 + digit`), which is exactly why this template naturally reverses a number's digits as a side effect.

**Template 2 — in-place matrix rotation (90 degrees clockwise).**
```
// Step 1: transpose (swap across the main diagonal)
for i in 0..n-1:
    for j in i+1..n-1:
        swap(matrix[i][j], matrix[j][i])

// Step 2: reverse each row
for i in 0..n-1:
    reverse(matrix[i])
```
Transposing turns rows into columns; reversing each row then flips left-right — together, these two simple, well-understood passes produce a 90-degree clockwise rotation with zero extra matrix allocation.

**Template 3 — normalized slope (for collinearity/direction problems).**
```
int dx = x2 - x1, dy = y2 - y1;
int g = gcd(Math.abs(dx), Math.abs(dy));
if (g != 0) { dx /= g; dy /= g; }
// canonicalize sign: keep dx non-negative (or dy non-negative if dx==0)
if (dx < 0) { dx = -dx; dy = -dy; }
// (dx, dy) is now a unique, comparable representation of this direction
```
Two direction vectors represent the *same* line direction if and only if their normalized `(dx, dy)` pairs are equal — dividing by the GCD removes any scale difference, and fixing a sign convention removes the ambiguity between a vector and its exact opposite.

**Why GCD normalization, not floating-point slope:** computing slope as `dy / dx` (a `double`) risks floating-point precision errors when comparing many pairs, and divides by zero for vertical lines. Integer GCD normalization avoids both problems entirely, using only exact integer arithmetic.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Matrix rotation as transpose followed by row reversal, shown on a 2x2 example">
  <g font-family="sans-serif" font-size="12">
    <text x="90" y="20" fill="#8b949e" text-anchor="middle">original</text>
    <rect x="40" y="30" width="40" height="30" fill="#161b22" stroke="#30363d"/><text x="60" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <rect x="80" y="30" width="40" height="30" fill="#161b22" stroke="#30363d"/><text x="100" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <rect x="40" y="60" width="40" height="30" fill="#161b22" stroke="#30363d"/><text x="60" y="80" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <rect x="80" y="60" width="40" height="30" fill="#161b22" stroke="#30363d"/><text x="100" y="80" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <text x="280" y="20" fill="#8b949e" text-anchor="middle">after transpose</text>
    <rect x="230" y="30" width="40" height="30" fill="#161b22" stroke="#f0883e"/><text x="250" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <rect x="270" y="30" width="40" height="30" fill="#161b22" stroke="#f0883e"/><text x="290" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <rect x="230" y="60" width="40" height="30" fill="#161b22" stroke="#f0883e"/><text x="250" y="80" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <rect x="270" y="60" width="40" height="30" fill="#161b22" stroke="#f0883e"/><text x="290" y="80" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <text x="470" y="20" fill="#8b949e" text-anchor="middle">after row reversal (final)</text>
    <rect x="420" y="30" width="40" height="30" fill="#161b22" stroke="#3fb950"/><text x="440" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <rect x="460" y="30" width="40" height="30" fill="#161b22" stroke="#3fb950"/><text x="480" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <rect x="420" y="60" width="40" height="30" fill="#161b22" stroke="#3fb950"/><text x="440" y="80" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <rect x="460" y="60" width="40" height="30" fill="#161b22" stroke="#3fb950"/><text x="480" y="80" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <text x="350" y="140" fill="#79c0ff" text-anchor="middle">two simple passes, zero extra matrix allocation</text>
  </g>
</svg>

Transpose swaps entries across the diagonal; reversing each row then completes the 90-degree clockwise rotation — no second matrix is ever allocated.

## 5. Runnable example

All three templates implemented together, each demonstrated on a small example.

```java
// MathGeometryTemplate.java
import java.util.*;

public class MathGeometryTemplate {

    // Template 1: digit-by-digit arithmetic (reverses a non-negative int's digits).
    static int reverseDigits(int n) {
        int result = 0;
        while (n != 0) {
            int digit = n % 10;
            n /= 10;
            result = result * 10 + digit;
        }
        return result;
    }

    // Template 2: in-place matrix rotation, 90 degrees clockwise.
    static void rotate(int[][] matrix) {
        int n = matrix.length;
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                int tmp = matrix[i][j];
                matrix[i][j] = matrix[j][i];
                matrix[j][i] = tmp;
            }
        }
        for (int[] row : matrix) {
            for (int l = 0, r = row.length - 1; l < r; l++, r--) {
                int tmp = row[l];
                row[l] = row[r];
                row[r] = tmp;
            }
        }
    }

    // Template 3: normalized slope between two points.
    static int gcd(int a, int b) {
        return b == 0 ? a : gcd(b, a % b);
    }

    static int[] normalizedSlope(int x1, int y1, int x2, int y2) {
        int dx = x2 - x1, dy = y2 - y1;
        int g = gcd(Math.abs(dx), Math.abs(dy));
        if (g != 0) { dx /= g; dy /= g; }
        if (dx < 0 || (dx == 0 && dy < 0)) { dx = -dx; dy = -dy; }
        return new int[]{dx, dy};
    }

    public static void main(String[] args) {
        System.out.println("reverseDigits(123): " + reverseDigits(123)); // 321

        int[][] matrix = {{1, 2}, {3, 4}};
        rotate(matrix);
        System.out.println("rotated: " + Arrays.deepToString(matrix)); // [[3,1],[4,2]]

        int[] slopeA = normalizedSlope(0, 0, 2, 4);
        int[] slopeB = normalizedSlope(1, 1, 3, 5);
        System.out.println("same direction: " + Arrays.equals(slopeA, slopeB)); // true
    }
}
```

**How to run:** save as `MathGeometryTemplate.java`, then run `java MathGeometryTemplate.java`.

## 6. Walkthrough

Trace `normalizedSlope(0,0,2,4)` and `normalizedSlope(1,1,3,5)`:

1. First call: `dx = 2-0 = 2`, `dy = 4-0 = 4`. `g = gcd(2,4) = 2`. Normalize: `dx = 1`, `dy = 2`. `dx` is non-negative already. Result: `(1, 2)`.
2. Second call: `dx = 3-1 = 2`, `dy = 5-1 = 4`. `g = gcd(2,4) = 2`. Normalize: `dx = 1`, `dy = 2`. Result: `(1, 2)`.
3. Both direction vectors normalize to the identical pair `(1, 2)`, even though the raw coordinates differ — confirming the two segments point in the same direction (and, combined with a shared point, would lie on the same line).

## 7. Gotchas & takeaways

> Gotcha: normalizing only the magnitude (dividing by GCD) without also fixing a sign convention leaves `(1, 2)` and `(-1, -2)` treated as different directions, even though they represent the same line — always canonicalize the sign (for example, forcing `dx` non-negative, or `dy` non-negative when `dx == 0`) after dividing by the GCD.

- Three templates: digit arithmetic (`% 10`, `/ 10`), in-place matrix rotation (transpose then reverse rows), normalized slope (GCD-reduced direction with a fixed sign convention).
- Digit templates avoid string allocation; matrix templates avoid a second array; slope templates avoid floating-point comparison.
- Complexity: digit templates are O(digit count); matrix rotation is O(n^2) for an n x n matrix; slope normalization is O(log(min(|dx|,|dy|))) per pair, dominated by the GCD computation.
