---
card: microservices
gi: 501
slug: caching-strategies-cache-aside-read-through-write-through-wr
title: "Caching strategies (cache-aside, read-through, write-through, write-behind)"
---

## 1. What it is

These are four distinct patterns for how an application's code interacts with a cache sitting in front of a slower data store, differing in **who** is responsible for populating the cache on a read miss and **when** the underlying store gets updated on a write. **Cache-aside**: the application manages the cache directly, checking it first and populating it on a miss. **Read-through**: the cache itself, not the application, fetches from the store on a miss. **Write-through**: every write goes to the cache and the store together, synchronously. **Write-behind**: writes go to the cache immediately and are flushed to the store asynchronously, later.

## 2. Why & when

You pick a specific strategy — or mix them for different access patterns — based on your actual read/write ratio and how much staleness or write-loss risk you can tolerate:

- **Cache-aside is the most common and flexible starting point.** The application has full control over what's cached and when, at the cost of every call site needing to correctly implement the check-cache-then-populate-on-miss logic itself, which is easy to get subtly wrong if done ad hoc.
- **Read-through simplifies application code by moving that logic into the cache layer itself** — the application just asks the cache for data, and the cache transparently handles the miss-then-populate sequence, at the cost of needing a cache implementation that actually supports this loading behavior.
- **Write-through guarantees the store and cache never diverge**, since every write updates both synchronously — at the cost of every write paying the latency of writing to both, making writes slower than either alone.
- **Write-behind gives the fastest possible write latency** (the caller only waits for the cache write, not the store write) at the real risk of data loss if the cache fails before the asynchronous flush to the store completes — you accept this tradeoff specifically when write latency matters more than the small window of loss risk, and typically only for data where losing the very latest update is tolerable.

## 3. Core concept

Think of a small notepad you keep on your desk (the cache) versus a filing cabinet across the room (the store): cache-aside is you personally checking the notepad first, and if it's not there, walking to the cabinet, getting it, and jotting it on the notepad yourself. Read-through is having an assistant who automatically checks the cabinet and updates your notepad whenever you ask for something not already on it. Write-through is writing something down on both the notepad and filing it in the cabinet before considering the task done. Write-behind is jotting it on the notepad immediately and telling your assistant to file it in the cabinet whenever they get a chance.

Concretely:

1. **Cache-aside (lazy loading)**: on read, check the cache; on a miss, read from the store and write the result into the cache before returning it. On write, update the store, and either update or invalidate the corresponding cache entry.
2. **Read-through**: the application asks the cache for data; the cache itself, configured with a loader function, fetches from the store on a miss, populates itself, and returns the result — the application never talks to the store directly for reads.
3. **Write-through**: on write, the cache synchronously writes to both itself and the underlying store before the write call returns — the store is never behind the cache.
4. **Write-behind (write-back)**: on write, the cache is updated immediately and the call returns; the actual write to the store happens later, asynchronously, often batched with other pending writes.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four caching strategies differing in who populates the cache on a miss and when the store is updated on a write">
  <rect x="20" y="20" width="290" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="165" y="45" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">cache-aside</text>
  <text x="165" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">app checks cache, populates on miss itself</text>

  <rect x="350" y="20" width="290" height="70" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="495" y="45" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">read-through</text>
  <text x="495" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">cache itself loads from store on a miss</text>

  <rect x="20" y="110" width="290" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="165" y="135" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">write-through</text>
  <text x="165" y="155" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">write to cache AND store, synchronously</text>

  <rect x="350" y="110" width="290" height="70" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="495" y="135" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">write-behind</text>
  <text x="495" y="155" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">write to cache now, store LATER, async</text>
</svg>

Four strategies, differing in read-miss ownership and write timing to the underlying store.

## 5. Runnable example

Scenario: comparing cache-aside, write-through, and write-behind against the same underlying store. We start with basic cache-aside read/populate logic, extend it to write-through's synchronous dual-write, then handle the hard case: write-behind's asynchronous flush, where a cache failure before the flush completes genuinely loses data — demonstrated explicitly, not glossed over.

### Level 1 — Basic

```java
// File: CacheAsideBasic.java -- models CACHE-ASIDE: the APPLICATION
// checks the cache first, and on a MISS, reads the store and populates
// the cache ITSELF.
import java.util.*;

public class CacheAsideBasic {
    static Map<String, String> store = new HashMap<>(Map.of("order-42", "SHIPPED"));
    static Map<String, String> cache = new HashMap<>(); // starts empty

    static String getOrderStatus(String orderId) {
        String cached = cache.get(orderId);
        if (cached != null) {
            System.out.println("[cache-aside] CACHE HIT for " + orderId);
            return cached;
        }
        System.out.println("[cache-aside] CACHE MISS for " + orderId + " -- reading from store");
        String fromStore = store.get(orderId);
        cache.put(orderId, fromStore); // the APPLICATION populates the cache itself
        return fromStore;
    }

    public static void main(String[] args) {
        System.out.println("first call: " + getOrderStatus("order-42"));
        System.out.println("second call: " + getOrderStatus("order-42"));
    }
}
```

