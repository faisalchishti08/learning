---
card: java
gi: 35
slug: jdeps-dependency-analyzer
title: jdeps — dependency analyzer
---

## 1. What it is

**`jdeps`** is the JDK static dependency analyzer. It reads `.class` files and JARs, traces all class-level and module-level dependencies, and reports which packages, modules, or internal APIs each class depends on. `jdeps` is part of `jdk.jdeps` module, JDK-only.

`jdeps` is the tool that answers: "Which JDK modules does my application actually use?" — the prerequisite to running `jlink` to build a minimal custom JRE.

## 2. Why & when

`jdeps` matters when:
- **Building a minimal `jlink` image** — `jdeps --print-module-deps app.jar` outputs exactly the `--add-modules` list for `jlink`.
- **Detecting internal API usage** — `jdeps --jdk-internals app.jar` lists `sun.*`, `com.sun.*` usage that will break under `--illegal-access=deny` (Java 16+).
- **Migration to modules** — `jdeps --generate-module-info . lib.jar` generates a draft `module-info.java` for a non-modular JAR.
- **Dependency auditing** — identify third-party library chains pulling in unexpected JDK internals.
- **Split-package detection** — `jdeps` warns when a package is split across multiple JARs/modules (illegal in the module system).

## 3. Core concept

Key `jdeps` commands:

```bash
# Print module-level summary (for jlink)
jdeps --print-module-deps app.jar
# → java.base,java.sql,java.net.http

# Verbose: show all class-level dependencies
jdeps -verbose app.jar

# Show which JDK internal APIs are used
jdeps --jdk-internals app.jar

# Dependency dot graph (render with Graphviz)
jdeps -dotoutput . app.jar && dot -Tpng summary.dot -o deps.png

# Analyse a module-path application
jdeps --module-path mods/ --module com.example.app

# Check multi-release JAR
jdeps --multi-release 17 app.jar

# Include transitive dependencies
jdeps --recursive app.jar

# Filter to a specific package
jdeps -package java.sql app.jar
```

Output columns:

```
app.jar -> java.base
   com.example -> java.lang (java.base)
   com.example -> java.util (java.base)
   com.example -> java.sql  (java.sql)
```

Format: `<source package> -> <dependency package> (<module>)`

`--print-module-deps` output is a comma-separated list suitable for direct use in `jlink --add-modules`.

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jdeps reads JARs, traces class references, outputs module list for jlink">
  <rect x="10" y="10" width="660" height="190" rx="8" fill="#0d1117"/>

  <!-- Input JARs -->
  <rect x="20"  y="55" width="110" height="80" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="75"  y="78"  fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">app.jar</text>
  <text x="75"  y="92"  fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">lib-a.jar</text>
  <text x="75"  y="106" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">lib-b.jar</text>

  <line x1="130" y1="95" x2="165" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#de1)"/>

  <!-- jdeps -->
  <rect x="165" y="73" width="110" height="44" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="220" y="95"  fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">jdeps</text>
  <text x="220" y="110" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">static analysis</text>

  <line x1="275" y1="95" x2="310" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#de2)"/>

  <!-- Outputs -->
  <rect x="310" y="28"  width="340" height="36" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480"  y="44"  fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">--print-module-deps: java.base,java.sql</text>
  <text x="480"  y="57"  fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">→ feed directly to jlink --add-modules</text>

  <rect x="310" y="73"  width="340" height="36" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480"  y="90"  fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">verbose: package → package (module)</text>
  <text x="480"  y="104" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">com.example → java.sql (java.sql)</text>

  <rect x="310" y="118" width="340" height="36" rx="4" fill="#0d1117" stroke="#f0883e" stroke-width="1.5"/>
  <text x="480"  y="135" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">--jdk-internals: WARNING! sun.* usage</text>
  <text x="480"  y="149" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">breaks in --illegal-access=deny (Java 16+)</text>

  <rect x="310" y="163" width="340" height="28" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="480"  y="180" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">-dotoutput: Graphviz graph of dependencies</text>

  <defs>
    <marker id="de1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#8b949e" stroke-width="1.5"/></marker>
    <marker id="de2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
  </defs>
</svg>

