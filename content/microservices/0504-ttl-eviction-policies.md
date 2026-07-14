---
card: microservices
gi: 504
slug: ttl-eviction-policies
title: "TTL & eviction policies"
---

## 1. What it is

**TTL (time-to-live)** determines how long a cache entry stays valid before it's automatically treated as expired. **Eviction policy** determines which entries get removed when a cache reaches its capacity limit *before* their TTL would have naturally expired them — common policies include **LRU** (least recently used — evict whatever hasn't been accessed in the longest time), **LFU** (least frequently used — evict whatever has been accessed the fewest times), and **FIFO** (first in, first out — evict the oldest entry regardless of access pattern). TTL bounds staleness; eviction policy bounds memory use.

## 2. Why & when

You configure both deliberately, because an unbounded cache and a cache with no expiration are both quiet ways to cause real problems:

- **A cache with no size limit and no eviction policy will eventually consume unbounded memory**, since every unique key ever requested gets added and nothing ever removes an entry — this is a slow, easy-to-miss memory leak in disguise.
- **A cache with no TTL serves entries forever, however stale they become**, unless something else (explicit or event-based invalidation) removes them — for data that changes over time, a permanently-cached entry is a permanently-wrong entry waiting to be read.
- **LRU is the most common default eviction policy** because "recently accessed data is likely to be accessed again soon" (temporal locality) is a reasonable assumption for most real access patterns, and LRU is comparatively cheap to implement correctly.
- **You tune TTL and eviction policy per cache, based on the specific data's access pattern and staleness tolerance** — a cache of rarely-changing reference data might use a long TTL and a large capacity; a cache of hot, frequently-changing data might use a short TTL and rely more on its eviction policy to manage size under load.

## 3. Core concept

Think of a small refrigerator (a bounded cache) where each item has a "best by" date stamped on it (TTL) — items are removed and thrown out once that date passes, regardless of anything else. But the fridge also has limited shelf space: if it's completely full and a new item needs to go in, something else has to come out *right now*, even if its "best by" date hasn't arrived yet — the eviction policy decides *which* item to sacrifice, whether that's whatever's been sitting untouched the longest (LRU) or whatever you eat the least often (LFU).

Concretely:

1. **TTL expiry**: each entry carries its own expiration time, set when it's written; on read, an expired entry is treated as absent regardless of whether it's still physically present in the cache's internal storage.
2. **LRU (least recently used)**: the cache tracks access order; when capacity is exceeded, the entry that hasn't been *read* in the longest time is evicted first, regardless of how long ago it was written or how many total times it's been accessed historically.
3. **LFU (least frequently used)**: the cache tracks access *count*; when capacity is exceeded, the entry with the *fewest total accesses* is evicted, which can behave very differently from LRU for data with occasional bursts of popularity followed by long quiet periods.
4. **FIFO**: the simplest policy — evict whatever was inserted longest ago, with no regard to access pattern at all — cheap to implement, but often a worse fit than LRU or LFU for genuinely skewed real-world access patterns.
5. **TTL and eviction operate independently and simultaneously**: an entry can be evicted early due to capacity pressure well before its TTL would have expired it, or it can expire via TTL long before capacity pressure would ever have evicted it.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="TTL removes entries after a fixed duration regardless of capacity; eviction policy removes entries when capacity is exceeded regardless of TTL, choosing which entry based on access pattern">
  <rect x="20" y="20" width="290" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="165" y="45" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">TTL expiry</text>
  <text x="165" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">removes after fixed time, regardless of capacity</text>

  <rect x="350" y="20" width="290" height="70" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="495" y="45" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">eviction policy (LRU/LFU/FIFO)</text>
  <text x="495" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">removes when capacity exceeded, regardless of TTL</text>

  <text x="330" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">both operate independently and simultaneously on the same cache</text>
</svg>

Two independent mechanisms bounding staleness and memory use respectively.

## 5. Runnable example

Scenario: a bounded cache with both TTL and LRU eviction. We start with basic TTL-only expiry, extend it to a size-bounded cache using LRU eviction, then handle the hard case: an entry that's frequently accessed (so LRU would never evict it) but has genuinely expired via TTL, which must still be correctly treated as gone despite its "popularity."

### Level 1 — Basic

