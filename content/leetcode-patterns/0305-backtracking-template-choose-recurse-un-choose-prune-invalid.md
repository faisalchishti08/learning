---
card: leetcode-patterns
gi: 305
slug: backtracking-template-choose-recurse-un-choose-prune-invalid
title: Backtracking — template: choose, recurse, un-choose (prune invalid branches)
---

## 1. What it is

This page gives the reusable template for backtracking problems: a recursive function that chooses one option, recurses deeper, then un-chooses it, with a pruning check placed as early as possible.

## 2. Why & when

Use this template whenever a problem needs every valid arrangement, combination, or path built up from smaller choices, with rules that can reject a PARTIAL solution before it is fully built. The structure below is intentionally generic — the exact "choices" and "is valid" checks change per problem, but the choose-recurse-un-choose skeleton stays identical.

## 3. Core concept

**Template — backtracking search.**
1. Define a recursive function `backtrack(partialSolution, remainingChoices)`.
2. **Base case:** if `partialSolution` is complete (or a target condition is met), record it as a valid result, and return.
3. **Loop over choices:** for each option still available at this level:
   - **Prune:** if choosing this option would immediately violate a constraint, skip it (`continue`).
   - **Choose:** add the option to `partialSolution` (and update any shared tracking structure, like a "visited" set).
   - **Recurse:** call `backtrack` again with the updated state.
   - **Un-choose:** remove the option from `partialSolution` (and undo any shared tracking structure changes), restoring the state for the next iteration of the loop.

Why it works: because every choice is undone right after its own subtree finishes exploring, the SAME `partialSolution` object can be reused across the entire search tree — there is no need to copy or snapshot state at each level, which keeps both the code and the memory usage simple. Pruning before recursing (not after) is what avoids wasting a full recursive call, and its own nested loop, on a branch already known to fail.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Template loop: prune check, choose, recurse, un-choose, repeating for each candidate at the current level">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">for each candidate at this level:</text>
    <rect x="10" y="35" width="110" height="30" fill="#161b22" stroke="#f85149"/><text x="65" y="54" fill="#e6edf3" text-anchor="middle" font-size="10">prune check</text>
    <text x="130" y="54">-&gt;</text>
    <rect x="150" y="35" width="90" height="30" fill="#161b22" stroke="#30363d"/><text x="195" y="54" fill="#e6edf3" text-anchor="middle" font-size="10">choose</text>
    <text x="250" y="54">-&gt;</text>
    <rect x="270" y="35" width="90" height="30" fill="#161b22" stroke="#30363d"/><text x="315" y="54" fill="#e6edf3" text-anchor="middle" font-size="10">recurse</text>
    <text x="370" y="54">-&gt;</text>
    <rect x="390" y="35" width="80" height="30" fill="#161b22" stroke="#30363d"/><text x="430" y="54" fill="#e6edf3" text-anchor="middle" font-size="10">un-choose</text>
    <text x="10" y="90">prune fails -&gt; skip straight to the next candidate, no recursion</text>
  </g>
</svg>

A failed prune check skips choose/recurse/un-choose entirely, moving on to the next candidate.

## 5. Runnable example

```java
// BacktrackingTemplate.java
import java.util.*;

public class BacktrackingTemplate {

    // Template applied to "all subsets of a set" -- one of the
    // simplest backtracking problems, useful as a template check.
    static void backtrack(int[] nums, int start, List<Integer> current, List<List<Integer>> results) {
        results.add(new ArrayList<>(current)); // every partial state is itself a valid subset

        for (int i = start; i < nums.length; i++) {
            // no prune needed here -- every remaining number is a valid next choice
            current.add(nums[i]);                          // choose
            backtrack(nums, i + 1, current, results);       // recurse
            current.remove(current.size() - 1);             // un-choose
        }
    }

    public static void main(String[] args) {
        List<List<Integer>> results = new ArrayList<>();
        backtrack(new int[]{1, 2, 3}, 0, new ArrayList<>(), results);
        System.out.println(results);
        // [[], [1], [1, 2], [1, 2, 3], [1, 3], [2], [2, 3], [3]]
    }
}
```

**How to run:** `java BacktrackingTemplate.java`

## 6. Walkthrough

1. `backtrack` is called with `start=0`, `current=[]`. It immediately records `[]` as a valid subset (the empty set counts).
2. The loop tries `i=0` (value `1`): choose `1` (`current=[1]`), recurse with `start=1`.
3. Inside that recursive call, `[1]` is recorded, then the loop tries `i=1` (value `2`): choose `2` (`current=[1,2]`), recurse with `start=2`.
4. This continues until `current=[1,2,3]` is recorded, then the recursion unwinds, un-choosing `3`, then `2`, back to `current=[1]`.
5. Back at the `start=0` level, after fully exploring the `1` branch, `1` is un-chosen (`current=[]`), and the loop moves to `i=1` (value `2`), repeating the same choose-recurse-un-choose cycle for the remaining candidates.

## 7. Gotchas & takeaways

> Gotcha: recording `new ArrayList<>(current)` (a COPY) into `results`, instead of `current` itself, is essential — since `current` keeps getting mutated (choose/un-choose) throughout the search, storing a direct reference to it would leave every recorded result pointing at the same, constantly-changing list.

- The template's shape stays constant: prune check, choose, recurse, un-choose — only the specific prune condition and choice set change per problem.
- Passing a `start` index (instead of re-scanning from the beginning each time) is how many combination/subset problems avoid generating duplicate, differently-ordered versions of the same set.
- For "kth smallest" or "just one valid answer" variants, add an early-return flag once the first valid answer is found, to skip exploring the rest of the search tree.
