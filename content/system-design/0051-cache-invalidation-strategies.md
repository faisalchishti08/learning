---
card: system-design
gi: 51
slug: cache-invalidation-strategies
title: Cache invalidation strategies
---

## 1. What it is

**Cache invalidation** is the process of removing or updating a cache entry once the underlying data it represents has changed, so the cache stops serving outdated values. The three common strategies are **TTL-based expiry** (remove after a fixed time), **explicit invalidation** (the writer deletes or updates the entry the moment it changes the data), and **event-based invalidation** (a message tells other services to invalidate their copies).

## 2. Why & when

Every cache creates a second copy of data that can drift from the source of truth. Invalidation is how you bound how wrong that copy is allowed to get. TTL alone is simple but always leaves a window of staleness up to the TTL length. Explicit invalidation removes staleness immediately for the service that made the write, but only for that service. Event-based invalidation extends explicit invalidation across multiple services or cache instances that each hold their own copy of the same data — essential once you scale beyond a single cache.

## 3. Core concept

**TTL-based expiry:** every entry is stored with an expiry time; the cache treats it as gone once that time passes, whether or not the underlying data actually changed. It requires no coordination but guarantees a staleness window equal to the TTL.

**Explicit invalidation:** the code path that writes new data also deletes (or updates) the matching cache entry as part of the same operation — the pattern already used in cache-aside and write-through. It is immediate and precise, but only invalidates the cache the writer itself knows about.

**Event-based invalidation:** the writer publishes an event ("`user:1` changed") to a message broker; every service holding its own cache subscribes to these events and invalidates its local copy on receipt. This is necessary once caching is distributed across multiple application instances, each with its own local (in-process) cache, because one instance's explicit invalidation cannot reach another instance's memory directly.

**Delete vs update on invalidation:** deleting the entry is usually safer than overwriting it with the new value, because a delete forces the next reader to reload fresh data from the source of truth, closing off a race where a slightly-out-of-order update could leave a stale value cached.

## 4. Diagram

```
Single instance, explicit invalidation:
  Writer: update DB -> delete cache["user:1"]                (done, safe)

Multiple instances, event-based invalidation:
  Instance A: update DB -> delete local cache["user:1"]
                          -> publish event "user:1 changed" --> Message broker
                                                                     |
                              Instance B <----------------------------+
                              Instance B: on receiving event, delete local cache["user:1"]
                              Instance C: on receiving event, delete local cache["user:1"]
```
*Caption: a single cache only needs explicit invalidation; multiple independent caches need an event to reach the ones the writer cannot touch directly.*

## 5. Runnable example

**Level 1 — Basic.** Explicit invalidation: a write deletes the matching cache entry in the same operation.

**Level 2 — TTL fallback.** An entry with an expiry timestamp that is treated as invalid once its time has passed, even without an explicit delete.

**Level 3 — Event-based, multi-instance.** Two independent in-memory caches subscribe to a shared event list; a write on one publishes an event that invalidates the entry on both.

```java
// CacheInvalidation.java
import java.util.HashMap;
import java.util.Map;
import java.util.ArrayList;
import java.util.List;

public class CacheInvalidation {

    static final Map<String, String> database = new HashMap<>();

    // Level 1: explicit invalidation on a single cache.
    static final Map<String, String> localCache = new HashMap<>();
    static void writeExplicit(String key, String value) {
        database.put(key, value);
        localCache.remove(key); // invalidate immediately, same operation
    }

    // Level 2: TTL-based invalidation, checked at read time.
    static class TtlEntry {
        String value; long expiresAtTick;
        TtlEntry(String value, long expiresAtTick) { this.value = value; this.expiresAtTick = expiresAtTick; }
    }
    static final Map<String, TtlEntry> ttlCache = new HashMap<>();
    static String readTtl(String key, long now) {
        TtlEntry e = ttlCache.get(key);
        if (e == null || now >= e.expiresAtTick) return null; // treated as invalid
        return e.value;
    }

    // Level 3: event-based invalidation across two independent caches.
    static final Map<String, String> cacheInstanceA = new HashMap<>();
    static final Map<String, String> cacheInstanceB = new HashMap<>();
    static final List<String> eventLog = new ArrayList<>();

    static void writeAndPublish(String key, String value) {
        database.put(key, value);
        cacheInstanceA.remove(key); // the writer's own local cache
        eventLog.add(key); // publish "changed" event for other instances
    }
    static void deliverEvents() {
        for (String key : eventLog) {
            cacheInstanceB.remove(key); // instance B invalidates on receiving the event
        }
        eventLog.clear();
    }

    public static void main(String[] args) {
        localCache.put("user:1", "Alice");
        writeExplicit("user:1", "Alice Smith");
        System.out.println("explicit: cache after write (should be absent): " + localCache.get("user:1"));

        ttlCache.put("price:XYZ", new TtlEntry("100", 100));
        System.out.println("ttl: read at t=50 (valid): " + readTtl("price:XYZ", 50));
        System.out.println("ttl: read at t=150 (expired): " + readTtl("price:XYZ", 150));

        cacheInstanceA.put("user:2", "Bob");
        cacheInstanceB.put("user:2", "Bob"); // both instances start with the same cached copy
        writeAndPublish("user:2", "Bob Jones");
        System.out.println("event: instance A right after write (invalidated locally): " + cacheInstanceA.get("user:2"));
        System.out.println("event: instance B BEFORE event delivery (still stale): " + cacheInstanceB.get("user:2"));
        deliverEvents();
        System.out.println("event: instance B AFTER event delivery (now invalidated): " + cacheInstanceB.get("user:2"));
    }
}
```

**How to run:** save as `CacheInvalidation.java`, then run `java CacheInvalidation.java`.

## 6. Walkthrough

1. `writeExplicit` writes the database and removes the key from `localCache` in the same call, so the very next line shows `localCache.get("user:1")` as `null`.
2. `readTtl("price:XYZ", 50)` sees `now=50 < expiresAtTick=100`, so the entry is still valid and its value is returned.
3. `readTtl("price:XYZ", 150)` sees `now=150 >= expiresAtTick=100` and returns `null` — the entry is treated as invalid purely because time passed, with no explicit delete involved.
4. `writeAndPublish("user:2", "Bob Jones")` updates the database, invalidates `cacheInstanceA` immediately, and queues an event in `eventLog` rather than touching `cacheInstanceB` directly.
5. Reading `cacheInstanceB` right after the write still shows the stale `"Bob"`, because the event has not been delivered yet — this is the propagation delay inherent to event-based invalidation.
6. `deliverEvents()` processes the queued event and removes `"user:2"` from `cacheInstanceB`; the final read confirms it is now invalidated too.

## 7. Gotchas & takeaways

> Gotcha: event-based invalidation has a delivery delay — between the write and the event reaching every instance, other instances serve stale data; if the message broker is slow or drops a message, that staleness can persist far longer than intended.

- Explicit invalidation is precise and immediate, but only for the cache the writer directly controls.
- TTL provides a safety net even when explicit or event-based invalidation is missed or delayed, at the cost of a guaranteed staleness window.
- Related concepts: [Cache consistency & staleness](0054-cache-consistency-staleness.md) (the broader question invalidation strategy answers), [Cache-aside (lazy loading)](0045-cache-aside-lazy-loading.md) (where explicit invalidation is most commonly applied).
