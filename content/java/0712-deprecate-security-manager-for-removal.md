---
card: java
gi: 712
slug: deprecate-security-manager-for-removal
title: Deprecate Security Manager for removal
---

## 1. What it is

**Java 17** (JEP 411) marked `java.lang.SecurityManager` and the related permission-checking APIs (`java.security.Permission` and its subclasses, `AccessController`, `Policy`) as **deprecated for removal** — the strongest level of deprecation the JDK uses, signaling that the API not only shouldn't be used in new code, but is a real candidate for a future JDK release removing it entirely. In Java 17, `SecurityManager` still works exactly as before: you can still call `System.setSecurityManager(...)`, still write custom `checkPermission` logic, and still have it enforced — but compiling code that uses it now produces a deprecation warning, and the JEP formally announced the JDK team's intent to remove the mechanism in a future release.

## 2. Why & when

`SecurityManager` dates back to Java 1.0, designed for a very specific 1990s use case: safely running untrusted applets and code downloaded over the network inside a sandboxed browser, restricting what that code could do (file access, network access, and so on) via a single, globally-installed policy checked on nearly every sensitive operation. Applets and that entire browser-sandboxing use case had been effectively dead for years by Java 17 — browsers had already removed applet plugin support, and the surviving audience for `SecurityManager` had shifted to unrelated purposes it was never well-suited for, like ad hoc, per-thread capability restriction inside a single trusted application. Meanwhile, the mechanism itself carried a real ongoing cost: because a security check needed to be woven through nearly every sensitive JDK API method, it constrained internal JDK implementation choices and added overhead, for a feature very few applications still genuinely relied on for its original purpose. JEP 411 started the formal, multi-release deprecation-then-removal process (the mechanism was ultimately removed outright in a much later JDK release), giving the ecosystem years of advance notice to migrate away from it toward more modern isolation mechanisms — containers, separate OS-level processes, or the Java Platform Module System's encapsulation — appropriate to how applications are actually deployed and sandboxed today.

## 3. Core concept

```java
// Java 17 — still works, but every one of these calls now triggers a
// "deprecated for removal" compiler warning:
SecurityManager sm = new SecurityManager() {
    @Override
    public void checkExit(int status) {
        throw new SecurityException("System.exit() is not allowed here");
    }
};
System.setSecurityManager(sm);

System.exit(1); // throws SecurityException, caught by the installed checkExit override
```

```bash
# See the deprecation warnings explicitly at compile time:
javac -Xlint:removal SecurityDemo.java
```

Functionally unchanged from earlier releases — the difference in Java 17 is the loud, explicit signal that this API's days are numbered.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SecurityManager still functions in Java 17 exactly as before, but is now flagged deprecated for removal, with the JDK team recommending migration to container or module-based isolation instead">
  <rect x="20" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="160" y="42" fill="#f0883e" font-size="12" text-anchor="middle" font-family="sans-serif">SecurityManager (Java 17)</text>
  <text x="160" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">still fully functional</text>
  <text x="160" y="100" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">deprecated for removal (JEP 411)</text>
  <text x="160" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">javac -Xlint:removal shows warnings</text>
  <text x="160" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">removed outright in a later JDK release</text>

  <rect x="340" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Recommended alternatives</text>
  <text x="480" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OS-level containers / sandboxes</text>
  <text x="480" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">separate, isolated processes</text>
  <text x="480" y="125" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JPMS module encapsulation</text>
  <text x="480" y="150" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">isolation matching modern deployment</text>
</svg>

Nothing behaves differently yet in Java 17 — the change is the formal, advance warning of eventual removal.

## 5. Runnable example

Scenario: a small program that restricts a specific dangerous operation — first installing a basic `SecurityManager` that blocks `System.exit()`, then extending it to block a broader category of operations (writing to a specific file path) while allowing others, then a version that demonstrates the compiler's `-Xlint:removal` warning directly, to show concretely what "deprecated for removal" looks like from a developer's seat.

