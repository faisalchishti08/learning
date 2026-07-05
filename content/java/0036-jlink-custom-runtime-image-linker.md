---
card: java
gi: 36
slug: jlink-custom-runtime-image-linker
title: jlink — custom runtime image linker
---

## 1. What it is

**`jlink`** is the JDK tool that assembles a custom Java runtime image containing only the modules your application needs. The output is a self-contained directory with a `bin/java` launcher and only the module subset you specified — no full JDK or JRE required on the target machine.

`jlink` ships with the JDK (`jdk.jlink` module). It requires modular JARs or a module path — it cannot create an image from pure classpath JARs without at least knowing which JDK modules they need (discoverable via `jdeps`).

## 2. Why & when

`jlink` is the right tool when:
- **Minimising Docker image size** — a `jlink` image for a Spring Boot REST API is ~50–80 MB vs 400 MB for a full JDK image.
- **Distributing CLI tools** — ship a single directory containing the JRE + app, no Java installation required on the target.
- **Serverless cold starts** — smaller JRE → less to load into memory → faster Lambda cold start (combined with CDS/AppCDS).
- **Security** — fewer modules = smaller attack surface (no `jdk.compiler`, no `jshell`, no `jdb`).

`jlink` requires:
1. All application JARs (if modular) on `--module-path`.
2. A list of modules to include (`--add-modules`).
3. A JDK, not just a JRE (the `jlink` tool itself is JDK-only).

The `jdeps --print-module-deps app.jar` output feeds directly into `jlink --add-modules`.

## 3. Core concept

```bash
jlink [options] --module-path <path> --add-modules <modules> --output <dir>

Essential flags:
  --module-path <path>     where to find modules (JDK modules auto-included)
  --add-modules <list>     comma-separated modules to include (from jdeps output)
  --output <dir>           directory to create the runtime image in

Size reduction flags (safe to combine):
  --compress=2             ZIP-compress class files inside the image
  --strip-debug            remove debug symbols from native JVM binaries
  --no-header-files        remove JNI header files (C/C++ only)
  --no-man-pages           remove man pages

Launcher shortcut:
  --launcher name=module/mainClass   add a launch script  (e.g. --launcher myapp=com.example/com.example.Main)

Other useful flags:
  --bind-services          include service providers (ServiceLoader) reachable from included modules
  --ignore-signing-information  needed if any JAR is signed
  --list-modules           list modules in the image and exit
  --endian <little|big>    target CPU byte order (cross-compilation)
```

Typical workflow:
```bash
# Step 1: find needed modules
jdeps --ignore-missing-deps --print-module-deps app.jar

# Step 2: link
jlink \
  --add-modules java.base,java.logging,java.net.http,java.sql \
  --compress=2 \
  --strip-debug \
  --no-header-files \
  --no-man-pages \
  --output custom-jre

# Step 3: run
custom-jre/bin/java -jar app.jar
```

