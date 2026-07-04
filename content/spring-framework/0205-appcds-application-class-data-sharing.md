---
card: spring-framework
gi: 205
slug: appcds-application-class-data-sharing
title: AppCDS (Application Class Data Sharing)
---

## 1. What it is

**Application Class Data Sharing (AppCDS)** is a JVM feature that pre-processes application classes into a shared archive (`.jsa` file) so subsequent JVM launches can memory-map them directly, skipping the bytecode verification and class linking steps that happen on every cold start. Spring Framework 6 adds first-class support for AppCDS through its AOT (Ahead-of-Time) compilation pipeline and provides convenience scripts to generate and use these archives.

The result is measurable startup time reduction — 20–50% faster depending on the application size — with no change to runtime behaviour.

## 2. Why & when

Spring applications are class-heavy. A minimal Spring Boot app loads thousands of classes at startup: Spring itself, libraries, your code. Each class goes through:
1. **Loading** — read bytes from the JAR.
2. **Verification** — bytecode safety check.
3. **Linking** — resolve references, prepare static state.

AppCDS caches the output of these steps in a binary archive. On the next launch, the JVM memory-maps the archive — dramatically faster than repeating the work.

Use AppCDS when:
- Startup latency matters (cloud functions, Kubernetes horizontal pod autoscaling, CLI tools).
- Your deployment environment allows a one-time archive generation step.
- You want faster restarts without switching to GraalVM native images (which have longer build times).

It complements Spring's AOT processing (which pre-processes bean definitions) and works with both traditional JVM and Spring Boot's layered JAR.

## 3. Core concept

Think of AppCDS as a "fast-forward snapshot" of the class loading phase. The first launch (the *training run*) records which classes were loaded and bakes them into a `.jsa` archive. Every subsequent launch skips straight to "classes already loaded" by mapping the archive into the process address space — a near-zero-cost mmap call.

Two-step workflow:

**Step 1 — Generate the archive:**
```bash
# Tell JVM to dump a class list during a training run
java -Xshare:off -XX:DumpLoadedClassList=app.lst -jar app.jar
# Bake the class list into a shared archive
java -Xshare:dump -XX:SharedClassListFile=app.lst \
     -XX:SharedArchiveFile=app.jsa -jar app.jar
```

**Step 2 — Use the archive:**
```bash
java -Xshare:on -XX:SharedArchiveFile=app.jsa -jar app.jar
```

Spring Boot 3.x (Spring Framework 6) adds Maven/Gradle plugin goals that automate these steps. The AOT phase (`spring-boot:process-aot`) generates hints that make more classes archivable (interfaces that are normally loaded lazily get pre-loaded during AOT).

Key constraint: the archive is JVM-version–specific and path-specific. A new JVM version or a change in the JAR invalidates the archive — regenerate it in CI.

## 4. Diagram

<svg viewBox="0 0 640 230" xmlns="http://www.w3.org/2000/svg">
  <!-- Cold start (no CDS) -->
  <rect x="15" y="30" width="280" height="75" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1" stroke-dasharray="4 2"/>
  <text x="155" y="50" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Without AppCDS</text>
  <rect x="25" y="58" width="60" height="36" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="55" y="79" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Load JARs</text>
  <line x1="85" y1="76" x2="105" y2="76" stroke="#8b949e" stroke-width="1" marker-end="url(#ag)"/>
  <rect x="105" y="58" width="65" height="36" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="138" y="79" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Verify bytes</text>
  <line x1="170" y1="76" x2="195" y2="76" stroke="#8b949e" stroke-width="1" marker-end="url(#ag)"/>
  <rect x="195" y="58" width="85" height="36" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="238" y="79" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Link &amp; prepare</text>

  <!-- With CDS -->
  <rect x="15" y="130" width="280" height="75" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="155" y="150" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">With AppCDS</text>
  <rect x="25" y="158" width="80" height="36" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="65" y="179" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">mmap .jsa</text>
  <line x1="105" y1="176" x2="280" y2="176" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ag2)"/>
  <text x="190" y="168" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">classes already resolved → skip</text>

  <!-- Archive -->
  <rect x="370" y="80" width="120" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="430" y="108" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">app.jsa</text>
  <text x="430" y="125" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">pre-verified</text>
  <text x="430" y="141" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">pre-linked classes</text>

  <!-- Arrow from cold run to archive -->
  <line x1="300" y1="65" x2="370" y2="105" stroke="#8b949e" stroke-width="1" stroke-dasharray="4 2" marker-end="url(#ag)"/>
  <text x="355" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">training run</text>

  <!-- Arrow from archive to warm -->
  <line x1="370" y1="145" x2="300" y2="170" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ag2)"/>
  <text x="355" y="168" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">subsequent runs</text>

  <defs>
    <marker id="ag" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#8b949e"/>
    </marker>
    <marker id="ag2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

