---
card: java
gi: 14
slug: graalvm
title: GraalVM
---

## 1. What it is

**GraalVM** is a high-performance JDK distribution from Oracle that extends standard Java in two major ways:

1. **Graal JIT compiler** — replaces HotSpot's C2 JIT with a compiler written in Java, offering better peak performance for some workloads.
2. **Native Image** — an ahead-of-time (AOT) compiler that compiles Java bytecode into a standalone native executable with no JVM required at runtime, providing near-instant startup (milliseconds) and very low memory usage.

GraalVM also supports **polyglot execution** via Truffle: it can run Python, Ruby, R, JavaScript, and LLVM bitcode (C/C++ compiled to LLVM IR) on the same JVM, sharing objects and calling across languages.

Two editions exist: **GraalVM Community** (free, GPL + CPE) and **GraalVM Enterprise** (paid Oracle license).

## 2. Why & when

GraalVM matters most in two scenarios:

**Native Image for cloud/serverless:**
- AWS Lambda cold starts in milliseconds instead of seconds.
- Quarkus and Micronaut are designed to compile to GraalVM Native Image for sub-100 ms startup.
- Docker images can be as small as 10–30 MB (no JVM bundled).

**Peak JIT performance:**
- The Graal JIT excels at workloads involving heavy method inlining, especially frameworks that use lots of reflection and annotation processing (Spring, Hibernate).
- Oracle offers **GraalVM Enterprise** with profile-guided optimization (PGO) for additional speedup.

You do NOT need GraalVM for:
- Standard long-running services where HotSpot's C2 is already well-tuned.
- Applications that use unsupported reflection patterns (many frameworks need configuration to work with Native Image).

## 3. Core concept

GraalVM's two compilation modes have fundamentally different trade-offs:

```
                  JVM mode (standard)          Native Image (AOT)
                  ──────────────────────────   ──────────────────────────
Compilation       bytecode → JIT at runtime    bytecode → native binary at build time
Startup           seconds (JVM init + JIT)     milliseconds (no JVM)
Throughput        excellent (JIT adapts)        good (no adaptive optimisation)
Memory            JVM overhead (~50 MB min)     tiny (~5–50 MB)
Dynamic loading   works out of the box          requires reflection config
Polyglot          yes (Truffle languages)        limited
```

**The Closed World Assumption** is Native Image's key constraint: the AOT compiler must know all reachable code at build time. Dynamic class loading, reflection, and `Class.forName` without configuration confuse the static analyser. You must provide a `reflection-config.json` (or use the GraalVM Tracing Agent) for any reflection the app uses.

**Truffle** is a framework for building language interpreters that can be JIT-compiled by the Graal compiler via partial evaluation — this is how Python/Ruby/JS run fast on GraalVM.

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GraalVM two paths: JVM mode with Graal JIT vs Native Image AOT compilation">
  <defs>
    <marker id="agvm" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="agvm2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
  <!-- Source -->
  <rect x="260" y="20" width="160" height="44" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="340" y="42" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Java source (.java)</text>
  <text x="340" y="56" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">compiled to bytecode (.class)</text>

  <!-- Fork -->
  <line x1="310" y1="64" x2="180" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#agvm)"/>
  <line x1="370" y1="64" x2="500" y2="105" stroke="#f0883e" stroke-width="1.5" marker-end="url(#agvm2)"/>

  <!-- JVM mode -->
  <rect x="40"  y="108" width="260" height="85" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="170" y="130" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">JVM mode</text>
  <text x="170" y="148" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Graal JIT compiler</text>
  <text x="170" y="163" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">startup: seconds · peak throughput: best</text>
  <text x="170" y="176" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">heap: standard JVM · polyglot: YES</text>
  <text x="170" y="189" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">dynamic class loading: YES</text>

  <!-- Native Image mode -->
  <rect x="380" y="108" width="280" height="85" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="520" y="130" fill="#f0883e" font-size="12" text-anchor="middle" font-family="sans-serif">Native Image (AOT)</text>
  <text x="520" y="148" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">native-image tool → executable</text>
  <text x="520" y="163" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">startup: milliseconds · memory: tiny</text>
  <text x="520" y="176" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">no JVM needed at runtime</text>
  <text x="520" y="189" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">reflection needs config · closed world</text>

  <!-- Labels -->
  <text x="170" y="218" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Best for: long-running services</text>
  <text x="520" y="218" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Best for: Lambda · CLI · microservices</text>
