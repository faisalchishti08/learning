---
card: java
gi: 45
slug: setting-java-home
title: Setting JAVA_HOME
---

## 1. What it is

**`JAVA_HOME`** is an environment variable that points to the root directory of the JDK you want to use. It tells build tools (Maven, Gradle, Ant), application servers (Tomcat, WildFly), and many scripts *which* JDK to run — not the terminal's `PATH`.

```bash
JAVA_HOME=/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home
```

Concretely: `$JAVA_HOME/bin/java` is the actual Java launcher, and `$JAVA_HOME/bin/javac` is the compiler.

## 2. Why & when

`JAVA_HOME` matters because:
- **Build tools check it, not `PATH`.** Maven reads `$JAVA_HOME` to call `javac`. If `JAVA_HOME` points to Java 8 but `PATH` points to Java 21, Maven compiles with Java 8 silently.
- **Multiple JDKs installed.** SDKMAN, Homebrew, OS installers can all put different JDKs on the machine. `JAVA_HOME` picks one.
- **Scripts and CI.** CI jobs set `JAVA_HOME` explicitly to isolate the build from whatever the OS default is.
- **Application servers.** Tomcat's `startup.sh` checks `JAVA_HOME` to find `java` even before consulting `PATH`.

Common symptoms of a wrong `JAVA_HOME`:
- `mvn` or `gradle` fail with "Unsupported class file major version".
- IDE complains about "module not found" because it's compiling with an older JDK.
- `./startup.sh` in Tomcat fails with "JAVA_HOME not set" or uses the wrong version.

## 3. Core concept

