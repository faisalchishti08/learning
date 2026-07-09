---
card: java
gi: 583
slug: jdeps-for-module-migration
title: jdeps for module migration
---

## 1. What it is

`jdeps` is a JDK-bundled static analysis tool that scans compiled `.class` files or JARs and reports their dependencies — which packages and modules they reference, including (critically, for migration purposes) any internal, JDK-implementation-detail APIs they depend on. Beyond plain dependency reporting, `jdeps` has a `--generate-module-info` mode that can automatically draft a `module-info.java` for an existing, non-modular JAR by analyzing what it actually uses.

## 2. Why & when

Modularizing an existing, non-trivial codebase by hand is tedious and error-prone: you'd have to manually trace every `import` across every source file to figure out which packages need to be exported, which JDK modules need to be required, and — the hardest part — whether any code relies on internal, unsupported JDK APIs that will break under strong encapsulation on a modern JDK. `jdeps` automates exactly this analysis. It's the standard first step in any "modularize this project" or "upgrade this old JAR to a modern JDK" task: run `jdeps` before touching any code, and let it tell you exactly what dependencies exist, what's missing, and what's likely to break.

## 3. Core concept

```
jdeps --jdk-internals mylib.jar
```
```
mylib.jar -> java.base
   com.mylib.Utils -> sun.misc.Unsafe   java.base
      JDK internal API (jdk.unsupported)
```

```
jdeps --generate-module-info out-dir mylib.jar
```
```
writing to out-dir/mylib/module-info.java
```

`--jdk-internals` specifically filters the report down to JDK-internal API usage — exactly the dependencies most likely to break when moving to a stricter, more strongly-encapsulated JDK version. `--generate-module-info` goes further, analyzing the JAR's actual `import`/reference graph and writing out a best-effort `module-info.java` draft (with `requires` for everything it detects being used, and `exports` for every package the JAR contains) as a starting point for manual review and refinement.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jdeps scans a compiled JAR and reports its dependencies, flags internal API usage, and can draft a module-info.java automatically">
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="50" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">mylib.jar</text>

  <line x1="200" y1="45" x2="280" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#j1)"/>
  <text x="240" y="35" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">jdeps</text>

  <rect x="280" y="20" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="360" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">dependency report</text>
  <text x="360" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">+ flagged internals</text>

  <rect x="460" y="20" width="160" height="50" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="540" y="42" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">draft module-info.java</text>
  <text x="540" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(--generate-module-info)</text>

  <line x1="200" y1="60" x2="460" y2="60" stroke="#f0883e" stroke-width="1" stroke-dasharray="3,3"/>
</svg>

Analysis first, code changes second — `jdeps` never modifies the JAR itself, only reports on it or writes a separate draft file.

## 5. Runnable example

Scenario: a small pre-existing "reporting" library JAR (no `module-info.java`) that depends on another library and on `java.sql` — starting with a plain dependency summary, then flagging any JDK-internal API usage specifically, then generating a draft `module-info.java` and using it as the real starting point for turning the JAR into a genuine named module.

### Level 1 — Basic

```java
// File: reportlib/com/reportlib/ReportBuilder.java — a plain library, no module-info.java
package com.reportlib;
import java.sql.Timestamp;
import java.util.List;

public class ReportBuilder {
    public String build(List<String> lines, Timestamp generatedAt) {
        return "Report (" + generatedAt + "):\n" + String.join("\n", lines);
    }
}
```

**How to run:**
```
javac -d out reportlib/com/reportlib/ReportBuilder.java
jar --create --file reportlib.jar -C out .
jdeps reportlib.jar
```

Expected output:
```
reportlib.jar -> java.base
reportlib.jar -> java.sql
   com.reportlib                                      -> java.lang                                          java.base
   com.reportlib                                      -> java.lang.invoke                                   java.base
   com.reportlib                                      -> java.sql                                           java.sql
   com.reportlib                                      -> java.util                                          java.base
```

Plain `jdeps reportlib.jar` (no extra flags) reports the JAR's package-level dependency graph: `com.reportlib` (the only package in this JAR) depends on `java.lang`, `java.lang.invoke` (pulled in implicitly by the compiler for `String.join`'s use of invokedynamic under the hood), and `java.util` — all supplied by `java.base` — plus `java.sql`, which is its own separate JDK module. The two summary lines at the top (`reportlib.jar -> java.base` and `reportlib.jar -> java.sql`) roll this up to module granularity: these are the two modules `reportlib.jar` as a whole depends on. This is the baseline: a complete, automatically-derived picture of what the JAR actually needs, without reading a single line of its source code by hand.

