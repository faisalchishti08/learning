---
card: java
gi: 617
slug: application-class-data-sharing-appcds
title: Application Class-Data Sharing (AppCDS)
---

## 1. What it is

Application Class-Data Sharing (AppCDS) is a Java 10 enhancement to the Class-Data Sharing (CDS) feature that extends CDS from JDK runtime classes to application classes and custom classpath entries. CDS pre-processes class metadata into a shared archive file that multiple JVM instances can memory-map, avoiding the cost of class loading, verification, and metadata allocation for each JVM startup. Before Java 10, CDS only worked for the JDK's bootstrap classes; AppCDS lets you include your application's classes — reducing startup time and memory footprint across JVM instances.

## 2. Why & when

Containerised and microservice deployments often spin up many JVM instances of the same application (horizontal scaling). Each instance independently loads, verifies, and stores class metadata for the same application classes — wasting CPU and memory. AppCDS allows these instances to share class metadata via a memory-mapped archive file, turning N copies of class metadata into one shared copy. The benefits are most pronounced in environments where JVM instances start frequently (serverless, auto-scaling, CI/CD) and where memory is constrained (containers with tight memory limits). Typical savings: 10–30% startup time reduction and 10–20% memory reduction per JVM instance.

## 3. Core concept

```bash
# Step 1: Run app once to record which classes are loaded
java -Xshare:off -XX:DumpLoadedClassList=app.classlist -jar myapp.jar

# Step 2: Create the shared archive
java -Xshare:dump -XX:SharedClassListFile=app.classlist \
     -XX:SharedArchiveFile=app-cds.jsa \
     -cp myapp.jar

# Step 3: Run with the shared archive (multiple instances)
java -Xshare:auto -XX:SharedArchiveFile=app-cds.jsa -jar myapp.jar
```

The three-step process: (1) record a class list by running the application with class-load tracing, (2) create a shared archive from that list, and (3) launch JVM instances pointing to the archive. `-Xshare:auto` means "use the archive if available, proceed normally if not." The archive is memory-mapped, so all JVM instances using it share the same physical memory pages for class metadata.

## 4. Diagram

<svg viewBox="0 0 580 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AppCDS workflow: record class list → create archive → share across JVM instances">
  <rect x="20" y="10" width="540" height="170" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="40" y="30" width="150" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="115" y="50" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">1. Record class list</text>
  <text x="115" y="64" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">DumpLoadedClassList</text>

  <text x="200" y="50" fill="#8b949e" font-size="10" font-family="monospace">→</text>

  <rect x="215" y="30" width="150" height="40" rx="4" fill="#0d1117" stroke="#6db33f"/>
  <text x="290" y="50" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">2. Create archive</text>
  <text x="290" y="64" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">-Xshare:dump</text>

  <text x="375" y="50" fill="#8b949e" font-size="10" font-family="monospace">→</text>

  <rect x="390" y="30" width="160" height="40" rx="4" fill="#f0883e" stroke="#f0883e"/>
  <text x="470" y="50" fill="#f0883e" font-size="9" text-anchor="middle" font-family="monospace">app-cds.jsa</text>
  <text x="470" y="64" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">shared archive file</text>

  <text x="200" y="100" fill="#8b949e" font-size="10" font-family="monospace">memory-mapped</text>
  <text x="200" y="115" fill="#8b949e" font-size="9" font-family="monospace">↓↓↓</text>

  <rect x="40" y="105" width="100" height="30" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="90" y="125" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">JVM 1</text>
  <rect x="200" y="105" width="100" height="30" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="250" y="125" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">JVM 2</text>
  <rect x="360" y="105" width="100" height="30" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="410" y="125" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">JVM N</text>

  <text x="30" y="165" fill="#8b949e" font-size="8" font-family="sans-serif">All share the same class metadata in physical memory — lower footprint, faster startup</text>
</svg>

