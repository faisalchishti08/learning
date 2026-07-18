---
card: leetcode-patterns
gi: 105
slug: partition-list
title: Partition List
---

## 1. What it is

Given the `head` of a linked list and a value `x`, partition the list so that all nodes with values less than `x` come before all nodes with values greater than or equal to `x`. The original relative order of the nodes in each partition must be preserved. Example: `head = [1,4,3,2,5,2]`, `x = 3` → `[1,2,2,4,3,5]`.

## 2. Why & when

This is the linked-list version of the same idea used in Odd Even Linked List: build two separate chains while scanning once, then join them at the end. Here the split condition is a value comparison (`< x` versus `>= x`) instead of position parity, but the mechanics — collect into two chains, join at the end — are identical.

## 3. Core concept

**Key idea:** walk through the list once, appending each node to one of two chains depending on whether its value is less than `x` or not. At the end, join the "less than" chain's tail to the "greater than or equal" chain's head.

**Steps:**
1. Create two dummy heads, `lessDummy` and `greaterDummy`, with tail pointers `lessTail = lessDummy`, `greaterTail = greaterDummy`.
2. Walk through the original list with `curr`:
   - If `curr.val < x`, append it to the less chain: `lessTail.next = curr`, `lessTail = curr`.
   - Otherwise, append it to the greater chain: `greaterTail.next = curr`, `greaterTail = curr`.
3. After the scan, terminate the greater chain: `greaterTail.next = null`.
4. Join the chains: `lessTail.next = greaterDummy.next`.
5. Return `lessDummy.next`.

**Why it is correct:** since every node is appended to exactly one of the two chains in its original relative order (the scan never reorders within a chain), each chain preserves the required relative ordering on its own. Joining the "less than" chain's tail directly to the "greater than or equal" chain's head produces the required overall partition with both orderings preserved.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Partitioning a list into two chains by value, then joining them">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">head = [1,4,3,2,5,2], x = 3</text>
    <circle cx="60" cy="60" r="18" fill="#161b22" stroke="#3fb950"/><text x="60" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="140" cy="60" r="18" fill="#161b22" stroke="#f0883e"/><text x="140" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">4</text>
    <circle cx="220" cy="60" r="18" fill="#161b22" stroke="#f0883e"/><text x="220" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <circle cx="300" cy="60" r="18" fill="#161b22" stroke="#3fb950"/><text x="300" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <circle cx="380" cy="60" r="18" fill="#161b22" stroke="#f0883e"/><text x="380" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">5</text>
    <circle cx="460" cy="60" r="18" fill="#161b22" stroke="#3fb950"/><text x="460" y="65" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <text x="20" y="110" fill="#3fb950">less chain (&lt;3): 1 -&gt; 2 -&gt; 2</text>
    <text x="20" y="135" fill="#f0883e">greater/equal chain (&gt;=3): 4 -&gt; 3 -&gt; 5</text>
    <text x="20" y="160" fill="#8b949e">joined result: 1 -&gt; 2 -&gt; 2 -&gt; 4 -&gt; 3 -&gt; 5</text>
  </g>
</svg>

Each node joins one of two chains based on its value versus `x`, preserving its original relative order within that chain; joining the two chains end to end produces the final partition.

## 5. Runnable example

```java
// PartitionList.java
public class PartitionList {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: copy values into two separate lists by
    // comparison to x, then rebuild. O(n) time, O(n) space -- wastes
    // memory an in-place two-chain relink does not need.
    static ListNode bruteForce(ListNode head, int x) {
        java.util.List<Integer> less = new java.util.ArrayList<>();
        java.util.List<Integer> greaterOrEqual = new java.util.ArrayList<>();
        for (ListNode cur = head; cur != null; cur = cur.next) {
            if (cur.val < x) less.add(cur.val); else greaterOrEqual.add(cur.val);
        }
        less.addAll(greaterOrEqual);
        ListNode dummy = new ListNode(0), cur = dummy;
        for (int v : less) { cur.next = new ListNode(v); cur = cur.next; }
        return dummy.next;
    }

    // KEY INSIGHT: building two separate chains while scanning once, each
    // preserving its own nodes' original relative order, then joining
    // them end to end reproduces the required partition without extra
    // memory or reordering within a group.

    // Level 2 -- Optimal: two dummy-headed chains, joined at the end.
    // O(n) time, O(1) extra space.
    public static ListNode partition(ListNode head, int x) {
        ListNode lessDummy = new ListNode(0), greaterDummy = new ListNode(0);
        ListNode lessTail = lessDummy, greaterTail = greaterDummy;

        for (ListNode curr = head; curr != null; curr = curr.next) {
            if (curr.val < x) {
                lessTail.next = curr;
                lessTail = curr;
            } else {
                greaterTail.next = curr;
                greaterTail = curr;
            }
        }
        greaterTail.next = null;
        lessTail.next = greaterDummy.next;
        return lessDummy.next;
    }

    // Level 3 -- Hardened: every node belongs to the same partition
    // (all less than x, or all greater/equal), where one chain ends up
    // entirely empty.
    static ListNode hardened(ListNode head, int x) {
        return partition(head, x);
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
        print(bruteForce(build(1, 4, 3, 2, 5, 2), 3));
        print(partition(build(1, 4, 3, 2, 5, 2), 3));

        System.out.print("all less than x: "); print(hardened(build(1, 2), 5));
    }
}
```

How to run: save as `PartitionList.java`, then run `java PartitionList.java`.

## 6. Walkthrough

Dry run of `partition({1,4,3,2,5,2}, 3)`:

| curr.val | < 3? | chain | less chain so far | greater chain so far |
|---|---|---|---|---|
| 1 | yes | less | 1 | — |
| 4 | no | greater | 1 | 4 |
| 3 | no | greater | 1 | 4,3 |
| 2 | yes | less | 1,2 | 4,3 |
| 5 | no | greater | 1,2 | 4,3,5 |
| 2 | yes | less | 1,2,2 | 4,3,5 |

Join: `greaterTail.next = null` terminates `4,3,5`. `lessTail.next = greaterDummy.next` joins `1,2,2` to `4,3,5`. Return `lessDummy.next = 1`. Final list: `1 -> 2 -> 2 -> 4 -> 3 -> 5`. Time complexity: O(n), one pass. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: forgetting `greaterTail.next = null` before joining the chains can leave a stray reference to whatever node originally followed the last "greater or equal" node in the source list, creating a cycle or a corrupted tail once the two chains are joined.

- This problem and Odd Even Linked List share the exact same "two chains, join at the end" mechanics — only the split condition differs (value comparison versus position parity).
- Related problems: Odd Even Linked List (position-based splitting), Sort Array By Parity (the array analog of this same partitioning idea).
