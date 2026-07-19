---
card: leetcode-patterns
gi: 106
slug: reverse-nodes-in-k-group
title: Reverse Nodes in k-Group
---

## 1. What it is

Given the `head` of a linked list and an integer `k`, reverse the nodes of the list `k` at a time, and return the new head. If the number of nodes left at the end is less than `k`, leave that final group as it is, unreversed. Example: `head = [1,2,3,4,5]`, `k = 2` → `[2,1,4,3,5]` (the last node, `5`, has no partner and stays untouched).

## 2. Why & when

This problem generalizes both Reverse Linked List II (reverse one fixed segment) and Swap Nodes in Pairs (reverse fixed groups of size `2`). Recognize it whenever a problem asks you to reverse the list in fixed-size chunks: check each chunk has exactly `k` nodes before reversing it, reverse it with the standard three-pointer technique, then reconnect it to the previous chunk and recurse or loop on the rest.

## 3. Core concept

**Key idea:** process the list one group of `k` nodes at a time. For each group, first check it actually has `k` nodes (count ahead). If it does, reverse just that group in place using the standard `prev/curr/next` pointer walk, then reconnect the reversed group's head and tail to the surrounding list. If it does not have `k` nodes, stop and leave it as is.

**Steps:**
1. Create `dummy.next = head`; set `groupPrev = dummy`.
2. Loop:
   - From `groupPrev.next`, walk forward `k` nodes to find `groupNext` (the node right after this group). If fewer than `k` nodes remain, stop the loop.
   - Reverse the `k` nodes between `groupPrev.next` and `groupNext` (exclusive), using three pointers `prev = groupNext`, `curr = groupPrev.next`.
   - After reversing, the old `groupPrev.next` is now the tail of the reversed group. Save it as the new `groupPrev` for the next iteration, and link `groupPrev.next` to the reversed group's new head.
3. Return `dummy.next`.

**Why it is correct:** counting ahead before reversing guarantees a partial final group is never touched, matching the problem's rule. Seeding `prev = groupNext` (instead of `null`) during the in-group reversal automatically wires the reversed group's tail to whatever comes after it, so no extra reconnection step is needed there. `groupPrev` always points to the node just before the next group, so each iteration starts from a correct, already-linked list.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Reversing the list in fixed groups of k=2">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">head = [1, 2, 3, 4, 5], k = 2</text>
    <circle cx="40" cy="70" r="16" fill="#161b22" stroke="#30363d"/><text x="40" y="75" fill="#8b949e" text-anchor="middle" font-size="9">dummy</text>
    <circle cx="120" cy="70" r="18" fill="#161b22" stroke="#f0883e"/><text x="120" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="200" cy="70" r="18" fill="#161b22" stroke="#f0883e"/><text x="200" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <circle cx="280" cy="70" r="18" fill="#161b22" stroke="#79c0ff"/><text x="280" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <circle cx="360" cy="70" r="18" fill="#161b22" stroke="#79c0ff"/><text x="360" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <circle cx="440" cy="70" r="18" fill="#161b22" stroke="#8b949e"/><text x="440" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">5</text>
    <line x1="58" y1="70" x2="102" y2="70" stroke="#3fb950" marker-end="url(#n)"/>
    <line x1="138" y1="70" x2="182" y2="70" stroke="#3fb950" marker-end="url(#n)"/>
    <line x1="218" y1="70" x2="262" y2="70" stroke="#3fb950" marker-end="url(#n)"/>
    <line x1="298" y1="70" x2="342" y2="70" stroke="#3fb950" marker-end="url(#n)"/>
    <line x1="378" y1="70" x2="422" y2="70" stroke="#3fb950" marker-end="url(#n)"/>
    <defs><marker id="n" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#3fb950"/></marker></defs>
    <text x="20" y="120" fill="#8b949e">group [1,2] reverses to [2,1]; group [3,4] reverses to [4,3]; group [5] is short, so it stays as is</text>
    <text x="20" y="150" fill="#e6edf3">result: 2 -&gt; 1 -&gt; 4 -&gt; 3 -&gt; 5</text>
  </g>
</svg>

Each full group of `k` nodes reverses internally; the final short group (fewer than `k` nodes) is detected before reversal starts and is left untouched.

## 5. Runnable example

