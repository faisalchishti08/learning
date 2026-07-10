---
card: java
gi: 940
slug: heap-dumps-analysis
title: Heap dumps & analysis
---

## 1. What it is

A heap dump is a complete, point-in-time snapshot of every object on the JVM heap — every instance, its field values, and every reference between objects — written out to a binary `.hprof` file. It can be triggered manually (`jcmd <pid> GC.heap_dump dump.hprof`, or the older `jmap -dump:file=dump.hprof <pid>`), taken automatically on an out-of-memory failure (`-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/path`), or captured programmatically. Once captured, a heap dump is analyzed with a tool such as Eclipse Memory Analyzer (MAT), VisualVM, or JDK Mission Control — these tools load the dump and let you query it: which objects consume the most retained memory, what is the shortest path from any given object back to a GC root (the reference chain keeping it alive), and which class has the most live instances. This is the primary practical tool for diagnosing exactly the kind of [logical memory leak](0938-memory-leaks-in-managed-memory.md) discussed earlier — turning "heap usage keeps growing" into "this specific static field is holding this specific collection, which is holding these specific stale entries."

## 2. Why & when

Heap dump analysis becomes necessary once you've confirmed — via GC logs or monitoring — that heap usage is trending upward over time (a real leak, not just normal fluctuation), but you don't yet know *which* object graph is responsible; without a heap dump, you're limited to guessing based on code review, while a heap dump gives you ground truth from the actual running process. The standard workflow is to capture two dumps some time apart under representative load (or one dump right before an `OutOfMemoryError`, via `-XX:+HeapDumpOnOutOfMemoryError`), then use a tool's comparison or "dominator tree" view to find which classes' retained-size grew the most between the two snapshots — the dominator tree is particularly useful because it shows *retained* size (an object plus everything only reachable through it) rather than just *shallow* size (the object's own fields), which is what actually matters for finding what's keeping large amounts of memory alive. It is generally not something to reach for casually in a routine debugging session — capturing a full heap dump on a large heap can itself pause the application for a nontrivial time and produces a large file — but it is exactly the right tool once a genuine, otherwise-unexplained memory-growth problem has been identified.

## 3. Core concept

```
Heap dump analysis workflow:

1. Capture:   jcmd <pid> GC.heap_dump dump1.hprof   (or on OOM: -XX:+HeapDumpOnOutOfMemoryError)
2. Wait/load  (let the suspected leak grow further)
3. Capture:   jcmd <pid> GC.heap_dump dump2.hprof
4. Load both dumps in MAT / VisualVM / JMC
5. Compare "dominator tree" between dump1 and dump2:
     - which class's RETAINED size grew the most?
     - "Path to GC Roots" on a sample instance of that class
       -> reveals the EXACT reference chain keeping it alive
6. Fix: break/bound that specific reference chain in the code
```

The dominator tree's "retained size" (an object plus everything exclusively reachable through it) is the key metric — a small object that's the sole gateway to a huge subgraph can show a tiny shallow size but an enormous retained size, and that's exactly the object worth investigating.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A dominator tree showing a small cache object with a large retained size because it is the sole path keeping a huge collection of stale entries reachable">
  <rect x="20" y="70" width="120" height="40" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="94" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">GC Root</text>

  <rect x="200" y="70" width="140" height="40" fill="#1c2430" stroke="#f0883e"/>
  <text x="270" y="88" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">static cache field</text>
  <text x="270" y="102" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">shallow: 32 bytes</text>

  <rect x="420" y="20" width="180" height="140" fill="none" stroke="#8b949e" stroke-dasharray="3"/>
  <text x="510" y="35" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">everything ONLY reachable</text>
  <text x="510" y="48" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">through the cache field</text>
  <rect x="440" y="60" width="60" height="25" fill="#1c2430" stroke="#8b949e"/>
  <rect x="510" y="60" width="60" height="25" fill="#1c2430" stroke="#8b949e"/>
  <rect x="440" y="95" width="60" height="25" fill="#1c2430" stroke="#8b949e"/>
  <rect x="510" y="95" width="60" height="25" fill="#1c2430" stroke="#8b949e"/>
  <text x="510" y="150" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">retained size: 400MB</text>

  <line x1="140" y1="90" x2="200" y2="90" stroke="#79c0ff" marker-end="url(#a)"/>
  <line x1="340" y1="90" x2="420" y2="90" stroke="#f0883e" marker-end="url(#a)"/>
</svg>

