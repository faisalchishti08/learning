---
card: java
gi: 573
slug: exports-directive
title: exports directive
---

## 1. What it is

The `exports` directive inside `module-info.java` declares that a package's `public` types are accessible to other modules. Without an `exports` line for a package, that package is invisible outside its own module at both compile time and runtime — even though its classes may be declared `public`, `public` alone no longer means "usable by the world" once a module boundary exists.

## 2. Why & when

On the classpath, every `public` class in every JAR was reachable from anywhere else on the classpath — there was no way for a library to say "these types are my internal implementation, don't depend on them" except a comment or a package name like `internal` that nothing actually enforced. `exports` gives that intention real teeth: a package left out of every `exports` line is compiled and packaged as part of the module, fully usable inside it, but genuinely unreachable — a compile error, not just a lint warning — from any other module, no matter how public its classes are declared. Use `exports` for every package that forms your module's intended public API, and deliberately leave internal packages unexported so consumers can never accidentally (or intentionally) couple to implementation details you want the freedom to change later.

## 3. Core concept

```java
module mylib {
    exports com.mylib.api;      // public types here are usable by any module that requires mylib
    // com.mylib.internal is NOT exported — invisible outside this module, even though its classes are public
}
```

```java
package com.mylib.internal;

public class Helper { // public, but still hidden — exports (or its absence) governs cross-module visibility
    public static void doWork() {}
}
```

A consuming module's `import com.mylib.internal.Helper;` fails to compile — not because `Helper` isn't `public`, but because `com.mylib.internal` was never named in any `exports` line.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Only exported packages are visible outside the module; unexported packages stay hidden regardless of class visibility">
  <rect x="20" y="20" width="280" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">module mylib</text>

  <rect x="40" y="55" width="240" height="35" rx="6" fill="#0d1117" stroke="#79c0ff"/>
  <text x="160" y="77" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">com.mylib.api  (exports)</text>

  <rect x="40" y="100" width="240" height="35" rx="6" fill="#0d1117" stroke="#f85149"/>
  <text x="160" y="122" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">com.mylib.internal (no exports)</text>

  <line x1="300" y1="72" x2="380" y2="72" stroke="#6db33f" stroke-width="2" marker-end="url(#e1)"/>
  <text x="480" y="62" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">other modules: import OK</text>

  <line x1="300" y1="117" x2="380" y2="117" stroke="#f85149" stroke-width="2" stroke-dasharray="4,3"/>
  <text x="480" y="132" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">other modules: compile error</text>

  <defs>
    <marker id="e1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The `exports` line is the single switch that determines cross-module reachability, independent of the `public` keyword on the classes inside.

## 5. Runnable example

Scenario: a small "text utilities" library with a clean public API and a private implementation detail — starting with everything accidentally left unexported (nothing usable), then exporting only the intended API package, then verifying the internal package genuinely stays hidden even under direct, deliberate attempts to reach it.

### Level 1 — Basic

```java
// File: textutils/module-info.java — accidentally empty, nothing exported yet
module textutils {
}
```

```java
// File: textutils/com/textutils/api/TextCleaner.java
package com.textutils.api;

public class TextCleaner {
    public static String clean(String input) {
        return input == null ? "" : input.trim().replaceAll("\\s+", " ");
    }
}
```

```java
// File: app/module-info.java
module app {
    requires textutils;
}
```

```java
// File: app/com/myapp/Main.java
package com.myapp;
import com.textutils.api.TextCleaner;

public class Main {
    public static void main(String[] args) {
        System.out.println("[" + TextCleaner.clean("  hello   world  ") + "]");
    }
}
```

**How to run:** `javac -d out --module-source-path . $(find textutils app -name "*.java")`

Expected output (compilation fails — this is the intended demonstration):
```
app/com/myapp/Main.java:2: error: package com.textutils.api is not visible
import com.textutils.api.TextCleaner;
                     ^
  (package com.textutils.api is declared in module textutils, which does not export it)
```

`textutils`'s `module-info.java` declares the module but exports nothing at all — a common mistake when first setting up a module. Even though `TextCleaner` is `public` and `app` correctly declares `requires textutils`, the compiler still rejects the import: `requires` only grants access to a module's *exported* packages, and right now there are none.

### Level 2 — Intermediate

```java
// File: textutils/module-info.java — export the API package
module textutils {
    exports com.textutils.api;
}
```

```java
// File: textutils/com/textutils/api/TextCleaner.java — unchanged
package com.textutils.api;

public class TextCleaner {
    public static String clean(String input) {
        return input == null ? "" : input.trim().replaceAll("\\s+", " ");
    }
}
```

```java
// File: app/module-info.java — unchanged
module app {
    requires textutils;
}
```

```java
// File: app/com/myapp/Main.java — unchanged
package com.myapp;
import com.textutils.api.TextCleaner;

public class Main {
    public static void main(String[] args) {
        System.out.println("[" + TextCleaner.clean("  hello   world  ") + "]");
    }
}
```

**How to run:**
```
javac -d out --module-source-path . $(find textutils app -name "*.java")
java --module-path out -m app/com.myapp.Main
```

Expected output:
```
[hello world]
```

The real-world concern this adds: with **exactly one word added** (`exports com.textutils.api;`), the same consumer code that failed in Level 1 now compiles and runs — this is the entire fix for "my module compiles fine on its own but nothing can use it," a very common first encounter with the module system.

### Level 3 — Advanced