`jdeps` reads JARs, traces all class references to JDK modules, and outputs: module list (for `jlink`), verbose package graph, or JDK internal API warnings.

## 5. Runnable example

Scenario: compile a class that uses various JDK modules, then use `jdeps` programmatically to discover its dependencies.

### Level 1 — Basic

```java
// JdepsBasic.java
import java.nio.file.*;
import java.util.*;

public class JdepsBasic {
    public static void main(String[] args) throws Exception {
        // Show what jdeps is and what commands to use
        System.out.println("=== jdeps dependency analyzer ===\n");

        System.out.println("Common jdeps commands:");
        System.out.printf("  %-55s  %s%n", "jdeps --print-module-deps app.jar", "module list for jlink");
        System.out.printf("  %-55s  %s%n", "jdeps -verbose:package app.jar", "package-level deps");
        System.out.printf("  %-55s  %s%n", "jdeps --jdk-internals app.jar", "internal API usage");
        System.out.printf("  %-55s  %s%n", "jdeps --generate-module-info . lib.jar", "draft module-info.java");
        System.out.printf("  %-55s  %s%n", "jdeps --dotoutput graphs/ app.jar", "Graphviz .dot output");

        // Check if jdeps is available
        Path jdeps = findTool("jdeps");
        System.out.println("\njdeps found: " + (jdeps != null ? jdeps : "not found (JRE-only?)"));

        // Show this JVM's module system
        System.out.println("\nModules in current boot layer: "
            + java.lang.ModuleLayer.boot().modules().size());
        System.out.println("Sample modules:");
        java.lang.ModuleLayer.boot().modules().stream()
            .map(Module::getName)
            .filter(n -> n.startsWith("java.") || n.startsWith("jdk."))
            .sorted()
            .limit(10)
            .forEach(m -> System.out.println("  " + m));
        System.out.println("  ...");
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java JdepsBasic.java`

`jdeps` is in `<JAVA_HOME>/bin/` alongside `javac` and `javap`. It requires a JDK install.

### Level 2 — Intermediate

Same jdeps demo extended to compile a class with known module dependencies and run `jdeps --print-module-deps` on it.

```java
// JdepsScan.java
import javax.tools.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class JdepsScan {

    // Source that uses multiple JDK modules
    static final String SOURCE =
        "import java.net.http.*;\n" +        // java.net.http module
        "import java.sql.*;\n" +              // java.sql module
        "import java.util.logging.*;\n" +     // java.logging module
        "import java.util.*;\n" +             // java.base
        "public class MultiModule {\n" +
        "    static Connection connect(String url) throws Exception {\n" +
        "        return DriverManager.getConnection(url);\n" +  // java.sql
        "    }\n" +
        "    static void log(String msg) {\n" +
        "        Logger.getLogger(\"demo\").info(msg);\n" +       // java.logging
        "    }\n" +
        "    static HttpClient http() {\n" +
        "        return HttpClient.newHttpClient();\n" +          // java.net.http
        "    }\n" +
        "}\n";

    public static void main(String[] args) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) { System.err.println("JDK required"); return; }

        Path tmpDir = Files.createTempDirectory("jdeps-scan");
        Path src = tmpDir.resolve("MultiModule.java");
        Files.writeString(src, SOURCE);
        new ProcessBuilder("javac", src.toString(), "-d", tmpDir.toString())
            .redirectErrorStream(true).start().waitFor();

        Path classFile = tmpDir.resolve("MultiModule.class");
        System.out.println("Compiled: " + Files.exists(classFile));

        // Run jdeps --print-module-deps
        Path jdeps = findJdeps();
        if (jdeps == null) { System.err.println("jdeps not found"); return; }

        System.out.println("\n[ jdeps --print-module-deps ]");
        runJdeps(jdeps, "--print-module-deps", classFile.toString());

        System.out.println("\n[ jdeps -verbose:package ]");
        runJdeps(jdeps, "-verbose:package", classFile.toString());

        Files.delete(classFile); Files.delete(src); Files.delete(tmpDir);
    }

    static void runJdeps(Path jdeps, String flag, String target) throws Exception {
        Process p = new ProcessBuilder(jdeps.toString(), flag, target)
            .redirectErrorStream(true).start();
        System.out.println(new String(p.getInputStream().readAllBytes()).strip());
        p.waitFor();
    }

    static Path findJdeps() {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/jdeps");
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java JdepsScan.java`

