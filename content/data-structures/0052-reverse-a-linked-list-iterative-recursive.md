---
card: data-structures
gi: 52
slug: reverse-a-linked-list-iterative-recursive
title: Reverse a linked list (iterative & recursive)
---

## 1. What it is

Reversing a linked list means flipping every node's `next` reference to point at its *previous* node instead of its successor, so the old tail becomes the new head and vice versa — all done in place, without allocating a new list. It can be done iteratively, walking forward while flipping pointers as you go, or recursively, using the call stack to hold the "rest of the list" while reversing on the way back up.

## 2. Why & when

Reversal is one of the most common linked-list interview questions precisely because it forces careful, correct pointer manipulation with no room for the "just index differently" shortcuts that work on arrays. It also appears as a sub-step in other problems, like checking if a list is a palindrome, or reversing only a sub-range of a longer list.

## 3. Core concept

**Iterative reversal: track three pointers as you walk forward.** `prev` (initially `null`), `current` (initially `head`), and a temporary `next` to remember `current.next` before overwriting it. At each step: save `next = current.next`, flip `current.next = prev`, then advance both `prev = current` and `current = next`. After the loop, `prev` is the new head.

**Why the temporary `next` variable is required.** The moment you execute `current.next = prev`, you have overwritten `current`'s original forward link — without saving it first, you would lose the ability to move on to the rest of the original list. This save-before-overwrite step is the crux of the whole algorithm.

**Recursive reversal: reverse the rest first, then fix the local link.** `reverse(node)` recursively reverses everything after `node`, getting back the new head of that reversed sub-list. Then it fixes up the local connection: `node.next.next = node` (make the node that used to follow `node` now point back at `node`), and `node.next = null` (since `node` is now the new tail of its sub-list).

**Both are O(n) time; they differ in space.** Iterative reversal uses O(1) extra space (just the three pointer variables). Recursive reversal uses O(n) call-stack space, one frame per node, due to the recursion depth — the same stack-depth cost noted for any deep recursive linked-list traversal.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Iteratively reversing a linked list by flipping each node's next to point backward while walking forward with prev, current, and next pointers">
  <g font-family="sans-serif" font-size="11">
    <text x="320" y="16" fill="#8b949e" text-anchor="middle">before: 1 -&gt; 2 -&gt; 3 -&gt; null</text>
    <rect x="60" y="30" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="90" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <rect x="150" y="30" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="180" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <rect x="240" y="30" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="270" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">3</text>
    <line x1="120" y1="45" x2="145" y2="45" stroke="#79c0ff" marker-end="url(#a20)"/>
    <line x1="210" y1="45" x2="235" y2="45" stroke="#79c0ff" marker-end="url(#a20)"/>
    <defs><marker id="a20" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>

    <text x="320" y="105" fill="#8b949e" text-anchor="middle">after: null &lt;- 1 &lt;- 2 &lt;- 3 (head is now 3)</text>
    <rect x="60" y="120" width="60" height="30" fill="#161b22" stroke="#f0883e"/><text x="90" y="140" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <rect x="150" y="120" width="60" height="30" fill="#161b22" stroke="#f0883e"/><text x="180" y="140" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <rect x="240" y="120" width="60" height="30" fill="#161b22" stroke="#f0883e"/><text x="270" y="140" fill="#e6edf3" text-anchor="middle" font-size="10">3</text>
    <line x1="150" y1="135" x2="125" y2="135" stroke="#f0883e" marker-end="url(#a21)"/>
    <line x1="240" y1="135" x2="215" y2="135" stroke="#f0883e" marker-end="url(#a21)"/>
    <defs><marker id="a21" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker></defs>
  </g>
</svg>

Every `next` link flips direction. The last original node (`3`) becomes the new head; the first original node (`1`) becomes the new tail.

## 5. Runnable example

