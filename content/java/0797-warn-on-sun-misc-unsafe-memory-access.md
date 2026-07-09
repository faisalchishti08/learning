---
card: java
gi: 797
slug: warn-on-sun-misc-unsafe-memory-access
title: Warn on sun.misc.Unsafe memory access
---

## 1. What it is

**Java 24** (JEP 498) escalates [Java 23's compile-time deprecation](0782-deprecate-memory-access-methods-in-sun-misc-unsafe.md) of `sun.misc.Unsafe`'s memory-access methods into a **runtime warning**: the first time any application code calls `allocateMemory`, `putInt`, `getInt`, `copyMemory`, or any of the other deprecated memory-access methods, the JVM prints a warning directly to standard error at run time — not just a `javac`-time compiler message that a rebuild might silence. This makes the deprecation visible even to code that was compiled years ago against an older JDK and is only now being *run* on Java 24, closing the gap where a compile-time-only warning could otherwise go unnoticed indefinitely for already-compiled `.jar` files.

## 2. Why & when

A compile-time deprecation warning only reaches developers who actively recompile the affected code — but a huge amount of real-world `Unsafe`-dependent code lives inside already-published libraries and frameworks, shipped as compiled `.jar` files that most downstream consumers never recompile from source. Java 23's compiler warning was invisible to exactly those consumers: an application depending on a library using deprecated `Unsafe` methods would compile and run cleanly, with no signal at all that a dependency was relying on something scheduled for eventual removal. JEP 498 fixes that visibility gap by moving the warning to where it can't be missed as easily — the moment the JVM actually executes one of these deprecated calls, regardless of when or with what compiler the calling code was built. This is a direct escalation on the same removal timeline `sun.misc.Unsafe`'s memory methods are on: deprecate at compile time (Java 23), warn at run time (Java 24), and the expected eventual future step is to require an explicit opt-in flag before allowing the calls at all, ahead of outright removal.

## 3. Core concept

```java
// Java 24: this call now prints a runtime warning to stderr on first use,
// in addition to the Java 23 compile-time deprecation warning.
sun.misc.Unsafe unsafe = ...; // obtained via reflection, as always
long address = unsafe.allocateMemory(64);
```

Running this on Java 24 prints something like:
```
WARNING: A terminally deprecated method in sun.misc.Unsafe has been called
WARNING: sun.misc.Unsafe::allocateMemory has been called by com.example.MyLibrary
WARNING: Please consider reporting this to the maintainers of com.example.MyLibrary
WARNING: sun.misc.Unsafe::allocateMemory will be removed in a future release
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The escalation path for deprecated Unsafe memory methods: compile-time warning in Java 23, runtime warning in Java 24, with an eventual opt-in requirement and removal expected in later releases" >
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="110" y="42" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Java 23:</text>
  <text x="110" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">compile-time warning only</text>

  <line x1="200" y1="45" x2="250" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#a797)"/>
  <defs><marker id="a797" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="260" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Java 24:</text>
  <text x="350" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">runtime warning on first call</text>

  <line x1="440" y1="45" x2="490" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#a797)"/>

  <rect x="500" y="20" width="120" height="50" rx="8" fill="#0f1620" stroke="#8b949e" stroke-dasharray="4"/>
  <text x="560" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">future:</text>
  <text x="560" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">opt-in, then removal</text>

  <text x="320" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">The runtime warning reaches consumers of pre-compiled jars, not just recompiled source</text>
</svg>

*Runtime visibility catches what compile-time-only warnings miss: already-compiled dependencies.*

## 5. Runnable example

Scenario: an off-heap counter, first shown reproducing the runtime warning directly, then wrapped so the warning becomes actionable diagnostic output, then extended into a small dependency-auditing tool that surfaces which library in a stack trace triggered the warning.

### Level 1 — Basic

```java
import java.lang.reflect.*;
import sun.misc.Unsafe;

public class UnsafeWarningBasic {
    public static void main(String[] args) throws Exception {
        Field f = Unsafe.class.getDeclaredField("theUnsafe");
        f.setAccessible(true);
        Unsafe unsafe = (Unsafe) f.get(null);

        long address = unsafe.allocateMemory(4); // triggers the Java 24 runtime warning on first call
        unsafe.putInt(address, 42);
        System.out.println("value: " + unsafe.getInt(address));
        unsafe.freeMemory(address);
    }
}
```

**How to run:** `java --add-opens java.base/sun.misc=ALL-UNNAMED UnsafeWarningBasic.java` (JDK 24+; watch standard error — a `WARNING:` block appears once, on the first deprecated call, not on every subsequent one).

Confirms the warning fires directly: this program's output on stdout is unaffected, but stderr now carries the new Java 24 runtime warning the first time `allocateMemory` executes.

### Level 2 — Intermediate

```java
import java.lang.reflect.*;
import sun.misc.Unsafe;
import java.io.*;

public class UnsafeWarningCaptured {
    public static void main(String[] args) throws Exception {
        // Redirect stderr temporarily to capture and inspect the warning programmatically —
        // a technique useful for testing/CI that wants to assert a warning did (or didn't) fire.
        ByteArrayOutputStream captured = new ByteArrayOutputStream();
        PrintStream originalErr = System.err;
        System.setErr(new PrintStream(captured));

        try {
            Field f = Unsafe.class.getDeclaredField("theUnsafe");
            f.setAccessible(true);
            Unsafe unsafe = (Unsafe) f.get(null);
            long address = unsafe.allocateMemory(4);
            unsafe.freeMemory(address);
        } finally {
            System.setErr(originalErr);
        }

        String warningOutput = captured.toString();
        boolean warned = warningOutput.contains("terminally deprecated");
        System.out.println("deprecated Unsafe warning observed: " + warned);
    }
}
```

**How to run:** `java --add-opens java.base/sun.misc=ALL-UNNAMED UnsafeWarningCaptured.java`.

The real-world concern added: **programmatically capturing** stderr to detect whether the warning fired — the kind of check a CI pipeline could run against a dependency's test suite to confirm (or rule out) that it still triggers deprecated `Unsafe` warnings, without a human needing to eyeball console output.

### Level 3 — Advanced

```java
import java.lang.reflect.*;
import sun.misc.Unsafe;
import java.io.*;
import java.util.*;

public class UnsafeDependencyAudit {
    record AuditResult(String method, boolean warningFired, String rawWarning) {}

    static AuditResult auditCall(String label, Runnable unsafeCall) {
        ByteArrayOutputStream captured = new ByteArrayOutputStream();
        PrintStream originalErr = System.err;
        System.setErr(new PrintStream(captured));
        try {
            unsafeCall.run();
        } finally {
            System.setErr(originalErr);
        }
        String output = captured.toString();
        return new AuditResult(label, output.contains("terminally deprecated"), output.trim());
    }

    public static void main(String[] args) throws Exception {
        Field f = Unsafe.class.getDeclaredField("theUnsafe");
        f.setAccessible(true);
        Unsafe unsafe = (Unsafe) f.get(null);

        List<AuditResult> results = new ArrayList<>();

        results.add(auditCall("allocateMemory", () -> {
            long addr = unsafe.allocateMemory(8);
            unsafe.freeMemory(addr);
        }));

        results.add(auditCall("arrayBaseOffset (non-memory-access, unaffected)", () -> {
            unsafe.arrayBaseOffset(int[].class); // not one of the deprecated memory-access methods
        }));

        for (AuditResult r : results) {
            System.out.println(r.method() + " -> warning fired: " + r.warningFired());
        }
    }
}
```

**How to run:** `java --add-opens java.base/sun.misc=ALL-UNNAMED UnsafeDependencyAudit.java`.

This adds the production-flavored hard case: distinguishing between an actually-**deprecated** `Unsafe` memory-access method (`allocateMemory`) and a **non-memory-access** `Unsafe` method (`arrayBaseOffset`, unaffected by this specific JEP) — the kind of precise audit a library maintainer would run to confirm exactly which of their `Unsafe` usages need migrating to the [Foreign Function & Memory API](0759-foreign-function-memory-api-standardized.md) versus which ones remain unaffected by this particular deprecation-and-warning track.

## 6. Walkthrough

Tracing `UnsafeDependencyAudit.main`:

1. `main` obtains the singleton `Unsafe` instance via the same reflection trick used across all `Unsafe`-based examples, then builds a `results` list.
2. `auditCall("allocateMemory", ...)` redirects `System.err` to an in-memory buffer, runs a lambda that allocates and immediately frees 8 bytes of off-heap memory via `Unsafe`, then restores the original `System.err` and inspects the captured output for the Java 24 runtime warning's characteristic text.
3. Because `allocateMemory` is one of the methods [deprecated for removal in Java 23](0782-deprecate-memory-access-methods-in-sun-misc-unsafe.md), calling it fires the runtime warning — `warningFired` is `true` for this entry, since this is the **first** call to any deprecated `Unsafe` memory method in this JVM process (the JVM typically only warns once per method per process, not on every call).
4. `auditCall("arrayBaseOffset ...", ...)` runs the same capture-and-restore pattern around a call to `arrayBaseOffset`, a different `Unsafe` method that computes array-layout metadata rather than performing raw memory access — this method is **not** part of the set targeted by JEP 498's warning, so no warning text appears in the captured output, and `warningFired` is `false`.
5. `main` iterates `results` and prints each method's audited outcome.

Expected output:
```
allocateMemory -> warning fired: true
arrayBaseOffset (non-memory-access, unaffected) -> warning fired: false
```

## 7. Gotchas & takeaways

> **Gotcha:** the JVM typically emits this warning **once per distinct deprecated method per process**, not once per call — running the same deprecated method a thousand times in a loop produces one warning, not a thousand. Don't assume warning volume in a log file is a reliable proxy for call *frequency*; it only reliably indicates call *presence*.

- Java 24 (JEP 498) escalates [Java 23's compile-time deprecation](0782-deprecate-memory-access-methods-in-sun-misc-unsafe.md) of `sun.misc.Unsafe`'s memory-access methods with a **runtime** warning printed to stderr on first use.
- Unlike the compile-time warning, this reaches consumers of already-compiled `.jar` dependencies, not just code being freshly recompiled — a much broader visibility net.
- The warning is emitted once per distinct deprecated method per JVM process, not once per call.
- Only the specific memory-access methods targeted by the Java 23 deprecation trigger this warning — other `Unsafe` methods (like `arrayBaseOffset`) are unaffected.
- The expected next steps on this removal timeline are an eventual opt-in requirement before these methods can be called at all, followed by outright removal — treat this warning as active pressure to migrate to the [Foreign Function & Memory API](0759-foreign-function-memory-api-standardized.md) sooner rather than later.
