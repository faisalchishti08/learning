---
card: java
gi: 607
slug: jlink
title: JLink
---

## 1. What it is

`jlink` is a JDK 9 tool that creates custom, minimal Java runtime images. It takes your application's modules (or JARs on the classpath), resolves their transitive dependencies on JDK modules, and assembles a stripped-down runtime image containing only the JDK modules your application actually needs. The output is a directory that functions as a complete, self-contained Java runtime — no external JDK installation required, no unused modules wasting disk space. `jlink` is the tool that turns the module system from a compile-time concern into a deployment-time optimisation.

## 2. Why & when

A standard JDK installation is large — typically 300–400 MB — because it includes every module from `java.desktop` (AWT, Swing, sound) to `java.sql` to `jdk.jshell`, even if your microservice only uses `java.base`, `java.logging`, and `java.net.http`. Before `jlink`, the only way to reduce footprint was manual JRE stripping (error-prone) or shipping the full JRE (wasteful). With `jlink`, you produce a runtime image that is typically 30–50 MB for a basic service — a 10× reduction. This makes Java competitive for containerised deployments (Docker images), serverless functions, and embedded systems where image size directly impacts cold-start time and storage cost.

## 3. Core concept

```
# Build a custom runtime image for a modular application
jlink --module-path $JAVA_HOME/jmods:myapp \
      --add-modules com.myapp \
      --output myruntime \
      --strip-debug \
      --compress=2 \
      --no-header-files \
      --no-man-pages

# The output 'myruntime/' contains:
#   bin/java        (launcher)
#   lib/modules     (a single optimized image file)
#   conf/           (configuration)
#   legal/          (licenses for included modules)
```

`jlink` resolves modules from the given `--module-path`, determines the transitive closure of `--add-modules`, and produces a runtime image in `--output`. The `--compress` option (0=none, 1=constant sharing, 2=ZIP) controls how module files are packed. `--strip-debug`, `--no-header-files`, and `--no-man-pages` further reduce image size.

## 4. Diagram

<svg viewBox="0 0 580 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jlink creates a minimal runtime image containing only the modules your app needs">
  <rect x="20" y="10" width="540" height="190" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="40" y="30" width="120" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="100" y="55" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">myapp module</text>

  <text x="175" y="55" fill="#8b949e" font-size="10" font-family="monospace">──►</text>

  <rect x="190" y="25" width="90" height="50" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="235" y="43" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">jlink</text>
  <text x="235" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">resolve + link</text>

  <text x="295" y="50" fill="#8b949e" font-size="10" font-family="monospace">──►</text>

  <rect x="310" y="25" width="130" height="50" rx="4" fill="#f0883e" stroke="#f0883e"/>
  <text x="375" y="43" fill="#f0883e" font-size="10" text-anchor="middle" font-family="monospace">runtime image</text>
  <text x="375" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">30-50 MB (vs 300+ MB)</text>

  <text x="40" y="100" fill="#8b949e" font-size="10" font-family="sans-serif">Input: Full JDK modules (~300+ MB)</text>

  <rect x="40" y="110" width="80" height="22" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="80" y="125" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">java.base</text>
  <rect x="125" y="110" width="80" height="22" rx="4" fill="#8b949e" stroke="#8b949e" opacity="0.3"/>
  <text x="165" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">java.desktop</text>
  <rect x="210" y="110" width="80" height="22" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="250" y="125" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">java.logging</text>
  <rect x="295" y="110" width="80" height="22" rx="4" fill="#8b949e" stroke="#8b949e" opacity="0.3"/>
  <text x="335" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">java.sql</text>

  <text x="40" y="155" fill="#8b949e" font-size="10" font-family="sans-serif">Output: Only required modules (java.base + java.logging + your modules)</text>
  <text x="40" y="178" fill="#8b949e" font-size="10" font-family="sans-serif">Optimizations: --strip-debug, --compress=2, --no-header-files, --no-man-pages</text>
</svg>

`jlink` traces the module dependency graph from your `--add-modules` and excludes everything unreachable.

## 5. Runnable example

Scenario: building a custom runtime for a modular "Hello" application — starting with basic module setup and linking, extending to adding logging and stripping debug info, and finally comparing image sizes and launching from the custom runtime.

