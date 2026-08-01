---
card: data-structures
gi: 71
slug: legacy-java-util-stack-why-to-avoid-it
title: Legacy java.util.Stack & why to avoid it
---

## 1. What it is

`java.util.Stack` is Java's original stack class, part of the language since Java 1.0. It provides `push`, `pop`, `peek`, and `empty()`. It is still in the standard library and still works correctly — but it carries design baggage that makes `ArrayDeque` the better choice for new code.

## 2. Why & when

You will still see `java.util.Stack` in older codebases and some interview solutions, so you need to recognize it and understand its downsides — even though you should not choose it for new code. This is the classic "know it, don't use it" library class, useful to compare against `ArrayDeque` to understand *why* the newer API is preferred.

## 3. Core concept

**What backs it, and why that is a problem.** `Stack` extends `Vector`, a legacy, **synchronized** (thread-safe via locking) dynamic array class from Java 1.0. Every single `push`/`pop`/`peek` call acquires a lock, even in single-threaded code that never needs thread safety — pure overhead most programs pay for nothing.

**It breaks encapsulation.** Because `Stack extends Vector`, every `Vector`/`List` method is also available on a `Stack` — `add(int index, E element)`, `remove(int index)`, `get(int index)`. This means code can insert or remove from the *middle* of a "stack," silently violating the entire point of a stack (LIFO-only access). `ArrayDeque` does not extend `List`, so this mistake is impossible.

**Ordering and complexity guarantees.** Functionally, `push`/`pop`/`peek` are still O(1), same as `ArrayDeque` — the algorithmic complexity is not the issue. The issues are the unnecessary synchronization overhead and the broken encapsulation.

**When to choose it: never, for new code.** The only reason to use `Stack` today is maintaining or reading existing code that already uses it. The official Java documentation for `Deque` explicitly recommends `ArrayDeque` over `Stack` for stack operations.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Class hierarchy showing Stack extends Vector, which extends List, exposing get and remove by index that break the stack-only contract; ArrayDeque implements Deque directly with no such leak">
  <g font-family="sans-serif" font-size="11">
    <rect x="30" y="20" width="140" height="30" fill="#0d1117" stroke="#f0883e" rx="4"/><text x="100" y="40" fill="#e6edf3" text-anchor="middle" font-size="9">Stack</text>
    <line x1="100" y1="50" x2="100" y2="70" stroke="#f0883e" marker-end="url(#ex)"/>
    <rect x="30" y="70" width="140" height="30" fill="#161b22" stroke="#8b949e" rx="4"/><text x="100" y="90" fill="#e6edf3" text-anchor="middle" font-size="9">Vector (extends List)</text>
    <text x="100" y="120" fill="#f0883e" text-anchor="middle" font-size="9">inherits get(i), remove(i) -- breaks LIFO-only contract</text>
    <defs><marker id="ex" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker></defs>

    <rect x="380" y="20" width="160" height="30" fill="#0d1117" stroke="#79c0ff" rx="4"/><text x="460" y="40" fill="#e6edf3" text-anchor="middle" font-size="9">ArrayDeque</text>
    <line x1="460" y1="50" x2="460" y2="70" stroke="#79c0ff" marker-end="url(#im)"/>
    <rect x="380" y="70" width="160" height="30" fill="#161b22" stroke="#8b949e" rx="4"/><text x="460" y="90" fill="#e6edf3" text-anchor="middle" font-size="9">implements Deque only</text>
    <defs><marker id="im" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
    <text x="460" y="120" fill="#79c0ff" text-anchor="middle" font-size="9">no List methods leaked -- LIFO-only by construction</text>
  </g>
</svg>

`Stack`'s inheritance from `Vector` (a `List`) leaks indexed methods that let code bypass LIFO order; `ArrayDeque` implements only `Deque`, so no such leak is possible.

## 5. Runnable example

