---
card: java
gi: 575
slug: opens-directive-reflection
title: opens directive (reflection)
---

## 1. What it is

The `opens` directive inside `module-info.java` grants **runtime reflective access** into a package — permitting operations like `setAccessible(true)` that bypass normal Java access checks (reaching private fields, private constructors, non-public methods). It's a separate permission from `exports`: `exports` allows normal, compile-time-checked use of a package's public API; `opens` allows deep reflection into that package's internals, public or not.

## 2. Why & when

Many popular frameworks — JSON libraries like Jackson or Gson, ORMs like Hibernate, dependency-injection containers, testing frameworks like JUnit — rely on reflection to construct objects and read/write fields the calling code never directly names: deserializing JSON into a POJO by reflectively setting private fields, or a DI container injecting into a private field annotated `@Inject`. Before modules, this always worked, because the classpath had no concept of restricting reflection. With modules, `exports` alone is not enough to permit this: a module can `exports` a package (letting other code compile against its public API) while still refusing reflective access into its guts, since exports only governs ordinary access-checked usage. `opens` exists specifically to grant that additional, more invasive permission — deliberately, package by package, so a module author decides exactly which packages allow deep reflection rather than exposing everything by default.

## 3. Core concept

```java
module myapp {
    exports com.myapp.api;      // normal compile-time use is fine
    opens com.myapp.model;      // reflective access (e.g. by a JSON library) is fine here too
    // com.myapp.internal has neither -- no compile-time use, no reflection, fully sealed
}
```

```java
package com.myapp.model;

public class User {
    private String name; // private field a JSON library needs to set reflectively
}
```

Without `opens com.myapp.model;`, a JSON library calling `field.setAccessible(true)` on `User.name` from a different module would throw `InaccessibleObjectException` at runtime — even though `com.myapp.model` might be `exports`-ed for ordinary use, `exports` alone never grants that deeper reflective permission.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="exports permits normal compiled access; opens additionally permits deep reflection bypassing access checks">
  <text x="20" y="25" fill="#8b949e" font-size="11" font-family="sans-serif">exports only — normal use OK, reflection blocked:</text>
  <rect x="20" y="35" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="57" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">import + call public API</text>
  <rect x="220" y="35" width="180" height="34" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="310" y="57" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">setAccessible(true) -&gt; throws</text>

  <text x="20" y="105" fill="#8b949e" font-size="11" font-family="sans-serif">exports + opens — both normal use AND reflection OK:</text>
  <rect x="20" y="115" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="137" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">import + call public API</text>
  <rect x="220" y="115" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="310" y="137" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">setAccessible(true) -&gt; works</text>
</svg>

Two separate permissions, two separate directives — a package can have either, both, or neither.

## 5. Runnable example

Scenario: a tiny hand-rolled reflective "field dumper" utility standing in for what a real JSON/serialization library does — starting with a model class whose package is exported but not opened (reflection fails), then opening the package to permit it, then restricting that reflective access to only one specific trusted module with a qualified `opens ... to`.

### Level 1 — Basic

```java
// File: model/module-info.java — exported, but NOT opened
module model {
    exports com.model;
}
```

```java
// File: model/com/model/User.java
package com.model;

public class User {
    private final String name;
    private final int age;

    public User(String name, int age) {
        this.name = name;
        this.age = age;
    }
}
```

```java
// File: tooling/module-info.java
module tooling {
    requires model;
}
```

```java
// File: tooling/com/tooling/FieldDumper.java
package com.tooling;
import com.model.User;
import java.lang.reflect.Field;

public class FieldDumper {
    public static void dump(Object target) throws Exception {
        for (Field field : target.getClass().getDeclaredFields()) {
            field.setAccessible(true); // deep reflection — needs "opens", not just "exports"
            System.out.println(field.getName() + " = " + field.get(target));
        }
    }

    public static void main(String[] args) throws Exception {
        dump(new User("Ada", 30));
    }
}
```

**How to run:** `javac -d out --module-source-path . $(find model tooling -name "*.java") && java --module-path out -m tooling/com.tooling.FieldDumper`

Expected output (throws at runtime — this is the intended demonstration):
```
Exception in thread "main" java.lang.reflect.InaccessibleObjectException: Unable to make field private final java.lang.String com.model.User.name accessible: module model does not "opens com.model" to module tooling
```

Compilation succeeds — `field.setAccessible(true)` is legal Java syntax regardless of modules — but the call **throws at runtime**, because `com.model` is `exports`-ed (fine for `new User(...)`, a normal constructor call) but not `opens`-ed, and reflectively bypassing `private` access checks requires that stronger, separate permission.

### Level 2 — Intermediate

```java
// File: model/module-info.java — add opens
module model {
    exports com.model;
    opens com.model; // now reflective access is permitted too
}
```

```java
// File: model/com/model/User.java — unchanged
package com.model;

public class User {
    private final String name;
    private final int age;

    public User(String name, int age) {
        this.name = name;
        this.age = age;
    }
}
```

```java
// File: tooling/com/tooling/FieldDumper.java — unchanged from Level 1
package com.tooling;
import com.model.User;
import java.lang.reflect.Field;

public class FieldDumper {
    public static void dump(Object target) throws Exception {
        for (Field field : target.getClass().getDeclaredFields()) {
            field.setAccessible(true);
            System.out.println(field.getName() + " = " + field.get(target));
        }
    }

    public static void main(String[] args) throws Exception {
        dump(new User("Ada", 30));
    }
}
```

**How to run:** `javac -d out --module-source-path . $(find model tooling -name "*.java") && java --module-path out -m tooling/com.tooling.FieldDumper`

Expected output:
```
name = Ada
age = 30
```

