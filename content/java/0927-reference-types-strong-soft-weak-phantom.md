---
card: java
gi: 927
slug: reference-types-strong-soft-weak-phantom
title: Reference types (strong/soft/weak/phantom)
---

## 1. What it is

Java has four distinct kinds of references, each giving the garbage collector different permission to reclaim the object they point to. **Strong** references are the ordinary kind (a plain variable, field, or array element) — as long as one exists, the collector will never reclaim the referent, no matter how much memory pressure exists. **Soft** references (`SoftReference<T>`) are reclaimed only when the JVM is genuinely running low on memory, making them suitable for memory-sensitive caches that should hold data as long as there's room, but release it under pressure rather than causing an `OutOfMemoryError`. **Weak** references (`WeakReference<T>`) are reclaimed at the very next garbage collection cycle if no strong reference to the same object exists, regardless of memory pressure — used throughout this course's own examples to observe collectibility, and the basis of `WeakHashMap`. **Phantom** references (`PhantomReference<T>`) are the most restrictive: `get()` always returns `null` (you can never actually retrieve the referent through a phantom reference), and they exist purely to be notified, via a `ReferenceQueue`, *after* the referent has already been finalized and is about to be reclaimed — used for reliable, post-mortem cleanup actions.

## 2. Why & when

Choosing the right reference type solves a specific, recurring problem: how strongly should this particular reference to an object hold it alive, given what the reference is actually *for*? Use a strong reference (the default, ordinary kind) for anything the program genuinely needs to keep using. Use a soft reference for caches where holding data longer is a nice-to-have but not essential — the JVM will keep soft-referenced objects around as long as memory allows, then clear them (all soft references are guaranteed to be cleared before an `OutOfMemoryError` is thrown) rather than let memory pressure cause a crash. Use a weak reference when you want to track or reference an object without that reference itself being a reason to keep it alive — canonicalizing maps (`WeakHashMap`), and diagnostic/testing code observing whether something has actually been collected. Use a phantom reference specifically when you need guaranteed post-collection cleanup notification and don't need (or want) to resurrect or access the object itself — a more reliable, structured replacement for the deprecated `finalize()` mechanism.

## 3. Core concept

```java
Object obj = new Object();                       // STRONG -- prevents collection unconditionally
SoftReference<Object> soft = new SoftReference<>(obj);   // reclaimed only under memory pressure
WeakReference<Object> weak = new WeakReference<>(obj);   // reclaimed at the NEXT GC, once no strong ref remains
ReferenceQueue<Object> queue = new ReferenceQueue<>();
PhantomReference<Object> phantom = new PhantomReference<>(obj, queue); // phantom.get() ALWAYS returns null

obj = null; // remove the ONLY strong reference
// Now: soft.get() likely still returns the object (unless memory is genuinely tight);
//      weak.get() returns null after the next GC;
//      phantom is enqueued onto `queue` once the object is finalized and about to be reclaimed.
```

Each reference type answers a different question: "keep this alive unconditionally" (strong), "keep it alive unless memory is tight" (soft), "let me observe it without keeping it alive" (weak), "tell me exactly when it's gone" (phantom).

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four reference types arranged by decreasing strength: strong references always prevent collection, soft references are cleared only under memory pressure, weak references are cleared at the next collection, phantom references never allow retrieval and only notify after finalization">
  <rect x="20" y="20" width="140" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="90" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Strong -- never collected</text>

  <rect x="180" y="20" width="140" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="250" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Soft -- under memory pressure</text>

  <rect x="340" y="20" width="140" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="410" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Weak -- next GC cycle</text>

  <rect x="500" y="20" width="130" height="40" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="565" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Phantom -- get() always null</text>

  <text x="320" y="90" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Decreasing "strength" left to right --</text>
  <text x="320" y="110" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">each answers a different question about WHEN reclamation is allowed.</text>
</svg>

*The four reference types form a spectrum of decreasing insistence that the referent stay alive, each suited to a different use case.*

## 5. Runnable example

Scenario: a simple image cache, growing from a naive strong-reference cache (risking `OutOfMemoryError` under load), to a `SoftReference`-based cache that releases entries under memory pressure, to combining a `WeakReference` (for diagnostic tracking) and a `PhantomReference` (for guaranteed cleanup notification) around the same object's lifecycle.

