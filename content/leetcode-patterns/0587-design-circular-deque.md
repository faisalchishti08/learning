---
card: leetcode-patterns
gi: 587
slug: design-circular-deque
title: Design Circular Deque
---

## 1. What it is

Design a `MyCircularDeque` class with a fixed `capacity`, supporting `insertFront(val)`, `insertLast(val)`, `deleteFront()`, `deleteLast()` (each returns `false` if the deque is full, for insert, or empty, for delete), `getFront()`, `getRear()`, `isEmpty()`, and `isFull()`. Unlike [Design Circular Queue](0583-design-circular-queue.md), insertion and deletion are both supported at **either** end. Example: `capacity=3`; `insertLast(1)`, `insertLast(2)`, `insertFront(3)` → deque is `[3,1,2]`, `insertFront(4)` → `false` (full), `getRear()` → `2`, `isFull()` → `true`.

## 2. Why & when

This extends [Design Circular Queue](0583-design-circular-queue.md)'s wraparound trick to both ends: a fixed-size array with a `front` index and a `size` counter already supports O(1) rear-insert and front-delete via `(front + size) % capacity`; adding front-insert and rear-delete requires moving `front` *backward* through the array, which needs care because Java's `%` operator returns a negative result for a negative left operand.

## 3. Core concept

**Key idea:** keep the same fields as a circular queue — `front`, `size`, `capacity`, backing array — but now `front` can move in either direction. Moving forward uses `(front + 1) % capacity` as before; moving backward uses `(front - 1 + capacity) % capacity`, adding `capacity` before the modulo to keep the result non-negative.

