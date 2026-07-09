---
card: java
gi: 697
slug: elastic-metaspace
title: Elastic Metaspace
---

## 1. What it is

**Java 16** shipped a rewritten memory-management implementation for **Metaspace** — the off-heap memory region where the JVM stores class metadata (loaded classes' structure, method bytecode references, and related data) — under the name **Elastic Metaspace** (JEP 387). The class-loading and reflection-facing behavior of Metaspace is unchanged; what changed is the internal allocator: the new implementation returns unused metaspace memory back to the operating system **more promptly**, reduces memory fragmentation, and simplifies the tunable flags around metaspace sizing, replacing the previous implementation which had a long-standing reputation for holding onto committed memory even after large numbers of classes were unloaded.

## 2. Why & when

Applications that load and unload large numbers of classes over their lifetime — application servers hosting many deployed apps, environments doing heavy dynamic class generation (frameworks generating proxies, ORMs, scripting-language runtimes on the JVM), or long-running services that redeploy code without a JVM restart — could previously see Metaspace's committed memory grow over time and never shrink back down, even after the classes responsible for that growth had long since become unreachable and been unloaded. This was a genuine operational pain point: a service's memory footprint (as reported by the OS) could look permanently bloated relative to what the running application actually needed at any given moment, complicating capacity planning and container memory-limit sizing. Elastic Metaspace directly addresses this by returning freed metaspace memory to the OS far more readily. This isn't something application code interacts with directly — it's an internal JVM implementation change — but it matters for anyone tuning JVM memory flags (`-XX:MaxMetaspaceSize`, `-XX:MetaspaceSize`) or investigating why a long-running JVM's resident memory looked larger than expected.

## 3. Core concept

```bash
# Observing Metaspace behavior is done via diagnostic flags/tools, not application code:
java -Xlog:gc+metaspace=info MyApp

# Or via jcmd against a running process:
jcmd <pid> VM.metaspace
```

There's no new application-facing API for Elastic Metaspace — the change is entirely in how the JVM manages this memory region internally; you observe its effect through GC logging, `jcmd`, or simply by measuring the process's memory footprint over time.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Before Java 16, metaspace memory committed for many loaded classes tends to stay committed even after those classes are unloaded; Elastic Metaspace returns freed memory to the OS more promptly">
  <rect x="20" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Pre-Java 16 Metaspace</text>
  <rect x="40" y="60" width="240" height="20" fill="#79c0ff" opacity="0.7"/>
  <text x="160" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">many classes loaded/unloaded</text>
  <rect x="40" y="115" width="240" height="20" fill="#f0883e" opacity="0.7"/>
  <text x="160" y="150" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">committed memory often stays high</text>

  <rect x="340" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 16+ Elastic Metaspace</text>
  <rect x="360" y="60" width="240" height="20" fill="#79c0ff" opacity="0.7"/>
  <text x="480" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">many classes loaded/unloaded</text>
  <rect x="360" y="115" width="120" height="20" fill="#3fb950" opacity="0.7"/>
  <text x="480" y="150" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">committed memory shrinks back down</text>
</svg>

Both JVMs load and unload the same classes; only the newer allocator returns the freed memory to the OS afterward.

## 5. Runnable example

Scenario: repeatedly loading and discarding classes via classloaders to put pressure on Metaspace — first a simple loop that creates many short-lived classloaders (each loading a small dynamically-defined class), then adding explicit `System.gc()` calls and metaspace measurement via `MemoryMXBean` to observe usage over time, then a version that logs metaspace usage at intervals to visualize the pattern an operator would look for.

### Level 1 — Basic

```java
// File: MetaspaceChurnBasic.java
import java.lang.invoke.MethodHandles;

public class MetaspaceChurnBasic {
    static byte[] tinyClassBytes() throws Exception {
        // Reuse a small nested class's compiled bytecode as "load material"
        return MetaspaceChurnBasic.class.getResourceAsStream("MetaspaceChurnBasic$Tiny.class").readAllBytes();
    }

    public static class Tiny {}

    public static void main(String[] args) throws Exception {
        byte[] classBytes = tinyClassBytes();
        int loaded = 0;
        for (int i = 0; i < 5000; i++) {
            MethodHandles.Lookup lookup = MethodHandles.lookup();
            lookup.defineHiddenClass(classBytes, false);
            loaded++;
        }
        System.out.println("Defined " + loaded + " short-lived hidden classes.");
    }
}
```

**How to run:** `java MetaspaceChurnBasic.java`

Expected output:
```
Defined 5000 short-lived hidden classes.
```

### Level 2 — Intermediate

```java
// File: MetaspaceMeasurement.java
import java.lang.invoke.MethodHandles;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryPoolMXBean;
import java.lang.management.MemoryUsage;

public class MetaspaceMeasurement {
    static byte[] tinyClassBytes() throws Exception {
        return MetaspaceMeasurement.class.getResourceAsStream("MetaspaceMeasurement$Tiny.class").readAllBytes();
    }

    public static class Tiny {}

    static MemoryPoolMXBean metaspacePool() {
        return ManagementFactory.getMemoryPoolMXBeans().stream()
                .filter(p -> p.getName().equals("Metaspace"))
                .findFirst().orElseThrow();
    }

    public static void main(String[] args) throws Exception {
        MemoryPoolMXBean metaspace = metaspacePool();
        byte[] classBytes = tinyClassBytes();

        MemoryUsage before = metaspace.getUsage();
        System.out.println("Metaspace used before: " + before.getUsed() / 1024 + " KB");

        for (int i = 0; i < 20000; i++) {
            MethodHandles.Lookup lookup = MethodHandles.lookup();
            lookup.defineHiddenClass(classBytes, false);
        }

        MemoryUsage after = metaspace.getUsage();
        System.out.println("Metaspace used after: " + after.getUsed() / 1024 + " KB");
        System.out.println("Growth: " + (after.getUsed() - before.getUsed()) / 1024 + " KB");
    }
}
```

**How to run:** `java MetaspaceMeasurement.java`

Expected output shape (exact KB values vary widely by JDK build, platform, and how many classes were already loaded before `main` ran — the important part is that `after` is measurably larger than `before`, reflecting metaspace growth from the 20,000 hidden classes just defined):
```
Metaspace used before: 17741 KB
Metaspace used after: 37906 KB
Growth: 20164 KB
```

### Level 3 — Advanced

```java
// File: MetaspaceOverTime.java
import java.lang.invoke.MethodHandles;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryPoolMXBean;

public class MetaspaceOverTime {
    static byte[] tinyClassBytes() throws Exception {
        return MetaspaceOverTime.class.getResourceAsStream("MetaspaceOverTime$Tiny.class").readAllBytes();
    }

    public static class Tiny {}

    static MemoryPoolMXBean metaspacePool() {
        return ManagementFactory.getMemoryPoolMXBeans().stream()
                .filter(p -> p.getName().equals("Metaspace"))
                .findFirst().orElseThrow();
    }

    public static void main(String[] args) throws Exception {
        MemoryPoolMXBean metaspace = metaspacePool();
        byte[] classBytes = tinyClassBytes();

        for (int wave = 1; wave <= 5; wave++) {
            for (int i = 0; i < 10000; i++) {
                MethodHandles.Lookup lookup = MethodHandles.lookup();
                lookup.defineHiddenClass(classBytes, false);
            }
            System.gc();
            long usedKb = metaspace.getUsage().getUsed() / 1024;
            long committedKb = metaspace.getUsage().getCommitted() / 1024;
            System.out.printf("After wave %d: used=%dKB, committed=%dKB%n", wave, usedKb, committedKb);
        }
    }
}
```

**How to run:** `java MetaspaceOverTime.java`

Expected output shape (exact values vary widely by JDK build, platform, and baseline classes already loaded; the key qualitative pattern is that both `used` and `committed` should level off after the first wave or two, rather than climbing wave after wave, once hidden classes from earlier waves become unreachable and are collected):
```
After wave 1: used=17797KB, committed=18048KB
After wave 2: used=18350KB, committed=18560KB
After wave 3: used=18350KB, committed=18560KB
After wave 4: used=18350KB, committed=18560KB
After wave 5: used=18350KB, committed=18560KB
```

Level 3 runs five successive "waves" of class-loading churn, calling `System.gc()` between waves to encourage collection of hidden classes from prior waves that are no longer referenced, then reports both `used` (metaspace bytes actually holding live class data) and `committed` (bytes the JVM has claimed from the OS, whether or not currently used) — `committed` staying roughly flat across waves, rather than climbing wave over wave, is the qualitative signature of Elastic Metaspace's improved memory return behavior.

## 6. Walkthrough

1. `main` retrieves the `MemoryPoolMXBean` specifically named `"Metaspace"` from `ManagementFactory.getMemoryPoolMXBeans()` — this bean tracks exactly the memory region this tutorial concerns, distinct from the heap or other memory pools.
2. The outer loop runs 5 "waves." In each wave, an inner loop of 10,000 iterations calls `MethodHandles.lookup().defineHiddenClass(classBytes, false)` — defining a fresh [hidden class](0681-hidden-classes.md) from the same small, precompiled `Tiny` class's bytecode each time. Passing `false` for the `initialize` argument skips running static initializers, since none exist here and this keeps each definition as lightweight as possible.
3. Because each of the 10,000 hidden classes defined per wave is never assigned to any retained variable or field, all of them become unreachable garbage almost immediately after being defined — nothing in the program holds a reference to any of them past the loop iteration that created them.
4. After each wave's loop completes, `System.gc()` is called — a request (not a guarantee) that the JVM run a garbage collection cycle, which, for unreachable hidden classes specifically, can allow the JVM to unload them and reclaim the metaspace memory that was backing their class metadata.
5. `metaspace.getUsage().getUsed()` and `.getCommitted()` are then read and printed: `used` reflects how many bytes of metaspace are actually occupied by live (still-referenced) class metadata at that moment, while `committed` reflects how many bytes the JVM currently holds reserved from the operating system for this pool, regardless of how much of it is actually in use right now.
6. Across the five waves, if class unloading and Elastic Metaspace's more prompt memory return are both working as intended, `used` should stay roughly flat wave-over-wave (each wave's 10,000 hidden classes get unloaded before or shortly after the next wave begins), and `committed` should likewise stay roughly flat rather than ratcheting upward — in older, pre-Elastic-Metaspace JVMs, `committed` was more prone to staying high even after `used` dropped, since the older allocator was less aggressive about returning freed metaspace regions to the OS.
7. The printed report — one line per wave, showing both `used` and `committed` — is exactly the kind of lightweight, ongoing diagnostic an operator monitoring a long-running, class-loading-heavy service would build to confirm metaspace isn't growing unboundedly over the service's actual lifetime.

