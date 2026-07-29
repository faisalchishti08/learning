---
card: leetcode-patterns
gi: 579
slug: design-linked-list
title: Design Linked List
---

## 1. What it is

Design a `MyLinkedList` class supporting `get(index)` (value at `index`, or `-1` if out of range), `addAtHead(val)`, `addAtTail(val)`, `addAtIndex(index, val)` (insert before the node currently at `index`), and `deleteAtIndex(index)`, all zero-indexed. Example: `addAtHead(1)`, `addAtTail(3)`, `addAtIndex(1,2)` → list is `[1,2,3]`, `get(1)` → `2`, `deleteAtIndex(0)` → list is `[2,3]`, `get(0)` → `2`.

## 2. Why & when

This problem asks you to build the pointer-chasing mechanics that a language's built-in `LinkedList` type normally hides. Constraints: up to `2,000` calls across all methods, and index/value bounds within `int` range — small enough that O(index) traversal per call is fast enough, so the focus is entirely on getting the pointer bookkeeping correct, not on beating a stricter time limit.

## 3. Core concept

**Key idea:** each node holds a value and a `next` pointer. Maintain a `head` pointer to the first real node (or `null` if empty) and a `size` counter, so index-out-of-range checks are simple arithmetic instead of pointer chasing to find the end.

**Steps:**
1. `get(index)`: reject if `index < 0` or `index >= size`. Otherwise, walk `next` pointers `index` times from `head` and return that node's value.
2. `addAtHead(val)`: create a new node whose `next` is the current `head`; set `head` to the new node; increment `size`.
3. `addAtTail(val)`: walk to the last node (or, if empty, treat it like `addAtHead`) and set its `next` to a new node; increment `size`.
4. `addAtIndex(index, val)`: reject if `index > size`. If `index <= 0`, delegate to `addAtHead`. Otherwise, walk to the node just before `index`, then splice in the new node between it and its current `next`; increment `size`.
5. `deleteAtIndex(index)`: reject if `index < 0` or `index >= size`. Walk to the node just before `index` (or handle `head` directly if `index == 0`), then relink its `next` to skip over the target node; decrement `size`.

**Why "the node just before the target" is the recurring sub-step:** a singly linked list has no `prev` pointer, so inserting or deleting at position `index` requires a reference to position `index - 1` in order to rewrite its `next` pointer. This one walk-to-predecessor step is reused by both `addAtIndex` and `deleteAtIndex`.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inserting a node at index 1 by rewriting the predecessor's next pointer">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="30" width="70" height="35" rx="4" fill="#161b22" stroke="#3fb950"/>
    <text x="55" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">1 (head)</text>
    <rect x="180" y="30" width="70" height="35" rx="4" fill="#161b22" stroke="#3fb950"/>
    <text x="215" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <rect x="100" y="90" width="70" height="35" rx="4" fill="#161b22" stroke="#f0883e"/>
    <text x="135" y="112" fill="#e6edf3" text-anchor="middle" font-size="11">2 (new)</text>
    <line x1="90" y1="47" x2="100" y2="107" stroke="#f0883e" stroke-dasharray="3,2" marker-end="url(#a6)"/>
    <line x1="170" y1="107" x2="180" y2="47" stroke="#f0883e" stroke-dasharray="3,2" marker-end="url(#a6)"/>
    <line x1="90" y1="47" x2="180" y2="47" stroke="#8b949e" stroke-dasharray="2,4"/>
    <defs><marker id="a6" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker></defs>
    <text x="350" y="140" fill="#8b949e" text-anchor="middle">node 1's next is rewritten to point at the new node 2, whose next points to node 3</text>
  </g>
</svg>

Inserting between two nodes needs a reference to the predecessor — its `next` pointer is what gets rewritten to splice in the new node.

## 5. Runnable example

**Level 1 — Brute force.** Backing the list with a resizable array (an `ArrayList`) makes `get` O(1), but `addAtHead`/`addAtIndex`/`deleteAtIndex` become O(n) due to shifting elements — arguably simpler to write, but it defeats the purpose of a linked-list exercise.

