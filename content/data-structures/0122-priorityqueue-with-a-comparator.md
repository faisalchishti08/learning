---
card: data-structures
gi: 122
slug: priorityqueue-with-a-comparator
title: PriorityQueue with a Comparator
---

## 1. What it is

`java.util.PriorityQueue` accepts a `Comparator` at construction time, which fully controls what "highest priority" means. This lets you build a priority queue over any type — not just numbers with a natural order — by composing comparisons across one or more fields, including tie-breaking rules.

## 2. Why & when

Real priority queues rarely sort by a single primitive value. A task scheduler might rank by urgency, then by earliest deadline as a tiebreaker; a "cheapest flight" search might rank by price, then by duration. `Comparator.comparing` and `.thenComparing` let you express exactly this kind of multi-field priority, cleanly, without writing a custom `compareTo` method on the domain class itself.

## 3. Core concept

**What backs it.** The same array-based binary heap as always — supplying a `Comparator` changes only which comparison function every internal sift-up/sift-down uses; the heap's structure and complexity guarantees (`O(log n)` insert/poll, `O(1)` peek) are unaffected.

**Composing comparisons.** `Comparator.comparing(Type::field)` builds a comparator from a single field (using its natural order). `.thenComparing(Type::otherField)` adds a tiebreaker, applied only when the first comparison returns equal. `.reversed()` flips a comparator's direction — useful for turning an ascending rule into "highest first."

**Updating an element's priority.** `PriorityQueue` has no `decrease-key` operation — you cannot change an element in place and expect the heap to notice. The standard workaround: `remove(element)` (an `O(n)` linear scan to find it, then `O(log n)` to fix the heap), mutate the value, then `offer` it back in. For workloads with frequent priority updates, this `O(n)` removal cost is the reason graph algorithms like Dijkstra's sometimes use an indexed heap instead.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three tasks compared first by urgency descending, then by deadline ascending as a tiebreaker, producing a single priority order">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="20" fill="#8b949e">tasks: (urgency, deadline)</text>
    <rect x="20" y="35" width="180" height="30" fill="#161b22" stroke="#8b949e"/><text x="110" y="54" fill="#e6edf3" text-anchor="middle" font-size="9">A: urgency=5, deadline=200</text>
    <rect x="20" y="75" width="180" height="30" fill="#161b22" stroke="#8b949e"/><text x="110" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">B: urgency=5, deadline=100</text>
    <rect x="20" y="115" width="180" height="30" fill="#161b22" stroke="#8b949e"/><text x="110" y="134" fill="#e6edf3" text-anchor="middle" font-size="9">C: urgency=9, deadline=300</text>
    <text x="300" y="60" fill="#8b949e" font-size="9">comparingInt(urgency).reversed()</text>
    <text x="300" y="90" fill="#8b949e" font-size="9">.thenComparingInt(deadline)</text>
    <rect x="420" y="35" width="180" height="30" fill="#0d1117" stroke="#f0883e"/><text x="510" y="54" fill="#e6edf3" text-anchor="middle" font-size="9">1st: C (highest urgency)</text>
    <rect x="420" y="75" width="180" height="30" fill="#0d1117" stroke="#79c0ff"/><text x="510" y="94" fill="#e6edf3" text-anchor="middle" font-size="9">2nd: B (tie broken by deadline)</text>
    <rect x="420" y="115" width="180" height="30" fill="#0d1117" stroke="#79c0ff"/><text x="510" y="134" fill="#e6edf3" text-anchor="middle" font-size="9">3rd: A</text>
  </g>
</svg>

`A` and `B` tie on urgency (`5`), so the tiebreaker (earlier deadline first) decides `B` comes before `A`; `C`'s higher urgency (`9`) always wins the primary comparison regardless of its deadline.

## 5. Runnable example

