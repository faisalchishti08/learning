---
card: spring-boot
gi: 18
slug: creating-an-executable-fat-uber-jar
title: Creating an executable (fat/uber) JAR
---

## 1. What it is

An **executable fat JAR** (also called an uber JAR or self-contained JAR) is a single `.jar` file that contains:
- Your compiled application class files.
- All dependency JARs embedded inside it (`BOOT-INF/lib/`).
- The embedded web server (e.g., Tomcat 10.1 JARs).
- Spring Boot's custom class loader (`org.springframework.boot.loader`) that knows how to load classes from nested JARs.

You run it with a single command: `java -jar app.jar`. No separate Tomcat, no classpath setup, no external dependencies — the JAR is the entire application.

Standard Maven/Gradle produce "thin" JARs containing only your classes. The `spring-boot-maven-plugin` or `spring-boot-gradle-plugin` repackages this thin JAR into a fat JAR by embedding all dependencies into the archive.

## 2. Why & when

**Before fat JARs**, deploying a Java web app meant:
1. Install Java on the server.
2. Install Tomcat (specific version) on the server.
3. Configure Tomcat (`server.xml`, `context.xml`).
4. Upload your WAR file to the `webapps/` directory.
5. Restart Tomcat.

**With fat JARs**:
1. Install Java on the server.
2. `scp app.jar server:` and `java -jar app.jar`.

The fat JAR is the right output for:
- **Docker containers** — `COPY app.jar .` and `CMD ["java","-jar","app.jar"]` — a Dockerfile that fits in two meaningful lines.
- **Kubernetes** — one pod, one JAR, no shared state with other deployments.
- **CI/CD pipelines** — the artifact is a single versioned file; deploy the same JAR to dev, staging, and prod.
- **Cloud platforms** (AWS Elastic Beanstalk, Azure App Service, GCP App Engine) — they natively accept Spring Boot fat JARs.

## 3. Core concept

The build sequence:

```
Maven (mvn package) or Gradle (./gradlew bootJar)
  │
  ├─ 1. Compile your source → thin JAR (your classes only)
  │
  └─ 2. spring-boot-maven/gradle-plugin repackages:
         ├─ BOOT-INF/classes/        ← your compiled classes
         ├─ BOOT-INF/lib/            ← ALL dependency JARs (including Tomcat)
         ├─ META-INF/MANIFEST.MF     ← Main-Class: JarLauncher, Start-Class: YourApp
         └─ org/springframework/boot/loader/  ← Spring Boot's class loader
```

**`JarLauncher`** is the real `Main-Class` in the fat JAR's `MANIFEST.MF`. When you run `java -jar app.jar`, the JVM invokes `JarLauncher.main`, which sets up a custom class loader capable of loading classes from the nested JARs inside `BOOT-INF/lib/`, then delegates to your `@SpringBootApplication` class (listed as `Start-Class`).

**Fat JAR size:** Expect 40–80 MB for a typical Spring Boot app with web + JPA starters. Most of the size is Tomcat and Hibernate JARs. This is acceptable for server-side deployment; for serverless or GraalVM native images, there are size-reduction strategies.

