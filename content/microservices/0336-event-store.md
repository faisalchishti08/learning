---
card: microservices
gi: 336
slug: event-store
title: "Event store"
---

## 1. What it is

An **event store** is a database purpose-built for [event sourcing](0335-event-sourcing.md): it stores events grouped into per-entity, append-only **streams** (all of `order-1`'s events, all of `order-2`'s events, and so on), guarantees events within a stream are strictly ordered, and is optimized for its two core operations — appending a new event to a stream, and reading a stream's events in order from the beginning (or from a given point) to fold into current state. This is a different access pattern than a conventional table optimized for "find and overwrite the one current row for this ID."

## 2. Why & when

A conventional relational table could technically hold events too — an `events` table with an `entity_id` column and an `ORDER BY sequence_number` query — and for smaller systems, this is a perfectly reasonable starting point. A dedicated event store becomes valuable once you need guarantees a general-purpose table doesn't give you for free: strict per-stream append ordering under concurrent writers (so two processes appending to the same order's stream at once can't silently interleave incorrectly), optimistic concurrency built into the append operation itself (reject an append if the stream's version has moved since you last read it), and efficient reading of a single stream without scanning unrelated data.

Use a dedicated event store (EventStoreDB, or an event-sourcing-shaped schema on top of a general database like Postgres) once your event-sourced entities need real production guarantees around concurrent writes and read performance. For prototypes or lower-throughput domains, a plain table with careful application-level discipline (checking version numbers yourself) can suffice as a starting point before reaching for specialized infrastructure.

## 3. Core concept

