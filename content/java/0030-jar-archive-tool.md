---
card: java
gi: 30
slug: jar-archive-tool
title: jar — archive tool
---

## 1. What it is

**`jar`** is the JDK tool that creates, updates, and inspects **JAR files** (Java ARchive). A JAR is a ZIP file with a specific directory structure and a mandatory `META-INF/MANIFEST.MF` file. JARs are the standard packaging format for Java libraries, applications, and modules.

`jar` ships with the JDK (`jdk.jartool` module). The `jar` command is modelled after Unix `tar` — flags like `c` (create), `t` (table of contents), `x` (extract), `u` (update), `f` (file), `v` (verbose) map directly.

## 2. Why & when

Every Java deployment involves JARs:
- **Library JARs** — distributed to Maven Central, added to `-cp`
- **Executable JARs** — contain `Main-Class` in `MANIFEST.MF`, run with `java -jar`
- **Modular JARs** — contain `module-info.class`, usable on the module path
- **Fat JARs / Uber JARs** — all dependencies merged into one JAR (Spring Boot, Maven Shade)
- **Multi-release JARs** — contain version-specific class files (Java 9+)

You use `jar` directly when:
- Creating a library JAR to share
- Inspecting a JAR's contents without unpacking it (`jar tf app.jar`)
- Building without Maven/Gradle (learning, minimal build scripts)
- Creating a modular JAR with `module-info.class`

Build tools (Maven `jar:jar`, Gradle `jar` task) invoke `jar` internally.

## 3. Core concept

JAR file structure:
```
app.jar
├── META-INF/
│   ├── MANIFEST.MF             ← required; contains Main-Class, Class-Path, etc.
│   └── NOTICE, LICENSE, etc.
├── com/example/
│   ├── App.class
│   └── util/
│       └── Helper.class
└── (resources)
    ├── application.properties
    └── static/index.html
```

Key `jar` commands:
```bash
# Create a JAR from compiled classes
jar --create --file app.jar -C target/classes .

# Create an executable JAR (with Main-Class)
jar --create --file app.jar --main-class com.example.App -C target/classes .

# List contents
jar --list --file app.jar

# Extract
jar --extract --file app.jar

# Update (add/replace files)
jar --update --file app.jar -C new-classes .

# Inspect manifest
jar --describe-module --file app.jar   (for modular JARs)
unzip -p app.jar META-INF/MANIFEST.MF  (any JAR)

# Short-flag equivalents (tar-style)
jar cf app.jar -C target/classes .     # create
jar tf app.jar                         # list
jar xf app.jar                         # extract
jar uf app.jar NewClass.class          # update
```

`MANIFEST.MF` key entries:
```
Manifest-Version: 1.0
Main-Class: com.example.App           ← enables java -jar
Class-Path: lib/util.jar lib/core.jar ← relative JARs on classpath
Automatic-Module-Name: com.example.app ← for non-modular JARs on module path
Multi-Release: true                   ← for multi-release JARs
```

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JAR file anatomy: META-INF/MANIFEST.MF, class files, resources inside a ZIP container">
  <rect x="10" y="10" width="660" height="200" rx="8" fill="#0d1117"/>
  <text x="340" y="34" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">app.jar (ZIP container)</text>

  <!-- Outer JAR border -->
  <rect x="30" y="45" width="620" height="150" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>

  <!-- META-INF -->
  <rect x="50" y="62" width="180" height="60" rx="5" fill="#0d1117" stroke="#f0883e" stroke-width="1.5"/>
  <text x="140" y="80"  fill="#f0883e" font-size="10" text-anchor="middle" font-family="monospace">META-INF/</text>
  <text x="140" y="96"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="monospace">MANIFEST.MF</text>
  <text x="140" y="110" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">Main-Class · Class-Path</text>

  <!-- Classes -->
  <rect x="250" y="62" width="180" height="60" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="80"  fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">com/example/</text>
  <text x="340" y="96"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="monospace">App.class</text>
  <text x="340" y="110" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="monospace">util/Helper.class</text>

  <!-- Resources -->
  <rect x="450" y="62" width="180" height="60" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="80"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">resources/</text>
  <text x="540" y="96"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="monospace">config.properties</text>
  <text x="540" y="110" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="monospace">static/index.html</text>

  <!-- Bottom row: commands -->
  <text x="50"  y="148" fill="#8b949e" font-size="9" font-family="monospace">jar cf app.jar -C classes .</text>
  <text x="50"  y="163" fill="#8b949e" font-size="9" font-family="monospace">jar tf app.jar</text>
  <text x="50"  y="178" fill="#8b949e" font-size="9" font-family="monospace">java -jar app.jar</text>
  <text x="310" y="148" fill="#6db33f" font-size="9" font-family="sans-serif">ZIP compression</text>
  <text x="310" y="163" fill="#6db33f" font-size="9" font-family="sans-serif">+ MANIFEST.MF = JAR</text>