### Level 1 — Basic

```java
// File: com/greeting/Main.java  (modular app — directory structure shown)
/*

Directory structure:
  hello-app/
    com/greeting/Main.java
    module-info.java

Contents:

  // module-info.java
  module com.greeting {
      exports com.greeting;
  }

  // com/greeting/Main.java
  package com.greeting;
  public class Main {
      public static void main(String[] args) {
          System.out.println("Hello from a custom runtime!");
      }
  }

Build and link:
  javac -d out --module-source-path . $(find . -name '*.java')
  jlink --module-path $JAVA_HOME/jmods:out \
        --add-modules com.greeting \
        --output myruntime

Run:
  myruntime/bin/java -m com.greeting/com.greeting.Main
  → Hello from a custom runtime!

*/

// Simulation — the actual steps require a module source tree.
// This file demonstrates the concept runnably.

public class JLinkDemo {
    public static void main(String[] args) throws Exception {
        System.out.println("=== jlink: Custom Runtime Image Builder ===\n");

        // Step 1: Show what modules our app would need
        System.out.println("Step 1 — Application module: com.greeting");
        System.out.println("  Transitive JDK modules needed: java.base (always required)\n");

        // Step 2: Build the runtime (simulated)
        System.out.println("Step 2 — Build with jlink:");
        System.out.println("  $ jlink --module-path $JAVA_HOME/jmods:out \\");
        System.out.println("          --add-modules com.greeting \\");
        System.out.println("          --output myruntime\n");

        // Step 3: The resulting image
        System.out.println("Step 3 — Runtime image structure:");
        System.out.println("  myruntime/");
        System.out.println("    bin/java          ← launcher");
        System.out.println("    lib/modules        ← single compressed module file");
        System.out.println("    conf/              ← configuration");
        System.out.println("    legal/             ← licenses\n");

        // Step 4: Run it
        System.out.println("Step 4 — Run the app with the custom runtime:");
        System.out.println("  $ myruntime/bin/java -m com.greeting/com.greeting.Main");
        System.out.println("  Hello from a custom runtime!\n");

        // Step 5: Verify the runtime is self-contained
        System.out.println("Step 5 — No external JDK needed:");
        System.out.println("  $ myruntime/bin/java --version");
        System.out.println("  (prints the JDK version — self-contained)");

        // The key benefit
        System.out.println("\nKey benefit: The runtime contains ONLY java.base");
        System.out.println("and com.greeting — no java.desktop, java.sql, etc.");
    }
}
```

**How to run:** `java JLinkDemo.java`

Expected output (concept demonstration):
```
=== jlink: Custom Runtime Image Builder ===

Step 1 — Application module: com.greeting
  Transitive JDK modules needed: java.base (always required)

Step 2 — Build with jlink:
  $ jlink --module-path $JAVA_HOME/jmods:out \
          --add-modules com.greeting \
          --output myruntime

Step 3 — Runtime image structure:
  myruntime/
    bin/java          ← launcher
    lib/modules        ← single compressed module file
    conf/              ← configuration
    legal/             ← licenses

Step 4 — Run the app with the custom runtime:
  $ myruntime/bin/java -m com.greeting/com.greeting.Main
  Hello from a custom runtime!

Step 5 — No external JDK needed:
  $ myruntime/bin/java --version
  (prints the JDK version — self-contained)

Key benefit: The runtime contains ONLY java.base
and com.greeting — no java.desktop, java.sql, etc.
```

The simplest concept: a module-based app linked into a minimal runtime. The output runtime is self-contained — it has its own `java` launcher and only the modules needed.

### Level 2 — Intermediate

