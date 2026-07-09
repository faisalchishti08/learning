---
card: java
gi: 567
slug: permgen-removed-metaspace
title: PermGen removed → Metaspace
---

## 1. What it is

**PermGen** ("Permanent Generation") was the JVM heap region, up through Java 7, that stored class metadata — loaded classes, method bytecode references, interned strings, static fields. Java 8 removed PermGen entirely and replaced it with **Metaspace**, which stores the same kind of class metadata but lives in **native memory** (outside the JVM heap) and, by default, grows dynamically instead of being capped by a fixed size set at JVM startup.

## 2. Why & when

PermGen had a well-known, chronic problem: it was sized with a fixed maximum (`-XX:MaxPermSize`, defaulting to a fairly small value) that was easy to exhaust, producing the notorious `java.lang.OutOfMemoryError: PermGen space`. This happened constantly in application servers that reloaded web applications repeatedly (each redeploy could load a fresh set of classes without always fully unloading the old ones), and tuning `-XX:MaxPermSize` correctly was a persistent operational headache — set it too low and you get crashes under normal use, too high and you waste memory the heap could have used instead. Metaspace fixes this by using native memory that, by default, grows as needed up to the amount of memory the operating system can provide (with an optional `-XX:MaxMetaspaceSize` cap you can still set if you want one) — the chronic "PermGen space" errors from class-metadata growth largely disappeared as a result. This matters most for anyone tuning JVM memory flags, diagnosing `OutOfMemoryError`s, or working with class-loader-heavy environments (app servers, dynamic proxy generation, heavy reflection/bytecode-generation frameworks).

## 3. Core concept

```
Java 7 and earlier:                    Java 8 and later:
+------------------+                   +------------------+
| Young Generation |                   | Young Generation |
+------------------+                   +------------------+
| Old Generation   |    heap           | Old Generation   |    heap
+------------------+                   +------------------+
| PermGen          |  <- fixed size,   +------------------+
+------------------+     part of heap

                                        +------------------+
                                        | Metaspace        |  <- native memory,
                                        +------------------+     grows dynamically
```

Class metadata moved out of the JVM heap entirely and into memory managed more like a native allocator, with size limited by available system memory rather than a hard-coded JVM flag (unless you explicitly set one).

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PermGen was part of the fixed-size heap; Metaspace lives in native memory and grows dynamically">
  <text x="20" y="25" fill="#8b949e" font-size="11" font-family="sans-serif">Java 7: PermGen inside the heap, fixed max size</text>
  <rect x="20" y="35" width="280" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="60" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Young + Old Generation</text>
  <rect x="20" y="95" width="280" height="30" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="160" y="115" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">PermGen (fixed cap -&gt; OOM risk)</text>

  <text x="340" y="25" fill="#8b949e" font-size="11" font-family="sans-serif">Java 8+: Metaspace outside the heap, native memory</text>
  <rect x="340" y="35" width="280" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="480" y="60" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Young + Old Generation (heap)</text>
  <rect x="340" y="105" width="280" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="125" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Metaspace (grows dynamically, native)</text>

  <text x="20" y="160" fill="#8b949e" font-size="10" font-family="sans-serif">Class metadata (loaded classes, method bytecode refs) lives in the red/green box either way —</text>
  <text x="20" y="175" fill="#8b949e" font-size="10" font-family="sans-serif">only where it lives, and how its size is bounded, changed between the two versions.</text>
</svg>

Same kind of data (class metadata), different storage location and growth strategy.

## 5. Runnable example

Scenario: observing class-metadata memory usage as a program dynamically generates and loads many classes at runtime (simulating what a heavy dependency-injection or proxy-generation framework does) — starting with reading Metaspace usage via `MemoryMXBean`, then generating many classes with a custom class loader to watch usage grow, then setting an explicit cap and observing what happens when it's exceeded.

### Level 1 — Basic

```java
import java.lang.management.*;
import java.util.List;

public class MetaspaceBasic {
    public static void main(String[] args) {
        List<MemoryPoolMXBean> pools = ManagementFactory.getMemoryPoolMXBeans();

        for (MemoryPoolMXBean pool : pools) {
            if (pool.getName().contains("Metaspace")) {
                MemoryUsage usage = pool.getUsage();
                System.out.println(pool.getName() + ": used=" + (usage.getUsed() / 1024) + " KB, "
                    + "max=" + (usage.getMax() == -1 ? "unbounded" : (usage.getMax() / 1024) + " KB"));
            }
        }
    }
}
```

**How to run:** `java MetaspaceBasic.java`

