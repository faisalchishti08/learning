---
card: java
gi: 56
slug: classpath-cp-classpath
title: Classpath (-cp / --classpath)
---

## 1. What it is

The **classpath** is the list of locations where the JVM and `javac` search for compiled `.class` files and JAR archives. It is specified with `-cp` or `--classpath` (or the `CLASSPATH` environment variable, though that is generally avoided).

```bash
# Compile against an external JAR
javac -cp lib/gson-2.10.jar src/Main.java

# Run with multiple classpath entries (: on Unix, ; on Windows)
java -cp ".:lib/gson-2.10.jar:lib/slf4j-api-2.0.jar" com.example.Main

# Equivalent long flag
java --classpath ".:lib/gson-2.10.jar" com.example.Main
```

Before the Java Module System (JDK 9), the classpath was the sole mechanism for locating user code. It still works for all non-modular code.

## 2. Why & when

| Situation | Role of classpath |
|---|---|
| Compiling | `javac` needs compiled classes referenced by source (`import com.google.gson.Gson`) |
| Running | `java` launcher needs all class files and JARs at runtime |
| Testing | Test runner adds compiled test classes + test-framework JARs |
| Fat JARs | Single JAR on classpath containing all deps (avoids long `-cp` lists) |
| IDE / build tools | Maven/Gradle construct the classpath from `pom.xml`/`build.gradle` automatically |

Common errors that trace back to classpath problems:
- `ClassNotFoundException` — class not found at runtime.
- `NoClassDefFoundError` — class existed at compile time but missing at runtime.
- `package does not exist` — `javac` can't find referenced classes.

## 3. Core concept

```bash
# Directory separator: . = current dir; : = Unix separator; ; = Windows
# JAR = single archive containing many .class files + META-INF/MANIFEST.MF

# ---- classpath entry types ----
# 1. Directory   — JVM searches for com/example/Foo.class inside the dir
# 2. JAR file    — JVM searches inside the JAR's zip entries
# 3. Wildcard *  — expands all JARs in a directory (no recursion)

# ---- compile + run lifecycle ----
mkdir -p out lib src

# javac: all source in src/, output to out/, lib/*.jar on classpath
javac -cp "lib/*" -d out src/*.java

# java: out/ + all JARs in lib/
java -cp "out:lib/*" com.example.Main

# ---- classpath search order ----
# Given: -cp "a:b:c"
# JVM searches a first, then b, then c
# FIRST match wins — earlier entries shadow later ones

# ---- wildcard expansion ----
# -cp "lib/*"  expands to all *.jar files in lib/  (NOT sub-directories)
# Order within * expansion is unspecified — don't rely on it for conflict resolution

# ---- CLASSPATH env var (avoid in production) ----
export CLASSPATH="out:lib/gson-2.10.jar"
java com.example.Main   # picks up CLASSPATH automatically
# -cp flag on command line OVERRIDES CLASSPATH env var entirely

# ---- fat JAR (uber JAR) ----
# Maven Shade plugin merges all deps into one JAR
# Classpath becomes just: java -jar app-fat.jar
# META-INF/MANIFEST.MF: Main-Class: com.example.Main
#                        Class-Path: (empty — all bundled)

# ---- common mistakes ----
# Missing current directory: java -cp "lib/*" Main
#   → ClassNotFoundException because out/ not included
# Fix: java -cp ".:lib/*" Main    (Unix) or ".;lib\*" (Windows)

# Classpath vs module path:
# Non-modular JAR → classpath
# Modular JAR (has module-info.class) → module path (--module-path)
# Both can coexist on same command
```

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Classpath: JVM searches each entry in order; first match wins; class not found = ClassNotFoundException">
  <rect x="8" y="8" width="684" height="184" rx="8" fill="#0d1117"/>

  <!-- Title row -->
  <text x="350" y="28" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">java -cp "out:lib/gson.jar:lib/slf4j.jar" com.example.Main</text>

  <!-- Entry boxes -->
  <rect x="20" y="40" width="130" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="85" y="58" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">out/</text>
  <text x="85" y="73" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">compiled .class files</text>
  <text x="85" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">com/example/Main.class</text>

  <text x="167" y="70" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">→</text>

  <rect x="178" y="40" width="140" height="60" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="248" y="58" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">lib/gson.jar</text>
  <text x="248" y="73" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">com/google/gson/Gson.class</text>
  <text x="248" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">... 400 more classes</text>

  <text x="327" y="70" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">→</text>

  <rect x="337" y="40" width="140" height="60" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="407" y="58" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">lib/slf4j.jar</text>
  <text x="407" y="73" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">org/slf4j/Logger.class</text>
  <text x="407" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">... 80 more classes</text>

  <!-- Not found -->
  <text x="487" y="70" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">→</text>
  <rect x="497" y="40" width="185" height="60" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="590" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">class not found in any entry</text>
  <text x="590" y="76" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ClassNotFoundException</text>

  <!-- Order note -->
  <text x="350" y="130" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Search order: left → right. First match wins (earlier entries shadow later ones).</text>

  <!-- Legend row -->
  <rect x="20" y="145" width="160" height="38" rx="4" fill="#1c2430"/>
  <text x="100" y="160" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Entry types:</text>
  <text x="100" y="174" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">dir/  •  file.jar  •  dir/*</text>

  <rect x="192" y="145" width="160" height="38" rx="4" fill="#1c2430"/>
  <text x="272" y="160" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Separators:</text>
  <text x="272" y="174" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">: Unix  ;  Windows</text>

  <rect x="364" y="145" width="160" height="38" rx="4" fill="#1c2430"/>
  <text x="444" y="160" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Build tool equivalent:</text>
  <text x="444" y="174" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Maven/Gradle auto-construct</text>

  <rect x="536" y="145" width="148" height="38" rx="4" fill="#1c2430"/>
  <text x="610" y="160" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Env var (avoid):</text>
  <text x="610" y="174" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">$CLASSPATH</text>
