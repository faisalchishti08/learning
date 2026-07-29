---
card: data-structures
gi: 6
slug: common-growth-rates-constant-to-factorial
title: Common growth rates (constant to factorial)
---

## 1. What it is

A **growth rate** describes how an algorithm's work scales as input size `n` increases. There is a standard ladder of named growth rates, from slowest-growing to fastest-growing: O(1) constant, O(log n) logarithmic, O(n) linear, O(n log n) linearithmic, O(n²) quadratic, O(2ⁿ) exponential, and O(n!) factorial. Each step up this ladder represents a qualitatively different scaling behavior, not just "a bit slower."

## 2. Why & when

Knowing this ladder by name lets you instantly recognize whether an algorithm will scale to real-world input sizes, without needing to benchmark it. An O(n²) algorithm might be perfectly fine for `n=100` but completely impractical for `n=1000000`; recognizing the growth-rate class tells you this before you ever run the code.

## 3. Core concept

**The ladder, with a typical example of each:**
- **O(1) constant:** work does not depend on `n` at all. Example: array index access, `HashMap` lookup.
- **O(log n) logarithmic:** work grows very slowly — doubling `n` only adds one more unit of work. Example: binary search, balanced binary search tree operations.
- **O(n) linear:** work grows directly proportional to `n`. Example: scanning an array once, linear search.
- **O(n log n) linearithmic:** slightly worse than linear, common for efficient comparison-based sorting. Example: merge sort, heap sort, quicksort's average case.
- **O(n²) quadratic:** work grows with the square of `n` — doubling `n` quadruples the work. Example: nested loops over the same input, naive pairwise comparison, bubble sort.
- **O(2ⁿ) exponential:** work doubles with every single additional input element — becomes impractical extremely quickly. Example: naive recursive Fibonacci, brute-force subset enumeration.
- **O(n!) factorial:** the fastest-growing common class — work grows by a full multiplicative factor of `n` with every additional element. Example: brute-force traveling salesman (trying every permutation of cities).

**Why the gap between consecutive classes matters more than exact constants:** for large enough `n`, an O(n) algorithm always eventually beats an O(n²) algorithm, *regardless* of their constant factors — a highly optimized O(n²) algorithm with a tiny constant will still lose to an unoptimized O(n) algorithm once `n` grows large enough. This is precisely why growth-rate class, not raw benchmark speed at one specific `n`, is the primary lens for reasoning about scalability.

**A concrete sense of scale, for `n = 20`:** O(log n) is about `4` operations. O(n) is `20`. O(n log n) is about `86`. O(n²) is `400`. O(2ⁿ) is over a million (`1,048,576`). O(n!) is over 2 quintillion (`2,432,902,008,176,640,000`) — at `n=20`, factorial growth has already left every other class far behind, illustrating just how explosively it scales.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Growth rate curves from constant (flat) through logarithmic, linear, linearithmic, quadratic, up to exponential and factorial, all plotted together showing how quickly the higher classes dominate">
  <g font-family="sans-serif" font-size="11">
    <line x1="50" y1="170" x2="650" y2="170" stroke="#8b949e"/>
    <line x1="50" y1="170" x2="50" y2="20" stroke="#8b949e"/>
    <path d="M50,165 L650,160" stroke="#3fb950" fill="none" stroke-width="2"/>
    <text x="655" y="160" fill="#3fb950" font-size="10">O(1)</text>
    <path d="M50,165 Q300,150 650,120" stroke="#79c0ff" fill="none" stroke-width="2"/>
    <text x="655" y="120" fill="#79c0ff" font-size="10">O(log n)</text>
    <path d="M50,165 L650,60" stroke="#f0883e" fill="none" stroke-width="2"/>
    <text x="655" y="60" fill="#f0883e" font-size="10">O(n)</text>
    <path d="M50,165 Q400,80 650,30" stroke="#d29922" fill="none" stroke-width="2"/>
    <text x="655" y="30" fill="#d29922" font-size="10">O(n log n)</text>
    <path d="M50,165 Q300,60 400,25" stroke="#f85149" fill="none" stroke-width="2"/>
    <text x="405" y="20" fill="#f85149" font-size="10">O(n^2)</text>
    <path d="M50,165 Q250,160 300,20" stroke="#a371f7" fill="none" stroke-width="2"/>
    <text x="230" y="20" fill="#a371f7" font-size="10">O(2^n)</text>
  </g>
</svg>

Each class's curve climbs steeper than the one below it — exponential and factorial growth become unusable within a tiny fraction of the input range where linear and logarithmic growth remain perfectly manageable.

## 5. Runnable example

The artifact below measures actual operation counts for representative algorithms in several growth-rate classes at the same input sizes, making the scaling difference concrete.

```java
// GrowthRates.java
public class GrowthRates {

    static long linearOps(int n) {
        long count = 0;
        for (int i = 0; i < n; i++) count++;
        return count;
    }

    static long quadraticOps(int n) {
        long count = 0;
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) count++;
        }
        return count;
    }

    static long logOps(int n) {
        long count = 0;
        while (n > 1) {
            n /= 2;
            count++;
        }
        return count;
    }

    public static void main(String[] args) {
        int[] sizes = {10, 100, 1000};
        for (int n : sizes) {
            System.out.printf("n=%-5d log=%-5d linear=%-6d quadratic=%d%n",
                n, logOps(n), linearOps(n), quadraticOps(n));
        }
    }
}
```

**How to run:** save as `GrowthRates.java`, then run `java GrowthRates.java`.

## 6. Walkthrough

1. At `n=10`: `logOps` takes about `3` steps (`10 -> 5 -> 2 -> 1`), `linearOps` takes exactly `10`, `quadraticOps` takes `100` (`10 x 10`).
2. At `n=100`: `logOps` takes about `7` steps, `linearOps` takes `100`, `quadraticOps` takes `10000`.
3. At `n=1000`: `logOps` takes about `10` steps, `linearOps` takes `1000`, `quadraticOps` takes `1000000`.
4. Notice the pattern: as `n` grows by a factor of `10` each time, `logOps` barely increases at all, `linearOps` grows by the same factor of `10`, and `quadraticOps` grows by a factor of `100` — directly demonstrating each class's distinct scaling behavior on the same measured input sizes.

## 7. Gotchas & takeaways

> Gotcha: judging an algorithm's scalability from a benchmark at only one input size can be misleading — an O(n²) algorithm can appear faster than an O(n log n) algorithm at small `n` (due to smaller constant factors), but this relationship reliably inverts once `n` grows large enough; always reason about growth-rate class for scalability, and reserve raw benchmarking for comparing algorithms within the *same* class.

- The standard ladder, slowest to fastest-growing: O(1), O(log n), O(n), O(n log n), O(n²), O(2ⁿ), O(n!).
- For large enough `n`, growth-rate class always wins over constant-factor differences — an O(n) algorithm eventually beats any O(n²) algorithm, regardless of implementation details.
- Related concepts: [Big-O, Big-Theta, Big-Omega notation](0002-big-o-big-theta-big-omega-notation.md) (the notation used to express these growth-rate classes precisely), [Amortized analysis (dynamic-array doubling)](0004-amortized-analysis-dynamic-array-doubling.md) (shows how doubling — a fundamentally logarithmic-frequency event — keeps per-operation cost constant).