**Layered JARs:** Spring Boot 2.3+ introduced layered JARs for optimised Docker builds. The fat JAR's content is split into layers (dependencies, spring-boot-loader, snapshot-dependencies, application), so Docker can cache unchanged layers.

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Fat JAR structure showing BOOT-INF/classes, BOOT-INF/lib with embedded Tomcat, and Spring Boot loader">
  <!-- Fat JAR outer box -->
  <rect x="200" y="20" width="260" height="220" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="44" fill="#6db33f" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">app.jar (fat JAR)</text>
  <text x="330" y="60" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">~50–80 MB · java -jar app.jar</text>

  <!-- MANIFEST.MF -->
  <rect x="216" y="68" width="228" height="32" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="330" y="82" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">META-INF/MANIFEST.MF</text>
  <text x="330" y="94" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Main-Class: JarLauncher · Start-Class: App</text>

  <!-- JarLauncher -->
  <rect x="216" y="108" width="228" height="28" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="330" y="127" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">org/springframework/boot/loader/JarLauncher</text>

  <!-- BOOT-INF/classes -->
  <rect x="216" y="144" width="228" height="28" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="330" y="163" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">BOOT-INF/classes/ — your app classes</text>

  <!-- BOOT-INF/lib -->
  <rect x="216" y="180" width="228" height="48" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="330" y="198" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">BOOT-INF/lib/</text>
  <text x="330" y="214" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">tomcat-embed-core.jar · spring-webmvc.jar</text>
  <text x="330" y="226" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">jackson-databind.jar · hibernate-core.jar …</text>

  <!-- java -jar label -->
  <line x1="60" y1="130" x2="196" y2="130" stroke="#6db33f" stroke-width="2" marker-end="url(#fatArr)"/>
  <text x="40" y="114" fill="#e6edf3" font-size="11" font-family="sans-serif">java -jar</text>
  <text x="40" y="128" fill="#e6edf3" font-size="11" font-family="sans-serif">app.jar</text>

  <!-- Output label -->
  <line x1="464" y1="130" x2="520" y2="130" stroke="#6db33f" stroke-width="2" marker-end="url(#fatArr2)"/>
  <rect x="520" y="112" width="120" height="36" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="580" y="130" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Running app</text>
  <text x="580" y="143" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">:8080 ready</text>

  <defs>
    <marker id="fatArr"  markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="fatArr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

`java -jar app.jar` → JarLauncher sets up a nested-JAR class loader → your `@SpringBootApplication` main class runs.

## 5. Runnable example

```java
// File: FatJarStructureDemo.java
// Shows fat JAR MANIFEST.MF structure and simulates JarLauncher delegation.
// Run: java FatJarStructureDemo.java

import java.util.*;
import java.util.jar.*;
import java.io.*;

public class FatJarStructureDemo {

    // Simulates the MANIFEST.MF inside a Spring Boot fat JAR
    static Manifest buildFatJarManifest(String appMainClass) {
        var manifest = new Manifest();
        var attrs = manifest.getMainAttributes();
        attrs.put(Attributes.Name.MANIFEST_VERSION, "1.0");
        // The JVM sees JarLauncher as the entry point
        attrs.put(Attributes.Name.MAIN_CLASS, "org.springframework.boot.loader.JarLauncher");
        // Spring Boot reads this to know YOUR main class
        attrs.putValue("Start-Class", appMainClass);
        attrs.putValue("Spring-Boot-Version", "3.3.4");
        attrs.putValue("Spring-Boot-Classes", "BOOT-INF/classes/");
        attrs.putValue("Spring-Boot-Lib", "BOOT-INF/lib/");
        return manifest;
    }

    // Simulates JarLauncher: reads Start-Class and delegates
    static void simulateJarLauncher(Manifest manifest) {
        var attrs = manifest.getMainAttributes();
        String mainClass = attrs.getValue("Main-Class");
        String startClass = attrs.getValue("Start-Class");
        String classesDir = attrs.getValue("Spring-Boot-Classes");
        String libDir     = attrs.getValue("Spring-Boot-Lib");

        System.out.println("java -jar app.jar");
        System.out.println();
        System.out.println("JVM reads MANIFEST.MF:");
        System.out.println("  Main-Class  = " + mainClass);
        System.out.println("  Start-Class = " + startClass);
        System.out.println();
        System.out.println("JarLauncher starts:");
        System.out.println("  1. Creates nested-JAR class loader");
        System.out.println("     loading classes from: " + classesDir);
        System.out.println("     loading JARs from:    " + libDir);
        System.out.println("  2. Delegates to Start-Class: " + startClass + ".main(args)");
        System.out.println("  → SpringApplication.run() → Tomcat starts → :8080 ready");
    }

    public static void main(String[] args) throws Exception {
        var manifest = buildFatJarManifest("com.example.demo.DemoApplication");
        simulateJarLauncher(manifest);

        System.out.println();
        System.out.println("=== Fat JAR structure (abbreviated) ===");
        List.of(
            "META-INF/MANIFEST.MF",
            "org/springframework/boot/loader/JarLauncher.class",
            "BOOT-INF/classes/com/example/demo/DemoApplication.class",
            "BOOT-INF/lib/spring-webmvc-6.1.12.jar",
            "BOOT-INF/lib/tomcat-embed-core-10.1.28.jar",
            "BOOT-INF/lib/jackson-databind-2.17.2.jar",
            "BOOT-INF/lib/hibernate-core-6.5.2.Final.jar"
        ).forEach(e -> System.out.println("  " + e));
        System.out.println("  ... (~50 more dependency JARs)");
    }
}
```

