---
card: java
gi: 614
slug: list-copyof-set-copyof-map-copyof
title: List.copyOf / Set.copyOf / Map.copyOf
---

## 1. What it is

Java 10 added static factory methods `List.copyOf(Collection)`, `Set.copyOf(Collection)`, and `Map.copyOf(Map)` that create **unmodifiable** shallow copies of existing collections. Unlike `Collections.unmodifiableList()` (which wraps the original collection and reflects mutations to the backing store), `copyOf` creates a snapshot — it copies the elements into a new internal structure, so the resulting collection is truly immutable and independent of the original. If the input is already an unmodifiable collection (e.g. from `List.of()`), `copyOf` returns it directly without an extra copy.

## 2. Why & when

The difference between "unmodifiable view" and "immutable copy" is critical for defensive programming. `Collections.unmodifiableList(list)` returns a view — if the original `list` is modified, those changes are visible through the "unmodifiable" wrapper. This has been a source of subtle bugs for decades. `List.copyOf()` solves this by always creating a snapshot: mutations to the original collection after the `copyOf` call have no effect on the copy. This makes `copyOf` the correct tool for returning internal state to callers, caching computation results, and ensuring thread safety without synchronisation.

## 3. Core concept

```java
var original = new ArrayList<String>();
original.add("a");
original.add("b");

// copyOf creates an independent snapshot
var copy = List.copyOf(original);
original.add("c");  // original now [a, b, c], copy still [a, b]

// copy.add("x");   // throws UnsupportedOperationException — immutable

// If input is already unmodifiable, copyOf returns the same object
var fromFactory = List.of("x", "y");
var copy2 = List.copyOf(fromFactory);
System.out.println(fromFactory == copy2); // true — no wasted copy
```

`copyOf` guarantees: (1) the result is unmodifiable, (2) the result is independent of the source (snapshot semantics), (3) null elements are rejected (`NullPointerException`), and (4) if the source is already unmodifiable, the existing instance is returned to avoid unnecessary copying.

## 4. Diagram

<svg viewBox="0 0 580 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="copyOf creates an independent snapshot; unmodifiable wrapper just creates a view">
  <rect x="20" y="10" width="540" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="30" y="30" width="120" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="90" y="55" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">mutable list</text>
  <text x="90" y="67" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">[a, b]</text>

  <text x="160" y="50" fill="#8b949e" font-size="10" font-family="monospace">──►</text>

  <rect x="175" y="30" width="130" height="40" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="240" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">List.copyOf()</text>

  <text x="315" y="50" fill="#8b949e" font-size="10" font-family="monospace">──►</text>

  <rect x="330" y="30" width="120" height="40" rx="4" fill="#0d1117" stroke="#6db33f"/>
  <text x="390" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">immutable copy</text>
  <text x="390" y="67" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">[a, b]</text>

  <text x="460" y="50" fill="#f85149" font-size="18" font-family="monospace">✕</text>
  <text x="475" y="67" fill="#f85149" font-size="8" font-family="sans-serif">independent</text>

  <rect x="30" y="90" width="120" height="40" rx="4" fill="#0d1117" stroke="#f85149"/>
  <text x="90" y="115" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">mutable list</text>
  <text x="90" y="127" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">[a, b]</text>

  <text x="160" y="110" fill="#8b949e" font-size="10" font-family="monospace">──►</text>

  <rect x="175" y="90" width="150" height="40" rx="4" fill="#f85149" stroke="#f85149"/>
  <text x="250" y="115" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">unmodifiableList()</text>

  <text x="335" y="110" fill="#8b949e" font-size="10" font-family="monospace">──►</text>

  <rect x="345" y="90" width="120" height="40" rx="4" fill="#0d1117" stroke="#f85149"/>
  <text x="405" y="115" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">view (wrapper)</text>
  <text x="405" y="127" fill="#f85149" font-size="8" text-anchor="middle" font-family="monospace">[a, b]</text>

  <text x="475" y="110" fill="#6db33f" font-size="18" font-family="monospace">→</text>
  <text x="490" y="127" fill="#6db33f" font-size="8" font-family="sans-serif">reflects</text>

  <text x="30" y="160" fill="#8b949e" font-size="9" font-family="sans-serif">copyOf → independent snapshot (safe) | unmodifiableList → live view (mutations leak)</text>
</svg>

`copyOf` creates a snapshot — the copy is unaffected by later changes to the source. `unmodifiableList` creates a view — changes to the source are visible through the wrapper.

## 5. Runnable example

Scenario: a defensive programming pattern where a service returns internal state to callers — starting with basic copy creation, extending to snapshot semantics vs view semantics, and finally building a thread-safe cache that uses `copyOf` to safely publish data.

### Level 1 — Basic

