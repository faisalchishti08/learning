# Java Modules (JPMS) [Java 9+]

## Overview

The Java Platform Module System (JPMS, JEP 261, Java 9) introduces strong encapsulation at the package level. A **module** is a named, self-describing unit of code that explicitly declares what it **exports** (public API) and what it **requires** (dependencies). Solves classpath hell and enables explicit dependency graphs.

---

## 1. Module Basics

### Visual Diagram — Module System

```
Before Java 9 (classpath):
  All packages visible to all code
  Any class can access any other public class
  JAR hell: duplicate classes, no versioning, no encapsulation

Java 9+ (module path):
  Module A          Module B          java.base (automatic)
  ┌─────────┐       ┌─────────┐       ┌─────────────┐
  │exports  │──────▶│requires │       │java.lang    │
  │com.api  │       │com.app  │◀──────│java.util    │
  │         │       │         │ auto  │java.io ...  │
  │internal │       │internal │       └─────────────┘
  │(hidden) │       │(hidden) │
  └─────────┘       └─────────┘

Rules:
  - Packages NOT exported are invisible to all other modules (deep encapsulation)
  - requires declares compile+runtime dependency
  - exports/requires must be explicit — no implicit access
  - java.base is required by all modules implicitly
```

### Example 1 — module-info.java Structure

```java
// File: src/com.library/module-info.java
// This file defines the module declaration (not a class)
module com.library {
    // What this module exports (makes public to other modules)
    exports com.library.api;           // public API
    exports com.library.model;         // data classes
    // com.library.internal is NOT exported — hidden from all modules

    // Conditional export — only to specific modules
    exports com.library.internal to com.trusted.module;

    // What this module depends on
    requires java.base;                // implicitly always required
    requires java.logging;             // need java.util.logging
    requires com.fasterxml.jackson.databind; // third-party module

    // Transitive dependency — modules requiring this module also get java.sql
    requires transitive java.sql;

    // Open for reflection (needed by frameworks like Spring, Hibernate)
    opens com.library.model;           // allow deep reflection at runtime
    opens com.library.dao to org.hibernate.orm.core; // selective reflection

    // Service provider interface (SPI)
    uses com.library.api.DataPlugin;   // this module consumes implementations
    provides com.library.api.DataPlugin
        with com.library.impl.DefaultPlugin; // this module provides an implementation
}
```

**What this does:** `module-info.java` lives at the module root. `exports` = public API. `requires transitive` = "my consumers also need this". `opens` = allow reflection (needed for Spring/Hibernate). `uses`/`provides` = ServiceLoader SPI.

---

## 2. Creating a Multi-Module Project

### Visual Diagram — Project Layout

```
my-project/
  com.api/
    module-info.java       module com.api { exports com.api; }
    src/com/api/
      Greeter.java
  
  com.impl/
    module-info.java       module com.impl { requires com.api; provides ... }
    src/com/impl/
      EnglishGreeter.java
  
  com.app/
    module-info.java       module com.app { requires com.api; }
    src/com/app/
      Main.java

Compile:
  javac --module-source-path src -d mods --module com.api,com.impl,com.app

Run:
  java --module-path mods -m com.app/com.app.Main
```

### Example 1 — Three-Module Setup

```java
// === Module 1: com.api ===
// module-info.java
module com.api {
    exports com.api;
}

// com/api/Greeter.java
package com.api;
public interface Greeter {
    String greet(String name);
}

// === Module 2: com.impl ===
// module-info.java
module com.impl {
    requires com.api;
    provides com.api.Greeter with com.impl.EnglishGreeter;
}

// com/impl/EnglishGreeter.java
package com.impl;
import com.api.Greeter;
public class EnglishGreeter implements Greeter {
    @Override public String greet(String name) { return "Hello, " + name + "!"; }
}

// === Module 3: com.app ===
// module-info.java
module com.app {
    requires com.api;
    uses com.api.Greeter; // discover implementations via ServiceLoader
}

// com/app/Main.java
package com.app;
import com.api.Greeter;
import java.util.ServiceLoader;

public class Main {
    public static void main(String[] args) {
        ServiceLoader<Greeter> loader = ServiceLoader.load(Greeter.class);
        loader.findFirst().ifPresent(g ->
            System.out.println(g.greet("World")) // Hello, World!
        );
    }
}
```

**What this does:** Three modules — interface, implementation, consumer. `com.impl` is not directly in `com.app`'s `requires` — discovered at runtime via `ServiceLoader`. This is the module-aware SPI pattern.

---

## 3. Module Directives Reference

### Visual Diagram — All Directives

```
module com.example {

  requires <module>                 ← compile + runtime dependency
  requires transitive <module>      ← dependency is re-exported to consumers
  requires static <module>          ← compile-time only (optional at runtime)

  exports <package>                 ← accessible to all modules
  exports <package> to <module>     ← accessible only to named module(s)

  opens <package>                   ← deep reflection allowed (runtime only)
  opens <package> to <module>       ← reflection only to named module(s)

  uses <service-interface>          ← discovers implementations via ServiceLoader
  provides <interface> with <impl>  ← registers implementation for ServiceLoader
}
```

### Example 1 — requires transitive