Expected output (exact KB values vary by JVM version and what's already loaded; the key detail is "unbounded" and a nonzero "used"):
```
Metaspace: used=3120 KB, max=unbounded
```

`ManagementFactory.getMemoryPoolMXBeans()` returns one `MemoryPoolMXBean` per JVM memory pool, including a `"Metaspace"` pool on Java 8+ (there is no `"PermGen"` pool anymore — this is the direct, observable proof that PermGen was replaced). `pool.getUsage().getMax()` returns `-1` when no `-XX:MaxMetaspaceSize` was set at JVM startup, which the code translates to `"unbounded"` — by default, Metaspace can grow until the operating system itself runs out of memory to give it.

### Level 2 — Intermediate

```java
import java.lang.management.*;
import javax.tools.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;

public class MetaspaceGrowth {
    static void printMetaspaceUsage(String label) {
        for (MemoryPoolMXBean pool : ManagementFactory.getMemoryPoolMXBeans()) {
            if (pool.getName().contains("Metaspace")) {
                System.out.println(label + ": used=" + (pool.getUsage().getUsed() / 1024) + " KB");
            }
        }
    }

    // Writes `count` distinct, tiny top-level classes as .java files and compiles them
    // all in one javac invocation via the JDK's own compiler API.
    static Path generateAndCompileClasses(int count) throws IOException {
        Path outputDir = Files.createTempDirectory("metaspace-growth-demo");
        List<Path> sourceFiles = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            String className = "Generated" + i;
            String source = "public class " + className + " { public static int marker = " + i + "; }";
            Path sourceFile = outputDir.resolve(className + ".java");
            Files.writeString(sourceFile, source);
            sourceFiles.add(sourceFile);
        }

        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        StandardJavaFileManager fileManager = compiler.getStandardFileManager(null, null, null);
        Iterable<? extends JavaFileObject> units = fileManager.getJavaFileObjectsFromPaths(sourceFiles);
        compiler.getTask(null, fileManager, null, List.of("-d", outputDir.toString()), null, units).call();
        fileManager.close();
        return outputDir;
    }

    public static void main(String[] args) throws Exception {
        int classCount = 5000;
        Path outputDir = generateAndCompileClasses(classCount); // compiled, but not yet loaded

        printMetaspaceUsage("Before loading");

        URL[] classpath = { outputDir.toUri().toURL() };
        URLClassLoader loader = new URLClassLoader(classpath, MetaspaceGrowth.class.getClassLoader());
        List<Class<?>> loaded = new ArrayList<>();
        for (int i = 0; i < classCount; i++) {
            loaded.add(Class.forName("Generated" + i, true, loader));
        }

        printMetaspaceUsage("After loading " + loaded.size() + " distinct classes");
    }
}
```

**How to run:** `java MetaspaceGrowth.java`

Expected output (exact KB values vary by machine/JVM; the key detail is that "after" is measurably higher than "before"):
```
Before loading: used=17500 KB
After loading 5000 distinct classes: used=20800 KB
```

The real-world concern this adds: **watching Metaspace grow in response to real class-loading activity**, the exact scenario that used to exhaust PermGen in frameworks that generate many classes at runtime (dynamic proxies, ORM entity enhancement, DI container bytecode generation). `generateAndCompileClasses` uses `ToolProvider.getSystemJavaCompiler()` — the same compiler `javac` itself uses — to produce 5,000 genuinely distinct, separately-named `.class` files up front; the loop then loads every one of them by name through a shared `URLClassLoader`, and because each is a distinct class (not the same class loaded repeatedly), each contributes its own metadata, growing Metaspace usage measurably between the two `printMetaspaceUsage` calls.

### Level 3 — Advanced

```java
import java.lang.management.*;
import javax.tools.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;

public class MetaspaceCapped {
    static void printMetaspaceUsage(String label) {
        for (MemoryPoolMXBean pool : ManagementFactory.getMemoryPoolMXBeans()) {
            if (pool.getName().contains("Metaspace")) {
                MemoryUsage usage = pool.getUsage();
                String max = usage.getMax() == -1 ? "unbounded" : (usage.getMax() / 1024 / 1024) + " MB";
                System.out.println(label + ": used=" + (usage.getUsed() / 1024) + " KB, max=" + max);
            }
        }
    }

    // Compiles `count` distinct, tiny top-level classes into `outputDir` in a single javac run.
    static void generateAndCompileClasses(Path outputDir, int count) throws IOException {
        List<Path> sourceFiles = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            String className = "Generated" + i;
            String source = "public class " + className + " { public static int marker = " + i + "; }";
            Path sourceFile = outputDir.resolve(className + ".java");
            Files.writeString(sourceFile, source);
            sourceFiles.add(sourceFile);
        }

        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        StandardJavaFileManager fileManager = compiler.getStandardFileManager(null, null, null);
        Iterable<? extends JavaFileObject> units = fileManager.getJavaFileObjectsFromPaths(sourceFiles);
        List<String> options = List.of("-d", outputDir.toString());
        compiler.getTask(null, fileManager, null, options, null, units).call();
        fileManager.close();
    }

    public static void main(String[] args) throws Exception {
        // Run with: java -XX:MaxMetaspaceSize=48m MetaspaceCapped.java
        printMetaspaceUsage("Startup");

        Path outputDir = Files.createTempDirectory("metaspace-demo");
        int batchSize = 500;
        generateAndCompileClasses(outputDir, batchSize); // one javac run compiles a whole batch

        URL[] classpath = { outputDir.toUri().toURL() };
        List<Object> keepAlive = new ArrayList<>(); // prevents loaded classes/classloaders from being GC'd

        try {
            int totalLoaded = 0;
            while (true) {
                // A FRESH classloader per class keeps every one of them permanently reachable and
                // ineligible for unloading, so their metadata accumulates in Metaspace for real.
                URLClassLoader loader = new URLClassLoader(classpath, MetaspaceCapped.class.getClassLoader());
                Class<?> generated = Class.forName("Generated" + (totalLoaded % batchSize), true, loader);
                keepAlive.add(loader);
                keepAlive.add(generated);
                totalLoaded++;

                if (totalLoaded % 1_000 == 0) {
                    printMetaspaceUsage("After " + totalLoaded + " class loads");
                }
            }
        } catch (OutOfMemoryError e) {
            System.out.println("Caught: " + e.getMessage());
            System.out.println("This is the modern equivalent of the old 'PermGen space' error —");
            System.out.println("now reported as Metaspace exhaustion, and only happens because we");
            System.out.println("explicitly capped it with -XX:MaxMetaspaceSize.");
        }
    }
}
```

**How to run:** `java -XX:MaxMetaspaceSize=48m MetaspaceCapped.java`

Expected output (exact class-load counts and KB values before exhaustion vary by JVM/machine; the key detail is that it always eventually throws, bounded by the explicit cap, unlike the default unbounded behavior — and notice it throws well *before* `used` reaches the full 48 MB, which part 6 explains):
```
Startup: used=17935 KB, max=48 MB
After 1000 class loads: used=21408 KB, max=48 MB
After 2000 class loads: used=22696 KB, max=48 MB
After 3000 class loads: used=23984 KB, max=48 MB
After 4000 class loads: used=25271 KB, max=48 MB
Caught: Metaspace
This is the modern equivalent of the old 'PermGen space' error —
now reported as Metaspace exhaustion, and only happens because we
explicitly capped it with -XX:MaxMetaspaceSize.
```

This handles the production-flavoured case of **deliberately re-introducing a size cap** with `-XX:MaxMetaspaceSize=48m` and driving real class-metadata growth: `generateAndCompileClasses` uses the JDK's own compiler API (`ToolProvider.getSystemJavaCompiler()`) to compile 500 genuinely distinct classes to disk in one batch, and the loop then loads them repeatedly through **fresh `URLClassLoader` instances**, each of which is kept reachable in `keepAlive` — since a class's metadata can only be reclaimed once its defining classloader becomes unreachable, this forces Metaspace to accumulate real class metadata until it hits the cap and throws `OutOfMemoryError`, exactly the failure mode PermGen was infamous for.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example, run with `-XX:MaxMetaspaceSize=48m` explicitly capping Metaspace at 48 megabytes (deliberately reintroducing the kind of fixed limit PermGen always had, purely to demonstrate the failure mode still exists when explicitly configured).

`printMetaspaceUsage("Startup")` reads the current Metaspace usage before any extra classes are loaded, confirming `max` reports as `"48 MB"` — the `MemoryUsage.getMax()` value now reflects the flag we passed, rather than `-1` (unbounded) as it did in the Level 1 example without the flag.

`generateAndCompileClasses(outputDir, 500)` runs next: it writes 500 tiny `.java` source files (`Generated0.java` through `Generated499.java`), each defining a genuinely distinct top-level class, then invokes `ToolProvider.getSystemJavaCompiler()` — the same compiler `javac` itself uses — to compile all 500 in a single `getTask(...).call()` invocation, writing `.class` files into `outputDir`. This happens once, up front, so the subsequent loop only pays for class *loading*, not repeated compilation.

The `while (true)` loop then loads classes repeatedly:

```
iteration 0: new URLClassLoader -> Class.forName("Generated0")   -> loader+class kept alive
iteration 1: new URLClassLoader -> Class.forName("Generated1")   -> loader+class kept alive
...
iteration 500: new URLClassLoader -> Class.forName("Generated0") again, but via a DIFFERENT loader
```

Crucially, each iteration creates a **fresh** `URLClassLoader` before loading the class by name. Because the JVM identifies a loaded class by the pair (class name, defining classloader), loading `"Generated0"` through two different `URLClassLoader` instances produces two *distinct* `Class` objects with two separate sets of class metadata in Metaspace — even though it's "the same" class name and bytecode on disk. `keepAlive.add(loader)` and `keepAlive.add(generated)` ensure both the classloader and the class stay strongly reachable from `main`'s local state, so none of that metadata is ever eligible for reclamation — this is precisely the shape of a real class-loader leak (e.g., a web app redeploy that never lets go of the old classloader).

Every 1,000 class loads, `printMetaspaceUsage(...)` reports the climbing `used` value. As `totalLoaded` grows into the thousands, each new (classloader, class) pair adds a small, permanent amount of class metadata, driving usage steadily upward.

Notice, though, that `OutOfMemoryError` is thrown while `used` is still well short of the full 48 MB cap — typically somewhere in the mid-20s of MB in the sample run above. This is not a bug in the demo; it reflects how Metaspace is actually managed internally: each distinct classloader gets its own metadata **arena**, allocated in fixed-size chunks, and a classloader that only ever loads one small class still reserves a whole chunk for itself. With thousands of short-lived, single-class `URLClassLoader` instances (exactly what this example creates), the *reserved-but-mostly-empty* chunk space adds up far faster than the *actually-used* bytes `MemoryUsage.getUsed()` reports — so the JVM runs out of usable Metaspace capacity well before the naive "used vs. max" arithmetic would suggest. This is itself a real, well-known Metaspace pitfall: many small, short-lived classloaders (a pattern seen in some poorly-tuned dynamic-proxy or scripting-heavy frameworks) waste far more Metaspace than the same classes loaded through fewer, longer-lived classloaders would.

Once capacity is exhausted, the next attempted class load causes the JVM to throw `OutOfMemoryError` with a message referencing Metaspace — the modern equivalent of the historical `"PermGen space"` message. The `catch (OutOfMemoryError e)` block catches it, prints the message, and explains that reaching this failure now requires an explicit `-XX:MaxMetaspaceSize` flag, rather than being the JVM's unavoidable default behavior the way it was with PermGen.

## 7. Gotchas & takeaways

> Metaspace being "unbounded by default" does **not** mean class-metadata leaks are harmless in Java 8+ — a class-loader leak (e.g., repeatedly reloading a web application without its old classes ever being unloaded) can still exhaust *all available system memory*, which is arguably worse than the old PermGen behavior, since it can affect the entire machine rather than failing cleanly and early inside just the JVM process. Setting `-XX:MaxMetaspaceSize` explicitly in production is still a reasonable defensive practice, trading "possible OOM at a known ceiling" for "unbounded growth risk with no early warning."

- Many small, short-lived classloaders waste Metaspace disproportionately compared to fewer, longer-lived ones — each classloader gets its own metadata arena allocated in chunks, so a classloader holding only one tiny class still reserves a whole chunk, and `OutOfMemoryError: Metaspace` can strike well before `MemoryUsage.getUsed()` nominally reaches a configured cap, as demonstrated in the Level 3 walkthrough.
- The old flag `-XX:MaxPermSize` is simply ignored (with a warning) on Java 8+ — the equivalent flag is `-XX:MaxMetaspaceSize`, and it's optional, unlike `MaxPermSize`, which effectively always had *some* default cap.
- Metaspace lives in **native memory**, not the JVM heap — it doesn't show up in `-Xmx` heap-size calculations or in a heap dump the way PermGen objects used to; use `MemoryPoolMXBean` (as shown above) or tools like `jcmd <pid> VM.metaspace` to inspect it specifically.
- Interned `String` literals, which lived in PermGen pre-Java 7, actually moved to the regular heap starting in Java 7 (before the PermGen-to-Metaspace change) — Metaspace holds *class metadata* specifically (loaded classes, method/field info, constant pool structures), not general string interning.
- Frameworks doing heavy runtime class generation (dynamic proxies, CGLIB/ByteBuddy-based enhancement, some ORM frameworks) are the main beneficiaries of this change — they were the most common source of pre-Java-8 `PermGen space` errors, since every redeploy or generation cycle could add more classes without the old ones being reclaimed.
- If you see `java.lang.OutOfMemoryError: Metaspace` today, the underlying cause and fix are usually the same as the old PermGen equivalent: look for a class-loader leak (classes/class-loaders that should have been garbage-collected but are still referenced somewhere) before reaching for a bigger `-XX:MaxMetaspaceSize` value.
