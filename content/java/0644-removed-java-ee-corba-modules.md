---
card: java
gi: 644
slug: removed-java-ee-corba-modules
title: Removed Java EE & CORBA modules
---

## 1. What it is

Java 11 **removed** several long-deprecated modules from the JDK as part of the ongoing modularisation and housekeeping effort. The most significant removals are the **Java EE modules** (also known as the Jakarta EE technologies that were bundled with Java SE) and the **CORBA module**. Specifically removed: `java.xml.ws` (JAX-WS), `java.xml.bind` (JAXB), `java.activation` (JAF), `java.corba` (CORBA, including the ORB, IDL compiler, and RMI-IIOP), `java.transaction` (JTA), `java.xml.ws.annotation`, and `java.se.ee` (the aggregator module). These were deprecated in Java 9, and their removal was announced by JEP 320. Applications that depend on these technologies must now include them as separate libraries (e.g., from Maven Central) or migrate to alternative implementations.

## 2. Why & when

The Java EE technologies were originally bundled with Java SE to jump-start enterprise development, but this coupling created problems: the JDK's bundled versions lagged behind the standalone specifications, the overlap with application-server-provided implementations caused class-loading conflicts, and the maintenance burden on the JDK team was significant. CORBA, in particular, had seen almost no active development for years and was considered legacy technology. Removing these modules shrinks the JDK distribution size (~10% reduction), simplifies the module graph, and allows the technologies to evolve independently (Jakarta EE under the Eclipse Foundation). If your application uses JAXB, JAX-WS, or CORBA, you must migrate to standalone libraries during the Java 11 upgrade.

## 3. Core concept

```java
// Before Java 11 (Java 8-10): these worked out of the box
import javax.xml.bind.JAXBContext;  // built-in JAXB
import javax.xml.ws.Service;        // built-in JAX-WS
import org.omg.CORBA.ORB;           // built-in CORBA

// Java 11+: these classes are NOT in the JDK
// You must add dependencies:
//   JAXB:   javax.xml.bind:jaxb-api + org.glassfish.jaxb:jaxb-runtime
//   JAX-WS: javax.xml.ws:jaxws-api + com.sun.xml.ws:jaxws-rt
//   CORBA:  (no widely-used standalone replacement — migrate away)
//   JAF:    com.sun.activation:javax.activation

// For JAXB, the simplest fix is to add the dependency and use it the same way:
// (No code changes needed — just add the JARs)
```

The removal is a build/deployment concern, not a code concern — the APIs are the same; they just moved from the JDK into external JARs.

## 4. Diagram

<svg viewBox="0 0 560 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java 11 removes Java EE and CORBA modules from the JDK — use standalone libraries instead">
  <rect x="10" y="10" width="540" height="140" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="20" width="120" height="55" rx="4" fill="#0d1117" stroke="#f85149"/>
  <text x="80" y="40" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">Java 8–10</text>
  <text x="80" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">JDK included:</text>
  <text x="80" y="66" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">JAXB, JAX-WS</text>
  <text x="80" y="74" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">CORBA, JTA, JAF</text>

  <text x="155" y="50" fill="#8b949e" font-size="16" font-family="monospace">→</text>

  <rect x="175" y="20" width="130" height="55" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="240" y="40" fill="#3fb950" font-size="10" text-anchor="middle" font-family="monospace">Java 11+</text>
  <text x="240" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">JDK removed:</text>
  <text x="240" y="66" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">JAXB, JAX-WS</text>
  <text x="240" y="74" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">CORBA, JTA, JAF</text>

  <text x="320" y="50" fill="#8b949e" font-size="16" font-family="monospace">→</text>

  <rect x="340" y="20" width="200" height="55" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="440" y="36" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">Standalone Libraries</text>
  <text x="440" y="50" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">Maven: jaxb-api + jaxb-runtime</text>
  <text x="440" y="62" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">or: Jakarta EE 9+ (jakarta.xml.bind)</text>
  <text x="440" y="74" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">CORBA: no replacement — migrate away</text>

  <text x="20" y="105" fill="#8b949e" font-size="9" font-family="sans-serif">Removed modules (JEP 320): java.xml.ws, java.xml.bind, java.activation, java.corba, java.transaction, java.xml.ws.annotation, java.se.ee</text>
  <text x="20" y="123" fill="#f85149" font-size="9" font-family="sans-serif">Deprecated in Java 9 | Removed in Java 11 | Part of Jakarta EE under Eclipse Foundation</text>
  <text x="20" y="141" fill="#3fb950" font-size="9" font-family="sans-serif">JAXB fix: add 2 JARs (API + impl). JAX-WS fix: add 2 JARs. CORBA fix: migrate to gRPC/RSocket/RMI.</text>