</svg>

JAR = ZIP file with `META-INF/MANIFEST.MF`. Contains class files, resources, and optional module descriptor.

## 5. Runnable example

Scenario: programmatically create a JAR, inspect its manifest, and read resources from it — the core operations any build tool performs.

### Level 1 — Basic

```java
// JarBasic.java
import java.util.jar.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class JarBasic {
    public static void main(String[] args) throws Exception {
        Path tmpDir = Files.createTempDirectory("jar-demo");
        Path jarPath = tmpDir.resolve("demo.jar");

        // Step 1: create a JAR programmatically
        Manifest manifest = new Manifest();
        manifest.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
        manifest.getMainAttributes().put(Attributes.Name.MAIN_CLASS, "com.example.Demo");

        try (JarOutputStream jos = new JarOutputStream(
                new FileOutputStream(jarPath.toFile()), manifest)) {

            // Add a stub class file: magic 0xCAFEBABE + major version 65 (Java 21)
            jos.putNextEntry(new JarEntry("com/example/Demo.class"));
            jos.write(new byte[]{(byte)0xCA,(byte)0xFE,(byte)0xBA,(byte)0xBE,0,0,0,65});
            jos.closeEntry();

            // Add a resource
            jos.putNextEntry(new JarEntry("application.properties"));
            jos.write("app.name=demo\napp.version=1.0\n".getBytes());
            jos.closeEntry();
        }

        System.out.println("Created JAR: " + jarPath);
        System.out.println("Size: " + Files.size(jarPath) + " bytes\n");

        // Step 2: read the manifest back
        try (JarFile jf = new JarFile(jarPath.toFile())) {
            Manifest mf = jf.getManifest();
            System.out.println("MANIFEST.MF contents:");
            mf.getMainAttributes().forEach((k, v) ->
                System.out.println("  " + k + ": " + v));

            // Step 3: list entries
            System.out.println("\nJAR entries:");
            jf.entries().asIterator().forEachRemaining(e ->
                System.out.println("  " + e.getName() + " (" + e.getSize() + " bytes)"));
        }

        Files.walk(tmpDir).sorted(Comparator.reverseOrder()).forEach(p -> p.toFile().delete());
    }
}
```

**How to run:** `java JarBasic.java`

`JarOutputStream` writes a JAR file. `JarFile` reads it. Both are in `java.util.jar`, part of `java.base` — no extra dependencies needed.

### Level 2 — Intermediate

Same JAR creation extended to build a real executable JAR from compiled class bytes and run it in a subprocess.

