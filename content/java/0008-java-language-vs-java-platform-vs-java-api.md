---
card: java
gi: 8
slug: java-language-vs-java-platform-vs-java-api
title: Java language vs Java platform vs Java API
---

## 1. What it is

"Java" is used to mean at least three different things, and conflating them causes real confusion:

- **Java language** — the syntax, type system, and semantics you write in `.java` files: classes, interfaces, generics, lambdas, records. Defined by the *Java Language Specification (JLS)*.
- **Java platform** — the runtime environment that executes programs: the JVM, the class loader, the JIT, the garbage collector, the security system. Defined by the *Java Virtual Machine Specification (JVMS)*.
- **Java API** — the standard library: the collection of classes and interfaces (`java.lang`, `java.util`, `java.io`, etc.) that Java programs can call. Documented in the Javadoc at docs.oracle.com.

These three evolved independently and at different rates. The language got lambdas in Java 8; the JVM got Loom (virtual threads) in Java 21; the API got `Stream`, `Optional`, and `CompletableFuture` at their own cadences.

## 2. Why & when

The distinction matters in practice:

- **Language vs API:** Kotlin compiles to JVM bytecode and runs on the Java platform, using the Java API — but it is not the Java language. Scala, Groovy, Clojure, and JRuby all work the same way.
- **Platform vs language:** GraalVM can compile Python and Ruby to run on the JVM (Truffle). The platform is bigger than the language.
- **Language vs API:** You can use `var` (Java 10 language feature) with any API class. The language feature and the API it works with are independent.
- **Deprecation:** `javax.xml.bind.JAXB` was removed from the Java API in Java 11; that's an API change, not a language change.
- **Licensing:** Oracle's JDK license governs a *distribution*; the Java language spec and JVMS are open standards. OpenJDK provides the open-source implementation of the platform.

## 3. Core concept

Analogy: the Java language is like English grammar rules; the Java platform is the library building where you work; the Java API is the catalogue of books on the shelves.

You can follow different grammar rules (Kotlin syntax) in the same building (JVM), using the same catalogue (Java API). You can also follow Java grammar but stand in a different building (GraalVM native image, which has a different execution model).

```
┌─────────────────────────────────────────────┐
│           Java Platform (JVM + GC + JIT)    │
│  ┌──────────────────────────────────────┐   │
│  │          Java API                    │   │
│  │  java.lang · java.util · java.io     │   │
│  │  java.net · java.math · java.sql     │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  Languages that run on the JVM:             │
│   Java  Kotlin  Scala  Groovy  Clojure      │
└─────────────────────────────────────────────┘
```

The **Java Language Specification** defines what valid Java syntax is and what it means — it says nothing about the JVM or the API.

The **JVMS** defines the bytecode instruction set, class file format, verification, and execution model — it says nothing about Java syntax.

The **Java SE API specification** (Javadoc) defines each class and method contract — it relies on both the language (Java generics) and the platform (`Object.hashCode` contract), but is independently versioned.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three-way Venn diagram: Java language, platform, and API with overlaps">
  <!-- Platform (large) -->
  <ellipse cx="280" cy="120" rx="240" ry="90" fill="none" stroke="#6db33f" stroke-width="2"/>
  <text x="100" y="70" fill="#6db33f" font-size="11" font-family="sans-serif">Java Platform</text>
  <text x="100" y="84" fill="#8b949e" font-size="9"  font-family="sans-serif">(JVM · GC · JIT)</text>

  <!-- API (mid) -->
  <ellipse cx="310" cy="130" rx="170" ry="66" fill="#1c2430" stroke="#79c0ff" stroke-width="1.8"/>
  <text x="190" y="98" fill="#79c0ff" font-size="10" font-family="sans-serif">Java API</text>
  <text x="190" y="111" fill="#8b949e" font-size="8"  font-family="sans-serif">(java.* classes)</text>

  <!-- Language (right, partially overlapping) -->
  <ellipse cx="460" cy="118" rx="180" ry="72" fill="none" stroke="#f0883e" stroke-width="2" stroke-dasharray="4,3"/>
  <text x="552" y="70" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">Java Language</text>
  <text x="552" y="83" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">(syntax · JLS)</text>

  <!-- JVM-only languages label -->
  <text x="95"  y="140" fill="#8b949e" font-size="9" font-family="sans-serif">Kotlin · Scala</text>
  <text x="95"  y="153" fill="#8b949e" font-size="9" font-family="sans-serif">Groovy · Clojure</text>

  <!-- Java core intersection label -->
  <text x="285" y="125" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">javac</text>
  <text x="285" y="139" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">compiles language</text>
  <text x="285" y="151" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">to use API on platform</text>

  <!-- Language-only features -->
  <text x="590" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">syntax sugar</text>
  <text x="590" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(var, records)</text>
