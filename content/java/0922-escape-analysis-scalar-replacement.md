---
card: java
gi: 922
slug: escape-analysis-scalar-replacement
title: Escape analysis & scalar replacement
---

## 1. What it is

Escape analysis is a JIT compiler technique that determines whether an object created inside a method could possibly be referenced ("escape") outside that method — returned to a caller, stored into a field of another object, passed to another thread, or captured by something that outlives the current call. If the compiler can prove an object *never* escapes (it's used only locally and then discarded), it becomes eligible for **scalar replacement**: instead of actually allocating the object on the [heap](0911-heap.md) at all, the compiler decomposes it into its individual primitive fields, which can then live directly in CPU registers or on the [stack](0913-jvm-stacks-stack-frames.md), exactly like ordinary local variables — completely eliminating both the allocation cost and any later garbage collection cost for that object, since it never actually existed as a heap object in the first place.

## 2. Why & when

This optimization matters enormously for code that creates small, short-lived, purely-local helper objects inside hot loops — a common and idiomatic Java pattern (a temporary `Point`, a small immutable value-holder, an iterator) that, without escape analysis, would otherwise generate real allocation pressure and garbage collection work proportional to how many times the hot loop runs. With scalar replacement, that entire cost can vanish: the object's fields simply become register/stack values, with the same runtime behavior as if you had manually "inlined" the object's fields into separate local variables yourself — except you get to keep the clean, encapsulated object-oriented code, and the compiler does the flattening automatically once it's confident the object genuinely stays local. Understanding this explains why modern Java performance advice increasingly says "don't manually avoid small object creation for performance reasons in hot loops" — the JIT compiler, once warmed up, frequently eliminates that cost entirely on its own, provided the object's usage pattern actually satisfies the non-escaping requirement escape analysis needs.

## 3. Core concept

```java
long sumOfSquaredDistances(int[] xs, int[] ys) {
    long total = 0;
    for (int i = 0; i < xs.length - 1; i++) {
        Point p = new Point(xs[i] - xs[i + 1], ys[i] - ys[i + 1]); // created, used, discarded -- NEVER escapes
        total += p.magnitudeSquared(); // p's fields consumed here, then p is never touched again
    }
    return total;
}
// Once the JIT confirms `p` never escapes this loop iteration (never returned, never stored
// anywhere else, never passed to another thread), it can scalar-replace it entirely --
// `p.x` and `p.y` become plain register/stack values, with ZERO actual heap allocation.
```

The source code still looks like ordinary object creation — the elimination happens invisibly, at the machine-code level, once the compiler proves it's safe.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without escape analysis, a temporary object is fully heap-allocated each loop iteration; with escape analysis proving it never escapes, its fields are scalar-replaced into register values with no heap allocation at all">
  <text x="160" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Without escape analysis</text>
  <rect x="30" y="35" width="240" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="150" y="57" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">new Point(...) -- HEAP allocation, every iteration</text>
  <text x="150" y="90" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">later: garbage collected</text>

  <text x="480" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">With escape analysis + scalar replacement</text>
  <rect x="360" y="35" width="260" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="490" y="57" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">x, y become plain register/stack values</text>
  <text x="490" y="90" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">NO heap allocation, NO GC work, at all</text>
</svg>

*Proving an object never escapes lets the compiler skip heap allocation entirely, decomposing it into plain scalar values instead.*

## 5. Runnable example

Scenario: measuring the real garbage-collection impact of a hot loop's temporary objects, growing from a baseline showing allocation cost when escape analysis can't apply (object genuinely escapes), to the same computation restructured so the temporary object provably never escapes, to directly observing GC activity difference via runtime statistics.

### Level 1 — Basic

```java
import java.util.*;

public class ObjectGenuinelyEscapes {
    static class Point {
        final int x, y;
        Point(int x, int y) { this.x = x; this.y = y; }
        long magnitudeSquared() { return (long) x * x + (long) y * y; }
    }

    static List<Point> collected = new ArrayList<>(); // KEEPS every Point reachable -- genuine escape

    static long sumWithEscaping(int[] xs, int[] ys) {
        long total = 0;
        for (int i = 0; i < xs.length - 1; i++) {
            Point p = new Point(xs[i] - xs[i + 1], ys[i] - ys[i + 1]);
            collected.add(p); // ESCAPES: stored somewhere that outlives this loop iteration
            total += p.magnitudeSquared();
        }
        return total;
    }

    public static void main(String[] args) {
        int[] xs = new int[1000], ys = new int[1000];
        for (int i = 0; i < xs.length; i++) { xs[i] = i; ys[i] = i * 2; }

        long start = System.nanoTime();
        long total = 0;
        for (int iter = 0; iter < 10_000; iter++) {
            collected.clear(); // reset each outer iteration, but STILL genuinely escapes within each inner pass
            total += sumWithEscaping(xs, ys);
        }
        System.out.println("total=" + total + ", elapsed=" + (System.nanoTime() - start) / 1_000_000 + "ms");
        System.out.println("(every Point object here GENUINELY escapes -- escape analysis CANNOT eliminate it)");
    }
}
```

**How to run:** `java ObjectGenuinelyEscapes.java` (JDK 17+).

Expected output shape:
```
total=..., elapsed=145ms
(every Point object here GENUINELY escapes -- escape analysis CANNOT eliminate it)
```

Because every `Point` is stored into `collected` (a field that outlives the loop iteration creating it), escape analysis cannot prove it stays local — every single `Point` really is allocated on the heap, and later genuinely collected by the garbage collector, incurring real allocation and collection cost.

### Level 2 — Intermediate

```java
public class ObjectNeverEscapes {
    static class Point {
        final int x, y;
        Point(int x, int y) { this.x = x; this.y = y; }
        long magnitudeSquared() { return (long) x * x + (long) y * y; }
    }

    static long sumWithoutEscaping(int[] xs, int[] ys) {
        long total = 0;
        for (int i = 0; i < xs.length - 1; i++) {
            Point p = new Point(xs[i] - xs[i + 1], ys[i] - ys[i + 1]); // used, then DISCARDED -- never escapes
            total += p.magnitudeSquared();
        }
        return total;
    }

    public static void main(String[] args) {
        int[] xs = new int[1000], ys = new int[1000];
        for (int i = 0; i < xs.length; i++) { xs[i] = i; ys[i] = i * 2; }

        long start = System.nanoTime();
        long total = 0;
        for (int iter = 0; iter < 10_000; iter++) {
            total += sumWithoutEscaping(xs, ys);
        }
        System.out.println("total=" + total + ", elapsed=" + (System.nanoTime() - start) / 1_000_000 + "ms (typically much faster)");
        System.out.println("(each Point here provably NEVER escapes -- likely scalar-replaced, no real allocation)");
    }
}
```

**How to run:** `java ObjectNeverEscapes.java` (JDK 17+).

Expected output shape (typically noticeably faster than Level 1's genuinely-escaping version):
```
total=..., elapsed=38ms (typically much faster)
(each Point here provably NEVER escapes -- likely scalar-replaced, no real allocation)
```

The real-world concern added: identical logical computation, but `p` is now used only within the same loop iteration that creates it and never stored anywhere that outlives that iteration — once hot, the JIT compiler can prove this and apply scalar replacement, eliminating the heap allocation entirely; the measured speedup directly reflects both the avoided allocation cost and the avoided later garbage-collection cost for what would otherwise have been millions of small, short-lived objects.

### Level 3 — Advanced

```java
import java.lang.management.*;

public class MeasuringGcActivityDifference {
    static class Point {
        final int x, y;
        Point(int x, int y) { this.x = x; this.y = y; }
        long magnitudeSquared() { return (long) x * x + (long) y * y; }
    }

    static long sumWithoutEscaping(int[] xs, int[] ys) {
        long total = 0;
        for (int i = 0; i < xs.length - 1; i++) {
            Point p = new Point(xs[i] - xs[i + 1], ys[i] - ys[i + 1]);
            total += p.magnitudeSquared();
        }
        return total;
    }

    public static void main(String[] args) {
        int[] xs = new int[1000], ys = new int[1000];
        for (int i = 0; i < xs.length; i++) { xs[i] = i; ys[i] = i * 2; }

        // Warm up first, so the JIT has a real chance to apply scalar replacement
        // BEFORE we start measuring GC activity for the "real" timed portion.
        for (int i = 0; i < 5000; i++) sumWithoutEscaping(xs, ys);

        long gcCountBefore = totalGcCollections();
        long start = System.nanoTime();
        long total = 0;
        for (int iter = 0; iter < 50_000; iter++) total += sumWithoutEscaping(xs, ys);
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        long gcCountAfter = totalGcCollections();

        System.out.println("total=" + total + ", elapsed=" + elapsedMs + "ms");
        System.out.println("GC collections during this measured run: " + (gcCountAfter - gcCountBefore));
        System.out.println("(a LOW or ZERO count here, despite ~50 BILLION logical Point 'creations',");
        System.out.println(" is strong evidence scalar replacement eliminated the real allocations)");
    }

    static long totalGcCollections() {
        long total = 0;
        for (GarbageCollectorMXBean bean : ManagementFactory.getGarbageCollectorMXBeans()) {
            total += bean.getCollectionCount();
        }
        return total;
    }
}
```

**How to run:** `java MeasuringGcActivityDifference.java` (JDK 17+).

Expected output shape (a low GC collection count despite the enormous logical object-creation count is the key signal):
```
total=..., elapsed=180ms
GC collections during this measured run: 0
(a LOW or ZERO count here, despite ~50 BILLION logical Point 'creations',
 is strong evidence scalar replacement eliminated the real allocations)
```

This adds the production-flavored hard case: directly measuring actual garbage collection activity (via `GarbageCollectorMXBean`) across a run that logically creates roughly 50 billion `Point` objects (50,000 outer iterations × 999 inner iterations each) — if these were all genuinely heap-allocated, this would produce an enormous amount of garbage collection work; observing zero (or very few) collections during the measured window is strong, direct evidence that scalar replacement really did eliminate the actual heap allocations for this provably-non-escaping object, not just a theoretical claim about what the JIT compiler *might* do.

## 6. Walkthrough

Reasoning through why GC activity stays low in `MeasuringGcActivityDifference.main`:

1. The initial warm-up loop (5000 iterations of `sumWithoutEscaping`) exists specifically to give the JIT compiler enough invocations to identify this method as hot and apply its full suite of optimizations, including escape analysis, *before* the actual timed-and-measured portion begins — without this warm-up, the measured run would include some genuinely interpreted or partially-optimized execution, muddying the GC-activity signal.
2. During compilation, C2's escape analysis examines `p`'s usage within `sumWithoutEscaping`: `p` is created, `p.magnitudeSquared()` is called on it, and then the loop moves to its next iteration — `p` is never returned from the method, never stored into any field, never passed to another method that might retain it, and never referenced by another thread. This satisfies the conditions for provably non-escaping.
3. With that proof established, the compiler applies scalar replacement: rather than emitting code that actually allocates a `Point` object on the heap (with its object header, its `x` and `y` fields laid out in memory), it instead treats `x` and `y` as if they were two separate, ordinary local variables — computed, used by the inlined body of `magnitudeSquared()` (itself likely inlined too, per [method inlining](0921-method-inlining.md)), and then simply discarded, with no object ever actually existing in memory.
4. Because no real heap allocation occurs for any of the roughly 50 billion logical `Point` "creations" across the measured loop, there's essentially no corresponding garbage for the collector to ever need to reclaim — hence the near-zero (often exactly zero) GC collection count observed, despite the enormous logical object-creation volume the source code appears to describe.
5. This is a direct, measured confirmation that scalar replacement isn't just a theoretical optimization described in JIT compiler literature — it has a concrete, observable effect (the near-total absence of GC activity that the same code, without this optimization, would otherwise clearly require) for code written in the ordinary, idiomatic, object-oriented style this example uses.

## 7. Gotchas & takeaways

> **Gotcha:** escape analysis is a best-effort, JIT-implementation-dependent optimization — it is never a language guarantee, and whether it actually applies to any specific piece of code can depend on subtle details of how that object is used, how large/complex the enclosing method is, and the specific JVM version in use. Never *rely* on scalar replacement happening for correctness or for a hard performance requirement; treat it as a valuable, frequently-occurring optimization for well-structured code, not a contract.

- Escape analysis determines whether an object created in a method can be proven to never escape that method's local scope; scalar replacement then decomposes such objects into individual primitive values, eliminating heap allocation entirely.
- This is exactly why creating small, purely-local helper objects inside hot loops is frequently free in practice, once the JIT compiler has warmed up and applied this optimization — a significant relaxation of older, pre-JIT-era intuitions about avoiding object creation for performance.
- An object that is returned, stored into a longer-lived field, passed to another thread, or otherwise made reachable beyond its creating method's local scope genuinely escapes and cannot be scalar-replaced — it will be allocated on the heap as usual.
- `GarbageCollectorMXBean`'s collection-count statistics are a useful, direct way to observe whether scalar replacement is actually occurring for a specific piece of code, rather than reasoning about it purely theoretically.
- See [method inlining](0921-method-inlining.md) (escape analysis frequently depends on inlining having already merged caller and callee code together, giving the optimizer a large enough unit of code to analyze an object's full usage within) and [deoptimization](0924-deoptimization.md) (the safety mechanism that lets the JIT compiler safely undo speculative optimizations, including this one, if an assumption it made turns out to be wrong later).
