---
card: java
gi: 835
slug: linkedlist-as-queue-deque
title: LinkedList as Queue/Deque
---

## 1. What it is

[`LinkedList`](0813-linkedlist-doubly-linked.md) implements both [`Queue`](0805-queue.md) and [`Deque`](0806-deque.md) in addition to [`List`](0802-list.md), so the exact same class can be declared and used through any of these three interface types: `List<T> list = new LinkedList<>()`, `Queue<T> queue = new LinkedList<>()`, or `Deque<T> deque = new LinkedList<>()`. Used as a `Queue`/`Deque`, it offers the standard `offer`/`poll`/`peek` and `addFirst`/`addLast`/`removeFirst`/`removeLast` operations, all in genuine O(1) — the same doubly-linked-node structure that gives O(1) end operations for `List` use naturally extends to `Queue`/`Deque` use, since they're fundamentally the same underlying operations viewed through a different-shaped interface.

## 2. Why & when

[`ArrayDeque`](0834-arraydeque.md) is generally faster and more memory-efficient for pure queue/stack use, since it avoids `LinkedList`'s per-element node allocation overhead — so for a brand-new queue or deque, `ArrayDeque` is usually the better default. `LinkedList`'s role as a `Queue`/`Deque` remains legitimate in a few specific situations: when `null` elements must be permitted (`ArrayDeque` disallows them entirely), when the same object needs to be used interchangeably as both a `List` and a `Queue`/`Deque` in different parts of the code (since `LinkedList` implements all three interfaces simultaneously, while `ArrayDeque` implements only `Deque`, not `List`), or simply when working with existing code already built around `LinkedList` where switching wouldn't provide a meaningful benefit. Understanding this dual nature also clarifies a common point of confusion: a variable declared as `Queue<String> q = new LinkedList<>()` is still, underneath, the exact same doubly-linked-node object a `List<String>` reference to the identical instance would see — the interface reference type only controls which methods are visible, not what the object actually is.

## 3. Core concept

```java
LinkedList<String> shared = new LinkedList<>();

List<String> asList = shared;   // same object, viewed as a List
Queue<String> asQueue = shared; // same object, viewed as a Queue
Deque<String> asDeque = shared; // same object, viewed as a Deque

asQueue.offer("first");  // adds at the tail
asList.get(0);            // "first" -- the SAME object, now readable via List's indexed access
asDeque.addFirst("zero"); // adds at the head
asList.get(0);            // "zero" -- List sees the Deque-added element too, since it's one object
```

Because all three variables reference the identical `LinkedList` instance, any mutation performed through one interface view is immediately visible through the others — there's no copying or synchronization needed between them, since there's only ever one underlying object.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single LinkedList instance can be referenced simultaneously as a List, a Queue, and a Deque, since it implements all three interfaces at once">
  <rect x="240" y="20" width="160" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">one LinkedList object</text>

  <line x1="280" y1="65" x2="130" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a835)"/>
  <line x1="320" y1="65" x2="320" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a835)"/>
  <line x1="360" y1="65" x2="510" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a835)"/>

  <rect x="40" y="115" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="130" y="140" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">List&lt;String&gt; view</text>

  <rect x="230" y="115" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="140" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Queue&lt;String&gt; view</text>

  <rect x="420" y="115" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="510" y="140" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Deque&lt;String&gt; view</text>

  <text x="320" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">All three variables point to the SAME object — a mutation via any one is visible through all</text>

  <defs><marker id="a835" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

*The same `LinkedList` object can be referenced simultaneously through `List`, `Queue`, and `Deque` interface types.*

## 5. Runnable example

Scenario: a task-processing pipeline that needs both queue-style processing and occasional list-style inspection of the same underlying data, growing from basic dual-interface usage, to demonstrating `null`-tolerance as the deciding factor over `ArrayDeque`, to a realistic comparison of when to actually choose `LinkedList` over `ArrayDeque` for this role.

### Level 1 — Basic