How to run: `java CacheAsideBasic.java`

`getOrderStatus` explicitly checks `cache` first, and only on a `null` result does it read `store` and explicitly call `cache.put(...)` itself — this population step, written directly in application code, is exactly what "cache-aside" means: the application, not the cache, owns the responsibility of loading on a miss.

### Level 2 — Intermediate

```java
// File: WriteThroughBasic.java -- the SAME cache-aside reads, now with
// WRITE-THROUGH writes: every write updates BOTH the cache AND the store,
// SYNCHRONOUSLY, before the write call returns -- guaranteeing they never diverge.
import java.util.*;

public class WriteThroughBasic {
    static Map<String, String> store = new HashMap<>(Map.of("order-42", "SHIPPED"));
    static Map<String, String> cache = new HashMap<>(Map.of("order-42", "SHIPPED"));

    static void writeThroughUpdateStatus(String orderId, String newStatus) {
        store.put(orderId, newStatus); // write to the STORE
        cache.put(orderId, newStatus); // AND the cache, synchronously, same call
        System.out.println("[write-through] updated BOTH store and cache to '" + newStatus + "' before returning");
    }

    public static void main(String[] args) {
        writeThroughUpdateStatus("order-42", "DELIVERED");
        System.out.println("store now: " + store.get("order-42"));
        System.out.println("cache now: " + cache.get("order-42"));
        System.out.println("in sync: " + store.get("order-42").equals(cache.get("order-42")));
    }
}
```

How to run: `java WriteThroughBasic.java`

`writeThroughUpdateStatus` performs both `store.put` and `cache.put` sequentially within the same method call, and returns only after both complete — by the time the method returns, `store` and `cache` are guaranteed to hold the identical value, which is write-through's defining guarantee.

### Level 3 — Advanced

```java
// File: WriteBehindDataLossRisk.java -- the SAME write pattern, now
// WRITE-BEHIND: the cache is updated IMMEDIATELY, and the store write is
// QUEUED for LATER, asynchronous flushing. This handles the
// PRODUCTION-FLAVORED hard case EXPLICITLY: if the cache is lost BEFORE
// the queued write is flushed to the store, that write is GENUINELY LOST
// -- this tradeoff must be visible in the code, not hidden.
import java.util.*;

public class WriteBehindDataLossRisk {
    static Map<String, String> store = new HashMap<>(Map.of("order-42", "SHIPPED"));
    static Map<String, String> cache = new HashMap<>(Map.of("order-42", "SHIPPED"));
    static Queue<Map.Entry<String, String>> pendingFlushQueue = new LinkedList<>();

    static void writeBehindUpdateStatus(String orderId, String newStatus) {
        cache.put(orderId, newStatus); // cache updated IMMEDIATELY
        pendingFlushQueue.add(Map.entry(orderId, newStatus)); // store write QUEUED, not done yet
        System.out.println("[write-behind] cache updated to '" + newStatus + "' immediately; store write QUEUED, not yet applied");
    }

    static void flushPendingWritesToStore() {
        System.out.println("[write-behind] flushing " + pendingFlushQueue.size() + " pending write(s) to the store");
        while (!pendingFlushQueue.isEmpty()) {
            Map.Entry<String, String> pending = pendingFlushQueue.poll();
            store.put(pending.getKey(), pending.getValue());
        }
    }

    // Simulates the CACHE failing/restarting BEFORE the flush ran -- pending writes are LOST.
    static void simulateCacheCrashBeforeFlush() {
        System.out.println("[incident] cache process CRASHES -- " + pendingFlushQueue.size()
                + " pending write(s) NEVER reached the store, and are now PERMANENTLY LOST");
        cache.clear(); // the cache's in-memory state, including anything not yet flushed, is gone
        pendingFlushQueue.clear(); // the queue itself lived in the crashed cache process too
    }

    public static void main(String[] args) {
        writeBehindUpdateStatus("order-42", "DELIVERED");
        System.out.println("store still shows OLD value: " + store.get("order-42") + " (not yet flushed)");
        System.out.println("cache shows NEW value: " + cache.get("order-42"));

        System.out.println();
        System.out.println("--- scenario A: flush happens normally before any failure ---");
        flushPendingWritesToStore();
        System.out.println("store now shows: " + store.get("order-42") + " (successfully flushed)");

        System.out.println();
        System.out.println("--- scenario B: a SECOND write happens, but the cache crashes BEFORE flushing ---");
        writeBehindUpdateStatus("order-42", "REFUNDED");
        simulateCacheCrashBeforeFlush();
        System.out.println("store STILL shows the OLD value: " + store.get("order-42") + " -- 'REFUNDED' write is PERMANENTLY LOST");
    }
}
```