### Level 2 — Intermediate

```java
// File: reportlib/com/reportlib/LegacyHelper.java — uses a JDK-internal API
package com.reportlib;
import sun.misc.Unsafe;
import java.lang.reflect.Field;

public class LegacyHelper {
    public static Unsafe getUnsafe() throws Exception {
        Field f = Unsafe.class.getDeclaredField("theUnsafe");
        f.setAccessible(true);
        return (Unsafe) f.get(null);
    }
}
```

**How to run:**
```
javac -d out reportlib/com/reportlib/ReportBuilder.java reportlib/com/reportlib/LegacyHelper.java
jar --create --file reportlib.jar -C out .
jdeps --jdk-internals reportlib.jar
```

Expected output:
```
reportlib.jar -> jdk.unsupported
   com.reportlib.LegacyHelper                         -> sun.misc.Unsafe                                    JDK internal API (jdk.unsupported)

Warning: JDK internal APIs are unsupported and private to JDK implementation that are
subject to be removed or changed incompatibly and could break your application.
Please modify your code to eliminate dependence on any JDK internal APIs.
For the most recent update on JDK internal API replacements, please check:
https://wiki.openjdk.org/display/JDK8/Java+Dependency+Analysis+Tool

JDK Internal API                         Suggested Replacement
----------------                         ---------------------
sun.misc.Unsafe                          See https://openjdk.org/jeps/260
```

The real-world concern this adds: `--jdk-internals` specifically isolates and flags dependencies on internal, unsupported JDK APIs — here, `LegacyHelper`'s use of `sun.misc.Unsafe` — with an explicit warning that such dependencies are exactly the kind that break or change across JDK versions, plus a suggested-replacement table pointing at the sanctioned public alternative (JEP 260, which documents `Unsafe`'s replacements including `VarHandle`, as covered in the strong-encapsulation topic). `reportlib.jar` still contains `ReportBuilder` alongside `LegacyHelper`, but `--jdk-internals` filters the report down to *only* internal-API dependencies — `ReportBuilder`'s ordinary `java.sql`/`java.util` usage from Level 1 simply doesn't appear in this filtered view, since it isn't an internal-API concern. This is the precise first step recommended before modularizing or upgrading any older codebase: run `--jdk-internals` and treat every flagged usage as a required fix before proceeding further.

### Level 3 — Advanced

```java
// File: reportlib/com/reportlib/ReportBuilder.java — remove the internal-API dependency first
package com.reportlib;
import java.sql.Timestamp;
import java.util.List;

public class ReportBuilder {
    public String build(List<String> lines, Timestamp generatedAt) {
        return "Report (" + generatedAt + "):\n" + String.join("\n", lines);
    }
}
```

