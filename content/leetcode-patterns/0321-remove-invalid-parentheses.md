---
card: leetcode-patterns
gi: 321
slug: remove-invalid-parentheses
title: Remove Invalid Parentheses
---

## 1. What it is

Given a string `s` containing letters and the characters `'('` and `')'`, remove the MINIMUM number of invalid parentheses so the remaining string is valid (every open parenthesis has a matching close, and none close before they open). Return ALL possible valid results with that minimum number of removals, with no duplicates. Example: `s = "()())()"` → `["(())()","()()()"]`.

## 2. Why & when

This combines counting (how many `'('` and `')'` are actually excess) with backtracking (which specific characters to remove). Use this shape whenever a problem must find the MINIMUM number of removals or changes to satisfy a validity rule, and needs EVERY way of achieving that minimum, not just one.

## 3. Core concept

**Key idea:** first count exactly how many excess `'('` and excess `')'` characters exist (a single left-to-right scan). Then backtrack over the string, at each parenthesis character choosing to either KEEP it or REMOVE it (if removals remain for that character type), pruning any partial string that already has more `')'` than `'('` so far.

**Steps:**
1. Scan `s` left to right, tracking `openCount`. For each `'('`, increment `openCount`. For each `')'`: if `openCount > 0`, decrement it (this `')'` has a matching `'('`); otherwise, this `')'` is EXCESS — increment `removeRight`. After the scan, `removeLeft = openCount` (any `'('` never matched is excess).
2. Define `backtrack(index, openSoFar, removeLeft, removeRight, current)`.
3. **Base case:** if `index == s.length()`: if `removeLeft == 0` and `removeRight == 0` (used up exactly the needed removals), record `current` as a valid result (deduplicated via a `Set`).
4. **Prune:** if `removeLeft < 0` or `removeRight < 0` or `openSoFar < 0`, this branch has already over-removed or gone invalid — stop.
5. **Loop over the current character:** if it is `'('`, try REMOVING it (recurse with `removeLeft - 1`, same `current`) and try KEEPING it (`current + '('`, `openSoFar + 1`). If it is `')'`, try REMOVING it (`removeRight - 1`) and try KEEPING it (`current + ')'`, `openSoFar - 1`, only if `openSoFar > 0`). Any other character is always kept unchanged.

**Why it is correct:** `removeLeft` and `removeRight` are computed as the EXACT minimum number of each type of excess parenthesis, so any solution achieving validity with fewer total removals is impossible — the search only explores paths that use up exactly this minimum. Tracking `openSoFar` and pruning the moment it goes negative stops any branch where a `')'` is kept without a matching earlier `'('`, enforcing validity incrementally instead of checking the whole string only at the end.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="At each parenthesis character, branching into keep and remove, pruning branches where open count goes negative or removal budgets are exceeded">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s = "()())()"  -&gt; removeLeft=0, removeRight=1 (one excess ')')</text>
    <text x="10" y="45">index 0 '(' -&gt; keep (removeLeft=0, can't remove) -&gt; current="(", open=1</text>
    <text x="10" y="65">index 1 ')' -&gt; keep -&gt; current="()", open=0</text>
    <text x="10" y="85">index 2 '(' -&gt; keep -&gt; current="()(", open=1</text>
    <text x="10" y="105">index 3 ')' -&gt; keep -&gt; current="()()", open=0</text>
    <text x="10" y="125">index 4 ')' -&gt; REMOVE (uses removeRight budget) -&gt; current="()()", removeRight=0</text>
    <rect x="10" y="135" width="160" height="24" fill="#3fb950"/><text x="90" y="152" fill="#0d1117" text-anchor="middle" font-size="10">continues to "()()()"</text>
  </g>
</svg>

Each `'('` or `')'` branches into keep-or-remove, with pruning stopping invalid partial states immediately.

## 5. Runnable example

```java
// RemoveInvalidParentheses.java
import java.util.*;

public class RemoveInvalidParentheses {

    // KEY INSIGHT: compute the EXACT minimum removals needed for each
    // parenthesis type first, then backtrack only over paths that use
    // exactly that many removals -- guaranteeing every result found
    // uses the true minimum, with no extra validity check needed.

    static List<String> removeInvalidParentheses(String s) {
        int removeLeft = 0, removeRight = 0;
        int openCount = 0;
        for (char c : s.toCharArray()) {
            if (c == '(') openCount++;
            else if (c == ')') {
                if (openCount > 0) openCount--;
                else removeRight++;
            }
        }
        removeLeft = openCount;

        Set<String> results = new HashSet<>();
        backtrack(s, 0, 0, removeLeft, removeRight, new StringBuilder(), results);
        return new ArrayList<>(results);
    }

    static void backtrack(String s, int index, int openSoFar, int removeLeft, int removeRight,
                           StringBuilder current, Set<String> results) {
        if (removeLeft < 0 || removeRight < 0 || openSoFar < 0) return; // prune

        if (index == s.length()) {
            if (removeLeft == 0 && removeRight == 0 && openSoFar == 0) {
                results.add(current.toString());
            }
            return;
        }

        char c = s.charAt(index);
        int len = current.length();

        if (c == '(') {
            backtrack(s, index + 1, openSoFar, removeLeft - 1, removeRight, current, results); // remove
            current.append(c);
            backtrack(s, index + 1, openSoFar + 1, removeLeft, removeRight, current, results); // keep
            current.setLength(len);
        } else if (c == ')') {
            backtrack(s, index + 1, openSoFar, removeLeft, removeRight - 1, current, results); // remove
            current.append(c);
            backtrack(s, index + 1, openSoFar - 1, removeLeft, removeRight, current, results); // keep
            current.setLength(len);
        } else {
            current.append(c);
            backtrack(s, index + 1, openSoFar, removeLeft, removeRight, current, results);
            current.setLength(len);
        }
    }

    public static void main(String[] args) {
        List<String> result = removeInvalidParentheses("()())()");
        Collections.sort(result);
        System.out.println(result);
        // [(())(), ()()()]
    }
}
```

**How to run:** `java RemoveInvalidParentheses.java`

## 6. Walkthrough

For `s = "()())()"`, the initial scan finds `removeLeft = 0`, `removeRight = 1` (the 5th character, index 4, is an unmatched `')'`). The backtracking search then explores every way to either keep or remove each parenthesis, subject to using EXACTLY 0 left-removals and 1 right-removal, and never letting `openSoFar` go negative. Two distinct maximal valid strings survive: `"(())()"` (removing the `')'` at index 2) and `"()()()"` (removing the `')'` at index 4). Time complexity is O(2^n) in the worst case (each of `n` parenthesis characters branches into keep/remove), heavily pruned by the `removeLeft`/`removeRight`/`openSoFar` checks. Space is O(n), for the recursion depth and the current string builder.

## 7. Gotchas & takeaways

> Gotcha: using a plain `List` instead of a `Set` for `results` would allow the SAME valid string to be recorded multiple times, since different sequences of remove/keep choices can produce the identical final string — deduplication via a `Set` (or an equivalent index-based technique) is required by the problem's "no duplicates" rule.

- Computing the exact `removeLeft`/`removeRight` minimums BEFORE searching is what guarantees every found result is optimal — searching without this upfront count would require comparing removal counts across all found results afterward, a much more wasteful approach.
- The `openSoFar < 0` prune enforces validity INCREMENTALLY (a `')'` is only kept if a matching `'('` was already kept), avoiding the need for a separate "is this string balanced" check at the very end.
- Related problems: Valid Parentheses (checking validity, no removal), Generate Parentheses (building valid strings from scratch, a related but distinct backtracking problem).