### Level 1 — Basic

```java
// File: BlockExitBasic.java
@SuppressWarnings("removal") // acknowledging the JEP 411 deprecation explicitly
public class BlockExitBasic {
    public static void main(String[] args) {
        SecurityManager sm = new SecurityManager() {
            @Override
            public void checkExit(int status) {
                throw new SecurityException("System.exit(" + status + ") is not allowed here");
            }
        };
        System.setSecurityManager(sm);

        try {
            System.exit(1);
        } catch (SecurityException e) {
            System.out.println("Blocked: " + e.getMessage());
        }

        System.out.println("Program continues normally after the blocked exit attempt.");
    }
}
```

**How to run:**
```
java BlockExitBasic.java
```

Expected output:
```
Blocked: System.exit(1) is not allowed here
Program continues normally after the blocked exit attempt.
```

### Level 2 — Intermediate

```java
// File: BlockSpecificFileWrite.java
import java.io.*;

@SuppressWarnings("removal")
public class BlockSpecificFileWrite {
    static final String PROTECTED_PATH = "protected-config.txt";

    public static void main(String[] args) {
        SecurityManager sm = new SecurityManager() {
            @Override
            public void checkWrite(String file) {
                if (file.endsWith(PROTECTED_PATH)) {
                    throw new SecurityException("Writing to " + PROTECTED_PATH + " is not allowed");
                }
            }
        };
        System.setSecurityManager(sm);

        tryWrite("scratch-output.txt", "temporary data");
        tryWrite(PROTECTED_PATH, "should never be written");
    }

    static void tryWrite(String filename, String content) {
        try (FileWriter writer = new FileWriter(filename)) {
            writer.write(content);
            System.out.println("Wrote to " + filename);
            new File(filename).deleteOnExit();
        } catch (SecurityException e) {
            System.out.println("Blocked write to " + filename + ": " + e.getMessage());
        } catch (IOException e) {
            System.out.println("I/O error writing to " + filename + ": " + e.getMessage());
        }
    }
}
```

**How to run:**
```
java BlockSpecificFileWrite.java
```

Expected output:
```
Wrote to scratch-output.txt
Blocked write to protected-config.txt: Writing to protected-config.txt is not allowed
```

### Level 3 — Advanced

```java
// File: DeprecationWarningDemo.java
// Intentionally omits @SuppressWarnings so the deprecation warning is visible at compile time.
public class DeprecationWarningDemo {
    public static void main(String[] args) {
        System.out.println("java.specification.version: " + System.getProperty("java.specification.version"));

        SecurityManager existing = System.getSecurityManager();
        System.out.println("SecurityManager currently installed: " + (existing != null));

        SecurityManager sm = new SecurityManager() {
            @Override
            public void checkPermission(java.security.Permission perm) {
                // Permissive: allow everything, just for this demonstration's compile-warning purpose.
            }
        };
        System.setSecurityManager(sm);
        System.out.println("Installed a permissive SecurityManager (still functional, still deprecated).");
        System.setSecurityManager(null); // clean up: remove it again
        System.out.println("SecurityManager removed.");
    }
}
```

**How to run (note the compiler warning on the second command):**
```
java DeprecationWarningDemo.java
javac -Xlint:removal DeprecationWarningDemo.java
```

Expected output (the `java` run succeeds normally; the separate `javac -Xlint:removal` compile step additionally prints deprecation warnings to stderr):
```
java.specification.version: 17
SecurityManager currently installed: false
Installed a permissive SecurityManager (still functional, still deprecated).
SecurityManager removed.
```

Expected `javac -Xlint:removal` warning output (exact wording varies by JDK build):
```
DeprecationWarningDemo.java:11: warning: [removal] SecurityManager in java.lang has been deprecated and marked for removal
        SecurityManager existing = System.getSecurityManager();
        ^
...
3 warnings
```

## 6. Walkthrough