```java
// File: TtlOnlyBasic.java -- models TTL expiry in ISOLATION, with NO
// capacity limit -- entries live forever UNLESS their TTL has passed.
import java.util.*;

public class TtlOnlyBasic {
    record Entry(String value, long expiresAtMs) {}
    static Map<String, Entry> cache = new HashMap<>();

    static void put(String key, String value, long ttlMs) {
        cache.put(key, new Entry(value, System.currentTimeMillis() + ttlMs));
    }

    static String get(String key) {
        Entry entry = cache.get(key);
        if (entry == null || System.currentTimeMillis() >= entry.expiresAtMs()) {
            System.out.println("[cache] '" + key + "' MISS or EXPIRED");
            return null;
        }
        System.out.println("[cache] '" + key + "' HIT");
        return entry.value();
    }

    public static void main(String[] args) throws InterruptedException {
        put("sku-123", "in-stock", 100);
        System.out.println("immediately: " + get("sku-123"));
        Thread.sleep(150);
        System.out.println("after TTL: " + get("sku-123"));
    }
}
```

How to run: `java TtlOnlyBasic.java`

`get` compares the current time to `entry.expiresAtMs()` on every access — no capacity concept exists here at all, so an entry is only ever removed logically (treated as a miss) by TTL, regardless of how much memory the underlying map might grow to hold.

### Level 2 — Intermediate

```java
// File: LruEvictionBasic.java -- the SAME cache concept, now with a
// CAPACITY LIMIT and LRU eviction: when full, the LEAST RECENTLY
// ACCESSED entry is evicted to make room, using LinkedHashMap's built-in
// access-order tracking.
import java.util.*;

public class LruEvictionBasic {
    static int capacity = 3;
    static LinkedHashMap<String, String> cache = new LinkedHashMap<>(16, 0.75f, true) { // true = access-order
        protected boolean removeEldestEntry(Map.Entry<String, String> eldest) {
            boolean shouldEvict = size() > capacity;
            if (shouldEvict) System.out.println("[LRU] capacity exceeded -- evicting least-recently-used: " + eldest.getKey());
            return shouldEvict;
        }
    };

    public static void main(String[] args) {
        cache.put("a", "1"); cache.put("b", "2"); cache.put("c", "3");
        System.out.println("cache after initial fill: " + cache.keySet());

        cache.get("a"); // accessing "a" marks it as recently used, moving it to the "end"
        System.out.println("accessed 'a' -- now the most-recently-used");

        cache.put("d", "4"); // capacity exceeded -- least recently used ("b") gets evicted
        System.out.println("cache after inserting 'd': " + cache.keySet());
    }
}
```

How to run: `java LruEvictionBasic.java`

`LinkedHashMap`'s access-order mode (the `true` constructor argument) reorders entries internally on every `get`, so the "eldest" entry (checked by `removeEldestEntry`) is always whichever key was *accessed* longest ago, not just inserted longest ago. Accessing `"a"` before inserting `"d"` means `"a"` is no longer the least-recently-used, so `"b"` — untouched since its initial insertion — is the one evicted instead.

### Level 3 — Advanced

```java
// File: TtlAndLruIndependent.java -- the SAME LRU-evicting cache, now
// COMBINED with TTL, handling the PRODUCTION-FLAVORED hard case: an entry
// is accessed FREQUENTLY (so LRU alone would NEVER evict it -- it's
// always "recently used"), but its TTL has genuinely EXPIRED. TTL and
// eviction are INDEPENDENT mechanisms -- a popular entry must STILL be
// treated as gone once its TTL passes, regardless of how often it's accessed.
import java.util.*;

public class TtlAndLruIndependent {
    record Entry(String value, long expiresAtMs) {}
    static int capacity = 3;
    static LinkedHashMap<String, Entry> cache = new LinkedHashMap<>(16, 0.75f, true) {
        protected boolean removeEldestEntry(Map.Entry<String, Entry> eldest) {
            return size() > capacity;
        }
    };

    static void put(String key, String value, long ttlMs) {
        cache.put(key, new Entry(value, System.currentTimeMillis() + ttlMs));
    }

    static String get(String key) {
        Entry entry = cache.get(key); // this call ALSO marks the key as recently-used for LRU purposes
        if (entry == null) {
            System.out.println("[cache] '" + key + "' MISS (not present / already LRU-evicted)");
            return null;
        }
        if (System.currentTimeMillis() >= entry.expiresAtMs()) {
            System.out.println("[cache] '" + key + "' TTL EXPIRED despite being frequently accessed -- treating as MISS");
            cache.remove(key); // explicitly remove the expired entry, even though LRU never would have
            return null;
        }
        System.out.println("[cache] '" + key + "' HIT");
        return entry.value();
    }

    public static void main(String[] args) throws InterruptedException {
        put("popular-sku", "in-stock", 100); // short TTL, 100ms

        // Access it repeatedly, keeping it as the MOST recently used entry every time --
        // LRU alone would NEVER choose to evict this key.
        System.out.println("--- accessing 'popular-sku' repeatedly, well within its TTL ---");
        for (int i = 1; i <= 3; i++) {
            get("popular-sku");
            Thread.sleep(20);
        }

        System.out.println();
        System.out.println("--- waiting past the TTL, but STILL accessing it (staying 'most recently used') ---");
        Thread.sleep(60); // total elapsed time now exceeds the 100ms TTL
        String result = get("popular-sku");
        System.out.println("[result] value: " + result + " -- TTL correctly overrides LRU's 'keep the popular one' bias");
    }
}
```

