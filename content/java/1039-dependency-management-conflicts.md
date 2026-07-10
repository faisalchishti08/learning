---
card: java
gi: 1039
slug: dependency-management-conflicts
title: Dependency management & conflicts
---

## 1. What it is

A **transitive dependency** is a library your project pulls in indirectly — you depend on library A, and A itself depends on library B, so B ends up on your classpath even though you never declared it yourself. A **dependency conflict** happens when two different things your project depends on (directly or transitively) require *different versions* of the same library — Maven and Gradle each have a resolution strategy that picks exactly one version to actually put on the classpath, and if that chosen version isn't compatible with what one of the callers actually needs, you get a `NoSuchMethodError` or `ClassNotFoundException` at *runtime*, not a compile error, because compilation only checked against whichever version happened to be on the classpath at compile time.

## 2. Why & when

A `pom.xml` might declare only two direct dependencies, but the actual dependency *tree* those two direct dependencies pull in transitively can easily include dozens of libraries — and if two different branches of that tree each need a different, incompatible version of the same library (Library A needs Jackson 2.10, Library B needs Jackson 2.17), Maven's default resolution ("nearest wins," picking whichever version is declared closest to your project in the dependency tree) or Gradle's default ("highest version wins") picks exactly one, silently, without alerting you that a conflict even existed. If the version that got picked is missing a method one of the libraries actually calls at runtime, that failure only surfaces when that specific code path executes — potentially in production, long after a clean-looking build succeeded.

Diagnose dependency conflicts with `mvn dependency:tree` (or `gradle dependencies`), which shows the full resolved tree including which version "won" for each library and why. Resolve a genuine conflict by explicitly declaring the version you need directly in your own POM/build script (which typically takes priority over transitively-pulled versions) — or, for Maven, using `<dependencyManagement>` to centralize and enforce one version across an entire multi-module project. Reach for this whenever a `dependency:tree` command reveals two different versions of the same library appearing in different branches of the tree, or when a runtime error like `NoSuchMethodError` suggests a version mismatch between compile-time and actual runtime classpath contents.

## 3. Core concept

