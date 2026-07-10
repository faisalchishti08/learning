---
card: java
gi: 938
slug: memory-leaks-in-managed-memory
title: Memory leaks in managed memory
---

## 1. What it is

A memory leak in Java (a managed, garbage-collected language) means something different from a leak in a manually-managed language like C: since the garbage collector reliably reclaims anything actually unreachable, a "leak" here is always a **logical leak** — objects that remain *reachable* (some live reference chain still points to them, whether directly or indirectly) even though the application logically no longer needs them, so the collector correctly, faithfully, and forever keeps them alive because its job is reachability, not intent. Common sources include: static collections that grow without ever being cleared (a cache implemented as a plain `HashMap` with no eviction policy), listener/callback registrations that are added but never removed (an object registers itself with a long-lived event bus and is never unregistered, so the event bus's reference keeps it alive indefinitely), unclosed resources whose associated native or off-heap memory outlives the managed object referencing it, and `ThreadLocal` values that are never cleared on long-lived threads (particularly in thread-pool-based servers, where the same worker thread — and therefore the same `ThreadLocal` map — is reused indefinitely across many logically-unrelated requests).

## 2. Why & when

This distinction matters because it changes where you look for the bug: there is no pointer arithmetic to audit and no `free()` call to check for — the fix is always about breaking an unwanted reference chain, not about "remembering to deallocate." A leak becomes worth actively hunting for whenever heap usage trends upward over a long-running process's lifetime even when load stays flat — an old-generation occupancy graph that keeps climbing between full GCs rather than returning to a stable baseline, or a service that must periodically be restarted to avoid running out of memory, are both classic symptoms. It's especially worth being deliberate about the caching, listener-registration, and `ThreadLocal` patterns above during code review, since each one is a completely ordinary, useful Java idiom that becomes a leak only through a specific, easy-to-miss omission (no eviction policy, no unregister call, no `remove()` on the `ThreadLocal`) — the code compiles and runs correctly in every test that doesn't specifically probe for unbounded growth over time.

## 3. Core concept

```
C-style leak:               Java-style "leak":
  malloc() called,            Object IS reachable (a reference
  free() never called         chain still points to it)
  -> memory genuinely          -> GC correctly keeps it alive
     unreachable, GC has          forever, because that is
     no way to find it            EXACTLY its job
  (not applicable to Java --   -> the "bug" is that a reference
   GC always finds and           chain exists that SHOULDN'T,
   reclaims truly unreachable    logically, from the app's
   objects)                      point of view
```

Fixing a Java memory leak is always about identifying and breaking an unintended reference — via an eviction policy, an unregister call, a `try-with-resources` block, or a `ThreadLocal.remove()` — never about explicit deallocation.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A long-lived static cache holding references to objects the application no longer logically needs, keeping them reachable from a GC root forever" >
  <rect x="20" y="70" width="110" height="40" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="94" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">GC Root (static)</text>

  <rect x="200" y="70" width="140" height="40" fill="#1c2430" stroke="#f0883e"/>
  <text x="270" y="94" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">static Map cache (no eviction)</text>

  <rect x="410" y="20" width="100" height="30" fill="#1c2430" stroke="#8b949e"/>
  <text x="460" y="39" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">entry: user #1 (stale)</text>
  <rect x="410" y="60" width="100" height="30" fill="#1c2430" stroke="#8b949e"/>
  <text x="460" y="79" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">entry: user #2 (stale)</text>
  <rect x="410" y="100" width="100" height="30" fill="#1c2430" stroke="#8b949e"/>
  <text x="460" y="119" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">entry: user #N (stale)</text>

  <line x1="130" y1="90" x2="200" y2="90" stroke="#79c0ff" marker-end="url(#a)"/>
  <line x1="340" y1="85" x2="410" y2="35" stroke="#f0883e"/>
  <line x1="340" y1="90" x2="410" y2="75" stroke="#f0883e"/>
  <line x1="340" y1="95" x2="410" y2="115" stroke="#f0883e"/>

  <text x="320" y="165" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">GC correctly sees a reachable chain from a root -- it CANNOT know these entries are logically stale</text>
</svg>

*Every entry stays reachable from a GC root through the never-cleared cache — the collector faithfully keeps them all alive forever.*

## 5. Runnable example

Scenario: reproduce and then fix a classic unbounded-cache leak — starting with a basic leaking cache that grows without bound, then adding a realistic request-processing loop that surfaces the growth as rising heap usage over time, then fixing it with a properly bounded, evicting cache and confirming heap usage stabilizes.

### Level 1 — Basic

```java
import java.util.*;

public class LeakyStaticCache {
    static final Map<String, byte[]> cache = new HashMap<>(); // static -> lives for the whole JVM run

    public static void main(String[] args) {
        for (int i = 0; i < 500_000; i++) {
            cache.put("user-" + i, new byte[500]); // never removed, ever
        }
        System.out.println("cache size: " + cache.size());
        System.out.println("every entry is still reachable from the static 'cache' field -- nothing is garbage");
    }
}
```

**How to run:** `java -Xlog:gc LeakyStaticCache.java` (JDK 17+).

Expected output shape:
```
[0.10s][info][gc] GC(0) Pause Young (Normal) ... 30M->28M(64M) 2.1ms
...
cache size: 500000
every entry is still reachable from the static 'cache' field -- nothing is garbage
```

Every young-generation collection reclaims almost nothing, because every single cached entry is genuinely reachable through the static field — the GC is behaving perfectly correctly; the "leak" is entirely a logical decision by the application to never remove anything.

### Level 2 — Intermediate

```java
import java.util.*;

public class LeakyCacheOverTime {
    static final Map<String, byte[]> cache = new HashMap<>();

    public static void main(String[] args) throws InterruptedException {
        for (int round = 0; round < 20; round++) {
            for (int i = 0; i < 50_000; i++) {
                String key = "req-" + round + "-" + i;
                cache.put(key, new byte[500]); // simulates caching per-request data, never evicted
            }
            long used = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
            System.out.println("round " + round + ": cache size=" + cache.size() + ", used=" + (used / 1_000_000) + "MB");
            Thread.sleep(50);
        }
    }
}
```

**How to run:** `java -Xmx512m LeakyCacheOverTime.java` (JDK 17+; simulates a long-running server processing many "requests" over time, each contributing a few entries to a never-evicted cache).

Expected output shape:
```
round 0: cache size=50000, used=41MB
round 1: cache size=100000, used=78MB
...
round 19: cache size=1000000, used=612MB
```

The real-world concern added: `used` memory climbs steadily and predictably, round after round, with no plateau — exactly the symptom of a real production leak (a service that must eventually be restarted), because each "round" (standing in for a batch of served requests) adds entries to `cache` that are never removed, regardless of whether the underlying request data is still logically relevant.

### Level 3 — Advanced

```java
import java.util.*;

public class BoundedCacheFixed {
    // A properly bounded LRU cache: evicts the least-recently-used entry once capacity is exceeded.
    static final int MAX_ENTRIES = 10_000;
    static final Map<String, byte[]> cache = new LinkedHashMap<>(16, 0.75f, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry<String, byte[]> eldest) {
            return size() > MAX_ENTRIES;
        }
    };

    public static void main(String[] args) throws InterruptedException {
        for (int round = 0; round < 20; round++) {
            for (int i = 0; i < 50_000; i++) {
                String key = "req-" + round + "-" + i;
                synchronized (cache) {
                    cache.put(key, new byte[500]);
                }
            }
            long used = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
            System.out.println("round " + round + ": cache size=" + cache.size() + ", used=" + (used / 1_000_000) + "MB");
            Thread.sleep(50);
        }
    }
}
```

**How to run:** `java -Xmx512m BoundedCacheFixed.java` (JDK 17+; identical workload to Level 2, but the cache now has a hard capacity with LRU eviction).

Expected output shape:
```
round 0: cache size=10000, used=9MB
round 1: cache size=10000, used=9MB
...
round 19: cache size=10000, used=9MB
```

The production-flavored hard case: with `LinkedHashMap`'s access-order mode and an overridden `removeEldestEntry`, the cache automatically evicts its least-recently-used entry the moment it exceeds `MAX_ENTRIES` — `used` memory now plateaus immediately and stays flat across all twenty rounds, directly demonstrating the fix: bounding *what stays reachable* rather than trying to intervene in garbage collection itself, which was never the problem.

## 6. Walkthrough

Tracing `BoundedCacheFixed.main` end to end, and contrasting it with the leaking version:

1. Each round's inner loop puts 50,000 new entries into `cache`, exactly as `LeakyCacheOverTime` did — from the JVM's perspective, both versions perform an identical sequence of `Map.put` calls, so the fix cannot be about the puts themselves.
2. The difference lies entirely in `cache`'s own internal behavior: because it's constructed as a `LinkedHashMap` in access-order mode (`true` as the third constructor argument) with `removeEldestEntry` overridden to return `true` once `size()` exceeds `MAX_ENTRIES`, every `put` that pushes the map over its 10,000-entry cap causes the map itself to remove its own least-recently-used entry as an automatic side effect of that same `put` call.
3. Once an entry is removed by `removeEldestEntry`, `cache` no longer holds any reference to it — and assuming nothing else in the program independently retains a reference to that same `byte[500]` array, it is now genuinely unreachable, and the very next young-generation collection reclaims it exactly as it would any other garbage.
4. This is why `used` memory plateaus immediately at round 0 and stays flat for the rest of the run: the cache's *logical* size is now bounded by design, which means the *reachable* set of cached entries is bounded too, which is the only thing that actually determines whether the GC can reclaim them.
5. The printed `cache size` staying pinned at 10,000 across every round is the direct, observable confirmation that eviction is working as intended — contrasted against `LeakyCacheOverTime`'s ever-growing `cache size` and `used` figures, this walkthrough shows the entire fix is a change in *reachability policy* (what the cache chooses to keep referencing), with the collector's own behavior — and every line of code that calls `cache.put(...)` — completely unchanged between the two versions.

## 7. Gotchas & takeaways

> **Gotcha:** `ThreadLocal` leaks are a particularly sneaky variant in thread-pool-based servers — a worker thread's `ThreadLocal` map persists across every request that thread happens to handle, so a value set during request A and never explicitly `remove()`-d can still be reachable (and even visible) during an unrelated later request B handled by that same reused thread; always pair `ThreadLocal.set(...)` with a `finally`-block `ThreadLocal.remove()` in request-scoped code.

- In Java, a "memory leak" always means objects remain *reachable* longer than the application logically needs them — the GC is working correctly; the bug is an unintended reference chain, not a missed deallocation.
- Common sources: unbounded static caches with no eviction policy, listeners/callbacks registered but never unregistered, resources whose off-heap memory outlives their managed wrapper, and `ThreadLocal` values never cleared on reused thread-pool threads.
- The classic symptom is old-generation (or total heap) usage trending upward over a long-running process's lifetime even under flat load, rather than returning to a stable baseline after each collection.
- The fix is always about bounding or breaking the unwanted reference chain — an eviction policy (LRU, TTL), an explicit unregister call, `try-with-resources`, or `ThreadLocal.remove()` — never about GC tuning, since no collector setting can reclaim something still genuinely reachable.
- See [heap dumps & analysis](0940-heap-dumps-analysis.md) for the practical tooling used to actually locate which reference chain is keeping unwanted objects alive in a real, already-leaking process.
