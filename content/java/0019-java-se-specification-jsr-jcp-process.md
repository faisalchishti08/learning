---
card: java
gi: 19
slug: java-se-specification-jsr-jcp-process
title: Java SE specification (JSR) & JCP process
---

## 1. What it is

The **Java Community Process (JCP)** is the formal mechanism by which Java specifications are developed and maintained. A **JSR (Java Specification Request)** is a formal document describing a proposed addition or change to the Java platform. Every major Java SE feature — from generics (JSR 14) to lambda expressions (JSR 335) to records — passed through the JCP before becoming part of the language.

The JCP produces three artifacts:
1. **The Specification** — a document defining the feature's behaviour precisely.
2. **The Reference Implementation (RI)** — a working implementation proving the spec is implementable.
3. **The Technology Compatibility Kit (TCK)** — a test suite that any implementation must pass to claim compliance.

OpenJDK is the reference implementation for Java SE specifications.

## 2. Why & when

The JCP exists because Java is a standard, not just Oracle's product. Multiple vendors (Amazon, IBM, Red Hat, SAP, Microsoft, Azul) need to implement Java and guarantee compatibility. The JCP's open process — with a committee that includes these vendors and community members — ensures that:
- No single vendor can unilaterally change Java SE in a way that breaks other implementations.
- Features are reviewed by experts from multiple organisations before being committed forever.
- The TCK provides an objective pass/fail test for compatibility claims.

Understanding the JCP matters when:
- You follow Java evolution via JEPs (which feed into JSRs) and want to understand the governance.
- You need to understand why a feature took multiple releases (the JCP review takes time).
- You read the Java Language Specification (JLS) or JVM Specification (JVMS) to understand precise language semantics.
- You evaluate third-party JDK distributions and want to know if they're spec-compliant.

## 3. Core concept

The JCP has two main tracks:

**JCP Executive Committee (EC):** A committee of vendors and community representatives that votes on JSR approval and maintenance. Oracle holds significant influence but cannot unilaterally pass JSRs; a majority vote is needed.

**JCP Process (simplified):**
```
Initiation  → draft JSR submitted
Review      → EC votes to accept
Development → specification + RI + TCK developed (Expert Group)
Public Draft → community feedback period
Final Draft  → EC votes to approve
Final Release→ specification published; TCK available
Maintenance  → errata, compatibility updates
```

Since Java 9 (2017), the JCP process has been partially supplemented by the **OpenJDK JEP (JDK Enhancement Proposal) process** for implementation-level features that don't require a separate JSR. Large platform changes still go through JSRs, but smaller incremental features (new API methods, GC improvements) go through JEPs directly.

**Key JSRs you encounter daily:**

| JSR | What it standardised |
|---|---|
| JSR 14 | Generics (Java 5) |
| JSR 175 | Annotations (Java 5) |
| JSR 335 | Lambda expressions (Java 8) |
| JSR 376 | Java Platform Module System (Java 9) |
| JSR 386 | Java SE 14 (umbrella) |
| JSR 390 | Java SE 17 (umbrella) |
| JSR 393 | Java SE 21 (umbrella) |

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JCP process flow from JSR initiation to final release">
  <defs>
    <marker id="ajcp" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <!-- Stage boxes -->
  <rect x="10"  y="80" width="90" height="44" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="55" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JSR Draft</text>
  <text x="55" y="114" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">initiation</text>

  <line x1="100" y1="102" x2="118" y2="102" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ajcp)"/>

  <rect x="120" y="80" width="90" height="44" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="165" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">EC Vote</text>
  <text x="165" y="114" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">accept/reject</text>

  <line x1="210" y1="102" x2="228" y2="102" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ajcp)"/>

  <rect x="230" y="70" width="110" height="64" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="285" y="96"  fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Expert Group</text>
  <text x="285" y="111" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">spec + RI + TCK</text>
  <text x="285" y="124" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">public draft review</text>

  <line x1="340" y1="102" x2="358" y2="102" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ajcp)"/>

  <rect x="360" y="80" width="100" height="44" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="410" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Final EC Vote</text>
  <text x="410" y="114" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">approve/reject</text>

  <line x1="460" y1="102" x2="478" y2="102" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ajcp)"/>

  <rect x="480" y="70" width="180" height="64" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="570" y="93"  fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Final Release</text>
  <text x="570" y="109" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">spec published · TCK available</text>
  <text x="570" y="122" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">OpenJDK = reference implementation</text>

  <!-- Output labels -->
  <text x="55"  y="160" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">jcp.org</text>
  <text x="285" y="160" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">e.g. lambdas: 3 years</text>
  <text x="570" y="160" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">JLS + JVMS + TCK</text>
