---
card: java
gi: 402
slug: concurrenthashmap
title: ConcurrentHashMap
---

## 1. What it is

`ConcurrentHashMap<K,V>` is a thread-safe `Map` implementation designed for high-concurrency reads and writes, without the heavy cost of wrapping every operation in a single lock (like `Collections.synchronizedMap` does). It also adds atomic compound operations — `putIfAbsent`, `computeIfAbsent`, `compute`, `merge` — that perform a read-then-write as one indivisible step, something a plain `HashMap` (or even a naively-synchronized one) cannot safely do without extra external locking.

## 2. Why & when

A plain `HashMap` is not thread-safe: concurrent modification from multiple threads can corrupt its internal structure (in older Java versions this could even cause an infinite loop during resizing) or silently lose updates. `Collections.synchronizedMap(new HashMap<>())` fixes the corruption problem but funnels *every* operation, including reads, through one single lock — so under heavy concurrent access, threads spend most of their time waiting for that one lock, defeating the purpose of using multiple threads.

`ConcurrentHashMap` was built specifically to fix this: it lets many threads read and write concurrently with far less contention, by partitioning locking internally rather than using one map-wide lock. Just as importantly, it provides atomic "check and update" operations like `computeIfAbsent` and `merge`, so common patterns — "insert this key only if it's the first time we've seen it" or "atomically increment a per-key counter" — don't need any external `synchronized` block at all. Reach for it whenever a `Map` is shared and mutated by more than one thread, which is extremely common for caches, counters, and registries.

## 3. Core concept

```java
ConcurrentHashMap<String, Integer> hits = new ConcurrentHashMap<>();

// WRONG under concurrency, even with a "thread-safe" map: read-then-write is two separate steps
Integer count = hits.get("page1");
hits.put("page1", (count == null ? 0 : count) + 1); // another thread could interleave here!

// RIGHT: merge() performs the read-modify-write as ONE atomic operation
hits.merge("page1", 1, Integer::sum); // adds 1 if absent, otherwise sums with existing value -- atomically
```

The key insight: thread-safety of the *container* doesn't automatically make a multi-step *sequence of operations on it* safe. `ConcurrentHashMap`'s compound methods (`compute`, `computeIfAbsent`, `computeIfPresent`, `merge`) exist precisely to collapse those sequences into one atomic call.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two threads calling get then put can race and lose an update; merge performs the read-modify-write atomically">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#f85149" font-size="11" font-family="sans-serif">get() then put() -- NOT atomic, can lose updates:</text>
  <text x="30" y="46" fill="#79c0ff" font-size="10" font-family="sans-serif">Thread A: get("x") -&gt; 5</text>
  <text x="30" y="64" fill="#6db33f" font-size="10" font-family="sans-serif">Thread B: get("x") -&gt; 5</text>
  <text x="30" y="82" fill="#79c0ff" font-size="10" font-family="sans-serif">Thread A: put("x", 6)</text>
  <text x="30" y="100" fill="#6db33f" font-size="10" font-family="sans-serif">Thread B: put("x", 6)   &lt;- lost update! should be 7</text>

  <text x="20" y="132" fill="#6db33f" font-size="11" font-family="sans-serif">merge("x", 1, Integer::sum) -- atomic, always correct:</text>
  <text x="30" y="152" fill="#79c0ff" font-size="10" font-family="sans-serif">Thread A: merge -&gt; 6 (atomic read+write)</text>
  <text x="30" y="170" fill="#6db33f" font-size="10" font-family="sans-serif">Thread B: merge -&gt; 7 (atomic read+write)</text>
</svg>

Separate `get()`/`put()` calls can race even on a thread-safe map; atomic compound methods like `merge` cannot.

## 5. Runnable example

Scenario: a web page-view counter shared across request-handling threads — the same counter map, evolved from a naive (buggy) increment pattern, through the correct atomic `merge`, to a small in-memory cache using `computeIfAbsent` to avoid redundant expensive lookups.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class HitCounterBuggy {
    public static void main(String[] args) throws InterruptedException {
        ConcurrentHashMap<String, Integer> hits = new ConcurrentHashMap<>();
        hits.put("home", 0);

        Runnable incrementer = () -> {
            for (int i = 0; i < 1000; i++) {
                Integer current = hits.get("home"); // read...
                hits.put("home", current + 1);       // ...then write: NOT atomic as a pair!
            }
        };

        Thread t1 = new Thread(incrementer);
        Thread t2 = new Thread(incrementer);
        t1.start(); t2.start();
        t1.join(); t2.join();

        System.out.println("Hits (expected 2000): " + hits.get("home"));
    }
}
```

**How to run:** `java HitCounterBuggy.java`

Even though `ConcurrentHashMap` itself is thread-safe, `get()` followed by `put()` is **two separate operations** — two threads can both read the same value before either writes back, causing one increment to be silently lost. The printed total is usually *less* than 2000, and the exact shortfall varies run to run.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class HitCounterAtomic {
    public static void main(String[] args) throws InterruptedException {
        ConcurrentHashMap<String, Integer> hits = new ConcurrentHashMap<>();
        hits.put("home", 0);

        Runnable incrementer = () -> {
            for (int i = 0; i < 1000; i++) {
                hits.merge("home", 1, Integer::sum); // atomic: read + add + write as one step
            }
        };

        Thread t1 = new Thread(incrementer);
        Thread t2 = new Thread(incrementer);
        t1.start(); t2.start();
        t1.join(); t2.join();

        System.out.println("Hits (expected 2000): " + hits.get("home"));
    }
}
```

