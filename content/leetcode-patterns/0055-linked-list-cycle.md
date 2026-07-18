---
card: leetcode-patterns
gi: 55
slug: linked-list-cycle
title: Linked List Cycle
---

## 1. What it is

Given the `head` of a linked list, determine whether the list has a cycle: some node's `next` pointer eventually loops back to a node earlier in the list, so the list has no true "end". Example: `head = [3,2,0,-4]` where the last node points back to the node at index `1` → answer `true`.

## 2. Why & when

This is the direct application of the Fast & Slow Pointers pattern's core signal: "does the linked list have a cycle?" The naive approach stores every visited node in a hash set and checks for repeats, which works but costs O(n) extra space. This problem is the canonical example for practicing the O(1)-space alternative.

## 3. Core concept

**Key idea:** move two pointers through the list at different speeds. If they ever land on the same node, a cycle exists. If the fast pointer reaches the end (`null`), no cycle exists.

**Steps:**
1. Set `slow = head`, `fast = head`.
2. While `fast != null && fast.next != null`:
   - `slow = slow.next`.
   - `fast = fast.next.next`.
   - If `slow == fast`, return `true`.
3. If the loop exits normally (fast hit `null`), return `false`.

**Why it is correct:** if there is no cycle, `fast` reaches `null` in at most `n/2` iterations, since it moves twice as fast as `slow`. If there is a cycle, once both pointers are inside it, the distance between them shrinks by one node every iteration (because `fast` gains one extra step relative to `slow`), so they must meet within at most the cycle's length in iterations.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Linked list with a cycle detected by fast and slow pointers">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">head = [3, 2, 0, -4], tail.next points back to node index 1 (value 2)</text>
    <circle cx="60" cy="90" r="20" fill="#161b22" stroke="#79c0ff"/>
    <text x="60" y="95" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="140" cy="90" r="20" fill="#161b22" stroke="#f0883e"/>
    <text x="140" y="95" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="220" cy="90" r="20" fill="#161b22" stroke="#30363d"/>
    <text x="220" y="95" fill="#e6edf3" text-anchor="middle">0</text>
    <circle cx="300" cy="90" r="20" fill="#161b22" stroke="#30363d"/>
    <text x="300" y="95" fill="#e6edf3" text-anchor="middle">-4</text>
    <line x1="80" y1="90" x2="120" y2="90" stroke="#8b949e" marker-end="url(#b)"/>
    <line x1="160" y1="90" x2="200" y2="90" stroke="#8b949e" marker-end="url(#b)"/>
    <line x1="240" y1="90" x2="280" y2="90" stroke="#8b949e" marker-end="url(#b)"/>
    <path d="M300,110 C300,150 140,150 140,110" fill="none" stroke="#8b949e" marker-end="url(#b)"/>
    <defs><marker id="b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#8b949e"/></marker></defs>
    <text x="20" y="160" fill="#8b949e">slow and fast both start at 3; fast laps slow inside the loop, so they meet</text>
  </g>
</svg>

The tail node `-4` points back to node `2` instead of `null`, forming the loop the fast pointer eventually laps.

## 5. Runnable example

```java
// LinkedListCycle.java
public class LinkedListCycle {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: track visited nodes in a hash set. O(n) time,
    // O(n) space -- wastes memory storing every node just to spot a repeat.
    static boolean bruteForce(ListNode head) {
        java.util.Set<ListNode> seen = new java.util.HashSet<>();
        ListNode cur = head;
        while (cur != null) {
            if (!seen.add(cur)) return true;
            cur = cur.next;
        }
        return false;
    }

    // KEY INSIGHT: a pointer moving twice as fast as another will always
    // lap it inside a cycle, because the gap between them shrinks by one
    // node every step -- so no extra memory is needed to detect the loop.

    // Level 2 -- Optimal: fast &amp; slow pointers. O(n) time, O(1) space.
    public static boolean hasCycle(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) return true;
        }
        return false;
    }

    // Level 3 -- Hardened: handles null head and single-node lists (with
    // or without a self-loop) without special-casing them separately.
    static boolean hardened(ListNode head) {
        if (head == null) return false;
        return hasCycle(head);
    }

    public static void main(String[] args) {
        ListNode a = new ListNode(3);
        ListNode b = new ListNode(2);
        ListNode c = new ListNode(0);
        ListNode d = new ListNode(-4);
        a.next = b; b.next = c; c.next = d; d.next = b; // cycle into b

        System.out.println("brute force: " + bruteForce(a));
        System.out.println("optimal:     " + hasCycle(a));

        ListNode single = new ListNode(1);
        System.out.println("single, no cycle: " + hardened(single));
        System.out.println("null head: " + hardened(null));
    }
}
```

How to run: save as `LinkedListCycle.java`, then run `java LinkedListCycle.java`.

## 6. Walkthrough

Dry run of `hasCycle` on `3 -> 2 -> 0 -> -4 -> back to 2`:

| step | slow | fast | slow == fast? |
|---|---|---|---|
| start | 3 | 3 | no |
| 1 | 2 | 0 | no |
| 2 | 0 | 2 (via -4 -> 2) | no |
| 3 | -4 | -4 (via 0 -> -4) | yes -> return true |

Time complexity: O(n), since each pointer visits at most O(n) nodes before the loop ends. Space complexity: O(1), since only `slow` and `fast` are stored.

## 7. Gotchas & takeaways

> Gotcha: comparing node *values* instead of node *references* (`slow.val == fast.val`) gives false positives when different nodes happen to hold equal values. Always compare the object references.

- This problem is the direct template application from the pattern-meta pages — no variation needed beyond the base loop.
- Related problems: Linked List Cycle II (find where the cycle starts), Happy Number (cycle detection on a value sequence instead of node pointers).
