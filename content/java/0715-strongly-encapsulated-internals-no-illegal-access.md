---
card: java
gi: 715
slug: strongly-encapsulated-internals-no-illegal-access
title: Strongly encapsulated internals (no illegal-access)
---

## 1. What it is

**Java 17** (JEP 403) took JDK-internals encapsulation one step further than [Java 16's default flip](0696-strong-encapsulation-of-jdk-internals-by-default.md): it **removed the `--illegal-access` command-line option entirely**. Java 16 had changed the *default* from "permit" to "deny," but still let you restore the old permissive behavior with `--illegal-access=permit` as an escape hatch. Java 17 removes that escape hatch: the `--illegal-access` flag no longer exists at all, and reflective access to unexported JDK internal packages is unconditionally denied unless explicitly opened via `--add-opens` (or `--add-exports` for exports without deep reflection). Only `java.base`'s small set of "critical" internal APIs still permitted for reflective access as of Java 16 (kept as a deliberate, temporary carve-out for a few especially entrenched libraries) remain reachable without an explicit module flag in Java 17.

## 2. Why & when

Java 16's default change was intentionally still escapable, specifically to avoid abruptly breaking every application relying on illegal reflective access all at once — `--illegal-access=permit` served as a safety valve while the ecosystem finished migrating. By Java 17, the JDK team judged that transition sufficiently complete: keeping the flag around indefinitely would have meant the module system's encapsulation goal was still, in effect, optional, which undermined the point of enforcing it in the first place. Removing `--illegal-access` outright means there is now exactly one way to access a JDK-internal package reflectively across a module boundary: explicit, per-package `--add-opens module/package=target-module` (or `ALL-UNNAMED` for classpath code), decided deliberately by whoever configures the application's launch, rather than a single blanket flag anyone could reach for. This matters immediately if you upgrade an application (or a dependency using reflection against JDK internals) straight from Java 15 or earlier to Java 17 — any lingering reliance on `--illegal-access=permit` as a stopgap must be replaced with specific `--add-opens` entries, or the dependency itself must be upgraded to one that no longer needs the access at all.

## 3. Core concept

```bash
# Java 16: --illegal-access still existed as an (already-deprecated) escape hatch
java --illegal-access=permit MyApp.jar        # worked in Java 16, with a warning

# Java 17: the flag is gone entirely
java --illegal-access=permit MyApp.jar        # error: unrecognized option

# The only supported way to reach a specific internal package in Java 17+:
java --add-opens java.base/sun.nio.ch=ALL-UNNAMED MyApp.jar
```

There is no longer a single switch to broadly restore illegal reflective access — only precise, per-package `--add-opens` entries remain.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java 16 denied illegal reflective access by default but allowed restoring the old behavior with --illegal-access=permit; Java 17 removes that flag entirely, leaving only precise per-package --add-opens as the way to reach an internal API">
  <rect x="20" y="20" width="280" height="170" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Java 16</text>
  <text x="160" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">default: illegal access denied</text>
  <text x="160" y="95" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">--illegal-access=permit still works</text>
  <text x="160" y="120" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">(broad escape hatch, one flag)</text>
  <text x="160" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">transition safety valve</text>

  <rect x="340" y="20" width="280" height="170" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 17+</text>
  <text x="480" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">--illegal-access flag: removed</text>
  <text x="480" y="100" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">--add-opens pkg=target only</text>
  <text x="480" y="125" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">(precise, per-package, deliberate)</text>
  <text x="480" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">encapsulation enforced, no broad escape hatch</text>
</svg>

The safety-valve flag disappears; only targeted, per-package `--add-opens` remains as the supported way to reach internals.

## 5. Runnable example

Scenario: a small tool that reflectively inspects a JDK-internal field — first showing it fail with `InaccessibleObjectException` when run with no special flags (the Java 17+ default), then succeeding once the specific package is opened via `--add-opens`, then a version that detects at runtime whether the required access has been granted and reports a clear, actionable message either way, the kind of defensive check a library relying on such access might add for its users.

### Level 1 — Basic

```java
// File: ReflectInternalBasic.java
import java.lang.reflect.Field;

public class ReflectInternalBasic {
    public static void main(String[] args) throws Exception {
        // sun.nio.ch is a java.base-internal package not open to unnamed modules by default.
        Class<?> clazz = Class.forName("sun.nio.ch.NativeThread");
        Field[] fields = clazz.getDeclaredFields();
        System.out.println("Declared field count on " + clazz.getName() + ": " + fields.length);
        if (fields.length > 0) {
            fields[0].setAccessible(true); // this line throws if the package isn't opened
            System.out.println("First field: " + fields[0].getName());
        }
    }
}
```

**How to run (no special flags — Java 17+ default):**
```
java ReflectInternalBasic.java
```

Expected output (the package is unopened by default in Java 17, so `setAccessible(true)` fails):
```
Declared field count on sun.nio.ch.NativeThread: 2
Exception in thread "main" java.lang.reflect.InaccessibleObjectException: Unable to make field ... accessible: module java.base does not "opens sun.nio.ch" to unnamed module ...
```

**How to run (explicitly opening the package):**
```
java --add-opens java.base/sun.nio.ch=ALL-UNNAMED ReflectInternalBasic.java
```

Expected output:
```
Declared field count on sun.nio.ch.NativeThread: 2
First field: id
```

### Level 2 — Intermediate

```java
// File: GracefulReflectionCheck.java
import java.lang.reflect.Field;
import java.lang.reflect.InaccessibleObjectException;

public class GracefulReflectionCheck {
    static boolean tryOpenInternalField() {
        try {
            Class<?> clazz = Class.forName("sun.nio.ch.NativeThread");
            Field field = clazz.getDeclaredFields()[0];
            field.setAccessible(true);
            return true;
        } catch (InaccessibleObjectException e) {
            return false;
        } catch (ReflectiveOperationException e) {
            return false;
        }
    }

    public static void main(String[] args) {
        boolean granted = tryOpenInternalField();
        System.out.println("Reflective access to sun.nio.ch internals granted: " + granted);
        if (!granted) {
            System.out.println("Add: --add-opens java.base/sun.nio.ch=ALL-UNNAMED to your launch command.");
        }
    }
}
```

**How to run (no flags):**
```
java GracefulReflectionCheck.java
```

Expected output:
```
Reflective access to sun.nio.ch internals granted: false
Add: --add-opens java.base/sun.nio.ch=ALL-UNNAMED to your launch command.
```

**How to run (with the required flag):**
```
java --add-opens java.base/sun.nio.ch=ALL-UNNAMED GracefulReflectionCheck.java
```

Expected output:
```
Reflective access to sun.nio.ch internals granted: true
```

### Level 3 — Advanced

```java
// File: DiagnosticReport.java
import java.lang.reflect.Field;
import java.lang.reflect.InaccessibleObjectException;

public class DiagnosticReport {
    record AccessCheck(String packageName, boolean accessible, String hint) {}

    static AccessCheck check(String className, String packageName) {
        try {
            Class<?> clazz = Class.forName(className);
            Field field = clazz.getDeclaredFields()[0];
            field.setAccessible(true);
            return new AccessCheck(packageName, true, "already accessible");
        } catch (InaccessibleObjectException e) {
            return new AccessCheck(packageName, false,
                    "--add-opens java.base/" + packageName + "=ALL-UNNAMED");
        } catch (ReflectiveOperationException | ArrayIndexOutOfBoundsException e) {
            return new AccessCheck(packageName, false, "unavailable: " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        String[][] targets = {
                { "sun.nio.ch.NativeThread", "sun.nio.ch" },
                { "sun.misc.Unsafe", "sun.misc" }
        };

        System.out.println("=== JDK-internal reflective access report (Java 17+) ===");
        for (String[] target : targets) {
            AccessCheck result = check(target[0], target[1]);
            System.out.printf("%-15s accessible=%-6s hint=%s%n", result.packageName(), result.accessible(), result.hint());
        }
    }
}
```

**How to run (no flags):**
```
java DiagnosticReport.java
```

Expected output shape (each internal package independently reports whether it's reachable and, if not, exactly which flag would open it):
```
=== JDK-internal reflective access report (Java 17+) ===
sun.nio.ch      accessible=false hint=--add-opens java.base/sun.nio.ch=ALL-UNNAMED
sun.misc        accessible=false hint=--add-opens java.base/sun.misc=ALL-UNNAMED
```

**How to run (opening both packages):**
```
java --add-opens java.base/sun.nio.ch=ALL-UNNAMED --add-opens java.base/sun.misc=ALL-UNNAMED DiagnosticReport.java
```

Expected output:
```
=== JDK-internal reflective access report (Java 17+) ===
sun.nio.ch      accessible=true hint=already accessible
sun.misc        accessible=true hint=already accessible
```

## 6. Walkthrough

1. `DiagnosticReport.main` iterates over a small table of internal-class-and-package pairs, calling `check(...)` for each — this pattern is exactly what a library or diagnostic tool would do at startup to determine, ahead of time, whether it has the reflective access it needs, rather than discovering the problem only when a deeper code path fails unexpectedly at runtime.
2. Inside `check`, `Class.forName(className)` loads the internal class successfully (loading a class doesn't require it to be *opened* — only reflectively accessing its non-public members does), then `field.setAccessible(true)` is the actual operation that triggers Java's module-access enforcement.
3. If the package is not open to the calling module (the default state for essentially every `java.base` internal package on Java 17+, since `--illegal-access=permit` no longer exists to override this broadly), `setAccessible(true)` throws `InaccessibleObjectException`, which `check` catches and turns into a clear, actionable `hint` string naming the exact `--add-opens` flag that would fix it.
4. Running the program with no flags demonstrates the Java 17+ default: every internal package check reports `accessible=false`, each with its own precise remediation hint — there is no single blanket flag left to try, only the specific `--add-opens` for each package actually needed.
5. Re-running with both `--add-opens` flags supplied on the command line flips both checks to `accessible=true`, demonstrating that access is granted (or not) **per package**, decided explicitly at launch time by whoever configures the JVM's command line — a deliberate, auditable decision rather than an implicit, broadly-permissive default.

```
Class.forName(internalClass)     <- loading the class itself always succeeds
        │
field.setAccessible(true)        <- module system enforcement happens here
        │
   package opened via --add-opens?
     yes -> succeeds, field usable reflectively
     no  -> InaccessibleObjectException (no blanket --illegal-access escape hatch remains)
```

## 7. Gotchas & takeaways

> Removing `--illegal-access` does **not** mean reflective access to JDK internals became impossible — it means the *only* remaining way to grant it is precise, per-package `--add-opens` (or `--add-exports`) entries, decided deliberately rather than through one broadly permissive flag. Applications and libraries that genuinely need specific internal access still can, by naming exactly which package they need opened.
- A small set of especially entrenched `java.base` internal APIs (carried over from the Java 16 transition) may remain reflectively accessible without any flag at all in Java 17 — but this is a narrow, explicitly-tracked exception list, not a general escape hatch, and code shouldn't rely on it persisting in future releases.
- If an application (or one of its dependencies) throws `InaccessibleObjectException` after upgrading straight from Java 15 or earlier to Java 17, check first whether the dependency has a newer version that no longer needs the internal access at all — adding `--add-opens` is a reasonable stopgap, but it's tying your launch configuration to an internal implementation detail that could change or disappear in a future JDK release regardless.
- `--add-opens` is more surgical than the old `--illegal-access=permit` by design: it must name the specific module and package (e.g., `java.base/sun.nio.ch`), which makes exactly what access an application requires visible and auditable in its launch configuration, rather than hidden behind one catch-all flag.
- Loading an internal class via `Class.forName(...)` never itself requires module access — only reflectively *invoking* or *setting accessible* on its non-public members does; this distinction is why `check`'s `Class.forName` call in this tutorial's example always succeeds even when the subsequent `setAccessible` call fails.
- See [Strong encapsulation of JDK internals by default](0696-strong-encapsulation-of-jdk-internals-by-default.md) (Java 16) for the earlier step in this same multi-release progression — Java 16 changed the default; Java 17 removed the last broad way to override it.