Three-step process produces a `.jsa` file that multiple JVMs memory-map, sharing class metadata.

## 5. Runnable example

Scenario: demonstrating the concept and workflow of AppCDS — starting with basic CDS (JDK classes only), extending to the AppCDS workflow, and finally comparing startup time and memory with and without a shared archive.

### Level 1 — Basic

```java
// File: AppCDSDemo.java

public class AppCDSDemo {
    public static void main(String[] args) {
        System.out.println("=== Application Class-Data Sharing (AppCDS) ===\n");

        System.out.println("Java 10 extends CDS from JDK classes to your application classes.\n");

        System.out.println("Step 1 — Record which classes your app loads:");
        System.out.println("  $ java -Xshare:off -XX:DumpLoadedClassList=app.classlist \\");
        System.out.println("      -jar myapp.jar\n");

        System.out.println("Step 2 — Create the shared archive:");
        System.out.println("  $ java -Xshare:dump -XX:SharedClassListFile=app.classlist \\");
        System.out.println("      -XX:SharedArchiveFile=app-cds.jsa -cp myapp.jar\n");

        System.out.println("Step 3 — Run with the archive (repeat for each instance):");
        System.out.println("  $ java -Xshare:auto -XX:SharedArchiveFile=app-cds.jsa \\");
        System.out.println("      -jar myapp.jar\n");

        System.out.println("The archive is memory-mapped — all JVM instances");
        System.out.println("sharing it use the same physical memory for class data.");
    }
}
```

**How to run:** `java AppCDSDemo.java`

Expected output:
```
=== Application Class-Data Sharing (AppCDS) ===

Java 10 extends CDS from JDK classes to your application classes.

Step 1 — Record which classes your app loads:
  $ java -Xshare:off -XX:DumpLoadedClassList=app.classlist \
      -jar myapp.jar

Step 2 — Create the shared archive:
  $ java -Xshare:dump -XX:SharedClassListFile=app.classlist \
      -XX:SharedArchiveFile=app-cds.jsa -cp myapp.jar

Step 3 — Run with the archive (repeat for each instance):
  $ java -Xshare:auto -XX:SharedArchiveFile=app-cds.jsa \
      -jar myapp.jar

The archive is memory-mapped — all JVM instances
sharing it use the same physical memory for class data.
```

The simplest walkthrough: the three-step AppCDS workflow explained step by step.

### Level 2 — Intermediate

```java
// File: AppCDSWorkflow.java
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class AppCDSWorkflow {

    public static void main(String[] args) throws Exception {
        System.out.println("=== AppCDS: Complete Workflow ===\n");

        // Simulate checking if CDS is active
        System.out.println("Checking CDS status:");
        // In real life: check with -Xshare:auto and read VM info
        // Here we simulate the concept

        System.out.println("  Default CDS (JDK classes only) is typically enabled");
        System.out.println("  in JDK 9+ via -Xshare:auto (default).\n");

        System.out.println("AppCDS extends this to your application classes:\n");

        System.out.println("1. Class list (.classlist):");
        System.out.println("   Lists every class your app loads at startup.");
        System.out.println("   Example content:");
        System.out.println("     java/lang/Object");
        System.out.println("     java/lang/String");
        System.out.println("     com/myapp/Main");
        System.out.println("     com/myapp/Service\n");

        System.out.println("2. Shared archive (.jsa):");
        System.out.println("   Pre-processed class metadata.");
        System.out.println("   Contains class structures, constant pools,");
        System.out.println("   method metadata — everything needed to");
        System.out.println("   skip class loading and verification.\n");

        System.out.println("3. Runtime: JVM memory-maps the .jsa file.");
        System.out.println("   Classes in the archive are 'pre-loaded'");
        System.out.println("   — the JVM uses them directly instead of");
        System.out.println("   loading from .class files.\n");

        System.out.println("Note: Starting JDK 13, AppCDS is simpler:");
        System.out.println("  $ java -XX:ArchiveClassesAtExit=app-cds.jsa -jar myapp.jar");
        System.out.println("  (Dynamic archive — no separate class-list step needed)");
    }
}
```

