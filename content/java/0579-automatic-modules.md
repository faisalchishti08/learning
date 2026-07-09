---
card: java
gi: 579
slug: automatic-modules
title: Automatic modules
---

## 1. What it is

An **automatic module** is a plain JAR — one with no `module-info.class` at all — that gets treated as a module simply by being placed on the module path instead of the classpath. The JVM synthesizes a module name for it (usually derived from the JAR's filename) and automatically exports **every** package inside it, unconditionally, to every other module. It's a bridge mechanism: a way for non-modularized JARs to participate in the module system, without their authors having written a single line of `module-info.java`.

## 2. Why & when

When Java 9 shipped, the overwhelming majority of published libraries had no `module-info.java` — the module system had to accommodate that reality, or adoption would have been impossible. Automatic modules solve the immediate problem: drop any ordinary JAR onto the module path, and other, real modules can `requires` it by name and use it, as if it had been a real module all along. This makes it practical to build a fully modular application (`module-info.java` in your own code) that depends on libraries which haven't modularized yet — extremely common in any real project, since even years after Java 9, plenty of libraries never add explicit module support at all. Automatic modules matter whenever you're building a modular application on top of a dependency tree that includes ordinary, non-modular JARs.

## 3. Core concept

```
// A plain JAR: mylib-2.3.jar, no module-info.class inside it, placed on --module-path

module app {
    requires mylib; // works! "mylib" is the AUTOMATIC MODULE NAME derived from the JAR filename
}
```

The automatic module name is derived by stripping the version number and file extension from the JAR filename and converting remaining separators to dots (`mylib-2.3.jar` → `mylib`; `commons-lang3-3.12.jar` → `commons.lang3`) — unless the JAR itself specifies an explicit `Automatic-Module-Name` entry in its `META-INF/MANIFEST.MF`, which library authors can add specifically to give consumers a stable, predictable module name in advance of full modularization.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A plain JAR on the module path becomes an automatic module with a derived name and every package exported">
  <text x="20" y="25" fill="#8b949e" font-size="11" font-family="sans-serif">mylib-2.3.jar (no module-info.class) placed on --module-path:</text>
  <rect x="20" y="35" width="600" height="60" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="330" y="60" fill="#f0883e" font-size="12" text-anchor="middle" font-family="monospace">automatic module "mylib"</text>
  <text x="330" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">ALL packages exported unconditionally, name derived from filename</text>

  <text x="20" y="130" fill="#8b949e" font-size="11" font-family="sans-serif">Same JAR on the classpath instead: no module identity at all — just unnamed-module code.</text>

  <text x="20" y="160" fill="#8b949e" font-size="10" font-family="sans-serif">requires mylib; in another module's module-info.java resolves to whichever form is on the module path.</text>
</svg>

The same JAR behaves completely differently depending on which path it's placed on — no code inside the JAR changes at all.

## 5. Runnable example

Scenario: a real, modular application that wants to depend on a small "CSV parsing" utility JAR that has never been modularized — starting with the JAR on the classpath (works, but not usable by a real module), then moving it to the module path as an automatic module (works, name derived from the filename), then giving it an explicit `Automatic-Module-Name` for a stable, predictable name independent of the exact filename.

### Level 1 — Basic

```java
// File: csvutil/com/csvutil/CsvParser.java — this becomes a plain JAR, "csvutil-1.0.jar", no module-info.java
package com.csvutil;
import java.util.List;
import java.util.Arrays;

public class CsvParser {
    public static List<String> parseLine(String line) {
        return Arrays.asList(line.split(","));
    }
}
```

```java
// File: app/com/myapp/Main.java — classpath consumer, no modules involved at all
package com.myapp;
import com.csvutil.CsvParser;

public class Main {
    public static void main(String[] args) {
        System.out.println(CsvParser.parseLine("a,b,c"));
    }
}
```

**How to run:**
```
javac -d csvout csvutil/com/csvutil/CsvParser.java
jar --create --file csvutil-1.0.jar -C csvout .
javac -cp csvutil-1.0.jar -d appout app/com/myapp/Main.java
java -cp csvutil-1.0.jar:appout com.myapp.Main
```

Expected output:
```
[a, b, c]
```

This is the plain classpath baseline: `csvutil-1.0.jar` has no `module-info.class`, and everything runs exactly as pre-module Java always did — both `CsvParser` and `Main` land in the unnamed module, with no `requires`/`exports` concept involved at all. This works, but a genuinely modular application (with its own `module-info.java`) cannot `requires` this JAR by name while it sits on the classpath.

### Level 2 — Intermediate

```java
// File: app/module-info.java — a REAL module wanting to depend on the same JAR
module app {
    requires csvutil; // "csvutil" — the AUTOMATIC MODULE NAME derived from csvutil-1.0.jar
}
```

```java
// File: app/com/myapp/Main.java — same logic, now inside a real module
package com.myapp;
import com.csvutil.CsvParser;

public class Main {
    public static void main(String[] args) {
        System.out.println(CsvParser.parseLine("a,b,c"));
    }
}
```

**How to run:** move `csvutil-1.0.jar` (built identically to Level 1, still with no `module-info.class` inside it) onto the **module path** instead of the classpath:
```
javac -d appout --module-path csvutil-1.0.jar --module-source-path . $(find app -name "*.java")
java --module-path csvutil-1.0.jar:appout -m app/com.myapp.Main
```

Expected output:
```
[a, b, c]
```

The real-world concern this adds: **the exact same, unmodified JAR file** now works as a dependency of a real module. `requires csvutil;` in `app`'s `module-info.java` resolves successfully because placing `csvutil-1.0.jar` on `--module-path` (instead of `-cp`) makes the JVM treat it as an automatic module, synthesizing the name `csvutil` from its filename (stripping the `-1.0` version suffix and `.jar` extension) and exporting every package inside it — including `com.csvutil` — unconditionally to any module that requires it.

### Level 3 — Advanced

```
# Inside the JAR's META-INF/MANIFEST.MF, added before packaging:
Automatic-Module-Name: com.csvutil.parser
```

```java
// File: app/module-info.java — requires the EXPLICIT name, independent of the exact jar filename
module app {
    requires com.csvutil.parser;
}
```

**How to run:** rebuild the JAR with the manifest entry, so its filename can change freely without breaking consumers:
```
javac -d csvout csvutil/com/csvutil/CsvParser.java
jar --create --file csvutil-2.0-SNAPSHOT.jar --manifest MANIFEST.MF -C csvout .
javac -d appout --module-path csvutil-2.0-SNAPSHOT.jar --module-source-path . $(find app -name "*.java")
java --module-path csvutil-2.0-SNAPSHOT.jar:appout -m app/com.myapp.Main
```

Expected output:
```
[a, b, c]
```

This handles the production-flavoured concern of **filename-derived names being fragile**: a plain automatic module's name is tied to its exact filename, so a version bump (`csvutil-1.0.jar` → `csvutil-2.0.jar`) or a differently-formatted filename (`csvutil-2.0-SNAPSHOT.jar`, which would otherwise derive an awkward name) could silently change the derived module name and break every consumer's `requires` line. Adding `Automatic-Module-Name: com.csvutil.parser` to the JAR's manifest fixes the name permanently, independent of filename — `app` now requires `com.csvutil.parser`, and this keeps working even though the actual filename changed to `csvutil-2.0-SNAPSHOT.jar`.

## 6. Walkthrough

Execution starts with the build commands in Level 3. `jar --create --file csvutil-2.0-SNAPSHOT.jar --manifest MANIFEST.MF -C csvout .` packages the compiled `CsvParser.class` into a JAR, additionally merging in the custom `MANIFEST.MF` containing the `Automatic-Module-Name: com.csvutil.parser` entry — this is a purely declarative addition to the JAR's manifest; no `module-info.class` is present, so this JAR is still, technically, not a real named module — it's still an automatic module, just one with an explicitly-chosen name instead of a filename-derived one.

`javac -d appout --module-path csvutil-2.0-SNAPSHOT.jar --module-source-path . ...` compiles `app`'s source. When the compiler processes `app/module-info.java`'s `requires com.csvutil.parser;`, it scans the module path, finds `csvutil-2.0-SNAPSHOT.jar`, opens its manifest, and reads the `Automatic-Module-Name` entry — rather than deriving a name from the filename (which would otherwise produce something like `csvutil.2.0.SNAPSHOT`, since `SNAPSHOT` isn't recognized as a plain version suffix the way a simple numeric version is), it uses the explicitly declared name `com.csvutil.parser` directly.

```
Automatic module naming, in priority order:

1. JAR's META-INF/MANIFEST.MF has "Automatic-Module-Name: X"  -> use X exactly, as declared
2. Otherwise: derive from filename (strip version suffix + .jar, replace
   remaining separators with dots)                              -> e.g. csvutil-1.0.jar -> csvutil
```

Because the manifest entry is present, path 1 applies: the module is named `com.csvutil.parser`, matching exactly what `app`'s `module-info.java` requires. Compilation succeeds, and `Main.java`'s `import com.csvutil.CsvParser` resolves — automatic modules export every package unconditionally, so `com.csvutil` (the actual Java package inside the JAR, a separate concept from the module's *name*, `com.csvutil.parser`) is visible without any `exports` declaration needed, since the JAR has no `module-info.class` to declare one in the first place.

At runtime, `java --module-path csvutil-2.0-SNAPSHOT.jar:appout -m app/com.myapp.Main` launches `Main.main`. `CsvParser.parseLine("a,b,c")` calls `"a,b,c".split(",")`, producing the array `["a", "b", "c"]`, wrapped via `Arrays.asList(...)` into a `List<String>`. `System.out.println(...)` calls that list's `toString()`, printing `"[a, b, c]"`.

The core lesson across all three levels: the exact same `CsvParser` bytecode, unmodified in any of the levels, behaves as plain classpath code, as a filename-named automatic module, or as an explicitly-named automatic module — purely based on which path it's placed on and what (if anything) its manifest declares, with zero source code changes required in the library itself.

## 7. Gotchas & takeaways

> Automatic modules export **every** package inside the JAR unconditionally — there is no way to hide "internal" packages the way a real module's `module-info.java` can, since there's no `module-info.class` at all to declare such boundaries in. This is a meaningful trade-off: an automatic module gives you cross-module `requires` compatibility, but none of the actual encapsulation benefits that motivated the module system in the first place — treat it as a compatibility bridge, not a substitute for genuine modularization.

- If a JAR's filename doesn't cleanly derive a valid Java identifier-like module name (unusual characters, ambiguous version formatting), the JVM either derives an imperfect name or, in some cases, refuses to treat the JAR as a valid automatic module at all — `Automatic-Module-Name` is the reliable fix for library authors who want to guarantee a stable name ahead of full modularization.
- Library authors commonly add `Automatic-Module-Name` as an intermediate step *before* fully modularizing — it gives consumers a stable module name to depend on immediately, with the freedom to later ship a real `module-info.class` using that same name without breaking anyone's `requires` line.
- Automatic modules **do** participate in `requires transitive` and can themselves be depended on transitively — from the perspective of a module requiring one, it behaves like any other named module for dependency-graph purposes, just with looser internal guarantees.
- Two automatic modules (or an automatic module and a real module) that happen to contain overlapping packages ("split packages") are rejected by the module system at resolution time — this is one of several cases where module-path behavior is stricter than classpath behavior, where such overlaps merge silently instead.
- An automatic module can read the unnamed module's classpath contents in some configurations (a relaxation not available to genuine named modules), part of the broader set of compatibility exceptions specifically designed to ease the transition from classpath-only applications to fully modular ones.