```java
import java.util.*;

public class DualInterfaceBasic {
    public static void main(String[] args) {
        LinkedList<String> tasks = new LinkedList<>();

        Queue<String> asQueue = tasks; // same object, Queue view
        asQueue.offer("task-1");
        asQueue.offer("task-2");
        asQueue.offer("task-3");

        List<String> asList = tasks; // same object, List view
        System.out.println("inspecting via List view -- task at index 1: " + asList.get(1));

        System.out.println("processing via Queue view:");
        while (!asQueue.isEmpty()) {
            System.out.println("  " + asQueue.poll());
        }
    }
}
```

**How to run:** `java DualInterfaceBasic.java` (JDK 17+).

Expected output:
```
inspecting via List view -- task at index 1: task-2
processing via Queue view:
  task-1
  task-2
  task-3
```

`asQueue` and `asList` reference the exact same `LinkedList` instance — elements added via the `Queue` view are immediately visible and indexable via the `List` view, since there's only one underlying object with one underlying state.

### Level 2 — Intermediate

```java
import java.util.*;

public class NullTolerancePipeline {
    public static void main(String[] args) {
        Queue<String> pipeline = new LinkedList<>(); // LinkedList permits null; ArrayDeque would not

        pipeline.offer("step-1-complete");
        pipeline.offer(null); // represents "step 2 produced no result", a legitimate business meaning here
        pipeline.offer("step-3-complete");

        System.out.println("pipeline contents (null is a meaningful marker here): " + pipeline);

        while (!pipeline.isEmpty()) {
            String step = pipeline.poll();
            if (step == null) {
                System.out.println("  (skipped a step that produced no result)");
            } else {
                System.out.println("  processing: " + step);
            }
        }

        // Confirm the alternative would have failed outright:
        Queue<String> arrayDequeVersion = new ArrayDeque<>();
        try {
            arrayDequeVersion.offer(null);
        } catch (NullPointerException e) {
            System.out.println("confirmed: ArrayDeque would have rejected this null immediately");
        }
    }
}
```

**How to run:** `java NullTolerancePipeline.java`.

Expected output:
```
pipeline contents (null is a meaningful marker here): [step-1-complete, null, step-3-complete]
  processing: step-1-complete
  (skipped a step that produced no result)
  processing: step-3-complete
confirmed: ArrayDeque would have rejected this null immediately
```

The real-world concern added: a concrete case where `null`-tolerance is a genuine, deliberate design requirement (representing "no result" as a queued marker) — the exact situation where `LinkedList`'s permissiveness is a feature, not an oversight, and switching to [`ArrayDeque`](0834-arraydeque.md) for its performance benefit would actively break this design by throwing on the very first `null` insertion.

### Level 3 — Advanced

```java
import java.util.*;

public class ChooseTheRightDeque {
    public static void main(String[] args) {
        // Scenario A: pure queue/stack use, no null elements, no need for List-style indexed access.
        // -> ArrayDeque is the better default here: faster, less memory overhead.
        Deque<Integer> fastQueue = new ArrayDeque<>();
        fastQueue.offer(1);
        fastQueue.offer(2);
        System.out.println("Scenario A (pure queue, no nulls needed): ArrayDeque -- " + fastQueue);

        // Scenario B: the SAME object needs to be processed as a queue AND inspected as a List
        // (e.g. a debugging/admin view that wants to see "position 3 in the pending queue").
        // -> LinkedList is the right choice, since ArrayDeque does NOT implement List at all.
        LinkedList<String> dualPurpose = new LinkedList<>();
        dualPurpose.offer("job-A");
        dualPurpose.offer("job-B");
        dualPurpose.offer("job-C");
        List<String> inspectable = dualPurpose; // this line would NOT COMPILE if dualPurpose were an ArrayDeque
        System.out.println("Scenario B (queue + List inspection): job at position 1 is " + inspectable.get(1));

        // Scenario C: null elements carry real meaning in this domain.
        // -> LinkedList again, since ArrayDeque flatly disallows null.
        Queue<String> nullTolerant = new LinkedList<>();
        nullTolerant.offer(null);
        System.out.println("Scenario C (null-tolerant queue): head is " + nullTolerant.peek());
    }
}
```

