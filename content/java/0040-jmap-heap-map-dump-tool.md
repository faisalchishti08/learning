---
card: java
gi: 40
slug: jmap-heap-map-dump-tool
title: jmap — heap map / dump tool
---

## 1. What it is

**`jmap`** is a JDK command-line tool that inspects the heap of a running JVM or a core dump file. Its two most useful modes are:

```bash
jmap -heap <pid>                        # heap summary: GC algorithm, regions, usage
jmap -histo <pid>                       # histogram: top classes by instance count + bytes
jmap -dump:format=b,file=heap.hprof <pid>  # full heap snapshot → .hprof file
```

The `.hprof` dump can be opened in **Eclipse MAT**, **VisualVM**, or **IntelliJ** for deep memory analysis. The histogram is faster and does not pause the process.

Modern alternative: `jcmd <pid> GC.heap_info` / `jcmd <pid> GC.heap_dump filename=...`

## 2. Why & when

`jmap` is the right tool when:
- **Memory leak investigation** — `jmap -histo <pid>` shows which classes are accumulating objects; take two snapshots minutes apart and compare.
- **OutOfMemoryError post-mortem** — add `-XX:+HeapDumpOnOutOfMemoryError` to the JVM flags; when OOM fires the JVM auto-writes an `.hprof` file that `jmap` can also write manually.
- **Heap sizing** — `jmap -heap <pid>` shows actual live vs committed vs max memory per region (Eden, Survivor, Old Gen, Metaspace).
- **Confirming GC algorithm** — `jmap -heap <pid>` prints the GC type (G1GC, ZGC, Shenandoah, ParallelGC).

Skip `jmap -dump` in production under tight latency constraints — a full heap dump causes a stop-the-world pause proportional to heap size (seconds for a large heap).

## 3. Core concept

```bash
# Heap summary (safe, fast)
jmap -heap <pid>
# Sample output:
#   Heap Configuration:
#     MinHeapFreeRatio: 40
#     MaxHeapFreeRatio: 70
#     MaxHeapSize: 2147483648 (2.0 GB)
#   G1 Heap:
#     regions  = 2048, region size = 1024K
#   G1 Young Generation:
#     Eden Space: capacity = 393216K (384.0MB), used = 73728K (72.0MB)
#     Survivor Space: capacity = 65536K (64.0MB), used = 32768K (32.0MB)
#   G1 Old Generation:
#     used = 102400K (100.0MB)

# Class instance histogram (safe, fast)
jmap -histo <pid> | head -20
# num     #instances    #bytes  class name
# ---     ----------    ------  ----------
#   1:     4,213,772   101,130,528  [B           (byte[])
#   2:     1,024,000    32,768,000  java.lang.String
#   3:       512,000    12,288,000  com.example.Order

# Full heap dump (causes GC pause, writes binary file)
jmap -dump:format=b,live,file=/tmp/heap.hprof <pid>
# live = only reachable objects (faster, smaller; skip 'live' for everything)

# Finalization queue (rarely used)
jmap -finalizerinfo <pid>
```

