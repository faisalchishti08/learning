---
card: java
gi: 708
slug: macos-aarch64-apple-silicon-port
title: macOS AArch64 (Apple Silicon) port
---

## 1. What it is

**Java 17** shipped a native, first-class **macOS/AArch64 port** (JEP 391), meaning the JDK could be built and run as native **ARM64** machine code directly on Apple Silicon Macs (the M1 and its successors) — rather than only running as translated x86-64 code through Apple's Rosetta 2 binary translator. This JEP landed proactively, before most Apple Silicon Macs had even shipped to the public, specifically so a native ARM64 JDK would already be available and mature by the time developers needed it. Like the [Metal rendering pipeline](0707-new-macos-rendering-pipeline-metal.md) in this same release, it is a JDK build/platform-support change, not a language or API feature — Java source code is completely unaffected and runs unchanged on either architecture.

## 2. Why & when

Apple announced a two-year transition of its entire Mac lineup from Intel x86-64 processors to its own ARM64-based Apple Silicon chips. Without a native ARM64 JDK, Java applications on those new Macs would only run via Rosetta 2's on-the-fly x86-64-to-ARM64 translation — functional, but with real performance overhead and none of the power-efficiency or native-instruction benefits Apple Silicon hardware offered. JEP 391 built and validated a genuinely native `aarch64`-targeting macOS JDK ahead of general availability of the hardware, so the Java ecosystem wouldn't lag behind the platform shift. Because Rosetta 2 can transparently run an x86-64 JVM even on Apple Silicon hardware, this matters specifically when you care about *actually* running native ARM64 Java — for maximum performance, for avoiding translation overhead, or for building/testing Java-based native images (like GraalVM native binaries) that must target the real underlying CPU architecture.

## 3. Core concept

```bash
# On an Apple Silicon Mac, verify which architecture the running JVM actually targets:
java -XshowSettings:properties -version 2>&1 | grep os.arch
# os.arch = aarch64   -> running as native ARM64
# os.arch = x86_64    -> running under Rosetta 2 translation (an Intel-built JDK)
```

`os.arch` reveals the architecture the *JVM itself* was built for and is executing as — which, on Apple Silicon, is not automatically the same as the underlying hardware unless you specifically installed an `aarch64`-native JDK build.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="On Apple Silicon hardware, an x86-64-built JDK runs translated through Rosetta 2 with overhead, while a native aarch64-built JDK runs directly on the ARM64 CPU with no translation">
  <rect x="20" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">x86-64 JDK on Apple Silicon</text>
  <text x="160" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JVM (x86-64 instructions)</text>
  <text x="160" y="95" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">↓ Rosetta 2 translation layer</text>
  <text x="160" y="120" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ARM64 CPU</text>
  <text x="160" y="150" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">translation overhead on every instruction</text>

  <rect x="340" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">aarch64 JDK (Java 17+)</text>
  <text x="480" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JVM (native ARM64 instructions)</text>
  <text x="480" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ARM64 CPU</text>
  <text x="480" y="140" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">no translation layer, direct execution</text>
</svg>

Both JDKs run on the same physical Apple Silicon hardware, but only the `aarch64`-native build avoids the Rosetta 2 translation layer entirely.

## 5. Runnable example

Scenario: an architecture-diagnostic tool a developer might reach for right after installing a JDK on a new Apple Silicon Mac — first a basic report of `os.arch` and `os.name`, then a check that also asks macOS itself (via its `sysctl` utility) whether the current process is running translated under Rosetta, then a fuller diagnostic combining both signals into one clear verdict about whether this specific JVM process is running as native ARM64 or translated x86-64.

### Level 1 — Basic

```java
// File: ArchReportBasic.java
public class ArchReportBasic {
    public static void main(String[] args) {
        System.out.println("os.name: " + System.getProperty("os.name"));
        System.out.println("os.arch: " + System.getProperty("os.arch"));
    }
}
```

**How to run:**
```
java ArchReportBasic.java
```