**Steps:**
1. `insertFront(val)`: if full, return `false`. Otherwise, move `front` backward: `front = (front - 1 + capacity) % capacity`, write `val` there, increment `size`.
2. `insertLast(val)`: if full, return `false`. Otherwise, write `val` at `(front + size) % capacity`, increment `size` (identical to the circular queue's `enQueue`).
3. `deleteFront()`: if empty, return `false`. Otherwise, move `front` forward: `front = (front + 1) % capacity`, decrement `size` (identical to the circular queue's `deQueue`).
4. `deleteLast()`: if empty, return `false`. Otherwise, just decrement `size` — the "rear" slot is `(front + size - 1) % capacity`, so shrinking `size` by one alone removes it, no separate pointer to move.
5. `getFront()` / `getRear()`: same as the circular queue, reading `array[front]` / `array[(front + size - 1) % capacity]`, or `-1` if empty.

**Why `(front - 1 + capacity) % capacity`, not just `(front - 1) % capacity`:** Java's `%` follows the sign of the dividend — `-1 % 3` evaluates to `-1` in Java, not `2` as true modular arithmetic would give. Adding `capacity` before taking `%` guarantees the intermediate value is non-negative, so the result lands correctly in `[0, capacity)`.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="insertFront moves the front pointer backward with wraparound, while insertLast writes at front+size with wraparound">
  <g font-family="sans-serif" font-size="12">
    <rect x="30" y="50" width="70" height="35" fill="#161b22" stroke="#30363d"/><text x="65" y="72" fill="#e6edf3" text-anchor="middle" font-size="10">idx 0</text>
    <rect x="110" y="50" width="70" height="35" fill="#161b22" stroke="#3fb950"/><text x="145" y="72" fill="#e6edf3" text-anchor="middle" font-size="10">idx 1: 1</text>
    <rect x="190" y="50" width="70" height="35" fill="#161b22" stroke="#3fb950"/><text x="225" y="72" fill="#e6edf3" text-anchor="middle" font-size="10">idx 2: 2</text>
    <text x="145" y="30" fill="#8b949e" text-anchor="middle" font-size="11">front (before insertFront)</text>
    <line x1="65" y1="45" x2="65" y2="85" stroke="#f0883e" stroke-width="2" marker-end="url(#a9)"/>
    <text x="65" y="30" fill="#f0883e" text-anchor="middle" font-size="11">new front</text>
    <text x="65" y="110" fill="#f0883e" text-anchor="middle" font-size="10">3</text>
    <defs><marker id="a9" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker></defs>
    <text x="350" y="150" fill="#79c0ff" text-anchor="middle">insertFront(3): front moves from 1 to (1-1+3)%3=0, writes 3 there</text>
  </g>
</svg>

`insertFront` moves `front` one slot backward, wrapping with `+capacity` before `%` to avoid Java's negative-modulo behavior — `insertLast` never moves `front` at all.

## 5. Runnable example

**Level 1 — Brute force.** Use a `LinkedList` (Java's built-in doubly linked list) for O(1) operations at both ends, but with no fixed capacity check — this would need an extra manual size check on every insert, and lacks the array-based memory locality a true circular buffer offers, though it is functionally close.

**KEY INSIGHT:** the same fixed-array-plus-two-fields (`front`, `size`) design from a circular queue already supports both directions — front-insert only needs `front` to move backward instead of forward, and rear-delete needs no pointer movement at all, just shrinking `size`.

**Level 2 — Optimal.** Fixed-size array, `front` and `size` fields, backward wraparound via `+capacity` before `%`.

**Level 3 — Hardened.** Correctly handles the transition through index `0` in both directions, and correctly disambiguates empty vs. full using `size` rather than pointer comparison.

```java
// MyCircularDeque.java
public class MyCircularDeque {

    private final int[] data;
    private final int capacity;
    private int front;
    private int size;

    public MyCircularDeque(int k) {
        capacity = k;
        data = new int[k];
        front = 0;
        size = 0;
    }

    public boolean insertFront(int value) {
        if (isFull()) return false;
        front = (front - 1 + capacity) % capacity;
        data[front] = value;
        size++;
        return true;
    }

    public boolean insertLast(int value) {
        if (isFull()) return false;
        data[(front + size) % capacity] = value;
        size++;
        return true;
    }

    public boolean deleteFront() {
        if (isEmpty()) return false;
        front = (front + 1) % capacity;
        size--;
        return true;
    }

    public boolean deleteLast() {
        if (isEmpty()) return false;
        size--; // the old rear slot (front+size-1) is simply no longer counted
        return true;
    }

    public int getFront() {
        return isEmpty() ? -1 : data[front];
    }

    public int getRear() {
        return isEmpty() ? -1 : data[(front + size - 1) % capacity];
    }

    public boolean isEmpty() {
        return size == 0;
    }

    public boolean isFull() {
        return size == capacity;
    }

    public static void main(String[] args) {
        MyCircularDeque dq = new MyCircularDeque(3);
        System.out.println(dq.insertLast(1));  // true
        System.out.println(dq.insertLast(2));  // true
        System.out.println(dq.insertFront(3)); // true -> deque is [3,1,2]
        System.out.println(dq.insertFront(4)); // false, full
        System.out.println(dq.getRear());      // 2
        System.out.println(dq.isFull());       // true
    }
}
```

**How to run:** save as `MyCircularDeque.java`, then run `java MyCircularDeque.java`.

## 6. Walkthrough

Trace `capacity=3`; `insertLast(1)`, `insertLast(2)`, `insertFront(3)`:

| call | data array | front | size |
|---|---|---|---|
| insertLast(1) | [1,_,_] | 0 | 1 |
| insertLast(2) | [1,2,_] | 0 | 2 |
| insertFront(3) | front=(0-1+3)%3=2; write data[2]=3 -> [1,2,3] | 2 | 3 |

After `insertFront(3)`, logically the deque reads `[3,1,2]` starting from `front=2`: `data[2]=3`, `data[(2+1)%3=0]=1`, `data[(2+2)%3=1]=2` — matching the expected order, even though the physical array storage is `[1,2,3]`.

## 7. Gotchas & takeaways

> Gotcha: writing `front = (front - 1) % capacity` without adding `capacity` first breaks when `front == 0`, since Java's `%` returns `-1` (not `capacity - 1`) for `-1 % capacity` — always add `capacity` before taking the modulo when moving a circular index backward.

- Signal: "insert/remove at both ends of a fixed-capacity buffer" is the two-directional circular-buffer signal — reuse the circular queue's `front`/`size` fields, just allow `front` to move both ways.
- `deleteLast` needs no pointer movement at all; only `size` shrinks, since the rear is always derived as `(front + size - 1) % capacity`.
- Related problems: Design Circular Queue (the one-directional version this problem builds on).
