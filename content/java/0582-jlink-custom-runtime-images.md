---
card: java
gi: 582
slug: jlink-custom-runtime-images
title: jlink custom runtime images
---

## 1. What it is

`jlink` is a JDK-bundled tool that builds a **custom, minimal Java runtime image** — a self-contained directory with its own `bin/java` launcher — containing only the specific JDK modules an application actually needs, instead of shipping the entire JDK. Because the JDK itself has been modularized since Java 9 (`java.base`, `java.sql`, `java.desktop`, and so on, each a real module), `jlink` can compute exactly which platform modules an application's own module graph transitively requires, and link only those into a smaller, purpose-built runtime.

## 2. Why & when

A full JDK install is large (well over 300 MB) because it includes every platform module — GUI toolkits, XML processing, scripting engines, database connectivity, and much more — regardless of whether a given application uses any of it. For a small microservice that only needs `java.base` and maybe `java.sql`, shipping the entire JDK inside a container image wastes disk space, increases image pull times, and expands the attack surface with unused code. `jlink` fixes this by producing a runtime image containing *only* the modules actually needed, computed automatically from the application's own `module-info.java` dependency graph — commonly used to build small Docker images, or to ship a self-contained application that doesn't require the end user to have any JDK installed at all (bundling the custom runtime alongside the application itself).

## 3. Core concept

```
jlink --module-path out:$JAVA_HOME/jmods \
      --add-modules app \
      --output myapp-runtime \
      --strip-debug --no-header-files --no-man-pages
```

`--module-path` must include both the application's own compiled modules and the JDK's own module definitions (`$JAVA_HOME/jmods`, a directory of `.jmod` files shipped with a full JDK install specifically for `jlink` to consume). `--add-modules app` names the root module to start resolution from — `jlink` then transitively includes every module `app` (and its dependencies, and their dependencies) actually `requires`. `--output myapp-runtime` is the directory the resulting minimal runtime is written to; running `myapp-runtime/bin/java -m app/com.myapp.Main` launches the application using only that image's included modules.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jlink computes the transitive module closure needed by an application and links only those modules into a minimal runtime image">
  <text x="20" y="25" fill="#8b949e" font-size="11" font-family="sans-serif">Full JDK: dozens of modules, most unused by any given app</text>
  <rect x="20" y="35" width="600" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="58" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">java.base, java.sql, java.desktop, java.xml, jdk.crypto.*, ... (everything)</text>

  <text x="20" y="100" fill="#8b949e" font-size="11" font-family="sans-serif">jlink --add-modules app -&gt; transitive closure of what "app" actually requires</text>
  <rect x="20" y="110" width="280" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="135" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">java.base + java.sql only</text>
  <text x="320" y="135" fill="#8b949e" font-size="10" font-family="sans-serif">-&gt; myapp-runtime/ (small, self-contained)</text>
</svg>

Only the modules actually reachable from the application's own `requires` graph make it into the final image.

## 5. Runnable example

Scenario: a tiny "greeting" application whose module graph deliberately only needs `java.base` — starting with building and inspecting a minimal `jlink` image for it, then adding a real dependency on `java.sql` and observing the resulting image grow to include it, then measuring and comparing the custom image's size against a full JDK install to see the space savings concretely.

### Level 1 — Basic

```java
// File: app/module-info.java
module app {
}
```

```java
// File: app/com/myapp/Main.java
package com.myapp;

public class Main {
    public static void main(String[] args) {
        System.out.println("Hello from a custom runtime image!");
    }
}
```

**How to run:**
```
javac -d out --module-source-path . $(find app -name "*.java")
jlink --module-path out:$JAVA_HOME/jmods --add-modules app --output myapp-runtime --strip-debug --no-header-files --no-man-pages
myapp-runtime/bin/java -m app/com.myapp.Main
myapp-runtime/bin/java --list-modules
```

Expected output:
```
Hello from a custom runtime image!
app
java.base@21.0.4
```

`jlink` builds `myapp-runtime`, a complete, standalone Java runtime — `myapp-runtime/bin/java` is a real, working `java` launcher, just one that only knows about the modules explicitly linked in. `--list-modules` confirms exactly what got included: `app` itself, and `java.base` — the one JDK platform module every application implicitly needs, and, in this case, the *only* one, since `app`'s `module-info.java` declares no other dependencies at all.

### Level 2 — Intermediate

```java
// File: app/module-info.java — now requires java.sql
module app {
    requires java.sql;
}
```

```java
// File: app/com/myapp/Main.java
package com.myapp;
import java.sql.Timestamp;

public class Main {
    public static void main(String[] args) {
        Timestamp now = new Timestamp(0);
        System.out.println("Hello from a custom runtime image! Timestamp: " + now);
    }
}
```

**How to run:**
```
javac -d out --module-source-path . $(find app -name "*.java")
jlink --module-path out:$JAVA_HOME/jmods --add-modules app --output myapp-runtime2 --strip-debug --no-header-files --no-man-pages
myapp-runtime2/bin/java -m app/com.myapp.Main
myapp-runtime2/bin/java --list-modules
```

Expected output (exact timestamp text may vary by machine timezone):
```
Hello from a custom runtime image! Timestamp: 1970-01-01 00:00:00.0
app
java.base@21.0.4
java.logging@21.0.4
java.sql@21.0.4
java.transaction.xa@21.0.4
java.xml@21.0.4
```

The real-world concern this adds: adding a genuine dependency (`requires java.sql;`) automatically **grows** the resulting image with exactly the modules needed to support it — `java.sql` itself, plus its own transitive dependencies (`java.xml`, `java.logging`, `java.transaction.xa`, which `java.sql` in turn requires) — all computed automatically by `jlink` from the module graph, with no manual list of "which JDK modules do I need" to maintain by hand.

