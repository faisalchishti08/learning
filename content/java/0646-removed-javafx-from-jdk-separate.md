---
card: java
gi: 646
slug: removed-javafx-from-jdk-separate
title: Removed JavaFX from JDK (separate)
---

## 1. What it is

**JavaFX** is a rich-client application framework for building desktop and embedded GUI applications. From Java 7 through Java 10, JavaFX was bundled with the JDK — it shipped as part of the standard Oracle JDK distribution. In **Java 11**, JavaFX was **removed from the JDK** and became a standalone open-source project under the **OpenJFX** umbrella. This means the `javafx.*` packages are no longer in the default module path; to use JavaFX, you must download the OpenJFX SDK separately or add it as Maven/Gradle dependencies. The removal was part of the broader effort to decouple non-core technologies from the JDK (similar to the Java EE module removals) so each can evolve at its own pace.

## 2. Why & when

JavaFX was always an awkward fit in the JDK: it was a massive framework (~20 MB) that most server-side Java applications never used, yet every JDK distribution had to ship it. Its release cycle was tied to the JDK's, so JavaFX couldn't release updates independently. By moving JavaFX to OpenJFX (openjfx.io), it gained an independent release cadence (new versions every 6 months), a dedicated community, and the freedom to adopt modern graphics technologies without JDK-process overhead. If you develop Java desktop applications with JavaFX, you now include it as a dependency — just like any other library. If you don't use it, your JDK is smaller and simpler.

## 3. Core concept

```bash
# Before Java 11: JavaFX was bundled — just compile and run
javac MyApp.java
java MyApp

# Java 11+: JavaFX is a separate SDK
# Option 1: Download the SDK from openjfx.io and use --module-path
java --module-path /path/to/javafx-sdk/lib --add-modules javafx.controls MyApp.java

# Option 2: Use Maven/Gradle dependencies
#   <dependency>
#     <groupId>org.openjfx</groupId>
#     <artifactId>javafx-controls</artifactId>
#     <version>21.0.0</version>
#   </dependency>

# Option 3: Use a JDK distribution that bundles JavaFX (Azul, Liberica)
```

The `javafx.*` packages (`javafx.application.Application`, `javafx.scene.Scene`, `javafx.stage.Stage`, etc.) are identical — only their location changed.

## 4. Diagram

<svg viewBox="0 0 560 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JavaFX moved from JDK (Java 8-10) to standalone OpenJFX (Java 11+)">
  <rect x="10" y="10" width="540" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="20" width="240" height="60" rx="4" fill="#0d1117" stroke="#f85149"/>
  <text x="140" y="40" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">Java 8–10: JDK with JavaFX</text>
  <text x="140" y="55" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">javafx.* bundled in the JDK distribution</text>
  <text x="140" y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">javafx.application, javafx.scene, javafx.stage, ...</text>

  <text x="275" y="50" fill="#8b949e" font-size="16" font-family="monospace">→</text>

  <rect x="290" y="20" width="250" height="60" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="415" y="40" fill="#3fb950" font-size="11" text-anchor="middle" font-family="monospace">Java 11+: JDK without JavaFX</text>
  <text x="415" y="55" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">OpenJFX as separate SDK / Maven dependency</text>
  <text x="415" y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Same API — different distribution model</text>

  <text x="20" y="105" fill="#8b949e" font-size="9" font-family="sans-serif">JavaFX modules: javafx.base, javafx.controls, javafx.fxml, javafx.graphics, javafx.media, javafx.swing, javafx.web</text>
  <text x="20" y="123" fill="#3fb950" font-size="9" font-family="sans-serif">OpenJFX: independent open-source project at openjfx.io | Maven: org.openjfx group | Independent release cycle</text>
  <text x="20" y="141" fill="#f85149" font-size="9" font-family="sans-serif">Also removed: javapackager (packaging tool), javafxpackager — replaced by jpackage (since Java 14)</text>