</svg>

Two paths from the same bytecode: JVM mode for throughput, Native Image for startup and footprint.

## 5. Runnable example

Scenario: a program that detects whether it's running in GraalVM JVM mode or as a Native Image, and demonstrates the key difference in startup characteristics.

### Level 1 — Basic

```java
// GraalVmCheck.java
public class GraalVmCheck {
    public static void main(String[] args) {
        String vmName = System.getProperty("java.vm.name", "");
        String vendor = System.getProperty("java.vendor", "");
        boolean isGraalJit     = vmName.contains("GraalVM") || vendor.contains("GraalVM");
        boolean isNativeImage  = System.getProperty("org.graalvm.nativeimage.imagecode") != null;

        System.out.println("VM name        : " + vmName);
        System.out.println("Vendor         : " + vendor);
        System.out.println("GraalVM JIT    : " + isGraalJit);
        System.out.println("Native Image   : " + isNativeImage);

        if (isNativeImage) {
            System.out.println("Running as GraalVM Native Image — no JVM present at runtime.");
        } else if (isGraalJit) {
            System.out.println("Running on GraalVM JVM mode — Graal compiler active.");
        } else {
            System.out.println("Running on standard HotSpot JVM.");
        }
    }
}
```

**How to run:** `java GraalVmCheck.java`

`org.graalvm.nativeimage.imagecode` is set to `"runtime"` when executing a Native Image binary. Its absence means standard JVM mode. `java.vm.name` contains `"GraalVM"` when running GraalVM JVM mode (Community or Enterprise).

### Level 2 — Intermediate

Same check extended to demonstrate the Closed World Assumption — show what happens when reflection is used without configuration, and how to detect whether a class is available at runtime.

```java
// GraalClosedWorld.java
public class GraalClosedWorld {

    public static void main(String[] args) {
        System.out.println("=== GraalVM Closed World Demo ===");
        System.out.println("Mode: " + runtimeMode());
        System.out.println();

        // In Native Image without reflection config, Class.forName of a dynamic name fails
        // This simulates what frameworks like Spring do with component scanning
        String[] classesToProbe = {
            "java.util.ArrayList",           // in java.base — always available
            "java.sql.DriverManager",        // java.sql module — may not be included
            "com.example.MyService",         // hypothetical app class — not on classpath
            "org.springframework.context.ApplicationContext"  // Spring — not on classpath here
        };

        System.out.printf("%-52s  %-10s  %s%n", "Class", "Available", "Note");
        System.out.println("-".repeat(90));
        for (String cn : classesToProbe) {
            boolean found = classExists(cn);
            String note = noteForClass(cn, found);
            System.out.printf("%-52s  %-10s  %s%n", cn, found ? "YES" : "NO", note);
        }

        System.out.println("\nNative Image note: classes NOT in the reflection-config.json");
        System.out.println("are removed from the binary even if present at build time.");
    }

    static boolean classExists(String name) {
        try { Class.forName(name); return true; }
        catch (ClassNotFoundException e) { return false; }
    }

    static String noteForClass(String cn, boolean found) {
        if (cn.equals("java.util.ArrayList")) return "java.base always present";
        if (cn.equals("java.sql.DriverManager")) return found ? "java.sql module loaded" : "java.sql module absent (jlink trimmed?)";
        if (cn.contains("example"))  return "not on classpath (expected)";
        if (cn.contains("springframework")) return "not on classpath (expected)";
        return "";
    }

    static String runtimeMode() {
        if (System.getProperty("org.graalvm.nativeimage.imagecode") != null) return "Native Image";
        if (System.getProperty("java.vm.name","").contains("GraalVM")) return "GraalVM JVM";
        return "Standard HotSpot";
    }
}
```

