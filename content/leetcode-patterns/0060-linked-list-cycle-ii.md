---
card: leetcode-patterns
gi: 60
slug: linked-list-cycle-ii
title: Linked List Cycle II
---

## 1. What it is

Given the `head` of a linked list, return the node where a cycle begins, or `null` if there is no cycle. Example: `head = [3,2,0,-4]` where the tail points back to node index `1` (value `2`) → return the node with value `2`.

## 2. Why & when

Linked List Cycle only asks *whether* a cycle exists. This problem asks *where* it starts, which needs an extra insight after the fast/slow pointers first meet. It is a direct, harder follow-up to the base fast & slow pointers template, and demonstrates the "hardened" level of the pattern.

## 3. Core concept

**Key idea:** after `slow` and `fast` meet inside the cycle (using the standard fast & slow pointers loop), reset one pointer to `head` and advance both remaining pointers one step at a time. The node where they meet again is the start of the cycle.

**Steps:**
1. Run the standard fast & slow pointers loop until `slow == fast` (cycle found) or `fast` hits `null` (no cycle — return `null`).
2. Reset `slow2 = head`, keep `fast` (or the shared meeting pointer) where it is.
3. Move both `slow2` and the meeting pointer one step at a time until they meet again.
4. Return that meeting node — it is the cycle's start.

**Why it is correct:** let the distance from `head` to the cycle's start be `a`, from the cycle's start to the meeting point be `b`, and the remaining cycle length back to the start be `c`. When `slow` and `fast` first meet, `slow` has traveled `a + b`, and `fast` has traveled `a + b + k(b + c)` for some number of extra laps `k`, but also `fast` traveled exactly twice as far as `slow`. Solving these two facts algebraically shows that `a` equals `k(b + c) - b`, which is a multiple of the cycle length offset by `-b`. That means walking `a` steps from `head` lands on the same node as walking `a` steps from the meeting point — which is exactly the cycle's start.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Finding the start of a cycle using a second pointer from head">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">head = [3, 2, 0, -4], cycle starts at node 2 (index 1)</text>
    <circle cx="60" cy="90" r="20" fill="#161b22" stroke="#79c0ff"/><text x="60" y="95" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="140" cy="90" r="20" fill="#161b22" stroke="#f0883e"/><text x="140" y="95" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="220" cy="90" r="20" fill="#161b22" stroke="#30363d"/><text x="220" y="95" fill="#e6edf3" text-anchor="middle">0</text>
    <circle cx="300" cy="90" r="20" fill="#161b22" stroke="#3fb950"/><text x="300" y="95" fill="#e6edf3" text-anchor="middle">-4</text>
    <line x1="80" y1="90" x2="120" y2="90" stroke="#8b949e" marker-end="url(#e)"/>
    <line x1="160" y1="90" x2="200" y2="90" stroke="#8b949e" marker-end="url(#e)"/>
    <line x1="240" y1="90" x2="280" y2="90" stroke="#8b949e" marker-end="url(#e)"/>
    <path d="M300,110 C300,150 140,150 140,110" fill="none" stroke="#8b949e" marker-end="url(#e)"/>
    <defs><marker id="e" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#8b949e"/></marker></defs>
    <text x="20" y="180" fill="#8b949e">meeting point is somewhere in the cycle; a fresh pointer from head meets it exactly at node 2</text>
  </g>
</svg>

Phase two starts a fresh pointer at `head`; it and the original meeting-point pointer both move one step at a time and converge exactly on the cycle's entrance.

## 5. Runnable example

```java
// LinkedListCycleII.java
public class LinkedListCycleII {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: hash set of visited nodes; first repeat is
    // the cycle start. O(n) time, O(n) space -- wastes memory.
    static ListNode bruteForce(ListNode head) {
        java.util.Set<ListNode> seen = new java.util.HashSet<>();
        ListNode cur = head;
        while (cur != null) {
            if (!seen.add(cur)) return cur;
            cur = cur.next;
        }
        return null;
    }

    // KEY INSIGHT: after slow and fast meet, the distance from head to the
    // cycle start equals the distance from the meeting point to the cycle
    // start (following the cycle around) -- so a fresh pointer from head,
    // moving one step at a time alongside the meeting point, finds it.

    // Level 2 -- Optimal: two-phase fast &amp; slow pointers. O(n) time,
    // O(1) space.
    public static ListNode detectCycle(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) {
                ListNode ptr = head;
                while (ptr != slow) {
                    ptr = ptr.next;
                    slow = slow.next;
                }
                return ptr;
            }
        }
        return null;
    }

    // Level 3 -- Hardened: no cycle at all, and a cycle that starts at
    // head itself (the whole list is one loop).
    static ListNode hardened(ListNode head) {
        return detectCycle(head);
    }

    public static void main(String[] args) {
        ListNode a = new ListNode(3);
        ListNode b = new ListNode(2);
        ListNode c = new ListNode(0);
        ListNode d = new ListNode(-4);
        a.next = b; b.next = c; c.next = d; d.next = b; // cycle starts at b

        System.out.println("brute force cycle start: " + bruteForce(a).val);
        System.out.println("optimal cycle start:     " + detectCycle(a).val);

        ListNode e = new ListNode(1);
        e.next = new ListNode(2);
        System.out.println("no cycle: " + hardened(e));
    }
}
```

How to run: save as `LinkedListCycleII.java`, then run `java LinkedListCycleII.java`.

## 6. Walkthrough

Dry run on `3 -> 2 -> 0 -> -4 -> back to 2`:

1. **Phase 1** (find a meeting point): `slow` and `fast` run the standard loop and meet at node `-4` (see the trace in Linked List Cycle for the equivalent steps).
2. **Phase 2** (find the start): reset `ptr = head` (node `3`). Keep `slow` at the meeting node `-4`.
3. Move both one step: `ptr` goes to `2`, `slow` goes to `2` (following `-4 -> 2`).
4. `ptr == slow` (both at node `2`), so the loop stops and returns node `2` — the correct cycle start.

Time complexity: O(n), since both phases together visit each node a bounded number of times. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: forgetting Phase 2 entirely and just returning the Phase 1 meeting point gives *a* node inside the cycle, but not necessarily the *start* of the cycle — the two are only guaranteed to be the same node when the meeting point happens to land exactly on the entrance.

- The algebra behind Phase 2 (`a == k(b+c) - b`) is the part worth memorizing: reset one pointer to head, then walk both one step at a time.
- Related problems: Linked List Cycle (Phase 1 only), Happy Number (same two-phase idea could locate the exact repeating value, though the problem does not ask for it).
