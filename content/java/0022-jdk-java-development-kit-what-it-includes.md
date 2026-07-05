---
card: java
gi: 22
slug: jdk-java-development-kit-what-it-includes
title: JDK (Java Development Kit) — what it includes
---

## 1. What it is

The **Java Development Kit (JDK)** is the full distribution of the Java platform for developers. It includes everything in the JRE (JVM + class library) plus the tools needed to write, compile, debug, package, and document Java code: `javac`, `jar`, `jdb`, `jshell`, `javadoc`, `jlink`, `jpackage`, `jcmd`, `jstack`, `jmap`, and more.

When you install Java for development — from Temurin, Corretto, Oracle, Azul, or any other vendor — you install the JDK. The JDK is what you need on your laptop, in CI, and in any container that compiles code.

## 2. Why & when

You need the JDK (not just the JRE) whenever you:
- Write and compile Java source code (`javac`).
- Run annotation processors or code generation at build time.
- Use build tools (Maven, Gradle — both call `javac` indirectly).
- Debug with `jdb`, `jstack`, or attach a profiler.
- Create JAR archives with `jar` or custom JREs with `jlink`.
- Generate documentation with `javadoc`.
- Inspect a running JVM with `jcmd`, `jmap`, or `jfr`.

In production containers that only **run** compiled code, the JRE (or a `jlink` image) is sufficient and smaller.

## 3. Core concept

The JDK directory layout (Java 11+ modular structure):

```
jdk/
├── bin/
│   ├── java          (JVM launcher — runs programs)
│   ├── javac         (compiler — .java → .class)
│   ├── jar           (archive tool — packages .class into .jar)
│   ├── javadoc       (doc generator)
│   ├── jshell        (REPL — interactive Java)
│   ├── jdb           (debugger)
│   ├── jlink         (custom JRE builder)
│   ├── jpackage      (native installer builder)
│   ├── jcmd          (JVM diagnostic commands)
│   ├── jstack        (thread dump)
│   ├── jmap          (heap dump / histogram)
│   ├── jfr           (Java Flight Recorder control)
│   └── jdeps         (module/class dependency analyser)
│
├── lib/
│   ├── modules       (compiled JDK modules — rt.jar equivalent)
│   ├── ct.sym        (cross-compilation symbol file)
│   └── src.zip       (JDK source code)
│
├── include/          (JNI header files — for writing native methods)
│
└── conf/
    ├── security/     (security policy, CA certs, crypto config)
    └── logging.properties
```

Key tools and what they do:

| Tool | Purpose |
|---|---|
| `javac` | Compile `.java` to `.class` |
| `jar` | Create/inspect `.jar` archives |
| `jshell` | Interactive REPL for experimenting |
| `jlink` | Build a custom minimal JRE |
| `jpackage` | Build native OS installers (`.msi`, `.dmg`, `.deb`) |
| `jcmd <pid> <cmd>` | Send diagnostic commands to a running JVM |
| `jstack <pid>` | Thread dump (diagnose deadlocks) |
| `jmap <pid>` | Heap histogram / dump |
| `jfr` | Control Java Flight Recorder from command line |
| `jdeps` | Analyse class/module dependencies |
| `jdb` | Command-line debugger |

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JDK contents: bin tools, lib modules, include JNI headers, conf security">
  <!-- JDK box -->
  <rect x="20" y="20" width="640" height="190" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="44" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">JDK (Java Development Kit)</text>

  <!-- bin -->
  <rect x="40" y="56" width="155" height="136" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="117" y="74" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">bin/ (tools)</text>
  <text x="117" y="90"  fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">java  javac  jar</text>
  <text x="117" y="103" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">jshell  jdb  javadoc</text>
  <text x="117" y="116" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">jlink  jpackage</text>
  <text x="117" y="129" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">jcmd  jstack  jmap</text>
  <text x="117" y="142" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">jfr  jdeps</text>

  <!-- lib -->
  <rect x="205" y="56" width="145" height="136" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="277" y="74" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">lib/ (class library)</text>
  <text x="277" y="90"  fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">modules (rt.jar equiv)</text>
  <text x="277" y="103" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">java.* + jdk.* mods</text>
  <text x="277" y="116" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ct.sym (cross-compile)</text>
  <text x="277" y="129" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">src.zip (source)</text>

  <!-- include -->
  <rect x="360" y="56" width="130" height="80" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="425" y="74" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">include/ (JNI)</text>
  <text x="425" y="90"  fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">jni.h  jvmti.h</text>
  <text x="425" y="103" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">for native methods</text>

  <!-- conf -->
  <rect x="500" y="56" width="140" height="80" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="570" y="74" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">conf/ (config)</text>
  <text x="570" y="90"  fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">security/ CA certs</text>
  <text x="570" y="103" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">crypto policy</text>

  <!-- JRE label at bottom -->
  <rect x="40" y="152" width="440" height="48" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="260" y="175" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">JRE subset: java + lib/modules + conf (no javac, jshell, jlink, jdb, javadoc, include/)</text>