```bash
# --- Find the correct path ---

# macOS: Homebrew Temurin
/usr/libexec/java_home -v 21       # prints the JDK home for Java 21
# → /Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home

# macOS: all installed versions
/usr/libexec/java_home -V

# Linux: follow the symlinks
readlink -f $(which java)
# → /usr/lib/jvm/temurin-21-amd64/bin/java
# → JAVA_HOME = /usr/lib/jvm/temurin-21-amd64

# SDKMAN: always
echo $JAVA_HOME   # SDKMAN sets it automatically when you run 'sdk use java'

# --- Set it temporarily (current shell session) ---
export JAVA_HOME=$(/usr/libexec/java_home -v 21)   # macOS
export JAVA_HOME=/usr/lib/jvm/temurin-21-amd64     # Linux

# --- Set it permanently ---

# macOS / Linux (Bash): add to ~/.bashrc or ~/.bash_profile
echo 'export JAVA_HOME=$(/usr/libexec/java_home -v 21)' >> ~/.bash_profile
source ~/.bash_profile

# macOS (Zsh): add to ~/.zshrc
echo 'export JAVA_HOME=$(/usr/libexec/java_home -v 21)' >> ~/.zshrc
source ~/.zshrc

# Linux: add to ~/.bashrc
echo 'export JAVA_HOME=/usr/lib/jvm/temurin-21-amd64' >> ~/.bashrc
source ~/.bashrc

# Windows (PowerShell, permanent)
[Environment]::SetEnvironmentVariable("JAVA_HOME", "C:\Program Files\Eclipse Adoptium\jdk-21.0.2.13-hotspot", "User")

# Windows (Command Prompt, session only)
set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.2.13-hotspot

# --- Verify ---
echo $JAVA_HOME
$JAVA_HOME/bin/java -version
java -version    # confirm PATH also points to the same version
```

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JAVA_HOME environment variable points build tools and scripts to the correct JDK directory">
  <rect x="8" y="8" width="684" height="184" rx="8" fill="#0d1117"/>

  <!-- JAVA_HOME box -->
  <rect x="20" y="60" width="220" height="75" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="130" y="78" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">JAVA_HOME</text>
  <text x="35" y="97"  fill="#6db33f" font-size="8" font-family="monospace">/path/to/temurin-21.jdk/</text>
  <text x="50" y="111" fill="#8b949e" font-size="8" font-family="monospace">Contents/Home</text>
  <text x="35" y="127" fill="#8b949e" font-size="7" font-family="sans-serif">set in .zshrc / .bashrc / system env</text>

  <!-- arrow to JDK dir -->
  <line x1="240" y1="97" x2="285" y2="97" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jh1)"/>

  <!-- JDK directory -->
  <rect x="288" y="30" width="175" height="140" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="375" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">JDK Directory</text>
  <text x="303" y="68"  fill="#6db33f" font-size="9" font-family="monospace">bin/java</text>
  <text x="303" y="82"  fill="#6db33f" font-size="9" font-family="monospace">bin/javac</text>
  <text x="303" y="96"  fill="#8b949e" font-size="9" font-family="monospace">bin/jshell</text>
  <text x="303" y="110" fill="#8b949e" font-size="9" font-family="monospace">bin/jlink</text>
  <text x="303" y="124" fill="#8b949e" font-size="9" font-family="monospace">lib/modules</text>
  <text x="303" y="138" fill="#8b949e" font-size="9" font-family="monospace">lib/security/cacerts</text>
  <text x="303" y="152" fill="#8b949e" font-size="9" font-family="monospace">release</text>

  <!-- Consumers -->
  <rect x="525" y="20"  width="155" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="602" y="42" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Maven / Gradle</text>

  <rect x="525" y="65"  width="155" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="602" y="87" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Tomcat / WildFly</text>

  <rect x="525" y="110" width="155" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="602" y="132" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">IntelliJ / Eclipse</text>

  <rect x="525" y="155" width="155" height="28" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="602" y="173" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">CI / shell scripts</text>

  <!-- arrows from JDK dir to consumers -->
  <line x1="463" y1="80"  x2="521" y2="37"  stroke="#6db33f" stroke-width="1" marker-end="url(#jh2)"/>
  <line x1="463" y1="90"  x2="521" y2="82"  stroke="#6db33f" stroke-width="1" marker-end="url(#jh2)"/>
  <line x1="463" y1="100" x2="521" y2="127" stroke="#6db33f" stroke-width="1" marker-end="url(#jh2)"/>
  <line x1="463" y1="110" x2="521" y2="169" stroke="#6db33f" stroke-width="1" marker-end="url(#jh2)"/>

  <defs>
    <marker id="jh1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
    <marker id="jh2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
  </defs>
</svg>

`JAVA_HOME` is the single variable that all build tools and scripts use to find the JDK. Setting it correctly in your shell profile ensures they all use the same version.

## 5. Runnable example

Scenario: a multi-module build system that checks `JAVA_HOME`, validates it points to the correct JDK version, and falls back gracefully — the same checks you'd put in a `pre-build.sh` script.

### Level 1 — Basic

```java
// JavaHomeBasic.java — check JAVA_HOME and current JDK alignment
public class JavaHomeBasic {
    public static void main(String[] args) {
        System.out.println("=== JAVA_HOME check ===\n");

        String javaHome = System.getenv("JAVA_HOME");
        String javaHomeProp = System.getProperty("java.home");

        System.out.println("JAVA_HOME env:    " + (javaHome != null ? javaHome : "(not set)"));
        System.out.println("java.home prop:   " + javaHomeProp);
        System.out.println("java.version:     " + System.getProperty("java.version"));
        System.out.println("java.vendor:      " + System.getProperty("java.vendor"));

        System.out.println();
        if (javaHome == null) {
            System.out.println("WARNING: JAVA_HOME is not set.");
            System.out.println("  Maven and Gradle may use a different JDK than this one.");
            System.out.println("  Set it with: export JAVA_HOME=" + javaHomeProp);
        } else {
            // Normalize paths for comparison (both may or may not have trailing slash)
            String homeNorm = javaHome.replaceAll("/$", "");
            String propNorm = javaHomeProp.replaceAll("/$", "");
            if (homeNorm.equals(propNorm)) {
                System.out.println("JAVA_HOME matches java.home — consistent.");
            } else {
                System.out.println("MISMATCH: JAVA_HOME and java.home differ.");
                System.out.println("  Tools using JAVA_HOME may compile with a different JDK.");
            }
        }

        System.out.println("\n[ Quick fix commands ]");
        System.out.println("  export JAVA_HOME=" + javaHomeProp + "  # temporary");
        System.out.println("  echo 'export JAVA_HOME=" + javaHomeProp + "' >> ~/.zshrc  # permanent");
    }
}
```