1. `DeprecationWarningDemo.main` first prints `java.specification.version` to confirm which Java SE version is in effect, then checks `System.getSecurityManager()` — this returns `null` unless a security manager has already been installed elsewhere, which is the normal, default state for a Java 17 application (no security manager runs unless explicitly installed).
2. An anonymous `SecurityManager` subclass is created overriding `checkPermission(Permission)` with an empty body — deliberately permissive, since this example exists to demonstrate the *compiler warning*, not to actually restrict anything.
3. `System.setSecurityManager(sm)` installs it; from this point until it's removed, every security-sensitive JDK operation that calls through to a `checkXxx` method would consult this security manager (though, because `checkPermission` here does nothing, every check silently passes).
4. `System.setSecurityManager(null)` removes the installed security manager again, restoring the default no-security-manager state — this call itself is also flagged by the deprecation, since `setSecurityManager` in its entirety is deprecated for removal, not merely the act of installing a *restrictive* one.
5. Running this file with plain `java DeprecationWarningDemo.java` succeeds and prints the expected output with no visible warning, because the single-file source-launcher doesn't surface lint warnings by default; compiling it explicitly with `javac -Xlint:removal DeprecationWarningDemo.java` is what surfaces the actual deprecation warnings the JEP introduced — one warning per line of code that touches a deprecated-for-removal API, exactly the loud, explicit signal JEP 411 was designed to give developers ahead of the mechanism's eventual removal.
6. In `BlockSpecificFileWrite` (Level 2), the overridden `checkWrite(String file)` method is consulted automatically by `FileWriter`'s internals before any actual write occurs — `tryWrite("scratch-output.txt", ...)` passes through because the filename doesn't end with `"protected-config.txt"`, while `tryWrite(PROTECTED_PATH, ...)` triggers the `throw` inside `checkWrite`, which propagates up as a caught `SecurityException` before any bytes are ever written to that file.

```
System.setSecurityManager(customSM)
        │
sensitive operation attempted (System.exit, file write, ...)
        │
JDK internals call customSM.checkXxx(...) automatically
        │
   checkXxx throws SecurityException?  -> operation aborted, exception propagates
   checkXxx returns normally?          -> operation proceeds as usual
```

## 7. Gotchas & takeaways

> `SecurityManager` was **removed outright** in a much later JDK release, well after Java 17 — code relying on it (as shown throughout this tutorial) is only guaranteed to work through the releases where the mechanism is deprecated but not yet removed. Treat any new `SecurityManager`-based code written today as inherently short-lived, and plan a migration path (containers, separate processes, module encapsulation) rather than investing further in this API.
- `@SuppressWarnings("removal")` silences the compiler warning for code that must still use `SecurityManager` during the deprecation window — use it deliberately and sparingly, as a marker of "this is known legacy code, not an oversight," rather than scattering it reflexively.
- `-Xlint:removal` (shown in Level 3) is the explicit way to surface every deprecated-for-removal usage in a codebase at compile time — a useful audit step before upgrading past whichever JDK release ultimately drops the API.
- The original applet-sandboxing use case `SecurityManager` was designed for had already disappeared from the ecosystem well before this deprecation — browsers stopped supporting the applet plugin model years earlier, which is the core reason this JEP judged the mechanism's ongoing maintenance cost no longer worth its shrinking, largely-repurposed user base.
- If your use case for `SecurityManager` was actually process- or thread-level capability restriction inside a single trusted application (rather than sandboxing genuinely untrusted code), that was already an unintended, unsupported use of the API — modern alternatives (separate OS processes, containers, or careful module boundaries) are both more robust and not scheduled for removal.
- This JEP lands in the same release as [Context-specific deserialization filters](0711-context-specific-deserialization-filters.md) — both reflect a broader shift in how the JDK approaches security: away from one coarse, globally-installed mechanism checked on every sensitive call, toward narrower, purpose-built, context-aware controls for the specific risks that remain relevant today.
