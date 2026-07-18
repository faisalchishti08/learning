---
card: leetcode-patterns
gi: 97
slug: reverse-linked-list
title: Reverse Linked List
---

## 1. What it is

Given the `head` of a singly linked list, reverse the list and return the new head. Example: `head = [1,2,3,4,5]` → `[5,4,3,2,1]`.

## 2. Why & when

This is the canonical named problem for the In-place LinkedList Reversal pattern-meta pages earlier in this section — the base case every other problem in this section builds on. Copying values into an array and rebuilding costs O(n) space; the iterative `prev`/`curr`/`next` loop reverses in place with O(1) space.

## 3. Core concept

**Key idea:** walk through the list once, redirecting each node's `next` pointer to point at the previous node instead of the next one, using a temporary variable to avoid losing the rest of the list.

**Steps:**
1. Set `prev = null`, `curr = head`.
2. While `curr != null`:
   - Save `next = curr.next`.
   - Set `curr.next = prev`.
   - Advance `prev = curr`, `curr = next`.
3. Return `prev` as the new head.

**Why it is correct:** every node's `next` pointer is rewritten exactly once, and the temporary `next` variable ensures the rest of the list is never lost before it can be visited. After the last node is processed, `prev` points to what was originally the last node — now the new head of the fully reversed list.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Reversing a five node linked list">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">head = [1,2,3,4,5]</text>
    <circle cx="60" cy="60" r="18" fill="#161b22" stroke="#30363d"/><text x="60" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="120" cy="60" r="18" fill="#161b22" stroke="#30363d"/><text x="120" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <circle cx="180" cy="60" r="18" fill="#161b22" stroke="#30363d"/><text x="180" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <circle cx="240" cy="60" r="18" fill="#161b22" stroke="#30363d"/><text x="240" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <circle cx="300" cy="60" r="18" fill="#161b22" stroke="#30363d"/><text x="300" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">5</text>
    <line x1="78" y1="60" x2="102" y2="60" stroke="#8b949e" marker-end="url(#j)"/>
    <line x1="138" y1="60" x2="162" y2="60" stroke="#8b949e" marker-end="url(#j)"/>
    <line x1="198" y1="60" x2="222" y2="60" stroke="#8b949e" marker-end="url(#j)"/>
    <line x1="258" y1="60" x2="282" y2="60" stroke="#8b949e" marker-end="url(#j)"/>
    <defs><marker id="j" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#8b949e"/></marker></defs>
    <circle cx="60" cy="130" r="18" fill="#161b22" stroke="#3fb950"/><text x="60" y="135" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="120" cy="130" r="18" fill="#161b22" stroke="#3fb950"/><text x="120" y="135" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <circle cx="180" cy="130" r="18" fill="#161b22" stroke="#3fb950"/><text x="180" y="135" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <circle cx="240" cy="130" r="18" fill="#161b22" stroke="#3fb950"/><text x="240" y="135" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <circle cx="300" cy="130" r="18" fill="#161b22" stroke="#3fb950"/><text x="300" y="135" fill="#e6edf3" text-anchor="middle" font-size="11">5</text>
    <line x1="282" y1="130" x2="258" y2="130" stroke="#8b949e" marker-end="url(#j)"/>
    <line x1="222" y1="130" x2="198" y2="130" stroke="#8b949e" marker-end="url(#j)"/>
    <line x1="162" y1="130" x2="138" y2="130" stroke="#8b949e" marker-end="url(#j)"/>
    <line x1="102" y1="130" x2="78" y2="130" stroke="#8b949e" marker-end="url(#j)"/>
  </g>
</svg>

Every arrow flips direction — the list that read `1,2,3,4,5` forward now reads `5,4,3,2,1` forward, using the same five nodes.

## 5. Runnable example

```java
// ReverseLinkedList.java
public class ReverseLinkedList {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: copy values into an array, rebuild the list
    // in reverse order. O(n) time, O(n) space -- wastes memory an
    // in-place pointer rewrite does not need.
    static ListNode bruteForce(ListNode head) {
        java.util.List<Integer> vals = new java.util.ArrayList<>();
        for (ListNode cur = head; cur != null; cur = cur.next) vals.add(cur.val);
        ListNode dummy = new ListNode(0), cur = dummy;
        for (int i = vals.size() - 1; i >= 0; i--) {
            cur.next = new ListNode(vals.get(i));
            cur = cur.next;
        }
        return dummy.next;
    }

    // KEY INSIGHT: each node's next pointer only needs to be rewritten
    // once, in place -- a temporary variable preserves the rest of the
    // list before it gets overwritten.

    // Level 2 -- Optimal: iterative prev/curr/next reversal. O(n) time,
    // O(1) space.
    public static ListNode reverseList(ListNode head) {
        ListNode prev = null, curr = head;
        while (curr != null) {
            ListNode next = curr.next;
            curr.next = prev;
            prev = curr;
            curr = next;
        }
        return prev;
    }

    // Level 3 -- Hardened: empty list and single-node list, both of
    // which should be returned unchanged (a single node's reversal is
    // itself).
    static ListNode hardened(ListNode head) {
        return reverseList(head);
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
        print(bruteForce(build(1, 2, 3, 4, 5)));
        print(reverseList(build(1, 2, 3, 4, 5)));

        System.out.print("empty list: "); print(hardened(null));
        System.out.print("single node: "); print(hardened(build(7)));
    }
}
```

How to run: save as `ReverseLinkedList.java`, then run `java ReverseLinkedList.java`.

## 6. Walkthrough

Dry run of `reverseList` on `1 -> 2 -> 3`:

| step | prev | curr | next (saved) | curr.next after |
|---|---|---|---|---|
| start | null | 1 | — | — |
| 1 | 1 | 2 | 2 | 1.next = null |
| 2 | 2 | 3 | 3 | 2.next = 1 |
| 3 | 3 | null | null | 3.next = 2 |

Loop ends (`curr == null`). Return `prev = 3`. Final list: `3 -> 2 -> 1`. Time complexity: O(n), one pass. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: initializing `prev` to anything other than `null` leaves the original head's `next` pointer pointing at a stray value instead of terminating the list correctly — the original head becomes the new tail and must end in `null`.

- This is the foundational template every other problem in this section builds on — memorize the three-pointer shape here first.
- Related problems: Reverse Linked List II (reverse only a segment), Swap Nodes in Pairs (reverse in groups of 2).
