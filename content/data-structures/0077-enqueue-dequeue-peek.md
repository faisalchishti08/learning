---
card: data-structures
gi: 77
slug: enqueue-dequeue-peek
title: enqueue / dequeue / peek
---

## 1. What it is

`enqueue`, `dequeue`, and `peek` are the three core operations of a queue. `enqueue` adds a value at the tail. `dequeue` removes and returns the value at the head. `peek` returns the head value without removing it. All three run in **O(1)** constant time, the same complexity guarantee as a stack's `push`/`pop`/`peek`, just applied to opposite ends.

## 2. Why & when

Understanding exactly why these are O(1) lets you reason correctly about the complexity of any queue-based algorithm — breadth-first search, task scheduling, or a producer-consumer pipeline. Whenever a problem needs "process items in the order they arrived, in constant time per item," a queue with these three operations is the tool.

## 3. Core concept

**Why `enqueue` is O(1).** On a circular-array-backed queue, `enqueue` writes to `data[tail]` and advances `tail` (wrapping with modulo) — one array write, one arithmetic update, regardless of how many elements are already queued. On a linked queue, `enqueue` allocates one node and links it after the current tail.

**Why `dequeue` is O(1).** `dequeue` reads `data[head]`, then advances `head` (array-backed), or reads `head.value` then reassigns `head = head.next` (linked). Either way, exactly one slot or node is touched — never a scan, never a shift of other elements.

**Why `peek` is O(1).** `peek` reads the value at the known head position without changing anything — no search needed, since the head is always tracked directly.

**The contrast that makes this concrete.** Compare to removing from the *front* of an `ArrayList`: every remaining element must shift one slot left, an O(n) operation. A properly implemented queue never does this, because both ends are tracked directly (a circular array's `head`/`tail` indices, or a linked list's head/tail node references).

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three operations on a two element queue: enqueue writes one new tail slot, dequeue reads and removes the head slot, peek reads the head slot without removing it">
  <g font-family="sans-serif" font-size="11">
    <rect x="30" y="30" width="40" height="26" fill="#0d1117" stroke="#f0883e"/><text x="50" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <rect x="70" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="90" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">20</text>
    <text x="50" y="20" fill="#f0883e" text-anchor="middle" font-size="9">head</text>

    <text x="180" y="20" fill="#79c0ff">enqueue(30)</text>
    <rect x="160" y="30" width="40" height="26" fill="#0d1117" stroke="#f0883e"/><text x="180" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <rect x="200" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="220" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">20</text>
    <rect x="240" y="30" width="40" height="26" fill="#161b22" stroke="#79c0ff"/><text x="260" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">30</text>
    <text x="220" y="75" fill="#79c0ff" text-anchor="middle" font-size="9">1 write at tail, O(1)</text>

    <text x="360" y="20" fill="#f0883e">dequeue() -&gt; 10</text>
    <rect x="360" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="380" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">20</text>
    <text x="380" y="75" fill="#f0883e" text-anchor="middle" font-size="9">1 read + advance head, O(1)</text>

    <text x="500" y="20" fill="#a5d6ff">peek() -&gt; 20</text>
    <rect x="500" y="30" width="40" height="26" fill="#0d1117" stroke="#a5d6ff"/><text x="520" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">20</text>
    <text x="520" y="75" fill="#a5d6ff" text-anchor="middle" font-size="9">1 read, nothing removed</text>
  </g>
</svg>

Each operation touches exactly one end's known position — never any middle element — which is why all three cost the same regardless of queue size.

## 5. Runnable example