```xml
<!-- Your project depends on two libraries that each transitively pull in
     DIFFERENT versions of the same library (jackson-databind here) -->
<dependencies>
    <dependency>
        <groupId>com.example</groupId>
        <artifactId>library-a</artifactId> <!-- transitively needs jackson-databind 2.10.0 -->
        <version>1.0.0</version>
    </dependency>
    <dependency>
        <groupId>com.example</groupId>
        <artifactId>library-b</artifactId> <!-- transitively needs jackson-databind 2.17.0 -->
        <version>2.0.0</version>
    </dependency>
</dependencies>

<!-- Fix: explicitly declare the version you actually want -- a DIRECT
     declaration in your own POM takes priority over transitive ones -->
<dependencies>
    <dependency>
        <groupId>com.example</groupId>
        <artifactId>library-a</artifactId>
        <version>1.0.0</version>
    </dependency>
    <dependency>
        <groupId>com.example</groupId>
        <artifactId>library-b</artifactId>
        <version>2.0.0</version>
    </dependency>
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>2.17.0</version> <!-- explicitly pinned: this version wins, resolving the conflict -->
    </dependency>
</dependencies>
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two direct dependencies, library-a and library-b, each transitively pulling in a different version of jackson-databind, with an explicit direct declaration overriding both to resolve the conflict">
  <rect x="30" y="20" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="100" y="41" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">library-a 1.0.0</text>
  <rect x="30" y="130" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="100" y="151" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">library-b 2.0.0</text>

  <rect x="260" y="20" width="160" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="340" y="41" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">jackson 2.10.0 (wants)</text>
  <rect x="260" y="130" width="160" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="340" y="151" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">jackson 2.17.0 (wants)</text>

  <rect x="470" y="70" width="160" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">jackson 2.17.0 (pinned)</text>

  <line x1="170" y1="37" x2="260" y2="37" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="170" y1="147" x2="260" y2="147" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="420" y1="37" x2="470" y2="80" stroke="#6db33f" marker-end="url(#a)"/>
  <line x1="420" y1="147" x2="470" y2="110" stroke="#6db33f" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Two transitive requirements for different versions of the same library are resolved to one explicitly pinned version.

## 5. Runnable example

Scenario: a small class that formats numbers using a locally-provided "utility" dependency, evolving from an unmanaged transitive dependency (silently picking a version) into an explicitly diagnosed and pinned resolution.

### Level 1 — Basic

```java
// File: NumberFormatterV1.java -- simulates an OLDER version of a shared utility library
public class NumberFormatterV1 {
    public String format(double value) {
        return String.format("%.1f", value); // only supports 1 decimal place
    }
}
```

```java
// File: ReportGenerator.java -- code written assuming the OLDER utility's behavior
public class ReportGenerator {
    public static void main(String[] args) {
        NumberFormatterV1 formatter = new NumberFormatterV1();
        System.out.println("Report total: " + formatter.format(42.987));
    }
}
```

**How to run:** save both files, then `javac NumberFormatterV1.java ReportGenerator.java && java ReportGenerator` (JDK 17+).

Expected output:
```
Report total: 43.0
```

This works, but it depends implicitly on whichever version of the utility happens to be present — nothing here documents or enforces which version is expected, so a build pulling in a different, incompatible version elsewhere in the dependency tree would silently change this behavior with no warning at compile time.

### Level 2 — Intermediate

```java
// File: NumberFormatterV2.java -- simulates a NEWER version of the SAME utility,
// with a DIFFERENT, incompatible method signature -- format() now REQUIRES a
// precision argument instead of defaulting to one decimal place.
public class NumberFormatterV2 {
    public String format(double value, int decimalPlaces) {
        return String.format("%." + decimalPlaces + "f", value);
    }
}
```

```java
// File: ReportGenerator.java -- code written assuming the OLDER signature,
// which no longer compiles against the newer version
public class ReportGenerator {
    public static void main(String[] args) {
        NumberFormatterV2 formatter = new NumberFormatterV2();
        System.out.println("Report total: " + formatter.format(42.987, 1)); // updated call site
    }
}
```

**How to run:** save both files, then `javac NumberFormatterV2.java ReportGenerator.java && java ReportGenerator` (JDK 17+).

Expected output:
```
Report total: 43.0
```

The real-world concern added: notice that upgrading from `NumberFormatterV1` to `NumberFormatterV2` required a **source code change** at the call site (`format(42.987)` became `format(42.987, 1)`) — this is exactly the kind of breaking change [semantic versioning](1038-semantic-versioning.md) says should bump a MAJOR version, and exactly the kind of change that, if it happened silently inside a transitive dependency your build resolved without you noticing, would cause a compile error (or worse, a runtime `NoSuchMethodError` if only one module recompiles against the old signature) instead of a clear, expected upgrade step.

### Level 3 — Advanced

```java
// File: ReportGenerator.java -- demonstrates the RUNTIME failure mode: code
// compiled against ONE version of a dependency, but run against a DIFFERENT,
// incompatible version actually present on the classpath at execution time.
import java.lang.reflect.Method;

