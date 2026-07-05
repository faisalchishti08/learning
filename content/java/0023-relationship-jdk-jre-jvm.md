---
card: java
gi: 23
slug: relationship-jdk-jre-jvm
title: Relationship JDK ⊃ JRE ⊃ JVM
---

## 1. What it is

The JDK, JRE, and JVM form a strict containment hierarchy: **JDK ⊃ JRE ⊃ JVM**. Each inner layer is a complete subset of the outer layer, and each outer layer adds capabilities on top:

- **JVM** (innermost) — the execution engine: class loading, bytecode verification, JIT compilation, garbage collection. Pure runtime, no files of its own beyond the executable binary.
- **JRE** (middle) — JVM + the Java standard library (`java.*` class files, native libraries, security configuration). Everything needed to **run** a Java program.
- **JDK** (outermost) — JRE + development tools: `javac`, `jar`, `jshell`, `jlink`, `jpackage`, diagnostics, JNI headers, source code. Everything needed to **develop** Java programs.

## 2. Why & when

Confusing these three layers causes real problems in practice:

- Installing only a JRE on a CI server and wondering why `mvn package` fails — Maven calls `javac`, which is in the JDK only.
- Shipping a Docker image with the full JDK in production — 400 MB when a 170 MB JRE image would work.
- Setting `JAVA_HOME` to a JRE path in a build script — `javac` is not there, so the build fails mysteriously.
- Asking "does the JVM include the compiler?" — no, the JVM is a runtime-only abstraction.

Understanding the hierarchy clarifies which tool belongs where and what minimum installation is needed for a given task.

## 3. Core concept

Analogy: a **kitchen** hierarchy.

- The **oven** (JVM) is the appliance that cooks (executes) food (bytecode). It does only one thing: cook.
- A **complete kitchen** (JRE) has the oven plus all the ingredients (standard library) and utensils (native libraries) needed to serve a meal. You can serve food but not develop new recipes.
- A **chef's workshop** (JDK) has the complete kitchen plus chef's tools: knives, a food processor, recipe books, nutrition analyser — everything to **create** meals (programs), not just serve them.

Formally:

```
JDK
├── JRE
│   ├── JVM
│   │   ├── Class loader subsystem
│   │   ├── Bytecode verifier
│   │   ├── Execution engine (interpreter + JIT)
│   │   ├── Garbage collector
│   │   └── Runtime data areas (heap, stacks, method area)
│   │
│   ├── Java class library (java.base, java.util, java.io, ...)
│   ├── Native libraries (crypto, networking, AWT/fonts)
│   └── Configuration (security policy, logging)
│
├── javac (compiler)
├── jar (packager)
├── jshell (REPL)
├── jlink (custom JRE builder)
├── jpackage (native installer)
├── jcmd / jstack / jmap / jfr (diagnostics)
├── jdeps (dependency analyser)
├── javadoc (documentation)
├── jdb (debugger)
└── include/ (JNI headers)
```

**Decision rule:** Use the smallest layer that satisfies your need:
- Need to run a JAR? → JRE (or a `jlink` image).
- Need to compile + run? → JDK.
- Need to diagnose a running JVM? → JDK (for `jcmd`/`jstack`) or JRE with JFR.

## 4. Diagram

<svg viewBox="0 0 640 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JDK contains JRE which contains JVM — three nested boxes with labels">
  <!-- JDK (outermost) -->
  <rect x="20" y="20" width="600" height="250" rx="12" fill="#1c2430" stroke="#6db33f" stroke-width="2.5"/>
  <text x="320" y="46" fill="#6db33f" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">JDK — Java Development Kit</text>
  <!-- JDK tools labels -->
  <text x="540" y="80"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">javac</text>
  <text x="540" y="95"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">jar</text>
  <text x="540" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">jshell</text>
  <text x="540" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">jlink</text>
  <text x="540" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">jcmd</text>
  <text x="540" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">jstack</text>
  <text x="540" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">javadoc</text>

  <!-- JRE (middle) -->
  <rect x="60" y="60" width="450" height="196" rx="10" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/>
  <text x="285" y="84" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">JRE — Java Runtime Environment</text>
  <!-- JRE labels -->
  <text x="430" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">java.base</text>
  <text x="430" y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">java.util</text>
  <text x="430" y="146" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">java.io</text>
  <text x="430" y="160" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">java.net</text>
  <text x="430" y="174" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">crypto libs</text>

  <!-- JVM (innermost) -->
  <rect x="100" y="100" width="290" height="138" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="245" y="122" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">JVM — Java Virtual Machine</text>
  <!-- JVM internals -->
  <text x="145" y="150" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ClassLoader</text>
  <text x="245" y="150" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Verifier</text>
  <text x="340" y="150" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">JIT (C1/C2)</text>
  <text x="145" y="178" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">GC (G1/ZGC)</text>
  <text x="245" y="178" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Heap · Stack</text>
  <text x="340" y="178" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Method Area</text>
  <text x="245" y="222" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">executes bytecode</text>
