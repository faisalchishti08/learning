---
card: java
gi: 46
slug: setting-path-for-java-javac
title: Setting PATH for java/javac
---

## 1. What it is

**`PATH`** is the shell environment variable that lists directories the shell searches when you type a command. Adding the JDK's `bin/` directory to `PATH` makes `java`, `javac`, `jshell`, and all other JDK tools callable by name from any directory.

```bash
export PATH=$JAVA_HOME/bin:$PATH
```

Without this, typing `java` fails with `command not found` even if the JDK is installed — the shell just doesn't know where to look for it.

## 2. Why & when

You need to set `PATH` to include the JDK when:
- `java -version` or `javac -version` returns `command not found`.
- You install a new JDK but typing `java` still invokes the old version (the old entry is earlier in `PATH`).
- Scripts that call `java` or `javac` fail even though the JDK is installed.
- You install via a tarball/zip and there's no installer to update `PATH` automatically.

Package managers like Homebrew (`brew install temurin@21`) often update `PATH` automatically via symlinks in `/usr/local/bin` or `/opt/homebrew/bin`. Manual installs (downloading a `.tar.gz` from adoptium.net) require you to set `PATH` yourself.

## 3. Core concept

```bash
# PATH is a colon-separated list of directories (semicolon on Windows)
# The shell searches them LEFT TO RIGHT and runs the first match.

echo $PATH
# → /usr/local/bin:/usr/bin:/usr/sbin:/bin:/sbin

# Add JDK bin/ at the FRONT (so it takes priority over OS /usr/bin/java)
export PATH=$JAVA_HOME/bin:$PATH

# Verify: which java should now show the JDK path
which java
# → /Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home/bin/java

# --- macOS (Zsh default since Catalina) ---
# Add to ~/.zshrc:
export JAVA_HOME=$(/usr/libexec/java_home -v 21)
export PATH=$JAVA_HOME/bin:$PATH

# --- macOS / Linux (Bash) ---
# Add to ~/.bash_profile (login shells) or ~/.bashrc (interactive shells):
export JAVA_HOME=/usr/lib/jvm/temurin-21-amd64
export PATH=$JAVA_HOME/bin:$PATH

# --- Linux system-wide (affects all users) ---
# /etc/environment (no export, just key=value):
JAVA_HOME=/usr/lib/jvm/temurin-21
PATH=/usr/lib/jvm/temurin-21/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Or create /etc/profile.d/java.sh (sourced by all login shells):
echo 'export JAVA_HOME=/usr/lib/jvm/temurin-21' | sudo tee /etc/profile.d/java.sh
echo 'export PATH=$JAVA_HOME/bin:$PATH'          | sudo tee -a /etc/profile.d/java.sh

# --- Windows (GUI) ---
# System Properties → Advanced → Environment Variables
# User variables: PATH → Edit → New → C:\Program Files\Eclipse Adoptium\jdk-21...\bin

# --- Windows (PowerShell, persistent) ---
$old = [Environment]::GetEnvironmentVariable("PATH","User")
[Environment]::SetEnvironmentVariable("PATH", "C:\Program Files\Eclipse Adoptium\jdk-21.0.2.13-hotspot\bin;$old", "User")
```

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PATH variable lists directories left-to-right; shell finds java in the first directory that contains it">
  <rect x="8" y="8" width="684" height="184" rx="8" fill="#0d1117"/>

  <!-- PATH variable representation -->
  <text x="30" y="34" fill="#8b949e" font-size="10" font-family="monospace">PATH = </text>

  <!-- Directory entries in PATH -->
  <rect x="105" y="18" width="165" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="187" y="38" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">$JAVA_HOME/bin</text>

  <text x="272" y="36" fill="#8b949e" font-size="12" font-family="monospace">:</text>

  <rect x="283" y="18" width="115" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="340" y="38" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">/usr/local/bin</text>

  <text x="400" y="36" fill="#8b949e" font-size="12" font-family="monospace">:</text>

  <rect x="410" y="18" width="95" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="458" y="38" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">/usr/bin</text>

  <text x="507" y="36" fill="#8b949e" font-size="12" font-family="monospace">:</text>

  <rect x="518" y="18" width="65" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="550" y="38" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">/bin</text>

  <text x="585" y="36" fill="#8b949e" font-size="12" font-family="monospace">:...</text>

  <!-- Shell searches left to right -->
  <text x="30" y="72" fill="#8b949e" font-size="9" font-family="sans-serif">Shell searches left-to-right when you type  java:</text>

  <!-- Search steps -->
  <rect x="105" y="83" width="165" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="187" y="102" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">$JAVA_HOME/bin/java</text>
  <text x="187" y="115" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">✓ FOUND — runs this one</text>
  <text x="187" y="127" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">stops searching here</text>

  <rect x="283" y="83" width="115" height="50" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1" opacity="0.5"/>
  <text x="340" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">skipped</text>

  <rect x="410" y="83" width="95" height="50" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1" opacity="0.5"/>
  <text x="458" y="106" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">/usr/bin/java</text>
  <text x="458" y="119" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(old version)</text>
  <text x="458" y="130" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">skipped</text>

  <!-- Result -->
  <rect x="50" y="155" width="590" height="30" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="345" y="175" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">java -version  →  openjdk version "21.0.2"  (from $JAVA_HOME/bin)</text>

  <defs>
    <marker id="path1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
  </defs>