```java
// EnqueueDequeuePeekDemo.java
import java.util.ArrayDeque;
import java.util.Deque;

public class EnqueueDequeuePeekDemo {

    // Basic: the three operations via java.util.ArrayDeque used as a queue.
    static void basicLevel() {
        Deque<Integer> queue = new ArrayDeque<>();
        queue.offer(10); // enqueue
        queue.offer(20);
        System.out.println("basic: peek -> " + queue.peek()); // 10, unchanged after
        System.out.println("basic: dequeue -> " + queue.poll()); // 10, removed
        System.out.println("basic: peek after dequeue -> " + queue.peek()); // 20
    }

    // Intermediate: a minimal custom circular-array queue, making the O(1) cost explicit.
    static class TinyQueue<T> {
        private Object[] data = new Object[8];
        private int head = 0, tail = 0, size = 0;

        void enqueue(T value) {
            data[tail] = value;
            tail = (tail + 1) % data.length; // one write, one wrapping increment
            size++;
        }

        @SuppressWarnings("unchecked")
        T dequeue() {
            if (size == 0) throw new IllegalStateException("empty");
            T value = (T) data[head];
            data[head] = null;
            head = (head + 1) % data.length; // one read, one wrapping increment
            size--;
            return value;
        }

        @SuppressWarnings("unchecked")
        T peek() {
            if (size == 0) throw new IllegalStateException("empty");
            return (T) data[head]; // one read, nothing changes
        }
    }

    static void intermediateLevel() {
        TinyQueue<String> queue = new TinyQueue<>();
        queue.enqueue("x");
        queue.enqueue("y");
        queue.enqueue("z");
        System.out.println("intermediate: peek -> " + queue.peek());
        System.out.println("intermediate: dequeue -> " + queue.dequeue());
        System.out.println("intermediate: dequeue -> " + queue.dequeue());
        System.out.println("intermediate: peek -> " + queue.peek());
    }

    // Advanced: confirm operation cost stays flat as size grows, by timing peek at small vs large size.
    static void advancedLevel() {
        Deque<Integer> small = new ArrayDeque<>();
        small.offer(1);
        Deque<Integer> large = new ArrayDeque<>();
        for (int i = 0; i < 1_000_000; i++) large.offer(i);

        long t0 = System.nanoTime();
        for (int i = 0; i < 100_000; i++) small.peek();
        long smallNs = System.nanoTime() - t0;

        long t1 = System.nanoTime();
        for (int i = 0; i < 100_000; i++) large.peek();
        long largeNs = System.nanoTime() - t1;

        System.out.println("advanced: 100k peeks on size-1 queue -> " + smallNs + " ns");
        System.out.println("advanced: 100k peeks on size-1,000,000 queue -> " + largeNs + " ns (roughly the same order of magnitude)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `EnqueueDequeuePeekDemo.java`, then run `java EnqueueDequeuePeekDemo.java`.

## 6. Walkthrough

1. `basicLevel()` enqueues `10`, then `20`. `peek()` returns `10` (the head) and leaves the queue unchanged. `poll()` (dequeue) returns `10` and removes it, leaving only `20`. A second `peek()` confirms the new head is `20`.
2. `intermediateLevel()`'s `TinyQueue` makes the mechanics explicit: `enqueue` writes to `data[tail]`, then advances `tail` with wraparound. `dequeue` reads `data[head]`, then advances `head` the same way. `peek` performs the same read as `dequeue` but skips the advance.
3. `advancedLevel()` times `peek()` on a queue of size `1` versus size `1,000,000`. Both take roughly the same total time for 100,000 calls, confirming the operation does not slow down as the queue grows — the defining property of O(1).

## 7. Gotchas & takeaways

> Gotcha: on a linked-list-backed queue, forgetting to update the `tail` reference (not just `head`) after removing the last remaining element leaves `tail` pointing at a now-detached node — the next `enqueue` would link a new node after a dangling reference. Always check for the single-element case explicitly when both `head` and `tail` must be reset.

- `enqueue`, `dequeue`, and `peek` are all O(1) because they only touch the single head or tail position, tracked directly.
- This contrasts with front-removal on an `ArrayList`, which is O(n) because it must shift every remaining element.
- Always check `isEmpty()` before `dequeue()`/`peek()`, or be ready to handle the exception/`null` your chosen API returns.
- Related concepts: [FIFO semantics](0072-fifo-semantics.md), [offer / poll vs add / remove semantics](0078-offer-poll-vs-add-remove-semantics.md).