</svg>

JavaFX was removed from the JDK by JEP 323 and became a standalone project (OpenJFX). The API is unchanged; only the distribution model changed from "built-in" to "add as dependency."

## 5. Runnable example

Scenario: detecting JavaFX availability and understanding the migration path — starting with basic detection, extending to a simple JavaFX application, and finally discussing distribution options.

### Level 1 — Basic

```java
// File: JavaFXCheck.java
public class JavaFXCheck {
    public static void main(String[] args) {
        System.out.println("=== JavaFX Availability Check ===\n");
        System.out.println("Java version: " + System.getProperty("java.version"));
        System.out.println("Java vendor:  " + System.getProperty("java.vendor"));

        // Try to load a JavaFX class
        try {
            Class.forName("javafx.application.Application");
            System.out.println("\nJavaFX IS available in this JDK.");
            System.out.println("(Bundled JDK like Azul ZuluFX or Liberica Full)");
        } catch (ClassNotFoundException e) {
            System.out.println("\nJavaFX is NOT in this JDK (standard since Java 11).");
            System.out.println("\nTo use JavaFX, you need to:");
            System.out.println("  1. Download OpenJFX SDK: https://openjfx.io");
            System.out.println("  2. Or add Maven dependency: org.openjfx:javafx-controls");
            System.out.println("  3. Or use a JDK that bundles JavaFX (Azul, Liberica)");
        }

        System.out.println("\n=== JavaFX Module Overview ===\n");
        System.out.println("Module              Purpose");
        System.out.println("------              -------");
        System.out.println("javafx.base         Core classes, bindings, properties");
        System.out.println("javafx.controls     UI controls (Button, TableView, etc.)");
        System.out.println("javafx.graphics     Rendering, CSS, geometry");
        System.out.println("javafx.fxml         XML-based UI definition");
        System.out.println("javafx.media        Audio/video playback");
        System.out.println("javafx.swing        Embed Swing in JavaFX / vice versa");
        System.out.println("javafx.web          WebView (embedded browser)");
    }
}
```

**How to run:** `java JavaFXCheck.java`

Expected output:
```
=== JavaFX Availability Check ===

Java version: 17.0...
Java vendor:  ...

JavaFX is NOT in this JDK (standard since Java 11).

To use JavaFX, you need to:
  1. Download OpenJFX SDK: https://openjfx.io
  2. Or add Maven dependency: org.openjfx:javafx-controls
  3. Or use a JDK that bundles JavaFX (Azul, Liberica)

=== JavaFX Module Overview ===

Module              Purpose
------              -------
javafx.base         Core classes, bindings, properties
...
```

### Level 2 — Intermediate

