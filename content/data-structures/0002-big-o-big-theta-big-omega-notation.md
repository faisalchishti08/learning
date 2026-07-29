---
card: data-structures
gi: 2
slug: big-o-big-theta-big-omega-notation
title: Big-O, Big-Theta, Big-Omega notation
---

## 1. What it is

**Big-O (O)**, **Big-Theta (Θ)**, and **Big-Omega (Ω)** are three related notations that describe how an algorithm's running time (or space use) grows as input size grows, ignoring constant factors and lower-order terms. Big-O describes an **upper bound** ("this algorithm never does more work than this, for large inputs"). Big-Omega describes a **lower bound** ("this algorithm never does less work than this"). Big-Theta describes a **tight bound** — both an upper and lower bound that match, meaning the algorithm's growth rate is exactly this rate, not just bounded by it.

## 2. Why & when

Use these notations whenever comparing algorithms independent of hardware speed, compiler optimizations, or a specific input size — they capture how an algorithm *scales*, which matters far more than a one-time benchmark once inputs grow large. Big-O is by far the most commonly used in casual conversation (often used loosely to mean "the tight bound," even when technically it only guarantees an upper bound), but knowing the precise distinction matters when reasoning carefully about best-case versus worst-case behavior.

## 3. Core concept

**Formal-ish intuition, without heavy math:** for a function `f(n)` describing an algorithm's actual work as a function of input size `n`:
- `f(n) = O(g(n))` means `f` grows **no faster than** `g`, for large enough `n` (up to a constant factor). Example: `f(n) = 3n + 5` is `O(n)`, since it never grows faster than a straight line.
- `f(n) = Ω(g(n))` means `f` grows **no slower than** `g`. Example: `f(n) = 3n + 5` is also `Ω(n)`.
- `f(n) = Θ(g(n))` means `f` grows **at the same rate** as `g` — both `O(g(n))` and `Ω(g(n))` hold simultaneously. Example: `f(n) = 3n + 5` is `Θ(n)`, since it is bounded both above and below by a linear function.

**Why Big-O is used so much more loosely in everyday practice than Big-Theta:** Big-O only requires an upper bound, so it is always "safe" to state (you can always pick a looser bound, like saying an O(n) algorithm is also technically O(n^2)) — but this looseness means Big-O alone does not tell you the algorithm's *actual* tight growth rate. When people casually say "this is O(n log n)," they usually mean the tighter Θ(n log n), since a genuinely useful complexity claim wants precision — but the distinction becomes important specifically when best-case and worst-case differ (see [Best / average / worst case analysis](0003-best-average-worst-case-analysis.md)), since a single Big-O bound can only describe one of them at a time.

**Constants and lower-order terms are dropped, and why that is still meaningful:** `f(n) = 100n + 1000000` is still `O(n)`, even though the constant `1000000` dominates for small `n` — because as `n` grows without bound, the linear term `100n` eventually dominates any fixed constant, and it is this large-`n` scaling behavior that Big-O notation is designed to capture, not small-`n` performance.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Big-O as an upper bound curve, Big-Omega as a lower bound curve, and Big-Theta as the tight band between them">
  <g font-family="sans-serif" font-size="12">
    <line x1="50" y1="170" x2="650" y2="170" stroke="#8b949e"/>
    <line x1="50" y1="170" x2="50" y2="20" stroke="#8b949e"/>
    <path d="M50,170 Q350,20 650,20" fill="none" stroke="#f85149" stroke-width="2"/>
    <text x="600" y="35" fill="#f85149" font-size="11">O(g(n)): upper bound</text>
    <path d="M50,170 Q350,160 650,140" fill="none" stroke="#3fb950" stroke-width="2"/>
    <text x="500" y="155" fill="#3fb950" font-size="11">Omega(g(n)): lower bound</text>
    <path d="M50,170 Q350,90 650,80" fill="none" stroke="#79c0ff" stroke-width="2"/>
    <text x="450" y="100" fill="#79c0ff" font-size="11">Theta(g(n)): both bounds match</text>
  </g>
</svg>

Big-O bounds growth from above, Big-Omega bounds it from below, and Big-Theta is the special case where an algorithm's actual growth is sandwiched tightly between a matching upper and lower bound.

## 5. Runnable example

The artifact below measures actual operation counts for a linear search, empirically demonstrating that its worst case grows linearly (matching Θ(n)), while its best case is constant (Ω(1) in the best case, distinct from its worst-case Θ(n)).

```java
// BigONotation.java
import java.util.*;

public class BigONotation {

    // Returns the number of comparisons made, not the found index - to measure actual work.
    static int linearSearchComparisons(int[] arr, int target) {
        int comparisons = 0;
        for (int value : arr) {
            comparisons++;
            if (value == target) return comparisons;
        }
        return comparisons;
    }

    public static void main(String[] args) {
        int[] sizes = {10, 100, 1000, 10000};
        System.out.println("Worst case (target not present, or at the very end):");
        for (int n : sizes) {
            int[] arr = new int[n];
            Arrays.fill(arr, -1); // target never found -> worst case, full scan
            int comparisons = linearSearchComparisons(arr, 999999);
            System.out.println("n=" + n + " -> comparisons=" + comparisons + " (matches n, i.e. Theta(n))");
        }

        System.out.println("Best case (target at index 0):");
        int[] arr = new int[10000];
        arr[0] = 42;
        System.out.println("comparisons=" + linearSearchComparisons(arr, 42) + " (constant, Omega(1) in the best case)");
    }
}
```

**How to run:** save as `BigONotation.java`, then run `java BigONotation.java`.

## 6. Walkthrough

1. For each input size `n`, the worst-case test fills the array with a value that never matches the target, forcing `linearSearchComparisons` to scan every element before returning.
2. The printed comparison counts exactly equal `n` in every case (`n=10` gives `10` comparisons, `n=10000` gives `10000`), directly demonstrating that the worst-case running time grows linearly with input size — matching `Θ(n)`, both upper- and lower-bounded by a linear function in the worst case.
3. The best-case test places the target at index `0`, so the loop returns after exactly `1` comparison, regardless of how large the array is — this demonstrates that the *best case* has a much better bound, `Ω(1)`, that the worst-case `Θ(n)` bound does not capture on its own.
4. This split between best-case and worst-case behavior is exactly why stating a single "Big-O" without specifying *which* case it describes can be ambiguous — a precise claim needs to say "worst-case O(n)" or "best-case O(1)" explicitly.

## 7. Gotchas & takeaways

> Gotcha: saying an algorithm "is O(n^2)" when its actual tight bound is O(n) is not technically wrong (Big-O only claims an upper bound, and any looser bound remains valid), but it is misleadingly imprecise — in practice, always state the tightest bound you can justify, and prefer Big-Theta language ("this algorithm's running time is Θ(n)") when you mean to describe exact growth, not just an upper limit.

- Big-O = upper bound, Big-Omega = lower bound, Big-Theta = tight bound (both match).
- Constants and lower-order terms are dropped because the notation describes large-`n` scaling behavior, not small-`n` absolute performance.
- Related concepts: [Best / average / worst case analysis](0003-best-average-worst-case-analysis.md) (why a single Big-O claim can be ambiguous without specifying which case it describes), [Common growth rates (constant to factorial)](0006-common-growth-rates-constant-to-factorial.md) (the standard vocabulary of growth-rate classes these notations are used to describe).
