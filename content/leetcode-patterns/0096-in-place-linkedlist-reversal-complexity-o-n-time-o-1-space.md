---
card: leetcode-patterns
gi: 96
slug: in-place-linkedlist-reversal-complexity-o-n-time-o-1-space
title: In-place LinkedList Reversal — complexity: O(n) time, O(1) space
---

## 1. What it is

This page states and proves the time and space cost of in-place linked list reversal: O(n) time, where `n` is the number of nodes involved in the reversal (the whole list, or just a segment), and O(1) extra space, since only a constant number of pointer variables are used regardless of list length.

## 2. Why & when

Knowing this bound in advance confirms that in-place reversal is never worse than a copy-based approach, and is always better in space. It also helps you reason about combined operations — for example, reversing groups of `k` nodes across an entire list of length `n` is still O(n) total, because each node's pointer is rewritten exactly once across the whole process, even though the work is split into `n/k` separate segment reversals.

## 3. Core concept

**Time — O(n):** the reversal loop visits each node in the segment exactly once. At each node, it does a constant amount of work: save `next`, rewrite `curr.next`, advance three pointers. For a full-list reversal, this is O(n); for a segment reversal, it is O(k), where `k` is the segment length — and O(k) segments processed across a full list still sum to O(n) total.

**Space — O(1):** only `prev`, `curr`, and `next` (plus, for segment problems, a small number of additional pointers like `beforeSegment` or a dummy node) are used. None of these scale with `n` — the algorithm never allocates a new list, array, or stack frame proportional to input size (assuming the reversal is implemented iteratively, not recursively).

**Recursive vs iterative:** a recursive implementation of list reversal is also O(n) time, but costs O(n) space for the call stack — one stack frame per node. The iterative version, using explicit `prev`/`curr`/`next` pointers, is what achieves the true O(1) space bound.

| Approach | Time | Space |
|---|---|---|
| Copy to array, reverse, rebuild | O(n) | O(n) |
| Recursive reversal | O(n) | O(n) (call stack) |
| Iterative in-place reversal | O(n) | O(1) |

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Constant extra space regardless of list length">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">extra space used as list length n grows</text>
    <text x="20" y="50" fill="#79c0ff">recursive:</text>
    <rect x="120" y="38" width="20" height="14" fill="#f0883e"/>
    <rect x="150" y="38" width="80" height="14" fill="#f0883e"/>
    <rect x="240" y="38" width="200" height="14" fill="#f0883e"/>
    <text x="20" y="85" fill="#79c0ff">iterative:</text>
    <rect x="120" y="73" width="10" height="14" fill="#3fb950"/>
    <rect x="150" y="73" width="10" height="14" fill="#3fb950"/>
    <rect x="240" y="73" width="10" height="14" fill="#3fb950"/>
    <text x="20" y="120" fill="#8b949e">recursive call-stack space grows with n; iterative pointer-only reversal stays flat at O(1)</text>
  </g>
</svg>

Both approaches finish in linear time, but only the iterative version keeps space flat as the list grows — the recursive version's call stack scales directly with `n`.

## 5. Runnable example

```java
// InPlaceReversalComplexity.java
public class InPlaceReversalComplexity {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // O(n) time, O(n) space -- one stack frame per node.
    static ListNode reverseRecursive(ListNode head) {
        if (head == null || head.next == null) return head;
        ListNode newHead = reverseRecursive(head.next);
        head.next.next = head;
        head.next = null;
        return newHead;
    }

    // O(n) time, O(1) space -- only three pointer variables, ever.
    static ListNode reverseIterative(ListNode head) {
        ListNode prev = null, curr = head;
        while (curr != null) {
            ListNode next = curr.next;
            curr.next = prev;
            prev = curr;
            curr = next;
        }
        return prev;
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
        print(reverseRecursive(build(1, 2, 3, 4, 5)));
        print(reverseIterative(build(1, 2, 3, 4, 5)));
        System.out.println("both produce the same reversed order; only space usage differs");
    }
}
```

How to run: save as `InPlaceReversalComplexity.java`, then run `java InPlaceReversalComplexity.java`.

## 6. Walkthrough

1. `reverseRecursive` calls itself on `head.next` before doing any work at the current level — this builds up `n` nested stack frames before any pointer rewiring happens, then unwinds them one at a time, fixing pointers on the way back up.
2. `reverseIterative` processes each node exactly once in a single forward loop, using only `prev`, `curr`, and `next` — no stack growth beyond the fixed set of local variables.
3. Both functions print the same reversed list, `5 4 3 2 1`, confirming they agree on correctness while differing in space usage — the recursive version's hidden call-stack cost does not show up in the output, only in memory profiling or a stack overflow on very long lists.

## 7. Gotchas & takeaways

> Gotcha: a recursive reversal on a very long list (tens of thousands of nodes or more) can throw a `StackOverflowError`, since each recursive call consumes a stack frame — the iterative version has no such limit tied to list length.

- Prefer the iterative `prev`/`curr`/`next` template whenever list length could be large or when a problem explicitly asks for O(1) space.
- The O(n) time bound holds whether you reverse the whole list at once or split it into multiple segment reversals — total pointer rewrites across the whole list never exceed `n`.
