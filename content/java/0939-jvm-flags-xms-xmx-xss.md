---
card: java
gi: 939
slug: jvm-flags-xms-xmx-xss
title: JVM flags (-Xms/-Xmx/-Xss)
---

## 1. What it is

`-Xms` and `-Xmx` set the initial and maximum size of the JVM's heap (the memory region holding all Java objects, managed by the garbage collector), while `-Xss` sets the size of each individual thread's stack (the memory region holding that thread's method call frames, local variables, and return addresses — one separate stack per thread, entirely outside the heap). `-Xms256m -Xmx2g` tells the JVM to start with a 256 MB heap and allow it to grow, as needed, up to 2 GB; `-Xss512k` gives every thread created in the JVM a 512 KB stack. These are among the most fundamental JVM sizing flags, and getting them meaningfully wrong produces two very different and very recognizable failure modes: too small a heap (relative to the application's genuine live-data volume) leads to `OutOfMemoryError: Java heap space`, while too small a stack (relative to how deep the application's call chains actually go — recursion depth being the classic culprit) leads to `StackOverflowError`.

## 2. Why & when

Setting `-Xms` equal to `-Xmx` (a common production practice) avoids the overhead of the JVM repeatedly resizing the heap at runtime as it grows from its initial size toward its maximum — each resize is itself a nontrivial operation, and for a long-running service that will eventually need close to its maximum heap anyway, paying that cost once at startup (by starting there directly) is usually preferable to paying it incrementally under load. Choosing `-Xmx` itself requires balancing the container or machine's total available memory (leaving headroom for thread stacks, the metaspace, JIT-compiled code, and native/off-heap memory — the heap is not the *only* memory a JVM process uses) against the application's actual live-data volume, ideally informed by a real [heap dump](0940-heap-dumps-analysis.md) rather than guesswork; setting it far too low forces the GC to run far more often than necessary just to keep up with allocation, while setting it far too high can leave a container without enough memory for the JVM's other regions, causing an OS-level OOM-kill rather than a clean, catchable `OutOfMemoryError`. `-Xss` matters less often, but becomes critical for any application with deep or unbounded recursion — the default (typically around 512 KB–1 MB depending on platform) is enough for ordinary call depths, but a recursive algorithm operating on a large or adversarial input can exceed it, at which point the fix is either to raise `-Xss` or, better, to eliminate the unbounded recursion (e.g., by converting it to an iterative form).

## 3. Core concept

```
JVM process memory (NOT all controlled by -Xmx!):

  [ Heap: -Xms (initial) ... -Xmx (max) ] <- objects, managed by GC
  [ Metaspace ]                          <- class metadata (see method-area-metaspace)
  [ Thread stacks: N threads x -Xss ]    <- one stack per thread, call frames + locals
  [ JIT-compiled native code, off-heap buffers, native libraries, etc. ]

Heap too small for live data  -> OutOfMemoryError: Java heap space
Stack too small for call depth -> StackOverflowError (per-thread, independent of heap size)

-Xms == -Xmx is common in production: avoids incremental resize overhead at runtime.
```

The heap and each thread's stack are entirely separate memory regions with entirely separate size limits and entirely separate failure modes — a deep-recursion bug will never be fixed by raising `-Xmx`, and a genuine heap-sizing problem will never be fixed by raising `-Xss`.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A JVM process's memory divided into the shared heap sized by Xms and Xmx, and separate per-thread stacks each sized by Xss" >
  <rect x="20" y="30" width="260" height="130" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="48" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Heap (shared, one region)</text>
  <text x="150" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">-Xms: initial size</text>
  <text x="150" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">-Xmx: maximum size (grows toward this)</text>
  <text x="150" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">All Java objects live here,</text>
  <text x="150" y="115" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">managed by the GC</text>
  <text x="150" y="140" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">too small -&gt; OutOfMemoryError</text>

  <rect x="320" y="30" width="90" height="50" fill="#1c2430" stroke="#79c0ff"/>
  <text x="365" y="49" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Thread A</text>
  <text x="365" y="64" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">stack: -Xss</text>

  <rect x="420" y="30" width="90" height="50" fill="#1c2430" stroke="#79c0ff"/>
  <text x="465" y="49" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Thread B</text>
  <text x="465" y="64" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">stack: -Xss</text>

  <rect x="520" y="30" width="90" height="50" fill="#1c2430" stroke="#79c0ff"/>
  <text x="565" y="49" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Thread N</text>
  <text x="565" y="64" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">stack: -Xss</text>

  <text x="465" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">EACH thread gets its OWN</text>
  <text x="465" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">separate stack of this size</text>
  <text x="465" y="145" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">too small -&gt; StackOverflowError</text>
</svg>

*The heap is one shared region sized by -Xms/-Xmx; each thread additionally gets its own independent stack sized by -Xss.*

## 5. Runnable example

Scenario: deliberately trigger and then fix both failure modes on the same conceptual program — starting with a basic heap-sizing demonstration, then a stack-depth demonstration showing the independent `-Xss` failure mode, then combining both concerns in one workload that needs both flags tuned correctly to run successfully.

### Level 1 — Basic

```java
import java.util.*;

public class HeapSizeDemo {
    public static void main(String[] args) {
        List<byte[]> retained = new ArrayList<>();
        try {
            for (int i = 0; i < 10_000; i++) {
                retained.add(new byte[100_000]); // ~1GB total if all 10,000 succeed
            }
            System.out.println("succeeded: retained " + retained.size() + " arrays");
        } catch (OutOfMemoryError e) {
            System.out.println("OutOfMemoryError after retaining " + retained.size() + " arrays");
        }
    }
}
```

**How to run first (too small):** `java -Xmx64m HeapSizeDemo.java` (JDK 17+) — expect `OutOfMemoryError after retaining ~600 arrays`.
**How to run second (fixed):** `java -Xmx2g HeapSizeDemo.java` — expect `succeeded: retained 10000 arrays`.

Expected output shape:
```
(with -Xmx64m):  OutOfMemoryError after retaining 624 arrays
(with -Xmx2g):   succeeded: retained 10000 arrays
```

With `-Xmx64m`, the heap simply cannot hold the roughly 1 GB of retained data this loop wants to accumulate, so it fails partway through; raising `-Xmx` to comfortably exceed the workload's genuine live-data volume is the direct, correct fix — no code change needed.

### Level 2 — Intermediate

```java
public class StackDepthDemo {
    static int countFrames(int depth) {
        try {
            return countFrames(depth + 1); // unbounded recursion, one stack frame per call
        } catch (StackOverflowError e) {
            System.out.println("StackOverflowError at approximate depth: " + depth);
            return depth;
        }
    }

    public static void main(String[] args) {
        countFrames(0);
    }
}
```

**How to run first (small stack):** `java -Xss228k StackDepthDemo.java` (JDK 17+) — expect a relatively shallow reported depth.
**How to run second (larger stack):** `java -Xss8m StackDepthDemo.java` — expect a much deeper reported depth before overflow.

Expected output shape:
```
(with -Xss228k): StackOverflowError at approximate depth: ~3200
(with -Xss8m):   StackOverflowError at approximate depth: ~115000
```

The real-world concern added: this demonstrates that `-Xss` (not `-Xmx`) is the relevant flag for recursion-depth problems, entirely independent of heap size — raising `-Xmx` would have no effect whatsoever on this failure, since each recursive call consumes stack space, not heap space, and the two are governed by completely separate flags.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.*;

public class CombinedSizingWorkload {
    static int recurse(int n) {
        if (n <= 0) return 0;
        return 1 + recurse(n - 1);
    }

    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(50);
        List<byte[]> retained = Collections.synchronizedList(new ArrayList<>());
        List<Future<Integer>> futures = new ArrayList<>();

        for (int i = 0; i < 50; i++) {
            futures.add(pool.submit(() -> {
                retained.add(new byte[500_000]); // each task retains ~500KB
                return recurse(20_000);          // each task also recurses moderately deep
            }));
        }
        for (Future<Integer> f : futures) f.get();
        pool.shutdown();
        System.out.println("tasks completed: " + futures.size() + ", retained: " + retained.size());
    }
}
```

**How to run:** `java -Xmx256m -Xss1m CombinedSizingWorkload.java` (JDK 17+; both flags must be sized adequately — 50 threads each need at least ~1MB of stack for the 20,000-deep recursion, and the heap must hold ~25MB of retained arrays plus JVM overhead).

Expected output shape:
```
tasks completed: 50, retained: 50
```

The production-flavored hard case: with 50 concurrent threads, total stack memory consumed is roughly `50 x -Xss` (here, ~50MB, entirely separate from the heap), while total retained heap data is roughly `50 x 500KB` (~25MB, well within `-Xmx256m`) — both flags must independently be sized correctly for this workload to succeed, and under-sizing either one (a too-small `-Xss` given the recursion depth, or a too-small `-Xmx` given the retained data plus per-thread overhead) produces its own distinct, independently diagnosable failure.

## 6. Walkthrough

Tracing `CombinedSizingWorkload.main` end to end:

1. A fixed thread pool of 50 threads is created — each of these threads, the moment it's created, is allocated its own stack of `-Xss1m` (1 MB), entirely separate from the heap and from every other thread's stack; this is committed regardless of whether that thread ever actually uses the full 1 MB.
2. 50 tasks are submitted; each task first appends a 500 KB `byte[]` to the shared, synchronized `retained` list — this array is allocated on the shared heap (sized by `-Xmx256m`), and because `retained` keeps a live reference to it, it survives any garbage collection that happens to run during the workload.
3. Each task then calls `recurse(20_000)`, which makes 20,000 nested method calls before returning — each nested call pushes a new frame onto *that thread's own stack* (not the heap), consuming a small, roughly constant amount of stack space per frame; with `-Xss1m`, 20,000 frames must fit comfortably within that thread's 1 MB budget, which this configuration is deliberately sized to satisfy.
4. As tasks complete across the pool, `futures.get()` calls in the main thread block until every task's result is available — since none of the 50 tasks fail (both the heap and stack budgets were sized adequately for this specific combination of retained-data volume and recursion depth), every `get()` call returns normally.
5. The final print statement confirms both the thread-count and heap-retention expectations were met: 50 completed tasks (meaning no `StackOverflowError` occurred on any of the 50 independent stacks) and 50 retained arrays (meaning the heap held all ~25 MB of retained data without triggering `OutOfMemoryError`) — a concrete demonstration that `-Xmx` and `-Xss` govern two entirely independent resources, both of which had to be correctly sized for this one workload to succeed at all.

## 7. Gotchas & takeaways

> **Gotcha:** total stack memory scales with *thread count*, not just `-Xss` alone — a service that creates thousands of threads, each with a generous `-Xss`, can exhaust available process memory through stack space alone, even while the heap (governed separately by `-Xmx`) still has plenty of room; this is a common, easy-to-miss cause of container OOM-kills in thread-heavy applications, and is exactly the kind of problem virtual threads (see [platform vs. virtual threads](0901-platform-vs-virtual-threads.md)) are designed to avoid by using far smaller, dynamically-sized stacks.

- `-Xms`/`-Xmx` size the shared heap (initial and maximum); `-Xss` sizes each individual thread's own separate stack — they govern entirely different memory regions with entirely different failure modes.
- Too small a heap for genuine live-data volume produces `OutOfMemoryError: Java heap space`; too small a stack for actual call depth produces `StackOverflowError` — raising the wrong flag never fixes the other problem.
- Setting `-Xms` equal to `-Xmx` avoids runtime heap-resize overhead and is common in production for services expected to reach near their maximum heap anyway.
- Total stack memory scales with thread count (`threads x -Xss`), which matters for thread-heavy applications even when the heap itself is sized generously.
- The heap is not the JVM's only memory region — metaspace, thread stacks, JIT-compiled code, and native/off-heap buffers all consume additional process memory that `-Xmx` alone does not account for, which matters when sizing a container's total memory limit.
- See [heap dumps & analysis](0940-heap-dumps-analysis.md) for determining an application's actual live-data volume before choosing `-Xmx`, rather than guessing.
