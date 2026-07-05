---
card: java
gi: 28
slug: java-the-launcher
title: java — the launcher
---

## 1. What it is

The **`java` command** is the JVM launcher — the executable that starts the JVM process, loads the initial class or module, and calls `main(String[] args)`. It ships with both the JDK and JRE (and every JRE/JDK image built with `jlink` that includes `java.base`).

Despite its simple appearance, `java` is doing substantial work before your first line of code runs: bootstrapping the class loaders, initialising the JVM runtime, setting up GC, parsing module graphs, and applying JVM flags.

## 2. Why & when

You need to understand `java` flags when:
- **Diagnosing OOM errors** — `-Xmx`, `-Xms`, `-XX:MaxMetaspaceSize`
- **Tuning GC** — `-XX:+UseG1GC`, `-XX:+UseZGC`, `-XX:MaxGCPauseMillis`
- **Enabling modules** — `--add-opens`, `--add-exports`, `--module-path`
- **Running JFR** — `-XX:+FlightRecorder`, `-XX:StartFlightRecording`
- **Remote debugging** — `-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=5005`
- **Running a main class in a named module** — `-m com.example/com.example.Main`

In Docker/Kubernetes, the `java` command is the process that gets PID 1 (or runs under `exec`). Wrong JVM flags in container environments cause: wrong heap sizing (reads host memory, not container limits), bad GC choices, and `-Xmx` too small or too large.

## 3. Core concept

```
java [JVM options] [-cp classpath | -m module/mainClass | -jar jarfile] [args]

Invocation modes:
  java MyClass          run class on classpath (looks for MyClass.class in -cp)
  java -jar app.jar     run Main-Class from MANIFEST.MF
  java -m mod/Cls       run main class in named module
  java Hello.java       source-file launch mode (JDK 11+, compiles first)
  java --list-modules   list observable modules and exit

Key JVM flags:
  Memory:
    -Xms<size>    initial heap (e.g. -Xms256m)
    -Xmx<size>    max heap     (e.g. -Xmx1g)
    -Xss<size>    thread stack size

  GC:
    -XX:+UseG1GC         G1 GC (default Java 9+)
    -XX:+UseZGC          ZGC (low-latency, Java 15+ production)
    -XX:+UseShenandoahGC Shenandoah (RedHat, OpenJDK 12+)

  Container-awareness (Java 10+, crucial for Docker):
    -XX:+UseContainerSupport   (on by default) — reads cgroup limits, not host
    -XX:MaxRAMPercentage=75.0  set Xmx as % of container memory limit

  Diagnostics:
    -verbose:class        log each class loaded
    -verbose:gc           log GC events
    -XX:+PrintCompilation log JIT compilations
    -XX:+PrintGCDetails   detailed GC logs (Java 8)
    -Xlog:gc*             unified logging (Java 9+)

  Module system:
    --module-path (-p) <path>   module path
    --add-opens <mod>/<pkg>=ALL-UNNAMED  open a package for deep reflection
    --add-exports <mod>/<pkg>=ALL-UNNAMED  export a package
```

