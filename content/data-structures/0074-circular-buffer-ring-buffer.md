---
card: data-structures
gi: 74
slug: circular-buffer-ring-buffer
title: Circular buffer / ring buffer
---

## 1. What it is

A **circular buffer** (or ring buffer) is a fixed-size array used as a queue, where the "end" wraps back around to index `0` once it runs past the last slot — like a clock face, where after `12` comes `1` again. It reuses the same fixed block of memory forever, instead of shifting elements or growing the array.

## 2. Why & when

Use a circular buffer whenever you need a fixed-capacity queue with O(1) enqueue and dequeue and no per-operation allocation — audio/video streaming buffers, producer-consumer pipelines with a bounded queue, or a "last N events" log that overwrites the oldest entry once full. It avoids both the O(n) shifting a plain array queue would need, and the per-element allocation a linked queue would need.

## 3. Core concept

**The structure's shape and invariants.** A circular buffer keeps a fixed-size array, a `head` index (next slot to read), a `tail` index (next slot to write), and a `size` counter (how many slots are currently filled). The invariant: both `head` and `tail` wrap using modulo arithmetic — `index = (index + 1) % capacity` — so they cycle through the array indefinitely without ever going out of bounds.

**How the invariant makes operations fast.** Because `head` and `tail` are tracked directly and wrap in O(1) via modulo, both `enqueue` (write at `tail`, advance `tail`) and `dequeue` (read at `head`, advance `head`) are O(1) — no shifting, no resizing, no allocation, ever.

**Full vs empty ambiguity.** When `head == tail`, that could mean the buffer is empty OR completely full — both look identical if you only compare the two indices. The `size` counter (or a dedicated `isFull` flag) resolves this ambiguity; without it, you cannot tell the two states apart.

## 4. Diagram

<svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A ring of six slots with head and tail pointers, where the tail wraps from the last slot back to slot zero after writing">
  <g font-family="sans-serif" font-size="11">
    <circle cx="200" cy="200" r="130" fill="none" stroke="#8b949e" stroke-dasharray="3,3"/>
    <circle cx="200" cy="70" r="22" fill="#0d1117" stroke="#f0883e"/><text x="200" y="74" fill="#e6edf3" text-anchor="middle" font-size="9">0</text>
    <circle cx="313" cy="135" r="22" fill="#161b22" stroke="#8b949e"/><text x="313" y="139" fill="#e6edf3" text-anchor="middle" font-size="9">1</text>
    <circle cx="313" cy="265" r="22" fill="#161b22" stroke="#8b949e"/><text x="313" y="269" fill="#e6edf3" text-anchor="middle" font-size="9">2</text>
    <circle cx="200" cy="330" r="22" fill="#0d1117" stroke="#79c0ff"/><text x="200" y="334" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <circle cx="87" cy="265" r="22" fill="#161b22" stroke="#8b949e"/><text x="87" y="269" fill="#e6edf3" text-anchor="middle" font-size="9">4</text>
    <circle cx="87" cy="135" r="22" fill="#161b22" stroke="#8b949e"/><text x="87" y="139" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>
    <text x="200" y="40" fill="#f0883e" text-anchor="middle" font-size="9">head = 0 (next to read)</text>
    <text x="200" y="365" fill="#79c0ff" text-anchor="middle" font-size="9">tail = 3 (next to write); after slot 5, tail wraps to 0</text>
  </g>
</svg>

Slots `0` through `5` form a ring; `tail` writes forward and wraps `5 -> 0` via `(tail + 1) % 6`, never needing to shift any existing element.

## 5. Runnable example

