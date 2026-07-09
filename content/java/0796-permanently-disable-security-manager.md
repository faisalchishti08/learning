---
card: java
gi: 796
slug: permanently-disable-security-manager
title: Permanently disable Security Manager
---

## 1. What it is

**Java 24** (JEP 486) **permanently disables** the Security Manager — the JDK's old sandboxing mechanism for restricting what code is allowed to do (file access, network access, reflection, and more), deprecated for removal back in Java 17. As of Java 24, the Security Manager can no longer be enabled at all: `System.setSecurityManager(...)` throws `UnsupportedOperationException` unconditionally, and the `-Djava.security.manager` system property has no effect. The classes themselves (`SecurityManager`, `AccessController`, `Policy`) still exist for source and binary compatibility, but they no longer do anything — there is no longer any way to run Java code under an active Security Manager.

## 2. Why & when

The Security Manager was designed in the mid-1990s for a threat model that barely resembles how Java is deployed today — untrusted applets and browser plugins running arbitrary downloaded code inside a user's browser, needing per-permission sandboxing to prevent that code from reading local files or opening arbitrary network connections. That deployment model has been essentially extinct for years (browsers dropped plugin support entirely), yet the Security Manager's machinery — permission checks threaded through nearly every security-sensitive JDK API, `AccessController.doPrivileged(...)` calls scattered through internal code — remained a persistent tax on JDK performance and internal complexity, actively working against other JDK evolution (it interacts awkwardly with virtual threads' cheap-thread model, for instance). JEP 411 (Java 17) started the two-stage removal by deprecating it; this JEP completes that removal's *functional* half — the mechanism stops doing anything — while leaving the class files in place so code that merely references `SecurityManager` types (without actually depending on active sandboxing) doesn't fail to compile or load. Any application still trying to run untrusted code inside a JVM sandbox needs a fundamentally different isolation strategy now — a separate process, a container, or a different sandboxing technology entirely — since the JVM itself no longer offers this option.

## 3. Core concept

```java
public class SecurityManagerGone {
    public static void main(String[] args) {
        try {
            System.setSecurityManager(new SecurityManager());
        } catch (UnsupportedOperationException e) {
            System.out.println("Security Manager can no longer be enabled: " + e.getMessage());
        }
    }
}
```

On Java 24+, this always prints the caught message — `setSecurityManager` unconditionally throws, regardless of what `SecurityManager` subclass or configuration is passed to it.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The Security Manager's two-stage removal: deprecated in Java 17, functionally disabled in Java 24 — the classes remain for compatibility but setSecurityManager always throws" >
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="110" y="50" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Java 17: deprecated</text>

  <line x1="200" y1="45" x2="250" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#a796)"/>
  <defs><marker id="a796" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="260" y="20" width="200" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="50" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Java 24: permanently disabled</text>

  <line x1="460" y1="45" x2="510" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#a796)"/>

  <rect x="520" y="20" width="100" height="50" rx="8" fill="#0f1620" stroke="#8b949e" stroke-dasharray="4"/>
  <text x="570" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">future: removal</text>

  <text x="320" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">setSecurityManager() always throws now — no configuration re-enables it</text>
</svg>

*Classes remain for compatibility; the actual sandboxing mechanism no longer functions.*

## 5. Runnable example

Scenario: a legacy application that used to conditionally enable a restrictive Security Manager, migrated step by step to detect the new unconditional failure and adapt, then redesigned around a genuinely supported isolation approach.

### Level 1 — Basic

```java
public class SecurityManagerLegacyAttempt {
    public static void main(String[] args) {
        try {
            SecurityManager sm = new SecurityManager();
            System.setSecurityManager(sm);
            System.out.println("Security Manager enabled (would only happen pre-Java 24)");
        } catch (UnsupportedOperationException e) {
            System.out.println("Cannot enable Security Manager on this JDK: " + e.getMessage());
        }
    }
}
```

**How to run:** `java SecurityManagerLegacyAttempt.java` (JDK 24+; on JDK 17-23 this would instead print a deprecation warning but still succeed).

Legacy code that used to enable a Security Manager now needs to handle the guaranteed `UnsupportedOperationException` — the `try`/`catch` here is exactly what any code still calling `setSecurityManager` needs on Java 24+.

### Level 2 — Intermediate

```java
public class SecurityManagerDetection {
    static boolean securityManagerAvailable() {
        try {
            System.setSecurityManager(new SecurityManager());
            System.setSecurityManager(null); // clean up if it somehow succeeded
            return true;
        } catch (UnsupportedOperationException e) {
            return false;
        }
    }

    public static void main(String[] args) {
        if (securityManagerAvailable()) {
            System.out.println("Running on a JDK where Security Manager still works — configure sandboxing.");
        } else {
            System.out.println("Security Manager unavailable on this JDK (24+) — "
                + "falling back to process-level isolation instead.");
        }
    }
}
```

**How to run:** `java SecurityManagerDetection.java`.

The real-world concern added: a small compatibility-detection helper that a migrating codebase could use to branch its startup logic — on Java 24+ it always reports "unavailable," but the same code would have reported "available" (with a deprecation warning) on Java 17 through 23, letting an application support a range of JDK versions during a migration window.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.*;

public class SandboxMigrationDemo {
    // The OLD approach (no longer functional): restrict what a task can do
    // via a per-thread SecurityManager permission check. This method now
    // always fails fast on Java 24+, documenting exactly why.
    static void attemptLegacySandbox(Runnable untrustedTask) {
        try {
            System.setSecurityManager(new SecurityManager());
            try {
                untrustedTask.run();
            } finally {
                System.setSecurityManager(null);
            }
        } catch (UnsupportedOperationException e) {
            throw new IllegalStateException(
                "Legacy SecurityManager-based sandboxing is not available on this JDK. "
                + "Use a subprocess, container, or dedicated sandboxing library instead.", e);
        }
    }

    // The NEW approach: isolate untrusted work in a separate OS process,
    // which the JVM's Security Manager removal does not affect at all.
    static int runInSeparateProcess(String javaCode) throws Exception {
        ProcessBuilder pb = new ProcessBuilder("java", "--source", "24", "-")
            .redirectErrorStream(true);
        Process process = pb.start();
        process.getOutputStream().write(javaCode.getBytes());
        process.getOutputStream().close();

        try (var reader = process.inputReader()) {
            reader.lines().forEach(System.out::println);
        }
        return process.waitFor();
    }

    public static void main(String[] args) throws Exception {
        try {
            attemptLegacySandbox(() -> System.out.println("this never runs"));
        } catch (IllegalStateException e) {
            System.out.println("As expected: " + e.getMessage());
        }

        System.out.println("--- migrating to process-based isolation ---");
        int exitCode = runInSeparateProcess("void main() { System.out.println(\"ran in isolated process\"); }");
        System.out.println("isolated process exit code: " + exitCode);
    }
}
```

**How to run:** `java --enable-preview --source 24 SandboxMigrationDemo.java` (JDK 24+; requires `java` itself to be on the `PATH` for the subprocess launch, and uses [simple source files](0789-simple-source-files-instance-main-methods-4th-preview.md) syntax for the isolated snippet).

This adds the production-flavored hard case: demonstrating **both** the now-broken legacy pattern and a genuinely working replacement — spawning a separate `java` process via `ProcessBuilder` to run untrusted-ish code with OS-level process isolation, which remains fully available and unaffected by the Security Manager's removal, since it isolates at the operating-system level rather than inside a single JVM.

## 6. Walkthrough

Tracing `SandboxMigrationDemo.main`:

1. `main` calls `attemptLegacySandbox(...)` with a trivial task. Inside, `System.setSecurityManager(new SecurityManager())` immediately throws `UnsupportedOperationException`, since no JDK 24+ configuration can make this succeed.
2. `attemptLegacySandbox` catches that exception and wraps it in an `IllegalStateException` with a message explaining the situation and pointing toward the replacement strategy — the `untrustedTask.run()` call inside the (never-reached) `try` block never executes.
3. `main` catches that `IllegalStateException` and prints its message, confirming the legacy path is unavailable, as expected.
4. `main` then calls `runInSeparateProcess(...)`, which builds a `ProcessBuilder` for a **new, separate `java` process**, launching it to run a small simple-source-file snippet piped in via standard input.
5. The child process starts, compiles and runs the piped-in snippet completely independently of the parent JVM's process, and prints its own output; the parent reads that output line by line via `process.inputReader()` and echoes it.
6. `process.waitFor()` blocks until the child process exits, returning its exit code, which `main` prints.

Expected output:
```
As expected: Legacy SecurityManager-based sandboxing is not available on this JDK. Use a subprocess, container, or dedicated sandboxing library instead.
--- migrating to process-based isolation ---
ran in isolated process
isolated process exit code: 0
```

## 7. Gotchas & takeaways

> **Gotcha:** process-based isolation (as in the Level 3 example) is a genuinely different security boundary than the old Security Manager was — it isolates at the operating-system level (separate memory space, separate process permissions) rather than within a single JVM's object graph, which is both **stronger** in some respects (a sandboxed process truly cannot touch the parent's heap) and **more expensive** in others (process startup cost, IPC overhead for any needed communication). Don't assume a straightforward one-to-one replacement exists; evaluate what your specific sandboxing use case actually needed before picking a migration path.

- Java 24 (JEP 486) makes `System.setSecurityManager(...)` unconditionally throw `UnsupportedOperationException` — the Security Manager can no longer be enabled by any means.
- `SecurityManager`, `AccessController`, and `Policy` classes remain present for source/binary compatibility, but perform no actual sandboxing anymore.
- This is the functional completion of the deprecation JEP 411 started in Java 17 — expect the classes themselves to be candidates for eventual removal in a further future release.
- Applications that relied on the Security Manager for actual untrusted-code sandboxing need a different isolation strategy: separate OS processes, containers, or a dedicated sandboxing technology outside the JVM.
- Applications that merely referenced `SecurityManager`-related classes without depending on active sandboxing (increasingly rare, since most real usage was already deprecated-and-warned since Java 17) should be unaffected by this change at the source level.