</svg>

JDK contains everything in the JRE plus compiler tools, diagnostics, and JNI headers.

## 5. Runnable example

Scenario: explore the JDK installation, discover which tools are present, and demonstrate the most useful diagnostic tools (`jcmd`, `jstack`) from Java code.

### Level 1 — Basic

```java
// JdkToolsProbe.java
import java.io.*;
import java.nio.file.*;

public class JdkToolsProbe {
    public static void main(String[] args) throws Exception {
        Path javaHome = Path.of(System.getProperty("java.home"));
        Path binDir   = javaHome.resolve("bin");

        System.out.println("JAVA_HOME : " + javaHome);
        System.out.println("bin/      : " + binDir);
        System.out.println();

        String[] coreTools = {"java", "javac", "jar", "jshell", "jlink", "jpackage", "jcmd"};
        System.out.println("Core tool availability:");
        for (String tool : coreTools) {
            // Try both Unix (no ext) and Windows (.exe)
            boolean present = Files.exists(binDir.resolve(tool)) || Files.exists(binDir.resolve(tool + ".exe"));
            System.out.printf("  %-12s %s%n", tool, present ? "PRESENT" : "absent (JRE-only image)");
        }

        boolean isJdk = Files.exists(binDir.resolve("javac")) || Files.exists(binDir.resolve("javac.exe"));
        System.out.println("\n" + (isJdk ? "Full JDK detected." : "JRE-only image (no javac)."));
    }
}
```

**How to run:** `java JdkToolsProbe.java`

On a JDK, `javac` exists in `bin/`. On a JRE-only image (Docker `eclipse-temurin:21-jre`), it does not.

### Level 2 — Intermediate

Same JDK probe extended to run `jcmd` (if available) to list running JVM processes and show diagnostic capabilities.

```java
// JdkDiagnostics.java
import java.io.*;
import java.lang.management.*;
import java.nio.file.*;
import java.util.*;

public class JdkDiagnostics {
    public static void main(String[] args) throws Exception {
        System.out.println("=== JDK Diagnostics ===\n");

        // Detect JDK vs JRE
        Path binDir = Path.of(System.getProperty("java.home"), "bin");
        boolean hasJcmd  = toolExists(binDir, "jcmd");
        boolean hasJstack = toolExists(binDir, "jstack");
        boolean hasJmap  = toolExists(binDir, "jmap");
        boolean hasJfr   = toolExists(binDir, "jfr");

        System.out.println("[ Diagnostic Tools Available ]");
        System.out.printf("  jcmd   : %s%n", hasJcmd   ? "YES (send commands to JVM)" : "NO");
        System.out.printf("  jstack : %s%n", hasJstack ? "YES (thread dump)" : "NO");
        System.out.printf("  jmap   : %s%n", hasJmap   ? "YES (heap histogram/dump)" : "NO");
        System.out.printf("  jfr    : %s%n", hasJfr    ? "YES (Flight Recorder control)" : "NO");

        // Memory stats via management API (works in JRE too)
        System.out.println("\n[ Memory (via management API) ]");
        MemoryMXBean mem = ManagementFactory.getMemoryMXBean();
        System.out.printf("  Heap used      : %d MB%n", mem.getHeapMemoryUsage().getUsed() / (1024*1024));
        System.out.printf("  Heap committed : %d MB%n", mem.getHeapMemoryUsage().getCommitted() / (1024*1024));
        System.out.printf("  Non-heap used  : %d MB%n", mem.getNonHeapMemoryUsage().getUsed() / (1024*1024));

        // Thread info (subset of what jstack shows)
        System.out.println("\n[ Thread Summary ]");
        ThreadMXBean threads = ManagementFactory.getThreadMXBean();
        System.out.printf("  Live threads     : %d%n", threads.getThreadCount());
        System.out.printf("  Peak threads     : %d%n", threads.getPeakThreadCount());
        System.out.printf("  Daemon threads   : %d%n", threads.getDaemonThreadCount());
        System.out.printf("  Deadlocks found  : %s%n",
            threads.findDeadlockedThreads() != null ? "YES — investigate!" : "none");

        if (hasJcmd) {
            System.out.println("\n[ jcmd commands for this JVM ]");
            System.out.println("  jcmd " + ProcessHandle.current().pid() + " help");
            System.out.println("  jcmd " + ProcessHandle.current().pid() + " VM.version");
            System.out.println("  jcmd " + ProcessHandle.current().pid() + " Thread.print");
            System.out.println("  jcmd " + ProcessHandle.current().pid() + " GC.heap_info");
        }
    }

    static boolean toolExists(Path binDir, String name) {
        return Files.exists(binDir.resolve(name)) || Files.exists(binDir.resolve(name + ".exe"));
    }
}
```