`.hprof` is a well-known binary format (HPROF agent protocol). Any memory profiler can read it. Common workflow:
1. `jmap -histo <pid>` → find suspicious class.
2. `jmap -dump:format=b,live,file=heap.hprof <pid>` → write dump.
3. Open in Eclipse MAT: *Find → Leak Suspects* → drill into retained heap.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jmap reads JVM heap and writes either a histogram or an hprof dump file">
  <rect x="8" y="8" width="684" height="204" rx="8" fill="#0d1117"/>

  <!-- JVM heap regions -->
  <rect x="20" y="25" width="220" height="170" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="44" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">JVM Heap</text>

  <rect x="35" y="55"  width="190" height="30" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="130" y="65" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Eden (72 MB used / 384 MB)</text>
  <rect x="35" y="55" width="135" height="30" rx="4" fill="#6db33f" fill-opacity="0.2"/>

  <rect x="35" y="92"  width="190" height="25" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="130" y="104" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Survivor (32 MB / 64 MB)</text>
  <rect x="35" y="92" width="95" height="25" rx="4" fill="#79c0ff" fill-opacity="0.2"/>

  <rect x="35" y="124" width="190" height="30" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="130" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Old Gen (100 MB / 1536 MB)</text>
  <rect x="35" y="124" width="12" height="30" rx="4" fill="#8b949e" fill-opacity="0.3"/>

  <rect x="35" y="161" width="190" height="22" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="130" y="176" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Metaspace (8 MB)</text>

  <!-- jmap -->
  <rect x="295" y="85" width="100" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="345" y="108" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">jmap</text>
  <text x="345" y="124" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">attach API</text>

  <line x1="240" y1="110" x2="291" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jm1)"/>

  <!-- Output: two options -->
  <rect x="455" y="30"  width="215" height="60" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="562" y="50"  fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">-histo (histogram)</text>
  <text x="470" y="66"  fill="#6db33f" font-size="8" font-family="monospace">1: 4M [B  101MB</text>
  <text x="470" y="78"  fill="#8b949e" font-size="8" font-family="monospace">2: 1M String 32MB</text>

  <rect x="455" y="105" width="215" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="562" y="124" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">-dump (heap.hprof)</text>
  <text x="470" y="140" fill="#8b949e" font-size="8" font-family="monospace">binary HPROF format</text>
  <text x="470" y="153" fill="#8b949e" font-size="8" font-family="monospace">open in Eclipse MAT</text>

  <line x1="395" y1="100" x2="451" y2="60"  stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jm2)"/>
  <line x1="395" y1="110" x2="451" y2="135" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jm2)"/>

  <defs>
    <marker id="jm1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
    <marker id="jm2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
  </defs>
</svg>

`jmap` reads heap region usage and object graphs from the JVM. The histogram is safe and fast; a full dump pauses the JVM while writing.

## 5. Runnable example

Scenario: simulate a memory leak in an order-processing service (accumulating `Order` objects in a static list), detect it with a heap histogram, then take and inspect a dump.

### Level 1 — Basic

```java
// HeapHistoBasic.java — read heap histogram programmatically
import java.lang.management.*;
import java.nio.file.*;

public class HeapHistoBasic {
    public static void main(String[] args) throws Exception {
        System.out.println("=== jmap heap histogram demo ===\n");

        // Show heap usage via JMX
        MemoryMXBean mem = ManagementFactory.getMemoryMXBean();
        MemoryUsage heap = mem.getHeapMemoryUsage();
        System.out.printf("Heap used:      %d MB%n", heap.getUsed() / 1024 / 1024);
        System.out.printf("Heap committed: %d MB%n", heap.getCommitted() / 1024 / 1024);
        System.out.printf("Heap max:       %d MB%n", heap.getMax() / 1024 / 1024);

        MemoryUsage meta = mem.getNonHeapMemoryUsage();
        System.out.printf("Metaspace used: %d MB%n", meta.getUsed() / 1024 / 1024);

        System.out.println("\n--- GC pools ---");
        for (MemoryPoolMXBean pool : ManagementFactory.getMemoryPoolMXBeans()) {
            MemoryUsage u = pool.getUsage();
            System.out.printf("  %-30s used=%d KB%n", pool.getName(), u.getUsed() / 1024);
        }

        Path jmap = findTool("jmap");
        long pid  = ProcessHandle.current().pid();
        System.out.println("\njmap tool: " + (jmap != null ? jmap : "not found"));
        System.out.println("Try: jmap -histo " + pid + " | head -20");
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java HeapHistoBasic.java`

`MemoryMXBean` reports heap and Metaspace usage without any external tool. For a live histogram, run `jmap -histo <pid>` in a second terminal while the program is paused (add `Thread.sleep` if needed).

### Level 2 — Intermediate

Same order-accumulation scenario: a service keeps references to `Order` objects in a growing static list — a simulated memory leak. Run `jmap -histo` against it to see `Order` at the top of the histogram.