```java
// Module: com.data
module com.data {
    requires transitive java.sql; // whoever requires com.data also gets java.sql
    exports com.data;
}

// Module: com.service
module com.service {
    requires com.data; // implicitly also has java.sql via transitive
    // can use java.sql.Connection etc. without explicit "requires java.sql"
}
```

**What this does:** `requires transitive` is for "implied readability" — if your API types in exported packages include types from `java.sql`, clients need `java.sql` too. Avoid making consumers declare unnecessary `requires`.

---

## 4. Unnamed Module and Automatic Modules

### Visual Diagram

```
Named module:    has module-info.java, explicit declarations
Unnamed module:  everything on the classpath (no module-info.java)
                 can READ all other modules, but no module can READ it (unnamed)
                 used for backward compatibility

Automatic module: JAR on the module path WITHOUT module-info.java
                  gets a module name derived from JAR filename
                  e.g.: jackson-databind-2.15.0.jar → com.fasterxml.jackson.databind (or similar)
                  exports ALL packages
                  requires ALL other modules
                  used for migration period

Module type    | module-info.java | on module-path | on classpath
Named          | YES              | YES            | NO (becomes unnamed)
Automatic      | NO               | YES            | NO
Unnamed        | NO               | NO             | YES (everything old)
```

---

## 5. JVM Module Flags

### Example 1 — Opening Modules for Reflection (Spring/Hibernate)

```bash
# Spring needs to reflect on your classes — they're in your named module
# Without opens: InaccessibleObjectException at runtime

# Option 1: open the package in module-info.java (preferred)
module com.myapp {
    opens com.myapp.model; // Spring can reflect
}

# Option 2: command-line flag (for code you can't modify)
java --add-opens java.base/java.lang=com.myapp --module-path mods -m com.myapp/Main

# Option 3: open entire module
open module com.myapp { // all packages open for reflection
    requires spring.context;
}

# Add reads between modules at runtime
java --add-reads com.myapp=java.logging

# Add export at runtime (use sparingly)
java --add-exports java.base/sun.misc=com.myapp
```

### Example 2 — Checking Module Info at Runtime

```java
public class ModuleInspection {
    public static void main(String[] args) {
        Module m = ModuleInspection.class.getModule();

        System.out.println("Module name: " + m.getName());
        System.out.println("Is named: " + m.isNamed());

        // Inspect module descriptor
        if (m.isNamed()) {
            var desc = m.getDescriptor();
            System.out.println("Exports: " + desc.exports());
            System.out.println("Requires: " + desc.requires());
        }

        // Check if package is exported
        Module javaBase = String.class.getModule();
        System.out.println("java.base name: " + javaBase.getName()); // java.base
    }
}
```

---

## 6. jlink — Custom Runtime Images [Java 9+]

### What is it

`jlink` packages only the modules your application uses into a minimal JVM runtime image. Instead of shipping a full 300MB JDK, ship a 50MB custom runtime.

```bash
# List available modules
java --list-modules

# Create minimal runtime with only needed modules
jlink \
  --module-path mods:$JAVA_HOME/jmods \
  --add-modules com.myapp,java.base,java.logging \
  --output dist/myapp-runtime \
  --strip-debug \
  --compress=2

# Result: dist/myapp-runtime/bin/java — minimal JVM
dist/myapp-runtime/bin/java -m com.myapp/com.myapp.Main
```

---

## 7. Migration Strategy

### Diagram — Migrating Legacy Code to Modules

```
Step 1: Analyze dependencies
  jdeps --class-path libs/*.jar app.jar
  Shows what your code uses from JDK + libraries

Step 2: Add module-info.java gradually
  Start with automatic modules on module path
  Add module-info.java when ready

Step 3: Handle reflection access
  If code uses internal JDK APIs (sun.misc.Unsafe etc.):
    Check if alternative exists in public API first
    Use --add-exports/--add-opens as temporary bridge

Step 4: Split packages (illegal in module system)
  Two modules cannot have the same package name
  Refactor if needed before modularizing

Common issues:
  - InaccessibleObjectException: framework can't reflect → add opens
  - Package split between modules → refactor package names
  - Automatic module names unstable → wait for library to add module-info.java
```

---

## Quick Reference

```
module-info.java keywords:
  module com.name {}            declare module
  requires com.other            dependency
  requires transitive com.x     re-exported dependency
  requires static com.x         compile-only (optional runtime)
  exports com.pkg               public API
  exports com.pkg to com.other  restricted export
  opens com.pkg                 allow deep reflection
  opens com.pkg to com.other    restricted reflection
  uses com.api.Service          consume via ServiceLoader
  provides com.api.Service      register implementation
    with com.impl.ServiceImpl

Command-line flags:
  --module-path <path>          module search path
  -m com.app/com.app.Main       launch module/class
  --add-opens m/pkg=other       open package for reflection
  --add-exports m/pkg=other     export package
  --add-reads m=other           add readability
  --list-modules                list observable modules

jdeps:
  jdeps --module-path ... -m com.app   analyze dependencies
  jdeps --class-path libs app.jar      analyze classpath app

jlink:
  jlink --module-path ... --add-modules ... --output dist/runtime
```