```java
// File: CopyOfDemo.java
import java.util.*;

public class CopyOfDemo {
    public static void main(String[] args) {
        // Create mutable source lists
        var mutableList = new ArrayList<>(List.of("a", "b", "c"));
        var mutableSet  = new HashSet<>(Set.of(1, 2, 3));
        var mutableMap  = new HashMap<>(Map.of("k1", "v1", "k2", "v2"));

        // Create unmodifiable copies
        var listCopy = List.copyOf(mutableList);
        var setCopy  = Set.copyOf(mutableSet);
        var mapCopy  = Map.copyOf(mutableMap);

        System.out.println("Copies: " + listCopy + " | " + setCopy + " | " + mapCopy);

        // Mutate originals
        mutableList.add("d");
        mutableSet.add(4);
        mutableMap.put("k3", "v3");

        System.out.println("After mutating originals:");
        System.out.println("  Original list: " + mutableList);
        System.out.println("  Copy (unchanged): " + listCopy);

        // Copy is truly immutable
        try {
            listCopy.add("x");
        } catch (UnsupportedOperationException e) {
            System.out.println("  Copy rejects modification: " + e.getClass().getSimpleName());
        }
    }
}
```

**How to run:** `java CopyOfDemo.java`

Expected output:
```
Copies: [a, b, c] | [1, 2, 3] | {k1=v1, k2=v2}
After mutating originals:
  Original list: [a, b, c, d]
  Copy (unchanged): [a, b, c]
  Copy rejects modification: UnsupportedOperationException
```

The simplest demonstration: snapshot semantics. After adding `"d"` to the original list, the copy still contains only `[a, b, c]`. The copy is also genuinely immutable — calling `add()` throws `UnsupportedOperationException`.

### Level 2 — Intermediate

```java
// File: SnapshotVsView.java
import java.util.*;

public class SnapshotVsView {

    static class OrderService {
        private final List<String> recentOrders = new ArrayList<>();

        void placeOrder(String orderId) {
            recentOrders.add(orderId);
        }

        // BAD: unmodifiable view — leaks internal state changes
        List<String> getRecentOrdersView() {
            return Collections.unmodifiableList(recentOrders);
        }

        // GOOD: copyOf — creates an independent snapshot
        List<String> getRecentOrdersSnapshot() {
            return List.copyOf(recentOrders);
        }
    }

    public static void main(String[] args) {
        var service = new OrderService();
        service.placeOrder("ORD-1");

        var view = service.getRecentOrdersView();
        var snapshot = service.getRecentOrdersSnapshot();

        System.out.println("After ORD-1:");
        System.out.println("  View:     " + view);
        System.out.println("  Snapshot: " + snapshot);

        // New order placed
        service.placeOrder("ORD-2");

        System.out.println("\nAfter ORD-2 (view leaks the change!):");
        System.out.println("  View:     " + view + "     ← CHANGED (live view!)");
        System.out.println("  Snapshot: " + snapshot + "   ← UNCHANGED (snapshot!)");
    }
}
```

**How to run:** `java SnapshotVsView.java`

Expected output:
```
After ORD-1:
  View:     [ORD-1]
  Snapshot: [ORD-1]

After ORD-2 (view leaks the change!):
  View:     [ORD-1, ORD-2]     ← CHANGED (live view!)
  Snapshot: [ORD-1]   ← UNCHANGED (snapshot!)
```

The real-world concern: `Collections.unmodifiableList()` returns a live view — when a new order is placed, the previously obtained view reflects it, potentially breaking the caller's assumption that the list is stable. `List.copyOf()` returns a snapshot — the previously obtained copy is unaffected by later orders. This is the crucial difference for defensive programming.

### Level 3 — Advanced

