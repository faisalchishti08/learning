---
card: leetcode-patterns
gi: 59
slug: intersection-of-two-linked-lists
title: Intersection of Two Linked Lists
---

## 1. What it is

Given the heads of two singly linked lists, `headA` and `headB`, return the node at which they intersect (become the same node onward), or `null` if they never intersect. Example: list A `[4,1,8,4,5]` and list B `[5,6,1,8,4,5]` share the tail starting at node `8` → return that node.

## 2. Why & when

The two lists may have different lengths before they merge, so naively walking both from their heads at the same pace does not align them at the intersection point. This problem uses a two-pointer trick closely related to fast & slow pointers: instead of different speeds, it equalizes the *distance remaining* by having each pointer walk the other list after finishing its own.

## 3. Core concept

**Key idea:** if pointer `a` walks list A then list B, and pointer `b` walks list B then list A, both pointers travel the exact same total distance (`lenA + lenB`) before reaching the end. If the lists intersect, both pointers arrive at the intersection node at the same step, because the combined path length equalizes any difference in the two lists' individual lengths.

**Steps:**
1. Set `a = headA`, `b = headB`.
2. Loop while `a != b`:
   - Move `a = (a == null) ? headB : a.next`.
   - Move `b = (b == null) ? headA : b.next`.
3. Return `a` (which equals `b`) — either the intersection node, or `null` if the lists never intersect.

**Why it is correct:** let list A have a unique prefix of length `p`, list B have a unique prefix of length `q`, and both share a common suffix of length `c`. Pointer `a` travels `p + c + q` steps before reaching the intersection on its second pass through list B's prefix. Pointer `b` travels `q + c + p` steps. These are equal, so both pointers land on the intersection node simultaneously.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two linked lists merging at a shared tail">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">A: 4 -&gt; 1 -&gt; 8 -&gt; 4 -&gt; 5   B: 5 -&gt; 6 -&gt; 1 -&gt; 8 -&gt; 4 -&gt; 5 (shared tail from 8)</text>
    <circle cx="60" cy="70" r="18" fill="#161b22" stroke="#79c0ff"/><text x="60" y="75" fill="#e6edf3" text-anchor="middle">4</text>
    <circle cx="120" cy="70" r="18" fill="#161b22" stroke="#79c0ff"/><text x="120" y="75" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="220" cy="100" r="18" fill="#161b22" stroke="#3fb950"/><text x="220" y="105" fill="#e6edf3" text-anchor="middle">8</text>
    <circle cx="280" cy="100" r="18" fill="#161b22" stroke="#3fb950"/><text x="280" y="105" fill="#e6edf3" text-anchor="middle">4</text>
    <circle cx="60" cy="140" r="18" fill="#161b22" stroke="#f0883e"/><text x="60" y="145" fill="#e6edf3" text-anchor="middle">5</text>
    <circle cx="120" cy="140" r="18" fill="#161b22" stroke="#f0883e"/><text x="120" y="145" fill="#e6edf3" text-anchor="middle">6</text>
    <circle cx="180" cy="140" r="18" fill="#161b22" stroke="#f0883e"/><text x="180" y="145" fill="#e6edf3" text-anchor="middle">1</text>
    <line x1="78" y1="70" x2="102" y2="70" stroke="#8b949e" marker-end="url(#d)"/>
    <line x1="132" y1="80" x2="205" y2="95" stroke="#8b949e" marker-end="url(#d)"/>
    <line x1="238" y1="100" x2="262" y2="100" stroke="#8b949e" marker-end="url(#d)"/>
    <line x1="78" y1="140" x2="102" y2="140" stroke="#8b949e" marker-end="url(#d)"/>
    <line x1="138" y1="140" x2="162" y2="140" stroke="#8b949e" marker-end="url(#d)"/>
    <line x1="195" y1="132" x2="212" y2="108" stroke="#8b949e" marker-end="url(#d)"/>
    <defs><marker id="d" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#8b949e"/></marker></defs>
    <text x="20" y="185" fill="#8b949e">node 8 is the intersection point where both lists merge into a shared tail</text>
  </g>
