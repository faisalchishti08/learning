---
card: java
gi: 31
slug: manifest-mf-executable-jars
title: MANIFEST.MF & executable JARs
---

## 1. What it is

**`META-INF/MANIFEST.MF`** is a required text file inside every JAR. It is a key-value property file (with a specific format) that tells the JVM and tooling about the JAR's contents. The `Main-Class` entry makes a JAR *executable* — runnable with `java -jar app.jar` without specifying a class name on the command line.

MANIFEST.MF is the central metadata file for the JAR contract: it specifies entry points, classpath dependencies, module identity, signing metadata, and framework-specific properties (Spring Boot's `Start-Class`, OSGi bundle headers, etc.).

## 2. Why & when

MANIFEST.MF matters when:
- **Deploying a JAR** — `java -jar` requires `Main-Class` in the manifest; without it, `java -jar` fails with `"no main manifest attribute"`.
- **Classpath in JARs** — `Class-Path` allows a JAR to reference other JARs by relative path, enabling a self-contained distribution without specifying `-cp`.
- **Module identity** — `Automatic-Module-Name` declares the module name for a non-modular JAR placed on the module path.
- **Debugging builds** — `Built-By`, `Build-Jdk`, `Implementation-Version` add build provenance to library JARs.
- **Security** — JAR signing uses `SHA-256-Digest` entries per file in the manifest.
- **Spring Boot** — Spring Boot fat JARs add `Spring-Boot-Version`, `Start-Class` (the user's `@SpringBootApplication` class), and `Main-Class` (`JarLauncher`) to the manifest.

## 3. Core concept

MANIFEST.MF format rules:
```
Manifest-Version: 1.0\r\n
Main-Class: com.example.App\r\n
Class-Path: lib/util.jar lib/core.jar\r\n
\r\n
```

Format rules (often tripped up):
1. Each line: `Name: Value\r\n` (colon-space, CRLF or LF)
2. **File must end with a newline** — last line without it is silently truncated
3. **Line length limit: 72 bytes** — longer values wrap with a space-indented continuation
4. **No tab characters** — only space for continuation lines
5. Attribute names are case-insensitive but conventionally Title-Cased

Standard attributes:

| Attribute | Purpose |
|-----------|---------|
| `Manifest-Version` | Always `1.0` |
| `Main-Class` | Entry point for `java -jar` |
| `Class-Path` | Space-separated relative JAR paths |
| `Automatic-Module-Name` | Module name for non-modular JARs |
| `Multi-Release` | `true` if this is a multi-release JAR |
| `Created-By` | JDK version that created the JAR |
| `Implementation-Version` | Library version (visible at runtime) |
| `Sealed` | `true` to prevent package mixing |

Long `Class-Path` values wrap:
```
Class-Path: lib/a.jar lib/b.jar lib/c.jar
 lib/d.jar lib/e.jar
```
(continuation line starts with a single space)

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="MANIFEST.MF inside JAR: Main-Class enables java -jar; Class-Path resolves dependencies">
  <rect x="10" y="10" width="660" height="200" rx="8" fill="#0d1117"/>

  <!-- JAR outline -->
  <rect x="20" y="28" width="300" height="168" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="170" y="48" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">app.jar</text>

  <!-- MANIFEST.MF box -->
  <rect x="35" y="58" width="270" height="110" rx="4" fill="#0d1117" stroke="#f0883e" stroke-width="1.5"/>
  <text x="170" y="76" fill="#f0883e" font-size="10" text-anchor="middle" font-family="monospace">META-INF/MANIFEST.MF</text>
  <text x="45"  y="95"  fill="#e6edf3" font-size="9"  font-family="monospace">Manifest-Version: 1.0</text>
  <text x="45"  y="109" fill="#79c0ff" font-size="9"  font-family="monospace">Main-Class: com.example.App</text>
  <text x="45"  y="123" fill="#8b949e" font-size="9"  font-family="monospace">Class-Path: lib/core.jar</text>
  <text x="45"  y="137" fill="#8b949e" font-size="9"  font-family="monospace"> lib/util.jar</text>
  <text x="45"  y="151" fill="#8b949e" font-size="9"  font-family="monospace">Implementation-Version: 2.1.0</text>

  <!-- Arrow for java -jar -->
  <line x1="320" y1="110" x2="360" y2="110" stroke="#79c0ff" stroke-width="2" marker-end="url(#mf1)"/>
  <text x="375" y="90" fill="#79c0ff" font-size="10" font-family="sans-serif">java -jar app.jar</text>
  <rect x="360" y="100" width="270" height="28" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="495" y="118" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">JVM reads Main-Class → calls main()</text>

  <!-- Class-Path arrow -->
  <line x1="320" y1="140" x2="360" y2="140" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#mf2)"/>
  <text x="375" y="135" fill="#8b949e" font-size="9" font-family="sans-serif">Class-Path resolved</text>
  <text x="375" y="149" fill="#8b949e" font-size="9" font-family="sans-serif">relative to JAR location</text>

  <!-- line length note -->
  <text x="35" y="185" fill="#8b949e" font-size="8" font-family="sans-serif">⚠ 72-byte line limit — continuation lines start with one space</text>

  <defs>
    <marker id="mf1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
    <marker id="mf2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#8b949e" stroke-width="1.5"/></marker>
  </defs>
</svg>

`MANIFEST.MF` inside `META-INF/`: `Main-Class` enables `java -jar`; `Class-Path` adds JARs to the runtime classpath relative to the JAR's location.

## 5. Runnable example

Scenario: read, write, and inspect `MANIFEST.MF` entries programmatically — from simple attribute access to building a Spring Boot-style manifest.

### Level 1 — Basic

```java
// ManifestReader.java
import java.util.jar.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class ManifestReader {
    public static void main(String[] args) throws Exception {
        // Create a sample manifest in memory
        Manifest manifest = new Manifest();
        Attributes main = manifest.getMainAttributes();
        main.put(Attributes.Name.MANIFEST_VERSION, "1.0");
        main.put(Attributes.Name.MAIN_CLASS, "com.example.App");
        main.put(new Attributes.Name("Implementation-Version"), "2.1.0");
        main.put(new Attributes.Name("Built-By"), System.getProperty("user.name"));
        main.put(new Attributes.Name("Build-Jdk"), System.getProperty("java.version"));

        // Serialize to bytes
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        manifest.write(baos);
        String manifestText = baos.toString();

        System.out.println("=== MANIFEST.MF content ===");
        System.out.println(manifestText);

        // Parse it back
        Manifest parsed = new Manifest(new ByteArrayInputStream(baos.toByteArray()));
        System.out.println("Main-Class from parsed: "
            + parsed.getMainAttributes().getValue("Main-Class"));
        System.out.println("Built-By from parsed: "
            + parsed.getMainAttributes().getValue("Built-By"));
    }
}
```

**How to run:** `java ManifestReader.java`

`Manifest.write()` produces a properly formatted MANIFEST.MF with line continuation for long values. `Attributes.Name.MAIN_CLASS` is the pre-defined constant for `Main-Class`.

### Level 2 — Intermediate

Same manifest handling extended to read the manifest from an existing JAR on disk and extract build metadata.

```java
// JarManifestInspector.java
import java.util.jar.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class JarManifestInspector {
    public static void main(String[] args) throws Exception {
        // Find any JAR on the classpath or in java.home to inspect
        Path javaHome = Path.of(System.getProperty("java.home"));

        // Look for a JAR in the JDK installation
        List<Path> jars = new ArrayList<>();
        try (var walker = Files.walk(javaHome, 3)) {
            walker.filter(p -> p.toString().endsWith(".jar"))
                  .limit(5)
                  .forEach(jars::add);
        }

        if (jars.isEmpty()) {
            // Create a sample JAR to inspect
            Path tmp = Files.createTempFile("demo", ".jar");
            Manifest mf = new Manifest();
            mf.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
            mf.getMainAttributes().put(Attributes.Name.MAIN_CLASS, "demo.Main");
            mf.getMainAttributes().put(new Attributes.Name("Implementation-Title"), "Demo Library");
            mf.getMainAttributes().put(new Attributes.Name("Implementation-Version"), "1.2.3");
            try (JarOutputStream jos = new JarOutputStream(new FileOutputStream(tmp.toFile()), mf)) {
                jos.putNextEntry(new JarEntry("demo/Main.class"));
                jos.write(new byte[]{(byte)0xCA, (byte)0xFE, (byte)0xBA, (byte)0xBE});
                jos.closeEntry();
            }
            jars.add(tmp);
        }

        System.out.println("=== JAR Manifest Inspector ===\n");
        for (Path jar : jars) {
            System.out.println("JAR: " + jar.getFileName());
            try (JarFile jf = new JarFile(jar.toFile())) {
                Manifest mf = jf.getManifest();
                if (mf == null) { System.out.println("  (no manifest)"); continue; }
                Attributes attrs = mf.getMainAttributes();
                System.out.println("  Main-Class           : " + attrs.getValue("Main-Class"));
                System.out.println("  Implementation-Title : " + attrs.getValue("Implementation-Title"));
                System.out.println("  Implementation-Version: " + attrs.getValue("Implementation-Version"));
                System.out.println("  Created-By           : " + attrs.getValue("Created-By"));
                System.out.println("  Automatic-Module-Name: " + attrs.getValue("Automatic-Module-Name"));
            } catch (Exception e) {
                System.out.println("  Error: " + e.getMessage());
            }
            System.out.println();
        }
    }
}
```

**How to run:** `java JarManifestInspector.java`

`JarFile.getManifest()` returns the parsed `Manifest`. `Attributes.getValue(String)` is case-insensitive for standard header names.

### Level 3 — Advanced

Same scenario grown to build a complete executable JAR with a Spring Boot-style manifest structure, showing how `JarLauncher` pattern works.

```java
// ExecutableJarBuilder.java
import java.util.jar.*;
import javax.tools.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.net.*;

public class ExecutableJarBuilder {
    // Simulated app entry point (would be com.example.App in real use)
    static final String APP_SOURCE =
        "package app;\n" +
        "public class Main {\n" +
        "    public static void main(String[] args) {\n" +
        "        System.out.println(\"=== App running from executable JAR ===\");\n" +
        "        System.out.println(\"Java: \" + System.getProperty(\"java.version\"));\n" +
        "        for (int i = 0; i < args.length; i++)\n" +
        "            System.out.println(\"arg[\" + i + \"] = \" + args[i]);\n" +
        "    }\n" +
        "}\n";

    public static void main(String[] args) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) { System.err.println("JDK required"); return; }

        Path tmpDir = Files.createTempDirectory("exe-jar");

        // Compile the app class
        Path srcDir = Files.createDirectories(tmpDir.resolve("src/app"));
        Files.writeString(srcDir.resolve("Main.java"), APP_SOURCE);
        Path classDir = Files.createDirectories(tmpDir.resolve("classes"));
        compiler.run(null, null, null,
            "-d", classDir.toString(),
            srcDir.resolve("Main.java").toString());

        // Build the manifest
        Manifest mf = new Manifest();
        Attributes a = mf.getMainAttributes();
        a.put(Attributes.Name.MANIFEST_VERSION,        "1.0");
        a.put(Attributes.Name.MAIN_CLASS,              "app.Main");
        a.put(new Attributes.Name("Implementation-Title"),   "My Application");
        a.put(new Attributes.Name("Implementation-Version"), "1.0.0");
        a.put(new Attributes.Name("Built-By"),               System.getProperty("user.name"));
        a.put(new Attributes.Name("Build-Jdk"),              System.getProperty("java.version"));
        a.put(new Attributes.Name("Created-By"),             "ExecutableJarBuilder 1.0");
        // Spring Boot adds: Spring-Boot-Version, Start-Class, Spring-Boot-Classes
        a.put(new Attributes.Name("Spring-Boot-Version"),    "3.2.0 (simulated)");
        a.put(new Attributes.Name("Start-Class"),            "app.Main");

        // Create the JAR
        Path jarFile = tmpDir.resolve("app.jar");
        try (JarOutputStream jos = new JarOutputStream(new FileOutputStream(jarFile.toFile()), mf)) {
            // Add compiled classes
            addDirectory(jos, classDir, classDir);
        }

        // Show the manifest
        System.out.println("=== Built executable JAR ===");
        System.out.println("Size: " + Files.size(jarFile) + " bytes\n");
        System.out.println("MANIFEST.MF:");
        try (JarFile jf = new JarFile(jarFile.toFile())) {
            ByteArrayOutputStream buf = new ByteArrayOutputStream();
            jf.getManifest().write(buf);
            System.out.println(buf.toString().indent(2).stripTrailing());
        }

        // Run it
        System.out.println("\nRunning: java -jar app.jar foo bar");
        Process p = new ProcessBuilder(
            ProcessHandle.current().info().command().orElse("java"),
            "-jar", jarFile.toString(), "foo", "bar")
            .redirectErrorStream(true).start();
        System.out.println(new String(p.getInputStream().readAllBytes()));

        Files.walk(tmpDir).sorted(Comparator.reverseOrder()).forEach(f -> f.toFile().delete());
    }

    static void addDirectory(JarOutputStream jos, Path dir, Path base) throws IOException {
        for (Path p : Files.walk(dir).filter(f -> !Files.isDirectory(f)).toList()) {
            String entryName = base.relativize(p).toString().replace('\\', '/');
            jos.putNextEntry(new JarEntry(entryName));
            Files.copy(p, jos);
            jos.closeEntry();
        }
    }
}
```

**How to run:** `java ExecutableJarBuilder.java`

This builds a self-contained executable JAR and runs it. The Spring Boot-specific attributes (`Start-Class`, `Spring-Boot-Version`) are included to show how Spring Boot extends the standard manifest schema.

## 6. Walkthrough

Execution in `ExecutableJarBuilder.main`:

1. **Compilation** — `compiler.run(null, null, null, "-d", classDir, srcFile)` is the simplest `JavaCompiler` API: returns an exit code (0 = success). Puts `app/Main.class` in `classDir`.

2. **Manifest construction** — `mf.getMainAttributes()` returns the main section's `Attributes` map. `Attributes.Name.MAIN_CLASS` is the pre-defined constant; `new Attributes.Name("Custom-Header")` creates custom headers. `Manifest.write(OutputStream)` serialises with proper line-wrapping.

3. **`addDirectory`** — walks all files under `classDir`, converts each to a relative path (e.g., `app/Main.class`), creates a `JarEntry`, and copies the file bytes. The entry path uses `/` as separator regardless of OS.

4. **`java -jar jarFile foo bar`** — the JVM reads `Main-Class: app.Main` from the manifest, finds `app.Main` in the JAR, and calls `main(new String[]{"foo","bar"})`. No `-cp` needed because the JAR itself is the classpath.

5. **Spring Boot pattern** — Spring Boot replaces `Main-Class` with `JarLauncher` (a class that knows how to load nested JARs from `BOOT-INF/lib/`) and adds `Start-Class` pointing to your `@SpringBootApplication` class. `JarLauncher.main()` sets up the classloader, then delegates to `Start-Class.main()`. This allows Spring Boot fat JARs to contain nested JARs (avoiding the flat-class-file merging that Maven Shade does).

## 7. Gotchas & takeaways

> **`MANIFEST.MF` must end with a newline.** The last attribute line without a trailing newline is silently truncated by the `java.util.jar.Manifest` parser. If `Main-Class` is the last line and has no newline, `java -jar` fails with `"no main manifest attribute"`. Always write manifests with `Manifest.write()`, not by hand.

> **`Class-Path` in manifest is resolved relative to the JAR's location on disk** — not the working directory. `lib/util.jar` means `<dir-containing-app.jar>/lib/util.jar`. This is why fat JARs (single JAR with all dependencies) are preferred for Docker deployments over manifest `Class-Path` distributions.

- `Main-Class` in `MANIFEST.MF` → `java -jar app.jar` works.
- `Manifest` API: `new Manifest()`, `getMainAttributes().put()`, `Manifest.write(stream)`.
- Lines are max 72 bytes; continuation lines start with a space.
- File must end with a newline or the last line is silently dropped.
- Spring Boot: `Main-Class=JarLauncher`, `Start-Class=YourApp`, nested JARs in `BOOT-INF/lib/`.