```java
// File: JLinkAdvanced.java
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class JLinkAdvanced {

    /*
    === Real jlink session (run in terminal) ===

    # 1. Create a modular app with logging
    mkdir -p hello-advanced/com/greeting
    cat > hello-advanced/module-info.java << 'EOF'
    module com.greeting {
        requires java.logging;
        exports com.greeting;
    }
    EOF

    cat > hello-advanced/com/greeting/Main.java << 'EOF'
    package com.greeting;
    import java.util.logging.Logger;
    public class Main {
        private static final Logger LOG = Logger.getLogger(Main.class.getName());
        public static void main(String[] args) {
            LOG.info("Application starting");
            System.out.println("Hello from " + System.getProperty("java.home"));
        }
    }
    EOF

    # 2. Compile
    javac -d out-advanced --module-source-path hello-advanced \
          hello-advanced/com/greeting/Main.java hello-advanced/module-info.java

    # 3. List the modules our app needs (jdeps)
    jdeps --module-path out-advanced -s --module com.greeting
    # Output:
    #   com.greeting -> java.base
    #   com.greeting -> java.logging

    # 4. Build minimal runtime with compression and stripping
    jlink --module-path $JAVA_HOME/jmods:out-advanced \
          --add-modules com.greeting \
          --output myruntime-advanced \
          --strip-debug \
          --compress=2 \
          --no-header-files \
          --no-man-pages

    # 5. Check what modules are included
    myruntime-advanced/bin/java --list-modules
    # Output:
    #   com.greeting
    #   java.base
    #   java.logging

    # 6. Compare sizes
    du -sh myruntime-advanced/
    # ~35 MB (vs ~300 MB for full JDK)

    # 7. Run it
    myruntime-advanced/bin/java -m com.greeting/com.greeting.Main
    # Output:
    #   Jul 09, 2026 INFO ... Main main: Application starting
    #   Hello from .../myruntime-advanced
    */

    public static void main(String[] args) throws Exception {
        System.out.println("=== jlink with Logging: Module Dependencies ===\n");

        System.out.println("Our app module (com.greeting) requires:");
        System.out.println("  java.base       (String, System, Object — always needed)");
        System.out.println("  java.logging    (Logger — for structured logging)\n");

        System.out.println("jlink resolves the transitive closure:");
        System.out.println("  com.greeting");
        System.out.println("    → java.logging");
        System.out.println("      → java.base (required by java.logging)");
        System.out.println("        → (nothing further — java.base has no dependencies)\n");

        System.out.println("Total modules in image: 3 (com.greeting + java.logging + java.base)");
        System.out.println("vs full JDK: ~70+ modules included\n");

        System.out.println("Optimization flags:");
        System.out.println("  --strip-debug        Remove debug info from class files");
        System.out.println("  --compress=2         ZIP-compress module files (best compression)");
        System.out.println("  --no-header-files    Exclude C/C++ header files");
        System.out.println("  --no-man-pages       Exclude man pages\n");

        System.out.println("Result: ~35 MB custom runtime (vs ~300 MB full JDK)");
    }
}
```

**How to run:** `java JLinkAdvanced.java`

Expected output:
```
=== jlink with Logging: Module Dependencies ===

Our app module (com.greeting) requires:
  java.base       (String, System, Object — always needed)
  java.logging    (Logger — for structured logging)

jlink resolves the transitive closure:
  com.greeting
    → java.logging
      → java.base (required by java.logging)
        → (nothing further — java.base has no dependencies)

Total modules in image: 3 (com.greeting + java.logging + java.base)
vs full JDK: ~70+ modules included

Optimization flags:
  --strip-debug        Remove debug info from class files
  --compress=2         ZIP-compress module files (best compression)
  --no-header-files    Exclude C/C++ header files
  --no-man-pages       Exclude man pages

Result: ~35 MB custom runtime (vs ~300 MB full JDK)
```

The real-world concern: adding a second JDK module (`java.logging`) expands the image from just `java.base` to `java.base` + `java.logging`. The `jlink` output size grows, but only by the size of the modules you actually use. The optimisation flags (`--strip-debug`, `--compress=2`, `--no-header-files`, `--no-man-pages`) shave additional megabytes.

### Level 3 — Advanced