**How to run:** `java JdkDiagnostics.java`

The management API works in JRE too. `jcmd` requires the full JDK. The printed `jcmd <pid>` commands can be run in another terminal against this live process.

### Level 3 — Advanced

Same scenario grown to a full JDK capability audit: filesystem tool discovery, running `jcmd` in a subprocess, capturing JFR event counts, and showing what a production ops team needs from the JDK.

```java
// JdkCapabilityAudit.java
import java.io.*;
import java.lang.management.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.*;

public class JdkCapabilityAudit {

    record ToolEntry(String name, String purpose, boolean present) {}

    public static void main(String[] args) throws Exception {
        System.out.println("╔══════════════════════════════════════════════╗");
        System.out.println("║            JDK Capability Audit              ║");
        System.out.println("╚══════════════════════════════════════════════╝\n");

        Path binDir = Path.of(System.getProperty("java.home"), "bin");
        System.out.println("JAVA_HOME : " + System.getProperty("java.home"));
        System.out.println("Java      : " + Runtime.version());
        System.out.println();

        // Tool inventory
        List<ToolEntry> tools = List.of(
            new ToolEntry("java",      "Launch JVM",              toolExists(binDir, "java")),
            new ToolEntry("javac",     "Compiler (.java→.class)", toolExists(binDir, "javac")),
            new ToolEntry("jar",       "JAR archive tool",        toolExists(binDir, "jar")),
            new ToolEntry("jshell",    "Interactive REPL",        toolExists(binDir, "jshell")),
            new ToolEntry("javadoc",   "Documentation generator", toolExists(binDir, "javadoc")),
            new ToolEntry("jlink",     "Custom JRE builder",      toolExists(binDir, "jlink")),
            new ToolEntry("jpackage",  "Native installer builder",toolExists(binDir, "jpackage")),
            new ToolEntry("jcmd",      "JVM diagnostic commands", toolExists(binDir, "jcmd")),
            new ToolEntry("jstack",    "Thread dump",             toolExists(binDir, "jstack")),
            new ToolEntry("jmap",      "Heap histogram/dump",     toolExists(binDir, "jmap")),
            new ToolEntry("jfr",       "Flight Recorder control", toolExists(binDir, "jfr")),
            new ToolEntry("jdeps",     "Dependency analyser",     toolExists(binDir, "jdeps")),
            new ToolEntry("jdb",       "Command-line debugger",   toolExists(binDir, "jdb"))
        );

        System.out.printf("  %-12s  %-5s  %s%n", "Tool", "Found", "Purpose");
        System.out.println("  " + "-".repeat(60));
        tools.forEach(t -> System.out.printf("  %-12s  %-5s  %s%n",
            t.name(), t.present() ? "YES" : "no", t.purpose()));

        long present = tools.stream().filter(ToolEntry::present).count();
        boolean isFullJdk = tools.stream().filter(t -> t.name().equals("javac")).findFirst()
            .map(ToolEntry::present).orElse(false);
        System.out.printf("%n  %d/%d tools present — %s%n%n",
            present, tools.size(), isFullJdk ? "Full JDK" : "JRE-only image (no compiler)");

        // JFR capabilities (available in JDK + JRE from Java 11)
        System.out.println("[ Java Flight Recorder ]");
        boolean hasJfr = moduleExists("jdk.jfr");
        System.out.println("  jdk.jfr module: " + (hasJfr ? "PRESENT" : "absent"));
        if (hasJfr) {
            System.out.println("  JFR is available even in JRE (Java 11+)");
            System.out.println("  Start: jcmd <pid> JFR.start duration=30s filename=app.jfr");
            System.out.println("  Stop:  jcmd <pid> JFR.stop");
        }

        // Live JVM stats
        System.out.println("\n[ Live JVM Stats ]");
        MemoryMXBean mem = ManagementFactory.getMemoryMXBean();
        System.out.printf("  PID           : %d%n", ProcessHandle.current().pid());
        System.out.printf("  Heap          : %d/%d MB (used/max)%n",
            mem.getHeapMemoryUsage().getUsed()/(1<<20),
            mem.getHeapMemoryUsage().getMax()/(1<<20));
        System.out.printf("  Live threads  : %d%n", ManagementFactory.getThreadMXBean().getThreadCount());
        System.out.printf("  Classes loaded: %d%n", ManagementFactory.getClassLoadingMXBean().getLoadedClassCount());
        ManagementFactory.getGarbageCollectorMXBeans()
            .forEach(gc -> System.out.printf("  GC %-28s : %d collections%n", gc.getName(), gc.getCollectionCount()));
    }

    static boolean toolExists(Path binDir, String name) {
        return Files.exists(binDir.resolve(name)) || Files.exists(binDir.resolve(name + ".exe"));
    }

    static boolean moduleExists(String name) {
        return java.lang.ModuleLayer.boot().findModule(name).isPresent();
    }
}
```