**How to run:** `java GraalClosedWorld.java`

If this were compiled to Native Image without a reflection config listing `java.sql.DriverManager`, the `Class.forName` call would throw `ClassNotFoundException` at runtime even though the class was present at compile time.

### Level 3 — Advanced

Same scenario grown to a full GraalVM compatibility audit — checks for common Native Image pitfalls (reflection, resource bundles, dynamic proxies), profiles startup time, and generates a partial `reflect-config.json`.

```java
// GraalCompatibilityAudit.java
import java.util.*;
import java.lang.reflect.*;

public class GraalCompatibilityAudit {

    record ReflectionCheck(String className, boolean found, String[] accessedMembers) {}

    public static void main(String[] args) throws Exception {
        long startNs = System.nanoTime();

        System.out.println("╔══════════════════════════════════════════╗");
        System.out.println("║   GraalVM Native Image Compatibility      ║");
        System.out.println("╚══════════════════════════════════════════╝\n");

        String mode = runtimeMode();
        System.out.println("Runtime mode : " + mode);
        System.out.println("Java version : " + Runtime.version());

        // ── Reflection usage audit ──────────────────────────────
        System.out.println("\n[ Reflection Usage Audit ]");
        List<ReflectionCheck> checks = List.of(
            probeClass("java.util.ArrayList",           new String[]{"size", "add", "get"}),
            probeClass("java.lang.String",              new String[]{"length", "charAt", "substring"}),
            probeClass("java.util.HashMap",             new String[]{"put", "get", "size"}),
            probeClass("java.time.LocalDate",           new String[]{"now", "parse", "toString"})
        );

        System.out.printf("  %-40s  %-8s  Members%n", "Class", "Found");
        System.out.println("  " + "-".repeat(75));
        for (ReflectionCheck c : checks) {
            System.out.printf("  %-40s  %-8s  %s%n",
                c.className(), c.found() ? "YES" : "NO",
                c.found() ? String.join(", ", c.accessedMembers()) : "—");
        }

        // ── Partial reflect-config.json output ──────────────────
        System.out.println("\n[ Sample reflect-config.json entries for Native Image ]");
        System.out.println("  (add to src/main/resources/META-INF/native-image/)");
        System.out.println("  [");
        boolean first = true;
        for (ReflectionCheck c : checks) {
            if (!c.found()) continue;
            if (!first) System.out.println("  ,");
            System.out.println("    {");
            System.out.println("      \"name\": \"" + c.className() + "\",");
            System.out.println("      \"allDeclaredConstructors\": true,");
            System.out.println("      \"allPublicMethods\": true");
            System.out.print("    }");
            first = false;
        }
        System.out.println("\n  ]");

        // ── Dynamic proxy check ─────────────────────────────────
        System.out.println("\n[ Dynamic Proxy Check ]");
        try {
            Object proxy = Proxy.newProxyInstance(
                GraalCompatibilityAudit.class.getClassLoader(),
                new Class[]{Runnable.class},
                (p, m, a) -> { System.out.println("  proxy method: " + m.getName()); return null; }
            );
            ((Runnable) proxy).run();
            System.out.println("  Dynamic proxy works in JVM mode.");
            System.out.println("  Native Image: add to proxy-config.json: [{\"interfaces\":[\"java.lang.Runnable\"]}]");
        } catch (Exception e) {
            System.out.println("  Dynamic proxy failed: " + e.getMessage());
        }

        // ── Startup time ─────────────────────────────────────────
        long startupMs = (System.nanoTime() - startNs) / 1_000_000;
        System.out.println("\n[ Startup Characteristics ]");
        System.out.printf("  Time from main() to here : %d ms%n", startupMs);
        System.out.println("  Native Image equivalent  : typically 5–50 ms total");
        System.out.println("  JVM mode equivalent      : this + JVM startup (~200–500 ms)");
    }

    static ReflectionCheck probeClass(String name, String[] members) {
        try {
            Class<?> cls = Class.forName(name);
            // verify members exist
            for (String m : members) {
                boolean found = Arrays.stream(cls.getMethods()).anyMatch(mt -> mt.getName().equals(m));
                if (!found) return new ReflectionCheck(name, true, new String[]{m + " NOT FOUND"});
            }
            return new ReflectionCheck(name, true, members);
        } catch (ClassNotFoundException e) {
            return new ReflectionCheck(name, false, new String[0]);
        }
    }

    static String runtimeMode() {
        if (System.getProperty("org.graalvm.nativeimage.imagecode") != null) return "GraalVM Native Image";
        if (System.getProperty("java.vm.name","").contains("GraalVM")) return "GraalVM JVM mode";
        return "Standard HotSpot JVM";
    }
}
```

