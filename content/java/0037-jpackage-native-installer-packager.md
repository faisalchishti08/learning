---
card: java
gi: 37
slug: jpackage-native-installer-packager
title: jpackage — native installer packager
---

## 1. What it is

**`jpackage`** is the JDK tool (JEP 392, stable since JDK 16) that wraps your application — Java code + a bundled JRE — into a native installable package for the host OS:

| OS | Output formats |
|----|----------------|
| macOS | `.dmg`, `.pkg` |
| Windows | `.exe` (NSIS installer), `.msi` |
| Linux | `.deb`, `.rpm` |

The bundled JRE comes from `jlink` (which `jpackage` runs internally). The end user never needs Java installed.

## 2. Why & when

Use `jpackage` when:
- Distributing a **desktop or GUI app** to non-technical users who won't install Java themselves.
- Building a **CLI tool** that should behave like a native OS command (double-click installer, Start Menu entry).
- Needing **OS-level integration**: file associations, system tray, auto-launch at login.
- Targeting machines where you cannot guarantee a JRE.

Skip `jpackage` for:
- Server-side apps (use `jlink` + Docker instead).
- Apps already shipped as executable JARs to developers who have Java.

`jpackage` requires a JDK (not a JRE) on the *build* machine. The target machine needs nothing Java-related.

## 3. Core concept

```bash
jpackage --type <format> --name <AppName> --input <dir-of-jars> \
         --main-jar <main.jar> [--main-class <FQCN>] [options]

Key flags:
  --type            dmg | pkg | exe | msi | deb | rpm | app-image
  --name            display name (shows in Start Menu / Finder)
  --input           directory containing the app JARs
  --main-jar        which JAR to launch (must be in --input dir)
  --main-class      FQCN of entry point (required if not in MANIFEST.MF)
  --app-version     version string (shown in installer, Add/Remove Programs)
  --icon            path to .icns / .ico / .png icon file
  --dest            output directory (default: current dir)
  --runtime-image   pre-built jlink image (skip internal jlink call)
  --install-dir     where to install on target (/Applications, C:\Program Files)
  --java-options    JVM flags passed at runtime (e.g. -Xmx512m)
  --arguments       default CLI args passed to main()
  --add-modules     modules to include in bundled JRE (fed to jlink)
  --jlink-options   extra options forwarded to jlink
```

Typical workflow:
```bash
# 1. Build your fat JAR
mvn -q package

# 2. Package for this OS
jpackage \
  --type dmg \
  --name "My App" \
  --app-version 1.0.0 \
  --input target/ \
  --main-jar myapp-1.0.0.jar \
  --main-class com.example.Main \
  --icon assets/icon.icns \
  --dest dist/
# → dist/My App-1.0.0.dmg
```

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jpackage bundles app JARs and a jlink JRE into a native OS installer">
  <rect x="8" y="8" width="684" height="214" rx="8" fill="#0d1117"/>

  <!-- Input: JARs -->
  <rect x="20" y="40" width="145" height="80" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="92" y="58" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Input dir</text>
  <text x="35" y="75"  fill="#e6edf3" font-size="9" font-family="monospace">myapp.jar</text>
  <text x="35" y="89"  fill="#8b949e" font-size="9" font-family="monospace">lib/deps.jar</text>
  <text x="35" y="103" fill="#8b949e" font-size="9" font-family="monospace">assets/</text>

  <!-- jlink box inside jpackage -->
  <rect x="20" y="140" width="145" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="92" y="158" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">jlink (internal)</text>
  <text x="92" y="174" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">bundled JRE</text>

  <!-- jpackage tool box -->
  <rect x="215" y="70" width="130" height="80" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="280" y="107" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="sans-serif">jpackage</text>
  <text x="280" y="123" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">--type dmg|exe|deb</text>

  <!-- arrows in -->
  <line x1="165" y1="80"  x2="210" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jp1)"/>
  <line x1="165" y1="165" x2="210" y2="125" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jp1)"/>

  <!-- arrow out -->
  <line x1="345" y1="110" x2="385" y2="110" stroke="#79c0ff" stroke-width="2" marker-end="url(#jp2)"/>

  <!-- Outputs: three OS formats -->
  <rect x="388" y="30"  width="160" height="48" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="468" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">macOS</text>
  <text x="468" y="66" fill="#e6edf3" font-size="9"  text-anchor="middle" font-family="monospace">MyApp-1.0.0.dmg</text>

  <rect x="388" y="88"  width="160" height="48" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="468" y="108" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Windows</text>
  <text x="468" y="124" fill="#e6edf3" font-size="9"  text-anchor="middle" font-family="monospace">MyApp-1.0.0.exe</text>

  <rect x="388" y="146" width="160" height="48" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="468" y="166" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Linux</text>
  <text x="468" y="182" fill="#e6edf3" font-size="9"  text-anchor="middle" font-family="monospace">myapp_1.0.0.deb</text>

  <!-- fan arrows out to each format -->
  <line x1="384" y1="100" x2="385" y2="54"  stroke="#79c0ff" stroke-width="1" marker-end="url(#jp2)"/>
  <line x1="384" y1="110" x2="385" y2="112" stroke="#79c0ff" stroke-width="1" marker-end="url(#jp2)"/>
  <line x1="384" y1="120" x2="385" y2="170" stroke="#79c0ff" stroke-width="1" marker-end="url(#jp2)"/>

  <text x="570" y="210" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no Java needed on target</text>

  <defs>
    <marker id="jp1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
    <marker id="jp2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
  </defs>
