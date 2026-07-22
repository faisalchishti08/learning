---
card: leetcode-patterns
gi: 220
slug: combination-sum-ii
title: Combination Sum II
---

## 1. What it is

Given a `candidates` array that MAY contain duplicates and a `target`, return all UNIQUE combinations summing to `target`, where EACH number may be used AT MOST ONCE (no reuse), and no duplicate combinations appear in the output. Example: `candidates = [10,1,2,7,6,1,5]`, `target = 8` → `[[1,1,6],[1,2,5],[1,7],[2,6]]`.

## 2. Why & when

This combines Combination Sum's sum-target tracking with Subsets II's duplicate-skipping trick, while REMOVING the reuse feature: recurse with `i + 1` (not `i`), since each number can only be used once, but still needs the sorted-input, same-level-duplicate-skip logic to avoid generating the same combination via different physical occurrences of a repeated value.

## 3. Core concept

**Key idea:** sort `candidates` so duplicates are adjacent. DFS tracks `remaining` (target minus sum so far) exactly like Combination Sum, but recurses with `i + 1` (no reuse). In the loop, skip index `i` if `i > start` AND `nums[i] == nums[i-1]` — using a later occurrence of the same value AT THE SAME TREE LEVEL would regenerate a combination already produced using the earlier occurrence.

**Steps:**
1. Sort `candidates` in ascending order.
2. Call a recursive helper with an empty partial list, a starting index of `0`, and `remaining = target`.
3. If `remaining == 0`, save a copy of `path` and return. If `remaining < 0`, return (prune).
4. Loop `i` from `start` to the end: if `i > start` AND `candidates[i] == candidates[i-1]`, skip (same-level duplicate).
5. Otherwise, add `candidates[i]`, recurse with `start = i + 1` (no reuse) and `remaining - candidates[i]`, then remove `candidates[i]` (backtrack).

**Why it is correct:** sorting plus the `i > start` duplicate-skip (identical logic to Subsets II) ensures each distinct combination of VALUES is generated exactly once, regardless of how many physically-identical copies of a value exist in the input. Recursing with `i + 1` correctly disallows reuse — the SAME physical element (at index `i`) can never be picked again in a later step of the same branch, satisfying the "used at most once" constraint, while a DIFFERENT index holding the same value (properly guarded by the skip check) can still legitimately contribute a second occurrence of that value to the sum, if the input actually contains two of it.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Same-level duplicate skip prevents duplicate combinations; index+1 recursion prevents reuse of the same element">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="30" width="30" height="30" fill="#3fb950"/><text x="35" y="50" fill="#0d1117" text-anchor="middle">1a</text>
    <rect x="60" y="30" width="30" height="30" fill="#161b22" stroke="#f85149"/><text x="75" y="50" fill="#e6edf3" text-anchor="middle">1b</text>
    <text x="100" y="50" fill="#f85149">skip at this level</text>
    <text x="10" y="90" fill="#e6edf3">but deeper in the SAME branch, after 1a is placed, 1b (different index) can still be chosen next</text>
  </g>
</svg>

At a given decision point, only the first occurrence of a repeated value is tried; a later occurrence of that same value can still contribute deeper in the same branch, once reached at its own turn.

## 5. Runnable example

```java
// CombinationSumII.java
import java.util.*;

public class CombinationSumII {

    // Level 1 -- Brute force: run Combination Sum's reuse-allowed
    // logic restricted to using each ORIGINAL index at most once (via
    // i+1 recursion), then deduplicate the final result list with a
    // Set<List<Integer>>. Correct, but wastes time generating and
    // discarding duplicate combinations that the same-level skip would
    // have prevented from being generated at all.

    // KEY INSIGHT: sort + skip-adjacent-duplicate-at-same-level
    // (identical to Subsets II) combined with i+1 recursion (no reuse)
    // -- generates each unique combination exactly once, directly.

    // Level 2 -- Optimal: sort + same-level skip + no-reuse recursion.
    static List<List<Integer>> combinationSum2(int[] candidates, int target) {
        Arrays.sort(candidates);
        List<List<Integer>> result = new ArrayList<>();
        dfs(candidates, target, 0, new ArrayList<>(), result);
        return result;
    }

    static void dfs(int[] candidates, int remaining, int start, List<Integer> path, List<List<Integer>> result) {
        if (remaining == 0) {
            result.add(new ArrayList<>(path));
            return;
        }
        if (remaining < 0) return;

        for (int i = start; i < candidates.length; i++) {
            if (i > start && candidates[i] == candidates[i - 1]) continue;
            path.add(candidates[i]);
            dfs(candidates, remaining - candidates[i], i + 1, path, result);
            path.remove(path.size() - 1);
        }
    }

    // Level 3 -- Hardened: since candidates is sorted, the loop can
    // `break` (not just `continue`) once `candidates[i] > remaining`,
    // as every later candidate is only larger -- a further prune on top
    // of the base `remaining < 0` check inside the recursive call.

    public static void main(String[] args) {
        System.out.println(combinationSum2(new int[]{10,1,2,7,6,1,5}, 8));
        // [[1,1,6],[1,2,5],[1,7],[2,6]]
    }
}
```

**How to run:** `java CombinationSumII.java`

## 6. Walkthrough

Trace `dfs` on sorted `candidates = [1,1,2,5,6,7,10]`, `remaining = 8`:

| Path built | remaining reaches | Outcome |
|---|---|---|
| [1,1,2] then any of 5,6,7,10 | negative | all overshoot, pruned |
| [1,1,5] then any of 6,7,10 | negative | all overshoot, pruned |
| [1,1,6] | 0 | save `[1,1,6]` |
| [1,2,5] | 0 | save `[1,2,5]` |
| [1,7] | 0 | save `[1,7]` |
| [2,6] | 0 | save `[2,6]` |

At the top level, index 1 (the second `1`) is skipped since index 0's `1` was tried first at that same level; deeper in the tree, once index 0's `1` is already part of the path, index 1's `1` becomes a valid next choice (seen in `[1,1,6]`). All 4 expected combinations are produced, with the same-level skip preventing any duplicate. Time complexity is exponential in the worst case, bounded by the number of valid and pruned branches; space is O(target / min value) for recursion depth, plus the output size.

## 7. Gotchas & takeaways

> Gotcha: applying the duplicate-skip check `i > start && candidates[i] == candidates[i-1]` is correct here, but combining it with `i` (reuse) instead of `i + 1` (no reuse) recursion would incorrectly allow the SAME index to be picked twice, since the skip logic alone does not prevent single-element reuse — only the recursive call's start argument does.

- The duplicate-skip logic is identical across Subsets II, Permutations II, and this problem — only the "what changes between recursive calls" (index-based `start`/`i+1` versus `used` array) differs to match each problem's own shape.
- The `remaining < 0` prune and a sorted-array early `break` together keep this efficient despite duplicates and a sum constraint stacked together.
- Related problems: Combination Sum (reuse allowed, no duplicates in input), Subsets II (same duplicate-skip trick, no sum constraint).