```java
// File: JLinkProductionDemo.java
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class JLinkProductionDemo {

    record ModuleInfo(String name, String size, String purpose) {}

    public static void main(String[] args) throws Exception {
        System.out.println("=== jlink in Production: Docker Image Optimization ===\n");

        // Simulate a typical microservice's module needs
        List<ModuleInfo> serviceModules = List.of(
            new ModuleInfo("com.myservice",     "200 KB",  "Application code"),
            new ModuleInfo("java.base",         "~20 MB",  "Core JDK (always)"),
            new ModuleInfo("java.logging",      "~1 MB",   "Structured logging"),
            new ModuleInfo("java.net.http",     "~2 MB",   "HTTP client (REST calls)"),
            new ModuleInfo("java.sql",          "~2 MB",   "JDBC (db access)"),
            new ModuleInfo("java.xml",          "~1 MB",   "XML parsing")
        );

        System.out.println("Modules needed by our microservice:");
        for (var m : serviceModules) {
            System.out.printf("  %-20s %-8s  %s%n", m.name(), m.size(), m.purpose());
        }

        long totalAppx = 26; // approximate MB
        System.out.printf("\n  Total (approx): ~%d MB%n", totalAppx);
        System.out.println("  vs full JDK:    ~300 MB\n");

        System.out.println("╔══════════════════════════════════════════╗");
        System.out.println("║  Dockerfile comparison                   ║");
        System.out.println("╠══════════════════════════════════════════╣");
        System.out.println("║  BEFORE (full JDK):                      ║");
        System.out.println("║    FROM eclipse-temurin:17-jre           ║");
        System.out.println("║    # Image size: ~200 MB                 ║");
        System.out.println("║                                          ║");
        System.out.println("║  AFTER (custom jlink image):             ║");
        System.out.println("║    # Build stage: create runtime         ║");
        System.out.println("║    RUN jlink --add-modules ... \\         ║");
        System.out.println("║        --output /opt/runtime             ║");
        System.out.println("║    # Runtime stage: copy only runtime    ║");
        System.out.println("║    FROM alpine:3.19                      ║");
        System.out.println("║    COPY --from=builder /opt/runtime ...  ║");
        System.out.println("║    # Image size: ~30 MB                  ║");
        System.out.println("╚══════════════════════════════════════════╝");

        System.out.println("\nBenefits in production:");
        System.out.println("  • Docker image: 200 MB → 30 MB (6.6× smaller)");
        System.out.println("  • Cold start: faster pull + smaller footprint");
        System.out.println("  • Attack surface: only 6 modules vs 70+");
        System.out.println("  • Compliance: you know exactly which JDK modules run");

        // Actually check the current JVM's module list
        System.out.println("\n\nCurrent JVM's module count (for reference):");
        ModuleLayer.boot().modules().stream()
            .map(Module::getName)
            .filter(n -> n.startsWith("java.") || n.startsWith("jdk."))
            .sorted()
            .forEach(n -> System.out.println("  " + n));
    }
}
```

**How to run:** `java JLinkProductionDemo.java`

Expected output (module list varies by JDK version):
```
=== jlink in Production: Docker Image Optimization ===

Modules needed by our microservice:
  com.myservice         200 KB   Application code
  java.base             ~20 MB   Core JDK (always)
  java.logging          ~1 MB    Structured logging
  java.net.http         ~2 MB    HTTP client (REST calls)
  java.sql              ~2 MB    JDBC (db access)
  java.xml              ~1 MB    XML parsing

  Total (approx): ~26 MB
  vs full JDK:    ~300 MB

╔══════════════════════════════════════════╗
║  Dockerfile comparison                   ║
╠══════════════════════════════════════════╣
║  BEFORE (full JDK):                      ║
║    FROM eclipse-temurin:17-jre           ║
║    # Image size: ~200 MB                 ║
║                                          ║
║  AFTER (custom jlink image):             ║
║    # Build stage: create runtime         ║
║    RUN jlink --add-modules ... \         ║
║        --output /opt/runtime             ║
║    # Runtime stage: copy only runtime    ║
║    FROM alpine:3.19                      ║
║    COPY --from=builder /opt/runtime ...  ║
║    # Image size: ~30 MB                  ║
╚══════════════════════════════════════════╝

Benefits in production:
  • Docker image: 200 MB → 30 MB (6.6× smaller)
  • Cold start: faster pull + smaller footprint
  • Attack surface: only 6 modules vs 70+
  • Compliance: you know exactly which JDK modules run


Current JVM's module count (for reference):
  java.base
  java.compiler
  java.datatransfer
  ...
```

