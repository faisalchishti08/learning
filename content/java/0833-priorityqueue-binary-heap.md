---
card: java
gi: 833
slug: priorityqueue-binary-heap
title: PriorityQueue (binary heap)
---

## 1. What it is

`PriorityQueue` is a [`Queue`](0805-queue.md) implementation backed by a **binary heap** — a complete binary tree (stored compactly in a plain array, no actual node/pointer objects needed) satisfying the heap property: every parent is smaller than (or equal to) both of its children, according to natural ordering or a supplied `Comparator`. This structure guarantees the smallest element is always at the root — accessible via `peek()` in O(1) — while `offer()` (insert) and `poll()` (remove the minimum) both run in O(log n), since restoring the heap property after either operation only requires moving an element up or down a single path from root to leaf, never a full re-sort.

## 2. Why & when

Whenever "always process the smallest (or highest-priority) item next, out of an ever-changing collection," a fully sorted structure like `TreeSet` is overkill — it maintains a *total* order, but a priority queue only ever needs to answer "what's the minimum right now," repeatedly, as items are added and removed in between. A binary heap does exactly that at lower overhead: O(log n) insert/remove-min versus a sorted structure's equivalent cost, with a much simpler, more cache-friendly array-based representation (no per-node object allocation, no separate linked pointers). Reach for `PriorityQueue` for task scheduling by priority, Dijkstra's/A* pathfinding's frontier, event simulation queues ordered by timestamp, or any "process cheapest/most-urgent-first" algorithm — anywhere the full sorted order of *all* elements is never actually needed, only repeated access to the current minimum.

## 3. Core concept

```
Binary heap as an array, natural ordering (min-heap):

index:    0   1   2   3   4
value:  [ 3,  5,  8,  9,  7 ]

Tree view (parent at index i, children at 2i+1 and 2i+2):

              3
            /   \
           5     8
          / \
         9   7

peek() -> 3 (the root, O(1))
poll()  -> removes 3, moves the LAST element (7) to the root, then "sifts it down"
           by repeatedly swapping with its smaller child until the heap property holds again
```

Every `offer()` places the new element at the next free array slot, then "sifts it up" — swapping with its parent as long as it's smaller — restoring the heap property in O(log n), the tree's height.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A binary heap stored as an array, with the smallest element always at the root, index 0">
  <g font-family="sans-serif">
    <circle cx="320" cy="40" r="22" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
    <text x="320" y="46" fill="#e6edf3" font-size="13" text-anchor="middle">3</text>
    <text x="320" y="20" fill="#8b949e" font-size="9" text-anchor="middle">[0] root = min</text>

    <circle cx="200" cy="100" r="20" fill="#1c2430" stroke="#79c0ff"/>
    <text x="200" y="106" fill="#e6edf3" font-size="12" text-anchor="middle">5</text>
    <text x="200" y="130" fill="#8b949e" font-size="9" text-anchor="middle">[1]</text>

    <circle cx="440" cy="100" r="20" fill="#1c2430" stroke="#79c0ff"/>
    <text x="440" y="106" fill="#e6edf3" font-size="12" text-anchor="middle">8</text>
    <text x="440" y="130" fill="#8b949e" font-size="9" text-anchor="middle">[2]</text>

    <circle cx="140" cy="160" r="18" fill="#1c2430" stroke="#8b949e"/>
    <text x="140" y="166" fill="#e6edf3" font-size="11" text-anchor="middle">9</text>
    <text x="140" y="188" fill="#8b949e" font-size="9" text-anchor="middle">[3]</text>

    <circle cx="260" cy="160" r="18" fill="#1c2430" stroke="#8b949e"/>
    <text x="260" y="166" fill="#e6edf3" font-size="11" text-anchor="middle">7</text>
    <text x="260" y="188" fill="#8b949e" font-size="9" text-anchor="middle">[4]</text>

    <line x1="320" y1="62" x2="200" y2="82" stroke="#79c0ff"/>
    <line x1="320" y1="62" x2="440" y2="82" stroke="#79c0ff"/>
    <line x1="200" y1="118" x2="140" y2="144" stroke="#8b949e"/>
    <line x1="200" y1="118" x2="260" y2="144" stroke="#8b949e"/>
  </g>
