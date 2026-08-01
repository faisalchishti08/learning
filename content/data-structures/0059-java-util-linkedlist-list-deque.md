---
card: data-structures
gi: 59
slug: java-util-linkedlist-list-deque
title: java.util.LinkedList (List + Deque)
---

## 1. What it is

`java.util.LinkedList` is Java's built-in **doubly linked list** implementation. It implements both the `List` interface (indexed access, like `ArrayList`) and the `Deque` interface (double-ended queue: push/pop from both ends), so it can act as a list, a stack, or a queue depending on which methods you call.

## 2. Why & when

Use it when you need frequent insertion or removal at both ends, or in the middle via an iterator, and you do not need fast random access by index. It is the natural choice for a stack (`push`/`pop`), a queue (`offer`/`poll`), or an undo history. Avoid it when you need `get(i)` a lot — that walks the chain from the nearer end, at O(n), while `ArrayList.get(i)` is O(1).

## 3. Core concept

**What backs it.** Every element sits inside a private `Node` object holding the value, a `prev` reference, and a `next` reference. The list keeps a reference to the `first` and `last` nodes, so both ends are reachable in O(1).

**Ordering and complexity guarantees.** Insertion order is preserved. Adding or removing at either end is O(1). Adding or removing at an arbitrary index is O(n) to find the position, plus O(1) to splice the node in or out. `get(i)` is O(n) because it must walk from whichever end is closer.

**When to choose it.** Choose `LinkedList` when the access pattern is "add/remove at the ends" (stack or queue) rather than "look up by index." For pure stack or queue use, `ArrayDeque` is usually faster in practice, since it avoids per-node object overhead — `LinkedList`'s advantage is implementing `List` too, so you can still insert mid-list via a `ListIterator`.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A doubly linked list with first and last references, and prev and next pointers between three nodes">
  <g font-family="sans-serif" font-size="11">
    <text x="10" y="16" fill="#8b949e">first</text>
    <line x1="30" y1="20" x2="60" y2="40" stroke="#79c0ff" marker-end="url(#d1)"/>
    <rect x="60" y="45" width="46" height="28" fill="#161b22" stroke="#8b949e"/><text x="83" y="63" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <rect x="150" y="45" width="46" height="28" fill="#161b22" stroke="#8b949e"/><text x="173" y="63" fill="#e6edf3" text-anchor="middle" font-size="9">20</text>
    <rect x="240" y="45" width="46" height="28" fill="#161b22" stroke="#8b949e"/><text x="263" y="63" fill="#e6edf3" text-anchor="middle" font-size="9">30</text>
    <line x1="106" y1="55" x2="146" y2="55" stroke="#79c0ff" marker-end="url(#d1)"/>
    <line x1="150" y1="65" x2="110" y2="65" stroke="#f0883e" marker-end="url(#d2)"/>
    <line x1="196" y1="55" x2="236" y2="55" stroke="#79c0ff" marker-end="url(#d1)"/>
    <line x1="240" y1="65" x2="200" y2="65" stroke="#f0883e" marker-end="url(#d2)"/>
    <defs>
      <marker id="d1" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker>
      <marker id="d2" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker>
    </defs>
    <text x="320" y="16" fill="#8b949e">last</text>
    <line x1="310" y1="20" x2="280" y2="40" stroke="#79c0ff" marker-end="url(#d1)"/>
    <text x="83" y="100" fill="#79c0ff" text-anchor="middle" font-size="9">next -&gt;</text>
    <text x="173" y="115" fill="#f0883e" text-anchor="middle" font-size="9">&lt;- prev</text>
  </g>
</svg>

`first` and `last` give O(1) access to both ends; each node's `prev`/`next` lets removal splice around it without shifting anything.

## 5. Runnable example