Docker multi-stage build:
```dockerfile
FROM eclipse-temurin:21-jdk AS builder
COPY . /app
RUN cd /app && ./mvnw -q package -DskipTests
RUN jdeps --ignore-missing-deps --print-module-deps target/app.jar > /modules.txt
RUN jlink --add-modules $(cat /modules.txt) --compress=2 --strip-debug \
          --no-header-files --no-man-pages --output /custom-jre

FROM debian:12-slim
COPY --from=builder /custom-jre /opt/jre
COPY --from=builder /app/target/app.jar /app.jar
ENTRYPOINT ["/opt/jre/bin/java", "-jar", "/app.jar"]
```

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jlink assembles selected modules from JDK into a minimal custom JRE directory">
  <rect x="10" y="10" width="660" height="200" rx="8" fill="#0d1117"/>

  <!-- JDK modules pool -->
  <rect x="20" y="35" width="200" height="140" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="120" y="55" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">JDK Modules</text>
  <text x="35" y="72"  fill="#6db33f" font-size="9" font-family="monospace">java.base ──────── ●</text>
  <text x="35" y="87"  fill="#6db33f" font-size="9" font-family="monospace">java.logging ───── ●</text>
  <text x="35" y="102" fill="#6db33f" font-size="9" font-family="monospace">java.sql ─────────●</text>
  <text x="35" y="117" fill="#8b949e" font-size="9" font-family="monospace">java.desktop ──── ○</text>
  <text x="35" y="132" fill="#8b949e" font-size="9" font-family="monospace">jdk.compiler ─── ○</text>
  <text x="35" y="147" fill="#8b949e" font-size="9" font-family="monospace">jdk.jshell ────── ○</text>
  <text x="35" y="162" fill="#8b949e" font-size="9" font-family="monospace">... (70+ modules) ○</text>

  <!-- jlink tool -->
  <rect x="260" y="80" width="100" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="310" y="104" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">jlink</text>
  <text x="310" y="120" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">--add-modules</text>

  <!-- arrows in -->
  <line x1="220" y1="90"  x2="255" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jl1)"/>
  <line x1="220" y1="100" x2="255" y2="103" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="220" y1="110" x2="255" y2="106" stroke="#6db33f" stroke-width="1.5"/>

  <!-- arrow out -->
  <line x1="360" y1="105" x2="395" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jl2)"/>

  <!-- Output image -->
  <rect x="395" y="35" width="255" height="150" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="520" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">custom-jre/</text>
  <text x="415" y="73"  fill="#e6edf3" font-size="9" font-family="monospace">bin/java</text>
  <text x="415" y="88"  fill="#8b949e" font-size="9" font-family="monospace">lib/modules  (only 3)</text>
  <text x="415" y="103" fill="#8b949e" font-size="9" font-family="monospace">lib/server/libjvm.so</text>
  <text x="415" y="118" fill="#8b949e" font-size="9" font-family="monospace">conf/ release legal/</text>
  <text x="415" y="143" fill="#6db33f" font-size="9" font-family="monospace">Size: ~50–80 MB</text>
  <text x="415" y="157" fill="#8b949e" font-size="8" font-family="sans-serif">vs 400 MB full JDK</text>
  <text x="415" y="171" fill="#8b949e" font-size="8" font-family="sans-serif">no Java needed on target</text>

  <defs>
    <marker id="jl1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
    <marker id="jl2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
  </defs>
</svg>

`jlink` selects the specified modules from the JDK module pool and produces a compact `custom-jre/` directory. Unneeded modules are excluded.

## 5. Runnable example

Scenario: build a minimal custom JRE, measure its size, and run a simple application using it — end-to-end from module discovery to execution.

### Level 1 — Basic

```java
// JlinkBasic.java
import java.nio.file.*;
import java.util.*;

public class JlinkBasic {
    public static void main(String[] args) throws Exception {
        System.out.println("=== jlink custom runtime image demo ===\n");

        // Show current module set
        Set<Module> mods = java.lang.ModuleLayer.boot().modules();
        System.out.println("Current JVM modules: " + mods.size());

        // Check jlink availability
        Path jlink = findTool("jlink");
        Path jdeps  = findTool("jdeps");
        System.out.println("jlink found: " + (jlink != null ? jlink : "NOT FOUND — needs JDK"));
        System.out.println("jdeps found: " + (jdeps != null ? jdeps : "NOT FOUND — needs JDK"));

        // Show what a minimal jlink command looks like
        System.out.println("\n[ Minimal jlink command ]");
        System.out.println("  jlink \\");
        System.out.println("    --add-modules java.base \\");
        System.out.println("    --compress=2 --strip-debug \\");
        System.out.println("    --no-header-files --no-man-pages \\");
        System.out.println("    --output /tmp/min-jre");
        System.out.println("\n  # Result: ~30–35 MB (java.base only)");
        System.out.println("  # Compare: full JDK ~400 MB, eclipse-temurin:21-jre ~170 MB");

        // Module size estimates
        System.out.println("\n[ Cumulative size by module (estimates) ]");
        Object[][] modules = {
            {"java.base",           "~40 MB", "always included"},
            {"+ java.logging",      "~42 MB", "+2 MB"},
            {"+ java.xml",          "~54 MB", "+12 MB"},
            {"+ java.sql",          "~57 MB", "+3 MB"},
            {"+ java.net.http",     "~60 MB", "+3 MB"},
            {"+ java.management",   "~62 MB", "+2 MB"},
            {"+ java.desktop",      "~82 MB", "+20 MB (Swing/AWT, avoid if possible)"},
        };
        for (var r : modules)
            System.out.printf("  %-25s %-10s %s%n", r[0], r[1], r[2]);
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java JlinkBasic.java`