*A tiny object can have an enormous retained size if it is the sole gateway keeping a large subgraph reachable — exactly what the dominator tree view surfaces.*

## 5. Runnable example

Scenario: produce and then diagnose a genuine leak using real heap-dump tooling — starting with a basic leaking program instrumented to make dumping convenient, then capturing and comparing two dumps to identify the growing class, then using "path to GC roots" to pinpoint the exact reference chain and confirm the fix.

### Level 1 — Basic

```java
import java.util.*;

public class HeapDumpTarget {
    static final Map<String, byte[]> leak = new HashMap<>();

    public static void main(String[] args) throws Exception {
        System.out.println("PID: " + ProcessHandle.current().pid());
        for (int round = 0; round < 100; round++) {
            for (int i = 0; i < 5_000; i++) {
                leak.put("k-" + round + "-" + i, new byte[1000]);
            }
            System.out.println("round " + round + ", leak.size()=" + leak.size());
            Thread.sleep(500); // pause between rounds so you have time to attach jcmd
        }
    }
}
```

**How to run:** `java HeapDumpTarget.java` (JDK 17+), then in a second terminal, note the printed PID and run `jcmd <PID> GC.heap_dump dump1.hprof` a few rounds in, then again later as `dump2.hprof`.

Expected output shape (first terminal):
```
PID: 41823
round 0, leak.size()=5000
round 1, leak.size()=10000
...
```

This just establishes a live, running, deliberately-leaking target process with a stable PID you can attach to — the actual analysis happens externally, against the `.hprof` files it produces.

### Level 2 — Intermediate

```java
import java.util.*;

public class HeapDumpTargetWithHint {
    static final Map<String, byte[]> leak = new HashMap<>();
    static final List<Object> decoyShortLived = new ArrayList<>(); // to show a NON-growing class too

    public static void main(String[] args) throws Exception {
        System.out.println("PID: " + ProcessHandle.current().pid());
        for (int round = 0; round < 100; round++) {
            for (int i = 0; i < 5_000; i++) {
                leak.put("k-" + round + "-" + i, new byte[1000]);
            }
            decoyShortLived.clear(); // this one does NOT grow -- for comparison in the dumps
            decoyShortLived.add(new int[10]);
            System.out.println("round " + round + ", leak.size()=" + leak.size());
            Thread.sleep(500);
        }
    }
}
```

**How to run:** same as Level 1 — `java HeapDumpTargetWithHint.java`, capturing `dump1.hprof` around round 10 and `dump2.hprof` around round 60, via `jcmd <PID> GC.heap_dump <file>`.

Expected outcome when both dumps are opened in MAT (or VisualVM) and compared:
```
Histogram/dominator comparison:
  byte[]           -- shallow count grew from ~50,000 to ~300,000 instances  (the leak)
  int[]            -- stays at 1 instance in decoyShortLived               (not the leak)
```

The real-world concern added: a real analysis session always involves more than one candidate class — `decoyShortLived` deliberately behaves like a normal, correctly-bounded collection (cleared every round) so that comparing the two dumps' histograms makes the actual leaking class (`byte[]`, retained via `leak`) stand out clearly against a class that is *not* growing, exactly as a real leak investigation would need to distinguish signal from noise.

### Level 3 — Advanced

```java
import java.util.*;

public class HeapDumpTargetForRootPathAnalysis {
    static final Map<String, List<byte[]>> leak = new HashMap<>();

    public static void main(String[] args) throws Exception {
        System.out.println("PID: " + ProcessHandle.current().pid());
        for (int round = 0; round < 200; round++) {
            List<byte[]> bucket = leak.computeIfAbsent("bucket-" + (round % 20), k -> new ArrayList<>());
            for (int i = 0; i < 2_000; i++) {
                bucket.add(new byte[1000]); // nested inside a List, inside a Map -- a realistic multi-level chain
            }
            System.out.println("round " + round + ", buckets=" + leak.size());
            Thread.sleep(300);
        }
    }
}
```

**How to run:** `java -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/tmp -Xmx256m HeapDumpTargetForRootPathAnalysis.java` (JDK 17+; deliberately small `-Xmx` so the program eventually throws `OutOfMemoryError` and automatically dumps to `/tmp` without needing manual `jcmd` timing).

Expected outcome (after the automatic dump is produced and opened in MAT):
```
Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
Dumping heap to /tmp/java_pid41900.hprof ...
Heap dump file created

In MAT: "Path to GC Roots" on the largest byte[] instance shows:
  byte[] <- ArrayList <- HashMap$Node <- HashMap "leak" (static field) <- Class HeapDumpTargetForRootPathAnalysis <- GC Root (class loader)
```