```java
// File: ThreadSafeCache.java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

public class ThreadSafeCache {

    record CacheEntry(String key, List<String> values, long timestamp) {}

    // Internal mutable state — never exposed directly
    private final ConcurrentHashMap<String, List<String>> storage = new ConcurrentHashMap<>();

    void addValue(String key, String value) {
        storage.compute(key, (k, list) -> {
            var newList = list == null ? new ArrayList<>() : new ArrayList<>(list);
            newList.add(value);
            return newList;
        });
    }

    // Thread-safe read: returns an independent snapshot
    CacheEntry getSnapshot(String key) {
        var current = storage.get(key);
        if (current == null) return null;
        return new CacheEntry(
            key,
            List.copyOf(current),    // snapshot — caller can't mutate storage
            System.currentTimeMillis()
        );
    }

    // Bulk snapshot of all entries
    Map<String, List<String>> getAllSnapshots() {
        var result = new HashMap<String, List<String>>();
        storage.forEach((k, v) -> result.put(k, List.copyOf(v)));
        return Map.copyOf(result);  // even the map itself is unmodifiable
    }

    public static void main(String[] args) {
        var cache = new ThreadSafeCache();
        cache.addValue("users", "Alice");
        cache.addValue("users", "Bob");
        cache.addValue("orders", "ORD-1");
        cache.addValue("users", "Charlie");

        var snapshot = cache.getSnapshot("users");
        System.out.println("Snapshot of 'users': " + snapshot.values());

        // Mutate the snapshot (impossible — it's unmodifiable)
        try {
            snapshot.values().add("Mallory");
        } catch (UnsupportedOperationException e) {
            System.out.println("Cannot mutate snapshot: " + e.getClass().getSimpleName());
        }

        // Subsequent snapshot reflects new additions
        cache.addValue("users", "Diana");
        var snapshot2 = cache.getSnapshot("users");
        System.out.println("Later snapshot: " + snapshot2.values());

        // Bulk snapshot
        System.out.println("\nAll snapshots:");
        var all = cache.getAllSnapshots();
        all.forEach((k, v) -> System.out.println("  " + k + " → " + v));
    }
}
```

**How to run:** `java ThreadSafeCache.java`

Expected output:
```
Snapshot of 'users': [Alice, Bob, Charlie]
Cannot mutate snapshot: UnsupportedOperationException
Later snapshot: [Alice, Bob, Charlie, Diana]

All snapshots:
  users → [Alice, Bob, Charlie, Diana]
  orders → [ORD-1]
```

The production-flavoured pattern: a thread-safe cache that uses `ConcurrentHashMap` internally but never exposes mutable references. Every read returns a `List.copyOf()` snapshot, ensuring the caller receives a stable, independent view. The bulk `getAllSnapshots()` returns `Map.copyOf()` to prevent the caller from mutating the map itself. This is the correct way to safely publish internal collection state in concurrent code.

## 6. Walkthrough

Tracing `getSnapshot("users")` in the Level 3 example:

1. `cache.getSnapshot("users")` is called. `storage.get("users")` retrieves the current `ArrayList` from the `ConcurrentHashMap`. At this point, the list contains `["Alice", "Bob", "Charlie"]`.

2. `List.copyOf(current)` is called. Internally, this method:
   - Checks if `current` is already an instance of `AbstractImmutableList` (the type used by `List.of()`). It's not — it's an `ArrayList`.
   - Creates a new array from `current.toArray()`.
   - Wraps it in an internal unmodifiable list implementation (`ListN` or `List12`).
   - On JDK 10, this creates a fresh internal list; on JDK 11+, it uses `Arrays.copyOf` for the element array and wraps it.
   - The returned list contains `["Alice", "Bob", "Charlie"]` and is completely independent of the `ArrayList` in `storage`.

3. A `CacheEntry` is constructed with the key, the snapshot list, and the current timestamp.

4. The caller receives `CacheEntry`. They cannot modify `snapshot.values()` — attempting `add("Mallory")` throws `UnsupportedOperationException`. The internal `storage` remains unmodified.

5. Later, `cache.addValue("users", "Diana")` computes a new `ArrayList` within `compute()`. The next `getSnapshot("users")` call creates a fresh snapshot containing `["Alice", "Bob", "Charlie", "Diana"]`. The previous snapshot (without Diana) is unaffected — it's an independent copy.

## 7. Gotchas & takeaways

> `copyOf` rejects `null` elements — passing a collection containing `null` throws `NullPointerException`. This differs from `Collections.unmodifiableList()`, which allows null elements. If your data may contain nulls, `copyOf` is not the right tool; use `Collections.unmodifiableList()` or filter nulls first.

- `copyOf` performs a **shallow** copy — the collection structure is copied, but the element references are shared. Modifying a mutable element object (e.g., calling `setter` on a `Person` object in the list) affects both the original and the copy. `copyOf` protects against collection-level mutations, not element-level mutations.
- If the input is already an unmodifiable collection from `List.of()`, `Set.of()`, `Map.of()`, or a previous `copyOf()` call, `copyOf` returns the **same instance** — no allocation, no copying. This is an optimisation that makes cascading `copyOf` calls cheap.
- `Set.copyOf()` deduplicates — if the source collection has duplicates (e.g. an `ArrayList` with two `"a"` elements), only one `"a"` appears in the resulting set. `List.copyOf()` preserves order and duplicates.
- `Map.copyOf()` copies both keys and values — if the values are mutable objects, the same shallow-copy caveat applies. The key-value associations are fixed, but the referenced objects are shared.
- There is no `copyOf` for queues, deques, or other collection types — the three methods cover the three main collection interfaces. For other types, use the copy constructor (e.g. `new ArrayList<>(collection)`) followed by `Collections.unmodifiableList()` or write your own defensive copy. 