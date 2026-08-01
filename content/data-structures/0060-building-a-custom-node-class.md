---
card: data-structures
gi: 60
slug: building-a-custom-node-class
title: Building a custom Node class
---

## 1. What it is

A **Node** is the basic building block of a linked structure: a small object holding one piece of data plus one or more references to other nodes. Building your own `Node` class — instead of always reaching for `java.util.LinkedList` — is what lets you construct singly linked lists, doubly linked lists, trees, and graphs from scratch, and control exactly what each node stores and how it connects.

## 2. Why & when

You write a custom `Node` class whenever you implement a linked structure yourself: for interview problems, for a specialized structure the standard library does not provide (like a doubly linked list with an extra "random" pointer, or an LRU cache's internal list), or to make a data structure generic and reusable in your own code. The alternative — always using `java.util.LinkedList` — hides the node internals, which is fine for application code but wrong when the task is to demonstrate or extend the structure itself.

## 3. Core concept

**Minimum shape.** A node needs a value field and at least one reference field pointing to another node (`next` for singly linked; `next` and `prev` for doubly linked). In Java this is almost always a small `static` nested class, or a top-level class if it is reused across files.

**Generics make it reusable.** A `Node<T>` with a type parameter lets the same class hold `Integer`, `String`, or any object type, instead of being locked to one type or using raw `Object` (which loses compile-time type safety and needs casts).

**Constructors reduce boilerplate.** A constructor that takes the value (and optionally the next/prev references) lets you build a node in one line — `new Node<>(5)` — instead of setting fields one at a time after a no-arg constructor.

**Encapsulation choice.** Inside a data-structure implementation, fields are often left package-private or public for direct access, since the surrounding class (the list itself) is the only code meant to touch them. If the node type is exposed to external callers, wrap access in getters instead, so callers cannot corrupt the internal links.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A generic Node object with a value field of type T, a next reference, and a prev reference for the doubly linked variant">
  <g font-family="sans-serif" font-size="11">
    <rect x="40" y="20" width="160" height="90" fill="#161b22" stroke="#8b949e" rx="4"/>
    <text x="120" y="38" fill="#e6edf3" text-anchor="middle" font-weight="bold">Node&lt;T&gt;</text>
    <text x="55" y="58" fill="#79c0ff">T value</text>
    <text x="55" y="78" fill="#f0883e">Node&lt;T&gt; next</text>
    <text x="55" y="98" fill="#a5d6ff">Node&lt;T&gt; prev  (doubly linked only)</text>
    <rect x="280" y="20" width="160" height="60" fill="#0d1117" stroke="#8b949e" rx="4"/>
    <text x="360" y="38" fill="#e6edf3" text-anchor="middle" font-size="9">Node&lt;T&gt;(T value)</text>
    <text x="360" y="55" fill="#e6edf3" text-anchor="middle" font-size="9">sets value, next = null</text>
    <line x1="200" y1="60" x2="276" y2="50" stroke="#79c0ff" marker-end="url(#nn)"/>
    <defs><marker id="nn" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
    <text x="240" y="140" fill="#8b949e" text-anchor="middle">the constructor builds one Node; the surrounding list class links many together</text>
  </g>
</svg>

A `Node<T>` bundles a value with the reference(s) needed to reach its neighbours; the constructor initializes those references to `null`.

## 5. Runnable example

```java
// CustomNodeDemo.java
public class CustomNodeDemo {

    // Basic: a minimal generic singly linked node, plus building a 3-node chain by hand.
    static class Node<T> {
        T value;
        Node<T> next;
        Node(T value) { this.value = value; }
    }

    static void basicLevel() {
        Node<Integer> head = new Node<>(1);
        head.next = new Node<>(2);
        head.next.next = new Node<>(3);

        StringBuilder sb = new StringBuilder();
        for (Node<Integer> c = head; c != null; c = c.next) sb.append(c.value).append(" ");
        System.out.println("basic: chain -> " + sb.toString().trim());
    }

    // Intermediate: a doubly linked node, with a constructor overload and a helper to append.
    static class DoublyNode<T> {
        T value;
        DoublyNode<T> next;
        DoublyNode<T> prev;

        DoublyNode(T value) { this.value = value; }

        DoublyNode(T value, DoublyNode<T> prev) {
            this.value = value;
            this.prev = prev;
        }
    }

    static DoublyNode<String> appendDoubly(DoublyNode<String> tail, String value) {
        DoublyNode<String> node = new DoublyNode<>(value, tail);
        if (tail != null) tail.next = node;
        return node;
    }

    static void intermediateLevel() {
        DoublyNode<String> head = new DoublyNode<>("a");
        DoublyNode<String> tail = appendDoubly(head, "b");
        tail = appendDoubly(tail, "c");

        StringBuilder forward = new StringBuilder();
        for (DoublyNode<String> c = head; c != null; c = c.next) forward.append(c.value).append(" ");
        StringBuilder backward = new StringBuilder();
        for (DoublyNode<String> c = tail; c != null; c = c.prev) backward.append(c.value).append(" ");

        System.out.println("intermediate: forward -> " + forward.toString().trim());
        System.out.println("intermediate: backward -> " + backward.toString().trim());
    }

    // Advanced: a node with an extra field (frequency), used to build a small structure like an LFU cache entry.
    static class FreqNode<K, V> {
        K key;
        V value;
        int frequency = 1;
        FreqNode<K, V> next;

        FreqNode(K key, V value) { this.key = key; this.value = value; }

        void touch() { frequency++; }
    }

    static void advancedLevel() {
        FreqNode<String, Integer> head = new FreqNode<>("views", 10);
        head.next = new FreqNode<>("clicks", 3);
        head.touch();
        head.touch();

        System.out.println("advanced: head key -> " + head.key + ", frequency -> " + head.frequency);
        System.out.println("advanced: second node key -> " + head.next.key + ", frequency -> " + head.next.frequency);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `CustomNodeDemo.java`, then run `java CustomNodeDemo.java`.

## 6. Walkthrough

1. `basicLevel()` allocates three `Node<Integer>` objects and links them by hand through `.next`, then walks the chain from `head` to `null`, printing each value in order: `1 2 3`.
2. `intermediateLevel()` builds a `DoublyNode<String>` chain using a constructor overload that sets `prev` at creation time, and `appendDoubly` wires the new node's `prev` back to the current tail, and the old tail's `next` forward to the new node. Walking forward from `head` gives `a b c`; walking backward from `tail` via `prev` gives `c b a` — proof both directions of the links are correctly wired.
3. `advancedLevel()` shows a node carrying extra state beyond a value and a link — a `frequency` counter, as you would need inside an LFU (least-frequently-used) cache's internal node. Calling `touch()` twice raises `head.frequency` from `1` to `3`, showing the node's own field, not just its links, drives structure-specific behaviour.

## 7. Gotchas & takeaways

> Gotcha: forgetting to initialize `next` (and `prev`) explicitly is usually fine in Java, since object reference fields default to `null` — but relying on that default without a comment can confuse a reader who does not know the language's default-initialization rule. State it in the constructor when it matters for clarity.

- A `Node<T>` needs a value field and one reference field per direction of traversal you support.
- Generics (`Node<T>`) make the node reusable across value types without casts.
- A doubly linked node's `prev` and `next` must both be kept in sync on every insert or remove, or the two directions of traversal disagree.
- Extra fields (like a frequency counter or a random pointer) turn a plain node into the building block for a more specialized structure.
- Related concepts: [Singly linked list](0045-singly-linked-list.md), [Doubly linked list](0046-doubly-linked-list.md), [java.util.LinkedList (List + Deque)](0059-java-util-linkedlist-list-deque.md).