The production-flavored hard case: `-XX:+HeapDumpOnOutOfMemoryError` captures the dump automatically at the exact moment of failure, with no manual timing needed, and the "Path to GC Roots" view exposes the *full, multi-level* reference chain — object, inside a `List`, inside a `Map`, referenced by a static field, referenced by the class itself — which is precisely the kind of nested chain a real production leak (a per-key bucketed cache, for instance) actually produces, and precisely what the tool is for: turning a single suspicious instance into the exact code location responsible.

## 6. Walkthrough

Tracing the diagnostic process using `HeapDumpTargetForRootPathAnalysis` end to end:

1. The program starts and prints its PID, then begins its main loop, allocating twenty rotating "buckets" (one `ArrayList<byte[]>` per bucket key) inside the static `leak` map — every allocated `byte[1000]` is added to whichever bucket the current round maps to, and since neither the buckets nor the map are ever cleared, every single array allocated across the entire run remains reachable.
2. As rounds proceed and the `-Xmx256m` cap approaches, GC pauses become more frequent and reclaim less and less memory each time, since an ever-larger fraction of the heap is now genuinely live (reachable via `leak`) rather than garbage — this is the same observable symptom discussed in [memory leaks in managed memory](0938-memory-leaks-in-managed-memory.md), here driven all the way to failure.
3. Eventually, an allocation attempt fails outright: the JVM throws `OutOfMemoryError: Java heap space`, and because `-XX:+HeapDumpOnOutOfMemoryError` was set, it automatically writes a complete heap snapshot to the configured path *before* the process exits — capturing the exact state that led to the failure, with no need to have manually timed a `jcmd` call.
4. Loading that dump into MAT and viewing the dominator tree (or a simple class histogram) immediately surfaces `byte[]` as the class with by far the largest total retained size — far larger than any other class in the dump, which narrows the investigation from "the whole heap" to "one specific class" in a single step.
5. Selecting a representative `byte[]` instance and choosing "Path to GC Roots" walks backward through the exact reference chain keeping it alive: the array is held by an `ArrayList` (one of the twenty buckets), which is held as a value in a `HashMap$Node`, which is part of the static `leak` field on the `HeapDumpTargetForRootPathAnalysis` class, which is itself reachable from a GC root (the class loader that loaded this class, which is always reachable while the class remains loaded).
6. This chain is the complete answer to "why is this object still alive?" — and it points directly at the specific code responsible: the static `leak` field with no eviction policy — confirming that the fix is exactly the same kind discussed for [memory leaks](0938-memory-leaks-in-managed-memory.md): bound the map's size, add a TTL, or otherwise ensure old buckets are removed, none of which requires touching GC configuration at all.

## 7. Gotchas & takeaways

> **Gotcha:** taking a heap dump on a large, actively-used heap can itself cause a significant pause (heap dumping typically needs to walk the entire live object graph, often during a stop-the-world-like phase) — capturing dumps casually and frequently on a production system under load can itself become a performance problem; prefer taking them sparingly, ideally around a suspected leak's growth window, or automatically and only on actual failure via `-XX:+HeapDumpOnOutOfMemoryError`.

- A heap dump is a complete snapshot of every live object, its fields, and every reference between objects, captured to a `.hprof` file via `jcmd ... GC.heap_dump`, `jmap`, or automatically on OOM via `-XX:+HeapDumpOnOutOfMemoryError`.
- Analysis tools (Eclipse MAT, VisualVM, JDK Mission Control) let you compare two dumps' histograms to find which class's instance count or retained size grew the most over time — the direct signal of a real leak.
- The dominator tree's "retained size" (not shallow size) is the key metric: a small object can retain an enormous subgraph if it's the sole gateway to it.
- "Path to GC Roots" on a specific instance reveals the exact, concrete reference chain keeping it alive, translating a suspicious object directly into the specific field or collection in the code responsible.
- Capturing dumps on a large production heap has real performance cost — prefer targeted, infrequent captures (or automatic on-failure capture) over routine, frequent dumping.
- See [memory leaks in managed memory](0938-memory-leaks-in-managed-memory.md) for the conceptual background this tooling is used to diagnose, and [stop-the-world pauses](0936-stop-the-world-pauses.md) for why capturing a dump itself can briefly affect a running application.
