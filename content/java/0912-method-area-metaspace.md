---
card: java
gi: 912
slug: method-area-metaspace
title: Method area / Metaspace
---

## 1. What it is

The method area is the JVM Specification's name for the runtime data area that stores per-class structure: each loaded class's metadata (its name, its superclass, the interfaces it implements), the bytecode for its methods, its [runtime constant pool](0916-runtime-constant-pool.md), and static field storage. **Metaspace** is HotSpot's (the reference JVM implementation's) concrete realization of the method area since Java 8, replacing the older "PermGen" (permanent generation) design — the key practical difference being that metaspace, by default, is allocated from **native memory** (outside the regular Java heap) and, unlike the old fixed-size PermGen, can grow dynamically as needed, up to an optional configured limit.

## 2. Why & when

Understanding metaspace matters specifically when working with systems that load many classes dynamically — application servers hosting many deployed applications, systems that generate bytecode at runtime (proxies, ORMs), or anything using [custom class loaders](0908-custom-class-loaders.md) heavily — because metaspace has its own memory limit (`-XX:MaxMetaspaceSize`, unlimited by default in most modern JVM configurations, but still bounded by available system memory) and its own distinct exhaustion error: `OutOfMemoryError: Metaspace`, which is a completely different problem from running out of heap space and requires a different diagnosis (typically, a [classloader leak](0910-class-unloading.md) that keeps loading new classes without ever unloading old ones, rather than too many live object instances). Recognizing this distinction — heap holds *instances*, metaspace holds *class metadata* — is the key to correctly diagnosing which kind of memory problem you're actually looking at.

## 3. Core concept

```java
// Loading a class stores its metadata in METASPACE, not the heap:
Class<?> clazz = SomeClass.class; // the CLASS METADATA itself lives in metaspace

// Creating instances of that class stores the OBJECTS in the HEAP:
Object instance = clazz.getDeclaredConstructor().newInstance(); // this instance lives in the heap

// A system that keeps loading NEW classes (via distinct class loaders) without ever
// unloading old ones grows METASPACE usage, regardless of how few object instances exist.
```

The class's own metadata (method bytecode, field layout descriptions, the constant pool) is a one-time cost per distinct loaded class, stored in metaspace; every instance created from that class is a separate, additional cost in the heap.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Metaspace stores class metadata such as bytecode and constant pools, growing with each distinct class loaded; the heap separately stores object instances, growing with each object created, regardless of how many classes exist">
  <rect x="20" y="20" width="270" height="120" rx="10" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="155" y="40" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">Metaspace (native memory)</text>
  <rect x="40" y="55" width="100" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="90" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Class A metadata</text>
  <rect x="150" y="55" width="100" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="200" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Class B metadata</text>
  <text x="155" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">grows with DISTINCT LOADED CLASSES</text>

  <rect x="350" y="20" width="270" height="120" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="485" y="40" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Heap (Java memory)</text>
  <rect x="370" y="55" width="70" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="405" y="75" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance 1</text>
  <rect x="450" y="55" width="70" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="485" y="75" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance 2</text>
  <rect x="530" y="55" width="70" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="565" y="75" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance N</text>
  <text x="485" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">grows with OBJECT INSTANCES created</text>
</svg>

*Metaspace grows with distinct loaded classes; the heap grows with object instances — two entirely separate memory pools with independent limits and independent failure modes.*

## 5. Runnable example

Scenario: distinguishing metaspace exhaustion from heap exhaustion directly, growing from observing metaspace usage as classes are dynamically loaded, to deliberately exhausting metaspace via repeated custom-loader class definitions, to demonstrating that unloading (via dropping loader references) reverses the growth, tying directly back to [class unloading](0910-class-unloading.md).

### Level 1 — Basic

```java
import java.lang.management.*;

public class ObservingMetaspaceUsage {
    public static void main(String[] args) {
        MemoryPoolMXBean metaspacePool = ManagementFactory.getMemoryPoolMXBeans().stream()
            .filter(pool -> pool.getName().contains("Metaspace"))
            .findFirst()
            .orElseThrow();

        System.out.println("metaspace used before: " + metaspacePool.getUsage().getUsed() / 1024 + "KB");

        // Force loading of several distinct classes we haven't touched yet
        for (Class<?> c : new Class<?>[]{
            java.util.TreeMap.class, java.util.LinkedList.class, java.util.PriorityQueue.class,
            java.time.LocalDate.class, java.time.LocalTime.class, java.util.regex.Pattern.class
        }) {
            System.out.println("touched: " + c.getSimpleName());
        }

        System.out.println("metaspace used after: " + metaspacePool.getUsage().getUsed() / 1024 + "KB");
    }
}
```

