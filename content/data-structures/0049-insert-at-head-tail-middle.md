---
card: data-structures
gi: 49
slug: insert-at-head-tail-middle
title: Insert at head / tail / middle
---

## 1. What it is

Inserting into a linked list means creating a new node and relinking `next` references so the new node takes its place in the chain. The cost depends entirely on *where* you insert: at the **head** (O(1), just redirect a couple of references), at the **tail** (O(1) with a maintained `tail` reference, or O(n) without one), or in the **middle** (O(1) to relink once you have a reference to the node just before the insertion point, but O(n) to *find* that node in the first place).

## 2. Why & when

Understanding these costs is essential for choosing where in your algorithm to insert, and whether to maintain a `tail` reference. A linked list's "O(1) insertion" reputation is only fully true at the head, or at the tail if you track it explicitly — inserting at an arbitrary position still costs O(n) overall, dominated by the search to reach that position.

## 3. Core concept

**Head insertion: always O(1).** Point the new node's `next` at the current `head`, then update `head` to the new node. No searching is needed, since the head is always directly accessible.

**Tail insertion: O(1) with a `tail` reference, O(n) without one.** If the list maintains a `tail` pointer, appending is just: point the old tail's `next` at the new node, then update `tail`. Without a maintained `tail`, you must traverse the whole list from `head` to find the current last node first — O(n).

**Middle insertion: O(1) to relink, but O(n) to find the spot.** Given a reference to the node just *before* the target position, insertion is three pointer updates: the new node's `next` becomes the previous node's old `next`, and the previous node's `next` becomes the new node. But reaching "the node just before position k" from `head` costs O(k) — for a middle position, that is O(n) in the worst case.

**Order of operations matters.** Always set the new node's `next` *before* changing the predecessor's `next` to point at the new node — reversing this order loses the reference to the rest of the list.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inserting a new node between two existing nodes by first pointing the new node forward, then relinking the predecessor" >
  <g font-family="sans-serif" font-size="11">
    <text x="320" y="16" fill="#8b949e" text-anchor="middle">insert 15 between 10 and 20</text>
    <rect x="60" y="30" width="80" height="35" fill="#161b22" stroke="#3fb950"/><text x="100" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">10</text>
    <rect x="440" y="30" width="80" height="35" fill="#161b22" stroke="#3fb950"/><text x="480" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">20</text>
    <line x1="140" y1="47" x2="435" y2="47" stroke="#8b949e" stroke-dasharray="3,3"/>

    <rect x="250" y="90" width="80" height="35" fill="#0d1117" stroke="#f0883e"/><text x="290" y="112" fill="#e6edf3" text-anchor="middle" font-size="10">15 (new)</text>
    <text x="290" y="145" fill="#f0883e" text-anchor="middle" font-size="10">step 1: new.next = 20</text>

    <line x1="140" y1="55" x2="250" y2="105" stroke="#79c0ff" marker-end="url(#a18)"/>
    <text x="180" y="150" fill="#79c0ff" text-anchor="middle" font-size="10">step 2: 10.next = 15</text>
    <defs><marker id="a18" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
    <line x1="330" y1="105" x2="440" y2="55" stroke="#f0883e" marker-end="url(#a19)"/>
    <defs><marker id="a19" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker></defs>
  </g>
</svg>

Point the new node forward first (step 1), then relink the predecessor to it (step 2) — this order preserves the connection to the rest of the list.

## 5. Runnable example

```java
// InsertHeadTailMiddle.java
public class InsertHeadTailMiddle {

    static class Node {
        int value;
        Node next;
        Node(int value) { this.value = value; }
    }

    static class LinkedList {
        Node head, tail;

        void insertAtHead(int value) { // O(1)
            Node node = new Node(value);
            node.next = head;
            head = node;
            if (tail == null) tail = node; // list was empty: new node is also the tail
        }

        void insertAtTail(int value) { // O(1), because tail is maintained
            Node node = new Node(value);
            if (tail == null) { head = tail = node; return; }
            tail.next = node;
            tail = node;
        }

        void insertAfter(Node prevNode, int value) { // O(1) given prevNode; O(n) to FIND prevNode
            Node node = new Node(value);
            node.next = prevNode.next; // step 1: link forward first
            prevNode.next = node;      // step 2: relink the predecessor
            if (prevNode == tail) tail = node;
        }

        void printAll() {
            StringBuilder sb = new StringBuilder();
            for (Node c = head; c != null; c = c.next) sb.append(c.value).append(" -> ");
            System.out.println(sb + "null");
        }
    }

    // Basic: head insertion, O(1).
    static void basicLevel() {
        LinkedList list = new LinkedList();
        list.insertAtHead(30);
        list.insertAtHead(20);
        list.insertAtHead(10);
        System.out.print("basic (head inserts): ");
        list.printAll(); // 10 -> 20 -> 30 -> null
    }

    // Intermediate: tail insertion, O(1) because tail is tracked.
    static void intermediateLevel() {
        LinkedList list = new LinkedList();
        list.insertAtTail(10);
        list.insertAtTail(20);
        list.insertAtTail(30);
        System.out.print("intermediate (tail inserts): ");
        list.printAll(); // 10 -> 20 -> 30 -> null
    }

    // Advanced: middle insertion -- O(n) to find the spot, O(1) to relink once found.
    static void advancedLevel() {
        LinkedList list = new LinkedList();
        list.insertAtTail(10);
        list.insertAtTail(30);
        // find the node before the insertion point (O(n) search)
        Node current = list.head;
        while (current != null && current.value != 10) current = current.next;
        list.insertAfter(current, 20); // O(1) relink, given the found node
        System.out.print("advanced (middle insert): ");
        list.printAll(); // 10 -> 20 -> 30 -> null
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `InsertHeadTailMiddle.java`, then run `java InsertHeadTailMiddle.java`.

## 6. Walkthrough

1. `basicLevel()` inserts `30`, then `20`, then `10`, each at the head — every insertion just redirects `head` and the new node's `next`, giving the final order `10 -> 20 -> 30 -> null` (reverse of insertion order), with no traversal needed for any of the three inserts.
2. `intermediateLevel()` inserts `10`, `20`, `30` at the tail. Because `tail` is maintained after every insertion, each `insertAtTail` call is O(1) — it never has to search from `head` to find the current last node.
3. `advancedLevel()` first performs an explicit O(n) search (`while (current.value != 10)`) to find the node just before where `20` should go, then calls `insertAfter(current, 20)`, which does the actual relinking in O(1): `node.next = prevNode.next` (pointing the new node at `30`) happens before `prevNode.next = node` (pointing `10` at the new node), preserving the connection to `30`.
4. The final list correctly reads `10 -> 20 -> 30 -> null` — the O(n) cost of this "middle insert" came entirely from the search step, not from the relinking itself.

## 7. Gotchas & takeaways

> Gotcha: setting `prevNode.next = node` *before* `node.next = prevNode.next` loses the reference to everything after `prevNode` — by the time you read `prevNode.next` for the new node's `next`, it has already been overwritten to point at the new node itself, silently truncating the rest of the list.

- Head insertion is always O(1); tail insertion is O(1) only if a `tail` reference is actively maintained.
- Middle insertion is O(1) to relink once you have the predecessor node, but reaching that predecessor from `head` costs O(n).
- Always link the new node forward first, then relink its predecessor — reversing this order breaks the chain.
- Related concepts: [Sentinel / dummy nodes](0048-sentinel-dummy-nodes.md), [Delete by node & by value](0050-delete-by-node-by-value.md).