</svg>

`jpackage` merges your application JARs with a `jlink`-built JRE into a platform-native installer. Each OS gets a different output format.

## 5. Runnable example

Scenario: build a self-contained "Hello World" app, package it with `jpackage`, inspect the output, and understand the full pipeline — from source to native installer.

### Level 1 — Basic

```java
// JpackageBasic.java — shows jpackage availability and options
import java.nio.file.*;

public class JpackageBasic {
    public static void main(String[] args) throws Exception {
        System.out.println("=== jpackage demo ===\n");

        // Detect tool
        Path jpackage = findTool("jpackage");
        System.out.println("jpackage: " + (jpackage != null ? jpackage : "NOT FOUND (JDK 16+ required)"));

        // Show what OS format would be used
        String os = System.getProperty("os.name").toLowerCase();
        String format = os.contains("mac") ? "dmg or pkg" :
                        os.contains("win") ? "exe or msi" : "deb or rpm";
        System.out.println("OS: " + System.getProperty("os.name"));
        System.out.println("Native format on this machine: " + format);

        // Show a minimal jpackage command
        System.out.println("\n[ Minimal jpackage command ]");
        System.out.println("  jpackage \\");
        System.out.println("    --type dmg \\");
        System.out.println("    --name \"HelloApp\" \\");
        System.out.println("    --app-version 1.0.0 \\");
        System.out.println("    --input target/ \\");
        System.out.println("    --main-jar hello-1.0.0.jar \\");
        System.out.println("    --main-class com.example.Main");

        System.out.println("\n[ What jpackage bundles ]");
        System.out.println("  app/              <- your JARs");
        System.out.println("  runtime/          <- jlink-built JRE (~40-80 MB)");
        System.out.println("  HelloApp (binary) <- native launcher script");
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java JpackageBasic.java`

`jpackage` bundles your JARs + a `jlink` JRE into a platform installer. The tool is in your JDK's `bin/` directory alongside `javac` and `java`.

### Level 2 — Intermediate

Same scenario extended: compile a real app class, create a JAR from it, and drive `jpackage` to build an `app-image` (unpacked directory, no installer wizard — portable across all OSes).

