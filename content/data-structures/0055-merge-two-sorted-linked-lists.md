---
card: data-structures
gi: 55
slug: merge-two-sorted-linked-lists
title: Merge two sorted linked lists
---

## 1. What it is

Merging two sorted linked lists combines them into a single sorted list, by repeatedly comparing the current front node of each list and attaching whichever is smaller to the result — the same core idea as the merge step of merge sort, but working directly on linked-list nodes instead of arrays, so no extra array copying is needed.

## 2. Why & when

This is a fundamental building block: it is the merge step of merge sort applied to linked lists, and it appears directly in problems like combining sorted event streams, merging k sorted lists (via repeated pairwise merging or a heap), and general list-combination tasks where both inputs are already ordered.

## 3. Core concept

**Compare fronts, attach the smaller, advance that list.** At each step, look at the current front of each list (call them `a` and `b`). Attach whichever has the smaller value to the result, and advance *that* list's pointer to its own next node. Repeat until one list is exhausted.

**Reusing existing nodes, not copying values.** The merge relinks the *existing* nodes from both input lists into a new order — it does not allocate new nodes with copied values. This makes the merge O(1) extra space (beyond the dummy node), since only pointers are rearranged.

**A leftover tail attaches directly.** Once one list is fully exhausted, the *entire remaining tail* of the other list can be attached in one step — since it is already sorted internally, and every one of its values is guaranteed to be `>=` everything already merged (because both original lists were sorted), no further comparison is needed.

**A sentinel dummy node avoids a head special case.** As covered in [Sentinel / dummy nodes](0048-sentinel-dummy-nodes.md), starting with a `dummy` node and a `tail` pointer means the first real node attached (from whichever list starts smaller) is handled by the exact same code path as every subsequent attachment — no separate "which list starts first" branch.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Merging list a (1,3,5) and list b (2,4,6) by comparing fronts and attaching the smaller each time" >
  <g font-family="sans-serif" font-size="11">
    <text x="120" y="16" fill="#8b949e" text-anchor="middle">a: 1 -&gt; 3 -&gt; 5</text>
    <text x="120" y="35" fill="#8b949e" text-anchor="middle">b: 2 -&gt; 4 -&gt; 6</text>

    <rect x="240" y="20" width="30" height="24" fill="#0d1117" stroke="#3fb950"/><text x="255" y="37" fill="#e6edf3" text-anchor="middle" font-size="9">1</text>
    <rect x="275" y="20" width="30" height="24" fill="#0d1117" stroke="#3fb950"/><text x="290" y="37" fill="#e6edf3" text-anchor="middle" font-size="9">2</text>
    <rect x="310" y="20" width="30" height="24" fill="#0d1117" stroke="#3fb950"/><text x="325" y="37" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <rect x="345" y="20" width="30" height="24" fill="#0d1117" stroke="#3fb950"/><text x="360" y="37" fill="#e6edf3" text-anchor="middle" font-size="9">4</text>
    <rect x="380" y="20" width="30" height="24" fill="#0d1117" stroke="#3fb950"/><text x="395" y="37" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>
    <rect x="415" y="20" width="30" height="24" fill="#0d1117" stroke="#3fb950"/><text x="430" y="37" fill="#e6edf3" text-anchor="middle" font-size="9">6</text>
    <text x="320" y="80" fill="#79c0ff" text-anchor="middle">merged: 1 -&gt; 2 -&gt; 3 -&gt; 4 -&gt; 5 -&gt; 6, built by comparing fronts each step</text>
  </g>
</svg>

At every step, the smaller of the two current fronts is attached to the result, and that list advances — building the merged order directly.

## 5. Runnable example

