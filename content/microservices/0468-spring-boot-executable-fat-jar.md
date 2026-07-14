---
card: microservices
gi: 468
slug: spring-boot-executable-fat-jar
title: "Spring Boot executable fat JAR"
---

## 1. What it is

A **Spring Boot executable fat JAR** (also called an "uber JAR") is a single `.jar` file that bundles an application's own compiled classes **together with every one of its dependency libraries**, plus an embedded application server (Tomcat, by default) and a manifest that makes the whole thing directly runnable with `java -jar app.jar` — no separate classpath setup, no external application server installation, no dependency JARs to manage by hand.

## 2. Why & when

You build a fat JAR whenever you want a microservice to be deployable as one self-contained unit, which for containerized microservices is essentially always:

- **A microservice needs to run anywhere without external setup.** A fat JAR needs only a JVM — no pre-installed application server, no manually assembled classpath of a dozen dependency JARs sitting in the right directories.
- **Container images want a single artifact to `COPY` in.** A `Dockerfile` for a Spring Boot service typically does little more than copy one fat JAR and set the run command — the JAR itself is the entire deployable unit.
- **Deployment simplicity beats disk-space efficiency for most services.** Each service's fat JAR duplicates its own copy of shared libraries (like the Spring framework itself) rather than relying on a shared, externally-managed classpath — a tradeoff that's worth it for the operational simplicity of one file per service.
- **You want it as the default packaging for essentially any standalone Spring Boot microservice** — it's what `spring-boot-maven-plugin` or `spring-boot-gradle-plugin` produces automatically when you run a standard build.

## 3. Core concept

Think of a fat JAR as a fully-stocked toolbox you hand someone, versus a set of individual tools scattered across different shelves that they'd have to gather themselves before starting work. With the fat JAR, everything needed to actually run — your code, every library it depends on, even the "workbench" (the embedded server) — travels together in one package; nothing needs to be assembled or located separately at the destination.

Concretely, a fat JAR's internal structure is:

1. **Your application's own compiled classes**, nested inside a `BOOT-INF/classes/` directory within the JAR (not at the JAR's root, which is a deliberate structural choice covered further below).
2. **Every dependency JAR your application needs**, nested whole, unextracted, inside `BOOT-INF/lib/` — Spring itself, your JSON library, your database driver, all bundled as complete JAR files within the outer JAR.
3. **A manifest (`META-INF/MANIFEST.MF`) declaring a special launcher class** as the JAR's entry point — not your own `main` class directly, but Spring Boot's `JarLauncher`, whose job is to set up a classloader that can find classes nested inside `BOOT-INF/lib/`'s inner JARs (something the JVM's default classloading can't do on its own).
4. **`JarLauncher` locates and invokes your actual application's `main` method** once its special classloader is ready, at which point your Spring Boot application starts exactly as if it had been launched normally.

## 4. Diagram

<svg viewBox="0 0 620 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A fat JAR's internal structure: a manifest pointing to JarLauncher, application classes under BOOT-INF/classes, and dependency JARs under BOOT-INF/lib">
  <rect x="20" y="20" width="580" height="200" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">app.jar</text>

  <rect x="40" y="55" width="250" height="40" rx="6" fill="#141a22" stroke="#79c0ff"/>
  <text x="165" y="79" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">META-INF/MANIFEST.MF -&gt; JarLauncher</text>

  <rect x="40" y="105" width="250" height="45" rx="6" fill="#141a22" stroke="#f0883e"/>
  <text x="165" y="123" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">BOOT-INF/classes/</text>
  <text x="165" y="140" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">your compiled .class files</text>

  <rect x="40" y="160" width="540" height="45" rx="6" fill="#141a22" stroke="#f0883e"/>
  <text x="310" y="178" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">BOOT-INF/lib/</text>
  <text x="310" y="195" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">spring-core.jar, jackson.jar, postgres-driver.jar, ...(whole, nested JARs)</text>
</svg>

The manifest points at `JarLauncher`, which sets up a classloader able to read classes directly out of nested JARs under `BOOT-INF/lib/`, then launches your real `main` method.

## 5. Runnable example

Spring Boot's actual fat-JAR packaging is done by its Maven/Gradle plugin, not something you'd hand-roll — but the *mechanics* it relies on (a manifest-declared entry point, and nested JARs needing a special classloader) are plain JVM concepts we can demonstrate directly. We start by building and running a normal, thin JAR with a manifest entry point, extend it to a version bundling a dependency, then handle the hard case a fat JAR's launcher actually solves: reading a class out of a JAR nested inside another JAR, which the JVM's default classloader cannot do.

