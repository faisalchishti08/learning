---
card: leetcode-patterns
gi: 310
slug: beautiful-arrangement
title: Beautiful Arrangement
---

## 1. What it is

Suppose you have `n` integers labeled `1` to `n`, arranged in any order into `perm[1..n]`. This arrangement is called "beautiful" if, for every position `i` (1-indexed), EITHER `perm[i]` is divisible by `i`, OR `i` is divisible by `perm[i]`. Given `n`, return the number of beautiful arrangements. Example: `n = 2` → `2` (both `[1,2]` and `[2,1]` qualify).

## 2. Why & when

This is a permutation-generation backtracking problem with an EARLY validity check: instead of generating a full permutation and checking it afterward, verify each position's divisibility rule the moment a number is placed there, pruning invalid placements immediately. Use this shape whenever a problem counts or generates permutations, but each individual placement can be validated against a rule BEFORE the rest of the permutation is built.

## 3. Core concept

**Key idea:** fill positions `1` to `n` one at a time. At each position `i`, try every UNUSED number; only proceed if that number satisfies the divisibility rule with `i`.

**Steps:**
1. Track a `used[]` boolean array (size `n + 1`) marking which numbers have already been placed.
2. Define `backtrack(position)`. **Base case:** if `position > n`, a full valid arrangement was built — increment the count, and return.
3. **Loop:** for `num` from `1` to `n`: skip if `used[num]` is true (prune: already placed). Skip if neither `num % position == 0` nor `position % num == 0` (prune: violates the rule).
4. Otherwise, choose `num` (mark `used[num] = true`), recurse to `position + 1`, then un-choose (`used[num] = false`).

**Why it is correct:** checking the divisibility rule at the moment `num` is placed at `position` — rather than waiting until the full permutation is built — prunes an entire invalid subtree immediately, since no later choice can fix an already-broken position. Because every position from `1` to `n` is filled in order, and every number from `1` to `n` is used exactly once (enforced by `used[]`), every fully-completed path corresponds to exactly one distinct beautiful arrangement.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Backtracking search for n=3, checking divisibility at each position and pruning numbers that violate the rule">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">n = 3</text>
    <text x="10" y="45">position 1: any number works (everything is divisible by 1)</text>
    <text x="10" y="65">try num=1 at position 1 -&gt; used=[1]</text>
    <text x="10" y="85">position 2: try num=2 (2%2==0, ok) -&gt; used=[1,2]</text>
    <text x="10" y="105">position 3: try num=3 (3%3==0, ok) -&gt; full arrangement [1,2,3]</text>
    <rect x="10" y="120" width="180" height="24" fill="#3fb950"/><text x="100" y="137" fill="#0d1117" text-anchor="middle" font-size="10">count += 1</text>
  </g>
</svg>

Position 1 always accepts any number, since every number is divisible by 1 — this is why arrangements are often found by placing "harder" numbers first, but simple forward order still works correctly.

## 5. Runnable example

```java
// BeautifulArrangement.java
public class BeautifulArrangement {

    // KEY INSIGHT: check the divisibility rule the moment a number is
    // placed at a position, instead of after building a full
    // permutation -- this prunes invalid subtrees immediately.

    static int count = 0;

    static int countArrangement(int n) {
        count = 0;
        boolean[] used = new boolean[n + 1];
        backtrack(1, n, used);
        return count;
    }

    static void backtrack(int position, int n, boolean[] used) {
        if (position > n) {
            count++; // a full valid arrangement was built
            return;
        }
        for (int num = 1; num <= n; num++) {
            if (used[num]) continue; // prune: already placed
            if (num % position != 0 && position % num != 0) continue; // prune: rule violated

            used[num] = true;               // choose
            backtrack(position + 1, n, used); // recurse
            used[num] = false;              // un-choose
        }
    }

    public static void main(String[] args) {
        System.out.println(countArrangement(2));
        // 2
        System.out.println(countArrangement(3));
        // 3
    }
}
```

**How to run:** `java BeautifulArrangement.java`

## 6. Walkthrough

Trace `countArrangement(3)`:

| position | tried num | rule check | outcome |
|---|---|---|---|
| 1 | 1 | 1%1==0 | choose 1, recurse |
| 2 | 2 | 2%2==0 | choose 2, recurse |
| 3 | 3 | 3%3==0 | choose 3, recurse -&gt; position=4&gt;3, count=1 ([1,2,3]) |
| 2 (after backtrack) | 3 | 3%2!=0, 2%3!=0 | pruned |
| 1 (after backtrack) | 2 | 2%1==0 | choose 2, recurse |
| 2 | 1 | 1%2!=0, but 2%1==0 | choose 1, recurse |
| 3 | 3 | 3%3==0 | choose 3 -&gt; count=2 ([2,1,3]) |
| 1 (after backtrack) | 3 | 3%1==0 | choose 3, recurse |
| 2 | 1 | 2%1==0 | choose 1, recurse |
| 3 | 2 | 2%3!=0, 3%2!=0 | pruned, no valid arrangement starting [3,1,...] |

The three full paths above show `[1,2,3]` and `[2,1,3]` succeeding, and one dead end where no number fits position 3 after `[3,1,...]`. A further branch, starting `[3,2,...]`, succeeds too, giving the full count of `3` valid arrangements for `n=3`. Time complexity is O(k), where `k` is the number of positions still satisfying the divisibility rule at each level — bounded above by O(n!) but pruned heavily in practice. Space is O(n), for the `used` array and recursion depth.

## 7. Gotchas & takeaways

> Gotcha: checking the rule as `num % position == 0 || position % num == 0` (an OR of BOTH directions) is required — checking only one direction (say, only `num % position == 0`) would incorrectly reject valid placements like `position=2, num=1` (`1 % 2 != 0`, but `2 % 1 == 0`).

- Validating each placement immediately, rather than checking a full permutation afterward, is the key optimization that makes this problem tractable for the `n` values typically given (up to `15`).
- Position `1` never prunes anything, since every number is divisible by `1` — the real pruning happens at later positions with stricter divisibility requirements.
- Related problems: Permutations (the base permutation-generation backtracking, with no validity rule), N-Queens (a similar placement-with-immediate-validation backtracking problem, on a 2D board).
