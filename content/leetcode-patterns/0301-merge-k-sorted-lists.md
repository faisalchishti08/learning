---
card: leetcode-patterns
gi: 301
slug: merge-k-sorted-lists
title: Merge k Sorted Lists
---

## 1. What it is

Given an array of `k` linked lists, each sorted ascending, merge them into a single sorted linked list and return its head. Example: `lists = [[1,4,5],[1,3,4],[2,6]]` → `[1,1,2,3,4,4,5,6]`.

## 2. Why & when

This is the canonical, textbook K-way Merge problem: `k` explicit sorted sequences, combined with a min-heap holding one node per list. Use this shape whenever the problem literally hands you an array of already-sorted sequences to combine — no derivation of implicit sequences needed, unlike Find K Pairs with Smallest Sums or Ugly Number II.

## 3. Core concept

**Key idea:** put the head node of every non-empty list into a min-heap ordered by node value. Repeatedly pop the smallest node, attach it to the result, and push that node's `next` (if any) back into the heap.

**Steps:**
1. Create a min-heap of `ListNode`, comparing by `.val`.
2. Push the head of every list in `lists` that is non-null.
3. Use a `dummy` head and a `tail` pointer for building the result.
4. While the heap is non-empty: pop the smallest node; attach it to `tail.next`; advance `tail`; if the popped node has a `next`, push it.
5. Return `dummy.next`.

**Why it is correct:** each list is individually sorted, so a list's un-popped nodes are always at least as large as its current head — exactly the K-way Merge invariant. Popping the heap's minimum repeatedly, and always replacing a popped node with its own successor, produces every node from every list exactly once, in fully sorted order.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Min-heap merging three sorted linked lists by repeatedly popping the smallest head node and pushing its successor">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">lists: [1,4,5], [1,3,4], [2,6]</text>
    <text x="10" y="45">seed heap: heads 1, 1, 2</text>
    <text x="10" y="65">pop 1 (list A) -&gt; result [1] -&gt; push list A's next (4)</text>
    <text x="10" y="85">pop 1 (list B) -&gt; result [1,1] -&gt; push list B's next (3)</text>
    <text x="10" y="105">pop 2 (list C) -&gt; result [1,1,2] -&gt; push list C's next (6)</text>
    <rect x="10" y="120" width="220" height="24" fill="#3fb950"/><text x="120" y="137" fill="#0d1117" text-anchor="middle" font-size="10">merged so far: 1, 1, 2, ...</text>
  </g>
</svg>

Each pop is immediately followed by pushing that same list's next node, keeping the heap seeded with one candidate per unfinished list.

## 5. Runnable example

```java
// MergeKSortedLists.java
import java.util.PriorityQueue;

public class MergeKSortedLists {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: repeatedly call Merge Two Sorted Lists
    // on pairs of lists until only one remains. Correct, O(kn) if
    // done naively one list at a time, or O(n log k) if merged in
    // pairs (divide and conquer) -- the heap approach below is
    // simpler to reason about directly.

    // KEY INSIGHT: a min-heap holding one head node per list always
    // surfaces the true next-smallest node across all k lists,
    // without ever comparing more than k nodes at once.

    // Level 2 -- Optimal: k-way merge via min-heap, O(n log k).
    static ListNode mergeKLists(ListNode[] lists) {
        PriorityQueue<ListNode> heap = new PriorityQueue<>((a, b) -> a.val - b.val);
        for (ListNode node : lists) {
            if (node != null) heap.offer(node);
        }

        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;
        while (!heap.isEmpty()) {
            ListNode smallest = heap.poll();
            tail.next = smallest;
            tail = tail.next;
            if (smallest.next != null) heap.offer(smallest.next);
        }
        return dummy.next;
    }

    // Level 3 -- Hardened: works when lists is empty (heap starts
    // empty, loop never runs, returns null) and when some lists are
    // null or empty (skipped during the initial seeding).

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
        ListNode[] lists = {build(1, 4, 5), build(1, 3, 4), build(2, 6)};
        print(mergeKLists(lists));
        // 1 1 2 3 4 4 5 6
    }
}
```

**How to run:** `java MergeKSortedLists.java`

## 6. Walkthrough

Trace merging `[[1,4,5],[1,3,4],[2,6]]`:

| pop | popped value | pushed next | result so far |
|---|---|---|---|
| 1 | 1 (list A) | 4 | 1 |
| 2 | 1 (list B) | 3 | 1, 1 |
| 3 | 2 (list C) | 6 | 1, 1, 2 |
| 4 | 3 (list B) | 4 | 1, 1, 2, 3 |
| 5 | 4 (list A) | 5 | 1, 1, 2, 3, 4 |
| 6 | 4 (list B) | (list B exhausted) | 1, 1, 2, 3, 4, 4 |
| 7 | 5 (list A) | (list A exhausted) | 1, 1, 2, 3, 4, 4, 5 |
| 8 | 6 (list C) | (list C exhausted) | 1, 1, 2, 3, 4, 4, 5, 6 |

Final merged list: `1, 1, 2, 3, 4, 4, 5, 6`. Time complexity is O(n log k): `n` total nodes across all lists, each pop-and-push costing O(log k), since the heap never exceeds `k` entries. Space is O(k) for the heap, plus O(1) extra for relinking nodes (the result reuses existing nodes).

## 7. Gotchas & takeaways

> Gotcha: a naive sequential merge — merging list 1 with list 2, then that result with list 3, and so on — costs O(nk) in the worst case (each merge touches the growing result), far worse than the heap's O(n log k); prefer the heap or a divide-and-conquer pairwise merge for large `k`.

- This is the reference-implementation problem for the entire K-way Merge pattern — its structure (heap of nodes, pop-and-replace-with-successor) generalizes directly to Kth Smallest Element in a Sorted Matrix and Smallest Range Covering Elements from K Lists.
- A divide-and-conquer approach (repeatedly merge pairs of lists using Merge Two Sorted Lists) also reaches O(n log k), trading the heap for recursive pairwise merges.
- Related problems: Merge Two Sorted Lists (the `k=2` base case), Kth Smallest Element in a Sorted Matrix (the same heap idea, applied to matrix rows).