**How to run:** `java AppCDSWorkflow.java`

Expected output:
```
=== AppCDS: Complete Workflow ===

Checking CDS status:
  Default CDS (JDK classes only) is typically enabled
  in JDK 9+ via -Xshare:auto (default).

AppCDS extends this to your application classes:

1. Class list (.classlist):
   Lists every class your app loads at startup.
   Example content:
     java/lang/Object
     java/lang/String
     com/myapp/Main
     com/myapp/Service

2. Shared archive (.jsa):
   Pre-processed class metadata.
   Contains class structures, constant pools,
   method metadata — everything needed to
   skip class loading and verification.

3. Runtime: JVM memory-maps the .jsa file.
   Classes in the archive are 'pre-loaded'
   — the JVM uses them directly instead of
   loading from .class files.

Note: Starting JDK 13, AppCDS is simpler:
  $ java -XX:ArchiveClassesAtExit=app-cds.jsa -jar myapp.jar
  (Dynamic archive — no separate class-list step needed)
```

The real-world workflow details: what each artifact contains and how it's used at runtime. The note about JDK 13+ dynamic archives is important — the three-step process in Java 10 was simplified in later versions.

### Level 3 — Advanced

```java
// File: CDSBenchmark.java
import java.util.*;

public class CDSBenchmark {

    // Simulate a realistic application startup with class loading
    static class ServiceA { static { simulateWork("ServiceA init"); } }
    static class ServiceB { static { simulateWork("ServiceB init"); } }
    static class Repository { static { simulateWork("Repository init"); } }
    static class Controller { static { simulateWork("Controller init"); } }

    static void simulateWork(String name) {
        try { Thread.sleep(1); } catch (InterruptedException e) {}
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== AppCDS Benchmark (Simulated) ===\n");

        // Simulate "first run" — record class list
        long start1 = System.nanoTime();
        var a = new ServiceA();
        var b = new ServiceB();
        var r = new Repository();
        var c = new Controller();
        long time1 = System.nanoTime() - start1;

        // Simulate "with AppCDS" — classes pre-loaded, no init cost
        long start2 = System.nanoTime();
        var a2 = new ServiceA();  // static init already done — faster
        var b2 = new ServiceB();
        var r2 = new Repository();
        var c2 = new Controller();
        long time2 = System.nanoTime() - start2;

        double speedup = (double)(time1 - time2) / time1 * 100;

        System.out.printf("Without CDS: %,d ns%n", time1);
        System.out.printf("With CDS:    %,d ns (%.0f%% faster)%n", time2, speedup);
        System.out.println("(Second run simulates AppCDS — static initialisers already done)\n");

        System.out.println("Real AppCDS benefits (typical):");
        System.out.println("  Startup time:      10-30% faster");
        System.out.println("  Memory per JVM:    10-20% less");
        System.out.println("  Best for:          containers, microservices, serverless");
        System.out.println("  Less benefit for:  single-JVM, long-running apps\n");

        System.out.println("Command to test with your app:");
        System.out.println("  $ java -XX:+UnlockDiagnosticVMOptions -XX:SharedArchiveFile=my.jsa -Xshare:on -jar myapp.jar");
        System.out.println("  (If archive mismatches, JVM fails fast — use -Xshare:auto for graceful fallback)");
    }
}
```

**How to run:** `java CDSBenchmark.java`

Expected output:
```
=== AppCDS Benchmark (Simulated) ===

Without CDS: 4,500,000 ns
With CDS:    150,000 ns (97% faster)
(Second run simulates AppCDS — static initialisers already done)

Real AppCDS benefits (typical):
  Startup time:      10-30% faster
  Memory per JVM:    10-20% less
  Best for:          containers, microservices, serverless
  Less benefit for:  single-JVM, long-running apps

Command to test with your app:
  $ java -XX:+UnlockDiagnosticVMOptions -XX:SharedArchiveFile=my.jsa -Xshare:on -jar myapp.jar
  (If archive mismatches, JVM fails fast — use -Xshare:auto for graceful fallback)
```

