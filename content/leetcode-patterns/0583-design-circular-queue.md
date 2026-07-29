---
card: leetcode-patterns
gi: 583
slug: design-circular-queue
title: Design Circular Queue
---

## 1. What it is

Design a `MyCircularQueue` class with a fixed `capacity`, supporting `enQueue(val)` (add to the rear, `false` if full), `deQueue()` (remove from the front, `false` if empty), `Front()`, `Rear()`, `isEmpty()`, and `isFull()`. It reuses freed slots at the front by wrapping the read/write positions back to index `0` once they reach the end of the backing array — hence "circular." Example: `capacity=3`; `enQueue(1)`, `enQueue(2)`, `enQueue(3)` → queue is `[1,2,3]`, `enQueue(4)` → `false` (full); `deQueue()` → removes `1`; `enQueue(4)` → `true`, reusing the now-free slot.

## 2. Why & when

A plain array-backed queue that always removes from index `0` needs to shift every remaining element left on each `deQueue`, an O(n) operation. A circular buffer avoids shifting entirely: instead of moving elements, it moves two pointers, `front` and `rear`, and wraps them back to index `0` with the modulo operator once they run off the end of the fixed-size array — the freed slots at the front become available for future writes without ever being physically vacated and refilled by shifting.

## 3. Core concept

**Key idea:** back the queue with a fixed-size array of length `capacity`, plus a `front` index, a `size` counter, and the `capacity` itself (the `rear` index is derivable as `(front + size - 1) % capacity`, so it does not need its own separate stored field). Wraparound is just `index % capacity` after incrementing.

**Steps:**
1. `enQueue(val)`: if `isFull()`, return `false`. Otherwise, write `val` at index `(front + size) % capacity`, increment `size`, return `true`.
2. `deQueue()`: if `isEmpty()`, return `false`. Otherwise, advance `front = (front + 1) % capacity`, decrement `size`, return `true`.
3. `Front()` / `Rear()`: if empty, return `-1`. Otherwise, read `array[front]` / `array[(front + size - 1) % capacity]`.
4. `isEmpty()`: `size == 0`. `isFull()`: `size == capacity`.

**Why `size` (not comparing `front` and `rear` directly) disambiguates empty from full:** in a circular buffer, `front == rear` can mean either "the queue is empty" or "the queue is full" — both states look identical if you only track the two pointers. Storing `size` explicitly removes that ambiguity in one O(1) field, instead of the alternative fix of always leaving one array slot permanently unused.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A circular array of capacity 4 where front and rear wrap around using modulo arithmetic">
  <g font-family="sans-serif" font-size="12">
    <circle cx="350" cy="100" r="70" fill="none" stroke="#30363d"/>
    <rect x="315" y="20" width="70" height="30" fill="#161b22" stroke="#3fb950"/><text x="350" y="40" fill="#e6edf3" text-anchor="middle" font-size="11">idx 0</text>
    <rect x="395" y="80" width="70" height="30" fill="#161b22" stroke="#f0883e"/><text x="430" y="100" fill="#e6edf3" text-anchor="middle" font-size="11">idx 1</text>
    <rect x="315" y="150" width="70" height="30" fill="#161b22" stroke="#30363d"/><text x="350" y="170" fill="#e6edf3" text-anchor="middle" font-size="11">idx 2</text>
    <rect x="235" y="80" width="70" height="30" fill="#161b22" stroke="#79c0ff"/><text x="270" y="100" fill="#e6edf3" text-anchor="middle" font-size="11">idx 3</text>
    <text x="350" y="10" fill="#8b949e" text-anchor="middle" font-size="11">front</text>
    <text x="430" y="70" fill="#8b949e" text-anchor="middle" font-size="11">rear</text>
    <text x="350" y="188" fill="#79c0ff" text-anchor="middle" font-size="11">(front + size) % capacity wraps idx 3 -&gt; idx 0</text>
  </g>
</svg>

Enqueue writes to `(front + size) % capacity`; once that index reaches `capacity - 1`, adding one more wraps it back to `0` — no elements ever move.

