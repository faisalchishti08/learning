---
card: java
gi: 645
slug: nashorn-deprecated
title: Nashorn deprecated
---

## 1. What it is

**Nashorn** is the lightweight, high-performance JavaScript engine that was built into the JDK from Java 8 through Java 14. In Java 11, Nashorn was **deprecated** (JEP 335), marking the beginning of its removal from the JDK. The deprecation was driven by the difficulty of maintaining a JavaScript engine that tracked the rapidly-evolving ECMAScript specification (Nashorn implemented ECMAScript 5.1, while the web had moved to ES6+). The `jdk.scripting.nashorn` module and the `jjs` command-line tool were deprecated in Java 11 and removed entirely in Java 15. The recommended replacement is **GraalJS** (part of GraalVM), which supports the latest ECMAScript standards and offers better performance.

## 2. Why & when

Nashorn served a real need — running JavaScript on the JVM for scripting, build tooling (Ant, Gradle scripts), and server-side rendering. However, keeping pace with ECMAScript evolution proved unsustainable for the JDK team: ES6 added classes, arrow functions, modules, generators, and more — each requiring significant engine rework. Rather than ship an outdated JS engine indefinitely, the JDK team deprecated Nashorn and pointed users to GraalJS (which runs on GraalVM or as a standalone JAR). If your application uses Nashorn (via `ScriptEngine` with `"nashorn"` or the `jjs` tool), plan to migrate to GraalJS before upgrading past Java 14.

## 3. Core concept

```java
// Before Java 11 (worked, but deprecated from Java 11):
ScriptEngineManager manager = new ScriptEngineManager();
ScriptEngine engine = manager.getEngineByName("nashorn");
engine.eval("print('Hello from JavaScript')");

// Java 11+ deprecated — still works but prints deprecation warning:
// Warning: Nashorn engine is deprecated and will be removed in a future release

// Java 15+ removed — throws NullPointerException (engine not found)

// Modern replacement (GraalJS):
// 1. Add dependency: org.graalvm.js:js
// 2. Use GraalJSScriptEngine or the polyglot API
```

The `jjs` command-line tool (`jjs script.js`) is also deprecated in Java 11 and removed in Java 15.

## 4. Diagram

<svg viewBox="0 0 560 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Nashorn deprecation timeline: deprecated in 11, removed in 15, replaced by GraalJS">
  <rect x="10" y="10" width="540" height="120" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="25" width="100" height="35" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="70" y="47" fill="#3fb950" font-size="10" text-anchor="middle" font-family="monospace">Java 8–10</text>
  <text x="70" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">Nashorn active</text>

  <text x="130" y="45" fill="#8b949e" font-size="14" font-family="monospace">→</text>

  <rect x="145" y="20" width="110" height="45" rx="4" fill="#0d1117" stroke="#f0883e"/>
  <text x="200" y="40" fill="#f0883e" font-size="10" text-anchor="middle" font-family="monospace">Java 11–14</text>
  <text x="200" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">Nashorn deprecated</text>

  <text x="265" y="45" fill="#8b949e" font-size="14" font-family="monospace">→</text>

  <rect x="280" y="20" width="100" height="45" rx="4" fill="#0d1117" stroke="#f85149"/>
  <text x="330" y="40" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">Java 15+</text>
  <text x="330" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">Nashorn removed</text>

  <text x="395" y="45" fill="#8b949e" font-size="14" font-family="monospace">→</text>

  <rect x="410" y="25" width="130" height="35" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="475" y="47" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">GraalJS</text>
  <text x="475" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">recommended replacement</text>

  <text x="20" y="100" fill="#8b949e" font-size="9" font-family="sans-serif">Deprecated: jdk.scripting.nashorn module, jjs tool, ScriptEngine "nashorn" name</text>
  <text x="20" y="118" fill="#3fb950" font-size="9" font-family="sans-serif">Migrate to: GraalJS (org.graalvm.js:js) — supports ES2023, better performance, polyglot interop</text>
</svg>

Nashorn's lifecycle: introduced in Java 8, deprecated in Java 11, removed in Java 15. The recommended migration path is GraalJS.

## 5. Runnable example

Scenario: detecting Nashorn availability and demonstrating the deprecation warning — starting with basic detection, extending to migration guidance, and finally testing alternative JS engines.

### Level 1 — Basic