The production-flavoured benchmark: a simulated comparison showing the concept (static initialisers run once; with CDS, they're already done at startup). The real AppCDS benefits table sets realistic expectations: 10–30% startup improvement and 10–20% memory savings, most valuable in containerised deployments.

## 6. Walkthrough

Tracing the AppCDS workflow for a Spring Boot microservice in a Kubernetes deployment:

1. **Build phase (CI/CD pipeline)**:
   - The application is built: `myapp.jar` with all dependencies.
   - `java -Xshare:off -XX:DumpLoadedClassList=app.classlist -jar myapp.jar` — the app starts normally, but additionally writes the name of every loaded class to `app.classlist`. This includes JDK classes (`java/lang/String`, `java/util/ArrayList`), framework classes (`org/springframework/...`), and application classes (`com/myapp/...`).
   - The app exits after recording the class list.

2. **Archive creation**:
   - `java -Xshare:dump -XX:SharedClassListFile=app.classlist -XX:SharedArchiveFile=app-cds.jsa -cp myapp.jar` — the JVM does not run the application; instead, it reads `app.classlist`, loads each class, verifies it, pre-computes class metadata (constant pools, method tables, field layouts), and writes everything to `app-cds.jsa`. This is a one-time build step. The `.jsa` file is ~20–50 MB for a typical Spring Boot app.

3. **Container image building**:
   - The `.jsa` file is baked into the Docker image alongside `myapp.jar`.
   - The container entrypoint is: `java -Xshare:auto -XX:SharedArchiveFile=/opt/app-cds.jsa -jar /opt/myapp.jar`.

4. **Runtime (container startup)**:
   - The JVM starts with `-Xshare:auto`. It checks if `/opt/app-cds.jsa` exists and is valid (matches the JDK version, classpath, and module configuration).
   - If valid: the JVM memory-maps the archive. Classes in the archive are "pre-loaded" — the JVM skips class loading, bytecode verification, and metadata allocation for them. The per-instance class metadata memory is replaced by a shared, read-only memory-mapped region.
   - If invalid (e.g., JAR changed, JDK version changed): `-Xshare:auto` falls back to normal class loading without error.
   - Multiple pods (JVM instances) on the same node share the same physical memory pages for the class archive, reducing overall memory pressure.

## 7. Gotchas & takeaways

> The shared archive is **tightly coupled** to the exact JDK version, classpath, and module configuration used to create it. If you change the JDK version, add/remove a JAR, or modify `module-info.class`, the archive becomes invalid. With `-Xshare:on`, the JVM refuses to start; with `-Xshare:auto` (recommended), it falls back to normal class loading silently. Always regenerate the archive after any classpath change.

- From JDK 13 onward, the dynamic AppCDS feature (`-XX:ArchiveClassesAtExit`) simplifies the workflow: run the app once, and the JVM writes the archive at exit. No separate class-list step needed.
- The `.jsa` file is platform-specific — an archive created on Linux x64 cannot be used on macOS or Windows. Generate it on the target platform.
- AppCDS works best for classes that are loaded at startup and remain loaded — application classes, framework classes, and frequently used JDK classes. Classes loaded dynamically at runtime (via reflection or custom classloaders) are not included.
- The memory savings are per-node, not per-JVM — if multiple JVMs on the same machine share the archive, they share physical memory. In containerised environments with one JVM per container, the benefit is primarily startup time, not memory, unless the container runtime supports page sharing.
- `-Xshare:dump` requires the application classes to be available on the classpath during archive creation — the JVM needs to actually load and verify them. A fat JAR works fine; custom classloader hierarchies may cause issues. 