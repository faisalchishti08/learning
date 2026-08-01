---
card: data-structures
gi: 63
slug: array-backed-vs-linked-stack
title: Array-backed vs linked stack
---

## 1. What it is

A stack's LIFO contract (`push`/`pop`/`peek` only) can be implemented two ways: on top of a resizable array, or on top of a singly linked list of nodes. Both give the same O(1) operations and the same LIFO behavior from the outside — the choice is purely an internal implementation decision.

## 2. Why & when

Understanding both implementations matters because Java's own stack-capable classes are built this way: `ArrayDeque` is array-backed, `LinkedList` (used as a `Deque`) is node-backed. Knowing the tradeoffs tells you which one to reach for, and lets you build a stack yourself when you need one with custom behavior a library class does not offer.

## 3. Core concept

**Decision criteria:**
- **Memory layout.** An array-backed stack stores elements contiguously, giving good CPU cache locality. A linked stack allocates a separate node object per element, each with its own memory location and a pointer — worse cache locality, more memory overhead (an extra reference per element, plus per-object allocation overhead).
- **Growth.** An array-backed stack must occasionally resize (allocate a bigger array and copy) when it fills up — amortized O(1) `push`, but an occasional O(n) spike. A linked stack never resizes; every `push` allocates exactly one new node, so it is O(1) every single time, with no spikes.
- **Fixed capacity option.** An array-backed stack can be built with a hard capacity limit (reject `push` when full) with zero extra memory for pointers — useful when a maximum size is known upfront.
- **Predictability.** If consistent per-operation latency matters more than average throughput (e.g. in a real-time system), the linked version avoids the array-backed version's occasional resize pause.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two stacks holding the same three elements: an array backed stack with contiguous slots and a top index, versus a linked stack with separate nodes connected by pointers">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">array-backed</text>
    <rect x="20" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="40" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">1</text>
    <rect x="60" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="80" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">2</text>
    <rect x="100" y="30" width="40" height="26" fill="#0d1117" stroke="#f0883e"/><text x="120" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <text x="120" y="75" fill="#f0883e" text-anchor="middle" font-size="9">top index = 2</text>
    <text x="220" y="16" fill="#8b949e">linked</text>
    <rect x="220" y="30" width="40" height="26" fill="#0d1117" stroke="#f0883e"/><text x="240" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <rect x="290" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="310" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">2</text>
    <rect x="360" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="380" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">1</text>
    <line x1="260" y1="43" x2="286" y2="43" stroke="#79c0ff" marker-end="url(#ab)"/>
    <line x1="330" y1="43" x2="356" y2="43" stroke="#79c0ff" marker-end="url(#ab)"/>
    <defs><marker id="ab" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
    <text x="240" y="75" fill="#f0883e" text-anchor="middle" font-size="9">top = this node</text>
    <text x="320" y="130" fill="#8b949e" text-anchor="middle">array: contiguous, resizes occasionally. linked: scattered, one alloc per push, never resizes.</text>
  </g>
</svg>

Both structures hold `1, 2, 3` with `3` on top; the array version tracks a `top` index into contiguous memory, the linked version tracks a `top` node reference into scattered memory.

## 5. Runnable example