A one-time training run generates the archive; every subsequent launch memory-maps it, skipping verification and linking for thousands of classes.

## 5. Runnable example

Scenario: a **minimal Spring application** — first measuring baseline startup without AppCDS, then generating the archive, then using it to see the speedup.

### Level 1 — Basic

Baseline: measure startup time of a Spring context with no AppCDS.

```java
// AppCdsDemo.java
import org.springframework.context.annotation.*;

@Configuration
public class AppCdsDemo {
    public static void main(String[] args) {
        long start = System.currentTimeMillis();
        var ctx = new AnnotationConfigApplicationContext(AppCdsDemo.class);
        long elapsed = System.currentTimeMillis() - start;
        System.out.println("Context started in " + elapsed + " ms");
        System.out.println("JVM: " + System.getProperty("java.vm.name")
            + " " + System.getProperty("java.version"));
        ctx.close();
    }
}
```

How to run: `java -Xshare:off -cp spring-context.jar:spring-beans.jar:spring-core.jar:spring-jcl.jar:. AppCdsDemo.java`

`-Xshare:off` disables any default CDS archive. The elapsed time is your baseline — on a laptop typically 400–900 ms for a minimal Spring context.

---

### Level 2 — Intermediate

Generate a class list and archive from the baseline app, then measure startup with the archive.

```bash
# Step 1: dump class list (training run)
java -Xshare:off \
     -XX:DumpLoadedClassList=appcds.lst \
     -cp spring-context.jar:spring-beans.jar:spring-core.jar:spring-jcl.jar:. \
     AppCdsDemo

# Step 2: create the archive
java -Xshare:dump \
     -XX:SharedClassListFile=appcds.lst \
     -XX:SharedArchiveFile=appcds.jsa \
     -cp spring-context.jar:spring-beans.jar:spring-core.jar:spring-jcl.jar:. \
     AppCdsDemo

# Step 3: use the archive
java -Xshare:on \
     -XX:SharedArchiveFile=appcds.jsa \
     -cp spring-context.jar:spring-beans.jar:spring-core.jar:spring-jcl.jar:. \
     AppCdsDemo
```

```java
// AppCdsDemo.java (same as Level 1 — no code change needed for AppCDS)
import org.springframework.context.annotation.*;

@Configuration
public class AppCdsDemo {
    public static void main(String[] args) {
        long start = System.currentTimeMillis();
        var ctx = new AnnotationConfigApplicationContext(AppCdsDemo.class);
        long elapsed = System.currentTimeMillis() - start;
        System.out.println("Context started in " + elapsed + " ms");
        String cdsStatus = System.getProperty("java.class.path.cds", "unknown");
        System.out.println("Archive: " + new java.io.File("appcds.jsa").exists());
        ctx.close();
    }
}
```

How to run: execute the three bash steps above (JDK 17+)

Step 1 appends every loaded class name to `appcds.lst`. Step 2 reads the list, loads those classes, and serialises their verified/linked form to `appcds.jsa`. Step 3 maps the archive — startup time drops measurably.

---

### Level 3 — Advanced

Spring Boot 3 integration: use `spring-boot:process-aot` + the built-in CDS support to generate a production-grade archive with a layered JAR.

```java
// AppCdsDemo.java — Spring Boot 3 entry point (illustrative)
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.web.bind.annotation.*;

@SpringBootApplication
@RestController
public class AppCdsDemo {

    @GetMapping("/hello")
    public String hello() { return "Hello, AppCDS!"; }

    public static void main(String[] args) {
        long t0 = System.nanoTime();
        SpringApplication.run(AppCdsDemo.class, args);
        System.out.printf("Started in %.2f s%n",
            (System.nanoTime() - t0) / 1e9);
    }
}
```