</svg>

Both lists funnel into the same tail starting at node `8` — the shared suffix that the two-pointer swap technique locates without measuring lengths up front.

## 5. Runnable example

```java
// IntersectionOfTwoLinkedLists.java
public class IntersectionOfTwoLinkedLists {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: for every node in A, scan all of B looking
    // for a reference match. O(n * m) time, O(1) space -- wastes time
    // rescanning B repeatedly.
    static ListNode bruteForce(ListNode headA, ListNode headB) {
        for (ListNode a = headA; a != null; a = a.next) {
            for (ListNode b = headB; b != null; b = b.next) {
                if (a == b) return a;
            }
        }
        return null;
    }

    // KEY INSIGHT: swapping each pointer onto the OTHER list once it runs
    // out equalizes the total distance each pointer travels -- so they
    // arrive at the intersection at the same step, with no length math.

    // Level 2 -- Optimal: two pointers swapping lists. O(n + m) time,
    // O(1) space.
    public static ListNode getIntersectionNode(ListNode headA, ListNode headB) {
        if (headA == null || headB == null) return null;
        ListNode a = headA, b = headB;
        while (a != b) {
            a = (a == null) ? headB : a.next;
            b = (b == null) ? headA : b.next;
        }
        return a;
    }

    // Level 3 -- Hardened: lists that never intersect. Both pointers
    // become null at the same step (after traversing lenA + lenB total),
    // so the loop ends correctly with a == b == null.
    static ListNode hardened(ListNode headA, ListNode headB) {
        return getIntersectionNode(headA, headB);
    }

    public static void main(String[] args) {
        ListNode shared1 = new ListNode(8);
        ListNode shared2 = new ListNode(4);
        ListNode shared3 = new ListNode(5);
        shared1.next = shared2;
        shared2.next = shared3;

        ListNode a1 = new ListNode(4);
        ListNode a2 = new ListNode(1);
        a1.next = a2;
        a2.next = shared1;

        ListNode b1 = new ListNode(5);
        ListNode b2 = new ListNode(6);
        ListNode b3 = new ListNode(1);
        b1.next = b2;
        b2.next = b3;
        b3.next = shared1;

        System.out.println("brute force intersection value: " + bruteForce(a1, b1).val);
        System.out.println("optimal intersection value:     " + getIntersectionNode(a1, b1).val);

        ListNode noShare1 = new ListNode(1);
        ListNode noShare2 = new ListNode(2);
        System.out.println("no intersection: " + hardened(noShare1, noShare2));
    }
}
```

How to run: save as `IntersectionOfTwoLinkedLists.java`, then run `java IntersectionOfTwoLinkedLists.java`.

## 6. Walkthrough

List A has unique prefix `[4,1]` (length 2), list B has unique prefix `[5,6,1]` (length 3), shared suffix `[8,4,5]` (length 3).

| step | a | b |
|---|---|---|
| start | 4 | 5 |
| 1 | 1 | 6 |
| 2 | 8 | 1 |
| 3 | 4 | 8 |
| 4 | 5 | 4 |
| 5 | (a hits null, switches to headB) 5 | 5 |
| 6 | 6 | (b hits null, switches to headA) 4 |
| 7 | 1 | 1 |
| 8 | 8 | 8 → `a == b`, return node `8` |

Time complexity: O(n + m), where `n` and `m` are the two list lengths. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: comparing node values instead of references can give a false intersection if two different nodes happen to hold the same value. Always compare object references, as shown by `a == b`.

- This pattern is a close cousin of fast & slow pointers: instead of unequal speeds, it uses unequal starting offsets that self-correct by swapping lists — the same "let the movement rule cancel out an unknown gap" idea.
- Related problems: Linked List Cycle II (uses distance math similarly), Middle of the Linked List.