</svg>

JVM searches classpath entries left-to-right; the first directory or JAR that contains the requested `.class` wins.

## 5. Runnable example

Scenario: build and run a multi-JAR application from scratch — compile, package into a JAR, compose a classpath, and diagnose `ClassNotFoundException` — so the classpath mechanics are visible end-to-end.

### Level 1 — Basic

```java
// ClasspathBasic.java — print the effective classpath at runtime
public class ClasspathBasic {
    public static void main(String[] args) {
        System.out.println("=== Classpath basics ===\n");

        // Get classpath from system properties
        String cp = System.getProperty("java.class.path");
        System.out.println("java.class.path = " + cp);
        System.out.println();

        // Split and print each entry
        String separator = System.getProperty("path.separator"); // : or ;
        String[] entries = cp.split(java.util.regex.Pattern.quote(separator));
        System.out.println("Entries (" + entries.length + "):");
        for (int i = 0; i < entries.length; i++) {
            System.out.printf("  [%d] %s%n", i, entries[i]);
        }

        System.out.println("\nPath separator for this OS: '" + separator + "'");
        System.out.println("  Unix: ':'  Windows: ';'");

        System.out.println("\n[ How to specify ]");
        System.out.println("  Short flag: java -cp \"out:lib/*\" com.example.Main");
        System.out.println("  Long flag:  java --classpath \"out:lib/*\" com.example.Main");
        System.out.println("  Env var:    export CLASSPATH=out:lib/* (avoid — applies globally)");

        System.out.println("\n[ Common classpath entries ]");
        System.out.println("  .          → current directory");
        System.out.println("  out/       → compiled class output directory");
        System.out.println("  lib/*.jar  → all JARs in lib/ (wildcard, no recursion)");
        System.out.println("  app.jar    → a single JAR file");
    }
}
```

**How to run:** `java ClasspathBasic.java`

Single-file source programs run with `.` as their effective classpath. In a real build, `java.class.path` would show all compiled output directories and JAR paths.

### Level 2 — Intermediate

Same order-processing scenario: compile two separate classes, package one into a JAR, run the other against it, and observe `ClassNotFoundException` when the JAR is missing.

```java
// OrderService.java — the "library" class (will be packaged into a JAR)
// OrderProcessor.java — uses OrderService; run against the JAR

// ============================================================
// File 1: OrderService.java
// ============================================================
public class OrderService {
    private final String region;

    public OrderService(String region) { this.region = region; }

    public String process(String orderId, double amount) {
        return String.format("[%s] Processed order %s for £%.2f", region, orderId, amount);
    }
}

// ============================================================
// File 2: ClasspathIntermediate.java — main entry point
// Uses OrderService on the classpath
// ============================================================
public class ClasspathIntermediate {
    // ClassLoader that shows where a class was loaded from
    static String sourceOf(Class<?> cls) {
        java.security.CodeSource cs = cls.getProtectionDomain().getCodeSource();
        return cs == null ? "<built-in>" : cs.getLocation().toString();
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Classpath intermediate demo ===\n");

        // Show classpath
        String cp = System.getProperty("java.class.path");
        System.out.println("Effective classpath:");
        String sep = System.getProperty("path.separator");
        for (String e : cp.split(java.util.regex.Pattern.quote(sep)))
            System.out.println("  " + e);

        // Show where OrderService was loaded from
        System.out.println("\nOrderService loaded from: " + sourceOf(OrderService.class));

        // Use OrderService normally
        OrderService svc = new OrderService("EU");
        System.out.println(svc.process("ORD-001", 299.99));
        System.out.println(svc.process("ORD-002", 50.00));

        // Demonstrate ClassNotFoundException in a controlled way
        System.out.println("\n[ Attempting to load unknown class ]");
        try {
            Class.forName("com.acme.NonExistentService");
        } catch (ClassNotFoundException e) {
            System.out.println("ClassNotFoundException: " + e.getMessage());
            System.out.println("  → Add the JAR containing this class to -cp");
        }

        // Classpath search order demo using current class
        System.out.println("\n[ Classpath search for this class ]");
        System.out.println("ClasspathIntermediate loaded from: " + sourceOf(ClasspathIntermediate.class));

        System.out.println("\n[ Build recipe ]");
        System.out.println("  # Compile both classes to out/");
        System.out.println("  javac -d out OrderService.java ClasspathIntermediate.java");
        System.out.println("  # Package OrderService into a JAR");
        System.out.println("  cd out && jar cf ../lib/order-service.jar OrderService.class && cd ..");
        System.out.println("  # Run using the JAR on classpath (not out/)");
        System.out.println("  java -cp \"lib/order-service.jar:out\" ClasspathIntermediate");
    }
}
```

