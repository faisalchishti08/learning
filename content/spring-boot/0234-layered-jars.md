---
card: spring-boot
gi: 234
slug: layered-jars
title: Layered JARs
---

## 1. What it is

A layered JAR is a Spring Boot executable JAR where the contents are split into ordered layers — typically `dependencies`, `spring-boot-loader`, `snapshot-dependencies`, and `application`. Each layer corresponds to a Docker image layer. Because dependencies rarely change but application code changes constantly, layered JARs dramatically reduce the amount of data pushed to a container registry on each build.

## 2. Why & when

Without layering, every code change triggers a full re-upload of the entire fat JAR (often 50-200 MB). With layering, only the `application` layer (a few KB of your class files) is pushed on most builds — the `dependencies` layer is already cached by the registry and the build nodes. This accelerates CI and saves bandwidth.

## 3. Core concept

The Spring Boot Maven and Gradle plugins produce a layered JAR by default (since Boot 2.4). Inside `BOOT-INF/layers.idx` you find a list of layers in order from least likely to change (bottom of image) to most likely (top):

```
- "dependencies":
  - "BOOT-INF/lib/"
- "spring-boot-loader":
  - "org/"
- "snapshot-dependencies":
  - "BOOT-INF/lib/*SNAPSHOT*"
- "application":
  - "BOOT-INF/classes/"
  - "BOOT-INF/classpath.idx"
  - "BOOT-INF/layers.idx"
  - "META-INF/"
```

Each layer is extracted into a separate directory and added as its own `COPY` instruction in the Dockerfile. Docker caches layers independently — only changed layers are rebuilt and pushed.

## 4. Diagram

<svg viewBox="0 0 620 300" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="620" height="300" fill="#1c2430" rx="10"/>
  <!-- FAT JAR side -->
  <rect x="20" y="40" width="170" height="220" rx="8" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="105" y="68" text-anchor="middle" fill="#8b949e">Fat JAR (no layers)</text>
  <rect x="35" y="80" width="140" height="160" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="105" y="165" text-anchor="middle" fill="#8b949e" font-size="12">single blob</text>
  <text x="105" y="185" text-anchor="middle" fill="#8b949e" font-size="11">~150 MB pushed</text>
  <text x="105" y="203" text-anchor="middle" fill="#8b949e" font-size="11">on every build</text>
  <!-- Layered JAR side -->
  <rect x="240" y="40" width="360" height="220" rx="8" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="420" y="68" text-anchor="middle" fill="#6db33f">Layered JAR → Docker image layers</text>
  <rect x="255" y="80" width="330" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="420" y="103" text-anchor="middle" fill="#8b949e" font-size="12">Layer 1: dependencies (rarely changes) ✓ cached</text>
  <rect x="255" y="122" width="330" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="420" y="145" text-anchor="middle" fill="#8b949e" font-size="12">Layer 2: spring-boot-loader (stable)     ✓ cached</text>
  <rect x="255" y="164" width="330" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="420" y="187" text-anchor="middle" fill="#8b949e" font-size="12">Layer 3: snapshot-deps (changes sometimes)</text>
  <rect x="255" y="206" width="330" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="420" y="225" text-anchor="middle" fill="#6db33f" font-size="12">Layer 4: application  ← only this is rebuilt</text>
  <text x="420" y="241" text-anchor="middle" fill="#8b949e" font-size="11">~100 KB pushed per build</text>
  <defs/>
</svg>

_Layering splits a fat JAR by change frequency so Docker only pushes the `application` layer on most builds._

## 5. Runnable example

```java
// File: InspectLayeredJar.java
// How to run: java InspectLayeredJar.java <path-to-boot-jar>
// Build a Spring Boot project first: ./mvnw package
// Then: java InspectLayeredJar.java target/myapp.jar

import java.util.jar.JarFile;
import java.util.jar.JarEntry;
import java.util.Enumeration;
import java.io.BufferedReader;
import java.io.InputStreamReader;

public class InspectLayeredJar {
    public static void main(String[] args) throws Exception {
        if (args.length == 0) {
            System.out.println("Usage: java InspectLayeredJar.java <boot-jar>");
            return;
        }
        try (JarFile jar = new JarFile(args[0])) {
            // Print layers.idx to show layer definitions
            JarEntry layersIdx = jar.getJarEntry("BOOT-INF/layers.idx");
            if (layersIdx == null) {
                System.out.println("No BOOT-INF/layers.idx found — JAR may not be layered.");
                return;
            }
            System.out.println("=== BOOT-INF/layers.idx ===");
            try (BufferedReader br =
                    new BufferedReader(new InputStreamReader(jar.getInputStream(layersIdx)))) {
                br.lines().forEach(System.out::println);
            }
            // Count entries per layer bucket
            System.out.println("\n=== Entry counts ===");
            long deps = 0, app = 0, loader = 0;
            Enumeration<JarEntry> entries = jar.entries();
            while (entries.hasMoreElements()) {
                String name = entries.nextElement().getName();
                if (name.startsWith("BOOT-INF/lib/")) deps++;
                else if (name.startsWith("BOOT-INF/classes/")) app++;
                else if (name.startsWith("org/springframework/boot/loader/")) loader++;
            }
            System.out.printf("dependencies (BOOT-INF/lib/)  : %d JARs%n", deps);
            System.out.printf("application  (BOOT-INF/classes/): %d entries%n", app);
            System.out.printf("loader       (org/...loader/)  : %d entries%n", loader);
        }
    }
}
```

**How to run:** Build any Spring Boot project then `java InspectLayeredJar.java target/myapp.jar`.

## 6. Walkthrough

1. `jar.getJarEntry("BOOT-INF/layers.idx")` — opens the layer index file present in all Boot 2.4+ JARs.
2. Printing `layers.idx` shows the layer names and which path patterns belong to each layer — exactly what the Dockerfile `extractLayersInto` tool reads.
3. The entry count loop confirms the distribution: `BOOT-INF/lib/` contains dozens of dependency JARs, while `BOOT-INF/classes/` holds only your app's compiled files.
4. The loader entries (`org/springframework/boot/loader/`) are minimal — Boot loader classes are stable across patch releases.

## 7. Gotchas & takeaways

> Layered JARs are the default in Spring Boot 2.4+. You do not need to enable them. To disable: `<layers><enabled>false</enabled></layers>` in the plugin config.

> Layering only benefits Docker builds. Running `java -jar myapp.jar` directly is unaffected — the layers index is ignored at runtime.

> Custom layer order matters: place the slowest-changing layer first (bottom of the Docker image) and the fastest-changing last (top). The default order is almost always correct.

- The `layertools` jar mode (`java -Djarmode=layertools -jar myapp.jar extract`) extracts each layer into a directory for use in a multi-stage Dockerfile.
- Check `layers.idx` if a dependency unexpectedly lands in `snapshot-dependencies` — any `*SNAPSHOT*` version triggers that layer.
- Layered JARs work with `spring-boot:build-image` (Buildpacks) too — Paketo buildpacks use the layer index automatically.