```java
// HeapHistoLeak.java — simulate a memory leak, run jmap histogram against it
import java.lang.management.*;
import java.nio.file.*;
import java.util.*;

public class HeapHistoLeak {

    // Simulated leaked objects
    static final List<byte[]> LEAKED = new ArrayList<>();

    public static void main(String[] args) throws Exception {
        Path jmap = findTool("jmap");
        long pid  = ProcessHandle.current().pid();
        System.out.println("PID: " + pid);

        if (jmap == null) {
            System.err.println("jmap not found — JDK required");
            return;
        }

        // Allocate ~50 MB of byte arrays (simulating retained orders)
        System.out.println("Allocating 50 MB of leaked byte[]...");
        for (int i = 0; i < 500; i++)
            LEAKED.add(new byte[100_000]); // 100 KB each × 500 = 50 MB

        MemoryUsage heap = ManagementFactory.getMemoryMXBean().getHeapMemoryUsage();
        System.out.printf("Heap used: %d MB%n%n", heap.getUsed() / 1024 / 1024);

        // Run jmap -histo against ourselves
        System.out.println("Running: jmap -histo " + pid);
        Process p = new ProcessBuilder(jmap.toString(), "-histo", String.valueOf(pid))
            .redirectErrorStream(true).start();
        String output = new String(p.getInputStream().readAllBytes());
        p.waitFor();

        // Print top 15 lines of histogram
        System.out.println("\n--- Top classes by bytes ---");
        output.lines().limit(17).forEach(System.out::println);
        System.out.println("...");
        System.out.println("\nNote: [B = byte[] — the leaked arrays should appear near the top.");
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java HeapHistoLeak.java`

After allocating 50 MB of `byte[]`, `jmap -histo` is run against the current process. `[B` (byte arrays) appears near the top with ~50 MB. In a real leak investigation you'd take two histograms 10 minutes apart and compare the difference.

### Level 3 — Advanced

Same leak scenario grown to take a full `.hprof` dump, verify it exists and has valid HPROF magic bytes, and show the production OOM auto-dump pattern.

```java
// HeapDump.java — take heap dump via jmap, verify hprof, show OOM auto-dump pattern
import java.lang.management.*;
import java.nio.file.*;
import java.util.*;

public class HeapDump {

    static final List<byte[]> LEAKED = new ArrayList<>();
    // HPROF file magic: "JAVA PROFILE 1.0.2" (first 18 bytes)
    static final byte[] HPROF_MAGIC = "JAVA PROFILE".getBytes();

    public static void main(String[] args) throws Exception {
        Path jmap = findTool("jmap");
        long pid  = ProcessHandle.current().pid();
        if (jmap == null) { System.err.println("JDK required"); return; }

        // Allocate ~30 MB
        for (int i = 0; i < 300; i++) LEAKED.add(new byte[100_000]);
        System.out.println("=== Heap dump demo ===");
        System.out.printf("PID %d | Heap used: %d MB%n%n", pid,
            ManagementFactory.getMemoryMXBean().getHeapMemoryUsage().getUsed() / 1024 / 1024);

        // Take a live-object-only dump
        Path hprof = Path.of(System.getProperty("java.io.tmpdir")).resolve("demo-" + pid + ".hprof");
        System.out.println("Taking heap dump (live objects only)...");
        Process dumpP = new ProcessBuilder(jmap.toString(),
            "-dump:format=b,live,file=" + hprof, String.valueOf(pid))
            .redirectErrorStream(true).start();
        String out = new String(dumpP.getInputStream().readAllBytes());
        dumpP.waitFor();
        System.out.println(out.strip());

        // Verify the file
        if (Files.exists(hprof)) {
            long sizeMB = Files.size(hprof) / 1024 / 1024;
            byte[] header = Files.readAllBytes(hprof);
            boolean valid = isPrefix(HPROF_MAGIC, header);
            System.out.printf("Dump: %s%n", hprof);
            System.out.printf("Size: %d MB | Valid HPROF magic: %s%n%n", sizeMB, valid);

            System.out.println("Analyse with:");
            System.out.println("  jhat " + hprof + "  (built-in, port 7000)");
            System.out.println("  jfr  — not applicable, .hprof is jmap format");
            System.out.println("  Eclipse MAT — 'Find Leak Suspects' wizard");
            System.out.println("  VisualVM — File > Load...");

            Files.delete(hprof);
            System.out.println("Cleaned up dump.");
        }

        System.out.println("\n[ Production pattern — auto-dump on OOM ]");
        System.out.println("  java -XX:+HeapDumpOnOutOfMemoryError \\");
        System.out.println("       -XX:HeapDumpPath=/var/log/dumps/ \\");
        System.out.println("       -Xmx2g -jar app.jar");
        System.out.println();
        System.out.println("[ Incremental leak detection — compare histograms ]");
        System.out.println("  jmap -histo <pid> | sort -k 3 -rn > histo1.txt");
        System.out.println("  # wait 10 minutes");
        System.out.println("  jmap -histo <pid> | sort -k 3 -rn > histo2.txt");
        System.out.println("  diff histo1.txt histo2.txt");
    }

    static boolean isPrefix(byte[] prefix, byte[] data) {
        if (data.length < prefix.length) return false;
        for (int i = 0; i < prefix.length; i++) if (data[i] != prefix[i]) return false;
        return true;
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java HeapDump.java`