**How to run:** `java FatJarStructureDemo.java` (JDK 17+, no dependencies needed).

Expected output:
```
java -jar app.jar

JVM reads MANIFEST.MF:
  Main-Class  = org.springframework.boot.loader.JarLauncher
  Start-Class = com.example.demo.DemoApplication

JarLauncher starts:
  1. Creates nested-JAR class loader
     loading classes from: BOOT-INF/classes/
     loading JARs from:    BOOT-INF/lib/
  2. Delegates to Start-Class: com.example.demo.DemoApplication.main(args)
  → SpringApplication.run() → Tomcat starts → :8080 ready

=== Fat JAR structure (abbreviated) ===
  META-INF/MANIFEST.MF
  org/springframework/boot/loader/JarLauncher.class
  BOOT-INF/classes/com/example/demo/DemoApplication.class
  BOOT-INF/lib/spring-webmvc-6.1.12.jar
  BOOT-INF/lib/tomcat-embed-core-10.1.28.jar
  BOOT-INF/lib/jackson-databind-2.17.2.jar
  BOOT-INF/lib/hibernate-core-6.5.2.Final.jar
  ... (~50 more dependency JARs)
```

## 6. Walkthrough

- **`Manifest` and `Attributes`** — Java's built-in `java.util.jar.Manifest` models the `META-INF/MANIFEST.MF` file. The `spring-boot-maven-plugin` writes this manifest when repackaging; we build it manually for demonstration.
- **`Main-Class` = `JarLauncher`** — the JVM invokes this when `java -jar` is used. Standard Java doesn't know how to load classes from JARs nested inside a JAR; `JarLauncher` provides that ability.
- **`Start-Class`** — a Spring Boot-specific manifest attribute that records your `@SpringBootApplication` main class. `JarLauncher` reads it and calls `.main(args)` on it via reflection after setting up the class loader.
- **`BOOT-INF/classes/`** and **`BOOT-INF/lib/`** — the convention Spring Boot uses inside the fat JAR. `JarLauncher` knows to look here; if you crack open a fat JAR (`jar tf app.jar`), you'll see exactly this structure.
- **`~50 more dependency JARs`** — a real Spring Boot web + JPA app has 50–100 dependency JARs. All embedded. This is why the JAR is 40–80 MB.

## 7. Gotchas & takeaways

> **`jar tf app.jar` inspects a fat JAR without extracting it.** If `java -jar app.jar` fails with `ClassNotFoundException`, run `jar tf app.jar | grep ClassName` to verify the class is in `BOOT-INF/classes` or the right JAR is in `BOOT-INF/lib`.

> **Don't add fat JAR dependencies to `<dependencies>` in multi-module projects.** If module A produces a fat JAR and module B tries to use A as a dependency, Maven sees the fat JAR, and `JarLauncher` is loaded instead of your classes. Add `<classifier>plain</classifier>` to the dependency or exclude repackaging in A's plugin config: `<configuration><skip>true</skip></configuration>`.

- Build with `./mvnw package` (Maven) or `./gradlew bootJar` (Gradle); output is in `target/` or `build/libs/`.
- Run with `java -jar target/app-0.0.1-SNAPSHOT.jar` — everything needed is inside.
- `jar tf app.jar` lists the fat JAR contents; `jar xf app.jar META-INF/MANIFEST.MF` extracts just the manifest.
- Pass JVM flags: `java -Xmx512m -jar app.jar`.
- For Docker, the Spring Boot Gradle plugin's `bootBuildImage` or Maven's `spring-boot:build-image` creates an OCI image using Buildpacks — no Dockerfile needed.
