---
card: leetcode-patterns
gi: 99
slug: reverse-linked-list-ii
title: Reverse Linked List II
---

## 1. What it is

Given the `head` of a linked list and two integers `left` and `right` (1-indexed positions), reverse the nodes from position `left` to position `right`, and return the resulting list. Example: `head = [1,2,3,4,5]`, `left = 2`, `right = 4` → `[1,4,3,2,5]`.

## 2. Why & when

This is the direct application of the in-place reversal template page: reverse only a segment, then reconnect both ends back into the surrounding list. It is a strictly harder version of Reverse Linked List, since it needs the extra bookkeeping of finding the segment boundaries and stitching the reversed piece back in.

## 3. Core concept

**Key idea:** use a dummy node to simplify the case where `left == 1` (the segment starts at the very head). Walk `left - 1` steps to find the node just before the segment. Reverse exactly `right - left + 1` nodes using the standard `prev`/`curr`/`next` loop. Reconnect the node before the segment to the new segment head, and the segment's original head (now its tail) to whatever follows.

**Steps:**
1. Create `dummy.next = head`. Walk `beforeSegment` forward `left - 1` steps from `dummy`.
2. Save `segmentHead = beforeSegment.next`.
3. Run the standard reversal loop for `right - left + 1` iterations, starting `prev = null`, `curr = segmentHead`.
4. Reconnect: `beforeSegment.next = prev` (new segment head); `segmentHead.next = curr` (node right after the segment).
5. Return `dummy.next`.

**Why it is correct:** this is exactly the segment-reversal template from the pattern-meta pages — walking to the boundary, reversing a bounded number of nodes, then reconnecting both ends. The dummy node means no special case is needed even when `left = 1`, since `beforeSegment` correctly becomes `dummy` itself in that situation.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Reversing positions 2 to 4 of a linked list">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">head = [1,2,3,4,5], left=2, right=4</text>
    <circle cx="40" cy="70" r="16" fill="#161b22" stroke="#30363d"/><text x="40" y="75" fill="#8b949e" text-anchor="middle" font-size="9">dummy</text>
    <circle cx="100" cy="70" r="18" fill="#161b22" stroke="#30363d"/><text x="100" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="180" cy="70" r="18" fill="#161b22" stroke="#f0883e"/><text x="180" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <circle cx="260" cy="70" r="18" fill="#161b22" stroke="#f0883e"/><text x="260" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <circle cx="340" cy="70" r="18" fill="#161b22" stroke="#f0883e"/><text x="340" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <circle cx="420" cy="70" r="18" fill="#161b22" stroke="#30363d"/><text x="420" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">5</text>
    <line x1="118" y1="70" x2="162" y2="70" stroke="#3fb950" marker-end="url(#l)"/>
    <line x1="358" y1="70" x2="402" y2="70" stroke="#3fb950" marker-end="url(#l)"/>
    <defs><marker id="l" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#3fb950"/></marker></defs>
    <text x="20" y="130" fill="#8b949e">node 1 reconnects to new segment head 4; node 2 (now tail) reconnects to node 5</text>
  </g>
</svg>

Positions `2` through `4` (values `2, 3, 4`) reverse internally to `4, 3, 2`, and the two reconnection links stitch the reversed piece back into the surrounding list.

## 5. Runnable example

```java
// ReverseLinkedListII.java
public class ReverseLinkedListII {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: copy all values into a list, reverse just
    // the [left,right] slice, rebuild the linked list. O(n) time, O(n)
    // space -- wastes memory an in-place segment reversal does not need.
    static ListNode bruteForce(ListNode head, int left, int right) {
        java.util.List<Integer> vals = new java.util.ArrayList<>();
        for (ListNode cur = head; cur != null; cur = cur.next) vals.add(cur.val);
        java.util.Collections.reverse(vals.subList(left - 1, right));
        ListNode dummy = new ListNode(0), cur = dummy;
        for (int v : vals) { cur.next = new ListNode(v); cur = cur.next; }
        return dummy.next;
    }

    // KEY INSIGHT: a dummy node before head plus the standard segment
    // reversal template (walk to boundary, reverse k nodes, reconnect
    // both ends) handles ANY left/right range, including left=1,
    // without special-casing.

    // Level 2 -- Optimal: dummy node, segment reversal, reconnect.
    // O(n) time, O(1) extra space.
    public static ListNode reverseBetween(ListNode head, int left, int right) {
        ListNode dummy = new ListNode(0);
        dummy.next = head;

        ListNode beforeSegment = dummy;
        for (int i = 0; i < left - 1; i++) beforeSegment = beforeSegment.next;

        ListNode segmentHead = beforeSegment.next;
        ListNode prev = null, curr = segmentHead;
        for (int i = 0; i < right - left + 1; i++) {
            ListNode next = curr.next;
            curr.next = prev;
            prev = curr;
            curr = next;
        }

        beforeSegment.next = prev;
        segmentHead.next = curr;
        return dummy.next;
    }

    // Level 3 -- Hardened: left == right (a single-node "segment," a
    // no-op reversal) and left == 1 (segment starts at the true head).
    static ListNode hardened(ListNode head, int left, int right) {
        return reverseBetween(head, left, right);
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
        print(bruteForce(build(1, 2, 3, 4, 5), 2, 4));
        print(reverseBetween(build(1, 2, 3, 4, 5), 2, 4));

        System.out.print("left==right: "); print(hardened(build(1, 2, 3), 2, 2));
        System.out.print("left==1: "); print(hardened(build(1, 2, 3), 1, 2));
    }
}
```

How to run: save as `ReverseLinkedListII.java`, then run `java ReverseLinkedListII.java`.

## 6. Walkthrough

Dry run of `reverseBetween({1,2,3,4,5}, 2, 4)`:

1. `beforeSegment` walks `left - 1 = 1` step from `dummy`, landing on node `1`.
2. `segmentHead = beforeSegment.next = 2`.
3. Reversal loop runs `right - left + 1 = 3` times: after all 3 iterations, `prev = 4` (new segment head), `curr = 5` (first node after the segment).
4. Reconnect: `beforeSegment.next = prev` → `1.next = 4`. `segmentHead.next = curr` → `2.next = 5`.
5. Return `dummy.next = 1`. Final list: `1 -> 4 -> 3 -> 2 -> 5`.

Time complexity: O(n) — O(left) to find the boundary plus O(right - left) to reverse. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: using 0-indexed loop bounds when the problem specifies 1-indexed `left`/`right` is a common off-by-one source — walking `left - 1` steps (not `left`) to reach the node *before* the segment is essential.

- This problem is the exact segment-reversal template from the pattern-meta pages, applied with explicit numeric boundaries — no new technique beyond what the template already covers.
- Related problems: Reverse Linked List (the full-list special case), Swap Nodes in Pairs (many small segment reversals of length 2 in a row).