</svg>

JCP: JSR draft → EC vote → Expert Group (spec + RI + TCK) → final EC vote → published standard.

## 5. Runnable example

Scenario: introspect the Java Language Specification version, locate the JVM Specification class-file format details from bytecode, and simulate a simplified TCK compliance check — what a JCP certification suite does.

### Level 1 — Basic

```java
// JcpProbe.java
public class JcpProbe {
    public static void main(String[] args) {
        // Java SE specification version (the JSR umbrella version)
        System.out.println("Java SE spec version : " + System.getProperty("java.specification.version"));
        System.out.println("JVM spec version     : " + System.getProperty("java.vm.specification.version"));
        System.out.println("JVM spec vendor      : " + System.getProperty("java.vm.specification.vendor"));
        System.out.println("JVM spec name        : " + System.getProperty("java.vm.specification.name"));
        System.out.println();
        System.out.println("These properties encode which JSR (JCP process) this JVM implements.");
        System.out.println("java.specification.version = JSR 393 for Java SE 21, JSR 390 for Java SE 17, etc.");
    }
}
```

**How to run:** `java JcpProbe.java`

`java.specification.version` returns the Java SE spec version (e.g. `"21"`). This is the output of the JSR/JCP process — the spec version identifies which umbrella JSR was approved.

### Level 2 — Intermediate

Same JCP probe extended to run a set of mini-TCK checks — verifying that the JVM implements the Java SE specification correctly for a handful of well-known contracts.

```java
// MiniTck.java
import java.util.*;

public class MiniTck {

    record TestResult(String name, boolean passed, String detail) {}

    public static void main(String[] args) {
        String specVersion = System.getProperty("java.specification.version");
        System.out.println("=== Mini-TCK for Java SE " + specVersion + " ===");
        System.out.println("(Simulates what the real TCK does at larger scale)\n");

        List<TestResult> results = new ArrayList<>();

        // JLS 15.17.1: Integer division by zero throws ArithmeticException
        results.add(check("Integer division by zero → ArithmeticException", () -> {
            try { int r = 1 / 0; return false; }
            catch (ArithmeticException e) { return true; }
        }));

        // JLS 10.6: Arrays.toString produces [...] format
        results.add(check("Arrays.toString int[]", () ->
            "[1, 2, 3]".equals(Arrays.toString(new int[]{1, 2, 3}))));

        // JLS 3.10.5: String literals are interned
        results.add(check("String literal interning (==)", () -> {
            String a = "hello";
            String b = "hello";
            return a == b;   // must be same object due to interning
        }));

        // JLS 17.17: volatile ensures visibility
        results.add(check("volatile field is accessible", () -> {
            class Box { volatile int v = 42; }
            return new Box().v == 42;
        }));

        // JVMS 4.1: class file magic 0xCAFEBABE
        results.add(check("Class file starts with 0xCAFEBABE", () -> {
            try {
                var stream = MiniTck.class.getResourceAsStream("/MiniTck.class");
                if (stream == null) return true;  // can't check in source-launch
                byte[] b = stream.readNBytes(4);
                stream.close();
                return b[0] == (byte)0xCA && b[1] == (byte)0xFE && b[2] == (byte)0xBA && b[3] == (byte)0xBE;
            } catch (Exception e) { return true; }
        }));

        // JLS 8.3: static fields are shared across instances
        results.add(check("Static field shared across instances", () -> {
            class Counter { static int count = 0; Counter() { count++; } }
            new Counter(); new Counter(); new Counter();
            return Counter.count == 3;
        }));

        // Print results
        long passed = results.stream().filter(TestResult::passed).count();
        results.forEach(r -> System.out.printf("  [%s] %s%s%n",
            r.passed() ? "PASS" : "FAIL", r.name(), r.detail().isEmpty() ? "" : " — " + r.detail()));
        System.out.printf("%n%d/%d passed%n", passed, results.size());
    }

    static TestResult check(String name, java.util.concurrent.Callable<Boolean> test) {
        try {
            boolean ok = test.call();
            return new TestResult(name, ok, "");
        } catch (Exception e) {
            return new TestResult(name, false, e.getClass().getSimpleName() + ": " + e.getMessage());
        }
    }
}
```