**How to run:** with `LegacyHelper.java` removed (its internal-API dependency fixed or eliminated first, per Level 2's guidance), generate a draft `module-info.java` for the now-clean JAR:
```
javac -d out reportlib/com/reportlib/ReportBuilder.java
jar --create --file reportlib.jar -C out .
jdeps --generate-module-info generated reportlib.jar
cat generated/reportlib/module-info.java
```

Expected output:
```
writing to generated/reportlib/module-info.java
```
```java
module reportlib {
    requires transitive java.sql;

    exports com.reportlib;

}
```

This handles the production-flavoured payoff: `--generate-module-info generated` analyzes `reportlib.jar`'s actual dependency graph (post-cleanup, with no more internal-API usage to complicate things) and writes a real, syntactically-correct `module-info.java` draft to `generated/reportlib/module-info.java` — `requires transitive java.sql;` because `ReportBuilder`'s own public method `build(...)` takes a `Timestamp` parameter directly in its signature, so `jdeps` correctly infers that `java.sql` isn't just an internal implementation detail but part of `reportlib`'s own exported public API surface (exactly the `requires transitive` scenario covered in its own topic), and `exports com.reportlib;` because that's the JAR's one and only package. This draft can now be copied into the project, recompiled together with the rest of the source, and refined by hand (double-checking that `transitive` is genuinely warranted, tightening `exports` to hide any packages that shouldn't be public) — turning what would otherwise be manual, error-prone analysis into a verified, generated starting point.

## 6. Walkthrough

Execution starts with the build and `jdeps` invocation in Level 3, run against the cleaned-up `reportlib.jar` (with `LegacyHelper` and its `sun.misc.Unsafe` dependency already removed, following Level 2's diagnostic).

`jdeps --generate-module-info generated reportlib.jar` performs a full static analysis of every class file inside `reportlib.jar`. For each class, `jdeps` inspects the constant pool (the part of a compiled `.class` file listing every external symbol — class names, method signatures — the class references) to determine exactly which other classes and packages it depends on, then maps each of those packages back to the JDK (or other) module that actually supplies it.

```
jdeps's analysis of ReportBuilder.class:

references java.sql.Timestamp   -> supplied by module java.sql   -> needs "requires ... java.sql;"
   AND Timestamp appears directly in build(...)'s PUBLIC signature -> mark it "transitive"
references java.util.List       -> supplied by module java.base  -> implicit, no requires line needed
references java.lang.String     -> supplied by module java.base  -> implicit

Package com.reportlib itself: the only package in this JAR -> gets "exports com.reportlib;"
```

Having built this picture, `jdeps` writes a draft `module-info.java` to `generated/reportlib/module-info.java`: `requires transitive java.sql;` for the one genuine external module-level dependency it found (`java.base` is never written explicitly, since it's always implicit for every module, exactly as covered in the `requires` directive topic) — `jdeps` specifically detects that `Timestamp`, a `java.sql` type, appears directly in `build(...)`'s own public parameter list, and infers that any consumer of `reportlib`'s public API will also need to name `Timestamp`, exactly the scenario the `requires transitive` topic covers, so it marks the dependency `transitive` automatically rather than requiring a human to notice this. `exports com.reportlib;` covers the JAR's single package, since `--generate-module-info` defaults to exporting every package a JAR contains — on the reasonable assumption that everything in a JAR with no existing `module-info.java` was previously reachable by any classpath consumer, so exporting everything preserves that prior, fully-open visibility as the safest starting point.

`cat generated/reportlib/module-info.java` displays the generated file's contents, confirming both lines are present and syntactically valid Java module-declaration syntax — ready to be copied directly into `reportlib`'s own source tree, after which `reportlib.jar` becomes a genuine named module rather than merely an automatic module (as it would be if simply placed on the module path without ever generating and adding this file).

The key insight this whole three-level progression demonstrates: `jdeps` is meant to be run in this order — first, plain dependency reporting (Level 1) for basic understanding; second, `--jdk-internals` (Level 2) to find and fix anything that would break under strong encapsulation *before* generating a module declaration around it; third, `--generate-module-info` (Level 3) only once the JAR's dependencies are clean, producing a draft that accurately reflects the JAR's real, sanctioned dependency graph rather than one polluted by internal APIs that shouldn't be depended on in the first place.

## 7. Gotchas & takeaways

> `--generate-module-info`'s draft is a **starting point, not a finished product** — it exports every package unconditionally by default (since it can't know which packages were meant to be genuinely public API versus merely reachable-by-accident on the old classpath), and it cannot detect dependencies reached only through reflection, `Class.forName(...)` with a dynamically-computed name, or `ServiceLoader`-based service loading, all of which are invisible to `jdeps`'s static constant-pool analysis. Always review and refine the generated file by hand — tightening `exports` to the genuinely intended public API, and adding any `uses`/`provides` directives `jdeps` couldn't infer.

- `jdeps -s` (or `--summary`) prints a condensed, module-to-module-only summary without the full per-class breakdown — useful for a quick, high-level view of a large JAR's dependencies before drilling into specifics.
- `jdeps --jdk-internals` is specifically the recommended first command to run before any JDK version upgrade, not just before modularizing — it surfaces every internal-API dependency that's a genuine risk of breaking on the target JDK version, regardless of whether you ever intend to add a `module-info.java` at all.
- `jdeps` can analyze an entire classpath or a directory of JARs at once (`jdeps -cp lib/*.jar myapp.jar`), useful for auditing a whole application's dependency tree rather than one library JAR in isolation.
- The generated `module-info.java`'s `requires` lines only cover what `jdeps` can statically observe in the compiled bytecode — if a dependency is only reached conditionally (a feature flag, an optional integration only exercised at runtime under specific conditions), it may still show up as a `requires` if the *reference* exists in the bytecode at all, even if that code path is rarely or never actually executed in practice.
- Running `jdeps` as part of a CI pipeline (failing the build if `--jdk-internals` reports any new internal-API usage) is a practical way to prevent a codebase from silently reaccumulating exactly the kind of unsupported-API dependency that made past JDK upgrades painful in the first place.
