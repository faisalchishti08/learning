---
card: leetcode-patterns
gi: 53
slug: fast-slow-pointers-template-two-pointers-moving-at-different
title: Fast & Slow Pointers — template: two pointers moving at different speeds
---

## 1. What it is

This page gives the reusable code template for the fast & slow pointers pattern. It is the skeleton you adapt for cycle detection, finding a middle node, or detecting cycles in a value sequence such as Happy Number.

## 2. Why & when

Instead of re-deriving the two-pointer loop from scratch every time, use one template and change only the "what to check" or "what to return" part. The template's shape stays the same because the underlying movement rule — slow steps once, fast steps twice — never changes.

Use this template when a problem's signal matches the previous page: cycle detection, finding a middle element in one pass, or detecting a repeating state in an iterated function.

## 3. Core concept

**Key idea:** the template has three interchangeable parts — the starting positions, the loop condition that stops the fast pointer safely, and what you do when the pointers meet or when the loop ends.

**General steps:**
1. Initialize `slow` and `fast` to the same starting point (or `fast` one step ahead, depending on the variant).
2. Loop while `fast` can safely take two steps (`fast != null && fast.next != null` for a linked list, or an equivalent bounds check for an array/value sequence).
3. Advance `slow` by one step and `fast` by two steps.
4. Check the stopping condition (pointers equal → cycle found; loop ends naturally → answer is where `slow` stopped).

**Why it works:** the ratio of speeds (2:1) is what matters, not the absolute speed. As long as `fast` covers twice the distance of `slow` every iteration, `slow` always lands exactly at the midpoint when `fast` reaches the end, and the two pointers always meet inside any cycle.

## 4. Diagram

<svg viewBox="0 0 700 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Fast and slow pointer template loop">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="20" width="660" height="30" fill="#161b22" stroke="#30363d"/>
    <text x="30" y="40" fill="#e6edf3">while (fast != null &amp;&amp; fast.next != null) { slow = slow.next; fast = fast.next.next; }</text>
    <text x="20" y="80" fill="#79c0ff">iteration 1: slow moves +1, fast moves +2</text>
    <text x="20" y="105" fill="#79c0ff">iteration 2: slow moves +1, fast moves +2</text>
    <text x="20" y="130" fill="#8b949e">loop stops when fast hits the end (no cycle) or slow == fast (cycle found)</text>
  </g>
</svg>

One loop, one movement rule, and a swappable stopping condition — that reuse is what makes this a template rather than a one-off solution.

## 5. Runnable example

```java
// FastSlowPointersTemplate.java
public class FastSlowPointersTemplate {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // The reusable template: swap the body to detect a cycle, find the
    // middle, or return the meeting point for later use.
    static ListNode findMiddle(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
        }
        // slow now sits on the middle node (or the second of two middles
        // for an even-length list).
        return slow;
    }

    public static void main(String[] args) {
        ListNode head = new ListNode(1);
        head.next = new ListNode(2);
        head.next.next = new ListNode(3);
        head.next.next.next = new ListNode(4);
        head.next.next.next.next = new ListNode(5);

        ListNode middle = findMiddle(head);
        System.out.println("middle value: " + middle.val);
    }
}
```

How to run: save as `FastSlowPointersTemplate.java`, then run `java FastSlowPointersTemplate.java`.

## 6. Walkthrough

Trace `findMiddle` on the list `1 -> 2 -> 3 -> 4 -> 5`:

1. Start: `slow = 1`, `fast = 1`.
2. Iteration 1: `slow = 2`, `fast = 3`. `fast.next` (`4`) is not null, so continue.
3. Iteration 2: `slow = 3`, `fast = 5`. `fast.next` is null, so the loop stops.
4. `slow` sits on node `3`, the exact middle of a 5-node list.

## 7. Gotchas & takeaways

> Gotcha: for an even-length list, `slow` stops on the *second* of the two middle nodes (e.g. for `1,2,3,4`, `slow` lands on `3`, not `2`). Check the problem statement for which middle it expects.

- The same loop condition (`fast != null && fast.next != null`) is safe for both cycle detection and finding the middle — memorize this one guard instead of re-deriving it.
- Swap only the loop body and the return value; the loop shape itself never changes across problems in this pattern.