</svg>

The JDK shed ~10% of its size by removing these modules. The technologies continue to exist as standalone libraries — they just moved out of the JDK distribution.

## 5. Runnable example

Scenario: demonstrating what happens when you try to use JAXB on Java 11 without adding dependencies, and how to detect and fix the issue — starting with identifying the problem, extending to the fix, and discussing migration strategies.

### Level 1 — Basic

```java
// File: RemovedModulesDemo.java
public class RemovedModulesDemo {
    public static void main(String[] args) {
        System.out.println("=== Removed Java EE & CORBA Modules ===\n");
        System.out.println("Java version: " + System.getProperty("java.version"));
        System.out.println("Java vendor:  " + System.getProperty("java.vendor"));

        System.out.println("\nModules removed in Java 11 (JEP 320):\n");

        String[] removed = {
            "java.xml.ws        — JAX-WS (SOAP web services)",
            "java.xml.bind      — JAXB (XML binding)",
            "java.activation    — JAF (JavaBeans Activation Framework)",
            "java.corba         — CORBA (Common Object Request Broker Architecture)",
            "java.transaction   — JTA (Java Transaction API)",
            "java.xml.ws.annotation — Common Annotations",
            "java.se.ee         — Aggregator module for all of the above"
        };

        for (String m : removed) {
            System.out.println("  ❌ " + m);
        }

        System.out.println("\nTry this on Java 11+ to see the error:");
        System.out.println("  import javax.xml.bind.JAXBContext;");
        System.out.println("  → Compilation error: package javax.xml.bind does not exist");

        System.out.println("\nAlso removed from the JDK (but not Java EE):");
        System.out.println("  ❌ javafx.* modules (moved to OpenJFX)");
        System.out.println("  ❌ Pack200 tools (removed in Java 14)");
        System.out.println("  ❌ Nashorn JavaScript engine (removed in Java 15, standalone: github.com/openjdk/nashorn)");
    }
}
```

**How to run:** `java RemovedModulesDemo.java`

Expected output:
```
=== Removed Java EE & CORBA Modules ===

Java version: 17.0...
Java vendor:  ...

Modules removed in Java 11 (JEP 320):

  ❌ java.xml.ws        — JAX-WS (SOAP web services)
  ❌ java.xml.bind      — JAXB (XML binding)
  ❌ java.activation    — JAF (JavaBeans Activation Framework)
  ❌ java.corba         — CORBA (Common Object Request Broker Architecture)
  ❌ java.transaction   — JTA (Java Transaction API)
  ❌ java.xml.ws.annotation — Common Annotations
  ❌ java.se.ee         — Aggregator module for all of the above

Try this on Java 11+ to see the error:
  import javax.xml.bind.JAXBContext;
  → Compilation error: package javax.xml.bind does not exist

Also removed from the JDK (but not Java EE):
  ❌ javafx.* modules (moved to OpenJFX)
  ❌ Pack200 tools (removed in Java 14)
  ❌ Nashorn JavaScript engine (removed in Java 15, standalone: github.com/openjdk/nashorn)
```

### Level 2 — Intermediate

