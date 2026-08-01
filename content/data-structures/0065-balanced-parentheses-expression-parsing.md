---
card: data-structures
gi: 65
slug: balanced-parentheses-expression-parsing
title: Balanced-parentheses & expression parsing
---

## 1. What it is

**Balanced-parentheses checking** verifies that every opening bracket (`(`, `[`, `{`) in a string has a matching closing bracket, in the correct nested order — `([]){}` is balanced, `([)]` is not, even though it has the same count of each bracket type. This is the canonical use of a stack in expression parsing.

## 2. Why & when

Compilers and interpreters use this exact check to validate syntax before parsing an expression further. It also shows up directly as a common interview problem, because it tests whether you recognize that "most recently opened, must close first" is a LIFO relationship — the same shape as a stack.

## 3. Core concept

**Key idea in one sentence.** Push every opening bracket onto a stack; when a closing bracket appears, it must match whatever is currently on top of the stack, since that is the most recently opened, still-unclosed bracket.

**The algorithm, step by step.**
1. Walk the string left to right, one character at a time.
2. If the character is an opening bracket, push it.
3. If it is a closing bracket, check the stack is not empty and its top matches this closing bracket's type; if either check fails, the string is unbalanced — stop.
4. If it matches, pop the stack (that bracket is now closed) and continue.
5. After the walk, the string is balanced only if the stack is empty — an empty stack means every opened bracket was eventually closed.

**Why it works.** Nesting is inherently LIFO: the innermost, most-recently-opened bracket must be the first one to close. A stack's `push`-on-open and `pop`-on-close naturally enforces exactly this rule, without any extra bookkeeping.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Scanning the string open-paren open-bracket close-bracket close-paren left to right, pushing opening brackets and popping on matching closing brackets, ending with an empty stack">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="20" fill="#8b949e">input: ( [ ] )</text>
    <text x="20" y="45" fill="#e6edf3">step 1: push (   -&gt; stack: [ ( ]</text>
    <text x="20" y="65" fill="#e6edf3">step 2: push [   -&gt; stack: [ ( [ ]</text>
    <text x="20" y="85" fill="#79c0ff">step 3: see ]  matches top [  -&gt; pop -&gt; stack: [ ( ]</text>
    <text x="20" y="105" fill="#79c0ff">step 4: see )  matches top (  -&gt; pop -&gt; stack: [ ]</text>
    <text x="20" y="130" fill="#f0883e">stack empty at end -&gt; balanced</text>
    <rect x="380" y="10" width="30" height="26" fill="#161b22" stroke="#8b949e"/><text x="395" y="27" fill="#e6edf3" text-anchor="middle" font-size="9">(</text>
    <rect x="380" y="40" width="30" height="26" fill="#0d1117" stroke="#f0883e"/><text x="395" y="57" fill="#e6edf3" text-anchor="middle" font-size="9">[</text>
    <text x="395" y="85" fill="#8b949e" text-anchor="middle" font-size="9">stack after step 2</text>
  </g>
</svg>

Each closing bracket must match whatever is currently on top; a mismatch or an empty stack at the wrong moment means the string is unbalanced.

## 5. Runnable example

```java
// BalancedParentheses.java
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Map;

public class BalancedParentheses {

    // Level 1: brute force -- but there is no simpler correct approach without a stack;
    // the naive attempt is counting brackets, which is wrong because it ignores order (see KEY INSIGHT).
    static boolean isBalancedByCountingOnly(String s) {
        int round = 0, square = 0, curly = 0;
        for (char c : s.toCharArray()) {
            if (c == '(') round++; else if (c == ')') round--;
            if (c == '[') square++; else if (c == ']') square--;
            if (c == '{') curly++; else if (c == '}') curly--;
        }
        return round == 0 && square == 0 && curly == 0; // WRONG: passes "([)]" incorrectly
    }

    static void basicLevel() {
        System.out.println("basic: counting-only check on \"([)]\" (should be false, but counting says) -> "
            + isBalancedByCountingOnly("([)]"));
    }

    // KEY INSIGHT: matching counts is not enough -- ORDER matters. A stack enforces order for free.

    // Level 2: optimal -- stack-based, correctly rejects out-of-order nesting.
    static final Map<Character, Character> CLOSE_TO_OPEN = Map.of(')', '(', ']', '[', '}', '{');

    static boolean isBalanced(String s) {
        Deque<Character> stack = new ArrayDeque<>();
        for (char c : s.toCharArray()) {
            if (c == '(' || c == '[' || c == '{') {
                stack.push(c);
            } else if (CLOSE_TO_OPEN.containsKey(c)) {
                if (stack.isEmpty() || stack.pop() != CLOSE_TO_OPEN.get(c)) return false;
            }
        }
        return stack.isEmpty();
    }

    static void intermediateLevel() {
        System.out.println("intermediate: isBalanced(\"([)]\") -> " + isBalanced("([)]"));   // false
        System.out.println("intermediate: isBalanced(\"([]){}\") -> " + isBalanced("([]){}")); // true
    }

    // Level 3: hardened -- empty string, unmatched opener, unmatched closer, and non-bracket characters mixed in.
    static void advancedLevel() {
        System.out.println("advanced: isBalanced(\"\") -> " + isBalanced(""));               // true, vacuously
        System.out.println("advanced: isBalanced(\"(a+b\") -> " + isBalanced("(a+b"));         // false: unclosed opener
        System.out.println("advanced: isBalanced(\"a+b)\") -> " + isBalanced("a+b)"));         // false: closer with no opener
        System.out.println("advanced: isBalanced(\"f(x[i]) + {y}\") -> " + isBalanced("f(x[i]) + {y}")); // true
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `BalancedParentheses.java`, then run `java BalancedParentheses.java`.

## 6. Walkthrough

Dry-run `isBalanced("([)]")`:

| char | action | stack after |
|---|---|---|
| `(` | push | `(` |
| `[` | push | `( [` |
| `)` | closing; top is `[`, expected `(` for `)` — mismatch | **return false** |

The counting-only version would have said `true` here (one `(`, one `)`, one `[`, one `]` — counts balance), which is exactly why counting alone is wrong: it ignores nesting order.

Dry-run `isBalanced("([]){}")`:

| char | action | stack after |
|---|---|---|
| `(` | push | `(` |
| `[` | push | `( [` |
| `]` | matches top `[` — pop | `(` |
| `)` | matches top `(` — pop | *(empty)* |
| `{` | push | `{` |
| `}` | matches top `{` — pop | *(empty)* |

Stack is empty at the end — balanced. Time complexity is O(n), one pass; space is O(n) worst case, for a string of all opening brackets.

## 7. Gotchas & takeaways

> Gotcha: checking `stack.pop() != CLOSE_TO_OPEN.get(c)` before checking `stack.isEmpty()` throws on an empty stack — always check emptiness first (short-circuit `||` handles this correctly above, since Java evaluates left to right and skips `pop()` if `isEmpty()` is true).

- Counting brackets is not enough; nesting order matters, and only a stack (LIFO) enforces it correctly.
- Push on every opening bracket; on a closing bracket, it must match the top of the stack, or the string is unbalanced.
- The string is balanced only if the stack is empty at the very end — a non-empty stack means some opener was never closed.
- Related concepts: [LIFO semantics](0062-lifo-semantics.md), [Infix / postfix / prefix evaluation](0066-infix-postfix-prefix-evaluation.md).