**How to run:** `java JdkCapabilityAudit.java`

`ProcessHandle.current().pid()` gives the PID of the running JVM process — you can then run `jcmd <pid> VM.flags` in another terminal to see all the JVM's active flags.

## 6. Walkthrough

Execution in `JdkCapabilityAudit.main`:

1. **Tool discovery** — `Path.of(java.home, "bin")` locates the JDK's binary directory. `Files.exists(binDir.resolve("javac"))` checks whether the compiler is present. The `.exe` check covers Windows where binaries have extensions. Tools like `jcmd`, `jstack`, and `jmap` are present in the JDK but absent in JRE images.

2. **Full JDK vs JRE classification** — `javac` presence is the definitive test. `jcmd` and `jmap` are also JDK-only in older Java versions, though in Java 9+ some diagnostic capabilities moved to the JRE.

3. **JFR module check** — `jdk.jfr` is available in both JDK and JRE from Java 11+. This means you can start a Flight Recorder session from inside a production container even without the full JDK, using `jcmd <pid> JFR.start` if `jcmd` is available.

4. **Live JVM stats** — `ProcessHandle.current().pid()` returns this JVM's OS process ID. The diagnostic output (heap, threads, GC collections) mirrors what `jcmd <pid> VM.info` would show. `ManagementFactory.getGarbageCollectorMXBeans()` lists both young and old generation GC beans.

5. **Tool purpose table** — each tool's `present` boolean is checked at runtime against the actual filesystem, not assumed. This makes the audit reliable across JDK vs JRE images.

Data flow:
```
System.getProperty("java.home") → Path
  → binDir.resolve(toolName) → Files.exists() → boolean
List<ToolEntry>
  → count present → classify as JDK vs JRE
ManagementFactory
  → MemoryMXBean → heap stats
  → ThreadMXBean → thread count
  → ClassLoadingMXBean → class count
  → GarbageCollectorMXBean × N → GC stats
ProcessHandle.current().pid() → OS PID
```

## 7. Gotchas & takeaways

> **`java.home` in Java 9+ points to the JDK root, not a `jre/` subdirectory.** In Java 8, `java.home` was `…/jdk1.8.0/jre/` (pointing at the JRE inside the JDK). In Java 9+, `java.home` is `…/jdk-21/` (the JDK root). Code that appends `/../bin/javac` to `java.home` to find the compiler will break on Java 9+.

> **`jcmd` is one of the most powerful tools in the JDK.** `jcmd <pid> help` lists every command supported by that specific JVM — it varies by JVM version and which modules are loaded. In production diagnostics, `jcmd <pid> Thread.print` is often faster and safer than attaching `jstack`.

- JDK = JRE + `javac` + `jar` + `jshell` + `jlink` + `jpackage` + diagnostics (`jcmd`, `jstack`, `jmap`, `jfr`, `jdeps`) + JNI headers.
- Production containers only run compiled code: use JRE image or `jlink` custom image; the JDK is not needed.
- `jcmd <pid> help` → full list of diagnostic commands for a running JVM.
- `jdeps --print-module-deps app.jar` → minimal `--add-modules` list for `jlink`.
- `ProcessHandle.current().pid()` → PID of the current JVM (use in JMX/diagnostic scripts).
- JFR (`jdk.jfr` module) is present in JRE from Java 11+; `jcmd JFR.start` works in production containers.
