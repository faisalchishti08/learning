---
card: leetcode-patterns
gi: 296
slug: merge-two-sorted-lists
title: Merge Two Sorted Lists
---

## 1. What it is

Given the heads of two sorted linked lists `list1` and `list2`, merge them into one sorted list and return its head. Example: `list1 = [1,2,4]`, `list2 = [1,3,4]` → `[1,1,2,3,4,4]`.

## 2. Why & when

This is the `k = 2` base case of K-way Merge — the exact same "always take the smaller current head" idea, but simple enough to compare the two heads directly with a few `if` statements, with no heap needed at all. Use this shape whenever exactly two sorted sequences must be combined; once `k` grows past two, reach for a min-heap instead (see Merge k Sorted Lists).

## 3. Core concept

**Key idea:** walk both lists with two pointers. At each step, compare the two current heads, attach the smaller one to the result, and advance only that pointer.

**Steps:**
1. Create a `dummy` node to simplify building the result (avoids special-casing the very first node).
2. While both `list1` and `list2` have remaining nodes: compare their values; attach whichever is smaller to the result's tail; advance that list's pointer.
3. When one list is exhausted, attach the REMAINDER of the other list directly (it is already sorted, so no further comparison is needed).
4. Return `dummy.next`.

**Why it is correct:** at every step, the smaller of the two current heads is guaranteed to be the smallest value not yet placed in the result, since both lists are individually sorted — nothing further down either list can be smaller than that list's own current head. Once one list runs out, every remaining node in the other list is, by its own sortedness, already in the correct final order.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two-pointer merge comparing heads 1 and 1, then 2 and 1, attaching the smaller each time">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">list1 = [1,2,4], list2 = [1,3,4]</text>
    <text x="10" y="45">compare 1 vs 1 -&gt; take list1's 1 -&gt; result [1]</text>
    <text x="10" y="65">compare 2 vs 1 -&gt; take list2's 1 -&gt; result [1,1]</text>
    <text x="10" y="85">compare 2 vs 3 -&gt; take list1's 2 -&gt; result [1,1,2]</text>
    <text x="10" y="105">compare 4 vs 3 -&gt; take list2's 3 -&gt; result [1,1,2,3]</text>
    <text x="10" y="125">compare 4 vs 4 -&gt; take list1's 4, then list2 remainder [4]</text>
    <rect x="10" y="135" width="220" height="24" fill="#3fb950"/><text x="120" y="152" fill="#0d1117" text-anchor="middle" font-size="10">result = [1,1,2,3,4,4]</text>
  </g>
</svg>

Comparing the two current heads and always taking the smaller builds the merged list in one pass.

## 5. Runnable example

```java
// MergeTwoSortedLists.java
public class MergeTwoSortedLists {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: collect all values into an array, sort
    // it, rebuild the list. Correct, but O((n+m) log(n+m)), ignoring
    // that both inputs are already sorted.

    // KEY INSIGHT: since both lists are sorted, the next value in the
    // merged result is always one of the two current heads -- no
    // comparison against any other node is ever needed.

    // Level 2 -- Optimal: two-pointer merge, O(n + m) time, O(1) extra
    // space (reuses existing nodes).
    static ListNode mergeTwoLists(ListNode list1, ListNode list2) {
        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;

        while (list1 != null && list2 != null) {
            if (list1.val <= list2.val) {
                tail.next = list1;
                list1 = list1.next;
            } else {
                tail.next = list2;
                list2 = list2.next;
            }
            tail = tail.next;
        }
        tail.next = (list1 != null) ? list1 : list2;
        return dummy.next;
    }

    // Level 3 -- Hardened: works when one list is empty from the
    // start (the remainder-attach step handles it directly) and when
    // both lists are empty (loop never runs, remainder is null, dummy
    // .next stays null).

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
        print(mergeTwoLists(build(1, 2, 4), build(1, 3, 4)));
        // 1 1 2 3 4 4
        print(mergeTwoLists(build(), build(0)));
        // 0
    }
}
```

**How to run:** `java MergeTwoSortedLists.java`

## 6. Walkthrough

Trace `mergeTwoLists([1,2,4], [1,3,4])`:

| list1 head | list2 head | comparison | attached | new tail |
|---|---|---|---|---|
| 1 | 1 | 1 &lt;= 1 | list1's 1 | 1 |
| 2 | 1 | 2 &gt; 1 | list2's 1 | 1 |
| 2 | 3 | 2 &lt;= 3 | list1's 2 | 2 |
| 4 | 3 | 4 &gt; 3 | list2's 3 | 3 |
| 4 | 4 | 4 &lt;= 4 | list1's 4 | 4 |
| null | 4 | list1 exhausted | attach list2 remainder (4) | 4 |

Final merged list: `1, 1, 2, 3, 4, 4`. Time complexity is O(n + m), one pass across both lists combined. Space is O(1) extra, since existing nodes are relinked rather than copied.

## 7. Gotchas & takeaways

> Gotcha: using `<` instead of `<=` when comparing equal values still produces a correctly sorted result, but changes WHICH list's node with a tied value comes first — matters for problems that require a stable merge order, though not for this one specifically.

- Using a `dummy` head node avoids special-casing "is this the very first node of the result," a common source of off-by-one bugs in list-building problems.
- This is the `k=2` special case of K-way Merge — no heap is needed because comparing exactly two candidates directly is simpler than maintaining a heap of size 2.
- Related problems: Merge k Sorted Lists (the general `k`-way version, needing a min-heap), Sort List (a different linked-list sorting technique, merge sort from scratch).
