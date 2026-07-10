---
card: java
gi: 805
slug: queue
title: Queue
---

## 1. What it is

`Queue<T>` is the [`Collection`](0801-collection.md) subtype modeling a sequence designed for **holding elements prior to processing**, typically in first-in-first-out (FIFO) order. It adds insertion methods `offer(e)` (add at the tail, returns `false` on failure instead of throwing) and `add(e)` (throws on failure), removal methods `poll()` (remove and return the head, `null` if empty) and `remove()` (throws if empty), and inspection methods `peek()` (view the head without removing, `null` if empty) and `element()` (throws if empty). The two forms — `offer`/`poll`/`peek` (return a sentinel on failure) versus `add`/`remove`/`element` (throw on failure) — exist side by side so callers can choose whichever error-handling style fits. Common implementations include [`LinkedList`](0813-linkedlist-doubly-linked.md), [`ArrayDeque`](0834-arraydeque.md), and [`PriorityQueue`](0833-priorityqueue-binary-heap.md) (which reorders by priority rather than strict FIFO).

## 2. Why & when

Anything modeling "things waiting to be processed, one at a time, in arrival order" — print jobs, task schedulers, breadth-first search frontiers, event buffers — needs exactly the operations `Queue` provides and nothing more. A `List` *could* technically be used the same way (`add` at the end, `remove(0)` from the front), but `remove(0)` on an `ArrayList` is O(n) because every remaining element shifts left one slot; `Queue` implementations like `ArrayDeque` give O(1) at both ends by design. Reach for `Queue` whenever the access pattern is genuinely "add to one end, remove from the other" and you want the type itself to communicate that intent, rather than a `List` used in a queue-like way by convention.

## 3. Core concept

```java
Queue<String> printJobs = new LinkedList<>();
printJobs.offer("report.pdf");
printJobs.offer("invoice.pdf");

printJobs.peek();   // "report.pdf" — head, not removed
printJobs.poll();   // "report.pdf" — removed and returned
printJobs.poll();   // "invoice.pdf"
printJobs.poll();   // null — queue is empty, poll() never throws

printJobs.remove(); // throws NoSuchElementException — remove() DOES throw on empty
```

`offer`/`poll`/`peek` return `null` or `false` on an empty or full queue; `add`/`remove`/`element` throw instead. Pick the pair that matches how the calling code wants to handle the empty case.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Queue adds elements at the tail via offer and removes them from the head via poll, in first-in-first-out order">
  <text x="320" y="25" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">FIFO: head is processed first, tail is where new work joins</text>

  <g font-family="sans-serif">
    <rect x="220" y="55" width="90" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="265" y="85" fill="#e6edf3" font-size="10" text-anchor="middle">report.pdf</text>
    <text x="265" y="45" fill="#8b949e" font-size="9" text-anchor="middle">head</text>

    <rect x="320" y="55" width="90" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="365" y="85" fill="#e6edf3" font-size="10" text-anchor="middle">invoice.pdf</text>
    <text x="365" y="45" fill="#8b949e" font-size="9" text-anchor="middle">tail</text>
  </g>

  <line x1="220" y1="80" x2="150" y2="80" stroke="#f85149" stroke-width="2" marker-end="url(#a805a)"/>
  <text x="150" y="65" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">poll() removes here</text>

  <line x1="480" y1="80" x2="410" y2="80" stroke="#3fb950" stroke-width="2" marker-end="url(#a805b)"/>
  <text x="480" y="65" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">offer() adds here</text>

  <defs>
    <marker id="a805a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f85149"/></marker>
    <marker id="a805b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M6,0 L0,3 L6,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

*New work joins at the tail via `offer()`; the oldest waiting work leaves from the head via `poll()`.*

## 5. Runnable example

Scenario: a print-job queue, growing from basic FIFO processing to safe empty-queue handling to a polymorphic processor that works with any `Queue` implementation, FIFO or priority-based.

### Level 1 — Basic

```java
import java.util.*;

public class PrintQueueBasic {
    public static void main(String[] args) {
        Queue<String> printJobs = new LinkedList<>();
        printJobs.offer("report.pdf");
        printJobs.offer("invoice.pdf");
        printJobs.offer("photo.png");

        System.out.println("next up: " + printJobs.peek());

        while (!printJobs.isEmpty()) {
            System.out.println("printing: " + printJobs.poll());
        }
    }
}
```

**How to run:** `java PrintQueueBasic.java` (JDK 17+).

Expected output:
```
next up: report.pdf
printing: report.pdf
printing: invoice.pdf
printing: photo.png
```

Jobs print in the exact order they were offered — first in, first out. `peek()` confirms what `poll()` would return, without removing it.

### Level 2 — Intermediate

