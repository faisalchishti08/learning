---
card: java
gi: 293
slug: stack
title: Stack
---

## 1. What it is

`Stack` is a legacy class representing a classic last-in-first-out (LIFO) stack of objects, where the most recently pushed element is the first one popped. It extends `Vector`, inheriting all of `Vector`'s list methods (`get`, `add`, `remove` at arbitrary positions) in addition to its own stack-specific operations: `push`, `pop`, `peek`, and `empty`.

```java
import java.util.Stack;

public class StackDemo {
    public static void main(String[] args) {
        Stack<String> stack = new Stack<>();
        stack.push("first");
        stack.push("second");
        stack.push("third");

        System.out.println(stack.pop());  // "third" -- last one in, first one out
        System.out.println(stack.peek()); // "second" -- look without removing
        System.out.println(stack);        // [first, second]
    }
}
```

`push` adds to the top, `pop` removes and returns the top, and `peek` returns the top without removing it — `pop` on an empty stack throws `EmptyStackException`, so callers should check `empty()` or `isEmpty()` first when the stack might be empty.

## 2. Why & when

Stacks (the abstract data structure) are fundamental to countless algorithms: expression evaluation, undo history, backtracking, and the call stack itself. Java's `Stack` class was the original, Java-1.0-era implementation of that idea.

- **LIFO-ordered processing** — undo/redo history, balanced-parenthesis checking, and depth-first traversal all naturally use last-in-first-out order.
- **Simple, familiar API** — `push`/`pop`/`peek` map directly onto the textbook stack data structure that most programmers already know.
- **Legacy code compatibility** — you'll still see `Stack` in older codebases and in some standard-library internals.

For new code, the official Java documentation itself recommends `Deque` (specifically `ArrayDeque`) over `Stack`: `ArrayDeque` is faster (no unnecessary synchronization, unlike `Vector`-derived `Stack`) and, critically, **doesn't** expose `Vector`'s arbitrary-position `get`/`insert`/`remove` methods that let code accidentally violate the stack's LIFO discipline. `Stack` is worth knowing to read legacy code and to understand the LIFO concept, but `ArrayDeque` (used via its `push`/`pop`/`peek` methods) is the modern choice.

## 3. Core concept

```java
import java.util.Stack;

public class StackCore {
    public static void main(String[] args) {
        Stack<Integer> stack = new Stack<>();
        for (int i = 1; i <= 3; i++) stack.push(i);

        while (!stack.isEmpty()) {
            System.out.println("Popped: " + stack.pop());
        }
    }
}
```

Pushing `1`, `2`, `3` in that order and then popping repeatedly yields `3`, `2`, `1` — the reverse of the push order — which is the defining property of LIFO: whatever went on last comes off first.

## 4. Diagram

<svg viewBox="0 0 400 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Elements are pushed onto the top of a stack and popped from the same top, in last in first out order">
  <rect x="8" y="8" width="384" height="204" rx="8" fill="#0d1117"/>
  <rect x="130" y="140" width="140" height="34" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="200" y="161" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">first</text>
  <rect x="130" y="104" width="140" height="34" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="200" y="125" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">second</text>
  <rect x="130" y="68" width="140" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="200" y="89" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">third  <tspan fill="#79c0ff">&#8592; top</tspan></text>
  <text x="200" y="40" fill="#79c0ff" font-size="11" text-anchor="middle">push adds here; pop removes from here</text>
</svg>

Both `push` and `pop` act on the same end — the top — never the bottom.

## 5. Runnable example

Scenario: a balanced-parentheses validator, evolved from a basic check into a full expression validator supporting multiple bracket types and reporting the exact position of the first mismatch.

### Level 1 — Basic

```java
import java.util.Stack;

public class StackBasic {
    static boolean isBalanced(String expr) {
        Stack<Character> stack = new Stack<>();
        for (char c : expr.toCharArray()) {
            if (c == '(') {
                stack.push(c);
            } else if (c == ')') {
                if (stack.isEmpty()) return false;
                stack.pop();
            }
        }
        return stack.isEmpty();
    }

    public static void main(String[] args) {
        System.out.println(isBalanced("(a + b) * (c - d)")); // true
        System.out.println(isBalanced("(a + b) * (c - d"));   // false: unclosed
        System.out.println(isBalanced("a + b)"));              // false: extra close
    }
}
```

**How to run:** `java StackBasic.java`

Every `(` is pushed; every `)` pops one — if a `)` arrives with nothing to pop, or characters remain on the stack at the end, the expression is unbalanced.

### Level 2 — Intermediate

Same balance-checking idea, now supporting three bracket types (`()`, `[]`, `{}`) and verifying that each closing bracket matches the *type* of the most recently opened one, not just that something was open.

```java
import java.util.Map;
import java.util.Stack;

public class StackIntermediate {
    static final Map<Character, Character> PAIRS = Map.of(')', '(', ']', '[', '}', '{');

    static boolean isBalanced(String expr) {
        Stack<Character> stack = new Stack<>();
        for (char c : expr.toCharArray()) {
            if (c == '(' || c == '[' || c == '{') {
                stack.push(c);
            } else if (PAIRS.containsKey(c)) {
                if (stack.isEmpty() || stack.pop() != PAIRS.get(c)) {
                    return false;
                }
            }
        }
        return stack.isEmpty();
    }

    public static void main(String[] args) {
        System.out.println(isBalanced("[a + (b * c)] - {d}")); // true
        System.out.println(isBalanced("[a + (b)]"));            // true
        System.out.println(isBalanced("[a + (b]"));              // false: mismatched types
    }
}
```

