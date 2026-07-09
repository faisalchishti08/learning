---
card: java
gi: 798
slug: late-barrier-expansion-for-g1
title: Late barrier expansion for G1
---

## 1. What it is

**Java 24** (JEP 475) changes **when**, during JIT compilation, the G1 garbage collector's **write barriers** — small pieces of bookkeeping code the JVM inserts around every reference field write, needed so G1 can track which objects point to which across its generational regions — get inserted into compiled machine code. Previously, the C2 JIT compiler inserted these barriers **early**, before most of its optimization passes ran, forcing every later optimization to understand and correctly handle barrier-related code. This JEP moves barrier insertion **late**, after the bulk of C2's optimizations have already run on simpler, barrier-free code — a purely internal JIT-compiler change with no new API, flag to enable (it's on automatically with G1), or application-visible behavior difference.

## 2. Why & when

A write barrier isn't optional — every reference field write under G1 needs one — but *when* the compiler inserts it changes how much complexity every other optimization pass has to deal with. Inserting barriers early meant C2's many optimization passes (inlining, loop transformations, instruction scheduling, register allocation) all had to be written to correctly recognize and preserve barrier-related code sequences threaded through the intermediate representation, adding real ongoing engineering cost and constraining how aggressively some optimizations could transform code containing them. Expanding barriers **late** — after most optimizations have already simplified and transformed the code — lets those optimization passes work on simpler, more conventional code shapes, then inserts the necessary barrier logic only once, right before final code generation. This is squarely a JIT-compiler-maintainability and long-term-flexibility change: it doesn't change what any Java program computes, and for most workloads any performance difference is expected to be neutral to slightly positive (simpler intermediate representations sometimes let other optimizations do a better job), but the primary motivation is making G1's interaction with C2 easier to maintain and evolve going forward, rather than pursuing a specific measured speedup as the headline goal.

## 3. Core concept

```
# No application code change required — this is a C2/G1 internal compiler change.
java -XX:+UseG1GC MyApp
```

Every reference-field write in `MyApp` still gets exactly the write barrier G1 requires — only the point in the JIT compilation pipeline where that barrier code gets woven into the generated machine instructions has moved.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Before Java 24, G1 write barriers were inserted early in C2 compilation, before optimizations ran; Java 24 moves barrier insertion to late in the pipeline, after most optimizations have already simplified the code" >
  <rect x="20" y="20" width="280" height="70" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="42" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Before Java 24</text>
  <text x="160" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">barriers inserted early, every later</text>
  <text x="160" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">optimization pass must handle them</text>

  <rect x="340" y="20" width="280" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Java 24: late barrier expansion</text>
  <text x="480" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">optimizations run on simpler code first,</text>
  <text x="480" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">barriers inserted just before codegen</text>

  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Same barriers, same correctness guarantee — simplified internal compiler pipeline</text>
</svg>

*A JIT-compiler-internals reordering: optimizations get a cleaner view of the code before barrier logic is woven in.*

## 5. Runnable example

Scenario: a reference-field-write-heavy workload (the exact pattern write barriers exist for), growing from a simple mutation loop into a concurrent, high-churn linked structure — with guidance on observing this change indirectly, since it has no directly observable Java-level effect.

### Level 1 — Basic

```java
public class BarrierWorkloadBasic {
    static class Node {
        Node next;
        int value;
    }

    public static void main(String[] args) {
        Node head = null;
        for (int i = 0; i < 5_000_000; i++) {
            Node n = new Node();
            n.value = i;
            n.next = head; // reference field write — needs a G1 write barrier
            head = n;
        }

        long count = 0;
        for (Node n = head; n != null; n = n.next) count++;
        System.out.println("nodes linked: " + count);
    }
}
```

**How to run:** `java -XX:+UseG1GC BarrierWorkloadBasic.java` (JDK 24+; G1 is the JDK's default collector, so this flag is often implicit).

Building a 5,000,000-node linked list means 5,000,000 reference-field writes (`n.next = head`) — each one requiring a G1 write barrier under the hood, regardless of when in the compilation pipeline that barrier gets woven in.

### Level 2 — Intermediate

```java
public class BarrierWorkloadTimed {
    static class Node {
        Node next;
        int value;
    }

    static long buildAndCount(int size) {
        Node head = null;
        for (int i = 0; i < size; i++) {
            Node n = new Node();
            n.value = i;
            n.next = head;
            head = n;
        }
        long count = 0;
        for (Node n = head; n != null; n = n.next) count++;
        return count;
    }

    public static void main(String[] args) {
        // Warm up the JIT so C2 has compiled the hot loop before timing it.
        for (int i = 0; i < 5; i++) buildAndCount(1_000_000);

        long start = System.nanoTime();
        long total = 0;
        for (int i = 0; i < 20; i++) {
            total += buildAndCount(1_000_000);
        }
        double millis = (System.nanoTime() - start) / 1_000_000.0;

        System.out.println("total nodes processed: " + total);
        System.out.printf("elapsed after warmup: %.1f ms%n", millis);
    }
}
```

**How to run:** `java -XX:+UseG1GC BarrierWorkloadTimed.java`.

The real-world concern added: an explicit **warmup phase** before timing, standard practice for measuring JIT-compiled steady-state performance — this is the shape of benchmark that could, in principle, show a small difference between JDK versions with and without late barrier expansion, though since this JEP targets compiler *maintainability* rather than a guaranteed speedup, any difference is expected to be modest at best and workload-dependent.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.*;

public class BarrierWorkloadConcurrent {
    static class Node {
        volatile Node next;
        int value;
    }

    static long buildAndCount(int size) {
        Node head = null;
        for (int i = 0; i < size; i++) {
            Node n = new Node();
            n.value = i;
            n.next = head; // volatile reference write — still needs the G1 barrier
            head = n;
        }
        long count = 0;
        for (Node n = head; n != null; n = n.next) count++;
        return count;
    }

    public static void main(String[] args) throws Exception {
        int threadCount = 4;
        try (var executor = Executors.newFixedThreadPool(threadCount)) {
            List<Future<Long>> futures = new ArrayList<>();
            for (int t = 0; t < threadCount; t++) {
                futures.add(executor.submit(() -> {
                    long total = 0;
                    for (int i = 0; i < 10; i++) total += buildAndCount(500_000);
                    return total;
                }));
            }
            long grandTotal = 0;
            for (var f : futures) grandTotal += f.get();
            System.out.println("grand total nodes processed across threads: " + grandTotal);
        }
    }
}
```

**How to run:** `java -XX:+UseG1GC -Xlog:gc:file=g1.log BarrierWorkloadConcurrent.java` — for deeper JIT-level inspection (advanced diagnostic use only), compare with `-XX:+PrintCompilation` output between JDK 23 and JDK 24 builds on identical hardware.

This adds the production-flavored hard case: **four threads concurrently** building and tearing down large linked structures with `volatile` reference fields — heavy, concurrent, sustained write-barrier traffic, the kind of allocation-and-mutation-heavy multi-threaded workload where G1's barrier-handling efficiency matters most, and the setting in which any (likely small) throughput difference from late barrier expansion would be most measurable.

## 6. Walkthrough

Tracing the GC/JIT-relevant behavior of `BarrierWorkloadConcurrent.main` (the program's own logic is ordinary Java; what differs under the hood is compiler-internal):

1. `main` submits four tasks to a fixed thread pool, each independently building and traversing ten separate 500,000-node linked lists.
2. Every `n.next = head` assignment is a reference field write; under G1, the JIT-compiled machine code for this loop includes a write barrier immediately around each such write, updating G1's remembered-set bookkeeping so the collector can correctly track cross-region references without needing to rescan the entire heap on every collection cycle.
3. Once C2 compiles `buildAndCount`'s hot loop (after enough invocations to trigger JIT compilation), the *compiled* machine code contains this barrier logic — under Java 24's late barrier expansion, that machine code was generated by first running C2's optimization passes on a simpler, barrier-free intermediate representation, then inserting the barrier logic in a final expansion step before actual code generation, rather than threading barrier-aware logic through every optimization pass from the start.
4. The **numeric result** (`grandTotal`) and the program's correctness are completely unaffected by this internal compilation-order change — G1 still tracks every cross-region reference correctly either way, since the barrier logic itself, only its insertion point in the compiler pipeline, is what changed.
5. `main` sums each thread's returned count and prints the grand total once all four `Future`s complete.

Expected output:
```
grand total nodes processed across threads: 20000000
```

(This number — 4 threads × 10 iterations × 500,000 nodes = 20,000,000 — is identical regardless of JDK version or barrier-expansion timing; any observable difference from this JEP would show up only in wall-clock timing or JIT compilation diagnostics, never in program output.)

## 7. Gotchas & takeaways

> **Gotcha:** because this change targets compiler internals and maintainability rather than a specific measured speedup, don't expect a dramatic, consistently reproducible performance difference in typical application benchmarks — some workloads may see a small improvement (simpler code shapes sometimes let other optimizations perform better), some may see no measurable difference at all, and drawing firm performance conclusions requires careful, repeated, warmed-up benchmarking on your specific workload rather than assuming a blanket speedup.

- No application-visible API — this is purely a C2 JIT compiler and G1 collector internals change, active automatically with G1 on Java 24+.
- Moves G1 write-barrier code insertion from early in C2's compilation pipeline (before most optimizations) to late (just before final code generation).
- The motivation is primarily compiler **maintainability and flexibility** for future JIT and GC evolution, not a guaranteed application-level speedup.
- Program correctness and output are completely unaffected — every reference field write still gets exactly the write barrier G1 requires.
- Complements other internal G1/C2 evolution (like [region pinning](0768-region-pinning-for-g1.md)) as part of the JDK's ongoing effort to keep G1's implementation maintainable while continuing to improve it.