</svg>

`PATH` entries are searched left-to-right. Putting `$JAVA_HOME/bin` at the front ensures the desired JDK is found before any OS-default `/usr/bin/java`.

## 5. Runnable example

Scenario: a developer on a team switches between Java 17 and Java 21 projects. Detect the `PATH` configuration, identify which `java` would be found, and simulate what happens when `PATH` has the wrong order.

### Level 1 — Basic

```java
// PathCheck.java — inspect PATH and find which java would be used
import java.nio.file.*;

public class PathCheck {
    public static void main(String[] args) throws Exception {
        System.out.println("=== PATH / java detection ===\n");

        // Current JVM
        System.out.println("Running JVM:");
        System.out.println("  java.version  = " + System.getProperty("java.version"));
        System.out.println("  java.home     = " + System.getProperty("java.home"));

        // Check JAVA_HOME
        String javaHome = System.getenv("JAVA_HOME");
        System.out.println("\nJAVA_HOME = " + (javaHome != null ? javaHome : "(not set)"));

        // Inspect PATH
        String path = System.getenv("PATH");
        System.out.println("\nPATH entries:");
        if (path != null) {
            String[] dirs = path.split(File.pathSeparator);
            for (int i = 0; i < dirs.length; i++) {
                Path javaExe = Path.of(dirs[i]).resolve("java");
                Path javaExeWin = Path.of(dirs[i]).resolve("java.exe");
                boolean hasJava = Files.exists(javaExe) || Files.exists(javaExeWin);
                System.out.printf("  [%2d] %-60s %s%n", i,
                    dirs[i], hasJava ? "<-- java found here" : "");
            }
        }

        System.out.println("\n[ which java would the shell pick? ]");
        System.out.println("  The FIRST entry in PATH that contains 'java' wins.");
        System.out.println("  To change it: add $JAVA_HOME/bin before any other java.");
    }
}
```

**How to run:** `java PathCheck.java`

The output shows each `PATH` directory and marks which ones contain `java`. The first match is what the shell would run. If your JDK's `bin/` appears at position `[5]` and an older Java appears at `[1]`, you'd run the wrong version — this program makes that visible.

### Level 2 — Intermediate

Same scenario: simulate what `which java` does programmatically — walk `PATH` and find the first executable `java` — then compare its version to what the current JVM knows about itself.

```java
// PathResolveJava.java — simulate 'which java' and compare versions
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;

public class PathResolveJava {
    public static void main(String[] args) throws Exception {
        System.out.println("=== Simulating 'which java' ===\n");

        String path = System.getenv("PATH");
        if (path == null) { System.out.println("PATH not set"); return; }

        String currentHome = System.getProperty("java.home");
        String currentVersion = System.getProperty("java.version");

        // Find all java executables in PATH (ordered)
        List<Path> javaExes = new ArrayList<>();
        for (String dir : path.split(File.pathSeparator)) {
            Path p = Path.of(dir).resolve("java");
            Path pw = Path.of(dir).resolve("java.exe");
            if (Files.isExecutable(p))  javaExes.add(p);
            else if (Files.isExecutable(pw)) javaExes.add(pw);
        }

        if (javaExes.isEmpty()) {
            System.out.println("ERROR: 'java' not found in PATH.");
            System.out.println("  Add to PATH: export PATH=$JAVA_HOME/bin:$PATH");
            return;
        }

        System.out.printf("Found %d java executable(s) in PATH:%n%n", javaExes.size());

        for (int i = 0; i < javaExes.size(); i++) {
            Path exe = javaExes.get(i);
            // Resolve symlinks to find real path
            Path real = exe.toRealPath();

            // Run -version to get exact version
            Process p = new ProcessBuilder(exe.toString(), "-version")
                .redirectErrorStream(true).start();
            String vout = new String(p.getInputStream().readAllBytes()).strip();
            p.waitFor();

            Matcher m = Pattern.compile("version \"([^\"]+)\"").matcher(vout);
            String version = m.find() ? m.group(1) : "?";

            String label = i == 0 ? " ← SHELL PICKS THIS ONE" : " (shadowed by entry above)";
            System.out.printf("[%d] %s%n    real path: %s%n    version: %s%s%n%n",
                i, exe, real, version, label);
        }

        // Check alignment with current JVM
        System.out.println("Current JVM: " + currentVersion + " at " + currentHome);
        Path shellJava = javaExes.get(0).toRealPath();
        boolean aligned = shellJava.toString().contains(currentHome.replaceAll("/$", ""));
        System.out.println(aligned
            ? "Aligned: shell 'java' matches running JVM."
            : "MISMATCH: shell 'java' differs from running JVM.\n" +
              "  Fix: export PATH=" + currentHome + "/bin:$PATH");
    }
}
```

