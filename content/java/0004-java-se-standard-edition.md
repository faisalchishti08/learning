---
card: java
gi: 4
slug: java-se-standard-edition
title: Java SE (Standard Edition)
---

## 1. What it is

**Java SE (Standard Edition)** is the core, baseline platform of the Java ecosystem. It defines the Java language itself, the Java Virtual Machine specification, and the foundational class library — everything from primitive types and collections to I/O, networking, concurrency, and security. When someone says "Java" without qualification, they almost always mean Java SE.

Java SE is defined by a **JSR (Java Specification Request)** — a formal standards process — and implemented by the **JDK (Java Development Kit)**, which includes the compiler (`javac`), the runtime (`java`), and the standard library (`java.*`, `javax.*`, `sun.*` internals).

## 2. Why & when

Java SE is the foundation everything else builds on:
- **Jakarta EE** (enterprise) extends Java SE with web servers, persistence, messaging.
- **Spring Boot** is a framework that runs on the Java SE JVM.
- **Android** (historically) used a subset of Java SE APIs via Dalvik/ART.
- **Apache Spark**, **Elasticsearch**, **Kafka** — all JVM-based applications, all require Java SE underneath.

You use Java SE directly when you write:
- Command-line tools and scripts.
- Libraries distributed as JARs.
- Backend services that use a framework built on top of it.
- Any Java code at all — every Java program is a Java SE program at its core.

## 3. Core concept

Java SE is best understood as five concentric layers:

| Layer | What it contains |
|---|---|
| **Language** | syntax, type system, OOP, generics, lambdas, records, sealed classes |
| **JVM** | bytecode execution, GC, JIT, class loading, security manager |
| **Core libraries** | `java.lang`, `java.util`, `java.io`, `java.nio`, `java.net` |
| **Optional libraries** | `java.sql`, `java.xml`, `java.security`, `java.math` |
| **Tooling** | `javac`, `jar`, `jshell`, `jlink`, `jpackage`, `javadoc` |

The JDK is the distribution of Java SE. Starting with Java 9, the JDK itself is **modularised**: the monolithic `rt.jar` was broken into ~70 named modules (`java.base`, `java.sql`, `java.desktop`, etc.). `java.base` is always present; other modules are opt-in. This means a minimal Java SE runtime can be as small as ~30 MB with `jlink`.

**Release cadence:** Java SE releases every **six months** (March and September). LTS (Long-Term Support) releases — 11, 17, 21, 25 — receive patch support for several years. Non-LTS releases receive patches only until the next release.

## 4. Diagram

<svg viewBox="0 0 620 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java SE concentric layers from language to tooling">
  <!-- Language (outermost) -->
  <ellipse cx="310" cy="130" rx="290" ry="118" fill="none" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="6,3"/>
  <text x="310" y="26" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Tooling (javac, jar, jshell, jlink, jpackage)</text>

  <!-- Optional libs -->
  <ellipse cx="310" cy="130" rx="240" ry="93" fill="none" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="4,3"/>
  <text x="310" y="52" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Optional libs (java.sql, java.xml, java.security)</text>

  <!-- Core libs -->
  <ellipse cx="310" cy="130" rx="185" ry="70" fill="none" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="310" y="74" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Core libs (java.lang, java.util, java.io, java.net)</text>

  <!-- JVM -->
  <ellipse cx="310" cy="130" rx="128" ry="48" fill="none" stroke="#6db33f" stroke-width="1.6"/>
  <text x="310" y="96" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">JVM (GC · JIT · classloader)</text>

  <!-- Language (innermost) -->
  <ellipse cx="310" cy="130" rx="70" ry="28" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="310" y="126" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Language</text>
  <text x="310" y="143" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">syntax · types · OOP</text>
</svg>

Java SE as concentric layers: the language is the innermost core; tooling is the outermost support ring.

## 5. Runnable example

Scenario: a self-contained program that exercises one class from each core Java SE layer — proving that every layer is available in any standard Java SE installation.

### Level 1 — Basic

```java
// JavaSELayers.java
import java.util.*;
import java.io.*;

public class JavaSELayers {
    public static void main(String[] args) {
        // java.lang (always auto-imported)
        String msg = "Hello from Java SE " + Runtime.version().feature();

        // java.util
        List<String> modules = List.of("java.lang", "java.util", "java.io", "java.net");

        // java.io
        PrintWriter out = new PrintWriter(System.out, true);

        out.println(msg);
        out.println("Core modules: " + modules);
        out.println("Available processors: " + Runtime.getRuntime().availableProcessors());
    }
}
```

