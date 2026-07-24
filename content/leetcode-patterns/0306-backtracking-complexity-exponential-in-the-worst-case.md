---
card: leetcode-patterns
gi: 306
slug: backtracking-complexity-exponential-in-the-worst-case
title: Backtracking — complexity: exponential in the worst case
---

## 1. What it is

This page pins down the time cost of backtracking, why it is inherently exponential, and how pruning changes the PRACTICAL (not theoretical worst-case) running time. It also lists the problems that use this pattern.

## 2. Why & when

Use this page as the reference point once you already recognize the signal and the template. You still need to be able to state the complexity honestly in an interview: backtracking's worst case is exponential, and pruning does not change that worst case, only the typical, practical performance on most inputs.

## 3. Core concept

**Why it is exponential.** At each of the `n` decision points, a backtracking search may try up to `b` choices (the "branching factor"). Without any pruning, the total number of complete paths explored is O(b^n) — a search TREE with `n` levels and `b` children per level has `b^n` leaves. This is fundamentally unavoidable for problems that ask for ALL valid arrangements, since the ANSWER itself can be exponentially large (there really can be `b^n` valid subsets, permutations, or paths).

**What pruning actually buys you.** Pruning cuts off branches EARLY, before they are fully explored, so the constant factor and the AVERAGE case improve dramatically — often turning an impractical brute force into a fast, usable solution. But the WORST-CASE bound stays exponential, because a problem instance can exist where no branch gets pruned until the very last choice.

**Reading complexity per problem shape.** A few common shapes and their typical costs:
- Generating all SUBSETS of `n` items: O(2^n) subsets, each taking up to O(n) to copy — O(n · 2^n) total.
- Generating all PERMUTATIONS of `n` items: O(n!) permutations, each O(n) to build — O(n · n!) total.
- Searching a grid of size `n × m` for a path: up to O(4^L) for a path of length `L`, since each cell has up to 4 neighboring choices.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Growth comparison of 2 to the n subsets versus n factorial permutations as n grows from 5 to 15">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">Growth as n increases</text>
    <text x="10" y="45">n=5:  2^5=32 subsets      5!=120 permutations</text>
    <text x="10" y="65">n=10: 2^10=1,024 subsets  10!=3,628,800 permutations</text>
    <text x="10" y="85">n=15: 2^15=32,768 subsets 15!=1,307,674,368,000 permutations</text>
    <rect x="10" y="100" width="300" height="24" fill="#f85149"/><text x="160" y="117" fill="#0d1117" text-anchor="middle" font-size="10">permutations explode far faster than subsets</text>
  </g>
</svg>

Factorial growth (permutations) vastly outpaces exponential growth (subsets) as `n` increases — both are backtracking, but their practical limits differ a lot.

## 5. Runnable example

```java
// BacktrackingComplexity.java
import java.util.*;

public class BacktrackingComplexity {

    // O(2^n) subsets, each O(n) to copy -- demonstrates counting how
    // many complete branches a backtracking search actually visits.
    static int branchesVisited = 0;

    static void countSubsets(int[] nums, int start, List<Integer> current) {
        branchesVisited++; // every recursive call is one "node" in the search tree
        for (int i = start; i < nums.length; i++) {
            current.add(nums[i]);
            countSubsets(nums, i + 1, current);
            current.remove(current.size() - 1);
        }
    }

    public static void main(String[] args) {
        int n = 15;
        int[] nums = new int[n];
        for (int i = 0; i < n; i++) nums[i] = i;

        branchesVisited = 0;
        long start = System.nanoTime();
        countSubsets(nums, 0, new ArrayList<>());
        long elapsed = System.nanoTime() - start;

        System.out.println("n = " + n);
        System.out.println("branches visited: " + branchesVisited);
        System.out.println("expected 2^n: " + (1 << n));
        System.out.println("elapsed ms: " + elapsed / 1_000_000);
    }
}
```

**How to run:** `java BacktrackingComplexity.java`

## 6. Walkthrough

1. `countSubsets` is called once per NODE in the search tree, including every partial subset, not just complete ones.
2. For `n = 15` items, the total number of nodes visited (every prefix of every subset) equals exactly `2^n = 32,768`, matching the "every element either included or excluded" reasoning.
3. Each call is O(1) work (incrementing a counter) beyond the loop overhead, so total time tracks the number of nodes directly: O(2^n).
4. If this were instead generating PERMUTATIONS of the same 15 items, the search tree would have `15! ≈ 1.3 trillion` leaves — computationally infeasible, which is why permutation-generating backtracking problems in practice always come with a small `n` (typically `n ≤ 10`).
5. This experiment confirms the theoretical bound directly: the branch count matches `2^n` exactly, with no pruning applied in this particular problem (every subset is valid, so nothing gets skipped).

## 7. Gotchas & takeaways

> Gotcha: assuming pruning changes the WORST-CASE complexity is a common misconception — pruning improves the typical case enormously, but the worst-case bound (when no branch gets pruned early) stays exponential; always state both when discussing a backtracking solution's complexity.

- Subsets: O(2^n). Permutations: O(n!). Grid paths: up to O(4^L). Know which shape your problem matches.
- Pruning changes practical runtime, not the worst-case asymptotic bound — say both in an interview.
- Problems using this pattern: Word Search, Combination Sum III, Restore IP Addresses, Beautiful Arrangement, Matchsticks to Square, Partition to K Equal Sum Subsets, Letter Case Permutation, Additive Number, Split Array into Fibonacci Sequence.