Container best practice: `java -XX:MaxRAMPercentage=75 -XX:+UseZGC -jar app.jar` — lets the JVM auto-size the heap to 75% of the cgroup memory limit.

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="java launcher startup sequence: OS fork, JVM init, classloaders, main()">
  <rect x="10" y="10" width="660" height="210" rx="8" fill="#0d1117"/>
  <text x="340" y="32" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">java launcher startup sequence</text>

  <!-- Steps -->
  <rect x="30"  y="50" width="120" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90"  y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">OS: fork java process</text>
  <text x="90"  y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">parse flags</text>

  <line x1="150" y1="68" x2="180" y2="68" stroke="#8b949e" stroke-width="1.5" marker-end="url(#la)"/>

  <rect x="180" y="50" width="120" height="36" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="240" y="70" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">JVM init</text>
  <text x="240" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">heap · GC · JIT threads</text>

  <line x1="300" y1="68" x2="330" y2="68" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#la2)"/>

  <rect x="330" y="50" width="130" height="36" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="395" y="70" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Bootstrap classloader</text>
  <text x="395" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">java.lang.* · java.base</text>

  <line x1="460" y1="68" x2="490" y2="68" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#la2)"/>

  <rect x="490" y="50" width="140" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="560" y="70" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">App ClassLoader</text>
  <text x="560" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-cp / --module-path</text>

  <!-- Main arrow -->
  <line x1="340" y1="130" x2="340" y2="160" stroke="#6db33f" stroke-width="2" marker-end="url(#la3)"/>
  <rect x="240" y="160" width="200" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="180" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">main(String[] args)</text>
  <text x="340" y="192" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">your code runs</text>

  <!-- Line from classloader down -->
  <line x1="560" y1="86" x2="560" y2="120" stroke="#6db33f" stroke-width="1" stroke-dasharray="3,2"/>
  <line x1="560" y1="120" x2="340" y2="120" stroke="#6db33f" stroke-width="1" stroke-dasharray="3,2"/>
  <line x1="340" y1="120" x2="340" y2="130" stroke="#6db33f" stroke-width="1" stroke-dasharray="3,2"/>

  <defs>
    <marker id="la"  markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#8b949e" stroke-width="1.5"/></marker>
    <marker id="la2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
    <marker id="la3" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
  </defs>
</svg>

`java` startup: OS fork → JVM init (heap/GC/JIT threads) → bootstrap classloader → app classloader → `main()`.

## 5. Runnable example

Scenario: inspect how the `java` launcher configured the current JVM process — heap settings, GC, flags, container awareness.

### Level 1 — Basic

```java
// LauncherInfo.java
import java.lang.management.*;

public class LauncherInfo {
    public static void main(String[] args) {
        System.out.println("=== java launcher info ===\n");
        System.out.println("Command       : java " + String.join(" ", args));
        System.out.println("Java version  : " + System.getProperty("java.version"));
        System.out.println("VM name       : " + System.getProperty("java.vm.name"));
        System.out.println("VM args       : " + ManagementFactory.getRuntimeMXBean().getInputArguments());
        System.out.println("Class path    : " + System.getProperty("java.class.path"));
        System.out.println("Module path   : " + System.getProperty("jdk.module.path", "(none)"));

        MemoryMXBean mem = ManagementFactory.getMemoryMXBean();
        long maxHeap  = mem.getHeapMemoryUsage().getMax() / (1024*1024);
        long usedHeap = mem.getHeapMemoryUsage().getUsed() / (1024*1024);
        System.out.printf("%nHeap max  : %d MB%n", maxHeap);
        System.out.printf("Heap used : %d MB%n", usedHeap);
    }
}
```

**How to run:** `java LauncherInfo.java` or `java -Xmx256m LauncherInfo.java`

`RuntimeMXBean.getInputArguments()` returns JVM flags passed to the launcher — `-Xmx`, `-XX:+UseZGC`, `-agentlib:...` — but not the application's `main(args)`.

### Level 2 — Intermediate

Same launcher info extended to detect container awareness and show effective heap sizing vs container memory limits.