**How to run:** `java JavaSELayers.java`

`Runtime.version().feature()` returns the Java major version (21, 17, etc.) — a clean API added in Java 9 replacing the `"1.x"` string parsing gymnastics.

### Level 2 — Intermediate

Same Java SE layer probe, extended to use `java.math`, `java.net`, and the module system API to list loaded modules.

```java
// JavaSEProbe.java
import java.util.*;
import java.math.*;
import java.nio.file.*;
import java.lang.module.*;

public class JavaSEProbe {
    public static void main(String[] args) {
        System.out.println("=== Java SE Layer Probe ===");

        // java.lang
        System.out.println("\n[java.lang]");
        Runtime.Version v = Runtime.version();
        System.out.printf("  Java %d (build %s)%n", v.feature(), v);

        // java.util
        System.out.println("\n[java.util]");
        Map<String, Long> data = new TreeMap<>(Map.of("alpha", 1L, "beta", 2L, "gamma", 3L));
        data.forEach((k, val) -> System.out.printf("  %-6s -> %d%n", k, val));

        // java.math
        System.out.println("\n[java.math]");
        BigInteger factorial20 = BigInteger.ONE;
        for (int i = 2; i <= 20; i++) factorial20 = factorial20.multiply(BigInteger.valueOf(i));
        System.out.println("  20! = " + factorial20);

        // java.lang.module (Java 9+)
        System.out.println("\n[java.lang.module — loaded modules sample]");
        ModuleLayer.boot().modules().stream()
            .map(Module::getName)
            .sorted()
            .limit(8)
            .forEach(m -> System.out.println("  " + m));
        System.out.println("  ... (" + ModuleLayer.boot().modules().size() + " total)");
    }
}
```

**How to run:** `java JavaSEProbe.java`

`ModuleLayer.boot().modules()` lists the modules loaded in the boot layer — the Java SE modules the JVM started with. On a full JDK install you see ~70; a `jlink`-trimmed runtime may show ~10.

### Level 3 — Advanced

Same scenario grown to a full Java SE capability audit: probes each layer with meaningful work, measures garbage collector info from the management API, and checks which GC algorithm is active — relevant for tuning production JVMs.

```java
// JavaSEAudit.java
import java.util.*;
import java.math.*;
import java.nio.file.*;
import java.lang.management.*;
import java.lang.module.*;

public class JavaSEAudit {
    public static void main(String[] args) throws Exception {
        System.out.println("╔═══════════════════════════════════╗");
        System.out.println("║       Java SE Capability Audit    ║");
        System.out.println("╚═══════════════════════════════════╝\n");

        // ─── Language layer ──────────────────
        System.out.println("[ Language ]");
        // Records (Java 16+), sealed classes (Java 17+), pattern matching (Java 21+)
        record Point(double x, double y) {
            double distanceTo(Point other) {
                double dx = this.x - other.x, dy = this.y - other.y;
                return Math.sqrt(dx * dx + dy * dy);
            }
        }
        Point a = new Point(0, 0), b = new Point(3, 4);
        System.out.printf("  Record Point: %s  distance to %s = %.1f%n", a, b, a.distanceTo(b));

        // ─── JVM layer ───────────────────────
        System.out.println("\n[ JVM — Memory & GC ]");
        MemoryMXBean mem = ManagementFactory.getMemoryMXBean();
        System.out.printf("  Heap used/committed: %d MB / %d MB%n",
            mem.getHeapMemoryUsage().getUsed() / (1024*1024),
            mem.getHeapMemoryUsage().getCommitted() / (1024*1024));
        List<GarbageCollectorMXBean> gcs = ManagementFactory.getGarbageCollectorMXBeans();
        for (GarbageCollectorMXBean gc : gcs) {
            System.out.printf("  GC: %-30s  collections=%d  time=%dms%n",
                gc.getName(), gc.getCollectionCount(), gc.getCollectionTime());
        }

        // ─── Core libraries layer ────────────
        System.out.println("\n[ Core Libraries ]");
        // java.math
        BigDecimal pi = new BigDecimal("3.14159265358979323846");
        System.out.println("  pi (BigDecimal 20dp): " + pi);

        // java.nio
        Path tmpFile = Files.createTempFile("jse-audit-", ".txt");
        Files.writeString(tmpFile, "Java SE I/O test\n");
        System.out.println("  NIO write+read OK: " + Files.readString(tmpFile).strip());
        Files.delete(tmpFile);

        // ─── Module system ───────────────────
        System.out.println("\n[ Module System (Java 9+) ]");
        long moduleCount = ModuleLayer.boot().modules().size();
        System.out.println("  Boot layer modules loaded: " + moduleCount);
        Optional<Module> javaBase = ModuleLayer.boot().findModule("java.base");
        javaBase.ifPresent(m -> System.out.println("  java.base packages: " + m.getPackages().size()));

        // ─── Version ─────────────────────────
        System.out.println("\n[ Version & LTS status ]");
        Runtime.Version rv = Runtime.version();
        System.out.printf("  Java %d.%d (build: %s)%n", rv.feature(), rv.interim(), rv);
        int feat = rv.feature();
        boolean isLts = feat == 8 || feat == 11 || feat == 17 || feat == 21 || feat == 25;
        System.out.println("  LTS release: " + isLts);
    }
}
```