`--print-module-deps` output should include `java.base,java.logging,java.net.http,java.sql`. Feed this directly to `jlink --add-modules`.

### Level 3 — Advanced

Same scenario grown to run `jdeps --jdk-internals` and detect use of JDK-internal APIs that will break under strong encapsulation.

```java
// JdepsInternals.java
import javax.tools.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.*;

public class JdepsInternals {

    // Source intentionally using JDK-internal APIs (common in older libraries)
    static final String SOURCE_WITH_INTERNALS =
        "import sun.misc.BASE64Encoder;\n" +     // internal (replaced by java.util.Base64)
        "import sun.reflect.ReflectionFactory;\n" + // internal (deep JDK internals)
        "public class OldCode {\n" +
        "    public void demo() {\n" +
        "        // These work in Java 8 but emit warnings in Java 11+\n" +
        "        // and fail in Java 17+ with --illegal-access=deny\n" +
        "        System.out.println(\"using legacy APIs\");\n" +
        "    }\n" +
        "}\n";

    static final String SOURCE_CLEAN =
        "import java.util.Base64;\n" +       // public API since Java 8
        "import java.util.*;\n" +
        "import java.nio.charset.StandardCharsets;\n" +
        "public class CleanCode {\n" +
        "    public String encode(byte[] data) {\n" +
        "        return Base64.getEncoder().encodeToString(data);\n" +
        "    }\n" +
        "    public List<String> filter(List<String> items, String prefix) {\n" +
        "        return items.stream().filter(s -> s.startsWith(prefix)).toList();\n" +
        "    }\n" +
        "}\n";

    public static void main(String[] args) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) { System.err.println("JDK required"); return; }

        Path tmpDir = Files.createTempDirectory("jdeps-internals");
        Path jdeps = findJdeps();
        if (jdeps == null) { System.err.println("jdeps not found"); return; }

        System.out.println("=== jdeps --jdk-internals demo ===\n");

        // Compile the clean code (should report no internals)
        Path cleanSrc = tmpDir.resolve("CleanCode.java");
        Files.writeString(cleanSrc, SOURCE_CLEAN);
        Path classDir = Files.createDirectories(tmpDir.resolve("classes"));
        int rc = runCompiler(compiler, cleanSrc, classDir);
        if (rc == 0) {
            System.out.println("[ CleanCode.class — jdeps --print-module-deps ]");
            runJdeps(jdeps, "--print-module-deps", classDir.resolve("CleanCode.class").toString());

            System.out.println("\n[ CleanCode.class — jdeps --jdk-internals ]");
            String internals = runJdepsCapture(jdeps, "--jdk-internals",
                classDir.resolve("CleanCode.class").toString());
            if (internals.contains("Warning")) {
                System.out.println(internals);
            } else {
                System.out.println("  No JDK internal APIs detected. ✓");
            }
        }

        // Attempt to compile the old code (may fail on newer JDKs)
        System.out.println("\n[ Attempting to compile OldCode.java (uses sun.misc.*) ]");
        Path oldSrc = tmpDir.resolve("OldCode.java");
        Files.writeString(oldSrc, SOURCE_WITH_INTERNALS);
        int oldRc = runCompilerCapture(compiler, oldSrc, classDir);
        if (oldRc != 0) {
            System.out.println("  Compilation FAILED — sun.misc.BASE64Encoder removed in Java 11+");
            System.out.println("  Use java.util.Base64 instead (available since Java 8)");
        } else {
            System.out.println("  Compiled (older JDK) — running --jdk-internals:");
            runJdeps(jdeps, "--jdk-internals", classDir.resolve("OldCode.class").toString());
        }

        // Migration guidance table
        System.out.println("\n[ Common internal API migrations ]");
        Object[][] migrations = {
            {"sun.misc.BASE64Encoder",      "java.util.Base64 (Java 8+)"},
            {"sun.misc.Unsafe",             "java.lang.invoke.VarHandle (Java 9+)"},
            {"sun.reflect.ReflectionFactory","Use standard reflection or MethodHandles"},
            {"com.sun.tools.javac.*",       "javax.tools.JavaCompiler API"},
        };
        System.out.printf("  %-40s  %s%n", "Internal API", "Public Replacement");
        System.out.println("  " + "-".repeat(75));
        for (var m : migrations)
            System.out.printf("  %-40s  %s%n", m[0], m[1]);

        Files.walk(tmpDir).sorted(Comparator.reverseOrder()).forEach(p -> p.toFile().delete());
    }

    static int runCompiler(JavaCompiler c, Path src, Path out) throws Exception {
        return c.run(null, null, OutputStream.nullOutputStream(),
            "--source", "17", "-d", out.toString(), src.toString());
    }

    static int runCompilerCapture(JavaCompiler c, Path src, Path out) throws Exception {
        return c.run(null, null, null, "-d", out.toString(), src.toString());
    }

    static void runJdeps(Path jdeps, String flag, String target) throws Exception {
        Process p = new ProcessBuilder(jdeps.toString(), flag, target)
            .redirectErrorStream(true).start();
        System.out.println("  " + new String(p.getInputStream().readAllBytes()).strip());
        p.waitFor();
    }

    static String runJdepsCapture(Path jdeps, String flag, String target) throws Exception {
        Process p = new ProcessBuilder(jdeps.toString(), flag, target)
            .redirectErrorStream(true).start();
        p.waitFor();
        return new String(p.getInputStream().readAllBytes());
    }

    static Path findJdeps() {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/jdeps");
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java JdepsInternals.java`

