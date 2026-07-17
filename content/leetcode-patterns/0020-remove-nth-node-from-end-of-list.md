---
card: leetcode-patterns
gi: 20
slug: remove-nth-node-from-end-of-list
title: Remove Nth Node From End of List
---

## 1. What it is

Given the head of a linked list, remove the `n`-th node from the **end** of the list, and return the head. Example: list `1 -> 2 -> 3 -> 4 -> 5`, `n = 2` → remove the 2nd-from-end node (`4`), returning `1 -> 2 -> 3 -> 5`.

## 2. Why & when

A linked list has no index access and no length known up front (without a separate pass). The two-pointer trick here is a **fixed-gap** variant: one pointer starts `n` steps ahead of the other, so when the lead pointer reaches the end, the trailing pointer is exactly at the node you need to act on. This finds the target in one pass instead of two (one to count the length, one to walk to the target).

## 3. Core concept

**Key idea:** if two pointers move at the same speed but start `n` nodes apart, they stay `n` nodes apart the whole time — so when the front one runs out of list, the back one is `n` nodes from the end.

**Steps:**
1. Create a dummy node pointing to `head`, so removing the actual head node does not need a special case. Set `slow = dummy`, `fast = dummy`.
2. Advance `fast` by `n + 1` steps (one extra, so `slow` ends up just *before* the node to remove, not on it).
3. While `fast != null`: advance both `slow` and `fast` by one step.
4. Now `slow.next` is the node to remove. Set `slow.next = slow.next.next` to unlink it.
5. Return `dummy.next` (the new head, which may have changed if the original head was removed).

**Why it is correct:** the gap between `fast` and `slow` stays constant at `n + 1` throughout the walk. When `fast` becomes `null` (has moved past the last node), `slow` is exactly `n + 1` nodes behind the end — one node before the target — which is exactly the position needed to unlink it with a single `next` reassignment.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Remove nth node fixed gap two pointers on a linked list">
  <g font-family="sans-serif" font-size="13">
    <rect x="20" y="40" width="50" height="34" fill="#161b22" stroke="#8b5cf6"/>
    <rect x="90" y="40" width="50" height="34" fill="#161b22" stroke="#79c0ff"/>
    <rect x="160" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="230" y="40" width="50" height="34" fill="#161b22" stroke="#f0883e"/>
    <rect x="300" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <text x="45" y="63" fill="#e6edf3" text-anchor="middle">dummy</text>
    <text x="115" y="63" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="185" y="63" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="255" y="63" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="325" y="63" fill="#e6edf3" text-anchor="middle">4</text>
    <text x="115" y="95" fill="#79c0ff" text-anchor="middle">slow</text>
    <text x="255" y="95" fill="#f0883e" text-anchor="middle">fast (n+1=3 ahead)</text>
    <text x="20" y="125" fill="#8b949e">both step together; when fast hits null, slow.next is the target to remove</text>
  </g>
</svg>

`fast` starts `n + 1` nodes ahead so that when it runs off the list, `slow` sits just before the node to delete.

## 5. Runnable example

```java
// RemoveNthFromEnd.java
public class RemoveNthFromEnd {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: walk the list once to count its length, then
    // walk again to the node just before the target. Two passes, O(L) time,
    // O(1) space -- correct, but does twice the traversal work.
    static ListNode bruteForce(ListNode head, int n) {
        int length = 0;
        for (ListNode node = head; node != null; node = node.next) length++;
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode cur = dummy;
        for (int i = 0; i < length - n; i++) cur = cur.next;
        cur.next = cur.next.next;
        return dummy.next;
    }

    // KEY INSIGHT: a fixed gap of n+1 between two same-speed pointers means
    // that when the lead pointer exhausts the list, the trailing pointer is
    // exactly one node before the target -- a single pass suffices.

    // Level 2 -- Optimal: fixed-gap two pointers, one pass. O(L) time, O(1)
    // space.
    public static ListNode removeNthFromEnd(ListNode head, int n) {
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode slow = dummy, fast = dummy;
        for (int i = 0; i < n + 1; i++) {
            fast = fast.next;
        }
        while (fast != null) {
            slow = slow.next;
            fast = fast.next;
        }
        slow.next = slow.next.next;
        return dummy.next;
    }

    // Level 3 -- Hardened: removing the head itself (n equals the list
    // length) works because of the dummy node -- slow stays at dummy, and
    // dummy.next = dummy.next.next correctly drops the old head.
    static ListNode hardened(ListNode head, int n) {
        if (head == null) throw new IllegalArgumentException("list must not be empty");
        return removeNthFromEnd(head, n);
    }

    static ListNode build(int... vals) {
        ListNode dummy = new ListNode(0);
        ListNode cur = dummy;
        for (int v : vals) { cur.next = new ListNode(v); cur = cur.next; }
        return dummy.next;
    }

    static String toStr(ListNode head) {
        StringBuilder sb = new StringBuilder();
        for (ListNode n = head; n != null; n = n.next) sb.append(n.val).append(n.next != null ? " -> " : "");
        return sb.toString();
    }

    public static void main(String[] args) {
        ListNode list = build(1, 2, 3, 4, 5);
        System.out.println("optimal: " + toStr(removeNthFromEnd(list, 2)));

        ListNode singleNode = build(1);
        System.out.println("remove only node: " + toStr(hardened(singleNode, 1)));
    }
}
```

How to run: save as `RemoveNthFromEnd.java`, then run `java RemoveNthFromEnd.java`.

## 6. Walkthrough

Dry run of `removeNthFromEnd(1 -> 2 -> 3 -> 4 -> 5, n = 2)`:

1. `dummy -> 1 -> 2 -> 3 -> 4 -> 5`. `slow = dummy`, `fast = dummy`.
2. Advance `fast` by `n + 1 = 3` steps: `fast` moves to `dummy -> 1 -> 2 -> 3`, landing on node `3`.
3. Loop: advance both one step at a time until `fast` is `null`.
   - `fast = 4`, `slow = 1`.
   - `fast = 5`, `slow = 2`.
   - `fast = null`, `slow = 3`.
4. `slow.next` is node `4`, the target. Set `slow.next = slow.next.next` (node `5`), unlinking `4`.
5. Return `dummy.next`, which is `1 -> 2 -> 3 -> 5`.

Time complexity: O(L), one pass over the list. Space complexity: O(1), plus the dummy node.

## 7. Gotchas & takeaways

> Gotcha: skipping the dummy node and starting `slow`/`fast` at `head` directly breaks the case where the node to remove is the head itself — there is no "previous" node to update `next` on. The dummy node sidesteps this by giving every real node a predecessor.

- The gap size is `n + 1`, not `n` — the extra step is what leaves `slow` one node *before* the target, which is what you need to unlink it.
- Related problems: Middle of the Linked List (a same-speed-gap variant using a 2x-speed `fast` pointer instead of a fixed gap), Linked List Cycle (fast/slow pointers detect a cycle instead of finding an end offset), Reorder List.