```java
// CircularBuffer.java
public class CircularBuffer<T> {
    private final Object[] data;
    private int head = 0; // index of the next element to read
    private int tail = 0; // index of the next free slot to write
    private int size = 0; // resolves the head==tail ambiguity (empty vs full)

    CircularBuffer(int capacity) {
        data = new Object[capacity];
    }

    boolean enqueue(T value) {
        if (size == data.length) return false; // full, caller must dequeue first (or grow, in a resizable variant)
        data[tail] = value;
        tail = (tail + 1) % data.length; // wrap around
        size++;
        return true;
    }

    @SuppressWarnings("unchecked")
    T dequeue() {
        if (size == 0) return null; // empty
        T value = (T) data[head];
        data[head] = null;
        head = (head + 1) % data.length; // wrap around
        size--;
        return value;
    }

    boolean isFull() { return size == data.length; }
    boolean isEmpty() { return size == 0; }

    // Basic: fill, drain, in order.
    static void basicLevel() {
        CircularBuffer<Integer> buffer = new CircularBuffer<>(3);
        System.out.println("basic: enqueue 1,2,3 -> " + buffer.enqueue(1) + "," + buffer.enqueue(2) + "," + buffer.enqueue(3));
        System.out.println("basic: enqueue 4 while full -> " + buffer.enqueue(4)); // false, no room
        System.out.println("basic: dequeue order -> " + buffer.dequeue() + ", " + buffer.dequeue() + ", " + buffer.dequeue());
    }

    // Intermediate: wrap around -- enqueue/dequeue enough times to cross the array boundary.
    static void intermediateLevel() {
        CircularBuffer<Integer> buffer = new CircularBuffer<>(3);
        buffer.enqueue(1);
        buffer.enqueue(2);
        buffer.dequeue(); // removes 1, frees a slot at the START of the backing array
        buffer.enqueue(3);
        buffer.enqueue(4); // tail wraps from index 2 back to index 0, reusing the freed slot
        StringBuilder sb = new StringBuilder();
        while (!buffer.isEmpty()) sb.append(buffer.dequeue()).append(" ");
        System.out.println("intermediate: after wraparound, dequeue order -> " + sb.toString().trim());
    }

    // Advanced: fixed-size "last N events" log that silently overwrites the oldest entry once full.
    static class LastNLog {
        private final CircularBuffer<String> buffer;

        LastNLog(int n) { buffer = new CircularBuffer<>(n); }

        void log(String event) {
            if (buffer.isFull()) buffer.dequeue(); // evict the oldest to make room
            buffer.enqueue(event);
        }
    }

    static void advancedLevel() {
        LastNLog log = new LastNLog(3);
        log.log("start");
        log.log("connect");
        log.log("send");
        log.log("receive"); // this evicts "start", the oldest entry

        System.out.println("advanced: log kept only the most recent 3 events (\"start\" was evicted)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `CircularBuffer.java`, then run `java CircularBuffer.java`.

## 6. Walkthrough

Trace `intermediateLevel()` on a capacity-3 buffer:

| Step | Action | head after | tail after | size after | backing array (index 0,1,2) |
|---|---|---|---|---|---|
| 1 | `enqueue(1)` writes index 0 | 0 | 1 | 1 | `[1, _, _]` |
| 2 | `enqueue(2)` writes index 1 | 0 | 2 | 2 | `[1, 2, _]` |
| 3 | `dequeue()` reads index 0 -> returns 1 | 1 | 2 | 1 | `[_, 2, _]` |
| 4 | `enqueue(3)` writes index 2, tail wraps 2->0 | 1 | 0 | 2 | `[_, 2, 3]` |
| 5 | `enqueue(4)` writes index 0, tail wraps 0->1 | 1 | 1 | 3 | `[4, 2, 3]` |

The final `dequeue` loop reads from `head = 1` forward, wrapping: `2`, then `3`, then `4` — the correct FIFO order, even though `4` physically sits at array index `0`, *before* `2` and `3` in raw memory layout. The wraparound is invisible to the caller; only `head`/`tail` arithmetic knows about it.

## 7. Gotchas & takeaways

> Gotcha: comparing only `head == tail` to detect "empty" is ambiguous, since a full buffer where `tail` has wrapped all the way back to `head` looks identical — always track a separate `size` (or a boolean `full` flag) to disambiguate the two states.

- A circular buffer reuses one fixed-size array forever, wrapping indices with `% capacity` instead of shifting elements or growing.
- `enqueue` and `dequeue` are both O(1), with zero allocation after the initial array is created.
- `head == tail` alone cannot distinguish empty from full; track `size` explicitly.
- Related concepts: [FIFO semantics](0072-fifo-semantics.md), [Array resizing / amortized append](0020-array-resizing-amortized-append.md) (the resizable-array alternative to a fixed-capacity ring buffer).
