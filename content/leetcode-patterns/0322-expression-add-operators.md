---
card: leetcode-patterns
gi: 322
slug: expression-add-operators
title: Expression Add Operators
---

## 1. What it is

Given a string `num` containing only digits and an integer `target`, insert the operators `'+'`, `'-'`, or `'*'` between digits (or insert none) so the resulting expression evaluates to `target`. Return ALL such expressions. Digits cannot be reordered, and no operand may have a leading zero (except the single digit `"0"` itself). Example: `num = "123"`, `target = 6` → `["1+2+3","1*2*3"]`.

## 2. Why & when

This is string-partitioning backtracking (like Restore IP Addresses) combined with expression EVALUATION, made trickier by operator precedence: multiplication binds tighter than addition or subtraction. Use this shape whenever a problem builds an expression piece by piece and must track a runtime VALUE that depends on the operator chosen, especially when precedence rules mean the "last operation" might need to be undone and redone.

## 3. Core concept

**Key idea:** at each step, choose the next operand's length (1 or more digits, no leading zero) and one of the three operators to place before it. Track the RUNNING TOTAL and the value of the LAST term added — so that if the next operator is `'*'`, you can undo the last addition/subtraction and redo it with the correct precedence.

**Steps:**
1. Define `backtrack(index, expression, total, lastTerm)`, where `total` is the expression's value so far, and `lastTerm` is the signed value of the most recently added term.
2. **Base case:** if `index == num.length()`: if `total == target`, record `expression`; return.
3. **Loop over operand length:** for `length` from `1` up to the remaining characters: extract `segment`. Skip if it has a leading zero and `length > 1` (prune). Parse `value = Long.parseLong(segment)` (use `long` for overflow safety).
4. **If this is the FIRST term** (`expression` is empty): recurse with `expression = segment`, `total = value`, `lastTerm = value`.
5. **Otherwise, try all 3 operators:** `'+'`: recurse with `total + value`, `lastTerm = value`. `'-'`: recurse with `total - value`, `lastTerm = -value`. `'*'`: recurse with `total - lastTerm + lastTerm * value` (UNDO the last term from `total`, then redo it multiplied by `value`), `lastTerm = lastTerm * value`.

**Why it is correct:** tracking `lastTerm` separately from `total` is what makes multiplication precedence correct — `total - lastTerm` removes the PREVIOUS term's contribution, and `lastTerm * value` recomputes that term as if it had always been multiplied by `value`, exactly matching how `"2+3*4"` should evaluate as `2 + (3*4) = 14`, not `(2+3)*4 = 20`. Trying every possible operand LENGTH at each step covers every way to split the remaining digits, and the leading-zero prune matches the problem's own rule for valid operands.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Building the expression 1 plus 2 times 3, showing total corrected from 3 to 7 when multiplication is applied to the last term">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">num = "123", building "1+2*3"</text>
    <text x="10" y="45">first term "1" -&gt; total=1, lastTerm=1</text>
    <text x="10" y="65">+"2" -&gt; total=1+2=3, lastTerm=2</text>
    <text x="10" y="85">*"3" -&gt; total = 3 - 2 + (2*3) = 3-2+6 = 7, lastTerm=2*3=6</text>
    <rect x="10" y="100" width="180" height="24" fill="#3fb950"/><text x="100" y="117" fill="#0d1117" text-anchor="middle" font-size="10">"1+2*3" evaluates to 7</text>
  </g>
</svg>

Multiplying requires undoing the previous term's addition before redoing it multiplied, so `total` always reflects correct operator precedence.

## 5. Runnable example

```java
// ExpressionAddOperators.java
import java.util.*;

public class ExpressionAddOperators {

    // KEY INSIGHT: tracking "lastTerm" separately from "total" lets a
    // later '*' undo-and-redo the previous term's contribution,
    // correctly implementing multiplication's higher precedence
    // without a separate expression parser.

    static List<String> addOperators(String num, int target) {
        List<String> results = new ArrayList<>();
        backtrack(num, target, 0, "", 0L, 0L, results);
        return results;
    }

    static void backtrack(String num, int target, int index, String expression,
                           long total, long lastTerm, List<String> results) {
        if (index == num.length()) {
            if (total == target) results.add(expression);
            return;
        }

        for (int length = 1; index + length <= num.length(); length++) {
            String segment = num.substring(index, index + length);
            if (segment.length() > 1 && segment.charAt(0) == '0') break; // prune: leading zero

            long value = Long.parseLong(segment);

            if (index == 0) {
                backtrack(num, target, length, segment, value, value, results);
            } else {
                backtrack(num, target, index + length, expression + "+" + segment,
                        total + value, value, results);
                backtrack(num, target, index + length, expression + "-" + segment,
                        total - value, -value, results);
                backtrack(num, target, index + length, expression + "*" + segment,
                        total - lastTerm + lastTerm * value, lastTerm * value, results);
            }
        }
    }

    public static void main(String[] args) {
        System.out.println(addOperators("123", 6));
        // [1+2+3, 1*2*3]
        System.out.println(addOperators("105", 5));
        // [1*0+5, 10-5]
    }
}
```

**How to run:** `java ExpressionAddOperators.java`

## 6. Walkthrough

Trace one successful path for `addOperators("123", 6)`, building `"1*2*3"`:

| index | expression | total | lastTerm | next segment | operator | new total | new lastTerm |
|---|---|---|---|---|---|---|---|
| 0 | "" (first term) | — | — | "1" | (none) | 1 | 1 |
| 1 | "1" | 1 | 1 | "2" | '*' | 1 - 1 + 1*2 = 2 | 2 |
| 2 | "1*2" | 2 | 2 | "3" | '*' | 2 - 2 + 2*3 = 6 | 6 |
| 3 (index==length) | "1*2*3" | 6 | — | — | — | total==target(6) -&gt; record | — |

Final result includes `"1*2*3"` and, via a different branch, `"1+2+3"`. Time complexity is O(4^n) in the worst case: at each of `n` positions, up to 4 choices (3 operators, or extending the current operand's length by one more digit), though the leading-zero prune and long overflow guard cut this in practice. Space is O(n), for the recursion depth and expression string.

## 7. Gotchas & takeaways

> Gotcha: the FIRST term (at `index == 0`) must never have an operator placed before it — this problem's operators only appear BETWEEN two terms, so special-casing the very first operand (no `'+'`, `'-'`, or `'*'` prefix) is required, unlike every subsequent term.

- The undo-and-redo trick for `'*'` (`total - lastTerm + lastTerm * value`) is the general technique for handling operator precedence in a single left-to-right pass, without building and evaluating a full expression tree.
- Using `long` instead of `int` for `total` and `lastTerm` guards against overflow when multiplying multi-digit operands together, which can exceed 32-bit integer range even for modest input lengths.
- Related problems: Restore IP Addresses (string-partitioning backtracking without operator precedence), Different Ways to Add Parentheses (a related expression-building problem, using divide-and-conquer instead of left-to-right backtracking).
