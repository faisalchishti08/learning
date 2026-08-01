---
card: data-structures
gi: 64
slug: push-pop-peek-o-1
title: push / pop / peek (O(1))
---

## 1. What it is

`push`, `pop`, and `peek` are the three core operations of a stack. `push` adds a value on top. `pop` removes and returns the top value. `peek` returns the top value without removing it. All three run in **O(1)** constant time — the cost does not grow as the stack gets bigger.

## 2. Why & when

Knowing exactly *why* these are O(1) — not just that they are — is what lets you reason correctly about the complexity of any algorithm built on a stack (like depth-first search or expression evaluation). Whenever you see "process the most recent item, in constant time" in a problem, a stack with these three operations is the tool.

## 3. Core concept

**Why `push` is O(1).** On an array-backed stack, `push` writes to `data[top + 1]` and increments `top` — one array write, one increment, regardless of how many elements are already in the stack. (Ignoring the rare resize, which is amortized away — see [Array-backed vs linked stack](0063-array-backed-vs-linked-stack.md).) On a linked stack, `push` allocates one `Node` and repoints `top` to it — also independent of stack size.

**Why `pop` is O(1).** `pop` reads `data[top]` then decrements `top` (array-backed), or reads `top.value` then reassigns `top = top.next` (linked). Either way, it touches exactly one slot or node — never a scan, never a shift.

