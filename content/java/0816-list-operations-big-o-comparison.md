---
card: java
gi: 816
slug: list-operations-big-o-comparison
title: List operations Big-O comparison
---

## 1. What it is

Different `List` implementations pay very different costs for the same named operation. The table below summarizes the core trade-off between [`ArrayList`](0812-arraylist-internals-resizing.md) (array-backed) and [`LinkedList`](0813-linkedlist-doubly-linked.md) (node-chain-backed):

| Operation | ArrayList | LinkedList |
|---|---|---|
| `get(index)` | O(1) | O(n) |
| `add(element)` (at end) | O(1) amortized | O(1) |
| `add(0, element)` (at front) | O(n) | O(1) |
| `add(index, element)` (middle) | O(n) | O(n) to find + O(1) to splice |
| `remove(0)` | O(n) | O(1) |
| `remove(index)` (middle) | O(n) | O(n) to find + O(1) to splice |
| `contains(element)` | O(n) | O(n) |
| iteration (full pass) | O(n) | O(n) |

Both structures are O(n) for the same *named* operations in several rows — the table is only useful when read alongside what actually happens internally, not memorized as an isolated fact sheet.

## 2. Why & when

Big-O notation describes how a cost scales with input size, not the actual wall-clock cost — and for `List` operations specifically, the same method name can mean "read one array slot" on one implementation and "walk potentially the entire structure" on another. Knowing this table matters because choosing the wrong implementation for an access pattern can silently turn an application from fast to catastrophically slow as data grows — code that indexes into a `LinkedList` in a loop, or repeatedly inserts at the front of an `ArrayList`, both work correctly at small scale and both degrade badly (to O(n²) overall) as the list grows into the thousands or millions of elements. The right time to consult this table is architecture time, before choosing a `List` implementation, based on which operations the code will actually call most.

## 3. Core concept

```java
// ArrayList: O(1) random access, because index i maps directly to array offset i.
List<Integer> array = new ArrayList<>();
array.get(500_000); // one memory read, regardless of list size

// LinkedList: O(n) random access, because index i requires walking i nodes from an end.
List<Integer> linked = new LinkedList<>();
linked.get(500_000); // walks up to 500,000 node references
```

The cost difference isn't a JDK inefficiency — it's an inescapable consequence of how each structure is laid out in memory. An array supports direct offset arithmetic; a chain of independently-allocated nodes fundamentally does not.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ArrayList and LinkedList have opposite cost profiles: ArrayList is fast for indexed access and slow for front insertion, LinkedList is the reverse">
  <g font-family="sans-serif">
    <text x="160" y="30" fill="#6db33f" font-size="13" text-anchor="middle">ArrayList</text>
    <rect x="40" y="45" width="240" height="35" rx="6" fill="#1c2430" stroke="#3fb950"/>
    <text x="160" y="68" fill="#3fb950" font-size="11" text-anchor="middle">get(i): O(1) — fast</text>
    <rect x="40" y="90" width="240" height="35" rx="6" fill="#1c2430" stroke="#f85149"/>
    <text x="160" y="113" fill="#f85149" font-size="11" text-anchor="middle">add(0, x): O(n) — slow</text>

    <text x="480" y="30" fill="#79c0ff" font-size="13" text-anchor="middle">LinkedList</text>
    <rect x="360" y="45" width="240" height="35" rx="6" fill="#1c2430" stroke="#f85149"/>
    <text x="480" y="68" fill="#f85149" font-size="11" text-anchor="middle">get(i): O(n) — slow</text>
    <rect x="360" y="90" width="240" height="35" rx="6" fill="#1c2430" stroke="#3fb950"/>
    <text x="480" y="113" fill="#3fb950" font-size="11" text-anchor="middle">add(0, x): O(1) — fast</text>
  </g>
  <text x="320" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Neither implementation is universally faster — each wins exactly where the other loses</text>
</svg>

*The two implementations have mirror-image cost profiles — pick based on which operation actually dominates.*

## 5. Runnable example

Scenario: a task scheduler that processes tasks in FIFO order but occasionally needs to look up a task by position for a status report — growing from a naive implementation that picks the wrong structure, to a benchmark proving it, to a hybrid design that picks the right structure per access pattern.

### Level 1 — Basic

```java
import java.util.*;

public class SchedulerNaive {
    public static void main(String[] args) {
        List<String> tasks = new LinkedList<>(); // chosen because "removeFirst() should be fast"
        for (int i = 0; i < 5; i++) {
            tasks.add("task-" + i);
        }

        // Process tasks in order.
        System.out.println("processing: " + tasks.remove(0));

        // Status report: "what's the 3rd task in the queue?"
        System.out.println("3rd task in queue: " + tasks.get(2));
    }
}
```

**How to run:** `java SchedulerNaive.java` (JDK 17+).

Expected output:
```
processing: task-0
3rd task in queue: task-3
```

This works correctly and looks fine at small scale — the bug is a *performance* bug, invisible until the list grows large, which is exactly why this class of mistake is easy to ship unnoticed.

### Level 2 — Intermediate

```java
import java.util.*;

public class SchedulerBenchmark {
    public static void main(String[] args) {
        int n = 20_000;
        int lookups = 2_000;

        List<String> linkedList = new LinkedList<>();
        for (int i = 0; i < n; i++) linkedList.add("task-" + i);

        List<String> arrayList = new ArrayList<>();
        for (int i = 0; i < n; i++) arrayList.add("task-" + i);

        long linkedListTime = timeRandomGets(linkedList, lookups);
        long arrayListTime = timeRandomGets(arrayList, lookups);

        System.out.println(lookups + " random get(index) calls on a list of " + n + " tasks:");
        System.out.println("  LinkedList: " + linkedListTime + " ms");
        System.out.println("  ArrayList:  " + arrayListTime + " ms");
    }

    static long timeRandomGets(List<String> list, int count) {
        Random random = new Random(7);
        long start = System.currentTimeMillis();
        for (int i = 0; i < count; i++) {
            list.get(random.nextInt(list.size()));
        }
        return System.currentTimeMillis() - start;
    }
}
```

