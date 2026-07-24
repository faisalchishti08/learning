---
card: leetcode-patterns
gi: 294
slug: k-way-merge-template-a-min-heap-holding-one-head-from-each-l
title: K-way Merge — template: a min-heap holding one head from each list
---

## 1. What it is

This page gives the reusable template for K-way Merge problems: a min-heap that always holds exactly one "current candidate" from each of the `k` sequences, repeatedly popping the smallest and advancing that sequence.

## 2. Why & when

Use this template whenever you must combine or rank across `k` already-sorted sequences. It generalizes cleanly whether the sequences are arrays, linked lists, or matrix rows, since the only thing that changes is how you "advance" a sequence after popping its head.

## 3. Core concept

**Template — k-way merge via min-heap.**
1. Create a min-heap. Each heap entry must carry enough information to know WHICH sequence a value came from and HOW to find that sequence's next element (an array index pair, or a linked-list node reference).
2. Seed the heap: push the first element of every non-empty sequence.
3. Loop while the heap is non-empty (or until you have popped the number of elements you need):
   - Poll the heap's minimum. This is the next value in sorted order.
   - Advance the sequence that value came from (move to the next array index, or `node.next` for a list), and if that sequence still has elements, push its new head.
4. Collect each popped value into your result, in the order popped.

Why it works: the heap only ever holds `k` candidates, so each poll-and-push pair costs O(log k), not O(log n). Since every sequence is internally sorted, the true global minimum at any point is always among the current `k` heads — nothing "hiding" deeper in a sequence can be smaller than that sequence's own current head.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Template loop: poll heap minimum, advance that sequence, push its next head, repeat">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">Loop body (repeats until heap empty or k values popped)</text>
    <rect x="10" y="35" width="140" height="30" fill="#161b22" stroke="#30363d"/><text x="80" y="54" fill="#e6edf3" text-anchor="middle" font-size="10">poll heap min</text>
    <text x="160" y="54">-&gt;</text>
    <rect x="180" y="35" width="150" height="30" fill="#161b22" stroke="#30363d"/><text x="255" y="54" fill="#e6edf3" text-anchor="middle" font-size="10">append to result</text>
    <text x="340" y="54">-&gt;</text>
    <rect x="360" y="35" width="110" height="30" fill="#161b22" stroke="#30363d"/><text x="415" y="54" fill="#e6edf3" text-anchor="middle" font-size="10">advance source</text>
    <path d="M415,65 L415,90 L80,90 L80,65" fill="none" stroke="#8b949e" marker-end="url(#m2)"/>
    <defs><marker id="m2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#8b949e"/></marker></defs>
    <text x="80" y="110">push new head if source has more</text>
  </g>
</svg>

The loop repeats: poll the smallest, record it, advance its source, and push the new head back in.

## 5. Runnable example

```java
// KWayMergeTemplate.java
import java.util.PriorityQueue;
import java.util.List;
import java.util.ArrayList;

public class KWayMergeTemplate {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Template applied to linked lists: heap entries are ListNode
    // references directly, since "advance" just means node.next.
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

    static ListNode build(int... vals) {
        ListNode dummy = new ListNode(0), cur = dummy;
        for (int v : vals) { cur.next = new ListNode(v); cur = cur.next; }
        return dummy.next;
    }

    static List<Integer> toList(ListNode head) {
        List<Integer> out = new ArrayList<>();
        for (ListNode cur = head; cur != null; cur = cur.next) out.add(cur.val);
        return out;
    }

    public static void main(String[] args) {
        ListNode[] lists = {build(1, 4, 7), build(2, 5, 8), build(3, 6, 9)};
        System.out.println(toList(mergeKLists(lists)));
        // [1, 2, 3, 4, 5, 6, 7, 8, 9]
    }
}
```

**How to run:** `java KWayMergeTemplate.java`

## 6. Walkthrough

1. Seed the heap with the head of each of the 3 lists: `[1, 2, 3]` (nodes, ordered by their `val`).
2. Poll `1`, append it to the output list, then push `1`'s next node (`4`). Heap now effectively holds `[2, 3, 4]`.
3. Poll `2`, append it, push `2`'s next node (`5`). Heap now holds `[3, 4, 5]`.
4. Continue this poll-append-push cycle until every node from every list has been appended and the heap is empty.
5. The final output list is `1, 2, 3, 4, 5, 6, 7, 8, 9`, fully merged and sorted, using only `k = 3` heap slots at any one time.

## 7. Gotchas & takeaways

> Gotcha: for linked-list inputs, pushing `smallest.next` (a node reference) directly into the heap is more direct than tracking array indices — but you must still check `smallest.next != null` first, since pushing a `null` node crashes the comparator the next time the heap compares it.

- The template is identical whether sequences are arrays (track index pairs) or linked lists (track node references) — only the "advance" step's mechanics change.
- Heap size never exceeds `k`, which is exactly why every operation costs O(log k) instead of O(log n).
- For a "kth smallest" variant, stop the loop after exactly `k` polls instead of running until the heap is empty.
