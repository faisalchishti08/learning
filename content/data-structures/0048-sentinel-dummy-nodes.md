---
card: data-structures
gi: 48
slug: sentinel-dummy-nodes
title: Sentinel / dummy nodes
---

## 1. What it is

A **sentinel** (or **dummy**) **node** is an extra, "fake" node placed at the front (and sometimes the back) of a linked list, holding no real data. Its only job is to remove special-case code: instead of writing separate logic for "the list is empty" or "we are inserting/deleting at the head," every operation can treat the sentinel's position as just another node with a `next` — the special cases disappear.

## 2. Why & when

Reach for a sentinel whenever you notice your linked-list code has an `if (head == null)` branch duplicated across several methods, or a separate "insert before head" case distinct from "insert in the middle." A sentinel unifies these into one code path, which is shorter and much less bug-prone — most real head-insertion/deletion bugs come from forgetting to handle the empty-list or head-specific case.

## 3. Core concept

**Without a sentinel, the head is special.** Deleting the first real node means reassigning the `head` reference itself, a different operation from deleting any other node (which just relinks the *previous* node's `next`) — this asymmetry is exactly what forces extra `if` branches.

**With a sentinel, every real node has a predecessor.** The sentinel sits before the first real node, so "delete the first real node" becomes "relink the sentinel's `next`" — the exact same operation used to delete any other node. There is no longer a special case for the head at all.

**The sentinel is never part of the logical data.** When traversing, printing, or returning results, you start from `sentinel.next`, skipping the sentinel itself — it exists purely as scaffolding for the algorithm's uniformity, not as a value in the list.

**Common pattern: `ListNode dummy = new ListNode(0); dummy.next = head;` then work from `dummy`, return `dummy.next`.** This one-line setup at the start of a method, and `dummy.next` at the end, is a widely used idiom in linked-list problems (merging lists, removing nodes matching a condition, reversing a range) precisely because it eliminates head-specific special-casing.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A dummy node placed before the real head, so every real node including the first has a uniform predecessor">
  <g font-family="sans-serif" font-size="11">
    <rect x="40" y="50" width="80" height="40" fill="none" stroke="#8b949e" stroke-dasharray="3,3"/><text x="80" y="75" fill="#8b949e" text-anchor="middle" font-size="10">dummy</text>
    <line x1="120" y1="70" x2="180" y2="70" stroke="#79c0ff" marker-end="url(#a16)"/>
    <defs><marker id="a16" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>

    <rect x="180" y="50" width="80" height="40" fill="#161b22" stroke="#3fb950"/><text x="220" y="75" fill="#e6edf3" text-anchor="middle" font-size="10">10 (real head)</text>
    <line x1="260" y1="70" x2="320" y2="70" stroke="#79c0ff" marker-end="url(#a16)"/>

    <rect x="320" y="50" width="80" height="40" fill="#161b22" stroke="#3fb950"/><text x="360" y="75" fill="#e6edf3" text-anchor="middle" font-size="10">20</text>
    <line x1="400" y1="70" x2="450" y2="70" stroke="#8b949e" marker-end="url(#a17)"/>
    <defs><marker id="a17" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
    <text x="470" y="75" fill="#8b949e">null</text>

    <text x="320" y="140" fill="#79c0ff" text-anchor="middle">deleting "10" is now identical to deleting any other node -- relink dummy.next</text>
  </g>
</svg>

The dummy node gives even the first real node a predecessor, making head operations identical to every other node's operations.

## 5. Runnable example

```java
// SentinelDummyNodes.java
public class SentinelDummyNodes {

    static class Node {
        int value;
        Node next;
        Node(int value) { this.value = value; }
    }

    // Basic: removing nodes with a given value WITHOUT a dummy -- head deletion needs its own special case.
    static Node removeValueNoSentinel(Node head, int target) {
        while (head != null && head.value == target) head = head.next; // special case: target(s) at the head
        Node current = head;
        while (current != null && current.next != null) {
            if (current.next.value == target) current.next = current.next.next;
            else current = current.next;
        }
        return head;
    }

    static void basicLevel() {
        Node head = new Node(5);
        head.next = new Node(5);
        head.next.next = new Node(3);
        head.next.next.next = new Node(5);
        head = removeValueNoSentinel(head, 5);
        printList("basic (no sentinel)", head);
    }

    // Intermediate: the same removal WITH a dummy node -- no special case for the head at all.
    static Node removeValueWithSentinel(Node head, int target) {
        Node dummy = new Node(0);
        dummy.next = head;
        Node current = dummy; // dummy is a uniform predecessor for every real node, including the old head
        while (current.next != null) {
            if (current.next.value == target) current.next = current.next.next;
            else current = current.next;
        }
        return dummy.next; // skip the dummy itself when returning the real list
    }

    static void intermediateLevel() {
        Node head = new Node(5);
        head.next = new Node(5);
        head.next.next = new Node(3);
        head.next.next.next = new Node(5);
        head = removeValueWithSentinel(head, 5);
        printList("intermediate (with sentinel)", head);
    }

    // Advanced: merging two sorted lists, using a dummy to avoid special-casing "which list starts first".
    static Node mergeSorted(Node a, Node b) {
        Node dummy = new Node(0);
        Node tail = dummy;
        while (a != null && b != null) {
            if (a.value <= b.value) { tail.next = a; a = a.next; }
            else { tail.next = b; b = b.next; }
            tail = tail.next;
        }
        tail.next = (a != null) ? a : b; // attach whichever list has leftover nodes
        return dummy.next;
    }

    static void advancedLevel() {
        Node a = new Node(1); a.next = new Node(3); a.next.next = new Node(5);
        Node b = new Node(2); b.next = new Node(4); b.next.next = new Node(6);
        Node merged = mergeSorted(a, b);
        printList("advanced (merged)", merged);
    }

    static void printList(String label, Node head) {
        StringBuilder sb = new StringBuilder();
        for (Node c = head; c != null; c = c.next) sb.append(c.value).append(" -> ");
        System.out.println(label + " -> " + sb + "null");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `SentinelDummyNodes.java`, then run `java SentinelDummyNodes.java`.

## 6. Walkthrough

1. `basicLevel()`'s `removeValueNoSentinel` must handle two distinct cases: first, a `while` loop specifically skipping past matching values *at the head* (advancing `head` itself), then a *separate* loop relinking `current.next` for matches elsewhere — two different code paths for what is logically the same operation.
2. `intermediateLevel()`'s `removeValueWithSentinel` introduces `dummy`, whose `next` starts pointing at the real head. The single loop that follows relinks `current.next` uniformly — when it happens to remove the old head, that is just `dummy.next` being relinked, exactly like removing any other node.
3. Both approaches correctly reduce `5 -> 5 -> 3 -> 5` down to `3 -> null`, but the sentinel version needed only one loop, not two.
4. `advancedLevel()`'s `mergeSorted` uses `dummy` to avoid asking "which list's first node becomes the merged head?" as a special case — `tail` starts at `dummy`, and the very first real node attached (whichever list has the smaller starting value) becomes `dummy.next` automatically, exactly like every other attached node.

## 7. Gotchas & takeaways

> Gotcha: forgetting to return `dummy.next` (returning `dummy` itself instead) leaves a spurious extra node with fake, unused data at the front of the result — always skip past the sentinel when handing the final list back to the caller.

- A sentinel/dummy node gives every real node (including the original head) a uniform predecessor, removing head-specific special-case code.
- The idiom is: create `dummy`, point `dummy.next` at the real head, operate using `dummy` as the starting predecessor, then return `dummy.next`.
- This pattern is especially valuable for deletion and merging operations, where "the head changes" would otherwise require separate logic.
- Related concepts: [Insert at head / tail / middle](0049-insert-at-head-tail-middle.md), [Merge two sorted linked lists](0055-merge-two-sorted-linked-lists.md).
