---
card: java
gi: 696
slug: strong-encapsulation-of-jdk-internals-by-default
title: Strong encapsulation of JDK internals by default
---

## 1. What it is

**Java 16 made strong encapsulation of JDK internals the default** (JEP 396). Since Java 9's module system introduced the concept of strongly encapsulating internal JDK packages (like `sun.misc`, `com.sun.*` internals, and similar non-public implementation packages), reflective access to those internals via `--illegal-access=permit` had remained the *default* behavior through Java 9 through 15 — meaning code using deprecated reflective tricks to reach into JDK internals kept working with just a warning printed once. Java 16 flipped that default to `--illegal-access=deny`: reflective access to internal JDK APIs not explicitly exported now fails by default, and code that needs it must explicitly opt in via `--add-opens` on the command line.

## 2. Why & when

Java 9's module system was designed to let the JDK team evolve internal implementation details freely, without those changes breaking external code — but achieving that goal required actually enforcing encapsulation, not just offering it as an option. For several releases (9 through 15), the JDK team deliberately kept the door open (`--illegal-access=permit` as the default) specifically to give the ecosystem — libraries, frameworks, tools — time to migrate away from reflective access to JDK internals, since a huge amount of existing code (some serialization libraries, some testing/mocking frameworks, some low-level performance tools) had accumulated dependencies on exactly these internals over many years of Java's history. By Java 16, that transition period had run its course, and flipping the default to deny access completed the module system's original enforcement goal. If your application or one of its dependencies fails to start on Java 16+ with an `InaccessibleObjectException`, it means some code (yours or a dependency's) is reflectively reaching into a JDK internal package that is no longer accessible by default — the fix is either upgrading that dependency to a version that no longer needs the internal access, or, as a stopgap, passing `--add-opens module/package=ALL-UNNAMED` explicitly for the specific internal package involved.

## 3. Core concept

```bash
# Java 9–15: illegal reflective access to JDK internals was PERMITTED by default
# (with a one-time warning printed to stderr)
java MyApp

# Java 16 onward: illegal reflective access is DENIED by default
java MyApp   # fails with InaccessibleObjectException if it reflects into JDK internals

# Explicit opt-in still available on Java 16+, naming the exact internal package:
java --add-opens java.base/sun.nio.ch=ALL-UNNAMED MyApp
```

The module boundaries and internal package names haven't changed — what changed is simply which side of the "permit or deny" default illegal reflective access falls on.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java 9 through 15 permitted illegal reflective access to JDK internals by default with a warning; Java 16 denies it by default, requiring explicit --add-opens">
  <rect x="20" y="30" width="280" height="140" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="55" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Java 9 – 15</text>
  <text x="160" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">reflective access to internals</text>
  <text x="160" y="105" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">permitted by default</text>
  <text x="160" y="130" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">(one-time warning printed)</text>

  <rect x="340" y="30" width="280" height="140" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="55" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 16+</text>
  <text x="480" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">reflective access to internals</text>
  <text x="480" y="105" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">denied by default</text>
  <text x="480" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(needs explicit --add-opens)</text>
</svg>

Same module boundaries throughout — only the default enforcement posture changed.

## 5. Runnable example

Scenario: code reflectively reaching into a JDK-internal field — first showing the failure that now occurs by default on Java 16+, then fixing it with an explicit `--add-opens`, then writing a small defensive utility that detects whether the required access is available before attempting the reflective operation, to fail with a clear, actionable message instead of a raw exception.

### Level 1 — Basic

```java
// File: ReflectIntoInternal.java
import java.lang.reflect.Field;

public class ReflectIntoInternal {
    public static void main(String[] args) throws Exception {
        // String's internal "value" field storing its characters/bytes —
        // a deliberately internal implementation detail of java.lang.String.
        Field valueField = String.class.getDeclaredField("value");
        valueField.setAccessible(true); // this is the "illegal reflective access" attempt
        Object value = valueField.get("hello");
        System.out.println("Accessed internal field, array length: "
                + java.lang.reflect.Array.getLength(value));
    }
}
```

**How to run on Java 16+ (fails by default):**
```
java ReflectIntoInternal.java
```