**How to run:** `java JavaSEAudit.java`

The **local record** inside `main` showcases a Java 16+ feature (records are a concise immutable data class). `GarbageCollectorMXBean` exposes live GC statistics — on a warm JVM you'd see collection counts incrementing, useful for diagnosing GC pressure.

## 6. Walkthrough

Execution flows linearly through the audit blocks:

1. **Language layer** — `record Point(double x, double y)` is a local record: the compiler auto-generates constructor, accessors, `equals`, `hashCode`, `toString`. `distanceTo` is an explicit instance method on top. `Math.sqrt` is `java.lang.Math` — the most basic of the standard library.

2. **JVM layer** — `ManagementFactory.getMemoryMXBean()` and `getGarbageCollectorMXBeans()` are the JMX (Java Management Extensions) APIs, part of `java.management` module. On a server you'd expose these via JMX over a remote port; here we query them locally. GC names like `"G1 Young Generation"` or `"ZGC Cycles"` tell you which GC algorithm is active without needing JVM flags.

3. **Core libraries layer** — `BigDecimal` (from `java.math`) stores `pi` without floating-point rounding error. `Files.createTempFile` (from `java.nio.file`) creates a real OS temp file; `Files.writeString` / `Files.readString` (Java 11+) are the modern NIO.2 convenience API — no boilerplate `OutputStream` wrapping.

4. **Module system** — `ModuleLayer.boot()` is the bootstrap layer, populated when the JVM starts based on `--module-path` and `--add-modules`. `findModule("java.base")` always succeeds; `.getPackages()` lists the 200+ packages exported from `java.base` alone.

5. **Version block** — `Runtime.version()` returns a structured `Version` object (not a string). `.feature()` is the major number; `.interim()` is the minor. This API was added in Java 9 precisely to end the `"1.x"` string parsing chaos.

Data flow: `main → ManagementFactory → JVM MXBean → GC stats back to main → formatted output`.

## 7. Gotchas & takeaways

> Java SE version numbers changed at Java 9. `System.getProperty("java.version")` returns `"1.8.0_362"` for Java 8 but `"21.0.2"` for Java 21. Use `Runtime.version().feature()` (Java 9+) for a clean integer major version.

> `java.base` is always present and never needs `requires` in `module-info.java`. All other modules must be declared. Forgetting `requires java.sql` is a common mistake when moving to a modular project.

- Java SE = language + JVM + standard library + tooling. It is the complete definition of "Java."
- The JDK is the distribution; multiple distributions exist (OpenJDK, Temurin, Corretto, Oracle JDK).
- Since Java 9, the JDK is modular: use `jlink` to build a custom minimal runtime containing only the modules you need.
- LTS releases (8, 11, 17, 21, 25) are the safe choice for production; non-LTS releases expire in 6 months.
- `ManagementFactory` provides live JVM internals (memory, GC, threads) — essential for diagnostics and health endpoints.
- Records (Java 16), sealed classes (Java 17), pattern matching (Java 21) show Java SE continues evolving; use an LTS that supports the features you need.