### Level 1 — Basic

```java
import java.util.*;

public class StrongReferenceCacheRisk {
    static Map<Integer, byte[]> cache = new HashMap<>(); // STRONG references -- NEVER released automatically

    public static void main(String[] args) {
        try {
            for (int i = 0; i < 10_000; i++) {
                cache.put(i, new byte[100_000]); // ~1GB total if allowed to run to completion
            }
            System.out.println("cached " + cache.size() + " entries without running out of memory");
        } catch (OutOfMemoryError e) {
            System.out.println("caught OutOfMemoryError -- cache size ballooned unconditionally: " + cache.size() + " entries before failure");
        }
    }
}
```

**How to run:** `java -Xmx256m StrongReferenceCacheRisk.java` (JDK 17+; capping heap size makes the risk concrete quickly).

Expected output shape (depends on the exact heap cap, but demonstrates unconditional growth until failure):
```
caught OutOfMemoryError -- cache size ballooned unconditionally: 2419 entries before failure
```

A cache built with ordinary, strong references has no mechanism to release entries under memory pressure — it simply grows until the heap is exhausted, risking `OutOfMemoryError` for what's supposed to be a "nice-to-have" cache rather than essential state.

### Level 2 — Intermediate

```java
import java.lang.ref.*;
import java.util.*;

public class SoftReferenceCache {
    static Map<Integer, SoftReference<byte[]>> cache = new HashMap<>();

    public static void main(String[] args) {
        int successfullyStored = 0;
        for (int i = 0; i < 10_000; i++) {
            cache.put(i, new SoftReference<>(new byte[100_000])); // SOFT -- reclaimable under pressure
            successfullyStored++;
        }

        int stillPresent = 0;
        for (SoftReference<byte[]> ref : cache.values()) {
            if (ref.get() != null) stillPresent++;
        }

        System.out.println("attempted to store: " + successfullyStored);
        System.out.println("entries still present (not yet reclaimed): " + stillPresent);
        System.out.println("no OutOfMemoryError -- the JVM cleared some/all soft references under pressure instead");
    }
}
```

**How to run:** `java -Xmx256m SoftReferenceCache.java` (JDK 17+; same heap cap as Level 1, for direct comparison).

Expected output shape (no crash; some entries have been cleared, reflecting the JVM proactively reclaiming soft references before running out of memory):
```
attempted to store: 10000
entries still present (not yet reclaimed): 683
no OutOfMemoryError -- the JVM cleared some/all soft references under pressure instead
```

The real-world concern added: with the exact same heap cap and the exact same total data volume as Level 1, wrapping cached values in `SoftReference` lets the JVM proactively clear entries under memory pressure — trading cache hit rate for program stability, avoiding the crash entirely, which is precisely the tradeoff soft references are designed for.

### Level 3 — Advanced

```java
import java.lang.ref.*;

public class WeakAndPhantomTogether {
    public static void main(String[] args) throws InterruptedException {
        ReferenceQueue<byte[]> phantomQueue = new ReferenceQueue<>();

        WeakReference<byte[]> weakRef;
        PhantomReference<byte[]> phantomRef;

        {
            byte[] data = new byte[1_000_000];
            weakRef = new WeakReference<>(data); // for DIAGNOSTIC observation
            phantomRef = new PhantomReference<>(data, phantomQueue); // for GUARANTEED cleanup notification
            System.out.println("phantomRef.get() (always null, by design): " + phantomRef.get());
        } // `data`'s only strong reference goes out of scope here

        System.gc();
        Thread.sleep(300);

        System.out.println("weakRef.get() after GC: " + weakRef.get() + " (null -- weak refs clear immediately)");

        // Poll the phantom reference queue -- this is how you're NOTIFIED the object
        // has been finalized and is genuinely about to be reclaimed.
        Reference<? extends byte[]> enqueued = phantomQueue.poll();
        System.out.println("phantom reference was enqueued (cleanup notification received)? " + (enqueued == phantomRef));
    }
}
```

**How to run:** `java WeakAndPhantomTogether.java` (JDK 17+).

