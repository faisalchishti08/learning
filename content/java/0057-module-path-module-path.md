---
card: java
gi: 57
slug: module-path-module-path
title: Module path (--module-path)
---

## 1. What it is

The **module path** (`--module-path` or `-p`) is the JDK 9+ alternative to the classpath for loading **modular JARs** — JARs that contain a `module-info.class` at their root. The module system resolves dependencies at startup, enforces explicit exports, and eliminates split packages.

```bash
# Compile: put modular dependencies on the module path
javac --module-path mods --module-source-path src -d out -m com.example.app

# Run: same flag, add --module to specify entry point
java --module-path "mods:out" --module com.example.app/com.example.app.Main

# Short aliases
javac -p mods ...
java  -p "mods:out" -m com.example.app/com.example.app.Main
```

A **module** is a named, self-describing unit of code: `module com.example.app { requires com.google.gson; exports com.example.api; }`. The JVM reads these declarations at startup and verifies the full dependency graph before executing any code.

## 2. Why & when

| Scenario | Use classpath | Use module path |
|---|---|---|
| Legacy / third-party non-modular JARs | yes | no (or automatic modules) |
| New modular application | no | yes |
| JDK's own APIs (`java.sql`, `java.logging`, etc.) | implicit (boot) | available via `--add-modules` |
| `jlink` custom runtime | requires module path | yes |
| Fat JAR / Spring Boot JAR | classpath | no |
| Strong encapsulation needed | no | yes |

Use the module path when:
1. Your project has a `module-info.java` at the source root.
2. You want the JVM to enforce explicit `exports`/`requires` at startup.
3. You're building a custom runtime with `jlink`.

Mix classpath and module path freely: `--module-path mods --class-path lib/legacy.jar` is valid.

## 3. Core concept

```bash
# ---- module-info.java: the module descriptor ----
# src/com.example.app/module-info.java
module com.example.app {
    requires java.sql;            # depends on java.sql module
    requires com.google.gson;     # depends on a third-party module
    exports com.example.api;      # only this package is visible to others
    opens   com.example.internal to com.google.gson;  # allow reflection for Gson
}

# ---- directory layout for multi-module build ----
src/
  com.example.app/
    module-info.java
    com/example/app/Main.java
    com/example/api/OrderService.java
mods/
  gson-2.10.1.jar           # modular JAR with module-info.class inside

# ---- compile all modules ----
javac \
  --module-path mods \
  --module-source-path src \
  -d out \
  -m com.example.app       # compile this module (+ transitive deps in --module-path)

# ---- run ----
java \
  --module-path "mods:out" \
  --module com.example.app/com.example.app.Main

# ---- automatic modules ----
# Non-modular JAR placed on --module-path becomes an "automatic module"
# Name derived from JAR filename: gson-2.10.1.jar → com.google.gson (dots, strip version)
# Exports ALL packages; requires ALL other automatic/explicit modules
# Use as stepping stone when migrating from classpath to module path

# ---- useful module-related flags ----
java --list-modules                    # list all observable modules
java --describe-module java.sql        # exports, requires, packages of java.sql
java --module-path mods --module com.example.app --describe-module com.example.app

# ---- add-modules: bring in optional platform modules ----
java --add-modules java.xml.bind --module-path ... --module com.example.app/...

# ---- add-opens: open a module's package for reflection (for frameworks) ----
java --add-opens java.base/java.lang=ALL-UNNAMED ...

# ---- mixed classpath + module path ----
java \
  --module-path mods \        # modular JARs here
  --add-modules com.google.gson \
  --class-path lib/legacy.jar \  # non-modular JARs here (unnamed module)
  -cp out \
  com.example.Main             # class in unnamed module (classpath)
```

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Module path: each module declares requires and exports; JVM verifies graph at startup; inaccessible packages cause module access error">
  <rect x="8" y="8" width="684" height="194" rx="8" fill="#0d1117"/>

  <!-- Module: com.example.app -->
  <rect x="20" y="28" width="175" height="110" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="107" y="46" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">com.example.app</text>
  <text x="107" y="62" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">requires java.sql</text>
  <text x="107" y="75" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">requires com.google.gson</text>
  <text x="107" y="92" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="monospace">exports com.example.api</text>
  <text x="107" y="105" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">opens internal → gson</text>
  <text x="107" y="125" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">module-info.class ✓</text>

  <!-- Arrow right -->
  <line x1="195" y1="83" x2="225" y2="83" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <defs><marker id="arr" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker></defs>
  <text x="210" y="78" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">requires</text>

  <!-- Module: java.sql -->
  <rect x="228" y="28" width="140" height="80" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="298" y="46" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">java.sql</text>
  <text x="298" y="62" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">requires java.logging</text>
  <text x="298" y="77" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="monospace">exports java.sql</text>
  <text x="298" y="96" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">JDK platform module</text>

  <!-- Arrow right -->
  <line x1="195" y1="103" x2="380" y2="65" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Module: com.google.gson -->
  <rect x="383" y="28" width="155" height="80" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="460" y="46" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">com.google.gson</text>
  <text x="460" y="62" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="monospace">exports com.google.gson</text>
  <text x="460" y="77" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="monospace">exports com.google.gson.reflect</text>
  <text x="460" y="96" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">modular third-party JAR</text>

  <!-- Access error -->
  <rect x="550" y="28" width="135" height="80" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="617" y="48" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Accessing non-exported</text>
  <text x="617" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">package from outside</text>
  <text x="617" y="78" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">→ InaccessibleObjectException</text>
  <text x="617" y="96" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">at startup (not runtime!)</text>

  <!-- Bottom: classpath vs module path -->
  <rect x="20" y="153" width="660" height="44" rx="5" fill="#1c2430"/>
  <text x="350" y="170" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Classpath: any class visible to all; split packages allowed; errors at runtime</text>
  <text x="350" y="187" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">Module path: only exported packages visible; graph verified at startup; split packages = error</text>
