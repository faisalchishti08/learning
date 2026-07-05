---
card: java
gi: 44
slug: installing-the-jdk
title: Installing the JDK
---

## 1. What it is

**Installing the JDK (Java Development Kit)** means getting `javac`, `java`, and the full suite of JDK tools (`jshell`, `jmap`, `keytool`, etc.) onto your machine and making them callable from the terminal.

A JDK installation is just a directory (e.g., `/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home/`) containing:
```
bin/      → javac, java, jshell, jlink, jmap, keytool ...
lib/      → modules, security/cacerts, ...
include/  → JNI header files
```

Installing = downloading that directory and pointing environment variables at it.

## 2. Why & when

You need a JDK (not just a JRE) when:
- **Writing Java code** — you need `javac` to compile.
- **Using JDK diagnostic tools** — `jmap`, `jstack`, `jconsole`, `jlink`.
- **Building with Maven / Gradle** — they call `javac` internally.
- **Generating Javadoc** — needs `javadoc`.

A JRE alone is enough only for *running* precompiled Java applications. All modern JDK distributions include the JRE.

**Which JDK to install:**
- **Eclipse Temurin** (formerly AdoptOpenJDK) — recommended, free, open-source, widely used.
- **Amazon Corretto** — Temurin-equivalent, AWS-optimised.
- **Oracle JDK** — free for personal use, needs a licence for commercial redistribution (JDK 17+ changed terms; check Oracle's FAQ).
- **GraalVM** — if you need native image compilation.

Use the **latest LTS**: Java 21 (2023–2028) or Java 17 (2021–2029).

## 3. Core concept

```bash
# --- macOS ---
# Option A: Homebrew (recommended)
brew install temurin@21

# Option B: SDKMAN (manages multiple JDK versions)
curl -s "https://get.sdkman.io" | bash
sdk install java 21-tem    # Temurin 21
sdk use java 21-tem

# --- Linux (Debian/Ubuntu) ---
sudo apt-get update
sudo apt-get install -y wget apt-transport-https
wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo tee /etc/apt/keyrings/adoptium.asc
echo "deb [signed-by=/etc/apt/keyrings/adoptium.asc] https://packages.adoptium.net/artifactory/deb $(awk -F= '/^VERSION_CODENAME/{print$2}' /etc/os-release) main" | sudo tee /etc/apt/sources.list.d/adoptium.list
sudo apt-get update
sudo apt-get install -y temurin-21-jdk

# --- Windows ---
# Download .msi installer from adoptium.net and run it.
# Or use winget:
winget install EclipseAdoptium.Temurin.21.JDK

# --- Verify ---
java -version
javac -version
# Expected: openjdk version "21.x.x" ...

# --- Where is it? ---
which java        # → /usr/bin/java (or via SDKMAN symlink)
java -XshowSettings:properties -version 2>&1 | grep java.home
# → java.home = /Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home
```

## 4. Diagram

<svg viewBox="0 0 700 215" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JDK installation paths: Homebrew/apt/winget download and unpack a JDK directory structure">
  <rect x="8" y="8" width="684" height="199" rx="8" fill="#0d1117"/>

  <!-- Installers -->
  <rect x="20" y="25" width="170" height="170" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="105" y="44" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Package Manager</text>
  <text x="35" y="63"  fill="#6db33f" font-size="9" font-family="monospace">brew install temurin@21</text>
  <text x="35" y="78"  fill="#6db33f" font-size="9" font-family="monospace">sdk install java 21-tem</text>
  <text x="35" y="93"  fill="#6db33f" font-size="9" font-family="monospace">apt-get install temurin-21</text>
  <text x="35" y="108" fill="#6db33f" font-size="9" font-family="monospace">winget install Temurin.21</text>
  <text x="35" y="128" fill="#8b949e" font-size="8" font-family="sans-serif">or manual .dmg / .msi</text>
  <text x="35" y="143" fill="#8b949e" font-size="8" font-family="sans-serif">from adoptium.net</text>
  <text x="35" y="163" fill="#79c0ff" font-size="8" font-family="sans-serif">↓ downloads + unpacks</text>

  <!-- arrow -->
  <line x1="190" y1="110" x2="226" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#inst1)"/>

  <!-- JDK directory -->
  <rect x="229" y="25" width="215" height="170" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="337" y="44" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">JDK Directory</text>
  <text x="245" y="62"  fill="#e6edf3" font-size="9" font-family="monospace">$JAVA_HOME/</text>
  <text x="260" y="77"  fill="#6db33f" font-size="9" font-family="monospace">bin/</text>
  <text x="275" y="91"  fill="#8b949e" font-size="8" font-family="monospace">javac  java  jshell</text>
  <text x="275" y="104" fill="#8b949e" font-size="8" font-family="monospace">jlink  jmap  keytool</text>
  <text x="260" y="119" fill="#6db33f" font-size="9" font-family="monospace">lib/</text>
  <text x="275" y="133" fill="#8b949e" font-size="8" font-family="monospace">modules  security/</text>
  <text x="260" y="148" fill="#6db33f" font-size="9" font-family="monospace">include/</text>
  <text x="275" y="162" fill="#8b949e" font-size="8" font-family="monospace">jni.h (JNI headers)</text>
  <text x="260" y="177" fill="#6db33f" font-size="9" font-family="monospace">release</text>

  <!-- PATH + JAVA_HOME -->
  <rect x="500" y="50" width="180" height="80" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="590" y="68" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Environment</text>
  <text x="515" y="86"  fill="#6db33f" font-size="8" font-family="monospace">JAVA_HOME=/path/to/jdk</text>
  <text x="515" y="100" fill="#6db33f" font-size="8" font-family="monospace">PATH=$JAVA_HOME/bin:$PATH</text>
  <text x="515" y="120" fill="#8b949e" font-size="8" font-family="sans-serif">→ java and javac</text>
  <text x="515" y="132" fill="#8b949e" font-size="8" font-family="sans-serif">   callable from anywhere</text>

  <!-- arrow -->
  <line x1="444" y1="110" x2="496" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#inst2)"/>

  <defs>
    <marker id="inst1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
    <marker id="inst2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
  </defs>
</svg>

A JDK installation is a directory tree. Package managers download and unpack it; environment variables point your shell at its `bin/` directory.

## 5. Runnable example

Scenario: detect the current JDK installation, verify required tools are present, and report what version and distribution is installed — the same checks a build script or CI job would run.

### Level 1 — Basic

```java
// JdkInstallCheck.java — detect and verify the current JDK
import java.nio.file.*;
import java.util.*;

public class JdkInstallCheck {
    public static void main(String[] args) throws Exception {
        System.out.println("=== JDK installation check ===\n");

        // Java home
        String javaHome = System.getProperty("java.home");
        System.out.println("java.home: " + javaHome);

        // Version
        System.out.println("java.version: " + System.getProperty("java.version"));
        System.out.println("java.vendor:  " + System.getProperty("java.vendor"));
        System.out.println("java.vm.name: " + System.getProperty("java.vm.name"));

        // Check key tools
        Path home = Path.of(javaHome);
        String[] tools = {"java", "javac", "jshell", "jlink", "jmap", "jstack",
                          "jcmd", "jstat", "keytool", "jar", "javadoc", "jpackage"};
        System.out.println("\nTool availability:");
        for (String tool : tools) {
            Path p = home.resolve("bin/" + tool);
            Path pe = home.resolve("bin/" + tool + ".exe");
            boolean found = Files.exists(p) || Files.exists(pe);
            System.out.printf("  %-15s %s%n", tool, found ? "✓ found" : "✗ not found");
        }

        System.out.println("\n[ Is this a JDK or JRE? ]");
        boolean hasJavac = Files.exists(home.resolve("bin/javac")) ||
                           Files.exists(home.resolve("bin/javac.exe"));
        System.out.println(hasJavac ? "This is a JDK (javac present)" : "This is a JRE only (no javac)");
    }
}
```

**How to run:** `java JdkInstallCheck.java`

`System.getProperty("java.home")` is the JDK home that executed this script. If `javac` is found in `bin/`, it's a full JDK; if not, it's a JRE-only installation that can run but not compile.

### Level 2 — Intermediate

Same scenario extended: run `java -version` and `javac -version` as child processes (the way a build script does it) and parse the version numbers to verify minimum JDK version requirements.

```java
// JdkVersionCheck.java — verify installed JDK version meets minimum requirement
import java.nio.file.*;
import java.util.regex.*;

public class JdkVersionCheck {
    static final int MIN_MAJOR = 17; // require JDK 17+

    public static void main(String[] args) throws Exception {
        System.out.println("=== JDK version check ===\n");

        Path javaHome = Path.of(System.getProperty("java.home"));
        Path java  = findExe(javaHome, "java");
        Path javac = findExe(javaHome, "javac");

        // Run java -version
        if (java != null) {
            Process p = new ProcessBuilder(java.toString(), "-version")
                .redirectErrorStream(true).start();
            String out = new String(p.getInputStream().readAllBytes()).strip();
            p.waitFor();
            System.out.println("java -version:\n  " + out.replace("\n", "\n  "));

            // Parse major version (e.g., "17.0.9", "21.0.1")
            Matcher m = Pattern.compile("version \"(\\d+)").matcher(out);
            if (m.find()) {
                int major = Integer.parseInt(m.group(1));
                System.out.printf("\nMajor version: %d (minimum required: %d) → %s%n",
                    major, MIN_MAJOR,
                    major >= MIN_MAJOR ? "OK" : "FAIL — upgrade your JDK");
            }
        }

        // Run javac -version
        if (javac != null) {
            System.out.println();
            Process p = new ProcessBuilder(javac.toString(), "-version")
                .redirectErrorStream(true).start();
            System.out.println("javac -version: " + new String(p.getInputStream().readAllBytes()).strip());
            p.waitFor();
        } else {
            System.out.println("\nWARNING: javac not found — install a full JDK, not just a JRE.");
        }

        // Show runtime version API (JDK 9+)
        Runtime.Version v = Runtime.version();
        System.out.println("\nRuntime.version(): " + v);
        System.out.println("  Feature (major): " + v.feature());
        System.out.println("  Interim:         " + v.interim());
        System.out.println("  Update:          " + v.update());
        System.out.println("  Patch:           " + v.patch());
        System.out.println("  LTS:             " + (v.feature() == 17 || v.feature() == 21 ? "yes" : "check JEP 3"));
    }

    static Path findExe(Path home, String name) {
        Path p = home.resolve("bin/" + name);
        if (Files.exists(p)) return p;
        Path pe = home.resolve("bin/" + name + ".exe");
        if (Files.exists(pe)) return pe;
        return null;
    }
}
```

**How to run:** `java JdkVersionCheck.java`

`Runtime.version()` is the programmatic API for querying JDK version (JDK 9+). `v.feature()` returns the major version number (17, 21, etc.). Use this in library code that needs to gate features by JDK version.

### Level 3 — Advanced

Same scenario grown to detect multiple installed JDKs, compare their versions, and output a report — the kind of check a multi-project developer or CI machine operator would run.

```java
// JdkInstallInventory.java — find all installed JDKs on this machine
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;
import java.util.stream.*;

public class JdkInstallInventory {

    record JdkInfo(Path home, String version, String vendor, boolean hasJavac) {}

    public static void main(String[] args) throws Exception {
        System.out.println("=== JDK installation inventory ===\n");

        List<JdkInfo> found = new ArrayList<>();

        // Discover JDK homes from common OS-specific locations
        List<Path> searchRoots = new ArrayList<>();
        String os = System.getProperty("os.name").toLowerCase();
        if (os.contains("mac")) {
            searchRoots.add(Path.of("/Library/Java/JavaVirtualMachines"));
            searchRoots.add(Path.of(System.getProperty("user.home"), "Library/Java/JavaVirtualMachines"));
            // SDKMAN
            searchRoots.add(Path.of(System.getProperty("user.home"), ".sdkman/candidates/java"));
        } else if (os.contains("linux")) {
            searchRoots.addAll(List.of(
                Path.of("/usr/lib/jvm"),
                Path.of("/usr/local/lib/jvm"),
                Path.of(System.getProperty("user.home"), ".sdkman/candidates/java")
            ));
        } else if (os.contains("windows")) {
            searchRoots.addAll(List.of(
                Path.of("C:\\Program Files\\Java"),
                Path.of("C:\\Program Files\\Eclipse Adoptium"),
                Path.of("C:\\Program Files\\Microsoft"),
                Path.of("C:\\Program Files\\Amazon Corretto")
            ));
        }

        for (Path root : searchRoots) {
            if (!Files.isDirectory(root)) continue;
            try (Stream<Path> dirs = Files.list(root)) {
                dirs.filter(Files::isDirectory).forEach(dir -> {
                    // macOS: JavaVirtualMachines/<name>.jdk/Contents/Home
                    Path home = dir;
                    if (os.contains("mac")) {
                        Path macHome = dir.resolve("Contents/Home");
                        if (Files.isDirectory(macHome)) home = macHome;
                    }
                    Path javaExe = home.resolve("bin/java");
                    Path javaExeWin = home.resolve("bin/java.exe");
                    if (!Files.exists(javaExe) && !Files.exists(javaExeWin)) return;

                    try {
                        Path exe = Files.exists(javaExe) ? javaExe : javaExeWin;
                        Process p = new ProcessBuilder(exe.toString(), "-version")
                            .redirectErrorStream(true).start();
                        String vout = new String(p.getInputStream().readAllBytes());
                        p.waitFor();

                        Matcher vm = Pattern.compile("version \"([^\"]+)\"").matcher(vout);
                        String version = vm.find() ? vm.group(1) : "unknown";
                        Matcher vendorm = Pattern.compile("^(.*?) version", Pattern.MULTILINE).matcher(vout);
                        String vendor = vendorm.find() ? vendorm.group(1).trim() : "unknown";
                        boolean hasJavac = Files.exists(home.resolve("bin/javac")) ||
                                           Files.exists(home.resolve("bin/javac.exe"));

                        found.add(new JdkInfo(home, version, vendor, hasJavac));
                    } catch (Exception ignored) {}
                });
            }
        }

        // Also include current JVM
        Path currentHome = Path.of(System.getProperty("java.home"));
        boolean alreadyFound = found.stream().anyMatch(j -> j.home().equals(currentHome));
        if (!alreadyFound) {
            found.add(new JdkInfo(currentHome, System.getProperty("java.version"),
                System.getProperty("java.vendor"), true));
        }

        if (found.isEmpty()) {
            System.out.println("No JDK installations found in standard locations.");
            System.out.println("Current JVM: " + System.getProperty("java.home"));
        } else {
            System.out.printf("Found %d JDK installation(s):%n%n", found.size());
            for (JdkInfo jdk : found) {
                System.out.printf("  Version: %-15s  JDK: %-5s  Vendor: %s%n",
                    jdk.version(), jdk.hasJavac() ? "yes" : "no", jdk.vendor());
                System.out.printf("  Home:    %s%n%n", jdk.home());
            }
        }

        System.out.println("Active JDK (java.home):");
        System.out.println("  " + System.getProperty("java.home"));
        System.out.println("  java.version = " + System.getProperty("java.version"));
    }
}
```

**How to run:** `java JdkInstallInventory.java`

Scans OS-specific JDK directories, runs `java -version` on each, and produces an inventory. Useful on developer machines that use SDKMAN or Homebrew with multiple JDK versions installed.

## 6. Walkthrough

Execution trace in `JdkInstallInventory.main`:

**Platform detection.** `System.getProperty("os.name")` returns `Mac OS X`, `Linux`, or `Windows 11`. This selects the right set of `searchRoots` — the conventional directories where JDK distributions install themselves.

**Directory scan.** For each `searchRoot`, `Files.list(root)` lists direct subdirectories. On macOS, each JDK lives under `JavaVirtualMachines/<name>.jdk/Contents/Home/`. On Linux, JDKs are directly under `/usr/lib/jvm/<name>/`. The code probes both paths.

**JDK probe.** For each candidate directory, it looks for `bin/java` (or `bin/java.exe` on Windows). If found, it runs `java -version` as a subprocess. The output (written to stderr by convention, redirected with `redirectErrorStream(true)`) looks like:
```
openjdk version "21.0.2" 2024-01-16
OpenJDK Runtime Environment Temurin-21.0.2+13 (build 21.0.2+13)
OpenJDK 64-Bit Server VM Temurin-21.0.2+13 (build 21.0.2+13, mixed mode)
```

**Regex extraction.** `Pattern.compile("version \"([^\"]+)\"")` extracts `"21.0.2"`. The vendor line is the first word before `" version"` — `"openjdk"` or `"java"`.

**JDK vs JRE.** `hasJavac` checks for `bin/javac`. A JRE-only installation has `bin/java` but not `bin/javac`. Modern JDK distributions always include both; the distinction only matters for older JRE-only installs.

**Active JDK.** The currently-running JVM's home is always in `System.getProperty("java.home")`. If it's already in `found`, de-duplicate; otherwise add it. This ensures the current JVM is always reported even if it's installed in a non-standard location.

## 7. Gotchas & takeaways

> **Multiple JDKs, wrong one active.** `java -version` in a terminal may report a different version than the JDK that your IDE or build tool uses. The one in `PATH` wins at the terminal; IDEs often use a separately configured JDK (check IntelliJ IDEA: File → Project Structure → SDK). Always verify with `java -XshowSettings:properties -version 2>&1 | grep java.home`.

> **SDKMAN / Homebrew manage symlinks, not copies.** `sdk use java 21-tem` updates `~/.sdkman/candidates/java/current` symlink and prepends it to `PATH`. Opening a new terminal tab may use a different version if `JAVA_HOME` is not set in `.zshrc` / `.bashrc`. SDKMAN's `sdk default java 21-tem` makes a version the default for all new shells.

- `java -version` — always run this first to confirm which JDK is active.
- `which javac` / `where javac` — shows which `javac` the shell finds; if `/usr/bin/javac` on macOS, it's the system stub, not a real JDK.
- SDKMAN (`sdk`) — the easiest way to manage multiple JDKs on macOS/Linux.
- `Runtime.version().feature()` — programmatic major version check (Java 9+).
- For Docker: use `FROM eclipse-temurin:21-jdk` for build stages, `FROM eclipse-temurin:21-jre` for runtime stages.