The production-flavoured analysis: comparing the full-JDK Docker image approach with a `jlink`-based multi-stage Docker build. A full `eclipse-temurin:17-jre` is ~200 MB; a custom `jlink` image for a microservice that needs only 6 modules is ~30 MB. The multi-stage Docker build pattern (build the runtime in a JDK stage, copy only the runtime into a slim Alpine stage) is the standard production approach. The final section shows the actual modules in the current JVM — all 70+ of them, most of which any given application never uses.

## 6. Walkthrough

Tracing the `jlink` tool execution from the Level 2 example:

1. **User runs the command**: `jlink --module-path $JAVA_HOME/jmods:out-advanced --add-modules com.greeting --output myruntime-advanced --strip-debug --compress=2 --no-header-files --no-man-pages`

2. `jlink` starts by parsing `--module-path`. It finds two entries:
   - `$JAVA_HOME/jmods` — the JDK's module files (`.jmod` format, containing `java.base`, `java.logging`, etc.)
   - `out-advanced` — the compiled application module directory with `com.greeting`

3. `jlink` reads `--add-modules com.greeting` as the root module. It starts a dependency resolution:
   - `com.greeting` → declared `requires java.logging;` in its `module-info.class`.
   - `java.logging` → `requires java.base;` (transitive).
   - `java.base` → no further dependencies (it's the root module).
   - Resolution complete: `[com.greeting, java.logging, java.base]`.

4. `jlink` builds the module graph. It excludes all JDK modules not in the transitive closure (`java.desktop`, `java.sql`, `jdk.jshell`, etc.). The output image will contain exactly 3 modules.

5. `jlink` processes each resolved module:
   - Reads the `.jmod` file for JDK modules, the exploded directory for `com.greeting`.
   - With `--strip-debug`, it removes debugging attributes (`LineNumberTable`, `LocalVariableTable`, etc.) from class files.
   - With `--compress=2`, it compresses resources using ZIP.
   - With `--no-header-files` and `--no-man-pages`, it skips those sections.

6. `jlink` writes the output to `myruntime-advanced/`:
   - `bin/java` — the launcher, configured to use the custom module path.
   - `lib/modules` — the compressed module image (a single file).
   - `conf/` — default configuration.
   - `legal/` — licenses for all included modules.
   - `release` — version information file.

7. The runtime is ready. `myruntime-advanced/bin/java -m com.greeting/com.greeting.Main` launches the application from this custom runtime — no `$JAVA_HOME` needed.

```
jlink command
  │
  ├── Parse --module-path
  │     JDK jmods/ → [java.base, java.logging, java.desktop, ...]
  │     out-advanced/ → [com.greeting]
  │
  ├── Resolve dependencies from --add-modules com.greeting
  │     com.greeting → java.logging → java.base
  │     [
  │
  ├── Apply optimizations
  │     --strip-debug → remove debug info from .class files
  │     --compress=2  → ZIP-compress resources
  │     --no-header-files, --no-man-pages → skip
  │
  └── Write output to myruntime-advanced/
        bin/java  (launcher)
        lib/modules  (compressed module image: ~35 MB)
        conf/, legal/, release
```

## 7. Gotchas & takeaways

> `jlink` can only link **explicit modules** (modules with `module-info.class`) and **automatic modules** — it cannot link unnamed modules (JARs on the classpath without module descriptors). If your application is not modularised, use `jdeps --generate-module-info` to generate module descriptors first, or use `jpackage` (for packaging, not linking) as an alternative.

- The `--output` directory must not already exist — `jlink` refuses to overwrite an existing directory. Delete it first or use a new output path.
- `jlink` images are **platform-specific** — a runtime image built on Linux x64 cannot run on macOS or Windows. You must build on the target platform or cross-link with the appropriate JDK build.
- The `--bind-services` flag is critical if your application uses `ServiceLoader` — without it, `jlink` may exclude service provider modules that are not directly required but are discovered at runtime.
- `jlink` does not create an installer or native package — it produces a directory-based runtime. For packaging into platform-native installers (`.msi`, `.dmg`, `.deb`), use `jpackage` (JDK 14+), which internally uses `jlink` to create the runtime and then wraps it.
- `jdeps` is the companion tool — before linking, run `jdeps --module-path your-app -s --module com.yourmodule` to see exactly which JDK modules your app needs. Add only those modules to `--add-modules`. 