```java
// File: JavaFXMigration.java
public class JavaFXMigration {
    public static void main(String[] args) {
        System.out.println("=== JavaFX Migration Guide ===\n");

        System.out.println("Option 1: Command-line (SDK download)\n");
        System.out.println("  1. Download SDK from https://openjfx.io");
        System.out.println("  2. Extract to e.g., /opt/javafx-sdk-21");
        System.out.println("  3. Compile and run with module path:");
        System.out.println("     javac --module-path /opt/javafx-sdk-21/lib \\");
        System.out.println("           --add-modules javafx.controls MyApp.java");
        System.out.println("     java --module-path /opt/javafx-sdk-21/lib \\");
        System.out.println("          --add-modules javafx.controls MyApp");
        System.out.println();

        System.out.println("Option 2: Maven (recommended for projects)\n");
        System.out.println("  <dependencies>");
        System.out.println("    <dependency>");
        System.out.println("      <groupId>org.openjfx</groupId>");
        System.out.println("      <artifactId>javafx-controls</artifactId>");
        System.out.println("      <version>21.0.0</version>");
        System.out.println("    </dependency>");
        System.out.println("  </dependencies>");
        System.out.println();
        System.out.println("  <!-- Also add javafx-maven-plugin for running -->");
        System.out.println("  <plugin>");
        System.out.println("    <groupId>org.openjfx</groupId>");
        System.out.println("    <artifactId>javafx-maven-plugin</artifactId>");
        System.out.println("    <version>0.0.8</version>");
        System.out.println("  </plugin>");
        System.out.println();

        System.out.println("Option 3: Bundled JDK (simplest for desktop apps)\n");
        System.out.println("  - Azul ZuluFX:        https://www.azul.com/downloads/");
        System.out.println("  - Liberica Full JDK:  https://bell-sw.com/pages/downloads/");
        System.out.println("  - Oracle JDK 8/10:    last versions with bundled JavaFX");
        System.out.println("  (These JDKs include JavaFX — no extra setup needed)");
        System.out.println();

        System.out.println("Option 4: jlink + jpackage (create native installer)\n");
        System.out.println("  jlink --add-modules javafx.controls --output myapp-runtime");
        System.out.println("  jpackage --name MyApp --input . --main-jar myapp.jar \\");
        System.out.println("           --main-class com.myapp.Main \\");
        System.out.println("           --runtime-image myapp-runtime");
        System.out.println("  (Creates .dmg (macOS), .msi (Windows), .deb/.rpm (Linux))");
    }
}
```

**How to run:** `java JavaFXMigration.java`

Expected output:
```
=== JavaFX Migration Guide ===

Option 1: Command-line (SDK download)
  ...

Option 2: Maven (recommended for projects)
  ...

Option 3: Bundled JDK (simplest for desktop apps)
  ...

Option 4: jlink + jpackage (create native installer)
  ...
```

### Level 3 — Advanced

```java
// File: JavaFXAdvanced.java
import java.util.*;

public class JavaFXAdvanced {
    public static void main(String[] args) {
        System.out.println("=== JavaFX — Past, Present, and Future ===\n");

        System.out.println("1. History:");
        System.out.println("   JavaFX was introduced in 2008 (JavaFX 1.0) as a Flash competitor.");
        System.out.println("   JavaFX 2.0 (2011) dropped the scripting language, went pure Java API.");
        System.out.println("   Java 7u6 (2012): JavaFX bundled with JDK for the first time.");
        System.out.println("   Java 8 (2014): JavaFX became the official replacement for Swing.");
        System.out.println("   Java 11 (2018): JavaFX removed from JDK (JEP 323).");
        System.out.println("   Today: OpenJFX thrives as an independent open-source project.");
        System.out.println();

        System.out.println("2. JavaFX vs Swing:");
        System.out.printf("  %-20s %-20s\n", "Feature", "JavaFX", "Swing");
        System.out.println("  " + "-".repeat(52));
        System.out.printf("  %-20s %-20s\n", "Styling", "CSS", "Look-and-Feel");
        System.out.printf("  %-20s %-20s\n", "UI Definition", "FXML (XML)", "Java code only");
        System.out.printf("  %-20s %-20s\n", "Graphics", "Hardware-accelerated", "Software");
        System.out.printf("  %-20s %-20s\n", "Animation", "Built-in timeline", "Manual");
        System.out.printf("  %-20s %-20s\n", "WebView", "Built-in (WebKit)", "None");
        System.out.printf("  %-20s %-20s\n", "Status", "Active development", "Maintenance mode");
        System.out.println();

        System.out.println("3. Modern JavaFX Features:");
        System.out.println("   - 3D Graphics API");
        System.out.println("   - Rich text and charting controls");
        System.out.println("   - Media playback (audio/video)");
        System.out.println("   - WebView (embedded Chromium-based browser)");
        System.out.println("   - CSS styling (similar to web development)");
        System.out.println("   - FXML for declarative UI (separation of concerns)");
        System.out.println("   - Bindings and properties (reactive data model)");
        System.out.println();

        System.out.println("4. Current OpenJFX Versions:");
        System.out.println("   OpenJFX 11 (LTS) — first standalone release");
        System.out.println("   OpenJFX 17 (LTS) — current long-term support");
        System.out.println("   OpenJFX 21 (LTS) — latest LTS, Java 21 aligned");
        System.out.println("   OpenJFX 22+  — feature releases (every 6 months)");
        System.out.println();

        System.out.println("5. javapackager Removal:");
        System.out.println("   Along with JavaFX, the javapackager tool was removed in Java 11.");
        System.out.println("   Replacement: jpackage (added in Java 14, final in Java 16).");
        System.out.println("   jpackage creates native installers: .dmg, .msi, .deb, .rpm.");
        System.out.println("   Combined with jlink, it produces self-contained applications");
        System.out.println("   with an embedded JRE — users don't need Java installed.");
    }
}
```