```java
// ContainerAwareness.java
import java.lang.management.*;
import java.nio.file.*;
import java.util.*;

public class ContainerAwareness {
    public static void main(String[] args) throws Exception {
        System.out.println("=== Container Awareness Check ===\n");

        MemoryMXBean mem = ManagementFactory.getMemoryMXBean();
        long maxHeap = mem.getHeapMemoryUsage().getMax();

        // Check if running in a container (cgroup v2)
        boolean inContainer = Files.exists(Path.of("/.dockerenv"))
            || Files.exists(Path.of("/run/.containerenv"))
            || isInsideCgroup();

        System.out.println("In container   : " + inContainer);

        // Host/container memory
        long hostMemMB = ((com.sun.management.OperatingSystemMXBean)
            ManagementFactory.getOperatingSystemMXBean()).getTotalPhysicalMemorySize() / (1024*1024);

        System.out.println("Host memory    : " + hostMemMB + " MB");
        System.out.printf("JVM max heap   : %.0f MB (%.1f%% of host)%n",
            maxHeap / 1e6, (100.0 * maxHeap) / (hostMemMB * 1024 * 1024));

        System.out.println("\n[ GC info ]");
        ManagementFactory.getGarbageCollectorMXBeans().forEach(gc ->
            System.out.println("  GC: " + gc.getName()));

        System.out.println("\n[ Recommended java flags for containers ]");
        System.out.println("  -XX:+UseContainerSupport       (on by default Java 10+)");
        System.out.println("  -XX:MaxRAMPercentage=75.0       (75% of cgroup memory limit)");
        System.out.println("  -XX:+UseZGC                    (low-latency, good for containers)");
        System.out.println("  -Xlog:gc*:stdout:time           (GC logs to stdout for log aggregators)");

        // Active JVM flags
        List<String> vmArgs = ManagementFactory.getRuntimeMXBean().getInputArguments();
        System.out.println("\n[ Active JVM flags ]");
        if (vmArgs.isEmpty()) {
            System.out.println("  (none — all defaults)");
        } else {
            vmArgs.forEach(f -> System.out.println("  " + f));
        }
    }

    static boolean isInsideCgroup() {
        try {
            return Files.exists(Path.of("/sys/fs/cgroup")) &&
                   Files.readString(Path.of("/proc/1/cgroup")).contains("docker");
        } catch (Exception e) { return false; }
    }
}
```

**How to run:** `java ContainerAwareness.java`

Without `-XX:MaxRAMPercentage`, the JVM defaults to ~25% of the container's memory limit for the heap — often too small. Explicitly setting `75.0` is a common production pattern.

### Level 3 — Advanced

Same launcher inspection grown to show full JVM flag introspection via `HotSpotDiagnosticMXBean` — showing which flags were set by the user vs defaulted.

```java
// JvmFlagInspector.java
import com.sun.management.HotSpotDiagnosticMXBean;
import javax.management.*;
import java.lang.management.*;
import java.util.*;
import java.util.stream.*;

public class JvmFlagInspector {

    // Flags most relevant for application developers
    static final List<String> INTERESTING_FLAGS = List.of(
        "UseG1GC", "UseZGC", "UseShenandoahGC", "UseSerialGC", "UseParallelGC",
        "MaxHeapSize", "InitialHeapSize", "MaxMetaspaceSize",
        "TieredCompilation", "TieredStopAtLevel",
        "UseContainerSupport", "MaxRAMPercentage",
        "FlightRecorder", "PrintGCDetails",
        "EnablePreviewFeatures"
    );

    public static void main(String[] args) throws Exception {
        HotSpotDiagnosticMXBean hsBean = ManagementFactory
            .getPlatformMXBean(HotSpotDiagnosticMXBean.class);

        System.out.println("╔══════════════════════════════════════════╗");
        System.out.println("║         JVM Flag Inspector               ║");
        System.out.println("╚══════════════════════════════════════════╝\n");

        System.out.printf("%-35s %-18s %s%n", "Flag", "Value", "Origin");
        System.out.println("-".repeat(70));

        for (String flag : INTERESTING_FLAGS) {
            try {
                var vmFlag = hsBean.getVMOption(flag);
                System.out.printf("%-35s %-18s %s%n",
                    flag,
                    vmFlag.getValue(),
                    vmFlag.getOrigin());  // DEFAULT, VM_OPTION, ERGONOMIC, JVMTI, MANAGEMENT
            } catch (IllegalArgumentException e) {
                System.out.printf("%-35s %-18s %s%n", flag, "(n/a)", "not supported this JVM");
            }
        }

        System.out.println("\n[ Heap sizing ]");
        MemoryMXBean mem = ManagementFactory.getMemoryMXBean();
        long initMB = mem.getHeapMemoryUsage().getInit() / (1024*1024);
        long maxMB  = mem.getHeapMemoryUsage().getMax()  / (1024*1024);
        System.out.printf("  Initial: %d MB  Max: %d MB%n", initMB, maxMB);

        System.out.println("\n[ Runtime MXBean input arguments ]");
        ManagementFactory.getRuntimeMXBean().getInputArguments()
            .stream().filter(f -> !f.startsWith("-Dsun") && !f.startsWith("-Djdk"))
            .forEach(f -> System.out.println("  " + f));
    }
}
```