### Level 1 — Basic

```java
// File: BuildThinJar.java -- builds a NORMAL, thin, single-purpose JAR
// with a manifest Main-Class entry, then demonstrates running it with
// `java -jar`. This models the manifest-driven entry point mechanism a
// fat JAR also relies on, before adding any bundled dependencies.
import java.io.*;
import java.nio.file.*;
import java.util.jar.*;
import java.util.zip.*;

public class BuildThinJar {
    public static void main(String[] args) throws Exception {
        Path workDir = Files.createTempDirectory("thinjar-demo");

        // 1. Write a tiny application class as source, then compile it.
        Path appSource = workDir.resolve("HelloApp.java");
        Files.writeString(appSource, """
            public class HelloApp {
                public static void main(String[] args) {
                    System.out.println("[HelloApp] running from inside a JAR, launched via manifest Main-Class");
                }
            }
            """);
        runProcess(workDir, "javac", "HelloApp.java");

        // 2. Package the compiled class into a JAR with a manifest Main-Class entry.
        Path jarPath = workDir.resolve("thin-app.jar");
        Manifest manifest = new Manifest();
        manifest.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
        manifest.getMainAttributes().put(Attributes.Name.MAIN_CLASS, "HelloApp");
        try (JarOutputStream jos = new JarOutputStream(new FileOutputStream(jarPath.toFile()), manifest)) {
            addFileToJar(jos, workDir.resolve("HelloApp.class"), "HelloApp.class");
        }
        System.out.println("[build] produced " + jarPath);

        // 3. Run it exactly like a deployed fat JAR would be run.
        runProcess(workDir, "java", "-jar", jarPath.toString());
    }

    static void addFileToJar(JarOutputStream jos, Path file, String entryName) throws IOException {
        jos.putNextEntry(new ZipEntry(entryName));
        jos.write(Files.readAllBytes(file));
        jos.closeEntry();
    }

    static void runProcess(Path dir, String... command) throws Exception {
        Process p = new ProcessBuilder(command).directory(dir.toFile()).inheritIO().start();
        p.waitFor();
    }
}
```

How to run: `java BuildThinJar.java`

This uses `javac` and `java -jar` as subprocesses to actually build and run a real JAR on disk, so what you see is genuine JVM behavior, not a simulation. `MAIN_CLASS` in the manifest is exactly the mechanism `JarLauncher` sits behind in a real fat JAR — the JVM reads that manifest attribute to know which class's `main` method to invoke when you run `java -jar`.

### Level 2 — Intermediate

```java
// File: BuildJarWithNestedDependency.java -- the SAME manifest-driven JAR,
// now with a DEPENDENCY bundled inside it as a NESTED JAR under a lib/
// directory -- mirroring BOOT-INF/lib/, though using the JVM's PLAIN
// classpath mechanism (extracting nested JARs onto the classpath) rather
// than Spring Boot's real custom classloader, which Level 3 addresses.
import java.io.*;
import java.nio.file.*;
import java.util.jar.*;
import java.util.zip.*;

public class BuildJarWithNestedDependency {
    public static void main(String[] args) throws Exception {
        Path workDir = Files.createTempDirectory("nested-demo");

        // 1. Build a small "dependency" JAR, standing in for a library like Jackson.
        Path depSource = workDir.resolve("Greeter.java");
        Files.writeString(depSource, """
            public class Greeter {
                public static String greet() { return "Hello from the bundled dependency!"; }
            }
            """);
        runProcess(workDir, "javac", "Greeter.java");
        Path depJar = workDir.resolve("greeter-lib.jar");
        try (JarOutputStream jos = new JarOutputStream(new FileOutputStream(depJar.toFile()))) {
            addFileToJar(jos, workDir.resolve("Greeter.class"), "Greeter.class");
        }
        System.out.println("[build] produced dependency " + depJar);

        // 2. Build the app class that USES the dependency (compiled against depJar on the classpath).
        Path appSource = workDir.resolve("AppUsingDep.java");
        Files.writeString(appSource, """
            public class AppUsingDep {
                public static void main(String[] args) {
                    System.out.println(Greeter.greet());
                }
            }
            """);
        runProcess(workDir, "javac", "-cp", depJar.toString(), "AppUsingDep.java");

        // 3. Run the app class DIRECTLY on the classpath, alongside the dependency JAR --
        //    this is how a THIN jar plus separate dependency JARs would normally run,
        //    which is exactly the manual classpath assembly a fat JAR exists to avoid.
        runProcess(workDir, "java", "-cp", depJar + File.pathSeparator + workDir, "AppUsingDep");
    }

    static void addFileToJar(JarOutputStream jos, Path file, String entryName) throws IOException {
        jos.putNextEntry(new ZipEntry(entryName));
        jos.write(Files.readAllBytes(file));
        jos.closeEntry();
    }

    static void runProcess(Path dir, String... command) throws Exception {
        Process p = new ProcessBuilder(command).directory(dir.toFile()).inheritIO().start();
        p.waitFor();
    }
}
```

