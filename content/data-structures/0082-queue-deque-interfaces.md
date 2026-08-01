---
card: data-structures
gi: 82
slug: queue-deque-interfaces
title: Queue & Deque interfaces
---

## 1. What it is

`Queue` and `Deque` are Java interfaces in `java.util` that define the *contract* for queue-shaped and deque-shaped behavior, separately from any particular implementation. `Deque` extends `Queue` (and also provides `Stack`-like methods), so any `Deque` implementation — like `ArrayDeque` — automatically satisfies both contracts at once.

## 2. Why & when

Programming against the interface (`Queue<T> q = new ArrayDeque<>();` instead of `ArrayDeque<T> q = new ArrayDeque<>();`) lets you swap the underlying implementation later without changing calling code, and it documents intent — a method parameter typed `Queue<T>` tells callers "I only need FIFO access here," while `Deque<T>` says "I need both ends." Understanding the interface hierarchy also clarifies why `ArrayDeque` and `LinkedList` can both serve as a queue, a deque, and (via `Deque`) a stack, despite being built completely differently underneath.

## 3. Core concept

**The decision criteria — which interface to declare.**
- **`Queue<T>`:** the caller only needs `offer`/`poll`/`peek` (or `add`/`remove`/`element`) — insertion at one end, removal from the other.
- **`Deque<T>`:** the caller needs both ends — `offerFirst`/`offerLast`/`pollFirst`/`pollLast`, or wants stack-shaped `push`/`pop`.
- Declaring the narrowest interface that covers your actual usage keeps the contract honest and makes future implementation swaps safer.

**The interface hierarchy.** `Deque<T> extends Queue<T> extends Collection<T> extends Iterable<T>`. This means every `Deque` is usable anywhere a `Queue` is expected, and every `Queue` is usable anywhere a `Collection` is expected (for `size()`, `isEmpty()`, iteration, and so on) — but not the reverse; a plain `Queue` reference cannot call `Deque`-only methods like `addFirst`.

**Implementations that satisfy these interfaces.** `ArrayDeque` implements `Deque` (so it satisfies both `Deque` and `Queue`). `LinkedList` also implements `Deque` (and `List`, separately). `PriorityQueue` implements only `Queue`, not `Deque` — since its removal order is priority-based, not tied to either physical end, a `Deque`-style "add/remove from a specific end" contract does not apply to it.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Interface hierarchy: Collection at the top, Queue extending it, Deque extending Queue, with ArrayDeque and LinkedList implementing Deque and PriorityQueue implementing only Queue">
  <g font-family="sans-serif" font-size="11">
    <rect x="250" y="10" width="140" height="30" fill="#161b22" stroke="#8b949e" rx="4"/><text x="320" y="30" fill="#e6edf3" text-anchor="middle" font-size="9">Collection&lt;T&gt;</text>
    <line x1="320" y1="40" x2="320" y2="60" stroke="#8b949e" marker-end="url(#ih)"/>
    <rect x="250" y="60" width="140" height="30" fill="#161b22" stroke="#8b949e" rx="4"/><text x="320" y="80" fill="#e6edf3" text-anchor="middle" font-size="9">Queue&lt;T&gt;</text>
    <line x1="320" y1="90" x2="320" y2="110" stroke="#f0883e" marker-end="url(#ih)"/>
    <rect x="250" y="110" width="140" height="30" fill="#0d1117" stroke="#f0883e" rx="4"/><text x="320" y="130" fill="#e6edf3" text-anchor="middle" font-size="9">Deque&lt;T&gt;</text>
    <defs><marker id="ih" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>

    <line x1="270" y1="140" x2="150" y2="160" stroke="#79c0ff"/>
    <text x="130" y="175" fill="#79c0ff" font-size="9">ArrayDeque</text>
    <line x1="370" y1="140" x2="450" y2="160" stroke="#79c0ff"/>
    <text x="420" y="175" fill="#79c0ff" font-size="9">LinkedList</text>
    <line x1="280" y1="90" x2="120" y2="60" stroke="#a5d6ff"/>
    <text x="60" y="55" fill="#a5d6ff" font-size="9">PriorityQueue (Queue only)</text>
  </g>
</svg>

