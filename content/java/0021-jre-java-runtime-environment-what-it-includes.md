---
card: java
gi: 21
slug: jre-java-runtime-environment-what-it-includes
title: JRE (Java Runtime Environment) — what it includes
---

## 1. What it is

The **Java Runtime Environment (JRE)** is the subset of the Java platform needed to **run** (not compile) Java applications. It contains the JVM, the core class library (`java.*`, `javax.*` packages), and supporting files — everything an end user needs to execute a `.jar` file, but nothing needed to write or compile Java code.

Before Java 9, the JRE was a distinct, separately downloadable product — about 200 MB — smaller than the full JDK (~400 MB). From Java 9 onwards, Oracle stopped shipping a standalone JRE for desktop use, though vendors like Eclipse Temurin still publish JRE-only images (notably the Docker `eclipse-temurin:21-jre` image).

## 2. Why & when

The JRE matters in two contexts:

**Container/Docker:** `eclipse-temurin:21-jre` is ~170 MB vs `eclipse-temurin:21-jdk` at ~400 MB. For production containers that never compile code, the JRE image is the right choice.

**Legacy desktop distribution:** Before bundled JREs (Java 8 and earlier), desktop apps shipped a "requires Java X" label and end users had to install the JRE separately. Now most production JARs bundle their own JRE (via `jlink` or native image) or run in containers.

Use a JRE when:
- Building a Docker image for a Spring Boot JAR that never runs `javac`.
- Distributing a runtime-only environment where compilation is not needed.
- Minimising attack surface (no compiler = fewer exploitable surface area).

You do NOT use a JRE when:
- Building / compiling code (`javac` is not in the JRE).
- Running annotation processors, code generation tools, or build tasks.

## 3. Core concept

The JRE contains:

```
JRE
├── JVM                         (java executable + libjvm.so/.dll)
├── Core class library          (java.base, java.sql, java.xml, ...)
│   └── compiled as .jar / modules (rt.jar in Java 8, modules in Java 9+)
├── Supporting native libraries  (crypto, networking, font rendering)
├── Configuration files          (security policy, logging.properties)
└── Licence files
```

What is NOT in the JRE (but is in the JDK):
- `javac` (compiler)
- `javadoc` (documentation generator)
- `jdb` (debugger)
- `jar` (archive tool) — though in Java 9+ the `jar` command is part of the JDK
- `jshell` (REPL)
- Header files (`.h`) for JNI
- Source code (`src.zip`)

**JRE vs custom runtime image:** With `jlink` (Java 9+) you can create a custom runtime image containing only the modules your application needs — potentially smaller than a full JRE. A `jlink`-trimmed image for a simple CLI tool can be as small as 25–30 MB.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JDK contains JRE which contains JVM — nested containment">
  <!-- JDK (outermost) -->
  <rect x="20" y="20" width="640" height="180" rx="10" fill="#0d1117" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="6,3"/>
  <text x="340" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">JDK — Java Development Kit</text>
  <text x="580" y="42" fill="#8b949e" font-size="9" text-anchor="end" font-family="sans-serif">javac · jar · jdb · jshell · javadoc · jlink · jpackage</text>

  <!-- JRE (middle) -->
  <rect x="60" y="58" width="480" height="128" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="300" y="80" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">JRE — Java Runtime Environment</text>
  <text x="300" y="96" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Core class library · native libs · config files</text>

  <!-- JVM (innermost) -->
  <rect x="120" y="108" width="360" height="64" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="132" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">JVM — Java Virtual Machine</text>
  <text x="300" y="150" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">class loader · bytecode verifier · JIT · GC</text>
</svg>

JDK ⊃ JRE ⊃ JVM. Each layer adds tools on top of the inner layer.

## 5. Runnable example

Scenario: a program that prints which JRE features are available and what size a minimal JRE for this application would need to be — useful when optimising Docker image sizes.

### Level 1 — Basic

```java
// JreInfo.java
import java.lang.module.*;

public class JreInfo {
    public static void main(String[] args) {
        System.out.println("=== JRE Information ===");
        System.out.println("Runtime name : " + System.getProperty("java.runtime.name"));
        System.out.println("Runtime ver  : " + System.getProperty("java.runtime.version"));
        System.out.println("Java home    : " + System.getProperty("java.home"));
        System.out.println();

        // In a JRE (no compiler), Class.forName("com.sun.tools.javac.Main") fails
        boolean hasCompiler = classExists("com.sun.tools.javac.Main");
        System.out.println("Has javac (JDK only) : " + hasCompiler);
        System.out.println("Has jshell API       : " + classExists("jdk.jshell.JShell"));
        System.out.println();
        System.out.println(hasCompiler ? "Running on full JDK (includes JRE)" : "Running on JRE-only image");
    }

    static boolean classExists(String name) {
        try { Class.forName(name); return true; }
        catch (ClassNotFoundException e) { return false; }
    }
}
```