**How to run:** `java StackIntermediate.java`

`stack.pop() != PAIRS.get(c)` checks that the bracket coming off the stack is the exact opening partner of the closing bracket just seen — `"[a + (b]"` fails because when `]` is encountered, the top of the stack is `(`, not `[`, so the types don't match even though the stack wasn't empty.

### Level 3 — Advanced

Same validator, now reporting the exact character index of the first problem found (either an unmatched closer or, if the string ends with unclosed brackets, the position of the earliest still-open bracket), useful for pointing a user at exactly where their expression is malformed.

```java
import java.util.Map;
import java.util.Stack;

public class StackAdvanced {
    static final Map<Character, Character> PAIRS = Map.of(')', '(', ']', '[', '}', '{');

    record Result(boolean balanced, int errorIndex) {}

    static Result validate(String expr) {
        Stack<int[]> stack = new Stack<>(); // [bracketChar, index]
        for (int i = 0; i < expr.length(); i++) {
            char c = expr.charAt(i);
            if (c == '(' || c == '[' || c == '{') {
                stack.push(new int[]{c, i});
            } else if (PAIRS.containsKey(c)) {
                if (stack.isEmpty() || stack.peek()[0] != PAIRS.get(c)) {
                    return new Result(false, i); // unmatched closer at index i
                }
                stack.pop();
            }
        }
        if (!stack.isEmpty()) {
            return new Result(false, stack.peek()[1]); // earliest still-open bracket
        }
        return new Result(true, -1);
    }

    public static void main(String[] args) {
        String[] tests = {"[a + (b * c)] - {d}", "[a + (b]", "[a + (b * c)"};
        for (String expr : tests) {
            Result r = validate(expr);
            System.out.println("\"" + expr + "\" -> " + (r.balanced()
                ? "balanced"
                : "unbalanced, first problem at index " + r.errorIndex()));
        }
    }
}
```

**How to run:** `java StackAdvanced.java`

Storing `int[]{bracketChar, index}` instead of just the character lets the stack remember *where* each open bracket appeared; when validation fails, that stored index — either of the mismatched closer or of the deepest still-unclosed opener — is reported directly to the caller.

## 6. Walkthrough

Trace `validate("[a + (b]")` from `StackAdvanced` step by step (this is the second test case).

**`i=0, c='['`.** Opening bracket, so `stack.push(new int[]{'[', 0})`. Stack now holds one entry: `['[' at 0]`.

**`i=1..3`, characters `a`, ` `, `+`.** None are brackets; the loop skips them (falls through both `if`/`else if` conditions).

**`i=4, c=' '`, `i=5, c='('`.** At index 5, `(` is another opener: `stack.push(new int[]{'(', 5})`. Stack now holds two entries, top-to-bottom: `['(' at 5]`, `['[' at 0]`.

**`i=6, c='b'`.** Not a bracket, skipped.

**`i=7, c=']'`.** This is a closer. `stack.peek()` returns the top entry, `['(' at 5]`, so `stack.peek()[0]` is `'('`. `PAIRS.get(']')` is `'['`. Since `'(' != '['`, the condition `stack.peek()[0] != PAIRS.get(c)` is `true` — a mismatch is detected immediately, **without popping**. The method returns `new Result(false, 7)`.

**Back in `main`.** `r.balanced()` is `false`, so the message becomes `"unbalanced, first problem at index 7"` — index 7 is exactly where the stray `]` sits in the string `"[a + (b]"`, precisely identifying the character that broke the nesting (it closes the wrong bracket type; the `(` opened at index 5 was still expecting a matching `)`).

```
"[a + (b]"
 0123456 7
 [        <- push '[' @0     stack: [ '[' @0 ]
      (   <- push '(' @5     stack: [ '(' @5, '[' @0 ]
        ] <- closer at 7; peek is '(' @5, but PAIRS[']'] is '[' -> MISMATCH
             -> return Result(false, 7)
```

**Output (all three test cases):**
```
"[a + (b * c)] - {d}" -> balanced
"[a + (b]" -> unbalanced, first problem at index 7
"[a + (b * c)" -> unbalanced, first problem at index 5
```

The third case shows the other failure path: no mismatched closer is ever seen, but the stack still has `['(' at 5, '[' at 0]` left over at the end — `stack.peek()[1]` reports index `5`, the position of the innermost (most recently opened, and therefore first-reported) bracket that was never closed.

## 7. Gotchas & takeaways

> `Stack` extends `Vector`, so it inherits `get`, `add(index, element)`, and `remove(index)` — methods that let you read or mutate the stack at **any** position, not just the top. Nothing in the type system stops code from quietly violating LIFO discipline by reaching into the middle of a `Stack`. This is exactly why the official recommendation is to use `Deque`/`ArrayDeque` instead, which expose no such arbitrary-access methods.

> `pop()` and `peek()` throw `EmptyStackException` (a `RuntimeException`) if called on an empty stack — always check `isEmpty()` first in any loop that pops until empty, or be prepared to catch the exception.

- `Stack` is a LIFO structure: `push` adds to the top, `pop` removes and returns the top, `peek` reads the top without removing it.
- It extends `Vector`, inheriting synchronization overhead and arbitrary-position access that can undermine the LIFO guarantee.
- `pop`/`peek` on an empty stack throw `EmptyStackException` — guard with `isEmpty()`.
- For new code, prefer `Deque`/`ArrayDeque` used via `push`/`pop`/`peek` — faster and safer against accidental misuse than `Stack`.