```java
// File: NashornDeprecationDemo.java
import javax.script.*;

public class NashornDeprecationDemo {
    public static void main(String[] args) {
        System.out.println("=== Nashorn Deprecation Check ===\n");
        System.out.println("Java version: " + System.getProperty("java.version"));

        ScriptEngineManager manager = new ScriptEngineManager();

        // Try to get the Nashorn engine
        ScriptEngine nashorn = manager.getEngineByName("nashorn");

        if (nashorn == null) {
            System.out.println("Nashorn is NOT available (removed in Java 15+).");
            System.out.println("Use GraalJS instead: org.graalvm.js:js");
        } else {
            System.out.println("Nashorn IS available (deprecated in Java 11-14).");
            try {
                nashorn.eval("print('JavaScript executed via Nashorn')");
                System.out.println("(If you saw a deprecation warning above, you are on Java 11-14)");
            } catch (ScriptException e) {
                System.out.println("Error: " + e.getMessage());
            }
        }

        // List all available script engines
        System.out.println("\nAvailable script engines:");
        for (ScriptEngineFactory factory : manager.getEngineFactories()) {
            System.out.println("  " + factory.getEngineName() +
                " (" + factory.getLanguageName() + ")");
        }
    }
}
```

**How to run:** `java NashornDeprecationDemo.java`

Expected output (Java 17+):
```
=== Nashorn Deprecation Check ===

Java version: 17.0...
Nashorn is NOT available (removed in Java 15+).
Use GraalJS instead: org.graalvm.js:js

Available script engines:
  (varies by JDK distribution)
```

### Level 2 — Intermediate

```java
// File: NashornMigration.java
import javax.script.*;

public class NashornMigration {
    public static void main(String[] args) {
        System.out.println("=== Migrating from Nashorn ===\n");

        // 1. Detect if Nashorn was used
        System.out.println("Step 1: Check if your app uses Nashorn");
        System.out.println("  Search for:");
        System.out.println("  - ScriptEngineManager.getEngineByName(\"nashorn\")");
        System.out.println("  - ScriptEngineManager.getEngineByExtension(\"js\")");
        System.out.println("  - jjs command-line invocations");
        System.out.println("  - new NashornScriptEngineFactory()");
        System.out.println();

        // 2. Migration options
        System.out.println("Step 2: Choose migration path\n");

        System.out.println("Option A: GraalJS (recommended)");
        System.out.println("  Add dependency: org.graalvm.js:js:23.0.0");
        System.out.println("  API remains similar via ScriptEngine interface:");
        System.out.println("    ScriptEngine engine = new ScriptEngineManager()");
        System.out.println("        .getEngineByName(\"graal.js\");");
        System.out.println("  Or use the polyglot API for better performance:");
        System.out.println("    try (Context ctx = Context.create(\"js\")) {");
        System.out.println("        Value result = ctx.eval(\"js\", \"40 + 2\");");
        System.out.println("    }");
        System.out.println();

        System.out.println("Option B: Alternative JVM languages");
        System.out.println("  - Groovy (groovy.lang.GroovyShell)");
        System.out.println("  - Kotlin Scripting (kotlin.script.experimental)");
        System.out.println("  - JShell API (built-in Java REPL for Java snippets)");
        System.out.println();

        // 3. Compatibility note
        System.out.println("Step 3: API differences");
        System.out.println("  Nashorn:   importClass, Java.type, Java.from");
        System.out.println("  GraalJS:   Java.type (same), but use polyglot bindings for");
        System.out.println("             advanced Java interop");
        System.out.println("  Key difference: Nashorn's JSObject/JSException classes");
        System.out.println("  are removed. GraalJS uses Value/Exception classes.");
    }
}
```

**How to run:** `java NashornMigration.java`

Expected output:
```
=== Migrating from Nashorn ===

Step 1: Check if your app uses Nashorn
  Search for:
  - ScriptEngineManager.getEngineByName("nashorn")
  ...

Step 2: Choose migration path
  ...

Step 3: API differences
  ...
```

### Level 3 — Advanced