**How to run:** `java PathResolveJava.java`

Walks `PATH` entries in order, checks each for an executable `java`, runs `java -version` on each, and identifies which one the shell would pick. If the shell picks Java 17 but the running JVM is Java 21, the output shows the mismatch and the fix.

### Level 3 — Advanced

Same scenario grown to generate a `set-java.sh` script that correctly sets both `JAVA_HOME` and `PATH` for any installed JDK found on the machine — the kind of helper a team would put in a project's `scripts/` directory.

```java
// PathSetupGenerator.java — detect JDKs and generate a set-java.sh helper script
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;
import java.util.stream.*;

public class PathSetupGenerator {

    record JdkInfo(String version, int major, Path home) {}

    public static void main(String[] args) throws Exception {
        System.out.println("=== Generating set-java.sh ===\n");

        // Discover JDKs in standard locations
        List<Path> roots = new ArrayList<>();
        String os = System.getProperty("os.name").toLowerCase();
        if (os.contains("mac")) {
            roots.add(Path.of("/Library/Java/JavaVirtualMachines"));
            roots.add(Path.of(System.getProperty("user.home"), ".sdkman/candidates/java"));
        } else if (os.contains("linux")) {
            roots.addAll(List.of(
                Path.of("/usr/lib/jvm"),
                Path.of(System.getProperty("user.home"), ".sdkman/candidates/java")
            ));
        }

        List<JdkInfo> jdks = new ArrayList<>();

        for (Path root : roots) {
            if (!Files.isDirectory(root)) continue;
            try (Stream<Path> dirs = Files.list(root)) {
                dirs.filter(Files::isDirectory).forEach(dir -> {
                    Path home = dir;
                    if (os.contains("mac")) {
                        Path macHome = dir.resolve("Contents/Home");
                        if (Files.isDirectory(macHome)) home = macHome;
                    }
                    Path javaExe = home.resolve("bin/java");
                    if (!Files.exists(javaExe)) return;
                    try {
                        Process p = new ProcessBuilder(javaExe.toString(), "-version")
                            .redirectErrorStream(true).start();
                        String out = new String(p.getInputStream().readAllBytes());
                        p.waitFor();
                        Matcher m = Pattern.compile("version \"(\\d+)\\.?([0-9.]*)\"").matcher(out);
                        if (m.find()) {
                            String version = m.group(1).equals("1") ?
                                "1." + m.group(2) : m.group(1) + "." + m.group(2);
                            int major = Integer.parseInt(m.group(1).equals("1") ?
                                m.group(2).split("\\.")[0] : m.group(1));
                            jdks.add(new JdkInfo(version, major, home));
                        }
                    } catch (Exception ignored) {}
                });
            }
        }

        // Always include current JVM
        String curVersion = System.getProperty("java.version");
        int curMajor = Runtime.version().feature();
        Path curHome = Path.of(System.getProperty("java.home"));
        if (jdks.stream().noneMatch(j -> j.home().equals(curHome)))
            jdks.add(new JdkInfo(curVersion, curMajor, curHome));

        jdks.sort(Comparator.comparingInt(JdkInfo::major).reversed());

        // Generate set-java.sh
        StringBuilder sb = new StringBuilder();
        sb.append("#!/bin/bash\n# Generated by PathSetupGenerator\n");
        sb.append("# Usage: source set-java.sh <major>   e.g.  source set-java.sh 21\n\n");
        sb.append("REQUESTED=${1:-21}\n\n");
        sb.append("case \"$REQUESTED\" in\n");
        for (JdkInfo j : jdks) {
            sb.append("  ").append(j.major()).append(")\n");
            sb.append("    export JAVA_HOME=\"").append(j.home()).append("\"\n");
            sb.append("    export PATH=\"$JAVA_HOME/bin:$PATH\"\n");
            sb.append("    echo \"Switched to Java ").append(j.major()).append(" (").append(j.version()).append(")\"\n");
            sb.append("    ;;\n");
        }
        sb.append("  *)\n    echo \"Unknown Java version: $REQUESTED. Available: ");
        sb.append(jdks.stream().map(j -> String.valueOf(j.major()))
            .collect(Collectors.joining(", ")));
        sb.append("\"\n    ;;\nesac\n");

        Path scriptFile = Path.of("set-java.sh");
        Files.writeString(scriptFile, sb.toString());
        scriptFile.toFile().setExecutable(true);

        System.out.println("Generated: " + scriptFile.toAbsolutePath());
        System.out.println("\nDetected JDKs:");
        for (JdkInfo j : jdks)
            System.out.printf("  Java %-5d (%s) at %s%n", j.major(), j.version(), j.home());

        System.out.println("\nUsage:");
        System.out.println("  source ./set-java.sh 21   # switch to Java 21");
        System.out.println("  source ./set-java.sh 17   # switch to Java 17");
        System.out.println();
        System.out.println("Script preview:");
        System.out.println("  " + sb.toString().replace("\n", "\n  ").substring(0, Math.min(500, sb.length())));

        // Cleanup generated file for demo
        Files.deleteIfExists(scriptFile);
        System.out.println("(script deleted for demo — remove deleteIfExists to keep it)");
    }
}
```

