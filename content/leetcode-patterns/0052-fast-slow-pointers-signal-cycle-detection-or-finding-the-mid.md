---
card: leetcode-patterns
gi: 52
slug: fast-slow-pointers-signal-cycle-detection-or-finding-the-mid
title: Fast & Slow Pointers — signal: cycle detection or finding the middle of a sequence
---

## 1. What it is

Fast & slow pointers (also called Floyd's tortoise and hare) is a technique that walks two pointers over the same sequence at different speeds. The slow pointer moves one step at a time. The fast pointer moves two steps at a time. Both start at the same place and traverse the same linked list or array.

## 2. Why & when

Some problems ask about the *shape* of a sequence rather than its values: does a linked list loop back on itself, or where is the exact middle node? A single pointer cannot answer these without extra memory, such as a hash set of visited nodes, or without a second pass, such as first counting the length then walking again.

Learn to recognize these signals in a problem statement:

- **"Does the linked list have a cycle?"** or **"find the node where the cycle begins."**
- **"Find the middle node"** of a linked list, especially when you can only make one pass.
- **A sequence defined by repeatedly applying a function** to a starting value, such as digit-squaring in Happy Number, where a cycle means the process never terminates.
- **"Detect a duplicate"** in an array of numbers within a bounded range, which can be reframed as a linked-list cycle problem.

The alternative is to use a hash set to track visited nodes, which costs O(n) extra space. Fast & slow pointers solves the same problems in O(1) space, because it needs no auxiliary storage — only two moving positions.

## 3. Core concept

**Key idea:** if a sequence loops back on itself, a pointer moving twice as fast as another will eventually lap it and the two will meet inside the loop. If the sequence has no loop, the fast pointer reaches the end first.

**Steps:**
1. Set `slow = head` and `fast = head`.
2. Loop while `fast` and `fast.next` are not null:
   - Move `slow = slow.next` (one step).
   - Move `fast = fast.next.next` (two steps).
   - If `slow == fast`, a cycle exists.
3. If the loop exits because `fast` or `fast.next` became null, there is no cycle.

**Why it works:** think of the gap between `fast` and `slow` inside a cycle. Each step, `fast` gains one extra position on `slow`. The gap shrinks by exactly one node per iteration. Since the cycle has a finite length, the gap must eventually reach zero, so the two pointers meet. Outside a cycle, `fast` simply reaches the null end before `slow` does, since it always covers twice the distance.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Fast and slow pointers meeting inside a cycle">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">list: 1 -&gt; 2 -&gt; 3 -&gt; 4 -&gt; 5 -&gt; back to 3 (cycle)</text>
    <circle cx="80" cy="100" r="22" fill="#161b22" stroke="#79c0ff"/>
    <text x="80" y="105" fill="#e6edf3" text-anchor="middle">1</text>
    <circle cx="160" cy="100" r="22" fill="#161b22" stroke="#79c0ff"/>
    <text x="160" y="105" fill="#e6edf3" text-anchor="middle">2</text>
    <circle cx="260" cy="60" r="22" fill="#161b22" stroke="#f0883e"/>
    <text x="260" y="65" fill="#e6edf3" text-anchor="middle">3</text>
    <circle cx="360" cy="60" r="22" fill="#161b22" stroke="#30363d"/>
    <text x="360" y="65" fill="#e6edf3" text-anchor="middle">4</text>
    <circle cx="330" cy="150" r="22" fill="#161b22" stroke="#30363d"/>
    <text x="330" y="155" fill="#e6edf3" text-anchor="middle">5</text>
    <line x1="102" y1="100" x2="138" y2="100" stroke="#8b949e" marker-end="url(#a)"/>
    <line x1="182" y1="94" x2="238" y2="66" stroke="#8b949e" marker-end="url(#a)"/>
    <line x1="282" y1="54" x2="338" y2="54" stroke="#8b949e" marker-end="url(#a)"/>
    <line x1="358" y1="82" x2="345" y2="130" stroke="#8b949e" marker-end="url(#a)"/>
    <line x1="313" y1="140" x2="278" y2="78" stroke="#8b949e" marker-end="url(#a)"/>
    <defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#8b949e"/></marker></defs>
    <text x="20" y="190" fill="#8b949e">slow moves 1 step, fast moves 2 steps; they meet somewhere inside the loop (node 3 or 4)</text>
  </g>
</svg>

The fast pointer laps the slow pointer inside the cycle, so the gap between them shrinks by one node every step until it hits zero.

## 5. Runnable example

A generic "does a cycle exist" scan you can adapt to any linked-list problem in this pattern.

```java
// FastSlowPointersSignal.java
public class FastSlowPointersSignal {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Generic cycle check: returns true if the list loops back on itself.
    static boolean hasCycle(ListNode head) {
        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) return true;
        }
        return false;
    }

    public static void main(String[] args) {
        ListNode a = new ListNode(1);
        ListNode b = new ListNode(2);
        ListNode c = new ListNode(3);
        a.next = b;
        b.next = c;
        c.next = a; // creates a cycle back to node a
        System.out.println("has cycle: " + hasCycle(a));

        ListNode x = new ListNode(1);
        x.next = new ListNode(2);
        System.out.println("has cycle: " + hasCycle(x));
    }
}
```

How to run: save as `FastSlowPointersSignal.java`, then run `java FastSlowPointersSignal.java`.

## 6. Walkthrough

Trace `hasCycle` on the list `1 -> 2 -> 3 -> back to 1`:

1. `slow = 1`, `fast = 1` at the start.
2. Step 1: `slow` moves to `2`. `fast` moves to `3`. They are not equal.
3. Step 2: `slow` moves to `3`. `fast` moves two steps: `3 -> 1 -> 2`, landing on `2`. Not equal.
4. Step 3: `slow` moves to `1`. `fast` moves two steps: `2 -> 3 -> 1`, landing on `1`. `slow == fast`, so the method returns `true`.

## 7. Gotchas & takeaways

> Gotcha: checking only `fast != null` and forgetting `fast.next != null` throws a `NullPointerException` when the list has an even number of nodes and no cycle, because `fast.next.next` dereferences a null `next`.

- Fast & slow pointers only needs O(1) extra space, unlike a hash-set approach which needs O(n).
- The same skeleton, with small tweaks, finds the middle node, detects a cycle's starting point, and even finds duplicates in an array — see the following pages in this section.