```java
// LinkedListDemo.java
import java.util.Deque;
import java.util.LinkedList;
import java.util.ListIterator;

public class LinkedListDemo {

    // Basic: common List and Deque methods.
    static void basicLevel() {
        LinkedList<Integer> list = new LinkedList<>();
        list.add(10);          // add at tail, like List.add
        list.addFirst(5);      // Deque: add at head
        list.addLast(20);      // Deque: add at tail
        System.out.println("basic: list -> " + list);
        System.out.println("basic: get(1) -> " + list.get(1));
        System.out.println("basic: peekFirst -> " + list.peekFirst() + ", peekLast -> " + list.peekLast());
    }

    // Intermediate: iteration, ListIterator for mid-list insertion, and as a Deque (stack + queue).
    static void intermediateLevel() {
        LinkedList<String> list = new LinkedList<>(java.util.List.of("a", "b", "d"));

        ListIterator<String> it = list.listIterator();
        while (it.hasNext()) {
            String value = it.next();
            if (value.equals("b")) it.add("c"); // insert "c" right after "b", O(1) once positioned
        }
        System.out.println("intermediate: after mid-list insert -> " + list);

        Deque<String> stack = new LinkedList<>();
        stack.push("x");
        stack.push("y");
        System.out.println("intermediate: stack pop order -> " + stack.pop() + ", " + stack.pop());

        Deque<String> queue = new LinkedList<>();
        queue.offer("first-in");
        queue.offer("second-in");
        System.out.println("intermediate: queue poll order -> " + queue.poll() + ", " + queue.poll());
    }

    // Advanced: a sliding window using LinkedList as a Deque, evicting from the front as it grows.
    static void advancedLevel() {
        int[] nums = {1, 3, -1, -3, 5, 3, 6, 7};
        int windowSize = 3;
        Deque<Integer> window = new LinkedList<>(); // holds indices, front-to-back decreasing values
        StringBuilder maxes = new StringBuilder();

        for (int i = 0; i < nums.length; i++) {
            if (!window.isEmpty() && window.peekFirst() <= i - windowSize) window.pollFirst(); // evict out-of-window
            while (!window.isEmpty() && nums[window.peekLast()] < nums[i]) window.pollLast();   // drop smaller tail values
            window.offerLast(i);
            if (i >= windowSize - 1) maxes.append(nums[window.peekFirst()]).append(" ");
        }
        System.out.println("advanced: sliding window maxes -> " + maxes.toString().trim());
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `LinkedListDemo.java`, then run `java LinkedListDemo.java`.

## 6. Walkthrough

1. `basicLevel()` builds `[5, 10, 20]` by mixing `add` (tail) with `addFirst`/`addLast`. `get(1)` walks from the head one step to reach index `1`, returning `10`. `peekFirst`/`peekLast` read the ends in O(1) without removing anything.
2. `intermediateLevel()` uses a `ListIterator` to insert `"c"` right after finding `"b"` during a forward scan — this is O(1) once the iterator is positioned, unlike `ArrayList`, which would shift every later element. The stack section shows `push`/`pop` giving last-in-first-out order (`y` then `x`); the queue section shows `offer`/`poll` giving first-in-first-out order (`first-in` then `second-in`).
3. `advancedLevel()` implements the sliding-window-maximum pattern. The `Deque<Integer>` stores indices, kept in an order where `nums` at those indices are decreasing from front to back. At each step: (a) evict the front index if it has fallen outside the window; (b) evict tail indices whose values are smaller than the current one, since they can never be the max while the current value is still in the window; (c) push the current index; (d) once the window is full, the front index always holds the current window's maximum.

## 7. Gotchas & takeaways

> Gotcha: calling `get(i)` in a loop over a `LinkedList` (`for (int i = 0; i < list.size(); i++) list.get(i)`) is O(n) per call, making the whole loop O(n²) — use an iterator or a for-each loop instead, which walks the chain once.

- `LinkedList` implements both `List` and `Deque`, so it can be a list, a stack, or a queue.
- Adding or removing at either end is O(1); indexed access (`get`/`set`) is O(n).
- Prefer a `ListIterator` for repeated mid-list insertion or removal during a scan.
- For a pure stack or queue with no need for `List` methods, `ArrayDeque` is typically faster.
- Related concepts: [LinkedList vs ArrayList tradeoffs](0061-linkedlist-vs-arraylist-tradeoffs.md), [Singly linked list](0045-singly-linked-list.md).