</svg>

The module system builds a directed dependency graph from `requires` declarations; non-exported packages are inaccessible even to reflection by default.

## 5. Runnable example

Scenario: order processing application that demonstrates the module descriptor, module path resolution, `--describe-module`, and the automatic module interop path — all using only JDK tools (no external dependencies needed).

### Level 1 — Basic

```java
// ModulePathBasic.java — inspect the module system at runtime
public class ModulePathBasic {
    public static void main(String[] args) {
        System.out.println("=== Module path basics ===\n");

        // This class's module
        Module m = ModulePathBasic.class.getModule();
        System.out.println("Module of this class: " + m.getName());
        System.out.println("Is named module?       " + m.isNamed());
        System.out.println("  (unnamed = running from classpath/single-file)");

        // Inspect some JDK modules
        System.out.println("\n[ JDK named modules ]");
        String[] modules = { "java.base", "java.sql", "java.logging", "java.xml" };
        ModuleLayer layer = ModuleLayer.boot();
        for (String name : modules) {
            layer.findModule(name).ifPresentOrElse(
                mod -> System.out.printf("  %-20s  loaded: true%n", name),
                ()  -> System.out.printf("  %-20s  loaded: false (not in boot layer)%n", name)
            );
        }

        // Module descriptor summary for java.sql
        layer.findModule("java.sql").ifPresent(sql -> {
            System.out.println("\n[ java.sql descriptor ]");
            var desc = sql.getDescriptor();
            System.out.println("  Name:     " + desc.name());
            System.out.println("  Version:  " + desc.version().map(Object::toString).orElse("none"));
            System.out.println("  Requires: " + desc.requires().stream()
                                                      .map(r -> r.name())
                                                      .sorted()
                                                      .toList());
            System.out.println("  Exports (first 3): " + desc.exports().stream()
                                                               .map(e -> e.source())
                                                               .sorted()
                                                               .limit(3)
                                                               .toList());
        });

        System.out.println("\n[ module-info.java snippet ]");
        System.out.println("  module com.example.app {");
        System.out.println("      requires java.sql;");
        System.out.println("      requires com.google.gson;");
        System.out.println("      exports com.example.api;");
        System.out.println("  }");
    }
}
```