Expected output:
```
phantomRef.get() (always null, by design): null
weakRef.get() after GC: null (null -- weak refs clear immediately)
phantom reference was enqueued (cleanup notification received)? true
```

This adds the production-flavored hard case: using both a `WeakReference` (purely to observe collectibility, as used diagnostically throughout this course) and a `PhantomReference` (specifically to receive a reliable notification, via `phantomQueue`, exactly when the object has been finalized and is about to be reclaimed) around the *same* underlying object — demonstrating each reference type's distinct role: `phantomRef.get()` never gives you the object back (by design — phantom references exist purely for the notification, not for continued access), while `phantomQueue.poll()` reliably tells you the reclamation moment has arrived, a guarantee weak references alone don't provide (a cleared weak reference tells you the object is gone, but not precisely when, nor does it integrate with a queue-based notification workflow the way phantom references do).

## 6. Walkthrough

Tracing the reference-clearing sequence in `WeakAndPhantomTogether.main`:

1. Inside the block, `data` is created and is the only strong reference to this particular `byte[1_000_000]` — `weakRef` and `phantomRef` are both constructed pointing to the same object, but neither is a strong reference, so neither by itself prevents collection.
2. `phantomRef.get()` is called and, as guaranteed by `PhantomReference`'s contract, always returns `null` — phantom references are deliberately designed to never let you retrieve the referent, only to be notified about its eventual reclamation.
3. Once the block ends, `data`'s scope ends too — since `weakRef` and `phantomRef` don't count as strong references, and nothing else references this object, it becomes eligible for garbage collection.
4. `System.gc()` triggers a collection cycle. The collector determines the object is unreachable; `weakRef` is cleared essentially immediately as part of this same collection cycle (weak references are always cleared at the very next GC once nothing strong references their referent) — so `weakRef.get()` correctly returns `null` right after.
5. The phantom reference behaves differently: rather than simply being cleared, `phantomRef` is placed onto `phantomQueue` — this happens only *after* the object has already been finalized (if it had a finalizer; in modern Java code without `finalize()` overrides, this happens essentially concurrently with the same collection) and is genuinely, definitively about to have its memory reclaimed.
6. `phantomQueue.poll()` retrieves that enqueued reference — confirming `enqueued == phantomRef` demonstrates that the notification mechanism worked exactly as designed: `main` now has a reliable, queue-based signal that this specific object has completed its lifecycle and is about to be freed, which it could use to trigger some corresponding cleanup action (releasing an associated native resource, for instance) with confidence that the timing is correct.

## 7. Gotchas & takeaways

> **Gotcha:** the JVM specification gives collectors considerable latitude in exactly *when* soft references are cleared under memory pressure — different JVM implementations and versions may behave somewhat differently in exactly how aggressively they hold onto soft-referenced data before clearing it; never assume a precise, guaranteed timing for soft-reference clearing, only that it's guaranteed to happen *before* an `OutOfMemoryError` would otherwise occur.

- Strong references unconditionally prevent collection; soft references are cleared only under genuine memory pressure (ideal for memory-sensitive caches); weak references are cleared at the very next GC cycle regardless of memory pressure (ideal for non-owning tracking references); phantom references never permit retrieval at all and exist purely to provide guaranteed post-finalization cleanup notification via a `ReferenceQueue`.
- `SoftReference`-backed caches trade cache hit rate for program stability under memory pressure — a meaningfully different risk profile than an ordinary, strongly-referenced cache, which can grow unboundedly until it crashes the program.
- `WeakReference` is the standard tool for observing an object's collectibility (as used throughout this course's examples) and for building non-owning associative structures like `WeakHashMap`.
- `PhantomReference`, combined with a `ReferenceQueue`, is the modern, structured, reliable replacement for the deprecated `finalize()` mechanism when guaranteed post-collection cleanup notification is genuinely needed.
- See [reachability & GC roots](0926-reachability-gc-roots.md) for the underlying reachability concept these reference types all modify the strength of, and [class unloading](0910-class-unloading.md) for a related scenario (an entire class loader graph becoming collectible) where these same reference-strength distinctions are frequently applied in practice.
