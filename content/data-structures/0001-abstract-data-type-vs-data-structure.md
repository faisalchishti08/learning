---
card: data-structures
gi: 1
slug: abstract-data-type-vs-data-structure
title: Abstract data type vs data structure
---

## 1. What it is

An **abstract data type (ADT)** is a description of *what* operations a container supports and what they guarantee — for example, a "stack" ADT guarantees `push`, `pop`, and `peek`, with `pop` always returning the most recently pushed item. A **data structure** is the concrete *implementation* that makes those operations work — for example, a resizable array or a linked list, each with different performance characteristics for the same stack behavior.

## 2. Why & when

This distinction matters whenever you choose how to build something: the ADT tells you the contract your code can rely on (what methods exist, what they promise), while the data structure tells you the cost of using that contract (how fast each method runs, how much memory it uses). Confusing the two leads to either over-committing to one implementation's specific quirks, or under-thinking the performance consequences of an implementation choice.

## 3. Core concept

**The relationship:** one ADT can have multiple valid data-structure implementations, each with different tradeoffs. A "queue" ADT (guaranteeing first-in-first-out order via `enqueue`/`dequeue`) can be implemented with a linked list (O(1) enqueue and dequeue), a circular array buffer (O(1) enqueue and dequeue, but a fixed capacity), or even two stacks (amortized O(1), simpler to reason about but with occasional O(n) operations).

**How to tell them apart when reading a problem or API:** an ADT is described purely in terms of *behavior* — "what goes in, what comes out, in what order" — with no mention of arrays, pointers, or memory layout. A data structure is described in terms of *mechanism* — arrays, nodes, pointers, hashing — the actual machinery that makes the behavior happen.

**Why this separation is useful in practice:** Java's `List` interface is an ADT (ordered collection, indexed access, `add`/`get`/`remove`); `ArrayList` and `LinkedList` are two different data structures implementing that same ADT. Code written against the `List` interface works with either implementation, but *which* one you pick determines whether `get(index)` is O(1) or O(n) — the ADT does not promise a specific performance, only a specific behavior.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One Queue ADT with two different underlying data structure implementations, each with different performance characteristics">
  <g font-family="sans-serif" font-size="12">
    <rect x="270" y="20" width="160" height="45" rx="6" fill="#161b22" stroke="#79c0ff"/>
    <text x="350" y="47" fill="#e6edf3" text-anchor="middle">Queue ADT</text>
    <text x="350" y="62" fill="#8b949e" text-anchor="middle" font-size="10">enqueue, dequeue, FIFO order</text>
    <rect x="60" y="110" width="200" height="45" rx="6" fill="#161b22" stroke="#3fb950"/>
    <text x="160" y="137" fill="#e6edf3" text-anchor="middle">Linked list</text>
    <text x="160" y="152" fill="#8b949e" text-anchor="middle" font-size="10">O(1) enqueue/dequeue</text>
    <rect x="440" y="110" width="200" height="45" rx="6" fill="#161b22" stroke="#f0883e"/>
    <text x="540" y="137" fill="#e6edf3" text-anchor="middle">Circular array buffer</text>
    <text x="540" y="152" fill="#8b949e" text-anchor="middle" font-size="10">O(1), fixed capacity</text>
    <line x1="300" y1="65" x2="160" y2="110" stroke="#8b949e"/>
    <line x1="400" y1="65" x2="540" y2="110" stroke="#8b949e"/>
  </g>
</svg>

Both implementations satisfy the same Queue ADT contract, but they differ in memory layout, capacity flexibility, and constant-factor performance.

## 5. Runnable example

The artifact below shows two different data structures implementing the same "stack" ADT (a common `Stack` interface), demonstrating that client code can use either interchangeably while their internal mechanisms differ.

```java
// AdtVsDataStructure.java
import java.util.*;

public class AdtVsDataStructure {

    // The ADT: a contract, described purely by behavior.
    interface SimpleStack<T> {
        void push(T item);
        T pop();
        boolean isEmpty();
    }

    // Implementation 1: array-backed data structure.
    static class ArrayStack<T> implements SimpleStack<T> {
        private final List<T> data = new ArrayList<>();
        public void push(T item) { data.add(item); }
        public T pop() { return data.remove(data.size() - 1); }
        public boolean isEmpty() { return data.isEmpty(); }
    }

    // Implementation 2: linked-list-backed data structure.
    static class LinkedStack<T> implements SimpleStack<T> {
        private final Deque<T> data = new ArrayDeque<>();
        public void push(T item) { data.push(item); }
        public T pop() { return data.pop(); }
        public boolean isEmpty() { return data.isEmpty(); }
    }

    static <T> void demo(SimpleStack<T> stack, T a, T b) {
        stack.push(a);
        stack.push(b);
        System.out.println("popped: " + stack.pop() + ", isEmpty: " + stack.isEmpty());
    }

    public static void main(String[] args) {
        demo(new ArrayStack<Integer>(), 1, 2);  // same ADT behavior
        demo(new LinkedStack<Integer>(), 1, 2); // different implementation, identical behavior
    }
}
```

**How to run:** save as `AdtVsDataStructure.java`, then run `java AdtVsDataStructure.java`.

## 6. Walkthrough

1. `demo` is written entirely against the `SimpleStack<T>` interface (the ADT) — it never references `ArrayList` or `ArrayDeque` directly.
2. Calling `demo(new ArrayStack<>(), 1, 2)`: `push(1)` appends `1` to an internal `ArrayList`; `push(2)` appends `2`. `pop()` removes and returns the last element, `2`. `isEmpty()` returns `false` (one element, `1`, remains).
3. Calling `demo(new LinkedStack<>(), 1, 2)`: `push(1)` and `push(2)` add to the front of an internal `ArrayDeque`. `pop()` removes and returns `2`, the same result as the array-backed version.
4. Both calls print identical output (`popped: 2, isEmpty: false`), even though one implementation is array-backed and the other is linked-list-backed — the ADT's guaranteed behavior is what `demo` relies on, and both implementations satisfy it.

## 7. Gotchas & takeaways

> Gotcha: writing code that depends on a data structure's *specific* implementation detail (like assuming `ArrayList.remove(0)` is fast) instead of the ADT's actual contract (a `List` only promises ordered access, not O(1) removal from the front) creates hidden performance bugs when the underlying implementation is swapped for a different one that also satisfies the same ADT.

- An ADT is a behavioral contract; a data structure is the mechanism that implements it — always check which one a description is actually specifying.
- The same ADT can have multiple valid implementations with different performance tradeoffs — picking the right one requires knowing the ADT's operations *and* your actual usage pattern.
- Related concepts: [Big-O, Big-Theta, Big-Omega notation](0002-big-o-big-theta-big-omega-notation.md) (the language used to describe a data structure's performance once an implementation is chosen).
