---
card: leetcode-patterns
gi: 213
slug: subsets-combinations-permutations-complexity-o-2-n-or-o-n-ti
title: Subsets (Combinations & Permutations) — complexity: O(2^n) or O(n!) time
---

## 1. What it is

This page explains why subset generation runs in O(2ⁿ) time and permutation generation runs in O(n!) time, why these ARE the optimal complexities (not a sign of a bad algorithm), and lists the named problems that use this pattern.

## 2. Why & when

Interviewers expect you to recognize that exponential or factorial time here is NOT a red flag — it is unavoidable, because the output itself has that many elements. Explaining "this is O(2ⁿ) because there are 2ⁿ subsets to produce, and we must produce each one" is a stronger answer than apologizing for the complexity.

## 3. Core concept

**Subsets — O(2ⁿ) time, O(2ⁿ) space.** There are exactly 2ⁿ subsets of an n-element set (each element independently in or out). The DFS backtracking template visits exactly one tree node per subset (since a result is added at every node), so the number of `result.add(...)` calls is exactly 2ⁿ. Each copy costs O(n) in the worst case (copying a full-length subset), so a tighter bound is O(n · 2ⁿ) if you count the copying cost, but the NUMBER of subsets itself is the dominant, unavoidable factor.

**Permutations — O(n!) time, O(n!) space.** There are exactly n! orderings of n distinct elements. The DFS backtracking template's leaves (where a full permutation is complete) number exactly n!, and each leaf costs O(n) to copy — so total time is O(n · n!).

**Combinations of size k — O(C(n,k)) time.** Restricting to a fixed size `k` prunes the tree to only the `n choose k` valid leaves, which is smaller than the full 2ⁿ subset count whenever `k` is far from `n/2`.

**Why this is optimal, not a mistake.** Any algorithm that must PRINT or RETURN every subset (or permutation) cannot run faster than the time it takes to write out the output, which is already 2ⁿ (or n!) in size. This is fundamentally different from a DP or greedy problem, where the answer is a single number and a polynomial algorithm is expected — here, exponential/factorial time is the theoretical lower bound, not an inefficiency to fix.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Subset count doubles per element; permutation count multiplies by a shrinking factor per position">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">Subsets: doubles each level</text>
    <rect x="20" y="30" width="20" height="20" fill="#3fb950"/>
    <rect x="50" y="30" width="20" height="20" fill="#3fb950"/><rect x="80" y="30" width="20" height="20" fill="#3fb950"/>
    <rect x="120" y="30" width="20" height="20" fill="#3fb950"/><rect x="150" y="30" width="20" height="20" fill="#3fb950"/>
    <rect x="180" y="30" width="20" height="20" fill="#3fb950"/><rect x="210" y="30" width="20" height="20" fill="#3fb950"/>
    <text x="10" y="70" fill="#8b949e">1, 2, 4, 8... = 2^n</text>

    <text x="20" y="110" fill="#e6edf3" font-weight="bold">Permutations: multiplies by shrinking count</text>
    <text x="10" y="150" fill="#8b949e">n, n*(n-1), n*(n-1)*(n-2)... = n!</text>
  </g>
</svg>

Subset count doubles at every level of the decision tree; permutation count multiplies by one fewer available choice at each successive position.

## 5. Runnable example

An instrumented DFS that counts how many `result.add` calls actually happen for subsets versus permutations, confirming both bounds hold exactly on real input.

```java
// ComplexityCheck.java
import java.util.*;

public class ComplexityCheck {
    static int subsetCalls = 0;
    static int permutationCalls = 0;

    static void subsetsDFS(int[] nums, int start, List<Integer> path) {
        subsetCalls++;
        for (int i = start; i < nums.length; i++) {
            path.add(nums[i]);
            subsetsDFS(nums, i + 1, path);
            path.remove(path.size() - 1);
        }
    }

    static void permutationsDFS(int[] nums, boolean[] used, List<Integer> path) {
        if (path.size() == nums.length) { permutationCalls++; return; }
        for (int i = 0; i < nums.length; i++) {
            if (used[i]) continue;
            used[i] = true;
            path.add(nums[i]);
            permutationsDFS(nums, used, path);
            path.remove(path.size() - 1);
            used[i] = false;
        }
    }

    public static void main(String[] args) {
        int[] nums = {1, 2, 3, 4, 5};
        subsetsDFS(nums, 0, new ArrayList<>());
        permutationsDFS(nums, new boolean[nums.length], new ArrayList<>());

        System.out.println("n=" + nums.length);
        System.out.println("subset results: " + subsetCalls + " (expected 2^n = " + (1 << nums.length) + ")");
        System.out.println("permutation results: " + permutationCalls + " (expected n! = 120)");
    }
}
```

**How to run:** `java ComplexityCheck.java`

## 6. Walkthrough

1. `nums` has 5 elements.
2. `subsetsDFS` is called once per tree node — every node (not just leaves) represents one valid subset, so `subsetCalls` should land exactly on `2^5 = 32`.
3. `permutationsDFS` only counts at leaves (`path.size() == nums.length`), so `permutationCalls` should land exactly on `5! = 120`.
4. Running the code confirms both counts match their theoretical formulas precisely — no wasted work beyond the necessary output size.
5. This confirms both algorithms do the theoretical minimum amount of "produce one result" work — any correct algorithm for these problems must do at least this much, since it has to actually generate every one of the 2ⁿ or n! outputs.

## 7. Gotchas & takeaways

> Gotcha: mistakenly believing a "smarter" algorithm could generate all subsets or permutations faster than O(2ⁿ) or O(n!) misunderstands the lower bound — the OUTPUT itself has that many elements, so no algorithm that returns all of them can be asymptotically faster.

- Time: O(n · 2ⁿ) for subsets (2ⁿ results, each O(n) to copy); O(n · n!) for permutations (n! results, each O(n) to copy).
- Space: matches the time bound, since the output itself must be stored — this is unavoidable, not a space-efficiency bug.
- Reference problems that use this pattern: Subsets, Subsets II, Permutations, Permutations II, Combinations, Combination Sum, Combination Sum II, Letter Combinations of a Phone Number, Generate Parentheses.
