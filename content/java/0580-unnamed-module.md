---
card: java
gi: 580
slug: unnamed-module
title: Unnamed module
---

## 1. What it is

The **unnamed module** is the catch-all module that every class loaded from the classpath (rather than the module path) automatically belongs to. It has no name, no `module-info.java`, and special, relaxed rules baked into the module system specifically so classpath code keeps working: it reads every other module (named or automatic) unconditionally, and, in turn, is readable by automatic modules — but it exports nothing in the structured, declared sense that real modules do.

## 2. Why & when

The module system had to preserve full backward compatibility with the entire pre-Java-9 Java ecosystem, where the very concept of "modules" and "exports" didn't exist. Rather than requiring every single class ever run to belong to some named module, the JVM gives classpath code an implicit home: the unnamed module. Understanding it matters because it's not a special case you opt into — it's the *default* for any class compiled and run without a `module-info.java`, and its special, one-directional read permissions are exactly why classpath-based libraries and applications continue to run unmodified under Java 9+, and why mixed classpath/module-path setups (covered in the previous topic) behave the way they do.

## 3. Core concept

```java
// No module-info.java anywhere in this compilation unit.
package com.myapp;

public class Main {
    public static void main(String[] args) {
        System.out.println(Main.class.getModule()); // prints information about the unnamed module
    }
}
```

```
java -cp out com.myapp.Main
// Output: unnamed module @<some hash>
```

Every class's `getClass().getModule()` returns a `java.lang.Module` object — for classpath code, that object represents the unnamed module specifically, distinguishable from any named module by `Module.isNamed()` returning `false` and `Module.getName()` returning `null`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The unnamed module reads every other module unconditionally but exports nothing in the structured, declared sense">
  <rect x="20" y="20" width="220" height="50" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="130" y="42" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">unnamed module</text>
  <text x="130" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(all classpath code lands here)</text>

  <line x1="240" y1="40" x2="330" y2="40" stroke="#6db33f" stroke-width="2" marker-end="url(#u1)"/>
  <text x="285" y="30" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">reads freely</text>

  <rect x="330" y="20" width="220" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="440" y="42" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">any named/automatic module</text>

  <line x1="330" y1="70" x2="240" y2="70" stroke="#8b949e" stroke-width="2" stroke-dasharray="4,3"/>
  <text x="285" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">named modules do NOT read the unnamed module by default</text>

  <text x="20" y="130" fill="#8b949e" font-size="10" font-family="sans-serif">This asymmetry is why classpath code can freely use module-path libraries once resolved,</text>
  <text x="20" y="145" fill="#8b949e" font-size="10" font-family="sans-serif">but a real module cannot casually depend on unmodularized classpath code the same way.</text>

  <defs>
    <marker id="u1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The read relationship is one-directional by design, which is exactly what makes gradual, incremental modularization possible.

## 5. Runnable example

Scenario: inspecting a running program's own module identity and using that information to branch behavior — starting with printing basic module info for classpath-run code, then comparing it against a genuine named module's identity, then writing a small utility that reports whether a given class's code is "modularized" or still running the classpath/unnamed-module way.

### Level 1 — Basic

```java
// File: com/myapp/Main.java — plain classpath code, no module-info.java
package com.myapp;

public class Main {
    public static void main(String[] args) {
        Module module = Main.class.getModule();
        System.out.println("Module: " + module);
        System.out.println("Is named: " + module.isNamed());
        System.out.println("Name: " + module.getName());
    }
}
```

**How to run:** `javac -d out com/myapp/Main.java && java -cp out com.myapp.Main`

Expected output:
```
Module: unnamed module @<some hash, e.g. 4517d9a3>
Is named: false
Name: null
```

`Main.class.getModule()` returns the `java.lang.Module` object representing whatever module `Main`'s class actually belongs to at runtime. Since `Main` was compiled and run purely via the classpath (`-cp out`, no `module-info.java`, no `--module-path`), it belongs to the unnamed module — `isNamed()` returns `false`, and `getName()` returns `null` (an unnamed module has, definitionally, no name), which is the reliable, programmatic way to detect "this class is running as classpath code" from within Java itself.

### Level 2 — Intermediate

```java
// File: greetlib/module-info.java — a real, named module for comparison
module greetlib {
    exports com.greetlib;
}
```

```java
// File: greetlib/com/greetlib/Greeter.java
package com.greetlib;

public class Greeter {
    public static void describeSelf() {
        Module module = Greeter.class.getModule();
        System.out.println("Greeter's module: " + module);
        System.out.println("Is named: " + module.isNamed());
        System.out.println("Name: " + module.getName());
    }
}
```

```java
// File: app/module-info.java
module app {
    requires greetlib;
}
```

```java
// File: app/com/myapp/Main.java
package com.myapp;
import com.greetlib.Greeter;

public class Main {
    public static void main(String[] args) {
        Module ownModule = Main.class.getModule();
        System.out.println("Main's own module: " + ownModule);
        System.out.println("Is named: " + ownModule.isNamed());
        System.out.println("Name: " + ownModule.getName());

        Greeter.describeSelf();
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
Main's own module: module app
Is named: true
Name: app
Greeter's module: module greetlib
Is named: true
Name: greetlib
```

The real-world concern this adds: **contrasting genuine named-module identity against the unnamed-module identity from Level 1**. Now that both `Main` and `Greeter` are compiled and launched as real modules (via `--module-path` and `-m app/...`), their `getModule()` calls return proper named `Module` objects — `isNamed()` returns `true` for both, and `getName()` returns their actual declared module names (`"app"` and `"greetlib"` respectively), a stark contrast to Level 1's `null`/`false` result for the exact same kind of `getModule()` call.

### Level 3 — Advanced