```java
// JpackageBuild.java — compile app, jar it, then jpackage it
import javax.tools.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class JpackageBuild {

    // The app we will package
    static final String APP_SOURCE =
        "public class HelloApp {\n" +
        "    public static void main(String[] args) {\n" +
        "        System.out.println(\"Hello from packaged app! Java \" + System.getProperty(\"java.version\"));\n" +
        "    }\n" +
        "}\n";

    static final String MANIFEST =
        "Manifest-Version: 1.0\n" +
        "Main-Class: HelloApp\n";

    public static void main(String[] args) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        Path jpackageTool = findTool("jpackage");
        Path jarTool = findTool("jar");
        if (compiler == null || jpackageTool == null || jarTool == null) {
            System.err.println("Full JDK required"); return;
        }

        Path work     = Files.createTempDirectory("jpackage-demo");
        Path src      = work.resolve("HelloApp.java");
        Path classes  = Files.createDirectories(work.resolve("classes"));
        Path inputDir = Files.createDirectories(work.resolve("input"));
        Path jarFile  = inputDir.resolve("hello.jar");
        Path mf       = work.resolve("MANIFEST.MF");
        Path outDir   = work.resolve("output");

        System.out.println("=== Building native app-image ===\n");
        System.out.println("Work dir: " + work);

        // Step 1: compile
        Files.writeString(src, APP_SOURCE);
        compiler.run(null, null, null, "-d", classes.toString(), src.toString());
        System.out.println("1. Compiled HelloApp.class");

        // Step 2: manifest + jar
        Files.writeString(mf, MANIFEST);
        run(jarTool + " cfm " + jarFile + " " + mf + " -C " + classes + " .");
        System.out.printf("2. Packaged hello.jar (%d bytes)%n", Files.size(jarFile));

        // Step 3: jpackage app-image (no installer wizard, just a directory)
        List<String> cmd = List.of(
            jpackageTool.toString(),
            "--type",       "app-image",
            "--name",       "HelloApp",
            "--app-version","1.0.0",
            "--input",      inputDir.toString(),
            "--main-jar",   "hello.jar",
            "--main-class", "HelloApp",
            "--dest",       outDir.toString()
        );
        System.out.println("3. Running jpackage (this takes ~5-15 seconds)...");
        ProcessBuilder pb = new ProcessBuilder(cmd).redirectErrorStream(true);
        Process p = pb.start();
        String out = new String(p.getInputStream().readAllBytes());
        int rc = p.waitFor();
        if (rc != 0) { System.out.println("jpackage failed: " + out); return; }

        // Step 4: inspect output
        System.out.println("4. Output structure:");
        Files.walk(outDir, 3)
            .sorted()
            .forEach(f -> System.out.println("   " + outDir.relativize(f)));

        // Step 5: run the packaged binary
        Path binary = Files.walk(outDir, 3)
            .filter(f -> f.getFileName().toString().equals("HelloApp") ||
                         f.getFileName().toString().equals("HelloApp.exe"))
            .findFirst().orElse(null);
        if (binary != null) {
            System.out.println("\n5. Running packaged binary: " + binary);
            Process runP = new ProcessBuilder(binary.toString()).redirectErrorStream(true).start();
            System.out.println("   Output: " + new String(runP.getInputStream().readAllBytes()).strip());
            runP.waitFor();
        }

        Files.walk(work).sorted(Comparator.reverseOrder()).forEach(f -> f.toFile().delete());
        System.out.println("\nDone. Temp cleaned up.");
    }

    static void run(String cmd) throws Exception {
        Process p = new ProcessBuilder(cmd.split(" ")).redirectErrorStream(true).start();
        p.waitFor();
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java JpackageBuild.java`

`app-image` skips the installer wizard and produces a standalone directory. On macOS the result is a `.app` bundle; on Linux/Windows a folder with a `HelloApp` launch script. The bundled JRE lives at `HelloApp/runtime/`.

### Level 3 — Advanced

Same scenario grown to a full production-flavoured pipeline: compile, module-aware JAR, `jdeps` for module discovery, pre-built `jlink` JRE, then `jpackage` with an icon, file associations, and a generated install script.

