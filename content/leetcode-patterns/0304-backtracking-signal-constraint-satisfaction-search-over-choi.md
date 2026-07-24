---
card: leetcode-patterns
gi: 304
slug: backtracking-signal-constraint-satisfaction-search-over-choi
title: Backtracking — signal: constraint-satisfaction search over choices
---

## 1. What it is

Backtracking explores every possible sequence of choices, one choice at a time, and ABANDONS a path the moment it can no longer lead to a valid answer. Think of navigating a maze by trying a direction, and if it dead-ends, walking back to the last junction to try a different direction, instead of giving up entirely.

## 2. Why & when

Reach for this pattern whenever a problem asks you to build up a solution one piece at a time — a path, a combination, an arrangement — and each partial solution can be checked, early, for whether it is still valid or has already failed. Trying every possibility with plain nested loops does not scale past a fixed, small number of choices; backtracking generalizes to any number of choices by using recursion, and PRUNES invalid branches early instead of wastefully exploring them to the end.

Learn to recognize these signals in a problem statement:

- **"Find all combinations/permutations/subsets that satisfy..."** — generate every valid arrangement of choices.
- **"Word search," "path in a grid using each cell once"** — explore a grid by trying each direction, backing off when a path fails.
- **"Partition into k groups/subsets with equal sum"** — try assigning each item to a group, backing off if a group's sum overflows.
- **"Generate all valid IP addresses / parentheses / fibonacci-like sequences"** — build a string or sequence piece by piece, checking validity as you go.

The alternative — generating EVERY possible combination first, then filtering out invalid ones — wastes huge amounts of work on combinations that could have been rejected long before they were even fully built.

## 3. Core concept

Every backtracking problem follows the same three-step rhythm, applied at each level of a recursive search:

**Choose.** Pick one option from the current set of choices (a cell to move to, a number to include, a digit to add) and add it to your current partial solution.

**Recurse.** Call the search function again, moving one level deeper, now working with the updated partial solution.

**Un-choose (backtrack).** After the recursive call returns — whether it found a solution or hit a dead end — UNDO the choice, restoring the state to before it was made, so the next choice at this level starts clean.

**Prune.** Before recursing (or even before choosing), check whether the current partial solution can still possibly succeed. If not, skip it entirely — this is what keeps backtracking from degenerating into brute-force enumeration.

The key insight: recursion naturally builds a tree of all possible choice sequences, and undoing each choice after its subtree is explored means the SAME shared state (an array, a string builder, a visited set) can be reused across the entire search, without needing to copy it at every level.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Recursion tree showing choose, recurse, un-choose at each branch, with one branch pruned early">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">Choosing digits for a 2-digit code from {1,2,3}</text>
    <circle cx="240" cy="45" r="16" fill="#161b22" stroke="#30363d"/><text x="240" y="49" fill="#e6edf3" text-anchor="middle" font-size="10">""</text>
    <circle cx="120" cy="95" r="16" fill="#161b22" stroke="#3fb950"/><text x="120" y="99" fill="#e6edf3" text-anchor="middle" font-size="10">"1"</text>
    <circle cx="240" cy="95" r="16" fill="#161b22" stroke="#f85149"/><text x="240" y="99" fill="#e6edf3" text-anchor="middle" font-size="10">"2"</text>
    <circle cx="360" cy="95" r="16" fill="#161b22" stroke="#3fb950"/><text x="360" y="99" fill="#e6edf3" text-anchor="middle" font-size="10">"3"</text>
    <line x1="240" y1="61" x2="120" y2="79" stroke="#8b949e"/>
    <line x1="240" y1="61" x2="240" y2="79" stroke="#8b949e"/>
    <line x1="240" y1="61" x2="360" y2="79" stroke="#8b949e"/>
    <text x="240" y="130" fill="#f85149" text-anchor="middle" font-size="10">pruned: "2" fails a rule, stop here</text>
    <text x="120" y="150" fill="#8b949e" text-anchor="middle" font-size="10">"1" continues to "12", "13"</text>
  </g>
</svg>

The branch under `"2"` is abandoned immediately once it violates a rule, saving the work of exploring anything below it.

## 5. Runnable example

```java
// BacktrackingSignal.java
import java.util.*;

public class BacktrackingSignal {

    // Signal check: generate all 2-digit codes from {1,2,3} where
    // consecutive digits must differ by more than 1 (a toy constraint
    // to demonstrate pruning).
    static void search(int[] choices, List<Integer> current, List<List<Integer>> results, int length) {
        if (current.size() == length) {
            results.add(new ArrayList<>(current)); // record a complete valid solution
            return;
        }
        for (int choice : choices) {
            if (!current.isEmpty() && Math.abs(current.get(current.size() - 1) - choice) <= 1) {
                continue; // prune: this choice violates the constraint
            }
            current.add(choice);       // choose
            search(choices, current, results, length); // recurse
            current.remove(current.size() - 1); // un-choose
        }
    }

    public static void main(String[] args) {
        List<List<Integer>> results = new ArrayList<>();
        search(new int[]{1, 2, 3}, new ArrayList<>(), results, 2);
        System.out.println(results);
        // [[1, 3], [3, 1]]
    }
}
```

**How to run:** `java BacktrackingSignal.java`

## 6. Walkthrough

1. You read a problem statement. "Find all valid arrangements satisfying a rule" is the backtracking signal — build one arrangement at a time, checking the rule as you go.
2. Running `search` with digits `{1,2,3}` and length `2` confirms only `[1,3]` and `[3,1]` survive, since `1↔2` and `2↔3` differ by only `1` and get pruned.
3. Each recursive call either extends `current` by one more valid choice, or the loop simply moves to the next candidate if the current one is pruned.
4. Removing the last element after each recursive call (`current.remove(...)`) is the "un-choose" step — it resets shared state so the next sibling branch starts from a clean slate.
5. This upfront classification (build one choice at a time, prune early, undo after recursing) tells you which template on the next page to reach for.

## 7. Gotchas & takeaways

> Gotcha: forgetting the un-choose step (or un-choosing the wrong element) corrupts the shared state for every SIBLING branch explored afterward — a bug that often shows up as a correct-looking first branch followed by silently wrong results in later branches.

- Choose, recurse, un-choose: the three-step rhythm behind every backtracking solution.
- Pruning as EARLY as possible (before recursing, not after) is what keeps backtracking from exploring the full exponential search space in practice.
- Using a single, reused mutable structure (a list, a string builder, a boolean array) — instead of copying state at every level — is what keeps backtracking memory-efficient.
