---
card: leetcode-patterns
gi: 218
slug: combinations
title: Combinations
---

## 1. What it is

Given two integers `n` and `k`, return all possible combinations of `k` numbers chosen from the range `[1, n]`. Example: `n = 4`, `k = 2` → `[[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]`.

## 2. Why & when

This is the Subsets template restricted to a FIXED output size: instead of collecting every partial state (as Subsets does), only collect a result when the partial list's length reaches exactly `k`, and stop recursing deeper once that size is reached.

## 3. Core concept

**Key idea:** DFS from `1` to `n`, using a `start` index exactly like Subsets, but only add to the results when `path.size() == k` — and PRUNE the search by returning early once that size is reached, since a combination cannot grow beyond `k` elements.

**Steps:**
1. Call a recursive helper with an empty partial list and a starting value of `1`.
2. If `path.size() == k`, save a copy of `path` to the results and return (no further recursion needed — this branch is complete).
3. Otherwise, loop `i` from `start` to `n`: add `i` to `path`, recurse with `start = i + 1`, then remove `i` (backtrack) before trying the next `i`.
4. Return the collected results once the initial call completes.

**Why it is correct:** using a `start` index (never revisiting earlier numbers) generates each combination in exactly one canonical increasing order, so no combination is produced twice. Stopping recursion the moment `path.size() == k` correctly prunes branches that could never produce a valid-size combination, avoiding wasted exploration.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DFS with a start index, only saving results and stopping recursion once size k is reached">
  <g font-family="sans-serif" font-size="12">
    <circle cx="80" cy="30" r="4" fill="#e6edf3"/>
    <line x1="80" y1="30" x2="40" y2="70" stroke="#3fb950"/>
    <line x1="80" y1="30" x2="80" y2="70" stroke="#79c0ff"/>
    <line x1="80" y1="30" x2="120" y2="70" stroke="#e3b341"/>
    <circle cx="40" cy="70" r="4" fill="#e6edf3"/><circle cx="80" cy="70" r="4" fill="#e6edf3"/><circle cx="120" cy="70" r="4" fill="#e6edf3"/>
    <text x="10" y="15" fill="#e6edf3">at depth k (here k=2), every node saves a result and recursion stops -- no deeper exploration needed</text>
  </g>
</svg>

Once the partial combination reaches size `k`, it is saved and the branch stops — no need to try any further extensions.

## 5. Runnable example

```java
// Combinations.java
import java.util.*;

public class Combinations {

    // Level 1 -- Brute force: generate ALL subsets (using the full
    // Subsets template, collecting at every node), then filter the
    // final list to keep only those with exactly k elements. Correct,
    // but wastes time generating and discarding subsets of every OTHER
    // size, instead of pruning them away during the search itself.

    // KEY INSIGHT: check `path.size() == k` and RETURN immediately once
    // reached -- this prunes the whole subtree beyond size k, so the
    // search only ever explores paths that could still become valid,
    // instead of exploring the full subset tree and filtering after.

    // Level 2 -- Optimal: DFS with start index, save-and-stop at size
    // k.
    static List<List<Integer>> combine(int n, int k) {
        List<List<Integer>> result = new ArrayList<>();
        dfs(n, k, 1, new ArrayList<>(), result);
        return result;
    }

    static void dfs(int n, int k, int start, List<Integer> path, List<List<Integer>> result) {
        if (path.size() == k) {
            result.add(new ArrayList<>(path));
            return;
        }
        for (int i = start; i <= n; i++) {
            path.add(i);
            dfs(n, k, i + 1, path, result);
            path.remove(path.size() - 1);
        }
    }

    // Level 3 -- Hardened: an additional pruning check `if (n - i + 1
    // < k - path.size()) break;` (not shown above, but a common
    // optimization) can stop the loop early once too few numbers
    // remain to ever reach size k -- useful for large n, small k
    // performance, though not required for correctness.

    public static void main(String[] args) {
        System.out.println(combine(4, 2));
        // [[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]
    }
}
```

**How to run:** `java Combinations.java`

## 6. Walkthrough

Trace `dfs(4, 2, 1, [], result)`:

| Call | path | Action |
|---|---|---|
| dfs(start=1) | [] | size 0 ≠ 2, loop i=1..4 |
| → dfs(start=2) via i=1 | [1] | size 1 ≠ 2, loop i=2..4 |
| → → dfs(start=3) via i=2 | [1,2] | size 2 == 2, save `[1,2]`, return |
| back at [1], try i=3 | [1,3] | size 2 == 2, save `[1,3]`, return |
| back at [1], try i=4 | [1,4] | size 2 == 2, save `[1,4]`, return |
| back at [], try i=2 | [2] | loop i=3..4, producing `[2,3]`, `[2,4]` |
| back at [], try i=3 | [3] | loop i=4, producing `[3,4]` |

Final results match `[[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]`. Time complexity is O(k · C(n,k)), since there are `C(n,k)` combinations, each costing O(k) to copy; space is O(k · C(n,k)) for the output, plus O(k) for the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: forgetting the `return` after saving a result at `path.size() == k` (falling through into the loop anyway) would try to extend an already-complete combination, generating invalid oversized combinations or wasted recursive calls.

- The `start` index here plays the exact same role as in Subsets — it is what makes this "combinations," not "permutations," since order never matters and no number is revisited.
- The size check acts as BOTH the base case AND a pruning condition — no combination can usefully grow past size `k`, so stopping there is both correct and an efficiency win.
- Related problems: Subsets (the unconstrained-size base case), Combination Sum (adds a sum-target constraint instead of a fixed-size one, allowing REPEATED use of the same number).
