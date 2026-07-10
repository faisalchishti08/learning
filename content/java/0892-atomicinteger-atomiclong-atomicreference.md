---
card: java
gi: 892
slug: atomicinteger-atomiclong-atomicreference
title: AtomicInteger / AtomicLong / AtomicReference
---

## 1. What it is

`AtomicInteger`, `AtomicLong`, and `AtomicReference<V>` are wrapper classes around a single mutable value (an `int`, a `long`, or an object reference, respectively) that provide atomic, lock-free read-modify-write operations built on [CAS](0891-cas-compare-and-swap.md) — `get()`, `set()`, `incrementAndGet()`/`decrementAndGet()`/`addAndGet()` (numeric types only), `compareAndSet(expected, new)`, `getAndUpdate(UnaryOperator)`, `updateAndGet(UnaryOperator)`, and more. They exist specifically to make the "read, compute, write" sequence — which is not atomic for a plain field, even one marked `volatile` — genuinely atomic without needing a lock.

## 2. Why & when

Use these classes for any single piece of shared, mutable state that needs atomic compound updates — a counter incremented from multiple threads, a "current leader" reference that gets swapped via compare-and-set, a flag that needs an atomic check-and-set. This is precisely the situation where `volatile` alone is insufficient (recall from [`volatile` semantics](0858-volatile-semantics.md) that `volatile int counter; counter++;` is *not* atomic, since it's three separate steps) — `AtomicInteger.incrementAndGet()` performs the equivalent operation as one indivisible unit. `AtomicReference<V>` generalizes the same idea to arbitrary object references, letting you atomically swap out an entire immutable object (a configuration snapshot, a linked-list node) via `compareAndSet` — a common building block for lock-free data structures.

## 3. Core concept

```java
AtomicInteger counter = new AtomicInteger(0);
counter.incrementAndGet();               // atomic ++counter
counter.compareAndSet(5, 10);            // atomic: if counter == 5, set it to 10

AtomicReference<Config> configRef = new AtomicReference<>(initialConfig);
Config current = configRef.get();
Config updated = current.withNewSetting(value);
configRef.compareAndSet(current, updated); // atomic swap -- fails if someone else already changed it

configRef.updateAndGet(cfg -> cfg.withNewSetting(value)); // retries internally until it succeeds
```

Every one of these methods is implemented internally via a CAS-retry loop — from the caller's perspective, they simply always succeed eventually and return the resulting (or prior) value, with no visible retry logic needed in application code.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AtomicReference holding a pointer to an immutable Config object; compareAndSet atomically swaps it for a new Config object only if no other thread has already changed it">
  <rect x="20" y="30" width="180" height="45" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">AtomicReference&lt;Config&gt;</text>
  <text x="110" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">currently points to Config-v1</text>

  <rect x="260" y="30" width="140" height="45" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="330" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Config-v1 (old)</text>

  <rect x="440" y="30" width="140" height="45" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="510" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Config-v2 (new)</text>

  <line x1="200" y1="52" x2="256" y2="52" stroke="#8b949e" stroke-width="2" marker-end="url(#a26)"/>
  <text x="330" y="110" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">compareAndSet(Config-v1, Config-v2)</text>
  <line x1="330" y1="75" x2="480" y2="75" stroke="#6db33f" stroke-width="2" stroke-dasharray="4" marker-end="url(#a26)"/>
  <text x="405" y="130" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">succeeds ONLY if the reference still points to Config-v1</text>
  <defs><marker id="a26" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*`AtomicReference` swaps an entire object pointer atomically — the whole `Config` object is treated as an immutable snapshot, replaced in one indivisible step.*

## 5. Runnable example

Scenario: a live configuration object shared across threads, growing from a `volatile`-only version that can't atomically update derived fields, to `AtomicInteger` for a simple request counter, to `AtomicReference` for atomically swapping the entire immutable configuration snapshot with retry-based updates.

### Level 1 — Basic

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class AtomicIntegerCounter {
    static AtomicInteger requestCount = new AtomicInteger(0);

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(8);
        for (int i = 0; i < 50_000; i++) {
            pool.submit(requestCount::incrementAndGet); // atomic, no lost updates
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("total requests handled: " + requestCount.get());
    }
}
```

**How to run:** `java AtomicIntegerCounter.java` (JDK 17+).

Expected output:
```
total requests handled: 50000
```

A straightforward, correctly-counted, lock-free counter — every one of the 50,000 concurrent increments is accounted for exactly once.

### Level 2 — Intermediate

```java
import java.util.concurrent.atomic.*;

public class AtomicLongAndCompareAndSet {
    static AtomicLong highScore = new AtomicLong(0);

    // Only updates highScore if the new score is actually higher -- a classic compareAndSet use case
    static void reportScore(long newScore) {
        long current;
        do {
            current = highScore.get();
            if (newScore <= current) return; // no improvement -- nothing to do
        } while (!highScore.compareAndSet(current, newScore)); // retry if another thread updated it first
    }

    public static void main(String[] args) throws InterruptedException {
        long[] scores = {100, 500, 300, 800, 250, 900, 400};
        Thread[] threads = new Thread[scores.length];
        for (int i = 0; i < scores.length; i++) {
            final long score = scores[i];
            threads[i] = new Thread(() -> reportScore(score));
            threads[i].start();
        }
        for (Thread t : threads) t.join();

        System.out.println("high score = " + highScore.get() + " (expected 900, the max of all reported scores)");
    }
}
```

**How to run:** `java AtomicLongAndCompareAndSet.java`.

Expected output:
```
high score = 900 (expected 900, the max of all reported scores)
```

The real-world concern added: `compareAndSet` used explicitly in a retry loop to implement "update only if the new value is actually an improvement," correctly handling the case where several threads report scores concurrently — regardless of the order threads happen to run in, the final `highScore` is guaranteed to be the true maximum, with no lost updates even if two threads' `get()`/`compareAndSet()` calls interleave.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class AtomicReferenceConfigSwap {
    record Config(int maxConnections, String mode) {
        Config withMaxConnections(int newMax) { return new Config(newMax, mode); }
    }

    static AtomicReference<Config> configRef = new AtomicReference<>(new Config(10, "normal"));

    // Atomically increments maxConnections by 5, retrying if another thread updates concurrently.
    static void bumpMaxConnections() {
        configRef.updateAndGet(cfg -> cfg.withMaxConnections(cfg.maxConnections() + 5));
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(8);
        for (int i = 0; i < 20; i++) {
            pool.submit(AtomicReferenceConfigSwap::bumpMaxConnections);
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);

        Config finalConfig = configRef.get();
        System.out.println("final config: " + finalConfig);
        System.out.println("expected maxConnections = 10 + 20*5 = " + (10 + 20 * 5));
    }
}
```

**How to run:** `java AtomicReferenceConfigSwap.java`.

Expected output:
```
final config: Config[maxConnections=110, mode=normal]
expected maxConnections = 10 + 20*5 = 110
```

This adds the production-flavored hard case: atomically updating a whole immutable `Config` object — not just a single number — across 20 concurrent calls, using `updateAndGet` with a function that reads the *current* `Config`, derives a new one from it, and retries the whole swap if another thread's update won the race first. Because `Config` is an immutable record and every update goes through `AtomicReference.updateAndGet`, there's no possibility of a lost update or a torn read of a partially-updated configuration, even under genuine concurrent contention from 8 threads racing through 20 updates.

## 6. Walkthrough

Tracing `AtomicReferenceConfigSwap.main` as several threads call `bumpMaxConnections()` concurrently:

1. `configRef.updateAndGet(cfg -> cfg.withMaxConnections(cfg.maxConnections() + 5))` is called by multiple threads at roughly the same time. Internally, `updateAndGet` reads the current `Config` reference — say `Config(10, "normal")` — and applies the lambda to it, producing a *new* `Config(15, "normal")` object (since `Config` is immutable, `withMaxConnections` returns a fresh instance rather than mutating the original).
2. `updateAndGet` then attempts a CAS: "if `configRef` still points to the exact `Config(10, "normal")` object I read, atomically swap it for the new `Config(15, "normal")` object."
3. If a different thread's `updateAndGet` call already succeeded in between (swapping in, say, `Config(15, "normal")` from its own concurrent call), this thread's CAS fails, since `configRef` no longer points to the original object it read.
4. On CAS failure, `updateAndGet` automatically retries: it re-reads the *new* current value (`Config(15, "normal")`), reapplies the lambda (`cfg.maxConnections() + 5 = 20`), producing `Config(20, "normal")`, and attempts the CAS again.
5. This retry loop continues internally, transparently to the calling code, until each of the 20 submitted `bumpMaxConnections()` calls successfully applies its own `+5` increment — since every single call's effect is captured atomically and no update is ever silently lost to a race, after all 20 calls complete, the final `maxConnections` value is guaranteed to be exactly `10 + 20*5 = 110`.
6. `configRef.get()` in `main`, called only after `pool.awaitTermination` confirms every submitted task has finished, retrieves this final, fully-updated `Config` object, and the printed values confirm the arithmetic held exactly, with no lost updates despite the concurrent contention.

## 7. Gotchas & takeaways

> **Gotcha:** `AtomicReference.compareAndSet` (and the update methods built on it) compare by **reference identity**, not by `.equals()` — if your object's class overrides `equals()` but you construct a logically-equal-but-different instance, a manual `compareAndSet(oldRef, newRef)` call using a freshly-constructed "old" object (rather than the exact instance you originally read) will always fail, since it's not the same object in memory.

- `AtomicInteger`/`AtomicLong` provide atomic compound operations (`incrementAndGet`, `addAndGet`, `compareAndSet`) for numeric counters — the correct replacement for a `volatile int` whenever the update depends on the current value.
- `AtomicReference<V>` generalizes the same atomicity to arbitrary object references, letting you atomically swap an entire immutable object — a foundational building block for lock-free data structures and configuration hot-swapping.
- `updateAndGet`/`getAndUpdate` (and their two-argument `accumulateAndGet` cousins) let you express arbitrary atomic read-modify-write logic without manually writing a CAS-retry loop — prefer these over hand-rolled loops for anything beyond a simple increment.
- Every atomic method here is built on [CAS](0891-cas-compare-and-swap.md) — understanding that underlying mechanism explains why these classes never block, and why they can occasionally retry internally under contention.
- For counters under *very* high contention specifically (many threads incrementing simultaneously), [`LongAdder`](0895-longadder-longaccumulator.md) often outperforms `AtomicLong` by spreading updates across multiple internal cells — worth knowing as the next step up when `AtomicLong` itself becomes a contention bottleneck.
