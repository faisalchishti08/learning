---
card: leetcode-patterns
gi: 98
slug: remove-linked-list-elements
title: Remove Linked List Elements
---

## 1. What it is

Given the `head` of a linked list and an integer `val`, remove every node whose value equals `val`, and return the new head. Example: `head = [1,2,6,3,4,5,6]`, `val = 6` → `[1,2,3,4,5]`.

## 2. Why & when

This problem sits alongside reversal problems in this section because it uses the same core skill — careful pointer relinking — to safely delete nodes from a singly linked list. A dummy node placed before `head` avoids special-casing the situation where the very first node itself must be removed, the same trick used to simplify segment-reversal reconnection.

## 3. Core concept

**Key idea:** walk through the list with a pointer `prev` that always trails one node behind `curr`. Whenever `curr.val == val`, skip over it by relinking `prev.next` directly to `curr.next`. Otherwise, advance `prev` along with `curr`.

**Steps:**
1. Create a `dummy` node with `dummy.next = head`; set `prev = dummy`, `curr = head`.
2. While `curr != null`:
   - If `curr.val == val`, remove it: `prev.next = curr.next`.
   - Otherwise, advance `prev = curr`.
   - Either way, advance `curr = curr.next`.
3. Return `dummy.next` — the new head, correctly handling the case where the original head itself was removed.

**Why it is correct:** `prev` always points at the most recently *kept* node. Skipping a matching node by relinking `prev.next` directly past it removes that node from the chain without disturbing the rest of the list. Because `prev` never advances onto a removed node, later relinking always starts from a valid, still-connected position.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Removing matching nodes using a trailing prev pointer">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">head = [1, 2, 6, 3], val = 6</text>
    <circle cx="40" cy="70" r="16" fill="#161b22" stroke="#30363d"/><text x="40" y="75" fill="#8b949e" text-anchor="middle" font-size="9">dummy</text>
    <circle cx="100" cy="70" r="18" fill="#161b22" stroke="#79c0ff"/><text x="100" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="160" cy="70" r="18" fill="#161b22" stroke="#79c0ff"/><text x="160" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <circle cx="220" cy="70" r="18" fill="#161b22" stroke="#f0883e"/><text x="220" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">6</text>
    <circle cx="280" cy="70" r="18" fill="#161b22" stroke="#79c0ff"/><text x="280" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <path d="M160,88 C185,110 220,110 240,88" fill="none" stroke="#3fb950" marker-end="url(#k)"/>
    <defs><marker id="k" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#3fb950"/></marker></defs>
    <text x="20" y="140" fill="#8b949e">prev (at node 2) relinks directly to node 3, skipping node 6 entirely</text>
  </g>
</svg>

`prev` (at node `2`) relinks `next` directly to node `3`, bypassing the matching node `6` and removing it from the chain in one pointer update.

## 5. Runnable example

```java
// RemoveLinkedListElements.java
public class RemoveLinkedListElements {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: copy non-matching values into a new list,
    // discarding matches. O(n) time, O(n) space -- wastes memory an
    // in-place relink does not need.
    static ListNode bruteForce(ListNode head, int val) {
        ListNode dummy = new ListNode(0), cur = dummy;
        for (ListNode node = head; node != null; node = node.next) {
            if (node.val != val) {
                cur.next = new ListNode(node.val);
                cur = cur.next;
            }
        }
        return dummy.next;
    }

    // KEY INSIGHT: a dummy node before head lets the SAME relinking logic
    // handle removing the very first node as removing any other node --
    // no special-casing needed for "head itself must be removed."

    // Level 2 -- Optimal: dummy node, trailing prev pointer. O(n) time,
    // O(1) extra space.
    public static ListNode removeElements(ListNode head, int val) {
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode prev = dummy, curr = head;
        while (curr != null) {
            if (curr.val == val) {
                prev.next = curr.next;
            } else {
                prev = curr;
            }
            curr = curr.next;
        }
        return dummy.next;
    }

    // Level 3 -- Hardened: every node matches val (result is an empty
    // list), and consecutive matching nodes in a row.
    static ListNode hardened(ListNode head, int val) {
        return removeElements(head, val);
    }

    static ListNode build(int... vals) {
        ListNode dummy = new ListNode(0), cur = dummy;
        for (int v : vals) { cur.next = new ListNode(v); cur = cur.next; }
        return dummy.next;
    }

    static void print(ListNode head) {
        StringBuilder sb = new StringBuilder();
        for (ListNode cur = head; cur != null; cur = cur.next) sb.append(cur.val).append(" ");
        System.out.println(sb.toString().trim());
    }

    public static void main(String[] args) {
        print(bruteForce(build(1, 2, 6, 3, 4, 5, 6), 6));
        print(removeElements(build(1, 2, 6, 3, 4, 5, 6), 6));

        System.out.print("all match: "); print(hardened(build(7, 7, 7), 7));
        System.out.print("consecutive matches: "); print(hardened(build(1, 6, 6, 2), 6));
    }
}
```

How to run: save as `RemoveLinkedListElements.java`, then run `java RemoveLinkedListElements.java`.

## 6. Walkthrough

Dry run of `removeElements` on `1 -> 2 -> 6 -> 3`, `val = 6`:

| step | prev | curr | curr.val==6? | action |
|---|---|---|---|---|
| 1 | dummy | 1 | no | prev=1 |
| 2 | 1 | 2 | no | prev=2 |
| 3 | 2 | 6 | yes | prev.next = curr.next (2.next=3), prev unchanged |
| 4 | 2 | 3 | no | prev=3 |

`curr` advances to `null` after step 4, loop ends. Return `dummy.next = 1`. Final list: `1 -> 2 -> 3`. Time complexity: O(n). Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: advancing `prev = curr` on every iteration, even when a node was just removed, leaves `prev` pointing at a node that is no longer connected to the list — always skip advancing `prev` on a removal, since it must always point at the last *kept* node.

- The dummy-node trick used here is the same simplification used for segment reversal reconnection — recognize it as a general-purpose tool for any "the first node might need special handling" linked list problem.
- Related problems: Remove Duplicates from Sorted List II (removes based on a value-repetition condition instead of a fixed target), Reverse Linked List (the base relinking skill this problem also depends on).
