---
card: java
gi: 569
slug: module-info-java
title: module-info.java
---

## 1. What it is

`module-info.java` is a special source file, placed at the root of a module's source tree, that declares everything the Java compiler and JVM need to know about a module: its name, which modules it `requires`, which packages it `exports`, and a handful of other directives (`opens`, `uses`, `provides`). It compiles to a real class file, `module-info.class`, that both `javac` and `java` read to enforce the module's boundaries.

## 2. Why & when

Without a single, compiler-and-runtime-enforced declaration file, a module's dependencies and exposed API would have to live in documentation, build-tool configuration, or convention alone — all of which can drift out of sync with the actual code, and none of which the compiler or JVM can check. `module-info.java` exists so that "what does this module need, and what does it expose" is a single, authoritative, machine-checked source of truth: write an incorrect or incomplete declaration, and `javac` refuses to compile the module (or a consumer of it) rather than letting a mismatch surface later as a runtime failure. You need to understand it any time you're building, splitting, or consuming a Java module — which, since Java 9, includes the JDK's own platform libraries (`java.base`, `java.sql`, `java.xml`, and so on), all of which are themselves modules with their own `module-info.java`-equivalent declarations.

## 3. Core concept

```java
module com.example.myapp {
    requires java.base;              // implicit for every module — rarely written explicitly
    requires java.sql;
    requires transitive com.example.core;

    exports com.example.myapp.api;
    exports com.example.myapp.spi to com.example.plugin.host;

    opens com.example.myapp.model;   // allows reflection into this package at runtime

    uses com.example.myapp.spi.Extension;
    provides com.example.myapp.spi.Extension with com.example.myapp.impl.DefaultExtension;
}
```

The file's name is fixed (`module-info.java`) and its location is fixed (the root of the module's source directory, as a sibling of the top-level package directories) — the compiler recognizes it by name and position, not by any annotation or configuration elsewhere. Think of it as a module's **manifest and contract** in one file: it says what this module needs to compile and run (`requires`), what it's willing to share with others (`exports`), and, more advanced still, what services it consumes or provides (`uses`/`provides`). Unlike a `MANIFEST.MF` in a plain JAR — which is largely descriptive metadata the JVM mostly ignores at the class-loading level — `module-info.java`'s declarations are actively **enforced**: an unlisted `requires` means a compile error the moment you try to use that dependency's classes; an unlisted `exports` means an inaccessible package, checked by both the compiler and the runtime module system.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="module-info.java sits at the module root and governs everything the compiler and JVM enforce about that module">
  <rect x="20" y="15" width="260" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="35" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">module source root</text>
  <rect x="35" y="45" width="230" height="26" rx="4" fill="#0d1117" stroke="#f0883e"/>
  <text x="150" y="63" fill="#f0883e" font-size="10" text-anchor="middle" font-family="monospace">module-info.java</text>
  <rect x="35" y="80" width="230" height="26" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="150" y="98" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">com/example/myapp/api/</text>
  <rect x="35" y="115" width="230" height="26" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="150" y="133" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">com/example/myapp/model/</text>

  <text x="340" y="55" fill="#8b949e" font-size="10" font-family="sans-serif">javac reads module-info.java to know:</text>
  <text x="340" y="75" fill="#8b949e" font-size="10" font-family="sans-serif">- what this module may import (requires)</text>
  <text x="340" y="95" fill="#8b949e" font-size="10" font-family="sans-serif">- what other modules may import from it (exports)</text>
  <text x="340" y="115" fill="#8b949e" font-size="10" font-family="sans-serif">java reads the compiled module-info.class</text>
  <text x="340" y="135" fill="#8b949e" font-size="10" font-family="sans-serif">to enforce the same rules again at startup</text>
</svg>

One file, read twice: once by the compiler while building, once by the JVM while launching.

## 5. Runnable example

Scenario: building a small "inventory" module whose `module-info.java` grows from a bare-bones declaration to one expressing multiple dependencies and export rules, then a consumer module that only compiles because the declarations line up correctly.

### Level 1 — Basic

```java
// File: inventory/module-info.java
module inventory {
    exports com.inventory.api;
}
```

