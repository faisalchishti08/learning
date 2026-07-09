---
card: java
gi: 717
slug: utf-8-as-default-charset
title: UTF-8 as default charset
---

## 1. What it is

**Java 18** (JEP 400) makes **UTF-8** the default charset for the JDK's standard APIs — `Charset.defaultCharset()`, `new FileReader(...)`, `new PrintWriter(...)`, `System.getProperty("file.encoding")`, and every other API that previously fell back to the *platform's native encoding* now uses UTF-8, everywhere, on every operating system. Before Java 18, if you didn't explicitly pass a charset, the JVM guessed based on the host OS: UTF-8 on most modern Linux and macOS systems, but often a legacy encoding like `windows-1252` on Windows, or something else entirely depending on locale settings. JEP 400 removes that guesswork by fixing the default to UTF-8 everywhere, regardless of platform or locale.

## 2. Why & when

Java's platform-default-charset behavior dated back to Java 1.0, when Java programs were expected to feel "native" to whatever OS they ran on, and matching the host's default text encoding seemed like the right way to interoperate with local files and terminals. In practice this became one of the most persistent sources of "works on my machine" bugs in the entire ecosystem: a developer on macOS writes a file with `new FileWriter("out.txt")`, gets UTF-8 without asking for it, ships the code, and a teammate on Windows reads that same file with `new FileReader("out.txt")` and gets mojibake — because their platform default was `windows-1252`, not UTF-8. The bug was invisible in code review, invisible in unit tests run on the author's machine, and only surfaced in production or on a colleague's laptop. Meanwhile UTF-8 had, over the two decades since Java 1.0, become the de facto universal encoding for the web, for source files, for JSON, and for nearly every modern text format. JEP 400 aligns Java's default with that reality: use UTF-8 unless a charset is explicitly requested, so behavior is consistent and predictable across every machine a Java program runs on, and reserve platform-default lookups for the rare `Charset.defaultCharset()` call site that genuinely wants the host's native encoding for OS-level interop (such as parsing OS-generated file names).

## 3. Core concept

```java
// Before Java 18, on a Windows machine with a non-UTF-8 platform default:
// new FileWriter("out.txt")  -> writes using windows-1252 (unless overridden)
//
// Java 18 and later, on the SAME Windows machine:
// new FileWriter("out.txt")  -> writes using UTF-8, always

// The old platform-dependent behavior is still reachable explicitly:
java.nio.charset.Charset native_ = Charset.forName(System.getProperty("native.encoding"));
```

