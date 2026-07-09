---
card: java
gi: 574
slug: exports-to-qualified
title: exports … to (qualified)
---

## 1. What it is

A **qualified export** (`exports package to module1, module2, ...`) restricts a package's visibility to only the specifically named module(s), rather than every module that requires the exporting module. It's a narrower version of plain `exports`: instead of "anyone who depends on me can use this," it's "only these specific, named modules can use this — everyone else, no."

## 2. Why & when

Plain `exports` is all-or-nothing: once a package is exported, *every* module that requires yours can use it, forever, with no way to limit that to a trusted subset. Sometimes that's too broad — a plugin host module might need to expose a service-provider interface package specifically to its own plugin implementation modules, without making that same package part of the general public API every ordinary consumer sees; or two closely related modules built by the same team might need to share a package that's genuinely an implementation detail from the outside world's perspective, but a legitimate, deliberate integration point between those two specific modules. Qualified exports let you thread that needle: keep a package fully hidden from the wider world while still sharing it, explicitly and by name, with one or a few trusted modules.

## 3. Core concept

```java
module plugin.host {
    exports com.pluginhost.api;                          // public to everyone who requires plugin.host
    exports com.pluginhost.spi to plugin.impl.builtin;    // visible ONLY to plugin.impl.builtin
}
```

```java
module plugin.impl.builtin {
    requires plugin.host;
    // can use com.pluginhost.spi — named explicitly in plugin.host's qualified export
}

module some.other.module {
    requires plugin.host;
    // CANNOT use com.pluginhost.spi — not named in the qualified export, even though it requires plugin.host
}
```

Both `some.other.module` and `plugin.impl.builtin` require `plugin.host` identically, but only the module named in the `to` clause can see the qualified package — the other still sees only the unconditionally exported `com.pluginhost.api`.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A qualified export is visible only to the specific module named in the to clause, not to every requiring module">
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="50" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">module plugin.host</text>

  <rect x="240" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="50" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">plugin.impl.builtin</text>

  <rect x="440" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="530" y="50" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">some.other.module</text>

  <line x1="200" y1="45" x2="240" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#q1)"/>
  <text x="220" y="35" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">requires</text>
  <line x1="420" y1="45" x2="440" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#q2)"/>
  <text x="430" y="35" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">requires</text>

  <text x="20" y="100" fill="#8b949e" font-size="10" font-family="sans-serif">exports com.pluginhost.spi to plugin.impl.builtin;</text>
  <line x1="110" y1="110" x2="330" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#q3)"/>
  <text x="220" y="125" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">CAN see com.pluginhost.spi (named explicitly)</text>

  <line x1="110" y1="150" x2="530" y2="150" stroke="#f85149" stroke-width="2" stroke-dasharray="4,3"/>
  <text x="320" y="165" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">CANNOT see com.pluginhost.spi (not named — compile error)</text>

  <defs>
    <marker id="q1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="q2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="q3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Requiring the exporting module is necessary but not sufficient — the consumer must also be named in the `to` clause to see a qualified package.

## 5. Runnable example

Scenario: a small "reporting" module exposing a public API to everyone, plus an internal formatting-hooks package meant only for one specific, trusted extension module — starting with an unqualified export (too permissive), then restricting it with a qualified export to a single named module, then verifying a second, uninvited module is genuinely denied while the named one still works.

### Level 1 — Basic

```java
// File: reporting/module-info.java — plain export, visible to EVERY consumer
module reporting {
    exports com.reporting.api;
    exports com.reporting.hooks; // meant only for one trusted extension, but not restricted yet
}
```

```java
// File: reporting/com/reporting/api/Report.java
package com.reporting.api;

public class Report {
    public String render(String title) {
        return "=== " + title + " ===";
    }
}
```

```java
// File: reporting/com/reporting/hooks/FormatHook.java
package com.reporting.hooks;

public interface FormatHook {
    String beforeRender(String title);
}
```

```java
// File: uninvited/module-info.java — NOT the intended consumer of hooks, but currently CAN see it
module uninvited {
    requires reporting;
}
```

```java
// File: uninvited/com/uninvited/Snoop.java
package com.uninvited;
import com.reporting.hooks.FormatHook; // works, but shouldn't — the whole point of this level

public class Snoop implements FormatHook {
    public String beforeRender(String title) { return "[snooped] " + title; }
}
```

**How to run:** `javac -d out --module-source-path . $(find reporting uninvited -name "*.java")`

Expected output: compiles cleanly — which is exactly the problem this level demonstrates.

`com.reporting.hooks` was meant as an internal extension point for one specific, trusted module, but plain `exports com.reporting.hooks;` makes it visible to **any** module that requires `reporting` — including `uninvited`, which was never supposed to have access to it. Nothing in the module system stops this yet, because the export isn't restricted to anyone in particular.

### Level 2 — Intermediate

```java
// File: reporting/module-info.java — restrict hooks to one named module
module reporting {
    exports com.reporting.api;
    exports com.reporting.hooks to trusted.extension; // ONLY trusted.extension can see this now
}
```

```java
// File: trusted.extension/module-info.java
module trusted.extension {
    requires reporting;
}
```

```java
// File: trusted.extension/com/trustedext/BoldHook.java
package com.trustedext;
import com.reporting.hooks.FormatHook;

public class BoldHook implements FormatHook {
    public String beforeRender(String title) {
        return "**" + title + "**";
    }
}
```