**How to run:** `java ChooseTheRightDeque.java`.

Expected output:
```
Scenario A (pure queue, no nulls needed): ArrayDeque -- [1, 2]
Scenario B (queue + List inspection): job at position 1 is job-B
Scenario C (null-tolerant queue): head is null
```

This adds the production-flavored hard case: three side-by-side scenarios showing exactly when each choice is correct. Note the comment on `List<String> inspectable = dualPurpose` — this assignment is only legal because `dualPurpose` is declared as `LinkedList<String>`, which implements `List`; the identical line would be a compile error if `dualPurpose` had been declared as `ArrayDeque<String>`, since `ArrayDeque` implements `Deque` but not `List` at all. This is the single clearest reason to deliberately choose `LinkedList` over `ArrayDeque` for a queue/deque role: needing the same object usable as a `List` too.

## 6. Walkthrough

Tracing `ChooseTheRightDeque.main`, focusing on Scenario B:

1. `dualPurpose` is declared as `LinkedList<String>` (the concrete type, not just `Queue` or `Deque`) and populated with three job names via `offer`, which — since `LinkedList` implements `Queue` — adds each one at the tail, just like any other `Queue` implementation would.
2. `List<String> inspectable = dualPurpose` assigns the same object to a new reference variable typed as `List<String>`. This compiles successfully specifically because `LinkedList` implements `List` directly (in addition to `Queue` and `Deque`) — the object itself hasn't changed at all, only a new reference variable of a different (but compatible) static type now points at it.
3. `inspectable.get(1)` calls `List`'s indexed-access method on that same object, walking the linked chain from whichever end is closer to index 1 (as explained in [LinkedList's internals](0813-linkedlist-doubly-linked.md)) and returning `"job-B"`, the second element in insertion order — demonstrating that the elements added via the `Queue`-style `offer` calls are fully visible and indexable through the `List` interface, because there was only ever one object and one underlying doubly-linked structure the whole time.
4. Had `dualPurpose` instead been declared as `ArrayDeque<String>`, the line `List<String> inspectable = dualPurpose;` would fail to compile with an incompatible-types error, since `ArrayDeque` simply does not implement `List` — this is a structural, compile-time distinction between the two classes, not a runtime behavior difference, and it's the deciding factor whenever a single object genuinely needs to serve both roles.

## 7. Gotchas & takeaways

> **Gotcha:** `ArrayDeque` does **not** implement `List` at all — code that needs the same object usable both as a `Queue`/`Deque` and as an indexed `List` **must** use `LinkedList` (or a separate, explicit conversion/copy) for that object; there is no way to get `List`-style indexed access out of an `ArrayDeque` instance directly.

- `LinkedList` implements `List`, [`Queue`](0805-queue.md), and [`Deque`](0806-deque.md) simultaneously — the same object can be referenced through any of the three interface types, and mutations via one view are immediately visible via the others.
- [`ArrayDeque`](0834-arraydeque.md) is generally faster and more memory-efficient for pure queue/stack use, and is the better default for a brand-new queue or deque with no other requirements.
- Choose `LinkedList` over `ArrayDeque` for a queue/deque role specifically when: `null` elements carry real meaning (`ArrayDeque` disallows them), or the same object must also be usable as a `List` (`ArrayDeque` doesn't implement `List` at all).
- The interface type used to reference an object (`List`, `Queue`, or `Deque`) only controls which methods are visible through that particular variable — it never changes what the underlying object actually is or how it stores its data.
- When in doubt for a new queue/deque with no `null`-tolerance or `List`-dual-use requirement, default to `ArrayDeque`; reach for `LinkedList` only when one of those two specific needs actually applies.
