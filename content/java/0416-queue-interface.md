---
card: java
gi: 416
slug: queue-interface
title: Queue interface
---

## 1. What it is

`Queue<E>`, added to the Collections Framework in Java 5, models a **first-in-first-out (FIFO)** collection — elements are added at the tail and removed from the head. It defines two parallel sets of methods with different failure behaviour: `add()`/`remove()`/`element()` throw an exception if the operation can't be performed (queue full or empty), while `offer()`/`poll()`/`peek()` return a special value (`false`/`null`) instead. `LinkedList` and `ArrayDeque` are the two most common general-purpose implementations; `PriorityQueue` is a notable variant that orders elements by priority rather than strict insertion order.

## 2. Why & when

Before `Queue`, `LinkedList` alone already supported adding to one end and removing from the other, but there was no dedicated interface capturing "FIFO collection" as a concept, and no standard vocabulary for the operations. `Queue` formalizes this and, importantly, gives you a choice between two failure modes for the same logical operation: throwing (`add`/`remove`) when a full or empty queue is a genuine programming error you want to catch loudly, versus a calm boolean/`null` return (`offer`/`poll`) when an empty or full queue is an entirely expected, routine condition to check for.

You reach for `Queue` any time you need ordered processing — a task queue processed in arrival order, a breadth-first-search frontier, or a simple buffer between producer and consumer code within a single thread (for actual thread-safe queues shared across threads, see `BlockingQueue` and `ConcurrentLinkedQueue`, covered earlier in this series — this `Queue` interface itself is not thread-safe).

## 3. Core concept

```java
import java.util.*;

Queue<String> queue = new LinkedList<>();

queue.offer("task-1"); // add to the tail -- returns false instead of throwing if it can't (rare for LinkedList)
queue.offer("task-2");

String head = queue.peek();  // look at the head WITHOUT removing it -- null if empty
String next = queue.poll();  // remove and return the head -- null if empty

// The throwing equivalents:
queue.add("task-3");     // throws IllegalStateException if it can't be added (capacity-bounded queues only)
String x = queue.element(); // throws NoSuchElementException if empty
String y = queue.remove();  // throws NoSuchElementException if empty
```

For an unbounded queue like `LinkedList`, `add()` and `offer()` behave identically (adding never fails) — the real difference shows up with `remove()`/`poll()` and `element()`/`peek()` on an **empty** queue, where the throwing and non-throwing pairs diverge.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Queue adds at the tail and removes from the head; offer/poll return special values on failure, add/remove throw exceptions">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#e6edf3" font-size="11" font-family="sans-serif">head                                                    tail</text>
  <rect x="30" y="35" width="60" height="30" fill="#1c2430" stroke="#6db33f"/><text x="60" y="55" fill="#6db33f" font-size="10" text-anchor="middle">task-1</text>
  <rect x="95" y="35" width="60" height="30" fill="#1c2430" stroke="#6db33f"/><text x="125" y="55" fill="#6db33f" font-size="10" text-anchor="middle">task-2</text>
  <rect x="160" y="35" width="60" height="30" fill="#1c2430" stroke="#6db33f"/><text x="190" y="55" fill="#6db33f" font-size="10" text-anchor="middle">task-3</text>
  <line x1="30" y1="75" x2="30" y2="90" stroke="#79c0ff" marker-end="url(#aq1)"/>
  <text x="30" y="105" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">poll()/remove()</text>
  <line x1="250" y1="90" x2="220" y2="60" stroke="#f85149" marker-end="url(#aq2)"/>
  <text x="270" y="105" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">offer()/add()</text>

  <text x="320" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">On an empty queue: poll()/peek() return null; remove()/element() throw</text>
  <defs><marker id="aq1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker><marker id="aq2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker></defs>
</svg>

New items join at the tail; `poll()`/`remove()` both take from the head, differing only in how they react to an empty queue.

## 5. Runnable example

Scenario: a simple print-job queue processed in arrival order — the same job queue, evolved from using `add`/`remove` (which throw on an empty queue, a real crash risk), through the safer `offer`/`poll` pair, to a `PriorityQueue` variant that processes urgent jobs first regardless of arrival order.

### Level 1 — Basic

```java
import java.util.*;

public class PrintQueueThrowing {
    public static void main(String[] args) {
        Queue<String> jobs = new LinkedList<>();
        jobs.add("document.pdf");
        jobs.add("photo.jpg");

        System.out.println(jobs.remove()); // "document.pdf"
        System.out.println(jobs.remove()); // "photo.jpg"
        System.out.println(jobs.remove()); // queue is now empty -- this THROWS NoSuchElementException
    }
}
```

**How to run:** `java PrintQueueThrowing.java`