```java
// File: NashornAdvanced.java
public class NashornAdvanced {
    public static void main(String[] args) {
        System.out.println("=== Nashorn — Why It Was Removed ===\n");

        System.out.println("1. ECMAScript Evolution:");
        System.out.println("   Nashorn implemented ECMAScript 5.1 (2011 standard).");
        System.out.println("   ECMAScript 6 (2015) added classes, arrow functions,");
        System.out.println("   modules, generators, proxies, and much more.");
        System.out.println("   Maintaining pace with TC39 proposals proved unsustainable.");
        System.out.println();

        System.out.println("2. Maintenance Burden:");
        System.out.println("   The JDK team estimated that full ES6 support would");
        System.out.println("   require a near-rewrite of Nashorn. With GraalVM already");
        System.out.println("   providing a high-performance ES2023-compliant JS engine,");
        System.out.println("   duplicating that effort in the JDK was wasteful.");
        System.out.println();

        System.out.println("3. GraalJS Advantages:");
        System.out.println("   - Supports ECMAScript 2023 (latest)");
        System.out.println("   - Faster than Nashorn (JIT-compiled via Graal)");
        System.out.println("   - Polyglot interop (JS can call Python, R, Ruby, Java)");
        System.out.println("   - Node.js compatibility mode");
        System.out.println("   - Standalone or embedded in the JDK (GraalVM)");
        System.out.println();

        System.out.println("4. Nashorn Standalone:");
        System.out.println("   Nashorn was split into a standalone project:");
        System.out.println("   github.com/openjdk/nashorn");
        System.out.println("   But it is NOT actively maintained — do not use for new apps.");
        System.out.println();

        System.out.println("5. jjs Replacement:");
        System.out.println("   Old:  jjs script.js");
        System.out.println("   New:  js script.js  (GraalVM's launcher)");
        System.out.println("   Or:   node script.js (if using Node.js API)");
        System.out.println();

        System.out.println("6. Timeline Summary:");
        System.out.println("   Java 8  (2014): Nashorn introduced (JEP 174)");
        System.out.println("   Java 11 (2018): Nashorn deprecated (JEP 335)");
        System.out.println("   Java 15 (2020): Nashorn removed (JEP 372)");
        System.out.println("   Today:          Use GraalJS or other JS-on-JVM engines");
    }
}
```

**How to run:** `java NashornAdvanced.java`

Expected output:
```
=== Nashorn — Why It Was Removed ===

1. ECMAScript Evolution:
   ...

2. Maintenance Burden:
   ...

3. GraalJS Advantages:
   ...

4. Nashorn Standalone:
   ...

5. jjs Replacement:
   ...

6. Timeline Summary:
   ...
```

The production-flavoured hard cases: (1) **Detection** — if your app calls `getEngineByName("nashorn")`, it will return `null` on Java 15+ without throwing an error (silent failure). Check for `null`. (2) **Standalone Nashorn** — the openjdk/nashorn GitHub repo exists but is not actively maintained; it's a dead end. Migrate to GraalJS. (3) **GraalJS vs JDK** — GraalJS can run on any JDK as a library (not just GraalVM). Add `org.graalvm.js:js` as a Maven dependency and use it via `ScriptEngine`.

## 6. Walkthrough

Tracing Nashorn deprecation detection:

1. `new ScriptEngineManager()` creates a manager that discovers all `ScriptEngineFactory` implementations on the classpath/module path using the ServiceLoader mechanism.

2. `manager.getEngineByName("nashorn")` iterates through discovered factories calling `factory.getNames()` to find one containing `"nashorn"`.

3. On Java 8–10: the JDK's `jdk.scripting.nashorn` module provides `NashornScriptEngineFactory`, which returns itself for `"nashorn"`, `"Nashorn"`, `"js"`, `"JS"`, `"JavaScript"`, `"javascript"`, `"ECMAScript"`, `"ecmascript"`. The engine is returned.

4. On Java 11–14: same as above, but the module is marked `@Deprecated(forRemoval=true)`. A deprecation warning is printed to stderr the first time the engine is loaded. The engine still works.

5. On Java 15+: the `jdk.scripting.nashorn` module no longer exists in the JDK. `getEngineByName("nashorn")` returns `null`. If the code doesn't null-check, a `NullPointerException` is thrown when calling `engine.eval(...)`.

Data flow: application code → `ScriptEngineManager` → ServiceLoader → finds (or doesn't find) Nashorn factory → returns engine or null → application handles result.

## 7. Gotchas & takeaways

> Calling `getEngineByName("nashorn")` on Java 15+ silently returns `null` — there is **no exception and no deprecation warning** because the engine is simply not there. If your code doesn't null-check, you get a `NullPointerException` on the next line. Always null-check after `getEngineByName()`.

- Nashorn is **deprecated** in Java 11 (warnings) and **removed** in Java 15 (engine not found). The deprecation was announced by JEP 335.
- The `jjs` command-line tool is also removed in Java 15. Shell scripts using `jjs` must be rewritten to use GraalVM's `js` launcher or Node.js.
- GraalJS is the official replacement. It supports ECMAScript 2023, runs on any JDK 11+ (not just GraalVM), and provides a `ScriptEngine` implementation under the name `"graal.js"`.
- The standalone Nashorn project (github.com/openjdk/nashorn) exists but is **not actively maintained** — do not use it for new projects. It exists only for legacy compatibility.
- Nashorn was not the only scripting engine removed. The `jdk.scripting.nashorn.shell` module (which provided `jjs`) was also removed, and the Rhino JavaScript engine (which preceded Nashorn) was never part of OpenJDK.
