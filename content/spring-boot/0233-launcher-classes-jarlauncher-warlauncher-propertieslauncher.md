---
card: spring-boot
gi: 233
slug: launcher-classes-jarlauncher-warlauncher-propertieslauncher
title: Launcher classes (JarLauncher / WarLauncher / PropertiesLauncher)
---

## 1. What it is

Spring Boot ships three `Launcher` classes that serve as the real `Main-Class` in an executable archive's manifest. Each knows how to find dependency JARs inside the archive, build a `LaunchedClassLoader`, and then delegate to your application's entry point. The right launcher is chosen automatically by the Spring Boot Maven/Gradle plugin.

## 2. Why & when

The JVM's built-in class loader cannot load classes from JARs nested inside another JAR. Each launcher solves this for a different packaging format. You rarely configure them manually, but understanding them matters when you customise packaging, debug class-loading issues, or add extra directories to the classpath at runtime.

## 3. Core concept

| Launcher | Archive type | Classpath source | Use when |
|---|---|---|---|
| `JarLauncher` | `.jar` | `BOOT-INF/lib/`, `BOOT-INF/classes/` | Default for `spring-boot:repackage` |
| `WarLauncher` | `.war` | `WEB-INF/lib/`, `WEB-INF/lib-provided/`, `WEB-INF/classes/` | WAR for embedded or traditional servlet container |
| `PropertiesLauncher` | `.jar` or `.war` | Configurable via `loader.properties` or system properties | Custom classpath, extra directories, encrypted entries |

`PropertiesLauncher` reads `loader.properties` from the archive root (or via `LOADER_PATH` env var) and can add external directories (e.g., `/ext/`) to the classpath, making it useful for plugin-style architectures where extra JARs are dropped beside the app.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="640" height="260" fill="#1c2430" rx="10"/>
  <!-- JarLauncher -->
  <rect x="20" y="50" width="180" height="80" rx="6" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="110" y="78" text-anchor="middle" fill="#6db33f">JarLauncher</text>
  <text x="110" y="96" text-anchor="middle" fill="#8b949e" font-size="11">BOOT-INF/lib/</text>
  <text x="110" y="112" text-anchor="middle" fill="#8b949e" font-size="11">BOOT-INF/classes/</text>
  <!-- WarLauncher -->
  <rect x="230" y="50" width="180" height="80" rx="6" fill="#2d3748" stroke="#79c0ff" stroke-width="2"/>
  <text x="320" y="78" text-anchor="middle" fill="#79c0ff">WarLauncher</text>
  <text x="320" y="96" text-anchor="middle" fill="#8b949e" font-size="11">WEB-INF/lib/</text>
  <text x="320" y="112" text-anchor="middle" fill="#8b949e" font-size="11">WEB-INF/classes/</text>
  <!-- PropertiesLauncher -->
  <rect x="440" y="50" width="180" height="80" rx="6" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="530" y="72" text-anchor="middle" fill="#e6edf3">Properties</text>
  <text x="530" y="90" text-anchor="middle" fill="#e6edf3">Launcher</text>
  <text x="530" y="110" text-anchor="middle" fill="#8b949e" font-size="11">loader.properties</text>
  <text x="530" y="126" text-anchor="middle" fill="#8b949e" font-size="11">/ LOADER_PATH env</text>
  <!-- LaunchedClassLoader -->
  <rect x="190" y="180" width="260" height="50" rx="6" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="202" text-anchor="middle" fill="#6db33f">LaunchedClassLoader</text>
  <text x="320" y="220" text-anchor="middle" fill="#8b949e" font-size="11">→ delegates to your Start-Class</text>
  <!-- arrows -->
  <line x1="110" y1="130" x2="240" y2="178" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a8)"/>
  <line x1="320" y1="130" x2="320" y2="178" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a8)"/>
  <line x1="530" y1="130" x2="400" y2="178" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a8)"/>
  <defs>
    <marker id="a8" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