```java
// File: inventory/com/inventory/api/Item.java
package com.inventory.api;

public class Item {
    private final String name;
    private final int quantity;

    public Item(String name, int quantity) {
        this.name = name;
        this.quantity = quantity;
    }

    @Override public String toString() {
        return name + " x" + quantity;
    }
}
```

```java
// File: app/module-info.java
module app {
    requires inventory;
}
```

```java
// File: app/com/myapp/Main.java
package com.myapp;
import com.inventory.api.Item;

public class Main {
    public static void main(String[] args) {
        Item item = new Item("Widget", 42);
        System.out.println(item);
    }
}
```

**How to run:**
```
javac -d out --module-source-path . $(find inventory app -name "*.java")
java --module-path out -m app/com.myapp.Main
```

Expected output:
```
Widget x42
```

`inventory/module-info.java` names the module `inventory` (matching its source directory by convention, though the name itself comes from the `module` declaration, not the directory) and exports exactly one package. `app/module-info.java` declares `requires inventory`, and because `app` only ever imports `com.inventory.api.Item` — a class inside the exported package — compilation succeeds and the program runs.

### Level 2 — Intermediate

```java
// File: inventory/module-info.java — now depends on java.sql for a persistence layer,
// and exports two packages instead of one.
module inventory {
    requires java.sql;
    exports com.inventory.api;
    exports com.inventory.report;
}
```

```java
// File: inventory/com/inventory/report/StockReport.java
package com.inventory.report;
import com.inventory.api.Item;
import java.util.List;

public class StockReport {
    public static String summarize(List<Item> items) {
        return "Stock report: " + items.size() + " item type(s)";
    }
}
```

```java
// File: app/module-info.java — unchanged from Level 1, still just requires inventory
module app {
    requires inventory;
}
```

```java
// File: app/com/myapp/Main.java
package com.myapp;
import com.inventory.api.Item;
import com.inventory.report.StockReport;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        List<Item> items = List.of(new Item("Widget", 42), new Item("Gadget", 7));
        System.out.println(StockReport.summarize(items));
    }
}
```

**How to run:**
```
javac -d out --module-source-path . $(find inventory app -name "*.java")
java --module-path out -m app/com.myapp.Main
```

Expected output:
```
Stock report: 2 item type(s)
```

