---
card: leetcode-patterns
gi: 575
slug: design-complexity-per-operation-complexity-is-the-goal
title: Design — complexity: per-operation complexity is the goal
---

## 1. What it is

In a normal algorithm problem, complexity is measured once, for the whole function. In a Design problem, complexity is measured **per method**, because each method can be called many times in any order, and the interface usually states a separate time bound for each one — for example, "`get` and `put` should each run in O(1) average time," even though `total calls x O(1)` still adds up to real total work.

## 2. Why & when

Use this lens whenever you finish drafting a Design class: check every method against its stated (or implied) bound individually, not the class as a whole. A structure that is fast to build once but slow on repeated calls fails a Design problem even if a single call looks fine in isolation.

## 3. Core concept

**Why per-operation matters more than total complexity here:** Design classes are called in a loop by the grader — potentially thousands of interleaved `get`/`put`/`push`/`pop` calls. If one method is O(n) instead of the required O(1), and the grader calls it 10,000 times, that single weak method turns the whole test case from fast to slow (or from passing to timing out), even though every other method is optimal.

**How to audit a method's complexity:**
1. Identify every operation the method performs: array/list access, hash map operation, heap operation, loop.
2. Take the *worst* single operation in the method, since sequential steps add (not multiply) unless one is nested inside another.
3. Compare against the stated requirement. A `HashMap.get` is O(1) average — but a `LinkedList.indexOf` (as opposed to a `HashMap`-backed lookup) is O(n), and easy to reach for by mistake when only "linked list" is in your head from the problem's own description.
4. Watch for **amortized** vs **worst-case** bounds: an `ArrayList.add` at the end is O(1) amortized (occasional resizes are rare and average out) but O(n) worst-case for a single call — most interview and LeetCode contexts accept amortized O(1) as satisfying an "O(1)" requirement.

**A quick reference table of common per-operation costs:**

| Structure | Lookup by key | Insert/remove at an end | Insert/remove in the middle | Min/max |
|---|---|---|---|---|
| `HashMap` | O(1) avg | — | — | — |
| Array / `ArrayList` | O(n) | O(1) amortized (end only) | O(n) | O(n) |
| Doubly linked list | O(n) (no map) | O(1) | O(1) (given the node) | O(n) |
| `PriorityQueue` (heap) | — | — | — | O(log n) insert/remove, O(1) peek |
| `TreeMap` (balanced BST) | O(log n) | — | — | O(log n) |

## 4. Diagram

<svg viewBox="0 0 700 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One weak O(n) method inside an otherwise O(1) class drags the whole workload down under repeated calls">
  <g font-family="sans-serif" font-size="12">
    <rect x="30" y="20" width="150" height="40" rx="4" fill="#161b22" stroke="#3fb950"/>
    <text x="105" y="45" fill="#e6edf3" text-anchor="middle" font-size="11">get(): O(1)</text>
    <rect x="200" y="20" width="150" height="40" rx="4" fill="#161b22" stroke="#3fb950"/>
    <text x="275" y="45" fill="#e6edf3" text-anchor="middle" font-size="11">put(): O(1)</text>
    <rect x="370" y="20" width="150" height="40" rx="4" fill="#161b22" stroke="#f85149"/>
    <text x="445" y="45" fill="#e6edf3" text-anchor="middle" font-size="11">evict(): O(n)</text>
    <text x="350" y="100" fill="#79c0ff" text-anchor="middle">10,000 calls x O(n) evict = the whole test case is slow</text>
    <text x="350" y="125" fill="#8b949e" text-anchor="middle" font-size="11">even though get() and put() are both optimal</text>
  </g>
</svg>

A single weak method, called repeatedly, dominates the class's real-world performance — auditing "the whole class" is not enough; audit each method.

## 5. Runnable example

The artifact below times two versions of a counter that must support O(1) `increment` and O(1) `getMax`: one uses a plain scan for `getMax` (O(n) per call), the other tracks the running maximum incrementally (O(1) per call).

```java
// DesignComplexity.java
import java.util.*;

public class DesignComplexity {

    // Weak: getMax() rescans every stored value - O(n) per call.
    static class SlowMaxTracker {
        List<Integer> values = new ArrayList<>();
        void increment(int v) { values.add(v); }
        int getMax() {
            int max = Integer.MIN_VALUE;
            for (int v : values) max = Math.max(max, v);
            return max;
        }
    }

    // Strong: track the running max as values arrive - O(1) per call.
    static class FastMaxTracker {
        int max = Integer.MIN_VALUE;
        void increment(int v) { max = Math.max(max, v); }
        int getMax() { return max; }
    }

    public static void main(String[] args) {
        SlowMaxTracker slow = new SlowMaxTracker();
        FastMaxTracker fast = new FastMaxTracker();

        long start = System.nanoTime();
        for (int i = 0; i < 20000; i++) {
            slow.increment(i);
            slow.getMax(); // O(n) every call -> O(n^2) total
        }
        long slowTime = System.nanoTime() - start;

        start = System.nanoTime();
        for (int i = 0; i < 20000; i++) {
            fast.increment(i);
            fast.getMax(); // O(1) every call -> O(n) total
        }
        long fastTime = System.nanoTime() - start;

        System.out.println("slow.getMax() result: " + slow.getMax());
        System.out.println("fast.getMax() result: " + fast.getMax());
        System.out.println("slow took longer: " + (slowTime > fastTime));
    }
}
```

**How to run:** save as `DesignComplexity.java`, then run `java DesignComplexity.java`.

## 6. Walkthrough

1. Both trackers receive the same 20,000 `increment` calls, each immediately followed by a `getMax` call — this simulates how a grader interleaves calls on a Design class.
2. `SlowMaxTracker.getMax` rescans its entire `values` list every call. Call number 20,000 rescans 20,000 elements, making the total work across all calls proportional to `1 + 2 + ... + 20000`, which is O(n^2).
3. `FastMaxTracker.getMax` only reads a single stored field, `max`, which `increment` keeps updated in O(1) as each new value arrives. Total work across all calls is O(n).
4. Both trackers report the same final maximum, `19999` — proving correctness alone does not distinguish them. The timing comparison is what reveals the complexity difference.
5. `slowTime > fastTime` prints `true`: identical output, very different real cost, purely from one method's per-call complexity.

## 7. Gotchas & takeaways

> Gotcha: two implementations can return identical answers on every test case, yet one times out on a large grader workload — always check each method's complexity against its stated bound, not just whether the returned values are correct.

- Audit per method, not per class: one O(n) method inside an otherwise-O(1) class still makes the whole class slow under many calls.
- Amortized O(1) (like `ArrayList.add` at the end) is normally acceptable where an "O(1)" bound is stated; a true O(n) method (like scanning a list to find a key) is not.
- Related pattern-meta pages: [Design — signal: implement a data structure to a required interface](0573-design-signal-implement-a-data-structure-to-a-required-inter.md), [Design — template: compose maps, heaps, and linked lists for O(1)/O(log n) ops](0574-design-template-compose-maps-heaps-and-linked-lists-for-o-1.md).