How to run: `java BuildJarWithNestedDependency.java`

`AppUsingDep` is compiled against `depJar` on the classpath and calls `Greeter.greet()`. The final run step passes both `depJar` and the app's own class directory on `-cp`, explicitly listing every piece — this is exactly the manual classpath assembly that becomes unmanageable once a real application has dozens of dependencies, which is the practical problem a fat JAR's single `java -jar app.jar` invocation solves.

### Level 3 — Advanced

```java
// File: NestedJarClassloadingProblem.java -- demonstrates the SPECIFIC,
// PRODUCTION-FLAVORED hard case that JarLauncher exists to solve: a
// dependency JAR bundled truly INSIDE another JAR's bytes (not sitting
// next to it on disk, as in Level 2, but embedded as a nested ZIP entry --
// what BOOT-INF/lib/ actually looks like). The JVM's default classloader
// CANNOT load classes directly out of a JAR nested inside another JAR --
// this program proves that limitation, then shows the technique
// (extracting the nested JAR to a temp location first) that a custom
// classloader like JarLauncher's uses to work around it.
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.jar.*;
import java.util.zip.*;

public class NestedJarClassloadingProblem {
    public static void main(String[] args) throws Exception {
        Path workDir = Files.createTempDirectory("nested-jar-in-jar");

        // 1. Build the inner dependency JAR (like a library under BOOT-INF/lib/).
        Path depSource = workDir.resolve("InnerLib.java");
        Files.writeString(depSource, """
            public class InnerLib {
                public static String message() { return "loaded from a JAR nested inside another JAR"; }
            }
            """);
        runProcess(workDir, "javac", "InnerLib.java");
        Path innerJarPath = workDir.resolve("inner-lib.jar");
        try (JarOutputStream jos = new JarOutputStream(new FileOutputStream(innerJarPath.toFile()))) {
            addFileToJar(jos, workDir.resolve("InnerLib.class"), "InnerLib.class");
        }

        // 2. Build the OUTER jar, embedding the inner JAR under a lib/ path -- like BOOT-INF/lib/.
        Path outerJarPath = workDir.resolve("outer-fat.jar");
        try (JarOutputStream jos = new JarOutputStream(new FileOutputStream(outerJarPath.toFile()))) {
            addFileToJar(jos, innerJarPath, "BOOT-INF/lib/inner-lib.jar");
        }
        System.out.println("[build] outer JAR now contains a NESTED jar at BOOT-INF/lib/inner-lib.jar");

        // 3. PROVE the default JVM classloader cannot reach into the nested jar directly.
        try (URLClassLoader naiveLoader = new URLClassLoader(new URL[]{outerJarPath.toUri().toURL()})) {
            naiveLoader.loadClass("InnerLib");
            System.out.println("[naive] unexpectedly succeeded");
        } catch (ClassNotFoundException e) {
            System.out.println("[naive] FAILED as expected: default classloader cannot see into a nested jar -- " + e.getMessage());
        }

        // 4. The technique a custom launcher (JarLauncher, conceptually) actually uses:
        //    read the nested jar's BYTES out of the outer jar and extract it somewhere
        //    loadable, THEN point a classloader at that extracted location.
        Path extractedInnerJar = workDir.resolve("extracted-inner-lib.jar");
        try (JarFile outerJar = new JarFile(outerJarPath.toFile())) {
            JarEntry nestedEntry = outerJar.getJarEntry("BOOT-INF/lib/inner-lib.jar");
            try (InputStream in = outerJar.getInputStream(nestedEntry)) {
                Files.copy(in, extractedInnerJar, StandardCopyOption.REPLACE_EXISTING);
            }
        }
        try (URLClassLoader launcherStyleLoader = new URLClassLoader(new URL[]{extractedInnerJar.toUri().toURL()})) {
            Class<?> innerLibClass = launcherStyleLoader.loadClass("InnerLib");
            Object result = innerLibClass.getMethod("message").invoke(null);
            System.out.println("[launcher-style] SUCCESS: " + result);
        }
    }

    static void addFileToJar(JarOutputStream jos, Path file, String entryName) throws IOException {
        jos.putNextEntry(new ZipEntry(entryName));
        jos.write(Files.readAllBytes(file));
        jos.closeEntry();
    }

    static void runProcess(Path dir, String... command) throws Exception {
        Process p = new ProcessBuilder(command).directory(dir.toFile()).inheritIO().start();
        p.waitFor();
    }
}
```

