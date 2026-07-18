---
card: leetcode-patterns
gi: 61
slug: reorder-list
title: Reorder List
---

## 1. What it is

Given the `head` of a singly linked list `L0 -> L1 -> ... -> Ln-1 -> Ln`, reorder it in place to `L0 -> Ln -> L1 -> Ln-1 -> L2 -> Ln-2 -> ...`, alternating the first and last remaining nodes. Example: `head = [1,2,3,4]` → reorder to `[1,4,2,3]`.

## 2. Why & when

The naive approach copies every node into an array, then rebuilds the list by alternately picking from the front and back of the array — O(n) time but O(n) extra space. Fast & slow pointers finds the middle in one pass, letting you split the list, reverse the second half in place, and merge the two halves alternately — all without extra storage.

## 3. Core concept

**Key idea:** this problem combines three techniques already used earlier in this section: find the middle (fast & slow pointers), reverse the second half in place, and merge two lists by alternating nodes.

**Steps:**
1. Find the middle node with fast & slow pointers, then split the list into a first half and a second half.
2. Reverse the second half in place.
3. Merge the two halves by alternating nodes: first node of half one, first node of (reversed) half two, second node of half one, and so on.

**Why it is correct:** reversing the second half turns "the last remaining node" into "the next node in a forward walk" — exactly what the target order needs. Interleaving two forward-moving lists one node at a time reproduces the required `L0, Ln, L1, Ln-1, ...` pattern.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Reordering a list by splitting, reversing, and merging">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">head = [1, 2, 3, 4]</text>
    <text x="20" y="45" fill="#8b949e">split at middle: first half [1,2], second half [3,4]</text>
    <text x="20" y="70" fill="#8b949e">reverse second half: [3,4] becomes [4,3]</text>
    <rect x="20" y="90" width="36" height="28" fill="#161b22" stroke="#79c0ff"/><text x="38" y="109" fill="#e6edf3" text-anchor="middle">1</text>
    <rect x="66" y="90" width="36" height="28" fill="#161b22" stroke="#f0883e"/><text x="84" y="109" fill="#e6edf3" text-anchor="middle">4</text>
    <rect x="112" y="90" width="36" height="28" fill="#161b22" stroke="#79c0ff"/><text x="130" y="109" fill="#e6edf3" text-anchor="middle">2</text>
    <rect x="158" y="90" width="36" height="28" fill="#161b22" stroke="#f0883e"/><text x="176" y="109" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="20" y="145" fill="#8b949e">merge alternately: 1(half1) -&gt; 4(half2) -&gt; 2(half1) -&gt; 3(half2)</text>
    <text x="20" y="180" fill="#8b949e">result: [1, 4, 2, 3]</text>
  </g>
</svg>

Splitting, reversing the tail half, then weaving the two halves together produces the alternating front/back pattern the problem asks for.

## 5. Runnable example

```java
// ReorderList.java
public class ReorderList {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: copy all nodes into a list, rebuild by
    // alternating from front and back. O(n) time, O(n) space -- wastes
    // memory holding a full copy of the list.
    static ListNode bruteForce(ListNode head) {
        java.util.List<ListNode> nodes = new java.util.ArrayList<>();
        for (ListNode cur = head; cur != null; cur = cur.next) nodes.add(cur);
        int i = 0, j = nodes.size() - 1;
        ListNode dummy = new ListNode(0), cur = dummy;
        boolean front = true;
        while (i <= j) {
            cur.next = front ? nodes.get(i++) : nodes.get(j--);
            cur = cur.next;
            front = !front;
        }
        cur.next = null;
        return dummy.next;
    }

    // KEY INSIGHT: reversing the second half converts "pick the last
    // remaining node" into "take the next node in a forward scan" --
    // turning the whole problem into split + reverse + merge, all O(1)
    // extra space.

    // Level 2 -- Optimal: find middle, reverse second half, merge
    // alternately, IN PLACE. O(n) time, O(1) extra space.
    public static void reorderList(ListNode head) {
        if (head == null || head.next == null) return;

        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
        }

        ListNode secondHalf = reverse(slow.next);
        slow.next = null; // cut the first half off from the second

        ListNode p1 = head, p2 = secondHalf;
        while (p2 != null) {
            ListNode p1Next = p1.next;
            ListNode p2Next = p2.next;
            p1.next = p2;
            if (p1Next != null) p2.next = p1Next;
            p1 = p1Next;
            p2 = p2Next;
        }
    }

    static ListNode reverse(ListNode head) {
        ListNode prev = null;
        while (head != null) {
            ListNode next = head.next;
            head.next = prev;
            prev = head;
            head = next;
        }
        return prev;
    }

    // Level 3 -- Hardened: odd-length lists, where the middle node stays
    // in the first half and has no partner from the second half.
    static ListNode hardened(ListNode head) {
        reorderList(head);
        return head;
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
        ListNode even = build(1, 2, 3, 4);
        reorderList(even);
        System.out.print("even length result: "); print(even);

        ListNode odd = build(1, 2, 3, 4, 5);
        hardened(odd);
        System.out.print("odd length result:  "); print(odd);
    }
}
```

How to run: save as `ReorderList.java`, then run `java ReorderList.java`.

## 6. Walkthrough

Dry run on `head = [1, 2, 3, 4]`:

1. Fast & slow pointers find `slow` at node `2` (the first of the two middles).
2. Reverse `slow.next` (`3 -> 4`) to get `4 -> 3`. Cut `slow.next = null`, leaving first half `1 -> 2` and second half `4 -> 3`.
3. Merge: `p1 = 1`, `p2 = 4`. Set `1.next = 4`. Advance `p1 = 2`, `p2 = 3`.
4. Set `4.next = 2`. Advance `p1 = null` (was `2.next`), `p2 = null` (was `3.next`).
5. Set `2.next = 3`. `p2` is now `null`, loop ends.
6. Final list: `1 -> 4 -> 2 -> 3`, matching the expected reorder.

Time complexity: O(n) — one pass to find the middle, one to reverse, one to merge. Space complexity: O(1), all done in place.

## 7. Gotchas & takeaways

> Gotcha: forgetting to cut `slow.next = null` after finding the middle leaves the first half still pointing into the second half, which can create an accidental cycle once the merge starts rewriting `next` pointers.

- This problem is a direct composition of three earlier building blocks: find-the-middle, in-place reversal, and alternate merge — recognizing the composition is more valuable than memorizing new code.
- Related problems: Palindrome Linked List (find-the-middle + reverse, but compares instead of merges), Merge Two Sorted Lists (a different kind of alternating merge).
