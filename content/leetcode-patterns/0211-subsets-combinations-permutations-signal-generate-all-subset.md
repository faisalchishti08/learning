---
card: leetcode-patterns
gi: 211
slug: subsets-combinations-permutations-signal-generate-all-subset
title: Subsets (Combinations & Permutations) — signal: generate all subsets, combinations, or permutations
---

## 1. What it is

This pattern covers problems that ask you to generate EVERY possible way of choosing or arranging elements from a set — every subset, every combination of a certain size, or every ordering (permutation). Think of it as systematically exploring a decision tree where each node represents a partial choice, and every leaf represents one complete answer.

## 2. Why & when

You reach for this pattern when a problem asks you to enumerate ALL valid outputs, not just count them or find one optimal one. Unlike dynamic programming (which often collapses many paths into one number), these problems need every distinct combination or arrangement actually listed out, which means the algorithm's output size itself grows exponentially or factorially.

Learn to recognize these signals in a problem statement:

- **"Return all possible subsets"** or **"the power set."** Every element is either included or excluded — a binary choice per element.
- **"Return all combinations of size k"** or **"that sum to a target."** You are choosing a subset with an additional constraint (fixed size, or a running sum condition).
- **"Return all permutations"** or **"all possible orderings/arrangements."** Every element must appear exactly once, but ORDER matters, unlike subsets/combinations.
- **"Generate all valid [parentheses / letter combinations / IP addresses]"** — a combinatorial generation problem with a validity rule that prunes some branches.

The alternative — a DP or greedy approach — applies when you only need a COUNT or an OPTIMAL VALUE, not every explicit answer. If the problem says "return all" or "return every," you need to actually build and collect each one, which is what this pattern's backtracking templates do.

## 3. Core concept

Every problem in this family builds a decision tree via BACKTRACKING: at each step, you make one choice (include this element, or don't; pick this next digit; place an open or close parenthesis), recurse into the consequence of that choice, then UNDO the choice (backtrack) before trying the next option at that same decision point.

Two distinct tree shapes cover almost every variant:

**Subsets/combinations tree (include/exclude, or choose-from-remaining).** At each step, decide whether to include the current element (then move to the next), or skip it. Order does not matter, so once an element is skipped, it is never reconsidered later in that branch — this naturally avoids generating the same subset twice.

**Permutations tree (choose next, from whatever remains).** At each step, pick ANY unused element to be the next one placed. Because order matters, every remaining element is tried at every position, and a `used` array (or list removal) tracks what is still available.

The key insight: both trees have depth equal to the number of elements considered, and BREADTH equal to the number of live choices at each node — which is exactly what produces the O(2ⁿ) or O(n!) output sizes this family is known for.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two decision-tree shapes: include/exclude for subsets, choose-next for permutations">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">Subsets: include/exclude at each element</text>
    <circle cx="60" cy="50" r="4" fill="#e6edf3"/>
    <line x1="60" y1="50" x2="30" y2="90" stroke="#3fb950"/><text x="20" y="105" fill="#3fb950" font-size="10">skip</text>
    <line x1="60" y1="50" x2="90" y2="90" stroke="#79c0ff"/><text x="90" y="105" fill="#79c0ff" font-size="10">include</text>
    <circle cx="30" cy="90" r="4" fill="#e6edf3"/>
    <circle cx="90" cy="90" r="4" fill="#e6edf3"/>

    <text x="380" y="20" fill="#e6edf3" font-weight="bold">Permutations: choose next from remaining</text>
    <circle cx="420" cy="50" r="4" fill="#e6edf3"/>
    <line x1="420" y1="50" x2="390" y2="90" stroke="#e3b341"/><text x="380" y="105" fill="#e3b341" font-size="10">pick A</text>
    <line x1="420" y1="50" x2="450" y2="90" stroke="#e3b341"/><text x="450" y="105" fill="#e3b341" font-size="10">pick B</text>
    <line x1="420" y1="50" x2="480" y2="90" stroke="#e3b341"/><text x="480" y="105" fill="#e3b341" font-size="10">pick C</text>
    <circle cx="390" cy="90" r="4" fill="#e6edf3"/>
    <circle cx="450" cy="90" r="4" fill="#e6edf3"/>
    <circle cx="480" cy="90" r="4" fill="#e6edf3"/>
  </g>
</svg>

Subsets branch two ways per element (2ⁿ leaves); permutations branch by every remaining choice per position (n! leaves).

## 5. Runnable example

A tiny probe that shows the two branching factors side by side, confirming which shape a given problem calls for.

### Signal-checker

```java
// SubsetsPermutationsSignal.java
public class SubsetsPermutationsSignal {
    static long subsetCount(int n) {
        return 1L << n; // 2^n: each element independently in or out
    }

    static long permutationCount(int n) {
        long result = 1;
        for (int i = 2; i <= n; i++) result *= i; // n!
        return result;
    }

    public static void main(String[] args) {
        int n = 4;
        System.out.println("n=" + n + " -> subsets: " + subsetCount(n) + " (2^n, order doesn't matter)");
        System.out.println("n=" + n + " -> permutations: " + permutationCount(n) + " (n!, order matters)");
    }
}
```

**How to run:** `java SubsetsPermutationsSignal.java`

## 6. Walkthrough

1. You read the problem statement. It says "return all possible subsets of the array" with no mention of order.
2. "All subsets" with no ordering requirement is the include/exclude signal — each of the `n` elements independently is in or out.
3. Running the checker above with `n=4` confirms `16` total subsets (`2^4`), matching what an include/exclude tree of depth 4 would produce.
4. If instead the problem said "return all possible ORDERINGS of the array," you would recognize the permutations signal, expecting `24` outputs (`4!`) instead.
5. This upfront classification tells you which template (§ next page) to reach for before writing a single line of backtracking code.

## 7. Gotchas & takeaways

> Gotcha: confusing "combinations" (order doesn't matter, `[1,2]` == `[2,1]`) with "permutations" (order matters, `[1,2]` != `[2,1]`) leads to either massively over-generating duplicate outputs or under-generating valid ones — always confirm from the problem statement which one is meant.

- Subsets/combinations: 2ⁿ possible outputs (or fewer, if constrained to a fixed size or sum) — order does not matter.
- Permutations: n! possible outputs — order matters, every element used exactly once.
- If duplicate elements are allowed in the input but the output must have no duplicate SUBSETS/permutations, expect an extra sorting-plus-skip step (see the "II" variants) on top of the base template.