```java
// PriorityQueueComparatorDemo.java
import java.util.Comparator;
import java.util.PriorityQueue;

public class PriorityQueueComparatorDemo {

    record Task(String name, int urgency, int deadline) {}

    // Basic: a single-field comparator, ranking by urgency descending (highest urgency first).
    static void basicLevel() {
        PriorityQueue<Task> queue = new PriorityQueue<>(Comparator.comparingInt(Task::urgency).reversed());
        queue.offer(new Task("email", 3, 500));
        queue.offer(new Task("outage", 9, 300));
        queue.offer(new Task("standup", 1, 100));

        System.out.println("basic: highest-urgency task -> " + queue.poll().name());
    }

    // Intermediate: two-field comparator -- urgency descending, then deadline ascending as a tiebreaker.
    static void intermediateLevel() {
        PriorityQueue<Task> queue = new PriorityQueue<>(
            Comparator.comparingInt(Task::urgency).reversed()
                      .thenComparingInt(Task::deadline));

        queue.offer(new Task("A", 5, 200));
        queue.offer(new Task("B", 5, 100)); // ties A on urgency, wins on earlier deadline
        queue.offer(new Task("C", 9, 300)); // highest urgency, wins outright

        StringBuilder order = new StringBuilder();
        while (!queue.isEmpty()) order.append(queue.poll().name()).append(" ");
        System.out.println("intermediate: poll order -> " + order.toString().trim() + " (expected: C B A)");
    }

    // Advanced: updating an element's priority -- PriorityQueue has no decrease-key, so remove + mutate + re-offer.
    static void advancedLevel() {
        PriorityQueue<Task> queue = new PriorityQueue<>(Comparator.comparingInt(Task::urgency).reversed());
        Task standup = new Task("standup", 1, 100);
        queue.offer(standup);
        queue.offer(new Task("email", 3, 500));

        System.out.println("advanced: before update, top task -> " + queue.peek().name());

        queue.remove(standup);                          // O(n) linear scan to find it, then O(log n) to fix the heap
        Task escalated = new Task("standup", 10, 100);   // "mutate" -- records are immutable, so build a new value
        queue.offer(escalated);                          // O(log n) re-insert

        System.out.println("advanced: after escalating standup's urgency to 10, top task -> " + queue.peek().name());
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `PriorityQueueComparatorDemo.java`, then run `java PriorityQueueComparatorDemo.java`.

## 6. Walkthrough

1. `basicLevel()` builds a queue with `Comparator.comparingInt(Task::urgency).reversed()` — natural order on `urgency` is ascending, so `.reversed()` makes the *largest* urgency count as "smallest" internally, which is what `PriorityQueue`'s min-heap semantics need to put it first. Polling returns `"outage"` (urgency `9`), the most urgent task.
2. `intermediateLevel()` chains `.thenComparingInt(Task::deadline)` after the reversed urgency comparator. Tasks `A` and `B` both have urgency `5`, so the primary comparison returns equal, and the tiebreaker compares their deadlines (`200` vs `100`); `B`'s earlier deadline sorts it first between the two. `C`'s urgency (`9`) beats both outright, so the poll order is `C, B, A`.
3. `advancedLevel()` shows the standard priority-update workaround. `"standup"` starts at urgency `1` (lowest priority) and is not the top task. To escalate it, the code removes the old `Task` object (an `O(n)` scan, since `PriorityQueue` does not track element positions by content), builds a new `Task` record with urgency `10`, and re-offers it. After this, `peek()` correctly reflects the escalated task as the new top priority.

## 7. Gotchas & takeaways

> Gotcha: `PriorityQueue.remove(Object)` is `O(n)`, not `O(log n)` — it must linearly scan the internal array to find the matching element first, since the heap has no index mapping from value to array position. Repeatedly updating priorities this way on a large queue can dominate your program's running time; an indexed heap (tracking each element's array position in a side map) fixes this but is not built into `java.util`.

- A `Comparator` fully controls "priority" — compose `Comparator.comparing(...).reversed().thenComparing(...)` for multi-field rules with tiebreakers.
- The heap's complexity guarantees (`O(log n)` insert/poll) are unaffected by which comparator you use.
- `PriorityQueue` has no built-in decrease-key; updating an element's priority requires `remove` (O(n)) then `offer` (O(log n)).
- Related concepts: [Priority queue concept](0075-priority-queue-concept.md), [java.util.PriorityQueue (binary heap)](0083-java-util-priorityqueue-binary-heap.md).