**How to run:** `java MiniTck.java`

Each test verifies a specific JLS or JVMS requirement. The real TCK has thousands of such tests — passing all of them is what earns the "Java SE certified" designation.

### Level 3 — Advanced

Same JCP/TCK simulation grown to read the actual class-file version and specification metadata, enumerate JSR-defined interfaces in the JDK, and cross-reference JEP numbers with their JSR umbrella.

```java
// JcpAudit.java
import java.lang.module.*;
import java.util.*;
import java.util.stream.*;

public class JcpAudit {

    record JsrEntry(int jsr, String name, int javaVersion, String keyClass) {}

    // Sample JSRs and a key class they introduced (for validation)
    static final List<JsrEntry> KNOWN_JSRS = List.of(
        new JsrEntry(14,  "Generics",              5,  "java.util.ArrayList"),
        new JsrEntry(175, "Annotations",           5,  "java.lang.annotation.Annotation"),
        new JsrEntry(203, "NIO.2 / Files API",     7,  "java.nio.file.Files"),
        new JsrEntry(310, "Date and Time API",     8,  "java.time.LocalDate"),
        new JsrEntry(335, "Lambda Expressions",    8,  "java.util.function.Function"),
        new JsrEntry(376, "Java Module System",    9,  "java.lang.module.ModuleDescriptor"),
        new JsrEntry(334, "HTTP Client",           11, "java.net.http.HttpClient"),
        new JsrEntry(359, "Records (umbrella 14)", 16, "java.lang.Record"),
        new JsrEntry(409, "Sealed Classes (umbrella 17)", 17, "java.lang.SealedInterface"),
        new JsrEntry(441, "Pattern matching (umbrella 21)", 21, "java.util.SequencedCollection")
    );

    public static void main(String[] args) {
        int feature = Runtime.version().feature();
        System.out.println("╔══════════════════════════════════════════╗");
        System.out.println("║          JCP / JSR Audit                 ║");
        System.out.println("╚══════════════════════════════════════════╝\n");

        System.out.println("[ Specification Properties ]");
        System.out.println("  Java SE spec version : " + System.getProperty("java.specification.version"));
        System.out.println("  JVM spec version     : " + System.getProperty("java.vm.specification.version"));
        System.out.println("  Bytecode class version: " + System.getProperty("java.class.version"));
        System.out.println();

        // Check JSRs whose key classes should be present on this JVM
        System.out.println("[ JSR Availability Check ]");
        System.out.printf("  %-5s  %-40s  %-5s  %-10s  %s%n", "JSR", "Name", "Java", "Status", "Key class");
        System.out.println("  " + "-".repeat(90));
        for (JsrEntry jsr : KNOWN_JSRS) {
            boolean available = jsr.javaVersion() <= feature && classExists(jsr.keyClass());
            String status;
            if (jsr.javaVersion() > feature) {
                status = "Java " + jsr.javaVersion() + " needed";
            } else if (available) {
                status = "PRESENT";
            } else {
                status = "MISSING (API removed?)";
            }
            System.out.printf("  %-5d  %-40s  %-5d  %-10s  %s%n",
                jsr.jsr(), jsr.name(), jsr.javaVersion(), status, jsr.keyClass());
        }

        // Module system view (JSR 376 — Java 9)
        System.out.println("\n[ JSR 376 Module System — Boot Layer ]");
        if (feature >= 9) {
            long count = ModuleLayer.boot().modules().size();
            System.out.println("  Boot modules loaded : " + count);
            System.out.println("  Spec modules present: " +
                List.of("java.base","java.sql","java.xml","java.net.http").stream()
                    .filter(m -> ModuleLayer.boot().findModule(m).isPresent())
                    .collect(Collectors.joining(", ")));
        } else {
            System.out.println("  JSR 376 (modules) requires Java 9+");
        }
    }

    static boolean classExists(String name) {
        try { Class.forName(name); return true; }
        catch (ClassNotFoundException e) { return false; }
    }
}
```

