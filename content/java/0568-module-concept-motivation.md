---
card: java
gi: 568
slug: module-concept-motivation
title: Module concept & motivation
---

## 1. What it is

A **Java module**, introduced in Java 9's Project Jigsaw, is a named, self-describing group of packages with an explicit declaration of what it needs from other modules (`requires`) and what it exposes to other modules (`exports`). It sits one level above packages and JARs: where a JAR is just a zip file with no enforced boundaries, a module is a JAR *plus* a `module-info.java` file that the JVM actually reads and enforces at compile time and runtime.

## 2. Why & when

Before modules, Java had two long-standing structural problems. First, the **classpath** offered no real encapsulation: any public class in any JAR was accessible to any other JAR on the classpath, so "internal" packages (like `com.mycompany.internal.*`) were public in name only — nothing stopped external code from importing and using them, and libraries had no way to say "this package is not for you." Second, there was no reliable way to know what a JAR actually depended on, or to detect missing/conflicting dependencies before runtime — you'd only discover a missing class when the code that used it actually ran and threw `NoClassDefFoundError`, sometimes deep in production. The module system fixes both: `exports` makes non-exported packages genuinely inaccessible from outside the module (enforced by the compiler and the JVM, not just convention), and `requires` makes dependencies explicit and checked at both compile time and application startup — a missing or conflicting module fails fast, before any application code runs. This matters for library authors protecting internal APIs, and for large applications wanting reliable dependency graphs and smaller, purpose-built runtime images (via `jlink`).

## 3. Core concept

```
my.app module:
  module-info.java  <- declares what this module requires and exports
  com/myapp/api/     <- exported package: usable by other modules
  com/myapp/internal/ <- NOT exported: invisible outside this module, even if classes are public

module my.app {
    requires java.sql;         // this module needs java.sql's exported packages
    exports com.myapp.api;     // this module exposes com.myapp.api to everyone
}
```

`public` inside a non-exported package is now "public within the module" rather than "public to the world" — a genuinely stronger form of encapsulation than access modifiers alone ever provided.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A module exposes only its exported packages; internal packages stay hidden even though their classes are public">
  <rect x="20" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">module my.app</text>

  <rect x="40" y="55" width="240" height="40" rx="6" fill="#0d1117" stroke="#79c0ff"/>
  <text x="160" y="79" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">com.myapp.api (exported)</text>

  <rect x="40" y="105" width="240" height="40" rx="6" fill="#0d1117" stroke="#f85149"/>
  <text x="160" y="129" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">com.myapp.internal (hidden)</text>

  <line x1="300" y1="75" x2="380" y2="75" stroke="#6db33f" stroke-width="2" marker-end="url(#m1)"/>
  <text x="480" y="65" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">other modules CAN use this</text>

  <line x1="300" y1="125" x2="380" y2="125" stroke="#f85149" stroke-width="2" stroke-dasharray="4,4"/>
  <text x="480" y="140" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">other modules CANNOT — compile error</text>

  <defs>
    <marker id="m1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Public classes in a non-exported package are still `public`, but the module boundary makes them unreachable from outside — a stronger guarantee than the access modifier alone ever gave.

## 5. Runnable example

Scenario: building a tiny "greeting library" with a public API and a private helper implementation — starting with the classic classpath-based JAR where the "internal" package is really just public by convention, then converting it into a real module that enforces the boundary, then adding a consumer module that depends on it and observing what the compiler does and doesn't allow.

### Level 1 — Basic

```java
// File layout (classpath-based, pre-module style):
//   src/com/greetinglib/api/Greeter.java
//   src/com/greetinglib/internal/GreetingFormatter.java
//   src/Main.java

package com.greetinglib.api;
import com.greetinglib.internal.GreetingFormatter;

public class Greeter {
    public String greet(String name) {
        return GreetingFormatter.format(name); // "internal" class, but nothing stops external use
    }
}
```

```java
package com.greetinglib.internal;

// Meant to be "internal", but with no module system, this is just a naming convention.
public class GreetingFormatter {
    public static String format(String name) {
        return "Hello, " + name + "!";
    }
}
```

```java
import com.greetinglib.api.Greeter;
import com.greetinglib.internal.GreetingFormatter; // nothing prevents this "illegal" import!

public class Main {
    public static void main(String[] args) {
        Greeter greeter = new Greeter();
        System.out.println(greeter.greet("World"));
        System.out.println(GreetingFormatter.format("Direct access")); // works — no real protection
    }
}
```

**How to run:** compile all files with `javac -d out src/com/greetinglib/api/Greeter.java src/com/greetinglib/internal/GreetingFormatter.java src/Main.java` and run `java -cp out Main`.

Expected output:
```
Hello, World!
Hello, Direct access!
```

