---
card: java
gi: 510
slug: tocollection
title: toCollection()
---

## 1. What it is

`Collectors.toCollection(supplier)` is a collector that gathers a stream's elements into a collection you specify, via a `Supplier` that constructs a fresh, empty instance of exactly the collection type you want — `TreeSet::new`, `LinkedList::new`, `ArrayDeque::new`, or any other `Collection` implementation, including your own custom ones. It's the escape hatch for whenever `.toList()` or `Collectors.toSet()`'s default choices (an unmodifiable list, a `HashSet`) aren't the specific collection type your code needs.

## 2. Why & when

`.toList()` gives an unmodifiable `List`; `Collectors.toSet()` gives an unspecified `Set` implementation (commonly `HashSet`, with no ordering guarantee). Neither lets you choose a *specific* concrete type. `Collectors.toCollection(...)` fills that gap: want a mutable `ArrayList` you can keep modifying afterward? A `TreeSet` that keeps elements sorted automatically? A `LinkedHashSet` that preserves insertion order while still deduplicating? All of these are one `Collectors.toCollection(SomeType::new)` call away.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

TreeSet<Integer> sortedUnique = Stream.of(5, 2, 8, 2, 1)
        .collect(Collectors.toCollection(TreeSet::new)); // [1, 2, 5, 8] -- sorted, deduplicated

ArrayList<String> mutableList = Stream.of("a", "b", "c")
        .collect(Collectors.toCollection(ArrayList::new)); // explicitly mutable, unlike toList()
```

`Collectors.toCollection(supplier)` calls the supplier once to create an empty collection, then adds each stream element to it as the stream is consumed — the resulting type is exactly whatever the supplier constructs.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="toCollection lets you choose the exact concrete collection type to collect into">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="52" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">5</text>
  <rect x="85" y="20" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="107" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">2</text>
  <rect x="140" y="20" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="162" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">8</text>
  <rect x="195" y="20" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="217" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">2</text>
  <text x="130" y="70" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">toCollection(TreeSet::new)</text>
  <line x1="130" y1="55" x2="130" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowTC)"/>
  <rect x="55" y="90" width="45" height="30" fill="#1c2430" stroke="#6db33f"/><text x="77" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">1</text>
  <rect x="110" y="90" width="45" height="30" fill="#1c2430" stroke="#6db33f"/><text x="132" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">2</text>
  <rect x="165" y="90" width="45" height="30" fill="#1c2430" stroke="#6db33f"/><text x="187" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">5</text>
  <rect x="220" y="90" width="45" height="30" fill="#1c2430" stroke="#6db33f"/><text x="242" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">8</text>
  <defs><marker id="arrowTC" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`toCollection(TreeSet::new)` produces a `TreeSet` specifically — sorted and deduplicated, because that's what a `TreeSet` does — not just any generic `Set`.

## 5. Runnable example

Scenario: building a priority worklist from a stream of incoming tasks — evolved from collecting into a sorted `TreeSet`, through building an insertion-ordered `LinkedHashSet`, to a version that collects into a custom collection type with its own constraints.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class ToCollectionBasic {
    public static void main(String[] args) {
        List<Integer> priorities = List.of(5, 2, 8, 2, 1, 5);

        TreeSet<Integer> sortedUnique = priorities.stream()
                .collect(Collectors.toCollection(TreeSet::new));

        System.out.println("Sorted, unique priorities: " + sortedUnique);
    }
}
```

**How to run:** `java ToCollectionBasic.java`

Expected output:
```
Sorted, unique priorities: [1, 2, 5, 8]
```

`Collectors.toCollection(TreeSet::new)` constructs an empty `TreeSet<Integer>` and adds each stream element to it. `TreeSet`'s own nature — sorted, deduplicated, backed by a red-black tree — automatically gives the sorted, duplicate-free result `[1, 2, 5, 8]`, entirely through the collection type's own behavior, not any special stream logic.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class ToCollectionLinkedHashSet {
    public static void main(String[] args) {
        List<String> taskTags = List.of("urgent", "backend", "urgent", "frontend", "backend");

        // LinkedHashSet: deduplicates like HashSet, but remembers insertion (first-seen) order.
        LinkedHashSet<String> firstSeenOrder = taskTags.stream()
                .collect(Collectors.toCollection(LinkedHashSet::new));

        System.out.println("Tags in first-seen order: " + firstSeenOrder);
    }
}
```

**How to run:** `java ToCollectionLinkedHashSet.java`

Expected output:
```
Tags in first-seen order: [urgent, backend, frontend]
```

The real-world concern this adds: plain `Collectors.toSet()` would deduplicate but give no ordering guarantee at all (in practice, `HashSet`'s iteration order depends on hash codes, not insertion order). `LinkedHashSet::new` still deduplicates, but preserves the order each distinct tag was *first* encountered — `"urgent"` first, then `"backend"`, then `"frontend"` — useful whenever "the order things first appeared" itself carries meaning.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class ToCollectionCustom {
    record Task(String name, int priority) {}

    // A small custom collection that caps its size, silently dropping additions past the limit.
    static class BoundedList<T> extends ArrayList<T> {
        private final int maxSize;
        BoundedList(int maxSize) { this.maxSize = maxSize; }
        @Override public boolean add(T item) {
            return size() < maxSize && super.add(item);
        }
    }

    public static void main(String[] args) {
        List<Task> tasks = List.of(
                new Task("Fix login bug", 9),
                new Task("Update docs", 2),
                new Task("Security patch", 10),
                new Task("Refactor logging", 3),
                new Task("Database migration", 8)
        );

        // Take the top 3 by priority, collected directly into a size-capped custom collection.
        BoundedList<Task> topThree = tasks.stream()
                .sorted(Comparator.comparing(Task::priority).reversed())
                .collect(Collectors.toCollection(() -> new BoundedList<>(3)));

        topThree.forEach(t -> System.out.println(t.name() + " (priority " + t.priority() + ")"));
        System.out.println("Worklist size: " + topThree.size());
    }
}
```

