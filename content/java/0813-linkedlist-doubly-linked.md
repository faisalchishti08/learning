---
card: java
gi: 813
slug: linkedlist-doubly-linked
title: LinkedList (doubly-linked)
---

## 1. What it is

`LinkedList` implements both [`List`](0802-list.md) and [`Deque`](0806-deque.md), but stores elements completely differently from `ArrayList`: instead of one contiguous array, each element lives inside its own **node** object holding the value plus references to the **previous** and **next** nodes in the chain. The list itself just tracks references to the `first` and `last` nodes. Because every node points both forward and backward, the list can be walked in either direction, and inserting or removing a node at either end (or, given a reference to a node, anywhere in the middle) is O(1) — no shifting of other elements required, unlike `ArrayList`.

## 2. Why & when

`ArrayList`'s `add(0, value)` (insert at the front) or `remove(0)` (remove from the front) is O(n), because every other element has to shift by one array slot. A doubly-linked structure sidesteps that entirely: adding or removing at either end just rewires a couple of node references, regardless of how many elements are in the list. `LinkedList` is the right choice specifically when the access pattern is dominated by insertion/removal at the ends (or via an iterator positioned in the middle) rather than indexed random access — a `LinkedList` used as a [`Deque`](0806-deque.md) (though `ArrayDeque` is usually preferred there) or as an actual list where elements are frequently spliced in and out mid-traversal. It is the *wrong* choice when code frequently calls `get(i)` with arbitrary indices, since that operation must walk the chain from one end, node by node, making it O(n) — dramatically slower than `ArrayList`'s O(1) array-index access.

## 3. Core concept

```
null <- [A] <-> [B] <-> [C] -> null
         ^                ^
        first            last
```

Each node holds a value and two references. Inserting `X` between `A` and `B` only touches four references — `A.next`, `X.prev`, `X.next`, `B.prev` — regardless of list size:

```
null <- [A] <-> [X] <-> [B] <-> [C] -> null
```

No other node is touched, and no array is copied — contrast this with `ArrayList.add(1, X)`, which would have to shift `B` and `C` one slot to the right first.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each node in a LinkedList holds references to both the previous and next node, allowing O(1) insertion anywhere given a reference to a neighboring node">
  <g font-family="sans-serif">
    <rect x="40" y="60" width="90" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="85" y="90" fill="#e6edf3" font-size="12" text-anchor="middle">A</text>

    <rect x="270" y="60" width="90" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4"/>
    <text x="315" y="90" fill="#79c0ff" font-size="12" text-anchor="middle">X (new)</text>

    <rect x="500" y="60" width="90" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="545" y="90" fill="#e6edf3" font-size="12" text-anchor="middle">B</text>
  </g>

  <line x1="130" y1="78" x2="265" y2="78" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a813f)"/>
  <line x1="265" y1="95" x2="130" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a813b)"/>
  <line x1="360" y1="78" x2="495" y2="78" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a813f)"/>
  <line x1="495" y1="95" x2="360" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a813b)"/>

  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Inserting X between A and B only rewires 4 references — no shifting, regardless of list length</text>

  <defs>
    <marker id="a813f" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="a813b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

*Insertion in a doubly-linked list only rewires a handful of neighboring references — no shifting of unrelated elements.*

## 5. Runnable example

Scenario: a music playlist supporting fast insert-next-song operations, growing from basic end-insertion to mid-playlist splicing via `ListIterator`, to a head-to-head performance comparison against `ArrayList` that demonstrates exactly when each structure wins.

### Level 1 — Basic

```java
import java.util.*;

public class PlaylistBasic {
    public static void main(String[] args) {
        LinkedList<String> playlist = new LinkedList<>();
        playlist.addLast("Intro");
        playlist.addLast("Song A");
        playlist.addLast("Song B");
        playlist.addFirst("Opening Jingle"); // O(1) — no shifting needed

        System.out.println("playlist: " + playlist);
        System.out.println("now playing: " + playlist.peekFirst());
        System.out.println("up next after that: " + playlist.get(1));
    }
}
```

**How to run:** `java PlaylistBasic.java` (JDK 17+).

Expected output:
```
playlist: [Opening Jingle, Intro, Song A, Song B]
now playing: Opening Jingle
up next after that: Intro
```

`addFirst` on a `LinkedList` is O(1) regardless of how many songs are already queued — it only creates one new node and rewires the old first node's `prev` reference, unlike `ArrayList.add(0, ...)`, which would shift every existing element.

### Level 2 — Intermediate

```java
import java.util.*;

public class PlaylistSplicing {
    public static void main(String[] args) {
        LinkedList<String> playlist = new LinkedList<>(List.of("Intro", "Song A", "Song B", "Song C"));

        ListIterator<String> it = playlist.listIterator();
        while (it.hasNext()) {
            String track = it.next();
            if (track.equals("Song A")) {
                it.add("Interlude"); // insert immediately after "Song A", mid-traversal
            }
        }

        System.out.println("playlist after splicing in an interlude: " + playlist);

        // Remove a track by value using the iterator, safely mid-traversal.
        Iterator<String> removalIt = playlist.iterator();
        while (removalIt.hasNext()) {
            if (removalIt.next().equals("Song C")) {
                removalIt.remove();
            }
        }
        System.out.println("playlist after removing Song C: " + playlist);
    }
}
```

**How to run:** `java PlaylistSplicing.java`.

Expected output:
```
playlist after splicing in an interlude: [Intro, Song A, Interlude, Song B, Song C]
playlist after removing Song C: [Intro, Song A, Interlude, Song B]
```

