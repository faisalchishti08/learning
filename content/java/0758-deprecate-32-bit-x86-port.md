---
card: java
gi: 758
slug: deprecate-32-bit-x86-port
title: Deprecate 32-bit x86 port
---

## 1. What it is

**Java 21** (JEP 449) formally **deprecates the 32-bit x86 port** of the JDK, marking it for potential removal in a future release. This is a **porting/platform-support** change, not a language or library feature: the JDK build for 32-bit x86 (`x86-32`, distinct from the still-fully-supported 64-bit `amd64`/`x64` port) is now flagged as deprecated, meaning it continues to be built and shipped for this release but carries an explicit signal that it should not be relied upon long-term, and that new development effort is not going into it.

## 2. Why & when

32-bit x86 hardware and operating systems have been steadily shrinking in relevance for the kind of server, cloud, and desktop workloads modern Java targets — 64-bit x86 (`amd64`) has been the dominant deployment target for well over a decade, offering a larger address space, more registers, and better throughput for the memory-hungry, multi-gigabyte-heap workloads typical of contemporary JVM applications. Maintaining a 32-bit x86 port means continuing to test, fix platform-specific bugs for, and validate every JDK feature (including newer ones like large-heap-oriented garbage collectors that make little sense on a platform limited to a 4 GB address space) against an architecture an ever-shrinking fraction of real deployments actually use. Deprecating it here is the standard first step in the JDK's own two-stage removal process — a JEP has previously done this for other legacy pieces (Applet API removal, RMI Activation removal) — giving downstream users, distribution maintainers, and anyone still building for genuinely 32-bit-only hardware advance notice and a real release cycle to migrate before actual removal lands in a subsequent JDK version. If your organization ships to embedded or legacy hardware that is genuinely 32-bit x86 only, this JEP is the signal to plan a migration path — either to 64-bit hardware, or to a different JVM distribution that might choose to keep maintaining a 32-bit x86 port independently after the mainline OpenJDK project drops it.

## 3. Core concept

```java
// Ordinary Java code — completely unaware of and unaffected by whether the
// underlying JVM happens to be a 32-bit or 64-bit build.
public class WhichBitness {
    public static void main(String[] args) {
        System.out.println("os.arch: " + System.getProperty("os.arch"));
        System.out.println("sun.arch.data.model: " + System.getProperty("sun.arch.data.model"));
    }
}
```

On a 64-bit x86 (`amd64`) build this prints `sun.arch.data.model: 64`; on the now-deprecated 32-bit x86 build of the same JDK version, the identical source and bytecode still run, but print `32` — the deprecation is a build/platform-support decision, not something application code needs to branch on today.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The JDK's two-stage removal process: a feature or platform port is first marked deprecated in one release, giving advance notice, before being considered for removal in a later release">
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="50" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Java 21: deprecated</text>

  <line x1="200" y1="45" x2="250" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrow758)"/>
  <defs><marker id="arrow758" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="260" y="20" width="180" height="50" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="350" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">still built, still works</text>

  <line x1="440" y1="45" x2="490" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrow758)"/>

  <rect x="500" y="20" width="120" height="50" rx="8" fill="#0f1620" stroke="#8b949e" stroke-dasharray="4"/>
  <text x="560" y="50" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">future: possible removal</text>

  <text x="320" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Deprecation is advance notice, not immediate removal — 32-bit x86 still fully functions in Java 21</text>
</svg>

*Deprecation buys migration time before an eventual removal decision in a later release.*

## 5. Runnable example

Scenario: a small diagnostic and compatibility-planning tool for teams that need to audit whether their deployment targets depend on a platform now flagged for eventual removal — growing from basic architecture detection into an automated build-matrix compatibility check.

### Level 1 — Basic

```java
public class ArchCheckBasic {
    public static void main(String[] args) {
        String arch = System.getProperty("os.arch");
        String dataModel = System.getProperty("sun.arch.data.model");
        System.out.println("Running on: " + arch + " (" + dataModel + "-bit)");
    }
}
```

**How to run:** `java ArchCheckBasic.java` (JDK 21+; the identical source runs on any supported architecture).

This just reports the current JVM's architecture and bitness — the starting point for any audit of what platforms a deployment fleet is actually running on.

### Level 2 — Intermediate

```java
public class ArchCheckWarning {
    static final java.util.Set<String> DEPRECATED_ARCHES = java.util.Set.of("x86");

    public static void main(String[] args) {
        String arch = System.getProperty("os.arch");
        String dataModel = System.getProperty("sun.arch.data.model");
        System.out.println("Running on: " + arch + " (" + dataModel + "-bit)");

        if (DEPRECATED_ARCHES.contains(arch) || "32".equals(dataModel)) {
            System.out.println("WARNING: this appears to be a 32-bit x86 build, "
                + "deprecated as of Java 21 (JEP 449) and a candidate for removal "
                + "in a future JDK release. Plan a migration to a 64-bit target.");
        } else {
            System.out.println("No deprecated-architecture warning for this platform.");
        }
    }
}
```

**How to run:** `java ArchCheckWarning.java`.

The real-world concern added: an explicit check flagging exactly the deprecated platform, so this tool could be dropped into a CI pipeline or fleet-audit script to surface risk automatically rather than relying on someone remembering which JDK release notes mentioned a deprecation.

### Level 3 — Advanced

