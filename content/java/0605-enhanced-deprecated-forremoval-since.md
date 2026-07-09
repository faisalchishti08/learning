---
card: java
gi: 605
slug: enhanced-deprecated-forremoval-since
title: Enhanced @Deprecated (forRemoval, since)
---

## 1. What it is

Java 9 enhanced the `@Deprecated` annotation with two new elements: `forRemoval` (a `boolean`, default `false`) and `since` (a `String`, default `""`). `forRemoval = true` signals that the annotated API is slated for actual removal in a future release — not merely discouraged. `since` documents the version in which the deprecation was introduced. Together they provide richer, machine-readable deprecation metadata that IDEs, build tools, and static analysis can use to emit appropriate warnings: a gentle reminder for ordinary deprecation, a more urgent warning when `forRemoval = true`.

## 2. Why & when

Before Java 9, `@Deprecated` was a marker annotation with no parameters. You could add a Javadoc `@deprecated` tag to explain *why* and *what to use instead*, but there was no standard way to distinguish "we recommend against using this" from "this will be deleted in the next major release." Tools treated every `@Deprecated` the same — a single yellow warning. Library maintainers wanted a way to signal the severity of the deprecation: a method deprecated in v2.0 and marked for removal in v3.0 should produce a stronger warning than one merely superseded by a better alternative that will coexist indefinitely. `forRemoval` and `since` provide exactly that signal.

## 3. Core concept

```java
// Mild deprecation — better alternative exists, but old API stays
@Deprecated(since = "2.0")
public void oldMethod() { ... }

// Serious deprecation — this API WILL be removed
@Deprecated(since = "2.0", forRemoval = true)
public void legacyMethod() { ... }

// Reflection can read the elements at runtime
Deprecated anno = MyClass.class
    .getDeclaredMethod("legacyMethod")
    .getAnnotation(Deprecated.class);
System.out.println(anno.since());      // "2.0"
System.out.println(anno.forRemoval()); // true
```

The `@Deprecated` annotation now has attributes you can query. The `javac` compiler uses these to control warning severity: any use of a `@Deprecated(forRemoval=true)` element produces a **mandatory** warning (suppressible only with `@SuppressWarnings("removal")`), while ordinary `@Deprecated` uses can be suppressed with the usual `@SuppressWarnings("deprecation")`.

## 4. Diagram

<svg viewBox="0 0 600 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@Deprecated now carries forRemoval and since for richer deprecation signalling">
  <rect x="20" y="10" width="560" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="40" y="30" width="240" height="50" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="160" y="48" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">@Deprecated</text>
  <text x="160" y="68" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">since="1.5", forRemoval=false</text>

  <text x="290" y="55" fill="#8b949e" font-size="10" font-family="monospace">──►</text>

  <rect x="300" y="35" width="120" height="40" rx="4" fill="#f0883e" stroke="#f0883e"/>
  <text x="360" y="60" fill="#f0883e" font-size="10" text-anchor="middle" font-family="monospace">warning (yellow)</text>

  <rect x="40" y="100" width="240" height="50" rx="4" fill="#0d1117" stroke="#f85149"/>
  <text x="160" y="118" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">@Deprecated</text>
  <text x="160" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">since="2.0", forRemoval=true</text>

  <text x="290" y="125" fill="#8b949e" font-size="10" font-family="monospace">──►</text>

  <rect x="300" y="105" width="120" height="40" rx="4" fill="#f85149" stroke="#f85149"/>
  <text x="360" y="130" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">mandatory warning</text>

  <text x="450" y="60" fill="#8b949e" font-size="8" font-family="sans-serif">@SuppressWarnings("deprecation")</text>
  <text x="450" y="130" fill="#8b949e" font-size="8" font-family="sans-serif">@SuppressWarnings("removal")</text>
</svg>

`forRemoval = true` triggers a stronger warning that requires a different suppression key.

## 5. Runnable example

Scenario: a library evolution story where a `ConnectionPool` API is gradually deprecated and eventually marked for removal — starting with basic deprecation metadata, extending to reflective inspection and compiler warning differentiation, and finally building a migration linter that detects and reports `forRemoval` usage.

### Level 1 — Basic

```java
// File: EnhancedDeprecatedDemo.java

public class EnhancedDeprecatedDemo {

    // Old API — still works, but replaced by connectSecure()
    @Deprecated(since = "2.0")
    public void connect(String host, int port) {
        System.out.println("Connecting to " + host + ":" + port + " (DEPRECATED)");
    }

    // New API
    public void connectSecure(String host, int port, String cert) {
        System.out.println("Secure connection to " + host + ":" + port);
    }

    public static void main(String[] args) {
        EnhancedDeprecatedDemo demo = new EnhancedDeprecatedDemo();

        @SuppressWarnings("deprecation")
        int x = 1; // dummy to show suppression is possible

        // This call produces a deprecation warning at compile time
        demo.connect("example.com", 443);
        demo.connectSecure("example.com", 443, "my-cert");
    }
}
```