</svg>

The platform is the largest container; the API sits within it; the language overlaps with both but is independently specified.

## 5. Runnable example

Scenario: a program that prints version info for each of the three layers separately, demonstrating that they can differ.

### Level 1 — Basic

```java
// ThreeLayers.java
public class ThreeLayers {
    public static void main(String[] args) {
        // Java API: what version of the standard library is this?
        System.out.println("=== Java API ===");
        System.out.println("  java.lang.String class: " + String.class.getName());
        System.out.println("  java.util.List class  : " + java.util.List.class.getName());

        // Java Platform: what JVM is executing us?
        System.out.println("\n=== Java Platform (JVM) ===");
        System.out.println("  JVM name   : " + System.getProperty("java.vm.name"));
        System.out.println("  JVM version: " + System.getProperty("java.vm.version"));
        System.out.println("  OS         : " + System.getProperty("os.name"));

        // Java Language: what bytecode version were we compiled to?
        System.out.println("\n=== Java Language (compiler output) ===");
        System.out.println("  class version: " + System.getProperty("java.class.version"));
        System.out.println("  spec version : " + System.getProperty("java.specification.version"));
    }
}
```

**How to run:** `java ThreeLayers.java`

`java.specification.version` is the Java SE spec version (e.g. `"21"`), while `java.vm.version` is the specific JVM build. They can differ when a JVM backports features.

### Level 2 — Intermediate

Same three-layer probe extended to show that **other JVM languages** (simulated here) produce valid bytecode the same platform runs.

```java
// ThreeLayersProbe.java
import java.util.*;
import java.lang.module.*;

public class ThreeLayersProbe {
    // Language feature: record (Java 16+), var (Java 10+)
    record LayerInfo(String layer, String key, String value) {}

    public static void main(String[] args) {
        // Collect info for each layer
        var info = new ArrayList<LayerInfo>();

        // Language layer evidence: record + var compile fine here
        info.add(new LayerInfo("Language",  "spec version",   System.getProperty("java.specification.version")));
        info.add(new LayerInfo("Language",  "class version",  System.getProperty("java.class.version")));
        info.add(new LayerInfo("Language",  "source feature", "records, var, lambdas, sealed classes"));

        // Platform layer
        info.add(new LayerInfo("Platform",  "JVM name",       System.getProperty("java.vm.name")));
        info.add(new LayerInfo("Platform",  "JVM version",    System.getProperty("java.vm.version")));
        info.add(new LayerInfo("Platform",  "GC",             detectGC()));

        // API layer
        info.add(new LayerInfo("API",       "java.base ver",  System.getProperty("java.version")));
        info.add(new LayerInfo("API",       "modules loaded", String.valueOf(ModuleLayer.boot().modules().size())));
        info.add(new LayerInfo("API",       "String methods", String.valueOf(String.class.getMethods().length)));

        // Print table
        System.out.printf("%-10s  %-22s  %s%n", "Layer", "Key", "Value");
        System.out.println("-".repeat(72));
        info.forEach(r -> System.out.printf("%-10s  %-22s  %s%n", r.layer(), r.key(), r.value()));

        System.out.println("\nKey insight: Kotlin/Scala produce bytecode the same Platform runs, using the same API.");
    }

    static String detectGC() {
        return java.lang.management.ManagementFactory.getGarbageCollectorMXBeans()
            .stream().map(gc -> gc.getName()).reduce((a,b) -> a + ", " + b).orElse("unknown");
    }
}
```