**How to run:** `java JreInfo.java`

On `eclipse-temurin:21-jre`, `classExists("com.sun.tools.javac.Main")` returns `false` — the compiler is not present. On a full JDK it returns `true`. This is the practical distinction between JRE and JDK.

### Level 2 — Intermediate

Same JRE probe extended to enumerate the modules present in the current runtime — showing the difference between a full JDK (70+ modules) and a JRE or `jlink` image (fewer modules).

```java
// JreModuleProfile.java
import java.lang.module.*;
import java.util.*;
import java.util.stream.*;

public class JreModuleProfile {

    // Modules present in a JRE but not necessarily a trimmed jlink image
    static final List<String> JRE_STANDARD_MODULES = List.of(
        "java.base", "java.logging", "java.xml", "java.naming",
        "java.sql", "java.desktop", "java.security.sasl"
    );

    // Modules present only in JDK (not JRE)
    static final List<String> JDK_ONLY_MODULES = List.of(
        "jdk.compiler", "jdk.jshell", "jdk.jdi", "jdk.javadoc",
        "jdk.jcmd", "jdk.jlink", "jdk.jpackage"
    );

    public static void main(String[] args) {
        Set<String> loaded = ModuleLayer.boot().modules().stream()
            .map(Module::getName)
            .collect(Collectors.toSet());

        System.out.println("=== JRE/JDK Module Profile ===");
        System.out.println("Total modules in boot layer: " + loaded.size());
        System.out.println();

        System.out.println("[ Standard JRE modules ]");
        for (String m : JRE_STANDARD_MODULES) {
            System.out.printf("  %-30s %s%n", m, loaded.contains(m) ? "PRESENT" : "absent (trimmed image)");
        }

        System.out.println("\n[ JDK-only modules (absent on JRE) ]");
        for (String m : JDK_ONLY_MODULES) {
            System.out.printf("  %-30s %s%n", m, loaded.contains(m) ? "PRESENT (full JDK)" : "absent (JRE or trimmed)");
        }

        System.out.println("\n[ Image type assessment ]");
        boolean hasCompiler = loaded.contains("jdk.compiler");
        boolean hasBase     = loaded.contains("java.base");
        System.out.println("  " + (hasCompiler ? "Full JDK" : "JRE or jlink-trimmed image"));
        System.out.println("  java.base present: " + hasBase + " (always required)");
    }
}
```

**How to run:** `java JreModuleProfile.java`

On a full JDK, `jdk.compiler` is present. On `eclipse-temurin:21-jre`, it's absent. On a `jlink` image you built yourself, only the modules you specified are present.

### Level 3 — Advanced

Same scenario grown to simulate the size of a minimal `jlink` image for different application types — the production tool you'd use to create a self-contained JRE-sized deployment artifact.

```java
// JlinkSizeEstimator.java
import java.lang.module.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.*;

public class JlinkSizeEstimator {

    // Approximate module sizes in MB (rough estimates for Java 21)
    static final Map<String, Double> MODULE_MB = new LinkedHashMap<>(Map.ofEntries(
        Map.entry("java.base",         40.0),
        Map.entry("java.logging",       2.0),
        Map.entry("java.xml",          12.0),
        Map.entry("java.naming",        3.0),
        Map.entry("java.sql",           2.5),
        Map.entry("java.net.http",      2.5),
        Map.entry("java.security.sasl", 0.5),
        Map.entry("java.desktop",      20.0),
        Map.entry("java.management",    2.0),
        Map.entry("jdk.crypto.ec",      1.5),
        Map.entry("jdk.localedata",    15.0)
    ));

    record Profile(String name, List<String> modules) {
        double estimatedMb() {
            return modules.stream().mapToDouble(m -> MODULE_MB.getOrDefault(m, 1.0)).sum();
        }
    }

    public static void main(String[] args) {
        List<Profile> profiles = List.of(
            new Profile("Minimal CLI tool",
                List.of("java.base")),
            new Profile("CLI with logging + XML",
                List.of("java.base", "java.logging", "java.xml")),
            new Profile("Spring Boot REST API",
                List.of("java.base", "java.logging", "java.xml", "java.naming",
                        "java.sql", "java.net.http", "java.security.sasl",
                        "java.management", "jdk.crypto.ec")),
            new Profile("Full JRE (runtime only)",
                new ArrayList<>(MODULE_MB.keySet()))
        );

        System.out.println("╔══════════════════════════════════════════════════╗");
        System.out.println("║       jlink Image Size Estimator                 ║");
        System.out.println("╚══════════════════════════════════════════════════╝\n");
        System.out.println("Current modules in boot layer: " + ModuleLayer.boot().modules().size());
        System.out.println();

        System.out.printf("%-35s  %-10s  %s%n", "Profile", "~Size", "Modules");
        System.out.println("-".repeat(85));
        for (Profile p : profiles) {
            System.out.printf("%-35s  ~%5.0f MB  %s%n", p.name(), p.estimatedMb(),
                p.modules().stream().collect(Collectors.joining(", ")));
        }

        System.out.println("\n[ jlink command for Spring Boot API profile ]");
        Profile spring = profiles.get(2);
        System.out.println("  jlink \\");
        System.out.println("    --add-modules " + String.join(",", spring.modules()) + " \\");
        System.out.println("    --output ./custom-jre \\");
        System.out.println("    --compress=2 --strip-debug --no-header-files --no-man-pages");
        System.out.println();
        System.out.println("  Then: ./custom-jre/bin/java -jar app.jar");
        System.out.println("  Docker: COPY --from=builder ./custom-jre /opt/jre");
        System.out.println("         ENTRYPOINT [\"/opt/jre/bin/java\", \"-jar\", \"/app.jar\"]");

        // Show actual module dependencies of this class
        System.out.println("\n[ Dependencies of THIS program ]");
        Module selfModule = JlinkSizeEstimator.class.getModule();
        System.out.println("  Module: " + (selfModule.isNamed() ? selfModule.getName() : "unnamed (classpath)"));
        System.out.println("  Tip: use 'jdeps --print-module-deps app.jar' to find your real module deps");
    }
}
```