**How to run:** `java HitCounterAtomic.java`

`merge("home", 1, Integer::sum)` replaces the buggy get-then-put pair with one atomic call: "add 1 to the existing value (or use 1 if absent), as a single indivisible step." The result is now reliably exactly `2000`, no matter how the two threads interleave.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class ExpensiveLookupCache {
    static String expensiveLookup(String key) {
        System.out.println("  (actually computing for " + key + " on " + Thread.currentThread().getName() + ")");
        try { Thread.sleep(100); } catch (InterruptedException ignored) { }
        return "value-for-" + key;
    }

    public static void main(String[] args) throws InterruptedException {
        ConcurrentHashMap<String, String> cache = new ConcurrentHashMap<>();

        Runnable worker = () -> {
            String result = cache.computeIfAbsent("shared-key", ExpensiveLookupCache::expensiveLookup);
            System.out.println(Thread.currentThread().getName() + " got: " + result);
        };

        Thread t1 = new Thread(worker, "worker-1");
        Thread t2 = new Thread(worker, "worker-2");
        Thread t3 = new Thread(worker, "worker-3");
        t1.start(); t2.start(); t3.start();
        t1.join(); t2.join(); t3.join();

        System.out.println("Final cache size: " + cache.size());
    }
}
```

**How to run:** `java ExpensiveLookupCache.java`

`computeIfAbsent` guarantees the expensive `expensiveLookup` function runs **at most once per key**, even with three threads racing to populate the same cache entry simultaneously — `ConcurrentHashMap` internally ensures only one thread's computation "wins" for a given key, and the others simply wait for and reuse that result instead of redundantly recomputing it.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. An empty `ConcurrentHashMap<String, String> cache` is created, then three threads (`worker-1`, `worker-2`, `worker-3`) are started, each running the same `worker` lambda that calls `cache.computeIfAbsent("shared-key", ExpensiveLookupCache::expensiveLookup)`.

Because all three threads start almost simultaneously and target the *same key* (`"shared-key"`), they race to be the one that actually computes the value. `ConcurrentHashMap` guarantees that for a given key, only one thread's `computeIfAbsent` call will actually invoke the mapping function (`expensiveLookup`) at a time — whichever thread gets there first "locks" that key's computation. Suppose `worker-1` wins the race: it calls `expensiveLookup("shared-key")`, which prints `"(actually computing for shared-key on worker-1)"`, sleeps 100ms to simulate real work, and returns `"value-for-shared-key"`. This return value is stored in the cache under `"shared-key"`.

Meanwhile, `worker-2` and `worker-3`, having lost the race for that same key, do **not** call `expensiveLookup` themselves — instead, they block briefly until `worker-1`'s computation finishes, and then both receive the *same* already-computed `"value-for-shared-key"` result directly from the cache. Only one `"(actually computing for shared-key ...)"` line is ever printed, no matter which of the three threads happened to win.

Each thread then prints its own `"workerName got: value-for-shared-key"` line, all three showing the identical value. Finally, `main`'s `cache.size()` reports `1`, since all three threads ultimately populated (or reused) the exact same single key.

Expected output (thread order of the final three print lines may vary, but the computation happens exactly once):
```
  (actually computing for shared-key on worker-1)
worker-1 got: value-for-shared-key
worker-2 got: value-for-shared-key
worker-3 got: value-for-shared-key
Final cache size: 1
```

## 7. Gotchas & takeaways

> A `Map` being thread-safe does **not** make a *sequence* of operations on it thread-safe. `get()` followed by `put()` is two separate steps with a race window between them — always reach for `merge`, `compute`, `computeIfAbsent`, or `computeIfPresent` when the update depends on the current value, exactly as Level 2 demonstrates fixing Level 1's bug.

- `ConcurrentHashMap` allows highly concurrent reads and writes without a single map-wide lock, unlike `Collections.synchronizedMap(new HashMap<>())`.
- `merge(key, value, remappingFunction)` is the idiomatic atomic way to update a counter or accumulate a value per key.
- `computeIfAbsent(key, mappingFunction)` guarantees the expensive mapping function runs at most once per key, even under concurrent access — ideal for lazily-populated caches.
- Never rely on separate `get()`/`containsKey()`/`put()` calls when another thread might be mutating the same map concurrently — use the atomic compound methods instead.
- `ConcurrentHashMap` does not allow `null` keys or `null` values (unlike `HashMap`), specifically because `null` would make some of these atomic "is it present?" checks ambiguous.