**How to run:** `java JvmFlagInspector.java`

`HotSpotDiagnosticMXBean.getVMOption()` shows the origin: `DEFAULT` (JVM default), `ERGONOMIC` (JVM auto-tuned based on hardware), `VM_OPTION` (set via `-XX:+...` flag), `MANAGEMENT` (changed at runtime via JMX).

## 6. Walkthrough

Execution in `JvmFlagInspector.main`:

1. **`ManagementFactory.getPlatformMXBean(HotSpotDiagnosticMXBean.class)`** — retrieves the HotSpot-specific diagnostics bean. This is a JVM-internal bean (`com.sun.management.*`) not guaranteed by the `java.management` module spec, but available on all HotSpot JVMs (OpenJDK, Temurin, Corretto, Zulu).

2. **`hsBean.getVMOption(flag)`** — returns a `VMOption` with `.getValue()` (current value) and `.getOrigin()`. Origin values:
   - `DEFAULT` — JVM's compiled-in default, never changed
   - `ERGONOMIC` — JVM auto-tuned based on available CPUs and memory at startup
   - `VM_OPTION` — explicitly set via `-XX:+Flag` or `-XX:Flag=N`
   - `MANAGEMENT` — changed at runtime via `setVMOption()`

3. **Heap ergonomics** — if you never set `-Xmx`, the JVM uses `ERGONOMIC` origin and sets `MaxHeapSize` to ~25% of physical (or container) memory. The `ERGONOMIC` origin means "the JVM chose this, not you".

4. **`UseContainerSupport`** — defaults to `true` on Java 10+. When true, the JVM reads `/sys/fs/cgroup/memory.limit_in_bytes` (cgroup v1) or `/sys/fs/cgroup/memory.max` (cgroup v2) instead of `/proc/meminfo` for heap ergonomics.

## 7. Gotchas & takeaways

> **Without `-XX:MaxRAMPercentage`, the JVM sets `MaxHeapSize` to 25% of host RAM** even in a Docker container with a 512 MB memory limit — so a 16 GB host gives a 4 GB heap to a container limited to 512 MB. `UseContainerSupport` (Java 10+, on by default) fixes host-reads-not-cgroup, but you still need `MaxRAMPercentage` to control the fraction used.

> **`-Xss` (thread stack size) defaults to 512 KB (Linux) or 1 MB (Windows).** Deep recursion (parsers, interpreters) needs a larger `-Xss`. `StackOverflowError` on deep but legitimate recursion → `-Xss4m`.

- `java -jar app.jar` reads `Main-Class` from `META-INF/MANIFEST.MF`.
- `java -m module/MainClass` runs a main class in a named module (Java 9+).
- `-XX:+UseContainerSupport` is on by default (Java 10+) — reads cgroup limits, not host memory.
- `-XX:MaxRAMPercentage=75` sets heap to 75% of container memory limit — standard production pattern.
- `HotSpotDiagnosticMXBean.getVMOption()` shows flag values and whether they were default, ergonomic, or explicitly set.
- Remote debug: `java -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005 -jar app.jar`.
