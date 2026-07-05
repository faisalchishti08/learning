---
card: java
gi: 2
slug: write-once-run-anywhere-wora-philosophy
title: Write-once-run-anywhere (WORA) philosophy
---

## 1. What it is

**Write Once, Run Anywhere (WORA)** is the design promise Sun Microsystems made when launching Java in 1995: you compile your Java source code exactly once, and the resulting file runs unmodified on any machine that has a compatible Java Virtual Machine (JVM) — Windows, Linux, macOS, Solaris, embedded devices.

Before WORA, compiled C or C++ code was platform-specific: a binary built for Windows would not run on Linux. You needed separate builds (and sometimes separate code paths) for every target. WORA eliminated that multi-platform build tax.

## 2. Why & when

In the mid-1990s, software had to support a fragmented landscape: multiple CPU architectures (x86, SPARC, PowerPC) and multiple operating systems (Windows 3.1/95/NT, various Unix flavours, Macintosh). Maintaining separate native builds was expensive. The web was exploding, and Java applets (small programs embedded in web pages) needed to work in any browser on any OS — a native binary was simply not an option.

WORA matters today whenever:
- You ship a JAR or WAR to production servers that may differ from your laptop.
- Your team uses Windows laptops but deploys to Linux containers.
- You build a library consumed by developers on many platforms.
- You need a single artifact to pass through CI/CD and land on multiple environments.

## 3. Core concept

WORA rests on one key abstraction: the **Java Virtual Machine (JVM)**.

The compilation chain has two stages, not one:

```
Java source (.java)
       │
       ▼  javac (compiler)
Java bytecode (.class)    ← platform-neutral, portable
       │
       ▼  JVM (interpreter / JIT)
Native machine code       ← platform-specific, produced at runtime
```

**Bytecode** is not machine code for any real CPU. It is an instruction set for an imaginary machine — the JVM. Every real platform ships its own JVM implementation that knows how to translate bytecode into that platform's native instructions. Your `.class` file never changes; only the JVM changes per platform.

Analogy: a recipe (bytecode) is written in English once. A chef in Tokyo (JVM on Linux/x86), a chef in Berlin (JVM on macOS/ARM), and a chef in Lagos (JVM on Windows/x64) each read the same recipe but cook it on their own equipment. Same recipe, different kitchens.

The contract that makes WORA work:
1. All JVMs must implement the **Java Language Specification (JLS)** and the **Java Virtual Machine Specification (JVMS)** — two documents that define exactly what any compliant JVM must do.
2. Distributions are validated against the **Technology Compatibility Kit (TCK)** — a massive test suite Oracle maintains.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="WORA: one Java source compiles to bytecode, which runs on many JVMs">
  <defs>
    <marker id="aw" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="ag" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <!-- source -->
  <rect x="20" y="95" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="116" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Hello.java</text>
  <text x="85" y="133" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">source code</text>
  <!-- arrow to bytecode -->
  <line x1="150" y1="120" x2="218" y2="120" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ag)"/>
  <text x="184" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">javac</text>
  <!-- bytecode -->
  <rect x="220" y="85" width="140" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="290" y="112" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Hello.class</text>
  <text x="290" y="128" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">bytecode</text>
  <text x="290" y="143" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(platform neutral)</text>
  <!-- arrows to JVMs -->
  <line x1="360" y1="100" x2="435" y2="65"  stroke="#8b949e" stroke-width="1.5" marker-end="url(#aw)"/>
  <line x1="360" y1="120" x2="435" y2="120" stroke="#8b949e" stroke-width="1.5" marker-end="url(#aw)"/>
  <line x1="360" y1="140" x2="435" y2="175" stroke="#8b949e" stroke-width="1.5" marker-end="url(#aw)"/>
  <!-- JVM boxes -->
  <rect x="436" y="38"  width="190" height="42" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="531" y="56"  fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JVM — Windows / x64</text>
  <text x="531" y="72"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">translates bytecode → x64 native</text>

  <rect x="436" y="98"  width="190" height="42" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="531" y="116" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JVM — Linux / x64</text>
  <text x="531" y="132" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">translates bytecode → x64 native</text>

  <rect x="436" y="156" width="190" height="42" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="531" y="174" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JVM — macOS / ARM</text>
  <text x="531" y="190" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">translates bytecode → ARM native</text>