**KEY INSIGHT:** a singly linked list trades O(1) index access for O(1) insert/delete **once you already hold a reference to the right predecessor node** — the real work in every method is walking to that predecessor.

**Level 2 — Optimal.** True node-and-pointer singly linked list; each method walks at most `size` nodes, matching the problem's small constraints.

**Level 3 — Hardened.** Correctly handles inserting/deleting at `index == 0` (touches `head` directly, no predecessor exists) and rejects out-of-range indices for every method.

```java
// MyLinkedList.java
public class MyLinkedList {

    static class Node {
        int val;
        Node next;
        Node(int val) { this.val = val; }
    }

    private Node head;
    private int size;

    public int get(int index) {
        if (index < 0 || index >= size) return -1;
        Node cur = head;
        for (int i = 0; i < index; i++) cur = cur.next;
        return cur.val;
    }

    public void addAtHead(int val) {
        Node node = new Node(val);
        node.next = head;
        head = node;
        size++;
    }

    public void addAtTail(int val) {
        if (size == 0) {
            addAtHead(val);
            return;
        }
        Node cur = head;
        while (cur.next != null) cur = cur.next;
        cur.next = new Node(val);
        size++;
    }

    public void addAtIndex(int index, int val) {
        if (index > size) return;
        if (index <= 0) {
            addAtHead(val);
            return;
        }
        Node predecessor = head;
        for (int i = 0; i < index - 1; i++) predecessor = predecessor.next;
        Node node = new Node(val);
        node.next = predecessor.next;
        predecessor.next = node;
        size++;
    }

    public void deleteAtIndex(int index) {
        if (index < 0 || index >= size) return;
        if (index == 0) {
            head = head.next;
            size--;
            return;
        }
        Node predecessor = head;
        for (int i = 0; i < index - 1; i++) predecessor = predecessor.next;
        predecessor.next = predecessor.next.next;
        size--;
    }

    public static void main(String[] args) {
        MyLinkedList list = new MyLinkedList();
        list.addAtHead(1);
        list.addAtTail(3);
        list.addAtIndex(1, 2); // list: 1 -> 2 -> 3
        System.out.println(list.get(1)); // 2
        list.deleteAtIndex(0);           // list: 2 -> 3
        System.out.println(list.get(0)); // 2
    }
}
```

**How to run:** save as `MyLinkedList.java`, then run `java MyLinkedList.java`.

## 6. Walkthrough

Trace `addAtHead(1)`, `addAtTail(3)`, `addAtIndex(1,2)`, `get(1)`:

1. `addAtHead(1)`: `head` was `null`. New node `1` becomes `head`. List: `1`. `size=1`.
2. `addAtTail(3)`: `size != 0`, walk from `head` (`1`) to the last node (still `1`, since `1.next == null`), attach `3`. List: `1 -> 3`. `size=2`.
3. `addAtIndex(1,2)`: `index=1`, not `<=0`, so walk to the predecessor at `index-1=0`: that is `head` itself, node `1`. Splice: new node `2`'s `next` becomes `predecessor.next` (node `3`); `predecessor.next` becomes node `2`. List: `1 -> 2 -> 3`. `size=3`.
4. `get(1)`: walk one step from `head`: `1 -> 2`. Return `2`.

## 7. Gotchas & takeaways

> Gotcha: for `addAtIndex` and `deleteAtIndex`, walking `index` steps instead of `index - 1` steps lands you *on* the target node instead of its predecessor — since a singly linked list has no `prev` pointer, that one-step error makes it impossible to rewrite the correct `next` link.

- Signal: "design a linked list from scratch" means implement the node/pointer mechanics yourself, not wrap a built-in `LinkedList`.
- The recurring sub-step for both insert and delete is "walk to the predecessor," since only the predecessor's `next` pointer can be rewritten.
- Related problems: LRU Cache (a doubly linked list, which adds a `prev` pointer so predecessor-walking is not needed), Design Circular Queue (a linked list constrained to a fixed capacity with wraparound).