The real-world concern this adds: a module that itself **depends on another module** (`requires java.sql`, one of the JDK's own platform modules) while also exporting **multiple** packages of its own. `app`'s `module-info.java` didn't need to change at all to gain access to the newly exported `com.inventory.report` package — `requires inventory` already grants visibility into everything `inventory` currently exports, present and future, without listing individual packages on the consumer side.

### Level 3 — Advanced

```java
// File: inventory/module-info.java — restricts one export to a specific trusted module
// and opens a package for reflection (needed by some serialization/DI frameworks).
module inventory {
    requires java.sql;
    exports com.inventory.api;
    exports com.inventory.report;
    exports com.inventory.internal.audit to app; // qualified export: ONLY visible to "app"
    opens com.inventory.api;                      // allows deep reflection into this package
}
```

```java
// File: inventory/com/inventory/internal/audit/AuditLog.java
package com.inventory.internal.audit;

public class AuditLog {
    public static void record(String action) {
        System.out.println("[audit] " + action);
    }
}
```

```java
// File: app/module-info.java
module app {
    requires inventory;
}
```

```java
// File: app/com/myapp/Main.java
package com.myapp;
import com.inventory.api.Item;
import com.inventory.report.StockReport;
import com.inventory.internal.audit.AuditLog; // allowed: qualified export names "app" specifically
import java.lang.reflect.Field;
import java.util.List;

public class Main {
    public static void main(String[] args) throws Exception {
        List<Item> items = List.of(new Item("Widget", 42));
        System.out.println(StockReport.summarize(items));

        AuditLog.record("Generated stock report");

        // Reflection into com.inventory.api works because that package is "opens"-ed.
        Field nameField = Item.class.getDeclaredField("name");
        nameField.setAccessible(true);
        System.out.println("Reflected field name: " + nameField.get(items.get(0)));
    }
}
```

**How to run:**
```
javac -d out --module-source-path . $(find inventory app -name "*.java")
java --module-path out -m app/com.myapp.Main
```

Expected output:
```
Stock report: 1 item type(s)
[audit] Generated stock report
Reflected field name: Widget
```

This handles the production-flavoured case of **fine-grained visibility control**: `exports ... to app` shares `com.inventory.internal.audit` with only the `app` module by name (any other module `requires inventory` would still be denied access to that specific package), and `opens com.inventory.api` grants **runtime reflective access** into `Item`'s private fields — something plain `exports` alone does not permit, since `exports` only governs normal compile-time-checked access, not `setAccessible(true)`-style deep reflection.

## 6. Walkthrough

Execution starts with the compilation command in Level 3. `javac` reads `inventory/module-info.java` first, recording four facts about the `inventory` module: it requires `java.sql`; it unconditionally exports `com.inventory.api` and `com.inventory.report`; it exports `com.inventory.internal.audit` but *only* to the module named `app`; and it `opens` `com.inventory.api` for reflective access.

`javac` then compiles `app/module-info.java`, recording that `app` requires `inventory`. When it reaches `Main.java`'s imports, each is checked against `inventory`'s declarations:

```
import com.inventory.api.Item                    -> exported unconditionally -> OK
import com.inventory.report.StockReport           -> exported unconditionally -> OK
import com.inventory.internal.audit.AuditLog       -> exported "to app" specifically, and this IS app -> OK
```

Had a *third* module (say, `other`) also declared `requires inventory` and tried to import `AuditLog`, that import would fail — the qualified export names `app` exclusively, so `other` cannot see `com.inventory.internal.audit` even though it's a legitimate consumer of `inventory`'s other exported packages.

At runtime, `java --module-path out -m app/com.myapp.Main` launches `Main.main`. Execution proceeds top to bottom: `items` is built with one `Item`; `StockReport.summarize(items)` is called (legal — `com.inventory.report` is exported), returning `"Stock report: 1 item type(s)"`, which is printed.

`AuditLog.record("Generated stock report")` runs next, printing `"[audit] Generated stock report"` — this call is only legal at all because of the qualified `exports ... to app` directive; without it, this line wouldn't have compiled in the first place.

Finally, the reflection block runs: `Item.class.getDeclaredField("name")` retrieves the `Field` object for `Item`'s private `name` field, then `nameField.setAccessible(true)` attempts to suppress Java's normal access checks for that field. This call would throw `InaccessibleObjectException` at runtime if `com.inventory.api` had **not** been `opens`-ed — `exports` alone permits normal compiled code to use `Item`'s public API, but reflective, access-check-bypassing operations additionally require `opens`. Because the package *is* opened, `setAccessible(true)` succeeds, and `nameField.get(items.get(0))` reads the private field's value directly, printing `"Reflected field name: Widget"`.

## 7. Gotchas & takeaways

> `exports` and `opens` are **not the same permission**. `exports` allows normal, compile-time-checked use of a package's public types (`import`, calling public methods). `opens` additionally allows runtime reflective access that bypasses normal access checks (`setAccessible(true)`, and by extension frameworks like Jackson, Hibernate, or JUnit that rely on reflecting into private fields/constructors). A package can be `exports`-ed without being `opens`-ed (compile-time use only, no deep reflection) or `opens`-ed without being `exports`-ed (reflection-only access, common for internal model classes a framework needs to touch but that shouldn't be part of the public compiled API).

- `module-info.java` must be the file's exact name, and it must sit at the root of that module's source tree — the compiler locates it structurally, not through any build-tool configuration alone (though build tools like Maven/Gradle do need to know where that root is).
- `requires java.base` is implicit for every module and essentially never written explicitly — `java.base` contains `java.lang`, `java.util`, and the other packages every Java program needs unconditionally.
- A qualified export (`exports pkg to moduleA, moduleB`) can name multiple target modules, comma-separated — useful for sharing an internal package with a small, known set of trusted consumers without making it universally public.
- `opens` can also be declared for an entire module at once (`open module inventory { ... }`, note `open` before `module`), which opens every package in the module for reflection — a common quick-fix for frameworks with heavy reflection needs, at the cost of losing fine-grained control over which packages allow it.
- Forgetting a `requires` for a dependency you actually use produces a compile-time error naming the missing package/module explicitly — a significant debugging improvement over the classpath era, where a missing dependency might not surface until the specific code path using it executed at runtime.