</svg>

One `.class` file, three JVMs, three native translations — WORA in action.

## 5. Runnable example

The scenario: a program that discovers its own runtime platform and proves the bytecode is identical regardless of where it runs.

### Level 1 — Basic

```java
// PlatformInfo.java
public class PlatformInfo {
    public static void main(String[] args) {
        System.out.println("OS   : " + System.getProperty("os.name"));
        System.out.println("Arch : " + System.getProperty("os.arch"));
        System.out.println("Java : " + System.getProperty("java.version"));
        System.out.println("Same bytecode, different platform!");
    }
}
```

**How to run:** `java PlatformInfo.java`

Run this on Windows and on Linux — the output will differ in `OS` and `Arch`, but the program (bytecode) is identical on both. That difference in `os.name` is WORA's point: the JVM shields your code from the OS.

### Level 2 — Intermediate

Same program extended to read its own `.class` file's magic bytes and class-file version — proving the bytecode really is the same binary across platforms.

```java
// BytecodeProof.java
import java.io.*;
import java.nio.file.*;

public class BytecodeProof {
    public static void main(String[] args) throws IOException {
        System.out.println("=== Platform ===");
        System.out.println("OS   : " + System.getProperty("os.name"));
        System.out.println("Arch : " + System.getProperty("os.arch"));

        // Find this class's .class file (only works when compiled separately,
        // but `java File.java` compiles to a temp dir — show the version via reflection instead)
        System.out.println("\n=== Bytecode version (via reflection) ===");
        // java.class.version = "major.minor" e.g. "65.0" for Java 21
        System.out.println("class version : " + System.getProperty("java.class.version"));
        int major = (int) Double.parseDouble(System.getProperty("java.class.version"));
        System.out.println("target JDK    : " + (major - 44));   // 45 = JDK 1, so major-44 = JDK version

        System.out.println("\nBytecode is platform-neutral — JVM handles the rest.");
    }
}
```

**How to run:** `java BytecodeProof.java`

`java.class.version` is the bytecode major version. `65.0` means Java 21 (`65 - 44 = 21`). This number is baked into every `.class` file and is the same regardless of which OS compiled it.

### Level 3 — Advanced

Same scenario grown to a full WORA audit: reports platform, verifies bytecode magic header from a real `.class` file, checks whether a `path.separator` difference (`:` on Unix, `;` on Windows) could silently break classpath handling, and detects endianness.

```java
// WoraAudit.java
import java.io.*;
import java.nio.file.*;
import java.nio.ByteOrder;

public class WoraAudit {
    public static void main(String[] args) throws Exception {
        System.out.println("=== WORA Audit ===\n");

        // Platform identity
        String os   = System.getProperty("os.name");
        String arch = System.getProperty("os.arch");
        String sep  = System.getProperty("path.separator");
        System.out.printf("Platform      : %s / %s%n", os, arch);
        System.out.printf("Path separator: '%s'  (%s)%n", sep,
            sep.equals(":") ? "Unix-style — colons in classpath" : "Windows-style — semicolons in classpath");
        System.out.printf("Endianness    : %s%n", ByteOrder.nativeOrder());

        // Compile this source to a temp file and read its magic bytes
        Path tmpDir = Files.createTempDirectory("wora");
        Path src = tmpDir.resolve("Probe.java");
        Files.writeString(src, "public class Probe {}");
        new ProcessBuilder("javac", src.toString())
            .redirectErrorStream(true)
            .start()
            .waitFor();
        Path cls = tmpDir.resolve("Probe.class");
        byte[] bytes = Files.readAllBytes(cls);

        // First 4 bytes of every .class file must be 0xCAFEBABE
        System.out.printf("%nMagic bytes   : %02X %02X %02X %02X  (must be CA FE BA BE)%n",
            bytes[0] & 0xFF, bytes[1] & 0xFF, bytes[2] & 0xFF, bytes[3] & 0xFF);
        int minor = ((bytes[4] & 0xFF) << 8) | (bytes[5] & 0xFF);
        int major = ((bytes[6] & 0xFF) << 8) | (bytes[7] & 0xFF);
        System.out.printf("Class version : %d.%d  (JDK %d)%n", major, minor, major - 44);
        System.out.printf("WORA verdict  : bytecode is %s regardless of OS%n",
            (bytes[0] == (byte)0xCA && bytes[1] == (byte)0xFE) ? "valid (0xCAFEBABE)" : "INVALID");

        // Cleanup
        Files.delete(cls); Files.delete(src); Files.delete(tmpDir);
    }
}
```

