---
card: data-structures
gi: 70
slug: arraydeque-as-a-stack-preferred
title: ArrayDeque as a stack (preferred)
---

## 1. What it is

`java.util.ArrayDeque` is a resizable, array-backed **double-ended queue** (deque). It implements `Deque`, which includes stack-shaped methods — `push`, `pop`, `peek` — so it works as a stack directly. It is the class the Java documentation itself recommends over `java.util.Stack` for stack use.

## 2. Why & when

Use `ArrayDeque` any time you need a stack in Java. It backs its elements with a plain resizable array (no per-element node objects, unlike `LinkedList`), it is not synchronized (no lock overhead, unlike `Stack`), and it explicitly disallows `null` elements, which catches a class of bugs early. It also doubles as an efficient queue, if you ever need both behaviors from one class.

## 3. Core concept

**What backs it.** A circular array — a fixed-size array where the "start" and "end" positions wrap around, so both `push`-at-front and `add`-at-back are O(1) without shifting elements. It resizes (doubles) when full, the same amortized-O(1) growth as `ArrayList`.

**Ordering and complexity guarantees.** `push`/`pop`/`peek` (stack use) are all O(1). `offer`/`poll` (queue use) are also O(1) at both ends. Iteration order for a stack-style traversal (`iterator()`) goes from most-recently-pushed to least — the natural LIFO order.

**Basic usage — the common methods.**

| Method | Effect |
|---|---|
| `push(e)` | add to the top |
| `pop()` | remove and return the top; throws if empty |
| `peek()` | return the top without removing; returns `null` if empty |
| `isEmpty()` | check if the stack has any elements |

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An ArrayDeque backed by a circular array, with push and pop operating at the same end, the head, giving stack behavior">
  <g font-family="sans-serif" font-size="11">
    <rect x="40" y="30" width="40" height="26" fill="#0d1117" stroke="#f0883e"/><text x="60" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">30</text>
    <rect x="80" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="100" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">20</text>
    <rect x="120" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="140" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <text x="60" y="20" fill="#f0883e" text-anchor="middle" font-size="9">head (top)</text>
    <line x1="30" y1="43" x2="10" y2="43" stroke="#79c0ff" marker-end="url(#pp)"/>
    <text x="10" y="65" fill="#79c0ff" font-size="9">push/pop here, O(1)</text>
    <defs><marker id="pp" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M8,0 L0,4 L8,8 z" fill="#79c0ff"/></marker></defs>
    <text x="320" y="100" fill="#8b949e" text-anchor="middle">no per-element Node objects -- one contiguous backing array, resized (doubled) when full</text>
  </g>
</svg>

`push`/`pop` operate at the same end (the head), giving LIFO order over a single contiguous array — no node allocation per element.

## 5. Runnable example

```java
// ArrayDequeAsStack.java
import java.util.ArrayDeque;
import java.util.Deque;

public class ArrayDequeAsStack {

    // Basic: the common stack methods.
    static void basicLevel() {
        Deque<Integer> stack = new ArrayDeque<>();
        stack.push(1);
        stack.push(2);
        stack.push(3);
        System.out.println("basic: peek -> " + stack.peek());
        System.out.println("basic: pop -> " + stack.pop());
        System.out.println("basic: isEmpty -> " + stack.isEmpty());
    }

    // Intermediate: iteration order, and using the SAME instance as a queue too (Deque supports both).
    static void intermediateLevel() {
        Deque<String> stack = new ArrayDeque<>();
        stack.push("a");
        stack.push("b");
        stack.push("c");

        StringBuilder stackOrder = new StringBuilder();
        for (String s : stack) stackOrder.append(s).append(" "); // most-recently-pushed first
        System.out.println("intermediate: stack iteration order -> " + stackOrder.toString().trim());

        Deque<String> queue = new ArrayDeque<>();
        queue.offer("a"); // offer/poll at opposite ends: FIFO, queue behavior
        queue.offer("b");
        queue.offer("c");
        System.out.println("intermediate: same class as a queue, poll order -> " + queue.poll() + ", " + queue.poll() + ", " + queue.poll());
    }

    // Advanced: null rejection, and using ArrayDeque for a realistic task -- DFS traversal with an explicit stack.
    static void advancedLevel() {
        Deque<Integer> stack = new ArrayDeque<>();
        try {
            stack.push(null);
        } catch (NullPointerException e) {
            System.out.println("advanced: ArrayDeque rejects null elements -- caught NullPointerException");
        }

        // iterative DFS over a small tree using an explicit ArrayDeque stack instead of recursion
        int[][] tree = {{1, 2}, {3, 4}, {}, {}, {}}; // node 0 -> children 1,2; node 1 -> children 3,4; leaves have none
        Deque<Integer> dfsStack = new ArrayDeque<>();
        dfsStack.push(0);
        StringBuilder visited = new StringBuilder();
        while (!dfsStack.isEmpty()) {
            int node = dfsStack.pop();
            visited.append(node).append(" ");
            for (int i = tree[node].length - 1; i >= 0; i--) dfsStack.push(tree[node][i]); // push right-to-left so left is popped first
        }
        System.out.println("advanced: iterative DFS visit order -> " + visited.toString().trim());
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `ArrayDequeAsStack.java`, then run `java ArrayDequeAsStack.java`.

## 6. Walkthrough

1. `basicLevel()` pushes `1, 2, 3`; `peek()` reads `3` without removing it; `pop()` removes and returns `3`; `isEmpty()` is `false`, since `1` and `2` remain.
2. `intermediateLevel()` shows that iterating an `ArrayDeque` used as a stack visits elements in pop order (`c, b, a`) — most recent first. The same `ArrayDeque` class, used with `offer`/`poll` instead of `push`/`pop`, behaves as a FIFO queue (`a, b, c` in, `a, b, c` out) — the class does not care which behavior you use, only which method names you call.
3. `advancedLevel()` first confirms `ArrayDeque` throws `NullPointerException` on `push(null)`, catching bugs where a `null` might otherwise silently corrupt the structure. Then it runs an iterative depth-first search using an explicit `ArrayDeque` stack instead of recursion: node `0`'s children `[1, 2]` are pushed right-to-left (`2` then `1`), so popping visits `1` first — mirroring what recursive DFS would do, but using an explicit stack instead of the JVM's call stack.

## 7. Gotchas & takeaways

> Gotcha: `ArrayDeque` throws `NullPointerException` on any attempt to add `null` (`push`, `offer`, `add`) — this is a deliberate design choice (a `null` return from `peek`/`poll` unambiguously means "empty"), unlike `LinkedList`, which does allow `null` elements. Do not port code between the two without checking this.

- `ArrayDeque` is the modern, recommended class for stack use in Java — array-backed, no lock overhead, disallows `null`.
- `push`/`pop`/`peek` give LIFO (stack); `offer`/`poll` give FIFO (queue) — same class, different method pairs.
- It replaces both `java.util.Stack` (for stacks) and is often faster than `LinkedList` (for queues), due to better cache locality.
- Related concepts: [Legacy java.util.Stack & why to avoid it](0071-legacy-java-util-stack-why-to-avoid-it.md), [LIFO semantics](0062-lifo-semantics.md).