_All three launchers build a `LaunchedClassLoader` and delegate to your `Start-Class`._

## 5. Runnable example

```java
// File: LauncherDemo.java
// How to run: java LauncherDemo.java
// Demonstrates reading MANIFEST.MF to see which launcher would be used.

import java.util.jar.Manifest;
import java.util.jar.Attributes;
import java.io.File;
import java.io.FileInputStream;
import java.util.jar.JarFile;

public class LauncherDemo {

    // Simulate choosing the correct launcher based on archive extension
    static String chooseLauncher(String archive) {
        if (archive.endsWith(".war")) {
            return "org.springframework.boot.loader.launch.WarLauncher";
        }
        // Check for loader.properties (signals PropertiesLauncher is wanted)
        if (new File("loader.properties").exists()) {
            return "org.springframework.boot.loader.launch.PropertiesLauncher";
        }
        return "org.springframework.boot.loader.launch.JarLauncher";
    }

    // Read Main-Class and Start-Class from a real Boot JAR/WAR manifest
    static void inspectManifest(String archivePath) throws Exception {
        try (JarFile jar = new JarFile(archivePath)) {
            Manifest mf = jar.getManifest();
            Attributes attrs = mf.getMainAttributes();
            System.out.println("Archive     : " + archivePath);
            System.out.println("Main-Class  : " + attrs.getValue("Main-Class"));
            System.out.println("Start-Class : " + attrs.getValue("Start-Class"));
        }
    }

    public static void main(String[] args) throws Exception {
        // Demo 1: launcher selection logic
        System.out.println("=== Launcher selection ===");
        System.out.println("app.jar -> " + chooseLauncher("app.jar"));
        System.out.println("app.war -> " + chooseLauncher("app.war"));

        // Demo 2: inspect a real Boot archive if provided
        if (args.length > 0) {
            System.out.println("\n=== Manifest inspection ===");
            inspectManifest(args[0]);
        } else {
            System.out.println("\nPass a Boot JAR/WAR path as argument to inspect its manifest.");
        }
    }
}
```

**How to run:** `java LauncherDemo.java` (shows launcher selection). With an actual Boot JAR: `java LauncherDemo.java target/myapp.jar`.

## 6. Walkthrough

1. `chooseLauncher("app.jar")` returns `JarLauncher` — the default for standard Spring Boot JARs built with the Maven plugin.
2. `chooseLauncher("app.war")` returns `WarLauncher` — WAR archives use `WEB-INF/lib/` not `BOOT-INF/lib/`, so a different launcher is needed.
3. `PropertiesLauncher` is opted into explicitly by setting `Main-Class` in the manifest manually or via plugin configuration. It reads `loader.path` from `loader.properties` to add extra directories.
4. `inspectManifest` opens a real Boot archive and prints `Main-Class` (the launcher) and `Start-Class` (your application). This is the MANIFEST layout Boot uses at runtime.

## 7. Gotchas & takeaways

> `PropertiesLauncher` is **not** the default. You must configure the Spring Boot Maven plugin to use it: `<layout>ZIP</layout>` in the plugin configuration. Without this, `JarLauncher` is always used for `.jar`.

> `WarLauncher` also runs in embedded mode — it works without a servlet container. The WAR just has a different directory layout so it can also be dropped into a traditional Tomcat/Jetty.

> In Spring Boot 3.2, the loader classes moved from `org.springframework.boot.loader` to `org.springframework.boot.loader.launch`. Scripts that hard-code the class name need updating.

- Never need to reference launchers directly in application code — they are infrastructure.
- For `PropertiesLauncher`, set `LOADER_PATH=/opt/plugins` at runtime to add JARs without rebuilding the archive.
- WAR packaging: `WarLauncher` excludes `WEB-INF/lib-provided/` from the embedded classpath (those are provided by the servlet container), but includes them when running standalone.
