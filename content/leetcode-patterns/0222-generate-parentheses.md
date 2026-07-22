---
card: leetcode-patterns
gi: 222
slug: generate-parentheses
title: Generate Parentheses
---

## 1. What it is

Given `n` pairs of parentheses, return all combinations of well-formed (balanced and correctly nested) parenthesis strings. Example: `n = 3` → `["((()))","(()())","(())()","()(())","()()()"]`.

## 2. Why & when

This is DFS backtracking where the "choices" are `'('` or `')'` at each step, constrained by a validity rule: you can add `'('` if you have not yet used all `n` opens, and you can add `')'` only if doing so would not create more closes than opens SO FAR (which would make the prefix invalid, since it could never become balanced by adding more characters later).

## 3. Core concept

**Key idea:** DFS tracks two counters — `openCount` (opens used so far) and `closeCount` (closes used so far) — instead of a `start` index. At each step, try adding `'('` if `openCount < n`, and try adding `')'` if `closeCount < openCount` (there is an unmatched open to close). A result is saved only when the partial string's length reaches `2n`.

**Steps:**
1. Call a recursive helper with an empty partial string, `openCount = 0`, `closeCount = 0`.
2. Base case: if the partial string's length equals `2n`, save a copy and return.
3. If `openCount < n`, append `'('`, recurse with `openCount + 1`, then remove the last character (backtrack).
4. If `closeCount < openCount`, append `')'`, recurse with `closeCount + 1`, then remove the last character (backtrack).
5. Both conditions are checked independently at each call — one, both, or neither branch may fire depending on the current counts.

**Why it is correct:** the condition `closeCount < openCount` is exactly the rule that a valid parenthesis prefix must never have more closes than opens at any point — enforcing it during generation (rather than checking validity after the fact) means EVERY complete string produced is automatically well-formed, and every well-formed string of length `2n` is reachable by SOME sequence of valid choices. The `openCount < n` condition simply caps total opens at `n`, guaranteeing exactly `n` pairs.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="At each step, add an open if under the limit, or a close if there is an unmatched open to close">
  <g font-family="sans-serif" font-size="12">
    <circle cx="100" cy="30" r="14" fill="#161b22" stroke="#3fb950"/><text x="100" y="34" fill="#e6edf3" text-anchor="middle" font-size="9">"("</text>
    <line x1="100" y1="44" x2="60" y2="80" stroke="#79c0ff"/><text x="30" y="95" fill="#79c0ff" font-size="10">add '(' (0&lt;3)</text>
    <line x1="100" y1="44" x2="140" y2="80" stroke="#e3b341"/><text x="150" y="95" fill="#e3b341" font-size="10">add ')' (1&gt;0)</text>
    <circle cx="60" cy="80" r="14" fill="#161b22" stroke="#79c0ff"/><text x="60" y="84" fill="#e6edf3" text-anchor="middle" font-size="7">"(("</text>
    <circle cx="140" cy="80" r="14" fill="#161b22" stroke="#e3b341"/><text x="140" y="84" fill="#e6edf3" text-anchor="middle" font-size="7">"()"</text>
    <text x="10" y="15" fill="#e6edf3">both branches can fire when both conditions hold, producing every valid continuation</text>
  </g>
</svg>

At each step, adding `'('` is allowed while under the open limit; adding `')'` is allowed only while there is an unmatched open waiting to be closed.

## 5. Runnable example

```java
// GenerateParentheses.java
import java.util.*;

public class GenerateParentheses {

    // Level 1 -- Brute force: generate ALL 2^(2n) strings of length 2n
    // over the alphabet {'(', ')'}, then check each one for balanced
    // validity afterward, keeping only the valid ones. Correct, but
    // wastes enormous time generating and checking invalid strings,
    // instead of only ever generating valid prefixes.

    // KEY INSIGHT: track openCount/closeCount and only ever take a
    // move that KEEPS the prefix potentially valid (`closeCount <
    // openCount` for a close) -- this guarantees every generated
    // string is automatically well-formed, no post-hoc validity check
    // needed.

    // Level 2 -- Optimal: DFS backtracking with a validity-preserving
    // constraint.
    static List<String> generateParenthesis(int n) {
        List<String> result = new ArrayList<>();
        dfs(n, 0, 0, new StringBuilder(), result);
        return result;
    }

    static void dfs(int n, int openCount, int closeCount, StringBuilder path, List<String> result) {
        if (path.length() == 2 * n) {
            result.add(path.toString());
            return;
        }
        if (openCount < n) {
            path.append('(');
            dfs(n, openCount + 1, closeCount, path, result);
            path.deleteCharAt(path.length() - 1);
        }
        if (closeCount < openCount) {
            path.append(')');
            dfs(n, openCount, closeCount + 1, path, result);
            path.deleteCharAt(path.length() - 1);
        }
    }

    // Level 3 -- Hardened: n == 0 correctly returns a single empty
    // string `[""]`, since the base case `path.length() == 0` is
    // immediately true and neither branch condition can fire
    // (openCount < 0 is false).

    public static void main(String[] args) {
        System.out.println(generateParenthesis(3));
        // [((())), (()()), (())(), ()(()), ()()()]
    }
}
```

**How to run:** `java GenerateParentheses.java`

## 6. Walkthrough

Trace `dfs(n=2, 0, 0, "", result)`:

| Call | path | openCount | closeCount | Branches tried |
|---|---|---|---|---|
| dfs | "" | 0 | 0 | open<2 → try '(' |
| → dfs | "(" | 1 | 0 | open<2 → try '('; close<1 → try ')' |
| → → dfs (via '(') | "((" | 2 | 0 | open not <2; close<2 → try ')' |
| → → → dfs | "(()" | 2 | 1 | close<2 → try ')' |
| → → → → dfs | "(())" | 2 | 2 | length==4, save "(())" |
| back to "((", try nothing else (open exhausted) | — | — | — | — |
| back to "(", try ')' branch | "()" | 1 | 1 | open<2 → try '(' |
| → dfs | "()(" | 2 | 1 | close<2 → try ')' |
| → → dfs | "()()" | 2 | 2 | length==4, save "()()" |

Both `"(())"` and `"()()"` are found this way — the full run produces all `Catalan(2) = 2` valid strings for `n=2`. Time complexity is O(4ⁿ / √n) (the nth Catalan number, times O(n) per string to build), which is the exact count of valid parenthesization strings; space matches, for the output, plus O(n) for the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: using `closeCount < n` instead of `closeCount < openCount` as the condition for adding a close parenthesis would allow closing before an open has been placed to match it, generating invalid strings like `")("`.

- The output size here is the Catalan number `C(n)`, not `2ⁿ` or `n!` — a different, smaller-growing sequence that still requires exponential-ish generation, but the validity constraint prunes the tree significantly compared to the full binary-string space.
- Both `if` conditions (not `if`/`else if`) must be checked independently at each call — at many nodes, BOTH an open and a close are valid next moves, and both branches must be explored.
- Related problems: Letter Combinations of a Phone Number (DFS backtracking with a fixed per-position choice set instead of a validity-based constraint), Combination Sum (DFS backtracking with a sum-based pruning constraint).