```java
// File: diagnostics/module-info.java — a small reusable utility module
module diagnostics {
    exports com.diagnostics;
}
```

```java
// File: diagnostics/com/diagnostics/ModuleReport.java
package com.diagnostics;

public class ModuleReport {
    public static void report(Class<?> clazz) {
        Module module = clazz.getModule();
        String origin = module.isNamed()
            ? "named module \"" + module.getName() + "\""
            : "the UNNAMED module (classpath code)";
        System.out.println(clazz.getName() + " runs in " + origin);
    }
}
```

```java
// File: app/module-info.java — a real module, using the diagnostics utility
module app {
    requires diagnostics;
}
```

```java
// File: app/com/myapp/Main.java
package com.myapp;
import com.diagnostics.ModuleReport;
import java.util.ArrayList;

public class Main {
    public static void main(String[] args) {
        ModuleReport.report(Main.class);        // app's own class: named module "app"
        ModuleReport.report(ArrayList.class);    // JDK class: named module "java.base"
        ModuleReport.report(ModuleReport.class); // diagnostics' own class: named module "diagnostics"
    }
}
```

**How to run:**
```
javac -d out --module-source-path . $(find diagnostics app -name "*.java")
java --module-path out -m app/com.myapp.Main
```

Expected output:
```
com.myapp.Main runs in named module "app"
java.util.ArrayList runs in named module "java.base"
com.diagnostics.ModuleReport runs in named module "diagnostics"
```

This handles the production-flavoured case of a **reusable diagnostic utility** that reports any class's module identity generically — useful for debugging exactly which modules a running application's classes actually belong to, especially in a mixed classpath/module-path deployment where the answer isn't always obvious just from looking at source code. Every class checked here happens to belong to a named module (since this whole example runs entirely on the module path), demonstrating that even the JDK's own `ArrayList` reports its true module identity (`java.base`) through this same generic mechanism.

## 6. Walkthrough

Execution starts with the compilation and launch commands in Level 3, which build `diagnostics` and `app` as real named modules and launch `app/com.myapp.Main` via the module path.

`main` calls `ModuleReport.report(Main.class)` first. Inside `report`, `clazz.getModule()` is called on the `Class` object for `com.myapp.Main` — this asks the JVM "which module does this class belong to?" Since `Main` was compiled as part of the `app` module and launched via `-m app/com.myapp.Main`, the JVM answers with the real, named `app` module. `module.isNamed()` returns `true`, so `origin` is set to `"named module \"app\""`, and `report` prints `"com.myapp.Main runs in named module \"app\""`.

```
ModuleReport.report(clazz) logic:

clazz.getModule()          -> the java.lang.Module this class actually belongs to
module.isNamed()           -> true for real modules, false for the unnamed module
module.isNamed() ? "named module \"" + name + "\"" : "the UNNAMED module (classpath code)"
```

The second call, `ModuleReport.report(ArrayList.class)`, asks the same question about `java.util.ArrayList` — a class that ships as part of the JDK itself. `ArrayList.class.getModule()` returns the `java.base` module, the foundational JDK platform module every Java program implicitly requires. `module.isNamed()` is `true`, `module.getName()` is `"java.base"`, so `report` prints `"java.util.ArrayList runs in named module \"java.base\""` — demonstrating that this same generic reflection-based technique works identically for JDK classes as for application-defined ones, since the JDK itself has been fully modularized since Java 9.

The third call, `ModuleReport.report(ModuleReport.class)`, asks about `ModuleReport`'s own class — which belongs to the `diagnostics` module, the same module `report` itself is defined in. This works exactly the same way: `clazz.getModule()` returns the `diagnostics` module, and the method prints `"com.diagnostics.ModuleReport runs in named module \"diagnostics\""`.

Had any of these classes instead been compiled and launched purely via the classpath (as `Main` was in Level 1), the corresponding `report(...)` call would print `"... runs in the UNNAMED module (classpath code)"` instead — the exact same generic method correctly distinguishes named-module code from unnamed-module (classpath) code for any class handed to it, which is precisely the diagnostic value of checking `Module.isNamed()` this way.

## 7. Gotchas & takeaways

> `Class.getModule()` is a reliable, built-in way to answer "is this specific class running as classpath code or as part of a real module?" at runtime — useful when debugging why a `requires`/`exports` rule seems not to apply, since the answer often turns out to be "that class isn't actually in the module you think it's in" (frequently because it landed in the unnamed module due to a classpath/module-path mixup in the build configuration).

- There is conceptually **one** unnamed module per classloader in a running JVM (in typical single-classloader applications, effectively one unnamed module for all classpath code) — it is not per-JAR or per-package the way named modules are.
- The unnamed module reads every other module (named and automatic) unconditionally — this is a deliberate, built-in relaxation, not something any `module-info.java` grants; there is no `module-info.java` for the unnamed module to have such declarations in, since it has no name to declare anything under.
- Named modules do **not** automatically read the unnamed module's classpath contents — this asymmetry is why a genuine, fully modular library generally cannot casually depend on unmodularized classpath code the same easy way classpath code can depend on modules (some escape hatches like `--add-reads ALL-UNNAMED` exist for edge cases, but they're exceptions, not the default).
- `Module.getPackages()`, `Module.canRead(otherModule)`, and other `java.lang.Module` API methods let code introspect and even (with sufficient permission) reconfigure module relationships programmatically at runtime — mostly used by advanced frameworks and application containers rather than typical application code.
- Automatic modules (covered in the previous topic) are a distinct concept from the unnamed module — an automatic module is a genuinely *named* module (with a synthesized or manifest-declared name), just one built from a JAR with no `module-info.class`; the unnamed module, by contrast, has no name and no module identity of that kind at all.
