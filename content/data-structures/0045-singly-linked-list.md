---
card: data-structures
gi: 45
slug: singly-linked-list
title: Singly linked list
---

## 1. What it is

A **singly linked list** is a sequence of **nodes**, where each node holds a value and a single reference (`next`) pointing to the following node. The list itself is just a reference to the first node (the **head**); the last node's `next` points to `null`, marking the end. Unlike an array, nodes are not contiguous in memory — they can live anywhere on the heap, connected only by their `next` pointers.

## 2. Why & when

Use a linked list when you need frequent insertions or deletions at the front (or at a known node), without the O(n) shifting cost an array pays for the same operation. Avoid it when you need frequent indexed access (`get(i)`) or good cache locality, since neither is a strength of a linked list — those are exactly where arrays win instead.

## 3. Core concept

**The core invariant: every node (except the last) points to exactly the next node, and the last node's `next` is `null`.** This invariant is what makes traversal well-defined — starting from `head` and following `next` repeatedly is guaranteed to reach every node exactly once, then reach `null`, and never loop back (as long as no cycle exists).

**Why insertion at the head is O(1).** Creating a new node and pointing it at the current `head`, then updating `head` to the new node, touches exactly two references — no shifting of existing nodes required, unlike an array's front-insertion.

**Why indexed access is O(n).** There is no formula for "the address of the i-th node" the way there is for an array — the only way to reach node `i` is to start at `head` and follow `next` exactly `i` times.

**Memory overhead per element.** Each node needs extra memory for its `next` reference, beyond just the value itself — an array stores only the raw values, contiguously, with no per-element pointer overhead.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A singly linked list of three nodes, head pointing to the first, each node's next pointing to the following node, the last pointing to null">
  <g font-family="sans-serif" font-size="12">
    <text x="40" y="20" fill="#8b949e">head</text>
    <line x1="40" y1="30" x2="70" y2="45" stroke="#79c0ff" marker-end="url(#a11)"/>
    <defs><marker id="a11" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>

    <rect x="70" y="50" width="90" height="40" fill="#161b22" stroke="#3fb950"/>
    <text x="95" y="75" fill="#e6edf3" font-size="11">10</text>
    <text x="140" y="75" fill="#8b949e" font-size="9">next</text>
    <line x1="160" y1="70" x2="220" y2="70" stroke="#79c0ff" marker-end="url(#a11)"/>

    <rect x="220" y="50" width="90" height="40" fill="#161b22" stroke="#3fb950"/>
    <text x="245" y="75" fill="#e6edf3" font-size="11">20</text>
    <text x="290" y="75" fill="#8b949e" font-size="9">next</text>
    <line x1="310" y1="70" x2="370" y2="70" stroke="#79c0ff" marker-end="url(#a11)"/>

    <rect x="370" y="50" width="90" height="40" fill="#161b22" stroke="#3fb950"/>
    <text x="395" y="75" fill="#e6edf3" font-size="11">30</text>
    <text x="440" y="75" fill="#8b949e" font-size="9">next</text>
    <line x1="460" y1="70" x2="500" y2="70" stroke="#8b949e" marker-end="url(#a12)"/>
    <defs><marker id="a12" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
    <text x="520" y="75" fill="#8b949e">null</text>
  </g>
</svg>

`head` points to the first node. Each node's `next` chains to the following node, and the last node's `next` is `null`.

## 5. Runnable example

```java
// SinglyLinkedList.java
public class SinglyLinkedList {

    static class Node {
        int value;
        Node next;
        Node(int value) { this.value = value; }
    }

    static class LinkedList {
        Node head;

        void addFirst(int value) { // O(1): no shifting needed
            Node node = new Node(value);
            node.next = head;
            head = node;
        }

        void printAll() {
            StringBuilder sb = new StringBuilder();
            Node current = head;
            while (current != null) {
                sb.append(current.value).append(" -> ");
                current = current.next;
            }
            sb.append("null");
            System.out.println(sb);
        }

        int size() {
            int count = 0;
            Node current = head;
            while (current != null) {
                count++;
                current = current.next;
            }
            return count;
        }
    }

    // Basic: build a list by repeated head insertion, and traverse it.
    static void basicLevel() {
        LinkedList list = new LinkedList();
        list.addFirst(30);
        list.addFirst(20);
        list.addFirst(10);
        System.out.print("basic: ");
        list.printAll(); // 10 -> 20 -> 30 -> null
    }

    // Intermediate: O(n) size() -- there is no stored length field, unlike an array.
    static void intermediateLevel() {
        LinkedList list = new LinkedList();
        for (int i = 1; i <= 5; i++) list.addFirst(i);
        System.out.println("intermediate: size (computed by full traversal) -> " + list.size());
    }

    // Advanced: O(n) indexed access -- must walk from head, unlike O(1) array indexing.
    static int getAt(LinkedList list, int index) {
        Node current = list.head;
        for (int i = 0; i < index; i++) {
            current = current.next; // no shortcut: must visit every earlier node
        }
        return current.value;
    }

    static void advancedLevel() {
        LinkedList list = new LinkedList();
        list.addFirst(30);
        list.addFirst(20);
        list.addFirst(10); // list is now 10 -> 20 -> 30 -> null
        System.out.println("advanced: getAt(2) -> " + getAt(list, 2)); // 30
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `SinglyLinkedList.java`, then run `java SinglyLinkedList.java`.

## 6. Walkthrough

1. `basicLevel()` calls `addFirst(30)`, `addFirst(20)`, `addFirst(10)` in that order. Each call makes the new node's `next` point at the current `head`, then makes `head` point at the new node — so the list ends up `10 -> 20 -> 30 -> null`, in the reverse order the values were inserted.
2. `printAll()` starts `current` at `head` and follows `next` until it hits `null`, printing each value along the way — this is the standard traversal pattern every linked-list operation builds on.
3. `intermediateLevel()`'s `size()` has no shortcut: it must walk the entire list, incrementing a counter, since — unlike an array — there is no stored `length` field to read directly.
4. `advancedLevel()`'s `getAt(list, 2)` starts at `head` (value 10) and follows `next` twice to reach the third node (value 30) — this O(n) walk is the cost of indexed access on a linked list, in contrast to an array's O(1) `arr[2]`.

## 7. Gotchas & takeaways

> Gotcha: forgetting to set the new node's `next` *before* reassigning `head` (or reassigning `head` in the wrong order relative to the `next` update) silently disconnects part of the list — always link the new node to the rest of the structure first, then update any external reference (like `head`) to point at it.

- A singly linked list is a chain of nodes connected by `next` references; `head` is the only entry point.
- Insertion at the head is O(1); indexed access and reaching the tail both require an O(n) traversal from `head`.
- Each node carries extra memory overhead for its `next` reference, unlike an array's tightly packed values.
- Related concepts: [Doubly linked list](0046-doubly-linked-list.md), [Insert at head / tail / middle](0049-insert-at-head-tail-middle.md).
