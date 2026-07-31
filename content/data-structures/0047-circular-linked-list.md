---
card: data-structures
gi: 47
slug: circular-linked-list
title: Circular linked list
---

## 1. What it is

A **circular linked list** is a linked list where the last node's `next` points back to the **first** node instead of to `null` — there is no true "end." Starting from any node and following `next` repeatedly eventually cycles back to where you started, forever. It can be built on either a singly linked structure (one circular direction) or a doubly linked one (circular in both directions).

## 2. Why & when

Use a circular linked list when your data is naturally cyclic — a round-robin scheduler cycling through tasks, a multiplayer game cycling through players' turns, or a fixed-size circular buffer. The defining benefit is that "the next item after the last" is a normal, well-defined operation (it just wraps to the first), with no special-case check needed.

## 3. Core concept

**No `null` terminator — traversal needs an explicit stopping condition.** A normal linked-list loop (`while (current != null)`) would loop forever on a circular list. Traversal must instead track a stopping point deliberately — commonly, loop while `current != head` (checked *after* the first step), or keep a count of nodes to visit.

**Insertion still relinks a `next` pointer, but "the end" wraps to the front.** Appending a new node means finding the current last node (the one whose `next` currently points to `head`), pointing the new node's `next` at `head`, then updating the old last node's `next` to point at the new node instead.

**Circularity is a real structural cycle, not a bug.** This is the one linked-list variant where a "cycle" is the intended design, not the error [Cycle Detection (Floyd's tortoise & hare)](0053-cycle-detection-floyd-s-tortoise-hare.md) is built to catch — the distinction is entirely about intent: is looping back to the start expected, or a corruption to detect?

**Round-robin advancing.** Given a reference to "the current node," advancing to the next turn is just `current = current.next` — because of the circular structure, this naturally wraps from the last participant back to the first with no special-case branch needed.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A circular linked list of three nodes arranged in a ring, the last node's next pointing back to the first">
  <g font-family="sans-serif" font-size="11">
    <rect x="270" y="20" width="90" height="40" fill="#161b22" stroke="#3fb950"/><text x="295" y="45" fill="#e6edf3" font-size="11">A</text>
    <rect x="450" y="90" width="90" height="40" fill="#161b22" stroke="#3fb950"/><text x="475" y="115" fill="#e6edf3" font-size="11">B</text>
    <rect x="90" y="90" width="90" height="40" fill="#161b22" stroke="#3fb950"/><text x="115" y="115" fill="#e6edf3" font-size="11">C</text>

    <line x1="355" y1="45" x2="460" y2="95" stroke="#79c0ff" marker-end="url(#a15)"/>
    <line x1="450" y1="110" x2="185" y2="110" stroke="#79c0ff" marker-end="url(#a15)"/>
    <line x1="105" y1="95" x2="280" y2="50" stroke="#79c0ff" marker-end="url(#a15)"/>
    <defs><marker id="a15" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
    <text x="320" y="170" fill="#79c0ff" text-anchor="middle">C's next points back to A -- no node's next is ever null</text>
  </g>
</svg>

Following `next` from any node eventually returns to the start — there is no `null`-terminated end.

## 5. Runnable example

```java
// CircularLinkedList.java
public class CircularLinkedList {

    static class Node {
        int value;
        Node next;
        Node(int value) { this.value = value; }
    }

    static class CircularList {
        Node last; // points to the LAST node; last.next is always the head

        void add(int value) {
            Node node = new Node(value);
            if (last == null) {
                last = node;
                last.next = last; // a single node points to itself
            } else {
                node.next = last.next; // new node points to the current head
                last.next = node;      // old last points to the new node
                last = node;           // new node becomes the last
            }
        }

        // Basic: traversal must stop explicitly -- there is no null to rely on.
        void printOnceAround() {
            if (last == null) { System.out.println("(empty)"); return; }
            Node head = last.next;
            Node current = head;
            StringBuilder sb = new StringBuilder();
            do {
                sb.append(current.value).append(" -> ");
                current = current.next;
            } while (current != head); // stop after one full loop back to head
            sb.append("(back to ").append(head.value).append(")");
            System.out.println(sb);
        }
    }

    static void basicLevel() {
        CircularList list = new CircularList();
        list.add(10);
        list.add(20);
        list.add(30);
        System.out.print("basic: ");
        list.printOnceAround();
    }

    // Intermediate: round-robin advancing -- "next turn" naturally wraps with no special case.
    static void intermediateLevel() {
        CircularList list = new CircularList();
        list.add(1); list.add(2); list.add(3);
        Node currentTurn = list.last.next; // start at the head
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 7; i++) { // walk past the end multiple times -- 7 turns over 3 players
            sb.append(currentTurn.value).append(" ");
            currentTurn = currentTurn.next; // wraps automatically from player 3 back to player 1
        }
        System.out.println("intermediate: 7 turns over 3 players -> " + sb.toString().trim());
    }

    // Advanced: confirm the structural cycle exists -- following next enough times returns to the start.
    static void advancedLevel() {
        CircularList list = new CircularList();
        list.add(100); list.add(200); list.add(300);
        Node start = list.last.next;
        Node current = start;
        int steps = 0;
        do {
            current = current.next;
            steps++;
        } while (current != start);
        System.out.println("advanced: steps to return to start (list size) -> " + steps);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `CircularLinkedList.java`, then run `java CircularLinkedList.java`.

## 6. Walkthrough

1. `basicLevel()` adds `10`, `20`, `30`. Each `add` relinks `last.next` to point at the new node and updates `last` — the final node (`30`) always has its `next` pointing back to the head (`10`).
2. `printOnceAround()` uses a `do-while` loop, checking the stop condition (`current != head`) *after* advancing — this correctly visits every node exactly once before recognizing it has looped back to `head`, printing `10 -> 20 -> 30 -> (back to 10)`.
3. `intermediateLevel()` simulates 7 turns across only 3 players by repeatedly setting `currentTurn = currentTurn.next`. Because the list is circular, the 4th "turn" naturally wraps back to player 1 with no `if (currentTurn == null)` check needed — the sequence prints `1 2 3 1 2 3 1`.
4. `advancedLevel()` counts how many `next` steps it takes to return to the exact starting node, confirming it equals the list's size (3) — direct proof that the structure really does form a closed loop, not a chain that happens to terminate.

## 7. Gotchas & takeaways

> Gotcha: reusing a standard `while (current != null)` traversal loop on a circular list causes an infinite loop, since no node's `next` is ever `null` — always use an explicit stopping condition, like checking `current != head` after each step (a `do-while`), or tracking a visit count.

- A circular linked list's last node points back to the first, instead of to `null` — there is no natural end.
- Traversal needs an explicit stop condition (checked after advancing), since the usual `null`-check pattern would loop forever.
- Useful whenever data is naturally cyclic, like round-robin scheduling, since "next after the last" is automatically well-defined.
- Related concepts: [Singly linked list](0045-singly-linked-list.md), [Cycle detection (Floyd's tortoise & hare)](0053-cycle-detection-floyd-s-tortoise-hare.md) (detecting an *unintended* cycle).