</svg>

*Every parent is ≤ both children — the minimum is always at the root, accessible in O(1).*

## 5. Runnable example

Scenario: a task scheduler that always processes the highest-priority (lowest-numbered) task next, growing from basic priority-ordered processing to a custom-object priority comparator, to a realistic scheduler correctly handling priority *changes* after tasks are already queued — the classic hard case for any heap-based priority queue.

### Level 1 — Basic

```java
import java.util.*;

public class TaskSchedulerBasic {
    public static void main(String[] args) {
        PriorityQueue<Integer> priorities = new PriorityQueue<>(); // min-heap: lowest number = highest priority
        priorities.offer(5);
        priorities.offer(1);
        priorities.offer(3);

        System.out.println("peek (next to process): " + priorities.peek());
        while (!priorities.isEmpty()) {
            System.out.println("processing priority: " + priorities.poll());
        }
    }
}
```

**How to run:** `java TaskSchedulerBasic.java` (JDK 17+).

Expected output:
```
peek (next to process): 1
processing priority: 1
processing priority: 3
processing priority: 5
```

Elements were offered in the order `5, 1, 3`, but `poll()` always returns the current minimum first — `1`, then `3`, then `5` — regardless of insertion order; the heap's internal array layout is not sorted, only the repeated `poll()` sequence is guaranteed to come out in order.

### Level 2 — Intermediate

```java
import java.util.*;

public class TaskSchedulerCustomObjects {
    record Task(String name, int priority) {}

    public static void main(String[] args) {
        PriorityQueue<Task> tasks = new PriorityQueue<>(Comparator.comparingInt(Task::priority));

        tasks.offer(new Task("Deploy hotfix", 1));
        tasks.offer(new Task("Write docs", 5));
        tasks.offer(new Task("Review PR", 2));

        System.out.println("processing order:");
        while (!tasks.isEmpty()) {
            Task next = tasks.poll();
            System.out.println("  " + next.name() + " (priority " + next.priority() + ")");
        }
    }
}
```

**How to run:** `java TaskSchedulerCustomObjects.java`.

Expected output:
```
processing order:
  Deploy hotfix (priority 1)
  Review PR (priority 2)
  Write docs (priority 5)
```

The real-world concern added: a custom `Comparator` (`Comparator.comparingInt(Task::priority)`) applied to a record type, demonstrating that `PriorityQueue` works with any object type as long as an ordering is supplied — the heap operations (sift up/down) only ever need to compare two elements, never inspect their internal structure directly.

### Level 3 — Advanced

```java
import java.util.*;

public class TaskSchedulerPriorityChange {
    static class Task {
        final String name;
        int priority; // MUTABLE -- this is exactly the hard case
        Task(String name, int priority) { this.name = name; this.priority = priority; }
    }

    public static void main(String[] args) {
        PriorityQueue<Task> tasks = new PriorityQueue<>(Comparator.comparingInt(t -> t.priority));

        Task deploy = new Task("Deploy hotfix", 3);
        Task docs = new Task("Write docs", 5);
        Task review = new Task("Review PR", 2);
        tasks.offer(deploy);
        tasks.offer(docs);
        tasks.offer(review);

        // An urgent escalation: "Deploy hotfix" priority changes AFTER it's already in the queue.
        deploy.priority = 1;

        // GOTCHA: just mutating the field does NOT re-sift the heap -- the queue doesn't know it changed.
        System.out.println("peek after silent priority mutation (WRONG, may still show 'Review PR'): " + tasks.peek().name);

        // The correct fix: remove and re-offer, forcing the heap to re-place the element.
        tasks.remove(deploy);
        tasks.offer(deploy);
        System.out.println("peek after remove+re-offer (CORRECT): " + tasks.peek().name);

        System.out.println("full processing order:");
        while (!tasks.isEmpty()) {
            Task next = tasks.poll();
            System.out.println("  " + next.name + " (priority " + next.priority + ")");
        }
    }
}
```

