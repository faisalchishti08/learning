---
card: java
gi: 578
slug: module-path-vs-classpath
title: Module path vs classpath
---

## 1. What it is

The **module path** (`--module-path` / `-p`) and the **classpath** (`-cp` / `-classpath`) are two different mechanisms for telling `javac` and `java` where to find compiled classes — but they behave completely differently. The classpath is a flat bag of classes and JARs with no module boundaries enforced at all; the module path is scanned for named modules (real modules with `module-info.class`, or "automatic modules" for plain JARs), and everything on it participates in the module system's `requires`/`exports` rules.

## 2. Why & when

Java 9 didn't remove the classpath — it kept it fully working, for backward compatibility with the entire pre-module ecosystem, and introduced the module path as a parallel, opt-in mechanism. Which one you use (or how you combine both) determines whether your code gets module-system enforcement at all: code compiled and run purely on the classpath behaves exactly like pre-Java-9 Java, with no `requires`/`exports` checks, because it isn't part of any named module (it lands in a special catch-all called the **unnamed module**). Code compiled and run on the module path, with a real `module-info.java`, gets full module-system behavior: encapsulation, explicit dependencies, all of it. Understanding the difference matters for every practical decision about adopting modules: whether to modularize a project at all, how to mix modular and non-modular dependencies in one build, and why a JAR that works fine on the classpath can suddenly behave differently once moved to the module path.

## 3. Core concept

```
javac -cp lib1.jar:lib2.jar -d out src/*.java     # classpath: flat, no module enforcement
java  -cp lib1.jar:lib2.jar:out com.myapp.Main     # unnamed module — sees everything, exports nothing to anyone

javac --module-path mods -d out --module-source-path src $(find src -name "*.java")   # module path: real modules
java  --module-path mods:out -m app/com.myapp.Main                                     # named modules — requires/exports enforced
```

Both mechanisms can be used together (`-cp` for some dependencies, `--module-path` for others) — the JVM supports "mixed" applications where some code is modular and some remains on the classpath, which is the normal transitional state for most real projects migrating to modules gradually.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Classpath is a flat pool of classes with no enforcement; module path is scanned for named modules with requires/exports enforced">
  <text x="20" y="25" fill="#8b949e" font-size="11" font-family="sans-serif">Classpath (-cp): flat pool, no boundaries</text>
  <rect x="20" y="35" width="600" height="45" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="330" y="63" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">lib1.jar + lib2.jar + out/  -&gt;  all merged into ONE "unnamed module"</text>

  <text x="20" y="105" fill="#8b949e" font-size="11" font-family="sans-serif">Module path (--module-path): scanned for named modules, boundaries enforced</text>
  <rect x="20" y="115" width="185" height="45" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="112" y="143" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">module app</text>
  <rect x="220" y="115" width="185" height="45" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="312" y="143" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">module billing</text>
  <rect x="420" y="115" width="185" height="45" rx="8" fill="#1c2430" stroke="#d2a8ff"/>
  <text x="512" y="143" fill="#d2a8ff" font-size="10" text-anchor="middle" font-family="monospace">module java.sql</text>
</svg>

Same JVM, two fundamentally different lookup-and-enforcement mechanisms — which one a JAR ends up on changes what rules apply to it.

## 5. Runnable example

Scenario: the same tiny "greeter" library and application, built and run three ways — first entirely on the classpath (pre-module behavior, everything visible to everything), then entirely on the module path (full enforcement), then a mixed setup showing a classpath-based application consuming a genuine module.

### Level 1 — Basic

```java
// File: src/com/greetlib/Greeter.java — a plain library class, no module-info.java at all
package com.greetlib;

public class Greeter {
    public String greet(String name) { return "Hello, " + name + "!"; }
}
```

```java
// File: src/com/myapp/Main.java
package com.myapp;
import com.greetlib.Greeter;

public class Main {
    public static void main(String[] args) {
        System.out.println(new Greeter().greet("World"));
    }
}
```

**How to run:**
```
javac -d out src/com/greetlib/Greeter.java src/com/myapp/Main.java
java -cp out com.myapp.Main
```

Expected output:
```
Hello, World!
```