```java
// File: MigrationHelper.java
import java.util.*;

public class MigrationHelper {
    public static void main(String[] args) {
        System.out.println("=== Migration Guide: Java 8/10 → Java 11 ===\n");

        printSection("If you use JAXB (javax.xml.bind):",
            "<dependency>",
            "  <groupId>javax.xml.bind</groupId>",
            "  <artifactId>jaxb-api</artifactId>",
            "  <version>2.3.1</version>",
            "</dependency>",
            "<dependency>",
            "  <groupId>org.glassfish.jaxb</groupId>",
            "  <artifactId>jaxb-runtime</artifactId>",
            "  <version>2.3.1</version>",
            "</dependency>",
            "",
            "NOTE: For Jakarta EE 9+, the package changes to jakarta.xml.bind",
            "      and the artifact is jakarta.xml.bind:jakarta.xml.bind-api");

        printSection("If you use JAX-WS (javax.xml.ws / javax.jws):",
            "<dependency>",
            "  <groupId>javax.xml.ws</groupId>",
            "  <artifactId>jaxws-api</artifactId>",
            "  <version>2.3.1</version>",
            "</dependency>",
            "<dependency>",
            "  <groupId>com.sun.xml.ws</groupId>",
            "  <artifactId>jaxws-rt</artifactId>",
            "  <version>2.3.1</version>",
            "</dependency>");

        printSection("If you use JAF / javax.activation:",
            "<dependency>",
            "  <groupId>com.sun.activation</groupId>",
            "  <artifactId>javax.activation</artifactId>",
            "  <version>1.2.0</version>",
            "</dependency>");

        printSection("If you use CORBA (org.omg.CORBA / javax.rmi):",
            "CORBA has NO widely-used standalone replacement.",
            "Migrate to one of:",
            "  - gRPC (modern, high-performance RPC)",
            "  - RSocket (reactive, message-based)",
            "  - REST/HTTP (widest interoperability)",
            "  - Java RMI (if you need Java-to-Java only)");

        printSection("Quick check — are you affected?",
            "Search your codebase for these imports:",
            "  grep -r 'javax.xml.bind' src/",
            "  grep -r 'javax.xml.ws' src/",
            "  grep -r 'org.omg.CORBA' src/",
            "  grep -r 'javax.activation' src/",
            "  grep -r 'javax.jws' src/",
            "If any return results, you need to migrate.");
    }

    static void printSection(String title, String... lines) {
        System.out.println(title);
        for (String line : lines) {
            System.out.println("  " + line);
        }
        System.out.println();
    }
}
```

**How to run:** `java MigrationHelper.java`

Expected output:
```
=== Migration Guide: Java 8/10 → Java 11 ===

If you use JAXB (javax.xml.bind):
  <dependency>
    <groupId>javax.xml.bind</groupId>
    ...

If you use JAX-WS (javax.xml.ws / javax.jws):
  ...

If you use JAF / javax.activation:
  ...

If you use CORBA (org.omg.CORBA / javax.rmi):
  CORBA has NO widely-used standalone replacement.
  Migrate to one of:
    - gRPC (modern, high-performance RPC)
    ...

Quick check — are you affected?
  grep -r 'javax.xml.bind' src/
  ...
```

### Level 3 — Advanced

```java
// File: RemovedModulesAdvanced.java
public class RemovedModulesAdvanced {
    public static void main(String[] args) {
        System.out.println("=== Deep Dive: Why These Modules Were Removed ===\n");

        System.out.println("1. Historical Context:");
        System.out.println("   Java SE and Java EE (now Jakarta EE) were always separate");
        System.out.println("   specifications, but the JDK bundled EE implementations for");
        System.out.println("   convenience. Over time, this caused problems:");
        System.out.println("   - JDK's bundled JAXB was version 2.x while apps needed 3.x");
        System.out.println("   - Application servers shipped their own JAXB (classpath conflicts)");
        System.out.println("   - CORBA in the JDK was essentially unmaintained since Java 6");
        System.out.println("   - The modules bloated the JDK (~10 MB of unused code for most apps)");
        System.out.println();

        System.out.println("2. The Module System Factor:");
        System.out.println("   Java 9's module system (Project Jigsaw) required every package");
        System.out.println("   to belong to exactly one module. The Java EE modules overlapped");
        System.out.println("   with the java.se module and were resolved by the 'java.se.ee'");
        System.out.println("   aggregator. Removing them simplified the module graph.");
        System.out.println();

        System.out.println("3. Impact on Popular Frameworks:");
        System.out.println("   - Spring Boot: migrated from javax.* to jakarta.* in Spring Boot 3");
        System.out.println("   - Hibernate: uses JAXB for XML config (add jaxb-api dependency)");
        System.out.println("   - Apache CXF: JAX-WS implementation (add jaxws-rt dependency)");
        System.out.println("   - Most apps: unaffected (JAXB is the most common dependency needed)");
        System.out.println();

        System.out.println("4. Detection Tools:");
        System.out.println("   - jdeps --jdk-internals: finds JDK internal API usage");
        System.out.println("   - jdeps --list-deps: lists module dependencies");
        System.out.println("   - Maven enforcer plugin: bans specific dependencies");
        System.out.println("   - IDE inspections: IntelliJ flags removed API usage");
        System.out.println();

        System.out.println("5. Future Removals (post-Java 11):");
        System.out.println("   - Java 15: removed Nashorn JS engine (standalone: OpenJFX Nashorn)");
        System.out.println("   - Java 15: removed Solaris/Sparc ports");
        System.out.println("   - Java 17: deprecated Applet API for removal");
        System.out.println("   - Java 17: deprecated Security Manager for removal");
        System.out.println("   - Java 21: deprecated 32-bit x86 port for removal");
        System.out.println();
        System.out.println("   Stay current: each LTS removes more legacy cruft.");
    }
}
```

