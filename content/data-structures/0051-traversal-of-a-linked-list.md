---
card: data-structures
gi: 51
slug: traversal-of-a-linked-list
title: Traversal of a linked list
---

## 1. What it is

**Traversal** means visiting every node in a linked list, one at a time, following `next` references from `head` until reaching the end. It is the foundational operation nearly every other linked-list algorithm builds on — searching, printing, counting, summing, or transforming values all start with the same basic walk.

## 2. Why & when

Every linked-list problem starts by asking "how do I walk this list?" — the answer is almost always some variant of the traversal pattern. Understanding the standard iterative form, its recursive counterpart, and their tradeoffs (call-stack depth versus explicit loop state) is a prerequisite for every other linked-list technique in this section.

## 3. Core concept

**The iterative pattern: a `current` reference stepping forward.** `Node current = head; while (current != null) { ...; current = current.next; }` — this is the universal template. Every step processes `current`, then advances by following its `next` reference, until `current` becomes `null`.

**The recursive pattern: process, then recurse on the rest.** `void traverse(Node node) { if (node == null) return; process(node); traverse(node.next); }` — the base case (`null`) stops the recursion; each call handles one node, then delegates the rest of the list to a recursive call. This naturally mirrors the list's own recursive structure (a node followed by "the rest of the list").

**Why recursion risks a stack overflow on long lists.** Each recursive call adds a frame to the call stack. A list with hundreds of thousands of nodes can exhaust the stack (`StackOverflowError`) with a naive recursive traversal, while the iterative version uses a fixed, small amount of stack space regardless of list length — this is the main practical reason iterative traversal is usually preferred for production code.

**Traversal order for recursion: before vs. after the recursive call.** Processing a node *before* the recursive call (`process(node); traverse(node.next);`) visits nodes in forward order. Processing *after* the recursive call (`traverse(node.next); process(node);`) visits them in reverse order, since each call waits for the rest of the list to finish first — this is the same idea behind [Reverse a linked list (iterative & recursive)](0052-reverse-a-linked-list-iterative-recursive.md).

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A current pointer stepping through three nodes one at a time, versus recursive calls stacking up then unwinding">
  <g font-family="sans-serif" font-size="11">
    <text x="160" y="16" fill="#8b949e" text-anchor="middle">iterative: current steps forward</text>
    <rect x="70" y="30" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="100" y="50" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <rect x="150" y="30" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="180" y="50" fill="#e6edf3" text-anchor="middle" font-size="9">20</text>
    <rect x="230" y="30" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="260" y="50" fill="#e6edf3" text-anchor="middle" font-size="9">30</text>
    <text x="100" y="80" fill="#79c0ff" text-anchor="middle" font-size="9">current</text>

    <text x="480" y="16" fill="#8b949e" text-anchor="middle">recursive: call stack builds, then unwinds</text>
    <rect x="440" y="30" width="150" height="22" fill="#161b22" stroke="#79c0ff"/><text x="515" y="46" fill="#e6edf3" text-anchor="middle" font-size="9">traverse(10)</text>
    <rect x="450" y="55" width="130" height="22" fill="#161b22" stroke="#79c0ff"/><text x="515" y="71" fill="#e6edf3" text-anchor="middle" font-size="9">traverse(20)</text>
    <rect x="460" y="80" width="110" height="22" fill="#161b22" stroke="#79c0ff"/><text x="515" y="96" fill="#e6edf3" text-anchor="middle" font-size="9">traverse(30)</text>
    <text x="320" y="140" fill="#79c0ff" text-anchor="middle">deep lists can overflow the recursive call stack; iterative uses constant stack space</text>
  </g>
</svg>

Iterative traversal moves one reference forward in a loop. Recursive traversal builds a call-stack frame per node before unwinding.

## 5. Runnable example

```java
// LinkedListTraversal.java
public class LinkedListTraversal {

    static class Node {
        int value;
        Node next;
        Node(int value) { this.value = value; }
    }

    // Basic: standard iterative traversal, summing all values.
    static int sumIterative(Node head) {
        int sum = 0;
        Node current = head;
        while (current != null) {
            sum += current.value;
            current = current.next;
        }
        return sum;
    }

    static void basicLevel() {
        Node head = buildList(1, 2, 3, 4, 5);
        System.out.println("basic: iterative sum -> " + sumIterative(head));
    }

    // Intermediate: recursive traversal, processing before the recursive call (forward order).
    static void printForwardRecursive(Node node) {
        if (node == null) return; // base case
        System.out.print(node.value + " "); // process this node...
        printForwardRecursive(node.next);   // ...then recurse on the rest
    }

    static void intermediateLevel() {
        Node head = buildList(1, 2, 3, 4, 5);
        System.out.print("intermediate: forward recursive -> ");
        printForwardRecursive(head);
        System.out.println();
    }

    // Advanced: recursive traversal processing AFTER the recursive call (reverse order).
    static void printReverseRecursive(Node node) {
        if (node == null) return; // base case
        printReverseRecursive(node.next);   // recurse first, all the way to the end...
        System.out.print(node.value + " "); // ...then process on the way back up
    }

    static void advancedLevel() {
        Node head = buildList(1, 2, 3, 4, 5);
        System.out.print("advanced: reverse recursive -> ");
        printReverseRecursive(head);
        System.out.println();
    }

    static Node buildList(int... values) {
        Node dummy = new Node(0), tail = dummy;
        for (int v : values) { tail.next = new Node(v); tail = tail.next; }
        return dummy.next;
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `LinkedListTraversal.java`, then run `java LinkedListTraversal.java`.

## 6. Walkthrough

1. `basicLevel()`'s `sumIterative` starts `current` at `head`, adds each node's value to `sum`, then advances `current = current.next`, stopping when `current` becomes `null` — this visits each of the 5 nodes exactly once, in order, giving `15`.
2. `intermediateLevel()`'s `printForwardRecursive` prints `node.value` *before* calling itself on `node.next` — so `1` prints first (from the outermost call), then `2`, then `3`, and so on, giving `1 2 3 4 5` in forward order.
3. `advancedLevel()`'s `printReverseRecursive` calls itself on `node.next` *before* printing `node.value`. The recursion descends all the way to the last node (`5`) before any printing happens, then each `print` runs as the calls return back up the stack — `5` prints first, then `4`, and so on, giving `5 4 3 2 1`, the reverse order.
4. This before-vs-after placement of the "process" step relative to the recursive call is the entire mechanism behind reverse-order recursive traversal — no explicit stack or extra data structure is needed, since the call stack itself holds the pending nodes.

## 7. Gotchas & takeaways

> Gotcha: recursive traversal on a very long list (tens or hundreds of thousands of nodes) risks `StackOverflowError`, since each recursive call consumes a call-stack frame — Java does not guarantee tail-call optimization. For long lists, prefer the iterative form, which uses a fixed, small amount of stack space regardless of list length.

- Iterative traversal (`current = current.next` in a loop) is the standard, stack-safe pattern for walking a linked list.
- Recursive traversal mirrors the list's own structure, and can process nodes in forward order (before the recursive call) or reverse order (after it).
- Deep recursion risks a stack overflow on long lists; iteration does not have this limitation.
- Related concepts: [Reverse a linked list (iterative & recursive)](0052-reverse-a-linked-list-iterative-recursive.md), [Recursion: the call stack & stack depth](0007-recursion-the-call-stack-stack-depth.md).
