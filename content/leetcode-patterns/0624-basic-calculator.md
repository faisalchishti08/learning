---
card: leetcode-patterns
gi: 624
slug: basic-calculator
title: Basic Calculator
---

## 1. What it is

Given a string `s` representing a valid mathematical expression with integers, `+`, `-`, parentheses `(`, `)`, and spaces (no `*` or `/`), evaluate it and return the result as an integer. Example: `s="1 + 1"` → `2`; `s="(1+(4+5+2)-3)+(6+8)"` → `23`.

## 2. Why & when

Parentheses can nest arbitrarily deep, and each nested group's result must be combined with an outer sign that itself might be negative (like `-(1+2)`) — this "remember the outer context, dive into the inner expression, then come back and apply what was remembered" structure is a direct **stack** signal, where the stack holds the running total and sign that were in effect *before* entering each parenthesis, to be restored (and combined) after that parenthesis closes.

## 3. Core concept

**Key idea:** scan the string left to right, maintaining a running `result` and a `sign` (`+1` or `-1`) that applies to the *next* number encountered. When an opening parenthesis is hit, push the current `result` and `sign` onto a stack (they represent "what to do with whatever comes out of this parenthesis"), then reset `result=0` and `sign=+1` to start evaluating the inner expression fresh. When a closing parenthesis is hit, the inner expression's `result` is complete — pop the saved sign and outer result from the stack, and combine: `result = poppedResult + poppedSign * result`.

**Steps:**
1. Initialize `result = 0`, `sign = 1`, and an empty stack.
2. Scan each character of `s`, skipping spaces:
3. If it is a digit, parse the full multi-digit number (consuming consecutive digit characters), then update `result += sign * number`.
4. If it is `+`, set `sign = 1`. If it is `-`, set `sign = -1`.
5. If it is `(`, push `result` and `sign` onto the stack (in that order, or as a pair), then reset `result = 0` and `sign = 1`.
6. If it is `)`, pop the saved `sign` and saved `result` from the stack, and update `result = savedResult + savedSign * result`.
7. Return `result` after the full scan.

**Why pushing both `result` and `sign` (not just `result`) before entering a parenthesis is necessary:** the sign in effect *outside* the parenthesis (like the `-` in `-(1+2)`) must be applied to the *entire* value that comes out of the parenthesis once it closes, not just to the first term inside it — saving that outer sign on the stack is what lets the closing `)` correctly apply it to the inner expression's complete, evaluated result.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Entering a parenthesis pushes the outer result and sign onto a stack; closing it pops them and combines with the inner result">
  <g font-family="sans-serif" font-size="12">
    <text x="150" y="20" fill="#8b949e" text-anchor="middle">on '(': push (result, sign), reset both</text>
    <rect x="30" y="30" width="240" height="35" fill="#161b22" stroke="#3fb950"/><text x="150" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">stack top: (result=1, sign=+1)</text>
    <text x="530" y="20" fill="#8b949e" text-anchor="middle">on ')': pop, combine</text>
    <rect x="410" y="30" width="240" height="35" fill="#161b22" stroke="#f0883e"/><text x="530" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">result = 1 + 1*innerResult</text>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">the stack remembers "what to do with the parenthesis's value" until it closes</text>
  </g>
</svg>

The stack holds exactly what is needed to resume the outer expression once the inner parenthesized group is fully evaluated — the saved result and the sign that must be applied to the inner value.

## 5. Runnable example

**Level 1 — Brute force.** Recursively evaluate by finding matching parentheses with index scanning, substring-ing out the inner expression, and recursively calling the evaluator on it. Correct, but string substring-ing at every level of nesting adds unnecessary overhead compared to a single linear scan with a stack.

**KEY INSIGHT:** a stack directly models the "remember the outer context, evaluate the inner part fresh, then combine" structure that nested parentheses require — no substring extraction or explicit recursion is needed, since the stack itself plays the role of the call stack a recursive solution would use implicitly.

**Level 2 — Optimal.** Single left-to-right scan with an explicit stack for saved `(result, sign)` pairs, O(n) time, O(n) space (worst case, for deeply nested parentheses).

**Level 3 — Hardened.** Correctly parses multi-digit numbers (not just single digits), correctly skips spaces, and correctly handles a `-` or `+` immediately following `(` (like `-(1+2)`), since the sign variable is reset fresh upon entering each parenthesis.

```java
// BasicCalculator.java
import java.util.*;

public class BasicCalculator {

    public static int calculate(String s) {
        Deque<Integer> stack = new ArrayDeque<>();
        int result = 0;
        int sign = 1;
        int i = 0;

        while (i < s.length()) {
            char c = s.charAt(i);
            if (Character.isDigit(c)) {
                int num = 0;
                while (i < s.length() && Character.isDigit(s.charAt(i))) {
                    num = num * 10 + (s.charAt(i) - '0');
                    i++;
                }
                result += sign * num;
                continue;
            } else if (c == '+') {
                sign = 1;
            } else if (c == '-') {
                sign = -1;
            } else if (c == '(') {
                stack.push(result);
                stack.push(sign);
                result = 0;
                sign = 1;
            } else if (c == ')') {
                int savedSign = stack.pop();
                int savedResult = stack.pop();
                result = savedResult + savedSign * result;
            }
            i++;
        }

        return result;
    }

    public static void main(String[] args) {
        System.out.println(calculate("1 + 1"));                    // 2
        System.out.println(calculate("(1+(4+5+2)-3)+(6+8)"));       // 23
        System.out.println(calculate("2-(5-6)"));                   // 3
    }
}
```

**How to run:** save as `BasicCalculator.java`, then run `java BasicCalculator.java`.

## 6. Walkthrough

Trace `calculate("2-(5-6)")`:

1. `'2'`: parse number `2`. `result = 0 + 1*2 = 2`. `sign` still `1`.
2. `'-'`: `sign = -1`.
3. `'('`: push `(result=2, sign=-1)` onto stack. Reset `result=0, sign=1`.
4. `'5'`: `result = 0 + 1*5 = 5`.
5. `'-'`: `sign = -1`.
6. `'6'`: `result = 5 + (-1)*6 = -1`.
7. `')'`: pop `savedSign=-1`, `savedResult=2`. `result = 2 + (-1)*(-1) = 2 + 1 = 3`.

Final result: `3`, matching `2 - (5 - 6) = 2 - (-1) = 3`.

## 7. Gotchas & takeaways

> Gotcha: forgetting to reset `sign = 1` (not just `result = 0`) upon entering a new `(` causes the *previous* sign to incorrectly leak into the fresh inner expression — each parenthesis starts a clean sub-evaluation with its own default `+` sign until a `+` or `-` character inside it says otherwise.

- Signal: expressions with arbitrarily nested structure (parentheses, brackets, nested scopes) where an outer context must be resumed after an inner one completes is a stack signal — push before descending, pop when returning.
- Multi-digit numbers must be parsed as a complete unit (consuming all consecutive digit characters) before being combined with `sign`, not digit by digit.
- Related problems: Basic Calculator II (adds `*` and `/`, needing operator precedence handling instead of, or in addition to, the stack-based parenthesis handling here), Evaluate Reverse Polish Notation (a different stack application, for postfix expressions with no parentheses at all).