public class ReportGenerator {
    public static void main(String[] args) throws Exception {
        // Simulates what happens when your code was COMPILED against
        // NumberFormatterV1's single-argument format(double), but a dependency
        // conflict resolved the ACTUAL runtime classpath to NumberFormatterV2,
        // which has NO such single-argument method at all.
        Class<?> formatterClass = Class.forName("NumberFormatterV2");
        Object formatter = formatterClass.getDeclaredConstructor().newInstance();

        try {
            // Looking for the OLD, single-argument signature this code expects --
            // but only the NEW, two-argument version actually exists on this classpath.
            Method oldMethod = formatterClass.getMethod("format", double.class);
            System.out.println((String) oldMethod.invoke(formatter, 42.987));
        } catch (NoSuchMethodException e) {
            System.out.println("RUNTIME FAILURE: " + e.getMessage());
            System.out.println("This is exactly what an unresolved dependency conflict produces --");
            System.out.println("a build that compiled successfully, but fails at runtime instead.");
        }
    }
}
```

**How to run:** save `NumberFormatterV2.java` (from Level 2) and this `ReportGenerator.java` in the same directory, then `javac NumberFormatterV2.java ReportGenerator.java && java ReportGenerator` (JDK 17+).

Expected output:
```
RUNTIME FAILURE: NumberFormatterV2.format(double)
This is exactly what an unresolved dependency conflict produces --
a build that compiled successfully, but fails at runtime instead.
```

The production-flavored hard case: this reflection-based lookup simulates precisely what a real dependency conflict produces — code that assumes one version's API (looked up via `getMethod`, mimicking what the compiler would have checked against a *different*, older version at compile time) fails at runtime when the actual resolved classpath contains an incompatible version instead. In a real conflict, this surfaces as `NoSuchMethodError` thrown directly by the JVM, not a caught `NoSuchMethodException` — shown here via reflection specifically so the failure can be demonstrated and explained without needing two actual separate JAR files on a real classpath.

## 6. Walkthrough

Tracing the reflection-based lookup in `ReportGenerator.main`:

1. `Class.forName("NumberFormatterV2")` loads the `NumberFormatterV2` class — this simulates the *actual* resolved dependency on the runtime classpath being the newer version, regardless of what version the calling code was originally written against.
2. `formatterClass.getDeclaredConstructor().newInstance()` constructs an instance of it via reflection.
3. `formatterClass.getMethod("format", double.class)` searches `NumberFormatterV2` for a public method named `format` taking exactly one `double` parameter — this simulates a compiler (or, in a real conflict, the JVM's method-resolution at invocation time) looking for the signature the *calling code* expects, based on whatever version it was compiled against.
4. `NumberFormatterV2` only declares `format(double, int)` — a method taking **two** parameters — so no method matching `format(double)` exists on this class at all. `getMethod` throws `NoSuchMethodException`, carrying the message `"NumberFormatterV2.format(double)"` describing exactly which signature couldn't be found.
5. The `catch (NoSuchMethodException e)` block catches this, printing the failure message followed by an explanation. In a real dependency-conflict scenario (not simulated via reflection), this exact situation — code compiled against one version's method signature, but a different, incompatible version resolved onto the actual runtime classpath — throws `NoSuchMethodError` directly from the JVM at the call site itself, crashing the program at that exact line, the moment it executes.
6. This is precisely why `mvn dependency:tree` (or `gradle dependencies`) matters as a proactive check — it would have shown, *before ever running the program*, that two different versions of the same library were present in the dependency tree, letting you pin the version and resolve the conflict deliberately rather than discovering the mismatch as an unexpected runtime crash.

## 7. Gotchas & takeaways

> **Gotcha:** a dependency conflict is *silent* by default — Maven and Gradle both resolve to exactly one version automatically, with no warning that a conflict existed unless you explicitly inspect the dependency tree; a clean, successful build gives no signal at all that two different, incompatible versions of a library were ever in contention.

- A transitive dependency is pulled in indirectly through something you directly depend on; a conflict arises when two different paths in the dependency tree require different, incompatible versions of the same library.
- Maven's default resolution is "nearest wins" (the version declared closest to your project in the tree); Gradle's default is typically "highest version wins" — both resolve silently, without alerting you to the conflict's existence.
- `mvn dependency:tree` (or `gradle dependencies`) is the direct, proactive way to inspect the fully resolved tree and spot conflicting versions before they cause a runtime failure.
- Explicitly declaring the version you need directly in your own POM/build script (or using Maven's `<dependencyManagement>` for multi-module consistency) overrides transitively-resolved versions, letting you deliberately pin the version that satisfies every consumer.
- A dependency conflict's failure mode is often a runtime `NoSuchMethodError` or `ClassNotFoundException`, not a compile error — the build can succeed cleanly and still fail the moment a specific, previously-unexercised code path actually runs.
- See [semantic versioning](1038-semantic-versioning.md) for why the version numbers involved in a conflict actually carry meaningful, trustworthy information about compatibility — that's what makes a deliberate version pin a safe resolution rather than a guess.
