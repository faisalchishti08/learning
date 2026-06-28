---
card: spring-boot
gi: 232
slug: executable-jars-the-nested-jar-format-loader
title: Executable JARs (the nested JAR format / Loader)
---

## 1. What it is

A Spring Boot executable JAR ("fat JAR" or "über JAR") bundles your application classes, resources, and all dependency JARs inside a single archive. Unlike a standard Java JAR, Spring Boot's format nests whole dependency JARs — not exploded class files — inside `BOOT-INF/lib/`. A custom class loader (`JarLauncher`) unpacks and runs them at startup.

## 2. Why & when

The standard Java class loader cannot load classes from JARs nested inside another JAR. Spring Boot's loader solves this with a custom URL handler, enabling one-file deploys: `java -jar myapp.jar` and you're done. No server installation, no classpath wrangling. Every Spring Boot project benefits from this by default.

## 3. Core concept

Inside a Spring Boot JAR the layout is:

```
myapp.jar
├── META-INF/MANIFEST.MF           ← Main-Class: org.springframework.boot.loader.launch.JarLauncher
├── BOOT-INF/
│   ├── classes/                   ← your compiled .class files & resources
│   └── lib/                       ← dependency JARs (nested, not exploded)
└── org/springframework/boot/loader/ ← Boot's own loader classes (always exploded)
```

`JarLauncher` is the entry point declared in `MANIFEST.MF`. It:
1. Reads nested JARs from `BOOT-INF/lib/`.
2. Creates a `LaunchedClassLoader` backed by custom URL handlers for `jar:nested:/…` URLs.
3. Delegates to your application's `Main-Class` (stored as `Start-Class` in the manifest).

## 4. Diagram

<svg viewBox="0 0 620 300" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="620" height="300" fill="#1c2430" rx="10"/>
  <!-- JAR outline -->
  <rect x="30" y="30" width="260" height="240" rx="8" fill="#2d3748" stroke="#79c0ff" stroke-width="2"/>
  <text x="160" y="58" text-anchor="middle" fill="#79c0ff">myapp.jar</text>
  <!-- Sections -->
  <rect x="45" y="68" width="230" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="89" text-anchor="middle" fill="#8b949e" font-size="12">META-INF/MANIFEST.MF</text>
  <rect x="45" y="106" width="230" height="70" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="128" text-anchor="middle" fill="#6db33f" font-size="12">BOOT-INF/classes/</text>
  <text x="160" y="148" text-anchor="middle" fill="#8b949e" font-size="11">your .class files</text>
  <text x="160" y="165" text-anchor="middle" fill="#8b949e" font-size="11">& resources</text>
  <rect x="45" y="184" width="230" height="70" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="206" text-anchor="middle" fill="#6db33f" font-size="12">BOOT-INF/lib/</text>
  <text x="160" y="226" text-anchor="middle" fill="#8b949e" font-size="11">spring-core.jar</text>
  <text x="160" y="244" text-anchor="middle" fill="#8b949e" font-size="11">jackson-databind.jar …</text>
  <!-- Loader -->
  <rect x="340" y="80" width="250" height="70" rx="8" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="465" y="108" text-anchor="middle" fill="#6db33f">JarLauncher</text>
  <text x="465" y="128" text-anchor="middle" fill="#8b949e" font-size="11">LaunchedClassLoader</text>
  <text x="465" y="146" text-anchor="middle" fill="#8b949e" font-size="11">jar:nested:// URL handler</text>
  <!-- App -->
  <rect x="340" y="190" width="250" height="60" rx="8" fill="#2d3748" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="465" y="215" text-anchor="middle" fill="#79c0ff">Your Application</text>
  <text x="465" y="235" text-anchor="middle" fill="#8b949e" font-size="11">Start-Class in MANIFEST.MF</text>
  <!-- arrows -->
  <line x1="295" y1="150" x2="338" y2="120" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a7)"/>
  <line x1="465" y1="150" x2="465" y2="188" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a7)"/>
  <text x="390" y="168" text-anchor="middle" fill="#8b949e" font-size="11">loads nested JARs</text>
  <defs>
    <marker id="a7" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

_`JarLauncher` is the real entry point; it loads nested JARs and then delegates to your `Main-Class`._

## 5. Runnable example

```java
// File: InspectBootJar.java
// How to run: java InspectBootJar.java <path-to-your-app.jar>
// On JDK 17+: java InspectBootJar.java myapp.jar

import java.util.jar.JarFile;
import java.util.jar.Manifest;
import java.util.jar.Attributes;
import java.util.Enumeration;
import java.util.jar.JarEntry;

public class InspectBootJar {
    public static void main(String[] args) throws Exception {
        if (args.length == 0) {
            System.out.println("Usage: java InspectBootJar.java <path-to-boot-jar>");
            return;
        }
        String jarPath = args[0];
        try (JarFile jar = new JarFile(jarPath)) {
            // 1. Print manifest entries
            Manifest mf = jar.getManifest();
            Attributes attrs = mf.getMainAttributes();
            System.out.println("=== MANIFEST.MF ===");
            System.out.println("Main-Class : " + attrs.getValue("Main-Class"));
            System.out.println("Start-Class: " + attrs.getValue("Start-Class"));

            // 2. Count nested JARs in BOOT-INF/lib/
            long nestedJars = 0;
            Enumeration<JarEntry> entries = jar.entries();
            while (entries.hasMoreElements()) {
                JarEntry e = entries.nextElement();
                if (e.getName().startsWith("BOOT-INF/lib/") && e.getName().endsWith(".jar"))
                    nestedJars++;
            }
            System.out.println("\n=== Structure ===");
            System.out.printf("Nested dependency JARs in BOOT-INF/lib/: %d%n", nestedJars);
            System.out.println("Run with: java -jar " + jarPath);
        }
    }
}
```

**How to run:** Build any Spring Boot project (`./mvnw package`), then:
`java InspectBootJar.java target/myapp.jar`

## 6. Walkthrough

1. `new JarFile(jarPath)` — standard Java API to open the outer JAR.
2. `mf.getMainAttributes().getValue("Main-Class")` — should print `org.springframework.boot.loader.launch.JarLauncher` (Boot 3.2+) or `...JarLauncher` on earlier versions.
3. `getValue("Start-Class")` — your application's actual main class (e.g., `com.example.DemoApplication`).
4. The loop counts entries starting with `BOOT-INF/lib/` ending in `.jar` — these are intact nested JARs, not exploded classes.
5. At runtime, `JarLauncher.main()` is invoked, which sets up `LaunchedClassLoader` with custom URL handlers for `jar:nested:/…` and then calls `DemoApplication.main()`.

## 7. Gotchas & takeaways

> Do NOT unzip and re-zip a Spring Boot JAR with standard tools. The nested JAR format requires specific entry ordering and index files; repackaging breaks `JarLauncher`.

> The loader classes live at the root of the JAR (not inside `BOOT-INF/`) because the standard JVM class loader must be able to find `JarLauncher` before the custom loader takes over.

- `./mvnw spring-boot:repackage` or `./mvnw package` (with the Spring Boot Maven Plugin) creates the executable JAR automatically.
- Original (thin) JAR is renamed to `myapp.jar.original`; the fat JAR replaces `myapp.jar`.
- Executable JARs are not suitable for inclusion as a dependency in another project — use the `.original` artifact for that.
- Spring Boot 3.2+ changed the loader package to `org.springframework.boot.loader.launch` — update `Main-Class` references if you have custom scripts.