Expected output shape (on a native Java 17+ ARM64 build on Apple Silicon):
```
os.name: Mac OS X
os.arch: aarch64
```

### Level 2 — Intermediate

```java
// File: RosettaCheck.java
import java.io.IOException;

public class RosettaCheck {
    static String checkRosettaTranslation() {
        if (!System.getProperty("os.name").startsWith("Mac")) {
            return "not applicable (not macOS)";
        }
        try {
            Process process = new ProcessBuilder("sysctl", "-n", "sysctl.proc_translated")
                    .redirectErrorStream(true).start();
            String output = new String(process.getInputStream().readAllBytes()).trim();
            int exitCode = process.waitFor();
            if (exitCode != 0 || output.isEmpty()) return "unknown (sysctl key not present; likely Intel Mac)";
            return output.equals("1") ? "yes, running under Rosetta 2 translation" : "no, running natively";
        } catch (IOException | InterruptedException e) {
            return "unknown (" + e.getMessage() + ")";
        }
    }

    public static void main(String[] args) {
        System.out.println("os.arch reported by JVM: " + System.getProperty("os.arch"));
        System.out.println("Rosetta 2 translation:   " + checkRosettaTranslation());
    }
}
```

**How to run:**
```
java RosettaCheck.java
```

Expected output shape (on an Apple Silicon Mac running a native aarch64 JDK):
```
os.arch reported by JVM: aarch64
Rosetta 2 translation:   no, running natively
```

### Level 3 — Advanced

```java
// File: FullArchDiagnostic.java
import java.io.IOException;

public class FullArchDiagnostic {
    record Verdict(String jvmArch, String hardwareArch, boolean translated, String summary) {}

    static String runCommand(String... command) {
        try {
            Process process = new ProcessBuilder(command).redirectErrorStream(true).start();
            String output = new String(process.getInputStream().readAllBytes()).trim();
            return process.waitFor() == 0 ? output : "(unavailable)";
        } catch (IOException | InterruptedException e) {
            return "(unavailable: " + e.getMessage() + ")";
        }
    }

    static Verdict diagnose() {
        String jvmArch = System.getProperty("os.arch");
        boolean isMac = System.getProperty("os.name").startsWith("Mac");

        if (!isMac) {
            return new Verdict(jvmArch, "(not macOS)", false, "Not applicable outside macOS.");
        }

        String hardwareArch = runCommand("uname", "-m"); // the true underlying CPU architecture
        String translatedFlag = runCommand("sysctl", "-n", "sysctl.proc_translated");
        boolean translated = translatedFlag.equals("1");

        String summary;
        if (jvmArch.equals("aarch64") && !translated) {
            summary = "Running native ARM64 JVM directly on Apple Silicon — no translation overhead.";
        } else if (jvmArch.equals("x86_64") && translated) {
            summary = "Running an x86-64 JVM translated through Rosetta 2 on Apple Silicon hardware.";
        } else if (jvmArch.equals("x86_64") && !translated) {
            summary = "Running an x86-64 JVM on genuine Intel hardware (or Rosetta status undetermined).";
        } else {
            summary = "Unrecognized combination — inspect jvmArch/hardwareArch/translated directly.";
        }

        return new Verdict(jvmArch, hardwareArch, translated, summary);
    }

    public static void main(String[] args) {
        Verdict v = diagnose();
        System.out.println("JVM os.arch:        " + v.jvmArch());
        System.out.println("Hardware (uname -m): " + v.hardwareArch());
        System.out.println("Rosetta-translated:  " + v.translated());
        System.out.println("Summary: " + v.summary());
    }
}
```

**How to run:**
```
java FullArchDiagnostic.java
```

Expected output shape (native aarch64 JDK on Apple Silicon hardware):
```
JVM os.arch:        aarch64
Hardware (uname -m): arm64
Rosetta-translated:  false
Summary: Running native ARM64 JVM directly on Apple Silicon — no translation overhead.
```

## 6. Walkthrough

