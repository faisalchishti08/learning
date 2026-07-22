---
card: leetcode-patterns
gi: 219
slug: combination-sum
title: Combination Sum
---

## 1. What it is

Given a distinct array `candidates` and a `target`, return all UNIQUE combinations where the chosen numbers sum to `target`. The SAME number may be chosen an UNLIMITED number of times. Example: `candidates = [2,3,6,7]`, `target = 7` → `[[2,2,3],[7]]`.

## 2. Why & when

This is Combinations with a sum constraint instead of a size constraint, plus one crucial twist: since the same number can be reused, the recursive call passes the SAME `start` index (not `start + 1`) when including a number — allowing it to be picked again in the same branch.

## 3. Core concept

**Key idea:** DFS from index `0`, tracking a running sum instead of a running size. At each step, try including `candidates[i]` (recursing with the SAME `i`, since reuse is allowed) or moving on to `candidates[i+1]` without including it. PRUNE any branch where the running sum exceeds `target` — no further additions can bring it back down.

**Steps:**
1. Call a recursive helper with an empty partial list, a starting index of `0`, and a `remaining` value initialized to `target`.
2. If `remaining == 0`, save a copy of `path` to the results and return (found a valid combination).
3. If `remaining < 0`, return immediately (this branch overshot the target — prune it).
4. Loop `i` from `start` to the end of `candidates`: add `candidates[i]` to `path`, recurse with `start = i` (NOT `i + 1`, allowing reuse) and `remaining - candidates[i]`, then remove `candidates[i]` (backtrack).

**Why it is correct:** passing the SAME index `i` (instead of `i + 1`) on the recursive call is exactly what permits choosing the same number multiple times, since a future call can still select `candidates[i]` again. Using `start` (never going BACKWARD to earlier indices) still prevents generating the same combination in a different order — e.g. `[2,2,3]` is generated, but `[2,3,2]` and `[3,2,2]` are not, since going backward is disallowed. The `remaining < 0` prune cuts off branches early, avoiding wasted exploration of sums that can only get worse.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Recursing with the same index allows reusing a number; recursing with index+1 moves on without reuse">
  <g font-family="sans-serif" font-size="12">
    <circle cx="100" cy="30" r="14" fill="#161b22" stroke="#3fb950"/><text x="100" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">[2]</text>
    <line x1="100" y1="44" x2="70" y2="80" stroke="#79c0ff"/><text x="40" y="95" fill="#79c0ff" font-size="10">reuse 2 (same i)</text>
    <line x1="100" y1="44" x2="140" y2="80" stroke="#e3b341"/><text x="150" y="95" fill="#e3b341" font-size="10">move to i+1</text>
    <circle cx="70" cy="80" r="14" fill="#161b22" stroke="#79c0ff"/><text x="70" y="84" fill="#e6edf3" text-anchor="middle" font-size="7">[2,2]</text>
    <circle cx="140" cy="80" r="14" fill="#161b22" stroke="#e3b341"/><text x="140" y="84" fill="#e6edf3" text-anchor="middle" font-size="7">[2,3]</text>
    <text x="10" y="15" fill="#e6edf3">the "reuse" branch stays at the same index; the "move on" branch advances past it</text>
  </g>
</svg>

Recursing with the same index lets the branch pick that number again; recursing with the next index moves past it permanently for this branch.

## 5. Runnable example

```java
// CombinationSum.java
import java.util.*;

public class CombinationSum {

    // Level 1 -- Brute force: DFS without a `remaining < 0` prune,
    // exploring every combination up to some depth bound and checking
    // the sum only at the very end. Correct, but wastes enormous time
    // exploring branches that already overshot the target long before
    // reaching a stopping point.

    // KEY INSIGHT: track `remaining` as you go and PRUNE the instant it
    // goes negative -- this cuts off invalid branches as early as
    // possible, instead of letting them run to full depth before being
    // discarded.

    // Level 2 -- Optimal: DFS with same-index reuse + early pruning.
    static List<List<Integer>> combinationSum(int[] candidates, int target) {
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
            path.add(candidates[i]);
            dfs(candidates, remaining - candidates[i], i, path, result);
            path.remove(path.size() - 1);
        }
    }

    // Level 3 -- Hardened: sorting `candidates` first (not shown, but
    // a common addition) lets the loop `break` early once
    // `candidates[i] > remaining`, since every later candidate would
    // only be larger -- a further pruning optimization on top of the
    // `remaining < 0` base check.

    public static void main(String[] args) {
        System.out.println(combinationSum(new int[]{2,3,6,7}, 7)); // [[2,2,3],[7]]
        System.out.println(combinationSum(new int[]{2,3,5}, 8)); // [[2,2,2,2],[2,3,3],[3,5]]
    }
}
```

**How to run:** `java CombinationSum.java`

## 6. Walkthrough

Trace `dfs(candidates=[2,3,6,7], remaining=7, start=0, [], result)`:

| Call | path | remaining | Action |
|---|---|---|---|
| dfs(start=0) | [] | 7 | not 0, not <0, loop i=0 (add 2), recurse with start=0 (reuse allowed) |
| → dfs(start=0) | [2] | 5 | add 2 again, recurse with start=0 |
| → → dfs(start=0) | [2,2] | 3 | add 2 again, recurse with start=0 |
| → → → dfs(start=0) | [2,2,2] | 1 | add 2 again → remaining=-1, prune; backtrack, try i=1 (add 3) → remaining=1-3=-2, prune; try i=2 (add 6)→-5 prune; i=3(7)→-6 prune; loop ends |
| back at [2,2] | [2,2] | 3 | try i=1 (add 3), recurse start=1 | 
| → dfs(start=1) | [2,2,3] | 0 | remaining==0, save `[2,2,3]`, return |

Continuing the backtrack eventually also finds `[7]` via the `i=3` branch at the top level. Time complexity is exponential in the worst case (bounded by the number of valid combinations and pruned branches), roughly O(2^target / min(candidates)); space is O(target / min(candidates)) for the recursion depth, plus the output size.

## 7. Gotchas & takeaways

> Gotcha: recursing with `i + 1` instead of `i` (copying the Combinations template without adjusting for reuse) silently disallows picking the same number twice, producing wrong results for any target that requires repetition (like `[2,2,3]` for target 7).

- The `remaining < 0` prune is not just an optimization here — without it, the recursion could run indefinitely deep for candidates that include very small numbers (like `1`), since reuse is unlimited.
- Sorting `candidates` first enables an even tighter prune (`break` the loop once `candidates[i] > remaining`), since all later candidates would only be larger — worth adding for performance, though not required for correctness.
- Related problems: Combination Sum II (no reuse allowed, has duplicates in input, needs the same-level skip trick instead), Combinations (fixed size instead of a sum target, no reuse).
