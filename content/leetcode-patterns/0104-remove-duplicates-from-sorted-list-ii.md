---
card: leetcode-patterns
gi: 104
slug: remove-duplicates-from-sorted-list-ii
title: Remove Duplicates from Sorted List II
---

## 1. What it is

Given the `head` of a sorted linked list, delete all nodes that have duplicate values, leaving only distinct numbers from the original list. Example: `head = [1,2,3,3,4,4,5]` → `[1,2,5]` (both `3`s and both `4`s are removed entirely, not just reduced to one copy).

## 2. Why & when

Unlike Remove Linked List Elements, which removes nodes matching a fixed known value, this problem must detect duplicate *runs* on the fly, since the values to remove are not known in advance — only that the list is sorted, so duplicates are always adjacent. A dummy node before `head` handles the case where the very first node is part of a duplicate run that gets fully removed.

## 3. Core concept

**Key idea:** use a trailing `prev` pointer, exactly like Remove Linked List Elements, but instead of comparing against a fixed value, look ahead to detect a run of one or more nodes sharing the same value as `curr`. If `curr` starts a run longer than one node, skip the *entire* run; otherwise, keep `curr` and advance `prev` normally.

**Steps:**
1. Create `dummy.next = head`; set `prev = dummy`, `curr = head`.
2. While `curr != null`:
   - If `curr.next != null && curr.next.val == curr.val`, a duplicate run starts here:
     - Advance `curr` while `curr.next != null && curr.next.val == curr.val` (walk to the last node of the run).
     - Skip the whole run: `prev.next = curr.next`.
   - Otherwise, this value is unique — advance `prev = curr`.
   - Either way, advance `curr = curr.next`.
3. Return `dummy.next`.

**Why it is correct:** because the list is sorted, every occurrence of a duplicated value is adjacent, so a single look-ahead scan correctly identifies the full extent of any run. Skipping the entire run (not just the extra copies) via `prev.next = curr.next` removes every node with that value, matching the problem's requirement to delete duplicated values entirely.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Removing entire runs of duplicate values from a sorted list">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">head = [1, 2, 3, 3, 4, 4, 5]</text>
    <circle cx="40" cy="70" r="16" fill="#161b22" stroke="#30363d"/><text x="40" y="75" fill="#8b949e" text-anchor="middle" font-size="9">dummy</text>
    <circle cx="100" cy="70" r="18" fill="#161b22" stroke="#3fb950"/><text x="100" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <circle cx="160" cy="70" r="18" fill="#161b22" stroke="#3fb950"/><text x="160" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">2</text>
    <circle cx="220" cy="70" r="18" fill="#161b22" stroke="#f0883e"/><text x="220" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <circle cx="280" cy="70" r="18" fill="#161b22" stroke="#f0883e"/><text x="280" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">3</text>
    <circle cx="340" cy="70" r="18" fill="#161b22" stroke="#3fb950"/><text x="340" y="75" fill="#e6edf3" text-anchor="middle" font-size="11">5</text>
    <path d="M160,88 C220,120 280,120 320,88" fill="none" stroke="#8b949e" marker-end="url(#o)"/>
    <defs><marker id="o" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#8b949e"/></marker></defs>
    <text x="20" y="150" fill="#8b949e">both 3s are skipped entirely; prev (at node 2) relinks directly past the whole run</text>
  </g>
</svg>

Once a run of matching values is detected (both `3`s), `prev` relinks past the entire run, so neither copy survives — only truly unique values remain.

## 5. Runnable example

```java
// RemoveDuplicatesFromSortedListII.java
public class RemoveDuplicatesFromSortedListII {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: count occurrences of every value with a
    // hash map, then rebuild the list keeping only count-1 values.
    // O(n) time, O(n) space -- wastes memory the sorted-order in-place
    // scan does not need.
    static ListNode bruteForce(ListNode head) {
        java.util.Map<Integer, Integer> count = new java.util.HashMap<>();
        for (ListNode cur = head; cur != null; cur = cur.next) count.merge(cur.val, 1, Integer::sum);
        ListNode dummy = new ListNode(0), cur = dummy;
        for (ListNode node = head; node != null; node = node.next) {
            if (count.get(node.val) == 1) { cur.next = new ListNode(node.val); cur = cur.next; }
        }
        return dummy.next;
    }

    // KEY INSIGHT: because the list is SORTED, every duplicate run is
    // contiguous -- a single look-ahead scan finds the full extent of
    // each run, and skipping the whole run (not just the extras) removes
    // every copy of a duplicated value.

    // Level 2 -- Optimal: dummy node, trailing prev, look-ahead run
    // detection. O(n) time, O(1) extra space.
    public static ListNode deleteDuplicates(ListNode head) {
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode prev = dummy, curr = head;

        while (curr != null) {
            if (curr.next != null && curr.next.val == curr.val) {
                while (curr.next != null && curr.next.val == curr.val) curr = curr.next;
                prev.next = curr.next;
            } else {
                prev = curr;
            }
            curr = curr.next;
        }
        return dummy.next;
    }

    // Level 3 -- Hardened: every value in the list is duplicated (result
    // is an empty list), and a duplicate run at the very start of the
    // list (handled by the dummy node).
    static ListNode hardened(ListNode head) {
        return deleteDuplicates(head);
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
        print(bruteForce(build(1, 2, 3, 3, 4, 4, 5)));
        print(deleteDuplicates(build(1, 2, 3, 3, 4, 4, 5)));

        System.out.print("all duplicated: "); print(hardened(build(1, 1, 1, 2, 2)));
        System.out.print("run at start: "); print(hardened(build(1, 1, 2, 3)));
    }
}
```

How to run: save as `RemoveDuplicatesFromSortedListII.java`, then run `java RemoveDuplicatesFromSortedListII.java`.

## 6. Walkthrough

Dry run of `deleteDuplicates` on `1 -> 2 -> 3 -> 3 -> 4 -> 4 -> 5`:

| step | prev | curr | curr.next.val == curr.val? | action |
|---|---|---|---|---|
| 1 | dummy | 1 | no (2≠1) | prev=1 |
| 2 | 1 | 2 | no (3≠2) | prev=2 |
| 3 | 2 | 3 | yes (3==3) | walk curr to second 3; prev.next = curr.next (4); prev stays 2 |
| 4 | 2 | 4 | yes (4==4) | walk curr to second 4; prev.next = curr.next (5); prev stays 2 |
| 5 | 2 | 5 | no (next is null) | prev=5 |

Return `dummy.next = 1`. Final list: `1 -> 2 -> 5`. Time complexity: O(n), each node visited a bounded number of times. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: the outer `while (curr != null)` and the inner look-ahead `while` both check `curr.next`, which must be null-checked before accessing `.val` — skipping the `curr.next != null` guard causes a `NullPointerException` when a duplicate run reaches the very end of the list.

- This problem generalizes Remove Linked List Elements: instead of a known target value, the "value to remove" is discovered dynamically by detecting adjacent equal values in the sorted list.
- Related problems: Remove Linked List Elements (fixed target value), Remove Duplicates from Sorted List (the easier variant that keeps one copy of each duplicate instead of removing all copies).
