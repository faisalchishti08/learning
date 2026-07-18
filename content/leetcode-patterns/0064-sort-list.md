---
card: leetcode-patterns
gi: 64
slug: sort-list
title: Sort List
---

## 1. What it is

Given the `head` of a singly linked list, sort it in ascending order and return the sorted list. Example: `head = [4,2,1,3]` → return `[1,2,3,4]`. The typical follow-up asks for O(n log n) time and O(1) extra space (ignoring recursion stack).

## 2. Why & when

Copying every value into an array, sorting the array, then rebuilding the list works but costs O(n) extra space. Merge sort achieves O(n log n) time without that array copy, but merge sort needs to repeatedly split a list in half — and finding the middle of a linked list in O(1) space is exactly the Fast & Slow Pointers signal from earlier in this section.

## 3. Core concept

**Key idea:** merge sort a linked list the same way you would merge sort an array — split in half, sort each half recursively, then merge the two sorted halves — but use fast & slow pointers to find the splitting point, since a linked list has no random-access index to bisect.

**Steps:**
1. Base case: if the list has 0 or 1 nodes, it is already sorted.
2. Use fast & slow pointers to find the middle node and split the list into two halves.
3. Recursively sort each half.
4. Merge the two sorted halves into one sorted list (the same merge step used in Merge Two Sorted Lists).

**Why it is correct:** merge sort's correctness does not depend on the data structure — splitting into two halves, sorting each independently, then merging preserves order for arrays and linked lists alike. Fast & slow pointers is simply the linked-list-native way to perform the split step, replacing the array's `mid = (lo + hi) / 2` index arithmetic.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Merge sort on a linked list using fast and slow pointers to split">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">head = [4, 2, 1, 3]</text>
    <text x="20" y="45" fill="#8b949e">split via fast/slow: [4, 2] and [1, 3]</text>
    <text x="20" y="70" fill="#8b949e">recursively split and sort each half: [2, 4] and [1, 3]</text>
    <rect x="20" y="90" width="36" height="28" fill="#161b22" stroke="#79c0ff"/><text x="38" y="109" fill="#e6edf3" text-anchor="middle">2</text>
    <rect x="66" y="90" width="36" height="28" fill="#161b22" stroke="#79c0ff"/><text x="84" y="109" fill="#e6edf3" text-anchor="middle">4</text>
    <text x="115" y="109" fill="#8b949e">merge with</text>
    <rect x="185" y="90" width="36" height="28" fill="#161b22" stroke="#f0883e"/><text x="203" y="109" fill="#e6edf3" text-anchor="middle">1</text>
    <rect x="231" y="90" width="36" height="28" fill="#161b22" stroke="#f0883e"/><text x="249" y="109" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="20" y="150" fill="#8b949e">merged result: [1, 2, 3, 4]</text>
  </g>
</svg>

Each recursive split finds its midpoint with fast & slow pointers, and the merge step at each level combines two already-sorted halves — the same shape as array merge sort, adapted to pointer-based lists.

## 5. Runnable example

```java
// SortList.java
public class SortList {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: copy values to an array, sort the array,
    // rebuild the list. O(n log n) time, O(n) space -- wastes memory on
    // an array copy the merge-sort approach does not need.
    static ListNode bruteForce(ListNode head) {
        java.util.List<Integer> vals = new java.util.ArrayList<>();
        for (ListNode cur = head; cur != null; cur = cur.next) vals.add(cur.val);
        java.util.Collections.sort(vals);
        ListNode dummy = new ListNode(0), cur = dummy;
        for (int v : vals) { cur.next = new ListNode(v); cur = cur.next; }
        return dummy.next;
    }

    // KEY INSIGHT: fast &amp; slow pointers gives merge sort a way to find
    // a linked list's midpoint in one pass, without random access --
    // making split-sort-merge work natively on pointer-based lists.

    // Level 2 -- Optimal: merge sort using fast &amp; slow pointers to
    // split. O(n log n) time, O(log n) space for recursion.
    public static ListNode sortList(ListNode head) {
        if (head == null || head.next == null) return head;

        ListNode slow = head, fast = head, prev = null;
        while (fast != null && fast.next != null) {
            prev = slow;
            slow = slow.next;
            fast = fast.next.next;
        }
        prev.next = null; // cut the list into two halves

        ListNode left = sortList(head);
        ListNode right = sortList(slow);
        return merge(left, right);
    }

    static ListNode merge(ListNode a, ListNode b) {
        ListNode dummy = new ListNode(0), cur = dummy;
        while (a != null && b != null) {
            if (a.val <= b.val) { cur.next = a; a = a.next; }
            else { cur.next = b; b = b.next; }
            cur = cur.next;
        }
        cur.next = (a != null) ? a : b;
        return dummy.next;
    }

    // Level 3 -- Hardened: lists with duplicate values (stability is
    // preserved because merge uses <= to prefer the left half on ties).
    static ListNode hardened(ListNode head) {
        return sortList(head);
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
        System.out.print("brute force: "); print(bruteForce(build(4, 2, 1, 3)));
        System.out.print("optimal:     "); print(sortList(build(4, 2, 1, 3)));
        System.out.print("duplicates:  "); print(hardened(build(3, 1, 3, 2, 1)));
    }
}
```

How to run: save as `SortList.java`, then run `java SortList.java`.

## 6. Walkthrough

Dry run of `sortList` on `[4, 2, 1, 3]`:

1. Fast & slow pointers split at the middle: `prev` stops at `2` (just before `slow`), so `prev.next = null` cuts the list into `[4, 2]` and `[1, 3]`.
2. Recursively sort `[4, 2]`: split into `[4]` and `[2]`, both base cases, then merge into `[2, 4]`.
3. Recursively sort `[1, 3]`: split into `[1]` and `[3]`, both base cases, then merge into `[1, 3]`.
4. Merge `[2, 4]` and `[1, 3]`: compare `2` vs `1` → take `1`; compare `2` vs `3` → take `2`; compare `4` vs `3` → take `3`; only `4` remains → append it. Result: `[1, 2, 3, 4]`.

Time complexity: O(n log n) — `log n` levels of splitting, each level doing O(n) work to merge. Space complexity: O(log n) for the recursion stack (the merge itself reuses existing nodes, no extra list allocation).

## 7. Gotchas & takeaways

> Gotcha: forgetting to set `prev.next = null` after finding the split point leaves the first half still linked to the second half, causing the recursive sort on the first half to silently include (and infinitely process, if it also loops back) nodes from the second half.

- This problem reuses two earlier building blocks: fast & slow pointers to split (from this section) and the merge step from Merge Two Sorted Lists.
- Related problems: Merge Two Sorted Lists (the merge step alone), Reorder List (same split-in-half step, different combination logic).
