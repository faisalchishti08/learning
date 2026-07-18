---
card: leetcode-patterns
gi: 100
slug: rotate-list
title: Rotate List
---

## 1. What it is

Given the `head` of a linked list, rotate the list to the right by `k` places. Example: `head = [1,2,3,4,5]`, `k = 2` → `[4,5,1,2,3]`.

## 2. Why & when

This problem does not reverse anything, but it belongs in this section because it uses the same pointer-relinking skill: find the right place to "cut" the list, then reconnect the pieces in a new order — the exact reconnection logic used to stitch a reversed segment back into a list.

## 3. Core concept

**Key idea:** first find the list's length `n` and connect the tail back to the head, forming a temporary circle. Then find the new tail, which sits at position `n - (k % n) - 1` from the original head, and break the circle there.

**Steps:**
1. Walk to the tail, counting the length `n` along the way. Connect `tail.next = head`, forming a cycle.
2. Compute the effective rotation `k = k % n` (rotating by a multiple of `n` is a no-op).
3. Walk `n - k - 1` steps from `head` to find the new tail.
4. Set `newHead = newTail.next`; break the cycle: `newTail.next = null`.
5. Return `newHead`.

**Why it is correct:** rotating the list right by `k` places is equivalent to making the node that is `k` positions from the end become the new head. Temporarily joining the list into a circle makes it trivial to "cut" at any position without special-casing the wraparound; computing `k % n` first avoids doing redundant full rotations.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Rotating a list by temporarily forming a cycle and cutting at the new boundary">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">head = [1,2,3,4,5], k = 2 (n=5, effective k=2)</text>
    <circle cx="60" cy="80" r="18" fill="#161b22" stroke="#30363d"/><text x="60" y="85" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="120" cy="80" r="18" fill="#161b22" stroke="#30363d"/><text x="120" y="85" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <circle cx="180" cy="80" r="18" fill="#161b22" stroke="#f0883e"/><text x="180" y="85" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <circle cx="240" cy="80" r="18" fill="#161b22" stroke="#79c0ff"/><text x="240" y="85" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <circle cx="300" cy="80" r="18" fill="#161b22" stroke="#79c0ff"/><text x="300" y="85" fill="#e6edf3" text-anchor="middle" font-size="11">5</text>
    <path d="M300,98 C300,140 60,140 60,98" fill="none" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#m)"/>
    <defs><marker id="m" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#8b949e"/></marker></defs>
    <text x="20" y="170" fill="#8b949e">new tail is node 3 (position n-k-1=2); cut its "next" link -&gt; new head is node 4</text>
  </g>
</svg>

Temporarily joining tail to head forms a circle; cutting the circle right after the node at position `n - k - 1` produces the rotated list starting at node `4`.

## 5. Runnable example

```java
// RotateList.java
public class RotateList {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: rotate one step at a time, k times, by
    // moving the last node to the front on each iteration. O(n * k)
    // time -- wastes repeated full traversals when k is large.
    static ListNode bruteForce(ListNode head, int k) {
        if (head == null || head.next == null) return head;
        int n = 0;
        for (ListNode cur = head; cur != null; cur = cur.next) n++;
        k = k % n;
        for (int step = 0; step < k; step++) {
            ListNode cur = head;
            while (cur.next.next != null) cur = cur.next;
            ListNode last = cur.next;
            cur.next = null;
            last.next = head;
            head = last;
        }
        return head;
    }

    // KEY INSIGHT: joining the list into a temporary circle turns "find
    // where to cut for a right rotation by k" into a single arithmetic
    // formula (n - k - 1), avoiding repeated single-step rotations.

    // Level 2 -- Optimal: form a cycle, cut at the computed boundary.
    // O(n) time, O(1) space.
    public static ListNode rotateRight(ListNode head, int k) {
        if (head == null || head.next == null) return head;

        int n = 1;
        ListNode tail = head;
        while (tail.next != null) { tail = tail.next; n++; }

        k = k % n;
        if (k == 0) return head;

        tail.next = head; // form the cycle
        ListNode newTail = head;
        for (int i = 0; i < n - k - 1; i++) newTail = newTail.next;

        ListNode newHead = newTail.next;
        newTail.next = null; // break the cycle
        return newHead;
    }

    // Level 3 -- Hardened: k larger than the list length (handled by
    // k % n), and k == 0 or a multiple of n (no-op rotation).
    static ListNode hardened(ListNode head, int k) {
        return rotateRight(head, k);
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
        print(bruteForce(build(1, 2, 3, 4, 5), 2));
        print(rotateRight(build(1, 2, 3, 4, 5), 2));

        System.out.print("k larger than n: "); print(hardened(build(1, 2, 3), 7));
        System.out.print("k is multiple of n: "); print(hardened(build(1, 2, 3), 3));
    }
}
```

How to run: save as `RotateList.java`, then run `java RotateList.java`.

## 6. Walkthrough

Dry run of `rotateRight({1,2,3,4,5}, 2)`:

1. Walk to tail: `n = 5`, `tail = node 5`.
2. `k = 2 % 5 = 2` (no reduction needed here).
3. `tail.next = head` forms the cycle: `5 -> 1`.
4. Walk `n - k - 1 = 5 - 2 - 1 = 2` steps from `head`: `1 -> 2 -> 3`, so `newTail = node 3`.
5. `newHead = newTail.next = 4`. Break the cycle: `newTail.next = null` (`3.next = null`).
6. Return `newHead = 4`. Final list: `4 -> 5 -> 1 -> 2 -> 3`, matching the expected rotation.

Time complexity: O(n) — one pass to find length, one to find the new tail. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: forgetting `k = k % n` before using `k` in the "steps to walk" formula can make `n - k - 1` negative when `k > n`, causing an infinite loop or a negative-count `for` loop that silently does nothing.

- Forming a temporary cycle and cutting it at a computed offset is a reusable trick for "rotate" and "reorder" linked list problems beyond just this one.
- Related problems: Split Linked List in Parts (also needs precise length-based boundary computation), Swap Nodes in Pairs (a different kind of local rearrangement).
