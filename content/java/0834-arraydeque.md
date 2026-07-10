---
card: java
gi: 834
slug: arraydeque
title: ArrayDeque
---

## 1. What it is

`ArrayDeque` is a resizable-array implementation of [`Deque`](0806-deque.md), storing elements in a circular buffer — a fixed-size array where the "start" and "end" positions can wrap around from the last index back to the first, avoiding the need to shift existing elements when adding or removing at either end. This gives genuine O(1) (not amortized-with-shifting) insertion and removal at both the head and tail. The JDK explicitly documents `ArrayDeque` as likely faster than [`LinkedList`](0813-linkedlist-doubly-linked.md) for both queue and stack use cases, and as the recommended modern replacement for the legacy `Stack` class. It disallows `null` elements — inserting `null` throws `NullPointerException` immediately, since `null` is reserved internally to represent an empty slot in the circular buffer.

## 2. Why & when

`LinkedList` gives O(1) operations at both ends too, but pays a real cost per element: each value is wrapped in a separately-allocated node object carrying two pointer references, meaning more memory overhead and worse CPU cache locality (nodes can be scattered anywhere in memory, unlike an array's contiguous layout) compared to `ArrayDeque`'s single backing array. For pure queue or stack use — where indexed access into the middle is never needed, only operations at the two ends — `ArrayDeque` is both faster in practice and more memory-efficient, making it the better default choice over `LinkedList` for these roles. Use it as a **stack** (`push`/`pop`/`peek`, replacing the legacy synchronized `Stack` class), as a **FIFO queue** (`offer`/`poll`/`peek`, an alternative to `LinkedList` as a `Queue`), or as a genuine double-ended structure needing fast operations at both ends.

## 3. Core concept

```
Circular buffer of capacity 8, currently holding [B, C, D] (head at index 2, tail at index 4):

index:   0    1    2    3    4    5    6    7
value:  [ ]  [ ]  [B]  [C]  [D]  [ ]  [ ]  [ ]
                   ^head          ^tail (next free slot)

addFirst(A): writes to index 1 (wrapping backward), head moves to index 1
addLast(E):  writes to index 5, tail moves to index 6

index:   0    1    2    3    4    5    6    7
value:  [ ]  [A]  [B]  [C]  [D]  [E]  [ ]  [ ]
              ^head                    ^tail

If the array fills up entirely, ArrayDeque allocates a new, larger array and copies
everything over -- the same doubling-and-copy strategy ArrayList uses for resizing.
```

Both ends can grow into "unused" space on either side without shifting any existing element — the wraparound is what makes this possible within a fixed-size array.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ArrayDeque stores elements in a circular buffer, allowing O(1) insertion and removal at both ends without shifting elements or wrapping through separate node objects">
  <g font-family="sans-serif">
    <rect x="40" y="60" width="70" height="45" fill="#1c2430" stroke="#8b949e"/>
    <rect x="110" y="60" width="70" height="45" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
    <text x="145" y="87" fill="#e6edf3" font-size="11" text-anchor="middle">A</text>
    <rect x="180" y="60" width="70" height="45" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
    <text x="215" y="87" fill="#e6edf3" font-size="11" text-anchor="middle">B</text>
    <rect x="250" y="60" width="70" height="45" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
    <text x="285" y="87" fill="#e6edf3" font-size="11" text-anchor="middle">C</text>
    <rect x="320" y="60" width="70" height="45" fill="#1c2430" stroke="#8b949e"/>
    <rect x="390" y="60" width="70" height="45" fill="#1c2430" stroke="#8b949e"/>
  </g>
  <text x="145" y="45" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">head</text>
  <text x="285" y="45" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">tail region</text>
  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">A single contiguous array, one allocation — no per-element node objects, unlike LinkedList</text>
</svg>

*A single array with wraparound indexing — both ends grow into free space with no shifting and no per-element node allocation.*

## 5. Runnable example

Scenario: an undo/redo stack for a text editor, growing from basic stack usage, through using the same structure as a plain FIFO queue, to a capacity-aware benchmark proving `ArrayDeque`'s advantage over `LinkedList` for this exact access pattern.

### Level 1 — Basic

```java
import java.util.*;

public class UndoStackBasic {
    public static void main(String[] args) {
        Deque<String> undoStack = new ArrayDeque<>();
        undoStack.push("typed 'hello'");
        undoStack.push("typed ' world'");
        undoStack.push("deleted 'world'");

        System.out.println("undo: " + undoStack.pop());
        System.out.println("undo: " + undoStack.pop());
        System.out.println("remaining actions: " + undoStack);
    }
}
```

**How to run:** `java UndoStackBasic.java` (JDK 17+).

Expected output:
```
undo: deleted 'world'
undo: typed ' world'
remaining actions: [typed 'hello']
```

`push`/`pop` operate on the front of the deque, giving last-in-first-out undo behavior — the most recent action is always undone first, exactly like the legacy `Stack` class, but backed by a faster, non-synchronized array.

### Level 2 — Intermediate

```java
import java.util.*;

public class PrintQueueViaArrayDeque {
    public static void main(String[] args) {
        Deque<String> printQueue = new ArrayDeque<>(); // same class, used as a FIFO queue instead
        printQueue.offer("report.pdf");
        printQueue.offer("invoice.pdf");
        printQueue.offer("photo.png");

        System.out.println("processing print jobs in arrival order:");
        while (!printQueue.isEmpty()) {
            System.out.println("  printing: " + printQueue.poll());
        }

        // ArrayDeque disallows null -- a common trap if code assumes LinkedList-like tolerance.
        try {
            printQueue.offer(null);
        } catch (NullPointerException e) {
            System.out.println("caught: ArrayDeque rejects null elements");
        }
    }
}
```

**How to run:** `java PrintQueueViaArrayDeque.java`.

Expected output:
```
processing print jobs in arrival order:
  printing: report.pdf
  printing: invoice.pdf
  printing: photo.png
caught: ArrayDeque rejects null elements
```

The real-world concern added: the **same** `ArrayDeque` class serves equally well as a FIFO queue (`offer`/`poll`, from the [`Queue`](0805-queue.md) interface it also implements) as it did as a stack in Level 1 — and the `null`-rejection behavior, which matters if code is migrated from a `LinkedList`-backed queue (which does permit `null`) to `ArrayDeque` without checking for that assumption first.

### Level 3 — Advanced

```java
import java.util.*;

public class DequeBenchmark {
    public static void main(String[] args) {
        int operations = 2_000_000;

        Deque<Integer> arrayDeque = new ArrayDeque<>();
        long arrayDequeTime = timeStackOperations(arrayDeque, operations);

        Deque<Integer> linkedListDeque = new LinkedList<>();
        long linkedListTime = timeStackOperations(linkedListDeque, operations);

        System.out.println(operations + " push/pop cycles as a stack:");
        System.out.println("  ArrayDeque:  " + arrayDequeTime + " ms");
        System.out.println("  LinkedList:  " + linkedListTime + " ms");
        System.out.println("-> ArrayDeque avoids per-element node allocation, typically winning this benchmark");
    }

    static long timeStackOperations(Deque<Integer> deque, int operations) {
        long start = System.currentTimeMillis();
        for (int i = 0; i < operations; i++) {
            deque.push(i);
        }
        for (int i = 0; i < operations; i++) {
            deque.pop();
        }
        return System.currentTimeMillis() - start;
    }
}
```

**How to run:** `java DequeBenchmark.java`. Exact timings vary by machine and JVM warm-up state, but `ArrayDeque` is documented and generally observed to be faster than `LinkedList` for this exact push/pop access pattern, due to avoiding per-element object allocation and improving CPU cache locality.

Expected output shape:
```
2000000 push/pop cycles as a stack:
  ArrayDeque:  ~40 ms
  LinkedList:  ~90 ms
-> ArrayDeque avoids per-element node allocation, typically winning this benchmark
```

This adds the production-flavored hard case: a direct benchmark of the exact scenario `ArrayDeque` is optimized for — repeated push/pop as a stack — confirming the JDK documentation's claim in practice. The gap comes from `ArrayDeque` writing directly into pre-allocated contiguous array slots (and occasionally doubling that array, exactly like [`ArrayList`'s resizing](0812-arraylist-internals-resizing.md)) versus `LinkedList` allocating a brand-new node object for every single `push` and discarding it on every `pop`.

