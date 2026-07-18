---
card: leetcode-patterns
gi: 102
slug: odd-even-linked-list
title: Odd Even Linked List
---

## 1. What it is

Given the `head` of a linked list, group all nodes at odd positions together, followed by all nodes at even positions, and return the reordered list. Positions are 1-indexed, and the relative order inside each group must be preserved. Example: `head = [1,2,3,4,5]` → `[1,3,5,2,4]`.

## 2. Why & when

This problem uses the same in-place pointer-relinking skill as the rest of the section, but instead of reversing, it splits the list into two interleaved sub-lists (odd-position and even-position nodes) and then joins them end to end — all without extra memory.

## 3. Core concept

**Key idea:** maintain two separate chains as you walk the list once — one collecting odd-position nodes, one collecting even-position nodes. At the end, attach the even chain after the tail of the odd chain.

**Steps:**
1. If the list is empty or has fewer than 3 nodes, return it unchanged (nothing to reorder).
2. Set `odd = head`, `even = head.next`, `evenHead = even` (remember where the even chain starts).
3. While `even != null && even.next != null`:
   - `odd.next = even.next`; advance `odd = odd.next`.
   - `even.next = odd.next`; advance `even = even.next`.
4. After the loop, `odd.next = evenHead` joins the two chains.
5. Return `head`.

**Why it is correct:** each step of the loop advances both `odd` and `even` by exactly one node, re-linking each to skip over the node belonging to the other group — so the odd chain and even chain are each built up correctly and in their original relative order. Joining the odd chain's tail to the even chain's head at the end produces exactly the required "all odd, then all even" arrangement.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Splitting a list into odd and even position chains then joining them">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">head = [1,2,3,4,5] (positions 1,2,3,4,5)</text>
    <circle cx="60" cy="60" r="18" fill="#161b22" stroke="#79c0ff"/><text x="60" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="140" cy="60" r="18" fill="#161b22" stroke="#f0883e"/><text x="140" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <circle cx="220" cy="60" r="18" fill="#161b22" stroke="#79c0ff"/><text x="220" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <circle cx="300" cy="60" r="18" fill="#161b22" stroke="#f0883e"/><text x="300" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <circle cx="380" cy="60" r="18" fill="#161b22" stroke="#79c0ff"/><text x="380" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">5</text>
    <text x="20" y="110" fill="#79c0ff">odd chain: 1 -&gt; 3 -&gt; 5</text>
    <text x="20" y="135" fill="#f0883e">even chain: 2 -&gt; 4</text>
    <text x="20" y="165" fill="#3fb950">joined: 1 -&gt; 3 -&gt; 5 -&gt; 2 -&gt; 4</text>
  </g>
</svg>

While scanning once, alternating nodes are peeled off into two separate chains, which are then joined tail-to-head at the very end.

## 5. Runnable example

```java
// OddEvenLinkedList.java
public class OddEvenLinkedList {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: copy values into two separate lists by
    // position parity, then rebuild. O(n) time, O(n) space -- wastes
    // memory an in-place relink does not need.
    static ListNode bruteForce(ListNode head) {
        java.util.List<Integer> odds = new java.util.ArrayList<>();
        java.util.List<Integer> evens = new java.util.ArrayList<>();
        int pos = 1;
        for (ListNode cur = head; cur != null; cur = cur.next, pos++) {
            if (pos % 2 == 1) odds.add(cur.val); else evens.add(cur.val);
        }
        odds.addAll(evens);
        ListNode dummy = new ListNode(0), cur = dummy;
        for (int v : odds) { cur.next = new ListNode(v); cur = cur.next; }
        return dummy.next;
    }

    // KEY INSIGHT: walking the list once while maintaining two separate
    // "next" chains (odd positions, even positions) and joining them at
    // the end reorders the list without ever leaving the original nodes.

    // Level 2 -- Optimal: two interleaved chains, joined at the end.
    // O(n) time, O(1) extra space.
    public static ListNode oddEvenList(ListNode head) {
        if (head == null || head.next == null) return head;

        ListNode odd = head, even = head.next, evenHead = even;
        while (even != null && even.next != null) {
            odd.next = even.next;
            odd = odd.next;
            even.next = odd.next;
            even = even.next;
        }
        odd.next = evenHead;
        return head;
    }

    // Level 3 -- Hardened: an empty list, a single-node list, and an
    // even-length list where the last node is at an even position.
    static ListNode hardened(ListNode head) {
        return oddEvenList(head);
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
        print(oddEvenList(build(1, 2, 3, 4, 5)));

        System.out.print("even length: "); print(hardened(build(1, 2, 3, 4)));
        System.out.print("empty: "); print(hardened(null));
    }
}
```

How to run: save as `OddEvenLinkedList.java`, then run `java OddEvenLinkedList.java`.

## 6. Walkthrough

Dry run of `oddEvenList({1,2,3,4,5})`:

1. `odd = 1`, `even = 2`, `evenHead = 2`.
2. Iteration 1: `odd.next = even.next (3)` → `odd = 3`. `even.next = odd.next (4)` → `even = 4`.
3. Iteration 2: `even (4) != null` and `even.next (5) != null`, continue. `odd.next = even.next (5)` → `odd = 5`. `even.next = odd.next (null)` → `even = null`.
4. `even == null`, loop ends. `odd.next = evenHead` → `5.next = 2`.

Final list: `1 -> 3 -> 5 -> 2 -> 4`, matching the expected reorder. Time complexity: O(n), one pass. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: forgetting to save `evenHead = even` before the loop starts loses the entry point to the even chain, since `even` itself gets reassigned repeatedly as the loop advances — without the saved reference, there is no way to reattach it at the end.

- The loop condition `even != null && even.next != null` correctly stops one step early, since `odd.next = even.next` inside the loop would otherwise dereference a null `even.next` on the final iteration.
- Related problems: Reverse Linked List (a different kind of single-pass in-place restructuring), Partition List (also splits into two chains based on a condition, then joins them).
