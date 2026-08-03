---
card: data-structures
gi: 183
slug: queue-deque-implementations
title: Queue/Deque implementations
---

## 1. What it is

`Queue` is an interface for first-in-first-out (FIFO) processing. `Deque` ("double-ended queue") extends it, allowing insertion and removal at **both** ends. `ArrayDeque`, `LinkedList`, and `PriorityQueue` are the main implementations, each backing this contract differently.

## 2. Why & when

Use `ArrayDeque` as the default for stack or queue behavior — it is faster and uses less memory per element than `LinkedList`, because it stores elements in a resizable circular array instead of individually allocated nodes. Use `PriorityQueue` when elements must come out in priority order rather than insertion order — task scheduling, Dijkstra's algorithm, or "always process the smallest/largest item next." Use `LinkedList` as a `Queue`/`Deque` only when you specifically also need its `List` behavior at the same time.

## 3. Core concept

**What backs each one.** `ArrayDeque`: a resizable circular array — a fixed-size array where the "start" and "end" positions wrap around, so adding to either end is `O(1)` without shifting. `LinkedList`: the same doubly linked list described in [List implementations](0180-list-implementations-arraylist-linkedlist-vector.md), which naturally supports `O(1)` insertion/removal at both ends. `PriorityQueue`: a [binary heap](0116-heap-property-array-representation.md), always keeping the smallest (or largest, with a custom `Comparator`) element accessible at the front in `O(1)`, with `O(log n)` insertion and removal.

**The operations each contract adds.** `Queue`: `offer` (add to the tail), `poll` (remove and return the head, or `null` if empty), `peek` (view the head without removing). `Deque`: all of the above, plus `addFirst`/`addLast`, `removeFirst`/`removeLast`, `peekFirst`/`peekLast` — letting a `Deque` act as a stack (`push`/`pop`, using the front) or a queue (`offer`/`poll`, using both ends) interchangeably.

**Why `PriorityQueue` breaks strict FIFO order.** A `PriorityQueue`'s `poll()` always returns the current smallest element (by natural order or a supplied `Comparator`), regardless of insertion order — it is a `Queue` in name and interface only; its ordering guarantee is priority, not arrival time. Internally, the binary heap structure only guarantees the root is the minimum; sibling and cousin elements are not fully sorted relative to each other.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ArrayDeque as a circular array supporting O(1) operations at both ends, versus PriorityQueue as a heap always exposing the minimum at the root">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">ArrayDeque: circular array, both ends O(1)</text>
    <rect x="20" y="30" width="40" height="30" fill="#161b22" stroke="#79c0ff"/><text x="40" y="50" text-anchor="middle">B</text>
    <rect x="60" y="30" width="40" height="30" fill="#161b22" stroke="#79c0ff"/><text x="80" y="50" text-anchor="middle">C</text>
    <rect x="100" y="30" width="40" height="30" fill="#161b22" stroke="#79c0ff"/><text x="120" y="50" text-anchor="middle">D</text>
    <text x="20" y="80" font-size="8">addFirst(A) and addLast(E) both O(1), wrapping around the array</text>

    <text x="10" y="130">PriorityQueue: heap, root is always the minimum</text>
    <circle cx="320" cy="150" r="16" fill="#161b22" stroke="#3fb950"/><text x="320" y="154" text-anchor="middle" font-size="9">2</text>
    <circle cx="280" cy="180" r="14" fill="#0d1117" stroke="#8b949e"/><text x="280" y="184" text-anchor="middle" font-size="8">5</text>
    <circle cx="360" cy="180" r="14" fill="#0d1117" stroke="#8b949e"/><text x="360" y="184" text-anchor="middle" font-size="8">7</text>
    <line x1="320" y1="164" x2="280" y2="168" stroke="#3fb950"/>
    <line x1="320" y1="164" x2="360" y2="168" stroke="#3fb950"/>
    <text x="450" y="160" font-size="8" fill="#8b949e">poll() -&gt; 2, but 5 and 7 are NOT</text>
    <text x="450" y="175" font-size="8" fill="#8b949e">guaranteed sorted relative to each other</text>
  </g>
</svg>

`ArrayDeque` gives `O(1)` at both ends; `PriorityQueue` only guarantees the root is smallest.

## 5. Runnable example