Expected output (fails — `java.lang.String`'s internals are encapsulated even from ordinary application code by default, this is not limited to `java.base`-external modules):
```
Exception in thread "main" java.lang.reflect.InaccessibleObjectException: Unable to make field private final byte[] java.lang.String.value accessible: module java.base does not "opens java.lang" to unnamed module
	at java.base/java.lang.reflect.AccessibleObject.throwInaccessibleObjectException(AccessibleObject.java:391)
	...
```

### Level 2 — Intermediate

```java
// File: ReflectWithOpens.java
import java.lang.reflect.Field;

public class ReflectWithOpens {
    public static void main(String[] args) throws Exception {
        Field valueField = String.class.getDeclaredField("value");
        valueField.setAccessible(true);
        Object value = valueField.get("hello");
        System.out.println("Accessed internal field, array length: "
                + java.lang.reflect.Array.getLength(value));
    }
}
```

**How to run, explicitly opening the specific internal package:**
```
java --add-opens java.base/java.lang=ALL-UNNAMED ReflectWithOpens.java
```

Expected output:
```
Accessed internal field, array length: 5
```

The exact same code that failed in Level 1 now succeeds — `--add-opens java.base/java.lang=ALL-UNNAMED` explicitly grants unnamed-module code (ordinary classpath code, like this single-file program) reflective access to `java.lang`'s internals, opting back in to exactly the behavior Java 9–15 permitted by default.

### Level 3 — Advanced

```java
// File: DefensiveReflection.java
import java.lang.reflect.Field;
import java.lang.reflect.InaccessibleObjectException;

public class DefensiveReflection {
    static Object tryAccessInternalField(Object target, String fieldName) {
        try {
            Field field = target.getClass().getDeclaredField(fieldName);
            field.setAccessible(true);
            return field.get(target);
        } catch (InaccessibleObjectException e) {
            System.out.println("Reflective access denied for " + target.getClass().getName()
                    + "." + fieldName + " — this JVM needs an explicit --add-opens flag.");
            System.out.println("Suggested flag: --add-opens "
                    + target.getClass().getModule().getName() + "/"
                    + target.getClass().getPackageName() + "=ALL-UNNAMED");
            return null;
        } catch (NoSuchFieldException | IllegalAccessException e) {
            System.out.println("Unexpected reflection error: " + e);
            return null;
        }
    }

    public static void main(String[] args) {
        Object result = tryAccessInternalField("hello", "value");
        if (result != null) {
            System.out.println("Successfully accessed internal field.");
        } else {
            System.out.println("Falling back to public String API instead: length=" + "hello".length());
        }
    }
}
```

**How to run without the flag (demonstrates graceful detection and fallback):**
```
java DefensiveReflection.java
```

Expected output:
```
Reflective access denied for java.lang.String.value — this JVM needs an explicit --add-opens flag.
Suggested flag: --add-opens java.base/java.lang=ALL-UNNAMED
Falling back to public String API instead: length=5
```

**How to run with the flag (succeeds instead):**
```
java --add-opens java.base/java.lang=ALL-UNNAMED DefensiveReflection.java
```

Expected output:
```
Successfully accessed internal field.
```

Level 3 writes a small utility that **catches `InaccessibleObjectException` specifically**, prints a diagnostic naming the exact `--add-opens` flag that would fix the problem (computed dynamically from the target's actual module and package), and falls back to safe, public-API behavior instead of letting the exception propagate and crash the program — the pattern any library that occasionally needs deep reflective access, but shouldn't hard-require it, should follow.

## 6. Walkthrough

1. `main` calls `tryAccessInternalField("hello", "value")`, attempting to reflectively read `java.lang.String`'s private internal `value` field (which stores the string's actual character/byte data) from the string instance `"hello"`.
2. Inside `tryAccessInternalField`, `target.getClass().getDeclaredField(fieldName)` locates the field via reflection (this step always succeeds — merely *finding* a private field's metadata is allowed regardless of module encapsulation), and `field.setAccessible(true)` is the actual "illegal reflective access" attempt: it asks the JVM to bypass Java's normal access-control checks (`private`) for this field.
3. On Java 16+ **without** `--add-opens`, `setAccessible(true)` throws `InaccessibleObjectException`, because `java.lang` (part of the `java.base` module) is not "opened" to reflective access from this program's unnamed module by default — the `catch (InaccessibleObjectException e)` block catches exactly this, rather than letting it propagate as an uncaught exception.
4. Inside that `catch` block, the code prints a diagnostic message, then **computes** the exact `--add-opens` flag that would resolve the problem: `target.getClass().getModule().getName()` gives `"java.base"` and `target.getClass().getPackageName()` gives `"java.lang"`, producing the suggestion `--add-opens java.base/java.lang=ALL-UNNAMED` — dynamically derived rather than hard-coded, so this same helper would produce the correct suggestion for *any* internal field it's asked to access, not just this specific one.
5. `tryAccessInternalField` returns `null` in the failure case, and back in `main`, since `result == null`, the program falls back to calling `"hello".length()` — the ordinary, fully public, always-accessible `String` API — demonstrating graceful degradation rather than crashing.
6. When the exact same program is instead run **with** `--add-opens java.base/java.lang=ALL-UNNAMED` on the command line, `setAccessible(true)` succeeds this time (the JVM was explicitly told to permit it), `field.get(target)` successfully retrieves the internal array, `tryAccessInternalField` returns that non-null value, and `main` takes the success branch instead, printing `"Successfully accessed internal field."`

```
tryAccessInternalField(target, fieldName)
        │
getDeclaredField(fieldName) ──► always succeeds (finding metadata is allowed)
        │
field.setAccessible(true)
        │
   --add-opens present? ──yes──► succeeds, field.get(target) returns value
        │no
        ▼
InaccessibleObjectException caught ──► print suggested --add-opens flag, return null
        │
main: result==null? ──yes──► fall back to public API
```

## 7. Gotchas & takeaways

> This default change applies broadly, including to `java.base`'s own packages like `java.lang` — it is **not** limited to obscure `sun.*`/`com.sun.*` internals. Reflective access via `setAccessible(true)` on **any** non-`public`, non-explicitly-opened member across a module boundary is affected, which is why even reflecting into `java.lang.String`'s internals (as shown here) now requires an explicit flag.

- The fix for a dependency that fails on Java 16+ due to this change is, in order of preference: upgrade the dependency to a version that no longer needs the internal access; if no such version exists yet, add the specific `--add-opens` flag the error message names as a stopgap.
- `--add-opens module/package=ALL-UNNAMED` opens the named package to all unnamed-module (plain classpath) code — for finer-grained control between two specific named modules, `--add-opens module/package=targetModule` names a specific target module instead of `ALL-UNNAMED`.
- Catching `InaccessibleObjectException` specifically (rather than a broad `Exception` catch) lets code distinguish "this JVM's module configuration denies the access" from other, unrelated reflection failures like `NoSuchFieldException`.
- This change (Java 16) followed years of advance warning — Java 9 introduced the encapsulation model, and the `--illegal-access` default stayed permissive through Java 15 specifically to give the ecosystem time to adapt before this stricter default arrived.
- Testing your application (and its full dependency tree) against a Java 16+ JVM early is the best way to discover any lingering illegal-reflective-access dependencies before they surface as a production startup failure.