Every stream has a name (usually the entity's type and ID, like `order-order-1`) and a monotonically increasing **version** (or sequence number). Appending requires stating the expected current version; if the actual stored version has moved on (because another append already happened), the append is rejected — this is the store's built-in optimistic concurrency check, needed because two processes might otherwise race to append conflicting events to the same stream.

```java
interface EventStore {
    void append(String streamId, int expectedVersion, Event event); // throws if expectedVersion is stale
    List<Event> readStream(String streamId); // in strict order, from the beginning
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two processes both try to append to the order-1 stream at expected version 2; the first succeeds and the stream advances to version 3; the second is rejected because the stream is no longer at version 2">
  <rect x="230" y="20" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Stream order-1 @ version 2</text>

  <rect x="30" y="90" width="200" height="40" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="130" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Process A: append(expected=2)</text>
  <rect x="410" y="90" width="200" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="510" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Process B: append(expected=2)</text>

  <line x1="130" y1="90" x2="290" y2="54" stroke="#3fb950" marker-end="url(#a336)"/>
  <text x="200" y="70" fill="#3fb950" font-size="9" font-family="sans-serif">SUCCEEDS -&gt; version 3</text>
  <line x1="510" y1="90" x2="350" y2="54" stroke="#f85149" marker-end="url(#a336)"/>
  <text x="440" y="70" fill="#f85149" font-size="9" font-family="sans-serif">REJECTED, stream moved</text>

  <defs><marker id="a336" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The event store rejects an append whose expected version no longer matches the stream's actual current version, preventing conflicting concurrent writes.

## 5. Runnable example

Scenario: a minimal in-memory event store, first shown allowing an append with no concurrency protection (letting a race condition corrupt a stream), then fixed with expected-version checking, and finally extended with a reader that folds a stream efficiently by only reading from a given version onward.

### Level 1 — Basic

```java
// File: NoVersionCheckStore.java -- appends with NO concurrency check;
// two processes reading the same version can both append, silently
// creating conflicting parallel history.
import java.util.*;

public class NoVersionCheckStore {
    static Map<String, List<String>> streams = new HashMap<>();

    static void append(String streamId, String event) { // no version argument at all
        streams.computeIfAbsent(streamId, k -> new ArrayList<>()).add(event);
        System.out.println("appended '" + event + "' to " + streamId + ", now at version " + streams.get(streamId).size());
    }

    public static void main(String[] args) {
        append("order-1", "OrderPlaced");

        // Two processes BOTH read the stream at version 1 and decide to append their own next event.
        System.out.println("Process A and Process B BOTH read version 1, unaware of each other:");
        append("order-1", "ItemAdded(widget)");   // process A's append
        append("order-1", "ItemAdded(gadget)");   // process B's append -- should this have conflicted with A's?

        System.out.println("Final stream: " + streams.get("order-1") + " -- BOTH landed, no conflict was ever detected.");
    }
}
```

How to run: `java NoVersionCheckStore.java`

Both appends succeed unconditionally — there is no way to express "only append this if the stream is still at the version I read," so two processes that both decided to add an item based on the same starting point can both succeed, even if their business logic assumed they were the only one appending at that moment.

### Level 2 — Intermediate

```java
// File: OptimisticConcurrencyStore.java -- append now REQUIRES an
// expected version and REJECTS the call if the stream has moved on,
// exactly like a real event store's core guarantee.
import java.util.*;

public class OptimisticConcurrencyStore {
    static Map<String, List<String>> streams = new HashMap<>();

    static boolean append(String streamId, int expectedVersion, String event) {
        List<String> stream = streams.computeIfAbsent(streamId, k -> new ArrayList<>());
        if (stream.size() != expectedVersion) {
            System.out.println("append REJECTED: " + streamId + " is at version " + stream.size()
                    + ", expected " + expectedVersion);
            return false;
        }
        stream.add(event);
        System.out.println("append SUCCEEDED: " + streamId + " now at version " + stream.size());
        return true;
    }

    public static void main(String[] args) {
        append("order-1", 0, "OrderPlaced"); // stream starts empty (version 0), append succeeds -> version 1

        // Both processes read the stream at version 1 and attempt to append based on that.
        boolean processASucceeded = append("order-1", 1, "ItemAdded(widget)"); // succeeds -> version 2
        boolean processBSucceeded = append("order-1", 1, "ItemAdded(gadget)"); // REJECTED -- stream is now at version 2, not 1

        System.out.println("Process A succeeded? " + processASucceeded + ", Process B succeeded? " + processBSucceeded);
        System.out.println("Process B must REREAD the stream (now at version 2) and retry its append.");
    }
}
```

How to run: `java OptimisticConcurrencyStore.java`

Process A's append passes `expectedVersion=1`, which matches the stream's actual size at that moment, so it succeeds and the stream grows to version `2`. Process B's append also passes `expectedVersion=1` (based on its own earlier read), but by the time it runs, the stream is already at version `2` — the mismatch is detected, the append is rejected, and Process B is correctly told to reread the current stream and retry, rather than silently corrupting the stream with an append based on stale assumptions.

### Level 3 — Advanced

```java
// File: EfficientStreamReadFromVersion.java -- reading a stream to fold
// its current state doesn't need to start from scratch every time; this
// store lets a reader resume folding from a KNOWN prior version plus its
// already-computed partial state, avoiding refolding the whole history.
import java.util.*;

public class EfficientStreamReadFromVersion {
    record CachedFold(int asOfVersion, List<String> itemsSoFar) {}
    static Map<String, List<String>> streams = new HashMap<>();
    static Map<String, CachedFold> foldCache = new HashMap<>(); // NOT a full snapshot store, just a simple cache here

    static boolean append(String streamId, int expectedVersion, String event) {
        List<String> stream = streams.computeIfAbsent(streamId, k -> new ArrayList<>());
        if (stream.size() != expectedVersion) return false;
        stream.add(event);
        return true;
    }

    static List<String> foldItems(String streamId) { // computes "items added" by folding, RESUMING from cache if possible
        List<String> stream = streams.getOrDefault(streamId, List.of());
        CachedFold cached = foldCache.get(streamId);
        int startFrom = (cached != null) ? cached.asOfVersion() : 0;
        List<String> items = (cached != null) ? new ArrayList<>(cached.itemsSoFar()) : new ArrayList<>();

        System.out.println("folding " + streamId + " from version " + startFrom + " to " + stream.size()
                + " (skipping " + startFrom + " already-folded events)");
        for (int i = startFrom; i < stream.size(); i++) {
            String event = stream.get(i);
            if (event.startsWith("ItemAdded(")) items.add(event.substring(10, event.length() - 1));
        }
        foldCache.put(streamId, new CachedFold(stream.size(), items)); // cache the new resume point
        return items;
    }

    public static void main(String[] args) {
        append("order-1", 0, "OrderPlaced");
        append("order-1", 1, "ItemAdded(widget)");

        System.out.println("First fold: " + foldItems("order-1")); // folds from version 0 -- nothing cached yet

        append("order-1", 2, "ItemAdded(gadget)");
        System.out.println("Second fold: " + foldItems("order-1")); // resumes from version 2, only processes the NEW event
    }
}
```

How to run: `java EfficientStreamReadFromVersion.java`

The first `foldItems` call finds no `foldCache` entry, so it folds the whole stream from version `0`, finding `"widget"`, and caches the result at version `2` (the stream's size at that point). After a third event is appended (bringing the stream to version `3`), the second `foldItems` call finds the cached fold at version `2` and starts its loop at `i=2` instead of `i=0` — it processes only the one new event (`"ItemAdded(gadget)"`), appends `"gadget"` to the already-cached `["widget"]`, and returns `["widget", "gadget"]` without ever re-examining the earlier events.

## 6. Walkthrough

Trace `EfficientStreamReadFromVersion.main` in order. **First**, two `append` calls build up `streams.get("order-1")` to `["OrderPlaced", "ItemAdded(widget)"]`, at version `2`.

**Next**, `foldItems("order-1")` runs. `foldCache.get("order-1")` is `null` (nothing cached yet), so `startFrom` is `0` and `items` starts as an empty list. The loop runs from `i=0` to `i=1`: at `i=0` the event is `"OrderPlaced"`, which doesn't match `"ItemAdded("`, so nothing is added; at `i=1` the event is `"ItemAdded(widget)"`, which does match, so `"widget"` is extracted and added to `items`. `foldCache` is then set to `CachedFold(asOfVersion=2, itemsSoFar=["widget"])`, and `["widget"]` is returned and printed.

**Then**, `append("order-1", 2, "ItemAdded(gadget)")` runs, succeeding (the stream's size matches the expected version `2`) and growing the stream to size `3`.

**Finally**, `foldItems("order-1")` runs a second time. This time `foldCache.get("order-1")` returns the cached fold from before, so `startFrom=2` and `items` is initialized as a copy of `["widget"]`. The loop runs only for `i=2`: the event there is `"ItemAdded(gadget)"`, which matches, so `"gadget"` is extracted and appended to `items`, producing `["widget", "gadget"]`. Crucially, indices `0` and `1` were never re-examined on this second call — only the genuinely new event was processed.

```
append(OrderPlaced, expected=0)      -> stream=[OrderPlaced], version=1
append(ItemAdded(widget), expected=1)-> stream=[..., ItemAdded(widget)], version=2
foldItems() 1st call  -> no cache -> fold from v0 -> items=[widget], cache={v2, [widget]}
append(ItemAdded(gadget), expected=2)-> stream grows to version=3
foldItems() 2nd call  -> cache found (v2) -> fold ONLY from v2 -> items=[widget, gadget]
```

## 7. Gotchas & takeaways

> Optimistic concurrency (expected-version checking) only protects a single stream — it does nothing to coordinate appends across two *different* streams (say, `order-1` and its related `payment-1`). Cross-stream coordination, if needed at all, is still the job of a [saga](0320-saga-pattern.md), not the event store's per-stream version check.

- An event store is optimized for two operations: append-with-expected-version to a per-entity stream, and read-a-stream-in-order — different from a general table's "find and overwrite one row" pattern.
- The expected-version check on append is the store's built-in defense against two concurrent writers silently producing conflicting history for the same entity.
- Efficiently reading a long stream benefits from resuming a fold from a cached or snapshotted point rather than always starting from the beginning — see [snapshots in event sourcing](0337-snapshots-in-event-sourcing.md) for the standard, more complete version of this idea.
- For lower-throughput systems, a well-disciplined conventional table can serve as an event store before dedicated infrastructure becomes necessary.
