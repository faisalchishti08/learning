---
card: data-structures
gi: 66
slug: infix-postfix-prefix-evaluation
title: Infix / postfix / prefix evaluation
---

## 1. What it is

**Infix** notation writes an operator between its operands, like `3 + 4`, the form humans normally use — it needs parentheses and precedence rules (`*` before `+`) to be unambiguous. **Postfix** (Reverse Polish Notation) writes the operator after its operands, like `3 4 +`. **Prefix** writes it before, like `+ 3 4`. Postfix and prefix need no parentheses and no precedence rules, because the order of operators and operands alone fully determines how to evaluate them.

## 2. Why & when

Postfix is what calculators and low-level interpreters actually evaluate, because it maps directly onto a stack machine — no need to track operator precedence or parenthesis nesting at evaluation time. Understanding this shows up whenever you build a simple expression evaluator or a calculator, and it is a classic use of a stack beyond bracket matching.

## 3. Core concept

**Evaluating postfix with a stack — the idea.** Scan left to right. Push every number. When you hit an operator, pop the top two numbers, apply the operator, and push the result back. At the end, exactly one number remains on the stack: the answer.

**Why this works.** In postfix, by the time you reach an operator, its two operands have always already appeared and are sitting on top of the stack — postfix guarantees operands come before the operator that uses them, so a stack (which only exposes "the most recent things") always has exactly the right two values on top.

**Operand order matters for non-commutative operators.** For `-` and `/`, pop order matters: the *second*-popped value is the left operand, the *first*-popped value is the right operand, since it was pushed later (closer to the operator). For `a b -`, you compute `a - b`, not `b - a`.

**Converting infix to postfix (brief).** The **shunting-yard algorithm** uses a second stack to hold operators temporarily, popping higher-or-equal precedence operators to the output before pushing a new one, and handling parentheses by pushing `(` and popping until `(` on `)`. This topic focuses on evaluation; conversion is a related, separate algorithm.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Evaluating the postfix expression 3 4 plus 2 star by pushing numbers and popping two operands per operator">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="18" fill="#8b949e">postfix: 3 4 + 2 *</text>
    <text x="20" y="42" fill="#e6edf3">push 3 -&gt; [3]</text>
    <text x="20" y="62" fill="#e6edf3">push 4 -&gt; [3, 4]</text>
    <text x="20" y="82" fill="#79c0ff">"+" : pop 4, pop 3, push 3+4=7 -&gt; [7]</text>
    <text x="20" y="102" fill="#e6edf3">push 2 -&gt; [7, 2]</text>
    <text x="20" y="122" fill="#79c0ff">"*" : pop 2, pop 7, push 7*2=14 -&gt; [14]</text>
    <text x="20" y="150" fill="#f0883e">one value left -&gt; result = 14</text>
    <rect x="420" y="60" width="40" height="26" fill="#0d1117" stroke="#f0883e"/><text x="440" y="77" fill="#e6edf3" text-anchor="middle" font-size="9">14</text>
    <text x="440" y="105" fill="#8b949e" text-anchor="middle" font-size="9">final stack</text>
  </g>
</svg>

Every operator consumes the two most recently pushed values and pushes back a single combined result.

## 5. Runnable example

```java
// PostfixEvaluator.java
import java.util.ArrayDeque;
import java.util.Deque;

public class PostfixEvaluator {

    // Basic: evaluate a simple postfix expression with all four operators.
    static int evaluatePostfix(String expression) {
        Deque<Integer> stack = new ArrayDeque<>();
        for (String token : expression.trim().split("\\s+")) {
            if (isOperator(token)) {
                int right = stack.pop(); // popped second operand: pushed most recently
                int left = stack.pop();  // popped first operand: pushed before that
                stack.push(apply(left, right, token.charAt(0)));
            } else {
                stack.push(Integer.parseInt(token));
            }
        }
        return stack.pop();
    }

    static boolean isOperator(String token) {
        return token.length() == 1 && "+-*/".contains(token);
    }

    static int apply(int left, int right, char op) {
        switch (op) {
            case '+': return left + right;
            case '-': return left - right; // order matters: left - right, not right - left
            case '*': return left * right;
            case '/': return left / right; // order matters: left / right
            default: throw new IllegalArgumentException("unknown operator: " + op);
        }
    }

    static void basicLevel() {
        System.out.println("basic: \"3 4 +\" -> " + evaluatePostfix("3 4 +"));       // 7
        System.out.println("basic: \"3 4 + 2 *\" -> " + evaluatePostfix("3 4 + 2 *")); // 14
    }

    // Intermediate: an expression where operand order changes the result, proving pop order matters.
    static void intermediateLevel() {
        System.out.println("intermediate: \"10 2 -\" (10 - 2) -> " + evaluatePostfix("10 2 -"));   // 8
        System.out.println("intermediate: \"2 10 -\" (2 - 10) -> " + evaluatePostfix("2 10 -"));    // -8
        System.out.println("intermediate: \"20 4 /\" (20 / 4) -> " + evaluatePostfix("20 4 /"));    // 5
    }

    // Advanced: a longer, nested-precedence expression that would need parentheses in infix but needs none here.
    static void advancedLevel() {
        // infix equivalent: (5 + 3) * (10 - 4) / 2
        String postfix = "5 3 + 10 4 - * 2 /";
        System.out.println("advanced: \"" + postfix + "\" -> " + evaluatePostfix(postfix)); // (8 * 6) / 2 = 24
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `PostfixEvaluator.java`, then run `java PostfixEvaluator.java`.

## 6. Walkthrough

Dry-run `evaluatePostfix("5 3 + 10 4 - * 2 /")` — the infix equivalent is `(5 + 3) * (10 - 4) / 2`:

| token | action | stack after |
|---|---|---|
| `5` | push | `[5]` |
| `3` | push | `[5, 3]` |
| `+` | pop 3, pop 5, push 5+3=8 | `[8]` |
| `10` | push | `[8, 10]` |
| `4` | push | `[8, 10, 4]` |
| `-` | pop 4, pop 10, push 10-4=6 | `[8, 6]` |
| `*` | pop 6, pop 8, push 8*6=48 | `[48]` |
| `2` | push | `[48, 2]` |
| `/` | pop 2, pop 48, push 48/2=24 | `[24]` |

One value remains: `24`. Notice the expression never needed parentheses — the position of each operator, right after its two operands, already fixed the evaluation order.

## 7. Gotchas & takeaways

> Gotcha: for `-` and `/`, swapping which popped value is `left` and which is `right` silently flips the answer's sign (or produces the reciprocal-ish wrong quotient) without throwing any error — always assign the **first** pop to `right` and the **second** pop to `left`, since the right operand was pushed last, closer to the operator.

- Postfix removes the need for parentheses and precedence rules, because operator position alone determines evaluation order.
- Evaluate postfix with a stack: push numbers, and on an operator pop two, apply, push the result.
- Pop order matters for non-commutative operators (`-`, `/`) — the second pop is the left operand.
- Related concepts: [Balanced-parentheses & expression parsing](0065-balanced-parentheses-expression-parsing.md), [LIFO semantics](0062-lifo-semantics.md).