`java.base` is always required and is ~40 MB. Each additional module adds to the image. `java.desktop` is the heaviest optional module — exclude it for server-side applications.

### Level 2 — Intermediate

Same jlink demo extended to actually build a minimal custom JRE (java.base only) and measure its size vs the full JDK.

```java
// JlinkBuildImage.java
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.*;

public class JlinkBuildImage {
    public static void main(String[] args) throws Exception {
        Path jlinkTool = findTool("jlink");
        if (jlinkTool == null) { System.err.println("jlink not found — JDK required"); return; }

        Path outDir = Path.of(System.getProperty("java.io.tmpdir")).resolve("min-jre-" + System.currentTimeMillis());

        System.out.println("=== Building minimal custom JRE ===");
        System.out.println("Output: " + outDir + "\n");

        // Build with java.base only
        ProcessBuilder pb = new ProcessBuilder(
            jlinkTool.toString(),
            "--add-modules", "java.base",
            "--compress=2",
            "--strip-debug",
            "--no-header-files",
            "--no-man-pages",
            "--output", outDir.toString()
        );
        pb.redirectErrorStream(true);
        Process p = pb.start();
        String output = new String(p.getInputStream().readAllBytes());
        int rc = p.waitFor();

        if (rc != 0) {
            System.out.println("jlink failed: " + output);
            return;
        }
        System.out.println("jlink succeeded!");

        // Measure size
        long sizeMB = Files.walk(outDir)
            .filter(Files::isRegularFile)
            .mapToLong(f -> { try { return Files.size(f); } catch (Exception e) { return 0; } })
            .sum() / (1024 * 1024);

        System.out.printf("Image size: %d MB%n", sizeMB);
        System.out.printf("Full JDK  : ~%d MB%n", dirSizeMB(Path.of(System.getProperty("java.home"))));

        // List top-level directories
        System.out.println("\nImage structure:");
        Files.list(outDir).sorted().forEach(d ->
            System.out.println("  " + outDir.relativize(d) + "/"));

        // Test: run the custom JRE
        Path customJava = outDir.resolve("bin/java");
        if (!Files.exists(customJava)) customJava = outDir.resolve("bin/java.exe");
        if (Files.exists(customJava)) {
            System.out.println("\nRunning: " + customJava + " --version");
            Process vp = new ProcessBuilder(customJava.toString(), "--version").start();
            System.out.println(new String(vp.getInputStream().readAllBytes()).strip());
            vp.waitFor();

            System.out.println("\nRunning: " + customJava + " --list-modules");
            Process lp = new ProcessBuilder(customJava.toString(), "--list-modules").start();
            System.out.print("  Modules: ");
            System.out.println(new String(lp.getInputStream().readAllBytes()).strip());
            lp.waitFor();
        }

        // Cleanup
        Files.walk(outDir).sorted(Comparator.reverseOrder()).forEach(f -> f.toFile().delete());
        System.out.println("\nCleaned up " + outDir);
    }

    static long dirSizeMB(Path dir) {
        try {
            return Files.walk(dir).filter(Files::isRegularFile)
                .mapToLong(f -> { try { return Files.size(f); } catch (Exception e) { return 0; } })
                .sum() / (1024 * 1024);
        } catch (Exception e) { return -1; }
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java JlinkBuildImage.java`

