---
card: leetcode-patterns
gi: 581
slug: min-stack
title: Min Stack
---

## 1. What it is

Design a `MinStack` class supporting the usual stack operations — `push(val)`, `pop()`, `top()` — plus `getMin()`, which returns the minimum value currently in the stack. Every method must run in O(1). Example: `push(-2)`, `push(0)`, `push(-3)`, `getMin()` → `-3`, `pop()`, `top()` → `0`, `getMin()` → `-2`.

## 2. Why & when

A plain stack gives O(1) `push`/`pop`/`top` but has no fast way to find the minimum — scanning the whole stack on every `getMin()` call is O(n). The challenge is keeping `getMin()` at O(1) *even as elements are popped*, since the minimum can change (increase) whenever the current minimum itself gets popped off.

## 3. Core concept

**Key idea:** maintain a second stack, `minStack`, that tracks the minimum-so-far at every depth of the main stack — its top always mirrors "the minimum among everything currently in the main stack." Push and pop both stacks together, so they always stay the same size and in sync.

**Steps:**
1. `push(val)`: push `val` onto the main stack. Compute the new minimum as `Math.min(val, minStack.isEmpty() ? val : minStack.peek())`, and push that onto `minStack`.
2. `pop()`: pop both stacks together — popping `minStack` automatically "restores" whatever the minimum was one level below.
3. `top()`: return the main stack's top, unchanged from a normal stack.
4. `getMin()`: return `minStack.peek()` — O(1), no scanning.

**Why pushing the minimum-so-far (not just the value) onto `minStack` works:** each entry in `minStack` records "what was the minimum, considering everything pushed up to and including this point." Popping the main stack removes the most recently pushed value; popping `minStack` in lockstep removes that same value's minimum-context, correctly revealing what the minimum was *before* that value was pushed — without needing to search.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two parallel stacks: the main stack of values and a shadow stack of the running minimum at each depth">
  <g font-family="sans-serif" font-size="12">
    <text x="120" y="20" fill="#8b949e" text-anchor="middle">main stack</text>
    <rect x="70" y="30" width="100" height="30" fill="#161b22" stroke="#3fb950"/><text x="120" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">-3 (top)</text>
    <rect x="70" y="60" width="100" height="30" fill="#161b22" stroke="#30363d"/><text x="120" y="80" fill="#e6edf3" text-anchor="middle" font-size="11">0</text>
    <rect x="70" y="90" width="100" height="30" fill="#161b22" stroke="#30363d"/><text x="120" y="110" fill="#e6edf3" text-anchor="middle" font-size="11">-2</text>
    <text x="420" y="20" fill="#8b949e" text-anchor="middle">minStack</text>
    <rect x="370" y="30" width="100" height="30" fill="#161b22" stroke="#f0883e"/><text x="420" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">-3 (top)</text>
    <rect x="370" y="60" width="100" height="30" fill="#161b22" stroke="#30363d"/><text x="420" y="80" fill="#e6edf3" text-anchor="middle" font-size="11">-2</text>
    <rect x="370" y="90" width="100" height="30" fill="#161b22" stroke="#30363d"/><text x="420" y="110" fill="#e6edf3" text-anchor="middle" font-size="11">-2</text>
    <text x="270" y="160" fill="#79c0ff" text-anchor="middle">getMin() reads minStack.peek() = -3, O(1), no scan</text>
  </g>
</svg>

Each `minStack` entry records the minimum-so-far at that depth — popping both stacks together always leaves `minStack.peek()` correct without rescanning.

## 5. Runnable example

**Level 1 — Brute force.** A single stack plus a `getMin()` that iterates the whole stack (or a copy of it) to find the smallest value. O(n) per `getMin()` call.

**KEY INSIGHT:** instead of recomputing the minimum by scanning, *record* it incrementally as each value is pushed, in a second stack that shrinks and grows in lockstep with the first — so the correct minimum for the current stack state is always sitting on top.

**Level 2 — Optimal.** Two parallel stacks (`ArrayDeque<Integer>` as a stack), synchronized push/pop, O(1) for every method.

**Level 3 — Hardened.** Correctly handles duplicate minimums (pushing the same minimum value again must still push a matching entry onto `minStack`, so popping one copy does not lose the other), and ties `minStack`'s size exactly to the main stack's size.

```java
// MinStack.java
import java.util.*;

public class MinStack {

    private final Deque<Integer> stack = new ArrayDeque<>();
    private final Deque<Integer> minStack = new ArrayDeque<>();

    public void push(int val) {
        stack.push(val);
        int currentMin = minStack.isEmpty() ? val : Math.min(val, minStack.peek());
        minStack.push(currentMin);
    }

    public void pop() {
        stack.pop();
        minStack.pop();
    }

    public int top() {
        return stack.peek();
    }

    public int getMin() {
        return minStack.peek();
    }

    public static void main(String[] args) {
        MinStack ms = new MinStack();
        ms.push(-2);
        ms.push(0);
        ms.push(-3);
        System.out.println(ms.getMin()); // -3
        ms.pop();
        System.out.println(ms.top());    // 0
        System.out.println(ms.getMin()); // -2
    }
}
```

**How to run:** save as `MinStack.java`, then run `java MinStack.java`.

## 6. Walkthrough

Trace `push(-2)`, `push(0)`, `push(-3)`, `getMin()`, `pop()`, `top()`, `getMin()`:

| call | stack (top first) | minStack (top first) | return |
|---|---|---|---|
| push(-2) | [-2] | [-2] | — |
| push(0) | [0,-2] | [-2,-2] | — |
| push(-3) | [-3,0,-2] | [-3,-2,-2] | — |
| getMin() | [-3,0,-2] | [-3,-2,-2] | -3 |
| pop() | [0,-2] | [-2,-2] | — |
| top() | [0,-2] | [-2,-2] | 0 |
| getMin() | [0,-2] | [-2,-2] | -2 |

Popping `-3` off `stack` also pops `-3` off `minStack`, revealing `-2` — the minimum that was correct one level below — without any scan.

## 7. Gotchas & takeaways

> Gotcha: pushing onto `minStack` only when the new value is strictly smaller than the current minimum (skipping the push otherwise) breaks synchronization — the two stacks must always have the same size, or a later `pop()` will desync them and `getMin()` will return a stale value.

- Signal: needing O(1) access to an aggregate (min, max) over a collection that also supports removal is the "shadow structure tracking the running aggregate" signal.
- The shadow stack must be pushed and popped in exact lockstep with the main stack, every single call, including duplicate minimums.
- Related problems: Max Stack (same idea for maximum, usually paired with an O(log n) `popMax`).