**How to run:** `java SchedulerBenchmark.java`. Exact milliseconds vary by machine; the relative gap (`LinkedList` much slower) is the consistent, reproducible result.

Expected output shape:
```
2000 random get(index) calls on a list of 20000 tasks:
  LinkedList: ~150 ms
  ArrayList:  ~1 ms
```

The real-world concern added: quantifying the naive choice's cost directly. `SchedulerNaive`'s status-report feature (`tasks.get(2)`) is cheap in a five-element demo, but scaled up to a realistic queue size, indexed access on a `LinkedList` becomes two orders of magnitude slower than the same calls on an `ArrayList` — purely because of the underlying node-chain-versus-array structural difference from part 3.

### Level 3 — Advanced

```java
import java.util.*;

public class SchedulerHybrid {

    // ArrayDeque for the hot path (FIFO process/enqueue) -- O(1) at both ends, array-backed.
    private final Deque<String> queue = new ArrayDeque<>();

    void enqueue(String task) {
        queue.addLast(task);
    }

    String processNext() {
        return queue.pollFirst();
    }

    // For occasional indexed status reports, snapshot into an ArrayList -- pay the O(n) copy
    // ONLY when a report is actually requested, not on every operation.
    List<String> snapshotForReport() {
        return new ArrayList<>(queue);
    }

    public static void main(String[] args) {
        SchedulerHybrid scheduler = new SchedulerHybrid();
        for (int i = 0; i < 5; i++) {
            scheduler.enqueue("task-" + i);
        }

        System.out.println("processing: " + scheduler.processNext());

        List<String> report = scheduler.snapshotForReport();
        System.out.println("3rd task in current queue: " + report.get(2));
        System.out.println("full queue snapshot: " + report);

        scheduler.enqueue("task-5"); // enqueue stays O(1), unaffected by having taken a snapshot
        System.out.println("processing: " + scheduler.processNext());
    }
}
```

**How to run:** `java SchedulerHybrid.java`.

Expected output:
```
processing: task-0
3rd task in current queue: task-2
full queue snapshot: [task-1, task-2, task-3, task-4]
processing: task-1
```

This adds the production-flavored hard case: a **hybrid design** that uses [`ArrayDeque`](0834-arraydeque.md) (array-backed, O(1) at both ends — faster than `LinkedList` for pure FIFO use, and avoiding `LinkedList`'s per-node memory overhead) for the frequent enqueue/process operations, and only pays the O(n) cost of copying into an `ArrayList` snapshot on the rare occasions a status report actually needs indexed access. This matches each operation to the structure that's actually cheap for it, rather than picking one structure and accepting whichever operations happen to be expensive on it.

## 6. Walkthrough

Tracing `SchedulerHybrid.main`:

1. `scheduler.enqueue(...)` is called five times, each calling `queue.addLast(...)` on the internal `ArrayDeque` — O(1) per call, since `ArrayDeque` (like `ArrayList`) is array-backed and supports O(1) appends at its tail (and, being a `Deque`, at its head too).
2. `scheduler.processNext()` calls `queue.pollFirst()`, removing and returning `"task-0"` in O(1) — `ArrayDeque` supports this directly, unlike `ArrayList`, which would need an O(n) shift for the same operation at index 0.
3. `scheduler.snapshotForReport()` calls `new ArrayList<>(queue)`, copying the queue's four remaining elements into a fresh `ArrayList` — this is the one place an O(n) cost is paid, but only when a report is actually requested, not on every enqueue or process call.
4. `report.get(2)` then runs in O(1) against the snapshot, correctly returning `"task-2"` (the third remaining task, after `"task-0"` was already processed) — indexed access is cheap here because it's operating on the `ArrayList` snapshot, not the original deque.
5. `scheduler.enqueue("task-5")` demonstrates that taking a snapshot didn't change anything about the live queue's performance characteristics — it's still an `ArrayDeque` underneath, still O(1) to enqueue, completely unaffected by the earlier snapshot having been taken.
6. `scheduler.processNext()` again returns the new front of the queue, `"task-1"`, confirming the live structure continued operating correctly and independently of the earlier snapshot copy.

## 7. Gotchas & takeaways

> **Gotcha:** Big-O tables describe *asymptotic* behavior — how cost scales as size grows — not fixed real-world speed. A `LinkedList` can outperform an `ArrayList` in a microbenchmark at very small sizes purely due to constant factors and cache effects, even though the table says `ArrayList.get` is "faster." Always validate an actual performance decision against a benchmark at *realistic* scale for the specific workload, not against the Big-O table alone.

- `ArrayList`: O(1) indexed `get`/`set` and O(1) amortized append at the end; O(n) insertion/removal anywhere else, due to shifting.
- `LinkedList`: O(1) insertion/removal at either end (or at a held iterator position); O(n) indexed `get`, due to chain traversal.
- The same method name (`get`, `add`, `remove`) can have wildly different real cost depending purely on which implementation is chosen — always check which one is actually in play.
- Match the implementation to the dominant access pattern: indexed reads favor `ArrayList`; frequent end-insertion/removal favors `ArrayDeque` or `LinkedList`.
- A hybrid approach — a fast structure for the hot path, plus an occasional cheap-when-rare snapshot copy for less common needs — often beats trying to find one structure that's good at everything.
