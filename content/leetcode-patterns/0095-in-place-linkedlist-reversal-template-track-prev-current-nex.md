---
card: leetcode-patterns
gi: 95
slug: in-place-linkedlist-reversal-template-track-prev-current-nex
title: In-place LinkedList Reversal — template: track prev/current/next and relink pointers
---

## 1. What it is

This page gives the reusable code template for in-place linked list reversal, extended beyond the full-list case: reversing a specific sub-section of a list (between two given nodes), which is the shape needed by most named problems in this section.

## 2. Why & when

Most problems in this pattern do not reverse the *entire* list — they reverse a segment (nodes `m` through `n`, or each group of `k` nodes) and then must reconnect that reversed segment back into the surrounding list correctly. The template adds two extra pieces to the base reversal loop: a pointer to the node *before* the segment (to reattach the new segment head) and careful tracking of the segment's original head (which becomes its new tail, and must reconnect to whatever follows).

## 3. Core concept

**Key idea:** walk to the node just before the segment to reverse. Run the standard `prev`/`curr`/`next` reversal loop, but only for the nodes inside the segment. After the loop, reconnect: the node before the segment points to the segment's new head (`prev`), and the segment's original head (now the tail of the reversed segment) points to whatever came after the segment (`curr`, which stopped just past the segment).

**General steps:**
1. Walk `k` steps (or however many nodes precede the segment) to find `beforeSegment`, the node just before the segment starts.
2. Save `segmentHead = beforeSegment.next` — this node becomes the segment's tail after reversal.
3. Run the standard reversal loop for exactly the segment's length, using `prev = null`, `curr = segmentHead`.
4. Reconnect: `beforeSegment.next = prev` (the new segment head); `segmentHead.next = curr` (the node right after the segment).

**Why it works:** the core swap-pointers loop does not care whether it operates on a whole list or a sub-list — it only needs a starting node and a stopping condition (in this case, after exactly the segment's length, rather than until `null`). The reconnection step is what stitches the reversed segment back into its surrounding context correctly.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Reversing a segment of a linked list and reconnecting it">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">1 -&gt; 2 -&gt; 3 -&gt; 4 -&gt; 5, reverse segment [2,4] (nodes with value 2,3,4)</text>
    <circle cx="60" cy="80" r="20" fill="#161b22" stroke="#30363d"/><text x="60" y="85" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="140" cy="80" r="20" fill="#161b22" stroke="#f0883e"/><text x="140" y="85" fill="#e6edf3" text-anchor="middle">4</text>
    <circle cx="220" cy="80" r="20" fill="#161b22" stroke="#f0883e"/><text x="220" y="85" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="300" cy="80" r="20" fill="#161b22" stroke="#f0883e"/><text x="300" y="85" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="380" cy="80" r="20" fill="#161b22" stroke="#30363d"/><text x="380" y="85" fill="#e6edf3" text-anchor="middle">5</text>
    <line x1="80" y1="80" x2="120" y2="80" stroke="#3fb950" marker-end="url(#i)"/>
    <line x1="160" y1="80" x2="200" y2="80" stroke="#8b949e" marker-end="url(#i)"/>
    <line x1="240" y1="80" x2="280" y2="80" stroke="#8b949e" marker-end="url(#i)"/>
    <line x1="320" y1="80" x2="360" y2="80" stroke="#3fb950" marker-end="url(#i)"/>
    <defs><marker id="i" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#8b949e"/></marker></defs>
    <text x="20" y="140" fill="#8b949e">beforeSegment (1) now points to new segment head (4); old segment head (2, now tail) points to 5</text>
  </g>
</svg>

The segment `2 -> 3 -> 4` reverses internally to `4 -> 3 -> 2`, and two reconnection links (`1 -> 4` and `2 -> 5`) stitch it back into the full list.

## 5. Runnable example

```java
// InPlaceReversalTemplate.java
public class InPlaceReversalTemplate {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Reverses exactly `count` nodes starting at `head`, returning the
    // new head of the reversed segment and leaving `head` pointing at
    // whatever comes right after the segment (its new tail role).
    static ListNode reverseSegment(ListNode head, int count) {
        ListNode prev = null, curr = head;
        for (int i = 0; i < count && curr != null; i++) {
            ListNode next = curr.next;
            curr.next = prev;
            prev = curr;
            curr = next;
        }
        head.next = curr; // old head (now tail) reconnects to what follows
        return prev; // new head of the reversed segment
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
        ListNode list = build(1, 2, 3, 4, 5);
        ListNode beforeSegment = list; // node "1"
        ListNode segmentHead = beforeSegment.next; // node "2"

        ListNode newSegmentHead = reverseSegment(segmentHead, 3);
        beforeSegment.next = newSegmentHead;

        print(list);
    }
}
```

How to run: save as `InPlaceReversalTemplate.java`, then run `java InPlaceReversalTemplate.java`.

## 6. Walkthrough

Trace `reverseSegment` on the segment `2 -> 3 -> 4 -> 5`, `count = 3` (reversing only `2, 3, 4`):

1. `prev = null`, `curr = 2`. Iteration 1: save `next = 3`, set `2.next = null`, `prev = 2`, `curr = 3`.
2. Iteration 2: save `next = 4`, set `3.next = 2`, `prev = 3`, `curr = 4`.
3. Iteration 3: save `next = 5`, set `4.next = 3`, `prev = 4`, `curr = 5`. Loop ends (3 iterations done).
4. `head.next = curr` sets `2.next = 5` (the original head, now tail, reconnects to what follows the segment).
5. Return `prev = 4`, the new segment head. Back in `main`, `beforeSegment.next = 4` completes the reconnection: `1 -> 4 -> 3 -> 2 -> 5`.

## 7. Gotchas & takeaways

> Gotcha: forgetting the `head.next = curr` reconnection step leaves the original segment head (now the segment's tail) still pointing at whatever node it pointed to *inside* the segment before reversal — silently creating a broken or cyclic list.

- The template separates cleanly into three parts: locate the segment, reverse it with the standard loop, reconnect both ends — memorize this three-part shape rather than re-deriving pointer logic each time.
- A dummy node before `head` is a common trick (used in the named problems ahead) to avoid special-casing when the segment to reverse starts at the very head of the list.