**How to run:** `java WoraAudit.java`

This compiles a tiny class on the fly, reads the resulting `.class` binary, and verifies `0xCAFEBABE` — the magic number every Java class file has carried since 1.0. The `path.separator` check highlights one real WORA pitfall: classpath-building code that hardcodes `:` breaks on Windows.

## 6. Walkthrough

Execution flows through `WoraAudit.main`:

1. **Platform identity block** — `System.getProperty` queries the JVM launcher's property table. `os.name` returns `"Mac OS X"` or `"Linux"` or `"Windows 10"` depending on the host. `path.separator` returns `":"` (Unix) or `";"` (Windows) — the JVM abstracts the OS but exposes the differences through properties, so your code can adapt.

2. **Source generation** — `Files.createTempDirectory` + `Files.writeString` writes a trivial `Probe.java` into a temp folder. `ProcessBuilder` runs the system `javac` to compile it — same compiler used for any production build.

3. **Magic bytes read** — `Files.readAllBytes` loads the `.class` binary. Bytes 0–3 are always `0xCA 0xFE 0xBA 0xBE` — this is the JVM specification's "class file magic". Any file lacking it is rejected by the JVM before a single instruction executes. The `& 0xFF` mask converts signed Java `byte` to an unsigned value for correct hex printing.

4. **Version decode** — bytes 4–5 are the minor version, bytes 6–7 are the major version, stored in big-endian order (hence `<< 8 | next`). Java has always used big-endian in class files, regardless of the host CPU's endianness — another deliberate platform-neutral decision.

5. **WORA verdict** — if the magic matches, the bytecode is valid and would load on any compliant JVM. The class version number tells you the minimum JDK needed to *run* it.

Expected output on JDK 21 on macOS/ARM:
```
=== WORA Audit ===

Platform      : Mac OS X / aarch64
Path separator: ':'  (Unix-style — colons in classpath)
Endianness    : LITTLE_ENDIAN

Magic bytes   : CA FE BA BE  (must be CA FE BA BE)
Class version : 65.0  (JDK 21)
WORA verdict  : bytecode is valid (0xCAFEBABE) regardless of OS
```

Note: `Endianness` reports `LITTLE_ENDIAN` even on ARM Mac — but class file bytes are always big-endian. The JVM reads them correctly regardless.

## 7. Gotchas & takeaways

> WORA is a **JVM contract**, not a magic property of Java code itself. Code that calls `Runtime.exec("cmd.exe /c ...")` or hardcodes `"C:\\Users"` is not portable. WORA only works when your code avoids platform-specific assumptions.

> `path.separator` is `":"` on Unix and `";"` on Windows. Classpath-building code that concatenates paths with a hardcoded colon will silently break on Windows — always use `File.pathSeparator` or `System.getProperty("path.separator")`.

- The JVM is the engine of WORA: it takes platform-neutral bytecode and produces platform-specific native code at runtime.
- Every `.class` file starts with `0xCAFEBABE` — a check the JVM performs before executing a single instruction.
- `java.class.version = major.minor`, where `major - 44 = JDK version` (e.g. 65 → JDK 21).
- WORA breaks when you use OS-specific shell commands, native libraries (`.dll`/`.so`), or hardcoded path separators.
- The **TCK** (Technology Compatibility Kit) is the test suite that certifies a JVM as compliant — without it, WORA guarantees don't hold.
- WORA is why you can build on a Mac laptop and deploy to a Linux Docker container with the same JAR file.