Takes a real `.hprof` dump from the live JVM, verifies the HPROF magic header, prints analysis options, then cleans up. The final output shows the production JVM flag pattern for automatic OOM dumps.

## 6. Walkthrough

Execution trace in `HeapDump.main`:

**Leak allocation.** 300 `byte[100_000]` arrays are allocated and kept alive by the static `LEAKED` list. Each array is ~100 KB; total ~30 MB. These are GC roots through the static field — no GC can collect them while the class is loaded.

**`jmap -dump:format=b,live,file=...`** → `jmap` connects via the attach socket. It sends the `heap_dump` command. The JVM triggers a safe-point (all threads pause at the next polling point). Then it traverses the object graph from GC roots, writing reachable objects in HPROF binary format. `live` means only live (reachable) objects are included — this produces a smaller file and runs faster. Without `live`, all objects (including unreachable garbage not yet collected) are written.

**HPROF header.** The first 18 bytes of the file are `JAVA PROFILE 1.0.2\0` (null-terminated ASCII). The code checks for `JAVA PROFILE` as a prefix to confirm the file was written correctly.

**GC pause duration.** For a small 30 MB heap the pause is typically < 500 ms. For a 4 GB heap it can be 20–60 seconds. This is why `-XX:+HeapDumpOnOutOfMemoryError` is preferred in production: it only fires when the process is dying anyway.

**Eclipse MAT workflow.** Open `heap.hprof` in MAT → *Leak Suspects* report → MAT identifies the largest retained object graphs and shows which root chain keeps them alive. In this demo it would show `HeapDump.LEAKED → byte[][] → ...` holding ~30 MB.

**Histogram comparison.** `jmap -histo <pid>` is a much lighter alternative: no stop-the-world pause (it marks objects without freezing threads). Two snapshots, diffed, show which classes grew — the starting point for any leak investigation.

## 7. Gotchas & takeaways

> **`jmap -dump` pauses the entire JVM.** The safe-point stop-the-world pause blocks all application threads until the dump is written. For large heaps (4+ GB) this can take 30–120 seconds. On production services with strict SLAs, trigger dumps during maintenance windows or use G1GC's heap dump (`jcmd <pid> GC.heap_dump filename=...`) which is equivalent.

> **`jmap` is deprecated for some flags in newer JDKs.** `jmap -heap` and `jmap -histo` print a warning on JDK 9+ saying to use `jcmd`. The output is identical; the flags still work but may be removed in a future major release.

- `jmap -histo <pid>` — fast histogram, no GC pause (use for routine leak detection).
- `jmap -dump:format=b,live,file=heap.hprof <pid>` — full dump, GC pause, needed for MAT analysis.
- `-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/path/` — always add to production JVM flags.
- Class name `[B` = `byte[]`, `[C` = `char[]`, `[I` = `int[]`, `[Ljava.lang.String;` = `String[]`.
- Compare two histograms with `diff` or `vimdiff` to spot growing classes — the simplest leak-detection method.
- Modern alternative: `jcmd <pid> GC.heap_dump filename=/tmp/heap.hprof` does the same thing.
