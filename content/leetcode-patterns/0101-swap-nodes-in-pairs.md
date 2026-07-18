---
card: leetcode-patterns
gi: 101
slug: swap-nodes-in-pairs
title: Swap Nodes in Pairs
---

## 1. What it is

Given the `head` of a linked list, swap every two adjacent nodes and return the head of the resulting list. You must do this by changing the nodes' links, not by changing the values inside the nodes. Example: `head = [1,2,3,4]` → `[2,1,4,3]`.

## 2. Why & when

This is a repeated application of the segment-reversal template with a fixed segment length of exactly `2` — swap the first two nodes, reconnect, then move on to the next pair, repeating until the list is exhausted. A dummy node before `head` avoids special-casing the very first swap.

## 3. Core concept

**Key idea:** process the list two nodes at a time. For each pair, unhook the first node, relink it after the second node, and reconnect the pair back into the surrounding list — then advance to the next pair.

**Steps:**
1. Create `dummy.next = head`; set `prev = dummy`.
2. While `prev.next != null` and `prev.next.next != null` (a full pair remains):
   - Let `first = prev.next`, `second = first.next`.
   - Swap: `first.next = second.next`; `second.next = first`; `prev.next = second`.
   - Advance `prev = first` (now the second node in the swapped pair, ready to link to the next pair).
3. Return `dummy.next`.

**Why it is correct:** each iteration performs exactly the segment-reversal template with a segment length of `2`, reconnecting the swapped pair to `prev` on one side and to the remainder of the list (`second.next`, preserved before the swap) on the other. Repeating this for every pair, advancing `prev` correctly each time, swaps the whole list without ever losing track of the remaining nodes.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Swapping adjacent pairs of nodes">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">head = [1, 2, 3, 4]</text>
    <circle cx="40" cy="70" r="16" fill="#161b22" stroke="#30363d"/><text x="40" y="75" fill="#8b949e" text-anchor="middle" font-size="9">dummy</text>
    <circle cx="120" cy="70" r="18" fill="#161b22" stroke="#f0883e"/><text x="120" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <circle cx="200" cy="70" r="18" fill="#161b22" stroke="#f0883e"/><text x="200" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="280" cy="70" r="18" fill="#161b22" stroke="#79c0ff"/><text x="280" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <circle cx="360" cy="70" r="18" fill="#161b22" stroke="#79c0ff"/><text x="360" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <line x1="58" y1="70" x2="102" y2="70" stroke="#3fb950" marker-end="url(#n)"/>
    <line x1="138" y1="70" x2="182" y2="70" stroke="#3fb950" marker-end="url(#n)"/>
    <line x1="218" y1="70" x2="262" y2="70" stroke="#3fb950" marker-end="url(#n)"/>
    <line x1="298" y1="70" x2="342" y2="70" stroke="#3fb950" marker-end="url(#n)"/>
    <defs><marker id="n" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#3fb950"/></marker></defs>
    <text x="20" y="130" fill="#8b949e">each pair swaps internally: (1,2)-&gt;(2,1), (3,4)-&gt;(4,3); prev reconnects each pair to the next</text>
  </g>
</svg>

Each pair swaps in place, and `prev` (starting at `dummy`, then advancing to the tail of each swapped pair) links every pair to the next in the correct order.

## 5. Runnable example

```java
// SwapNodesInPairs.java
public class SwapNodesInPairs {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: copy values into an array, swap adjacent
    // pairs in the array, rebuild the list. O(n) time, O(n) space --
    // wastes memory an in-place pair swap does not need.
    static ListNode bruteForce(ListNode head) {
        java.util.List<Integer> vals = new java.util.ArrayList<>();
        for (ListNode cur = head; cur != null; cur = cur.next) vals.add(cur.val);
        for (int i = 0; i + 1 < vals.size(); i += 2) {
            java.util.Collections.swap(vals, i, i + 1);
        }
        ListNode dummy = new ListNode(0), cur = dummy;
        for (int v : vals) { cur.next = new ListNode(v); cur = cur.next; }
        return dummy.next;
    }

    // KEY INSIGHT: swapping a pair is the segment-reversal template with
    // segment length exactly 2 -- repeat it pair by pair, advancing prev
    // to the new tail of each swapped pair before moving to the next.

    // Level 2 -- Optimal: dummy node, repeated pair swaps. O(n) time,
    // O(1) extra space.
    public static ListNode swapPairs(ListNode head) {
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode prev = dummy;

        while (prev.next != null && prev.next.next != null) {
            ListNode first = prev.next;
            ListNode second = first.next;

            first.next = second.next;
            second.next = first;
            prev.next = second;

            prev = first;
        }
        return dummy.next;
    }

    // Level 3 -- Hardened: an odd-length list, where the last unpaired
    // node must stay in place untouched.
    static ListNode hardened(ListNode head) {
        return swapPairs(head);
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
        print(bruteForce(build(1, 2, 3, 4)));
        print(swapPairs(build(1, 2, 3, 4)));

        System.out.print("odd length: "); print(hardened(build(1, 2, 3)));
    }
}
```

How to run: save as `SwapNodesInPairs.java`, then run `java SwapNodesInPairs.java`.

## 6. Walkthrough

Dry run of `swapPairs({1, 2, 3, 4})`:

1. `prev = dummy`. `first = 1`, `second = 2`. Swap: `1.next = 2.next (3)`; `2.next = 1`; `dummy.next = 2`. List so far: `2 -> 1 -> 3 -> 4`. `prev = 1`.
2. `prev.next (3)` and `prev.next.next (4)` both exist. `first = 3`, `second = 4`. Swap: `3.next = 4.next (null)`; `4.next = 3`; `1.next = 4`. List: `2 -> 1 -> 4 -> 3`. `prev = 3`.
3. `prev.next` is now `null` — loop ends.

Return `dummy.next = 2`. Final list: `2 -> 1 -> 4 -> 3`. Time complexity: O(n). Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: forgetting to advance `prev = first` after each pair swap (or advancing it incorrectly to `second`) breaks the link to the next pair, since `prev` must end up at the *tail* of the just-swapped pair, which is the original `first` node.

- This problem is a repeated, fixed-length-2 instance of the general segment-reversal template — recognizing the connection avoids re-deriving pointer logic from scratch.
- Related problems: Reverse Linked List II (variable-length segment reversal), Reverse Nodes in k-Group (a related problem generalizing this to arbitrary group size `k`).