## 6. Walkthrough

Tracing `DequeBenchmark.timeStackOperations` for the `ArrayDeque` case:

1. The first loop calls `deque.push(i)` two million times. Each `push` (an alias for `addFirst`) writes `i` into the next available slot at the "head" side of the circular buffer and moves the head pointer, wrapping around the array's boundary as needed — no object allocation happens per call beyond the boxed `Integer` itself, and no shifting of other elements occurs.
2. If the backing array fills up during this loop, `ArrayDeque` allocates a new, larger array (doubling capacity, the same strategy `ArrayList` uses) and copies every existing element into it — an infrequent O(n) cost, amortized across many O(1) pushes, exactly like `ArrayList`'s amortized-O(1)-append argument.
3. The second loop calls `deque.pop()` (an alias for `removeFirst`) two million times, each one reading the value at the current head position, clearing that slot (setting it to `null` internally so the old reference can be garbage collected), and advancing the head pointer — again no shifting, no per-call allocation beyond what `pop` itself needs.
4. For the `LinkedList` case, the identical loop structure instead allocates a brand-new node object on every single `push` call (to wrap the value plus its `prev`/`next` pointers) and discards a node object on every `pop` call — four million total node allocations across the whole benchmark, each one a small but real cost in both allocation time and subsequent garbage collection pressure.
5. The measured elapsed times reflect this difference directly: `ArrayDeque`'s array-based, allocation-light approach consistently outperforms `LinkedList`'s node-based approach for this exact "operate only at one end, repeatedly" access pattern — matching the JDK documentation's explicit recommendation.

## 7. Gotchas & takeaways

> **Gotcha:** `ArrayDeque` disallows `null` elements outright — `push(null)`, `offer(null)`, and `addFirst(null)`/`addLast(null)` all throw `NullPointerException` immediately. This differs from `LinkedList` (also a valid `Deque`), which does permit `null` elements. Code migrating from a `LinkedList`-backed queue/deque to `ArrayDeque` for the performance benefit must first confirm `null` elements were never relied upon.

- `ArrayDeque` stores elements in a circular array buffer, giving true O(1) insertion/removal at both ends without shifting elements and without per-element node allocation.
- The JDK documents it as likely faster than [`LinkedList`](0813-linkedlist-doubly-linked.md) for both stack and queue use cases, and recommends it as the modern replacement for the legacy, synchronized `Stack` class.
- It serves equally well as a stack (`push`/`pop`/`peek`) or a FIFO queue (`offer`/`poll`/`peek`) — the same object, same underlying structure, just used through a different subset of the `Deque` interface's methods.
- Like `ArrayList`, it occasionally resizes (doubling capacity and copying) when the backing array fills — an infrequent O(n) cost amortized across many O(1) operations.
- It disallows `null` elements, unlike `LinkedList` — a real migration consideration when switching between the two.