**How to run:** `java ThreeLayersProbe.java`

The `record` keyword (language) compiles to a class using standard API classes (`Object`, `String`) running on the JVM (platform). All three are independently versioned but cooperate.

### Level 3 — Advanced

Same scenario grown to dynamically load a class compiled with a different `--release` target, demonstrating that the platform is backward-compatible with older API versions — a key Java guarantee.

```java
// ApiVsLanguageVsPlatform.java
import java.util.*;
import java.lang.management.*;
import java.lang.module.*;
import java.io.*;
import java.nio.file.*;

public class ApiVsLanguageVsPlatform {

    public static void main(String[] args) throws Exception {
        System.out.println("════════════════════════════════════════════════");
        System.out.println("  Java Language vs Platform vs API — Live Audit");
        System.out.println("════════════════════════════════════════════════\n");

        // ── Language ─────────────────────────────────────────────
        System.out.println("[ Java Language ]");
        System.out.println("  Spec  : JLS " + System.getProperty("java.specification.version"));
        System.out.println("  Class : bytecode " + System.getProperty("java.class.version"));
        // Language features used in THIS file:
        System.out.println("  Features used here: record, var, lambdas, text blocks");
        var textBlock = """
            (text block: a Java 15 language feature)
            """.strip();
        System.out.println("  " + textBlock);

        // ── Platform ──────────────────────────────────────────────
        System.out.println("\n[ Java Platform (JVM) ]");
        System.out.println("  JVM   : " + System.getProperty("java.vm.name"));
        System.out.println("  Build : " + System.getProperty("java.vm.version"));
        // Virtual thread support (Java 21+)
        boolean hasVirtualThreads = Runtime.version().feature() >= 21;
        System.out.println("  Virtual threads (Loom) available: " + hasVirtualThreads);
        if (hasVirtualThreads) {
            Thread vt = Thread.ofVirtual().start(() -> System.out.println("  ↳ hello from virtual thread!"));
            vt.join();
        }
        // GC info
        ManagementFactory.getGarbageCollectorMXBeans()
            .forEach(gc -> System.out.printf("  GC: %-30s  collections=%d%n", gc.getName(), gc.getCollectionCount()));

        // ── API ───────────────────────────────────────────────────
        System.out.println("\n[ Java API ]");
        System.out.println("  Version : " + System.getProperty("java.version"));
        long bootModules = ModuleLayer.boot().modules().size();
        System.out.println("  Boot layer modules : " + bootModules);
        // API can be trimmed with jlink — show what's available
        boolean hasSql    = ModuleLayer.boot().findModule("java.sql").isPresent();
        boolean hasDesktop= ModuleLayer.boot().findModule("java.desktop").isPresent();
        System.out.println("  java.sql available    : " + hasSql);
        System.out.println("  java.desktop available: " + hasDesktop);

        // ── Distinction proof ─────────────────────────────────────
        System.out.println("\n[ Distinction: compile --release 11, run on Java 21 ]");
        // Compile a tiny class targeting Java 11 bytecode (API class: java.util.List)
        Path tmpDir = Files.createTempDirectory("javadist");
        Path src = tmpDir.resolve("OldClass.java");
        Files.writeString(src, "public class OldClass { public String greet() { return java.util.List.of(\"a\",\"b\").toString(); } }");
        Process p = new ProcessBuilder("javac", "--release", "11", src.toString())
            .redirectErrorStream(true).start();
        String out = new String(p.getInputStream().readAllBytes());
        p.waitFor();
        if (out.isBlank()) {
            // Load and invoke
            var cl = new java.net.URLClassLoader(new java.net.URL[]{tmpDir.toUri().toURL()});
            Class<?> cls = cl.loadClass("OldClass");
            Object instance = cls.getDeclaredConstructor().newInstance();
            String result = (String) cls.getMethod("greet").invoke(instance);
            System.out.println("  Java 11-compiled class ran on Java " + Runtime.version().feature() + ": " + result);
            cl.close();
        } else {
            System.out.println("  Compile note: " + out.strip());
        }
        Files.delete(src);
        try { Files.delete(tmpDir.resolve("OldClass.class")); } catch(Exception ignore) {}
        Files.delete(tmpDir);
    }
}
```