```java
// MergeTwoSortedLinkedLists.java
public class MergeTwoSortedLinkedLists {

    static class Node {
        int value;
        Node next;
        Node(int value) { this.value = value; }
    }

    // Basic: iterative merge using a dummy node and a tail pointer.
    static Node mergeIterative(Node a, Node b) {
        Node dummy = new Node(0);
        Node tail = dummy;
        while (a != null && b != null) {
            if (a.value <= b.value) { tail.next = a; a = a.next; }
            else { tail.next = b; b = b.next; }
            tail = tail.next;
        }
        tail.next = (a != null) ? a : b; // attach whichever list still has nodes left
        return dummy.next;
    }

    static void basicLevel() {
        Node a = buildList(1, 3, 5);
        Node b = buildList(2, 4, 6);
        Node merged = mergeIterative(a, b);
        printList("basic (iterative merge)", merged);
    }

    // Intermediate: recursive merge -- the smaller front recurses on merging the rest.
    static Node mergeRecursive(Node a, Node b) {
        if (a == null) return b; // base case: one list is exhausted
        if (b == null) return a;
        if (a.value <= b.value) {
            a.next = mergeRecursive(a.next, b); // a's front is smaller: it leads, rest is merged recursively
            return a;
        } else {
            b.next = mergeRecursive(a, b.next);
            return b;
        }
    }

    static void intermediateLevel() {
        Node a = buildList(1, 4, 7);
        Node b = buildList(2, 3, 8);
        Node merged = mergeRecursive(a, b);
        printList("intermediate (recursive merge)", merged);
    }

    // Advanced: merge k sorted lists by repeatedly merging pairs.
    static Node mergeKLists(Node[] lists) {
        if (lists.length == 0) return null;
        Node result = lists[0];
        for (int i = 1; i < lists.length; i++) {
            result = mergeIterative(result, lists[i]); // fold each additional list into the running merge
        }
        return result;
    }

    static void advancedLevel() {
        Node[] lists = {
            buildList(1, 5, 9),
            buildList(2, 6),
            buildList(3, 4, 7, 8)
        };
        Node merged = mergeKLists(lists);
        printList("advanced (merge k lists)", merged);
    }

    static Node buildList(int... values) {
        Node dummy = new Node(0), tail = dummy;
        for (int v : values) { tail.next = new Node(v); tail = tail.next; }
        return dummy.next;
    }

    static void printList(String label, Node head) {
        StringBuilder sb = new StringBuilder();
        for (Node c = head; c != null; c = c.next) sb.append(c.value).append(" -> ");
        System.out.println(label + " -> " + sb + "null");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `MergeTwoSortedLinkedLists.java`, then run `java MergeTwoSortedLinkedLists.java`.

## 6. Walkthrough

1. `basicLevel()`'s `mergeIterative` compares `a`'s front (`1`) and `b`'s front (`2`); `1 <= 2`, so `tail.next = a`, and `a` advances to `3`. The next comparison is `3` vs `2`; `2` is smaller, so `b` is attached and advances to `4` — this alternation continues, producing `1 -> 2 -> 3 -> 4 -> 5 -> 6`.
2. Once `a` becomes `null` (after `5` is attached), the loop exits, and `tail.next = b` attaches the remaining `6` directly, since it is already known to be `>=` everything merged so far.
3. `intermediateLevel()`'s `mergeRecursive` compares `1` (from `a`) and `2` (from `b`); `a`'s front is smaller, so `a.next` is reassigned to the result of recursively merging `a.next` (`4,7`) with `b` (`2,3,8`) — the recursion continues picking the smaller front at each level, and the base case returns the other list directly once one side is exhausted.
4. `advancedLevel()`'s `mergeKLists` folds three lists together by repeatedly calling `mergeIterative`: first merging list 0 and list 1, then merging that result with list 2 — producing the fully sorted `1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9`.

## 7. Gotchas & takeaways

> Gotcha: the leftover-tail shortcut (`tail.next = (a != null) ? a : b;`) only works correctly because each *input* list is already sorted internally — if either input list were unsorted, attaching its remaining tail wholesale (instead of continuing the element-by-element comparison) would produce an incorrectly ordered result.

- Merging two sorted lists compares current fronts and attaches the smaller, advancing that list, repeating until one is exhausted.
- The remaining tail of the non-exhausted list can be attached in one step, since it is already sorted and guaranteed no smaller than anything merged so far.
- A [sentinel dummy node](0048-sentinel-dummy-nodes.md) avoids a special case for which list contributes the very first merged node.
- Related concepts: [Sentinel / dummy nodes](0048-sentinel-dummy-nodes.md), [Detect intersection of two lists](0056-detect-intersection-of-two-lists.md).
