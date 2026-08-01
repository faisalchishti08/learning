---
card: data-structures
gi: 62
slug: lifo-semantics
title: LIFO semantics
---

## 1. What it is

A **stack** is a data structure that only lets you add or remove an element at one end, called the **top**. That single rule gives it **LIFO** order: Last In, First Out — the most recently added element is always the first one removed. Picture a stack of plates: you can only take the top plate off, and you can only add a new plate on top.

## 2. Why & when

LIFO order is exactly what you need whenever the most recent thing must be undone or processed first: undo history, back-button navigation, matching brackets, or tracking function calls (the call stack itself is a stack). Use a stack instead of a general list whenever your logic only ever touches "the most recent item," since restricting the interface to `push`/`pop`/`peek` prevents bugs from code accidentally reaching into the middle of the structure.

## 3. Core concept

**The invariant: only the top is reachable.** A stack exposes exactly three operations — `push` (add to the top), `pop` (remove and return the top), `peek` (look at the top without removing it). There is no `get(i)` or "insert in the middle"; that restriction is the whole point, since it guarantees LIFO order can never be violated.

**How the invariant makes operations fast.** Because every operation only ever touches the top, a stack can be backed by either an array or a linked list and still give O(1) `push`, `pop`, and `peek` — there is never a need to shift elements or walk a chain, since "the top" is always a known, fixed position (the last array slot in use, or the head of a linked list).

**LIFO vs FIFO.** A queue is the mirror image: First In, First Out (FIFO), where removal happens from the opposite end from insertion. A stack's `push`/`pop` both happen at the same end; a queue's `enqueue`/`dequeue` happen at opposite ends. This single difference in *which end* you touch is what produces reversed order (stack) versus preserved order (queue).

## 4. Diagram

<svg viewBox="0 0 500 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A stack of three plates labeled 3, 2, 1 from top to bottom, with push adding to the top and pop removing from the top">
  <g font-family="sans-serif" font-size="11">
    <rect x="150" y="140" width="120" height="30" fill="#161b22" stroke="#8b949e"/><text x="210" y="160" fill="#e6edf3" text-anchor="middle">1 (pushed first)</text>
    <rect x="150" y="105" width="120" height="30" fill="#161b22" stroke="#8b949e"/><text x="210" y="125" fill="#e6edf3" text-anchor="middle">2</text>
    <rect x="150" y="70" width="120" height="30" fill="#0d1117" stroke="#f0883e"/><text x="210" y="90" fill="#e6edf3" text-anchor="middle">3 (top)</text>
    <text x="210" y="55" fill="#f0883e" text-anchor="middle">top -&gt; next pop returns 3</text>
    <line x1="290" y1="85" x2="330" y2="85" stroke="#79c0ff" marker-end="url(#lf)"/>
    <text x="360" y="70" fill="#79c0ff" font-size="9">push(4)</text>
    <line x1="330" y1="95" x2="290" y2="95" stroke="#f0883e" marker-end="url(#lf2)"/>
    <text x="360" y="105" fill="#f0883e" font-size="9">pop() -&gt; 3</text>
    <defs>
      <marker id="lf" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker>
      <marker id="lf2" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker>
    </defs>
  </g>
</svg>

Elements stack like plates: `1` went in first and sits at the bottom; `3` went in last and is the only one reachable — the next `pop()` must return `3`.

## 5. Runnable example

```java
// LifoSemanticsDemo.java
import java.util.ArrayDeque;
import java.util.Deque;

public class LifoSemanticsDemo {

    // Basic: push three values, observe LIFO pop order.
    static void basicLevel() {
        Deque<Integer> stack = new ArrayDeque<>(); // ArrayDeque used as a stack, see topic 0070
        stack.push(1);
        stack.push(2);
        stack.push(3);
        System.out.println("basic: pop order -> " + stack.pop() + ", " + stack.pop() + ", " + stack.pop());
    }

    // Intermediate: peek does not remove; mixing push/pop shows order depends only on recency.
    static void intermediateLevel() {
        Deque<String> stack = new ArrayDeque<>();
        stack.push("first");
        stack.push("second");
        System.out.println("intermediate: peek (no removal) -> " + stack.peek());
        stack.pop(); // removes "second"
        stack.push("third");
        System.out.println("intermediate: pop order after mixing -> " + stack.pop() + ", " + stack.pop());
    }

    // Advanced: reverse a sequence using only LIFO operations, to make the "last becomes first" property concrete.
    static void advancedLevel() {
        Deque<Character> stack = new ArrayDeque<>();
        String word = "stack";
        for (char c : word.toCharArray()) stack.push(c);

        StringBuilder reversed = new StringBuilder();
        while (!stack.isEmpty()) reversed.append(stack.pop());

        System.out.println("advanced: \"" + word + "\" reversed via a stack -> " + reversed);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `LifoSemanticsDemo.java`, then run `java LifoSemanticsDemo.java`.

## 6. Walkthrough

1. `basicLevel()` pushes `1`, `2`, `3` in that order, so the top is `3`. Three `pop()` calls return `3`, `2`, `1` — the exact reverse of the push order, which is the definition of LIFO.
2. `intermediateLevel()` pushes `"first"`, then `"second"`; `peek()` reads `"second"` without removing it, so it stays on top. `pop()` removes `"second"`, then `push("third")` puts `"third"` on top of `"first"`. The final two pops return `"third"`, then `"first"` — order depends only on which element is most recently on top, not on the total history of pushes.
3. `advancedLevel()` pushes every character of `"stack"` (`s, t, a, c, k`), then pops all of them into a new string. Since pop always returns the most recently pushed character, the result is `"kcats"` — the original string reversed. This shows why a stack is the standard tool for reversing a sequence.

## 7. Gotchas & takeaways

> Gotcha: calling `pop()` or `peek()` on an empty stack throws (`NoSuchElementException` for `ArrayDeque`, or returns `null` for the poll/peek-style methods if you use `poll()`/`peek()` on a `Deque` used as a queue) — always check `isEmpty()` first, or use the `Deque` poll-family methods if a `null`/no-op result is preferable to an exception.

- A stack restricts access to one end (the top), which is what guarantees LIFO order.
- `push`, `pop`, and `peek` are all O(1), regardless of whether the stack is array-backed or linked.
- LIFO (stack) and FIFO (queue) differ only in which end removal happens from.
- Related concepts: [Array-backed vs linked stack](0063-array-backed-vs-linked-stack.md), [ArrayDeque as a stack (preferred)](0070-arraydeque-as-a-stack-preferred.md).