```java
// ReverseKGroup.java
public class ReverseKGroup {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: copy values into an array, reverse each
    // k-sized chunk in the array (skipping a short final chunk), rebuild
    // the list. O(n) time, O(n) space -- wastes memory an in-place
    // pointer reversal does not need.
    static ListNode bruteForce(ListNode head, int k) {
        java.util.List<Integer> vals = new java.util.ArrayList<>();
        for (ListNode cur = head; cur != null; cur = cur.next) vals.add(cur.val);

        for (int i = 0; i + k <= vals.size(); i += k) {
            int lo = i, hi = i + k - 1;
            while (lo < hi) {
                java.util.Collections.swap(vals, lo, hi);
                lo++; hi--;
            }
        }
        ListNode dummy = new ListNode(0), cur = dummy;
        for (int v : vals) { cur.next = new ListNode(v); cur = cur.next; }
        return dummy.next;
    }

    // KEY INSIGHT: count k nodes ahead BEFORE reversing so a short final
    // group is never touched, and seed the in-group reversal's `prev`
    // pointer with the node after the group -- that automatically wires
    // the reversed group's tail to the rest of the list.

    // Level 2 -- Optimal: reverse each full group in place, group by
    // group, reconnecting as we go. O(n) time, O(1) extra space.
    public static ListNode reverseKGroup(ListNode head, int k) {
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode groupPrev = dummy;

        while (true) {
            ListNode groupNext = groupPrev;
            for (int i = 0; i < k; i++) {
                groupNext = groupNext.next;
                if (groupNext == null) return dummy.next; // fewer than k left
            }
            groupNext = skipK(groupPrev.next, k); // node right after the group

            ListNode prev = groupNext;
            ListNode curr = groupPrev.next;
            for (int i = 0; i < k; i++) {
                ListNode nxt = curr.next;
                curr.next = prev;
                prev = curr;
                curr = nxt;
            }

            ListNode oldGroupHead = groupPrev.next; // now the tail of the reversed group
            groupPrev.next = prev;                  // link to the reversed group's new head
            groupPrev = oldGroupHead;
        }
    }

    private static ListNode skipK(ListNode node, int k) {
        for (int i = 0; i < k && node != null; i++) node = node.next;
        return node;
    }

    // Level 3 -- Hardened: k = 1 (no-op, list unchanged) and a list whose
    // length is an exact multiple of k (every group reverses, none left over).
    static ListNode hardened(ListNode head, int k) {
        return reverseKGroup(head, k);
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
        print(reverseKGroup(build(1, 2, 3, 4, 5), 2));

        System.out.print("k = 1: "); print(hardened(build(1, 2, 3), 1));
        System.out.print("exact multiple: "); print(hardened(build(1, 2, 3, 4, 5, 6), 3));
    }
}
```

How to run: save as `ReverseKGroup.java`, then run `java ReverseKGroup.java`.

## 6. Walkthrough

Dry run of `reverseKGroup({1, 2, 3, 4, 5}, k = 2)`:

1. `groupPrev = dummy`. Count ahead 2 nodes from `dummy.next`: reach `1`, then `2` — both exist, so `groupNext = 3`. Reverse `1 -> 2` with `prev` seeded at `3`: after the loop, `2.next = 1`, `1.next = 3`. `oldGroupHead = 1`. Set `dummy.next = 2` (the new group head). `groupPrev = 1`. List so far: `2 -> 1 -> 3 -> 4 -> 5`.
2. `groupPrev = 1`. Count ahead 2 nodes from `1.next (3)`: reach `3`, then `4` — both exist, so `groupNext = 5`. Reverse `3 -> 4` with `prev` seeded at `5`: `4.next = 3`, `3.next = 5`. `oldGroupHead = 3`. Set `1.next = 4`. `groupPrev = 3`. List so far: `2 -> 1 -> 4 -> 3 -> 5`.
3. `groupPrev = 3`. Count ahead from `3.next (5)`: only `5` exists, then `null` — fewer than `k` nodes remain, so return `dummy.next` immediately, without touching `5`.

Final list: `2 -> 1 -> 4 -> 3 -> 5`. Time complexity: O(n), since every node is visited a constant number of times (once to count, once to reverse). Space complexity: O(1) with the iterative version (a recursive version would use O(n / k) stack space).

## 7. Gotchas & takeaways

> Gotcha: reversing a group before confirming it has `k` nodes corrupts the list — if the last group is short, you must detect that in advance (by counting ahead) and leave it completely untouched, not partially reversed.

- Seeding the in-group reversal's `prev` pointer with `groupNext` (the node after the group), instead of `null`, is what automatically reconnects the reversed group's tail to the rest of the list — no separate "stitch the tail" step is needed.
- This is the general form of the segment-reversal template: Reverse Linked List II reverses one arbitrary segment; Swap Nodes in Pairs is this same problem with `k` fixed at `2`.
- Related problems: Swap Nodes in Pairs (this problem with `k = 2`), Reverse Linked List II (reverse one segment by position), Rotate List (a different way of rearranging a list in chunks).