This is plain classpath compilation and execution — no `module-info.java` anywhere, no `--module-path`, no `-m`. Both classes end up in the JVM's **unnamed module**: a special, implicit module that can see (and be seen by) everything else on the classpath, with none of the `requires`/`exports` rules enforced. This is exactly how all Java code worked before Java 9, and it's still the default if you never opt into modules at all.

### Level 2 — Intermediate

```java
// File: greetlib/module-info.java
module greetlib {
    exports com.greetlib;
}
```

```java
// File: greetlib/com/greetlib/Greeter.java — same class, now inside a real module
package com.greetlib;

public class Greeter {
    public String greet(String name) { return "Hello, " + name + "!"; }
}
```

```java
// File: app/module-info.java
module app {
    requires greetlib;
}
```

```java
// File: app/com/myapp/Main.java — identical logic to Level 1
package com.myapp;
import com.greetlib.Greeter;

public class Main {
    public static void main(String[] args) {
        System.out.println(new Greeter().greet("World"));
    }
}
```

**How to run:**
```
javac -d out --module-source-path . $(find greetlib app -name "*.java")
java --module-path out -m app/com.myapp.Main
```

Expected output:
```
Hello, World!
```

The real-world concern this adds: the exact same program logic, but now compiled and run entirely on the **module path** — `--module-path out` tells `java` to scan `out` for named modules (it finds `greetlib` and `app`, each with its own `module-info.class`), and `-m app/com.myapp.Main` explicitly names which module's main class to launch. The output is identical to Level 1, but this run is now fully governed by `requires`/`exports` — if `greetlib` hadn't exported `com.greetlib`, this would fail to compile, exactly as covered in the `exports` topic.

### Level 3 — Advanced

```java
// File: greetlib/module-info.java — UNCHANGED, still a real module
module greetlib {
    exports com.greetlib;
}
```

```java
// File: greetlib/com/greetlib/Greeter.java — UNCHANGED
package com.greetlib;

public class Greeter {
    public String greet(String name) { return "Hello, " + name + "!"; }
}
```

```java
// File: legacyapp/com/myapp/Main.java — a NON-modular consumer, no module-info.java, uses greetlib
package com.myapp;
import com.greetlib.Greeter;

public class Main {
    public static void main(String[] args) {
        System.out.println(new Greeter().greet("Mixed World"));
    }
}
```

**How to run:** compile `greetlib` as a module, then compile the plain `Main.java` against it on the **classpath**, and run with both a module path and a classpath, explicitly adding `greetlib` to the runtime with `--add-modules`:
```
javac -d modout --module-source-path . $(find greetlib -name "*.java")
javac -d clsout --module-path modout -cp modout/greetlib legacyapp/com/myapp/Main.java
java --module-path modout --add-modules greetlib -cp clsout com.myapp.Main
```

Expected output:
```
Hello, Mixed World!
```