**How to run:** `java ModulePathBasic.java`

Running via single-file source puts the class in the **unnamed module** — `m.isNamed()` returns `false`. Named modules only exist when you compile with `module-info.java` and run with `--module-path --module`.

### Level 2 — Intermediate

Same order system: programmatically build a module layer at runtime, load a class from it, and call a method — demonstrating how `ModuleLayer`, `ModuleFinder`, and `ClassLoader` interact.

```java
// ModulePathIntermediate.java — dynamic module layer construction
import java.lang.module.*;
import java.nio.file.*;
import java.util.*;

public class ModulePathIntermediate {
    public static void main(String[] args) throws Exception {
        System.out.println("=== Module path intermediate demo ===\n");

        // 1. Show boot layer modules (JDK platform modules)
        ModuleLayer boot = ModuleLayer.boot();
        System.out.println("Boot layer module count: " + boot.modules().size());
        System.out.println("Sample boot layer modules:");
        boot.modules().stream()
            .map(m -> m.getName())
            .filter(n -> n.startsWith("java."))
            .sorted()
            .limit(8)
            .forEach(n -> System.out.println("  " + n));

        // 2. Examine module accessibility rules
        System.out.println("\n[ Module accessibility rules ]");
        Module base = String.class.getModule();
        System.out.println("java.lang.String is in:    " + base.getName());
        System.out.println("java.lang exported?        " +
            base.getDescriptor().exports().stream()
                .anyMatch(e -> e.source().equals("java.lang") && !e.isQualified()));

        // 3. Programmatic access to module descriptor
        boot.findModule("java.logging").ifPresent(logging -> {
            System.out.println("\n[ java.logging descriptor ]");
            var d = logging.getDescriptor();
            System.out.println("  requires: " + d.requires().stream()
                                                   .map(r -> r.name()).sorted().toList());
            System.out.println("  exports:  " + d.exports().stream()
                                                   .map(e -> e.source()).sorted().toList());
        });

        // 4. Find a module via ModuleFinder on the current module path
        System.out.println("\n[ ModuleFinder on boot module path ]");
        ModuleFinder systemFinder = ModuleFinder.ofSystem();
        Set<ModuleReference> refs = systemFinder.findAll();
        System.out.println("  System module references: " + refs.size());
        refs.stream()
            .map(r -> r.descriptor().name())
            .filter(n -> n.startsWith("java.") && !n.contains("jdk"))
            .sorted()
            .limit(5)
            .forEach(n -> System.out.println("  " + n));

        // 5. Configuration: resolve a module from system modules
        System.out.println("\n[ Module resolution ]");
        Configuration cfg = ModuleLayer.boot().configuration();
        cfg.findModule("java.sql").ifPresent(rm -> {
            System.out.println("  java.sql resolved: true");
            System.out.println("  reads: " + rm.reads().stream()
                                                .map(r -> r.name()).sorted().toList());
        });

        System.out.println("\n[ Flags summary ]");
        System.out.println("  --module-path (-p)  : where to find modular JARs");
        System.out.println("  --module (-m)       : module/MainClass to run");
        System.out.println("  --add-modules       : add optional/missing modules");
        System.out.println("  --add-opens         : open package for deep reflection");
        System.out.println("  --add-exports       : export package to another module");
        System.out.println("  --list-modules      : list all observable modules and exit");
        System.out.println("  --describe-module   : print descriptor and exit");
    }
}
```

**How to run:** `java ModulePathIntermediate.java`

`ModuleFinder.ofSystem()` mirrors what `--module-path` does at command-line level: it finds all platform modules. `Configuration.resolve()` is the same graph resolution the JVM performs at startup when you pass `--module com.example.app`.

