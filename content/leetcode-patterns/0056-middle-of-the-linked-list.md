---
card: leetcode-patterns
gi: 56
slug: middle-of-the-linked-list
title: Middle of the Linked List
---

## 1. What it is

Given the `head` of a singly linked list, return the middle node. If there are two middle nodes (an even-length list), return the second one. Example: `head = [1,2,3,4,5]` → return the node with value `3`. Example: `head = [1,2,3,4,5,6]` → return the node with value `4`.

## 2. Why & when

The naive approach counts the list's length in one pass, computes the middle index, then walks the list a second time to reach it — two full passes. Fast & slow pointers finds the middle in a single pass, using the fact that when a pointer moving twice as fast reaches the end, a pointer moving half as fast is exactly at the midpoint.

## 3. Core concept

**Key idea:** advance `slow` by one node and `fast` by two nodes on every iteration. When `fast` cannot move two more steps (it is `null` or its `next` is `null`), `slow` sits exactly on the middle node.

**Steps:**
1. Set `slow = head`, `fast = head`.
2. While `fast != null && fast.next != null`:
   - `slow = slow.next`.
   - `fast = fast.next.next`.
3. Return `slow`.

**Why it is correct:** at every step, `slow` has covered exactly half the distance `fast` has covered. When `fast` finishes traversing the list (reaching `null` or the last node), `slow` has covered half that distance — which is, by definition, the middle.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Slow pointer landing on the middle node">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">head = [1, 2, 3, 4, 5]</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="70" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="120" y="40" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <rect x="170" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="220" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="90" y="60" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="140" y="60" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="190" y="60" fill="#e6edf3" text-anchor="middle">4</text>
    <text x="240" y="60" fill="#e6edf3" text-anchor="middle">5</text>
    <text x="140" y="30" fill="#f0883e" text-anchor="middle">slow stops here</text>
    <text x="240" y="30" fill="#79c0ff" text-anchor="middle">fast stops here</text>
    <text x="20" y="110" fill="#8b949e">fast covers 4 links while slow covers 2 -- slow lands on the middle, node 3</text>
  </g>
</svg>

Fast reaches the last node after 2 double-steps; slow, moving at half the speed, has covered exactly half the list — landing on the middle.

## 5. Runnable example

```java
// MiddleOfTheLinkedList.java
public class MiddleOfTheLinkedList {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: count the length, then walk again to the
    // midpoint index. O(n) time but TWO passes -- wastes a full re-scan.
    static ListNode bruteForce(ListNode head) {
        int len = 0;
        for (ListNode cur = head; cur != null; cur = cur.next) len++;
        ListNode cur = head;
        for (int i = 0; i < len / 2; i++) cur = cur.next;
        return cur;
    }

    // KEY INSIGHT: a pointer moving at double speed always covers exactly
    // double the distance -- so when it finishes the list, the half-speed
    // pointer is standing exactly at the midpoint, no counting needed.

    // Level 2 -- Optimal: fast &amp; slow pointers, ONE pass. O(n) time,
    // O(1) space.
    public static ListNode middleNode(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
        }
        return slow;
    }

    // Level 3 -- Hardened: works for a single-node list (returns that node)
    // and correctly picks the SECOND middle for even-length lists.
    static ListNode hardened(ListNode head) {
        if (head == null) throw new IllegalArgumentException("empty list");
        return middleNode(head);
    }

    static void printFrom(ListNode node) {
        StringBuilder sb = new StringBuilder();
        for (ListNode cur = node; cur != null; cur = cur.next) sb.append(cur.val).append(" ");
        System.out.println(sb.toString().trim());
    }

    public static void main(String[] args) {
        ListNode odd = build(1, 2, 3, 4, 5);
        System.out.println("odd-length middle onward:");
        printFrom(middleNode(odd));

        ListNode even = build(1, 2, 3, 4, 5, 6);
        System.out.println("even-length middle onward:");
        printFrom(hardened(even));
    }

    static ListNode build(int... vals) {
        ListNode dummy = new ListNode(0), cur = dummy;
        for (int v : vals) { cur.next = new ListNode(v); cur = cur.next; }
        return dummy.next;
    }
}
```

How to run: save as `MiddleOfTheLinkedList.java`, then run `java MiddleOfTheLinkedList.java`.

## 6. Walkthrough

Dry run of `middleNode` on `1 -> 2 -> 3 -> 4 -> 5`:

| step | slow | fast |
|---|---|---|
| start | 1 | 1 |
| 1 | 2 | 3 |
| 2 | 3 | 5 |
| — | — | `fast.next` is null, loop stops |

`slow` ends on node `3`, the middle. Time complexity: O(n), one pass. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: for an even-length list like `1,2,3,4`, this template returns the *second* middle (`3`). If a variant of the problem wants the first middle, start `fast` one step ahead: `fast = head.next`.

- This is the direct application of the "finding the middle" half of the pattern's signal.
- Related problems: Linked List Cycle (same loop shape, different stopping condition), Palindrome Linked List (uses this to split the list in half), Reorder List (also splits at the middle first).