How to run: `java WriteBehindDataLossRisk.java`

`writeBehindUpdateStatus` never touches `store` directly — it only updates `cache` and adds the pending write to `pendingFlushQueue`, meaning `store` remains stale until `flushPendingWritesToStore` is explicitly called later. In scenario B, `simulateCacheCrashBeforeFlush` runs *before* any flush happens for the `"REFUNDED"` write — it clears both `cache` and `pendingFlushQueue`, modeling the cache process's entire in-memory state being lost, which means that pending write to `store` never happens at all, ever, demonstrating write-behind's real data-loss risk concretely rather than glossing over it.

## 6. Walkthrough

Trace `WriteBehindDataLossRisk.main` in order. **First**, `writeBehindUpdateStatus("order-42", "DELIVERED")` runs: `cache.put(...)` updates the cache immediately to `"DELIVERED"`, and the same key-value pair is added to `pendingFlushQueue` — `store` is untouched at this point, still holding `"SHIPPED"`.

**Next**, `main` prints both values, showing `store` still stale at `"SHIPPED"` while `cache` already reflects `"DELIVERED"` — the visible gap write-behind's asynchronous flushing creates.

**Then**, scenario A calls `flushPendingWritesToStore()`, which drains `pendingFlushQueue` entirely, writing `"DELIVERED"` into `store` — after this, `store` and `cache` agree again, and the pending write has been safely and successfully persisted.

**After that**, scenario B calls `writeBehindUpdateStatus("order-42", "REFUNDED")` — identical mechanics to the first write: `cache` updates immediately to `"REFUNDED"`, and a new entry is added to `pendingFlushQueue`, while `store` remains at `"DELIVERED"` (its last successfully flushed value).

**Finally**, `simulateCacheCrashBeforeFlush()` runs *before* `flushPendingWritesToStore()` is ever called again — it clears both `cache` and `pendingFlushQueue`, representing the cache process going down with that pending write still sitting only in its own volatile memory. Because the flush never happened, `store` is left permanently holding `"DELIVERED"` — the `"REFUNDED"` update, which the cache had already accepted and would have reported to any reader as the current value, has vanished entirely and unrecoverably, exactly demonstrating write-behind's core tradeoff made concrete rather than abstract.

```
[write-behind] cache updated to 'DELIVERED' immediately; store write QUEUED, not yet applied
store still shows OLD value: SHIPPED (not yet flushed)
cache shows NEW value: DELIVERED

--- scenario A: flush happens normally before any failure ---
[write-behind] flushing 1 pending write(s) to the store
store now shows: DELIVERED (successfully flushed)

--- scenario B: a SECOND write happens, but the cache crashes BEFORE flushing ---
[write-behind] cache updated to 'REFUNDED' immediately; store write QUEUED, not yet applied
[incident] cache process CRASHES -- 1 pending write(s) NEVER reached the store, and are now PERMANENTLY LOST
store STILL shows the OLD value: DELIVERED -- 'REFUNDED' write is PERMANENTLY LOST
```

## 7. Gotchas & takeaways

> Choosing write-behind for its write-latency benefit without consciously accepting its data-loss risk is a real, sometimes costly mistake — this pattern is appropriate specifically for data where losing the very latest write is genuinely tolerable (view counts, non-critical analytics), and a poor fit for anything where losing an update (a payment status, an inventory decrement) would be a real problem.
- Cache-aside is the most common default because it gives the application explicit, visible control over exactly what gets cached and when — but that visibility comes with the responsibility of implementing the miss-then-populate logic correctly and consistently at every call site.
- Write-through's synchronous dual-write guarantee (cache and store never diverge) is valuable precisely for data where staleness between the two would be a real problem — but it costs every write the latency of both operations, never just one.
- Mixing strategies for different data within the same system is common and often correct — cache-aside for read-heavy reference data, write-through for data needing strong consistency, write-behind only for genuinely loss-tolerant, write-heavy data.
- Whatever strategy you choose, pair it with a deliberate [cache invalidation](0503-cache-invalidation.md) approach — none of these four patterns alone solves the separate, equally important problem of correctly expiring or refreshing stale cached data.