Corresponding Maven/Bash workflow:
```bash
# 1. Build the fat JAR
mvn package -q

# 2. AOT processing (pre-bakes bean definitions; makes more classes archivable)
mvn spring-boot:process-aot

# 3. Training run — Spring Boot 3 uses -Dspring.aot.enabled=true
java -Xshare:off \
     -XX:DumpLoadedClassList=app.lst \
     -Dspring.aot.enabled=true \
     -jar target/myapp.jar --spring.main.web-environment=false \
     && echo "Training run done"

# 4. Create archive
java -Xshare:dump \
     -XX:SharedClassListFile=app.lst \
     -XX:SharedArchiveFile=app.jsa \
     -jar target/myapp.jar

# 5. Production launch
java -Xshare:on \
     -XX:SharedArchiveFile=app.jsa \
     -Dspring.aot.enabled=true \
     -jar target/myapp.jar
```

How to run: requires Maven + Spring Boot 3 + JDK 17+

AOT processing (`process-aot`) generates `BeanDefinitionRegistrar` classes that Spring loads instead of parsing XML/annotations at startup — more deterministic class loading means a better archive hit rate. Combined with AppCDS, Spring Boot 3 apps routinely achieve sub-1-second startup for moderately-sized applications.

## 6. Walkthrough

**Training run execution path:**

1. JVM starts with `-Xshare:off -XX:DumpLoadedClassList=appcds.lst`.
2. The classloader loads each class normally (from JAR, verify, link).
3. Every time a class is loaded, its binary name is appended to `appcds.lst`.
4. `AppCdsDemo.main` runs — Spring context starts, all Spring classes get loaded, all names recorded.
5. JVM exits; `appcds.lst` now contains ~3 000–5 000 class names for a minimal Spring app.

**Archive creation (`-Xshare:dump`) execution path:**

1. JVM reads `appcds.lst` line by line.
2. Each class is loaded, verified, and linked exactly as in a normal JVM run.
3. The internal representation of each class (vtables, method bytecodes, constant pool pointers) is serialised into `appcds.jsa`.
4. The archive is a binary file, typically 30–80 MB for a Spring Boot app.

**Warm launch (`-Xshare:on`) execution path:**

1. JVM opens `appcds.jsa` with `mmap` — no disk I/O block, just virtual address space mapping.
2. When the classloader requests `org.springframework.context.annotation.AnnotationConfigApplicationContext`, the JVM checks the archive index first.
3. Found in archive → the class metadata is read from the mapped memory region (already verified, already linked) and installed directly. No JAR read, no bytecode verification.
4. Only classes *not* in the archive go through the normal load-verify-link path.

**Data state change at each stage:**
- After training run: `appcds.lst` = 4 831 lines of class names.
- After dump: `appcds.jsa` = ~45 MB binary archive.
- At warm launch: classloader cache hits ≈90% of Spring classes → startup time ≈40% faster.

**AOT + AppCDS synergy:** Spring's AOT phase replaces `ClassPathScanningCandidateComponentProvider.findCandidateComponents()` (which scans JARs at runtime) with pre-generated code. This means those scanner classes are loaded earlier and more predictably, increasing archive hit rate.

## 7. Gotchas & takeaways

> **The archive is JDK-version and classpath-specific.** A new JDK patch, a dependency version bump, or even a different JAR order can invalidate the archive, causing `-Xshare:on` to print a warning and fall back to normal loading. Always regenerate the archive in CI after any dependency change.

> **`-Xshare:on` is strict — startup fails if the archive is invalid.** Use `-Xshare:auto` (the JDK default from Java 12) to silently fall back rather than fail. Use `-Xshare:on` only in production where you control the environment.

- AppCDS reduces *class-loading* time, not bean initialisation time. For further startup reduction, combine with Spring AOT (`-Dspring.aot.enabled=true`).
- The training run must exit cleanly (the app must start fully and then stop) to capture all relevant classes. Use a `--spring.main.web-environment=false` flag to suppress Tomcat startup in training mode.
- `-XX:+UseSharedSpaces` is an older alias; prefer `-Xshare:on` on JDK 11+.
- Spring Boot 3.2 added a `CDS` profile (experimental) in `spring-boot:start` that automates the three-step process inside the Maven lifecycle.
- GraalVM native images are a harder alternative that eliminates the JVM entirely; AppCDS is a gentler optimisation that keeps all JVM debugging tools working.