```java
// JarExecutable.java
import java.util.jar.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import javax.tools.*;

public class JarExecutable {
    static final String MAIN_SOURCE =
        "package demo;\n" +
        "public class App {\n" +
        "    public static void main(String[] args) {\n" +
        "        System.out.println(\"Hello from inside the JAR!\");\n" +
        "        System.out.println(\"Args: \" + java.util.Arrays.toString(args));\n" +
        "    }\n" +
        "}\n";

    public static void main(String[] args) throws Exception {
        Path tmpDir = Files.createTempDirectory("jar-exec");

        // Step 1: compile the App class
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) { System.err.println("JDK required"); return; }

        Path srcDir = tmpDir.resolve("src/demo");
        Files.createDirectories(srcDir);
        Path srcFile = srcDir.resolve("App.java");
        Files.writeString(srcFile, MAIN_SOURCE);

        Path classDir = tmpDir.resolve("classes");
        Files.createDirectories(classDir);

        compiler.run(null, null, null,
            "-d", classDir.toString(), srcFile.toString());

        Path classFile = classDir.resolve("demo/App.class");
        System.out.println("Compiled: " + Files.exists(classFile));

        // Step 2: create executable JAR
        Path jarFile = tmpDir.resolve("app.jar");
        Manifest mf = new Manifest();
        mf.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
        mf.getMainAttributes().put(Attributes.Name.MAIN_CLASS, "demo.App");

        try (JarOutputStream jos = new JarOutputStream(new FileOutputStream(jarFile.toFile()), mf)) {
            // Add the compiled class
            jos.putNextEntry(new JarEntry("demo/App.class"));
            Files.copy(classFile, jos);
            jos.closeEntry();
        }

        System.out.println("JAR created: " + jarFile + " (" + Files.size(jarFile) + " bytes)\n");

        // Step 3: run the JAR
        System.out.println("Running: java -jar " + jarFile);
        Process p = new ProcessBuilder(
            ProcessHandle.current().info().command().orElse("java"),
            "-jar", jarFile.toString(), "hello", "world")
            .redirectErrorStream(true)
            .start();
        System.out.println(new String(p.getInputStream().readAllBytes()));
        System.out.println("Exit code: " + p.waitFor());

        Files.walk(tmpDir).sorted(Comparator.reverseOrder()).forEach(f -> f.toFile().delete());
    }
}
```

**How to run:** `java JarExecutable.java`

`Attributes.Name.MAIN_CLASS` in the manifest enables `java -jar`. Without it, `java -jar` fails with `"no main manifest attribute"`.

### Level 3 — Advanced

Same scenario grown to read resources from inside a JAR at runtime — the pattern used by frameworks to bundle configuration, templates, and static files.

```java
// JarResourceReader.java
import java.util.jar.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.net.*;

public class JarResourceReader {
    public static void main(String[] args) throws Exception {
        Path tmpDir = Files.createTempDirectory("jar-res");

        // Step 1: create a JAR with embedded resources
        Path jarFile = tmpDir.resolve("resources.jar");
        Manifest mf = new Manifest();
        mf.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");

        try (JarOutputStream jos = new JarOutputStream(new FileOutputStream(jarFile.toFile()), mf)) {
            addText(jos, "config/app.properties", "app.name=demo\napp.port=8080\napp.debug=false\n");
            addText(jos, "templates/welcome.html", "<h1>Welcome to {{app.name}}</h1>\n");
            addText(jos, "META-INF/services/com.example.Plugin",
                "com.example.plugin.DefaultPlugin\ncom.example.plugin.LogPlugin\n");
        }

        System.out.println("Created JAR with embedded resources\n");

        // Step 2: read resources via URLClassLoader (same way ClassLoader.getResourceAsStream works)
        URLClassLoader loader = new URLClassLoader(new URL[]{ jarFile.toUri().toURL() });

        System.out.println("[ Reading resources from JAR via ClassLoader ]");
        readResource(loader, "config/app.properties");
        readResource(loader, "templates/welcome.html");
        readResource(loader, "META-INF/services/com.example.Plugin");

        // Step 3: iterate all entries
        System.out.println("\n[ All JAR entries ]");
        try (JarFile jf = new JarFile(jarFile.toFile())) {
            jf.entries().asIterator().forEachRemaining(e -> {
                if (!e.isDirectory()) {
                    System.out.printf("  %-45s %d bytes%n", e.getName(), e.getSize());
                }
            });
        }

        // Step 4: show how Class.getResourceAsStream works (delegates to classloader)
        System.out.println("\n[ Class.getResourceAsStream pattern ]");
        System.out.println("  // In a class loaded from the JAR:");
        System.out.println("  InputStream in = MyClass.class.getResourceAsStream(\"/config/app.properties\");");
        System.out.println("  // Leading '/' = absolute from classloader root");
        System.out.println("  // No leading '/' = relative to the class's package");

        loader.close();
        Files.walk(tmpDir).sorted(Comparator.reverseOrder()).forEach(p -> p.toFile().delete());
    }

    static void addText(JarOutputStream jos, String path, String content) throws IOException {
        jos.putNextEntry(new JarEntry(path));
        jos.write(content.getBytes());
        jos.closeEntry();
    }

    static void readResource(URLClassLoader loader, String path) throws IOException {
        try (InputStream in = loader.getResourceAsStream(path)) {
            if (in == null) { System.out.println(path + ": NOT FOUND"); return; }
            System.out.println("--- " + path + " ---");
            System.out.println(new String(in.readAllBytes()).stripTrailing());
            System.out.println();
        }
    }
}
```