This builds a real `java.base`-only JRE in a temp directory, runs it to check `--version`, and measures the size. The resulting image is typically 30–40 MB.

### Level 3 — Advanced

Same scenario grown to simulate a full Docker-style workflow: discover modules with `jdeps`, link, embed an app JAR, and show the complete multi-stage build pattern.

```java
// JlinkWorkflow.java
import javax.tools.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.*;

public class JlinkWorkflow {

    // A minimal app that uses java.base + java.logging
    static final String APP_SOURCE =
        "import java.util.logging.*;\n" +
        "import java.util.*;\n" +
        "public class App {\n" +
        "    private static final Logger LOG = Logger.getLogger(\"App\");\n" +
        "    public static void main(String[] args) {\n" +
        "        LOG.info(\"App started\");\n" +
        "        System.out.println(\"Running in custom JRE!\");\n" +
        "        System.out.println(\"Java: \" + System.getProperty(\"java.version\"));\n" +
        "        System.out.println(\"Modules in boot layer: \" +\n" +
        "            java.lang.ModuleLayer.boot().modules().size());\n" +
        "    }\n" +
        "}\n";

    public static void main(String[] args) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        Path jdepsTool  = findTool("jdeps");
        Path jlinkTool  = findTool("jlink");
        if (compiler == null || jdepsTool == null || jlinkTool == null) {
            System.err.println("Full JDK required (javac, jdeps, jlink)"); return;
        }

        Path workDir = Files.createTempDirectory("jlink-workflow");
        Path appSrc  = workDir.resolve("App.java");
        Path classDir = Files.createDirectories(workDir.resolve("classes"));
        Path jreDir   = workDir.resolve("custom-jre");
        Path jarFile  = workDir.resolve("app.jar");

        System.out.println("=== Full jlink workflow: compile → jdeps → jlink → run ===\n");

        // Step 1: compile
        Files.writeString(appSrc, APP_SOURCE);
        compiler.run(null, null, null, "-d", classDir.toString(), appSrc.toString());
        System.out.println("Step 1: compiled App.java → " + classDir.resolve("App.class"));

        // Step 2: create a JAR
        Process jarProc = new ProcessBuilder(findTool("jar").toString(),
            "cf", jarFile.toString(), "-C", classDir.toString(), ".")
            .redirectErrorStream(true).start();
        jarProc.waitFor();
        System.out.println("Step 2: created app.jar (" + Files.size(jarFile) + " bytes)");

        // Step 3: jdeps to discover modules
        Process jdepsProc = new ProcessBuilder(jdepsTool.toString(),
            "--ignore-missing-deps", "--print-module-deps", jarFile.toString())
            .redirectErrorStream(true).start();
        String modules = new String(jdepsProc.getInputStream().readAllBytes()).strip();
        jdepsProc.waitFor();
        System.out.println("Step 3: jdeps modules → " + modules);

        // Step 4: jlink
        ProcessBuilder jlinkPb = new ProcessBuilder(jlinkTool.toString(),
            "--add-modules", modules,
            "--compress=2", "--strip-debug",
            "--no-header-files", "--no-man-pages",
            "--output", jreDir.toString());
        jlinkPb.redirectErrorStream(true);
        Process jlinkProc = jlinkPb.start();
        String jlinkOut = new String(jlinkProc.getInputStream().readAllBytes());
        jlinkProc.waitFor();
        if (!jlinkOut.isBlank()) System.out.println("  jlink: " + jlinkOut.strip());

        long jreMB = Files.walk(jreDir).filter(Files::isRegularFile)
            .mapToLong(f -> { try { return Files.size(f); } catch (Exception e) { return 0; } })
            .sum() / (1024 * 1024);
        System.out.printf("Step 4: custom JRE built — %d MB (modules: %s)%n", jreMB, modules);

        // Step 5: run app with custom JRE
        Path customJava = jreDir.resolve("bin/java");
        if (!Files.exists(customJava)) customJava = jreDir.resolve("bin/java.exe");

        System.out.println("\nStep 5: running App.class with custom JRE");
        Process runProc = new ProcessBuilder(customJava.toString(),
            "-cp", classDir.toString(), "App")
            .redirectErrorStream(true).start();
        System.out.println(new String(runProc.getInputStream().readAllBytes()).indent(2));
        runProc.waitFor();

        System.out.println("[ Docker equivalent ]");
        System.out.println("  FROM eclipse-temurin:21-jdk AS builder");
        System.out.println("  RUN jdeps --print-module-deps target/app.jar > /modules.txt");
        System.out.println("  RUN jlink --add-modules $(cat /modules.txt) --compress=2 --strip-debug \\");
        System.out.println("            --no-header-files --no-man-pages --output /custom-jre");
        System.out.println("  FROM debian:12-slim");
        System.out.println("  COPY --from=builder /custom-jre /opt/jre");
        System.out.println("  COPY --from=builder /app.jar /app.jar");
        System.out.println("  ENTRYPOINT [\"/opt/jre/bin/java\", \"-jar\", \"/app.jar\"]");

        Files.walk(workDir).sorted(Comparator.reverseOrder()).forEach(f -> f.toFile().delete());
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java JlinkWorkflow.java`