### Level 3 — Advanced

Same order system: write `module-info.java` programmatically, compile a named module in a temp directory, load it via a dynamic `ModuleLayer`, and call a method via reflection — demonstrating the full module lifecycle end-to-end.

```java
// ModulePathAdvanced.java — compile + load a named module at runtime
import java.io.*;
import java.lang.module.*;
import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;
import javax.tools.*;

public class ModulePathAdvanced {
    public static void main(String[] args) throws Exception {
        System.out.println("=== Module path advanced: dynamic module compilation ===\n");

        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) {
            System.out.println("No system JavaCompiler (run with JDK, not JRE). Skipping compile.");
            printConceptSummary();
            return;
        }

        Path tmp = Files.createTempDirectory("module-demo");
        Path src = tmp.resolve("src/com.example.order");
        Path out = tmp.resolve("out");
        Files.createDirectories(src.resolve("com/example/order"));
        Files.createDirectories(out);

        // Write module-info.java
        Files.writeString(src.resolve("module-info.java"),
            """
            module com.example.order {
                exports com.example.order;
            }
            """);

        // Write the module's class
        Files.writeString(src.resolve("com/example/order/OrderService.java"),
            """
            package com.example.order;
            public class OrderService {
                public String process(String id, double amount) {
                    return String.format("Processed [%s] £%.2f", id, amount);
                }
            }
            """);

        System.out.println("[ Compiling module com.example.order ]");
        int rc = compiler.run(null, null, System.err,
            "--module-source-path", src.getParent().toString(),
            "-d", out.toString(),
            "-m", "com.example.order"
        );
        System.out.println("  Compile result: " + (rc == 0 ? "SUCCESS" : "FAIL (rc=" + rc + ")"));
        if (rc != 0) { cleanup(tmp); return; }

        // List compiled files
        System.out.println("  Compiled files:");
        Files.walk(out).filter(Files::isRegularFile).sorted().forEach(f ->
            System.out.println("    " + out.relativize(f)));

        // Load the module via ModuleLayer
        System.out.println("\n[ Loading module into a new ModuleLayer ]");
        ModuleFinder finder = ModuleFinder.of(out.resolve("com.example.order"));
        ModuleLayer parent  = ModuleLayer.boot();
        Configuration cfg   = parent.configuration()
                                     .resolve(finder, ModuleFinder.of(), Set.of("com.example.order"));
        ModuleLayer layer   = parent.defineModulesWithOneLoader(cfg, ClassLoader.getSystemClassLoader());

        System.out.println("  Layer modules: " + layer.modules().stream()
                                                       .map(m -> m.getName()).sorted().toList());

        // Instantiate OrderService via reflection and invoke process()
        ClassLoader loader = layer.findLoader("com.example.order");
        Class<?> cls  = loader.loadClass("com.example.order.OrderService");
        Object svc    = cls.getDeclaredConstructor().newInstance();
        Method method = cls.getMethod("process", String.class, double.class);

        System.out.println("\n[ Invoking OrderService.process() via reflection ]");
        String[] orderIds = { "ORD-100", "ORD-101", "ORD-102" };
        double[] amounts  = { 299.99, 50.00, 1200.00 };
        for (int i = 0; i < orderIds.length; i++) {
            String result = (String) method.invoke(svc, orderIds[i], amounts[i]);
            System.out.println("  " + result);
        }

        // Confirm module isolation
        Module mod = cls.getModule();
        System.out.println("\n[ Module metadata ]");
        System.out.println("  Module name:   " + mod.getName());
        System.out.println("  Is named:      " + mod.isNamed());
        System.out.println("  Exports:       " + mod.getDescriptor().exports().stream()
                                                      .map(e -> e.source()).toList());
        System.out.println("  Layer:         " + layer);

        cleanup(tmp);
        printConceptSummary();
    }

    static void cleanup(Path tmp) throws IOException {
        Files.walk(tmp).sorted(Comparator.reverseOrder()).map(Path::toFile).forEach(File::delete);
        System.out.println("Cleaned up.");
    }

    static void printConceptSummary() {
        System.out.println("\n[ Module path vs classpath — when to use each ]");
        System.out.println("  Classpath  : legacy/non-modular JARs, Spring Boot, fat JARs");
        System.out.println("  Module path: explicit requires/exports, jlink, strong encapsulation");
        System.out.println("  Mixed      : --module-path mods --class-path lib/legacy.jar");
        System.out.println("\n[ Common errors ]");
        System.out.println("  module X not found                      → JAR missing from --module-path");
        System.out.println("  package X is not exported from module Y → missing 'exports' or 'opens'");
        System.out.println("  module X reads module Y which reads X   → split package or cycle");
        System.out.println("  InaccessibleObjectException             → add --add-opens M/pkg=ALL-UNNAMED");
    }
}
```