```java
// StackImplementations.java
public class StackImplementations {

    // Basic: array-backed stack with manual resizing.
    static class ArrayStack<T> {
        private Object[] data = new Object[4];
        private int top = -1; // index of the top element; -1 means empty

        void push(T value) {
            if (top + 1 == data.length) resize();
            data[++top] = value;
        }

        @SuppressWarnings("unchecked")
        T pop() {
            if (top < 0) throw new IllegalStateException("stack is empty");
            T value = (T) data[top];
            data[top--] = null; // avoid holding a stale reference
            return value;
        }

        private void resize() {
            Object[] bigger = new Object[data.length * 2]; // O(n) copy, but amortized over many pushes
            System.arraycopy(data, 0, bigger, 0, data.length);
            data = bigger;
        }

        boolean isEmpty() { return top < 0; }
    }

    static void basicLevel() {
        ArrayStack<Integer> stack = new ArrayStack<>();
        for (int i = 1; i <= 6; i++) stack.push(i); // forces at least one resize (capacity starts at 4)
        StringBuilder sb = new StringBuilder();
        while (!stack.isEmpty()) sb.append(stack.pop()).append(" ");
        System.out.println("basic: array-backed pop order -> " + sb.toString().trim());
    }

    // Intermediate: linked (node-based) stack, never resizes.
    static class LinkedStack<T> {
        private static class Node<T> {
            T value;
            Node<T> next;
            Node(T value, Node<T> next) { this.value = value; this.next = next; }
        }

        private Node<T> top;

        void push(T value) { top = new Node<>(value, top); } // one allocation, always O(1)

        T pop() {
            if (top == null) throw new IllegalStateException("stack is empty");
            T value = top.value;
            top = top.next;
            return value;
        }

        boolean isEmpty() { return top == null; }
    }

    static void intermediateLevel() {
        LinkedStack<String> stack = new LinkedStack<>();
        stack.push("a");
        stack.push("b");
        stack.push("c");
        StringBuilder sb = new StringBuilder();
        while (!stack.isEmpty()) sb.append(stack.pop()).append(" ");
        System.out.println("intermediate: linked pop order -> " + sb.toString().trim());
    }

    // Advanced: compare push cost across many operations to show the array version's amortized spikes.
    static void advancedLevel() {
        int n = 20_000;

        long t0 = System.nanoTime();
        ArrayStack<Integer> arrayStack = new ArrayStack<>();
        for (int i = 0; i < n; i++) arrayStack.push(i);
        long arrayMs = (System.nanoTime() - t0) / 1_000_000;

        long t1 = System.nanoTime();
        LinkedStack<Integer> linkedStack = new LinkedStack<>();
        for (int i = 0; i < n; i++) linkedStack.push(i);
        long linkedMs = (System.nanoTime() - t1) / 1_000_000;

        System.out.println("advanced: " + n + " pushes -> array-backed: " + arrayMs + " ms, linked: " + linkedMs + " ms (both O(1) amortized/always)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `StackImplementations.java`, then run `java StackImplementations.java`.

## 6. Walkthrough

1. `basicLevel()` pushes `1` through `6` onto an `ArrayStack` that starts with capacity `4`. The fifth push (`5`) triggers `resize()`, doubling capacity to `8` and copying all four existing elements — an O(n) cost paid once, amortized across many O(1) pushes. Popping all six values gives `6 5 4 3 2 1`, the reverse of push order.
2. `intermediateLevel()` pushes `"a"`, `"b"`, `"c"` onto a `LinkedStack`. Each push allocates one new `Node` whose `next` points at the previous top, then becomes the new top — no resizing ever happens. Popping gives `c b a`.
3. `advancedLevel()` times 20,000 pushes on each implementation. Both finish in comparable time in practice, since the array version's resizes are infrequent and amortize away — this is why "amortized O(1)" and "always O(1)" behave the same in aggregate, even though a single array-backed push can occasionally take longer than a single linked push.

## 7. Gotchas & takeaways

> Gotcha: an array-backed stack that does not null out popped slots (`data[top--] = null`) keeps a reference to the popped object alive, preventing it from being garbage collected until that slot is overwritten — a subtle memory leak in long-running programs with a stack that grows and shrinks repeatedly.

- Both implementations give O(1) `push`/`pop`/`peek` from the caller's perspective.
- Array-backed: better cache locality, less per-element memory, but occasional O(n) resize spikes.
- Linked: no resize spikes (every push is a single O(1) allocation), but worse cache locality and more per-element memory.
- Java's `ArrayDeque` is array-backed; `LinkedList` used as a `Deque` is node-backed — this is the exact same tradeoff, already built for you.
- Related concepts: [LIFO semantics](0062-lifo-semantics.md), [ArrayDeque as a stack (preferred)](0070-arraydeque-as-a-stack-preferred.md), [Array resizing / amortized append](0020-array-resizing-amortized-append.md).