**How to run:** `java JlinkSizeEstimator.java`

`jdeps --print-module-deps app.jar` (a JDK tool not available in a JRE) produces the exact `--add-modules` list for your specific JAR — then `jlink` builds a self-contained JRE image with only those modules.

## 6. Walkthrough

Execution in `JlinkSizeEstimator.main`:

1. **`ModuleLayer.boot().modules().size()`** — counts modules in the current boot layer. On a full JDK install: ~70. On `eclipse-temurin:21-jre`: ~60 (JDK-only modules removed). On a `jlink` image: as few as 10.

2. **`Profile` records** — each `Profile` holds a name and list of modules. `estimatedMb()` sums the approximate sizes from `MODULE_MB`. These are rough estimates; real sizes depend on compression, debug info stripping, and JDK version.

3. **Four profiles** — from minimal (1 module, ~40 MB) to full JRE (~100 MB). A Spring Boot API typically needs `java.base` + 8 more modules. `java.desktop` (Swing/AWT) is the largest optional module at ~20 MB; omitting it saves significant space.

4. **`jlink` command** — the printed command uses `--compress=2` (zip compression of class files), `--strip-debug` (removes debug symbols from the JVM binary), `--no-header-files` (removes JNI headers), `--no-man-pages`. Together these reduce the output by another 20–30%.

5. **`class.getModule()`** — returns the module this class belongs to. In source-launch mode (`java File.java`), the class is in the unnamed module. In a proper JAR with `module-info.java`, it would be in the named module.

Docker multi-stage build with custom JRE:
```
# Stage 1: build app and create custom JRE
FROM eclipse-temurin:21-jdk AS builder
COPY . /app
RUN cd /app && ./mvnw package -DskipTests
RUN jdeps --ignore-missing-deps --print-module-deps /app/target/app.jar > /modules.txt
RUN jlink --add-modules $(cat /modules.txt) --output /custom-jre --compress=2 --strip-debug

# Stage 2: tiny runtime image
FROM debian:12-slim
COPY --from=builder /custom-jre /opt/jre
COPY --from=builder /app/target/app.jar /app.jar
ENTRYPOINT ["/opt/jre/bin/java", "-jar", "/app.jar"]
```
Final image: ~80–120 MB (custom JRE + app JAR) vs ~400 MB (full JDK image).

## 7. Gotchas & takeaways

> **The standalone JRE download was discontinued for Java 11+** at Oracle. For runtime-only deployments, use `eclipse-temurin:21-jre` (Docker) or build a custom image with `jlink`. There is no `jdk-21-jre-windows-x64.exe` to download from oracle.com for Java 21+.

> **`jlink` requires modular JARs or a `--module-path`.** For non-modular "classpath" applications (most Spring Boot apps), `jdeps --print-module-deps` can still find the JDK module dependencies even if the app itself is non-modular. You link the JDK modules your app needs into the custom JRE; the app itself runs on the classpath.

- JRE = JVM + core class library + native libs + config. No compiler tools.
- `eclipse-temurin:21-jre` (~170 MB) vs `eclipse-temurin:21-jdk` (~400 MB) — use JRE in production containers.
- Java 9+ modular JDK: use `jlink` to build a custom JRE containing only the modules your app needs — as small as 25 MB.
- `jdeps --print-module-deps app.jar` discovers the exact JDK modules a JAR needs.
- No `javac` in JRE — annotation processors, build tools, and code generation cannot run.
- For zero-JRE deployments: GraalVM Native Image compiles the whole app + JRE into a single binary; no JRE needed at runtime.
