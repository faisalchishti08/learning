---
card: leetcode-patterns
gi: 327
slug: dp-0-1-knapsack-complexity-o-n-w-time
title: DP: 0/1 Knapsack — complexity: O(n*W) time
---

## 1. What it is

This page pins down the time and space cost of the 0/1 Knapsack pattern, why it counts as "pseudo-polynomial," and lists the problems that use it.

## 2. Why & when

Use this page as the reference point once you recognize the signal and the template. You need to be able to state the complexity precisely, including the important caveat that it depends on the NUMERIC SIZE of the capacity, not just the number of items — a detail that trips people up in interviews.

## 3. Core concept

**Complexity.** With `n` items and capacity `W`, the DP table has `(n+1) * (W+1)` cells, each computed in O(1) time (one comparison between "skip" and "take"). Total time: O(n · W). Space: O(n · W) for the 2D table, or O(W) for the 1D space-optimized version.

**Why this is called "pseudo-polynomial."** O(n · W) LOOKS polynomial in `n` and `W`, but `W` is a NUMERIC VALUE (the capacity), not the size of the input in the usual algorithmic sense — representing the number `W` only takes O(log W) bits. So the runtime is actually exponential in the INPUT SIZE if `W` is very large (say, `W = 10^9`), even though it is perfectly fast when `W` is small or moderate (say, `W <= 10^5`), which is why LeetCode 0/1 knapsack problems always constrain the capacity or target sum to a reasonably small range.

**Compare against brute force.** Trying every subset of `n` items costs O(2^n), which is far worse than O(n · W) whenever `W` is small relative to `2^n` — for `n = 30` items, brute force explores over a billion subsets, while a knapsack with `W = 1000` computes the answer in about 30,000 operations.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparison of brute force 2 to the n subsets versus knapsack DP n times W operations for n=30 items and W=1000 capacity">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">n = 30 items, W = 1000 capacity</text>
    <text x="10" y="45">Brute force: 2^30 ~ 1,073,741,824 subsets</text>
    <text x="10" y="65">0/1 Knapsack DP: 30 * 1000 = 30,000 cell computations</text>
    <rect x="10" y="80" width="280" height="24" fill="#3fb950"/><text x="150" y="97" fill="#0d1117" text-anchor="middle" font-size="10">DP is roughly 35,000x fewer operations here</text>
  </g>
</svg>

The DP's O(n · W) cost tracks the capacity's numeric size, not the exponential subset count.

## 5. Runnable example

```java
// Knapsack01Complexity.java
public class Knapsack01Complexity {

    // O(n * W): n items, W capacity, one O(1) decision per cell.
    static int knapsack(int[] weights, int[] values, int capacity) {
        int[] dp = new int[capacity + 1];
        for (int i = 0; i < weights.length; i++) {
            for (int w = capacity; w >= weights[i]; w--) {
                dp[w] = Math.max(dp[w], dp[w - weights[i]] + values[i]);
            }
        }
        return dp[capacity];
    }

    public static void main(String[] args) {
        int n = 30, capacity = 1000;
        int[] weights = new int[n];
        int[] values = new int[n];
        for (int i = 0; i < n; i++) {
            weights[i] = (i % 20) + 1;
            values[i] = (i % 15) + 1;
        }

        long start = System.nanoTime();
        int result = knapsack(weights, values, capacity);
        long elapsed = System.nanoTime() - start;

        System.out.println("best value: " + result);
        System.out.println("cells computed (approx n*W): " + (n * capacity));
        System.out.println("elapsed ms: " + elapsed / 1_000_000);
    }
}
```

**How to run:** `java Knapsack01Complexity.java`

## 6. Walkthrough

1. `n = 30` items, `capacity = 1000`. The DP processes each item once, and for each item, scans up to `1000` capacity values.
2. Total cell computations: `30 * 1000 = 30,000`, each doing a single comparison and addition — a trivially fast amount of work for modern hardware.
3. Compare this to brute force: trying every one of the `2^30 ≈ 1.07 billion` subsets, each requiring at least O(n) work to sum weights and values, would be many orders of magnitude slower.
4. This experiment confirms the theoretical bound directly: the algorithm's total work scales with `n * capacity`, not with the exponential subset count.
5. If `capacity` were instead `10^9` (still just one number, but a huge one), this SAME algorithm would need `30 * 10^9 = 3*10^10` operations — far too slow, despite the identical "polynomial-looking" O(n · W) formula; this is the pseudo-polynomial caveat in action.

## 7. Gotchas & takeaways

> Gotcha: stating the complexity as simply "O(n · W)" without noting that `W` is a NUMERIC VALUE (not a count of input items) can be misleading in an interview — always mention the pseudo-polynomial caveat, since it explains why 0/1 knapsack works great for LeetCode-scale capacities but would need a different approach (like meet-in-the-middle) for astronomically large capacities.

- Time: O(n · W). Space: O(n · W) for the 2D table, O(W) for the 1D optimized version.
- "Pseudo-polynomial" means the runtime depends on the CAPACITY'S VALUE, not just the number of items — fine for small/moderate capacities, problematic for huge ones.
- Problems using this pattern: Partition Equal Subset Sum, Target Sum, Last Stone Weight II, Ones and Zeroes, Maximum Value of K Coins From Piles, Filling Bookcase Shelves, Profitable Schemes, Tallest Billboard, Number of Ways to Earn Points.