**How to run:** `java PathSetupGenerator.java`

Scans the machine for installed JDKs, generates a `set-java.sh` script with a `case` statement for each found version, and prints usage instructions. `source ./set-java.sh 21` sets `JAVA_HOME` and prepends `$JAVA_HOME/bin` to `PATH` for that shell session — a pattern useful in projects that need different Java versions for different build targets.

## 6. Walkthrough

Execution trace in `PathResolveJava.main`:

**Split PATH.** `System.getenv("PATH")` returns the raw `PATH` string (`/usr/local/bin:/usr/bin:...`). `split(File.pathSeparator)` splits on `:` (Unix) or `;` (Windows) to get individual directory strings.

**Find `java` executables.** For each directory, `Path.of(dir).resolve("java")` constructs the candidate path. `Files.isExecutable(p)` checks both existence and execute permission. On macOS, `/usr/bin/java` is a shim that triggers Java install prompts — it counts as executable but reports a strange version.

**Symlink resolution.** `exe.toRealPath()` follows all symlinks to the actual file. `brew install temurin@21` creates a symlink `/usr/local/bin/java → /opt/homebrew/Cellar/...`. `toRealPath()` shows the real JDK location so you can see which Homebrew formula it came from.

**`java -version` subprocess.** Note: Java writes its version to **stderr**, not stdout. `redirectErrorStream(true)` merges stderr into stdout so we can read it. The output format is:
```
openjdk version "21.0.2" 2024-01-16
OpenJDK Runtime Environment Temurin-21.0.2+13 (build 21.0.2+13)
```

**Alignment check.** The running JVM's `java.home` is compared to the real path of the first `java` in `PATH`. If they don't match, the developer typed `java` but is actually running a different JDK than their tools are configured for — a common source of confusion.

**`set-java.sh` generation.** The `case` statement approach works with any POSIX shell. `source ./set-java.sh 21` (or `. ./set-java.sh 21`) runs the script in the current shell, so the `export` commands affect the current session's environment. Running without `source` (just `./set-java.sh 21`) runs in a subshell and the parent shell sees no change.

## 7. Gotchas & takeaways

> **New terminal tabs don't pick up `export PATH=...` unless it's in your shell profile.** Running `export PATH=$JAVA_HOME/bin:$PATH` in a terminal only affects that session. To persist it, add it to `~/.zshrc` (Zsh on macOS), `~/.bashrc` (Bash on Linux), or `~/.bash_profile` (Bash on macOS). Then `source ~/.zshrc` or open a new tab.

> **`PATH` order is critical when two JDK versions are installed.** `$JAVA_HOME/bin:$PATH` (new version first) → correct. `$PATH:$JAVA_HOME/bin` (appended last) → the old `/usr/bin/java` wins. Always prepend, never append.

- `which java` (Unix) / `where java` (Windows) — shows which `java` the shell would use.
- `java -version` — shows the version of the java that was found on `PATH`.
- `source ~/.zshrc` or `exec $SHELL` — reload profile after editing.
- On macOS, Homebrew puts symlinks in `/opt/homebrew/bin` (M1/M2) or `/usr/local/bin` (Intel). Verify with `brew info temurin@21`.
- SDKMAN manages `PATH` and `JAVA_HOME` automatically — use it on developer machines to avoid manual management.