The third `remove()` call, on an already-empty queue, throws `NoSuchElementException` and crashes the program — `remove()`/`element()` are meant for situations where an empty queue truly is an unexpected error, not a routine possibility you need to check for first.

### Level 2 — Intermediate

```java
import java.util.*;

public class PrintQueueSafe {
    public static void main(String[] args) {
        Queue<String> jobs = new LinkedList<>();
        jobs.offer("document.pdf");
        jobs.offer("photo.jpg");

        String job;
        while ((job = jobs.poll()) != null) { // poll() returns null on empty -- clean loop exit, no exception
            System.out.println("Printing: " + job);
        }
        System.out.println("No more jobs. Queue empty: " + jobs.isEmpty());
    }
}
```

**How to run:** `java PrintQueueSafe.java`

`poll()` returning `null` once the queue is empty makes for a natural drain loop with no risk of an uncaught exception — an empty queue is treated as a routine, expected condition rather than an error state.

### Level 3 — Advanced

```java
import java.util.*;

public class PrintQueuePriority {
    record Job(String name, int priority) { } // lower number = more urgent

    public static void main(String[] args) {
        Queue<Job> jobs = new PriorityQueue<>(Comparator.comparingInt(Job::priority));

        jobs.offer(new Job("newsletter.pdf", 5));
        jobs.offer(new Job("urgent-invoice.pdf", 1));
        jobs.offer(new Job("report.pdf", 3));
        jobs.offer(new Job("emergency-notice.pdf", 0));

        Job job;
        while ((job = jobs.poll()) != null) {
            System.out.println("Printing (priority " + job.priority() + "): " + job.name());
        }
    }
}
```

**How to run:** `java PrintQueuePriority.java`

Even though `"newsletter.pdf"` was added first, `PriorityQueue` doesn't preserve insertion (FIFO) order at all — it always returns the element with the **lowest** value per the given `Comparator` first, so the most urgent jobs print first regardless of when they were queued.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `jobs` is a `PriorityQueue<Job>` ordered by `priority` ascending (lower number = printed sooner). Four jobs are offered in this order: priority 5, then 1, then 3, then 0.

Internally, `PriorityQueue` maintains a binary heap, not a simple linked list — each `offer()` call inserts the new job and re-arranges the heap so the *minimum*-priority job is always efficiently accessible at the front, regardless of insertion order. After all four offers, the heap's internal array order doesn't correspond to insertion order at all, but `peek()`/`poll()` always correctly returns whichever job currently has the lowest `priority` value.

The `while` loop calls `jobs.poll()` repeatedly. The **first** `poll()` call returns the job with priority `0` — `"emergency-notice.pdf"` — even though it was the *last* one added, because `PriorityQueue` orders strictly by the comparator, never by arrival time. This is printed as `"Printing (priority 0): emergency-notice.pdf"`.

The **second** `poll()` call returns priority `1` — `"urgent-invoice.pdf"` (added second). The **third** returns priority `3` — `"report.pdf"` (added third). The **fourth** returns priority `5` — `"newsletter.pdf"` (added *first*, but printed *last*, since it has the highest, least-urgent priority number).

After the fourth `poll()`, the queue is empty; the fifth call to `poll()` returns `null`, and the `while` loop condition `(job = jobs.poll()) != null` becomes `false`, ending the loop.

Expected output:
```
Printing (priority 0): emergency-notice.pdf
Printing (priority 1): urgent-invoice.pdf
Printing (priority 3): report.pdf
Printing (priority 5): newsletter.pdf
```

## 7. Gotchas & takeaways

> `PriorityQueue`'s iterator (and its internal array) does **not** guarantee any particular order beyond "the head is always the minimum element" — only repeated `poll()` calls are guaranteed to return elements in priority order. Iterating a `PriorityQueue` directly with a `for-each` loop (rather than draining it via `poll()`) will visit elements in an unspecified, heap-internal order, not sorted order — a common and easy-to-miss mistake.

- `Queue` defines two parallel method families: `add`/`remove`/`element` (throw on failure) and `offer`/`poll`/`peek` (return a special value on failure) — prefer the `offer`/`poll`/`peek` family whenever an empty or full queue is a routine, expected condition.
- `LinkedList` and `ArrayDeque` are general-purpose FIFO implementations; `ArrayDeque` is usually preferred over `LinkedList` for pure queue/stack use, since it avoids per-node object overhead.
- `PriorityQueue` orders elements by a `Comparator` (or natural ordering) rather than insertion order — the head is always the "smallest" element per that ordering, not the oldest one.
- None of these `Queue` implementations are thread-safe — for a queue shared across threads, use `BlockingQueue` implementations or `ConcurrentLinkedQueue` instead.
- Draining a queue with a `while ((x = queue.poll()) != null)` loop is a common, clean idiom for "process everything currently in the queue."