```java
import java.util.*;

public class BuildMatrixAudit {
    record DeploymentTarget(String name, String arch, int bits, String jdkVersion) {}

    static List<String> auditTarget(DeploymentTarget target) {
        List<String> findings = new ArrayList<>();
        if (target.bits() == 32 && target.arch().equals("x86")) {
            findings.add(target.name() + ": running 32-bit x86 — deprecated since Java 21 (JEP 449), plan migration");
        }
        if (target.jdkVersion().compareTo("21") < 0 && target.bits() == 32) {
            findings.add(target.name() + ": pre-21 JDK on 32-bit x86 — deprecation warning will appear after upgrading to 21+");
        }
        return findings;
    }

    public static void main(String[] args) {
        List<DeploymentTarget> fleet = List.of(
            new DeploymentTarget("prod-web-01", "amd64", 64, "21"),
            new DeploymentTarget("legacy-embedded-03", "x86", 32, "17"),
            new DeploymentTarget("edge-device-12", "x86", 32, "21"),
            new DeploymentTarget("prod-db-01", "aarch64", 64, "21")
        );

        List<String> allFindings = new ArrayList<>();
        for (DeploymentTarget target : fleet) {
            allFindings.addAll(auditTarget(target));
        }

        System.out.println("Audited " + fleet.size() + " deployment targets.");
        if (allFindings.isEmpty()) {
            System.out.println("No deprecated-architecture risks found.");
        } else {
            System.out.println("Findings:");
            allFindings.forEach(f -> System.out.println("  - " + f));
        }
    }
}
```

**How to run:** `java BuildMatrixAudit.java`.

This adds the production-flavored hard case: auditing a small, realistic **fleet inventory** of deployment targets (mixing architectures and JDK versions) against the deprecation, surfacing both currently-affected targets and targets that will start showing warnings once they upgrade — exactly the kind of pre-migration audit a platform team would run before broadly adopting Java 21.

## 6. Walkthrough

Tracing `BuildMatrixAudit.main`:

1. `main` builds a `fleet` list of four `DeploymentTarget` records representing a mixed inventory: a modern 64-bit production web server, a legacy 32-bit embedded device still on JDK 17, a 32-bit edge device already on JDK 21, and a 64-bit ARM database server.
2. The loop calls `auditTarget` for each. For `"prod-web-01"` (`amd64`, 64-bit, JDK 21): neither `if` condition in `auditTarget` matches (`bits() == 32` is false), so no findings are added.
3. For `"legacy-embedded-03"` (`x86`, 32-bit, JDK 17): the first check (`bits() == 32 && arch equals "x86"`) is true regardless of JDK version, but the specific deprecation *notice text* is about the Java 21 JEP — the second check catches that this target is on a pre-21 JDK, so it gets the "will appear after upgrading" finding instead of (or alongside) the direct deprecation finding. Both `if` blocks are independent, so this target could accumulate findings from both if both conditions are true — here it's 32-bit x86 (matches check one) and pre-21 (matches check two), so it gets both messages.
4. For `"edge-device-12"` (`x86`, 32-bit, JDK 21): only the first check matches (`bits() == 32 && arch equals "x86"`); the second check's `jdkVersion().compareTo("21") < 0` is false since it's already on 21, so only the direct deprecation finding is added.
5. For `"prod-db-01"` (`aarch64`, 64-bit, JDK 21): neither check matches — ARM64 was never the architecture this JEP deprecates, and it's 64-bit regardless.
6. `main` collects every target's findings into `allFindings` and prints them, giving a platform team a concrete, itemized list of exactly which fleet members need a migration plan before the eventual removal of 32-bit x86 support lands in some future JDK release.

Expected output:
```
Audited 4 deployment targets.
Findings:
  - legacy-embedded-03: running 32-bit x86 — deprecated since Java 21 (JEP 449), plan migration
  - legacy-embedded-03: pre-21 JDK on 32-bit x86 — deprecation warning will appear after upgrading to 21+
  - edge-device-12: running 32-bit x86 — deprecated since Java 21 (JEP 449), plan migration
```

## 7. Gotchas & takeaways

> **Gotcha:** deprecation is **not** removal — a 32-bit x86 JDK 21 build still fully functions, and existing 32-bit x86 deployments do not break the moment they upgrade to Java 21. The risk this JEP signals is entirely about the future: a subsequent JDK release may drop the port outright, so treat Java 21 as the deadline for *starting* migration planning, not evidence that anything is broken today.

- This is a platform-support deprecation, not an application-visible API change — no class, method, or language feature is affected, and `System.getProperty("os.arch")`/`"sun.arch.data.model"` remain the standard way to detect the current platform if you need to.
- 64-bit x86 (`amd64`) and other 64-bit architectures (ARM64, RISC-V64) are entirely unaffected — this deprecation is specific to the legacy 32-bit x86 port.
- Teams still deploying to genuinely 32-bit-only hardware (some embedded and legacy industrial systems) should treat this as the trigger to plan a migration — to 64-bit hardware where feasible, or to evaluate whether an alternative JDK distribution intends to keep supporting 32-bit x86 independently after mainline OpenJDK removes it.
- This follows the same two-stage deprecate-then-remove pattern used for other legacy JDK components (the Applet API, RMI Activation) — expect an explicit removal JEP in some future release rather than a silent drop.
- A simple architecture/bitness audit script, as shown in Level 3, is a low-effort way to get ahead of this kind of platform-support change across a real deployment fleet before it becomes urgent.