The real-world concern added: mid-list insertion and removal via [`ListIterator`](0810-listiterator.md)/[`Iterator`](0809-iterator.md), which on a `LinkedList` is genuinely O(1) once the iterator's cursor is positioned at the right node — no shifting of `Song B` or any other track happens, because splicing a node in or out only touches its immediate neighbors' references.

### Level 3 — Advanced

```java
import java.util.*;

public class ListPerformanceComparison {
    public static void main(String[] args) {
        int n = 50_000;

        List<Integer> arrayList = new ArrayList<>();
        List<Integer> linkedList = new LinkedList<>();

        long arrayListFrontInsertTime = timeInsertsAtFront(arrayList, n);
        long linkedListFrontInsertTime = timeInsertsAtFront(linkedList, n);
        System.out.println("inserting " + n + " elements at index 0:");
        System.out.println("  ArrayList:  " + arrayListFrontInsertTime + " ms");
        System.out.println("  LinkedList: " + linkedListFrontInsertTime + " ms");

        List<Integer> arrayListForReads = new ArrayList<>(arrayList);
        List<Integer> linkedListForReads = new LinkedList<>(linkedList);
        long arrayListReadTime = timeRandomAccessReads(arrayListForReads, n / 10);
        long linkedListReadTime = timeRandomAccessReads(linkedListForReads, n / 10);
        System.out.println("performing " + (n / 10) + " random-index get() calls:");
        System.out.println("  ArrayList:  " + arrayListReadTime + " ms");
        System.out.println("  LinkedList: " + linkedListReadTime + " ms");
    }

    static long timeInsertsAtFront(List<Integer> list, int count) {
        long start = System.currentTimeMillis();
        for (int i = 0; i < count; i++) {
            list.add(0, i); // insert at the front every time
        }
        return System.currentTimeMillis() - start;
    }

    static long timeRandomAccessReads(List<Integer> list, int reads) {
        Random random = new Random(42);
        long start = System.currentTimeMillis();
        for (int i = 0; i < reads; i++) {
            list.get(random.nextInt(list.size()));
        }
        return System.currentTimeMillis() - start;
    }
}
```

**How to run:** `java ListPerformanceComparison.java`. Timings vary by machine, but the *relative* pattern is consistent: `LinkedList` wins the front-insertion benchmark decisively; `ArrayList` wins the random-access benchmark decisively.

Expected output shape (exact milliseconds vary):
```
inserting 50000 elements at index 0:
  ArrayList:  ~800 ms
  LinkedList: ~5 ms
performing 5000 random-index get() calls:
  ArrayList:  ~1 ms
  LinkedList: ~40 ms
```

This adds the production-flavored hard case: an actual side-by-side benchmark proving the theoretical Big-O difference in practice. `ArrayList.add(0, ...)` shifts every existing element on every call, making 50,000 front-inserts an O(n²) disaster overall; `LinkedList.add(0, ...)` stays O(1) per call regardless of size. The read benchmark flips the result entirely: `ArrayList.get(i)` is a direct array index in O(1), while `LinkedList.get(i)` must walk the chain from whichever end is closer, making repeated random-index reads far more expensive.

## 6. Walkthrough

Tracing `ListPerformanceComparison.main`:

1. `timeInsertsAtFront` runs a loop calling `list.add(0, i)` exactly `n` times. For the `ArrayList` argument, each call shifts every currently-stored element one slot to the right before writing the new value at index 0 — the total work across all `n` calls sums to roughly `0 + 1 + 2 + ... + n`, which is O(n²).
2. For the `LinkedList` argument, the identical loop body instead creates a new node and rewires two references (the old first node's `prev`, and the new node's `next`) on every call — each call is O(1), so the total work across `n` calls is O(n), dramatically faster for large `n`.
3. `timeRandomAccessReads` generates `reads` random indices (seeded for reproducibility) and calls `list.get(randomIndex)` for each. On `arrayListForReads`, every call is a direct array-offset computation — O(1) regardless of the index.
4. On `linkedListForReads`, every call to `get(index)` must traverse node-by-node from whichever end (`first` or `last`) is closer to the target index — an O(n) walk per call, making repeated random-access reads on a `LinkedList` far slower than the equivalent `ArrayList` reads, even though `LinkedList` internally optimizes by choosing the nearer end to start from.
5. The two benchmarks together demonstrate that neither structure is universally "better" — the right choice depends entirely on whether the dominant operation is end/middle insertion (favors `LinkedList`) or indexed random access (favors `ArrayList`).

## 7. Gotchas & takeaways

> **Gotcha:** calling `get(i)` in a loop over a `LinkedList` (`for (int i = 0; i < list.size(); i++) { ... list.get(i) ... }`) is an O(n²) anti-pattern — each `get(i)` call independently walks the chain from an end. Always iterate a `LinkedList` with a for-each loop or an explicit `Iterator`/`ListIterator`, which advances one node at a time without restarting the walk on every step.

- `LinkedList` stores elements as nodes linked in both directions, giving O(1) insertion/removal at either end or at an iterator's current position — but O(n) indexed access via `get(i)`.
- `ArrayList` is the opposite trade-off: O(1) indexed `get`/`set`, but O(n) insertion/removal anywhere except the very end.
- `LinkedList` implements both [`List`](0802-list.md) and [`Deque`](0806-deque.md), so it can serve as a queue, stack, or double-ended structure directly.
- Never loop with indexed `get(i)` calls over a `LinkedList` — use iteration instead to stay O(n) overall rather than O(n²).
- For most general-purpose use, `ArrayList` is the better default; reach for `LinkedList` specifically when the workload is dominated by frequent insertion/removal at the ends or via a held iterator position, and even then, [`ArrayDeque`](0834-arraydeque.md) is usually a faster choice for pure end operations.