**How to run:** `javac -d out --module-source-path . $(find reporting trusted.extension -name "*.java")`

Expected output: compiles cleanly.

The real-world concern this adds: `com.reporting.hooks` is now exported **only** `to trusted.extension` — the named module in the `to` clause is granted exactly the same access a plain `exports` would give, while every other module (like `uninvited` from Level 1) is now denied, verified next.

### Level 3 — Advanced

```java
// File: uninvited/com/uninvited/Snoop.java — same file as Level 1, unchanged
package com.uninvited;
import com.reporting.hooks.FormatHook; // this will now FAIL to compile

public class Snoop implements FormatHook {
    public String beforeRender(String title) { return "[snooped] " + title; }
}
```

**How to run:** compile `reporting` (with the qualified export from Level 2), `trusted.extension`, and `uninvited` all together:
```
javac -d out --module-source-path . $(find reporting trusted.extension uninvited -name "*.java")
```

Expected output (compilation fails — this is the intended demonstration):
```
uninvited/com/uninvited/Snoop.java:2: error: package com.reporting.hooks is not visible
import com.reporting.hooks.FormatHook;
                     ^
  (package com.reporting.hooks is declared in module reporting, which does not export it to module uninvited)
```

This handles the production-flavoured payoff: `trusted.extension` compiles successfully (it's named in the `to` clause), while `uninvited` — with the exact same `requires reporting;` declaration it had in Level 1 — now fails to compile that same import, purely because it wasn't named. The error message even confirms the distinction explicitly: `"does not export it to module uninvited"`, naming exactly which module was excluded.

## 6. Walkthrough

Execution starts with the compilation command in Level 3, which compiles all three modules together: `reporting` (with the qualified `exports com.reporting.hooks to trusted.extension;`), `trusted.extension`, and `uninvited`.

`javac` reads `reporting/module-info.java` first, recording two facts: `com.reporting.api` is exported unconditionally, and `com.reporting.hooks` is exported, but *only* to the module named `trusted.extension` — any other module's `requires reporting` grants access to `com.reporting.api` alone.

```
Compiling trusted.extension/com/trustedext/BoldHook.java:
  import com.reporting.hooks.FormatHook
    -> trusted.extension requires reporting               -> OK, module found
    -> com.reporting.hooks exported "to trusted.extension" -> trusted.extension IS named -> OK

Compiling uninvited/com/uninvited/Snoop.java:
  import com.reporting.hooks.FormatHook
    -> uninvited requires reporting                        -> OK, module found
    -> com.reporting.hooks exported "to trusted.extension"  -> uninvited is NOT named -> ERROR
```

When `javac` compiles `BoldHook.java` (inside `trusted.extension`), it checks the qualified export's target list, finds `trusted.extension` present, and allows the import — `BoldHook` implements `FormatHook` normally, no different from an unqualified export as far as this specific, named consumer is concerned.

When `javac` reaches `Snoop.java` (inside `uninvited`), it performs the identical check: `uninvited` does have a `requires reporting` edge (so `reporting` the module itself is resolvable), but when checking the *qualified* export's target list for `com.reporting.hooks`, `uninvited` is not among the named modules. The compiler reports the package as "not visible," with the message explicitly stating "does not export it to module uninvited" — naming the excluded module directly, which is a deliberately more specific diagnostic than the generic "does not export it" message a plain (non-qualified) missing export would produce, helping a developer immediately understand this isn't a missing `exports` line entirely, but a qualified one that simply doesn't include their module.

Compilation halts at this error; no `.class` files are produced for `uninvited` in this combined build. If `uninvited` were compiled on its own, *without* attempting the `FormatHook` import (i.e., with the offending line removed), it would still succeed independently — the qualified export only blocks the specific restricted package, not `uninvited`'s ability to depend on `reporting` at all (it can still use `com.reporting.api` freely, since that remains unconditionally exported).

## 7. Gotchas & takeaways

> A qualified export is a **compile-time-enforced** allowlist, not merely documentation of "who this is intended for" — unlike a code comment saying "internal, do not use outside module X," `exports ... to` makes any unauthorized import a hard compiler error, for every module not explicitly named, forever, until the `module-info.java` itself is changed. This is meaningfully stronger than any classpath-era convention for restricting access to a trusted set of consumers.

- The `to` clause can name multiple modules, comma-separated: `exports com.pluginhost.spi to plugin.impl.builtin, plugin.impl.legacy;` — useful for sharing an internal package with a small, known set of trusted modules without making it universally public.
- A single package can only have **one** `exports` directive for it in a given `module-info.java` — you cannot both unconditionally export a package and separately qualify-export the same package; choose one or the other for that package.
- Qualified exports are commonly used by the JDK itself — several `jdk.internal.*` packages are exported by internal JDK modules to a small, specific list of other JDK modules that legitimately need them, while remaining completely inaccessible to any application code, no matter what that application requires.
- Being named in a `to` clause requires knowing the exporting module's exact module name up front — if the consuming module is renamed later, the qualified export in the producing module must be updated to match, or the consumer silently loses access at the next compile.
- Qualified exports do not affect `opens` at all — a package can be qualified-exported to one module for compile-time use and separately, independently `opens`-ed (unconditionally or with its own `to` clause) for reflective access, since `exports` and `opens` are governed by entirely separate directives.
