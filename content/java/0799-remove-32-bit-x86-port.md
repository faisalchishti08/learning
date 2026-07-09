---
card: java
gi: 799
slug: remove-32-bit-x86-port
title: Remove 32-bit x86 port
---

## 1. What it is

**Java 24** (JEP 501) **removes** the source code and build support for the 32-bit x86 (`x86-32`/`linux-x86-32`) port of the JDK, completing the two-stage removal process [Java 21's deprecation](0758-deprecate-32-bit-x86-port.md) started. From Java 24 onward, there is no OpenJDK build for 32-bit x86 at all — the platform-specific source code, build configurations, and test infrastructure that supported it have been deleted from the codebase. This is purely a **build/platform-support** change: 64-bit x86 (`amd64`) and every other supported 64-bit architecture (ARM64, RISC-V64) are completely unaffected.

## 2. Why & when

Java 21's deprecation was explicit advance notice, not a threat left unfulfilled — the entire point of a deprecate-then-remove process is that the removal actually happens on a predictable timeline, giving anyone still depending on the deprecated thing a real, bounded window to migrate rather than an open-ended "maybe someday." By Java 24, three full JDK release cycles (Java 21, 22, 23) had passed since the deprecation, each one continuing to build and ship the 32-bit x86 port purely as a courtesy while carrying the maintenance cost of a platform an ever-shrinking fraction of Java deployments actually used. Actually removing the port's source and build support at this point stops that ongoing cost: no more porting effort, no more platform-specific bug triage, no more validating every new JDK feature (including large-heap-oriented collectors that never made sense on a 4 GB-address-space platform to begin with) against an architecture with negligible remaining real-world usage. Any organization still deploying to genuinely 32-bit-only x86 hardware needed to have completed their migration — to 64-bit hardware, or to an alternative JVM distribution choosing to maintain a 32-bit x86 fork independently — before adopting Java 24; there is no configuration flag or workaround that brings this port back on mainline OpenJDK.

## 3. Core concept

```
# Java 21-23: a 32-bit x86 build of the JDK still existed (deprecated but functional).
# Java 24: no such build exists at all — attempting to obtain or build one from
# mainline OpenJDK source fails, since the platform-specific code has been removed.

java -version
# On any Java 24 build, this always reports a 64-bit (or other 64-bit architecture) JVM —
# there is no 32-bit x86 Java 24 JVM to report anything else.
```

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The 32-bit x86 port's full lifecycle: deprecated in Java 21, still built through Java 23, then completely removed from the codebase in Java 24 with no way to bring it back on mainline OpenJDK" >
  <rect x="20" y="20" width="180" height="55" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="110" y="42" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Java 21: deprecated</text>
  <text x="110" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">still built and works</text>

  <line x1="200" y1="47" x2="240" y2="47" stroke="#79c0ff" stroke-width="2" marker-end="url(#a799)"/>
  <defs><marker id="a799" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="250" y="20" width="180" height="55" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="340" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Java 22-23: still built</text>
  <text x="340" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">migration window continues</text>

  <line x1="430" y1="47" x2="470" y2="47" stroke="#79c0ff" stroke-width="2" marker-end="url(#a799)"/>

  <rect x="480" y="20" width="160" height="55" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="560" y="42" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Java 24: removed</text>
  <text x="560" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no build exists at all</text>

  <text x="320" y="175" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Three full release cycles of advance notice, then the port is actually gone</text>
</svg>

*A deprecation warning that was, in fact, followed by real removal on schedule.*

## 5. Runnable example

Scenario: a platform-compatibility audit tool, growing from a basic architecture check into a fleet-wide migration-verification report confirming no deployment target is still relying on the now-removed port.

### Level 1 — Basic

```java
public class ArchCheckRemoved {
    public static void main(String[] args) {
        String arch = System.getProperty("os.arch");
        String dataModel = System.getProperty("sun.arch.data.model");
        String javaVersion = System.getProperty("java.version");
        System.out.println("Java " + javaVersion + " running on: " + arch + " (" + dataModel + "-bit)");
    }
}
```

**How to run:** `java ArchCheckRemoved.java` (JDK 24+; this same source, run on JDK 24, can only ever report a 64-bit or other non-x86-32 architecture, since no 32-bit x86 build of JDK 24 exists to run it on in the first place).

Reports the current JVM's architecture — on Java 24+, `dataModel` reporting `"32"` alongside `arch` reporting `"x86"` is now a structural impossibility rather than merely deprecated behavior.

### Level 2 — Intermediate

```java
public class MigrationVerification {
    public static void main(String[] args) {
        String javaVersion = System.getProperty("java.version");
        String arch = System.getProperty("os.arch");
        int majorVersion = Integer.parseInt(javaVersion.split("\\.")[0]);

        System.out.println("Java version: " + javaVersion + ", arch: " + arch);

        if (majorVersion >= 24) {
            System.out.println("Running on Java 24+: 32-bit x86 is structurally impossible here — "
                + "if this deployment target used to be x86-32, migration to 64-bit hardware "
                + "already succeeded, since this program couldn't run here otherwise.");
        } else if ("x86".equals(arch) && "32".equals(System.getProperty("sun.arch.data.model"))) {
            System.out.println("WARNING: running on deprecated 32-bit x86 under Java " + javaVersion
                + " — this JVM cannot be upgraded to Java 24+ without a hardware migration first.");
        } else {
            System.out.println("Running on a non-x86-32 platform under Java " + javaVersion
                + " — no migration blocker from this specific removal.");
        }
    }
}
```

**How to run:** `java MigrationVerification.java`.

The real-world concern added: a **version-aware** check — the mere fact that this program is running successfully at all under Java 24+ already proves the deployment target isn't 32-bit x86 (since no such Java 24 build exists), turning "did we migrate?" into something this program's own successful execution answers, rather than something it needs to separately detect.

### Level 3 — Advanced

```java
import java.util.*;

public class FleetRemovalAudit {
    record DeploymentTarget(String name, String arch, int bits, String jdkVersion) {}

    static String assessTarget(DeploymentTarget target) {
        int major = Integer.parseInt(target.jdkVersion().split("\\.")[0]);
        boolean isX86_32 = target.arch().equals("x86") && target.bits() == 32;

        if (major >= 24 && isX86_32) {
            // This combination cannot actually exist — flagged as a data-integrity issue,
            // not a real deployment, since no Java 24+ build runs on 32-bit x86 at all.
            return target.name() + ": INVALID RECORD — Java 24+ paired with x86-32 is impossible; check inventory data";
        }
        if (major < 24 && isX86_32) {
            return target.name() + ": BLOCKED — still on x86-32 (Java " + target.jdkVersion()
                + "); must migrate hardware before any Java 24+ upgrade";
        }
        if (major >= 24) {
            return target.name() + ": OK — Java " + target.jdkVersion() + " on " + target.arch()
                + ", 32-bit x86 removal does not affect this target";
        }
        return target.name() + ": OK — pre-Java-24, not on x86-32, no action needed yet";
    }

    public static void main(String[] args) {
        List<DeploymentTarget> fleet = List.of(
            new DeploymentTarget("prod-web-01", "amd64", 64, "24"),
            new DeploymentTarget("legacy-embedded-03", "x86", 32, "17"),
            new DeploymentTarget("edge-device-12", "x86", 32, "23"),
            new DeploymentTarget("prod-db-01", "aarch64", 64, "24")
        );

        System.out.println("Fleet removal-readiness audit:");
        for (DeploymentTarget target : fleet) {
            System.out.println("  " + assessTarget(target));
        }
    }
}
```

**How to run:** `java FleetRemovalAudit.java`.

This adds the production-flavored hard case: a fleet inventory audit that classifies each deployment target against the **completed removal**, distinguishing targets that have already safely upgraded (`prod-web-01`, `prod-db-01`), targets still blocked on 32-bit x86 hardware and therefore stuck below Java 24 (`legacy-embedded-03`, `edge-device-12`), and even guarding against **impossible inventory records** (a target claiming both Java 24+ and 32-bit x86, which the removal itself guarantees cannot be a real, functioning deployment) — the kind of sanity check a fleet-management system should apply once a removal like this actually lands.

## 6. Walkthrough

Tracing `FleetRemovalAudit.main`:

1. `main` builds a `fleet` list of four `DeploymentTarget` records: a 64-bit production web server already on Java 24, a 32-bit embedded device still on Java 17, a 32-bit edge device on Java 23, and a 64-bit ARM database server on Java 24.
2. For `"prod-web-01"` (`amd64`, Java 24): `major >= 24` is true and `isX86_32` is false, so `assessTarget` falls through to the `major >= 24` branch, reporting `"OK"` — this target has successfully adopted Java 24 with no conflict, since it was never on the removed platform.
3. For `"legacy-embedded-03"` (`x86`, 32-bit, Java 17): `major >= 24` is false, so the first check doesn't apply; the second check, `major < 24 && isX86_32`, is true, reporting `"BLOCKED"` — this target genuinely cannot upgrade to Java 24 without first migrating off 32-bit x86 hardware entirely.
4. For `"edge-device-12"` (`x86`, 32-bit, Java 23): the same `"BLOCKED"` classification applies, since it's still below Java 24 and still on the deprecated (now-removed-for-24+) platform.
5. For `"prod-db-01"` (`aarch64`, Java 24): like `prod-web-01`, this reports `"OK"` — a different 64-bit architecture entirely, never affected by this x86-specific removal.
6. `main` prints each target's assessment, giving a platform team a concrete, itemized readiness report distinguishing already-migrated targets from those still requiring a hardware migration before any further JDK upgrade.

Expected output:
```
Fleet removal-readiness audit:
  prod-web-01: OK — Java 24 on amd64, 32-bit x86 removal does not affect this target
  legacy-embedded-03: BLOCKED — still on x86-32 (Java 17); must migrate hardware before any Java 24+ upgrade
  edge-device-12: BLOCKED — still on x86-32 (Java 23); must migrate hardware before any Java 24+ upgrade
  prod-db-01: OK — Java 24 on aarch64, 32-bit x86 removal does not affect this target
```

## 7. Gotchas & takeaways

> **Gotcha:** unlike the Java 21 deprecation, this removal has **no workaround on mainline OpenJDK** — there is no flag, no configuration, no compatibility shim that brings back a 32-bit x86 Java 24 build. Any target genuinely stuck on 32-bit-only x86 hardware must either stay on Java 23 (or earlier) indefinitely, migrate to 64-bit hardware, or evaluate whether a third-party JVM distribution has chosen to independently maintain a 32-bit x86 fork — mainline OpenJDK is not that option anymore.

- Java 24 (JEP 501) completes the removal [Java 21 deprecated](0758-deprecate-32-bit-x86-port.md): 32-bit x86 source code and build support are gone from the OpenJDK codebase entirely.
- 64-bit x86 (`amd64`) and other 64-bit architectures (ARM64, RISC-V64) are completely unaffected — this removal is specific to the legacy 32-bit x86 port.
- Any deployment target still requiring 32-bit x86 must remain on Java 23 or earlier, migrate to 64-bit hardware, or seek an alternative JVM distribution maintaining that platform independently.
- This is the textbook completion of a two-stage deprecate-then-remove process, delivered on the timeline the deprecation JEP signaled three release cycles earlier.
- A fleet-audit script (as in Level 3) is a low-effort way to confirm, ahead of any Java 24 rollout, that no deployment target still genuinely depends on the now-removed platform.
