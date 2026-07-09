---
card: java
gi: 672
slug: jpackage-incubator
title: jpackage (incubator)
---

## 1. What it is

**`jpackage`**, introduced as an **incubator tool** (JEP 343) in **Java 14**, is a command-line tool that packages a Java application into a **platform-native installable format** — an `.msi` or `.exe` on Windows, a `.pkg` or `.dmg` on macOS, and a `.deb` or `.rpm` on Linux. The output is a self-contained application image that bundles your application's JAR(s) together with a **custom, minimal JRE** (built using `jlink`, itself introduced in Java 9) — end users don't need Java installed separately at all; they just install your app the same way they'd install any other native application, with a proper OS-level icon, entry in the applications menu/Start menu, and uninstaller. This directly replaced the deprecated-and-removed `javapackager` tool from the old JavaFX/Java EE-adjacent tooling. Being an **incubator tool** meant it was available as `jpackage` under `$JAVA_HOME/bin` but wasn't yet a fully finalized, guaranteed-stable command — it stabilized as a standard tool in Java 16.

## 2. Why & when

Distributing a Java application to end users has always had an awkward middle step: your program is a `.jar`, but most non-technical users don't want to install a JRE separately and run `java -jar MyApp.jar` from a terminal — they want to download an installer, double-click it, and get an app icon. Before `jpackage`, achieving this meant using third-party tools (Install4j, Launch4j, native OS packaging scripts) or the retired `javapackager`, none of which were part of a standard, first-party JDK toolchain. `jpackage` closes this gap directly in the JDK: point it at your application's JAR and main class, and it produces a proper native installer bundling everything needed to run, including a custom-trimmed JRE via `jlink` so end users have zero external Java dependency. Reach for `jpackage` whenever you're distributing a desktop Java application (JavaFX, Swing, or even a headless CLI tool) to end users who expect a normal, native installation experience rather than a raw JAR and a "make sure you have Java installed" instruction.

## 3. Core concept

```bash
# Basic usage: package a JAR with a main class into a native installer
jpackage --name MyApp \
         --input target/ \
         --main-jar myapp.jar \
         --main-class com.example.Main \
         --type app-image   # or msi/exe/pkg/dmg/deb/rpm depending on platform

# The result bundles: your JAR(s) + a custom JRE (built via jlink) +
# a native launcher + platform packaging metadata — one self-contained unit.
```

`--type app-image` produces a runnable application directory (useful for testing before building a full installer); `--type` values like `msi`, `exe`, `pkg`, `dmg`, `deb`, `rpm` produce an actual installable package, with the available types depending on which OS you run `jpackage` on (you can't build a `.msi` on macOS, for instance — cross-platform packaging isn't supported; you package on the target OS).

## 4. Diagram

<svg viewBox="0 0 620 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jpackage combines an application JAR and a custom jlink-built JRE into one native installer per platform">
  <rect x="10" y="20" width="140" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="45" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">myapp.jar</text>
  <text x="80" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">your application</text>

  <rect x="10" y="95" width="140" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="120" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">custom JRE</text>
  <text x="80" y="137" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">built via jlink</text>

  <line x1="150" y1="50" x2="230" y2="90" stroke="#6db33f" stroke-width="2" marker-end="url(#jp1)"/>
  <line x1="150" y1="125" x2="230" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#jp2)"/>

  <rect x="240" y="55" width="130" height="70" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="305" y="80" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">jpackage</text>
  <text x="305" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">combines both</text>

  <line x1="370" y1="90" x2="420" y2="90" stroke="#f85149" stroke-width="2" marker-end="url(#jp3)"/>

  <rect x="430" y="20" width="180" height="140" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="520" y="45" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Native installer</text>
  <text x="520" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">.msi / .exe (Windows)</text>
  <text x="520" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">.pkg / .dmg (macOS)</text>
  <text x="520" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">.deb / .rpm (Linux)</text>
  <text x="520" y="135" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">No separate JRE needed</text>
  <text x="520" y="148" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">for the end user.</text>

  <defs>
    <marker id="jp1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="jp2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="jp3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
</svg>

`jpackage` fuses your application and a trimmed-down JRE into a single, platform-native, self-contained distributable.

## 5. Runnable example

Scenario: preparing a small command-line Java application for native packaging — first writing and building the application as a plain runnable JAR, then packaging it into a self-contained application image with `jpackage`, then adding proper metadata (name, version, vendor, icon references) for a production-quality installer build.

### Level 1 — Basic

```java
// File: GreeterApp.java
public class GreeterApp {
    public static void main(String[] args) {
        String name = args.length > 0 ? args[0] : "World";
        System.out.println("Hello, " + name + "! This app was packaged with jpackage.");
    }
}
```

**How to build a runnable JAR (the traditional distribution unit, before packaging):**
```
javac GreeterApp.java
jar --create --file greeter.jar --main-class GreeterApp GreeterApp.class
java -jar greeter.jar Ada
```

Expected output:
```
Hello, Ada! This app was packaged with jpackage.
```

### Level 2 — Intermediate

**How to package that JAR into a native application image** (a runnable, self-contained directory — good for testing before building a full installer):
```
mkdir input
cp greeter.jar input/
jpackage --name Greeter \
         --input input/ \
         --main-jar greeter.jar \
         --main-class GreeterApp \
         --type app-image
```