```java
// LegacyStackDemo.java
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Stack;

public class LegacyStackDemo {

    // Basic: java.util.Stack works correctly for normal push/pop/peek use.
    static void basicLevel() {
        Stack<Integer> stack = new Stack<>();
        stack.push(1);
        stack.push(2);
        stack.push(3);
        System.out.println("basic: peek -> " + stack.peek());
        System.out.println("basic: pop -> " + stack.pop());
    }

    // Intermediate: the encapsulation break -- Stack lets you touch the middle, defeating LIFO.
    static void intermediateLevel() {
        Stack<Integer> stack = new Stack<>();
        stack.push(10);
        stack.push(20);
        stack.push(30);
        System.out.println("intermediate: before -> " + stack);

        stack.remove(1); // removes the MIDDLE element (index 1, value 20) -- legal, and a bug waiting to happen
        System.out.println("intermediate: after stack.remove(1) (a List method) -> " + stack);
        System.out.println("intermediate: this compiles because Stack extends Vector, which extends List");

        // ArrayDeque has no such method to misuse -- Deque exposes only end-based operations.
        Deque<Integer> properStack = new ArrayDeque<>(java.util.List.of(10, 20, 30));
        System.out.println("intermediate: ArrayDeque has no remove(int index) method -- this class of bug cannot happen");
    }

    // Advanced: rough timing comparison -- Stack's synchronization overhead vs ArrayDeque, single-threaded.
    static void advancedLevel() {
        int n = 2_000_000;

        Stack<Integer> legacy = new Stack<>();
        long t0 = System.nanoTime();
        for (int i = 0; i < n; i++) legacy.push(i);
        for (int i = 0; i < n; i++) legacy.pop();
        long legacyMs = (System.nanoTime() - t0) / 1_000_000;

        Deque<Integer> modern = new ArrayDeque<>();
        long t1 = System.nanoTime();
        for (int i = 0; i < n; i++) modern.push(i);
        for (int i = 0; i < n; i++) modern.pop();
        long modernMs = (System.nanoTime() - t1) / 1_000_000;

        System.out.println("advanced: " + n + " push+pop pairs -> Stack: " + legacyMs + " ms, ArrayDeque: " + modernMs + " ms");
        System.out.println("advanced: Stack pays lock overhead on every call, even single-threaded");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `LegacyStackDemo.java`, then run `java LegacyStackDemo.java`.

## 6. Walkthrough

1. `basicLevel()` shows `Stack` working correctly for ordinary use — push `1, 2, 3`, `peek()` returns `3`, `pop()` returns `3`. Nothing here looks wrong yet.
2. `intermediateLevel()` builds `[10, 20, 30]` (bottom to top) and calls `stack.remove(1)` — a `List` method inherited from `Vector`, that removes the element at index `1` (value `20`) from the *middle*. This compiles and runs without error, silently corrupting what should be a LIFO-only structure. The `ArrayDeque` equivalent has no `remove(int index)` method at all, so this class of bug is caught at compile time, not left as a runtime surprise.
3. `advancedLevel()` times two million push+pop pairs on each class. `Stack` is typically measurably slower, since every call acquires and releases `Vector`'s internal lock, even though this code never touches the stack from more than one thread.

## 7. Gotchas & takeaways

> Gotcha: because `Stack` is a `List`, passing a `Stack<T>` to any method expecting a `List<T>` compiles fine — and that method could call `add(0, x)`, `set(i, x)`, or `sort()` on it, none of which respect stack semantics at all. `ArrayDeque` cannot be passed where a `List` is expected, which is a feature, not a limitation.

- `Stack` still works correctly for `push`/`pop`/`peek`, but carries two real costs: unnecessary lock overhead, and a broken encapsulation (`List` methods leak through).
- `ArrayDeque` implements only `Deque`, so indexed mid-structure access is impossible by construction.
- Java's own documentation recommends `ArrayDeque` over `Stack` for stack use.
- Recognize `Stack` in legacy code; do not introduce it in new code.
- Related concepts: [ArrayDeque as a stack (preferred)](0070-arraydeque-as-a-stack-preferred.md), [LIFO semantics](0062-lifo-semantics.md).