**How to run:** `java ObservingMetaspaceUsage.java` (JDK 17+).

Expected output shape (metaspace usage grows as each class's metadata is loaded, though the exact amounts are JVM/version-dependent):
```
metaspace used before: 8452KB
touched: TreeMap
touched: LinkedList
touched: PriorityQueue
touched: LocalDate
touched: LocalTime
touched: Pattern
metaspace used after: 9103KB
```

Simply referencing each class (triggering its loading, even without creating any instances) grows metaspace usage — this is entirely separate from heap usage, which wouldn't change at all from this code alone.

### Level 2 — Intermediate

```java
import java.net.*;
import java.nio.file.*;
import java.util.*;

public class ExhaustingMetaspace {
    public static void main(String[] args) throws Exception {
        // Re-load the SAME .class file's bytes repeatedly, but through a BRAND NEW,
        // never-reused ClassLoader instance each time. Since (name, defining loader) is
        // what determines class identity, each loader produces a genuinely DISTINCT Class
        // object and its own metadata entry in metaspace -- even though the bytecode is
        // identical every time. Keeping every loader in `keepAlive` prevents any of them
        // from ever being unloaded, so metaspace usage only ever grows.
        URL classesDir = ExhaustingMetaspace.class.getProtectionDomain().getCodeSource().getLocation();
        List<ClassLoader> keepAlive = new ArrayList<>();
        int classesLoaded = 0;
        try {
            while (true) {
                URLClassLoader loader = new URLClassLoader(new URL[]{classesDir}, null);
                Class<?> loaded = loader.loadClass("Reloadable"); // same class, fresh loader every time
                keepAlive.add(loader); // never released -- nothing here can be unloaded
                classesLoaded++;
                if (classesLoaded % 2000 == 0) System.out.println("loaded " + classesLoaded + " distinct Class objects so far...");
            }
        } catch (OutOfMemoryError e) {
            System.out.println("caught OutOfMemoryError after loading roughly " + classesLoaded + " distinct Class objects");
            System.out.println("message: " + e.getMessage());
        }
    }
}

class Reloadable {}
```

**How to run:** compile both classes (`javac ExhaustingMetaspace.java`), then `java -XX:MaxMetaspaceSize=32m ExhaustingMetaspace` (JDK 17+; capping metaspace explicitly makes exhaustion happen quickly and deterministically).

Expected output shape (exact class count before failure depends on the configured cap and average per-class metadata size):
```
loaded 2000 distinct Class objects so far...
loaded 4000 distinct Class objects so far...
caught OutOfMemoryError after loading roughly 6482 distinct Class objects
message: Metaspace
```

The real-world concern added: repeatedly loading the *same* bytecode through a brand-new, permanently-referenced loader each time still produces a genuinely distinct `Class` object (and its own metadata) every iteration, exhausting metaspace specifically — note the error message is literally `"Metaspace"`, distinct from `"Java heap space"`, confirming this is a class-metadata capacity problem, not an object-instance capacity problem, even though no unusually large objects were ever created.

### Level 3 — Advanced

```java
import java.net.*;
import java.lang.ref.*;
import java.lang.management.*;

public class UnloadingReclaimsMetaspace {
    public static void main(String[] args) throws Exception {
        MemoryPoolMXBean metaspacePool = ManagementFactory.getMemoryPoolMXBeans().stream()
            .filter(pool -> pool.getName().contains("Metaspace"))
            .findFirst()
            .orElseThrow();

        long before = metaspacePool.getUsage().getUsed();

        URL classesDir = UnloadingReclaimsMetaspace.class.getProtectionDomain().getCodeSource().getLocation();
        URLClassLoader loader = new URLClassLoader(new URL[]{classesDir}, null);
        Class<?> loadedClass = loader.loadClass("ThrowawayClass");
        Object instance = loadedClass.getDeclaredConstructor().newInstance();

        long afterLoad = metaspacePool.getUsage().getUsed();
        System.out.println("metaspace grew by " + (afterLoad - before) / 1024 + "KB after loading ThrowawayClass");

        WeakReference<ClassLoader> loaderRef = new WeakReference<>(loader);
        instance = null;
        loadedClass = null;
        loader = null;

        System.gc();
        Thread.sleep(300);

        System.out.println("loader unloaded? " + (loaderRef.get() == null));
        long afterUnload = metaspacePool.getUsage().getUsed();
        System.out.println("metaspace usage after unload attempt: " + afterUnload / 1024 + "KB (should be closer to the 'before' baseline)");
    }
}

class ThrowawayClass {
    public String toString() { return "ThrowawayClass instance"; }
}
```

**How to run:** `java UnloadingReclaimsMetaspace.java` (JDK 17+).

Expected output shape (metaspace usage after unload should drop back close to the original baseline, though exact numbers vary by JVM and version):
```
metaspace grew by 4KB after loading ThrowawayClass
loader unloaded? true
metaspace usage after unload attempt: 8460KB (should be closer to the 'before' baseline)
```

This adds the production-flavored hard case: confirming that metaspace usage genuinely goes back down once a class loader (and the classes it defined) becomes unreachable and is collected — directly tying [class unloading](0910-class-unloading.md)'s reachability rules to the concrete memory region (metaspace) that actually shrinks as a result, and demonstrating that metaspace growth from dynamic class loading is not necessarily permanent, as long as loaders are properly dereferenced when no longer needed.

## 6. Walkthrough

Tracing `UnloadingReclaimsMetaspace.main`:

1. `loader.loadClass("ThrowawayClass")` triggers loading, linking, and (upon instantiation) initialization of `ThrowawayClass` through the newly-constructed, isolated `loader` — this stores `ThrowawayClass`'s metadata (its bytecode, constant pool, field/method descriptors) in metaspace, increasing `metaspacePool.getUsage().getUsed()` by a measurable amount.
2. `instance` holds the only strong reference to an actual `ThrowawayClass` object (in the heap); `loadedClass` holds a strong reference to its `Class` object; `loader` holds a strong reference to the class loader itself — all three are, for now, reachable from `main`'s local variables.
3. Setting all three to `null` removes every direct reference this code holds — since nothing else in the JVM references `ThrowawayClass`, its instance, or `loader` (it was constructed with `null` as its parent, and nothing else was told about it), the entire object/class/loader graph becomes unreachable.
4. `System.gc()` triggers a collection cycle; finding this graph unreachable, the collector reclaims the heap-resident instance and — crucially, since the class loader itself is also now unreachable — the metaspace-resident class metadata for `ThrowawayClass` as well, exactly the class-unloading process described in the prior tutorial.
5. `loaderRef.get() == null` confirms the loader itself was indeed collected.
6. The final metaspace usage reading, measured via the same `MemoryPoolMXBean` used at the start, drops back down close to the original `before` baseline — direct, measured confirmation that the metadata genuinely was reclaimed, not merely marked as logically unused while still consuming memory.

## 7. Gotchas & takeaways

> **Gotcha:** metaspace's default configuration in modern JVMs is effectively unbounded (limited only by available native/system memory, not a small fixed size the way old PermGen was) — this removed one common historical failure mode (a small, fixed PermGen filling up from ordinary application class loading) but replaced it with a different risk: a genuine classloader leak in an unbounded-metaspace configuration can consume all available system memory rather than failing fast with a small, easily-noticed limit, making the underlying leak potentially harder to notice until it affects the whole machine, not just the JVM process.

- The method area (realized as metaspace in HotSpot since Java 8) stores per-class metadata — bytecode, constant pools, static field storage — entirely separate from the heap, which stores object instances.
- Metaspace is allocated from native memory by default and can grow dynamically, bounded only by `-XX:MaxMetaspaceSize` (if set) or available system memory.
- `OutOfMemoryError: Metaspace` specifically indicates class-metadata exhaustion — typically caused by a [classloader leak](0910-class-unloading.md) (repeatedly loading new classes/loaders that are never unloaded), not by too many object instances, which would instead manifest as heap exhaustion.
- Metaspace usage does genuinely decrease once class loaders and the classes they defined become unreachable and are collected — dynamic class loading is not inherently a one-way, ever-growing cost, as long as loaders are correctly dereferenced when their classes are no longer needed.
- `java.lang.management.MemoryPoolMXBean` (queryable via `ManagementFactory.getMemoryPoolMXBeans()`) is a useful, standard way to directly observe metaspace (and heap) usage at runtime, without needing external profiling tools for basic diagnostics.