```java
import java.util.*;

public class PrintQueueSafe {
    public static void main(String[] args) {
        Queue<String> printJobs = new LinkedList<>();
        printJobs.offer("report.pdf");

        // poll()/peek() return null instead of throwing — safe to check directly.
        System.out.println(printJobs.poll());  // "report.pdf"
        System.out.println(printJobs.poll());  // null — queue is empty, no exception
        System.out.println(printJobs.peek());  // null

        // remove()/element() throw instead — useful when an empty queue IS a bug.
        try {
            printJobs.remove();
        } catch (NoSuchElementException e) {
            System.out.println("caught: queue was unexpectedly empty");
        }

        // offer() returns false on failure (e.g. a capacity-bounded queue that's full);
        // add() throws IllegalStateException in that same situation instead.
        Queue<String> bounded = new java.util.concurrent.ArrayBlockingQueue<>(1);
        bounded.offer("first.pdf");
        boolean accepted = bounded.offer("second.pdf"); // queue full, capacity 1
        System.out.println("second job accepted: " + accepted);
    }
}
```

**How to run:** `java PrintQueueSafe.java`.

Expected output:
```
report.pdf
null
null
caught: queue was unexpectedly empty
second job accepted: false
```

The real-world concern added: choosing between the **null-returning** pair (`poll`/`peek`, natural when "empty" is a normal, expected state) and the **throwing** pair (`remove`/`element`, natural when reaching an empty queue signals a bug the caller wants surfaced loudly) — plus `offer`'s graceful `false` return on a capacity-bounded queue that's full, versus `add`'s `IllegalStateException` in the same case.

### Level 3 — Advanced

```java
import java.util.*;

public class QueueProcessor {

    // Written against Queue<T> — works identically for strict FIFO or priority-based ordering.
    static void processAll(Queue<String> jobs) {
        while (!jobs.isEmpty()) {
            System.out.println("  processing: " + jobs.poll());
        }
    }

    public static void main(String[] args) {
        System.out.println("FIFO queue (arrival order):");
        Queue<String> fifo = new LinkedList<>(List.of("report.pdf", "invoice.pdf", "photo.png"));
        processAll(fifo);

        System.out.println("Priority queue (urgent jobs first, by name length as a stand-in priority):");
        Queue<String> priority = new PriorityQueue<>(Comparator.comparingInt(String::length));
        priority.offer("report.pdf");
        priority.offer("q.pdf");
        priority.offer("invoice.pdf");
        processAll(priority);
    }
}
```

**How to run:** `java QueueProcessor.java`.

Expected output:
```
FIFO queue (arrival order):
  processing: report.pdf
  processing: invoice.pdf
  processing: photo.png
Priority queue (urgent jobs first, by name length as a stand-in priority):
  processing: q.pdf
  processing: report.pdf
  processing: invoice.pdf
```

This adds the production-flavored hard case: the exact same `processAll` method, written once against the `Queue<String>` interface, produces **strict arrival order** when backed by `LinkedList` and **priority order** when backed by `PriorityQueue` — because `poll()` always removes "whatever the implementation considers next," and each implementation defines that differently. Code that only needs "give me the next thing to process" should depend on `Queue`, not on a specific implementation, so the ordering policy can change without touching the processing logic.

## 6. Walkthrough

Tracing `QueueProcessor.main`:

1. `fifo` is built as a `LinkedList` seeded with three job names in a specific order; `processAll(fifo)` loops `while (!jobs.isEmpty())`, calling `poll()` each time — for a `LinkedList`-backed `Queue`, `poll()` always removes the earliest-inserted remaining element, so the three names print in their original arrival order.
2. `priority` is built as a `PriorityQueue` with a `Comparator` ordering by string length ascending; three jobs are `offer`ed in a different order than they'll come out.
3. `processAll(priority)` runs the identical loop body as before — `poll()` on a `PriorityQueue` removes the **smallest** element according to its comparator (here, the shortest name), not the earliest-inserted one. `"q.pdf"` (5 characters) comes out first even though it was offered second, because the binary heap backing `PriorityQueue` always surfaces the minimum element at the head.
4. Because both `fifo` and `priority` are handled through the same `Queue<String>` parameter type in `processAll`, the method body never needed to know which ordering policy was in effect — that decision lives entirely in which concrete implementation was constructed.

## 7. Gotchas & takeaways

> **Gotcha:** `PriorityQueue`'s iteration order (via a plain for-each loop or `toString()`) is **not** sorted order — only repeated `poll()` calls are guaranteed to come out in priority order. Printing a `PriorityQueue` directly, or iterating it with a for-each loop, exposes its internal heap array layout, which looks unsorted.

- `Queue<T>` models FIFO-style (or priority-based) processing: `offer`/`poll`/`peek` are the null-returning, non-throwing trio; `add`/`remove`/`element` throw on failure instead.
- `poll()` and `peek()` return `null` on an empty queue — safe to call without a prior `isEmpty()` check, but be careful not to confuse a `null` element value with an empty queue if the queue can legitimately hold `null`s (most `Queue` implementations disallow `null` elements specifically to avoid this ambiguity).
- `LinkedList` gives strict FIFO; [`PriorityQueue`](0833-priorityqueue-binary-heap.md) reorders by a comparator so `poll()` always returns the current minimum, not the oldest arrival.
- Write processing code against the `Queue` interface so the ordering policy (FIFO vs. priority) can change by swapping the concrete implementation.
- Never rely on a `PriorityQueue`'s iteration order — only its `poll()` sequence is guaranteed to respect the comparator.
