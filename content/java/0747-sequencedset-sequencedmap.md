---
card: java
gi: 747
slug: sequencedset-sequencedmap
title: SequencedSet / SequencedMap
---

## 1. What it is

`SequencedSet<E>` and `SequencedMap<K,V>` extend the same idea as [SequencedCollection](0746-sequenced-collections-sequencedcollection.md) to sets and maps: any `Set` or `Map` implementation that maintains a well-defined iteration order (`LinkedHashSet`, `LinkedHashMap`, and sorted collections like `TreeMap`/`TreeSet` via adapters) now exposes `getFirst`/`getLast`, `addFirst`/`addLast` (for sets), `putFirst`/`putLast` (for maps), and `reversed()` — the same first/last vocabulary `SequencedCollection` gives lists and deques, extended to key-based and unique-element collections.

## 2. Why & when

`LinkedHashMap` has always maintained insertion order (or access order, in LRU mode), and `LinkedHashSet` has always maintained insertion order too — but neither type exposed that order through dedicated "first entry" or "last entry" methods. Getting the first entry of a `LinkedHashMap` meant `map.entrySet().iterator().next()`, and there was no built-in way to get a reversed view at all without manually rebuilding the map. `SequencedMap` and `SequencedSet` give these already-ordered collections the same clean, purpose-built API that `SequencedCollection` gives lists: `firstEntry()`/`lastEntry()`, `putFirst()`/`putLast()`, and `reversed()`, so code that's already relying on a `LinkedHashMap`'s order (an LRU cache, a most-recently-used tracker, an ordered configuration map) can express that reliance directly instead of working around missing accessors.

## 3. Core concept

```java
import java.util.*;

SequencedMap<String, Integer> scores = new LinkedHashMap<>();
scores.put("ada", 90);
scores.put("linus", 85);
scores.put("grace", 95);

Map.Entry<String, Integer> first = scores.firstEntry(); // ada=90
Map.Entry<String, Integer> last = scores.lastEntry();   // grace=95
scores.putFirst("admin", 100);                          // moves to the front
SequencedMap<String, Integer> reversed = scores.reversed(); // live, reversed view
```

`LinkedHashMap` implements `SequencedMap` directly — no wrapping or conversion needed, since Java 21 retrofits the interface onto the existing class.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SequencedMap and SequencedSet extend the SequencedCollection idea of first and last to LinkedHashMap and LinkedHashSet">
  <rect x="230" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">SequencedCollection</text>

  <line x1="290" y1="60" x2="160" y2="95" stroke="#8b949e"/>
  <line x1="360" y1="60" x2="480" y2="95" stroke="#8b949e"/>

  <rect x="80" y="95" width="160" height="36" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="160" y="118" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">SequencedSet</text>
  <text x="160" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">impl: LinkedHashSet</text>

  <rect x="400" y="95" width="160" height="36" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="480" y="118" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">SequencedMap</text>
  <text x="480" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">impl: LinkedHashMap</text>
</svg>

*The same first/last/reversed vocabulary extends from sequences to unique-key sets and maps.*

## 5. Runnable example

Scenario: a simple most-recently-used (MRU) cache tracker, growing from manual `LinkedHashMap` iteration to full `SequencedMap` usage.

### Level 1 — Basic

```java
import java.util.*;

public class MruBasic {
    public static void main(String[] args) {
        LinkedHashMap<String, Integer> visits = new LinkedHashMap<>();
        visits.put("home", 1);
        visits.put("profile", 2);
        visits.put("settings", 3);

        Map.Entry<String, Integer> firstEntry = visits.entrySet().iterator().next();
        System.out.println("first visited: " + firstEntry.getKey());
    }
}
```

**How to run:** `java MruBasic.java` (JDK 21+, but `LinkedHashMap` itself works on any JDK).

This is the pre-`SequencedMap` style: getting the first entry means grabbing an `Iterator` and calling `next()` once — it works, but nothing about the code communicates "get the first entry" directly.

### Level 2 — Intermediate

```java
import java.util.*;

public class MruSequenced {
    public static void main(String[] args) {
        SequencedMap<String, Integer> visits = new LinkedHashMap<>();
        visits.put("home", 1);
        visits.put("profile", 2);
        visits.put("settings", 3);

        System.out.println("first visited: " + visits.firstEntry().getKey());
        System.out.println("most recent: " + visits.lastEntry().getKey());

        visits.putFirst("splash", 0); // record a page visited before all current entries
        System.out.println(visits.sequencedKeySet());
    }
}
```

**How to run:** `java MruSequenced.java`.