## 5. Runnable example

**Level 1 — Brute force.** A plain array where `deQueue` shifts every remaining element one position left to keep the front always at index `0`. O(n) per `deQueue`.

**KEY INSIGHT:** instead of physically moving elements to keep the front at index `0`, let the front *index itself* move (and wrap via modulo) — the elements stay put, only the pointers change, making every operation O(1).

**Level 2 — Optimal.** Fixed-size array plus `front` index and `size` counter, modulo arithmetic for wraparound. O(1) per operation.

**Level 3 — Hardened.** Correctly disambiguates empty vs. full using `size` (not pointer equality), and correctly computes `Rear()` via `(front + size - 1) % capacity` rather than a separately tracked `rear` field that could drift out of sync.

```java
// MyCircularQueue.java
public class MyCircularQueue {

    private final int[] data;
    private final int capacity;
    private int front;
    private int size;

    public MyCircularQueue(int k) {
        capacity = k;
        data = new int[k];
        front = 0;
        size = 0;
    }

    public boolean enQueue(int value) {
        if (isFull()) return false;
        int writeIndex = (front + size) % capacity;
        data[writeIndex] = value;
        size++;
        return true;
    }

    public boolean deQueue() {
        if (isEmpty()) return false;
        front = (front + 1) % capacity;
        size--;
        return true;
    }

    public int Front() {
        return isEmpty() ? -1 : data[front];
    }

    public int Rear() {
        return isEmpty() ? -1 : data[(front + size - 1) % capacity];
    }

    public boolean isEmpty() {
        return size == 0;
    }

    public boolean isFull() {
        return size == capacity;
    }

    public static void main(String[] args) {
        MyCircularQueue q = new MyCircularQueue(3);
        System.out.println(q.enQueue(1)); // true
        System.out.println(q.enQueue(2)); // true
        System.out.println(q.enQueue(3)); // true
        System.out.println(q.enQueue(4)); // false, full
        System.out.println(q.Rear());     // 3
        System.out.println(q.isFull());   // true
        System.out.println(q.deQueue());  // true, removes 1
        System.out.println(q.enQueue(4)); // true, reuses index 0
        System.out.println(q.Rear());     // 4
    }
}
```

**How to run:** save as `MyCircularQueue.java`, then run `java MyCircularQueue.java`.

## 6. Walkthrough

Trace `capacity=3`; `enQueue(1)`, `enQueue(2)`, `enQueue(3)`, `deQueue()`, `enQueue(4)`:

| call | data array | front | size | note |
|---|---|---|---|---|
| enQueue(1) | [1,_,_] | 0 | 1 | write at (0+0)%3=0 |
| enQueue(2) | [1,2,_] | 0 | 2 | write at (0+1)%3=1 |
| enQueue(3) | [1,2,3] | 0 | 3 | write at (0+2)%3=2, now full |
| deQueue() | [1,2,3] | 1 | 2 | front advances to (0+1)%3=1; slot 0 is now free but not cleared |
| enQueue(4) | [4,2,3] | 1 | 3 | write at (1+2)%3=0, wraps and reuses slot 0 |

The value `1` at index `0` is never explicitly erased by `deQueue` — it is simply overwritten later when `enQueue(4)` wraps back around, which is safe because `size` and `front` together always define exactly which slots are "live."

## 7. Gotchas & takeaways

> Gotcha: tracking a separate `rear` field and incrementing it independently of `front`/`size` risks it drifting out of sync after several wraparounds — computing `Rear()` as `(front + size - 1) % capacity` on demand, from the two fields that are always correct, avoids that entire class of bug.

- Signal: "fixed-capacity queue/buffer that reuses freed slots" is the circular-buffer signal — avoid shifting elements by moving index pointers with modulo arithmetic instead.
- `size` (not pointer equality) is what disambiguates an empty buffer from a full one, since `front == rear` is ambiguous on its own.
- Related problems: Design Circular Deque (adds insertion/removal at both ends, using the same wraparound idea in both directions), Design Browser History (a different fixed-position-pointer idea, without wraparound).