This handles the production-flavoured, and very common, **mixed** case: `greetlib` is a real, fully modular library, while `Main` is ordinary, non-modular classpath code (the realistic situation for a project just beginning to adopt modules, or consuming a modular library from legacy code that hasn't been modularized yet). The classpath-based `Main` class lands in the unnamed module, which — once a module is actually part of the resolved module graph — is allowed to read that module's exports freely, so it can `import com.greetlib.Greeter` and use it, even though `Main` itself has no `module-info.java` and no `requires` declaration of any kind. Getting `greetlib` *into* that resolved graph in the first place is exactly what `--add-modules greetlib` is for, as the walkthrough below explains.

## 6. Walkthrough

Execution starts with the three build/run commands in Level 3, compiling `greetlib` as a genuine named module and `Main.java` as ordinary classpath code, then launching with both a module path and a classpath specified simultaneously.

The first `javac` invocation compiles `greetlib`'s module-aware source (`module-info.java` plus `Greeter.java`) into `modout`, producing a proper named module with a `module-info.class`.

The second `javac` invocation compiles `Main.java` — which has no `module-info.java` — using `--module-path modout` (so the compiler can find `greetlib` as a module) combined with `-cp modout/greetlib` (so the compiler can also resolve `Greeter` via the classpath route for this classpath-based compilation unit). `Main.class` ends up in `clsout`, with no module identity of its own. This compile step succeeds without needing `--add-modules`, because `javac` resolves whatever the source file actually imports, regardless of root-module rules.

At runtime, `java --module-path modout -cp clsout com.myapp.Main` — **without** `--add-modules` — fails with `NoClassDefFoundError: com/greetlib/Greeter`. This is the detail worth understanding: simply putting a module on `--module-path` does not make it part of the running application. When the JVM launches an unnamed-module class (via `-cp` and a plain class name, rather than `-m module/Class`), its default "root modules" are just the platform's own modules — application modules sitting on `--module-path` are only pulled in if something roots them, either by being the module launched via `-m`, by being required (transitively) by such a module, or by being named explicitly via `--add-modules`.

```
Without --add-modules:                        With --add-modules greetlib:
--module-path modout  -> greetlib PRESENT      --module-path modout  -> greetlib PRESENT
                          but NOT RESOLVED                              and EXPLICITLY ROOTED
-cp clsout -> Main runs in unnamed module       -cp clsout -> Main runs in unnamed module
Main calls Greeter -> NoClassDefFoundError      Main calls Greeter -> resolves, runs fine
```

With `--add-modules greetlib` added, `greetlib` becomes one of the resolved graph's root modules for this launch. Now the unnamed module — which, once a module is actually part of the resolved graph, is permitted to read that module's exported packages — can successfully resolve `com.greetlib.Greeter` at class-loading time. `Main.main` runs: `import com.greetlib.Greeter` (already resolved at compile time) and `new Greeter().greet("Mixed World")` execute normally, `Greeter.greet(...)` returns `"Hello, Mixed World!"`, and `main` prints it.

Note the asymmetry this demonstrates: a named module (like `greetlib`) can be used by classpath code once it's actually resolved into the running application's module graph — but that resolution isn't automatic just because a module happens to sit on `--module-path`; it must be reached by root-module rules (`-m`, transitive `requires`, or `--add-modules`). This is a common source of confusion when first mixing classpath and module-path code: the compiler is comparatively permissive about resolving imports, but the runtime's module-graph resolution is stricter about which modules actually get included.

## 7. Gotchas & takeaways

> The unnamed module (classpath code) can freely use any *resolved* named module's exported packages — but getting a module resolved in the first place takes an explicit root (`-m`, a transitive `requires` from it, or `--add-modules`), as the Level 3 walkthrough shows. This convenience is exactly why mixing classpath and module-path code is meant as a **transitional** strategy, not a permanent architecture — code sitting in the unnamed module gets none of the module system's own protections (no `exports` enforcement *for it*, since it isn't a module itself and has no `module-info.java` of its own to declare boundaries with), so a codebase that stays half-migrated indefinitely keeps the enforcement benefits for its modular half only.

- Merely listing a module on `--module-path` does not make it part of the running application when launching via a classpath main class (`-cp ... com.myapp.Main` rather than `-m module/Class`) — it must additionally be reached through root-module resolution (named via `-m`, required transitively from the module named via `-m`, or listed explicitly with `--add-modules`), or it's simply never resolved and code trying to use it fails with `NoClassDefFoundError` at runtime despite compiling fine, as demonstrated in the Level 3 walkthrough.
- A plain JAR placed on the **module path** (rather than the classpath) without its own `module-info.class` becomes an **automatic module** — the JVM synthesizes a module name from the JAR's filename and exports *all* of its packages unconditionally; this is a separate, related mechanism (covered in its own topic) distinct from both true named modules and classpath/unnamed-module code.
- `-cp` and `--module-path` are genuinely independent JVM options and can both be supplied in the same `java`/`javac` invocation, exactly as shown in Level 3 — this is the standard way to run a partially-modularized application.
- Two JARs on the classpath that happen to define classes in the same package silently merge (classpath has no "split package" detection) — the module path explicitly forbids this ("split packages," where the same package appears in two different modules, is a hard error), one of several stricter guarantees the module path provides over the classpath.
- `-m app/com.myapp.Main` (module path launch) explicitly names both the module and the fully-qualified main class; `-cp ... com.myapp.Main` (classpath launch) only ever names the class, since there's no module to specify — this syntax difference is a quick visual cue for which mode a given command is using.
- Migrating a large existing classpath-based application to modules is rarely an all-at-once switch — the mixed mode demonstrated in Level 3 is the normal, supported way to modularize incrementally, converting one library at a time to a real module while the rest of the application remains on the classpath during the transition.
