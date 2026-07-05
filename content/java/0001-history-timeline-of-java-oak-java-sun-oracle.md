---
card: java
gi: 1
slug: history-timeline-of-java-oak-java-sun-oracle
title: History & timeline of Java (Oak → Java, Sun → Oracle)
---

## 1. What it is

Java is a general-purpose, object-oriented programming language created at Sun Microsystems in the early 1990s. What began as an experiment for consumer electronics became one of the most widely deployed platforms on the planet. Understanding where Java came from helps you make sense of its unusual design decisions — why it chose a virtual machine, why it shunned pointers, why its name is not the original one.

## 2. Why & when

Knowing Java's history matters because almost every quirk you encounter has a reason rooted in a specific constraint from a specific era. The explicit garbage collector, the write-once-run-anywhere promise, the bytecode model, the module system added in Java 9 — all products of real problems faced at a real moment in time. History is the "why" behind the "what".

## 3. Core concept

Think of Java's history as three distinct acts:

**Act 1 — The Lab (1991–1995):** James Gosling, Mike Sheridan, and Patrick Naughton at Sun Microsystems launched the "Green Project" to build software for set-top boxes and smart TVs. The first language was called **Oak** (after a tree outside Gosling's office). When they found "Oak" was already trademarked, a coffee-shop brainstorm produced **Java** — named loosely after the slang for coffee.

**Act 2 — The Web Boom (1995–2010):** Java was officially unveiled on 23 May 1995, riding the explosion of the World Wide Web. Sun positioned Java applets as interactive web content. The JVM and "write once, run anywhere" made Java the dominant enterprise platform through the late 1990s and 2000s. Major releases brought generics (Java 5, 2004), closures as lambdas (Java 8, 2014 — still one of the most transformative releases).

**Act 3 — Oracle & Modernity (2010–present):** Oracle acquired Sun Microsystems in January 2010 for $7.4 billion. The acquisition brought stewardship debates, the Android lawsuit against Google (alleging unauthorised use of Java APIs), and eventually a new release cadence: starting with Java 9 (2017) Java moves to a **six-month feature release cycle** with long-term support (LTS) releases every few years (11, 17, 21, 25).

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java history timeline from 1991 to 2024">
  <defs>
    <marker id="ah" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <!-- timeline spine -->
  <line x1="40" y1="100" x2="670" y2="100" stroke="#8b949e" stroke-width="2" marker-end="url(#ah)"/>
  <!-- events -->
  <!-- 1991 -->
  <circle cx="80"  cy="100" r="5" fill="#6db33f"/>
  <line x1="80" y1="100" x2="80" y2="60" stroke="#6db33f" stroke-width="1.2"/>
  <text x="80"  y="52"  fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">1991</text>
  <text x="80"  y="40"  fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Green Project</text>
  <!-- 1995 -->
  <circle cx="200" cy="100" r="5" fill="#6db33f"/>
  <line x1="200" y1="100" x2="200" y2="140" stroke="#6db33f" stroke-width="1.2"/>
  <text x="200" y="155" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">1995</text>
  <text x="200" y="168" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Java 1.0 launched</text>
  <!-- 2004 -->
  <circle cx="340" cy="100" r="5" fill="#79c0ff"/>
  <line x1="340" y1="100" x2="340" y2="60" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="340"  y="52"  fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">2004</text>
  <text x="340"  y="40"  fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Java 5 (generics)</text>
  <!-- 2010 -->
  <circle cx="450" cy="100" r="5" fill="#f85149"/>
  <line x1="450" y1="100" x2="450" y2="140" stroke="#f85149" stroke-width="1.2"/>
  <text x="450" y="155" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">2010</text>
  <text x="450" y="168" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Oracle acquires Sun</text>
  <!-- 2014 -->
  <circle cx="530" cy="100" r="5" fill="#79c0ff"/>
  <line x1="530" y1="100" x2="530" y2="60" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="530"  y="52"  fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">2014</text>
  <text x="530"  y="40"  fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Java 8 (lambdas)</text>
  <!-- 2017 -->
  <circle cx="610" cy="100" r="5" fill="#6db33f"/>
  <line x1="610" y1="100" x2="610" y2="140" stroke="#6db33f" stroke-width="1.2"/>
  <text x="610" y="155" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">2017+</text>
  <text x="610" y="168" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">6-month cadence</text>
</svg>

Java's journey from a set-top-box experiment to an enterprise mainstay to a modern cadence-driven platform.

## 5. Runnable example

The simplest way to *touch* Java history is to print the version you're running and observe the metadata baked into the JVM.

### Level 1 — Basic

```java
// JavaVersion.java
public class JavaVersion {
    public static void main(String[] args) {
        System.out.println("Java version : " + System.getProperty("java.version"));
        System.out.println("Vendor        : " + System.getProperty("java.vendor"));
        System.out.println("VM name       : " + System.getProperty("java.vm.name"));
    }
}
```

**How to run:** `java JavaVersion.java`

This prints the JVM's self-reported identity. The `java.version` property format changed in Java 9 from `1.8.0_xyz` (the old "1.x" style) to `17.0.2` (plain major version), which is itself a piece of history — the old scheme survived because Java 1.0 through 1.4 was versioned as "1.x".

### Level 2 — Intermediate

Same program, extended to parse the major version number and explain which era of Java you're in — reflecting the three historical acts above.

```java
// JavaVersionEra.java
public class JavaVersionEra {
    public static void main(String[] args) {
        String version = System.getProperty("java.version");
        int major = parseMajor(version);

        System.out.println("Java version : " + version);
        System.out.println("Major        : " + major);
        System.out.println("Era          : " + era(major));
        System.out.println("LTS?         : " + isLts(major));
    }

    static int parseMajor(String v) {
        // Old style: "1.8.0_xxx" -> major 8; new style: "17.0.2" -> major 17
        String first = v.split("[._]")[0];
        int n = Integer.parseInt(first);
        return (n == 1) ? Integer.parseInt(v.split("[._]")[1]) : n;
    }

    static String era(int major) {
        if (major <= 8)  return "Classic (pre-modules, pre-cadence)";
        if (major <= 16) return "Transition (modules introduced, old cadence)";
        return "Modern (6-month release cadence, LTS pattern)";
    }

    static boolean isLts(int major) {
        // LTS releases: 8, 11, 17, 21, 25 ...
        return major == 8 || major == 11 || major == 17 || major == 21 || major == 25;
    }
}
```

**How to run:** `java JavaVersionEra.java`

`parseMajor` handles both the legacy `1.x` scheme and the modern plain-major scheme — a concrete reminder of the fork in versioning philosophy that happened in 2017.

### Level 3 — Advanced

Same scenario, now pulling all version-related system properties, detecting the vendor (Oracle JDK vs OpenJDK lineage), and printing a condensed provenance report — useful in production diagnostics.

```java
// JavaProvenance.java
import java.util.Map;
import java.util.LinkedHashMap;

public class JavaProvenance {
    public static void main(String[] args) {
        Map<String, String> props = new LinkedHashMap<>();
        String[] keys = {
            "java.version", "java.vendor", "java.vendor.url",
            "java.runtime.name", "java.runtime.version",
            "java.vm.name", "java.vm.vendor", "java.vm.version",
            "java.class.version", "os.name", "os.arch"
        };
        for (String k : keys) props.put(k, System.getProperty(k, "<not set>"));

        int colW = props.keySet().stream().mapToInt(String::length).max().orElse(20);
        System.out.println("=== Java Provenance Report ===");
        props.forEach((k, v) ->
            System.out.printf("%-" + colW + "s : %s%n", k, v));

        int major = parseMajor(props.get("java.version"));
        String vendor = props.get("java.vendor").toLowerCase();
        System.out.println("\nVendor lineage : " + vendorLineage(vendor));
        System.out.println("Release era    : " + era(major));
        System.out.println("LTS release    : " + isLts(major));
    }

    static int parseMajor(String v) {
        String first = v.split("[._]")[0];
        int n = Integer.parseInt(first);
        return (n == 1) ? Integer.parseInt(v.split("[._]")[1]) : n;
    }

    static String vendorLineage(String vendor) {
        if (vendor.contains("oracle")) return "Oracle JDK (commercial license for some uses post-Java 8)";
        if (vendor.contains("eclipse") || vendor.contains("adoptium")) return "Eclipse Temurin (free, TCK-certified OpenJDK build)";
        if (vendor.contains("amazon"))  return "Amazon Corretto (free, long-term OpenJDK build)";
        if (vendor.contains("azul"))    return "Azul Zulu (free community / Zing commercial)";
        if (vendor.contains("microsoft")) return "Microsoft Build of OpenJDK (free)";
        return "OpenJDK lineage (free, open-source)";
    }

    static String era(int major) {
        if (major <= 8)  return "Classic";
        if (major <= 16) return "Transition";
        return "Modern (6-month cadence)";
    }

    static boolean isLts(int major) {
        return major == 8 || major == 11 || major == 17 || major == 21 || major == 25;
    }
}
```

**How to run:** `java JavaProvenance.java`

This is the same "detect my runtime" scenario grown to production-grade: it now handles multi-vendor detection, formats a table of all version properties, and maps `java.class.version` (the bytecode level) to understand what bytecode generation level the compiler targeted.

## 6. Walkthrough

Execution begins at `main`. The program calls `System.getProperty`, which queries properties set by the JVM launcher when the process started — they live in the JVM's internal property table, initialised before `main` runs.

**Data flow through Level 3:**

1. **Property collection** — the loop populates a `LinkedHashMap` (insertion-order preserved, important for tidy output). Each key maps to a string or `"<not set>"` as a safe default.
2. **Column width** — a stream over key lengths finds the longest, so `printf` can pad all keys to the same width. Minor ergonomics detail, but it mirrors how production diagnostics tools format output.
3. **Version parsing (`parseMajor`)** — receives `"17.0.2"` or `"1.8.0_362"`. Splits on `.` or `_`, reads the first segment. If it is `1`, the real major is the *second* segment (the legacy scheme). Otherwise the first segment *is* the major. Returns an `int`.
4. **Vendor lineage** — `vendor.toLowerCase()` followed by `contains` checks identifies the distribution. This matters because Oracle JDK changed its license terms in 2019; teams need to know whether their JDK requires a paid subscription.
5. **Era & LTS classification** — returns a human-readable string; the LTS list is hardcoded because the LTS cadence is a policy decision, not something the JVM exposes as a property.

Sample output on Java 21 (Temurin):
```
=== Java Provenance Report ===
java.version            : 21.0.2
java.vendor             : Eclipse Adoptium
...
java.class.version      : 65.0

Vendor lineage : Eclipse Temurin (free, TCK-certified OpenJDK build)
Release era    : Modern (6-month cadence)
LTS release    : true
```

`java.class.version` `65.0` means class files compiled with Java 21 (`45 + major - 1` = `65`). An older JVM would refuse to load them with `UnsupportedClassVersionError` — the versioning artefact that has existed since Java 1.0.

## 7. Gotchas & takeaways

> The version string format changed in Java 9. Code that parses `"1.8.0_362"` with a simple `split(".")[0]` returns `"1"`, not `"8"`. Always handle both the old `1.x` and new plain-major formats.

> Oracle JDK is not always free. Since January 2019, Oracle JDK requires a paid subscription for production use on versions 8u211+ (with some exceptions). OpenJDK builds (Temurin, Corretto, Zulu) carry no such restriction. Know which distribution your production servers run.

- Java started as **Oak** in 1991; the name changed to Java before the 1995 public launch.
- The **JVM** (virtual machine) was not an afterthought — it was the core design decision that enabled platform independence.
- Java 5 (2004) was a seismic release: generics, annotations, autoboxing, enums, varargs all landed at once.
- Java 8 (2014) brought lambdas and streams — still the most-used release in enterprise after a decade.
- From Java 9 (2017) onwards: **six-month release cadence**; LTS every 3 years (later every 2).
- `java.class.version` encodes bytecode compatibility; `UnsupportedClassVersionError` happens when this version exceeds the JVM's supported range.
