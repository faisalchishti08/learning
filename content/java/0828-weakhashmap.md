---
card: java
gi: 828
slug: weakhashmap
title: WeakHashMap
---

## 1. What it is

`WeakHashMap` is a `Map` implementation whose **keys** are held via `WeakReference`s instead of ordinary (strong) references. Normally, an object referenced as a map key stays reachable — and therefore un-collectible by the garbage collector — for as long as the map itself is reachable, even if nothing else in the program holds a reference to that key anymore. `WeakHashMap` breaks that: if a key object becomes otherwise unreachable (no strong references to it remain anywhere else in the program), the garbage collector is free to reclaim it, and `WeakHashMap` automatically removes the corresponding entry — key and value both — the next time the map is accessed or during garbage collection processing. Values are held with ordinary strong references; only the keys get the weak treatment.

## 2. Why & when

An ordinary `HashMap` used as a cache keyed by some object risks a memory leak: if entries are never explicitly removed, every key stays strongly reachable through the map forever, even after the rest of the program has completely finished with that key object — the map single-handedly prevents garbage collection of keys that would otherwise be reclaimable. `WeakHashMap` is designed for exactly the scenario where a cache or metadata table should **not** be the reason an object stays alive — associating auxiliary data with an object (a listener's metadata, a computed property) for as long as that object is used elsewhere, but automatically forgetting it the moment nothing else needs the object anymore. This is a fairly narrow, specific use case; for general-purpose caching with explicit size or time-based eviction control, a dedicated cache library or a manually-managed [`LinkedHashMap`](0824-linkedhashmap-insertion-access-order-lru.md)-based LRU is usually a better fit.

## 3. Core concept

```java
WeakHashMap<Object, String> metadata = new WeakHashMap<>();
Object key = new Object();
metadata.put(key, "some associated metadata");

System.out.println(metadata.size()); // 1 -- key is still strongly reachable via the local variable "key"

key = null; // the ONLY strong reference to that object is gone now
System.gc(); // request (not guarantee) garbage collection

// After GC actually runs, the entry is very likely gone:
System.out.println(metadata.size()); // likely 0 -- the entry was automatically removed
```

The entry's removal isn't immediate or guaranteed to happen at any specific moment — it depends on when the garbage collector actually runs and reclaims the now-unreachable key object; `System.gc()` is only a *request*, not a command, though in practice most JVMs honor it promptly enough for demonstration purposes.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A WeakHashMap holds its keys via weak references, so once no strong reference to a key remains elsewhere, the garbage collector can reclaim it and the entry disappears automatically">
  <g font-family="sans-serif">
    <rect x="40" y="30" width="180" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="130" y="57" fill="#e6edf3" font-size="11" text-anchor="middle">local variable "key"</text>

    <line x1="220" y1="52" x2="280" y2="52" stroke="#3fb950" stroke-width="2" marker-end="url(#a828s)"/>
    <text x="250" y="42" fill="#3fb950" font-size="9" text-anchor="middle">strong ref</text>

    <rect x="290" y="30" width="120" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
    <text x="350" y="57" fill="#e6edf3" font-size="11" text-anchor="middle">key object</text>

    <line x1="290" y1="65" x2="230" y2="105" stroke="#8b949e" stroke-width="2" stroke-dasharray="4" marker-end="url(#a828w)"/>
    <text x="245" y="95" fill="#8b949e" font-size="9" text-anchor="middle">weak ref</text>

    <rect x="40" y="105" width="180" height="45" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
    <text x="130" y="132" fill="#e6edf3" font-size="10" text-anchor="middle">WeakHashMap entry</text>
  </g>
  <text x="320" y="175" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Once "key = null" removes the only strong reference, GC can reclaim it — the entry then vanishes too</text>

  <defs>
    <marker id="a828s" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="a828w" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

*A `WeakHashMap`'s reference to each key is weak — it doesn't by itself keep the key alive, unlike the map's own reference to each value.*

## 5. Runnable example

Scenario: attaching debug metadata to short-lived request objects without leaking memory, growing from basic put/get through observing automatic cleanup after garbage collection, to a realistic caveat about why relying on this for correctness (not just memory hygiene) is risky.

### Level 1 — Basic

```java
import java.util.*;

public class RequestMetadataBasic {
    public static void main(String[] args) {
        WeakHashMap<Object, String> metadata = new WeakHashMap<>();

        Object request = new Object(); // stands in for some request object
        metadata.put(request, "trace-id: abc123");

        System.out.println("metadata for request: " + metadata.get(request));
        System.out.println("map size while request is still referenced: " + metadata.size());
    }
}
```

**How to run:** `java RequestMetadataBasic.java` (JDK 17+).

Expected output:
```
metadata for request: trace-id: abc123
map size while request is still referenced: 1
```

While `request` is still held by the local variable, it's strongly reachable, so the entry stays exactly as it would in a normal `HashMap`.

### Level 2 — Intermediate

```java
import java.util.*;

public class RequestMetadataCleanup {
    public static void main(String[] args) throws InterruptedException {
        WeakHashMap<Object, String> metadata = new WeakHashMap<>();

        Object request = new Object();
        metadata.put(request, "trace-id: abc123");
        System.out.println("size before dropping the reference: " + metadata.size());

        request = null; // the ONLY strong reference to the key object is now gone
        System.gc();     // request garbage collection (not guaranteed to run immediately)
        Thread.sleep(200); // give the collector a moment in this demo

        System.out.println("size after GC (entry auto-removed once key is unreachable): " + metadata.size());
    }
}
```

**How to run:** `java RequestMetadataCleanup.java`. Because `System.gc()` is only a request, results can occasionally vary between JVM runs — but in practice, on virtually every mainstream JVM, the entry is reliably gone after this sequence for a demo this small and simple.

Expected output:
```
size before dropping the reference: 1
size after GC (entry auto-removed once key is unreachable): 0
```

The real-world concern added: actually forcing (requesting) garbage collection and observing the entry disappear. Note that `metadata.get(request)` was never called again after `request = null` — there was no `request` variable left to call it with — which is itself the point: once nothing in the program can reach the key anymore, the map's own internal cleanup (triggered by the `ReferenceQueue` mechanism `WeakHashMap` uses internally) removes the stale entry without any explicit `remove()` call needed.

### Level 3 — Advanced

```java
import java.util.*;

public class WeakHashMapCorrectnessCaveat {
    public static void main(String[] args) throws InterruptedException {
        WeakHashMap<Object, Integer> requestCounts = new WeakHashMap<>();

        // DANGEROUS pattern: relying on WeakHashMap for logic correctness, not just memory hygiene.
        Object sessionA = new Object();
        requestCounts.put(sessionA, 1);
        requestCounts.put(sessionA, requestCounts.get(sessionA) + 1); // "increment" -- sessionA still referenced here, fine so far

        System.out.println("sessionA count while referenced: " + requestCounts.get(sessionA));

        // The danger: if GC happens to run between uses of a key still logically "in use"
        // but only reachable through a chain the collector doesn't consider strong enough,
        // the entry can vanish out from under logic that assumed it would persist.
        // WeakHashMap is NOT a substitute for explicit lifecycle management when correctness,
        // not just memory cleanup, depends on an entry still being present.

        System.gc();
        Thread.sleep(100);
        System.out.println("sessionA count after a GC request, key STILL referenced: " + requestCounts.get(sessionA));
        System.out.println("-> still present, because 'sessionA' variable keeps it strongly reachable throughout");
        System.out.println("-> the risk only appears once code stops holding a strong reference somewhere UNINTENTIONALLY");
    }
}
```

**How to run:** `java WeakHashMapCorrectnessCaveat.java`.

Expected output:
```
sessionA count while referenced: 2
sessionA count after a GC request, key STILL referenced: 2
-> still present, because 'sessionA' variable keeps it strongly reachable throughout
-> the risk only appears once code stops holding a strong reference somewhere UNINTENTIONALLY
```

This adds the production-flavored hard case: the entry survives garbage collection here **only** because `sessionA` remains strongly referenced by the local variable throughout — proving that `WeakHashMap` doesn't aggressively evict entries just because a GC cycle ran, only once the key genuinely becomes unreachable everywhere. The real danger in production code is subtler: if a key object is accidentally only reachable *through* the `WeakHashMap` itself (no other strong reference exists anywhere), an entry that logic still depends on can silently disappear between two operations, exactly when a GC cycle happens to run — making `WeakHashMap` a poor fit for anything where a missing entry would be a correctness bug rather than an acceptable, expected cleanup.

## 6. Walkthrough

Tracing `WeakHashMapCorrectnessCaveat.main`:

1. `sessionA = new Object()` creates an object with the local variable `sessionA` as its (currently only) strong reference.
2. `requestCounts.put(sessionA, 1)` inserts an entry keyed by `sessionA`, held weakly by the map — but `sessionA` the local variable still holds a strong reference to the same object, so the object remains reachable regardless of what the map does internally.
3. `requestCounts.put(sessionA, requestCounts.get(sessionA) + 1)` reads the current count (`1`), adds one, and stores `2` back under the same key — an ordinary read-modify-write, unaffected by the map's weak-key mechanics since the key object hasn't gone anywhere.
4. `System.gc()` requests a garbage collection cycle. Even if the JVM honors this request promptly, the collector examines reachability from GC roots — and `sessionA` (the local variable, still in scope on the stack) is one such root, keeping the object it points to reachable. The `WeakHashMap`'s weak reference to that same object is therefore irrelevant here; the object survives because of the *strong* reference, not despite the weak one.
5. `requestCounts.get(sessionA)` after the GC request still returns `2`, confirming the entry survived — precisely because the object was never actually eligible for collection in the first place. This demonstrates the subtlety: `WeakHashMap` only cleans up entries whose keys are **genuinely** unreachable everywhere else, and code relying on an entry's continued presence must be certain no accidental loss of the last strong reference can occur, or risk exactly the kind of GC-timing-dependent bug the final printed lines warn about.

## 7. Gotchas & takeaways

> **Gotcha:** entry removal in a `WeakHashMap` is tied to garbage collection timing, which is neither immediate nor deterministic. Code that depends on an entry **remaining present** for correctness (not just as an acceptable cache-eviction side effect) is fragile by construction — a GC cycle running at an unlucky moment, or an accidental loss of a key's last strong reference elsewhere in the program, can remove an entry the logic didn't expect to lose.

- `WeakHashMap` holds keys via `WeakReference`s; once a key becomes otherwise unreachable, the garbage collector may reclaim it, and the corresponding entry is automatically removed.
- Values are held with ordinary strong references — only keys get weak-reference treatment.
- Entry removal timing is tied to GC cycles, not deterministic or immediate — never rely on it for anything beyond memory hygiene.
- The intended use case is narrow: associating auxiliary metadata with an object for exactly as long as that object is used elsewhere, without the map itself preventing garbage collection.
- For general-purpose caching with controlled eviction, prefer an explicit size- or time-based strategy (like a [`LinkedHashMap`](0824-linkedhashmap-insertion-access-order-lru.md)-based LRU) over relying on `WeakHashMap`'s GC-driven cleanup.