The real-world concern this adds: with the single word `opens com.model;` added, the exact same `FieldDumper` code that threw in Level 1 now works — this is precisely how a real serialization library (Jackson, Gson) would need your module's classes to be declared in order to reflectively read/write private fields during (de)serialization.

### Level 3 — Advanced

```java
// File: model/module-info.java — restrict reflection to ONE trusted module
module model {
    exports com.model;
    opens com.model to tooling; // reflective access ONLY for "tooling", not every module
}
```

```java
// File: outsider/module-info.java — a second module, also requires model
module outsider {
    requires model;
}
```

```java
// File: outsider/com/outsider/Snoop.java — attempts the same reflection tooling does
package com.outsider;
import com.model.User;
import java.lang.reflect.Field;

public class Snoop {
    public static void main(String[] args) throws Exception {
        User user = new User("Ada", 30);
        Field field = User.class.getDeclaredField("name");
        field.setAccessible(true); // will throw for THIS module, though not for "tooling"
        System.out.println(field.get(user));
    }
}
```

**How to run:** `javac -d out --module-source-path . $(find model tooling outsider -name "*.java") && java --module-path out -m outsider/com.outsider.Snoop`

Expected output (throws at runtime — this is the intended demonstration):
```
Exception in thread "main" java.lang.reflect.InaccessibleObjectException: Unable to make field private final java.lang.String com.model.User.name accessible: module model does not "opens com.model" to module outsider
```

This handles the production-flavoured payoff: `opens com.model to tooling;` grants reflective access **only** to the module named `tooling` — running `tooling/com.tooling.FieldDumper` (from Level 2, still present and still compiled against the same `model`) continues to succeed, while `outsider`, despite also legitimately requiring `model` and using the identical `setAccessible(true)` pattern, is rejected, because it wasn't named in the qualified `opens` clause.

## 6. Walkthrough

Execution starts with the compilation and launch commands in Level 3, which build `model` (with the qualified `opens com.model to tooling;`), `tooling`, and `outsider` together, then launch `outsider/com.outsider.Snoop`.

Compilation succeeds for all three modules — `opens` (qualified or not) has no effect on compile-time checks at all; `field.setAccessible(true)` is ordinary, always-legal Java reflection API usage as far as `javac` is concerned. The module system's `opens` permission is checked entirely at **runtime**, the first time reflective access is actually attempted.

```
Runtime reflective access check, when setAccessible(true) is called:

tooling calling User.class.getDeclaredField("name").setAccessible(true):
  -> model opens com.model "to tooling"  -> tooling IS named -> permitted

outsider calling the same:
  -> model opens com.model "to tooling"  -> outsider is NOT named -> InaccessibleObjectException
```

`java --module-path out -m outsider/com.outsider.Snoop` launches `Snoop.main`. `new User("Ada", 30)` succeeds normally — this is ordinary constructor invocation through `com.model`'s exported public API, governed by `exports`, unaffected by `opens` at all. `User.class.getDeclaredField("name")` also succeeds — merely *obtaining* a `Field` reflection object for a private field doesn't require any special module permission; it's `setAccessible(true)`, the call that actually attempts to suppress Java's access checks for future use of that `Field`, which triggers the module system's runtime check.

At that `setAccessible(true)` call, the JVM checks whether `outsider` (the module that made this reflective call) is permitted to reflectively access `com.model`. Because the `opens` directive names only `tooling`, and this call originates from `outsider`'s code, the check fails, and `InaccessibleObjectException` is thrown immediately — `Snoop.main` never reaches the subsequent `field.get(user)` line, since the exception propagates uncaught out of `main` and terminates the program.

Had this same `dump(...)`-style reflection been invoked from `tooling`'s `FieldDumper` (as it was, successfully, in Level 2's identical setup), the check at `setAccessible(true)` would find `tooling` named in the qualified `opens` clause, permit the operation, and let execution proceed exactly as demonstrated in Level 2 — reading and printing `"Ada"` and `30` for the `name` and `age` fields respectively.

## 7. Gotchas & takeaways

> `opens` grants reflective access at **runtime only** — it does not, by itself, make a package's types importable and directly usable in normal compiled code the way `exports` does. A package can be `opens`-ed without being `exports`-ed at all, which is common for internal model or DTO classes a framework needs to reflect into (for JSON binding, ORM mapping) but that were never meant to be part of the module's compiled, public, `import`-able API surface.

- `open module modulename { ... }` (note `open` before the `module` keyword) opens **every** package in the module for unrestricted reflection at once — a common blanket fix for modules with pervasive reflection needs across many packages, at the cost of losing per-package control.
- `opens` (like `exports`) supports the qualified form (`opens pkg to module1, module2`) for restricting reflective access to specific trusted modules — exactly as demonstrated in Level 3 — useful for limiting which frameworks or tools can reflectively poke into your internals.
- The reflective operations `opens` actually gates are specifically the ones that call `setAccessible(true)` (or its equivalents used internally by `Field.get`/`.set`, `Constructor.newInstance`, `Method.invoke` on non-public members) — reflecting on already-`public` members without ever bypassing an access check does not require `opens` at all, only `exports`.
- Many serialization/DI frameworks that predate the module system (or that support pre-module classpath usage as well) rely on this reflection pattern pervasively — migrating an existing classpath-based application that uses such a framework into the module system often requires adding `opens` (sometimes to `ALL-UNNAMED`, a special target representing classpath code, when the framework itself isn't modularized) as part of the migration.
- `--add-opens module/package=target` is a JVM command-line flag that can grant `opens`-equivalent permission at launch time without modifying `module-info.java` at all — a common escape hatch for third-party JARs whose module declarations can't easily be changed, though it's a workaround best treated as temporary rather than a substitute for properly declaring `opens` in your own modules.