**Why `peek` is O(1).** `peek` just reads the value at the known `top` position (array index, or the `top` node's field) without changing anything. Since the top is always tracked directly, there is nothing to search for.

**The contrast that makes this concrete.** Compare to inserting at the *front* of an `ArrayList`: every existing element must shift one slot right, which is O(n). A stack never does this, because it only ever touches the position it already keeps a direct reference or index to.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three operations shown against a stack of two elements: push writes one new slot, pop reads and removes the top slot, peek reads the top slot without removing it">
  <g font-family="sans-serif" font-size="11">
    <rect x="30" y="60" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="50" y="77" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <rect x="30" y="30" width="40" height="26" fill="#0d1117" stroke="#f0883e"/><text x="50" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">20</text>
    <text x="50" y="20" fill="#f0883e" text-anchor="middle" font-size="9">top</text>

    <text x="180" y="20" fill="#79c0ff">push(30)</text>
    <rect x="160" y="60" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="180" y="77" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <rect x="160" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="180" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">20</text>
    <rect x="160" y="0" width="40" height="26" fill="#0d1117" stroke="#79c0ff"/><text x="180" y="17" fill="#e6edf3" text-anchor="middle" font-size="9">30</text>
    <text x="180" y="105" fill="#79c0ff" text-anchor="middle" font-size="9">1 write, O(1)</text>

    <text x="320" y="20" fill="#f0883e">pop() -&gt; 20</text>
    <rect x="300" y="60" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="320" y="77" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <text x="320" y="47" fill="#8b949e" text-anchor="middle" font-size="9">(removed: 20)</text>
    <text x="320" y="105" fill="#f0883e" text-anchor="middle" font-size="9">1 read + decrement, O(1)</text>

    <text x="460" y="20" fill="#a5d6ff">peek() -&gt; 20</text>
    <rect x="440" y="60" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="460" y="77" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <rect x="440" y="30" width="40" height="26" fill="#0d1117" stroke="#a5d6ff"/><text x="460" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">20</text>
    <text x="460" y="105" fill="#a5d6ff" text-anchor="middle" font-size="9">1 read, nothing removed</text>
  </g>
</svg>

Each operation touches exactly the `top` position — never any other element — which is why all three cost the same regardless of stack size.

## 5. Runnable example

```java
// PushPopPeekDemo.java
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.EmptyStackException;

public class PushPopPeekDemo {

    // Basic: the three operations on java.util.ArrayDeque used as a stack.
    static void basicLevel() {
        Deque<Integer> stack = new ArrayDeque<>();
        stack.push(10);
        stack.push(20);
        System.out.println("basic: peek -> " + stack.peek()); // 20, unchanged after
        System.out.println("basic: pop -> " + stack.pop());   // 20, removed
        System.out.println("basic: peek after pop -> " + stack.peek()); // 10
    }

    // Intermediate: a minimal custom stack that makes the O(1) cost of each op explicit.
    static class TinyStack<T> {
        private Object[] data = new Object[8];
        private int top = -1;

        void push(T value) { data[++top] = value; } // one array write, one increment

        @SuppressWarnings("unchecked")
        T pop() {
            if (top < 0) throw new EmptyStackException();
            T value = (T) data[top];
            data[top--] = null;
            return value; // one array read, one decrement
        }

        @SuppressWarnings("unchecked")
        T peek() {
            if (top < 0) throw new EmptyStackException();
            return (T) data[top]; // one array read, nothing changes
        }
    }

    static void intermediateLevel() {
        TinyStack<String> stack = new TinyStack<>();
        stack.push("x");
        stack.push("y");
        stack.push("z");
        System.out.println("intermediate: peek -> " + stack.peek());
        System.out.println("intermediate: pop -> " + stack.pop());
        System.out.println("intermediate: pop -> " + stack.pop());
        System.out.println("intermediate: peek -> " + stack.peek());
    }

    // Advanced: confirm operation cost stays flat as size grows, by timing peek at small vs large size.
    static void advancedLevel() {
        Deque<Integer> small = new ArrayDeque<>();
        small.push(1);
        Deque<Integer> large = new ArrayDeque<>();
        for (int i = 0; i < 1_000_000; i++) large.push(i);

        long t0 = System.nanoTime();
        for (int i = 0; i < 100_000; i++) small.peek();
        long smallNs = System.nanoTime() - t0;

        long t1 = System.nanoTime();
        for (int i = 0; i < 100_000; i++) large.peek();
        long largeNs = System.nanoTime() - t1;

        System.out.println("advanced: 100k peeks on size-1 stack -> " + smallNs + " ns");
        System.out.println("advanced: 100k peeks on size-1,000,000 stack -> " + largeNs + " ns (roughly the same order of magnitude)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `PushPopPeekDemo.java`, then run `java PushPopPeekDemo.java`.

## 6. Walkthrough

1. `basicLevel()` pushes `10`, then `20`. `peek()` returns `20` and leaves the stack unchanged. `pop()` returns `20` and removes it, leaving only `10`. A second `peek()` confirms the new top is `10`.
2. `intermediateLevel()`'s `TinyStack` makes the mechanics explicit: `push` writes to `data[++top]`, a single array cell. `pop` reads `data[top]` then decrements `top` — the value technically still sits in the array until overwritten, but is logically gone since `top` no longer includes it. `peek` performs the same read as `pop` but skips the decrement.
3. `advancedLevel()` times `peek()` on a stack of size `1` versus size `1,000,000`. Both take roughly the same total time for 100,000 calls, confirming `peek` (and by the same logic, `push`/`pop`) does not slow down as the stack grows — the defining property of O(1).

## 7. Gotchas & takeaways

> Gotcha: `java.util.Stack.peek()` and `pop()` throw `EmptyStackException` on an empty stack, while `Deque`'s `peekFirst()`/`pollFirst()` return `null` instead — mixing these two APIs' error-handling styles in the same codebase leads to inconsistent crash-vs-null-check bugs. Pick one API (prefer `Deque`) and stay consistent.

- `push`, `pop`, and `peek` are all O(1) because they only ever touch the single `top` position, tracked directly by an index or a reference.
- This contrasts with front-insertion on an array-backed list, which is O(n) because it must shift every other element.
- Always check `isEmpty()` before `pop()`/`peek()`, or be ready to handle the exception/`null` your chosen API returns.
- Related concepts: [LIFO semantics](0062-lifo-semantics.md), [Array-backed vs linked stack](0063-array-backed-vs-linked-stack.md).
