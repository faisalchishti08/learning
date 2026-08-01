---
card: data-structures
gi: 72
slug: fifo-semantics
title: FIFO semantics
---

## 1. What it is

A **queue** is a data structure that adds elements at one end (the **tail**) and removes them from the other end (the **head**). This gives **FIFO** order: First In, First Out — the element that has been waiting longest is always the next one removed. Picture a line at a checkout counter: whoever joined first gets served first.

## 2. Why & when

FIFO order fits anything processed in arrival order: a task queue, a print spooler, a message queue, or breadth-first search (visiting nodes in the order they were discovered). Use a queue instead of a general list whenever "first arrived, first handled" is the rule your logic depends on — restricting access to enqueue-at-tail/dequeue-at-head prevents code from accidentally processing things out of order.

## 3. Core concept

**The invariant: insertion and removal happen at opposite ends.** A queue exposes `enqueue` (add at the tail), `dequeue` (remove from the head), and `peek` (look at the head without removing it). Because insertion and removal never touch the same end, the oldest element is always the one nearest the head, and it is always removed first.

**How the invariant makes operations fast.** As long as the structure tracks both a head and a tail position directly (an index into a circular array, or head/tail node references in a linked list), both `enqueue` and `dequeue` are O(1) — neither needs to shift or search, since each always targets a known, fixed position.

**FIFO vs LIFO.** A stack's `push`/`pop` touch the *same* end, giving Last In, First Out. A queue's `enqueue`/`dequeue` touch *opposite* ends, giving First In, First Out. This single difference — same end vs opposite ends — is the entire distinction between the two structures.

## 4. Diagram

<svg viewBox="0 0 560 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A queue of three people, with new arrivals joining the tail and service happening at the head, so first arrived is first served">
  <g font-family="sans-serif" font-size="11">
    <rect x="60" y="50" width="46" height="30" fill="#0d1117" stroke="#f0883e"/><text x="83" y="70" fill="#e6edf3" text-anchor="middle" font-size="9">1 (head)</text>
    <rect x="130" y="50" width="46" height="30" fill="#161b22" stroke="#8b949e"/><text x="153" y="70" fill="#e6edf3" text-anchor="middle" font-size="9">2</text>
    <rect x="200" y="50" width="46" height="30" fill="#161b22" stroke="#8b949e"/><text x="223" y="70" fill="#e6edf3" text-anchor="middle" font-size="9">3 (tail)</text>
    <line x1="55" y1="65" x2="20" y2="65" stroke="#f0883e" marker-end="url(#dq)"/>
    <text x="20" y="45" fill="#f0883e" font-size="9">dequeue -&gt; 1</text>
    <line x1="250" y1="65" x2="290" y2="65" stroke="#79c0ff" marker-end="url(#eq)"/>
    <text x="260" y="45" fill="#79c0ff" font-size="9">enqueue(4)</text>
    <defs>
      <marker id="dq" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker>
      <marker id="eq" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker>
    </defs>
  </g>
</svg>

Removal always happens at the head (oldest, `1`); insertion always happens at the tail — the two ends never mix.

## 5. Runnable example

```java
// FifoSemanticsDemo.java
import java.util.ArrayDeque;
import java.util.Deque;

public class FifoSemanticsDemo {

    // Basic: enqueue three values, observe FIFO dequeue order.
    static void basicLevel() {
        Deque<Integer> queue = new ArrayDeque<>(); // used as a queue via offer/poll, see topic 0081
        queue.offer(1);
        queue.offer(2);
        queue.offer(3);
        System.out.println("basic: dequeue order -> " + queue.poll() + ", " + queue.poll() + ", " + queue.poll());
    }

    // Intermediate: peek does not remove; mixing enqueue/dequeue preserves arrival order among remaining elements.
    static void intermediateLevel() {
        Deque<String> queue = new ArrayDeque<>();
        queue.offer("first");
        queue.offer("second");
        System.out.println("intermediate: peek (no removal) -> " + queue.peek());
        queue.poll(); // removes "first"
        queue.offer("third");
        System.out.println("intermediate: dequeue order after mixing -> " + queue.poll() + ", " + queue.poll());
    }

    // Advanced: simulate serving a line of customers in arrival order, to make FIFO concrete.
    static void advancedLevel() {
        Deque<String> line = new ArrayDeque<>();
        String[] arrivals = {"Alice", "Bob", "Cara"};
        for (String name : arrivals) line.offer(name);

        StringBuilder servedOrder = new StringBuilder();
        while (!line.isEmpty()) servedOrder.append(line.poll()).append(" ");

        System.out.println("advanced: service order -> " + servedOrder.toString().trim() + " (matches arrival order)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `FifoSemanticsDemo.java`, then run `java FifoSemanticsDemo.java`.

## 6. Walkthrough

1. `basicLevel()` enqueues `1`, `2`, `3` in that order, so `1` sits at the head. Three `poll()` calls return `1`, `2`, `3` — the exact same order they were enqueued in, which is the definition of FIFO.
2. `intermediateLevel()` enqueues `"first"`, then `"second"`; `peek()` reads `"first"` (the head) without removing it. `poll()` removes `"first"`, then `offer("third")` adds it at the tail, behind `"second"`. The final two polls return `"second"`, then `"third"` — order always follows arrival time among whatever remains.
3. `advancedLevel()` enqueues three names in arrival order and polls them all — the service order exactly matches the arrival order, confirming no one is served out of turn.

## 7. Gotchas & takeaways

> Gotcha: calling `poll()` or `peek()` on an empty queue returns `null` (for `Deque`'s poll-family methods) rather than throwing — a common bug is to treat that `null` as a valid queued value instead of "queue was empty." Always check `isEmpty()` first, or explicitly handle a `null` result.

- A queue restricts insertion to the tail and removal to the head, which is what guarantees FIFO order.
- `enqueue`, `dequeue`, and `peek` are all O(1) when both ends are tracked directly.
- FIFO (queue) and LIFO (stack) differ only in whether removal happens at the same end as insertion, or the opposite end.
- Related concepts: [LIFO semantics](0062-lifo-semantics.md), [ArrayDeque as queue & deque](0081-arraydeque-as-queue-deque.md).
