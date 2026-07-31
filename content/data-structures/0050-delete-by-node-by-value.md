---
card: data-structures
gi: 50
slug: delete-by-node-by-value
title: Delete by node & by value
---

## 1. What it is

Deleting from a linked list means relinking a `next` reference to skip over (and effectively remove) a node. **Delete by value** searches for the first node matching a given value, then removes it. **Delete by node** assumes you already have a direct reference to the target node — a subtly different (and, for a singly linked list, surprisingly trickier) problem.

## 2. Why & when

Delete-by-value is the everyday case: "remove the first `7` from this list." Delete-by-node matters in problems where you are handed a node reference directly (common in interview-style questions) without access to `head` — this forces a different technique, since you cannot simply search from the front.

## 3. Core concept

**Delete by value: find the predecessor, then relink.** To delete the node holding a target value, you need a reference to the node *before* it, so you can set `predecessor.next = target.next`. This means walking from `head`, always keeping one step behind the node you are examining — an O(n) search in the worst case, even though the relinking itself is O(1).

**Delete by node (singly linked, no predecessor access): copy-and-skip.** If you only have a reference to the node to delete (not its predecessor, and not `head`), you cannot relink the predecessor directly. The trick: copy the *next* node's value into the current node, then delete the next node instead (`node.value = node.next.value; node.next = node.next.next;`). The node the caller "wanted deleted" now effectively holds what used to be its successor's value, and the true successor is unlinked — functionally equivalent to deleting the original node.

**Why the copy-and-skip trick has a hard limitation.** It cannot delete the *last* node this way, since there is no `next` node to copy from — deleting the true last node still requires a predecessor reference, found the normal way.

**Deleting the head is a special case without a sentinel.** If the target is the first node, `head` itself must be reassigned to `head.next` — this is exactly the asymmetry a [Sentinel / dummy node](0048-sentinel-dummy-nodes.md) is designed to eliminate.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Deleting a node by value via predecessor relinking, versus deleting by node reference via the copy-and-skip trick" >
  <g font-family="sans-serif" font-size="11">
    <text x="160" y="16" fill="#8b949e" text-anchor="middle">delete by value: relink predecessor</text>
    <rect x="60" y="30" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="90" y="50" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <rect x="140" y="30" width="60" height="30" fill="#21262d" stroke="#f85149"/><text x="170" y="50" fill="#e6edf3" text-anchor="middle" font-size="9">20 x</text>
    <rect x="220" y="30" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="250" y="50" fill="#e6edf3" text-anchor="middle" font-size="9">30</text>
    <line x1="90" y1="65" x2="250" y2="65" stroke="#79c0ff" stroke-dasharray="3,3"/>
    <text x="160" y="85" fill="#79c0ff" text-anchor="middle" font-size="9">10.next = 30 (skip 20)</text>

    <text x="480" y="16" fill="#8b949e" text-anchor="middle">delete by node: copy next's value in, skip next</text>
    <rect x="420" y="30" width="60" height="30" fill="#0d1117" stroke="#f0883e"/><text x="450" y="50" fill="#e6edf3" text-anchor="middle" font-size="9">20-&gt;30</text>
    <rect x="500" y="30" width="60" height="30" fill="#21262d" stroke="#f85149"/><text x="530" y="50" fill="#e6edf3" text-anchor="middle" font-size="9">30 x</text>
    <rect x="580" y="30" width="40" height="30" fill="#161b22" stroke="#3fb950"/><text x="600" y="50" fill="#e6edf3" text-anchor="middle" font-size="9">40</text>
    <text x="480" y="85" fill="#79c0ff" text-anchor="middle" font-size="9">the "20" node now holds 30's value; the real 30 node is unlinked</text>
  </g>
</svg>

Delete-by-value relinks the predecessor found via search. Delete-by-node (no predecessor available) instead copies the successor's data forward and removes the successor.

## 5. Runnable example