</svg>

Strict nesting: JVM executes, JRE runs programs, JDK develops programs.

## 5. Runnable example

Scenario: a self-diagnostic program that identifies which layer is running and which operations are possible — a practical guide for environment setup.

### Level 1 — Basic

```java
// LayerCheck.java
import java.nio.file.*;

public class LayerCheck {
    public static void main(String[] args) throws Exception {
        Path binDir = Path.of(System.getProperty("java.home"), "bin");

        boolean hasJvm   = true;  // we're running, so JVM must exist
        boolean hasJre   = classExists("java.util.ArrayList");
        boolean hasJavac = Files.exists(binDir.resolve("javac")) || Files.exists(binDir.resolve("javac.exe"));
        boolean hasJlink = Files.exists(binDir.resolve("jlink")) || Files.exists(binDir.resolve("jlink.exe"));

        System.out.println("JVM present    : " + hasJvm   + "  (always true — we're running)");
        System.out.println("JRE present    : " + hasJre   + "  (java.util.ArrayList in class library)");
        System.out.println("JDK present    : " + hasJavac + "  (javac compiler in bin/)");
        System.out.println("jlink present  : " + hasJlink + "  (custom JRE builder)");
        System.out.println();
        System.out.println("Layer: " + (hasJavac ? "JDK (full)" : "JRE (runtime only)"));
    }

    static boolean classExists(String name) {
        try { Class.forName(name); return true; }
        catch (ClassNotFoundException e) { return false; }
    }
}
```

**How to run:** `java LayerCheck.java`

By definition, if this program runs, the JVM and JRE are present. Only `javac` presence distinguishes JDK from JRE.

### Level 2 — Intermediate

Same layer check extended to demonstrate what each layer can and cannot do — a practical capability matrix.

```java
// LayerCapabilities.java
import java.io.*;
import java.nio.file.*;
import java.lang.management.*;
import java.util.*;

public class LayerCapabilities {

    record Capability(String name, String layer, boolean available, String ifMissing) {}

    public static void main(String[] args) throws Exception {
        Path binDir = Path.of(System.getProperty("java.home"), "bin");

        List<Capability> caps = List.of(
            // JVM capabilities
            new Capability("Execute bytecode",       "JVM", true,  "not applicable — JVM required"),
            new Capability("Garbage collection",      "JVM", true,  "not applicable — GC is JVM"),
            new Capability("JIT compilation",         "JVM", true,  "not applicable"),

            // JRE capabilities
            new Capability("java.util.ArrayList",    "JRE", classExists("java.util.ArrayList"),     "class library missing"),
            new Capability("java.net.http.HttpClient","JRE", classExists("java.net.http.HttpClient"), "add java.net.http module"),
            new Capability("java.sql.DriverManager", "JRE", classExists("java.sql.DriverManager"),  "add java.sql module"),

            // JDK capabilities
            new Capability("javac compiler",         "JDK", toolExists(binDir, "javac"),    "install JDK"),
            new Capability("jar tool",               "JDK", toolExists(binDir, "jar"),      "install JDK"),
            new Capability("jlink tool",             "JDK", toolExists(binDir, "jlink"),    "install JDK"),
            new Capability("jcmd diagnostics",       "JDK", toolExists(binDir, "jcmd"),     "install JDK"),
            new Capability("jshell REPL",            "JDK", toolExists(binDir, "jshell"),   "install JDK"),
            new Capability("javadoc generator",      "JDK", toolExists(binDir, "javadoc"),  "install JDK")
        );

        System.out.println("=== JDK ⊃ JRE ⊃ JVM Capability Matrix ===\n");
        System.out.printf("%-35s  %-5s  %-10s  %s%n", "Capability", "Layer", "Available", "If missing");
        System.out.println("-".repeat(80));
        caps.forEach(c -> System.out.printf("%-35s  %-5s  %-10s  %s%n",
            c.name(), c.layer(), c.available() ? "YES" : "NO", c.available() ? "" : c.ifMissing()));

        System.out.println("\n[ Recommended setup for each use case ]");
        System.out.println("  Running a JAR in production  : JRE or jlink image");
        System.out.println("  CI/CD build pipeline         : JDK (needs javac)");
        System.out.println("  Developer laptop             : JDK (javac + jshell + jdb)");
        System.out.println("  Docker prod container        : eclipse-temurin:21-jre (~170 MB)");
        System.out.println("  Docker build container       : eclipse-temurin:21-jdk (~400 MB)");
    }

    static boolean classExists(String name) {
        try { Class.forName(name); return true; } catch (ClassNotFoundException e) { return false; }
    }
    static boolean toolExists(Path bin, String name) {
        return Files.exists(bin.resolve(name)) || Files.exists(bin.resolve(name + ".exe"));
    }
}
```