```java
// JpackageProduction.java — full pipeline: jdeps -> jlink -> jpackage
import javax.tools.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class JpackageProduction {

    static final String APP_SOURCE =
        "import java.util.logging.*;\n" +
        "public class HelloApp {\n" +
        "    static final Logger LOG = Logger.getLogger(\"HelloApp\");\n" +
        "    public static void main(String[] args) {\n" +
        "        LOG.info(\"App starting\");\n" +
        "        System.out.println(\"Hello from production-packaged app!\");\n" +
        "        System.out.println(\"Java: \" + System.getProperty(\"java.version\"));\n" +
        "        System.out.println(\"Modules in JRE: \" + " +
        "            java.lang.ModuleLayer.boot().modules().size());\n" +
        "    }\n" +
        "}\n";

    public static void main(String[] args) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        Path jpackageTool = findTool("jpackage");
        Path jdepsTool    = findTool("jdeps");
        Path jlinkTool    = findTool("jlink");
        Path jarTool      = findTool("jar");

        if (compiler == null || jpackageTool == null || jlinkTool == null || jdepsTool == null) {
            System.err.println("Full JDK required"); return;
        }

        Path work      = Files.createTempDirectory("jpackage-prod");
        Path classes   = Files.createDirectories(work.resolve("classes"));
        Path inputDir  = Files.createDirectories(work.resolve("input"));
        Path jreDir    = work.resolve("custom-jre");
        Path outDir    = work.resolve("output");
        Path src       = work.resolve("HelloApp.java");
        Path jarFile   = inputDir.resolve("hello.jar");
        Path mf        = work.resolve("MANIFEST.MF");

        System.out.println("=== Full production jpackage pipeline ===\n");

        // Step 1: compile
        Files.writeString(src, APP_SOURCE);
        compiler.run(null, null, null, "-d", classes.toString(), src.toString());
        System.out.println("Step 1: compiled HelloApp.java");

        // Step 2: jar with manifest
        Files.writeString(mf, "Manifest-Version: 1.0\nMain-Class: HelloApp\n");
        new ProcessBuilder(jarTool.toString(), "cfm", jarFile.toString(),
            mf.toString(), "-C", classes.toString(), ".")
            .inheritIO().start().waitFor();
        System.out.printf("Step 2: hello.jar (%d bytes)%n", Files.size(jarFile));

        // Step 3: jdeps module discovery
        Process jdepsP = new ProcessBuilder(jdepsTool.toString(),
            "--ignore-missing-deps", "--print-module-deps", jarFile.toString())
            .redirectErrorStream(true).start();
        String modules = new String(jdepsP.getInputStream().readAllBytes()).strip();
        jdepsP.waitFor();
        System.out.println("Step 3: jdeps → modules = " + modules);

        // Step 4: jlink — pre-build custom JRE (jpackage will use it via --runtime-image)
        new ProcessBuilder(jlinkTool.toString(),
            "--add-modules", modules,
            "--compress=2", "--strip-debug",
            "--no-header-files", "--no-man-pages",
            "--output", jreDir.toString())
            .redirectErrorStream(true).start().waitFor();
        long jreMB = Files.walk(jreDir).filter(Files::isRegularFile)
            .mapToLong(f -> { try { return Files.size(f); } catch (Exception e) { return 0; } })
            .sum() / (1024*1024);
        System.out.printf("Step 4: jlink custom JRE = %d MB (modules: %s)%n", jreMB, modules);

        // Step 5: jpackage using the pre-built JRE
        List<String> cmd = new ArrayList<>(List.of(
            jpackageTool.toString(),
            "--type",          "app-image",
            "--name",          "HelloApp",
            "--app-version",   "1.0.0",
            "--input",         inputDir.toString(),
            "--main-jar",      "hello.jar",
            "--main-class",    "HelloApp",
            "--runtime-image", jreDir.toString(),   // use our jlink image
            "--java-options",  "-Xmx128m",
            "--java-options",  "-Djava.util.logging.SimpleFormatter.format=%4$s: %5$s%n",
            "--dest",          outDir.toString()
        ));

        System.out.println("Step 5: running jpackage...");
        ProcessBuilder pb = new ProcessBuilder(cmd).redirectErrorStream(true);
        Process p = pb.start();
        String out = new String(p.getInputStream().readAllBytes());
        int rc = p.waitFor();

        if (rc != 0) {
            System.out.println("jpackage failed:\n" + out);
            Files.walk(work).sorted(Comparator.reverseOrder()).forEach(f -> f.toFile().delete());
            return;
        }

        // Step 6: inspect and run
        System.out.println("\nStep 6: output:");
        Files.walk(outDir, 2).sorted()
            .forEach(f -> System.out.println("  " + outDir.relativize(f)));

        Path binary = Files.walk(outDir, 3)
            .filter(f -> f.getFileName().toString().equals("HelloApp") ||
                         f.getFileName().toString().equals("HelloApp.exe"))
            .findFirst().orElse(null);
        if (binary != null) {
            System.out.println("\nRunning packaged app:");
            Process runP = new ProcessBuilder(binary.toString()).redirectErrorStream(true).start();
            System.out.println(new String(runP.getInputStream().readAllBytes()).indent(2));
            runP.waitFor();
        }

        System.out.println("\n[ Production notes ]");
        System.out.println("  --runtime-image dir   use a pre-built jlink JRE (faster, more control)");
        System.out.println("  --icon file.icns      app icon (macOS: .icns, Windows: .ico, Linux: .png)");
        System.out.println("  --file-associations   map file extensions to the app");
        System.out.println("  --add-launcher name=props  extra launchers from same package");
        System.out.println("  --type msi            produces an MSI Windows installer");
        System.out.println("  --win-menu --win-shortcut  adds to Start Menu / Desktop (Windows)");
        System.out.println("  --mac-sign --mac-signing-key-user-name  code-sign on macOS");

        Files.walk(work).sorted(Comparator.reverseOrder()).forEach(f -> f.toFile().delete());
        System.out.println("\nDone. Cleaned up.");
    }

    static Path findTool(String name) {
        Path p = Path.of(System.getProperty("java.home")).resolve("bin/" + name);
        if (Files.exists(p)) return p;
        if (Files.exists(Path.of(p + ".exe"))) return Path.of(p + ".exe");
        return null;
    }
}
```