```java
// DeleteByNodeByValue.java
public class DeleteByNodeByValue {

    static class Node {
        int value;
        Node next;
        Node(int value) { this.value = value; }
    }

    // Basic: delete by value -- search for the predecessor, then relink.
    static Node deleteByValue(Node head, int target) {
        if (head == null) return null;
        if (head.value == target) return head.next; // special case: target is the head itself

        Node prev = head;
        while (prev.next != null && prev.next.value != target) prev = prev.next;
        if (prev.next != null) prev.next = prev.next.next; // relink around the target
        return head;
    }

    static void basicLevel() {
        Node head = new Node(10);
        head.next = new Node(20);
        head.next.next = new Node(30);
        head = deleteByValue(head, 20);
        printList("basic", head); // 10 -> 30 -> null
    }

    // Intermediate: delete by node reference -- copy-and-skip trick, no predecessor or head needed.
    static void deleteNodeReference(Node node) {
        if (node == null || node.next == null) {
            throw new IllegalArgumentException("cannot delete the last node this way");
        }
        node.value = node.next.value; // copy the successor's data into this node
        node.next = node.next.next;   // unlink the (now-duplicate) successor
    }

    static void intermediateLevel() {
        Node head = new Node(10);
        head.next = new Node(20);
        head.next.next = new Node(30);
        Node target = head.next; // a direct reference to the "20" node, no access to head needed
        deleteNodeReference(target);
        printList("intermediate", head); // 10 -> 30 -> null
    }

    // Advanced: deleting the head, and confirming the copy-and-skip trick cannot delete the true last node.
    static void advancedLevel() {
        Node head = new Node(10);
        head.next = new Node(20);
        head = deleteByValue(head, 10); // deleting the head itself
        printList("advanced (head deleted)", head); // 20 -> null

        Node lastNode = head; // "20", which is now the only (and last) node
        try {
            deleteNodeReference(lastNode);
        } catch (IllegalArgumentException e) {
            System.out.println("advanced: caught -> " + e.getMessage());
        }
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

**How to run:** save as `DeleteByNodeByValue.java`, then run `java DeleteByNodeByValue.java`.

## 6. Walkthrough

1. `basicLevel()`'s `deleteByValue(head, 20)` walks `prev` from `head` until `prev.next.value == 20`, then sets `prev.next = prev.next.next`, skipping the `20` node entirely — the result is `10 -> 30 -> null`.
2. `intermediateLevel()` holds `target`, a direct reference to the `20` node, with no access to `head` or any predecessor. `deleteNodeReference(target)` copies `30` (the successor's value) into `target`, then sets `target.next` to skip past the now-redundant original `30` node — from the outside, the list still reads `10 -> 30 -> null`, exactly as if `20` had been truly deleted.
3. `advancedLevel()` first deletes the head (`10`) using `deleteByValue`'s special-case branch, leaving just `20 -> null`.
4. Attempting `deleteNodeReference` on this remaining single node throws `IllegalArgumentException`, since it has no `next` to copy from — the copy-and-skip trick fundamentally cannot remove the true last node of a singly linked list without a predecessor reference.

## 7. Gotchas & takeaways

> Gotcha: the copy-and-skip "delete by node" trick silently fails (or must explicitly be forbidden, as shown here) on the last node of a list — always confirm the target node has a `next` before applying this trick, and fall back to predecessor-based deletion (which needs `head`) for the last node.

- Deleting by value requires finding the predecessor via an O(n) search from `head`, then an O(1) relink.
- Deleting by a direct node reference (no predecessor available) uses the copy-and-skip trick, but only works if the node has a successor.
- Deleting the head itself is a special case without a [sentinel node](0048-sentinel-dummy-nodes.md) — it needs a separate branch to reassign `head`.
- Related concepts: [Sentinel / dummy nodes](0048-sentinel-dummy-nodes.md), [Insert at head / tail / middle](0049-insert-at-head-tail-middle.md).