### Level 3 — Advanced

```java
// File: app/module-info.java — UNCHANGED from Level 1 (java.base only, for the smallest possible comparison)
module app {
}
```

```java
// File: app/com/myapp/Main.java — UNCHANGED from Level 1
package com.myapp;

public class Main {
    public static void main(String[] args) {
        System.out.println("Hello from a custom runtime image!");
    }
}
```

**How to run:** build the minimal image, then compare its on-disk size against the full JDK install it was built from:
```
javac -d out --module-source-path . $(find app -name "*.java")
jlink --module-path out:$JAVA_HOME/jmods --add-modules app --output myapp-runtime3 --strip-debug --no-header-files --no-man-pages --compress zip-6
du -sh "$JAVA_HOME"
du -sh myapp-runtime3
```

Expected output (exact sizes vary by JDK version and platform, but the custom image is dramatically smaller — commonly a 5-10x reduction):
```
308M	/path/to/full/jdk
 31M	myapp-runtime3
```

This handles the production-flavoured payoff that motivates `jlink` in the first place: **quantifying the actual size reduction**. `--compress zip-6` additionally compresses the module content inside the image (trading a small amount of startup decompression cost for further size reduction), and `--strip-debug`/`--no-header-files`/`--no-man-pages` (used since Level 1) remove debugging symbols, C header files, and documentation that a deployed application never needs — none of this is required for the image to function correctly, all of it exists purely to minimize footprint for exactly this kind of deployment scenario, most commonly a container image.

## 6. Walkthrough

Execution starts with the `jlink` command in Level 3, invoked against `app` (whose `module-info.java` declares no dependencies beyond the always-implicit `java.base`).

`--module-path out:$JAVA_HOME/jmods` tells `jlink` where to look for module definitions: `out` (the freshly compiled `app` module) and `$JAVA_HOME/jmods` (the JDK's own `.jmod` files — a packaging format specifically for `jlink` consumption, distinct from the regular `.jar`/module-path form used at compile and run time, and only present in a *full* JDK install, not a JRE-only or already-jlinked minimal install).

`--add-modules app` roots the resolution at `app`. `jlink` then computes the transitive closure: `app` itself requires nothing beyond the implicit `java.base`, so the closure is just `{app, java.base}` — no `java.sql`, no `java.desktop`, none of the dozens of other platform modules a full JDK ships, because nothing in `app`'s module graph ever requires them.

```
jlink's module resolution, for this specific app:

app (root)  -->  requires java.base (implicit)  -->  DONE, closure = {app, java.base}

(Contrast with Level 2, where app requires java.sql:
 app --> java.sql --> java.xml, java.logging, java.transaction.xa --> DONE, larger closure)
```

`--output myapp-runtime3` writes the resulting minimal runtime image to that directory — a complete copy of just the resolved modules' compiled classes (further reduced by `--strip-debug`, which removes debugging line-number and variable-name tables the JIT and a deployed application don't need), assembled into the same internal format (`lib/modules`, a single optimized file) a normal JDK install uses, plus a working `bin/java` launcher pointed at exactly that module set.

`du -sh "$JAVA_HOME"` measures the size of the full, original JDK install this image was linked from — commonly several hundred megabytes, since it contains every platform module regardless of use. `du -sh myapp-runtime3` measures the resulting custom image — dramatically smaller, since it contains only `java.base` (plus `app` itself, negligible in size by comparison) rather than the JDK's entire module set, further reduced by the debug-symbol stripping and zip compression flags.

The practical payoff: `myapp-runtime3/bin/java -m app/com.myapp.Main` runs the exact same application, correctly, using this much smaller runtime — the kind of image genuinely worth building into a container, since every megabyte not included is a megabyte that never needs to be pulled, stored, or scanned for vulnerabilities in a deployed environment.

## 7. Gotchas & takeaways

> A `jlink` image only includes what the **module graph** declares — any dependency reached only through reflection, dynamic class loading, or a service loaded via `ServiceLoader` (covered in the `uses`/`provides` topics) that `jlink` can't statically see from `requires` declarations alone may be silently missing from the resulting image, causing a runtime failure that never shows up at build time. Use `--bind-services` (to include all modules that provide services any included module `uses`) and thoroughly test the actual linked image, not just the pre-jlink development build, before shipping it.

- `jlink` requires the application (and every dependency in its graph) to actually be fully modularized, with real `module-info.java` files — plain classpath JARs or even automatic modules generally cannot be `jlink`-ed directly into a minimal image the same way, since `jlink` needs a complete, closed module graph to compute the correct closure.
- `--strip-debug` removes debugging information useful for attaching a debugger to a deployed application — a reasonable trade-off for production images, but worth reconsidering for images specifically built for local development or debugging purposes.
- The resulting custom runtime image is tied to the specific JDK version and platform (OS/architecture) it was linked on — it is not a portable, cross-platform artifact; building images for multiple target platforms requires running `jlink` separately on (or targeting) each platform.
- `jlink` images can be further combined with `jpackage` (a related, separate JDK tool) to produce a fully native, installable application package (`.exe`, `.dmg`, `.deb`) that bundles the custom runtime image alongside the application itself, requiring zero separate Java installation on the end user's machine at all.
- Because a `jlink` image only contains the modules actually resolved into it, it provides a meaningful **security** benefit beyond just size: modules like `java.desktop` or `java.scripting`, if never included, simply cannot be exploited or abused by any vulnerability discovered in them later, since their code isn't present in the deployed artifact at all.