**How to run:** `java JavaHomeBasic.java`

`System.getenv("JAVA_HOME")` reads the environment variable; `System.getProperty("java.home")` reads what the current JVM knows about itself. If they differ, Maven and the terminal use different JDKs — a common source of "it works locally but fails in CI" bugs.

### Level 2 — Intermediate

Same scenario extended: read `JAVA_HOME`, run `$JAVA_HOME/bin/java -version` as a subprocess, parse the version, and fail fast if the version doesn't meet the minimum requirement.

```java
// JavaHomeVerify.java — validate JAVA_HOME for a build script
import java.nio.file.*;
import java.util.regex.*;

public class JavaHomeVerify {
    static final int MIN_MAJOR = 17;

    public static void main(String[] args) throws Exception {
        System.out.println("=== Build pre-check: JAVA_HOME validation ===\n");

        String javaHomeEnv = System.getenv("JAVA_HOME");
        if (javaHomeEnv == null || javaHomeEnv.isBlank()) {
            fail("JAVA_HOME is not set.\n" +
                 "  macOS:  export JAVA_HOME=$(/usr/libexec/java_home -v 21)\n" +
                 "  Linux:  export JAVA_HOME=/usr/lib/jvm/temurin-21-amd64\n" +
                 "  Windows: set JAVA_HOME=C:\\Program Files\\Eclipse Adoptium\\jdk-21...");
            return;
        }
        System.out.println("JAVA_HOME: " + javaHomeEnv);

        // Check directory exists
        Path javaHome = Path.of(javaHomeEnv);
        if (!Files.isDirectory(javaHome)) {
            fail("JAVA_HOME directory does not exist: " + javaHome);
            return;
        }

        // Find java executable
        Path javaExe = javaHome.resolve("bin/java");
        Path javaExeWin = javaHome.resolve("bin/java.exe");
        Path exe = Files.exists(javaExe) ? javaExe : (Files.exists(javaExeWin) ? javaExeWin : null);
        if (exe == null) {
            fail("$JAVA_HOME/bin/java not found — JAVA_HOME may not point to a JDK directory.");
            return;
        }

        // Run java -version
        Process p = new ProcessBuilder(exe.toString(), "-version")
            .redirectErrorStream(true).start();
        String versionOutput = new String(p.getInputStream().readAllBytes()).strip();
        p.waitFor();
        System.out.println("java -version output:\n  " + versionOutput.replace("\n", "\n  "));

        // Parse major version
        Matcher m = Pattern.compile("version \"(\\d+)").matcher(versionOutput);
        if (!m.find()) { fail("Could not parse java version from: " + versionOutput); return; }
        int major = Integer.parseInt(m.group(1));
        System.out.printf("\nMajor version: %d (minimum: %d)%n", major, MIN_MAJOR);

        if (major < MIN_MAJOR) {
            fail("JDK too old. Install JDK " + MIN_MAJOR + "+ and update JAVA_HOME.");
            return;
        }

        // Check javac exists (not a JRE-only install)
        Path javac = javaHome.resolve("bin/javac");
        Path javacWin = javaHome.resolve("bin/javac.exe");
        if (!Files.exists(javac) && !Files.exists(javacWin)) {
            fail("$JAVA_HOME/bin/javac not found — JAVA_HOME must point to a JDK, not a JRE.");
            return;
        }

        System.out.println("\nAll checks passed. JAVA_HOME is correctly configured.");
        System.out.println("  You can now run: mvn package  or  gradle build");
    }

    static void fail(String msg) {
        System.err.println("\nERROR: " + msg);
        System.exit(1);
    }
}
```