**How to run:** `java LayerCapabilities.java`

Running this on a JRE shows `NO` for all JDK tools, helping diagnose why a build is failing on a misconfigured CI server.

### Level 3 — Advanced

Same scenario grown to provide a full environment validation and recommended remediation — the kind of script a devops team adds to their deployment checklist.

```java
// JavaEnvironmentValidator.java
import java.io.*;
import java.lang.management.*;
import java.nio.file.*;
import java.util.*;

public class JavaEnvironmentValidator {

    enum UseCase { DEVELOPMENT, CI_BUILD, PRODUCTION_CONTAINER, DIAGNOSTIC }

    public static void main(String[] args) throws Exception {
        System.out.println("╔══════════════════════════════════════════════════╗");
        System.out.println("║        Java Environment Validator                ║");
        System.out.println("╚══════════════════════════════════════════════════╝\n");

        Path javaHome = Path.of(System.getProperty("java.home"));
        Path binDir   = javaHome.resolve("bin");
        int  feature  = Runtime.version().feature();

        // Detect environment
        System.out.println("[ Environment ]");
        System.out.println("  JAVA_HOME     : " + javaHome);
        System.out.println("  Java version  : " + Runtime.version());
        System.out.println("  Vendor        : " + System.getProperty("java.vendor"));

        boolean hasJavac  = toolExists(binDir, "javac");
        boolean hasJlink  = toolExists(binDir, "jlink");
        boolean hasJcmd   = toolExists(binDir, "jcmd");
        boolean hasJshell = toolExists(binDir, "jshell");
        boolean hasJfr    = moduleExists("jdk.jfr");
        boolean isLts     = Set.of(8, 11, 17, 21, 25).contains(feature);

        String layer = hasJavac ? "Full JDK" : "JRE (runtime only)";
        System.out.println("  Layer         : " + layer);

        // Validate per use case
        System.out.println("\n[ Use Case Validation ]");
        validate("Development", UseCase.DEVELOPMENT, hasJavac, hasJshell, hasJlink, isLts, feature);
        validate("CI/CD Build", UseCase.CI_BUILD, hasJavac, hasJshell, hasJlink, isLts, feature);
        validate("Production Container", UseCase.PRODUCTION_CONTAINER, hasJavac, hasJshell, hasJlink, isLts, feature);
        validate("Diagnostics/OPS", UseCase.DIAGNOSTIC, hasJcmd, hasJfr, true, isLts, feature);

        // Memory health
        System.out.println("\n[ JVM Memory Health ]");
        MemoryMXBean m = ManagementFactory.getMemoryMXBean();
        long heapMax  = m.getHeapMemoryUsage().getMax();
        long heapUsed = m.getHeapMemoryUsage().getUsed();
        double heapPct = heapMax > 0 ? (heapUsed * 100.0 / heapMax) : 0;
        System.out.printf("  Heap: %d MB / %d MB (%.0f%% used)  %s%n",
            heapUsed/(1<<20), heapMax/(1<<20), heapPct,
            heapPct > 85 ? "⚠ HIGH — tune -Xmx" : "OK");

        // GC
        ManagementFactory.getGarbageCollectorMXBeans().forEach(gc ->
            System.out.printf("  GC: %-28s  collections=%d%n", gc.getName(), gc.getCollectionCount()));
    }

    static void validate(String label, UseCase uc, boolean... conditions) {
        boolean ok;
        String recommendation;
        switch (uc) {
            case DEVELOPMENT -> {
                ok = conditions[0] && conditions[1];  // javac + jshell
                recommendation = ok ? "OK" : "Install full JDK (need javac + jshell)";
            }
            case CI_BUILD -> {
                ok = conditions[0];  // javac required
                recommendation = ok ? "OK" : "Install JDK — CI needs javac to compile";
            }
            case PRODUCTION_CONTAINER -> {
                ok = !conditions[0];  // NOT having javac is ideal (JRE-only)
                recommendation = ok ? "OK — JRE-only image (no compiler = smaller attack surface)"
                    : "Consider eclipse-temurin:21-jre instead of full JDK";
            }
            case DIAGNOSTIC -> {
                ok = conditions[0] && conditions[1];  // jcmd + jfr
                recommendation = ok ? "OK (jcmd + JFR available)" : "Install full JDK for jcmd/jstack/jmap";
            }
            default -> { ok = false; recommendation = "unknown use case"; }
        }
        System.out.printf("  %-25s %s  %s%n", label, ok ? "[PASS]" : "[WARN]", recommendation);
    }

    static boolean toolExists(Path bin, String name) {
        return Files.exists(bin.resolve(name)) || Files.exists(bin.resolve(name + ".exe"));
    }
    static boolean moduleExists(String name) {
        return java.lang.ModuleLayer.boot().findModule(name).isPresent();
    }
}
```

