---
card: data-structures
gi: 81
slug: arraydeque-as-queue-deque
title: ArrayDeque as queue & deque
---

## 1. What it is

`java.util.ArrayDeque` is the standard, recommended implementation for both a queue and a deque in Java. The same class, backed by a resizable circular array, supports FIFO (queue), LIFO (stack, covered separately), and full two-ended (deque) access, depending only on which methods you call.

## 2. Why & when

Use `ArrayDeque` whenever you need a queue or a deque in Java — it is documented as faster than `LinkedList` for this purpose in most cases, since it avoids per-element node allocation and has better cache locality. It also disallows `null` elements, which removes a whole class of ambiguity bugs between "empty" and "contains null."

## 3. Core concept

**What backs it.** A circular array (see [Circular buffer / ring buffer](0074-circular-buffer-ring-buffer.md)) that automatically resizes (doubles) when full — the same amortized-O(1) growth strategy as `ArrayList`, applied at both ends instead of just the tail.

**Ordering and complexity guarantees.** All of `offerFirst`/`offerLast`/`pollFirst`/`pollLast`/`peekFirst`/`peekLast` are O(1). Using it as a plain `Queue` (`offer`/`poll`/`peek`) maps to the tail/head pair (`offer` = `offerLast`, `poll` = `pollFirst`); using it as a `Deque` gives full access to both ends explicitly.

**Basic usage — common methods.**

| Goal | Queue-style method | Deque-style method |
|---|---|---|
| insert at tail | `offer(e)` | `offerLast(e)` |
| remove from head | `poll()` | `pollFirst()` |
| insert at head | — | `offerFirst(e)` |
| remove from tail | — | `pollLast()` |

**Iteration, comparators, views.** `ArrayDeque` supports the standard `Iterable` for-each loop (head to tail order), and `descendingIterator()` for tail-to-head order — useful when you need to walk a deque backwards without manually tracking indices.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single ArrayDeque instance shown driving three different access patterns depending on which methods are called: queue via offer and poll, stack via push and pop, deque via offerFirst offerLast pollFirst pollLast">
  <g font-family="sans-serif" font-size="11">
    <rect x="240" y="10" width="160" height="30" fill="#161b22" stroke="#8b949e" rx="4"/><text x="320" y="30" fill="#e6edf3" text-anchor="middle" font-size="9">ArrayDeque&lt;T&gt;</text>
    <line x1="280" y1="40" x2="120" y2="90" stroke="#79c0ff"/>
    <line x1="320" y1="40" x2="320" y2="90" stroke="#f0883e"/>
    <line x1="360" y1="40" x2="520" y2="90" stroke="#a5d6ff"/>
    <rect x="40" y="90" width="160" height="30" fill="#0d1117" stroke="#79c0ff" rx="4"/><text x="120" y="110" fill="#e6edf3" text-anchor="middle" font-size="9">as Queue: offer/poll</text>
    <rect x="240" y="90" width="160" height="30" fill="#0d1117" stroke="#f0883e" rx="4"/><text x="320" y="110" fill="#e6edf3" text-anchor="middle" font-size="9">as Stack: push/pop</text>
    <rect x="440" y="90" width="160" height="30" fill="#0d1117" stroke="#a5d6ff" rx="4"/><text x="520" y="110" fill="#e6edf3" text-anchor="middle" font-size="9">as Deque: both ends</text>
  </g>
</svg>

One class, three access styles — which subset of methods you call determines the behavior your code gets.

## 5. Runnable example

```java
// ArrayDequeQueueAndDeque.java
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Iterator;
import java.util.Queue;

public class ArrayDequeQueueAndDeque {

    // Basic: common methods, used as a plain Queue.
    static void basicLevel() {
        Queue<Integer> queue = new ArrayDeque<>();
        queue.offer(1);
        queue.offer(2);
        queue.offer(3);
        System.out.println("basic: queue -> " + queue);
        System.out.println("basic: poll -> " + queue.poll() + ", remaining -> " + queue);
    }

    // Intermediate: iteration (forward and descending), and a view of it as a genuine Deque.
    static void intermediateLevel() {
        Deque<String> deque = new ArrayDeque<>();
        deque.offerLast("a");
        deque.offerLast("b");
        deque.offerFirst("z"); // z, a, b

        StringBuilder forward = new StringBuilder();
        for (String s : deque) forward.append(s).append(" ");
        System.out.println("intermediate: forward iteration -> " + forward.toString().trim());

        StringBuilder backward = new StringBuilder();
        Iterator<String> it = deque.descendingIterator();
        while (it.hasNext()) backward.append(it.next()).append(" ");
        System.out.println("intermediate: descending iteration -> " + backward.toString().trim());
    }

    // Advanced: a realistic task -- a browser-style back/forward history using both ends of one deque.
    static class History {
        private final Deque<String> back = new ArrayDeque<>();
        private final Deque<String> forward = new ArrayDeque<>();
        private String current;

        void visit(String url) {
            if (current != null) back.push(current);
            current = url;
            forward.clear(); // new navigation invalidates forward history
        }

        void goBack() {
            if (back.isEmpty()) return;
            forward.push(current);
            current = back.pop();
        }

        void goForward() {
            if (forward.isEmpty()) return;
            back.push(current);
            current = forward.pop();
        }

        String current() { return current; }
    }

    static void advancedLevel() {
        History history = new History();
        history.visit("home");
        history.visit("products");
        history.visit("checkout");
        System.out.println("advanced: current -> " + history.current());
        history.goBack();
        System.out.println("advanced: after goBack -> " + history.current());
        history.goForward();
        System.out.println("advanced: after goForward -> " + history.current());
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `ArrayDequeQueueAndDeque.java`, then run `java ArrayDequeQueueAndDeque.java`.

## 6. Walkthrough

1. `basicLevel()` uses `ArrayDeque` purely as a `Queue`: `offer` at the tail, `poll` from the head — FIFO order, `1` comes out first.
2. `intermediateLevel()` builds `[z, a, b]` using `offerFirst`/`offerLast`, then iterates it two ways: the default forward iterator gives head-to-tail order (`z, a, b`); `descendingIterator()` gives tail-to-head order (`b, a, z`) — both without any manual index bookkeeping.
3. `advancedLevel()`'s `History` class uses two separate `ArrayDeque`s as stacks (`back` and `forward`) to implement browser-style navigation. `visit` pushes the current page onto `back` before switching, and clears `forward` (a new visit invalidates any old forward history). `goBack`/`goForward` swap the current page between the two stacks — the same push/pop pattern from [Undo/redo & the call stack](0067-undo-redo-the-call-stack.md), applied to page URLs instead of text edits.

## 7. Gotchas & takeaways

> Gotcha: `ArrayDeque`'s plain `iterator()` always goes head-to-tail, regardless of whether you are using the deque as a queue or a stack — if you used `push`/`pop` (stack semantics, where `push` adds at the head), the "head" is the most-recently-pushed element, so forward iteration shows *pop* order, not insertion order. Always double-check which end your `push`/`offer` calls actually targeted before assuming what iteration order means.

- `ArrayDeque` implements `Queue` and `Deque`, giving FIFO, LIFO, and two-ended access from one class.
- It disallows `null` elements and is generally faster than `LinkedList` for both queue and stack use.
- Use `descendingIterator()` to walk a deque tail-to-head without manual bookkeeping.
- Related concepts: [Double-ended queue (deque)](0073-double-ended-queue-deque.md), [ArrayDeque as a stack (preferred)](0070-arraydeque-as-a-stack-preferred.md), [Queue & Deque interfaces](0082-queue-deque-interfaces.md).
