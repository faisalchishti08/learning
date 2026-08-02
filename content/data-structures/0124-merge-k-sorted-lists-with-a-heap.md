---
card: data-structures
gi: 124
slug: merge-k-sorted-lists-with-a-heap
title: Merge K sorted lists with a heap
---

## 1. What it is

Given `k` linked lists, each already sorted, this problem merges them into a single fully sorted linked list. A min-heap of size `k` tracks "the current smallest unmerged head" across all `k` lists at once, letting you build the output one node at a time without ever comparing more than `k` candidates.

## 2. Why & when

Merging two sorted lists is a simple two-pointer walk. Merging `k` of them by repeatedly comparing all `k` current heads directly costs `O(k)` per output node, or `O(n*k)` overall for `n` total nodes — wasteful once `k` grows. A heap keeps "the current best among k candidates" accessible in `O(log k)`, dropping the total cost to `O(n log k)`. This exact pattern also underlies external sorting (merging sorted chunks too large to fit in memory) and merging results from `k` parallel data sources.

## 3. Core concept

**How the operation works.** Put the head node of every non-empty list into a min-heap, ordered by node value.

1. Poll the heap — this is the smallest value among all current list heads, so it belongs next in the output.
2. Append that node to the result list.
3. If the polled node has a `next`, offer that `next` into the heap (it is now that list's new current head).
4. Repeat until the heap is empty.

**The invariant it must preserve.** At every point, the heap holds exactly one candidate per still-nonempty list — the smallest unconsumed node from each. Because a min-heap's root is always the smallest of whatever it currently holds, polling always yields the correct next value for the merged output, across all `k` lists simultaneously.

**Why this beats pairwise merging.** Merging lists two at a time (merge list 1 and 2, then merge that with list 3, and so on) still visits most nodes `O(k)` times in the worst case, giving `O(n*k)` total. The heap approach only ever compares `k` "current heads" at once, and each comparison costs `O(log k)` instead of `O(k)` — the heap replaces a linear scan across `k` candidates with a logarithmic one.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three sorted lists with heads 1, 4, 2 all placed in a min heap; the smallest head 1 is polled and appended to the output, then its next node 5 is offered back in">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">list A: 1 -&gt; 5</text>
    <text x="20" y="34" fill="#8b949e">list B: 4 -&gt; 6</text>
    <text x="20" y="52" fill="#8b949e">list C: 2 -&gt; 8</text>
    <rect x="180" y="15" width="200" height="50" fill="#161b22" stroke="#79c0ff"/>
    <text x="280" y="35" fill="#e6edf3" text-anchor="middle" font-size="9">min-heap of current heads:</text>
    <text x="280" y="55" fill="#e6edf3" text-anchor="middle" font-size="9">{1(A), 4(B), 2(C)}</text>
    <text x="480" y="30" fill="#f0883e" font-size="9">poll() -&gt; 1 (smallest)</text>
    <text x="480" y="50" fill="#f0883e" font-size="9">append 1 to output</text>
    <text x="480" y="70" fill="#79c0ff" font-size="9">offer A's next (5) back in</text>
    <rect x="180" y="100" width="200" height="30" fill="#0d1117" stroke="#79c0ff"/>
    <text x="280" y="120" fill="#e6edf3" text-anchor="middle" font-size="9">heap now: {2(C), 4(B), 5(A)}</text>
    <text x="280" y="170" fill="#8b949e" text-anchor="middle" font-size="10">output so far: 1</text>
    <text x="280" y="195" fill="#8b949e" text-anchor="middle" font-size="9">next poll() will return 2 -- process repeats</text>
  </g>
</svg>

The heap always holds exactly one node per still-active list. Polling the smallest, appending it to the output, then offering that list's next node back in — repeating this drains all `k` lists into one sorted result.

## 5. Runnable example

```java
// MergeKSortedLists.java
import java.util.PriorityQueue;
import java.util.Comparator;

public class MergeKSortedLists {

    static class ListNode {
        int value;
        ListNode next;
        ListNode(int value) { this.value = value; }
    }

    static ListNode buildList(int... values) {
        ListNode dummy = new ListNode(0), tail = dummy;
        for (int v : values) { tail.next = new ListNode(v); tail = tail.next; }
        return dummy.next;
    }

    static String printList(ListNode head) {
        StringBuilder out = new StringBuilder();
        while (head != null) { out.append(head.value).append(" "); head = head.next; }
        return out.toString().trim();
    }

    // Basic: merge just two sorted lists, using a min-heap of size 2 -- the simplest case of the general pattern.
    static ListNode mergeK(ListNode[] lists) {
        PriorityQueue<ListNode> minHeap = new PriorityQueue<>(Comparator.comparingInt(n -> n.value));
        for (ListNode head : lists) if (head != null) minHeap.offer(head); // seed with each list's current head

        ListNode dummy = new ListNode(0), tail = dummy;
        while (!minHeap.isEmpty()) {
            ListNode smallest = minHeap.poll();      // the smallest current head across ALL lists
            tail.next = smallest;
            tail = tail.next;
            if (smallest.next != null) minHeap.offer(smallest.next); // that list's new current head
        }
        return dummy.next;
    }

    static void basicLevel() {
        ListNode[] lists = { buildList(1, 5), buildList(2, 6) };
        System.out.println("basic: merge([1,5], [2,6]) -> " + printList(mergeK(lists)));
    }

    // Intermediate: the full k=3 case, matching the diagram.
    static void intermediateLevel() {
        ListNode[] lists = { buildList(1, 5), buildList(4, 6), buildList(2, 8) };
        System.out.println("intermediate: merge([1,5], [4,6], [2,8]) -> " + printList(mergeK(lists)));
    }

    // Advanced: uneven list lengths, including an empty list, confirming the pattern handles both edge cases.
    static void advancedLevel() {
        ListNode[] lists = { buildList(3), null, buildList(1, 2, 9, 20), buildList() };
        System.out.println("advanced: merge([3], [], [1,2,9,20], []) -> " + printList(mergeK(lists)));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `MergeKSortedLists.java`, then run `java MergeKSortedLists.java`.

## 6. Walkthrough

1. `basicLevel()` seeds the heap with heads `1` and `2` from the two lists. Polling returns `1` (list A's head), appends it to the output, and offers `A`'s next node (`5`) back in. The heap now holds `{2, 5}`. Polling again returns `2` (list B's head), offers `6` back in, and so on — the merged result comes out `1 2 5 6`.
2. `intermediateLevel()` runs the exact three-list scenario from the diagram. The heap starts as `{1(A), 4(B), 2(C)}`. It polls `1`, offers `5` back in (heap: `{2, 4, 5}`), polls `2`, offers `8` back in (heap: `{4, 5, 8}`), and continues, ultimately producing `1 2 4 5 6 8`.
3. `advancedLevel()` includes `null` (an empty list) and a single-node list among the inputs. `mergeK` only seeds the heap with non-null heads, so the empty lists contribute nothing and are silently skipped — no special-case code is needed beyond the initial `if (head != null)` check, since a list that runs out simply never gets its `next` offered back in.

## 7. Gotchas & takeaways

> Gotcha: forgetting to offer a polled node's `next` back into the heap silently drops the rest of that list from the output — every poll must be paired with checking (and re-offering) the same list's next node, or the merge will terminate early with some lists only partially consumed.

- The heap always holds at most one node per still-active list — never more, never fewer — so `k` bounds the heap's size regardless of how long the individual lists are.
- Total cost is `O(n log k)` for `n` total nodes across `k` lists, compared to `O(n*k)` for naive pairwise merging.
- `null` (empty) input lists need no special-case handling — they simply never contribute a head to the initial seeding.
- Related concepts: [Top-K elements with a heap](0123-top-k-elements-with-a-heap.md), [PriorityQueue with a Comparator](0122-priorityqueue-with-a-comparator.md).
