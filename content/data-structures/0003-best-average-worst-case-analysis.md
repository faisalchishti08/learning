---
card: data-structures
gi: 3
slug: best-average-worst-case-analysis
title: Best / average / worst case analysis
---

## 1. What it is

**Best case** describes an algorithm's performance on the most favorable possible input (the least amount of work it could ever do). **Worst case** describes performance on the least favorable input (the most work it could ever do). **Average case** describes expected performance across a distribution of "typical" inputs, which requires assumptions about what inputs are likely. The same algorithm can have very different complexities for each — [linear search](0002-big-o-big-theta-big-omega-notation.md)'s best case is O(1) (target is first), but its worst case is O(n) (target is last, or absent).

## 2. Why & when

Use this three-way split whenever a single Big-O claim would be misleading or ambiguous — many algorithms behave very differently depending on the input's shape, and picking the wrong case to reason about leads to either overly pessimistic assumptions (rejecting a fast-in-practice algorithm because its rare worst case is bad) or dangerously optimistic ones (deploying an algorithm whose worst case causes a production timeout under adversarial or unlucky input).

## 3. Core concept

**Why the three cases can differ so much, using quicksort as the sharpest example:** quicksort's *average* case is O(n log n), and this is what makes it practically fast and widely used. But its *worst* case is O(n²) — this happens when the pivot chosen at every step is consistently the smallest or largest remaining element (for example, naive first-element-pivot quicksort on an already-sorted array), causing each partition to only shrink the problem by one element instead of roughly halving it. The *best* case is also O(n log n), achieved when every pivot happens to split the array into two roughly equal halves.

**When each case matters most in practice:**
- **Worst case** matters for systems with hard guarantees — real-time systems, adversarial inputs (an attacker deliberately crafting slow input), or any context where an occasional slow run is unacceptable, not just undesirable.
- **Average case** matters for typical throughput reasoning — how a system behaves "usually," assuming inputs are not adversarial and roughly match some expected distribution.
- **Best case** matters least often in practice, but is useful for understanding an algorithm's theoretical floor, and for recognizing when an algorithm has been given ideal input (helpful when debugging why something ran unexpectedly fast).

**Why average-case analysis requires an assumption about input distribution, while best/worst case do not:** best case is defined as "the input that minimizes work" and worst case as "the input that maximizes work" — both are well-defined without any probabilistic assumptions, since they are just asking for an extremum over all possible inputs. Average case, by contrast, requires deciding *how likely* each input is (uniformly random? following some real-world distribution?), and a different assumed distribution can produce a genuinely different average-case answer for the same algorithm.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Quicksort's three cases plotted against input size: best and average both n log n, worst case n squared">
  <g font-family="sans-serif" font-size="12">
    <line x1="50" y1="170" x2="650" y2="170" stroke="#8b949e"/>
    <line x1="50" y1="170" x2="50" y2="20" stroke="#8b949e"/>
    <path d="M50,170 Q350,60 650,25" fill="none" stroke="#f85149" stroke-width="2"/>
    <text x="600" y="40" fill="#f85149" font-size="11">worst: O(n^2)</text>
    <path d="M50,170 Q350,140 650,110" fill="none" stroke="#3fb950" stroke-width="2"/>
    <text x="500" y="150" fill="#3fb950" font-size="11">best/average: O(n log n)</text>
  </g>
</svg>

## 5. Runnable example

The artifact below measures linear search's actual comparison counts across best-case, average-case (random target position), and worst-case scenarios, demonstrating the gap empirically.

```java
// BestAverageWorstCase.java
import java.util.*;

public class BestAverageWorstCase {

    static int linearSearchComparisons(int[] arr, int target) {
        int comparisons = 0;
        for (int value : arr) {
            comparisons++;
            if (value == target) return comparisons;
        }
        return comparisons;
    }

    public static void main(String[] args) {
        int n = 10000;
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = i;

        // Best case: target is the first element.
        System.out.println("Best case: " + linearSearchComparisons(arr, 0) + " comparisons");

        // Worst case: target is the last element (or absent).
        System.out.println("Worst case: " + linearSearchComparisons(arr, n - 1) + " comparisons");

        // Average case: measure across many random target positions.
        Random random = new Random(42);
        long totalComparisons = 0;
        int trials = 1000;
        for (int t = 0; t < trials; t++) {
            int target = random.nextInt(n);
            totalComparisons += linearSearchComparisons(arr, target);
        }
        System.out.println("Average case (over " + trials + " random targets): "
            + (totalComparisons / trials) + " comparisons (expect close to n/2 = " + (n / 2) + ")");
    }
}
```

**How to run:** save as `BestAverageWorstCase.java`, then run `java BestAverageWorstCase.java`.

## 6. Walkthrough

1. Best case: searching for `0` (stored at index `0`) takes exactly `1` comparison — the loop returns on its very first iteration, matching O(1).
2. Worst case: searching for `n-1` (stored at the last index) forces the loop to scan every single element before finding a match, taking `n` comparisons — matching O(n).
3. Average case: across `1000` trials with uniformly random target positions, the measured average comparison count converges close to `n/2` — matching the theoretical expectation that, on average, a linear search scans about half the array before finding a uniformly random target.
4. All three numbers come from running the *exact same algorithm*, `linearSearchComparisons`, on different input scenarios — the algorithm itself did not change; only the input's position relative to the search order did, which is precisely what "case" analysis is measuring.

## 7. Gotchas & takeaways

> Gotcha: assuming "average case" automatically means "typical" or "safe to rely on" is risky — average-case analysis depends entirely on the assumed input distribution, and a malicious or adversarial actor can deliberately construct worst-case inputs (as in algorithmic-complexity denial-of-service attacks against naive hash tables or quicksort implementations), making the *worst* case the one that actually matters for security-sensitive systems.

- Best case = most favorable input; worst case = least favorable input; average case = expected performance under an assumed input distribution.
- The three cases can differ dramatically for the same algorithm (quicksort: O(n log n) average/best, O(n²) worst) — always specify which case a complexity claim refers to.
- Related concepts: [Big-O, Big-Theta, Big-Omega notation](0002-big-o-big-theta-big-omega-notation.md) (the notation used to express each case's bound precisely), [Amortized analysis (dynamic-array doubling)](0004-amortized-analysis-dynamic-array-doubling.md) (a related but distinct idea — average cost *per operation across a sequence*, not average cost across random inputs).