The real-world concern added: `firstEntry()`/`lastEntry()` replace manual iterator use, and `putFirst()` inserts a new entry **at the front** of the map's order — something a plain `LinkedHashMap` had no direct API for at all.

### Level 3 — Advanced

```java
import java.util.*;

public class MruAdvanced {
    static final int CAPACITY = 3;

    static void recordVisit(SequencedMap<String, Integer> visits, String page) {
        visits.remove(page);       // drop any existing entry for this page
        visits.putLast(page, 1);   // re-insert at the end: "most recently visited"
        if (visits.size() > CAPACITY) {
            var oldest = visits.pollFirstEntry(); // evict the least-recently visited
            System.out.println("evicted: " + oldest.getKey());
        }
    }

    public static void main(String[] args) {
        SequencedMap<String, Integer> visits = new LinkedHashMap<>();
        recordVisit(visits, "home");
        recordVisit(visits, "profile");
        recordVisit(visits, "settings");
        recordVisit(visits, "home");     // re-visiting moves "home" to most-recent
        recordVisit(visits, "billing");  // pushes capacity over the limit

        System.out.println("current order (oldest to newest): " + visits.sequencedKeySet());
        System.out.println("most recent first: " + visits.reversed().sequencedKeySet());
    }
}
```

**How to run:** `java MruAdvanced.java`.

This adds the production-flavored hard case: a small **MRU eviction policy** built entirely on `SequencedMap` operations — `remove` + `putLast` to move a re-visited page to the "most recent" end, `pollFirstEntry()` to evict the least-recently-used entry once capacity is exceeded, and `reversed()` to report the order from most to least recent without any manual list reversal.

## 6. Walkthrough

Tracing `MruAdvanced.main`:

1. `main` creates an empty `LinkedHashMap` typed as `SequencedMap<String, Integer>` and calls `recordVisit` five times.
2. `recordVisit(visits, "home")`: `visits.remove("home")` does nothing (not present yet). `visits.putLast("home", 1)` inserts it at the end — the map's order is now `[home]`. Size is `1`, not over `CAPACITY` (3), so no eviction.
3. `recordVisit(visits, "profile")` and `recordVisit(visits, "settings")` proceed the same way, growing the order to `[home, profile, settings]`, still at capacity exactly.
4. `recordVisit(visits, "home")`: this time `visits.remove("home")` **does** remove the existing entry, leaving `[profile, settings]`; then `putLast("home", 1)` re-inserts it at the end, producing `[profile, settings, home]` — `"home"` has moved from oldest to most-recent, which is the entire point of MRU tracking.
5. `recordVisit(visits, "billing")`: `remove` does nothing (not present). `putLast` appends it: `[profile, settings, home, billing]`, size `4`, which **is** over `CAPACITY` (3). `visits.pollFirstEntry()` removes and returns the first entry, `profile=1`, printing `"evicted: profile"`. The map is now `[settings, home, billing]`.
6. Back in `main`, `visits.sequencedKeySet()` returns the keys in current order: `[settings, home, billing]` — oldest first.
7. `visits.reversed().sequencedKeySet()` returns the same keys through a reversed view: `[billing, home, settings]` — most recent first, with no manual reversal logic written anywhere.

Expected output:
```
evicted: profile
current order (oldest to newest): [settings, home, billing]
most recent first: [billing, home, settings]
```

## 7. Gotchas & takeaways

> **Gotcha:** `SequencedMap`'s ordering guarantees only apply to backing implementations that actually maintain order — plain `HashMap` and `HashSet` do **not** implement `SequencedMap`/`SequencedSet` at all, because their iteration order is unspecified. Only switch to `LinkedHashMap`/`LinkedHashSet` (or a sorted variant) when you actually need the sequenced guarantees; don't assume every `Map`/`Set` gained these methods.

- `SequencedMap` adds `firstEntry`/`lastEntry`, `putFirst`/`putLast`, `pollFirstEntry`/`pollLastEntry`, `sequencedKeySet`/`sequencedValues`/`sequencedEntrySet`, and `reversed()`.
- `SequencedSet` adds the `SequencedCollection` first/last vocabulary to `LinkedHashSet` and similar ordered sets.
- `putFirst`/`putLast` **move** an existing key to the front/back if it's already present in some implementations — check the specific implementation's docs, or explicitly `remove` first as shown above if you need guaranteed move-to-end semantics.
- `reversed()` on a map or set is a live view, exactly like on `SequencedCollection` — mutating it mutates the backing map/set.
- These retrofits require no new collection classes for typical code — `LinkedHashMap` and `LinkedHashSet` gained the new interfaces automatically in Java 21.