**How to run:** `java ApiVsLanguageVsPlatform.java`

The `--release 11` compilation targets Java 11 API + bytecode, but runs on the current JVM. This is the backward-compatibility guarantee of the platform — independent of the language version used to write `ApiVsLanguageVsPlatform.java` itself.

## 6. Walkthrough

Execution proceeds through three labeled blocks:

**Language block:**
- `System.getProperty("java.specification.version")` returns the JLS version (`"21"`). This is the language spec, not the JVM spec.
- The `var` keyword and text block are compiled away at compile time — they are pure language sugar that produces standard bytecode. By runtime, there is no `var` or text-block in the bytecode; both are erased by `javac`.
- `record` compiles to a standard class with auto-generated methods. The platform sees an ordinary class with `ACC_RECORD` flag in the class file.

**Platform block:**
- `Thread.ofVirtual().start(...)` is a **platform** feature (Project Loom, Java 21). It requires the JVM to support virtual thread scheduling. This is independent of which language you wrote the code in — Kotlin on Java 21 gets virtual threads too.
- `GarbageCollectorMXBeans` lists the GC algorithms active in *this JVM instance*. GC choice (`-XX:+UseZGC` etc.) is a **platform** configuration, invisible to the Java language or API.

**API block:**
- `ModuleLayer.boot().findModule("java.sql")` checks whether `java.sql` (part of the Java SE API) is present. With `jlink` you can strip it out — the platform still runs, the language still works, but that slice of the API is gone.
- The `--release 11` compilation in the distinction block proves that the platform is backward-compatible: code compiled targeting Java 11's API and bytecode runs on Java 21 without recompilation. The language version of `ApiVsLanguageVsPlatform.java` (Java 21 features) and the API version of `OldClass.java` (Java 11 API) are completely independent.

Data state transformations:
```
Source (.java) → javac (language spec) → bytecode (.class)
                                               │
                              JVM classloader (platform) loads it
                                               │
                         JIT compiles hot methods to native (platform)
                                               │
                    method calls → java.util.List.of() (API)
                                               │
                                         return value
```

## 7. Gotchas & takeaways

> **"Java removed feature X"** almost always means the API changed, not the language. `javax.xml.bind` (JAXB) was removed from the Java SE API in Java 11; you add the `jakarta.xml.bind` dependency instead. The language itself is highly stable and very rarely breaks.

> **`--release` vs `--source`/`--target`**: `--release N` sets language version, API version, AND bytecode version atomically. `--source N --target N` only sets bytecode version and may let you accidentally call APIs unavailable in Java N. Always use `--release` for cross-version compatibility.

- Java language = JLS-governed syntax. Versions: 8 (lambdas), 10 (var), 14 (records preview), 16 (records stable), 17 (sealed), 21 (pattern matching).
- Java platform = JVM + GC + JIT + security. Versions: 8 (G1 default), 9 (modules), 21 (virtual threads).
- Java API = standard library. Versions: 8 (Streams/Optional), 11 (String.isBlank), 14 (Records in API), 21 (SequencedCollections).
- Other JVM languages (Kotlin, Scala, Groovy) use the platform and API without using the Java language.
- `jlink` lets you trim the API layer; the platform still runs.
- Use `Runtime.version().feature()` (not string parsing) to query the API/platform version at runtime.