**How to run:** `java ModulePathAdvanced.java`

`ModuleFinder.of(path)` scans a directory for `module-info.class` files — exactly what `--module-path path` does at the command line. `ModuleLayer.defineModulesWithOneLoader()` creates an isolated class-loading scope; classes in one layer don't bleed into another.

## 6. Walkthrough

Execution trace in `ModulePathAdvanced.main`:

**Compilation.** `compiler.run(..., "--module-source-path", src.getParent(), "-m", "com.example.order")` compiles all source files in the `com.example.order` module tree. Output: `out/com.example.order/module-info.class` and `out/com.example.order/com/example/order/OrderService.class`. The module name `com.example.order` becomes the subdirectory name under `out/`.

**ModuleFinder.** `ModuleFinder.of(out.resolve("com.example.order"))` looks for `module-info.class` in that directory. It finds it and registers the module reference. This is the programmatic equivalent of `--module-path out/com.example.order`.

**Configuration.resolve.** `parent.configuration().resolve(finder, ModuleFinder.of(), Set.of("com.example.order"))` resolves the module graph: `com.example.order` requires only `java.base` (implicit). The resolved configuration is checked for missing or conflicting modules before any class loading.

**ModuleLayer.defineModulesWithOneLoader.** Creates a new class loader for `com.example.order`. `layer.findLoader("com.example.order")` returns that loader. `loader.loadClass("com.example.order.OrderService")` loads the class — and the loader checks that `com.example.order` exports `com.example.order` (it does) before allowing the class to be visible.

**`--add-opens` pattern.** If a framework (e.g., Jackson, Spring) needs deep reflection into a named module's package, you need `--add-opens module/pkg=ALL-UNNAMED` (or `=framework.module`). Without it, `setAccessible(true)` on a field throws `InaccessibleObjectException`.

## 7. Gotchas & takeaways

> **The unnamed module can't require named modules.** Code on the classpath lives in the "unnamed module," which reads ALL named modules but cannot be required by any named module. If you mix `-cp legacy.jar` with `--module-path app.jar`, the legacy code can use app's exported API, but `app`'s `module-info.java` can't `requires` the legacy JAR as a named module.

> **Split packages are a hard error on the module path.** If two JARs on `--module-path` contain the same package (e.g., both export `com.example.util`), the JVM refuses to start: `Error: Module X contains package P, module Y exports package P`. On the classpath, the first entry silently wins — on the module path, it's immediate death.

- `--module-path` (`-p`) — where to find modular JARs.
- `--module` (`-m`) — `moduleName/MainClass` to launch.
- `module-info.java` — `requires` (dependencies) + `exports` (public API surface) + `opens` (reflection access).
- Non-modular JAR on `--module-path` → automatic module (exports everything; name from filename).
- `--add-modules`, `--add-exports`, `--add-opens` — escape hatches for frameworks and legacy code.
- `java --list-modules` and `java --describe-module M` — built-in inspection tools.
- Use classpath for fat JARs and legacy code; module path for strong encapsulation and `jlink`.