**How to run:** `java TaskSchedulerPriorityChange.java`.

Expected output:
```
peek after silent priority mutation (WRONG, may still show 'Review PR'): Review PR
peek after remove+re-offer (CORRECT): Deploy hotfix
full processing order:
  Deploy hotfix (priority 1)
  Review PR (priority 2)
  Write docs (priority 5)
```

This adds the production-flavored hard case: `PriorityQueue` (like most heap implementations) has **no mechanism to detect that an element already in the queue has changed its priority** — mutating `deploy.priority` directly leaves the heap's array layout exactly as it was, since nothing triggered a re-sift. The queue still believes `review` (priority 2 at insertion time) is smaller than `deploy`, even though `deploy`'s priority field now reads `1`. The correct fix is `remove(element)` (an O(n) linear scan to find it, then a heap removal) followed by `offer(element)` again (which re-inserts it fresh, sifting it to its now-correct position) — there's no cheaper built-in way to signal "this element's priority changed" to a plain `PriorityQueue`.

## 6. Walkthrough

Tracing `TaskSchedulerPriorityChange.main`:

1. Three tasks are offered: `deploy` (priority 3), `docs` (priority 5), `review` (priority 2). After all three inserts, the heap's internal array has `review` (priority 2) at the root, since it's currently the smallest.
2. `deploy.priority = 1` mutates the `Task` object's field directly — but `PriorityQueue` has no way to observe this mutation happening; its internal array still has `deploy` positioned wherever it was placed based on its *original* priority (3), sitting below `review` in the heap structure.
3. `tasks.peek()` returns whatever's at the root of the (now-stale) heap — `review`, since the heap still "believes" priority 2 is the current minimum, unaware that `deploy`'s priority field has since dropped to 1.
4. `tasks.remove(deploy)` performs a linear scan through the heap's internal array to locate the exact `deploy` object (by `equals()`, or here effectively by reference since `Task` doesn't override `equals()`), removes it, and re-heapifies the remaining elements to restore the heap property without it.
5. `tasks.offer(deploy)` re-inserts the same `deploy` object as a fresh element — this time, the heap correctly reads its *current* priority field (`1`) and sifts it up to the root, since `1` is now smaller than both `review`'s `2` and `docs`'s `5`.
6. `tasks.peek()` now correctly returns `deploy`, and the subsequent `poll()` loop correctly drains the queue in true priority order: `deploy` (1), `review` (2), `docs` (5) — confirming the remove-then-re-offer pattern successfully corrected the stale heap position.

## 7. Gotchas & takeaways

> **Gotcha:** mutating an object's priority-determining field while it's already inside a `PriorityQueue` does **not** automatically reposition it in the heap — the queue has no change-notification mechanism. The only correct fix with the standard library's `PriorityQueue` is to `remove()` the element and `offer()` it again, which is O(n) for the removal (finding the element) plus O(log n) for the re-insertion. For workloads with frequent priority changes, a specialized "indexed priority queue" (tracking each element's array position for O(log n) updates) is a better fit than plain `PriorityQueue`, though it isn't provided by the standard library.

- `PriorityQueue` is backed by a binary heap stored in a plain array — `peek()` is O(1) (always the current minimum/root), `offer`/`poll` are O(log n).
- Iteration order (a plain for-each loop, or `toString()`) is **not** sorted — only the repeated `poll()` sequence is guaranteed to come out in priority order.
- A custom `Comparator` lets `PriorityQueue` order any object type; natural ordering (`Comparable`) is used if no comparator is supplied.
- Mutating an already-queued element's priority-determining field does not automatically re-sift it — `remove()` then `offer()` again is the standard workaround.
- Reach for `PriorityQueue` for "always process the current minimum/highest-priority item next" workloads — task scheduling, event simulation, and graph algorithms like Dijkstra's shortest path all use exactly this access pattern.