Both calls succeed — `Main` was never supposed to touch `GreetingFormatter` directly (it's named "internal"), but on the plain classpath, `public class` genuinely means "usable from anywhere," with no mechanism to enforce the intended boundary between the library's API and its implementation details.

### Level 2 — Intermediate

```java
// File layout (module-based):
//   greetinglib/module-info.java
//   greetinglib/com/greetinglib/api/Greeter.java
//   greetinglib/com/greetinglib/internal/GreetingFormatter.java

module greetinglib {
    exports com.greetinglib.api; // only this package is visible to other modules
    // com.greetinglib.internal is intentionally NOT exported
}
```

```java
package com.greetinglib.api;
import com.greetinglib.internal.GreetingFormatter;

public class Greeter {
    public String greet(String name) {
        return GreetingFormatter.format(name); // fine: same module, always visible internally
    }
}
```

```java
package com.greetinglib.internal;

public class GreetingFormatter {
    public static String format(String name) {
        return "Hello, " + name + "!";
    }
}
```

**How to run:** `javac -d out greetinglib/module-info.java greetinglib/com/greetinglib/api/Greeter.java greetinglib/com/greetinglib/internal/GreetingFormatter.java`

Expected output: compiles cleanly, no output (this level only demonstrates the library module compiling on its own).

The real-world concern this adds: `com.greetinglib.internal` is now genuinely enforced as private to the module — `Greeter` (in the same module) can still use `GreetingFormatter` freely, since intra-module access is always allowed regardless of `exports`, but nothing outside `greetinglib` will be permitted to reference it, as the next level demonstrates.

### Level 3 — Advanced

```java
// File layout (consumer module depending on greetinglib):
//   greetinglib/module-info.java, greetinglib/com/greetinglib/api/Greeter.java, .../internal/GreetingFormatter.java
//   app/module-info.java
//   app/com/myapp/Main.java

module app {
    requires greetinglib; // explicit dependency, checked at compile time and startup
}
```

```java
package com.myapp;
import com.greetinglib.api.Greeter;
// import com.greetinglib.internal.GreetingFormatter; // <- if uncommented, this FAILS to compile

public class Main {
    public static void main(String[] args) {
        Greeter greeter = new Greeter();
        System.out.println(greeter.greet("World"));
    }
}
```

**How to run:**
```
javac -d out --module-source-path . $(find greetinglib app -name "*.java")
java --module-path out -m app/com.myapp.Main
```

Expected output:
```
Hello, World!
```

If the commented-out `import com.greetinglib.internal.GreetingFormatter;` line is uncommented, `javac` fails with:
```
error: package com.greetinglib.internal is not visible
  (package com.greetinglib.internal is declared in module greetinglib, which does not export it)
```
This is the production-flavoured payoff: the module system doesn't just document the intended API boundary, it makes violating it a **compile-time error**, not a documentation comment or a code-review nitpick that can slip through.

## 6. Walkthrough

Execution starts with the two-module compilation command in Level 3. `--module-source-path .` tells `javac` that source files are organized one directory per module (`greetinglib/`, `app/`), each containing its own `module-info.java` — this lets a single `javac` invocation compile both modules together, resolving their `requires`/`exports` relationships as it goes.

`javac` first processes `greetinglib`'s `module-info.java`: it records that this module exports `com.greetinglib.api` and does not export `com.greetinglib.internal`. It then compiles `Greeter.java` and `GreetingFormatter.java` inside that module, and since both are in the same module, `Greeter`'s `import com.greetinglib.internal.GreetingFormatter` is allowed — module boundaries only restrict access *between* modules, never *within* one.

Next, `javac` processes `app`'s `module-info.java`, which declares `requires greetinglib`. This tells the compiler: "when compiling `app`'s source files, make `greetinglib`'s exported packages (just `com.greetinglib.api`, since that's all it exports) visible and resolvable." Compiling `Main.java`, the `import com.greetinglib.api.Greeter` line succeeds because `com.greetinglib.api` is exported and `app` explicitly requires `greetinglib`.

```
javac dependency resolution:

app  --requires-->  greetinglib
 |                        |
 uses Greeter        exports com.greetinglib.api  (visible to app)
 (from api package)  does NOT export com.greetinglib.internal  (invisible to app)
```

At runtime, `java --module-path out -m app/com.myapp.Main` launches the `app` module's `Main` class. The JVM's module system performs the same dependency check again at startup — if `greetinglib` were missing from the module path entirely, the JVM would refuse to launch at all with a clear "module not found" error, rather than letting the application start and fail later with a `NoClassDefFoundError` the first time `Greeter` was actually used.

`Main.main` creates a `Greeter` and calls `greet("World")`, which internally calls `GreetingFormatter.format("World")` — legal because that call happens *inside* `greetinglib`, where module boundaries don't apply. The formatted string `"Hello, World!"` is returned up through `greet(...)` and printed by `Main`.

Had the commented-out direct import of `GreetingFormatter` been left active in `Main.java` (a different module than `greetinglib`), `javac` would reject it during the very first compilation step shown above — `com.greetinglib.internal` was never exported, so it's simply not part of what `app` is allowed to see, no matter how public the class itself is declared.

## 7. Gotchas & takeaways

> A class being declared `public` no longer guarantees it's usable from other code — visibility is now the **intersection** of the access modifier and the module's `exports` declarations. A `public class` in a package the module doesn't export is invisible to every other module, full stop; this is a common source of confusion for developers used to pre-module Java, where `public` alone was always sufficient.

- `exports` grants visibility to *all* modules that `requires` this one; `exports ... to specificModule` (a qualified export, covered separately) restricts visibility to only the named module(s) — useful for exposing something to one trusted consumer without making it fully public.
- Access *within* a single module is never restricted by the module system — `exports`/`requires` only govern boundaries *between* modules. Regular Java access modifiers (`private`, package-private, `protected`, `public`) still apply exactly as before within a module.
- A library can still choose not to modularize at all and remain a plain JAR on the classpath — modules and the classpath can coexist in the same application, though unmodularized JARs on the module path become "automatic modules" with looser rules (covered separately).
- Missing or conflicting module dependencies are detected by the JVM at **application startup**, before `main` even runs — a meaningful reliability improvement over classpath-based `NoClassDefFoundError`s that could previously surface arbitrarily deep into a running application.
- Modularizing an existing large classpath-based codebase is often nontrivial in practice — circular package dependencies across intended module boundaries, split packages (the same package name in two different JARs, which the module system forbids), and reflection-heavy frameworks are the most common migration obstacles.
