---
card: leetcode-patterns
gi: 481
slug: remove-nodes-from-linked-list
title: Remove Nodes From Linked List
---

## 1. What it is

Given the head of a singly linked list, remove every node that has a node with a **strictly greater** value somewhere to its right. Return the head of the modified list. Example: `1 -> 2 -> 3` in reverse thinking; concretely `5 -> 2 -> 13 -> 3 -> 8` → `13 -> 8` (`5`, `2`, and `3` all have a bigger value later in the list).

## 2. Why & when

"Remove a node if a bigger one exists later" is precisely the next-greater-element signal from the [monotonic-stack signal](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md) family, applied to a linked list instead of an array. Constraints: up to 100,000 nodes.

## 3. Core concept

**Key idea:** convert the problem to "keep only the nodes that have no bigger node to their right," which is the same as "keep only nodes that are part of a suffix that is non-increasing when read from the end." Scan the list and use a decreasing monotonic stack of node values: any node smaller than a later node gets popped (discarded) since that later, bigger node proves it should be removed.

**Steps:**
1. Walk the linked list, pushing each node's value onto a stack, but before pushing, pop every value on the stack that is smaller than the current node's value (those nodes have a bigger node to their right — the current one — so they must be removed).
2. After processing every node, the stack holds exactly the values that survive, in the correct final order from head to tail (bottom of the stack first).
3. Rebuild a new linked list from the stack's contents, or (more simply, in Java) collect the stack into a list-like structure and relink nodes.

**Why a decreasing stack captures the answer directly:** a node survives if and only if no node after it is bigger. Scanning left to right and popping every previous value that is smaller than the current one is exactly a "next greater element" resolution — every popped node has just found the bigger node that disqualifies it.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Decreasing stack of linked-list values, popping any node that finds a bigger node later">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">list: 5 -&gt; 2 -&gt; 13 -&gt; 3 -&gt; 8</text>
    <text x="20" y="45" fill="#8b949e">5: push. stack=[5]</text>
    <text x="20" y="65" fill="#8b949e">2: 5 not &lt; 2, push. stack=[5, 2]</text>
    <text x="20" y="85" fill="#8b949e">13: pop 2 (2&lt;13); pop 5 (5&lt;13). push 13. stack=[13]</text>
    <text x="20" y="105" fill="#8b949e">3: 13 not &lt; 3, push. stack=[13, 3]</text>
    <text x="20" y="130" fill="#f0883e">8: pop 3 (3&lt;8); 13 not &lt; 8, stop. push 8. stack=[13, 8]</text>
    <text x="20" y="155" fill="#3fb950">final list, bottom to top of stack: 13 -&gt; 8</text>
  </g>
</svg>

Any value smaller than a later value is popped and discarded, exactly like resolving "next greater element."

## 5. Runnable example

**Level 1 — Brute force.** For each node, scan the rest of the list for any bigger value; remove the node if found. O(n²).

**KEY INSIGHT:** "has a bigger node later" is answered for every node in one pass by a decreasing monotonic stack — a node is removed the instant a bigger node arrives, exactly like resolving next-greater-element queries.

**Level 2 — Optimal.** Single-pass decreasing stack of node values, O(n).

**Level 3 — Hardened.** Handles a strictly decreasing list (nothing removed), and a single-node list.

```java
// RemoveNodesFromLinkedList.java
import java.util.*;

public class RemoveNodesFromLinkedList {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 2 & 3: decreasing monotonic stack of node values, O(n)
    static ListNode removeNodes(ListNode head) {
        Deque<ListNode> stack = new ArrayDeque<>();
        ListNode current = head;

        while (current != null) {
            while (!stack.isEmpty() && stack.peek().val < current.val) {
                stack.pop(); // a bigger node just showed up: discard the smaller one
            }
            stack.push(current);
            current = current.next;
        }

        // stack now holds surviving nodes, top = last node processed (tail).
        // Relink from tail back to head using the stack's pop order.
        ListNode newHead = null;
        while (!stack.isEmpty()) {
            ListNode node = stack.pop();
            node.next = newHead;
            newHead = node;
        }
        return newHead;
    }

    static ListNode build(int... values) {
        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;
        for (int v : values) { tail.next = new ListNode(v); tail = tail.next; }
        return dummy.next;
    }

    static String toStr(ListNode head) {
        StringBuilder sb = new StringBuilder();
        while (head != null) { sb.append(head.val); if (head.next != null) sb.append(" -> "); head = head.next; }
        return sb.toString();
    }

    public static void main(String[] args) {
        System.out.println(toStr(removeNodes(build(5, 2, 13, 3, 8))));  // 13 -> 8
        System.out.println(toStr(removeNodes(build(5, 4, 3, 2, 1))));   // 5 -> 4 -> 3 -> 2 -> 1 (nothing removed)
        System.out.println(toStr(removeNodes(build(1, 1, 1))));         // 1 -> 1 -> 1 (equal values never removed)
    }
}
```

**How to run:** save as `RemoveNodesFromLinkedList.java`, then run `java RemoveNodesFromLinkedList.java`.

## 6. Walkthrough

Trace the scan phase on `5 -> 2 -> 13 -> 3 -> 8`:

| node value | stack before | pops | stack after |
|---|---|---|---|
| 5 | [] | none | [5] |
| 2 | [5] | none (5 not < 2) | [5, 2] |
| 13 | [5, 2] | pop 2 (2<13), pop 5 (5<13) | [13] |
| 3 | [13] | none (13 not < 3) | [13, 3] |
| 8 | [13, 3] | pop 3 (3<8); 13 not < 8, stop | [13, 8] |

The stack, bottom to top, is `[13, 8]`. Relinking from the top down (last popped becomes the new tail) rebuilds `13 -> 8`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: using `<=` instead of `<` in the pop condition removes nodes with values *equal* to a later node, which is wrong — the problem requires a strictly greater later value to trigger removal.

- "Has a bigger node later" for a linked list is the same next-greater-element idea as for an array, applied node by node.
- Relinking after collecting survivors on a stack rebuilds the list in the correct order automatically, since the stack's pop order is tail-to-head.
- Time: O(n) — each node is pushed once and popped at most once.