```java
// QueueDequeImplementations.java
import java.util.*;

public class QueueDequeImplementations {

    // Basic: ArrayDeque used as both a stack (push/pop) and a queue (offer/poll).
    static void basicLevel() {
        Deque<Integer> stack = new ArrayDeque<>();
        stack.push(1);
        stack.push(2);
        stack.push(3);
        System.out.println("basic: stack pop() -> " + stack.pop()); // LIFO: 3

        Deque<Integer> queue = new ArrayDeque<>();
        queue.offer(1);
        queue.offer(2);
        queue.offer(3);
        System.out.println("basic: queue poll() -> " + queue.poll()); // FIFO: 1
    }

    // Intermediate: PriorityQueue with a custom Comparator, processing tasks by priority, not arrival order.
    record Task(String name, int priority) {}

    static void intermediateLevel() {
        PriorityQueue<Task> tasks = new PriorityQueue<>(Comparator.comparingInt(Task::priority));
        tasks.offer(new Task("cleanup", 3));
        tasks.offer(new Task("fire alarm", 1));
        tasks.offer(new Task("send report", 2));

        while (!tasks.isEmpty()) {
            System.out.println("intermediate: next task -> " + tasks.poll());
        }
    }

    // Advanced: a sliding-window maximum using a Deque to hold candidate indices in decreasing value order.
    static int[] slidingWindowMax(int[] nums, int k) {
        Deque<Integer> indices = new ArrayDeque<>(); // holds indices, values in decreasing order
        int[] result = new int[nums.length - k + 1];

        for (int i = 0; i < nums.length; i++) {
            while (!indices.isEmpty() && indices.peekFirst() <= i - k) {
                indices.pollFirst(); // remove indices that fell out of the window
            }
            while (!indices.isEmpty() && nums[indices.peekLast()] < nums[i]) {
                indices.pollLast(); // remove smaller values -- they can never be the max again
            }
            indices.offerLast(i);
            if (i >= k - 1) {
                result[i - k + 1] = nums[indices.peekFirst()];
            }
        }
        return result;
    }

    static void advancedLevel() {
        int[] nums = {1, 3, -1, -3, 5, 3, 6, 7};
        System.out.println("advanced: sliding window max (k=3) -> " + Arrays.toString(slidingWindowMax(nums, 3)));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java QueueDequeImplementations.java`

## 6. Walkthrough

Using `ArrayDeque` as a stack: `push(1)`, `push(2)`, `push(3)` each add to the front (in `Deque`'s stack convention). `pop()` removes and returns the front, `3` — last in, first out, matching stack semantics.

Using `ArrayDeque` as a queue: `offer(1)`, `offer(2)`, `offer(3)` each add to the tail. `poll()` removes and returns the head, `1` — first in, first out, matching queue semantics. The same underlying `ArrayDeque` supports both usage patterns, depending only on which methods you call.

For `PriorityQueue`: insert three tasks with priorities `3, 1, 2` (in that insertion order). Calling `poll()` repeatedly does **not** return them in insertion order (`cleanup, fire alarm, send report`) — it returns them in priority order: `fire alarm` (priority `1`) first, then `send report` (priority `2`), then `cleanup` (priority `3`) last. The `Comparator` passed at construction decides "smallest priority number comes first."

For the sliding window maximum: the `Deque` holds candidate **indices**, kept in an order where their corresponding values are strictly decreasing from front to back. Before adding a new index, pop any indices from the back whose values are smaller than the incoming value — those values can never be the maximum of any future window, since the new, later, larger value will always be preferred. Pop from the front any index that has fallen outside the current window. The front of the deque is always the index of the current window's maximum.

**Complexity.** `ArrayDeque`: `offer`/`poll`/`push`/`pop` at either end, `O(1)` amortized. `LinkedList` as `Queue`/`Deque`: same `O(1)` at both ends, with more per-element memory overhead. `PriorityQueue`: `offer` `O(log n)`, `poll` `O(log n)`, `peek` `O(1)`.

## 7. Gotchas & takeaways

> `PriorityQueue.toString()` (and its iterator) does **not** print elements in sorted order — it exposes the underlying heap array's internal layout, which only guarantees the root is smallest. Only repeated `poll()` calls guarantee sorted output.

- Prefer `offer`/`poll`/`peek` over `add`/`remove`/`element` on an empty queue — the `offer` family returns `null`/`false` on failure, while the `add` family throws an exception, which matters when queue emptiness is a normal, expected condition rather than an error.
- `ArrayDeque` does not allow `null` elements (unlike `LinkedList`), because `null` is used internally as a sentinel to signal "empty" from `poll`/`peek`.
- For Dijkstra's algorithm, task schedulers, or any "always process the current best candidate next" pattern, `PriorityQueue` is the standard tool — pair it with a `Comparator` (or a record implementing `Comparable`) matching whatever "best" means for your problem.
