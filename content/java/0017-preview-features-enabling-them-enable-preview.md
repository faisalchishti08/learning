---
card: java
gi: 17
slug: preview-features-enabling-them-enable-preview
title: Preview features & enabling them (--enable-preview)
---

## 1. What it is

A **preview feature** in Java is a language, JVM, or API feature that is fully specified and implemented but not yet permanent — it exists behind the `--enable-preview` flag to gather real-world feedback before being committed to the Java language specification forever. Preview features may change between releases; they are not guaranteed to be backwards-compatible.

Preview features are different from **incubator modules** (API-level experiments) and **experimental JVM flags** (JVM-internal tuning). Preview features are language/spec-level — things like records, sealed classes, pattern matching, and unnamed classes all spent one or two releases as previews before finalisation.

## 2. Why & when

The six-month release cadence creates a problem: you want to get feedback on a new language feature from real developers using it in real code, but you don't want to commit to the exact syntax and semantics permanently on the first release. Preview features solve this: they land in a release, developers try them, they report feedback, and the feature is finalised (or refined, or dropped) in the next release.

You use `--enable-preview` when:
- Experimenting with upcoming language features in a development environment.
- Following a new JEP that's in preview and want to understand it before it's final.
- Using a framework or tool that explicitly targets preview features (e.g. early adopters of string templates).

You do **not** use `--enable-preview` in production, because the feature can change in the next release, breaking your code.

## 3. Core concept

`--enable-preview` must be passed to **both** the compiler and the runtime:

```
javac --enable-preview --release 21 MyClass.java
java  --enable-preview MyClass
```

If you compile with `--enable-preview` and run without it, the JVM rejects the class file:
```
Error: LinkageError occurred while loading main class MyClass
  java.lang.UnsupportedClassVersionError: Preview features are not enabled for MyClass
  (class file version 65.65535). Try running with '--enable-preview'
```

The version `65.65535` is the signal: the class file major is 65 (Java 21) and the minor is 65535 (0xFFFF), the JVM's sentinel value meaning "preview features used."

**Preview feature lifecycle:**
```
Preview (release N, --enable-preview required)
  → possibly: 2nd preview (release N+1) with refinements
  → Final (release N+1 or N+2, no flag needed)
```

Examples:
- Records: preview Java 14, 2nd preview Java 15, **final Java 16**.
- Sealed classes: preview Java 15, 2nd preview Java 16, **final Java 17**.
- Pattern matching for `switch`: preview Java 17–20, **final Java 21**.
- Virtual threads: preview Java 19–20, **final Java 21**.
- String templates: preview Java 21–22, dropped from Java 23 (rare case).

## 4. Diagram

<svg viewBox="0 0 680 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Preview feature lifecycle: preview in one release, possibly refined, then final">
  <defs>
    <marker id="aprev" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <!-- Stages -->
  <rect x="20" y="70" width="130" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="85" y="96"  fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">Preview</text>
  <text x="85" y="112" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Java N</text>
  <text x="85" y="124" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">--enable-preview</text>

  <line x1="150" y1="100" x2="188" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#aprev)"/>
  <text x="169" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">feedback</text>

  <rect x="190" y="70" width="160" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="270" y="96"  fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">2nd Preview</text>
  <text x="270" y="112" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Java N+1 (optional)</text>
  <text x="270" y="124" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">refined + --enable-preview</text>

  <line x1="350" y1="100" x2="388" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#aprev)"/>
  <text x="369" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">final</text>

  <rect x="390" y="70" width="130" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="455" y="96"  fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Final</text>
  <text x="455" y="112" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Java N+1 or N+2</text>
  <text x="455" y="124" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">no flag needed</text>

  <!-- Drop path -->
  <rect x="390" y="148" width="130" height="32" rx="6" fill="#0d1117" stroke="#f85149" stroke-width="1.5" stroke-dasharray="4,2"/>
  <text x="455" y="166" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Dropped (rare)</text>
  <line x1="455" y1="130" x2="455" y2="147" stroke="#f85149" stroke-width="1" stroke-dasharray="3,2"/>

  <!-- version note -->
  <text x="560" y="90" fill="#8b949e" font-size="9" font-family="sans-serif">class minor=0xFFFF</text>
  <text x="560" y="104" fill="#8b949e" font-size="9" font-family="sans-serif">signals preview class</text>
</svg>

Preview features require `--enable-preview` at compile and runtime. They may be refined across releases before becoming permanent.

## 5. Runnable example

Scenario: explore how the compiler enforces the preview flag, and write code that uses a preview-era feature (demonstrated with a feature that was preview in Java 21 or earlier and is now final — so it actually compiles cleanly on modern JDKs).

### Level 1 — Basic