Two related but distinct properties now exist: `file.encoding` (the JDK's *default* charset, fixed at UTF-8 since Java 18) and the new `native.encoding` system property (the actual platform encoding, for the rare code that still needs it).

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Before Java 18 the default charset varied by operating system; from Java 18 onward it is UTF-8 everywhere">
  <text x="320" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Same code: new FileWriter("out.txt")</text>

  <rect x="20" y="50" width="280" height="140" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="72" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Before Java 18</text>
  <text x="160" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Linux/macOS -&gt; UTF-8</text>
  <text x="160" y="122" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Windows -&gt; windows-1252 (often)</text>
  <text x="160" y="150" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">Same code, different bytes on disk</text>

  <rect x="340" y="50" width="280" height="140" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="72" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 18+</text>
  <text x="480" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Linux, macOS, Windows -&gt; UTF-8</text>
  <text x="480" y="150" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">Same code, same bytes, every platform</text>
</svg>

The default charset stopped depending on which operating system the JVM happened to be running on.

## 5. Runnable example

Scenario: writing a file containing a non-ASCII character and reading it back, first relying on defaults, then making the encoding explicit for portability, then building a small utility that reports exactly which charsets are in play so cross-platform mismatches can be diagnosed before they cause data corruption.

### Level 1 — Basic

```java
// File: DefaultCharsetBasic.java
import java.io.*;
import java.nio.file.*;

public class DefaultCharsetBasic {
    public static void main(String[] args) throws IOException {
        Path file = Files.createTempFile("greeting", ".txt");

        // Relies on the JDK's default charset — UTF-8 on Java 18+, everywhere.
        try (Writer w = new FileWriter(file.toFile())) {
            w.write("café – hello in UTF-8: 你好");
        }

        String readBack = Files.readString(file); // Files.readString always uses UTF-8
        System.out.println("Default charset: " + java.nio.charset.Charset.defaultCharset());
        System.out.println("Content read back: " + readBack);

        Files.deleteIfExists(file);
    }
}
```

**How to run:**
```
java DefaultCharsetBasic.java
```

Expected output (on Java 18+, any OS):
```
Default charset: UTF-8
Content read back: café – hello in UTF-8: 你好
```

On Java 17 or earlier running on Windows with a non-UTF-8 platform default, the same program could print a *different* default charset and garbled content, because `new FileWriter(...)` and `Files.readString` would disagree about encoding — `FileWriter` used the platform default, `readString` always used UTF-8.

### Level 2 — Intermediate

```java
// File: ExplicitCharsetIntermediate.java
// Never rely on an implicit charset for data crossing machine boundaries —
// name it, even though Java 18 made the implicit case safe by default.
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;

public class ExplicitCharsetIntermediate {
    public static void main(String[] args) throws IOException {
        Path file = Files.createTempFile("greeting", ".txt");
        String text = "café – hello in UTF-8: 你好";

        // Explicit charset: correct on Java 18+ AND on any older JDK too.
        Files.writeString(file, text, StandardCharsets.UTF_8);
        String readBack = Files.readString(file, StandardCharsets.UTF_8);

        System.out.println("Wrote and read with explicit UTF-8: " + readBack);
        System.out.println("Bytes on disk: " + Files.size(file) + " (multi-byte chars cost more than 1 byte each)");

        Files.deleteIfExists(file);
    }
}
```

**How to run:**
```
java ExplicitCharsetIntermediate.java
```

Expected output:
```
Wrote and read with explicit UTF-8: café – hello in UTF-8: 你好
Bytes on disk: 33 (multi-byte chars cost more than 1 byte each)
```

This adds the real-world concern JEP 400 doesn't fully remove: even with a safe default, library code that ships across teams and JDK versions should still name its charset explicitly, so behavior is guaranteed rather than inherited from configuration.

### Level 3 — Advanced

```java
// File: CharsetDiagnostics.java
// A small utility distinguishing "default charset" (file.encoding, UTF-8 on
// Java 18+) from "native encoding" (native.encoding, the actual platform
// encoding), and demonstrating the escape hatch for code that genuinely
// needs the platform's native encoding (e.g. talking to a native OS API).
import java.io.*;
import java.nio.charset.Charset;
import java.nio.file.*;

public class CharsetDiagnostics {
    public static void main(String[] args) throws IOException {
        Charset defaultCharset = Charset.defaultCharset();
        String nativeEncodingName = System.getProperty("native.encoding");
        Charset nativeCharset = nativeEncodingName != null
                ? Charset.forName(nativeEncodingName)
                : defaultCharset;

        System.out.println("JDK default charset (file.encoding): " + defaultCharset);
        System.out.println("Platform native encoding (native.encoding): " + nativeCharset);
        System.out.println("These match on Java 18+ UTF-8-native platforms, but can differ on legacy Windows locales.");

        // Round-trip through both, proving the default is now stable and
        // explicit charsets remain available whenever native interop demands them.
        Path file = Files.createTempFile("diag", ".txt");
        String payload = "diagnostic: café 你好";

        Files.writeString(file, payload); // uses default charset (UTF-8 on Java 18+)
        byte[] rawBytes = Files.readAllBytes(file);
        String decodedAsDefault = new String(rawBytes, defaultCharset);
        String decodedAsNative = new String(rawBytes, nativeCharset);

        System.out.println("Decoded with default charset: " + decodedAsDefault);
        System.out.println("Decoded with native charset:   " + decodedAsNative);
        System.out.println("Match: " + decodedAsDefault.equals(decodedAsNative));

        Files.deleteIfExists(file);
    }
}
```

**How to run:**
```
java CharsetDiagnostics.java
```

Expected output (Java 18+ on a UTF-8-native platform such as Linux or macOS):
```
JDK default charset (file.encoding): UTF-8
Platform native encoding (native.encoding): UTF-8
These match on Java 18+ UTF-8-native platforms, but can differ on legacy Windows locales.
Decoded with default charset: diagnostic: café 你好
Decoded with native charset:   diagnostic: café 你好
Match: true
```

## 6. Walkthrough

1. `CharsetDiagnostics.main` first reads `Charset.defaultCharset()` — this is the value JEP 400 pinned to UTF-8 starting in Java 18; every API in the JDK that doesn't take an explicit `Charset` argument falls back to this value.
2. It then reads the `native.encoding` system property, a property JEP 400 *introduced* specifically so code that genuinely needs the OS's real native encoding (for example, decoding file names produced by the operating system, or shelling out to native processes) still has a documented, reliable way to get it — separate from the now-fixed default.
3. `Files.writeString(file, payload)` is called with no charset argument, so it uses the default charset — UTF-8, guaranteed, on Java 18+. Before Java 18, on some Windows configurations, this same call could have silently used a different encoding.
4. The raw bytes are read back with `Files.readAllBytes` and decoded twice: once against `defaultCharset` and once against `nativeCharset`. On any Java 18+ platform where the OS's native encoding is already UTF-8 (the common case for modern Linux, macOS, and even most current Windows configurations), both decodes match. The diagnostic exists to make visible the exact moment a mismatch *would* have shown up on the older, platform-dependent default.
5. The takeaway is procedural, not just observational: `defaultCharset()` is now something a program can trust unconditionally, while `native.encoding` is the deliberate, opt-in door left open for the narrow cases that still need the platform's own answer.

```
Text data written with no explicit charset
        |
        v
Java 17 and earlier: Charset.defaultCharset() == platform-dependent
        |                                             |
        v                                             v
  UTF-8 on Linux/macOS                     windows-1252 (or other) on Windows
        |                                             |
        +---------------------+----------------------+
                               v
                    Same bytes, different meaning
                    depending on which machine reads them

Java 18+: Charset.defaultCharset() == UTF-8, always
        |
        v
  Same bytes, same meaning, on every machine
```

## 7. Gotchas & takeaways

> `Charset.defaultCharset()` being fixed at UTF-8 does **not** mean every text-processing bug involving encoding disappears — it means the *implicit* case is now safe. Code that reads bytes written by an external, non-UTF-8 source (a legacy database export, a file from an old Windows tool) still needs an explicit charset to decode correctly; JEP 400 only fixes what happens when *no* charset is specified.
- The change affects APIs that previously used the platform default: `FileReader`, `FileWriter`, `PrintStream`, `PrintWriter` (no-charset constructors), `Charset.defaultCharset()`, and the `file.encoding` system property — but not APIs that already always used UTF-8 (like `Files.readString`/`writeString`) or APIs where you already passed a charset explicitly.
- The new `native.encoding` system property is the escape hatch: use it (or `System.getProperty("sun.jnu.encoding")` for the JVM's own file-name/argument encoding, which JEP 400 does *not* change) when code genuinely needs the OS's real native encoding rather than the JDK's UTF-8 default.
- Best practice both before and after this JEP: pass `StandardCharsets.UTF_8` (or whatever charset the format actually requires) explicitly at any I/O boundary that crosses machines, teams, or JDK versions — don't rely on defaults even when they've become predictable, since predictability of *this JVM's* default says nothing about the encoding of bytes written by some *other* system.
- If upgrading an old codebase to Java 18+, the risk direction flips from before: code that previously depended on getting the *platform* default (rare, but it happens with some legacy Windows-specific text-processing tools) may now behave differently, since it silently gets UTF-8 instead.