```
for wave in 1..5:
    define 10,000 hidden classes (all become unreachable immediately)
    System.gc()  ── request unloading of unreferenced hidden classes
    read metaspace used / committed
    print wave report
```

## 7. Gotchas & takeaways

> `System.gc()` is only a **request**, not a guarantee, that garbage collection runs immediately — in a real long-running service, class unloading happens whenever the JVM's normal collection cycles determine it's appropriate, not necessarily right when your code calls `System.gc()`. The explicit call here is used purely to make the demonstration's timing more predictable; production code should essentially never call `System.gc()` directly.

- Elastic Metaspace is an **internal JVM implementation change** — there's no new application-facing API; you observe its effect via `MemoryPoolMXBean`, `-Xlog:gc+metaspace`, or `jcmd <pid> VM.metaspace`, not through any code you write.
- The specific benefit — memory being returned to the OS more promptly after classes are unloaded — matters most for long-running processes with significant class-loading churn: application servers, systems doing heavy dynamic proxy/bytecode generation, or services that redeploy code without restarting the JVM.
- `-XX:MaxMetaspaceSize` and `-XX:MetaspaceSize` remain the relevant tuning flags; Elastic Metaspace simplified some of the more obscure, harder-to-tune flags that existed in the older implementation, without removing the two most commonly used ones.
- Metaspace usage is driven by **class metadata**, not regular object instances — this tutorial's technique of churning through many [hidden classes](0681-hidden-classes.md) specifically targets metaspace, unlike an ordinary object-allocation-heavy workload, which would primarily pressure the regular heap instead.
- If you're diagnosing unexpectedly high resident memory in a running JVM, `jcmd <pid> VM.metaspace` gives a detailed breakdown (by class loader, by memory chunk type) that's more informative for root-causing metaspace bloat than the coarser `used`/`committed` numbers from `MemoryPoolMXBean` alone.