```java
// PreviewCheck.java
// Demonstrates how to detect if the class was compiled with preview features
public class PreviewCheck {
    public static void main(String[] args) {
        System.out.println("Java version: " + Runtime.version());
        System.out.println("Feature     : " + Runtime.version().feature());

        // Check class file minor version: 0xFFFF (65535) means preview-enabled
        try {
            var classBytes = PreviewCheck.class.getResourceAsStream(
                "/PreviewCheck.class");
            if (classBytes != null) {
                byte[] header = classBytes.readAllBytes();
                int minor = ((header[4] & 0xFF) << 8) | (header[5] & 0xFF);
                System.out.println("Class minor version: " + minor +
                    (minor == 65535 ? " (preview features enabled)" : " (standard)"));
                classBytes.close();
            } else {
                System.out.println("Class file not accessible via classloader in source-launch mode.");
            }
        } catch (Exception e) {
            System.out.println("Could not read class header: " + e.getMessage());
        }

        System.out.println("\nTo enable preview features:");
        System.out.println("  javac --enable-preview --release " + Runtime.version().feature() + " PreviewCheck.java");
        System.out.println("  java  --enable-preview PreviewCheck");
    }
}
```

**How to run:** `java PreviewCheck.java`

When run without `--enable-preview`, the class minor version is 0. When compiled and run WITH `--enable-preview`, the minor version is 65535 (0xFFFF).

### Level 2 — Intermediate

Same scenario: write code that uses a feature that was *preview* during its introduction (unnamed patterns and variables, JEP 456 — preview Java 21, final Java 22) to show the ergonomics difference before/after.

```java
// UnnamedVariables.java
// JEP 456: Unnamed Variables — preview Java 21, FINAL Java 22
// Run on Java 22+: java UnnamedVariables.java
// Run on Java 21: java --enable-preview UnnamedVariables.java
import java.util.*;

public class UnnamedVariables {

    sealed interface Shape permits Circle, Rectangle, Triangle {}
    record Circle(double radius) implements Shape {}
    record Rectangle(double width, double height) implements Shape {}
    record Triangle(double base, double height) implements Shape {}

    public static void main(String[] args) {
        List<Shape> shapes = List.of(
            new Circle(5.0),
            new Rectangle(4.0, 3.0),
            new Triangle(6.0, 8.0)
        );

        System.out.println("Areas using pattern matching:");
        for (Shape s : shapes) {
            double area = switch (s) {
                case Circle c    -> Math.PI * c.radius() * c.radius();
                case Rectangle r -> r.width() * r.height();
                case Triangle t  -> 0.5 * t.base() * t.height();
            };
            System.out.printf("  %-30s area = %.2f%n", s, area);
        }

        // Unnamed variable _ in catch (JEP 456 — Java 22+ final)
        // Before JEP 456: had to write catch (NumberFormatException e) even if not using e
        System.out.println("\nUnnamed variable in catch:");
        String[] inputs = {"42", "not-a-number", "7"};
        int sum = 0;
        for (String input : inputs) {
            try {
                sum += Integer.parseInt(input);
            } catch (NumberFormatException _) {   // _ is the unnamed variable
                System.out.println("  Skipping invalid input: " + input);
            }
        }
        System.out.println("  Sum of valid numbers: " + sum);
    }
}
```

**How to run:** `java UnnamedVariables.java` (on Java 22+ without `--enable-preview`; on Java 21 add the flag)

The `_` (unnamed variable) in `catch (NumberFormatException _)` was a preview feature in Java 21, final in Java 22. This example shows the progression: the same syntax requires the flag in one release and none in the next.

### Level 3 — Advanced

Same scenario grown to demonstrate how to gate preview features at runtime and handle graceful degradation — important for library authors who want to support multiple Java versions.