**How to run:** `java JavaEnvironmentValidator.java`

The production container use case deliberately PASSES when `javac` is absent — a JRE-only image is the correct production setup. This inverted check is a common source of confusion for developers who think "more tools = better."

## 6. Walkthrough

Execution in `JavaEnvironmentValidator.main`:

1. **Layer detection** — `toolExists(binDir, "javac")` is the critical discriminator. If `javac` is absent, we're in JRE mode. All other JDK tools (`jlink`, `jcmd`, `jshell`) are optional even within the JDK (some trimmed images omit them).

2. **Use case validation** — `validate` uses a switch on `UseCase` to define which conditions matter for each scenario. Critically, `PRODUCTION_CONTAINER` passes when `conditions[0]` (javac) is `false` — a JRE-only deployment is correct because the compiler is a security risk (code injection via `javac`) and a waste of image space.

3. **JFR module check** — `moduleExists("jdk.jfr")` is the correct test for JFR availability. JFR is part of `jdk.jfr` module which ships in both JDK and JRE from Java 11+. You do NOT need the full JDK to use JFR in production.

4. **Heap health** — `heapPct = heapUsed * 100 / heapMax`. If this exceeds 85% in a running application, the GC is working hard to reclaim space — tune `-Xmx` or profile for memory leaks.

5. **GC reporting** — `getGarbageCollectorMXBeans()` returns all GC phases. On G1GC you see two beans: young and old generation. High collection counts on the old generation indicate heap pressure.

Layer decision tree:
```
Q: Do I need to compile Java code?
  YES → JDK
  NO  → Q: Do I need diagnostic tools (jcmd/jstack)?
          YES → JDK
          NO  → Q: Do I need a smaller image?
                  YES → jlink image (custom JRE, 25–100 MB)
                  NO  → JRE (eclipse-temurin:21-jre, ~170 MB)
```

## 7. Gotchas & takeaways

> **Maven and Gradle require the JDK.** Both invoke `javac` (the compiler) as part of `mvn package` / `gradle build`. Setting `JAVA_HOME` to a JRE path causes confusing failures like `tools.jar not found` (Java 8) or `javac: command not found`. Always set `JAVA_HOME` to the JDK root.

> **`JAVA_HOME` points to the JDK root, not `bin/`.** `JAVA_HOME=/usr/lib/jvm/java-21`, then `$JAVA_HOME/bin/java`. Appending `/bin` to `JAVA_HOME` is a common mistake in shell scripts.

- JVM ⊂ JRE ⊂ JDK — strict containment, each outer layer adds tools.
- JVM: executes bytecode. JRE: runs programs. JDK: develops + runs programs.
- Production container: use JRE image (smaller, fewer exploitable tools).
- CI/CD build: use JDK (needs `javac`).
- Maven/Gradle always need the JDK — they call `javac` internally.
- JFR is available in JRE from Java 11+; you do not need the JDK for production profiling.
- `JAVA_HOME` = JDK root (not `bin/`); `$JAVA_HOME/bin/javac` = compiler.