**How to run:** `java GraalCompatibilityAudit.java`

In production, you'd run this with the GraalVM Tracing Agent (`-agentlib:native-image-agent=config-output-dir=./config`) to auto-generate the complete `reflect-config.json`, `proxy-config.json`, and `resource-config.json` files.

## 6. Walkthrough

Execution in `GraalCompatibilityAudit.main`:

1. **Runtime mode detection** — `org.graalvm.nativeimage.imagecode` is set to `"buildtime"` during `native-image` compilation and to `"runtime"` when the resulting binary executes. `java.vm.name` contains `"GraalVM"` in JVM mode. Standard HotSpot JVM has neither.

2. **Reflection audit** — `probeClass(name, members)` calls `Class.forName(name)` (the core reflective operation that Native Image must be told about) then verifies each method exists via `getMethods()`. In Native Image without config, `Class.forName` of a class not listed in `reflect-config.json` throws `ClassNotFoundException` even if the class was on the classpath at build time.

3. **reflect-config.json generation** — the output is a JSON snippet that tells `native-image` to include these classes and their methods in the native binary's metadata. In practice: `src/main/resources/META-INF/native-image/reflect-config.json` or auto-generated via the tracing agent.

4. **Dynamic proxy** — `Proxy.newProxyInstance` creates a runtime-generated class implementing `Runnable`. Native Image's static analyser cannot see this class at build time unless you list the interface in `proxy-config.json`. Without it, Native Image produces `IllegalArgumentException: cannot create proxy for interface not registered`.

5. **Startup timing** — `System.nanoTime()` at the top and bottom of `main` measures JVM-mode startup overhead (everything after the JVM itself started). In Native Image, the binary starts, the OS loads it, and `main` runs — typical wall-clock startup is 5–50 ms total vs 200–2000 ms for a JVM-mode application.

Native Image AOT flow:
```
javac → .class bytecode
  ↓ native-image (analysis phase)
  Static reachability analysis (closed world)
  + reads reflect-config.json / proxy-config.json
  ↓ (compilation phase, can take minutes)
  Native executable (ELF on Linux, Mach-O on macOS)
  ↓ (runtime: no JVM)
  Instant startup · tiny heap
```

## 7. Gotchas & takeaways

> **Native Image's closed world breaks dynamic frameworks.** Hibernate, Spring, and Jackson all use reflection heavily. Without a `reflect-config.json` (or GraalVM Tracing Agent run), they fail at startup in Native Image mode. Quarkus and Micronaut solve this by generating the config at build time.

> **`native-image` compilation is slow (minutes for large apps) and memory-hungry (~4–8 GB heap).** It is not a drop-in replacement for `javac`; it is a separate build step that produces a release artifact.

- GraalVM has two modes: JVM (Graal JIT replaces C2) and Native Image (AOT, no JVM at runtime).
- Native Image: millisecond startup, tiny memory, closed world — requires reflection/proxy/resource config.
- GraalVM Tracing Agent auto-generates config by running the app on a standard JVM and recording all reflective accesses.
- Quarkus and Micronaut are frameworks designed for GraalVM Native Image — they generate the config at build time.
- Polyglot (Python/Ruby/JS on GraalVM JVM) uses Truffle; not available in Native Image (mostly).
- GraalVM Community (free) vs GraalVM Enterprise (paid, PGO): for most users Community is sufficient.