Full end-to-end: compile → JAR → `jdeps` module discovery → `jlink` custom JRE → run app with custom JRE. The final `custom-jre/` would go into the Docker `COPY --from=builder` stage.

## 6. Walkthrough

Execution in `JlinkWorkflow.main`:

1. **Compile** — `App.java` imports `java.util.logging.Logger` and `java.util.*`. Standard compile to `classes/App.class`.

2. **Create JAR** — `jar cf app.jar -C classes .` creates a plain JAR (no `MANIFEST.MF Main-Class` — run with `-cp` for this demo). For `-jar`, add `--main-class App` to the jar command.

3. **`jdeps --print-module-deps app.jar`** — output: `java.base,java.logging` (because `Logger` is in `java.logging`). This is the comma-separated list fed directly to `jlink --add-modules`.

4. **`jlink` execution** — takes ~2–5 seconds on a modern machine. `--compress=2` zip-compresses class files inside the `lib/modules` JIMAGE file. `--strip-debug` removes DWARF debug symbols from native JVM binaries (saves 10–20 MB).

5. **Run with custom JRE** — `custom-jre/bin/java -cp classes App`. The output shows `Modules in boot layer: 2` (java.base + java.logging) — vs 70+ for a full JDK. All other JDK modules are physically absent from `custom-jre/lib/modules`.

6. **Docker pattern** — the multi-stage Dockerfile uses the JDK-based image for the build stage (needs `jlink`), then copies only the `custom-jre/` into a minimal base image (Debian slim). The final image needs no JDK, no JRE package — just the custom JRE directory.

## 7. Gotchas & takeaways

> **`jlink` requires all application JARs to be modular or their JDK module deps to be explicitly listed.** For non-modular "classpath" apps (most Spring Boot apps), use `jdeps --ignore-missing-deps --print-module-deps` to find the JDK module list, then `jlink` that. Your app code runs on the classpath; you only `jlink` the JDK modules.

> **`--bind-services` is needed if your code uses `ServiceLoader` to discover JDK services.** JDBC drivers (loaded via `DriverManager`), crypto providers, charset providers, and XML parsers all use ServiceLoader. Without `--bind-services`, those services may not be present in the image.

- `jlink --add-modules M1,M2 --output dir` → minimal JRE with only M1 and M2.
- `--compress=2 --strip-debug --no-header-files --no-man-pages` → save ~30–50% image size.
- `jdeps --print-module-deps app.jar` → get the `--add-modules` list automatically.
- Output image is self-contained: `dir/bin/java -jar app.jar` works with no Java install needed.
- `--bind-services` for ServiceLoader-dependent code (JDBC, crypto, XML parsers).
- Docker: build JRE in a JDK stage, copy `custom-jre/` into a minimal base image.