1. `FullArchDiagnostic.main` calls `diagnose()`, which first reads `os.arch` directly from the running JVM — this property reflects what architecture *the JVM binary itself* was compiled for, which is exactly the distinction JEP 391 is about: before Java 17, macOS JDK builds only targeted `x86_64`, so on Apple Silicon, this property could only ever report `x86_64` (running translated), never `aarch64`.
2. `diagnose()` then shells out twice via `runCommand`: once to `uname -m`, which asks the operating system kernel for the **true underlying hardware architecture** (`arm64` on any Apple Silicon Mac, translation or not), and once to `sysctl -n sysctl.proc_translated`, a macOS-specific key that reports whether the *current process* is running under Rosetta 2 translation (`1`) or natively (`0`, or the key is absent entirely on Intel Macs where the concept doesn't apply).
3. Combining these three signals — the JVM's own self-reported architecture, the hardware's real architecture, and the translation flag — lets `diagnose()` distinguish the three meaningfully different scenarios: a native ARM64 JVM on Apple Silicon (the JEP 391 outcome), an x86-64 JVM being translated on Apple Silicon (the pre-JEP-391 situation, still possible today by simply installing an Intel-built JDK), or an x86-64 JVM on genuine Intel hardware (`translated` reads `false` because the concept doesn't apply there at all).
4. The `Verdict` record packages all four pieces of information together, and `main` prints each field followed by the human-readable `summary`, giving a complete, actionable answer to "is this JVM actually running natively on this Apple Silicon Mac?" — the exact question a developer setting up a new machine, or debugging unexpectedly slow Java performance on Apple Silicon, would want answered.
5. Note that `runCommand`'s fallback branches (`"(unavailable)"`) mean this program degrades gracefully rather than crashing on non-macOS platforms or in environments where `sysctl`/`uname` aren't on the `PATH`, consistent with keeping the example runnable everywhere even though its interesting branch only triggers on real macOS hardware.

```
diagnose():
  jvmArch = System.getProperty("os.arch")          (what the JVM binary itself targets)
  if not macOS: return early, "not applicable"
  hardwareArch = `uname -m`                        (the true CPU architecture)
  translated = `sysctl -n sysctl.proc_translated` == "1"
  classify (jvmArch, translated) into one of:
    native ARM64 | translated x86-64 | native Intel | unrecognized
```

## 7. Gotchas & takeaways

> `sysctl.proc_translated` is a **macOS-specific** `sysctl` key that only exists meaningfully on Apple Silicon Macs; running this check on Linux, Windows, or older Intel Macs correctly falls back to `"(unavailable)"` via the `catch` block, since the command either fails or the key doesn't exist — treat any non-macOS result as simply "not applicable," not an error.
- Installing "a JDK" on an Apple Silicon Mac does **not** automatically mean you're running native ARM64 Java — you must specifically download an `aarch64`/ARM64-targeted JDK distribution; an Intel (`x86_64`) build will run perfectly well, just translated through Rosetta 2, with `os.arch` reporting `x86_64` the whole time.
- `os.arch` reflects the **JVM's own build target**, not necessarily the underlying silicon — always check `os.arch` first when diagnosing "is this actually running natively," since it's the one property that's portable across every platform, unlike the macOS-specific `sysctl` checks.
- This JEP is purely a **platform/build-support** change — no Java API or language feature is affected; correctly-written, portable Java code behaves identically whether the JVM underneath is `x86_64` or `aarch64`.
- Performance-sensitive applications, and especially anything invoking native code via JNI or the [Foreign Function & Memory API](0709-foreign-function-memory-api-incubator.md), benefit most directly from running a genuinely native ARM64 JDK on Apple Silicon, since native libraries themselves must also match the running architecture (an ARM64 JVM cannot load an x86-64 native `.dylib`, and vice versa).
- This port shipped proactively, ahead of most Apple Silicon Macs reaching end users — a deliberate choice to have mature native ARM64 Java support ready *before* demand for it peaked, rather than scrambling to catch up afterward.