How to run: `java NestedJarClassloadingProblem.java`

Step 3's `URLClassLoader` pointed straight at `outer-fat.jar` fails to find `InnerLib` — a plain `URLClassLoader` can index a JAR's own entries but cannot recurse into a JAR-within-a-JAR, which is precisely why Spring Boot ships a custom `JarLauncher`/`LaunchedURLClassLoader` rather than relying on the JVM's default classpath handling. Step 4 shows the workaround conceptually: read the nested entry's raw bytes back out via `JarFile.getInputStream`, materialize them at an extractable location, and only then point a classloader at it — which is close to (a simplified version of) what Spring Boot's real launcher does at startup, in memory, for every JAR under `BOOT-INF/lib/`.

## 6. Walkthrough

Trace `NestedJarClassloadingProblem.main` in order. **First**, `InnerLib` is compiled and packaged into `inner-lib.jar`, a normal standalone JAR at this point.

**Next**, `outer-fat.jar` is built, embedding `inner-lib.jar`'s entire bytes as a single nested entry at the path `BOOT-INF/lib/inner-lib.jar` — from the outer JAR's own perspective, that nested JAR is just an opaque blob of bytes at one ZIP entry, no different from an image or a text file as far as the ZIP format is concerned.

**Then**, the "naive" attempt constructs a `URLClassLoader` pointed at `outer-fat.jar` and calls `loadClass("InnerLib")`. `URLClassLoader` knows how to look inside one JAR for `.class` files at top-level (or namespaced) paths, but it has no logic to detect that one of that JAR's entries is itself a JAR containing more classes — the lookup fails and `ClassNotFoundException` is thrown, caught, and reported.

**After that**, the "launcher-style" workaround runs: `JarFile.getJarEntry` locates the nested entry by its exact path, `getInputStream` reads its raw bytes, and `Files.copy` writes those bytes out to `extracted-inner-lib.jar` on disk — now a real, independent, loadable JAR file again, no longer trapped inside the outer JAR's ZIP structure.

**Finally**, a fresh `URLClassLoader` is pointed at that *extracted* JAR, and `loadClass("InnerLib")` succeeds this time, because the classloader is now looking at a genuine top-level JAR rather than bytes nested inside another one. Invoking `InnerLib.message()` via reflection confirms the class is fully usable, proving the extraction step is what actually bridges the gap the naive attempt couldn't cross.

```
[build] outer JAR now contains a NESTED jar at BOOT-INF/lib/inner-lib.jar
[naive] FAILED as expected: default classloader cannot see into a nested jar -- InnerLib
[launcher-style] SUCCESS: loaded from a JAR nested inside another JAR
```

## 7. Gotchas & takeaways

> Trying to run a fat JAR's contents with a plain `java -cp` pointed at the outer JAR, expecting the JVM to somehow reach into `BOOT-INF/lib/`'s nested JARs on its own, will fail exactly like the naive attempt above — this is not a bug, it's the JVM's default classloader working as designed, and it's precisely why `JarLauncher` exists as a real, necessary piece of machinery rather than a formality.
- `BOOT-INF/classes/` and `BOOT-INF/lib/` (rather than putting your classes at the JAR's root) is a deliberate structural choice — it keeps your application's own classes cleanly separated from bundled dependencies, and gives `JarLauncher`'s classloader clear, distinct locations to set up.
- Spring Boot's real `JarLauncher` does this extraction-and-classloading dance in memory at startup, far more efficiently than writing files to disk one at a time — this example trades some of that efficiency for clarity.
- The fat JAR tradeoff is disk space and per-service duplication versus deployment simplicity — for containerized microservices, where each service already ships as its own image, that tradeoff is almost always worth it.
- [Layered JARs](0469-spring-boot-layered-jars-for-efficient-images.md) address the resulting container-image-layer inefficiency of a monolithic fat JAR, without giving up the executable-JAR model described here.
- You can inspect any real Spring Boot fat JAR's structure yourself with a plain unzip tool (`unzip -l app.jar`) — seeing `BOOT-INF/classes/` and `BOOT-INF/lib/` directly makes this whole mechanism concrete rather than abstract.
