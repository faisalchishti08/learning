---
card: data-structures
gi: 78
slug: offer-poll-vs-add-remove-semantics
title: offer / poll vs add / remove semantics
---

## 1. What it is

Java's `Queue` interface offers two parallel sets of methods for the same operations: `offer`/`poll`/`peek` and `add`/`remove`/`element`. They do the same job — insert, remove, and look at the head — but differ in **how they report failure** when the queue cannot honor the request (full, for a bounded queue; or empty, for removal/inspection).

## 2. Why & when

Choosing the right pair matters because they fail differently: one family returns a sentinel value (`null` or `false`), the other throws an exception. Using the wrong one for your situation either forces awkward exception-catching for a routine "queue was empty" check, or silently swallows a bug that should have been loud. This distinction is specific to `java.util`'s collection design, and it is easy to use inconsistently without realizing it.

## 3. Core concept

**The two families, side by side.**

| Operation | Throws on failure | Returns a sentinel on failure |
|---|---|---|
| insert | `add(e)` — throws `IllegalStateException` if a bounded queue is full | `offer(e)` — returns `false` if full |
| remove | `remove()` — throws `NoSuchElementException` if empty | `poll()` — returns `null` if empty |
| examine | `element()` — throws `NoSuchElementException` if empty | `peek()` — returns `null` if empty |

**When to use which.** Use `offer`/`poll`/`peek` as the default — checking `isEmpty()` or a `null`/`false` return is cheap and reads naturally at a call site that expects "the queue might be empty right now" as a normal condition (like polling a work queue in a loop). Use `add`/`remove`/`element` when an empty or full queue would be a genuine bug you want to surface loudly and immediately, rather than silently continue past.

**Why `ArrayDeque` rarely uses `add`/`remove`'s failure path in practice.** `ArrayDeque` is unbounded (it resizes instead of rejecting inserts), so `add` never actually throws for being "full" — the throwing behavior only matters for bounded queue implementations. But `remove()`/`element()` still throw on an empty `ArrayDeque`, since emptiness is a real possible state regardless of capacity.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two parallel method families on an empty queue: remove and element throw NoSuchElementException, while poll and peek return null">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="18" fill="#8b949e">empty queue -- calling each removal/examine method:</text>
    <rect x="20" y="40" width="180" height="30" fill="#0d1117" stroke="#f0883e" rx="4"/><text x="110" y="60" fill="#e6edf3" text-anchor="middle" font-size="9">remove() / element()</text>
    <text x="110" y="90" fill="#f0883e" text-anchor="middle" font-size="9">throws NoSuchElementException</text>

    <rect x="260" y="40" width="180" height="30" fill="#0d1117" stroke="#79c0ff" rx="4"/><text x="350" y="60" fill="#e6edf3" text-anchor="middle" font-size="9">poll() / peek()</text>
    <text x="350" y="90" fill="#79c0ff" text-anchor="middle" font-size="9">returns null, no exception</text>

    <text x="230" y="140" fill="#8b949e" text-anchor="middle">same underlying queue, same empty state -- only the FAILURE REPORTING differs</text>
  </g>
</svg>

Both families do the identical operation when the queue has elements; they diverge only in how they signal failure.

## 5. Runnable example

```java
// OfferPollVsAddRemove.java
import java.util.ArrayDeque;
import java.util.NoSuchElementException;
import java.util.Queue;

public class OfferPollVsAddRemove {

    // Basic: normal (non-empty) use -- both families behave identically.
    static void basicLevel() {
        Queue<Integer> queue = new ArrayDeque<>();
        queue.offer(1);
        queue.add(2); // add works the same as offer when there is room
        System.out.println("basic: element() -> " + queue.element());
        System.out.println("basic: poll() -> " + queue.poll());
        System.out.println("basic: remove() -> " + queue.remove());
    }

    // Intermediate: the divergence on an EMPTY queue -- poll/peek return null, remove/element throw.
    static void intermediateLevel() {
        Queue<Integer> queue = new ArrayDeque<>();

        System.out.println("intermediate: poll() on empty -> " + queue.poll()); // null, no exception
        System.out.println("intermediate: peek() on empty -> " + queue.peek()); // null, no exception

        try {
            queue.remove();
        } catch (NoSuchElementException e) {
            System.out.println("intermediate: remove() on empty -> threw NoSuchElementException");
        }

        try {
            queue.element();
        } catch (NoSuchElementException e) {
            System.out.println("intermediate: element() on empty -> threw NoSuchElementException");
        }
    }

    // Advanced: a worker loop that SHOULD use poll (empty queue is a normal, expected state to check for).
    static void advancedLevel() {
        Queue<String> workQueue = new ArrayDeque<>();
        workQueue.offer("task-1");
        workQueue.offer("task-2");

        StringBuilder processed = new StringBuilder();
        String task;
        while ((task = workQueue.poll()) != null) { // poll's null return is the natural "no more work" signal
            processed.append(task).append(" ");
        }
        System.out.println("advanced: processed all work via poll loop -> " + processed.toString().trim());

        // contrast: using remove() here would require a try/catch just to detect "no more work" -- awkward for a routine condition
        System.out.println("advanced: using remove() for this loop would need a try/catch around a NORMAL, expected condition");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `OfferPollVsAddRemove.java`, then run `java OfferPollVsAddRemove.java`.

## 6. Walkthrough

1. `basicLevel()` shows both families behaving the same when the queue has elements — `add` and `offer` both succeed; `poll`/`element`/`remove` all return the head correctly. The difference only appears on failure.
2. `intermediateLevel()` empties the queue, then calls all four "read the head" style methods. `poll()` and `peek()` quietly return `null`. `remove()` and `element()` throw `NoSuchElementException`, caught here to demonstrate the behavior without crashing the program.
3. `advancedLevel()` shows the natural fit: a worker loop that drains a queue until empty. `poll()`'s `null` return doubles as the loop's exit condition, reading cleanly as `while ((task = workQueue.poll()) != null)`. Using `remove()` here would force wrapping the loop body in a `try`/`catch` just to detect a condition (queue empty) that is completely expected, not exceptional.

## 7. Gotchas & takeaways

> Gotcha: if the queue itself might legitimately hold `null` elements (which `LinkedList` allows, though `ArrayDeque` does not), `poll()`'s `null` return becomes ambiguous — you cannot tell "queue was empty" apart from "queue's head element was actually null." This is one more reason `ArrayDeque`'s null-rejection is a feature, not a limitation.

- `offer`/`poll`/`peek` fail by returning a sentinel (`false`/`null`); `add`/`remove`/`element` fail by throwing an exception.
- Prefer `offer`/`poll`/`peek` when an empty or full queue is a normal, expected condition to check for in a loop.
- Prefer `add`/`remove`/`element` when that condition should never happen, and you want a loud failure if it does.
- Related concepts: [enqueue / dequeue / peek](0077-enqueue-dequeue-peek.md), [ArrayDeque as queue & deque](0081-arraydeque-as-queue-deque.md).