**How to run:** `java JavaFXAdvanced.java`

Expected output:
```
=== JavaFX — Past, Present, and Future ===

1. History:
   ...

2. JavaFX vs Swing:
   ...

3. Modern JavaFX Features:
   ...

4. Current OpenJFX Versions:
   ...

5. javapackager Removal:
   ...
```

The production-flavoured hard cases: (1) **Module path requirement** — JavaFX on Java 11+ requires `--module-path` and `--add-modules` because it's not in the default module graph. The `javafx-maven-plugin` handles this automatically. (2) **Platform-specific natives** — JavaFX has native libraries (.dll, .dylib, .so) for graphics rendering. The SDK download includes all platforms; Maven artifacts are platform-classified. (3) **jpackage** — the replacement for `javapackager` creates native installers with embedded JRE. Combined with jlink (which creates a minimal runtime image with just the modules you need), you can ship a self-contained desktop app that doesn't require users to install Java.

## 6. Walkthrough

Tracing JavaFX availability detection:

1. `Class.forName("javafx.application.Application")` attempts to load the core JavaFX class using the current thread's context class loader.

2. On a JDK without JavaFX (standard since Java 11): the class loader searches the boot layer and classpath for a module or JAR containing `javafx.application.Application`. It finds none. `ClassNotFoundException` is thrown.

3. The `catch` block catches the exception and prints guidance on obtaining JavaFX.

4. On a JDK with bundled JavaFX (Azul ZuluFX, Liberica Full): `javafx.application.Application` is found in the `javafx.graphics` module in the boot layer. The class loads successfully, confirming JavaFX availability.

5. The application proceeds accordingly — either using JavaFX directly or informing the user how to set it up.

The removal is purely a distribution change: the JavaFX API is identical, and applications compiled against JavaFX on Java 8 work on Java 11+ as long as OpenJFX is on the module path.

## 7. Gotchas & takeaways

> JavaFX is **not "dead"** — it was only removed from the JDK distribution. OpenJFX is actively maintained with a vibrant community, regular releases, and commercial support from multiple vendors (Gluon, BellSoft, Azul). The "JavaFX is dead" myth comes from confusion between "not in the JDK" and "abandoned."

- JavaFX applications compiled on Java 8 with bundled JavaFX still work on Java 11+ — just add OpenJFX as a dependency. No code changes are typically needed.
- The `javapackager` tool was also removed. Use `jpackage` (Java 14+) for creating native installers. It's more capable and maintained.
- Some JDK vendors ship **JavaFX-included builds**: Azul ZuluFX, BellSoft Liberica Full JDK. If your project heavily uses JavaFX and you want minimal setup friction, consider these distributions.
- OpenJFX has an **independent release cycle** from the JDK. OpenJFX 11, 17, and 21 are LTS versions aligned with corresponding JDK LTS releases, but OpenJFX 22, 23, etc., ship on their own schedule.
- JavaFX on the module path requires explicit `--add-modules javafx.controls` (or whichever modules you use). The `javafx-maven-plugin` handles this automatically for Maven projects.