**How to run:** `java JcpAudit.java`

`java.lang.SealedInterface` — the marker interface for sealed classes (JSR 409) — was added in Java 17. Running on Java 16 would show `MISSING` for that entry, correctly reflecting that the JSR had not yet been finalised at that version.

## 6. Walkthrough

Execution in `JcpAudit.main`:

1. **Specification properties** — `java.specification.version` returns the umbrella JSR version (the Java SE version number). `java.vm.specification.version` is the JVMS version. Both are set by the JVM at startup from constants baked into the JDK build.

2. **JSR availability check** — for each `JsrEntry`, the check has two conditions: `jsr.javaVersion() <= feature` (this JDK is old enough to include the JSR) AND `classExists(jsr.keyClass())` (the API class is actually on the classpath). The second check catches cases where the module was explicitly excluded with `jlink`.

3. **`java.lang.SealedInterface`** — this interface was added to `java.lang` as the marker for sealed class hierarchies. Its presence on the classpath confirms JSR 409 (sealed classes) is implemented. Running on Java 16 (pre-sealing) would show `classExists` returning `false`.

4. **Module layer** — `ModuleLayer.boot().modules().size()` lists how many modules the JVM loaded in the boot layer. On a full JDK install this is ~70; on a `jlink`-trimmed runtime it can be as low as 10. `findModule(name).isPresent()` verifies that specific JSR-defined modules are present.

5. **`java.net.http.HttpClient`** (JSR 334, Java 11) — if running on Java 10 or earlier, `classExists` returns `false` and the table shows `Java 11 needed`. This precisely reflects the JCP/JSR versioning.

Data flow:
```
Runtime.version().feature()     → int (e.g. 21)
KNOWN_JSRS list                 → static in-memory list
  for each: Class.forName(keyClass) → boolean (class present?)
  + javaVersion <= feature       → boolean (spec version met?)
  → "PRESENT" / "MISSING" / "needed"
ModuleLayer.boot().modules()   → Set<Module>
  → count and named-module lookup
console output
```

## 7. Gotchas & takeaways

> **JSRs are umbrella documents for Java SE releases.** "JSR 393" is not for a single feature — it is the umbrella specification for all of Java SE 21. Individual features have their own JSRs (JSR 335 for lambdas, JSR 376 for modules) but ship as part of the umbrella Java SE JSR.

> **The JEP process ≠ the JCP process.** JEPs (JDK Enhancement Proposals at openjdk.org) are the implementation-level design documents used inside the OpenJDK community. JSRs (at jcp.org) are the formal specification documents. A feature often has both a JEP (how we'll implement it) and a JSR reference (the formal spec obligation). Small changes may only have a JEP.

- JCP (jcp.org) is the formal standards body; JSR is a specification document; TCK is the compliance test suite.
- OpenJDK is the reference implementation of Java SE specifications.
- `java.specification.version` tells you which Java SE JSR umbrella this JVM implements.
- Since Java 9, incremental features use JEPs (openjdk.org/jeps/) directly; large spec changes still use JSRs.
- TCK certification is what makes a JVM "Java SE compliant" — Temurin, Corretto, Zulu all pass it.
- The JLS (Java Language Specification) and JVMS (JVM Specification) are the normative documents produced by the JCP process.