**How to run (single-file shortcut):** `java ClasspathIntermediate.java`

To see the full JAR demo: compile to `out/`, jar `OrderService.class` into `lib/order-service.jar`, then run with `-cp "lib/order-service.jar:out"`.

### Level 3 — Advanced

Same order system: inspect classpath at runtime, detect shadowing conflicts (two JARs with the same class), print all classpath entries with their type (directory vs JAR), and enumerate classes in a JAR programmatically.

```java
// ClasspathAdvanced.java — classpath inspector
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;
import java.util.jar.*;
import java.util.zip.*;

public class ClasspathAdvanced {
    public static void main(String[] args) throws Exception {
        System.out.println("=== Classpath advanced inspector ===\n");

        String cp  = System.getProperty("java.class.path");
        String sep = System.getProperty("path.separator");
        String[] entries = cp.split(java.util.regex.Pattern.quote(sep));

        // 1. Classify each entry
        System.out.println("[ Classpath entries ]");
        Map<String, Integer> typeCounts = new LinkedHashMap<>();
        typeCounts.put("dir", 0); typeCounts.put("jar", 0);
        typeCounts.put("missing", 0); typeCounts.put("other", 0);

        for (int i = 0; i < entries.length; i++) {
            String e = entries[i];
            Path p = Path.of(e);
            String kind;
            if (!Files.exists(p))           kind = "missing";
            else if (Files.isDirectory(p))  kind = "dir    ";
            else if (e.endsWith(".jar"))    kind = "jar    ";
            else                            kind = "other  ";
            System.out.printf("  [%02d] %s  %s%n", i, kind, e);
            typeCounts.merge(kind.strip(), 1, Integer::sum);
        }
        System.out.println("  Summary: " + typeCounts);

        // 2. Scan JARs for a class name to see if shadowing could occur
        String targetClass = "java/util/ArrayList.class"; // safe to scan for in bootstrap
        System.out.println("\n[ Shadow detection: scanning for '" + targetClass + "' ]");
        System.out.println("  (JDK bootstrap classes are not on classpath; this demo shows the pattern)");
        List<String> jarMatches = new ArrayList<>();
        for (String e : entries) {
            Path p = Path.of(e);
            if (!Files.exists(p) || !e.endsWith(".jar")) continue;
            try (JarFile jar = new JarFile(p.toFile())) {
                if (jar.getEntry(targetClass) != null) {
                    jarMatches.add(e);
                    System.out.println("  Found in: " + e);
                }
            } catch (IOException | ZipException ignored) {}
        }
        if (jarMatches.isEmpty())
            System.out.println("  Not found in user classpath (expected for bootstrap class).");
        if (jarMatches.size() > 1)
            System.out.println("  ⚠ SHADOWING: first entry wins → " + jarMatches.get(0));

        // 3. Create a temp JAR and list its contents programmatically
        System.out.println("\n[ Creating and inspecting a demo JAR ]");
        Path tmp = Files.createTempDirectory("cp-demo");
        Path demoJar = tmp.resolve("demo.jar");

        // Write a minimal JAR with a fake class entry
        try (JarOutputStream jos = new JarOutputStream(new FileOutputStream(demoJar.toFile()))) {
            // Manifest
            Manifest mf = new Manifest();
            mf.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
            mf.getMainAttributes().put(Attributes.Name.MAIN_CLASS, "com.example.Main");
            JarEntry manifestEntry = new JarEntry("META-INF/MANIFEST.MF");
            jos.putNextEntry(manifestEntry);
            mf.write(jos);
            jos.closeEntry();

            // Fake class entries
            String[] fakeClasses = {
                "com/example/Main.class",
                "com/example/OrderService.class",
                "com/example/internal/Helper.class"
            };
            for (String cls : fakeClasses) {
                jos.putNextEntry(new JarEntry(cls));
                jos.write(new byte[]{(byte)0xCA,(byte)0xFE,(byte)0xBA,(byte)0xBE}); // magic
                jos.closeEntry();
            }
        }

        System.out.println("JAR created: " + demoJar);
        System.out.println("Contents:");
        try (JarFile jar = new JarFile(demoJar.toFile())) {
            jar.stream()
               .sorted(Comparator.comparing(ZipEntry::getName))
               .forEach(e -> {
                   String type = e.getName().endsWith(".class") ? "class" : "meta ";
                   System.out.printf("  [%s]  %s  (%d bytes)%n", type, e.getName(), e.getSize());
               });
            System.out.println("  Main-Class: " + jar.getManifest()
                                                      .getMainAttributes()
                                                      .getValue("Main-Class"));
        }

        // Cleanup
        Files.walk(tmp).sorted(Comparator.reverseOrder()).map(Path::toFile).forEach(File::delete);
        System.out.println("Cleaned up temp dir.");

        // 4. Resolution tip
        System.out.println("\n[ ClassNotFoundException resolution checklist ]");
        System.out.println("  1. javac -verbose 2>&1 | grep 'class'   → see compile-time search");
        System.out.println("  2. java -verbose:class                   → see runtime class loading");
        System.out.println("  3. jar tf lib/mylib.jar | grep ClassName → is class actually in JAR?");
        System.out.println("  4. Check: -cp includes both 'out/' AND all lib/*.jar");
        System.out.println("  5. Shadow check: two JARs with same class? Earlier one wins.");
    }
}
```