```java
// ReverseLinkedList.java
public class ReverseLinkedList {

    static class Node {
        int value;
        Node next;
        Node(int value) { this.value = value; }
    }

    // Basic: iterative reversal using prev/current/next pointers.
    static Node reverseIterative(Node head) {
        Node prev = null, current = head;
        while (current != null) {
            Node next = current.next; // save before overwriting
            current.next = prev;      // flip the link backward
            prev = current;           // advance prev
            current = next;           // advance current
        }
        return prev; // prev is the new head once current runs off the end
    }

    static void basicLevel() {
        Node head = buildList(1, 2, 3, 4, 5);
        Node reversed = reverseIterative(head);
        printList("basic (iterative)", reversed);
    }

    // Intermediate: recursive reversal -- reverse the rest, then fix the local link.
    static Node reverseRecursive(Node node) {
        if (node == null || node.next == null) return node; // base case: 0 or 1 node is already "reversed"
        Node newHead = reverseRecursive(node.next); // reverse everything after node
        node.next.next = node; // the node after 'node' should now point back at 'node'
        node.next = null;      // 'node' becomes the new tail of its (sub-)list
        return newHead;
    }

    static void intermediateLevel() {
        Node head = buildList(1, 2, 3, 4, 5);
        Node reversed = reverseRecursive(head);
        printList("intermediate (recursive)", reversed);
    }

    // Advanced: reverse only a sub-range [left, right] (1-indexed), leaving the rest of the list intact.
    static Node reverseRange(Node head, int left, int right) {
        Node dummy = new Node(0);
        dummy.next = head;
        Node beforeRange = dummy;
        for (int i = 1; i < left; i++) beforeRange = beforeRange.next; // walk to just before the range

        Node rangeStart = beforeRange.next;
        Node prev = null, current = rangeStart;
        for (int i = 0; i <= right - left; i++) { // reverse exactly (right - left + 1) nodes
            Node next = current.next;
            current.next = prev;
            prev = current;
            current = next;
        }
        beforeRange.next = prev;   // connect the part before the range to the new range head
        rangeStart.next = current; // connect the (now-tail) old range start to the part after the range
        return dummy.next;
    }

    static void advancedLevel() {
        Node head = buildList(1, 2, 3, 4, 5);
        Node result = reverseRange(head, 2, 4); // reverse just the middle: 2,3,4 -> 4,3,2
        printList("advanced (reverse range [2,4])", result);
    }

    static Node buildList(int... values) {
        Node dummy = new Node(0), tail = dummy;
        for (int v : values) { tail.next = new Node(v); tail = tail.next; }
        return dummy.next;
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

**How to run:** save as `ReverseLinkedList.java`, then run `java ReverseLinkedList.java`.

## 6. Walkthrough

1. `basicLevel()`'s `reverseIterative` starts with `prev=null, current=1`. Step 1: save `next=2`, set `1.next=null`, advance `prev=1, current=2`. Step 2: save `next=3`, set `2.next=1`, advance `prev=2, current=3` — this repeats until `current` becomes `null`, leaving `prev` at the old tail (`5`), now the new head.
2. The final result reads `5 -> 4 -> 3 -> 2 -> 1 -> null`, confirming every link was flipped.
3. `intermediateLevel()`'s `reverseRecursive` recurses all the way to the last node (`5`), which becomes `newHead`. Unwinding back up: at node `4`, `node.next.next = node` makes `5.next` point back at `4`, and `4.next = null` makes `4` the new tail of that sub-list — this repeats at each level, producing the same fully reversed list.
4. `advancedLevel()`'s `reverseRange` first walks to the node just before position `2` (`beforeRange = 1`), then reverses exactly 3 nodes (`2,3,4`) using the same prev/current/next iterative technique, and finally reconnects: `beforeRange.next` points at the new local head (`4`), and `rangeStart` (`2`, now the tail of the reversed sub-range) points at whatever came after the range (`5`) — giving `1 -> 4 -> 3 -> 2 -> 5 -> null`.

## 7. Gotchas & takeaways

> Gotcha: forgetting to save `current.next` into a temporary variable *before* overwriting `current.next = prev` permanently loses access to the rest of the original list — the reversal silently truncates after the first node, with no exception to signal the bug.

- Iterative reversal flips each node's `next` while walking forward, using three pointers (`prev`, `current`, a temporary `next`) and O(1) extra space.
- Recursive reversal reverses the rest of the list first, then fixes the local link on the way back up the call stack, using O(n) stack space.
- Reversing only a sub-range combines the same technique with careful reconnection to the parts of the list before and after the range.
- Related concepts: [Traversal of a linked list](0051-traversal-of-a-linked-list.md), [Sentinel / dummy nodes](0048-sentinel-dummy-nodes.md).