**How to run:** `java JavaHomeVerify.java`

This is the logic a build tool or CI pre-flight script would run. It validates that `JAVA_HOME` is set, the directory exists, contains a real JDK (not a JRE), and meets the minimum version. If any check fails, it prints a clear remediation message and exits with code 1.

### Level 3 — Advanced

Same scenario grown to detect `JAVA_HOME` mismatches between Maven, Gradle, and the shell — a common multi-tool environment issue — and print a reconciliation report.

```java
// JavaHomeReconcile.java — detect JDK version used by Maven/Gradle vs JAVA_HOME
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;

public class JavaHomeReconcile {

    record ToolVersion(String tool, String version, String home, boolean ok) {}

    public static void main(String[] args) throws Exception {
        System.out.println("=== JAVA_HOME reconciliation report ===\n");

        String javaHomeEnv   = System.getenv("JAVA_HOME");
        String currentVersion = System.getProperty("java.version");
        String currentHome    = System.getProperty("java.home");

        System.out.println("Shell active JVM:");
        System.out.printf("  java.home    = %s%n", currentHome);
        System.out.printf("  java.version = %s%n", currentVersion);
        System.out.printf("  JAVA_HOME    = %s%n%n", javaHomeEnv != null ? javaHomeEnv : "(not set)");

        // Query each build tool for the JDK it uses
        List<ToolVersion> results = new ArrayList<>();
        results.add(new ToolVersion("Current JVM", currentVersion, currentHome, true));

        // Maven: mvn -version prints "Java version: 21.0.2, ..."
        queryTool(results, "mvn", new String[]{"mvn", "--version"},
            "Java version: ([0-9.]+)", "java home: (.+)");

        // Gradle: gradle --version prints "JVM: 21.0.2 ..."
        queryTool(results, "gradle", new String[]{"gradle", "--version"},
            "JVM:\\s+([0-9.]+)", "Java home:\\s+(.+)");

        // Print report
        System.out.println("Build tool JDK comparison:");
        System.out.printf("  %-15s %-12s %s%n", "Tool", "Version", "Home");
        System.out.printf("  %-15s %-12s %s%n", "----", "-------", "----");
        for (ToolVersion tv : results)
            System.out.printf("  %-15s %-12s %s%n", tv.tool(), tv.version(), tv.home());

        // Check consistency
        System.out.println();
        long distinctVersions = results.stream()
            .map(tv -> tv.version().split("\\.")[0]) // compare only major version
            .distinct().count();

        if (distinctVersions > 1) {
            System.out.println("WARNING: build tools use different JDK major versions.");
            System.out.println("  This can cause subtle compilation differences and build failures.");
            System.out.println("  Fix: ensure JAVA_HOME and PATH both point to the same JDK.");
            System.out.println("       Then restart your IDE and terminal.");
        } else {
            System.out.println("All tools use the same JDK major version. Consistent.");
        }

        System.out.println("\n[ Tip: SDKMAN ensures consistency automatically ]");
        System.out.println("  sdk use java 21-tem   → sets JAVA_HOME + PATH for current shell");
        System.out.println("  sdk default java 21-tem → makes it permanent for new shells");
        System.out.println("  .sdkmanrc file → per-project JDK pinning (like .nvmrc for Node)");
    }

    static void queryTool(List<ToolVersion> results, String name, String[] cmd,
                           String versionPattern, String homePattern) {
        try {
            Process p = new ProcessBuilder(cmd)
                .environment().containsKey("PATH") ?
                new ProcessBuilder(cmd).redirectErrorStream(true) :
                new ProcessBuilder(cmd).redirectErrorStream(true);
            p = new ProcessBuilder(cmd).redirectErrorStream(true).start();
            String out = new String(p.getInputStream().readAllBytes());
            p.waitFor();
            Matcher vm = Pattern.compile(versionPattern, Pattern.MULTILINE).matcher(out);
            Matcher hm = Pattern.compile(homePattern, Pattern.MULTILINE | Pattern.CASE_INSENSITIVE).matcher(out);
            String version = vm.find() ? vm.group(1) : "not found";
            String home    = hm.find() ? hm.group(1).trim() : "(unknown)";
            results.add(new ToolVersion(name, version, home, !version.equals("not found")));
        } catch (Exception e) {
            results.add(new ToolVersion(name, "(not installed)", "", false));
        }
    }
}
```

