---
card: java
gi: 894
slug: atomicfieldupdater
title: AtomicFieldUpdater
---

## 1. What it is

`AtomicIntegerFieldUpdater<T>`, `AtomicLongFieldUpdater<T>`, and `AtomicReferenceFieldUpdater<T,V>` let you perform atomic CAS-based updates on a **plain `volatile` field** of an existing class, without needing to change that field's declared type to `AtomicInteger`/`AtomicLong`/`AtomicReference`. You obtain an updater once (typically as a `static final` field) via a reflective-lookup factory method, specifying the target class and field name, and then use it to atomically read/update that field on any instance of that class — the field itself stays a plain `volatile int`/`long`/reference type in the class's own source.

## 2. Why & when

The primary reason to reach for a field updater instead of just declaring the field as `AtomicInteger` directly is memory footprint at scale: an `AtomicInteger` field is itself an object, meaning every instance of your class pays for an extra object header and reference on top of the actual `int` value it wraps. When you have a very large number of instances of a class — millions of nodes in some in-memory structure, for example — and only occasionally need atomic updates to one particular field, an `AtomicXxxFieldUpdater` lets the field remain a plain primitive (`volatile int`, cheap, no extra object), while still supporting atomic operations through a single, shared updater object referenced by the class (not duplicated per instance). This is a narrow, memory-optimization-focused tool — for the overwhelming majority of code, a direct `AtomicInteger`/`AtomicLong`/`AtomicReference` field is simpler and the memory difference is irrelevant; reach for a field updater specifically when profiling shows the per-instance overhead of wrapper objects actually matters.

## 3. Core concept

```java
class Node {
    volatile int refCount; // plain volatile field -- NOT an AtomicInteger, saves per-instance object overhead

    static final AtomicIntegerFieldUpdater<Node> REF_COUNT_UPDATER =
        AtomicIntegerFieldUpdater.newUpdater(Node.class, "refCount"); // ONE shared updater for the whole class
}

Node node = new Node();
Node.REF_COUNT_UPDATER.incrementAndGet(node); // atomic update on THIS instance's refCount field
```

The updater object is created once (typically `static final`) and reused for every instance of the class — the atomicity machinery is shared, while each instance only pays for a plain primitive field.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A million Node instances each with a plain volatile int field, versus one shared static AtomicIntegerFieldUpdater used to atomically update any of them, contrasted with each instance instead holding its own AtomicInteger object">
  <text x="160" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">With AtomicInteger field: EACH instance has an extra object</text>
  <rect x="20" y="30" width="80" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="60" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Node A</text>
  <rect x="110" y="30" width="90" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3"/>
  <text x="155" y="50" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">+AtomicInteger obj</text>

  <text x="480" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">With FieldUpdater: plain field, ONE shared updater</text>
  <rect x="380" y="30" width="80" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="420" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Node A</text>
  <rect x="470" y="30" width="80" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="510" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Node B</text>
  <rect x="380" y="90" width="170" height="35" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="465" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ONE static shared updater</text>
  <line x1="420" y1="60" x2="440" y2="88" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a27)"/>
  <line x1="510" y1="60" x2="490" y2="88" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a27)"/>
  <defs><marker id="a27" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Each `AtomicInteger` field costs an extra object per instance; a `FieldUpdater` is shared across all instances, leaving each instance's field a cheap primitive.*

## 5. Runnable example