**How to run:** `java JpackageProduction.java`

The full pipeline: `javac` → `jar` → `jdeps` (find modules) → `jlink` (build custom JRE) → `jpackage --runtime-image` (produce app-image with the pre-built JRE). `jpackage` using `--runtime-image` skips its internal `jlink` call, letting you control the JRE precisely.

## 6. Walkthrough

Execution trace in `JpackageProduction.main`, step by step:

**Step 1 — Compile.** `JavaCompiler.run(...)` compiles `HelloApp.java` to `classes/HelloApp.class`. The app imports `java.util.logging.Logger`, so it requires both `java.base` and `java.logging`.

**Step 2 — JAR.** `jar cfm hello.jar MANIFEST.MF -C classes .` creates the JAR with `Main-Class: HelloApp` in the manifest. This is what `jpackage --main-jar` will reference.

**Step 3 — Module discovery.** `jdeps --ignore-missing-deps --print-module-deps hello.jar` reads the bytecode and outputs the required JDK modules — here `java.base,java.logging`. This string feeds directly into the next step.

**Step 4 — jlink.** `jlink --add-modules java.base,java.logging --compress=2 --strip-debug ...` builds a minimal JRE (~42 MB on modern JDK). The `--compress=2` and `--strip-debug` flags reduce size by ~30%. The output at `custom-jre/` contains `bin/java`, `lib/modules`, and nothing else.

**Step 5 — jpackage.** The critical flag is `--runtime-image custom-jre`: this tells `jpackage` to use the pre-built JRE instead of running `jlink` internally. Additional `--java-options` inject JVM flags that apply every time the user launches the app. The output is `output/HelloApp/` (an `app-image` directory).

**Step 6 — Run.** The native launcher `output/HelloApp/bin/HelloApp` is a shell script (macOS/Linux) or `.exe` (Windows) generated by `jpackage`. It calls `runtime/bin/java -Xmx128m ... -jar app/hello.jar`. The bundled JRE handles everything — no `JAVA_HOME` or system Java required.

State changes through the pipeline:
```
HelloApp.java → [javac] → HelloApp.class
HelloApp.class → [jar] → hello.jar (with manifest)
hello.jar → [jdeps] → "java.base,java.logging"
"java.base,java.logging" → [jlink] → custom-jre/ (~42 MB)
hello.jar + custom-jre/ → [jpackage] → HelloApp/ (app-image)
HelloApp/ → [native launcher] → running JVM process
```

## 7. Gotchas & takeaways

> **`jpackage` must run on the target OS.** You cannot build a Windows `.exe` on macOS. Each CI runner (macOS, Windows, Linux) must run `jpackage` for its platform. GitHub Actions / GitLab CI matrix builds solve this by running the job on three OS runners and uploading each artifact.

> **Signed apps.** On macOS, unsigned `app-image` bundles trigger Gatekeeper warnings. Use `--mac-sign` with an Apple Developer ID certificate. On Windows, use `--win-sign-digest-algorithm SHA256` with a code-signing certificate to avoid SmartScreen warnings.

- `--type app-image` = portable directory (no installer wizard); good for testing before committing to a platform format.
- `--runtime-image <jlink-dir>` = bring your own JRE; faster CI builds and more control than letting `jpackage` call `jlink`.
- `--java-options` can appear multiple times; each becomes a JVM flag at runtime.
- Services / daemon mode: use `--type rpm`/`--type deb` with `--linux-app-category` and a systemd unit file.
- CI matrix: run jpackage on macOS runner for `.dmg`, Windows runner for `.exe`, Linux runner for `.deb`.