**How to run:** `java ToCollectionCustom.java`

Expected output:
```
Security patch (priority 10)
Fix login bug (priority 9)
Database migration (priority 8)
Worklist size: 3
```

This uses `Collectors.toCollection(...)` with a **custom** collection type (`BoundedList`, a small `ArrayList` subclass that silently refuses additions past a fixed size). Even though `sorted(...)` produces all five tasks in priority order, the collector's target collection itself enforces the cap — only the first three `add(...)` calls actually succeed, so `topThree` ends up holding exactly the three highest-priority tasks, with no separate `.limit(3)` call needed in the pipeline (though using `.limit(3)` would be the more conventional and readable way to achieve this same result in most real code).

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `tasks` holds five entries with priorities `9, 2, 10, 3, 8`.

`tasks.stream().sorted(Comparator.comparing(Task::priority).reversed())` arranges all five tasks by priority, highest first: `Security patch (10)`, `Fix login bug (9)`, `Database migration (8)`, `Refactor logging (3)`, `Update docs (2)`.

`.collect(Collectors.toCollection(() -> new BoundedList<>(3)))` calls the supplier once to create an empty `BoundedList<Task>` with `maxSize = 3`, then feeds each of the five sorted tasks to it via `add(...)`, in order.

For `Security patch` (priority `10`, first in sorted order): `add` checks `size() < maxSize`, i.e. `0 < 3`, `true` — the task is added, `super.add(item)` succeeds, size becomes `1`.

For `Fix login bug` (priority `9`): `size() < maxSize` is `1 < 3`, `true` — added, size becomes `2`.

For `Database migration` (priority `8`): `size() < maxSize` is `2 < 3`, `true` — added, size becomes `3`.

For `Refactor logging` (priority `3`): `size() < maxSize` is `3 < 3`, `false` — the `&&` short-circuits, `super.add(item)` is never called, `add` returns `false`, the collection's size stays `3`.

For `Update docs` (priority `2`): same as above — `size() < maxSize` is `3 < 3`, `false`, rejected.

```
sorted order: Security(10), Fix login(9), DB migration(8), Refactor(3), Update docs(2)

add(Security,10)     -> 0<3 true  -> added, size=1
add(Fix login,9)     -> 1<3 true  -> added, size=2
add(DB migration,8)  -> 2<3 true  -> added, size=3
add(Refactor,3)      -> 3<3 false -> REJECTED, size stays 3
add(Update docs,2)   -> 3<3 false -> REJECTED, size stays 3
```

The final `topThree` contains exactly the three highest-priority tasks, in the order they were fed to it: `Security patch`, `Fix login bug`, `Database migration`. `.forEach(...)` prints all three, and `topThree.size()` confirms `3` — the custom `BoundedList`'s own `add` override enforced the cap directly, purely because that's the behavior of the collection type the collector was told to build.

## 7. Gotchas & takeaways

> The collection returned by `Collectors.toCollection(...)` inherits whatever behavior its own type has — including any quirks. A `TreeSet` requires its elements to be mutually comparable (either via `Comparable` or an explicit `Comparator` passed to its constructor), and will throw `ClassCastException` at the first `add` if given elements with no natural ordering and no comparator supplied. Choose the target collection type deliberately, with its specific behavior in mind, not just as an arbitrary container.

- `Collectors.toCollection(supplier)` collects into exactly the concrete collection type the supplier constructs — full control over the result type, unlike `.toList()` or `Collectors.toSet()`.
- Common choices: `TreeSet::new` for sorted + deduplicated, `LinkedHashSet::new` for insertion-ordered + deduplicated, `ArrayList::new` for an explicitly mutable list, `ArrayDeque::new` for a double-ended queue.
- The supplier is called exactly once to create a fresh, empty collection — each element is then added to it one at a time as the stream is consumed.
- Since the collection is a genuine, standard implementation, it inherits that type's real behavior and constraints (e.g. `TreeSet` needing comparability), not stream-specific logic layered on top.
- For simply capping a stream's result to a fixed number of elements, `.limit(n)` (see [[limit]]) before collecting is the more idiomatic approach than relying on a custom size-capping collection, as shown in Level 3 purely to illustrate custom collection support.