How to run: `java TtlAndLruIndependent.java`

`get` checks TTL expiry *after* the `LinkedHashMap` access has already happened (which updates LRU ordering), and explicitly `cache.remove(key)`s an expired entry even though nothing about LRU's own logic would ever have chosen to evict a key this frequently accessed. This proves the two mechanisms are genuinely independent: an entry's access frequency has zero bearing on whether its TTL has passed, and the explicit TTL check is what catches this case that pure LRU tracking never would.

## 6. Walkthrough

Trace `TtlAndLruIndependent.main` in order. **First**, `put("popular-sku", "in-stock", 100)` stores the entry with an expiration `100ms` in the future.

**Next**, the loop runs three `get("popular-sku")` calls, each followed by a `20ms` sleep — roughly `60ms` elapses in total across this loop. Each call's `System.currentTimeMillis() >= entry.expiresAtMs()` check is `false`, since less than `100ms` has passed each time, so each access is reported as a normal HIT, and each `LinkedHashMap.get` call marks `"popular-sku"` as the most-recently-used entry all over again.

**Then**, an additional `60ms` sleep runs, bringing the total elapsed time since `put` to roughly `120ms` — now past the `100ms` TTL.

**After that**, the final `get("popular-sku")` call runs. The `LinkedHashMap.get` call itself succeeds in finding the entry (it was never LRU-evicted, since it's been the most-recently-accessed key throughout), so `entry` is non-null and the first `if (entry == null)` check is skipped. But the second check, `System.currentTimeMillis() >= entry.expiresAtMs()`, is now `true`, since real elapsed time has exceeded the TTL — the expired branch runs, printing the specific message noting this despite frequent access, explicitly calling `cache.remove(key)`, and returning `null`.

**Finally**, `main` prints the result as `null`, with a message emphasizing that TTL correctly overrode LRU's natural bias toward keeping frequently-accessed entries — demonstrating concretely that these two mechanisms check genuinely different, independent conditions, and an entry needs to satisfy *both* "not TTL-expired" and "not LRU-evicted" to remain validly cached.

```
--- accessing 'popular-sku' repeatedly, well within its TTL ---
[cache] 'popular-sku' HIT
[cache] 'popular-sku' HIT
[cache] 'popular-sku' HIT

--- waiting past the TTL, but STILL accessing it (staying 'most recently used') ---
[cache] 'popular-sku' TTL EXPIRED despite being frequently accessed -- treating as MISS
[result] value: null -- TTL correctly overrides LRU's 'keep the popular one' bias
```

## 7. Gotchas & takeaways

> Assuming a popular, frequently-accessed cache entry is automatically "safe" from ever going stale is a real mistake — access frequency affects *eviction* decisions (LRU/LFU), but has absolutely no bearing on *TTL* expiry, which is purely a function of elapsed time since the entry was written. A hot, popular entry can be just as stale as a cold, rarely-accessed one.
- LRU is a reasonable default eviction policy for most workloads, but LFU can outperform it specifically for data with bursty popularity followed by long quiet periods, where "recently accessed" and "genuinely important to keep" diverge.
- Size your cache's capacity based on actual memory constraints and the working set size of your access pattern — too small a capacity causes excessive eviction churn (evicting and re-fetching the same hot data repeatedly); too large wastes memory that could serve other purposes.
- This is closely related to, but distinct from, [cache invalidation](0503-cache-invalidation.md) — invalidation is about correctness (removing data that's now *wrong*), while TTL and eviction are about bounding staleness and memory *by policy*, independent of whether the underlying data has actually changed.
- Test TTL and eviction behavior under realistic access patterns, not just isolated unit tests — the interaction between the two (as shown in Level 3) only becomes visible when both are exercised together over enough elapsed time and enough access volume to matter.