`Deque` extends `Queue`, which extends `Collection` — every `Deque` implementation is automatically a valid `Queue` and `Collection` too; `PriorityQueue` opts into `Queue` only, since it has no two-ended structure to expose.

## 5. Runnable example

```java
// QueueDequeInterfaces.java
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.LinkedList;
import java.util.PriorityQueue;
import java.util.Queue;

public class QueueDequeInterfaces {

    // Basic: the same ArrayDeque instance, referenced through two different interface types.
    static void basicLevel() {
        Deque<Integer> asDeque = new ArrayDeque<>();
        asDeque.offerFirst(1);
        asDeque.offerLast(2);

        Queue<Integer> asQueue = asDeque; // a Deque reference IS-A Queue reference -- always legal, no cast needed
        System.out.println("basic: via Queue reference, poll -> " + asQueue.poll());
        System.out.println("basic: via Deque reference, remaining -> " + asDeque);
    }

    // Intermediate: a method that only needs Queue behavior should declare Queue, not a concrete class -- enables swapping implementations.
    static int sumAndDrain(Queue<Integer> queue) {
        int sum = 0;
        while (!queue.isEmpty()) sum += queue.poll();
        return sum;
    }

    static void intermediateLevel() {
        Queue<Integer> fromArrayDeque = new ArrayDeque<>(java.util.List.of(1, 2, 3));
        Queue<Integer> fromLinkedList = new LinkedList<>(java.util.List.of(4, 5, 6));

        System.out.println("intermediate: sumAndDrain works on ArrayDeque -> " + sumAndDrain(fromArrayDeque));
        System.out.println("intermediate: sumAndDrain works on LinkedList -> " + sumAndDrain(fromLinkedList));
    }

    // Advanced: PriorityQueue implements Queue but NOT Deque -- confirm it has no addFirst/addLast, since priority order overrides physical ends.
    static void advancedLevel() {
        Queue<Integer> pq = new PriorityQueue<>(java.util.List.of(5, 1, 3));
        System.out.println("advanced: PriorityQueue via Queue interface, poll order (by priority, not insertion) -> "
            + pq.poll() + ", " + pq.poll() + ", " + pq.poll());
        System.out.println("advanced: PriorityQueue does not implement Deque -- no addFirst/addLast exist on it,");
        System.out.println("advanced: because removal order is priority-based, not tied to either physical end.");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `QueueDequeInterfaces.java`, then run `java QueueDequeInterfaces.java`.

## 6. Walkthrough

1. `basicLevel()` builds one `ArrayDeque`, referenced first as `Deque<Integer>`, then assigned directly to a `Queue<Integer>` variable — legal without any cast, since `Deque extends Queue`. Calling `poll()` through the `Queue` reference removes from the head, exactly as it would through the `Deque` reference.
2. `intermediateLevel()`'s `sumAndDrain` is written against `Queue<Integer>`, not any concrete class. It runs correctly whether handed an `ArrayDeque` or a `LinkedList`, because both satisfy the `Queue` contract — this is the practical payoff of coding to the interface.
3. `advancedLevel()` shows `PriorityQueue` used through a `Queue` reference: `poll()` returns elements in priority order (`1, 3, 5`), not insertion order. `PriorityQueue` has no `addFirst`/`addLast` methods at all, because it does not implement `Deque` — there is no "front" or "back" in a priority-ordered structure, only "current best."

## 7. Gotchas & takeaways

> Gotcha: declaring a variable as `Queue<T>` when you actually need `Deque`-only methods (`addFirst`, `pollLast`, `push`/`pop`) will not compile — the fix is to widen the declared type to `Deque<T>`, not to add an unsafe cast. Decide the narrowest-but-sufficient interface type up front, based on what methods the code actually calls.

- `Deque<T> extends Queue<T> extends Collection<T>` — every `Deque` is usable as a `Queue`, but not the reverse.
- Program against the interface (`Queue<T>` or `Deque<T>`) rather than a concrete class, so implementations can be swapped without changing calling code.
- `ArrayDeque` and `LinkedList` implement `Deque` (and therefore `Queue`); `PriorityQueue` implements only `Queue`, since priority order has no fixed "ends."
- Related concepts: [ArrayDeque as queue & deque](0081-arraydeque-as-queue-deque.md), [java.util.PriorityQueue (binary heap)](0083-java-util-priorityqueue-binary-heap.md).
