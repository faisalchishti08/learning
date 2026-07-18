---
card: leetcode-patterns
gi: 94
slug: in-place-linkedlist-reversal-signal-reverse-all-or-part-of-a
title: In-place LinkedList Reversal — signal: reverse all or part of a linked list without extra space
---

## 1. What it is

In-place linked list reversal is a technique for reversing the direction of `next` pointers in some or all of a linked list, without allocating a new list or copying values into an array. It works by walking the list once, redirecting each node's `next` pointer to point backward instead of forward.

## 2. Why & when

Copying node values into an array, reversing the array, then writing the values back into the list works, but it costs O(n) extra space and it is unnecessary — a linked list can be reversed by only rewiring existing pointers, needing no extra memory beyond a few tracking variables.

Learn to recognize these signals in a problem statement:

- **"Reverse a linked list"**, in whole or in part (e.g. "reverse nodes from position `m` to `n`").
- **"Reverse in groups of `k`"** or **"reverse every other group."**
- **"Rotate"** or **"rearrange"** a linked list, where the underlying mechanism often needs a partial reversal or a reversal combined with relinking.
- **A constraint of O(1) extra space** on a linked list problem — a strong hint that pointer rewiring, not array copying, is expected.

The alternative is copying to an array (O(n) space) or building a brand-new reversed list with newly allocated nodes (also O(n) space, plus wasted allocation). In-place reversal is the answer whenever the existing nodes can simply be relinked.

## 3. Core concept

**Key idea:** walk through the list with three pointers — `prev` (initially `null`), `curr` (starting at `head`), and a temporary `next` to remember where to go before you overwrite `curr.next`. At each step, redirect `curr.next` to point at `prev` instead of forward, then advance all three pointers by one node.

**Steps:**
1. Set `prev = null`, `curr = head`.
2. While `curr != null`:
   - Save `next = curr.next` (before it gets overwritten).
   - Reverse the pointer: `curr.next = prev`.
   - Advance: `prev = curr`, `curr = next`.
3. When the loop ends (`curr == null`), `prev` is the new head of the reversed list.

**Why it works:** each node's `next` pointer is rewritten exactly once, in place, using only the temporary `next` variable to avoid losing the rest of the list. Since every node is visited exactly once and each visit does O(1) work, the whole list reverses in one linear pass with no extra list-sized memory.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Reversing a linked list by rewiring next pointers">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">before: 1 -&gt; 2 -&gt; 3 -&gt; null</text>
    <circle cx="60" cy="60" r="20" fill="#161b22" stroke="#79c0ff"/><text x="60" y="65" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="140" cy="60" r="20" fill="#161b22" stroke="#79c0ff"/><text x="140" y="65" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="220" cy="60" r="20" fill="#161b22" stroke="#79c0ff"/><text x="220" y="65" fill="#e6edf3" text-anchor="middle">3</text>
    <line x1="80" y1="60" x2="120" y2="60" stroke="#8b949e" marker-end="url(#h)"/>
    <line x1="160" y1="60" x2="200" y2="60" stroke="#8b949e" marker-end="url(#h)"/>
    <defs><marker id="h" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#8b949e"/></marker></defs>
    <text x="20" y="120" fill="#e6edf3">after: null &lt;- 1 &lt;- 2 &lt;- 3 (new head is 3)</text>
    <circle cx="60" cy="160" r="20" fill="#161b22" stroke="#3fb950"/><text x="60" y="165" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="140" cy="160" r="20" fill="#161b22" stroke="#3fb950"/><text x="140" y="165" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="220" cy="160" r="20" fill="#161b22" stroke="#3fb950"/><text x="220" y="165" fill="#e6edf3" text-anchor="middle">3</text>
    <line x1="120" y1="160" x2="80" y2="160" stroke="#8b949e" marker-end="url(#h)"/>
    <line x1="200" y1="160" x2="160" y2="160" stroke="#8b949e" marker-end="url(#h)"/>
  </g>
</svg>

Each `next` pointer is flipped to point backward, one node at a time, transforming the forward chain into a reversed one using only existing nodes.

## 5. Runnable example

A generic full-list reversal skeleton you can adapt to related problems in this pattern.

```java
// InPlaceReversalSignal.java
public class InPlaceReversalSignal {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    static ListNode reverse(ListNode head) {
        ListNode prev = null, curr = head;
        while (curr != null) {
            ListNode next = curr.next;
            curr.next = prev;
            prev = curr;
            curr = next;
        }
        return prev;
    }

    public static void main(String[] args) {
        ListNode head = new ListNode(1);
        head.next = new ListNode(2);
        head.next.next = new ListNode(3);

        ListNode reversed = reverse(head);
        StringBuilder sb = new StringBuilder();
        for (ListNode cur = reversed; cur != null; cur = cur.next) sb.append(cur.val).append(" ");
        System.out.println(sb.toString().trim());
    }
}
```

How to run: save as `InPlaceReversalSignal.java`, then run `java InPlaceReversalSignal.java`.

## 6. Walkthrough

1. `prev = null`, `curr = 1`. Save `next = 2`. Set `1.next = null`. Advance: `prev = 1`, `curr = 2`.
2. Save `next = 3`. Set `2.next = 1` (pointing backward). Advance: `prev = 2`, `curr = 3`.
3. Save `next = null`. Set `3.next = 2`. Advance: `prev = 3`, `curr = null`. Loop ends.
4. `prev` is `3`, the new head. The list now reads `3 -> 2 -> 1 -> null`.

## 7. Gotchas & takeaways

> Gotcha: forgetting to save `next = curr.next` before overwriting `curr.next = prev` permanently loses the rest of the list — once `curr.next` is rewritten, there is no way to reach the remaining nodes.

- In-place reversal only needs O(1) extra space, unlike an array-copy approach which needs O(n).
- The three-pointer shape (`prev`, `curr`, `next`) generalizes to partial reversals, group reversals, and many relinking problems — see the following pages in this section.
