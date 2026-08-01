---
card: data-structures
gi: 75
slug: priority-queue-concept
title: Priority queue concept
---

## 1. What it is

A **priority queue** is a queue where each element has a priority, and removal always returns the element with the highest priority — not the one that arrived first. "Highest priority" usually means smallest value (a **min-priority-queue**) or largest value (a **max-priority-queue**), depending on the comparator used. Unlike a plain queue, arrival order plays no role at all.

## 2. Why & when

Use a priority queue whenever you repeatedly need "the current smallest/largest item, then the next one, then the next" — Dijkstra's shortest-path algorithm, task schedulers that run the most urgent job next, or merging several sorted streams. It is the right structure specifically because it gives O(log n) insert and O(log n) removal-of-the-best, far better than sorting the whole collection (O(n log n)) every time the best element changes.

## 3. Core concept

**The invariant: removal always returns the current extreme.** A priority queue does not promise any order among the other elements — only that `peek()`/`poll()` gives you whichever element currently has the best priority. Internally, this is usually implemented with a **binary heap** (covered separately as its own structure), which keeps a partial order sufficient to find the extreme quickly, without fully sorting everything.

**Why a binary heap makes this fast.** A heap keeps a much weaker invariant than full sorting — only "a parent is never worse than its children" — which is enough to guarantee the best element sits at the root, findable in O(1), while insertion and removal cost only O(log n) to restore the heap invariant, instead of O(n log n) to keep everything fully sorted.

**Comparator-driven priority.** "Priority" is whatever a `Comparator` (or natural ordering, via `Comparable`) says it is — smallest number first, earliest deadline first, shortest string first, or a custom multi-field rule. The priority queue itself does not know or care what the values represent; it only trusts the comparator.

## 4. Diagram

<svg viewBox="0 0 500 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A min priority queue holding values 5, 8, 3, 9, always returning the smallest value 3 first regardless of insertion order">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="18" fill="#8b949e">inserted in order: 5, 8, 3, 9</text>
    <rect x="20" y="40" width="46" height="26" fill="#161b22" stroke="#8b949e"/><text x="43" y="57" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>
    <rect x="70" y="40" width="46" height="26" fill="#161b22" stroke="#8b949e"/><text x="93" y="57" fill="#e6edf3" text-anchor="middle" font-size="9">8</text>
    <rect x="120" y="40" width="46" height="26" fill="#0d1117" stroke="#f0883e"/><text x="143" y="57" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <rect x="170" y="40" width="46" height="26" fill="#161b22" stroke="#8b949e"/><text x="193" y="57" fill="#e6edf3" text-anchor="middle" font-size="9">9</text>
    <text x="120" y="85" fill="#f0883e" text-anchor="middle" font-size="9">smallest, not oldest -- poll() returns 3 first</text>
    <text x="120" y="130" fill="#79c0ff" text-anchor="middle" font-size="9">poll order: 3, 5, 8, 9 (sorted, not arrival order)</text>
  </g>
</svg>

Insertion order was `5, 8, 3, 9`; removal order is `3, 5, 8, 9` — always the current smallest, regardless of when it arrived.

## 5. Runnable example

```java
// PriorityQueueConceptDemo.java
import java.util.Comparator;
import java.util.PriorityQueue;

public class PriorityQueueConceptDemo {

    // Basic: min-priority-queue by natural ordering -- always returns the smallest remaining value.
    static void basicLevel() {
        PriorityQueue<Integer> pq = new PriorityQueue<>(); // min-heap by default
        pq.offer(5);
        pq.offer(8);
        pq.offer(3);
        pq.offer(9);
        StringBuilder order = new StringBuilder();
        while (!pq.isEmpty()) order.append(pq.poll()).append(" ");
        System.out.println("basic: poll order -> " + order.toString().trim() + " (sorted ascending, not insertion order)");
    }

    // Intermediate: max-priority-queue via a reversed comparator, and priority on custom objects.
    record Task(String name, int urgency) {}

    static void intermediateLevel() {
        PriorityQueue<Integer> maxHeap = new PriorityQueue<>(Comparator.reverseOrder());
        maxHeap.offer(5);
        maxHeap.offer(8);
        maxHeap.offer(3);
        System.out.println("intermediate: max-heap poll order -> " + maxHeap.poll() + ", " + maxHeap.poll() + ", " + maxHeap.poll());

        PriorityQueue<Task> tasks = new PriorityQueue<>(Comparator.comparingInt(Task::urgency).reversed());
        tasks.offer(new Task("email", 2));
        tasks.offer(new Task("outage", 9));
        tasks.offer(new Task("standup", 1));
        System.out.println("intermediate: most urgent task first -> " + tasks.poll().name());
    }

    // Advanced: a simple event scheduler -- always process the event with the earliest timestamp next.
    record Event(String description, int timestamp) {}

    static void advancedLevel() {
        PriorityQueue<Event> schedule = new PriorityQueue<>(Comparator.comparingInt(Event::timestamp));
        schedule.offer(new Event("send reminder", 300));
        schedule.offer(new Event("start meeting", 100));
        schedule.offer(new Event("send follow-up", 500));
        schedule.offer(new Event("close ticket", 200));

        StringBuilder processedOrder = new StringBuilder();
        while (!schedule.isEmpty()) {
            Event next = schedule.poll();
            processedOrder.append(next.description()).append(" @").append(next.timestamp()).append("; ");
        }
        System.out.println("advanced: processed in timestamp order -> " + processedOrder);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `PriorityQueueConceptDemo.java`, then run `java PriorityQueueConceptDemo.java`.

## 6. Walkthrough

1. `basicLevel()` inserts `5, 8, 3, 9` in that order, but `poll()` returns `3, 5, 8, 9` — sorted ascending, completely independent of insertion order, because a min-priority-queue always surfaces the current smallest value.
2. `intermediateLevel()` flips the comparison with `Comparator.reverseOrder()` to get a max-heap (`8, 5, 3` — largest first). The `Task` example shows priority need not be the value itself: `Comparator.comparingInt(Task::urgency).reversed()` makes urgency the priority field, so `"outage"` (urgency 9) is polled before the lower-urgency tasks, even though it was inserted second.
3. `advancedLevel()` builds a tiny scheduler where each `Event` carries a timestamp. Even though events are inserted out of chronological order (`300, 100, 500, 200`), polling always returns the earliest remaining timestamp next: `100, 200, 300, 500` — exactly the processing order a real scheduler needs.

## 7. Gotchas & takeaways

> Gotcha: iterating a `PriorityQueue` directly (a `for-each` loop, or `toString()`) does **not** visit elements in priority order — only `poll()` (repeatedly) guarantees sorted output, since the internal heap array is only partially ordered, not fully sorted. Printing a `PriorityQueue` for debugging can be misleading for exactly this reason.

- A priority queue always removes the current best element (by whatever comparator you give it), ignoring arrival order entirely.
- It is typically implemented with a binary heap, giving O(log n) insert and O(log n) removal-of-the-best.
- The comparator defines "priority" — natural ordering, reversed, or a custom multi-field rule on domain objects.
- Never assume iteration order equals priority order; only repeated `poll()` guarantees sorted output.
- Related concepts: [java.util.PriorityQueue (binary heap)](0083-java-util-priorityqueue-binary-heap.md).