```java
// File: textutils/module-info.java — add an internal package, deliberately NOT exported
module textutils {
    exports com.textutils.api;
    // com.textutils.internal intentionally has no exports line
}
```

```java
// File: textutils/com/textutils/internal/RegexCache.java — public, but not exported
package com.textutils.internal;
import java.util.regex.Pattern;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class RegexCache { // public class...
    private static final Map<String, Pattern> CACHE = new ConcurrentHashMap<>();

    public static Pattern get(String regex) { // ...with a public method...
        return CACHE.computeIfAbsent(regex, Pattern::compile);
    }
}
```

```java
// File: textutils/com/textutils/api/TextCleaner.java — uses RegexCache internally (same module, always OK)
package com.textutils.api;
import com.textutils.internal.RegexCache;

public class TextCleaner {
    public static String clean(String input) {
        if (input == null) return "";
        return RegexCache.get("\\s+").matcher(input.trim()).replaceAll(" ");
    }
}
```

```java
// File: app/com/myapp/Main.java — attempts to reach the internal package directly
package com.myapp;
import com.textutils.api.TextCleaner;
import com.textutils.internal.RegexCache; // <- this import will fail to compile

public class Main {
    public static void main(String[] args) {
        System.out.println("[" + TextCleaner.clean("  hello   world  ") + "]");
        System.out.println(RegexCache.get("\\d+")); // never reached — compilation fails first
    }
}
```

**How to run:** `javac -d out --module-source-path . $(find textutils app -name "*.java")`

Expected output (compilation fails — this is the intended demonstration):
```
app/com/myapp/Main.java:3: error: package com.textutils.internal is not visible
import com.textutils.internal.RegexCache;
                      ^
  (package com.textutils.internal is declared in module textutils, which does not export it)
1 error
```

This handles the production-flavoured payoff: `RegexCache` is a genuinely `public` class with a genuinely `public` static method, used internally by `TextCleaner` without any issue (same-module access is always unrestricted) — but a consumer's attempt to reach it directly is rejected at compile time, precisely and only because `com.textutils.internal` was deliberately left off every `exports` line. This is the real protection `exports` provides: not obscurity or convention, but an enforced boundary.

## 6. Walkthrough

Execution starts with the compilation command in Level 3. `javac` reads `textutils/module-info.java`, recording that this module exports `com.textutils.api` and nothing else — `com.textutils.internal` is a real package inside the module (its classes compile fine as part of `textutils` itself) but is absent from every `exports` line.

`javac` compiles `textutils`'s own source files first. `TextCleaner.java`'s `import com.textutils.internal.RegexCache` succeeds without any issue, because module boundaries only restrict access *between* modules — `TextCleaner` and `RegexCache` are both inside `textutils`, so intra-module visibility applies, governed only by ordinary Java access modifiers (both are `public`, so this would work regardless).

```
Within textutils (same module):
  TextCleaner --imports--> RegexCache        -> OK (module boundary doesn't apply intra-module)

Between modules (app requires textutils):
  Main --imports--> com.textutils.api.TextCleaner       -> OK (exported)
  Main --imports--> com.textutils.internal.RegexCache    -> ERROR (not exported)
```

`javac` then moves to compiling `app`'s `Main.java`. The first import, `com.textutils.api.TextCleaner`, resolves successfully — `app` requires `textutils`, and `com.textutils.api` is exported. The second import, `com.textutils.internal.RegexCache`, is checked against the same rule: `app` requires `textutils`, but `com.textutils.internal` was never named in an `exports` line, so this package is treated as though it doesn't exist from `app`'s perspective. `javac` reports the "not visible" error immediately and halts — the `println` call referencing `RegexCache` inside `Main.main` is never even reached, because compilation fails before any code would run.

If the offending import and the line using it were removed, `Main.java` would compile and run exactly as in Level 2: `TextCleaner.clean("  hello   world  ")` calls `RegexCache.get("\\s+")` internally (legal, same-module access), which lazily compiles and caches a `Pattern` for the whitespace regex, then applies it via `matcher(...).replaceAll(" ")` to collapse the input's internal whitespace runs into single spaces after trimming — producing `"hello world"`, printed inside brackets as `"[hello world]"`.

## 7. Gotchas & takeaways

> A package with no `exports` line is not merely "discouraged from use" — it is **structurally invisible** to every other module, checked by the compiler on every single build, not by a linter that can be silenced or a code-review comment that can be missed. This is a stronger guarantee than any pre-module convention (naming a package `internal`, documenting "do not use") ever provided, and it's the single biggest practical benefit of adopting the module system for library authors.

- Forgetting to `exports` a package you *meant* to make public (as in the Level 1 example) is a very common first mistake — if a module compiles fine on its own but every consumer fails with "package ... is not visible," check the module's own `exports` list first.
- `exports` grants visibility to every module that requires the exporting module — for restricting a package to one or a few specific, named consumer modules instead, use the qualified form (`exports pkg to specificModule`), a related, separate directive.
- `exports` governs ordinary compile-time-checked access only; it does not by itself permit deep reflection (`setAccessible(true)`) into a package's private members — that additionally requires the separate `opens` directive.
- A package can be part of a module's source tree without ever being exported at all — this is exactly how to structure genuinely private implementation code that should never be part of the module's public contract, and it costs nothing beyond simply omitting the `exports` line for it.
- Multiple `exports` lines are normal and expected for any module with more than one logically distinct public package — there's no limit on how many packages a single module can export, only a requirement that each exported package actually exist within that module's own source tree.