`--jdk-internals` lists each internal API usage with a suggested replacement. This is the first step in migrating legacy code to work with Java 17+.

## 6. Walkthrough

Execution in `JdepsInternals.main`:

1. **Clean code compile** — `CleanCode.java` uses only public APIs (`java.util.Base64`, `java.util.List`, `java.util.stream`). `jdeps --print-module-deps` returns `java.base` — a single module. `jdeps --jdk-internals` returns no warnings.

2. **Old code compile** — `OldCode.java` imports `sun.misc.BASE64Encoder`. On JDK 11+, this class no longer exists — compilation fails. On JDK 8/9/10, it compiled but `jdeps --jdk-internals` would report it.

3. **`runCompilerCapture` with `-d out`** — `compiler.run(null, null, null, ...)` suppresses output (null = stderr). Returns exit code; 0 = success, non-zero = failure.

4. **`--jdk-internals` output format**:
   ```
   OldCode.class -> JDK internal API sun.misc.BASE64Encoder (jdk.unsupported)
      OldCode -> sun.misc.BASE64Encoder          jdk.unsupported
   JDK internal APIs are unsupported and private to JDK implementation ...
   ```
   The last column shows which JDK module contains the internal API — `jdk.unsupported` for `sun.misc.*`, `jdk.compiler` for `com.sun.tools.javac.*`.

5. **Migration table** — `sun.misc.Unsafe` is used internally by many high-performance libraries (Netty, Kryo, Disruptor). `VarHandle` (Java 9+) is the supported replacement for atomic memory operations.

## 7. Gotchas & takeaways

> **`jdeps --print-module-deps` does not detect dynamically-loaded classes** — `Class.forName("com.example.Plugin")` is not analysed statically. Include all code paths in your analysis, or run with `-verbose` to check for gaps.

> **`jdeps` reports split packages as errors in module mode.** A split package is when the same package name appears in two different JARs/modules — forbidden in the module system. `jdeps` will print `Error: split package: com.example [lib-a.jar, lib-b.jar]` — resolve by relocating one package or using shading.

- `jdeps --print-module-deps app.jar` → comma-separated module list for `jlink --add-modules`.
- `jdeps --jdk-internals app.jar` → identifies `sun.*` / `com.sun.*` usage that breaks in Java 17+.
- `jdeps -verbose:package app.jar` → full package-to-package dependency graph.
- `jdeps --generate-module-info . lib.jar` → draft `module-info.java` for modularising a legacy JAR.
- `-dotoutput graphs/` → Graphviz `.dot` files for visualising dependency graphs.