**How to run:** `java RemovedModulesAdvanced.java`

Expected output:
```
=== Deep Dive: Why These Modules Were Removed ===

1. Historical Context:
   ...

2. The Module System Factor:
   ...

3. Impact on Popular Frameworks:
   ...

4. Detection Tools:
   ...

5. Future Removals (post-Java 11):
   ...
```

The production-flavoured hard cases: (1) **JAXB is the most common impact** — many applications use it for XML processing. The fix is adding 2 JARs. (2) **CORBA has no good replacement** — if you still use CORBA, plan a migration to gRPC or REST. (3) **Jakarta EE 9+ renamed packages** from `javax.*` to `jakarta.*` — if you're adding JAXB to a Java 11+ app, decide whether to use the legacy `javax.xml.bind` (EOL) or the modern `jakarta.xml.bind` (active). (4) **`jdeps` is your friend** — run `jdeps --jdk-internals your-app.jar` to find all usages of removed or internal APIs.

## 6. Walkthrough

Tracing what happens when an application built for Java 8 tries to use JAXB on Java 11:

1. The application imports `javax.xml.bind.JAXBContext`. On Java 8, this class is in `rt.jar` (the monolithic JDK runtime JAR). The compiler and runtime find it automatically.

2. The application is recompiled on Java 11. `javac` looks for `javax.xml.bind.JAXBContext` in the JDK module path. The `java.xml.bind` module is no longer present. Compilation fails: `package javax.xml.bind does not exist`.

3. **Fix:** The developer adds two JARs to the classpath/module path: `jaxb-api-2.3.1.jar` (the API) and `jaxb-runtime-2.3.1.jar` (GlassFish implementation). Now `javax.xml.bind.JAXBContext` is found in `jaxb-api.jar`. Compilation succeeds.

4. At runtime, the JVM loads `JAXBContext` from the application classpath (not the JDK). The JAXB implementation works identically — the API is unchanged, only its location moved.

5. No application code changes are needed (unless the application also references CORBA, which requires migration to a different technology).

## 7. Gotchas & takeaways

> Just adding the JAXB JARs is not always enough for **Java 11's module system**. If your application runs on the module path (with `--module-path`), the JAXB JARs need to be proper modules or you need `--add-modules java.xml.bind` even though the module was removed — the flag tells the JVM to look on the classpath. Most applications run on the classpath, where this isn't an issue.

- The removed modules are **gone from the JDK** in Java 11, not just deprecated. Code that uses them will not compile or run without adding external dependencies.
- **JAXB** is the most commonly missed dependency. If your application does any XML processing (parsing config files, SOAP, XML data binding), add `jaxb-api` + `jaxb-runtime`.
- **CORBA** has no community-supported standalone replacement. If your application uses CORBA (check for `org.omg.*` imports), plan a migration to gRPC, RSocket, or REST before upgrading to Java 11.
- The removal follows the **Jakarta EE transition**: Java EE was donated to the Eclipse Foundation, renamed to Jakarta EE, and the `javax.*` packages are being renamed to `jakarta.*`. Java 11's removal is part of this larger industry shift.
- Use `jdeps --jdk-internals your-app.jar` to detect all dependencies on removed or internal JDK APIs. It's the official migration tool.
