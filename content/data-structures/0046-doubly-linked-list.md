---
card: data-structures
gi: 46
slug: doubly-linked-list
title: Doubly linked list
---

## 1. What it is

A **doubly linked list** extends a singly linked list by giving every node a second reference, `prev`, pointing back to the previous node — not just `next` pointing forward. This lets you walk the list in either direction, and (given a reference to a node) delete or insert around it in O(1), without needing to first find its predecessor by scanning from the head.

## 2. Why & when

Use a doubly linked list when you need to traverse backward as well as forward, or when you need O(1) deletion of a node you already have a reference to (an LRU cache's eviction logic is the classic example, built on `LinkedHashMap`, which itself uses a doubly linked list internally). The cost is extra memory (one more pointer per node) and slightly more bookkeeping on every insert/delete.

## 3. Core concept

**The invariant: every node's `next.prev` points back to itself, and every node's `prev.next` points forward to itself.** This symmetry must hold after every operation — it is exactly what makes backward traversal (`current = current.prev`) as reliable as forward traversal.

**Why O(1) deletion of a known node becomes possible.** In a singly linked list, deleting a node you have a direct reference to still requires finding its *predecessor* by scanning from the head (to update the predecessor's `next`) — an O(n) operation. In a doubly linked list, the node's own `prev` reference already points at its predecessor, so deletion needs no search: just relink `node.prev.next = node.next` and `node.next.prev = node.prev`.

**Every insert/delete must update pointers on both sides.** Inserting a new node between `a` and `b` means setting four references: the new node's `next` and `prev`, plus `a.next` and `b.prev` — miss any one of them, and the invariant breaks, silently corrupting later traversals.

**Common use: backing structure for `LinkedHashMap`/`LinkedList` and LRU caches.** Java's own `java.util.LinkedList` is doubly linked internally, which is why it can implement `Deque` (efficient operations at both ends) and support backward iteration.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A doubly linked list of three nodes, each with next pointing forward and prev pointing backward, forming a symmetric chain">
  <g font-family="sans-serif" font-size="11">
    <rect x="90" y="50" width="90" height="50" fill="#161b22" stroke="#3fb950"/>
    <text x="115" y="70" fill="#e6edf3" font-size="11">10</text>
    <text x="135" y="88" fill="#8b949e" font-size="8">prev=null</text>

    <rect x="270" y="50" width="90" height="50" fill="#161b22" stroke="#3fb950"/>
    <text x="295" y="70" fill="#e6edf3" font-size="11">20</text>

    <rect x="450" y="50" width="90" height="50" fill="#161b22" stroke="#3fb950"/>
    <text x="475" y="70" fill="#e6edf3" font-size="11">30</text>
    <text x="470" y="88" fill="#8b949e" font-size="8">next=null</text>

    <line x1="180" y1="65" x2="265" y2="65" stroke="#79c0ff" marker-end="url(#a13)"/>
    <line x1="270" y1="85" x2="185" y2="85" stroke="#f0883e" marker-end="url(#a14)"/>
    <line x1="360" y1="65" x2="445" y2="65" stroke="#79c0ff" marker-end="url(#a13)"/>
    <line x1="450" y1="85" x2="365" y2="85" stroke="#f0883e" marker-end="url(#a14)"/>
    <defs>
      <marker id="a13" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker>
      <marker id="a14" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker>
    </defs>
    <text x="320" y="140" fill="#79c0ff" text-anchor="middle">blue = next (forward), orange = prev (backward) -- both directions walkable</text>
  </g>
</svg>

Each node links both forward (`next`) and backward (`prev`), forming a symmetric chain that can be traversed either way.

## 5. Runnable example

```java
// DoublyLinkedList.java
public class DoublyLinkedList {

    static class Node {
        int value;
        Node prev, next;
        Node(int value) { this.value = value; }
    }

    static class DLL {
        Node head, tail;

        void addLast(int value) { // O(1): append at the tail using the prev reference
            Node node = new Node(value);
            if (tail == null) {
                head = tail = node;
            } else {
                node.prev = tail;
                tail.next = node;
                tail = node;
            }
        }

        void printForward() {
            StringBuilder sb = new StringBuilder();
            for (Node c = head; c != null; c = c.next) sb.append(c.value).append(" <-> ");
            System.out.println("forward: " + sb + "null");
        }

        void printBackward() {
            StringBuilder sb = new StringBuilder();
            for (Node c = tail; c != null; c = c.prev) sb.append(c.value).append(" <-> ");
            System.out.println("backward: " + sb + "null");
        }

        void deleteNode(Node node) { // O(1) given a direct reference -- no scanning needed
            if (node.prev != null) node.prev.next = node.next; else head = node.next;
            if (node.next != null) node.next.prev = node.prev; else tail = node.prev;
        }
    }

    // Basic: build the list at the tail, traverse forward and backward.
    static void basicLevel() {
        DLL list = new DLL();
        list.addLast(10);
        list.addLast(20);
        list.addLast(30);
        System.out.print("basic: ");
        list.printForward();
        System.out.print("basic: ");
        list.printBackward();
    }

    // Intermediate: deleting a known middle node in O(1), no traversal from head needed.
    static void intermediateLevel() {
        DLL list = new DLL();
        list.addLast(10);
        Node middle = new Node(20);
        // manually link 'middle' in between 10 and 30 to obtain a direct reference to it
        list.head.next = middle; middle.prev = list.head; list.tail = middle;
        list.addLast(30);

        list.deleteNode(middle); // O(1): uses middle.prev and middle.next directly
        System.out.print("intermediate: after deleting middle node -> ");
        list.printForward();
    }

    // Advanced: verify the invariant -- every node's next.prev points back to itself.
    static void advancedLevel() {
        DLL list = new DLL();
        list.addLast(1);
        list.addLast(2);
        list.addLast(3);

        boolean invariantHolds = true;
        for (Node c = list.head; c != null && c.next != null; c = c.next) {
            if (c.next.prev != c) invariantHolds = false;
        }
        System.out.println("advanced: prev/next invariant holds -> " + invariantHolds);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `DoublyLinkedList.java`, then run `java DoublyLinkedList.java`.

## 6. Walkthrough

1. `basicLevel()` appends `10`, `20`, `30` at the tail. `printForward()` walks `next` references from `head`, printing `10 <-> 20 <-> 30 <-> null`; `printBackward()` walks `prev` references from `tail`, printing the same values in reverse: `30 <-> 20 <-> 10 <-> null`.
2. `intermediateLevel()` manually links a `middle` node between the head (`10`) and a newly appended tail (`30`), giving direct access to `middle`. Calling `deleteNode(middle)` relinks `list.head.next` to skip past `middle` directly to `30`, and sets `30`'s `prev` back to `10` — both sides updated, no traversal from `head` needed to find `middle`'s neighbors.
3. `advancedLevel()` walks the list checking that for every node `c` with a `next`, `c.next.prev` points back to `c` — confirming the doubly linked invariant holds after all the insertions performed so far.

## 7. Gotchas & takeaways

> Gotcha: updating only one side of a link (e.g. setting `a.next = b` but forgetting `b.prev = a`) leaves the list in an inconsistent state — forward traversal might look correct while backward traversal silently breaks, since the two directions are maintained by entirely separate pointers that must both be kept in sync.

- A doubly linked list adds a `prev` reference to every node, enabling backward traversal and O(1) deletion given a direct node reference.
- Every insert or delete must correctly update pointers on both sides of the affected node(s) to preserve the prev/next symmetry.
- Java's own `LinkedList` is doubly linked internally, which is why it can act as an efficient `Deque`.
- Related concepts: [Singly linked list](0045-singly-linked-list.md), [Delete by node & by value](0050-delete-by-node-by-value.md).