**How to run:** `java JavaHomeReconcile.java`

Queries `mvn --version` and `gradle --version` as subprocesses and parses their JDK info. If Maven and the shell report different major versions, there's a `JAVA_HOME` / `PATH` mismatch that can silently cause build problems. The SDKMAN tip shows the modern solution: `.sdkmanrc` pins a JDK per project, just like `.nvmrc` does for Node.

## 6. Walkthrough

Execution trace in `JavaHomeReconcile.main`:

**Environment reads.** `System.getenv("JAVA_HOME")` reads the shell's `JAVA_HOME` variable. `System.getProperty("java.home")` reads what the JVM was started with — these can differ if you set `JAVA_HOME` but didn't update `PATH`, or vice versa.

**`mvn --version` subprocess.** The `ProcessBuilder` starts `mvn` as a child process. Maven's startup script (`mvn` or `mvn.cmd`) reads `JAVA_HOME` (not `PATH`) to find `java` for JVM startup, then runs `java org.apache.maven.cli.MavenCli`. The version output includes `Java version: 21.0.2, vendor: Eclipse Adoptium`. Our regex extracts `21.0.2`.

**`gradle --version` subprocess.** Gradle uses `JAVA_HOME` for compilation and execution. Its version output includes `JVM: 21.0.2 (Eclipse Adoptium 21.0.2+13)` and `Java home: /Library/Java/...`.

**Consistency check.** We extract the major version (the part before the first `.`) from each tool and count distinct values. If all tools report `21`, they're consistent. If Maven reports `17` and the shell reports `21`, that's a mismatch — Maven compiles with Java 17 features even though the developer thinks they're on Java 21.

**Root cause of mismatch.** Typically: `JAVA_HOME` was set to one JDK in `.bashrc`, but the user later installed a newer JDK and updated `PATH` without updating `JAVA_HOME`. The shell `java` command uses the new JDK (from `PATH`) but Maven uses the old one (from `JAVA_HOME`).

## 7. Gotchas & takeaways

> **`JAVA_HOME` must point to the JDK root, not `bin/`.** `JAVA_HOME=/path/to/jdk` — the directory that contains `bin/`, `lib/`, `include/`. Not `/path/to/jdk/bin/`. Build tools append `bin/java` themselves.

> **macOS `/usr/bin/java` is a stub.** On macOS, `/usr/bin/java` is a system stub that launches a dialog asking you to install Java if no JDK is present, or delegates to the system JDK. It does NOT use `JAVA_HOME`. Always set `JAVA_HOME` explicitly and use `$JAVA_HOME/bin/java` in scripts.

- `echo $JAVA_HOME` — first thing to check when a build fails.
- `/usr/libexec/java_home -v 21` — macOS utility that prints the correct path for a given JDK version.
- SDKMAN's `.sdkmanrc` in a project directory auto-switches `JAVA_HOME` when you `cd` into it.
- Maven wrapper (`mvnw`) and Gradle wrapper (`gradlew`) pin their own tool version but still use `JAVA_HOME` for the JDK.
- CI: always set `JAVA_HOME` explicitly in your pipeline YAML, do not rely on the runner's default.
