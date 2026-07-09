---
card: java
gi: 572
slug: requires-static
title: requires static
---

## 1. What it is

`requires static` is a variant of `requires` that makes a dependency mandatory **only at compile time**, optional at runtime. The declaring module can reference the required module's types while compiling, but the JVM does not insist that module be present when the application actually launches — if it's absent at runtime, the module still loads successfully, as long as none of the optional dependency's types are actually touched during execution.

## 2. Why & when

Some dependencies are used for a small, optional feature that most consumers of a library never need — a common example is annotation-only libraries (like `org.jetbrains.annotations` or certain validation-annotation modules) that a class references purely for compile-time tooling/documentation purposes (`@Nullable`, `@NotNull`) and that have no effect at runtime at all, or optional integrations (a library that can *optionally* integrate with a JSON library if it's present, but works fine without it). Requiring these unconditionally with plain `requires` would force every single consumer to have that optional module on their module path just to launch the application, even if they never use the optional feature. `requires static` lets the library compile against the optional dependency's types while leaving it out of the mandatory runtime requirement — consumers who want the optional feature add the dependency themselves; consumers who don't, simply omit it, and the application still starts.

## 3. Core concept

```java
module mylib {
    requires static com.some.optional.annotations; // compile-time only
    exports com.mylib.api;
}
```

```java
package com.mylib.api;
import com.some.optional.annotations.Nullable;

public class Widget {
    @Nullable
    public String getLabel() { return label; } // annotation is compile-time metadata only
    private String label;
}
```

At compile time, `mylib` needs `com.some.optional.annotations` on the module path to resolve `@Nullable`. At runtime, if a consumer's module path omits `com.some.optional.annotations` entirely, the JVM still lets `mylib` load and run — as long as nothing at runtime actually tries to load the `Nullable` annotation class itself (annotations retained only at `SOURCE` or with no runtime reflection on them typically pose no issue; annotations with `RUNTIME` retention that get reflectively inspected would still need the class present when that reflection actually runs).

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="requires static is enforced at compile time but optional at runtime, unlike plain requires which is enforced at both">
  <text x="20" y="25" fill="#8b949e" font-size="11" font-family="sans-serif">plain requires — enforced at BOTH stages:</text>
  <rect x="20" y="35" width="150" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="95" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">compile: mandatory</text>
  <rect x="180" y="35" width="150" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="255" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">runtime: mandatory</text>

  <text x="20" y="100" fill="#8b949e" font-size="11" font-family="sans-serif">requires static — compile mandatory, runtime OPTIONAL:</text>
  <rect x="20" y="110" width="150" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="95" y="130" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">compile: mandatory</text>
  <rect x="180" y="110" width="150" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="255" y="130" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">runtime: optional</text>
</svg>

The module still has to exist when `javac` compiles the declaring module, but `java` won't refuse to launch a consumer that omits it.

## 5. Runnable example

Scenario: a small "validation" utility module that references an optional `@Experimental` marker annotation from a separate module purely for documentation/tooling purposes — starting with a plain mandatory `requires` that forces every consumer to have the annotation module present, then switching to `requires static` so consumers can omit it, then verifying that a consumer genuinely runs successfully without the optional module on its module path.

### Level 1 — Basic

```java
// File: markers/module-info.java
module markers {
    exports com.markers;
}
```

```java
// File: markers/com/markers/Experimental.java
package com.markers;
import java.lang.annotation.*;

@Retention(RetentionPolicy.CLASS) // present in .class files, but NOT loaded/inspected at runtime by default
public @interface Experimental {}
```

```java
// File: validation/module-info.java — PLAIN requires, mandatory at runtime too
module validation {
    requires markers;
    exports com.validation;
}
```

```java
// File: validation/com/validation/Validator.java
package com.validation;
import com.markers.Experimental;

public class Validator {
    @Experimental
    public boolean isValid(String input) {
        return input != null && !input.isBlank();
    }
}
```

**How to run:** `javac -d out --module-source-path . $(find markers validation -name "*.java")`

Expected output: compiles cleanly (this level only establishes the baseline — the runtime consequence shows up once a consumer tries to launch without `markers`, in Level 2).

`Validator` uses `@Experimental` purely as documentation-style metadata — it has no runtime behavior at all (`RetentionPolicy.CLASS` means it's kept in the `.class` file for tools, but not loaded by the JVM's classloader at runtime unless something explicitly inspects it via reflection). Even so, plain `requires markers` in `validation`'s `module-info.java` makes `markers` a *mandatory* dependency for every consumer of `validation`, at both compile time and runtime — whether or not they care about `@Experimental` at all.

### Level 2 — Intermediate

```java
// File: app/module-info.java — consumer WITHOUT markers on its module path
module app {
    requires validation;
}
```

```java
// File: app/com/myapp/Main.java
package com.myapp;
import com.validation.Validator;

public class Main {
    public static void main(String[] args) {
        Validator validator = new Validator();
        System.out.println("Valid: " + validator.isValid("hello"));
    }
}
```

**How to run:** compile all three modules, then try to launch with only `validation` and `app`'s output present — deliberately excluding `markers` from the runtime module path:
```
javac -d out --module-source-path . $(find markers validation app -name "*.java")
java --module-path out/app:out/validation -m app/com.myapp.Main
```

Expected output (launch fails — this is the intended demonstration):
```
Error occurred during initialization of boot layer
java.lang.module.FindException: Module markers not found, required by validation
```

The real-world concern this adds: because `validation` declared a **plain, mandatory** `requires markers`, the JVM's module resolution at startup refuses to launch `app` at all unless `markers` is present on the module path — even though `Main.java` never uses `@Experimental` or anything from `markers` directly, and `Validator.isValid(...)` doesn't actually need `markers` present to run correctly at runtime, since the annotation itself is never loaded during normal execution.

### Level 3 — Advanced

```java
// File: validation/module-info.java — switched to requires static
module validation {
    requires static markers; // mandatory to COMPILE validation, optional at runtime for consumers
    exports com.validation;
}
```

```java
// File: app/module-info.java — UNCHANGED, still just requires validation, no markers at all
module app {
    requires validation;
}
```

```java
// File: app/com/myapp/Main.java — UNCHANGED
package com.myapp;
import com.validation.Validator;

public class Main {
    public static void main(String[] args) {
        Validator validator = new Validator();
        System.out.println("Valid: " + validator.isValid("hello"));
    }
}
```

**How to run:**
```
javac -d out --module-source-path . $(find markers validation app -name "*.java")
java --module-path out/app:out/validation -m app/com.myapp.Main
```

Expected output:
```
Valid: true
```

This handles the production-flavoured fix: with only the single word `static` added to `validation`'s `requires markers` line, and `markers` deliberately still excluded from the runtime module path (`--module-path` only lists `out/app:out/validation`, omitting `out/markers` entirely), the application now launches and runs successfully — the JVM's module resolver treats a `requires static` dependency as satisfiable-or-absent at runtime, only enforcing it during `validation`'s own compilation.

## 6. Walkthrough

Execution starts with the compilation command shared by Levels 2 and 3 — `javac` compiles all three modules together (`markers`, `validation`, `app`), and this step succeeds identically in both levels, because `requires static markers` is still a real, mandatory dependency **for compilation**: `javac` needs `markers` present to resolve the `@Experimental` annotation type when compiling `Validator.java`.

The difference appears at the `java --module-path out/app:out/validation -m app/com.myapp.Main` step, which deliberately omits `out/markers` from the module path — simulating a consumer who never added the optional `markers` module to their deployment.

```
JVM module resolution at startup:

app requires validation           -> validation IS on the module path -> OK
validation requires markers       -> plain requires: mandatory -> markers MISSING -> FAIL (Level 2)
validation requires static markers -> optional requires: markers MISSING is OK -> proceed (Level 3)
```

In Level 2 (plain `requires markers`), the JVM's module resolution algorithm — which runs before any application code executes, while building the "module graph" for the launch — sees that `validation` has an unconditional dependency on `markers`, finds `markers` absent from the module path, and refuses to construct a valid module graph at all. The JVM exits immediately with `FindException`, and `Main.main` never runs.

In Level 3 (`requires static markers`), the JVM's resolver treats this edge differently: it's allowed to be absent. Module graph construction succeeds without `markers` in it at all. `app/com.myapp.Main` then launches normally: `Main.main` creates a `Validator` and calls `validator.isValid("hello")`. Inside `isValid`, the method body only checks `input != null && !input.isBlank()` — it never actually loads or inspects the `@Experimental` annotation class at runtime (annotations are only loaded reflectively if something explicitly asks for them, e.g., via `getAnnotation(...)`), so the fact that `markers` isn't even present doesn't matter for this call's actual execution. `isValid("hello")` returns `true` (a non-null, non-blank string), and `Main` prints `"Valid: true"`.

Had `Validator`'s code path actually attempted runtime reflection on `@Experimental` (e.g., `method.getAnnotation(Experimental.class)`), that specific call would throw `NoClassDefFoundError` at the moment it ran, since the annotation's class genuinely isn't available — `requires static` defers the "is this actually needed" question from "at JVM startup, unconditionally" to "only if and when this specific code path actually executes and needs it."

## 7. Gotchas & takeaways

> `requires static` shifts a missing dependency from a **guaranteed, early, clear failure** (JVM refuses to start, in Level 2) to a **possible, later, path-dependent failure** (a `NoClassDefFoundError` only if and when the optional type is actually touched at runtime). This trade-off is exactly right for genuinely optional features nobody depends on, but is a footgun if applied to something that actually matters at runtime — always verify the specific code paths that use a `requires static` dependency handle its absence gracefully (or document clearly that consumers wanting that feature must add the dependency themselves), rather than assuming "it compiled, so it's fine."

- `requires static` is most commonly seen with compile-time-only annotation libraries (nullability annotations, certain Lombok-adjacent tooling, static-analysis markers) that have zero runtime footprint by design — `RetentionPolicy.SOURCE` or `CLASS` annotations are the safest fit, since they're guaranteed never to be loaded reflectively at runtime.
- Combining `requires static transitive` is legal and propagates the *optionality* along with the visibility — a consumer that requires your module also gets the option (not obligation) to have that dependency present.
- Unlike plain `requires`, where a missing dependency is caught immediately and identically for every consumer, a `requires static` dependency's absence is only discovered by whichever consumer actually exercises the code path that needs it — meaning it's easy for this kind of gap to slip past testing if the optional feature isn't well covered.
- `requires static` does not make the dependency optional **at compile time** — `javac` still needs it present to compile the declaring module itself; it only relaxes the runtime requirement for that module's own consumers.
- This is functionally similar in spirit to Maven's `<optional>true</optional>` or Gradle's `compileOnly` configuration for classpath-based projects — `requires static` is the module system's native equivalent, now enforced by the JVM's own module resolver rather than left entirely to build-tool convention.