**How to run:** `java EnhancedDeprecatedDemo.java`

Expected output:
```
Connecting to example.com:443 (DEPRECATED)
Secure connection to example.com:443
```

The simplest usage: `@Deprecated(since = "2.0")` documents when the deprecation was introduced. If you compile with `javac -Xlint:deprecation`, you'll see a warning for the `connect()` call. The `@SuppressWarnings("deprecation")` annotation silences it.

### Level 2 — Intermediate

```java
// File: DeprecatedInspection.java
import java.lang.reflect.Method;

public class DeprecatedInspection {

    // Mild deprecation — prefer the new API, but old one is safe
    @Deprecated(since = "1.0")
    public static String formatDateLegacy(int y, int m, int d) {
        return y + "-" + m + "-" + d;
    }

    // Marked for removal — will be deleted in the next major version
    @Deprecated(since = "2.0", forRemoval = true)
    public static String formatDateAncient(int y, int m, int d) {
        return d + "/" + m + "/" + y;
    }

    // Replacement API (not deprecated)
    public static String formatDate(int y, int m, int d) {
        return String.format("%04d-%02d-%02d", y, m, d);
    }

    static void inspectDeprecation(Class<?> cls, String methodName) {
        try {
            Method m = cls.getDeclaredMethod(methodName, int.class, int.class, int.class);
            Deprecated d = m.getAnnotation(Deprecated.class);
            if (d != null) {
                System.out.printf("  %s is @Deprecated since %s%s%n",
                    methodName,
                    d.since(),
                    d.forRemoval() ? " (MARKED FOR REMOVAL!)" : ""
                );
            } else {
                System.out.printf("  %s is NOT deprecated%n", methodName);
            }
        } catch (NoSuchMethodException e) {
            System.out.println("  Method not found");
        }
    }

    @SuppressWarnings("removal")
    public static void main(String[] args) {
        System.out.println("=== Deprecation status of formatting methods ===\n");

        inspectDeprecation(DeprecatedInspection.class, "formatDateLegacy");
        inspectDeprecation(DeprecatedInspection.class, "formatDateAncient");
        inspectDeprecation(DeprecatedInspection.class, "formatDate");

        System.out.println("\n=== Calling all three (suppressed warnings) ===");
        System.out.println("  formatDateLegacy: " + formatDateLegacy(2026, 7, 9));
        System.out.println("  formatDateAncient: " + formatDateAncient(2026, 7, 9));
        System.out.println("  formatDate: " + formatDate(2026, 7, 9));
    }
}
```

**How to run:** `java DeprecatedInspection.java`

Expected output:
```
=== Deprecation status of formatting methods ===

  formatDateLegacy is @Deprecated since 1.0
  formatDateAncient is @Deprecated since 2.0 (MARKED FOR REMOVAL!)
  formatDate is NOT deprecated

=== Calling all three (suppressed warnings) ===
  formatDateLegacy: 2026-7-9
  formatDateAncient: 9/7/2026
  formatDate: 2026-07-09
```

The real-world concern added: reflective inspection of `@Deprecated` metadata. The `inspectDeprecation` method reads `since()` and `forRemoval()` at runtime to produce different warnings. Notice the `@SuppressWarnings("removal")` on `main` — this is the *different* suppression key required for `forRemoval = true` APIs. Ordinary `@SuppressWarnings("deprecation")` does NOT suppress removal warnings.

### Level 3 — Advanced