**How to run:** `java JarResourceReader.java`

`ClassLoader.getResourceAsStream(path)` looks up resources in the classloader's JARs. Spring Boot uses this to load `application.properties`, templates, and `META-INF/spring.factories` from inside the JAR without knowing its on-disk path.

## 6. Walkthrough

Execution in `JarResourceReader.main`:

1. **JAR creation** — `JarOutputStream` wraps a `FileOutputStream`. `putNextEntry(new JarEntry(path))` starts a new ZIP entry. Writing bytes to `jos` writes the entry content. `closeEntry()` finalises the entry's checksum. The `Manifest` passed to the constructor goes into `META-INF/MANIFEST.MF` automatically.

2. **`URLClassLoader`** — given `jarFile.toUri().toURL()`, it adds the JAR to the classloader's search path. `loader.getResourceAsStream("config/app.properties")` opens the JAR, finds the entry, and returns an `InputStream` over the compressed bytes. The JVM transparently decompresses as you read.

3. **`META-INF/services/` directory** — this is the Java ServiceLoader SPI mechanism. A file named after an interface (`com.example.Plugin`) lists implementations one per line. `ServiceLoader.load(Plugin.class)` reads this file from the classpath to discover implementations. Spring Boot's `spring.factories` and `spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` follow the same pattern.

4. **Absolute vs relative resource paths** — `Class.getResourceAsStream("/config/app.properties")` (leading `/`) is equivalent to `ClassLoader.getResourceAsStream("config/app.properties")`. Without the `/`, the path is relative to the class's package: `com.example.Foo.class.getResourceAsStream("bar.properties")` looks for `com/example/bar.properties`.

## 7. Gotchas & takeaways

> **`"no main manifest attribute"` error from `java -jar`** means `Main-Class` is missing or has trailing whitespace in `MANIFEST.MF`. The MANIFEST.MF format requires each line to end with `\r\n` or `\n` and the file must end with a newline — a common hand-editing mistake causes silent truncation.

> **Fat JARs merge `META-INF/services/` files from multiple dependencies.** If two JARs both provide `META-INF/services/com.example.Plugin`, a naive fat JAR (Maven Shade without transformers) keeps only one. The `ServicesResourceTransformer` in Maven Shade merges them correctly.

- `jar cf app.jar -C classes .` — create; `jar tf app.jar` — list; `jar xf app.jar` — extract.
- `Main-Class` in `MANIFEST.MF` enables `java -jar app.jar`.
- `Class.getResourceAsStream("/path/in/jar")` reads embedded resources without knowing the JAR's on-disk path.
- `META-INF/services/<interface>` files power Java's `ServiceLoader` SPI — used by JDBC drivers, codec discovery, Spring Boot auto-configuration.
- Multi-release JARs (`Multi-Release: true`) contain version-specific class overrides in `META-INF/versions/N/`.