Expected result: a new `Greeter/` directory appears (on Linux/macOS) or `Greeter\` (Windows) containing a native launcher executable and a bundled, trimmed JRE. Running the launcher directly:
```
./Greeter/bin/Greeter Ada   # Linux
./Greeter.app/Contents/MacOS/Greeter Ada   # macOS
Greeter\Greeter.exe Ada     # Windows
```
produces the same output as before:
```
Hello, Ada! This app was packaged with jpackage.
```

No JDK/JRE needs to be installed on the machine running this launcher — the `Greeter/` directory contains its own private, `jlink`-built Java runtime alongside the application.

### Level 3 — Advanced

**How to build a full installer with production metadata**, rather than just an application image:
```
jpackage --name Greeter \
         --input input/ \
         --main-jar greeter.jar \
         --main-class GreeterApp \
         --type deb \
         --app-version 1.0.0 \
         --vendor "Example Corp" \
         --description "A friendly greeting CLI, distributed as a native package" \
         --linux-shortcut \
         --linux-menu-group "Utilities"
```

(Substitute `--type msi` with `--win-shortcut --win-menu` on Windows, or `--type pkg` with `--mac-package-name Greeter` on macOS — the packaging type and platform-specific flags must match the OS you run `jpackage` on.)

Expected result: a proper installable package, e.g. `greeter_1.0.0-1_amd64.deb` on Linux, which — when installed via the OS package manager (`sudo dpkg -i greeter_1.0.0-1_amd64.deb`) — registers `Greeter` in the system's application menu under "Utilities", with version `1.0.0` and vendor metadata visible in the package manager, and provides a proper uninstall path (`sudo dpkg -r greeter`) — the complete native-application lifecycle a Java-only JAR distribution never offered.

## 6. Walkthrough

1. The build starts with plain Java tooling you already know: `javac GreeterApp.java` compiles the source, and `jar --create ... GreeterApp.class` bundles the compiled class into `greeter.jar` with a manifest declaring `GreeterApp` as the main class — this is the ordinary, JVM-dependent distribution artifact.
2. `jpackage --input input/ --main-jar greeter.jar --main-class GreeterApp --type app-image` reads the JAR from the `input/` directory. Internally, `jpackage` performs roughly three steps: it determines which JDK modules the application actually needs (using `jdeps`-style analysis or a default full-JRE fallback), invokes `jlink` to build a custom, minimal Java runtime containing just those modules, and generates a small **native launcher executable** for the current platform that, when run, starts that bundled JRE and invokes `GreeterApp.main` with whatever command-line arguments were passed to the launcher.
3. The result is a self-contained `Greeter/` directory: a native binary launcher, the bundled JRE's files, and the application JAR — everything needed to run, with no dependency on any JRE/JDK already being installed on the target machine.
4. Running `./Greeter/bin/Greeter Ada` executes the native launcher, which starts the bundled JVM internally and calls `GreeterApp.main(new String[]{"Ada"})` — from `GreeterApp`'s own code's perspective, this is indistinguishable from being run via `java -jar greeter.jar Ada`; `args[0]` is `"Ada"`, so `name` is set to `"Ada"`, and the same `System.out.println` line executes and prints the same greeting.
5. For the production installer build (Level 3), `jpackage` performs the same bundling process, but instead of stopping at a raw application-image directory, it invokes the platform's native packaging tooling (`dpkg-deb` on Debian/Ubuntu for `--type deb`, similarly `rpmbuild`, `msitools`/WiX for `.msi`, or macOS's `pkgbuild`/`hdiutil` for `.pkg`/`.dmg`) to wrap that application image into a proper OS-level installable package, embedding the `--app-version`, `--vendor`, and `--description` metadata into the package's own metadata fields.
6. When an end user installs `greeter_1.0.0-1_amd64.deb` via their system's package manager, the OS handles file placement, desktop-menu registration (thanks to `--linux-shortcut --linux-menu-group "Utilities"`), and dependency bookkeeping exactly as it would for any other native Debian package — the fact that the underlying application is written in Java is entirely invisible to that installation experience.

```
GreeterApp.java ──javac──► GreeterApp.class ──jar──► greeter.jar
                                                          │
                                              jpackage (+ jlink internally)
                                                          │
                                    Greeter/ (app-image: launcher + custom JRE + jar)
                                                          │
                                          jpackage --type deb (+ dpkg-deb)
                                                          │
                                          greeter_1.0.0-1_amd64.deb (installable)
```

## 7. Gotchas & takeaways

> As an **incubator tool** in Java 14, `jpackage`'s exact flag set and behavior were subject to change before it stabilized as a standard tool in Java 16 — scripts and build configurations written against the Java 14 incubator version should be re-verified against later JDK documentation before relying on them in a stable release pipeline, particularly around flag names, which saw some refinement.

- `jpackage` builds a **platform-native** package for the OS it's run on — you cannot cross-compile a Windows `.msi` from macOS or Linux; CI pipelines producing multi-platform installers need to run `jpackage` on each target OS.
- The bundled JRE is built via `jlink`, meaning it only includes the JDK modules your application actually needs — the resulting package is typically much smaller than bundling a full standard JRE.
- `--type app-image` is useful for local testing (a runnable directory, no installer packaging step) before committing to building a full platform installer with `--type msi`/`deb`/`pkg`/etc.
- End users of a `jpackage`-built installer need **no separate Java installation** — this directly targets the "my users don't want to install Java just to run my app" distribution problem.
- This tool replaced the deprecated-and-removed `javapackager`, giving the JDK a first-party, standard (as of Java 16) native packaging story it had lacked since `javapackager`'s removal.