**How to run:** `java ClasspathAdvanced.java`

`-verbose:class` on the JVM prints every class load with the source JAR or directory — the fastest way to see exactly which classpath entry won for any given class.

## 6. Walkthrough

Execution trace in `ClasspathAdvanced.main`:

**Entry classification.** Each classpath entry is tested with `Files.isDirectory()` / `e.endsWith(".jar")`. Missing entries (classpath includes a dir that doesn't exist) are flagged — they silently cause `ClassNotFoundException` in production.

**Shadow detection.** For each JAR entry, `JarFile.getEntry(targetClass)` checks if the class exists inside that archive. If two JARs contain the same class (e.g., two versions of `gson`), the JVM uses whichever appears first in `-cp`. This is the root cause of "wrong version at runtime" bugs. The fix: use a build tool (Maven/Gradle) that enforces a single version per dependency.

**JAR creation.** `JarOutputStream` writes `META-INF/MANIFEST.MF` first (required by spec), then entries. Each `.class` entry starts with the magic bytes `CAFEBABE` — the ClassLoader validates this at load time. Entries are stored as `com/example/Main.class` (forward slashes always, even on Windows).

**`Main-Class` attribute.** When running with `java -jar app.jar`, the JVM reads `META-INF/MANIFEST.MF` → `Main-Class` to find the entry point. The classpath from `-cp` is ignored when using `-jar`; only the `Class-Path` manifest attribute is used (or everything bundled in the JAR itself for fat JARs).

**`-verbose:class` output.** At runtime, `java -verbose:class -cp "out:lib/*" com.example.Main` prints a line like `[Loaded com.example.Main from file:/path/to/out/]` for every class load — definitively showing which classpath entry each class came from.

## 7. Gotchas & takeaways

> **`java -jar` ignores `-cp`.** When you launch with `java -jar app.jar`, the JVM ignores any `-cp` flag. The only classpath that applies is the `Class-Path:` entry in `META-INF/MANIFEST.MF`. This surprises developers who add `-cp extra.jar` hoping it works alongside `-jar` — it doesn't.

> **Wildcard `*` does not recurse.** `-cp "lib/*"` expands to all `.jar` files directly inside `lib/`. JARs in `lib/subdir/` are NOT included. Use `find lib -name '*.jar'` to build the classpath dynamically if you need subdirectory JARs.

- `-cp "entry1:entry2"` — specify classpath; overrides `$CLASSPATH`.
- First match wins — earlier entries shadow later ones.
- `ClassNotFoundException` at runtime → class (or its JAR) missing from `-cp`.
- `NoClassDefFoundError` → class existed at compile time but missing at runtime (usually a JAR you forgot to include on the runtime classpath).
- Maven/Gradle construct the classpath from the dependency graph — prefer them over manual `-cp` for multi-dependency projects.
- `java -verbose:class` shows exactly which entry each class was loaded from — the canonical debugging tool for classpath issues.