```java
// File: MigrationLinter.java
import java.lang.reflect.Method;
import java.util.List;

public class MigrationLinter {

    // Simulated library API evolution
    static class LegacyLib {
        @Deprecated(since = "1.5")
        public void oldSave() {}

        @Deprecated(since = "2.0", forRemoval = true)
        public void ancientLoad() {}

        public void newSave() {}
        public void newLoad() {}
    }

    // A linter that checks a class for usage of deprecated APIs
    record LintFinding(String method, String severity, String message) {}

    static List<LintFinding> lintClass(Class<?> target) {
        return List.of(target.getDeclaredMethods()).stream()
            .filter(m -> m.isAnnotationPresent(Deprecated.class))
            .map(m -> {
                Deprecated d = m.getAnnotation(Deprecated.class);
                String severity = d.forRemoval() ? "ERROR" : "WARNING";
                String msg = d.forRemoval()
                    ? "Method will be removed — migrate immediately to newLoad()"
                    : "Prefer newSave() — deprecated since " + d.since();
                return new LintFinding(m.getName(), severity, msg);
            })
            .toList();
    }

    public static void main(String[] args) {
        System.out.println("=== Migration Linter Report: LegacyLib ===\n");

        List<LintFinding> findings = lintClass(LegacyLib.class);

        if (findings.isEmpty()) {
            System.out.println("  No deprecated APIs found. Clean bill of health.");
            return;
        }

        for (var f : findings) {
            String icon = f.severity().equals("ERROR") ? "❌" : "⚠️";
            System.out.printf("  %s [%s] %s%n", icon, f.severity(), f.method());
            System.out.printf("     %s%n", f.message());
        }

        System.out.println("\nSummary:");
        long errors = findings.stream().filter(f -> f.severity().equals("ERROR")).count();
        long warnings = findings.size() - errors;
        System.out.printf("  %d error(s), %d warning(s)%n", errors, warnings);
        if (errors > 0) {
            System.out.println("  ❌ Build should fail — forRemoval APIs detected.");
        }
    }
}
```

**How to run:** `java MigrationLinter.java`

Expected output:
```
=== Migration Linter Report: LegacyLib ===

  ⚠️ [WARNING] oldSave
     Prefer newSave() — deprecated since 1.5
  ❌ [ERROR] ancientLoad
     Method will be removed — migrate immediately to newLoad()

Summary:
  1 error(s), 1 warning(s)
  ❌ Build should fail — forRemoval APIs detected.
```

The production-flavoured tooling: a migration linter that scans a class for deprecated methods and categorises them by severity. `forRemoval = true` methods produce `ERROR`-level findings (suggesting the build should fail), while ordinary deprecation produces `WARNING`-level findings. This is exactly how modern build plugins operate — they read `@Deprecated` metadata and can be configured to fail the build on removal-marked API usage.

## 6. Walkthrough

Tracing `lintClass(LegacyLib.class)` in the Level 3 example:

1. `lintClass(LegacyLib.class)` receives the `Class<LegacyLib>` object. `target.getDeclaredMethods()` returns all methods declared directly in `LegacyLib`: `[oldSave, ancientLoad, newSave, newLoad]`.

2. The stream filters: `.filter(m -> m.isAnnotationPresent(Deprecated.class))`. Only `oldSave` and `ancientLoad` have the `@Deprecated` annotation. `newSave` and `newLoad` are filtered out.

3. For `oldSave`:
   - `d = m.getAnnotation(Deprecated.class)` returns the annotation instance.
   - `d.forRemoval()` → `false` (default, not set).
   - `d.since()` → `"1.5"`.
   - Severity: `"WARNING"`. Message: `"Prefer newSave() — deprecated since 1.5"`.
   - `LintFinding("oldSave", "WARNING", msg)` is produced.

4. For `ancientLoad`:
   - `d.forRemoval()` → `true`.
   - `d.since()` → `"2.0"`.
   - Severity: `"ERROR"`. Message: `"Method will be removed — migrate immediately to newLoad()"`.
   - `LintFinding("ancientLoad", "ERROR", msg)` is produced.

5. `.toList()` collects both `LintFinding` objects. The list is returned to `main`.

6. `main` iterates the findings: `oldSave` prints with `⚠️` and `[WARNING]`, `ancientLoad` prints with `❌` and `[ERROR]`. The summary counts 1 error, 1 warning, and prints the build-failure recommendation.

## 7. Gotchas & takeaways

> `@SuppressWarnings("deprecation")` does **not** suppress warnings for `forRemoval = true` APIs. You need `@SuppressWarnings("removal")` for that. If a method is both deprecated and marked for removal, you may need both suppression annotations if you want to silence all related warnings.

- `since` is a free-form `String` — there is no enforced format. The convention is to use the version number as it appears in the library's release (`"1.5"`, `"2.0.1"`, `"2024-03"`), but the compiler doesn't validate it.
- `forRemoval` defaults to `false` — existing `@Deprecated` annotations without the element behave exactly as before, so the enhancement is fully backward-compatible.
- The Javadoc tool uses `@Deprecated(since="...", forRemoval=true)` to generate a stronger "Deprecated. For removal." label in the generated documentation, with the `since` value rendered in the deprecation notice.
- Reflective access works as expected: `AnnotatedElement.getAnnotation(Deprecated.class)` returns the annotation with `since` and `forRemoval` populated. This enables runtime tooling like the migration linter to make decisions based on deprecation severity.
- The JDK itself uses these elements extensively — check `java.util.Observable` (`@Deprecated(since="9")`) or `Thread.destroy()` (`@Deprecated(since="1.5", forRemoval=true)`) for examples in the standard library. 