```java
// PreviewFeatureGating.java
import java.lang.reflect.*;
import java.util.*;

public class PreviewFeatureGating {

    // Check if a specific preview feature is available via reflection
    // (simulates how framework authors probe for optional capabilities)
    static boolean hasFeature(String className, String methodName) {
        try {
            Class<?> cls = Class.forName(className);
            cls.getMethod(methodName);
            return true;
        } catch (ClassNotFoundException | NoSuchMethodException e) {
            return false;
        }
    }

    public static void main(String[] args) {
        int feature = Runtime.version().feature();
        System.out.println("╔════════════════════════════════════════════╗");
        System.out.println("║       Preview Feature Compatibility Gate   ║");
        System.out.println("╚═══════════��════════════════════════════════╝\n");
        System.out.println("Java " + feature);

        // Feature matrix with the Java version they became final
        record FeatureEntry(String name, int previewSince, int finalSince, String jep) {}

        List<FeatureEntry> features = List.of(
            new FeatureEntry("Records",                    14, 16, "JEP 395"),
            new FeatureEntry("Sealed classes",             15, 17, "JEP 409"),
            new FeatureEntry("Pattern matching instanceof",14, 16, "JEP 394"),
            new FeatureEntry("Pattern matching switch",    17, 21, "JEP 441"),
            new FeatureEntry("Virtual threads",            19, 21, "JEP 444"),
            new FeatureEntry("Sequenced collections",      -1, 21, "JEP 431"),
            new FeatureEntry("Unnamed variables & patterns",21, 22, "JEP 456"),
            new FeatureEntry("Stream Gatherers",           22, 24, "JEP 485"),
            new FeatureEntry("Flexible constructor bodies",22, 25, "JEP 492")
        );

        System.out.printf("%-35s  %-8s  %-8s  %-10s  %s%n",
            "Feature", "Preview", "Final", "JEP", "Status on Java " + feature);
        System.out.println("-".repeat(90));

        for (FeatureEntry f : features) {
            String status;
            if (feature >= f.finalSince()) {
                status = "FINAL — use without --enable-preview";
            } else if (f.previewSince() > 0 && feature >= f.previewSince()) {
                status = "PREVIEW — requires --enable-preview";
            } else {
                status = "NOT AVAILABLE";
            }
            System.out.printf("%-35s  %-8s  %-8d  %-10s  %s%n",
                f.name(),
                f.previewSince() < 0 ? "n/a" : String.valueOf(f.previewSince()),
                f.finalSince(), f.jep(), status);
        }

        System.out.println("\n[ Runtime probe: Virtual Threads (final Java 21) ]");
        boolean hasVT = feature >= 21;
        if (hasVT) {
            System.out.println("  Virtual threads available. No --enable-preview needed.");
            try {
                Thread vt = Thread.ofVirtual().start(() ->
                    System.out.println("  Virtual thread running: " + Thread.currentThread().isVirtual()));
                vt.join();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        } else {
            System.out.println("  Virtual threads not available on Java " + feature + ". Upgrade to 21+.");
        }

        System.out.println("\n[ Preview feature compile/run instructions ]");
        System.out.println("  Compile: javac --enable-preview --release " + feature + " FileName.java");
        System.out.println("  Run    : java  --enable-preview FileName");
        System.out.println("  Maven  : add <compilerArgs><arg>--enable-preview</arg></compilerArgs>");
        System.out.println("           and <jvmArgs><jvmArg>--enable-preview</jvmArg></jvmArgs> to surefire");
    }
}
```

**How to run:** `java PreviewFeatureGating.java`

The `FeatureEntry` record (final Java 16) is used inside a program that runs on Java 17+. The table shows which features need `--enable-preview` on the current version.

## 6. Walkthrough

Execution in `PreviewFeatureGating.main`:

1. **`Runtime.version().feature()`** returns the integer major version. All feature availability comparisons are `feature >= finalSince` — straightforward integer comparisons.

2. **`FeatureEntry` records** — each entry carries `previewSince` (the first release it appeared as preview; `-1` if it was never a preview, just added directly) and `finalSince` (the release it became permanent). The table is a snapshot; new entries would be added as new JEPs land.

3. **Status classification** — three states: `FINAL` (use freely), `PREVIEW` (need flag), `NOT AVAILABLE` (JDK too old). The `previewSince > 0 && feature >= previewSince` check ensures we don't claim "preview" for features whose preview era predates the JDK.

4. **Virtual thread probe** — `Thread.ofVirtual().start(...)` would throw `NoSuchMethodError` on Java < 21 if someone bypassed the version check. The `feature >= 21` guard prevents that. The lambda prints `Thread.currentThread().isVirtual()` — `true` for virtual threads, `false` for platform threads.

5. **Maven configuration note** — in Maven, `--enable-preview` must be in both `<compilerArgs>` (javac) and the Surefire plugin's `<jvmArgs>` (for running tests). Missing either causes compilation or test runtime failures.

State/data flow:
```
Runtime.version().feature()  → int (e.g. 22)
List<FeatureEntry>           → static list (no I/O)
  for each entry: feature >= finalSince → "FINAL" / "PREVIEW" / "NOT AVAILABLE"
Thread.ofVirtual().start()   → virtual thread → runs lambda → joins
console output
```

## 7. Gotchas & takeaways

> **A preview feature compiled with Java 21 (`--enable-preview`) will NOT run on Java 22 without also passing `--enable-preview`** — even if the feature became final in Java 22. You must recompile with the Java 22 compiler (without `--enable-preview` if final) to get a standard class file. Preview class files carry the `0xFFFF` minor version and are always rejected without the flag.

> **String Templates (JEP 430) was preview in Java 21–22 and then DROPPED in Java 23** — the only notable feature dropped after preview. This is the risk of using preview features in any code you intend to maintain long-term.

- Preview features require `--enable-preview` at BOTH compile time and run time.
- Class files compiled with `--enable-preview` have minor version `0xFFFF` — the JVM rejects them without the flag.
- Preview → Final typically takes 1–2 releases; exceptions are rare.
- `Runtime.version().feature() >= N` is the correct runtime check for "does this Java support feature F?".
- For Maven/Gradle: set `--enable-preview` in both compiler plugin args and test runner JVM args.
- Never use `--enable-preview` in production — the feature may change in the next release.
