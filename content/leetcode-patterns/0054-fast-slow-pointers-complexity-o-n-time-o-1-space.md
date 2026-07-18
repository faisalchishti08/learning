---
card: leetcode-patterns
gi: 54
slug: fast-slow-pointers-complexity-o-n-time-o-1-space
title: Fast & Slow Pointers — complexity: O(n) time, O(1) space
---

## 1. What it is

This page states and proves the time and space cost of the fast & slow pointers pattern: O(n) time, where `n` is the number of nodes or elements scanned, and O(1) extra space, because the technique uses only two pointer variables no matter how large the input is.

## 2. Why & when

Knowing the complexity in advance lets you judge, before writing any code, whether fast & slow pointers beats the alternative. The main competing approach — a hash set of visited nodes — also runs in O(n) time but costs O(n) extra space. When an interview or problem statement asks for O(1) space, that is a strong hint to reach for fast & slow pointers instead of a hash set.

## 3. Core concept

**Time — O(n):** the fast pointer visits at most `n` nodes before either reaching the end (no cycle) or lapping the slow pointer (cycle found). Even in the worst case, where the cycle is the entire list, the fast pointer cannot take more than roughly `n` steps before the gap between it and the slow pointer closes to zero, because the gap shrinks by exactly one node per iteration and starts at most `n` nodes wide.

**Space — O(1):** the algorithm never allocates memory proportional to the input. It only tracks two references, `slow` and `fast`, regardless of whether the list has 10 nodes or 10 million.

**Comparison:**

| Approach | Time | Space |
|---|---|---|
| Hash set of visited nodes | O(n) | O(n) |
| Fast & slow pointers | O(n) | O(1) |

Both approaches find a cycle in linear time, but only fast & slow pointers does it without extra memory.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Complexity comparison bar chart">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">space used as input size n grows</text>
    <text x="20" y="45" fill="#79c0ff">hash set:</text>
    <rect x="100" y="34" width="20" height="14" fill="#f0883e"/>
    <rect x="130" y="34" width="80" height="14" fill="#f0883e"/>
    <rect x="220" y="34" width="200" height="14" fill="#f0883e"/>
    <text x="20" y="80" fill="#79c0ff">fast &amp; slow:</text>
    <rect x="100" y="69" width="10" height="14" fill="#3fb950"/>
    <rect x="130" y="69" width="10" height="14" fill="#3fb950"/>
    <rect x="220" y="69" width="10" height="14" fill="#3fb950"/>
    <text x="20" y="120" fill="#8b949e">hash-set space grows with n; fast &amp; slow pointers stays flat at O(1)</text>
  </g>
</svg>

Both scans finish in linear time, but the space bars show why fast & slow pointers wins when memory matters: it never grows with `n`.

## 5. Runnable example

```java
// FastSlowPointersComplexity.java
import java.util.HashSet;
import java.util.Set;

public class FastSlowPointersComplexity {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // O(n) time, O(n) space -- stores every visited node.
    static boolean hasCycleHashSet(ListNode head) {
        Set<ListNode> seen = new HashSet<>();
        ListNode cur = head;
        while (cur != null) {
            if (!seen.add(cur)) return true;
            cur = cur.next;
        }
        return false;
    }

    // O(n) time, O(1) space -- only two pointer variables, ever.
    static boolean hasCycleFastSlow(ListNode head) {
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
        c.next = b; // cycle back into the list

        System.out.println("hash set result:   " + hasCycleHashSet(a));
        System.out.println("fast/slow result:  " + hasCycleFastSlow(a));
    }
}
```

How to run: save as `FastSlowPointersComplexity.java`, then run `java FastSlowPointersComplexity.java`.

## 6. Walkthrough

1. `hasCycleHashSet` walks the list once, adding each node to a `HashSet`. Each `add` and lookup costs O(1) on average, so the total time is O(n). The set grows by one entry per node, so space is O(n).
2. `hasCycleFastSlow` walks the same list with two pointers. Each iteration is O(1) work, and the loop runs at most O(n) times, so total time is O(n).
3. `hasCycleFastSlow` never allocates a collection — `slow` and `fast` are the only extra variables, so space stays O(1) regardless of list length.
4. Both methods print `true` for the cyclic list in the example, confirming they agree on correctness while differing only in space usage.

## 7. Gotchas & takeaways

> Gotcha: O(n) time does not mean "one pass is always enough" — the fast pointer can take up to roughly `2n` total steps (n for slow, up to n extra for fast lapping it), but that is still a constant multiple of `n`, so it stays O(n).

- Reach for fast & slow pointers whenever a problem explicitly asks for O(1) space, since the hash-set approach is usually the first idea that comes to mind but costs O(n) space.
- The O(1) space guarantee holds for cycle detection, finding the middle, and Happy Number — none of them need extra data structures.