Scenario: a large graph of reference-counted nodes, growing from a plain (non-atomic, buggy) `volatile` field, to a per-instance `AtomicInteger` field, to a shared `AtomicIntegerFieldUpdater` demonstrating the memory-saving pattern at scale.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class PlainVolatileFieldBug {
    static class Node {
        volatile int refCount = 0;
        void incrementRefCount() {
            refCount++; // NOT atomic -- volatile only guarantees visibility, not atomicity of ++
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Node node = new Node();
        ExecutorService pool = Executors.newFixedThreadPool(8);
        for (int i = 0; i < 10_000; i++) {
            pool.submit(node::incrementRefCount);
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("refCount = " + node.refCount + " (expected 10000, likely LESS due to lost updates)");
    }
}
```

**How to run:** `java PlainVolatileFieldBug.java` (JDK 17+).

Expected output shape (undercounts, as with any `volatile int` incremented by `++`):
```
refCount = 8734 (expected 10000, likely LESS due to lost updates)
```

Exactly the classic `volatile` pitfall — visibility is guaranteed, but `refCount++` is still a non-atomic read-modify-write, so concurrent increments race and lose updates.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class PerInstanceAtomicInteger {
    static class Node {
        AtomicInteger refCount = new AtomicInteger(0); // an extra OBJECT per instance
        void incrementRefCount() {
            refCount.incrementAndGet(); // genuinely atomic
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Node node = new Node();
        ExecutorService pool = Executors.newFixedThreadPool(8);
        for (int i = 0; i < 10_000; i++) {
            pool.submit(node::incrementRefCount);
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        System.out.println("refCount = " + node.refCount.get() + " (correct: exactly 10000)");
        System.out.println("but every Node instance now carries its own extra AtomicInteger object");
    }
}
```

**How to run:** `java PerInstanceAtomicInteger.java`.

Expected output:
```
refCount = 10000 (correct: exactly 10000)
but every Node instance now carries its own extra AtomicInteger object
```

The real-world concern added: correctness is fixed via `AtomicInteger`, but at the cost of every single `Node` instance carrying its own separate `AtomicInteger` object — fine for a handful of nodes, but a real per-instance memory cost if you have millions of them.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class SharedFieldUpdater {
    static class Node {
        volatile int refCount = 0; // PLAIN primitive field -- no extra object per instance
    }

    // ONE updater, shared across every Node instance -- created once, referenced via the class + field name.
    static final AtomicIntegerFieldUpdater<Node> REF_COUNT_UPDATER =
        AtomicIntegerFieldUpdater.newUpdater(Node.class, "refCount");

    public static void main(String[] args) throws InterruptedException {
        // Simulate a large number of nodes -- each one only pays for a plain int field.
        Node[] nodes = new Node[3];
        for (int i = 0; i < nodes.length; i++) nodes[i] = new Node();

        ExecutorService pool = Executors.newFixedThreadPool(8);
        for (Node node : nodes) {
            for (int i = 0; i < 10_000; i++) {
                pool.submit(() -> REF_COUNT_UPDATER.incrementAndGet(node)); // atomic, via the SHARED updater
            }
        }
        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);

        for (int i = 0; i < nodes.length; i++) {
            System.out.println("node " + i + " refCount = " + nodes[i].refCount + " (expected 10000 each)");
        }
    }
}
```

**How to run:** `java SharedFieldUpdater.java`.

Expected output:
```
node 0 refCount = 10000 (expected 10000 each)
node 1 refCount = 10000 (expected 10000 each)
node 2 refCount = 10000 (expected 10000 each)
```

This adds the production-flavored hard case: three separate `Node` instances, each with a plain `volatile int refCount` field (no extra per-instance object), all correctly and atomically updated through the *same single* `REF_COUNT_UPDATER` object — demonstrating that one shared updater correctly manages atomic access to that named field across an arbitrary number of distinct instances, which is exactly the memory-saving pattern that matters when the instance count scales into the millions.

## 6. Walkthrough

Tracing `REF_COUNT_UPDATER.incrementAndGet(node)` for a specific `node`:

1. `AtomicIntegerFieldUpdater.newUpdater(Node.class, "refCount")` was called once at class-initialization time, using reflection to locate the `refCount` field on the `Node` class and verify it's accessible, `volatile`, and of type `int` — this lookup happens exactly once, regardless of how many `Node` instances later exist.
2. `REF_COUNT_UPDATER.incrementAndGet(node)` takes the specific `node` instance as an explicit argument — since the updater itself holds no per-instance state, it needs to be told *which* object's field to operate on for each call.
3. Internally, this performs the same CAS-retry-loop pattern as `AtomicInteger.incrementAndGet()` (see [CAS](0891-cas-compare-and-swap.md)) — but instead of operating on a dedicated `AtomicInteger` object's internal value, it operates directly on `node`'s `refCount` field via the reflective field-access mechanism set up during the updater's construction.
4. Because `refCount` is declared `volatile`, the field's visibility guarantees hold exactly as they would for any `volatile` field — combined with the updater's CAS logic, this gives the same atomicity and visibility guarantees as an `AtomicInteger` would, but without `node` needing to hold a reference to a separate `AtomicInteger` object at all.
5. This pattern repeats independently for each of the three `Node` instances in the example — the *same* `REF_COUNT_UPDATER` object is reused for `nodes[0]`, `nodes[1]`, and `nodes[2]`, correctly tracking each one's own `refCount` field completely independently, since the updater always operates on whatever specific instance is passed as its argument.
6. After all 30,000 total submitted increments (10,000 per node) complete, each node's `refCount` field correctly reflects exactly the number of increments that targeted it — confirming the shared updater correctly maintains per-instance atomicity despite being a single, class-level object.

## 7. Gotchas & takeaways

> **Gotcha:** the target field **must** be declared `volatile` and must be accessible to the code creating the updater (not `private` from an unrelated class, and never `static`) — `AtomicIntegerFieldUpdater.newUpdater` throws an exception at construction time if these requirements aren't met, since the updater relies on the field's `volatile` semantics for its visibility guarantees and needs reflective access to it.

- `AtomicXxxFieldUpdater` gives atomic CAS-based updates on a plain `volatile` field, without requiring the field's type to be `AtomicInteger`/`AtomicLong`/`AtomicReference` — trading a small amount of API awkwardness (passing the target instance explicitly to every call) for reduced per-instance memory overhead.
- Create the updater once, typically as a `static final` field on the class whose field it manages — one updater instance correctly serves atomic access for every instance of that class.
- This is a narrow, memory-optimization-focused tool: reach for it specifically when profiling shows that per-instance `AtomicInteger`/`AtomicLong`/`AtomicReference` wrapper objects meaningfully bloat memory at the scale your application actually operates at (e.g., millions of instances) — for ordinary code, a direct `Atomic*` field is simpler and the difference doesn't matter.
- The target field must be `volatile` and accessible; it cannot be `private` in a way that's inaccessible to the updater's creation context, and it cannot be `static`.
- The underlying atomicity mechanism (CAS-based, potentially retrying under contention) is identical to `AtomicInteger`/`AtomicLong`/`AtomicReference` — only the storage location (a plain field on an arbitrary instance versus a dedicated wrapper object) differs.
